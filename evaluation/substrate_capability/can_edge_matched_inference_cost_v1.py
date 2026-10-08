#!/usr/bin/env python3
"""Exact MAP cost on edge-matched grids and sparse partial q-trees."""
from __future__ import annotations
import hashlib,importlib.util,itertools,json,os,platform,random,resource,statistics,subprocess,sys,time,tracemalloc
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_EDGE_MATCHED_INFERENCE_COST_V1_PREREG_20260929.md"
RUNNER=Path(__file__).resolve()
GENERATOR=ROOT/"evaluation/substrate_capability/can_edge_matched_width_topology_v1.py"
AMENDMENT=ROOT/"docs/research/engine_substrate/CAN_EDGE_MATCHED_INFERENCE_COST_V1_1_AMENDMENT_20260929.md"
AMENDMENT_V1_2=ROOT/"docs/research/engine_substrate/CAN_EDGE_MATCHED_INFERENCE_COST_V1_2_AMENDMENT_20260929.md"
LOCK=ROOT/"evaluation/substrate_capability/can_edge_matched_inference_cost_v1_2_lock_20260929.json"
OUT=ROOT/"evaluation/reports/can_edge_matched_inference_cost_v1_2_20260929.json"
WIDTHS=(4,5,6); N=120; REPLICATES=6; FAMILIES=("grid","sparse_partial_qtree"); VOCAB=(-1.0,1.0)
SOURCES=("domains/can_junction_tree.py","domains/graph_treewidth.py",
 "runners/dsl/python/substrate_rs/_native.abi3.so","runners/dsl/python/substrate_rs/_native.build.json")
_spec=importlib.util.spec_from_file_location("edge_generator",GENERATOR)
GEN=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(GEN)

def digest(path):
 raw=path.read_bytes(); return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def input_lock():
 return {"schema_version":1,"protocol":digest(PROTOCOL),"amendments":[digest(AMENDMENT),digest(AMENDMENT_V1_2)],"runner":digest(RUNNER),"generator":digest(GENERATOR),
  "sources":[digest(ROOT/p) for p in SOURCES],"widths":list(WIDTHS),"nodes":N,"replicates":REPLICATES,
  "families":list(FAMILIES),"vocabulary":list(VOCAB),"git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def fixture(q,family,rep):
 seed=20260929+q*1000003+FAMILIES.index(family)*10007+rep*65537
 rng=random.Random(seed); grid_edges,grid_order=GEN.grid(q)
 if family=="grid": edges,cert=grid_edges,grid_order
 else: edges,cert=GEN.sparse_partial_qtree(q,rng,len(grid_edges))
 labels=list(range(N)); rng.shuffle(labels); remap={u:labels[u] for u in range(N)}
 edges=[tuple(sorted((remap[a],remap[b]))) for a,b in edges]; rng.shuffle(edges)
 nodes=list(range(N)); rng.shuffle(nodes); cert=[remap[v] for v in cert]
 # Potentials are deterministic by final node ids, independent from the graph generator's RNG.
 prng=random.Random(0xC0FFEE+q*100003+rep*503)
 unary={i:prng.randint(-8,8)/4.0 for i in range(N)}
 pair={edge:prng.randint(-8,8)/4.0 for edge in sorted(edges)}
 return seed,nodes,edges,cert,unary,pair,len(grid_edges)

def factor_oracle(order,unary,pair):
 """Independent generic min-sum variable elimination over explicit factor tables."""
 factors=[]; operations=0
 for v,h in unary.items(): factors.append(((v,),{(-1.0,):h, (1.0,):-h}))
 for (a,b),w in pair.items():
  factors.append(((a,b),{(x,y):-w*x*y for x in VOCAB for y in VOCAB}))
 for v in order:
  bucket=[f for f in factors if v in f[0]]
  factors=[f for f in factors if v not in f[0]]
  scope=tuple(sorted(set().union(*(set(s) for s,_ in bucket))))
  rest=tuple(x for x in scope if x!=v); table={}
  for values in itertools.product(VOCAB,repeat=len(rest)):
   partial=dict(zip(rest,values)); best=float("inf")
   for sigma in VOCAB:
    assignment={**partial,v:sigma}; total=0.0
    for fscope,ftable in bucket:
     total+=ftable[tuple(assignment[x] for x in fscope)]
    operations+=len(bucket)
    if total<best: best=total
   table[values]=best
  factors.append((rest,table))
 result=0.0
 for scope,table in factors:
  if scope: raise AssertionError("oracle left a nonconstant factor")
  result+=table[()]
 return result,operations

def direct_energy(state,unary,pair):
 return -sum(h*state[i] for i,h in unary.items())-sum(w*state[a]*state[b] for (a,b),w in pair.items())

def timed_map(cjt,nodes,edges,unary,pair,order):
 tracemalloc.start(); wall=time.perf_counter_ns(); cpu=time.process_time_ns()
 result=cjt.junction_tree_map(nodes,edges,unary,{frozenset(k):v for k,v in pair.items()},VOCAB,order=order)
 cpu_ns=time.process_time_ns()-cpu; wall_ns=time.perf_counter_ns()-wall
 _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
 return result,wall_ns,cpu_ns,peak

def decomposition_profile(nodes,edges,order):
 from collections import Counter
 from domains.graph_treewidth import build_elimination_triangulation
 tri=build_elimination_triangulation(nodes,edges,order)
 bags=tri["bags"]; parent=tri["parent"]
 children={v:0 for v in nodes}
 for v,p in parent.items():
  if p is not None: children[p]+=1
 bag_sizes={v:len(bags[v]) for v in nodes}
 sep_sizes={v:bag_sizes[v]-1 for v in nodes}
 return {"bag_size_histogram":{str(k):v for k,v in sorted(Counter(bag_sizes.values()).items())},
  "separator_size_histogram":{str(k):v for k,v in sorted(Counter(sep_sizes.values()).items())},
  "child_count_histogram":{str(k):v for k,v in sorted(Counter(children.values()).items())},
  "max_bag_size":max(bag_sizes.values(),default=0),
  "message_entries":sum(2**size for size in sep_sizes.values()),
  "bag_assignments":sum(2**size for size in bag_sizes.values()),
  "estimated_inner_loop_iterations":sum(len(VOCAB)*(2**sep_sizes[v])*(1+children[v]) for v in nodes),
  "estimated_local_energy_term_visits":sum(len(VOCAB)*(2**sep_sizes[v])*bag_sizes[v] for v in nodes)}

def worker(q,family,rep):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound,build_elimination_triangulation
 seed,nodes,edges,cert,unary,pair,expected_edges=fixture(q,family,rep)
 start=time.perf_counter_ns(); s=sr.Substrate(); inner=s._inner
 mt=inner.add_node("Microtheory",{"discrete_mode":"2state"})
 handles={i:inner.add_node("Concept",{"name":f"x{i}","external_field":unary[i],"identity_field":0.0,"state":0.0}) for i in nodes}
 for node in handles.values(): inner.add_edge_unchecked(mt,"has_concept",node,{})
 for (a,b),w in pair.items():
  inner.add_edge_unchecked(handles[a],"causal_influence",handles[b],{"weight":w})
  inner.add_edge_unchecked(handles[b],"causal_influence",handles[a],{"weight":w})
 construction_ns=time.perf_counter_ns()-start
 start=time.perf_counter_ns(); net=cjt.can_network_from_mt(s,mt); extract_ns=time.perf_counter_ns()-start
 actual_to_fixture={handle.value:i for i,handle in handles.items()}
 actual_unary={actual_to_fixture[i]:v for i,v in net["unary"].items()}
 actual_pair={tuple(sorted(actual_to_fixture[i] for i in edge)):v for edge,v in net["pairwise"].items()}
 exact_extraction=actual_unary==unary and actual_pair==pair
 ids=list(net["nodes"]); graph_edges=[tuple(x) for x in net["edges"]]
 engine_unary=dict(net["unary"]); engine_pair=dict(net["pairwise"])
 cert_native=[handles[i].value for i in cert]
 start=time.perf_counter_ns(); mf=min_fill_upper_bound(ids,graph_edges); minfill_ns=time.perf_counter_ns()-start
 tri=build_elimination_triangulation(ids,graph_edges,cert_native)
 certificate_width=max((len(b)-1 for b in tri["bags"].values()),default=0)
 minfill_profile=decomposition_profile(ids,graph_edges,mf["elimination_order"])
 certificate_profile=decomposition_profile(ids,graph_edges,cert_native)
 oracle_start=time.perf_counter_ns(); oracle,oracle_ops=factor_oracle(cert,unary,pair); oracle_ns=time.perf_counter_ns()-oracle_start
 states_before={i:float(inner.node(handles[i])["attrs"].get("state",0)) for i in nodes}
 mf_result,mf_wall,mf_cpu,mf_peak=timed_map(cjt,ids,graph_edges,engine_unary,engine_pair,mf["elimination_order"])
 cert_result,cert_wall,cert_cpu,cert_peak=timed_map(cjt,ids,graph_edges,engine_unary,engine_pair,cert_native)
 mf_energy=direct_energy({actual_to_fixture[i]:v for i,v in mf_result["state"].items()},unary,pair)
 cert_energy=direct_energy({actual_to_fixture[i]:v for i,v in cert_result["state"].items()},unary,pair)
 states_after={i:float(inner.node(handles[i])["attrs"].get("state",0)) for i in nodes}
 return {"width":q,"family":family,"replicate":rep,"seed":seed,"nodes":len(ids),"edges":len(graph_edges),"expected_edges":expected_edges,
  "extraction_exact":exact_extraction,"certificate_width":certificate_width,"minfill_width":mf["treewidth"],
  "minfill_bag_size":mf_result["max_bag_size"],"certificate_bag_size":cert_result["max_bag_size"],
  "decomposition_profiles":{"minfill":minfill_profile,"certificate":certificate_profile},
  "oracle_energy":oracle,"minfill_energy":mf_result["energy"],"certificate_energy":cert_result["energy"],
  "minfill_direct_energy":mf_energy,"certificate_direct_energy":cert_energy,
  "oracle_operations":oracle_ops,"no_mutation":states_before==states_after,
  "timing_ns":{"graph_construction":construction_ns,"runtime_extraction":extract_ns,"minfill_order":minfill_ns,
    "oracle":oracle_ns,"jt_minfill_wall":mf_wall,"jt_minfill_cpu":mf_cpu,
    "jt_certificate_wall":cert_wall,"jt_certificate_cpu":cert_cpu},
  "traced_peak_bytes":{"jt_minfill":mf_peak,"jt_certificate":cert_peak},
  "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}

def main():
 if len(sys.argv)==5 and sys.argv[1]=="--worker":
  print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],int(sys.argv[4])),sort_keys=True)); return
 OUT.parent.mkdir(parents=True,exist_ok=True)
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite lock/capture")
  LOCK.write_text(json.dumps(input_lock(),indent=2,sort_keys=True)+"\n"); print(LOCK.relative_to(ROOT)); return
 lock=json.loads(LOCK.read_text())
 if input_lock()!=lock: raise SystemExit("source/fixture lock drift")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale: raise SystemExit("native build stale:\n"+"\n".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"}
 rows=[]
 for q in WIDTHS:
  for rep in range(REPLICATES):
   for family in FAMILIES:
    p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(q),family,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
    row=json.loads(p.stdout.strip()); rows.append(row)
    print(f"q={q} family={family} rep={rep} width_mf={row['minfill_width']} oracle_ms={row['timing_ns']['oracle']/1e6:.2f} "
      f"JTmf_ms={row['timing_ns']['jt_minfill_wall']/1e6:.2f} JTcert_ms={row['timing_ns']['jt_certificate_wall']/1e6:.2f}",flush=True)
 post=input_lock()
 checks={"complete_workers":len(rows)==36,
  "coverage":all(sum(r["width"]==q and r["family"]==f for r in rows)==REPLICATES for q in WIDTHS for f in FAMILIES),
  "paired_node_edge_sizes":all(r["nodes"]==N and r["edges"]==r["expected_edges"] for r in rows),
  "exact_extraction":all(r["extraction_exact"] for r in rows),
  "certificate_width_q":all(r["certificate_width"]==r["width"] for r in rows),
  "profile_widths_reconcile":all(r["decomposition_profiles"]["minfill"]["max_bag_size"]==r["minfill_bag_size"] and
    r["decomposition_profiles"]["certificate"]["max_bag_size"]==r["certificate_bag_size"] for r in rows),
  "minfill_oracle_match":all(abs(r["minfill_direct_energy"]-r["oracle_energy"])<1e-8 and abs(r["minfill_energy"]-r["oracle_energy"])<1e-8 for r in rows),
  "certificate_oracle_match":all(abs(r["certificate_direct_energy"]-r["oracle_energy"])<1e-8 and abs(r["certificate_energy"]-r["oracle_energy"])<1e-8 for r in rows),
  "no_mutation":all(r["no_mutation"] for r in rows),"pre_post_lock_match":lock==post}
 payload={"schema_version":1,"run_id":"can-edge-matched-inference-cost-v1.2-20260929","status":"complete",
  "input_lock":lock,"post_run_input_lock":post,"configuration":{"widths":WIDTHS,"nodes":N,"replicates":REPLICATES,"families":FAMILIES},
  "claim_boundary":"exact MAP and cost on two edge-matched synthetic graph families only",
  "environment":{"python":platform.python_version(),"platform":platform.platform()},"checks":checks,"runs":rows}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"checks":checks},indent=2))
 if not all(checks.values()): raise SystemExit("edge matched inference integrity failure")

if __name__=="__main__": main()
