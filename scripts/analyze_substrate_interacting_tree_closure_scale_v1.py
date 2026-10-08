#!/usr/bin/env python3
"""Independent parity, attribution, and topology analysis for tree closure v1."""
from __future__ import annotations
import hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_interacting_tree_closure_scale_v1_20260928.json'
LOCK=ROOT/'evaluation/substrate_capability/interacting_tree_closure_scale_v1_lock_20260928.json'
OUT=ROOT/'evaluation/reports/substrate_interacting_tree_closure_scale_v1_analysis_20260928.json'
SIZES=(10_000,100_000,1_000_000);TOPOLOGIES=('balanced','star');AUDITS=(False,True);REPS=(0,1,2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def med(rows,key):return int(statistics.median(r[key] for r in rows))
def pr_metric(r,idx,name):return sum(int(v) for i,k,v in r.get('per_rule',[]) if int(i)==idx and k==name)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw.get('runs',[])
 groups={(n,t,rep):{r['audit']:r for r in runs if (r.get('n'),r.get('topology'),r.get('replicate'))==(n,t,rep)} for n in SIZES for t in TOPOLOGIES for rep in REPS}
 paired=all(set(g)==set(AUDITS) for g in groups.values());comparable=('nodes','edges','report','pending_count','ready_count','active_count','samples')
 parity=paired and all(all(g[False].get(k)==g[True].get(k) for k in comparable) for g in groups.values())
 current_match=all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in lock.get('files',{}).items())
 audit_rows=[r for r in runs if r.get('audit')]
 attribution=all(
  sum(pr_metric(r,i,'candidate_tests') for i in (0,1))==r.get('counters',{}).get('cand_tested')
  and sum(pr_metric(r,i,'effect_attr_set_attempts') for i in (0,1))==r.get('counters',{}).get('rule_effect_attr_set_attempts')==2*(r['n']-1)
  and all(sum(int(x[2]) for x in r.get('clause_counters',[]) if int(x[0])==i)==pr_metric(r,i,'candidate_tests') for i in (0,1))
  and r.get('counters',{}).get('cand_tested_unattributed')==0
  and all(pr_metric(r,i,'effect_attr_set_attempts')==r['n']-1 for i in (0,1))
  for r in audit_rows)
 checks={
  'runner_gates_all_pass':bool(raw.get('all_checks_pass')) and all(raw.get('checks',{}).values()),
  'thirty_six_rows':len(runs)==36,
  'three_replicates_per_factorial_cell':all(sum(r.get('n')==n and r.get('topology')==t and r.get('audit')==a for r in runs)==3 for n in SIZES for t in TOPOLOGIES for a in AUDITS),
  'unique_processes':len({r.get('pid') for r in runs})==36,
  'all_workers_match_source_lock':all(r.get('before')==lock==r.get('after') for r in runs) and raw.get('locked_inputs')==lock==raw.get('post_run_inputs'),
  'locked_sources_match_checkout':current_match,
  'exact_terminal_oracle':all(r.get('nodes')==r.get('n') and r.get('edges')==2*(r.get('n')-1) and r.get('report',{}).get('status')=='fixed_point' and r.get('report',{}).get('budget_overshoot')==0 and r.get('pending_count')==0 and r.get('ready_count')==0 and r.get('active_count')==r.get('n') for r in runs),
  'audit_on_off_semantic_parity':parity,
  'both_rules_fire_expected_effect_count_and_conserve_candidates':len(audit_rows)==18 and attribution,
  'audit_counters_separated':all((bool(r.get('per_rule')) and bool(r.get('counters'))) if r.get('audit') else (not r.get('per_rule') and not r.get('counters')) for r in runs),
  'all_phase_timings_positive':all(all(r.get(k,0)>0 for k in ('node_build_wall_ns','edge_build_wall_ns','index_declaration_wall_ns','rule_install_wall_ns','closure_wall_ns','validation_wall_ns')) for r in runs),
 }
 summaries=[]
 for n in SIZES:
  for top in TOPOLOGIES:
   off=[r for r in runs if r.get('n')==n and r.get('topology')==top and not r.get('audit')]
   on=[r for r in runs if r.get('n')==n and r.get('topology')==top and r.get('audit')]
   if not off or not on:continue
   row={'nodes':n,'edges':2*(n-1),'topology':top,'replicates_per_audit_mode':len(off),'plain_median_closure_cpu_ns':med(off,'closure_cpu_ns'),'plain_median_closure_wall_ns':med(off,'closure_wall_ns'),'audit_median_closure_wall_ns':med(on,'closure_wall_ns'),'audit_median_passes':med(on,'report_passes_completed') if 'report_passes_completed' in on[0] else int(statistics.median(r['report']['passes_completed'] for r in on)),'plain_live_rss_increase_bytes':int(statistics.median(r['rss_after_closure_bytes']-r['rss_before_bytes'] for r in off)),'plain_peak_rss_bytes_range':[min(r['peak_rss_bytes'] for r in off),max(r['peak_rss_bytes'] for r in off)],'audit_candidate_tests':[r['counters']['cand_tested'] for r in on],'audit_effect_attempts':[r['counters']['rule_effect_attr_set_attempts'] for r in on]}
   summaries.append(row)
 analysis={'schema_version':1,'analysis_id':'substrate-interacting-tree-closure-scale-v1-independent-analysis','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'all_checks_pass':all(checks.values()),'topology_size_summaries':summaries,'interpretation':'Two monotone rules on balanced and star trees. Audit-off time is primary. The maintained status index and N-entry terminal readback are included in memory; peak RSS includes validation allocations. This is not a general closure theorem.'}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_checks_pass':analysis['all_checks_pass'],'summaries':summaries},indent=2))
 if not analysis['all_checks_pass']:raise SystemExit('independent tree closure analysis failed')
if __name__=='__main__':main()
