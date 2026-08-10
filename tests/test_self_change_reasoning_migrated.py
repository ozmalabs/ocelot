"""Graph-native gates for proof-carrying self-change diagnosis.

The fixture is blind to the graph: it supplies observations and measurements,
not an expected diagnosis.  Python here is only the experimental world adapter:
it ingests measurements and reads the graph's verdict.
"""
from __future__ import annotations

import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

from substrate.world_adapter import WorldAdapter  # noqa: E402


SEED = os.path.join(ROOT, "seeds", "self_change_reasoning.json")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "self_change_blind_faults.json")
SCHEMA = os.path.join(ROOT, "schemas", "self_change_protocol.schema.json")

EXPECTED = {
    "fn_threshold_001": "threshold_adjustment",
    "fp_context_002": "guard_strengthening",
    "missing_relation_003": "relation_addition",
    "wrong_effect_004": "effect_substitution",
    "runaway_noop_005": "firing_budget_guard",
    "ambiguous_minimal_006": "threshold_adjustment",
}


def _attrs(agent, node):
    return agent.s.node(node)["attrs"]


def _nodes(agent, node_type, **attrs):
    return [
        node
        for node in agent.s.nodes(type=node_type)
        if all(_attrs(agent, node).get(key) == value for key, value in attrs.items())
    ]


def _out(agent, node, edge_type):
    return list(agent.inner.neighbours(node, edge_type))


def _agent():
    agent = WorldAdapter(seeds=())
    with open(SEED, encoding="utf-8") as fh:
        agent.inner.load_seed_manifest(json.load(fh), agent.agent)
    return agent


def _probe_attrs(case):
    attrs = {
        "case_id": case["case_id"],
        "target_uid": 1001,
        "expected_revision": 0,
        "baseline_hash": 12345,
        "live_clause": {"type": "Lit", "value": True},
        "change_opened": 0,
    }
    attrs.update(case["signals"])
    # These are candidate representations, not labels.  Every fixture receives
    # the same family vocabulary; its observations determine which are proposed.
    attrs.update({
        "threshold_adjustment_clause": {
            "type": "Gte",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "signal"},
            "b": {"type": "Lit", "value": 1},
        },
        "guard_strengthening_clause": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "context_ok"},
            "b": {"type": "Lit", "value": 1},
        },
        "relation_addition_clause": {"type": "Lit", "value": True},
        "effect_substitution_clause": [
            ["set_attr", "x", "outcome", "corrected"],
        ],
        "firing_budget_guard_clause": {
            "type": "Lt",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "handled"},
            "b": {"type": "Lit", "value": 1},
        },
    })
    return attrs


def _open_case(case):
    agent = _agent()
    probe = agent.s.add_node("FaultProbe", _probe_attrs(case))
    agent.inner.add_edge_unchecked(agent.agent, "observes_fault_probe", probe)
    agent.s.tick()
    changes = _nodes(agent, "SelfChange", case_id=case["case_id"])
    assert len(changes) == 1
    return agent, changes[0]


def _ingest_measured_arms(agent, change, case):
    patches = _out(agent, change, "has_patch")
    assert patches, "the graph must propose at least one structurally admissible patch"
    noop = agent.s.add_node("TrialEvidence", {
        "arm": "no_op",
        "causal_gain": case["noop_gain"],
    })
    placebo = agent.s.add_node("TrialEvidence", {
        "arm": "same_size_placebo",
        "causal_gain": case["placebo_gain"],
    })
    noop_arm = _out(agent, change, "has_noop_control")
    placebo_arm = _out(agent, change, "has_placebo_control")
    assert len(noop_arm) == len(placebo_arm) == 1
    agent.inner.add_edge_unchecked(noop_arm[0], "has_evidence", noop)
    agent.inner.add_edge_unchecked(placebo_arm[0], "has_evidence", placebo)
    for patch in patches:
        family = _attrs(agent, patch)["family"]
        ev = agent.s.add_node("TrialEvidence", {
            "arm": "candidate",
            "causal_gain": case["evidence"].get(family, 0),
            "protected_regressions": 0,
            "resource_cost": 1,
            "resource_budget": 3,
            "replications": 3,
            "replicated_gain": case["evidence"].get(family, 0),
        })
        agent.inner.add_edge_unchecked(patch, "candidate_evidence", ev)
    agent.s.tick()


def test_fixture_contains_no_answer_key():
    with open(FIXTURE, encoding="utf-8") as fh:
        raw = json.load(fh)
    blob = json.dumps(raw).lower()
    for forbidden in ("expected_family", "correct_family", "answer_key"):
        assert forbidden not in blob
    assert len(raw["cases"]) == 7


def test_stage_schema_and_proof_burden_are_explicit_graph_data():
    with open(SEED, encoding="utf-8") as fh:
        seed = json.load(fh)
    blob = json.dumps(seed)
    for node_type in (
        "ObservedGap", "CausalHypothesis", "ChangeSpec", "RulePatch",
        "ProofObligation", "Trial", "Canary", "Commit", "Abort",
        "Consolidation",
    ):
        assert node_type in blob
    for proof in (
        "causal_gain", "protected_invariants", "beats_no_op_control",
        "beats_same_size_placebo", "resource_budget", "replication",
    ):
        assert proof in blob
    assert '"apply_rule_patch"' in blob

    with open(SCHEMA, encoding="utf-8") as fh:
        schema = json.load(fh)
    assert schema["$schema"].endswith("2020-12/schema")
    node_types = schema["properties"]["type"]["enum"]
    assert set(node_types) >= {
        "ObservedGap", "CausalHypothesis", "ChangeSpec", "RulePatch",
        "ProofObligation", "Trial", "Canary", "Commit", "Abort",
        "Consolidation",
    }
    patch_branch = schema["allOf"][0]["then"]["properties"]["attrs"]
    assert {
        "target_uid", "expected_revision", "expected_content_hash",
        "field", "proposed_clause", "mdl_cost", "blast_radius", "status",
    } <= set(patch_branch["required"])


def test_blinded_faults_are_diagnosed_and_minimal_proven_patch_selected():
    with open(FIXTURE, encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    for case in cases:
        if case["case_id"] not in EXPECTED:
            continue
        agent, change = _open_case(case)
        _ingest_measured_arms(agent, change, case)

        selected = _out(agent, change, "selected_patch")
        assert len(selected) == 1, case["case_id"]
        patch = selected[0]
        assert _attrs(agent, patch)["family"] == EXPECTED[case["case_id"]]
        assert _attrs(agent, patch)["proofs_passed"] == 1
        assert len(_out(agent, patch, "has_trial")) == 1
        assert len(_out(agent, patch, "has_canary")) == 1


def test_controls_can_falsify_every_candidate_and_force_honest_abort():
    with open(FIXTURE, encoding="utf-8") as fh:
        case = next(
            row for row in json.load(fh)["cases"]
            if row["case_id"] == "correlation_only_007"
        )
    agent, change = _open_case(case)
    _ingest_measured_arms(agent, change, case)
    assert _out(agent, change, "selected_patch") == []

    batch = agent.s.add_node("EvidenceBatch", {"status": "closed"})
    agent.inner.add_edge_unchecked(change, "evidence_batch", batch)
    agent.s.tick()

    aborts = _out(agent, change, "has_abort")
    assert len(aborts) == 1
    assert _attrs(agent, aborts[0])["reason"] == "no_causally_supported_patch"
    assert _attrs(agent, change)["status"] == "aborted"


def test_failed_canary_aborts_without_touching_the_parent_rule():
    with open(FIXTURE, encoding="utf-8") as fh:
        case = json.load(fh)["cases"][0]
    agent, change = _open_case(case)
    _ingest_measured_arms(agent, change, case)
    patch = _out(agent, change, "selected_patch")[0]
    canary = _out(agent, patch, "has_canary")[0]
    evidence = agent.s.add_node("CanaryEvidence", {
        "replicated_gain": 20,
        "protected_regressions": 1,
        "replications": 3,
    })
    agent.inner.add_edge_unchecked(canary, "has_canary_evidence", evidence)
    agent.s.tick()

    abort = _out(agent, change, "has_abort")
    assert len(abort) == 1
    assert _attrs(agent, abort[0])["stage"] == "canary"
    assert _attrs(agent, abort[0])["rollback_required"] == 0
    assert _attrs(agent, patch)["status"] == "proposed"


def test_generator_is_authoring_only_and_contains_no_substrate_decision_loop():
    source = open(
        os.path.join(ROOT, "scripts", "gen_self_change_reasoning_seed.py"),
        encoding="utf-8",
    ).read()
    for forbidden in (
        "WorldAdapter", "substrate_rs", ".tick(", ".run_rules(",
        ".add_node(", ".add_edge(",
    ):
        assert forbidden not in source
