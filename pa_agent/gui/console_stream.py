"""Capture stdout/stderr into an in-app console buffer.

The desktop launcher starts the app with ``pythonw.exe`` (no console window), so
everything the program used to print — logging output, library warnings,
tracebacks — is redirected into a bounded in-memory buffer that the
「控制台」 tab reads with a timer.

Design notes:
* No Qt objects here: this module is imported and installed **before**
  ``QApplication`` exists.
* Thread safe: worker threads (RefreshLoop, analysis) also print/log.
* Bounded: only the most recent chunks are kept.
"""
from __future__ import annotations

import sys
import threading
from collections import deque
from typing import TextIO

_MAX_CHUNKS = 4000


class ConsoleBuffer:
    """Thread-safe bounded sink for console text."""

    def __init__(self, max_chunks: int = _MAX_CHUNKS) -> None:
        self._chunks: deque[str] = deque(maxlen=max_chunks)
        self._lock = threading.Lock()

    def write(self, text: str) -> None:
        if not text:
            return
        with self._lock:
            self._chunks.append(text)

    def drain(self) -> str:
        """Return and forget everything written since the last drain."""
        with self._lock:
            if not self._chunks:
                return ""
            text = "".join(self._chunks)
            self._chunks.clear()
            return text


class _Tee:
    """Write-through stream: original stdout/stderr plus the console buffer."""

    def __init__(self, original: TextIO | None, buffer: ConsoleBuffer) -> None:
        self._original = original
        self._buffer = buffer

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            text = str(text)
        self._buffer.write(text)
        if self._original is not None:
            try:
                self._original.write(text)
            except Exception:  # noqa: BLE001 - a broken console must not break us
                pass
        return len(text)

    def flush(self) -> None:
        if self._original is not None:
            try:
                self._original.flush()
            except Exception:  # noqa: BLE001
                pass

    def isatty(self) -> bool:
        return False

    def fileno(self) -> int:  # pragma: no cover - only used by niche libraries
        if self._original is not None and hasattr(self._original, "fileno"):
            return self._original.fileno()  # type: ignore[return-value]
        raise OSError("no file descriptor")


CONSOLE_BUFFER = ConsoleBuffer()
_installed = False


def install_console_capture() -> ConsoleBuffer:
    """Route ``sys.stdout`` / ``sys.stderr`` into :data:`CONSOLE_BUFFER`."""
    global _installed
    if _installed:
        return CONSOLE_BUFFER
    sys.stdout = _Tee(sys.stdout, CONSOLE_BUFFER)  # type: ignore[assignment]
    sys.stderr = _Tee(sys.stderr, CONSOLE_BUFFER)  # type: ignore[assignment]
    _installed = True
    return CONSOLE_BUFFER
