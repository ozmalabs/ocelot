"""Core System-1/System-2 arbitration and native scheduling boundary."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _fresh():
    return WorldAdapter(seeds=("affective_state_core", "dual_process_core"))


def _context(agent, *, epoch=1, prediction_error=0.0, novelty=0.0,
             uncertainty=0.0, affect=None, system_two_utility=0.0,
             system_two_reliability=0.0, system_two_latency=0.0,
             system_two_effort=0.0):
    context = agent.s.add_node("DualProcessContext", {
        "status": "pending",
        "epoch": epoch,
        "prediction_error": prediction_error,
        "novelty": novelty,
        "uncertainty": uncertainty,
        "system_two_expected_utility": system_two_utility,
        "system_two_reliability": system_two_reliability,
        "system_two_latency": system_two_latency,
        "system_two_effort": system_two_effort,
    })
    _edge(agent, agent.agent, "has_dual_process_context", context)
    if affect is not None:
        _edge(agent, context, "uses_affective_state", affect)
    return context


def _candidate(agent, context, *, epoch=1, value=0.0, urgency=0.0,
               valence=0.0, residual=0.0, grounded=1, reliability=1.0):
    candidate = agent.s.add_node("SystemOneCandidate", {
        "status": "ready",
        "epoch": epoch,
        "default_value": value,
        "urgency": urgency,
        "valence": valence,
        "residual": residual,
        "grounded": grounded,
        "reliability": reliability,
        "learned_default": 0,
        "consolidation_strength": 0.0,
        "accumulated_evidence": 0.0,
        "evidence_increment": 0.0,
        "experience_count": 0,
        "eligibility_trace": 1.0,
        "predicted_value": 0.0,
    })
    _edge(agent, context, "has_system_one_candidate", candidate)
    return candidate


def _selected(agent, context):
    commits = list(agent.inner.neighbours(context, "has_system_one_commit"))
    assert len(commits) == 1
    selected = list(agent.inner.neighbours(commits[0], "selects_candidate"))
    assert len(selected) == 1
    return selected[0]


def _escalation(agent, context):
    escalations = list(
        agent.inner.neighbours(context, "has_system_two_escalation"))
    assert len(escalations) == 1
    return escalations[0]


def _learning_scope(agent, escalation):
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "name": "test_learning", "area": "learning", "enabled": 1,
    })
    _edge(agent, escalation, "recruits_task_set", task_set)
    return task_set


def test_unique_grounded_default_commits_without_system_two():
    agent = _fresh()
    context = _context(agent)
    weak = _candidate(agent, context, value=1.0)
    strong = _candidate(agent, context, value=2.0)

    report = agent.dual_process_tick(trace=True)

    assert _selected(agent, context) == strong
    assert _selected(agent, context) != weak
    assert agent.s.node(context)["attrs"]["route"] == "system_one"
    assert report["system_one_commits"] == 1
    assert report["needs_system_two"] is False
    assert report["system_two_steps"] == 0
    assert [row[1] for row in report["trace"]] == [
        "system_one_settle", "system_one_commit",
    ]


def test_exact_instinct_conflict_is_explicit_system_two_escalation():
    agent = _fresh()
    context = _context(agent)
    _candidate(agent, context, value=1.0)
    _candidate(agent, context, value=1.0)

    report = agent.dual_process_tick()
    escalation = _escalation(agent, context)

    assert agent.s.node(escalation)["attrs"]["reason"] == "instinct_conflict"
    assert agent.s.node(escalation)["attrs"]["status"] == "serviced"
    assert agent.s.node(context)["attrs"]["route"] == "system_two"
    assert report["needs_system_two"] is True
    assert report["system_two_escalations"] == 1
    assert report["system_one_commits"] == 0


def test_out_of_basin_default_escalates_instead_of_guessing():
    agent = _fresh()
    context = _context(agent)
    _candidate(agent, context, value=10.0, residual=2.0)

    report = agent.dual_process_tick()
    escalation = _escalation(agent, context)

    assert agent.s.node(escalation)["attrs"]["reason"] == "no_grounded_default"
    assert report["needs_system_two"] is True


def test_canonical_affect_changes_fast_default_and_uncertainty_weight():
    neutral = _fresh()
    neutral_context = _context(neutral)
    urgent = _candidate(neutral, neutral_context, value=0.0, urgency=1.0)
    calm = _candidate(neutral, neutral_context, value=0.5, urgency=0.0)
    neutral.dual_process_tick()
    assert _selected(neutral, neutral_context) == calm
    assert _selected(neutral, neutral_context) != urgent

    aroused = _fresh()
    affect = aroused.s.add_node("AffectiveState", {
        "arousal": 1.0, "valence": 0.0, "selection_threshold": 0.0,
    })
    aroused_context = _context(
        aroused, uncertainty=0.8, affect=affect)
    urgent = _candidate(aroused, aroused_context, value=0.0, urgency=1.0)
    _candidate(aroused, aroused_context, value=0.5, urgency=0.0)
    report = aroused.dual_process_tick()

    # Arousal changes the fast competition through the canonical affect node,
    # while uncertainty contributes continuously to controller arbitration.
    assert report["needs_system_two"] is False
    assert _selected(aroused, aroused_context) == urgent
    assert aroused.s.node(urgent)["attrs"]["system_one_score"] == pytest.approx(1.0)
    assert aroused.s.node(aroused_context)["attrs"]["system_two_weight"] > 0.0


def agent_reason(agent, context):
    return agent.s.node(_escalation(agent, context))["attrs"]["reason"]


def test_soft_rules_are_deferred_until_graph_requests_system_two():
    agent = _fresh()
    probe = agent.s.add_node("SlowProbe", {"ran": 0})
    root = agent.s.add_node("SlowRoot", {})
    _edge(agent, root, "has_slow_probe", probe)
    agent.inner.add_rule({
        "name": "test_soft_rule",
        "area": "planning",
        "order": 100,
        "latency_class": "soft_realtime",
        "match": [["root", "has_slow_probe", "probe"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                  "key": "ran"},
            "b": {"type": "Lit", "value": 0},
        },
        "effects": [["set_attr", "probe", "ran", 1]],
    })

    report = agent.dual_process_tick()
    assert report["needs_system_two"] is False
    assert agent.s.node(probe)["attrs"]["ran"] == 0

    context = _context(agent, epoch=2, novelty=2.0)
    planning = agent.s.add_node("SystemTwoTaskSet", {
        "name": "planning_scope", "area": "planning", "enabled": 1,
    })
    _edge(agent, context, "recruits_system_two_task_set", planning)
    _candidate(agent, context, epoch=2, value=1.0)
    report = agent.dual_process_tick()
    assert report["needs_system_two"] is True
    assert report["system_two_steps"] > 0
    assert agent.s.node(probe)["attrs"]["ran"] == 1


def test_scoped_system_two_does_not_open_unrelated_soft_area():
    agent = _fresh()
    planning_probe = agent.s.add_node("SlowProbe", {"ran": 0})
    memory_probe = agent.s.add_node("SlowProbe", {"ran": 0})
    planning_root = agent.s.add_node("SlowRoot", {})
    memory_root = agent.s.add_node("SlowRoot", {})
    _edge(agent, planning_root, "has_planning_probe", planning_probe)
    _edge(agent, memory_root, "has_memory_probe", memory_probe)
    for name, area, edge_type in (
        ("test_scoped_planning", "planning", "has_planning_probe"),
        ("test_unrelated_memory", "memory", "has_memory_probe"),
    ):
        agent.inner.add_rule({
            "name": name, "area": area, "order": 100,
            "latency_class": "soft_realtime",
            "match": [["root", edge_type, "probe"]],
            "where": {"type": "Eq",
                      "a": {"type": "Attr",
                            "node": {"type": "Var", "name": "probe"},
                            "key": "ran"},
                      "b": {"type": "Lit", "value": 0}},
            "effects": [["set_attr", "probe", "ran", 1]],
        })

    context = _context(agent, epoch=20, novelty=2.0)
    planning = agent.s.add_node("SystemTwoTaskSet", {
        "name": "planning_only", "area": "planning", "enabled": 1,
    })
    _edge(agent, context, "recruits_system_two_task_set", planning)
    _candidate(agent, context, epoch=20, value=1.0)

    report = agent.dual_process_tick()

    assert report["system_two_escalations"] == 1
    assert agent.s.node(planning_probe)["attrs"]["ran"] == 1
    assert agent.s.node(memory_probe)["attrs"]["ran"] == 0


def test_unscoped_request_remains_pending_and_opens_nothing():
    agent = _fresh()
    probe = agent.s.add_node("SlowProbe", {"ran": 0})
    root = agent.s.add_node("SlowRoot", {})
    _edge(agent, root, "has_slow_probe", probe)
    agent.inner.add_rule({
        "name": "test_unscoped_refusal", "area": "planning", "order": 100,
        "latency_class": "soft_realtime",
        "match": [["root", "has_slow_probe", "probe"]],
        "effects": [["set_attr", "probe", "ran", 1]],
    })
    request = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "external", "epoch": 1,
    })

    report = agent.dual_process_tick()

    assert report["needs_system_two"] is True
    assert report["system_two_escalations"] == 0
    assert agent.s.node(request)["attrs"]["status"] == "requested"
    assert agent.s.node(probe)["attrs"]["ran"] == 0


@pytest.mark.parametrize("task_type, enabled", [
    ("SystemTwoTaskSet", 0),
    ("NotASystemTwoTaskSet", 1),
])
def test_admission_rejects_disabled_or_wrongly_typed_task_sets(
        task_type, enabled):
    agent = _fresh()
    request = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "external", "epoch": 1,
    })
    task_set = agent.s.add_node(task_type, {
        "name": "invalid_scope", "area": "planning", "enabled": enabled,
    })
    _edge(agent, request, "recruits_task_set", task_set)

    report = agent.dual_process_tick()

    assert report["system_two_escalations"] == 0
    assert agent.s.node(request)["attrs"]["status"] == "requested"


def test_explicit_input_epoch_staleness_is_rejected_before_admission():
    agent = _fresh()
    context = _context(agent, epoch=8)
    agent.inner.set_attr(context, "status", "escalated")
    request = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "external",
        "epoch": 7, "input_epoch": 7,
    })
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "name": "stale_scope", "area": "planning", "enabled": 1,
    })
    _edge(agent, request, "about_context", context)
    _edge(agent, request, "recruits_task_set", task_set)

    report = agent.dual_process_tick()

    assert report["system_two_escalations"] == 0
    assert report["system_two_stale"] == 1
    assert agent.s.node(request)["attrs"]["status"] == "stale"


def test_graph_authored_motor_reserve_survives_deep_budget_exhaustion():
    agent = WorldAdapter(seeds=())
    policy = agent.s.add_node("DualProcessPolicy", {
        "enabled": 1, "motor_reserve_steps": 1,
    })
    assert policy is not None
    request = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "external", "epoch": 1,
    })
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "name": "bounded_planning", "area": "planning", "enabled": 1,
    })
    _edge(agent, request, "recruits_task_set", task_set)
    probe = agent.s.add_node(
        "BudgetProbe", {"selected": 0, "counter": 0, "folded": 0})
    root = agent.s.add_node("BudgetRoot", {})
    _edge(agent, root, "has_budget_probe", probe)
    agent.inner.add_rule({
        "name": "test_budgeted_deep_work",
        "area": "planning", "order": 0,
        "latency_class": "soft_realtime",
        "match": [["root", "has_budget_probe", "probe"]],
        "where": {
            "type": "Lt",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                  "key": "counter"},
            "b": {"type": "Lit", "value": 100},
        },
        "effects": [
            ["set_attr", "probe", "selected", 1],
            ["set_attr", "probe", "counter", {"__term__": {
                "type": "Plus",
                "items": [
                    {"type": "Attr",
                     "node": {"type": "Var", "name": "probe"},
                     "key": "counter"},
                    {"type": "Lit", "value": 1},
                ],
            }}],
        ],
    })
    agent.inner.add_rule({
        "name": "test_reserved_motor_fold",
        "area": "motor", "order": 0,
        "latency_class": "hard_realtime",
        "match": [["root", "has_budget_probe", "probe"]],
        "where": {"type": "And", "items": [
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "probe"},
                   "key": "selected"},
             "b": {"type": "Lit", "value": 1}},
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "probe"},
                   "key": "folded"},
             "b": {"type": "Lit", "value": 0}},
        ]},
        "effects": [["set_attr", "probe", "folded", 1]],
    })

    report = agent.dual_process_tick(max_steps=3, trace=True)

    attrs = agent.s.node(probe)["attrs"]
    assert attrs["counter"] == 2
    assert attrs["folded"] == 1
    assert report["steps"] == 3
    assert "system_two_motor_fold" in [row[1] for row in report["trace"]]


def test_scoped_system_two_result_folds_through_hard_motor_rule_same_tick():
    agent = _fresh()
    probe = agent.s.add_node("ExecutiveProbe", {"selected": 0, "folded": 0})
    root = agent.s.add_node("ExecutiveRoot", {})
    _edge(agent, root, "has_executive_probe", probe)
    agent.inner.add_rule({
        "name": "test_executive_select", "area": "planning", "order": 100,
        "latency_class": "soft_realtime",
        "match": [["root", "has_executive_probe", "probe"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr",
                        "node": {"type": "Var", "name": "probe"},
                        "key": "selected"},
                  "b": {"type": "Lit", "value": 0}},
        "effects": [["set_attr", "probe", "selected", 1]],
    })
    agent.inner.add_rule({
        "name": "test_motor_fold", "area": "motor", "order": 0,
        "latency_class": "hard_realtime",
        "match": [["root", "has_executive_probe", "probe"]],
        "where": {"type": "And", "items": [
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "probe"},
                   "key": "selected"},
             "b": {"type": "Lit", "value": 1}},
            {"type": "Eq",
             "a": {"type": "Attr",
                   "node": {"type": "Var", "name": "probe"},
                   "key": "folded"},
             "b": {"type": "Lit", "value": 0}},
        ]},
        "effects": [["set_attr", "probe", "folded", 1]],
    })
    context = _context(agent, epoch=25, novelty=2.0)
    planning = agent.s.add_node("SystemTwoTaskSet", {
        "name": "planning_scope", "area": "planning", "enabled": 1,
    })
    _edge(agent, context, "recruits_system_two_task_set", planning)
    _candidate(agent, context, epoch=25, value=1.0)

    report = agent.dual_process_tick(trace=True)

    assert agent.s.node(probe)["attrs"]["selected"] == 1
    assert agent.s.node(probe)["attrs"]["folded"] == 1
    assert "system_two_motor_fold" in [row[1] for row in report["trace"]]


def test_relative_reliability_utility_and_cost_arbitrate_continuously():
    cheap = _fresh()
    context = _context(
        cheap, system_two_utility=2.0, system_two_reliability=1.0)
    _candidate(cheap, context, value=1.0)
    report = cheap.dual_process_tick()
    assert report["needs_system_two"] is True
    assert agent_reason(cheap, context) == "controller_arbitration"
    assert cheap.s.node(context)["attrs"]["system_two_weight"] > 0.55

    costly = _fresh()
    context = _context(
        costly, system_two_utility=2.0, system_two_reliability=1.0,
        system_two_latency=0.8, system_two_effort=0.8)
    candidate = _candidate(costly, context, value=1.0)
    report = costly.dual_process_tick()
    assert report["needs_system_two"] is False
    assert _selected(costly, context) == candidate
    assert costly.s.node(context)["attrs"]["system_two_weight"] < 0.55


def test_near_conflict_and_low_confidence_recruit_control():
    near = _fresh()
    context = _context(near, epoch=30)
    _candidate(near, context, epoch=30, value=1.0)
    _candidate(near, context, epoch=30, value=1.1)
    near.dual_process_tick()
    assert agent_reason(near, context) == "near_conflict"

    unsure = _fresh()
    context = _context(unsure, epoch=31)
    _candidate(unsure, context, epoch=31, value=2.0, reliability=0.1)
    _candidate(unsure, context, epoch=31, value=0.0, reliability=1.0)
    unsure.dual_process_tick()
    assert agent_reason(unsure, context) == "low_confidence"
    assert unsure.s.node(context)["attrs"]["decision_confidence"] < 0.2


def test_candidate_evidence_accumulates_once_per_epoch():
    agent = _fresh()
    first = _context(agent, epoch=50)
    candidate = _candidate(agent, first, epoch=50, value=1.0)
    agent.inner.set_attr(candidate, "evidence_increment", 0.4)
    agent.dual_process_tick()
    first_evidence = agent.s.node(candidate)["attrs"]["accumulated_evidence"]
    assert first_evidence == pytest.approx(0.4)

    # A second settlement in the same epoch cannot integrate evidence twice.
    agent.dual_process_tick()
    assert agent.s.node(candidate)["attrs"]["accumulated_evidence"] == pytest.approx(
        first_evidence)

    second = _context(agent, epoch=51)
    agent.inner.set_attr(candidate, "epoch", 51)
    _edge(agent, second, "has_system_one_candidate", candidate)
    agent.dual_process_tick()
    assert agent.s.node(candidate)["attrs"]["accumulated_evidence"] == pytest.approx(
        first_evidence * 0.75 + 0.4)


def test_exhausted_budget_does_not_consume_system_two_request():
    agent = _fresh()
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "novelty", "epoch": 3,
    })
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "name": "budgeted_deliberation", "area": "deliberation", "enabled": 1,
    })
    _edge(agent, escalation, "recruits_task_set", task_set)

    deferred = agent.dual_process_tick(max_steps=0, trace=True)
    assert deferred["needs_system_two"] is True
    assert deferred["system_two_escalations"] == 0
    assert agent.s.node(escalation)["attrs"]["status"] == "requested"
    assert [row[1] for row in deferred["trace"]][-1] == "system_two_deferred"

    admitted = agent.dual_process_tick()
    assert admitted["system_two_escalations"] == 1
    assert agent.s.node(escalation)["attrs"]["status"] == "serviced"


def test_one_step_dual_process_cycles_fairly_service_a_held_system_two_request():
    """A continuing fast sheet cannot make a requested slow closure unreachable.

    This is deliberately the smallest physical scheduler budget.  The first
    native cycle services System 1, publishes the graph-resident owed turn,
    and the second services the requested scoped System 2 work; the third
    returns to System 1.  No Python cadence or domain-specific exception is
    involved.
    """
    agent = WorldAdapter(seeds=())
    policy = agent.s.add_node("DualProcessPolicy", {"enabled": 1})
    root = agent.s.add_node("FairnessRoot", {})
    hard_probe = agent.s.add_node("FairnessProbe", {"count": 0})
    soft_probe = agent.s.add_node("FairnessProbe", {"count": 0})
    _edge(agent, root, "has_hard_fairness_probe", hard_probe)
    _edge(agent, root, "has_soft_fairness_probe", soft_probe)
    agent.inner.add_rule({
        "name": "test_continuing_hard_sheet_for_fairness",
        "area": "fairness_fast", "latency_class": "hard_realtime",
        "match": [["root", "has_hard_fairness_probe", "probe"]],
        "where": {"type": "Lt",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                        "key": "count"},
                  "b": {"type": "Lit", "value": 2}},
        "effects": [["set_attr", "probe", "count", {"__term__": {
            "type": "Plus", "items": [
                {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                 "key": "count"},
                {"type": "Lit", "value": 1},
            ],
        }}]],
    })
    agent.inner.add_rule({
        "name": "test_held_soft_sheet_for_fairness",
        "area": "fairness_slow", "latency_class": "soft_realtime",
        "match": [["root", "has_soft_fairness_probe", "probe"]],
        "where": {"type": "Eq",
                  "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"},
                        "key": "count"},
                  "b": {"type": "Lit", "value": 0}},
        "effects": [["set_attr", "probe", "count", 1]],
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "fairness_regression",
    })
    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "area": "fairness_slow", "enabled": 1,
    })
    _edge(agent, escalation, "recruits_task_set", task_set)

    first = agent.dual_process_tick(max_steps=1)
    assert agent.s.node(hard_probe)["attrs"]["count"] == 1
    assert agent.s.node(soft_probe)["attrs"]["count"] == 0
    assert agent.s.node(policy)["attrs"]["system_two_turn_owed"] == 1
    assert first["system_two_escalations"] == 0

    second = agent.dual_process_tick(max_steps=1)
    assert agent.s.node(hard_probe)["attrs"]["count"] == 1
    assert agent.s.node(soft_probe)["attrs"]["count"] == 1
    assert agent.s.node(policy)["attrs"]["system_two_turn_owed"] == 0
    assert second["system_two_escalations"] == 1

    agent.dual_process_tick(max_steps=1)
    assert agent.s.node(hard_probe)["attrs"]["count"] == 2


def test_held_process_admits_its_checkin_but_not_continuation_work():
    agent = WorldAdapter(seeds=())
    policy = agent.s.add_node("CognitiveSupervisionPolicy", {
        "enabled": 1, "cognitive_epoch": 0,
    })
    process = agent.s.add_node("CognitiveProcess", {
        "continuation_authority": 0,
        "lease_generation": 3,
        "renew_before_epoch": 1,
    })
    _edge(
        agent, process,
        "governed_by_cognitive_supervision_policy", policy,
    )

    planning_probe = agent.s.add_node("LeaseProbe", {"ran": 0})
    checkin_probe = agent.s.add_node("LeaseProbe", {"ran": 0})
    root = agent.s.add_node("LeaseRoot", {})
    _edge(agent, root, "has_planning_lease_probe", planning_probe)
    _edge(agent, root, "has_checkin_lease_probe", checkin_probe)
    for name, area, edge_type in (
        ("lease_continuation_probe", "planning", "has_planning_lease_probe"),
        ("lease_checkin_probe", "cognitive_supervision", "has_checkin_lease_probe"),
    ):
        agent.inner.add_rule({
            "name": name,
            "area": area,
            "latency_class": "soft_realtime",
            "match": [["root", edge_type, "probe"]],
            "where": {
                "type": "Eq",
                "a": {"type": "Attr", "node": {
                    "type": "Var", "name": "probe",
                }, "key": "ran"},
                "b": {"type": "Lit", "value": 0},
            },
            "effects": [["set_attr", "probe", "ran", 1]],
        })

    continuation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "continue",
        "lease_generation": 3,
    })
    planning = agent.s.add_node("SystemTwoTaskSet", {
        "area": "planning", "enabled": 1,
    })
    _edge(agent, continuation, "continues_cognitive_process", process)
    _edge(agent, continuation, "recruits_task_set", planning)

    checkin = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "check_in",
        "lease_generation": 3,
    })
    supervision = agent.s.add_node("SystemTwoTaskSet", {
        "area": "cognitive_supervision", "enabled": 1,
    })
    _edge(agent, checkin, "checks_cognitive_process", process)
    _edge(agent, checkin, "recruits_task_set", supervision)

    report = agent.dual_process_tick(trace=True)

    assert agent.s.node(policy)["attrs"]["cognitive_epoch"] == 1
    assert report["system_two_lease_blocked"] == 1
    assert report["system_two_escalations"] == 1
    assert agent.s.node(planning_probe)["attrs"]["ran"] == 0
    assert agent.s.node(checkin_probe)["attrs"]["ran"] == 1
    assert agent.s.node(continuation)["attrs"]["status"] == "requested"
    assert agent.s.node(checkin)["attrs"]["status"] == "serviced"


def test_verified_success_strengthens_habit_incrementally_not_one_shot():
    agent = _fresh()
    context = _context(agent, epoch=4)
    candidate = agent.s.add_node("SystemOneCandidate", {
        "status": "provisional", "learned_default": 0,
        "consolidation_strength": 0.0, "predicted_value": 0.0,
        "experience_count": 0, "eligibility_trace": 1.0,
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "novelty", "epoch": 4,
    })
    outcome = agent.s.add_node("SystemTwoOutcome", {
        "status": "successful", "verified": 1, "actual_value": 1.0,
    })
    _edge(agent, escalation, "about_context", context)
    _edge(agent, escalation, "has_system_two_outcome", outcome)
    _edge(agent, outcome, "consolidates_candidate", candidate)
    _learning_scope(agent, escalation)

    report = agent.dual_process_tick()

    attrs = agent.s.node(candidate)["attrs"]
    assert report["needs_system_two"] is True
    assert attrs["learned_default"] == 0
    assert 0.0 < attrs["consolidation_strength"] < 1.0
    assert attrs["experience_count"] == 1
    assert attrs["source"] == "incremental_system_two_consolidation"
    assert attrs["status"] == "ready"
    assert agent.s.node(outcome)["attrs"]["status"] == "consolidated"


def test_repeated_success_strengthens_then_devaluation_weakens_default():
    agent = _fresh()
    context = _context(agent, epoch=40)
    candidate = agent.s.add_node("SystemOneCandidate", {
        "status": "provisional", "learned_default": 0,
        "consolidation_strength": 0.0, "predicted_value": 0.0,
        "experience_count": 0, "eligibility_trace": 1.0,
    })

    strengths = []
    for epoch in (40, 41, 42):
        escalation = agent.s.add_node("SystemTwoEscalation", {
            "status": "requested", "reason": "training", "epoch": epoch,
        })
        outcome = agent.s.add_node("SystemTwoOutcome", {
            "status": "successful", "verified": 1, "actual_value": 1.0,
        })
        _edge(agent, escalation, "about_context", context)
        _edge(agent, escalation, "has_system_two_outcome", outcome)
        _edge(agent, outcome, "consolidates_candidate", candidate)
        _learning_scope(agent, escalation)
        agent.dual_process_tick()
        strengths.append(
            agent.s.node(candidate)["attrs"]["consolidation_strength"])

    assert strengths[0] < strengths[1] < strengths[2] < 1.0
    assert agent.s.node(candidate)["attrs"]["experience_count"] == 3

    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "devaluation", "epoch": 43,
    })
    outcome = agent.s.add_node("SystemTwoOutcome", {
        "status": "devalued", "verified": 1, "actual_value": 0.0,
    })
    _edge(agent, escalation, "about_context", context)
    _edge(agent, escalation, "has_system_two_outcome", outcome)
    _edge(agent, outcome, "consolidates_candidate", candidate)
    _learning_scope(agent, escalation)
    agent.dual_process_tick()

    attrs = agent.s.node(candidate)["attrs"]
    assert attrs["consolidation_strength"] < strengths[-1]
    assert attrs["source"] == "devalued_or_extinguished_default"
    assert agent.s.node(outcome)["attrs"]["status"] == "revalued"


def test_verified_system_two_success_teaches_attached_small_net():
    agent = _fresh()
    context = _context(agent, epoch=5)
    assemblage = agent.s.add_node("NetworkAssemblage", {
        "input_dim": 1, "output_dim": 1,
    })
    step = agent.s.add_node("AssemblageStep", {
        "order": 0, "dim_behavior": "transform",
    })
    _edge(agent, assemblage, "has_step", step)
    for role, data in {
        "W1": [[1.0]], "b1": [0.0], "W2": [[0.0]], "b2": [0.0],
    }.items():
        weight = agent.s.add_node("WeightTensor", {
            "role": role, "data": data,
        })
        _edge(agent, step, "has_weight", weight)
    net = agent.s.add_node("ReflexNet", {"eta": 0.5})
    _edge(agent, net, "net_assemblage", assemblage)

    candidate = agent.s.add_node("SystemOneCandidate", {
        "status": "provisional", "learned_default": 0,
        "consolidation_strength": 0.0, "predicted_value": 0.0,
        "experience_count": 0, "eligibility_trace": 1.0,
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "novelty", "epoch": 5,
    })
    outcome = agent.s.add_node("SystemTwoOutcome", {
        "status": "successful", "verified": 1,
        "actual_value": 1.0, "input_vec": [1.0], "target": [1.0],
    })
    _edge(agent, escalation, "about_context", context)
    _edge(agent, escalation, "has_system_two_outcome", outcome)
    _edge(agent, outcome, "consolidates_candidate", candidate)
    _edge(agent, outcome, "trains_reflex_net", net)
    _learning_scope(agent, escalation)
    assemblage_id = (
        assemblage.value if hasattr(assemblage, "value") else int(assemblage))
    before = agent.inner.net_forward(assemblage_id, [1.0])[0]

    agent.dual_process_tick()

    after = agent.inner.net_forward(assemblage_id, [1.0])[0]
    assert before == pytest.approx(0.0)
    assert after > before
    assert agent.s.node(outcome)["attrs"]["net_training_queued"] == 1
    assert agent.s.node(net)["attrs"]["surprise"] > 0


def test_dual_process_seed_is_available_but_not_required_by_minimal_core():
    """Available, not required: the seed is registered, loadable, frozen when
    present, and NOT part of the minimal core (2026-10-06)."""
    from substrate.boot_core import CORE_SEEDS, OPTIONAL_CORE_SEEDS, boot_core, load_seeds_into
    from substrate.boot_all import _FROZEN_SEED_IDS

    assert "dual_process_core" not in CORE_SEEDS
    assert "dual_process_core" in OPTIONAL_CORE_SEEDS
    assert "dual_process_core" in _FROZEN_SEED_IDS
    s, ag = boot_core()
    assert not list(s.nodes("DualProcessPolicy"))
    load_seeds_into(s, ag, ["dual_process_core"])
    assert list(s.nodes("DualProcessPolicy"))
