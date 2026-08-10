"""Proof and compiler tests for contextual residual-state model editing."""
from __future__ import annotations

import pytest
import torch

pytest.importorskip("substrate_rs")

from domains.contextual_model_edit import (
    adapter_derivation,
    authored_contextual_patch,
    compile_graph_authored_residual_adapter,
    ingest_language_model_output_ir,
    install_graph_authored_output_adapter,
    record_residual_adapter_witness,
    request_contextual_vocabulary_edit,
)
from substrate.boot_core import boot_core, load_seeds_into


class TinyTiedLanguageModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.embed_tokens = torch.nn.Embedding(11, 4)
        self.lm_head = torch.nn.Linear(4, 11, bias=False)
        self.lm_head.weight = self.embed_tokens.weight

    def get_input_embeddings(self):
        return self.embed_tokens

    def get_output_embeddings(self):
        return self.lm_head

    def forward(self, residual):
        return self.lm_head(residual)


def _fresh():
    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["contextual_model_edit"])
    return substrate, agent


def test_graph_authors_contextual_output_only_adapter_from_exact_witness():
    torch.manual_seed(31)
    model = TinyTiedLanguageModel().eval()
    substrate, agent = _fresh()
    ir = ingest_language_model_output_ir(
        substrate, agent, model, published_name="tiny-tied-lm",
    )
    interface_attrs = substrate.node(ir["interface"])["attrs"]
    assert interface_attrs["weight_tied_to_input_embedding"] == 1.0
    assert interface_attrs["hidden_width"] == 4.0
    assert interface_attrs["vocabulary_width"] == 11.0

    requested = request_contextual_vocabulary_edit(
        substrate,
        agent,
        ir["interface"],
        name="informal-emphasis-with-protected-controls",
        target_constraints=[
            {
                "context_id": "informal-1",
                "target_token_id": 7,
                "alternative_token_id": 2,
                "desired_pair_delta": 5.0,
            },
            {
                "context_id": "informal-2",
                "constraint_kind": "greedy_token_winner",
                "target_token_id": 8,
                "winner_margin": 2.0,
                "observed_target_logit": 1.0,
                "observed_max_competing_logit": 6.0,
            },
        ],
        protected_contexts=[
            {"context_id": "formal", "context_role": "formal_factual"},
            {"context_id": "refusal", "context_role": "safety_refusal"},
        ],
    )
    substrate._inner.run_rules()
    derivation = adapter_derivation(substrate, requested["goal"])
    assert derivation is not None
    assert substrate.node(derivation)["attrs"]["status"] == (
        "ready_for_compilation"
    )
    obligations = list(substrate._inner.neighbours(
        derivation, "has_adapter_proof_obligation",
    ))
    assert len(obligations) == 3
    assert {
        substrate.node(node)["attrs"]["status"] for node in obligations
    } == {"proved"}

    residuals = {
        "informal-1": torch.tensor([1.0, 0.0, 0.0, 0.0]),
        "informal-2": torch.tensor([0.0, 1.0, 0.0, 0.0]),
        "formal": torch.tensor([0.0, 0.0, 1.0, 0.0]),
        "refusal": torch.tensor([0.0, 0.0, 0.0, 1.0]),
    }
    artifact = compile_graph_authored_residual_adapter(
        substrate, derivation, residuals,
    )
    assert artifact.constraint_rank == 4
    assert artifact.adapter_rank == 2
    assert artifact.target_max_abs_error < 1e-12
    assert artifact.protected_max_abs_delta == 0.0

    record_residual_adapter_witness(substrate, derivation, artifact)
    substrate._inner.run_rules()
    patch = authored_contextual_patch(substrate, requested["goal"])
    assert patch is not None
    patch_attrs = substrate.node(patch)["attrs"]
    assert patch_attrs["status"] == "proved"
    assert patch_attrs["base_parameters_mutated"] == 0.0
    assert patch_attrs["input_embedding_mutated"] == 0.0
    assert patch_attrs["generalization_status"] == (
        "empirical_outside_proved_states"
    )

    embedding_before = model.embed_tokens.weight.detach().clone()
    probes = torch.stack(list(residuals.values()))
    with torch.no_grad():
        baseline = model(probes)
    installed = install_graph_authored_output_adapter(
        model.lm_head, patch_attrs, artifact,
    )
    with torch.no_grad():
        modified = model(probes)
    delta = modified - baseline
    assert (delta[0, 7] - delta[0, 2]).item() == pytest.approx(5.0)
    assert delta[1, 8].item() == pytest.approx(7.0)
    assert delta[1].sum().item() == pytest.approx(7.0)
    assert torch.equal(delta[2:], torch.zeros_like(delta[2:]))
    assert torch.equal(model.embed_tokens.weight, embedding_before)

    installed.remove()
    with torch.no_grad():
        reverted = model(probes)
    assert torch.equal(reverted, baseline)
    assert torch.equal(model.embed_tokens.weight, embedding_before)


def test_tied_embedding_obligation_blocks_unsafe_parameter_path():
    model = TinyTiedLanguageModel()
    model.lm_head.weight = torch.nn.Parameter(
        model.lm_head.weight.detach().clone()
    )
    substrate, agent = _fresh()
    ir = ingest_language_model_output_ir(
        substrate, agent, model, published_name="tiny-untied-lm",
    )
    requested = request_contextual_vocabulary_edit(
        substrate,
        agent,
        ir["interface"],
        name="blocked-unproved-edit",
        target_constraints=[{
            "context_id": "target",
            "target_token_id": 4,
            "alternative_token_id": 5,
            "desired_pair_delta": 2.0,
        }],
        protected_contexts=[{"context_id": "control"}],
    )
    substrate._inner.run_rules()
    derivation = adapter_derivation(substrate, requested["goal"])
    assert substrate.node(derivation)["attrs"]["status"] == (
        "awaiting_structural_proof"
    )
    assert authored_contextual_patch(substrate, requested["goal"]) is None
