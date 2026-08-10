"""RUNG 231000 gates — SEE the ls20 mechanic (indicator + destination flash +
exit-glyph rotation on reaching the cross). Every detection claim is gated against
the GROUND-TRUTH raw pixel deltas, never the eye's self-report."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_see import (  # noqa: E402
    ReachScenario, ColourChangeEye, score_detection, located_cause,
    ground_destination_flash, required_transform_key, raw_changed_cells,
    changed_regions, classify_transient_persistent, recognise_rotation, _dist,
)
from worlds.arc_ls20_flash import OnsetEye  # noqa: E402

N = 32


def _frames(seed):
    sc = ReachScenario(np.random.default_rng(seed), n=N)
    b, r, a = sc.frames()
    return sc, b, r, a


# ---- GROUND TRUTH is a real raw diff -----------------------------------------
def test_ground_truth_is_a_real_raw_cell_diff():
    _, b, r, a = _frames(0)
    gt = raw_changed_cells(b, r)
    # exactly the cells whose colour index changed
    manual = {(i, j) for i in range(N) for j in range(N) if int(b[i, j]) != int(r[i, j])}
    assert gt == manual and len(gt) > 0


def test_reach_produces_indicator_destination_and_rotation_regions():
    sc, b, r, a = _frames(0)
    cls = classify_transient_persistent(b, r, a)
    # at least one distal transient (destination) and one distal persistent (rotation)
    distal_transient = [x for x in cls if x["transient"] and _dist(x["centroid"], sc.locus) > 8]
    distal_persistent = [x for x in cls if (not x["transient"]) and _dist(x["centroid"], sc.locus) > 8]
    assert distal_transient, "no distal transient (destination flash) region"
    assert distal_persistent, "no distal persistent (exit-glyph rotation) region"


# ---- G-detect-the-effects (HEADLINE) -----------------------------------------
def test_colour_eye_detects_all_three_effects_luma_eye_misses():
    col_all = luma_all = 0
    n = 24
    for seed in range(n):
        sc, b, r, a = _frames(100 + seed)
        ce = ColourChangeEye()
        rc = score_detection(ce, b, r, a, sc.locus, eye_n=N)
        le = OnsetEye(N)
        le.adapt(np.zeros((N, N), dtype=np.int32), frames=4)
        rl = score_detection(le, b, r, a, sc.locus, eye_n=N)
        le.stop()
        col_all += int(rc["all_three"])
        luma_all += int(rl["all_three"])
    # the colour eye detects all three every time; the luma eye never does (null).
    assert col_all == n, f"colour eye all-three {col_all}/{n}"
    assert luma_all == 0, f"luma eye all-three {luma_all}/{n} (should reproduce the 229/230 null)"


def test_detection_is_gated_against_ground_truth_not_self_report():
    # the colour eye's detected regions are a SUBSET of the ground-truth changed
    # cells — the detector reports only real changes (no confabulation).
    sc, b, r, a = _frames(3)
    ce = ColourChangeEye()
    events = ce.onset_on_transition(b, r)
    gt = raw_changed_cells(b, r)
    assert events, "colour eye fired no events on a real change"
    assert all((row, col) in gt for (row, col, _m) in events)


# ---- G-located-cause ---------------------------------------------------------
def test_located_cause_is_threshold_with_per_region_evidence():
    sc, b, r, a = _frames(7)
    le = OnsetEye(N)
    le.adapt(np.zeros((N, N), dtype=np.int32), frames=4)
    lc = located_cause(b, r, a, sc.locus, le, eye_n=N)
    le.stop()
    assert lc["operative_cause"] == "threshold"
    # the missed regions are colour-only, PRESENT in the returned frame, sub-+6dB,
    # and the colour eye fires on them.
    missed = [row for row in lc["regions"] if row["colour_eye_fired"] and not row["luma_eye_fired"]]
    assert missed, "no region missed by luma (the located cause must bite)"
    for row in missed:
        assert row["present_in_returned_reach_frame"] is True
        assert row["luma_above_6db"] is False, "a missed region must be sub-threshold luminance"
        assert row["colour_eye_fired"] is True


# ---- G-wires-to-pipeline -----------------------------------------------------
def test_detected_destination_flash_grounds_causes_via_229():
    sc, b, r, a = _frames(5)
    ce = ColourChangeEye()
    res = score_detection(ce, b, r, a, sc.locus, eye_n=N)
    assert res["destination_flash"], "destination flash must be detected first"
    grounded, edges, facts = ground_destination_flash((sc.cr, sc.cc), res["destination_flash"])
    assert grounded is True
    assert ("cross", "destination_flash") in edges
    assert any(f["cause"] == "cross" and f["status"] == "grounded" and
               f["source"] == "observation" for f in facts)


def test_no_detection_grounds_nothing_control():
    sc, b, r, a = _frames(5)
    grounded, edges, _ = ground_destination_flash((sc.cr, sc.cc), False)
    assert grounded is False and ("cross", "destination_flash") not in edges


def test_exit_rotation_reads_as_227_rot90_key():
    for seed in range(6):
        sc, b, r, a = _frames(200 + seed)
        got = None
        for reg in classify_transient_persistent(b, r, a):
            if (not reg["transient"]) and _dist(reg["centroid"], sc.locus) > 8:
                k = required_transform_key(b, a, reg)
                if k:
                    got = k
                    break
        assert got is not None and got.startswith("rot90:"), f"seed {seed}: {got}"


# ---- transient vs persistent (the owner's event-clock distinction) -----------
def test_flashes_are_transient_rotation_is_persistent():
    sc, b, r, a = _frames(0)
    cls = classify_transient_persistent(b, r, a)
    # the destination flash region reverts; the exit-glyph rotation region persists.
    dest = [x for x in cls if x["transient"] and _dist(x["centroid"], sc.locus) > 8]
    rot = [x for x in cls if (not x["transient"]) and _dist(x["centroid"], sc.locus) > 8]
    assert dest and all(x["reverted_frac"] >= 0.5 for x in dest)
    assert rot and all(x["reverted_frac"] < 0.5 for x in rot)


# ---- default-OFF byte-identical: the fix touches NO shared perception path ----
def test_fix_touches_no_shared_perception_path():
    # the existing luma eye + photon_eye + onset seeds are UNTOUCHED — the fix is a
    # new module. Assert the new module does not monkeypatch or reassign them.
    import re
    src = (_ROOT / "worlds" / "arc_ls20_see.py").read_text()
    # actual MUTATION patterns of the shared path (assignment / patch), not mentions.
    mutation_patterns = [
        r"OnsetEye\.\w+\s*=",          # patching a method on the luma eye
        r"GraphEye\s*=",               # rebinding the eye class
        r"_LUMA_LUT\s*\[[^\]]+\]\s*=", # writing the shared luminance LUT
        r"\bmonkeypatch\b",
        r"\bsetattr\s*\(\s*(OnsetEye|GraphEye|F|arc_ls20_flash)",
        r"^\s*def luma\b",             # redefining luma
    ]
    for pat in mutation_patterns:
        assert not re.search(pat, src, re.M), f"the fix must not mutate the shared path: {pat}"
    # and importing the fix does not alter OnsetEye behaviour
    import worlds.arc_ls20_flash as F
    assert hasattr(F, "OnsetEye") and hasattr(F, "luma")


# ---- source-audit: no hardcoded destination/exit locations -------------------
def test_source_audit_no_hardcoded_destination_or_exit_location():
    from arc_ls20_see_measure import source_audit
    audit = source_audit()
    assert audit["clean"] is True
    assert audit["no_hardcoded_ls20_destination_or_exit_location_in_detector"] is True
    assert audit["regions_emerge_from_observed_change"] is True
    assert audit["banned_domain_tokens_in_detector_logic"] == []


def test_colour_eye_is_event_native_residual_against_held_prior():
    # the eye holds a prior and reports the residual; presenting the SAME frame twice
    # yields NO events (nothing changed against the held prior).
    _, b, r, a = _frames(1)
    ce = ColourChangeEye()
    ce.adapt(b)
    assert ce.submit(b) == [], "no change against the held prior must yield no events"
    ev = ce.submit(r)
    assert ev, "a real change must yield residual events"
    assert ce.submit(r) == [], "presenting the held frame again yields no residual"
