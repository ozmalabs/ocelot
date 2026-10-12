#!/usr/bin/env python3
"""Independent check that a boundary probe removes the false class member."""
import hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runners/dsl/python'))
LOCK=ROOT/'evaluation/substrate_capability/boundary_directed_probe_repair_v1_lock_20261004.json'
RAW=ROOT/'evaluation/reports/boundary_directed_probe_repair_v1_20261004.json'
BASE=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_analysis_20261004.json'
OUT=ROOT/'evaluation/reports/boundary_directed_probe_repair_v1_analysis_20261004.json'
VALS=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5);KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(r):return float(r[0])==-float(r[2])
def makewide(seed,n):
 q=random.Random(seed);rows=[]
 for _ in range(n):
  x=q.uniform(-1e6,1e6);y=q.uniform(-1e6,1e6);z=q.uniform(-1e6,1e6);rows.append(([x,y,-x,z],True));e=q.uniform(-1e6,1e6)
  if e==-x:e+=1.
  rows.append(([x,y,e,z],False))
 for x in (0.,-0.,1.,-1.,.5,-.5,1e-300,-1e-300,1e300,-1e300,sys.float_info.max,-sys.float_info.max):
  rows.append(([x,0.,-x,7.],True));e=1. if x==0. else x
  if e==-x:e=-x+2.
  rows.append(([x,0.,e,-9.],False))
 return rows
def main():
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());base=json.loads(BASE.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture provenance mismatch')
 if not base.get('passed') or base['summary'].get('false_safe_class_returns')!=5:errors.append('baseline failure reference mismatch')
 for rel,want in lock.get('sources',{}).get('files',{}).items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=want:errors.append(f'source drift: {rel}')
 native=_native.Substrate();terms={h['id']:h['term'] for h in lock['candidate_terms']};wide=makewide(418204,1500);hold=[r for r in itertools.product(VALS,repeat=4) if r!=(0.,0.,0.,0.)];rows=[]
 for w,p in zip(raw.get('workers',[]),lock['panels']):
  key=(p['task'],p['worker'])
  if (w.get('task'),w.get('worker'))!=key:errors.append(f'panel identity mismatch {key}')
  row=tuple(map(float,w['query_row']));threshold=float(w['threshold'])
  if w['threshold_variable']!='ax' or threshold!=4.0:errors.append(f'wrong extracted bound {key}')
  if row not in {tuple(float(x[k]) for k in KEYS) for x in w['generated_probes']}:errors.append(f'selected input was not candidate-generated {key}')
  if row[0]<threshold or row[2]!=-row[0]:errors.append(f'selected query does not cross and satisfy exact relation {key}')
  if w.get('oracle_label') is not truth(row) or w.get('oracle_label') is not True:errors.append(f'boundary oracle label invalid {key}')
  score={hid:native.evaluate(term,env(row)) for hid,term in terms.items()}
  expected={'opposition_direct','opposition_swapped_negation'}
  survivors={hid for hid,v in score.items() if type(v)is bool and v is w['oracle_label']}
  if survivors!=expected or set(w['survivor_ids_after'])!=expected:errors.append(f'boundary filtering mismatch {key}')
  if w.get('partition',{}).get('class_count')!=1:errors.append(f'remaining exact terms not one class {key}')
  hold_safe={hid:all(type(native.evaluate(term,env(q)))is bool and native.evaluate(term,env(q))is truth(q) for q in hold) for hid,term in terms.items() if hid in expected}
  wide_errors={}
  for hid in expected:
   count=0
   for q,y in wide:
    v=native.evaluate(terms[hid],env(q))
    if type(v)is not bool or v is not y:count+=1
   wide_errors[hid]=count
  if not all(hold_safe.values()) or any(wide_errors.values()):errors.append(f'repaired survivor fails transfer scoring {key}')
  rows.append({'task':key[0],'worker':key[1],'query':list(row),'oracle_label':w['oracle_label'],'survivors':sorted(survivors),
   'discarded_restricted_candidate':'opposition_bounded_x_lt_4' not in survivors,'class_count':w['partition'].get('class_count'),
   'holdout_safe':hold_safe,'wider_errors':wide_errors,'boundary_candidate_evaluations':w.get('candidate_evaluations')})
 if len(rows)!=5:errors.append('expected five repair panels')
 summary={'panels':len(rows),'baseline_false_safe_returns':int(base['summary']['false_safe_class_returns']),'repair_false_safe_returns':sum(not r['discarded_restricted_candidate'] or any(r['wider_errors'].values()) for r in rows),
  'exact_distinct_members_retained':sum(len(r['survivors'])==2 for r in rows),'oracle_labels_total':len(rows),'wide_cases_per_member':len(wide),'all_repaired_members_wide_safe':all(not any(r['wider_errors'].values()) for r in rows)}
 result={'schema':'BoundaryDirectedProbeRepairV1Analysis','passed':not errors,'errors':errors,'lock_sha256':sha(LOCK),'capture_sha256':sha(RAW),'analyzer_sha256':sha(Path(__file__)),'summary':summary,'rows':rows,'limits':['one authored opposition relation','numeric literal boundary and exact relation are harness supplied','five frozen panels','does not establish a generic solver for arbitrary terms']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':not errors,'errors':errors,'summary':summary},sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
