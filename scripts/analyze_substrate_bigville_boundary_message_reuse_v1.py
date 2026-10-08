#!/usr/bin/env python3
"""Independent checks and work/time summaries for boundary message reuse."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_bigville_boundary_message_reuse_v1_20260926.json';LOCK=ROOT/'evaluation/substrate_capability/bigville_boundary_message_reuse_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_bigville_boundary_message_reuse_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads(RAW.read_text());lk=json.loads(LOCK.read_text());runs=p['runs'];cases=[c for r in runs for c in r['cases']]
 gates={'schema_and_24_cases':p.get('schema_version')==1 and len(cases)==24,'source_lock':p['locked_inputs']==lk['locked_inputs'] and p['post_run_inputs']==p['locked_inputs'] and p['lock_sha256']==sha(LOCK),'three_fresh_stable_workers':len(runs)==3 and len({r['pid'] for r in runs})==3 and all(r['started_inputs']==p['locked_inputs']==r['finished_inputs'] for r in runs) and all(c['source_inputs_start']==p['locked_inputs']==c['source_inputs_end'] for c in cases),'complete_design':all(sum(c['n_residents']==n and c['k']==k for c in cases)==3 for n in (10,25) for k in (0,2,4,6)),'exact_boundary_and_separator':all(c['boundary_size']==c['k'] and c['separator_condition_valid'] for c in cases),'reconstructed_message_work':all(c['message_assignment_count']==sum(3**(m+i) for m,i in c['component_shape'])==c['expected_message_assignment_count'] and c['global_boundary_assignments']==3**c['k']==c['expected_global_boundary_assignments'] for c in cases),'full_state_and_energy_parity':all(c['states_valid'] and abs(c['energy_gap'])<=1e-7 and abs(c['global_energy']-c['independent_global_energy'])<=1e-7 and abs(c['message_energy']-c['independent_message_energy'])<=1e-7 for c in cases),'positive_timing':all(all(t>0 for t in c['timing_ns'].values()) for c in cases)}
 summary=[]
 for n in (10,25):
  for k in (0,2,4,6):
   xs=[c for c in cases if c['n_residents']==n and c['k']==k];med=lambda f:statistics.median(f(c) for c in xs)
   summary.append({'residents':n,'boundary_dimension':k,'replicates':len(xs),'median_max_component_interface_size':med(lambda c:max(c['component_interfaces'],default=0)),'median_message_assignments':med(lambda c:c['message_assignment_count']),'median_direct_assignments':med(lambda c:c['direct_oracle_assignment_count']),'median_work_reduction_factor':med(lambda c:c['direct_oracle_assignment_count']/max(1,c['message_assignment_count'])),'median_global_map_ms':med(lambda c:c['timing_ns']['global_width_and_map'])/1e6,'median_message_map_ms':med(lambda c:c['timing_ns']['message_build_and_boundary_map'])/1e6,'median_global_width':med(lambda c:c['global_width'])})
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'gates':gates,'passed':all(gates.values()),'case_count':len(cases),'summary_by_size_and_boundary':summary,'claim_boundary':p['claim_boundary']};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()
