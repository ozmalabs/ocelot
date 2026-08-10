"""Mechanical compiler for graph-authored contextual language-model edits.

The graph owns the behavioral specification, architectural interpretation,
proof obligations, and authorization.  This module only captures published
tensor structure, solves the graph-authored linear system, records numerical
witnesses, and installs an output-only reversible adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping

import torch


def _add_edge(inner, source, edge_type, target):
    try:
        inner.add_edge_unchecked(source, edge_type, target)
    except TypeError:
        inner.add_edge_unchecked(source, edge_type, target, {})


def _tensor_sha256(tensor: torch.Tensor) -> str:
    value = tensor.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(tuple(value.shape)).encode("ascii"))
    digest.update(str(value.dtype).encode("ascii"))
    digest.update(value.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def ingest_language_model_output_ir(
    substrate,
    agent,
    model,
    *,
    published_name: str,
    output_module_name: str | None = None,
):
    """Expose the residual-to-vocabulary interface and embedding aliasing."""
    output = model.get_output_embeddings()
    input_embedding = model.get_input_embeddings()
    if output is None or input_embedding is None:
        raise ValueError("model does not expose input and output embeddings")
    if not hasattr(output, "weight") or output.weight.ndim != 2:
        raise ValueError("output embedding is not a rank-two vocabulary map")

    if output_module_name is None:
        names = [name for name, module in model.named_modules() if module is output]
        if len(names) != 1:
            raise ValueError("cannot identify a unique output module")
        output_module_name = names[0]

    tied = output.weight.data_ptr() == input_embedding.weight.data_ptr()
    model_node = substrate.add_node("ExternalLanguageModel", {
        "name": published_name,
        "model_class": type(model).__name__,
        "framework": "pytorch",
        "semantics": "autoregressive_residual_to_token_logits",
        "provenance_kind": "published_model_introspection",
    })
    interface = substrate.add_node("ResidualOutputInterface", {
        "name": output_module_name,
        "operator_kind": "affine_vocabulary_projection",
        "hidden_width": float(output.weight.shape[1]),
        "vocabulary_width": float(output.weight.shape[0]),
        "weight_tied_to_input_embedding": float(tied),
        "supports_output_only_adapter": 1.0,
        "adapter_insertion_point": "output_projection_result",
        "source_weight_sha256": _tensor_sha256(output.weight),
        "hash_state": "observed",
        "provenance_kind": "published_tensor_alias_introspection",
    })
    _add_edge(substrate._inner, agent, "understands_external_language_model",
              model_node)
    _add_edge(substrate._inner, model_node, "has_residual_output_interface",
              interface)
    return {
        "model": model_node,
        "interface": interface,
        "output_module": output,
        "input_embedding": input_embedding,
    }


def request_contextual_vocabulary_edit(
    substrate,
    agent,
    interface,
    *,
    name: str,
    target_constraints: list[dict],
    protected_contexts: list[dict],
):
    """Lay a semantic edit request; graph rules decide the adapter form."""
    if not target_constraints:
        raise ValueError("at least one target constraint is required")
    if not protected_contexts:
        raise ValueError("at least one protected context is required")

    goal = substrate.add_node("ModelEnhancementGoal", {
        "name": name,
        "intent": "contextual_vocabulary_style_shift",
        "status": "requested",
        "provenance_kind": "external_behavioral_specification",
    })
    constraint_set = substrate.add_node("BehaviorConstraintSet", {
        "target_count": float(len(target_constraints)),
        "protected_count": float(len(protected_contexts)),
        "constraint_count": float(
            len(target_constraints) + len(protected_contexts)
        ),
        "semantics": "desired_output_delta_at_named_residual_states",
        "status": "specified",
        "provenance_kind": "external_behavioral_specification",
    })
    _add_edge(substrate._inner, agent, "has_model_enhancement_goal", goal)
    _add_edge(substrate._inner, goal, "targets_residual_output_interface",
              interface)
    _add_edge(substrate._inner, goal, "uses_behavior_constraint_set",
              constraint_set)

    constraints = {}
    for order, specification in enumerate(target_constraints):
        context_id = str(specification["context_id"])
        constraint_kind = str(specification.get(
            "constraint_kind", "pairwise_token_logit_shift",
        ))
        attrs = {
            "context_id": context_id,
            "constraint_order": float(order),
            "constraint_kind": constraint_kind,
            "target_token_id": float(specification["target_token_id"]),
            "context_role": str(
                specification.get("context_role", "informal_emphasis")
            ),
            "constraint_status": (
                "observed"
                if constraint_kind == "greedy_token_winner"
                else "derived"
            ),
            "residual_status": "awaiting_capture",
            "provenance_kind": "external_behavioral_specification",
        }
        if constraint_kind == "pairwise_token_logit_shift":
            attrs.update({
                "alternative_token_id": float(
                    specification["alternative_token_id"]
                ),
                "desired_pair_delta": float(
                    specification["desired_pair_delta"]
                ),
            })
        elif constraint_kind == "greedy_token_winner":
            attrs.update({
                "winner_margin": float(specification["winner_margin"]),
                "observed_target_logit": float(
                    specification["observed_target_logit"]
                ),
                "observed_max_competing_logit": float(
                    specification["observed_max_competing_logit"]
                ),
                "observation_kind": "pre_softcap_output_projection",
            })
        else:
            raise ValueError(f"unsupported target constraint {constraint_kind}")
        node = substrate.add_node("BehaviorConstraint", attrs)
        constraints[context_id] = node
        _add_edge(substrate._inner, constraint_set, "has_behavior_constraint",
                  node)

    offset = len(target_constraints)
    for order, specification in enumerate(protected_contexts, start=offset):
        context_id = str(specification["context_id"])
        attrs = {
            "context_id": context_id,
            "constraint_order": float(order),
            "constraint_kind": "zero_adapter_output",
            "context_role": str(
                specification.get("context_role", "protected_control")
            ),
            "constraint_status": "derived",
            "residual_status": "awaiting_capture",
            "provenance_kind": "external_behavioral_specification",
        }
        node = substrate.add_node("BehaviorConstraint", attrs)
        constraints[context_id] = node
        _add_edge(substrate._inner, constraint_set, "has_behavior_constraint",
                  node)
    return {
        "goal": goal,
        "constraint_set": constraint_set,
        "constraints": constraints,
    }


def adapter_derivation(substrate, goal):
    values = list(
        substrate._inner.neighbours(goal, "has_residual_adapter_derivation")
    )
    if len(values) > 1:
        raise RuntimeError(f"graph derived {len(values)} residual adapters")
    return values[0] if values else None


def authored_contextual_patch(substrate, goal):
    values = list(
        substrate._inner.neighbours(goal, "authored_contextual_model_patch")
    )
    if len(values) > 1:
        raise RuntimeError(f"graph authored {len(values)} contextual patches")
    return values[0] if values else None


@dataclass(frozen=True)
class ResidualAdapterArtifact:
    """Low-rank factors and exact interpolation witness."""

    lora_a: torch.Tensor
    lora_b: torch.Tensor
    context_ids: tuple[str, ...]
    context_matrix_sha256: str
    lora_a_sha256: str
    lora_b_sha256: str
    constraint_rank: int
    adapter_rank: int
    target_max_abs_error: float
    protected_max_abs_delta: float


def compile_graph_authored_residual_adapter(
    substrate,
    derivation,
    residuals: Mapping[str, torch.Tensor],
) -> ResidualAdapterArtifact:
    """Solve D = A B H exactly for the graph-authored ordered constraints."""
    derivation_attrs = substrate.node(derivation)["attrs"]
    if derivation_attrs.get("status") != "ready_for_compilation":
        raise ValueError("graph has not authorized adapter compilation")
    if derivation_attrs.get("compiler") != "minimum_norm_right_inverse":
        raise ValueError("unsupported graph-authored adapter compiler")

    sets = list(substrate._inner.neighbours(
        derivation, "compiles_behavior_constraint_set",
    ))
    interfaces = list(substrate._inner.neighbours(
        derivation, "uses_residual_output_interface",
    ))
    if len(sets) != 1 or len(interfaces) != 1:
        raise ValueError("derivation does not identify one constraint interface")
    constraints = list(substrate._inner.neighbours(
        sets[0], "has_behavior_constraint",
    ))
    constraints.sort(
        key=lambda node: substrate.node(node)["attrs"]["constraint_order"]
    )
    interface_attrs = substrate.node(interfaces[0])["attrs"]
    hidden_width = int(interface_attrs["hidden_width"])
    vocabulary_width = int(interface_attrs["vocabulary_width"])

    columns = []
    context_ids = []
    for constraint in constraints:
        attrs = substrate.node(constraint)["attrs"]
        context_id = str(attrs["context_id"])
        if context_id not in residuals:
            raise ValueError(f"missing residual for {context_id}")
        column = residuals[context_id].detach().to(
            device="cpu", dtype=torch.float64,
        ).reshape(-1)
        if column.numel() != hidden_width:
            raise ValueError(f"wrong residual width for {context_id}")
        substrate.set_attr(constraint, "residual_status", "captured")
        substrate.set_attr(
            constraint, "residual_sha256", _tensor_sha256(column),
        )
        columns.append(column)
        context_ids.append(context_id)

    h = torch.stack(columns, dim=1)
    constraint_rank = int(torch.linalg.matrix_rank(h).item())
    if constraint_rank != h.shape[1]:
        raise ValueError("context residual constraints are not independent")

    desired = torch.zeros(
        vocabulary_width, len(constraints), dtype=torch.float64,
    )
    for column, constraint in enumerate(constraints):
        attrs = substrate.node(constraint)["attrs"]
        if attrs["constraint_kind"] == "zero_adapter_output":
            continue
        if attrs["constraint_kind"] == "greedy_token_winner":
            target = int(attrs["target_token_id"])
            delta = float(attrs["desired_target_delta"])
            if not (0 <= target < vocabulary_width and delta > 0):
                raise ValueError("invalid graph-derived greedy-winner constraint")
            desired[target, column] += delta
            continue
        if attrs["constraint_kind"] != "pairwise_token_logit_shift":
            raise ValueError("unsupported behavioral constraint")
        target = int(attrs["target_token_id"])
        alternative = int(attrs["alternative_token_id"])
        delta = float(attrs["desired_pair_delta"])
        if not (
            0 <= target < vocabulary_width
            and 0 <= alternative < vocabulary_width
            and target != alternative
            and delta > 0
        ):
            raise ValueError("invalid graph-authored token-logit constraint")
        desired[target, column] += delta / 2.0
        desired[alternative, column] -= delta / 2.0

    # H has shape [hidden, constraints]. Full column rank makes H+ H = I.
    # Factor D=U S V^T at its exact numerical rank, then choose
    # A=U S and B=V^T H+. Thus ABH=D while the serialized inner dimension is
    # rank(D), not the (usually much larger) number of constraints.
    u, singular_values, vh = torch.linalg.svd(
        desired, full_matrices=False,
    )
    tolerance = (
        max(desired.shape)
        * torch.finfo(desired.dtype).eps
        * singular_values[0]
    )
    adapter_rank = int((singular_values > tolerance).sum().item())
    if adapter_rank == 0:
        raise ValueError("behavioral specification has no target output delta")
    lora_a = (
        u[:, :adapter_rank] * singular_values[:adapter_rank]
    ).to(torch.float32)
    lora_b = (
        vh[:adapter_rank] @ torch.linalg.pinv(h)
    ).to(torch.float32)
    # Witness the factors that are actually serialized and installed, rather
    # than the higher-precision intermediates used to construct them.
    witnessed = (
        lora_a.to(torch.float64)
        @ (lora_b.to(torch.float64) @ h)
    )
    target_mask = desired.abs().sum(dim=0) > 0
    protected_mask = ~target_mask
    target_error = (
        (witnessed[:, target_mask] - desired[:, target_mask]).abs().max()
        if bool(target_mask.any()) else torch.tensor(0.0)
    )
    protected_delta = (
        witnessed[:, protected_mask].abs().max()
        if bool(protected_mask.any()) else torch.tensor(0.0)
    )
    return ResidualAdapterArtifact(
        lora_a=lora_a,
        lora_b=lora_b,
        context_ids=tuple(context_ids),
        context_matrix_sha256=_tensor_sha256(h),
        lora_a_sha256=_tensor_sha256(lora_a),
        lora_b_sha256=_tensor_sha256(lora_b),
        constraint_rank=constraint_rank,
        adapter_rank=adapter_rank,
        target_max_abs_error=float(target_error.item()),
        protected_max_abs_delta=float(protected_delta.item()),
    )


def record_residual_adapter_witness(
    substrate,
    derivation,
    artifact: ResidualAdapterArtifact,
):
    """Expose compiler numerics to Rules; Rules, not Python, accept them."""
    witness = substrate.add_node("ResidualAdapterWitness", {
        "compiler": "minimum_norm_right_inverse",
        "constraint_rank": float(artifact.constraint_rank),
        "adapter_rank": float(artifact.adapter_rank),
        "context_count": float(len(artifact.context_ids)),
        "context_matrix_sha256": artifact.context_matrix_sha256,
        "lora_a_sha256": artifact.lora_a_sha256,
        "lora_b_sha256": artifact.lora_b_sha256,
        "target_max_abs_error": artifact.target_max_abs_error,
        "protected_max_abs_delta": artifact.protected_max_abs_delta,
        "factors_finite": float(
            torch.isfinite(artifact.lora_a).all()
            and torch.isfinite(artifact.lora_b).all()
        ),
        "status": "observed",
        "provenance_kind": "deterministic_linear_algebra_witness",
    })
    _add_edge(substrate._inner, derivation, "has_residual_adapter_witness",
              witness)
    return witness


class _OutputOnlyLowRankAdapter(torch.nn.Module):
    def __init__(self, artifact: ResidualAdapterArtifact):
        super().__init__()
        self.register_buffer("lora_a", artifact.lora_a)
        self.register_buffer("lora_b", artifact.lora_b)

    def forward(self, residual: torch.Tensor) -> torch.Tensor:
        value = residual.to(dtype=self.lora_b.dtype)
        return torch.nn.functional.linear(
            torch.nn.functional.linear(value, self.lora_b), self.lora_a,
        )


@dataclass
class InstalledResidualAdapter:
    hook: object
    adapter: torch.nn.Module
    output_weight_sha256: str

    def remove(self) -> None:
        self.hook.remove()


def install_graph_authored_output_adapter(
    output_module,
    patch_attrs: dict,
    artifact: ResidualAdapterArtifact,
) -> InstalledResidualAdapter:
    """Install a proved output-only hook without touching tied embeddings."""
    if patch_attrs.get("status") != "proved":
        raise ValueError("refusing unproved contextual model patch")
    if patch_attrs.get("transformation_kind") != (
        "add_output_only_residual_adapter"
    ):
        raise ValueError("unsupported contextual model transformation")
    if _tensor_sha256(output_module.weight) != (
        patch_attrs["source_weight_sha256"]
    ):
        raise ValueError("output weight hash does not match proved patch")
    if artifact.lora_a_sha256 != patch_attrs["lora_a_sha256"]:
        raise ValueError("adapter A hash does not match proved patch")
    if artifact.lora_b_sha256 != patch_attrs["lora_b_sha256"]:
        raise ValueError("adapter B hash does not match proved patch")

    adapter = _OutputOnlyLowRankAdapter(artifact).to(
        device=output_module.weight.device,
    )

    def add_adapter(module, inputs, output):
        del module
        return output + adapter(inputs[0])

    hook = output_module.register_forward_hook(add_adapter)
    return InstalledResidualAdapter(
        hook=hook,
        adapter=adapter,
        output_weight_sha256=_tensor_sha256(output_module.weight),
    )


__all__ = [
    "InstalledResidualAdapter",
    "ResidualAdapterArtifact",
    "adapter_derivation",
    "authored_contextual_patch",
    "compile_graph_authored_residual_adapter",
    "ingest_language_model_output_ir",
    "install_graph_authored_output_adapter",
    "record_residual_adapter_witness",
    "request_contextual_vocabulary_edit",
]
