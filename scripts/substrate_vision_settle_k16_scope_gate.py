#!/usr/bin/env python3
"""Calibrated K=16 orientation response under scope and cycle-plan arms."""
from __future__ import annotations
import copy,hashlib,json,platform,sys,time,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_K16_SCOPING_GATE_V1_1_AMENDMENT_20260925.md'
OUT=ROOT/'evaluation/reports/substrate_vision_settle_k16_scope_gate_v1_1_20260925.json'
TARGETS={'vision_waves','vision_settle','vision_onoff','vision_lateral','vision_compose'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def patched_doc(doc,scoped):
 m=copy.deepcopy(doc);n=0
 def visit(x):
  nonlocal n
  if isinstance(x,dict):
   if scoped and m.get('id')=='vision_settle' and x.get('type')=='NodesOfType' and x.get('node_type')=='SUnit':
    n+=1;return {'type':'Neighbours','node':{'type':'Var','name':'r'},'edge_type':'has_sunit','any_type':False}
   return {k:visit(v) for k,v in x.items()}
  if isinstance(x,list):return [visit(v) for v in x]
  return x
 for r in m.get('rules',[]):
  if 'match' not in r:continue
  if r.get('name')=='st_settle' and scoped:
   r['name']='st_settle_root_scoped_benchmark';r['where']=visit(r.get('where'));r['effects']=visit(r.get('effects'))
  r['latency_class']='hard_realtime'
 if scoped and m.get('id')=='vision_settle' and n!=2:raise RuntimeError(f'expected two root-scope substitutions, found {n}')
 return m

def arm(seed,scoped,executor,seed_doc):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as orig_manifest
 from scripts.settle_lib import build_sheet
 from domains.onoff_world import set_params
 from domains.lateral_world import set_lat_params
 import domains.complex_cells as cc
 from scripts.rung8_lib import develop_retina
 from scripts.rung8b_lib import grating_ensemble
 cache={sid:patched_doc(orig_manifest(sid),scoped) for sid in TARGETS}
 def wrapped(sid):return cache[sid] if sid in cache else orig_manifest(sid)
 boot_core.manifest_for=wrapped
 try:w,units,n_edges=build_sheet(seed=seed,n_side=4,channels='lateral',connectivity=8,settle=1,bubble=0)
 finally:
  boot_core.manifest_for=orig_manifest
 w.detect_cycles=True;s=w.s;inner=s._inner;root=w.retina
 if set(inner.neighbours(root,'has_sunit'))!=set(units):raise RuntimeError('root membership mismatch')
 rules=inner.export_rules();settle_name='st_settle_root_scoped_benchmark' if scoped else 'st_settle'
 selected={settle_name,'st_commit','oo_sunit_activate','oo_sunit_rate','lat_pool','lat_residual','lat_bipolar'}
 rule_classes={r['name']:r.get('latency_class','') for r in rules if r['name'] in selected}
 if executor=='tagged_tick' and not all(rule_classes.get(n)=='hard_realtime' for n in selected):raise RuntimeError(f'vision rules not all tagged: {rule_classes}')
 # Calibrated preparation: develop retina before cortical probe, then adapt theta.
 prep_start=time.perf_counter();develop_retina(w,3000);develop_seconds=time.perf_counter()-prep_start
 p=s.nodes('OnOffParams')[0];old_eta=float(s.node(p)['attrs'].get('oo_eta',5e-4))
 set_params(w,oo_eta=0.0,frozen=0.0,homeo=1.0)
 for lp in s.nodes('LatParams'):s.set_attr(lp,'frozen',1.0)
 rng=np.random.default_rng(seed+701);prep_reports=[];probe_reports=[];current_reports=prep_reports
 def present(world,frame,*,dstep=10.0):
  ss=world.s;step=float(ss.node(world.retina)['attrs'].get('step',0.0))+dstep;ss.set_attr(world.retina,'step',step)
  for (r,c),node in world.cells.items():
   on=(r<frame.shape[0] and c<frame.shape[1] and frame[r,c]>.5)
   ss.set_attr(node,'bursting',1.0 if on else 0.0);ss.set_attr(node,'last_burst',step if on else -999.0);ss.set_attr(node,'state','rested')
  for node in ss.nodes('Unit'):ss.set_attr(node,'bursting',0.0)
  if executor=='tagged_tick':
   n=int(ss._inner.tick(200000,True));current_reports.append({'progress':n,'status':'tick_cycle_detected' if n>0 else 'zero_progress'})
  else:
   q=ss._inner.run_rules_report(200000,True);current_reports.append({'progress':int(q['progress_steps']),'status':q['status']})
  return step
 old_present=cc.present;cc.present=present
 try:
  adapt_start=time.perf_counter()
  for _ in range(2000):present(w,grating_ensemble(w,rng))
  adapt_seconds=time.perf_counter()-adapt_start
 finally:cc.present=old_present
 set_params(w,oo_eta=old_eta,homeo=0.0)
 set_params(w,oo_eta=0.0,frozen=1.0,homeo=0.0);set_lat_params(w,frozen=1.0)
 wp=s.nodes('WaveParams')[0];s.set_attr(wp,'oja',1.0);s.set_attr(wp,'oja_eta',0.0);s.set_attr(wp,'bcm',0.0)
 for cp in s.nodes('ComplexParams'):s.set_attr(cp,'cx_eta',0.0)
 current_reports=probe_reports;cc.present=present
 try:
  t=time.perf_counter();stats=cc.cell_stats(w,units,key='rate',period=4.0,K=16);probe_seconds=time.perf_counter()-t
 finally:cc.present=old_present
 tuning=np.asarray(stats['tuning'],float);osi=np.asarray(stats['osi'],float)
 weights=[]
 for u in units:
  weights.append([float(s.node(v)['attrs'].get('weight',0.0)) for v in s.in_neighbours(u,'oo_post')])
 return {'variant':{'scope':'root_scoped' if scoped else 'global','executor':executor},'seed':seed,'n_side':4,'n_units':len(units),'n_edges':n_edges,'root_membership_count':len(s.neighbours(root,'has_sunit')),'rule_latency_classes':rule_classes,'development_seconds':develop_seconds,'adaptation_seconds':adapt_seconds,'probe_seconds':probe_seconds,'adaptation_status_counts':dict(__import__('collections').Counter(q['status'] for q in prep_reports)),'probe_status_counts':dict(__import__('collections').Counter(q['status'] for q in probe_reports)),'all_reports':len(probe_reports)+len(prep_reports),'mean_osi':float(np.mean(osi)),'osi_per_unit':osi.tolist(),'alive_per_unit':(tuning>1e-9).sum(axis=1).astype(int).tolist(),'tuning':tuning.tolist(),'tuning_sha256':hashlib.sha256(tuning.tobytes()).hexdigest(),'weight_sha256':hashlib.sha256(json.dumps(weights,separators=(',',':')).encode()).hexdigest(),'max_weight':max(max(q,default=0.0) for q in weights)}

def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from substrate.seed_loader import manifest_for
 from substrate_rs import _native
 # Load authored docs from live registry function for exact, current manifests.
 docs={sid:manifest_for(sid) for sid in TARGETS}
 seed=20260927;arms=[]
 for scoped in (False,True):
  for ex in ('full_rescan','tagged_tick'):
   print(f'ARM START scope={scoped} executor={ex}',flush=True)
   q=arm(seed,scoped,ex,docs['vision_settle']);arms.append(q)
   print(f'ARM DONE scope={scoped} executor={ex} OSI={q["mean_osi"]:.6f} development={q["development_seconds"]:.1f}s adaptation={q["adaptation_seconds"]:.1f}s probe={q["probe_seconds"]:.1f}s',flush=True)
   (OUT.parent/(OUT.stem+'.partial.json')).write_text(json.dumps({'completed_arms':arms},indent=2,sort_keys=True)+'\n')
 by={(q['variant']['scope'],q['variant']['executor']):q for q in arms}
 def delta(a,b):return float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
 checks={'four_arms':len(arms)==4,'all_roots_own_all_units':all(q['root_membership_count']==q['n_units'] for q in arms),'all_responses_nonzero':all(max(map(max,q['tuning']))>0 for q in arms),'global_executor_tuning_parity':delta(by[('global','full_rescan')]['tuning'],by[('global','tagged_tick')]['tuning'])<=1e-10,'scoped_executor_tuning_parity':delta(by[('root_scoped','full_rescan')]['tuning'],by[('root_scoped','tagged_tick')]['tuning'])<=1e-10,'fullrescan_scope_parity':delta(by[('global','full_rescan')]['tuning'],by[('root_scoped','full_rescan')]['tuning'])<=1e-10,'tagged_scope_parity':delta(by[('global','tagged_tick')]['tuning'],by[('root_scoped','tagged_tick')]['tuning'])<=1e-10,'no_silent_or_zero_progress_probe_reports':all(q['probe_status_counts'] and all(v in ('fixed_point','repeated_graph_state','tick_cycle_detected') for v in q['probe_status_counts']) for q in arms)}
 result={'run_id':'vision-settle-k16-scope-gate-20260925','arms':arms,'checks':checks,'max_deltas':{'global_executor':delta(by[('global','full_rescan')]['tuning'],by[('global','tagged_tick')]['tuning']),'scoped_executor':delta(by[('root_scoped','full_rescan')]['tuning'],by[('root_scoped','tagged_tick')]['tuning']),'fullrescan_scope':delta(by[('global','full_rescan')]['tuning'],by[('root_scoped','full_rescan')]['tuning']),'tagged_scope':delta(by[('global','tagged_tick')]['tuning'],by[('root_scoped','tagged_tick')]['tuning'])},'pass':all(checks.values()),'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(ROOT/'seeds/vision_settle.json'),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('cognitive_cycle.rs','substrate.rs','rewrite.rs','py.rs')}}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'max_deltas':result['max_deltas'],'osi':[{**q['variant'],'mean_osi':q['mean_osi'],'prep_s':q['development_seconds']+q['adaptation_seconds'],'probe_s':q['probe_seconds']} for q in arms]},indent=2))
 if not result['pass']:raise SystemExit('K=16 settling/scope gate failed')
if __name__=='__main__':main()
