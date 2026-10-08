#!/usr/bin/env python3
"""Independent analysis of the route-J graph repeat diagnostic."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/route_j_graph_repeat_diagnostic_v1_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/route_j_graph_repeat_diagnostic_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/route_j_graph_repeat_diagnostic_v1_analysis_20260927.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_ROUTE_J_GRAPH_REPEAT_DIAGNOSTIC_V1_PREREG_20260927.md"
RUNNER=ROOT/"scripts/diagnose_route_j_graph_repeat_v1.py"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=raw["runs"]
 checks={"three_unique_workers":len(rows)==3 and len({r["pid"] for r in rows})==3,
  "driver_worker_source_locks_stable":raw["driver_lock"]["study_source_lock"]==raw["post_run_lock"]["study_source_lock"]==lock["study_source_lock"] and all(r["worker_start_lock"]==lock["study_source_lock"]==r["worker_end_lock"] for r in rows),
  "protocol_runner_lock_match":raw["driver_lock"]["protocol_sha256"]==lock["protocol_sha256"]==sha(PROTOCOL) and raw["driver_lock"]["runner_sha256"]==lock["runner_sha256"]==sha(RUNNER),
  "complete_graph_fingerprints":all(len(r["node_fingerprints"])==r["node_count"] and len(r["edge_records"])==r["edge_count"] for r in rows),
  "route_and_reply_repeat":len({(r["route"],r["reply"],json.dumps(r["comprehension"],sort_keys=True)) for r in rows})==1}
 node_maps=[{(x[0],x[1]):x[2] for x in r["node_fingerprints"]} for r in rows]
 edge_sets=[{tuple(e) for e in r["edge_records"]} for r in rows]
 node_diffs=[];edge_diffs=[]
 for i in range(1,len(rows)):
  base,other=node_maps[0],node_maps[i]
  node_diffs.append({"replicate":rows[i]["replicate"],"added_nodes":sorted([list(k) for k in other.keys()-base.keys()]),"removed_nodes":sorted([list(k) for k in base.keys()-other.keys()]),"changed_node_attr_hashes":sorted([list(k) for k in base.keys()&other.keys() if base[k]!=other[k]])})
  edge_diffs.append({"replicate":rows[i]["replicate"],"added_edges":sorted([list(x) for x in edge_sets[i]-edge_sets[0]]),"removed_edges":sorted([list(x) for x in edge_sets[0]-edge_sets[i]])})
 canonical_equal=len({r["canonical_digest"] for r in rows})==1
 checks["canonical_graph_repeats"]=canonical_equal
 result={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),
  "canonical_graph_repeats":canonical_equal,"workers":[{k:r[k] for k in ("replicate","pid","route","reply","node_count","edge_count","order_sensitive_digest","canonical_digest")} for r in rows],
  "node_differences_from_replicate_0":node_diffs,"edge_differences_from_replicate_0":edge_diffs,
  "interpretation":"If the order-sensitive hashes differ but canonical hashes agree, only graph enumeration order varied. Otherwise the listed node/edge fingerprints identify structural or attribute-level variation."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,indent=2))
 if not checks["three_unique_workers"] or not checks["driver_worker_source_locks_stable"] or not checks["protocol_runner_lock_match"] or not checks["complete_graph_fingerprints"] or not checks["route_and_reply_repeat"]:raise SystemExit("graph repeat diagnostic integrity failed")
if __name__=="__main__":main()
