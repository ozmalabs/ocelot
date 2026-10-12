#!/usr/bin/env python3
"""Post-search paired audit of integer versus balanced continuous examples."""
import hashlib,json,math,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/CONTINUOUS_SINGLETON_AUDIT_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_continuous_singleton_audit_v1.py'
ADRUN=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1.py';ADAN=ROOT/'evaluation/substrate_capability/analyze_adaptive_factored_operator_search_v1.py';ADLOCK=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1_lock_20261004.json';ADRAW=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_20261004.json';ADOUT=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/continuous_singleton_audit_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/continuous_singleton_audit_v1_20261004.json'
KEYS=('ax','ay','ex','ey');TASKS=('additive','product','absolute','minimum');HELD=(-2.5,-1.5,-.5,.5,1.5,2.5);LOW=-2.4;HIGH=2.4;PER_CLASS=2
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,ADRUN,ADAN,ADLOCK,ADRAW,ADOUT];b=Path(_native.__file__).resolve()
 return {'files':{str(x.relative_to(ROOT)):sha(x) for x in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels():return json.loads(ADLOCK.read_text())['panels']
def truth(task,r):
 if task=='additive':return r[0]+r[1]==r[2]+r[3]
 if task=='product':return r[0]*r[1]==r[2]*r[3]
 if task=='absolute':return abs(r[0])==abs(r[2])
 return min(r[0],r[1])==min(r[2],r[3])
def audit_rows(task,seed,forbidden):
 rng=random.Random(seed+90871);pos=[];neg=[]
 def valid(x):return all(LOW<=v<=HIGH for v in x) and tuple(x) not in forbidden and all(abs(v-round(v))>1e-5 for v in x)
 while len(pos)<PER_CLASS or len(neg)<PER_CLASS:
  if task=='additive':
   ax,ay,ex=[rng.uniform(-2.2,2.2) for _ in range(3)];ey=ax+ay-ex
   x=[ax,ay,ex,ey]
   if valid(x) and len(pos)<PER_CLASS:pos.append(x)
   y=[ax,ay,ex,ey+0.35]
   if valid(y) and not truth(task,y) and len(neg)<PER_CLASS:neg.append(y)
  elif task=='product':
   ax,ay=[rng.uniform(-2.,2.) for _ in range(2)];x=[ax,ay,ax,ay];y=[ax+0.35,ay,ax,ay]
   if valid(x) and len(pos)<PER_CLASS:pos.append(x)
   if valid(y) and not truth(task,y) and len(neg)<PER_CLASS:neg.append(y)
  elif task=='absolute':
   ax=rng.uniform(-2.2,2.2);ay=rng.uniform(-2.2,2.2);ex=ax if len(pos)%2==0 else -ax;ey=rng.uniform(-2.2,2.2);x=[ax,ay,ex,ey];y=[ax,ay,abs(ax)+0.35,ey]
   if valid(x) and len(pos)<PER_CLASS:pos.append(x)
   if valid(y) and not truth(task,y) and len(neg)<PER_CLASS:neg.append(y)
  else:
   m=rng.uniform(-1.4,1.4);u=rng.uniform(m+0.55,2.3);v=rng.uniform(m+0.55,2.3);x=[m,u,m,v] if len(pos)%2==0 else [u,m,v,m];y=[m,u,m+0.35,v]
   if valid(x) and len(pos)<PER_CLASS:pos.append(x)
   if valid(y) and not truth(task,y) and len(neg)<PER_CLASS:neg.append(y)
 rows=[{'row':x,'label':int(truth(task,x)),'kind':'positive'} for x in pos]+[{'row':x,'label':int(truth(task,x)),'kind':'negative'} for x in neg]
 rng.shuffle(rows);return rows
def worker(panel,up):
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();hid=up.get('accepted_id');desc=next((h for h in up.get('final_terms',[]) if h['id']==hid),None)
 reserved=[]
 for b in up.get('branches',[]):
  if b.get('decision')=='accept':reserved=[e for e in b['events'] if e['kind']=='audit' and e.get('candidate_id')==hid]
 forbidden={tuple(map(float,x['row'])) for x in panel['training']}|{tuple(map(float,x)) for x in panel['selection_pool']}
 rows=audit_rows(panel['task'],panel['seed'],forbidden) if desc else []
 events=[];decision='request_help';used=0
 if desc:
  decision='accept'
  for x in rows:
   q=dict(zip(KEYS,x['row']));pred=classify(n.evaluate(desc['term'],q));label=bool(truth(panel['task'],x['row']));events.append({'row':x['row'],'kind':x['kind'],'prediction':pred,'label':label,'match':pred is label});used+=1
   if pred is not label:decision='request_help';break
 return {'task':panel['task'],'worker':panel['worker'],'seed':panel['seed'],'training':panel['training'],'selection_pool':panel['selection_pool'],'selection_order':panel['selection_order'],'candidate_id':hid,'candidate_term':None if not desc else desc['term'],'adaptive_integer_decision':up['decision'],'integer_audit_events':reserved,'integer_policy_labels':len(reserved),'continuous_audit_examples':rows,'continuous_events':events,'continuous_policy_decision':decision,'continuous_policy_labels':used,'help_control_decision':'request_help','help_control_labels':0}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  raw=json.loads(ADRAW.read_text());analysis=json.loads(ADOUT.read_text())
  if raw.get('lock_sha256')!=sha(ADLOCK) or not analysis.get('passed'):raise SystemExit('upstream adaptive evidence invalid')
  LOCK.write_text(json.dumps({'schema':'ContinuousSingletonAuditV1Lock','sources':source_map(),'adaptive_lock_sha256':sha(ADLOCK),'adaptive_capture_sha256':sha(ADRAW),'panels':panels(),'tasks':TASKS,'audit_seed_offset':90871,'audit_range':[LOW,HIGH],'balanced_per_class':PER_CLASS,'heldout_values':HELD},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text());raw=json.loads(ADRAW.read_text())
  if source_map()!=l['sources'] or panels()!=l['panels'] or sha(ADRAW)!=l['adaptive_capture_sha256']:raise SystemExit('source/capture drift')
  e={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i,(p,up) in enumerate(zip(l['panels'],raw['workers'])):
   q=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env=e,text=True,capture_output=True,timeout=30)
   if q.returncode:raise RuntimeError(q.stderr[-2000:])
   rows.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift')
  OUT.write_text(json.dumps({'schema':'ContinuousSingletonAuditV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':
  i=int(a[1]);print(json.dumps(worker(panels()[i],json.loads(ADRAW.read_text())['workers'][i]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
