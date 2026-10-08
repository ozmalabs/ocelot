#!/usr/bin/env python3
"""Independent gates for deferred framebuffer sample attribution v1."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_deferred_fb_sample_attribution_v1_lock_20261002.json"
CAPTURE=ROOT/"evaluation/reports/thoughtexperiment_deferred_fb_sample_attribution_v1_20261002.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text()); c=json.loads(CAPTURE.read_text()); ws=c.get("workers",[]); err=[]
 if c.get("lock_sha256")!=sha(LOCK): err.append("lock hash mismatch")
 if len(ws)!=l["workers"]: err.append("worker count mismatch")
 if len({w.get("pid") for w in ws})!=len(ws): err.append("worker PIDs not distinct")
 for w in ws:
  i=w.get("worker_index"); r=w.get("result",{})
  if not w.get("source_stable") or w.get("sources_before")!=l["sources"] or w.get("sources_after")!=l["sources"]: err.append(f"worker {i}: source/native lock mismatch")
  if not(r.get("plain")==r.get("traced")==r.get("exact")): err.append(f"worker {i}: settlement parity")
  if r.get("region_count",0)<1 or r.get("world_instance_count",0)<4: err.append(f"worker {i}: non-vacuous framebuffer graph absent")
  for k in ("event_covers_exact_nodes","event_covers_exact_edges","aggregate_covers_event_nodes","aggregate_covers_event_edges"):
   if not r.get(k): err.append(f"worker {i}: {k} failed")
  if r.get("dropped_events")!=0: err.append(f"worker {i}: trace events dropped")
  origins=r.get("origin_events",[])
  if len(origins)!=1 or not origins[0].get("deferred") or not origins[0].get("progressed"): err.append(f"worker {i}: exactly one successful deferred origin event required")
  elif origins[0].get("rule_name")!="look_when_frame_advances": err.append(f"worker {i}: wrong producer identity")
 out={"schema":"DeferredFbSampleAttributionV1Analysis","gates_pass":not err,"errors":err,"summary":{"workers":len(ws),"unique_pids":len({w.get("pid") for w in ws}),"successful_deferred_origin_events":sum(len(w.get("result",{}).get("origin_events",[])) for w in ws),"all_exact_graph_deltas_covered":all(w.get("result",{}).get("event_covers_exact_nodes") and w.get("result",{}).get("event_covers_exact_edges") for w in ws)}}
 dest=CAPTURE.with_name("thoughtexperiment_deferred_fb_sample_attribution_v1_analysis_20261002.json"); dest.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2,sort_keys=True)); return int(bool(err))
if __name__=="__main__": raise SystemExit(main())
