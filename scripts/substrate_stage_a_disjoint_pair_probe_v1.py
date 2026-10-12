#!/usr/bin/env python3
"""Paired Stage A compare probe for disjoint two-variable mixed writes."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_STAGE_A_DISJOINT_PAIR_PREREG_20260926.md"
SOURCES={"stage_a":ROOT/"runners/dsl/src/stage_a.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","rewrite":ROOT/"runners/dsl/src/rewrite.rs","graph":ROOT/"runners/dsl/src/graph.rs"}
LOCK=ROOT/"evaluation/substrate_capability/stage_a_disjoint_pair_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_stage_a_disjoint_pair_v1_20260926.json"
SIZES=(1,2,6,16,32)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def arm(size,compare):
 from substrate_rs import Substrate,_native
 _native.stage_a_compare_enable(compare);_native.stage_a_compare_reset()
 sub=Substrate();g=sub._inner;pairs=[]
 for i in range(size):
  x=g.add_node("DisjointPairNode",{"watched":i+10,"ordinal":i,"side":"x"})
  y=g.add_node("DisjointPairNode",{"ordinal":i,"side":"y"});pairs.append((x,y))
  g.add_edge_unchecked(x,"trigger",y,{})
  g.add_edge_unchecked(x,"derived",y,{"value":-1,"marker":i})
 read={"__term__":{"type":"Attr","node":{"type":"Var","name":"x"},"key":"watched"}}
 g.add_rule({"name":"disjoint_pair_edge_overwrite","match":[["x","trigger","y"]],"effects":[["add_edge","x","derived","y",{"value":read}]]})
 progress=g.run_rules(100);state=g.graph_to_dict();terminal=g.run_rules(1)
 stats=_native.stage_a_compare_stats();nodes={n["id"]:n for n in state["nodes"]};derived={(e["src"],e["tgt"]):e for e in state["edges"] if e["type"]=="derived"}
 values=[derived[(x.value,y.value)]["attrs"] for x,y in pairs]
 return {"compare_enabled":compare,"progress":progress,"terminal_progress":terminal,"graph":state,"derived_attrs":values,"derived_edge_count":len(derived),"stage_a_compare_stats":stats,"stage_a_stats":_native.stage_a_stats(),"oracle_gate":values==[{"value":i+10} for i in range(size)] and len(derived)==size}
def worker(rep):
 started=lock_inputs();cells=[]
 for n in SIZES:
  control=arm(n,False);candidate=arm(n,True)
  cells.append({"size":n,"control":control,"candidate":candidate,"exact_graph_parity":control["graph"]==candidate["graph"],"progress_parity":control["progress"]==candidate["progress"] and control["terminal_progress"]==candidate["terminal_progress"]})
 return {"replicate":rep,"pid":os.getpid(),"started_inputs":started,"finished_inputs":lock_inputs(),"cells":cells}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 schedule=[0,1,2];random.Random(20260926).shuffle(schedule);runs=[]
 for rep in schedule:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=lock_inputs();checks={"three_fresh_processes":len({r["pid"] for r in runs})==3,"sources_stable":post==locked and all(r["started_inputs"]==locked==r["finished_inputs"] for r in runs),"all_sizes_present":all(tuple(c["size"] for c in r["cells"])==SIZES for r in runs),"all_arms_match_oracle_and_each_other":all(c["control"]["oracle_gate"] and c["candidate"]["oracle_gate"] and c["exact_graph_parity"] and c["progress_parity"] for r in runs for c in r["cells"]),"stage_a_compares_cleanly":all(c["candidate"]["stage_a_compare_stats"]["compared_drains"]>0 and c["candidate"]["stage_a_compare_stats"]["diverged_drains"]==0 and c["candidate"]["stage_a_compare_stats"]["unsound_drains"]==0 and c["candidate"]["stage_a_stats"]["conflict_fallbacks"]==0 for r in runs for c in r["cells"])}
 payload={"schema_version":1,"run_id":"substrate-stage-a-disjoint-pair-v1-20260926","claim_boundary":"Disjoint two-variable pairs apply AddEdge attribute replacement to pre-existing cross-edges; compares normal closure and Stage A derive/undo/commit at 1/2/6/16/32 bindings.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":schedule,"sizes":SIZES,"checks":checks,"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("capture validity or semantic gate failed")
if __name__=="__main__":main()
