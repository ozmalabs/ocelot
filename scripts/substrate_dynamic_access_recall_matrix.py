#!/usr/bin/env python3
"""Behavioral read/write dependency recall probe for the native rule engine.

For controlled rule pairs, mutate edge, edge-weight, node-attribute, and
node-type resources after an existing reader binding is established. Compare
the reader's refreshed value with a direct final-graph oracle, inspect native
static access-set overlap, and require a terminal no-work probe.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_dynamic_access_recall_matrix_20260925.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def var(name):
    return {"type": "Var", "name": name}


def term(kind, **fields):
    return {"type": kind, **fields}


def graph_oracle(graph, kind, source_id, target_id=None):
    causal = [e for e in graph["edges"] if e["type"] == "causal"]
    if kind == "out_count":
        return sum(e["src"] == source_id for e in causal)
    if kind == "in_count":
        return sum(e["tgt"] == target_id for e in causal)
    if kind == "reachable_count":
        adjacency = {}
        for e in causal:
            adjacency.setdefault(e["src"], set()).add(e["tgt"])
        reached, stack = set(), list(adjacency.get(source_id, set()))
        while stack:
            node = stack.pop()
            if node not in reached:
                reached.add(node)
                stack.extend(adjacency.get(node, set()) - reached)
        return len(reached)
    if kind == "all_out_count":
        return sum(e["src"] == source_id for e in graph["edges"])
    if kind == "mapped_neighbor_count":
        roots = {n["id"] for n in graph["nodes"] if n["type"] == "WakeupRoot"}
        return len({e["tgt"] for e in causal if e["src"] in roots})
    if kind == "weight_sum":
        return sum(e["attrs"].get("weight", 0) for e in causal if e["src"] == source_id)
    if kind == "attr":
        return next(n["attrs"].get("watched", 0) for n in graph["nodes"] if n["id"] == source_id)
    if kind == "spawned_count":
        return sum(n["type"] == "Spawned" for n in graph["nodes"])
    raise ValueError(kind)


def resource_overlap(reader_row, writer_row):
    reads = set(reader_row[3]) | set(reader_row[4])
    writes = set(writer_row[5])
    return bool(reader_row[6] or writer_row[7] or reads & writes), sorted(reads), sorted(writes)


def make_case(case, mutation, read, oracle_kind, initial_causal=False, initial_weight=0,
              reader_where=None):
    from substrate_rs import Substrate, _native

    s = Substrate()
    inner = s._inner
    source = inner.add_node("WakeupRoot", {"watched": 0})
    target = inner.add_node("WakeupTarget", {})
    inner.add_edge_unchecked(source, "trigger", target, {})
    if initial_causal:
        inner.add_edge_unchecked(source, "causal", target, {"weight": initial_weight})
    reader_rule = {
        "name": f"access_recall_{case}_{mutation}_reader",
        "match": [["x", "trigger", "y"]],
        "effects": [["set_attr", "y", "observed_value", {"__term__": read}]],
    }
    if reader_where is not None:
        reader_rule["where"] = reader_where
    reader_idx = inner.add_rule(reader_rule)
    if mutation == "insert":
        effects = [["add_edge", "x", "causal", "y", {"weight": 1}]]
    elif mutation == "delete":
        effects = [["del_edge", "x", "causal", "y"]]
    elif mutation == "replace_weight":
        effects = [["del_edge", "x", "causal", "y"],
                   ["add_edge", "x", "causal", "y", {"weight": 2}]]
    elif mutation == "set_node_attr":
        effects = [["set_attr", "x", "watched", 7]]
    elif mutation == "add_node":
        effects = [["add_node", "born", "Spawned", {}]]
    else:
        raise ValueError(mutation)
    writer_idx = inner.add_rule({
        "name": f"access_recall_{case}_{mutation}_writer",
        "match": [["x", "trigger", "y"]], "effects": effects,
    })
    try:
        access = inner.rule_access_sets()
        reader_row = next(row for row in access if row[0] == reader_idx)
        writer_row = next(row for row in access if row[0] == writer_idx)
        reader_reads, reader_term_reads = list(reader_row[3]), list(reader_row[4])
        reader_writes, reader_any = list(reader_row[5]), bool(reader_row[6])
        writer_writes, writer_any = list(writer_row[5]), bool(writer_row[7])
        access_source = "native_rule_access_sets"
        native_access_available = True
        access_rows = [list(row) for row in access]
    except AttributeError:
        # Some locally installed extension binaries predate this source API.
        # Use the checked-in JSON rule resource extractor, and mark that fact.
        helper_path = ROOT / "scripts/substrate_rule_dependency_census.py"
        spec = importlib.util.spec_from_file_location("rule_dependency_extractor", helper_path)
        helper = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(helper)
        exported = inner.export_rules()
        source_reader = next(rule for rule in exported if rule["name"] == f"access_recall_{case}_{mutation}_reader")
        source_writer = next(rule for rule in exported if rule["name"] == f"access_recall_{case}_{mutation}_writer")
        reader_projection = helper.rule_accesses(source_reader, "global_key")
        writer_projection = helper.rule_accesses(source_writer, "global_key")
        def normalize(resources):
            return [r.replace("node_type:", "type:", 1) if r.startswith("node_type:") else r
                    for r in resources]
        reader_reads = normalize(reader_projection["reads"])
        reader_term_reads = []
        reader_writes = normalize(reader_projection["writes"])
        reader_any = any(r.startswith("wildcard:") for r in reader_reads)
        writer_writes = normalize(writer_projection["writes"])
        writer_any = any(r.startswith("wildcard:") for r in writer_writes)
        reader_row = [reader_idx, source_reader["name"], True, reader_reads,
                      reader_term_reads, reader_writes, reader_any, False]
        writer_row = [writer_idx, source_writer["name"], True, writer_projection["reads"],
                      [], writer_writes, False, writer_any]
        access_source = "python_seed_resource_extractor_over_exported_rules"
        native_access_available = False
        access_rows = []
    before_graph = inner.graph_to_dict()
    progress = inner.run_rules(100)
    value = inner.node(target)["attrs"].get("observed_value")
    final_graph = inner.graph_to_dict()
    terminal = inner.run_rules(1)
    expected = graph_oracle(final_graph, oracle_kind, source.value, target.value)
    # Compare only changed-resource write sets with the reader's resources.
    predicts, reads, writes = resource_overlap(reader_row, writer_row)
    return {
        "case": case, "mutation": mutation, "oracle_kind": oracle_kind,
        "reader_has_where": reader_where is not None,
        "reader_rule": reader_row[1], "writer_rule": writer_row[1],
        "access_set_source": access_source,
        "native_rule_access_sets_available": native_access_available,
        "reader_reads": reader_reads, "reader_term_edge_reads": reader_term_reads,
        "reader_reads_any": reader_any, "writer_writes": writer_writes,
        "writer_writes_any": writer_any,
        "static_dependency_predicted": predicts,
        "normalized_reads": reads, "normalized_writes": writes,
        "progress_count": progress, "terminal_probe_progress": terminal,
        "observed_value": value, "final_graph_oracle": expected,
        "reader_matches_oracle": value == expected,
        "settled": terminal == 0,
        "graph_before": {"nodes": len(before_graph["nodes"]), "edges": len(before_graph["edges"])},
        "graph_after": {"nodes": len(final_graph["nodes"]), "edges": len(final_graph["edges"])},
        "actual_mutation_visible": before_graph != final_graph,
        "native_rule_access_sets": access_rows,
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
    }


def main():
    from substrate_rs import _native

    x, y = var("x"), var("y")
    typed_edges = term("Edges", node=x, edge_type="causal")
    reads = [
        ("edges_typed", term("Count", source=typed_edges), "out_count"),
        ("neighbours_typed", term("Count", source=term("Neighbours", node=x, edge_type="causal")), "out_count"),
        ("in_neighbours_typed", term("Count", source=term("InNeighbours", node=y, edge_type="causal")), "in_count"),
        ("reachable_typed", term("Count", source=term("ReachableFrom", node=x, edge_type="causal")), "reachable_count"),
        ("map_neighbours_typed", term("Count", source=term("MapNeighbours",
            source=term("NodesOfType", node_type="WakeupRoot"), edge_type="causal")), "mapped_neighbor_count"),
        ("edges_any_type", term("Count", source=term("Edges", node=x, edge_type=None)), "all_out_count"),
        ("edge_attr_sum", term("Sum", source=typed_edges, var_name="edge",
            value=term("EdgeAttr", edge=var("edge"), key="weight")), "weight_sum"),
    ]
    cases = []
    for name, query, oracle in reads:
        for mutation in ("insert", "delete"):
            deletion = mutation == "delete"
            cases.append(make_case(name, mutation, query, oracle,
                                   initial_causal=deletion or name == "edge_attr_sum" and mutation == "insert",
                                   initial_weight=1 if deletion else 0))
    name, query, oracle = reads[-1]
    cases.append(make_case(name, "replace_weight", query, oracle,
                           initial_causal=True, initial_weight=1))
    cases.append(make_case("node_attr_read", "set_node_attr",
                           term("Attr", node=x, key="watched"), "attr"))
    cases.append(make_case("node_attr_predicate_read", "set_node_attr",
                           term("Attr", node=x, key="watched"), "attr",
                           reader_where=term("Gt", a=term("Attr", node=x, key="watched"),
                                             b=term("Lit", value=0))))
    cases.append(make_case("node_type_read", "add_node",
                           term("Count", source=term("NodesOfType", node_type="Spawned")),
                           "spawned_count"))

    ext_path = Path(_native.__file__).resolve()
    effect_only_attr = next(r for r in cases if r["case"] == "node_attr_read")
    predicate_attr = next(r for r in cases if r["case"] == "node_attr_predicate_read")
    eligible = [r for r in cases if r["case"] != "node_attr_read"]
    checks = {
        "all_supported_reader_values_match_final_graph_oracle": all(
            r["reader_matches_oracle"] for r in eligible),
        "effect_only_attribute_read_limit_reproduced": (
            not effect_only_attr["reader_matches_oracle"] and effect_only_attr["settled"]),
        "attribute_predicate_read_refreshes": predicate_attr["reader_matches_oracle"],
        "all_cases_reach_terminal_no_work": all(r["settled"] for r in cases),
        "all_mutations_change_the_graph": all(r["actual_mutation_visible"] for r in cases),
        "all_writer_reader_pairs_have_source_dependency_overlap": all(r["static_dependency_predicted"] for r in cases),
        "native_static_access_diagnostic_available": all(r["native_rule_access_sets_available"] for r in cases),
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-dynamic-access-recall-matrix-20260925",
        "scope": "controlled two-rule runtime perturbations for typed traversal, any-edge, edge-attribute, node-attribute, and node-type read/write dependencies",
        "claim_boundary": "Behavioral invalidation/replay coverage for these hand-built cases only. Effect-only Attr reads are a known scheduler exception: the current policy re-wakes Attr readers with a where-clause but not a rule whose only Attr read supplies an effect value. This is not a complete dynamic read trace, general rule-family proof, task-level frame locality result, or parallel execution test.",
        "configuration": {"cases": len(cases), "mutations": ["insert", "delete", "replace_weight", "set_node_attr", "add_node"], "progress_cap": 100},
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "native_extension_path": str(ext_path), "native_extension_sha256": sha(ext_path),
            "source_sha256": {"harness": sha(Path(__file__).resolve()),
                "rewrite": sha(ROOT / "runners/dsl/src/rewrite.rs"),
                "substrate": sha(ROOT / "runners/dsl/src/substrate.rs"),
                "term": sha(ROOT / "runners/dsl/src/term.rs"),
                "binding": sha(ROOT / "runners/dsl/src/py.rs"),
                "native_build_manifest": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json")},
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        },
        "checks": checks, "cases": cases,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(cases), "checks": checks, "output": str(OUT)}, indent=2))
    if not all(value for key, value in checks.items()
               if key != "native_static_access_diagnostic_available"):
        raise SystemExit("dynamic access recall probe failed")


if __name__ == "__main__":
    main()
