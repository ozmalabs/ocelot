#!/usr/bin/env python3
"""Verify current live-task pattern/work join and summarize high-work joins."""
from __future__ import annotations
import hashlib,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_workers_raw_20260927.json'
GRAPH=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_runtime_graph_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_analysis_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/live_task_runtime_join_capture_v1_lock_20260927.json'
def sha_bytes(x):return hashlib.sha256(x).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw['runs'];graph=json.loads(GRAPH.read_text());checks={}
 checks['three_fresh_processes']=len(runs)==3 and len({r['pid'] for r in runs})==3
 checks['source_native_identity_stable']=raw['locked_inputs']==lock==raw['post_run_inputs'] and all(r['before']==lock==r['after'] for r in runs)
 checks['representative_graph_snapshot_hash_and_counts']=sha_bytes(canon(graph))==raw['runtime_graph_sha256'] and len(graph.get('nodes',[]))==raw['runs'][0]['runtime_graph_checkpoint']['node_count'] and len(graph.get('edges',[]))==raw['runs'][0]['runtime_graph_checkpoint']['edge_count']
 checks['runtime_graph_is_pre_action_checkpoint']=all(r['runtime_graph_checkpoint']['event_kind']=='action_result' and r['runtime_graph_checkpoint']['thread']=='request-B' for r in runs)
 checks['task_schedule_identity_lifecycle_and_reply_records']=all(r['task']['threads_joined'] and not r['task']['errors'] and r['task']['b_was_serialized'] and not r['task']['b_completed_while_a_blocked'] and r['task']['event_order_gate'] and r['task']['identity_gate'] and r['task']['lifecycle_gate'] and r['task']['pause_gate'] and set(r['task']['replies'])=={'A','B'} for r in runs)
 reply_pairs={(r['task']['replies'].get('A'),r['task']['replies'].get('B')) for r in runs}
 checks['actual_reply_outcomes_reproduce']=len(reply_pairs)==1
 checks['three_complete_producer_sequences']=all(len(r['task']['producer_work'])==6 and len(r['producer_rule_work'])>0 for r in runs)
 checks['final_semantic_task_graphs_reproduce']=len({r['task']['whole_graph_semantic_sha256'] for r in runs})==1
 # Validate RuleIdx map and native candidate-test conservation at each producer interval.
 by_event=[];multi_by_key=defaultdict(list);pattern_digests=[]
 for r in runs:
  patterns={int(x['rule_index']):x for x in r['rule_patterns']}
  checks[f"rep{r['replicate']}_active_rule_map_aligned"]=len(patterns)==len(r['rule_patterns']) and all(p['rule_name'] for p in patterns.values())
  checks[f"rep{r['replicate']}_active_rule_count_matches"]=sum(bool(p['active']) for p in patterns.values())==r['active_rule_count']
  for event in r['task']['producer_work']:
   counters=event['counters'];n=sum(int(c) for idx,metric,c in counters['per_rule'] if metric=='candidate_tests')
   checks[f"rep{r['replicate']}_{event['thread']}_{event['kind']}_candidate_conservation"]=n==int(counters['scale'].get('cand_tested',0))
  event_patterns={(e['thread'],e['kind'],e['goal_id']):snap for e,snap in zip(r['task']['producer_work'],r['event_rule_patterns'])}
  for item in r['multi_edge_firing_work']:
   info=event_patterns.get((item['thread'],item['event_kind'],item['goal_id']),{}).get(item['rule_index'])
   checks[f"rep{r['replicate']}_{item['thread']}_{item['event_kind']}_pattern_join"]=bool(info and info['active'] and info['match_arity']>=3 and info['match']==item['match'] and item['candidate_tests']>0)
   key=(item['thread'],item['event_kind'],item['rule_index'],item['rule_name'],json.dumps(item['match'],sort_keys=True))
   multi_by_key[key].append(item)
  pattern_digests.append(sha_bytes(canon(r['rule_patterns'])))
 checks['same_active_rule_pattern_table_each_worker']=len(set(pattern_digests))==1
 # Stable aggregation across all event/replicate observations.
 summary=[]
 for key,vals in sorted(multi_by_key.items(),key=lambda kv:(-sum(v['candidate_tests'] for v in kv[1]),kv[0][0],kv[0][1],kv[0][3])):
  th,kind,idx,name,match_json=key
  summary.append({'thread':th,'event_kind':kind,'rule_index':idx,'rule_name':name,'match':json.loads(match_json),
    'match_arity':len(json.loads(match_json)),'replicate_count':len(vals),'candidate_tests_total':sum(v['candidate_tests'] for v in vals),
    'candidate_tests_median':statistics.median(v['candidate_tests'] for v in vals),
    'candidate_pairs_total':sum(v['candidate_pairs'] for v in vals),'term_evaluations_total':sum(v['term_evaluations'] for v in vals),
    'candidate_tests_by_replicate':[v['candidate_tests'] for v in vals]})
 task_semantic_gate_pass=all(r['task']['reply_parity'] for r in runs)
 payload={'schema_version':1,'raw_sha256':sha(RAW),'runtime_graph_sha256':sha(GRAPH),'analysis_sha256':sha(Path(__file__).resolve()),
  'checks':checks,'capture_integrity_pass':all(checks.values()),'task_semantic_gate_pass':task_semantic_gate_pass,
  'observed_reply_pairs':[{'A':a,'B':b} for a,b in sorted(reply_pairs)],'all_checks_pass':all(checks.values()),'checks_passed':sum(checks.values()),'checks_total':len(checks),
  'replicates':len(runs),'active_rule_count':runs[0]['active_rule_count'],'multi_edge_rule_event_rows':sum(len(r['multi_edge_firing_work']) for r in runs),
  'multi_edge_rule_event_summary':summary,
  'runtime_graph_checkpoint':{'path':str(GRAPH.relative_to(ROOT)),'sha256':sha(GRAPH),'node_count':len(graph['nodes']),'edge_count':len(graph['edges']),
   'captured_before':'request-B action_result event/closure path'},
  'claim_boundary':'Current-source three-repeat replay of one authored describe_scene concurrent fixture. Native per-rule candidate counters cover the six _record_live_goal_event closures only. Active rule match patterns are captured at boot; one pre-action graph snapshot is retained. This is partial task-level work evidence, not full converse closure accounting or population prevalence.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture_integrity_pass':payload['capture_integrity_pass'],'task_semantic_gate_pass':task_semantic_gate_pass,'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'multi_edge_rows':payload['multi_edge_rule_event_rows'],'top_rules':summary[:10]},indent=2))
 if not payload['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
