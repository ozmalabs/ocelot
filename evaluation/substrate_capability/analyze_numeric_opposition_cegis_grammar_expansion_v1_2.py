#!/usr/bin/env python3
"""Audit repeated counterexample repair and resynthesis."""
import hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_grammar_expansion_v1_2_lock_20261003.json';CAP=ROOT/'evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_2_20261003.json';OUT=ROOT/'evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_2_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r):return (r[0]==-r[2]) != (r[1]==-r[3])
def main():
 from substrate_rs import _native
 l=json.loads(LOCK.read_text());c=json.loads(CAP.read_text());n=_native.Substrate();err=[];rows=c.get('workers',[])
 if c.get('lock_sha256')!=sha(LOCK):err.append('lock hash mismatch')
 if c.get('sources')!=l['sources']:err.append('source map mismatch')
 if len(rows)!=5:err.append('worker count mismatch')
 milestones=[]
 for i,w in enumerate(rows):
  base=l['workers'][i];revealed=list(w.get('starting_training',[]));seen=[q['row'] for q in w.get('starting_reserve_queries',[])]
  if w.get('reserve')!=base['reserve']:err.append(f'{i}: reserve mismatch')
  exact_at=[]
  for qi,q in enumerate(w.get('repair_events',[])):
   row=q['row'];candidate=q.get('candidate_term');pred=bool(n.evaluate(candidate,env(row))) if candidate else None;y=bool(truth(row))
   if row not in base['reserve'] or row in seen:err.append(f'{i}: invalid repeated reserve input')
   if pred!=q['prediction'] or q['label']!=int(y) or q['disagrees']!=(pred!=y):err.append(f'{i}: repair oracle/prediction mismatch')
   if candidate is not None:
    tp0=fp0=fn0=tn0=0
    for z in itertools.product(l['heldout_grid'],repeat=4):
     zy=truth(z);zp=bool(n.evaluate(candidate,env(z)))
     if zy and zp:tp0+=1
     elif zy:fn0+=1
     elif zp:fp0+=1
     else:tn0+=1
    if not(fp0 or fn0):exact_at.append(qi)
   if revealed[-1:] and revealed[-1]['row']==row:err.append(f'{i}: duplicate revealed case')
   revealed.append({'row':row,'label':int(y)});seen.append(row)
   if pred!=y:
    if w.get('final_term') is None:err.append(f'{i}: no candidate after counterexample')
  if revealed!=w.get('final_training'):err.append(f'{i}: final training ledger mismatch')
  term=w.get('final_term')
  if term is not None:
   for x in revealed:
    if bool(n.evaluate(term,env(x['row'])))!=bool(x['label']):err.append(f'{i}: final term fails revealed example')
   tp=fp=fn=tn=0
   for x in itertools.product(l['heldout_grid'],repeat=4):
    y=truth(x);p=bool(n.evaluate(term,env(x)))
    if y and p:tp+=1
    elif y:fn+=1
    elif p:fp+=1
    else:tn+=1
   score={'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':not(fp or fn)}
   if score!=w.get('heldout'):err.append(f'{i}: holdout mismatch')
   if score['exact']:exact_at.append(len(w.get('repair_events',[])))
  milestones.append({'worker':w.get('worker'),'first_exact_after_additional_labels':min(exact_at) if exact_at else None,'additional_labels':len(w.get('repair_events',[])),'heldout_exact':bool(w.get('heldout',{}).get('exact'))})
 summary={'workers':len(rows),'statuses':{s:sum(w.get('status')==s for w in rows) for s in sorted({w.get('status') for w in rows})},'exact_holdouts':sum(bool(w.get('heldout',{}).get('exact')) for w in rows),'false_final_hypotheses':sum(w.get('final_term') is not None and not w.get('heldout',{}).get('exact',False) for w in rows),'median_additional_oracle_calls':sorted(len(w.get('repair_events',[])) for w in rows)[len(rows)//2] if rows else None}
 summary['first_exact_label_counts']=[m['first_exact_after_additional_labels'] for m in milestones]
 out={'schema':'CegisGrammarExpansionV1_2Analysis','integrity_pass':not err,'errors':err,'summary':summary,'milestones':milestones,'limits':'Holdout milestones are post-capture analysis only and never affect policy. Five related synthetic XOR panels; fixed, human-authored Not expansion; no unrelated-task transfer or autonomous primitive invention.','hashes':{'lock':sha(LOCK),'capture':sha(CAP),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(err))
if __name__=='__main__':raise SystemExit(main())
