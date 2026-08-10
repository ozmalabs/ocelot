"""MECHANISM GATE for `SupportInfer` (the appearance-partition rung).

Every field this gate reads off a refusal is asserted by an INDEPENDENT Term
evaluation, ONE PER FIELD.  That shape is not decoration: `GapAbduce`'s
`refused()` calls `finish()`, **which SELECTS the field**, so a patch that
restored a measurement on a refusal SILENTLY DID NOTHING on every call that
asked for it -- an output of the constructor masquerading as a measurement,
caught by a mechanism test rather than by inspection.

What it asserts:

  * **A0 -- the Term ACCEPTS its own best case.**  A mechanism you have not
    made accept is one whose refusals mean nothing, and a DEAD READER SCORES A
    PERFECT REFUSAL ARM -- the two are the same measurement on this class of
    question (the refusal-capacity rung nearly published a fake null of exactly
    this shape).
  * **THE HEADLINE: it explains what `TimeInfer` refuses**, on the identical
    stimulus, when the ONLY difference is appearance.
  * **IT STILL REFUSES** -- a broken offset, a broken cardinality, a broken
    predicate, and the IDENTITY.
  * **`appearance_residual` IS MEASURED, NOT A CONSTRUCTOR DEFAULT** -- it
    takes DIFFERENT values on different stimuli, and is non-zero exactly where
    appearance differs.
  * **`compared` PROVES THE PASS RAN** -- a refusal is a failure after a full
    comparison, not a refusal at a guard.
  * **THE RASTER IS STILL DEAD, AND AT THE IDENTITY CLAUSE** -- appearance
    tolerance does not rescue a dense bounded raster.  This is the rung's
    prior question, asserted at the mechanism.
"""
from __future__ import annotations
import json
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs                               # noqa: E402
from substrate.boot_core import boot_core                # noqa: E402
from domains import reflective_faculty as rf             # noqa: E402

DT_V = ["pred", "coord:r", "coord:c", "val"]


def _boot(frames, dt=DT_V):
    s, ag = boot_core()
    rf._native_eval2(s)
    s.add_node("ShapeSignature",
               {"name": "sup_base", "signature": json.dumps(frames[0]),
                "kind": "faculty", "faculty": "sup_base", "dim_types": dt})
    return s


def _field(frames, field, dt=DT_V):
    """ONE Term evaluation PER FIELD -- the shape in which the `finish()`
    selection bug surfaces."""
    s = _boot(frames, dt)
    return s.evaluate(srs.Term("SupportInfer", sequence=srs.Lit(frames),
                               codebook_type="ShapeSignature", field=field), {})


def _time_infer(frames, field, dt=DT_V):
    s = _boot(frames, dt)
    return s.evaluate(srs.Term("TimeInfer", sequence=srs.Lit(frames),
                               codebook_type="ShapeSignature",
                               max_b=8, field=field), {})


# --- stimuli ---------------------------------------------------------------
def _cells(c0, val):
    return [["px", 0, c0, val], ["px", 0, c0 + 1, val], ["px", 1, c0, val]]


RIGID_SAME = [_cells(0, 7), _cells(4, 7), _cells(8, 7)]          # appearance fixed
RIGID_VARY = [_cells(0, 7), _cells(4, 3), _cells(8, 9)]          # appearance VARIES
STATIC = [_cells(0, 7), _cells(0, 7), _cells(0, 7)]
ACCEL = [_cells(0, 7), _cells(4, 7), _cells(12, 7)]


# --------------------------------------------------------------------------- #
def test_A0_the_term_ACCEPTS_its_own_best_case():
    """A mechanism you have not made ACCEPT is one whose refusals mean
    nothing."""
    assert _field(RIGID_SAME, "explained") is True
    assert tuple(_field(RIGID_SAME, "offset")) == (0, 4)
    assert _field(RIGID_SAME, "kind") == "translate"


def test_THE_HEADLINE_it_explains_what_TimeInfer_refuses():
    """THE IDENTICAL STIMULUS.  The only difference is the appearance slot,
    and it is the ONLY thing R6 forbids to change."""
    assert _time_infer(RIGID_VARY, "explained") is False
    assert _field(RIGID_VARY, "explained") is True
    assert tuple(_field(RIGID_VARY, "offset")) == (0, 4)
    # and the two AGREE where appearance is constant -- the partition is a
    # strict ADDITION, not a different mechanism.
    assert _time_infer(RIGID_SAME, "explained") is True
    assert _field(RIGID_SAME, "explained") is True


def test_the_appearance_residual_is_MEASURED_not_a_constructor_default():
    """It must take DIFFERENT values on different stimuli.  A field that reads
    the same on every call cannot distinguish a measurement from an absence."""
    quiet = _field(RIGID_SAME, "appearance_residual")
    loud = _field(RIGID_VARY, "appearance_residual")
    assert quiet == 0, quiet
    assert loud > 0, loud
    assert quiet != loud
    assert _field(RIGID_SAME, "appearance_identical") is True
    assert _field(RIGID_VARY, "appearance_identical") is False


def test_it_STILL_REFUSES_a_broken_offset():
    """ONE offset must carry the WHOLE orbit -- THE THIRD FRAME CONSTRAINS."""
    assert _field(ACCEL, "explained") is False
    assert _field(ACCEL, "reason") == "offset"


def test_it_STILL_REFUSES_the_identity():
    """A still pattern is not a motion."""
    assert _field(STATIC, "explained") is False
    assert _field(STATIC, "reason") == "identity"


def test_it_STILL_REFUSES_a_broken_cardinality():
    frames = [_cells(0, 7), _cells(4, 7)[:-1]]
    assert _field(frames, "explained") is False
    assert _field(frames, "reason") == "cardinality"


def test_it_STILL_REFUSES_a_changed_PREDICATE():
    """The predicate slot is NEVER transformable -- it stays inside the
    verdict when appearance leaves it."""
    frames = [_cells(0, 7), [["qq", 0, 4, 7], ["qq", 0, 5, 7], ["qq", 1, 4, 7]]]
    assert _field(frames, "explained") is False
    assert _field(frames, "reason") == "predicate"


def test_a_refusal_is_a_FAILURE_AFTER_A_FULL_PASS_not_a_guard():
    """`compared` counts the cell pairs actually examined.  A gate that
    refuses BEFORE searching is a §13 negative, not a result."""
    assert _field(ACCEL, "compared") > 0
    assert _field(STATIC, "compared") == len(STATIC[0]) * (len(STATIC) - 1)
    # a GUARD refusal, by contrast, compares nothing
    assert _field([_cells(0, 7)], "compared") == 0
    assert _field([_cells(0, 7)], "reason") == "few_frames"


def test_THE_RASTER_IS_STILL_DEAD_AND_AT_THE_IDENTITY_CLAUSE():
    """THE RUNG'S PRIOR QUESTION, ASSERTED AT THE MECHANISM.

    A full raster's coordinate SET is translation-INVARIANT, so an EXACT
    toroidal roll pairs (r,c) with (r,c), the offset reads (0,0), and the
    IDENTITY clause refuses.  **Appearance tolerance does not rescue a raster
    -- it changes WHICH clause kills it, and the new clause is worse: the
    operator now refuses because it sees NO MOTION AT ALL.**"""
    w = 6
    base = [[i * 3 % 11 for i in range(w)] for _ in range(2)]
    def raster(shift):
        return [["px", r, c, base[r][(c - shift) % w]]
                for r in range(2) for c in range(w)]
    rolled = [raster(0), raster(2), raster(4)]
    assert _field(rolled, "explained") is False
    assert _field(rolled, "reason") == "identity"
    assert tuple(_field(rolled, "offset")) == ()
    # and the pass DID run -- this is not a guard refusal
    assert _field(rolled, "compared") == 2 * w * 2


def test_the_partition_does_not_leak_on_a_swapped_appearance():
    """Everything `SupportInfer` accepts that `TimeInfer` refused must carry a
    NON-ZERO residual.  If it did not, the tolerance would be swallowing a
    discrimination silently instead of MOVING it to a second verdict."""
    assert _time_infer(RIGID_VARY, "explained") is False
    assert _field(RIGID_VARY, "explained") is True
    assert _field(RIGID_VARY, "appearance_residual") > 0
