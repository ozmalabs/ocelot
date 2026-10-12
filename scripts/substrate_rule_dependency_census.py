#!/usr/bin/env python3
"""Extract conservative rule-dependency graphs from two active seed families.

This is source-structure analysis, not a runtime graph snapshot or a proof that
partitioned execution preserves the executor's semantics.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_rule_dependency_census_20260924.json"
SEED_PATHS = {
    "can_discrete_inference": "seeds/can_native_reimplementation.json",
    "conversation_deliberation": "seeds/conversation_deliberation_phase4a.json",
}
PARTITIONS_PER_GRAPH = 5
MAX_LEAF_RULES = 4


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def structural_helper():
    path = ROOT / "scripts/substrate_structural_census_pilot.py"
    spec = importlib.util.spec_from_file_location("substrate_structural_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the shared recursive partition helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def attribute_resource(key: str, node, variable_roles: dict[str, set[str]], scope: str) -> str:
    if scope == "global_key":
        return f"attr:{key}"
    if isinstance(node, dict) and node.get("type") == "Var":
        name = node.get("name")
        roles = sorted(variable_roles.get(name, set()))
        context = "+".join(roles) if roles else "unanchored"
        return f"attr:{key}@{context}"
    return f"attr:{key}@indirect"


def collect_term_reads(value, reads: set[str], variable_roles: dict[str, set[str]],
                       scope: str) -> None:
    if isinstance(value, list):
        for item in value:
            collect_term_reads(item, reads, variable_roles, scope)
        return
    if not isinstance(value, dict):
        return
    if "__term__" in value:
        collect_term_reads(value["__term__"], reads, variable_roles, scope)
        return
    term_type = value.get("type")
    if term_type == "Attr" and isinstance(value.get("key"), str):
        reads.add(attribute_resource(value["key"], value.get("node"), variable_roles, scope))
    elif term_type in ("Edges", "Neighbours", "InNeighbours", "MapNeighbours",
                       "ReachableFrom"):
        if isinstance(value.get("edge_type"), str):
            reads.add(f"edge:{value['edge_type']}")
        else:
            reads.add("wildcard:any_edge_type")
    elif term_type in ("TypeOf", "AttrByName", "EvalSubgraph", "SlideNeighbours"):
        reads.add(f"wildcard:dynamic_term:{term_type}")
    elif term_type == "EdgeAttr":
        reads.add("wildcard:edge_attribute_read")
    elif term_type in ("NodesOf", "NodesOfType", "NodesWhere") and isinstance(value.get("node_type"), str):
        reads.add(f"node_type:{value['node_type']}")
    if term_type == "NodesWhere" and isinstance(value.get("attr_key"), str):
        reads.add(attribute_resource(value["attr_key"], None, variable_roles, scope))
    for child in value.values():
        collect_term_reads(child, reads, variable_roles, scope)


def rule_accesses(rule: dict, attribute_scope: str) -> dict:
    reads: set[str] = set()
    writes: set[str] = set()
    variable_roles: dict[str, set[str]] = {}
    for edge in rule.get("match", []) or []:
        if isinstance(edge, (list, tuple)) and len(edge) >= 3:
            reads.add(f"edge:{edge[1]}")
            if len(edge) >= 3:
                variable_roles.setdefault(str(edge[0]), set()).add(f"edge:{edge[1]}:source")
                variable_roles.setdefault(str(edge[2]), set()).add(f"edge:{edge[1]}:target")
    collect_term_reads(rule.get("where"), reads, variable_roles, attribute_scope)

    unknown_effects = []
    for effect in rule.get("effects", []) or []:
        if not isinstance(effect, (list, tuple)) or not effect:
            unknown_effects.append(repr(effect))
            writes.add("wildcard:unknown_effect")
            continue
        op = effect[0]
        if op in ("add_edge", "del_edge") and len(effect) >= 3:
            writes.add(f"edge:{effect[2]}")
            if len(effect) >= 5:
                collect_term_reads(effect[4], reads, variable_roles, attribute_scope)
        elif op in ("set_attr", "set_attr_if_different") and len(effect) >= 3:
            writes.add(attribute_resource(effect[2], {"type": "Var", "name": effect[1]},
                                          variable_roles, attribute_scope))
            if len(effect) >= 4:
                collect_term_reads(effect[3], reads, variable_roles, attribute_scope)
        elif op in ("add_node", "add_node_if_absent") and len(effect) >= 4:
            writes.add(f"node_type:{effect[2]}")
            attrs = effect[3]
            if isinstance(attrs, dict):
                for key, value in attrs.items():
                    writes.add(attribute_resource(key, None, variable_roles, attribute_scope))
                    collect_term_reads(value, reads, variable_roles, attribute_scope)
        elif op in ("del_node", "replace_value"):
            writes.add("wildcard:graph_structure")
        else:
            unknown_effects.append(str(op))
            writes.add("wildcard:unknown_effect")

    return {
        "name": rule.get("name", "unnamed"),
        "reads": sorted(reads),
        "writes": sorted(writes),
        "variable_roles": {name: sorted(roles) for name, roles in sorted(variable_roles.items())},
        "unknown_effects": unknown_effects,
    }


def intersects(writes: set[str], reads: set[str]) -> bool:
    if any(resource.startswith("wildcard:") for resource in writes | reads):
        return True
    return bool(writes & reads)


def native_access_audit(rules: list[dict]) -> dict:
    """Compare the source extractor with RewriteRule::derive_access readback.

    Returns an explicit unavailable status when the loaded extension predates
    rule_access_sets(); callers must not interpret that as a successful audit.
    """
    try:
        from substrate_rs import Substrate, _native
    except Exception as exc:  # noqa: BLE001 - preserve import failure as evidence
        return {"status": "unavailable", "reason": f"native import failed: {exc}"}

    substrate = Substrate()
    try:
        for rule in rules:
            substrate._inner.add_rule(rule)
        readback = substrate._inner.rule_access_sets()
    except AttributeError as exc:
        return {"status": "unavailable", "reason": f"native diagnostic missing: {exc}"}
    except Exception as exc:  # noqa: BLE001 - make schema incompatibility visible
        return {"status": "error", "reason": f"native rule loading failed: {exc}"}

    rows = []
    for index, (rule_index, name, active, native_reads, native_term_edge_reads,
                native_writes, reads_any, writes_any) in enumerate(readback):
        extracted = rule_accesses(rules[index], "global_key")

        def normalise(resources: list[str]) -> set[str]:
            return {resource.replace("node_type:", "type:", 1)
                    if resource.startswith("node_type:") else resource
                    for resource in resources if not resource.startswith("wildcard:")}

        extracted_reads = normalise(extracted["reads"])
        extracted_writes = normalise(extracted["writes"])
        native_reads_set = set(native_reads)
        native_writes_set = set(native_writes)
        rows.append({
            "rule_index": rule_index,
            "rule_name": name,
            "active": active,
            "native_only_reads": sorted(native_reads_set - extracted_reads),
            "extractor_only_reads": sorted(extracted_reads - native_reads_set),
            "native_only_writes": sorted(native_writes_set - extracted_writes),
            "extractor_only_writes": sorted(extracted_writes - native_writes_set),
            "extractor_read_wildcards": sorted(
                r for r in extracted["reads"] if r.startswith("wildcard:")),
            "extractor_write_wildcards": sorted(
                r for r in extracted["writes"] if r.startswith("wildcard:")),
            "native_reads_any": reads_any,
            "native_writes_any": writes_any,
            "extractor_reads_any": any(r.startswith("wildcard:") for r in extracted["reads"]),
            "extractor_writes_any": any(r.startswith("wildcard:") for r in extracted["writes"]),
            "reads_any_agrees": reads_any == any(r.startswith("wildcard:") for r in extracted["reads"]),
            "writes_any_agrees": writes_any == any(r.startswith("wildcard:") for r in extracted["writes"]),
            "native_reads": sorted(native_reads_set),
            "native_term_edge_reads": sorted(native_term_edge_reads),
            "native_writes": sorted(native_writes_set),
        })
    extension_path = Path(_native.__file__).resolve()
    return {
        "status": "compared",
        "rule_count": len(readback),
        "native_extension_path": str(extension_path),
        "native_extension_sha256": sha(extension_path),
        "rules": rows,
    }


def strongly_connected_components(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    adjacency = [[] for _ in range(n)]
    for u, v in edges:
        adjacency[u].append(v)
    next_index = 0
    indices = [-1] * n
    lowlink = [0] * n
    stack: list[int] = []
    on_stack = [False] * n
    result: list[list[int]] = []

    def visit(v: int) -> None:
        nonlocal next_index
        indices[v] = lowlink[v] = next_index
        next_index += 1
        stack.append(v)
        on_stack[v] = True
        for w in adjacency[v]:
            if indices[w] == -1:
                visit(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack[w]:
                lowlink[v] = min(lowlink[v], indices[w])
        if lowlink[v] == indices[v]:
            component = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
                if w == v:
                    break
            result.append(sorted(component))

    for v in range(n):
        if indices[v] == -1:
            visit(v)
    return result


def main() -> None:
    from domains.graph_treewidth import exact_treewidth, min_fill_upper_bound

    partitioner = structural_helper()
    records = []
    seeds = {}
    for family, relative_path in SEED_PATHS.items():
        seed_path = ROOT / relative_path
        seed = json.loads(seed_path.read_text())
        seeds[family] = {"path": relative_path, "sha256": sha(seed_path),
                         "seed_id": seed.get("id"), "seed_version": seed.get("version")}
        all_rules = seed.get("rules", []) or []
        active_rules = [rule for rule in all_rules if rule.get("active", True)]
        native_audit = native_access_audit(active_rules)
        nodes = list(range(len(active_rules)))
        for attribute_scope in ("global_key", "variable_role"):
            accesses = [rule_accesses(rule, attribute_scope) for rule in active_rules]
            dep_edges = []
            for i, writer in enumerate(accesses):
                write_set = set(writer["writes"])
                for j, reader in enumerate(accesses):
                    if intersects(write_set, set(reader["reads"])):
                        dep_edges.append((i, j))
            t0 = time.perf_counter_ns()
            exact = exact_treewidth(nodes, dep_edges, max_exact_n=10)
            exact_ns = time.perf_counter_ns() - t0 if exact is not None else None
            t0 = time.perf_counter_ns()
            upper = min_fill_upper_bound(nodes, dep_edges)
            min_fill_ns = time.perf_counter_ns() - t0
            partitions = []
            t0 = time.perf_counter_ns()
            canonical = partitioner.recursive_partition(nodes, dep_edges, MAX_LEAF_RULES)
            canonical_ns = time.perf_counter_ns() - t0
            partitions.append({
                "partition_id": "seed_rule_order",
                "seed": None,
                "construction_time_ns": canonical_ns,
                **canonical,
            })
            for partition_seed in range(PARTITIONS_PER_GRAPH):
                order = list(nodes)
                random.Random(72100 + partition_seed).shuffle(order)
                t0 = time.perf_counter_ns()
                shuffled = partitioner.recursive_partition(order, dep_edges, MAX_LEAF_RULES)
                duration = time.perf_counter_ns() - t0
                partitions.append({
                    "partition_id": f"shuffled_{partition_seed}",
                    "seed": 72100 + partition_seed,
                    "construction_time_ns": duration,
                    **shuffled,
                })

            names = [access["name"] for access in accesses]
            named_edges = [{"writer": names[i], "reader": names[j]}
                           for i, j in dep_edges]
            components = strongly_connected_components(len(accesses), dep_edges)
            records.append({
                "workload_family": family,
                "dependency_projection": attribute_scope,
                "source_seed": seeds[family],
                "rules_total": len(all_rules),
                "rules_active": len(active_rules),
        "rules_with_unknown_effects": sum(bool(a["unknown_effects"]) for a in accesses),
                "nodes": len(accesses),
                "directed_dependency_edges": len(dep_edges),
                "undirected_projection_edges": len({(min(u, v), max(u, v)) for u, v in dep_edges if u != v}),
                "self_dependency_count": sum(u == v for u, v in dep_edges),
                "treewidth_exact": exact["treewidth"] if exact is not None else None,
                "treewidth_upper_bound": upper["treewidth"],
                "treewidth_exact_time_ns": exact_ns,
                "min_fill_time_ns": min_fill_ns,
                "scc_sizes": sorted((len(c) for c in components), reverse=True),
                "dependency_edges": named_edges,
                "rule_accesses": accesses,
                "native_access_audit": native_audit,
                "partitions": partitions,
            })

    patch = subprocess.check_output(["git", "diff", "--binary"], cwd=ROOT)
    manifest = {
        "run_state": "pilot",
        "protocol": "seed-derived rule-dependency census v2; benchmark protocol 1.1",
        "command": "PYTHONPATH=. python3 scripts/substrate_rule_dependency_census.py",
        "commit": git("rev-parse", "HEAD"),
        "dirty": git("status", "--porcelain") != "",
        "tracked_patch_sha256": hashlib.sha256(patch).hexdigest(),
        "harness_sha256": sha(Path(__file__)),
        "native_access_source_sha256": {
            "py_binding": sha(ROOT / "runners/dsl/src/py.rs"),
            "rule_access_derivation": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        },
        "protocol_sha256": sha(ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md"),
        "treewidth_source_sha256": sha(ROOT / "domains/graph_treewidth.py"),
        "partitioner_source_sha256": sha(ROOT / "scripts/substrate_structural_census_pilot.py"),
        "runtime_paths": {
            "can_discrete_inference": [
                "tests/test_can_native_reimplementation.py",
                "domains/can_native_orchestration.py",
            ],
            "conversation_deliberation": [
                "substrate/boot_profiles.py",
                "substrate/world_adapter.py",
                "tests/test_conversation_deliberation_phase4a.py",
            ],
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
        },
        "definitions": {
            "nodes": "Active authored rules in each seed manifest.",
            "global_key_projection": "Rule i writes a resource read by rule j; attributes are matched solely by key, a high-recall overapproximation.",
            "variable_role_projection": "Attribute resources are refined by the matched edge-role signature of the referenced variable; this is sensitivity analysis and may miss dependencies when runtime nodes alias across distinct roles.",
            "wildcards": "Node deletion, value replacement, and unknown effect forms conservatively connect to every rule read set.",
            "partition": "Recursive balanced bisection of seed rule order, or a fixed-seed permutation, until each leaf frame has at most four rules.",
            "treewidth": "Undirected simple projection of the directed rule dependency graph; exact when rule count<=10, min-fill upper bound otherwise.",
        },
        "limits": [
            "Seed-level rule specifications, not dynamic runtime graph snapshots.",
            "Native access-set comparison is source-extractor versus loaded RewriteRule::derive_access readback only; it does not capture data-dependent runtime access traces.",
            "Dependency edges are static conservative projections; runtime aliasing, guards, scheduler state, and effect semantics can make them incomplete or overconnected.",
            "No partitioned execution, update cost, or monolithic semantic parity is measured.",
        ],
        "source_seeds": seeds,
        "records": records,
    }
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "records": len(records),
        "summary": {
            f"{r['workload_family']}:{r['dependency_projection']}": {
                "rules": r["nodes"],
                "directed_dependencies": r["directed_dependency_edges"],
                "exact_treewidth": r["treewidth_exact"],
            }
            for r in records
        },
    }, indent=2))


if __name__ == "__main__":
    main()
