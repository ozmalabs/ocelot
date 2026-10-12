#!/usr/bin/env python3
"""Independent analysis of the production Gamma operator selection panel."""
from __future__ import annotations
import json,random,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
import substrate_production_gamma_operator_selection_v1 as runner
RAW=ROOT/"evaluation/reports/production_gamma_operator_selection_v1_20261001_raw.json"
OUT=ROOT/"evaluation/reports/production_gamma_operator_selection_v1_20261001_analysis.json"

def main():
 raw=json.loads(RAW.read_text());rows=raw["workers"];workers=[r for r in rows if r.get("kind")=="worker"]
 by={task:[r for r in workers if r.get("task")==task] for task in runner.TASKS}
 expected=[(task,r) for task in runner.TASKS for r in range(runner.REPETITIONS)]
 random.Random(runner.SEED).shuffle(expected)
 source=(ROOT/"runners/dsl/src/synth_enumerate.rs").read_text()
 op_table=source.split("const OP_TABLE:",1)[1].split("];",1)[0]
 modulo=by["modulo"];factorial=by["factorial"]
 gates={
  "current_source_native_lock":raw.get("lock")==runner.payload(),
  "all_workers_present":len(rows)==10 and len(workers)==10,
  "unique_fresh_pids":len({r.get("pid") for r in workers})==10,
  "five_workers_per_task":all(len(g)==5 and {r.get("repetition") for r in g}==set(range(5)) for g in by.values()),
  "locked_randomized_schedule":raw.get("schedule")==[list(x) for x in expected],
  "no_explicit_operator_list":all(r.get("message_explicit_ops") is None for r in workers),
  "graph_gamma_supplies_operator_list":all(r.get("gamma_used") is True and bool(r.get("gamma_ops")) for r in workers),
  "mod_is_in_native_inventory":'("Mod",' in op_table and '("Factorial",' not in op_table,
  "gamma_selects_mod_and_program_uses_it":all(r.get("status")=="accepted" and "Mod" in r.get("gamma_ops",[])
   and r.get("ir_root_count")==1 and '"type": "Mod"' in json.dumps(r.get("ir")) for r in modulo),
  "modulo_heldouts_exact":all(len(r.get("heldout",[]))==8 and all(x["exact"] for x in r["heldout"]) for r in modulo),
  "factorial_gap_at_native_candidate_limit":all(r.get("status")=="gapped" and
   r.get("gap_reason")=="enumerate_failed" and r.get("enumerate_outcome")=="failed" and
   r.get("candidate_count")==200000 and r.get("program_count")==0 and
   "Factorial" not in r.get("gamma_ops",[]) for r in factorial),
  "finite_resource_capture":all(r.get("pump_wall_ns",-1)>=0 and r.get("pump_cpu_ns",-1)>=0 and
   r.get("peak_rss_bytes",-1)>0 and r.get("stable") is True for r in workers),
 }
 summary={}
 for task,group in by.items():
  summary[task]={"workers":len(group),"statuses":[r.get("status") for r in group],
   "gap_reasons":[r.get("gap_reason") for r in group],"candidate_counts":[r.get("candidate_count") for r in group],
   "candidate_median":statistics.median(r["candidate_count"] for r in group),
   "pump_wall_median_ms":statistics.median(r["pump_wall_ns"] for r in group)/1e6,
   "pump_cpu_median_ms":statistics.median(r["pump_cpu_ns"] for r in group)/1e6,
   "peak_rss_median_mib":statistics.median(r["peak_rss_bytes"] for r in group)/(1024*1024),
   "gamma_ops":[r.get("gamma_ops") for r in group],"programs":[r.get("program_json") for r in group],
   "heldout_exact":sum(x["exact"] for r in group for x in r.get("heldout",[])),
   "heldout_total":sum(len(r.get("heldout",[])) for r in group)}
 out={"schema":"SubstrateProductionGammaOperatorSelectionV1Analysis","gates":gates,
  "passed":sum(gates.values()),"total":len(gates),"summary":summary,"worker_count":len(workers),
  "worker_errors":[r for r in rows if r.get("kind")!="worker"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":main()
