#!/usr/bin/env python3
"""Independent-axis scaling for finite Term disagreement query selection."""
from __future__ import annotations
import hashlib,json,math,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_SCALE_FACTORS_V1_PREREG_20261001.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_contract_query_scale_factors_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_scale_factors_v1_lock_20261001.json'
RAW=ROOT/'evaluation/reports/substrate_contract_query_scale_factors_v1_raw_20261001.json'
REPS=2;SEED=20261101
CELLS=[('baseline',32,0,20),('h256',256,0,32),('h512',512,0,36),('d16',32,16,20),('d64',32,64,20),('n100',32,0,100),('n500',32,0,500)]
ACTIVE=('domains/contract_query.py','runners/dsl/src/term.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def active():
 sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')];import substrate_rs as sr
 r={p:sha(ROOT/p) for p in ACTIVE};r['native']=sha(Path(sr._native.__file__).resolve());return r
def make_term(index,k,padding):
 var={'type':'Var','name':'x'};term=var
 for bit,point in reversed(list(enumerate(range(-k,0)))):
  term={'type':'IfThenElse','cond':{'type':'Eq','a':var,'b':{'type':'Lit','value':point}},'then':{'type':'Lit','value':10*((index>>bit)&1)},'other':term}
 for i in range(padding):
  term={'type':'IfThenElse','cond':{'type':'Eq','a':{'type':'Lit','value':-1000-i},'b':{'type':'Lit','value':-2000-i}},
        'then':{'type':'Lit','value':999999},'other':term}
 return term
def cells():
 out=[]
 for name,h,d,n in CELLS:
  k=int(math.log2(h));assert 2**k==h and n>=k
  points=list(range(-k,0));grid=points+list(range(1,n-k+1))
  out.append({'cell':name,'H':h,'K':k,'D':d,'N':n,'hypotheses':[{'id':f'h{i}','term':make_term(i,k,d)} for i in range(h)],
   'candidate_inputs':[{'x':x} for x in grid],'initial_observations':[{'inputs':{'x':0},'expected':0}],
   'target_id':f'h{h//3}'})
 return out
def payload():return {'schema':'SubstrateContractQueryScaleFactorsV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL)},
  'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'design':{'cells':cells(),'repetitions':REPS,'seed':SEED,'selector':'domains.contract_query.select_discriminating_input','target_id_not_passed_to_selector':True}}
def code_value(i,k,x):
 for bit,point in enumerate(range(-k,0)):
  if x==point:return 10*((i>>bit)&1)
 return x
def worker(cell_name,rep,cell_index):
 os.environ.setdefault('OZMA_NO_LLM','1');lock=json.loads(LOCK.read_text());before=active()
 if before!=lock['active']:raise RuntimeError('active source differs from lock')
 import substrate_rs as sr
 from domains.contract_query import select_discriminating_input
 native=sr.Substrate()._inner;cell=next(c for c in lock['design']['cells'] if c['cell']==cell_name)
 hs=cell['hypotheses'];h=cell['H'];k=cell['K'];d=cell['D'];grid=cell['candidate_inputs'];target=int(cell['target_id'][1:])
 # Closed-form oracle for every generated Term and input.
 for i,item in enumerate(hs):
  for x in (-k,0,1,k):
   if native.evaluate(item['term'],{'x':x})!=code_value(i,k,x):raise RuntimeError('Term disagrees with closed-form hypothesis')
 calls=0;obs=list(cell['initial_observations']);history=[];started=time.perf_counter_ns()
 def counted(term,env):
  nonlocal calls
  calls+=1;return native.evaluate(term,env)
 for _ in range(k+1):
  result=select_discriminating_input(counted,hs,grid,obs)
  if not result.get('ok'):
   terminal=result;break
  env=result['query'];x=env['x'];label=code_value(target,k,x)
  history.append({'query':env,'entropy_bits':result['entropy_bits'],'survivors_before':result['surviving_hypotheses'],
   'predictions':result['predictions'],'oracle_output':label})
  obs.append({'inputs':env,'expected':label})
 else:terminal={'ok':True,'reason':'budget exhausted'}
 elapsed=time.perf_counter_ns()-started;after=active()
 return {'kind':'worker','cell':cell_name,'rep':rep,'pid':os.getpid(),'source_stable':before==after,'before':before,'after':after,
  'H':h,'K':k,'D':d,'N':len(grid),'target_id_for_analysis_only':cell['target_id'],'initial_observations':cell['initial_observations'],
  'history':history,'terminal':terminal,'native_evaluation_calls':calls,'selection_elapsed_ns':elapsed,
  'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 current=payload()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=current:raise SystemExit('missing/stale lock')
 if RAW.exists():raise SystemExit('refusing overwrite capture')
 schedule=[(name,r,i) for i,(name,_,_,_) in enumerate(CELLS) for r in range(1,REPS+1)];random.Random(SEED).shuffle(schedule)
 env=dict(os.environ,OZMA_NO_LLM='1');env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 rows=[];start=time.perf_counter()
 for idx,(name,rep,cell_index) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',name,str(rep),str(cell_index)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  row=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else {'kind':'worker_error','cell':name,'rep':rep,'error':p.stderr[-4000:]}
  rows.append(row);print(f'{idx}/14 {name} r={rep}: {row["kind"]}',flush=True)
 post=payload();RAW.write_text(json.dumps({'schema':'SubstrateContractQueryScaleFactorsV1Capture','lock':current,'post_lock':post,
  'schedule':[{'cell':n,'rep':r} for n,r,_ in schedule],'workers':rows,'elapsed_seconds':time.perf_counter()-start,
  'environment':{'python':sys.version,'platform':platform.platform()}},indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'workers':len(rows),'errors':sum(w.get('kind')!='worker' for w in rows),'stable':current==post}))
if __name__=='__main__':
 if len(sys.argv)==5 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),int(sys.argv[4])),sort_keys=True,default=str))
 else:main()
