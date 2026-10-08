#!/usr/bin/env python3
"""Independent integrity and semantic analysis for Stage A overlap fallback."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_stage_a_overlap_fallback_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_stage_a_overlap_fallback_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/stage_a_overlap_fallback_v1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=p["runs"];sizes=(1,2,6,16,32)
 cells=[c for r in runs for c in r["cells"]]
 checks={
  "capture_schema":p.get("schema_version")==1 and len(runs)==3,
  "lock_matches_capture":p.get("locked_inputs")==lock.get("locked_inputs") and p.get("lock_sha256")==sha(LOCK),
  "fresh_processes":len({r["pid"] for r in runs})==3,
  "worker_source_stability":all(r["started_inputs"]==p["locked_inputs"]==r["finished_inputs"] for r in runs),
  "all_fanouts_replicated":all(tuple(c["size"] for c in r["cells"])==sizes for r in runs),
  "oracle_and_whole_graph_parity":all(c[a]["oracle_gate"] and c["exact_graph_parity"] for c in cells for a in ("control","candidate")),
  "progress_parity_and_terminal":all(c["progress_parity"] and c["control"]["terminal_progress"]==0 and c["candidate"]["terminal_progress"]==0 for c in cells),
  "fallback_expected_by_fanout":all((c["candidate"]["stage_a_stats"]["conflict_fallbacks"]==0 if c["size"]==1 else c["candidate"]["stage_a_stats"]["conflict_fallbacks"]>0) for c in cells),
  "no_fallback_in_control":all(c["control"]["stage_a_stats"]["conflict_fallbacks"]==0 for c in cells),
  "compare_diagnostic_disabled":all(c[a]["stage_a_compare_stats"]["compared_drains"]==0 for c in cells for a in ("control","candidate")),
 }
 summary=[]
 for n in sizes:
  cs=[c for c in cells if c["size"]==n]
  summary.append({"fanout":n,"replicates":len(cs),"stage_a_fallback_counts":[c["candidate"]["stage_a_stats"]["conflict_fallbacks"] for c in cs],"ordinary_closure_progress":[c["control"]["progress"] for c in cs],"stage_a_enabled_progress":[c["candidate"]["progress"] for c in cs],"divergence_cells":sum(not c["exact_graph_parity"] or not c["progress_parity"] for c in cs)})
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"passed":all(checks.values()),"cell_count":len(cells),"summary_by_fanout":summary,"claim_boundary":p["claim_boundary"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
 if not out["passed"]:raise SystemExit("independent analysis failed")
if __name__=="__main__":main()
