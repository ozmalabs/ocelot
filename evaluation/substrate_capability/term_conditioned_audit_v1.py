#!/usr/bin/env python3
"""Candidate-Term-conditioned, task-blind balanced audits."""
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_CONDITIONED_AUDIT_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_conditioned_audit_v1.py'
UPRUN=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1.py';UPAN=ROOT/'evaluation/substrate_capability/analyze_adaptive_factored_operator_search_v1.py';UPLOCK=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1_lock_20261004.json';UPRAW=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_20261004.json';UPOUT=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_analysis_20261004.json'
CLRUN=ROOT/'evaluation/substrate_capability/continuous_singleton_audit_v1.py';CLLOCK=ROOT/'evaluation/substrate_capability/continuous_singleton_audit_v1_lock_20261004.json';CLRAW=ROOT/'evaluation/reports/continuous_singleton_audit_v1_20261004.json';CLAN=ROOT/'evaluation/substrate_capability/analyze_continuous_singleton_audit_v1.py';CLOUT=ROOT/'evaluation/reports/continuous_singleton_audit_v1_analysis_20261004.json'
GRUN=ROOT/'evaluation/substrate_capability/generic_continuous_audit_v1.py';GLOCK=ROOT/'evaluation/substrate_capability/generic_continuous_audit_v1_lock_20261004.json';GRAW=ROOT/'evaluation/reports/generic_continuous_audit_v1_20261004.json';GAN=ROOT/'evaluation/substrate_capability/analyze_generic_continuous_audit_v1.py';GOUT=ROOT/'evaluation/reports/generic_continuous_audit_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/term_conditioned_audit_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_conditioned_audit_v1_20261004.json'
KEYS=('ax','ay','ex','ey');TASKS=('additive','product','absolute','minimum');SUPPORT=tuple(-3.+.25*i for i in range(25));CAPS=(4,16,64);PER_CLASS=32;PROPOSAL_BUDGET=100000;SEED_OFFSET=73091

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 files=[RUN,PRE,AN,UPRUN,UPAN,UPLOCK,UPRAW,UPOUT,CLRUN,CLLOCK,CLRAW,CLAN,CLOUT,GRUN,GLOCK,GRAW,GAN,GOUT]
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels():return json.loads(UPLOCK.read_text())['panels']
def truth(task,r):
 a,b,c,d=r
 return a+b==c+d if task=='additive' else a*b==c*d if task=='product' else abs(a)==abs(c) if task=='absolute' else min(a,b)==min(c,d)
def proposals(task,seed,term,forbidden,native):
 rng=random.Random(seed+SEED_OFFSET); denied={tuple(map(float,x)) for x in forbidden};held={tuple(x) for x in __import__('itertools').product((-2.5,-1.5,-.5,.5,1.5,2.5),repeat=4)}
 yes=[];no=[];stream=[];evals=0;start=time.perf_counter_ns();cpu=time.process_time_ns()
 for i in range(PROPOSAL_BUDGET):
  row=tuple(rng.choice(SUPPORT) for _ in KEYS)
  if row in denied or row in held:continue
  pred=native.evaluate(term,dict(zip(KEYS,row)));evals+=1
  if type(pred) is not bool:continue
  item={'proposal_index':i,'row':list(row),'prediction':pred}
  stream.append(item)
  target=yes if pred else no
  if len(target)<PER_CLASS:target.append(item)
  if len(yes)>=PER_CLASS and len(no)>=PER_CLASS:break
 wall=time.perf_counter_ns()-start;cpu_ns=time.process_time_ns()-cpu
 chosen=sorted(yes+no,key=lambda x:x['proposal_index'])
 return chosen,evals,wall,cpu_ns,{'true':len(yes),'false':len(no),'proposals':(chosen[-1]['proposal_index']+1 if chosen else 0)}
def worker(panel,up):
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import score
 n=_native.Substrate();hid=up.get('accepted_id');cand=next((x for x in up.get('final_terms',[]) if x['id']==hid),None)
 forbidden=[x['row'] for x in panel['training']]+panel['selection_pool'];chosen,evals,wall,cpu,counts=proposals(panel['task'],panel['seed'],None if cand is None else cand['term'],forbidden,n) if cand else ([],0,0,0,{'true':0,'false':0,'proposals':0})
 events=[];stop=None
 for i,item in enumerate(chosen):
  label=bool(truth(panel['task'],item['row']));match=item['prediction'] is label
  events.append({'index':i,'proposal_index':item['proposal_index'],'row':item['row'],'prediction':item['prediction'],'label':label,'match':match})
  if not match:stop=i+1;break
 exact=bool(cand and score(n,panel['task'],cand['term'])['exact']);outcomes=[]
 for cap in CAPS:
  decision='request_help' if not cand or (stop is not None and stop<=cap) else 'accept';labels=0 if not cand else min(cap,len(events))
  outcomes.append({'cap':cap,'decision':decision,'labels':labels,'correct_accept':decision=='accept' and exact,'false_accept':decision=='accept' and not exact,'help':decision!='accept'})
 return {'task':panel['task'],'worker':panel['worker'],'seed':panel['seed'],'candidate_id':hid,'candidate_term':None if not cand else cand['term'],'proposal_stream':chosen,'proposal_counts':counts,'native_term_evaluations':evals,'proposal_wall_ns':wall,'proposal_cpu_ns':cpu,'events':events,'first_mismatch_labels':stop,'outcomes':outcomes,'help_control':{'decision':'request_help','labels':0}}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(UPOUT.read_text()).get('passed') or not json.loads(CLOUT.read_text()).get('passed') or not json.loads(GOUT.read_text()).get('passed'):raise SystemExit('upstream analyses must pass')
  raw=json.loads(UPRAW.read_text());cr=json.loads(CLRAW.read_text());gr=json.loads(GRAW.read_text())
  LOCK.write_text(json.dumps({'schema':'TermConditionedAuditV1Lock','sources':source_map(),'upstream_lock_sha256':sha(UPLOCK),'upstream_capture_sha256':sha(UPRAW),'conditioned_lock_sha256':sha(CLLOCK),'conditioned_capture_sha256':sha(CLRAW),'generic_lock_sha256':sha(GLOCK),'generic_capture_sha256':sha(GRAW),'panels':panels(),'support':SUPPORT,'per_class':PER_CLASS,'proposal_budget':PROPOSAL_BUDGET,'caps':CAPS,'seed_offset':SEED_OFFSET},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text());raw=json.loads(UPRAW.read_text())
  if source_map()!=lock['sources'] or panels()!=lock['panels'] or sha(UPRAW)!=lock['upstream_capture_sha256']:raise SystemExit('source/panel drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i,(p,u) in enumerate(zip(lock['panels'],raw['workers'])):
   cp=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=45)
   if cp.returncode:raise RuntimeError(cp.stderr[-2000:])
   rows.append(json.loads(cp.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift')
  OUT.write_text(json.dumps({'schema':'TermConditionedAuditV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':
  i=int(args[1]);print(json.dumps(worker(panels()[i],json.loads(UPRAW.read_text())['workers'][i]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
