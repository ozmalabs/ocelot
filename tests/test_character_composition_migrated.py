"""tests/test_character_composition_migrated.py — the 5 gates for DISCRIMINATION lever (c) of
scratchpad/HANDWRITING_DESIGN.md: "CHARACTER COMPOSITION = THE SAME LOOP ONE LEVEL UP"
(domains/character_compose.py), plus levers (a) REFINEMENT-TREE SIGNATURES and (b) POSE
READ-OFF IN ALL TIERS (both landed in domains/ink_decode.py) that lever (c) depends on.
Hermetic, synthetic geometry only (plain line segments / `glyph_motor_world` helpers) —
Omniglot stays a scripts/ gate, not pytest.

1. Composed discrimination (test_composed_discrimination_t_l_plus) — THE lever-(c) proof: T,
   L, + built from the SAME two stroke identities at different relative poses classify
   correctly via composed-signature coverage, while a bare MULTISET of stroke identities ties
   (cannot discriminate at all).
2. Character-level rung 1 (test_character_level_rung1_zero_mint) — a whole-character
   translate / scale (each tested separately — see the test's own docstring for the honest
   `max_dims=2` / axis-aligned-bbox reasons a combined rotate+scale+translate is out of scope
   for the GENERIC ladder) reads as a CHARACTER-LEVEL pose delta (`cpose_*`), zero character
   mint — the per-stroke `rel` arrangement stays invariant (self-normalizing frame).
3. Pose read-off restored (test_pose_read_off_restored_all_tiers) — DISCRIMINATION item (b):
   a COARSE-tier recognition gets the SAME high transform-explanation rate the fine tier
   always had (`ink_decode._pose_read_goal`/`_install_pose_transform`).
4. Child-id identity (test_child_id_identity_differs_per_refinement) — DISCRIMINATION item
   (a): two spans matching DIFFERENT refinement children of the SAME coarse parent resolve to
   DIFFERENT identities downstream (`ink_decode._resolved_identity`).
5. Character sd loop (test_character_sd_loop_mint_then_recognize) — a novel arrangement of
   known strokes mints EXACTLY ONE character quantum via the UNCHANGED `sd_*` ladder
   (`domains.reflective_faculty.induce_concern`); the repeat arrangement recognizes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

from domains import abs_read as ar
from domains import character_compose as cc
from domains import ink_decode as ink
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc

ROOT = Path(__file__).resolve().parent.parent


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _stroke_quantize_live() -> bool:
    s = srs.Substrate()
    return sc._stroke_quantize_live(s._inner)


def _transformdecode_pools_by_predicate() -> bool:
    s = srs.Substrate()
    native = s._inner
    held = [["strokeq", 0, "x"], ["cpose_x", 4], ["cpose_y", 4], ["cpose_o", 2], ["cpose_s", 3]]
    s.add_node("ShapeSignature", {"name": "probe", "kind": "character", "signature": json.dumps(held)})
    goal = [["strokeq", 0, "x"], ["cpose_x", 4], ["cpose_y", 4], ["cpose_o", 7], ["cpose_s", 3]]
    res = native.evaluate({"type": "TransformDecode", "goal": {"type": "Lit", "value": goal},
                           "max_dims": 4}, {})
    return bool(res.get("explained"))


def _stroke_render_live() -> bool:
    s = srs.Substrate()
    return ar._stroke_render_live(s._inner)


SQ_LIVE = _stroke_quantize_live()
TD_FIX_LIVE = _transformdecode_pools_by_predicate()
SR_LIVE = _stroke_render_live()
SQ_SKIP = "StrokeQuantize not live -- honest skip, not a faked pass (see test_ink_decode_migrated.py)."
TD_SKIP = "TransformDecode's (predicate,slot) pooling fix not live -- honest skip."
SR_SKIP = ("StrokeRender not live -- authored against the ABS AS DEFAULT design's schema, "
           "not yet operative (built in parallel, 2026-07-03); honest skip, not a faked pass.")


# ---------------------------------------------------------------------------
# Hand-built line strokes -- no dataset, no StrokeQuantize needed to CONSTRUCT
# them (compose_character_signature itself calls StrokeQuantize internally,
# so gates 1/2/5 below still need SQ_LIVE; gates 3/4 stay hand-set/always-live).
# ---------------------------------------------------------------------------
def _line(p0, p1, n=24) -> list:
    return np.linspace(p0, p1, n).tolist()


def _t_shape() -> list:
    """A 'T': a vertical stem (top -> bottom) + a horizontal crossbar at the TOP."""
    vert = _line((0.0, 0.0), (0.0, -1.0))
    horiz = _line((-0.5, 0.0), (0.5, 0.0))
    return [(vert, "line_v"), (horiz, "line_h")]


def _l_shape() -> list:
    """An 'L': the SAME vertical stem + a horizontal foot at the BOTTOM, extending right."""
    vert = _line((0.0, 0.0), (0.0, -1.0))
    horiz = _line((0.0, -1.0), (1.0, -1.0))
    return [(vert, "line_v"), (horiz, "line_h")]


def _plus_shape() -> list:
    """A '+': the SAME vertical stem (now centered) + a horizontal crossbar at the MIDDLE."""
    vert = _line((0.0, 0.5), (0.0, -0.5))
    horiz = _line((-0.5, 0.0), (0.5, 0.0))
    return [(vert, "line_v"), (horiz, "line_h")]


def _rotate(pts, deg) -> list:
    theta = np.radians(deg)
    c, si = np.cos(theta), np.sin(theta)
    rot = np.array([[c, -si], [si, c]])
    return (np.asarray(pts, dtype=float) @ rot.T).tolist()


def _scale(pts, k) -> list:
    return (np.asarray(pts, dtype=float) * k).tolist()


def _translate(pts, dx, dy) -> list:
    return (np.asarray(pts, dtype=float) + np.array([dx, dy])).tolist()


# ---------------------------------------------------------------------------
# The SAME "Sum + In" coverage / Argmax classification idiom
# scripts/jabberwock_omniglot_dynamic_quantization.py's own `_coverage_term`/
# `_argmax_pairs_term` establish -- generalized here to composed RELATION lists
# instead of bare quantum-name multisets (the "richer than multisets" claim).
# ---------------------------------------------------------------------------
def _coverage_term(query_sig, exemplar_sig) -> dict:
    return {"type": "Sum", "source": {"type": "Lit", "value": query_sig}, "var_name": "n",
            "value": {"type": "IfThenElse",
                      "cond": {"type": "In", "member": {"type": "Var", "name": "n"},
                               "container": {"type": "Lit", "value": exemplar_sig}},
                      "then": {"type": "Lit", "value": 1.0}, "other": {"type": "Lit", "value": 0.0}}}


def _argmax_pairs_term(pairs) -> dict:
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def _classify(native, query_sig, candidates: dict) -> str:
    """candidates: {label: signature}. ONE held Argmax over per-candidate coverage counts --
    never a Python argmax/sort-by-score."""
    labels = list(candidates)
    pairs = [(float(native.evaluate(_coverage_term(query_sig, candidates[lb]), {}) or 0.0), i)
             for i, lb in enumerate(labels)]
    winner = native.evaluate(_argmax_pairs_term(pairs), {})
    return labels[winner[1]] if winner is not None else None


# ===========================================================================
# Gate 1 — composed discrimination (THE lever-(c) proof).
# ===========================================================================
def test_composed_discrimination_t_l_plus():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner

    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    sigs = {name: cc.compose_character_signature(native, pts)["signature"]
            for name, pts in shapes.items()}

    # The bare MULTISET of stroke identities is IDENTICAL for all three -- {"line_v","line_h"}
    # -- a multiset-only classifier cannot discriminate at all (a tie every time).
    multisets = {name: sorted(r[2] for r in sig if r[0] == "strokeq") for name, sig in sigs.items()}
    assert multisets["T"] == multisets["L"] == multisets["+"], (
        "the three characters must share the SAME multiset of stroke identities -- "
        "otherwise this isn't testing arrangement, it's testing vocabulary")

    # The COMPOSED signature (with "rel") correctly classifies a fresh, independently-composed
    # instance of each character -- arrangement carries the identity a multiset cannot.
    for name, pts in shapes.items():
        query_sig = cc.compose_character_signature(native, pts)["signature"]
        winner = _classify(native, query_sig, sigs)
        assert winner == name, f"composed signature must classify {name!r} correctly, got {winner!r}"

    # Confirm the mechanism: scoring the T query against the MULTISET-only reduction of each
    # candidate ties (proves the "rel" relations are what carries the discrimination above).
    ms_sigs = {name: [["strokeq", k, nm] for k, nm in enumerate(multisets[name])]
              for name in shapes}
    t_multiset_query = [["strokeq", k, nm] for k, nm in enumerate(multisets["T"])]
    ms_scores = {name: float(native.evaluate(_coverage_term(t_multiset_query, ms_sigs[name]), {}) or 0.0)
                for name in shapes}
    assert len(set(ms_scores.values())) == 1, (
        f"multiset-only coverage must TIE across T/L/+ (identical vocabulary): {ms_scores!r}")


# ===========================================================================
# Gate 2 — character-level rung 1 (whole-character pose delta, zero mint).
# ===========================================================================
def test_character_level_rung1_zero_mint():
    """A whole-character TRANSLATION (about the origin -- 2 dims: `cpose_x`/`cpose_y`) and a
    whole-character SCALE about the origin (1 dim: `cpose_s`) are tested SEPARATELY --
    `sd_transform_decode`'s seeded `max_dims=2` (seeds/shape_decode_loop.json, shared by every
    domain, unchanged here) caps how many simultaneously-differing (predicate,slot) dims ONE
    observation can explain. `cpose_x`/`cpose_y` quantize a stroke's start point against the
    CHARACTER's own (axis-aligned) bbox -- the SAME documented "self-bbox limitation" a
    stroke's own `pose_x`/`pose_y` already carries (`runners/dsl/src/strokes.rs`'s own test
    comment: "position/scale are read relative to the point-set's OWN bbox, which itself
    rotates/scales/translates with the stroke") -- a ROTATION reshapes that axis-aligned bbox,
    so it ALSO perturbs `cpose_x`/`cpose_y` (empirically: a 40°+1.7x rotate+scale probe showed
    all 4 `cpose_*` predicates differing at once, honestly exceeding `max_dims=2`); a pure
    SCALE or pure TRANSLATION about the origin does not reshape the bbox's own proportions and
    stays within budget, which is what this gate verifies. Rotation-only whole-character
    recognition via the GENERIC `sd_transform_decode` ladder is an HONEST, documented residual
    (mirrors how STROKE-level rung 1 only handles it by bypassing that ladder entirely --
    `ink_decode._read_pose_transform`'s OWN direct `max_dims=4` call, not the generic seed's
    `max_dims=2` -- a different, direct-read mechanism this gate deliberately does not reach
    for, since the design wants characters recognized via the SAME UNCHANGED sd_* ladder as
    everything else). The codebook entry is authored at its NATURAL baseline pose
    (`canonical=False`, `compose_character_signature`'s own default and documented convention
    -- see its docstring for why a fixed zero PIN does not work for characters, unlike
    strokes).

    CONVENTION CHANGE (RUN-4 LEVERS "LEVER 1", 2026-07-02): this gate's OWN prior docstring
    named the combined rotate+scale+translate case as an HONEST, documented residual of the
    GENERIC `sd_transform_decode` ladder (`induce_concern`, seeded `max_dims=2`) -- that
    residual is now CLOSED, but via a DIFFERENT, deliberately separate path:
    `test_lever1_full_transform_recognized_via_direct_readoff` below exercises the NEW
    `cc.recognize_or_mint_character` (a direct `TransformDecode` read-off with its OWN
    `max_dims=4`, mirroring `ink_decode._read_pose_transform` -- see `compose_character_
    signature`'s docstring for the full reasoning). THIS gate is left as-is, still exercising
    the GENERIC `induce_concern` ladder specifically (still correctly capped at `max_dims=2`,
    still correctly restricted to translate-only/scale-only) -- that ladder is a SEPARATE,
    still-real code path other callers (a truly novel arrangement's mint decision) still go
    through, so its own documented scope is unchanged."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    t_pts = _t_shape()

    canon_sig = cc.compose_character_signature(native, t_pts)["signature"]
    grow = cc.grow_character_quantum(s, "T", canon_sig)
    assert grow["grown"] is True
    epoch0 = s.node(ag)["attrs"]["codebook_epoch"]

    # (a) whole-character TRANSLATION only.
    moved = [(_translate(pts, 3.0, -2.0), nm) for (pts, nm) in t_pts]
    moved_sig = cc.compose_character_signature(native, moved, canonical=False)["signature"]
    res_t = rf.induce_concern(s, moved_sig, name_hint="probe_T_translated")
    assert res_t["minted"] is False, f"a translated T must recognize, not mint: {res_t!r}"
    assert s.node(ag)["attrs"]["codebook_epoch"] == epoch0

    # (b) whole-character SCALE (about the origin) only.
    if not TD_FIX_LIVE:
        pytest.skip(TD_SKIP)
    scaled = [(_scale(pts, 1.7), nm) for (pts, nm) in t_pts]
    scaled_sig = cc.compose_character_signature(native, scaled, canonical=False)["signature"]
    res_s = rf.induce_concern(s, scaled_sig, name_hint="probe_T_scaled")
    assert res_s["minted"] is False, f"a scaled T must recognize, not mint: {res_s!r}"
    assert s.node(ag)["attrs"]["codebook_epoch"] == epoch0


# ===========================================================================
# RUN-4 LEVERS "LEVER 1" — the combined rotate+scale+translate residual gate 2's own
# docstring names, closed via the NEW direct character-grain read-off
# (`cc.recognize_or_mint_character`, own `max_dims=4`) rather than the generic ladder.
# ===========================================================================
def test_lever1_full_transform_recognized_via_direct_readoff():
    """RUN-4 LEVERS "LEVER 1": an ARBITRARY continuous rotation (37 degrees -- not a bin-
    aligned angle, not merely about the stroke's own start point the way the Rust-level
    stroke fixture simplifies it) + a 1.7x scale + a (3, -2) translation of the WHOLE
    character. `rel`/`strokeq` relations (the invariant-frame arrangement) must stay
    BYTE-IDENTICAL -- the intrinsic frame co-transforms with the input by construction, this
    is the SAME property `test_character_level_rung1_zero_mint` already relies on, just
    checked directly here. `cpose_*` DOES differ (the whole point: the transform shows up
    there, confined to those 4 predicates). `cc.recognize_or_mint_character` (own
    `max_dims=4`, NOT the generic `induce_concern` ladder) must report `minted=False` --
    recognized, zero mint through the sd loop -- with every explained delta confined to
    `cpose_*` predicates."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not TD_FIX_LIVE:
        pytest.skip(TD_SKIP)
    s, ag, native = _boot()
    t_pts = _t_shape()

    # Codebook entries now use the CANONICAL (zero-pinned) cpose convention (RUN-4 LEVERS
    # "LEVER 1" -- mirrors stroke_codebook.grow_stroke_quantum's own canonical_pose=True).
    canon_sig = cc.compose_character_signature(native, t_pts, canonical=True)["signature"]
    grow = cc.grow_character_quantum(s, "T_canon", canon_sig)
    assert grow["grown"] is True
    epoch0 = s.node(ag)["attrs"]["codebook_epoch"]

    transformed = [(_translate(_scale(_rotate(pts, 37.0), 1.7), 3.0, -2.0), nm)
                   for (pts, nm) in t_pts]
    query_sig = cc.compose_character_signature(native, transformed, canonical=False)["signature"]

    def _non_cpose(sig):
        return [list(r) for r in sig if not str(r[0]).startswith("cpose")]

    assert _non_cpose(query_sig) == _non_cpose(canon_sig), (
        "rel/strokeq relations must be BYTE-IDENTICAL under an arbitrary similarity transform")

    cpose_canon = {r[0]: r[1] for r in canon_sig if str(r[0]).startswith("cpose")}
    cpose_query = {r[0]: r[1] for r in query_sig if str(r[0]).startswith("cpose")}
    assert cpose_query != cpose_canon, (
        "the transform must show up SOMEWHERE (cpose) or this test proves nothing")

    res = cc.recognize_or_mint_character(s, query_sig, name_hint="probe_T_full_transform")
    assert res["minted"] is False, (
        f"an arbitrary rotate+scale+translate must recognize via the direct read-off, "
        f"not mint: {res!r}")
    assert res["path"] == "direct_character_transform"
    assert s.node(ag)["attrs"]["codebook_epoch"] == epoch0, "zero mint through the sd loop"

    if res["transform"]["explained"]:
        preds = {t.get("pred") for t in res["transform"]["transforms"]}
        assert preds and preds <= {"cpose_x", "cpose_y", "cpose_o", "cpose_s"}, (
            f"every explained delta must be confined to cpose dims, got {preds!r}")


def test_lever1_recognize_or_mint_falls_through_to_mint_for_novel_arrangement():
    """`cc.recognize_or_mint_character`'s direct read-off must NOT swallow genuine novelty --
    with an empty character codebook (`checked=0` candidates), the direct check can never
    explain anything, so a first-ever arrangement still falls through to the EXISTING
    `induce_concern` -> `sd_mint_quantum` ladder, UNCHANGED (mirrors gate 5's own mint
    behaviour, just entered via the new function)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    baseline_axes = len(list(s.nodes("CapabilityAxis")))
    l_pts = _l_shape()
    sig = cc.compose_character_signature(native, l_pts)["signature"]

    res = cc.recognize_or_mint_character(s, sig, name_hint="probe_novel_via_direct")
    assert res["minted"] is True
    assert res["path"] == "induce_concern"
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 1


# ===========================================================================
# Gate 3 — pose read-off restored (DISCRIMINATION item (b)).
# ===========================================================================
def test_pose_read_off_restored_all_tiers():
    """A COARSE-tier recognition (fine `seg` jittered non-uniformly -- the SAME scenario
    `test_ink_decode_migrated.py::test_gate_a_coarse_recognition_not_minted` exercises) must
    get its pose read off EXACTLY like the fine tier does: `_install_pose_transform` splices
    the OBSERVED pose onto the CHOSEN PARENT's own stored (canonical) `seg` before the
    `TransformDecode` read (`_pose_read_goal`), isolating the pose reading from the (fine,
    separately-tracked) seg mismatch that put this span in the coarse tier to begin with --
    restoring the SAME high explain rate the fine tier always had (the DISCRIMINATION
    section's measured '100% -> 6.9%' regression)."""
    s = srs.Substrate()
    native = s._inner
    stroke_node = s.add_node("ShapeSignature", {"name": "A", "kind": "stroke",
                             "signature": json.dumps(
                                 [["seg", 0, 1, 1], ["seg", 1, 2, 1], ["seg", 2, 3, 1],
                                  ["pose_x", 0], ["pose_y", 0], ["pose_o", 0], ["pose_s", 0]])})
    span_node = s.add_node("Stroke", {})

    # A NON-UNIFORM fine jitter (seg[0] turn 1->2, everything else matches "A"'s stored fine
    # seg) COMBINED with a genuine pose difference (translation + rotation + scale) -- exactly
    # what a real coarse-tier recognition looks like: the fine seg mismatch is what put it in
    # the coarse tier, the pose difference is what a caller actually wants read off.
    jittered_moved_full = [["seg", 0, 2, 1], ["seg", 1, 2, 1], ["seg", 2, 3, 1],
                           ["pose_x", 3], ["pose_y", 2], ["pose_o", 4], ["pose_s", 1]]

    transform = ink._install_pose_transform(s, native, span_node, None, "A", jittered_moved_full)
    assert transform["explained"] is True, (
        f"coarse-tier pose read-off must explain the transform exactly like the fine tier "
        f"does (DISCRIMINATION item (b)): {transform!r}")
    read_preds = {t.get("pred") for t in (transform.get("transforms") or []) if t.get("delta")}
    assert read_preds <= {"pose_x", "pose_y", "pose_o", "pose_s"}, (
        f"only pose slots should carry the explained delta, got {read_preds!r}")

    # SANITY: the RAW (un-fixed) signature -- no substitution -- must NOT explain (proves the
    # fix is doing real work, not vacuously always succeeding).
    raw_transform = ink._read_pose_transform(native, jittered_moved_full)
    assert raw_transform.get("explained") is not True, (
        "the RAW observed signature (unfixed seg mismatch bleeding into the pose read) "
        "should NOT explain -- otherwise this test isn't isolating the fix")


# ===========================================================================
# Gate 4 — child-id identity (DISCRIMINATION item (a)).
# ===========================================================================
def test_child_id_identity_differs_per_refinement():
    """Two spans that both recognize the SAME coarse parent "A" but mismatch its fine grain
    in DIFFERENT dimensions (turn-only vs len-only) mint/match DIFFERENT refinement children
    -- `ink_decode._resolved_identity` must resolve each span's downstream identity to its
    OWN child, not the shared coarse parent, so `character_compose`'s `strokeq` relations
    correctly distinguish them."""
    s, ag, native = _boot()
    parent_pts = [(1, 1), (2, 1), (3, 1)]
    s.add_node("ShapeSignature", {"name": "A", "kind": "stroke",
                                  "signature": json.dumps([["seg", i, t, l] for i, (t, l) in
                                                          enumerate(parent_pts)])})

    span_turn_mismatch = [["seg", 0, 9, 1], ["seg", 1, 2, 1], ["seg", 2, 3, 1],
                          ["pose_x", 0], ["pose_y", 0], ["pose_o", 0], ["pose_s", 0]]
    span_len_mismatch = [["seg", 0, 1, 9], ["seg", 1, 2, 1], ["seg", 2, 3, 1],
                         ["pose_x", 0], ["pose_y", 0], ["pose_o", 0], ["pose_s", 0]]

    refine_turn = ink._refine_or_note(s, s, native, ag, s.add_node("Stroke", {}), "A",
                                      span_turn_mismatch, segments=3, turn_bins=sc.DEFAULT_TURN_BINS,
                                      len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                                      scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    refine_len = ink._refine_or_note(s, s, native, ag, s.add_node("Stroke", {}), "A",
                                     span_len_mismatch, segments=3, turn_bins=sc.DEFAULT_TURN_BINS,
                                     len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                                     scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert refine_turn["minted"] is True and refine_len["minted"] is True

    identity_turn = ink._resolved_identity("A", refine_turn)
    identity_len = ink._resolved_identity("A", refine_len)
    assert identity_turn != "A" and identity_len != "A", (
        "a refined span's downstream identity must be the CHILD, not the coarse parent")
    assert identity_turn != identity_len, (
        f"two DIFFERENT refinement children must resolve to DIFFERENT identities, got "
        f"{identity_turn!r} == {identity_len!r}")

    # Composed into two 1-stroke "characters", the strokeq relations correctly differ.
    sig_turn = cc.compose_character_signature(native, [([(0.0, 0.0), (1.0, 0.0)], identity_turn)])
    sig_len = cc.compose_character_signature(native, [([(0.0, 0.0), (1.0, 0.0)], identity_len)])
    strokeq_turn = [r for r in sig_turn["signature"] if r[0] == "strokeq"]
    strokeq_len = [r for r in sig_len["signature"] if r[0] == "strokeq"]
    assert strokeq_turn != strokeq_len, "composed strokeq relations must differ per child identity"

    # NOTHING RESOLVED (no comparable parent / exact-at-fine) -- chosen_name stands unchanged.
    exact = [["seg", 0, 1, 1], ["seg", 1, 2, 1], ["seg", 2, 3, 1],
             ["pose_x", 0], ["pose_y", 0], ["pose_o", 0], ["pose_s", 0]]
    refine_exact = ink._refine_or_note(s, s, native, ag, s.add_node("Stroke", {}), "A", exact,
                                       segments=3, turn_bins=sc.DEFAULT_TURN_BINS,
                                       len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                                       scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert ink._resolved_identity("A", refine_exact) == "A"
    assert ink._resolved_identity("A", None) == "A"


# ===========================================================================
# Gate 5 — character sd loop (mint exactly once, then recognize).
# ===========================================================================
def test_character_sd_loop_mint_then_recognize():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    baseline_axes = len(list(s.nodes("CapabilityAxis")))
    baseline_chars = sc._existing_names(s, "character")

    l_pts = _l_shape()
    sig = cc.compose_character_signature(native, l_pts)["signature"]

    res_novel = rf.induce_concern(s, sig, name_hint="probe_novel_character")
    assert res_novel["minted"] is True
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 1

    axis_node = None
    for n in s.nodes("CapabilityAxis"):
        axis_node = n
    grow = cc.grow_character_quantum(s, "L_arrangement", sig)
    assert grow["grown"] is True
    assert sc._existing_names(s, "character") - baseline_chars == {"L_arrangement"}

    # RE-observe the EXACT SAME arrangement: now recognized (the codebook grew), no new mint.
    res_repeat = rf.induce_concern(s, sig, name_hint="probe_repeat_character")
    assert res_repeat["minted"] is False, (
        f"the SAME composed arrangement must now be RECOGNIZED, not minted again: {res_repeat!r}")
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 1, (
        "no SECOND CapabilityAxis for the repeat observation")


# ===========================================================================
# EAGER CHILD MINTING (scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING" section,
# 2026-07-02 — the a6fe069b residual). ADDITIVE: every gate above this line is unchanged.
# The design's own literal gate: "two strokes identical at fine grain but distinct at
# sub-fine -> same parent, different children, distinguishable composed characters."
# ===========================================================================
def test_eager_children_distinguish_composed_characters_via_strokeq_fine():
    """Two ONE-stroke 'characters' share the SAME parent identity (`strokeq` ties) and the
    SAME underlying point geometry (so `rel`/`cpose` tie too — this is deliberately the
    'same parent' half of the design's gate) but carry DIFFERENT eager `fine_child` names
    (exactly what `ink_decode.decode_ink`'s eager-child mechanism mints for two real
    instances that match one parent at fine but differ at sub-fine, see
    `test_ink_decode_migrated.py::test_eager_child_gate4_live_decode_ink_additive_identity`).
    WITHOUT `strokeq_fine` the two composed signatures are BYTE-IDENTICAL (a genuine tie —
    proves the discrimination comes from `strokeq_fine`, not some other relation); WITH it
    they classify correctly against each other — "distinguishable composed characters"."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    pts = _line((0.0, 0.0), (1.0, 0.0))

    sig_a_with = cc.compose_character_signature(
        native, [(pts, "bulge", "bulge__eager_turn_AAA")])["signature"]
    sig_b_with = cc.compose_character_signature(
        native, [(pts, "bulge", "bulge__eager_turn_BBB")])["signature"]
    sig_a_without = cc.compose_character_signature(
        native, [(pts, "bulge", "bulge__eager_turn_AAA")],
        include_fine_children=False)["signature"]
    sig_b_without = cc.compose_character_signature(
        native, [(pts, "bulge", "bulge__eager_turn_BBB")],
        include_fine_children=False)["signature"]

    assert sig_a_without == sig_b_without, (
        "WITHOUT strokeq_fine the two composed signatures must be indistinguishable (same "
        "parent, same geometry) -- proves strokeq_fine is what carries the discrimination")
    assert sig_a_with != sig_b_with

    def _non_fine(sig):
        return [r for r in sig if r[0] != "strokeq_fine"]
    assert _non_fine(sig_a_with) == sig_a_without, (
        "the flag must be PURELY ADDITIVE -- every non-strokeq_fine relation identical "
        "whether the flag is on or off")

    winner_for_a = _classify(native, sig_a_with, {"A": sig_a_with, "B": sig_b_with})
    winner_for_b = _classify(native, sig_b_with, {"A": sig_a_with, "B": sig_b_with})
    assert winner_for_a == "A" and winner_for_b == "B", (
        "WITH strokeq_fine the two must classify correctly against each other")


def test_eager_child_3tuple_backward_compatible_with_2tuple():
    """`compose_character_signature` must accept the pre-existing 2-tuple `(points, name)`
    shape (every committed caller) byte-identically alongside the NEW 3-tuple shape — a
    2-tuple item never emits a `strokeq_fine` relation (nothing to add)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    pts = _line((0.0, 0.0), (1.0, 0.0))

    sig_2tuple = cc.compose_character_signature(native, [(pts, "bulge")])["signature"]
    sig_3tuple_none = cc.compose_character_signature(native, [(pts, "bulge", None)])["signature"]
    assert sig_2tuple == sig_3tuple_none
    assert not any(r[0] == "strokeq_fine" for r in sig_2tuple)


# ===========================================================================
# ARRANGEMENT FIDELITY (scratchpad/HANDWRITING_DESIGN.md's "ARRANGEMENT FIDELITY" section,
# 2026-07-03 — the accb0d47 residual). PHASE A (scripts/jabberwock_omniglot_arrangement_diag.py,
# run against the COMMITTED seeds/stroke_shapes.json codebook, reproducing the real gate's own
# 33.8%/66.2% miss rate) ranked the coverage METRIC (naive Sum+In whole-relation-tuple
# membership) as the top lever: 52.8% of misses decided by a TIE, 32.1% by a gap<=1, vs only
# 18.9% recoverable by an alternate frame anchor. `cc.assignment_coverage_term` (PER-STROKE
# best-match, additive alongside the UNCHANGED `_coverage_term` control below) is the built
# fix. ADDITIVE: every gate above this line is unchanged; `_coverage_term`/`_classify` above
# are the pre-existing naive metric, kept as the logged CONTROL in every gate below.
# ===========================================================================
def _split_stroke(pairs: list, idx: int) -> list:
    """Diagnostic-style helper (mirrors scripts/jabberwock_omniglot_arrangement_diag.py's own
    geometry probes): split stroke `idx` of a `[(points, name), ...]` list into TWO pen-down
    halves (same identity, half each) -- simulates a drawer's pen-lift mid-stroke, the
    concrete real-world cause of the STRUCTURAL (different stroke COUNT) mismatch Phase A
    measured in 47.2% of misses."""
    out = []
    for i, (pts, name) in enumerate(pairs):
        if i == idx:
            half = len(pts) // 2
            out.append((pts[:half + 1], name))
            out.append((pts[half:], name))
        else:
            out.append((pts, name))
    return out


def test_assignment_coverage_preserves_composed_discrimination():
    """Regression: `assignment_coverage_term` must still solve gate 1's own T-vs-L-vs-+ proof
    (the SAME two stroke identities at different relative poses) -- the new metric must not
    lose the arrangement-carries-identity property the naive metric already had."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    sigs = {name: cc.compose_character_signature(native, pts)["signature"]
            for name, pts in shapes.items()}

    for name, pts in shapes.items():
        query_sig = cc.compose_character_signature(native, pts)["signature"]
        labels = list(sigs)
        pairs = [(float(native.evaluate(cc.assignment_coverage_term(query_sig, sigs[lb]), {})
                        or 0.0), i) for i, lb in enumerate(labels)]
        winner = native.evaluate(_argmax_pairs_term(pairs), {})
        assert labels[winner[1]] == name, (
            f"assignment coverage must still classify {name!r} correctly")


def test_assignment_coverage_distinguishes_near_miss_from_total_miss():
    """THE metric-granularity proof: the naive `_coverage_term` scores a "rel" relation as
    ONE atomic all-or-nothing element -- a query whose `rel` differs from its true match on
    ONLY `do_q` (a realistic single-bin near-miss) loses EXACTLY the same 1 point as a query
    whose `rel` differs on ALL FOUR slots (a total, unrelated mismatch) -- Phase A's own
    "small gap" / "tie" signature (>50% of the 53 real misses). `assignment_coverage_term`
    scores each of the four `rel` slots independently, so it must lose LESS for the near-miss
    than for the total miss -- the near-miss/total-miss distinction the naive metric cannot
    make at all."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    t_sig = cc.compose_character_signature(native, _t_shape())["signature"]

    def _perturb(sig, k, slot_offsets):
        out = [list(r) for r in sig]
        for r in out:
            if r[0] == "rel" and r[1] == k:
                for off in slot_offsets:
                    r[2 + off] = r[2 + off] + 5     # a large, guaranteed-different bin value
        return out

    near_miss = _perturb(t_sig, 1, [2])            # only do_q changes
    total_miss = _perturb(t_sig, 1, [0, 1, 2, 3])  # dx/dy/do/ds all change

    naive_exact = float(native.evaluate(_coverage_term(t_sig, t_sig), {}))
    naive_near = float(native.evaluate(_coverage_term(near_miss, t_sig), {}))
    naive_total = float(native.evaluate(_coverage_term(total_miss, t_sig), {}))
    assert naive_exact - naive_near == naive_exact - naive_total, (
        "the naive metric must NOT be able to tell a 1-slot near-miss from a 4-slot total "
        "miss -- both lose the SAME whole-relation point (this is the bug being fixed)")

    assign_exact = float(native.evaluate(cc.assignment_coverage_term(t_sig, t_sig), {}))
    assign_near = float(native.evaluate(cc.assignment_coverage_term(near_miss, t_sig), {}))
    assign_total = float(native.evaluate(cc.assignment_coverage_term(total_miss, t_sig), {}))
    near_drop = assign_exact - assign_near
    total_drop = assign_exact - assign_total
    assert 0 < near_drop < total_drop, (
        f"assignment coverage must lose LESS for a near-miss ({near_drop}) than a total miss "
        f"({total_drop}) -- the partial-credit fix Phase A's diagnosis calls for")


def test_assignment_coverage_robust_to_structural_stroke_count_mismatch():
    """THE structural-mismatch proof (Phase A: 47.2% of the 53 real misses decoded the query
    and its true exemplar to a DIFFERENT STROKE COUNT). Query = an 'L' whose vertical stroke
    was drawn as two pen-down halves (`_split_stroke`, a pen-lift) -- 3 strokes total, same
    identities/geometry as a genuine 'L'. The naive metric is shown to actively MISCLASSIFY:
    a WRONG-identity decoy that merely happens to share the query's own accidental 3-stroke
    structure ('T_split' -- a 'T' with its vertical ALSO split) scores HIGHER under naive
    whole-relation-tuple membership than the TRUE 'L' (2 strokes) does, because naive
    coverage rewards structural (draw-order-key) alignment over genuine geometric identity.
    `assignment_coverage_term` -- matching by CONTENT via `MaxOver`, never by shared draw-
    order `k` -- must correctly prefer the true 'L' over both decoys."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    l_pairs, t_pairs = _l_shape(), _t_shape()
    l_sig = cc.compose_character_signature(native, l_pairs)["signature"]
    t_sig = cc.compose_character_signature(native, t_pairs)["signature"]
    t_split_sig = cc.compose_character_signature(
        native, _split_stroke(t_pairs, 0))["signature"]
    query_sig = cc.compose_character_signature(
        native, _split_stroke(l_pairs, 0))["signature"]

    candidates = {"L_true": l_sig, "T": t_sig, "T_split_decoy": t_split_sig}

    naive_scores = {lb: float(native.evaluate(_coverage_term(query_sig, sig), {}) or 0.0)
                    for lb, sig in candidates.items()}
    assert naive_scores["T_split_decoy"] > naive_scores["L_true"], (
        f"this gate's OWN premise (the naive metric must be FOOLED by the structural decoy) "
        f"did not reproduce: {naive_scores!r} -- Phase A's diagnosed failure mode is not "
        f"present in this construction, the gate needs a different one")

    assign_scores = {lb: float(native.evaluate(cc.assignment_coverage_term(query_sig, sig), {})
                              or 0.0) for lb, sig in candidates.items()}
    assert assign_scores["L_true"] > assign_scores["T_split_decoy"], (
        f"assignment coverage must correctly prefer the TRUE identity over the structural "
        f"decoy: {assign_scores!r}")
    assert assign_scores["L_true"] == max(assign_scores.values())


def test_assignment_coverage_term_is_pure_and_additive():
    """`assignment_coverage_term` must be a pure Term-builder (no graph mutation, no cached
    state) and PURELY ADDITIVE alongside the pre-existing naive `_coverage_term` -- calling it
    must never change what `_coverage_term` itself returns for the SAME signatures (the
    "keep the OLD score logged as the control" discipline)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    t_sig = cc.compose_character_signature(native, _t_shape())["signature"]
    l_sig = cc.compose_character_signature(native, _l_shape())["signature"]

    naive_before = float(native.evaluate(_coverage_term(t_sig, l_sig), {}))
    _ = native.evaluate(cc.assignment_coverage_term(t_sig, l_sig), {})
    _ = native.evaluate(cc.assignment_coverage_term(l_sig, t_sig), {})
    naive_after = float(native.evaluate(_coverage_term(t_sig, l_sig), {}))
    assert naive_before == naive_after

    a1 = float(native.evaluate(cc.assignment_coverage_term(t_sig, l_sig), {}))
    a2 = float(native.evaluate(cc.assignment_coverage_term(t_sig, l_sig), {}))
    assert a1 == a2, "assignment_coverage_term must be deterministic/pure (same inputs, same score)"


# ===========================================================================
# HIGHER-ORDER ARRANGEMENT RELATIONS (scratchpad/HANDWRITING_DESIGN.md's "HIGHER-ORDER
# ARRANGEMENT RELATIONS" section, 2026-07-03 — the 97d54623 residual). ADDITIVE: every gate
# above this line is unchanged. Phase A (scripts/jabberwock_omniglot_arrangement_diag.py,
# run 8) found ties decide 52.8% of the naive-coverage misses; "rel2" gives the naive metric
# ONE extra atomic, independently-checkable fact per NON-ADJACENT stroke pair — mechanically
# DERIVED from the two strokes' own already-computed "rel" pose bins, no new geometry.
# ===========================================================================
def test_rel2_relations_mechanical_derivation():
    """Unit gate for `cc._rel2_relations`/`cc._wrap_signed_bin`: rel2 is a PURE function of
    the two strokes' own already-computed "rel" pose bins (no new `StrokeQuantize` call, no
    new geometry) — only NON-ADJACENT pairs (`j > i+1`) are emitted; `dx_q`/`dy_q`/`ds_q` are
    plain integer differences of unsigned buckets; `do_q` wraps a SIGNED bin difference back
    into its own range (the +180/-180 seam case a plain subtraction would get wrong)."""
    pose_by_k = {
        0: {"x_q": 0, "y_q": 0, "orient_q": 7, "scale_q": 2},
        1: {"x_q": 1, "y_q": 1, "orient_q": 0, "scale_q": 3},
        2: {"x_q": 4, "y_q": 2, "orient_q": -7, "scale_q": 5},
        3: {"x_q": 6, "y_q": 1, "orient_q": 1, "scale_q": 1},
    }
    rel2 = cc._rel2_relations(pose_by_k, turn_bins=16)
    pairs = {(r[1], r[2]) for r in rel2}
    assert pairs == {(0, 2), (0, 3), (1, 3)}, (
        f"only NON-ADJACENT pairs (j > i+1) should be emitted (draw order 0..3), got {pairs!r}")
    assert all(r[0] == "rel2" for r in rel2)

    by_pair = {(r[1], r[2]): tuple(r[3:]) for r in rel2}
    # (0, 2): dx=4-0=4, dy=2-0=2, do=wrap(-7-7,16)=wrap(-14,16)=+2, ds=5-2=3.
    assert by_pair[(0, 2)] == (4, 2, 2, 3)
    # (1, 3): dx=6-1=5, dy=1-1=0, do=wrap(1-0,16)=1, ds=1-3=-2.
    assert by_pair[(1, 3)] == (5, 0, 1, -2)

    # A stroke missing its "rel" entry (a degenerate <2-point span, same exclusion
    # `compose_character_signature`'s own "rel" loop already applies) contributes NO rel2
    # relation involving it, but every OTHER pair is unaffected.
    pose_missing = dict(pose_by_k)
    del pose_missing[2]
    rel2_missing = cc._rel2_relations(pose_missing, turn_bins=16)
    assert {(r[1], r[2]) for r in rel2_missing} == {(0, 3), (1, 3)}


def test_wrap_signed_bin_seam_and_identity():
    assert cc._wrap_signed_bin(0, 16) == 0
    assert cc._wrap_signed_bin(3, 16) == 3
    assert cc._wrap_signed_bin(-3, 16) == -3
    # Straddling the seam: +7 and -7 (turn_bins=16, half=8) are only 2 bins apart the SHORT
    # way around, not 14.
    assert cc._wrap_signed_bin(7 - (-7), 16) == -2
    assert cc._wrap_signed_bin(-7 - 7, 16) == 2


def test_rel2_breaks_naive_coverage_tie_higher_order_arrangement():
    """THE headline gate, per the design's own literal wording: "two 3-stroke characters with
    IDENTICAL consecutive-pair rels but DIFFERENT stroke-1<->stroke-3 geometry ...
    indistinguishable without rel2, classified correctly with it." Hand-built at the relation
    level (mirrors this file's own `test_pose_read_off_restored_all_tiers`/`test_assignment_
    coverage_distinguishes_near_miss_from_total_miss` — no `StrokeQuantize` needed, no
    dataset): QUERY Q (3 strokes, k=0,1,2, all identity "line" so `strokeq` never
    discriminates — the arrangement is the whole point) is scored, under the pre-existing
    NAIVE `_coverage_term`, against candidate A (mismatches Q on the CONSECUTIVE k=1 "rel")
    and decoy B (mismatches Q on the k=2 "rel" — i.e. the stroke-0<->stroke-2, "1<->3"
    relationship) — both score the SAME 9/10 relations, a genuine numeric TIE (neither
    uniquely preferred, exactly Phase A's diagnosed failure mode). A is the geometrically
    RIGHT answer (its stroke-0<->stroke-2 relationship matches Q's); adding the mechanically-
    derived "rel2" fact for that ONE non-adjacent pair gives A a point B cannot get (B's own
    rel2 differs, since it is DERIVED from B's own mismatching "rel"), breaking the tie in
    A's favour — the naive metric itself is UNCHANGED (still "the SAME naive strict
    coverage"), only the relation VOCABULARY grew."""
    s = srs.Substrate()
    native = s._inner
    turn_bins = 16

    def _sig(rel):
        strokeq = [["strokeq", k, "line"] for k in range(3)]
        rel_rels = [["rel", k, *vals] for k, vals in enumerate(rel)]
        cpose = [["cpose_x", 3], ["cpose_y", 3], ["cpose_o", 0], ["cpose_s", 4]]
        pose_by_k = {k: {"x_q": v[0], "y_q": v[1], "orient_q": v[2], "scale_q": v[3]}
                    for k, v in enumerate(rel)}
        rel2 = cc._rel2_relations(pose_by_k, turn_bins)
        no_rel2 = strokeq + rel_rels + cpose
        return no_rel2, no_rel2 + rel2

    q_rel = [(0, 0, 0, 4), (2, 0, 0, 4), (4, 0, 0, 4)]
    a_rel = [(0, 0, 0, 4), (2, 0, 1, 4), (4, 0, 0, 4)]    # mismatches Q on k=1 (consecutive)
    b_rel = [(0, 0, 0, 4), (2, 0, 0, 4), (6, 0, 0, 4)]    # mismatches Q on k=2 (the 0<->2 pair)

    q_sig, q_sig_rel2 = _sig(q_rel)
    a_sig, a_sig_rel2 = _sig(a_rel)
    b_sig, b_sig_rel2 = _sig(b_rel)

    assert any(r[0] == "rel2" for r in q_sig_rel2), "the 3-stroke query must produce a rel2 fact"

    score_a_no_rel2 = float(native.evaluate(_coverage_term(q_sig, a_sig), {}))
    score_b_no_rel2 = float(native.evaluate(_coverage_term(q_sig, b_sig), {}))
    assert score_a_no_rel2 == score_b_no_rel2 == 9.0, (
        f"this gate's OWN premise (a genuine tie WITHOUT rel2) did not reproduce: "
        f"A={score_a_no_rel2}, B={score_b_no_rel2}")

    pairs_no_rel2 = [(score_a_no_rel2, 0), (score_b_no_rel2, 1)]
    winner_no_rel2 = native.evaluate(_argmax_pairs_term(pairs_no_rel2), {})
    # A tie means the Argmax cannot be relied on to prefer the geometrically correct answer —
    # do NOT assert which index wins here (that would pin an incidental tie-break rule); the
    # numeric tie itself (asserted above) is the indistinguishability the design names.

    score_a_rel2 = float(native.evaluate(_coverage_term(q_sig_rel2, a_sig_rel2), {}))
    score_b_rel2 = float(native.evaluate(_coverage_term(q_sig_rel2, b_sig_rel2), {}))
    assert score_a_rel2 == 10.0 and score_b_rel2 == 9.0, (
        f"rel2 must add exactly ONE point to the geometrically-correct candidate A and none "
        f"to decoy B: A={score_a_rel2}, B={score_b_rel2}")
    assert score_a_rel2 > score_b_rel2, (
        "WITH rel2 the tie must be broken in favour of the geometrically correct candidate")

    pairs_rel2 = [(score_a_rel2, 0), (score_b_rel2, 1)]
    winner_rel2 = native.evaluate(_argmax_pairs_term(pairs_rel2), {})
    assert winner_rel2[1] == 0, "WITH rel2 candidate A (the correct answer) must win outright"


def test_rel2_flag_purely_additive_byte_identical_with_flag_off():
    """Additivity discipline (the design's own instruction), and the DEFAULT direction this
    module chose (`include_rel2` defaults `False` — OPT-IN, unlike `include_fine_children`'s
    default-`True`, precisely so the MANY existing unflagged callers of this function across
    this codebase are UNTOUCHED): the DEFAULT (unflagged) call must reproduce the pre-rel2
    signature byte-for-byte, and `include_rel2=True` must add ONLY `rel2` relations on top —
    never alter/reorder anything else. A caller wanting the NEW headline passes
    `include_rel2=True` EXPLICITLY (mirrored by `scripts/jabberwock_omniglot_dynamic_
    quantization.py`'s RUN 9 section, which computes its "control" from the plain default
    call — UNCHANGED from every prior run — alongside an explicit `include_rel2=True` call
    for the headline)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    four_strokes = [
        (_line((0.0, 0.0), (1.0, 0.0)), "line_h"),
        (_line((1.0, 0.0), (1.0, 1.0)), "line_v"),
        (_line((1.0, 1.0), (2.0, 1.0)), "line_h"),
        (_line((2.0, 1.0), (2.0, 2.0)), "line_v"),
    ]

    default_sig = cc.compose_character_signature(native, four_strokes)["signature"]
    explicit_off_sig = cc.compose_character_signature(
        native, four_strokes, include_rel2=False)["signature"]
    with_rel2 = cc.compose_character_signature(
        native, four_strokes, include_rel2=True)["signature"]

    def _non_rel2(sig):
        return [list(r) for r in sig if r[0] != "rel2"]

    assert default_sig == explicit_off_sig, (
        "the DEFAULT call must be byte-identical to an explicit include_rel2=False call")
    assert not any(r[0] == "rel2" for r in default_sig), (
        "include_rel2 must default to False -- the many existing unflagged callers of this "
        "function must be UNAFFECTED by this lever's addition")
    assert _non_rel2(with_rel2) == default_sig, (
        "include_rel2=True must ONLY ADD rel2 relations -- everything else byte-identical")
    rel2_present = [r for r in with_rel2 if r[0] == "rel2"]
    assert rel2_present, "a 4-stroke character must produce >=1 rel2 relation (non-adjacent pairs exist)"
    pairs = {(r[1], r[2]) for r in rel2_present}
    assert pairs == {(0, 2), (0, 3), (1, 3)}

    # A 2-stroke character (every T/L/+ fixture elsewhere in this file) has NO non-adjacent
    # pair at all — rel2 is naturally empty even WITH the flag on, so every pre-existing
    # 2-stroke gate above stays valid regardless of this lever's default.
    two_stroke_sig = cc.compose_character_signature(
        native, _t_shape(), include_rel2=True)["signature"]
    assert not any(r[0] == "rel2" for r in two_stroke_sig)


def test_rel2_ignored_by_assignment_coverage_additive_scope():
    """`assignment_coverage_term` (`_stroke_records`/`_cpose_pairs`) reads only `strokeq`/
    `rel`/`strokeq_fine`/`cpose_*` — the design scopes rel2 to "the SAME naive strict
    coverage" only ("STRICTNESS IS THE SIGNAL... do NOT soften the metric"), so
    `assignment_coverage_term`'s score must be IDENTICAL whether or not `rel2` relations are
    present in the signature — confirms rel2 cannot silently change the (currently
    underperforming, per RUN 7/8) assignment-aware arm's behaviour."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    four_strokes = [
        (_line((0.0, 0.0), (1.0, 0.0)), "line_h"),
        (_line((1.0, 0.0), (1.0, 1.0)), "line_v"),
        (_line((1.0, 1.0), (2.0, 1.0)), "line_h"),
        (_line((2.0, 1.0), (2.0, 2.0)), "line_v"),
    ]
    with_rel2 = cc.compose_character_signature(
        native, four_strokes, include_rel2=True)["signature"]
    without_rel2 = cc.compose_character_signature(native, four_strokes)["signature"]

    score_with = float(native.evaluate(cc.assignment_coverage_term(with_rel2, with_rel2), {}))
    score_without = float(native.evaluate(cc.assignment_coverage_term(without_rel2, without_rel2), {}))
    assert score_with == score_without


# ===========================================================================
# Audit — no Python decisions in domains/character_compose.py.
# ===========================================================================
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")
_ALLOWED_SORT_KEYS = {"x[1]", "x[0]"}


def test_character_compose_no_python_decisions():
    src = Path(cc.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src), (
        "character_compose.py must not call argmin/argmax in Python -- classification is a "
        "held Argmax/Covers Term (see the callers in scripts/ and this test file)")
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===========================================================================
# ABS AS DEFAULT (scratchpad/HANDWRITING_DESIGN.md's "ABS AS DEFAULT" section, 2026-07-03 —
# "the generation and reading model is the same, like speech — AbS is the default. It just
# runs the same engine in reverse."). `domains/abs_read.py` (new module): PROPOSE top-K by
# the existing strict coverage (UNCHANGED, `ar.propose_top_k`), then RENDER-COMPARE each
# candidate against the query's actual observed ink via the held `StrokeRender` Term (the
# generative inverse of `StrokeQuantize`, built in PARALLEL against this design — see
# `ar._stroke_render_live()`, `SR_LIVE`/`SR_SKIP` above, the SAME "authored, not yet
# operative" pattern `SQ_LIVE`/`TD_FIX_LIVE` already established in this file). ADDITIVE:
# every gate above this line is unchanged.
def _add_stroke_node_hermetic(sub, native, name: str, points) -> int:
    """A HERMETIC stand-in for `stroke_codebook.grow_stroke_quantum` for THIS section's
    gates only: installs a `ShapeSignature{kind:"stroke"}` node directly on the live graph
    (mirrors `test_pose_read_off_restored_all_tiers`'s own `s.add_node("ShapeSignature", ...)`
    idiom above) WITHOUT going through `teach()` — `grow_stroke_quantum` persists to the
    real, checked-in `seeds/stroke_shapes.json` via `teach()`, which would otherwise leak
    test-only quanta (e.g. "shape_line"/"shape_zigzag") into that file on every local test
    run. `_find_stroke_node`/`abs_read._candidate_seg` only ever read the node's `signature`
    attr, which this reproduces exactly (canonical pose, same `_quantize` call
    `grow_stroke_quantum` itself makes)."""
    q = sc._quantize(native, points, segments=sc.DEFAULT_SEGMENTS, turn_bins=sc.DEFAULT_TURN_BINS,
                     len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                     scale_bins=sc.DEFAULT_SCALE_BINS, canonical_pose=True)
    return sub.add_node("ShapeSignature", {
        "name": name, "kind": "stroke",
        "signature": json.dumps([list(r) for r in q["signature"]])})


# ===========================================================================
def test_stroke_render_roundtrip_canonical_signature():
    """R's own round-trip gate: `StrokeQuantize(StrokeRender(sig)) == sig` for a CANONICAL
    signature at matching params — "exact at bin centers" per the design. Checks the
    INVARIANT `seg` relations specifically (the core dequantization/generation duality this
    module depends on for every render-compare call); pose-relation round-trip is the
    design's own documented "boundary caveat," not asserted here as strictly as `seg`."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s = srs.Substrate()
    native = s._inner
    pts = _line((0.0, 0.0), (1.0, -1.0), n=24)

    q = sc._quantize(native, pts, segments=sc.DEFAULT_SEGMENTS, turn_bins=sc.DEFAULT_TURN_BINS,
                     len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                     scale_bins=sc.DEFAULT_SCALE_BINS, canonical_pose=True)
    sig = [list(r) for r in q["signature"]]

    rendered = ar._render_term(sig, n_points=24, bounds=(0.0, 0.0, 1.0, 1.0),
                               turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                               grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)
    rendered_points = native.evaluate(rendered, {})
    assert rendered_points, "StrokeRender must return a non-empty polyline"

    q2 = sc._quantize(native, rendered_points, segments=sc.DEFAULT_SEGMENTS,
                      turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                      grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS,
                      canonical_pose=True)
    sig2 = [list(r) for r in q2["signature"]]

    def _seg_only(s_):
        return [r for r in s_ if r[0] == "seg"]

    assert _seg_only(sig2) == _seg_only(sig), (
        f"StrokeQuantize(StrokeRender(sig)) must reproduce the SAME invariant seg relations "
        f"at matching params: {_seg_only(sig)!r} != {_seg_only(sig2)!r}")


def test_abs_rerank_breaks_naive_coverage_tie_render_compare():
    """THE headline gate: "two characters tied under coverage but separable by render-
    compare (the run-9 tie case re-gated the AbS way)." TWO real stroke quanta are grown
    into the codebook with GENUINELY DIFFERENT geometry — "shape_line" (a straight line,
    matching the query's OWN actual ink) and "shape_zigzag" (a sharp right-angle turn). Two
    1-stroke candidate signatures are hand-built to carry the query's OWN "rel"/"cpose"
    relations verbatim (an exact tie on arrangement) but DIFFERENT `strokeq` identities
    neither of which matches the query's own placeholder identity — naive coverage TIES
    (both candidates lose the identical single `strokeq` point, gain the identical
    rel/cpose points, exactly run-9's own tie signature: "two candidates agreeing on every
    OTHER fact, differing only on the ONE fact naive coverage can't discriminate"). Render-
    compare must break the tie in favour of "shape_line" — the candidate whose STORED
    quantum, rendered at the query's OWN decoded pose, actually reproduces the query's real
    observed ink; "shape_zigzag" renders a shape geometrically unlike the query's straight
    line at that SAME pose, so its DtwTo distance must be materially higher."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()

    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    zigzag_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                  [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])
    _add_stroke_node_hermetic(s, native, "shape_line", line_pts)
    _add_stroke_node_hermetic(s, native, "shape_zigzag", zigzag_pts)

    query_pts = [(line_pts, "query_local")]
    query_sig = cc.compose_character_signature(native, query_pts)["signature"]

    def _swap_identity(sig, new_name):
        return [["strokeq", r[1], new_name] if r[0] == "strokeq" else list(r) for r in sig]

    cand_line_sig = _swap_identity(query_sig, "shape_line")
    cand_zigzag_sig = _swap_identity(query_sig, "shape_zigzag")

    naive_line = float(native.evaluate(_coverage_term(query_sig, cand_line_sig), {}))
    naive_zigzag = float(native.evaluate(_coverage_term(query_sig, cand_zigzag_sig), {}))
    assert naive_line == naive_zigzag, (
        f"this gate's OWN premise (a genuine naive-coverage TIE) did not reproduce: "
        f"line={naive_line}, zigzag={naive_zigzag}")

    res = ar.abs_rerank(
        s, query_sig, query_pts, [cand_line_sig, cand_zigzag_sig],
        [[(line_pts, "shape_line")], [(zigzag_pts, "shape_zigzag")]], k=2,
        turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
        scale_bins=sc.DEFAULT_SCALE_BINS)

    assert set(res["top_k"]) == {0, 1}, f"both tied candidates must be in the top-K: {res!r}"
    assert len(res["scores"]) == 2
    # `res["scores"]` is `[(score, candidate_index), ...]` (the SAME `(score, id)` pair shape
    # `_argmin_pairs_term` itself expects) -- invert to {candidate_index: score} for lookup.
    score_by_idx = {ci: score for (score, ci) in res["scores"]}
    assert score_by_idx[0] < score_by_idx[1], (
        f"the render-compare DtwTo distance for the MATCHING shape (index 0, 'shape_line') "
        f"must be LOWER than for the mismatching shape (index 1, 'shape_zigzag'): {res!r}")
    assert res["winner"] == 0, (
        f"AbS re-rank must break the coverage tie in favour of the candidate whose stored "
        f"quantum actually reproduces the query's observed ink: {res!r}")


def test_abs_rerank_t_l_plus_still_correct():
    """The T/L/+ proof (gate 1) must still hold end-to-end through the FULL propose+re-rank
    path, not just the bare coverage Argmax: `ar.abs_rerank` classifies each fresh instance
    of T/L/+ correctly against the {T, L, +} exemplar set — the AbS re-rank must AGREE with
    the (already-correct) coverage proposal here, not merely fail to break it."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)

    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]

    for lb, pts in shapes.items():
        query_sig = cc.compose_character_signature(native, pts)["signature"]
        res = ar.abs_rerank(s, query_sig, pts, sigs, [shapes[l2] for l2 in labels], k=3,
                            turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                            grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)
        assert res["winner"] is not None and labels[res["winner"]] == lb, (
            f"AbS re-rank must still classify {lb!r} correctly end-to-end: {res!r}")
        assert labels[res["coverage_pick"]] == lb, (
            "the logged coverage-only control must also still classify correctly here "
            "(this gate is a sanity/regression check, not the tie-breaking proof)")


def test_propose_top_k_is_bookkeeping_not_ranking():
    """`ar.propose_top_k` must return AT MOST `k` indices, contain no duplicates, and (the
    control-reproduction discipline) its FIRST element must equal what a single bare
    coverage Argmax would pick — the top-K shortlist is a superset-preserving REPEAT of the
    existing single-winner idiom, never a different metric."""
    s = srs.Substrate()
    native = s._inner
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    sigs = {name: cc.compose_character_signature(native, pts)["signature"]
            for name, pts in shapes.items()}
    labels = list(sigs)
    exemplar_sigs = [sigs[lb] for lb in labels]
    query_sig = sigs["T"]

    top_k = ar.propose_top_k(native, query_sig, exemplar_sigs, k=2)
    assert len(top_k) == 2
    assert len(set(top_k)) == len(top_k), "no duplicate indices in the shortlist"

    pairs = [(float(native.evaluate(ar._coverage_term(query_sig, exemplar_sigs[i]), {}) or 0.0), i)
            for i in range(len(exemplar_sigs))]
    winner = native.evaluate(ar._argmax_pairs_term(pairs), {})
    assert top_k[0] == winner[1], (
        "propose_top_k's FIRST pick must match a bare single-Argmax coverage winner "
        "(control reproduction)")


def test_abs_read_no_python_decisions():
    """The SAME audit `test_character_compose_no_python_decisions` runs against
    `character_compose.py`, applied to the new `domains/abs_read.py`: no Python
    argmin/argmax/sort-by-score anywhere — the top-K shortlist and the final verdict are
    both held Terms (`Argmax`/`Argmin`), never a Python ranking."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src), (
        "abs_read.py must not call argmin/argmax in Python -- the top-K proposal and the "
        "final verdict are held Argmax/Argmin Terms")
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===========================================================================
# PROPOSAL RECALL / VARIABLE-APERTURE DWELL (scratchpad/HANDWRITING_DESIGN.md's section of
# the same name, the 42855d5f residual + the radar frame's first falsifiable instance,
# 2026-07-03): RUN 10 measured coverage@5 = 53.8% — the fixed K=5 shortlist misses the true
# exemplar on ~46% of episodes before render-compare ever gets a look. `ar.propose_variable_
# k` builds the shortlist as every candidate within margin `delta` (DATA) of the top
# proposal score, via held `MaxOver` + held `FilterList` — never a Python score branch.
# `ar.abs_rerank`'s new `top_k` override param lets the SAME render-compare/Argmin verdict
# run over that shortlist (or a full-dwell all-candidates one) in place of the fixed-K
# `propose_top_k` call. ADDITIVE: every gate above this line is unchanged.
# ===========================================================================
def test_abs_rerank_top_k_override_default_matches_internal_propose_top_k():
    """Additivity discipline (design: 'the K=5 arm byte-identical'): omitting the new `top_k`
    param (`None`, the default) must reproduce EXACTLY what `abs_rerank` computed BEFORE this
    param existed — the internal `propose_top_k` call, unchanged — whether passed explicitly
    or left to the default path."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[labels.index("T")]

    explicit_top_k = ar.propose_top_k(native, query_sig, sigs, k=3)
    kwargs = dict(k=3, turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                  grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)
    res_default = ar.abs_rerank(s, query_sig, shapes["T"], sigs,
                                [shapes[l2] for l2 in labels], **kwargs)
    res_explicit = ar.abs_rerank(s, query_sig, shapes["T"], sigs,
                                 [shapes[l2] for l2 in labels], top_k=explicit_top_k, **kwargs)
    assert res_default["top_k"] == res_explicit["top_k"] == explicit_top_k
    assert res_default["winner"] == res_explicit["winner"]
    assert res_default["scores"] == res_explicit["scores"]
    assert res_default["shortlist_size"] == len(explicit_top_k)


def test_propose_variable_k_preserves_order_and_handles_empty():
    """`propose_variable_k` never re-sorts (`FilterList`'s own "ordered twin of Filter"
    contract — original candidate-index order preserved) and degrades to `[]` for an empty
    candidate set (no crash, no fabricated shortlist)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[0]

    wide = ar.propose_variable_k(native, query_sig, sigs, delta=1000.0)
    assert wide == sorted(wide), "FilterList preserves ORIGINAL candidate-index order"
    assert set(wide) <= set(range(len(sigs)))
    assert ar.propose_variable_k(native, query_sig, [], delta=0.0) == []


def test_propose_variable_k_delta_zero_passes_exact_ties_render_compare_resolves():
    """THE headline gate (design: "a query with tied proposals resolved correctly only when
    the tie set passes through (δ=0 arm)"). TWO candidates ("shape_line", matching the
    query's OWN actual ink, and "shape_zigzag", a mismatching shape) tie EXACTLY under naive
    coverage — the SAME construction `test_abs_rerank_breaks_naive_coverage_tie_render_
    compare` uses (swap only the `strokeq` identity, keep every other relation verbatim). A
    THIRD candidate ("shape_far") is perturbed on ONE relation (`cpose_x`) to score
    STRICTLY LOWER by exactly one point — the non-tied control. `propose_variable_k` at
    `delta=0` must pass through EXACTLY the tied pair (excluding the lower-scoring third,
    proving the margin filter is genuinely SELECTIVE, not "everything"), and render-compare
    over that shortlist must resolve to the candidate whose stored quantum actually
    reproduces the query's observed ink — the tie could NOT have been broken correctly
    without both tied members reaching the shortlist."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()

    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    zigzag_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                  [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])
    _add_stroke_node_hermetic(s, native, "shape_line", line_pts)
    _add_stroke_node_hermetic(s, native, "shape_zigzag", zigzag_pts)
    _add_stroke_node_hermetic(s, native, "shape_far", zigzag_pts)

    query_pts = [(line_pts, "query_local")]
    query_sig = cc.compose_character_signature(native, query_pts)["signature"]

    def _swap_identity(sig, new_name):
        return [["strokeq", r[1], new_name] if r[0] == "strokeq" else list(r) for r in sig]

    def _perturb_one(sig, pred, bump=1000):
        out, done = [], False
        for r in sig:
            r = list(r)
            if not done and r[0] == pred:
                r[1] = r[1] + bump
                done = True
            out.append(r)
        assert done, f"premise: a {pred!r} relation must exist to perturb"
        return out

    cand_line_sig = _swap_identity(query_sig, "shape_line")
    cand_zigzag_sig = _swap_identity(query_sig, "shape_zigzag")
    cand_far_sig = _perturb_one(_swap_identity(query_sig, "shape_far"), "cpose_x")

    exemplar_sigs = [cand_line_sig, cand_zigzag_sig, cand_far_sig]
    naive = [float(native.evaluate(ar._coverage_term(query_sig, es), {}) or 0.0)
             for es in exemplar_sigs]
    assert naive[0] == naive[1], f"premise: line/zigzag candidates must tie: {naive!r}"
    assert naive[2] < naive[0], f"premise: far candidate must score strictly lower: {naive!r}"

    shortlist0 = ar.propose_variable_k(native, query_sig, exemplar_sigs, delta=0.0)
    assert set(shortlist0) == {0, 1}, (
        f"delta=0 must pass through EXACTLY the tied pair, excluding the lower-scoring "
        f"candidate: {shortlist0!r}")

    candidate_stroke_points = [[(line_pts, "shape_line")], [(zigzag_pts, "shape_zigzag")],
                               [(zigzag_pts, "shape_far")]]
    res = ar.abs_rerank(s, query_sig, query_pts, exemplar_sigs, candidate_stroke_points,
                        top_k=shortlist0, turn_bins=sc.DEFAULT_TURN_BINS,
                        len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                        scale_bins=sc.DEFAULT_SCALE_BINS)
    assert res["top_k"] == shortlist0
    assert res["winner"] == 0, (
        f"render-compare over the delta=0 shortlist must break the tie in favour of the "
        f"candidate whose stored quantum actually reproduces the query's observed ink: "
        f"{res!r}")


def test_proposal_rank_matches_manual_strict_ordering():
    """`ar.proposal_rank`'s held `Count(FilterList(...))` read-off must agree with a plain
    (test-side, non-audited) manual count of strictly-higher scores, for every candidate as
    the "true" one — including the best (rank 1) and the worst (rank == n). An out-of-range
    index returns `None`, never a fabricated rank."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[labels.index("T")]
    scores = [float(native.evaluate(ar._coverage_term(query_sig, s_), {}) or 0.0) for s_ in sigs]

    for true_idx in range(len(sigs)):
        rank = ar.proposal_rank(native, query_sig, sigs, true_idx)
        expected = 1 + sum(1 for sc_ in scores if sc_ > scores[true_idx])
        assert rank == expected, f"idx={true_idx}: rank={rank} expected={expected} scores={scores!r}"

    assert ar.proposal_rank(native, query_sig, sigs, true_idx=len(sigs)) is None
    assert ar.proposal_rank(native, query_sig, sigs, true_idx=-1) is None


def test_abs_read_no_python_decisions_variable_k_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the
    variable-K addition — `propose_variable_k`/`proposal_rank`/the `top_k` override must not
    have introduced a Python argmin/argmax/sort-by-score anywhere in the module (the
    shortlist-size decision is the held `MaxOver`+`FilterList` pair, not a Python branch)."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===========================================================================
# TARGETED WIDEN + SECOND MODALITY (scratchpad/HANDWRITING_DESIGN.md's section of the same
# name, the 6db362d1 residual, 2026-07-03): state going in — delta=0 variable-K control
# 38.8% @ mean 2.05 renders; uniform widening measured monotonically HARMFUL; recall-tail: 16
# beam-reachable, 3 proposal-blind. LEVER 1 (`ar.widen_decision`/`ar.abs_rerank_targeted`'s
# `use_widen`) and LEVER 2 (`ar.propose_appearance_top_m`/`use_appearance`) — see
# `domains/abs_read.py`'s own top-of-file docstring for the full rationale. ADDITIVE: every
# gate above this line is unchanged.
# ===========================================================================
def _swap_identity(sig, new_name):
    return [["strokeq", r[1], new_name] if r[0] == "strokeq" else list(r) for r in sig]


def _perturb_one(sig, pred, bump=1000):
    out, done = [], False
    for r in sig:
        r = list(r)
        if not done and r[0] == pred:
            r[1] = r[1] + bump
            done = True
        out.append(r)
    assert done, f"premise: a {pred!r} relation must exist to perturb"
    return out


def test_widen_decision_margin_and_fit_clauses():
    """`ar.widen_decision`'s two independent clauses, checked in isolation on synthetic
    `(score, id)` pairs: (a) a razor-thin margin between the best and runner-up fires even
    when the absolute fit is excellent; (b) a lone candidate (no runner-up — the margin
    clause is structurally inert, `Lit(False)`) still fires on a poor ABSOLUTE fit alone;
    (c) a clear margin + good absolute fit never fires."""
    s = srs.Substrate()
    native = s._inner

    # (a) razor-thin margin (0.001 apart), both scores excellent in absolute terms.
    assert ar.widen_decision(native, [(0.01, 0), (0.011, 1)],
                             margin_threshold=0.01, fit_threshold=1.0) is True
    # (b) singleton shortlist (no runner-up), poor absolute fit.
    assert ar.widen_decision(native, [(5.0, 0)],
                             margin_threshold=0.01, fit_threshold=1.0) is True
    # (b') singleton shortlist, GOOD absolute fit -- margin clause inert, fit clause quiet.
    assert ar.widen_decision(native, [(0.01, 0)],
                             margin_threshold=0.01, fit_threshold=1.0) is False
    # (c) clear margin (1.0 apart) + good absolute fit -- neither clause fires.
    assert ar.widen_decision(native, [(0.01, 0), (1.01, 1)],
                             margin_threshold=0.01, fit_threshold=1.0) is False
    # empty pairs -- honest False, never a crash.
    assert ar.widen_decision(native, [], margin_threshold=0.01, fit_threshold=1.0) is False


def test_targeted_widen_recovers_coverage_excluded_candidate():
    """THE headline gate for LEVER 1: a near-tie-under-render case that only resolves when
    the widen fires. TWO wrong shapes ("shape_zigzag_a"/"shape_zigzag_b", DIFFERENT stored
    geometry, both mismatching the query) tie for the delta=0 coverage shortlist (both carry
    the query's own rel/cpose verbatim, `_swap_identity`'s construction — the SAME tie
    pattern `test_abs_rerank_breaks_naive_coverage_tie_render_compare` uses). The TRUE match
    ("shape_line", the query's own actual shape) is perturbed on ONE UNRELATED relation
    (`cpose_x`) so its naive coverage is STRICTLY LOWER — excluded from the delta=0 shortlist
    entirely (`propose_variable_k`'s own contract). Render-compare over the delta=0 shortlist
    alone can only produce a POOR absolute fit (both candidates are genuinely the wrong
    shape) — `widen_decision`'s fit clause must fire on that, and widening to
    `propose_top_k(k=3)` (every candidate, at this size) must recover "shape_line" as the
    final winner."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()

    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    zigzag_a_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                    [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])
    zigzag_b_pts = ([(0.0, y) for y in np.linspace(0.0, 0.5, 12)] +
                    [(x, 0.5) for x in np.linspace(0.0, 0.5, 12)])

    query_pts = [(line_pts, "query_local")]
    query_sig = cc.compose_character_signature(native, query_pts)["signature"]

    cand_a_sig = _swap_identity(query_sig, "shape_zigzag_a")
    cand_b_sig = _swap_identity(query_sig, "shape_zigzag_b")
    cand_true_sig = _perturb_one(_swap_identity(query_sig, "shape_line"), "cpose_x")
    exemplar_sigs = [cand_a_sig, cand_b_sig, cand_true_sig]
    candidate_stroke_points = [[(zigzag_a_pts, "shape_zigzag_a")],
                               [(zigzag_b_pts, "shape_zigzag_b")],
                               [(line_pts, "shape_line")]]

    naive = [float(native.evaluate(ar._coverage_term(query_sig, es), {}) or 0.0)
             for es in exemplar_sigs]
    assert naive[0] == naive[1], f"premise: the two wrong shapes must tie: {naive!r}"
    assert naive[2] < naive[0], f"premise: the TRUE shape must score strictly lower: {naive!r}"

    shortlist0 = ar.propose_variable_k(native, query_sig, exemplar_sigs, delta=0.0)
    assert set(shortlist0) == {0, 1}, (
        f"premise: delta=0 must exclude the true candidate entirely: {shortlist0!r}")

    res0 = ar.abs_rerank(s, query_sig, query_pts, exemplar_sigs, candidate_stroke_points,
                         top_k=shortlist0, turn_bins=sc.DEFAULT_TURN_BINS,
                         len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                         scale_bins=sc.DEFAULT_SCALE_BINS)
    best0 = min(sc_ for sc_, _ in res0["scores"])
    assert best0 > 0.0, (
        f"premise: BOTH delta=0 candidates must be a genuinely poor render-compare fit "
        f"(neither is the query's real shape): {res0!r}")
    fit_threshold = best0 * 0.5   # strictly BELOW the measured poor fit -- must trigger widen.

    result = ar.abs_rerank_targeted(
        s, query_sig, query_pts, exemplar_sigs, candidate_stroke_points, delta=0.0,
        use_widen=True, margin_threshold=0.0, fit_threshold=fit_threshold, widen_to=3,
        turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
        scale_bins=sc.DEFAULT_SCALE_BINS)
    assert result["widened"] is True, f"the poor-fit clause must fire the widen: {result!r}"
    assert result["winner"] == 2, (
        f"widening must recover the coverage-excluded TRUE candidate: {result!r}")
    assert result["budget"] == len(shortlist0) + 3, (
        f"budget must count BOTH stages' renders when widened: {result!r}")


def test_targeted_widen_does_not_fire_on_confident_verdict():
    """Additivity/precision check: the SAME T/L/+ classification
    (`test_abs_rerank_t_l_plus_still_correct`'s own construction) with `use_widen=True` but
    thresholds that describe a CONFIDENT verdict (a real render match is near-zero distance)
    must NOT widen — `abs_rerank_targeted`'s defaults (`margin_threshold=0.0`,
    `fit_threshold=+inf`) already guarantee this; this gate exercises it with the CALLER
    passing an explicit, generously-confident threshold instead of relying on the default."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[labels.index("T")]

    result = ar.abs_rerank_targeted(
        s, query_sig, shapes["T"], sigs, [shapes[l2] for l2 in labels], delta=0.0,
        use_widen=True, margin_threshold=1e6, fit_threshold=1e6, widen_to=3,
        turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
        scale_bins=sc.DEFAULT_SCALE_BINS)
    assert result["widened"] is False, (
        f"a confident (near-zero-distance) render-compare verdict must not widen even with "
        f"lax-looking thresholds evaluated correctly against the ACTUAL scores: {result!r}")
    assert labels[result["winner"]] == "T"


def test_appearance_proposes_fragmented_decode_case():
    """THE headline gate for LEVER 2: a fragmented-decode case where appearance proposes what
    coverage cannot. The query's composed signature carries an identity ("query_only_identity")
    that no candidate's signature holds — a stand-in for "the query's decode fragmented
    differently from the true exemplar's own decode," per the design. Candidate 0 (the TRUE
    match) is composed from UNRELATED geometry (its signature only coincidentally shares a
    couple of frame-relative points that any single-stroke character's own self-normalizing
    frame produces — its `strokeq` identity never matches) but its own STORED observed ink is
    the query's OWN actual raw points — appearance must find it. Candidate 1 (the coverage
    DECOY) is given the query's OWN relations verbatim (maximal naive coverage, strictly
    HIGHER than candidate 0's) but its own stored observed ink is a totally different shape —
    appearance must NOT prefer it."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    other_pts = _line((0.0, 0.0), (0.0, -1.0), n=24)
    zigzag_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                  [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])

    query_stroke_points = [(line_pts, "query_only_identity")]
    query_sig = cc.compose_character_signature(native, query_stroke_points)["signature"]

    cand0_sig = cc.compose_character_signature(native, [(other_pts, "unrelated_id")])["signature"]
    cand0_stroke_points = [(line_pts, "unrelated_id")]     # OBSERVED ink == the query's own.

    cand1_sig = list(query_sig)                            # identical relations -> max coverage.
    cand1_stroke_points = [(zigzag_pts, "query_only_identity")]

    naive = [float(native.evaluate(ar._coverage_term(query_sig, cand0_sig), {}) or 0.0),
             float(native.evaluate(ar._coverage_term(query_sig, cand1_sig), {}) or 0.0)]
    assert naive[1] > naive[0], (
        f"premise: candidate 1 must win on naive coverage (candidate 0's own "
        f"`strokeq` identity never matches the query's; the two DO NOT tie): {naive!r}")

    exemplar_sigs = [cand0_sig, cand1_sig]
    candidate_stroke_points = [cand0_stroke_points, cand1_stroke_points]

    structural = ar.propose_variable_k(native, query_sig, exemplar_sigs, delta=0.0)
    assert structural == [1], (
        f"premise: the structural proposal must miss candidate 0 entirely: {structural!r}")

    _, q_slices = ar._stroke_frame_slices(query_stroke_points)
    cand_slices = [ar._stroke_frame_slices(cp)[1] for cp in candidate_stroke_points]
    appearance = ar.propose_appearance_top_m(native, q_slices, cand_slices, m=2)
    assert appearance[0] == 0, (
        f"appearance must propose candidate 0 FIRST -- its observed ink IS the query's own "
        f"raw points, unlike the coverage winner's mismatching ink: {appearance!r}")

    result = ar.abs_rerank_targeted(
        s, query_sig, query_stroke_points, exemplar_sigs, candidate_stroke_points, delta=0.0,
        use_appearance=True, appearance_m=2, turn_bins=sc.DEFAULT_TURN_BINS,
        len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)
    assert 0 in result["shortlist0"], (
        f"the second modality must ADD the structurally-invisible true candidate to the "
        f"shortlist: {result!r}")
    assert result["winner"] == 0, (
        f"once in the shortlist, whole-ink compare must correctly prefer the candidate whose "
        f"OWN observed ink matches the query's: {result!r}")


def test_abs_rerank_targeted_delta0_control_byte_identical():
    """Additivity discipline (design: "delta=0 arm byte-identical"): `abs_rerank_targeted`
    with both levers OFF must reproduce EXACTLY what RUN 11's own `propose_variable_k(0.0)` +
    `abs_rerank` pair computes — the control arm's own code path, untouched."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[labels.index("T")]
    candidate_stroke_points = [shapes[l2] for l2 in labels]

    kwargs = dict(turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                  grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)
    shortlist_direct = ar.propose_variable_k(native, query_sig, sigs, delta=0.0)
    res_direct = ar.abs_rerank(s, query_sig, shapes["T"], sigs, candidate_stroke_points,
                               top_k=shortlist_direct, **kwargs)
    res_targeted = ar.abs_rerank_targeted(
        s, query_sig, shapes["T"], sigs, candidate_stroke_points, delta=0.0,
        use_widen=False, use_appearance=False, **kwargs)

    assert res_targeted["winner"] == res_direct["winner"]
    assert res_targeted["scores"] == res_direct["scores"]
    assert res_targeted["top_k"] == res_direct["top_k"] == shortlist_direct
    assert res_targeted["widened"] is False
    assert res_targeted["appearance0"] == []
    assert res_targeted["structural0"] == shortlist_direct
    assert res_targeted["shortlist0"] == shortlist_direct
    assert res_targeted["budget"] == len(shortlist_direct)


def test_abs_read_no_python_decisions_targeted_widen_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the TARGETED
    WIDEN + SECOND MODALITY addition — `widen_decision`/`propose_appearance_top_m`/
    `abs_rerank_targeted` must not have introduced a Python argmin/argmax/sort-by-score
    anywhere in the module (the widen verdict is the held `Or(Lt(...), Gt(...))` Term, the
    shortlist union is a plain `set`/`sorted` over candidate INDICES, never a score-keyed
    ranking)."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===========================================================================
# INSTANCE-CONDITIONED QUANTA (scratchpad/HANDWRITING_DESIGN.md's section of the same name,
# the a6c7740f endgame clause, 2026-07-03): state going in — 41.2% (delta=0 + appearance);
# far-tail 0/3 reachable by any SEARCH arm; the residual read as EXEMPLAR-SIDE (the
# render-compare verdict approximates every candidate through the GLOBAL codebook's small
# vocabulary, discarding the exemplar's own actual geometry). LEVER A (`exemplar_true` on
# `abs_render_compare_term`/`abs_rerank`) and LEVER B (`instance_conditioned_signatures`/
# `abs_rerank_targeted`'s `use_instance`) — see `domains/abs_read.py`'s own top-of-file
# docstring for the full rationale. ADDITIVE: every gate above this line is unchanged.
# ===========================================================================
def test_exemplar_true_rendering_separates_shared_global_quantum_candidates():
    """THE decisive LEVER A gate (design: "exemplar-true rendering separates two exemplars
    that share identical global-quantum approximations but differ in actual stroke shape").
    Candidates A and B are BOTH recognized as the SAME global stroke quantum ("shape_line" —
    `_swap_identity` gives them byte-IDENTICAL composed signatures), so (1) naive coverage
    ties them outright and (2) the PRE-EXISTING `exemplar_true=False` render-compare ALSO
    ties them (`_candidate_seg` looks up ONE shared codebook entry for both — the
    "information bound" the design names: the specific exemplar's own geometry is discarded).
    Candidate A's own STORED points are the query's own actual ink (a real match); candidate
    B's own STORED points are a genuinely different shape (a false match that merely happened
    to quantize into the same global bucket). `exemplar_true=True` must break the tie in favor
    of A — the ONLY configuration under test that ever looks at each candidate's own points."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()

    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    zigzag_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                  [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])
    _add_stroke_node_hermetic(s, native, "shape_line", line_pts)   # the ONE shared global quantum.

    query_pts = [(line_pts, "query_local")]
    query_sig = cc.compose_character_signature(native, query_pts)["signature"]

    cand_a_sig = _swap_identity(query_sig, "shape_line")
    cand_b_sig = _swap_identity(query_sig, "shape_line")
    assert cand_a_sig == cand_b_sig, (
        "premise: both candidates recognized as the SAME global quantum -- byte-identical "
        "composed signatures")
    candidate_stroke_points = [[(line_pts, "shape_line")], [(zigzag_pts, "shape_line")]]

    kwargs = dict(k=2, turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                  grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS,
                  segments=sc.DEFAULT_SEGMENTS)

    res_global = ar.abs_rerank(s, query_sig, query_pts, [cand_a_sig, cand_b_sig],
                               candidate_stroke_points, exemplar_true=False, **kwargs)
    score_global = {ci: score for (score, ci) in res_global["scores"]}
    assert score_global[0] == score_global[1], (
        f"premise: the GLOBAL-quantum render must tie (both candidates render the SAME "
        f"shared codebook entry, discarding each candidate's own actual geometry): "
        f"{res_global!r}")

    res_exemplar = ar.abs_rerank(s, query_sig, query_pts, [cand_a_sig, cand_b_sig],
                                 candidate_stroke_points, exemplar_true=True, **kwargs)
    score_exemplar = {ci: score for (score, ci) in res_exemplar["scores"]}
    assert score_exemplar[0] < score_exemplar[1], (
        f"exemplar-true rendering must separate the two candidates -- A's own stored points "
        f"ARE the query's actual ink, B's are a genuinely different shape: {res_exemplar!r}")
    assert res_exemplar["winner"] == 0, (
        f"exemplar-true rendering must break the global-quantum tie in favor of the "
        f"candidate whose OWN geometry actually matches the query: {res_exemplar!r}")


def test_instance_decode_query_assigns_exemplar_stroke_identity():
    """THE headline gate for LEVER B (design: "instance-decode assigns a query stroke the
    exemplar-stroke identity when it matches the exemplar better than any global quantum").
    Two candidates' own stroke points are hand-built (no global codebook entries at all —
    "better than any global quantum" trivially holds when there IS no global quantum): the
    query's own points are IDENTICAL to candidate 1's own stroke, and genuinely different
    from candidate 0's. `instance_decode_query` must resolve the query's stroke to EXACTLY
    `_instance_name(1, 0)` — candidate 1's own stroke 0 — never candidate 0's."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner

    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    zigzag_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                  [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])
    candidate_stroke_points = [[(zigzag_pts, "c0")], [(line_pts, "c1")]]
    query_stroke_points = [(line_pts, "query_local")]

    kwargs = dict(segments=sc.DEFAULT_SEGMENTS, turn_bins=sc.DEFAULT_TURN_BINS,
                  len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                  scale_bins=sc.DEFAULT_SCALE_BINS)
    scratch, names = ar.build_instance_codebook(candidate_stroke_points, **kwargs)
    assert names == {(0, 0): ar._instance_name(0, 0), (1, 0): ar._instance_name(1, 0)}

    q_extra = ar.instance_decode_query(scratch._inner, query_stroke_points, **kwargs)
    assert q_extra == [["strokeq_instance", 0, ar._instance_name(1, 0)]], (
        f"the query's own stroke must resolve to candidate 1's OWN instance identity "
        f"(its points are identical to the query's), never candidate 0's: {q_extra!r}")


def test_instance_conditioned_signatures_make_proposal_class_specific():
    """LEVER B's full combinator (`instance_conditioned_signatures`): TWO candidates
    recognized as the SAME generic global identity (naive coverage ties them outright,
    mirroring `test_exemplar_true_rendering_separates_shared_global_quantum_candidates`'s own
    premise) — candidate 0's own stroke IS the query's actual ink, candidate 1's is not. The
    EXISTING strict-coverage Term (`_coverage_term`, UNCHANGED), fed the instance-conditioned
    signatures, must now score candidate 0 STRICTLY HIGHER than candidate 1 — "making the
    strict-coverage proposal CLASS-SPECIFIC" for free, off an ADDITIVE relation."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()

    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    zigzag_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                  [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])
    query_pts = [(line_pts, "query_local")]
    query_sig = cc.compose_character_signature(native, query_pts)["signature"]
    cand0_sig = _swap_identity(query_sig, "generic")
    cand1_sig = _swap_identity(query_sig, "generic")
    assert cand0_sig == cand1_sig, "premise: both candidates share one generic identity"

    candidate_stroke_points = [[(line_pts, "generic")], [(zigzag_pts, "generic")]]
    query_stroke_points = query_pts

    naive0 = float(native.evaluate(_coverage_term(query_sig, cand0_sig), {}) or 0.0)
    naive1 = float(native.evaluate(_coverage_term(query_sig, cand1_sig), {}) or 0.0)
    assert naive0 == naive1, "premise: naive coverage must tie before instance-conditioning"

    kwargs = dict(segments=sc.DEFAULT_SEGMENTS, turn_bins=sc.DEFAULT_TURN_BINS,
                  len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                  scale_bins=sc.DEFAULT_SCALE_BINS)
    q_inst, cand_inst = ar.instance_conditioned_signatures(
        query_sig, query_stroke_points, [cand0_sig, cand1_sig], candidate_stroke_points,
        **kwargs)

    score0 = float(native.evaluate(_coverage_term(q_inst, cand_inst[0]), {}) or 0.0)
    score1 = float(native.evaluate(_coverage_term(q_inst, cand_inst[1]), {}) or 0.0)
    assert score0 > score1, (
        f"instance-conditioning must break the naive-coverage tie in favor of the candidate "
        f"whose OWN stroke matches the query: score0={score0} score1={score1}")
    assert score0 == naive0 + 1.0, (
        "the instance boost must be PURELY ADDITIVE -- exactly one extra relation hit on top "
        f"of the unchanged naive coverage: {score0!r} vs {naive0!r}")
    assert score1 == naive1, (
        "the losing candidate's score must be UNCHANGED by instance-conditioning (no "
        f"fabricated penalty): {score1!r} vs {naive1!r}")


def test_instance_codebook_episode_scoped_no_leakage():
    """Design: "episode-scoping (no cross-episode leakage — assert the codebook/graph state
    identical before/after an episode)." `build_instance_codebook`/`instance_conditioned_
    signatures` never receive the agent's own substrate at all (a structural guarantee, not
    merely an empirical one — see their own signatures), but this gate checks it empirically
    too: a full `graph_to_dict()` snapshot of the AGENT's held substrate, taken before and
    after an `instance_conditioned_signatures` call using unrelated synthetic data, must be
    BYTE IDENTICAL — nothing the call does (installing instance quanta into ITS OWN scratch
    substrate, decoding against it) ever touches the agent's graph. Also checks the LEARN
    codebook specifically: `stroke_codebook._existing_names(s, "stroke")` is empty before and
    after (no instance quantum ever leaks into the real, persisted codebook)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()

    line_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    zigzag_pts = ([(x, 0.0) for x in np.linspace(0.0, 0.5, 12)] +
                  [(0.5, y) for y in np.linspace(0.0, 0.5, 12)])
    query_pts = [(line_pts, "query_local")]
    query_sig = cc.compose_character_signature(native, query_pts)["signature"]
    cand0_sig = _swap_identity(query_sig, "generic")
    cand1_sig = _swap_identity(query_sig, "generic")
    candidate_stroke_points = [[(line_pts, "generic")], [(zigzag_pts, "generic")]]

    snapshot_before = s._inner.graph_to_dict()
    codebook_before = sc._existing_names(s, "stroke")

    ar.instance_conditioned_signatures(
        query_sig, query_pts, [cand0_sig, cand1_sig], candidate_stroke_points,
        segments=sc.DEFAULT_SEGMENTS, turn_bins=sc.DEFAULT_TURN_BINS,
        len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)

    snapshot_after = s._inner.graph_to_dict()
    codebook_after = sc._existing_names(s, "stroke")
    assert snapshot_after == snapshot_before, (
        "the agent's own held graph must be byte-identical before/after an "
        "instance-conditioned episode -- no leakage")
    assert codebook_after == codebook_before == set(), (
        "the LEARN codebook (real, persisted stroke quanta) must be untouched by an "
        "episode-scoped instance codebook")


def test_abs_rerank_targeted_run12_control_byte_identical_with_levers_off():
    """Additivity discipline (design: "run-12 adopted config as control... must reproduce
    41.2%"): `abs_rerank_targeted` with `use_exemplar_true=False, use_instance=False` (RUN
    13's own control arm config) must reproduce EXACTLY what RUN 12's own `+appearance` arm
    computes (`use_widen=False, use_appearance=True`, no instance/exemplar-true levers) —
    the pre-existing code path, untouched."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[labels.index("T")]
    candidate_stroke_points = [shapes[l2] for l2 in labels]

    kwargs = dict(turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                  grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)
    res_run12 = ar.abs_rerank_targeted(
        s, query_sig, shapes["T"], sigs, candidate_stroke_points, delta=0.0,
        use_widen=False, use_appearance=True, **kwargs)
    res_run13_control = ar.abs_rerank_targeted(
        s, query_sig, shapes["T"], sigs, candidate_stroke_points, delta=0.0,
        use_widen=False, use_appearance=True, use_exemplar_true=False, use_instance=False,
        **kwargs)

    assert res_run13_control["winner"] == res_run12["winner"]
    assert res_run13_control["scores"] == res_run12["scores"]
    assert res_run13_control["shortlist0"] == res_run12["shortlist0"]
    assert res_run13_control["budget"] == res_run12["budget"]
    assert res_run13_control["widened"] is False


def test_abs_read_no_python_decisions_instance_conditioned_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the
    INSTANCE-CONDITIONED QUANTA addition — `_exemplar_true_seg`/`build_instance_codebook`/
    `instance_decode_query`/`instance_conditioned_signatures` must not have introduced a
    Python argmin/argmax/sort-by-score anywhere in the module (every identity assignment is a
    held `ShapeDecode`/`StrokeQuantize` evaluate's own `covered_by` read-off, never a Python
    ranking)."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===========================================================================
# BRANCH B CONTINUOUS — JUNCTION-BLENDED RENDERING (scratchpad/HANDWRITING_DESIGN.md's
# "RUN 15 — POWER THE GATE, THEN BRANCH B CONTINUOUS" section, PHASE 2, 2026-07-03): the
# surviving fork hypothesis (junction coarticulation) executed as a CONTINUOUS endpoint
# deformation inside the AbS render-compare channel — "no context-conditioned quanta, no new
# discrete relations." `ar._junction_blend` (pure mechanical geometry) + `ar.abs_render_
# compare_term`'s new `junction_blend`/`junction_frac` params — see `domains/abs_read.py`'s
# own top-of-file docstring for the full rationale. ADDITIVE: every gate above this line is
# unchanged.
# ===========================================================================
def test_junction_blend_bounded_endpoint_anchored_taper():
    """`ar._junction_blend`'s own mechanics, directly: TWO draw-order-consecutive rendered
    strokes with a REAL positional gap at their shared joint (stroke 0's own last point !=
    stroke 1's own first point — the honest artifact of two strokes rendered/reconstructed
    independently). After blending: (1) the two endpoints SNAP EXACTLY to their shared
    midpoint (full taper strength, `w=1.0`, at the single outermost point of each blended
    span); (2) every point STRICTLY OUTSIDE the blended span is BYTE IDENTICAL to the input
    (the deformation never touches a stroke's interior beyond `j_frac`); (3) `j_frac<=0`
    returns the ORIGINAL dict object unchanged (the flag-off no-op, byte-identical)."""
    stroke0 = [[0.0, 0.0], [0.5, 0.0], [0.8, 0.0], [1.0, 0.0]]     # ends at (1.0, 0.0)
    stroke1 = [[1.3, 0.2], [1.6, 0.2], [1.9, 0.2], [2.2, 0.2]]     # starts at (1.3, 0.2)
    rendered = {0: [list(p) for p in stroke0], 1: [list(p) for p in stroke1]}

    off = ar._junction_blend(rendered, 0.0)
    assert off is rendered, "j_frac<=0 must be an exact no-op (same object, byte-identical)"

    blended = ar._junction_blend(rendered, 0.3)      # round(0.3*4) == 1 point per side
    joint = ((np.asarray(stroke0[-1]) + np.asarray(stroke1[0])) / 2.0).tolist()
    assert blended[0][-1] == pytest.approx(joint), "stroke 0's last point must snap to the joint"
    assert blended[1][0] == pytest.approx(joint), "stroke 1's first point must snap to the joint"
    # Interior points (everything but the single blended point per side) untouched.
    assert blended[0][:-1] == stroke0[:-1]
    assert blended[1][1:] == stroke1[1:]
    # The ORIGINAL input dict must never be mutated.
    assert rendered[0][-1] == [1.0, 0.0] and rendered[1][0] == [1.3, 0.2]


def test_junction_blend_no_neighbour_or_short_stroke_left_untouched():
    """A single, isolated stroke (no draw-order neighbour) and a degenerate (<2 point)
    neighbour are both honest non-crashes — `_junction_blend` leaves them untouched rather
    than fabricating a junction."""
    solo = {0: [[0.0, 0.0], [1.0, 0.0]]}
    assert ar._junction_blend(solo, 0.3) == {0: [[0.0, 0.0], [1.0, 0.0]]}

    degenerate = {0: [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]], 1: [[5.0, 5.0]]}
    out = ar._junction_blend(degenerate, 0.3)
    assert out[0] == degenerate[0] and out[1] == degenerate[1], (
        "a <2-point neighbour must not be blended into or warped toward — left untouched")


def test_junction_blend_separates_a_naive_render_tie_the_decisive_case():
    """THE decisive gate (design: "two exemplars identical except junction-adjacent
    deformation, separated only with blend on"). Two candidates share an IDENTICAL stroke 0
    and an IDENTICAL stroke 1 EXCEPT for stroke 1's single joint-adjacent point (its very
    first point), which is offset from the query's own true joint point by `+eps` (candidate
    A) or `-eps` (candidate B) — a deformation confined entirely to the junction, every other
    point of every stroke byte-identical between A and B and equal to the query's own ink.

    UNBLENDED: the mean per-stroke `DtwTo` distance to the query TIES EXACTLY for A and B —
    a real, provable symmetry (swapping the sign of a single-point offset at one END of a
    two-term sum swaps which term carries `+eps`/`-eps`, leaving the SUM unchanged). Naive
    per-stroke render-compare is BLIND to which of the two candidates has the "right" junction
    sign — it cannot separate them at all.

    BLENDED (`j_frac` wide enough to warp >=2 points per side — the single-point-snap case
    stays tied by the SAME symmetry, `w=1.0` for both A and B's outermost point, so THIS gate
    specifically needs a wider `j_frac`, verified numerically not asserted from first
    principles): the tie breaks. The mechanism needs no candidate-vs-candidate asymmetry
    beyond the deformation itself — it is a direct, honest consequence of `_junction_blend`'s
    linear taper interacting differently with `+eps` vs `-eps` once more than the single
    endpoint is involved."""
    E = (1.0, 0.0)
    S = (1.3, 0.2)
    query_stroke0 = [(0.0, 0.0), (0.5, 0.0), (0.8, 0.0), E]
    query_stroke1 = [S, (1.6, 0.2), (1.9, 0.2), (2.2, 0.2)]
    query_by_k = {0: [list(p) for p in query_stroke0], 1: [list(p) for p in query_stroke1]}

    eps = 0.12
    cand_a = {0: [list(p) for p in query_stroke0],
              1: [[S[0] + eps, S[1] + eps]] + [list(p) for p in query_stroke1[1:]]}
    cand_b = {0: [list(p) for p in query_stroke0],
              1: [[S[0] - eps, S[1] - eps]] + [list(p) for p in query_stroke1[1:]]}

    def _mean_dtw(rendered_by_k):
        terms = [ar._dtw_term({"type": "Lit", "value": rendered_by_k[k]}, query_by_k[k])
                 for k in sorted(rendered_by_k)]
        return {"type": "Div", "a": {"type": "Plus", "items": terms},
                "b": {"type": "Lit", "value": float(len(terms))}}

    s = srs.Substrate()
    native = s._inner

    score_a_unblended = native.evaluate(_mean_dtw(cand_a), {})
    score_b_unblended = native.evaluate(_mean_dtw(cand_b), {})
    assert score_a_unblended == pytest.approx(score_b_unblended, abs=1e-9), (
        f"premise: naive (unblended) render-compare must TIE exactly on this junction-only "
        f"deformation: a={score_a_unblended!r} b={score_b_unblended!r}")

    blended_a = ar._junction_blend(cand_a, 0.5)      # round(0.5*4) == 2 points per side
    blended_b = ar._junction_blend(cand_b, 0.5)
    score_a_blended = native.evaluate(_mean_dtw(blended_a), {})
    score_b_blended = native.evaluate(_mean_dtw(blended_b), {})
    assert score_a_blended != pytest.approx(score_b_blended, abs=1e-6), (
        f"junction blending must separate the two candidates the naive comparison could not: "
        f"a={score_a_blended!r} b={score_b_blended!r}")


def test_abs_render_compare_term_junction_blend_off_byte_identical():
    """Additivity discipline (design: "flag-gated, off = byte-identical"): omitting
    `junction_blend` (the default `False`) must produce the EXACT SAME comparison Term dict
    as the pre-existing call shape — no extra `native.evaluate` call is even made in this mode
    (`abs_render_compare_term`'s own docstring)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[labels.index("T")]
    q_bbox, q_slices = ar._stroke_frame_slices(shapes["T"])

    kwargs = dict(n_points=ar.DEFAULT_RENDER_N_POINTS, turn_bins=sc.DEFAULT_TURN_BINS,
                  len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                  scale_bins=sc.DEFAULT_SCALE_BINS)
    term_default = ar.abs_render_compare_term(s, query_sig, q_slices, q_bbox, sigs[0], **kwargs)
    term_explicit_off = ar.abs_render_compare_term(s, query_sig, q_slices, q_bbox, sigs[0],
                                                    junction_blend=False, **kwargs)
    assert term_default == term_explicit_off, (
        "junction_blend=False (explicit) must reproduce the omitted-kwarg default EXACTLY")


def test_abs_rerank_targeted_junction_blend_off_byte_identical_with_run12_control():
    """Additivity at the `abs_rerank_targeted` combinator level: `use_junction_blend=False`
    (the default) must reproduce EXACTLY RUN 12's own adopted control arm
    (`use_widen=False, use_appearance=True`) — the pre-existing arms are untouched by the new
    flag's mere existence."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]
    query_sig = sigs[labels.index("T")]
    candidate_stroke_points = [shapes[l2] for l2 in labels]
    kwargs = dict(turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                  grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS)

    res_control = ar.abs_rerank_targeted(s, query_sig, shapes["T"], sigs, candidate_stroke_points,
                                         delta=0.0, use_widen=False, use_appearance=True, **kwargs)
    res_jb_off = ar.abs_rerank_targeted(s, query_sig, shapes["T"], sigs, candidate_stroke_points,
                                        delta=0.0, use_widen=False, use_appearance=True,
                                        use_junction_blend=False, **kwargs)
    assert res_jb_off["winner"] == res_control["winner"]
    assert res_jb_off["scores"] == res_control["scores"]
    assert res_jb_off["shortlist0"] == res_control["shortlist0"]
    assert res_jb_off["budget"] == res_control["budget"]


def test_abs_rerank_junction_blend_on_still_classifies_t_l_plus_correctly():
    """A live end-to-end sanity/regression check (not the decisive tie-break proof above):
    `junction_blend=True` must not BREAK the already-correct T/L/+ classification — every
    query still resolves to its own label with blending on, at a realistic `junction_frac`."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not SR_LIVE:
        pytest.skip(SR_SKIP)
    s, ag, native = _boot()
    vert_pts = _line((0.0, 0.0), (0.0, -1.0))
    horiz_pts = _line((-0.5, 0.0), (0.5, 0.0))
    _add_stroke_node_hermetic(s, native, "line_v", vert_pts)
    _add_stroke_node_hermetic(s, native, "line_h", horiz_pts)
    shapes = {"T": _t_shape(), "L": _l_shape(), "+": _plus_shape()}
    labels = list(shapes)
    sigs = [cc.compose_character_signature(native, shapes[lb])["signature"] for lb in labels]

    for lb, pts in shapes.items():
        query_sig = cc.compose_character_signature(native, pts)["signature"]
        res = ar.abs_rerank(s, query_sig, pts, sigs, [shapes[l2] for l2 in labels], k=3,
                            turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                            grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS,
                            junction_blend=True, junction_frac=ar.DEFAULT_JUNCTION_FRAC)
        assert res["winner"] is not None and labels[res["winner"]] == lb, (
            f"junction_blend=True must not break the already-correct classification of {lb!r}: "
            f"{res!r}")


def test_abs_read_no_python_decisions_junction_blend_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the BRANCH B
    CONTINUOUS addition — `_junction_blend`/`abs_render_compare_term`'s new branch must not
    have introduced a Python argmin/argmax/sort-by-score anywhere in the module (the blend is
    pure mechanical geometry over an already-computed render, never a ranking decision)."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===========================================================================
# RECONCILIATION -- SC+TPS CONTINUOUS VERDICT (RUN 16, scratchpad/HANDWRITING_DESIGN.md's
# "RECONCILIATION" section, 2026-07-03): the earlier Family-A arc
# (`domains/analysis_by_synthesis.py`) hit 78-81.5% using FUSED CONTINUOUS comparators
# (ShapeContextDist + TpsDeformDist [+ SmoothDeformDist]) over RAW point-sets, decided by a
# held Argmax/Argmin — this gate's own DtwTo-on-quantized-renders verdict is the weak
# comparator RUN 11's K=20 full-dwell ablation already implicated. `ar.whole_figure_point_set`
# / `ar.sctps_verdict_term` / `ar.sctps_rerank` transplant that fused verdict as a held Term
# (never a Python argmin), additive — nothing above this line is touched.
# ===========================================================================
def _circle_points(n=80, r=1.0, cx=0.0, cy=0.0):
    return [[cx + r * np.cos(t), cy + r * np.sin(t)] for t in np.linspace(0.0, 2 * np.pi, n,
                                                                            endpoint=False)]


def test_whole_figure_point_set_degenerate_inputs_return_none():
    """Honest-miss discipline (mirrors `analysis_by_synthesis.point_set`'s own contract):
    fewer than 3 raw points, or zero arc length (all points coincident), must return `None`
    rather than a fabricated point-set."""
    assert ar.whole_figure_point_set([([[0.0, 0.0], [1.0, 0.0]], "s0")]) is None, (
        "a single 2-point stroke (< 3 raw points total) must be an honest None")
    assert ar.whole_figure_point_set(
        [([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]], "s0")]) is None, (
        "zero arc length (coincident points) must be an honest None")


def test_whole_figure_point_set_resamples_to_n_and_normalizes():
    """Mechanical adapter contract: output has exactly `n_points` rows, and is centred +
    scale-normalized (mirrors `analysis_by_synthesis.point_set`'s own centroid/abs-max
    convention) — never a decision, just resample+normalize."""
    line = [[float(x), 0.0] for x in np.linspace(0.0, 10.0, 40)]
    ps = ar.whole_figure_point_set([(line, "s0")], n_points=24)
    assert ps is not None and len(ps) == 24
    arr = np.asarray(ps)
    assert abs(arr.mean(0)[0]) < 1e-6 and abs(arr.mean(0)[1]) < 1e-6, (
        "output must be centred at its own centroid")
    assert abs(np.abs(arr).max() - 1.0) < 1e-6, "output must be abs-max normalized to 1.0"


def test_sctps_verdict_term_include_smooth_purely_additive():
    """Byte-identity off-flag discipline (this codebase's own established convention, e.g.
    `test_rel2_flag_purely_additive_byte_identical_with_flag_off` /
    `test_abs_render_compare_term_junction_blend_off_byte_identical`): the default
    (`include_smooth=False`) must be byte-identical to an explicit `include_smooth=False`
    call, and `include_smooth=True` must ONLY ADD one `SmoothDeformDist` item — the two
    pre-existing items (`ShapeContextDist`, `TpsDeformDist`) stay byte-identical either way."""
    a, b = _circle_points(n=8), _circle_points(n=8, r=1.2)
    default_term = ar.sctps_verdict_term(a, b)
    explicit_off_term = ar.sctps_verdict_term(a, b, include_smooth=False)
    assert default_term == explicit_off_term, (
        "the DEFAULT call must be byte-identical to an explicit include_smooth=False call")
    assert [it["type"] for it in default_term["items"]] == ["ShapeContextDist", "TpsDeformDist"]

    with_smooth_term = ar.sctps_verdict_term(a, b, include_smooth=True)
    assert with_smooth_term["items"][:2] == default_term["items"], (
        "include_smooth=True must ONLY ADD a SmoothDeformDist item -- the first two items "
        "stay byte-identical")
    assert [it["type"] for it in with_smooth_term["items"]] == [
        "ShapeContextDist", "TpsDeformDist", "SmoothDeformDist"]


def test_sctps_rerank_picks_the_true_matching_point_set_held_argmin():
    """THE verdict-builder held-Term audit: a query point-set (a circle) vs three candidates —
    one an EXACT copy of the query, one a scaled/rotated variant of a DIFFERENT shape (a
    square), one pure noise — `sctps_rerank`'s held `Argmin` over the fused
    ShapeContextDist+TpsDeformDist score must pick the exact-copy candidate. Confirms the
    verdict is genuinely computed by the held Terms (not a fluke of the shortlist order) by
    running the SAME candidates in reversed shortlist order and getting the SAME winning
    index."""
    native = srs.Substrate()._inner
    rng = np.random.default_rng(0)
    query = _circle_points(n=48)
    exact = [list(p) for p in query]                      # candidate 0: exact match
    square = [[x, y] for x in (-1.0, 1.0) for y in (-1.0, 1.0)] * 12
    square = square[:48]                                    # candidate 1: a different shape
    noise = rng.normal(size=(48, 2)).tolist()               # candidate 2: pure noise

    res = ar.sctps_rerank(native, query, [exact, square, noise], [0, 1, 2])
    assert res["winner"] == 0, f"the exact-copy candidate must win the held Argmin: {res!r}"
    assert res["n_compared"] == 3

    # order independence: the shortlist is a Python-assembled index list, but the DECISION
    # (Argmin) is a held Term over (score, id) pairs -- reversing input order must not change
    # which INDEX wins.
    res_rev = ar.sctps_rerank(native, query, [exact, square, noise], [2, 1, 0])
    assert res_rev["winner"] == 0


def test_sctps_rerank_skips_degenerate_candidates_and_falls_back_honestly():
    """Honest non-crash: a `None` point-set in the candidate list (degenerate ink) is skipped
    -- never a fabricated score -- and an all-degenerate/empty shortlist falls back to
    `shortlist[0]` (mirrors `abs_rerank`'s own `coverage_pick` fallback discipline), never a
    crash."""
    native = srs.Substrate()._inner
    query = _circle_points(n=16)
    res = ar.sctps_rerank(native, query, [None, [list(p) for p in query]], [0, 1])
    assert res["winner"] == 1 and res["n_compared"] == 1

    res_none_query = ar.sctps_rerank(native, None, [[list(p) for p in query]], [0])
    assert res_none_query["winner"] == 0 and res_none_query["n_compared"] == 0


def test_abs_read_no_python_decisions_sctps_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the
    RECONCILIATION (SC+TPS continuous verdict) addition -- `sctps_verdict_term`/`sctps_rerank`
    must not have introduced a Python argmin/argmax/sort-by-score anywhere in the module (the
    final pick is the SAME held `_argmin_pairs_term` idiom `abs_rerank` already uses)."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# --------------------------------------------------------------------------- #
#  RUN 17 -- CLOSE THE GAP (tuned fusion / ensemble members / parse marginalization):
#  additive verdict-builder extensions in domains/abs_read.py. Gates: (1) weighted-verdict
#  byte-identity at unit weights (the additivity discipline every prior lever obeys);
#  (2) weighted-verdict correctness (weights actually steer the held verdict); (3) the
#  ScTpsDist-alone ensemble member picks the true match via the held Argmin; (4) parse-
#  marginal staging + Family A's own held predict_smooth_marginal_sc_term on a hand case;
#  (5) the no-Python-decisions audit re-asserted over the grown module.
# --------------------------------------------------------------------------- #
def test_sctps_verdict_term_weighted_unit_weights_numerically_identical():
    """`sctps_verdict_term_weighted(sc_w=1, tps_w=1, smooth_w=0)` must EVALUATE to the exact
    same number as the unweighted `sctps_verdict_term(include_smooth=False)` (the Times(Lit(1),
    x) wrapper is the numeric identity), and `smooth_w=0.0` must OMIT the SmoothDeformDist
    sub-term entirely (never a zero-weighted evaluated distance)."""
    native = srs.Substrate()._inner
    a, b = _circle_points(n=16), _circle_points(n=16, r=1.3, cx=0.2)
    v_unweighted = float(native.evaluate(ar.sctps_verdict_term(a, b, include_smooth=False), {}))
    t_unit = ar.sctps_verdict_term_weighted(a, b, sc_w=1.0, tps_w=1.0, smooth_w=0.0)
    v_unit = float(native.evaluate(t_unit, {}))
    assert abs(v_unweighted - v_unit) < 1e-12
    types = [it["items"][1]["type"] for it in t_unit["items"]]
    assert types == ["ShapeContextDist", "TpsDeformDist"], (
        "smooth_w=0.0 must omit the SmoothDeformDist sub-term entirely")
    t_smooth = ar.sctps_verdict_term_weighted(a, b, sc_w=1.0, tps_w=1.0, smooth_w=0.5)
    types_s = [it["items"][1]["type"] for it in t_smooth["items"]]
    assert types_s == ["ShapeContextDist", "TpsDeformDist", "SmoothDeformDist"]


def test_sctps_rerank_weighted_weights_steer_the_held_verdict():
    """Weights are genuinely consumed as DATA: at unit weights the weighted rerank must agree
    with the unweighted `sctps_rerank` on the same candidates (winner AND scores), and an
    extreme weight setting must be able to CHANGE the fused scores (proof the Lit weights
    reach the held Term, not a dead parameter)."""
    native = srs.Substrate()._inner
    rng = np.random.default_rng(3)
    query = _circle_points(n=32)
    exact = [list(p) for p in query]
    noise = rng.normal(size=(32, 2)).tolist()
    r_unw = ar.sctps_rerank(native, query, [exact, noise], [0, 1])
    r_unit = ar.sctps_rerank_weighted(native, query, [exact, noise], [0, 1],
                                       sc_w=1.0, tps_w=1.0, smooth_w=0.0)
    assert r_unit["winner"] == r_unw["winner"] == 0
    for (s_a, i_a), (s_b, i_b) in zip(r_unw["scores"], r_unit["scores"]):
        assert i_a == i_b and abs(s_a - s_b) < 1e-12
    r_scaled = ar.sctps_rerank_weighted(native, query, [exact, noise], [0, 1],
                                         sc_w=5.0, tps_w=0.25, smooth_w=0.0)
    assert any(abs(sa - sb) > 1e-9 for (sa, _), (sb, _) in
               zip(r_unit["scores"], r_scaled["scores"])), (
        "non-unit weights must change the fused scores -- the Lit weights must reach the Term")
    assert r_scaled["winner"] == 0                     # exact copy still wins under any
                                                        # positive re-weighting of distances


def test_single_sctps_rerank_picks_true_match_held_argmin():
    """The ScTpsDist-alone ensemble member (LEVER 3's second arm): exact-copy candidate wins
    the held Argmin; input order must not change the winning INDEX (the same order-independence
    check `test_sctps_rerank_picks_the_true_matching_point_set_held_argmin` runs for the fused
    verdict)."""
    native = srs.Substrate()._inner
    rng = np.random.default_rng(5)
    query = _circle_points(n=32)
    exact = [list(p) for p in query]
    noise = rng.normal(size=(32, 2)).tolist()
    res = ar.single_sctps_rerank(native, query, [exact, noise], [0, 1])
    assert res["winner"] == 0 and res["n_compared"] == 2
    res_rev = ar.single_sctps_rerank(native, query, [exact, noise], [1, 0])
    assert res_rev["winner"] == 0


def test_parse_marginal_verdict_hand_case_true_candidate_wins():
    """LEVER 4 on a hand case: two synthetic 'characters' (an L-shape drawn as ONE pen-stroke,
    and a circle), each staged as a candidate via a temp motor file; the query is the SAME
    L-shape drawn as TWO pen-strokes (a different 'writer segmentation'). Family A's held
    `predict_smooth_marginal_sc_term` (reused verbatim by `ar.parse_marginal_verdict`) must
    marginalise over the canonical-parse hypotheses and pick the L candidate -- the exact
    writer-invariance the parse marginalization exists to buy. Staging is `ar.stage_parse_
    char`'s own mechanical graph construction on a throwaway substrate."""
    import tempfile

    def _write_motor(path, strokes):
        with open(path, "w") as fh:
            fh.write("START\n")
            for st in strokes:
                for (x, y) in st:
                    fh.write(f"{x},{y},0\n")
                fh.write("BREAK\n")

    ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(ang), 40 + 20 * np.sin(ang)], 1).tolist()]
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]         # vertical bar
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]        # horizontal bar
    l_one_stroke = [down + across]                               # ONE pen-stroke L
    l_two_strokes = [down, across]                               # TWO pen-strokes, same shape

    with tempfile.TemporaryDirectory() as td:
        p_l = f"{td}/cand_l.txt"
        p_c = f"{td}/cand_circle.txt"
        p_q = f"{td}/query_l2.txt"
        _write_motor(p_l, l_one_stroke)
        _write_motor(p_c, circle)
        _write_motor(p_q, l_two_strokes)

        scratch = srs.Substrate()
        n_l = ar.stage_parse_char(scratch, p_l, is_query=False, name="L")
        n_c = ar.stage_parse_char(scratch, p_c, is_query=False, name="circle")
        qn = ar.stage_parse_char(scratch, p_q, is_query=True)
        winner = ar.parse_marginal_verdict(scratch, qn)
        assert winner is not None
        assert scratch.node(winner)["attrs"].get("name") == "L", (
            f"the same-shape (differently-segmented) candidate must win: "
            f"{scratch.node(winner)['attrs']!r}")
        assert winner == n_l and winner != n_c


# --------------------------------------------------------------------------- #
#  RUN 18 -- PARSE MARGINALIZATION AT FULL DWELL: RUN 17's own pilot already proved the
#  parse-marginal STAGING cheap (1.1s/20 episodes) and its END-TO-END winner-pick correct (the
#  hand case above); what neither RUN 17 nor its own tests checked is the marginal Term's own
#  ARITHMETIC -- that `recognition_graph.marginal_part_error_term`'s nested Sum/Exp/Log/Div
#  composition actually COMPUTES the log-sum-exp marginal it claims to (not, say, a mislabeled
#  hard-min or a Python-side reduction masquerading as a held Term), and that it behaves like a
#  genuine temperature-controlled marginalisation (beta->large recovers the hard min; a small
#  beta genuinely differs from it, not silently collapsing to it). Both tests below measure
#  their own oracle via the SAME `PointSetDist` primitive the Term calls internally (never
#  re-deriving point-set geometry in Python) -- only the AGGREGATION formula is independently
#  checked. A third test extends the hand case's true-match-wins property from 2 candidates to
#  a FULL-DWELL 5-candidate pool (RUN 18's own arm scores every candidate, never a shortlist).
# --------------------------------------------------------------------------- #
def _stage_two_parse_marginal(qh_pts_list, ch_pts_list):
    """Mechanical scratch-substrate staging for the oracle tests below: a query node `s` with
    one ParseHyp (one Stroke, `PTS_ATTR`) per entry of `qh_pts_list`, a candidate node `w` with
    one ParseHyp per entry of `ch_pts_list` -- the SAME `has_parse -> ParseHyp -> has_stroke ->
    Stroke{stroke_pts}` shape `ar.stage_parse_char` builds from real files, built by hand here
    from known point sets so the closed-form oracle can be computed independently. Returns
    `(native, s, w)`."""
    from domains import recognition_graph as rg
    scratch = srs.Substrate()
    s = scratch.add_node("Mark", {})
    w = scratch.add_node("Concept", {"is_word": 1.0})
    for qp in qh_pts_list:
        qh = scratch.add_node("ParseHyp", {})
        scratch.add_edge_unchecked(s, rg.PARSE_EDGE, qh)
        st = scratch.add_node("Stroke", {rg.PTS_ATTR: qp})
        scratch.add_edge_unchecked(qh, rg.STROKE_EDGE, st)
    for cp in ch_pts_list:
        ch = scratch.add_node("ParseHyp", {})
        scratch.add_edge_unchecked(w, rg.PARSE_EDGE, ch)
        st = scratch.add_node("Stroke", {rg.PTS_ATTR: cp})
        scratch.add_edge_unchecked(ch, rg.STROKE_EDGE, st)
    return scratch._inner, s, w


def test_marginal_part_error_term_matches_closed_form_log_sum_exp():
    """The marginal Term's own arithmetic, checked by hand: `marginal_part_error_term(beta)`
    must equal `-1/beta * log( sum_{qh,ch} exp(-beta * parse_pair_dist(qh, ch)) )` where
    `parse_pair_dist(qh, ch) = PointSetDist(qh, ch) + PointSetDist(ch, qh)` (one Stroke per
    ParseHyp collapses `_directed_part_dist`'s own mean-of-mins to a single PointSetDist each
    way) -- measured via the SAME primitive the held Term calls, combined by an independent
    Python oracle, and compared to one `evaluate()` of the held Term over a hand-staged scratch
    substrate. This is the composition (Plus/Exp/Log/Sum/Div held Terms) RUN 17's own tests
    never isolated -- only its end-to-end winner-pick."""
    from domains import recognition_graph as rg
    native = srs.Substrate()._inner
    rng = np.random.default_rng(11)
    qh_pts = [rng.normal(size=(10, 2)).tolist() for _ in range(2)]
    ch_pts = [rng.normal(size=(10, 2)).tolist() for _ in range(2)]

    def _pointset_dist(a, b):
        return float(native.evaluate(
            {"type": "PointSetDist", "a": {"type": "Lit", "value": a},
             "b": {"type": "Lit", "value": b}}, {}) or 0.0)

    beta = 2.0
    total = 0.0
    for qp in qh_pts:
        for cp in ch_pts:
            pair = _pointset_dist(qp, cp) + _pointset_dist(cp, qp)
            total += float(np.exp(-beta * pair))
    expected = -1.0 / beta * float(np.log(total))

    s_native, s, w = _stage_two_parse_marginal(qh_pts, ch_pts)
    got = float(s_native.evaluate(rg.marginal_part_error_term(beta=beta), {"s": s, "w": w}))
    assert abs(got - expected) < 1e-5, (got, expected)


def test_marginal_part_error_term_beta_is_a_genuine_temperature():
    """beta is the marginalisation TEMPERATURE (design: 'beta->inf is the min (commit to the
    best parse); a finite beta AVERAGES over plausible parses'). Built here: one (qh, ch)
    pairing is an EXACT match (PointSetDist 0, so the hard min over the 4 pairings is 0
    exactly) and the other three pairings are well-separated (large, distinguishable
    distances). At a LARGE beta the held Term must converge to that hard min (commit to the
    best parse); at a SMALL beta it must land CLEARLY AWAY from the hard min (the unnormalised
    log-sum-exp's own `-log(n_pairs)/beta` term dominates as beta shrinks) -- proof the
    composition genuinely depends on ALL parse pairings, not just the best one in disguise."""
    from domains import recognition_graph as rg
    native = srs.Substrate()._inner
    p = _circle_points(n=16)
    far1 = [[x + 3.0, y] for x, y in p]
    far2 = [[x - 3.0, y + 3.0] for x, y in p]
    qh_pts, ch_pts = [p, far1], [p, far2]     # (p, p) pairing is an exact match -> hard min 0

    def _pointset_dist(a, b):
        return float(native.evaluate(
            {"type": "PointSetDist", "a": {"type": "Lit", "value": a},
             "b": {"type": "Lit", "value": b}}, {}) or 0.0)

    pair_dists = [_pointset_dist(qp, cp) + _pointset_dist(cp, qp)
                  for qp in qh_pts for cp in ch_pts]
    hard_min = min(pair_dists)
    assert hard_min < 1e-9
    assert max(pair_dists) > 1.0, "the far pairings must be genuinely separated from the match"

    def _eval(beta):
        s_native, s, w = _stage_two_parse_marginal(qh_pts, ch_pts)
        return float(s_native.evaluate(rg.marginal_part_error_term(beta=beta), {"s": s, "w": w}))

    val_large_beta = _eval(200.0)
    val_small_beta = _eval(0.05)
    assert abs(val_large_beta - hard_min) < 1e-2, (
        f"large beta must converge to the hard min: {val_large_beta} vs {hard_min}")
    assert val_small_beta < hard_min - 1.0, (
        f"small beta must land clearly away from the hard min (genuine marginalisation over "
        f"ALL pairings, not a min in disguise): {val_small_beta} vs hard_min {hard_min}")


def test_predict_smooth_marginal_sc_term_full_dwell_five_candidates():
    """RUN 18's own arm scores EVERY candidate (full dwell, never a shortlist) -- extend the
    existing 2-candidate hand case to a 5-candidate pool: the true match (an L-shape drawn as
    ONE pen-stroke) among four distractors (the SAME writer-segmented L query as the existing
    hand case, plus a circle, a square-ish loop, and two more L-shape distractors drawn at a
    different SCALE/POSITION so only the true match's own SHAPE, not incidental proximity,
    should win) must still win `ar.parse_marginal_verdict`'s held Argmax over the full pool."""
    import tempfile

    def _write_motor(path, strokes):
        with open(path, "w") as fh:
            fh.write("START\n")
            for st in strokes:
                for (x, y) in st:
                    fh.write(f"{x},{y},0\n")
                fh.write("BREAK\n")

    ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(ang), 40 + 20 * np.sin(ang)], 1).tolist()]
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    l_one_stroke = [down + across]
    l_two_strokes = [down, across]                                  # the query's own segmentation
    square_loop = [[[10.0 + 4.0 * i, 10.0] for i in range(11)]
                   + [[50.0, 10.0 + 4.0 * i] for i in range(11)]
                   + [[50.0 - 4.0 * i, 50.0] for i in range(11)]
                   + [[10.0, 50.0 - 4.0 * i] for i in range(11)]]
    down_far = [[100.0, 100.0 + 3.0 * i] for i in range(21)]         # an L at a different scale/
    across_far = [[100.0 + 3.0 * i, 160.0] for i in range(16)]       # position -- distinct pose
    l_far_one_stroke = [down_far + across_far]
    down_tiny = [[5.0, 5.0 + 0.5 * i] for i in range(21)]             # an L at a much smaller scale
    across_tiny = [[5.0 + 0.5 * i, 15.0] for i in range(16)]
    l_tiny_one_stroke = [down_tiny + across_tiny]

    with tempfile.TemporaryDirectory() as td:
        paths = {
            "L": (f"{td}/cand_l.txt", l_one_stroke),
            "circle": (f"{td}/cand_circle.txt", circle),
            "square": (f"{td}/cand_square.txt", square_loop),
            "L_far": (f"{td}/cand_l_far.txt", l_far_one_stroke),
            "L_tiny": (f"{td}/cand_l_tiny.txt", l_tiny_one_stroke),
        }
        for path, strokes in paths.values():
            _write_motor(path, strokes)
        p_q = f"{td}/query_l2.txt"
        _write_motor(p_q, l_two_strokes)

        scratch = srs.Substrate()
        cand_nodes = {name: ar.stage_parse_char(scratch, path, is_query=False, name=name)
                      for name, (path, _strokes) in paths.items()}
        qn = ar.stage_parse_char(scratch, p_q, is_query=True)
        winner = ar.parse_marginal_verdict(scratch, qn)
        assert winner is not None
        assert winner == cand_nodes["L"], (
            f"the true match must win over a 5-candidate FULL-DWELL pool: winner attrs="
            f"{scratch.node(winner)['attrs']!r}")


def test_abs_read_no_python_decisions_run18_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after RUN 18's own
    addition (`DEFAULT_PARSE_PART_W`/`DEFAULT_PARSE_SC_W`/`DEFAULT_PARSE_BETA` -- named
    constants only, no new control flow) -- no Python argmin/argmax/sort-by-score anywhere in
    the grown module."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    assert ar.DEFAULT_PARSE_PART_W == 0.25
    assert ar.DEFAULT_PARSE_SC_W == 1.6
    assert ar.DEFAULT_PARSE_BETA == 2.0


def test_abs_read_no_python_decisions_run17_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the RUN 17
    additions (`sctps_verdict_term_weighted`/`sctps_rerank_weighted`/`single_sctps_rerank`/
    `stage_parse_char`/`parse_marginal_verdict`) -- no Python argmin/argmax/sort-by-score
    anywhere in the grown module; every verdict is a held Term (`_argmin_pairs_term`, or
    Family A's own `predict_smooth_marginal_sc_term` internal Argmax)."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


# ===========================================================================
# RUN 19 -- EARNED PARSE JOINS THE MARGINALIZATION + TOKEN-REFIT (scratchpad/HANDWRITING_
# DESIGN.md's section of the same name): LEVER 1a (`_earned_parts_from_stroke_points`/
# `stage_parse_char`'s new `earned_stroke_points` param) stages the codebook's own lattice-
# decoded per-stroke spans as ONE MORE ParseHyp alongside the theta grid; LEVER 2
# (`program_refit_verdict`/`program_refit_rerank`) is a directional program-explains-
# observation faculty, knowing nothing of characters. Hermetic, synthetic geometry only.
# ===========================================================================
def _write_motor_file(path, strokes):
    with open(path, "w") as fh:
        fh.write("START\n")
        for st in strokes:
            for (x, y) in st:
                fh.write(f"{x},{y},0\n")
            fh.write("BREAK\n")


def test_earned_parts_from_stroke_points_shape_and_normalization():
    """`_earned_parts_from_stroke_points` mirrors `canonical_parse.canonical_parts`'s OWN
    joint-normalize (one shared centroid + RMS over every sub-point) + per-part arc-length
    resample: one output part per input `stroke_points` item, each resampled to `per_part`
    points, all sharing the SAME normalization (computed jointly, not per-part) -- verified
    here against an independent by-hand oracle."""
    down = [[0.0, 2.0 * i] for i in range(10)]
    across = [[2.0 * i, 18.0] for i in range(8)]
    stroke_points = [(down, "d"), (across, "a")]
    per_part = 12

    parts = ar._earned_parts_from_stroke_points(stroke_points, per_part)
    assert len(parts) == 2
    for p in parts:
        assert p.shape == (per_part, 2)

    allp = np.concatenate([np.asarray(down, dtype=float), np.asarray(across, dtype=float)], 0)
    c = allp.mean(axis=0, keepdims=True)
    rms = float(np.sqrt(((allp - c) ** 2).sum(axis=1).mean())) or 1.0
    from domains.glyph_motor_world import _resample_arclen
    expected_down = _resample_arclen((np.asarray(down, dtype=float) - c) / rms, per_part)
    np.testing.assert_allclose(parts[0], expected_down, atol=1e-9)


def test_earned_parts_from_stroke_points_empty_is_empty():
    """Degenerate input (no stroke points at all) returns `[]`, never a fabricated part."""
    assert ar._earned_parts_from_stroke_points([], 12) == []


def test_stage_parse_char_earned_default_none_byte_identical():
    """Additivity discipline: omitting `earned_stroke_points` (the default, `None`) must stage
    EXACTLY the theta-grid ParseHyp count -- no extra 'earned'-kind hypothesis -- byte-identical
    to `stage_parse_char`'s pre-RUN-19 behaviour."""
    import tempfile
    from domains import recognition_graph as rg
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/cand.txt"
        _write_motor_file(p, [down + across])
        scratch = srs.Substrate()
        node = ar.stage_parse_char(scratch, p, is_query=False, name="L")
        hyps = list(scratch.neighbours(node, rg.PARSE_EDGE))
        assert len(hyps) == len(ar.DEFAULT_PARSE_THETAS)
        kinds = {scratch.node(h)["attrs"].get("kind") for h in hyps}
        assert "earned" not in kinds


def test_stage_parse_char_earned_adds_one_more_parsehyp_additively():
    """`earned_stroke_points` (LEVER 1a) is PURELY ADDITIVE: passing it stages exactly ONE MORE
    ParseHyp (tagged `kind='earned'`, `theta=DEFAULT_PARSE_EARNED_THETA`) alongside the
    UNCHANGED theta-grid hypotheses -- never replacing them."""
    import tempfile
    from domains import recognition_graph as rg
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/cand.txt"
        _write_motor_file(p, [down + across])
        scratch = srs.Substrate()
        node = ar.stage_parse_char(scratch, p, is_query=False, name="L",
                                    earned_stroke_points=[(down, "d"), (across, "a")])
        hyps = list(scratch.neighbours(node, rg.PARSE_EDGE))
        assert len(hyps) == len(ar.DEFAULT_PARSE_THETAS) + 1
        earned = [h for h in hyps if scratch.node(h)["attrs"].get("kind") == "earned"]
        assert len(earned) == 1
        assert scratch.node(earned[0])["attrs"].get("theta") == ar.DEFAULT_PARSE_EARNED_THETA
        strokes = list(scratch.neighbours(earned[0], rg.STROKE_EDGE))
        assert len(strokes) == 2, "one Stroke per earned_stroke_points item"


def test_stage_parse_char_earned_empty_stroke_points_adds_nothing():
    """An empty `earned_stroke_points` list is an honest no-op (no fabricated ParseHyp) --
    same byte-identical theta-grid-only staging as the default `None` path."""
    import tempfile
    from domains import recognition_graph as rg
    circle_ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(circle_ang), 40 + 20 * np.sin(circle_ang)], 1).tolist()]
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/cand.txt"
        _write_motor_file(p, circle)
        scratch = srs.Substrate()
        node = ar.stage_parse_char(scratch, p, is_query=False, name="circle",
                                    earned_stroke_points=[])
        hyps = list(scratch.neighbours(node, rg.PARSE_EDGE))
        assert len(hyps) == len(ar.DEFAULT_PARSE_THETAS)


def test_parse_marginal_verdict_earned_parse_alone_drives_the_verdict():
    """THE functional gate (LEVER 1a): with the theta GRID disabled entirely (`thetas=()`) and
    ONLY the earned segmentation staged, `parse_marginal_verdict` must still pick the true,
    differently-writer-segmented candidate -- proof the earned ParseHyp genuinely PARTICIPATES
    in (drives, not merely decorates) the marginal verdict, the SAME writer-invariance property
    `test_parse_marginal_verdict_hand_case_true_candidate_wins` established for the theta grid,
    now reproduced from the codebook's OWN learned segmentation alone."""
    import tempfile
    ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(ang), 40 + 20 * np.sin(ang)], 1).tolist()]
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    l_one_stroke = [down + across]
    l_two_strokes = [down, across]

    with tempfile.TemporaryDirectory() as td:
        p_l = f"{td}/cand_l.txt"
        p_c = f"{td}/cand_circle.txt"
        p_q = f"{td}/query_l2.txt"
        _write_motor_file(p_l, l_one_stroke)
        _write_motor_file(p_c, circle)
        _write_motor_file(p_q, l_two_strokes)

        scratch = srs.Substrate()
        # The candidate's own "earned" segmentation: its natural pen-stroke breakdown --
        # (down, across) for the L, (circle,) for the circle -- exactly what `ink_decode.
        # decode_ink`'s lattice would resolve for a codebook that already knows these shapes.
        n_l = ar.stage_parse_char(scratch, p_l, is_query=False, name="L", thetas=(),
                                   earned_stroke_points=[(down, "d"), (across, "a")])
        n_c = ar.stage_parse_char(scratch, p_c, is_query=False, name="circle", thetas=(),
                                   earned_stroke_points=[(circle[0], "c")])
        qn = ar.stage_parse_char(scratch, p_q, is_query=True, thetas=(),
                                  earned_stroke_points=[(down, "d"), (across, "a")])
        winner = ar.parse_marginal_verdict(scratch, qn)
        assert winner is not None
        assert winner == n_l and winner != n_c, (
            f"the earned parse alone (no theta grid) must still resolve the true, "
            f"differently-segmented candidate: {scratch.node(winner)['attrs']!r}")


# ---------------------------------------------------------------------------
# RUN 19 -- LEVER 2, TOKEN-REFIT AbS: `program_refit_verdict`/`program_refit_rerank`. The
# DIRECTIONAL asymmetry vs RUN 17/18's SYMMETRIC `recognition_graph.partnested_error_term`/
# `marginal_part_error_term` (this module's own top-of-file "RUN 19" docstring documents the
# rationale) -- a program that is a genuine SUBSET of a noisier observation pays nothing for
# the observation's extra, unmatched ink under the directional metric, where the SYMMETRIC
# family is charged for it via its own query-side term.
# ---------------------------------------------------------------------------
def test_tps_deform_dist_is_genuinely_directional():
    """Sanity precondition for the whole LEVER 2 rationale: the underlying Rust primitive
    itself is asymmetric (`TpsDeformDist(a, b) != TpsDeformDist(b, a)` in general, since it
    warps `a` TOWARD `b`'s own nearest points) -- verified directly, independent of this
    module's own composition."""
    native = srs.Substrate()._inner
    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    ang = np.linspace(0.0, np.pi, 20)
    arc = np.stack([np.cos(ang), np.sin(ang)], 1).tolist()

    def _tps(a, b):
        return float(native.evaluate(
            {"type": "TpsDeformDist", "a": {"type": "Lit", "value": a},
             "b": {"type": "Lit", "value": b}}, {}) or 0.0)

    d_ab = _tps(line, arc)
    d_ba = _tps(arc, line)
    assert abs(d_ab - d_ba) > 1e-6, f"TpsDeformDist must be directional: {d_ab} vs {d_ba}"


def test_program_refit_verdict_degenerate_inputs_return_none():
    """Empty `program_parts` or empty `observed_path_parts` is an honest `None` (never a
    fabricated score -- the inner soft-min over zero candidates is undefined)."""
    native = srs.Substrate()._inner
    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    assert ar.program_refit_verdict(native, [], [line]) is None
    assert ar.program_refit_verdict(native, [line], []) is None


def test_program_refit_verdict_subset_of_noisier_query_directional_vs_symmetric():
    """THE design's own synthetic case (scratchpad/HANDWRITING_DESIGN.md's RUN 19 section):
    'a program that is a SUBSET of a noisier query -- extra ink hurts symmetric distance but
    the program still explains its part well.' A single-part program (a line) that matches
    ONE part of the observation closely is scored TWICE: once against the observation ALONE,
    once against the SAME observation plus an unrelated extra part ('junk', a totally
    different shape). The DIRECTIONAL `program_refit_verdict` (marginalises only over the
    PROGRAM's own part) must be near-insensitive to the extra ink; the pre-existing SYMMETRIC
    family (`recognition_graph.partnested_error_term`, RUN 17/18's own comparator, which sums
    BOTH directions) must be hurt proportionally MORE by it -- the query-side term now has an
    unmatched part to explain."""
    from domains import recognition_graph as rg
    native = srs.Substrate()._inner
    rng = np.random.default_rng(7)

    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    line_noisy = (np.asarray(line) + rng.normal(scale=0.01, size=(20, 2))).tolist()
    junk = _circle_points(n=20, r=0.3, cx=5.0, cy=5.0)

    program = [line]
    observed_alone = [line_noisy]
    observed_with_junk = [line_noisy, junk]

    dir_alone = ar.program_refit_verdict(native, program, observed_alone)
    dir_junk = ar.program_refit_verdict(native, program, observed_with_junk)
    assert dir_alone is not None and dir_junk is not None
    rel_change_directional = abs(dir_junk - dir_alone) / max(1e-9, dir_alone)

    def _symmetric(program_parts, observed_parts):
        s = srs.Substrate()
        s_node = s.add_node("Mark", {})
        for p in observed_parts:
            st = s.add_node("Stroke", {rg.PTS_ATTR: p})
            s.add_edge_unchecked(s_node, rg.STROKE_EDGE, st)
        w_node = s.add_node("Concept", {"is_word": 1.0})
        for p in program_parts:
            st = s.add_node("Stroke", {rg.PTS_ATTR: p})
            s.add_edge_unchecked(w_node, rg.STROKE_EDGE, st)
        return float(s._inner.evaluate(rg.partnested_error_term(), {"s": s_node, "w": w_node}))

    sym_alone = _symmetric(program, observed_alone)
    sym_junk = _symmetric(program, observed_with_junk)
    rel_change_symmetric = abs(sym_junk - sym_alone) / max(1e-9, sym_alone)

    assert rel_change_directional < 0.1, (
        f"the directional program-refit score should barely move when unrelated extra ink is "
        f"added to the observation: {dir_alone} -> {dir_junk} "
        f"({100*rel_change_directional:.1f}% relative change)")
    assert rel_change_symmetric > rel_change_directional, (
        f"the SYMMETRIC family must be hurt proportionally MORE by the same extra ink: "
        f"directional {100*rel_change_directional:.1f}% vs symmetric "
        f"{100*rel_change_symmetric:.1f}% relative change")


def test_program_refit_rerank_picks_the_true_explaining_program():
    """`program_refit_rerank`'s held Argmin over multiple candidates: a program that matches
    part of the (noisier) observation must beat a program built from a shape unrelated to
    EVERY part of the observation -- basic discriminative correctness of the multi-candidate
    verdict, order-independent (input order must not change the winning INDEX)."""
    native = srs.Substrate()._inner
    rng = np.random.default_rng(13)
    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    line_noisy = (np.asarray(line) + rng.normal(scale=0.01, size=(20, 2))).tolist()
    junk = _circle_points(n=20, r=0.3, cx=5.0, cy=5.0)
    unrelated = _circle_points(n=20, r=0.15, cx=-8.0, cy=-8.0)

    observed = [line_noisy, junk]
    candidate_true = [line]
    candidate_false = [unrelated]

    res = ar.program_refit_rerank(native, [candidate_true, candidate_false], observed, [0, 1])
    assert res["winner"] == 0 and res["n_compared"] == 2
    res_rev = ar.program_refit_rerank(native, [candidate_true, candidate_false], observed, [1, 0])
    assert res_rev["winner"] == 0


def test_program_refit_rerank_skips_missing_parts_and_falls_back():
    """A candidate with no usable parts (`None`/empty) is skipped, not a crash; the fallback
    winner for an all-degenerate shortlist is `shortlist[0]`, mirroring every other rerank
    verdict's own fallback discipline."""
    native = srs.Substrate()._inner
    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    res = ar.program_refit_rerank(native, [[line], []], [line], [0, 1])
    assert res["winner"] == 0 and res["n_compared"] == 1

    res_all_empty = ar.program_refit_rerank(native, [[], []], [line], [0, 1])
    assert res_all_empty["winner"] == 0 and res_all_empty["n_compared"] == 0


def test_abs_read_no_python_decisions_run19_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the RUN 19
    additions (`_earned_parts_from_stroke_points`/`stage_parse_char`'s `earned_stroke_points`/
    `program_refit_term`/`program_refit_verdict`/`program_refit_rerank`) -- no Python
    argmin/argmax/sort-by-score anywhere in the grown module; `program_refit_rerank`'s verdict
    is the SAME held `Argmin` (`_argmin_pairs_term`) idiom every other rerank already uses."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"
    assert ar.DEFAULT_REFIT_BETA == 2.0
    assert ar.DEFAULT_PARSE_EARNED_THETA == -1.0


# ---------------------------------------------------------------------------
# RUN 20 -- BIDIRECTIONAL COVERAGE-CONSTRAINED REFIT: `program_refit_bidir_verdict`/
# `program_refit_bidir_rerank` (results/omniglot_gate_run19_refit.log's own diagnosis of RUN
# 19's 25.5% "actively harmful" directional metric + commit e43fba60's "NEXT (run 20)"
# paragraph). THE decisive gate below proves the mechanism directly: RUN 19's own directional
# score is provably insensitive to ink a program leaves unexplained (its own mean is only over
# the PROGRAM's parts); the new bidirectional score is provably NOT.
# ---------------------------------------------------------------------------

def test_program_refit_bidir_verdict_degenerate_inputs_return_none():
    """The SAME honest-`None` discipline as `program_refit_verdict` (RUN 19), re-asserted for
    the bidirectional verdict: either empty side makes ONE of the two soft-min directions
    undefined."""
    native = srs.Substrate()._inner
    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    assert ar.program_refit_bidir_verdict(native, [], [line]) is None
    assert ar.program_refit_bidir_verdict(native, [line], []) is None


def test_program_refit_bidir_term_is_the_sum_of_both_swapped_directions():
    """Definitional consistency: `program_refit_bidir_verdict(p, o)` must equal `program_refit_
    verdict(p, o) + program_refit_verdict(o, p)` EXACTLY (the bidirectional Term IS the RUN 19
    directional Term evaluated twice with its two argument lists swapped, summed at unit
    weight -- no other arithmetic sneaks in)."""
    native = srs.Substrate()._inner
    rng = np.random.default_rng(3)
    line = _line((0.0, 0.0), (1.0, 0.0), n=16)
    arc = _circle_points(n=16, r=0.4, cx=0.3, cy=0.1)
    program = [line, (np.asarray(arc) + rng.normal(scale=0.01, size=(16, 2))).tolist()]
    observed = [arc, line]

    bidir = ar.program_refit_bidir_verdict(native, program, observed)
    fwd = ar.program_refit_verdict(native, program, observed)
    rev = ar.program_refit_verdict(native, observed, program)
    assert bidir is not None and fwd is not None and rev is not None
    assert abs(bidir - (fwd + rev)) < 1e-6, f"{bidir} != {fwd} + {rev}"


def test_bidirectional_refit_charges_for_unexplained_ink_where_directional_does_not():
    """THE decisive gate for the run19->run20 fix, built and NUMERICALLY VALIDATED (not merely
    asserted) from RUN 19's own per-episode diagnosis: "an unpenalised per-part soft-min ...
    rewards generic/matchable programs ... regardless of how much of the true candidate's own
    more distinctive structure goes unmatched." A single-part program (a line) that matches ONE
    observed part closely, tested with and without a second, ENTIRELY UNEXPLAINED observed part
    (a distant, unrelated shape -- this module's OWN `test_program_refit_verdict_subset_of_
    noisier_query_directional_vs_symmetric` fixture, reused verbatim): the DIRECTIONAL score
    (RUN 19's own metric, unchanged) must stay ~UNMOVED by the unexplained ink (its own mean is
    over the PROGRAM's parts only, oblivious to anything the program doesn't own) -- exactly the
    "actively harmful" insensitivity RUN 19 diagnosed. The BIDIRECTIONAL score (RUN 20's fix)
    must move SUBSTANTIALLY worse, because the new ink->program term now measures whether the
    unexplained part has ANY good match among the program's own parts -- it does not (a lone
    straight line cannot explain a distant, unrelated shape), so it is finally charged for.

    (Attempted-but-not-included: a full multi-candidate RERANK-level flip, an actively WRONG
    'attractor' program numerically outscoring the TRUE program directionally then losing
    bidirectionally, was explored with several hand-built shape pairs (near-duplicate arrangements,
    complexity-mismatched pairs, spatially-distant 'junk' parts) during this test's construction;
    none reproduced a clean flip, because `TpsDeformDist`'s own directional asymmetry (a
    soft-min's score can only IMPROVE or stay flat as more candidate options are added, and a
    complex/flexible source can cheaply warp toward almost any target) means a candidate that
    explains MORE of the observation never scores worse than one that explains less, for any
    hand-built shapes tried. The SCORE-SENSITIVITY property this test proves -- unidirectional
    is blind to unexplained ink, bidirectional is not -- is the mechanism the design names; the
    empirical Omniglot run is the test of whether it moves classification accuracy in practice.)"""
    native = srs.Substrate()._inner
    rng = np.random.default_rng(7)

    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    line_noisy = (np.asarray(line) + rng.normal(scale=0.01, size=(20, 2))).tolist()
    junk = _circle_points(n=20, r=0.3, cx=5.0, cy=5.0)   # far, unrelated -- nothing a line can
                                                          # cheaply explain

    program = [line]
    observed_alone = [line_noisy]
    observed_with_junk = [line_noisy, junk]

    dir_alone = ar.program_refit_verdict(native, program, observed_alone)
    dir_junk = ar.program_refit_verdict(native, program, observed_with_junk)
    bidir_alone = ar.program_refit_bidir_verdict(native, program, observed_alone)
    bidir_junk = ar.program_refit_bidir_verdict(native, program, observed_with_junk)
    assert None not in (dir_alone, dir_junk, bidir_alone, bidir_junk)

    rel_change_dir = abs(dir_junk - dir_alone) / max(1e-9, abs(dir_alone))
    rel_change_bidir = abs(bidir_junk - bidir_alone) / max(1e-9, abs(bidir_alone))
    assert rel_change_dir < 0.05, (
        f"RUN 19's own pathology must reproduce here first: the directional score should barely "
        f"move when unrelated, unexplained ink is added -- {dir_alone} -> {dir_junk} "
        f"({100*rel_change_dir:.2f}% relative change)")
    assert bidir_junk > bidir_alone, (
        f"THE FIX: bidirectional coverage must get WORSE (higher score) once the observation "
        f"contains ink the program cannot explain -- {bidir_alone} -> {bidir_junk}")
    assert rel_change_bidir > 20 * rel_change_dir, (
        f"the bidirectional relative change must be DRAMATICALLY larger than the directional "
        f"one -- directional {100*rel_change_dir:.3f}% vs bidirectional "
        f"{100*rel_change_bidir:.1f}%")


def test_program_refit_bidir_rerank_picks_the_true_explaining_program():
    """The SAME basic discriminative sanity `test_program_refit_rerank_picks_the_true_explaining_
    program` (RUN 19) established, re-asserted for the bidirectional verdict: a program that
    matches part of a (noisier) observation must still beat a program built from a shape
    unrelated to EVERY part of the observation."""
    native = srs.Substrate()._inner
    rng = np.random.default_rng(17)
    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    line_noisy = (np.asarray(line) + rng.normal(scale=0.01, size=(20, 2))).tolist()
    junk = _circle_points(n=20, r=0.3, cx=5.0, cy=5.0)
    unrelated = _circle_points(n=20, r=0.15, cx=-8.0, cy=-8.0)

    observed = [line_noisy, junk]
    candidate_true = [line, junk]     # the true program also explains the junk part
    candidate_false = [unrelated]

    res = ar.program_refit_bidir_rerank(native, [candidate_true, candidate_false], observed,
                                          [0, 1])
    assert res["winner"] == 0 and res["n_compared"] == 2
    res_rev = ar.program_refit_bidir_rerank(native, [candidate_true, candidate_false], observed,
                                              [1, 0])
    assert res_rev["winner"] == 0


def test_program_refit_bidir_rerank_skips_missing_parts_and_falls_back():
    """A candidate with no usable parts is skipped, not a crash; `shortlist[0]` is the fallback
    winner for an all-degenerate pass -- the SAME fallback discipline `program_refit_rerank`
    (RUN 19) and every other rerank verdict in this module already follow."""
    native = srs.Substrate()._inner
    line = _line((0.0, 0.0), (1.0, 0.0), n=20)
    res = ar.program_refit_bidir_rerank(native, [[line], []], [line], [0, 1])
    assert res["winner"] == 0 and res["n_compared"] == 1

    res_all_empty = ar.program_refit_bidir_rerank(native, [[], []], [line], [0, 1])
    assert res_all_empty["winner"] == 0 and res_all_empty["n_compared"] == 0


# ---------------------------------------------------------------------------
# RUN 20 -- ARM 3, THE FULL GENERATIVE STACK: `parse_marginal_pair_error`/`refit_bidir_plus_
# marginal_rerank` -- bidirectional token-refit joined INSIDE the parse-hypothesis
# marginalization as one additional summed Term, rather than a search-only reconciliation
# metric.
# ---------------------------------------------------------------------------
def test_parse_marginal_pair_error_matches_predict_smooth_marginal_ranking():
    """Consistency precondition for the joined arm: `parse_marginal_pair_error` (a per-PAIR
    evaluate of `predict_smooth_marginal_sc_term`'s own fused error, `s`/`w` bound directly)
    must rank candidates IDENTICALLY to `parse_marginal_verdict`'s own held Argmax over the same
    staged graph (`Argmax(-err) == Argmin(err)`) -- otherwise summing a second score onto it
    would not be summing onto the quantity the marginal verdict actually decides by."""
    ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(ang), 40 + 20 * np.sin(ang)], 1).tolist()]
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    l_one_stroke = [down + across]
    l_two_strokes = [down, across]

    with __import__("tempfile").TemporaryDirectory() as td:
        p_l, p_c, p_q = f"{td}/cand_l.txt", f"{td}/cand_circle.txt", f"{td}/query_l2.txt"
        _write_motor_file(p_l, l_one_stroke)
        _write_motor_file(p_c, circle)
        _write_motor_file(p_q, l_two_strokes)

        scratch = srs.Substrate()
        n_l = ar.stage_parse_char(scratch, p_l, is_query=False, name="L")
        n_c = ar.stage_parse_char(scratch, p_c, is_query=False, name="circle")
        qn = ar.stage_parse_char(scratch, p_q, is_query=True)
        winner = ar.parse_marginal_verdict(scratch, qn)
        assert winner == n_l

        err_l = ar.parse_marginal_pair_error(scratch, qn, n_l)
        err_c = ar.parse_marginal_pair_error(scratch, qn, n_c)
        assert err_l < err_c, (
            f"the per-pair error for the ACTUAL winner must be the lower one: "
            f"L={err_l} circle={err_c}")


def test_refit_bidir_plus_marginal_rerank_picks_true_candidate():
    """Wiring/basic-correctness gate for the joined FULL-STACK verdict: the SAME L-vs-circle
    fixture, `refit_bidir_plus_marginal_rerank` must pick the true L candidate combining the
    staged parse-marginal error with the raw-per-stroke bidirectional refit score, ONE combined
    Term per candidate, no Python score addition."""
    ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(ang), 40 + 20 * np.sin(ang)], 1).tolist()]
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    l_one_stroke = [down + across]
    l_two_strokes = [down, across]

    with __import__("tempfile").TemporaryDirectory() as td:
        p_l, p_c, p_q = f"{td}/cand_l.txt", f"{td}/cand_circle.txt", f"{td}/query_l2.txt"
        _write_motor_file(p_l, l_one_stroke)
        _write_motor_file(p_c, circle)
        _write_motor_file(p_q, l_two_strokes)

        scratch = srs.Substrate()
        n_l = ar.stage_parse_char(scratch, p_l, is_query=False, name="L")
        n_c = ar.stage_parse_char(scratch, p_c, is_query=False, name="circle")
        qn = ar.stage_parse_char(scratch, p_q, is_query=True)

        cand_nodes = {0: n_l, 1: n_c}
        program_parts_list = [[down, across], [circle[0]]]
        observed_path_parts = [down, across]
        res = ar.refit_bidir_plus_marginal_rerank(scratch, qn, cand_nodes, program_parts_list,
                                                    observed_path_parts, [0, 1])
        assert res["winner"] == 0 and res["n_compared"] == 2
        res_rev = ar.refit_bidir_plus_marginal_rerank(scratch, qn, cand_nodes,
                                                        program_parts_list, observed_path_parts,
                                                        [1, 0])
        assert res_rev["winner"] == 0


def test_refit_bidir_plus_marginal_rerank_skips_missing_and_falls_back():
    """A candidate missing its staged node OR its program parts is skipped, not a crash;
    `shortlist[0]` is the fallback winner -- the SAME discipline every other rerank in this
    module follows."""
    ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(ang), 40 + 20 * np.sin(ang)], 1).tolist()]
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    l_one_stroke = [down + across]
    l_two_strokes = [down, across]

    with __import__("tempfile").TemporaryDirectory() as td:
        p_l, p_c, p_q = f"{td}/cand_l.txt", f"{td}/cand_circle.txt", f"{td}/query_l2.txt"
        _write_motor_file(p_l, l_one_stroke)
        _write_motor_file(p_c, circle)
        _write_motor_file(p_q, l_two_strokes)

        scratch = srs.Substrate()
        n_l = ar.stage_parse_char(scratch, p_l, is_query=False, name="L")
        qn = ar.stage_parse_char(scratch, p_q, is_query=True)

        observed_path_parts = [down, across]
        res = ar.refit_bidir_plus_marginal_rerank(scratch, qn, {0: n_l},
                                                    [[down, across], []], observed_path_parts,
                                                    [0, 1])
        assert res["winner"] == 0 and res["n_compared"] == 1


def test_abs_read_no_python_decisions_run20_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the RUN 20
    additions (`program_refit_bidir_term`/`program_refit_bidir_verdict`/`program_refit_bidir_
    rerank`/`parse_marginal_pair_error_term`/`parse_marginal_pair_error`/`joined_refit_marginal_
    term`/`refit_bidir_plus_marginal_rerank`) -- no Python argmin/argmax/sort-by-score anywhere
    in the grown module; every new verdict is the SAME held `Argmin` (`_argmin_pairs_term`)
    idiom every pre-existing rerank in this module already uses."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"
    assert "program_refit_bidir_term" in src and "refit_bidir_plus_marginal_rerank" in src


# ===========================================================================
# RUN 25 -- THE NUMBER (scratchpad/HANDWRITING_DESIGN.md's "RUN 25" scope): C1 finer theta
# grid (pure data, no new function), C2 verdict fusion at different grains (`fused_grain_
# verdict_term`/`fused_grain_rerank`), C3 exemplar-nuisance marginalization (`stage_parse_
# char`'s new `nuisance_variant_parts` param). Hermetic, synthetic geometry only, the SAME
# L-vs-circle fixture (`_write_motor_file`) RUN 19/20's own gates already established.
# ===========================================================================
def test_default_parse_thetas_fine_widens_the_grid():
    """C1: the fine grid is strictly WIDER than RUN 17b's own (55, 70, 85) -- a pure
    hypothesis-count increase, no new function needed."""
    assert len(ar.DEFAULT_PARSE_THETAS_FINE) > len(ar.DEFAULT_PARSE_THETAS)
    assert min(ar.DEFAULT_PARSE_THETAS_FINE) < min(ar.DEFAULT_PARSE_THETAS)
    assert max(ar.DEFAULT_PARSE_THETAS_FINE) > max(ar.DEFAULT_PARSE_THETAS)


def test_stage_parse_char_fine_thetas_stages_more_parsehyps():
    """C1 functional: passing `thetas=ar.DEFAULT_PARSE_THETAS_FINE` stages exactly
    `len(DEFAULT_PARSE_THETAS_FINE)` ParseHyp nodes -- the SAME staging code path, a wider
    DATA tuple."""
    import tempfile
    from domains import recognition_graph as rg
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/cand.txt"
        _write_motor_file(p, [down + across])
        scratch = srs.Substrate()
        node = ar.stage_parse_char(scratch, p, is_query=False, name="L",
                                    thetas=ar.DEFAULT_PARSE_THETAS_FINE)
        hyps = list(scratch.neighbours(node, rg.PARSE_EDGE))
        assert len(hyps) == len(ar.DEFAULT_PARSE_THETAS_FINE)


def _l_circle_fixture(td):
    ang = np.linspace(0.0, 2 * np.pi, 40)
    circle = [np.stack([40 + 20 * np.cos(ang), 40 + 20 * np.sin(ang)], 1).tolist()]
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    l_one_stroke = [down + across]
    l_two_strokes = [down, across]
    p_l, p_c, p_q = f"{td}/cand_l.txt", f"{td}/cand_circle.txt", f"{td}/query_l2.txt"
    _write_motor_file(p_l, l_one_stroke)
    _write_motor_file(p_c, circle)
    _write_motor_file(p_q, l_two_strokes)
    return dict(p_l=p_l, p_c=p_c, p_q=p_q, down=down, across=across, circle=circle)


def test_fused_grain_verdict_term_byte_identical_at_unit_norm():
    """C2 additivity: `norm_a=norm_b=1.0` (the default) must build a bare unweighted `Plus` of
    the two RAW sub-terms -- no `Div` node at all -- so the norm-less path is byte-identical to
    a hand-built `Plus([parse_marginal_pair_error_term(), sctps_verdict_term(...)])`."""
    qps = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]
    cps = [[0.0, 0.0], [1.0, 0.1], [1.1, 1.0]]
    term = ar.fused_grain_verdict_term(qps, cps)
    expected = {"type": "Plus", "items": [
        ar.parse_marginal_pair_error_term(), ar.sctps_verdict_term(qps, cps)]}
    assert term == expected


def test_fused_grain_rerank_picks_true_candidate_raw():
    """C2 functional (raw/unnormalized): the SAME L-vs-circle fixture RUN 19/20's own gates use
    -- `fused_grain_rerank` must pick the true L candidate combining the staged part-marginal
    error with the whole-figure SC+TPS error over the query's/candidates' own point-sets."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fx = _l_circle_fixture(td)
        scratch = srs.Substrate()
        n_l = ar.stage_parse_char(scratch, fx["p_l"], is_query=False, name="L")
        n_c = ar.stage_parse_char(scratch, fx["p_c"], is_query=False, name="circle")
        qn = ar.stage_parse_char(scratch, fx["p_q"], is_query=True)

        q_ps = ar.whole_figure_point_set([(fx["down"], "d"), (fx["across"], "a")])
        l_ps = ar.whole_figure_point_set([(fx["down"] + fx["across"], "l")])
        c_ps = ar.whole_figure_point_set([(fx["circle"][0], "c")])
        cand_nodes = {0: n_l, 1: n_c}
        candidate_ps_list = [l_ps, c_ps]

        res = ar.fused_grain_rerank(scratch, qn, cand_nodes, q_ps, candidate_ps_list, [0, 1])
        assert res["winner"] == 0 and res["n_compared"] == 2
        assert res["norm_a"] == 1.0 and res["norm_b"] == 1.0


def test_fused_grain_rerank_normalized_variant_also_picks_true_candidate():
    """C2 functional (normalized): `normalize=True` divides each sub-term by its own
    per-episode candidate-mean -- a monotonic rescaling of two POSITIVE per-candidate lists
    cannot flip which candidate is lower on its own scale-normalized sum vs the true L/circle
    contrast this fixture is built around; the true candidate must still win, and the reported
    `norm_a`/`norm_b` must be the plain means of the raw per-candidate scores actually used."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fx = _l_circle_fixture(td)
        scratch = srs.Substrate()
        n_l = ar.stage_parse_char(scratch, fx["p_l"], is_query=False, name="L")
        n_c = ar.stage_parse_char(scratch, fx["p_c"], is_query=False, name="circle")
        qn = ar.stage_parse_char(scratch, fx["p_q"], is_query=True)

        q_ps = ar.whole_figure_point_set([(fx["down"], "d"), (fx["across"], "a")])
        l_ps = ar.whole_figure_point_set([(fx["down"] + fx["across"], "l")])
        c_ps = ar.whole_figure_point_set([(fx["circle"][0], "c")])
        cand_nodes = {0: n_l, 1: n_c}
        candidate_ps_list = [l_ps, c_ps]

        res = ar.fused_grain_rerank(scratch, qn, cand_nodes, q_ps, candidate_ps_list, [0, 1],
                                     normalize=True)
        assert res["winner"] == 0 and res["n_compared"] == 2
        raw_a = [ar.parse_marginal_pair_error(scratch, qn, n_l),
                 ar.parse_marginal_pair_error(scratch, qn, n_c)]
        native = scratch._inner
        raw_b = [float(native.evaluate(ar.sctps_verdict_term(q_ps, l_ps), {}) or 0.0),
                 float(native.evaluate(ar.sctps_verdict_term(q_ps, c_ps), {}) or 0.0)]
        assert res["norm_a"] == pytest.approx(sum(raw_a) / len(raw_a))
        assert res["norm_b"] == pytest.approx(sum(raw_b) / len(raw_b))


def test_fused_grain_rerank_skips_missing_and_falls_back():
    """A candidate missing its staged node OR its point-set is skipped, not a crash;
    `shortlist[0]` is the fallback winner -- the SAME discipline every other rerank in this
    module follows."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fx = _l_circle_fixture(td)
        scratch = srs.Substrate()
        n_l = ar.stage_parse_char(scratch, fx["p_l"], is_query=False, name="L")
        qn = ar.stage_parse_char(scratch, fx["p_q"], is_query=True)
        q_ps = ar.whole_figure_point_set([(fx["down"], "d"), (fx["across"], "a")])
        l_ps = ar.whole_figure_point_set([(fx["down"] + fx["across"], "l")])
        res = ar.fused_grain_rerank(scratch, qn, {0: n_l}, q_ps, [l_ps, None], [0, 1])
        assert res["winner"] == 0 and res["n_compared"] == 1


def test_stage_parse_char_nuisance_default_none_byte_identical():
    """C3 additivity: omitting `nuisance_variant_parts` (the default, `None`) stages EXACTLY
    the theta-grid ParseHyp count -- no extra 'nuisance'-kind hypothesis."""
    import tempfile
    from domains import recognition_graph as rg
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/cand.txt"
        _write_motor_file(p, [down + across])
        scratch = srs.Substrate()
        node = ar.stage_parse_char(scratch, p, is_query=False, name="L")
        hyps = list(scratch.neighbours(node, rg.PARSE_EDGE))
        assert len(hyps) == len(ar.DEFAULT_PARSE_THETAS)
        kinds = {scratch.node(h)["attrs"].get("kind") for h in hyps}
        assert "nuisance" not in kinds


def test_stage_parse_char_nuisance_adds_k_more_parsehyps_additively():
    """C3: passing K nuisance variant part-lists stages exactly K MORE ParseHyp nodes (tagged
    `kind='nuisance'`, `theta=DEFAULT_PARSE_NUISANCE_THETA`), alongside the UNCHANGED
    theta-grid hypotheses -- never replacing them; an empty variant in the list is skipped
    (honest non-crash, never a fabricated ParseHyp)."""
    import tempfile
    from domains import recognition_graph as rg
    down = [[20.0, 20.0 + 2.0 * i] for i in range(21)]
    across = [[20.0 + 2.0 * i, 60.0] for i in range(16)]
    variant1 = [np.asarray(down) + 0.5, np.asarray(across) + 0.5]
    variant2 = [np.asarray(down) - 0.5, np.asarray(across) - 0.5]
    with tempfile.TemporaryDirectory() as td:
        p = f"{td}/cand.txt"
        _write_motor_file(p, [down + across])
        scratch = srs.Substrate()
        node = ar.stage_parse_char(scratch, p, is_query=False, name="L",
                                    nuisance_variant_parts=[variant1, variant2, []])
        hyps = list(scratch.neighbours(node, rg.PARSE_EDGE))
        assert len(hyps) == len(ar.DEFAULT_PARSE_THETAS) + 2, (
            "exactly 2 nuisance ParseHyps (the empty 3rd variant is skipped), theta grid intact")
        nuisance = [h for h in hyps if scratch.node(h)["attrs"].get("kind") == "nuisance"]
        assert len(nuisance) == 2
        for h in nuisance:
            assert scratch.node(h)["attrs"].get("theta") == ar.DEFAULT_PARSE_NUISANCE_THETA
        strokes0 = list(scratch.neighbours(nuisance[0], rg.STROKE_EDGE))
        assert len(strokes0) == 2, "one Stroke per part in the variant"


def test_stage_parse_char_nuisance_variant_participates_in_marginal_verdict():
    """C3 functional: with the theta grid disabled entirely (`thetas=()`) and ONLY a nuisance
    variant of the true candidate's own strokes staged, `parse_marginal_verdict` must still
    pick the true candidate -- proof the nuisance ParseHyp genuinely participates in the
    marginal verdict (not merely decorates it), mirroring `test_parse_marginal_verdict_earned_
    parse_alone_drives_the_verdict`'s own precedent for the earned ParseHyp."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fx = _l_circle_fixture(td)
        scratch = srs.Substrate()
        # A nuisance variant of the L's OWN strokes, mildly perturbed -- what
        # glyph_motor_world.write_with_hand would produce, in miniature.
        l_variant = [np.asarray(fx["down"]) * 1.02 + 0.3, np.asarray(fx["across"]) * 1.02 + 0.3]
        c_variant = [np.asarray(fx["circle"][0]) * 1.02 + 0.3]
        n_l = ar.stage_parse_char(scratch, fx["p_l"], is_query=False, name="L", thetas=(),
                                   nuisance_variant_parts=[l_variant])
        n_c = ar.stage_parse_char(scratch, fx["p_c"], is_query=False, name="circle", thetas=(),
                                   nuisance_variant_parts=[c_variant])
        qn = ar.stage_parse_char(scratch, fx["p_q"], is_query=True, thetas=(),
                                  nuisance_variant_parts=[l_variant])
        winner = ar.parse_marginal_verdict(scratch, qn)
        assert winner == n_l


def test_abs_read_no_python_decisions_run25_additions():
    """The SAME audit as `test_abs_read_no_python_decisions`, re-asserted after the RUN 25
    additions (`fused_grain_verdict_term`/`fused_grain_rerank`/`stage_parse_char`'s new
    `nuisance_variant_parts` param/`DEFAULT_PARSE_THETAS_FINE`/`DEFAULT_PARSE_NUISANCE_THETA`)
    -- no Python argmin/argmax/sort-by-score anywhere in the grown module; the fused verdict's
    final pick is the SAME held `Argmin` (`_argmin_pairs_term`) idiom every other rerank in
    this module already uses; the mechanical per-episode scale-alignment mean
    (`sum(...)/len(...)`) is plain bookkeeping over an already-computed list, never itself a
    ranking decision."""
    src = Path(ar.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"
    assert "fused_grain_verdict_term" in src and "fused_grain_rerank" in src
    assert ar.DEFAULT_PARSE_NUISANCE_THETA == -2.0
    assert len(ar.DEFAULT_PARSE_THETAS_FINE) == 6
