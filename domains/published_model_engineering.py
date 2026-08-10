"""Mechanical boundary for graph-native understanding of published models.

This module translates published PyTorch structure and Python control flow
into graph IR, then compiles only proof-carrying transformations already
authored by Rust graph Rules. It does not infer mechanisms, select edits, or
decide whether a proof obligation is satisfied.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import inspect
from pathlib import Path
import textwrap

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


def _model_sha256(model) -> str:
    digest = hashlib.sha256()
    for name, tensor in model.state_dict().items():
        digest.update(name.encode("utf-8"))
        digest.update(_tensor_sha256(tensor).encode("ascii"))
    return digest.hexdigest()


def ingest_pytorch_model_ir(substrate, agent, model, *, published_name: str):
    """Expose module, parameter, containment, and exact partition structure."""
    inner = substrate._inner
    external_model = substrate.add_node("ExternalModel", {
        "name": published_name,
        "framework": "pytorch",
        "model_class": type(model).__name__,
        "state_sha256": _model_sha256(model),
        "semantics": "deterministic_forward_program",
        "provenance_kind": "published_model_introspection",
    })
    _add_edge(inner, agent, "understands_external_model", external_model)

    operators = {}
    module_objects = {}
    for order, (name, module) in enumerate(model.named_modules()):
        if not name:
            continue
        attrs = {
            "name": name,
            "operator_class": type(module).__name__,
            "operator_order": float(order),
            "deterministic_semantics": 1.0,
            "provenance_kind": "published_module_structure",
        }
        if (
            hasattr(module, "n_head")
            and hasattr(module, "out")
            and hasattr(module.out, "in_features")
        ):
            width = int(module.out.in_features)
            heads = int(module.n_head)
            attrs.update({
                "operator_kind": "multi_head_attention",
                "state_width": float(width),
                "partition_count": float(heads),
                "partition_width": float(width // heads),
                "partition_layout": "contiguous_concatenation",
                "output_is_affine_in_partition": 1.0,
                "equation": "y=W_o concat(h_0,...,h_n)+b_o",
            })
        elif isinstance(module, torch.nn.Linear):
            attrs.update({
                "operator_kind": "affine",
                "input_width": float(module.in_features),
                "output_width": float(module.out_features),
                "equation": "y=W x+b",
            })
        elif isinstance(module, torch.nn.Conv1d):
            attrs.update({
                "operator_kind": "convolution_1d",
                "input_width": float(module.in_channels),
                "output_width": float(module.out_channels),
            })
        elif isinstance(module, torch.nn.LayerNorm):
            attrs["operator_kind"] = "layer_normalization"
        elif isinstance(module, torch.nn.Embedding):
            attrs["operator_kind"] = "embedding"
        else:
            attrs["operator_kind"] = "composite_or_nonlinear"
        node = substrate.add_node("ModelOperator", attrs)
        operators[name] = node
        module_objects[name] = module
        _add_edge(inner, external_model, "has_model_operator", node)

    for name, node in operators.items():
        parent_name = name.rsplit(".", 1)[0] if "." in name else ""
        if parent_name in operators:
            _add_edge(inner, node, "nested_in_model_operator", operators[parent_name])

    parameters = {}
    parameter_objects = {}
    for name, parameter in model.named_parameters():
        owner_name = name.rsplit(".", 1)[0]
        node = substrate.add_node("ModelParameter", {
            "name": name,
            "shape": "x".join(str(part) for part in parameter.shape),
            "rank": float(parameter.ndim),
            "element_count": float(parameter.numel()),
            "dtype": str(parameter.dtype),
            "content_sha256": _tensor_sha256(parameter),
            "hash_state": "observed",
            "trainable": float(parameter.requires_grad),
            "provenance_kind": "published_parameter_structure",
        })
        parameters[name] = node
        parameter_objects[name] = parameter
        _add_edge(inner, external_model, "has_model_parameter", node)
        if owner_name in operators:
            _add_edge(inner, operators[owner_name], "owns_model_parameter", node)

    partitions = {}
    for name, operator in operators.items():
        attrs = substrate.node(operator)["attrs"]
        if attrs.get("operator_kind") != "multi_head_attention":
            continue
        count = int(attrs["partition_count"])
        width = int(attrs["partition_width"])
        output_parameter_name = f"{name}.out.weight"
        output_parameter = parameters[output_parameter_name]
        for index in range(count):
            start = index * width
            end = start + width
            partition_name = f"{name}.head.{index}"
            partition = substrate.add_node("ModelInputPartition", {
                "name": partition_name,
                "partition_kind": "attention_head",
                "partition_index": float(index),
                "start": float(start),
                "end": float(end),
                "width": float(width),
                "bounds_valid": 1.0,
                "exclusive_contiguous_slice": 1.0,
                "provenance_kind": "derived_from_published_tensor_layout",
            })
            partitions[partition_name] = partition
            _add_edge(inner, external_model, "has_model_partition", partition)
            _add_edge(inner, partition, "partition_of_model_operator", operator)
            _add_edge(
                inner, partition, "controls_columns_of_parameter",
                output_parameter,
            )

    return {
        "model": external_model,
        "operators": operators,
        "parameters": parameters,
        "partitions": partitions,
        "module_objects": module_objects,
        "parameter_objects": parameter_objects,
    }


def ingest_affine_classifier_ir(
    substrate, ir: dict, *, operator_name: str, labels: list[str],
):
    """Expose the row/class correspondence of a published affine head."""
    module = ir["module_objects"][operator_name]
    if not isinstance(module, torch.nn.Linear):
        raise TypeError(f"{operator_name} is not an affine classifier")
    if module.bias is None:
        raise ValueError("classifier IR currently requires an explicit bias")
    if len(labels) != module.out_features:
        raise ValueError("label count does not match classifier output width")

    substrate.set_attr(
        ir["operators"][operator_name], "output_semantics", "class_logits",
    )
    substrate.set_attr(
        ir["operators"][operator_name],
        "class_count", float(module.out_features),
    )
    weight = ir["parameters"][f"{operator_name}.weight"]
    bias = ir["parameters"][f"{operator_name}.bias"]
    classes = {}
    for index, label in enumerate(labels):
        node = substrate.add_node("ModelOutputClass", {
            "label": str(label),
            "class_index": float(index),
            "row_bounds_valid": 1.0,
            "provenance_kind": "published_classifier_label_order",
        })
        classes[str(label)] = node
        _add_edge(
            substrate._inner, ir["model"], "has_model_output_class", node,
        )
        _add_edge(
            substrate._inner, node, "output_class_of_operator",
            ir["operators"][operator_name],
        )
        _add_edge(
            substrate._inner, node, "controls_weight_row", weight,
        )
        _add_edge(
            substrate._inner, node, "controls_bias_element", bias,
        )
    return classes


def _ast_identifiers(node: ast.AST) -> list[str]:
    identifiers = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            identifiers.append(child.id)
        elif isinstance(child, ast.Attribute):
            identifiers.append(child.attr)
    return list(dict.fromkeys(identifiers))


def ingest_python_policy_ir(substrate, external_model, function):
    """Translate assignments, guards, and data dependencies from source AST."""
    inner = substrate._inner
    source = textwrap.dedent(inspect.getsource(function))
    source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    source_path = str(Path(inspect.getsourcefile(function) or "").resolve())
    tree = ast.parse(source)
    signal_nodes = {}

    def signal(identifier):
        if identifier not in signal_nodes:
            node = substrate.add_node("ProgramSignal", {
                "identifier": identifier,
                "role": "unclassified",
                "provenance_kind": "python_ast_identifier",
            })
            signal_nodes[identifier] = node
            _add_edge(inner, external_model, "has_program_signal", node)
        return signal_nodes[identifier]

    assignments = []

    def walk(node, guards):
        next_guards = guards
        if isinstance(node, ast.If):
            guard = substrate.add_node("ProgramGuard", {
                "source_path": source_path,
                "source_sha256": source_sha256,
                "line": float(node.lineno),
                "expression": ast.unparse(node.test),
                "provenance_kind": "python_ast_control_flow",
            })
            _add_edge(inner, external_model, "has_program_guard", guard)
            for identifier in _ast_identifiers(node.test):
                _add_edge(inner, guard, "reads_program_signal", signal(identifier))
            next_guards = guards + [guard]
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                segment = ast.get_source_segment(source, node) or ast.unparse(node)
                value_kind = (
                    "literal_false"
                    if isinstance(value, ast.Constant) and value.value is False
                    else "literal_true"
                    if isinstance(value, ast.Constant) and value.value is True
                    else "expression"
                )
                assignment = substrate.add_node("ProgramAssignment", {
                    "target_identifier": target.id,
                    "value_kind": value_kind,
                    "source_path": source_path,
                    "source_sha256": source_sha256,
                    "line": float(node.lineno),
                    "source_segment": segment,
                    "provenance_kind": "python_ast_assignment",
                })
                assignments.append((node.lineno, target.id, assignment))
                _add_edge(inner, external_model, "has_program_assignment", assignment)
                _add_edge(inner, assignment, "writes_program_signal", signal(target.id))
                for identifier in _ast_identifiers(value):
                    _add_edge(
                        inner, assignment, "reads_program_signal",
                        signal(identifier),
                    )
                for guard in guards:
                    _add_edge(inner, guard, "controls_program_assignment", assignment)
        for child in ast.iter_child_nodes(node):
            walk(child, next_guards)

    walk(tree, [])
    by_target = {}
    for line, target, assignment in assignments:
        by_target.setdefault(target, []).append((line, assignment))
    for target_assignments in by_target.values():
        target_assignments.sort(key=lambda item: item[0])
        for earlier, later in zip(target_assignments, target_assignments[1:]):
            _add_edge(
                inner, earlier[1],
                "followed_by_same_target_assignment", later[1],
            )
    return {
        "source": source,
        "source_sha256": source_sha256,
        "source_path": source_path,
        "signals": signal_nodes,
        "assignments": [assignment for _line, _target, assignment in assignments],
    }


def request_partition_transformation(
    substrate, agent, partition, *, factor: float,
):
    """Lay an externally requested outcome; graph derives and authors the edit."""
    goal = substrate.add_node("ModelEnhancementGoal", {
        "intent": "scale_additive_partition",
        "factor": float(factor),
        "status": "requested",
        "provenance_kind": "external_engineering_request",
    })
    _add_edge(substrate._inner, agent, "has_model_enhancement_goal", goal)
    _add_edge(substrate._inner, goal, "targets_model_partition", partition)
    return goal


def request_class_swap_transformation(
    substrate, agent, class_a, class_b,
):
    """Request a semantic output permutation; graph must derive the edit."""
    goal = substrate.add_node("ModelEnhancementGoal", {
        "intent": "swap_output_classes",
        "status": "requested",
        "provenance_kind": "external_engineering_request",
    })
    _add_edge(substrate._inner, agent, "has_model_enhancement_goal", goal)
    _add_edge(substrate._inner, goal, "swaps_output_class_a", class_a)
    _add_edge(substrate._inner, goal, "swaps_output_class_b", class_b)
    return goal


def authored_model_patch(substrate, goal):
    patches = list(
        substrate._inner.neighbours(goal, "authored_deterministic_model_patch")
    )
    if len(patches) > 1:
        raise RuntimeError(f"graph authored {len(patches)} model patches")
    return patches[0] if patches else None


def derived_mechanisms(substrate, external_model):
    return list(
        substrate._inner.neighbours(
            external_model, "has_derived_model_mechanism",
        )
    )


def engineering_affordances(substrate, external_model):
    """Read exact transformation capabilities already derived by the graph."""
    return list(
        substrate._inner.neighbours(
            external_model, "has_engineering_affordance",
        )
    )


@dataclass
class AppliedParameterPatch:
    parameter_name: str
    start: int
    end: int
    factor: float
    original_columns: torch.Tensor
    before_parameter_sha256: str
    after_parameter_sha256: str
    before_model_sha256: str
    after_model_sha256: str


@dataclass
class AppliedClassSwapPatch:
    weight_name: str
    bias_name: str
    class_a: int
    class_b: int
    original_weight_rows: torch.Tensor
    original_bias_elements: torch.Tensor
    before_model_sha256: str
    after_model_sha256: str
    augmented_update_rank: int
    lora_a: torch.Tensor
    lora_b_augmented: torch.Tensor


def apply_authored_parameter_patch(model, patch_attrs: dict) -> AppliedParameterPatch:
    """Compile one graph-authored affine-column transformation exactly."""
    if patch_attrs.get("status") != "proved":
        raise ValueError("refusing unproved model patch")
    if patch_attrs.get("transformation_kind") != "scale_parameter_columns":
        raise ValueError("unsupported deterministic transformation")
    name = str(patch_attrs["parameter_name"])
    parameters = dict(model.named_parameters())
    parameter = parameters[name]
    start = int(patch_attrs["start"])
    end = int(patch_attrs["end"])
    factor = float(patch_attrs["factor"])
    before_parameter = _tensor_sha256(parameter)
    if before_parameter != patch_attrs["source_parameter_sha256"]:
        raise ValueError("source parameter hash does not match proved patch")
    if not (parameter.ndim == 2 and 0 <= start < end <= parameter.shape[1]):
        raise ValueError("proved column slice does not match live parameter")
    before_model = _model_sha256(model)
    original = parameter[:, start:end].detach().clone()
    with torch.no_grad():
        parameter[:, start:end].mul_(factor)
    return AppliedParameterPatch(
        parameter_name=name,
        start=start,
        end=end,
        factor=factor,
        original_columns=original,
        before_parameter_sha256=before_parameter,
        after_parameter_sha256=_tensor_sha256(parameter),
        before_model_sha256=before_model,
        after_model_sha256=_model_sha256(model),
    )


def revert_parameter_patch(model, receipt: AppliedParameterPatch) -> str:
    parameter = dict(model.named_parameters())[receipt.parameter_name]
    with torch.no_grad():
        parameter[:, receipt.start:receipt.end].copy_(receipt.original_columns)
    return _model_sha256(model)


def apply_authored_class_swap_patch(
    model, patch_attrs: dict,
) -> AppliedClassSwapPatch:
    """Compile a proved class permutation as an exact rank-one update."""
    if patch_attrs.get("status") != "proved":
        raise ValueError("refusing unproved model patch")
    if patch_attrs.get("transformation_kind") != "swap_affine_output_rows":
        raise ValueError("unsupported deterministic transformation")
    parameters = dict(model.named_parameters())
    weight_name = str(patch_attrs["weight_parameter_name"])
    bias_name = str(patch_attrs["bias_parameter_name"])
    weight = parameters[weight_name]
    bias = parameters[bias_name]
    if _tensor_sha256(weight) != patch_attrs["source_weight_sha256"]:
        raise ValueError("classifier weight hash does not match proved patch")
    if _tensor_sha256(bias) != patch_attrs["source_bias_sha256"]:
        raise ValueError("classifier bias hash does not match proved patch")
    class_a = int(patch_attrs["class_a_index"])
    class_b = int(patch_attrs["class_b_index"])
    if not (
        weight.ndim == 2
        and bias.ndim == 1
        and weight.shape[0] == bias.shape[0]
        and 0 <= class_a < weight.shape[0]
        and 0 <= class_b < weight.shape[0]
        and class_a != class_b
    ):
        raise ValueError("proved class rows do not match live parameters")

    before_model = _model_sha256(model)
    rows = weight[[class_a, class_b]].detach().clone()
    elements = bias[[class_a, class_b]].detach().clone()
    output_width, input_width = weight.shape
    lora_a = torch.zeros(
        output_width, 1, dtype=weight.dtype, device=weight.device,
    )
    lora_a[class_a, 0] = 1
    lora_a[class_b, 0] = -1
    row_delta = rows[1] - rows[0]
    bias_delta = elements[1] - elements[0]
    lora_b_augmented = torch.cat(
        (row_delta, bias_delta.reshape(1)),
    ).reshape(1, input_width + 1)
    augmented_delta = lora_a @ lora_b_augmented

    with torch.no_grad():
        weight[class_a].copy_(rows[1])
        weight[class_b].copy_(rows[0])
        bias[class_a].copy_(elements[1])
        bias[class_b].copy_(elements[0])
    return AppliedClassSwapPatch(
        weight_name=weight_name,
        bias_name=bias_name,
        class_a=class_a,
        class_b=class_b,
        original_weight_rows=rows,
        original_bias_elements=elements,
        before_model_sha256=before_model,
        after_model_sha256=_model_sha256(model),
        augmented_update_rank=int(torch.linalg.matrix_rank(
            augmented_delta.detach().cpu(),
        ).item()),
        lora_a=lora_a.detach().cpu(),
        lora_b_augmented=lora_b_augmented.detach().cpu(),
    )


def revert_class_swap_patch(model, receipt: AppliedClassSwapPatch) -> str:
    parameters = dict(model.named_parameters())
    weight = parameters[receipt.weight_name]
    bias = parameters[receipt.bias_name]
    with torch.no_grad():
        weight[receipt.class_a].copy_(receipt.original_weight_rows[0])
        weight[receipt.class_b].copy_(receipt.original_weight_rows[1])
        bias[receipt.class_a].copy_(receipt.original_bias_elements[0])
        bias[receipt.class_b].copy_(receipt.original_bias_elements[1])
    return _model_sha256(model)


def compile_source_transformation(source: str, transform_attrs: dict) -> str:
    """Apply one graph-authored assignment-preservation edit to source text."""
    if transform_attrs.get("status") != "proved":
        raise ValueError("refusing unproved source transformation")
    if transform_attrs.get("transformation_kind") != "preserve_prior_boolean":
        raise ValueError("unsupported source transformation")
    line = int(transform_attrs["target_line"])
    target = str(transform_attrs["target_identifier"])
    live_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if live_hash != transform_attrs["source_sha256"]:
        raise ValueError("source hash does not match proved transformation")
    lines = source.splitlines()
    original = lines[line - 1]
    if original.strip() != str(transform_attrs["target_source_segment"]).strip():
        raise ValueError("target assignment does not match proved transformation")
    indentation = original[:len(original) - len(original.lstrip())]
    lines[line - 1] = f"{indentation}{target} = {target}"
    return "\n".join(lines) + ("\n" if source.endswith("\n") else "")


def audit_no_engineering_decisions() -> list[str]:
    """Conservative audit: adapter may address exact graph-authored targets only."""
    module = inspect.getmodule(audit_no_engineering_decisions)
    tree = ast.parse(inspect.getsource(module))
    violations = []
    forbidden = {"argmin", "argmax", "argsort"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            violations.append(f"line {node.lineno}: host {node.attr}")
    return violations


__all__ = [
    "AppliedClassSwapPatch",
    "AppliedParameterPatch",
    "apply_authored_class_swap_patch",
    "apply_authored_parameter_patch",
    "audit_no_engineering_decisions",
    "authored_model_patch",
    "compile_source_transformation",
    "derived_mechanisms",
    "engineering_affordances",
    "ingest_affine_classifier_ir",
    "ingest_python_policy_ir",
    "ingest_pytorch_model_ir",
    "request_partition_transformation",
    "request_class_swap_transformation",
    "revert_class_swap_patch",
    "revert_parameter_patch",
]
