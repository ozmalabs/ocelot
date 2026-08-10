"""SURPRISE PROMOTES — the migrated gate (EFFECTOR_AUTHORITY_COLLAPSE_PREREG.md).

Three cases, ONE mechanism, no rule that knows what any of them is:

  hand/desk  a channel no goal is using promotes on contact and can yield
  wall       a channel the goal needs promotes and the spend is affordable
  falling    a projected crossing promotes limbs BEFORE contact

The gates that matter most are the negative ones: that a dark channel promotes
NOTHING (blindness is not a decision), that damage alone can promote an
effector whose goal relevance is at the floor (it is not zero), and that no
rule reduces the axes to a scalar before the collapse sees them.
"""
import json
from pathlib import Path

from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.gen_energy_ledger_seed import manifest as ledger_manifest   # noqa: E402
from scripts.gen_surprise_promotion_seed import (                      # noqa: E402
    LATTICE_STEP_UNITS, STREAM_HORIZON_UNITS, manifest,
)
from substrate.seed_loader import manifest_for                           # noqa: E402
from substrate.world_adapter import WorldAdapter                         # noqa: E402


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _agent():
    agent = WorldAdapter()
    for seed in ("counterfactual_experiment", "embodied_learning_session",
                 "embodied_development"):
        agent.inner.load_seed_manifest(manifest_for(seed), agent.agent)
    agent.inner.load_seed_manifest(ledger_manifest(), agent.agent)
    agent.inner.load_seed_manifest(manifest(), agent.agent)
    return agent


def _episode(agent):
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    agent.inner.run_rules()
    return episode


def _effector(agent, episode, **attrs):
    base = {"goal_relevance_units": 0, "release_cost_units": 1,
            "recoverability_units": 5}
    base.update(attrs)
    effector = agent.s.add_node("EmbodiedEffector", base)
    _edge(agent, episode, "has_embodied_effector", effector)
    return effector


def _channel(agent, effector, **attrs):
    base = {"channel": "contact_force", "declared_units": 0,
            "tolerance_units": 1, "damage_units": 0, "predict_horizon_units": 8}
    base.update(attrs)
    channel = agent.s.add_node("SensedChannel", base)
    _edge(agent, effector, "has_sensed_channel", channel)
    return channel


def _observe(agent, channel, value):
    node = agent.s.add_node("ChannelObservation", {"value_units": value})
    _edge(agent, channel, "has_channel_observation", node)
    return node


def _expect(agent, channel, value):
    node = agent.s.add_node("ChannelExpectation", {"value_units": value})
    _edge(agent, channel, "has_channel_expectation", node)
    return node


def _project(agent, channel, *, crossing, order_fit=1):
    node = agent.s.add_node("TemporalProjection", {
        "crossing": crossing, "order_fit": order_fit, "source": "time_infer"})
    _edge(agent, channel, "has_temporal_projection", node)
    return node


def _candidate_nodes(agent, effector):
    return list(agent.inner.neighbours(effector, "has_promoted_candidate"))


def _candidates(agent, effector):
    return [agent.s.node(c)["attrs"]
            for c in _candidate_nodes(agent, effector)]


# ------------------------------------------------------------- resolution

def test_a_reading_beats_an_expectation_and_says_so():
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector)
    _expect(agent, channel, 0)
    _observe(agent, channel, 7)
    agent.inner.run_rules()
    attrs = agent.s.node(channel)["attrs"]
    assert attrs["value_units"] == 7
    assert attrs["provenance"] == "measured"
    assert attrs["measured"] == 1


def test_we_expect_to_turn_so_we_assume_we_have():
    """No reading: the efference copy stands in, flagged as an assumption."""
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, channel="torso_orientation")
    _expect(agent, channel, 90)
    agent.inner.run_rules()
    attrs = agent.s.node(channel)["attrs"]
    assert attrs["value_units"] == 90
    assert attrs["provenance"] == "expected"
    assert attrs["measured"] == 0


def test_no_information_is_declared_not_a_silent_zero():
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, declared_units=3)
    agent.inner.run_rules()
    attrs = agent.s.node(channel)["attrs"]
    assert attrs["value_units"] == 3
    assert attrs["provenance"] == "declared"
    assert attrs["measured"] == 0


# ------------------------------------------------------------ the three cases

def test_desk_a_channel_no_goal_is_using_promotes_on_contact():
    """Turning; the hand meets a desk. Goal relevance is at the floor."""
    agent = _agent()
    effector = _effector(agent, _episode(agent), goal_relevance_units=0)
    channel = _channel(agent, effector, damage_units=9)
    _expect(agent, channel, 0)          # the hand should sweep free space
    _observe(agent, channel, 40)        # it did not
    agent.inner.run_rules()
    promoted = _candidates(agent, effector)
    assert len(promoted) == 1
    assert promoted[0]["route"] == "detected"
    assert promoted[0]["surprise_units"] == 40
    # It promoted with goal relevance at zero — the whole point.
    assert promoted[0]["goal_relevance_units"] == 0
    assert promoted[0]["damage_units"] == 9


def test_falling_promotes_before_contact_from_a_projected_crossing():
    """Route (b): anticipation, not reaction. No observation exists at all."""
    agent = _agent()
    effector = _effector(agent, _episode(agent), goal_relevance_units=0)
    channel = _channel(agent, effector, channel="support_height")
    _project(agent, channel, crossing=3, order_fit=2)
    agent.inner.run_rules()
    promoted = _candidates(agent, effector)
    assert len(promoted) == 1
    assert promoted[0]["route"] == "predicted"
    # Nothing was observed and nothing was contacted.
    assert not agent.inner.neighbours(channel, "has_channel_observation")
    # Urgency is read off the clock: horizon 8, crossing 3 -> 5.
    assert promoted[0]["urgency_units"] == 5


def test_a_nearer_crossing_is_more_urgent_without_any_authored_constant():
    agent = _agent()
    episode = _episode(agent)
    near = _effector(agent, episode)
    far = _effector(agent, episode)
    _project(agent, _channel(agent, near, channel="a"), crossing=1)
    _project(agent, _channel(agent, far, channel="b"), crossing=7)
    agent.inner.run_rules()
    assert (_candidates(agent, near)[0]["urgency_units"]
            > _candidates(agent, far)[0]["urgency_units"])


def test_wall_a_goal_relevant_spend_is_affordable_when_the_ledger_covers_it():
    agent = _agent()
    episode = _episode(agent)
    effector = _effector(agent, episode, goal_relevance_units=10,
                         release_cost_units=20)
    channel = _channel(agent, effector, channel="obstruction")
    _project(agent, channel, crossing=2)
    agent.inner.run_rules()
    promoted = _candidates(agent, effector)[0]
    assert promoted["goal_relevance_units"] == 10
    assert promoted["affordable"] == 1


def test_a_catch_you_cannot_afford_is_marked_unaffordable_not_hidden():
    agent = _agent()
    episode = _episode(agent)
    ledger = agent.inner.neighbours(episode, "has_energy_ledger")[0]
    agent.inner.set_attr(ledger, "opening_units", 4)
    agent.inner.run_rules()
    effector = _effector(agent, episode, release_cost_units=10_000)
    _project(agent, _channel(agent, effector), crossing=1)
    agent.inner.run_rules()
    promoted = _candidates(agent, effector)[0]
    assert promoted["affordable"] == 0
    # Refused, but legible — the collapse can still see it and say why.
    assert promoted["ledger_stock_units"] < promoted["energy_cost_units"]


# ------------------------------------------------------------ the negatives

def test_a_dark_channel_promotes_nothing():
    """Blindness is not a decision.

    No observation, no expectation, no projection: nothing can be surprising,
    so nothing promotes and the effector is never rescued. This is exactly the
    live humanoid's state — `state_support_*_force` and
    `time_to_contact_seconds` read in the hundreds and written zero times.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector)
    agent.inner.run_rules()
    assert _candidates(agent, effector) == []
    assert not agent.inner.neighbours(channel, "has_surprise")
    # It still resolved, and honestly.
    assert agent.s.node(channel)["attrs"]["provenance"] == "declared"


def test_an_expectation_met_is_not_surprising():
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector)
    _expect(agent, channel, 12)
    _observe(agent, channel, 12)
    agent.inner.run_rules()
    assert _candidates(agent, effector) == []


def test_promotion_is_idempotent_under_a_re_run_fixpoint():
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector)
    _expect(agent, channel, 0)
    _observe(agent, channel, 30)
    for _ in range(5):
        agent.inner.run_rules()
    assert len(_candidates(agent, effector)) == 1


def test_no_rule_reduces_the_axes_to_a_scalar():
    """The axes must reach the collapse separately.

    A `score`, `priority`, `weight` or `utility` attribute minted on the
    candidate would mean this seed picked a winner, which is not its job.
    """
    seed = json.loads((Path(__file__).resolve().parents[1] /
                       "seeds" / "surprise_promotion.json").read_text())
    minted = [e[3] for rule in seed["rules"] for e in rule["effects"]
              if e[0] == "add_node" and e[2] == "PromotedCandidate"]
    assert minted, "no candidate is minted at all"
    for attrs in minted:
        for banned in ("score", "priority", "weight", "utility", "rank", "value"):
            assert banned not in attrs, f"{banned!r} scalarises the axes"
        for axis in ("goal_relevance_units", "urgency_units", "damage_units",
                     "energy_cost_units", "recoverability_units"):
            assert axis in attrs, f"missing axis {axis}"


def test_no_rule_knows_what_a_fall_or_a_desk_or_a_wall_is():
    """A case-specific handler anywhere is a design failure, not a feature.

    Scans the EXECUTABLE parts only — name, match, where, effects. Comments
    are allowed to name the cases, because explaining what a general mechanism
    covers is not the same as branching on it, and the prose is how a reader
    checks the generality claim at all.
    """
    seed = json.loads((Path(__file__).resolve().parents[1] /
                       "seeds" / "surprise_promotion.json").read_text())
    executable = json.dumps([
        {k: rule[k] for k in ("name", "match", "where", "effects") if k in rule}
        for rule in seed["rules"]
    ]).lower()
    # Word-bounded: `recoverability_units` is a legitimate AXIS from the
    # prereg, not a case token, and must not trip this.
    import re
    for banned in ("fall", "falling", "desk", "wall", "smash", "reflex",
                   "protective", "obstacle", "collision", "impact"):
        assert not re.search(rf"\b{banned}\b", executable), (
            f"case-specific token {banned!r} in rule logic — the mechanism "
            f"is supposed to be blind to which case it is handling")


# ------------------------------------------------- the flat-zero pathology

def test_an_unpriced_option_is_not_the_cheapest_one():
    """Imported from the F16 frontier, where this shape was measured twice.

    A surrendered axis scored flat 0.0 dominated a kept axis scored
    unbounded-below; a weaker engine priced as a cheaper escape. Both are
    `failing to have a property priced better than having it imperfectly`.
    An effector that declares no release cost is UNPRICED, not free.
    """
    agent = _agent()
    episode = _episode(agent)
    honest = _effector(agent, episode, release_cost_units=25)
    silent = _effector(agent, episode, release_cost_units=0)
    for effector in (honest, silent):
        channel = _channel(agent, effector)
        _expect(agent, channel, 0)
        _observe(agent, channel, 50)
    agent.inner.run_rules()
    priced = _candidates(agent, honest)[0]
    unpriced = _candidates(agent, silent)[0]
    assert priced["cost_priced"] == 1
    assert unpriced["cost_priced"] == 0
    # The one that declared nothing must NOT look cheaper than the one that
    # declared an honest 25. This is the whole finding.
    assert unpriced["energy_cost_units"] > priced["energy_cost_units"]
    # ...and the floor is DERIVED, not a sentinel: one step past the larger of
    # the ledger's two ceilings. A number picked to be big enough would be
    # wrong the moment a body had a bigger budget than the guess.
    ledger = agent.s.node(
        agent.inner.neighbours(episode, "has_energy_ledger")[0])["attrs"]
    reach = max(ledger["stock_units"], ledger["reachable_units"])
    assert unpriced["energy_cost_units"] == reach + LATTICE_STEP_UNITS
    # Unaffordable BY CONSTRUCTION, whatever the budget turns out to be, so it
    # never reaches the frontier at all.
    assert unpriced["affordable"] == 0
    assert priced["affordable"] == 1
    assert not agent.inner.neighbours(
        _candidate_nodes(agent, silent)[0], "has_pareto_value")


def test_the_unpriced_floor_tracks_a_budget_that_grows():
    """A SENTINEL CAN BE OUT-GUESSED; A DERIVED FLOOR CANNOT.

    Raise the opening balance far above anything a hand-picked constant would
    have anticipated. The unpriced option must still be the more expensive one
    and must still be unaffordable.
    """
    agent = _agent()
    episode = _episode(agent)
    ledger = agent.inner.neighbours(episode, "has_energy_ledger")[0]
    agent.inner.set_attr(ledger, "opening_units", 10_000_000)
    agent.inner.run_rules()
    silent = _effector(agent, episode, release_cost_units=0)
    channel = _channel(agent, silent)
    _expect(agent, channel, 0)
    _observe(agent, channel, 50)
    agent.inner.run_rules()
    unpriced = _candidates(agent, silent)[0]
    stock = agent.s.node(ledger)["attrs"]["stock_units"]
    assert stock == 10_000_000
    assert unpriced["energy_cost_units"] > stock
    assert unpriced["affordable"] == 0


def test_a_finite_converter_makes_an_escape_slower_not_cheaper():
    """The rate ceiling belongs in DURATION, never in price."""
    agent = _agent()
    episode = _episode(agent)
    ledger = agent.inner.neighbours(episode, "has_energy_ledger")[0]
    agent.inner.set_attr(ledger, "rate_ceiling_units", 10)
    effector = _effector(agent, episode, release_cost_units=45)
    _project(agent, _channel(agent, effector), crossing=1)
    agent.inner.run_rules()
    promoted = _candidates(agent, effector)[0]
    # Cost is untouched by how fast the body can convert.
    assert promoted["energy_cost_units"] == 45
    # 45 units at 10 per action is five actions, not a discount.
    assert promoted["actions_required"] == 5
    assert promoted["affordable"] == 1


def test_a_weaker_converter_never_prices_an_option_lower():
    agent = _agent()
    fast_cost, slow_cost = [], []
    for rate in (50, 5):
        a = _agent()
        episode = _episode(a)
        ledger = a.inner.neighbours(episode, "has_energy_ledger")[0]
        a.inner.set_attr(ledger, "rate_ceiling_units", rate)
        effector = _effector(a, episode, release_cost_units=40)
        _project(a, _channel(a, effector), crossing=1)
        a.inner.run_rules()
        c = _candidates(a, effector)[0]
        (fast_cost if rate == 50 else slow_cost).append(
            (c["energy_cost_units"], c["actions_required"]))
    (fast_price, fast_actions), (slow_price, slow_actions) = fast_cost[0], slow_cost[0]
    assert fast_price == slow_price == 40      # price is a property of the act
    assert slow_actions > fast_actions         # weakness costs TIME


# --------------------------------------------- into the real collapse

def _values(agent, candidate_node):
    return sorted(
        (agent.s.node(v)["attrs"] for v in
         agent.inner.neighbours(candidate_node, "has_pareto_value")),
        key=lambda a: a["dimension_ordinal"])


def _candidate_nodes(agent, effector):
    return agent.inner.neighbours(effector, "has_promoted_candidate")


def test_a_candidate_reaches_the_existing_frontier_with_its_axes_separate():
    agent = _agent()
    episode = _episode(agent)
    effector = _effector(agent, episode, goal_relevance_units=4,
                         release_cost_units=6, recoverability_units=2)
    channel = _channel(agent, effector, damage_units=9)
    _expect(agent, channel, 0)
    _observe(agent, channel, 50)
    agent.inner.run_rules()

    profile = agent.inner.neighbours(episode, "has_authority_pareto_profile")[0]
    assert agent.s.node(profile)["attrs"]["dimension_count"] == 5
    candidate = _candidate_nodes(agent, effector)[0]
    assert agent.inner.neighbours(profile, "has_pareto_candidate") == [candidate]

    values = _values(agent, candidate)
    assert [v["dimension_ordinal"] for v in values] == [0, 1, 2, 3, 4]
    assert [v["signed_value"] for v in values] == [4, 8, 9, -6, 2]
    # Cost is the ONLY negated axis — the one place more is worse.
    assert values[3]["objective"] == "authority_energy_cost"
    assert all(v["verified"] == 1 for v in values)


def test_the_existing_dominance_rule_decides_and_this_seed_does_not():
    """`cp_recognize_relational_dominance` does the comparing.

    A candidate that is worse on every axis must be marked dominated by the
    EXISTING rule, with nothing in surprise_promotion ranking anything.
    """
    agent = _agent()
    agent.inner.load_seed_manifest(manifest_for("cognitive_pareto"), agent.agent)
    episode = _episode(agent)
    strong = _effector(agent, episode, goal_relevance_units=9,
                       release_cost_units=1, recoverability_units=9)
    weak = _effector(agent, episode, goal_relevance_units=1,
                     release_cost_units=50, recoverability_units=1)
    for effector, damage in ((strong, 9), (weak, 1)):
        channel = _channel(agent, effector, damage_units=damage)
        _expect(agent, channel, 0)
        _observe(agent, channel, 50)
    agent.inner.run_rules()

    weak_candidate = _candidate_nodes(agent, weak)[0]
    strong_candidate = _candidate_nodes(agent, strong)[0]
    assert agent.s.node(weak_candidate)["attrs"]["dominated"] == 1
    assert agent.s.node(strong_candidate)["attrs"]["dominated"] == 0
    assert agent.inner.neighbours(
        weak_candidate, "is_dominated_by_pareto_candidate") == [strong_candidate]


def test_an_unaffordable_candidate_is_not_published_but_stays_legible():
    agent = _agent()
    episode = _episode(agent)
    ledger = agent.inner.neighbours(episode, "has_energy_ledger")[0]
    agent.inner.set_attr(ledger, "opening_units", 4)
    agent.inner.run_rules()
    effector = _effector(agent, episode, release_cost_units=10_000)
    _project(agent, _channel(agent, effector), crossing=1)
    agent.inner.run_rules()

    profile = agent.inner.neighbours(episode, "has_authority_pareto_profile")[0]
    candidate = _candidate_nodes(agent, effector)[0]
    # The amount ceiling is the one outright refusal: not an option to compare.
    assert agent.inner.neighbours(profile, "has_pareto_candidate") == []
    assert not agent.inner.neighbours(candidate, "has_pareto_value")
    # ...but the refusal is inspectable rather than silent.
    assert agent.s.node(candidate)["attrs"]["affordable"] == 0


def test_publication_is_idempotent_under_a_re_run_fixpoint():
    agent = _agent()
    episode = _episode(agent)
    effector = _effector(agent, episode)
    channel = _channel(agent, effector)
    _expect(agent, channel, 0)
    _observe(agent, channel, 40)
    for _ in range(5):
        agent.inner.run_rules()
    candidate = _candidate_nodes(agent, effector)[0]
    assert len(agent.inner.neighbours(candidate, "has_pareto_value")) == 5


# ------------------------------------------- the efference copy as a rule

def test_the_expectation_comes_from_the_enacted_program_not_the_adapter():
    """The full chain with NO hand-written expectation.

    A reading is published with only its provenance (which program produced
    it); the graph turns the program's own declared prediction into the
    expectation, and the reading then contradicts it.
    """
    agent = _agent()
    episode = _episode(agent)
    effector = _effector(agent, episode)
    channel = _channel(agent, effector, predictor_kind="peak_load")
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "predicted_peak_load_units": 5, "integer_native": 1})
    observation = agent.s.add_node("ChannelObservation", {
        "channel": "contact_force", "value_units": 300, "grounded": 1})
    _edge(agent, channel, "has_channel_observation", observation)
    _edge(agent, observation, "observed_under_motor_program", program)
    agent.inner.run_rules()

    expectations = agent.inner.neighbours(channel, "has_channel_expectation")
    assert len(expectations) == 1
    assert agent.s.node(expectations[0])["attrs"]["value_units"] == 5
    # ...and the body's actual 300 against the command's predicted 5 IS surprise.
    surprises = agent.inner.neighbours(channel, "has_surprise")
    assert len(surprises) == 1
    assert agent.s.node(surprises[0])["attrs"]["surprise_units"] == 295
    assert agent.s.node(surprises[0])["attrs"]["route"] == "detected"
    assert len(_candidates(agent, effector)) == 1


def test_a_channel_with_no_declared_predictor_stays_unsurprisable():
    """An honest statement about the body, not a silent gap."""
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, predictor_kind="")
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "predicted_peak_load_units": 5, "integer_native": 1})
    observation = agent.s.add_node("ChannelObservation", {"value_units": 300})
    _edge(agent, channel, "has_channel_observation", observation)
    _edge(agent, observation, "observed_under_motor_program", program)
    agent.inner.run_rules()
    assert not agent.inner.neighbours(channel, "has_channel_expectation")
    assert not agent.inner.neighbours(channel, "has_surprise")


def test_an_undeclared_prediction_mints_no_expectation_and_no_false_surprise():
    """Caught on a live body: the fall channel was manufacturing surprise.

    The motor program declares no `predicted_vertical_units`, so an expectation
    minted from it carried None and the raw measurement read as the whole
    discrepancy. That is `failing to have a property priced as having it` — the
    F16 shape, in code written an hour after importing the fix for it.

    The engine CAN tell absent from zero: `Eq(Attr, Lit None)` is True only for
    a missing key. The `Plus[Attr, Lit 0]` idiom is what destroys it.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, predictor_kind="vertical")
    program = agent.s.add_node("EmbodiedMotorProgram", {"integer_native": 1})
    observation = agent.s.add_node("ChannelObservation", {"value_units": 116})
    _edge(agent, channel, "has_channel_observation", observation)
    _edge(agent, observation, "observed_under_motor_program", program)
    agent.inner.run_rules()
    assert not agent.inner.neighbours(channel, "has_channel_expectation")
    assert not agent.inner.neighbours(channel, "has_surprise")
    assert _candidates(agent, effector) == []


def test_a_declared_zero_prediction_is_a_real_expectation():
    """...and a program that genuinely predicts 0 must still be expectable."""
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, predictor_kind="vertical")
    program = agent.s.add_node("EmbodiedMotorProgram", {
        "predicted_vertical_units": 0, "integer_native": 1})
    observation = agent.s.add_node("ChannelObservation", {"value_units": 116})
    _edge(agent, channel, "has_channel_observation", observation)
    _edge(agent, observation, "observed_under_motor_program", program)
    agent.inner.run_rules()
    expectations = agent.inner.neighbours(channel, "has_channel_expectation")
    assert len(expectations) == 1
    assert agent.s.node(expectations[0])["attrs"]["value_units"] == 0
    assert len(agent.inner.neighbours(channel, "has_surprise")) == 1


# ------------------------------------------- route (b), from a real stream
#
# Everything above hands the predicted route a `TemporalProjection` already
# made. These gates cover the half that did not exist: turning a channel's own
# observation history into a stream and PROJECTING it. Before this, no rule
# anywhere attached a projection to a channel, so route (b) was present in the
# rule set and unreachable in every run.


def _stream(agent, channel, values, *, trial_ordinal=1):
    """Publish one trial's worth of samples, oldest first."""
    for ordinal, value in enumerate(values):
        node = agent.s.add_node("ChannelObservation", {
            "value_units": value, "trial_ordinal": trial_ordinal,
            "stream_ordinal": ordinal})
        _edge(agent, channel, "has_channel_observation", node)


def _height_channel(agent, effector, values, **kwargs):
    """An APPROACH channel: no predictor, so only route (b) can reach it."""
    # No `predictor_kind`: route (a) is honestly unavailable on this channel
    # (no issued command predicts an altitude), so only route (b) can reach it.
    channel = _channel(agent, effector, channel="base_height_above_ground",
                       damage_units=4, **kwargs)
    _stream(agent, channel, values)
    agent.inner.run_rules()
    return channel


def _projections(agent, channel):
    return [agent.s.node(p)["attrs"]
            for p in agent.inner.neighbours(channel, "has_temporal_projection")]


def test_a_descending_stream_projects_a_crossing_and_promotes_before_contact():
    """THE FALL. Nothing here knows what a fall is.

    The channel carries heights above the floor; the frame origin of a height
    IS the ground. A descending stream reaches it in a countable number of
    steps, and that count promotes an effector no goal is using — while the
    body is still in the air.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent), goal_relevance_units=0)
    values = [117, 90, 63, 36]
    channel = _height_channel(agent, effector, values)

    projection = _projections(agent, channel)
    assert len(projection) == 1
    assert projection[0]["order_fit"] == 1
    assert projection[0]["crossing"] == 2

    promoted = _candidates(agent, effector)
    assert len(promoted) == 1
    assert promoted[0]["route"] == "predicted"
    # Urgency is read off the clock, never authored: horizon 8, crossing 2.
    assert promoted[0]["urgency_units"] == 6
    # ANTICIPATION, NOT REACTION: every sample is still above the ground, so
    # the candidate exists before the body arrives there.
    assert min(values) > 0
    assert not agent.inner.neighbours(channel, "has_channel_expectation")


def test_the_crossing_is_read_at_the_measured_order_not_a_linear_one():
    """Curvature is the whole point of reading the clock at order N.

    A stream whose descent is itself accelerating reaches the ground SOONER
    than its current rate implies. The linear reading of the same last sample
    and last rate (120 at -35 per step) says four steps; the measured
    second-order generator says three.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _height_channel(agent, effector, [200, 195, 180, 155, 120])
    projection = _projections(agent, channel)[0]
    assert projection["order_fit"] == 2
    assert projection["crossing"] == 3
    linear_reading = -(-120 // 35)          # ceiling of margin / rate
    assert projection["crossing"] < linear_reading


def test_a_settled_body_has_no_deadline_and_promotes_nothing():
    """FAILING TO HAVE A DEADLINE MUST NOT BE PRICED AS HAVING ONE.

    The forward walk returns its own bound both when a stream reaches the
    origin exactly there and when it never reaches it at all. A flat stream
    comes back carrying the bound, and promoting on that would turn "no
    measured deadline" into "deadline at the horizon" — the same shape as
    pricing an unpriced option at zero.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _height_channel(agent, effector, [40, 40, 40, 40])
    projection = _projections(agent, channel)[0]
    assert projection["crossing"] == projection["horizon_units"]
    assert _candidates(agent, effector) == []
    assert not agent.inner.neighbours(channel, "has_surprise")


def test_a_receding_stream_promotes_nothing():
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _height_channel(agent, effector, [10, 20, 30, 40])
    assert _projections(agent, channel)[0]["crossing"] == STREAM_HORIZON_UNITS
    assert _candidates(agent, effector) == []


def test_an_incompressible_stream_grounds_at_the_floor_and_promotes_nothing():
    """The honest MDL floor, carried through to promotion.

    A stream with no measured structure has no measured deadline. `order_fit`
    is 0 and the predicted route requires a measured order, so noise cannot
    manufacture urgency.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _height_channel(agent, effector, [7, 2, 91, 13, 55])
    assert _projections(agent, channel)[0]["order_fit"] == 0
    assert _candidates(agent, effector) == []


def test_two_samples_are_not_a_stream():
    """A second difference needs three samples; the stream is never padded."""
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _height_channel(agent, effector, [117, 40])
    assert agent.s.node(channel)["attrs"]["stream_length"] == 2
    assert _projections(agent, channel) == []
    assert _candidates(agent, effector) == []


def test_a_stream_is_scoped_to_one_trial_across_a_reset():
    """Two trials are not one trajectory.

    Every trial begins with a reset, so concatenating them would fit a
    generator to a discontinuity and report a deadline no body is approaching.
    After a second, much slower trial the crossing is re-read from THAT
    trial's samples alone.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _height_channel(agent, effector, [117, 90, 63, 36])
    assert _projections(agent, channel)[0]["crossing"] == 2

    _stream(agent, channel, [120, 119, 118, 117], trial_ordinal=2)
    agent.inner.run_rules()
    projection = _projections(agent, channel)[0]
    assert agent.s.node(channel)["attrs"]["stream_epoch"] == 2
    assert projection["stream_length"] == 4
    # 117 falling at 1 per step is far outside the bound: no near deadline.
    assert projection["crossing"] == STREAM_HORIZON_UNITS


def test_a_projection_is_refreshed_rather_than_left_stale():
    """A stale deadline is worse than no deadline.

    The same channel, the same trial, more samples: the body decelerates and
    stops. The projection minted while it was descending must not survive as
    a standing claim that the ground is two steps away.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _height_channel(agent, effector, [117, 90, 63, 36])
    assert _projections(agent, channel)[0]["crossing"] == 2
    _stream(agent, channel, [36, 36, 36], trial_ordinal=1)
    agent.inner.run_rules()
    projection = _projections(agent, channel)[0]
    assert projection["stream_length"] == 7
    assert projection["crossing"] == STREAM_HORIZON_UNITS


def test_a_sample_with_no_reading_never_reads_as_being_at_the_origin():
    """A MISSING SAMPLE IS NOT A SAMPLE AT ZERO.

    Zero is exactly the origin the crossing is measured to, so coalescing an
    absent reading to 0 would report a body already at the ground — maximum
    urgency manufactured out of blindness. The stream must refuse to fit
    instead.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, channel="base_height_above_ground")
    _stream(agent, channel, [117, 90, 63])
    blind = agent.s.add_node("ChannelObservation", {"trial_ordinal": 1})
    _edge(agent, channel, "has_channel_observation", blind)
    agent.inner.run_rules()
    projection = _projections(agent, channel)[0]
    assert projection["order_fit"] == 0
    assert projection["crossing"] == STREAM_HORIZON_UNITS
    assert _candidates(agent, effector) == []


# ------------------------------------------- the relata, not the constants
#
# Three literals used to sit in the seed. A magic number is a quantity whose
# relatum you failed to name; these gates name each one by showing that the
# behaviour MOVES when the graph datum it is read from moves.


def test_a_discrepancy_below_the_channels_own_quantum_is_not_news():
    """The tolerance floor is the CHANNEL'S measurement step, not a literal.

    Only the adapter that owns the units knows how coarsely it samples. A
    channel that resolves to five units cannot tell four units of disagreement
    from none, and must not report it as surprise.
    """
    agent = _agent()
    episode = _episode(agent)
    coarse = _effector(agent, episode)
    fine = _effector(agent, episode)
    for effector, quantum in ((coarse, 5), (fine, 1)):
        channel = _channel(agent, effector, tolerance_units=0,
                           quantum_units=quantum)
        _expect(agent, channel, 0)
        _observe(agent, channel, 4)
    agent.inner.run_rules()
    # Same disagreement, same tolerance; only the declared quantum differs.
    assert _candidates(agent, coarse) == []
    assert len(_candidates(agent, fine)) == 1


def test_a_channel_declaring_no_quantum_keeps_the_lattice_step():
    """Absence must not become a coarser sensor.

    A channel that declares nothing is quantized onto the integer lattice like
    everything else in-frame, so its step is one and a one-unit disagreement
    still counts. Reading an absent quantum as 0 would push the floor BELOW the
    lattice and make a zero discrepancy surprising.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, tolerance_units=0)
    assert "quantum_units" not in agent.s.node(channel)["attrs"]
    _expect(agent, channel, 0)
    _observe(agent, channel, 1)
    agent.inner.run_rules()
    assert len(_candidates(agent, effector)) == 1
    assert _candidates(agent, effector)[0]["surprise_units"] == 1


def test_an_exactly_zero_discrepancy_is_never_surprising():
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, tolerance_units=0)
    _expect(agent, channel, 7)
    _observe(agent, channel, 7)
    agent.inner.run_rules()
    assert not agent.inner.neighbours(channel, "has_surprise")


def test_urgency_is_read_off_the_loops_own_declared_horizon():
    """The horizon is the ledger's `horizon_actions`, not a number beside it.

    It is the same window the affordability projection already commits to, so
    lengthening the loop's horizon lengthens what counts as an early crossing
    and rescales urgency with it — with nothing in this seed edited.
    """
    agent = _agent()
    episode = _episode(agent)
    ledger = agent.inner.neighbours(episode, "has_energy_ledger")[0]
    agent.inner.set_attr(ledger, "horizon_actions", 20)
    agent.inner.run_rules()
    effector = _effector(agent, episode)
    channel = _channel(agent, effector, predict_horizon_units=0)
    _project(agent, channel, crossing=12)
    agent.inner.run_rules()
    promoted = _candidates(agent, effector)
    # Crossing 12 is outside the default horizon of 8 and inside a horizon of
    # 20; under the old literal this promoted nothing at all.
    assert len(promoted) == 1
    assert promoted[0]["urgency_units"] == 8


def test_a_crossing_beyond_the_loops_horizon_promotes_nothing():
    agent = _agent()
    episode = _episode(agent)
    ledger = agent.inner.neighbours(episode, "has_energy_ledger")[0]
    agent.inner.set_attr(ledger, "horizon_actions", 4)
    agent.inner.run_rules()
    effector = _effector(agent, episode)
    channel = _channel(agent, effector, predict_horizon_units=0)
    _project(agent, channel, crossing=6)
    agent.inner.run_rules()
    assert _candidates(agent, effector) == []


# ------------------------------------- absence, distinguished from zero
#
# Seven instances of one defect landed in a single day: an absent value reading
# as a measured one. These gates pin the three sites in this seed where the
# coalescing idiom put absence on the satisfying side of a guard.


def test_a_blind_reading_cannot_contradict_its_expectation():
    """A MISSING READING IS NOT A READING OF ZERO.

    Coalesced, an observation carrying no value contradicts its expectation by
    exactly the expectation's own size — surprise manufactured out of blindness,
    which is precisely what a dark channel must never produce.
    """
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector)
    _expect(agent, channel, 500)
    blind = agent.s.add_node("ChannelObservation", {"channel": "contact_force"})
    _edge(agent, channel, "has_channel_observation", blind)
    agent.inner.run_rules()
    assert not agent.inner.neighbours(channel, "has_surprise")
    assert _candidates(agent, effector) == []


def test_a_blind_expectation_cannot_be_contradicted_either():
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector)
    empty = agent.s.add_node("ChannelExpectation", {"predictor_kind": "peak_load"})
    _edge(agent, channel, "has_channel_expectation", empty)
    _observe(agent, channel, 500)
    agent.inner.run_rules()
    assert not agent.inner.neighbours(channel, "has_surprise")


def test_a_projection_with_no_crossing_is_not_a_crossing_at_zero():
    """Coalesced, an absent crossing reads as one arriving THIS step —
    maximum urgency conjured from a missing number."""
    agent = _agent()
    effector = _effector(agent, _episode(agent))
    channel = _channel(agent, effector, channel="support_height")
    node = agent.s.add_node("TemporalProjection", {
        "order_fit": 2, "source": "time_infer"})      # no `crossing`
    _edge(agent, channel, "has_temporal_projection", node)
    agent.inner.run_rules()
    assert not agent.inner.neighbours(channel, "has_surprise")
    assert _candidates(agent, effector) == []


def test_a_candidate_with_no_priced_cost_is_never_affordable():
    """AN UNPRICED CANDIDATE IS NOT AN AFFORDABLE ONE. Coalesced, a missing
    cost compares as costing nothing — ignorance priced as the cheapest
    option, the exact shape imported from the F16 frontier."""
    agent = _agent()
    episode = _episode(agent)
    ledger = agent.inner.neighbours(episode, "has_energy_ledger")[0]
    effector = _effector(agent, episode)
    candidate = agent.s.add_node("PromotedCandidate", {
        "route": "detected", "affordable": 1, "integer_native": 1})
    _edge(agent, effector, "has_promoted_candidate", candidate)
    agent.inner.run_rules()
    attrs = agent.s.node(candidate)["attrs"]
    assert "energy_cost_units" not in attrs
    assert attrs["affordable"] == 0
    assert agent.s.node(ledger)["attrs"]["stock_units"] > 0
