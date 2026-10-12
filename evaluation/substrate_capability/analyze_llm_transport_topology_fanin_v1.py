#!/usr/bin/env python3
"""Independent validation and fan-in summaries for transport sparsification."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_topology_fanin_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_transport_topology_fanin_v1_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_topology_fanin_v1_analysis_20261002.json'
FANINS=(1,2,4,8);TOL=1e-8
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b))<TOL
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());runs=data.get('runs',[]);errors=[];cells=[]
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(data.get('lock_sha256')==sha(LOCK),'lock hash mismatch')
 require(data.get('sources')==lock.get('sources'),'capture/lock source mismatch')
 require(data.get('post_run_sources')==lock.get('sources'),'post-run source drift')
 require(not data.get('failures'),'worker failures recorded')
 require(len(runs)==3 and len({r.get('worker_pid') for r in runs})==len(runs),'worker count/PID mismatch')
 by_key={}
 for ri,r in enumerate(runs):
  require(r.get('source_lock_start')==lock.get('sources')==r.get('source_lock_end'),f'worker {ri}: source drift')
  rows=r.get('rows',[]);require(len(rows)==40 and r.get('input_cells')==40,f'worker {ri}: grid size mismatch')
  require({(c.get('heldout_index'),c.get('fan_in')) for c in rows}=={(i,k) for i in range(10) for k in FANINS},f'worker {ri}: incomplete/duplicate grid')
  for c in rows:
   cells.append(c);key=(c.get('heldout_index'),c.get('fan_in'));by_key.setdefault(key,[]).append(c.get('topology_signature'))
   label=f'worker {ri} input {key[0]} fanin={key[1]}';k=key[1]
   require(c.get('nodes')==16 and c.get('pair_factors')==8*k,f'{label}: graph size/retained-edge count mismatch')
   sizes=c.get('component_sizes',[]);require(sum(sizes)==16 and sizes==sorted(sizes),f'{label}: component census invalid')
   require(c.get('width')==c.get('triangulation_width'),f'{label}: width certificate mismatch')
   require(c.get('exact_extraction') is True,f'{label}: extracted factors mismatch')
   require(close(c.get('jt_energy'),c.get('oracle_energy')) and close(c.get('direct_rescore'),c.get('oracle_energy')),f'{label}: exact energy mismatch')
   require(len(c.get('oracle_prediction',[]))==8,f'{label}: oracle prediction width mismatch')
   target=[float(v) for v in c.get('target',[])]
   for pk,sk in [('exact_prediction','exact_accuracy'),('bp_prediction','bp_accuracy'),('linear_prediction','linear_accuracy')]:
    pred=[float(v) for v in c.get(pk,[])]
    require(len(pred)==len(target)==8,f'{label}: {pk} width mismatch')
    if len(pred)==len(target)==8:require(abs(float(c.get(sk,-1))-sum(a==b for a,b in zip(pred,target))/8)<1e-12,f'{label}: {sk} does not match predictions')
   require(c.get('no_mutation') is True,f'{label}: graph mutated')
   timing=c.get('timing_ns',{})
   require(all(isinstance(timing.get(t),int) and timing[t]>=0 for t in ('graph_construction','factor_extraction','minfill_order','junction_tree','belief_propagation')),f'{label}: timing invalid')
 require(len(cells)==120,'expected 120 cases')
 require(all(len(set(sigs))==1 for sigs in by_key.values()),'topology varies across fresh workers for a paired input/fan-in')
 summary={}
 for k in FANINS:
  group=[c for c in cells if c['fan_in']==k]
  summary[str(k)]={'cells':len(group),'median_edges':statistics.median(c['pair_factors'] for c in group) if group else None,
   'widths':sorted(set(c['width'] for c in group)),'median_components':statistics.median(len(c['component_sizes']) for c in group) if group else None,
   'median_largest_component':statistics.median(max(c['component_sizes']) for c in group) if group else None,
   'median_ms':{t:statistics.median(c['timing_ns'][t]/1e6 for c in group) for t in ('graph_construction','factor_extraction','minfill_order','junction_tree','belief_propagation')} if group else {},
   'mean_accuracy':{name:statistics.mean(c[name] for c in group) for name in ('exact_accuracy','bp_accuracy','linear_accuracy')} if group else {},
   'exact_bp_prediction_matches':sum(c['exact_prediction']==c['bp_prediction'] for c in group)}
 result={'schema':'LlmTransportTopologyFaninV1Analysis','gates_pass':not errors,'errors':errors,'summary':{'worker_count':len(runs),'case_count':len(cells),'by_fan_in':summary}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
