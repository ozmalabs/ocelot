"""OPTIONAL DEPENDENCIES ARE SKIPS, NOT REDS — and the marker says which.

WHY THIS EXISTS (red-test triage, 2026-08-12). A red baseline is only useful if
every entry in it is something a reader has to ACT on. An entry that means
"opencv is not installed in this environment" is not that: it forces the same
re-diagnosis in every rung, forever, and — measured at `d239b7c` — it was
**76 node ids across 25 files**, the second-largest red class in the tree,
every one of them a capability that is UNTESTED here rather than BROKEN here.

The distinction this file draws, and it is the whole point:

  * a HARD dependency that is missing is a RED. Nothing here touches those.
  * a DECLARED-OPTIONAL dependency that is missing is a SKIP, with a reason
    naming the requirements file that declares it — so the reader knows the
    capability was not measured, and knows exactly how to measure it.

The optional set is an ALLOWLIST, not a catch-all: only a module this repo
actually declares in a `requirements-*.txt` extra (or ships as an explicitly
optional world adapter) may be skipped. A `ModuleNotFoundError` for anything
NOT on this list stays a red, because that one really is a defect.

Deliberately NOT a `conftest.py` exception hook. Converting any import error
into a skip at collection time would hide the real ones too — the failure mode
CLAUDE.md's own 2026-07-21 retraction warns about (a status line that becomes
reusable as an excuse). Every skip in this tree is written at its site, by
name, and is visible in the diff that added it.
"""
from __future__ import annotations

import importlib.util

import pytest

# module -> where the repo DECLARES it. If it is not declared somewhere, it is
# not optional, and it does not belong here.
OPTIONAL = {
    "cv2": "requirements-arc.txt (opencv-python-headless)",
    "matplotlib": "plotting-only dependency of the scripts/*_measure.py figure path",
    "scipy": "optional numerics dependency of the pen/ink corpora loaders",
    "av": "PyAV — optional container/codec dependency of the audio world adapter",
    "pybullet": "requirements-robot.txt (6-DoF physics world)",
    "vizdoom": "optional DOOM world adapter dependency",
    "torch": "optional dependency of the published-model probes",
    "whisper": "optional dependency of the published-model probes",
    "tree_sitter_rust": "optional dependency of the Rust/Lua program reader",
    "tree_sitter_lua": "optional dependency of the Rust/Lua program reader",
}


def have(module: str) -> bool:
    """Is `module` importable? Mechanical probe, never raises."""
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def requires(module: str):
    """A skip marker for a DECLARED-OPTIONAL dependency.

    Raises on an undeclared module rather than silently granting a skip — a
    marker that can excuse anything is the count-shaped defect again."""
    if module not in OPTIONAL:
        raise KeyError(
            f"{module!r} is not a declared-optional dependency of this repo. "
            "A missing hard dependency is a RED, not a skip. If it really is "
            f"optional, declare it in tests/optional_deps.OPTIONAL with the "
            "requirements file that ships it.")
    return pytest.mark.skipif(
        not have(module),
        reason=f"optional dependency {module!r} absent ({OPTIONAL[module]}). "
               "The capability is UNTESTED here, not broken.")


def importorskip(module: str):
    """Module-level form, for a file whose EVERY test needs the dependency."""
    if module not in OPTIONAL:
        raise KeyError(f"{module!r} is not a declared-optional dependency")
    if not have(module):
        pytest.skip(f"optional dependency {module!r} absent ({OPTIONAL[module]}). "
                    "The capability is UNTESTED here, not broken.",
                    allow_module_level=True)
