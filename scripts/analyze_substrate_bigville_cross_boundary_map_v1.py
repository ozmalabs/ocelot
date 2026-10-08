#!/usr/bin/env python3
"""Independent structural and exactness checks for the boundary MAP replay."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_bigville_cross_boundary_map_v1_20260926.json';LOCK=ROOT/'evaluation/substrate_capability/bigville_cross_boundary_map_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_bigville_cross_boundary_map_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=p['runs'];cases=[c for r in runs for c in r['cases']]
 checks={'schema_and_case_count':p.get('schema_version')==1 and len(cases)==24,'source_lock_and_capture_hash':p['locked_inputs']==lock['locked_inputs'] and p['lock_sha256']==sha(LOCK) and p['post_run_inputs']==p['locked_inputs'],'three_fresh_stable_workers':len(runs)==3 and len({r['pid'] for r in runs})==3 and all(r['started_inputs']==p['locked_inputs']==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==p['locked_inputs']==c['source_inputs_end'] for c in cases),'full_design_replication':all(sum(c['n_residents']==n and c['k']==k for c in cases)==3 for n in (10,25) for k in (0,2,4,6)),'boundary_nodes_match_k':all(c['boundary_size']==c['k'] and len(c['boundary_nodes'])==len(set(c['boundary_nodes'])) for c in cases),'interior_components_separated':all(c['interior_factorization_valid'] for c in cases),'enumeration_counts_reconstructed':all(c['boundary_assignments_checked']==3**c['k'] and c['local_assignments_checked']==c['expected_local_assignments'] and c['expected_local_assignments']==3**c['k']*sum(3**s for s in c['interior_component_sizes']) for c in cases),'global_conditional_exact_energy_agreement':all(abs(c['energy_gap'])<=1e-7 and abs(c['global_energy']-c['independent_global_energy'])<=1e-7 and abs(c['conditional_energy']-c['independent_conditional_energy'])<=1e-7 for c in cases),'complete_domain_valid_states':all(c['states_valid'] for c in cases),'positive_timing_records':all(all(x>0 for x in c['timing_ns'].values()) for c in cases)}
 summary=[]
 for n in (10,25):
  for k in (0,2,4,6):
   xs=[c for c in cases if c['n_residents']==n and c['k']==k]
   summary.append({'residents':n,'boundary_dimension':k,'replicates':len(xs),'median_interior_component_count':statistics.median(c['interior_component_count'] for c in xs),'median_global_width':statistics.median(c['global_width'] for c in xs),'boundary_assignments':statistics.median(c['boundary_assignments_checked'] for c in xs),'local_assignments':statistics.median(c['local_assignments_checked'] for c in xs),'median_global_ms':statistics.median(c['timing_ns']['global_width_and_map'] for c in xs)/1e6,'median_conditional_ms':statistics.median(c['timing_ns']['boundary_discovery_and_conditional_map'] for c in xs)/1e6})
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'case_count':len(cases),'summary_by_size_and_boundary':summary,'claim_boundary':p['claim_boundary']};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()
