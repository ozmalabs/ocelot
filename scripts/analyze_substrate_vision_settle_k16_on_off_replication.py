#!/usr/bin/env python3
"""Independent audit of the two-seed K=16 settling replication."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_replication_20260925.json';LOCK=ROOT/'evaluation/substrate_capability/vision_settle_k16_on_off_replication_lock_20260925.json';OUT=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_replication_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def osi(t):
 out=[]
 for x in np.asarray(t,float):
  i=int(np.argmax(x));j=(i+len(x)//2)%len(x);a=x[i];b=x[j];out.append((a-b)/(a+b) if a+b>1e-9 else 0.)
 return np.asarray(out)
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];pairs=[]
 for seed in (20260929,20260930):
  on=next(a for a in d['arms'] if a['seed']==seed and a['settle']==1.0);off=next(a for a in d['arms'] if a['seed']==seed and a['settle']==0.0)
  x=np.asarray(on['tuning'],float);y=np.asarray(off['tuning'],float);s_on=int(sum(on['probe_tick_progress']));s_off=int(sum(off['probe_tick_progress']))
  pairs.append({'seed':seed,'max_abs_tuning_delta':float(np.max(np.abs(x-y))),'mean_osi_on':float(np.mean(osi(x))),'mean_osi_off':float(np.mean(osi(y))),'progress_on':s_on,'progress_off':s_off,'progress_reduction_fraction':1.0-s_off/s_on,'seconds_on':float(on['probe_seconds']),'seconds_off':float(off['probe_seconds'])})
 checks={'hashes_match_lock':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'] and l['hashes']['seed']==p['seed_sha256'],'analyzer_hash':l['hashes']['analyzer']==sha(Path(__file__)),'native_extension_match':l['native_extension_sha256']==p['native_extension_sha256'],'engine_matches_source':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'four_arms':len(d['arms'])==4,'480_readout_calls_each':all(len(a['probe_tick_progress'])==480 for a in d['arms']),'2000_adaptation_calls_each':all(len(a['adaptation_tick_progress'])==2000 for a in d['arms']),'counts_positive_below_budget':all(0<n<200000 for a in d['arms'] for n in a['probe_tick_progress']+a['adaptation_tick_progress']),'independent_osi_recomputation':max(float(np.max(np.abs(osi(a['tuning'])-np.asarray(a['osi_per_unit'])))) for a in d['arms'])<=1e-12,'probe_weights_unchanged':all(a['max_weight_drift']==0.0 and a['weight_sha256_before']==a['weight_sha256_after'] for a in d['arms']),'matched_adaptation_work_each_seed':all(sum(next(a for a in d['arms'] if a['seed']==s and a['settle']==1.0)['adaptation_tick_progress'])==sum(next(a for a in d['arms'] if a['seed']==s and a['settle']==0.0)['adaptation_tick_progress']) for s in (20260929,20260930))}
 out={'run_id':'vision-settle-k16-on-off-replication-independent-audit-v1','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'pairs':pairs,'checks':checks,'pass':all(checks.values()),'claim_boundary':['Two additional seeds; findings apply only to the declared preparation and orientation readout.','Progress values are native tick return counts, not termination classifications.','Timing is descriptive and based on one pair per seed.','This does not test cortical-weight learning or task-level capability.']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass'],'pairs':pairs},indent=2))
 if not out['pass']:raise SystemExit('independent replication audit failed')
if __name__=='__main__':main()
