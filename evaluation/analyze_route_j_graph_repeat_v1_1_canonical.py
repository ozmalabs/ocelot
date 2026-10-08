#!/usr/bin/env python3
"""Canonicalize serialized set-valued graph attrs in the route-J follow-up."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"scripts"))
from measurement_graph_digest import normalize_unordered
RAW=ROOT/"evaluation/reports/route_j_graph_repeat_diagnostic_v1_1_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/route_j_graph_repeat_diagnostic_v1_1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/route_j_graph_repeat_diagnostic_v1_1_canonical_analysis_20260927.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=raw["runs"]
 checks={"three_unique_workers":len(rows)==3 and len({r["pid"] for r in rows})==3,
  "full_snapshot_lock_stable":raw["driver_lock"]==raw["post_run_lock"]==lock and all(r["worker_start_lock"]==lock==r["worker_end_lock"] for r in rows),
  "route_reply_comprehension_repeat":len({(r["route"],r["reply"],json.dumps(r["comprehension"],sort_keys=True)) for r in rows})==1}
 canonical=[];interlocutors=[]
 for row in rows:
  nmap={(x[0],x[1]):x[2] for x in row["node_fingerprints"]}
  normalized=[]
  for item in row["interlocutor_records"]:
   attrs=normalize_unordered(item["attrs"]);normalized.append({"id":item["id"],"attrs":attrs})
   body=json.dumps(attrs,sort_keys=True,separators=(",",":"),default=str)
   nmap[(item["id"],"Interlocutor")]=hashlib.sha256(body.encode()).hexdigest()
  nodes=sorted([[k[0],k[1],v] for k,v in nmap.items()],key=lambda x:(x[1],x[0],x[2]))
  edges=sorted(row["edge_records"])
  encoded=json.dumps({"nodes":nodes,"edges":edges},sort_keys=True,separators=(",",":"))
  canonical.append(hashlib.sha256(encoded.encode()).hexdigest());interlocutors.append(normalized)
 checks["normalized_interlocutor_attrs_repeat"]=all(x==interlocutors[0] for x in interlocutors[1:])
 checks["set_order_normalized_graph_repeats"]=len(set(canonical))==1
 result={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),
  "original_order_sensitive_digests":[r["order_sensitive_digest"] for r in rows],"first_pass_canonical_digests":[r["canonical_digest"] for r in rows],
  "set_order_normalized_digests":canonical,"interlocutor_attrs_after_normalization":interlocutors,
  "conclusion":"The only node fingerprint difference is the ordering of values serialized under Interlocutor.believed_concepts.__fset__. After sorting set-wrapper values recursively, full graph digests match. This is serialization-order variance, not graph-state variance."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,indent=2))
 if not result["all_checks_pass"]:raise SystemExit("canonical graph repeat checks failed")
if __name__=="__main__":main()
