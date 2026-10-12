#!/usr/bin/env python3
"""Locked full-vs-scoped replay for overlapping conversation frames."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_READONLY_BOUNDARY_PREREG_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/conversation_readonly_boundary_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_readonly_boundary_v1_20260926.json"
SEED = ROOT / "seeds/conversation_deliberation_phase4a.json"
MATERIALIZER = ROOT / "domains/conversation_deliberation.py"
SIZES, REPS, ARMS, CAP = (1, 2, 4, 8), 3, ("full", "scoped"), 100_000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def make(size):
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains.conversation_deliberation import materialize_deliberation
    a=WorldAdapter(seeds=())
    manifest=manifest_for("conversation_deliberation_phase4a")
    score_rule=next(r for r in manifest["rules"] if r["name"]=="cm4a_score_grounded_candidates")
    score_rule["match"].append(["c","derived_from_evidence","e"])
    score_term=score_rule["effects"][0][3]["__term__"]
    score_term["items"].append({"type":"Attr","node":{"type":"Var","name":"e"},"key":"boundary_value"})
    score_rule_boundary_read=( ["c","derived_from_evidence","e"] in score_rule["match"] and {"type":"Attr","node":{"type":"Var","name":"e"},"key":"boundary_value"} in score_term["items"] )
    if not score_rule_boundary_read: raise RuntimeError("scoring rule does not read shared boundary evidence")
    a.inner.load_seed_manifest(manifest,a.agent)
    tasks=[];scopes=[];candidate_ids=[];edge_candidates=[];boundary=[]
    for j in range(size-1):
        boundary.append(a.s.add_node("BoundaryEvidence",{"boundary_id":f"shared_answer_{j}","boundary_value":float(j+1)}))
    for i in range(size):
        key=f"frame_{i}"
        goal=a.s.add_node("Goal",{"kind":"answer","status":"active","frame_key":key})
        specs=[
          {"candidate_id":f"{key}_repair","kind":"repair","grounding":1.0,"expected_value":0.45,"residual_cost":0.1,"consequence":0.1,"novelty":0.05,"evidence_path":"goal->gap->repair"},
          {"candidate_id":f"{key}_unsupported","kind":"answer","grounding":0.0,"expected_value":4.0,"residual_cost":0.0,"consequence":1.0,"novelty":1.0,"evidence_path":""}]
        incident=[]
        if i>0: incident.append(i-1)
        if i<size-1: incident.append(i)
        if size==1: specs.append({"candidate_id":"local_answer_0","kind":"answer","grounding":1.0,"expected_value":0.8,"residual_cost":0.1,"consequence":0.5,"novelty":0.2,"evidence_path":"goal->fact"})
        for j in incident:
          specs.append({"candidate_id":f"shared_answer_{j}_at_{i}","kind":"answer","grounding":1.0,"expected_value":0.50+0.001*j,"residual_cost":0.05,"consequence":0.1,"novelty":0.05,"evidence_path":"local-copy->shared-read-only-boundary"})
        local_evidence=a.s.add_node("BoundaryEvidence",{"boundary_id":f"local_{i}","boundary_value":0.0})
        candidate_sources={spec["candidate_id"]:local_evidence for spec in specs if not spec["candidate_id"].startswith("shared_answer_")}
        for j in incident: candidate_sources[f"shared_answer_{j}_at_{i}"]=boundary[j]
        d=materialize_deliberation(a,goal=goal,candidates=specs)
        mt=a.inner.add_node("Microtheory",{"name":key})
        candidates=list(a.inner.neighbours(d,"has_candidate"))
        owned=[goal,d,local_evidence,*candidates]
        for node in owned:a.inner.add_edge_unchecked(mt,"has_concept",node,{})
        by_id={a.s.node(c)["attrs"]["candidate_id"]:c for c in candidates}
        for cid,c in by_id.items(): a.inner.add_edge_unchecked(c,"derived_from_evidence",candidate_sources[cid])
        for j in incident:
          c=by_id[f"shared_answer_{j}_at_{i}"]
          edge_candidates.append((i,j,c))
        tasks.append((key,d));scopes.append(mt);candidate_ids.append(set(by_id))
    for j,node in enumerate(boundary):
        for i in (j,j+1):a.inner.add_edge_unchecked(scopes[i],"has_concept",node,{})
    expected=[]
    for i in range(size):
        if size==1: expected.append("local_answer_0");continue
        j=(i if i<size-1 else i-1)
        expected.append(f"shared_answer_{j}_at_{i}")
    return a,tasks,scopes,expected,boundary,edge_candidates,score_rule_boundary_read

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
    a,tasks,scopes,expected,boundary,edge_candidates,score_rule_boundary_read=make(n)
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
    candidate_rows=[[a.s.node(c)["attrs"]["candidate_id"] for c in a.inner.neighbours(d,"has_candidate")] for _,d in tasks]
    candidate_refs=[c for _,d in tasks for c in a.inner.neighbours(d,"has_candidate")]
    return {"size":n,"replicate":rep,"arm":arm,"pid":os.getpid(),"outcome":settle,"progress_applied":moved,"frame_turns":turns,"wall_ns":wall,"cpu_ns":cpu,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"scale_audit":scale,"projection":proj,"expected_winners":expected,"expected_task_outcomes":decisions,"all_expected_task_outcomes":all(decisions),"native_extension_sha256":sha(native),"boundary_count":len(boundary),"boundary_owner_sizes":[len(a.inner.in_neighbours(node,"has_concept")) for node in boundary],"boundary_candidate_edges":len(edge_candidates),"candidate_owner_sizes":[len(a.inner.in_neighbours(c,"has_concept")) for c in candidate_refs],"mutable_candidate_ids_unique":len({cid for row in candidate_rows for cid in row})==sum(len(row) for row in candidate_rows),"scoring_rule_boundary_read":score_rule_boundary_read}

def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True)); return
    locked={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"analyzer_sha256":sha(ROOT/"scripts/analyze_substrate_conversation_readonly_boundary_v1.py"),"seed_sha256":sha(SEED),"materializer_sha256":sha(MATERIALIZER),"rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),"py_binding_sha256":sha(ROOT/"runners/dsl/src/py.rs")}
    if sys.argv[1:]==["--lock"]: print(json.dumps(locked,indent=2,sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text())!=locked: raise SystemExit("missing lock or locked inputs changed")
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
    checks={"worker_count_24":len(runs)==24,"expected_outcomes":all(x["all_expected_task_outcomes"] for x in runs),"fixed_points":all(x["outcome"]["status"]=="fixed_point" for x in runs),"paired_projection_parity":all(x["projection_equal"] and x["fixed_point_both"] for x in pairs),"complete_matrix":len(pairs)==12,"boundary_ownership":all(x["boundary_owner_sizes"]==[2]*(x["size"]-1) and x["boundary_count"]==x["size"]-1 for x in runs),"unique_local_mutable_candidates":all(x["mutable_candidate_ids_unique"] and set(x["candidate_owner_sizes"])=={1} for x in runs),"scoring_rule_boundary_read":all(x["scoring_rule_boundary_read"] for x in runs)}
    summaries=[]
    for n in SIZES:
        ps=[x for x in pairs if x["size"]==n]
        summaries.append({"size":n,"replicates":len(ps),**{f"median_{key}":int(statistics.median(x[key] for x in ps)) for key in ("full_candidates","scoped_candidates","full_term_evaluations","scoped_term_evaluations","full_wall_ns","scoped_wall_ns","scoped_frame_turns")}})
    payload={"schema_version":1,"run_id":"conversation-readonly-boundary-20260926-v1","claim_boundary":"frame-local mutable candidate copies read a shared immutable evidence node on one native conversation deliberation rule family; not natural task prevalence","locked_inputs":locked,"lock_sha256":sha(LOCK),"checks":checks,"summaries":summaries,"paired":pairs,"schedule":[list(x) for x in jobs],"native_extension_sha256":runs[0]["native_extension_sha256"],"runs":runs}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"summaries":summaries},indent=2))
    if not all(checks.values()): raise SystemExit("connected-frame gate failed; preserve raw report")

if __name__=="__main__": main()
