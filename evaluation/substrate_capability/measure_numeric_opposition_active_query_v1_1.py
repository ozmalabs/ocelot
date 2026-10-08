#!/usr/bin/env python3
"""Order-balanced active-query replication over synthesized Term hypotheses."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_numeric_opposition_active_query_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_active_query_v1_1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_active_query_v1_1_20261003.json'
ORDERS=30;CALL_BUDGET=6
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from evaluation.substrate_capability.measure_numeric_opposition_active_query_v1 import source_map as base_map
 x=base_map();x['files'].update({str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PRE,ANALYZER)})
 return x
def make_panels():
 from evaluation.substrate_capability.measure_numeric_opposition_active_query_v1 import panels
 out=[]
 for panel in panels():
  orders=[]
  for j in range(ORDERS):
   xs=list(panel['query_pool']);random.Random(661033+panel['worker']*1000+j).shuffle(xs)
   orders.append({'order_id':j,'seed':661033+panel['worker']*1000+j,'rows':xs})
  out.append({**panel,'orders':orders})
 return out
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  from domains.engine_provenance import build_is_stale
  if build_is_stale(str(ROOT)):raise SystemExit('native engine is stale')
  LOCK.write_text(json.dumps({'schema':'NumericOppositionActiveQueryV1_1Lock','sources':source_map(),'panels':make_panels(),'orders_per_worker':ORDERS,'call_budget':CALL_BUDGET,
   'synth_config':{'ops':['Neg','Eq','And'],'constants':[],'max_size':9,'timeout_s':12.0,'max_solutions':128,'include_output_constants':False}},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)>2 and sys.argv[1]=='--worker':
  print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(sys.argv[2])]),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker ID')
 lock=json.loads(LOCK.read_text())
 if source_map()!=lock['sources']:raise SystemExit('source drift from lock')
 envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};workers=[]
 for i in range(len(lock['panels'])):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=120)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2500:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'NumericOppositionActiveQueryV1_1Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_map(),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
def worker(panel):
 from evaluation.substrate_capability.measure_numeric_opposition_active_query_v1 import run_worker as synthesize_panel,env,truth,observed_equal,GRID,NAV_TASKS,ACTION_VECTOR
 from domains.contract_query import select_discriminating_input
 from substrate_rs import _native
 native=_native.Substrate();base=synthesize_panel({k:panel[k] for k in ('worker','seed','training','query_pool','random_order')})
 hypotheses=base['hypotheses'];blocks=[]
 grid=list(itertools.product(GRID,repeat=4))
 for order_spec in panel['orders']:
  order=order_spec['rows'];arms=[]
  for policy in ('max_entropy','sequential_random_order'):
   survivors=list(hypotheses);observations=[];used=[];steps=[];selector_ns=0;t0=time.perf_counter_ns()
   for _ in range(CALL_BUDGET):
    if len(survivors)<2:break
    unused=[r for r in order if r not in used]
    if not unused:break
    available=[env(r) for r in unused]
    if policy=='max_entropy':
     ts=time.perf_counter_ns();picked=select_discriminating_input(lambda t,e:native.evaluate(t,e),survivors,available,observations);selector_ns+=time.perf_counter_ns()-ts
     if not picked.get('ok'):break
     q=picked['query'];predictions=picked['predictions'];entropy=picked['entropy_bits']
    else:
     q=available[0];predictions=[{'hypothesis':h['id'],'output':native.evaluate(h['term'],q)} for h in survivors];entropy=None
    row=[int(q[k]) for k in ('ax','ay','ex','ey')];label=bool(truth(row));used.append(row)
    observations.append({'inputs':q,'expected':label});before=len(survivors)
    survivors=[h for h in survivors if observed_equal(native.evaluate(h['term'],q),label)]
    steps.append({'query':row,'label':label,'predictions':predictions,'entropy_bits':entropy,'before':before,'after':len(survivors)})
   policy_wall_ns=time.perf_counter_ns()-t0
   hscores=[]
   for h in survivors:
    tp=fp=fn=tn=0
    for row in grid:
     y=truth(row);p=bool(native.evaluate(h['term'],env(row)))
     if y and p:tp+=1
     elif y:fn+=1
     elif p:fp+=1
     else:tn+=1
    nav=[]
    for task in NAV_TASKS:
     av=ACTION_VECTOR.get(task['actual']);ev=ACTION_VECTOR.get(task['expected']) if task['expected'] is not None else None
     if av is None or ev is None:rel=None;proposal=False
     else:rel=bool(native.evaluate(h['term'],{'ax':av[0],'ay':av[1],'ex':ev[0],'ey':ev[1]}));proposal=rel and task['kind']!='absent_target'
     nav.append({'task_id':task['id'],'relation':rel,'proposal':proposal,'expected_proposal':task['kind']=='opposite'})
    hscores.append({'hypothesis':h['id'],'heldout':{'n':len(grid),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':fp==0 and fn==0},'navigation':nav})
   arms.append({'policy':policy,'steps':steps,'oracle_calls':len(steps),'selector_ns':selector_ns,'arm_wall_ns':policy_wall_ns,'survivor_ids':[h['id'] for h in survivors],'heldout_scores':hscores})
  blocks.append({'order_id':order_spec['order_id'],'seed':order_spec['seed'],'order':order,'arms':arms})
 return {'worker':panel['worker'],'training':panel['training'],'query_pool':panel['query_pool'],'hypotheses':hypotheses,'version_halt_reason':base['version_halt_reason'],'version_explored':base['version_explored'],'version_wall_ns':base['version_wall_ns'],'version_cpu_ns':base['version_cpu_ns'],'target_present':base['target_present'],'blocks':blocks}
if __name__=='__main__':raise SystemExit(main())
