#!/usr/bin/env python3
"""Source-locked whole-cast exact MAP vs graph-discovered component MAP."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_BIGVILLE_AGGREGATE_COMPONENT_INFERENCE_PREREG_20260926.md"
CAST=ROOT/"seeds/bigville_cast100.json";BUILDER=ROOT/"worlds/bigville_can_beliefs.py"
SOURCES={"jt":ROOT/"domains/can_junction_tree.py","width":ROOT/"domains/graph_treewidth.py","graph_rs":ROOT/"runners/dsl/src/graph.rs","py_rs":ROOT/"runners/dsl/src/py.rs"}
LOCK=ROOT/"evaluation/substrate_capability/bigville_aggregate_component_inference_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_bigville_aggregate_component_inference_v1_20260926.json"
SIZES=(10,25,50,100);BETA=1.5;TOL=1e-7;ARM_ORDERS=(("global","components"),("components","global"),("global","components"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"cast_sha256":sha(CAST),"builder_sha256":sha(BUILDER),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def independent_energy(unary,pairwise,state):
 total=-sum(float(h)*float(state[i]) for i,h in unary.items())
 for pair,w in pairwise.items():
  i,j=tuple(pair);total-=float(w)*float(state[i])*float(state[j])
 return total
def discover_components(nodes,edges):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 unseen=set(nodes);out=[]
 while unseen:
  root=min(unseen);stack=[root];unseen.remove(root);comp=[]
  while stack:
   v=stack.pop();comp.append(v)
   for u in sorted(adj[v]):
    if u in unseen:unseen.remove(u);stack.append(u)
  out.append(sorted(comp))
 return out
def exhaustive_component(nodes,unary,pairwise,vocab):
 import itertools,math
 best=math.inf;best_state=None;checked=0
 for values in itertools.product(vocab,repeat=len(nodes)):
  state=dict(zip(nodes,values));energy=independent_energy(unary,pairwise,state);checked+=1
  if energy<best:best,best_state=energy,state
 return best,best_state,checked
def run_case(n,rep,arm_order):
 import substrate_rs as sr
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound
 from worlds import bigville_can_beliefs as bv
 started=lock_inputs();cast=json.loads(CAST.read_text())["residents"][:n]
 s=sr.Substrate();inner=s._inner;bv.install_productions(inner);locals_=[];all_concepts=[]
 t0=time.perf_counter_ns()
 for resident in cast:
  built=bv.build_resident_can_mt(inner,resident,beta=BETA);mt=built["mt_node"]
  bv.apply_scenario_evidence(inner,built["concepts"]);inner.set_attr(mt,"discrete_mode","3state");inner.set_attr(mt,"can_tick",0.0)
  all_concepts.extend(built["concepts"].values())
  locals_.append(cjt.can_network_from_mt(inner,mt))
 aggregate=inner.add_node("Microtheory",{"name":"bigville_aggregate","discrete_mode":"3state","temperature":BETA})
 for concept in all_concepts:inner.add_edge_unchecked(aggregate,"has_concept",concept,{})
 setup_extract_ns=time.perf_counter_ns()-t0
 t0=time.perf_counter_ns();net=cjt.can_network_from_mt(inner,aggregate);global_extract_ns=time.perf_counter_ns()-t0
 local_nodes=[v for q in locals_ for v in q["nodes"]];local_edges=[e for q in locals_ for e in q["edges"]]
 local_unary={k:v for q in locals_ for k,v in q["unary"].items()};local_pairwise={k:v for q in locals_ for k,v in q["pairwise"].items()}
 extraction_union_exact=(set(local_nodes)==set(net["nodes"]) and set(local_edges)==set(net["edges"]) and local_unary==net["unary"] and local_pairwise==net["pairwise"])
 components=discover_components(net["nodes"],net["edges"])
 def global_solve():
  width=min_fill_upper_bound(net["nodes"],net["edges"])
  answer=cjt.junction_tree_map(net["nodes"],net["edges"],net["unary"],net["pairwise"],net["vocab"],order=width["elimination_order"])
  return width,answer
 def component_solve():
  states={};checked=0;component_energies=[];sizes=[];pairs_per_component=[]
  for comp in discover_components(net["nodes"],net["edges"]):
   cset=set(comp);pairs={k:v for k,v in net["pairwise"].items() if k.issubset(cset)};unary={v:net["unary"][v] for v in comp}
   e,state,count=exhaustive_component(comp,unary,pairs,net["vocab"]);states.update(state);checked+=count;component_energies.append(e);sizes.append(len(comp));pairs_per_component.append(len(pairs))
  return {"state":states,"energy":sum(component_energies),"states_checked":checked,"component_sizes":sizes,"pairs_per_component":pairs_per_component}
 answers={};times={}
 for name in arm_order:
  t0=time.perf_counter_ns();answers[name]=global_solve() if name=="global" else component_solve();times[name]=time.perf_counter_ns()-t0
 gw,global_answer=answers["global"];component_answer=answers["components"]
 global_energy=independent_energy(net["unary"],net["pairwise"],global_answer["state"])
 component_energy=independent_energy(net["unary"],net["pairwise"],component_answer["state"])
 post=lock_inputs()
 return {"n_residents":n,"replicate":rep,"arm_order":arm_order,"nodes":len(net["nodes"]),"undirected_pairs":len(net["pairwise"]),"discovered_component_count":len(components),"discovered_component_sizes":[len(c) for c in components],"discovered_component_pair_counts":[sum(1 for p in net["pairwise"] if p.issubset(set(c))) for c in components],"max_global_width_upper_bound":gw["treewidth"],"max_component_width_upper_bound":max(min_fill_upper_bound(c,[e for e in net["edges"] if e[0] in set(c) and e[1] in set(c)])["treewidth"] for c in components),"component_exhaustive_states_checked":component_answer["states_checked"],"global_exact_energy":float(global_answer["energy"]),"component_exact_energy":float(component_answer["energy"]),"independent_global_energy_of_global_state":global_energy,"independent_global_energy_of_component_state":component_energy,"exact_energy_gap":float(global_energy-component_energy),"global_state_vocab_valid":all(v in net["vocab"] for v in global_answer["state"].values()),"component_state_vocab_valid":all(v in net["vocab"] for v in component_answer["state"].values()),"extraction_union_exact":extraction_union_exact,"timing_ns":{"resident_setup_and_local_extractions":setup_extract_ns,"aggregate_network_extraction":global_extract_ns,"global_width_and_junction_tree":times["global"],"components_discovery_and_exhaustive_map":times["components"]},"source_inputs_start":started,"source_inputs_end":post}
def worker(rep):
 locked=lock_inputs();order=ARM_ORDERS[rep];cases=[run_case(n,rep,order) for n in SIZES]
 return {"replicate":rep,"pid":os.getpid(),"started_inputs":locked,"finished_inputs":lock_inputs(),"cases":cases}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1");env["PYTHONPATH"]=str(ROOT/"runners/dsl/python")+os.pathsep+str(ROOT)+os.pathsep+str(ROOT/"scripts")+os.pathsep+env.get("PYTHONPATH","")
 runs=[]
 for rep in range(3):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=120);runs.append(json.loads(p.stdout))
 post=lock_inputs();cases=[c for r in runs for c in r["cases"]]
 order_rows=[tuple(c["arm_order"]) for c in cases if c["n_residents"]==10]
 checks={"three_fresh_workers":len({r["pid"] for r in runs})==3,"source_stability":post==locked and all(r["started_inputs"]==locked==r["finished_inputs"] for r in runs) and all(c["source_inputs_start"]==locked==c["source_inputs_end"] for c in cases),"all_sizes_replicated":all(sum(c["n_residents"]==n for c in cases)==3 for n in SIZES),"solver_order_counterbalanced":set(order_rows)=={("global","components"),("components","global")} and len(order_rows)==3,"component_structure_exact":all(c["discovered_component_count"]==c["n_residents"] and set(c["discovered_component_sizes"])=={5} and set(c["discovered_component_pair_counts"])=={5} and c["nodes"]==5*c["n_residents"] and c["undirected_pairs"]==5*c["n_residents"] for c in cases),"aggregate_extraction_matches_resident_union":all(c["extraction_union_exact"] for c in cases),"exact_width_and_energy_parity":all(c["max_global_width_upper_bound"]==2 and c["max_component_width_upper_bound"]==2 and abs(c["exact_energy_gap"])<=TOL and abs(c["global_exact_energy"]-c["independent_global_energy_of_global_state"])<=TOL and abs(c["component_exact_energy"]-c["independent_global_energy_of_component_state"])<=TOL for c in cases),"all_states_valid":all(c["global_state_vocab_valid"] and c["component_state_vocab_valid"] for c in cases),"independent_oracle_counts":all(c["component_exhaustive_states_checked"]==243*c["n_residents"] for c in cases)}
 payload={"schema_version":1,"run_id":"substrate-bigville-aggregate-component-inference-v1-20260926","claim_boundary":"Graph-discovered disconnected components in the deterministic authored Bigville CAN cast; exact global junction-tree versus local exhaustive MAP, not connected-boundary factorization or natural data.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"configuration":{"resident_counts":SIZES,"replicates":3,"component_method":"BFS from extracted causal edges; no resident labels used","local_oracle_states_per_component":243,"arm_orders":ARM_ORDERS},"runs":runs,"checks":checks}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("capture validity or semantic gate failed")
if __name__=="__main__":main()
