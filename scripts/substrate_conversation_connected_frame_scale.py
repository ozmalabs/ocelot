#!/usr/bin/env python3
"""Locked full-vs-scoped replay for overlapping conversation frames."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_CONNECTED_FRAME_SCALE_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/conversation_connected_frame_scale_lock_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_connected_frame_scale_20260925.json"
SEED = ROOT / "seeds/conversation_deliberation_phase4a.json"
MATERIALIZER = ROOT / "domains/conversation_deliberation.py"
SIZES, REPS, ARMS, CAP = (1, 2, 4, 8), 3, ("full", "scoped"), 100_000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def make(size):
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains.conversation_deliberation import materialize_deliberation
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest_for("conversation_deliberation_phase4a"), a.agent)
    tasks, scopes, locals_ = [], [], []
    for i in range(size):
        key=f"frame_{i}"
        goal=a.s.add_node("Goal", {"kind":"answer", "status":"active", "frame_key":key})
        specs=[
            {"candidate_id":f"{key}_repair", "kind":"repair", "grounding":1.0, "expected_value":0.55, "residual_cost":0.1, "consequence":0.2, "novelty":0.1, "evidence_path":"goal->gap->repair"},
            {"candidate_id":f"{key}_unsupported", "kind":"answer", "grounding":0.0, "expected_value":1.0, "residual_cost":0.0, "consequence":1.0, "novelty":1.0, "evidence_path":""},
        ]
        if size == 1:
            specs.append({"candidate_id":"local_answer_0", "kind":"answer", "grounding":1.0, "expected_value":0.8, "residual_cost":0.1, "consequence":0.5, "novelty":0.2, "evidence_path":"goal->fact"})
        d=materialize_deliberation(a, goal=goal, candidates=specs)
        mt=a.inner.add_node("Microtheory", {"name":key})
        owned=[goal,d,*a.inner.neighbours(d,"has_candidate")]
        for node in owned: a.inner.add_edge_unchecked(mt,"has_concept",node,{})
        tasks.append((key,d)); scopes.append(mt); locals_.append(owned)
    shared=[]
    for j in range(size-1):
        cid=f"shared_answer_{j}"
        c=a.s.add_node("DeliberativeCandidate", {"candidate_id":cid,"kind":"answer","grounding":1.0,
            "expected_value":0.8+0.001*j,"residual_cost":0.1,"consequence":0.5,"novelty":0.2,
            "evidence_path":"shared-boundary-answer","source_relation":"adjacent_frame_boundary","status":"proposed",
            "ordinal":3.0,"score_epoch":-1.0,"rejection_trace":0.0,"counterfactual_trace":0.0,
            "execution_ready":0.0,"outcome_status":"pending"})
        a.inner.add_edge_unchecked(tasks[j][1],"has_candidate",c)
        a.inner.add_edge_unchecked(tasks[j+1][1],"has_candidate",c)
        for i in (j,j+1): a.inner.add_edge_unchecked(scopes[i],"has_concept",c,{})
        shared.append(c)
    expected=[]
    for i in range(size):
        expected.append(f"shared_answer_{min(i,size-2)}" if size>1 else "local_answer_0")
    return a,tasks,scopes,expected

def project(a,tasks):
    out=[]
    for key,d in tasks:
        attrs=a.s.node(d)["attrs"]
        candidates={}
        for c in a.inner.neighbours(d,"has_candidate"):
            ca=a.s.node(c)["attrs"]
            candidates[ca["candidate_id"]]={"status":ca.get("status"),"reason":ca.get("rejection_reason"),"score":ca.get("arbitration_score"),"valuation_trace":ca.get("valuation_trace"),"rejection_trace":ca.get("rejection_trace")}
        selections=[a.s.node(x)["attrs"].get("selected_candidate_id") for x in a.inner.neighbours(d,"has_selection")]
        out.append({"frame":key,"status":attrs.get("status"),"candidate_trace_complete":attrs.get("candidate_trace_complete"),"selection":selections,"candidates":candidates})
    return out

def worker(n,rep,arm):
    from substrate_rs import _native
    a,tasks,scopes,expected=make(n)
    a.inner.scale_audit_reset(); a.inner.scale_audit_per_rule_reset(); a.inner.scale_audit_set_enabled(True); a.inner.scale_audit_set_per_rule_enabled(True)
    w0,c0=time.perf_counter_ns(),time.process_time_ns()
    if arm=="full":
        settle=a.inner.run_rules_report(CAP,False); moved=int(settle["progress_steps"]); turns=0
    else:
        moved=turns=rounds=0
        while rounds<CAP:
            rounds+=1; round_progress=0
            for mt in scopes:
                count=int(a.inner.run_rules_scoped(CAP-moved,False,mt)); moved+=count; round_progress+=count; turns+=1
                if moved>=CAP: break
            if round_progress==0 or moved>=CAP: break
        settle=a.inner.run_rules_report(CAP,False)
    wall,cpu=time.perf_counter_ns()-w0,time.process_time_ns()-c0
    scale=dict(a.inner.scale_audit_snapshot()); a.inner.scale_audit_set_per_rule_enabled(False); a.inner.scale_audit_set_enabled(False)
    proj=project(a,tasks)
    decisions=[row["status"]=="selected" and row["selection"]==[winner] and row["candidates"][winner]["status"]=="selected" and row["candidates"][row["frame"]+"_repair"]["status"]=="rejected" and row["candidates"][row["frame"]+"_unsupported"]["reason"]=="missing_grounding_evidence" for row,winner in zip(proj,expected)]
    native=Path(_native.__file__).resolve()
    return {"size":n,"replicate":rep,"arm":arm,"outcome":settle,"progress_applied":moved,"frame_turns":turns,"wall_ns":wall,"cpu_ns":cpu,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"scale_audit":scale,"projection":proj,"expected_winners":expected,"expected_task_outcomes":decisions,"all_expected_task_outcomes":all(decisions),"native_extension_sha256":sha(native)}

def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True)); return
    locked={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"seed_sha256":sha(SEED),"materializer_sha256":sha(MATERIALIZER),"rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),"py_binding_sha256":sha(ROOT/"runners/dsl/src/py.rs")}
    if sys.argv[1:]==["--lock"]: print(json.dumps(locked,indent=2,sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing lock or locked inputs changed")
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    stale=subprocess.check_output([sys.executable,"-c","from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
    if stale: raise SystemExit("native build stale:\n"+stale)
    jobs=[(n,r,a) for n in SIZES for r in range(REPS) for a in ARMS]; random.Random(20260925).shuffle(jobs); runs=[]
    for n,r,arm in jobs:
        q=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(r),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        row=json.loads(q.stdout); runs.append(row); print(f"n={n} rep={r} arm={arm} status={row['outcome']['status']} wall_ms={row['wall_ns']/1e6:.2f}",flush=True)
    ix={(x["size"],x["replicate"],x["arm"]):x for x in runs}; pairs=[]
    for n in SIZES:
        for r in range(REPS):
            f,s=ix[n,r,"full"],ix[n,r,"scoped"]
            pairs.append({"size":n,"replicate":r,"projection_equal":f["projection"]==s["projection"],"fixed_point_both":f["outcome"]["status"]==s["outcome"]["status"]=="fixed_point","full_candidates":f["scale_audit"].get("cand_enum",0),"scoped_candidates":s["scale_audit"].get("cand_enum",0),"full_term_evaluations":f["scale_audit"].get("term_evals_total",0),"scoped_term_evaluations":s["scale_audit"].get("term_evals_total",0),"full_wall_ns":f["wall_ns"],"scoped_wall_ns":s["wall_ns"],"scoped_frame_turns":s["frame_turns"]})
    checks={"worker_count_24":len(runs)==24,"expected_outcomes":all(x["all_expected_task_outcomes"] for x in runs),"fixed_points":all(x["outcome"]["status"]=="fixed_point" for x in runs),"paired_projection_parity":all(x["projection_equal"] and x["fixed_point_both"] for x in pairs),"complete_matrix":len(pairs)==12}
    summaries=[]
    for n in SIZES:
        ps=[x for x in pairs if x["size"]==n]
        summaries.append({"size":n,"replicates":len(ps),**{f"median_{key}":int(statistics.median(x[key] for x in ps)) for key in ("full_candidates","scoped_candidates","full_term_evaluations","scoped_term_evaluations","full_wall_ns","scoped_wall_ns","scoped_frame_turns")}})
    payload={"schema_version":1,"run_id":"conversation-connected-frame-scale-20260925-v1","claim_boundary":"shared-candidate chain on one native conversation deliberation rule family; not natural task prevalence","locked_inputs":locked,"lock_sha256":sha(LOCK),"checks":checks,"summaries":summaries,"paired":pairs,"runs":runs}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"summaries":summaries},indent=2))
    if not all(checks.values()): raise SystemExit("connected-frame gate failed; preserve raw report")

if __name__=="__main__": main()
