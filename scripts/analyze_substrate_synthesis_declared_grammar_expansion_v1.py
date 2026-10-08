#!/usr/bin/env python3
"""Independent integrity and outcome analysis for grammar expansion v1."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import substrate_synthesis_declared_grammar_expansion_v1 as runner

RAW = ROOT / "evaluation/reports/synthesis_declared_grammar_expansion_v1_20261001_raw.json"
OUT = ROOT / "evaluation/reports/synthesis_declared_grammar_expansion_v1_20261001_analysis.json"


def main() -> None:
    raw = json.loads(RAW.read_text())
    rows = raw["workers"]
    workers = [row for row in rows if row.get("kind") == "worker"]
    by_condition = {condition: [row for row in workers if row["condition"] == condition]
                    for condition in runner.GRAMMARS}
    expected_schedule = [(condition, rep) for condition in runner.GRAMMARS
                         for rep in range(runner.REPETITIONS)]
    __import__("random").Random(runner.SEED).shuffle(expected_schedule)
    gates = {
        "current_source_lock": raw.get("lock") == runner.lock_payload(),
        "complete_schedule": len(rows) == 10 and len(raw.get("schedule", [])) == 10,
        "all_workers_completed": len(workers) == 10,
        "unique_fresh_processes": len({row.get("pid") for row in workers}) == 10,
        "five_repetitions_per_condition": all(len(group) == 5 and
            {row["repetition"] for row in group} == set(range(5))
            for group in by_condition.values()),
        "locked_randomized_schedule": raw.get("schedule") == [list(item) for item in expected_schedule],
        "operator_absent_completes_without_fit": all(row["status"] == "no_fit" and
            row["halt_reason"] == "max_size" and not row["heldout"]
            for row in by_condition["operator_absent"]),
        "expanded_grammar_transfers_exactly": all(row["status"] == "accepted" and
            row["halt_reason"] == "solved" and row["heldout"] and
            all(item["exact"] for item in row["heldout"])
            for row in by_condition["expanded_with_div"]),
        "expanded_solution_uses_division": all("/" in row["term"]
            for row in by_condition["expanded_with_div"] if row.get("term")),
        "finite_cost_capture": all(row.get("explored", -1) >= 0 and
            row.get("wall_s", -1) >= 0 and row.get("cpu_s", -1) >= 0
            for row in workers),
    }
    summary = {}
    for condition, group in by_condition.items():
        summary[condition] = {
            "workers": len(group), "statuses": [row["status"] for row in group],
            "halt_reasons": [row["halt_reason"] for row in group],
            "terms": [row["term"] for row in group],
            "explored_median": statistics.median(row["explored"] for row in group),
            "wall_median_s": statistics.median(row["wall_s"] for row in group),
            "cpu_median_s": statistics.median(row["cpu_s"] for row in group),
            "heldout_exact": sum(item["exact"] for row in group for item in row["heldout"]),
            "heldout_total": sum(len(row["heldout"]) for row in group),
        }
    analysis = {"schema":"SubstrateSynthesisDeclaredGrammarExpansionV1Analysis",
                "gates":gates, "passed":sum(gates.values()), "total":len(gates),
                "summary":summary, "worker_count":len(workers),
                "worker_errors":[row for row in rows if row.get("kind") != "worker"]}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps(analysis, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
