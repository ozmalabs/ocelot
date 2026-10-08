#!/usr/bin/env python3
"""Independent integrity, parity, and scaling analysis for rule closure v1."""
from __future__ import annotations
import hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_rule_closure_scale_v1_20260928.json'
LOCK=ROOT/'evaluation/substrate_capability/rule_closure_scale_v1_lock_20260928.json'
OUT=ROOT/'evaluation/reports/substrate_rule_closure_scale_v1_analysis_20260928.json'
SIZES=(10_000,100_000,1_000_000,10_000_000);AUDITS=(False,True);REPS=(0,1)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def median(rows,key):return int(statistics.median(r[key] for r in rows))
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw.get('runs',[])
 groups={(n,rep):{r['audit']:r for r in runs if r.get('n')==n and r.get('replicate')==rep} for n in SIZES for rep in REPS}
 paired=all(set(g)==set(AUDITS) for g in groups.values())
 comparable=('nodes','edges','report','pending_count','done_count','sampled_nodes')
 parity=paired and all(all(g[False].get(k)==g[True].get(k) for k in comparable) for g in groups.values())
 current_files=lock.get('files',{});current_match=all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in current_files.items())
 audited=[r for r in runs if r.get('audit')]
 def metric(r,name):
  return sum(int(v) for idx,key,v in r.get('per_rule',[]) if int(idx)==0 and key==name)
 attribution=all(
  metric(r,'candidate_tests')==r.get('counters',{}).get('cand_tested')==2*r['n']
  and metric(r,'effect_attr_set_attempts')==r.get('counters',{}).get('rule_effect_attr_set_attempts')==r['n']
  and sum(int(row[2]) for row in r.get('clause_counters',[]) if int(row[0])==0)==metric(r,'candidate_tests')
  and r.get('counters',{}).get('cand_tested_unattributed')==0
  for r in audited)
 checks={
  'runner_all_checks_pass':bool(raw.get('all_checks_pass')) and all(raw.get('checks',{}).values()),
  'sixteen_worker_rows':len(runs)==16,
  'two_replicates_for_every_size_and_audit_mode':all(len(g)==2 for g in groups.values()) and paired,
  'unique_process_ids':len({r.get('pid') for r in runs})==16,
  'stable_source_lock_all_workers':all(r.get('before')==lock==r.get('after') for r in runs) and raw.get('locked_inputs')==lock==raw.get('post_run_inputs'),
  'locked_sources_match_checkout':current_match,
  'exact_terminal_counts_and_fixed_point':all(r.get('report',{}).get('status')=='fixed_point' and r.get('report',{}).get('budget_overshoot')==0 and r.get('nodes')==r.get('n') and r.get('edges')==r.get('n') and r.get('pending_count')==0 and r.get('done_count')==r.get('n') for r in runs),
  'audit_on_off_semantic_parity':parity,
  'audited_work_counter_conservation_and_predicted_linear_counts':len(audited)==8 and attribution,
  'instrumented_and_plain_counters_separated':all((bool(r.get('per_rule')) and bool(r.get('counters'))) if r.get('audit') else (not r.get('per_rule') and not r.get('counters')) for r in runs),
  'positive_closure_and_setup_timers':all(all(r.get(k,0)>0 for k in ('node_build_wall_ns','edge_build_wall_ns','index_declaration_wall_ns','rule_install_wall_ns','closure_wall_ns','validation_wall_ns')) for r in runs),
 }
 summaries=[]
 for n in SIZES:
  plain=[r for r in runs if r.get('n')==n and not r.get('audit')];audited=[r for r in runs if r.get('n')==n and r.get('audit')]
  if not plain or not audited:continue
  row={'nodes':n,'edges':n,'replicates_per_audit_mode':len(plain),'plain_median_closure_wall_ns':median(plain,'closure_wall_ns'),'plain_median_closure_cpu_ns':median(plain,'closure_cpu_ns'),'audit_median_closure_wall_ns':median(audited,'closure_wall_ns'),'audit_median_closure_cpu_ns':median(audited,'closure_cpu_ns'),'plain_median_rss_increase_bytes':int(statistics.median(r['rss_after_closure_bytes']-r['rss_before_bytes'] for r in plain)),'audit_median_rss_increase_bytes':int(statistics.median(r['rss_after_closure_bytes']-r['rss_before_bytes'] for r in audited)),'plain_peak_rss_bytes':[r['peak_rss_bytes'] for r in plain],'audit_peak_rss_bytes':[r['peak_rss_bytes'] for r in audited]}
  for r in audited:
   row.setdefault('audit_candidate_tests',[]).append(r.get('counters',{}).get('cand_tested'))
   row.setdefault('audit_attr_set_attempts',[]).append(r.get('counters',{}).get('rule_effect_attr_set_attempts'))
  summaries.append(row)
 analysis={'schema_version':1,'analysis_id':'substrate-rule-closure-scale-v1-independent-analysis','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'all_checks_pass':all(checks.values()),'size_summaries':summaries,'interpretation':'One attributed ring and one status-transition rule. Audit-on counters describe native operation work; audit-on timing includes instrumentation, so audit-off timing is primary. The declared status index is included in memory and is used by the terminal-state oracle. This panel is not a general closure theorem or representative task workload.'}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_checks_pass':analysis['all_checks_pass'],'size_summaries':summaries},indent=2))
 if not analysis['all_checks_pass']:raise SystemExit('independent closure scale analysis failed')
if __name__=='__main__':main()
