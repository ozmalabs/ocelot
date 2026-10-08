#!/usr/bin/env python3
"""Independent structural audit of the live multi-Goal origin capture."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_live_multi_goal_origin_identity_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/live_multi_goal_origin_identity_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_multi_goal_origin_identity_v1_analysis_20260926.json"
RUNNER=ROOT/"scripts/substrate_live_multi_goal_origin_identity_v1.py"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_MULTI_GOAL_ORIGIN_IDENTITY_PREREG_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","discourse_state":ROOT/"domains/discourse_state.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json",
 "phase4a_seed":ROOT/"seeds/conversation_deliberation_phase4a.json"}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text())["locked_inputs"]
 from substrate_rs import _native
 expected={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(RUNNER),
  "source_sha256":{k:sha(p) for k,p in SOURCES.items()},
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":lock.get("commit")}
 runs=raw["runs"]
 checks={"raw_lock_matches_current_sources":raw.get("locked_inputs")==expected==lock,
  "three_fresh_processes":len(runs)==3 and len({r.get("pid") for r in runs})==3,
  "each_run_has_two_distinct_instruction_origins":all(len(r.get("records",[]))==2 and len({x.get("message_id") for x in r["records"]})==2 and len({x.get("event_id") for x in r["records"]})==2 for r in runs),
  "each_goal_maps_only_to_its_turn_origin":all(all(len(x.get("goals",[]))==1 and x["goals"][0].get("comprehends_message") and x["goals"][0].get("originates_in_event") and x.get("new_action_goal_count")==1 and x.get("new_discourse_event_count")==1 for x in r["records"]) for r in runs),
  "same_recipient_per_run":all(r.get("same_recipient") and r["records"][0]["event_recipients"]==r["records"][1]["event_recipients"] for r in runs),
  "no_goal_cross_links_in_capture":all(not x.get("event_for_goal_edges") for r in runs for x in r["records"]),
  "no_selection_execution_or_result_events":all(r.get("state_event_kind_counts",{}).get(k)==0 for r in runs for k in ("selection","execution","action_result")),
  "no_goal_lifecycle_transitions":all(not g.get("transition_events") for r in runs for x in r["records"] for g in x["goals"]),
  "producer_shape_replicates":len({json.dumps([{k:x[k] for k in ("event_attrs","event_for_goal_edges","event_recipients","goals")} for x in r["records"]],sort_keys=True) for r in runs})==1}
 analysis={"schema_version":1,"raw_capture":str(RAW.relative_to(ROOT)),"raw_sha256":sha(RAW),"checks":checks,
  "metrics":{"replicates":len(runs),"distinct_pids":len({r.get("pid") for r in runs}),"median_full_seed_boot_seconds":raw.get("summary",{}).get("boot_ns_median",0)/1e9,"median_two_turn_seconds":raw.get("summary",{}).get("turn_median_ns_median",0)*2/1e9,"median_per_turn_seconds":raw.get("summary",{}).get("turn_median_ns_median",0)/1e9,"event_kinds":raw.get("summary",{}).get("operation_event_counts")},
  "conclusion":"The live path preserves distinct origin links for two same-recipient instruction Goals across three fresh full-seed runs. It emits no selection, execution, action_result, or Goal transition events in this probe. This demonstrates ingress provenance only, not downstream action lifecycle identity or general action execution."}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"checks":checks,"metrics":analysis["metrics"]},indent=2))
 if not all(checks.values()): raise SystemExit("independent analysis gate failed")
if __name__=="__main__": run()
