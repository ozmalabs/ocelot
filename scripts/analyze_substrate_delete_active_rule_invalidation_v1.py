#!/usr/bin/env python3
"""Independent analysis of active-rule deletion refresh probe."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_delete_active_rule_invalidation_v1_1_20260928.json"
OUT=ROOT/"evaluation/reports/substrate_delete_active_rule_invalidation_v1_1_analysis_20260928.json"
def main():
 raw=json.loads(RAW.read_text()); rows=raw["runs"]
 checks={"runner_gates_pass":raw.get("all_checks_pass") is True and all(raw["checks"].values()),
  "three_unique_processes":len(rows)==3 and len({r["pid"] for r in rows})==3,
  "default_mode_refreshes_in_every_replica":all(r["default"]["final_value"]==0 and r["default"]["independent_watched_count"]==0 for r in rows),
  "precise_mode_refreshes_every_replica":all(r["precise"]["final_value"]==0 and r["precise"]["independent_watched_count"]==0 for r in rows),
  "precise_mode_enumerates_reader_after_delete":all(r["precise"]["delete_settle_metrics"].get("rule_enumerations",0)>=1 and r["precise"]["delete_settle_metrics"].get("cand_enum",0)>=1 for r in rows),
  "default_mode_enumerates_reader":all(r["default"]["delete_settle_metrics"].get("rule_enumerations",0)>=1 for r in rows),
  "initial_and_postdelete_reports_fixed_point":all(r[k]["initial_report"]["status"]==r[k]["delete_settle_report"]["status"]=="fixed_point" for r in rows for k in ("default","precise")),
  "manifest_success":raw["run_manifest"].get("exit_status")==0}
 result={"analysis_id":"substrate-delete-active-rule-invalidation-v1-1-independent-analysis","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),
  "checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"all_checks_pass":all(checks.values()),
  "per_condition_medians":{k:{"delete_settle_wall_ns":sorted(r[k]["delete_settle_wall_ns"] for r in rows)[1],
   "rule_enumerations":sorted(r[k]["delete_settle_metrics"].get("rule_enumerations",0) for r in rows)[1],
   "candidate_pairs":sorted(r[k]["delete_settle_metrics"].get("cand_enum",0) for r in rows)[1],
   "final_value":r[k]["final_value"]} for k in ("default","precise") for r in rows[:1]},
  "claim_boundary":raw["claim_boundary"]}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"checks_passed":result["checks_passed"],"checks_total":result["checks_total"],"all_checks_pass":result["all_checks_pass"],"output":str(OUT.relative_to(ROOT))},indent=2))
 return 0 if result["all_checks_pass"] else 1
if __name__=="__main__": raise SystemExit(main())
