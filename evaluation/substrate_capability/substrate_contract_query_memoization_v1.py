#!/usr/bin/env python3
"""Paired source-locked pure-Term evaluation-cache benchmark."""
from __future__ import annotations
import hashlib,json,math,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_MEMOIZATION_V1_PREREG_20261001.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_contract_query_memoization_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_memoization_v1_lock_20261001.json'
RAW=ROOT/'evaluation/reports/substrate_contract_query_memoization_v1_raw_20261001.json'
REPS=2;SEED=20261103;CELLS=[('h32_n500',32,500),('h128_n28',128,28),('h512_n36',512,36)]
ACTIVE=('domains/contract_query.py','runners/dsl/src/term.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def active():
 sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')];import substrate_rs as sr
 r={p:sha(ROOT/p) for p in ACTIVE};r['native']=sha(Path(sr._native.__file__).resolve());return r
def term_for(i,k):
 v={'type':'Var','name':'x'};t=v
 for b,x in reversed(list(enumerate(range(-k,0)))):
  t={'type':'IfThenElse','cond':{'type':'Eq','a':v,'b':{'type':'Lit','value':x}},'then':{'type':'Lit','value':10*((i>>b)&1)},'other':t}
 return t
def cell_data(name,h,n):
 k=int(math.log2(h));xs=list(range(-k,0))+list(range(1,n-k+1))
 return {'cell':name,'H':h,'K':k,'N':n,'hypotheses':[{'id':f'h{i}','term':term_for(i,k)} for i in range(h)],
  'inputs':[{'x':x} for x in xs],'initial':[{'inputs':{'x':0},'expected':0}],'target_id':f'h{h//3}'}
def payload():return {'schema':'SubstrateContractQueryMemoizationV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL)},
 'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'design':{'cells':[cell_data(*c) for c in CELLS],'repetitions':REPS,'seed':SEED,'cache_arms':['off','on'],'pure_types':'domains/contract_query.py::_PURE_TERM_TYPES'}}
def value(i,k,x):
 for b,p in enumerate(range(-k,0)):
  if x==p:return 10*((i>>b)&1)
 return x
def noncacheable_control(native):
 from domains.contract_query import select_discriminating_input
 calls=0;cache={}
 def callback(term,env):
  nonlocal calls
  calls+=1
  return (1 if env['x']==1 else 0) if term.get('concept')=='left' else 0
 hs=[{'id':'left','term':{'type':'Holds','concept':'left'}},{'id':'right','term':{'type':'Holds','concept':'right'}}]
 r=select_discriminating_input(callback,hs,[{'x':1}],[{'inputs':{'x':0},'expected':0}],evaluation_cache=cache)
 return {'result':r,'callback_calls':calls,'cache_entries':len(cache)}
def worker(cell_name,rep,arm):
 os.environ.setdefault('OZMA_NO_LLM','1');lock=json.loads(LOCK.read_text());before=active()
 if before!=lock['active']:raise RuntimeError('active source differs from lock')
 import substrate_rs as sr
 from domains.contract_query import select_discriminating_input
 native=sr.Substrate()._inner;c=next(x for x in lock['design']['cells'] if x['cell']==cell_name)
 h=c['H'];k=c['K'];hs=c['hypotheses'];inputs=c['inputs'];target=int(c['target_id'][1:]);cache={};calls=0;obs=list(c['initial']);history=[];start=time.perf_counter_ns()
 def counted(term,env):
  nonlocal calls
  calls+=1;return native.evaluate(term,env)
 use_cache=arm=='on'
 for _ in range(k+1):
  r=select_discriminating_input(counted,hs,inputs,obs,evaluation_cache=cache if use_cache else None)
  if not r.get('ok'):
   terminal=r;break
  x=r['query']['x'];y=value(target,k,x)
  history.append({'query':r['query'],'entropy_bits':r['entropy_bits'],'predictions':r['predictions'],
   'survivors_before':r['surviving_hypotheses'],'oracle_output':y})
  obs.append({'inputs':r['query'],'expected':y})
 else:terminal={'ok':True,'reason':'budget exhausted'}
 elapsed=time.perf_counter_ns()-start
 bypass=noncacheable_control(native)
 after=active()
 cache_bytes=sum(len(key.encode())+len(json.dumps(val,separators=(',',':')).encode()) for key,val in cache.items())
 return {'kind':'worker','cell':cell_name,'rep':rep,'arm':arm,'pid':os.getpid(),'before':before,'after':after,'source_stable':before==after,
  'H':h,'K':k,'N':len(inputs),'target_id_for_analysis_only':c['target_id'],'history':history,'terminal':terminal,
  'native_evaluation_calls':calls,'cache_entries':len(cache),'cache_serialized_bytes':cache_bytes,'selection_elapsed_ns':elapsed,
  'noncacheable_control':bypass,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 cur=payload()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=cur:raise SystemExit('missing/stale lock')
 if RAW.exists():raise SystemExit('refusing overwrite capture')
 schedule=[(name,r,arm) for name,_,_ in CELLS for r in range(1,REPS+1) for arm in ('off','on')];random.Random(SEED).shuffle(schedule)
 env=dict(os.environ,OZMA_NO_LLM='1');env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 ws=[];t=time.perf_counter()
 for i,(name,rep,arm) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',name,str(rep),arm],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  row=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else {'kind':'worker_error','cell':name,'rep':rep,'arm':arm,'error':p.stderr[-4000:]}
  ws.append(row);print(f'{i}/12 {name} r={rep} cache={arm}: {row["kind"]}',flush=True)
 post=payload();RAW.write_text(json.dumps({'schema':'SubstrateContractQueryMemoizationV1Capture','lock':cur,'post_lock':post,
  'schedule':[{'cell':c,'rep':r,'arm':a} for c,r,a in schedule],'workers':ws,'elapsed_seconds':time.perf_counter()-t,
  'environment':{'python':sys.version,'platform':platform.platform()}},indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'workers':len(ws),'errors':sum(w.get('kind')!='worker' for w in ws),'stable':cur==post}))
if __name__=='__main__':
 if len(sys.argv)==5 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),sys.argv[4]),sort_keys=True,default=str))
 else:main()
