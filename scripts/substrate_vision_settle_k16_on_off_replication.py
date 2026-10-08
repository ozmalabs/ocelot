#!/usr/bin/env python3
"""Two-seed, counterbalanced replication of the K=16 settle ablation."""
from __future__ import annotations
import hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_K16_ON_OFF_REPLICATION_PREREG_20260925.md'
OUT=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_replication_20260925.json'
PARTIAL=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_replication_20260925.partial.json'
OLD=ROOT/'scripts/substrate_vision_settle_k16_on_off_ablation.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from substrate.seed_loader import manifest_for
 from substrate_rs import _native
 import importlib.util
 spec=importlib.util.spec_from_file_location('first_ablation_runner',OLD);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 docs={sid:manifest_for(sid) for sid in mod.TARGETS};arms=[]
 order={20260929:(1.0,0.0),20260930:(0.0,1.0)}
 for seed,values in order.items():
  for value in values:
   print(f'ARM START seed={seed} settle={value}',flush=True);a=mod.arm(seed,value,docs);arms.append(a)
   print(f'ARM DONE seed={seed} settle={value} OSI={a["mean_osi"]:.6f} adapt={a["adaptation_seconds"]:.1f}s probe={a["probe_seconds"]:.1f}s',flush=True)
   PARTIAL.write_text(json.dumps({'completed_arms':arms},indent=2,sort_keys=True)+'\n')
 pairs=[]
 for seed in order:
  on=next(a for a in arms if a['seed']==seed and a['settle']==1.0);off=next(a for a in arms if a['seed']==seed and a['settle']==0.0)
  delta=np.asarray(on['tuning'])-np.asarray(off['tuning'])
  pairs.append({'seed':seed,'max_abs_tuning_delta':float(np.max(np.abs(delta))),'mean_osi_delta_on_minus_off':on['mean_osi']-off['mean_osi'],'progress_sum_on':int(sum(on['probe_tick_progress'])),'progress_sum_off':int(sum(off['probe_tick_progress']))})
 checks={'four_arms':len(arms)==4,'seed_order_counterbalanced':[(a['seed'],a['settle']) for a in arms]==[(20260929,1.0),(20260929,0.0),(20260930,0.0),(20260930,1.0)],'shape_each_arm':all(a['units']==a['root_members']==16 for a in arms),'probe_count_expected':all(len(a['probe_tick_progress'])==480 for a in arms),'adaptation_count_expected':all(len(a['adaptation_tick_progress'])==2000 for a in arms),'all_tick_counts_positive_and_below_cap':all(0<n<200000 for a in arms for n in a['probe_tick_progress']+a['adaptation_tick_progress']),'probe_weights_unchanged':all(a['max_weight_drift']==0.0 for a in arms),'matched_adaptation_work_within_seed':all(sum(next(a for a in arms if a['seed']==s and a['settle']==1.0)['adaptation_tick_progress'])==sum(next(a for a in arms if a['seed']==s and a['settle']==0.0)['adaptation_tick_progress']) for s in order),'nonzero_responses':all(max(map(max,a['tuning']))>0 for a in arms)}
 result={'run_id':'vision-settle-k16-on-off-replication-20260925','arms':arms,'pairs':pairs,'checks':checks,'pass':all(checks.values()),'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(ROOT/'seeds/vision_settle.json'),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('cognitive_cycle.rs','substrate.rs','rewrite.rs','py.rs')}}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'pairs':pairs},indent=2))
 if not result['pass']:raise SystemExit('replication failed a measurement invariant')
if __name__=='__main__':main()
