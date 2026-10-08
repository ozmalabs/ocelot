#!/usr/bin/env python3
"""Analyze default parity and rule-phase maps for the natural-image probe."""
import hashlib,json,math,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/natural_image_act_rate_phase_diagnostic_v1_20260929_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/natural_image_act_rate_phase_diagnostic_v1_20260929_lock.json'
OUT=ROOT/'evaluation/reports/natural_image_act_rate_phase_diagnostic_v1_20260929_analysis.json'
SEEDS=(20260935,20260936,20260937);SCOPES=('global','root_scoped')
RULE_SETTLE={'global':'st_settle','root_scoped':'st_settle_root_scoped_benchmark'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def relerr(a,b):return float(np.abs(np.asarray(a)-np.asarray(b)).sum()/(np.abs(b).sum()+1e-9))
def phase_state(arm,phase,seed,scope):
    if phase=='final':return arm['final_target_state']
    events=[e for rep in arm['trace_reports'] for e in rep['events']]
    rule='oo_sunit_rate' if phase=='after_rate' else RULE_SETTLE[scope]
    selected=[e for e in events if e['rule_name']==rule]
    if not selected:return None
    e=selected[-1];idx={int(n):i for i,n in enumerate(e['node_ids'])}
    # Target units occupy the first half of the explicitly locked node list.
    target=sorted((n for n in e['node_ids'] if n in idx),key=idx.get)[:16]
    return {'_event_order':events.index(e),'_progress_step':e['progress_step'],'_pass_index':e['pass_index'],
        **{key:[e['values'][idx[n]][e['attr_names'].index(key)] for n in target] for key in ('act','rate','act_step','rate_step','theta','aff')}}
def main():
    data=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];workers=data['workers'];rows=[];phase_cells=[]
    event_rule_sets=[];parity=[];trunc=[];snapshots_complete=True;calls=[]
    for w in workers:
        input_map={i['label']:i for i in w['inputs']}
        for label,item in input_map.items():
            d=item['default'];t=item['traced'];calls.append((w,d,t))
            parity.append(d['final_graph_sha256']==t['final_graph_sha256'])
            trunc.append(t['trace_dropped_events']==0 and all(not r['trace_truncated'] for r in t['trace_reports']))
            events=[e for rep in t['trace_reports'] for e in rep['events']]
            event_rule_sets.append(set(e['rule_name'] for e in events))
            snapshots_complete &= all(len(e['node_ids'])==32 and len(e['values'])==32 and all(len(v)==6 for v in e['values']) for e in events)
        # Save rule order and event progression for each traced condition.
        for label,item in input_map.items():
            ev=[e for rep in item['traced']['trace_reports'] for e in rep['events']]
            rules=[e['rule_name'] for e in ev]
            phase_cells.append({'seed':w['seed'],'scope':w['scope'],'input':label,
                'event_rule_order':rules,'event_progress_steps':[e['progress_step'] for e in ev],
                'event_pass_indices':[e['pass_index'] for e in ev]})
        states={label:{phase:phase_state(item['traced'],phase,w['seed'],w['scope']) for phase in ('after_rate','after_settle','final')}
                for label,item in input_map.items()}
        for phase in ('after_rate','after_settle','final'):
          for field in ('act','rate'):
            o=states['original'][phase];r=states['rotated_180'][phase];b=states['blank'][phase]
            if not o or not r or not b:continue
            od=np.asarray(o[field],float)-np.asarray(b[field],float)
            rd=np.asarray(r[field],float)-np.asarray(b[field],float)
            phase_cells.append({'seed':w['seed'],'scope':w['scope'],'phase':phase,'field':field,
                'equivariance_relative_l1':relerr(np.rot90(od.reshape(4,4),2),rd.reshape(4,4)),
                'identity_relative_l1':relerr(od,rd),
                'original_delta_l1':float(np.abs(od).sum()),'rotated_delta_l1':float(np.abs(rd).sum()),
                'original_update_stamps':{'act_step':o['act_step'],'rate_step':o['rate_step']},
                'rotated_update_stamps':{'act_step':r['act_step'],'rate_step':r['rate_step']},
                'event_order':o.get('_event_order') if phase!='final' else None,
                'progress_step':o.get('_progress_step') if phase!='final' else None,
                'pass_index':o.get('_pass_index') if phase!='final' else None})
    expected=6
    matrix={(s,c) for s in SEEDS for c in SCOPES}
    checks={'worker_matrix_complete':len(workers)==expected and {(w['seed'],w['scope']) for w in workers}==matrix,
      'capture_lock_matches':data.get('locked_inputs')==lock,'source_stable':data.get('source_stable') is True,
      'default_trace_final_graph_parity':len(parity)==18 and all(parity),
      'no_trace_truncation':len(trunc)==18 and all(trunc),
      'rate_and_settle_observed_each_input':len(event_rule_sets)==18 and all({'oo_sunit_rate',RULE_SETTLE[w['scope']]}<=rules for w,rules in zip((w for w in workers for _ in w['inputs']),event_rule_sets)),
      'complete_rule_snapshots':snapshots_complete,
      'all_three_inputs_per_worker':all({i['label'] for i in w['inputs']}=={'original','rotated_180','blank'} for w in workers),
      'checkpoint_graphs_match':all(i[arm]['checkpoint_graph_sha256']==lock.get('prepared_checkpoint_graph_sha256',{}).get(str(w['seed']),i[arm]['checkpoint_graph_sha256']) for w in workers for i in w['inputs'] for arm in ('default','traced'))}
    grouped={}
    for phase in ('after_rate','after_settle','final'):
      for scope in SCOPES:
       for field in ('act','rate'):
        rs=[r for r in phase_cells if r.get('phase')==phase and r.get('scope')==scope and r.get('field')==field]
        grouped[f'{phase}:{scope}:{field}']={'checkpoint_count':len(rs),
           'median_equivariance_relative_l1':statistics.median(x['equivariance_relative_l1'] for x in rs) if rs else None,
           'median_identity_relative_l1':statistics.median(x['identity_relative_l1'] for x in rs) if rs else None,
           'proper_mapping_wins':sum(x['equivariance_relative_l1']<x['identity_relative_l1'] for x in rs),
           'median_original_delta_l1':statistics.median(x['original_delta_l1'] for x in rs) if rs else None}
    out={'run_id':data['run_id'],'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'integrity_pass':all(checks.values()),
      'default_trace_parity_calls':sum(parity),'call_count':len(parity),'worker_count':len(workers),
      'phase_scores':phase_cells,'event_sequences':phase_cells[:18],'summary':grouped,
      'claim_boundary':'One natural image, its exact 180-degree rotation, and blank input across three adapted checkpoints and two scopes. Whole-rule event snapshots localize state differences but do not prove per-binding causality.',
      'analysis_note':'Settlement snapshots may be multiple invocations in one tick. The last observed invocation is used for each named rule, with its event order, pass, and progress step retained.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':len(checks),'integrity_pass':out['integrity_pass'],'parity_calls':sum(parity),'summary':grouped},indent=2))
    if not out['integrity_pass']:raise SystemExit('phase diagnostic integrity gate failed')
if __name__=='__main__':main()
