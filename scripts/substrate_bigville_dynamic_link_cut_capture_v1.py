#!/usr/bin/env python3
"""Fresh current-source Bigville dynamic-link graph/cut capture."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, random, resource, statistics, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTO=ROOT/"docs/research/engine_substrate/SUBSTRATE_BIGVILLE_DYNAMIC_LINK_CUT_CAPTURE_V1_PREREG_20260926.md"
BASE=ROOT/"scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
CAST=ROOT/"seeds/bigville_cast100.json"; SEED=ROOT/"seeds/can_native_reimplementation.json"
BUILDER=ROOT/"worlds/bigville_can_beliefs.py"
LOCK=ROOT/"evaluation/substrate_capability/bigville_dynamic_link_cut_capture_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json"
ANALYZER=ROOT/"scripts/analyze_substrate_bigville_dynamic_link_cut_capture_v1.py"
TOPOLOGIES=("ring","star","random_connected"); REPS=3; TARGETS=tuple(range(0,100,10)); CAP=100_000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x): return int(x.value if hasattr(x,"value") else x)
def load_base():
 spec=importlib.util.spec_from_file_location("dynamic_cut_capture_base",BASE)
 if spec is None or spec.loader is None: raise RuntimeError("cannot import frozen Bigville builder")
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def locked_inputs():
 from substrate_rs import _native
 native=Path(_native.__file__).resolve()
 return {"protocol_sha256":sha(PROTO),"runner_sha256":sha(Path(__file__)),"analyzer_sha256":sha(ANALYZER),
  "base_runner_sha256":sha(BASE),"cast_sha256":sha(CAST),"seed_sha256":sha(SEED),"builder_sha256":sha(BUILDER),
  "native_extension_sha256":sha(native),"native_extension_path":str(native),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "cargo_lock_sha256":sha(ROOT/"runners/dsl/Cargo.lock"),
  "rust_sources_sha256":{n:sha(ROOT/"runners/dsl/src"/n) for n in ("graph.rs","rewrite.rs","substrate.rs","term.rs","access_trace.rs","py.rs")}}

def topology_pairs(topology,rep,count=100):
 if topology=="ring": return [(i,(i+1)%count) for i in range(count)]
 if topology=="star": return [(0,i) for i in range(1,count)]
 rng=random.Random(20260925+rep*1009); pairs=[]
 for child in range(1,count): pairs.append((rng.randrange(child),child))
 have={tuple(sorted(x)) for x in pairs}
 candidates=[(i,j) for i in range(count) for j in range(i+1,count) if (i,j) not in have]
 rng.shuffle(candidates); pairs.extend(candidates[:count-len(pairs)])
 return pairs

def minfill(nodes,pairs):
 g={n:set() for n in nodes}
 for a,b in pairs:
  if a!=b: g[a].add(b);g[b].add(a)
 order=[];width=0
 while g:
  ranked=[]
  for n,ns in g.items():
   q=sorted(ns); fill=sum(1 for i,a in enumerate(q) for b in q[i+1:] if b not in g[a])
   ranked.append((fill,n))
  chosen=min(ranked)[1]; ns=list(g[chosen]);width=max(width,len(ns))
  for i,a in enumerate(ns):
   for b in ns[i+1:]:g[a].add(b);g[b].add(a)
  for a in ns:g[a].discard(chosen)
  del g[chosen];order.append(chosen)
 return order,width

def partition_capture(graph, authored, trace_rows):
 started_wall=time.perf_counter_ns();started_cpu=time.process_time_ns()
 task=set(authored); nodes=sorted(task); frames=sorted(set(authored.values()))
 sizes=[sum(authored[n]==f for n in nodes) for f in frames]
 edges=[(int(e["src"]),str(e["type"]),int(e["tgt"])) for e in graph["edges"]]
 obs=[(int(r[2]),int(r[4]),int(r[5])) for r in trace_rows if r[2] is not None and r[4] is not None]
 dep_pairs={tuple(sorted((a,b))) for a,t,b in edges if t!="has_concept" and a in task and b in task and a!=b}
 dep_pairs.update(tuple(sorted((a,b))) for a,b,_ in obs if a in task and b in task and a!=b)
 order,width=minfill(nodes,dep_pairs)
 owners={"authored":dict(authored)}
 for name,ordered in (("balanced_id",nodes),("dependency_min_fill",order)):
  owner={};cursor=0
  for f,size in zip(frames,sizes):
   for n in ordered[cursor:cursor+size]:owner[n]=f
   cursor+=size
  owners[name]=owner
 authored_pairs=[(a,b) for i,a in enumerate(nodes) for b in nodes[i+1:] if authored[a]==authored[b]]
 results=[]
 for name,owner in owners.items():
  cross=[(a,t,b) for a,t,b in edges if t!="has_concept" and a in task and b in task and owner[a]!=owner[b]]
  boundary=[(a,t,b) for a,t,b in edges if t!="has_concept" and ((a in task)!=(b in task))]
  causal=[x for x in cross if x[1]=="causal_influence"]
  observed=[(a,b,c) for a,b,c in obs if a in task and b in task and owner[a]!=owner[b]]
  touched={n for a,_,b in cross for n in (a,b)};touched.update(a if a in task else b for a,_,b in boundary)
  retained=sum(owner[a]==owner[b] for a,b in authored_pairs)
  count=lambda xs:{t:sum(1 for _,typ,_ in xs if typ==t) for t in sorted({typ for _,typ,_ in xs})}
  results.append({"partition":name,"frame_sizes":[sum(owner[n]==f for n in nodes) for f in frames],
   "captured_task_dependency_pair_count":len(dep_pairs),"cross_frame_nonownership_edge_count_by_type":count(cross),
   "cross_frame_causal_influence_directed_edges":len(causal),"task_to_global_boundary_edge_count_by_type":count(boundary),
   "distinct_cross_frame_observed_access_pairs":len({tuple(sorted((a,b))) for a,b,_ in observed if a!=b}),
   "weighted_cross_frame_observed_access_count":sum(c for _,_,c in observed),
   "task_nodes_on_cut_or_global_boundary":len(touched),"within_authored_pair_retention":{"retained":retained,"total":len(authored_pairs),"fraction":retained/len(authored_pairs) if authored_pairs else 1.0},
   "min_fill_induced_width_upper_bound":width})
 static_any=[]
 return {"partition_rebuild_wall_ns":time.perf_counter_ns()-started_wall,
  "partition_rebuild_cpu_ns":time.process_time_ns()-started_cpu,"min_fill_order_node_ids":order,
  "dependency_pair_count":len(dep_pairs),"induced_width_upper_bound":width,"partitions":results,
  "complete_graph_edge_inventory":True,"ownership_link_count_excluded":sum(1 for _,t,_ in edges if t=="has_concept"),
  "runtime_access_trace_is_partial":True}

def worker(topology,rep):
 import substrate_rs as sr
 from substrate_rs import _native
 from worlds import bigville_can_beliefs as bigville
 base=load_base(); cast=json.loads(CAST.read_text())["residents"]; seed=json.loads(SEED.read_text())
 t0=time.perf_counter_ns()
 (outer,inner,residents,mts,concepts,frame_nodes,node_frame,edges,cross,ref_by_id,node_flat)=base.build(sr,cast,seed,bigville)
 build_ns=time.perf_counter_ns()-t0
 if len(frame_nodes)!=100 or set(map(len,frame_nodes))!={5} or cross:raise RuntimeError("runtime Bigville frame precondition failed")
 rule_rows=[r for r in inner.rule_access_sets() if r[2] and r[1]=="can_native_update_3state"]
 if len(rule_rows)!=1:raise RuntimeError("expected one active CAN update rule")
 reads_any=bool(rule_rows[0][6]); weights=base.weights_by_id(concepts,residents,bigville,node_flat)
 all_pairs=topology_pairs(topology,rep); removed=all_pairs[::3]; active={}; checkpoints=[]
 def add(pair,value):
  l,r=pair; a=concepts[l]["world_safe"];b=concepts[r]["world_safe"]; ai,bi=base.nid(a),base.nid(b)
  inner.add_edge_unchecked(a,"causal_influence",b,{"weight":value});inner.add_edge_unchecked(b,"causal_influence",a,{"weight":value})
  active[pair]={"left_id":ai,"right_id":bi,"left_flat":node_flat[ai],"right_flat":node_flat[bi],"weight":value}
  for x,y in ((ai,bi),(bi,ai)):
   pairflat=(node_flat[x],node_flat[y]);weights[:]=[z for z in weights if z[:2]!=pairflat];weights.append((pairflat[0],pairflat[1],value))
 def delete(pair):
  rec=active.pop(pair);a=ref_by_id[rec["left_id"]];b=ref_by_id[rec["right_id"]]
  inner.remove_edge_unchecked(a,"causal_influence",b);inner.remove_edge_unchecked(b,"causal_influence",a)
  keys={(rec["left_flat"],rec["right_flat"]),(rec["right_flat"],rec["left_flat"])}
  weights[:]=[z for z in weights if z[:2] not in keys]
 def settle(stage,mutation_ns):
  inner.runtime_access_trace_reset();inner.runtime_access_trace_set_enabled(True)
  wall,cpu=time.perf_counter_ns(),time.process_time_ns();sweep=base.settle_full(inner,mts,audit=True)
  wall_ns=time.perf_counter_ns()-wall;cpu_ns=time.process_time_ns()-cpu
  report={"status":"fixed_point" if sweep["complete"] else "budget_exhausted",
          "progress_steps":int(sweep["steps"]),"rounds":int(sweep["rounds"]),"turns":int(sweep["turns"]),
          "audit":{str(k):int(v) for k,v in sweep["audit"].items()}}
  inner.runtime_access_trace_set_enabled(False)
  counters=report["audit"]
  trace,dropped=inner.runtime_access_trace_snapshot();graph=inner.graph_to_dict()
  states=base.states(inner,concepts);fields=base.fields(inner,concepts);residual=base.residuals(states,fields,weights)
  part=partition_capture(graph,node_frame,trace)
  terminal_sweep=base.settle_full(inner,mts,audit=False)
  terminal={"status":"fixed_point" if terminal_sweep["complete"] else "budget_exhausted",
            "progress_steps":int(terminal_sweep["steps"]),"rounds":int(terminal_sweep["rounds"]),
            "turns":int(terminal_sweep["turns"])}
  digest=hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
  checkpoints.append({"stage":stage,"mutation_ns":mutation_ns,"closure_wall_ns":wall_ns,"closure_cpu_ns":cpu_ns,
   "closure_report":report,"audit_counters":counters,"terminal_probe":terminal,"states":states,"fields":fields,
   "weights_by_flat_index":[list(z) for z in weights],"independent_residual_count":sum(residual),
   "graph_sha256":digest,"graph":graph,"trace_dropped":int(dropped),
   "runtime_access_trace":[[int(x[0]),str(x[1]),x[2],x[3],x[4],int(x[5])] for x in trace],
   "partition_metrics":part,"partition_execution":{"status":"refused_wildcard_rule_access" if reads_any else "not_attempted","scoped_calls":0},
   "active_cross_links":[[a,b,rec["weight"]] for (a,b),rec in sorted(active.items())]})
 initial=base.settle_full(inner,mts,audit=False)
 if not initial["complete"]:raise RuntimeError("baseline all-owner sweep failed")
 settle("runtime_partition_baseline",0)
 started=time.perf_counter_ns()
 for pair in all_pairs:add(pair,0.2)
 settle("insert_cross_links",time.perf_counter_ns()-started)
 started=time.perf_counter_ns()
 for target in TARGETS:base.mutate(inner,concepts,residents,bigville,target)
 settle("authored_evidence_update",time.perf_counter_ns()-started)
 started=time.perf_counter_ns()
 for pair in removed:delete(pair)
 settle("delete_one_third",time.perf_counter_ns()-started)
 started=time.perf_counter_ns(); remain=list(active)
 for pair in remain:delete(pair);add(pair,0.35)
 settle("reweight_remaining",time.perf_counter_ns()-started)
 started=time.perf_counter_ns()
 for pair in removed:add(pair,0.35)
 settle("reinsert_deleted_pairs",time.perf_counter_ns()-started)
 started=time.perf_counter_ns()
 for pair in list(active):delete(pair)
 settle("remove_all_cross_links",time.perf_counter_ns()-started)
 return {"topology":topology,"replicate":rep,"pid":os.getpid(),"runtime_component_count":len(frame_nodes),
  "runtime_component_sizes":[len(x) for x in frame_nodes],"runtime_node_frame":[[int(n),int(f)] for n,f in sorted(node_frame.items())],
  "target_rule_reads_any":reads_any,"build_wall_ns":build_ns,"dynamic_pair_count":len(all_pairs),
  "removed_pair_count":len(removed),"checkpoints":checkpoints,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  "native_extension_sha256":sha(Path(_native.__file__).resolve())}

def main():
 if len(sys.argv)==4 and sys.argv[1]=="--worker":
  print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True));return
 locked=locked_inputs()
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":locked},indent=2,sort_keys=True));return
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}";env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[(t,r) for t in TOPOLOGIES for r in range(REPS)];random.Random(20260926).shuffle(jobs);runs=[]
 for t,r in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",t,str(r)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=240)
  x=json.loads(p.stdout);runs.append(x);print(f"{t} replicate={r} checkpoints={len(x['checkpoints'])} pid={x['pid']}",flush=True)
 post=locked_inputs()
 checks={"nine_fresh_workers":len(runs)==9 and len({x['pid'] for x in runs})==9,
  "three_replicates_per_topology":all(sum(x['topology']==t for x in runs)==3 for t in TOPOLOGIES),
  "locked_sources_stable":post==locked,
  "100_runtime_five_concept_frames":all(x['runtime_component_count']==100 and set(x['runtime_component_sizes'])=={5} for x in runs),
  "seven_checkpoints_each":all(len(x['checkpoints'])==7 for x in runs),
  "all_full_fixed_points_and_residuals_zero":all(c['closure_report'].get('status')=='fixed_point' and c['terminal_probe'].get('status')=='fixed_point' and c['terminal_probe'].get('progress_steps')==0 and c['independent_residual_count']==0 for x in runs for c in x['checkpoints']),
  "all_alternative_partition_arms_refuse":all(c['partition_execution']=={"status":"refused_wildcard_rule_access","scoped_calls":0} for x in runs for c in x['checkpoints'])}
 out={"schema_version":1,"run_id":"substrate-bigville-dynamic-link-cut-capture-v1-20260926","status":"source_current_structural_capture_partition_execution_refused",
  "locked_inputs":locked,"post_run_inputs":post,"checks":checks,"configuration":{"topologies":TOPOLOGIES,"replicates":REPS,"checkpoint_order":["runtime_partition_baseline","insert_cross_links","authored_evidence_update","delete_one_third","reweight_remaining","reinsert_deleted_pairs","remove_all_cross_links"]},
  "claim_boundary":"Fresh complete-graph cut reconstruction across the old dynamic-link mutation seam. Generated topology only. Candidate partitions refuse on reads_any; no candidate speed/parity claim.","runs":runs}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("dynamic-link cut capture gate failed; preserve raw")

if __name__=="__main__":main()
