#!/usr/bin/env python3
"""Independent acceptance analysis for GenInfer relation transfer v1."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_relation_transfer_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/substrate_geninfer_relation_transfer_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_relation_transfer_v1_analysis_20261003.json'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('cases',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('raw capture does not bind to lock')
 if data.get('source_manifest')!=lock.get('sources'):errors.append('raw source manifest differs from lock')
 if len(rows)!=len(lock.get('cases',[])):errors.append('case count mismatch')
 expected={row['id']:row for row in lock['cases']}
 if len({r.get('case',{}).get('id') for r in rows})!=len(rows):errors.append('case IDs are not unique')
 for r in rows:
  case=r['case'];name=case['id'];train=r['stages']['training'];held=r['stages']['heldout']
  if case!=expected.get(name):errors.append(f'{name}: case inputs differ from lock')
  if not r.get('source_stable'):errors.append(f'{name}: source/native drift')
  if not r.get('heldout_inserted_after_training'):errors.append(f'{name}: held-out graph added before training capture')
  if any(g['matrix']==case['matrix'] for g in r['initial_linear_generators']):
   errors.append(f'{name}: target matrix already existed before training')
  acquired=r.get('target_matrix_acquired_during_training')
  if case['enabled'] and not case['identity_control']:
   if not acquired:errors.append(f'{name}: expected target matrix not graph-minted during training')
  else:
   if acquired:errors.append(f'{name}: target matrix appeared without an enabled nonidentity acquisition')
  if case['identity_control'] and any(g['matrix']==case['matrix'] for g in r['linear_generators_after_training']):
   errors.append(f'{name}: identity control minted identity as a new linear generator')
  if case['holdout_corrupted']:
   if not acquired:errors.append(f'{name}: corrupted-holdout control lacked training-acquired generator')
   if r.get('heldout_exact_match'):errors.append(f'{name}: corrupted held-out labels falsely pass exact oracle')
  elif case['enabled'] and not case['identity_control']:
   if not train.get('status')=='recognized_transformed':errors.append(f'{name}: training did not settle through transformed recognition')
   if r.get('training_quanta_added')!=0:errors.append(f'{name}: training minted task quanta despite generator acquisition')
   if not r.get('same_training_generator_used_heldout'):
    errors.append(f'{name}: held-out transform did not name the training-acquired generator')
   if not r.get('heldout_exact_match'):errors.append(f'{name}: held-out rows failed exact target oracle')
   if not any(t.get('generator') in r['training_acquired_generator_names']
              for t in held.get('transform_receipts',[])):
    errors.append(f'{name}: held-out receipts lack generator attribution')
 summary={
  'cases':len(rows),'clean_enabled_transfer_cases':sum(r['case']['enabled'] and not r['case']['identity_control'] and not r['case']['holdout_corrupted'] for r in rows),
  'clean_enabled_matrix_acquisitions':sum(r['target_matrix_acquired_during_training'] for r in rows if r['case']['enabled'] and not r['case']['identity_control'] and not r['case']['holdout_corrupted']),
  'clean_enabled_exact_transfers':sum(bool(r['heldout_exact_match'] and r['same_training_generator_used_heldout']) for r in rows if r['case']['enabled'] and not r['case']['identity_control'] and not r['case']['holdout_corrupted']),
  'disabled_target_generator_acquisitions':sum(r['target_matrix_acquired_during_training'] for r in rows if not r['case']['enabled']),
  'identity_new_generators':sum(any(g['matrix']==r['case']['matrix'] for g in r['linear_generators_after_training']) for r in rows if r['case']['identity_control']),
  'corrupted_holdout_exact_matches':sum(bool(r['heldout_exact_match']) for r in rows if r['case']['holdout_corrupted']),
  'corrupted_holdout_same_generator_routes':sum(bool(r['same_training_generator_used_heldout']) for r in rows if r['case']['holdout_corrupted']),
  'median_training_closure_ms':statistics.median(r['stages']['training']['closure_ns'] for r in rows)/1e6,
  'median_heldout_closure_ms':statistics.median(r['stages']['heldout']['closure_ns'] for r in rows)/1e6,
  'median_training_wall_ms':statistics.median(r['training_wall_ns'] for r in rows)/1e6,
  'median_heldout_wall_ms':statistics.median(r['heldout_wall_ns'] for r in rows)/1e6,
  'matrix_transfer_rates':{name:{'n':sum(r['case']['family']==name and r['case']['enabled'] and not r['case']['holdout_corrupted'] for r in rows),
   'acquired_and_transferred':sum(r['case']['family']==name and r['case']['enabled'] and not r['case']['holdout_corrupted']
    and r['target_matrix_acquired_during_training'] and r['heldout_exact_match'] and r['same_training_generator_used_heldout'] for r in rows)} for name in lock['matrices']}}
 current_mismatches=[]
 for rel,digest in lock['sources']['source_sha256'].items():
  path=ROOT/rel
  if not path.exists() or sha(path)!=digest:current_mismatches.append(rel)
 native=Path(lock['sources']['native_path'])
 if not native.exists() or sha(native)!=lock['sources']['native_sha256']:current_mismatches.append('native_binary')
 if current_mismatches:errors.append('current sources differ from lock: '+', '.join(current_mismatches))
 report={'schema':'GenInferRelationTransferV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':not errors,'errors':errors,'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE)},'summary':summary}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':report['gates_pass'],'errors':errors,'summary':summary},sort_keys=True))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
