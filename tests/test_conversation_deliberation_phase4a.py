"""Phase 4A: candidate ledger and native deliberative collapse."""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

pytest.importorskip("substrate_rs")

from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from domains.conversation_deliberation import (
    materialize_deliberation,
    materialize_from_live_thought_manifold,
    materialize_from_thought_manifold,
    materialize_from_discourse_state,
)
from domains.discourse_state import ensure_discourse_state, open_goal, record_event


def _goal(a):
    return a.s.add_node("Goal", {"kind": "answer", "status": "active"})


def _candidates():
    return [
        {"candidate_id": "repair", "kind": "repair", "grounding": 1.0,
         "expected_value": 0.55, "residual_cost": 0.1, "consequence": 0.2,
         "novelty": 0.1, "evidence_path": "goal->gap->repair"},
        {"candidate_id": "answer", "kind": "answer", "grounding": 1.0,
         "expected_value": 0.8, "residual_cost": 0.1, "consequence": 0.5,
         "novelty": 0.2, "evidence_path": "goal->referent->fact"},
        {"candidate_id": "unsupported", "kind": "answer", "grounding": 0.0,
         "expected_value": 1.0, "residual_cost": 0.0, "consequence": 1.0,
         "novelty": 1.0, "evidence_path": ""},
    ]


def test_native_collapse_records_winner_and_rejections():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    d = materialize_deliberation(a, goal=_goal(a), candidates=_candidates())
    a.inner.run_rules()

    da = a.s.node(d)["attrs"]
    assert da["status"] == "selected"
    assert da["candidate_trace_complete"] == 1.0
    selections = list(a.inner.neighbours(d, "has_selection"))
    assert len(selections) == 1
    assert a.s.node(selections[0])["attrs"]["selected_candidate_id"] == "answer"

    by_id = {a.s.node(c)["attrs"]["candidate_id"]: a.s.node(c)["attrs"]
              for c in a.inner.neighbours(d, "has_candidate")}
    assert by_id["answer"]["status"] == "selected"
    assert by_id["repair"]["rejection_reason"] == "outcompeted_by_native_collapse"
    assert by_id["unsupported"]["rejection_reason"] == "missing_grounding_evidence"
    assert all(x["valuation_trace"] == 1.0 for x in by_id.values()
               if x["candidate_id"] != "unsupported")


def test_no_candidate_is_explicit_when_all_candidates_lack_grounding():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    d = materialize_deliberation(a, goal=_goal(a), candidates=[
        {"candidate_id": "hallucinated", "grounding": 0.0,
         "expected_value": 9.0, "residual_cost": 0.0, "consequence": 9.0,
         "novelty": 9.0}
    ])
    a.inner.run_rules()
    assert a.s.node(d)["attrs"]["status"] == "no_candidate"
    assert not list(a.inner.neighbours(d, "has_selection"))


def test_adapter_does_not_select_or_rank_candidates():
    tree = ast.parse(inspect.getsource(materialize_deliberation))
    forbidden = {"sorted", "sort", "max", "min", "argmax", "argmin"}
    calls = {n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not calls.intersection(forbidden)


def test_incomplete_tuple_is_rejected_unless_prior_mode_is_explicit():
    a = WorldAdapter(seeds=())
    goal = _goal(a)
    with pytest.raises(ValueError, match="missing evidence fields"):
        materialize_deliberation(a, goal=goal, candidates=[
            {"candidate_id": "partial", "grounding": 1.0}
        ])
    with pytest.raises(ValueError, match="must not supply Phase 4 tuple"):
        materialize_deliberation(a, goal=goal, candidates=[
            {"candidate_id": "mixed", "grounding": 1.0,
             "expected_value": 0.5}
        ], valuation_mode="authored_family_prior")


def test_authored_prior_mode_preserves_absence_and_requires_seed_policy():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    d = materialize_deliberation(
        a, goal=_goal(a), valuation_mode="authored_family_prior",
        candidates=[{"candidate_id": "unknown-family", "kind": "unlisted",
                     "grounding": 1.0}])
    a.s.set_attr(d, "candidate_source", "authored_family_prior")
    candidate = next(iter(a.inner.neighbours(d, "has_candidate")))
    a.inner.run_rules()
    attrs = a.s.node(candidate)["attrs"]
    assert all(key not in attrs for key in
               ("expected_value", "residual_cost", "consequence", "novelty"))
    assert attrs.get("valuation_trace") != 1.0
    assert a.s.node(d)["attrs"]["status"] == "no_candidate"


def test_family_prior_rules_do_not_overwrite_complete_tuple_valuation():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    d = materialize_deliberation(a, goal=_goal(a), candidates=[{
        "candidate_id": "measured-direct-fact",
        "kind": "turn_continuation_direct_fact", "grounding": 1.0,
        "expected_value": 0.21, "residual_cost": 0.1,
        "consequence": 0.3, "novelty": 0.2,
    }])
    a.inner.run_rules()
    candidate = next(iter(a.inner.neighbours(d, "has_candidate")))
    attrs = a.s.node(candidate)["attrs"]
    assert attrs["expected_value"] == 0.21
    assert "policy_source" not in attrs
    assert attrs["valuation_trace"] == 1.0
    assert attrs.get("valuation_basis") != "authored_family_prior"


def test_live_thought_manifold_source_is_materialized_with_provenance():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    manifold = a.s.add_node("ThoughtManifold", {"manifold_id": "live-1"})
    source = a.s.add_node("ThoughtCandidate", {
        "candidate_id": "manifold-answer", "kind": "answer",
        "grounding": 1.0, "expected_value": 0.8, "residual_cost": 0.1,
        "consequence": 0.5, "novelty": 0.2,
        "evidence_path": "manifold->referent->fact",
    })
    a.inner.add_edge_unchecked(manifold, "proposes_candidate", source)
    d = materialize_from_thought_manifold(a, goal=_goal(a), manifold=manifold)

    assert a.s.node(d)["attrs"]["candidate_source"] == "thought_manifold"
    assert a.s.node(d)["attrs"]["source_candidate_count"] == 1.0
    ledger = list(a.inner.neighbours(d, "has_candidate"))
    assert len(ledger) == 1
    assert list(a.inner.neighbours(ledger[0], "copied_from")) == [source]


def test_native_rejection_and_settle_back_are_traced_from_live_source():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    goal = _goal(a)
    manifold = a.s.add_node("ThoughtManifold", {"manifold_id": "live-2"})
    winner = a.s.add_node("ThoughtCandidate", {
        "candidate_id": "executable", "kind": "action",
        "grounding": 1.0, "expected_value": 0.9, "residual_cost": 0.1,
        "consequence": 0.6, "novelty": 0.2, "execution_ready": 1.0,
        "outcome_status": "pending", "evidence_path": "manifold->goal->act",
    })
    rejected = a.s.add_node("ThoughtCandidate", {
        "candidate_id": "unsupported", "kind": "answer",
        "grounding": 0.0, "expected_value": 1.0, "residual_cost": 0.0,
        "consequence": 1.0, "novelty": 1.0,
    })
    a.inner.add_edge_unchecked(manifold, "proposes_candidate", winner)
    a.inner.add_edge_unchecked(manifold, "proposes_candidate", rejected)
    d = materialize_from_thought_manifold(a, goal=goal, manifold=manifold)
    a.inner.run_rules()

    assert a.s.node(d)["attrs"]["status"] == "executing"
    ledger = {a.s.node(c)["attrs"]["candidate_id"]: c
              for c in a.inner.neighbours(d, "has_candidate")}
    assert a.s.node(ledger["unsupported"])["attrs"]["rejection_trace"] == 1.0
    a.s.set_attr(ledger["executable"], "outcome_status", "resolved")
    a.inner.run_rules()

    attrs = a.s.node(d)["attrs"]
    assert attrs["status"] == "resolved"
    assert attrs["settle_back_trace"] == 1.0
    settlements = list(a.inner.neighbours(d, "has_settlement"))
    assert len(settlements) == 1
    assert a.s.node(settlements[0])["attrs"]["settle_back_trace"] == 1.0

    credits = list(a.inner.neighbours(d, "has_counterfactual_credit"))
    assert len(credits) == 0


def test_resolved_winner_records_grounded_counterfactual_credit_only():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    goal = _goal(a)
    manifold = a.s.add_node("ThoughtManifold", {"manifold_id": "live-credit"})
    winner = a.s.add_node("ThoughtCandidate", {
        "candidate_id": "resolved-answer", "kind": "answer",
        "grounding": 1.0, "expected_value": 0.9, "residual_cost": 0.1,
        "consequence": 0.6, "novelty": 0.2, "execution_ready": 1.0,
        "outcome_status": "pending",
    })
    alternative = a.s.add_node("ThoughtCandidate", {
        "candidate_id": "grounded-repair", "kind": "repair",
        "grounding": 1.0, "expected_value": 0.4, "residual_cost": 0.1,
        "consequence": 0.1, "novelty": 0.1,
    })
    unsupported = a.s.add_node("ThoughtCandidate", {
        "candidate_id": "unsupported", "kind": "answer",
        "grounding": 0.0, "expected_value": 9.0, "residual_cost": 0.0,
        "consequence": 9.0, "novelty": 9.0,
    })
    for candidate in (winner, alternative, unsupported):
        a.inner.add_edge_unchecked(manifold, "proposes_candidate", candidate)

    d = materialize_from_thought_manifold(a, goal=goal, manifold=manifold)
    a.inner.run_rules()
    ledger = {a.s.node(c)["attrs"]["candidate_id"]: c
              for c in a.inner.neighbours(d, "has_candidate")}
    assert a.s.node(d)["attrs"]["status"] == "executing"
    a.s.set_attr(ledger["resolved-answer"], "outcome_status", "resolved")
    a.inner.run_rules()

    credits = list(a.inner.neighbours(d, "has_counterfactual_credit"))
    assert len(credits) == 1
    credit = a.s.node(credits[0])["attrs"]
    assert credit["selected_candidate_id"] == "resolved-answer"
    assert credit["rejected_candidate_id"] == "grounded-repair"
    assert credit["counterfactual_status"] == "unexecuted_alternative"
    assert credit["winner_outcome"] == "resolved"
    assert credit["winner_margin"] > 0.0
    assert credit["counterfactual_credit"] < 0.0
    assert a.s.node(ledger["grounded-repair"])["attrs"]["counterfactual_trace"] == 1.0
    assert a.s.node(ledger["unsupported"])["attrs"]["counterfactual_trace"] == 0.0


def test_repeated_native_tasks_preserve_grounding_and_credit_without_duplication():
    """Repeated tasks replay the same native arbitration contract.

    The loop only supplies graph evidence and advances the observed outcome;
    it never chooses a winner.  Each iteration therefore tests that native
    arbitration keeps the grounded winner, records exactly one grounded
    rejected alternative, and remains idempotent when the rule engine is
    settled again.
    """
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    observations = []

    for epoch in range(1, 5):
        goal = a.s.add_node("Goal", {"kind": "answer", "status": "active",
                                     "task_epoch": float(epoch)})
        manifold = a.s.add_node("ThoughtManifold", {
            "manifold_id": f"repeated-task-{epoch}",
            "task_family": "grounded-answer",
        })
        winner = a.s.add_node("ThoughtCandidate", {
            "candidate_id": f"answer-{epoch}", "kind": "answer",
            "grounding": 1.0, "expected_value": 0.9,
            "residual_cost": 0.1, "consequence": 0.6, "novelty": 0.2,
            "execution_ready": 1.0, "outcome_status": "pending",
            "evidence_path": "manifold->referent->fact",
        })
        alternative = a.s.add_node("ThoughtCandidate", {
            "candidate_id": f"repair-{epoch}", "kind": "repair",
            "grounding": 1.0, "expected_value": 0.4,
            "residual_cost": 0.1, "consequence": 0.1, "novelty": 0.1,
            "evidence_path": "manifold->residual->repair",
        })
        a.inner.add_edge_unchecked(manifold, "proposes_candidate", winner)
        a.inner.add_edge_unchecked(manifold, "proposes_candidate", alternative)

        d = materialize_from_thought_manifold(
            a, goal=goal, manifold=manifold, epoch=epoch)
        a.inner.run_rules()
        ledger = {a.s.node(c)["attrs"]["candidate_id"]: c
                  for c in a.inner.neighbours(d, "has_candidate")}
        selected = [c for c in ledger.values()
                    if a.s.node(c)["attrs"]["status"] == "executing"]
        assert len(selected) == 1
        selected_attrs = a.s.node(selected[0])["attrs"]
        assert selected_attrs["candidate_id"] == f"answer-{epoch}"
        assert selected_attrs["grounding"] == 1.0

        a.inner.run_rules()
        assert a.s.node(d)["attrs"]["status"] == "executing"
        a.s.set_attr(selected[0], "outcome_status", "resolved")
        a.inner.run_rules()
        a.inner.run_rules()

        credits = list(a.inner.neighbours(d, "has_counterfactual_credit"))
        assert len(credits) == 1
        credit = a.s.node(credits[0])["attrs"]
        assert credit["selected_candidate_id"] == f"answer-{epoch}"
        assert credit["rejected_candidate_id"] == f"repair-{epoch}"
        assert credit["counterfactual_status"] == "unexecuted_alternative"
        assert credit["counterfactual_credit"] < 0.0
        assert a.s.node(ledger[f"repair-{epoch}"])["attrs"]["grounding"] == 1.0
        observations.append((credit["winner_margin"], credit["counterfactual_credit"]))

    assert len(observations) == 4
    assert len(set(observations)) == 1


def test_discourse_state_generates_goal_and_residual_stance_candidates_for_native_collapse():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    state = ensure_discourse_state(a, conversation_id="generated")
    origin = record_event(a, state, kind="request", expectation="answer")
    goal_evidence = a.s.add_node("GoalEvidence", {
        "grounding": 1.0, "expected_value": 0.3,
        "residual_cost": 0.1, "consequence": 0.1, "novelty": 0.1,
    })
    goal = open_goal(a, state, kind="answer", origin_event=origin,
                     evidence=goal_evidence)
    stance = a.s.add_node("ResidualStance", {
        "stance_id": "uncertain", "grounding": 1.0,
        "expected_value": 0.2, "residual_cost": 0.1,
        "consequence": 0.1, "novelty": 0.1,
    })
    a.inner.add_edge_unchecked(state, "has_residual_stance", stance)
    repair = a.s.add_node("RepairNeed", {
        "repair_id": "missing-evidence", "grounding": 1.0,
        "expected_value": 0.4, "residual_cost": 0.2,
        "consequence": 0.2, "novelty": 0.0,
    })
    a.inner.add_edge_unchecked(state, "has_repair_need", repair)
    d = materialize_from_discourse_state(a, state=state)
    a.inner.run_rules()

    assert a.s.node(d)["attrs"]["candidate_source"] == "discourse_state"
    assert a.s.node(d)["attrs"]["source_candidate_count"] == 3.0
    ids = {a.s.node(c)["attrs"]["candidate_id"]: c
           for c in a.inner.neighbours(d, "has_candidate")}
    assert "goal:" + str(goal) in ids
    assert "stance:uncertain" in ids
    assert "repair:missing-evidence" in ids
    assert list(a.inner.neighbours(ids["goal:" + str(goal)], "derived_from_evidence")) == [goal]
    assert list(a.inner.neighbours(ids["repair:missing-evidence"], "derived_from_evidence")) == [repair]
    assert a.s.node(d)["attrs"]["status"] == "selected"
    assert a.s.node(d)["attrs"]["candidate_trace_complete"] == 1.0


def test_discourse_state_without_cognitive_evidence_is_explicit_no_candidate():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    state = ensure_discourse_state(a, conversation_id="empty")
    d = materialize_from_discourse_state(a, state=state)
    a.inner.run_rules()
    assert a.s.node(d)["attrs"]["candidate_source"] == "discourse_state"
    assert a.s.node(d)["attrs"]["source_candidate_count"] == 0.0
    assert a.s.node(d)["attrs"]["status"] == "no_candidate"
    assert not list(a.inner.neighbours(d, "has_selection"))


def test_live_thought_manifold_materializes_multiple_graph_evidence_paths():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    goal = _goal(a)
    manifold = a.s.add_node("ThoughtManifold", {"manifold_id": "live-multi-source"})
    sources = [
        ("has_goal_evidence", "GoalEvidence", "goal", 0.65),
        ("has_repair_evidence", "RepairEvidence", "repair", 0.55),
        ("has_stance_evidence", "StanceEvidence", "repair_or_defer", 0.25),
        ("has_residual_evidence", "ResidualEvidence", "repair_or_defer", 0.15),
    ]
    source_nodes = []
    for relation, node_type, kind, expected_value in sources:
        source = a.s.add_node(node_type, {
            "grounding": 1.0, "expected_value": expected_value,
            "residual_cost": 0.1, "consequence": 0.1, "novelty": 0.1,
        })
        a.inner.add_edge_unchecked(manifold, relation, source)
        source_nodes.append(source)

    d = materialize_from_live_thought_manifold(a, goal=goal, manifold=manifold)
    candidates = list(a.inner.neighbours(d, "has_candidate"))
    assert len(candidates) == 4
    assert a.s.node(d)["attrs"]["candidate_source"] == "live_thought_manifold"
    assert a.s.node(d)["attrs"]["source_candidate_count"] == 4.0
    assert {a.s.node(c)["attrs"]["source_relation"] for c in candidates} == {
        row[0] for row in sources
    }
    assert all(list(a.inner.neighbours(c, "derived_from_evidence"))
               for c in candidates)

    a.inner.run_rules()
    assert a.s.node(d)["attrs"]["status"] == "selected"
    selection = list(a.inner.neighbours(d, "has_selection"))
    assert len(selection) == 1
    # Native arbitration chose the winner; the adapter never did.
    winner_id = a.s.node(selection[0])["attrs"]["selected_candidate_id"]
    assert winner_id == "has_goal_evidence:" + str(source_nodes[0])


def test_empty_live_thought_manifold_is_native_no_candidate():
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    manifold = a.s.add_node("ThoughtManifold", {"manifold_id": "live-empty"})
    d = materialize_from_live_thought_manifold(a, goal=_goal(a), manifold=manifold)
    a.inner.run_rules()
    assert a.s.node(d)["attrs"]["candidate_source"] == "live_thought_manifold"
    assert a.s.node(d)["attrs"]["source_candidate_count"] == 0.0
    assert a.s.node(d)["attrs"]["status"] == "no_candidate"
    assert not list(a.inner.neighbours(d, "has_selection"))


def test_live_manifold_adapter_has_no_python_outcome_selection():
    tree = ast.parse(inspect.getsource(materialize_from_live_thought_manifold))
    forbidden = {"sorted", "sort", "max", "min", "argmax", "argmin"}
    calls = {n.func.id for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not calls.intersection(forbidden)


@pytest.mark.parametrize(
    "family,relation,kind",
    [
        ("action", "has_goal_evidence", "action"),
        ("repair", "has_repair_evidence", "repair"),
        ("social", "has_stance_evidence", "social_action"),
        ("information", "has_goal_evidence", "answer"),
    ],
)
def test_live_manifold_task_families_preserve_grounded_native_lifecycle(
        family, relation, kind):
    """Every task family must retain the same graph-native lifecycle trace.

    The family label changes the upstream cognitive evidence and candidate
    kind only.  Generation remains provenance transport; native rules must
    still perform collapse, execution, settle-back, and counterfactual
    accounting.  This deliberately checks graph facts rather than reply
    text, so the coverage remains language-agnostic.
    """
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    goal = _goal(a)
    manifold = a.s.add_node("ThoughtManifold", {"manifold_id": f"family-{family}"})

    winner = a.s.add_node("TaskEvidence", {
        "candidate_id": f"{family}-winner",
        "kind": kind,
        "grounding": 1.0,
        "expected_value": 0.9,
        "residual_cost": 0.1,
        "consequence": 0.6,
        "novelty": 0.2,
        "execution_ready": 1.0,
        "outcome_status": "resolved",
        "evidence_path": f"manifold->{family}->winner",
    })
    alternative = a.s.add_node("TaskEvidence", {
        "candidate_id": f"{family}-alternative",
        "kind": kind,
        "grounding": 1.0,
        "expected_value": 0.4,
        "residual_cost": 0.2,
        "consequence": 0.1,
        "novelty": 0.1,
        "execution_ready": 0.0,
        "outcome_status": "pending",
        "evidence_path": f"manifold->{family}->alternative",
    })
    a.inner.add_edge_unchecked(manifold, relation, winner)
    a.inner.add_edge_unchecked(manifold, relation, alternative)

    d = materialize_from_live_thought_manifold(
        a, goal=goal, manifold=manifold, epoch=family.__hash__() & 0x7FFFFFFF,
    )
    ledger = {
        a.s.node(c)["attrs"]["candidate_id"]: c
        for c in a.inner.neighbours(d, "has_candidate")
    }
    winner_id = f"{relation}:{family}-winner"
    alternative_id = f"{relation}:{family}-alternative"
    assert set(ledger) == {winner_id, alternative_id}
    assert all(list(a.inner.neighbours(c, "derived_from_evidence"))
               for c in ledger.values())
    assert all(a.s.node(c)["attrs"]["source_relation"] == relation
               for c in ledger.values())

    a.inner.run_rules()

    assert a.s.node(d)["attrs"]["status"] == "resolved"
    assert a.s.node(d)["attrs"]["candidate_trace_complete"] == 1.0
    assert a.s.node(d)["attrs"]["settle_back_trace"] == 1.0
    selections = list(a.inner.neighbours(d, "has_selection"))
    settlements = list(a.inner.neighbours(d, "has_settlement"))
    credits = list(a.inner.neighbours(d, "has_counterfactual_credit"))
    assert len(selections) == len(settlements) == len(credits) == 1
    assert a.s.node(selections[0])["attrs"]["selected_candidate_id"] == \
        winner_id
    assert a.s.node(settlements[0])["attrs"]["candidate_id"] == \
        winner_id
    credit = a.s.node(credits[0])["attrs"]
    assert credit["selected_candidate_id"] == winner_id
    assert credit["rejected_candidate_id"] == alternative_id
    assert credit["counterfactual_status"] == "unexecuted_alternative"
    assert credit["winner_margin"] > 0.0
    assert credit["counterfactual_credit"] < 0.0
    assert a.s.node(ledger[winner_id])["attrs"]["status"] == "resolved"
    assert a.s.node(ledger[alternative_id])["attrs"]["status"] == "rejected"


def test_live_fact_continuation_is_selected_and_released_by_phase4a():
    a = WorldAdapter(seeds=())
    fact = a.learn_fact({"is_a": {"left": "moon", "right": "rock"}})
    inbound = a.receive_utterance("The moon looks bright", "statement")

    reply = a._deliberate_turn_continuation(
        inbound, "The moon looks bright")

    assert reply == "moon is_a rock"
    deliberations = [d for d in a.s.nodes("Deliberation")
                     if inbound in a.inner.neighbours(
                         d, "generated_from_message")]
    assert len(deliberations) == 1
    d = deliberations[0]
    assert a.s.node(d)["attrs"]["status"] == "selected"
    assert a.s.node(d)["attrs"]["candidate_trace_complete"] == 1.0
    selections = list(a.inner.neighbours(d, "has_selection"))
    assert len(selections) == 1
    winners = list(a.inner.neighbours(selections[0], "selects_candidate"))
    assert len(winners) == 1
    winner = winners[0]
    attrs = a.s.node(winner)["attrs"]
    assert attrs["kind"] == "turn_continuation_direct_fact"
    assert attrs["policy_source"] == "seed:grounded_fact_continuation"
    assert attrs["status"] == "selected"
    assert attrs["surface"] == reply
    assert list(a.inner.neighbours(winner, "derived_from_evidence")) == [fact]

    receipts = [node for node in a.s.nodes("ProductionGateReceipt")
                if a.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)
                and a.s.node(node)["attrs"].get("surface") == reply]
    assert len(receipts) == 1
    receipt = receipts[0]
    assert a.s.node(receipt)["attrs"]["status"] == "released"
    assert list(a.inner.neighbours(receipt, "releases")) == [winner]


def test_live_fact_continuation_fails_closed_without_native_policy():
    a = WorldAdapter(seeds=())
    a.learn_fact({"is_a": {"left": "moon", "right": "rock"}})
    inbound = a.receive_utterance("The moon looks bright", "statement")
    a._ensure_live_deliberation_seeds = lambda: False

    reply = a._deliberate_turn_continuation(
        inbound, "The moon looks bright")

    assert reply is None
    assert not [node for node in a.s.nodes("ProductionGateReceipt")
                if a.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]


def test_transitive_continuation_candidates_collapse_natively_and_release_winner():
    a = WorldAdapter(seeds=())
    poodle = a.s.add_node("Concept", {"name": "poodle"})
    dog = a.s.add_node("Concept", {"name": "dog"})
    mammal = a.s.add_node("Concept", {"name": "mammal"})
    a.inner.add_edge_unchecked(poodle, "causal_influence", dog)
    a.inner.add_edge_unchecked(dog, "causal_influence", mammal)
    inbound = a.receive_utterance("The poodle is clever", "user")

    reply = a._deliberate_turn_continuation(
        inbound, "The poodle is clever")

    assert reply == "Indeed, poodle relates to mammal."
    deliberation = next(d for d in a.s.nodes("Deliberation")
                        if inbound in a.inner.neighbours(
                            d, "generated_from_message"))
    assert a.s.node(deliberation)["attrs"]["status"] == "selected"
    trace = a.reply_turn_trace(int(inbound.value))
    assert len(trace["deliberations"]) == 1
    assert trace["deliberations"][0]["id"] == int(deliberation.value)
    assert len(trace["deliberations"][0]["candidates"]) >= 2
    candidates = list(a.inner.neighbours(deliberation, "has_candidate"))
    assert len(candidates) >= 2
    winner = next(candidate for selection in a.inner.neighbours(
        deliberation, "has_selection")
        for candidate in a.inner.neighbours(selection, "selects_candidate"))
    winner_attrs = a.s.node(winner)["attrs"]
    assert winner_attrs["kind"] == "turn_continuation_transitive_relation"
    assert winner_attrs["decision_depth"] == "deep"
    assert winner_attrs["policy_source"] == \
        "seed:transitive_relation_continuation"
    assert winner_attrs["valuation_basis"] == "authored_family_prior"
    assert all(key not in winner_attrs for key in
               ("residual_cost", "consequence", "novelty"))
    assert winner_attrs["surface"] == reply
    rejected = [a.s.node(candidate)["attrs"] for candidate in candidates
                if candidate != winner]
    assert rejected and all(
        attrs.get("status") == "rejected"
        and attrs.get("rejection_reason") == "outcompeted_by_native_collapse"
        for attrs in rejected)

    receipt = next(node for node in a.s.nodes("ProductionGateReceipt")
                   if a.s.node(node)["attrs"].get("turn_message_id")
                   == int(inbound.value))
    assert a.s.node(receipt)["attrs"]["surface"] == reply
    assert list(a.inner.neighbours(receipt, "releases")) == [winner]
