#!/usr/bin/env python3
"""Independent policy-history and holdout audit for CEGIS adequacy study."""
import hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_adequacy_v1_lock_20261003.json';CAP=ROOT/'evaluation/reports/numeric_opposition_cegis_adequacy_v1_20261003.json';OUT=ROOT/'evaluation/reports/numeric_opposition_cegis_adequacy_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r,t):
 x=r[0]==-r[2];y=r[1]==-r[3]
 return (x and y) if t=='opposition' else (x!=y)
def main():
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 l=json.loads(LOCK.read_text());c=json.loads(CAP.read_text());n=_native.Substrate();err=[];rows=c.get('workers',[])
 if c.get('lock_sha256')!=sha(LOCK):err.append('lock hash mismatch')
 if c.get('sources')!=l.get('sources'):err.append('source map mismatch')
 if len(rows)!=len(l['panels']):err.append('worker count mismatch')
 for i,w in enumerate(rows):
  p=l['panels'][i];task=w.get('task');train=list(p['training']);used=[]
  if task!=p['task'] or w.get('initial_training')!=train or w.get('query_pool')!=p['query_pool']:err.append(f'{i}: panel mismatch')
  for turn,r in enumerate(w.get('rounds',[])):
   if r.get('turn')!=turn or r.get('training')!=train:err.append(f'{i}: history mismatch at {turn}')
   hs=r.get('hypotheses',[])
   for h in hs:
    for e in train:
     try:pred=n.evaluate(h['term'],env(e['row']))
     except Exception as ex:err.append(f'{i}: candidate eval error {ex}');continue
     if bool(pred)!=bool(e['label']):err.append(f'{i}: candidate violates revealed label')
   q=r.get('query')
   if q is not None:
    if q not in p['query_pool'] or q in used or q in [x['row'] for x in train]:err.append(f'{i}: invalid query')
    if r.get('label')!=int(truth(q,task)):err.append(f'{i}: oracle label error')
    avail=[x for x in p['query_pool'] if x not in used and x not in [z['row'] for z in train]]
    exp=select_discriminating_input(lambda term,e:n.evaluate(term,e),hs,[env(x) for x in avail],[])
    if not exp.get('ok') or [int(exp['query'][k]) for k in ('ax','ay','ex','ey')]!=q:err.append(f'{i}: query choice mismatch')
    used.append(q);train.append({'row':q,'label':r['label']})
  scores=[];grid=itertools.product(l['heldout_grid'],repeat=4)
  for h in w.get('final_hypotheses',[]):
   tp=fp=fn=tn=0
   for x in grid:
    y=truth(x,task);pr=bool(n.evaluate(h['term'],env(x)))
    if y and pr:tp+=1
    elif y:fn+=1
    elif pr:fp+=1
    else:tn+=1
   scores.append({'hypothesis':h['id'],'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':not(fp or fn)})
   grid=itertools.product(l['heldout_grid'],repeat=4)
  if scores!=w.get('heldout_scores'):err.append(f'{i}: holdout score mismatch')
  if w.get('oracle_calls')!=len(used):err.append(f'{i}: oracle call count mismatch')
 summary={}
 for t in l['tasks']:
  group=[x for x in rows if x.get('task')==t]
  summary[t]={'workers':len(group),'statuses':{s:sum(x.get('status')==s for x in group) for s in sorted({x.get('status') for x in group})},'exact_singletons':sum(x.get('status')=='singleton' and len(x.get('heldout_scores',[]))==1 and x['heldout_scores'][0]['exact'] for x in group),'false_singletons':sum(x.get('status')=='singleton' and not(len(x.get('heldout_scores',[]))==1 and x['heldout_scores'][0]['exact']) for x in group),'median_oracle_calls':sorted(x.get('oracle_calls',0) for x in group)[len(group)//2] if group else None,'median_synthesis_rounds':sorted(len(x.get('rounds',[])) for x in group)[len(group)//2] if group else None}
 out={'schema':'NumericOppositionCegisAdequacyV1Analysis','integrity_pass':not err,'errors':err,'summary':summary,'interpretation':'Holdout correctness is scored after freeze and is not used by learner policy. This paired comparison measures only the declared target/grammar/pool panel.','hashes':{'lock':sha(LOCK),'capture':sha(CAP),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(err))
if __name__=='__main__':raise SystemExit(main())
