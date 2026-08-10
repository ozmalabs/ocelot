"""A SUSPENSION MUST NOT OUTLIVE ITS PREMISE — the migrated gate.

Measured 2026-08-07 (growth8 and growth9): ordinal 1
`effector_consequence_survey` sat at `meta_suspended` for entire runs — 22
attempts / 7 successes, then nothing, ever.

`ed_release_dominated_process_for_checkin_replanning` suspends a capability when
the cognitive supervisor withdraws continuation authority. It deletes the active
and selected edges, stamps both step and instance `meta_suspended` — and writes
no `reassess_after_learning_capability` edge. The only reopen rule in the tree,
`ml_reopen_suspended_step_after_revision_condition_changes`, MATCHES on exactly
that edge. So an instance suspended by the embodied path was structurally
unreachable by the only rule that could revive it. Not slow recovery: none.

The release is the exact negation of the suspending premise

    process.status == "replan_required" AND process.continuation_authority == 0

on the same discipline as `cp_retract_stale_relational_dominance`: a derived
state is retracted when the thing it was derived from is gone. Deliberately NOT
keyed on the dominating alternative mastering, nor on this capability's own
evidence changing — both are downstream facts that may never occur, and neither
is what put the instance in this state.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import pytest                                         # noqa: E402

from substrate.world_adapter import WorldAdapter      # noqa: E402
from substrate.seed_loader import manifest_for        # noqa: E402


def _suspended(process_status, authority):
    """A capability suspended by the embodied path, under a supervisor in the
    given state. Returns (agent, instance, step)."""
    agent = WorldAdapter()
    for seed in ("counterfactual_experiment", "embodied_learning_session",
                 "embodied_development"):
        agent.inner.load_seed_manifest(manifest_for(seed), agent.agent)
    edge = agent.inner.add_edge_unchecked

    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    edge(agent.agent, "has_embodied_development_episode", episode)
    plan = agent.s.add_node("SelfDirectedLearningPlan", {})
    edge(episode, "has_self_directed_learning_plan", plan)
    step = agent.s.add_node("LearningPlanStep", {"status": "meta_suspended"})
    edge(plan, "has_learning_plan_step", step)
    instance = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability",
        {"status": "meta_suspended", "name": "effector_consequence_survey",
         "evidence_kind": "effector_coverage"})
    edge(step, "plans_learning_capability", instance)
    process = agent.s.add_node("CognitiveProcess", {
        "status": process_status, "continuation_authority": authority})
    edge(episode, "has_cognitive_process", process)
    edge(process, "supervises_learning_plan_step", step)
    return agent, instance, step


def _settle(agent, instance, step, passes=1):
    for _ in range(passes):
        agent.inner.run_rules()
    return (agent.s.node(instance)["attrs"]["status"],
            agent.s.node(step)["attrs"]["status"])


# ------------------------------------------------------------ the premise holds

def test_a_capability_stays_suspended_while_its_premise_holds():
    """The control. While the supervisor is still withholding authority the
    suspension is correct and must not be released — a fix that simply unsticks
    everything is not a fix."""
    agent, instance, step = _suspended("replan_required", 0)
    assert _settle(agent, instance, step) == ("meta_suspended", "meta_suspended")


# --------------------------------------------------------- the premise is gone

@pytest.mark.parametrize(
    "process_status,authority,why",
    [("continuing", 1, "authority restored outright"),
     ("replan_required", 1, "still replanning, but authority returned"),
     ("planning", 0, "supervisor moved on from replan_required")],
    ids=["authority_restored", "authority_returned", "status_moved_on"])
def test_the_suspension_is_released_when_its_premise_is_gone(
        process_status, authority, why):
    """THE HEADLINE. The premise is a CONJUNCTION, so either half falling away
    ends it. Each of these is a state the supervisor genuinely reaches."""
    agent, instance, step = _suspended(process_status, authority)
    assert _settle(agent, instance, step) == ("available", "ready"), why


def test_the_release_is_recorded_rather_than_silent():
    agent, instance, step = _suspended("continuing", 1)
    _settle(agent, instance, step)
    assert agent.s.node(instance)["attrs"].get(
        "released_from_meta_suspension") == 1


def test_release_reaches_a_fixed_point():
    """Re-running must not thrash between released and suspended."""
    agent, instance, step = _suspended("continuing", 1)
    assert _settle(agent, instance, step, passes=5) == ("available", "ready")


def test_release_returns_it_to_the_frontier_not_straight_to_active():
    """`available` is the planner's input, not its output. Reopening must not
    reselect — whether to run this capability again is the Pareto planner's
    decision, and short-circuiting that would reintroduce the host deciding."""
    agent, instance, step = _suspended("continuing", 1)
    status, _ = _settle(agent, instance, step)
    assert status == "available"
    assert status != "active"


def test_the_embodied_suspender_is_reachable_by_this_rule_at_all():
    """The structural point the live latch turned on: the suspender DELETES
    `has_selected_learning_plan_step`, so a reopen keyed on that edge can never
    match the instances it exists to release. This asserts the release works on
    a graph where only `has_learning_plan_step` remains — which is exactly the
    post-suspension shape."""
    agent, instance, step = _suspended("continuing", 1)
    selected = [n for n in agent.s.nodes("SelfDirectedLearningPlan")
                if agent.inner.neighbours(n, "has_selected_learning_plan_step")]
    assert not selected, "fixture no longer reproduces the post-suspension shape"
    assert _settle(agent, instance, step) == ("available", "ready")
