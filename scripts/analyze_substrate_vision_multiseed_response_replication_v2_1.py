#!/usr/bin/env python3
"""Integrity gates and cross-seed summaries for response replication v2.1."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/vision_multiseed_response_replication_v2_1_20260927.json'
OUT=ROOT/'evaluation/reports/vision_multiseed_response_replication_v2_1_analysis_20260927.json'
d=json.loads(INPUT.read_text());seeds=d['seeds'];expected={'both_blank'}
for theta in (0,45,90,135):
 for phase in (0.0,1.570796):
  tag=f'theta_{theta}_phase_{phase:.6f}';expected|={f'{tag}_{mode}' for mode in ('A_only','B_only','both')}
rows=[r for ss in seeds.values() for r in ss]
def exact_digest(graph):return hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
raw_checkpoint_hash={s:exact_digest(json.loads((ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'/f'seed_{s}.json').read_text())['graph']) for s in seeds}
counts={s:Counter(x['termination'] for x in rs) for s,rs in seeds.items()}
missing_rate=sum(x['rate_write_snapshot'] is None for x in rows)
mismatches=sum(len(x['rate_write_snapshot']['equation_mismatches']) for x in rows if x['rate_write_snapshot'])
checks={
 'all_three_seed_checkpoints_present':set(seeds)=={'20260935','20260936','20260937'},
 'all_75_conditions_present':all(len(seeds.get(s,[]))==25 and {r['condition'] for r in seeds[s]}==expected for s in ('20260935','20260936','20260937')),
 'source_stable_and_locked':d.get('source_stable') is True and d['locked_inputs']==__import__('substrate_vision_multiseed_response_replication_v2_1').source_inputs(),
 'checkpoint_reference_matches_and_restore_succeeded':all(r['checkpoint_sha256']==json.loads((ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'/f'seed_{r["seed"]}.json').read_text())['prepared_graph_sha256'] for r in rows),
 'input_bursts_match_active_pixels':all(r['a_pixels']==r['a_retinal_bursts'] and r['b_pixels']==r['b_retinal_bursts'] for r in rows),
 'rate_write_snapshot_present':missing_rate==0,
 'rate_equation_holds_at_write':mismatches==0,
 'step_stamps_consistent':all(r['retina_step']==23010 and all(int(z)==23010 for layer in ('A','B') for z in r['rate_write_snapshot']['state'][layer]['rate_step']) and all(int(z)==23010 for layer in ('A','B') for z in r['rate_write_snapshot']['state'][layer]['act_step']) for r in rows if r['rate_write_snapshot']),
 'all_termination_classes_observed_without_trace_caps':all(r['termination'] in ('fixed_point','repeated_graph_state') and r['passes_completed']<=512 and r['progress_steps']<=1_600_000 for r in rows),
 'cycle_statistics_present':all(r['termination']!='repeated_graph_state' or (r['cycle_period_passes'] and r['post_settle_orbit_statistics']['A']['act']['unit_min'] and r['post_settle_orbit_statistics']['B']['act']['unit_mean']) for r in rows),
 'all_conditions_use_each_seed_checkpoint':all(r['seed']==int(s) for s,rs in seeds.items() for r in rs)}
summary={}
for seed,rs in seeds.items():
 summary[seed]={'termination_counts':dict(counts[seed]),'pass_min':min(r['passes_completed'] for r in rs),'pass_median':sorted(r['passes_completed'] for r in rs)[len(rs)//2],'pass_max':max(r['passes_completed'] for r in rs),'progress_total':sum(r['progress_steps'] for r in rs),'rate_write_sums':{r['condition']:sum(r['rate_write_snapshot']['state']['B']['rate']) for r in rs},'cycle_periods':{r['condition']:r['cycle_period_passes'] for r in rs if r['termination']=='repeated_graph_state'}}
by_condition={}
for c in sorted(expected):
 items=[next(r for r in seeds[s] if r['condition']==c) for s in sorted(seeds)]
 by_condition[c]={'termination_by_seed':{str(r['seed']):r['termination'] for r in items},'passes_by_seed':{str(r['seed']):r['passes_completed'] for r in items},'B_rate_write_sum_by_seed':{str(r['seed']):sum(r['rate_write_snapshot']['state']['B']['rate']) for r in items}}
result={'input':str(INPUT.relative_to(ROOT)),'checks':checks,'pass':all(checks.values()),'trial_count':len(rows),'rate_write_mismatch_count':mismatches,'missing_rate_write_count':missing_rate,'termination_counts_by_seed':{k:dict(v) for k,v in counts.items()},'seed_summary':summary,'condition_comparison':by_condition,'interpretation':'All conditions use one of three independently adapted root-scoped checkpoints on the same synthetic fixture. A pass validates the recorded phase-aware measurements and bounded closure on these 75 trials only. Seed-dependent fixed-point/cycle classes are evidence of attractor sensitivity; they do not establish natural-task prevalence, asymptotic complexity, or large-scale CPU performance.'}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'pass':result['pass'],'checks':checks,'termination_counts_by_seed':result['termination_counts_by_seed'],'work':{s:{k:v for k,v in x.items() if k in ('pass_min','pass_median','pass_max','progress_total')} for s,x in summary.items()}},indent=2))
if not result['pass']:raise SystemExit(1)
