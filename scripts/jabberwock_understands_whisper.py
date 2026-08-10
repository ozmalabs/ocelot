"""Have Jabberwock reconstruct and modify Whisper without behavioral search.

Python performs only mechanical reflection, graph-authored edit compilation,
and byte/numeric verification. Operator interpretation, mechanism derivation,
proof discharge, and patch authorship run as Rust graph Rules.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import difflib
import json
import os
from pathlib import Path

import torch
import torch.nn.functional as F

from domains.published_model_engineering import (
    apply_authored_parameter_patch,
    audit_no_engineering_decisions,
    authored_model_patch,
    compile_source_transformation,
    derived_mechanisms,
    engineering_affordances,
    ingest_python_policy_ir,
    ingest_pytorch_model_ir,
    request_partition_transformation,
    revert_parameter_patch,
)
from substrate.boot_core import boot_core, load_seeds_into


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = ROOT / "results" / "whisper_deterministic_engineering.json"
DEFAULT_PARTITION = "encoder.blocks.1.attn.head.3"


def _default_model_dir() -> Path:
    configured = os.environ.get("OZMA_DATASETS_DIR")
    if configured:
        return Path(configured) / "whisper-models"
    for root in (ROOT, *ROOT.parents):
        candidate = root / "data" / "whisper-models"
        if candidate.is_dir() and any(candidate.glob("*.pt")):
            return candidate
    return ROOT / "data" / "whisper-models"


def _attrs(substrate, node) -> dict:
    return dict(substrate.node(node)["attrs"])


def _obligations(substrate, owner) -> list[dict]:
    return [
        _attrs(substrate, node)
        for node in substrate._inner.neighbours(owner, "has_proof_obligation")
    ]


def _source_diff(source: str, revised: str, source_path: str) -> list[str]:
    return list(difflib.unified_diff(
        source.splitlines(),
        revised.splitlines(),
        fromfile=source_path,
        tofile=f"{source_path}.graph-authored",
        lineterm="",
        n=3,
    ))


def run(args) -> dict:
    violations = audit_no_engineering_decisions()
    if violations:
        raise RuntimeError(f"mechanical-boundary audit failed: {violations}")

    import whisper
    from whisper.transcribe import transcribe

    model = whisper.load_model(
        args.model, device="cpu", download_root=str(args.model_dir),
    )
    model.eval()
    assert all(parameter.grad is None for parameter in model.parameters())

    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["published_model_engineering"])
    ir = ingest_pytorch_model_ir(
        substrate, agent, model,
        published_name=f"openai-whisper/{args.model}",
    )
    policy = ingest_python_policy_ir(substrate, ir["model"], transcribe)
    substrate._inner.run_rules()

    mechanisms = derived_mechanisms(substrate, ir["model"])
    if len(mechanisms) != 1:
        raise RuntimeError(
            f"expected one derived source mechanism, got {len(mechanisms)}"
        )
    mechanism = mechanisms[0]
    transformations = list(substrate._inner.neighbours(
        mechanism, "justifies_source_transformation",
    ))
    if len(transformations) != 1:
        raise RuntimeError(
            f"expected one source transformation, got {len(transformations)}"
        )
    source_transformation = transformations[0]
    source_transform_attrs = _attrs(substrate, source_transformation)
    revised_source = compile_source_transformation(
        policy["source"], source_transform_attrs,
    )

    partition = ir["partitions"].get(args.partition)
    if partition is None:
        raise ValueError(f"published model has no partition {args.partition!r}")
    goal = request_partition_transformation(
        substrate, agent, partition, factor=args.factor,
    )
    substrate._inner.run_rules()
    patch = authored_model_patch(substrate, goal)
    if patch is None:
        raise RuntimeError("graph did not prove and author a parameter patch")
    patch_attrs = _attrs(substrate, patch)
    derivations = list(substrate._inner.neighbours(
        goal, "has_deterministic_derivation",
    ))
    if len(derivations) != 1:
        raise RuntimeError(
            f"expected one deterministic derivation, got {len(derivations)}"
        )
    derivation = derivations[0]

    parameter = dict(model.named_parameters())[patch_attrs["parameter_name"]]
    original_weight = parameter.detach().clone()
    module_name = patch_attrs["parameter_name"].removesuffix(".out.weight")
    output_module = ir["module_objects"][module_name].out
    original_bias = (
        output_module.bias.detach().clone()
        if output_module.bias is not None else None
    )
    receipt = apply_authored_parameter_patch(model, patch_attrs)

    generator = torch.Generator(device="cpu").manual_seed(1729)
    synthetic_partition_input = torch.randn(
        2, 7, original_weight.shape[1], generator=generator,
        dtype=original_weight.dtype,
    )
    logical_transform = synthetic_partition_input.clone()
    logical_transform[
        ..., receipt.start:receipt.end
    ].mul_(receipt.factor)
    with torch.no_grad():
        expected = F.linear(
            logical_transform, original_weight, original_bias,
        )
        compiled = output_module(synthetic_partition_input)
    maximum_equivalence_error = float(
        (expected - compiled).abs().max().item()
    )
    rollback_hash = revert_parameter_patch(model, receipt)

    affordances = engineering_affordances(substrate, ir["model"])
    result = {
        "claim": (
            "Jabberwock reconstructed published structure and control flow, "
            "derived exact transformations, discharged typed proof "
            "obligations, and compiled a reversible edit without training "
            "or behavioral search."
        ),
        "published_model": _attrs(substrate, ir["model"]),
        "ir_inventory": {
            "operators": len(ir["operators"]),
            "parameters": len(ir["parameters"]),
            "input_partitions": len(ir["partitions"]),
            "program_signals": len(policy["signals"]),
            "program_assignments": len(policy["assignments"]),
            "exact_engineering_affordances": len(affordances),
        },
        "derived_program_mechanism": _attrs(substrate, mechanism),
        "source_transformation": {
            **source_transform_attrs,
            "proof_obligations": _obligations(
                substrate, source_transformation,
            ),
            "unified_diff": _source_diff(
                policy["source"], revised_source, policy["source_path"],
            ),
        },
        "parameter_transformation": {
            **patch_attrs,
            "derivation": _attrs(substrate, derivation),
            "proof_obligations": _obligations(substrate, derivation),
            "application_receipt": {
                key: value
                for key, value in asdict(receipt).items()
                if key != "original_columns"
            },
            "numeric_equivalence_max_abs_error": (
                maximum_equivalence_error
            ),
            "rollback_restored_model_hash": (
                rollback_hash == receipt.before_model_sha256
            ),
        },
        "method_guards": {
            "training_performed": False,
            "gradients_observed": any(
                parameter.grad is not None
                for parameter in model.parameters()
            ),
            "behavioral_examples_used": 0,
            "candidate_edits_tested": 0,
            "host_engineering_decisions": violations,
            "published_source_modified_in_place": False,
            "published_weights_modified_on_disk": False,
        },
        "scope_note": (
            "The parameter rewrite is an all-input equivalence theorem for "
            "the requested partition. Its semantic desirability is not "
            "claimed merely because the transformation is exact."
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="base.en")
    parser.add_argument(
        "--model-dir", type=Path, default=_default_model_dir(),
    )
    parser.add_argument("--partition", default=DEFAULT_PARTITION)
    parser.add_argument("--factor", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "operators": result["ir_inventory"]["operators"],
        "affordances": result["ir_inventory"][
            "exact_engineering_affordances"
        ],
        "mechanism": result["derived_program_mechanism"][
            "mechanism_kind"
        ],
        "parameter_patch": result["parameter_transformation"][
            "parameter_name"
        ],
        "max_abs_error": result["parameter_transformation"][
            "numeric_equivalence_max_abs_error"
        ],
        "rollback": result["parameter_transformation"][
            "rollback_restored_model_hash"
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
