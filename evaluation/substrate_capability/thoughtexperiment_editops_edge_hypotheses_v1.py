#!/usr/bin/env python3
"""Run cross-family proposal selection using the substrate's shared edit-op vocabulary."""
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_lock_20261002.json'
BASE_ORDERS=ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_orders_20261002.json'
BASE_SCORES=ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_1_scores_20261002.json'
BASE_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
EDITOPS=ROOT/'domains/edit_ops.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EDITOPS_EDGE_HYPOTHESES_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_editops_edge_hypotheses_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_editops_edge_hypotheses_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_scores_20261002.json'
WORKERS=4

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('bidirectional_edge_identity_base_editops_v1',BASE)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 from substrate_rs import _native
 base=load_base()
 return {'runner':sha(Path(__file__).resolve()),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'shared_edit_ops':sha(EDITOPS),'base_runner':sha(BASE),'base_lock_reference':sha(BASE_LOCK),
  'base_orders_reference':sha(BASE_ORDERS),'base_scores_reference':sha(BASE_SCORES),
  'base_analyzer_reference':sha(BASE_ANALYZER),'base_current_sources':{p:sha(ROOT/p) for p in base.SOURCES},
  'loaded_native_binary':sha(Path(_native.__file__).resolve())}
def canonical_hypotheses(rule):
 from domains.edit_ops import find_edge_identity_sites,apply_add_edge_identity_guard
 start=time.perf_counter_ns();all_sites=find_edge_identity_sites(rule)
 sites=[s for s in all_sites if s.get('scope','edge')=='edge'];out=[]
 for i,site in enumerate(sites):
  name=f"{rule.get('name','rule')}_editops_identity_{i}"
  variant=apply_add_edge_identity_guard(rule,site,name)
  if variant is None:continue
  label=f"editops_edge_once:{site['direction']}:{site['var']}:{site['edge_type']}:{site.get('other') or 'any'}"
  out.append({'label':label,'rules':{rule['name']:variant}})
 elapsed=time.perf_counter_ns()-start
 expected_sites=[s for s in all_sites if s.get('scope','edge')=='edge']
 if len(out)!=3 or len(sites)!=3:raise RuntimeError(f"expected 3 edge hypotheses, generated {len(out)} from {len(sites)} sites")
 return out,expected_sites,elapsed
def install(base):
 genmeta={'by_target':{}}
 def generated(rule):
  out,sites,elapsed=canonical_hypotheses(rule)
  genmeta['by_target'][rule.get('name')]= {'generation_ns':elapsed,'site_count':len(sites)}
  return out,sites
 base.generic_edge_guard_hypotheses=generated
 return genmeta
def worker(mode,worker_id,order=None):
 base=load_base();meta=install(base)
 if mode=='orders':
  row=base.order_worker(int(worker_id))
 else:
  row=base.score_worker(order)
 row['editops_generation_by_target']=meta['by_target']
 row['wrapper_pid']=os.getpid();row['generation_source']='domains.edit_ops.find_edge_identity_sites+apply_add_edge_identity_guard'
 return row
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker-orders']:
  print(json.dumps(worker('orders',int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args[:1]==['--worker-score']:
  print(json.dumps(worker_score_from_stdin(),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit('refusing to overwrite lock or captures')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentEditOpsEdgeHypothesesV1Lock','sources':frozen(),
   'workers':WORKERS,'families':['recurrence','conversation'],'generated_edge_site_count':3,
   'composer_candidate_count':1,'candidate_count':4,'train_repeats':2,'heldout_repeats':2,
   'generator':'find_edge_identity_sites + apply_add_edge_identity_guard','scope':'edge only; node_attrs excluded'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args==['--orders']:
  if not LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit('missing lock or captures already exist')
  lock=json.loads(LOCK.read_text())
  if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker-orders',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
   if p.returncode:raise RuntimeError(f'order worker {i}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift during order capture')
  ORDERS.write_text(json.dumps({'schema':'ThoughtexperimentEditOpsEdgeHypothesesV1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'workers':rows},indent=2,sort_keys=True)+'\n')
  print(ORDERS.relative_to(ROOT));return 0
 if args==['--scores']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('orders missing or scores already exist')
  lock=json.loads(LOCK.read_text())
  if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for order in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker-score'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
   if p.returncode:raise RuntimeError(f"score worker {order['worker']}: {p.stderr[-3000:]}")
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift during heldout scoring')
  SCORES.write_text(json.dumps({'schema':'ThoughtexperimentEditOpsEdgeHypothesesV1Scores','lock_sha256':sha(LOCK),
   'orders_sha256':sha(ORDERS),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n')
  print(SCORES.relative_to(ROOT));return 0
 raise SystemExit('use --lock, --orders, --scores, or worker modes')
def worker_score_from_stdin():
 order=json.load(sys.stdin);return worker('score',int(order['worker']),order)
if __name__=='__main__':raise SystemExit(main())
