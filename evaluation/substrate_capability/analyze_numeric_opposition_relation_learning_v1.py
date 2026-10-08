#!/usr/bin/env python3
"""Independent source, training-fit, grammar, and held-out checks."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_relation_learning_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_analysis_20261003.json'
ALLOWED={'Var','Lit','Neg','Eq','And'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('workers',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock.get('sources'):errors.append('capture source mismatch')
 if len(rows)!=lock['workers'] or {r['worker'] for r in rows}!=set(range(lock['workers'])):errors.append('worker coverage mismatch')
 native=_native.Substrate();grid=list(itertools.product(lock['heldout_values'],repeat=4))
 summaries=[]
 for r in rows:
  i=r['worker'];panel=lock['panels'][i];term=r.get('term')
  if r.get('training')!=panel['training']:errors.append(f'worker {i}: training panel mismatch')
  if not(r.get('source_stable') and r.get('sources_before')==lock['sources'] and r.get('sources_after')==lock['sources']):errors.append(f'worker {i}: source drift')
  if not(term and r.get('halt_reason')=='solved' and r.get('fits') and r.get('size',99)<=lock['max_size']):
   errors.append(f'worker {i}: synthesis failed or exceeded size cap');continue
  operators=set();variables=set();literal_count=0
  def walk(node):
   nonlocal literal_count
   if isinstance(node,dict):
    typ=node.get('type')
    if typ:
     operators.add(typ)
     if typ not in ALLOWED:errors.append(f'worker {i}: unsupported operator {typ}')
     if typ=='Var':variables.add(node.get('name'))
     if typ=='Lit':literal_count+=1
    for child in node.values():walk(child)
   elif isinstance(node,(list,tuple)):
    for child in node:walk(child)
  walk(term)
  if literal_count:errors.append(f'worker {i}: generated term contains a literal despite empty constant grammar')
  if variables!={'ax','ay','ex','ey'}:errors.append(f'worker {i}: generated term does not use exactly the declared inputs')
  for ex in panel['training']:
   env={k:float(v) for k,v in zip(('ax','ay','ex','ey'),ex['row'])}
   try:pred=native.evaluate(term,env)
   except Exception as exc:errors.append(f'worker {i}: training evaluation error {exc}');continue
   if bool(pred)!=(bool(ex['label'])):errors.append(f'worker {i}: training label mismatch')
  tp=fp=fn=tn=0
  for a,b,c,d in grid:
   env={'ax':a,'ay':b,'ex':c,'ey':d};expected=(a==-c and b==-d)
   try:pred=bool(native.evaluate(term,env))
   except Exception as exc:errors.append(f'worker {i}: held-out evaluation error {exc}');break
   if pred and expected:tp+=1
   elif pred:fp+=1
   elif expected:fn+=1
   else:tn+=1
  observed={'n':len(grid),'positive_n':tp+fn,'negative_n':fp+tn,'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':fp==fn==0}
  if observed!=r.get('heldout'):errors.append(f'worker {i}: runner score differs from independent score')
  if not observed['exact']:errors.append(f'worker {i}: held-out relation generalization failed')
  summaries.append({'worker':i,'term_str':r.get('term_str'),'operators':sorted(operators),'size':r['size'],'explored':r['explored'],
    'distinct':r['distinct'],'halt_reason':r['halt_reason'],'wall_ms':r['wall_ns']/1e6,
    'cpu_ms':r['cpu_ns']/1e6,'heldout':observed})
 summary={'workers':len(rows),'successful_syntheses':sum(r.get('halt_reason')=='solved' for r in rows),
  'heldout_grid_per_worker':len(grid),'all_workers_exact':len(summaries)==lock['workers'] and all(s['heldout']['exact'] for s in summaries),
  'mean_explored_terms':statistics.mean(r['explored'] for r in rows) if rows else 0,
  'median_wall_ms':statistics.median(r['wall_ns'] for r in rows)/1e6 if rows else 0,
  'median_cpu_ms':statistics.median(r['cpu_ns'] for r in rows)/1e6 if rows else 0,
  'median_term_size':statistics.median(r['size'] for r in rows if r.get('size') is not None) if rows else None}
 result={'schema':'NumericOppositionRelationLearningV1Analysis','gates_pass':not errors,
  'errors':errors,'summary':summary,'workers':summaries,
  'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE)}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
