"""Mechanical instrumentation for graph-native diagnosis of published nets.

This module exposes PyTorch modules as graph evidence and enacts only the
intervention or RuntimeNetworkPatch already selected by substrate Rules. It
does not rank components, update hypotheses, or select a repair.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import hashlib
import inspect

import torch


def _add_edge(inner, src, edge_type, tgt):
    try:
        inner.add_edge_unchecked(src, edge_type, tgt)
    except TypeError:
        inner.add_edge_unchecked(src, edge_type, tgt, {})


def enumerate_whisper_components(model) -> list[dict]:
    """Translate the published hierarchy into a stable intervention grammar."""
    components = []
    order = 0
    for side, blocks in (
        ("encoder", model.encoder.blocks),
        ("decoder", model.decoder.blocks),
    ):
        for layer, block in enumerate(blocks):
            modules = [("self_attention", block.attn), ("mlp", block.mlp)]
            if block.cross_attn is not None:
                modules.insert(1, ("cross_attention", block.cross_attn))
            for kind, module in modules:
                name = f"{side}.blocks.{layer}.{kind}"
                components.append({
                    "name": name,
                    "side": side,
                    "layer": layer,
                    "kind": kind,
                    "level": 0,
                    "order": order,
                    "module": module,
                    "head_index": None,
                    "parent": None,
                })
                order += 1
                if kind != "mlp":
                    for head in range(module.n_head):
                        components.append({
                            "name": f"{name}.head.{head}",
                            "side": side,
                            "layer": layer,
                            "kind": kind,
                            "level": 1,
                            "order": order,
                            "module": module,
                            "head_index": head,
                            "parent": name,
                        })
                        order += 1
    return components


def lay_whisper_architecture(substrate, agent, study, model):
    """Lay components and containment. Returns mechanical name indexes."""
    inner = substrate._inner
    nodes = {}
    specs = {}
    for spec in enumerate_whisper_components(model):
        node = substrate.add_node("PublishedNetComponent", {
            "name": spec["name"],
            "network": "openai-whisper/base.en",
            "side": spec["side"],
            "layer": float(spec["layer"]),
            "kind": spec["kind"],
            "level": float(spec["level"]),
            "experiment_order": float(spec["order"]),
            "eligible": float(spec["level"] == 0),
            "tested": 0.0,
            "selected": 0.0,
            "causal_utility": 0.0,
            "causal_candidate": 0.0,
            "provenance_kind": "published_network_structure",
        })
        nodes[spec["name"]] = node
        specs[spec["name"]] = spec
        _add_edge(inner, study, "has_inspectable_component", node)
        _add_edge(inner, agent, "can_inspect_published_component", node)
    for name, spec in specs.items():
        if spec["parent"] is not None:
            _add_edge(
                inner, nodes[name], "part_of_published_component",
                nodes[spec["parent"]],
            )
    return nodes, specs


@contextmanager
def intervention_hook(spec):
    """Temporarily zero exactly the named residual contribution."""
    module = spec["module"]
    head = spec["head_index"]
    if spec["kind"] == "mlp":
        handle = module.register_forward_hook(
            lambda _m, _args, output: torch.zeros_like(output)
        )
    elif head is None:
        def zero_attention(_m, _args, output):
            return torch.zeros_like(output[0]), output[1]
        handle = module.register_forward_hook(zero_attention)
    else:
        width = module.out.in_features // module.n_head

        def zero_head(_m, args):
            value = args[0].clone()
            value[..., head * width:(head + 1) * width] = 0
            return (value, *args[1:])

        handle = module.out.register_forward_pre_hook(zero_head)
    try:
        yield
    finally:
        handle.remove()


def state_dict_sha256(model) -> str:
    """Byte identity witness over names, shapes, dtypes, and tensor contents."""
    digest = hashlib.sha256()
    for name, tensor in model.state_dict().items():
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def requested_intervention(substrate, study):
    """Read the graph's single pending request; never choose among requests."""
    requests = list(
        substrate._inner.neighbours(study, "requests_network_intervention")
    )
    pending = [
        request for request in requests
        if substrate.node(request)["attrs"].get("status") == "requested"
    ]
    if len(pending) > 1:
        raise RuntimeError(f"graph requested {len(pending)} interventions")
    return pending[0] if pending else None


def record_outcome(substrate, intervention, counts: dict):
    """Stamp mechanically measured counts for the graph to interpret."""
    outcome = substrate.add_node("InterventionOutcome", {
        **{key: float(value) for key, value in counts.items()},
        "status": "measured",
        "provenance_kind": "observed_do_intervention",
    })
    _add_edge(
        substrate._inner, intervention, "has_intervention_outcome", outcome
    )
    return outcome


def authored_patch(substrate, study):
    patches = list(substrate._inner.neighbours(study, "authored_runtime_patch"))
    if len(patches) > 1:
        raise RuntimeError(f"graph authored {len(patches)} patches")
    return patches[0] if patches else None


def authored_control(substrate, study):
    controls = list(
        substrate._inner.neighbours(
            study, "authored_deterministic_control",
        )
    )
    if len(controls) > 1:
        raise RuntimeError(f"graph authored {len(controls)} controls")
    return controls[0] if controls else None


def record_validation(substrate, patch, counts: dict):
    """Stamp prospective counts; graph Rules alone judge the repair."""
    validation = substrate.add_node("RepairValidationOutcome", {
        **{key: float(value) for key, value in counts.items()},
        "status": "measured",
        "provenance_kind": "prospective_held_out_measurement",
    })
    _add_edge(
        substrate._inner, patch, "has_repair_validation", validation
    )
    return validation


def requested_gate_intervention(substrate, study):
    requests = list(
        substrate._inner.neighbours(study, "requests_gate_intervention")
    )
    pending = [
        request for request in requests
        if substrate.node(request)["attrs"].get("status") == "requested"
    ]
    if len(pending) > 1:
        raise RuntimeError(f"graph requested {len(pending)} gate experiments")
    return pending[0] if pending else None


def record_gate_outcome(substrate, intervention, counts: dict):
    outcome = substrate.add_node("GateInterventionOutcome", {
        **{key: float(value) for key, value in counts.items()},
        "status": "measured",
        "provenance_kind": "observed_conditional_do_intervention",
    })
    _add_edge(
        substrate._inner, intervention,
        "has_gate_intervention_outcome", outcome,
    )
    return outcome


def authored_conditional_patch(substrate, study):
    patches = list(
        substrate._inner.neighbours(study, "authored_conditional_patch")
    )
    if len(patches) > 1:
        raise RuntimeError(
            f"graph authored {len(patches)} conditional patches"
        )
    return patches[0] if patches else None


def record_conditional_validation(substrate, patch, counts: dict):
    validation = substrate.add_node("RepairValidationOutcome", {
        **{key: float(value) for key, value in counts.items()},
        "status": "measured",
        "provenance_kind": "prospective_conditional_measurement",
    })
    _add_edge(
        substrate._inner, patch, "has_conditional_validation", validation
    )
    return validation


def audit_no_host_decisions() -> list[str]:
    """Reject ranking/choice operations in the mechanical adapter."""
    tree = ast.parse(inspect.getsource(inspect.getmodule(audit_no_host_decisions)))
    violations = []
    forbidden = {"min", "max", "sorted"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None)
            if name in forbidden:
                violations.append(f"line {node.lineno}: host {name}()")
        if isinstance(node, ast.Attribute) and node.attr in {
            "argmin", "argmax", "argsort",
        }:
            violations.append(f"line {node.lineno}: host {node.attr}")
    return violations


__all__ = [
    "authored_control",
    "authored_conditional_patch",
    "authored_patch",
    "audit_no_host_decisions",
    "enumerate_whisper_components",
    "intervention_hook",
    "lay_whisper_architecture",
    "record_outcome",
    "record_conditional_validation",
    "record_gate_outcome",
    "record_validation",
    "requested_intervention",
    "requested_gate_intervention",
    "state_dict_sha256",
]
