#!/usr/bin/env python3
"""Capture native closure on repeated-variable and self-join rule schemas."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/mint_termination_self_join_v1_20260926.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_SELF_JOIN_PREREG_20260926.md"
RUNNER = Path(__file__).resolve()
from substrate_rs import _native  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


RULES = {
    "L": {"name": "self_loop_witness", "match": [["x", "loop", "x"]], "effects": [
        ["add_node_if_absent", "l", "Witness", {"tag": "L"}],
        ["add_edge", "x", "has_loop", "l", {}]]},
    "R": {"name": "reciprocal_witness", "match": [["x", "rel", "y"], ["y", "rel", "x"]], "effects": [
        ["add_node_if_absent", "r", "Witness", {"tag": "R"}],
        ["add_edge", "x", "has_recip", "r", {}]]},
    "T": {"name": "triangle_witness", "match": [["x", "rel", "y"], ["y", "rel", "z"], ["z", "rel", "x"]], "effects": [
        ["add_node_if_absent", "t", "Witness", {"tag": "T"}],
        ["add_edge", "x", "has_tri", "t", {}]]},
}


def graph_facts(n: int, family: str):
    facts = []
    if family in ("rich_triangles", "self_only"):
        facts.extend((i, "loop", i) for i in range(n))
    if family == "rich_triangles":
        for base in range(0, n, 3):
            a, b, c = base, base + 1, base + 2
            facts.extend((s, "rel", t) for s, t in
                         ((a,b),(b,c),(c,a),(a,c),(c,b),(b,a)))
    elif family == "reciprocal_pairs":
        for base in range(0, n, 2):
            facts.extend(((base, "rel", base+1), (base+1, "rel", base)))
    elif family not in ("self_only",):
        raise ValueError(family)
    return facts


def one_case(n: int, family: str, order: str, replicate: int):
    facts = graph_facts(n, family)
    rule_specs = [RULES[key] for key in order]
    sub = _native.Substrate()
    ids = [sub.add_node("Seed", {"idx": i}) for i in range(n)]
    for src, edge_type, tgt in facts:
        sub.add_edge_unchecked(ids[src], edge_type, ids[tgt])
    for rule in rule_specs:
        sub.add_rule(rule)
    report = sub.run_rules_report(200000, False)
    return {
        "case_id": f"n{n}_{family}_{order}_r{replicate}",
        "n_initial_nodes": n, "family": family, "rule_order": order,
        "replicate": replicate,
        "initial_node_ids": [f"n{i}" for i in range(n)],
        "initial_edges": [[f"n{s}", et, f"n{t}", {}] for s, et, t in facts],
        "rule_specs": rule_specs,
        "native_report": report, "native_graph": sub.graph_to_dict(),
    }


def main():
    design = [(n, "rich_triangles") for n in (3,6,9)] + [(n,"self_only") for n in (3,6,9)] + [(n,"reciprocal_pairs") for n in (4,6)]
    cases = [one_case(n, family, order, rep) for n, family in design
             for order in ("LRT", "TRL", "RLT") for rep in (1,2,3)]
    native_path = Path(_native.__file__).resolve()
    out = {
        "schema_version": 1,
        "run_id": "mint-termination-self-join-v1-20260926",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "engine": provenance_line(), "python": sys.version, "platform": platform.platform(),
        "provenance": {"runner_sha256": sha(RUNNER), "prereg_sha256": sha(PREREG),
                       "native_sha256": sha(native_path), "native_path": str(native_path)},
        "design": {"strata": [{"N": n, "family": family} for n,family in design],
                   "rule_orders": ["LRT", "TRL", "RLT"], "replicates": 3,
                   "cases": len(cases), "budget": 200000,
                   "rule_edge_types": ["loop", "rel", "has_loop", "has_recip", "has_tri"],
                   "claim_limit": "three fixed positive rules with self-join patterns; no nonmonotone effects"},
        "cases": cases,
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": out["run_id"], "cases": len(cases),
                      "output": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
