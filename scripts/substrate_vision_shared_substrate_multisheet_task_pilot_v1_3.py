#!/usr/bin/env python3
"""K=16 task-interference pilot with bounded closure continuation."""
from __future__ import annotations
import contextlib, hashlib, importlib, json, os, platform, subprocess, sys, time
from pathlib import Path
from collections import Counter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'runners/dsl/python')]
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_PREREG_20260927.md'
AMENDMENT = ROOT / 'docs/research/engine_substrate/SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_3_AMENDMENT_20260927.md'
LOCK = ROOT / 'evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_3_lock_20260927.json'
OUT = ROOT / 'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_3_20260927.json'
ANALYZER = ROOT / 'scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_3.py'
SEED_DOCS = ('vision_waves', 'vision_settle', 'vision_onoff', 'vision_lateral', 'vision_compose')
SEED = 20260934
INITIAL_PROGRESS_BUDGET = 200_000
MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION = 1_600_000
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

def benchmark_doc(doc, scoped=False):
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
        if 'match' in rule: rule['latency_class']='hard_realtime'
        if rule.get('name')=='st_settle':
            if scoped:
                rule['name']='st_settle_root_scoped_benchmark';rule['where']=visit(rule.get('where'));rule['effects']=visit(rule.get('effects'))
    if scoped and hits!=2: raise RuntimeError(f'expected exactly two SUnit fold substitutions, got {hits}')
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
    cache={sid:benchmark_doc(original_manifest_for(sid),scoped and sid=='vision_settle') for sid in SEED_DOCS}
    def manifest_for(sid): return cache[sid] if sid in cache else original_manifest_for(sid)
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
    rules=s._inner.export_rules(); selected={'st_settle_root_scoped_benchmark' if scoped else 'st_settle','st_commit','oo_sunit_activate','oo_sunit_rate','lat_pool','lat_residual','lat_bipolar'}
    classes={r['name']:r.get('latency_class','') for r in rules if r['name'] in selected}
    manifest_tag_counts={sid:sum(1 for r in cache[sid].get('rules',[]) if 'match' in r and r.get('latency_class')=='hard_realtime') for sid in SEED_DOCS}
    if not all(classes.get(n)=='hard_realtime' for n in selected): raise RuntimeError(f'benchmark vision rules are not all hard_realtime: {classes}')
    return s,(wA,wB),(unitsA,unitsB),{'root_membership_counts':[len(x) for x in members],'singleton_counts':singleton_counts,
        'retina_ids':[str(x) for x in roots],'unit_ids':[[str(x) for x in unitsA],[str(x) for x in unitsB]],
        'rule_names':[r['name'] for r in rules],'selected_rule_latency_classes':classes,'manifest_tag_counts':manifest_tag_counts},(anatA,anatB)

def weight_matrix(s,units):
    return [[float(s.node(v)['attrs'].get('weight',0.0)) for v in s.in_neighbours(u,'oo_post')] for u in units]

def canonical_graph(value):
    if isinstance(value,dict):return {k:canonical_graph(v) for k,v in value.items()}
    if isinstance(value,list):return [canonical_graph(v) for v in value]
    if isinstance(value,float):return round(value,12)
    return value

def graph_digest(value):
    return hashlib.sha256(json.dumps(canonical_graph(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def graph_equivalent(a,b,tol=1e-12):
    if type(a)!=type(b):return False
    if isinstance(a,dict):return set(a)==set(b) and all(graph_equivalent(a[k],b[k],tol) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(graph_equivalent(x,y,tol) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):return abs(float(a)-float(b))<=tol
    return a==b

def one_scope(scoped):
    from domains.onoff_world import set_params
    from domains.lateral_world import set_lat_params, gains, channels
    from scripts.rung8b_lib import grating_ensemble
    from domains.complex_cells import grating, binarize
    import domains.complex_cells as cc
    s,(wA,wB),(unitsA,unitsB),topology,(anatA,anatB)=build_pair(SEED,scoped)
    inner=s._inner;run_reports=[];contexts=[];presentation_summaries=[];phase='development';phase_calls=0
    def heartbeat(msg): print(f'HEARTBEAT seed={SEED} scope={"root_scoped" if scoped else "global"} {msg}',flush=True)
    def develop(world,label):
        pp=s.nodes('OnOffParams')[0];eta=float(s.node(pp)['attrs'].get('oo_eta',5e-4))
        set_params(world,oo_eta=0.0,frozen=1.0);set_lat_params(world,frozen=0.0)
        begin=time.perf_counter()
        for i in range(3000):
            world.step(ignite_k=1 if i%5==0 else 0)
            if (i+1)%100==0: heartbeat(f'phase=development retina={label} steps={i+1} elapsed_s={time.perf_counter()-begin:.1f}')
        set_params(world,oo_eta=eta,frozen=0.0)
    dev_start=[float(s.node(w.retina)['attrs'].get('step',0.0)) for w in (wA,wB)]
    t0=time.perf_counter();print('PHASE START development',flush=True);develop(wA,'A');develop(wB,'B');dev_seconds=time.perf_counter()-t0
    dev_end=[float(s.node(w.retina)['attrs'].get('step',0.0)) for w in (wA,wB)]
    gainA=gains(wA,anatA['hcells']);gainB=gains(wB,anatB['hcells'])
    if not (np.max(np.abs(gainA))>0.01 and np.max(np.abs(gainB))>0.01): raise RuntimeError('retinal development did not produce nonzero surround gains')
    print(f'PHASE DONE development seconds={dev_seconds:.3f} gain_max={[float(np.max(np.abs(gainA))),float(np.max(np.abs(gainB)))]}',flush=True)
    p=s.nodes('OnOffParams')[0];old_eta=float(s.node(p)['attrs'].get('oo_eta',5e-4))
    set_params(wA,oo_eta=0.0,frozen=0.0,homeo=1.0)
    for lp in s.nodes('LatParams'):s.set_attr(lp,'frozen',1.0)
    rng=np.random.default_rng(SEED+701);phase='adaptation';adapt_start=time.perf_counter();print('PHASE START adaptation presentations=2000',flush=True)
    phase_calls=0

    def apply_pair_inputs(frameA,frameB,*,advance=True,bulk=True):
        nonlocal phase_calls
        phase_calls+=1
        for world,frame in ((wA,frameA),(wB,frameB)):
            nodes=[world.cells[(r,c)] for r in range(world.h) for c in range(world.w)]
            on=[world.cells[(r,c)] for r in range(world.h) for c in range(world.w) if frame[r,c]>.5]
            off=[world.cells[(r,c)] for r in range(world.h) for c in range(world.w) if frame[r,c]<=.5]
            step=float(s.node(world.retina)['attrs'].get('step',0.0))+(10.0 if advance else 0.0)
            if advance:s.set_attr(world.retina,'step',step)
            if bulk:
                if on:s.set_attr_many(on,'bursting',1.0);s.set_attr_many(on,'last_burst',step)
                if off:s.set_attr_many(off,'bursting',0.0);s.set_attr_many(off,'last_burst',-999.0)
                s.set_attr_many(nodes,'state','rested')
            else:
                for (r,c),node in world.cells.items():
                    is_on=frame[r,c]>.5
                    s.set_attr(node,'bursting',1.0 if is_on else 0.0)
                    s.set_attr(node,'last_burst',step if is_on else -999.0)
                    s.set_attr(node,'state','rested')
        s.set_attr_many(s.nodes('Unit'),'bursting',0.0)

    # Verify batched writer semantics against the scalar registered behavior
    # before any learning or task readout.
    testA=binarize(grating((wA.h,wA.w),45.0,0.3,4.0));testB=binarize(grating((wB.h,wB.w),90.0,0.7,4.0))
    input_base=inner.graph_to_dict();apply_pair_inputs(testA,testB,advance=False,bulk=False);scalar_state=inner.graph_to_dict()
    inner.graph_from_dict(input_base);apply_pair_inputs(testA,testB,advance=False,bulk=True);batch_state=inner.graph_to_dict()
    batch_writer_equal=graph_equivalent(scalar_state,batch_state)
    inner.graph_from_dict(input_base)
    if not batch_writer_equal:
        def first_diff(a,b,path='$'):
            if type(a)!=type(b): return (path,type(a).__name__,type(b).__name__)
            if isinstance(a,dict):
                if set(a)!=set(b): return (path,'keys',sorted(set(a)^set(b),key=str)[:10])
                for k in a:
                    d=first_diff(a[k],b[k],f'{path}.{k}')
                    if d:return d
            elif isinstance(a,list):
                if len(a)!=len(b):return (path,'length',len(a),len(b))
                for i,(x,y) in enumerate(zip(a,b)):
                    d=first_diff(x,y,f'{path}[{i}]')
                    if d:return d
            elif a!=b:return (path,repr(a)[:120],repr(b)[:120])
            return None
        heartbeat(f'batch_writer_first_diff={first_diff(scalar_state,batch_state)}')
        raise RuntimeError('batched frame writes differ from scalar writes')
    phase_calls=0

    def present_pair(frameA,frameB,*,dstep=10.0):
        nonlocal phase_calls
        apply_pair_inputs(frameA,frameB,advance=True,bulk=True)
        pid=phase_calls;budget=INITIAL_PROGRESS_BUDGET;cumulative=0;attempt=0;attempts=[]
        while True:
            attempt+=1;q=inner.run_rules_report(budget,True);progress=int(q['progress_steps']);cumulative+=progress
            row={'phase':phase,'call':pid,'attempt':attempt,'progress':progress,'budget':budget,'status':q['status'],'cumulative_progress':cumulative,'passes_completed':int(q['passes_completed'])}
            run_reports.append(row);attempts.append(row)
            if q['status']!='progress_budget_reached':break
            heartbeat(f'BUDGET CONTINUE phase={phase} call={pid} attempt={attempt} cumulative={cumulative}/{MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION}')
            if cumulative>=MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION:
                cap_record={'seed':SEED,'scope':'root_scoped' if scoped else 'global','phase':phase,'call':pid,'attempts':attempts,
                    'prior_status_counts':{p:dict(Counter(x['status'] for x in run_reports if x['phase']==p)) for p in ('adaptation','probe_blank','probe_blank_replay','probe_grating')},
                    'prior_completed_contexts':contexts,'prior_presentation_reports':presentation_summaries}
                (OUT.parent/f'{OUT.stem}.cap_diagnostic.json').write_text(json.dumps(cap_record,indent=2,sort_keys=True)+'\n')
                raise RuntimeError(f'cumulative progress bound reached in {phase} call {pid}: {cumulative}')
            budget=min(budget*2,MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION-cumulative)
        presentation_summaries.append({'phase':phase,'call':pid,'attempt_count':attempt,'intermediate_budget_hits':sum(r['status']=='progress_budget_reached' for r in attempts),
            'cumulative_progress':cumulative,'final_status':q['status']})
        if phase_calls%100==0:heartbeat(f'phase={phase} calls={phase_calls} status={q["status"]}')
        return float(s.node(wA.retina)['attrs']['step'])

    old_present=cc.present;cc.present=lambda world,frame,**kw:present_pair(frame,frame,**kw)
    try:
        for i in range(2000):
            stimulus=grating_ensemble(wA,rng);present_pair(stimulus,stimulus)
            if (i+1)%100==0:heartbeat(f'phase=adaptation presentations={i+1} elapsed_s={time.perf_counter()-adapt_start:.1f}')
    finally:cc.present=old_present
    adapt_seconds=time.perf_counter()-adapt_start
    set_params(wA,oo_eta=old_eta,homeo=0.0);set_params(wA,oo_eta=0.0,frozen=1.0,homeo=0.0);set_lat_params(wA,frozen=1.0)
    wp=s.nodes('WaveParams')[0];s.set_attr(wp,'oja',1.0);s.set_attr(wp,'oja_eta',0.0);s.set_attr(wp,'bcm',0.0)
    for cp in s.nodes('ComplexParams'):s.set_attr(cp,'cx_eta',0.0)
    onA,offA=channels(wA,anatA['bipolars']);onB,offB=channels(wB,anatB['bipolars'])
    channel_activity={'A_on':float(onA.sum()),'A_off':float(offA.sum()),'B_on':float(onB.sum()),'B_off':float(offB.sum())}
    if min(channel_activity.values())<=0.0:raise RuntimeError(f'both retinal ON/OFF channels must be active after calibration/adaptation: {channel_activity}')

    blank=np.zeros((wB.h,wB.w),dtype=np.float32)
    bgrating=binarize(grating((wB.h,wB.w),0.0,0.0,4.0))
    prepared_graph=inner.graph_to_dict();prepared_sha=graph_digest(prepared_graph)
    for context,bframe in (('blank',blank),('blank_replay',blank),('grating',bgrating)):
        inner.graph_from_dict(prepared_graph)
        restored=inner.graph_to_dict();restored_sha=graph_digest(restored)
        if restored_sha!=prepared_sha:raise RuntimeError('prepared graph snapshot did not restore exactly')
        phase=f'probe_{context}';phase_calls=0;probe_start=time.perf_counter();
        cc.present=lambda world,frame,**kw:present_pair(frame,bframe,**kw)
        before=weight_matrix(s,unitsA)
        try:stats=cc.cell_stats(wA,unitsA,key='rate',period=4.0,K=16)
        finally:cc.present=old_present
        after=weight_matrix(s,unitsA);max_weight_delta=max((abs(x-y) for a,b in zip(before,after) for x,y in zip(a,b)),default=0.0)
        report_rows=[x for x in run_reports if x['phase']==phase]
        b_bursting=sum(float(s.node(u)['attrs'].get('bursting',0.0)) for u in wB.cells.values())
        contexts.append({'context':context,'b_frame_active_pixels':int(np.count_nonzero(bframe)),'b_bursting_after_readout':b_bursting,
            'restored_graph_sha256':restored_sha,'tuning':np.asarray(stats['tuning'],float).tolist(),'osi_per_unit':np.asarray(stats['osi'],float).tolist(),
            'mean_osi':float(np.mean(stats['osi'])),'readout_seconds':time.perf_counter()-probe_start,
            'reports':report_rows,'report_status_counts':dict(Counter(x['status'] for x in report_rows)),
            'final_presentation_status_counts':dict(Counter(x['final_status'] for x in presentation_summaries if x['phase']==phase)),
            'presentation_work': [x for x in presentation_summaries if x['phase']==phase],
            'readout_weight_before':before,'readout_weight_after':after,'readout_weight_max_abs_delta':max_weight_delta})
        (OUT.parent/f'{OUT.stem}.contexts.partial.json').write_text(json.dumps({'scope':'root_scoped' if scoped else 'global','contexts':contexts},indent=2,sort_keys=True)+'\n')
        heartbeat(f'phase={phase} done calls={phase_calls} elapsed_s={contexts[-1]["readout_seconds"]:.2f}')
    cc.present=old_present
    status_summary={p:dict(Counter(x['final_status'] for x in presentation_summaries if x['phase']==p)) for p in ('adaptation','probe_blank','probe_blank_replay','probe_grating')}
    for run_phase in ('adaptation','probe_blank','probe_blank_replay','probe_grating'):
        rows=[x for x in presentation_summaries if x['phase']==run_phase]
        if not rows or any(x['final_status'] not in ('fixed_point','repeated_graph_state') for x in rows):
            diagnostic={'scope':'root_scoped' if scoped else 'global','status_counts':status_summary,
                'unexpected_rows':[x for x in presentation_summaries if x['final_status'] not in ('fixed_point','repeated_graph_state')],
                'contexts':contexts,'calibration_gains':{'A':gainA.tolist(),'B':gainB.tolist()},
                'retinal_channel_activity_after_adaptation':channel_activity,'batch_writer_scalar_equivalence':batch_writer_equal,
                'prepared_graph_sha256':prepared_sha}
            (OUT.parent/f'{OUT.stem}.phase_status_diagnostic.json').write_text(json.dumps(diagnostic,indent=2,sort_keys=True)+'\n')
            raise RuntimeError(f'cap or unrecognized rule-report status in {run_phase}: {status_summary}')
    return {'seed':SEED,'scope':'root_scoped' if scoped else 'global','n_side':4,'units_per_root':[16,16],
        'topology':topology,'development_start_steps':dev_start,'development_end_steps':dev_end,'development_requested_steps':[3000,3000],
        'development_seconds':dev_seconds,'adaptation_seconds':adapt_seconds,'calibration_gains':{'A':gainA.tolist(),'B':gainB.tolist()},
        'retinal_channel_activity_after_adaptation':channel_activity,'batch_writer_scalar_equivalence':batch_writer_equal,
        'prepared_graph_sha256':prepared_sha,'contexts':contexts,'adaptation_report_counts':dict(Counter(x['final_status'] for x in presentation_summaries if x['phase']=='adaptation')),
        'adaptation_budget_retries':sum(x['intermediate_budget_hits'] for x in presentation_summaries if x['phase']=='adaptation'),
        'maximum_cumulative_progress_per_presentation':max((x['cumulative_progress'] for x in presentation_summaries),default=0),
        'presentation_work':presentation_summaries}

def worker():
    started=source_inputs();scopes=[];log=OUT.parent/f'{OUT.stem}.worker.log';OUT.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w') as fh,contextlib.redirect_stdout(fh):
        for scoped in (False,True):
            print(f'SCOPE START scope={scoped}',flush=True)
            result=one_scope(scoped);scopes.append(result)
            print(f'SCOPE DONE scope={result["scope"]}',flush=True)
            OUT.with_suffix('.partial.json').write_text(json.dumps({'completed_scopes':scopes},indent=2,sort_keys=True)+'\n')
    return {'pid':os.getpid(),'started_inputs':started,'finished_inputs':source_inputs(),'scopes':scopes}

def main():
    if sys.argv[1:]==['--lock']:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
    if len(sys.argv)==2 and sys.argv[1]=='--worker': print(json.dumps(worker(),sort_keys=True));return
    locked=source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing or stale source lock')
    env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
    proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True)
    if proc.returncode:
        (OUT.parent/f'{OUT.stem}.worker.stderr.log').write_text(proc.stderr)
        raise SystemExit(f'worker exited {proc.returncode}; see {OUT.parent / (OUT.stem + ".worker.stderr.log")}')
    run=json.loads(proc.stdout);post=source_inputs()
    scopes=run['scopes'];by={(x['scope'],c['context']):dict(x,**c) for x in scopes for c in x['contexts']}
    def maxdelta(x,y):return float(np.max(np.abs(np.asarray(x['tuning'])-np.asarray(y['tuning']))))
    from domains.complex_cells import binarize,grating
    expected_b_pixels=int(np.count_nonzero(binarize(grating((16,16),0.0,0.0,4.0))))
    scope_deltas={'global':maxdelta(by[('global','blank')],by[('global','grating')]),'root_scoped':maxdelta(by[('root_scoped','blank')],by[('root_scoped','grating')])}
    checks={'source_stable':post==locked==run['started_inputs']==run['finished_inputs'],
        'native_source_matches':locked['engine_provenance'].get('source_match') in ('own','shared') and not locked['engine_provenance'].get('stale_rust'),
        'two_scopes_complete':len(scopes)==2 and set(x['scope'] for x in scopes)=={'global','root_scoped'},
        'contexts_and_replay_complete':set(by)=={(s,c) for s in ('global','root_scoped') for c in ('blank','blank_replay','grating')} and all(by[(s,'blank')]['tuning']==by[(s,'blank_replay')]['tuning'] for s in ('global','root_scoped')),
        'topology_tags_and_singletons':all(x['units_per_root']==[16,16] and x['topology']['root_membership_counts']==[16,16] and len(set(x['topology']['retina_ids']))==2 and all(v==1 for v in x['topology']['singleton_counts'].values()) and all(v>0 for v in x['topology']['manifest_tag_counts'].values()) and all(v=='hard_realtime' for v in x['topology']['selected_rule_latency_classes'].values()) for x in scopes),
        'development_clocks_exact':all(x['development_start_steps']==[0.0,0.0] and x['development_end_steps']==[3000.0,3000.0] and x['development_requested_steps']==[3000,3000] for x in scopes),
        'batch_equivalence_and_calibration':all(x['batch_writer_scalar_equivalence'] and min(x['retinal_channel_activity_after_adaptation'].values())>0 and min(np.max(np.abs(np.asarray(v))) for v in x['calibration_gains'].values())>0.01 for x in scopes),
        'all_presentations_settled_within_cumulative_bound':all(x['adaptation_report_counts'] and all(set(c['final_presentation_status_counts'])<={'fixed_point','repeated_graph_state'} and sum(c['final_presentation_status_counts'].values())>0 for c in x['contexts']) and x['maximum_cumulative_progress_per_presentation']<=MAX_CUMULATIVE_PROGRESS_PER_PRESENTATION for x in scopes),
        'finite_nonzero_A_response':all(np.isfinite(np.asarray(x['tuning'])).all() and np.max(np.asarray(x['tuning']))>0 for x in by.values()),
        'readout_weights_unchanged':all(x['readout_weight_max_abs_delta']==0.0 and x['readout_weight_before']==x['readout_weight_after'] for x in by.values()),
        'b_context_stimulus_applied':all(by[(s,'blank')]['b_frame_active_pixels']==0 and by[(s,'grating')]['b_frame_active_pixels']==expected_b_pixels and by[(s,'grating')]['b_bursting_after_readout']==expected_b_pixels for s in ('global','root_scoped'))}
    payload={'schema_version':1,'run_id':'vision-shared-substrate-multisheet-task-pilot-v1.3-20260927','locked_inputs':locked,'post_run_inputs':post,
        'worker':run,'scope_deltas':scope_deltas,'checks':checks,'pass':all(checks.values()),
        'claim_boundary':'One-seed feasibility pilot for two full visual sheets sharing one substrate. Task contrast is whether B input changes A K=16 tuning under global versus root-scoped settling. Does not establish prevalence or cost.'}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'scope_deltas':scope_deltas},indent=2))
    if not payload['pass']:raise SystemExit('shared-substrate multi-sheet pilot failed its fixture/provenance gates')

if __name__=='__main__':main()
