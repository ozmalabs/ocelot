#!/usr/bin/env python3
"""Independently compare complete full/scoped typed graphs by descriptors."""
from __future__ import annotations
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_phase4a_goal_identity_graph_isomorphism_v1_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/phase4a_goal_identity_graph_isomorphism_lock_20260926.json"
BASE_ANALYSIS=ROOT/"evaluation/reports/substrate_phase4a_produced_goal_identity_v1_analysis_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_phase4a_goal_identity_graph_isomorphism_v1_analysis_20260926.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def descriptor(n):return (n["type"],json.dumps(n["attrs"],sort_keys=True,default=str))
def nodes_by_desc(g):
 d=collections.defaultdict(list)
 for n in g["nodes"]:d[descriptor(n)].append(int(n["id"]))
 return d
def mapped_edges(g,mapping):
 return collections.Counter((mapping[int(e["src"])],e["type"],mapping[int(e["tgt"])],
   json.dumps(e["attrs"],sort_keys=True,default=str)) for e in g["edges"])
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());base=json.loads(BASE_ANALYSIS.read_text())
 cells={(int(r["size"]),int(r["replicate"]),r["arm"]):r for r in raw["runs"]};pairs={};
 for n in (2,4,8):
  for rep in range(3):
   f=cells[n,rep,"full"];s=cells[n,rep,"scoped"];fg=f["graph_snapshot"];sg=s["graph_snapshot"]
   fd,sd=nodes_by_desc(fg),nodes_by_desc(sg);keys=set(fd)|set(sd)
   descriptor_multiset_equal=all(len(fd[k])==len(sd.get(k,[])) for k in keys)
   mapping={}
   ambiguous=[]
   for k in sorted(keys):
    left,right=sorted(fd[k]),sorted(sd.get(k,[]))
    if len(left)!=len(right):continue
    if len(left)>1:ambiguous.append({"type":k[0],"attrs":json.loads(k[1]),"multiplicity":len(left)})
    mapping.update(zip(left,right))
   full_map=mapped_edges(fg,mapping)
   scoped_id={int(x["id"]):int(x["id"]) for x in sg["nodes"]}
   scoped_edges=mapped_edges(sg,scoped_id)
   pair={"size":n,"replicate":rep,"node_count_full":len(fg["nodes"]),"node_count_scoped":len(sg["nodes"]),
    "edge_count_full":len(fg["edges"]),"edge_count_scoped":len(sg["edges"]),
    "raw_digest_equal":f["graph_digest"]==s["graph_digest"],"node_descriptor_multisets_equal":descriptor_multiset_equal,
    "all_nodes_mapped":len(mapping)==len(fg["nodes"])==len(sg["nodes"]),"ambiguous_descriptor_classes":ambiguous,
    "typed_edge_multisets_equal_after_mapping":full_map==scoped_edges,
    "task_projection_equal":f["projection"]==s["projection"],"both_workers_complete":f["complete"] and s["complete"],
    "both_provenance_gates":f["source_provenance_all_tasks"] and s["source_provenance_all_tasks"]}
   pairs[f"{n}:{rep}"]=pair
 checks={"locked_inputs_match":raw["locked_inputs"]==lock["locked_inputs"] and raw["lock_sha256"]==sha(LOCK),
  "18_fresh_workers_and_pids":len(raw["runs"])==18 and len({r["pid"] for r in raw["runs"]})==18,
  "complete_size_replicate_arm_matrix":len(cells)==18,
  "base_semantic_capture_passes":all(base["checks"].values()),
  "every_pair_isomorphic_by_descriptor_map":all(p["node_descriptor_multisets_equal"] and p["all_nodes_mapped"] and p["typed_edge_multisets_equal_after_mapping"] for p in pairs.values()),
  "every_pair_has_matching_task_projection":all(p["task_projection_equal"] and p["both_workers_complete"] and p["both_provenance_gates"] for p in pairs.values())}
 result={"schema_version":1,"run_id":"phase4a-goal-identity-graph-isomorphism-v1-analysis-20260926",
  "raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"base_analysis_sha256":sha(BASE_ANALYSIS),"checks":checks,"pairs":pairs,
  "interpretation":"All 9 full/scoped graph pairs are isomorphic under pairing nodes by exact type and attribute descriptors, followed by complete typed-edge multiset comparison. Generated IDs and insertion order differ. This is evidence only for this frozen Phase 4A workload and sizes. Ambiguous descriptor classes are disclosed per pair; ID order resolves ties and the edge check verifies the resulting mapping.",
  "claim_boundary":"Finite graph-isomorphism diagnostic for one generated Phase 4A family, N=2/4/8, three fresh-process pairs per size; no general graph canonicalization or natural-workload claim."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"pairs":pairs},indent=2))
 if not all(checks.values()):raise SystemExit("one or more graph mapping/parity checks failed; preserve counterexample")
if __name__=="__main__":main()
