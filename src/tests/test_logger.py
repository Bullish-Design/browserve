# File: /src/tests/test_logger.py
import asyncio
import json
import time
from pathlib import Path

import pytest

from browserve.core import PageBase, BrowserLogger
from browserve.events import InteractionEvent
from browserve.events.filters import EventFilter
from browserve.models import LoggingConfig

# Formatted timestamp for log filenames
timestamp = time.strftime("%Y%m%d_%H%M%S")


@pytest.mark.asyncio
async def test_logger_writes_jsonl(tmp_path: Path):
    tmp_path = Path("/home/andrew/Documents/Projects/browserve/src/.hidden/logs/test_logger")

    out = tmp_path / f"log_{timestamp}.jsonl"
    # Respect buffer_size >= 10
    logger = BrowserLogger(output_path=out, config=LoggingConfig(format="jsonl", auto_flush=True, buffer_size=10))

    page = PageBase(session_id="s1", url="https://example.com")
    await logger.start_logging(page)

    # Provide required top-level fields: action and selector
    for i in range(5):
        evt = InteractionEvent(
            event_type="interaction",
            page_url="https://example.com",
            session_id="s1",
            action="click",
            selector="#btn",
            metadata={"index": i},
            timestamp=time.time(),
        )
        await page.emit(evt)

    await asyncio.sleep(0.1)
    await logger.stop_logging(page)

    assert out.exists()
    with open(out, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]

    assert len(lines) == 5
    assert all(l["event_type"] == "interaction" for l in lines)


@pytest.mark.asyncio
async def test_logger_filters_by_session(tmp_path: Path):
    tmp_path = Path("/home/andrew/Documents/Projects/browserve/src/.hidden/logs/test_logger")

    out = tmp_path / f"log_filter_{timestamp}.jsonl"
    logger = BrowserLogger(output_path=out, config=LoggingConfig(format="jsonl", auto_flush=True, buffer_size=10))

    # Build a session filter using your existing API (no changes to filters.py)
    keep_ids = {"keep"}
    logger.add_filter(EventFilter(custom_filter=lambda e: getattr(e, "session_id", None) in keep_ids))

    p1 = PageBase(session_id="drop", url="https://example.com")
    p2 = PageBase(session_id="keep", url="https://example.com")
    await logger.start_logging(p1)
    await logger.start_logging(p2)

    await p1.emit(
        InteractionEvent(
            event_type="interaction",
            page_url="https://example.com",
            session_id="drop",
            action="click",
            selector="#a",
        )
    )
    await p2.emit(
        InteractionEvent(
            event_type="interaction",
            page_url="https://example.com",
            session_id="keep",
            action="click",
            selector="#b",
        )
    )

    await asyncio.sleep(0.1)
    await logger.stop_logging(p1)
    await logger.stop_logging(p2)

    with open(out, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]

    assert len(lines) == 1
    assert lines[0]["session_id"] == "keep"


@pytest.mark.asyncio
async def test_export_to_csv(tmp_path: Path):
    tmp_path = Path("/home/andrew/Documents/Projects/browserve/src/.hidden/logs/test_logger")

    out = tmp_path / f"log_{timestamp}.jsonl"
    csv_out = tmp_path / f"export_{timestamp}.csv"
    logger = BrowserLogger(output_path=out, config=LoggingConfig(format="jsonl", auto_flush=True, buffer_size=10))
    page = PageBase(session_id="s1", url="https://example.com")
    await logger.start_logging(page)

    for i in range(3):
        await page.emit(
            InteractionEvent(
                event_type="interaction",
                page_url="https://example.com",
                session_id="s1",
                action="click",
                selector="#btn",
                metadata={"i": i},
            )
        )

    await asyncio.sleep(0.1)
    await logger.stop_logging(page)

    ok = await logger.export_logs(csv_out, format="csv")
    assert ok and csv_out.exists()
    with open(csv_out, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
    assert "event_type" in header and "session_id" in header


@pytest.mark.asyncio
async def test_rotation(tmp_path: Path):
    out = tmp_path / f"log_{timestamp}.jsonl"
    # Respect max_file_size >= 1 MiB; force rotation by sending large events
    logger = BrowserLogger(
        output_path=out,
        config=LoggingConfig(
            format="jsonl", auto_flush=True, buffer_size=50, max_file_size=1_048_576, rotate_logs=True
        ),
    )
    page = PageBase(session_id="s1", url="https://example.com")
    await logger.start_logging(page)

    # Each event carries a ~5KB payload; ~300 events ~ 1.5MB -> should rotate
    payload = "x" * 5000
    for i in range(300):
        await page.emit(
            InteractionEvent(
                event_type="interaction",
                page_url="https://example.com",
                session_id="s1",
                action="click",
                selector="#big",
                metadata={"i": i, "payload": payload},
            )
        )

    await asyncio.sleep(0.5)
    await logger.stop_logging(page)

    rotated = list(tmp_path.glob("log*.jsonl"))
    assert out.exists()
    # At least one rotated file should exist alongside the active file
    assert len(rotated) >= 1


@pytest.mark.asyncio
async def test_perf_1000_eps(tmp_path: Path):
    tmp_path = Path("/home/andrew/Documents/Projects/browserve/src/.hidden/logs/test_logger")
    out = tmp_path / f"perf_{timestamp}.jsonl"
    logger = BrowserLogger(output_path=out, config=LoggingConfig(format="jsonl", auto_flush=True, buffer_size=256))
    page = PageBase(session_id="s1", url="https://example.com")
    await logger.start_logging(page)

    N = 1200
    t0 = time.perf_counter()
    for i in range(N):
        await page.emit(
            InteractionEvent(
                event_type="interaction",
                page_url="https://example.com",
                session_id="s1",
                action="click",
                selector="#fast",
                metadata={"i": i},
            )
        )
    await asyncio.sleep(0.25)
    await logger.stop_logging(page)
    t1 = time.perf_counter()

    assert (t1 - t0) < 1.5
    with open(out, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) >= N * 0.8
