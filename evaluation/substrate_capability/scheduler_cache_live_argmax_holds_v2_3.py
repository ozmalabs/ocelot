#!/usr/bin/env python3
"""Exercise evaluator-generated Argmax/Holds caches through checkpoint replay."""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import substrate_rs as sr
from domains.engine_provenance import assert_measuring_engine
from substrate.seed_loader import engine_rules_only
from substrate_rs import _native

RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_SCHEDULER_CACHE_LIVE_ARGMAX_HOLDS_V2_3_PREREG_20261004.md'
SEED=ROOT/'seeds/can_native_reimplementation.json'
SOURCES=('runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock','substrate/seed_loader.py')
LOCK=ROOT/'evaluation/substrate_capability/scheduler_cache_live_argmax_holds_v2_3_lock_20261004.json'
OUT=ROOT/'evaluation/reports/scheduler_cache_live_argmax_holds_v2_3_20261004.json'
CAP=100

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(SEED),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'sources':{x:sha(ROOT/x) for x in SOURCES}}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)

def build():
    s=sr.Substrate()._inner
    s.load_seed_manifest(engine_rules_only(json.loads(SEED.read_text())))
    rules=s.export_rules();rules=json.loads(rules) if isinstance(rules,str) else rules
    for i in reversed(range(len(rules))):s.remove_rule(i)
    owners=[]
    for group in ('alpha','beta'):
        owner=s.add_node('Microtheory',{'name':f'cache-{group}','group':group});owners.append(owner)
        for name,state in (('a',1),('b',3),('c',2)):
            nid=s.add_node('Concept',{'name':f'{group}-{name}','state':state});s.add_edge(owner,'has_concept',nid,{})
    s.define_concept('cache_state3',{'type':'And','items':[
        {'type':'Eq','a':{'type':'Attr','node':{'type':'Var','name':'x'},'key':'state'},'b':{'type':'Lit','value':3}},
        {'type':'Eq','a':{'type':'Attr','node':{'type':'Var','name':'y'},'key':'group'},'b':{'type':'Lit','value':'alpha'}}]})
    rule={'name':'cache_argmax_holds_fixture','match_type':'Microtheory','match':[['m','has_concept','c']],
        'where':{'type':'And','items':[
          {'type':'Eq','a':{'type':'Argmax','source':{'type':'Neighbours','node':{'type':'Var','name':'m'},'edge_type':'has_concept','any_type':False},'var_name':'candidate','value':{'type':'Attr','node':{'type':'Var','name':'candidate'},'key':'state'},'default':None},'b':{'type':'Var','name':'c'}},
          {'type':'Holds','concept':'cache_state3','node':{'type':'Var','name':'c'},'node2':{'type':'Var','name':'m'}}]},
        'effects':[['set_attr','c','picked',{'__term__':{'type':'Lit','value':1}}]]}
    s.add_rule(rule)
    steps=int(s.run_rules(CAP))
    return s,steps,owners

def snapshot(s):
    rules=s.export_rules();rules=json.loads(rules) if isinstance(rules,str) else rules
    return {'graph':s.graph_to_dict(),'rules':rules,'scheduler':s.rule_scheduler_checkpoint()}
def restore(state):
    s=sr.Substrate()._inner;s.graph_from_dict(state['graph']);s.import_rules_preserving_match_order(state['rules']);s.restore_rule_scheduler_checkpoint(state['scheduler']);return s
def run(s):
    s.scale_audit_set_enabled(False);s.scale_audit_set_per_rule_enabled(False);s.scale_audit_reset();s.scale_audit_per_rule_reset();s.scale_audit_set_per_rule_enabled(True);s.scale_audit_set_enabled(True)
    start=time.perf_counter_ns();steps=int(s.run_rules(CAP));elapsed=time.perf_counter_ns()-start
    glob={str(k):int(v) for k,v in dict(s.scale_audit_snapshot()).items() if not str(k).endswith('_ns') and k!='scheduler_plan_ns'}
    ids={int(a):(int(store),int(local)) for a,store,local in s.scale_audit_rule_identity_snapshot()};per={}
    for aid,metric,value in s.scale_audit_per_rule_snapshot():
        if int(aid) in ids:per.setdefault(str(ids[int(aid)][1]),{})[str(metric)]=int(value)
    s.scale_audit_set_per_rule_enabled(False);s.scale_audit_set_enabled(False)
    return {'steps':steps,'elapsed_ns':elapsed,'global':glob,'per_rule':per,'graph':s.graph_to_dict(),'scheduler':s.rule_scheduler_checkpoint()}

def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior cache-live artifacts')
        LOCK.write_text(json.dumps({'schema':'SchedulerCacheLiveArgmaxHoldsV2_3Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale cache-live source lock')
    source,initial_steps,owners=build();initial=snapshot(source);counts=initial['scheduler']['eval_cache']['entry_counts']
    # Wake all rules without a semantic graph mutation so the exact populated
    # memo state remains valid at the captured scheduler boundary.
    source.force_all_dirty();state=snapshot(source);state['scheduler']['any_mutation']=False
    live=restore(state);replay=restore(state)
    live_rt=live.rule_scheduler_checkpoint()==state['scheduler'];replay_rt=replay.rule_scheduler_checkpoint()==state['scheduler']
    live_out=run(live);replay_out=run(replay)
    replay.set_attr(sr.NodeID(owners[0].value),'group','changed')
    graph_now=replay.graph_to_dict()
    alpha_winner=next(n for n in graph_now['nodes'] if n['type']=='Concept' and n['attrs'].get('name')=='alpha-b')
    replay.set_attr(sr.NodeID(int(alpha_winner['id'])),'picked',0)
    mutation_pending=replay.rule_scheduler_checkpoint()['any_mutation']
    invalidated_counts=replay.rule_scheduler_checkpoint()['eval_cache']['entry_counts']
    mutated_out=run(replay);post_mutation_counts=mutated_out['scheduler']['eval_cache']['entry_counts']
    replay.force_all_dirty();refresh=snapshot(replay);refresh['scheduler']['any_mutation']=False
    replay.restore_rule_scheduler_checkpoint(refresh['scheduler'])
    rebuilt_out=run(replay);mutated_counts=rebuilt_out['scheduler']['eval_cache']['entry_counts'];post=inputs()
    graph_after_mutation=mutated_out['graph']
    alpha_winner_after=next(n for n in graph_after_mutation['nodes'] if n['type']=='Concept' and n['attrs'].get('name')=='alpha-b')
    holds_after=rebuilt_out['scheduler']['eval_cache']['holds']
    checks={'source_stable':locked==post,'initial_run_progressed':initial_steps>0,'argmax_populated_by_evaluator':counts[3]>0,'holds_populated_by_evaluator':counts[4]>0,
      'multiple_argmax_binding_keys':counts[3]>=2,'multiple_two_node_holds_keys':counts[4]>=2,
      'neighbours_populated_by_evaluator':counts[1]>=2,'live_and_replay_restore_exact':live_rt and replay_rt,
      'global_work_exact':live_out['global']==replay_out['global'],'per_rule_work_exact':canonical(live_out['per_rule'])==canonical(replay_out['per_rule']),
      'graph_after_exact':canonical(live_out['graph'])==canonical(replay_out['graph']),'scheduler_after_exact':canonical(live_out['scheduler'])==canonical(replay_out['scheduler']),
      'mutation_pending_before_next_pass':mutation_pending,'stale_holds_cleared_after_mutation_pass':post_mutation_counts[4]==0,
      'stale_holds_did_not_refire_effect':alpha_winner_after['attrs'].get('picked')==0,
      'mutated_holds_recomputed_false':any(row[3] is False for row in holds_after),'mutated_cache_families_rebuilt':mutated_counts[3]>=2 and mutated_counts[4]>=1}
    result={'schema':'SchedulerCacheLiveArgmaxHoldsV2_3','locked_inputs':locked,'post_run_inputs':post,'initial_steps':initial_steps,'captured_cache_counts':counts,
      'invalidated_cache_counts':invalidated_counts,'post_mutation_cache_counts':post_mutation_counts,'mutated_cache_counts':mutated_counts,'live':live_out,'replay':replay_out,'mutated_replay':mutated_out,'rebuilt_replay':rebuilt_out,'checks':checks,'passed':all(checks.values()),
      'claim_limit':'small synthetic graph with two outer bindings and one authored rule; evaluator naturally populates neighbour/argmax/two-node-Holds entries; verifies pre-pass mutation invalidation and recomputation but does not establish natural-task prevalence or scaling'}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'cache_counts':counts,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
