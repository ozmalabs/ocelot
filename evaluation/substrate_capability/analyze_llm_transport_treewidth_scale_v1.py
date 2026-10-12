#!/usr/bin/env python3
"""Independent checks and per-width summaries for transport scaling."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_treewidth_scale_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_transport_treewidth_scale_v1_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_treewidth_scale_v1_analysis_20261002.json'
TOL=1e-8;WIDTHS=(1,2,4,6,8,10)
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
 for ri,r in enumerate(runs):
  require(r.get('source_lock_start')==lock.get('sources')==r.get('source_lock_end'),f'worker {ri}: source drift')
  rows=r.get('rows',[]);require(len(rows)==60 and r.get('input_cells')==60,f'worker {ri}: grid size mismatch')
  require({(c.get('heldout_index'),c.get('k')) for c in rows}=={(i,k) for i in range(10) for k in WIDTHS},f'worker {ri}: incomplete or duplicate grid')
  for c in rows:
   cells.append(c);label=f'worker {ri} input {c.get("heldout_index")} k={c.get("k")}';k=c.get('k')
   require(k in WIDTHS and c.get('nodes')==2*k,f'{label}: graph size mismatch')
   require(c.get('connected') is True,f'{label}: disconnected')
   require(c.get('width')==c.get('triangulation_width'),f'{label}: width certificate mismatch')
   require(c.get('exact_extraction') is True,f'{label}: expected factors not extracted')
   require(close(c.get('jt_energy'),c.get('oracle_energy')) and close(c.get('direct_rescore'),c.get('oracle_energy')),f'{label}: JT/oracle/rescore mismatch')
   require(c.get('oracle_source_assignments')==3**k,f'{label}: exhaustive source assignment coverage mismatch')
   target=[float(x) for x in c.get('target',[])];ep=[float(x) for x in c.get('exact_prediction',[])];bp=[float(x) for x in c.get('bp_prediction',[])]
   require(len(target)==len(ep)==len(bp)==k,f'{label}: prediction dimensions mismatch')
   if len(target)==len(ep)==len(bp)==k:
    require(abs(float(c['exact_accuracy'])-sum(a==b for a,b in zip(ep,target))/k)<1e-12,f'{label}: exact accuracy mismatch')
    require(abs(float(c['bp_accuracy'])-sum(a==b for a,b in zip(bp,target))/k)<1e-12,f'{label}: BP accuracy mismatch')
   require(c.get('no_mutation') is True,f'{label}: graph mutated')
   times=c.get('timing_ns',{})
   require(all(isinstance(times.get(t),int) and times[t]>=0 for t in ('substrate_init','graph_construction','factor_extraction','minfill_order','junction_tree','belief_propagation')),f'{label}: timing field invalid')
 require(len(cells)==180,'expected 180 cells')
 by_k={}
 for k in WIDTHS:
  group=[c for c in cells if c['k']==k];by_k[str(k)]={'cells':len(group),'nodes':2*k,'median_width':statistics.median(c['width'] for c in group) if group else None,
   'median_ms':{key:statistics.median(c['timing_ns'][key]/1e6 for c in group) for key in ('graph_construction','factor_extraction','minfill_order','junction_tree','belief_propagation')} if group else {},
   'mean_exact_accuracy':statistics.mean(c['exact_accuracy'] for c in group) if group else None,'mean_bp_accuracy':statistics.mean(c['bp_accuracy'] for c in group) if group else None,
   'oracle_assignments':3**k,'max_abs_energy_error':max((abs(float(c['jt_energy'])-float(c['oracle_energy'])) for c in group),default=None)}
 result={'schema':'LlmTransportTreewidthScaleV1Analysis','gates_pass':not errors,'errors':errors,'summary':{'workers':len(runs),'cell_count':len(cells),'by_mode_count':by_k}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
