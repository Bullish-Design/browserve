# File: /src/browserve/core/logger.py
"""
Browser Logger: high-performance, buffered event logger.

- Subscribes to PageBase events non-blockingly
- Filters events with composable EventFilter objects
- Buffers writes for throughput; periodic async flush
- Supports JSONL (stream), JSON (array), CSV exports
- Simple size-based log rotation

Usage example::

    logger = BrowserLogger(output_path=Path("logs/session.jsonl"))
    logger.add_filter(create_event_type_filter(["interaction", "navigation"]))  # optional
    await logger.start_logging(page)
    # ... emit events ...
    await logger.stop_logging(page)

All methods are async-friendly and should not block page interactions.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional, TextIO, TYPE_CHECKING, Iterable

from ..events.base import EventBase
from ..events.filters import EventFilter
from ..events.handlers import EventHandler
from ..models.config import LoggingConfig
from ..exceptions import LoggingError

if TYPE_CHECKING:
    from ..core.page import PageBase


class LogBuffer:
    """High-performance event buffer with automatic flushing.

    Thread-safe-ish for asyncio via an internal lock.
    """

    def __init__(self, max_size: int = 1000, auto_flush: bool = True):
        self.max_size = max_size
        self.auto_flush = auto_flush
        self._buffer: deque[EventBase] = deque()
        self._lock = asyncio.Lock()

    async def add_event(self, event: EventBase) -> bool:
        """Add event to buffer, return True if buffer should flush."""
        async with self._lock:
            self._buffer.append(event)
            return len(self._buffer) >= self.max_size

    async def flush_all(self) -> List[EventBase]:
        """Flush and return all buffered events."""
        async with self._lock:
            events = list(self._buffer)
            self._buffer.clear()
            return events

    @property
    def size(self) -> int:
        return len(self._buffer)


class BrowserLogger:
    """Event-driven logger for comprehensive browser interaction tracking.

    Designed to be lightweight on the hot path (event handling), doing I/O
    in batches via an async flush coroutine.
    """

    def __init__(
        self,
        output_path: Optional[Path] = None,
        config: Optional[LoggingConfig] = None,
    ):
        self.config = config or LoggingConfig()
        self.output_path = Path(output_path) or self.config.output_path or Path("browserve_session.jsonl")
        self.filters: List[EventFilter] = []
        self.buffer = LogBuffer(max_size=self.config.buffer_size, auto_flush=self.config.auto_flush)
        self._active_pages: Dict[str, "PageBase"] = {}
        self._output_file: Optional[TextIO] = None
        self._flush_task: Optional[asyncio.Task] = None
        self._is_logging = False

    async def start_logging(self, page: "PageBase") -> None:
        """Begin logging events from a page."""
        if not self._is_logging:
            await self._initialize_logging()

        # Subscribe to all core page events
        page.subscribe("interaction", self._handle_event)
        page.subscribe("navigation", self._handle_event)
        page.subscribe("network_request", self._handle_event)
        page.subscribe("dom_change", self._handle_event)

        self._active_pages[page.session_id] = page

    async def stop_logging(self, page: "PageBase") -> None:
        """Stop logging events from a specific page."""
        # Attempt to unsubscribe to avoid leaks
        try:
            page.unsubscribe("interaction", self._handle_event)
            page.unsubscribe("navigation", self._handle_event)
            page.unsubscribe("network_request", self._handle_event)
            page.unsubscribe("dom_change", self._handle_event)
        except Exception:
            # Unsubscribe best-effort; continue
            pass

        if page.session_id in self._active_pages:
            del self._active_pages[page.session_id]

        if not self._active_pages:
            await self._shutdown_logging()

    async def _handle_event(self, event: EventBase) -> None:
        """Process an event through filters and buffer non-blockingly."""
        # Filters
        for event_filter in self.filters:
            try:
                if not event_filter.should_process(event):
                    return
            except Exception as e:
                # Fail open on filter errors but record an internal error event
                # (We do not raise to avoid breaking emit path.)
                continue

        # Buffering
        should_flush = await self.buffer.add_event(event)

        # Auto flush if configured
        if should_flush and self.config.auto_flush:
            await self._flush_buffer()

    async def _flush_buffer(self) -> None:
        """Flush current buffer batch to disk."""
        if not self._output_file:
            return

        events = await self.buffer.flush_all()
        if not events:
            return

        try:
            # Rotate if necessary before writing
            if self.config.rotate_logs and self._needs_rotation(events):
                await self._rotate_file()

            if self.config.format == "jsonl":
                for evt in events:
                    line = json.dumps(evt.model_dump()) + "\n"
                    self._output_file.write(line)

            elif self.config.format == "json":
                # Append as an array chunk; if file is empty, create array, else extend it.
                # We do a simple read/append/write cycle; this is acceptable for small batches.
                # For very large logs, prefer JSONL format.
                try:
                    self._output_file.flush()
                    # Read existing
                    existing: List[dict] = []
                    if self.output_path.exists() and self.output_path.stat().st_size > 0:
                        with open(self.output_path, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                    existing.extend([e.model_dump() for e in events])
                    with open(self.output_path, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2)
                finally:
                    # Reopen append for future writes
                    self._output_file.close()
                    self._output_file = open(self.output_path, "a", encoding="utf-8")

            elif self.config.format == "csv":
                # If file is empty, write header. Flatten metadata keys dynamically.
                # Choose a stable set of columns
                base_cols = ["event_type", "timestamp", "page_url", "session_id"]
                # Collect metadata keys
                meta_keys: set[str] = set()
                for e in events:
                    md = e.model_dump().get("metadata", {}) or {}
                    meta_keys.update(md.keys())
                headers = base_cols + sorted(meta_keys)

                # Determine if file empty for header
                write_header = self.output_path.stat().st_size == 0
                writer = csv.DictWriter(self._output_file, fieldnames=headers)
                if write_header:
                    writer.writeheader()

                for e in events:
                    d = e.model_dump()
                    row = {k: d.get(k) for k in base_cols}
                    meta = d.get("metadata", {}) or {}
                    for k in meta_keys:
                        row[k] = meta.get(k)
                    writer.writerow(row)

            # Ensure data hits disk without blocking loop too long
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._output_file.flush)

        except Exception as e:
            raise LoggingError(f"Failed to flush events: {e}") from e

    def _needs_rotation(self, pending_events: Iterable[EventBase]) -> bool:
        try:
            cur = self.output_path.stat().st_size if self.output_path.exists() else 0
            if cur >= self.config.max_file_size:
                return True
            # Approximate size of pending write (jsonl worst-case)
            approx = sum(len(json.dumps(e.model_dump())) + 1 for e in pending_events)
            return (cur + approx) >= self.config.max_file_size
        except Exception:
            return False

    async def _rotate_file(self) -> None:
        """Rotate current log file by renaming with timestamp suffix."""
        if self._output_file:
            self._output_file.close()
            self._output_file = None

        ts = int(time.time())
        rotated = self.output_path.with_name(f"{self.output_path.stem}.{ts}{self.output_path.suffix}")
        try:
            if self.output_path.exists():
                self.output_path.rename(rotated)
        except OSError as e:
            # If rename fails, we continue without rotation
            pass
        finally:
            # Reopen the file for subsequent appends
            self._output_file = open(self.output_path, "a", encoding="utf-8")

    async def _initialize_logging(self) -> None:
        """Initialize logging: create directories and open file."""
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self._output_file = open(self.output_path, "a", encoding="utf-8")
            self._is_logging = True
            if self.config.auto_flush:
                self._flush_task = asyncio.create_task(self._periodic_flush())
        except Exception as e:
            raise LoggingError(f"Failed to initialize logging: {e}") from e

    async def _shutdown_logging(self) -> None:
        """Shutdown logging, flushing any remaining buffer and closing file."""
        self._is_logging = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None
        await self._flush_buffer()
        if self._output_file:
            try:
                self._output_file.close()
            finally:
                self._output_file = None

    async def _periodic_flush(self) -> None:
        """Background task for periodic flushes (every second)."""
        while self._is_logging:
            await asyncio.sleep(1.0)
            if self.buffer.size > 0:
                await self._flush_buffer()

    # Filter management
    def add_filter(self, event_filter: EventFilter) -> None:
        self.filters.append(event_filter)

    def remove_filter(self, event_filter: EventFilter) -> None:
        if event_filter in self.filters:
            self.filters.remove(event_filter)

    # Export
    async def export_logs(self, export_path: Path, format: str = "jsonl") -> bool:
        """Export existing logs from current output_path to another file/format.

        This reads from ``self.output_path`` and converts to the requested format.
        """
        try:
            src = self.output_path
            if not src.exists():
                raise LoggingError(f"No log file at {src}")

            export_path.parent.mkdir(parents=True, exist_ok=True)

            if format == "jsonl":
                # If already jsonl, just copy
                with open(src, "r", encoding="utf-8") as r, open(export_path, "w", encoding="utf-8") as w:
                    for line in r:
                        w.write(line)
                return True

            # Load all events from jsonl/json
            events: List[dict] = []
            if src.suffix.lower().endswith("l"):  # .jsonl
                with open(src, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        events.append(json.loads(line))
            else:
                with open(src, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                    if isinstance(obj, list):
                        events = obj
                    else:
                        events = [obj]

            if format == "json":
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2)
                return True

            if format == "csv":
                # Flatten metadata
                base_cols = ["event_type", "timestamp", "page_url", "session_id"]
                meta_keys = set()
                for e in events:
                    md = e.get("metadata", {}) or {}
                    meta_keys.update(md.keys())
                headers = base_cols + sorted(meta_keys)
                with open(export_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    for e in events:
                        row = {k: e.get(k) for k in base_cols}
                        md = e.get("metadata", {}) or {}
                        for mk in meta_keys:
                            row[mk] = md.get(mk)
                        writer.writerow(row)
                return True

            raise LoggingError(f"Unsupported export format: {format}")

        except Exception as e:
            raise LoggingError(f"Export failed: {e}") from e
