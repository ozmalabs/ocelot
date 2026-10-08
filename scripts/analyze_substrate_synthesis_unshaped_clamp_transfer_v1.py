#!/usr/bin/env python3
"""Independent checks for unshaped clamp synthesis transfer."""
from __future__ import annotations
import hashlib,json,random,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as srs
STEM="synthesis_unshaped_clamp_transfer_v1_20260929"
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
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def med(v):return statistics.median(v) if v else None
def main():
 lock=json.loads(LOCK.read_text()); data=[json.loads(x) for x in RAW.read_text().splitlines() if x.strip()]
 heads=[x for x in data if x.get("kind")=="header"]; feet=[x for x in data if x.get("kind")=="footer"]
 workers=[x for x in data if x.get("kind")=="worker"]; inp=lock["inputs"]
 expected={(t,r) for t in inp["task_order"] for r in range(inp["repetitions"])}
 actual=[(x.get("task"),x.get("repetition")) for x in workers]
 schedule=[(t,r) for r in range(inp["repetitions"]) for t in inp["task_order"]]; random.Random(inp["schedule_seed"]).shuffle(schedule)
 source={p:sha(ROOT/p)==h for p,h in lock["source_sha256"].items()}
 native=Path(lock["native_extension"]["path"]); native_ok=native.exists() and sha(native)==lock["native_extension"]["sha256"]
 summaries={}
 for task in inp["task_order"]:
  group=[x for x in workers if x.get("task")==task]; accepted=[x for x in group if x.get("status")=="accepted"]
  exact=[x for x in accepted if x.get("program_count")==1 and x.get("ir_root_count")==1 and len(x.get("heldout",[]))==6 and all(y.get("exact") is True for y in x.get("heldout",[]))]
  bad=[x for x in accepted if x not in exact]
  tests=[(x.get("facts") or {}).get("ps_enum_tested") for x in group if isinstance((x.get("facts") or {}).get("ps_enum_tested"),int)]
  wall=[x.get("pump_wall_ns") for x in group if isinstance(x.get("pump_wall_ns"),int)]; cpu=[x.get("pump_cpu_ns") for x in group if isinstance(x.get("pump_cpu_ns"),int)]
  summaries[task]={"n":len(group),"accepted":len(accepted),"gapped":sum(x.get("status")=="gapped" for x in group),
   "exact_transfer_workers":len(exact),"false_accept_workers":len(bad),
   "exact_holdout_points":sum(y.get("exact") is True for x in group for y in x.get("heldout",[])),
   "holdout_points":sum(len(x.get("heldout",[])) for x in group),
   "candidate_tests":{"median":med(tests),"min":min(tests) if tests else None,"max":max(tests) if tests else None},
   "pump_wall_ms":{"median":med(wall)/1e6 if wall else None,"min":min(wall)/1e6 if wall else None,"max":max(wall)/1e6 if wall else None},
   "pump_cpu_ms":{"median":med(cpu)/1e6 if cpu else None},
   "max_peak_rss_bytes":max((x.get("peak_rss_bytes",0) for x in group),default=None),
   "selected_shapes":sorted({str((x.get("facts") or {}).get("ps_enum_operator_shape")) for x in group}),
   "explicit_operator_lists":sorted({str((x.get("facts") or {}).get("ps_enum_ops")) for x in group}),
   "programs":sorted({p.get("program_json") for x in group for p in x.get("programs",[]) if p.get("program_json")})}
 integrity={
  "locked_schedule_header_footer":len(heads)==1 and len(feet)==1 and heads[0].get("lock")==lock and heads[0].get("schedule")==[list(x) for x in schedule],
  "complete_unique_10_worker_matrix":len(workers)==10 and len(actual)==len(set(actual))==10 and set(actual)==expected,
  "no_worker_failures":not [x for x in workers if x.get("worker_failed")],
  "current_sources_and_native_match_lock":all(source.values()) and native_ok,
  "all_workers_source_stable":len([x for x in workers if x.get("source_native_stable") is True])==10,
  "all_workers_reach_rung3_and_terminal":all((x.get("rungs") or {}).get("enumerate")==1.0 and x.get("status") in ("accepted","gapped") for x in workers),
  "no_operator_shape_or_explicit_ops_selected":all(not (x.get("facts") or {}).get("ps_enum_operator_shape") and not (x.get("facts") or {}).get("ps_enum_ops") for x in workers),
  "accepted_programs_have_six_holdout_rows":all(x.get("program_count")==1 and x.get("ir_root_count")==1 and len(x.get("heldout",[]))==6 for x in workers if x.get("status")=="accepted"),
  "footer_lock_unchanged":len(feet)==1 and feet[0].get("source_native_stable") is True and feet[0].get("post_lock_payload")==lock,
 }
 transfer={f"{task}_exact_transfer_at_least_4_of_5":summary["exact_transfer_workers"]>=4 for task,summary in summaries.items()}
 report={"run_id":STEM,"integrity_checks":integrity,"capture_integrity_pass":all(integrity.values()),
  "transfer_gates":transfer,"transfer_pass":all(transfer.values()),"all_preregistered_gates_pass":all(integrity.values()) and all(transfer.values()),
  "passed_integrity_checks":sum(integrity.values()),"total_integrity_checks":len(integrity),"case_results":summaries,
  "source_file_matches":source,"native_matches_lock":native_ok,
  "interpretation":"Tests default-grammar acquisition and holdout transfer on two fixed scalar clamp instances without an operator-shape selection. It does not establish broad task-family generalization or scaling.",
  "lock_sha256":sha(LOCK),"raw_sha256":sha(RAW)}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT.relative_to(ROOT)),"capture_integrity_pass":report["capture_integrity_pass"],
  "transfer_pass":report["transfer_pass"],"integrity_checks":integrity,"transfer_gates":transfer,"case_results":summaries},indent=2))
 if not report["capture_integrity_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
