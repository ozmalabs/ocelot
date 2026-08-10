"""BORDER-OWNERSHIP / PROTO-OBJECT — the migrated gate (VISION_BORDER_OWNERSHIP_PREREG.md).

Deterministic. Pins the claim that a local edge becomes a DIRECTED boundary that OWNS
its figure, and a bounded, owned, PRE-IDENTITY region is minted as a ProtoObject, via
ONE seed (vision_border_ownership: bo_bgflood / bo_label / bo_mint_enclosed /
bo_mint_gestalt / bo_own) with NO new Rust:

  * HEADLINE — the ZHOU signature: for a BYTE-IDENTICAL local edge, ownership FLIPS with
    the GLOBAL figure. Border-ownership is CONTEXTUAL, not local edge-detection.
  * FIGURE-GROUND — a closed figure mints exactly ONE ProtoObject; the border owns the
    ENCLOSED side (every perimeter cell), the surround is ground, the interior is unowned.
  * RECURRENCE — the run_rules fixpoint makes ownership globally consistent (K==1 proto
    around the whole contour) and is LOAD-BEARING (a truncated feedforward pass mints no
    proto; the flood grows monotonically toward the fixpoint).
  * GESTALT SIZE — when surroundedness is silent (a bipartition), the SMALLER region is
    figure, and the figure TRACKS size across a swap (load-bearing).
  * FLOORS — an OPEN contour owns nothing; a symmetric AMBIGUOUS split is held open; iid
    NOISE mints nothing (a small sample here; the 100-seed floor is in the runner).
  * §9 — the seed is inert with the flag OFF (default): no bg/owns/proto written.

The closure test (a proto is a HOLE IN ONE SURFACE) refuses speckle with NO size
threshold — closure FALLS OUT of "enclosed by one ground" (§13). In-frame integer
coords; ownership is a RELATION; surroundedness is discrete reachability.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.border_ownership_measure import (  # noqa: E402
    arm_zhou, arm_figure_ground, arm_recurrence, arm_size, arm_convexity,
    arm_floor_open, arm_floor_ambiguous, arm_floor_noise, arm_offday)


def test_HEADLINE_zhou_identical_edge_flips_ownership_with_global_figure():
    r = arm_zhou()
    assert r["pass"], r
    assert r["window_identical"]                      # the local edge IS identical
    assert r["A_owns_55_56"] == [1, 0]                # figure LEFT  -> left owns
    assert r["B_owns_55_56"] == [0, 1]                # figure RIGHT -> right owns
    assert r["flipped"]                               # contextual, not local
    assert r["A_left_target"] is not None and r["B_right_target"] is not None


def test_figure_ground_closed_mints_one_owned_proto_object():
    r = arm_figure_ground()
    assert r["pass"], r
    assert r["n_protos"] == 1
    assert r["protos"][0]["members"] == 24 and r["protos"][0]["gestalt"] == 0
    assert r["all_perimeter_own"]                     # the border owns the figure
    assert r["all_perimeter_target_is_proto"]         # owns_figure -> the ONE proto
    assert r["no_interior_own"]                       # only the border owns
    assert r["surround_is_ground"]                    # surround = ground, unowned


def test_recurrence_fixpoint_is_globally_consistent_and_load_bearing():
    r = arm_recurrence()
    assert r["pass"], r
    assert r["sweeps"] > 1                            # the recurrence is USED
    assert r["distinct_owned_roots"] == 1             # ownership globally consistent
    assert r["n_protos"] == 1
    assert r["flood_monotone"]                        # the flood grows toward fixpoint
    assert r["recurrence_load_bearing"]               # truncation mints no proto


def test_gestalt_size_smaller_region_is_figure_and_tracks_size():
    r = arm_size()
    assert r["pass"], r
    assert r["left_is_figure"] and r["right_is_figure"]
    assert r["figure_tracks_size"]                    # figure follows SIZE, not position


def test_floor_open_contour_owns_nothing():
    r = arm_floor_open()
    assert r["pass"], r
    assert r["n_protos"] == 0 and r["owned_roots"] == []


def test_floor_ambiguous_symmetric_split_is_held_open():
    r = arm_floor_ambiguous()
    assert r["pass"], r
    assert r["n_protos"] == 0 and r["held_open"]


def test_floor_noise_mints_nothing():
    # small sample here (20 seeds); the 100-seed confirmatory floor is in the runner.
    r = arm_floor_noise(n_seeds=20, base_seed=36000)
    assert r["pass"], r
    assert r["false_mint_fields"] == 0


def test_offday_seed_is_inert_by_default():
    r = arm_offday()
    assert r["pass"], r
    assert r["n_protos"] == 0
    assert r["max_bg"] == 0.0 and r["max_owns"] == 0.0


def test_convexity_is_exploratory_and_held_open_named_frontier():
    # NOT a confirmatory claim: convexity-as-tiebreaker is NOT wired; an equal-size
    # ambiguity is held open (anti-confabulation). Convexity is a NAMED FRONTIER.
    r = arm_convexity()
    assert r["exploratory"] and r["held_open"] and r["n_protos"] == 0
