#!/usr/bin/env python3
"""Independent parity/provenance audit for the orientation scope pilot."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_vision_settle_orientation_scope_pilot_v1_1_20260925.json"
LOCK=ROOT/"evaluation/substrate_capability/vision_settle_orientation_scope_pilot_v1_1_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_vision_settle_orientation_scope_pilot_v1_1_analysis_20260925.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];arms=[a for pair in d['pairs'] for a in pair['arms']]
 max_tune_delta=max(float(np.max(np.abs(np.asarray(q['arms'][0]['tuning'])-np.asarray(q['arms'][1]['tuning'])))) for q in d['pairs'])
 max_osi_delta=max(abs(q['arms'][0]['mean_osi']-q['arms'][1]['mean_osi']) for q in d['pairs'])
 checks={'runner_protocol_seed_hashes_match':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'] and l['hashes']['seed']==p['seed_sha256'],'analyzer_hash_matches_lock':l['hashes']['analyzer']==sha(Path(__file__)),'native_extension_matches_lock':l['native_extension_sha256']==p['native_extension_sha256'],'engine_matches_source':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'two_registered_pairs':[(q['n_side'],q['seed']) for q in d['pairs']]==[(3,20260925),(4,20260926)],'root_owns_all_units':all(a['root_membership_count']==a['units'] for a in arms),'all_units_respond_under_full_rescan':all(max(map(max,a['tuning']))>0 for a in arms),'all_standard_ticks_make_zero_progress':all(a['first_frame_path_diagnostic']['default_tick_progress']==0 for a in arms),'full_rescan_responds_on_same_frame':all(a['first_frame_path_diagnostic']['full_rescan_max_act']>0 and a['first_frame_path_diagnostic']['full_rescan_max_rate']>0 for a in arms),'reports_have_known_terminal_status':all(r['status'] in ('fixed_point','repeated_graph_state') for a in arms for r in a['probe_closure_reports']),'paired_tuning_within_tolerance':max_tune_delta<=1e-10,'paired_mean_osi_within_tolerance':max_osi_delta<=1e-10}
 out={'run_id':'vision-settle-orientation-scope-independent-audit-v1.1','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'max_tuning_abs_delta':max_tune_delta,'max_mean_osi_abs_delta':max_osi_delta,'checks':checks,'pass':all(checks.values()),'claim_boundary':['Full-rescan 12-orientation/four-phase OSI is paired and identical for these two single-sheet seeds.','Mean OSI is low (0.0132, 0.0176); this pilot does not demonstrate useful selectivity or capability.','Default tick makes zero progress after direct grating writes in this probe; full rescan responds. This is a default plan/rule-class mismatch to investigate.','Four phases are pilot resolution only; K=16 confirmation and learning/task-quality studies remain open.']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass'],'max_tuning_abs_delta':max_tune_delta,'max_mean_osi_abs_delta':max_osi_delta},indent=2))
 if not out['pass']:raise SystemExit('independent orientation audit failed')
if __name__=='__main__':main()
