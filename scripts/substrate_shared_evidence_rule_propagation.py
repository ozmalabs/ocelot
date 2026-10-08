#!/usr/bin/env python3
"""Native shared-evidence propagation against full-closure oracle."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SHARED_EVIDENCE_RULE_PROPAGATION_PREREG_20260925.md"
LOCK=ROOT/"evaluation/substrate_capability/shared_evidence_rule_propagation_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_shared_evidence_rule_propagation_20260925.json"
SIZES=(1,2,4,8); REPS=3; ARMS=("full","scoped","scoped_omit_right"); CAP=100_000
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rules():
    attr=lambda node,key:{"type":"Attr","node":{"type":"Var","name":node},"key":key}
    lit=lambda value:{"type":"Lit","value":value}
    eq=lambda a,b:{"type":"Eq","a":a,"b":b}
    diff=lambda a,b:{"type":"Not","arg":eq(a,b)}
    base=[["e","supports","s"]]
    return [
      {"name":"bench_copy_active_shared_evidence","match":base,"where":{"type":"And","items":[eq(attr("e","active"),lit(1.0)),diff(attr("s","derived"),attr("e","signal"))]},"effects":[["set_attr","s","derived",{"__term__":attr("e","signal")}]]},
      {"name":"bench_retract_inactive_shared_evidence","match":base,"where":{"type":"And","items":[eq(attr("e","active"),lit(0.0)),diff(attr("s","derived"),lit(0.0))]},"effects":[["set_attr","s","derived",0.0]]},
    ]

def setup(n):
    from substrate.world_adapter import WorldAdapter
    a=WorldAdapter(seeds=())
    for r in rules(): a.inner.add_rule(r)
    frames=[]; scopes=[]
    for i in range(n):
        f=a.s.add_node("BenchFrame",{"frame_index":i})
        mt=a.inner.add_node("Microtheory",{"name":f"frame_{i}"})
        a.inner.add_edge_unchecked(mt,"has_concept",f,{})
        frames.append(f); scopes.append(mt)
    boundaries=[]
    for i in range(n-1):
        e=a.s.add_node("BenchEvidence",{"boundary_index":i,"active":0.0,"signal":0.0,"input_kind":"shared_boundary_evidence"})
        states=[]
        for owner,side in ((i,"left"),(i+1,"right")):
            s=a.s.add_node("BenchFrameLocalState",{"owner_frame":owner,"boundary_index":i,"side":side,"derived":0.0})
            a.inner.add_edge_unchecked(e,"supports",s)
            a.inner.add_edge_unchecked(frames[owner],"has_output",s)
            a.inner.add_edge_unchecked(scopes[owner],"has_concept",s,{})
            states.append(s)
        for owner in (i,i+1): a.inner.add_edge_unchecked(scopes[owner],"has_concept",e,{})
        boundaries.append((e,states))
    return a,frames,scopes,boundaries

def expected_states(n,checkpoint):
    if checkpoint==1: return [1.0]*(2*(n-1))
    return [0.0]*(2*(n-1))

def run_closure(a,scopes,arm):
    start_wall,start_cpu=time.perf_counter_ns(),time.process_time_ns()
    if arm=="full":
        report=a.inner.run_rules_report(CAP,False); turns=0; progress=int(report["progress_steps"])
    else:
        omit=(1 if len(scopes)>1 else None) if arm=="scoped_omit_right" else None
        moved=rounds=turns=0
        while rounds<CAP:
            rounds+=1; round_progress=0
            for i,mt in enumerate(scopes):
                if i==omit: continue
                count=int(a.inner.run_rules_scoped(CAP-moved,False,mt)); moved+=count; round_progress+=count; turns+=1
                if moved>=CAP: break
            if round_progress==0 or moved>=CAP: break
        report=a.inner.run_rules_report(CAP,False); progress=moved
    return report,progress,turns,time.perf_counter_ns()-start_wall,time.process_time_ns()-start_cpu

def worker(n,rep,arm):
    from substrate_rs import _native
    a,frames,scopes,bounds=setup(n)
    a.inner.scale_audit_set_enabled(True)
    checkpoints=[]
    for cp in range(4):
        if cp==0:
            pass
        elif cp==1:
            for e,_ in bounds: a.s.set_attr(e,"active",1.0); a.s.set_attr(e,"signal",1.0)
        elif cp==2:
            for e,_ in bounds: a.s.set_attr(e,"signal",0.0)
        else:
            for e,_ in bounds: a.s.set_attr(e,"active",0.0)
        a.inner.scale_audit_reset()
        report,progress,turns,wall,cpu=run_closure(a,scopes,arm)
        values=[float(a.s.node(s)["attrs"].get("derived",-999.0)) for _,ss in bounds for s in ss]
        want=expected_states(n,cp)
        wrong=[i for i,(x,y) in enumerate(zip(values,want)) if x!=y]
        audit=dict(a.inner.scale_audit_snapshot())
        checkpoints.append({"checkpoint":("baseline","activate_1","change_to_0","retract")[cp],"report_status":report["status"],"progress":progress,"frame_turns":turns,"wall_ns":wall,"cpu_ns":cpu,"state_values":values,"expected_values":want,"wrong_state_indices":wrong,"scale_audit":audit})
    a.inner.scale_audit_set_enabled(False)
    native=Path(_native.__file__).resolve()
    return {"size":n,"replicate":rep,"arm":arm,"checkpoints":checkpoints,"all_fixed_points":all(x["report_status"]=="fixed_point" for x in checkpoints),"all_expected":all(not x["wrong_state_indices"] for x in checkpoints) if arm!="scoped_omit_right" else True,"native_extension_sha256":sha(native),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}

def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True)); return
    locked={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),"py_binding_sha256":sha(ROOT/"runners/dsl/src/py.rs")}
    if sys.argv[1:]==["--lock"]: print(json.dumps(locked,indent=2,sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing lock or locked inputs changed")
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    stale=subprocess.check_output([sys.executable,"-c","from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
    if stale: raise SystemExit("native build stale:\n"+stale)
    jobs=[(n,r,arm) for n in SIZES for r in range(REPS) for arm in ARMS]; random.Random(20260925).shuffle(jobs); runs=[]
    for n,r,arm in jobs:
        q=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(r),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        row=json.loads(q.stdout); runs.append(row); print(f"n={n} rep={r} arm={arm} checkpoints=4 fixed={row['all_fixed_points']} expected={row['all_expected']}",flush=True)
    ix={(x["size"],x["replicate"],x["arm"]):x for x in runs}; pairs=[]
    for n in SIZES:
        for r in range(REPS):
            f,s,o=(ix[n,r,k] for k in ARMS)
            pairs.append({"size":n,"replicate":r,"full_scoped_values_equal":[x["state_values"] for x in f["checkpoints"]]==[x["state_values"] for x in s["checkpoints"]],"full_all_expected":f["all_expected"],"scoped_all_expected":s["all_expected"],"omission_has_expected_stale_control":(n==1 or bool(o["checkpoints"][1]["wrong_state_indices"]) and len(o["checkpoints"][1]["wrong_state_indices"])==1),"scoped_candidates":sum(x["scale_audit"].get("cand_enum",0) for x in s["checkpoints"]),"full_candidates":sum(x["scale_audit"].get("cand_enum",0) for x in f["checkpoints"]),"scoped_term_evaluations":sum(x["scale_audit"].get("term_evals_total",0) for x in s["checkpoints"]),"full_term_evaluations":sum(x["scale_audit"].get("term_evals_total",0) for x in f["checkpoints"]),"full_wall_ns":sum(x["wall_ns"] for x in f["checkpoints"]),"scoped_wall_ns":sum(x["wall_ns"] for x in s["checkpoints"])})
    checks={"worker_count_36":len(runs)==36,"all_reports_fixed_point":all(x["all_fixed_points"] for x in runs),"full_scoped_all_expected":all(x["full_all_expected"] and x["scoped_all_expected"] and x["full_scoped_values_equal"] for x in pairs),"omission_controls_sensitive":all(x["omission_has_expected_stale_control"] for x in pairs),"matrix_complete":len(pairs)==12}
    summaries=[]
    for n in SIZES:
        ps=[p for p in pairs if p["size"]==n]
        summaries.append({"size":n,"replicates":len(ps),**{f"median_{k}":int(statistics.median(p[k] for p in ps)) for k in ("full_candidates","scoped_candidates","full_term_evaluations","scoped_term_evaluations","full_wall_ns","scoped_wall_ns")}})
    payload={"schema_version":1,"run_id":"shared-evidence-rule-propagation-20260925-v1","claim_boundary":"two benchmark-native copy/retract rules on shared evidence and frame-local states; fixed topology; caller-visitation only","locked_inputs":locked,"lock_sha256":sha(LOCK),"checks":checks,"summaries":summaries,"paired":pairs,"runs":runs}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"summaries":summaries},indent=2))
    if not all(checks.values()): raise SystemExit("shared evidence gate failed; preserve raw report")

if __name__=="__main__": main()
