#!/usr/bin/env python3
"""Replay deduplicated policy outcomes and independently rescore Terms."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runners/dsl/python'))
LOCK=ROOT/'evaluation/substrate_capability/term_deduplication_class_return_v1_lock_20261004.json'
RAW=ROOT/'evaluation/reports/term_deduplication_class_return_v1_20261004.json'
UPLOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
UPRAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
UPAN=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
OUT=ROOT/'evaluation/reports/term_deduplication_class_return_v1_analysis_20261004.json'
KEYS=('ax','ay','ex','ey');VALS=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(t,r):
 a,b,c,d=r
 return {'additive':a+b==c+d,'product':a*b==c*d,'ordering':a<c,'opposition':a==-c,'inequality':a!=c}[t]
def main():
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());upl=json.loads(UPLOCK.read_text());upr=json.loads(UPRAW.read_text());upa=json.loads(UPAN.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('dedup capture provenance mismatch')
 if lock.get('upstream_lock_sha256')!=sha(UPLOCK) or lock.get('upstream_capture_sha256')!=sha(UPRAW):errors.append('upstream input hash mismatch')
 if not upa.get('passed'):errors.append('upstream policy analysis not passed')
 panels={(p['task'],p['worker']):p for p in upl['panels']};base={(r['task'],r['worker']):r for r in upa['rows']};original={(w['task'],w['worker']):w for w in upr['workers']}
 native=_native.Substrate();rows=[];all_removed=all_initial=all_unique=0;taskdups={}
 for w in raw.get('workers',[]):
  key=(w.get('task'),w.get('worker'));p=panels.get(key)
  if p is None:errors.append(f'unlocked panel {key}');continue
  seen=set();expected=[]
  for h in p['initial_hypotheses']:
   k=canon(h['term'])
   if k not in seen:seen.add(k);expected.append(h)
  if [h['id'] for h in expected]!=[h['id'] for h in w.get('unique_hypotheses',[])]:errors.append(f'dedup set mismatch {key}')
  result=w.get('result',{});alive={h['id']:h for h in expected}
  for step in result.get('steps',[]):
   row=tuple(map(float,step.get('row',[])));label=truth(key[0],row)
   if step.get('label') is not label:errors.append(f'oracle label mismatch {key}')
   for hid,h in list(alive.items()):
    try:value=native.evaluate(h['term'],env(row))
    except Exception:value=None
    if type(value) is not bool or value is not label:alive.pop(hid)
  survivors={h['id']:h for h in result.get('survivors',[])}
  if set(alive)!=set(survivors):errors.append(f'survivor replay mismatch {key}')
  exact_flags={}
  for hid,h in survivors.items():
   bad=False
   for r in itertools.product(VALS,repeat=4):
    if r==(0.,0.,0.,0.):continue
    try:v=native.evaluate(h['term'],env(r))
    except Exception:bad=True;break
    if type(v) is not bool or v is not truth(key[0],r):bad=True;break
   exact_flags[hid]=not bad
   if h.get('heldout',{}).get('exact')!=(not bad):errors.append(f'embedded score mismatch {key}:{hid}')
  if result.get('decision')=='behavior_class':
   class_terms={canon(survivors[h]['term']) for h in survivors}
   if not result.get('coverage',{}).get('adequate') or len(class_terms)!=1:errors.append(f'unsafe or non-single class {key}')
  base_row=base.get(key,{});orig=original.get(key,{}).get('result',{})
  n0=len(p['initial_hypotheses']);nu=len(expected);removed=n0-nu;all_initial+=n0;all_unique+=nu;all_removed+=removed;taskdups[key[0]]=taskdups.get(key[0],0)+removed
  rows.append({'task':key[0],'worker':key[1],'initial_candidates':n0,'unique_terms':nu,'duplicates_removed':removed,
   'original_decision':orig.get('decision'),'deduplicated_decision':result.get('decision'),'original_labels':orig.get('calls'),
   'deduplicated_labels':result.get('calls'),'label_delta':result.get('calls',0)-orig.get('calls',0),
   'expansions':len(result.get('expansions',[])),'returned_survivors':len(survivors),
   'all_survivors_exact':bool(survivors) and all(exact_flags.values()),'base_analyzed_decision':base_row.get('decision')})
 summary={'panels':len(rows),'initial_candidate_rows':all_initial,'unique_term_rows':all_unique,'duplicate_rows_removed':all_removed,
  'duplicate_fraction':all_removed/all_initial if all_initial else None,'per_task_duplicates_removed':taskdups,
  'original_class_return_panels':sum(r['original_decision']=='behavior_class' for r in rows),
  'deduplicated_class_return_panels':sum(r['deduplicated_decision']=='behavior_class' for r in rows),
  'deduplicated_exact_term_panels':sum(r['deduplicated_decision']=='exact_term' for r in rows),
  'deduplicated_false_or_mixed_outputs':sum(not r['all_survivors_exact'] for r in rows),
  'median_original_labels':statistics.median(r['original_labels'] for r in rows),
  'median_deduplicated_labels':statistics.median(r['deduplicated_labels'] for r in rows),
  'median_label_delta':statistics.median(r['label_delta'] for r in rows)}
 if len(rows)!=25:errors.append('expected 25 panels')
 result={'schema':'TermDeduplicationClassReturnV1Analysis','passed':not errors,'errors':errors,'capture_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'summary':summary,'rows':rows,'limits':['five authored numeric relations','exact canonical Term JSON deduplication only','fixed upstream candidate pools and finite holdout','does not measure candidate discovery on natural tasks']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':not errors,'errors':errors,'summary':summary},sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
