#!/usr/bin/env python3
"""Exercise native ownership-aware cleanup and fail-closed validation."""
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

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_TERM_SUBGRAPH_NATIVE_CLEANUP_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/term_subgraph_native_cleanup_lock_20260925.json"
TERM = {"type": "Cat", "items": [
    {"type": "Lit", "value": "left"},
    {"type": "Reverse", "seq": {"type": "Var", "name": "x"}},
]}
CASES = ("unshared", "shared_subtree", "shared_leaf", "shared_root",
         "cyclic_child", "non_term_child", "non_term_root", "missing_root")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_fingerprint(sub):
    body = json.dumps(sub.graph_to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


def nodes_by_type(sub):
    graph = sub.graph_to_dict()
    result = {}
    for node in graph["nodes"]:
        result.setdefault(node["type"], []).append(srs.NodeID(int(node["id"])))
    return result


def mk_term(sub):
    root = sub._inner.add_term_subgraph(TERM)
    by_type = nodes_by_type(sub)
    term_nodes = {t: ids for t, ids in by_type.items() if t.startswith("Term.")}
    all_ids = {int(n.value) for ids in term_nodes.values() for n in ids}
    return root, term_nodes, all_ids


def add_owner(sub, target):
    owner = sub.add_node("TermOwner", {"keeps": int(target.value)})
    sub.add_edge_unchecked(owner, "holds_term", target)
    return owner


def call_cleanup(sub, root):
    return sub._inner.remove_term_subgraph(root)


def run_valid_case(case):
    sub = srs.Substrate()
    base_count = sub.node_count()
    root, term_nodes, all_term_ids = mk_term(sub)
    held = None
    owner = None
    if case == "shared_subtree":
        held = term_nodes["Term.Reverse"][0]
        owner = add_owner(sub, held)
    elif case == "shared_leaf":
        held = term_nodes["Term.Var"][0]
        owner = add_owner(sub, held)
    elif case == "shared_root":
        held = root
        owner = add_owner(sub, held)
    held_json = sub._inner.term_subgraph_json(held) if held is not None else None
    before = sub.node_count()
    result = call_cleanup(sub, root)
    removed = {int(x) for x in result["removed_node_ids"]}
    protected = {int(x) for x in result["protected_node_ids"]}
    after_types = nodes_by_type(sub)
    live_term_ids = {int(n.value) for ty, ids in after_types.items()
                     if ty.startswith("Term.") for n in ids}
    live_owner_edges = []
    if owner is not None:
        live_owner_edges = [int(n.value) for n in sub.neighbours(owner, "holds_term")]
    preserved = held is None or int(held.value) in live_term_ids
    held_stable = held_json is None or sub._inner.term_subgraph_json(held) == held_json
    if owner is None:
        cleanup_after_owner = None
        returns_to_baseline = sub.node_count() == base_count
    else:
        sub.remove_node(owner)
        second = call_cleanup(sub, held)
        cleanup_after_owner = second
        returns_to_baseline = sub.node_count() == base_count
    expected_removed = (all_term_ids if case == "unshared" else
                        ({int(root.value), int(term_nodes["Term.Lit"][0].value)} if case == "shared_subtree" else
                         {int(root.value), int(term_nodes["Term.Lit"][0].value), int(term_nodes["Term.Reverse"][0].value)} if case == "shared_leaf" else
                         set()))
    expected_protected = (set() if case == "unshared" else
                          {int(term_nodes["Term.Reverse"][0].value), int(term_nodes["Term.Var"][0].value)} if case == "shared_subtree" else
                          {int(term_nodes["Term.Var"][0].value)} if case == "shared_leaf" else
                          all_term_ids)
    passed = (removed == expected_removed and protected == expected_protected and
              preserved and held_stable and returns_to_baseline and
              (owner is None or live_owner_edges == [int(held.value)]))
    return {"case": case, "passed": passed, "base_node_count": base_count,
            "pre_cleanup_node_count": before, "term_node_ids": sorted(all_term_ids),
            "removed_ids": sorted(removed), "protected_ids": sorted(protected),
            "post_cleanup_term_node_ids": sorted(live_term_ids),
            "held_subgraph_survives": preserved, "held_subgraph_roundtrip_stable": held_stable,
            "owner_edge_targets_after_cleanup": live_owner_edges,
            "cleanup_after_owner_removal": cleanup_after_owner,
            "final_node_count": sub.node_count(), "returns_to_baseline": returns_to_baseline}


def run_rejection_case(case):
    sub = srs.Substrate()
    error = None
    if case == "non_term_root":
        root = sub.add_node("Plain", {})
        expected = "term_subgraph_root_not_term"
    elif case == "missing_root":
        root = srs.NodeID(2_000_000_000)
        expected = "term_subgraph_root_missing"
    else:
        root, term_nodes, _ = mk_term(sub)
        if case == "cyclic_child":
            leaf = term_nodes["Term.Var"][0]
            sub.add_edge_unchecked(leaf, "child.cycle", root)
            expected = "term_subgraph_child_cycle"
        else:
            invalid = sub.add_node("NotTerm", {})
            sub.add_edge_unchecked(root, "child.invalid", invalid)
            expected = "term_subgraph_child_not_term"
    before = graph_fingerprint(sub)
    try:
        call_cleanup(sub, root)
    except ValueError as exc:
        error = str(exc)
    after = graph_fingerprint(sub)
    return {"case": case, "passed": error == expected and before == after,
            "expected_error": expected, "observed_error": error,
            "graph_unchanged": before == after, "node_count": sub.node_count()}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: substrate_term_subgraph_native_cleanup.py OUTPUT.json")
    output = Path(sys.argv[1])
    lock = json.loads(LOCK.read_text())
    native = Path(srs._native.__file__).resolve()
    expected = {"preregistration_sha256": sha(PREREG),
                "runner_sha256": sha(Path(__file__).resolve()),
                "native_sha256": sha(native)}
    if any(lock.get(k) != v for k, v in expected.items()):
        raise SystemExit("native cleanup probe lock mismatch")
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")
    start = time.perf_counter_ns()
    results = [run_valid_case(case) for case in CASES[:4]]
    results.extend(run_rejection_case(case) for case in CASES[4:])
    passed = all(r["passed"] for r in results)
    payload = {"schema_version": 1, "run_id": "term-subgraph-native-cleanup-20260925-v1",
               "term": TERM, "cases": results, "all_cases_pass": passed,
               "wall_ns": time.perf_counter_ns() - start,
               "environment": {"python": sys.version, "platform": platform.platform(),
                               "native_path": str(native), "native_sha256": sha(native)},
               "provenance": {**expected, "lock_sha256": sha(LOCK),
                              "build_record_sha256": sha(native.with_name("_native.build.json")),
                              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()},
               "claim_boundary": "local native API probe; no concurrency/arena compaction proof"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_cases_pass": passed, "output": str(output)}))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
