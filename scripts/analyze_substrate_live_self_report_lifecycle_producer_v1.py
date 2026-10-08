#!/usr/bin/env python3
"""Independent audit of the live self-report lifecycle producer capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_lifecycle_producer_v1_1_lock_20260926.json"
RUNNER=ROOT/"scripts/substrate_live_self_report_lifecycle_producer_v1.py"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_PREREG_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_V1_1_AMENDMENT_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","discourse_state":ROOT/"domains/discourse_state.py",
 "conversation_action":ROOT/"domains/conversation_action.py","reflective_faculty":ROOT/"domains/reflective_faculty.py",
 "self_model":ROOT/"domains/self_model.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json"}
OUT=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def signature(run):
 return [{"route":t.get("communication_route"),"reply_nonempty":t.get("reply_nonempty"),"reply_mentions_organisation":t.get("reply_mentions_organisation"),
  "event_kind":(t.get("event_attrs") or {}).get("kind"),"goal_attrs":{k:t["goals"][0]["attrs"].get(k) for k in ("kind","predicate","object","self_target","source")} if t.get("goals") else None,
  "recipient_count":len(t.get("event_recipients",[])),"goal_origin":t["goals"][0].get("originates_in_event",False) if t.get("goals") else False} for t in run.get("turns",[])]
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"]
 from substrate_rs import _native
 expected={"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"runner_sha256":sha(RUNNER),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":locked.get("commit")}
 runs=raw.get("runs",[])
 checks={"raw_lock_matches_current_sources":locked==expected==raw.get("locked_inputs"),
  "worker_and_postrun_source_fingerprints_match_lock":raw.get("post_run_inputs")==locked and all(r.get("worker_started_inputs")==locked and r.get("worker_finished_inputs")==locked for r in runs),
  "three_fresh_processes":len(runs)==3 and len({r.get("pid") for r in runs})==3,
  "each_run_contains_two_live_held_self_report_turns":all(len(r.get("turns",[]))==2 and r.get("positive_route_and_origin_gate") for r in runs),
  "recipient_stable_and_goal_ids_distinct":all(r.get("same_recipient") and r.get("distinct_turn_identity") for r in runs),
  "each_goal_comprehends_its_own_origin":all(all(t.get("goal_count")==1 and t["goals"][0].get("originates_in_event") and t["goals"][0]["attrs"].get("origin_turn_id")==t.get("message_id") for t in r["turns"]) for r in runs),
  "no_for_goal_lifecycle_links":all(all(not t.get("event_for_goal_edges") for t in r["turns"]) for r in runs),
  "no_lifecycle_events_or_transitions":all(r.get("lifecycle_gap") and all(r.get("event_counts",{}).get(k)==0 for k in ("selection","execution","action_result")) for r in runs),
  "producer_shape_repeats":len({json.dumps(signature(r),sort_keys=True) for r in runs})==1,
  "runner_gates_pass":all(raw.get("checks",{}).values())}
 analysis={"schema_version":1,"raw_capture":str(RAW.relative_to(ROOT)),"raw_sha256":sha(RAW),"checks":checks,
  "metrics":{"replicates":len(runs),"distinct_pids":len({r.get("pid") for r in runs}),"median_full_seed_boot_seconds":raw.get("summary",{}).get("boot_ns_median",0)/1e9,"median_turn_seconds":raw.get("summary",{}).get("turn_ns_median",0)/1e9,"event_counts":raw.get("summary",{}).get("event_counts")},
  "conclusion":"The repeated live held self-report route preserves distinct per-turn Goal origin provenance across two same-recipient turns and three fresh full-seed runs. Although the reply route is self_report, the discourse lifecycle stream records only the inbound instructions: no selection, execution, action_result, for_goal edge, or Goal transition was observed. This is evidence for the audited route only; the reply is not itself a durable execution receipt."}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"checks":checks,"metrics":analysis["metrics"]},indent=2))
 if not all(checks.values()):raise SystemExit("independent self-report analysis gate failed")
if __name__=="__main__":main()
