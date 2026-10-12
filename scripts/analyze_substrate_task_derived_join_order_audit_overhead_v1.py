#!/usr/bin/env python3
"""Independent paired semantic and timer analysis for audit overhead replay."""
from __future__ import annotations
import hashlib,itertools,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/task_derived_join_order_audit_overhead_v1_raw_20260929.json'
OUT=ROOT/'evaluation/reports/task_derived_join_order_audit_overhead_v1_analysis_20260929.json'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_join_order_audit_overhead_v1_lock_20260929.json'
V1=ROOT/'evaluation/reports/task_derived_join_order_context_scale_v1_analysis_20260929.json'
COUNTS=(0,8,32);MODES=('off','on')
EXPECTED={(d,r,m) for d in COUNTS for r in range(10) for m in MODES}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs']
 checks={'expected_60_workers':len(runs)==60 and all('worker_error' not in x for x in runs)}
 flat=[x['worker'] for x in runs if 'worker' in x]
 actual={(w['decoy_count'],w['replicate'],w['audit_mode']) for w in flat}
 checks['exact_context_pair_mode_grid']=actual==EXPECTED
 checks['unique_fresh_processes']=len(flat)==60 and len({w['pid'] for w in flat})==60
 checks['source_native_lock_stable']=raw['locked_inputs']==locked==raw['post_run_inputs'] and all(x.get('before')==locked==x.get('after') for x in runs if 'worker' in x)
 ref=json.loads(V1.read_text());reference={(r['decoy_count'],tuple(r['installed_order'])):r['target_candidate_tests'] for r in ref['rows']}
 grouped=defaultdict(list);rows=[]
 for w in flat:
  d=w['decoy_count'];rep=w['replicate'];mode=w['audit_mode'];t=w['task_run'];idx=w['target_rule_index'];order=tuple(e[1] for e in w['installed_match']);key=f'D{d}_r{rep}_{mode}'
  checks[key+'_semantic_oracles']=t['task_oracle_pass'] and t['common_ground_oracle_pass'] and t['all_checkpoints_fixed'] and len(t['checkpoints'])==10
  checks[key+'_inert_decoys']=w['decoy_goal_count']==d and w['decoy_transition_count']==0
  checks[key+'_source_requested']=w['permutation']=='0123'
  counts=[]
  for cp,audit in zip(t['checkpoints'],w['audit_rows']):
   per=sum(int(n) for i,name,n in audit['per_rule'] if int(i)==idx and str(name)=='candidate_tests')
   clauses=sum(int(n) for i,j,n in audit['clauses'] if int(i)==idx)
   checks[key+f'_cp{cp["event_index"]}_counter_conservation']=per==clauses
   counts.append(per)
  total=sum(counts)
  if mode=='off':checks[key+'_counters_zero']=total==0 and all(not any(int(x[2]) for x in a['per_rule']) and not any(int(x[2]) for x in a['clauses']) for a in w['audit_rows'])
  else:checks[key+'_counters_match_reference']=total==reference.get((d,order))
  row={'decoy_count':d,'replicate':rep,'mode':mode,'pid':w['pid'],'installed_order':list(order),
   'target_candidate_tests':total,'final_digest':t['final_digest'],
   'closure_wall_ns':sum(int(c['wall_ns']) for c in t['checkpoints']),
   'closure_cpu_ns':sum(int(c['cpu_ns']) for c in t['checkpoints'])}
  rows.append(row);grouped[(d,rep)].append(row)
 pairs=[]
 for (d,rep),rs in sorted(grouped.items()):
  by={r['mode']:r for r in rs};checks[f'D{d}_r{rep}_paired_modes_present']=set(by)==set(MODES)
  if set(by)==set(MODES):
   off,on=by['off'],by['on'];checks[f'D{d}_r{rep}_same_order']=off['installed_order']==on['installed_order']
   checks[f'D{d}_r{rep}_graph_parity']=off['final_digest']==on['final_digest']
   pairs.append({'decoy_count':d,'replicate':rep,'installed_order':off['installed_order'],
    'graph_digest_equal':off['final_digest']==on['final_digest'],
    'off_wall_ns':off['closure_wall_ns'],'on_wall_ns':on['closure_wall_ns'],
    'off_cpu_ns':off['closure_cpu_ns'],'on_cpu_ns':on['closure_cpu_ns'],
    'wall_on_over_off':on['closure_wall_ns']/max(1,off['closure_wall_ns']),
    'cpu_on_over_off':on['closure_cpu_ns']/max(1,off['closure_cpu_ns'])})
 summary=[]
 for d in COUNTS:
  ps=[p for p in pairs if p['decoy_count']==d]
  summary.append({'decoy_count':d,'pairs':len(ps),
   'closure_wall_on_over_off':{'median':statistics.median(p['wall_on_over_off'] for p in ps),'min':min(p['wall_on_over_off'] for p in ps),'max':max(p['wall_on_over_off'] for p in ps)},
   'closure_cpu_on_over_off':{'median':statistics.median(p['cpu_on_over_off'] for p in ps),'min':min(p['cpu_on_over_off'] for p in ps),'max':max(p['cpu_on_over_off'] for p in ps)},
   'off_wall_ns':{'median':statistics.median(p['off_wall_ns'] for p in ps),'min':min(p['off_wall_ns'] for p in ps),'max':max(p['off_wall_ns'] for p in ps)},
   'on_wall_ns':{'median':statistics.median(p['on_wall_ns'] for p in ps),'min':min(p['on_wall_ns'] for p in ps),'max':max(p['on_wall_ns'] for p in ps)}})
 payload={'schema_version':1,'raw_sha256':sha(RAW),'analysis_sha256':sha(Path(__file__).resolve()),
  'v1_reference_sha256':sha(V1),'checks':checks,'all_checks_pass':all(checks.values()),
  'checks_passed':sum(checks.values()),'checks_total':len(checks),'worker_count':len(flat),
  'paired_summary':summary,'pairs':pairs,'rows':rows,
  'claim_boundary':'Paired scale-counter on/off timings over one frozen task family. Instrumented API calls remain in the off path; results are task-specific diagnostics, not general overhead or production latency estimates.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':payload['all_checks_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'paired_summary':summary},indent=2))
 if not payload['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
