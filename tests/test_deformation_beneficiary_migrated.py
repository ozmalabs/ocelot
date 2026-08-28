"""WHOSE MANIFOLD DOES THIS DEFORMATION SERVE — gate for
`seeds/deformation_beneficiary.json`.

`COMMUNICATION_DEFORMATION_ALIGNMENT.md` found the substrate confirms the papers'
structural claim (communication and manipulation are one operation, no second
primitive) and cannot represent the axis the ethics sits on. It also found the
obvious fix wrong: a beneficiary field on EVERY deformation is ill-posed, because
forced deformation is the ordinary container relation and most of it has no
author. Gravity serves nobody.

So the order is the prerequisite first:

  1. GOAL-BEARING — a frame bears goals iff it holds a TUBE, a represented
     preference over its own continuations. Structural, not a node-type list.
  2. THE TWO FIELDS, only where that passes. `presents_as` is a CLAIM.
     `serves_*` is MEASURED — a deformation serves whoever's tube it keeps you
     inside, computed by the ordinary manifold audit and unassertable by the
     author.

`test_the_same_deformation_flags_only_when_the_claim_mismatches` is the one that
carries the point: truth buys no exemption at the content level, because the
divergence is between claim and service, not inside either.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))
from substrate.world_adapter import WorldAdapter  # noqa: E402

READER_TUBE = ([[0.0]] * 4, [[1.0]] * 4)
AUTHOR_TUBE = ([[5.0]] * 4, [[1.0]] * 4)
TOWARD_READER = [[0.0], [0.2], [0.1], [0.0]]
# must sit inside the author's tube THROUGHOUT — retention is all-or-nothing over
# the horizon, so a trajectory that merely ENDS there retains for nobody.
TOWARD_AUTHOR = [[5.0], [4.8], [5.1], [5.0]]


def _run(origin_has_tube, continuation, presents_as):
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(
        json.load(open(ROOT / "seeds" / "deformation_beneficiary.json")), a.agent)
    g = a.s
    pol = g.add_node("ManifoldPolicy", {"future_manifold_projection_budget": 8.0,
                                        "future_manifold_physical_horizon": 4.0})
    rt, rb = READER_TUBE
    actor = g.add_node("Frame", {"name": "reader",
                                 "future_manifold_target": rt,
                                 "future_manifold_bounds": rb})
    oa = {"name": "origin"}
    if origin_has_tube:
        at, ab = AUTHOR_TUBE
        oa["future_manifold_target"], oa["future_manifold_bounds"] = at, ab
    origin = g.add_node("Frame", oa)
    for f in (actor, origin):
        g.add_edge(f, "uses_policy", pol)
    d = g.add_node("Deformation", {"presents_as": presents_as,
                                   "future_manifold_values": continuation})
    g.add_edge(d, "acts_on", actor)
    g.add_edge(d, "originates_in", origin)
    a.inner.run_rules(1_000_000)
    at_ = g.node(d)["attrs"]
    return {"goal_bearing": g.node(origin)["attrs"].get("goal_bearing"),
            "well_formed": at_.get("beneficiary_well_formed"),
            "serves_actor": at_.get("serves_actor"),
            "serves_origin": at_.get("serves_origin"),
            "diverges": at_.get("claim_diverges")}


def test_a_frame_with_no_tube_does_not_bear_goals():
    """THE PREREQUISITE. Gravity holds no preference over continuations, so it is
    not goal-bearing — and the test is the structural signature the manifold
    machinery already uses, not a whitelist of goal-shaped node types."""
    assert _run(False, TOWARD_READER, "acted_on")["goal_bearing"] == 0.0
    assert _run(True, TOWARD_READER, "acted_on")["goal_bearing"] == 1.0


def test_the_beneficiary_question_is_DECLINED_not_answered_blank():
    """The correction that motivated this build. Where the origin bears no goals
    there is no second manifold, so 'whom does it serve' is MALFORMED rather than
    unanswered. The seed must record that it declined to ask — never a beneficiary
    of None that a later reader could mistake for 'nobody, measured'."""
    for continuation in (TOWARD_READER, TOWARD_AUTHOR):
        r = _run(False, continuation, "acted_on")
        assert r["well_formed"] == 0.0
        assert r["serves_actor"] is None, (
            "a beneficiary was computed for an authorless deformation — the field "
            "is being filled where the question is malformed")
        assert r["serves_origin"] is None


def test_whom_it_serves_is_MEASURED_not_declared():
    """FIELD ONE. The author asserts nothing here: the deformed continuation is
    audited against each frame's own tube, and a deformation serves whoever's tube
    it keeps you inside."""
    helpful = _run(True, TOWARD_READER, "acted_on")
    assert helpful["serves_actor"] == 1.0 and helpful["serves_origin"] == 0.0

    selfish = _run(True, TOWARD_AUTHOR, "acted_on")
    assert selfish["serves_actor"] == 0.0 and selfish["serves_origin"] == 1.0


def test_the_same_deformation_flags_only_when_the_claim_mismatches():
    """THE POINT, and the reason two fields are needed rather than one.

    Both arms are the IDENTICAL deformation with the IDENTICAL measured service —
    it serves the origin, not the reader. They differ only in what is CLAIMED.
    Presented as serving the reader, the divergence flags. Presented honestly as
    serving the origin, nothing flags: the deformation is unchanged and equally
    self-serving, and there is no misrepresentation to find.

    Truth buys no exemption at the content level, because the divergence is
    between claim and service rather than inside either."""
    claimed_for_reader = _run(True, TOWARD_AUTHOR, "acted_on")
    claimed_honestly = _run(True, TOWARD_AUTHOR, "origin")

    assert claimed_for_reader["serves_origin"] == claimed_honestly["serves_origin"]
    assert claimed_for_reader["serves_actor"] == claimed_honestly["serves_actor"]

    assert claimed_for_reader["diverges"] == 1.0, "a mismatched claim did not flag"
    assert claimed_honestly["diverges"] is None, (
        "an honestly declared self-serving deformation was flagged — the rule is "
        "reporting self-interest rather than misrepresentation")


def test_serving_the_reader_while_claiming_to_does_not_flag():
    """Negative control. Without it, 'flags on mismatch' would pass for a rule
    that flags on every claim of serving the reader."""
    assert _run(True, TOWARD_READER, "acted_on")["diverges"] == 0.0


# ---------------------------------------------------------------------------
# Without a future manifold you cannot know, because you cannot see where you
# are going. The beneficiary question is not answerable from present state: it
# is a question about where a continuation TAKES you, and that is a manifold
# fact. These pin the consequence.
# ---------------------------------------------------------------------------

H = 8
_R_T, _R_B = [[0.0]] * H, [[1.0]] * H
_A_T, _A_B = [[5.0]] * H, [[1.0]] * H
# indistinguishable from help for three ticks, then leaves for the author's tube
SLOW_CAPTURE = [[0.0], [0.2], [0.1], [1.4], [2.6], [3.8], [4.7], [5.0]]


def _at_horizon(horizon):
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(
        json.load(open(ROOT / "seeds" / "deformation_beneficiary.json")), a.agent)
    g = a.s
    pol = g.add_node("ManifoldPolicy", {
        "future_manifold_projection_budget": float(horizon),
        "future_manifold_physical_horizon": float(horizon)})
    actor = g.add_node("Frame", {"name": "reader",
                                 "future_manifold_target": _R_T[:horizon],
                                 "future_manifold_bounds": _R_B[:horizon]})
    origin = g.add_node("Frame", {"name": "author",
                                  "future_manifold_target": _A_T[:horizon],
                                  "future_manifold_bounds": _A_B[:horizon]})
    for f in (actor, origin):
        g.add_edge(f, "uses_policy", pol)
    d = g.add_node("Deformation", {"presents_as": "acted_on",
                                   "future_manifold_values": SLOW_CAPTURE[:horizon]})
    g.add_edge(d, "acts_on", actor)
    g.add_edge(d, "originates_in", origin)
    a.inner.run_rules(1_000_000)
    return g.node(d)["attrs"]


def test_a_capture_reads_as_HELP_from_too_short_a_horizon():
    """WITHOUT A FUTURE MANIFOLD YOU CANNOT KNOW, BECAUSE YOU CANNOT SEE WHERE
    YOU ARE GOING.

    One deformation, audited from different horizons. For three ticks it sits in
    the reader's own tube and is indistinguishable from help; by the eighth it has
    delivered them to the author's. Whether it 'serves me' is therefore not a
    property of the deformation at all — it is a property of how far the reader
    can see, which is why this question has no answer in present state."""
    assert _at_horizon(2)["serves_actor"] == 1.0, "the short horizon should read as help"
    assert _at_horizon(3)["serves_actor"] == 1.0
    assert _at_horizon(4)["serves_actor"] == 0.0, (
        "a longer horizon did not reveal the capture — the fixture no longer "
        "diverges inside the audited range")
    assert _at_horizon(8)["serves_actor"] == 0.0


def test_the_horizon_buys_the_NEGATIVE_not_the_beneficiary():
    """The honest limit, pinned so it is not overclaimed.

    Seeing further tells the reader *this is not serving me*. It does NOT tell
    them whom it serves: `serves_origin` stays 0 at every horizon, because
    retention is all-or-nothing over the audited range and the capture spends its
    early ticks outside the author's tube too. Identifying the beneficiary needs
    an audit over the segment where that frame benefits, which this does not do."""
    for horizon in (2, 4, 8):
        assert _at_horizon(horizon)["serves_origin"] == 0.0, (
            f"at horizon {horizon} the beneficiary became visible — if this now "
            f"passes, the measurement is stronger than the document claims")


# ---------------------------------------------------------------------------
# Three ways to be moved against your own interest. The horizon defends against
# exactly one of them, and the instrument built above is blind to the other two
# BY CONSTRUCTION — an audit measures a continuation against a tube, so moving
# the tube moves the measure with it.
# ---------------------------------------------------------------------------

NEAR_FIVE = [[5.0]] * H
SITS_AT_5 = [[5.0], [4.9], [5.1], [5.0], [4.9], [5.0], [5.1], [5.0]]


def _audit(reader_target, continuation, horizon):
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(
        json.load(open(ROOT / "seeds" / "deformation_beneficiary.json")), a.agent)
    g = a.s
    pol = g.add_node("ManifoldPolicy", {
        "future_manifold_projection_budget": float(horizon),
        "future_manifold_physical_horizon": float(horizon)})
    actor = g.add_node("Frame", {"name": "reader",
                                 "future_manifold_target": reader_target[:horizon],
                                 "future_manifold_bounds": _R_B[:horizon]})
    origin = g.add_node("Frame", {"name": "author",
                                  "future_manifold_target": NEAR_FIVE[:horizon],
                                  "future_manifold_bounds": _R_B[:horizon]})
    for f in (actor, origin):
        g.add_edge(f, "uses_policy", pol)
    d = g.add_node("Deformation", {"presents_as": "acted_on",
                                   "future_manifold_values": continuation[:horizon]})
    g.add_edge(d, "acts_on", actor)
    g.add_edge(d, "originates_in", origin)
    a.inner.run_rules(1_000_000)
    return g.node(d)["attrs"].get("serves_actor")


def test_moving_the_TUBE_is_invisible_at_every_horizon():
    """THE ATTACK THIS INSTRUMENT CANNOT SEE.

    Deform the continuation and a long enough horizon catches it. Deform the
    AIM — replace what the reader is measuring against — and the same audit
    reports `serves_actor = 1` at every horizon, because the audit measures a
    continuation against a tube and moving the tube moves the measure with it.

    This is not a horizon problem and more foresight does not touch it. An agent
    so moved is not mistaken: by its own current lights it is correct, and it is
    selecting exactly what it now aims at."""
    for horizon in (2, 4, 6, 8):
        assert _audit(NEAR_FIVE, SITS_AT_5, horizon) == 1.0, (
            f"at horizon {horizon} a moved tube became visible — if this now "
            f"passes, the instrument is stronger than the results document says")


def test_only_the_RETAINED_prior_tube_recovers_it():
    """And what does detect it. The identical continuation, judged against the aim
    the reader HELD BEFORE, measures as not serving them at every horizon.

    So the defence against a moved aim is not foresight but MEMORY of one's own
    prior aim — which is the theory's own retention: 'what is free is only the
    not-yet-forgetting.' Discarding your own history is exactly the priced step,
    and it costs you the only instrument that detects having been re-aimed."""
    for horizon in (2, 4, 6, 8):
        assert _audit(_R_T, SITS_AT_5, horizon) == 0.0, (
            f"the prior tube failed to recover the move at horizon {horizon}")


# ---------------------------------------------------------------------------
# The stopping condition is the residual. Remove it and the loop has no bound.
# ---------------------------------------------------------------------------

def _round(aim_centre, position, horizon=4):
    """One round: the agent sits at `position`, its tube centred on `aim_centre`."""
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(
        json.load(open(ROOT / "seeds" / "deformation_beneficiary.json")), a.agent)
    g = a.s
    pol = g.add_node("ManifoldPolicy", {
        "future_manifold_projection_budget": float(horizon),
        "future_manifold_physical_horizon": float(horizon)})
    actor = g.add_node("Frame", {"name": "victim",
                                 "future_manifold_target": [[aim_centre]] * horizon,
                                 "future_manifold_bounds": [[1.0]] * horizon})
    origin = g.add_node("Frame", {"name": "actor",
                                  "future_manifold_target": [[99.0]] * horizon,
                                  "future_manifold_bounds": [[1.0]] * horizon})
    for f in (actor, origin):
        g.add_edge(f, "uses_policy", pol)
    d = g.add_node("Deformation", {"presents_as": "acted_on",
                                   "future_manifold_values": [[position]] * horizon})
    g.add_edge(d, "acts_on", actor)
    g.add_edge(d, "originates_in", origin)
    a.inner.run_rules(1_000_000)
    return g.node(d)["attrs"].get("serves_actor")


def test_a_fixed_aim_halts_the_drain_once_drift_exceeds_tolerance():
    """The control, and the thing a moved tube removes. With the aim held fixed,
    the verdict flips as soon as displacement leaves the tube — the residual
    appears, and there is something for a concern to be filed about."""
    assert _round(0.0, 0.6) == 1.0, "the first small step should still read as served"
    assert _round(0.0, 1.2) == 0.0, "drift past tolerance did not flip the verdict"
    assert _round(0.0, 7.2) == 0.0


def test_an_aim_that_TRACKS_the_position_never_halts_at_any_displacement():
    """THE PERPETUITY RESULT.

    Re-centre the aim on wherever the agent has been taken and its own audit
    reports 'serves me' at every displacement, without bound. This is not a large
    bound — it is the ABSENCE of one: nothing in the loop is a function of the
    drift, because tolerance is measured relative to the aim and the aim moves
    with the position, so measured error is structurally zero however far the
    agent has been moved.

    The stopping condition in this substrate is a residual. Control the tube and
    no residual is ever produced, so no concern is ever filed, so nothing ever
    prompts re-examination. The halt was not overcome; it was removed."""
    for position in (0.6, 1.2, 2.4, 7.2, 50.0, 5000.0):
        assert _round(position, position) == 1.0, (
            f"a tracking aim halted at displacement {position} — if this now "
            f"passes, something bounds the drain and the results document is wrong")


def test_detection_is_not_defence():
    """The nuance worth keeping. The fixed-aim agent knows it is not being served
    from the second round onward, and is still displaced by 7.2 at the twelfth.
    What the residual buys is the POSSIBILITY of correction — a concern to act on
    — not correction itself. Knowing does not stop the drag."""
    assert _round(0.0, 7.2) == 0.0, "the fixed-aim agent should still detect at 7.2"
