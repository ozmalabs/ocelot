#!/usr/bin/env python3
"""Gated validation for explicit Rayon worker RuleIdx attribution."""
from __future__ import annotations
import hashlib,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_parallel_rule_audit_context_v1_1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_parallel_rule_audit_context_v1_1_analysis_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/parallel_rule_audit_context_v1_1_lock_20260927.json'
BASE=ROOT/'evaluation/reports/substrate_live_task_request_cost_capture_v1_workers_raw_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs'];base=json.loads(BASE.read_text())['runs'];checks={}
 base_graphs={r['whole_graph_semantic_sha256'] for r in base}
 checks['three_fresh_processes']=len(runs)==3 and len({r['pid'] for r in runs})==3
 checks['source_native_identity_stable']=raw['locked_inputs']==lock==raw['post_run_inputs'] and all(r['worker_started_inputs']==lock==r['worker_finished_inputs'] for r in runs)
 checks['task_schedule_and_lifecycle']=all(r['threads_joined'] and not r['errors'] and r['b_was_serialized'] and not r['b_completed_while_a_blocked'] and r['event_order_gate'] and r['identity_gate'] and r['lifecycle_gate'] and r['pause_gate'] for r in runs)
 checks['final_graph_reproduces_across_v1_1_workers']=len({r['whole_graph_semantic_sha256'] for r in runs})==1
 checks['reply_pair_reproduces']=len({json.dumps(r['replies'],sort_keys=True) for r in runs})==1
 checks['reply_parity_with_v1']=all(r['replies']==base[0]['replies'] for r in runs)
 totals=defaultdict(list); arities=defaultdict(Counter); rule_sums=defaultdict(Counter); costs=defaultdict(list); clause_anomalies=[]
 for r in runs:
  checks[f"rep{r['replicate']}_six_event_pattern_snapshots"]=len(r['event_rule_patterns'])==6 and all(x['patterns'] for x in r['event_rule_patterns'])
  checks[f"rep{r['replicate']}_counter_reset_clean"]=set(r.get('request_counter_after_reset',{}))=={'request-A','request-B'} and all(int(x['global'].get('cand_tested',0))==0 and not x['per_rule'] and not x['per_clause'] for x in r['request_counter_after_reset'].values())
  for req,c in r['request_cost'].items():
   g=c['global'];patterns=c['rule_patterns_end']; per=c['per_rule'];clause=c['per_clause'];global_n=int(g.get('cand_tested',0));by_rule=Counter();missing=[];badpos=[]
   for idx,metric,value in per:
    idx=int(idx);value=int(value);info=patterns.get(str(idx))
    if info is None:missing.append(idx)
    elif metric=='candidate_tests':
     by_rule[idx]+=value;arities[req][int(info['match_arity'])]+=value;rule_sums[req][str(info['rule_name'])]+=value
   for idx,pos,value in clause:
    idx=int(idx);pos=int(pos);value=int(value);info=patterns.get(str(idx))
    if info is None:missing.append(idx)
    elif pos>=int(info['match_arity']):badpos.append({'rule_index':idx,'rule_name':info['rule_name'],'match_arity':info['match_arity'],'clause_position':pos,'candidate_tests':value})
   clause_n=sum(int(v) for _,_,v in clause);rule_n=sum(by_rule.values())
   checks[f"rep{r['replicate']}_{req}_rule_ids_mapped"]=not missing
   checks[f"rep{r['replicate']}_{req}_clause_positions_within_arity"]=not badpos
   checks[f"rep{r['replicate']}_{req}_per_rule_conservation"]=rule_n==global_n
   checks[f"rep{r['replicate']}_{req}_per_clause_conservation"]=clause_n==global_n
   checks[f"rep{r['replicate']}_{req}_matches_v1_global_total"]=global_n==next(int(x['request_cost'][req]['global'].get('cand_tested',0)) for x in base)
   clause_anomalies.extend([{'replicate':r['replicate'],'request':req,**x} for x in badpos])
   totals[req].append(global_n)
   costs[req].append({'replicate':r['replicate'],'global_candidate_tests':global_n,'per_rule_candidate_tests':rule_n,'per_clause_candidate_tests':clause_n,'arity_candidate_tests':dict(sorted(Counter({int(patterns[str(i)]['match_arity']):0 for i,m,v in per if m=='candidate_tests' and str(i) in patterns}).items())),'per_rule':per,'per_clause':clause,'patterns':patterns,'global':g,'bad_clause_positions':badpos})
 summary={req:{'per_worker_candidate_tests':vals,'median':statistics.median(vals),'min':min(vals),'max':max(vals)} for req,vals in totals.items()}
 grand=sum(sum(v) for v in totals.values());arity_totals=Counter()
 for req,rows in ((req,[r['request_cost'][req] for r in runs]) for req in totals):
  for r in rows:
   patt=r['rule_patterns_end']
   for idx,metric,val in r['per_rule']:
    if metric=='candidate_tests':arity_totals[int(patt[str(int(idx))]['match_arity'])]+=int(val)
 arity_summary={str(k):{'candidate_tests':v,'share':v/grand if grand else 0.0} for k,v in sorted(arity_totals.items())}
 top_rules={req:[{'rule_name':name,'candidate_tests':value} for name,value in rule_sums[req].most_common(12)] for req in rule_sums}
 payload={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analysis_sha256':sha(Path(__file__).resolve()),'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_gates_pass':all(checks.values()),'capture_integrity_pass':all(v for k,v in checks.items() if 'clause_positions_within_arity' not in k),'rule_attribution_gate_pass':all(v for k,v in checks.items() if 'clause_positions_within_arity' in k),'clause_position_anomalies':clause_anomalies,'task_semantic_reply_gate_pass':all(r['reply_parity'] for r in runs),'reply_pairs':[r['replies'] for r in runs],'baseline_comparison_comparable':False,'baseline_noncomparability_reason':'world_adapter source hash changed between v1 and v1.1 locks; the v1.1 graph is checked for within-capture reproduction instead.','request_candidate_summary':summary,'candidate_work_by_match_arity_diagnostic_untrusted':arity_summary,'top_rules_by_request_diagnostic_untrusted':top_rules,'candidate_work_total':grand,'request_cost_rows':dict(costs),'claim_boundary':'Three fresh-process repeats of one authored serialized describe_scene fixture. Exact native candidate work covers the outer conversation-lock intervals and excludes boot, pre-acquisition/post-release Python work, and lock wait. Passing clause-arity gates validates per-rule attribution on the observed serial and Rayon paths only for this fixture. Request A legacy reply gate remains separately evaluated.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_gates_pass':payload['all_gates_pass'],'capture_integrity_pass':payload['capture_integrity_pass'],'rule_attribution_gate_pass':payload['rule_attribution_gate_pass'],'task_semantic_reply_gate_pass':payload['task_semantic_reply_gate_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'request_candidate_summary':summary,'candidate_work_by_match_arity_diagnostic_untrusted':arity_summary,'top_rules_by_request_diagnostic_untrusted':top_rules},indent=2))
 if not payload['all_gates_pass']:raise SystemExit(1)
if __name__=='__main__':main()
