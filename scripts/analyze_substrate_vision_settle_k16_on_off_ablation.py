#!/usr/bin/env python3
"""Independent response/work audit for the K=16 settle ablation."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_ablation_20260925.json';LOCK=ROOT/'evaluation/substrate_capability/vision_settle_k16_on_off_ablation_lock_20260925.json';OUT=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_ablation_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def osi(t):
 out=[]
 for x in np.asarray(t,float):
  i=int(np.argmax(x));j=(i+len(x)//2)%len(x);a=x[i];b=x[j];out.append((a-b)/(a+b) if a+b>1e-9 else 0.)
 return np.asarray(out)
def main():
 d=json.loads(RAW.read_text());l=json.loads(LOCK.read_text());p=d['provenance'];on,off=sorted(d['arms'],key=lambda a:-a['settle']);
 ton=np.asarray(on['tuning'],float);toff=np.asarray(off['tuning'],float);delt=np.abs(ton-toff)
 sums={str(a['settle']):int(sum(a['probe_tick_progress'])) for a in (on,off)};times={str(a['settle']):float(a['probe_seconds']) for a in (on,off)}
 checks={'hashes_match_lock':l['hashes']['runner']==p['runner_sha256'] and l['hashes']['protocol']==p['protocol_sha256'] and l['hashes']['seed']==p['seed_sha256'],'analyzer_hash':l['hashes']['analyzer']==sha(Path(__file__)),'native_extension_match':l['native_extension_sha256']==p['native_extension_sha256'],'engine_matches_source':p['engine_provenance']['source_match'] in ('own','shared') and not p['engine_provenance']['stale_rust'],'two_arms_on_then_off':[a['settle'] for a in d['arms']]==[1.0,0.0],'480_cell_stats_calls_each':len(on['probe_tick_progress'])==len(off['probe_tick_progress'])==480,'2000_adaptation_calls_each':len(on['adaptation_tick_progress'])==len(off['adaptation_tick_progress'])==2000,'counts_positive_below_budget':all(0<n<200000 for a in d['arms'] for n in a['probe_tick_progress']+a['adaptation_tick_progress']),'exact_response_parity':float(delt.max())==0.0,'independent_osi_recomputation':max(float(np.max(np.abs(osi(a['tuning'])-np.asarray(a['osi_per_unit'])))) for a in d['arms'])<=1e-12,'probe_weights_unchanged':all(a['max_weight_drift']==0.0 and a['weight_sha256_before']==a['weight_sha256_after'] for a in d['arms']),'matched_adaptation_work':sum(on['adaptation_tick_progress'])==sum(off['adaptation_tick_progress'])}
 out={'run_id':'vision-settle-k16-on-off-independent-audit-v1.1','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'max_abs_tuning_delta':float(delt.max()),'mean_osi_by_settle':{str(a['settle']):float(np.mean(osi(a['tuning']))) for a in d['arms']},'probe_progress_sum_by_settle':sums,'probe_seconds_by_settle':times,'probe_progress_reduction_fraction':1.0-sums['0.0']/sums['1.0'],'probe_time_reduction_fraction':1.0-times['0.0']/times['1.0'],'checks':checks,'pass':all(checks.values()),'claim_boundary':['One seed; exact response parity only for this developed/adapted sheet and probe sequence.','Settle-on used 91,006 versus 2,848 native progress applications; the operation difference is a direct measurement on these 480 inputs.','13.11s versus 3.92s is one paired timing observation and not a speedup estimate.','Tick integer returns do not identify termination reason.']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pass':out['pass'],'max_delta':float(delt.max()),'progress_sums':sums,'time_s':times},indent=2))
 if not out['pass']:raise SystemExit('independent settle-ablation audit failed')
if __name__=='__main__':main()
