#!/usr/bin/env python3
"""One-worker interpretation readback supplement for the route regression."""
from __future__ import annotations
import hashlib,json,os,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 import substrate_live_self_report_dimension_frame_v1 as frame
 start=frame.lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());boot=load_all_seeds(a)
 import domains.comprehend_text as comprehend
 original=comprehend.comprehend_text;captured=[]
 def observe(*args,**kwargs):
  result=original(*args,**kwargs);captured.append(result);return result
 comprehend.comprehend_text=observe
 try:reply=str(a.converse("report your organisation",speech_act="instruction",speaker="alice"))
 finally:comprehend.comprehend_text=original
 m=a._last_turn_inbound;attrs=dict(a.s.node(m)["attrs"]);c=captured[-1] if captured else None
 dispatch=(getattr(c,"dispatch",None) or {}) if c is not None else {}
 graph=a.s.graph_to_dict();end=frame.lock_inputs()
 payload={"probe_sha256":sha(__file__),"source_lock":start,"source_lock_end":end,"replicate_type":"single_read_only_comprehension_observer","python":{"version":sys.version,"platform":platform.platform()},
  "observation":{"reply":reply,"route":attrs.get("communication_route"),"message_attributes":{k:v for k,v in attrs.items() if k.startswith("comp_") or k.startswith("communication_") or k in ("instruction_outcome","speech_act","kind")},
   "comprehension":{"kind":getattr(c,"kind",None),"raw":getattr(c,"raw",None),"dispatch":dispatch},"loaded_seed_count":len(boot.get("loaded_seed_ids",[])),"failed_seeds":boot.get("failed",[]),"graph_nodes":len(graph.get("nodes",[])),"graph_edges":len(graph.get("edges",[])),"semantic_graph_sha256":frame.semantic_digest(graph)}}
 out=ROOT/"evaluation/reports/live_self_report_route_regression_v1_comprehension_diagnostic_20260927.json";out.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n");print(out)
if __name__=="__main__":main()
