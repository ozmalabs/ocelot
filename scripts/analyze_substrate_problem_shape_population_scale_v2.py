#!/usr/bin/env python3
"""Independent per-rule scale analysis for ProblemShape population v2."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/problem_shape_population_scale_v2_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_population_scale_v2_lock_20260927.json'
OLD=ROOT/'evaluation/reports/substrate_problem_shape_population_scale_20260925.json'
OUT=ROOT/'evaluation/reports/problem_shape_population_scale_v2_analysis_20260927.json'
EXPECTED_SIZES=(16,32,64);MIXES=('recognition','recurrent_residual');MODES=('dynamic','frozen')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rule_work(run):
 out={}
 for rec in run['records']:
  for row in rec['problem_shape_rule_scale_audit']:
   if row.get('metric') not in ('candidate_pairs','term_evaluations'):continue
   k=(row.get('rule_name'),row['metric']);out[k]=out.get(k,0)+int(row['count'])
 return {f'{rule}:{metric}':n for (rule,metric),n in sorted(out.items())}
def analyze():
 d=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=d['runs'];cells={}
 for r in runs:
  n=int(r['population_size']);mix=r['task_mix'];mode=r['codebook_mode'];key=f'N{n}/{mix}/{mode}';records=r['records'];initial=[x['observation_status_initial'] for x in records];final=[x['observation_status_final'] for x in records]
  if mix=='recognition':want_i=want_f=['recognized']*n;want_mints=0
  elif mode=='dynamic':want_i=['residual']+['recognized']*(n-1);want_f=['recognized']*n;want_mints=1
  else:want_i=want_f=['residual']*n;want_mints=0
  per_rule=rule_work(r);tri=n*(n+1)//2;mint_pairs=per_rule.get('ps_mint:candidate_pairs',0);mint_terms=per_rule.get('ps_mint:term_evaluations',0)
  fixed=all(x['post_observe_settle_report']['status']=='fixed_point' for x in records)
  cells[key]={'N':n,'mix':mix,'codebook':mode,'initial_statuses_match':initial==want_i,'final_statuses_match':final==want_f,'mint_count_matches':r['total_mints']==want_mints,'fixed_point_all':fixed,'record_count':len(records),'total_ps_candidate_pairs':r['problem_shape_candidate_pairs_total'],'total_ps_term_evaluations':r['problem_shape_term_evaluations_total'],'ps_mint_candidate_pairs':mint_pairs,'ps_mint_term_evaluations':mint_terms,'triangular_guard_formula_matches':mix!='recognition' or (mint_pairs==(tri if mode=='dynamic' else 0) and mint_terms==(5*tri if mode=='dynamic' else 0)),'per_rule_work':per_rule,'peak_rss_bytes':r['peak_rss_bytes'],'boot_wall_s':r['full_seed_boot_wall_ns']/1e9,'boot_cpu_s':r['full_seed_boot_cpu_ns']/1e9,'cumulative_candidate_work_by_prefix':r['cumulative_candidate_work_by_prefix'],'worker_inputs_match_parent_lock':r.get('worker_inputs')==locked,'v1_worker_gates_pass':r['all_checks_pass'] and r['worker_returncode']==0}
 old=json.loads(OLD.read_text());old_lock=json.loads((ROOT/'evaluation/substrate_capability/problem_shape_population_scale_lock_20260925.json').read_text())
 current_native=locked['runtime_inputs']['runtime_inputs']['native_extension_sha256']
 old_native=old.get('native_sha256');same_native=old_native==current_native
 runpids=[r.get('process_id') for r in runs]
 checks={'twelve_cells':len(cells)==12,'one_per_factorial_cell':set(cells)=={f'N{n}/{m}/{c}' for n in EXPECTED_SIZES for m in MIXES for c in MODES},'unique_worker_pids':len(runpids)==12 and len(set(runpids))==12,'parent_inputs_match_lock':d['locked_inputs']==d['post_run_inputs']==locked,'all_child_input_records_match':all(v['worker_inputs_match_parent_lock'] for v in cells.values()),'all_v1_native_gates_pass':all(v['v1_worker_gates_pass'] for v in cells.values()),'independent_status_mint_and_fixpoint_checks_pass':all(v['initial_statuses_match'] and v['final_statuses_match'] and v['mint_count_matches'] and v['fixed_point_all'] for v in cells.values()),'recognition_ps_mint_triangular_formula_passes':all(v['triangular_guard_formula_matches'] for v in cells.values() if v['mix']=='recognition'),'historical_v1_is_not_native_comparable':not same_native and old_lock.get('native_sha256')==old_native}
 ratios={}
 for mix in MIXES:
  for mode in MODES:
   vals=[cells[f'N{n}/{mix}/{mode}']['total_ps_candidate_pairs'] for n in EXPECTED_SIZES]
   ratios[f'{mix}/{mode}']={'N16_to_N32':vals[1]/vals[0] if vals[0] else None,'N32_to_N64':vals[2]/vals[1] if vals[1] else None,'per_size_counts':vals}
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'integrity_pass':all(checks.values()),'current_native_sha256':current_native,'historical_v1_native_sha256':old_native,'historical_v1_same_native':same_native,'cells':cells,'candidate_pair_scaling_ratios':ratios,'interpretation':'The recognition-only dynamic ps_mint recurrence guard follows N(N+1)/2 candidate pairs and five term evaluations per pair at N=16/32/64; frozen mode removes those attributed checks. Total ProblemShape work includes decode/recognize/residual/redecode and is not just the guard. The older N=2/4/8 capture used a different native build and is not pooled with this current-source extension.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'integrity_pass':out['integrity_pass'],'checks':checks,'recognition_dynamic':{n:{'candidate_pairs':cells[f'N{n}/recognition/dynamic']['total_ps_candidate_pairs'],'ps_mint':cells[f'N{n}/recognition/dynamic']['ps_mint_candidate_pairs']} for n in EXPECTED_SIZES},'total_candidate_pair_ratios':ratios},indent=2))
 if not out['integrity_pass']:raise SystemExit('ProblemShape v2 analysis gate failed')
if __name__=='__main__':analyze()
