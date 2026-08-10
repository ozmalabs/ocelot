"""RUNG 2 — dimension inference (design 'transform-as-quantum-delta',
scratchpad TRANSFORM_DESIGN.md, "RUNG 2 — NOW IN SCOPE" section, 2026-07-02):
"sometimes you need to infer a dimension before you transform — rotating a
flat 2D rectangle in the Z dimension gives you a transform in XY that can't
be replicated without Z." Extends `seeds/shape_decode_loop.json` (v1.3.0)
with `sd_infer_dimension` / `sd_recognize_dim` (new rules), a
`sd_dim_check_mark` resilience rule (see its own seed comment), an extended
`sd_mint_quantum` guard, and three `DimensionGenerator` codebook nodes
(rotation90, reflection_r, reflection_c — seed data), all backed by the new
Rust `DimInfer` Term (`runners/dsl/src/shape_decode.rs` family — landed
DURING this pass; see `runners/dsl/src/shape_decode.rs::dim_infer_tests` for
the authoritative Rust fixtures this suite's own fixtures are deliberately
built to mirror 1:1, exactly like `test_transform_decode_migrated.py`'s grid
test mirrored `TransformDecode`'s own cargo "grid-flavored" test).

FOLLOWS `tests/test_transform_decode_migrated.py`'s CONVENTIONS DIRECTLY (it
is this suite's immediate predecessor): the same `_boot`/`_add_part`/`_epoch`/
`_axes` helpers (reused verbatim below, extended with an optional
`dim_types` kwarg), the same hand-set `status="decoded"` + `residual`
convention for exercising the loop rules in isolation for gates 1-4/6, and a
real end-to-end `induce_concern` drive for gate 7 (organic pipeline) — plus
the SAME module-level "not yet landed" skip pattern for the Rust Term this
work depends on (`DimInfer`), in case this file is ever run against an
older wheel that predates it.

TROMINO FIXTURE, taken directly from `dim_infer_tests::tromino` (Rust): an
"L" of 3 red cells at `(0,0) (0,1) (1,0)` — asymmetric under 90-degree
rotation (all four `k=0..3` land on a distinct cell set), which is exactly
what makes "the correct generator/k is reported" a meaningful assertion
rather than a coincidence, and why a symmetric/checkerboard fixture (the
first thing tried while authoring this suite) does NOT work: rotating or
reflecting a shape onto ITSELF (same bbox, same coordinate set) is
indistinguishable, after rung 1's canonical sort, from a plain per-dimension
value substitution — a genuine coordinate-remapping gate needs a bbox whose
rotated/reflected image occupies a DIFFERENT coordinate set. Every numeric
fixture below (`ROTATED_K1_TROMINO`, `ROTATED_TRANSLATED_RECOLOURED_GOAL`,
`SCRAMBLED_GOAL`, `REFLECTED_R_GOAL`) is either copied verbatim from, or
independently re-derived and cross-checked live against, the landed
`DimInfer` Term (`native.evaluate({"type": "DimInfer", ...})`, see the
per-fixture comments) while authoring this pass — not guessed.

DIM-TYPING ASSUMPTION (reported for reconciliation): the design says
"ShapeSignature nodes (AND OBSERVATIONS) gain an OPTIONAL `dim_types`
attr". The landed `eval_dim_infer` (`runners/dsl/src/shape_decode.rs`) only
ever reads `dim_types` off the CODEBOOK (`ShapeSignature`) side (`load_parts`
returns `Part.dim_types`; `eval_dim_infer`'s own loop skips a part with none)
— it never reads an Observation-side `dim_types` attr at all. This suite
therefore sets `dim_types` on the `ShapeSignature` codebook node (load-
bearing) and, belt-and-suspenders, ALSO on the `Observation` node (harmless,
confirmed unread by the Term, kept only in case a future caller wants it)."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf


def _dim_infer_live() -> bool:
    """Cheap probe: is the Rust `DimInfer` Term callable yet? Mirrors
    `test_transform_decode_migrated.py::_term_decode_live` exactly."""
    s, ag = boot_core()
    native = s._inner
    try:
        native.evaluate(
            {"type": "DimInfer",
             "goal": {"type": "Lit", "value": [["cell", 0, 0, "x"]]}}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _dim_infer_live():
    pytest.skip(
        "DimInfer Term not yet landed (Part A of RUNG 2 pending in parallel "
        "— runners/dsl/src/shape_decode.rs::eval_dim_infer does not exist "
        "yet in the currently-installed substrate_rs wheel); "
        "seeds/shape_decode_loop.json's sd_infer_dimension/sd_recognize_dim "
        "rules are authored and install-clean (skipped with a loud warning "
        "at seed-load time, exactly like sd_transform_decode was before "
        "TransformDecode landed) but cannot fire without it. The guard-level "
        "logic that does NOT need the live Term (sd_mint_quantum's new "
        "dim_checked==1 requirement staying satisfiable via the Term-free "
        "sd_dim_check_mark resilience rule; a rung-1 win never touching "
        "dim_checked) was verified separately with a hand-set-attr sanity "
        "script — see the task's final report. Honest skip, not a faked "
        "pass.",
        allow_module_level=True)


DIM_TYPES = ["pred", "coord:r", "coord:c", "val"]


def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _add_part(s, name, signature, kind="faculty", dim_types=None):
    attrs = {"name": name, "signature": json.dumps(signature), "kind": kind}
    if kind == "faculty":
        attrs["faculty"] = name
    else:
        attrs["concept"] = name
    if dim_types is not None:
        attrs["dim_types"] = list(dim_types)
    return s.add_node("ShapeSignature", attrs)


def _observe_decoded(s, ag, *, signature, key, residual, decoded_epoch, dim_types=None):
    attrs = {"signature": signature, "key": [key], "status": "decoded",
              "residual": residual, "decoded_epoch": decoded_epoch}
    if dim_types is not None:
        attrs["dim_types"] = list(dim_types)
    obs = s.add_node("Observation", attrs)
    s.add_edge(ag, "observed", obs)
    return obs


def _epoch(s, ag):
    return s.node(ag)["attrs"].get("codebook_epoch") or 0.0


def _axes(s):
    return len(list(s.nodes("CapabilityAxis")))


# ---------------------------------------------------------------------------
# Fixtures — copied from / cross-checked live against
# `dim_infer_tests::tromino` and its sibling cargo tests (see module
# docstring). `dim_types` = ["pred", "coord:r", "coord:c", "val"] so slots
# 1/2 are typed as the coordinate pair rotation90/reflection_r/reflection_c
# act on (coord_dims [1,2] for all three seed-authored generators).
# ---------------------------------------------------------------------------
TROMINO = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 1, 0, "red"]]

# k=1 image of the tromino (hand-verified in `rotate90_once`'s own doc and
# reproduced live against `DimInfer` while authoring this suite): zero
# residual — the generator alone fully explains it.
ROTATED_K1_TROMINO = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 1, 1, "red"]]

# The same k=1 rotation, PLUS a uniform +5 row shift, PLUS a red->green
# substitution (col held fixed, unlike the Rust cargo test's 3-dim version,
# so this fits the seed's max_dims=2) — composes generator + residual
# per-dim deltas in one pass. Verified live: explained=True, generator
# "rotation90", k=1, dims=(1,3) (row shift + colour), transforms =
# [{dim:1,kind:"shift",delta:5}, {dim:3,kind:"subst",delta:(("red","green"),)}].
ROTATED_TRANSLATED_RECOLOURED_GOAL = [
    ["cell", 5, 0, "green"], ["cell", 5, 1, "green"], ["cell", 6, 1, "green"]]

# Scrambled: the held colour is uniformly "red", the goal's three colours
# are pairwise distinct at the SAME coordinates as the held tromino — no
# function maps "red" to 3 different values for ANY generator/k, and rung 1
# fails the same way (same coordinates, incoherent value mapping). Verified
# live: explained=False for DimInfer; also NOT explained by TransformDecode
# (rung 1) since it is the exact `scrambled_not_explained` cargo fixture.
SCRAMBLED_GOAL = [["cell", 0, 0, "blue"], ["cell", 0, 1, "green"], ["cell", 1, 0, "yellow"]]

# reflection_r (k=1) image of the tromino (hand-verified in
# `dim_infer_tests::reflection_explained` and reproduced live): zero
# residual.
REFLECTED_R_GOAL = [["cell", 1, 0, "red"], ["cell", 1, 1, "red"], ["cell", 0, 0, "red"]]

# scale2 (k=1) image of the tromino — the base-as-dimension fixture: the
# tromino {(0,0),(0,1),(1,0)} scaled x2 about its origin is
# {(0,0),(0,2),(2,0)} (mirrors `dim_infer_tests::
# scaled_shape_explained_via_scale2_generator`). Asymmetric under scaling
# (distinct cell set), so "generator scale2, k=1" is a real assertion.
SCALED_X2_TROMINO = [["cell", 0, 0, "red"], ["cell", 0, 2, "red"], ["cell", 2, 0, "red"]]

# --- Cyclic (modular / Z_n) fixtures (seed v1.5.0, generator `cycle4`,
# coord_dims [1] = the row slot, modulus 4) — mirror
# `dim_infer_tests::cycle_pair` and its siblings, cross-checked live
# against the seed-loaded `DimInfer` while authoring this pass (all five
# generators — rotation90/reflection_r/reflection_c/scale2/cycle4 — in the
# codebook; `cycle4` is the sole winner for the wrap fixtures below). Two
# cells at rows {0,3} (distinct cols so the relations differ); the row slot
# is the cyclic axis, and it WRAPS under mod 4 (row 3 -> 0), which is
# precisely what a plain rung-1 shift cannot reproduce.
CYCLE_PAIR = [["cell", 0, 0, "red"], ["cell", 3, 1, "red"]]

# cycle4 (k=1, mod 4) image of CYCLE_PAIR: row 0 -> 1 (no wrap), row 3 -> 0
# (WRAPS). {(1,0),(0,1)} — a DISTINCT cell set, zero residual. Verified
# live: explained=True, generator "cycle4", k=1, dims=(), transforms=().
CYCLE_K1 = [["cell", 1, 0, "red"], ["cell", 0, 1, "red"]]

# A NON-wrapping uniform +1 shift on the SAME cyclic row axis: rows {0,3}
# -> {1,4} (no value crosses the modulus). This is a plain per-dimension
# delta rung 1 (sd_transform_decode) explains outright, so rung 2 (and
# `cycle4`) never gets a look — the discrimination that proves the modular
# generator only fires when the wrap is genuinely needed. Verified live:
# reaches recognized_transformed with transform_explained set, generator
# None, dims=(1,), and dim_checked NEVER set.
NONWRAP_ROW_SHIFT = [["cell", 1, 0, "red"], ["cell", 4, 1, "red"]]

# --- COMPOSITION (length-<=2) fixtures (seed v1.6.0, design
# runners/dsl/COMPOSITION_DESIGN.md) — mirror
# `dim_infer_tests::composed_rotate_then_scale_is_length2` /
# `composed_reflect_then_scale_is_length2` (Rust), cross-checked live
# against the seed-loaded `DimInfer` while authoring this pass. Each is a
# tromino stepped by TWO distinct generators where NEITHER generator alone
# (plus a linear residual) reaches it: rotation/reflection preserve extent
# 1, scale2 alone spreads to a DIFFERENT cell set, so the composite is the
# minimal (and only) explanation.

# rotate90 (k=1) {(0,0),(0,1),(1,1)} THEN scale2 (x2, k=1) ->
# {(0,0),(0,2),(2,2)}. NOT reachable by any single generator, so DimInfer
# composes rotation90 THEN scale2. Verified live: explained=True, length=2,
# generators=("rotation90","scale2"), ks=(1,1), zero residual.
ROTATE_SCALE_GOAL = [["cell", 0, 0, "red"], ["cell", 0, 2, "red"], ["cell", 2, 2, "red"]]

# reflection_r (k=1) {(1,0),(1,1),(0,0)} THEN scale2 (x2, k=1) ->
# {(0,0),(2,0),(2,2)}. A DISTINCT image from ROTATE_SCALE_GOAL, so the
# inferred generator PAIR (reflection_r, not rotation90) is meaningful.
# Verified live: generators=("reflection_r","scale2"), ks=(1,1).
REFLECT_SCALE_GOAL = [["cell", 0, 0, "red"], ["cell", 2, 0, "red"], ["cell", 2, 2, "red"]]


# ---------------------------------------------------------------------------
# 1 — a rotated tromino (asymmetric bbox, zero leftover residual) is
#     recognised via the rotation90 DimensionGenerator: recognized_transformed,
#     ZERO CapabilityAxis minted, a LatentDimension node minted carrying k.
# ---------------------------------------------------------------------------
def test_rotated_grid_recognized_via_generator_zero_mint():
    s, ag, native = _boot()
    _add_part(s, "part_tromino", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)
    baseline_latent = len(list(s.nodes("LatentDimension")))

    obs = _observe_decoded(s, ag, signature=ROTATED_K1_TROMINO, key="probe_rotate",
                            residual=ROTATED_K1_TROMINO, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_checked") == 1
    assert at.get("dim_checked") == 1, (
        "dim_checked can only be set once rung 1 (sd_transform_decode) has "
        "ALREADY run and failed to explain this coordinate-remapping "
        "rotation as a per-dimension delta/substitution — the proof rung 1 "
        "did not resolve this alone")
    assert at.get("dim_explained"), "rotation90 must explain the rotated tromino"
    # NOTE: transform_explained is now ALSO 1 here — sd_recognize_dim
    # DELIBERATELY reuses this attr the moment rung 2 succeeds (see its own
    # seed comment); it does NOT mean rung 1 itself explained the residual
    # (dim_checked==1, asserted above, is the real proof rung 1 did not).
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_tromino"
    assert _axes(s) == baseline_axes, "recognition-under-a-generator must mint NO CapabilityAxis"

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("generator") == "rotation90"
    assert t_at.get("k") == 1
    assert t_at.get("dim") == "latent:rotation90"
    assert t_at.get("delta") == 1
    assert t_at.get("base") == "part_tromino"

    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1
    ld_node = next(iter(s.neighbours(obs, "has_latent_dimension")))
    ld_at = s.node(ld_node)["attrs"]
    assert ld_at.get("generator") == "rotation90"
    assert ld_at.get("k") == 1
    assert ld_at.get("name") == "latent:rotation90"


# ---------------------------------------------------------------------------
# 2 — rotation composed with a residual per-dimension delta (translate +
#     recolour): the generator explains the coordinate remapping, and the
#     LEFTOVER row-shift + value-substitution is captured as ordinary
#     residual dims/transforms on the SAME Transform node.
# ---------------------------------------------------------------------------
def test_rotated_translated_recoloured_composes():
    s, ag, native = _boot()
    _add_part(s, "part_tromino2", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)

    obs = _observe_decoded(
        s, ag, signature=ROTATED_TRANSLATED_RECOLOURED_GOAL, key="probe_compose",
        residual=ROTATED_TRANSLATED_RECOLOURED_GOAL, decoded_epoch=_epoch(s, ag),
        dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("dim_checked") == 1, "proof rung 1 alone could not explain the rotation"
    assert at.get("dim_explained"), "generator + residual delta must compose"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_tromino2"
    assert _axes(s) == baseline_axes

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("generator") == "rotation90"
    assert t_at.get("k") == 1
    residual_dims = sorted(list(t_at.get("dims") or []))
    assert residual_dims == [1, 3], (
        f"expected the LEFTOVER row-shift (dim 1) + value-substitution "
        f"(dim 3) after the generator is applied; got {residual_dims!r}")
    transforms = list(t_at.get("transforms") or [])
    assert len(transforms) == 2
    kinds = {t["dim"]: t["kind"] for t in transforms}
    assert kinds == {1: "shift", 3: "subst"}


# ---------------------------------------------------------------------------
# 3 — discriminative null: a residual that fails BOTH rungs (no uniform
#     per-dim delta, and no generator reaches the scrambled colours) falls
#     through to sd_mint_quantum, exactly ONE CapabilityAxis minted. This
#     is the gate that PROVES sd_dim_check_mark's resilience marker does
#     not silently let genuinely-novel structure escape minting.
# ---------------------------------------------------------------------------
def test_scrambled_observation_fails_both_rungs_and_mints():
    s, ag, native = _boot()
    _add_part(s, "part_tromino3", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)

    obs = _observe_decoded(s, ag, signature=SCRAMBLED_GOAL, key="probe_scrambled_dim",
                            residual=SCRAMBLED_GOAL, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert not at.get("transform_explained")
    assert at.get("dim_checked") == 1
    assert not at.get("dim_explained"), "no generator/k explains an incoherent colour scramble"
    assert at.get("status") == "minted"
    assert _axes(s) == baseline_axes + 1
    assert len(list(s.neighbours(obs, "has_transform"))) == 0


# ---------------------------------------------------------------------------
# 4 — reflection case (reflection_r): the tromino reflected about its own
#     row-axis bbox center is recognised, zero mint.
# ---------------------------------------------------------------------------
def test_reflection_recognized_zero_mint():
    s, ag, native = _boot()
    _add_part(s, "part_tromino4", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)

    obs = _observe_decoded(s, ag, signature=REFLECTED_R_GOAL, key="probe_reflect",
                            residual=REFLECTED_R_GOAL, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("dim_explained"), "a bbox-centered row reflection must be explained by reflection_r"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_tromino4"
    assert _axes(s) == baseline_axes

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("generator") == "reflection_r"
    assert t_at.get("k") == 1


# ---------------------------------------------------------------------------
# 5 — rung-order Occam: an observation rung 1 (sd_transform_decode) ALREADY
#     explains must be recognized by rung 1 — dim_checked must NEVER be set
#     (sd_infer_dimension's guard, and sd_dim_check_mark's identical guard,
#     both require transform_explained != 1, so a rung-1 win blocks rung 2
#     outright before either ever looks at the residual).
# ---------------------------------------------------------------------------
def test_rung1_explained_observation_never_sets_dim_checked():
    s, ag, native = _boot()
    _add_part(s, "part_move_track_r2", [["move", "X", "by", "D"], ["stop", "X"]])
    baseline_axes = _axes(s)

    sig = [["move", "Y", "by", "D"], ["stop", "Y"]]
    obs = _observe_decoded(s, ag, signature=sig, key="probe_rung1_wins",
                            residual=sig, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_explained"), "a plain rung-1 substitution must still win at rung 1"
    assert at.get("status") == "recognized_transformed"
    assert at.get("dim_checked") in (None, 0, 0.0), (
        "rung 1 explaining the residual must mean sd_infer_dimension "
        "(and sd_dim_check_mark) NEVER fire — dim_checked stays untouched")
    assert at.get("dim_explained") in (None, 0, 0.0, False)
    assert _axes(s) == baseline_axes


# ---------------------------------------------------------------------------
# 6 — no dim_types on the codebook side: rung 2 gracefully skips (DimInfer
#     finds no dim-typed candidate to apply a generator to -> explained=
#     false, checked=0, no crash) and the observation still mints via the
#     pre-existing path.
# ---------------------------------------------------------------------------
def test_no_dim_types_gracefully_skips_and_mints():
    s, ag, native = _boot()
    _add_part(s, "part_tromino_untyped", TROMINO)  # NO dim_types attr
    baseline_axes = _axes(s)

    # A residual rung 1 also cannot explain (the scrambled colours), so it
    # is genuinely novel with or without rung 2's involvement.
    obs = _observe_decoded(s, ag, signature=SCRAMBLED_GOAL, key="probe_no_dim_types",
                            residual=SCRAMBLED_GOAL, decoded_epoch=_epoch(s, ag))
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("dim_checked") == 1, "rung 2 must still be GIVEN a look (guard-level), just find nothing to apply"
    assert not at.get("dim_explained")
    assert at.get("status") == "minted"
    assert _axes(s) == baseline_axes + 1


# ---------------------------------------------------------------------------
# 7 — organic pipeline: the real induce_concern entrypoint (pending ->
#     decoded -> rung 1 fails -> rung 2 recognises via rotation90), not the
#     hand-set-status="decoded" shortcut the other gates use.
# ---------------------------------------------------------------------------
def test_organic_induce_concern_recognizes_rotation():
    s, ag = boot_core()
    _add_part(s, "part_tromino_organic", TROMINO, dim_types=DIM_TYPES)

    res = rf.induce_concern(s, ROTATED_K1_TROMINO, name_hint="probe_organic_rotate")
    assert res["minted"] is False
    assert res.get("covered_by") == "part_tromino_organic"
    assert "transform" in res, (
        "the organic pipeline must reach recognized_transformed via rung 2 "
        "for a residual rung 1 cannot explain")
    assert res["transform"].get("generator") == "rotation90"
    assert res["transform"].get("k") == 1


# ---------------------------------------------------------------------------
# 8 — BASE-AS-DIMENSION: a x2-scaled shape is recognised via the `scale2`
#     generator (seed v1.4.0). A LOG2-SCALE base is a DIMENSION, not
#     hand-set config: recognized_transformed, ZERO CapabilityAxis minted,
#     ONE LatentDimension `latent:scale2` minted carrying k=1. This is the
#     capability half of the claim — a ratio (x2) is now recognised for
#     free as the additive k-delta, so a novel size no longer mints.
# ---------------------------------------------------------------------------
def test_scaled_grid_recognized_via_scale2_generator_zero_mint():
    s, ag, native = _boot()
    _add_part(s, "part_scale_tromino", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)
    baseline_latent = len(list(s.nodes("LatentDimension")))

    obs = _observe_decoded(s, ag, signature=SCALED_X2_TROMINO, key="probe_scale",
                            residual=SCALED_X2_TROMINO, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_checked") == 1
    assert at.get("dim_checked") == 1, (
        "a x2 scaling is NOT a uniform per-dim shift (deltas 0/+1/0 across "
        "cells), so rung 1 must fail and hand off to rung 2 — the proof the "
        "scale base is inferred, not a plain translation")
    assert at.get("dim_explained"), "scale2 must explain the x2-scaled tromino"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_scale_tromino"
    assert _axes(s) == baseline_axes, "recognising a scale FAMILY must mint NO CapabilityAxis"

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("generator") == "scale2"
    assert t_at.get("k") == 1
    assert t_at.get("dim") == "latent:scale2"
    assert t_at.get("delta") == 1
    assert t_at.get("base") == "part_scale_tromino"

    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1
    ld_node = next(iter(s.neighbours(obs, "has_latent_dimension")))
    ld_at = s.node(ld_node)["attrs"]
    assert ld_at.get("generator") == "scale2"
    assert ld_at.get("k") == 1
    assert ld_at.get("name") == "latent:scale2"


# ---------------------------------------------------------------------------
# 9 — TERMINATION: the base-dimension is minted EXACTLY ONCE. Bumping the
#     codebook epoch re-arms the observation (sd_redecode), but the
#     `has_transform`-edge guard on sd_recognize_dim blocks a second
#     LatentDimension / Transform — a recurring scaled observation does not
#     grow the graph unboundedly (the efficiency half of the claim, and the
#     'salience for axes' unbounded-growth guard applied one rung up).
# ---------------------------------------------------------------------------
def test_scale_base_dimension_minted_once_terminates_under_growth():
    s, ag, native = _boot()
    _add_part(s, "part_scale_term", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)
    baseline_latent = len(list(s.nodes("LatentDimension")))

    obs = _observe_decoded(s, ag, signature=SCALED_X2_TROMINO, key="probe_scale_term",
                            residual=SCALED_X2_TROMINO, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()
    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1
    assert _axes(s) == baseline_axes

    # Grow the codebook (mechanical epoch bump, as grow_part_library does)
    # and pump the loop again: the observation re-arms but must NOT re-mint.
    s.set_attr(ag, "codebook_epoch", (_epoch(s, ag) or 0.0) + 1)
    native.run_rules()

    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1, (
        "a re-decoded scaled observation must reuse its base dimension, not "
        "mint a second latent:scale2")
    assert _axes(s) == baseline_axes, "still zero CapabilityAxis after growth"
    assert len(list(s.neighbours(obs, "has_transform"))) == 1, "exactly one Transform node"


# ---------------------------------------------------------------------------
# 10 — PHASE-AS-DIMENSION: a cyclic observation whose row slot has stepped
#      by ONE around a Z_4 ring is recognised via the `modular` generator
#      `cycle4` (seed v1.5.0). The row-3 cell WRAPS to 0, so the held->goal
#      delta is non-uniform and rung 1 cannot explain it: recognized_
#      transformed, ZERO CapabilityAxis minted, ONE LatentDimension
#      `latent:cycle4` minted carrying k=1. Mirrors gate 8 (scale2), one
#      generator over. The whole point is the WRAP — without it a modular
#      step is indistinguishable from a plain shift (see gate 12).
# ---------------------------------------------------------------------------
def test_cyclic_grid_recognized_via_modular_generator_zero_mint():
    s, ag, native = _boot()
    _add_part(s, "part_cycle", CYCLE_PAIR, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)
    baseline_latent = len(list(s.nodes("LatentDimension")))

    obs = _observe_decoded(s, ag, signature=CYCLE_K1, key="probe_cycle",
                            residual=CYCLE_K1, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_checked") == 1
    assert at.get("dim_checked") == 1, (
        "a Z_4 wrap (row 3 -> 0) is NOT a uniform per-dim shift (deltas +1 "
        "and -3 across the two cells), so rung 1 must fail and hand off to "
        "rung 2 — the proof the cyclic phase is inferred, not a plain shift")
    assert at.get("dim_explained"), "cycle4 must explain the wrapped cyclic pair"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_cycle"
    assert _axes(s) == baseline_axes, "recognising a phase FAMILY must mint NO CapabilityAxis"

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("generator") == "cycle4"
    assert t_at.get("k") == 1
    assert t_at.get("dim") == "latent:cycle4"
    assert t_at.get("delta") == 1
    assert t_at.get("base") == "part_cycle"

    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1
    ld_node = next(iter(s.neighbours(obs, "has_latent_dimension")))
    ld_at = s.node(ld_node)["attrs"]
    assert ld_at.get("generator") == "cycle4"
    assert ld_at.get("k") == 1
    assert ld_at.get("name") == "latent:cycle4"


# ---------------------------------------------------------------------------
# 11 — TERMINATION: the cyclic base-dimension is minted EXACTLY ONCE.
#      Bumping the codebook epoch re-arms the observation (sd_redecode), but
#      the `has_transform`-edge guard on sd_recognize_dim blocks a second
#      LatentDimension / Transform — a recurring cyclic observation does not
#      grow the graph unboundedly. Mirrors gate 9 (scale2), one generator
#      over.
# ---------------------------------------------------------------------------
def test_cyclic_base_dimension_minted_once_terminates_under_growth():
    s, ag, native = _boot()
    _add_part(s, "part_cycle_term", CYCLE_PAIR, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)
    baseline_latent = len(list(s.nodes("LatentDimension")))

    obs = _observe_decoded(s, ag, signature=CYCLE_K1, key="probe_cycle_term",
                            residual=CYCLE_K1, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()
    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1
    assert _axes(s) == baseline_axes

    # Grow the codebook (mechanical epoch bump, as grow_part_library does)
    # and pump the loop again: the observation re-arms but must NOT re-mint.
    s.set_attr(ag, "codebook_epoch", (_epoch(s, ag) or 0.0) + 1)
    native.run_rules()

    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1, (
        "a re-decoded cyclic observation must reuse its base dimension, not "
        "mint a second latent:cycle4")
    assert _axes(s) == baseline_axes, "still zero CapabilityAxis after growth"
    assert len(list(s.neighbours(obs, "has_transform"))) == 1, "exactly one Transform node"


# ---------------------------------------------------------------------------
# 12 — WRAP-DISCRIMINATION: a NON-wrapping uniform shift on the SAME cyclic
#      row axis (rows {0,3} -> {1,4}, no value crosses the modulus) is a
#      plain per-dimension delta rung 1 (sd_transform_decode) explains
#      outright, so dim_checked is NEVER set — `cycle4` only fires when the
#      wrap is genuinely needed. This is the gate that PROVES the modulus is
#      load-bearing: a modular step that does not wrap is indistinguishable
#      from an ordinary shift, and rung 1 (Occam-earlier) claims it.
# ---------------------------------------------------------------------------
def test_nonwrapping_shift_is_explained_by_rung1_never_reaches_modular():
    s, ag, native = _boot()
    _add_part(s, "part_cycle_nowrap", CYCLE_PAIR, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)

    obs = _observe_decoded(s, ag, signature=NONWRAP_ROW_SHIFT, key="probe_nowrap",
                            residual=NONWRAP_ROW_SHIFT, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_explained"), "a non-wrapping row shift must win at rung 1"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_cycle_nowrap"
    assert at.get("dim_checked") in (None, 0, 0.0), (
        "rung 1 explaining the non-wrapping shift must mean sd_infer_dimension "
        "(and therefore cycle4) NEVER fire — dim_checked stays untouched")
    assert at.get("dim_explained") in (None, 0, 0.0, False)
    assert _axes(s) == baseline_axes

    # The Transform recorded is a plain per-dimension delta, NOT a generator.
    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("generator") in (None, ""), "no generator should be attributed to a plain shift"
    assert sorted(list(t_at.get("dims") or [])) == [1], "a uniform shift on the row slot (dim 1)"


# ---------------------------------------------------------------------------
# 13 — COMPOSITION (length 2): a tromino ROTATED THEN SCALED (seed v1.6.0)
#      is recognised via a length-2 composition of rotation90 THEN scale2 —
#      NEITHER generator alone explains it. recognized_transformed, ZERO
#      CapabilityAxis minted, ONE composite LatentDimension
#      `latent:rotation90+scale2` minted carrying the step SEQUENCE
#      (generators/ks). The composite Transform node carries the same
#      sequence; scalar generator/k stay the FIRST step (back-compat).
# ---------------------------------------------------------------------------
def test_composed_rotate_then_scale_recognized_length2_zero_mint():
    s, ag, native = _boot()
    _add_part(s, "part_comp_rs", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)
    baseline_latent = len(list(s.nodes("LatentDimension")))

    obs = _observe_decoded(s, ag, signature=ROTATE_SCALE_GOAL, key="probe_rotate_scale",
                            residual=ROTATE_SCALE_GOAL, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("transform_checked") == 1
    assert at.get("dim_checked") == 1, (
        "a rotate-then-scale is neither a uniform per-dim shift (rung 1) nor "
        "a single generator, so rung 1 must fail and hand off to rung 2")
    assert at.get("dim_explained"), "the rotation90 THEN scale2 composition must explain it"
    assert at.get("status") == "recognized_transformed"
    assert at.get("covered_by") == "part_comp_rs"
    assert _axes(s) == baseline_axes, "recognition-under-a-composition must mint NO CapabilityAxis"

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    # The composite label + step sequence — the headline of v1.6.0.
    assert t_at.get("dim") == "latent:rotation90+scale2"
    assert list(t_at.get("generators") or []) == ["rotation90", "scale2"]
    assert list(t_at.get("ks") or []) == [1, 1]
    assert t_at.get("base") == "part_comp_rs"
    # Scalar back-compat fields carry the FIRST step.
    assert t_at.get("generator") == "rotation90"
    assert t_at.get("k") == 1

    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1, (
        "exactly ONE composite LatentDimension for the whole 2-step sequence")
    ld_node = next(iter(s.neighbours(obs, "has_latent_dimension")))
    ld_at = s.node(ld_node)["attrs"]
    assert ld_at.get("name") == "latent:rotation90+scale2"
    assert list(ld_at.get("generators") or []) == ["rotation90", "scale2"]
    assert list(ld_at.get("ks") or []) == [1, 1]


# ---------------------------------------------------------------------------
# 14 — COMPOSITION (length 2), distinct pair: reflect THEN scale is inferred
#      as (reflection_r, scale2), a DIFFERENT pair than gate 13 for a
#      different image — proving the inferred sequence is meaningful, not a
#      generic "some two generators" catch-all.
# ---------------------------------------------------------------------------
def test_composed_reflect_then_scale_recognized_length2():
    s, ag, native = _boot()
    _add_part(s, "part_comp_fs", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)

    obs = _observe_decoded(s, ag, signature=REFLECT_SCALE_GOAL, key="probe_reflect_scale",
                            residual=REFLECT_SCALE_GOAL, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("dim_explained"), "the reflection_r THEN scale2 composition must explain it"
    assert at.get("status") == "recognized_transformed"
    assert _axes(s) == baseline_axes

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("dim") == "latent:reflection_r+scale2"
    assert list(t_at.get("generators") or []) == ["reflection_r", "scale2"]
    assert list(t_at.get("ks") or []) == [1, 1]


# ---------------------------------------------------------------------------
# 15 — ALIAS-NULL / Occam (seed level): a PURE x2-scaled tromino stays a
#      LENGTH-1 `scale2` recognition even though rotation90/scale2 are BOTH
#      in the codebook (so length-2 compositions are available). Composition
#      LENGTH is the strict-primary Occam key, so the single-generator
#      explanation wins — NO spurious 2-step. The minted Transform/
#      LatentDimension label stays `latent:scale2`, generators=["scale2"].
# ---------------------------------------------------------------------------
def test_pure_scale_stays_length1_no_spurious_composition():
    s, ag, native = _boot()
    _add_part(s, "part_alias_null", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)

    obs = _observe_decoded(s, ag, signature=SCALED_X2_TROMINO, key="probe_alias_null",
                            residual=SCALED_X2_TROMINO, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()

    at = s.node(obs)["attrs"]
    assert at.get("dim_explained")
    assert at.get("status") == "recognized_transformed"
    assert _axes(s) == baseline_axes

    t_node = next(iter(s.neighbours(obs, "has_transform")))
    t_at = s.node(t_node)["attrs"]
    assert t_at.get("dim") == "latent:scale2", "a pure scale must NOT be minted as a composite"
    assert list(t_at.get("generators") or []) == ["scale2"], "length 1 — no spurious 2-step"
    assert list(t_at.get("ks") or []) == [1]
    assert t_at.get("generator") == "scale2"
    assert t_at.get("k") == 1


# ---------------------------------------------------------------------------
# 16 — TERMINATION: a composite base-dimension is minted EXACTLY ONCE.
#      Bumping the codebook epoch re-arms the observation (sd_redecode) but
#      the `has_transform`-edge guard blocks a second composite Transform /
#      LatentDimension — a recurring composed observation does not grow the
#      graph unboundedly (mirrors gates 9/11, one rung's composition over).
# ---------------------------------------------------------------------------
def test_composite_dimension_minted_once_terminates_under_growth():
    s, ag, native = _boot()
    _add_part(s, "part_comp_term", TROMINO, dim_types=DIM_TYPES)
    baseline_axes = _axes(s)
    baseline_latent = len(list(s.nodes("LatentDimension")))

    obs = _observe_decoded(s, ag, signature=ROTATE_SCALE_GOAL, key="probe_comp_term",
                            residual=ROTATE_SCALE_GOAL, decoded_epoch=_epoch(s, ag),
                            dim_types=DIM_TYPES)
    native.run_rules()
    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1
    assert _axes(s) == baseline_axes

    s.set_attr(ag, "codebook_epoch", (_epoch(s, ag) or 0.0) + 1)
    native.run_rules()

    assert len(list(s.nodes("LatentDimension"))) == baseline_latent + 1, (
        "a re-decoded composed observation must reuse its composite dimension, "
        "not mint a second latent:rotation90+scale2")
    assert _axes(s) == baseline_axes, "still zero CapabilityAxis after growth"
    assert len(list(s.neighbours(obs, "has_transform"))) == 1, "exactly one composite Transform node"
