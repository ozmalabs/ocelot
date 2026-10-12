#!/usr/bin/env python3
"""Read-only graph repeat diagnostic for route panel stimulus J."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_ROUTE_J_GRAPH_REPEAT_DIAGNOSTIC_V1_1_AMENDMENT_20260927.md"
OUT=ROOT/"evaluation/reports/route_j_graph_repeat_diagnostic_v1_1_20260927.json"
TEXT="what is organisation?"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock():
 import substrate_live_self_report_dimension_frame_v1 as frame
 contrast=__import__("probe_self_report_route_contrast_v1_2")
 return {"study_source_lock":contrast.study_source_lock(),"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__)}
def worker(rep):
 start=lock()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());boot=load_all_seeds(a)
 import domains.comprehend_text as comprehend
 captured=[];original=comprehend.comprehend_text
 def observe(*args,**kwargs):
  c=original(*args,**kwargs);captured.append(c);return c
 comprehend.comprehend_text=observe
 try:reply=str(a.converse(TEXT,speech_act="instruction",speaker="alice"))
 finally:comprehend.comprehend_text=original
 m=a._last_turn_inbound;attrs=dict(a.s.node(m)["attrs"]);c=captured[-1] if captured else None
 graph=a.s.graph_to_dict();frame=__import__("substrate_live_self_report_dimension_frame_v1")
 node_records=[]
 for n in graph.get("nodes",[]):
  x=dict(n.get("attrs",{}))
  if n.get("type")=="SystemModel":x.pop("ts",None);x.pop("runtime_s",None)
  body=json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
  node_records.append([str(n["id"]),str(n["type"]),hashlib.sha256(body.encode()).hexdigest()])
 node_records.sort(key=lambda r:(r[1],r[0],r[2]))
 edge_records=sorted([[int(e["src"]),str(e["type"]),int(e["tgt"])] for e in graph.get("edges",[])])
 canonical=json.dumps({"nodes":node_records,"edges":edge_records},sort_keys=True,separators=(",",":"))
 end=lock();dispatch=getattr(c,"dispatch",None) or {}
 interlocutors=[{"id":str(n["id"]),"attrs":dict(n.get("attrs",{}))} for n in graph.get("nodes",[]) if n.get("type")=="Interlocutor"]
 return {"replicate":rep,"pid":os.getpid(),"route":attrs.get("communication_route"),"reply":reply,
  "comprehension":{"kind":getattr(c,"kind",None),"intent":getattr(c,"intent",None),"dispatch":dispatch},
  "loaded_seed_count":len(boot.get("loaded_seed_ids",[])),"failed_seeds":boot.get("failed",[]),
  "node_count":len(node_records),"edge_count":len(edge_records),"node_type_counts":dict(Counter(r[1] for r in node_records)),
  "order_sensitive_digest":frame.semantic_digest(graph),"canonical_digest":hashlib.sha256(canonical.encode()).hexdigest(),
  "node_fingerprints":node_records,"edge_records":edge_records,"interlocutor_records":interlocutors,"worker_start_lock":start,"worker_end_lock":end}
def main():
 if sys.argv[1:2]==["--worker"]:
  print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 driver=lock()
 if sys.argv[1:]==["--lock"]:print(json.dumps(driver,indent=2,sort_keys=True));return
 jobs=[0,1,2];runs=[]
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(p.stdout));print(f"completed graph replicate={rep}",flush=True)
 post=lock();payload={"schema_version":1,"run_id":"route-j-graph-repeat-diagnostic-v1-20260927","driver_lock":driver,"post_run_lock":post,"runs":runs,"environment":{"python":sys.version,"platform":platform.platform()}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"workers":len(runs),"source_stable":post==driver and all(r["worker_start_lock"]==driver==r["worker_end_lock"] for r in runs)},indent=2))
if __name__=="__main__":main()
