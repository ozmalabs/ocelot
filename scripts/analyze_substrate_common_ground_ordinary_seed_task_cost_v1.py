#!/usr/bin/env python3
"""Independent gate and stage-cost analysis for the ordinary seed replay."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/common_ground_ordinary_seed_task_cost_v1_raw_20260929.json'
OUT=ROOT/'evaluation/reports/common_ground_ordinary_seed_task_cost_v1_analysis_20260929.json'
LOCK=ROOT/'evaluation/substrate_capability/common_ground_ordinary_seed_task_cost_v1_lock_20260929.json'
EXPECTED_PATHS={'0':[4,5,6],'1':[7,8,9]}
EXPECTED_GROUNDS=[['calendar_checked','location_shared'],['calendar_request','calendar_shared']]
TIMERS=('python_module_import_wall','python_module_import_cpu','fixture_load','adapter_init_wall','adapter_init_cpu','seed_load_wall','seed_load_cpu',
 'chat_state_setup_wall','chat_state_setup_cpu','event_construction_wall_total','event_construction_cpu_total',
 'closure_wall_total','closure_cpu_total','terminal_probe_wall','terminal_probe_cpu','full_task_wall','full_task_cpu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs']
 checks={'ten_workers':len(runs)==10 and all('worker_error' not in x for x in runs)}
 workers=[x['worker'] for x in runs if 'worker' in x]
 checks['replicate_ids_complete']=len(workers)==10 and {w['replicate'] for w in workers}==set(range(10))
 checks['unique_fresh_processes']=len(workers)==10 and len({w['pid'] for w in workers})==10
 checks['source_native_lock_stable']=raw['locked_inputs']==locked==raw['post_run_inputs'] and all(x.get('before')==locked==x.get('after') for x in runs if 'worker' in x)
 grouped={};rows=[]
 for w in workers:
  rep=w['replicate'];key=f'r{rep}';timing=w['timings_ns'];cp=w['checkpoints']
  checks[key+'_seed_load_and_rule_inventory']=bool(w['loaded_seed_ids']) and sorted(w['active_lifecycle_rules'])==['discourse_goal_execute','discourse_goal_resolve','discourse_goal_select']
  checks[key+'_event_and_goal_counts']=w['event_count']==10 and w['goal_count']==2 and w['fixture_links_added']==6
  checks[key+'_task_identity_oracle']=w['task_oracle_pass'] and w['final_paths']==EXPECTED_PATHS
  normalized=sorted([sorted(x) for x in w['common_grounds']])
  checks[key+'_common_ground_oracle']=w['common_ground_oracle_pass'] and normalized==EXPECTED_GROUNDS
  checks[key+'_ten_ordinary_closures']=len(cp)==10 and all(isinstance(x['progress_steps'],int) and x['progress_steps']>=0 for x in cp)
  checks[key+'_terminal_no_change_probe']=w['terminal_probe']['progress_steps']==0 and w['terminal_probe']['graph_unchanged']
  checks[key+'_scale_counters_never_enabled']=all(int(v)==0 for v in w['scale_audit_counters'].values())
  checks[key+'_ordinary_api_declared']=w.get('closure_api')=='inner.run_rules' and w.get('audit_enable_calls')==0
  checks[key+'_all_timers_nonnegative']=all(int(timing[k])>=0 for k in TIMERS)
  checks[key+'_checkpoint_semantics']=all(x['paths'] and x['node_count']>0 and x['edge_count']>0 for x in cp)
  grouped[rep]=w
  rows.append({'replicate':rep,'pid':w['pid'],'loaded_seed_ids':w['loaded_seed_ids'],
   'active_lifecycle_rules':w['active_lifecycle_rules'],'final_digest':w['final_digest'],
   'final_node_count':w['final_node_count'],'final_edge_count':w['final_edge_count'],
   'timings_ns':timing,'closure_progress_steps':[int(x['progress_steps']) for x in cp],
   'closure_wall_ns_by_event':[int(x['closure_wall_ns']) for x in cp],
   'closure_cpu_ns_by_event':[int(x['closure_cpu_ns']) for x in cp],
   'peak_rss_kib':int(w['peak_rss_kib'])})
 checks['all_terminal_graphs_identical']=len({w['final_digest'] for w in workers})==1
 checks['seed_and_rule_inventory_repeats']=len({tuple(w['loaded_seed_ids']) for w in workers})==1 and len({tuple(w['active_lifecycle_rules']) for w in workers})==1
 summary={}
 for k in TIMERS:
  vals=[int(w['timings_ns'][k]) for w in workers]
  summary[k]={'median_ns':statistics.median(vals),'min_ns':min(vals),'max_ns':max(vals),'per_worker_ns':vals}
 rss=[int(w['peak_rss_kib']) for w in workers]
 payload={'schema_version':1,'raw_sha256':sha(RAW),'analysis_sha256':sha(Path(__file__).resolve()),
  'checks':checks,'all_checks_pass':all(checks.values()),'checks_passed':sum(checks.values()),'checks_total':len(checks),
  'worker_count':len(workers),'timing_summary':summary,'peak_rss_kib':{'median':statistics.median(rss),'min':min(rss),'max':max(rss)},
  'terminal_graph_digest':workers[0]['final_digest'] if workers else None,'rows':rows,
  'claim_boundary':'One current-source explicit-identity task on ordinary seed loading and run_rules with scale counters never enabled. Process startup is excluded; task fixture supplies for_goal links. No natural-task prevalence, production-ingestion, or broad performance claim.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':payload['all_checks_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'timing_summary_us':{k:round(v['median_ns']/1000,2) for k,v in summary.items()},'peak_rss_kib':payload['peak_rss_kib']},indent=2))
 if not payload['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
