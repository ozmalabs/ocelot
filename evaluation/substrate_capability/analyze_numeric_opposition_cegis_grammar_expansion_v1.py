#!/usr/bin/env python3
"""Audit reserve counterexamples and independently score expanded terms."""
import hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_grammar_expansion_v1_lock_20261003.json';CAP=ROOT/'evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_20261003.json';OUT=ROOT/'evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r):return (r[0]==-r[2]) != (r[1]==-r[3])
def main():
 from substrate_rs import _native
 l=json.loads(LOCK.read_text());c=json.loads(CAP.read_text());n=_native.Substrate();errs=[];rows=c.get('workers',[])
 if c.get('lock_sha256')!=sha(LOCK):errs.append('lock hash mismatch')
 if c.get('sources')!=l['sources']:errs.append('source map mismatch')
 if len(rows)!=5:errs.append('worker count mismatch')
 for i,w in enumerate(rows):
  src=l['workers'][i]
  if w.get('reserve')!=src['reserve']:errs.append(f'{i}: reserve mismatch')
  if w.get('revealed_training')[:len(src['initial_training'])]!=src['initial_training']:errs.append(f'{i}: initial examples mismatch')
  queries=w.get('reserve_queries',[]);seen=[];first_mismatch=None
  term=w.get('stage1_term')
  for q in queries:
   row=q['row']
   if row not in src['reserve'] or row in seen:errs.append(f'{i}: invalid reserve query')
   seen.append(row);truth=bool((row[0]==-row[2]) != (row[1]==-row[3]))
   if q['label']!=int(truth):errs.append(f'{i}: oracle label mismatch')
   pred=bool(n.evaluate(term,env(row))) if term is not None else None
   if pred!=q['prediction'] or (pred is not None and q['disagrees']!=(pred!=truth)):errs.append(f'{i}: candidate prediction mismatch')
   if pred is not None and pred!=truth and first_mismatch is None:first_mismatch=row
  expect='no_fit' if w.get('stage1_status')=='no_fit' else ('reserve_counterexample' if first_mismatch else 'reserve_exhausted')
  if w.get('trigger')!=expect:errs.append(f'{i}: trigger mismatch')
  tr=w.get('expanded_term'); train=w.get('revealed_training',[])
  if expect in ('no_fit','reserve_counterexample') and tr is None:errs.append(f'{i}: expansion missing after trigger')
  if tr is not None:
   for x in train:
    if bool(n.evaluate(tr,env(x['row'])))!=bool(x['label']):errs.append(f'{i}: expanded term fails revealed example')
   tp=fp=fn=tn=0
   for x in itertools.product(l['heldout_grid'],repeat=4):
    y=bool((x[0]==-x[2]) != (x[1]==-x[3]));p=bool(n.evaluate(tr,env(x)))
    if y and p:tp+=1
    elif y:fn+=1
    elif p:fp+=1
    else:tn+=1
   expected={'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':not(fp or fn)}
   if expected!=w.get('heldout'):errs.append(f'{i}: holdout mismatch')
 summary={'workers':len(rows),'triggers':{x:sum(w.get('trigger')==x for w in rows) for x in sorted({w.get('trigger') for w in rows})},'expanded_exact':sum(bool(w.get('heldout',{}).get('exact')) for w in rows),'expanded_no_fit':sum(w.get('expanded_term') is None and w.get('expanded_ops') for w in rows),'median_expansion_ms':sorted(w.get('expanded_wall_ns',0)/1e6 for w in rows)[len(rows)//2] if rows else None,'counterexamples_found':sum(any(q.get('disagrees') for q in w.get('reserve_queries',[])) for w in rows)}
 out={'schema':'CegisGrammarExpansionV1Analysis','integrity_pass':not errs,'errors':errs,'summary':summary,'limits':'Only a predeclared Not expansion was tested on the related XOR target. No primitive was invented and no unrelated task family was evaluated.','hashes':{'lock':sha(LOCK),'capture':sha(CAP),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(errs))
if __name__=='__main__':raise SystemExit(main())
