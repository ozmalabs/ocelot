#!/usr/bin/env python3
"""Independent analysis of rematch and effect-trace counterfactual diagnosis."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_effect_trace_counterfactual_v1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_trace_counterfactual_v1_lock_20261005.json';RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_trace_counterfactual_v1.py';LOCKED_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_effect_trace_counterfactual_v1.py'
ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantics(row):
 r=json.loads(json.dumps(row))
 def strip(x):
  if isinstance(x,dict):
   return {k:strip(v) for k,v in x.items() if not k.endswith('_ns')}
  if isinstance(x,list):return [strip(v) for v in x]
  return x
 return strip(r)
def summary(rows):
 out={}
 for n in (4,8,16,32):
  group=[r for r in rows if r['size']==n]
  med=lambda key:statistics.median(r[key] for r in group)
  out[str(n)]={'cases':len(group),'mean_endpoint_counterfactual_branches':statistics.mean(r['endpoint']['candidate_attempts'] for r in group),'full_rematch_branches':statistics.mean(r['full_rematch']['attempts'] for r in group),'effect_trace_branches':statistics.mean(r['effect_trace']['attempts'] for r in group),'endpoint_total_median_ms':med('endpoint_total_wall_ns')/1e6,'full_rematch_total_median_ms':statistics.median(r['full_rematch']['total_wall_ns'] for r in group)/1e6,'effect_trace_total_median_ms':statistics.median(r['effect_trace']['total_wall_ns'] for r in group)/1e6,'full_rematch_vs_trace_median_ratio':statistics.median(r['full_rematch']['total_wall_ns'] for r in group)/max(statistics.median(r['effect_trace']['total_wall_ns'] for r in group),1),'endpoint_total_median_cpu_ms':statistics.median(r['endpoint_total_cpu_ns'] for r in group)/1e6,'full_rematch_total_median_cpu_ms':statistics.median(r['full_rematch']['total_cpu_ns'] for r in group)/1e6,'effect_trace_total_median_cpu_ms':statistics.median(r['effect_trace']['total_cpu_ns'] for r in group)/1e6,'full_rematch_vs_trace_median_cpu_ratio':statistics.median(r['full_rematch']['total_cpu_ns'] for r in group)/max(statistics.median(r['effect_trace']['total_cpu_ns'] for r in group),1)}
 return out
def main():
 d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=d['workers'];rows=workers[0]['rows']
 checks={'schema':d['schema']=='ThoughtexperimentEffectTraceCounterfactualV1','lock_hash':d['lock_sha256']==sha(LOCK),'worker_count_and_lock':len(workers)==3 and len({w['pid'] for w in workers})==3 and all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'runner_analyzer_hashes':lock['sources']['files'][str(RUNNER.relative_to(ROOT))]==sha(RUNNER) and lock['sources']['files'][str(LOCKED_ANALYZER.relative_to(ROOT))]==sha(LOCKED_ANALYZER)}
 checks['exact_case_matrix']=len(rows)==80 and {(r['size'],r['case_id']) for r in rows}=={(n,i) for n in lock['sizes'] for i in range(lock['cases_per_size'])}
 checks['workers_replicate_semantics']=all([semantics(r) for r in w['rows']]==[semantics(r) for r in rows] for w in workers[1:])
 exact=True;branch_counts=True;statuses=True;primary=True;event_only=True;trace_full=True;matches=True
 for r in rows:
  oracle=r['oracle'];bad=int(oracle['bad_effect_index']);n=int(r['size']);ep=r['endpoint'];rm=r['full_rematch'];tr=r['effect_trace']
  exact &= rm['candidates']==[bad] and rm['found']==bad and tr['candidates']==[bad] and tr['found']==bad and ep['found']==bad
  branch_counts &= ep['candidate_attempts']==bad+1 and rm['attempts']==1 and tr['attempts']==1
  statuses &= ep['progress_steps']==1 and tr['progress_steps']==1 and ep['status']==tr['status']
  primary &= r['primary_unchanged'] and r['primary_digest']==r['primary_after_digest'] and r['primary_revision_before']==r['primary_revision_after']
  event_only &= ep['candidate_count']==n and ep['event_count']==1 and ep['event_effect_snapshots']==0
  trace_full &= tr['event_count']==1 and tr['snapshots_truncated']==0
  matches &= len(oracle['effect_variables'])==n and len(set(oracle['effect_variables']))==n and oracle['variable_node_ids'][oracle['bad_variable']]==oracle['bad_node_id'] and oracle['effect_variables'][bad]==oracle['bad_variable']
 checks['rematch_and_trace_exact_effect']=bool(exact);checks['counterfactual_branch_outcomes_and_counts']=bool(branch_counts);checks['closure_status_and_one_firing']=bool(statuses);checks['primary_graph_rule_revision_isolated']=bool(primary);checks['event_observer_has_no_effect_values']=bool(event_only);checks['effect_trace_complete']=bool(trace_full);checks['oracle_bindings_internally_consistent']=bool(matches)
 summaries=summary(rows)
 all_rows=[r for w in workers for r in w['rows']]
 overall={'cases_per_worker':len(rows),'workers':len(workers),'mean_event_only_counterfactual_branches':statistics.mean(r['endpoint']['candidate_attempts'] for r in rows),'mean_full_rematch_counterfactual_branches':statistics.mean(r['full_rematch']['attempts'] for r in rows),'mean_effect_trace_counterfactual_branches':statistics.mean(r['effect_trace']['attempts'] for r in rows),'endpoint_total_median_ms':statistics.median(r['endpoint_total_wall_ns'] for r in rows)/1e6,'full_rematch_total_median_ms':statistics.median(r['full_rematch']['total_wall_ns'] for r in rows)/1e6,'effect_trace_total_median_ms':statistics.median(r['effect_trace']['total_wall_ns'] for r in rows)/1e6,'full_rematch_to_effect_trace_median_ratio':statistics.median(r['full_rematch']['total_wall_ns'] for r in rows)/max(statistics.median(r['effect_trace']['total_wall_ns'] for r in rows),1),'endpoint_total_median_cpu_ms':statistics.median(r['endpoint_total_cpu_ns'] for r in rows)/1e6,'full_rematch_total_median_cpu_ms':statistics.median(r['full_rematch']['total_cpu_ns'] for r in rows)/1e6,'effect_trace_total_median_cpu_ms':statistics.median(r['effect_trace']['total_cpu_ns'] for r in rows)/1e6,'full_rematch_to_effect_trace_median_cpu_ratio':statistics.median(r['full_rematch']['total_cpu_ns'] for r in rows)/max(statistics.median(r['effect_trace']['total_cpu_ns'] for r in rows),1),'primary_isolation_passes':sum(r['primary_unchanged'] for r in rows)}
 out={'schema':'ThoughtexperimentEffectTraceCounterfactualV1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'overall':overall,'by_size':summaries,'claim_limit':'This controlled synthetic rule family compares report-only search, complete rule rematching, effect trace, and actual shared-page omission branches. It does not establish natural-task diagnosis or repair utility; total times exclude common case/snapshot setup and use an opt-level 3 non-LTO build.'}
 dest=ROOT/'evaluation/reports/thoughtexperiment_effect_trace_counterfactual_v1_analysis_correction_20261005.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'overall':overall,'by_size':summaries},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
