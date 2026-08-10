"""control_regime_escalation — expected-evidence absence is a residual.

The metastability gap measured twice (docs/metastable_regime_escalation.md):
the F-16 jammed-rudder probes all crashed chasing a fixed point that does not
exist, and humanoid epochs 16-18 replayed three byte-identical inert episodes
inside a fixed point that is not the goal — in both, every learning channel
was gated on events that only occur INSIDE the metastable condition, so the
controller could never see that it was outside.

v3.0.0 (docs/regime_pareto_frontier_prereg.md): the four-architecture
powered measurement traced every failure to WHAT THERE WAS TO DECIDE
BETWEEN, not WHEN TO DECIDE.  `cre_publish_regime_deliberation`'s Argmax
over per-rung "support" scalars was the smuggled winner-selection score
docs/embodied_pareto_profiles.md forbids.  Regime selection is now a
Pareto frontier (the shared embodied_pareto_profile primitive's relational
dominance, reused verbatim) plus one explicit, declared selection policy
over whatever survives it.  `regime_ordinal` is an IDENTIFIER a consumer's
Pareto candidate proposes, never a rung position.

Gates here:
  * the general seed's absence -> deliberate -> mint-a-fresh-Pareto-profile
    machinery runs in the agent's own run_rules fixpoint on a synthetic
    regime holder that mints its OWN synthetic candidates (mirroring what a
    real consumer, e.g. the F-16 seed, does);
  * evidence flowing => no escalation; evidence starved past the horizon =>
    exactly ONE ControlRegimeImpasse and an open deliberation;
  * a decisive frontier candidate (situational-priority value > 1.0)
    publishes immediately (order zero, reflex-like); an ambiguous field
    settles at the window backstop;
  * a disabled monitor never fires (opt-in contract);
  * the F-16 consumer seed declares the rung-1 semantics: progress-ratchet /
    band-residence evidence, and adoption retires the yaw-attitude drive and
    swaps the lateral objective to the metastable trim follower; the
    uncontrollability criterion that used to gate orbit ADOPTION now lives
    in the orbit candidate's own achievable-margin formula.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.embodied_graph_transducer import (  # noqa: E402
    add_unchecked_edge,
    stamp_attrs,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


SEED_PATH = os.path.join(ROOT, "seeds", "control_regime_escalation.json")
F16_SEED_PATH = os.path.join(ROOT, "seeds", "f16_flight_path_control.json")


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def _impasses(a):
    out = []
    for node in a.inner.neighbours(a.agent, "has_control_regime_impasse"):
        if a.inner.has_node(node):
            out.append(dict(a.s.node(node)["attrs"]))
    return out


@pytest.fixture()
def agent():
    return WorldAdapter(
        seeds=("control_regime_escalation", "cognitive_pareto")
    )


def _regime(a, **overrides):
    attrs = {
        "regime_monitor_enabled": 1.0,
        "regime_ordinal": 0.0,
        "regime_terminal": 0.0,
        "regime_clock_seq": 0.0,
        "regime_evidence_seq": 0.0,
        "regime_evidence_horizon_actions": 5.0,
        "regime_escalation_requested": 0.0,
        "regime_escalation_count": 0.0,
        "regime_last_escalation_seq": -1.0,
        "regime_pareto_dimension_count": 2.0,
        "regime_pareto_minted_seq": -1.0,
        "regime_absence_integral": 0.0,
        "regime_absence_seq": 0.0,
        "regime_deliberating": 0.0,
    }
    attrs.update(overrides)
    node = a.s.add_node("EmbodiedMotorProgramEpisode", attrs)
    add_unchecked_edge(a, a.agent, "holds_control_regime", node)
    return node


def _current_profile(a, regime):
    """The freshly-minted profile for the CURRENT deliberation, if any."""
    profiles = a.inner.neighbours(regime, "deliberates_over_pareto_profile")
    minted_seq = float(a.s.node(regime)["attrs"]["regime_pareto_minted_seq"])
    for profile in profiles:
        if float(a.s.node(profile)["attrs"]["minted_seq"]) == minted_seq:
            return profile
    return None


def _mint_candidate(a, profile, *, ordinal, terminal, priority_value,
                     dimension_values):
    """Mint one synthetic Pareto candidate the way a real consumer (e.g. the
    F-16 seed's mint_*_pareto_candidate_rule family) would: a candidate node
    plus one verified EmbodiedParetoValue per declared dimension."""
    candidate = a.s.add_node("ParetoCandidate", {
        "identity": f"regime:{ordinal:g}",
        "dominated": 0.0,
        "verified": 1.0,
        "candidate_regime_ordinal": float(ordinal),
        "candidate_terminal": float(terminal),
        "regime_situational_priority_value": float(priority_value),
    })
    add_unchecked_edge(a, profile, "has_pareto_candidate", candidate)
    for ordinal_index, value in enumerate(dimension_values):
        node = a.s.add_node("ParetoValue", {
            "dimension_ordinal": float(ordinal_index),
            "signed_value": float(value),
            "verified": 1.0,
        })
        add_unchecked_edge(a, candidate, "has_pareto_value", node)
    return candidate


def test_seed_is_general_and_declares_the_contract():
    seed = json.loads(open(SEED_PATH, encoding="utf-8").read())
    assert seed["id"] == "control_regime_escalation"
    assert seed["version"] == "7.11.0"
    # v7.8.0: TWO accounts on one scale.  What the goal is worth and what
    # KNOWING is worth are different purchases -- charging both to one account
    # stopped the checklist the moment viability dipped and crashed a scenario
    # that survived by probing (§92).
    budget2 = json.dumps(_rule(seed, "cre_publish_spend_authority"))
    assert "regime_information_worth_log" in budget2
    assert "regime_info_budget_exhausted" in budget2
    # And the floor is measured from the high-water rung, not the current one,
    # or it tracks the descent and can never be violated.
    assert "regime_rung_high_water" in budget2
    # v7.7.0: value is LOG-IRREVERSIBILITY.  The operator declares a RATIO --
    # how many log units separate adjacent rungs -- and the worth in the same
    # units; the loop divides.  Nothing is infinitely valuable, so no rung is
    # unbuyable; and absence degrades to "spend nothing", which is the safe
    # reading of lexicographic ordering rather than the correct one.
    budget = json.dumps(_rule(seed, "cre_publish_spend_authority"))
    assert "regime_rung_decade" in budget
    assert "regime_goal_worth_log" in budget
    assert '"IDiv"' in budget  # a ratio, not a threshold
    # v7.6.0: the OPERATOR declares the budget.  The body is a resource to be
    # spent in service of a goal, so what may be spent is not a property of the
    # body and nothing inside the loop can supply it.  Absent reads 0 -- spend
    # nothing, preserve everything -- which is what every consumer does today.
    budget = json.dumps(_rule(seed, "cre_publish_spend_authority"))
    for key in ("regime_viability_rung", "regime_goal_worth_log",
                "regime_spend_floor", "regime_spend_authorised"):
        assert key in budget, key
    # v7.5.0: the manifold is bounded by regions to REACH and regions to
    # AVOID, and both are the same closure -- reaching a goal and being reached
    # BY a threat differ only in `region_sense`.  A landing envelope, an
    # ejection window and an incoming threat are one declaration.
    region = json.dumps(_rule(seed, "cre_project_region_reachability"))
    for key in ("region_gap", "region_axis_ordinal", "region_actions",
                "region_inside", "channel_rate_measured"):
        assert key in region, key
    # Domain-free: the rule names no vehicle, no threat, no axis.
    for word in ("aircraft", "missile", "threat", "wing", "altitude", "land"):
        assert word not in region.lower(), word
    # v7.2.0: YOU CANNOT WAIT LONGER THAN YOU HAVE.  The opening guard waits
    # the SHORTER of the evidence horizon and the loop's own projection of
    # actions remaining, so a deadline of 8 does not sit behind a wait of 80.
    # Still domain-free -- `regime_actions_to_act` is the general seed's own
    # projection, not a consumer quantity.
    opening = json.dumps(_rule(seed, "cre_note_regime_evidence_absence"))
    assert "regime_actions_to_act" in opening
    assert '"Min"' in opening
    # v7.3.0: the same principle one level in -- a deliberation that has run
    # longer than the time remaining is deciding about a moment that has
    # passed, so it is abandoned and a fresh one may open on current evidence.
    # v7.4.0: a terminal channel is projected TWICE when the consumer supplies
    # a measured loss rate and a measured opposing authority.  Domain-free: the
    # general seed names no axis and no effector.
    assisted = json.dumps(_rule(seed, "cre_project_channel_assisted_clock"))
    assert "channel_rate_measured" in assisted
    assert "channel_authority_measured" in assisted
    assert "channel_clock_assisted" in assisted
    for word in ("roll", "attitude", "wing", "aileron", "wheel", "brake"):
        assert word not in assisted.lower(), word
    stale = json.dumps(_rule(seed, "cre_abandon_stale_deliberation"))
    assert "regime_deliberation_integral" in stale
    assert "regime_actions_to_act" in stale
    # It withdraws a stale question; it must never choose anything.
    assert "regime_ordinal" not in stale
    assert seed["depends_on"] == ["cognitive_pareto"]
    note = json.dumps(_rule(seed, "cre_note_regime_evidence_absence"))
    publish = json.dumps(_rule(seed, "cre_publish_regime_pareto_verdict"))
    # absence is measured purely on the generic contract attrs — no domain
    # vocabulary anywhere in the general seed.
    for key in (
        "regime_monitor_enabled",
        "regime_clock_seq",
        "regime_evidence_seq",
        "regime_evidence_horizon_actions",
        "regime_pareto_dimension_count",
    ):
        assert key in note
    assert "ControlRegimeImpasse" in note
    assert "evidence_absence" in note
    # opening a deliberation mints a fresh, isolated Pareto profile.
    assert "ParetoProfile" in note
    assert "deliberates_over_pareto_profile" in note
    # publication reuses the shared primitive's dominance flag and selects
    # via the one declared, explicit policy axis — never a weighted sum,
    # never an Argmax over fixed per-rung scalars.
    assert "dominated" in publish
    assert "regime_situational_priority_value" in publish
    assert "candidate_regime_ordinal" in publish
    assert "candidate_terminal" in publish
    assert "regime_support_1" not in publish
    assert "Argmax" in json.dumps(seed)
    payload = json.dumps(seed)
    for domain_word in (
        "sideslip", "heading", "humanoid", "gait", "f16",
        # v7.0.0: the reserve contract is about a STOCK, never about fuel, and
        # the ledger it bounds is in ACTION quanta, never in joules or metres.
        # A plant is not required to publish any of those words for the general
        # seed to hold a finite non-increasing bound on its behalf.
        "fuel", "thrust", "energy", "altitude", "airspeed",
    ):
        assert domain_word not in payload
    # v7.0.0 -- UNKNOWN IS NOT UNBOUNDED.  The reserve contract is declared,
    # the ratchet exists, and the option clock is bounded by it.
    ratchet = json.dumps(_rule(seed, "cre_ratchet_channel_reserve"))
    for key in (
        "channel_reserve_actions",
        "channel_reserve_measured",
        "channel_reserve_ceiling",
        "channel_reserve_held",
        "channel_sample_spacing",
    ):
        assert key in ratchet
    project = json.dumps(_rule(seed, "cre_project_channel_clocks"))
    assert "channel_reserve_held" in project
    assert "channel_actions_to_option_loss" in project


def test_flowing_evidence_never_escalates(agent):
    regime = _regime(agent)
    for clock in range(1, 21):
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(clock),
            "regime_evidence_seq": float(clock),
        })
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_ordinal"]) == 0.0
    assert float(attrs["regime_escalation_count"]) == 0.0
    assert _impasses(agent) == []


def test_starved_evidence_opens_a_deliberation_and_mints_a_fresh_profile(
    agent,
):
    regime = _regime(agent)
    # evidence flows to clock 10 …
    for clock in range(1, 11):
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(clock),
            "regime_evidence_seq": float(clock),
        })
        agent.tick()
    # … then stops; inside the horizon nothing happens.  (The integrator's
    # order-safe reset credits evidence one integration late, so the
    # absence integral starts accumulating at clock 12 and crosses the
    # horizon of 5 at clock 17.)
    for clock in range(11, 17):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
        assert float(
            agent.s.node(regime)["attrs"]["regime_ordinal"]
        ) == 0.0, f"escalated inside the horizon at clock {clock}"
    # One action past the horizon the residual is minted — but escalation is
    # a TRIGGER, not a switch: it opens a deliberation and mints a fresh,
    # isolated Pareto profile for it, while the regime itself is unchanged
    # (v2.0.0: reflex and deliberation are one process at different depths).
    stamp_attrs(agent, regime, {"regime_clock_seq": 17.0})
    agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_deliberating"]) == 1.0
    assert float(attrs["regime_ordinal"]) == 0.0
    impasses = _impasses(agent)
    assert len(impasses) == 1
    assert impasses[0]["kind"] == "evidence_absence"
    assert float(impasses[0]["from_ordinal"]) == 0.0
    profile = _current_profile(agent, regime)
    assert profile is not None
    assert float(agent.s.node(profile)["attrs"]["dimension_count"]) == 2.0


def test_no_candidate_leaves_the_incumbent_standing(agent):
    """A deliberation with nothing to compare closes on the incumbent.

    v4.0.0: the verdict is the general goal-audit faculty's — an incumbent
    is left alone unless a DOMINATING alternative falsifies it.  With no
    candidates at all there is no counterexample, so at the window
    backstop `cre_publish_incumbent_stands` closes the deliberation and
    opens a fresh evidence window, changing nothing.  (v3.1.0 hung here
    instead: nothing matched the publish rule and `regime_deliberating`
    stayed 1 forever, blocking every later deliberation.)"""
    regime = _regime(agent, regime_evidence_horizon_actions=3.0)
    for clock in range(1, 8):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    # The deliberation really did open — the residual is graph data the
    # agent holds about itself, whatever the verdict turns out to be.
    assert len(_impasses(agent)) == 1
    # Past the window backstop the incumbent stands and the deliberation
    # closes — the regime is untouched, and the monitor is free to open a
    # later deliberation when evidence starves again.
    for clock in range(8, 60):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_deliberating"]) == 0.0
    assert float(attrs["regime_ordinal"]) == 0.0
    assert float(attrs["regime_escalation_count"]) == 0.0


def test_unambiguous_candidate_publishes_at_order_zero(agent):
    """A decisive frontier candidate settles the collapse immediately — the
    same rule behaving as a reflex, without a separate reflex mechanism."""
    regime = _regime(agent)
    for clock in range(1, 11):
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(clock),
            "regime_evidence_seq": float(clock),
        })
        agent.tick()
    for clock in range(11, 18):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_deliberating"]) == 1.0
    profile = _current_profile(agent, regime)
    assert profile is not None
    # A weak "hold" candidate and a decisively-supported alternative — no
    # worse on either declared axis, strictly better on one, and its own
    # situational-priority reading is decisive (> 1.0).
    _mint_candidate(
        agent, profile,
        ordinal=0, terminal=0, priority_value=0.1,
        dimension_values=(0.0, 0.0),
    )
    _mint_candidate(
        agent, profile,
        ordinal=3, terminal=0, priority_value=4.0,
        dimension_values=(1.0, 4.0),
    )
    # Clock 18 settles dominance and lets the goal-audit faculty mint the
    # GoalRevisionRequest; the verdict publishes on the next action.
    for clock in (18.0, 19.0):
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_ordinal"]) == 3.0
    assert float(attrs["regime_last_verdict"]) == 3.0
    assert float(attrs["regime_deliberating"]) == 0.0


def test_a_tie_keeps_the_regime_being_flown(agent):
    """v3.1.0: the burden of proof is on the CHANGE.

    Two Pareto-EQUAL candidates both survive dominance (neither is no-worse-
    and-strictly-better than the other), and their declared priority
    readings are equal too.  The Argmax alone would break that tie by
    whatever order the frontier happens to iterate in, which is how a
    deliberation opened in healthy flight could abandon the regime it was
    flying on no measured preference at all.  A tie now publishes the
    status quo: the deliberation closes, a fresh evidence window opens,
    and System 1 keeps flying what it was flying.
    """
    regime = _regime(agent)
    for clock in range(1, 11):
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(clock),
            "regime_evidence_seq": float(clock),
        })
        agent.tick()
    for clock in range(11, 18):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    profile = _current_profile(agent, regime)
    assert profile is not None
    _mint_candidate(
        agent, profile,
        ordinal=0, terminal=0, priority_value=0.5,
        dimension_values=(1.0, 1.0),
    )
    _mint_candidate(
        agent, profile,
        ordinal=2, terminal=0, priority_value=0.5,
        dimension_values=(1.0, 1.0),
    )
    # Just past the window backstop — far enough to publish, not so far
    # that the next evidence window starves and opens a SECOND
    # deliberation (which this test mints no candidates for).
    for clock in range(18, 24):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_ordinal"]) == 0.0
    assert float(attrs["regime_escalation_count"]) == 0.0
    assert float(attrs["regime_deliberating"]) == 0.0
    # … and the verdict really was published: the evidence window is fresh.
    assert float(attrs["regime_last_verdict"]) == 0.0
    assert float(attrs["regime_absence_integral"]) < 2.0


def test_a_priority_win_without_dominance_does_not_leave_the_regime(agent):
    """v4.0.0: a higher priority reading is NOT a reason to abandon the
    regime being flown — only a counterexample is.

    Both candidates are Pareto-EQUAL, so neither dominates and the
    goal-audit faculty finds nothing to falsify.  The alternative's
    situational-priority reading is higher, which under v3.1.0's
    domain-local tie-break would have been the whole test; under the
    general faculty it is not evidence at all.  The declared priority
    policy only ever chooses AMONG counterexamples."""
    regime = _regime(agent)
    for clock in range(1, 11):
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(clock),
            "regime_evidence_seq": float(clock),
        })
        agent.tick()
    for clock in range(11, 18):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    profile = _current_profile(agent, regime)
    _mint_candidate(
        agent, profile,
        ordinal=0, terminal=0, priority_value=0.5,
        dimension_values=(1.0, 1.0),
    )
    _mint_candidate(
        agent, profile,
        ordinal=2, terminal=0, priority_value=0.6,
        dimension_values=(1.0, 1.0),
    )
    for clock in range(18, 24):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_ordinal"]) == 0.0
    assert float(attrs["regime_escalation_count"]) == 0.0
    assert float(attrs["regime_deliberating"]) == 0.0


def test_dominated_candidate_is_never_selected(agent):
    """The shared primitive's relational dominance is REUSED, not
    reimplemented: a candidate no worse anywhere and strictly better
    somewhere dominates, and the dominated point is never the verdict even
    if its own situational-priority reading looks larger in isolation."""
    regime = _regime(agent)
    for clock in range(1, 11):
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(clock),
            "regime_evidence_seq": float(clock),
        })
        agent.tick()
    for clock in range(11, 18):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    profile = _current_profile(agent, regime)
    # The incumbent — what is actually being flown, and what the goal-audit
    # faculty needs in order to have something to falsify.
    _mint_candidate(
        agent, profile,
        ordinal=0, terminal=0, priority_value=0.1,
        dimension_values=(0.0, 0.0),
    )
    dominated = _mint_candidate(
        agent, profile,
        ordinal=1, terminal=0, priority_value=5.0,
        dimension_values=(1.0, 1.0),
    )
    _mint_candidate(
        agent, profile,
        ordinal=2, terminal=0, priority_value=0.2,
        dimension_values=(2.0, 2.0),
    )
    stamp_attrs(agent, regime, {"regime_clock_seq": 18.0})
    # One tick to let the shared dominance rule settle …
    agent.tick()
    assert agent.inner.neighbours(
        dominated, "is_dominated_by_pareto_candidate"
    )
    # … the publish rule requires a full tick to have passed since minting
    # before it ever reads `dominated`, so the verdict needs one more.
    for clock in range(19, 45):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_ordinal"]) == 2.0


def test_disabled_monitor_never_fires(agent):
    regime = _regime(agent, regime_monitor_enabled=0.0)
    for clock in range(1, 40):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_ordinal"]) == 0.0
    assert _impasses(agent) == []


def test_terminal_regime_stops_monitoring(agent):
    """`regime_terminal` (mirrored from the selected candidate's own
    `candidate_terminal`) replaces the old `regime_ordinal < regime_max_
    ordinal` ladder ceiling now that ordinals carry no order: once set, the
    absence integrator and the note-absence rule both stop."""
    regime = _regime(agent, regime_terminal=1.0)
    for clock in range(1, 40):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_absence_integral"]) == 0.0
    assert float(attrs["regime_deliberating"]) == 0.0
    assert _impasses(agent) == []


# ────────── v6.0.0: TWO CLOCKS, NOT THREE CLASSES ───────────────────────
#
# Stability is not a third class — it is a KIND CHANGE THAT HAS NOT FINISHED
# HAPPENING YET, whose onset timescale the environment sets.  So the plant is
# in one of two states and everything between them is a TIME, and there are
# TWO of those: how long until the fixpoint is gone, and how long until the
# ESCAPE from it is gone.  The gate fires on their minimum, because a
# projection is only actionable while the option to act survives.  Every
# stream below is SYNTHETIC and declared by shape, never copied from a
# scenario.

_HORIZON = 1023.0  # the consumer's declared "beyond what I can see"


def _channel(a, regime, **overrides):
    attrs = {
        "channel_axis_ordinal": 0.0,
        "channel_history_window": 16.0,
        "channel_horizon": _HORIZON,
        "channel_sample_seq": -1.0,
        "channel_history_seq": -1.0,
        "channel_projected_seq": -1.0,
        "channel_crossing": _HORIZON,
        "channel_option_crossing": _HORIZON,
        "channel_actions_to_transition": _HORIZON,
        "channel_actions_to_option_loss": _HORIZON,
        "verified": 1.0,
    }
    attrs.update(overrides)
    node = a.s.add_node("ControlRegimeChannel", attrs)
    add_unchecked_edge(a, regime, "has_regime_channel", node)
    return node


def _publish(a, regime, channel, crossings, options=None, spacing=1,
             reserves=None):
    """One sample per consumer ACTION, exactly as a consumer publishes them
    from its own per-action projection.

    `reserves` is the v7.0.0 addition: a consumer that can MEASURE the stock
    funding its escape publishes it here, and one that cannot passes None and
    publishes nothing at all."""
    options = options if options is not None else [_HORIZON] * len(crossings)
    measured = reserves if reserves is not None else [None] * len(crossings)
    seq = 0
    for crossing, option, reserve in zip(crossings, options, measured):
        seq += spacing
        stamp_attrs(a, regime, {
            "regime_clock_seq": float(seq),
            "regime_evidence_seq": float(seq),
        })
        stamp_attrs(a, channel, {
            "channel_crossing": float(crossing),
            "channel_option_crossing": float(option),
            "channel_sample_seq": float(seq),
            **(
                {}
                if reserve is None
                else {
                    "channel_reserve_actions": float(reserve),
                    "channel_reserve_measured": 1.0,
                }
            ),
        })
        a.tick()
    return a.s.node(regime)["attrs"]


def test_a_stationary_margin_projects_no_transition(agent):
    """Nothing is closing in, so the TRANSITION clock sits at the declared
    ceiling — the honest reading of "beyond what I can see" and not a number
    the seed invented.

    The ACTING clock does not, and v7.0.0 is why: this channel publishes no
    reserve measurement at all, so the seed holds its own finite bound and
    that bound falls one action per action.  Nothing is closing in on the
    OBJECTIVE, and the stock that would fund the escape is still being spent."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    attrs = _publish(agent, regime, channel, [_HORIZON] * 6)
    assert float(attrs["regime_actions_to_transition"]) == _HORIZON
    acting = float(attrs["regime_actions_to_act"])
    assert acting < _HORIZON
    assert acting == float(attrs["regime_reserve_actions"])


def test_an_unmeasured_reserve_is_finite_and_only_ever_falls(agent):
    """UNKNOWN IS NOT UNBOUNDED.

    The consumer publishes NOTHING about the stock funding its escape — no
    value, no measurement flag — and the seed still holds a finite bound on it
    that never rises.  An unmeasured tank treated as infinite would be an
    assertion; this is the withheld judgement, and it still ends."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    readings = []
    for seq in range(1, 7):
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(seq),
            "regime_evidence_seq": float(seq),
        })
        stamp_attrs(agent, channel, {
            "channel_crossing": _HORIZON,
            "channel_option_crossing": _HORIZON,
            "channel_sample_seq": float(seq),
        })
        agent.tick()
        readings.append(
            float(agent.s.node(regime)["attrs"]["regime_reserve_actions"])
        )
    assert readings == sorted(readings, reverse=True)
    assert readings[0] < _HORIZON
    assert readings[-1] < readings[0]
    # and it bounds the option, which is what makes it more than telemetry
    attrs = agent.s.node(regime)["attrs"]
    assert float(attrs["regime_actions_to_option_loss"]) == readings[-1]


def test_a_measured_reserve_refines_the_bound_but_never_raises_it(agent):
    """A consumer that publishes real values gets a TIGHTER bound; one that
    publishes a larger value than it did before gets no option back.

    The ratchet is the whole law: the reserve never rises, whatever the plant
    reports.  A re-scaled sensor, a mis-read, a refuelling — none of them
    return an option the agent has already spent."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    _publish(agent, regime, channel, [_HORIZON] * 3, reserves=[40, 30, 20])
    tightened = float(
        agent.s.node(regime)["attrs"]["regime_reserve_actions"]
    )
    assert tightened == 20.0
    _publish(agent, regime, channel, [_HORIZON] * 3,
             reserves=[900, 900, 900], spacing=1)
    assert float(
        agent.s.node(regime)["attrs"]["regime_reserve_actions"]
    ) <= tightened


def test_the_reserve_binds_the_option_clock(agent):
    """The trajectory says the escape's own margin is nowhere near its floor;
    the stock that pays for the escape says otherwise, and the acting clock
    follows the earlier of the two."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    attrs = _publish(
        agent, regime, channel, [_HORIZON] * 4,
        reserves=[12, 11, 10, 9],
    )
    assert float(attrs["regime_actions_to_transition"]) == _HORIZON
    assert float(attrs["regime_actions_to_option_loss"]) == 9.0
    assert float(attrs["regime_actions_to_act"]) == 9.0


def test_restoring_the_basin_is_admissible_only_while_the_reserve_lasts(
    agent,
):
    """THE PRICE OF `restores_basin`, representable and not asserted.

    Inside the transition region only a candidate that changes the operating
    condition may be published — and moving the plant to where the basin is
    bigger is paid for out of the one column that never refills.  With the
    reserve exhausted the acting clock is at the lattice floor, so the
    admissible response is no longer "restore" but the full corner set.  The
    hypothesis this makes testable is "restore the basin WHILE THE FUEL TO DO
    IT EXISTS"; nothing here claims the manoeuvre works."""
    regime = _regime(
        agent, regime_class_gate_enabled=1.0,
        regime_kind_horizon_actions=_HORIZON,
        regime_evidence_horizon_actions=200.0,
    )
    channel = _channel(agent, regime)
    # The objective itself is nowhere near unattainable; only the stock is.
    _publish(agent, regime, channel, [_HORIZON] * 4, reserves=[3, 2, 1, 0])
    assert float(
        agent.s.node(regime)["attrs"]["regime_actions_to_act"]
    ) == 0.0
    for _ in range(400):
        clock = float(agent.s.node(regime)["attrs"]["regime_clock_seq"]) + 1.0
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
        if float(agent.s.node(regime)["attrs"]["regime_deliberating"]) > 0.5:
            break
    profile = _current_profile(agent, regime)
    assert profile is not None
    _mint_candidate(agent, profile, ordinal=0, terminal=0,
                    priority_value=0.1, dimension_values=(0.0, 0.0))
    # a corner that SURRENDERS an objective — inadmissible while the escape is
    # still funded, admissible once it is not
    _mint_candidate(agent, profile, ordinal=5, terminal=0,
                    priority_value=9.0, dimension_values=(2.0, 9.0))
    for _ in range(4):
        clock = float(agent.s.node(regime)["attrs"]["regime_clock_seq"]) + 1.0
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
    assert float(agent.s.node(regime)["attrs"]["regime_ordinal"]) == 5.0


def test_a_collapsing_deadline_projects_a_finite_transition_time(agent):
    """The point reading is comfortable at every single sample (600 actions
    left, then 480, …) and the SAMPLE-grain reading of the same operator
    says the deadline itself reaches zero in five samples.  The minimum is
    what the gate reads — the identical argument the consumer makes one
    level down."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    attrs = _publish(
        agent, regime, channel, [600, 480, 360, 240, 120, 60], spacing=10
    )
    projected = float(attrs["regime_actions_to_transition"])
    assert 0.0 < projected < 60.0, projected
    assert float(attrs["regime_actions_to_act"]) == projected


def test_the_option_clock_can_bind_before_the_transition_clock(agent):
    """Fifty metres further down the drain the transition projection is just
    as accurate and completely useless.  With the objective still far off
    but the ESCAPE expiring, the acting clock follows the option."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    attrs = _publish(
        agent, regime, channel,
        [_HORIZON] * 6,
        options=[300, 240, 180, 120, 60, 30],
        spacing=10,
    )
    assert float(attrs["regime_actions_to_transition"]) == _HORIZON
    option = float(attrs["regime_actions_to_option_loss"])
    assert 0.0 < option < 60.0, option
    assert float(attrs["regime_actions_to_act"]) == option


def test_the_projection_is_available_before_evidence_starves(agent):
    """The clocks are NOT gated on a deliberation being open.  Every
    escalation in this line so far has been reactive; a projected time is
    only worth having if it arrives while the authority to act still
    exists."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    attrs = _publish(
        agent, regime, channel, [600, 480, 360, 240, 120, 60], spacing=10
    )
    # evidence flowed the whole way, so nothing ever escalated …
    assert float(attrs["regime_deliberating"]) == 0.0
    assert _impasses(agent) == []
    # … and the projection is on the graph regardless.
    assert float(attrs["regime_actions_to_act"]) < _HORIZON


def test_the_projected_transition_is_minted_as_graph_data(agent):
    regime = _regime(
        agent, regime_kind_horizon_actions=_HORIZON,
        regime_evidence_horizon_actions=200.0,
    )
    channel = _channel(agent, regime)
    _publish(agent, regime, channel, [600, 480, 360, 240, 120, 60],
             spacing=10)
    held = [
        dict(agent.s.node(node)["attrs"])
        for node in agent.inner.neighbours(
            agent.agent, "holds_regime_transition"
        )
        if agent.inner.has_node(node)
    ]
    assert len(held) == 1
    assert held[0]["kind"] == "projected_fixpoint_loss"
    # both clocks are on the record, so it says which one is binding
    assert "actions_to_transition" in held[0]
    assert "actions_to_option_loss" in held[0]


def test_no_projected_transition_routes_to_recalibration(agent):
    """Beyond the control horizon and never are the SAME response, and the
    difference between them is in the minted time rather than a route."""
    regime = _regime(
        agent, regime_class_gate_enabled=1.0,
        regime_kind_horizon_actions=_HORIZON,
    )
    channel = _channel(agent, regime)
    _publish(agent, regime, channel, [_HORIZON] * 6)
    for clock in range(7, 60):
        stamp_attrs(agent, regime, {"regime_clock_seq": float(clock)})
        agent.tick()
        if float(agent.s.node(regime)["attrs"]["regime_deliberating"]) > 0.5:
            break
    profile = _current_profile(agent, regime)
    assert profile is not None
    _mint_candidate(agent, profile, ordinal=0, terminal=0,
                    priority_value=0.1, dimension_values=(0.0, 0.0))
    _mint_candidate(agent, profile, ordinal=3, terminal=0,
                    priority_value=4.0, dimension_values=(1.0, 4.0))
    for _ in range(30):
        clock = float(agent.s.node(regime)["attrs"]["regime_clock_seq"]) + 1.0
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    # the objective set is untouched and the deliberation did not hang
    assert float(attrs["regime_ordinal"]) == 0.0
    assert float(attrs["regime_deliberating"]) == 0.0
    assert float(attrs["regime_recalibration_requested"]) > 0.0


def test_a_coming_transition_admits_only_an_operating_condition_change(
    agent,
):
    """A transition that has NOT happened is not a reason to give up an
    objective — it is a reason to move the plant to where the basin is
    bigger, while the authority to move it still exists.  So inside the
    control horizon only a candidate declaring `candidate_restores_basin`
    may be published, even when a surrendering corner dominates it."""
    regime = _regime(
        agent, regime_class_gate_enabled=1.0,
        regime_kind_horizon_actions=_HORIZON,
        regime_evidence_horizon_actions=200.0,
    )
    channel = _channel(agent, regime)
    _publish(agent, regime, channel, [600, 480, 360, 240, 120, 60],
             spacing=10)
    acting = float(agent.s.node(regime)["attrs"]["regime_actions_to_act"])
    assert 0.0 < acting < 200.0
    for _ in range(400):
        clock = float(agent.s.node(regime)["attrs"]["regime_clock_seq"]) + 1.0
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
        if float(agent.s.node(regime)["attrs"]["regime_deliberating"]) > 0.5:
            break
    profile = _current_profile(agent, regime)
    assert profile is not None
    _mint_candidate(agent, profile, ordinal=0, terminal=0,
                    priority_value=0.1, dimension_values=(0.0, 0.0))
    # a dominating corner that SURRENDERS — must not be published here
    surrender = _mint_candidate(
        agent, profile, ordinal=5, terminal=0,
        priority_value=9.0, dimension_values=(2.0, 9.0),
    )
    del surrender
    for _ in range(4):
        clock = float(agent.s.node(regime)["attrs"]["regime_clock_seq"]) + 1.0
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
    assert float(agent.s.node(regime)["attrs"]["regime_ordinal"]) == 0.0


def test_a_lost_fixpoint_admits_the_full_corner_set(agent):
    """Once the acting clock is at the lattice floor the objective really is
    gone, and surrendering it is the honest response."""
    regime = _regime(
        agent, regime_class_gate_enabled=1.0,
        regime_kind_horizon_actions=_HORIZON,
    )
    channel = _channel(agent, regime)
    _publish(agent, regime, channel, [0, 0, 0, 0, 0, 0])
    assert float(
        agent.s.node(regime)["attrs"]["regime_actions_to_act"]
    ) == 0.0
    for _ in range(400):
        clock = float(agent.s.node(regime)["attrs"]["regime_clock_seq"]) + 1.0
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
        if float(agent.s.node(regime)["attrs"]["regime_deliberating"]) > 0.5:
            break
    profile = _current_profile(agent, regime)
    assert profile is not None
    _mint_candidate(agent, profile, ordinal=0, terminal=0,
                    priority_value=0.1, dimension_values=(0.0, 0.0))
    _mint_candidate(agent, profile, ordinal=5, terminal=0,
                    priority_value=9.0, dimension_values=(2.0, 9.0))
    for _ in range(4):
        clock = float(agent.s.node(regime)["attrs"]["regime_clock_seq"]) + 1.0
        stamp_attrs(agent, regime, {"regime_clock_seq": clock})
        agent.tick()
    assert float(agent.s.node(regime)["attrs"]["regime_ordinal"]) == 5.0


def test_f16_publishes_on_the_general_channel_contract():
    seed = json.loads(open(F16_SEED_PATH, encoding="utf-8").read())
    hold = json.dumps(_rule(seed, "f16_hold_regime_channels"))
    assert "ControlRegimeChannel" in hold
    assert "has_regime_channel" in hold
    publish = json.dumps(_rule(seed, "f16_publish_axis_clock_samples"))
    for key in ("channel_crossing", "channel_option_crossing",
                "channel_sample_seq"):
        assert key in publish
    # the consumer publishes what its OWN held recursion measured, including
    # the OPTION clock read off its own shifted margin stream …
    assert "f16_axis_clock_sideslip" in publish
    assert "f16_axis_clock_option_altitude" in publish
    sample = json.dumps(_rule(seed, "f16_sample_axis_margins"))
    assert "f16_margin_option_altitude" in sample
    # v8.0.0: THRUST IS NOT FREE ENERGY.  The option margin is the REACHABLE
    # set, and it carries both ceilings the falsified block ignored — a rate
    # (the engine's published rating) and an amount (the tank) — plus the two
    # ledger columns whose sum is what the next prediction is about.
    for key in (
        "state_remaining_fuel_kg",
        "state_fuel_specific_energy_j_kg",
        "state_maximum_thrust_n",
        "state_maximum_thrust_n_measured",
        "state_vehicle_mass_kg",
        "f16_energy_mechanical_m",
        "f16_energy_convertible_m",
        "f16_energy_total_m",
        "f16_margin_fuel",
    ):
        assert key in sample
    # the reserve is read off the fuel stream by the SAME held recursion, and
    # published on the general seed's domain-free contract with an honest
    # measured/not-measured token
    assert "f16_axis_clock_fuel" in json.dumps(
        _rule(seed, "f16_project_axis_clocks")
    )
    for key in ("channel_reserve_actions", "channel_reserve_measured",
                "state_remaining_fuel_kg_measured", "f16_axis_clock_fuel"):
        assert key in publish
    # … the projection runs every ACTION, not once per deliberation …
    project = json.dumps(_rule(seed, "f16_project_axis_clocks"))
    assert "regime_deliberating" not in project
    # … exactly ONE corner declares that it changes the operating condition …
    restoring = [
        rule["name"] for rule in seed["rules"]
        if '"candidate_restores_basin": 1.0' in json.dumps(rule)
    ]
    assert restoring == ["f16_mint_speed_priority_pareto_candidate"]
    # … and the general seed's recalibration request routes to the path the
    # consumer already had.
    recal = json.dumps(
        _rule(seed, "f16_recalibrate_on_no_projected_transition")
    )
    assert "regime_recalibration_requested" in recal
    assert "recalibration_marking" in recal


def test_f16_consumer_declares_pareto_regime_candidates():
    seed = json.loads(open(F16_SEED_PATH, encoding="utf-8").read())
    assert seed["version"] == "8.72.0"
    # v8.69.0: the margin is PUBLISHED, not just obeyed.  The MinOver that
    # `terrain_clear` compares against a horizon is now also written out as
    # `margin_actions`, because a boolean can only be obeyed and a number can
    # be priced -- `motor_compose.rs::margin_price` is the consumer.
    rung = json.dumps(_rule(seed, "f16_publish_viability_rung"))
    assert "margin_actions" in rung
    # v8.70.0: and it is a min over regions to AVOID.  Ground contact is a
    # crash for a plane and the whole point for a kinetic payload -- the
    # physics is identical and only `region_sense` differs, so an unfiltered
    # margin would price arriving at a goal region as an emergency.
    assert "region_sense" in rung
    assert "f16_viability_terrain_clear" in rung, (
        "publishing the margin must not replace the ladder that reads it"
    )
    # v8.61.0: the consumer declares its one region -- the terrain -- and the
    # general seed turns the altitude gap and the sink rate into actions to
    # ground.  The ladder then orders what remains: controllable, survivable,
    # terrain clear.
    terrain = json.dumps(_rule(seed, "f16_declare_terrain_region"))
    assert "ControlRegimeRegion" in terrain
    assert "region_gap" in terrain and "region_sense" in terrain
    assert "channel_rate_measured" in terrain
    rung = json.dumps(_rule(seed, "f16_publish_viability_rung"))
    for key in ("f16_viability_rung", "f16_viability_controllable",
                "f16_viability_survivable", "f16_viability_terrain_clear"):
        assert key in rung, key
    # v8.60.0: the PLANT is a contributor.  Its command was issued at
    # construction, so its deviation is command-minus-conformance in the same
    # units every other effector's tracking error uses, and it is gated on
    # `never_commanded` rather than on any F-16 vocabulary.
    plant = json.dumps(_rule(seed, "f16_track_plant_effector_deviation"))
    assert "never_commanded" in plant
    assert "f16_plant_deviation" in plant
    assert "f16_shape_difference_sq" in plant
    # v8.59.0: control residuals are published in the sd loop's vocabulary --
    # an `observed` edge, a `signature`, status "pending".  The slot names are
    # ALIASES: ShapeDecode matches structure, so what matters is only that the
    # two residual classes are different relation graphs.
    for name, marker in (
        ("f16_observe_effector_silent_residual", "silent"),
        ("f16_observe_plant_moved_residual", "answers"),
    ):
        body = json.dumps(_rule(seed, name))
        assert marker in body, name
        assert '"pending"' in body and '"observed"' in body
    # v8.57.0: the tie-break among non-dominated candidates is the SHORTEST
    # CLOCK -- prioritise what you are about to lose -- not two thresholds and
    # a default that never mentioned the axis running out.
    prio = json.dumps(_rule(seed, "f16_choose_regime_situational_priority"))
    assert "500.0" not in prio and "70.0" not in prio
    for key in ("f16_axis_clock_altitude", "f16_axis_clock_heading",
                "f16_axis_clock_attitude"):
        assert key in prio
    # v8.55.0/v8.56.0: an allocation is a BUDGET -- shares normalised by their
    # declared total, so authority given to one objective is not available to
    # another -- and attitude's two streams are wired into the axis budgets so
    # that budget has something to interpolate between.
    assert "_allocated" not in json.dumps(seed)  # a build-time transform
    # v8.38.0/v8.39.0: the probe is read as an escalating LADDER -- how hard
    # it was pushed, the smallest push that answered, and how long the answer
    # took.  Silence at the stop is a verdict; silence at 0.2 is not.
    probe = json.dumps(_rule(seed, "f16_note_probe_authority_evidence"))
    for key in ("f16_probe_max_tested_amplitude",
                "f16_probe_min_responding_amplitude",
                "f16_probe_response_lag_actions"):
        assert key in probe
    # v8.40.0-8.44.0: confidence is ESCALATION COMPLETENESS, not sample
    # volume, and the authority estimate is read off the ladder rather than
    # the ok/fail ratio.  The volume reading is kept under its own name so the
    # two can be compared in one block.
    weight = json.dumps(_rule(seed, "f16_weight_authority_by_evidence"))
    assert "f16_authority_volume_confidence" in weight
    assert "f16_probe_min_responding_amplitude" in weight
    assert "regime_evidence_horizon_actions" in weight
    # v8.45.0: QUORUM is TWO rules -- a group-scoped stamp on the model, then
    # an episode-level Exists over it.  Folding it into the per-model rule
    # read wrong both ways it was tried (a latch fires on the escalation
    # transient; an unlatched episode attr written per-model is whichever
    # model wrote last), so the split is the fix and is asserted here.
    assert "f16_probe_group_silent_at_stop" in weight
    quorum = json.dumps(_rule(seed, "f16_note_probe_quorum"))
    assert '"Exists"' in quorum
    assert "f16_probe_group_silent_at_stop" in quorum
    assert "f16_probe_explanation_found" in quorum
    assert _rule(seed, "f16_note_probe_quorum")["match"] == [
        ["agent", "has_embodied_motor_program_episode", "episode"]
    ]
    # v8.46.0-8.49.0: the stop ends the calibration pass, and it is a latch
    # with ASYMMETRIC energies -- it activates on how long quorum has HELD
    # (never its instantaneous value, which fired on a 1-action transient and
    # crashed a healthy aircraft) and releases on a single action of the
    # condition not holding, because nothing is permanent.
    stop = json.dumps(_rule(seed, "f16_stop_probe_on_quorum"))
    assert "f16_probe_quorum_actions" in stop
    assert "recalibration_required" in stop
    # The activation threshold must contain NO literal horizon constant: it is
    # the measured response lag plus the observation action.
    assert "regime_evidence_horizon_actions" not in stop
    assert "f16_probe_max_response_lag_actions" in stop
    release = json.dumps(_rule(seed, "f16_release_probe_stop"))
    assert "f16_probe_stopped" in release
    # v8.50.0: CONTAINMENT SELECTS.  A kept axis on an objective outside reach
    # contributes nothing, which is the non-uniform rule dominance needs -- a
    # uniform rescale provably cannot change frontier membership (block S).
    hold = json.dumps(_rule(seed, "f16_mint_hold_pareto_candidate"))
    assert "f16_goal_outside_altitude" in hold
    # v8.51.0: attitude is a TERMINAL channel and is priced at its own clock.
    # Discounting it to the horizon hid an 8-action deadline behind 1023.
    chans = _rule(seed, "f16_hold_regime_channels")
    disc = {e[3]["channel_axis"]: e[3]["channel_surrender_discount"]
            for e in chans["effects"]
            if isinstance(e, list) and e[0] == "add_node"
            and isinstance(e[3], dict) and "channel_axis" in e[3]}
    assert disc["attitude"] == 0.0 and disc["altitude"] == 0.0
    assert disc["heading"] == 1.0 and disc["sideslip"] == 1.0
    # v8.53.0: attitude gains its SECOND projection -- the one that lets the
    # axis discriminate at all.  Both terms are measured: roll rate minted as
    # an EMA of the observed angle, roll authority read off the learned
    # effector models.  No coefficient appears.
    # v8.54.0: the consumer publishes MEASUREMENTS onto its attitude channel;
    # the general seed does the projection.  Only which measurements feed it
    # is domain-specific.
    att = json.dumps(_rule(seed, "f16_publish_attitude_channel_measurements"))
    assert "channel_rate_measured" in att
    assert "channel_authority_measured" in att
    assert "mean_roll" in att and "state_roll_angle" in att
    # Once per action, or the measured rate collapses to zero.
    assert "f16_roll_rate_seq" in att
    mirror = json.dumps(_rule(seed, "f16_mirror_attitude_assisted_clock"))
    assert "channel_clock_assisted" in mirror
    assert "control_regime_escalation" in seed["depends_on"]
    # v8.33.0/v8.34.0: a corner is GENERATED, not hand-authored.  Its
    # allocation is computed per axis from the containment margin, so no
    # `shares` tuple appears anywhere in its body -- that is the whole point,
    # and a literal tuple creeping back in is the regression to catch.
    # THE GENERATED CORNER IS RETIRED (block BI).  Minted at the HELD ordinal so
    # adoption changed nothing, it was a measurement probe -- and because it
    # could not be adopted, winning every frontier meant HOLD, suppressing every
    # corner that could have been adopted (AS, AW).
    #
    # The first retirement attempt (BE) took crashes 3/24 -> 7/24, because the
    # probe was a fuse in series with a FALSE ALARM: shifted_cg tripped rung 0 at
    # action 215 on a terrain clock that read 10x short (BG), and removing the
    # fuse let the loop act on it.  The alarm is fixed in BH; the jobs the probe
    # was really doing belong to `candidate_requires_change` (AY) and
    # `cre_close_inadmissible_deliberation` (BC).
    assert "f16_mint_generated_pareto_candidate" not in {
        rule["name"] for rule in seed["rules"]
    }, (
        "the generated probe is retired; re-registering it re-creates the "
        "frontier suppression of blocks AS through AW"
    )
    evidence = json.dumps(
        _rule(seed, "f16_note_flight_path_progress_evidence")
    )
    adopt = json.dumps(_rule(seed, "f16_adopt_metastable_trim"))
    follow = json.dumps(_rule(seed, "f16_follow_metastable_trim"))
    override = json.dumps(_rule(seed, "f16_trim_target_lateral_override"))
    reset = json.dumps(_rule(seed, "f16_reset_regime_on_reference_change"))
    # evidence = progress ratchet or settling-band residence over the three
    # published tracking errors.
    for key in (
        "flight_path_altitude_error_m",
        "flight_path_heading_error_rad",
        "flight_path_airspeed_error_m_s",
        "regime_best_error",
        "regime_evidence_seq",
    ):
        assert key in evidence
    # rung-1 adoption retires the yaw-attitude drive (the unreachable half of
    # the fixed point) and initialises the trim from held state.  Gated on
    # the EXACT identifier now (an Eq, never an inequality — ordinals carry
    # no order).
    assert '"active_yaw_attitude_stabilization", 0.0' in adopt
    assert '"attitude_axis_gating_enabled", 1.0' in adopt
    assert "state_body_vy" in adopt
    assert '"regime_ordinal"' in adopt
    assert '"Eq"' in adopt
    # the trim is a slow follower of the emergent equilibrium …
    assert "trim_follow_time_constant_seconds" in follow
    # … and the lateral objective damps deviation from the trim, not from zero.
    assert "flight_path_trim_body_vy" in override
    assert '"target_lateral"' in override
    # every reference change opens a fresh evidence window.
    assert "regime_best_error" in reset
    assert "regime_reference_heading_snapshot" in reset
    # rung 2: the steady orbit — absolute heading honestly retired, roll
    # objective wings-level, evidence re-scoped away from the heading term.
    orbit = json.dumps(_rule(seed, "f16_adopt_orbit_regime"))
    roll_override = json.dumps(_rule(seed, "f16_orbit_target_roll_override"))
    assert "flight_path_orbit_active" in orbit
    assert '"target_roll_angle", 0.0' in roll_override
    # v2.0.0: the MEASURED uncontrollability criterion — sustained yaw rate
    # vs g*tan(max_bank)/V — moved OUT of the adoption precondition (which
    # is now a bare Eq on the identifier) and INTO the achievable-margin
    # formula every KEEPS-heading candidate (trim, hold, speed priority)
    # scores itself on; orbit SURRENDERS heading (declared 0.0, neutral),
    # so it dominates them exactly when that formula goes negative for a
    # controllable-heading fault, it never needs the criterion itself.
    mint_trim = json.dumps(
        _rule(seed, "f16_mint_sideslip_trim_pareto_candidate")
    )
    assert "f16_yaw_rate_ema" in mint_trim
    assert "maximum_bank_angle_rad" in mint_trim
    assert _rule(seed, "f16_track_yaw_rate_ema")
    # evidence re-scoping keys on actual orbit adoption, not ladder position.
    assert '"flight_path_orbit_active"' in evidence
    # the escalated regime suspends the render-first System-2 proposer:
    # fault dynamics keep the plan-aware search composer.
    assert '"render_first_suspended", 1.0' in adopt


def test_f16_declares_the_two_new_regimes_and_selection_policy():
    seed = json.loads(open(F16_SEED_PATH, encoding="utf-8").read())
    speed_mint = json.dumps(
        _rule(seed, "f16_mint_speed_priority_pareto_candidate")
    )
    roll_mint = json.dumps(
        _rule(seed, "f16_mint_roll_priority_pareto_candidate")
    )
    speed_targets = json.dumps(
        _rule(seed, "f16_speed_priority_targets_override")
    )
    roll_targets = json.dumps(
        _rule(seed, "f16_roll_priority_targets_override")
    )
    # speed priority: altitude surrendered (declared 0.0, never computed
    # from the live altitude error), airspeed and control authority kept.
    assert '"dimension_ordinal": 0.0' in speed_mint
    assert "flight_path_altitude_error_m" not in speed_mint
    assert '"target_forward"' in speed_targets
    assert "maximum_forward_delta_m_s" in speed_targets
    # roll priority: heading AND altitude surrendered, attitude and
    # structural margin kept.
    assert "flight_path_altitude_error_m" not in roll_mint
    assert "f16_yaw_rate_ema" not in roll_mint
    # v5.0.0: a SURRENDERED axis is priced on its own clock -- the actions
    # it has left with no correction applied -- never at a flat 0.0.  Roll
    # priority surrenders altitude, so its altitude value is the
    # actions-to-ground the airframe is already on, read off the ORDER-N
    # projection of the altitude margin's own sample stream rather than
    # from a first-order `altitude / sink` ratio.  The candidate rule
    # therefore names the projected clock, and the projection rule is what
    # names the raw state.
    assert "f16_axis_clock_altitude" in roll_mint
    project = json.dumps(_rule(seed, "f16_project_axis_clocks"))
    sample = json.dumps(_rule(seed, "f16_sample_axis_margins"))
    assert "state_altitude_m" in sample
    assert '"TimeInfer"' in project
    assert '"crossing"' in project
    assert '"order_fit"' in project
    # Structural margin is declared but cannot discriminate: no corner
    # surrenders it, and it has no terminal state this protocol declares,
    # so every candidate scores the planning horizon on it.  That was
    # already true of the ratio bases -- every corner kept it and scored
    # it identically -- and is stated here rather than left implicit.
    assert "state_structural_capacity_fraction" not in roll_mint
    assert '"target_roll_angle", 0.0' in roll_targets
    # the situational selection policy is explicit, declared graph data —
    # a single axis choice, never a weighted sum, never folded into
    # dominance (only used by the general seed's Argmax tie-break).
    priority_rule = json.dumps(
        _rule(seed, "f16_choose_regime_situational_priority")
    )
    assert "regime_policy_priority_axis_ordinal" in priority_rule
    # v8.57.0: the situational priority used to read raw state against two
    # thresholds (`state_altitude_m` < 500 m, `state_true_airspeed_m_s` <
    # 70 m/s, else heading).  It now reads the AXIS CLOCKS and prioritises the
    # shortest -- the loop already measures urgency, and terrain proximity IS
    # a short altitude clock.  The thresholds are gone, and their absence is
    # asserted because they are what pinned the priority to heading for a whole
    # departure (block AF).
    assert "state_altitude_m" not in priority_rule
    assert "500.0" not in priority_rule and "70.0" not in priority_rule
    assert "f16_axis_clock_attitude" in priority_rule
    assert "state_true_airspeed_m_s" not in priority_rule
    for candidate_rule_name in (
        "f16_mint_hold_pareto_candidate",
        "f16_mint_sideslip_trim_pareto_candidate",
        "f16_mint_orbit_pareto_candidate",
        "f16_mint_speed_priority_pareto_candidate",
        "f16_mint_roll_priority_pareto_candidate",
    ):
        rendered = json.dumps(_rule(seed, candidate_rule_name))
        assert "regime_situational_priority_value" in rendered
        assert "ParetoCandidate" in rendered
    # a regime transition resets every corner's mode flags so a
    # re-deliberation can re-enter a corner it has already left.
    reset = json.dumps(
        _rule(seed, "f16_reset_regime_modes_on_transition")
    )
    assert "flight_path_speed_priority_active" in reset
    assert "flight_path_roll_priority_active" in reset


_ALTITUDE_BAND_M = 30.48


def _f16_episode(a, **overrides):
    """The minimal episode the F-16 evidence rule reads, stamped directly.

    Mechanical: every attr here is one the seed's own evidence rule
    consults, at its runner-declared initial value
    (`scripts/jabberwock_jsbsim_f16_paper_replication.py`).
    """
    attrs = {
        "regime_monitor_enabled": 1.0,
        "regime_ordinal": 0.0,
        "regime_terminal": 0.0,
        "regime_max_ordinal": 5.0,
        "regime_clock_seq": 0.0,
        "regime_evidence_seq": 0.0,
        "regime_evidence_horizon_actions": 80.0,
        "regime_absence_integral": 0.0,
        "regime_absence_seq": 0.0,
        "regime_escalation_requested": 0.0,
        "regime_escalation_count": 0.0,
        "regime_last_escalation_seq": -1.0,
        "regime_deliberating": 0.0,
        "regime_urgency": 1.0,
        "regime_previous_error": 0.0,
        "regime_error_ema": 0.0,
        "regime_best_error": 1000000000.0,
        "regime_pareto_dimension_count": 6.0,
        "f16_objectives_held": 0.0,
        "state_body_vy": 0.0,
        "regime_pareto_minted_seq": -1.0,
        "control_action_duration_seconds": 0.1,
        "program_request_seq": 0.0,
        "flight_path_target_request_seq": 0.0,
        "flight_path_altitude_error_m": 0.0,
        "flight_path_heading_error_rad": 0.0,
        "flight_path_airspeed_error_m_s": 0.0,
        "flight_path_orbit_active": 0.0,
        "flight_path_speed_priority_active": 0.0,
        "flight_path_roll_priority_active": 0.0,
        "f16_evidence_seq": 0.0,
        "f16_sink_rate_ema": 0.0,
        "f16_sink_ema_seq": 0.0,
        "f16_sink_ema_time_constant_seconds": 4.0,
        "state_vz": 0.0,
        "state_true_airspeed_m_s": 270.0,
        "maximum_vertical_speed_m_s": 20.0,
        "maximum_flight_path_angle_rad": 0.2617993878,
        "altitude_time_constant_seconds": 20.0,
        "airspeed_time_constant_seconds": 3.0,
        "maximum_forward_delta_m_s": 0.5,
        "maximum_bank_angle_rad": 0.6981317008,
        "gravity_m_s2": 9.80665,
        "state_roll_angle": 0.0,
        "state_structural_capacity_fraction": 1.0,
        "f16_yaw_rate_ema": 0.0,
        "state_altitude_m": 3000.0,
        "regime_reference_altitude_snapshot": 0.0,
        "regime_reference_heading_snapshot": 0.0,
        "regime_reference_airspeed_snapshot": 0.0,
        "reference_altitude_m": 0.0,
        "reference_heading_rad": 0.0,
        "reference_true_airspeed_m_s": 0.0,
    }
    attrs.update(overrides)
    node = a.s.add_node("EmbodiedMotorProgramEpisode", attrs)
    add_unchecked_edge(a, a.agent, "has_embodied_motor_program_episode", node)
    add_unchecked_edge(a, a.agent, "holds_control_regime", node)
    return node


def _drive_f16_evidence(a, episode, altitude_errors_m, start=1, vz=None,
                        altitudes_m=None):
    """Step the evidence rule once per declared altitude error.

    `altitudes_m`, when given, also stamps the AIRFRAME'S OWN ALTITUDE per
    action -- what the v5.0.0 axis-sample stream is accumulated from.  The
    order-N projection has nothing to fit without a moving margin.
    """
    for index, error_m in enumerate(altitude_errors_m, start=start):
        stamped = {
            "program_request_seq": float(index),
            "regime_clock_seq": float(index),
            "flight_path_target_request_seq": float(index),
            "flight_path_altitude_error_m": float(error_m),
        }
        if vz is not None:
            stamped["state_vz"] = float(vz)
        if altitudes_m is not None:
            offset = index - start
            stamped["state_altitude_m"] = float(
                altitudes_m[min(offset, len(altitudes_m) - 1)]
            )
        stamp_attrs(a, episode, stamped)
        a.tick()
    return dict(a.s.node(episode)["attrs"])


def test_f16_evidence_ratchet_is_floored_at_the_settling_band():
    """v2.0.1 regression: healthy in-band flight must keep producing evidence.

    Every episode starts AT its reference, so the first action's joint
    error is identically 0.0 and the ratchet latches `regime_best_error`
    there.  With the settling-band floor applied to the residence arm
    ALONE (the state the Pareto rewrite shipped), "a new best" became
    `error < 0.9 * 0.0` — unsatisfiable — and a healthy episode drifting
    slowly off its initial altitude sat above its own lagging EMA on
    nearly every sample, so evidence starved from the second action in
    ORDINARY HEALTHY FLIGHT (measured, n=100 nominal: 88 episodes opened
    a deliberation and 82 surrendered altitude to the speed-priority
    corner; results/..._pareto_frontier_v1/nominal.json).  The floor
    belongs to BOTH arms: a state inside the published settling band is
    healthy by definition, whatever the regime's own best happens to be.
    """
    agent = WorldAdapter(
        seeds=("embodied_motor_program", "f16_flight_path_control")
    )
    episode = _f16_episode(agent)
    # A monotone drift to ~1.9 band units — well inside the joint band,
    # and rising, so the residence arm's trend test rejects every sample.
    errors = [0.0] + [
        _ALTITUDE_BAND_M * 1.9 * step / 40.0 for step in range(1, 41)
    ]
    attrs = _drive_f16_evidence(agent, episode, errors)
    # Evidence kept flowing: the last action is itself the evidence seq.
    assert float(attrs["regime_evidence_seq"]) == float(len(errors))
    assert float(attrs["regime_absence_integral"]) == 0.0
    assert float(attrs["regime_deliberating"]) == 0.0
    assert float(attrs["regime_ordinal"]) == 0.0


def test_f16_evidence_still_starves_on_a_divergence_past_the_band():
    """The floor must not blind the monitor: a regime diverging past the
    band still stops producing evidence and still opens a deliberation."""
    agent = WorldAdapter(
        seeds=("embodied_motor_program", "f16_flight_path_control")
    )
    episode = _f16_episode(agent, regime_evidence_horizon_actions=10.0)
    # Straight past the band and away: 1 -> 30 band units.
    errors = [0.0] + [
        _ALTITUDE_BAND_M * step for step in range(1, 31)
    ]
    attrs = _drive_f16_evidence(agent, episode, errors[:15])
    # Evidence stopped while the error was still climbing …
    assert float(attrs["regime_evidence_seq"]) < 15.0
    assert float(attrs["regime_absence_integral"]) > 0.0
    # … and past the horizon the deliberation is open.
    assert float(attrs["regime_deliberating"]) == 1.0
    # It then publishes -- and with every control axis still INSIDE its
    # declared authority (nothing is sustaining a rate the loop cannot
    # command), no corner that surrenders an objective dominates the one
    # being flown, so the verdict is the status quo.  A tracking error is
    # not by itself a reason to give an objective up.
    attrs = _drive_f16_evidence(agent, episode, errors[15:], start=16)
    assert float(attrs["regime_ordinal"]) == 0.0
    assert float(attrs["regime_deliberating"]) == 0.0


def test_f16_prices_a_surrendered_axis_on_its_own_clock():
    """The altitude axis is DISTURBANCE-vs-AUTHORITY, not tracking error.

    Same starved divergence as above, but the airframe is now sustaining a
    descent past the vertical speed its own loop can command (20 m/s, the
    declared clamp).  Altitude-hold is genuinely unachievable, so the
    corner that surrenders it dominates the status quo and publishes.
    """
    agent = WorldAdapter(
        seeds=("embodied_motor_program", "f16_flight_path_control")
    )
    episode = _f16_episode(
        agent,
        regime_evidence_horizon_actions=10.0,
        # The descent is already established when the deliberation opens:
        # candidates are minted once per opening, from the state at that
        # moment, and the EMA's own time constant is slower than this
        # synthetic window.
        state_vz=-45.0,
        f16_sink_rate_ema=-45.0,
    )
    errors = [0.0] + [_ALTITUDE_BAND_M * step for step in range(1, 31)]
    # The airframe's own altitude, falling at the declared 45 m/s over the
    # 0.1 s action: the sample stream the v5.0.0 projection is fitted to.
    altitudes = [3000.0 - 4.5 * step for step in range(len(errors))]
    attrs = _drive_f16_evidence(
        agent, episode, errors, vz=-45.0, altitudes_m=altitudes
    )
    assert float(attrs["f16_sink_rate_ema"]) < -20.0
    # The projection ran, at a MEASURED order, on the axis's own history.
    assert float(attrs["f16_axis_order_altitude"]) >= 1.0
    # v5.0.0: the corner that KEEPS altitude spends its declared vertical
    # authority against the descent, so it projects the assisted margin
    # stream; the corner that surrenders it spends none and projects the
    # raw one.  Both are order-N projections of the same airframe at the
    # same instant, differing only by the authority the corner has
    # declared it will apply -- so the keeper is strictly better and the
    # surrendering corner cannot win the axis it gave up, which is the
    # whole point of pricing in time.
    assert (float(attrs["f16_axis_clock_altitude_kept"])
            > float(attrs["f16_axis_clock_altitude"])), attrs
    profile = _current_profile(agent, episode)
    assert profile is not None
    by_identity = {
        agent.s.node(c)["attrs"]["identity"]: c
        for c in agent.inner.neighbours(profile, "has_pareto_candidate")
    }

    def _altitude_value(candidate):
        for value in agent.inner.neighbours(candidate, "has_pareto_value"):
            attrs = agent.s.node(value)["attrs"]
            if float(attrs["dimension_ordinal"]) == 0.0:
                return float(attrs["signed_value"])
        raise AssertionError("no altitude value")

    keeper = _altitude_value(by_identity["regime:hold"])
    surrenderer = _altitude_value(by_identity["regime:4"])
    # v8.50.0 CONTAINMENT SELECTS -- and this assertion is where the old
    # semantics were written down, so it is updated rather than deleted.
    #
    # It used to read `keeper >= surrenderer` unconditionally: keeping an axis
    # must never score worse than giving it up.  That invariant is exactly what
    # made `fixed_point` -- the only corner that surrenders nothing -- score >=
    # every corner on every axis simultaneously, so it was non-dominated in
    # every deliberation and no corner that TRADES could ever be elected.
    # Measured: under a damaged wing the frontier proposed `fixed_point` at
    # every deliberation while the aircraft rolled inverted and hit the ground
    # (regime_pareto_frontier_results.md, block Y).
    #
    # The rule now: keeping an axis outscores surrendering it WHEN THE
    # OBJECTIVE IS REACHABLE, and scores nothing when it is not, because
    # claiming what the plant cannot deliver is worth less than admitting it.
    outside = float(attrs.get("f16_goal_outside_altitude", 0.0)) > 0.5
    if outside:
        assert keeper < surrenderer, (keeper, surrenderer)
    else:
        assert keeper >= surrenderer, (keeper, surrenderer)
    # and every value is an integer count of actions, not a ratio
    assert keeper == int(keeper) and surrenderer == int(surrenderer)


def test_a_channel_that_declares_no_discount_is_priced_in_full(agent):
    """The DEFAULT is the flat MIN, byte-identically.

    `channel_surrender_discount` is v7.1.0's relative-weighting contract, and a
    consumer that has never heard of it must be unaffected.  P0 reads an absent
    attribute as zero, and zero is "priced in full", so the roll-up is the same
    minimum it has always been.  This is the property that lets the contract
    ship without touching any other consumer of this seed."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime)
    assert "channel_surrender_discount" not in agent.s.node(channel)["attrs"]
    attrs = _publish(agent, regime, channel, [60, 50, 40, 30, 20, 10])
    projected = float(attrs["regime_actions_to_transition"])
    assert projected < _HORIZON
    # explicitly priced in full reads the same as not declaring one at all
    other_regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    other = _channel(agent, other_regime, channel_surrender_discount=0.0)
    same = _publish(agent, other_regime, other, [60, 50, 40, 30, 20, 10])
    assert float(same["regime_actions_to_transition"]) == projected


def test_a_fully_discounted_channel_never_forces_action_on_its_own(agent):
    """A channel whose loss is already paid for in another channel's ledger
    does not get to spend it twice.

    The measured defect this fixes: a coordinated turn IS transient sideslip,
    so in HEALTHY flight the sideslip channel reads its floor and a flat
    minimum handed that reading authority over the whole regime — the
    excursion the two-clock block was falsified on.  Discounted in full, the
    same floor reading leaves the acting time at the horizon."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime, channel_surrender_discount=1.0)
    attrs = _publish(agent, regime, channel, [6, 5, 4, 3, 2, 1])
    assert float(attrs["regime_actions_to_transition"]) == _HORIZON
    assert float(attrs["regime_actions_to_act"]) == float(
        attrs["regime_actions_to_option_loss"]
    )


def test_the_undiscounted_channel_still_sets_the_acting_time(agent):
    """Discounting is RELATIVE, not blanket suppression.

    Two channels, one priced in full and one discounted away: the roll-up must
    follow the priced one even though the discounted one reads far lower.  The
    flat minimum would have followed the lower reading, which is the whole
    difference."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    funding = _channel(
        agent, regime, channel_axis_ordinal=0.0,
        channel_surrender_discount=0.0,
    )
    cheap = _channel(
        agent, regime, channel_axis_ordinal=1.0,
        channel_surrender_discount=1.0,
    )
    seq = 0
    for funding_crossing, cheap_crossing in zip(
        (900, 880, 860, 840, 820, 800), (6, 5, 4, 3, 2, 1)
    ):
        seq += 1
        stamp_attrs(agent, regime, {
            "regime_clock_seq": float(seq),
            "regime_evidence_seq": float(seq),
        })
        for node, crossing in (
            (funding, funding_crossing), (cheap, cheap_crossing)
        ):
            stamp_attrs(agent, node, {
                "channel_crossing": float(crossing),
                "channel_option_crossing": _HORIZON,
                "channel_sample_seq": float(seq),
            })
        agent.tick()
    attrs = agent.s.node(regime)["attrs"]
    projected = float(attrs["regime_actions_to_transition"])
    # the cheap channel is at its floor and must NOT be what is read
    assert float(agent.s.node(cheap)["attrs"][
        "channel_actions_to_transition"
    ]) < 10.0
    assert projected > 10.0


def test_the_discount_is_minted_back_onto_the_integer_lattice(agent):
    """In-frame quantities are INTEGER; the discount is a cross-frame ratio.

    A fractional discount is admissible in the MAP between the channel's clock
    and the regime's, and the result of applying it is not — so the weighted
    reading is an integer number of actions like every other clock here."""
    regime = _regime(agent, regime_kind_horizon_actions=_HORIZON)
    channel = _channel(agent, regime, channel_surrender_discount=0.5)
    attrs = _publish(agent, regime, channel, [60, 50, 40, 30, 20, 10])
    projected = float(attrs["regime_actions_to_transition"])
    assert projected == float(int(projected))
    assert 10.0 < projected < _HORIZON
