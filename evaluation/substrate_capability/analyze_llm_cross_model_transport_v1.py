#!/usr/bin/env python3
"""Independent source, coverage, exactness, and per-model summaries."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_cross_model_transport_v1_1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_cross_model_transport_v1_1_20261002.json'
OUT=ROOT/'evaluation/reports/llm_cross_model_transport_v1_1_analysis_20261002.json'
HOPS=((10,11),(11,12),(12,13),(13,14));FANINS=(1,2,4,8);TOL=1e-8

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def close(a,b):return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b))<TOL
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());runs=data.get('runs',[]);errors=[];by={}
 def req(ok,msg):
  if not ok:errors.append(msg)
 req(data.get('lock_sha256')==sha(LOCK),'capture lock hash mismatch')
 req(data.get('sources')==lock['sources']==data.get('post_run_sources'),'source lock or post-run drift')
 req(not data.get('failures'),'capture reports worker failures')
 req(len(runs)==6 and len({r.get('worker_pid') for r in runs})==6,'six independent workers required')
 rows_all=[]
 for model in ('qwen3_0_6b','qwen3_1_7b'):
  mruns=[r for r in runs if r.get('model')==model];req(len(mruns)==3,f'{model}: worker count')
  sigs={};cells=[]
  for wi,r in enumerate(mruns):
   req(r.get('cells')==160 and len(r.get('rows',[]))==160,f'{model} worker {wi}: row count')
   req(r.get('source_lock_start')==r.get('source_lock_end'),f'{model} worker {wi}: nested source lock drift')
   actual={(c.get('source_layer'),c.get('target_layer'),c.get('heldout_index'),c.get('fan_in')) for c in r.get('rows',[])}
   expected={(a,b,i,k) for a,b in HOPS for i in range(10) for k in FANINS}
   req(actual==expected,f'{model} worker {wi}: incomplete/duplicate grid')
   for c in r.get('rows',[]):
    cells.append(c);rows_all.append(c);key=(c['source_layer'],c['target_layer'],c['heldout_index'],c['fan_in']);sigs.setdefault(key,[]).append(c['topology_signature']);label=f'{model} worker {wi} case {key}'
    req(c['nodes']==16 and c['edges']==8*c['fan_in'] and c['pair_factors']==8*c['fan_in'],label+': graph accounting')
    req(sum(c['component_sizes'])==16 and c['component_sizes']==sorted(c['component_sizes']),label+': components')
    req(c['exact_extraction'] is True,label+': factor extraction')
    req(c['width']==c['triangulation_width'],label+': width certificate')
    req(close(c['jt_energy'],c['oracle_energy']) and close(c['direct_rescore'],c['oracle_energy']),label+': exact oracle/rescore')
    req(c['no_mutation'] is True,label+': mutation')
    for p,a in [('exact_prediction','exact_accuracy'),('bp_prediction','bp_accuracy'),('linear_prediction','linear_accuracy')]:
     pred=c[p];target=c['target'];req(len(pred)==len(target)==8,label+f': {p} dimension')
     if len(pred)==len(target)==8:req(abs(c[a]-sum(float(x)==float(y) for x,y in zip(pred,target))/8)<1e-12,label+f': {a} arithmetic')
   req(all(len(set(v))==1 for v in sigs.values()),f'{model}: topology instability across workers')
  req(len(cells)==480,f'{model}: expected 480 cases')
  summary={}
  for hop in HOPS:
   summary[f'{hop[0]}->{hop[1]}']={}
   for k in FANINS:
    g=[c for c in cells if (c['source_layer'],c['target_layer'])==hop and c['fan_in']==k]
    summary[f'{hop[0]}->{hop[1]}'][str(k)]={'cells':len(g),'widths':sorted({c['width'] for c in g}),'median_jt_ms':statistics.median(c['timing_ns']['junction_tree']/1e6 for c in g),'median_bp_ms':statistics.median(c['timing_ns']['belief_propagation']/1e6 for c in g),'mean_accuracy':{a:statistics.mean(c[a] for c in g) for a in ('exact_accuracy','bp_accuracy','linear_accuracy')},'exact_bp_match_rate':statistics.mean(c['exact_prediction']==c['bp_prediction'] for c in g)}
  by[model]={'workers':len(mruns),'cases':len(cells),'hops':summary}
 req(len(rows_all)==960,'expected 960 total graph rows')
 out={'schema':'LlmCrossModelTransportV1Analysis','gates_pass':not errors,'errors':errors,'summary':by,'cross_model_comparison':{'pooled':False,'interpretation':'two independently fit models on one synthetic text corpus; no cross-basis transfer or task utility claim'}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
