#!/usr/bin/env python3
"""Independent checks for mixed-topology node deletion replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_mixed_node_delete_semantics_v1_1_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_mixed_node_delete_semantics_v1_1_analysis_20260928.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_after(row: dict) -> dict:
    doomed = row["ids"]["doomed"]
    graph = row["before_graph"]
    return {**graph,
            "nodes": [n for n in graph["nodes"] if n["id"] != doomed],
            "edges": [e for e in graph["edges"] if e["src"] != doomed and e["tgt"] != doomed]}


def main() -> int:
    raw = json.loads(RAW.read_text())
    rows = raw["runs"]
    checks = {
        "runner_gates_pass": raw.get("all_checks_pass") is True and all(raw["checks"].values()),
        "three_unique_workers": len(rows) == 3 and len({r["pid"] for r in rows}) == 3,
        "post_state_independently_derived": all(r["after_graph"] == expected_after(r) for r in rows),
        "all_incident_edges_absent_unrelated_edge_present": all(r["lookups"] == [False] * 6 + [True] for r in rows),
        "counts_exact": all(r["removed"] is True and r["node_count"] == 3 and r["edge_count"] == 1 for r in rows),
        "hook_contract_exact": all(r["node_events"] == [[r["ids"]["doomed"], "Doomed"]]
                                    and r["edge_events"] == [] for r in rows),
        "mixed_incident_edge_families": all(len({e[1] for e in r["specs"] if e[0] == r["ids"]["doomed"] or e[2] == r["ids"]["doomed"]}) == 5
                                             and any(e[0] == e[2] == r["ids"]["doomed"] for e in r["specs"])
                                             for r in rows),
        "successful_run_manifest": raw["run_manifest"].get("exit_status") == 0,
    }
    result = {"analysis_id": "substrate-mixed-node-delete-semantics-v1-independent-analysis",
              "raw_sha256": digest(RAW), "checks": checks, "checks_passed": sum(checks.values()),
              "checks_total": len(checks), "all_checks_pass": all(checks.values()),
              "claim_boundary": raw["claim_boundary"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks_passed": result["checks_passed"], "checks_total": result["checks_total"],
                      "all_checks_pass": result["all_checks_pass"], "output": str(OUT.relative_to(ROOT))}, indent=2))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
