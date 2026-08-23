"""PARALLAX / EFFERENCE-COPY seed gate (rung 116000).

The graph-resident realization of the parallax rung: `seeds/parallax_efference.json`
replaces `vision_motion_group`'s mo_dominant (ESTIMATED reference frame = the
largest group's velocity) with a SUPPLIED efference copy (field.efference_v),
so the fixated plane reads stationary (space constancy) and parallax carves the
residual into surfaces.

This gate is FUNCTIONAL and POSITIVE-CONTROLLED BOTH WAYS (§1 clause 4, §12.3):

  * DEFAULT OFF is byte-identical to vision_motion_group (§9) -- a seed that
    changed committed behaviour when disarmed would FAIL here;
  * ARMED is LOAD-BEARING (§13.2 / §1's fifth clause): arming with a chosen
    fixation refuses a DIFFERENT plane than the estimated dominant, moving the
    minted object set. The DEAD-CONTROL (arming with the SAME vector the field
    would estimate as dominant) collapses the difference -- if it did NOT, the
    load-bearing test would be theatre;
  * space constancy: the fixated plane's ground-truth residual is EXACTLY 0, and
    a FLAT world armed on its own uniform motion mints ZERO objects.

No new numeric threshold enters the seed (§13): its only literals are flag
guards (`> 0.5`, the same standing as vision_motion_group's own flag guards) and
the -1/0/1 sentinels; the agreement tolerance is still the field's own
(reused from vision_motion_group), never a constant in this file.
"""
from __future__ import annotations
import json
import pathlib
import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

pytest.importorskip("substrate_rs")
import sys
sys.path.insert(0, str(ROOT / "scripts"))
from parallax_char import make_scene, vector_field           # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into    # noqa: E402
import domains.motion_group_world as mgw                       # noqa: E402

SHIFTS = [0, 3, 6]      # 3 depth planes; fixation = middle (index 1), velocity (0,3)
BLOCK = 8
GRID = 144
REF = 1


def _obj_key(objs):
    return sorted((int(o["root"]), int(o["members"]),
                   (float(o["v"][0]), float(o["v"][1]))) for o in objs)


def _run(V, *, load_mine, arm_vec):
    s, ag = boot_core()
    seeds = ["vision_motion_group", "parallax_efference"] if load_mine else ["vision_motion_group"]
    load_seeds_into(s, ag, seeds)
    h = mgw.add_mfield(s, V)
    if load_mine:
        for p in s.nodes("MotionParams"):
            s.set_attr(p, "mo_efference", 1.0 if arm_vec is not None else 0.0)
        if arm_vec is not None:
            s.set_attr(h["field"], "efference_v", [float(arm_vec[0]), float(arm_vec[1])])
    # THE EXACT ARM, SELECTED DELIBERATELY (was `mtol_exact=0.0`, the Otsu arm).
    #
    # `mtol_exact` is an ARM SELECTOR, not a value: above 0.5 it picks
    # `mo_tol_exact` (tolerance = exact integer vector equality, mtol = 0), below
    # it picks `mo_tol_otsu`. These fixtures are piecewise-constant synthetic
    # velocity fields -- three planes at (0,0), (0,3), (0,6) plus noise -- and
    # what they depend on is exact grouping.
    #
    # They were passing on the OTSU arm only because `mo_tol_otsu` was broken:
    # its divide guard was written `{Max, a, b}` where the variant takes `items`,
    # which the Term reader silently accepted as `Max{items: []}` = 0, so every
    # candidate threshold scored 0/0 and the Argmax returned an arbitrary cell --
    # in practice pd = 0.0, which is precisely the EXACT arm's value. The seed
    # calls the two arms "mutually exclusive"; this suite was nominally on one
    # and behaviourally on the other.
    #
    # With the reader made strict (jsonio.rs `children_of`) and the seed's arity
    # corrected, Otsu genuinely computes -- and returns 2.0 on this field, which
    # lets noise cells within 2.0 of a plane bridge into it and dissolves the
    # planes. So the arm is now named explicitly rather than arrived at by
    # accident.
    #
    # WHAT THIS NARROWS, said plainly: the parallax capability's behaviour under
    # a genuinely DERIVED tolerance is no longer covered here, and on the
    # measured evidence it does not currently hold. That is an open question
    # about Otsu on smoothly graded fields, not something this switch answers.
    mgw.settle(s, marm=1.0, mcontrast=1.0, mtol_exact=1.0)
    dom = tuple(float(x) for x in (mgw.field_attr(s, h, "dom_v") or (0.0, 0.0)))
    return _obj_key(mgw.objects(s)), dom, mgw.assert_settled(s, h)["unsettled_pairs"]


def _field(cond, seed=116000):
    sc = make_scene(np.random.default_rng(seed), SHIFTS, BLOCK, grid=GRID, ref_idx=REF)
    return vector_field(sc["a"], sc["b_depth" if cond == "DEPTH" else "b_flat"], BLOCK), sc


def test_seed_is_registered_and_loads():
    V, _ = _field("DEPTH")
    key, _dom, un = _run(V, load_mine=True, arm_vec=None)
    assert un == 0                       # genuine fixpoint (assert_settled clean)


def test_default_off_is_byte_identical():
    """§9: loaded+disarmed == not loaded, on every confirmatory-adjacent seed."""
    for seed in (116000, 116001, 116002):
        V, _ = _field("DEPTH", seed)
        base, _b, _ = _run(V, load_mine=False, arm_vec=None)
        off, _o, _ = _run(V, load_mine=True, arm_vec=None)
        assert off == base, f"seed {seed}: disarmed seed changed behaviour"


def test_armed_is_load_bearing_and_refuses_the_chosen_fixation():
    """§13.2: arming on the CHOSEN fixation (0,3) moves the object set, and the
    fixation plane is refused (its velocity is not among the minted surfaces)."""
    moved = 0
    for seed in (116000, 116001, 116002):
        V, _ = _field("DEPTH", seed)
        base, base_dom, _ = _run(V, load_mine=False, arm_vec=None)
        arm, arm_dom, un = _run(V, load_mine=True, arm_vec=(0, 3))
        assert un == 0
        assert arm_dom == (0.0, 3.0), "efference copy must become the reference frame"
        # the estimated dominant is the largest band (near, (0,6)); arming refuses (0,3) instead
        assert base_dom != (0.0, 3.0)
        surfaces = {(v0, v1) for (_r, m, (v0, v1)) in arm if m >= 5}
        assert (0.0, 3.0) not in surfaces, "the fixated plane must be refused (space constancy)"
        assert (0.0, 6.0) in surfaces and (0.0, 0.0) in surfaces, "near+far must be minted"
        if arm != base:
            moved += 1
    assert moved == 3, "arming must MOVE the minted set vs the disarmed baseline"


def test_dead_control_arming_on_the_estimated_dominant_does_NOT_move():
    """POSITIVE CONTROL for the load-bearing test: if we arm the efference copy
    with the SAME vector the field would estimate as dominant, the refusal set
    is unchanged -- proving the load-bearing test above bites on the CHOICE of
    reference, not merely on the seed being loaded."""
    V, sc = _field("DEPTH")
    base, base_dom, _ = _run(V, load_mine=False, arm_vec=None)
    # arm on the estimated dominant itself
    arm_same, dom_same, _ = _run(V, load_mine=True, arm_vec=base_dom)
    assert dom_same == base_dom
    assert arm_same == base, "arming on the estimated dominant must reproduce the baseline set"


def test_flat_world_armed_reads_stationary_space_constancy():
    """A FLAT world armed on its own uniform motion mints ZERO objects: the whole
    world reads stationary despite the retinal shift (space constancy)."""
    for seed in (116000, 116001, 116002):
        V, _ = _field("FLAT", seed)
        arm, dom, un = _run(V, load_mine=True, arm_vec=(0, 3))
        assert un == 0
        assert dom == (0.0, 3.0)
        assert len(arm) == 0, f"seed {seed}: FLAT armed should mint no objects"


def test_space_constancy_is_exact_on_ground_truth():
    """The fixated plane's residual under the KNOWN efference copy is EXACTLY 0
    (exact-to-pixel), on the true field by construction."""
    sc = make_scene(np.random.default_rng(116000), SHIFTS, BLOCK, grid=GRID, ref_idx=REF)
    delta = np.array([0.0, float(SHIFTS[REF])])
    R = sc["t_depth"] - delta
    refmask = sc["owner"] == REF
    assert float(np.abs(R[refmask]).max()) == 0.0


def test_seed_has_no_tuned_threshold():
    """§13: the seed's numeric literals are ONLY flag guards (0.5) and -1/0/1
    sentinels; NO agreement tolerance or magnitude threshold is a constant here
    (it is reused from vision_motion_group's own field-derived tolerance)."""
    blob = json.loads((ROOT / "seeds" / "parallax_efference.json").read_text())
    lits = []

    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "Lit":
                lits.append(float(x["value"]))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(blob["rules"])
    allowed = {0.5, -1.0, 1.0, 0.0}
    assert set(lits) <= allowed, f"unexpected numeric literal in seed: {set(lits) - allowed}"
