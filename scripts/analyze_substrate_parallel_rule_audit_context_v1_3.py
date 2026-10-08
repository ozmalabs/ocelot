#!/usr/bin/env python3
"""Validate native matcher identity attribution and conserved live-task work."""
from __future__ import annotations
import hashlib,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_parallel_rule_audit_context_v1_3_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_parallel_rule_audit_context_v1_3_analysis_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/parallel_rule_audit_context_v1_3_lock_20260927.json'
BASE=ROOT/'evaluation/reports/substrate_live_task_request_cost_capture_v1_workers_raw_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs'];base=json.loads(BASE.read_text())['runs'];checks={}
 checks['three_fresh_processes']=len(runs)==3 and len({r['pid'] for r in runs})==3
 checks['source_native_identity_stable']=raw['locked_inputs']==lock==raw['post_run_inputs'] and all(r['worker_started_inputs']==lock==r['worker_finished_inputs'] for r in runs)
 checks['task_schedule_and_lifecycle']=all(r['threads_joined'] and not r['errors'] and r['b_was_serialized'] and not r['b_completed_while_a_blocked'] and r['event_order_gate'] and r['identity_gate'] and r['lifecycle_gate'] and r['pause_gate'] for r in runs)
 checks['final_graph_reproduces_across_v1_3_workers']=len({r['whole_graph_semantic_sha256'] for r in runs})==1
 checks['reply_pair_reproduces']=len({json.dumps(r['replies'],sort_keys=True) for r in runs})==1
 checks['reply_parity_with_v1_3_fixture_baseline']=all(r['replies']==base[0]['replies'] for r in runs)
 summaries=defaultdict(list); rows={}; arity_totals=Counter(); name_totals=defaultdict(Counter); anomalies=[]
 for r in runs:
  checks[f"rep{r['replicate']}_six_event_pattern_snapshots"]=len(r['event_rule_patterns'])==6 and all(x['patterns'] for x in r['event_rule_patterns'])
  checks[f"rep{r['replicate']}_counter_reset_clean"]=set(r.get('request_counter_after_reset',{}))=={'request-A','request-B'} and all(int(x['global'].get('cand_tested',0))==0 and not x['per_rule'] and not x['per_clause'] and not x['metadata'] for x in r['request_counter_after_reset'].values())
  for req,c in r['request_cost'].items():
   g=c['global'];global_n=int(g.get('cand_tested',0));unattributed=int(g.get('cand_tested_unattributed',0));meta={int(i):{'name_symbol':int(sym),'rule_name':str(name),'match_arity':int(arity),'ambiguous':bool(amb)} for i,sym,name,arity,amb in c['metadata']}
   per_rule=Counter(); per_clause=Counter(); bad=[]; missing=set()
   for idx,metric,value in c['per_rule']:
    idx=int(idx);value=int(value)
    if metric=='candidate_tests':per_rule[idx]+=value
    if idx not in meta:missing.add(idx)
   for idx,pos,value in c['per_clause']:
    idx=int(idx);pos=int(pos);value=int(value);info=meta.get(idx)
    if info is None:missing.add(idx)
    elif pos>=info['match_arity']:bad.append({'audit_id':idx,'rule_name':info['rule_name'],'match_arity':info['match_arity'],'clause_position':pos,'candidate_tests':value})
    else:
     per_clause[idx]+=value;arity_totals[info['match_arity']]+=value;name_totals[req][info['rule_name']]+=value
   rule_n=sum(per_rule.values());clause_n=sum(per_clause.values());expected=global_n-unattributed
   checks[f"rep{r['replicate']}_{req}_all_candidate_ids_have_metadata"]=not missing
   checks[f"rep{r['replicate']}_{req}_ambiguous_ids_have_no_attributed_rows"]=all(not info['ambiguous'] or (per_rule.get(i,0)==0 and per_clause.get(i,0)==0) for i,info in meta.items())
   checks[f"rep{r['replicate']}_{req}_clause_positions_within_arity"]=not bad
   checks[f"rep{r['replicate']}_{req}_per_rule_equals_verified_attributed"]=rule_n==expected
   checks[f"rep{r['replicate']}_{req}_per_clause_equals_verified_attributed"]=clause_n==expected
   checks[f"rep{r['replicate']}_{req}_attributed_plus_unattributed_conserves_global"]=0<=unattributed<=global_n and expected+unattributed==global_n
   bad_ids=[i for i in meta if (i&0x80000000)]
   checks[f"rep{r['replicate']}_{req}_graph_rule_ids_are_tagged"]=all((i&0x80000000)!=0 for i in bad_ids)
   checks[f"rep{r['replicate']}_{req}_matches_v1_global_total"]=global_n==next(int(x['request_cost'][req]['global'].get('cand_tested',0)) for x in base)
   anomalies.extend([{'replicate':r['replicate'],'request':req,**x} for x in bad])
   summaries[req].append(global_n)
   rows.setdefault(req,[]).append({'replicate':r['replicate'],'global_candidate_tests':global_n,'verified_attributed_candidate_tests':expected,'unattributed_candidate_tests':unattributed,'per_rule_candidate_tests':rule_n,'per_clause_candidate_tests':clause_n,'metadata_count':len(meta),'rule_metadata':meta,'per_rule':c['per_rule'],'per_clause':c['per_clause'],'global':g})
 result={req:{'per_worker_candidate_tests':v,'median':statistics.median(v),'min':min(v),'max':max(v)} for req,v in summaries.items()}
 payload={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analysis_sha256':sha(Path(__file__).resolve()),'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_gates_pass':all(checks.values()),'capture_integrity_pass':all(v for k,v in checks.items() if 'positions_within_arity' not in k),'rule_attribution_gate_pass':all(v for k,v in checks.items() if any(t in k for t in ('all_candidate_ids','positions_within_arity','ambiguous_ids','per_rule_equals','per_clause_equals','conserves_global','graph_rule_ids'))),'task_semantic_reply_gate_pass':all(r['reply_parity'] for r in runs),'reply_pairs':[r['replies'] for r in runs],'clause_position_anomalies':anomalies,'request_candidate_summary':result,'candidate_work_by_match_arity':{str(k):{'candidate_tests':v,'share':v/max(1,sum(arity_totals.values()))} for k,v in sorted(arity_totals.items())},'top_rules_by_request':{req:[{'rule_name':name,'candidate_tests':count} for name,count in values.most_common(20)] for req,values in name_totals.items()},'request_cost_rows':rows,'candidate_work_total':sum(sum(v) for v in summaries.values()),'claim_boundary':'Three fresh-process repeats of one authored serialized describe_scene fixture. Candidate counts are exact for this lock-scoped interval. Matcher attribution is accepted only when native audit identity, matcher symbol, and match arity validate; all remaining tests are reported as unattributed. This does not establish prevalence, asymptotic complexity, or capability generality.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:payload[k] for k in ('all_gates_pass','capture_integrity_pass','rule_attribution_gate_pass','task_semantic_reply_gate_pass','checks_passed','checks_total','request_candidate_summary','candidate_work_by_match_arity','top_rules_by_request')},indent=2))
 if not payload['all_gates_pass']:raise SystemExit(1)
if __name__=='__main__':main()
