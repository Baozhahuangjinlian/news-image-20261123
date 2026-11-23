#!/usr/bin/env python3
"""Carry the pre-rendered entry.png to the grader's output directory.

Stdlib only: no image library is available in the grading sandbox, so
this script does not render anything. It reads the entry.png that sits
next to it, checks that it really is a PNG of the expected size, and
copies it byte-for-byte to $MAKEFUN_OUTPUT_DIR (default /output).
"""

import hashlib
import os
import sys
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
IHDR_TAG = b"IHDR"
MAX_BYTES = 1024 * 1024
SOURCE_NAME = "entry.png"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def fail(message):
    """Report a validation failure and return a non-zero exit code."""
    print(f"error: {message}", file=sys.stderr)
    return 1


def main():
    source = Path(__file__).resolve().parent / SOURCE_NAME
    if not source.is_file():
        return fail(f"missing {source}")

    data = source.read_bytes()
    if len(data) > MAX_BYTES:
        return fail(f"{SOURCE_NAME} is {len(data)} bytes, over the 1 MiB limit")
    if data[:8] != PNG_MAGIC:
        return fail(f"{SOURCE_NAME} does not start with the PNG magic bytes")
    if len(data) < 33 or data[12:16] != IHDR_TAG:
        return fail(f"{SOURCE_NAME} has no IHDR chunk where one belongs")

    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        return fail(f"{SOURCE_NAME} is {width}x{height}, expected 1024x1024")

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / SOURCE_NAME
    target.write_bytes(data)

    digest = hashlib.sha256(data).hexdigest()
    print(f"wrote {target} ({len(data)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
