#!/usr/bin/env python3
"""Independent integrity and semantic analysis for Stage A disjoint-pair capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_stage_a_disjoint_pair_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_stage_a_disjoint_pair_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/stage_a_disjoint_pair_v1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=p["runs"];expected=(1,2,6,16,32)
 checks={
  "capture_schema":p.get("schema_version")==1 and len(runs)==3,
  "lock_matches_capture":p.get("locked_inputs")==lock.get("locked_inputs") and p.get("lock_sha256")==sha(LOCK),
  "fresh_processes":len({r["pid"] for r in runs})==3,
  "worker_source_stability":all(r["started_inputs"]==p["locked_inputs"]==r["finished_inputs"] for r in runs),
  "replicate_schedules_complete":all(tuple(c["size"] for c in r["cells"])==expected for r in runs),
  "control_and_candidate_oracles":all(c[a]["oracle_gate"] for r in runs for c in r["cells"] for a in ("control","candidate")),
  "whole_graph_and_progress_parity":all(c["exact_graph_parity"] and c["progress_parity"] for r in runs for c in r["cells"]),
  "stage_a_compare_and_guard":all(c["candidate"]["stage_a_compare_stats"]["compared_drains"]==1 and c["candidate"]["stage_a_compare_stats"]["diverged_drains"]==0 and c["candidate"]["stage_a_compare_stats"]["unsound_drains"]==0 and c["candidate"]["stage_a_stats"]["conflict_fallbacks"]==0 for r in runs for c in r["cells"]),
  "single_pass_terminal":all(c[a]["terminal_progress"]==0 for r in runs for c in r["cells"] for a in ("control","candidate")),
 }
 summary=[]
 for n in expected:
  cs=[c for r in runs for c in r["cells"] if c["size"]==n]
  summary.append({"size":n,"replicates":len(cs),"compared_drains":[c["candidate"]["stage_a_compare_stats"]["compared_drains"] for c in cs],"diverged_drains":sum(c["candidate"]["stage_a_compare_stats"]["diverged_drains"] for c in cs),"unsound_drains":sum(c["candidate"]["stage_a_compare_stats"]["unsound_drains"] for c in cs),"conflict_fallbacks":sum(c["candidate"]["stage_a_stats"]["conflict_fallbacks"] for c in cs),"progress_values":[c["candidate"]["progress"] for c in cs]})
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"passed":all(checks.values()),"cell_count":sum(len(r["cells"]) for r in runs),"summary_by_binding_count":summary,"claim_boundary":p["claim_boundary"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
 if not out["passed"]:raise SystemExit("independent analysis failed")
if __name__=="__main__":main()
