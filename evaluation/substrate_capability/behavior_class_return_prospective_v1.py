#!/usr/bin/env python3
"""Fresh paired query/help/finite-class policy study."""
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/BEHAVIOR_CLASS_RETURN_PROSPECTIVE_V1_PREREG_20261003.md';AN=ROOT/'evaluation/substrate_capability/analyze_behavior_class_return_prospective_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/behavior_class_return_prospective_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/behavior_class_return_prospective_v1_20261003.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('additive','product','ordering','opposition','inequality');KEYS=('ax','ay','ex','ey');TRAIN_VALUES=(-3.,-2.,-1.,1.,2.,3.);ALL_VALUES=(-3.,-2.,-1.,0.,1.,2.,3.);HELDOUT=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5);FAMILIES=('Base','Plus','Times','Lt')
OPS={'Base':('Neg','Eq','And'),'Plus':('Neg','Eq','And','Plus'),'Times':('Neg','Eq','And','Times'),'Lt':('Neg','Eq','And','Lt'),'Not':('Neg','Eq','And','Not')};HINT={'additive':'Plus','product':'Times','ordering':'Lt','opposition':'Base','inequality':'Not'}
LABEL_BUDGET=6;POST_CHALLENGE=2;MAX_SIZE=7;TIMEOUT=6.;MAX_SOLUTIONS=64;WORKERS=5
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(t,r):
 if t=='additive':return r[0]+r[1]==r[2]+r[3]
 if t=='product':return r[0]*r[1]==r[2]*r[3]
 if t=='ordering':return r[0]<r[2]
 if t=='opposition':return r[0]==-r[2]
 return r[0]!=r[2]
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/x for x in SOURCES]+[HERE,PRE,AN]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def build_panels():
 from itertools import product
 train_domain=list(product(TRAIN_VALUES,repeat=4));all_domain=list(product(ALL_VALUES,repeat=4));panels=[]
 for ti,task in enumerate(TASKS):
  pos=[r for r in train_domain if truth(task,r)];neg=[r for r in train_domain if not truth(task,r)]
  for wi in range(WORKERS):
   seed=3103000+ti*100+wi;rng=random.Random(seed);training=rng.sample(pos,8)+rng.sample(neg,8);train=set(training)
   available_non=[r for r in train_domain if r not in train];rng.shuffle(available_non);nz_sel=available_non[:32];nz_ch=available_non[32:64]
   available_zero=[r for r in all_domain if r not in train];rng2=random.Random(seed+50000)
   def stratified(exclude):
    pool=[r for r in available_zero if r not in exclude];picked=[]
    z=[r for r in pool if 0. in r];b=[r for r in pool if any(abs(v)==3. for v in r) and 0. not in r]
    general=[r for r in pool if 0. not in r and not any(abs(v)==3. for v in r)]
    picked.extend(rng2.sample(z,min(8,len(z))));picked.extend(rng2.sample(b,min(8,len(b))))
    remain=[r for r in general if r not in picked];picked.extend(rng2.sample(remain,32-len(picked)))
    return picked
   zsel=stratified(set());zch=stratified(set(zsel));
   for pset in (nz_sel,nz_ch,zsel,zch):
    if len(pset)!=32 or len(set(pset))!=32 or set(pset)&train:raise RuntimeError('invalid panel pool')
   if set(nz_sel)&set(nz_ch) or set(zsel)&set(zch):raise RuntimeError('overlapping selection/challenge pools')
   panel={'task':task,'worker':wi,'seed':seed,'training':[{'row':list(r),'label':int(truth(task,r))} for r in training]}
   for name,values,offset in (('nonzero',nz_sel,10000),('nonzero_challenge',nz_ch,20000),('zero_aware',zsel,30000),('zero_aware_challenge',zch,40000)):
    order=list(values);random.Random(seed+offset).shuffle(order);panel[name+'_pool']=[list(x) for x in values];panel[name+'_order']=[list(x) for x in order]
   panels.append(panel)
 return panels
def generate(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 native=_native.Substrate();examples=[(env(x['row']),float(x['label'])) for x in panel['training']];probe=[env(r) for r in panel['nonzero_pool']];arms=[];total_ns=0;explored=0
 for family in FAMILIES:
  start=time.perf_counter_ns();v=synthesize(native,examples,ops=OPS[family],consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=probe,max_solutions=MAX_SOLUTIONS,saturate_k=999999);ns=time.perf_counter_ns()-start;total_ns+=ns
  hypotheses=[] if not v else [{'id':family+':'+str(i),'family':family,'term':h['term'].to_dict()} for i,h in enumerate(v.get('hypotheses',[]))]
  explored+=0 if not v else int(v.get('explored',0) or 0);arms.append({'family':family,'wall_ns':ns,'explored':0 if not v else v.get('explored',0),'halt_reason':None if not v else v.get('halt_reason'),'hypotheses':hypotheses})
 return arms,total_ns,explored
def class_partition(native,survivors,pool):
 groups={};started=time.perf_counter_ns();evals=0
 for h in survivors:
  sig=[]
  for row in pool:
   try:v=native.evaluate(h['term'],env(row));key=[type(v).__name__,v]
   except Exception as e:key=['error',type(e).__name__]
   sig.append(key);evals+=1
  k=json.dumps(sig,sort_keys=True,separators=(',',':'));groups.setdefault(k,[]).append(h)
 ns=time.perf_counter_ns()-started
 return list(groups.values()),ns,evals
# (keep policy's action sequence independent of the hidden task label)
def run_policy(panel,hyps,domain,kind,oracle,help_callback,score_callback):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 n=_native.Substrate();surv=list(hyps);steps=[];used=[];obs=[];selector_ns=class_ns=class_evals=class_audit_ns=class_audit_evals=0;pool=panel[domain+'_pool']+panel[domain+'_challenge_pool'];select=panel[domain+'_order'];challenge=panel[domain+'_challenge_order'];stop='empty' if not surv else '';returned_class=None;decision_classes=[];class_checks=[]
 while surv and len(steps)<LABEL_BUDGET:
  if kind=='class':
   classes,ns,ne=class_partition(n,surv,pool);class_ns+=ns;class_evals+=ne;decision_classes=[[h['id'] for h in c] for c in classes];class_checks.append({'survivor_ids':[h['id'] for h in surv],'classes':decision_classes,'elapsed_ns':ns,'term_evaluations':ne})
   if len(classes)==1:returned_class=classes[0];stop='single_behavior_class';break
  if len(surv)==1:
   if sum(x['phase']=='challenge' for x in steps)>=POST_CHALLENGE:stop='singleton_after_challenge';break
   row=next((r for r in challenge if r not in used),None)
   if row is None:stop='challenge_pool_exhausted';break
   q=env(row);phase='challenge';pred=[]
  else:
   avail=[env(r) for r in select if r not in used]
   if not avail:stop='query_pool_exhausted';break
   start=time.perf_counter_ns();choice=select_discriminating_input(lambda term,e:n.evaluate(term,e),surv,avail,obs);selector_ns+=time.perf_counter_ns()-start
   if not choice.get('ok'):stop='selector_abstention';break
   q=choice['query'];row=[float(q[k]) for k in KEYS];phase='selection';pred=choice.get('predictions',[])
  label=bool(oracle(q));before=len(surv);next_surv=[]
  for h in surv:
   try:v=n.evaluate(h['term'],q)
   except Exception:continue
   if type(v)is bool and v==label:next_surv.append(h)
  surv=next_surv;used.append(row);obs.append({'inputs':q,'expected':label});steps.append({'phase':phase,'row':list(row),'before':before,'after':len(surv),'label':label,'predictions':pred})
  if not surv:stop='empty';break
  if len(surv)==1 and kind=='help':stop='candidate_singleton'
 if kind=='class' and returned_class is None and surv:
  classes,ns,ne=class_partition(n,surv,pool);class_ns+=ns;class_evals+=ne;decision_classes=[[h['id'] for h in c] for c in classes];class_checks.append({'survivor_ids':[h['id'] for h in surv],'classes':decision_classes,'elapsed_ns':ns,'term_evaluations':ne})
  if len(classes)==1:returned_class=classes[0];stop='single_behavior_class'
 if not stop:stop='label_budget'
 need_help=(returned_class is None and (not surv or stop in ('selector_abstention','query_pool_exhausted','challenge_pool_exhausted','label_budget')))
 help_result=None;help_ns=0
 if need_help:help_result=help_callback()
 out=returned_class if returned_class is not None else surv
 if help_result is not None:out=help_result['hypotheses']
 # Evaluation-only scoring after all policy actions.
 test_native=_native.Substrate();scored=[score_callback(h) for h in out]
 audit_classes,audit_ns,audit_evals=class_partition(n,surv,pool) if surv else ([],0,0);class_audit_ns+=audit_ns;class_audit_evals+=audit_evals
 return {'policy':kind,'domain':domain,'labels':len(steps),'steps':steps,'stop':stop,'survivor_count':len(surv),'survivor_ids_at_stop':[h['id'] for h in surv],'behavior_classes_at_stop':len(audit_classes),'audit_classes':[[h['id'] for h in c] for c in audit_classes],'decision_classes':decision_classes,'class_checks':class_checks,'returned_class_size':len(returned_class) if returned_class else 0,'returned_ids':[h['id'] for h in out],'returned_terms':[{'id':h['id'],'family':h['family'],'term':h['term']} for h in out],'returned_scores':scored,'all_returned_exact':bool(scored) and all(x['exact'] for x in scored),'help':help_result,'cost':{'selector_ns':selector_ns,'class_decision_ns':class_ns,'class_decision_term_evaluations':class_evals,'class_audit_ns':class_audit_ns,'class_audit_term_evaluations':class_audit_evals,'help_ns':0 if help_result is None else help_result['wall_ns']}}
def worker(panel):
 arms,synth_ns,explored=generate(panel);hyps=[h for a in arms for h in a['hypotheses']];policies=[]
 def oracle(q):return truth(panel['task'],tuple(float(q[k]) for k in KEYS))
 def help_callback():
  from substrate_rs import _native
  from domains.generator import synthesize
  hint=HINT[panel['task']];native=_native.Substrate();examples=[(env(x['row']),float(x['label'])) for x in panel['training']];start=time.perf_counter_ns();v=synthesize(native,examples,ops=OPS[hint],consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=[env(r) for r in panel['zero_aware_pool']],max_solutions=MAX_SOLUTIONS,saturate_k=999999);wall=time.perf_counter_ns()-start
  return {'calls':1,'family':hint,'wall_ns':wall,'halt_reason':None if not v else v.get('halt_reason'),'hypotheses':[] if not v else [{'id':'help:'+hint+':'+str(i),'family':hint,'term':h['term'].to_dict()} for i,h in enumerate(v.get('hypotheses',[]))]}
 values=[x for x in itertools.product(HELDOUT,repeat=4) if x!=(0.,0.,0.,0.)]
 def score_callback(h):
  from substrate_rs import _native
  n=_native.Substrate();bad=invalid=0
  for row in values:
   try:v=n.evaluate(h['term'],env(row))
   except Exception:invalid+=1;continue
   y=truth(panel['task'],row)
   if type(v)is not bool:invalid+=1
   elif v!=y:bad+=1
  return {'id':h['id'],'family':h['family'],'exact':bad==0 and invalid==0,'fp_fn_errors':bad,'invalid':invalid,'n':len(values)}
 policy_panel={k:v for k,v in panel.items() if k!='task'}
 for domain,kind in (('zero_aware','help'),('zero_aware','class'),('nonzero','class')):policies.append(run_policy(policy_panel,hyps,domain,kind,oracle,help_callback,score_callback))
 return {'task':panel['task'],'worker':panel['worker'],'seed':panel['seed'],'training':panel['training'],'family_searches':arms,'synthesis_total_ns':synth_ns,'synthesis_explored_total':explored,'policies':policies}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'BehaviorClassReturnProspectiveV1Lock','sources':source_map(),'panels':build_panels(),'tasks':TASKS,'families':FAMILIES,'ops':OPS,'hint_oracle':HINT,'all_values':ALL_VALUES,'heldout_values':HELDOUT,'label_budget':LABEL_BUDGET,'post_singleton_challenge':POST_CHALLENGE,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources']:raise SystemExit('source drift')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};workers=[]
  for i,p in enumerate(lock['panels']):
   q=subprocess.run([sys.executable,str(HERE),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=240)
   if q.returncode:raise RuntimeError(f'worker {i}: {q.stderr[-2500:]}')
   workers.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'BehaviorClassReturnProspectiveV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
