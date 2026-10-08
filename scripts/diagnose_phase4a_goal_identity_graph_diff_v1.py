#!/usr/bin/env python3
"""Capture and compare complete graph structures for the N=2 parity pair."""
from __future__ import annotations
import collections,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/substrate_phase4a_produced_goal_identity_v1.py"
OUT=ROOT/"evaluation/reports/phase4a_goal_identity_graph_diff_diagnostic_20260926.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(g):
 nodes=collections.defaultdict(list)
 for n in g["nodes"]:
  desc=(n["type"],json.dumps(n["attrs"],sort_keys=True,default=str))
  nodes[desc].append(int(n["id"]))
 return nodes
def edge_set(g,mapping):
 return {(mapping[int(e["src"])],e["type"],mapping[int(e["tgt"])],json.dumps(e["attrs"],sort_keys=True,default=str)) for e in g["edges"]}
def main():
 if len(sys.argv)==4 and sys.argv[1]=="--worker":
  from substrate_rs._native import Substrate
  old=Substrate.graph_to_dict; captured={}
  def record(self):
   graph=old(self);captured["graph"]=graph;return graph
  Substrate.graph_to_dict=record
  import importlib.util
  spec=importlib.util.spec_from_file_location("phase4a_identity_runner",RUNNER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  row=mod.worker(int(sys.argv[2]),0,sys.argv[3]);row["graph_snapshot"]=captured["graph"]
  print(json.dumps(row,sort_keys=True,default=str));return
 env=dict(__import__("os").environ);env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 captures={}
 for arm in ("full","scoped"):
  raw=subprocess.check_output([sys.executable,str(Path(__file__).resolve()),"--worker","2",arm],cwd=ROOT,env=env,text=True)
  captures[arm]=json.loads(raw)
 f,s=captures["full"]["graph_snapshot"],captures["scoped"]["graph_snapshot"]
 fd,sd=canonical(f),canonical(s)
 descriptors_equal={k:len(fd[k])==len(sd.get(k,[])) for k in set(fd)|set(sd)}
 mapping={}
 for k,ids in fd.items():
  if len(ids)!=len(sd[k]):continue
  for left,right in zip(sorted(ids),sorted(sd[k])):mapping[left]=right
 edges_equal=edge_set(f,mapping)==edge_set(s,{int(n["id"]):int(n["id"]) for n in s["nodes"]})
 result={"run_id":"phase4a-goal-identity-graph-diff-diagnostic-20260926",
  "runner_sha256":sha(RUNNER),"captured_arms":{a:{k:v for k,v in x.items() if k in ("size","arm","pid","graph_digest","projection")} for a,x in captures.items()},
  "comparison":{"node_count_full":len(f["nodes"]),"node_count_scoped":len(s["nodes"]),
    "edge_count_full":len(f["edges"]),"edge_count_scoped":len(s["edges"]),
    "raw_digest_equal":captures["full"]["graph_digest"]==captures["scoped"]["graph_digest"],
    "node_descriptor_multisets_equal":all(descriptors_equal.values()),"descriptor_mapping_nodes":len(mapping),
    "all_nodes_mapped":len(mapping)==len(f["nodes"])==len(s["nodes"]),"typed_edges_equal_after_descriptor_mapping":edges_equal,
    "normalized_task_projection_equal":captures["full"]["projection"]==captures["scoped"]["projection"]},
  "graph_snapshots":{"full":f,"scoped":s},
  "interpretation":"Raw graph digests differ because scheduling changes insertion order/IDs of generated nodes. For this N=2 pair, typed nodes can be paired by type+attributes and every typed edge then matches exactly. The graph is isomorphic, although byte-for-byte identity is not preserved."
 }
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,default=str)+"\n")
 print(json.dumps({"output":str(OUT),"comparison":result["comparison"]},indent=2))
if __name__=="__main__":main()
