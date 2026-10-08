#!/usr/bin/env python3
"""Independent audit of cross-family induction outcomes."""
import hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python')]
LOCK=ROOT/'evaluation/substrate_capability/structural_induction_cross_family_v1_lock_20261003.json';CAP=ROOT/'evaluation/reports/structural_induction_cross_family_v1_20261003.json';OUT=ROOT/'evaluation/reports/structural_induction_cross_family_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r,t):
 if t=='xor_opposition':return (r[0]==-r[2]) != (r[1]==-r[3])
 if t=='absolute_equality':return abs(r[0])==abs(r[2])
 return r[0]+r[1]==r[2]
def main():
 from substrate_rs import _native
 l=json.loads(LOCK.read_text());c=json.loads(CAP.read_text());n=_native.Substrate();errs=[];rows=c.get('workers',[])
 if c.get('lock_sha256')!=sha(LOCK):errs.append('lock hash mismatch')
 if c.get('sources')!=l['sources']:errs.append('source map mismatch')
 if len(rows)!=len(l['panels']):errs.append('worker count mismatch')
 for i,w in enumerate(rows):
  p=l['panels'][i];task=p['task'];revealed=list(p['training']);queries=[];streak=0;disagreements=0
  if w.get('task')!=task or w.get('worker')!=p['worker'] or w.get('reserve')!=p['reserve']:errs.append(f'{i}: panel mismatch')
  for s in w.get('searches',[]):
   if s.get('example_count')>len(w.get('revealed_training',[])):errs.append(f'{i}: invalid synthesis example count')
   if s.get('term') is not None:
    for x in w['revealed_training'][:s['example_count']]:
     if bool(n.evaluate(s['term'],env(x['row'])))!=bool(x['label']):errs.append(f'{i}: synthesized candidate violates its examples')
  for e in w.get('events',[]):
   row=e['row'];term=e['candidate_term']
   if row not in p['reserve'] or row in queries:errs.append(f'{i}: invalid/duplicate query')
   pred=bool(n.evaluate(term,env(row)));label=int(truth(row,task));dis=pred!=bool(label)
   if pred!=e['prediction'] or label!=e['label'] or dis!=e['disagrees']:errs.append(f'{i}: query prediction/label mismatch')
   if e['streak_before']!=streak:errs.append(f'{i}: streak-before mismatch')
   if dis:streak=0;disagreements+=1
   else:streak+=1
   if e['streak_after']!=streak:errs.append(f'{i}: streak-after mismatch')
   queries.append(row);revealed.append({'row':row,'label':label})
   if len(queries)>=l['query_budget'] and e!=w['events'][-1]:errs.append(f'{i}: continued beyond query budget')
  if revealed!=w.get('revealed_training'):errs.append(f'{i}: training ledger mismatch')
  if w.get('oracle_calls')!=len(queries):errs.append(f'{i}: query count mismatch')
  term=w.get('final_term');scores=None
  if term is not None:
   for x in revealed:
    if bool(n.evaluate(term,env(x['row'])))!=bool(x['label']):errs.append(f'{i}: final term fails revealed data')
   tp=fp=fn=tn=0
   grid=list(itertools.product(l['heldout_values'],repeat=4))
   for r in grid:
    y=bool(truth(r,task));pred=bool(n.evaluate(term,env(r)))
    if y and pred:tp+=1
    elif y:fn+=1
    elif pred:fp+=1
    else:tn+=1
   scores={'n':len(grid),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':not(fp or fn)}
  if scores!=w.get('heldout'):errs.append(f'{i}: heldout score mismatch')
 summary={}
 for t in l['tasks']:
  g=[w for w in rows if w.get('task')==t]
  summary[t]={'workers':len(g),'statuses':{s:sum(w.get('status')==s for w in g) for s in sorted({w.get('status') for w in g})},'exact_holdouts':sum(bool((w.get('heldout') or {}).get('exact')) for w in g),'median_oracle_calls':sorted(w.get('oracle_calls',0) for w in g)[len(g)//2] if g else None,'median_synthesis_calls':sorted(len(w.get('searches',[])) for w in g)[len(g)//2] if g else None,'median_wall_synthesis_ms':sorted([s.get('wall_ns',0)/1e6 for w in g for s in w.get('searches',[])])[len([s for w in g for s in w.get('searches',[])])//2] if g else None}
 out={'schema':'StructuralInductionCrossFamilyV1Analysis','integrity_pass':not errs,'errors':errs,'summary':summary,'limits':'Five seeded workers per three related numeric tasks; fixed authored grammar-expansion order and synthetic oracle. Not evidence of general task or primitive invention.','hashes':{'lock':sha(LOCK),'capture':sha(CAP),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(errs))
if __name__=='__main__':raise SystemExit(main())
