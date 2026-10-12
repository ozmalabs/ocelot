#!/usr/bin/env python3
"""Exploratory parity pilot: sweep current Microtheory scopes over conversation tasks."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
PANEL=ROOT/'evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_conversation_task_scope_anchor_pilot_v2_0.py'
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_anchor_pilot_v2_0_2_lock_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_anchor_pilot_v2_0_2_20261003.json'
RUST=('rewrite.rs','substrate.rs','graph.rs','access_trace.rs','term.rs','py.rs','scale_audit.rs','graph_rules.rs')
CASES=(('common_ground_stress',None),('concurrent_goals',2),('concurrent_goals',4),('concurrent_goals',8))
ORDER_POLICIES=('ascending','descending','outside_in')
CAP=100_000
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_TASK_SCOPE_DECLARED_ANCHOR_V2_PREREG_20261003.md'
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
def run_configured_case(panel,case_id,replicate,n,arm,ownership_variant,mode,world_meta):
    from substrate import seed_loader
    previous_manifest_for=seed_loader.manifest_for
    def manifest_for(seed_id):
        manifest=previous_manifest_for(seed_id)
        if seed_id=='conversation_discourse_state' and arm=='partition_fallback':
            manifest=copy.deepcopy(manifest)
            for rule in manifest.get('rules',[]):
                for field in ANCHOR_FIELDS: rule.pop(field,None)
        return manifest
    seed_loader.manifest_for=manifest_for
    try:
        mode.update({'name':arm,'ownership_variant':ownership_variant,'owner_variant_applied':False,'orphan_goal_id':None})
        world_meta.clear()
        return panel.run_case(case_id,replicate,n,False)
    finally:
        seed_loader.manifest_for=previous_manifest_for
def worker(replicate):
    from substrate_rs import NodeID
    panel=load_panel();baseline_settle=panel.settle_checkpoint
    order_id=replicate%len(ORDER_POLICIES);order_policy=ORDER_POLICIES[order_id]
    replicate_id=replicate//len(ORDER_POLICIES)
    mode={'name':'monolithic','ownership_variant':'aligned','owner_variant_applied':False};world_meta={};cases=[]
    def settle(adapter,event_id,event_index,event_frame,goal_frame,goals,trace_enabled):
        inner=adapter.inner;key=id(inner)
        if key not in world_meta:
            world_meta[key]={'roots':{},'linked':set()}
        meta=world_meta[key]
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
    conditions=[(case_id,n,'aligned') for case_id,n in CASES]
    conditions.extend(('concurrent_goals',2,control) for control in ('cross_frame','orphan_goal'))
    for case_id,n,ownership_variant in conditions:
        mono=run_configured_case(panel,case_id,replicate,n,'monolithic',ownership_variant,mode,world_meta)
        fallback=run_configured_case(panel,case_id,replicate,n,'partition_fallback',ownership_variant,mode,world_meta)
        anchor=run_configured_case(panel,case_id,replicate,n,'partition_anchor',ownership_variant,mode,world_meta)
        traced=run_configured_case(panel,case_id,replicate,n,'partition_anchor_trace',ownership_variant,mode,world_meta)
        fallback_checkpoint_equal=[x['graph_digest']==y['graph_digest'] for x,y in zip(mono['checkpoints'],fallback['checkpoints'])]
        anchor_checkpoint_equal=[x['graph_digest']==y['graph_digest'] for x,y in zip(mono['checkpoints'],anchor['checkpoints'])]
        trace_checkpoint_equal=[x['graph_digest']==y['graph_digest'] for x,y in zip(anchor['checkpoints'],traced['checkpoints'])]
        cases.append({'case_id':case_id,'requested_goal_count':n,'ownership_variant':ownership_variant,
          'monolithic':mono,'partition_fallback':fallback,'partition_anchor':anchor,'partition_anchor_trace':traced,
          'paired':{'fallback_final_equal':mono['final_graph_digest']==fallback['final_graph_digest'],
            'fallback_checkpoint_equal':fallback_checkpoint_equal,
            'anchor_final_equal':mono['final_graph_digest']==anchor['final_graph_digest'],
            'anchor_checkpoint_equal':anchor_checkpoint_equal,
            'goal_status_equal':([x['status'] for x in mono['goals']]==[x['status'] for x in fallback['goals']]==[x['status'] for x in anchor['goals']]),
            'trace_arm_final_equal':anchor['final_graph_digest']==traced['final_graph_digest'],
            'trace_arm_checkpoint_equal':trace_checkpoint_equal,
            'fallback_scoped_calls':sum(x.get('scoped_calls',0) for x in fallback['checkpoints']),
            'anchor_scoped_calls':sum(x.get('scoped_calls',0) for x in anchor['checkpoints'])}})
    return {'worker_index':replicate,'replicate':replicate_id,'scope_order_policy':order_policy,'pid':os.getpid(),'cases':cases}
def main():
    if sys.argv[1:]==['--lock']:
        if OUT.exists(): raise SystemExit('refusing to overwrite capture')
        LOCK.write_text(json.dumps({'schema':'ConversationTaskScopeAnchorPilotV2_0Lock','locked_inputs':locked_inputs()},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return
    if len(sys.argv)==3 and sys.argv[1]=='--worker':
        print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
    locked=locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked: raise SystemExit('missing or stale source lock')
    env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
    env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
    started=time.perf_counter_ns();runs=[json.loads(subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300).stdout) for i in range(9)]
    all_cases=[c for r in runs for c in r['cases']]
    aligned=[c for c in all_cases if c['ownership_variant']=='aligned']
    controls=[c for c in all_cases if c['ownership_variant']!='aligned']
    post=locked_inputs();checks={'nine_fresh_workers':len({r['pid'] for r in runs})==9,'source_stable':post==locked and all(len(r['cases'])==6 for r in runs),
      'fifty_four_paired_cases':len(all_cases)==54,
      'fallback_exact_states':all(c['paired']['fallback_final_equal'] and all(c['paired']['fallback_checkpoint_equal']) for c in all_cases),
      'anchor_exact_states':all(c['paired']['anchor_final_equal'] and all(c['paired']['anchor_checkpoint_equal']) for c in all_cases),
      'goal_status_equal':all(c['paired']['goal_status_equal'] for c in all_cases),
      'trace_on_off_anchor_parity':all(c['paired']['trace_arm_final_equal'] and all(c['paired']['trace_arm_checkpoint_equal']) for c in all_cases),
      'anchor_path_exercised_on_aligned_cases':all(sum(cp['scale_counters'].get('scoped_declared_anchor_rule_matches',0) for cp in c['partition_anchor']['checkpoints'])>0 for c in aligned),
      'unsafe_ownership_guard_rejected':all(sum(cp['scale_counters'].get('scoped_anchor_rejected_rule_matches',0) for cp in c['partition_anchor']['checkpoints'])>0 for c in controls),
      'trace_nonempty_no_drops':all(any(cp['runtime_access_trace_events'] for cp in c['partition_anchor_trace']['checkpoints']) and all(cp['trace_dropped']==0 for cp in c['partition_anchor_trace']['checkpoints']) for c in all_cases)}
    payload={'schema':'ConversationTaskScopeAnchorPilotV2_0_2','locked_inputs':locked,'post_run_inputs':post,
      'claim_boundary':'Source-locked comparison of full scoped fallback and declared-anchor matching on aligned, cross-frame, and orphan-owner authored conversation cases. This measures state parity, native candidate/Term work, and candidate expansion counts by semantic match edge; it does not prove general scope correctness, natural-task prevalence, computational factorization, or speedup.',
      'configuration':{'replicates_per_scope_order':3,'scope_order_policies':ORDER_POLICIES,'base_cases':CASES,'ownership_controls':['cross_frame','orphan_goal'],'partition_policy':'resweep every scope in the locked order until a complete round reports zero progress; require each scoped deferred queue empty','scope_ownership':'Goals and Events with a for_goal edge; unrelated events remain shared/unowned'},
      'timing':{'wall_ns':time.perf_counter_ns()-started},'runs':runs,'checks':checks}
    if OUT.exists(): raise SystemExit('refusing to overwrite capture')
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
    if not all(checks.values()): raise SystemExit('pilot gates failed')
if __name__=='__main__':main()
