#!/usr/bin/env python3
"""Independent correctness and stage-cost analysis for default-boot task."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/default_boot_anaphora_task_cost_v1_raw_20260929.json'
OUT=ROOT/'evaluation/reports/default_boot_anaphora_task_cost_v1_analysis_20260929.json'
LOCK=ROOT/'evaluation/substrate_capability/default_boot_anaphora_task_cost_v1_lock_20260929.json'
TIMERS=('python_module_import_wall','python_module_import_cpu','default_adapter_init_wall','default_adapter_init_cpu',
 'first_receive_wall','first_receive_cpu','first_comprehend_wall','first_comprehend_cpu',
 'second_receive_wall','second_receive_cpu','second_comprehend_wall','second_comprehend_cpu',
 'two_turn_task_wall','two_turn_task_cpu','post_task_settle_wall','post_task_settle_cpu','terminal_probe_wall','terminal_probe_cpu')
MATCH_EDGES={'has_mention','responds_to','has_intent','about_concept'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs']
 checks={'ten_workers':len(runs)==10 and all('worker_error' not in x for x in runs)}
 ws=[x['worker'] for x in runs if 'worker' in x]
 checks['complete_replicate_grid']=len(ws)==10 and {w['replicate'] for w in ws}==set(range(10))
 checks['unique_fresh_processes']=len(ws)==10 and len({w['pid'] for w in ws})==10
 checks['source_native_lock_stable']=raw['locked_inputs']==locked==raw['post_run_inputs'] and all(x.get('before')==locked==x.get('after') for x in runs if 'worker' in x)
 rows=[]
 for w in ws:
  r=w['replicate'];key=f'r{r}';proj=w['task_projection'];order=tuple(str(e[1]) for e in proj['target_rule_match_order'])
  checks[key+'_anaphora_oracle']=w['task_oracle_pass'] and proj['it_mention_count']==1 and proj['it_refers_to_names']==['question'] and proj['intent_exists'] and 'question' in proj['intent_about_concept_names']
  checks[key+'_target_rule_readback']=proj['target_rule_count']==1 and len(order)==4 and set(order)==MATCH_EDGES
  checks[key+'_two_turn_inventory']=len(w['turns'])==2 and all(x['message_id']>=0 for x in w['turns']) and 'intent' in w['after_second_receive_seed_ids']
  checks[key+'_default_seed_configuration']=len(w['default_core_seed_ids'])==17
  checks[key+'_terminal_fixed_point']=w['terminal_probe']['progress_steps']==0 and w['terminal_probe']['graph_unchanged']
  checks[key+'_counter_free']=all(int(v)==0 for v in w['scale_audit_counters'].values())
  checks[key+'_timer_values_nonnegative']=all(int(w['timings_ns'][k])>=0 for k in TIMERS)
  checks[key+'_graph_size_positive']=w['graph_size']['nodes']>0 and w['graph_size']['edges']>0
  rows.append({'replicate':r,'pid':w['pid'],'default_core_seed_ids':w['default_core_seed_ids'],'initial_seed_ids':w['initial_seed_ids'],
   'after_first_receive_seed_ids':w['after_first_receive_seed_ids'],'after_second_receive_seed_ids':w['after_second_receive_seed_ids'],
   'task_projection':proj,'task_oracle_pass':w['task_oracle_pass'],'task_graph_digest':w['task_graph_digest'],
   'post_task_settle_progress':w['post_task_settle']['progress_steps'],'terminal_digest':w['terminal_probe']['graph_digest'],
   'timings_ns':w['timings_ns'],'graph_size':w['graph_size'],'peak_rss_kib':w['peak_rss_kib']})
 checks['task_projection_repeats']=len({json.dumps(w['task_projection'],sort_keys=True) for w in ws})==1
 checks['task_graphs_repeat']=len({w['task_graph_digest'] for w in ws})==1
 checks['terminal_graphs_repeat']=len({w['terminal_probe']['graph_digest'] for w in ws})==1
 checks['seed_inventory_repeat']=len({tuple(w['initial_seed_ids']) for w in ws})==1 and len({tuple(w['after_second_receive_seed_ids']) for w in ws})==1
 summary={}
 for k in TIMERS:
  vals=[int(w['timings_ns'][k]) for w in ws]
  summary[k]={'median_ns':statistics.median(vals),'min_ns':min(vals),'max_ns':max(vals),'per_worker_ns':vals}
 rss=[int(w['peak_rss_kib']) for w in ws]
 payload={'schema_version':1,'raw_sha256':sha(RAW),'analysis_sha256':sha(Path(__file__).resolve()),
  'checks':checks,'all_checks_pass':all(checks.values()),'checks_passed':sum(checks.values()),'checks_total':len(checks),
  'worker_count':len(ws),'timing_summary':summary,'peak_rss_kib':{'median':statistics.median(rss),'min':min(rss),'max':max(rss)},
  'terminal_graph_digest':ws[0]['terminal_probe']['graph_digest'] if ws else None,'rows':rows,
  'claim_boundary':'One frozen current-source two-turn anaphora task through default WorldAdapter boot, receive_utterance and comprehend. Process launch and pre-task fingerprint are excluded; scale counters are disabled. No natural-task prevalence or broad runtime claim.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':payload['all_checks_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],
  'timing_summary_us':{k:round(v['median_ns']/1000,2) for k,v in summary.items()},'peak_rss_kib':payload['peak_rss_kib']},indent=2))
 if not payload['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
