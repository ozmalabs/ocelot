#!/usr/bin/env python3
"""Restore and fixed-point replay each store snapshot from live runtime v1.2."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native
CAP=ROOT/'evaluation/reports/live_runtime_store_states_v1_2_20261004.json';CAP_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_store_states_v1_2_lock_20261004.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_STORE_REPLAY_V1_1_PREREG_20261004.md';RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_runtime_store_replay_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/live_runtime_store_replay_v1_1_lock_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_store_replay_v1_1_20261004.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 spec=importlib.util.spec_from_file_location('store_capture_source_lock',ROOT/'evaluation/substrate_capability/live_runtime_store_states_v1_2.py');m=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(m)
 cap=json.loads(CAP.read_text());capture_lock=json.loads(CAP_LOCK.read_text())['locked_inputs']
 if not cap.get('source_stable') or cap.get('locked_inputs')!=capture_lock or cap.get('post_run_inputs')!=capture_lock or m.lock_inputs()!=capture_lock:raise SystemExit('v1.2 store capture is stale or failed its source lock')
 payloads=[]
 for req in cap['requests']:
  for row in req['stores']:payloads.append({'path':row['path'],'sha256':sha(ROOT/row['path'])})
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'capture_sha256':sha(CAP),'capture_lock_sha256':sha(CAP_LOCK),'capture_payloads':payloads,'native_sha256':sha(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock')}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior replay record')
  LOCK.write_text(json.dumps({'schema':'LiveRuntimeStoreReplayV1_1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 assert_measuring_engine();locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale replay source lock')
 cap=json.loads(CAP.read_text());runs=[];Native=_native.Substrate
 for req_i,req in enumerate(cap['requests'],1):
  for row in req['stores']:
   state=json.loads(gzip.open(ROOT/row['path'],'rb').read());rules=sorted(state['rules'],key=lambda x:int(x['local_rule_index']));indices=[int(x['local_rule_index']) for x in rules]
   rec={'request':req_i,'store_id':int(row['store_id']),'graph_nodes':len(state['graph'].get('nodes',[])),'graph_edges':len(state['graph'].get('edges',[])),'rule_count':len(rules),'local_rule_indices':indices,'payload_sha256':row['state_sha256']}
   try:
    rec['indices_contiguous']=indices==list(range(len(indices)))
    if not rec['indices_contiguous']:raise ValueError('local rule indices are not contiguous')
    s=Native();s.graph_from_dict(state['graph']);rec['graph_roundtrip']=s.graph_to_dict()==state['graph']
    
    for i,x in enumerate(rules):
     idx=int(s.add_rule_preserving_match_order(x['definition']))
     if idx!=i:raise ValueError(f'rule slot drift: expected {i}, got {idx}')
     if not x['definition'].get('active',True):s.remove_rule(idx)
    def semantic_rule(d):return {k:v for k,v in d.items() if k not in ('rule_uid','revision','content_hash','mutation_protected')}
    rec['rule_roundtrip']=canonical([semantic_rule(x) for x in s.export_rules()])==canonical([semantic_rule(x['definition']) for x in rules])
    if not rec['graph_roundtrip'] or not rec['rule_roundtrip']:raise ValueError('graph/rule round-trip mismatch')
    Native.scale_audit_set_enabled(False);Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_reset();Native.scale_audit_per_rule_reset()
    Native.scale_audit_set_enabled(True);Native.scale_audit_set_per_rule_enabled(True);call_rows=[];started=time.perf_counter()
    for call_i in range(1,9):
     t=time.perf_counter();steps=int(s.run_rules(100_000));call_rows.append({'call':call_i,'progress_steps':steps,'elapsed_s':time.perf_counter()-t})
     if steps==0:break
    elapsed=time.perf_counter()-started;Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_set_enabled(False)
    ident={int(a):(int(store),int(local)) for a,store,local in Native.scale_audit_rule_identity_snapshot()};replay={}
    for aid,metric,count in Native.scale_audit_per_rule_snapshot():
     pair=ident.get(int(aid));
     if pair is None:continue
     local_store,local_index=pair
     # This fresh Substrate is the only active replay store in this window.
     replay.setdefault(int(local_index),{})[str(metric)]=int(count)
    obs=cap['native_counter_observations'][req_i-1]['counter_rows'];source_ids={int(a):(int(store),int(local)) for a,store,local in obs['identities']};expected={}
    for aid,metric,count in obs['per_rule']:
     source=source_ids.get(int(aid))
     if source and source[0]==rec['store_id']:expected.setdefault(source[1],{})[str(metric)]=int(count)
    rec.update({'replay_calls':call_rows,'elapsed_s':elapsed,'replay_progress_steps':sum(x['progress_steps'] for x in call_rows),'final_nodes':len(s.graph_to_dict().get('nodes',[])),'final_edges':len(s.graph_to_dict().get('edges',[])),'global_counters':dict(Native.scale_audit_snapshot()),'replay_per_rule':replay,'expected_per_rule':expected,'replayed_rule_count':len(replay),'expected_active_rule_count':len(expected)})
   except Exception as e:
    Native.scale_audit_set_per_rule_enabled(False);Native.scale_audit_set_enabled(False);rec['error']=f'{type(e).__name__}: {e}'
   runs.append(rec);print(f"replay request={req_i} store={row['store_id']} rules={len(indices)} error={rec.get('error','none')}",flush=True)
 post=inputs();result={'schema':'LiveRuntimeStoreReplayV1_1','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'replay_count':len(runs),'runs':runs,'all_stores_restored':len(runs)==sum(len(x['stores']) for x in cap['requests']) and all(not x.get('error') and x.get('graph_roundtrip') and x.get('rule_roundtrip') and x.get('indices_contiguous') for x in runs),'claim_limit':'fixed-point replay of one first graph and cumulative rule table per request/store; chronological route schedule and scopes are not captured'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'all_stores_restored':result['all_stores_restored'],'source_stable':result['source_stable'],'replays':len(runs),'errors':sum(bool(x.get('error')) for x in runs),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['all_stores_restored'] and result['source_stable'] else 2
if __name__=='__main__':raise SystemExit(main())
