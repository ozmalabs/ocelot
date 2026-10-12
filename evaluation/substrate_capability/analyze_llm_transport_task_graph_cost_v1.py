#!/usr/bin/env python3
"""Analyze separated cost profile fields and recompute prediction scores."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_cost_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_transport_task_graph_cost_v1_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_task_graph_cost_v1_analysis_20261002.json'
TOL=1e-8
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());runs=data.get('runs',[]);errors=[];cells=[]
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(data.get('lock_sha256')==sha(LOCK),'lock hash mismatch')
 require(data.get('sources')==lock.get('sources'),'capture source mismatch')
 require(data.get('post_run_sources')==lock.get('sources'),'post-run source drift')
 require(not data.get('failures'),'worker failures recorded')
 require(len(runs)==3 and len({r.get('worker_pid') for r in runs})==len(runs),'worker count/PID mismatch')
 for ri,r in enumerate(runs):
  require(r.get('input_rows')==20 and len(r.get('rows',[]))==20,f'worker {ri}: input coverage mismatch')
  require(r.get('source_lock_start')==lock.get('sources')==r.get('source_lock_end'),f'worker {ri}: source drift')
  for i in range(10):
   a,b=r['rows'][2*i:2*i+2]
   require(a.get('heldout_index')==b.get('heldout_index')==i and a.get('condition')=='learned' and b.get('condition')=='shuffled',f'worker {ri}: pairing/order mismatch')
   require(a.get('topology_signature')==b.get('topology_signature'),f'worker {ri} input {i}: condition topology mismatch')
  for c in r.get('rows',[]):
   cells.append(c);label=f'worker {ri} input {c.get("heldout_index")} {c.get("condition")}'
   require(c.get('connected') and c.get('nodes')==16 and c.get('pair_factors')==64,f'{label}: topology size/connectivity mismatch')
   require(c.get('exact_extraction') is True,f'{label}: factors differ from expected graph')
   require(c.get('width')==c.get('triangulation_width')==8,f'{label}: treewidth certificate mismatch')
   require(c.get('no_mutation') is True,f'{label}: graph changed')
   require(abs(float(c.get('exact_energy'))-float(c.get('direct_energy')))<TOL and abs(float(c.get('profile_energy'))-float(c.get('exact_energy')))<TOL,f'{label}: MAP energy mismatch')
   target=[float(x) for x in c.get('target',[])]
   for pk,ak in [('exact_prediction','exact_accuracy'),('bp_prediction','bp_accuracy')]:
    pred=[float(x) for x in c.get(pk,[])]
    require(len(pred)==len(target)==8 and abs(float(c.get(ak,-1))-sum(x==y for x,y in zip(pred,target))/8)<1e-12,f'{label}: {ak} mismatch')
   times=c.get('timing_ns',{})
   require(all(isinstance(times.get(k),int) and times[k]>=0 for k in ('substrate_init','graph_construction','factor_extraction','minfill_order','junction_tree_uninstrumented','belief_propagation')),f'{label}: invalid disjoint timings')
   require(isinstance(c.get('traced_peak_bytes'),int) and c['traced_peak_bytes']>=0,f'{label}: invalid traced allocation')
 require(len(cells)==60,'expected sixty timing cells')
 def med(name):return statistics.median(c['timing_ns'][name]/1e6 for c in cells) if cells else None
 def mean_acc(cond,key):
  vals=[float(c[key]) for c in cells if c['condition']==cond]
  return statistics.mean(vals) if vals else None
 summary={'condition_cells':len(cells),'median_ms':{k:med(k) for k in ('substrate_init','graph_construction','factor_extraction','minfill_order','junction_tree_uninstrumented','belief_propagation')},
  'median_separate_traced_jt_peak_bytes':statistics.median(c['traced_peak_bytes'] for c in cells) if cells else None,
  'mean_exact_accuracy':{k:mean_acc(k,'exact_accuracy') for k in ('learned','shuffled')},'mean_bp_accuracy':{k:mean_acc(k,'bp_accuracy') for k in ('learned','shuffled')},
  'median_process_peak_rss_kib':statistics.median(r['process_peak_rss_kib'] for r in runs) if runs else None}
 result={'schema':'LlmTransportTaskGraphCostV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
