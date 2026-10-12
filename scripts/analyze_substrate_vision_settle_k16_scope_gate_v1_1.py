#!/usr/bin/env python3
"""Independent K=16 tuning/OSI parity and provenance audit."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_vision_settle_k16_scope_gate_v1_1_20260925.json';LOCK=ROOT/'evaluation/substrate_capability/vision_settle_k16_scope_gate_v1_1_lock_20260925.json';OUT=ROOT/'evaluation/reports/substrate_vision_settle_k16_scope_gate_v1_1_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def recalc_osi(tuning):
 a=np.asarray(tuning,float);out=[]
 for row in a:
  j=int(np.argmax(row));b=row[(j+len(row)//2)%len(row)];x=row[j]
  out.append(float((x-b)/(x+b)) if x+b>1e-9 else 0.0)
 return np.asarray(out)
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];arms=d['arms'];by={(q['variant']['scope'],q['variant']['executor']):q for q in arms}
 tuning_arrays=[np.asarray(q['tuning'],float) for q in arms];max_delta=max(float(np.max(np.abs(tuning_arrays[i]-tuning_arrays[0]))) for i in range(1,len(arms)))
 osi_errors=[float(np.max(np.abs(recalc_osi(q['tuning'])-np.asarray(q['osi_per_unit'],float)))) for q in arms]
 checks={'lock_runner_protocol_seed':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'] and l['hashes']['seed']==p['seed_sha256'],'analyzer_hash':l['hashes']['analyzer']==sha(Path(__file__)),'native_extension_hash':l['native_extension_sha256']==p['native_extension_sha256'],'engine_source_match':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'four_registered_arms':len(arms)==4 and set(by)=={('global','full_rescan'),('global','tagged_tick'),('root_scoped','full_rescan'),('root_scoped','tagged_tick')},'root_owns_every_unit':all(q['root_membership_count']==q['n_units']==16 for q in arms),'all_tuning_nonzero':all(np.max(np.asarray(q['tuning']))>0 for q in arms),'all_mean_osi_recomputed':max(osi_errors,default=1.0)<=1e-12,'all_pairs_exact_tuning':max_delta==0.0,'all_pair_mean_osi_equal':max(abs(q['mean_osi']-arms[0]['mean_osi']) for q in arms)==0.0,'matched_weight_hashes':len({q['weight_sha256'] for q in arms})==1,'fullrescan_statuses_explicit_and_tick_returns_positive':all(q['probe_status_counts'] and (set(q['probe_status_counts']).issubset({'fixed_point','repeated_graph_state'}) if q['variant']['executor']=='full_rescan' else q['probe_status_counts']=={'tick_cycle_detected':480}) for q in arms)}
 out={'run_id':'vision-settle-k16-scope-independent-audit-v1.1','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'max_abs_tuning_delta_across_four_arms':max_delta,'max_abs_osi_recalculation_error':max(osi_errors,default=0.0),'independent_mean_osi':{f"{s}/{e}":float(np.mean(recalc_osi(q['tuning']))) for (s,e),q in by.items()},'checks':checks,'pass':all(checks.values()),'claim_boundary':['One seed, 4x4 spatial sheet; calibrated development and 2,000-step theta adaptation; K=16 probe.','Exact parity holds for the four benchmark variants on this seed. Mean OSI 0.25246 is not a population estimate or evidence that the architecture learned useful selectivity.','Full-rescan termination statuses are explicit. Tick termination reason and exact per-call progress were not retained; the raw tick label denotes only a positive returned count, not proven cycle detection.','Production latency metadata and seed semantics remain unchanged.']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass'],'max_abs_tuning_delta':max_delta,'mean_osi':out['independent_mean_osi']},indent=2))
 if not out['pass']:raise SystemExit('independent K=16 audit failed')
if __name__=='__main__':main()
