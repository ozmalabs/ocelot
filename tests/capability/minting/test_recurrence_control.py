"""Deterministic controls for accumulated predicate-count recurrence.

This test locks the current predicate-only candidate identity contract: residual
signature tuples ``(dimension, predicate, k)`` are projected to ``predicate``
before recurrence counting and minting. It is not evidence for complete-tuple
identity; a future change to tuple identity must rewrite these controls and add
a same-predicate/different-dimension-or-k split case.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))

import substrate_runner as R  # noqa: E402
from domains import minting_train_of_thought as mtot  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402


P = "test"
PT = frozenset({("test:recurrence", P, 1)})
EMPTY = frozenset()
_SELF_EXPERIMENT_OBS = [
    ["test", "HYPOTHESIS", "about", "SELF"],
    ["vary", "SEED", "by", "DELTA"],
    ["send", "VARIANT", "to", "WORLD"],
    ["judge", "TRIAL", "by", "OUTCOME"],
]


def _build_replay(monkeypatch: pytest.MonkeyPatch, residuals: list[frozenset]):
    """Build one fresh native substrate and replay exactly one residual per segment."""
    fixture = R.load_fixture()
    items = fixture["categories"]["bird"]
    substrate, nodes, proto = R.build_category("bird", items)
    observer = R.observer(substrate, "recurrence_control", R.FINE)
    spy = R.AskSpy()
    reached_topics = [name for name in nodes if name != proto][:len(residuals)]
    assert len(reached_topics) == len(residuals)

    state = {"segment": -1}

    def controlled_segment(*_args, **_kwargs):
        state["segment"] += 1
        return {
            "topics_thought": [reached_topics[state["segment"]]],
            "recovered_total": [],
            "stop_reason": None,
        }

    residual_iter = iter(residuals)

    def controlled_residual(*_args, **_kwargs):
        return next(residual_iter)

    gate_calls: list[dict] = []
    real_induce = mtot.rf.induce_concern

    def recording_induce(*args, **kwargs):
        result = real_induce(*args, **kwargs)
        gate_calls.append({
            "segment": state["segment"],
            "observation": kwargs.get("observation", args[1] if len(args) > 1 else None),
            "name_hint": kwargs.get("name_hint"),
            "result": result,
        })
        return result

    monkeypatch.setattr(mtot.tot, "run_inner_conversation", controlled_segment)
    monkeypatch.setattr(mtot, "_residual_tuples", controlled_residual)
    monkeypatch.setattr(mtot.rf, "induce_concern", recording_induce)
    return substrate, proto, observer, spy, gate_calls


def _run_replay(monkeypatch: pytest.MonkeyPatch, residuals: list[frozenset]):
    substrate, proto, observer, spy, gate_calls = _build_replay(monkeypatch, residuals)
    result = mtot.run_minting_train_of_thought(
        substrate,
        topic=proto,
        setpoint_observer=observer,
        setpoint_topic=proto,
        width0=2,
        turns_per_segment=1,
        max_segments=3,
        mint_after_quanta=2,
        deviation_wide_quanta=99,
        deviation_converge_quanta=-1,
        on_unknown="return",
        ask_fn=spy,
    )
    receipts = list(substrate.nodes("NativeMintingTrainReceipt"))
    assert receipts
    assert all(substrate.node(n)["attrs"]["outcome_source"] ==
               "native_rule_readback" for n in receipts)
    assert all(substrate.node(n)["attrs"]["python_outcome_selection"] is False
               for n in receipts)
    return substrate, observer, spy, result, gate_calls


@pytest.mark.parametrize(
    ("residuals", "expected_trace", "expected_count", "expected_due_segment"),
    [
        ([PT, PT, PT], [[P], [P], [P]], 3, 1),
        ([PT, EMPTY, EMPTY], [[P], [], []], 1, None),
        ([PT, EMPTY, PT], [[P], [], [P]], 2, 2),
    ],
    ids=["continuous-recurrence", "one-exposure-below-threshold", "interrupted-recurrence"],
)
def test_accumulated_recurrence_matched_traces(
        monkeypatch, residuals, expected_trace, expected_count, expected_due_segment):
    substrate, observer, spy, result, gate_calls = _run_replay(monkeypatch, residuals)

    assert substrate.node(observer)["attrs"]["grain"] == R.FINE
    assert result["width_trace"] == [2, 2, 2]
    assert result["residual_trace"] == expected_trace
    assert result["residual_persistence"] == {P: expected_count}
    assert spy.calls == []

    if expected_due_segment is None:
        assert result["mint_events"] == []
        assert result["minted_axes"] == []
        assert gate_calls == []
        return

    assert len(result["mint_events"]) == 1
    event = result["mint_events"][0]
    assert event["predicate"] == P
    assert event["persistence"] == 2
    assert event["minted"] is True
    assert len(result["minted_axes"]) == 1
    assert result["minted_axes"][0]
    # Native mrl_offer_due_once, not the Python adapter, creates the Observation.
    assert gate_calls == []
    assert event["offered_at_segment"] == expected_due_segment


def test_recurrence_eligible_duplicate_is_not_reminted(monkeypatch):
    substrate, proto, observer, spy, gate_calls = _build_replay(monkeypatch, [PT, PT, PT])
    original = rf.induce_concern(
        substrate, [[P]], name_hint="minted_" + rf._key_component(P))
    assert original["minted"] is True
    original_axis_id = original["axis_id"]
    axis_ids_before = {str(node) for node in substrate.nodes("CapabilityAxis")}
    gate_calls.clear()  # exclude the deliberate pre-mint from the replay trace

    result = mtot.run_minting_train_of_thought(
        substrate,
        topic=proto,
        setpoint_observer=observer,
        setpoint_topic=proto,
        width0=2,
        turns_per_segment=1,
        max_segments=3,
        mint_after_quanta=2,
        deviation_wide_quanta=99,
        deviation_converge_quanta=-1,
        on_unknown="return",
        ask_fn=spy,
    )

    assert result["width_trace"] == [2, 2, 2]
    assert result["residual_trace"] == [[P], [P], [P]]
    assert result["residual_persistence"] == {P: 3}
    assert spy.calls == []
    assert gate_calls == []
    assert len(result["mint_events"]) == 1
    event = result["mint_events"][0]
    assert event["offered_at_segment"] == 1
    assert event["predicate"] == P
    assert event["persistence"] == 2
    assert event["minted"] is False
    assert event["covered_by_existing_axis"] == original_axis_id
    assert result["minted_axes"] == []
    assert {str(node) for node in substrate.nodes("CapabilityAxis")} == axis_ids_before


def test_recurrence_minted_axis_reaches_native_authored_operation(monkeypatch):
    substrate, proto, observer, spy, gate_calls = _build_replay(monkeypatch, [PT, PT, PT])
    agent = next(iter(substrate.nodes("Agent")))
    summary = substrate.load_seed_manifest(manifest_for("relation_vocabulary"), agent)
    assert not summary.get("rules_skipped"), summary

    bootstrap = rf.induce_concern(
        substrate, _SELF_EXPERIMENT_OBS, name_hint="recurrence_experiment_concern")
    assert bootstrap["minted"] is True
    grounded = rf.ground_concern(substrate, [bootstrap["capability_key"]])
    assert grounded["grounded"] is True
    assert grounded["served_by"] == "graph"
    assert grounded["path"] == "compose_experiment_rule"
    rule_name = "author_experiment_from_residual_" + bootstrap["capability_key"]
    native_rule_names = {
        rule.get("name") for rule in substrate.export_rules() if isinstance(rule, dict)
    }
    assert rule_name in native_rule_names
    active_rule = next(rule for rule in grounded["rules"] if rule["name"] == rule_name)
    active_where = json.dumps(active_rule["where"], sort_keys=True)
    assert "capability_keys" not in active_where
    assert "residual_predicates" not in active_where
    gate_calls.clear()  # exclude the deliberate composer bootstrap from replay tracing

    world = substrate.add_node(
        "WorldInstance", {"world_type": "Game", "world_id": "game", "name": "navigate"})
    substrate.add_edge_unchecked(agent, "knows", world)
    experiment_ids_before = {str(node) for node in substrate.nodes("Experiment")}

    result = mtot.run_minting_train_of_thought(
        substrate,
        topic=proto,
        setpoint_observer=observer,
        setpoint_topic=proto,
        width0=2,
        turns_per_segment=1,
        max_segments=3,
        mint_after_quanta=2,
        deviation_wide_quanta=99,
        deviation_converge_quanta=-1,
        on_unknown="return",
        ask_fn=spy,
    )

    assert result["width_trace"] == [2, 2, 2]
    assert result["residual_trace"] == [[P], [P], [P]]
    assert spy.calls == []
    assert gate_calls == []
    assert result["mint_events"][0]["offered_at_segment"] == 1
    assert len(result["minted_axes"]) == 1
    recurrence_axis_id = result["minted_axes"][0]
    recurrence_axis = next(
        node for node in substrate.nodes("CapabilityAxis") if str(node) == recurrence_axis_id)

    # The recurrence-minted axis can itself be grounded into a graph-authored
    # operation; this uses its graph-resident minted observation/provenance, not a
    # Python recurrence call or synthetic axis.
    recurrence_grounded = rf.ground_concern(substrate, ["minted_" + rf._key_component(P)])
    assert recurrence_grounded["grounded"] is True
    substrate.run_rules()
    new_experiment_ids = {str(node) for node in substrate.nodes("Experiment")} - experiment_ids_before
    assert new_experiment_ids
    tested_by = {str(node) for node in substrate.neighbours(recurrence_axis, "tested_by")}
    assert tested_by & new_experiment_ids
    experiment_id = next(iter(tested_by & new_experiment_ids))
    experiment = next(node for node in substrate.nodes("Experiment") if str(node) == experiment_id)
    attrs = substrate.node(experiment)["attrs"]
    assert attrs["status"] in {"requested", "counterfactual_requested"}
    assert attrs["axis_tag"]

    experiment_ids_after = {str(node) for node in substrate.nodes("Experiment")}
    substrate.run_rules()
    assert {str(node) for node in substrate.nodes("Experiment")} == experiment_ids_after
