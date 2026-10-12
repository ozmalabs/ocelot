#!/usr/bin/env python3
"""Independent finite representative-domain oracle for variable relations."""
import hashlib,itertools,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/finite_float_variable_relations_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/finite_float_variable_relations_v1_20261004.json';OUT=ROOT/'evaluation/reports/finite_float_variable_relations_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def truth(x,op,y):
 return {'Eq':x==y,'Lt':x<y,'Lte':x<=y,'Gt':x>y,'Gte':x>=y}[op]
def representatives(case):
 s={-sys.float_info.max,sys.float_info.max,-0.,0.}
 for atom in case['atoms']:
  for side in ('a','b'):
   obj=atom[side]
   if obj.get('type')!='Lit':continue
   x=float(obj['value']);s.add(x)
   lo=hi=x
   for _ in range(2):
    lo=math.nextafter(lo,-math.inf);hi=math.nextafter(hi,math.inf)
    if math.isfinite(lo):s.add(lo)
    if math.isfinite(hi):s.add(hi)
 return sorted(s)
def reference(case,domain):
 for x,y in itertools.product(domain,repeat=2):
  env={'ax':x,'ay':y};ok=True
  for a in case['atoms']:
   left=env[a['a']['name']] if a['a']['type']=='Var' else float(a['a']['value'])
   right=env[a['b']['name']] if a['b']['type']=='Var' else float(a['b']['value'])
   if not truth(left,a['op'],right):ok=False;break
  if ok:return 'satisfiable',env
 return 'no_representative_witness',None
def main():
 import finite_float_variable_relations_v1 as m
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());errors=[];workers={w.get('id'):w for w in raw.get('workers',[])};counts={'satisfiable':0,'no_representative_witness':0};false_unresolved=0;bad_witness=0;native_mismatch=0;pair_count=0;n=_native.Substrate()
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or m.canon(m.cases())!=m.canon(lock.get('cases')):errors.append('source/case drift')
 if sha(m.BRAW)!=lock['upstream_capture_sha256'] or not json.loads(m.BAN.read_text()).get('passed'):errors.append('upstream audit')
 if len(workers)!=m.NCASES:errors.append('worker count')
 for case in lock['cases']:
  w=workers.get(case['id'])
  if w is None:errors.append(f"missing {case['id']}");continue
  if not any(a['a'].get('type')=='Var' and a['b'].get('type')=='Var' for a in case['atoms']):errors.append(f"{case['id']}: no variable relation")
  domain=representatives(case);pair_count+=len(domain)**2;status,witness=reference(case,domain);counts[status]+=1
  if w.get('reference_status')!=status or w.get('parse_status')!='unresolved':false_unresolved+=1
  stored=w.get('witness')
  if status=='satisfiable':
   if not isinstance(stored,dict) or not all(truth(float(stored[a['a']['name']]) if a['a']['type']=='Var' else float(a['a']['value']),a['op'],float(stored[a['b']['name']]) if a['b']['type']=='Var' else float(a['b']['value'])) for a in case['atoms']):bad_witness+=1
   elif classify(n.evaluate({'type':'And','items':[{'type':a['op'],'a':a['a'],'b':a['b']} for a in case['atoms']]},stored)) is not True or w.get('native_result') is not True:native_mismatch+=1
  elif stored is not None or w.get('native_result') is not None:errors.append(f"{case['id']}: unexpected no-witness payload")
 if raw.get('representative_pairs')!=pair_count:errors.append('representative work count')
 if raw.get('native_witness_evaluations')!=counts['satisfiable']:errors.append('native work count')
 checks={'source_and_seed_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'all_cases_have_variable_relations':not any('no variable relation' in e or 'missing' in e for e in errors),'representative_domain_replay':false_unresolved==0,'unresolved_classification_fail_closed':false_unresolved==0,'satisfying_witnesses_hold':bad_witness==0,'native_term_parity':native_mismatch==0,'work_counts_reconcile':not any('count' in e for e in errors)}
 result={'schema':'FiniteFloatVariableRelationsV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cases':m.NCASES,'reference_status_counts':counts,'representative_pairs':pair_count,'unresolved_classification_errors':false_unresolved,'invalid_witnesses':bad_witness,'native_witness_disagreements':native_mismatch,'wall_ns':raw.get('wall_ns'),'cpu_ns':raw.get('cpu_ns'),'claim_boundary':'1,024 generated two-variable comparison conjunctions are checked over a finite representative set; 629 have no witness in that set, which is not claimed as an unrestricted unsatisfiability proof. The current direct-unary solver abstains on all because each contains a variable-variable comparison.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
