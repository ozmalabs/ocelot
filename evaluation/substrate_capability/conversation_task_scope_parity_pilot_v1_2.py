#!/usr/bin/env python3
"""Exploratory parity pilot: sweep current Microtheory scopes over conversation tasks."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
PANEL=ROOT/'evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_2.py'
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_2_lock_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_parity_pilot_v1_2_20261003.json'
RUST=('rewrite.rs','substrate.rs','graph.rs','access_trace.rs','py.rs')
CASES=(('common_ground_stress',None),('concurrent_goals',2),('concurrent_goals',4),('concurrent_goals',8))
CAP=100_000
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def locked_inputs():
    from substrate_rs import _native
    return {'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'panel_runner_sha256':sha(PANEL),
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
def worker(replicate):
    from substrate_rs import NodeID
    panel=load_panel();baseline_settle=panel.settle_checkpoint
    mode={'name':'monolithic'};world_meta={};cases=[]
    def settle(adapter,event_id,event_index,event_frame,goal_frame,goals,trace_enabled):
        inner=adapter.inner;key=id(inner)
        if key not in world_meta:
            world_meta[key]={'roots':{},'linked':set()}
        meta=world_meta[key]
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
        frames=active_frames
        for node,frame in list(event_frame.items())+list(goal_frame.items()):
            if node not in meta['linked']:
                inner.add_edge_unchecked(meta['roots'][frame],'has_concept',NodeID(node),{})
                meta['linked'].add(node)
        if mode['name']=='monolithic':
            return baseline_settle(adapter,event_id,event_index,event_frame,goal_frame,goals,False)
        # Exhaustively resweep every scope until a complete round makes no
        # progress; this supplies conservative notification delivery across
        # all task frames, including shared-state dependencies.
        start=time.perf_counter_ns();rounds=0;calls=0
        inner.scale_audit_reset();inner.scale_audit_per_rule_reset()
        inner.scale_audit_set_enabled(True);inner.scale_audit_set_per_rule_enabled(True)
        while True:
            rounds+=1;progress=False
            if rounds>100: raise RuntimeError('partition sweep cap reached')
            for frame in frames:
                steps=int(inner.run_rules_scoped(CAP,False,meta['roots'][frame]));calls+=1
                progress |= steps>0
            if not progress: break
        # At the global sweep fixed point, check each scope's deferred queues.
        quiescence=[]
        for frame in frames:
            report=dict(inner.run_rules_scoped_delta_report(meta['roots'][frame],CAP,False));calls+=1
            if report.get('progress_steps',0): raise RuntimeError('scope changed during quiescence check')
            if report.get('deferred_effects_pending'): raise RuntimeError('deferred effects remain pending')
            quiescence.append({'frame':frame,'progress_steps':int(report.get('progress_steps',0)),
              'deferred_effects_pending':bool(report.get('deferred_effects_pending')),
              'frame_notifications_complete':bool(report.get('frame_notifications_complete',False))})
        inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_set_enabled(False)
        graph=inner.graph_to_dict()
        return {'event_id':event_id,'event_index':event_index,'closure':{'status':'fixed_point','sweeps':rounds},
          'wall_ns':time.perf_counter_ns()-start,'graph_digest':panel.digest(graph),'nodes':len(graph['nodes']),
          'edges':len(graph['edges']),'candidate_pairs':0,'term_evaluations':0,
          'goal_statuses':[adapter.s.node(g)['attrs'].get('lifecycle_status') for g in goals],
          'runtime_access_trace':[],'trace_dropped':0,'scoped_calls':calls,'scope_frame_ids':frames,
          'scope_quiescence':quiescence}
    panel.settle_checkpoint=settle
    for case_id,n in CASES:
        mode['name']='monolithic';world_meta.clear();mono=panel.run_case(case_id,replicate,n,False)
        mode['name']='partition_sweep';world_meta.clear();part=panel.run_case(case_id,replicate,n,False)
        cases.append({'case_id':case_id,'requested_goal_count':n,'monolithic':mono,'partition_sweep':part,
          'paired':{'final_graph_equal':mono['final_graph_digest']==part['final_graph_digest'],
            'checkpoint_graph_equal':[x['graph_digest']==y['graph_digest'] for x,y in zip(mono['checkpoints'],part['checkpoints'])],
            'goal_status_equal':[x['status'] for x in mono['goals']]==[x['status'] for x in part['goals']],
            'partition_scoped_calls':sum(x.get('scoped_calls',0) for x in part['checkpoints'])}})
    return {'replicate':replicate,'pid':os.getpid(),'cases':cases}
def main():
    if sys.argv[1:]==['--lock']:
        if OUT.exists(): raise SystemExit('refusing to overwrite capture')
        LOCK.write_text(json.dumps({'schema':'ConversationTaskScopeParityPilotV1_2Lock','locked_inputs':locked_inputs()},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return
    if len(sys.argv)==3 and sys.argv[1]=='--worker':
        print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
    locked=locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked: raise SystemExit('missing or stale source lock')
    env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
    env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
    started=time.perf_counter_ns();runs=[json.loads(subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300).stdout) for i in range(3)]
    post=locked_inputs();checks={'three_fresh_workers':len({r['pid'] for r in runs})==3,'source_stable':post==locked and all(len(r['cases'])==len(CASES) for r in runs),
      'twelve_paired_cases':sum(len(r['cases']) for r in runs)==12,
      'all_final_states_equal':all(c['paired']['final_graph_equal'] for r in runs for c in r['cases']),
      'all_checkpoint_states_equal':all(all(c['paired']['checkpoint_graph_equal']) for r in runs for c in r['cases']),
      'goal_status_equal':all(c['paired']['goal_status_equal'] for r in runs for c in r['cases'])}
    payload={'schema':'ConversationTaskScopeParityPilotV1_2','locked_inputs':locked,'post_run_inputs':post,
      'claim_boundary':'Exploratory exact-state comparison of full closure with globally reswept task-specific Microtheory scopes on authored two-, three-, four-, and eight-frame conversation cases. Scope nodes and ownership edges are added as measurement annotations in both arms. This does not isolate or prove computational factorization, general scope correctness, speedup, or natural-task prevalence.',
      'configuration':{'replicates':3,'cases':CASES,'partition_policy':'resweep all discovered scopes until a complete round reports zero progress; require each scoped deferred queue empty'},
      'timing':{'wall_ns':time.perf_counter_ns()-started},'runs':runs,'checks':checks}
    if OUT.exists(): raise SystemExit('refusing to overwrite capture')
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks},indent=2))
    if not all(checks.values()): raise SystemExit('pilot gates failed')
if __name__=='__main__':main()
