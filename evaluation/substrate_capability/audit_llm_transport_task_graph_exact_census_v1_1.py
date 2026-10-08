#!/usr/bin/env python3
"""Post-capture audit: recompute reported accuracies from saved predictions."""
from __future__ import annotations
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_20261002.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_task_graph_exact_census_v1_1_lock_20261002.json'
ANALYSIS=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_analysis_20261002.json'
OUT=ROOT/'evaluation/reports/llm_transport_task_graph_exact_census_v1_1_posthoc_audit_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 data=json.loads(CAPTURE.read_text());locked=json.loads(LOCK.read_text());analysis=json.loads(ANALYSIS.read_text());errors=[];cells=[]
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(data.get('lock_sha256')==sha(LOCK),'lock hash mismatch')
 require(data.get('sources')==locked.get('sources'),'source set differs from lock')
 require(data.get('post_run_sources')==locked.get('sources'),'source drift after run')
 require(analysis.get('gates_pass') is True,'registered analyzer did not pass')
 for ri,run in enumerate(data.get('runs',[])):
  require([r.get('heldout_index') for r in run.get('rows',[])]==list(range(10)),f'worker {ri}: heldout rows missing/reordered')
  for row in run.get('rows',[]):
   target=[float(x) for x in row.get('target_signs',[])]
   require(len(target)==8 and set(target)<={-1.0,1.0},f'worker {ri} input {row.get("heldout_index")}: invalid target')
   for name,c in row.get('conditions',{}).items():
    for pred_key,score_key in [('exact_prediction','exact_accuracy'),('bp_prediction','bp_accuracy'),('linear_prediction','linear_accuracy')]:
     pred=[float(x) for x in c.get(pred_key,[])]
     require(len(pred)==8 and len(target)==8,f'worker {ri} {name}: invalid prediction size')
     if len(pred)==len(target)==8:
      computed=sum(a==b for a,b in zip(pred,target))/8
      require(abs(float(c.get(score_key,-1))-computed)<1e-12,f'worker {ri} {name}: {score_key} not derived from saved predictions')
    cells.append((name,c))
 def mean(name,key):
  vals=[float(c[key]) for n,c in cells if n==name]
  return statistics.mean(vals) if vals else None
 metrics={'mean_exact_learned_accuracy':mean('learned','exact_accuracy'),'mean_exact_shuffled_accuracy':mean('shuffled','exact_accuracy'),
  'mean_bp_learned_accuracy':mean('learned','bp_accuracy'),'mean_bp_shuffled_accuracy':mean('shuffled','bp_accuracy'),
  'mean_linear_learned_accuracy':mean('learned','linear_accuracy'),'mean_linear_shuffled_accuracy':mean('shuffled','linear_accuracy')}
 for key,value in metrics.items():
  require(value is not None and abs(value-float(analysis['summary'][key]))<1e-12,f'{key}: posthoc summary mismatch')
 result={'schema':'LlmTransportTaskGraphExactCensusV1_1PosthocAudit','gates_pass':not errors,'errors':errors,
  'capture_sha256':sha(CAPTURE),'metrics_recomputed_from_predictions':metrics,'condition_cells':len(cells),
  'scope':'post-capture arithmetic audit of prediction/target agreement; does not replace source-locked experiment gates'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
