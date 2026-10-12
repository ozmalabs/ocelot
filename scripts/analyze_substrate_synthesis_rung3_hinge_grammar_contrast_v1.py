#!/usr/bin/env python3
"""Independent gates and arm summaries for the hinge grammar contrast."""
from __future__ import annotations
import hashlib,json,statistics,sys,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as srs
STEM="synthesis_rung3_hinge_grammar_contrast_v1_20260929"
RAW=ROOT/f"evaluation/reports/{STEM}_raw.jsonl"
LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json"
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
def stat(vals,key,scale=1):
 xs=[x.get(key) for x in vals if isinstance(x.get(key),(int,float))]
 return {"median":statistics.median(xs)/scale if xs else None,
         "min":min(xs)/scale if xs else None,"max":max(xs)/scale if xs else None}
def main():
 lock=json.loads(LOCK.read_text()); rows=[json.loads(x) for x in RAW.read_text().splitlines() if x.strip()]
 heads=[x for x in rows if x.get("kind")=="header"]; feet=[x for x in rows if x.get("kind")=="footer"]
 workers=[x for x in rows if x.get("kind")=="worker"]
 expected={(arm,rep) for arm in lock["inputs"]["arms"] for rep in range(lock["inputs"]["repetitions"])}
 expected_schedule=[(arm,rep) for rep in range(lock["inputs"]["repetitions"]) for arm in lock["inputs"]["arms"]]
 random.Random(lock["inputs"]["schedule_seed"]).shuffle(expected_schedule)
 actual=[(x.get("arm"),x.get("repetition")) for x in workers]
 errors=[x for x in workers if x.get("worker_failed")]
 source_ok={p:sha(ROOT/p)==v for p,v in lock["source_sha256"].items()}
 native=Path(lock["native_extension"]["path"]); native_ok=native.exists() and sha(native)==lock["native_extension"]["sha256"]
 lockok=(len(heads)==1 and len(feet)==1 and heads[0].get("lock")==lock)
 footerok=(len(feet)==1 and feet[0].get("source_native_stable") is True and feet[0].get("post_lock_payload")==lock)
 grouped={arm:[x for x in workers if x.get("arm")==arm] for arm in lock["inputs"]["arms"]}
 summaries={}
 for arm,group in grouped.items():
  accepted=[x for x in group if x.get("status")=="accepted"]
  valid=[x for x in accepted if x.get("program_count")==1 and x.get("ir_root_count")==1 and
         len(x.get("heldout",[]))==6 and all(y.get("exact") is True for y in x.get("heldout",[]))]
  false_accept=[x for x in accepted if x not in valid]
  counts=[(x.get("facts") or {}).get("ps_enum_tested") for x in group]
  summaries[arm]={"n":len(group),"accepted":len(accepted),"gapped":sum(x.get("status")=="gapped" for x in group),
    "reached_rung3":sum((x.get("rungs") or {}).get("enumerate")==1.0 for x in group),
    "terminal":sum(x.get("status") in ("accepted","gapped") for x in group),
    "exact_transfer_workers":len(valid),"false_accept_workers":len(false_accept),
    "holdout_exact_predictions":sum(y.get("exact") is True for x in group for y in x.get("heldout",[])),
    "holdout_total_predictions":sum(len(x.get("heldout",[])) for x in group),
    "candidate_tests":{"median":statistics.median(counts) if counts else None,"min":min(counts) if counts else None,"max":max(counts) if counts else None},
    "pump_wall_ms":stat(group,"pump_wall_ns",1e6),"pump_cpu_ms":stat(group,"pump_cpu_ns",1e6),
    "max_peak_rss_bytes":max((x.get("peak_rss_bytes",0) for x in group),default=None),
    "operator_inventories":sorted({str((x.get("facts") or {}).get("ps_enum_ops")) for x in group}),
    "programs":sorted({p.get("program_json") for x in group for p in x.get("programs",[]) if p.get("program_json")})}
 default=grouped.get("default",[]); oracle=grouped.get("oracle_grammar",[])
 dtests=[(x.get("facts") or {}).get("ps_enum_tested") for x in default if isinstance((x.get("facts") or {}).get("ps_enum_tested"),int)]
 otests=[(x.get("facts") or {}).get("ps_enum_tested") for x in oracle if isinstance((x.get("facts") or {}).get("ps_enum_tested"),int)]
 ratio=(statistics.median(dtests)/statistics.median(otests)) if dtests and otests and statistics.median(otests) else None
 integrity={
  "header_footer_lock_and_schedule_match":lockok and len(feet)==1 and heads[0].get("schedule")==[list(x) for x in expected_schedule],
  "complete_unique_10_worker_arm_matrix":len(workers)==10 and len(actual)==len(set(actual))==10 and set(actual)==expected,
  "no_worker_failures":not errors,
  "current_source_and_native_match_lock":all(source_ok.values()) and native_ok,
  "all_workers_source_native_stable":len([x for x in workers if x.get("source_native_stable") is True])==10,
  "all_workers_reach_rung3_and_terminal":all((x.get("rungs") or {}).get("enumerate")==1.0 and x.get("status") in ("accepted","gapped") for x in workers),
  "every_accepted_program_has_complete_independent_holdout_readback":all(
    x.get("program_count")==1 and x.get("ir_root_count")==1 and len(x.get("heldout",[]))==6
    for x in workers if x.get("status")=="accepted"),
  "footer_lock_unchanged":footerok,
 }
 thresholds={
  "oracle_grammar_exact_transfer_at_least_4_of_5":summaries.get("oracle_grammar",{}).get("exact_transfer_workers",0)>=4,
  "default_grammar_hits_candidate_cap_at_least_4_of_5":sum((x.get("facts") or {}).get("ps_enum_tested")==200000 for x in default)>=4,
  "median_candidate_work_reduction_at_least_3x":ratio is not None and ratio>=3.0,
 }
 report={"run_id":STEM,"integrity_checks":integrity,"capture_integrity_pass":all(integrity.values()),
   "contrast_thresholds":thresholds,"contrast_pass":all(thresholds.values()),
   "all_preregistered_checks_pass":all(integrity.values()) and all(thresholds.values()),
   "passed_integrity_checks":sum(integrity.values()),"total_integrity_checks":len(integrity),
   "arm_summaries":summaries,"default_to_oracle_median_candidate_ratio":ratio,
   "failed_workers":errors,"interpretation":"The oracle grammar arm is a manually supplied search restriction, not learned operator selection. A passing contrast shows sufficiency/cost impact for this fixed balanced hinge task only.",
   "source_file_match":source_ok,"native_matches_lock":native_ok,"lock_sha256":sha(LOCK),"raw_sha256":sha(RAW)}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT.relative_to(ROOT)),"capture_integrity_pass":report["capture_integrity_pass"],
   "contrast_pass":report["contrast_pass"],"integrity_checks":integrity,"contrast_thresholds":thresholds,
   "arm_summaries":summaries,"candidate_ratio":ratio},indent=2))
 if not report["capture_integrity_pass"]: raise SystemExit(1)
if __name__=="__main__": main()
