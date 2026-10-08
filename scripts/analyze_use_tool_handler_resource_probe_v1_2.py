#!/usr/bin/env python3
"""Independent checks for the v1.2 offline handler resource probe."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_use_tool_handler_resource_probe_v1_2_20260928.json"
OUT = ROOT / "evaluation/reports/substrate_use_tool_handler_resource_probe_v1_2_analysis_20260928.json"


def main() -> None:
    d = json.loads(RAW.read_text())
    workers = d["workers"]
    expected = set(d["lock"]["cases"])
    gates = {
        "three_workers": len(workers) == 3,
        "all_workers_completed": all("handlers" in w for w in workers),
        "all_handlers_present": all(set(w.get("handlers", {})) == expected for w in workers),
        "source_and_resource_stable": d["source_resource_stable"] and d["lock"]["source_resource_snapshot"] == d["snapshot_after"],
    }
    repeatable = True
    across_workers = True
    handler_summary = {}
    for name in sorted(expected):
        observations = []
        for worker in workers:
            calls = worker["handlers"][name]["calls"]
            observations.append(calls)
            repeatable &= calls[0] == calls[1]
        across_workers &= observations[0] == observations[1] == observations[2]
        status = observations[0][0]["status"]
        handler_summary[name] = {
            "status": status,
            "value": observations[0][0].get("value"),
            "repeatable_within_worker": all(c[0] == c[1] for c in observations),
            "same_across_workers": observations[0] == observations[1] == observations[2],
        }
    gates["repeatable_within_worker"] = repeatable
    gates["identical_across_workers"] = across_workers
    attempts = [w.get("acquisition_attempts", []) for w in workers]
    gates["acquisition_attempts_consistent"] = attempts[0] == attempts[1] == attempts[2]
    statuses = {s: sum(v["status"] == s for v in handler_summary.values()) for s in ("ok", "error")}
    resources = d["lock"]["source_resource_snapshot"]
    result = {
        "analysis": "UseTool handler resource probe v1.2",
        "all_gates_pass": all(gates.values()), "gates": gates,
        "handler_count": len(handler_summary), "handler_status_counts": statuses,
        "handlers": handler_summary,
        "acquisition_attempts_per_worker": attempts,
        "nltk_resource_presence": {k: v for k, v in resources.items() if k.startswith("nltk:")},
        "limitations": [
            "Fixed representative inputs measure repeatability, not lexical accuracy or full function purity.",
            "Same-process call two is warm relative to call one; independent workers start with empty Python caches.",
            "Blocked acquisition attempts are observed behavior; no successful download or changed-resource invalidation is measured.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": result["all_gates_pass"], "gates": gates,
                      "handler_status_counts": statuses,
                      "attempts_per_worker": [len(x) for x in attempts],
                      "analysis": str(OUT.relative_to(ROOT))}, indent=2))
    if not result["all_gates_pass"]:
        raise SystemExit("one or more independent analysis gates failed")


if __name__ == "__main__":
    main()
