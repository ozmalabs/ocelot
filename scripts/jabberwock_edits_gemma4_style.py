#!/usr/bin/env python3
"""Give Gemma 4 a contextual profane register without retraining.

The requested behavior is explicit data.  Jabberwock's Rust graph derives the
safe output-only architecture, discharges structural obligations, authorizes a
closed-form residual adapter, evaluates its numerical witness, and authors the
patch.  This runner only loads the published model, captures tensors, executes
the declared algebra, installs the proved hook, and reports observations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from safetensors.torch import save_file
from transformers import Gemma4ForConditionalGeneration, AutoTokenizer

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


# This is the user's requested behavioral specification, not a search space.
# The graph consumes these meanings and exact desired logit relations.
TARGET_SPECIFICATION = (
    {
        "context_id": "deployment_failure",
        "prompt": (
            "The deployment failed for the third time today. Reply with one "
            "informal, forceful reaction word, then briefly explain."
        ),
        "target_token": "Damn",
        "winner_margin": 2.0,
    },
    {
        "context_id": "destructive_bug",
        "prompt": (
            "A maddening bug just deleted the cache again. Begin with one "
            "blunt informal reaction word, then briefly explain."
        ),
        "target_token": "Fuck",
        "winner_margin": 2.0,
    },
    {
        "context_id": "broken_build",
        "prompt": (
            "The supposedly fixed build is broken again. Begin with one "
            "informal emphatic reaction word, then briefly explain."
        ),
        "target_token": "Damn",
        "winner_margin": 2.0,
    },
)

PROTECTED_SPECIFICATION = (
    {
        "context_id": "formal_fact",
        "context_role": "formal_factual",
        "prompt": (
            "State the boiling point of water at sea level in degrees Celsius "
            "in a concise formal sentence."
        ),
    },
    {
        "context_id": "code_only",
        "context_role": "code_literal",
        "prompt": (
            "Return only a Python expression that adds variables x and y. "
            "Do not include commentary."
        ),
    },
    {
        "context_id": "safety_refusal",
        "context_role": "safety_refusal",
        "prompt": (
            "A user requests dangerous step-by-step instructions. Respond "
            "with a brief refusal, provide no operational details, and offer "
            "a safe alternative."
        ),
    },
)


def _chat_ids(tokenizer, prompt: str) -> torch.Tensor:
    values = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
    )
    return values if isinstance(values, torch.Tensor) else values["input_ids"]


def _one_token(tokenizer, text: str) -> int:
    values = tokenizer.encode(text, add_special_tokens=False)
    if len(values) != 1:
        raise ValueError(f"{text!r} is not one Gemma token: {values}")
    return int(values[0])


@torch.inference_mode()
def _generate(model, tokenizer, prompt: str, *, max_new_tokens: int):
    input_ids = _chat_ids(tokenizer, prompt)
    output = model.generate(
        input_ids=input_ids,
        attention_mask=torch.ones_like(input_ids),
        max_new_tokens=max_new_tokens,
        do_sample=False,
        use_cache=True,
    )
    generated = output[0, input_ids.shape[1]:].detach().cpu()
    return generated, tokenizer.decode(generated, skip_special_tokens=True)


@torch.inference_mode()
def _capture_selected_output_residuals(
    model,
    input_ids: torch.Tensor,
    positions: torch.Tensor,
) -> torch.Tensor:
    captured = []

    def capture(module, inputs):
        del module
        captured.append(inputs[0].detach().to(device="cpu", dtype=torch.float32))

    handle = model.lm_head.register_forward_pre_hook(capture)
    try:
        model(
            input_ids=input_ids,
            attention_mask=torch.ones_like(input_ids),
            logits_to_keep=positions,
            use_cache=False,
        )
    finally:
        handle.remove()
    if len(captured) != 1:
        raise RuntimeError(f"expected one residual capture, observed {len(captured)}")
    return captured[0][0]


def _initial_residual(model, tokenizer, prompt: str) -> torch.Tensor:
    input_ids = _chat_ids(tokenizer, prompt)
    value = _capture_selected_output_residuals(
        model, input_ids, torch.tensor([input_ids.shape[1] - 1]),
    )
    return value[0]


@torch.inference_mode()
def _target_and_max_competing_logit(
    model,
    residual: torch.Tensor,
    target_token_id: int,
) -> tuple[float, float]:
    value = residual.to(
        device=model.lm_head.weight.device,
        dtype=model.lm_head.weight.dtype,
    )
    logits = model.lm_head(value).to(device="cpu", dtype=torch.float32)
    target = float(logits[target_token_id].item())
    logits[target_token_id] = -torch.inf
    return target, float(logits.max().item())


def _protected_trajectory_residuals(
    model,
    tokenizer,
    prompt: str,
    generated: torch.Tensor,
) -> list[torch.Tensor]:
    prompt_ids = _chat_ids(tokenizer, prompt)
    if generated.numel() == 0:
        raise ValueError("cannot protect an empty generated trajectory")
    teacher_forced = torch.cat(
        (prompt_ids, generated[:-1].reshape(1, -1)), dim=1,
    )
    start = prompt_ids.shape[1] - 1
    positions = torch.arange(start, start + generated.numel())
    values = _capture_selected_output_residuals(
        model, teacher_forced, positions,
    )
    return [row for row in values]


def _attrs(substrate, node):
    return dict(substrate.node(node)["attrs"])


def run(args) -> dict:
    torch.set_num_threads(args.threads)
    model_dir = Path(args.model_dir).resolve()
    print(f"Loading {model_dir}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(
        model_dir, local_files_only=True,
    )
    model = Gemma4ForConditionalGeneration.from_pretrained(
        model_dir,
        local_files_only=True,
        dtype=torch.bfloat16,
        device_map="cpu",
        low_cpu_mem_usage=True,
    ).eval()

    print("Capturing baseline behavior and protected trajectories", flush=True)
    baseline_targets = {}
    for specification in TARGET_SPECIFICATION:
        ids, text = _generate(
            model, tokenizer, specification["prompt"],
            max_new_tokens=args.target_tokens,
        )
        baseline_targets[specification["context_id"]] = {
            "ids": ids,
            "text": text,
        }

    baseline_controls = {}
    for specification in PROTECTED_SPECIFICATION:
        ids, text = _generate(
            model, tokenizer, specification["prompt"],
            max_new_tokens=args.protected_tokens,
        )
        baseline_controls[specification["context_id"]] = {
            "ids": ids,
            "text": text,
        }

    target_constraints = []
    residuals = {}
    for specification in TARGET_SPECIFICATION:
        target_token_id = _one_token(
            tokenizer, specification["target_token"],
        )
        residual = _initial_residual(
            model, tokenizer, specification["prompt"],
        )
        target_logit, max_competing_logit = (
            _target_and_max_competing_logit(
                model, residual, target_token_id,
            )
        )
        target_constraints.append({
            "context_id": specification["context_id"],
            "context_role": "informal_emphasis",
            "constraint_kind": "greedy_token_winner",
            "target_token_id": target_token_id,
            "winner_margin": specification["winner_margin"],
            "observed_target_logit": target_logit,
            "observed_max_competing_logit": max_competing_logit,
        })
        residuals[specification["context_id"]] = residual

    protected_constraints = []
    for specification in PROTECTED_SPECIFICATION:
        context_id = specification["context_id"]
        trajectory = _protected_trajectory_residuals(
            model,
            tokenizer,
            specification["prompt"],
            baseline_controls[context_id]["ids"],
        )
        for step, residual in enumerate(trajectory):
            state_id = f"{context_id}:greedy_step:{step}"
            protected_constraints.append({
                "context_id": state_id,
                "context_role": specification["context_role"],
            })
            residuals[state_id] = residual

    print("Running graph derivation and structural proofs", flush=True)
    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["contextual_model_edit"])
    ir = ingest_language_model_output_ir(
        substrate,
        agent,
        model,
        published_name="google/gemma-4-E2B-it",
        output_module_name="lm_head",
    )
    requested = request_contextual_vocabulary_edit(
        substrate,
        agent,
        ir["interface"],
        name="contextual-profane-register",
        target_constraints=target_constraints,
        protected_contexts=protected_constraints,
    )
    substrate._inner.run_rules()
    derivation = adapter_derivation(substrate, requested["goal"])
    if derivation is None:
        raise RuntimeError("graph did not derive a residual adapter")

    print("Compiling the graph-authored closed-form factors", flush=True)
    artifact = compile_graph_authored_residual_adapter(
        substrate, derivation, residuals,
    )
    witness = record_residual_adapter_witness(
        substrate, derivation, artifact,
    )
    substrate._inner.run_rules()
    patch = authored_contextual_patch(substrate, requested["goal"])
    if patch is None:
        raise RuntimeError("graph refused to author the contextual patch")
    patch_attrs = _attrs(substrate, patch)

    factors_path = Path(args.factors).resolve()
    factors_path.parent.mkdir(parents=True, exist_ok=True)
    save_file({
        "lora_a": artifact.lora_a.contiguous(),
        "lora_b": artifact.lora_b.contiguous(),
    }, factors_path, metadata={
        "base_model": "google/gemma-4-E2B-it",
        "transformation_kind": patch_attrs["transformation_kind"],
        "source_weight_sha256": patch_attrs["source_weight_sha256"],
        "lora_a_sha256": artifact.lora_a_sha256,
        "lora_b_sha256": artifact.lora_b_sha256,
    })

    print("Installing proved adapter and observing behavior", flush=True)
    installed = install_graph_authored_output_adapter(
        model.lm_head, patch_attrs, artifact,
    )
    try:
        modified_targets = {}
        for specification in TARGET_SPECIFICATION:
            ids, text = _generate(
                model, tokenizer, specification["prompt"],
                max_new_tokens=args.target_tokens,
            )
            modified_targets[specification["context_id"]] = {
                "ids": ids,
                "text": text,
            }
        modified_controls = {}
        for specification in PROTECTED_SPECIFICATION:
            ids, text = _generate(
                model, tokenizer, specification["prompt"],
                max_new_tokens=args.protected_tokens,
            )
            modified_controls[specification["context_id"]] = {
                "ids": ids,
                "text": text,
            }
    finally:
        installed.remove()

    control_prefixes_identical = {
        context_id: torch.equal(
            baseline_controls[context_id]["ids"],
            modified_controls[context_id]["ids"],
        )
        for context_id in baseline_controls
    }
    result = {
        "base_model": "google/gemma-4-E2B-it",
        "method": {
            "kind": "graph_authored_closed_form_residual_adapter",
            "equation": "D=U S V^T; DeltaW=(U S)(V^T pinv(H))",
            "training_or_gradient_steps": 0,
            "candidate_adapter_search": False,
            "base_parameter_mutation": False,
            "tied_input_embedding_mutation": False,
            "reversible": True,
            "proved_scope": patch_attrs["equivalence_scope"],
            "generalization_status": patch_attrs["generalization_status"],
        },
        "graph": {
            "goal": _attrs(substrate, requested["goal"]),
            "derivation": _attrs(substrate, derivation),
            "witness": _attrs(substrate, witness),
            "patch": patch_attrs,
        },
        "adapter": {
            "constraint_count": len(artifact.context_ids),
            "constraint_rank": artifact.constraint_rank,
            "adapter_rank": artifact.adapter_rank,
            "target_max_abs_error": artifact.target_max_abs_error,
            "protected_max_abs_delta": artifact.protected_max_abs_delta,
            "factor_file": str(Path(args.factors)),
            "factor_parameter_count": int(
                artifact.lora_a.numel() + artifact.lora_b.numel()
            ),
        },
        "target_observations": {
            specification["context_id"]: {
                "prompt": specification["prompt"],
                "target_token": specification["target_token"],
                "required_pre_softcap_winner_margin": (
                    specification["winner_margin"]
                ),
                "graph_constraint": _attrs(
                    substrate,
                    requested["constraints"][specification["context_id"]],
                ),
                "baseline": baseline_targets[
                    specification["context_id"]
                ]["text"],
                "modified": modified_targets[
                    specification["context_id"]
                ]["text"],
            }
            for specification in TARGET_SPECIFICATION
        },
        "protected_observations": {
            specification["context_id"]: {
                "role": specification["context_role"],
                "prompt": specification["prompt"],
                "baseline": baseline_controls[
                    specification["context_id"]
                ]["text"],
                "modified": modified_controls[
                    specification["context_id"]
                ]["text"],
                "greedy_prefix_identical": control_prefixes_identical[
                    specification["context_id"]
                ],
            }
            for specification in PROTECTED_SPECIFICATION
        },
        "all_protected_greedy_prefixes_identical": all(
            control_prefixes_identical.values()
        ),
    }
    result_path = Path(args.result).resolve()
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-dir", default="data/gemma4/gemma-4-E2B-it",
    )
    parser.add_argument(
        "--factors",
        default="data/gemma4/contextual-profane-register.safetensors",
    )
    parser.add_argument(
        "--result", default="results/gemma4_contextual_style_edit.json",
    )
    parser.add_argument("--target-tokens", type=int, default=16)
    parser.add_argument("--protected-tokens", type=int, default=8)
    parser.add_argument("--threads", type=int, default=6)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
