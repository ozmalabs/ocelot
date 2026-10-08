#!/usr/bin/env python3
"""Independent validation and sealed-corner replay for native reader selection."""
from __future__ import annotations
import hashlib,json,math,random,statistics
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/vision_eye_native_reader_selection_v1_2_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_native_reader_selection_v1_2_lock_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/vision_eye_native_reader_selection_v1_2.py'
SCRIPT=Path(__file__).resolve()
OUT=ROOT/'evaluation/reports/vision_eye_native_reader_selection_v1_2_analysis_20261005.json'
LABELS=('horizontal','vertical');KINDS=('dot_product','prototype_distance');W=16;EXPOSURES=400
FIT=((3,6),(3,9),(6,3),(6,12),(9,3),(9,12),(12,6),(12,9))
VAL=((6,6),(6,9),(9,6),(9,9),(4,7),(7,4),(7,11),(11,7));HELD=((3,3),(3,12),(12,3),(12,12))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask(site,label):
 y,x=site;points={(y,x+d) for d in (-2,-1,0,1,2)} if label=='horizontal' else {(y+d,x) for d in (-2,-1,0,1,2)}
 return sorted(yy*W+xx for yy,xx in points)
def schedule(seed):
 rows=[(site,label) for site in FIT for label in LABELS for _ in range(EXPOSURES)]
 random.Random(610_000+seed).shuffle(rows);h=hashlib.sha256()
 for site,label in rows:h.update(json.dumps([list(site),label],separators=(',',':')).encode())
 return rows,h.hexdigest()
def predict(kind,acts,counts):
 scores={}
 for label in LABELS:
  if kind=='dot_product':scores[label]=sum(acts[i]*counts[f'{label}:{i}'] for i in range(8))
  else:scores[label]=sum((acts[i]-counts[f'{label}:{i}']/3200.0)**2 for i in range(8))
 return (max(LABELS,key=lambda x:(scores[x],-LABELS.index(x))) if kind=='dot_product'
   else min(LABELS,key=lambda x:(scores[x],LABELS.index(x)))),scores
def nearest_mean(rows,acts):
 means={label:[sum(r['acts'][i] for r in rows if r['label']==label)/sum(r['label']==label for r in rows) for i in range(8)] for label in LABELS}
 return min(LABELS,key=lambda label:(sum((a-b)**2 for a,b in zip(acts,means[label])),LABELS.index(label)))
def main():
 data=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text())
 if data.get('lock_sha256')!=sha(LOCK) or data.get('locked_inputs')!=lock['inputs'] or data.get('post_run_inputs')!=lock['inputs']:
  raise SystemExit('capture/source lock mismatch')
 if not data.get('passed'):raise SystemExit('runner capture gates failed')
 if lock['inputs']['runner_sha256']!=sha(RUNNER) or lock['inputs']['analyzer_sha256']!=sha(SCRIPT):raise SystemExit('locked runner/analyzer hash mismatch')
 checks={k:True for k in ('source_lock_match','six_seed_workers','unique_worker_processes','partition_exact',
  'schedule_reconstructed','fit_associations_reconstructed','candidate_predictions_replay',
  'validation_scores_replay','native_unique_selection_or_refusal_replay','corner_labels_sealed',
  'selected_corner_predictions_replay','weights_frozen','associations_frozen')}
 all_corner=[];seed_rows=[];closure=[];seeds=sorted(int(w['result']['seed']) for w in data['workers'])
 checks['six_seed_workers']=seeds==[46,47,48,49,50,51]
 checks['unique_worker_processes']=len({w['pid'] for w in data['workers']})==6
 for worker in sorted(data['workers'],key=lambda x:x['result']['seed']):
  r=worker['result'];seed=int(r['seed']);rows,digest=schedule(seed)
  checks['partition_exact'] &= tuple(map(tuple,r['train_sites']))==FIT and tuple(map(tuple,r['validation_sites']))==VAL and tuple(map(tuple,r['heldout_sites']))==HELD
  checks['schedule_reconstructed'] &= r['steps']==len(rows)==6400 and r['schedule_sha256']==digest and set(r['exposures'].values())=={EXPOSURES}
  trace=r['training_trace'];checks['fit_associations_reconstructed'] &= len(trace)==6400
  expected={f'{label}:{i}':0.0 for label in LABELS for i in range(8)}
  for step,((site,label),entry) in enumerate(zip(rows,trace),1):
   checks['fit_associations_reconstructed'] &= entry['step']==step and entry['site']==list(site) and entry['label']==label and len(entry['acts'])==8
   for i,a in enumerate(entry['acts']):expected[f'{label}:{i}']+=float(a)
  for key,value in expected.items():checks['fit_associations_reconstructed'] &= math.isclose(value,float(r['association_counts'][key]),rel_tol=1e-12,abs_tol=1e-9)
  val=[p for p in r['probes'] if p['split']=='validation'];held=[p for p in r['probes'] if p['split']=='heldout']
  checks['partition_exact'] &= len(val)==16 and len(held)==8
  for p in r['probes']:
   checks['partition_exact'] &= p['mask']==mask(tuple(p['site']),p['label']) and p['active_count']==5
   for kind in KINDS:
    pred,scores=predict(kind,p['acts'],r['association_counts'])
    got=p['candidate_predictions'].get(kind,[])
    checks['candidate_predictions_replay'] &= got==[pred]
  val_score={kind:sum(p['candidate_predictions'][kind][0]==p['label'] for p in val) for kind in KINDS}
  checks['validation_scores_replay'] &= r['candidate_scores']==val_score
  top=max(val_score.values());winners=[k for k,v in val_score.items() if v==top]
  if len(winners)==1:
   checks['native_unique_selection_or_refusal_replay'] &= r['selected_candidate']==winners[0] and r['selection_status']=='selected'
  else:
   checks['native_unique_selection_or_refusal_replay'] &= r['selected_candidate'] is None and r['selection_status']=='tied_refusal'
  checks['corner_labels_sealed'] &= r['heldout_predictions_captured_before_label_reveal'] is True and r['heldout_labels_revealed_after_capture'] is True
  checks['corner_labels_sealed'] &= all('query_target' not in p for p in held)
  fit_rows=[{'label':x['label'],'acts':x['acts']} for x in trace]
  initial_fields=r['initial_fields'];counts=r['association_counts']
  for p in held:
   chosen=p['candidate_predictions'][r['selected_candidate']][0] if r['selected_candidate'] else None
   expected_selected_count=1 if r['selected_candidate'] else 0
   checks['selected_corner_predictions_replay'] &= p.get('selected_prediction_count')==expected_selected_count and p.get('selected_prediction')==chosen
   external=nearest_mean(fit_rows,p['acts'])
   initial_acts=[sum(f['weights'][i] for i in p['mask']) for f in initial_fields]
   initial=nearest_mean([{'label':x['label'],'acts':[sum(f['weights'][i] for i in x['mask']) for f in initial_fields]} for x in val],initial_acts)
   predrow={'seed':seed,'site':p['site'],'label':p['label'],'selected_candidate':r['selected_candidate'],
     'selection_status':r['selection_status'],'selected':p.get('selected_prediction'),'dot_product':p['candidate_predictions']['dot_product'][0],
     'prototype_distance':p['candidate_predictions']['prototype_distance'][0],
     'external_nearest_mean':external,'initial_projection':initial,
     'centroid_or_count':'horizontal','translation_aware_template':p['label']}
   predrow['correct']={k:(predrow[k]==predrow['label'] if predrow[k] is not None else False) for k in ('selected','dot_product','prototype_distance','external_nearest_mean','initial_projection','centroid_or_count','translation_aware_template')}
   all_corner.append(predrow)
  checks['weights_frozen'] &= r['freeze_value']==1.0 and r['learned_fields']==r['post_probe_fields']
  checks['associations_frozen'] &= r['association_counts']==r['post_probe_association_counts']==r['association_counts_before_probes']
  counts=Counter({k:sum(x['correct'][k] for x in all_corner if x['seed']==seed) for k in ('selected','dot_product','prototype_distance','external_nearest_mean','initial_projection')})
  seed_rows.append({'seed':seed,'validation_scores':val_score,'selected_candidate':r['selected_candidate'],
    'corner_correct':dict(counts),'candidate_score_margin':abs(val_score[KINDS[0]]-val_score[KINDS[1]]),
    'closure_ns':r['closure_ns'],'input_update_ns':r['input_update_ns']})
  closure.append(r['closure_ns']/r['steps']/1e6)
 summary={k:{'correct':sum(p['correct'][k] for p in all_corner),'total':len(all_corner),
  'accuracy':sum(p['correct'][k] for p in all_corner)/len(all_corner)} for k in ('selected','dot_product','prototype_distance','external_nearest_mean','initial_projection')}
 for_control=('centroid_or_count','translation_aware_template')
 summary.update({k:{'correct':sum(p['correct'][k] for p in all_corner),'total':len(all_corner),
  'accuracy':sum(p['correct'][k] for p in all_corner)/len(all_corner)} for k in for_control})
 result={'schema':'VisionEyeNativeReaderSelectionV1_2Analysis','run_id':'vision-eye-native-reader-selection-v1.2-analysis-20261005',
  'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(SCRIPT),
  'checks':checks,'passed':all(checks.values()),'summary':summary,'per_seed':seed_rows,
  'predictions':all_corner,'median_closure_ms_per_fit_training_step':statistics.median(closure),
  'selection_coverage':sum(p['selected_candidate'] is not None for p in seed_rows),'selection_abstentions':sum(p['selected_candidate'] is None for p in seed_rows),
  'interpretation_boundary':'Native ArgminUnique selects between two externally supplied supervised readers using disjoint labeled validation positions, or abstains on a score tie. Candidate rules, task, and labels are external. The corner labels are absent during selection and captured prediction. Accuracy counts abstentions as incorrect; coverage is reported separately. This is bounded internal model selection, not autonomous candidate invention or general self-improvement.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':result['passed'],'checks':checks,'summary':summary,'median_closure_ms_per_fit_training_step':result['median_closure_ms_per_fit_training_step'],'output':OUT.relative_to(ROOT).as_posix()}))
 return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
