#!/usr/bin/env python3
"""Independent gates for deferred RuleEdit producer attribution v1."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_attribution_v1_1_lock_20261002.json"
CAPTURE=ROOT/"evaluation/reports/thoughtexperiment_deferred_rule_edit_attribution_v1_1_20261002.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text()); c=json.loads(CAPTURE.read_text()); ws=c.get("workers",[]); errors=[]
 if c.get("lock_sha256")!=sha(LOCK): errors.append("lock hash mismatch")
 if len(ws)!=l["workers"]: errors.append("worker count mismatch")
 if len({w.get("pid") for w in ws})!=len(ws): errors.append("worker PIDs not distinct")
 for w in ws:
  i=w.get("worker_index"); r=w.get("result",{})
  if not w.get("source_stable") or w.get("sources_before")!=l["sources"] or w.get("sources_after")!=l["sources"]: errors.append(f"worker {i}: source/native lock mismatch")
  if not(r.get("plain")==r.get("traced")==r.get("exact")): errors.append(f"worker {i}: settlement parity")
  if not r.get("rule_definition_changed"): errors.append(f"worker {i}: live target rule did not change")
  if not r.get("graph_target_written"): errors.append(f"worker {i}: patched target rule produced no graph write")
  if not r.get("event_covers_exact_nodes") or not r.get("event_covers_exact_edges"): errors.append(f"worker {i}: exact graph delta uncovered")
  if not r.get("aggregate_covers_event_nodes") or not r.get("aggregate_covers_event_edges"): errors.append(f"worker {i}: aggregate event targets uncovered")
  if r.get("dropped_events")!=0: errors.append(f"worker {i}: trace events dropped")
  origins=r.get("origin_events",[])
  if len(origins)!=1 or any(not x.get("deferred") for x in origins): errors.append(f"worker {i}: exactly one deferred producer event required")
  elif origins[0].get("rule_name")!="edit_target_clause": errors.append(f"worker {i}: wrong producer label")
 out={"schema":"DeferredRuleEditAttributionV1_1Analysis","gates_pass":not errors,"errors":errors,"summary":{"workers":len(ws),"unique_pids":len({w.get("pid") for w in ws}),"origin_events":sum(len(w.get("result",{}).get("origin_events",[])) for w in ws),"all_rule_and_graph_deltas_verified":all(w.get("result",{}).get("rule_definition_changed") and w.get("result",{}).get("event_covers_exact_nodes") for w in ws)}}
 dest=CAPTURE.with_name("thoughtexperiment_deferred_rule_edit_attribution_v1_1_analysis_20261002.json"); dest.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2,sort_keys=True)); return int(bool(errors))
if __name__=="__main__": raise SystemExit(main())
