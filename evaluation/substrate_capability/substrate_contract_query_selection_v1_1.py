#!/usr/bin/env python3
"""Locked native-runtime evaluation of finite-hypothesis query selection."""
from __future__ import annotations
import hashlib,json,math,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_SELECTION_V1_1_PREREG_20261001.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_contract_query_selection_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_selection_v1_1_lock_20261001.json'
RAW=ROOT/'evaluation/reports/substrate_contract_query_selection_v1_1_raw_20261001.json'
V={'type':'Var','name':'x'}
TASKS={
 'curvature':{'hypotheses':[['identity',V],['square',{'type':'Times','items':[V,V]}],['absolute',{'type':'Abs','arg':V}]],
  'observations':[{'inputs':{'x':0},'expected':0},{'inputs':{'x':1},'expected':1}],'target':'square'},
 'direction':{'hypotheses':[['identity',V],['square',{'type':'Times','items':[V,V]}],['negative',{'type':'Neg','arg':V}]],
  'observations':[{'inputs':{'x':0},'expected':0}],'target':'negative'},
 'polynomial':{'hypotheses':[['square',{'type':'Times','items':[V,V]}],['cube',{'type':'Times','items':[V,V,V]}],['absolute',{'type':'Abs','arg':V}]],
  'observations':[{'inputs':{'x':0},'expected':0},{'inputs':{'x':1},'expected':1}],'target':'cube'},
}
def coded_term(index):
 term=V
 for bit,point in reversed(list(enumerate((-5,-4,-3)))):
  term={'type':'IfThenElse','cond':{'type':'Eq','a':V,'b':{'type':'Lit','value':point}},
        'then':{'type':'Lit','value':10*((index>>bit)&1)},'other':term}
 return term
TASKS['coded_eight']={'hypotheses':[[f'h{i}',coded_term(i)] for i in range(8)],
 'observations':[{'inputs':{'x':0},'expected':0},{'inputs':{'x':1},'expected':1}],'target':'h5'}
GRID=[{'x':x} for x in range(-5,6)];REPS=2;RANDOM_TRIALS=2000;SEED=20261029
ACTIVE=('domains/contract_query.py','runners/dsl/src/term.rs','runners/dsl/src/py.rs',
 'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def active():
 sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')];import substrate_rs as sr
 r={p:sha(ROOT/p) for p in ACTIVE};r['native']=sha(Path(sr._native.__file__).resolve());return r
def payload():return {'schema':'SubstrateContractQuerySelectionV1_1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL)},
 'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'design':{'tasks':TASKS,'candidate_inputs':GRID,'repetitions':REPS,'random_trials':RANDOM_TRIALS,'seed':SEED,
 'selector':'domains.contract_query.select_discriminating_input','target_not_passed_to_selector':True}}
def formula(name,x):
 if name.startswith('h') and name[1:].isdigit():
  index=int(name[1:])
  return {point:10*((index>>bit)&1) for bit,point in enumerate((-5,-4,-3))}.get(x,x)
 return {'identity':lambda x:x,'square':lambda x:x*x,'absolute':lambda x:abs(x),'negative':lambda x:-x,
         'cube':lambda x:x*x*x}[name](x)
def random_counts(task,rep):
 row=TASKS[task];names=[n for n,_ in row['hypotheses']];target=row['target'];initial=row['observations'];counts=[]
 rng=random.Random(SEED+rep*101+list(TASKS).index(task)*10007)
 for _ in range(RANDOM_TRIALS):
  survivors=list(names);obs=list(initial);order=list(range(-5,6));rng.shuffle(order);n=0
  for x in order:
   if any(o['inputs']['x']==x for o in obs):continue
   y=formula(target,x);obs.append({'inputs':{'x':x},'expected':y});n+=1
   survivors=[name for name in survivors if formula(name,x)==y]
   if len(survivors)<=1:break
  counts.append(n)
 return counts
def worker(task,rep):
 os.environ.setdefault('OZMA_NO_LLM','1');lock=json.loads(LOCK.read_text());before=active()
 if before!=lock['active']:raise RuntimeError('active source differs from lock')
 import substrate_rs as sr
 from domains.contract_query import select_discriminating_input
 native=sr.Substrate()._inner;spec=TASKS[task];hyp=[{'id':n,'term':t} for n,t in spec['hypotheses']]
 # Validate native Terms against separately coded formulas before measuring selection.
 for name,term in spec['hypotheses']:
  for x in (-3,0,2):
   if native.evaluate(term,{'x':x})!=formula(name,x):raise RuntimeError('fixture Term disagrees with independent formula')
 target=spec['target'];observations=list(spec['observations']);history=[];start=time.perf_counter_ns()
 for _ in range(len(hyp)):
  selected=select_discriminating_input(native.evaluate,hyp,GRID,observations)
  if not selected.get('ok'):break
  env=selected['query'];expected=native.evaluate(dict(spec['hypotheses'])[target],env)
  history.append({'query':env,'entropy_bits':selected['entropy_bits'],'partition_count':selected['partition_count'],
   'survivors_before':selected['surviving_hypotheses'],'predictions':selected['predictions'],'oracle_output':expected})
  observations.append({'inputs':env,'expected':expected})
 elapsed=time.perf_counter_ns()-start
 surviving=select_discriminating_input(native.evaluate,hyp,GRID,observations)
 after=active()
 return {'kind':'worker','task':task,'rep':rep,'pid':os.getpid(),'source_stable':before==after,'before':before,'after':after,
  'hypothesis_ids':[n for n,_ in spec['hypotheses']],'target_id_for_analysis_only':target,
  'initial_observations':spec['observations'],'history':history,'final_selector_status':surviving,
  'selector_elapsed_ns':elapsed,'random_query_counts':random_counts(task,rep),
  'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 current=payload()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=current:raise SystemExit('missing/stale lock')
 if RAW.exists():raise SystemExit('refusing overwrite capture')
 schedule=[(task,rep) for task in TASKS for rep in range(1,REPS+1)];random.Random(SEED).shuffle(schedule)
 env=dict(os.environ,OZMA_NO_LLM='1');env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 workers=[];start=time.perf_counter()
 for i,(task,rep) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',task,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  row=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else {'kind':'worker_error','task':task,'rep':rep,'error':p.stderr[-4000:]}
  workers.append(row);print(f'{i}/8 {task} r={rep}: {row["kind"]}',flush=True)
 post=payload();RAW.write_text(json.dumps({'schema':'SubstrateContractQuerySelectionV1_1Capture','lock':current,'post_lock':post,
  'schedule':[{'task':t,'rep':r} for t,r in schedule],'workers':workers,'elapsed_seconds':time.perf_counter()-start,
  'environment':{'python':sys.version,'platform':platform.platform()}},indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'workers':len(workers),'errors':sum(w.get('kind')!='worker' for w in workers),'stable':current==post}))
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,default=str))
 else:main()
