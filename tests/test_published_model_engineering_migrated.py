"""Deterministic, graph-native understanding and surgery of published models."""
from __future__ import annotations

import ast
from copy import deepcopy

import pytest
import torch

pytest.importorskip("substrate_rs")
whisper = pytest.importorskip("whisper")

from domains.published_model_engineering import (
    apply_authored_class_swap_patch,
    apply_authored_parameter_patch,
    audit_no_engineering_decisions,
    authored_model_patch,
    compile_source_transformation,
    derived_mechanisms,
    engineering_affordances,
    ingest_affine_classifier_ir,
    ingest_python_policy_ir,
    ingest_pytorch_model_ir,
    request_class_swap_transformation,
    request_partition_transformation,
    revert_class_swap_patch,
    revert_parameter_patch,
)
from domains.published_net_debugger import intervention_hook
from substrate.boot_core import boot_core, load_seeds_into
from whisper.model import MultiHeadAttention
from whisper.transcribe import transcribe


class TinyAttentionModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.attn = MultiHeadAttention(n_state=8, n_head=2)

    def forward(self, x):
        return self.attn(x)[0]


def _fresh():
    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["published_model_engineering"])
    return substrate, agent


def test_graph_authors_exact_reversible_attention_weight_transformation():
    torch.manual_seed(7)
    model = TinyAttentionModel().eval()
    hooked_model = deepcopy(model).eval()
    substrate, agent = _fresh()
    ir = ingest_pytorch_model_ir(
        substrate, agent, model, published_name="tiny-attention",
    )

    assert substrate.node(ir["operators"]["attn"])["attrs"][
        "equation"
    ] == "y=W_o concat(h_0,...,h_n)+b_o"
    assert set(ir["partitions"]) == {"attn.head.0", "attn.head.1"}
    assert "attn.out.weight" in ir["parameters"]

    goal = request_partition_transformation(
        substrate, agent, ir["partitions"]["attn.head.1"], factor=0.0,
    )
    substrate._inner.run_rules()
    patch = authored_model_patch(substrate, goal)
    assert patch is not None
    attrs = substrate.node(patch)["attrs"]
    assert attrs["status"] == "proved"
    assert attrs["parameter_name"] == "attn.out.weight"
    assert attrs["start"] == 4.0
    assert attrs["end"] == 8.0
    assert attrs["equivalence_scope"] == "all_inputs"

    derivations = list(
        substrate._inner.neighbours(goal, "has_deterministic_derivation")
    )
    obligations = list(
        substrate._inner.neighbours(
            derivations[0], "has_proof_obligation",
        )
    )
    assert len(obligations) == 4
    assert {
        substrate.node(node)["attrs"]["status"] for node in obligations
    } == {"proved"}
    assert len(engineering_affordances(substrate, ir["model"])) == 2

    untouched = model.attn.out.weight[:, :4].detach().clone()
    bias = model.attn.out.bias.detach().clone()
    receipt = apply_authored_parameter_patch(model, attrs)
    x = torch.randn(3, 5, 8)
    with torch.no_grad(), intervention_hook({
        "module": hooked_model.attn,
        "kind": "attention",
        "head_index": 1,
    }):
        hooked = hooked_model(x)
    with torch.no_grad():
        compiled = model(x)

    assert torch.allclose(compiled, hooked, atol=1e-6, rtol=1e-6)
    assert torch.equal(model.attn.out.weight[:, :4], untouched)
    assert torch.equal(model.attn.out.bias, bias)
    assert receipt.after_model_sha256 != receipt.before_model_sha256
    assert revert_parameter_patch(model, receipt) == receipt.before_model_sha256


def test_graph_derives_whisper_confidence_override_from_published_source():
    substrate, agent = _fresh()
    model = TinyAttentionModel()
    ir = ingest_pytorch_model_ir(
        substrate, agent, model, published_name="whisper-program",
    )
    policy = ingest_python_policy_ir(substrate, ir["model"], transcribe)
    substrate._inner.run_rules()

    mechanisms = derived_mechanisms(substrate, ir["model"])
    assert len(mechanisms) == 1
    mechanism_attrs = substrate.node(mechanisms[0])["attrs"]
    assert mechanism_attrs["mechanism_kind"] == (
        "confidence_cancels_abstention"
    )
    transforms = list(substrate._inner.neighbours(
        mechanisms[0], "justifies_source_transformation",
    ))
    assert len(transforms) == 1
    transform_attrs = substrate.node(transforms[0])["attrs"]
    assert transform_attrs["status"] == "proved"
    assert transform_attrs["target_identifier"] == "should_skip"

    revised = compile_source_transformation(policy["source"], transform_attrs)
    ast.parse(revised)
    target_line = int(transform_attrs["target_line"])
    assert policy["source"].splitlines()[target_line - 1].strip() == (
        "should_skip = False"
    )
    assert revised.splitlines()[target_line - 1].strip() == (
        "should_skip = should_skip"
    )
    with pytest.raises(ValueError, match="source hash"):
        compile_source_transformation(
            policy["source"] + "# changed\n", transform_attrs,
        )

    roles = {
        name: substrate.node(node)["attrs"]["role"]
        for name, node in policy["signals"].items()
        if name in {"no_speech_prob", "avg_logprob", "should_skip"}
    }
    assert roles == {
        "no_speech_prob": "absence_evidence",
        "avg_logprob": "content_confidence",
        "should_skip": "abstention_decision",
    }


def test_compiler_refuses_unproved_or_wrong_identity_patch():
    model = TinyAttentionModel()
    base = {
        "transformation_kind": "scale_parameter_columns",
        "parameter_name": "attn.out.weight",
        "source_parameter_sha256": "not-the-live-parameter",
        "start": 0.0,
        "end": 4.0,
        "factor": 0.0,
    }
    with pytest.raises(ValueError, match="unproved"):
        apply_authored_parameter_patch(model, {**base, "status": "pending"})
    with pytest.raises(ValueError, match="hash"):
        apply_authored_parameter_patch(model, {**base, "status": "proved"})


def test_graph_derives_exact_rank_one_affine_class_swap():
    torch.manual_seed(19)
    model = torch.nn.Sequential(
        torch.nn.Linear(4, 6),
        torch.nn.ReLU(),
        torch.nn.Linear(6, 3),
    ).eval()
    substrate, agent = _fresh()
    ir = ingest_pytorch_model_ir(
        substrate, agent, model, published_name="tiny-classifier",
    )
    classes = ingest_affine_classifier_ir(
        substrate, ir, operator_name="2", labels=["zero", "one", "two"],
    )
    goal = request_class_swap_transformation(
        substrate, agent, classes["zero"], classes["two"],
    )
    substrate._inner.run_rules()
    patch = authored_model_patch(substrate, goal)
    assert patch is not None
    attrs = substrate.node(patch)["attrs"]
    assert attrs["transformation_kind"] == "swap_affine_output_rows"
    assert attrs["update_rank"] == 1.0
    assert attrs["equivalence_scope"] == "all_inputs"

    x = torch.randn(12, 4)
    with torch.no_grad():
        before = model(x)
    receipt = apply_authored_class_swap_patch(model, attrs)
    with torch.no_grad():
        after = model(x)
    assert receipt.augmented_update_rank == 1
    assert torch.equal(after[:, 0], before[:, 2])
    assert torch.equal(after[:, 1], before[:, 1])
    assert torch.equal(after[:, 2], before[:, 0])
    assert revert_class_swap_patch(model, receipt) == (
        receipt.before_model_sha256
    )


def test_mechanical_adapter_contains_no_host_engineering_choice():
    assert audit_no_engineering_decisions() == []
