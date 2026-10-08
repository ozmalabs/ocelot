#!/usr/bin/env python3
"""Memory-isolated size scaling with compact arm summaries and no trace instrumentation."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
PANEL=ROOT/'evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_conversation_task_scope_size_memory_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_size_memory_v1_1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_size_memory_v1_1_20261003.json'
RUST=('rewrite.rs','substrate.rs','graph.rs','access_trace.rs','term.rs','py.rs','scale_audit.rs','graph_rules.rs')
CASES=(('common_ground_stress',None),('concurrent_goals',2),('concurrent_goals',4),('concurrent_goals',8))
ORDER_POLICIES=('ascending','descending','outside_in')
CAP=100_000
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_TASK_SCOPE_SIZE_MEMORY_V1_1_AMENDMENT_20261003.md'
ANCHOR_FIELDS=('scope_anchor_var','scope_anchor_type','scope_anchor_owner_var','scope_anchor_owner_type','scope_anchor_owner_edge')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def locked_inputs():
    from substrate_rs import _native
    return {'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'panel_runner_sha256':sha(PANEL),'preregistration_sha256':sha(PREREG),
      'discourse_materializer_sha256':sha(ROOT/'domains/discourse_state.py'),
      'rule_seed_sha256':sha(ROOT/'seeds/conversation_discourse_state.json'),
      'stress_fixture_sha256':sha(ROOT/'tests/fixtures/conversational_manifold/phase3_common_ground_stress.json'),
      'scale_fixture_sha256':sha(ROOT/'tests/fixtures/conversational_manifold/phase3_same_addressee_concurrent_goals_scale.json'),
      'native_extension_sha256':sha(Path(_native.__file__).resolve()),
      'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
      'rust_sources_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in RUST},
      'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def load_panel():
    spec=importlib.util.spec_from_file_location('conversation_trace_panel',PANEL)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def frame_order(frames,policy):
    if policy=='ascending':return list(frames)
    if policy=='descending':return list(reversed(frames))
    out=[];lo=0;hi=len(frames)-1
    while lo<=hi:
        out.append(frames[lo]);lo+=1
        if lo<=hi:out.append(frames[hi]);hi-=1
    return out
def run_configured_case(panel,case_id,replicate,n,arm,ownership_variant,decoy_count,decoy_profile,mode,world_meta):
    from substrate import boot_core, seed_loader
    previous_manifest_for=seed_loader.manifest_for
    previous_boot_manifest_for=boot_core.manifest_for
    def manifest_for(seed_id):
        manifest=previous_manifest_for(seed_id)
        if seed_id=='conversation_discourse_state' and arm=='partition_fallback':
            manifest=copy.deepcopy(manifest)
            for rule in manifest.get('rules',[]):
                for field in ANCHOR_FIELDS: rule.pop(field,None)
        return manifest
    seed_loader.manifest_for=manifest_for
    # load_seeds_into retains a module-level import, so patch that lookup too.
    boot_core.manifest_for=manifest_for
    try:
        mode.update({'name':arm,'ownership_variant':ownership_variant,'owner_variant_applied':False,'orphan_goal_id':None,'decoy_count':decoy_count,'decoy_profile':decoy_profile})
        world_meta.clear()
        return panel.run_case(case_id,replicate,n,False)
    finally:
        seed_loader.manifest_for=previous_manifest_for
        boot_core.manifest_for=previous_boot_manifest_for
def worker(replicate,decoy_count):
    from substrate_rs import NodeID
    panel=load_panel();baseline_settle=panel.settle_checkpoint
    order_id=replicate%len(ORDER_POLICIES);order_policy=ORDER_POLICIES[order_id]
    replicate_id=replicate//len(ORDER_POLICIES)
    mode={'name':'monolithic','ownership_variant':'aligned','owner_variant_applied':False,'decoy_count':0,'decoy_profile':'none'};world_meta={};cases=[]
    def settle(adapter,event_id,event_index,event_frame,goal_frame,goals,trace_enabled):
        inner=adapter.inner;key=id(inner)
        if key not in world_meta:
            world_meta[key]={'roots':{},'linked':set(),'decoys_inserted':False}
        meta=world_meta[key]
        if not meta['decoys_inserted']:
            decoy_count=int(mode.get('decoy_count',0))
            if decoy_count:
                before=inner.graph_to_dict()
                states=[int(node['id']) for node in before['nodes'] if node['type']=='DiscourseState']
                if len(states)!=1: raise RuntimeError(f'expected one discourse state, got {len(states)}')
                state=NodeID(states[0])
                profile=str(mode.get('decoy_profile','isolated_complete'))
                shared_event=None
                if profile=='shared_event_complete':
                    shared_event=inner.add_node('Event',{'kind':'decoy','event_index':-1})
                    inner.add_edge_unchecked(state,'has_event',shared_event,{})
                omitted={
                    'missing_has_active_goal':'has_active_goal',
                    'missing_originated_in':'originated_in',
                    'missing_has_event':'has_event',
                    'missing_for_goal':'for_goal',
                }.get(profile)
                if profile not in ('isolated_complete','shared_event_complete') and omitted is None:
                    raise ValueError(f'unknown decoy profile {profile}')
                for i in range(decoy_count):
                    goal=inner.add_node('Goal',{'schema':'communicative_goal_v1','kind':'decoy','status':'decoy_ineligible','lifecycle_status':'decoy_ineligible','outcome':None})
                    event=shared_event or inner.add_node('Event',{'kind':'decoy','event_index':-i-1})
                    edges=(('has_active_goal',state,goal),('originated_in',goal,event),('has_event',state,event),('for_goal',event,goal))
                    for relation,src,tgt in edges:
                        if relation==omitted:
                            continue
                        if profile=='shared_event_complete' and relation=='has_event':
                            continue
                        inner.add_edge_unchecked(src,relation,tgt,{})
            meta['decoys_inserted']=True
        if not mode['owner_variant_applied'] and mode['ownership_variant']!='aligned' and goals:
            first_goal=panel.nid(goals[0])
            if mode['ownership_variant']=='cross_frame':
                goal_frame[first_goal]=1
            elif mode['ownership_variant']=='orphan_goal':
                mode['orphan_goal_id']=first_goal
            else:
                raise ValueError(f"unknown ownership control {mode['ownership_variant']}")
            mode['owner_variant_applied']=True
        active_frames=sorted(set(event_frame.values())|set(goal_frame.values()))
        if not active_frames or active_frames!=list(range(max(active_frames)+1)):
            raise RuntimeError(f'non-contiguous task frames {active_frames}')
        # Add task-scoped roots as ordinary graph nodes, then mark task-local
        # events/goals as members. The checked vocabulary does not currently
        # admit these typed ownership edges, so the measurement annotation is
        # inserted unchecked in both arms.
        for frame in active_frames:
            if frame not in meta['roots']:
                meta['roots'][frame]=inner.add_node('Microtheory',{'name':f'pilot_task_frame_{frame}'})
        frames=active_frames;scope_order=frame_order(frames,order_policy)
        graph_before_ownership=inner.graph_to_dict()
        linked_events={int(edge['src']) for edge in graph_before_ownership['edges'] if edge['type']=='for_goal'}
        owned_events=[(node,frame) for node,frame in event_frame.items() if node in linked_events]
        owned_goals=[(node,frame) for node,frame in goal_frame.items() if node!=mode.get('orphan_goal_id')]
        for node,frame in owned_events+owned_goals:
            if node not in meta['linked']:
                inner.add_edge_unchecked(meta['roots'][frame],'has_concept',NodeID(node),{})
                meta['linked'].add(node)
        if mode['name']=='monolithic':
            return baseline_settle(adapter,event_id,event_index,event_frame,goal_frame,goals,False)
        # Exhaustively resweep every scope until a complete round makes no
        # progress; this supplies conservative notification delivery across
        # all task frames, including shared-state dependencies.
        trace_enabled=mode['name']=='partition_anchor_trace'
        inner.runtime_access_trace_reset();inner.runtime_access_trace_set_enabled(trace_enabled)
        start=time.perf_counter_ns();rounds=0;calls=0
        inner.scale_audit_reset();inner.scale_audit_per_rule_reset()
        inner.scale_audit_set_enabled(True);inner.scale_audit_set_per_rule_enabled(True)
        while True:
            rounds+=1;progress=False
            if rounds>100: raise RuntimeError('partition sweep cap reached')
            for frame in scope_order:
                steps=int(inner.run_rules_scoped(CAP,False,meta['roots'][frame]));calls+=1
                progress |= steps>0
            if not progress: break
        # At the global sweep fixed point, check each scope's deferred queues.
        quiescence=[]
        for frame in scope_order:
            report=dict(inner.run_rules_scoped_delta_report(meta['roots'][frame],CAP,False));calls+=1
            if report.get('progress_steps',0): raise RuntimeError('scope changed during quiescence check')
            if report.get('deferred_effects_pending'): raise RuntimeError('deferred effects remain pending')
            quiescence.append({'frame':frame,'progress_steps':int(report.get('progress_steps',0)),
              'deferred_effects_pending':bool(report.get('deferred_effects_pending')),
              'frame_notifications_complete':bool(report.get('frame_notifications_complete',False))})
        inner.runtime_access_trace_set_enabled(False)
        trace_rows,trace_dropped=inner.runtime_access_trace_snapshot()
        counters={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()}
        rule_names_by_index={int(index):str(name) for index,name,*_rest in inner.rule_access_sets()}
        per_rule=[{'rule_index':int(i),'metric':str(metric),'count':int(count),'rule_name':rule_names_by_index.get(int(i),'unknown')} for i,metric,count in inner.scale_audit_per_rule_snapshot()]
        match_edges=[{'rule_index':int(i),'rule_name':rule_names_by_index.get(int(i),'unknown'),
          'src_var':str(src),'edge_type':str(edge),'tgt_var':str(tgt),
          'expansion_calls':int(calls),'candidate_pairs':int(candidates)}
          for i,src,edge,tgt,calls,candidates in inner.scale_audit_match_edge_snapshot()]
        inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_set_enabled(False)
        rule_names={}
        for index,name,*_rest in inner.rule_access_sets():
            metadata=inner.rule_metadata(index);rule_names[int(metadata['rule_uid'])]=str(name)
        trace=[[int(x[0]),str(x[1]),x[2],x[3],x[4],int(x[5])] for x in trace_rows]
        graph=inner.graph_to_dict()
        return {'event_id':event_id,'event_index':event_index,'closure':{'status':'fixed_point','sweeps':rounds},
          'wall_ns':time.perf_counter_ns()-start,'scale_counters_by_rule':per_rule,'graph_digest':panel.digest(graph),'nodes':len(graph['nodes']),
          'edges':len(graph['edges']),'candidate_pairs':counters.get('cand_enum',0),
          'term_evaluations':counters.get('term_evals_total',0),'scale_counters':counters,
          'goal_statuses':[adapter.s.node(g)['attrs'].get('lifecycle_status') for g in goals],
          'candidate_expansions_by_match_edge':match_edges,
          'runtime_access_trace':trace,'trace_dropped':int(trace_dropped),'trace_rule_names':rule_names,
          'scoped_calls':calls,'scope_frame_ids':frames,'scope_sweep_order':scope_order,
          'scope_quiescence':quiescence}
    panel.settle_checkpoint=settle
    conditions=[('concurrent_goals',2,'aligned',int(decoy_count),'shared_event_complete')]
    def compact(arm):
        return {'final_graph_digest':arm['final_graph_digest'],'frame_count':arm.get('frame_count'),
          'goals':[{'status':g.get('status')} for g in arm.get('goals',[])],
          'checkpoints':[{'graph_digest':cp.get('graph_digest'),'closure':cp.get('closure'),
            'nodes':int(cp.get('nodes',0)),'edges':int(cp.get('edges',0)),
            'candidate_pairs':int(cp.get('candidate_pairs',0)),'term_evaluations':int(cp.get('term_evaluations',0)),
            'wall_ns':int(cp.get('wall_ns',0)),'scale_counters':cp.get('scale_counters',{})} for cp in arm.get('checkpoints',[])]}
    for case_id,n,ownership_variant,decoy_count,decoy_profile in conditions:
        mono_raw=run_configured_case(panel,case_id,replicate,n,'monolithic',ownership_variant,decoy_count,decoy_profile,mode,world_meta)
        mono=compact(mono_raw); del mono_raw
        fallback_raw=run_configured_case(panel,case_id,replicate,n,'partition_fallback',ownership_variant,decoy_count,decoy_profile,mode,world_meta)
        fallback=compact(fallback_raw); del fallback_raw
        anchor_raw=run_configured_case(panel,case_id,replicate,n,'partition_anchor',ownership_variant,decoy_count,decoy_profile,mode,world_meta)
        anchor=compact(anchor_raw); del anchor_raw
        fallback_checkpoint_equal=[x['graph_digest']==y['graph_digest'] for x,y in zip(mono['checkpoints'],fallback['checkpoints'])]
        anchor_checkpoint_equal=[x['graph_digest']==y['graph_digest'] for x,y in zip(mono['checkpoints'],anchor['checkpoints'])]
        cases.append({'case_id':case_id,'requested_goal_count':n,'ownership_variant':ownership_variant,'decoy_count':decoy_count,'decoy_profile':decoy_profile,
          'monolithic':mono,'partition_fallback':fallback,'partition_anchor':anchor,
          'paired':{'fallback_final_equal':mono['final_graph_digest']==fallback['final_graph_digest'],
            'fallback_checkpoint_equal':fallback_checkpoint_equal,
            'anchor_final_equal':mono['final_graph_digest']==anchor['final_graph_digest'],
            'anchor_checkpoint_equal':anchor_checkpoint_equal,
            'goal_status_equal':([x['status'] for x in mono['goals']]==[x['status'] for x in fallback['goals']]==[x['status'] for x in anchor['goals']]),
            'fallback_scoped_calls':sum(x.get('scoped_calls',0) for x in fallback.get('checkpoints',[])),
            'anchor_scoped_calls':sum(x.get('scoped_calls',0) for x in anchor.get('checkpoints',[]))}})
    import resource
    return {'worker_index':replicate,'replicate':replicate_id,'scope_order_policy':order_policy,'decoy_count':int(decoy_count),'pid':os.getpid(),'peak_rss_kb':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'cases':cases}

def main():
    if sys.argv[1:]==['--lock']:
        if OUT.exists() or OUT.with_suffix('.partial').exists(): raise SystemExit('refusing to overwrite capture')
        LOCK.write_text(json.dumps({'schema':'ConversationTaskScopeSizeMemoryV1_1Lock','locked_inputs':locked_inputs()},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return
    if len(sys.argv)==4 and sys.argv[1]=='--worker':
        print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3])),sort_keys=True,separators=(',',':')));return
    locked=locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked: raise SystemExit('missing or stale source lock')
    env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
    env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
    started=time.perf_counter_ns();decoy_counts=(0,256,1024,4096,16384);pids=[];worker_ok=True
    partial=OUT.with_suffix('.partial')
    with partial.open('w') as stream:
        stream.write(json.dumps({'schema':'ConversationTaskScopeSizeMemoryV1_1','locked_inputs':locked,'claim_boundary':'Fresh-process comparison of monolithic, verified fallback, and declared-anchor closure with tracing disabled and compact checkpoint summaries. Peak RSS is the maximum across three arms in one isolated worker; no natural-task prevalence or general tractability claim follows.','configuration':{'replicates_per_scope_order':3,'scope_order_policies':ORDER_POLICIES,'decoy_counts':list(decoy_counts),'case':['concurrent_goals',2],'decoy_profile':'shared_event_complete','trace_enabled':False}},separators=(',',':'))[:-1])
        stream.write(',"runs":[')
        first=True
        for size_index,decoy_count in enumerate(decoy_counts):
            for replicate in range(9):
                worker_index=size_index*9+replicate
                proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(worker_index),str(decoy_count)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600)
                run=json.loads(proc.stdout);pids.append(int(run['pid']))
                if len(run.get('cases',[]))!=1: worker_ok=False
                if not first: stream.write(',')
                stream.write(json.dumps(run,separators=(',',':')));first=False
                del run,proc
        post=locked_inputs()
        checks={'forty_five_fresh_workers':len(set(pids))==45,'source_stable':post==locked,'forty_five_cases':worker_ok and len(pids)==45}
        stream.write('],"post_run_inputs":'+json.dumps(post,separators=(',',':')))
        stream.write(',"checks":'+json.dumps(checks,separators=(',',':')))
        stream.write(',"timing":{"wall_ns":'+str(time.perf_counter_ns()-started)+'}}\n')
    if not all(checks.values()): raise SystemExit('pilot integrity gates failed; partial capture retained')
    partial.replace(OUT)
    print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
if __name__=='__main__':main()
