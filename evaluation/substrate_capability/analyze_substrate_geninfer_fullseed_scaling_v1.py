#!/usr/bin/env python3
"""Independent gate and descriptive scaling analysis for full-seed GenInfer."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/substrate_geninfer_fullseed_scaling_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_fullseed_scaling_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def med(rows,path):return statistics.median(rows)
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('cases',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('capture does not bind to source lock')
 if data.get('source_manifest')!=lock.get('sources'):errors.append('source manifest differs from lock')
 expected={c['id']:c for c in lock['cases']};actual={r.get('case',{}).get('id'):r for r in rows}
 if len(rows)!=84 or len(actual)!=84 or set(actual)!=set(expected):errors.append('case count or identity mismatch')
 pids={r.get('pid') for r in rows}
 if len(pids)!=len(rows):errors.append('cases did not run in distinct processes')
 for ident,r in actual.items():
  c=expected[ident];kind=c['kind'];n=c['n'];b=c['bound'];m=[b-1,1,1,1]
  if r.get('case')!=c:errors.append(f'{ident}: locked case mismatch')
  if not r.get('source_stable'):errors.append(f'{ident}: source/native drift')
  if r.get('expected_bound')!=b or r.get('expected_candidate_checks_per_part')!=(2*b+1)**4-1:
   errors.append(f'{ident}: candidate work formula mismatch')
  if r.get('matrix')!=m:errors.append(f'{ident}: matrix mismatch')
  for stage in ('train','heldout','corrupted_heldout'):
   x=r.get(stage,{})
   if any(not isinstance(x.get(k),int) or x[k]<0 for k in ('closure_work','closure_wall_ns','closure_cpu_ns','hwm_before_kib','hwm_after_kib','hwm_delta_kib','nodes_before','nodes_after','edges_after')):
    errors.append(f'{ident}: invalid {stage} resource/graph fields')
  if kind=='positive':
   if any(g.get('matrix')==m for g in r.get('initial_linear_generators',[])):errors.append(f'{ident}: target matrix existed initially')
   if not r.get('target_acquired_during_training'):errors.append(f'{ident}: training failed to acquire target')
   if not r.get('same_training_generator_on_heldout'):errors.append(f'{ident}: heldout lacks training-generator attribution')
   if not r.get('training_oracle_exact_match'):errors.append(f'{ident}: training oracle mismatch')
   if not r.get('heldout_exact_match'):errors.append(f'{ident}: heldout oracle mismatch')
   if r.get('corrupted_heldout_exact_match'):errors.append(f'{ident}: corrupted heldout passed exact oracle')
  elif kind=='disabled' and r.get('target_acquired_during_training'):
   errors.append(f'{ident}: disabled condition acquired target')
 current=[]
 for rel,dig in lock['sources']['source_sha256'].items():
  path=ROOT/rel
  if not path.exists() or sha(path)!=dig:current.append(rel)
 native=Path(lock['sources']['native_path'])
 if not native.exists() or sha(native)!=lock['sources']['native_sha256']:current.append('native_binary')
 if current:errors.append('current files differ from lock: '+', '.join(current))
 positives=[r for r in rows if r['case']['kind']=='positive']
 controls=[r for r in rows if r['case']['kind']=='predicate_corrupt']
 by_n={}
 for n in lock['relation_counts']:
  cell=[r for r in positives if r['case']['n']==n]
  by_n[str(n)]={'runs':len(cell),'median_train_wall_ms':statistics.median(r['train']['closure_wall_ns'] for r in cell)/1e6,
   'median_train_cpu_ms':statistics.median(r['train']['closure_cpu_ns'] for r in cell)/1e6,
   'median_train_hwm_delta_kib':statistics.median(r['train']['hwm_delta_kib'] for r in cell),
   'median_train_closure_work':statistics.median(r['train']['closure_work'] for r in cell),
   'median_train_nodes_after':statistics.median(r['train']['nodes_after'] for r in cell)}
 by_b={}
 for b in lock['bounds']:
  cell=[r for r in positives if r['case']['bound']==b]
  by_b[str(b)]={'candidate_checks_per_part':(2*b+1)**4-1,'runs':len(cell),
   'median_train_wall_ms':statistics.median(r['train']['closure_wall_ns'] for r in cell)/1e6,
   'median_train_cpu_ms':statistics.median(r['train']['closure_cpu_ns'] for r in cell)/1e6,
   'median_train_hwm_delta_kib':statistics.median(r['train']['hwm_delta_kib'] for r in cell),
   'median_train_closure_work':statistics.median(r['train']['closure_work'] for r in cell)}
 summary={'case_count':len(rows),'positive_cases':len(positives),'positive_acquisition_and_transfer':sum(bool(r['target_acquired_during_training'] and r['same_training_generator_on_heldout'] and r['heldout_exact_match']) for r in positives),
  'disabled_target_acquisitions':sum(bool(r['target_acquired_during_training']) for r in rows if r['case']['kind']=='disabled'),
  'predicate_corrupt_cases':len(controls),'predicate_corrupt_target_acquisitions':sum(bool(r['target_acquired_during_training']) for r in controls),
  'predicate_corrupt_recognized_transformed':sum(r['train']['status']=='recognized_transformed' for r in controls),
  'predicate_corrupt_exact_training_matches':sum(bool(r['training_oracle_exact_match']) for r in controls),
  'corrupted_heldout_recognized_transformed':sum(r['corrupted_heldout']['status']=='recognized_transformed' for r in positives),
  'corrupted_heldout_exact_matches':sum(bool(r['corrupted_heldout_exact_match']) for r in positives),
  'median_positive_train_wall_ms':statistics.median(r['train']['closure_wall_ns'] for r in positives)/1e6,
  'median_positive_heldout_wall_ms':statistics.median(r['heldout']['closure_wall_ns'] for r in positives)/1e6,
  'by_relation_count':by_n,'by_bound':by_b}
 report={'schema':'GenInferFullSeedScalingV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':not errors,'errors':errors,'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE)},'summary':summary}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':report['gates_pass'],'errors':errors,'summary':summary},sort_keys=True))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
