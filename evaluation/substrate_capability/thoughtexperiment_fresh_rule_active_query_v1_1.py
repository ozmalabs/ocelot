#!/usr/bin/env python3
"""Fresh-rule active-query replication with isolated full-copy/CoW branches."""
from __future__ import annotations
import copy,hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_fresh_rule_active_query_v1_1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_FRESH_RULE_ACTIVE_QUERY_V1_1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_fresh_rule_active_query_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_fresh_rule_active_query_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_fresh_rule_active_query_v1_1_scores_20261002.json'
WORKERS=4;POOL=100;ALIAS_RATES=(0,50,90,99);SEED=90217;TARGET='classify_meter_mode';MODES=('cow_snapshot','full_copy')
TERMS=[{'type':'Lit','value':'fault'},{'type':'Lit','value':'proposal'}]
ACTIVE=(ROOT/'domains/reflective_faculty.py',ROOT/'domains/edit_ops.py',ROOT/'domains/self_correction.py',
 ROOT/'domains/contract_query.py',ROOT/'domains/engine_provenance.py',ROOT/'substrate/boot_core.py',ROOT/'substrate/seed_loader.py',
 ROOT/'runners/dsl/src/py.rs',ROOT/'runners/dsl/src/substrate.rs',ROOT/'runners/dsl/src/graph.rs',ROOT/'runners/dsl/src/graph_rules.rs',
 ROOT/'runners/dsl/src/term.rs',ROOT/'runners/dsl/src/persist.rs',ROOT/'runners/dsl/src/grammar.rs',ROOT/'runners/dsl/src/sym.rs',
 ROOT/'runners/dsl/src/lib.rs',ROOT/'runners/dsl/Cargo.toml',ROOT/'runners/dsl/Cargo.lock',
 ROOT/'runners/dsl/python/substrate_rs/__init__.py',ROOT/'seeds/relation_vocabulary.json')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 out={str(p.relative_to(ROOT)):sha(p) for p in (*ACTIVE,RUNNER,ANALYZER,PROTOCOL)}
 out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def sem_digest(rule):
 value=copy.deepcopy(rule)
 if isinstance(value,dict):
  for key in ('name','content_hash','revision','rule_uid','active'):value.pop(key,None)
 return 'sha256:'+hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def target_rule():
 return {'name':TARGET,'active':True,
  'match':[['world','has_request','req'],['req','has_measurement','m']],
  'where':{'type':'Eq','a':{'type':'Attr','node':{'type':'Var','name':'req'},'key':'classified'},'b':{'type':'Lit','value':0.0}},
  'effects':[['set_attr','req','predicted',{'__term__':{'type':'IfThenElse',
   'cond':{'type':'Gt','a':{'type':'Attr','node':{'type':'Var','name':'m'},'key':'score'},'b':{'type':'Lit','value':0.0}},
   'then':{'type':'Attr','node':{'type':'Var','name':'m'},'key':'positive'},
   'other':{'type':'Attr','node':{'type':'Var','name':'m'},'key':'negative'}}}],['set_attr','req','classified',1.0]]}
def boot_fault():
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 from domains.edit_ops import apply_flip_comparison
 sub,root=boot_core(seeds=());native=sub._inner
 native.load_seed_manifest(manifest_for('relation_vocabulary'),root)
 source=target_rule();fault=apply_flip_comparison(source,TARGET)
 native.add_rule(fault)
 return sub,root,native,source,fault
class Agent:
 def __init__(self,sub,root):self.s=sub;self.inner=sub._inner;self.agent=root
def compose(worker):
 import domains.reflective_faculty as rf
 from domains.self_correction import _default_candidates
 sub,root,native,source,fault=boot_fault();agent=Agent(sub,root)
 key=f'fresh_meter_active_query_{worker}'
 sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
  'residual_predicates':['classify','meter','mode','threshold','flip','comparison'],
  'structural_rule_scope':'all_mutable_rules','from_observation':1.0,
  'source':'thoughtexperiment_fresh_rule_active_query_v1'})
 before=next(copy.deepcopy(r) for r in native.export_rules() if r.get('name')==TARGET and r.get('active',True))
 start=time.perf_counter_ns();result=rf.compose_general_structural_variant(agent,[key],f'w{worker}')
 decision_ns=time.perf_counter_ns()-start
 after=next(copy.deepcopy(r) for r in native.export_rules() if r.get('name')==TARGET and r.get('active',True))
 if before!=after:raise RuntimeError('composition changed primary rule')
 if not result.get('built'):raise RuntimeError('composer abstained: '+str(result.get('wall')))
 candidate=result['rule'];refs=_default_candidates(native,TARGET)
 reference=next((c for c in refs if c['label']=='flip_comparison'),None)
 if reference is None:raise RuntimeError('generic enumerator did not expose flip reference')
 return {'sub':sub,'root':root,'native':native,'source_rule':source,'fault_rule':fault,'candidate_rule':candidate,
  'result':result,'decision_ns':decision_ns,'reference_digest':sem_digest(reference['rules'][TARGET]),
  'proposal_digest':sem_digest(candidate),'reference_label':reference['label'],'primary_target_preserved':before==after}
def predict_isolated(base,snapshot,mode,rule,env):
 fork_start=time.perf_counter_ns()
 branch=snapshot.fork() if mode=='cow_snapshot' else base.fork_full_copy_experiment()
 fork_ns=time.perf_counter_ns()-fork_start;native=branch._inner
 patch_start=time.perf_counter_ns()
 if not native.replace_active_rule_by_name(TARGET,copy.deepcopy(rule)):raise RuntimeError('rule replacement failed')
 patch_ns=time.perf_counter_ns()-patch_start
 actual=next((r for r in native.export_rules() if r.get('name')==rule.get('name') and r.get('active',True)),None)
 fields=('match','match_type','where','effects')
 if actual is None or any(actual.get(k)!=rule.get(k) for k in fields):raise RuntimeError('candidate receipt mismatch')
 return predict(branch,native,env,fork_ns,patch_ns)
def predict(branch,native,env,fork_ns=0,patch_ns=0):
 world=branch.add_node('World',{'probe_id':env['probe_id']})
 request=branch.add_node('Request',{'classified':0.0})
 measurement=branch.add_node('Measurement',{'score':env['score'],'positive':env['positive'],'negative':env['negative']})
 native.add_edge_unchecked(world,'has_request',request,{})
 native.add_edge_unchecked(request,'has_measurement',measurement,{})
 closure_start=time.perf_counter_ns();work=int(native.run_rules(100));attrs=branch.node(request)['attrs'];fixed=int(native.run_rules(100));closure_ns=time.perf_counter_ns()-closure_start
 if fixed!=0:raise RuntimeError('branch did not reach fixed point')
 return {'output':(attrs.get('predicted'),float(attrs.get('classified',0.0))),
  'closure_work':work,'fixedpoint_work':fixed,'receipt_verified':True,
  'branch_fork_ns':fork_ns,'candidate_patch_ns':patch_ns,'closure_ns':closure_ns}
def candidate_pool(worker,rate):
 neutral=round(POOL*rate/100);rows=[]
 for i in range(POOL):
  if i<POOL-neutral:
   score=(1.0 if (i+worker)%2==0 else -1.0)
  else:score=0.0
  env={'probe_id':f'w{worker}_r{rate}_i{i}','score':score,'positive':'HOT','negative':'COLD'}
  rows.append(env)
 random.Random(SEED+worker*1000+rate).shuffle(rows);return rows
def prediction_summary(metrics):
 rows=list(metrics.values())
 outputs=[(key,row['output']) for key,row in sorted(metrics.items())]
 raw=json.dumps(outputs,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
 mean=lambda k:sum(r[k] for r in rows)/len(rows) if rows else 0.0
 return {'n':len(rows),'output_sha256':hashlib.sha256(raw).hexdigest(),
  'mean_branch_fork_ns':mean('branch_fork_ns'),'mean_candidate_patch_ns':mean('candidate_patch_ns'),
  'mean_closure_ns':mean('closure_ns'),'mean_prediction_ns':mean('prediction_ns'),
  'total_closure_work':sum(r['closure_work'] for r in rows),
  'all_fixedpoint_zero':all(r['fixedpoint_work']==0 for r in rows),
  'all_receipts_verified':all(r['receipt_verified'] for r in rows)}
def order_worker(worker):
 before=frozen();built=compose(worker);base,root,native,source,fault=boot_fault()
 primary_rules=native.export_rules();primary_rev=tuple(native.experiment_graph_rule_revision())
 snapshot_start=time.perf_counter_ns();snapshot=base.snapshot();snapshot_ns=time.perf_counter_ns()-snapshot_start
 from domains.contract_query import select_discriminating_input
 hypotheses=[{'id':'fault','term':TERMS[0]},{'id':'proposal','term':TERMS[1]}];selections=[]
 for mode in MODES:
  for rate in ALIAS_RATES:
   inputs=candidate_pool(worker,rate);metrics={}
   def evaluate(term,env):
    arm=native.evaluate(term,env);rule=fault if arm=='fault' else built['candidate_rule']
    key=(arm,env['probe_id'])
    if key not in metrics:
     t0=time.perf_counter_ns();metrics[key]=predict_isolated(base,snapshot,mode,rule,env)
     metrics[key]['prediction_ns']=time.perf_counter_ns()-t0
    return metrics[key]['output']
   wall0=time.perf_counter_ns();cpu0=time.process_time_ns();selected=select_discriminating_input(evaluate,hypotheses,inputs)
   wall=time.perf_counter_ns()-wall0;cpu=time.process_time_ns()-cpu0
   random_env=random.Random(SEED+worker*1000+rate).choice(inputs)
   selections.append({'mode':mode,'alias_rate_percent':rate,'selected':selected,'random_env':random_env,
    'selector_wall_ns':wall,'selector_cpu_ns':cpu,'candidate_count':len(inputs),
    'prediction_calls':2*len(inputs),'native_closure_calls':2*len(inputs),
    'input_pool_sha256':hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    'prediction_summary':prediction_summary(metrics)})
 primary_preserved=native.export_rules()==primary_rules and tuple(native.experiment_graph_rule_revision())==primary_rev
 if not primary_preserved:raise RuntimeError('prediction changed primary substrate')
 after=frozen()
 if before!=after:raise RuntimeError('source drift during order capture')
 return {'worker':worker,'source_before':before,'source_after':after,'source_stable':before==after,
  'target':built['result']['removed_rule'],'operator':built['result']['kind'],'site':built['result']['site'],
  'proposal':built['candidate_rule'],'proposal_digest':built['proposal_digest'],
  'reference_label':built['reference_label'],'reference_digest':built['reference_digest'],
  'semantic_candidate_match':built['proposal_digest']==built['reference_digest'],
  'primary_target_preserved':built['primary_target_preserved'] and primary_preserved,'branch_receipts_verified':True,
  'composer_decision_ns':built['decision_ns'],'snapshot_creation_ns':snapshot_ns,'selections':selections}
def score_worker(order):
 before=frozen();sub,root,native,source,fault=boot_fault();snapshot=sub.snapshot()
 proposal=order['proposal'];primary_rules=native.export_rules();primary_rev=tuple(native.experiment_graph_rule_revision())
 results=[]
 for row in order['selections']:
  selected=row['selected'];rate=row['alias_rate_percent'];inputs=candidate_pool(order['worker'],rate)
  by_id={x['probe_id']:x for x in inputs};query=selected['query']
  if not selected.get('ok') or query.get('probe_id') not in by_id:raise RuntimeError('query is outside frozen pool')
  def oracle(env):return ('HOT',1.0) if env['score']>0 else ('COLD',1.0)
  predictions={p['hypothesis']:tuple(p['output']) for p in selected['predictions']}
  expected=oracle(query);survivors=[k for k,v in predictions.items() if v==expected]
  mode=row['mode'];random_env=row['random_env']
  random_trial_preds={'fault':predict_isolated(sub,snapshot,mode,fault,random_env),
   'proposal':predict_isolated(sub,snapshot,mode,proposal,random_env)}
  random_preds={k:v['output'] for k,v in random_trial_preds.items()}
  random_expected=oracle(random_env);random_survivors=[k for k,v in random_preds.items() if v==random_expected]
  results.append({'mode':mode,'alias_rate_percent':rate,'query':query,'expected':expected,'predictions':predictions,
   'survivors_after_oracle':survivors,'random_probe':{'env':random_env,'expected':random_expected,
   'predictions':random_preds,'branch_metrics':random_trial_preds,'survivors_after_oracle':random_survivors,
   'discriminates':random_preds['fault']!=random_preds['proposal']},
   'entropy_bits':selected['entropy_bits'],'partition_count':selected['partition_count'],
   'selector_wall_ns':row['selector_wall_ns'],'selector_cpu_ns':row['selector_cpu_ns'],
   'prediction_summary':row['prediction_summary']})
 heldout={}
 for mode in MODES:
  heldout[mode]=[]
  for i,score in enumerate((2.0,-2.0,0.0,3.0)):
   env={'probe_id':f'heldout_{i}','score':score,'positive':'HOT','negative':'COLD'}
   expected=oracle(env);pred_fault=predict_isolated(sub,snapshot,mode,fault,env);pred_prop=predict_isolated(sub,snapshot,mode,proposal,env)
   heldout[mode].append({'score':score,'expected':expected,'fault':pred_fault,'proposal':pred_prop,
    'fault_pass':pred_fault['output']==expected,'proposal_pass':pred_prop['output']==expected})
 source_preserved=native.export_rules()==primary_rules and tuple(native.experiment_graph_rule_revision())==primary_rev
 after=frozen()
 if before!=after:raise RuntimeError('source drift during score stage')
 return {'worker':order['worker'],'source_before':before,'source_after':after,'source_stable':before==after,
  'heldout':heldout,'primary_preserved':source_preserved,'branch_receipts_verified':True,'active_query_results':results}
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
  LOCK.write_text(json.dumps({'schema':'FreshRuleActiveQueryV1_1Lock','sources':frozen(),
   'semantic_engine':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'pool_size':POOL,
   'alias_rates_percent':ALIAS_RATES,'seed':SEED,'target':TARGET,'branch_backends':MODES,
   'isolation':'one fresh branch per hypothesis and candidate input'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return
 if not LOCK.exists():raise SystemExit('missing source lock')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT}'}
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('capture already exists')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-3000:]}')
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift while freezing orders')
  ORDERS.write_text(json.dumps({'schema':'FreshRuleActiveQueryV1_1Orders','lock_sha256':sha(LOCK),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'platform':platform.platform(),
   'machine':platform.machine(),'python':sys.version.split()[0]},'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'orders_frozen','workers':len(workers),'path':ORDERS.relative_to(ROOT).as_posix()}));return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or score exists')
  workers=[]
  for row in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(row),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"score worker {row['worker']}: {p.stderr[-3000:]}")
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=lock['sources']:raise SystemExit('source drift while scoring')
  SCORES.write_text(json.dumps({'schema':'FreshRuleActiveQueryV1_1Scores','orders_sha256':sha(ORDERS),
   'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(json.dumps({'stage':'scored_after_order_freeze','workers':len(workers),'path':SCORES.relative_to(ROOT).as_posix()}));return
 raise SystemExit('choose --lock, --orders, or --score')
if __name__=='__main__':main()
