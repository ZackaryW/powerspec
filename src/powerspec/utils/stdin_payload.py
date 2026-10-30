"""Read one JSON object from a stream without waiting for end of input."""

from __future__ import annotations

import json
import os
import queue
import threading
import time


def _chunks(stream, sink: queue.Queue) -> None:
    """Forward raw bytes, then an empty chunk at end of input or on failure."""
    try:
        descriptor = stream.fileno()
    except (AttributeError, OSError, ValueError):
        descriptor = None
    try:
        if descriptor is None:
            data = stream.read()
            sink.put(data.encode("utf-8") if isinstance(data, str) else data)
            sink.put(b"")
            return
        while True:
            # os.read returns whatever has arrived, so a host that keeps the
            # pipe open after writing cannot stall the reader.
            data = os.read(descriptor, 65536)
            sink.put(data)
            if not data:
                return
    except (OSError, ValueError):
        sink.put(b"")


def read_json_object(stream, timeout: float) -> dict | None:
    """Return the first complete JSON object on *stream*, or ``None``.

    Stops when one object is complete, at end of input, as soon as the input
    cannot start an object, or after *timeout* seconds; it never waits for
    end-of-file. A terminal is not read. Malformed input is ``None``.
    """
    try:
        if stream.isatty():
            return None
    except (AttributeError, OSError, ValueError):
        return None
    sink: queue.Queue = queue.Queue()
    threading.Thread(target=_chunks, args=(stream, sink), daemon=True).start()
    decoder = json.JSONDecoder()
    deadline = time.monotonic() + timeout
    buffer = b""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            data = sink.get(timeout=remaining)
        except queue.Empty:
            return None
        if not data:
            return None
        buffer += data
        try:
            text = buffer.decode("utf-8").lstrip()
        except UnicodeDecodeError:
            continue  # A multi-byte character may be split across reads.
        if text and not text.startswith("{"):
            return None
        try:
            value, _ = decoder.raw_decode(text)
        except json.JSONDecodeError:
            continue
        return value if isinstance(value, dict) else None
