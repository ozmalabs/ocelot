#!/usr/bin/env python3
"""Independent integrity, query, and outcome audit for Term-derived probes."""
import hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/term_derived_probe_generation_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_derived_probe_generation_v1_20261004.json';OUT=ROOT/'evaluation/reports/term_derived_probe_generation_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import term_derived_probe_generation_v1 as m
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());assert raw['lock_sha256']==sha(LOCK) and raw['sources']==lock['sources'];assert len(raw['workers'])==120
 expected={(t,w,float(c),e) for t in m.TASKS for w in range(5) for c in m.THRESHOLDS for e in m.ENCODINGS}
 assert {(x['task'],x['worker'],x['threshold'],x['encoding']) for x in raw['workers']}==expected
 native=_native.Substrate();by_encoding={e:{'cells':0,'extract_ok':0,'selector_ok':0,'class_ok':0,'false_accepts':0,'labels':0,'candidate_probe_evaluations':0,'wide_cases':0,'wide_errors':0,'selection_ns':[]} for e in m.ENCODINGS};cells=[]
 for row,p in zip(raw['workers'],lock['panels']):
  task,c,e=row['task'],float(row['threshold']),row['encoding'];s=by_encoding[e];s['cells']+=1
  assert row['worker']==p['worker'] and row['task']==p['task'] and row['threshold']==p['threshold'] and row['encoding']==p['encoding']
  terms=p['candidate_terms'];term=terms[2]['term']['items'][1];derived=m.extract(term);assert derived==c and row['derived_bound']==c;s['extract_ok']+=1
  assert [x['ax'] for x in row['probes']]==[c-.5,c,c+.5]
  choice=row['choice'];s['candidate_probe_evaluations']+=len(terms)*len(row['probes'])
  if choice.get('ok'):
   q=choice['query'];assert q in row['probes']
   truth=(q['ax']+q['ay']==q['ex']+q['ey']) if task=='additive' else (q['ax']*q['ay']==q['ex']*q['ey'])
   assert truth is True and row['label'] is truth;s['selector_ok']+=1;s['labels']+=1;s['selection_ns'].append(row['selection_ns'])
   assert row['survivor_ids']==['exact_a','exact_b'];s['class_ok']+=1
  else:
   s['false_accepts']+=1
  rng=random.Random(m.SEED+row['worker']+int(c*100)+m.ENCODINGS.index(e)+(10000 if task=='product' else 0));errors=0
  for _ in range(m.N):
   x=rng.randint(-12,12);env=m.env(task,x)
   if task=='additive':assert env['ax']+env['ay']==env['ex']+env['ey']
   else:assert env['ax']*env['ay']==env['ex']*env['ey']
   errors+=native.evaluate(terms[2]['term'],env) is not True
   assert native.evaluate(terms[0]['term'],env) is True and native.evaluate(terms[1]['term'],env) is True
  assert errors==row['wide_bounded_errors'] and errors>0;s['wide_errors']+=errors;s['wide_cases']+=m.N
  cells.append({'task':task,'worker':row['worker'],'threshold':c,'encoding':e,'extracted_bound':derived,'query':row.get('query'),'survivors':row['survivor_ids'],'wide_bounded_errors':errors})
 for s in by_encoding.values():
  times=sorted(s.pop('selection_ns'));s['median_selection_ns']=times[len(times)//2] if times else None
  assert s['extract_ok']==s['cells']==30 and s['selector_ok']==s['class_ok']==30 and s['false_accepts']==0 and s['wide_errors']>0
 result={'schema':'TermDerivedProbeGenerationV1Analysis','passed':True,'lock_sha256':sha(LOCK),'capture_sha256':sha(RAW),'summary_by_encoding':by_encoding,'cell_count':len(cells),'cells':cells,'claim_boundary':'Authored affine comparison extractor and arithmetic task families only; no generic Term semantics, candidate invention, or natural-task capability claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':True,'summary_by_encoding':by_encoding},sort_keys=True))
if __name__=='__main__':main()
