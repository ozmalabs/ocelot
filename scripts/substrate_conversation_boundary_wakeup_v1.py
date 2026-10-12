#!/usr/bin/env python3
"""Locked full-vs-scoped replay for overlapping conversation frames."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_BOUNDARY_WAKEUP_PREREG_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/conversation_boundary_wakeup_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_boundary_wakeup_v1_20260926.json"
SEED = ROOT / "seeds/conversation_deliberation_phase4a.json"
MATERIALIZER = ROOT / "domains/conversation_deliberation.py"
SIZES, REPS, ARMS, CAP = (2, 4, 8), 3, ("full", "required", "omitted"), 100_000

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

def settle_scoped(a,scopes,frames):
    moved=turns=rounds=0
    while rounds<CAP:
        rounds+=1;round_progress=0
        for i in frames:
            count=int(a.inner.run_rules_scoped(CAP-moved,False,scopes[i]));moved+=count;round_progress+=count;turns+=1
            if moved>=CAP:break
        if round_progress==0 or moved>=CAP:break
    return {"progress_steps":moved,"frame_turns":turns,"rounds":rounds,"status":"fixed_point" if moved<CAP else "budget_exhausted"}

def reopen_for_next_epoch(a,tasks,indices):
    for i in indices:
        d=tasks[i][1]
        for sel in list(a.inner.neighbours(d,"has_selection")):
            a.inner.remove_edge(d,"has_selection",sel);a.inner.remove_node(sel)
        for credit in list(a.inner.neighbours(d,"has_counterfactual_credit")):
            a.inner.remove_edge(d,"has_counterfactual_credit",credit);a.inner.remove_node(credit)
        a.s.set_attr(d,"status","proposed");a.s.set_attr(d,"candidate_trace_complete",0.0)
        for c in a.inner.neighbours(d,"has_candidate"):
            a.s.set_attr(c,"status","proposed");a.s.set_attr(c,"rejection_trace",0.0);a.s.set_attr(c,"counterfactual_trace",0.0);a.s.set_attr(c,"rejection_reason","")

def bump_epoch(a,tasks,indices):
    for i in indices:
        d=tasks[i][1];attrs=a.s.node(d)["attrs"];a.s.set_attr(d,"epoch",float(attrs.get("epoch",0.0))+1.0)

def worker(n,rep,arm):
    from substrate_rs import _native
    a,tasks,scopes,baseline_expected,boundary,edge_candidates,score_rule_boundary_read=make(n)
    if n<2 or len(boundary)!=n-1:raise RuntimeError("bad connected boundary fixture")
    base_out=a.inner.run_rules_report(CAP,False)
    if base_out["status"]!="fixed_point":raise RuntimeError("baseline did not reach fixed point")
    baseline=project(a,tasks)
    baseline_ok=all(row["status"]=="selected" and row["selection"]==[winner] for row,winner in zip(baseline,baseline_expected))
    if not baseline_ok:raise RuntimeError("baseline did not select expected boundary winners")
    affected=[0,1]
    reopen_for_next_epoch(a,tasks,affected)
    t0,c0=time.perf_counter_ns(),time.process_time_ns()
    a.s.set_attr(boundary[0],"boundary_value",4.0)
    bump_epoch(a,tasks,affected)
    if arm=="full":
        closure=a.inner.run_rules_report(CAP,False);pre_repair=project(a,tasks);recovery=None;recovery_progress=0;turns=0
    elif arm=="required":
        closure=settle_scoped(a,scopes,affected);pre_repair=project(a,tasks);recovery=a.inner.run_rules_report(CAP,False);recovery_progress=int(recovery["progress_steps"]);turns=closure["frame_turns"]
    elif arm=="omitted":
        closure=settle_scoped(a,scopes,[0]);pre_repair=project(a,tasks);recovery=a.inner.run_rules_report(CAP,False);recovery_progress=int(recovery["progress_steps"]);turns=closure["frame_turns"]
    else:raise ValueError(arm)
    wall,cpu=time.perf_counter_ns()-t0,time.process_time_ns()-c0
    final=project(a,tasks)
    expected=baseline_expected.copy();expected[1]="shared_answer_0_at_1"
    final_decisions=[row["status"]=="selected" and row["selection"]==[winner] for row,winner in zip(final,expected)]
    a.inner.scale_audit_reset();a.inner.scale_audit_per_rule_reset();a.inner.scale_audit_set_enabled(True);a.inner.scale_audit_set_per_rule_enabled(True)
    # An independently executed zero-progress full pass certifies the terminal recovered state.
    terminal=a.inner.run_rules_report(CAP,False);audit=dict(a.inner.scale_audit_snapshot());a.inner.scale_audit_set_per_rule_enabled(False);a.inner.scale_audit_set_enabled(False)
    if float(a.s.node(boundary[0])["attrs"].get("boundary_value"))!=4.0:raise RuntimeError("closure wrote shared boundary evidence")
    if terminal["status"]!="fixed_point" or int(terminal["progress_steps"])!=0:raise RuntimeError("post-mutation terminal state is not a full-closure fixed point")
    native=Path(_native.__file__).resolve()
    return {"size":n,"replicate":rep,"arm":arm,"pid":os.getpid(),"baseline_fixed_point":base_out["status"],"baseline_projection":baseline,"baseline_expected":baseline_ok,"mutated_boundary_value":float(a.s.node(boundary[0])["attrs"].get("boundary_value")),"affected_frames":affected,"executed_frames":affected if arm in ("full","required") else [0],"omitted_frames":[] if arm in ("full","required") else [1],"mutation_closure":closure,"pre_repair_projection":pre_repair,"recovery_outcome":recovery,"recovery_progress":recovery_progress,"final_projection":final,"expected_final_winners":expected,"all_final_decisions":all(final_decisions),"terminal_full_probe":terminal,"terminal_audit":audit,"wall_ns":wall,"cpu_ns":cpu,"frame_turns":turns,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"native_extension_sha256":sha(native),"native_extension_sha256":sha(native),"boundary_count":len(boundary),"boundary_owner_sizes":[len(a.inner.in_neighbours(node,"has_concept")) for node in boundary],"score_rule_boundary_read":score_rule_boundary_read}

def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True));return
    locked={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"analyzer_sha256":sha(ROOT/"scripts/analyze_substrate_conversation_boundary_wakeup_v1.py"),"base_runner_sha256":sha(ROOT/"scripts/substrate_conversation_readonly_boundary_v1.py"),"seed_sha256":sha(SEED),"materializer_sha256":sha(MATERIALIZER),"rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),"py_binding_sha256":sha(ROOT/"runners/dsl/src/py.rs")}
    if sys.argv[1:]==["--lock"]:print(json.dumps(locked,indent=2,sort_keys=True));return
    if not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit("missing lock or locked inputs changed")
    env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    stale=json.loads(subprocess.check_output([sys.executable,"-c","import json,domains.engine_provenance as ep; print(json.dumps(ep.build_is_stale('.')))"],cwd=ROOT,env=env,text=True))
    if stale:raise SystemExit("native build stale:\n"+stale)
    jobs=[(n,r,a) for n in SIZES for r in range(REPS) for a in ARMS];random.Random(20260929).shuffle(jobs);runs=[]
    for n,r,arm in jobs:
        q=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(r),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        row=json.loads(q.stdout);runs.append(row);print(f"n={n} rep={r} arm={arm} pid={row['pid']} progress={row['mutation_closure']['progress_steps']}",flush=True)
    cells={(x["size"],x["replicate"],x["arm"]):x for x in runs};pairs=[]
    for n in SIZES:
      for r in range(REPS):
        f,req,omit=cells[n,r,"full"],cells[n,r,"required"],cells[n,r,"omitted"]
        pairs.append({"size":n,"replicate":r,"required_matches_full":req["final_projection"]==f["final_projection"],"omission_detected":omit["pre_repair_projection"]!=f["final_projection"],"omitted_recovered":omit["final_projection"]==f["final_projection"],"required_recovery_zero":req["recovery_progress"]==0,"omitted_recovery_positive":omit["recovery_progress"]>0,"full_expected":f["all_final_decisions"],"required_expected":req["all_final_decisions"],"omitted_expected_after_recovery":omit["all_final_decisions"]})
    checks={"worker_count_27":len(runs)==27,"unique_pids":len({x["pid"] for x in runs})==27,"complete_matrix":len(cells)==27,"all_baseline_fixed_point_expected":all(x["baseline_fixed_point"]=="fixed_point" and x["baseline_expected"] for x in runs),"boundary_owner_topology":all(x["boundary_count"]==x["size"]-1 and x["boundary_owner_sizes"]==[2]*(x["size"]-1) for x in runs),"scoring_rule_reads_boundary":all(x["score_rule_boundary_read"] for x in runs),"evidence_unchanged_by_closure":all(x["mutated_boundary_value"]==4.0 for x in runs),"required_notification_schedule":all(x["executed_frames"]==[0,1] and x["omitted_frames"]==[] for x in runs if x["arm"]=="required"),"omission_schedule":all(x["executed_frames"]==[0] and x["omitted_frames"]==[1] for x in runs if x["arm"]=="omitted"),"all_postrepair_fixed_points":all(x["terminal_full_probe"]["status"]=="fixed_point" and x["terminal_full_probe"]["progress_steps"]==0 for x in runs),"required_full_parity":all(x["required_matches_full"] and x["required_recovery_zero"] for x in pairs),"omission_detected_each_case":all(x["omission_detected"] and x["omitted_recovery_positive"] for x in pairs),"omission_recovers_exactly":all(x["omitted_recovered"] and x["omitted_expected_after_recovery"] for x in pairs),"full_required_expected":all(x["full_expected"] and x["required_expected"] for x in pairs)}
    payload={"schema_version":1,"run_id":"conversation-boundary-wakeup-20260926-v1","claim_boundary":"explicit caller notification for one changed read-only evidence boundary in one authored conversation chain; no native observer or natural topology claim","locked_inputs":locked,"lock_sha256":sha(LOCK),"schedule":[list(x) for x in jobs],"checks":checks,"pairs":pairs,"runs":runs,"native_extension_sha256":runs[0]["native_extension_sha256"]}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"pairs":pairs},indent=2))
    if not all(checks.values()):raise SystemExit("boundary wakeup gate failed; preserve raw report")

if __name__=="__main__": main()
