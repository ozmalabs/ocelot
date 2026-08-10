"""Gates for autonomous, graph-native diagnosis of a published net."""
from __future__ import annotations

import pytest
import torch

pytest.importorskip("substrate_rs")

from domains.published_net_debugger import (
    authored_control,
    authored_conditional_patch,
    authored_patch,
    audit_no_host_decisions,
    intervention_hook,
    record_outcome,
    record_conditional_validation,
    record_gate_outcome,
    record_validation,
    requested_intervention,
    requested_gate_intervention,
    state_dict_sha256,
)
from substrate.boot_core import boot_core, load_seeds_into


def _add_edge(inner, source, edge_type, target):
    try:
        inner.add_edge_unchecked(source, edge_type, target)
    except TypeError:
        inner.add_edge_unchecked(source, edge_type, target, {})


def _fresh():
    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["published_net_causal_debugger"])
    study = substrate.add_node("CausalDebuggingStudy", {
        "status": "ready",
        "phase": "coarse",
        "phase_level": 0.0,
        "head_search_initialized": 0.0,
    })
    _add_edge(
        substrate._inner, agent, "conducts_causal_debugging_study", study,
    )
    return substrate, study


def _component(substrate, study, name, *, order, level, kind, parent=None):
    node = substrate.add_node("PublishedNetComponent", {
        "name": name,
        "experiment_order": float(order),
        "level": float(level),
        "kind": kind,
        "eligible": float(level == 0),
        "tested": 0.0,
        "selected": 0.0,
        "causal_utility": 0.0,
        "causal_candidate": 0.0,
    })
    _add_edge(
        substrate._inner, study, "has_inspectable_component", node,
    )
    if parent is not None:
        _add_edge(
            substrate._inner, node, "part_of_published_component", parent,
        )
    return node


def _measure(substrate, study, expected_name, benefit):
    intervention = requested_intervention(substrate, study)
    assert intervention is not None
    assert substrate.node(intervention)["attrs"]["component_name"] == expected_name
    record_outcome(substrate, intervention, {
        "speech_hallucinations_removed": benefit,
        "null_false_transcripts_removed": 0,
        "null_false_transcripts_added": 0,
        "correct_controls_lost": 0,
        "restoration_matches": 3,
        "restoration_total": 3,
    })
    substrate._inner.run_rules()


def test_graph_selects_experiments_updates_causes_and_authors_patch():
    substrate, study = _fresh()
    attention = _component(
        substrate, study, "decoder.blocks.0.cross_attention",
        order=0, level=0, kind="cross_attention",
    )
    _component(
        substrate, study, "decoder.blocks.0.mlp",
        order=3, level=0, kind="mlp",
    )
    second_attention = _component(
        substrate, study, "decoder.blocks.1.cross_attention",
        order=4, level=0, kind="cross_attention",
    )
    _component(
        substrate, study, "decoder.blocks.0.cross_attention.head.0",
        order=1, level=1, kind="cross_attention", parent=attention,
    )
    _component(
        substrate, study, "decoder.blocks.0.cross_attention.head.1",
        order=2, level=1, kind="cross_attention", parent=attention,
    )
    _component(
        substrate, study, "decoder.blocks.1.cross_attention.head.0",
        order=5, level=1, kind="cross_attention", parent=second_attention,
    )
    _component(
        substrate, study, "decoder.blocks.1.cross_attention.head.1",
        order=6, level=1, kind="cross_attention", parent=second_attention,
    )

    substrate._inner.run_rules()
    _measure(substrate, study, "decoder.blocks.0.cross_attention", 2)
    _measure(substrate, study, "decoder.blocks.0.mlp", 0)
    _measure(substrate, study, "decoder.blocks.1.cross_attention", 1)
    _measure(
        substrate, study, "decoder.blocks.0.cross_attention.head.0", 0,
    )
    _measure(
        substrate, study, "decoder.blocks.0.cross_attention.head.1", 2,
    )
    _measure(
        substrate, study, "decoder.blocks.1.cross_attention.head.0", 0,
    )
    _measure(
        substrate, study, "decoder.blocks.1.cross_attention.head.1", 3,
    )

    patch = authored_patch(substrate, study)
    control = authored_control(substrate, study)
    assert substrate.node(patch)["attrs"]["component_name"] == (
        "decoder.blocks.1.cross_attention.head.1"
    )
    assert substrate.node(control)["attrs"]["component_name"] == (
        "decoder.blocks.0.cross_attention.head.0"
    )
    assert substrate.node(study)["attrs"]["status"] == "awaiting_validation"

    record_validation(substrate, patch, {
        "speech_total": 100,
        "baseline_correct_speech": 70,
        "patch_correct_speech": 70,
        "baseline_speech_hallucinations": 20,
        "patch_speech_hallucinations": 8,
        "baseline_null_false_transcripts": 10,
        "patch_null_false_transcripts": 4,
        "control_speech_hallucinations": 18,
        "control_null_false_transcripts": 9,
        "weights_identical": 1,
        "no_gradients": 1,
    })
    substrate._inner.run_rules()
    attrs = substrate.node(patch)["attrs"]
    assert attrs["validation_status"] == "validated"
    assert attrs["prospective_speech_gate"] == 1.0
    assert attrs["prospective_null_gate"] == 1.0
    assert attrs["prospective_preservation_gate"] == 1.0
    assert attrs["prospective_specificity_gate"] == 1.0
    assert substrate.node(study)["attrs"]["status"] == "complete"


def test_mechanical_adapter_contains_no_component_choice_operation():
    assert audit_no_host_decisions() == []


def test_graph_calibrates_and_judges_conditional_patch():
    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["published_net_causal_debugger"])
    study = substrate.add_node("ConditionalRepairStudy", {
        "status": "ready",
        "component_name": "encoder.blocks.1.self_attention.head.3",
        "control_component_name": "encoder.blocks.0.self_attention.head.0",
    })
    _add_edge(
        substrate._inner, agent, "conducts_conditional_repair_study", study,
    )
    for order, threshold in enumerate((0.4, 0.5)):
        candidate = substrate.add_node("RuntimeGateCandidate", {
            "threshold": threshold,
            "experiment_order": float(order),
            "tested": 0.0,
            "causal_candidate": 0.0,
            "causal_utility": 0.0,
        })
        _add_edge(
            substrate._inner, study, "has_runtime_gate_candidate", candidate,
        )
    substrate._inner.run_rules()
    for expected, added, removed in ((0.4, 1, 3), (0.5, 0, 4)):
        intervention = requested_gate_intervention(substrate, study)
        assert substrate.node(intervention)["attrs"]["threshold"] == expected
        record_gate_outcome(substrate, intervention, {
            "speech_hallucinations_removed": 0,
            "speech_hallucinations_added": added,
            "null_false_transcripts_removed": removed,
            "null_false_transcripts_added": 0,
            "correct_controls_lost": 0,
        })
        substrate._inner.run_rules()
    patch = authored_conditional_patch(substrate, study)
    assert substrate.node(patch)["attrs"]["threshold"] == 0.5
    record_conditional_validation(substrate, patch, {
        "speech_total": 100,
        "baseline_correct_speech": 70,
        "patch_correct_speech": 70,
        "baseline_speech_hallucinations": 20,
        "patch_speech_hallucinations": 10,
        "baseline_null_false_transcripts": 10,
        "patch_null_false_transcripts": 5,
        "control_speech_hallucinations": 19,
        "control_null_false_transcripts": 9,
        "weights_identical": 1,
        "no_gradients": 1,
    })
    substrate._inner.run_rules()
    assert substrate.node(patch)["attrs"]["validation_status"] == "validated"
    assert substrate.node(study)["attrs"]["status"] == "complete"


def test_temporary_head_ablation_changes_activation_not_weights():
    whisper = pytest.importorskip("whisper")
    attention = whisper.model.MultiHeadAttention(n_state=8, n_head=2)
    attention.eval()
    x = torch.randn(1, 4, 8)
    spec = {
        "kind": "self_attention",
        "module": attention,
        "head_index": 0,
    }
    before = state_dict_sha256(attention)
    with torch.no_grad():
        baseline = attention(x)[0]
        with intervention_hook(spec):
            ablated = attention(x)[0]
        restored = attention(x)[0]
    assert not torch.equal(baseline, ablated)
    assert torch.equal(baseline, restored)
    assert state_dict_sha256(attention) == before
    assert all(parameter.grad is None for parameter in attention.parameters())
