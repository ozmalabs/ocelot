#!/usr/bin/env python3
"""Independent candidate-bound, outcome and latency audit for GenInfer sweep."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_geninfer_bound_scaling_v1_20260926.json';LOCK=ROOT/'evaluation/substrate_capability/geninfer_bound_scaling_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_geninfer_bound_scaling_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bound_from_rows(*sets):
 vals=[]
 for rows in sets:
  for slot in (1,2):
   coords=[int(row[slot]) for row in rows];mn=min(coords);vals.append(max(abs(x-mn) for x in coords))
 return max(vals,default=0)
def main():
 p=json.loads(RAW.read_text());lk=json.loads(LOCK.read_text());runs=p['runs'];cases=[c for r in runs for c in r['cases']]
 checks={'schema_and_12_cells':p.get('schema_version')==1 and len(cases)==12,'source_lock_and_raw_hash':p['locked_inputs']==lk['locked_inputs'] and p['post_run_inputs']==p['locked_inputs'] and p['lock_sha256']==sha(LOCK),'three_fresh_stable_workers':len(runs)==3 and len({r['pid'] for r in runs})==3 and all(r['started_inputs']==p['locked_inputs']==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==p['locked_inputs']==c['source_inputs_end'] for c in cases),'all_scales_replicated':all(sum(c['scale']==s for c in cases)==3 for s in (1,2,3,4)),'data_bound_and_candidate_formula':True,'positive_exact_recovery':all(c['positive']['result']['explained'] is True and c['positive']['result']['matrix']==[1,1,0,1] and c['positive']['result']['residual_dims']==0 for c in cases),'null_refusal':all(c['predicate_null']['result']['explained'] is False for c in cases),'complete_and_timed_records':all(c['positive']['result']['checked']>0 and c['predicate_null']['result']['checked']>0 and all(c[a][t]>0 for a in ('positive','predicate_null') for t in ('wall_ns','cpu_ns')) for c in cases)}
 for c in cases:
  actual=bound_from_rows(c['positive']['base'],c['positive']['goal']);expected=(2*actual+1)**4-1
  if not (c['expected_bound']==actual==3*c['scale'] and c['expected_candidates']==expected and c['positive']['result']['checked']==expected and c['predicate_null']['result']['checked']==expected):checks['data_bound_and_candidate_formula']=False
 summary=[]
 for s in (1,2,3,4):
  xs=[c for c in cases if c['scale']==s];b=3*s;cnt=(2*b+1)**4-1
  summary.append({'scale':s,'data_derived_bound':b,'candidates_per_call':cnt,'replicates':len(xs),'positive_median_wall_ms':statistics.median(c['positive']['wall_ns'] for c in xs)/1e6,'positive_median_cpu_ms':statistics.median(c['positive']['cpu_ns'] for c in xs)/1e6,'null_median_wall_ms':statistics.median(c['predicate_null']['wall_ns'] for c in xs)/1e6,'null_median_cpu_ms':statistics.median(c['predicate_null']['cpu_ns'] for c in xs)/1e6,'positive_wall_ms_range':[min(c['positive']['wall_ns'] for c in xs)/1e6,max(c['positive']['wall_ns'] for c in xs)/1e6]})
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'case_count':len(cases),'summary_by_scale':summary,'claim_boundary':p['claim_boundary']};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()
