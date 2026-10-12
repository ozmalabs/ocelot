#!/usr/bin/env python3
"""Finite version-space active-query benchmark for numeric opposition."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_numeric_opposition_active_query_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_active_query_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_active_query_v1_20261003.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','evaluation/substrate_capability/measure_residual_to_composer_numeric_cue_v1.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
BASE_SEED=61033;WORKERS=5;MAX_SIZE=9;TIMEOUT=12.0;MAX_SOLUTIONS=128;CALL_BUDGET=6
GRID=(-2.5,-1.5,-.5,.5,1.5,2.5)
NAV_TASKS=[{'id':'opposite_up','actual':'Down','expected':'Up','kind':'opposite'},{'id':'opposite_down','actual':'Up','expected':'Down','kind':'opposite'},{'id':'opposite_left','actual':'Right','expected':'Left','kind':'opposite'},{'id':'opposite_right','actual':'Left','expected':'Right','kind':'opposite'},{'id':'orthogonal','actual':'Right','expected':'Up','kind':'other'},{'id':'orthogonal_2','actual':'Up','expected':'Left','kind':'other'},{'id':'same_direction','actual':'Up','expected':'Up','kind':'other'},{'id':'same_direction_2','actual':'Left','expected':'Left','kind':'other'},{'id':'unknown_action','actual':'Teleport','expected':'Up','kind':'unknown'},{'id':'unknown_expected','actual':'Down','expected':'Portal','kind':'unknown'},{'id':'missing_expected','actual':'Down','expected':None,'kind':'missing'},{'id':'zero_displacement','actual':'Stay','expected':'Up','kind':'zero'},{'id':'target_absent','actual':'Down','expected':'Up','kind':'absent_target'}]
ACTION_VECTOR={'Up':(-1.,0.),'Down':(1.,0.),'Left':(0.,-1.),'Right':(0.,1.),'Stay':(0.,0.)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r):return r[0]==-r[2] and r[1]==-r[3]
def observed_equal(a,b):return type(a) is type(b) and a==b
def panels():
 out=[];allrows=list(itertools.product(range(-2,3),repeat=4))
 for w in range(WORKERS):
  rng=random.Random(BASE_SEED+w);a,b=rng.choice((1,-1,2,-2)),rng.choice((1,-1,2,-2))
  train=[(a,0,-a,0),(0,b,0,-b),(a,0,a,0),(a,0,0,b)]
  mandatory=[(1,1,-1,0),(1,1,0,-1),(1,1,-1,-1),(2,1,-2,1),(1,2,1,-2)]
  pool=list(dict.fromkeys(mandatory+[r for r in allrows if r not in train and r not in mandatory]))
  rng.shuffle(pool);chosen=mandatory+[r for r in pool if r not in mandatory][:27]
  # Ensure no query duplicates any training observation, including across seeds.
  chosen=[r for r in chosen if r not in train]
  while len(chosen)<32:
   r=rng.choice(allrows)
   if r not in train and r not in chosen:chosen.append(r)
  random_order=list(chosen);random.Random(BASE_SEED+1000+w).shuffle(random_order)
  out.append({'worker':w,'seed':BASE_SEED+w,'training':[{'row':list(r),'label':int(truth(r))} for r in train],
   'query_pool':[list(r) for r in chosen],'random_order':[list(r) for r in random_order]})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'semantic_engine':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def run_worker(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 from domains.contract_query import select_discriminating_input
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('native build stale')
 native=_native.Substrate(); examples=[(env(x['row']),float(x['label'])) for x in panel['training']]
 queries=[env(x) for x in panel['query_pool']];t0=time.perf_counter_ns();c0=time.process_time_ns()
 version=synthesize(native,examples,ops=('Neg','Eq','And'),consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,
  include_output_constants=False,probe_envs=queries,max_solutions=MAX_SOLUTIONS,saturate_k=999999)
 synth_wall=time.perf_counter_ns()-t0;synth_cpu=time.process_time_ns()-c0
 hyps=[] if not version else [{'id':f'h{i:03d}','term':h['term'].to_dict()} for i,h in enumerate(version['hypotheses'])]
 target={'type':'And','items':[{'type':'Eq','a':{'type':'Var','name':'ax'},'b':{'type':'Neg','arg':{'type':'Var','name':'ex'}}},{'type':'Eq','a':{'type':'Var','name':'ay'},'b':{'type':'Neg','arg':{'type':'Var','name':'ey'}}}]}
 target_present=any(h['term']==target for h in hyps)
 arms=[]
 for policy in ('max_entropy','fixed_first','seeded_random'):
  survivors=list(hyps);observations=[];used=[];steps=[];sel_ns=0;wall_arm=time.perf_counter_ns()
  order=panel['query_pool'] if policy!='seeded_random' else panel['random_order']
  for turn in range(CALL_BUDGET):
   if len(survivors)<2:break
   available=[env(r) for r in order if r not in used]
   if not available:break
   ts=time.perf_counter_ns()
   if policy=='max_entropy':
    picked=select_discriminating_input(lambda t,e:native.evaluate(t,e),survivors,available,observations)
    if not picked.get('ok'):break
    q=picked['query'];preds=picked['predictions'];entropy=picked['entropy_bits']
   else:
    q=available[0];preds=[{'hypothesis':h['id'],'output':native.evaluate(h['term'],q)} for h in survivors];entropy=None
   sel_ns+=time.perf_counter_ns()-ts
   row=[int(q[k]) for k in ('ax','ay','ex','ey')];label=bool(truth(row));used.append(row)
   observations.append({'inputs':q,'expected':label})
   pre=len(survivors);survivors=[h for h in survivors if observed_equal(native.evaluate(h['term'],q),label)]
   steps.append({'query':row,'label':label,'predictions':preds,'entropy_bits':entropy,'before':pre,'after':len(survivors)})
  nav=[]
  for h in survivors:
   rows=[]
   for task in NAV_TASKS:
    av=ACTION_VECTOR.get(task['actual']);ev=ACTION_VECTOR.get(task['expected']) if task['expected'] is not None else None
    if av is None or ev is None:relation=None;proposal=False;expected_proposal=False
    else:
     relation=bool(native.evaluate(h['term'],{'ax':av[0],'ay':av[1],'ex':ev[0],'ey':ev[1]}))
     proposal=relation and task['kind']!='absent_target';expected_proposal=task['kind']=='opposite'
    rows.append({'task_id':task['id'],'relation':relation,'proposal':proposal,'expected_proposal':expected_proposal})
   nav.append({'hypothesis':h['id'],'tasks':rows})
  arms.append({'policy':policy,'steps':steps,'oracle_calls':len(steps),'selector_ns':sel_ns,'arm_wall_ns':time.perf_counter_ns()-wall_arm,
   'survivor_ids':[h['id'] for h in survivors],'survivor_terms':[h['term'] for h in survivors],'navigation_transfer':nav})
 return {'worker':panel['worker'],'training':panel['training'],'query_pool':panel['query_pool'],'random_order':panel['random_order'],
  'hypotheses':[{'id':h['id'],'term':h['term']} for h in hyps], 'version_halt_reason':version.get('halt_reason') if version else 'no_result',
  'version_explored':version.get('explored',0) if version else 0,'version_distinct':version.get('distinct',0) if version else 0,
  'version_synth_elapsed_s':version.get('elapsed_s',0) if version else 0,'version_wall_ns':synth_wall,'version_cpu_ns':synth_cpu,
  'target_present':target_present,'target_term':target,'arms':arms}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  from domains.engine_provenance import build_is_stale
  if build_is_stale(str(ROOT)):raise SystemExit('native build stale')
  LOCK.write_text(json.dumps({'schema':'NumericOppositionActiveQueryV1Lock','sources':source_map(),'panels':panels(),
  'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,'call_budget':CALL_BUDGET,'heldout_values':GRID,'heldout_cases':1296,
  'navigation_tasks':NAV_TASKS,'action_vectors':ACTION_VECTOR},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)>2 and sys.argv[1]=='--worker':
  p=json.loads(LOCK.read_text())['panels'][int(sys.argv[2])];print(json.dumps(run_worker(p),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker ID')
 lock=json.loads(LOCK.read_text())
 if source_map()!=lock['sources']:raise SystemExit('source drift from lock')
 envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
 for i in range(WORKERS):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=90)
  if p.returncode:raise RuntimeError(f'worker {i} failed: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'NumericOppositionActiveQueryV1Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_map(),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
