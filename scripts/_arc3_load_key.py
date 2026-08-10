"""_arc3_load_key — load ARC_API_KEY from the gitignored .env into os.environ
WITHOUT surfacing the value anywhere.

This is a transport-only helper for the LIVE ARC-3 driver. It reads the key
solely so ``arc3_live_env`` can pick it up from ``os.environ['ARC_API_KEY']``.
The value is NEVER printed, logged, returned, or written to any file. The only
thing this module exposes is a boolean / length for a presence check.

NO substrate dependency, NO agent code — pure environment plumbing.
"""
from __future__ import annotations

import os
from pathlib import Path

# The gitignored secrets file. Relative to this experiment's repo so the loader
# works regardless of CWD. (.../internal/.env)
_ENV_PATH = Path("/home/matt/ozma/internal/.env")


def load_arc_api_key() -> bool:
    """Read ARC_API_KEY from the gitignored .env into os.environ if not already
    present. Returns True iff the key is present in the environment afterwards.
    NEVER returns or prints the value."""
    if os.environ.get("ARC_API_KEY"):
        return True
    if not _ENV_PATH.exists():
        return False
    for raw in _ENV_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        if name == "ARC_API_KEY":
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ["ARC_API_KEY"] = value
            break
    return bool(os.environ.get("ARC_API_KEY"))


__all__ = ["load_arc_api_key"]
