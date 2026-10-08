#!/usr/bin/env python3
"""Independent per-case audit of v2.4.1 dynamic cross-frame mutation controls."""
from __future__ import annotations
import gzip, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_degree_selectivity_v2_4_1_dynamic_lock_20261004.json'
CAP=ROOT/'evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_4_1_20261004.json.gz'
MAIN=ROOT/'evaluation/reports/conversation_task_scope_degree_selectivity_pilot_v2_4_1_analysis_20261004.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_degree_selectivity_v2_4_1_dynamic_analysis_20261004.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=json.loads(LOCK.read_text())
    with gzip.open(CAP,'rt',encoding='utf-8') as f: capture=json.load(f)
    analysis=json.loads(MAIN.read_text())
    errors=[]
    def req(ok,msg):
        if not ok: errors.append(msg)
    req(lock.get('capture_sha256')==sha(CAP),'capture hash differs from supplemental lock')
    req(lock.get('main_analysis_sha256')==sha(MAIN),'main analysis hash differs from supplemental lock')
    req(lock.get('protocol_sha256')==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_TASK_SCOPE_DEGREE_SELECTIVITY_V2_4_1_PREREG_20261004.md'),'protocol hash differs from supplemental lock')
    req(lock.get('analyzer_sha256')==sha(Path(__file__)),'supplemental analyzer hash differs from lock')
    req(capture.get('schema')=='ConversationTaskScopeDegreeSelectivityPilotV2_4_1','capture schema mismatch')
    req(capture.get('locked_inputs')==capture.get('post_run_inputs'),'source closure changed during capture')
    req(analysis.get('gates_pass') is True and not analysis.get('errors'),'main independent analysis failed')
    runs=capture.get('runs',[])
    req(len(runs)==9 and len({r.get('pid') for r in runs})==9,'worker independence mismatch')
    cases=[(r,c) for r in runs for c in r.get('cases',[]) if c.get('ownership_variant')=='cross_frame_mutation']
    req(len(cases)==9,'dynamic mutation case count mismatch')
    expected={'ascending':3,'descending':3,'outside_in':3}
    from collections import Counter
    req(Counter(r.get('scope_order_policy') for r,_ in cases)==expected,'scope-order replication mismatch')
    rows=[]
    for run,case in cases:
        anchor=case['partition_anchor'];fallback=case['partition_fallback'];paired=case['paired']
        rejected=sum(int(cp.get('scale_counters',{}).get('scoped_anchor_rejected_rule_matches',0)) for cp in anchor.get('checkpoints',[]))
        full_fallback=sum(int(cp.get('scale_counters',{}).get('scoped_full_fallback_rule_matches',0)) for cp in anchor.get('checkpoints',[]))
        after_mutation=[cp for cp in anchor.get('checkpoints',[]) if int(cp.get('event_index',-1))>=2]
        post_rejected=sum(int(cp.get('scale_counters',{}).get('scoped_anchor_rejected_rule_matches',0)) for cp in after_mutation)
        post_fallback=sum(int(cp.get('scale_counters',{}).get('scoped_full_fallback_rule_matches',0)) for cp in after_mutation)
        row={'worker_index':run['worker_index'],'scope_order_policy':run['scope_order_policy'],
             'edge_injected':case.get('dynamic_cross_frame_edge_injected') is True,
             'anchor_proof_rejections':rejected,'anchor_full_fallback_calls':full_fallback,
             'post_mutation_anchor_rejections':post_rejected,'post_mutation_full_fallback_calls':post_fallback,
             'anchor_final_parity':paired.get('anchor_final_equal') is True,
             'anchor_checkpoint_parity':all(paired.get('anchor_checkpoint_equal',[])),
             'fallback_final_parity':paired.get('fallback_final_equal') is True,
             'fallback_checkpoint_parity':all(paired.get('fallback_checkpoint_equal',[])),
             'lifecycle_parity':paired.get('goal_status_equal') is True,
             'trace_final_parity':paired.get('trace_arm_final_equal') is True,
             'trace_checkpoint_parity':all(paired.get('trace_arm_checkpoint_equal',[]))}
        row['passed']=(row['edge_injected'] and rejected>0 and full_fallback>0 and post_rejected>0 and post_fallback>0 and all(row[k] for k in ('anchor_final_parity','anchor_checkpoint_parity','fallback_final_parity','fallback_checkpoint_parity','lifecycle_parity','trace_final_parity','trace_checkpoint_parity')))
        rows.append(row)
    req(len(rows)==9 and all(r['passed'] for r in rows),'one or more dynamic mutation controls failed')
    out={'schema':'ConversationTaskScopeDynamicMutationAuditV1','passed':not errors,'errors':errors,
         'source_hashes':lock,'control_count':len(rows),'all_controls_pass':len(rows)==9 and all(r['passed'] for r in rows),
         'per_control':rows,'claim_boundary':'Per-case verification of a controlled runtime-added cross-frame dependency on one synthetic conversation family. It does not validate learned ownership, natural-task prevalence, or broad partition completeness.',
         'analyzer_sha256':sha(Path(__file__))}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':out['passed'],'errors':errors,'controls':len(rows),'all_controls_pass':out['all_controls_pass'],'per_control':[{'policy':r['scope_order_policy'],'rejections':r['anchor_proof_rejections'],'fallback_calls':r['anchor_full_fallback_calls'],'passed':r['passed']} for r in rows]},indent=2))
    return int(bool(errors))
if __name__=='__main__': raise SystemExit(main())
