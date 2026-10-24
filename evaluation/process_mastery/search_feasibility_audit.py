"""Read-only finite-effect feasibility audits for P23.

This module accepts archived graph snapshots and emits external diagnostic
records. It does not boot or mutate an agent, qualify candidates, or access
sealed worlds.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
D4_ARTIFACT = ROOT / "evaluation/process_mastery/results/p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json"
D4_ROOT_ARTIFACT = ROOT / "evaluation/process_mastery/results/p22_four_arm_checkpoint_roots_d4_0520.json"
LOOPOVER_ARTIFACT = ROOT / "evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_g1_0924_0926_ticks60_depth3.json"


def _decode(value):
    if isinstance(value, dict):
        if set(value) == {"__list__"}:
            return [_decode(item) for item in value["__list__"]]
        return {key: _decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode(item) for item in value]
    return value


def _tuple_perm(value) -> tuple[int, ...]:
    decoded = _decode(value)
    if (not isinstance(decoded, list) or any(type(item) is not int for item in decoded)
            or sorted(decoded) != list(range(len(decoded)))):
        raise ValueError("effect must be a finite permutation")
    return tuple(decoded)


def compose(first: tuple[int, ...], second: tuple[int, ...]) -> tuple[int, ...]:
    """Match P22's destination-index ProcessCompose convention."""
    if len(first) != len(second):
        raise ValueError("permutation domains differ")
    return tuple(second[first[index]] for index in range(len(first)))


def inverse(effect: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(effect)
    for source, destination in enumerate(effect):
        result[destination] = source
    return tuple(result)


def _finite_closure(generators: list[tuple[str, tuple[int, ...]]], *,
                    max_depth: int | None = None,
                    max_nodes: int | None = None) -> tuple[dict[tuple[int, ...], tuple[str, ...]], bool]:
    size = len(generators[0][1])
    identity = tuple(range(size))
    paths = {identity: ()}
    queue = deque([identity])
    truncated = False
    while queue:
        current = queue.popleft()
        path = paths[current]
        if max_depth is not None and len(path) >= max_depth:
            continue
        for name, generator in generators:
            result = compose(current, generator)
            if result in paths:
                continue
            if max_nodes is not None and len(paths) >= max_nodes:
                truncated = True
                return paths, truncated
            paths[result] = (*path, name)
            queue.append(result)
    return paths, truncated


def _checkpoint(record: dict, *, path: tuple[str, ...] = ("parent_checkpoint",)) -> dict:
    selected = record
    for component in path:
        selected = selected[component]
    if not selected.get("native_graph_snapshot_json"):
        raise ValueError("checkpoint has no native graph snapshot")
    return selected


def _graph(checkpoint: dict) -> dict:
    return json.loads(checkpoint["native_graph_snapshot_json"])


def _attrs(graph: dict, node_type: str) -> Iterable[dict]:
    for node in graph.get("nodes", []):
        if node.get("type") == node_type and isinstance(node.get("attrs"), dict):
            yield _decode(node["attrs"])


def _task_effect(attrs: dict) -> tuple[int, ...]:
    initial = _tuple_perm(attrs["initial_state"])
    goal = _tuple_perm(attrs["goal"])
    if len(initial) != len(goal):
        raise ValueError("task initial and goal domains differ")
    # ProcessApply uses the same source-to-destination convention as the
    # world generator, so the effect is the unique permutation mapping initial
    # to goal.
    mapping = [0] * len(initial)
    for destination, value in enumerate(goal):
        mapping[initial.index(value)] = destination
    return tuple(mapping)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify_goal_pair(*, effect_reachable: bool, guard_passes: bool,
                       precondition_passes: bool,
                       source_novel: bool, child_novel: bool) -> str:
    """Keep predicate rejection separate from bounded reachability claims."""
    if not effect_reachable:
        return "UNKNOWN_OUTSIDE_BOUND"
    if not guard_passes:
        return "REJECTED_BY_NAMED_PREDICATE:guard_mismatch"
    if not precondition_passes:
        return "REJECTED_BY_NAMED_PREDICATE:precondition_failed"
    if not source_novel:
        return "REJECTED_BY_NAMED_PREDICATE:source_effect_not_novel"
    if not child_novel:
        return "REJECTED_BY_NAMED_PREDICATE:child_effect_not_novel"
    return "FINITE_WITNESS_FOUND"


def audit_d4_checkpoint(checkpoint: dict, *, task_checkpoint: dict | None = None,
                        composition_depth: int = 3) -> dict:
    """Enumerate D4 closure and training-only source/child feasibility."""
    if composition_depth < 0:
        raise ValueError("composition_depth must be nonnegative")
    graph = _graph(checkpoint)
    schemas = [attrs for attrs in _attrs(graph, "ProcessSchema")
        if attrs.get("domain") == "p22-development-d4"]
    active = [attrs for attrs in schemas if attrs.get("status") == "active"]
    generators = [(str(attrs.get("name")), _tuple_perm(attrs["params"]))
        for attrs in active if attrs.get("provenance") == "world_affordance"]
    if len(generators) < 2:
        raise ValueError("D4 checkpoint does not contain its two held generators")
    closure, _ = _finite_closure(generators)
    identity = tuple(range(4))
    active_effects = {_tuple_perm(attrs["params"]) for attrs in active}
    adopted_effects = {_tuple_perm(attrs.get("params")) for attrs in _attrs(
        graph, "OpenProcessCandidate")
        if attrs.get("domain") == "p22-development-d4"
        and attrs.get("status") == "adopted_candidate"
        and attrs.get("adoption_status") == "approved"}
    known = active_effects | adopted_effects | {identity}
    remaining = sorted(set(closure) - known)
    expression_paths, _ = _finite_closure(generators, max_depth=composition_depth)
    task_graph = _graph(task_checkpoint or checkpoint)
    tasks = [attrs for attrs in _attrs(task_graph, "SolveTask")
        if attrs.get("domain") == "p22-development-d4"
        and attrs.get("split") == "training"]
    task_rows = []
    for attrs in tasks:
        task_rows.append({"task_key": attrs.get("training_trial_key"),
            "goal_effect": _task_effect(attrs),
            "initial_state": _tuple_perm(attrs["initial_state"])})

    records = []
    for source_effect in remaining:
        source_tasks = [row for row in task_rows if row["goal_effect"] == source_effect]
        pair_records = []
        for source_task in source_tasks:
            for child_task in task_rows:
                if (child_task["task_key"] == source_task["task_key"]
                        or child_task["goal_effect"] == source_task["goal_effect"]):
                    continue
                child_effect = child_task["goal_effect"]
                residual = compose(inverse(source_effect), child_effect)
                path = expression_paths.get(residual)
                status = classify_goal_pair(effect_reachable=True,
                    # For finite D4, composition paths are exhaustive only up
                    # to this stated grammar-depth bound.
                    guard_passes=(source_task["initial_state"]
                                  == child_task["initial_state"]),
                    precondition_passes=(source_task["initial_state"]
                                         == tuple(range(4))),
                    source_novel=source_effect not in known,
                    child_novel=child_effect not in known) if path is not None else \
                    "UNKNOWN_OUTSIDE_BOUND"
                pair_records.append({"source_training_task": source_task["task_key"],
                    "independent_training_task": child_task["task_key"],
                    "source_effect": source_effect,
                    "child_effect": child_effect,
                    "residual_composition": residual,
                    "residual_grammar_path": path,
                    "status": status})
        witness = next((pair for pair in pair_records
                        if pair["status"] == "FINITE_WITNESS_FOUND"), None)
        pair_status_counts = dict(sorted(Counter(
            pair["status"] for pair in pair_records).items()))
        if witness:
            feasibility = "FINITE_WITNESS_FOUND"
        elif not pair_records:
            feasibility = "UNKNOWN_NO_DISTINCT_NOVEL_TRAINING_GOAL_PAIR"
        elif "UNKNOWN_OUTSIDE_BOUND" in pair_status_counts:
            feasibility = "UNKNOWN_OUTSIDE_BOUND"
        else:
            feasibility = "NO_ADMISSIBLE_TRAINING_GOAL_PAIR_WITHIN_REGISTERED_CONTEXT"
        records.append({"effect": source_effect,
            "is_identity": source_effect == identity,
            "is_active_or_adopted": source_effect in active_effects | adopted_effects,
            "training_source_task_count": len(source_tasks),
            "goal_pair_records": pair_records,
            "goal_pair_status_counts": pair_status_counts,
            "qualification_feasibility": feasibility,
            "witness": witness,
            "native_qualification": "NOT_ESTABLISHED_REQUIRES_NATIVE_VERIFIED_TRIALS"})

    return {"schema": "p23_d4_effect_feasibility_v1",
        "scope": "external_read_only_training_diagnostic",
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "checkpoint_digest": checkpoint.get("checkpoint_digest"),
        "generator_effects": [{"name": name, "effect": effect}
                              for name, effect in generators],
        "closure_size": len(closure),
        "closure_effects": sorted(closure),
        "active_effects": sorted(active_effects),
        "adopted_effects": sorted(adopted_effects),
        "identity_effect": identity,
        "remaining_novel_nonidentity_effects": remaining,
        "composition_depth_bound": composition_depth,
        "training_goal_count": len(task_rows),
        "records": records,
        "heldout_accessed": False,
        "agent_graph_mutated": False}


def audit_loopover_checkpoint(checkpoint: dict, *, max_depth: int = 3,
                              max_nodes: int = 100_000) -> dict:
    """Bounded Loopover BFS over active world primitives and training tasks."""
    if max_depth < 0 or max_nodes < 1:
        raise ValueError("invalid Loopover BFS bounds")
    graph = _graph(checkpoint)
    schemas = [attrs for attrs in _attrs(graph, "ProcessSchema")
        if attrs.get("domain") == "p22-development-loopover"
        and attrs.get("status") == "active"
        and attrs.get("provenance") == "world_affordance"]
    generators = [(str(attrs.get("name")), _tuple_perm(attrs["params"]))
        for attrs in schemas]
    if not generators:
        raise ValueError("Loopover checkpoint has no active world primitives")
    paths, truncated = _finite_closure(generators,
        max_depth=max_depth, max_nodes=max_nodes)
    tasks = [attrs for attrs in _attrs(graph, "SolveTask")
        if attrs.get("domain") == "p22-development-loopover"
        and attrs.get("split") == "training"]
    witnesses = []
    for attrs in tasks:
        effect = _task_effect(attrs)
        path = paths.get(effect)
        witnesses.append({"task_key": attrs.get("training_trial_key"),
            "effect": effect,
            "status": "WITNESS_FOUND" if path is not None else "UNKNOWN_OUTSIDE_BOUND",
            "grammar_path": path,
            "minimum_depth": len(path) if path is not None else None})
    primitive_effects = {effect for _, effect in generators}
    return {"schema": "p23_loopover_bounded_feasibility_v1",
        "scope": "external_read_only_training_diagnostic",
        "checkpoint_id": checkpoint.get("checkpoint_id"),
        "checkpoint_digest": checkpoint.get("checkpoint_digest"),
        "max_depth": max_depth, "max_nodes": max_nodes,
        "visited_effect_count": len(paths), "node_bound_reached": truncated,
        "primitive_count": len(generators),
        "primitive_witnesses": [{"name": name, "effect": effect,
            "grammar_path": paths.get(effect)} for name, effect in generators],
        "training_goal_witnesses": witnesses,
        "unknown_goal_count": sum(row["status"] == "UNKNOWN_OUTSIDE_BOUND"
                                   for row in witnesses),
        "absence_claim": "UNKNOWN_OUTSIDE_BOUND; never global unreachability",
        "heldout_accessed": False, "agent_graph_mutated": False}


def run_default_audits(*, loopover_depth: int = 3,
                       loopover_node_bound: int = 100_000) -> dict:
    d4_record = json.loads(D4_ARTIFACT.read_text())
    d4_root_record = json.loads(D4_ROOT_ARTIFACT.read_text())
    loopover_record = json.loads(LOOPOVER_ARTIFACT.read_text())
    d4_generation_zero = d4_root_record["arms"]["invention_only"][
        "generation_zero_checkpoint"]
    d4_generation_two = _checkpoint(d4_record)
    input_paths = [D4_ROOT_ARTIFACT, D4_ARTIFACT, LOOPOVER_ARTIFACT,
        Path(__file__).resolve(), ROOT / "evaluation/process_mastery/independent_worlds.py",
        ROOT / "scripts/gen_independent_improvement_seed.py",
        ROOT / "scripts/gen_open_process_search_seed.py",
        ROOT / "seeds/independent_improvement.json",
        ROOT / "seeds/open_process_search.json",
        ROOT / "docs/research/engine_substrate/COGNITION_SEARCH_DIAGNOSIS_CONTRACT.md"]
    return {"schema": "p23_search_feasibility_audit_v1",
        "input_hashes": {str(path.relative_to(ROOT)): _sha256(path)
                         for path in input_paths},
        "d4": {
            "generation_zero": audit_d4_checkpoint(d4_generation_zero,
                task_checkpoint=d4_generation_two),
            "generation_two": audit_d4_checkpoint(d4_generation_two),
        },
        "loopover": audit_loopover_checkpoint(_checkpoint(loopover_record),
            max_depth=loopover_depth, max_nodes=loopover_node_bound),
        "heldout_accessed": False, "agent_graph_mutated": False}


if __name__ == "__main__":
    print(json.dumps(run_default_audits(), indent=2, sort_keys=True))
