"""Graph-native quantity and operator-shape grounding for synthesis."""
from __future__ import annotations

import json
from pathlib import Path

import substrate_rs as srs

from domains import prog_synthesis as ps


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "program_synthesis_grounding.json"


def boot():
    substrate = srs.Substrate()
    agent = substrate.add_node("Agent", {})
    ps.ensure_program_synthesis(substrate, substrate._inner, agent)
    return substrate, agent


def solve(text, rows):
    substrate, agent = boot()
    message = ps.ingest_spec(substrate, agent, text, rows)
    ps.pump(substrate, agent)
    goal = substrate.in_neighbours(message, "about_message")[0]
    return substrate, message, goal, ps.read_goal(substrate, goal)


def eval_accepted(substrate, result, inputs):
    root = substrate.neighbours(result["program"], "ir_subgraph")[0]
    outcome = substrate._inner.evaluate({
        "type": "ProgEval",
        "prog": {"type": "Var", "name": "program"},
        "env": {"type": "Var", "name": "inputs"},
        "oracles": None,
        "fuel": 10000,
        "field": "",
    }, {"program": root, "inputs": inputs})
    assert outcome["halted"] is True and outcome["trap"] is None
    return outcome["result"]


def test_grounding_seed_is_integer_graph_data_and_loads_cleanly():
    manifest = json.loads(SEED.read_text(encoding="utf-8"))

    def assert_no_float(value):
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for child in value.values():
                assert_no_float(child)
        elif isinstance(value, list):
            for child in value:
                assert_no_float(child)

    assert_no_float(manifest)
    substrate = srs.Substrate()
    agent = substrate.add_node("Agent", {})
    summary = substrate._inner.load_seed_manifest(manifest, agent)
    assert summary["rules_skipped"] == []
    assert summary["reflexes_skipped"] == []


def test_words_ground_quantity_and_shape_build_threshold_classifier():
    text = (
        "write a function cost_excess that returns micros when processed "
        "is more than ten times progress otherwise zero"
    )
    rows = [
        ({"processed": 100, "progress": 20, "micros": 300}, 0),
        ({"processed": 201, "progress": 20, "micros": 300}, 300),
        ({"processed": 1000, "progress": 99, "micros": 7}, 7),
        ({"processed": 100, "progress": 10, "micros": 11}, 0),
    ]
    substrate, message, goal, result = solve(text, rows)

    assert result["status"] == "accepted"
    enumeration = result["enumerate"]
    assert enumeration["operator_shape"] == "thresholded_greater_branch"
    assert enumeration["ops"] == ["Times", "Gt", "IfThenElse"]
    assert enumeration["grounded_constants"] == [0, 10]
    assert enumeration["tested"] < 20000
    assert enumeration["solution_size"] == 7
    quantities = {
        substrate.node(node)["attrs"]["value"]
        for node in substrate.neighbours(message, "ps_grounds_quantity")
    }
    assert quantities == {0, 10}
    assert substrate.node(goal)["attrs"]["ps_enumerate_note"] == (
        "(micros * (processed > (progress * 10)))"
    )
    assert eval_accepted(substrate, result, {
        "processed": 501, "progress": 50, "micros": 19,
    }) == 19


def test_threshold_is_a_variable_not_a_magic_constant():
    text = (
        "write a function cost_excess that returns micros when processed "
        "is more than threshold times progress otherwise zero"
    )
    rows = [
        ({"processed": 100, "progress": 20, "micros": 300,
          "threshold": 10}, 0),
        ({"processed": 201, "progress": 20, "micros": 300,
          "threshold": 10}, 300),
        ({"processed": 61, "progress": 20, "micros": 7,
          "threshold": 3}, 7),
        ({"processed": 60, "progress": 20, "micros": 11,
          "threshold": 3}, 0),
    ]
    substrate, _message, goal, result = solve(text, rows)

    assert result["status"] == "accepted"
    assert result["enumerate"]["operator_shape"] == (
        "thresholded_greater_branch"
    )
    assert 10 not in result["enumerate"]["grounded_constants"]
    assert "threshold" in substrate.node(goal)["attrs"]["ps_enumerate_note"]
    assert eval_accepted(substrate, result, {
        "processed": 9, "progress": 4, "micros": 23, "threshold": 2,
    }) == 23
    assert eval_accepted(substrate, result, {
        "processed": 8, "progress": 4, "micros": 23, "threshold": 2,
    }) == 0


def test_quantity_vocabulary_is_teachable_graph_data():
    substrate, agent = boot()
    thirteen = substrate.add_node("SynthesisQuantityLexeme", {
        "token": "THIRTEEN",
        "value": 13,
        "source": "learned_number_lexicon",
    })
    substrate.add_edge_unchecked(
        agent, "has_synthesis_quantity_lexeme", thirteen
    )
    message = ps.ingest_spec(
        substrate,
        agent,
        "write a function threshold that returns thirteen",
        [({}, 13)],
    )
    substrate._inner.run_rules(400000)

    assert thirteen in substrate.neighbours(message, "ps_grounds_quantity")


def test_arbitrary_integer_literal_is_grounded_at_the_boundary():
    substrate, agent = boot()
    message = ps.ingest_spec(
        substrate,
        agent,
        "write a function scale that returns thirty seven times x using 37",
        [({"x": 2}, 74)],
    )
    values = [
        substrate.node(node)["attrs"]["value"]
        for node in substrate.neighbours(message, "ps_grounds_quantity")
    ]
    assert values == [37]
