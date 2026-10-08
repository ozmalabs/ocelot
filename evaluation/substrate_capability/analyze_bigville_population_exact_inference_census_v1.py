#!/usr/bin/env python3
"""Independent integrity and population summaries for Bigville CAN census."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/'evaluation/substrate_capability/bigville_population_exact_inference_census_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/bigville_population_exact_inference_census_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/bigville_population_exact_inference_census_v1_20261002.json'
OUT=ROOT/'evaluation/reports/bigville_population_exact_inference_census_v1_20261002_analysis.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location('bigville_pop_census_analyzer',RUNNER)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def analyze():
 r=load_runner();cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text());rows=cap.get('runs',[]);checks=[]
 def check(name,ok):checks.append((name,bool(ok)))
 check('schema',cap.get('schema')=='BigvillePopulationExactInferenceCensusV1Results')
 check('capture_lock',cap.get('lock_sha256')==sha(LOCK))
 check('source_lock',cap.get('sources')==lock.get('sources')==r.source_lock())
 check('postrun_lock',cap.get('post_run_sources')==lock.get('sources'))
 check('worker_count',len(rows)==r.REPLICATES)
 check('fresh_worker_pids',len({x.get('worker_pid') for x in rows})==r.REPLICATES)
 check('capture_gates',all(cap.get('checks',{}).values()))
 check('full_population_per_worker',all(x.get('resident_count')==100 and len(x.get('local_results',[]))==100 for x in rows))
 check('unique_resident_positions',all([z['resident_position'] for z in x['local_results']]==list(range(100)) for x in rows))
 check('component_sizes',all(set(x['frame_sizes'])=={5} and len(x['frame_sizes'])==100 for x in rows))
 check('disconnected_by_design',all(x['cross_frame_edges']==0 and x['directed_causal_edges']==1000 for x in rows))
 check('all_local_oracles',all(x['all_local_oracles_match'] and all(abs(z['jt_energy']-z['oracle_energy'])<r.TOL and abs(z['direct_rescore']-z['oracle_energy'])<r.TOL and z['valid_state'] for z in x['local_results']) for x in rows))
 check('whole_population_parity',all(x['whole_matches_oracle'] and x['whole_matches_local_oracle'] for x in rows))
 check('exact_widths',all(set(x['certified_widths'])=={2} and x['global_minfill_width']==2 and x['global_profile']['width']==2 for x in rows))
 check('no_mutation',all(x['no_state_mutation'] for x in rows))
 check('resident_bins_repeat',all(x['effective_bins']==rows[0]['effective_bins'] for x in rows))
 bins=rows[0]['effective_bins'] if rows else []
 distribution={str(k):bins.count(k) for k in sorted(set(bins))}
 metrics=('population_build','runtime_extraction_all_frames','global_minfill_order','whole_population_jt')
 result={'schema':'BigvillePopulationExactInferenceCensusV1Analysis','passed':sum(ok for _,ok in checks),'total':len(checks),
  'checks':[{'name':n,'passed':ok} for n,ok in checks],'worker_count':len(rows),'population_size':len(bins),
  'effective_resolution_bins_distribution':distribution,'per_worker':[
   {'replicate':x['replicate'],'whole_width':x['global_minfill_width'],'whole_jt_ms':x['timing_ns']['whole_population_jt']/1e6,
    'resident_jt_median_ms':x['local_jt_median_ns']/1e6,'resident_jt_total_ms':x['local_jt_total_ns']/1e6,
    'population_build_ms':x['timing_ns']['population_build']/1e6,'extract_all_frames_ms':x['timing_ns']['runtime_extraction_all_frames']/1e6,
    'global_minfill_ms':x['timing_ns']['global_minfill_order']/1e6,'local_oracle_assignments':x['local_assignment_total'],
    'whole_vs_local_jt_ratio':x['timing_ns']['whole_population_jt']/x['local_jt_total_ns']} for x in rows],
  'median_ms':{k:statistics.median(x['timing_ns'][k] for x in rows)/1e6 for k in metrics},
  'interpretation':'Complete census of the registered Bigville population; all frames are five-node width-2 CANs and disconnected by construction, so this is an integration positive control, not evidence for natural cheap-cut prevalence.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(f"{result['passed']}/{result['total']} checks; {OUT.relative_to(ROOT)}")
 return 0 if all(ok for _,ok in checks) else 1
if __name__=='__main__':raise SystemExit(analyze())
