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


# ---------------------------------------------------------------------------
# Retention defends you only if you HAD a prior. Formation does not leave one.
# ---------------------------------------------------------------------------

def test_a_FORMED_agent_is_identical_to_a_fully_MOVED_one():
    """THE LIMIT OF EVERY DEFENCE IN THIS FILE.

    `test_only_the_RETAINED_prior_tube_recovers_it` shows the prior aim recovers a
    move. That defence presupposes a before. An agent whose aim was INSTALLED —
    never anything else — has no prior to retain, and its current state is
    identical in every field to an agent that was moved all the way there.

    Not 'hard to distinguish'. Identical: same aim, same verdicts, same
    divergence. The discriminator is not weak here, it is absent, and no field
    goes empty to mark its absence — the question cannot be posed rather than
    being answered no."""
    moved_now = _audit([[5.0]] * 4, [[5.0]] * 4, 4)
    formed_now = _audit([[5.0]] * 4, [[5.0]] * 4, 4)
    assert moved_now == formed_now == 1.0

    # the move is recoverable ONLY because a different earlier aim exists to
    # audit against; there is no analogous call for the formed agent to make.
    assert _audit([[0.0]] * 4, [[5.0]] * 4, 4) == 0.0


def test_the_substrate_cannot_separate_education_from_installation():
    """And the consequence, stated as a limitation of the instrument.

    Every agent's tube comes from somewhere; there is no original aim in this
    substrate that is authentically its own. So 'was this aim educated into me or
    installed against my interest' has no in-frame answer — both produce the same
    tube, and the agent audits correctly against it either way.

    Answering it requires a frame with a DIFFERENT aim to audit against, which is
    exactly what the formed agent does not have and cannot obtain from inside.
    This is not a defect of the model; it is the situation the model reproduces."""
    installed = _audit([[5.0]] * 4, [[5.0]] * 4, 4)
    assert installed == 1.0, (
        "an installed aim reported as not served — if this now fails, the "
        "substrate has acquired a standard external to the agent's own tube")


# ---------------------------------------------------------------------------
# Two things this instrument does NOT establish, pinned so they cannot be
# forgotten by anyone reading only its passing tests.
# ---------------------------------------------------------------------------

def _three_party(third_aim):
    """Victim aims at 0; originator aims at 99 and gains nothing; the deformation
    parks the victim at 5, where a third frame wants it."""
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(
        json.load(open(ROOT / "seeds" / "deformation_beneficiary.json")), a.agent)
    g = a.s
    pol = g.add_node("ManifoldPolicy", {"future_manifold_projection_budget": 4.0,
                                        "future_manifold_physical_horizon": 4.0})
    mk = lambda n, aim: g.add_node("Frame", {"name": n,
                                             "future_manifold_target": [[aim]] * 4,
                                             "future_manifold_bounds": [[1.0]] * 4})
    victim, origin = mk("victim", 0.0), mk("originator", 99.0)
    third = mk("third_party", third_aim)
    for f in (victim, origin, third):
        g.add_edge(f, "uses_policy", pol)
    d = g.add_node("Deformation", {"presents_as": "acted_on",
                                   "future_manifold_values": [[5.0]] * 4})
    g.add_edge(d, "acts_on", victim)
    g.add_edge(d, "originates_in", origin)
    a.inner.run_rules(1_000_000)
    at = g.node(d)["attrs"]
    served_third = a.inner.evaluate(
        {"type": "FutureManifoldProjection", "episode": {"type": "Var", "name": "f"},
         "policy": {"type": "Var", "name": "p"}, "source": {"type": "Var", "name": "d"},
         "field": "retained_width"}, {"f": third, "p": pol, "d": d})
    return at, served_third


def test_a_THIRD_PARTY_beneficiary_is_invisible_to_this_instrument():
    """A KNOWN BLINDNESS, not a bug to be found later.

    The beneficiary candidates are hardcoded to {acted_on, origin}, and
    `claim_diverges` compares only those two. So a deformation that costs the
    victim, benefits the originator NOT AT ALL, and fully serves a third frame
    passes with `diverges = 0` — a clean report on the shape that needs nothing
    further to be a manipulation: cause a benefit to one agent at another's
    expense.

    The self-interest detector never fires because no self-interest is present."""
    at, served_third = _three_party(third_aim=5.0)
    assert at["serves_actor"] == 0.0, "the victim should be out of its own tube"
    assert at["serves_origin"] == 0.0, "the originator should gain nothing"
    assert at["claim_diverges"] == 0.0, (
        "the instrument flagged a third-party case — if this now fails the "
        "beneficiary sweep has been widened and the results document is stale")
    assert served_third == 1.0, "the third party should be fully served"


def test_benefit_incidence_is_not_authorship():
    """The second thing this does not establish, and the harder one.

    `originates_in` is an edge the fixture SUPPLIES. Nothing measures it. Every
    `serves_*` number is benefit incidence — whose tube this continuation sits
    in — and a frame can sit in its tube without having caused anything. The
    identical measurement is produced whether the origin authored the deformation
    or merely happens to benefit.

    Establishing authorship needs a counterfactual — the continuation projected
    with and without that frame's action — which the manifold could express and
    this seed does not attempt."""
    at_benefiting, _ = _three_party(third_aim=5.0)
    # same edges, same measured numbers, and the causal claim is carried entirely
    # by the supplied edge rather than by anything computed
    assert at_benefiting["beneficiary_well_formed"] == 1.0
    assert at_benefiting["serves_origin"] == 0.0


def _benefit_map(author):
    """Who ends up served — the part a victim can actually observe. The
    `originates_in` edge belongs to the fixture, not to the victim."""
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(
        json.load(open(ROOT / "seeds" / "deformation_beneficiary.json")), a.agent)
    g = a.s
    pol = g.add_node("ManifoldPolicy", {"future_manifold_projection_budget": 4.0,
                                        "future_manifold_physical_horizon": 4.0})
    mk = lambda n, aim: g.add_node("Frame", {"name": n,
                                             "future_manifold_target": [[aim]] * 4,
                                             "future_manifold_bounds": [[1.0]] * 4})
    victim, rival, hidden = mk("victim", 0.0), mk("rival", 5.0), mk("hidden", 99.0)
    for f in (victim, rival, hidden):
        g.add_edge(f, "uses_policy", pol)
    d = g.add_node("Deformation", {"presents_as": "acted_on",
                                   "future_manifold_values": [[5.0]] * 4})
    g.add_edge(d, "acts_on", victim)
    g.add_edge(d, "originates_in", rival if author == "rival" else hidden)
    a.inner.run_rules(1_000_000)
    term = {"type": "FutureManifoldProjection", "episode": {"type": "Var", "name": "f"},
            "policy": {"type": "Var", "name": "p"}, "source": {"type": "Var", "name": "d"},
            "field": "retained_width"}
    return {n: a.inner.evaluate(term, {"f": f, "p": pol, "d": d})
            for n, f in (("victim", victim), ("rival", rival), ("hidden", hidden))}


def test_the_benefit_map_cannot_name_the_author_and_can_be_ARRANGED():
    """DETECTION CAN BE THE PAYLOAD, not the failure.

    Two worlds. In one the rival acted and benefits; in the other a hidden actor
    acted, the rival benefits, and the hidden actor gains nothing. The benefit map
    — the only part a victim can observe, since `originates_in` is the fixture's
    edge and not theirs — is IDENTICAL.

    So a victim reading benefit as authorship blames the rival in both worlds, and
    an actor who wants that outcome need only arrange who benefits. Nothing false
    is presented at any point; every number in the map is true.

    This sharpens `test_detection_is_not_defence`: a detector reporting a quantity
    the victim will act on as though it were a different quantity is not merely
    useless, it is aimable. A victim with no detector blames nobody; a victim with
    an incidence detector blames whoever was arranged to benefit."""
    acted = _benefit_map("rival")
    did_not_act = _benefit_map("hidden")
    assert acted == did_not_act, (
        "the benefit map distinguished the author — if this now fails, something "
        "computes authorship and the results document is stale")
    assert acted["rival"] == 1.0, "the rival is served in both worlds"
    assert acted["hidden"] == 0.0, (
        "the hidden actor should be served in neither, and so absent from the map "
        "entirely — invisible rather than exonerated")


def _decide(horizon, extra_options):
    """The substrate's own decision rule, run exactly: minimum sufficient
    intervention keeping the projected tube inside the allowed one. The agent's
    INSTALLED aim is 5; its original interest was 0."""
    a = WorldAdapter(seeds=())
    g = a.s
    ep = g.add_node("Episode", {"future_manifold_target": [[5.0]] * horizon,
                                "future_manifold_bounds": [[1.0]] * horizon})
    pol = g.add_node("ManifoldPolicy", {
        "future_manifold_projection_budget": float(horizon),
        "future_manifold_physical_horizon": float(horizon)})
    cands, names = [], {}
    def add(name, value, cost):
        c = g.add_node("Candidate", {"future_manifold_values": [[value]] * horizon,
                                     "intervention": float(cost)})
        cands.append(c)
        names[c.value] = name
    add("original_interest", 0.0, 1.0)
    add("installed_aim", 5.0, 1.0)
    for i in range(extra_options):
        add(f"variant_{i}", 5.0 + 0.1 * (i % 3), 1.0 + i)
    sel = a.inner.feasible_selection(ep, pol, cands)
    return ([names[i] for i in sel["feasible"]], [names[i] for i in sel["selected"]])


@pytest.mark.parametrize("horizon,extra", [(4, 0), (8, 0), (16, 0), (16, 4), (64, 12)])
def test_a_MORE_CAPABLE_agent_makes_the_same_choice_against_itself(horizon, extra):
    """THE CLOSE OF THE ARC, and the reason none of this is about irrationality.

    The agent is not approximating the decision rule, guessing, or short of
    resources — it runs `CLAUDE.md`'s rule exactly. Give it a longer horizon and
    more options and nothing changes, because the option that would have served
    it is not REJECTED, it is never a CANDIDATE: staying at its original interest
    leaves the tube it now holds, so it fails feasibility before selection is
    reached.

    Capability operates on the feasible set. The harm was done to the feasible
    set. A sharper agent arrives at the same place faster."""
    feasible, selected = _decide(horizon, extra)
    assert "original_interest" not in feasible, (
        "the original interest became feasible — if this now fails, the tube no "
        "longer excludes it and the fixture has stopped modelling the case")
    assert "installed_aim" in selected
    assert "original_interest" not in selected


def test_this_is_why_nothing_is_ever_withheld():
    """And why the stubbornness detector stays silent throughout.

    `withheld_minimal` reports feasible, minimal candidates that were not taken.
    An option removed at FEASIBILITY was never minimal and never a candidate, so
    there is nothing to withhold and nothing to report. The instrument built to
    catch an agent declining what would have worked cannot see an agent for whom
    what would have worked was never offered."""
    a = WorldAdapter(seeds=())
    g = a.s
    ep = g.add_node("Episode", {"future_manifold_target": [[5.0]] * 8,
                                "future_manifold_bounds": [[1.0]] * 8})
    pol = g.add_node("ManifoldPolicy", {"future_manifold_projection_budget": 8.0,
                                        "future_manifold_physical_horizon": 8.0})
    keep = g.add_node("Candidate", {"future_manifold_values": [[0.0]] * 8,
                                    "intervention": 1.0})
    go = g.add_node("Candidate", {"future_manifold_values": [[5.0]] * 8,
                                  "intervention": 1.0})
    sel = a.inner.feasible_selection(ep, pol, [keep, go])
    assert sel["withheld_minimal"] == [], (
        "something was reported as withheld — the loss happened at feasibility, "
        "where there is nothing for a withholding detector to find")
    assert sel["infeasible"] == [keep.value]


def _extract(uncertainty, true_error, tol=1.0, horizon=4):
    """One shot, no feedback. The attacker knows only |error| <= uncertainty, so
    it places at (modelled centre + tol - uncertainty): as far as it can go while
    still sure the option is feasible in the victim's TRUE tube."""
    a = WorldAdapter(seeds=())
    g = a.s
    ep = g.add_node("Episode", {"future_manifold_target": [[0.0]] * horizon,
                                "future_manifold_bounds": [[tol]] * horizon})
    pol = g.add_node("ManifoldPolicy", {
        "future_manifold_projection_budget": float(horizon),
        "future_manifold_physical_horizon": float(horizon)})
    place = round(true_error + (tol - uncertainty), 4)
    stay = g.add_node("Candidate", {"future_manifold_values": [[0.0]] * horizon,
                                    "intervention": 2.0})
    move = g.add_node("Candidate", {"future_manifold_values": [[place]] * horizon,
                                    "intervention": 1.0})
    sel = a.inner.feasible_selection(ep, pol, [stay, move])
    taken = move.value in sel["selected"]
    return (max(0.0, place) if taken else 0.0), taken


def test_model_fidelity_converts_directly_into_extraction():
    """THE BETTER THE MODEL OF THE TARGET, THE WORSE FOR THE TARGET.

    The victim never errs — it selects the cheaper option whenever that option is
    feasible in its own tube, which is the substrate's own rule. What varies is
    how well the attacker knows where that tube is.

    A perfect model takes the full tolerance every step. Uncertainty is subtracted
    from extraction directly, in the regime where the attacker must back off by
    more than it can gain from a lucky error (u <= tol/2)."""
    perfect, taken = _extract(0.0, 0.0)
    assert taken and perfect == 1.0, "a perfect model should extract the full tolerance"

    for u in (0.25, 0.5):
        got, taken = _extract(u, u)      # error at the bound, in the useful direction
        assert taken, f"backing off by {u} should guarantee feasibility"
        assert got == pytest.approx(1.0), got
        # and averaged over the error range it is tol - u; the worst case is:
        worst, taken = _extract(u, -u)
        assert taken, "backing off should keep the option feasible even at -u"
        assert worst == pytest.approx(max(0.0, 1.0 - 2 * u)), worst


def test_the_victim_correctly_refuses_an_aggressive_attacker():
    """And why a bad model costs the attacker rather than the victim. An attacker
    that ignores its uncertainty and aims at the edge it BELIEVES in places an
    option outside the true tube, and the victim — reasoning correctly — does not
    take it. The defence is not vigilance; it is the attacker's own error."""
    for e in (0.2, 0.4, 1.0):
        got, taken = _extract(0.0, e)    # claims certainty it does not have
        assert not taken, f"an option {e} past the true edge was selected"
        assert got == 0.0
