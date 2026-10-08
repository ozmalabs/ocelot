#!/usr/bin/env python3
"""Paired native resynthesis with and without a Term-audit residual."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/RESIDUAL_TRIGGERED_RESYNTHESIS_V1_PREREG_20261004.md';AMEND=ROOT/'docs/research/engine_substrate/RESIDUAL_TRIGGERED_RESYNTHESIS_V1_2_AMENDMENT_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_residual_triggered_resynthesis_v1_2.py'
UP=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1.py';UL=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1_lock_20261004.json';UR=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_20261004.json';UA=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_analysis_20261004.json'
TR=ROOT/'evaluation/substrate_capability/term_conditioned_audit_v1.py';TL=ROOT/'evaluation/substrate_capability/term_conditioned_audit_v1_lock_20261004.json';TRAW=ROOT/'evaluation/reports/term_conditioned_audit_v1_20261004.json';TA=ROOT/'evaluation/substrate_capability/analyze_term_conditioned_audit_v1.py';TO=ROOT/'evaluation/reports/term_conditioned_audit_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/residual_triggered_resynthesis_v1_2_lock_20261004.json';OUT=ROOT/'evaluation/reports/residual_triggered_resynthesis_v1_2_20261004.json'
OPS=('Plus','Times','Abs','Min');BASE=('Neg','Eq','And');KEYS=('ax','ay','ex','ey');HELD=(-2.5,-1.5,-.5,.5,1.5,2.5);BRANCH_TIMEOUT=2.0;MAX_SIZE=7;MAX_SOLUTIONS=64;SELECTOR_LABEL_BUDGET=8

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AMEND,AN,UP,UL,UR,UA,TR,TL,TRAW,TA,TO,ROOT/'domains/generator.py',ROOT/'domains/contract_query.py',ROOT/'runners/dsl/src/grammar.rs',ROOT/'runners/dsl/src/synth_enumerate.rs',ROOT/'runners/dsl/src/term.rs']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels():return json.loads(UL.read_text())['panels']
def heldout_values(task,term,n):
 from adaptive_factored_operator_search_v1 import score
 return score(n,task,term)
def unique_cands(n,examples,pool,operator_order):
 from domains.generator import synthesize
 allh={}; branches=[];wall_all=0;cpu_all=0
 for op in operator_order:
  start=time.perf_counter_ns();cpu=time.process_time_ns()
  v=synthesize(n,examples,ops=BASE+(op,),consts=(),max_size=MAX_SIZE,timeout_s=BRANCH_TIMEOUT,include_output_constants=False,probe_envs=pool,max_solutions=MAX_SOLUTIONS,saturate_k=999999)
  wall=time.perf_counter_ns()-start;cpu_ns=time.process_time_ns()-cpu;wall_all+=wall;cpu_all+=cpu_ns
  hrows=[] if not v else v.get('hypotheses',[{'term':v.get('term').to_dict()}] if v.get('term') else [])
  ids=[]
  for h in hrows:
   t=h['term'].to_dict() if hasattr(h['term'],'to_dict') else h['term'];key=json.dumps(t,sort_keys=True,separators=(',',':'));hid='term_'+hashlib.sha256(key.encode()).hexdigest()[:16]
   if hid not in allh:allh[hid]={'id':hid,'term':t,'families':[]}
   if op not in allh[hid]['families']:allh[hid]['families'].append(op)
   ids.append(hid)
  branches.append({'operator':op,'wall_ns':wall,'cpu_ns':cpu_ns,'explored':0 if not v else v.get('explored',0),'halt_reason':None if not v else v.get('halt_reason'),'candidate_ids':ids})
 return list(allh.values()),branches,wall_all,cpu_all
def arm(n,panel,examples,operators):
 from domains.contract_query import select_discriminating_input
 from adaptive_factored_operator_search_v1 import classify,truth,score
 pool=[dict(zip(KEYS,map(float,row))) for row in panel['selection_order']]
 t0=time.perf_counter_ns();cpu0=time.process_time_ns();cands,branches,search_wall,search_cpu=unique_cands(n,examples,pool,operators)
 labels=[];survivors=cands.copy();used=set()
 while len(survivors)>1 and len(labels)<SELECTOR_LABEL_BUDGET:
  avail=[e for e in pool if tuple(float(e[k]) for k in KEYS) not in used]
  ans=select_discriminating_input(lambda term,e:classify(n.evaluate(term,e)),survivors,avail,[])
  if not ans.get('ok'):break
  q=ans['query'];row=[float(q[k]) for k in KEYS];label=bool(truth(panel['task'],row));before=len(survivors)
  survivors=[h for h in survivors if classify(n.evaluate(h['term'],q)) is label];used.add(tuple(row));labels.append({'row':row,'label':label,'before':before,'after':len(survivors),'selector_entropy_bits':ans.get('entropy_bits')})
 decision='accept' if len(survivors)==1 else 'request_help';selected=survivors[0] if decision=='accept' else None
 scored=[{'id':h['id'],'score':score(n,panel['task'],h['term'])} for h in (survivors if selected else cands)]
 return {'decision':decision,'selected_id':None if selected is None else selected['id'],'selected_term':None if selected is None else selected['term'],'initial_candidate_count':len(cands),'final_survivor_ids':[h['id'] for h in survivors],'candidate_terms':cands,'branches':branches,'selection_labels':labels,'scored_candidates':scored,'search_wall_ns':search_wall,'search_cpu_ns':search_cpu,'total_wall_ns':time.perf_counter_ns()-t0,'total_cpu_ns':time.process_time_ns()-cpu0}
def worker(i):
 from substrate_rs import _native
 p=panels()[i]; up=json.loads(UR.read_text())['workers'][i]; aw=json.loads(TRAW.read_text())['workers'][i]; n=_native.Substrate()
 residual=None
 for e in aw.get('events',[]):
  if not e['match']:
   residual={'row':e['row'],'label':int(e['label']),'candidate_prediction':e['prediction']};break
 if residual is None:return {'task':p['task'],'worker':p['worker'],'triggered':False,'residual':None,'no_residual_control':None,'residual_arm':None}
 original=[(dict(zip(KEYS,map(float,x['row']))),float(x['label'])) for x in p['training']]
 augmented=original+[(dict(zip(KEYS,map(float,residual['row']))),float(residual['label']))]
 seed=int(p['seed']);shift=seed%len(OPS);order=list(OPS[shift:]+OPS[:shift])
 return {'task':p['task'],'worker':p['worker'],'seed':seed,'triggered':True,'residual':residual,'operator_order':order,'no_residual_control':arm(n,p,original,order),'residual_arm':arm(n,p,augmented,order)}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(UA.read_text()).get('passed') or not json.loads(TO.read_text()).get('passed'):raise SystemExit('upstream analysis failure')
  LOCK.write_text(json.dumps({'schema':'ResidualTriggeredResynthesisV1_2Lock','sources':source_map(),'upstream_lock_sha256':sha(UL),'upstream_capture_sha256':sha(UR),'audit_lock_sha256':sha(TL),'audit_capture_sha256':sha(TRAW),'panels':panels(),'operators':OPS,'base_ops':BASE,'branch_timeout_s':BRANCH_TIMEOUT,'max_size':MAX_SIZE,'max_solutions':MAX_SOLUTIONS,'selection_label_budget':SELECTOR_LABEL_BUDGET,'heldout_values':HELD},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources'] or panels()!=lock['panels']:raise SystemExit('source/panel drift')
  rows=[]
  for i in range(len(lock['panels'])):
   cp=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'},text=True,capture_output=True,timeout=100)
   if cp.returncode:raise RuntimeError(f'worker {i}: {cp.stderr[-2000:]}')
   rows.append(json.loads(cp.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift')
  OUT.write_text(json.dumps({'schema':'ResidualTriggeredResynthesisV1_2Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker I')
if __name__=='__main__':raise SystemExit(main())
