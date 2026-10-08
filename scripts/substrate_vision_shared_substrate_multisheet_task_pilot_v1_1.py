#!/usr/bin/env python3
"""K=16 task-interference pilot on two full sheets sharing one substrate."""
from __future__ import annotations
import contextlib, hashlib, importlib, json, os, platform, subprocess, sys, time
from pathlib import Path
from collections import Counter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'runners/dsl/python')]
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_PREREG_20260927.md'
AMENDMENT = ROOT / 'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_1_AMENDMENT_20260927.md'
LOCK = ROOT / 'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_1_lock_20260927.json'
OUT = ROOT / 'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_1_20260927.json'
ANALYZER = ROOT / 'scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_1.py'
SEED_DOCS = ('vision_waves', 'vision_settle', 'vision_onoff', 'vision_lateral', 'vision_compose')
SEED = 20260934
RUST = ('py.rs', 'scale_audit.rs', 'rewrite.rs', 'substrate.rs', 'graph_rules.rs', 'term.rs', 'access_trace.rs', 'cognitive_cycle.rs')
MODULES = ('scripts.settle_lib', 'scripts.rung8_lib', 'scripts.rung8b_lib',
           'domains.engine_provenance', 'domains.seed_registry', 'domains.settle_world',
           'domains.wave_world', 'domains.onoff_world', 'domains.lateral_world',
           'domains.complex_cells', 'substrate.boot_core', 'substrate.seed_loader',
           'substrate.seeds', 'evaluation.p0a.legacy_io_guard')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_inputs():
    for name in MODULES: importlib.import_module(name)
    from substrate.boot_core import CORE_SEEDS
    from substrate.seeds import REGISTRY
    ids = set(CORE_SEEDS); ids.update(x.id for x in REGISTRY.resolve(list(SEED_DOCS)))
    pending, seen, paths = list(ids), set(), set()
    while pending:
        sid = str(pending.pop())
        if sid in seen: continue
        seen.add(sid); p = ROOT / 'seeds' / f'{sid}.json'
        if not p.is_file(): continue
        paths.add(p)
        try: pending.extend(str(x) for x in json.loads(p.read_text()).get('depends_on', ()))
        except (OSError, json.JSONDecodeError): pass
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if not name: continue
        p = Path(name).resolve()
        if p.suffix != '.py' or '__pycache__' in p.parts: continue
        try: rel = p.relative_to(ROOT)
        except ValueError: continue
        if any(x in {'domains','substrate','scripts','evaluation','runners'} for x in rel.parts):
            if p not in {Path(__file__).resolve(), ANALYZER.resolve()}: paths.add(p)
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance
    return {'protocol_sha256':sha(PROTOCOL),'amendment_sha256':sha(AMENDMENT),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),
            'source_closure_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},
            'seed_sha256':{x:sha(ROOT/'seeds'/f'{x}.json') for x in sorted(seen) if (ROOT/'seeds'/f'{x}.json').is_file()},
            'rust_sha256':{x:sha(ROOT/'runners/dsl/src'/x) for x in RUST},
            'native_extension_sha256':sha(Path(_native.__file__).resolve()),
            'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
            'engine_provenance':engine_provenance(),
            'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}

def scoped_doc(doc):
    import copy
    out=copy.deepcopy(doc); hits=0
    def visit(x):
        nonlocal hits
        if isinstance(x,dict):
            if x.get('type')=='NodesOfType' and x.get('node_type')=='SUnit':
                hits+=1;return {'type':'Neighbours','node':{'type':'Var','name':'r'},'edge_type':'has_sunit','any_type':False}
            return {k:visit(v) for k,v in x.items()}
        if isinstance(x,list): return [visit(v) for v in x]
        return x
    for rule in out.get('rules',[]):
        if rule.get('name')=='st_settle':
            rule['name']='st_settle_root_scoped_benchmark';rule['where']=visit(rule.get('where'));rule['effects']=visit(rule.get('effects'))
    if hits!=2: raise RuntimeError(f'expected exactly two SUnit fold substitutions, got {hits}')
    return out

def build_pair(seed, scoped):
    import substrate.boot_core as boot
    from substrate.seed_loader import manifest_for as original_manifest_for
    from domains.wave_world import WaveWorld
    import domains.wave_world as wave_module
    from domains.lateral_world import add_lateral_retina, set_lat_params
    from domains.onoff_world import add_signed_units, set_params
    from domains.settle_world import wire_sheet, set_settle_params
    from scripts.settle_lib import lattice_centres
    from scripts.rung8_lib import H, W, RF
    chosen=scoped_doc(original_manifest_for('vision_settle')) if scoped else original_manifest_for('vision_settle')
    def manifest_for(sid): return chosen if sid=='vision_settle' else original_manifest_for(sid)
    boot.manifest_for=manifest_for
    try:
        s,agent=boot.boot_core(); seeds=['vision_waves','vision_settle','vision_onoff','vision_lateral','vision_compose']
        boot.load_seeds_into(s,agent,seeds)
    finally: boot.manifest_for=original_manifest_for
    wp=s.nodes('WaveParams')[0]
    s.set_attr(wp,'propagate',1.0);s.set_attr(wp,'oja',1.0);s.set_attr(wp,'oja_eta',0.0)
    wA=WaveWorld(s,h=H,w=W,seed=seed); wA.detect_cycles=True
    anatA=add_lateral_retina(wA); set_lat_params(wA,lateral=1.0,learn_gain=1.0,radius2=1.0,lat_eta=2e-3,lat_gmax=2.0,lat_g0=0.0,frozen=0.0)
    for p in s.nodes('ComposeParams'): s.set_attr(p,'compose',1.0)
    centers=lattice_centres(4)
    unitsA=add_signed_units(wA,anatA['bipolars'],16,rf=RF,seed=seed,centres=centers,w0=1.0)
    set_params(wA,onoff=1.0,split=1.0,subnorm=1.0,oo_eta=5e-4,oo_wmax=2.0,frozen=0.0)
    wire_sheet(wA,unitsA,connectivity=8);set_settle_params(wA,settle=1.0,bubble=0.0)
    # A second WaveWorld on the same graph must share the adapter-installed
    # drive rules; installing a duplicate set would confound the rule inventory.
    prior_installer=wave_module._install_change_rules
    wave_module._install_change_rules=lambda substrate: list(wA._drive_rules)
    try: wB=WaveWorld(s,h=H,w=W,seed=seed+1)
    finally: wave_module._install_change_rules=prior_installer
    wB.detect_cycles=True
    anatB=add_lateral_retina(wB)
    unitsB=add_signed_units(wB,anatB['bipolars'],16,rf=RF,seed=seed+100,centres=centers,w0=1.0)
    for i,u in enumerate(unitsB): s.set_attr(u,'name',f'B_s{i}')
    wire_sheet(wB,unitsB,connectivity=8)
    roots=[wA.retina,wB.retina]
    members=[set(s._inner.neighbours(r,'has_sunit')) for r in roots]
    if members != [set(unitsA),set(unitsB)] or members[0]&members[1]: raise RuntimeError('two-root membership mismatch')
    singleton_types=('SettleParams','OnOffParams','LatParams','ComposeParams')
    singleton_counts={t:len(s.nodes(t)) for t in singleton_types}
    if any(v!=1 for v in singleton_counts.values()): raise RuntimeError(f'parameter singleton mismatch: {singleton_counts}')
    return s,(wA,wB),(unitsA,unitsB),{'root_membership_counts':[len(x) for x in members],'singleton_counts':singleton_counts,
        'retina_ids':[str(x) for x in roots],'unit_ids':[[str(x) for x in unitsA],[str(x) for x in unitsB]],'rule_names':[r['name'] for r in s._inner.export_rules()]}

def weight_matrix(s,units):
    return [[float(s.node(v)['attrs'].get('weight',0.0)) for v in s.in_neighbours(u,'oo_post')] for u in units]

def one_arm(scoped,b_driven):
    from domains.onoff_world import set_params
    from domains.lateral_world import set_lat_params
    from scripts.rung8b_lib import grating_ensemble
    import domains.complex_cells as cc
    s,(wA,wB),(unitsA,unitsB),topology=build_pair(SEED,scoped)
    inner=s._inner; run_reports=[]; phase='development'
    dev_start=[float(s.node(w.retina)['attrs'].get('step',0.0)) for w in (wA,wB)]
    def develop_with_heartbeat(world,label):
        if not s.nodes('LatParams'): return
        pp=s.nodes('OnOffParams')[0];eta=float(s.node(pp)['attrs'].get('oo_eta',5e-4))
        set_params(world,oo_eta=0.0,frozen=1.0);set_lat_params(world,frozen=0.0)
        tstart=time.perf_counter()
        for i in range(3000):
            world.step(ignite_k=1 if i%5==0 else 0)
            if (i+1)%100==0: print(f'HEARTBEAT seed={SEED} scope={"root_scoped" if scoped else "global"} b={"grating" if b_driven else "blank"} phase=development world={label} steps={i+1} elapsed_s={time.perf_counter()-tstart:.1f}',flush=True)
        set_params(world,oo_eta=eta,frozen=0.0)
    t0=time.perf_counter();print('PHASE START development world=A',flush=True);develop_with_heartbeat(wA,'A');print('PHASE START development world=B',flush=True);develop_with_heartbeat(wB,'B');dev_seconds=time.perf_counter()-t0
    print(f'PHASE DONE development elapsed_s={dev_seconds:.2f}',flush=True)
    dev_end=[float(s.node(w.retina)['attrs'].get('step',0.0)) for w in (wA,wB)]
    p=s.nodes('OnOffParams')[0];old_eta=float(s.node(p)['attrs'].get('oo_eta',5e-4))
    set_params(wA,oo_eta=0.0,frozen=0.0,homeo=1.0)
    for lp in s.nodes('LatParams'):s.set_attr(lp,'frozen',1.0)
    rng=np.random.default_rng(SEED+701);phase='adaptation';phase_calls=0;adapt_start=time.perf_counter();print('PHASE START adaptation calls=2000',flush=True)
    def present_pair(frameA,frameB,*,dstep=10.0):
        nonlocal phase_calls
        phase_calls+=1
        for world,frame in ((wA,frameA),(wB,frameB)):
            step=float(s.node(world.retina)['attrs'].get('step',0.0))+dstep;s.set_attr(world.retina,'step',step)
            for (r,c),node in world.cells.items():
                on=(r<frame.shape[0] and c<frame.shape[1] and frame[r,c]>.5)
                s.set_attr(node,'bursting',1.0 if on else 0.0);s.set_attr(node,'last_burst',step if on else -999.0);s.set_attr(node,'state','rested')
        s.set_attr_many(s.nodes('Unit'),'bursting',0.0)
        q=inner.run_rules_report(200000,True);run_reports.append({'phase':phase,'progress':int(q['progress_steps']),'status':q['status']})
        if phase_calls%100==0: print(f'HEARTBEAT seed={SEED} scope={"root_scoped" if scoped else "global"} b={"grating" if b_driven else "blank"} phase={phase} calls={phase_calls} status={q["status"]}',flush=True)
        return float(s.node(wA.retina)['attrs']['step'])
    cc_present=cc.present;cc.present=lambda world,frame,**kw:present_pair(frame,frame,**kw)
    try:
        for i in range(2000):
            sample=grating_ensemble(wA,rng);present_pair(sample,sample)
            if (i+1)%100==0: print(f'HEARTBEAT seed={SEED} scope={"root_scoped" if scoped else "global"} b={"grating" if b_driven else "blank"} phase=adaptation presentations={i+1} elapsed_s={time.perf_counter()-adapt_start:.1f}',flush=True)
    finally: cc.present=cc_present
    adapt_seconds=time.perf_counter()-adapt_start;print(f'PHASE DONE adaptation elapsed_s={adapt_seconds:.2f}',flush=True)
    set_params(wA,oo_eta=old_eta,homeo=0.0);set_params(wA,oo_eta=0.0,frozen=1.0,homeo=0.0);set_lat_params(wA,frozen=1.0)
    wp=s.nodes('WaveParams')[0];s.set_attr(wp,'oja',1.0);s.set_attr(wp,'oja_eta',0.0);s.set_attr(wp,'bcm',0.0)
    for cp in s.nodes('ComplexParams'):s.set_attr(cp,'cx_eta',0.0)
    blank=np.zeros((wB.h,wB.w),dtype=np.float32)
    from domains.complex_cells import grating,binarize
    b_frame=binarize(grating((wB.h,wB.w),0.0,0.0,4.0)) if b_driven else blank
    phase='probe';phase_calls=0;probe_start=time.perf_counter();orig_present=cc.present;print('PHASE START probe K=16',flush=True)
    cc.present=lambda world,frame,**kw:present_pair(frame,b_frame,**kw)
    before=weight_matrix(s,unitsA)
    try: stats=cc.cell_stats(wA,unitsA,key='rate',period=4.0,K=16)
    finally: cc.present=orig_present
    after=weight_matrix(s,unitsA)
    max_weight_delta=max((abs(x-y) for a,b in zip(before,after) for x,y in zip(a,b)),default=0.0)
    probe_seconds=time.perf_counter()-probe_start;print(f'PHASE DONE probe elapsed_s={probe_seconds:.2f} calls={phase_calls}',flush=True)
    b_rates=[float(s.node(u)['attrs'].get('rate',0.0)) for u in unitsB]
    b_acts=[float(s.node(u)['attrs'].get('act',0.0)) for u in unitsB]
    b_bursting=sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wB.cells.values())
    return {'seed':SEED,'scope':'root_scoped' if scoped else 'global','b_condition':'grating' if b_driven else 'blank',
        'n_side':4,'units_per_root':[len(unitsA),len(unitsB)],'topology':topology,
        'development_start_steps':dev_start,'development_end_steps':dev_end,'development_requested_steps':[3000,3000],
        'development_seconds':dev_seconds,'adaptation_seconds':adapt_seconds,'probe_seconds':probe_seconds,
        'report_counts_by_phase':{k:dict(Counter(x['status'] for x in run_reports if x['phase']==k)) for k in ('development','adaptation','probe')},
        'reports':run_reports,'tuning':np.asarray(stats['tuning'],float).tolist(),'osi_per_unit':np.asarray(stats['osi'],float).tolist(),
        'mean_osi':float(np.mean(stats['osi'])),'a_tuning_sha256':hashlib.sha256(np.asarray(stats['tuning'],dtype=float).tobytes()).hexdigest(),
        'b_frame_active_pixels':int(np.count_nonzero(b_frame)),'b_bursting_after_readout':b_bursting,
        'b_rate_after_readout':b_rates,'b_act_after_readout':b_acts,
        'readout_weight_before':before,'readout_weight_after':after,'readout_weight_max_abs_delta':max_weight_delta}

def worker():
    started=source_inputs();arms=[];log=OUT.parent/f'{OUT.stem}.worker.log';OUT.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w') as fh,contextlib.redirect_stdout(fh):
        for scoped,b in ((False,False),(False,True),(True,False),(True,True)):
            print(f'ARM START scope={scoped} b={b}',flush=True)
            arm=one_arm(scoped,b);arms.append(arm)
            print(f'ARM DONE scope={arm["scope"]} b={arm["b_condition"]} OSI={arm["mean_osi"]:.6f}',flush=True)
            OUT.with_suffix('.partial.json').write_text(json.dumps({'completed_arms':arms},indent=2,sort_keys=True)+'\n')
    return {'pid':os.getpid(),'started_inputs':started,'finished_inputs':source_inputs(),'arms':arms}

def main():
    if sys.argv[1:]==['--lock']:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
    if len(sys.argv)==2 and sys.argv[1]=='--worker': print(json.dumps(worker(),sort_keys=True));return
    locked=source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing or stale source lock')
    env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
    proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
    run=json.loads(proc.stdout);post=source_inputs()
    arms=run['arms'];by={(x['scope'],x['b_condition']):x for x in arms}
    def maxdelta(x,y):return float(np.max(np.abs(np.asarray(x['tuning'])-np.asarray(y['tuning']))))
    from domains.complex_cells import binarize,grating
    expected_b_pixels=int(np.count_nonzero(binarize(grating((16,16),0.0,0.0,4.0))))
    scope_deltas={'global':maxdelta(by[('global','blank')],by[('global','grating')]),'root_scoped':maxdelta(by[('root_scoped','blank')],by[('root_scoped','grating')])}
    checks={'source_stable':post==locked==run['started_inputs']==run['finished_inputs'],
        'native_source_matches':locked['engine_provenance'].get('source_match') in ('own','shared') and not locked['engine_provenance'].get('stale_rust'),
        'four_arms_complete':len(arms)==4 and set((x['scope'],x['b_condition']) for x in arms)=={('global','blank'),('global','grating'),('root_scoped','blank'),('root_scoped','grating')},
        'topology_and_singletons':all(x['units_per_root']==[16,16] and x['topology']['root_membership_counts']==[16,16] and len(set(x['topology']['retina_ids']))==2 and all(v==1 for v in x['topology']['singleton_counts'].values()) and sum(n.startswith('st_settle') for n in x['topology']['rule_names'])==1 for x in arms),
        'development_clocks_exact':all(x['development_start_steps']==[0.0,0.0] and x['development_end_steps']==[3000.0,3000.0] and x['development_requested_steps']==[3000,3000] for x in arms),
        'report_statuses_no_cap':all(set(x['report_counts_by_phase'][phase])<= {'fixed_point','repeated_graph_state'} and sum(x['report_counts_by_phase'][phase].values())>0 for x in arms for phase in ('adaptation','probe')),
        'finite_nonzero_A_response':all(np.isfinite(np.asarray(x['tuning'])).all() and np.max(np.asarray(x['tuning']))>0 for x in arms),
        'readout_weights_unchanged':all(x['readout_weight_max_abs_delta']==0.0 and x['readout_weight_before']==x['readout_weight_after'] for x in arms),
        'b_context_stimulus_applied':all(x['b_frame_active_pixels']==(0 if x['b_condition']=='blank' else expected_b_pixels) and x['b_bursting_after_readout']==x['b_frame_active_pixels'] for x in arms)}
    payload={'schema_version':1,'run_id':'vision-shared-substrate-multisheet-task-pilot-v1.1-20260927','locked_inputs':locked,'post_run_inputs':post,
        'worker':run,'scope_deltas':scope_deltas,'checks':checks,'pass':all(checks.values()),
        'claim_boundary':'One-seed feasibility pilot for two full visual sheets sharing one substrate. Task contrast is whether B input changes A K=16 tuning under global versus root-scoped settling. Does not establish prevalence or cost.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'scope_deltas':scope_deltas},indent=2))
    if not payload['pass']:raise SystemExit('shared-substrate multi-sheet pilot failed its fixture/provenance gates')

if __name__=='__main__':main()
