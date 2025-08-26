#!/usr/bin/env python3
"""
/// script
/// requires-python = ">=3.13"
/// dependencies = [
///     "playwright>=1.52.0",
///     "pytest>=8",
///     "pytest-asyncio>=0.23",
/// ]
/// ///

End-to-end test runner for browserve library.

This script sets up Playwright browsers and runs the full e2e test suite
against real websites to verify browserve functionality.
"""

from __future__ import annotations
import subprocess
import sys
import logging
import datetime
from pathlib import Path
import asyncio


def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    # Create log directory
    log_dir = Path("/home/andrew/Documents/Projects/browserve/src/.hidden/logs/run_e2e_tests")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamped log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"e2e_test_run_{timestamp}.log"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - log file: {log_file}")
    return logger


async def check_playwright_setup():
    """Check if Playwright browsers are available (Nix or installed)."""
    import os

    # Check if using Nix setup (devenv provides browsers)
    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if browsers_path:
        print(f"PLAYWRIGHT_BROWSERS_PATH: {browsers_path}")

        # Check if parent directory exists and has browser subdirectories
        browsers_dir = Path(browsers_path)
        # Iterate through subdirectories to find any browser directories:
        if browsers_dir.exists() and any(browsers_dir.iterdir()):
            print(f"✓ Found Playwright browsers in: {browsers_dir}")
            # For directory in browsers_dir.iterdir(), print its name:
            for d in browsers_dir.iterdir():
                if d.is_dir():
                    print(f"    ✓ Found browser directory: {d.name}")

        if browsers_dir.exists():
            # Look for chromium directory (pattern: chromium-*)
            chromium_dirs = list(browsers_dir.glob("chromium-*"))
            if chromium_dirs:
                print(f"✓ Found Nix Chromium browser: {chromium_dirs[0]}")
                return True

        print(f"    Parent exists: {browsers_dir.parent.exists()}")
        print(f"    Full path exists: {browsers_dir.exists()}")

    # Skip installation - can't write to Nix store
    print("✗ Nix browsers not found and can't install to read-only store")
    return False


async def run_e2e_tests():
    """Run the end-to-end tests."""
    print("Running browserve end-to-end tests...")

    # Change to tests directory
    tests_dir = Path(__file__).parent

    # Run pytest with specific test file
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "test_e2e_integration.py",
        "-v",
        "-s",  # verbose and no capture for real-time output
        "--tb=short",  # shorter traceback format
    ]

    try:
        result = subprocess.run(cmd, cwd=tests_dir)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


async def main():
    """Main entry point."""
    print("Browserve E2E Test Runner")
    print("=" * 40)

    # Check Playwright setup (Nix or install browsers)
    if not await check_playwright_setup():
        print("✗ Playwright setup failed. Cannot run tests.")
        sys.exit(1)

    # Run the tests
    success = await run_e2e_tests()

    if success:
        print("\n✓ All end-to-end tests passed!")
        print("\nTest outputs saved in test_output/ directory")
    else:
        print("\n✗ Some tests failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
