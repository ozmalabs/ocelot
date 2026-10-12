#!/usr/bin/env python3
"""Independent parity and rate-phase analysis for the native trace pilot."""
import hashlib,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/vision_native_rule_phase_trace_v1_20260929_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_native_rule_phase_trace_v1_20260929_lock.json'
OUT=ROOT/'evaluation/reports/vision_native_rule_phase_trace_v1_20260929_analysis.json'
CHECKPOINTS=ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'
SEEDS=(20260935,20260936,20260937)
SCOPES=('global','root_scoped')
RATE_RULE='oo_sunit_rate'

def canon(x):
    if isinstance(x,dict):return {k:canon(v) for k,v in x.items()}
    if isinstance(x,list):return [canon(v) for v in x]
    if isinstance(x,float):return round(x,12)
    return x
def graph_digest(x):return hashlib.sha256(json.dumps(canon(x),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    data=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];workers=data['workers']
    expected=3*2; keys=[(w['seed'],w['scope']) for w in workers]
    pairs=[]; event_names=[]; residuals=[]; matched=0; rate_events_by_call=[]
    for w in workers:
        cp=json.loads((CHECKPOINTS/f"seed_{w['seed']}.json").read_text())
        cp_hash=sha(CHECKPOINTS/f"seed_{w['seed']}.json")
        cp_graph=graph_digest(cp['graph'])
        default=w['default'];traced=w['traced']
        parity=[a['graph_sha256']==b['graph_sha256'] for a,b in zip(default['steps'],traced['steps'])]
        pairs.append({'seed':w['seed'],'scope':w['scope'],'step_graph_parity':parity,
                      'default_digest':[x['graph_sha256'] for x in default['steps']],
                      'traced_digest':[x['graph_sha256'] for x in traced['steps']]})
        reports=traced['trace_reports']
        if len(reports)==2:
            rate_events_by_call.append([sum(e['rule_name']==RATE_RULE for e in r['events']) for r in reports])
        for ri,report in enumerate(reports):
            for event in report['events']:
                event_names.append(event['rule_name'])
                if event['rule_name']!=RATE_RULE:continue
                attrs=event['attr_names']; col={name:i for i,name in enumerate(attrs)}
                for node_values in event['values']:
                    if any(node_values[i] is None for i in (col['act'],col['theta'],col['rate'],col['act_step'],col['rate_step'])):continue
                    if node_values[col['act_step']]==node_values[col['rate_step']]:
                        matched+=1
                        residuals.append(abs(node_values[col['rate']]-max(node_values[col['act']]-node_values[col['theta']],0.0)))
    unique_events=set(event_names)
    checks={
        'worker_matrix_complete':len(workers)==expected and len(set(keys))==expected and data.get('expected_workers')==expected,
        'capture_lock_matches':data.get('locked_inputs')==locked,
        'source_stable':data.get('source_stable') is True and all(w['default']['source_stable'] and w['traced']['source_stable'] for w in workers),
        'checkpoint_file_and_graph_identity':all(
            sha(CHECKPOINTS/f"seed_{w['seed']}.json")==locked['checkpoints'][str(w['seed'])]
            and json.loads((CHECKPOINTS/f"seed_{w['seed']}.json").read_text())['prepared_graph_sha256']==graph_digest(json.loads((CHECKPOINTS/f"seed_{w['seed']}.json").read_text())['graph'])
            and w['default']['checkpoint_sha256']==graph_digest(json.loads((CHECKPOINTS/f"seed_{w['seed']}.json").read_text())['graph'])
            and w['traced']['checkpoint_sha256']==graph_digest(json.loads((CHECKPOINTS/f"seed_{w['seed']}.json").read_text())['graph']) for w in workers),
        'two_step_calls_per_arm':all(len(w['default']['steps'])==2 and len(w['traced']['steps'])==2 for w in workers),
        'exact_final_graph_parity':all(all(p['step_graph_parity']) for p in pairs),
        'trace_not_truncated':all(w['traced']['trace_dropped_events']==0 and all(r['trace_truncated'] is False for r in w['traced']['trace_reports']) for w in workers),
        'rate_rule_observed_each_call':len(rate_events_by_call)==expected and all(len(x)==2 and all(n>0 for n in x) for x in rate_events_by_call),
        'state_samples_complete':all(all(len(e['node_ids'])==32 and len(e['values'])==32 and len(e['attr_names'])==6 for r in w['traced']['trace_reports'] for e in r['events']) for w in workers),
        'numeric_rate_diagnostics_present':matched>0 and all(math.isfinite(x) for x in residuals),
    }
    timing={arm:{'worker_wall_median_s':statistics.median(w[arm]['worker_wall_ns']/1e9 for w in workers),
                 'worker_cpu_median_s':statistics.median(w[arm]['worker_process_cpu_ns']/1e9 for w in workers),
                 'peak_rss_max_bytes':max(w[arm]['peak_rss_bytes'] for w in workers)} for arm in ('default','traced')}
    out={'run_id':data['run_id'],'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'pass':all(checks.values()),
         'worker_count':len(workers),'exact_graph_parity':pairs,'trace_rule_names':sorted(unique_events),
         'rate_rule_events_per_call':rate_events_by_call,'same_stamp_rate_samples':matched,
         'rate_equation_diagnostic':{'max_abs_residual':max(residuals,default=None),'mismatches_over_1e_9':sum(x>1e-9 for x in residuals),
             'median_abs_residual':statistics.median(residuals) if residuals else None,
             'claim':'Samples are taken immediately after a successful whole-rule invocation, not individual bindings.'},
         'timing':timing,'trace_event_count':sum(w['traced']['trace_event_count'] for w in workers),
         'claim_boundary':'Exact default-tick final graph parity and post-rule snapshots on three adapted checkpoints and one synthetic grating. No scaling, natural-image accuracy, or frame-discovery claim.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':out['total_checks'],
        'rate_equation_diagnostic':out['rate_equation_diagnostic'],'timing':timing},indent=2))
    if not out['pass']:raise SystemExit('native rule trace parity gate failed')

if __name__=='__main__':main()
