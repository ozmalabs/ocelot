#!/usr/bin/env python3
"""Locked integration of general-rule proposal composition and active querying."""
from __future__ import annotations
import copy,hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_composed_proposal_active_query_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_COMPOSED_PROPOSAL_ACTIVE_QUERY_V1_PREREG_20261002.md'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_general_structural_proposal_control_kind_v1_2.py'
ADAPTER=ROOT/'evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py'
TASK=ROOT/'evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_composed_proposal_active_query_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_composed_proposal_active_query_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_composed_proposal_active_query_v1_scores_20261002.json'
WORKERS=4;POOL=100;ALIAS_RATES=(0,50,90,99);SEED=31027;TARGET='classify_kind_family'
FAMILIES={'relative_pointer':['trackpad','mouse','touchpad','pointer','trackball'],
 'discrete_select':['rotary','dial','knob'],'continuous_rotation':['steering','wheel','paddle'],
 'discrete_act':['trigger','button','switch','key'],'continuous_direction':['joystick','stick'],
 'range_1dof':['slider','throttle','lever','pedal']}
NEUTRALS=('quartz widget','silent vessel','amber object','blank instrument','plain device')
TERMS=[{'type':'Lit','value':'fault'},{'type':'Lit','value':'proposal'}]
ACTIVE=(ROOT/'domains/reflective_faculty.py',ROOT/'domains/edit_ops.py',ROOT/'domains/self_correction.py',
 ROOT/'domains/contract_query.py',ROOT/'domains/engine_provenance.py',ROOT/'substrate/boot_core.py',ROOT/'substrate/seed_loader.py',
 ROOT/'runners/dsl/src/py.rs',ROOT/'runners/dsl/src/substrate.rs',ROOT/'runners/dsl/src/graph.rs',
 ROOT/'runners/dsl/src/graph_rules.rs',ROOT/'runners/dsl/src/term.rs',ROOT/'runners/dsl/src/persist.rs',
 ROOT/'runners/dsl/src/grammar.rs',ROOT/'runners/dsl/src/sym.rs',ROOT/'runners/dsl/src/lib.rs',
 ROOT/'runners/dsl/Cargo.toml',ROOT/'runners/dsl/Cargo.lock',ROOT/'runners/dsl/python/substrate_rs/__init__.py',
 ROOT/'seeds/control_kinds.json',ROOT/'seeds/relation_vocabulary.json')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(*ACTIVE,RUNNER,ANALYZER,PROTOCOL,BASE,ADAPTER,TASK)
 out={str(p.relative_to(ROOT)):sha(p) for p in files};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def digest(candidate):
 import thoughtexperiment_blinded_panel_adapters_v1 as a
 return a.digest(candidate)
def proposal(worker):
 import thoughtexperiment_general_structural_proposal_control_kind_v1_2 as composer
 result=composer._compose(worker,True)
 if not result['candidate']:raise RuntimeError('general composer abstained')
 if result['target']!=TARGET:raise RuntimeError('unexpected proposal target')
 return result
def pool(worker,rate):
 informative=POOL-round(POOL*rate/100);rows=[]
 family_names=[(word,fam) for fam,words in FAMILIES.items() for word in words]
 for i in range(POOL):
  if i<informative:
   word,fam=family_names[(i+worker*3)%len(family_names)]
   name=f'{word} instrument probe{worker}_{rate}_{i}'
   rows.append({'env':{'name':name},'label':fam,'informative':True})
  else:
   stem=NEUTRALS[(i+worker)%len(NEUTRALS)]
   name=f'{stem} probe{worker}_{rate}_{i}'
   rows.append({'env':{'name':name},'label':None,'informative':False})
 random.Random(SEED+worker*1000+rate).shuffle(rows)
 return rows
def make_branch(ctx,candidate):
 import thoughtexperiment_blinded_panel_adapters_v1 as a
 branch=ctx['sub'].fork_full_copy_experiment();bn=branch._inner
 applied=a._replace(bn,candidate)
 if not a._receipt(bn,candidate,applied):raise RuntimeError('candidate patch receipt failed')
 registry=next((n for n in branch.nodes('SignalRegistry') if branch.node(n)['attrs'].get('name')=='control_family_signals'),None)
 if registry is None:raise RuntimeError('signal registry absent')
 return branch,bn,registry
def branch_predict(branch,bn,registry,name):
 node=branch.add_node('ControlKind',{'name':name,'name_lc':name.lower(),'family_set':0.0})
 bn.add_edge_unchecked(registry,'has_kind',node,{})
 bn.run_rules(1000)
 attrs=branch.node(node)['attrs']
 return (attrs.get('effect_family'),float(attrs.get('family_set',0.0)))
def order_worker(worker):
 import thoughtexperiment_blinded_panel_adapters_v1 as a
 before=frozen();generated=proposal(worker);ctx=a.prepare('control_kind',worker,'train')
 fault={'label':'fault_baseline','rules':{TARGET:copy.deepcopy(generated['source_target'])}}
 candidate=copy.deepcopy(generated['candidate'])
 fault_branch=make_branch(ctx,fault);proposal_branch=make_branch(ctx,candidate)
 branches={'fault':fault_branch,'proposal':proposal_branch};cache={}
 hypotheses=[{'id':'fault','term':TERMS[0]},{'id':'proposal','term':TERMS[1]}]
 selections=[]
 for rate in ALIAS_RATES:
  rows=pool(worker,rate);inputs=[x['env'] for x in rows]
  def evaluate(term,env):
   name=ctx['native'].evaluate(term,env)
   branch,bn,registry=branches[name]
   key=(name,env['name'])
   if key not in cache:cache[key]=branch_predict(branch,bn,registry,env['name'])
   return cache[key]
  t0=time.perf_counter_ns();cpu0=time.process_time_ns()
  selected=__import__('domains.contract_query',fromlist=['select_discriminating_input']).select_discriminating_input(evaluate,hypotheses,inputs)
  wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-cpu0
  rng=random.Random(SEED+worker*1000+rate);random_env=inputs[rng.randrange(len(inputs))]
  # Only prediction-side data is frozen here. Oracle labels are attached in the score stage.
  selections.append({'alias_rate_percent':rate,'selected':selected,'random_env':random_env,
   'selector_wall_ns':wall,'selector_cpu_ns':cpu,'candidate_count':len(inputs),
   'informative_count':sum(x['informative'] for x in rows)})
 after=frozen()
 if before!=after:raise RuntimeError('source drift during order capture')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'target':generated['target'],'operator':generated['operator'],'site':generated['site'],
  'proposal':candidate,'proposal_digest':digest(candidate),'proposal_host_reference_match':generated['candidate_host_reference_match'],
  'fault_baseline':fault,'selections':selections}
def score_worker(order):
 import thoughtexperiment_blinded_panel_adapters_v1 as a
 before=frozen();w=order['worker'];ctx=a.prepare('control_kind',w,'heldout')
 outcomes={'proposal':a.score(ctx,order['proposal']),'fault':a.score(ctx,order['fault_baseline'])}
 results=[]
 for row in order['selections']:
  selected=row['selected'];rate=row['alias_rate_percent'];rows=pool(w,rate)
  by_name={x['env']['name']:x for x in rows}
  if not selected.get('ok'):raise RuntimeError('selector did not produce a query')
  query=selected['query'];random_env=row['random_env']
  def adjudicate(env):
   datum=by_name[env['name']]
   expected=(datum['label'],1.0) if datum['label'] is not None else (None,0.0)
   preds={p['hypothesis']:tuple(p['output']) for p in selected.get('predictions',[])} if env==query else None
   return {'env':env,'expected':expected,'informative':datum['informative'],'predictions':preds,
    'survivors':[hid for hid,value in (preds or {}).items() if type(value) is type(expected) and value==expected]}
  query_score=adjudicate(query)
  # Random baseline predictions are computed on the frozen native rule branches below via a fresh train context.
  train=a.prepare('control_kind',w,'train');fb=make_branch(train,order['fault_baseline']);pb=make_branch(train,order['proposal'])
  predicted={hid:branch_predict(*branch,random_env['name']) for hid,branch in [('fault',fb),('proposal',pb)]}
  random_datum=by_name[random_env['name']];expected=(random_datum['label'],1.0) if random_datum['label'] is not None else (None,0.0)
  random_survivors=[hid for hid,value in predicted.items() if value==expected]
  results.append({'alias_rate_percent':rate,'query':query_score,'random_probe':{'env':random_env,'predictions':predicted,
   'expected':expected,'informative':random_datum['informative'],'survivors':random_survivors,
   'discriminates':predicted['fault']!=predicted['proposal']},
   'entropy_bits':selected['entropy_bits'],'partition_count':selected['partition_count'],
   'survivors_after_oracle':query_score['survivors'],'selector_wall_ns':row['selector_wall_ns'],'selector_cpu_ns':row['selector_cpu_ns']})
 after=frozen()
 if before!=after:raise RuntimeError('source drift during scoring')
 return {'worker':w,'source_before':before,'source_after':after,'source_stable':before==after,
  'proposal_outcome':outcomes['proposal'],'fault_outcome':outcomes['fault'],'active_query_results':results}
def main():
 if sys.argv[1:2]==['--order-worker']:
  print(json.dumps(order_worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(score_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite capture')
  LOCK.write_text(json.dumps({'schema':'ComposedProposalActiveQueryV1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'pool_size':POOL,
   'alias_rates_percent':ALIAS_RATES,'seed':SEED,'target':TARGET,'family_table':FAMILIES},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}:{ROOT / "evaluation/substrate_capability"}'}
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('capture already exists')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift while capturing orders')
  ORDERS.write_text(json.dumps({'schema':'ComposedProposalActiveQueryV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),
   'machine':platform.machine(),'python':sys.version.split()[0]},'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(workers),'path':ORDERS.relative_to(ROOT).as_posix()}));return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or score capture exists')
  doc=json.loads(ORDERS.read_text());workers=[]
  for row in doc['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(row),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"score worker {row['worker']}: {p.stderr[-3000:]}")
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift while scoring')
  SCORES.write_text(json.dumps({'schema':'ComposedProposalActiveQueryV1Scores','orders_sha256':sha(ORDERS),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'scored_after_order_freeze','workers':len(workers),'path':SCORES.relative_to(ROOT).as_posix()}));return
 raise SystemExit('choose --lock, --orders, or --score')
if __name__=='__main__':main()
