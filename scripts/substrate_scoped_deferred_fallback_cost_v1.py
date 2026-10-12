#!/usr/bin/env python3
"""Fresh-process cost comparison for full closure and deferred scoped fallback."""
from __future__ import annotations
import hashlib,json,os,random,subprocess,sys,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_DEFERRED_FALLBACK_COST_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/scoped_deferred_fallback_cost_v1_1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_scoped_deferred_fallback_cost_v1_1_20260926.json"
PAIR_COUNTS=(1,2,4,8,16);REPS=12;CAP=20000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def worker(pair_count,arm):
 from substrate_rs import Substrate,Attr,Eq,Lit,Not,Var,_native
 from substrate_rs.ext import add_rule
 t0=time.perf_counter_ns();c0=time.process_time_ns()
 s=Substrate();controller=s.add_node("Microtheory",{"name":"identity_controller"});anchor=s.add_node("Anchor",{})
 s.add_edge_unchecked(controller,"has_concept",anchor);s.add_edge_unchecked(anchor,"has_anchor",anchor)
 prev=[];cur=[]
 for i in range(pair_count):
  mp=s.add_node("Microtheory",{"name":f"prev_{i}"});mc=s.add_node("Microtheory",{"name":f"cur_{i}"})
  p=s.add_node("PrevPercept",{"feat":[float(i*10),0.0]});q=s.add_node("CurPercept",{"feat":[float(i*10)+0.05,0.05]})
  s.add_edge_unchecked(mp,"has_concept",p);s.add_edge_unchecked(mc,"has_concept",q);prev.append(p);cur.append(q)
 add_rule(s._inner,"fallback_cost_track_identity",[("mt","has_concept","a"),("a","has_anchor","a")],
  [["track_identity",{"__term__":{"type":"NodesOfType","node_type":"PrevPercept"}},{"__term__":{"type":"NodesOfType","node_type":"CurPercept"}},"feat",None,None,"identity",1.0],
   ["set_attr","a","tracking_done",True]],
  where=Not(Eq(Attr(Var("a"),"tracking_done"),Lit(True))))
 setup_wall=time.perf_counter_ns()-t0;setup_cpu=time.process_time_ns()-c0
 scoped_wall=scoped_cpu=0;scoped_report=None
 if arm=="scoped_fallback":
  t0=time.perf_counter_ns();c0=time.process_time_ns()
  scoped_report=s._inner.run_rules_scoped_delta_report(controller,1,False)
  scoped_wall=time.perf_counter_ns()-t0;scoped_cpu=time.process_time_ns()-c0
  if not scoped_report["deferred_effects_pending"]:raise RuntimeError("fallback arm did not expose pending deferred work")
 t0=time.perf_counter_ns();c0=time.process_time_ns();global_report=s._inner.run_rules_report(CAP,False)
 global_wall=time.perf_counter_ns()-t0;global_cpu=time.process_time_ns()-c0
 identities={"previous":s._inner.get_attr_many(prev,"identity"),"current":s._inner.get_attr_many(cur,"identity"),"controller_done":s.node(anchor)["attrs"].get("tracking_done")}
 terminal=s._inner.run_rules_report(CAP,False)
 result={"pair_count":pair_count,"frame_count":2*pair_count,"arm":arm,"pid":os.getpid(),
  "setup_wall_ns":setup_wall,"setup_cpu_ns":setup_cpu,"scoped_wall_ns":scoped_wall,"scoped_cpu_ns":scoped_cpu,
  "global_wall_ns":global_wall,"global_cpu_ns":global_cpu,"settlement_wall_ns":scoped_wall+global_wall,"settlement_cpu_ns":scoped_cpu+global_cpu,
  "global_report":global_report,"scoped_report":None if scoped_report is None else {"progress_steps":scoped_report["progress_steps"],"hit_progress_budget":scoped_report["hit_progress_budget"],"deferred_effects_pending":scoped_report["deferred_effects_pending"]},
  "identities":identities,"terminal_status":terminal["status"],"terminal_progress":terminal["progress_steps"],
  "rss_peak_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"native_extension_sha256":sha(Path(_native.__file__).resolve())}
 return result

def inputs():
 paths={"protocol":PROTOCOL,"runner":Path(__file__).resolve(),"analyzer":ROOT/"scripts/analyze_substrate_scoped_deferred_fallback_cost_v1.py",
 "rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","term":ROOT/"runners/dsl/src/term.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
 return {k:sha(v) for k,v in paths.items()}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps(inputs(),indent=2,sort_keys=True));return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3]),sort_keys=True));return
 locked=inputs()
 if json.loads(LOCK.read_text())!=locked:raise SystemExit("input lock mismatch")
 env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT/'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH','')}"
 jobs=[(n,r,a) for n in PAIR_COUNTS for r in range(REPS) for a in ("full","scoped_fallback")];random.Random(20260926).shuffle(jobs);runs=[]
 for n,r,arm in jobs:
  t0=time.perf_counter_ns();cmd=[sys.executable,str(Path(__file__).resolve()),"--worker",str(n),arm]
  row=json.loads(subprocess.check_output(cmd,cwd=ROOT,env=env,text=True));row["replicate"]=r;row["worker_elapsed_ns"]=time.perf_counter_ns()-t0;runs.append(row)
  print(f"pairs={n} rep={r} arm={arm} settle_ns={row['settlement_wall_ns']}",flush=True)
 payload={"schema_version":1,"run_id":"substrate-scoped-deferred-fallback-cost-v1_1-20260926","locked_inputs":locked,"schedule":[list(x) for x in jobs],"runs":runs,
  "claim_boundary":"host-specific cost envelope for one synthetic TrackIdentity deferred-effect family"}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(f"raw report: {OUT.relative_to(ROOT)} ({len(runs)} workers)")
if __name__=="__main__":main()
