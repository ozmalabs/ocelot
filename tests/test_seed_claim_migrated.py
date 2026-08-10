"""READ-SIDE ENFORCEMENT for the burned-seed ledger — the standing gate.

`test_seed_accounting_migrated.py` gates the WRITE side: does a runner stay
inside the block it DECLARED? That assertion needs a declaration to check
against, so it is structurally blind to the ledger's dominant defect — a block
consumed with NO declaration at all.

This module gates the READ side. Two things run here:

  1. THE CLAIM CHECK is alive -- positive-controlled on REAL TREE DATA, not a
     plant. `scripts/det1_measure.py` and `scripts/continuous_pose_measure.py`
     really did consume 38000-38099 and 40000-40099 without ever declaring
     them, and the checker really refuses those ranges while a ledger-only
     check calls them FREE. Per VISION_PROTOCOL.md §1.1 and §12, a checker that
     finds nothing and a clean tree are indistinguishable; this is the evidence
     the instrument can fire.

  2. UNDECLARED CONSUMPTION DOES NOT GROW. A frozen baseline of every
     ledger-scale seed run in this tree that falls in no declared block. A new
     entry means a rung consumed seeds without a §11 row -- exactly the defect
     that produced 38000 and 40000 -- and the failure message says what to do.

BOTH CAVEATS ARE ASSERTED AS PROPERTIES OF THE OUTPUT TEXT, not left to prose:
the seed-INTEGER unit, and that a clean result means "no collision DETECTED",
never "no collision exists".
"""
from __future__ import annotations

import os
import sys
import textwrap

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from seed_claim import (  # noqa: E402
    check_claim,
    claim_report,
    first_clean_subrange,
    undeclared_runs,
)
from seed_ledger_audit import parse_ledger  # noqa: E402

# --- the two undeclared blocks, as the seed-accounting rung found them -------
UNDECLARED_BLOCKS = [
    (38000, 38099, "scripts/det1_measure.py"),
    (40000, 40099, "scripts/continuous_pose_measure.py"),
]

# --- namespaces that are DELIBERATELY outside the ledger ---------------------
# Recommendation 5 of VISION_SEED_ACCOUNTING_RESULTS.md: date literals and
# conventional magic constants are a separate convention, not ledger draws, and
# a collision check should not chase them.
DATE_LITERAL_FLOOR = 20_000_000
CONVENTIONAL_MAGIC = {1234, 12345, 1451, 2024, 2026, 2748, 3243, 3567,
                      789996, 12648430}

# --- THE FROZEN BASELINE ----------------------------------------------------
# Every ledger-scale run measured OUTSIDE every declared block at
# 0d7dbef5d1782f067baea3a77153135e8cf254b5. Each entry is a real accounting
# gap; the gate exists so the LIST DOES NOT GROW, not because the list is fine.
KNOWN_UNDECLARED = {
    (1000, 1019):    "tests/test_vision_maps_migrated.py -- below the ledger's "
                     "lowest declared block (1100); ambiguous, predates the "
                     "ledger convention.",
    (38000, 38099):  "scripts/det1_measure.py -- REAL undeclared block. §11 "
                     "row recommended by the seed-accounting rung, NOT YET "
                     "APPLIED.",
    (40000, 40019):  "scripts/continuous_pose_measure.py + its own gate test "
                     "-- REAL undeclared block. §11 row recommended, NOT YET "
                     "APPLIED.",
    (40020, 40099):  "scripts/continuous_pose_measure.py -- same block, split "
                     "here because the drawing file-set changes at 40020.",
    (90000, 90002):  "scripts/rung7_snr_pilot.py -- undeclared, and it sits "
                     "inside the block 90000-90999 allocated to the seed-claim "
                     "rung. Found BY this tool, on its first real use.",
    (99991, 99991):  "scripts/self_directed_speech_loop.py -- one seed above "
                     "the ledger's top.",
    (100003, 100003): "scripts/jabberwock_handwriting_feasibility.py -- one "
                      "seed above the ledger's top.",
}


def _ledger_scale(runs):
    """Drop the two deliberate non-ledger namespaces."""
    out = []
    for r in runs:
        if r["lo"] >= DATE_LITERAL_FLOOR:
            continue
        if r["n"] == 1 and r["lo"] in CONVENTIONAL_MAGIC:
            continue
        out.append(r)
    return out


# --- 1. POSITIVE CONTROL ON REAL DATA ---------------------------------------

@pytest.mark.parametrize("lo,hi,runner", UNDECLARED_BLOCKS)
def test_claim_check_refuses_the_known_undeclared_blocks(lo, hi, runner):
    """THE POSITIVE CONTROL, and it fires on history rather than a plant."""
    if not os.path.exists(os.path.join(ROOT, runner)):
        pytest.skip(f"{runner} absent from this tree")
    ok, report = check_claim(lo, hi)
    assert not ok, (
        f"claim check went QUIET on {lo}-{hi}, which "
        f"{runner} measurably consumes. The instrument is dead."
    )
    rep = claim_report(lo, hi)
    assert rep["occupied_count"] == 100
    assert runner in rep["occupying_files"]
    assert runner in report


@pytest.mark.parametrize("lo,hi,runner", UNDECLARED_BLOCKS)
def test_a_ledger_only_check_calls_those_same_blocks_free(lo, hi, runner):
    """WHY THIS TOOL EXISTS: the ledger cannot see either block.

    If this ever fails because a §11 row was added, that is the defect being
    FIXED -- update UNDECLARED_BLOCKS and KNOWN_UNDECLARED together.
    """
    blocks = parse_ledger()[0]
    overlapping = [(b_lo, b_hi) for b_lo, b_hi, _ in blocks
                   if b_lo <= hi and lo <= b_hi]
    assert overlapping == [], (
        f"{lo}-{hi} is now DECLARED at {overlapping}. The ledger-blindness this "
        f"gate documents has been fixed; update the baseline."
    )


# --- 2. PLANTED CONTROL: the checker responds to a NEW draw ------------------

def test_planted_draw_flips_a_clean_range_and_removal_restores_it(tmp_path):
    """§1.1: show the detector both FIRES and GOES QUIET."""
    roots = (str(tmp_path),)
    lo, hi = 90500, 90599

    ok, _ = check_claim(lo, hi, roots=roots, consult_ledger=False, refresh=True)
    assert ok, "empty directory must read CLEAN before the plant"

    planted = tmp_path / "planted_rung.py"
    planted.write_text(textwrap.dedent(
        """
        import random
        BASE = 90000          # never appears as the string 90540 anywhere
        def run():
            for t in range(60):
                random.Random(BASE + 500 + t)
        """
    ))
    ok, report = check_claim(lo, hi, roots=roots, consult_ledger=False,
                            refresh=True)
    assert not ok, "planted draw into 90500-90559 was NOT detected"
    rep = claim_report(lo, hi, roots=roots, consult_ledger=False)
    assert 90540 in rep["occupied_seeds"], (
        "the seed must be recovered through BASE + 500 + t, not by matching "
        "the literal -- no substring selector would find it (§12)"
    )
    assert "planted_rung.py" in report

    planted.unlink()
    ok, _ = check_claim(lo, hi, roots=roots, consult_ledger=False, refresh=True)
    assert ok, "removing the plant must restore CLEAN"


def test_a_verified_clean_range_reads_clean():
    """Negative control: the checker is not simply always-red."""
    ok, report = check_claim(90003, 90102)
    assert ok, report


# --- 3. THE STANDING ENFORCEMENT --------------------------------------------

def test_undeclared_consumption_does_not_grow():
    """A rung that consumes seeds without a §11 row fails HERE, not never."""
    runs = _ledger_scale(undeclared_runs())
    found = {(r["lo"], r["hi"]): r for r in runs}
    new = sorted(set(found) - set(KNOWN_UNDECLARED))
    assert not new, (
        "NEW UNDECLARED SEED CONSUMPTION -- seeds are drawn in these ranges and "
        "no VISION_PROTOCOL.md §11 row declares them:\n"
        + "\n".join(
            f"  {lo}-{hi}  n={found[(lo, hi)]['n']}  "
            f"{', '.join(found[(lo, hi)]['files'])}" for lo, hi in new)
        + "\n\nThis is the defect that produced 38000-38099 and 40000-40099: a "
          "correct free-range check that was never written down. FIX by adding "
          "the §11 ledger row (the supervisor owns that file), then adding the "
          "range to KNOWN_UNDECLARED here in the SAME commit as the runner.\n"
          "\nIf the runner and its §11 row land in different commits this gate "
          "fires on the gap. That is a true positive about ordering, not a "
          "false accusation.\n"
        + "\nCAVEAT 1 -- the unit is the SEED INTEGER, not consecutive draws "
          "from one generator.\nCAVEAT 2 -- this measurement UNDER-REPORTS by "
          "design; a clean result means NO COLLISION DETECTED, never NO "
          "COLLISION EXISTS."
    )


def test_the_baseline_is_not_stale():
    """A baseline entry that no longer measures is itself a defect.

    Without this, KNOWN_UNDECLARED silently becomes a graveyard and the gate
    above weakens every time a runner is deleted.
    """
    found = {(r["lo"], r["hi"]) for r in _ledger_scale(undeclared_runs())}
    gone = sorted(set(KNOWN_UNDECLARED) - found)
    assert not gone, (
        "baseline entries no longer measured (runner deleted, or a §11 row was "
        f"added): {gone}. Remove them from KNOWN_UNDECLARED."
    )


# --- 4. THE CAVEATS ARE PROPERTIES OF THE OUTPUT, NOT PROSE -----------------

@pytest.mark.parametrize("lo,hi,expect_ok", [
    (90003, 90102, True),    # clean verdict
    (38000, 38099, False),   # refused verdict
])
def test_both_caveats_are_carried_into_every_verdict(lo, hi, expect_ok):
    ok, report = check_claim(lo, hi)
    assert ok is expect_ok
    assert "SEED INTEGER" in report, "caveat 1 (unit) missing from the verdict"
    assert "UNDER-REPORTS BY DESIGN" in report, "caveat 2 missing"
    assert "NEVER 'NO COLLISION EXISTS'" in report, (
        "the verdict must refuse to let a reader read CLEAN as proof of absence"
    )
    assert "UNRESOLVED sink sites" in report, (
        "the silence must be priced: report how much the tool could not resolve"
    )


def test_a_clean_verdict_still_reports_unresolved_sinks():
    """The vacuous-instrument guard: CLEAN must never be bare."""
    rep = claim_report(90003, 90102)
    assert rep["clean"]
    assert rep["unresolved_sinks_in_tree"] > 0, (
        "zero unresolved sinks tree-wide would mean the scanner is not running"
    )
    assert rep["files_scanned"] > 100


# --- 5. THE LEDGER ADVISORY ARM AND THE RECOVERY PATH -----------------------

def test_a_declared_block_is_refused_even_at_zero_measured_consumption():
    """58 of 108 declared blocks measure zero. They are still reservations."""
    blocks = parse_ledger()[0]
    zero_declared = None
    for lo, hi, _ in blocks:
        rep = claim_report(lo, hi, consult_ledger=False)
        if rep["occupied_count"] == 0:
            zero_declared = (lo, hi)
            break
    assert zero_declared is not None, (
        "expected at least one declared-but-unmeasured block (the audit found "
        "58); if none remain the advisory arm is untestable here"
    )
    ok, report = check_claim(*zero_declared)
    assert not ok, (
        f"{zero_declared} measures zero but IS declared -- claiming it must "
        f"still be refused, because measuring zero does not mean drawing "
        f"nothing (caveat 1)"
    )
    assert "DECLARED ELSEWHERE" in report


def test_first_clean_subrange_skips_the_occupied_head():
    """The recovery path, exercised on the real case this rung hit."""
    sub = first_clean_subrange(90000, 90999, 100)
    assert sub is not None
    assert sub[0] > 90002, (
        f"90000-90002 is consumed by rung7_snr_pilot.py; a clean sub-range "
        f"must start after it, got {sub}"
    )
    ok, report = check_claim(*sub)
    assert ok, report
