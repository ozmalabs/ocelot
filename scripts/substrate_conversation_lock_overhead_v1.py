#!/usr/bin/env python3
"""Paired sequential full-turn timing with and without the conversation lock."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CONVERSATION_LOCK_OVERHEAD_PREREG_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py","conversation_action":ROOT/"domains/conversation_action.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json"}
LOCK=ROOT/"evaluation/substrate_capability/conversation_lock_overhead_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_conversation_lock_overhead_v1_20260926.json"
PAIRS=20
BASELINE="I see the grey thing stays, the yellow counter, and the blue thing moves."
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
class NoLock:
 def __enter__(self):return self
 def __exit__(self,*exc):return False
def capture():
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 a=WorldAdapter(seeds=());load_all_seeds(a)
 attach_scene(a,[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}])
 for _ in range(2):a.converse("describe what you see",speech_act="instruction",speaker="alice")
 guarded_lock=a._conversation_lock
 rng=random.Random(20260926);orders=[]
 for _ in range(PAIRS):
  pair_order=["guarded","noop"];rng.shuffle(pair_order);orders.append(pair_order)
 rows=[]
 for pair in range(PAIRS):
  pair_rows=[]
  for condition in orders[pair]:
   a._conversation_lock=guarded_lock if condition=="guarded" else NoLock()
   t0=time.perf_counter_ns();reply=a.converse("describe what you see",speech_act="instruction",speaker="alice");elapsed=time.perf_counter_ns()-t0
   pair_rows.append({"condition":condition,"elapsed_ns":elapsed,"reply":str(reply),"reply_matches_baseline":str(reply)==BASELINE})
  rows.append({"pair":pair,"order":[r["condition"] for r in pair_rows],"rows":pair_rows,"paired_delta_ns":next(r["elapsed_ns"] for r in pair_rows if r["condition"]=="guarded")-next(r["elapsed_ns"] for r in pair_rows if r["condition"]=="noop")})
 finished=lock_inputs()
 return {"started_inputs":started,"finished_inputs":finished,"rows":rows,"graph_nodes":a.inner.node_count(),"reply_parity":all(r["reply_matches_baseline"] for pair in rows for r in pair["rows"])}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 locked=json.loads(LOCK.read_text())["locked_inputs"]
 if lock_inputs()!=locked:raise SystemExit("stale or missing lock")
 os.environ.setdefault("OZMA_NO_LLM","1");os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 result=capture();post=lock_inputs();conditions={c:[r["elapsed_ns"] for p in result["rows"] for r in p["rows"] if r["condition"]==c] for c in ("guarded","noop")}
 payload={"schema_version":1,"run_id":"substrate-conversation-lock-overhead-v1-20260926","claim_boundary":"Within-adapter paired sequential full-turn latency comparison; no concurrent throughput or broad route claim.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"warmup_turns":2,"pairs":PAIRS,"order_seed":20260926,"started_inputs":result["started_inputs"],"finished_inputs":result["finished_inputs"],"graph_nodes":result["graph_nodes"],"reply_parity":result["reply_parity"],"conditions":conditions,"pairs_raw":result["rows"],"summary":{"guarded_median_ns":statistics.median(conditions["guarded"]),"noop_median_ns":statistics.median(conditions["noop"]),"paired_delta_median_ns":statistics.median(r["paired_delta_ns"] for r in result["rows"]),"guarded_p90_ns":sorted(conditions["guarded"])[int(.9*(len(conditions["guarded"])-1))],"noop_p90_ns":sorted(conditions["noop"])[int(.9*(len(conditions["noop"])-1))]}}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"summary":payload["summary"],"reply_parity":payload["reply_parity"],"source_stable":locked==post==result["started_inputs"]==result["finished_inputs"]},indent=2))
if __name__=="__main__":main()
