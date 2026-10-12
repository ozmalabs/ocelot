#!/usr/bin/env python3
"""Independent integrity and descriptive analysis for route contrast v1."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/self_report_route_contrast_v1_1_20260927.json"
OUT=ROOT/"evaluation/reports/self_report_route_contrast_v1_1_analysis_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/self_report_route_contrast_v1_1_lock_20260927.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_1_AMENDMENT_20260927.md"
RUNNER=ROOT/"scripts/probe_self_report_route_contrast_v1_1.py"
RUNTIME_SLABS=ROOT/"data/slabs"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());rows=raw["runs"];groups=defaultdict(list)
 for r in rows:groups[r["stimulus_id"]].append(r)
 locked=json.loads(LOCK.read_text())
 runtime={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(RUNTIME_SLABS.glob("*")) if p.is_file()}
 checks={"worker_count_30":len(rows)==30,"unique_processes_30":len({r["pid"] for r in rows})==30,
  "driver_source_lock_stable":raw["driver_lock"]["source_lock"]==raw["post_run_source_lock"]==locked["source_lock"],
  "protocol_runner_match_lock":raw["driver_lock"]["protocol_sha256"]==locked["protocol_sha256"]==sha(PROTOCOL) and raw["driver_lock"]["runner_sha256"]==locked["runner_sha256"]==sha(RUNNER),
  "runtime_reference_assets_match_lock":raw["driver_lock"]["source_lock"]["runtime_slab_sha256"]==runtime and raw["post_run_source_lock"]["runtime_slab_sha256"]==runtime,
  "three_replicates_each":set(groups)==set("ABCDEFGHIJ") and all(len(v)==3 for v in groups.values()),
  "all_worker_source_locks_match":all(r["worker_start_lock"]==locked["source_lock"]==r["worker_end_lock"] for r in rows),
  "records_complete":all(r.get("comprehension") is not None and r.get("reply") is not None and r.get("semantic_graph_sha256") for r in rows)}
 summary={}
 for sid,rs in sorted(groups.items()):
  sigs={(r["route"],r["instruction_outcome"],json.dumps(r["comprehension"],sort_keys=True),r["reply"],r["semantic_graph_sha256"]) for r in rs}
  summary[sid]={"text":rs[0]["text"],"replicates":len(rs),"stable_within_stimulus":len(sigs)==1,
   "routes":sorted({str(r["route"]) for r in rs}),"comprehension_kinds":sorted({str(r["comprehension"]["kind"]) for r in rs}),
   "dispatch_paths":sorted({str((r["comprehension"]["dispatch"] or {}).get("path")) for r in rs}),
   "instruction_outcomes":sorted({str(r["instruction_outcome"]) for r in rs}),"replies":sorted({r["reply"] for r in rs}),
   "coinage_tokens":sorted({str((r["comprehension"]["dispatch"] or {}).get("coinage")) for r in rs if (r["comprehension"]["dispatch"] or {}).get("path")=="wordplay"}),
   "loaded_seed_counts":sorted({r["loaded_seed_count"] for r in rs}),"failed_seed_profiles":len({json.dumps(r["failed_seeds"],sort_keys=True) for r in rs}),
   "graph_digests":len({r["semantic_graph_sha256"] for r in rs})}
 checks["within_stimulus_behavior_repeats"]=all(v["stable_within_stimulus"] for v in summary.values())
 payload={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),"stimuli":summary,"claim_boundary":"Descriptive routing outcomes for ten authored utterances, each on three fresh full boots of one locked source snapshot. This is not a natural-task prevalence estimate or evidence of tractability."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"all_checks_pass":payload["all_checks_pass"],"stimuli":summary},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("independent contrast-panel checks failed")
if __name__=="__main__":main()
