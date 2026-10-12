#!/usr/bin/env python3
"""Active choice among host-enumerated ordered attribute swaps."""
from __future__ import annotations
import copy,hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_attribute_site_active_choice_v2.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_ATTRIBUTE_SITE_GRAPH_SELECTION_V2_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_attribute_site_active_choice_v2_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_attribute_site_active_choice_v2_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_attribute_site_active_choice_v2_scores_20261002.json'
WORKERS=4;MODES=('cow_snapshot','full_copy');RATES=(0,50,90,99);TARGET='classify_meter_delta'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_attribute_site_active_query_v1.py'
BASE_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_attribute_site_active_query_v1.py'
ACTIVE=('domains/reflective_faculty.py','domains/edit_ops.py','domains/self_correction.py','domains/contract_query.py','domains/engine_provenance.py',
 'substrate/boot_core.py','substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs',
 'runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs',
 'runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py','seeds/relation_vocabulary.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in ACTIVE]+[RUNNER,ANALYZER,PROTOCOL,BASE_RUNNER,BASE_ANALYZER]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths};out['loaded_native_binary']=sha(Path(_native.__file__).resolve());return out
def sem_digest(rule):
 v=copy.deepcopy(rule)
 for k in ('name','content_hash','revision','rule_uid','active'):v.pop(k,None)
 return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def prepare(worker,cue=False):
 from thoughtexperiment_attribute_site_active_query_v1 import boot_fault,Agent
 import domains.reflective_faculty as rf
 from domains.self_correction import _default_candidates
 sub,root,native,source,fault=boot_fault();compose_ns=0;composition=None
 if cue:
  key=f'active_choice_{worker}'
  sub.add_node('CapabilityAxis',{'is_axis':1.0,'capability_keys':[key],'induced':1.0,
   'residual_predicates':['classify','meter','delta','swap','attribute'],
   'structural_rule_scope':'all_mutable_rules','from_observation':1.0,'source':'attribute_site_active_choice_v2'})
  t=time.perf_counter_ns();composition=rf.compose_general_structural_variant(Agent(sub,root),[key],f'active_choice_{worker}');compose_ns=time.perf_counter_ns()-t
 primary=next(copy.deepcopy(r) for r in native.export_rules() if r.get('name')==TARGET and r.get('active',True))
 t=time.perf_counter_ns();all_candidates=_default_candidates(native,TARGET);enum_ns=time.perf_counter_ns()-t
 by_label={c['label']:c for c in all_candidates}
 labels=('swap_term_leaf:bad_score->good_score','swap_term_leaf:good_score->bad_score')
 if any(k not in by_label for k in labels):raise RuntimeError('required generic swap candidate missing')
 proposals={'fault':fault,'forward':by_label[labels[0]]['rules'][TARGET],'reverse':by_label[labels[1]]['rules'][TARGET]}
 current=next(copy.deepcopy(r) for r in native.export_rules() if r.get('name')==TARGET and r.get('active',True))
 if current!=primary:raise RuntimeError('primary target changed during candidate construction')
 return sub,root,native,proposals,{'composition_built':bool(composition.get('built')) if composition else None,
  'composition_wall':composition.get('wall') if composition else None,'composer_ns':compose_ns,'enumerator_ns':enum_ns,
  'candidate_labels':sorted(c['label'] for c in all_candidates),'proposal_digests':{k:sem_digest(v) for k,v in proposals.items()},'primary_unchanged':True}
def pool(worker,rate):
 neutral=round(100*rate/100);rows=[]
 for i in range(100):
  good=1.0 if (i+worker)%2==0 else -1.0;bad=good if i>=100-neutral else -good
  rows.append({'probe_id':f'w{worker}_r{rate}_i{i}','bad_score':bad,'good_score':good,'positive':'HOT','negative':'COLD'})
 random.Random(55103+worker*1000+rate).shuffle(rows);return rows
def evaluate(sub,native,snapshot,mode,rule,env):
 from thoughtexperiment_attribute_site_active_query_v1 import predict_isolated
 return predict_isolated(sub,snapshot,mode,rule,env)
def order_worker(worker):
 from domains.contract_query import select_discriminating_input
 sub,root,native,props,meta=prepare(worker,cue=True);rev=tuple(native.experiment_graph_rule_revision());rules=native.export_rules();snapshot=sub.snapshot()
 ids=[{'id':k,'term':{'type':'Lit','value':k}} for k in ('fault','forward','reverse')];choices=[]
 for mode in MODES:
  for rate in RATES:
   inputs=pool(worker,rate);metrics={}
   def pred(term,env):
    arm=native.evaluate(term,env);key=(arm,env['probe_id'])
    if key not in metrics:metrics[key]=evaluate(sub,native,snapshot,mode,props[arm],env)
    return metrics[key]['output'][0]
   w=time.perf_counter_ns();cpu=time.process_time_ns();selected=select_discriminating_input(pred,ids,inputs);wall=time.perf_counter_ns()-w;cpu_ns=time.process_time_ns()-cpu
   random_env=random.Random(55103+worker*1000+rate).choice(inputs)
   metric_rows=[{'hypothesis':arm,'probe_id':probe,**value} for (arm,probe),value in sorted(metrics.items())]
   choices.append({'mode':mode,'alias_rate_percent':rate,'pool':inputs,'pool_sha256':hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
    'selected':selected,'selector_wall_ns':wall,'selector_cpu_ns':cpu_ns,'prediction_calls':len(metrics),'predictions':metric_rows,
    'random_env':random_env})
 if native.export_rules()!=rules or tuple(native.experiment_graph_rule_revision())!=rev:raise RuntimeError('primary revision changed')
 return {'worker':worker,'meta':meta,'choices':choices,'primary_preserved':True,'source_hashes':frozen()}
def score_worker(order):
 from domains.contract_query import select_candidate_from_graph_evidence
 sub,root,native,props,meta=prepare(order['worker'],cue=False);snapshot=sub.snapshot();results=[]
 primary_rules=native.export_rules()
 oracle=lambda e:('HOT',1.0) if e['good_score']>0 else ('COLD',1.0)
 for c in order['choices']:
  env=c['selected'].get('query',{});expected=oracle(env) if env else None
  pred={k:tuple(evaluate(sub,native,snapshot,c['mode'],r,env)['output']) for k,r in props.items()} if env else {}
  random_env=c['random_env'];rand={k:tuple(evaluate(sub,native,snapshot,c['mode'],r,random_env)['output']) for k,r in props.items()}
  
  evidence=[{'proposal_id':k,'probe_id':env.get('probe_id','missing'),
   'predicted':v[0],'expected':expected[0]} for k,v in pred.items()] if env else []
  fork_start=time.perf_counter_ns();selection_branch=snapshot.fork();selection_fork_ns=time.perf_counter_ns()-fork_start
  decision_start=time.perf_counter_ns()
  decision=select_candidate_from_graph_evidence(selection_branch,f'active_choice_v2_w{order["worker"]}_{c["mode"]}_{c["alias_rate_percent"]}',
   [{'proposal_id':k,'proposal_label':k} for k in props],evidence)
  decision_ns=time.perf_counter_ns()-decision_start
  decision.pop('proposal_node',None)
  residual_id=None;residual_start=time.perf_counter_ns()
  if decision.get('ok'):
   residual_id=sub.add_node('ExperimentResidual',{'experiment_id':f'active_choice_v2_w{order["worker"]}_{c["mode"]}_{c["alias_rate_percent"]}',
    'selected_candidate_id':decision['proposal_id'],'probe_id':env['probe_id'],'matching_evidence_count':decision['matching_evidence_count'],
    'source':'thoughtexperiment_attribute_site_active_choice_v2'})
  residual_ok=bool(residual_id is not None and sub.node(residual_id)['attrs'].get('selected_candidate_id')==decision.get('proposal_id'))
  residual_return_ns=time.perf_counter_ns()-residual_start
  results.append({'mode':c['mode'],'alias_rate_percent':c['alias_rate_percent'],'query':env,'expected':expected,'predictions':pred,
   'survivors':[k for k,v in pred.items() if v==expected],'graph_decision':decision,'graph_decision_ns':decision_ns,
   'selection_branch_fork_ns':selection_fork_ns,'residual_returned_to_primary':residual_ok,'residual_return_ns':residual_return_ns,
   'random_probe':{'env':random_env,'expected':oracle(random_env),'predictions':rand,
    'survivors':[k for k,v in rand.items() if v==oracle(random_env)]}})
 held=[]
 for bad,good in ((-2.,2.),(2.,-2.),(0.,0.),(-3.,3.),(3.,-3.)):
  env={'probe_id':f'held_{len(held)}','bad_score':bad,'good_score':good,'positive':'HOT','negative':'COLD'};expected=oracle(env)
  held.append({'env':env,'expected':expected,'predictions':{k:evaluate(sub,native,snapshot,'cow_snapshot',r,env)['output'] for k,r in props.items()}})
 controls=[]
 pids=[{'proposal_id':'a','proposal_label':'A'},{'proposal_id':'b','proposal_label':'B'}]
 control_branch=snapshot.fork()
 tie=[{'proposal_id':'a','probe_id':'q1','predicted':'x','expected':'x'},
  {'proposal_id':'a','probe_id':'q2','predicted':'x','expected':'z'},
  {'proposal_id':'b','probe_id':'q1','predicted':'x','expected':'z'},
  {'proposal_id':'b','probe_id':'q2','predicted':'z','expected':'z'}]
 tie_result=select_candidate_from_graph_evidence(control_branch,f'tie_w{order["worker"]}',pids,tie)
 duplicate_result=select_candidate_from_graph_evidence(control_branch,f'tie_w{order["worker"]}',pids,tie)
 zero=[{'proposal_id':pid,'probe_id':'q','predicted':'wrong','expected':'right'} for pid in ('a','b')]
 zero_result=select_candidate_from_graph_evidence(control_branch,f'zero_w{order["worker"]}',pids,zero)
 before_nodes=sum(len(control_branch.nodes(t)) for t in ('CandidateProposal','CandidateEvidence'))
 incomplete=select_candidate_from_graph_evidence(control_branch,f'incomplete_w{order["worker"]}',pids,
  [{'proposal_id':'a','probe_id':'q','predicted':'x','expected':'x'}])
 after_nodes=sum(len(control_branch.nodes(t)) for t in ('CandidateProposal','CandidateEvidence'))
 controls={'tie_abstains':not tie_result.get('ok'),'duplicate_namespace_rejected':not duplicate_result.get('ok'),
  'zero_match_abstains':not zero_result.get('ok'),'incomplete_coverage_rejected':not incomplete.get('ok'),
  'incomplete_rejection_did_not_mutate_graph':before_nodes==after_nodes,
  'tie_reason':tie_result.get('reason'),'duplicate_reason':duplicate_result.get('reason'),
  'zero_reason':zero_result.get('reason'),'incomplete_reason':incomplete.get('reason')}
 primary_preserved=native.export_rules()==primary_rules
 primary_clean=not sub.nodes('CandidateProposal') and not sub.nodes('CandidateEvidence') and len(sub.nodes('ExperimentResidual'))==len(results)
 return {'worker':order['worker'],'meta':meta,'results':results,'heldout':held,'controls':controls,'primary_preserved':primary_preserved,
  'primary_contains_only_residuals':primary_clean,'source_hashes':frozen()}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT / "runners/dsl/python"}:{ROOT / "evaluation/substrate_capability"}:{ROOT}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)):raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'AttributeSiteActiveChoiceV2Lock','sources':frozen(),'semantic_engine':rust_source_fingerprint(str(ROOT)),
   'workers':WORKERS,'modes':MODES,'alias_rates':RATES,'hypotheses':['fault','forward','reverse']},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if not LOCK.exists() or frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('missing lock or source drift')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists():raise SystemExit('capture exists')
  ws=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--order-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source drift while ordering')
  ORDERS.write_text(json.dumps({'schema':'AttributeSiteActiveChoiceV2Orders','lock_sha256':sha(LOCK),'workers':ws,'host':{'platform':platform.platform(),'python':sys.version.split()[0]}},indent=2,sort_keys=True)+'\n');print(ORDERS);return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit('missing orders or existing score')
  ws=[]
  for o in json.loads(ORDERS.read_text())['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(o),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr[-3000:])
   ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
  SCORES.write_text(json.dumps({'schema':'AttributeSiteActiveChoiceV2Scores','orders_sha256':sha(ORDERS),'workers':ws},indent=2,sort_keys=True)+'\n');print(SCORES);return
 if sys.argv[1:2]==['--order-worker']:print(json.dumps(order_worker(int(sys.argv[2])),separators=(',',':')));return
 if sys.argv[1:2]==['--score-worker']:print(json.dumps(score_worker(json.load(sys.stdin)),separators=(',',':')));return
 raise SystemExit('use --lock, --orders, --score, --order-worker, or --score-worker')
if __name__=='__main__':main()
