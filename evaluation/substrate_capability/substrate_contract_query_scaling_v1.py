#!/usr/bin/env python3
"""Locked scale and open-world probes for finite Term disagreement search."""
from __future__ import annotations
import hashlib,json,math,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_SCALING_V1_PREREG_20261001.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_contract_query_scaling_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_scaling_v1_lock_20261001.json'
RAW=ROOT/'evaluation/reports/substrate_contract_query_scaling_v1_raw_20261001.json'
REPS=2;RANDOM_TRIALS=2000;SEED=20261031
CASES=[('scale_h8',8),('scale_h32',32),('scale_h128',128),('open_alias_h32',32),('open_conflict_h32',32)]
ACTIVE=('domains/contract_query.py','runners/dsl/src/term.rs','runners/dsl/src/py.rs',
 'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def active():
 sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')];import substrate_rs as sr
 r={p:sha(ROOT/p) for p in ACTIVE};r['native']=sha(Path(sr._native.__file__).resolve());return r
def make_hypotheses(h):
 k=int(math.log2(h));points=list(range(-k,0));var={'type':'Var','name':'x'};out=[]
 for i in range(h):
  term=var
  for bit,point in reversed(list(enumerate(points))):
   term={'type':'IfThenElse','cond':{'type':'Eq','a':var,'b':{'type':'Lit','value':point}},
         'then':{'type':'Lit','value':10*((i>>bit)&1)},'other':term}
  out.append({'id':f'h{i}','term':term})
 return out,points
def design():
 cases=[]
 for name,h in CASES:
  k=int(math.log2(h));hyp,points=make_hypotheses(h);grid=points+list(range(1,3*k+1));
  item={'case':name,'hypotheses':hyp,'initial_observations':[{'inputs':{'x':0},'expected':0}],
        'candidate_inputs':[{'x':x} for x in grid],'target_id':f'h{h//3}','K':k}
  if name=='open_alias_h32':item['alias_decoy']=3*k
  if name=='open_conflict_h32':item['initial_observations']=[{'inputs':{'x':0},'expected':1}]
  cases.append(item)
 return cases
def payload():return {'schema':'SubstrateContractQueryScalingV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL)},
  'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'design':{'cases':design(),'repetitions':REPS,'random_trials':RANDOM_TRIALS,'seed':SEED,
            'selector':'domains.contract_query.select_discriminating_input','target_id_not_passed_to_selector':True}}
def code_value(index,k,x):
 for bit,point in enumerate(range(-k,0)):
  if x==point:return 10*((index>>bit)&1)
 return x
def target_value(index,k,x,alias_decoy=None):
 y=code_value(index,k,x)
 return y+100 if alias_decoy is not None and x==alias_decoy else y
def random_counts(h,k,target,grid,initial,case_index,rep):
 rng=random.Random(SEED+case_index*1009+rep*79);counts=[]
 for _ in range(RANDOM_TRIALS):
  survivors=list(range(h));obs=list(initial);order=list(grid);rng.shuffle(order);n=0
  for x in order:
   if any(o['inputs']['x']==x for o in obs):continue
   y=code_value(target,k,x);obs.append({'inputs':{'x':x},'expected':y});n+=1
   survivors=[i for i in survivors if code_value(i,k,x)==y]
   if len(survivors)<=1:break
  counts.append(n)
 return counts
def run_selector(native,hyp,grid,initial,target_index,k,alias_decoy=None):
 from domains.contract_query import select_discriminating_input
 observations=list(initial);history=[];calls=0;started=time.perf_counter_ns()
 def counted(term,env):
  nonlocal calls
  calls+=1;return native.evaluate(term,env)
 for _ in range(k+2):
  result=select_discriminating_input(counted,hyp,grid,observations)
  if not result.get('ok'):
   terminal=result;break
  env=result['query'];x=env['x'];label=target_value(target_index,k,x,alias_decoy)
  history.append({'query':env,'entropy_bits':result['entropy_bits'],'partition_count':result['partition_count'],
   'survivors_before':result['surviving_hypotheses'],'predictions':result['predictions'],'oracle_output':label})
  observations.append({'inputs':env,'expected':label})
 else:terminal={'ok':True,'reason':'query budget exhausted'}
 return history,terminal,calls,time.perf_counter_ns()-started
def worker(case_name,rep,case_index):
 os.environ.setdefault('OZMA_NO_LLM','1');lock=json.loads(LOCK.read_text());before=active()
 if before!=lock['active']:raise RuntimeError('active source differs from lock')
 import substrate_rs as sr
 from domains.contract_query import select_discriminating_input
 native=sr.Substrate()._inner;case=next(c for c in lock['design']['cases'] if c['case']==case_name)
 h=len(case['hypotheses']);k=case['K'];hyp=case['hypotheses'];grid=case['candidate_inputs'];target_name=case['target_id'];target_index=int(target_name[1:])
 # Verify the generated Term family against a separate closed-form evaluator.
 for i,item in enumerate(hyp):
  for x in range(-k,3*k+1):
   if native.evaluate(item['term'],{'x':x})!=code_value(i,k,x):raise RuntimeError('native hypothesis differs from closed-form fixture')
 alias=case.get('alias_decoy');history,terminal,calls,elapsed=run_selector(native,hyp,grid,case['initial_observations'],target_index,k,alias)
 result={'kind':'worker','case':case_name,'rep':rep,'pid':os.getpid(),'source_stable':before==active(),'before':before,'after':active(),
  'hypothesis_count':h,'term_depth':k,'input_count':len(grid),'target_id_for_analysis_only':target_name,
  'initial_observations':case['initial_observations'],'history':history,'terminal':terminal,
  'native_evaluation_calls':calls,'selection_elapsed_ns':elapsed,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
 if case_name.startswith('scale_'):
  result['random_query_counts']=random_counts(h,k,target_index,[p['x'] for p in grid],case['initial_observations'],case_index,rep)
 if alias is not None:
  candidate_id=terminal.get('surviving_hypotheses',[None])[0] if len(terminal.get('surviving_hypotheses',[]))==1 else None
  result['heldout']={'input':{'x':alias},'candidate_id':candidate_id,
   'candidate_output':code_value(int(candidate_id[1:]),k,alias) if candidate_id else None,
   'oracle_output':target_value(target_index,k,alias,alias)}
 return result
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 current=payload()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=current:raise SystemExit('missing/stale lock')
 if RAW.exists():raise SystemExit('refusing overwrite capture')
 schedule=[(name,r,idx) for idx,(name,_) in enumerate(CASES) for r in range(1,REPS+1)];random.Random(SEED).shuffle(schedule)
 env=dict(os.environ,OZMA_NO_LLM='1');env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 rows=[];start=time.perf_counter()
 for i,(case,rep,idx) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',case,str(rep),str(idx)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  row=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else {'kind':'worker_error','case':case,'rep':rep,'error':p.stderr[-4000:]}
  rows.append(row);print(f'{i}/10 {case} r={rep}: {row["kind"]}',flush=True)
 post=payload();RAW.write_text(json.dumps({'schema':'SubstrateContractQueryScalingV1Capture','lock':current,'post_lock':post,
  'schedule':[{'case':c,'rep':r} for c,r,_ in schedule],'workers':rows,'elapsed_seconds':time.perf_counter()-start,
  'environment':{'python':sys.version,'platform':platform.platform()}},indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'workers':len(rows),'errors':sum(w.get('kind')!='worker' for w in rows),'stable':current==post}))
if __name__=='__main__':
 if len(sys.argv)==5 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),int(sys.argv[4])),sort_keys=True,default=str))
 else:main()
