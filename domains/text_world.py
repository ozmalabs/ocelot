"""text_world — world adapter that exposes text sources to the substrate
by pointer, not by copy. Supports streaming with explicit
seekability + endedness flags.

The substrate gets a TextSource node with attributes describing the
external source. The agent's runtime reads from it via the
`read_text_source` / `seek_text_source` calls (driven by user code
or higher-level world drivers between substrate ticks).

PER CLAUDE.MD

This is mechanical translation of external I/O into substrate state:
  · open_text_source: external handle (file, in-memory string, pipe)
    → substrate node + attributes
  · read_text_source: external read → return bytes + update position
  · seek_text_source: external seek (if seekable)
  · close_text_source: release the external handle

No agent decisions. No reading logic. No interpretation of the text.
Just the I/O boundary translated into substrate state.

THE CONTRACT — TextSource node attributes the agent can read

  · kind: "file", "memory", "stream"
  · pointer: the external pointer (path, URL, or opaque ID)
  · seekable: True iff the source supports random access
  · length: number of bytes/chars when known; -1 when unknown (streams)
  · position: current read offset (updated by read_text_source)
  · ended: True iff the source has been fully consumed
  · streaming: True iff the source is a forward-only stream
  · no_lookback: True iff streaming AND not seekable — the agent
                 CANNOT revisit content once read. The agent's rules
                 must decide what to retain BEFORE reading the next
                 chunk.

The agent inspects these via Attr() and decides how to read.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any, BinaryIO, TextIO

# Substrate-side handle → Python-side I/O state. NOT the agent's
# concern; this is bookkeeping internal to the world adapter.
_OPEN_TEXTS: dict[int, dict[str, Any]] = {}


def open_text_source(
    substrate,
    source: str | Path | TextIO | BinaryIO,
    *,
    name: str | None = None,
    streaming: bool | None = None,
    seekable: bool | None = None,
    encoding: str = "utf-8",
) -> Any:
    """Register an external text source with the substrate. Returns the
    TextSource NodeID.

    `source` can be:
      · a Path or str-path naming a file (default seekable, finite)
      · a string of in-memory text (always seekable, finite)
      · an already-open file-like object (seekable inferred from object)
      · an iterable of strings/bytes — treated as a stream (not seekable)

    `streaming` overrides the inferred streaming nature.
    `seekable` overrides the inferred seekable flag. When the source is
    streaming AND not seekable, the agent gets `no_lookback=True` —
    a hard contract that content read past cannot be revisited.
    """
    # Identify the source kind + initial properties.
    if isinstance(source, (str, Path)) and Path(str(source)).exists():
        path = str(source)
        handle = open(path, "r", encoding=encoding)
        kind = "file"
        length = Path(path).stat().st_size
        seekable_default = True
        streaming_default = False
    elif isinstance(source, str):
        handle = io.StringIO(source)
        kind = "memory"
        length = len(source)
        seekable_default = True
        streaming_default = False
    elif hasattr(source, "read"):
        handle = source
        kind = "stream"
        length = -1
        seekable_default = bool(getattr(source, "seekable",
                                          lambda: False)())
        streaming_default = not seekable_default
    else:
        # Iterable of chunks → wrap as a stream.
        handle = _IterableStream(source)
        kind = "stream"
        length = -1
        seekable_default = False
        streaming_default = True

    streaming_v = streaming_default if streaming is None else streaming
    seekable_v = seekable_default if seekable is None else seekable
    no_lookback = bool(streaming_v and not seekable_v)

    attrs = {
        "name":         name or kind,
        "kind":         kind,
        "pointer":      str(source) if kind == "file" else f"<{kind}>",
        "seekable":     seekable_v,
        "streaming":    streaming_v,
        "no_lookback":  no_lookback,
        "length":       length,
        "position":     0,
        "ended":        False,
        "encoding":     encoding,
        "origin":       "text_world",
    }
    nid = substrate.add_node("TextSource", attrs)
    _OPEN_TEXTS[_nid_int(nid)] = {
        "handle": handle,
        "kind": kind,
    }
    return nid


def read_text_source(substrate, source_nid, n: int = -1) -> str:
    """Read up to `n` characters (or all remaining when n=-1). Returns the
    read text. Updates `position` and `ended` attributes on the
    TextSource node. Raises if the source isn't open.

    For streaming sources without lookback, the returned text is the
    only chance the agent has to read it — the source's `position` flag
    moves forward, and `seek_text_source` will fail.
    """
    nid = _nid_int(source_nid)
    if nid not in _OPEN_TEXTS:
        raise ValueError(f"no open text source for nid {nid}")
    handle = _OPEN_TEXTS[nid]["handle"]
    chunk = handle.read(n)
    if not isinstance(chunk, str):
        # iterable stream may yield bytes
        try:
            chunk = chunk.decode("utf-8")
        except Exception:
            chunk = str(chunk)
    new_pos = substrate.node(source_nid)["attrs"].get("position", 0) + len(chunk)
    substrate.set_attr(source_nid, "position", new_pos)
    if n != -1 and len(chunk) < n:
        substrate.set_attr(source_nid, "ended", True)
    if n == -1:
        substrate.set_attr(source_nid, "ended", True)
    return chunk


def seek_text_source(substrate, source_nid, position: int) -> None:
    """Seek to an absolute position in the source. Raises ValueError if
    the source is not seekable (e.g. streaming without lookback)."""
    nid = _nid_int(source_nid)
    if nid not in _OPEN_TEXTS:
        raise ValueError(f"no open text source for nid {nid}")
    attrs = substrate.node(source_nid)["attrs"]
    if not attrs.get("seekable", False):
        raise ValueError(
            f"text source {nid} is not seekable "
            f"(streaming={attrs.get('streaming')}, "
            f"no_lookback={attrs.get('no_lookback')})")
    handle = _OPEN_TEXTS[nid]["handle"]
    handle.seek(position)
    substrate.set_attr(source_nid, "position", position)
    substrate.set_attr(source_nid, "ended", False)


def close_text_source(substrate, source_nid) -> None:
    """Release the external handle. Does not delete the substrate node;
    subsequent reads return empty + `ended=True`."""
    nid = _nid_int(source_nid)
    if nid in _OPEN_TEXTS:
        h = _OPEN_TEXTS[nid]["handle"]
        try:
            h.close()
        except Exception:
            pass
        del _OPEN_TEXTS[nid]
    substrate.set_attr(source_nid, "ended", True)


# --- internals ---


def _nid_int(nid) -> int:
    return nid.value if hasattr(nid, "value") else int(nid)


class _IterableStream:
    """Wraps an iterable of chunks into a `.read(n)` interface so the
    same read/seek machinery handles in-memory, file, and iterable
    inputs uniformly. Forward-only by construction."""

    def __init__(self, iterable):
        self._iter = iter(iterable)
        self._buf = ""

    def read(self, n: int = -1) -> str:
        if n < 0:
            parts = [self._buf]
            self._buf = ""
            for chunk in self._iter:
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8")
                parts.append(chunk)
            return "".join(parts)
        while len(self._buf) < n:
            try:
                chunk = next(self._iter)
            except StopIteration:
                break
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def seekable(self):
        return False

    def close(self):
        pass
