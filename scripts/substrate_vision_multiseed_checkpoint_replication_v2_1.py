#!/usr/bin/env python3
"""Build independently adapted, source-locked vision checkpoints for three seeds."""
from __future__ import annotations
import hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from domains.onoff_world import set_params
from domains.lateral_world import set_lat_params,gains,channels
import domains.complex_cells as cc
from scripts.rung8b_lib import grating_ensemble
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_MULTI_SEED_CHECKPOINT_REPLICATION_V2_1_PREREG_20260929.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_1_lock_20260929.json'
OUT=ROOT/'evaluation/reports/vision_multiseed_checkpoint_replication_v2_1_20260929.json'
CHECKPOINTS=ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_1'
SEEDS=(20260938,20260939,20260940)
ANALYZER=ROOT/'scripts/analyze_substrate_vision_multiseed_checkpoint_replication_v2_1.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def exact_digest(g):return base.graph_digest(g)
def source_inputs():
 b=base.source_inputs();b.get('source_closure_sha256',{}).pop(f'scripts/{Path(__file__).name}',None)
 from domains.engine_provenance import engine_provenance
 from substrate_rs import _native
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'v1_4_source_inputs':b,'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'python':platform.python_version(),'platform':platform.platform(),'seeds':list(SEEDS)}
def build_one(seed):
 from scripts.rung8_lib import H,W
 s,(wA,wB),(uA,uB),top,(anatA,anatB)=base.build_pair(seed,True);inner=s._inner
 pp=s.nodes('OnOffParams')[0];eta=float(s.node(pp)['attrs'].get('oo_eta',5e-4))
 for world in (wA,wB):set_params(world,oo_eta=0.0,frozen=1.0);set_lat_params(world,frozen=0.0)
 dev_start=[float(s.node(w.retina)['attrs'].get('step',0.0)) for w in (wA,wB)]
 for world in (wA,wB):
  t=time.perf_counter()
  for i in range(3000):
   world.step(ignite_k=1 if i%5==0 else 0)
   if (i+1)%500==0:print(f'seed={seed} development={world.retina} steps={i+1}/3000 elapsed={time.perf_counter()-t:.1f}s',flush=True)
 for world in (wA,wB):set_params(world,oo_eta=eta,frozen=0.0)
 ga=gains(wA,anatA['hcells']);gb=gains(wB,anatB['hcells'])
 if min(float(np.max(np.abs(ga))),float(np.max(np.abs(gb))))<=.01:raise RuntimeError(f'seed {seed}: retinal calibration failed')
 set_params(wA,oo_eta=0.0,frozen=0.0,homeo=1.0)
 for lp in s.nodes('LatParams'):s.set_attr(lp,'frozen',1.0)
 rng=np.random.default_rng(seed+701);original=cc.present
 def apply(a,b):
  for world,frame in ((wA,a),(wB,b)):
   nodes=[world.cells[(r,c)] for r in range(world.h) for c in range(world.w)]
   on=[world.cells[(r,c)] for r in range(world.h) for c in range(world.w) if frame[r,c]>.5]
   off=[world.cells[(r,c)] for r in range(world.h) for c in range(world.w) if frame[r,c]<=.5]
   step=float(s.node(world.retina)['attrs'].get('step',0.0))+10.0;s.set_attr(world.retina,'step',step)
   if on:s.set_attr_many(on,'bursting',1.0);s.set_attr_many(on,'last_burst',step)
   if off:s.set_attr_many(off,'bursting',0.0);s.set_attr_many(off,'last_burst',-999.0)
   s.set_attr_many(nodes,'state','rested')
  s.set_attr_many(s.nodes('Unit'),'bursting',0.0)
 def present(a,b):
  apply(a,b);cum=0;budget=base.INITIAL_PROGRESS_BUDGET;attempts=[]
  while True:
   q=inner.run_rules_report(budget,True);p=int(q['progress_steps']);cum+=p
   attempts.append({'status':q['status'],'progress':p,'budget':budget,'cumulative':cum,'passes':int(q['passes_completed'])})
   if q['status']!='progress_budget_reached':return attempts
   if cum>=base.MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION:raise RuntimeError(f'seed {seed}: presentation cap')
   budget=min(budget*2,base.MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION-cum)
 try:
  work=[]
  for i in range(2000):
   x=grating_ensemble(wA,rng);attempts=present(x,x)
   if any(a['status'] not in ('fixed_point','repeated_graph_state') for a in attempts):raise RuntimeError(f'seed {seed}: unsettled adaptation presentation {i+1}')
   work.append({'presentation':i+1,'progress':sum(a['progress'] for a in attempts),'passes':sum(a['passes'] for a in attempts),'termination':attempts[-1]['status'],'attempts':attempts})
   if (i+1)%250==0:print(f'seed={seed} adaptation={i+1}/2000 elapsed={sum(x["progress"] for x in work):,} progress',flush=True)
 finally:cc.present=original
 set_params(wA,oo_eta=eta,homeo=0.0);set_params(wA,oo_eta=0.0,frozen=1.0,homeo=0.0);set_lat_params(wA,frozen=1.0)
 wp=s.nodes('WaveParams')[0];s.set_attr(wp,'oja',1.0);s.set_attr(wp,'oja_eta',0.0);s.set_attr(wp,'bcm',0.0)
 for cp in s.nodes('ComplexParams'):s.set_attr(cp,'cx_eta',0.0)
 oa,fa=channels(wA,anatA['bipolars']);ob,fb=channels(wB,anatB['bipolars'])
 activity={'A_on':float(oa.sum()),'A_off':float(fa.sum()),'B_on':float(ob.sum()),'B_off':float(fb.sum())}
 if min(activity.values())<=0:raise RuntimeError(f'seed {seed}: inactive ON/OFF channel {activity}')
 graph=inner.graph_to_dict();digest=exact_digest(graph)
 cp=CHECKPOINTS/f'seed_{seed}.json';cp.parent.mkdir(parents=True,exist_ok=True)
 checkpoint={'seed':seed,'scope':'root_scoped','topology':top,'development_start_steps':dev_start,'development_end_steps':[float(s.node(w.retina)['attrs'].get('step',0.0)) for w in (wA,wB)],'development_requested_steps':[3000,3000],'calibration_gain_max_abs':[float(np.max(np.abs(ga))),float(np.max(np.abs(gb)))],'retinal_channel_activity_after_adaptation':activity,'adaptation_presentations':2000,'adaptation_termination_counts':{k:sum(x['termination']==k for x in work) for k in ('fixed_point','repeated_graph_state')},'adaptation_progress_total':sum(x['progress'] for x in work),'adaptation_progress_max':max(x['progress'] for x in work),'adaptation_passes_total':sum(x['passes'] for x in work),'adaptation_work':work,'prepared_graph_sha256':digest,'graph':graph}
 cp.write_text(json.dumps(checkpoint,separators=(',',':'),sort_keys=True)+'\n')
 checkpoint.pop('graph');checkpoint['checkpoint_file']=str(cp.relative_to(ROOT));checkpoint['checkpoint_file_sha256']=sha(cp)
 return checkpoint
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=source_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing or stale source lock')
 prior=json.loads(OUT.read_text()) if OUT.exists() else {'run_id':'vision-multiseed-checkpoint-replication-v2.1-20260929','locked_inputs':locked,'seeds':{}}
 if prior.get('locked_inputs')!=locked:raise SystemExit('partial output source lock mismatch')
 for seed in SEEDS:
  dest=CHECKPOINTS/f'seed_{seed}.json'
  if str(seed) in prior['seeds']:
   cp=json.loads(dest.read_text())
   if exact_digest(cp['graph'])!=prior['seeds'][str(seed)]['prepared_graph_sha256']:raise SystemExit(f'seed {seed} checkpoint corrupt')
   print(f'seed={seed} checkpoint verified; skipping',flush=True);continue
  print(f'seed={seed} build_start',flush=True);record=build_one(seed);prior['seeds'][str(seed)]=record
  prior['source_stable']=source_inputs()==locked;OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(prior,indent=2,sort_keys=True)+'\n')
  print(f'seed={seed} checkpointed graph_sha256={record["prepared_graph_sha256"]}',flush=True)
 prior['source_stable']=source_inputs()==locked
 if not prior['source_stable']:raise SystemExit('source drift')
 OUT.write_text(json.dumps(prior,indent=2,sort_keys=True)+'\n')
 print(f'completed {len(prior["seeds"])}/{len(SEEDS)} seed checkpoints',flush=True)
if __name__=='__main__':main()
