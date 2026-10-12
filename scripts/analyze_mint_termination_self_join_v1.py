#!/usr/bin/env python3
"""Independent monotone interpreter and raw-state audit for interaction gate."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/mint_termination_self_join_v1_20260926.json"
OUT = ROOT / "evaluation/reports/mint_termination_self_join_v1_analysis_20260926.json"
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bindings_for(patterns, edges):
    bindings = [{}]
    for src_var, edge_type, tgt_var in patterns:
        next_bindings = []
        for binding in bindings:
            for src, et, tgt, _attrs in sorted(edges, key=lambda e: (e[0], e[1], e[2])):
                if et != edge_type:
                    continue
                trial = dict(binding)
                if src_var in trial and trial[src_var] != src:
                    continue
                if tgt_var in trial and trial[tgt_var] != tgt:
                    continue
                trial[src_var], trial[tgt_var] = src, tgt
                next_bindings.append(trial)
        bindings = next_bindings
    return bindings


def reference_closure(case):
    nodes = [{"id": i, "type": "Seed", "attrs": {"idx": i}}
             for i in range(case["n_initial_nodes"])]
    edges = set()
    for src, et, tgt, attrs in case["initial_edges"]:
        edges.add((int(src[1:]), et, int(tgt[1:]), tuple(sorted(attrs.items()))))
    changed = True
    rounds = 0
    while changed:
        changed = False
        rounds += 1
        if rounds > 100:
            raise RuntimeError("reference closure unexpectedly exceeded 100 rounds")
        for rule in case["rule_specs"]:
            # Snapshot matches at the start of each rule application. Newly
            # inserted facts become visible to later rules/rounds.
            matches = bindings_for(rule["match"], edges)
            for binding in matches:
                b = dict(binding)
                for effect in rule["effects"]:
                    op = effect[0]
                    if op == "add_node_if_absent":
                        _, var, node_type, attrs = effect
                        found = next((node["id"] for node in nodes
                                      if node["type"] == node_type and
                                      all(node["attrs"].get(k, object()) == v for k, v in attrs.items())), None)
                        if found is None:
                            found = len(nodes)
                            nodes.append({"id": found, "type": node_type, "attrs": dict(attrs)})
                            changed = True
                        b[var] = found
                    elif op == "add_edge":
                        _, src, et, tgt, attrs = effect
                        fact = (b[src], et, b[tgt], tuple(sorted(attrs.items())))
                        if fact not in edges:
                            edges.add(fact)
                            changed = True
                    else:
                        raise ValueError(f"reference interpreter does not admit {op}")
    return nodes, edges, rounds


def normalize(nodes, edges):
    id_to_label = {}
    for node in nodes:
        attrs = node["attrs"]
        if node["type"] == "Seed":
            label = f"seed:{attrs['idx']}"
        elif node["type"] == "Witness":
            label = f"witness:{attrs['tag']}"
        else:
            raise ValueError(node["type"])
        id_to_label[node["id"]] = label
    node_set = {(node["type"], json.dumps(node["attrs"], sort_keys=True)) for node in nodes}
    edge_set = {(id_to_label[src], et, id_to_label[tgt], json.dumps(dict(attrs), sort_keys=True))
                for src, et, tgt, attrs in edges}
    return node_set, edge_set


def main() -> int:
    raw = json.loads(RAW.read_text())
    per_case = []
    normalized_by_design = {}
    for case in raw["cases"]:
        static = analyze(case["rule_specs"], case["initial_node_ids"], case["initial_edges"])
        ref_nodes, ref_edges, oracle_rounds = reference_closure(case)
        got_nodes, got_edges = normalize(case["native_graph"]["nodes"], [
            (e["src"], e["type"], e["tgt"], tuple(sorted(e["attrs"].items())))
            for e in case["native_graph"]["edges"]])
        want_nodes, want_edges = normalize(ref_nodes, ref_edges)
        bound = static["progress_steps_upper_bound"]
        expected_tags = ({"L", "R", "T"} if case["family"] == "rich_triangles"
                         else {"L"} if case["family"] == "self_only" else {"R"})
        observed_tags = {node["attrs"].get("tag") for node in case["native_graph"]["nodes"]
                         if node["type"] == "Witness"}
        checks = {
            "analyzer_accepts": static["accepted"],
            "expected_mint_signature_count": static["unique_mint_signatures"] == 3,
            "expected_edge_type_count": static["edge_type_count"] == 5,
            "native_fixed_point": case["native_report"]["status"] == "fixed_point",
            "expected_positive_and_null_activation": observed_tags == expected_tags,
            "native_matches_independent_oracle_nodes": got_nodes == want_nodes,
            "native_matches_independent_oracle_edges": got_edges == want_edges,
            "progress_within_fact_bound": case["native_report"]["progress_steps"] <= bound,
            "no_budget_overshoot": case["native_report"]["budget_overshoot"] == 0,
        }
        design_key = (case["n_initial_nodes"], case["family"])
        normalized_by_design.setdefault(design_key, set()).add(
            (frozenset(got_nodes), frozenset(got_edges)))
        per_case.append({"case_id": case["case_id"], "static_analysis": static,
                         "oracle_rounds": oracle_rounds, "checks": checks,
                         "all_checks_pass": all(checks.values()),
                         "progress_steps": case["native_report"]["progress_steps"],
                         "bound": bound, "passes": case["native_report"]["passes_completed"]})
    order_invariance = all(len(states) == 1 for states in normalized_by_design.values())
    strata = [(n, "rich_triangles") for n in (3,6,9)] + [(n,"self_only") for n in (3,6,9)] + [(n,"reciprocal_pairs") for n in (4,6)]
    expected_ids = {f"n{n}_{family}_{order}_r{r}"
                    for n,family in strata for order in ("LRT", "TRL", "RLT")
                    for r in (1, 2, 3)}
    checks = {"72_expected_cases": {c["case_id"] for c in raw["cases"]} == expected_ids,
              "all_per_case_gates_pass": all(c["all_checks_pass"] for c in per_case),
              "terminal_semantics_order_invariant": order_invariance}
    result = {"analysis_version": 1, "run_id": raw["run_id"], "raw_sha256": sha(RAW),
              "checks": checks, "checks_pass": all(checks.values()),
              "cases": per_case,
              "claim_limit": raw["design"]["claim_limit"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_pass": result["checks_pass"], "checks": checks,
                      "output": str(OUT)}, indent=2))
    return 0 if result["checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
