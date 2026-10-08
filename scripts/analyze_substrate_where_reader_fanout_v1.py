#!/usr/bin/env python3
"""Independent fan-out and scaling analysis for where-reader deletion."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/substrate_where_reader_fanout_v1_20260928.json";OUT=ROOT/"evaluation/reports/substrate_where_reader_fanout_v1_analysis_20260928.json"
def med(rows,fn):return int(statistics.median(fn(r) for r in rows))
def main():
 raw=json.loads(RAW.read_text());runs=raw["runs"];checks={"runner_gates_pass":raw["all_checks_pass"] is True and all(raw["checks"].values()),"36_distinct_workers":len(runs)==36 and len({r["pid"] for r in runs})==36,"all_sound_graphs_match":all(r["arms"]["off"]["graph"]==r["arms"]["incremental"]["graph"] for r in runs),"falsifier_diverges_everywhere":all(r["arms"]["unsound"]["open_count"]==0 and r["arms"]["incremental"]["open_count"]==r["n"] for r in runs),"candidate_work_equals_reader_times_bindings":all(r["arms"]["incremental"]["metrics"].get("cand_enum",0)==r["reader_count"]*r["n"] for r in runs),"manifest_success":raw["run_manifest"].get("exit_status")==0}
 cells=[]
 for family in ("out_edges","in_neighbours"):
  for n in (32,128):
   for readers in (1,4,16):
    rs=[r for r in runs if r["family"]==family and r["n"]==n and r["reader_count"]==readers]
    cells.append({"family":family,"n":n,"reader_count":readers,"replicates":len(rs),"expected_candidate_pairs":n*readers,"arms":{mode:{"median_candidate_pairs":med(rs,lambda r:r["arms"][mode]["metrics"].get("cand_enum",0)),"median_rule_enumerations":med(rs,lambda r:r["arms"][mode]["metrics"].get("rule_enumerations",0)),"median_settle_wall_ns":med(rs,lambda r:r["arms"][mode]["settle_wall_ns"]),"median_delete_wall_ns":med(rs,lambda r:r["arms"][mode]["delete_wall_ns"]),"open_count":rs[0]["arms"][mode]["open_count"]} for mode in ("off","incremental","unsound")}})
 checks["all_12_cell_counts_recomputed"]=len(cells)==12 and all(c["replicates"]==3 and c["arms"]["incremental"]["median_candidate_pairs"]==c["expected_candidate_pairs"] for c in cells)
 out={"analysis_id":"substrate-where-reader-fanout-v1-independent-analysis","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"all_checks_pass":all(checks.values()),"cells":cells,"claim_boundary":raw["claim_boundary"]};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"checks_passed":out["checks_passed"],"checks_total":out["checks_total"],"all_checks_pass":out["all_checks_pass"],"cells":cells},indent=2));return 0 if out["all_checks_pass"] else 1
if __name__=="__main__":raise SystemExit(main())
