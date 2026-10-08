#!/usr/bin/env python3
"""Independent audit of the live Goal lifecycle identity integration capture."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_8_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_8_lock_20260926.json"
RUNNER=ROOT/"scripts/substrate_live_self_report_lifecycle_identity_integration_v1_8.py"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_PREREG_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_8_AMENDMENT_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json",
 "analyzer":ROOT/"scripts/analyze_substrate_live_self_report_lifecycle_identity_integration_v1_8.py"}
OUT=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_8_diagnostic_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_closure():
 paths=set()
 for folder in (ROOT/"domains",ROOT/"substrate",ROOT/"runners/dsl/python"):
  paths.update(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
 seed_dir=ROOT/"seeds";paths.update(seed_dir.glob("*.json"));paths.update((seed_dir/"generated").glob("*.json"))
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"]
 from substrate_rs import _native
 expected={"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"runner_sha256":sha(RUNNER),
 "source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "source_closure_sha256":source_closure(),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":locked.get("commit")}
 runs=raw.get("runs",[]);cs=raw.get("controls",{})
 positives=all(len(r.get("turns",[]))==2 and (lambda t:t.get("route")=="self_report" and t.get("reply_nonempty") and t.get("goal_count")==1 and t.get("goal_origin_matches") and t.get("origin_event_separate") and (t.get("goal") or {}).get("attrs",{}).get("self_target")==t.get("expected_self_target") and (t.get("goal") or {}).get("status")=="resolved" and (t.get("goal") or {}).get("transition_kinds")==["selection","execution","action_result"] and (t.get("goal") or {}).get("transition_links_all_bound") and (t.get("goal") or {}).get("closed") and not (t.get("goal") or {}).get("active") and [e.get("kind") for e in t.get("lifecycle_events",[]) ]==["selection","execution","action_result"])(r["turns"][0]) and r.get("same_recipient") for r in runs)
 cchecks={
  "correct_link_selects_only_owner":cs.get("correct_link",{}).get("statuses")==["selected","proposed"] and len(cs.get("correct_link",{}).get("event_goal_ids",[]))==1,
  "omitted_link_selects_no_goal":cs.get("omitted_link",{}).get("statuses")==["proposed","proposed"] and not cs.get("omitted_link",{}).get("event_goal_ids"),
  "swapped_link_follows_explicit_edge":cs.get("swapped_link",{}).get("statuses")==["proposed","selected"] and cs.get("swapped_link",{}).get("declared_target")==cs.get("swapped_link",{}).get("goal_ids",[None])[0] and cs.get("swapped_link",{}).get("event_goal_ids")==[cs.get("swapped_link",{}).get("goal_ids",[None,None])[1]],
  "duplicate_result_is_idempotent_and_closed":cs.get("duplicate_result",{}).get("status")=="resolved" and cs.get("duplicate_result",{}).get("transition_kinds")==["selection","execution","action_result"] and cs.get("duplicate_result",{}).get("result_event_count")==2 and cs.get("duplicate_result",{}).get("closed") and not cs.get("duplicate_result",{}).get("active"),
  "faculty_failure_blocks_and_closes":cs.get("faculty_failure",{}).get("goal_status")=="blocked" and cs.get("faculty_failure",{}).get("goal_transition_kinds")==["selection","execution","action_failure"] and cs.get("faculty_failure",{}).get("closed") and not cs.get("faculty_failure",{}).get("active") and "action_result" not in cs.get("faculty_failure",{}).get("event_kinds",[])}
 work_profiles=[];work_by_kind={}
 for run in runs:
  profile=[];kind_counts={};total_pairs=0;total_terms=0
  for turn in run.get("turns",[]):
   calls=turn.get("producer_work",[])
   for row in calls:
    c=row["counters"]["scale"];pr={}
    for _,metric,value in row["counters"]["per_rule"]:pr[metric]=pr.get(metric,0)+value
    conserved=(c.get("cand_enum",0)==pr.get("candidate_pairs",0) and c.get("term_evals_total",0)==pr.get("term_evaluations",0) and c.get("term_evals_total",0)==sum(v for k,v in c.items() if k.startswith("term_eval:")))
    profile.append((turn["turn"],row["kind"],c.get("cand_enum",0),c.get("term_evals_total",0),conserved))
    total_pairs+=c.get("cand_enum",0);total_terms+=c.get("term_evals_total",0)
    kind_counts.setdefault(row["kind"],{"calls":0,"candidate_pairs":0,"term_evaluations":0,"elapsed_ns":[]})
    k=kind_counts[row["kind"]];k["calls"]+=1;k["candidate_pairs"]+=c.get("cand_enum",0);k["term_evaluations"]+=c.get("term_evals_total",0);k["elapsed_ns"].append(row["elapsed_ns"])
   expected_calls=["selection","execution","action_result"] if turn["turn"]==0 else []
   if [x["kind"] for x in calls]!=expected_calls:profile.append((turn["turn"],"wrong_call_shape"))
   profile.append((turn["turn"],turn.get("route"),turn.get("goal_count"),bool(turn.get("reply_nonempty"))))
  work_profiles.append(profile);work_by_kind[run["replicate"]]={"candidate_pairs":total_pairs,"term_evaluations":total_terms,"by_kind":kind_counts}
 noncap_runner={k:v for k,v in raw.get("checks",{}).items() if k!="production_route_identity_and_lifecycle"}
 checks={"raw_lock_matches_current_sources":locked==expected==raw.get("locked_inputs"),
  "all_worker_and_postrun_fingerprints_stable":raw.get("post_run_inputs")==locked and all(r.get("worker_started_inputs")==locked and r.get("worker_finished_inputs")==locked for r in runs),
  "three_distinct_fresh_pids":len(runs)==3 and len({r.get("pid") for r in runs})==3,
  "first_prompt_live_producer_lifecycle_passes":positives,
  "event_identity_shape_repeats":len({json.dumps([{ "prompt":t.get("prompt"),"expected_self_target":t.get("expected_self_target"),"route":t.get("route"),"event_kinds":[e.get("kind") for e in t.get("lifecycle_events",[])],"goal_status":(t.get("goal") or {}).get("status"),"transition_kinds":(t.get("goal") or {}).get("transition_kinds")} for t in r.get("turns",[])],sort_keys=True) for r in runs})==1,
  "five_controls_pass":all(cchecks.values()),"all_noncapability_runner_gates_pass":all(noncap_runner.values()) and all(raw.get("control_checks",{}).values()),
  "three_producer_calls_on_valid_first_prompt":all(sum(len(t.get("producer_work",[])) for t in r["turns"])==3 for r in runs),"producer_counter_conservation":all(x[-1] for p in work_profiles for x in p if len(x)==5),
  "second_prompt_dispatch_shortfall_replicates":all(r["turns"][1].get("route") is None and r["turns"][1].get("goal_count")==0 and not r["turns"][1].get("lifecycle_events") and not r["turns"][1].get("producer_work") and r["turns"][1].get("reply_nonempty") for r in runs),
  "producer_work_replicates_exactly":len({json.dumps(p,sort_keys=True) for p in work_profiles})==1}
 producer_summary={}
 for kind in ("selection","execution","action_result"):
  event_times=[t for r in runs for turn in r["turns"] for t in turn["producer_work"] if t["kind"]==kind]
  sample=next(iter(work_by_kind.values()))["by_kind"][kind]
  producer_summary[kind]={"calls_per_run":sample["calls"],"candidate_pairs_per_run":sample["candidate_pairs"],"term_evaluations_per_run":sample["term_evaluations"],"median_elapsed_ns_per_call":statistics.median(t["elapsed_ns"] for t in event_times),"elapsed_ns_range":[min(t["elapsed_ns"] for t in event_times),max(t["elapsed_ns"] for t in event_times)]}
 analysis={"schema_version":1,"raw_capture":str(RAW.relative_to(ROOT)),"raw_sha256":sha(RAW),"checks":checks,"control_checks":cchecks,
  "analysis_valid":all(checks.values()),"capability_gate_pass":positives,
  "production_helper_work_by_replicate":work_by_kind,"production_helper_work_summary":producer_summary,
  "metrics":{"replicates":len(runs),"distinct_pids":len({r.get("pid") for r in runs}),"median_full_seed_boot_seconds":raw.get("summary",{}).get("boot_ns_median",0)/1e9,"median_turn_seconds":raw.get("summary",{}).get("turn_ns_median",0)/1e9},
  "conclusion":"The amended producer emits Goal-bound selection, execution, and result events on the live self_report route. Native identity-constrained rules resolve each successful Goal and close it; omission/swapped-link/duplicate-result/faculty-failure controls pass. Scope is limited to this action route and two sequential same-recipient turns."}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"control_checks":cchecks,"metrics":analysis["metrics"]},indent=2))
 if not all(checks.values()):raise SystemExit("diagnostic analysis could not reproduce/verify the preserved capture")
if __name__=="__main__":main()
