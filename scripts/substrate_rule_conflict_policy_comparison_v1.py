#!/usr/bin/env python3
"""Compare order metadata, conflict proposal nodes, and a narrow reject prototype."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_RULE_CONFLICT_POLICY_COMPARISON_V1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_rule_conflict_policy_comparison_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/rule_conflict_policy_comparison_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/rule_conflict_policy_comparison_v1_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_rule_conflict_policy_comparison_v1.py",
    "scripts/analyze_rule_conflict_policy_comparison_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_RULE_CONFLICT_POLICY_COMPARISON_V1_PREREG_20260928.md",
)
ORDERS = ("A_then_B", "B_then_A")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
            "native_extension_path": str(ext), "native_extension_sha256": sha(ext),
            "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json")}


def rule_specs(policy: str) -> dict:
    from substrate_rs import Lit, Term
    where = Term("Eq", a=Term("UseTool", tool="always_true", args=[Lit("same")]), b=Lit("yes")).to_dict()
    if policy == "metadata_order":
        return {
            "A": {"name": "conflict_A", "order": 10, "match": [["x", "trigger", "y"]], "where": where,
                  "effects": [["set_attr_if_different", "y", "accepted", 1]]},
            "B": {"name": "conflict_B", "order": 20, "match": [["x", "trigger", "y"]], "where": where,
                  "effects": [["set_attr_if_different", "y", "accepted", 2]]},
        }
    return {
        "A": {"name": "proposal_A", "match": [["x", "trigger", "y"]], "where": where,
              "effects": [["add_node_if_absent", "pa", "ConflictProposal", {"rule": "A", "value": 1}],
                          ["add_edge", "y", "proposes", "pa", {}]]},
        "B": {"name": "proposal_B", "match": [["x", "trigger", "y"]], "where": where,
              "effects": [["add_node_if_absent", "pb", "ConflictProposal", {"rule": "B", "value": 2}],
                          ["add_edge", "y", "proposes", "pb", {}]]},
    }


def exact_conflict_reject(rules: dict) -> dict:
    a, b = rules["A"], rules["B"]
    same_trigger = a["match"] == b["match"] and a["where"] == b["where"]
    writes = {}
    for label, rule in (("A", a), ("B", b)):
        for effect in rule["effects"]:
            if effect[0] in ("set_attr", "set_attr_if_different"):
                key = (effect[1], effect[2])
                writes.setdefault(key, []).append((label, effect[3]))
    conflicts = [{"variable": k[0], "attribute": k[1], "proposals": vals}
                 for k, vals in writes.items() if len(vals) > 1 and len({json.dumps(v, sort_keys=True) for _, v in vals}) > 1]
    reject = same_trigger and bool(conflicts)
    return {"decision": "reject_before_install" if reject else "admit",
            "same_match_and_where": same_trigger, "conflicting_writes": conflicts,
            "scope": "exact structural equality only; no graph pattern unification or predicate equivalence"}


def cell(policy: str, order: str) -> dict:
    from substrate_rs import Substrate, _native
    _native.clear_tool_handlers(); calls = []

    def handler(arg):
        calls.append(str(arg)); return "yes"

    _native.register_tool_handler("always_true", handler)
    rules = rule_specs(policy)
    sub = Substrate(); inner = sub._inner
    x = inner.add_node("ConflictProbe", {}); y = inner.add_node("ConflictProbe", {})
    inner.add_edge_unchecked(x, "trigger", y, {})
    sequence = ("A", "B") if order == "A_then_B" else ("B", "A")
    admission = exact_conflict_reject(rule_specs("metadata_order"))
    if policy == "metadata_order" and admission["decision"] != "reject_before_install":
        raise RuntimeError("exact conflict admission prototype failed to reject fixture")
    for label in sequence:
        inner.add_rule(rules[label])
    report = inner.run_rules_report(12, True)
    graph = inner.graph_to_dict()
    attrs = {int(n["id"]): n.get("attrs", {}) for n in graph.get("nodes", [])}
    proposals = sorted((n.get("attrs", {}).get("rule"), n.get("attrs", {}).get("value"))
                       for n in graph.get("nodes", []) if n["type"] == "ConflictProposal")
    proposal_edges = sum(e["type"] == "proposes" and int(e["src"]) == y.value for e in graph.get("edges", []))
    _native.clear_tool_handlers()
    return {"policy": policy, "order": order, "rule_sequence": sequence,
            "termination": dict(report), "callback_count": len(calls),
            "accepted": attrs.get(y.value, {}).get("accepted"),
            "proposal_nodes": proposals, "proposal_edge_count": proposal_edges,
            "exact_reject_prototype": admission, "graph": graph}


def worker(worker_id: int) -> dict:
    started = lock_inputs()
    if json.loads(LOCK.read_text())["locked_inputs"] != started:
        raise RuntimeError("source/native lock mismatch")
    cells = [cell(policy, order) for policy in ("metadata_order", "proposal_nodes") for order in ORDERS]
    return {"worker_id": worker_id, "pid": os.getpid(), "platform": platform.platform(),
            "python": sys.version, "started_inputs": started, "cells": cells}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--worker", type=int); ap.add_argument("--write-lock", action="store_true")
    args = ap.parse_args()
    if args.write_lock:
        if LOCK.exists(): raise SystemExit(f"refusing to overwrite {LOCK}")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"lock_id": "rule_conflict_policy_comparison_v1_20260928",
                                    "locked_inputs": lock_inputs(), "workers": 3,
                                    "policies": ["metadata_order", "proposal_nodes"], "orders": ORDERS}, indent=2, sort_keys=True)+"\n")
        print(str(LOCK.relative_to(ROOT))); return
    if args.worker is not None:
        print(json.dumps(worker(args.worker), sort_keys=True)); return
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    lock = json.loads(LOCK.read_text())
    if lock_inputs() != lock["locked_inputs"]: raise SystemExit("source/native lock mismatch")
    runs=[]
    for wid in range(1,4):
        argv=[sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)]
        cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True)
        if cp.returncode: raise SystemExit(f"worker {wid} failed: {cp.stderr[-2000:]}")
        runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
    raw={"run_id":"rule_conflict_policy_comparison_v1_20260928","locked_inputs":lock["locked_inputs"],
         "protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs,
         "claim_boundary":"Narrow exact-conflict admission prototype, existing global order metadata, and graph proposal-node representation on one deterministic conflict."}
    RAW.parent.mkdir(parents=True,exist_ok=True)
    with RAW.open("x",encoding="utf-8") as f:f.write(json.dumps(raw,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))


if __name__=="__main__":main()
