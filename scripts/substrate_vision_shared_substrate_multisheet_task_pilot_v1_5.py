#!/usr/bin/env python3
"""Fixed-frame B-stack diagnostic on the v1.4 root-scoped paired fixture."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from domains.onoff_world import set_params
from domains.lateral_world import set_lat_params, gains, channels
from domains.complex_cells import grating,binarize
import domains.complex_cells as cc
from scripts.rung8b_lib import grating_ensemble
SEED=base.SEED
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_5_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_5_lock_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_5_20260927.json'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    locked=base.source_inputs()
    return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'v1_4_inputs':locked,
            'python':platform.python_version(),'platform':platform.platform()}
def main():
    if sys.argv[1:]==['--lock']:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
    print('stage=source_fingerprint_start',flush=True)
    locked=inputs()
    print('stage=source_fingerprint_done',flush=True)
    if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
    from scripts.rung8_lib import H,W,RF
    print('stage=build_pair_start',flush=True)
    s,(wA,wB),(uA,uB),top,(anatA,anatB)=base.build_pair(SEED,True);inner=s._inner
    print('stage=build_pair_done',flush=True)
    # Match v1.4's independent retinal development schedule.
    pp=s.nodes('OnOffParams')[0];eta=float(s.node(pp)['attrs'].get('oo_eta',5e-4))
    for world in (wA,wB):set_params(world,oo_eta=0.0,frozen=1.0);set_lat_params(world,frozen=0.0)
    for world in (wA,wB):
        tdev=time.perf_counter()
        for i in range(3000):
            world.step(ignite_k=1 if i%5==0 else 0)
            if (i+1)%100==0:print(f'stage=retina_development retina={world.retina} steps={i+1} elapsed={time.perf_counter()-tdev:.1f}s',flush=True)
        print(f'stage=retina_development_done retina={world.retina}',flush=True)
    for world in (wA,wB):set_params(world,oo_eta=eta,frozen=0.0)
    ga=gains(wA,anatA['hcells']);gb=gains(wB,anatB['hcells'])
    if min(float(np.max(np.abs(ga))),float(np.max(np.abs(gb))))<=.01:raise RuntimeError('retinal calibration failed')
    set_params(wA,oo_eta=0.0,frozen=0.0,homeo=1.0)
    for lp in s.nodes('LatParams'):s.set_attr(lp,'frozen',1.0)
    rng=np.random.default_rng(SEED+701)
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
    old_present=cc.present
    def present_pair(a,b):
        apply(a,b);cum=0;budget=base.INITIAL_PROGRESS_BUDGET;attempts=[]
        while True:
            q=inner.run_rules_report(budget,True);p=int(q['progress_steps']);cum+=p
            attempts.append({'status':q['status'],'progress':p,'budget':budget,'cumulative':cum,'passes':int(q['passes_completed'])})
            if q['status']!='progress_budget_reached':return attempts
            if cum>=base.MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION:raise RuntimeError('closure cumulative budget reached')
            budget=min(budget*2,base.MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION-cum)
    try:
        for i in range(2000):
                x=grating_ensemble(wA,rng);present_pair(x,x)
                if (i+1)%50==0:print(f'adaptation {i+1}/2000',flush=True)
    finally:cc.present=old_present
    set_params(wA,oo_eta=eta,homeo=0.0);set_params(wA,oo_eta=0.0,frozen=1.0,homeo=0.0);set_lat_params(wA,frozen=1.0)
    wp=s.nodes('WaveParams')[0];s.set_attr(wp,'oja',1.0);s.set_attr(wp,'oja_eta',0.0);s.set_attr(wp,'bcm',0.0)
    for cp in s.nodes('ComplexParams'):s.set_attr(cp,'cx_eta',0.0)
    oa,fa=channels(wA,anatA['bipolars']);ob,fb=channels(wB,anatB['bipolars'])
    if min(oa.sum(),fa.sum(),ob.sum(),fb.sum())<=0:raise RuntimeError('ON/OFF calibration channels inactive')
    blank=np.zeros((H,W),dtype=np.float32);a=binarize(grating((H,W),45.0,.3,4.0));b=binarize(grating((H,W),0.0,0.0,4.0))
    prepared=inner.graph_to_dict();prepared_hash=base.graph_digest(prepared);rows=[]
    conditions=[('both_blank',blank,blank),('b_only_exact',blank,b),('a_only_exact',a,blank),('both_exact',a,b)]
    for name,af,bf in conditions:
        inner.graph_from_dict(prepared)
        if base.graph_digest(inner.graph_to_dict())!=prepared_hash:raise RuntimeError('prepared state restore mismatch')
        reports=present_pair(af,bf)
        row={'condition':name,'prepared_graph_sha256':prepared_hash,'a_pixels':int(np.count_nonzero(af)),'b_pixels':int(np.count_nonzero(bf)),
             'a_retinal_bursts':sum(float(s.node(u)['attrs'].get('bursting',0)) for u in wA.cells.values()),
             'b_retinal_bursts':sum(float(s.node(u)['attrs'].get('bursting',0)) for u in wB.cells.values()),
             'A_units':base.unit_state(s,uA),'B_units':base.unit_state(s,uB),'closure_attempts':reports}
        rows.append(row);OUT.with_suffix('.partial.json').write_text(json.dumps({'conditions':rows},indent=2,sort_keys=True)+'\n')
        print(json.dumps({'condition':name,'b_rate_sum':row['B_units']['rate_sum'],'b_act_sum':row['B_units']['act_sum'],'statuses':[x['status'] for x in reports]},sort_keys=True),flush=True)
    final=inputs();result={'run_id':'vision-shared-substrate-multisheet-fixed-frame-v1.5-20260927','locked_inputs':locked,'post_run_inputs':final,
      'source_stable':locked==final,'scope':'root_scoped','seed':SEED,'topology':top,'calibration_channel_sums':{'A_on':float(oa.sum()),'A_off':float(fa.sum()),'B_on':float(ob.sum()),'B_off':float(fb.sum())},
      'adaptation_presentations':2000,'prepared_graph_sha256':prepared_hash,'conditions':rows}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'source_stable':result['source_stable'],'conditions':[(r['condition'],r['B_units']['rate_sum'],r['B_units']['act_sum']) for r in rows]},indent=2))
    if not result['source_stable']:raise SystemExit('source changed during diagnostic')
if __name__=='__main__':main()
