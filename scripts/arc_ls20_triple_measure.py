"""arc_ls20_triple_measure — RUNG 232000 powered offline gates.

Proves the RESIDUAL-AFTER-EXPLAINING-THE-AVATAR mechanism decisively on a
synthetic ls20-shaped reach (avatar approach + on-cell reach + the three effects),
every claim gated against the GROUND-TRUTH raw cell-diff, with Wilson 95% CIs and
CI-separated controls:

  · G-isolate-triple      — the residual isolates all three effects AND excludes the
                            avatar; the NO-EXPLANATION control (raw before->reach
                            diff) always contains the avatar (the confound).
  · G-residual-explains-avatar — residual ∩ avatar_explained_cells == 0 (the tracker's
                            translate accounts for the avatar), non-trivially (the
                            prediction actually moved the avatar); raw diff contains it.
  · G-rotation-recognised — the isolated distal-persistent region reads as rot90:k
                            (227 UNCHANGED), matching the ground-truth k; a near-miss
                            (no effect) control reads nothing.
  · G-reach-certified     — on-cell reach certifies the triple; a NEAR-MISS (avatar
                            one hop short, effects absent) does NOT.

Run: PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_triple_measure.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from arc_ls20_see_measure import wilson, sep  # reuse 231's exact CI helpers  # noqa: E402
from worlds.arc_ls20_triple import (  # noqa: E402
    TripleReachScenario, learn_and_isolate, raw_diff_isolation, isolate_triple,
)
from worlds.arc_ls20_percell_track import LiveObjectTracker  # noqa: E402
from worlds.arc_ls20_percell import Percell  # noqa: E402

_BASE = 232000
_N = 64


def _drive(seed, near_miss=False):
    """Build the scenario, learn the avatar shift from the approach, and isolate the
    triple on the reach (residual) + the raw-diff control. Returns everything the
    gates need."""
    sc = TripleReachScenario(np.random.default_rng(seed), near_miss=near_miss)
    ag = Percell()
    tr = LiveObjectTracker(ag)
    frames = sc.approach()
    for i in range(len(frames) - 1):
        tr.observe(frames[i], frames[i + 1], "move_down")
    before, reach, after = sc.frames()
    iso = isolate_triple(before, reach, after, tr, "move_down", sc.locus)
    raw = raw_diff_isolation(before, reach, after, sc.locus)
    return sc, iso, raw


def isolate_triple_gate():
    clean = 0                 # residual: all three isolated + excludes avatar + subset
    raw_excludes_avatar = 0   # control: does the RAW diff exclude the avatar? (want 0)
    for seed in range(_BASE, _BASE + _N):
        sc, iso, raw = _drive(seed)
        subset = (sc.effect_gt["indicator"] <= iso["residual_cells"] and
                  sc.effect_gt["destination"] <= iso["residual_cells"] and
                  sc.effect_gt["rotation"] <= iso["residual_cells"])
        if (iso["all_three"] and iso["residual_excludes_avatar"] and subset and
                iso["avatar_cells"] == sc.avatar_gt):
            clean += 1
        # the control: the raw diff "excludes the avatar" iff the avatar cells are
        # NOT in it — which never happens (the avatar move IS in the raw diff).
        if not (sc.avatar_gt <= raw["changed_cells"]):
            raw_excludes_avatar += 1
    res_ci = wilson(clean, _N)
    ctl_ci = wilson(raw_excludes_avatar, _N)
    return {
        "n": _N,
        "residual_clean_isolate_all_three_rate": res_ci,
        "raw_diff_excludes_avatar_rate (NO-EXPLANATION control, want 0)": ctl_ci,
        "ci_separated": sep(res_ci, ctl_ci),
        "note": "clean = residual contains all three effect regions (subset of the "
                "ground-truth effect cells) AND excludes every avatar cell AND the "
                "avatar footprint equals the ground truth. The control uses the raw "
                "before->reach diff, which always contains the avatar (the confound).",
    }


def residual_explains_avatar_gate():
    residual_excludes = 0     # residual ∩ avatar == 0, non-trivially (avatar predicted)
    raw_excludes = 0          # raw diff excludes avatar? (want 0)
    overlaps = []
    for seed in range(_BASE, _BASE + _N):
        sc, iso, raw = _drive(seed)
        nontrivial = (len(iso["avatar_cells"]) > 0 and iso["avatar_cells"] == sc.avatar_gt)
        if nontrivial and iso["avatar_overlap"] == 0:
            residual_excludes += 1
        overlaps.append(iso["avatar_overlap"])
        if not (sc.avatar_gt <= raw["changed_cells"]):
            raw_excludes += 1
    res_ci = wilson(residual_excludes, _N)
    ctl_ci = wilson(raw_excludes, _N)
    return {
        "n": _N,
        "residual_excludes_avatar_nontrivial_rate": res_ci,
        "raw_diff_excludes_avatar_rate (control, want 0)": ctl_ci,
        "mean_residual_avatar_overlap": float(np.mean(overlaps)),
        "ci_separated": sep(res_ci, ctl_ci),
        "note": "'non-trivial' = the tracker's translate ACTUALLY predicted the "
                "avatar (avatar_cells == ground-truth avatar footprint, non-empty), "
                "so residual ∩ avatar == 0 is a real confound-removal, not a vacuous "
                "empty-prediction pass. The confound is removed by PREDICTION.",
    }


def rotation_recognised_gate():
    keyed = 0                 # residual distal-persistent region reads rot90:k == sc.k
    control = 0               # near-miss (no effect) reads a rotation (want 0)
    for seed in range(_BASE, _BASE + _N):
        sc, iso, _raw = _drive(seed)
        if iso["rotation_key"] == f"rot90:{sc.k}":
            keyed += 1
        sc2, iso2, _r2 = _drive(seed, near_miss=True)
        if iso2["exit_rotation"]:
            control += 1
    ci = wilson(keyed, _N)
    ctl = wilson(control, _N)
    return {
        "n": _N,
        "rotation_read_as_rot90_k_matching_ground_truth_rate": ci,
        "near_miss_reads_a_rotation_rate (NO-DETECTION control, want 0)": ctl,
        "ci_separated": sep(ci, ctl),
        "note": "the ISOLATED exit-glyph rotation reads as rot90:k via 227's "
                "UNCHANGED _recognise_transform (through 231's recognise_rotation), "
                "matching the ground-truth k — the transform 231 could not recognise "
                "because it was not isolated.",
    }


def reach_certified_gate():
    on_cell = 0               # on-cell reach certifies the triple
    near_miss = 0             # near-miss falsely certifies (want 0)
    for seed in range(_BASE, _BASE + _N):
        _sc, iso, _raw = _drive(seed)
        on_cell += iso["all_three"]
        _sc2, iso2, _r2 = _drive(seed, near_miss=True)
        near_miss += iso2["all_three"]
    on_ci = wilson(on_cell, _N)
    nm_ci = wilson(near_miss, _N)
    return {
        "n": _N,
        "on_cell_triple_certified_rate": on_ci,
        "near_miss_triple_certified_rate (control, want 0)": nm_ci,
        "ci_separated": sep(on_ci, nm_ci),
        "note": "the triple firing (all three effects in the residual) certifies the "
                "avatar reached the cross CELL; a NEAR-MISS (avatar one quantum hop "
                "short, effects absent) yields NO triple — the triple is a sufficient "
                "on-cell certificate (vs 231's locus-only reach).",
    }


def source_audit():
    """The isolation names NO effect LOCATION and reads NO ground-truth
    action->effect table; the regions EMERGE from the residual. Verified on the
    DECISION functions of arc_ls20_triple.py (not the prose)."""
    src = (_ROOT / "worlds" / "arc_ls20_triple.py").read_text()
    banned = ["door", "doom", "lever"]
    # non-capturing group so findall returns the whole function BODY, not just the name
    fns = re.findall(r"def (?:isolate_triple|residual_after_avatar|avatar_explained_cells|"
                     r"_classify_cells|raw_diff_isolation).*?(?=\ndef |\nclass |\Z)",
                     src, re.S)
    joined = "\n".join(fns)
    # no hardcoded (row,col) effect location literal driving the decision, and no
    # ground-truth effect table read. The scenario's ground truth (effect_gt /
    # avatar_gt) must NOT be referenced by the isolation decision functions.
    reads_ground_truth = ("effect_gt" in joined or "avatar_gt" in joined)
    hardcoded_coord = re.findall(r"==\s*\(\d+,\s*\d+\)|centroid\s*==\s*\d+", joined)
    return {
        "isolation_reads_no_scenario_ground_truth_in_decision": not reads_ground_truth,
        "regions_emerge_from_residual": "_cluster" in src and "residual" in joined,
        "isolation_is_predict_and_residual":
            "tracker.predict" in joined and "raw_changed_cells" in joined,
        "no_hardcoded_effect_location_literal": len(hardcoded_coord) == 0,
        "banned_domain_tokens_in_decision_logic":
            [t for t in banned if re.search(rf"[^#\"']*\b{t}\b", joined)],
        "reuses_224_tracker_and_231_recogniser":
            "LiveObjectTracker" in src and "recognise_rotation" in src,
        "clean": (not reads_ground_truth) and len(hardcoded_coord) == 0,
    }


def main():
    results = {
        "rung": 232000,
        "commitment": "ISOLATE THE CLEAN TRIPLE via residual-after-explaining-the-"
                      "avatar: PREDICT the avatar (224 tracker translate), the "
                      "RESIDUAL against the actual reach frame IS the indicator + "
                      "destination flash + exit-glyph rotation — excluding the "
                      "avatar. Gated against the GROUND-TRUTH raw cell-diff; rotation "
                      "read by the UNCHANGED 227. The held-prediction principle, not "
                      "an ls20 pixel hack.",
        "G_isolate_triple": isolate_triple_gate(),
        "G_residual_explains_avatar": residual_explains_avatar_gate(),
        "G_rotation_recognised": rotation_recognised_gate(),
        "G_reach_certified": reach_certified_gate(),
        "source_audit": source_audit(),
    }
    out = _ROOT / "results" / "arc_ls20_triple_powered.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print("=== RUNG 232000 — ISOLATE THE CLEAN TRIPLE (powered, ground-truth-gated) ===")
    for g in ("G_isolate_triple", "G_residual_explains_avatar",
              "G_rotation_recognised", "G_reach_certified"):
        print(f"\n{g}:")
        for k, v in results[g].items():
            if k == "note":
                continue
            print(f"  {k}: {v}")
    print(f"\nsource_audit: {results['source_audit']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
