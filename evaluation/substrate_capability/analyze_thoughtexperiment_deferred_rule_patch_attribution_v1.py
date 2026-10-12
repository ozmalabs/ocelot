#!/usr/bin/env python3
"""Independent multi-producer gates for deferred RulePatch attribution."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_deferred_rule_patch_attribution_v1_lock_20261002.json"
CAPTURE=ROOT/"evaluation/reports/thoughtexperiment_deferred_rule_patch_attribution_v1_20261002.json"
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
  if r.get("producer_names")!=r.get("expected_producers"): errors.append(f"worker {i}: full producer-origin set mismatch")
  if r.get("patch_status")!="committed" or not r.get("target_changed"): errors.append(f"worker {i}: patch did not commit exactly once")
  if r.get("target_revision_after")!=r.get("target_revision_before",0)+1: errors.append(f"worker {i}: target revision did not advance once")
  if not r.get("exact_patch_node_covered"): errors.append(f"worker {i}: patch receipt node absent from trace")
  for k in ("event_covers_exact_nodes","event_covers_exact_edges","aggregate_covers_event_nodes","aggregate_covers_event_edges"):
   if not r.get(k): errors.append(f"worker {i}: {k} failed")
  if r.get("dropped_events")!=0: errors.append(f"worker {i}: trace events dropped")
  d=r.get("deferred_events",[])
  if len(d)!=1 or not d[0].get("progressed") or len(d[0].get("origin_rules",[]))!=2: errors.append(f"worker {i}: deduplicated event lacks both origins")
 out={"schema":"DeferredRulePatchAttributionV1Analysis","gates_pass":not errors,"errors":errors,"summary":{"workers":len(ws),"unique_pids":len({w.get("pid") for w in ws}),"deferred_multi_origin_events":sum(len(w.get("result",{}).get("deferred_events",[])) for w in ws),"all_patch_and_graph_state_verified":all(w.get("result",{}).get("target_changed") and w.get("result",{}).get("event_covers_exact_nodes") for w in ws)}}
 dest=CAPTURE.with_name("thoughtexperiment_deferred_rule_patch_attribution_v1_analysis_20261002.json"); dest.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2,sort_keys=True)); return int(bool(errors))
if __name__=="__main__": raise SystemExit(main())
