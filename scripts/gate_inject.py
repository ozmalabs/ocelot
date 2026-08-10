"""gate_inject — ESTABLISH A GATE'S PROPERTIES BY CONSTRUCTION, NEVER BY READING.

PROTOCOL §1 (gate the measure before the agent), §12 (a selector that matches by
substring is not a selector), §13 (magic numbers fall OUT).

WHY THIS EXISTS
---------------
Five AST/§13 gates in this tree have failed, each found by accident by the rung
that tripped over it: red on a DOCSTRING; array indices counted as thresholds;
a selector that located by substring and selected the wrong subtree (so the
supervisor's own injection test PASSED when it should have FAILED); a §13
threshold closed BY NAMING IT; and a substring assertion that MATCHED ITSELF,
inside the test written to warn about substring selectors.

The common thread is that every one of them was believed correct because it was
READ and it looked right. So this harness never reads. It plants a defect,
verifies the plant LANDED where the gate claims to look, runs the gate, and
records whether it reddened.

THE THREE OUTCOMES, and only the first is a working gate:

  ALIVE      plant -> RED, revert -> GREEN.
  INERT      plant -> GREEN. The gate has never been ABLE to fail. Three
             provenance gates in this tree sat green for 51 commits in exactly
             this state, then all fired at once as false accusations.
  MISLANDED  the plant did not end up inside the region the gate selects. The
             run is VOID -- neither alive nor inert -- and reporting it either
             way is the defect this harness exists to catch. A gate is only
             INERT once its defect has been shown to LAND.

The MISLANDED outcome is the whole point of `verify_lands`. Without it an
injection test that silently misses reports GREEN and is read as "the gate is
fine", which is precisely how failure #3 happened.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from contextlib import contextmanager

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


@contextmanager
def planted(relpath: str, old: str, new: str, *, count: int = 1):
    """Textually plant `new` in place of `old`, yield, then ALWAYS restore the
    original bytes -- restoration is in a `finally`, so a gate that raises, a
    pytest that segfaults or a KeyboardInterrupt cannot leave a defect in the
    tree. Verifies the anchor is unique-enough before writing: a plant that
    matched more sites than intended is a different experiment than the one
    being reported."""
    path = os.path.join(ROOT, relpath)
    with open(path, encoding="utf-8") as fh:
        original = fh.read()
    found = original.count(old)
    if found != count:
        raise AssertionError(
            f"plant anchor is not unique in {relpath}: expected {count} "
            f"occurrence(s) of {old!r}, found {found}. A plant that lands in "
            f"an unexpected number of places is not the experiment claimed.")
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(original.replace(old, new, count))
        yield path
    finally:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(original)


def verify_lands(relpath: str, marker: str, region: tuple[int, int] | None = None) -> bool:
    """Did the plant land where the gate looks? `marker` must be present, and --
    when the gate selects a line range -- inside it. Returns False for MISLANDED.

    This is the check whose absence made a supervisor's injection test pass when
    it should have failed: the injection went into the file, the gate looked at a
    different subtree, and 'green' was read as 'the code is clean'."""
    path = os.path.join(ROOT, relpath)
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    hits = [i + 1 for i, ln in enumerate(lines) if marker in ln]
    if not hits:
        return False
    if region is None:
        return True
    lo, hi = region
    return any(lo <= h <= hi for h in hits)


def run_gate(nodeid: str, timeout: int = 600) -> tuple[bool, str]:
    """Run one pytest node id. Returns (passed, tail-of-output).

    Uses an explicit node id -- never `-k`. §12: `-k` is a substring match, not
    a namespace, and this tree has already reported four different baselines
    because of it."""
    proc = subprocess.run(
        [sys.executable, "-W", "ignore", "-m", "pytest", "-q", "-x", "--no-header", nodeid],
        cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return proc.returncode == 0, (proc.stdout + proc.stderr)[-2500:]


def probe(nodeid: str, relpath: str, old: str, new: str, marker: str,
          region: tuple[int, int] | None = None) -> dict:
    """One full by-construction probe of one gate against one planted defect.

    Order matters and is not negotiable: baseline GREEN first (a gate already
    red proves nothing about the plant), then plant, then verify the plant
    LANDED, then run. A plant that did not land yields VOID, never INERT."""
    base_ok, base_out = run_gate(nodeid)
    if not base_ok:
        return {"verdict": "BASELINE-RED", "detail": base_out}
    with planted(relpath, old, new):
        landed = verify_lands(relpath, marker, region)
        ok, out = run_gate(nodeid)
    if not landed:
        return {"verdict": "VOID-MISLANDED",
                "detail": f"marker {marker!r} not found in region {region}"}
    return {"verdict": "ALIVE" if not ok else "INERT", "detail": out if not ok else ""}
