#!/usr/bin/env python3
"""Independent integrity and scaling analysis for size/memory v1."""
import hashlib, json, statistics
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_size_memory_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/conversation_task_scope_size_memory_v1_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_size_memory_v1_analysis_20261003.json'
COUNTS=(0,256,1024,4096,16384)
POLICIES=('ascending','descending','outside_in')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def median(xs): return statistics.median(xs) if xs else None
def main():
    errors=[]
    def req(ok,msg):
        if not ok: errors.append(msg)
    lock=json.loads(LOCK.read_text())['locked_inputs']; cap=json.loads(CAP.read_text())
    req(cap.get('locked_inputs')==lock==cap.get('post_run_inputs'),'source lock drift')
    runs=cap.get('runs',[]); req(len(runs)==45,'expected 45 workers')
    req(len({r.get('pid') for r in runs})==45,'worker PIDs not unique')
    req(cap.get('checks',{}).get('source_stable') is True,'runner source-stability check failed')
    summaries={}; rows=[]
    for i,run in enumerate(runs):
        dose=COUNTS[i//9]; local=i%9; policy=POLICIES[local%3]; rep=local//3
        req(run.get('worker_index')==i and run.get('decoy_count')==dose,'size/worker assignment mismatch')
        req(run.get('scope_order_policy')==policy and run.get('replicate')==rep,'order/replicate assignment mismatch')
        req(len(run.get('cases',[]))==1,'worker must run exactly one size cell')
        if not run.get('cases'): continue
        case=run['cases'][0]; req(case.get('decoy_count')==dose and case.get('decoy_profile')=='shared_event_complete','decoy workload mismatch')
        mono=case['monolithic']; fallback=case['partition_fallback']; anchor=case['partition_anchor']; traced=case['partition_anchor_trace']
        for name,arm in [('fallback',fallback),('anchor',anchor),('trace',traced)]:
            req(len(arm['checkpoints'])==len(mono['checkpoints']),f'{name} checkpoint mismatch')
            req(all(cp.get('closure',{}).get('status')=='fixed_point' for cp in arm['checkpoints']),f'{name} non-fixed-point result')
            req(all(not cp.get('deferred_effects_pending',False) for cp in arm['checkpoints']),f'{name} deferred effects pending')
        for name,arm in [('fallback',fallback),('anchor',anchor),('trace',traced)]:
            eq=[x.get('graph_digest')==y.get('graph_digest') for x,y in zip(mono['checkpoints'],arm['checkpoints'])]
            req(all(eq) and mono.get('final_graph_digest')==arm.get('final_graph_digest'),f'{name} state mismatch')
        trace_eq=[x.get('graph_digest')==y.get('graph_digest') for x,y in zip(anchor['checkpoints'],traced['checkpoints'])]
        req(all(trace_eq) and anchor.get('final_graph_digest')==traced.get('final_graph_digest'),'trace parity failure')
        req([g.get('status') for g in mono.get('goals',[])]==[g.get('status') for g in anchor.get('goals',[])],'lifecycle mismatch')
        for cp in fallback['checkpoints']:
            c=cp.get('scale_counters',{})
            req(c.get('scoped_declared_anchor_rule_matches',0)==0 and c.get('scoped_anchor_rejected_rule_matches',0)==0,'fallback used anchor metadata')
            req(c.get('scoped_full_fallback_rule_matches',0)>0,'fallback did not use full matcher')
        req(sum(cp.get('scale_counters',{}).get('scoped_declared_anchor_rule_matches',0) for cp in anchor['checkpoints'])>0,'anchor path not exercised')
        def arm_stats(a):
            cps=a['checkpoints']
            return {'nodes_peak':max((int(x.get('nodes',0)) for x in cps),default=0),'edges_peak':max((int(x.get('edges',0)) for x in cps),default=0),
              'candidate_pairs':sum(int(x.get('candidate_pairs',0)) for x in cps),'term_evaluations':sum(int(x.get('term_evaluations',0)) for x in cps),
              'wall_ns':sum(int(x.get('wall_ns',0)) for x in cps)}
        row={'worker_index':i,'decoy_count':dose,'scope_order_policy':policy,'replicate':rep,'peak_rss_kb':int(run.get('peak_rss_kb',0)),
          'checkpoint_count':len(mono['checkpoints']),'arms':{n:arm_stats(a) for n,a in [('monolithic',mono),('fallback',fallback),('anchor',anchor),('trace',traced)]}}
        rows.append(row)
    req(len(rows)==45,'independent row count mismatch')
    bydose={}
    for dose in COUNTS:
        group=[r for r in rows if r['decoy_count']==dose]
        req(len(group)==9,f'expected nine replicates at dose {dose}')
        if not group: continue
        agg={arm:{metric:sum(r['arms'][arm][metric] for r in group) for metric in ('candidate_pairs','term_evaluations','wall_ns')} for arm in ('monolithic','fallback','anchor','trace')}
        agg['graph']={'median_peak_nodes':median([r['arms']['anchor']['nodes_peak'] for r in group]),'median_peak_edges':median([r['arms']['anchor']['edges_peak'] for r in group])}
        agg['process_memory']={'median_peak_rss_kb':median([r['peak_rss_kb'] for r in group]),'min_peak_rss_kb':min(r['peak_rss_kb'] for r in group),'max_peak_rss_kb':max(r['peak_rss_kb'] for r in group)}
        for metric in ('candidate_pairs','term_evaluations','wall_ns'):
            agg[f'anchor_{metric}_ratio_vs_monolithic']=agg['anchor'][metric]/agg['monolithic'][metric] if agg['monolithic'][metric] else None
            agg[f'anchor_{metric}_ratio_vs_fallback']=agg['anchor'][metric]/agg['fallback'][metric] if agg['fallback'][metric] else None
        bydose[str(dose)]=agg
    req(cap.get('checks',{}).get('forty_five_fresh_workers') is True,'runner worker gate failed')
    req(cap.get('checks',{}).get('fallback_exact_states') is True and cap.get('checks',{}).get('anchor_exact_states') is True,'runner parity gate failed')
    req(cap.get('checks',{}).get('trace_on_off_anchor_parity') is True,'runner trace parity gate failed')
    out={'schema':'ConversationTaskScopeSizeMemoryV1Analysis','gates_pass':not errors,'errors':errors,'workers':rows,'by_decoy_count':bydose,
      'peak_memory_warning':'ru_maxrss is the worker process high-water RSS, including interpreter, fixture setup, all arms, retained checkpoint payload, and trace instrumentation; it is not an isolated per-arm allocation measurement.',
      'timing_warning':'Arm wall times sum closure checkpoint timings from the capture. Treat them as descriptive; traced arm is excluded from primary timing interpretation.',
      'claim_boundary':cap.get('claim_boundary'),'analysis_script_sha256':sha(__file__)}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'gates_pass':out['gates_pass'],'errors':errors,'by_decoy_count':bydose},indent=2))
    return int(bool(errors))
if __name__=='__main__': raise SystemExit(main())
