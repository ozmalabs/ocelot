#!/usr/bin/env python3
"""Independent re-score of the coverage-directed symbolic learning capture."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_relation_learning_v1_1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_1_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_1_coverage_analysis_20261003.json'
ALLOWED={'Var','Lit','Neg','Eq','And'};INPUTS={'ax','ay','ex','ey'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(row):return {k:float(v) for k,v in zip(('ax','ay','ex','ey'),row)}
def main():
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('workers',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('capture source map differs from lock')
 if len(rows)!=lock['workers'] or {r.get('worker') for r in rows}!=set(range(lock['workers'])):errors.append('worker count/IDs mismatch')
 native=_native.Substrate();grid=list(itertools.product(lock['heldout_values'],repeat=4));results=[]
 for r in rows:
  i=r['worker'];panel=lock['panels'][i];term=r.get('term')
  if r.get('training')!=panel['training']:errors.append(f'worker {i}: training data mismatch')
  positives=[x['row'] for x in panel['training'] if x['label']==1]
  negatives=[x['row'] for x in panel['training'] if x['label']==0]
  if len(positives)!=8 or len(negatives)!=8:errors.append(f'worker {i}: training balance mismatch')
  if not(any(p[0]==0 for p in positives) and any(p[1]==0 for p in positives)
      and any(p[0]!=0 and p[1]!=0 for p in positives)):
   errors.append(f'worker {i}: positive axis coverage missing')
  if not(any(n[0]==-n[2] and n[1]!=-n[3] for n in negatives)
      and any(n[1]==-n[3] and n[0]!=-n[2] for n in negatives)):
   errors.append(f'worker {i}: x-only/y-only counterexample coverage missing')
  if not(r.get('source_stable') and r.get('sources_before')==lock['sources'] and r.get('sources_after')==lock['sources']):errors.append(f'worker {i}: source drift')
  if not term or r.get('halt_reason')!='solved':errors.append(f'worker {i}: no solved hypothesis');continue
  ops=set();vars_=set();lits=0
  def walk(x):
   nonlocal lits
   if isinstance(x,dict):
    typ=x.get('type')
    if typ:
     ops.add(typ)
     if typ not in ALLOWED:errors.append(f'worker {i}: operator outside grammar: {typ}')
     if typ=='Var':vars_.add(x.get('name'))
     if typ=='Lit':lits+=1
    for v in x.values():walk(v)
   elif isinstance(x,(list,tuple)):
    for v in x:walk(v)
  walk(term)
  if not vars_<=INPUTS or not vars_ or lits:errors.append(f'worker {i}: candidate violates variable/constant grammar')
  def nodes(x):
   if isinstance(x,dict):return (1 if x.get('type') else 0)+sum(nodes(v) for k,v in x.items() if k!='type')
   if isinstance(x,(list,tuple)):return sum(nodes(v) for v in x)
   return 0
  if nodes(term)!=r.get('size'):errors.append(f'worker {i}: AST size mismatch')
  for ex in panel['training']:
   try:pred=bool(native.evaluate(term,env(ex['row'])))
   except Exception as e:errors.append(f'worker {i}: training eval error {e}');continue
   if pred!=bool(ex['label']):errors.append(f'worker {i}: training example not fit')
  tp=fp=fn=tn=0
  for a,b,c,d in grid:
   truth=(a==-c and b==-d)
   try:pred=bool(native.evaluate(term,{'ax':a,'ay':b,'ex':c,'ey':d}))
   except Exception as e:errors.append(f'worker {i}: held-out eval error {e}');break
   if pred and truth:tp+=1
   elif pred:fp+=1
   elif truth:fn+=1
   else:tn+=1
  score={'n':len(grid),'positive_n':tp+fn,'negative_n':fp+tn,'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':fp==0 and fn==0}
  if score!=r.get('heldout'):errors.append(f'worker {i}: capture score differs from independent engine replay')
  results.append({'worker':i,'term':r.get('term_str'),'size':r.get('size'),'operators':sorted(ops),
    'explored':r.get('explored'),'wall_ms':r.get('wall_ns',0)/1e6,'cpu_ms':r.get('cpu_ns',0)/1e6,
    'heldout':score})
 summary={'workers':len(rows),'training_fit_workers':sum(not any(f'worker {r["worker"]}: training example not fit'==e for e in errors) for r in rows),
  'exact_heldout_workers':sum(x['heldout']['exact'] for x in results),'heldout_cases_per_worker':len(grid),
  'pooled_tp':sum(x['heldout']['tp'] for x in results),'pooled_fp':sum(x['heldout']['fp'] for x in results),
  'pooled_fn':sum(x['heldout']['fn'] for x in results),'pooled_tn':sum(x['heldout']['tn'] for x in results),
  'median_wall_ms':statistics.median(r['wall_ns'] for r in rows)/1e6 if rows else None,
  'median_cpu_ms':statistics.median(r['cpu_ns'] for r in rows)/1e6 if rows else None,
  'median_explored_terms':statistics.median(r['explored'] for r in rows) if rows else None}
 result={'schema':'NumericOppositionRelationLearningV1_2Analysis','measurement_integrity_pass':not errors,
  'generalization_gate_pass':not errors and summary['exact_heldout_workers']==lock['workers'],
  'errors':errors,'analysis_note':'This analyzes measured capability. A learned hypothesis can fit training yet fail held-out generalization; such errors are retained as capability outcomes, not measurement-invalidity.','summary':summary,'workers':results,
  'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE),'analyzer_sha256':sha(Path(__file__))}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
