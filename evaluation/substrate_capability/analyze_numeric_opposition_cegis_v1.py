#!/usr/bin/env python3
"""Replay integrity and independently rescore the CEGIS capture."""
import hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_v1_lock_20261003.json'; CAP=ROOT/'evaluation/reports/numeric_opposition_cegis_v1_20261003.json'; OUT=ROOT/'evaluation/reports/numeric_opposition_cegis_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r):return r[0]==-r[2] and r[1]==-r[3]
def main():
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 lock=json.loads(LOCK.read_text()); cap=json.loads(CAP.read_text()); errors=[]; native=_native.Substrate(); panels=lock['panels']; rows=cap.get('workers',[])
 if cap.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 if cap.get('sources')!=lock.get('sources'):errors.append('source map mismatch')
 if len(rows)!=len(panels):errors.append('worker count mismatch')
 for i,row in enumerate(rows):
  if i>=len(panels):break
  panel=panels[i]
  if row.get('initial_training')!=panel['training'] or row.get('query_pool')!=panel['query_pool']:errors.append(f'worker {i}: panel mismatch')
  revealed=list(panel['training']); used=[]
  for turn,rr in enumerate(row.get('rounds',[])):
   if rr.get('turn')!=turn or rr.get('training')!=revealed:errors.append(f'worker {i} turn {turn}: revealed-example history mismatch')
   hyps=rr.get('hypotheses',[])
   for h in hyps:
    for ex in revealed:
     try:p=native.evaluate(h['term'],env(ex['row']))
     except Exception as e:errors.append(f'worker {i}: candidate evaluation error {e}');continue
     # domains.generator._matches_target deliberately treats numeric 0/1 and
     # Boolean labels as equivalent for synthesis fitting.
     if bool(p)!=bool(ex['label']):errors.append(f'worker {i}: candidate fails revealed example')
   q=rr.get('query')
   if q is not None:
    if q not in panel['query_pool'] or q in used or q in [x['row'] for x in revealed]:errors.append(f'worker {i}: invalid/duplicate query')
    if rr.get('label')!=int(truth(q)):errors.append(f'worker {i}: oracle label mismatch')
    avail=[x for x in panel['query_pool'] if x not in used and x not in [z['row'] for z in revealed]]
    expected=select_discriminating_input(lambda t,e:native.evaluate(t,e),hyps,[env(x) for x in avail],[])
    if not expected.get('ok') or [int(expected['query'][k]) for k in ('ax','ay','ex','ey')]!=q:errors.append(f'worker {i}: active query choice mismatch')
    used.append(q);revealed.append({'row':q,'label':rr['label']})
  final=row.get('final_hypotheses',[]); grid=list(itertools.product(lock['heldout_grid'],repeat=4)); scored=[]
  for h in final:
   tp=fp=fn=tn=0
   for x in grid:
    y=truth(x);p=bool(native.evaluate(h['term'],env(x)))
    if y and p:tp+=1
    elif y:fn+=1
    elif p:fp+=1
    else:tn+=1
   scored.append({'hypothesis':h['id'],'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':fp==0 and fn==0})
  if scored!=row.get('heldout_scores'):errors.append(f'worker {i}: heldout score mismatch')
  if row.get('oracle_calls')!=len(used):errors.append(f'worker {i}: call count mismatch')
 summary={'workers':len(rows),'status_counts':{s:sum(r.get('status')==s for r in rows) for s in sorted({r.get('status') for r in rows})},'total_oracle_calls':sum(r.get('oracle_calls',0) for r in rows),'exact_singleton_workers':sum(r.get('status')=='singleton' and len(r.get('heldout_scores',[]))==1 and r['heldout_scores'][0]['exact'] for r in rows),'false_singleton_workers':sum(r.get('status')=='singleton' and not (len(r.get('heldout_scores',[]))==1 and r['heldout_scores'][0]['exact']) for r in rows),'mean_synthesis_rounds':sum(len(r.get('rounds',[])) for r in rows)/max(1,len(rows))}
 result={'schema':'NumericOppositionCEGISV1Analysis','integrity_pass':not errors,'errors':errors,'summary':summary,'worker_outcomes':[{'worker':r.get('worker'),'status':r.get('status'),'calls':r.get('oracle_calls'),'candidate_counts':[len(x.get('hypotheses',[])) for x in r.get('rounds',[])],'exact_survivors':sum(x.get('exact',False) for x in r.get('heldout_scores',[]))} for r in rows],'hashes':{'lock':sha(LOCK),'capture':sha(CAP),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
