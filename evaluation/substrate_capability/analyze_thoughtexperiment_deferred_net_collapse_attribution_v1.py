#!/usr/bin/env python3
"""Independent gates for deferred NetCollapse origin attribution v1."""
import hashlib, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
if os.environ.get("OCELot_NATIVE_IMPORT_ROOT"): sys.path.insert(0,os.environ["OCELot_NATIVE_IMPORT_ROOT"])
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_deferred_net_collapse_attribution_v1_lock_20261002.json"
CAPTURE=ROOT/"evaluation/reports/thoughtexperiment_deferred_net_collapse_attribution_v1_20261002.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=json.loads(LOCK.read_text()); cap=json.loads(CAPTURE.read_text()); errors=[]; ws=cap.get("workers",[])
    if cap.get("lock_sha256")!=sha(LOCK): errors.append("lock hash mismatch")
    if len(ws)!=lock["workers"]: errors.append("worker count mismatch")
    if len({w.get("pid") for w in ws})!=len(ws): errors.append("worker PIDs not distinct")
    for w in ws:
        i=w.get("worker_index"); r=w.get("result",{})
        if not w.get("source_stable") or w.get("sources_before")!=lock["sources"] or w.get("sources_after")!=lock["sources"]: errors.append(f"worker {i}: source/native fingerprint mismatch")
        if not (r.get("plain")==r.get("traced")==r.get("exact")): errors.append(f"worker {i}: settlement parity failed")
        for k in ("event_covers_exact_nodes","event_covers_exact_edges","aggregate_covers_event_nodes","aggregate_covers_event_edges","observation_consumed"):
            if not r.get(k): errors.append(f"worker {i}: {k} failed")
        if r.get("dropped_events")!=0: errors.append(f"worker {i}: trace events dropped")
        origins=r.get("origin_events",[])
        if len(origins)!=1 or any(not e.get("deferred") for e in origins): errors.append(f"worker {i}: exactly one deferred producer event required")
        if not r.get("deferred_events"): errors.append(f"worker {i}: no deferred event")
    result={"schema":"DeferredNetCollapseAttributionV1Analysis","gates_pass":not errors,"errors":errors,
      "summary":{"workers":len(ws),"unique_pids":len({w.get("pid") for w in ws}),"producer_events":sum(len(w.get("result",{}).get("origin_events",[])) for w in ws),"all_exact_changes_covered":all(w.get("result",{}).get("event_covers_exact_nodes") and w.get("result",{}).get("event_covers_exact_edges") for w in ws)}}
    out=CAPTURE.with_name("thoughtexperiment_deferred_net_collapse_attribution_v1_analysis_20261002.json")
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return int(bool(errors))
if __name__=="__main__": raise SystemExit(main())
