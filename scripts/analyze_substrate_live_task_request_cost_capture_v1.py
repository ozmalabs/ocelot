#!/usr/bin/env python3
"""Independent integrity and work attribution for lock-scoped live task costs."""
from __future__ import annotations
import hashlib,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_task_request_cost_capture_v1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_task_request_cost_capture_v1_analysis_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/live_task_request_cost_capture_v1_lock_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text())['locked_inputs']; runs=raw['runs']; checks={}
 checks['three_fresh_processes']=len(runs)==3 and len({r['pid'] for r in runs})==3
 checks['source_native_identity_stable']=raw['locked_inputs']==lock==raw['post_run_inputs'] and all(r['worker_started_inputs']==lock==r['worker_finished_inputs'] for r in runs)
 checks['task_schedule_and_lifecycle']=all(r['threads_joined'] and not r['errors'] and r['b_was_serialized'] and not r['b_completed_while_a_blocked'] and r['event_order_gate'] and r['identity_gate'] and r['lifecycle_gate'] and r['pause_gate'] for r in runs)
 checks['semantic_graph_reproduces']=len({r['whole_graph_semantic_sha256'] for r in runs})==1 and len({json.dumps(r['final'],sort_keys=True) for r in runs})==1
 replies={(r['replies'].get('A'),r['replies'].get('B')) for r in runs}
 checks['reply_pair_reproduces']=len(replies)==1
 checks['two_lock_intervals_per_worker']=all(set(r['request_cost'])=={'request-A','request-B'} and set(r['request_counter_pre_reset'])=={'request-A','request-B'} for r in runs)
 arity_work=Counter();event_work=Counter();request_rows=defaultdict(list);timing_rows=defaultdict(list);global_totals={};request_arity=defaultdict(Counter);request_rule=defaultdict(Counter);attribution_anomalies=defaultdict(list)
 for r in runs:
  event_snaps=r['event_rule_patterns'];checks[f"rep{r['replicate']}_event_pattern_history_complete"]=len(event_snaps)==6 and all(len(x['patterns'])>0 for x in event_snaps)
  for req,cost in r['request_cost'].items():
   gm=cost['global']; per=cost['per_rule']; clause=cost['per_clause'];patterns=cost['rule_patterns_end']
   by_rule=Counter();unknown=[]
   for idx,metric,value in per:
    idx=int(idx);metric=str(metric);value=int(value)
    info=patterns.get(str(idx))
    if info is None:unknown.append(idx)
    if metric=='candidate_tests' and info is not None:
     by_rule[idx]+=value; arity_work[int(info['match_arity'])]+=value; request_arity[req][int(info['match_arity'])]+=value; request_rule[req][info['rule_name']]+=value
   checks[f"rep{r['replicate']}_{req}_all_rule_slots_mapped"]=not unknown
   clause_unknown=[{'rule_index':int(i),'clause_position':int(pos),'candidate_tests':int(v),'rule_name':patterns.get(str(int(i)),{}).get('rule_name'),'match_arity':patterns.get(str(int(i)),{}).get('match_arity')} for i,pos,v in clause if str(int(i)) not in patterns or int(pos)>=int(patterns[str(int(i))]['match_arity'])]
   attribution_anomalies[req].extend([{'replicate':r['replicate'],**x} for x in clause_unknown])
   rule_total=sum(by_rule.values()); global_candidate=int(gm.get('cand_tested',0))
   checks[f"rep{r['replicate']}_{req}_per_rule_candidate_conservation"]=rule_total==global_candidate
   clause_total=sum(int(v) for _,_,v in clause)
   checks[f"rep{r['replicate']}_{req}_per_clause_candidate_conservation"]=clause_total==global_candidate
   checks[f"rep{r['replicate']}_{req}_positive_candidate_work"]=global_candidate>0
   global_totals.setdefault(req,[]).append(global_candidate)
   request_rows[req].append({'replicate':r['replicate'],'candidate_tests':global_candidate,'rule_candidate_tests':rule_total,'clause_candidate_tests':clause_total,'rule_count':len(patterns),'active_rule_count':sum(bool(x['active']) for x in patterns.values()),'per_rule':per,'per_clause':clause,'patterns':patterns,'global':gm})
   timing_rows[req].append({'replicate':r['replicate'],'lock_wall_ns':cost['wall_ns'],'lock_thread_cpu_ns':cost['thread_cpu_ns'],'call_wall_ns':r['call_timings']['A' if req=='request-A' else 'B']['wall_ns'],'call_thread_cpu_ns':r['call_timings']['A' if req=='request-A' else 'B']['thread_cpu_ns']})
  checks[f"rep{r['replicate']}_counter_reset_boundaries_clean"]=set(r['request_counter_pre_reset'])=={'request-A','request-B'} and set(r.get('request_counter_after_reset',{}))=={'request-A','request-B'} and all(int(x['global'].get('cand_tested',0))==0 and not x['per_rule'] and not x['per_clause'] for x in r['request_counter_after_reset'].values())
 # Arity distribution is aggregated across all request intervals and workers.
 grand=sum(global_totals['request-A'])+sum(global_totals['request-B'])
 by_arity={str(k):{'candidate_tests':v,'share':v/grand if grand else 0.0} for k,v in sorted(arity_work.items())}
 medians={}
 for req,vals in global_totals.items():medians[req]={'per_worker_candidate_tests':vals,'median_candidate_tests':statistics.median(vals),'min':min(vals),'max':max(vals)}
 arity_summary={req:{str(k):{'candidate_tests':v,'share':v/sum(request_arity[req].values())} for k,v in sorted(counts.items())} for req,counts in request_arity.items()}
 top_rules={req:[{'rule_name':name,'candidate_tests':count} for name,count in request_rule[req].most_common(10)] for req in request_rule}
 payload={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analysis_sha256':sha(Path(__file__).resolve()),'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'capture_integrity_pass':all(checks.values()),'rule_attribution_gate_pass':not any(attribution_anomalies.values()),'rule_attribution_anomalies':{k:{'row_count':len(v),'examples':v[:12]} for k,v in attribution_anomalies.items()},'task_semantic_reply_gate_pass':all(r['reply_parity'] for r in runs),'reply_pairs':[{'A':a,'B':b} for a,b in sorted(replies)],'request_candidate_summary':medians,'candidate_work_by_match_arity_diagnostic_untrusted':by_arity,'candidate_work_by_request_and_match_arity_diagnostic_untrusted':arity_summary,'top_rules_by_request_diagnostic_untrusted':top_rules,'candidate_work_total':grand,'request_cost_rows':dict(request_rows),'timing_rows':dict(timing_rows),'claim_boundary':'Three fresh-process repeats of one authored serialized describe_scene fixture. Candidate totals cover exact observed outer conversation-lock intervals, not Python work before acquisition, after release, boot, or lock wait. Audit counters are enabled during the interval; timing is instrumented. Request A legacy reply gate is expected to fail; this is work/failure characterization, not successful task-quality or population prevalence evidence.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture_integrity_pass':payload['capture_integrity_pass'],'task_semantic_reply_gate_pass':payload['task_semantic_reply_gate_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'request_candidate_summary':medians,'rule_attribution_gate_pass':payload['rule_attribution_gate_pass'],'rule_attribution_anomalies':payload['rule_attribution_anomalies'],'candidate_work_total':grand},indent=2))
 if not payload['capture_integrity_pass']:raise SystemExit(1)
if __name__=='__main__':main()
