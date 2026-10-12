#!/usr/bin/env python3
"""Independent raw-data checks for BP parameter semantics v1.1."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/problem_shape_bp_parameter_semantics_v1_1_20260927.json'
OUT=ROOT/'evaluation/reports/problem_shape_bp_parameter_semantics_v1_1_analysis_20260927.json'
def main():
 p=json.loads(RAW.read_text());runs=p['runs']
 checks={'six_workers':len(runs)==6,'unique_pids':len({r.get('pid') for r in runs})==6,
 'two_replicates_per_resident':all(sum(r['resident_index']==i for r in runs)==2 for i in (0,25,50)),
 'source_locks_stable':p['post_run_inputs']==p['locked_inputs'] and all(r.get('source_stable') and r.get('worker_inputs_before')==p['locked_inputs']==r.get('worker_inputs_after') for r in runs),
 'goals_resolved':all(all(x['status']=='resolved' for x in r['goal_resolution']) for r in runs),
 'same_structural_key_and_finite':all(r['same_signature_key'] and r['finite_beliefs'] for r in runs),
 'no_commit_computational_state_parity':all(r['can_state_unchanged'] for r in runs)}
 contrasts=[{'resident_index':r['resident_index'],'replicate':r['replicate'],'same_key':r['same_signature_key'],'beliefs_equal':r['belief_maps_exactly_equal'],'max_abs_delta':r['max_abs_belief_delta'],'max_product_converged':r['rows'][0]['answer'].get('converged'),'sum_product_converged':r['rows'][1]['answer'].get('converged')} for r in runs]
 result={'schema_version':1,'raw_report':str(RAW.relative_to(ROOT)),'checks':checks,'all_checks_pass':all(checks.values()),'contrasts':contrasts,'summary':{'same_key_all_pairs':all(x['same_key'] for x in contrasts),'beliefs_differing_pairs':sum(not x['beliefs_equal'] for x in contrasts),'max_product_nonconverged':sum(x['max_product_converged'] is False for x in contrasts),'sum_product_nonconverged':sum(x['sum_product_converged'] is False for x in contrasts),'max_abs_delta_values':sorted(set(x['max_abs_delta'] for x in contrasts))},'claim_boundary':'Three locked resident networks, two repeated paired contrasts each; shows parameter-sensitive solver outcomes on this fixture panel, not comparative solver quality or general semantic equivalence.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'checks':checks,'summary':result['summary']},indent=2))
 if not result['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
