"""WELL-POSEDNESS — the synthetic gate re-run under the THIRD predicate.

`VISION_FIGADJ_WELLPOSED_PREREG.md` M-B. Seed `vision_border_ownership` v1.2.0.

`test_border_ownership_migrated.py` pins the incumbent 9/9 and
`test_border_ownership_owned_migrated.py` pins the competitive replacement 9/9.
Neither is evidence about the well-posedness conjunct — for both, `bown_wp` is
at its 0.0 default and the `Or` short-circuits. THIS file is the constraint
tested substantively: all nine arms re-run with `bown_wp` ARMED.

WHY THIS FILE IS THE ONE THAT MATTERS. The failed control it answers is a
FALSE POSITIVE (26/100 mints on iid speckle), and the cheap way to fix a false
positive is to trade it for a false NEGATIVE — exclude small components and the
speckle tax vanishes along with every small genuine figure. That trade is
exactly what these nine arms refuse to let happen silently: they contain small
figures, an open contour that must stay refused, an ambiguous split that must
stay held open, and a 100-field noise floor.

`arm_floor_noise` (seeds 36000-36099, the incumbent arm's own range, reused so
all three predicates see byte-identical fields) is load-bearing in the opposite
direction from the 18x18 control: it must remain 0/100 here too, so the
conjunct is not merely relocating the failure.
"""
import pytest

from domains.engine_provenance import engine_preamble

engine_preamble()

from scripts import border_ownership_measure as bom  # noqa: E402


@pytest.fixture(autouse=True)
def _armed():
    """Arm BOTH the competitive predicate and the well-posedness conjunct for
    every arm in this file, and restore."""
    prev_own, prev_wp = bom.BOWN_OWN_DEFAULT, bom.BOWN_WP_DEFAULT
    bom.BOWN_OWN_DEFAULT = 1.0
    bom.BOWN_WP_DEFAULT = 1.0
    try:
        yield
    finally:
        bom.BOWN_OWN_DEFAULT = prev_own
        bom.BOWN_WP_DEFAULT = prev_wp


def test_HEADLINE_zhou_flip_survives_the_replacement():
    r = bom.arm_zhou()
    assert r["pass"], r
    assert r["window_identical"]
    assert r["A_owns_55_56"] == [1, 0]
    assert r["B_owns_55_56"] == [0, 1]
    assert r["flipped"]
    assert r["A_left_target"] is not None and r["B_right_target"] is not None


def test_figure_ground_closed_still_mints_exactly_one_owned_proto():
    r = bom.arm_figure_ground()
    assert r["pass"], r
    assert r["n_protos"] == 1
    assert r["protos"][0]["members"] == 24 and r["protos"][0]["gestalt"] == 0
    assert r["all_perimeter_own"]
    assert r["all_perimeter_target_is_proto"]
    assert r["no_interior_own"]
    assert r["surround_is_ground"]


def test_recurrence_fixpoint_still_globally_consistent_and_load_bearing():
    r = bom.arm_recurrence()
    assert r["pass"], r
    assert r["sweeps"] > 1
    assert r["distinct_owned_roots"] == 1
    assert r["n_protos"] == 1
    assert r["flood_monotone"]


def test_gestalt_size_unchanged():
    r = bom.arm_size()
    assert r["pass"], r


def test_floor_open_contour_still_owns_nothing():
    r = bom.arm_floor_open()
    assert r["pass"], r
    assert r["n_protos"] == 0


def test_floor_ambiguous_symmetric_split_still_held_open():
    r = bom.arm_floor_ambiguous()
    assert r["pass"], r
    assert r["n_protos"] == 0


def test_floor_NOISE_still_mints_nothing_under_the_weaker_gate():
    """THE LOAD-BEARING FLOOR. The replacement is strictly more permissive, so
    this is where a confabulating gate would announce itself: 100 iid fields,
    still zero false proto-objects.

    SEED DISCLOSURE: this arm draws seeds 36000-36099 — the INCUMBENT arm's own
    range, deliberately reused so the two predicates see the BYTE-IDENTICAL 100
    fields and the comparison is paired. It is not an allocation out of this
    rung's 83000-83999 block; it is the same control, re-run.
    """
    r = bom.arm_floor_noise()
    assert r["pass"], r
    assert r["false_mint_fields"] == 0, r
    assert r["seed_range"] == [36000, 36099]


def test_convexity_still_exploratory_and_held_open():
    r = bom.arm_convexity()
    assert r["held_open"], r
    assert r["n_protos"] == 0


def test_offday_seed_still_inert_by_default():
    """§9: with `bown` OFF the seed writes nothing, whichever predicate is armed."""
    r = bom.arm_offday()
    assert r["pass"], r
    assert r["n_protos"] == 0
    assert r["max_bg"] == 0.0 and r["max_owns"] == 0.0
