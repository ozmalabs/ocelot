"""Gates for the unified programming -> metacognition -> self-change path."""
from __future__ import annotations

import json
from pathlib import Path

from substrate.world_adapter import WorldAdapter
from scripts.gen_program_self_modification_seed import manifest


ROOT = Path(__file__).resolve().parents[1]


def attrs(agent, node):
    return agent.s.node(node)["attrs"]


def out(agent, node, edge):
    return list(agent.inner.neighbours(node, edge))


def floats(value, path=()):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(floats(child, path + (key,)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(floats(child, path + (index,)))
    elif isinstance(value, float):
        found.append((path, value))
    return found


def agent_with_faculties():
    agent = WorldAdapter(seeds=())
    for seed_id in (
        "dual_process_core", "cognitive_pareto", "metacognitive_learning",
        "self_repair", "self_change_reasoning", "program_self_modification",
    ):
        payload = json.loads((ROOT / "seeds" / f"{seed_id}.json").read_text())
        agent.inner.load_seed_manifest(payload, agent.agent)
    return agent


def test_program_self_modification_and_self_change_are_integer_only():
    for seed_id in ("program_self_modification", "self_change_reasoning"):
        payload = json.loads((ROOT / "seeds" / f"{seed_id}.json").read_text())
        assert floats(payload) == []


def test_program_self_modification_seed_regenerates_identically():
    committed = json.loads(
        (ROOT / "seeds" / "program_self_modification.json").read_text()
    )
    assert manifest() == committed


def test_program_gap_opens_plan_and_measured_probe_enters_self_change():
    agent = agent_with_faculties()
    concern = agent.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": "code_write",
        "content": "learn a missing deterministic program transformation",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
    agent.s.tick()

    plans = out(agent, concern, "has_program_self_change_plan")
    requests = out(agent, concern, "requests_program_self_change_probe")
    assert len(plans) == len(requests) == 1
    plan = plans[0]
    assert attrs(agent, plan)["integer_native"] == 1
    assert out(agent, plan, "has_active_metacognitive_learning_policy")

    measurement = agent.s.add_node("ProgramGapMeasurement", {
        "status": "observed", "materialized": 0,
        "case_id": "program_gap_1", "target_uid": 1001,
        "expected_revision": 0, "baseline_hash": 12345,
        "live_clause": {"type": "Lit", "value": True},
        "false_negative": 2, "threshold_sensitivity": 1,
        "threshold_adjustment_clause": {
            "type": "Gte",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "x"},
                  "key": "signal"},
            "b": {"type": "Lit", "value": 1},
        },
    })
    agent.inner.add_edge_unchecked(
        requests[0], "has_program_gap_measurement", measurement
    )
    # The faculties are independently scheduled: bridge -> self-change ->
    # bridge binding may occupy successive fixpoint cycles.
    for _ in range(3):
        agent.s.tick()

    probes = out(agent, requests[0], "materialized_as_fault_probe")
    changes = out(agent, plan, "has_program_self_change")
    assert len(probes) == len(changes) == 1
    assert attrs(agent, probes[0])["integer_native"] == 1
    assert attrs(agent, changes[0])["status"] == "diagnosing"
