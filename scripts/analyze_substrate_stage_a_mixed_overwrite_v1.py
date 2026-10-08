#!/usr/bin/env python3
"""Independently validate mixed overwrite compare-mode captures."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_stage_a_mixed_overwrite_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/stage_a_mixed_overwrite_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_stage_a_mixed_overwrite_v1_analysis_20260926.json"
SIZES=(1,2,6,16,32)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 cells=[(r,c) for r in runs for c in r["cells"]]
 checks={"raw_and_lock_match":raw["locked_inputs"]==locked and raw["lock_sha256"]==sha(LOCK),
  "three_source_stable_workers":len({r["pid"] for r in runs})==3 and raw["post_run_inputs"]==locked and all(r["started_inputs"]==locked==r["finished_inputs"] for r in runs),
  "five_binding_sizes_each":len(cells)==15 and all(tuple(c["size"] for c in r["cells"])==SIZES for r in runs),
  "normal_closure_and_compare_match_exact_oracle":all(c["control"]["oracle_gate"] and c["candidate"]["oracle_gate"] and c["exact_graph_parity"] and c["progress_parity"] for _,c in cells),
  "mixed_overwrite_enters_stage_a_compare":all(c["candidate"]["stage_a_compare_stats"]["compared_drains"]==1 for _,c in cells),
  "no_divergence_or_unsound_drain":all(c["candidate"]["stage_a_compare_stats"]["diverged_drains"]==0 and c["candidate"]["stage_a_compare_stats"]["unsound_drains"]==0 for _,c in cells),
  "repeat_projection_stable":len({json.dumps([(c["size"],c["candidate"]["oracle_gate"],c["exact_graph_parity"],c["candidate"]["stage_a_compare_stats"]["compared_drains"],c["candidate"]["stage_a_compare_stats"]["diverged_drains"],c["candidate"]["stage_a_compare_stats"]["unsound_drains"]) for c in r["cells"]],sort_keys=True) for r in runs})==1}
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"finding":"A mixed SetAttr plus existing-edge attribute replacement rule entered Stage A compare for independent one-variable bindings at 1, 2, 6, 16, and 32 bindings. Every case compared exactly one drain, reported zero divergence and unsoundness, and produced the same complete graph, progress count, terminal result, and independent output oracle as ordinary closure.","limits":"One self-loop match shape with independent nodes and literal attr keys/values. No contended writes, multi-variable binding, mint/delete, rule-order interaction, concurrency, or workload distribution is covered."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("mixed overwrite analysis failed")
if __name__=="__main__":main()
