"""Preregistered controls for the fully graph-native discovery demonstration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from domains import analogy_search, minting_train_of_thought, reflective_faculty, regulated_train_of_thought, train_of_thought
from domains.autonomous_discovery import (
    OPAQUE_LABEL_KEYS, PROHIBITED_ADAPTER_NODE_TYPES, adapter_audit, boot_native, counts,
    external_callbacks, graph_snapshot, load_fixture, rule_inventory, settle_native,
    structural_graph_snapshot, submit_held_out_operation, submit_preregistered_case,
)
from substrate.boot_core import load_seeds_into


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = load_fixture(ROOT / "tests/capability/minting/fixtures/autonomous_discovery_preregistered.json")


def _raise_historical(*_args, **_kwargs):
    raise AssertionError("historical Python controller must not run in autonomous discovery")


@pytest.fixture
def prohibited_python(monkeypatch):
    """Make every prohibited historical trajectory/semantic route loudly unavailable."""
    monkeypatch.setattr(minting_train_of_thought, "run_minting_train_of_thought", _raise_historical)
    monkeypatch.setattr(minting_train_of_thought, "_residual_tuples", _raise_historical)
    monkeypatch.setattr(minting_train_of_thought, "_residual_predicates", _raise_historical)
    monkeypatch.setattr(minting_train_of_thought, "_post_segment_evidence", _raise_historical)
    monkeypatch.setattr(train_of_thought, "run_inner_conversation", _raise_historical)
    monkeypatch.setattr(regulated_train_of_thought, "_admitted_signature", _raise_historical)
    monkeypatch.setattr(analogy_search, "concept_signature", _raise_historical)
    monkeypatch.setattr(reflective_faculty, "induce_concern", _raise_historical)


def _run(case_name: str):
    substrate, agent = boot_native()
    state = submit_preregistered_case(substrate, agent, case_name=case_name, fixture=FIXTURE)
    initial = graph_snapshot(substrate)
    settle_native(substrate)
    settled = graph_snapshot(substrate)
    held_out = submit_held_out_operation(substrate, agent, state)
    settle_native(substrate)
    return substrate, agent, state, held_out, initial, settled


def _episode(substrate):
    episodes = substrate.nodes("DiscoveryEpisode")
    assert len(episodes) == 1
    return episodes[0]


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(_strings(key) | _strings(item) for key, item in value.items())) if value else set()
    if isinstance(value, (list, tuple)):
        return set().union(*(_strings(item) for item in value)) if value else set()
    return set()


def _opaque_attr_strings(snapshot: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for node in snapshot["nodes"]:
        attrs = node["attrs"]
        for key in ("concept_id", "display_label", "entity_id", "relation_id", "request_id", "surface_label"):
            values |= _strings(attrs.get(key))
    return values


@pytest.mark.parametrize("case_name", list(FIXTURE["cases"]))
def test_preregistered_graph_native_cases(case_name, prohibited_python):
    substrate, _agent, state, held_out, _initial, _settled = _run(case_name)
    expected = FIXTURE["cases"][case_name]["expected"]
    episode = _episode(substrate)
    evidence = list(substrate.neighbours(episode, "has_residual_segment_evidence"))
    candidates = list(substrate.neighbours(episode, "has_predicate_recurrence_candidate"))
    offers = list(substrate.neighbours(episode, "has_mint_offer"))
    axes = list(substrate.neighbours(episode, "minted_axis"))

    assert len(evidence) == expected["evidence"]
    assert len(candidates) == expected["candidates"]
    assert sorted(substrate.node(candidate)["attrs"]["persistence"] for candidate in candidates) == expected.get("persistence", [])
    assert len(offers) == expected["offers"]
    assert len(axes) == expected["new_axes"]
    assert bool(substrate.node(held_out)["attrs"].get("admissible")) is expected["held_out_licensed"]
    assert bool(list(substrate.neighbours(held_out, "licensed_by"))) is expected["held_out_licensed"]
    assert bool(list(substrate.neighbours(held_out, "reachable_via"))) is expected["held_out_licensed"]
    audit = adapter_audit(substrate)
    assert audit is state["audit"]
    assert audit["raw_discovery_submissions"] == 1
    assert audit["held_out_submissions"] == 1
    assert audit["permitted_adapter_writes"] == len(audit["adapter_write_events"])
    assert audit["permitted_adapter_writes"] > 0
    assert audit["prohibited_writes"] == 0
    assert audit["callback_invocations"] == 0

    if case_name == "discovered_axis_positive":
        assert len({substrate.node(candidate)["attrs"]["recurrence_key"] for candidate in candidates}) == 1
        assert all(substrate.node(offer)["attrs"]["offer_status"] == "minted" for offer in offers)
    if case_name == "precovered_no_new_axis":
        assert substrate.node(offers[0])["attrs"]["offer_status"] == "recognized"
    if case_name == "same_predicate_different_structure_no_aggregation":
        assert len({substrate.node(candidate)["attrs"]["recurrence_key"] for candidate in candidates}) == 2


def test_adapter_blocks_derived_and_mint_status_writes_after_raw_submission():
    substrate, agent = boot_native()
    state = submit_preregistered_case(substrate, agent, case_name="discovered_axis_positive", fixture=FIXTURE)
    audit = adapter_audit(substrate)

    for node_type in PROHIBITED_ADAPTER_NODE_TYPES:
        with pytest.raises(AssertionError, match="derived node type"):
            substrate.add_node(node_type, {})
    with pytest.raises(AssertionError, match="adapter set_attr"):
        substrate.set_attr(state["request"], "offer_status", "minted")
    with pytest.raises(AssertionError, match="adapter set_attr"):
        substrate.set_attr(state["request"], "status", "minted")

    assert audit["prohibited_writes"] == len(PROHIBITED_ADAPTER_NODE_TYPES) + 2
    assert len(audit["prohibited_write_attempts"]) == audit["prohibited_writes"]
    assert all(event["phase"] == "locked" for event in audit["prohibited_write_attempts"])


def test_external_callbacks_are_raising_stubs_with_live_telemetry():
    substrate, agent = boot_native()
    submit_preregistered_case(substrate, agent, case_name="discovered_axis_positive", fixture=FIXTURE)
    callbacks = external_callbacks(substrate)
    audit = adapter_audit(substrate)

    assert set(callbacks) == {"ask", "llm", "network", "tool"}
    for name, callback in callbacks.items():
        with pytest.raises(AssertionError, match=rf"external {name} callback"):
            callback("must-not-run")
    assert audit["callback_invocations"] == len(callbacks)
    assert audit["callback_calls"] == list(callbacks)


def test_complete_opaque_bijection_has_structurally_invariant_graphs(prohibited_python):
    assert set(FIXTURE["opaque_bijection"]) == OPAQUE_LABEL_KEYS
    assert len(set(FIXTURE["opaque_bijection"].values())) == len(OPAQUE_LABEL_KEYS)

    ordinary, _agent, _state, ordinary_held_out, _initial, _settled = _run("discovered_axis_positive")
    scrambled, _agent, scrambled_state, scrambled_held_out, _initial, _settled = _run("label_scramble_structural_transfer")

    assert structural_graph_snapshot(ordinary) == structural_graph_snapshot(scrambled)
    ordinary_attrs = ordinary.node(ordinary_held_out)["attrs"]
    scrambled_attrs = scrambled.node(scrambled_held_out)["attrs"]
    assert ordinary_attrs["relation_head"] == scrambled_attrs["relation_head"]
    assert ordinary_attrs["arg1_role"] == scrambled_attrs["arg1_role"]
    assert ordinary_attrs["arg2_role"] == scrambled_attrs["arg2_role"]
    used_values = {FIXTURE["opaque_bijection"][key] for key in scrambled_state["opaque_label_keys_used"]}
    scrambled_snapshot = graph_snapshot(scrambled)
    assert used_values <= _opaque_attr_strings(scrambled_snapshot)
    assert not (set(scrambled_state["opaque_label_keys_used"]) & _opaque_attr_strings(scrambled_snapshot))


def test_idempotence_and_seed_reload_are_graph_stable(prohibited_python):
    substrate, agent, _state, _held_out, _initial, _settled = _run("idempotence_and_seed_reload")
    settle_native(substrate)
    before_rerun = graph_snapshot(substrate)
    settle_native(substrate)
    assert graph_snapshot(substrate) == before_rerun
    before_reload = graph_snapshot(substrate)
    load_seeds_into(substrate, agent, ["autonomous_discovery"])
    settle_native(substrate)
    assert graph_snapshot(substrate) == before_reload
    inventory = rule_inventory(substrate)["counts"]
    for prefix in ("ad_", "mrl_", "mrs_"):
        assert all(count == 1 for name, count in inventory.items() if name.startswith(prefix))


def test_seed_closure_contains_no_held_out_answer_or_target_axis():
    closure = "\n".join((ROOT / "seeds" / name).read_text() for name in (
        "autonomous_discovery.json", "minting_recurrence_ledger.json", "minting_recurrence_semantic_demo.json",
    ))
    assert "held_out_test_z" not in closure
    assert "precovered_structural_basis" not in closure
    assert "minted_[[\"rel:binding\"" not in closure


def test_serialized_graph_artifacts_are_json_and_have_only_native_outputs(prohibited_python):
    substrate, _agent, _state, _held_out, initial, settled = _run("discovered_axis_positive")
    json.dumps(initial, sort_keys=True)
    json.dumps(settled, sort_keys=True)
    observed = counts(substrate)
    assert observed["ResidualSegmentEvidence"] == 2
    assert observed["PredicateRecurrenceCandidate"] == 1
    assert observed["Observation"] == 1
