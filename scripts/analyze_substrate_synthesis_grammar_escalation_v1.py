#!/usr/bin/env python3
"""Independent gate and cost analysis for the grammar escalation panel."""
from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import substrate_synthesis_grammar_escalation_v1 as runner
RAW=ROOT/"evaluation/reports/synthesis_grammar_escalation_v1_20261001_raw.json"
OUT=ROOT/"evaluation/reports/synthesis_grammar_escalation_v1_20261001_analysis.json"


def main() -> None:
    raw=json.loads(RAW.read_text()); rows=raw["workers"]
    workers=[r for r in rows if r.get("kind")=="worker"]
    by_task={task:[r for r in workers if r.get("task")==task] for task in runner.TASKS}
    expected=[(task,rep) for task in runner.TASKS for rep in range(runner.REPETITIONS)]
    random.Random(runner.SEED).shuffle(expected)
    division=by_task["division"]; modulo=by_task["modulo"]
    gates={
        "current_source_native_lock":raw.get("lock")==runner.lock_payload(),
        "all_scheduled_workers_recorded":len(rows)==10 and len(workers)==10,
        "unique_fresh_processes":len({r.get("pid") for r in workers})==10,
        "five_repetitions_per_task":all(len(group)==5 and
            {r.get("repetition") for r in group}==set(range(5)) for group in by_task.values()),
        "exact_seeded_schedule":raw.get("schedule")==[list(x) for x in expected],
        "division_escalation_stops_at_numeric_grammar":all(
            [s["stage"] for s in r["stages"]]==["arithmetic","numeric"] and
            r["stages"][0]["status"]=="no_fit" and r["stages"][0]["halt_reason"]=="max_size" and
            r["stages"][1]["status"]=="accepted" and r["stages"][1]["halt_reason"]=="solved"
            for r in division),
        "division_transfer_exact":all(r.get("selected_term")=="(x / 2)" and
            len(r.get("heldout",[]))==7 and all(x["exact"] for x in r["heldout"])
            for r in division),
        "modulo_exhausts_all_registered_stages":all(
            [s["stage"] for s in r["stages"]]==["arithmetic","numeric","full"] and
            all(s["status"]=="no_fit" and s["halt_reason"]=="max_size" for s in r["stages"])
            and r.get("selected_term") is None and not r.get("heldout") for r in modulo),
        "modulo_primitive_absent_everywhere":all(
            "Mod" not in s["grammar"] for r in modulo for s in r["stages"]),
        "finite_stage_and_total_costs":all(
            len(r["stages"]) in (2,3) and all(s.get("explored",-1)>=0 and
            s.get("wall_s",-1)>=0 and s.get("cpu_s",-1)>=0 for s in r["stages"])
            and r.get("total_wall_s",-1)>=0 and r.get("total_cpu_s",-1)>=0 for r in workers),
    }
    summary={}
    for task,group in by_task.items():
        stage_names=list(dict.fromkeys(s["stage"] for r in group for s in r["stages"]))
        stages={}
        for stage in stage_names:
            subset=[s for r in group for s in r["stages"] if s["stage"]==stage]
            stages[stage]={"workers":len(subset),
                "statuses":[s["status"] for s in subset],
                "median_explored":statistics.median(s["explored"] for s in subset),
                "median_wall_s":statistics.median(s["wall_s"] for s in subset),
                "median_cpu_s":statistics.median(s["cpu_s"] for s in subset)}
        summary[task]={"workers":len(group),"stages":stages,
            "selected_stages":[r["selected_stage"] for r in group],
            "median_total_wall_s":statistics.median(r["total_wall_s"] for r in group),
            "median_total_cpu_s":statistics.median(r["total_cpu_s"] for r in group),
            "heldout_exact":sum(x["exact"] for r in group for x in r["heldout"]),
            "heldout_total":sum(len(r["heldout"]) for r in group)}
    output={"schema":"SubstrateSynthesisGrammarEscalationV1Analysis","gates":gates,
            "passed":sum(gates.values()),"total":len(gates),"summary":summary,
            "worker_count":len(workers),"worker_errors":[r for r in rows if r.get("kind")!="worker"]}
    OUT.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print(json.dumps(output,indent=2,sort_keys=True))


if __name__=="__main__": main()
