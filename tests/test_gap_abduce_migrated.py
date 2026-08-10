"""`GapAbduce` -- THE ENDPOINT-ABDUCED GENERATOR, gated.

The operator the timephi rung (93000-93999) measured the substrate to lack:
every temporal mechanism here infers `G` from a CONSECUTIVE VISIBLE PAIR and
EXTRAPOLATES (CONTINUATION), and a phi stimulus supplies exactly ONE pre-gap
sample -- so `BlinkBridge` correctly FREEZES.  This Term solves
`G^(gap+1)(f_before) = f_after` for `G` from the TWO ENDPOINTS ALONE
(INTERPOLATION), admitted by a DIVISIBILITY test with no threshold in it.

The vacuity gate (PROTOCOL 1 clause 5) runs FIRST: a mechanism must be shown to
MOVE SOMETHING DOWNSTREAM before its statistics mean anything.
"""
from __future__ import annotations
import json

import numpy as np
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.boot_core import boot_core            # noqa: E402
from domains import reflective_faculty as rf          # noqa: E402
from substrate.seed_loader import manifest_for        # noqa: E402
import substrate_rs as srs                            # noqa: E402

DOT, ROW, H, W, BG, FG = 4, 8, 24, 160, 0, 255
DT = ["pred", "coord:r", "coord:c", "val"]


def cells(col, size=DOT):
    if col is None:
        return []
    f = np.full((H, W), BG, dtype=np.uint8)
    f[ROW:ROW + size, col:col + size] = FG
    vals, counts = np.unique(f, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(f != modal)
    return [["px", int(r), int(c), int(f[r, c])] for r, c in zip(rs, cs)]


def seq(cols):
    return [cells(c) for c in cols]


def phi(S, k):
    """THE PHI TOPOLOGY: one pre-gap sample, k blanks, one resumed sample."""
    return seq([0] + [None] * k + [S])


@pytest.fixture(scope="module")
def sub():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    native.load_seed_manifest(manifest_for("gap_abduce"), ag)
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(cells(0)),
                "kind": "faculty", "faculty": "px_base", "dim_types": DT})
    return s, ag, native


def ev(sub, frames, field):
    s, _, _ = sub
    return s.evaluate(srs.Term("GapAbduce", sequence=srs.Lit(frames),
                               codebook_type="ShapeSignature", max_b=8,
                               field=field), {})


# --------------------------------------------------------------------------- #
#  PROTOCOL 1 clause 5 -- THE VACUITY GATE, RUN FIRST
# --------------------------------------------------------------------------- #
def test_the_mechanism_MOVES_SOMETHING_DOWNSTREAM(sub):
    """Toggle the flag; measure `max|on - off|` on every attribute the rule
    claims to write.  `D == 0.0` exactly would mean the subsystem is
    DECORATIVE -- correct, gated, tested, and wired to nothing.  FM-0 found
    exactly that in an afternoon, after nine pre-registrations did not."""
    _, _, _ = sub
    moved = {}
    for flag in (0.0, 1.0):
        s, ag = boot_core()
        native = rf._native_eval2(s)
        rf._ensure_shape_decode_loop(s, native, ag)
        native.load_seed_manifest(manifest_for("time_axis"), ag)
        native.load_seed_manifest(manifest_for("gap_abduce"), ag)
        s.set_attr(ag, "gap_abduce_enabled", flag)
        s.add_node("ShapeSignature",
                   {"name": "px_base", "signature": json.dumps(cells(0)),
                    "kind": "faculty", "faculty": "px_base", "dim_types": DT})
        o = s.add_node("Observation", {"frames": phi(4, 1), "dim_types": DT,
                                       "status": "gap_seq", "key": ["vac"]})
        s.add_edge(ag, "observed", o)
        native.run_rules()
        moved[flag] = s.node(o)["attrs"]

    on, off = moved[1.0], moved[0.0]
    assert off.get("status") == "gap_seq", "OFF must be inert (PROTOCOL 9)"
    assert on.get("status") == "gap_abduced"
    changed = [k for k in ("abduced", "closes", "abduce_offset", "abduce_reason",
                           "abduce_correction", "status")
               if on.get(k) != off.get(k)]
    assert changed, "D == 0 exactly: the mechanism is DECORATIVE"
    assert float(on.get("abduced")) == 1.0


def test_default_is_OFF_so_every_committed_result_reproduces(sub):
    """PROTOCOL 9: the flag is absent unless a caller sets it."""
    s, ag = boot_core()
    assert not s.node(ag)["attrs"].get("gap_abduce_enabled")


# --------------------------------------------------------------------------- #
#  the mechanism
# --------------------------------------------------------------------------- #
def test_the_phi_topology_CLOSES_where_BlinkBridge_froze(sub):
    """THE CAPABILITY.  One pre-gap sample, a gap, a resumed sample: the gap
    closes EXACTLY.  `BlinkBridge` at this identical topology reports
    kind='freeze', confidence 0.00 and correction 32 (the dot's 16 cells
    counted twice) -- measured by the timephi rung, 16/16."""
    assert ev(sub, phi(4, 1), "explained") is True
    assert ev(sub, phi(4, 1), "prefix_len") == 1
    assert ev(sub, phi(4, 1), "offset") == (0, 2)
    assert ev(sub, phi(4, 1), "closes") is True
    assert ev(sub, phi(4, 1), "correction") == 0
    # and the CONTRAST, on the SAME stimulus, from the incumbent operator
    bb = srs.Term("BlinkBridge", sequence=srs.Lit(phi(4, 1)),
                  codebook_type="ShapeSignature", max_b=8, field="kind")
    s, _, _ = sub
    assert s.evaluate(bb, {}) == "freeze"


def test_the_divisibility_test_is_EXACT_in_both_directions(sub):
    """Closes IFF (gap+1) divides the displacement.  A biconditional, checked
    both ways -- a mechanism that only ever accepts has no aperture the way a
    stopped clock has no error."""
    for S, k, want in [(4, 1, True), (5, 1, False), (16, 3, True),
                       (16, 2, False), (12, 2, True), (12, 4, False),
                       (32, 7, True), (32, 4, False)]:
        assert ev(sub, phi(S, k), "explained") is want, (S, k)
        assert ev(sub, phi(S, k), "divisible") is want, (S, k)


def test_an_indivisible_gap_reports_a_DIAGNOSABLE_reason(sub):
    """A null must say WHY.  `reason` separates the refusals by kind, and the
    measured endpoint displacement survives on the refusal -- an indivisible D
    is a NUMBER, not an absence."""
    assert ev(sub, phi(5, 1), "reason") == "indivisible"
    assert ev(sub, phi(5, 1), "total") == (0, 5)


def test_the_identity_is_refused(sub):
    """A still figure is not a motion -- the same exclusion `TimeInfer`
    applies at source."""
    assert ev(sub, seq([0, None, 0]), "explained") is False
    assert ev(sub, seq([0, None, 0]), "reason") == "identity"


def test_a_non_translate_pair_is_refused(sub):
    """Endpoints that are not rigid translates of one another.  FORCED by the
    cardinality check in `infer_translate_offset` -- asserted to confirm the
    source reading against the REAL ENGINE, which is the thing a doc comment
    failed at this week."""
    frames = [cells(0, DOT), [], cells(20, DOT + 1)]
    assert ev(sub, frames, "explained") is False
    assert ev(sub, frames, "reason") == "not_rigid"


def test_the_abduced_intermediates_are_EMITTED_and_land_on_the_lattice(sub):
    """The gap is FILLED, not merely judged: `bridged` carries `G^t(f_before)`
    for each gap tick, and each is a real frame of the right cardinality."""
    br = ev(sub, phi(16, 3), "bridged")
    assert len(br) == 3
    assert all(len(f) == DOT * DOT for f in br)


def test_gap_zero_is_the_DEGENERATE_case_not_a_refusal(sub):
    """ISI = 0: an all-visible pair, `steps == 1`, everything divisible by 1.
    This is the point at which the abduction reduces EXACTLY to the two-frame
    reading `TimeInfer` already explains vacuously (9/9), and keeping it on the
    SAME operator is what makes the ISI curve's zero point measurable rather
    than spliced in from a different mechanism."""
    assert ev(sub, seq([0, 7]), "explained") is True
    assert ev(sub, seq([0, 7]), "steps") == 1
    assert ev(sub, seq([0, 7]), "offset") == (0, 7)


def test_it_has_NO_DISCRIMINATIVE_POWER_on_the_translate_class(sub):
    """THE SCOPE LIMIT, ASSERTED RATHER THAN BURIED.  Any two same-shape
    figures ARE rigid translates, so divisibility is the ONLY constraint and an
    ARBITRARY pair of positions is accepted whenever the difference divides.
    `TimeInfer` at N>=3 refuses ACCEL and SHUFFLE 18/18 because a THIRD frame
    CONSTRAINS the orbit; two endpoints and one free generator always fit."""
    # an arbitrary, unmotivated pair -- accepted purely because 2 divides 66
    assert ev(sub, seq([13, None, 79]), "explained") is True
    assert ev(sub, seq([13, None, 79]), "offset") == (0, 33)
