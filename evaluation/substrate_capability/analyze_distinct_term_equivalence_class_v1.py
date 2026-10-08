#!/usr/bin/env python3
"""Independent replay and wider-domain check for distinct-Term class control."""
import hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runners/dsl/python'))
LOCK=ROOT/'evaluation/substrate_capability/distinct_term_equivalence_class_v1_lock_20261004.json'
RAW=ROOT/'evaluation/reports/distinct_term_equivalence_class_v1_20261004.json'
ULOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
UVALS=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5);KEYS=('ax','ay','ex','ey')
OUT=ROOT/'evaluation/reports/distinct_term_equivalence_class_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def env(row):return dict(zip(KEYS,map(float,row)))
def truth(row):return float(row[0])==-float(row[2])
def wider(seed,n):
 r=random.Random(seed);out=[]
 for _ in range(n):
  x=r.uniform(-1e6,1e6);ay=r.uniform(-1e6,1e6);ey=r.uniform(-1e6,1e6)
  out.append(([x,ay,-x,ey],True))
  e=r.uniform(-1e6,1e6)
  if e==-x:e+=1.0
  out.append(([x,ay,e,ey],False))
 for x in (0.0,-0.0,1.0,-1.0,.5,-.5,1e-300,-1e-300,1e300,-1e300,sys.float_info.max,-sys.float_info.max):
  out.append(([x,0.0,-x,7.0],True));bad=1.0 if x==0.0 else x
  if bad==-x:bad=-x+2.0
  out.append(([x,0.0,bad,-9.0],False))
 return out
def main():
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());up=json.loads(ULOCK.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture provenance mismatch')
 if lock.get('upstream_lock_sha256')!=sha(ULOCK):errors.append('upstream lock mismatch')
 for rel,want in lock.get('sources',{}).get('files',{}).items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=want:errors.append(f'source drift: {rel}')
 panels={(p['task'],p['worker']):p for p in up['panels']};native=_native.Substrate();cases=wider(lock['wider_domain_seed'],lock['balanced_pairs']);out=[]
 term_ids=[h['id'] for h in lock['candidate_terms']];term_map={h['id']:h['term'] for h in lock['candidate_terms']}
 if len({canon(x) for x in term_map.values()})!=3:errors.append('candidate Terms are not three structurally distinct trees')
 for w in raw.get('workers',[]):
  key=(w.get('task'),w.get('worker'));p=panels.get(key);r=w.get('result',{})
  if p is None or key[0]!='opposition':errors.append(f'unlocked panel {key}');continue
  alive={h['id']:h for h in lock['candidate_terms']};steps=r.get('steps',[])
  for s in steps:
   row=tuple(map(float,s.get('row',[])));label=truth(row)
   if s.get('label') is not label:errors.append(f'oracle label mismatch {key}')
   for hid,h in list(alive.items()):
    try:v=native.evaluate(h['term'],env(row))
    except Exception:v=None
    if type(v) is not bool or v is not label:alive.pop(hid)
  survivors={h['id']:h for h in r.get('survivors',[])}
  if set(alive)!=set(survivors):errors.append(f'survivor replay mismatch {key}')
  returned=set(survivors)
  if r.get('decision')!='behavior_class' or returned!={'opposition_direct','opposition_swapped_negation'}:errors.append(f'distinct class decision mismatch {key}: {r.get("decision")} {sorted(returned)}')
  domain=p['original_selection_pool']+p['original_challenge_order']+p['zero_selection_pool']+p['zero_challenge_pool']
  probes=list(dict.fromkeys(tuple(map(float,x)) for x in domain));signatures={}
  for hid in returned:
   signatures[hid]=tuple((type(v).__name__,v) for v in (native.evaluate(term_map[hid],env(x)) for x in probes))
  if len(set(signatures.values()))!=1:errors.append(f'members disagree on covered probes {key}')
  holdout=[x for x in itertools.product(UVALS,repeat=4) if x!=(0.,0.,0.,0.)]
  def safe(h,rows):
   for row in rows:
    try:v=native.evaluate(h,env(row))
    except Exception:return False
    if type(v)is not bool or v is not truth(row):return False
   return True
  holdout_safe={hid:safe(term_map[hid],holdout) for hid in returned}
  wide_safe={hid:safe(term_map[hid],[row for row,_ in cases]) for hid in returned}
  if not all(holdout_safe.values()) or not all(wide_safe.values()):errors.append(f'member failed independent domain {key}')
  control_predictions=[native.evaluate(term_map['same_sign_control'],env(row)) for row,_ in cases]
  control_errors=sum(type(v)is not bool or v is not y for v,(_,y) in zip(control_predictions,cases))
  if control_errors==0:errors.append(f'same-sign control unexpectedly exact {key}')
  out.append({'task':key[0],'worker':key[1],'decision':r.get('decision'),'labels':r.get('calls'),'expansions':len(r.get('expansions',[])),
   'returned_ids':sorted(returned),'distinct_returned_terms':len({canon(term_map[i]) for i in returned}),'covered_probe_count':len(probes),
   'holdout_safe':holdout_safe,'wider_cases_per_member':len(cases),'wider_safe':wide_safe,'same_sign_control_errors':control_errors})
 if len(out)!=5:errors.append(f'expected five opposition panels, got {len(out)}')
 result={'schema':'DistinctTermEquivalenceClassV1Analysis','passed':not errors,'errors':errors,'lock_sha256':sha(LOCK),'capture_sha256':sha(RAW),'analyzer_sha256':sha(Path(__file__)),'summary':{'panels':len(out),'distinct_term_class_panels':sum(r['distinct_returned_terms']>1 for r in out),'all_members_holdout_safe':all(all(x['holdout_safe'].values()) for x in out),'all_members_wider_safe':all(all(x['wider_safe'].values()) for x in out),'total_wider_domain_cases_per_member':len(cases),'median_labels':sorted(r['labels'] for r in out)[len(out)//2]},'rows':out,'limits':['five frozen opposition panels','three harness-supplied Terms','finite independent wider-domain check','does not measure candidate generation or natural-task prevalence']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':not errors,'errors':errors,'summary':result['summary']},sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
