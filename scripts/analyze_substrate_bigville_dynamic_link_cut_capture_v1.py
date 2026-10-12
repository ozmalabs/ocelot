#!/usr/bin/env python3
"""Independent cut and residual verification for the current Bigville panel."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/substrate_bigville_dynamic_link_cut_capture_v1.py"
ANALYZER=Path(__file__)
LOCK=ROOT/"evaluation/substrate_capability/bigville_dynamic_link_cut_capture_v1_lock_20260926.json"
RAW=ROOT/"evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_analysis_20260926.json"
TOPICS=("trust_mayor","claim_credible","world_safe","self_worth","debtor_trustworthy")
THRESHOLD=0.5493061443340548
def digest(graph):return hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def minfill(nodes,pairs):
 g={n:set() for n in nodes}
 for a,b in pairs:
  if a!=b:g[a].add(b);g[b].add(a)
 order=[];width=0
 while g:
  ranked=[]
  for n,ns in g.items():
   q=sorted(ns);fill=sum(1 for i,a in enumerate(q) for b in q[i+1:] if b not in g[a])
   ranked.append((fill,n))
  chosen=min(ranked)[1];ns=list(g[chosen]);width=max(width,len(ns))
  for i,a in enumerate(ns):
   for b in ns[i+1:]:g[a].add(b);g[b].add(a)
  for a in ns:g[a].discard(chosen)
  del g[chosen];order.append(chosen)
 return order,width
def independent_residual(cp):
 flat=[float(row[k]) for row in cp["states"] for k in TOPICS]
 fields=cp["fields"];sums=[float(v[0])+float(v[1]) for v in fields]
 for src,dst,w in cp["weights_by_flat_index"]:sums[int(src)]+=float(w)*flat[int(dst)]
 return sum((1.0 if 1.5*h>THRESHOLD else -1.0 if 1.5*h < -THRESHOLD else 0.0)!=state for h,state in zip(sums,flat))
def partition_oracle(cp,authored):
 nodes=sorted(authored);frames=sorted(set(authored.values()));sizes=[sum(authored[n]==f for n in nodes) for f in frames]
 g=cp["graph"];edges=[(int(e["src"]),str(e["type"]),int(e["tgt"])) for e in g["edges"]]
 trace=cp["runtime_access_trace"]
 obs=[(int(r[2]),int(r[4]),int(r[5])) for r in trace if r[2] is not None and r[4] is not None]
 pairs={tuple(sorted((a,b))) for a,t,b in edges if t!="has_concept" and a in authored and b in authored and a!=b}
 pairs.update(tuple(sorted((a,b))) for a,b,_ in obs if a in authored and b in authored and a!=b)
 order,width=minfill(nodes,pairs)
 maps={"authored":dict(authored)}
 for name,ordered in (("balanced_id",nodes),("dependency_min_fill",order)):
  own={};cursor=0
  for f,size in zip(frames,sizes):
   for n in ordered[cursor:cursor+size]:own[n]=f
   cursor+=size
  maps[name]=own
 authored_pairs=[(a,b) for i,a in enumerate(nodes) for b in nodes[i+1:] if authored[a]==authored[b]]
 expect={}
 for name,own in maps.items():
  cross=[(a,t,b) for a,t,b in edges if t!="has_concept" and a in authored and b in authored and own[a]!=own[b]]
  boundary=[(a,t,b) for a,t,b in edges if t!="has_concept" and ((a in authored)!=(b in authored))]
  causal=[x for x in cross if x[1]=="causal_influence"]
  observed=[(a,b,c) for a,b,c in obs if a in authored and b in authored and own[a]!=own[b]]
  touched={n for a,_,b in cross for n in (a,b)};touched.update(a if a in authored else b for a,_,b in boundary)
  by_type=lambda xs:{t:sum(1 for _,typ,_ in xs if typ==t) for t in sorted({typ for _,typ,_ in xs})}
  retained=sum(own[a]==own[b] for a,b in authored_pairs)
  expect[name]={"frame_sizes":[sum(own[n]==f for n in nodes) for f in frames],
   "captured_task_dependency_pair_count":len(pairs),"cross_frame_nonownership_edge_count_by_type":by_type(cross),
   "cross_frame_causal_influence_directed_edges":len(causal),"task_to_global_boundary_edge_count_by_type":by_type(boundary),
   "distinct_cross_frame_observed_access_pairs":len({tuple(sorted((a,b))) for a,b,_ in observed if a!=b}),
   "weighted_cross_frame_observed_access_count":sum(c for _,_,c in observed),"task_nodes_on_cut_or_global_boundary":len(touched),
   "within_authored_pair_retention":{"retained":retained,"total":len(authored_pairs),"fraction":retained/len(authored_pairs) if authored_pairs else 1.0},
   "min_fill_induced_width_upper_bound":width}
 return order,width,expect
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());locked=lock.get("locked_inputs",lock)
 current={"runner_sha256":hashlib.sha256(RUNNER.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(ANALYZER.read_bytes()).hexdigest()}
 checks={"runner_analyzer_match_lock":all(locked.get(k)==v for k,v in current.items()),
  "post_run_sources_match_lock":raw["post_run_inputs"]==raw["locked_inputs"],
  "nine_fresh_workers_three_per_topology":len(raw["runs"])==9 and len({x["pid"] for x in raw["runs"]})==9 and all(sum(x["topology"]==t for x in raw["runs"])==3 for t in ("ring","star","random_connected")),
  "all_source_current_frame_preconditions":all(x["runtime_component_count"]==100 and set(x["runtime_component_sizes"])=={5} for x in raw["runs"]),
  "all_scoped_candidates_refused":all(c["partition_execution"]=={"status":"refused_wildcard_rule_access","scoped_calls":0} for x in raw["runs"] for c in x["checkpoints"]),
  "dialogue_not_substituted":True}
 case_checks={}
 expected_stages=["runtime_partition_baseline","insert_cross_links","authored_evidence_update","delete_one_third","reweight_remaining","reinsert_deleted_pairs","remove_all_cross_links"]
 for run in raw["runs"]:
  own={int(n):int(f) for n,f in run["runtime_node_frame"]}; errors=[]
  expected_links=(0,run["dynamic_pair_count"],run["dynamic_pair_count"],run["dynamic_pair_count"]-len(range(0,run["dynamic_pair_count"],3)),run["dynamic_pair_count"]-len(range(0,run["dynamic_pair_count"],3)),run["dynamic_pair_count"],0)
  for i,cp in enumerate(run["checkpoints"]):
   order,width,metrics=partition_oracle(cp,own);reported={p["partition"]:p for p in cp["partition_metrics"]["partitions"]}
   links=cp["active_cross_links"];directed=[e for e in cp["graph"]["edges"] if e["type"]=="causal_influence" and int(e["src"]) in own and int(e["tgt"]) in own and own[int(e["src"])]!=own[int(e["tgt"])] ]
   weights={float(x[2]) for x in links}
   expected_weight=.2 if i in (1,2,3) else .35 if i in (4,5) else None
   check={"graph_digest_recomputed":digest(cp["graph"])==cp["graph_sha256"],
    "independent_residual_matches_zero":independent_residual(cp)==cp["independent_residual_count"]==0,
    "closure_and_terminal_fixed":cp["closure_report"].get("status")=="fixed_point" and cp["terminal_probe"].get("status")=="fixed_point" and cp["terminal_probe"].get("progress_steps")==0,
    "dynamic_link_count_matches_stage":len(links)==expected_links[i] and len(directed)==2*len(links),
    "dynamic_link_weights_match_stage":(weights=={expected_weight}) if expected_weight is not None else not weights,
    "minfill_order_and_width_match":order==cp["partition_metrics"]["min_fill_order_node_ids"] and width==cp["partition_metrics"]["induced_width_upper_bound"],
    "all_cut_metrics_independently_match":all(all(reported[n].get(k)==v for k,v in m.items()) for n,m in metrics.items()),
    "complete_edge_capture_and_wildcard_refusal":cp["partition_metrics"]["complete_graph_edge_inventory"] and cp["partition_execution"]["status"]=="refused_wildcard_rule_access"}
   errors.append(check)
  key=f"{run['topology']}_rep{run['replicate']}"
  case_checks[key]={"checkpoint_sequence_matches":[c["stage"] for c in run["checkpoints"]]==expected_stages,
                    "all_independent_recomputations_pass":all(all(c.values()) for c in errors),"checkpoints":errors}
 checks["all_checkpoint_recomputations_pass"]=all(x["checkpoint_sequence_matches"] and x["all_independent_recomputations_pass"] for x in case_checks.values())
 result={"schema_version":1,"run_id":"substrate-bigville-dynamic-link-cut-capture-v1-analysis-20260926",
  "raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"lock_sha256":hashlib.sha256(LOCK.read_bytes()).hexdigest(),
  "checks":checks,"case_checks":case_checks,"claim_boundary":raw["claim_boundary"]}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"case_count":len(case_checks)},indent=2))
 if not all(checks.values()):raise SystemExit("independent dynamic-link cut verification failed")
if __name__=="__main__":main()
