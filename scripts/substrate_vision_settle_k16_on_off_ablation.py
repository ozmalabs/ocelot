#!/usr/bin/env python3
"""Matched K=16 acute settle-on/off orientation response ablation."""
from __future__ import annotations
import copy,hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_K16_ON_OFF_ABLATION_PREREG_20260925.md'
OUT=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_ablation_20260925.json'
PARTIAL=ROOT/'evaluation/reports/substrate_vision_settle_k16_on_off_ablation_20260925.partial.json'
TARGETS={'vision_waves','vision_settle','vision_onoff','vision_lateral','vision_compose'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tag_doc(doc):
 m=copy.deepcopy(doc)
 for r in m.get('rules',[]):
  if 'match' in r:r['latency_class']='hard_realtime'
 return m
def arm(seed,settle_value,seed_docs):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as original
 from scripts.settle_lib import build_sheet
 from scripts.rung8_lib import develop_retina
 from scripts.rung8b_lib import grating_ensemble,weights_of
 from domains.onoff_world import set_params
 from domains.lateral_world import set_lat_params
 import domains.complex_cells as cc
 cache={sid:tag_doc(seed_docs[sid]) for sid in TARGETS}
 def wrapped(sid):return cache[sid] if sid in cache else original(sid)
 boot_core.manifest_for=wrapped
 try:w,units,n_edges=build_sheet(seed=seed,n_side=4,channels='lateral',connectivity=8,settle=1.0,bubble=0.0)
 finally:boot_core.manifest_for=original
 w.detect_cycles=True;s=w.s;inner=s._inner;root=w.retina
 if set(inner.neighbours(root,'has_sunit'))!=set(units):raise RuntimeError('Retina does not own all SUnits')
 dev0=time.perf_counter();develop_retina(w,3000);dev_s=time.perf_counter()-dev0
 p=s.nodes('OnOffParams')[0];eta=float(s.node(p)['attrs'].get('oo_eta',5e-4))
 set_params(w,oo_eta=0.0,frozen=0.0,homeo=1.0)
 for lp in s.nodes('LatParams'):s.set_attr(lp,'frozen',1.0)
 rng=np.random.default_rng(seed+701);adapt_steps=[]
 def present(world,frame,*,dstep=10.0):
  ss=world.s;step=float(ss.node(world.retina)['attrs'].get('step',0.0))+dstep;ss.set_attr(world.retina,'step',step)
  for (r,c),node in world.cells.items():
   on=(r<frame.shape[0] and c<frame.shape[1] and frame[r,c]>.5)
   ss.set_attr(node,'bursting',1.0 if on else 0.0);ss.set_attr(node,'last_burst',step if on else -999.0);ss.set_attr(node,'state','rested')
  for node in ss.nodes('Unit'):ss.set_attr(node,'bursting',0.0)
  n=int(ss._inner.tick(200000,True));return step,n
 old_present=cc.present;cc.present=lambda world,frame,*,dstep=10.0:present(world,frame,dstep=dstep)[0]
 try:
  t=time.perf_counter()
  for _ in range(2000):adapt_steps.append(present(w,grating_ensemble(w,rng))[1])
  adapt_s=time.perf_counter()-t
 finally:cc.present=old_present
 set_params(w,oo_eta=eta,homeo=0.0);set_params(w,oo_eta=0.0,frozen=1.0,homeo=0.0);set_lat_params(w,frozen=1.0)
 wp=s.nodes('WaveParams')[0];s.set_attr(wp,'oja',1.0);s.set_attr(wp,'oja_eta',0.0);s.set_attr(wp,'bcm',0.0)
 for cp in s.nodes('ComplexParams'):s.set_attr(cp,'cx_eta',0.0)
 sett=s.nodes('SettleParams')
 if len(sett)!=1:raise RuntimeError(f'expected singleton SettleParams, got {len(sett)}')
 s.set_attr(sett[0],'settle',float(settle_value))
 probe_steps=[];cc.present=lambda world,frame,*,dstep=10.0:present_capture(world,frame,dstep)
 # Capture exact native tick counts for the 12*16 phase/orientation presentations.
 def _unused():pass
 def present_capture(world,frame,dstep=10.0):
  step,n=present(world,frame,dstep=dstep);probe_steps.append(n);return step
 cc.present=lambda world,frame,*,dstep=10.0:present_capture(world,frame,dstep)
 before=weights_of(w,units)
 try:t=time.perf_counter();stats=cc.cell_stats(w,units,key='rate',period=4.0,K=16);probe_s=time.perf_counter()-t
 finally:cc.present=old_present
 after=weights_of(w,units);tuning=np.asarray(stats['tuning'],float);osi=np.asarray(stats['osi'],float)
 return {'seed':seed,'settle':float(settle_value),'units':len(units),'edges':n_edges,'root_members':len(s.neighbours(root,'has_sunit')),'development_seconds':dev_s,'adaptation_seconds':adapt_s,'probe_seconds':probe_s,'adaptation_tick_progress':adapt_steps,'probe_tick_progress':probe_steps,'mean_osi':float(np.mean(osi)),'osi_per_unit':osi.tolist(),'alive_per_unit':(tuning>1e-9).sum(axis=1).astype(int).tolist(),'tuning':tuning.tolist(),'tuning_sha256':hashlib.sha256(tuning.tobytes()).hexdigest(),'weight_sha256_before':hashlib.sha256(np.asarray(before).tobytes()).hexdigest(),'weight_sha256_after':hashlib.sha256(np.asarray(after).tobytes()).hexdigest(),'max_weight_drift':float(np.max(np.abs(np.asarray(after)-np.asarray(before))))}
def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from substrate.seed_loader import manifest_for
 from substrate_rs import _native
 seed=20260928;docs={sid:manifest_for(sid) for sid in TARGETS};arms=[]
 for value in (1.0,0.0):
  print(f'ARM START settle={value}',flush=True);a=arm(seed,value,docs);arms.append(a)
  print(f'ARM DONE settle={value} OSI={a["mean_osi"]:.6f} dev={a["development_seconds"]:.1f}s adapt={a["adaptation_seconds"]:.1f}s probe={a["probe_seconds"]:.1f}s',flush=True)
  PARTIAL.write_text(json.dumps({'completed_arms':arms},indent=2,sort_keys=True)+'\n')
 on,off=arms;delta=np.asarray(on['tuning'])-np.asarray(off['tuning']);max_delta=float(np.max(np.abs(delta)))
 checks={'two_arms':len(arms)==2,'same_shape':on['units']==off['units']==16 and on['root_members']==off['root_members']==16,'probe_weights_unchanged':on['max_weight_drift']==0.0 and off['max_weight_drift']==0.0,'probe_count_expected':len(on['probe_tick_progress'])==len(off['probe_tick_progress'])==192,'adaptation_count_expected':len(on['adaptation_tick_progress'])==len(off['adaptation_tick_progress'])==2000,'all_tick_counts_positive_and_below_cap':all(0<n<200000 for a in arms for n in a['probe_tick_progress']+a['adaptation_tick_progress']),'nonzero_responses':max(map(max,on['tuning']))>0 and max(map(max,off['tuning']))>0}
 result={'run_id':'vision-settle-k16-on-off-ablation-20260925','arms':arms,'max_abs_tuning_delta':max_delta,'mean_osi_delta_on_minus_off':on['mean_osi']-off['mean_osi'],'checks':checks,'pass':all(checks.values()),'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(ROOT/'seeds/vision_settle.json'),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('cognitive_cycle.rs','substrate.rs','rewrite.rs','py.rs')}}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'max_abs_tuning_delta':max_delta,'mean_osi':[on['mean_osi'],off['mean_osi']],'mean_osi_delta':result['mean_osi_delta_on_minus_off']},indent=2))
 if not result['pass']:raise SystemExit('settle on/off gate failed a measurement invariant')
if __name__=='__main__':main()
