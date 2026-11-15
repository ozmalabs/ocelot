"""Compatibility shims for the dev tooling that moved to ozagia.

The graph dev tooling (dev memory, repo map, code search, symbol graph, edits,
LSP bridge, MCP server, evals) now lives in the ozagia package
(https://github.com/ozmalabs/ozagia), installed into this venv. Each old
`scripts/ocelot_*.py` module is a two-line shim that calls `alias`, so
imports, `python -m scripts.ocelot_*` commands and MCP registrations that name
the old modules keep working.

Before ozagia is imported, `alias` maps the old environment variables to the
new names (an explicit new name wins) and points OZAGIA_ROOT at this checkout,
so the tools act on Ocelot as before. Ocelot's layout and its seed adapter come
from `.ozagia.toml`.
"""
from __future__ import annotations

import importlib
import os
import runpy
import sys
from pathlib import Path

OCELOT_ROOT = Path(__file__).resolve().parents[1]

_ENV = {
    "OCELOT_DEV_ROOT": "OZAGIA_ROOT",
    "OCELOT_DEV_DUMP": "OZAGIA_DUMP",
    "OCELOT_DEV_JOURNAL": "OZAGIA_JOURNAL",
    "OCELOT_DEV_AUTOBUILD": "OZAGIA_AUTOBUILD",
    "OCELOT_INDEX_WORKERS": "OZAGIA_INDEX_WORKERS",
    "OCELOT_LIVE_LSP": "OZAGIA_LIVE_LSP",
    "OCELOT_AGENT_EVAL_LIVE": "OZAGIA_EVAL_LIVE",
    "OCELOT_AGENT_EVAL_DRIVER": "OZAGIA_EVAL_DRIVER",
}


def _map_env() -> None:
    for old, new in _ENV.items():
        if old in os.environ and new not in os.environ:
            os.environ[new] = os.environ[old]
    os.environ.setdefault("OZAGIA_ROOT", str(OCELOT_ROOT))


def alias(name: str, target: str) -> None:
    """Make module `name` be ozagia module `target`.

    Imported: `sys.modules[name]` becomes the ozagia module, private names
    included. Run with `python -m`: the ozagia module runs as `__main__`.
    """
    _map_env()
    if name == "__main__":
        sys.argv[0] = target
        runpy.run_module(target, run_name="__main__", alter_sys=True)
        return
    sys.modules[name] = importlib.import_module(target)
