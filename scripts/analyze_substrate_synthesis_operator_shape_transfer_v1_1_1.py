#!/usr/bin/env python3
"""Independent integrity and transfer gates for operator-shape panel."""
from __future__ import annotations
import hashlib,json,statistics,sys,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as srs
STEM="synthesis_operator_shape_transfer_v1_1_1_20260929"
RAW=ROOT/f"evaluation/reports/{STEM}_raw.jsonl"; LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json"
OUT=ROOT/f"evaluation/reports/{STEM}_analysis.json"
SOURCES=("domains/prog_synthesis.py","domains/engine_provenance.py","domains/code_writing.py",
 "domains/prog_retrieval.py","seeds/program_synthesis.json","seeds/program_synthesis_grounding.json",
 "seeds/program_synthesis_opgrammar.json","seeds/code_write_request_cues.json","seeds/exact_families.json",
 "runners/dsl/src/synth_enumerate.rs","runners/dsl/src/prog_eval.rs","runners/dsl/src/term.rs",
 "runners/dsl/src/py.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/substrate.rs",
 "runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()
def median(vals): return statistics.median(vals) if vals else None
def main():
 lock=json.loads(LOCK.read_text()); data=[json.loads(x) for x in RAW.read_text().splitlines() if x.strip()]
 heads=[x for x in data if x.get("kind")=="header"]; feet=[x for x in data if x.get("kind")=="footer"]
 workers=[x for x in data if x.get("kind")=="worker"]
 inp=lock["inputs"]; expected={(t,w,r) for t in inp["tasks"] for w in inp["wordings"] for r in range(inp["repetitions"])}
 actual=[(x.get("task"),x.get("wording"),x.get("repetition")) for x in workers]
 sched=[(t,w,r) for r in range(inp["repetitions"]) for t in inp["task_order"] for w in inp["wording_order"]]
 random.Random(inp["schedule_seed"]).shuffle(sched)
 lockok=len(heads)==1 and len(feet)==1 and heads[0].get("lock")==lock and heads[0].get("schedule")==[list(x) for x in sched]
 source_matches={p:sha(ROOT/p)==v for p,v in lock["source_sha256"].items()}
 npath=Path(lock["native_extension"]["path"]); native_match=npath.exists() and sha(npath)==lock["native_extension"]["sha256"]
 worker_fail=[x for x in workers if x.get("worker_failed")]
 cases={}
 for t in inp["tasks"]:
  for w in inp["wordings"]:
   group=[x for x in workers if x.get("task")==t and x.get("wording")==w]
   accepted=[x for x in group if x.get("status")=="accepted"]
   exact=[x for x in accepted if x.get("program_count")==1 and x.get("ir_root_count")==1 and
          len(x.get("heldout",[]))==6 and all(y.get("exact") is True for y in x.get("heldout",[]))]
   bad=[x for x in accepted if x not in exact]
   tests=[(x.get("facts") or {}).get("ps_enum_tested") for x in group if isinstance((x.get("facts") or {}).get("ps_enum_tested"),int)]
   walls=[x.get("pump_wall_ns") for x in group if isinstance(x.get("pump_wall_ns"),int)]
   cpus=[x.get("pump_cpu_ns") for x in group if isinstance(x.get("pump_cpu_ns"),int)]
   cases[f"{t}:{w}"]={"n":len(group),"accepted":len(accepted),"gapped":sum(x.get("status")=="gapped" for x in group),
    "exact_transfer_workers":len(exact),"false_accept_workers":len(bad),
    "holdout_exact_predictions":sum(y.get("exact") is True for x in group for y in x.get("heldout",[])),
    "holdout_prediction_count":sum(len(x.get("heldout",[])) for x in group),
    "candidate_tests":{"median":median(tests),"min":min(tests) if tests else None,"max":max(tests) if tests else None},
    "pump_wall_ms":{"median":median(walls)/1e6 if walls else None,"min":min(walls)/1e6 if walls else None,"max":max(walls)/1e6 if walls else None},
    "pump_cpu_ms":{"median":median(cpus)/1e6 if cpus else None},
    "selected_shapes":sorted({str((x.get("facts") or {}).get("ps_enum_operator_shape")) for x in group}),
    "selected_operator_lists":sorted({str((x.get("facts") or {}).get("ps_enum_ops")) for x in group}),
    "message_operator_selections":sorted({str((x.get("message_facts") or {}).get("ps_operator_shape_selected")) for x in group})}
 integrity={
  "locked_schedule_header_footer":lockok,
  "complete_unique_20_cell_matrix":len(workers)==20 and len(actual)==len(set(actual))==20 and set(actual)==expected,
  "no_worker_failures":not worker_fail,
  "current_source_and_native_match_lock":all(source_matches.values()) and native_match,
  "all_workers_source_stable":len([x for x in workers if x.get("source_native_stable") is True])==20,
  "all_workers_reach_rung3_terminal":all((x.get("rungs") or {}).get("enumerate")==1.0 and x.get("status") in ("accepted","gapped") for x in workers),
  "accepted_programs_have_six_independent_holdout_rows":all(x.get("program_count")==1 and x.get("ir_root_count")==1 and len(x.get("heldout",[]))==6 for x in workers if x.get("status")=="accepted"),
  "footer_lock_unchanged":len(feet)==1 and feet[0].get("source_native_stable") is True and feet[0].get("post_lock_payload")==lock,
 }
 behavioral={}; ratios={}
 for t in inp["tasks"]:
  trig=cases[f"{t}:trigger"]; abl=cases[f"{t}:lexical_ablation"]
  trig_workers=[x for x in workers if x.get("task")==t and x.get("wording")=="trigger"]
  abl_workers=[x for x in workers if x.get("task")==t and x.get("wording")=="lexical_ablation"]
  selection_ok=all((x.get("facts") or {}).get("ps_enum_operator_shape")=="thresholded_greater_branch" and
                   (x.get("facts") or {}).get("ps_enum_ops")==["Times","Gt","IfThenElse"] and
                   (x.get("message_facts") or {}).get("ps_enum_ops")==["Times","Gt","IfThenElse"] and
                   (x.get("message_facts") or {}).get("ps_operator_shape_selected")==1.0
                   for x in trig_workers)
  ablation_ok=all(not (x.get("facts") or {}).get("ps_enum_operator_shape") and
                  not ((x.get("facts") or {}).get("ps_enum_ops")) for x in abl_workers)
  tr_tests=(trig.get("candidate_tests") or {}).get("median"); ab_tests=(abl.get("candidate_tests") or {}).get("median")
  ratio=ab_tests/tr_tests if tr_tests else None; ratios[t]=ratio
  behavioral[f"{t}_trigger_selects_registered_shape_without_harness_ops"]=selection_ok
  behavioral[f"{t}_lexical_ablation_selects_no_shape"]=ablation_ok
  behavioral[f"{t}_trigger_exact_transfer_at_least_4_of_5"]=trig["exact_transfer_workers"]>=4
  behavioral[f"{t}_ablation_hits_candidate_cap_at_least_4_of_5"]=sum((x.get("facts") or {}).get("ps_enum_tested")==inp["candidate_cap"] for x in abl_workers)>=4
  behavioral[f"{t}_median_candidate_reduction_at_least_1_5x"]=ratio is not None and ratio>=1.5
 report={"run_id":STEM,"integrity_checks":integrity,"capture_integrity_pass":all(integrity.values()),
  "behavioral_gates":behavioral,"behavioral_pass":all(behavioral.values()),
  "all_preregistered_gates_pass":all(integrity.values()) and all(behavioral.values()),
  "passed_integrity_checks":sum(integrity.values()),"total_integrity_checks":len(integrity),
  "case_results":cases,"ablation_to_trigger_candidate_ratios":ratios,"worker_failures":worker_fail,
  "source_file_matches":source_matches,"native_matches_lock":native_match,
  "interpretation":"Tests this registered thresholded-greater selector across two fixed scalar piecewise-scaling tasks and a lexical ablation. It does not establish operator selection beyond this shape family or general grammar induction.",
  "lock_sha256":sha(LOCK),"raw_sha256":sha(RAW)}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT.relative_to(ROOT)),"capture_integrity_pass":report["capture_integrity_pass"],
  "behavioral_pass":report["behavioral_pass"],"integrity_checks":integrity,"behavioral_gates":behavioral,
  "case_results":cases,"candidate_ratios":ratios},indent=2))
 if not report["capture_integrity_pass"]: raise SystemExit(1)
if __name__=="__main__":main()
