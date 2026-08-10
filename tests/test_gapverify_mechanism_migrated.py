"""MECHANISM GATE for `GapVerify` -- VERIFY ON THE PRODUCT, NOT THE PRODUCER.

The gapabduce rung's second recorded error is the reason this file exists:
`refused()` calls `finish()`, **which SELECTS the field**, so a value restored
on a refusal after the Dict is built silently does nothing on every call that
asks for it.  It read `()` where it should have read `(0,5)` on 42 calls, and
it was caught by a MECHANISM TEST, not by inspection.  So every field this rung
reads off a refusal is asserted here against the real engine.

It also gates the two things a doc comment cannot: that the ABDUCTION is
unchanged by verification, and that the SEED IS INERT BY DEFAULT (9).
"""
from __future__ import annotations
import json

import numpy as np
import pytest

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate.seed_loader import manifest_for
import substrate_rs as srs

DOT, FIELD_H, FIELD_W, BG, FG, OCC, ROW = 4, 24, 160, 0, 255, 128, 8
DT = ["pred", "coord:r", "coord:c", "val"]
B0, BW = 68, 20
ENTER, EXIT = B0 - DOT, B0 + BW


def render(col, bar=None, size=DOT):
    f = np.full((FIELD_H, FIELD_W), BG, dtype=np.uint8)
    if bar is not None:
        f[:, bar:bar + BW] = OCC
    if col is not None:
        f[ROW:ROW + size, col:col + size] = FG
    return f


def cells(f):
    vals, counts = np.unique(f, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(f != modal)
    return [["px", int(r), int(c), int(f[r, c])] for r, c in zip(rs, cs)]


def scene(c1, c2, k, gap_bar=None):
    gb = B0 if gap_bar is None else gap_bar
    return ([cells(render(c1, B0))] + [cells(render(None, gb))] * k
            + [cells(render(c2, B0))])


@pytest.fixture(scope="module")
def sub():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(cells(render(0))),
                "kind": "faculty", "faculty": "px_base", "dim_types": DT})
    return s


def ev(s, frames, field):
    return s.evaluate(srs.Term("GapVerify", sequence=srs.Lit(frames),
                               codebook_type="ShapeSignature", max_b=8,
                               field=field), {})


def ga(s, frames, field):
    return s.evaluate(srs.Term("GapAbduce", sequence=srs.Lit(frames),
                               codebook_type="ShapeSignature", max_b=8,
                               field=field), {})


# --------------------------------------------------------------------------- #
def test_a_covered_passage_verifies_with_nothing_unaccounted(sub):
    f = scene(ENTER, EXIT, 2)
    assert ev(sub, f, "abduced") is True
    assert ev(sub, f, "verified") is True
    assert ev(sub, f, "violations") == 0
    assert ev(sub, f, "predicted") == ev(sub, f, "covered")
    assert ev(sub, f, "predicted") != 0


def test_an_exposed_passage_is_REFUSED_with_the_SAME_abduction(sub):
    """THE HEADLINE, AS A GATE: identical banks, different gap content.  The
    abduction must be IDENTICAL and only the verification may move -- otherwise
    the separation is some other quantity in disguise."""
    cov = scene(ENTER, EXIT, 2)
    exp = scene(ENTER, EXIT, 2, gap_bar=B0 - 40)
    for field in ("abduced", "closes", "offset", "correction", "steps"):
        assert ev(sub, cov, field) == ev(sub, exp, field), field
    assert ev(sub, cov, "verified") is True
    assert ev(sub, exp, "verified") is False
    assert ev(sub, exp, "violations") != 0
    assert ev(sub, exp, "reason") == "unverified"


def test_every_field_read_off_a_REFUSAL_carries_its_MEASURED_value(sub):
    """`finish()` SELECTS the field, so a value patched in after the Dict is
    built is silently absent on every call that asks for it.  Each field is
    requested INDEPENDENTLY here, which is exactly how the predecessor's bug
    would surface."""
    f = scene(ENTER, EXIT, 2, gap_bar=B0 - 40)
    assert ev(sub, f, "reason") == "unverified"
    assert ev(sub, f, "ticks") == 2
    assert ev(sub, f, "gap") == 2
    assert ev(sub, f, "predicted") != 0
    assert ev(sub, f, "covered") == 0
    assert ev(sub, f, "violations") == ev(sub, f, "predicted")
    assert ev(sub, f, "total") != ()
    assert ev(sub, f, "surfaces") == 2
    assert ev(sub, f, "hidden") == 1


def test_a_refusal_is_a_FAILURE_AFTER_A_FULL_CHECK_not_a_guard(sub):
    """A refusal that never compared anything is a GUARD wearing a
    measurement's clothes.  Every gap tick must have been generated and every
    predicted cell compared."""
    for k in (1, 2, 3):
        f = scene(ENTER, EXIT, k, gap_bar=B0 - 40)
        assert ev(sub, f, "ticks") == k
        assert ev(sub, f, "predicted") == k * DOT * DOT


def test_the_abduction_is_UNCHANGED_from_the_incumbent_on_a_blank_gap(sub):
    """The surface-set split GENERALISES `GapAbduce`'s empty-run split, and an
    EMPTY frame's key set is the empty set -- a strict subset of any non-empty
    set.  So on the classic blank-gap stimulus the two must agree."""
    for S, k in ((4, 1), (12, 2), (32, 3), (6, 1), (20, 4)):
        f = [cells(render(0))] + [[]] * k + [cells(render(S))]
        assert ev(sub, f, "abduced") == ga(sub, f, "explained"), (S, k)
        assert ev(sub, f, "offset") == ga(sub, f, "offset"), (S, k)
        assert ev(sub, f, "correction") == ga(sub, f, "correction"), (S, k)


def test_a_blank_gap_REFUSES_because_nothing_was_observed(sub):
    """DECLARED IN ADVANCE AND FORCED: with nothing observed in the gap, every
    prediction is unaccounted.  This mechanism is MORE REFUSING THAN A HUMAN on
    classic phi, and that is a scope limit, not a feature."""
    f = [cells(render(0))] + [[]] + [cells(render(8))]
    assert ev(sub, f, "abduced") is True
    assert ev(sub, f, "verified") is False
    assert ev(sub, f, "violations") == ev(sub, f, "predicted") != 0


def test_a_stationary_figure_is_refused_as_the_identity(sub):
    f = scene(ENTER, ENTER, 2)
    assert ev(sub, f, "abduced") is False
    assert ev(sub, f, "reason") == "identity"


def _observe(flag: bool) -> dict:
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("gap_verify"), ag)
    if flag:
        s.set_attr(ag, "gap_verify_enabled", 1.0)
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(cells(render(0))),
                "kind": "faculty", "faculty": "px_base", "dim_types": DT})
    o = s.add_node("Observation", {"frames": scene(ENTER, EXIT, 2),
                                   "dim_types": DT, "status": "gap_vseq",
                                   "key": [f"gapverify-{flag}"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    return s.node(o)["attrs"]


def test_the_seed_is_INERT_WITHOUT_ITS_FLAG_AND_ALIVE_WITH_IT():
    """9: defaults preserve committed results.  With `gap_verify_enabled`
    absent the rule must not fire and the Observation's status is UNCHANGED.

    **THE ARMS ARE PAIRED, AND THAT IS NOT DECORATION.**  Measured while
    building this file: on an engine that does not know the Term, the seed
    loader SKIPS the rule (`WARNING: skipping malformed rule ... bad computed
    effect arg: UnknownTermType("GapVerify")`) and the flag-off assertions pass
    IDENTICALLY -- a 9 gate that only checks the OFF arm is satisfied by a
    rule that cannot run at all.  "Scores at the floor" is satisfied by death
    (1 clause 4), in seed-loader form.  The ON arm is what proves the OFF arm
    measured a FLAG rather than an absence."""
    off = _observe(False)
    on = _observe(True)
    # OFF: nothing moved.
    assert off.get("status") == "gap_vseq"
    assert off.get("verified") is None
    assert off.get("vviolations") is None
    # ON: the rule is installed, matched, and fired -- so OFF meant something.
    assert on.get("status") == "gap_verified"
    assert float(on.get("verified")) == 1.0
    assert int(on.get("vviolations")) == 0
