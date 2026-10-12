#!/usr/bin/env python3
"""Independent audit of graph-native supervised orientation association."""
from __future__ import annotations
import hashlib, json, math, statistics
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/vision_eye_orientation_native_association_v1_2_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_orientation_native_association_v1_2_lock_20261005.json'
PRIOR_CAPTURE=ROOT/'evaluation/reports/vision_eye_position_heldout_orientation_v1_20261005.json'
PRIOR_ANALYSIS=ROOT/'evaluation/reports/vision_eye_position_heldout_orientation_v1_analysis_20261005.json'
PRIOR_NATIVE_CAPTURE=ROOT/'evaluation/reports/vision_eye_orientation_native_association_v1_1_20261005.json'
PRIOR_NATIVE_ANALYSIS=ROOT/'evaluation/reports/vision_eye_orientation_native_association_v1_1_analysis_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/vision_eye_orientation_native_association_v1_2.py'
SCRIPT=Path(__file__).resolve()
OUT=ROOT/'evaluation/reports/vision_eye_orientation_native_association_v1_2_analysis_20261005.json'
LABELS=('horizontal','vertical');W=16
TRAIN_SITES=tuple((y,x) for y in (3,6,9,12) for x in (3,6,9,12) if (y,x) not in ((3,3),(3,12),(12,3),(12,12)))
HELDOUT=((3,3),(3,12),(12,3),(12,12));EXPOSURES=400;STEPS=len(TRAIN_SITES)*2*EXPOSURES

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def geometry(site,label):
 y,x=site; pts={(y,x+d) for d in (-2,-1,0,1,2)} if label=='horizontal' else {(y+d,x) for d in (-2,-1,0,1,2)}
 return sorted(yy*W+xx for yy,xx in pts)
def nearest_mean(train,vector,key='acts'):
 means={lab:[sum(row[key][i] for row in train if row['label']==lab)/sum(row['label']==lab for row in train) for i in range(len(vector))] for lab in LABELS}
 scores={lab:sum((a-b)**2 for a,b in zip(vector,means[lab])) for lab in LABELS}
 return min(LABELS,key=lambda lab:(scores[lab],LABELS.index(lab)))
def reconstruct_schedule(seed):
 import random
 rows=[(site,label) for site in TRAIN_SITES for label in LABELS for _ in range(EXPOSURES)]
 random.Random(610_000+seed).shuffle(rows);h=hashlib.sha256()
 for site,label in rows:h.update(json.dumps([list(site),label],separators=(',',':')).encode())
 return rows,h.hexdigest()

def main():
 data=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text())
 prior=json.loads(PRIOR_CAPTURE.read_text());prior_analysis=json.loads(PRIOR_ANALYSIS.read_text());prior_native=json.loads(PRIOR_NATIVE_CAPTURE.read_text());prior_native_analysis=json.loads(PRIOR_NATIVE_ANALYSIS.read_text())
 if data.get('lock_sha256')!=sha(LOCK) or data.get('locked_inputs')!=lock['inputs'] or data.get('post_run_inputs')!=lock['inputs']:
  raise SystemExit('native-association capture/source lock mismatch')
 if not data.get('passed') or not prior.get('passed') or not prior_analysis.get('passed') or not prior_native.get('passed') or not prior_native_analysis.get('passed'):
  raise SystemExit('current or paired baseline capture/analysis did not pass')
 if lock['inputs']['runner_sha256']!=sha(RUNNER) or lock['inputs']['analyzer_sha256']!=sha(SCRIPT):
  raise SystemExit('runner/analyzer hashes differ from source lock')
 prior_rows={int(w['result']['seed']):w['result'] for w in prior['workers']}
 prior_native_rows={int(w['result']['seed']):w['result'] for w in prior_native['workers']}
 prior_native_analysis_rows={int(w['seed']):w for w in prior_native_analysis['per_seed']}
 prior_analysis_rows={int(w['seed']):w for w in prior_analysis['per_seed']}
 checks={'current_and_baseline_gates_pass':True,'source_lock_and_hashes_match':True,
  'six_paired_seed_ids':len(data['workers'])==6 and sorted(w['result']['seed'] for w in data['workers'])==[40,41,42,43,44,45],
  'unique_worker_processes':len({w['pid'] for w in data['workers']})==6,
  'schedule_matches_paired_unsupervised_panel':True,'geometry_and_exposure_exact':True,
  'association_counts_reconstructed_from_training_trace':True,'no_association_updates_during_probe':True,
  'one_native_prediction_per_query':True,'visual_weights_frozen':True,
  'paired_v1_decoders_reproduce_exactly':True,'training_state_matches_v1_1':True,
  'analyzer_source_stable':True}
 per_seed=[];all_preds=[];closures=[]
 for worker in sorted(data['workers'],key=lambda x:x['result']['seed']):
  r=worker['result'];seed=int(r['seed']);base=prior_rows[seed];native_base=prior_native_rows[seed]
  schedule,digest=reconstruct_schedule(seed)
  checks['schedule_matches_paired_unsupervised_panel'] &= r['schedule_sha256']==digest==base['schedule_sha256']==native_base['schedule_sha256'] and r['steps']==STEPS==base['steps']==native_base['steps']
  checks['training_state_matches_v1_1'] &= r['initial_fields']==native_base['initial_fields'] and r['learned_fields']==native_base['learned_fields'] and r['association_counts']==native_base['association_counts']
  checks['geometry_and_exposure_exact'] &= tuple(map(tuple,r['train_sites']))==TRAIN_SITES and tuple(map(tuple,r['heldout_sites']))==HELDOUT and set(r['exposures'].values())=={EXPOSURES}
  trace=r['training_trace'];checks['association_counts_reconstructed_from_training_trace'] &= len(trace)==STEPS
  for step,((site,label),entry) in enumerate(zip(schedule,trace),1):
   checks['association_counts_reconstructed_from_training_trace'] &= entry['step']==step and entry['site']==list(site) and entry['label']==label and len(entry['acts'])==8
  expected_counts={f'{lab}:{unit}':0.0 for lab in LABELS for unit in range(8)}
  for item in trace:
   for unit,act in enumerate(item['acts']):
    key=f"{item['label']}:{unit}";expected_counts[key]+=float(act)
  for key,val in expected_counts.items():
   actual=float(r['association_counts'][key])
   checks['association_counts_reconstructed_from_training_trace'] &= math.isclose(actual,val,rel_tol=1e-12,abs_tol=1e-9)
  checks['no_association_updates_during_probe'] &= r['association_counts']==r['association_counts_before_probes']==r['post_probe_association_counts']
  checks['visual_weights_frozen'] &= r['freeze_value']==1.0 and r['initial_fields']==base['initial_fields'] and r['learned_fields']==r['post_probe_fields']==base['learned_fields']
  train=[p for p in r['probes'] if p['split']=='train'];test=[p for p in r['probes'] if p['split']=='heldout']
  checks['geometry_and_exposure_exact'] &= len(train)==24 and len(test)==8 and len(r['probes'])==32
  for p in r['probes']:
   checks['one_native_prediction_per_query'] &= p['prediction_count']==1 and p['native_prediction'] in LABELS
   checks['geometry_and_exposure_exact'] &= p['mask']==geometry(tuple(p['site']),p['label']) and p['active_count']==5
  prior_decodes={(tuple(p['site']),p['label']):p for p in prior_analysis_rows[seed]['predictions']}
  prior_native_decodes={(tuple(p['site']),p['label']):p for p in prior_native_analysis_rows[seed]['predictions']}
  outcomes=Counter();preds=[]
  init_train=[{**p,'acts':[sum(f['weights'][i] for i in p['mask']) for f in r['initial_fields']]} for p in train]
  for p in test:
   prior_probe=prior_decodes[(tuple(p['site']),p['label'])]
   learned_readout=nearest_mean(train,p['acts'])
   initial_readout=nearest_mean(init_train,[sum(f['weights'][i] for i in p['mask']) for f in r['initial_fields']])
   checks['paired_v1_decoders_reproduce_exactly'] &= learned_readout==prior_probe['prediction'] and initial_readout==prior_probe['initial_prediction']
   expected={'native_association':p['native_prediction']==p['label'],
     'external_nearest_mean':learned_readout==p['label'],
     'v1_1_dot_product':prior_native_decodes[(tuple(p['site']),p['label'])]['correct']['native_association'],
     'initial_random_projection':initial_readout==p['label'],
     'centroid_or_count':p['label']=='horizontal', 'translation_aware_template':True}
   for name,val in expected.items():outcomes[name]+=int(val)
   preds.append({'site':p['site'],'label':p['label'],'native_prediction':p['native_prediction'],
      'external_nearest_mean_prediction':learned_readout,'initial_random_projection_prediction':initial_readout,
      'correct':expected,'native_winners':p['winners']})
  per_seed.append({'seed':seed,'heldout_count':len(test),'correct':dict(outcomes),'predictions':preds,
    'train_closure_ns':r['closure_ns'],'input_update_ns':r['input_update_ns'],'input_writes':r['input_writes']})
  all_preds.extend((seed,x) for x in preds);closures.append(r['closure_ns']/STEPS/1e6)
 totals=Counter()
 for _,p in all_preds:
  for k,v in p['correct'].items():totals[k]+=int(v)
 summary={k:{'correct':totals[k],'total':len(all_preds),'accuracy':totals[k]/len(all_preds)} for k in
   ('native_association','v1_1_dot_product','external_nearest_mean','initial_random_projection','centroid_or_count','translation_aware_template')}
 for name in ('native_association','v1_1_dot_product','external_nearest_mean','initial_random_projection'):
  summary[name]['class_correct']={lab:sum(p['correct'][name] for _,p in all_preds if p['label']==lab) for lab in LABELS}
 analyzer_sha=sha(SCRIPT)
 checks['analyzer_source_stable']=analyzer_sha==sha(SCRIPT)
 result={'schema':'VisionEyeOrientationNativeAssociationV1_2Analysis','run_id':'vision-eye-orientation-native-association-v1.2-analysis-20261005',
   'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'analyzer_sha256':analyzer_sha,
   'checks':checks,'passed':all(checks.values()),'summary':summary,'per_seed':per_seed,
   'median_closure_ms_per_training_step':statistics.median(closures),
   'interpretation_boundary':'Graph rules learn supervised WUnit/class association counts and select predictions entirely within native closure. Teacher labels and the reader rules are externally authored. Result covers this fixed synthetic position-heldout task only; it is not autonomous rule invention or self-improvement.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':result['passed'],'checks':checks,'summary':summary,'median_closure_ms_per_training_step':result['median_closure_ms_per_training_step'],'output':OUT.relative_to(ROOT).as_posix()}))
 return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
