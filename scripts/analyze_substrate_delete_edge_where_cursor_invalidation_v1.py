#!/usr/bin/env python3
"""Independent scale and semantic checks for where-only cursor deletion panel."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/substrate_delete_edge_where_cursor_invalidation_v1_20260928.json";OUT=ROOT/"evaluation/reports/substrate_delete_edge_where_cursor_invalidation_v1_analysis_20260928.json"
def main():
 r=json.loads(RAW.read_text());rows=r["runs"];checks={"runner_gates_pass":r["all_checks_pass"] is True and all(r["checks"].values()),"three_unique_processes":len(rows)==9 and len({x["pid"] for x in rows})==9,"off_incremental_graph_identity":all(x["arms"]["off"]["graph"]==x["arms"]["incremental"]["graph"] for x in rows),"sound_reopens_all_slots":all(x["arms"]["off"]["open_count"]==x["arms"]["incremental"]["open_count"]==x["n"] for x in rows),"unsound_falsifier_diverges":all(x["arms"]["unsound"]["open_count"]==0 for x in rows),"incremental_candidate_rescans":all(x["arms"]["incremental"]["metrics"].get("cand_enum",0)>=x["n"] for x in rows),"manifest_success":r["run_manifest"].get("exit_status")==0}
 cells=[]
 for n in (8,32,128):
  rs=[x for x in rows if x["n"]==n];cells.append({"n":n,"replicates":len(rs),"arms":{m:{"median_candidate_pairs":int(statistics.median(x["arms"][m]["metrics"].get("cand_enum",0) for x in rs)),"median_rule_enumerations":int(statistics.median(x["arms"][m]["metrics"].get("rule_enumerations",0) for x in rs)),"median_post_delete_wall_ns":int(statistics.median(x["arms"][m]["post_delete_wall_ns"] for x in rs)),"open_count":rs[0]["arms"][m]["open_count"]} for m in ("off","incremental","unsound")}})
 out={"analysis_id":"substrate-delete-edge-where-cursor-invalidation-v1-independent-analysis","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"all_checks_pass":all(checks.values()),"cells":cells,"claim_boundary":r["claim_boundary"]};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"checks_passed":out["checks_passed"],"checks_total":out["checks_total"],"all_checks_pass":out["all_checks_pass"],"cells":cells},indent=2));return 0 if out["all_checks_pass"] else 1
if __name__=="__main__":raise SystemExit(main())
