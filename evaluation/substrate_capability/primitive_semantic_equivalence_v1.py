#!/usr/bin/env python3
"""Paired original/zero-aware query domains with finite behavior classes."""
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/PRIMITIVE_SEMANTIC_EQUIVALENCE_V1_PREREG_20261003.md';ANALYZER=ROOT/'evaluation/substrate_capability/analyze_primitive_semantic_equivalence_v1.py';LOCK=ROOT/'evaluation/substrate_capability/primitive_semantic_equivalence_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_20261003.json'
UPLOCK=ROOT/'evaluation/substrate_capability/primitive_menu_help_policy_v1_1_lock_20261003.json';UPRAW=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_1_20261003.json';UPAN=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_1_analysis_20261003.json';UPSEM=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_1_semantic_addendum_20261003.json';UPSEM_SCRIPT=ROOT/'evaluation/substrate_capability/analyze_primitive_menu_help_semantic_addendum_v1.py'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('additive','product','ordering','opposition','inequality');KEYS=('ax','ay','ex','ey');DOMAIN=(-3.,-2.,-1.,0.,1.,2.,3.);HELDOUT=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5);MAX_SIZE=7;TIMEOUT=6.;MAX_SOLUTIONS=64;BUDGET=6;CHALLENGE=2;FAMILIES=('Base','Plus','Times','Lt','Not');OPS={'Base':('Neg','Eq','And'),'Plus':('Neg','Eq','And','Plus'),'Times':('Neg','Eq','And','Times'),'Lt':('Neg','Eq','And','Lt'),'Not':('Neg','Eq','And','Not')};HINT={'additive':'Plus','product':'Times','ordering':'Lt','opposition':'Base','inequality':'Not'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(row):return dict(zip(KEYS,map(float,row)))
def truth(t,r):
 if t=='additive':return r[0]+r[1]==r[2]+r[3]
 if t=='product':return r[0]*r[1]==r[2]*r[3]
 if t=='ordering':return r[0]<r[2]
 if t=='opposition':return r[0]==-r[2]
 return r[0]!=r[2]
def score(n,t,term):
 tp=fp=fn=tn=invalid=0
 for row in itertools.product(HELDOUT,repeat=4):
  if row==(0.,0.,0.,0.):continue
  try:v=n.evaluate(term,env(row))
  except Exception:invalid+=1;continue
  y=truth(t,row)
  if type(v)is not bool:invalid+=1
  elif v and y:tp+=1
  elif v:fp+=1
  elif y:fn+=1
  else:tn+=1
 return {'n':6560,'exact':not invalid and not fp and not fn,'invalid':invalid,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def upstream():
 l=json.loads(UPLOCK.read_text());d=json.loads(UPRAW.read_text());a=json.loads(UPAN.read_text())
 if d['sources']!=l['sources'] or d['lock_sha256']!=sha(UPLOCK) or a['passed']!=a['total']:raise RuntimeError('upstream v1.1 evidence invalid')
 return l,d
def panels():
 lock,raw=upstream();source_panels=lock['panels'];workers={(w['task'],w['worker']):w for w in raw['workers']};out=[];special=[(0.,1.,1.,1.),(1.,1.,0.,1.),(0.,-1.,1.,-1.),(-1.,1.,0.,1.)]
 allrows=list(itertools.product(DOMAIN,repeat=4))
 for p in source_panels:
  if p['task'] not in TASKS:continue
  rng=random.Random(p['seed']+880001);train={tuple(x['row']) for x in p['training']};sel=[r for r in special if r not in train];choices=[r for r in allrows if r not in train and r not in sel and r!=(0.,0.,0.,0.)];rng.shuffle(choices);sel+=choices[:28];remaining=[r for r in choices[28:] if r not in sel];rng.shuffle(remaining);chall=remaining[:32];so=list(sel);co=list(chall);random.Random(p['seed']+990001).shuffle(so);random.Random(p['seed']+990002).shuffle(co)
  w=workers[(p['task'],p['worker'])];hyps=[{'id':h['id'],'family':h['family'],'term':h['term']} for arm in w['families'] for h in arm['hypotheses']]
  out.append({'task':p['task'],'worker':p['worker'],'seed':p['seed'],'training':p['training'],'original_selection_pool':p['selection_pool'],'original_selection_order':p['selection_order'],'original_challenge_order':p['challenge_order'],'zero_selection_pool':[list(x) for x in sel],'zero_selection_order':[list(x) for x in so],'zero_challenge_pool':[list(x) for x in chall],'zero_challenge_order':[list(x) for x in co],'initial_hypotheses':hyps})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 files=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER,UPLOCK,UPRAW,UPAN,UPSEM,UPSEM_SCRIPT]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def signatures(native,hyps,rows):
 groups={}
 for h in hyps:
  sig=[]
  for row in rows:
   try:v=native.evaluate(h['term'],env(row));sig.append([type(v).__name__,v])
   except Exception as e:sig.append(['error',type(e).__name__])
  key=json.dumps(sig,separators=(',',':'),sort_keys=True);groups.setdefault(key,[]).append(h['id'])
 return [sorted(v) for v in groups.values()]
def policy(panel,hyps,domain,oracle):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 n=_native.Substrate();surv=list(hyps);steps=[];obs=[];used=[];selector_ns=0;kind=domain
 sp=panel['original_selection_order'] if domain=='original' else panel['zero_selection_order'];cp=panel['original_challenge_order'] if domain=='original' else panel['zero_challenge_order'];stop='empty' if not surv else ''
 while surv and len(steps)<BUDGET:
  if len(surv)==1 and sum(s['phase']=='challenge' for s in steps)>=CHALLENGE:stop='singleton_after_challenge';break
  if len(surv)==1:
   row=next((x for x in cp if x not in used),None)
   if row is None:stop='challenge_pool_exhausted';break
   q=env(row);phase='challenge';pred=[];ent=None
  else:
   avail=[env(x) for x in sp if x not in used]
   if not avail:stop='query_pool_exhausted';break
   t=time.perf_counter_ns();choice=select_discriminating_input(lambda term,e:n.evaluate(term,e),surv,avail,obs);selector_ns+=time.perf_counter_ns()-t
   if not choice.get('ok'):stop='selector_abstention';break
   q=choice['query'];row=[float(q[k]) for k in KEYS];phase='selection';pred=choice.get('predictions',[]);ent=choice.get('entropy_bits')
  label=bool(oracle(q));before=len(surv);kept=[]
  for h in surv:
   try:v=n.evaluate(h['term'],q)
   except Exception:continue
   if type(v)is bool and v==label:kept.append(h)
  surv=kept;used.append(row);obs.append({'inputs':q,'expected':label});steps.append({'phase':phase,'row':list(row),'input_env':q,'label':label,'before':before,'after':len(surv),'predictions':pred,'entropy_bits':ent})
  if not surv:stop='empty'
 if not stop:stop='label_budget'
 if len(surv)==1 and sum(s['phase']=='challenge' for s in steps)>=CHALLENGE:stop='singleton_after_challenge'
 full_rows=(panel['original_selection_pool']+panel['original_challenge_order']) if domain=='original' else (panel['zero_selection_pool']+panel['zero_challenge_pool'])
 classes=signatures(n,surv,full_rows)
 trigger=stop in ('empty','selector_abstention','query_pool_exhausted','challenge_pool_exhausted','label_budget')
 return {'domain':domain,'steps':steps,'calls':len(steps),'selector_ns':selector_ns,'stop':stop,'survivors':surv,'equivalence_classes':classes,'help_trigger':trigger}
def help_branch(panel,run):
 from domains.generator import synthesize
 from substrate_rs import _native
 if not run['help_trigger']:return None
 family=HINT[panel['task']];n=_native.Substrate();examples=[(env(x['row']),float(x['label'])) for x in panel['training']];t=time.perf_counter_ns();v=synthesize(n,examples,ops=OPS[family],consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=[env(x) for x in panel['zero_selection_pool']],max_solutions=MAX_SOLUTIONS,saturate_k=999999);wall=time.perf_counter_ns()-t;hs=[] if not v else [{'id':family+f'{i:03d}','family':family,'term':h['term'].to_dict(),'heldout':score(n,panel['task'],h['term'].to_dict())} for i,h in enumerate(v.get('hypotheses',[]))]
 return {'help_calls':1,'hinted_family':family,'wall_ns':wall,'candidate_count':len(hs),'halt_reason':None if not v else v.get('halt_reason'),'hypotheses':hs}
def worker(panel):
 from substrate_rs import _native
 task=panel['task'];n=_native.Substrate();hyps=panel['initial_hypotheses'];out=[]
 inputs={k:panel[k] for k in ('training','original_selection_pool','original_selection_order','original_challenge_order','zero_selection_pool','zero_selection_order','zero_challenge_pool','zero_challenge_order')}
 oracle=lambda e:truth(task,tuple(float(e[k]) for k in KEYS))
 for d in ('original','zero_aware'):
  run=policy(inputs,hyps,d,oracle);run['scored_survivors']=[{'id':h['id'],'family':h['family'],'term':h['term'],'heldout':score(n,task,h['term'])} for h in run.pop('survivors')];run['help']=help_branch(panel,run);out.append(run)
 return {'task':task,'worker':panel['worker'],'training':panel['training'],'initial_hypothesis_ids':[h['id'] for h in hyps],'original':out[0],'zero_aware':out[1]}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'PrimitiveSemanticEquivalenceV1Lock','sources':source_map(),'panels':panels(),'tasks':TASKS,'domain_values':DOMAIN,'heldout_values':HELDOUT,'heldout_count':6560,'families':FAMILIES,'ops':OPS,'hint_oracle':HINT,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,'query_budget':BUDGET,'post_singleton_challenge':CHALLENGE},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources']:raise SystemExit('source drift')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};workers=[]
  for i,p in enumerate(l['panels']):
   q=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=120)
   if q.returncode:raise RuntimeError(f'worker {i}: {q.stderr[-2000:]}')
   workers.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'PrimitiveSemanticEquivalenceV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
