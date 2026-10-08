#!/usr/bin/env python3
"""Source-locked operator-menu, query, and explicit help-action evaluation."""
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/PRIMITIVE_MENU_HELP_POLICY_V1_1_AMENDMENT_20261003.md';ANALYZER=ROOT/'evaluation/substrate_capability/analyze_primitive_menu_help_policy_v1_1.py';LOCK=ROOT/'evaluation/substrate_capability/primitive_menu_help_policy_v1_1_lock_20261003.json';OUT=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_1_20261003.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('additive','product','ordering','opposition','inequality');KEYS=('ax','ay','ex','ey');TRAIN_VALUES=(-3.,-2.,-1.,1.,2.,3.);HELDOUT_VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5);FAMILIES=('Base','Plus','Times','Lt');OPS={'Base':('Neg','Eq','And'),'Plus':('Neg','Eq','And','Plus'),'Times':('Neg','Eq','And','Times'),'Lt':('Neg','Eq','And','Lt'),'Not':('Neg','Eq','And','Not')};HINT={'additive':'Plus','product':'Times','ordering':'Lt','opposition':'Base','inequality':'Not'};WORKERS=5;MAX_SIZE=7;TIMEOUT=6.;MAX_SOLUTIONS=64;LABEL_BUDGET=6;POST_SINGLETON_CHALLENGE=2
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(t,r):
 if t=='additive':return r[0]+r[1]==r[2]+r[3]
 if t=='product':return r[0]*r[1]==r[2]*r[3]
 if t=='ordering':return r[0]<r[2]
 if t=='opposition':return r[0]==-r[2]
 return r[0]!=r[2]
def score(n,t,term):
 tp=fp=fn=tn=invalid=0
 for r in itertools.product(HELDOUT_VALUES,repeat=4):
  try:v=n.evaluate(term,env(r))
  except Exception:invalid+=1;continue
  y=truth(t,r)
  if type(v) is not bool:invalid+=1
  elif v and y:tp+=1
  elif v:fp+=1
  elif y:fn+=1
  else:tn+=1
 return {'n':1296,'exact':not invalid and not fp and not fn,'invalid':invalid,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def panels():
 rows=list(itertools.product(TRAIN_VALUES,repeat=4));out=[]
 for ti,t in enumerate(TASKS):
  pos=[r for r in rows if truth(t,r)];neg=[r for r in rows if not truth(t,r)]
  for w in range(WORKERS):
   seed=903000+ti*100+w;rng=random.Random(seed);train=rng.sample(pos,8)+rng.sample(neg,8);rest=[r for r in rows if r not in train];rng.shuffle(rest);select=rest[:32];challenge=rest[32:64];so=list(select);co=list(challenge);random.Random(seed+10000).shuffle(so);random.Random(seed+20000).shuffle(co)
   out.append({'task':t,'worker':w,'seed':seed,'training':[{'row':list(r),'label':int(truth(t,r))} for r in train],'selection_pool':[list(r) for r in select],'selection_order':[list(r) for r in so],'challenge_pool':[list(r) for r in challenge],'challenge_order':[list(r) for r in co]})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def synth(panel,family):
 from substrate_rs import _native
 from domains.generator import synthesize
 native=_native.Substrate();examples=[(env(x['row']),float(x['label'])) for x in panel['training']];probes=[env(r) for r in panel['selection_pool']];start=time.perf_counter_ns()
 v=synthesize(native,examples,ops=OPS[family],consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=probes,max_solutions=MAX_SOLUTIONS,saturate_k=999999)
 wall=time.perf_counter_ns()-start
 hs=[] if not v else [{'id':family+f'{i:03d}','family':family,'term':h['term'].to_dict()} for i,h in enumerate(v.get('hypotheses',[]))]
 return {'family':family,'ops':OPS[family],'wall_ns':wall,'explored':0 if not v else v.get('explored',0),'halt_reason':None if not v else v.get('halt_reason'),'hypotheses':hs}
def run_policy(panel,hyps,kind,assisted,oracle,teacher_hint):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 native=_native.Substrate();survivors=list(hyps);steps=[];observations=[];used=[];selector_ns=0;stop='candidate_singleton' if len(survivors)==1 else ('empty' if not survivors else '')
 while survivors and len(steps)<LABEL_BUDGET:
  if len(survivors)==1:
   if sum(s['phase']=='challenge' for s in steps)>=POST_SINGLETON_CHALLENGE:stop='singleton_after_challenge';break
   row=next((r for r in panel['challenge_order'] if r not in used),None)
   if row is None:stop='challenge_pool_exhausted';break
   q=env(row);phase='challenge';predictions=[];entropy=None
  else:
   available=[env(r) for r in panel['selection_order'] if r not in used]
   if not available:stop='query_pool_exhausted';break
   if kind=='entropy':
    start=time.perf_counter_ns();choice=select_discriminating_input(lambda term,e:native.evaluate(term,e),survivors,available,observations);selector_ns+=time.perf_counter_ns()-start
    if not choice.get('ok'):stop='selector_abstention';break
    q=choice['query'];predictions=choice.get('predictions',[]);entropy=choice.get('entropy_bits')
   else:q=available[0];predictions=[];entropy=None
   row=[float(q[k]) for k in KEYS];phase='selection'
  label=bool(oracle(q));before=len(survivors);kept=[]
  for h in survivors:
   try:v=native.evaluate(h['term'],q)
   except Exception:continue
   if type(v) is bool and v==label:kept.append(h)
  survivors=kept;used.append(row);observations.append({'inputs':q,'expected':label});steps.append({'phase':phase,'row':row,'input_env':q,'label':label,'before':before,'after':len(survivors),'predictions':predictions,'entropy_bits':entropy})
  if not survivors:stop='empty';break
  if len(survivors)==1:stop='candidate_singleton'
  else:stop='label_budget' if len(steps)>=LABEL_BUDGET else ''
 if not stop:stop='label_budget'
 if len(survivors)==1 and sum(s['phase']=='challenge' for s in steps)>=POST_SINGLETON_CHALLENGE:stop='singleton_after_challenge'
 need_help=assisted and stop in ('empty','selector_abstention','query_pool_exhausted','label_budget','challenge_pool_exhausted')
 help_record=None;helped=None
 if need_help:
  hinted=teacher_hint();help_record={'calls':1,'hinted_family':hinted,'trigger':stop};arm=synth(panel,hinted)
  helped={'family':hinted,'candidate_count':len(arm['hypotheses']),'halt_reason':arm['halt_reason'],'wall_ns':arm['wall_ns'],'hypotheses':arm['hypotheses']}
 survivors_out=[{'id':h['id'],'family':h['family'],'term':h['term']} for h in survivors]
 return {'policy':kind,'assisted':assisted,'steps':steps,'calls':len(steps),'selector_ns':selector_ns,'stop':stop,'survivors':survivors_out,'help':help_record,'helped_result':helped}
def worker(panel):
 task=panel['task'];arms=[synth(panel,f) for f in FAMILIES];hyps=[h for a in arms for h in a['hypotheses']]
 inputs={k:panel[k] for k in ('training','selection_pool','selection_order','challenge_pool','challenge_order')}
 oracle=lambda e:truth(task,tuple(float(e[k]) for k in KEYS));teacher_hint=lambda:HINT[task]
 policies=[run_policy(inputs,hyps,k,a,oracle,teacher_hint) for k in ('fixed_order','entropy') for a in (False,True)]
 from substrate_rs import _native
 native=_native.Substrate()
 for arm in arms:
  for h in arm['hypotheses']:h['heldout']=score(native,task,h['term'])
 for policy in policies:
  for h in policy['survivors']:h['heldout']=score(native,task,h['term'])
  if policy['helped_result']:
   for h in policy['helped_result']['hypotheses']:h['heldout']=score(native,task,h['term'])
 return {'task':panel['task'],'worker':panel['worker'],'training':panel['training'],'selection_pool':panel['selection_pool'],'selection_order':panel['selection_order'],'challenge_pool':panel['challenge_pool'],'challenge_order':panel['challenge_order'],'families':arms,'policies':policies}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'PrimitiveMenuHelpPolicyV1_1Lock','sources':source_map(),'panels':panels(),'tasks':TASKS,'families':FAMILIES,'ops':OPS,'hint_oracle':HINT,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,'label_budget':LABEL_BUDGET,'post_singleton_challenge':POST_SINGLETON_CHALLENGE,'heldout_values':HELDOUT_VALUES},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources']:raise SystemExit('source drift')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};workers=[]
  for i,p in enumerate(lock['panels']):
   q=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=180)
   if q.returncode:raise RuntimeError(f'worker {i}: {q.stderr[-2500:]}')
   workers.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'PrimitiveMenuHelpPolicyV1_1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
