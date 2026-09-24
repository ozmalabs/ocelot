"""Phase 7F: the live deliberation bridge has a narrow native boundary."""

from evaluation.native_authority_audit import audit_python_cognitive_branches
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def _agent():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    return agent


def test_live_deliberation_run_rules_is_bound_as_evidence_only_native_boundary():
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "world_adapter.live_deliberation_bridge"]

    assert len(bound) == 1
    record = bound[0]
    assert record["file"] == "substrate/world_adapter.py"
    assert record["function"] == "_bind_live_goals_and_deliberation"
    assert record["call"] == "run_rules"
    assert record["authority"] == "native_graph_bound"
    assert record["boundary"] == "graph_evidence_materialization_only"
    assert record["provenance"] == (
        "native_rule_readback:phase4a_live_deliberation")
    assert record["exception_rule"] == (
        "conversation_deliberation_phase4a_native_settlement_v1")
    assert record["outcome_source"] == "native_rule_readback"
    assert record["python_outcome_selection"] is False
    assert not any(item["file"] == "substrate/world_adapter.py"
                   and item["function"] == "_bind_live_goals_and_deliberation"
                   for item in audit["findings"])


def test_communication_comprehension_execution_is_bound_without_python_selection():
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] == "world_adapter.comprehension_rule_execution"]
    assert len(bound) == 2
    record = bound[0]
    assert record["file"] == "substrate/world_adapter.py"
    assert record["function"] == "comprehend"
    assert record["call"] == "run_rules"
    assert record["authority"] == "native_graph_bound"
    assert record["boundary"] == "graph_rule_execution_only"
    assert record["outcome_source"] == "native_rule_readback"
    assert record["python_outcome_selection"] is False
    assert all(item["boundary"] == "graph_rule_execution_only"
               and item["outcome_source"] == "native_rule_readback"
               and item["python_outcome_selection"] is False
               for item in bound)
    assert not any(item["file"] == "substrate/world_adapter.py"
                   and item["function"] == "comprehend"
                   for item in audit["findings"])


def test_native_cycle_entrypoints_are_bound_as_schedule_execution_only():
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] in {
                 "world_adapter.native_default_cycle",
                 "world_adapter.native_dual_process_cycle",
             }]
    assert len(bound) == 2
    assert {item["function"] for item in bound} == {
        "tick", "dual_process_tick"}
    assert all(item["boundary"] == "native_schedule_execution_only"
               and item["outcome_source"] == "native_cycle_readback"
               and item["python_outcome_selection"] is False
               for item in bound)


def test_neutral_semantic_ingress_is_bound_as_evidence_only():
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] ==
             "world_adapter.neutral_semantic_event_ingress"]
    assert len(bound) == 1
    record = bound[0]
    assert record["function"] == "ingest_semantic_event"
    assert record["call"] == "run_rules"
    assert record["boundary"] == "mechanical_evidence_materialization_only"
    assert record["outcome_source"] == "native_rule_readback"
    assert record["python_outcome_selection"] is False
    assert not any(item["file"] == "substrate/world_adapter.py"
                   and item["function"] == "ingest_semantic_event"
                   for item in audit["findings"])


def test_describe_scene_goal_readback_is_native_evidence_only():
    audit = audit_python_cognitive_branches(".")
    bound = [item for item in audit["bound_calls"]
             if item["cluster"] ==
             "conversation_action.describe_scene_goal_readback"]
    assert len(bound) == 1
    record = bound[0]
    assert record["function"] == "_act_describe_scene"
    assert record["call"] == "run_rules"
    assert record["boundary"] == "graph_evidence_materialization_only"
    assert record["outcome_source"] == "native_rule_readback"
    assert record["python_outcome_selection"] is False
    assert not any(item["file"] == "domains/conversation_action.py"
                   and item["function"] == "_act_describe_scene"
                   for item in audit["findings"])


def test_live_bridge_readback_preserves_graph_provenance_and_native_no_candidate():
    agent = _agent()
    agent.converse("Check the pressure.", speech_act="instruction",
                   speaker="alice", context={"interaction_mode": "non_turn"})
    message = agent._last_turn_inbound
    message_attrs = agent.s.node(message)["attrs"]
    state = message_attrs["discourse_state_id"]
    event = message_attrs["discourse_event_id"]
    goals = [goal for goal in agent.inner.neighbours(agent.agent, "has_goal")
             if message in agent.inner.neighbours(goal, "comprehends")]
    assert goals

    deliberations = [d for d in agent.s.nodes("Deliberation")
                     if goals[0] in agent.inner.neighbours(d, "about_goal")]
    assert len(deliberations) == 1
    deliberation = deliberations[0]
    attrs = agent.s.node(deliberation)["attrs"]

    # These are the materialization/provenance facts crossing the adapter
    # boundary.  The outcome itself is the native Phase 4A readback.
    assert attrs["candidate_source"] == "discourse_state"
    assert attrs["source_candidate_count"] == 0.0
    assert state in agent.inner.neighbours(
        deliberation, "generated_from_discourse_state")
    assert event in agent.inner.neighbours(
        deliberation, "generated_from_discourse_event")
    assert not list(agent.inner.neighbours(deliberation, "has_candidate"))

    # ``no_candidate`` and the complete trace are written by the native rule,
    # not by the Python bridge.  This test intentionally does not infer a
    # conversational response from the result.
    assert attrs["status"] == "no_candidate"
    assert attrs["candidate_trace_complete"] == 1.0
