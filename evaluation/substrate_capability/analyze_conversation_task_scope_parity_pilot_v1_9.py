#!/usr/bin/env python3
"""Independent checks for the exploratory task-scope closure parity pilot."""
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_9_lock_20261003.json'
CAP=ROOT/'evaluation/reports/conversation_task_scope_parity_pilot_v1_9_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_parity_pilot_v1_9_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 errors=[]
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());inputs=lock['locked_inputs']
 def req(ok,msg):
  if not ok:errors.append(msg)
 req(cap['locked_inputs']==inputs==cap['post_run_inputs'],'locked input drift')
 req(cap['checks'].get('nine_fresh_workers') is True,'fresh worker gate failed')
 req(cap['checks'].get('thirty_six_paired_cases') is True,'paired case count mismatch')
 rows=[];access_kinds=Counter();access_owner=Counter();trace_mult=0
 candidate_total=0;term_total=0;monolithic_candidate_total=0;monolithic_term_total=0
 full_fallback_total=0;local_match_total=0;local_pattern_total=0;mt_seed_total=0;rule_metrics=Counter()
 for run in cap['runs']:
  req(run['worker_index'] in range(9),'unexpected worker index')
  req(run['replicate'] in (0,1,2),'unexpected replicate')
  req(run['replicate']==run['worker_index']//3,'worker replicate mapping mismatch')
  req(run['scope_order_policy']==('ascending','descending','outside_in')[run['worker_index']%3],'scope-order assignment mismatch')
  req(len(run['cases'])==4,'worker case coverage mismatch')
  for case in run['cases']:
   mono=case['monolithic'];part=case['partition_sweep'];traced=case['partition_trace'];paired=case['paired']
   req(mono['final_graph_digest']==sha_json(mono['final_graph']),'monolithic digest mismatch')
   req(part['final_graph_digest']==sha_json(part['final_graph']),'partition digest mismatch')
   checkpoint_equal=[a['graph_digest']==b['graph_digest'] for a,b in zip(mono['checkpoints'],part['checkpoints'])]
   expected_checkpoints=10 if case['case_id']=='common_ground_stress' else 4*int(case['requested_goal_count'])
   req(len(mono['checkpoints'])==len(part['checkpoints'])==len(traced['checkpoints'])==expected_checkpoints,'checkpoint count mismatch')
   req(paired['final_graph_equal']==(mono['final_graph_digest']==part['final_graph_digest']),'final equality flag mismatch')
   req(paired['checkpoint_graph_equal']==checkpoint_equal,'checkpoint equality flags mismatch')
   req(all(checkpoint_equal),'checkpoint state mismatch')
   req(paired['goal_status_equal']==([g['status'] for g in mono['goals']]==[g['status'] for g in part['goals']]),'goal status flag mismatch')
   req(paired['goal_status_equal'],'goal status mismatch')
   trace_cp=[a['graph_digest']==b['graph_digest'] for a,b in zip(part['checkpoints'],traced['checkpoints'])]
   req(paired['trace_arm_final_equal']==(part['final_graph_digest']==traced['final_graph_digest']),'trace arm final flag mismatch')
   req(paired['trace_arm_checkpoint_equal']==trace_cp,'trace arm checkpoint flags mismatch')
   req(paired['trace_arm_final_equal'] and all(trace_cp),'partition trace-on/off state mismatch')
   req(all(checkpoint['closure'].get('status')=='fixed_point' for arm in (mono,part,traced) for checkpoint in arm['checkpoints']),'non-fixed-point closure')
   req(all(not checkpoint.get('deferred_effects_pending',False) for checkpoint in part['checkpoints']),'deferred work remains')
   req(all(checkpoint.get('scoped_calls',0)>0 for checkpoint in part['checkpoints']),'missing scoped closure accounting')
   req(all(sorted(q.get('frame') for q in checkpoint.get('scope_quiescence',[]))==checkpoint.get('scope_frame_ids') for checkpoint in part['checkpoints']),'scope quiescence coverage mismatch')
   def expected_order(frames,policy):
    if policy=='ascending':return list(frames)
    if policy=='descending':return list(reversed(frames))
    out=[];lo=0;hi=len(frames)-1
    while lo<=hi:
     out.append(frames[lo]);lo+=1
     if lo<=hi:out.append(frames[hi]);hi-=1
    return out
   req(all(checkpoint.get('scope_sweep_order')==expected_order(checkpoint.get('scope_frame_ids',[]),run['scope_order_policy'])
      for checkpoint in part['checkpoints']),'scope order record mismatch')
   req(all([q.get('frame') for q in checkpoint.get('scope_quiescence',[])]==checkpoint.get('scope_sweep_order')
      for checkpoint in part['checkpoints']),'quiescence order mismatch')
   req(all(q.get('progress_steps')==0 and q.get('deferred_effects_pending') is False for checkpoint in part['checkpoints'] for q in checkpoint.get('scope_quiescence',[])),'scope did not independently report quiescence')
   req(all(q.get('frame_notifications_complete') is False for checkpoint in part['checkpoints'] for q in checkpoint.get('scope_quiescence',[])),'unexpected notification completeness claim')
   for checkpoint in part['checkpoints']:
    counters=checkpoint.get('scale_counters',{})
    req(checkpoint.get('candidate_pairs')==counters.get('cand_enum',0),'candidate count/counter mismatch')
    req(checkpoint.get('term_evaluations')==counters.get('term_evals_total',0),'Term count/counter mismatch')
    candidate_total+=checkpoint.get('candidate_pairs',0);term_total+=checkpoint.get('term_evaluations',0)
    full_fallback_total+=counters.get('scoped_full_fallback_rule_matches',0)
    local_match_total+=counters.get('scoped_local_rule_matches',0)
    local_pattern_total+=counters.get('scoped_local_pattern_rule_matches',0)
    for row in checkpoint.get('scale_counters_by_rule',[]):
     rule_metrics[(row.get('rule_name','unknown'),row['metric'])]+=int(row['count'])
    mt_seed_total+=counters.get('scoped_mt_seeded_rule_matches',0)
   for checkpoint in mono['checkpoints']:
    monolithic_candidate_total+=checkpoint.get('candidate_pairs',0)
    monolithic_term_total+=checkpoint.get('term_evaluations',0)
   for checkpoint in traced['checkpoints']:
    req(checkpoint.get('trace_dropped')==0,'trace rows dropped')
    for event in checkpoint.get('runtime_access_trace_events',[]):
     req(event.get('rule_name') not in (None,'unknown'),'trace rule UID unresolved')
     access_kinds[event['kind']]+=1;trace_mult+=int(event.get('count',0))
     if event.get('node_frame') is None and event.get('peer_frame') is None: relation='both_shared_or_unowned'
     elif event.get('node_frame') is not None and event.get('peer_frame') is not None and event.get('node_frame')==event.get('peer_frame'): relation='same_frame'
     elif event.get('node_frame') is not None and event.get('peer_frame') is not None: relation='cross_frame'
     else: relation='one_endpoint_shared_or_unowned'
     access_owner[relation]+=int(event.get('count',0))
   expected_frames=4 if case['case_id']=='common_ground_stress' else int(case['requested_goal_count'])
   req(mono['frame_count']==part['frame_count']==expected_frames,'actual frame count mismatch')
   rows.append({'worker_index':run['worker_index'],'replicate':run['replicate'],'scope_order_policy':run['scope_order_policy'],
     'case_id':case['case_id'],'requested_goal_count':case['requested_goal_count'],
     'frame_count':mono['frame_count'],'final_equal':paired['final_graph_equal'],
     'checkpoint_count':len(mono['checkpoints']),'partition_scoped_calls':paired['partition_scoped_calls'],
     'monolithic_candidate_pairs':sum(x.get('candidate_pairs',0) for x in mono['checkpoints']),
     'monolithic_term_evaluations':sum(x.get('term_evaluations',0) for x in mono['checkpoints']),
     'partition_candidate_pairs':sum(x.get('candidate_pairs',0) for x in part['checkpoints']),
     'partition_term_evaluations':sum(x.get('term_evaluations',0) for x in part['checkpoints']),
     'monolithic_goal_statuses':[g['status'] for g in mono['goals']],
     'partition_goal_statuses':[g['status'] for g in part['goals']]})
 req(len(rows)==36,'independent row count mismatch')
 coverage=Counter((row['case_id'],row['requested_goal_count'],row['scope_order_policy']) for row in rows)
 req(coverage==Counter({(case,n,policy):3 for case,n in [('common_ground_stress',None),('concurrent_goals',2),
   ('concurrent_goals',4),('concurrent_goals',8)] for policy in ('ascending','descending','outside_in')}),'locked workload/order matrix mismatch')
 case_coverage={(case,n) for case,n,_policy in coverage}
 schedule_replicates=Counter((row['scope_order_policy'],row['replicate']) for row in rows)
 req(schedule_replicates==Counter({(policy,rep):4 for policy in ('ascending','descending','outside_in') for rep in (0,1,2)}),'replicate/order coverage mismatch')
 req(trace_mult>0,'partition trace empty')
 req(full_fallback_total>0,'no full-fallback scoped work observed')
 req(local_pattern_total>0,'multi-edge ownership-seeded path was not exercised')
 req(mt_seed_total==0,'unexpected microtheory seed path observed')
 out={'schema':'ConversationTaskScopeParityPilotV1_9Analysis','gates_pass':not errors,'errors':errors,
  'paired_cases':rows,'summary':{'paired_case_count':len(rows),'final_state_matches':sum(r['final_equal'] for r in rows),
   'checkpoint_count':sum(r['checkpoint_count'] for r in rows),'scoped_calls':sum(r['partition_scoped_calls'] for r in rows),
   'partition_candidate_pairs':candidate_total,'partition_term_evaluations':term_total,
   'scoped_full_fallback_rule_matches':full_fallback_total,'scoped_local_rule_matches':local_match_total,'scoped_local_pattern_rule_matches':local_pattern_total,
   'scoped_mt_seeded_rule_matches':mt_seed_total,
   'top_rules_by_candidate_pairs':dict(sorted(((name,count) for (name,metric),count in rule_metrics.items() if metric=='candidate_pairs'),key=lambda x:(-x[1],x[0]))[:20]),
   'top_rules_by_term_evaluations':dict(sorted(((name,count) for (name,metric),count in rule_metrics.items() if metric=='term_evaluations'),key=lambda x:(-x[1],x[0]))[:20]),
   'scope_path_counts_by_rule':{name:{metric:count for (rule,metric),count in sorted(rule_metrics.items()) if rule==name and metric.startswith('scoped_path_')} for name in sorted({rule for rule,metric in rule_metrics if metric.startswith('scoped_path_')})},
   'monolithic_candidate_pairs':monolithic_candidate_total,'monolithic_term_evaluations':monolithic_term_total,
   'candidate_pair_work_ratio':candidate_total/monolithic_candidate_total if monolithic_candidate_total else None,
   'term_evaluation_work_ratio':term_total/monolithic_term_total if monolithic_term_total else None,
   'partition_trace_multiplicity':trace_mult,'partition_trace_access_by_kind':dict(sorted(access_kinds.items())),
   'partition_trace_owner_relation':dict(sorted(access_owner.items())),
   'work_by_case':{f"{case}:{n}":{
     'monolithic_candidate_pairs':sum(r['monolithic_candidate_pairs'] for r in rows if r['case_id']==case and r['requested_goal_count']==n),
     'partition_candidate_pairs':sum(r['partition_candidate_pairs'] for r in rows if r['case_id']==case and r['requested_goal_count']==n),
     'monolithic_term_evaluations':sum(r['monolithic_term_evaluations'] for r in rows if r['case_id']==case and r['requested_goal_count']==n),
     'partition_term_evaluations':sum(r['partition_term_evaluations'] for r in rows if r['case_id']==case and r['requested_goal_count']==n),
     'partition_scoped_calls':sum(r['partition_scoped_calls'] for r in rows if r['case_id']==case and r['requested_goal_count']==n)}
     for case,n in sorted(case_coverage,key=lambda x:(str(x[0]),str(x[1])))},
   'frame_count_by_case':{f"{case}:{n}":next(r['frame_count'] for r in rows if r['case_id']==case and r['requested_goal_count']==n)
     for case,n in sorted(case_coverage,key=lambda x:(str(x[0]),str(x[1])))}},
  'analysis_script_sha256':sha(__file__),
  'claim_boundary':cap['claim_boundary']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errors))
def sha_json(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
if __name__=='__main__':raise SystemExit(main())
