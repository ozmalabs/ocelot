#!/usr/bin/env python3
"""Validate live self-report boundary projections and native matcher cost."""
from __future__ import annotations
import hashlib,json,statistics,importlib.util
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_self_report_task_boundary_v2_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/live_self_report_task_boundary_v2_lock_20260927.json'
RUNNER=ROOT/'scripts/substrate_live_self_report_task_boundary_v2.py'
OUT=ROOT/'evaluation/reports/substrate_live_self_report_task_boundary_v2_analysis_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 spec=importlib.util.spec_from_file_location('boundary_runner',RUNNER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=raw.get('runs',[]);checks={};intervals=[]
 checks['lock_matches_current_sources']=locked==mod.lock_inputs()==raw.get('locked_inputs')
 checks['workers_and_postrun_source_stable']=raw.get('post_run_inputs')==locked and all(r.get('worker_started_inputs')==locked==r.get('worker_finished_inputs') for r in runs)
 checks['three_distinct_fresh_processes']=len(runs)==3 and len({r.get('pid') for r in runs})==3
 checks['lifecycle_and_route_shortfall_gates']=all(r['turns'][0]['route']=='self_report' and r['turns'][0]['goal_count']==1 and r['turns'][0]['goal']['status']=='resolved' and r['turns'][0]['goal']['transition_kinds']==['selection','execution','action_result'] and r['turns'][1]['route'] is None and r['turns'][1]['goal_count']==0 for r in runs)
 checks['all_five_identity_controls_pass']=all(raw.get('control_checks',{}).values())
 checks['semantic_graph_reproduces']=len({r['whole_graph_semantic_sha256'] for r in runs})==1
 checks['task_boundaries_reproduce']=len({json.dumps(r['task_boundaries'],sort_keys=True) for r in runs})==1
 checks['independent_full_edge_recomputation_passes']=all(r['boundary_integrity'].get('valid') and r['boundary_integrity'].get('pair_valid') and all(x.get('valid') and x.get('exact_edge_lists_match') and x.get('owned_and_external_nodes_resolve') for x in r['boundary_integrity']['by_task'].values()) for r in runs)
 boundaries=[]
 for r in runs:
  for key in ('turn_0','turn_1'):
   b=r['task_boundaries'][key];owned=set(b['owned_node_ids']);internal=[tuple(x) for x in b['internal_edges']];cut=[tuple(x) for x in b['boundary_edges']]
   valid=(len(owned)==b['owned_node_count'] and len(internal)==b['internal_edge_count'] and len(cut)==b['boundary_incidence_count'] and all(s in owned and t in owned for s,_,t in internal) and all((s in owned)!=(t in owned) for s,_,t in cut) and len(set(internal))==len(internal) and len(set(cut))==len(cut) and b['owned_induced_treewidth_upper_bound']['value']<=max(0,len(owned)-1))
   checks[f"rep{r['replicate']}_{key}_projection_counts_and_width_valid"]=valid
   boundaries.append({'replicate':r['replicate'],'task':key,'owned_node_count':b['owned_node_count'],'internal_edge_count':b['internal_edge_count'],'boundary_incidence_count':b['boundary_incidence_count'],'boundary_unique_external_node_count':b['boundary_unique_external_node_count'],'owned_width_upper_bound':b['owned_induced_treewidth_upper_bound']['value'],'boundary_edge_type_counts':b['boundary_edge_type_counts'],'boundary_external_node_type_counts':b['boundary_external_node_type_counts'],'owned_node_ids':b['owned_node_ids'],'boundary_edges':b['boundary_edges']})
  for row in r['turns'][0]['producer_work']:
   c=row['counters'];g=c['scale'];global_n=int(g.get('cand_tested',0));unattr=int(g.get('cand_tested_unattributed',0));meta={int(i):{'name':str(n),'arity':int(a),'ambiguous':bool(x)} for i,s,n,a,x in c['metadata']}
   pr=Counter();pc=Counter();bad=[];missing=[];ambig=[]
   for i,m,v in c['per_rule']:
    i=int(i);v=int(v)
    if i not in meta:missing.append(i)
    if m=='candidate_tests':pr[i]+=v
   for i,pos,v in c['per_clause']:
    i=int(i);pos=int(pos);v=int(v);info=meta.get(i)
    if info is None:missing.append(i)
    elif info['ambiguous']:ambig.append(i)
    elif pos>=info['arity']:bad.append((i,pos,info['arity']))
    else:pc[i]+=v
   attributed=global_n-unattr;pn=sum(pr.values());cn=sum(pc.values());prefix=f"rep{r['replicate']}_{row['kind']}"
   checks[prefix+'_metadata_complete']=not missing
   checks[prefix+'_valid_arity_and_unambiguous']=not bad and not ambig and all(not x['ambiguous'] or pr.get(i,0)==0 for i,x in meta.items())
   checks[prefix+'_counter_conservation']=0<=unattr<=global_n and pn==cn==attributed
   term=int(g.get('term_evals_total',0));term_pr=sum(int(v) for _,m,v in c['per_rule'] if m=='term_evaluations')
   checks[prefix+'_term_count_conservation']=term==term_pr==sum(int(v) for k,v in g.items() if k.startswith('term_eval:'))
   intervals.append({'replicate':r['replicate'],'kind':row['kind'],'candidate_tests':global_n,'attributed':attributed,'unattributed':unattr,'term_evaluations':term})
 checks['three_producer_events_per_run']=all(len(r['turns'][0]['producer_work'])==3 and [x['kind'] for x in r['turns'][0]['producer_work']]==['selection','execution','action_result'] for r in runs)
 by_task={}
 for key in ('turn_0','turn_1'):
  xs=[x for x in boundaries if x['task']==key]
  sample=xs[0]
  by_task[key]={k:sample[k] for k in ('owned_node_count','internal_edge_count','boundary_incidence_count','boundary_unique_external_node_count','owned_width_upper_bound','boundary_edge_type_counts','boundary_external_node_type_counts')}
 work={kind:{'candidate_tests_per_worker':[x['candidate_tests'] for x in intervals if x['kind']==kind],'attributed_per_worker':[x['attributed'] for x in intervals if x['kind']==kind],'unattributed_per_worker':[x['unattributed'] for x in intervals if x['kind']==kind],'term_evaluations_per_worker':[x['term_evaluations'] for x in intervals if x['kind']==kind]} for kind in ('selection','execution','action_result')}
 payload={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analysis_sha256':sha(Path(__file__).resolve()),'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_gates_pass':all(checks.values()),'boundary_integrity_pass':checks['independent_full_edge_recomputation_passes'] and checks['task_boundaries_reproduce'],'matcher_attribution_pass':all(v for k,v in checks.items() if any(t in k for t in ('metadata_complete','valid_arity','counter_conservation','term_count_conservation'))),'whole_graph_sizes':{'nodes':runs[0]['task_boundaries']['whole_graph_node_count'],'edges':runs[0]['task_boundaries']['whole_graph_edge_count']},'task_boundary_summary':by_task,'task_boundary_rows':boundaries,'paired_boundary':runs[0]['task_boundaries']['pair'],'matcher_work_by_event':work,'event_intervals':intervals,'claim_boundary':'Three source-locked workers measure two protocol-declared self-report task projections in one full runtime graph. Complete typed-edge cuts and min-fill upper bounds are for the owned induced graphs only. They are operational views, not learned frames or the full matcher dependency treewidth, and do not prove factorization or natural-task prevalence.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps({'all_gates_pass':payload['all_gates_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'boundary_integrity_pass':payload['boundary_integrity_pass'],'matcher_attribution_pass':payload['matcher_attribution_pass'],'whole_graph_sizes':payload['whole_graph_sizes'],'task_boundary_summary':by_task,'matcher_work_by_event':work},indent=2))
 if not payload['all_gates_pass']:raise SystemExit(1)
if __name__=='__main__':main()
