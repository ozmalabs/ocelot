"""COMPETITIVE BORDER OWNERSHIP — the synthetic gate re-run under the REPLACEMENT.

`VISION_FIGADJ_REPLACEMENT_PREREG.md`. Seed `vision_border_ownership` v1.1.0.

`tests/test_border_ownership_migrated.py` pins the incumbent 9/9 with
`bown_own` at its 0.0 default. That file passing is NOT evidence about the
replacement — it is the flag being off. THIS file is constraint 1 tested
substantively: every one of the nine synthetic arms is re-run with
`bo_mint_owned` armed, and must return the SAME verdict.

Why it must: on a synthetic figure-on-blank stimulus the figure component has no
abutting enclosed component at all, so the competitive conjunct
`Not(Lt(R.rim, n.rim))` is never reached and `bo_mint_owned`'s term tree
evaluates identically to `bo_mint_enclosed`'s. The replacement is a STRICT
WEAKENING: it agrees with the incumbent on every component that touches nothing,
and differs only where a component abuts another enclosed component — the case a
photograph is full of and a synthetic raster has none of. These tests assert
that identity rather than assuming it.

The noise floor is the load-bearing one: a more permissive gate is exactly the
kind of change that starts minting on speckle, and `arm_floor_noise` (100 iid
fields) is where that would show.
"""
import pytest

from domains.engine_provenance import engine_preamble

engine_preamble()

from scripts import border_ownership_measure as bom  # noqa: E402


@pytest.fixture(autouse=True)
def _armed():
    """Arm the competitive predicate for every arm in this file, and restore."""
    prev = bom.BOWN_OWN_DEFAULT
    bom.BOWN_OWN_DEFAULT = 1.0
    try:
        yield
    finally:
        bom.BOWN_OWN_DEFAULT = prev


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
