#!/usr/bin/env python3
"""Coverage-aware expand/query/class-return/help policy on frozen panels."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/COVERAGE_AWARE_CLASS_RETURN_V1_PREREG_20261003.md';ANALYZER=ROOT/'evaluation/substrate_capability/analyze_coverage_aware_class_return_v1.py';LOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
UPLOCK=ROOT/'evaluation/substrate_capability/primitive_semantic_equivalence_v1_lock_20261003.json';UPRAW=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_20261003.json';UPAN=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_analysis_20261003.json';UPRUN=ROOT/'evaluation/substrate_capability/primitive_semantic_equivalence_v1.py'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
KEYS=('ax','ay','ex','ey');TASKS=('additive','product','ordering','opposition','inequality');FAMILIES=('Base','Plus','Times','Lt','Not');OPS={'Base':('Neg','Eq','And'),'Plus':('Neg','Eq','And','Plus'),'Times':('Neg','Eq','And','Times'),'Lt':('Neg','Eq','And','Lt'),'Not':('Neg','Eq','And','Not')};HINT={'additive':'Plus','product':'Times','ordering':'Lt','opposition':'Base','inequality':'Not'};LABEL_BUDGET=6;POST_SINGLETON_CHALLENGE=2;MIN_COVERAGE=-2.;MAX_COVERAGE=2.;REQUIRED_ZERO=True
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(row):return dict(zip(KEYS,map(float,row)))
def truth(task,r):
 if task=='additive':return r[0]+r[1]==r[2]+r[3]
 if task=='product':return r[0]*r[1]==r[2]*r[3]
 if task=='ordering':return r[0]<r[2]
 if task=='opposition':return r[0]==-r[2]
 return r[0]!=r[2]
def score(n,task,term):
 vals=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5);tp=fp=fn=tn=bad=0
 import itertools
 for row in itertools.product(vals,repeat=4):
  if row==(0.,0.,0.,0.):continue
  try:v=n.evaluate(term,env(row))
  except Exception:bad+=1;continue
  y=truth(task,row)
  if type(v)is not bool:bad+=1
  elif v and y:tp+=1
  elif v:fp+=1
  elif y:fn+=1
  else:tn+=1
 return {'n':6560,'exact':not bad and not fp and not fn,'invalid':bad,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def coverage(rows):
 vals={k:[float(row[i]) for row in rows] for i,k in enumerate(KEYS)}
 per={k:{'zero':0. in x,'min':min(x) if x else None,'max':max(x) if x else None,'negative_at_or_below_threshold':any(v<=MIN_COVERAGE for v in x),'positive_at_or_above_threshold':any(v>=MAX_COVERAGE for v in x)} for k,x in vals.items()}
 ok=all(v['zero'] and v['negative_at_or_below_threshold'] and v['positive_at_or_above_threshold'] for v in per.values())
 return {'adequate':ok,'per_variable':per,'probe_count':len(rows)}
def source_panels():
 lock=json.loads(UPLOCK.read_text());raw=json.loads(UPRAW.read_text());analysis=json.loads(UPAN.read_text())
 if raw['sources']!=lock['sources'] or raw['lock_sha256']!=sha(UPLOCK) or analysis['passed']!=analysis['total']:raise RuntimeError('upstream capture not valid')
 by={(w['task'],w['worker']):w for w in raw['workers']};out=[]
 for p in lock['panels']:
  w=by[(p['task'],p['worker'])];hyps=p['initial_hypotheses']
  out.append({'task':p['task'],'worker':p['worker'],'training':p['training'],'initial_hypotheses':hyps,'original_selection_order':p['original_selection_order'],'original_selection_pool':p['original_selection_pool'],'original_challenge_order':p['original_challenge_order'],'zero_selection_order':p['zero_selection_order'],'zero_selection_pool':p['zero_selection_pool'],'zero_challenge_order':p['zero_challenge_order'],'zero_challenge_pool':p['zero_challenge_pool'],'baseline_original_help_calls':int(bool(w['original']['help'])),'baseline_zero_help_calls':int(bool(w['zero_aware']['help']))})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER,UPLOCK,UPRAW,UPAN,UPRUN]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def teacher_synthesis(panel,family,examples,probes):
 from substrate_rs import _native
 from domains.generator import synthesize
 n=_native.Substrate();t=time.perf_counter_ns();v=synthesize(n,[(env(x['row']),float(x['label'])) for x in panel['training']],ops=OPS[family],consts=(),max_size=7,timeout_s=6.,include_output_constants=False,probe_envs=[env(x) for x in probes],max_solutions=64,saturate_k=999999);elapsed=time.perf_counter_ns()-t
 terms=[] if not v else [{'id':family+f'{i:03d}','family':family,'term':h['term'].to_dict(),'heldout':score(n,panel['task'],h['term'].to_dict())} for i,h in enumerate(v.get('hypotheses',[]))]
 return {'family':family,'wall_ns':elapsed,'candidate_count':len(terms),'halt_reason':None if not v else v.get('halt_reason'),'hypotheses':terms}
def run_policy(panel):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 n=_native.Substrate();task=panel['task'];hyp=list(panel['initial_hypotheses']);oracle=lambda e:truth(task,tuple(float(e[k]) for k in KEYS));obs=[];used=[];steps=[];selector_ns=0;domain='original';expandations=[];stop='empty' if not hyp else '';decision='';class_result=None;helper=None
 while hyp and len(steps)<LABEL_BUDGET:
  if len(hyp)==1 and sum(x['phase']=='challenge' for x in steps)>=POST_SINGLETON_CHALLENGE:stop='singleton_after_challenge';decision='exact_term';break
  if len(hyp)==1:
   challenge=panel['original_challenge_order'] if domain=='original' else panel['zero_challenge_order'];row=next((x for x in challenge if x not in used),None)
   if row is None:stop='challenge_pool_exhausted';break
   q=env(row);phase='challenge';pred=[];entropy=None
  else:
   pool=panel['original_selection_order'] if domain=='original' else panel['zero_selection_order']+panel['zero_challenge_order']
   available=[env(x) for x in pool if x not in used]
   if not available:stop='query_pool_exhausted';break
   t=time.perf_counter_ns();choice=select_discriminating_input(lambda term,e:n.evaluate(term,e),hyp,available,obs);selector_ns+=time.perf_counter_ns()-t
   if not choice.get('ok'):
    stop='selector_abstention'
    current=panel['original_selection_pool']+panel['original_challenge_order'] if domain=='original' else panel['original_selection_pool']+panel['original_challenge_order']+panel['zero_selection_pool']+panel['zero_challenge_pool']
    cov=coverage(current)
    if domain=='original' and not cov['adequate']:
     domain='zero_aware';expandations.append({'from':'original','to':'zero_aware','trigger':'insufficient_coverage','coverage':cov});continue
    class_result=partition_hypotheses_by_behavior(lambda term,e:n.evaluate(term,e),hyp,[env(x) for x in dict.fromkeys(tuple(r) for r in current)])
    if class_result.get('ok') and class_result['class_count']==1 and cov['adequate']:
     decision='behavior_class';break
    break
   q=choice['query'];row=[float(q[k]) for k in KEYS];phase='selection';pred=choice.get('predictions',[]);entropy=choice.get('entropy_bits')
  y=bool(oracle(q));before=len(hyp);kept=[]
  for h in hyp:
   try:v=n.evaluate(h['term'],q)
   except Exception:continue
   if type(v)is bool and v==y:kept.append(h)
  hyp=kept;used.append(row);obs.append({'inputs':q,'expected':y});steps.append({'phase':phase,'row':list(row),'input_env':q,'label':y,'before':before,'after':len(hyp),'predictions':pred,'entropy_bits':entropy})
  if not hyp:stop='empty';break
 if not stop:stop='label_budget'
 if not decision and stop=='singleton_after_challenge':decision='exact_term'
 current=panel['original_selection_pool']+panel['original_challenge_order'] if domain=='original' else panel['original_selection_pool']+panel['original_challenge_order']+panel['zero_selection_pool']+panel['zero_challenge_pool']
 cov=coverage(current)
 if not decision and hyp and stop in ('empty','selector_abstention','query_pool_exhausted','challenge_pool_exhausted','label_budget'):
  if class_result is None:class_result=partition_hypotheses_by_behavior(lambda term,e:n.evaluate(term,e),hyp,[env(x) for x in dict.fromkeys(tuple(r) for r in current)])
  if class_result.get('ok') and class_result['class_count']==1 and cov['adequate']:decision='behavior_class'
  else:
   stop='help_requested';family=HINT[task];helper=teacher_synthesis(panel,family,[],panel['zero_selection_pool']);decision='teacher_help'
 scored=[{'id':h['id'],'family':h['family'],'term':h['term'],'heldout':score(n,task,h['term'])} for h in hyp]
 return {'steps':steps,'calls':len(steps),'selector_ns':selector_ns,'domain':domain,'expansions':expandations,'coverage':cov,'stop':stop,'decision':decision,'survivors':scored,'behavior_partition':class_result,'teacher':helper}
def worker(panel):
 task=panel['task'];result=run_policy(panel);return {'task':task,'worker':panel['worker'],'training':panel['training'],'result':result}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'CoverageAwareClassReturnV1Lock','sources':source_map(),'panels':source_panels(),'tasks':TASKS,'coverage':{'required_zero':REQUIRED_ZERO,'minimum_value':MIN_COVERAGE,'maximum_value':MAX_COVERAGE,'variables':KEYS},'label_budget':LABEL_BUDGET,'post_singleton_challenge':POST_SINGLETON_CHALLENGE},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources']:raise SystemExit('source drift')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};workers=[]
  for i,p in enumerate(l['panels']):
   q=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=120)
   if q.returncode:raise RuntimeError(f'worker {i}: {q.stderr[-2500:]}')
   workers.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'CoverageAwareClassReturnV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
