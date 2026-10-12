#!/usr/bin/env python3
"""Independent audit of the live Goal lifecycle identity integration capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_4_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_4_lock_20260926.json"
RUNNER=ROOT/"scripts/substrate_live_self_report_lifecycle_identity_integration_v1.py"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_PREREG_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_4_AMENDMENT_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json"}
OUT=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_4_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"]
 from substrate_rs import _native
 expected={"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"runner_sha256":sha(RUNNER),
  "source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":locked.get("commit")}
 runs=raw.get("runs",[]);cs=raw.get("controls",{})
 positives=all(len(r.get("turns",[]))==2 and all(t.get("route")=="self_report" and t.get("reply_nonempty") and t.get("reply_mentions_organisation") and t.get("goal_count")==1 and t.get("goal_origin_matches") and t.get("origin_event_separate") and t.get("goal",{}).get("status")=="resolved" and t.get("goal",{}).get("transition_kinds")==["selection","execution","action_result"] and t.get("goal",{}).get("transition_links_all_bound") and t.get("goal",{}).get("closed") and not t.get("goal",{}).get("active") and [e.get("kind") for e in t.get("lifecycle_events",[]) ]==["selection","execution","action_result"] for t in r.get("turns",[])) and r.get("same_recipient") and r.get("distinct_identity") for r in runs)
 cchecks={
  "correct_link_selects_only_owner":cs.get("correct_link",{}).get("statuses")==["selected","proposed"] and len(cs.get("correct_link",{}).get("event_goal_ids",[]))==1,
  "omitted_link_selects_no_goal":cs.get("omitted_link",{}).get("statuses")==["proposed","proposed"] and not cs.get("omitted_link",{}).get("event_goal_ids"),
  "swapped_link_follows_explicit_edge":cs.get("swapped_link",{}).get("statuses")==["proposed","selected"] and cs.get("swapped_link",{}).get("declared_target")==cs.get("swapped_link",{}).get("goal_ids",[None])[0] and cs.get("swapped_link",{}).get("event_goal_ids")==[cs.get("swapped_link",{}).get("goal_ids",[None,None])[1]],
  "duplicate_result_is_idempotent_and_closed":cs.get("duplicate_result",{}).get("status")=="resolved" and cs.get("duplicate_result",{}).get("transition_kinds")==["selection","execution","action_result"] and cs.get("duplicate_result",{}).get("result_event_count")==2 and cs.get("duplicate_result",{}).get("closed") and not cs.get("duplicate_result",{}).get("active"),
  "faculty_failure_blocks_and_closes":cs.get("faculty_failure",{}).get("goal_status")=="blocked" and cs.get("faculty_failure",{}).get("goal_transition_kinds")==["selection","execution","action_failure"] and cs.get("faculty_failure",{}).get("closed") and not cs.get("faculty_failure",{}).get("active") and "action_result" not in cs.get("faculty_failure",{}).get("event_kinds",[])}
 checks={"raw_lock_matches_current_sources":locked==expected==raw.get("locked_inputs"),
  "all_worker_and_postrun_fingerprints_stable":raw.get("post_run_inputs")==locked and all(r.get("worker_started_inputs")==locked and r.get("worker_finished_inputs")==locked for r in runs),
  "three_distinct_fresh_pids":len(runs)==3 and len({r.get("pid") for r in runs})==3,
  "live_producer_events_have_one_goal_owner":positives,
  "event_identity_shape_repeats":len({json.dumps([{ "route":t.get("route"),"event_kinds":[e.get("kind") for e in t.get("lifecycle_events",[])],"goal_status":t.get("goal",{}).get("status"),"transition_kinds":t.get("goal",{}).get("transition_kinds")} for t in r.get("turns",[])],sort_keys=True) for r in runs})==1,
  "five_controls_pass":all(cchecks.values()),"runner_gates_pass":all(raw.get("checks",{}).values()) and all(raw.get("control_checks",{}).values())}
 analysis={"schema_version":1,"raw_capture":str(RAW.relative_to(ROOT)),"raw_sha256":sha(RAW),"checks":checks,"control_checks":cchecks,
  "metrics":{"replicates":len(runs),"distinct_pids":len({r.get("pid") for r in runs}),"median_full_seed_boot_seconds":raw.get("summary",{}).get("boot_ns_median",0)/1e9,"median_turn_seconds":raw.get("summary",{}).get("turn_ns_median",0)/1e9},
  "conclusion":"The amended producer emits Goal-bound selection, execution, and result events on the live self_report route. Native identity-constrained rules resolve each successful Goal and close it; omission/swapped-link/duplicate-result/faculty-failure controls pass. Scope is limited to this action route and two sequential same-recipient turns."}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"control_checks":cchecks,"metrics":analysis["metrics"]},indent=2))
 if not all(checks.values()):raise SystemExit("independent lifecycle integration analysis failed")
if __name__=="__main__":main()
