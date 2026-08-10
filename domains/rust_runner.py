"""Lazy ctypes loader for the Rust ``recognise_frame`` binary runner.

The .so is built out-of-process via ``cargo build --release`` in
``runners/rust/``. This module loads it lazily; if the binary isn't built
the API silently falls back to "unavailable" so the substrate still runs
on the pure-Python recogniser. Callers check ``is_available()`` before
delegating.
"""
from __future__ import annotations

import ctypes
import json
from pathlib import Path

_SO_PATH = (Path(__file__).resolve().parent.parent
            / "runners" / "rust" / "target" / "release"
            / "librecognise_frame.so")

_lib: "ctypes.CDLL | None" = None
_load_attempted: bool = False


def _lib_handle() -> "ctypes.CDLL | None":
    """Load the cdylib on first access; cache the result. None if missing
    or unloadable — the caller should fall back to the Python recogniser."""
    global _lib, _load_attempted
    if _load_attempted:
        return _lib
    _load_attempted = True
    if not _SO_PATH.exists():
        return None
    try:
        h = ctypes.CDLL(str(_SO_PATH))
        h.install_frame.argtypes = [ctypes.c_char_p]
        h.install_frame.restype = ctypes.c_int
        h.clear_frames.argtypes = []
        h.clear_frames.restype = None
        h.recognise_frame.argtypes = [ctypes.c_char_p]
        h.recognise_frame.restype = ctypes.c_void_p
        h.free_cstring.argtypes = [ctypes.c_void_p]
        h.free_cstring.restype = None
        _lib = h
    except OSError:
        _lib = None
    return _lib


def is_available() -> bool:
    """True iff the Rust runner can be delegated to."""
    return _lib_handle() is not None


def clear() -> None:
    """Clear the process-global Rust frame store."""
    h = _lib_handle()
    if h is not None:
        h.clear_frames()


def install(spec: dict) -> bool:
    """Install a frame into the Rust store. ``spec`` matches the FrameSpec
    schema the .so expects (see runners/rust/src/lib.rs). Returns True on
    success."""
    h = _lib_handle()
    if h is None:
        return False
    rc = h.install_frame(json.dumps(spec).encode())
    return rc == 0


def recognise(question_text: str, agent_scope: list) -> "tuple | None":
    """Delegate recognition to the Rust runner. ``agent_scope`` is the
    pre-flattened Mt closure (matches what the Python recogniser computes
    via ``_agent_scope_mts``). Returns ``(frame_id_int, slots_dict, fok)``
    or None when no Frame matched."""
    h = _lib_handle()
    if h is None:
        return None
    req = {"question_text": question_text,
           "agent_scope": agent_scope,
           "mt_genl_table": {}}
    p = h.recognise_frame(json.dumps(req).encode())
    if not p:
        return None
    body = ctypes.c_char_p(p).value
    h.free_cstring(p)
    if body is None:
        return None
    data = json.loads(body.decode())
    if data is None:
        return None
    # Rust serialises Value as {"kind": "Int" | "Str", "v": ...}; unwrap.
    slots = {k: v["v"] for k, v in data["slots"].items()}
    return data["frame_id"], slots, data["fok"]
