#!/usr/bin/env python3
"""Measure Goal identity emitted by the Phase 4A materializer/rules."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, statistics, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_PHASE4A_PRODUCED_GOAL_IDENTITY_PREREG_20260926.md"
SEED=ROOT/"seeds/conversation_deliberation_phase4a.json"
MATERIALIZER=ROOT/"domains/conversation_deliberation.py"
LOCK=ROOT/"evaluation/substrate_capability/phase4a_produced_goal_identity_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_phase4a_produced_goal_identity_v1_20260926.json"
SIZES=(2,4,8); ARMS=("full","scoped"); CAP=100000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x): return int(x.value if hasattr(x,"value") else x)
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(ROOT/"docs/research/engine_substrate/SUBSTRATE_PHASE4A_PRODUCED_GOAL_IDENTITY_AMENDMENT_20260926.md"),"runner_sha256":sha(__file__),"seed_sha256":sha(SEED),
  "materializer_sha256":sha(MATERIALIZER),"native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "rust_rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"rust_substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),
  "rust_py_sha256":sha(ROOT/"runners/dsl/src/py.rs"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def project(a,tasks):
 rows=[]
 for i,(goal,d,mt,source) in enumerate(tasks):
  selected=[a.s.node(x)["attrs"].get("selected_candidate_id") for x in a.inner.neighbours(d,"has_selection")]
  executions=[]
  for trace in a.s.nodes("DeliberationExecutionTrace"):
   if a.inner.has_edge(trace,"for_goal",goal):
    executions.append({"candidate":a.s.node(trace)["attrs"].get("candidate_id"),"status":a.s.node(trace)["attrs"].get("status")})
  settlements=[]
  for settlement in a.inner.neighbours(d,"has_settlement"):
   settlements.append({"candidate":a.s.node(settlement)["attrs"].get("candidate_id"),"goal_link":goal in a.inner.neighbours(settlement,"returns_to_goal")})
  rows.append({"task":i,"goal_status":a.s.node(goal)["attrs"].get("status"),
   "deliberation_status":a.s.node(d)["attrs"].get("status"),"selection":selected,
   "execution_traces_for_goal":executions,"settlements":settlements,
   "source_link":source in a.inner.neighbours(next(iter(a.inner.neighbours(d,"has_candidate")),None),"derived_from_evidence") if a.inner.neighbours(d,"has_candidate") else False})
 return rows

def worker(n,rep,arm):
 from substrate.world_adapter import WorldAdapter
 from substrate.seed_loader import manifest_for
 from domains.conversation_deliberation import materialize_from_live_thought_manifold
 from substrate_rs import _native
 a=WorldAdapter(seeds=()); a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"),a.agent)
 tasks=[]; frames=[]; construct0=time.perf_counter_ns()
 for i in range(n):
  goal=a.s.add_node("Goal",{"kind":"answer","status":"active","goal_id":f"task_{i}"})
  manifold=a.s.add_node("ThoughtManifold",{"status":"evidence_ready","task_id":f"task_{i}"})
  source=a.s.add_node("ThoughtCandidate",{"candidate_id":f"answer_{i}","kind":"answer","grounding":1.0,
   "expected_value":1.0+i/100,"residual_cost":0.05,"consequence":0.4,"novelty":0.1,
   "execution_ready":1.0,"outcome_status":"resolved","evidence_path":f"authored_evidence_{i}"})
  a.inner.add_edge_unchecked(manifold,"has_goal_evidence",source)
  d=materialize_from_live_thought_manifold(a,goal=goal,manifold=manifold,epoch=1)
  mt=a.s.add_node("Microtheory",{"name":f"phase4a_goal_frame_{i}"})
  for node in (goal,manifold,source,d,*a.inner.neighbours(d,"has_candidate")):
   a.inner.add_edge_unchecked(mt,"has_concept",node)
  tasks.append((goal,d,mt,source)); frames.append(mt)
 construction_ns=time.perf_counter_ns()-construct0
 a.inner.scale_audit_reset(); a.inner.scale_audit_set_enabled(True)
 wall0=time.perf_counter_ns(); cpu0=time.process_time_ns(); reports=[]; turns=0
 if arm=="full":
  report=dict(a.inner.run_rules_report(CAP,False)); reports=[report]
  complete=report.get("status")=="fixed_point"
 else:
  total=0; round_count=0
  while round_count<CAP and total<CAP:
   round_count+=1; sweep=0
   for mt in frames:
    rep0=dict(a.inner.run_rules_scoped_delta_report(mt,CAP-total,False)); reports.append(rep0);turns+=1
    steps=int(rep0.get("progress_steps",0));total+=steps;sweep+=steps
    if rep0.get("hit_progress_budget") or rep0.get("deferred_effects_pending"):break
   if any(r.get("hit_progress_budget") or r.get("deferred_effects_pending") for r in reports):break
   if sweep==0:break
  complete=bool(reports) and not any(r.get("hit_progress_budget") or r.get("deferred_effects_pending") for r in reports) and (round_count<CAP)
 wall_ns=time.perf_counter_ns()-wall0;cpu_ns=time.process_time_ns()-cpu0
 counters={str(k):int(v) for k,v in dict(a.inner.scale_audit_snapshot()).items()};a.inner.scale_audit_set_enabled(False)
 rows=project(a,tasks); final=dict(a.inner.graph_to_dict())
 expected=[{"task":i,"goal_status":"active","deliberation_status":"resolved","selection":[f"has_goal_evidence:answer_{i}"],
  "execution_traces_for_goal":[{"candidate":f"has_goal_evidence:answer_{i}","status":"resolved"}],
  "settlements":[{"candidate":f"has_goal_evidence:answer_{i}","goal_link":True}],"source_link":True} for i in range(n)]
 # Source provenance is checked from the actual copied candidate edges below; the projection keeps identity linkage explicit.
 provenance=[]
 for goal,d,mt,source in tasks:
  candidates=a.inner.neighbours(d,"has_candidate")
  provenance.append(bool(candidates) and all(source in a.inner.neighbours(c,"derived_from_evidence") for c in candidates))
 return {"size":n,"replicate":rep,"arm":arm,"pid":os.getpid(),"construction_ns":construction_ns,
  "wall_ns":wall_ns,"cpu_ns":cpu_ns,"turns":turns,"complete":complete,"reports":[{k:v for k,v in r.items() if k in ("status","progress_steps","hit_progress_budget","deferred_effects_pending","affected_microtheories")} for r in reports],
  "counters":counters,"projection":rows,"source_provenance_all_tasks":all(provenance),"expected_projection":rows==expected,
  "graph_digest":digest(final),"peak_rss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
  "native_extension_sha256":sha(Path(_native.__file__).resolve())}

def main():
 if sys.argv[1:]==["--lock"]: print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[(n,r,a) for n in SIZES for r in range(3) for a in ARMS];random.Random(20260926).shuffle(jobs);runs=[]
 for n,r,arm in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(r),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(p.stdout))
 cells={(x["size"],x["replicate"],x["arm"]):x for x in runs}; gates={};summary={}
 for n in SIZES:
  gates[str(n)]={}
  for r in range(3):
   f=cells[n,r,"full"];s=cells[n,r,"scoped"]
   gates[str(n)][str(r)]={"full_complete":f["complete"],"scoped_complete":s["complete"],
    "both_task_oracles":f["expected_projection"] and s["expected_projection"],
    "producer_source_provenance":f["source_provenance_all_tasks"] and s["source_provenance_all_tasks"],
    "exact_full_scoped_projection":f["projection"]==s["projection"]}
  summary[str(n)]={}
  for arm in ARMS:
   rows=[]
   for r in range(3):
    x=cells[n,r,arm];c=x["counters"]
    rows.append({"replicate":r,"candidate_pairs":c.get("cand_tested",0),"term_evaluations":c.get("term_evals_total",0),
     "wall_ns":x["wall_ns"],"cpu_ns":x["cpu_ns"],"construction_ns":x["construction_ns"],"turns":x["turns"],"peak_rss_kib":x["peak_rss_kib"]})
   summary[str(n)][arm]={"per_replicate":rows}
   for k in rows[0]:
    if k!="replicate":
     vals=[x[k] for x in rows];summary[str(n)][arm][k+"_median"]=statistics.median(vals);summary[str(n)][arm][k+"_range"]=[min(vals),max(vals)]
  summary[str(n)]["scoped_over_full_candidate_ratio"]=summary[str(n)]["scoped"]["candidate_pairs_median"]/max(1,summary[str(n)]["full"]["candidate_pairs_median"])
  summary[str(n)]["scoped_over_full_wall_ratio"]=summary[str(n)]["scoped"]["wall_ns_median"]/max(1,summary[str(n)]["full"]["wall_ns_median"])
 checks={"18_workers_unique_pids":len(runs)==18 and len({r["pid"] for r in runs})==18,
  "complete_matrix":len(cells)==18,"all_identity_and_parity_gates_pass":all(all(v.values()) for byrep in gates.values() for v in byrep.values())}
 payload={"schema_version":1,"run_id":"substrate-phase4a-produced-goal-identity-v1-20260926",
  "claim_boundary":"Production materializer and Phase 4A native trace producer tested on generated independent Goals; runner-authored frames; not natural task prevalence or general locality.",
  "locked_inputs":locked,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},
  "schedule":[list(j) for j in jobs],"checks":checks,"replicate_gates":gates,"summary":summary,"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"checks":checks,"summary":summary},indent=2))
 if not all(checks.values()):raise SystemExit("produced identity probe failed; raw report preserved")

if __name__=="__main__":
 if len(sys.argv)==5 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True));
 else:main()
