#!/usr/bin/env python3
"""Locked exact-inference scaling on native-rule-settled CAN snapshots."""
from __future__ import annotations
import hashlib, itertools, json, os, platform, random, resource, statistics, subprocess, sys, time, tracemalloc
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/"runners/dsl/python"))
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_RUNTIME_GENERATED_EXACT_INFERENCE_SCALE_V1_PREREG_20260929.md"
RUNNER=Path(__file__).resolve(); FIXTURE=ROOT/"scripts/substrate_can_structure_envelope.py"
SEED=ROOT/"seeds/can_native_reimplementation.json"
LOCK=ROOT/"evaluation/substrate_capability/can_runtime_generated_exact_inference_scale_v1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/can_runtime_generated_exact_inference_scale_v1_20260929.json"
SIZES=(32,64,128,256); TOPOLOGIES=("path","banded2"); MODES=("2state","3state")
REPLICATES=3; GRANULARITY=0.25; MAX_STEPS=100000; TOL=1e-7

def digest(path):
 raw=path.read_bytes(); return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def lock_inputs():
 from substrate_rs import _native
 sources=("domains/can_junction_tree.py","domains/graph_treewidth.py","substrate/seed_loader.py",
          "runners/dsl/src/rewrite.rs","runners/dsl/src/can_ops.rs","runners/dsl/python/substrate_rs/_native.build.json")
 return {"schema_version":1,"protocol":digest(PROTOCOL),"runner":digest(RUNNER),"fixture":digest(FIXTURE),
         "seed":digest(SEED),"sources":[digest(ROOT/p) for p in sources],
         "native_extension":{"path":Path(_native.__file__).resolve().relative_to(ROOT).as_posix(),
                             "sha256":hashlib.sha256(Path(_native.__file__).resolve().read_bytes()).hexdigest()},
         "sizes":list(SIZES),"topologies":list(TOPOLOGIES),"modes":list(MODES),
         "replicates":REPLICATES,"granularity":GRANULARITY,"max_steps":MAX_STEPS,
         "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def oracle_ve(nodes,unary,pairwise,vocab):
 """Independent table-based min-sum VE in natural node order."""
 factors=[]; evaluations=0
 for v,h in unary.items():
  factors.append(((v,),{(x,):-float(h)*float(x) for x in vocab}))
 for pair,w in pairwise.items():
  a,b=sorted(pair)
  factors.append(((a,b),{(x,y):-float(w)*float(x)*float(y) for x in vocab for y in vocab}))
 for v in nodes:
  bucket=[f for f in factors if v in f[0]]
  factors=[f for f in factors if v not in f[0]]
  scope=tuple(sorted({x for s,_ in bucket for x in s}))
  rest=tuple(x for x in scope if x!=v); table={}
  for values in itertools.product(vocab,repeat=len(rest)):
   context=dict(zip(rest,values)); best=float("inf")
   for x in vocab:
    context[v]=x; score=0.0
    for fscope,ftable in bucket:
     score+=ftable[tuple(context[y] for y in fscope)]
    evaluations+=1
    if score<best: best=score
   table[values]=best
  factors.append((rest,table))
 energy=sum(table[()] for scope,table in factors if not scope)
 return {"energy":energy,"factor_evaluations":evaluations}

def direct_energy(unary,pairwise,state):
 total=-sum(float(h)*float(state[v]) for v,h in unary.items())
 for pair,w in pairwise.items():
  a,b=tuple(pair); total-=float(w)*float(state[a])*float(state[b])
 return total

def worker(n,topology,mode,rep):
 import substrate_rs as sr
 from substrate.seed_loader import engine_rules_only
 import domains.can_junction_tree as cjt
 from domains.graph_treewidth import min_fill_upper_bound
 from collections import Counter
 started=lock_inputs(); seed_doc=json.loads(SEED.read_text()); inner=sr.Substrate()._inner
 t_setup=time.perf_counter_ns(); inner.load_seed_manifest(engine_rules_only(seed_doc))
 vocab=(-1.0,1.0) if mode=="2state" else (-1.0,0.0,1.0)
 mt=inner.add_node("Microtheory",{"temperature":2.0,"discrete_mode":mode,"can_tick":0})
 rng_seed=20260929+n*1009+rep*9176
 fr=random.Random(rng_seed*53+n); pr=random.Random(rng_seed*31+n)
 fields=[fr.uniform(-1.0,1.0) for _ in range(n)]
 handles=[inner.add_node("Concept",{"name":f"c{i}","state":0.0,"external_field":fields[i],"identity_field":0.0}) for i in range(n)]
 for h in handles: inner.add_edge(mt,"has_concept",h,{})
 pairs=[]
 for a in range(n):
  for b in range(a+1,min(n,a+(2 if topology=="banded2" else 1)+1)):
   w=round(pr.uniform(-1.0,1.0)/GRANULARITY)*GRANULARITY
   pairs.append((a,b,w))
   inner.add_edge(handles[a],"causal_influence",handles[b],{"weight":w})
   inner.add_edge(handles[b],"causal_influence",handles[a],{"weight":w})
 setup_ns=time.perf_counter_ns()-t_setup
 rss_setup=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 t0=time.perf_counter_ns(); progress=inner.run_rules(MAX_STEPS); closure_ns=time.perf_counter_ns()-t0
 terminal=inner.run_rules(1); rss_closed=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 t0=time.perf_counter_ns(); net=cjt.can_network_from_mt(inner,mt); extract_ns=time.perf_counter_ns()-t0
 # Verify the live runtime extraction against the exact constructor factors.
 expected_unary={handles[i].value:fields[i] for i in range(n)}
 expected_pair={frozenset((handles[a].value,handles[b].value)):w for a,b,w in pairs}
 extraction_exact=(net["unary"]==expected_unary and net["pairwise"]==expected_pair and len(net["nodes"])==n)
 t0=time.perf_counter_ns(); width=min_fill_upper_bound(net["nodes"],net["edges"]); width_ns=time.perf_counter_ns()-t0
 before={h.value:float(inner.node(h)["attrs"].get("state",0.0)) for h in handles}
 tracemalloc.start(); t0=time.perf_counter_ns()
 exact=cjt.junction_tree_map(net["nodes"],net["edges"],net["unary"],net["pairwise"],net["vocab"],order=width["elimination_order"])
 jt_ns=time.perf_counter_ns()-t0; _,py_peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
 t0=time.perf_counter_ns(); oracle=oracle_ve(net["nodes"],net["unary"],net["pairwise"],net["vocab"]); oracle_ns=time.perf_counter_ns()-t0
 scored=direct_energy(net["unary"],net["pairwise"],exact["state"])
 after={h.value:float(inner.node(h)["attrs"].get("state",0.0)) for h in handles}
 postnet=cjt.can_network_from_mt(inner,mt)
 model_preserved=(net["unary"]==postnet["unary"] and net["pairwise"]==postnet["pairwise"] and net["edges"]==postnet["edges"])
 deg=Counter()
 for a,b in net["edges"]: deg[a]+=1;deg[b]+=1
 post=lock_inputs()
 return {"n":n,"topology":topology,"mode":mode,"replicate":rep,"seed":rng_seed,"worker_pid":os.getpid(),
  "nodes":len(net["nodes"]),"undirected_pairs":len(net["pairwise"]),"directed_edges":2*len(net["pairwise"]),
  "expected_pairs":len(pairs),"max_degree":max(deg.values(),default=0),"min_fill_width":width["treewidth"],
  "closure_progress":progress,"terminal_probe_progress":terminal,"extraction_exact":extraction_exact,
  "exact_energy":float(exact["energy"]),"oracle_energy":float(oracle["energy"]),"direct_rescore":float(scored),
  "oracle_factor_evaluations":oracle["factor_evaluations"],"state_domain_valid":all(x in vocab for x in exact["state"].values()),
  "no_state_mutation":before==after,"model_preserved":model_preserved,
  "timing_ns":{"rule_setup":setup_ns,"native_closure":closure_ns,"network_extraction":extract_ns,
                "min_fill":width_ns,"junction_tree":jt_ns,"independent_ve_oracle":oracle_ns},
  "python_jt_peak_bytes":py_peak,"process_rss_setup_highwater_kib":rss_setup,
  "process_rss_closed_highwater_kib":rss_closed,"process_rss_final_highwater_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  "source_lock_start":started,"source_lock_end":post}

def main():
 if len(sys.argv)==6 and sys.argv[1]=="--worker":
  print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or OUT.exists():raise SystemExit("refusing to overwrite lock or capture")
  LOCK.write_text(json.dumps(lock_inputs(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if lock_inputs()!=lock:raise SystemExit("source/protocol lock drift")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale:\n"+"\n".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"}
 rows=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   for mode in MODES:
    for rep in range(REPLICATES):
     p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),topology,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=180)
     row=json.loads(p.stdout); rows.append(row)
     print(f"n={n} {topology} {mode} rep={rep} width={row['min_fill_width']} jt_ms={row['timing_ns']['junction_tree']/1e6:.2f} rss={row['process_rss_final_highwater_kib']}KiB",flush=True)
 post=lock_inputs()
 checks={"fresh_worker_coverage":len(rows)==48 and len({r["worker_pid"] for r in rows})==48,
  "cell_coverage":all(sum(r["n"]==n and r["topology"]==t and r["mode"]==m for r in rows)==REPLICATES for n in SIZES for t in TOPOLOGIES for m in MODES),
  "node_pair_counts":all(r["nodes"]==r["n"] and r["undirected_pairs"]==r["expected_pairs"] for r in rows),
  "closure_terminal":all(r["closure_progress"]<MAX_STEPS and r["terminal_probe_progress"]==0 for r in rows),
  "width_at_most_two":all(r["min_fill_width"]<=2 for r in rows),
  "extraction_exact":all(r["extraction_exact"] for r in rows),
  "oracle_and_rescore_match":all(abs(r["exact_energy"]-r["oracle_energy"])<=TOL and abs(r["direct_rescore"]-r["oracle_energy"])<=TOL for r in rows),
  "state_and_model_preserved":all(r["state_domain_valid"] and r["no_state_mutation"] and r["model_preserved"] for r in rows),
  "pre_post_source_lock":lock==post and all(r["source_lock_start"]==lock==r["source_lock_end"] for r in rows)}
 groups=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   for mode in MODES:
    g=[r for r in rows if (r["n"],r["topology"],r["mode"])==(n,topology,mode)]
    groups.append({"n":n,"topology":topology,"mode":mode,"replicates":len(g),
     "median_pairs":int(statistics.median(r["undirected_pairs"] for r in g)),
     "median_width":statistics.median(r["min_fill_width"] for r in g),
     "median_closure_ms":statistics.median(r["timing_ns"]["native_closure"] for r in g)/1e6,
     "median_extract_ms":statistics.median(r["timing_ns"]["network_extraction"] for r in g)/1e6,
     "median_jt_ms":statistics.median(r["timing_ns"]["junction_tree"] for r in g)/1e6,
     "median_oracle_ms":statistics.median(r["timing_ns"]["independent_ve_oracle"] for r in g)/1e6,
     "median_jt_python_peak_bytes":int(statistics.median(r["python_jt_peak_bytes"] for r in g)),
     "median_process_rss_kib":int(statistics.median(r["process_rss_final_highwater_kib"] for r in g))})
 payload={"schema_version":1,"run_id":"can-runtime-generated-exact-inference-scale-v1-20260929","status":"complete",
  "input_lock":lock,"post_run_input_lock":post,"claim_boundary":"authored native-rule-settled path/banded CAN snapshots only; no natural graph prevalence",
  "configuration":{"sizes":SIZES,"topologies":TOPOLOGIES,"modes":MODES,"replicates":REPLICATES,"granularity":GRANULARITY},
  "environment":{"python":platform.python_version(),"platform":platform.platform()},"checks":checks,"groups":groups,"runs":rows}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("runtime inference scale gate failed")

if __name__=="__main__":main()
