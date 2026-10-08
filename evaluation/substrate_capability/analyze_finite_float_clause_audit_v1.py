#!/usr/bin/env python3
"""Independent bound-intersection oracle for the finite-float clause audit."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/finite_float_clause_audit_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/finite_float_clause_audit_v1_20261004.json';OUT=ROOT/'evaluation/reports/finite_float_clause_audit_v1_analysis_20261004.json';VARS=('ax','ay')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def holds(v,op,x):
 return {'Eq':lambda:v==x,'Lt':lambda:v<x,'Lte':lambda:v<=x,'Gt':lambda:v>x,'Gte':lambda:v>=x}[op]()
def ref_status(constraints):
 by={}
 for v,op,x in constraints:by.setdefault(v,[]).append((op,float(x)))
 for items in by.values():
  eqs=[x for op,x in items if op=='Eq']
  if eqs:
   candidate=eqs[0]
   if not math.isfinite(candidate) or any(x!=candidate for x in eqs) or not all(holds(candidate,op,x) for op,x in items):return 'proven_unsat'
   continue
  lowers=[(x,op=='Gt') for op,x in items if op in ('Gt','Gte')]
  if lowers:
   lo=max(x for x,_ in lowers);exclusive=any(strict and x==lo for x,strict in lowers)
   candidate=math.nextafter(lo,math.inf) if exclusive else lo
  else:candidate=-float.fromhex('0x1.fffffffffffffp+1023')
  if not math.isfinite(candidate) or not all(holds(candidate,op,x) for op,x in items):return 'proven_unsat'
 return 'satisfiable'
def main():
 import finite_float_clause_audit_v1 as m
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());errors=[];counts={'solver_sat_reference_unsat':0,'solver_unsat_reference_sat':0,'witness_invalid_python':0,'witness_invalid_native':0};n=_native.Substrate();workers=raw.get('workers',[])
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or m.canon(m.cases())!=m.canon(lock.get('cases')):errors.append('source/case drift')
 if sha(m.SRAW)!=lock['upstream_capture_sha256'] or not json.loads(m.SAN.read_text()).get('passed'):errors.append('upstream evidence')
 if len(workers)!=m.NCASES or raw.get('cases')!=m.NCASES:errors.append('case count')
 by_id={w.get('id'):w for w in workers};native_checks=0;solver_counts={'satisfiable':0,'proven_unsat':0};total_constraints=0
 for case in lock['cases']:
  w=by_id.get(case['id']);cs=case['constraints'];expected=ref_status(cs);total_constraints+=len(cs)
  if w is None:errors.append(f"case {case['id']}: missing");continue
  status=w.get('solver_status');solver_counts[status]=solver_counts.get(status,0)+1
  if status!=expected:
   if status=='satisfiable':counts['solver_sat_reference_unsat']+=1
   else:counts['solver_unsat_reference_sat']+=1
  if expected=='satisfiable':
   witness=w.get('witness')
   if not isinstance(witness,dict) or any(not math.isfinite(float(x)) for x in witness.values()) or not all(holds(float(witness[v]),op,float(x)) for v,op,x in cs):counts['witness_invalid_python']+=1
   else:
    pred=classify(n.evaluate(m.term_for(cs),witness));native_checks+=1
    if w.get('native_witness_result') is not True or pred is not True:counts['witness_invalid_native']+=1
  elif w.get('witness') is not None:errors.append(f"case {case['id']}: witness on unsat")
 if raw.get('constraint_count')!=total_constraints or raw.get('native_witness_evaluations')!=native_checks:errors.append('work count')
 checks={'source_and_seed_lock':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'all_generated_cases_replayed':len(by_id)==m.NCASES and not any('missing' in e for e in errors),'status_matches_independent_interval_oracle':sum(counts[k] for k in ('solver_sat_reference_unsat','solver_unsat_reference_sat'))==0,'all_satisfying_witnesses_valid':counts['witness_invalid_python']==0,'native_term_agrees_on_all_witnesses':counts['witness_invalid_native']==0,'cost_counts_reconcile':not any('count' in e for e in errors)}
 result={'schema':'FiniteFloatClauseAuditV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'status_confusions':counts,'solver_status_counts':solver_counts,'cases':m.NCASES,'constraints':total_constraints,'native_witness_checks':native_checks,'wall_ns':raw.get('wall_ns'),'cpu_ns':raw.get('cpu_ns'),'cases_per_second':m.NCASES/(raw.get('wall_ns',1)/1e9),'claim_boundary':'Differential validation covers 4,096 seeded conjunctions of direct unary comparisons over finite binary64 values. It does not cover cross-variable constraints, arbitrary Terms, or proposal-policy completeness.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
