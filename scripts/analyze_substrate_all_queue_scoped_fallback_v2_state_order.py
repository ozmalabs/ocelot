#!/usr/bin/env python3
"""Post-hoc separate graph-fact equality from edge insertion-order equality."""
from __future__ import annotations
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/all_queue_scoped_fallback_v2_workers_20261001.json"
OUT=ROOT/"evaluation/reports/all_queue_scoped_fallback_v2_state_order_20261001.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edge_key(edge):return (int(edge["src"]),str(edge["type"]),int(edge["tgt"]),json.dumps(edge["attrs"],sort_keys=True,separators=(",",":")))
def main():
 raw=json.loads(RAW.read_text());rows=[];wire_equal=0;fact_equal=0;nodes_equal=0
 for run in raw["runs"]:
  full=run["arms"]["full"]["graph"];other=run["arms"]["scoped_fallback"]["graph"]
  same_nodes=full["nodes"]==other["nodes"];same_wire=full==other
  full_edges=[edge_key(e) for e in full["edges"]];other_edges=[edge_key(e) for e in other["edges"]]
  same_facts=collections.Counter(full_edges)==collections.Counter(other_edges)
  nodes_equal+=same_nodes;wire_equal+=same_wire;fact_equal+=same_nodes and same_facts
  first=next((i for i,(a,b) in enumerate(zip(full_edges,other_edges)) if a!=b),None)
  full_mid=[key for key in full_edges if key[1]=="handled_mid"];other_mid=[key for key in other_edges if key[1]=="handled_mid"]
  rows.append({"rules":run["rules"],"multiplicity":run["multiplicity"],"replicate":run["replicate"],"node_array_equal":same_nodes,"edge_fact_multiset_equal":same_facts,"exact_graph_wire_equal":same_wire,"edge_count_full":len(full_edges),"first_edge_order_difference":first,"handled_mid_relative_order_equal":full_mid==other_mid})
 result={"schema_version":1,"raw_sha256":sha(RAW),"source_lock":raw["locked_inputs"],"workers":len(rows),"node_array_equal_workers":nodes_equal,"canonical_graph_fact_equal_workers":fact_equal,"exact_wire_equal_workers":wire_equal,"rows":rows,"claim_boundary":"Post-hoc analysis of the v2 captured final graph dictionaries. Canonical fact equality sorts edge facts and does not show that insertion order is operationally irrelevant. No order-sensitive continuation was measured."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(rows),"node_array_equal":nodes_equal,"canonical_graph_fact_equal":fact_equal,"exact_wire_equal":wire_equal,"handled_mid_order_equal":sum(x["handled_mid_relative_order_equal"] for x in rows)},indent=2))
if __name__=="__main__":main()
