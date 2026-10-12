#!/usr/bin/env python3
"""Independent exact-attribution analysis for live self-report event closures."""
from __future__ import annotations
import hashlib,json,statistics,importlib.util
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_self_report_matcher_cost_v1_9_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/live_self_report_matcher_cost_v1_9_lock_20260927.json'
RUNNER=ROOT/'scripts/substrate_live_self_report_matcher_cost_v1_9.py'
OUT=ROOT/'evaluation/reports/substrate_live_self_report_matcher_cost_v1_9_analysis_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 spec=importlib.util.spec_from_file_location('selfreport_runner',RUNNER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=raw.get('runs',[]);checks={};intervals=[];profiles=[];anomalies=[]
 expected=mod.lock_inputs()
 checks['lock_matches_current_sources']=locked==expected==raw.get('locked_inputs')
 checks['workers_and_postrun_source_stable']=raw.get('post_run_inputs')==locked and all(r.get('worker_started_inputs')==locked==r.get('worker_finished_inputs') for r in runs)
 checks['three_distinct_fresh_processes']=len(runs)==3 and len({r.get('pid') for r in runs})==3
 checks['first_prompt_live_lifecycle_passes']=all(r['turns'][0]['route']=='self_report' and r['turns'][0]['goal_count']==1 and r['turns'][0]['goal_origin_matches'] and r['turns'][0]['goal']['status']=='resolved' and r['turns'][0]['goal']['transition_kinds']==['selection','execution','action_result'] and r['turns'][0]['goal']['transition_links_all_bound'] and r['turns'][0]['goal']['closed'] and len(r['turns'][0]['producer_work'])==3 for r in runs)
 checks['second_prompt_shortfall_reproduces']=all(r['turns'][1]['route'] is None and r['turns'][1]['goal_count']==0 and not r['turns'][1]['lifecycle_events'] and not r['turns'][1]['producer_work'] and r['turns'][1]['reply_nonempty'] for r in runs)
 checks['identity_and_failure_controls_pass']=all(raw.get('control_checks',{}).values()) and all(raw.get('checks',{}).get(k,False) for k in ('all_semantic_controls_pass','source_stable_through_workers_and_controls'))
 checks['event_shape_reproduces']=len({json.dumps([(t['route'],t['goal_count'],[e['kind'] for e in t['lifecycle_events']]) for t in r['turns']],sort_keys=True) for r in runs})==1
 for r in runs:
  run_prof=[]
  for row in r['turns'][0]['producer_work']:
   c=row['counters'];g=c['scale'];global_n=int(g.get('cand_tested',0));unattr=int(g.get('cand_tested_unattributed',0))
   meta={int(i):{'symbol':int(sym),'name':str(name),'arity':int(arity),'ambiguous':bool(amb)} for i,sym,name,arity,amb in c['metadata']}
   per=Counter();clauses=Counter();missing=set();bad=[];ambiguous_hits=[]
   for i,m,v in c['per_rule']:
    i=int(i);v=int(v)
    if i not in meta:missing.add(i)
    if m=='candidate_tests':per[i]+=v
   for i,pos,v in c['per_clause']:
    i=int(i);pos=int(pos);v=int(v);info=meta.get(i)
    if info is None:missing.add(i)
    elif info['ambiguous']:ambiguous_hits.append({'audit_id':i,'clause':pos,'count':v})
    elif pos>=info['arity']:bad.append({'audit_id':i,'name':info['name'],'arity':info['arity'],'clause':pos,'count':v})
    else:clauses[i]+=v
   per_n=sum(per.values());clause_n=sum(clauses.values());attributed=global_n-unattr
   prefix=f"rep{r['replicate']}_{row['kind']}"
   checks[prefix+'_candidate_id_metadata']=not missing
   checks[prefix+'_clause_arity']=not bad
   checks[prefix+'_ambiguous_ids_excluded']=not ambiguous_hits and all(not info['ambiguous'] or per.get(i,0)==0 for i,info in meta.items())
   checks[prefix+'_per_rule_conservation']=per_n==attributed
   checks[prefix+'_per_clause_conservation']=clause_n==attributed
   checks[prefix+'_attributed_plus_unattributed_conservation']=0<=unattr<=global_n and attributed+unattr==global_n
   term_total=int(g.get('term_evals_total',0));term_per=sum(int(v) for _,m,v in c['per_rule'] if m=='term_evaluations')
   checks[prefix+'_term_eval_conservation']=term_total==term_per==sum(int(v) for k,v in g.items() if k.startswith('term_eval:'))
   rows={'replicate':r['replicate'],'kind':row['kind'],'candidate_tests':global_n,'verified_attributed':attributed,'unattributed':unattr,'per_rule_candidate_tests':per_n,'per_clause_candidate_tests':clause_n,'term_evaluations':term_total,'metadata_count':len(meta),'ambiguous_ids':sum(x['ambiguous'] for x in meta.values()),'per_rule':c['per_rule'],'per_clause':c['per_clause'],'metadata':c['metadata'],'elapsed_ns':row['elapsed_ns']}
   intervals.append(rows);run_prof.append((row['kind'],global_n,attributed,unattr,term_total))
  profiles.append(run_prof)
 checks['three_producer_events_per_run']=all(len(p)==3 and [x[0] for x in p]==['selection','execution','action_result'] for p in profiles)
 checks['per_event_work_reproduces']=len({json.dumps(p,sort_keys=True) for p in profiles})==1
 by_kind={}
 for kind in ('selection','execution','action_result'):
  xs=[x for x in intervals if x['kind']==kind]
  by_kind[kind]={'candidate_tests_per_run':[x['candidate_tests'] for x in xs],'attributed_per_run':[x['verified_attributed'] for x in xs],'unattributed_per_run':[x['unattributed'] for x in xs],'term_evaluations_per_run':[x['term_evaluations'] for x in xs],'median_elapsed_ns':statistics.median(x['elapsed_ns'] for x in xs),'ambiguous_ids_per_run':[x['ambiguous_ids'] for x in xs]}
 payload={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analysis_sha256':sha(Path(__file__).resolve()),'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_gates_pass':all(checks.values()),'matcher_attribution_gate_pass':all(v for k,v in checks.items() if any(x in k for x in ('candidate_id_metadata','clause_arity','ambiguous_ids_excluded','conservation'))),'first_prompt_capability_gate_pass':checks['first_prompt_live_lifecycle_passes'],'second_prompt_shortfall_gate_pass':checks['second_prompt_shortfall_reproduces'],'producer_work_by_kind':by_kind,'event_intervals':intervals,'claim_boundary':'Three source-locked fresh processes measuring only the three lifecycle producer closures for one live self-report organization prompt. The second prompt is a separately classified route shortfall. Exact candidate counts and identity attribution do not establish semantic generality, natural-task prevalence, asymptotic scaling, or uninstrumented CPU cost.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_gates_pass':payload['all_gates_pass'],'matcher_attribution_gate_pass':payload['matcher_attribution_gate_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'producer_work_by_kind':by_kind},indent=2))
 if not payload['all_gates_pass']:raise SystemExit(1)
if __name__=='__main__':main()
