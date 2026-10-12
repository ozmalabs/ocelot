#!/usr/bin/env python3
"""Independent acceptance checks and summaries for transport exact inference."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
ANALYSIS=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_analysis_20261002.json'
TOL=1e-8
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b))<TOL
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());runs=data.get('runs',[]);errors=[]
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(data.get('lock_sha256')==sha(LOCK),'lock hash mismatch')
 require(data.get('sources')==lock.get('sources'),'capture/lock source mismatch')
 require(data.get('post_run_sources')==lock.get('sources'),'post-run source drift')
 require(not data.get('failures'),'worker failures recorded')
 require(len(runs)==3,'expected three workers')
 require(len({r.get('worker_pid') for r in runs})==len(runs),'worker PIDs are not distinct')
 cells=[]
 for ri,r in enumerate(runs):
  require(r.get('input_count')==10 and len(r.get('rows',[]))==10,f'worker {ri}: input coverage mismatch')
  require(r.get('source_lock_start')==lock.get('sources')==r.get('source_lock_end'),f'worker {ri}: source drift')
  for row in r.get('rows',[]):
   i=row.get('heldout_index');conds=row.get('conditions',{})
   require(isinstance(i,int) and 0<=i<10,f'worker {ri}: invalid heldout index')
   require(set(conds)=={'learned','shuffled'},f'worker {ri} input {i}: condition mismatch')
   if set(conds)!={'learned','shuffled'}:continue
   target=row.get('target_signs',[]);require(len(target)==8,f'worker {ri} input {i}: target width mismatch')
   for name,c in conds.items():
    cells.append((ri,i,name,c))
    require(c.get('components_connected') is True,f'worker {ri} input {i} {name}: graph disconnected')
    require(c.get('nodes')==16 and c.get('pair_factors')==64,f'worker {ri} input {i} {name}: graph size mismatch')
    require(c.get('exact_extraction') is True,f'worker {ri} input {i} {name}: factor extraction mismatch')
    require(c.get('width')==c.get('triangulation_width'),f'worker {ri} input {i} {name}: width certificate mismatch')
    for key in ('jt_energy','direct_rescore'):
     require(close(c.get(key),c.get('oracle_energy')),f'worker {ri} input {i} {name}: {key} differs from independent VE')
    require(c.get('no_mutation') is True,f'worker {ri} input {i} {name}: input state mutated')
    for key in ('exact_prediction','bp_prediction','linear_prediction'):
     require(len(c.get(key,[]))==8 and all(float(v) in (-1.0,0.0,1.0) for v in c.get(key,[])),f'worker {ri} input {i} {name}: invalid {key}')
    require(isinstance(c.get('exact_accuracy'),(int,float)) and 0<=c['exact_accuracy']<=1,f'worker {ri} input {i} {name}: invalid exact accuracy')
    require(isinstance(c.get('bp_accuracy'),(int,float)) and 0<=c['bp_accuracy']<=1,f'worker {ri} input {i} {name}: invalid BP accuracy')
    require(isinstance(c.get('linear_accuracy'),(int,float)) and 0<=c['linear_accuracy']<=1,f'worker {ri} input {i} {name}: invalid linear accuracy')
 require(len(cells)==60,'expected sixty condition cells')
 def mean_acc(name,field):
  vals=[float(c[field]) for _,_,n,c in cells if n==name]
  return statistics.mean(vals) if vals else None
 summary={'workers':len(runs),'heldout_inputs_per_worker':10,'condition_cells':len(cells),
  'mean_exact_learned_accuracy':mean_acc('learned','exact_accuracy'),'mean_exact_shuffled_accuracy':mean_acc('shuffled','exact_accuracy'),
  'mean_bp_learned_accuracy':mean_acc('learned','bp_accuracy'),'mean_bp_shuffled_accuracy':mean_acc('shuffled','bp_accuracy'),
  'mean_linear_learned_accuracy':mean_acc('learned','linear_accuracy'),'mean_linear_shuffled_accuracy':mean_acc('shuffled','linear_accuracy'),
  'widths':sorted(set(c.get('width') for _,_,_,c in cells)),'median_jt_ms':statistics.median(c['timing_ns']['junction_tree']/1e6 for _,_,_,c in cells) if cells else None,
  'median_oracle_ms':statistics.median(c['timing_ns']['oracle']/1e6 for _,_,_,c in cells) if cells else None,
  'oracle_max_abs_energy_delta':max((abs(float(c['jt_energy'])-float(c['oracle_energy'])) for _,_,_,c in cells),default=None)}
 out={'schema':'LlmTransportTaskGraphExactCensusV1_1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
