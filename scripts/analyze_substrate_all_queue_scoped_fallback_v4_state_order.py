#!/usr/bin/env python3
"""Post-hoc separate graph-fact equality from edge insertion-order equality."""
from __future__ import annotations
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/all_queue_scoped_fallback_v4_workers_20261001.json"
OUT=ROOT/"evaluation/reports/all_queue_scoped_fallback_v4_state_order_20261001.json"
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
  full_selected=run["arms"]["full"].get("selected_mid");other_selected=run["arms"]["scoped_fallback"].get("selected_mid")
  full_nid=full_selected.get("__nid__") if isinstance(full_selected,dict) else None
  other_nid=other_selected.get("__nid__") if isinstance(other_selected,dict) else None
  full_slab_tail=next((e["tgt"] for e in reversed(full["edges"]) if e["type"]=="handled_mid"),None)
  other_slab_tail=next((e["tgt"] for e in reversed(other["edges"]) if e["type"]=="handled_mid"),None)
  rows.append({"rules":run["rules"],"multiplicity":run["multiplicity"],"replicate":run["replicate"],"node_array_equal":same_nodes,"edge_fact_multiset_equal":same_facts,"exact_graph_wire_equal":same_wire,"edge_count_full":len(full_edges),"first_edge_order_difference":first,"handled_mid_relative_order_equal":full_mid==other_mid,"matcher_selected_node_equal":full_nid==other_nid,"full_selection_matches_last_graph_slab_edge":full_nid==full_slab_tail,"fallback_selection_matches_last_graph_slab_edge":other_nid==other_slab_tail})
 result={"schema_version":1,"raw_sha256":sha(RAW),"source_lock":raw["locked_inputs"],"workers":len(rows),"node_array_equal_workers":nodes_equal,"canonical_graph_fact_equal_workers":fact_equal,"exact_wire_equal_workers":wire_equal,"matcher_selected_node_equal_workers":sum(x["matcher_selected_node_equal"] for x in rows),"full_selection_matches_graph_slab_tail_workers":sum(x["full_selection_matches_last_graph_slab_edge"] for x in rows),"fallback_selection_matches_graph_slab_tail_workers":sum(x["fallback_selection_matches_last_graph_slab_edge"] for x in rows),"rows":rows,"claim_boundary":"Post-hoc analysis of v4 graph dictionaries and the locked one-shot matcher result. Persistence iterates edge slabs, while the matcher reads edges_by_type and adjacency indexes. Comparing the selected match to the final slab edge is diagnostic only and does not represent matcher order."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(rows),"node_array_equal":nodes_equal,"canonical_graph_fact_equal":fact_equal,"exact_wire_equal":wire_equal,"handled_mid_order_equal":sum(x["handled_mid_relative_order_equal"] for x in rows),"matcher_selected_equal":result["matcher_selected_node_equal_workers"],"full_selection_matches_graph_slab_tail":result["full_selection_matches_graph_slab_tail_workers"]},indent=2))
if __name__=="__main__":main()
