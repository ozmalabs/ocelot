"""A missing faculty is self-authored; a build wall targets meta-faculties."""
from __future__ import annotations

import json
from pathlib import Path

from domains import faculty_autogenesis
from scripts.gen_faculty_autogenesis_seed import manifest
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]


def _edge(agent, src, edge_type, tgt):
    agent.inner.add_edge_unchecked(src, edge_type, tgt)


def test_faculty_autogenesis_seed_regenerates_integer_only():
    committed = json.loads(
        (ROOT / "seeds" / "faculty_autogenesis.json").read_text()
    )
    generated = manifest()
    assert generated == committed

    def visit(value):
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(generated)


def test_missing_humanoid_discriminator_is_authored_and_installed_live():
    agent = WorldAdapter(seeds=("metacognitive_program_discrimination",))
    assert agent.inner.neighbours(agent.agent, "holds_faculty") == []
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)

    faculty_autogenesis.pump(agent)
    receipts = list(agent.s.nodes("NativeFacultyAutogenesisReceipt"))
    assert len(receipts) == 1
    receipt_attrs = agent.s.node(receipts[0])["attrs"]
    assert receipt_attrs["provenance"] == (
        "native_rule_readback:faculty_autogenesis")
    assert receipt_attrs["outcome_source"] == "native_rule_readback"
    assert receipt_attrs["python_outcome_selection"] is False
    needs = agent.inner.neighbours(agent.agent, "has_faculty_need")
    assert len(needs) == 1
    assert agent.s.node(needs[0])["attrs"]["status"] == "installed"
    held = agent.inner.neighbours(agent.agent, "holds_faculty")
    assert len(held) == 1
    attrs = agent.s.node(held[0])["attrs"]
    assert attrs["faculty_kind"] == "threshold_classifier"
    assert attrs["self_authored"] == 1
    assert agent.s.node(needs[0])["attrs"]["status"] == "installed"
    assert agent.inner.neighbours(needs[0], "installed_faculty") == held

    root = agent.inner.neighbours(held[0], "ir_subgraph")[0]
    result = agent.inner.evaluate({
        "type": "ProgEval",
        "prog": {"type": "Var", "name": "program"},
        "env": {"type": "Var", "name": "inputs"},
        "oracles": None,
        "fuel": 10000,
        "field": "result",
    }, {
        "program": root,
        "inputs": {
            "processed": 21, "progress": 2,
            "threshold": 10, "micros": 9,
        },
    })
    assert result == 9


def test_unbuildable_faculty_opens_meta_faculty_self_modification_plan():
    agent = WorldAdapter(seeds=("faculty_autogenesis",))
    need = agent.s.add_node("FacultyNeed", {
        "status": "requested",
        "kind": "contradictory_classifier",
        "program_name": "contradictory",
        "request": "write a function contradictory that returns the expected value",
        "order_n": 1,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(agent, agent.agent, "has_faculty_need", need)
    for ordinal, expected in enumerate((0, 1)):
        example = agent.s.add_node("FacultyExample", {
            "ordinal": ordinal,
            "inputs_json": '{"x":1}',
            "expected": expected,
            "output_authority": 0,
            "integer_native": 1,
        })
        _edge(agent, need, "has_faculty_example", example)

    faculty_autogenesis.pump(agent)
    assert agent.s.node(need)["attrs"]["status"] == "repairing_meta_faculty"
    gaps = agent.inner.neighbours(need, "has_meta_faculty_gap")
    concerns = agent.inner.neighbours(need, "has_authoring_self_concern")
    assert len(gaps) == len(concerns) == 1
    assert agent.s.node(gaps[0])["attrs"]["order_n"] == 2
    assert agent.s.node(gaps[0])["attrs"]["kind"] == "faculty_authoring_failure"
    plans = agent.inner.neighbours(
        concerns[0], "has_program_self_change_plan"
    )
    assert len(plans) == 1
    assert agent.s.node(plans[0])["attrs"]["status"] == "active"
