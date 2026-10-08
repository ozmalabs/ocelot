#!/usr/bin/env python3
"""Task-agnostic uniform continuous audits of fixed singleton candidates."""
import hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve(); PRE=ROOT/'docs/research/engine_substrate/GENERIC_CONTINUOUS_AUDIT_V1_PREREG_20261004.md'
AN=ROOT/'evaluation/substrate_capability/analyze_generic_continuous_audit_v1.py'
ADRUN=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1.py'; ADAN=ROOT/'evaluation/substrate_capability/analyze_adaptive_factored_operator_search_v1.py'
ADLOCK=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1_lock_20261004.json'; ADRAW=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_20261004.json'; ADOUT=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_analysis_20261004.json'
C_RUN=ROOT/'evaluation/substrate_capability/continuous_singleton_audit_v1.py'; C_LOCK=ROOT/'evaluation/substrate_capability/continuous_singleton_audit_v1_lock_20261004.json'; C_RAW=ROOT/'evaluation/reports/continuous_singleton_audit_v1_20261004.json'; C_ANAL=ROOT/'evaluation/substrate_capability/analyze_continuous_singleton_audit_v1.py'; C_OUT=ROOT/'evaluation/reports/continuous_singleton_audit_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/generic_continuous_audit_v1_lock_20261004.json'; OUT=ROOT/'evaluation/reports/generic_continuous_audit_v1_20261004.json'
KEYS=('ax','ay','ex','ey'); TASKS=('additive','product','absolute','minimum'); LOW=-2.4; HIGH=2.4; CAPS=(4,16,64); SEED_OFFSET=190417

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale, rust_source_fingerprint
 if build_is_stale(str(ROOT)): raise RuntimeError('stale native build')
 files=[RUN,PRE,AN,ADRUN,ADAN,ADLOCK,ADRAW,ADOUT,C_RUN,C_LOCK,C_RAW,C_ANAL,C_OUT]
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels(): return json.loads(ADLOCK.read_text())['panels']
def truth(task,r):
 a,b,c,d=r
 if task=='additive': return a+b==c+d
 if task=='product': return a*b==c*d
 if task=='absolute': return abs(a)==abs(c)
 return min(a,b)==min(c,d)
def draw(task,seed,forbidden):
 rng=random.Random(seed+SEED_OFFSET); rows=[]; denied={tuple(map(float,x)) for x in forbidden}; held={tuple(x) for x in __import__('itertools').product((-2.5,-1.5,-.5,.5,1.5,2.5),repeat=4)}
 while len(rows)<max(CAPS):
  x=tuple(rng.uniform(LOW,HIGH) for _ in KEYS)
  if x in denied or x in held: continue
  rows.append(list(x))
 return rows
def worker(panel,up):
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify,score
 n=_native.Substrate(); hid=up.get('accepted_id'); candidate=next((h for h in up.get('final_terms',[]) if h['id']==hid),None)
 forbidden=[x['row'] for x in panel['training']]+panel['selection_pool']
 rows=draw(panel['task'],panel['seed'],forbidden) if candidate else []
 events=[]; stop=None
 if candidate:
  for i,row in enumerate(rows):
   env=dict(zip(KEYS,row)); pred=classify(n.evaluate(candidate['term'],env)); label=bool(truth(panel['task'],row))
   events.append({'index':i,'row':row,'prediction':pred,'label':label,'match':pred is label})
   if pred is not label: stop=i+1; break
 outcomes=[]
 for cap in CAPS:
  used=min(cap,len(events)); decision='request_help' if stop is not None and stop<=cap else ('accept' if candidate else 'request_help')
  exact=bool(candidate and score(n,panel['task'],candidate['term'])['exact'])
  outcomes.append({'cap':cap,'decision':decision,'labels':used,'correct_accept':decision=='accept' and exact,'false_accept':decision=='accept' and not exact,'help':decision!='accept'})
 return {'task':panel['task'],'worker':panel['worker'],'seed':panel['seed'],'candidate_id':hid,'candidate_term':None if not candidate else candidate['term'],'rows':rows,'events':events,'first_mismatch_labels':stop,'outcomes':outcomes,'help_control':{'decision':'request_help','labels':0}}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists(): raise SystemExit('refusing overwrite')
  raw=json.loads(ADRAW.read_text()); analysis=json.loads(ADOUT.read_text()); c_raw=json.loads(C_RAW.read_text()); c_analysis=json.loads(C_OUT.read_text())
  if raw.get('lock_sha256')!=sha(ADLOCK) or not analysis.get('passed') or c_raw.get('lock_sha256')!=sha(C_LOCK) or not c_analysis.get('passed'): raise SystemExit('upstream evidence invalid')
  LOCK.write_text(json.dumps({'schema':'GenericContinuousAuditV1Lock','sources':source_map(),'adaptive_lock_sha256':sha(ADLOCK),'adaptive_capture_sha256':sha(ADRAW),'continuous_lock_sha256':sha(C_LOCK),'continuous_capture_sha256':sha(C_RAW),'panels':panels(),'range':[LOW,HIGH],'caps':CAPS,'seed_offset':SEED_OFFSET},indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text()); raw=json.loads(ADRAW.read_text())
  if source_map()!=lock['sources'] or panels()!=lock['panels'] or sha(ADRAW)!=lock['adaptive_capture_sha256']: raise SystemExit('source/panel drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}; rows=[]
  for i,(p,u) in enumerate(zip(lock['panels'],raw['workers'])):
   cp=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=30)
   if cp.returncode: raise RuntimeError(cp.stderr[-2000:])
   rows.append(json.loads(cp.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']: raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'GenericContinuousAuditV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n'); print(OUT.relative_to(ROOT)); return 0
 if len(args)==2 and args[0]=='--worker':
  i=int(args[1]); p=panels()[i]; up=json.loads(ADRAW.read_text())['workers'][i]; print(json.dumps(worker(p,up),sort_keys=True,separators=(',',':'))); return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__': raise SystemExit(main())
