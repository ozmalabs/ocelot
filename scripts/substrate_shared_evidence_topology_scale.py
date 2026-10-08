#!/usr/bin/env python3
"""Topology/fan-out scale study for shared-evidence native rules."""
from __future__ import annotations
import hashlib,json,os,random,resource,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SHARED_EVIDENCE_TOPOLOGY_SCALE_PREREG_20260925.md"
LOCK=ROOT/"evaluation/substrate_capability/shared_evidence_topology_scale_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_shared_evidence_topology_scale_20260925.json"
SIZES=(8,16,32,64); TOPOLOGIES=("path","star","binary_tree"); REPS=3; ARMS=("full","scoped","scoped_omit_boundary0"); CAP=100_000
CHECKPOINTS=("baseline","insert_signal_1","update_signal_0_5","retract_delete","reinsert_signal_0_75","retract_delete_again")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edge_list(n,topology):
    if topology=="path": return [(i,i+1) for i in range(n-1)]
    if topology=="star": return [(0,i) for i in range(1,n)]
    if topology=="binary_tree": return [((i-1)//2,i) for i in range(1,n)]
    raise ValueError(topology)
def rules():
    attr=lambda node,key:{"type":"Attr","node":{"type":"Var","name":node},"key":key}
    lit=lambda value:{"type":"Lit","value":value}
    eq=lambda a,b:{"type":"Eq","a":a,"b":b}
    diff=lambda a,b:{"type":"Not","arg":eq(a,b)}
    match=[["e","supports","s"]]
    return [
      {"name":"bench_copy_active_shared_evidence","match":match,"where":{"type":"And","items":[eq(attr("e","active"),lit(1.0)),diff(attr("s","derived"),attr("e","signal"))]},"effects":[["set_attr","s","derived",{"__term__":attr("e","signal")}]]},
      {"name":"bench_retract_inactive_shared_evidence","match":match,"where":{"type":"And","items":[eq(attr("e","active"),lit(0.0)),diff(attr("s","derived"),lit(0.0))]},"effects":[["set_attr","s","derived",0.0]]},
    ]
def setup(n,topology):
    from substrate.world_adapter import WorldAdapter
    a=WorldAdapter(seeds=())
    for rule in rules(): a.inner.add_rule(rule)
    edges=edge_list(n,topology); frames=[]; scopes=[]
    for i in range(n):
        f=a.s.add_node("BenchFrame",{"frame_index":i}); mt=a.inner.add_node("Microtheory",{"name":f"frame_{i}"})
        a.inner.add_edge_unchecked(mt,"has_concept",f,{}); frames.append(f); scopes.append(mt)
    bounds=[]
    for j,(left,right) in enumerate(edges):
        ev=a.s.add_node("BenchEvidence",{"boundary_index":j,"active":0.0,"signal":0.0,"input_kind":"shared_boundary_evidence"})
        states=[]
        for owner,side in ((left,"left"),(right,"right")):
            state=a.s.add_node("BenchFrameLocalState",{"owner_frame":owner,"boundary_index":j,"side":side,"derived":0.0})
            a.inner.add_edge_unchecked(frames[owner],"has_output",state); a.inner.add_edge_unchecked(state,"boundary_source",ev)
            a.inner.add_edge_unchecked(scopes[owner],"has_concept",state,{})
            states.append(state)
        for owner in (left,right): a.inner.add_edge_unchecked(scopes[owner],"has_concept",ev,{})
        bounds.append({"index":j,"left":left,"right":right,"evidence":ev,"states":states})
    return a,frames,scopes,bounds
def mutate_before(a,bounds,cp):
    if cp==1:
        for b in bounds:
            e=b["evidence"]; a.inner.add_edge_unchecked(e,"supports",b["states"][0]); a.inner.add_edge_unchecked(e,"supports",b["states"][1])
            a.s.set_attr(e,"signal",1.0); a.s.set_attr(e,"active",1.0)
    elif cp==2:
        for b in bounds: a.s.set_attr(b["evidence"],"signal",0.5)
    elif cp in (3,5):
        for b in bounds: a.s.set_attr(b["evidence"],"active",0.0)
    elif cp==4:
        for b in bounds:
            e=b["evidence"]; a.inner.add_edge_unchecked(e,"supports",b["states"][0]); a.inner.add_edge_unchecked(e,"supports",b["states"][1])
            a.s.set_attr(e,"signal",0.75); a.s.set_attr(e,"active",1.0)
def expected(bounds,cp):
    value={0:0.0,1:1.0,2:0.5,3:0.0,4:0.75,5:0.0}[cp]
    return [value for _ in bounds for _ in range(2)]
def close(a,scopes,arm,bounds):
    t0,c0=time.perf_counter_ns(),time.process_time_ns()
    if arm=="full":
        report=a.inner.run_rules_report(CAP,False); return report["status"],int(report["progress_steps"]),0,time.perf_counter_ns()-t0,time.process_time_ns()-c0
    omit=set()
    if arm=="scoped_omit_boundary0" and bounds: omit={bounds[0]["left"],bounds[0]["right"]}
    moved=turns=rounds=0; last_progress=0
    while rounds<CAP:
        rounds+=1; last_progress=0
        for i,mt in enumerate(scopes):
            if i in omit: continue
            count=int(a.inner.run_rules_scoped(CAP-moved,False,mt)); moved+=count; turns+=1; last_progress+=count
            if moved>=CAP: break
        if last_progress==0 or moved>=CAP: break
    return ("scoped_no_progress" if last_progress==0 and moved<CAP else "scoped_budget"),moved,turns,time.perf_counter_ns()-t0,time.process_time_ns()-c0
def worker(n,topology,rep,arm):
    from substrate_rs import _native
    a,frames,scopes,bounds=setup(n,topology); a.inner.scale_audit_set_enabled(True); checkpoints=[]
    for cp,name in enumerate(CHECKPOINTS):
        mutate_before(a,bounds,cp); a.inner.scale_audit_reset()
        status,progress,turns,wall,cpu=close(a,scopes,arm,bounds)
        vals=[float(a.s.node(s)["attrs"]["derived"]) for b in bounds for s in b["states"]]
        exp=expected(bounds,cp); wrong=[i for i,(v,x) in enumerate(zip(vals,exp)) if v!=x]
        audit=dict(a.inner.scale_audit_snapshot())
        if cp in (3,5):
            for b in bounds:
                a.inner.remove_edge(b["evidence"],"supports",b["states"][0]); a.inner.remove_edge(b["evidence"],"supports",b["states"][1])
        checkpoints.append({"checkpoint":name,"settlement_status":status,"progress":progress,"frame_turns":turns,"wall_ns":wall,"cpu_ns":cpu,"state_values":vals,"expected_values":exp,"wrong_state_indices":wrong,"scale_audit":audit})
    a.inner.scale_audit_set_enabled(False); native=Path(_native.__file__).resolve()
    return {"size":n,"topology":topology,"replicate":rep,"arm":arm,"checkpoints":checkpoints,"all_settled":all(x["settlement_status"] in ("fixed_point","scoped_no_progress") for x in checkpoints),"all_expected":all(not x["wrong_state_indices"] for x in checkpoints),"native_extension_sha256":sha(native),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
    if len(sys.argv)==6 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],int(sys.argv[4]),sys.argv[5]),sort_keys=True)); return
    locked = {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(__file__),
        "rewrite_sha256": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "substrate_sha256": sha(ROOT / "runners/dsl/src/substrate.rs"),
        "py_binding_sha256": sha(ROOT / "runners/dsl/src/py.rs"),
    }
    if sys.argv[1:]==["--lock"]: print(json.dumps(locked,indent=2,sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing lock or locked inputs changed")
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    stale=subprocess.check_output([sys.executable,"-c","from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
    if stale: raise SystemExit("native build stale:\n"+stale)
    jobs=[(n,t,r,a) for t in TOPOLOGIES for n in SIZES for r in range(REPS) for a in ARMS]; random.Random(20260925).shuffle(jobs); runs=[]
    for n,t,r,arm in jobs:
        q=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),t,str(r),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        row=json.loads(q.stdout); runs.append(row); print(f"topology={t} n={n} rep={r} arm={arm} settled={row['all_settled']} expected={row['all_expected']}",flush=True)
    ix={(x["size"],x["topology"],x["replicate"],x["arm"]):x for x in runs}; pairs=[]
    for t in TOPOLOGIES:
      for n in SIZES:
       for r in range(REPS):
        f,s,o=(ix[n,t,r,k] for k in ARMS)
        omission_ok=(o["checkpoints"][1]["wrong_state_indices"]==[0,1] and o["checkpoints"][2]["wrong_state_indices"]==[0,1] and o["checkpoints"][4]["wrong_state_indices"]==[0,1] and not o["checkpoints"][0]["wrong_state_indices"] and not o["checkpoints"][3]["wrong_state_indices"] and not o["checkpoints"][5]["wrong_state_indices"])
        pairs.append({"topology":t,"size":n,"replicate":r,"full_scoped_values_equal":[x["state_values"] for x in f["checkpoints"]]==[x["state_values"] for x in s["checkpoints"]],"full_expected":f["all_expected"],"scoped_expected":s["all_expected"],"omission_control_sensitive":omission_ok,"full_candidates":sum(x["scale_audit"].get("cand_enum",0) for x in f["checkpoints"]),"scoped_candidates":sum(x["scale_audit"].get("cand_enum",0) for x in s["checkpoints"]),"full_term_evaluations":sum(x["scale_audit"].get("term_evals_total",0) for x in f["checkpoints"]),"scoped_term_evaluations":sum(x["scale_audit"].get("term_evals_total",0) for x in s["checkpoints"]),"full_wall_ns":sum(x["wall_ns"] for x in f["checkpoints"]),"scoped_wall_ns":sum(x["wall_ns"] for x in s["checkpoints"])})
    checks={"worker_count_108":len(runs)==108,"all_arms_settled":all(x["all_settled"] for x in runs),"all_full_scoped_expected_and_equal":all(p["full_expected"] and p["scoped_expected"] and p["full_scoped_values_equal"] for p in pairs),"all_omission_controls_sensitive":all(p["omission_control_sensitive"] for p in pairs),"matrix_complete":len(pairs)==36}
    summaries=[]
    for t in TOPOLOGIES:
      for n in SIZES:
       ps=[p for p in pairs if p["topology"]==t and p["size"]==n]
       summaries.append({"topology":t,"size":n,"replicates":len(ps),**{f"median_{k}":int(statistics.median(p[k] for p in ps)) for k in ("full_candidates","scoped_candidates","full_term_evaluations","scoped_term_evaluations","full_wall_ns","scoped_wall_ns")}})
    payload={"schema_version":1,"run_id":"shared-evidence-topology-scale-20260925-v1","claim_boundary":"three fixed connected graph families through N=64; benchmark-native rules; caller visitation; explicit active-bit retraction before support-edge removal","locked_inputs":locked,"lock_sha256":sha(LOCK),"checks":checks,"summaries":summaries,"paired":pairs,"runs":runs}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"summary_count":len(summaries)},indent=2))
    if not all(checks.values()): raise SystemExit("topology scale gate failed; preserve raw report")
if __name__=="__main__": main()
