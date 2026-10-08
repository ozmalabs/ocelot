#!/usr/bin/env python3
"""Replay each captured primary run_rules call from its exact entry state."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native
CAP=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v1_1_20261004.json';CAP_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_entry_states_v1_1_lock_20261004.json';CAP_ANALYSIS=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v1_1_analysis_20261004.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_REPLAY_V2_PREREG_20261004.md';RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_runtime_closure_entry_replay_v2.py'
LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_entry_replay_v2_lock_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_closure_entry_replay_v2_20261004.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 cap=json.loads(CAP.read_text());lock=json.loads(CAP_LOCK.read_text())['locked_inputs'];analysis=json.loads(CAP_ANALYSIS.read_text())
 if not cap.get('source_stable') or not all(cap.get('parent_parity',{}).values()) or cap.get('locked_inputs')!=lock or cap.get('post_run_inputs')!=lock or not analysis.get('passed'):raise SystemExit('closure-entry capture is stale or failed analysis')
 payloads=[]
 for req in cap['requests']:
  for state in req['states']:payloads.append({'path':state['path'],'sha256':sha(ROOT/state['path'])})
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'capture_sha256':sha(CAP),'capture_lock_sha256':sha(CAP_LOCK),'capture_analysis_sha256':sha(CAP_ANALYSIS),'capture_payloads':payloads,'native_sha256':sha(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock')}
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def semantic_rule(x):return {k:v for k,v in x.items() if k not in ('rule_uid','revision','content_hash',)}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior entry replay')
  LOCK.write_text(json.dumps({'schema':'LiveRuntimeClosureEntryReplayV2Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 assert_measuring_engine();locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale entry replay lock')
 cap=json.loads(CAP.read_text());Native=_native.Substrate;out_reqs=[]
 for req_i,req in enumerate(cap['requests'],1):
  state_by_hash={r['state_sha256']:r for r in req['states']};call_rows=[];aggregate={};t0=time.perf_counter()
  for call in req['calls']:
   row=state_by_hash[call['state_sha256']];state=json.loads(gzip.open(ROOT/row['path'],'rb').read());rules=state['rules'];
   s=Native();s.graph_from_dict(state['graph']);graph_ok=s.graph_to_dict()==state['graph'];
   s.import_rules_preserving_match_order(rules)
   if int(s.rule_count()) != len(rules):raise ValueError('rule count drift during exact import')
   exported=s.export_rules();rule_ok=canon([semantic_rule(x) for x in exported])==canon([semantic_rule(x) for x in rules])
   Native.scale_audit_set_enabled(False);Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_reset();Native.scale_audit_per_rule_reset()
   Native.scale_audit_set_enabled(True);Native.scale_audit_set_per_rule_enabled(True);started=time.perf_counter();steps=int(s.run_rules(int(call['max_steps'])));elapsed=time.perf_counter()-started
   Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_set_enabled(False)
   identities={int(a):(int(store),int(local)) for a,store,local in Native.scale_audit_rule_identity_snapshot()};metrics={}
   for aid,metric,value in Native.scale_audit_per_rule_snapshot():
    ident=identities.get(int(aid))
    if ident is None:continue
    local=int(ident[1]);metrics.setdefault(local,{})[str(metric)]=int(value)
    aggregate.setdefault(local,{})[str(metric)]=aggregate.setdefault(local,{}).get(str(metric),0)+int(value)
   call_rows.append({'call_index':call['call_index'],'state_sha256':call['state_sha256'],'graph_roundtrip':graph_ok,'rule_roundtrip':rule_ok,'rule_count':len(rules),'mutation_protected_rules':sum(bool(x.get('mutation_protected')) for x in rules),'progress_steps':steps,'elapsed_s':elapsed,'per_rule':metrics,'global_counters':dict(Native.scale_audit_snapshot()),'final_graph_sha256':hashlib.sha256(canon(s.graph_to_dict()).encode()).hexdigest()})
   print(f'replayed request={req_i} call={call["call_index"]} rules={len(rules)} steps={steps} graph={graph_ok} rules_rt={rule_ok}',flush=True)
  out_reqs.append({'request':req_i,'prompt':req.get('prompt'),'calls':call_rows,'aggregate_per_rule':aggregate,'elapsed_s':time.perf_counter()-t0})
 post=inputs();result={'schema':'LiveRuntimeClosureEntryReplayV2','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'requests':out_reqs,'all_calls_replayed':len(out_reqs)==2 and sum(len(r['calls']) for r in out_reqs)==sum(len(r['calls']) for r in cap['requests']) and all(c['graph_roundtrip'] and c['rule_roundtrip'] for r in out_reqs for c in r['calls']),'claim_limit':'primary run_rules calls only; per-call states replay independently and are summed; rule metadata is preserved, but scheduler dirty bits, dirty nodes, and cursors are not checkpointed'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'all_calls_replayed':result['all_calls_replayed'],'source_stable':result['source_stable'],'calls_per_request':[len(x['calls']) for x in out_reqs],'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['all_calls_replayed'] and result['source_stable'] else 2
if __name__=='__main__':raise SystemExit(main())
