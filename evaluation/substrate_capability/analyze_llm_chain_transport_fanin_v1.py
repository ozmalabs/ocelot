#!/usr/bin/env python3
"""Independent validation and hop-specific summaries for chain fan-in data."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_chain_transport_fanin_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_chain_transport_fanin_v1_20261002.json'
OUT=ROOT/'evaluation/reports/llm_chain_transport_fanin_v1_analysis_20261002.json'
FANINS=(1,2,4,8);HOPS=((10,11),(11,12),(12,13),(13,14));TOL=1e-8
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b))<TOL
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());runs=data.get('runs',[]);errors=[];cells=[];sigsets={}
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(data.get('lock_sha256')==sha(LOCK),'lock hash mismatch')
 require(data.get('sources')==lock.get('sources'),'capture/lock source mismatch')
 require(data.get('post_run_sources')==lock.get('sources'),'post-run source drift')
 require(not data.get('failures'),'worker failures recorded')
 require(len(runs)==3 and len({r.get('worker_pid') for r in runs})==len(runs),'worker count/PID mismatch')
 for ri,run in enumerate(runs):
  require(run.get('source_lock_start')==lock.get('sources')==run.get('source_lock_end'),f'worker {ri}: source drift')
  rows=run.get('rows',[]);require(len(rows)==160 and run.get('cells')==160,f'worker {ri}: grid size mismatch')
  expected={(a,b,i,k) for a,b in HOPS for i in range(10) for k in FANINS}
  actual={(c.get('source_layer'),c.get('target_layer'),c.get('heldout_index'),c.get('fan_in')) for c in rows}
  require(actual==expected,f'worker {ri}: incomplete or duplicate hop/input/fan-in grid')
  for c in rows:
   cells.append(c);hop=(c.get('source_layer'),c.get('target_layer'));key=(*hop,c.get('heldout_index'),c.get('fan_in'));sigsets.setdefault(key,[]).append(c.get('topology_signature'));label=f'worker {ri} hop {hop} input {key[2]} r={key[3]}'
   k=c.get('fan_in');sizes=c.get('component_sizes',[])
   require(c.get('nodes')==16 and c.get('edges')==8*k and c.get('pair_factors')==8*k,f'{label}: node/edge count mismatch')
   require(sum(sizes)==16 and sizes==sorted(sizes),f'{label}: component accounting invalid')
   require(c.get('width')==c.get('triangulation_width'),f'{label}: width certificate mismatch')
   require(c.get('exact_extraction') is True,f'{label}: factor extraction mismatch')
   require(close(c.get('jt_energy'),c.get('oracle_energy')) and close(c.get('direct_rescore'),c.get('oracle_energy')),f'{label}: JT/oracle/rescore mismatch')
   target=[float(v) for v in c.get('target',[])]
   for pk,sk in [('exact_prediction','exact_accuracy'),('bp_prediction','bp_accuracy'),('linear_prediction','linear_accuracy')]:
    pred=[float(v) for v in c.get(pk,[])]
    require(len(pred)==len(target)==8,f'{label}: {pk} dimension mismatch')
    if len(pred)==len(target)==8:require(abs(float(c.get(sk,-1))-sum(a==b for a,b in zip(pred,target))/8)<1e-12,f'{label}: {sk} mismatch')
   require(len(c.get('oracle_prediction',[]))==8,f'{label}: oracle prediction dimension mismatch')
   require(c.get('no_mutation') is True,f'{label}: graph mutated')
   timing=c.get('timing_ns',{})
   require(all(isinstance(timing.get(t),int) and timing[t]>=0 for t in ('graph_construction','factor_extraction','minfill_order','junction_tree','belief_propagation')),f'{label}: invalid timing')
 require(len(cells)==480,'expected 480 total graph cases')
 require(all(len(set(sigs))==1 for sigs in sigsets.values()),'topology does not replicate across workers')
 by={}
 for hop in HOPS:
  by[f'{hop[0]}->{hop[1]}']={}
  for k in FANINS:
   group=[c for c in cells if (c['source_layer'],c['target_layer'])==hop and c['fan_in']==k]
   by[f'{hop[0]}->{hop[1]}'][str(k)]={'cells':len(group),'widths':sorted(set(c['width'] for c in group)),
    'median_edges':statistics.median(c['edges'] for c in group) if group else None,'median_components':statistics.median(len(c['component_sizes']) for c in group) if group else None,
    'median_ms':{t:statistics.median(c['timing_ns'][t]/1e6 for c in group) for t in ('graph_construction','factor_extraction','minfill_order','junction_tree','belief_propagation')} if group else {},
    'mean_accuracy':{t:statistics.mean(c[t] for c in group) for t in ('exact_accuracy','bp_accuracy','linear_accuracy')} if group else {},
    'exact_bp_matches':sum(c['exact_prediction']==c['bp_prediction'] for c in group)}
 result={'schema':'LlmChainTransportFaninV1Analysis','gates_pass':not errors,'errors':errors,'summary':{'workers':len(runs),'case_count':len(cells),'by_hop_and_fan_in':by}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
