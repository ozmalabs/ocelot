#!/usr/bin/env python3
"""Probe ownership-aware cleanup for reflected Term child-edge trees."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
import substrate_rs as srs

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_TERM_SUBGRAPH_OWNERSHIP_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/term_subgraph_ownership_lock_20260925.json"
TERM = {"type": "Cat", "items": [
    {"type": "Lit", "value": "left"},
    {"type": "Reverse", "seq": {"type": "Var", "name": "x"}},
]}
CASES = ("unshared", "shared_subtree", "shared_leaf")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(sub):
    graph = sub.graph_to_dict()
    nodes = {int(n["id"]): n for n in graph["nodes"]}
    edges = graph["edges"]
    node_ids = {int(n.value): n for n in sub.nodes()}
    return graph, nodes, edges, node_ids


def owned_postorder(nodes, edges, root_id):
    children = {}
    for e in edges:
        if str(e["type"]).startswith("child."):
            children.setdefault(int(e["src"]), []).append(int(e["tgt"]))
    visited, order = set(), []

    def visit(nid):
        if nid in visited:
            return
        visited.add(nid)
        for child in children.get(nid, []):
            visit(child)
        order.append(nid)

    visit(root_id)
    if any(nodes[nid]["type"] != "Term." + nodes[nid]["type"].split("Term.", 1)[-1]
           for nid in visited):
        raise RuntimeError("non-Term node appeared inside child-edge ownership tree")
    return order, children


def remove_owned_term_tree(sub, root):
    root_id = int(root.value)
    _, nodes, edges, node_ids = snapshot(sub)
    order, children = owned_postorder(nodes, edges, root_id)
    owned = set(order)
    external_seeds = {int(e["tgt"]) for e in edges
                      if int(e["tgt"]) in owned and int(e["src"]) not in owned}
    protected, stack = set(), list(external_seeds)
    while stack:
        nid = stack.pop()
        if nid in protected:
            continue
        protected.add(nid)
        stack.extend(children.get(nid, []))
    removed = []
    for nid in order:
        if nid not in protected and nid in node_ids:
            if sub.remove_node(node_ids[nid]):
                removed.append(nid)
    return {"root_id": root_id, "owned_ids": sorted(owned),
            "external_reference_seeds": sorted(external_seeds),
            "protected_ids": sorted(protected), "removed_ids": removed}


def add_owner(sub, target):
    owner = sub.add_node("TermOwner", {"case": "external_owner"})
    sub.add_edge_unchecked(owner, "holds_term", target)
    return owner


def native_root_remove_control(case):
    sub = srs.Substrate()
    root = sub._inner.add_term_subgraph(TERM)
    graph, nodes, _, ids = snapshot(sub)
    held = None
    owner = None
    if case == "shared_subtree":
        held = next(ids[nid] for nid, n in nodes.items() if n["type"] == "Term.Reverse")
    elif case == "shared_leaf":
        held = next(ids[nid] for nid, n in nodes.items() if n["type"] == "Term.Var")
    if held is not None:
        owner = add_owner(sub, held)
    before = sub.node_count()
    sub.remove_node(root)
    _, after_nodes, after_edges, _ = snapshot(sub)
    held_id = int(held.value) if held is not None else None
    return {"before_nodes": before, "after_nodes": sub.node_count(),
            "term_nodes_remaining": sorted(nid for nid, n in after_nodes.items()
                                            if n["type"].startswith("Term.")),
            "held_child_survives": held_id is None or held_id in after_nodes,
            "owner_edge_survives": owner is None or any(
                int(e["src"]) == int(owner.value) and e["type"] == "holds_term"
                and int(e["tgt"]) == held_id for e in after_edges)}


def one_case(case):
    sub = srs.Substrate()
    baseline = sub.node_count()
    root = sub._inner.add_term_subgraph(TERM)
    before, nodes, edges, ids = snapshot(sub)
    root_id = int(root.value)
    term_ids = {nid for nid, n in nodes.items() if n["type"].startswith("Term.")}
    if case == "unshared":
        held = None
        owner = None
    elif case == "shared_subtree":
        held = next(ids[nid] for nid, n in nodes.items() if n["type"] == "Term.Reverse")
        owner = add_owner(sub, held)
    else:
        held = next(ids[nid] for nid, n in nodes.items() if n["type"] == "Term.Var")
        owner = add_owner(sub, held)
    held_id = int(held.value) if held is not None else None
    held_json = sub._inner.term_subgraph_json(held) if held is not None else None
    before_cleanup_count = sub.node_count()
    result = remove_owned_term_tree(sub, root)
    _, after_nodes, after_edges, after_ids = snapshot(sub)
    owner_edge_survives = (owner is None or any(int(e["src"]) == int(owner.value)
                                                and e["type"] == "holds_term"
                                                and int(e["tgt"]) == held_id
                                                for e in after_edges))
    held_survives = held_id is None or held_id in after_nodes
    held_roundtrip = (held_json is None or
                      sub._inner.term_subgraph_json(after_ids[held_id]) == held_json)
    unowned_term_ids = sorted(nid for nid in term_ids - {root_id}
                              if nid not in result["protected_ids"] and nid in after_nodes)
    retained_types = {nid: after_nodes[nid]["type"] for nid in result["protected_ids"]
                      if nid in after_nodes}
    post_cleanup_count = sub.node_count()
    after_owner_removal = None
    if owner is not None:
        sub.remove_node(owner)
        later = remove_owned_term_tree(sub, held)
        after_owner_removal = {"cleanup": later, "final_node_count": sub.node_count(),
                               "returns_to_baseline": sub.node_count() == baseline}
    return {
        "case": case, "baseline_nodes": baseline,
        "materialized_term_node_ids": sorted(term_ids),
        "materialized_nodes": len(term_ids), "materialized_root_id": root_id,
        "native_remove_node_control": native_root_remove_control(case),
        "collector": result, "post_cleanup_node_count": post_cleanup_count,
        "unowned_term_nodes_left": unowned_term_ids,
        "held_id": held_id, "held_subgraph_type": None if held is None else after_nodes.get(held_id, {}).get("type"),
        "held_subgraph_survives": held_survives,
        "held_subgraph_roundtrip_stable": held_roundtrip,
        "owner_edge_survives": owner_edge_survives,
        "retained_types": retained_types,
        "after_owner_removal": after_owner_removal,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: substrate_term_subgraph_ownership.py OUTPUT.json")
    output = Path(sys.argv[1])
    lock = json.loads(LOCK.read_text())
    expected = {"preregistration_sha256": sha(PREREG),
                "runner_sha256": sha(Path(__file__).resolve()),
                "native_sha256": sha(Path(srs._native.__file__).resolve())}
    if any(lock.get(k) != v for k, v in expected.items()):
        raise SystemExit("Term subgraph ownership lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    started = time.perf_counter_ns()
    results = [one_case(case) for case in CASES]
    passed = all(not r["unowned_term_nodes_left"] and r["held_subgraph_survives"] and
                 r["held_subgraph_roundtrip_stable"] and r["owner_edge_survives"] and
                 (r["after_owner_removal"] is None or r["after_owner_removal"]["returns_to_baseline"])
                 for r in results)
    payload = {"schema_version": 1, "run_id": "term-subgraph-ownership-20260925-v1",
               "term": TERM, "cases": results, "all_cases_pass": passed,
               "wall_ns": time.perf_counter_ns() - started,
               "provenance": {"preregistration_sha256": sha(PREREG),
                              "lock_sha256": sha(LOCK), "runner_sha256": sha(Path(__file__).resolve()),
                              "native_sha256": sha(Path(srs._native.__file__).resolve()),
                              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                              "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())},
               "claim_boundary": "host-side prototype only; not a production cleanup API"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_cases_pass": passed, "output": str(output)}))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
