#!/usr/bin/env python3
"""Independent validation for live instruction event/Goal producer probe."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_action_event_identity_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_action_event_identity_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_action_event_identity_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 per={}
 for row in runs:
  state_kinds=row["state_event_kind_counts"];events=row["new_discourse_events"];goals=row["new_goal_rows"]
  action_goals=[g for g in goals if g["attrs"].get("source")=="conversation"]
  per[str(row["replicate"]) ]={"one_inbound_instruction_event":len(events)==1 and events[0]["attrs"].get("kind")=="instruction",
   "event_has_no_explicit_for_goal_edge":events==[{**events[0],"for_goal_edges":[]}] if events else False,
   "conversation_goal_bound_to_message_and_origin_event":bool(action_goals) and all(g["comprehends_inbound"] and g["originated_in_inbound_event"] for g in action_goals),
   "lifecycle_event_kinds_absent":all(state_kinds.get(k)==0 for k in ("selection","execution","action_result")),
   "no_new_goal_has_lifecycle_transition":all(not g["transition_events"] for g in goals),
   "goal_deliberations_are_empty_state_routes":all(all(d["candidate_source"]=="discourse_state" and d["status"]=="no_candidate" for d in g["deliberations"]) for g in action_goals)}
 checks={"locked_input_and_output_hash_match":raw["locked_inputs"]==lock["locked_inputs"] and raw["lock_sha256"]==sha(LOCK),
  "three_distinct_fresh_workers":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "runner_gates_pass":all(raw["checks"].values()),
  "independent_live_path_gates_pass":all(all(g.values()) for g in per.values()),
  "replicates_match_event_goal_kind_shape":len({json.dumps({"events":r["new_discourse_events"],"goals":r["new_goal_rows"],"kinds":r["state_event_kind_counts"]},sort_keys=True) for r in runs})==1}
 result={"schema_version":1,"run_id":"substrate-live-action-event-identity-v1-analysis-20260926",
  "raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"worker_gates":per,
  "summary":raw["summary"],"claim_boundary":raw["claim_boundary"],
  "interpretation":"The tested live instruction path produces inbound message/discourse provenance and conversation Goals bound to that turn. It produces no operation lifecycle DiscourseEvents and the new Goals have no lifecycle transitions. This is a bounded path audit; it does not establish absence in all producers or applications."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"worker_gates":per},indent=2))
 if not all(checks.values()):raise SystemExit("independent live event/Goal analysis failed")
if __name__=="__main__":main()
