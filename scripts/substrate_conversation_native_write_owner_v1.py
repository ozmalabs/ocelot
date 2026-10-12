#!/usr/bin/env python3
"""Locked full-vs-scoped replay for overlapping conversation frames."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_NATIVE_WRITE_OWNER_PREREG_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/conversation_native_write_owner_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_native_write_owner_v1_20260926.json"
SEED = ROOT / "seeds/conversation_deliberation_phase4a.json"
MATERIALIZER = ROOT / "domains/conversation_deliberation.py"
SIZES, REPS, ARMS, CAP = (2, 4, 8), 3, ("full_oracle", "native_required", "native_omitted"), 100_000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def make(size):
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains.conversation_deliberation import materialize_deliberation
    a=WorldAdapter(seeds=())
    manifest=manifest_for("conversation_deliberation_phase4a")
    writer_rule={"name":"conversation_boundary_evidence_writer","area":"deliberation","order":0.5,"match":[["trigger","updates_evidence","evidence"]],"where":{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"trigger"},"key":"active"},"b":{"type":"Lit","value":1.0}},"effects":[["set_attr","evidence","boundary_value",4.0],["set_attr","trigger","active",0.0]]}
    manifest["rules"].insert(0,writer_rule)
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
    controller=a.s.add_node("Microtheory",{"name":"boundary_writer_controller"})
    trigger=a.s.add_node("BoundaryTrigger",{"active":0.0})
    a.inner.add_edge_unchecked(controller,"has_concept",trigger,{})
    a.inner.add_edge_unchecked(controller,"has_concept",boundary[0],{})
    a.inner.add_edge_unchecked(trigger,"updates_evidence",boundary[0],{})
    expected=[]
    for i in range(size):
        if size==1: expected.append("local_answer_0");continue
        j=(i if i<size-1 else i-1)
        expected.append(f"shared_answer_{j}_at_{i}")
    return a,tasks,scopes,expected,boundary,edge_candidates,score_rule_boundary_read,controller,trigger

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
def mid(node):return int(node.value if hasattr(node,"value") else node)
def worker(n,rep,arm):
    from substrate_rs import _native
    a,tasks,scopes,base_expected,boundary,edge_candidates,score_read,controller,trigger=make(n)
    controller_id=mid(controller);consumer_ids={mid(mt):i for i,mt in enumerate(scopes)}
    id_names={controller_id:"writer_controller",**{mid(mt):f"frame_{i}" for i,mt in enumerate(scopes)}}
    baseline_run=a.inner.run_rules_report(CAP,False);baseline_proj=project(a,tasks)
    baseline_ok=baseline_run["status"]=="fixed_point" and all(row["selection"]==[winner] for row,winner in zip(baseline_proj,base_expected))
    affected=[0,1];reopen_for_next_epoch(a,tasks,affected)
    for i in affected:
        d=tasks[i][1];a.s.set_attr(d,"epoch",float(a.s.node(d)["attrs"].get("epoch",0.0))+1.0)
    a.s.set_attr(trigger,"active",1.0)
    call0=time.perf_counter_ns()
    if arm=="full_oracle":
        report=a.inner.run_rules_snapshot_delta_report(CAP,False);pre=project(a,tasks);recovery=None;recovery_steps=0;notified=[];queue_order=[]
        oracle_report=report
        oracle_call_ns=time.perf_counter_ns()-call0;writer_call_ns=None;consumer_schedule_ns=0
    elif arm in ("native_required","native_omitted"):
        writer_report=a.inner.run_rules_scoped_delta_report(controller,CAP,False)
        writer_call_ns=time.perf_counter_ns()-call0
        owner_ids=[int(x) for x in writer_report["affected_microtheories"]]
        unmapped_owner_ids=sorted(x for x in owner_ids if x not in id_names)
        if arm=="native_required":todo=sorted(i for owner,i in consumer_ids.items() if owner in owner_ids)
        else:todo=sorted(i for owner,i in consumer_ids.items() if owner in owner_ids and i!=1)
        visited={controller_id};queue_order=[];reports=[writer_report];consumer0=time.perf_counter_ns()
        while todo:
            i=todo.pop(0);owner=mid(scopes[i])
            if owner in visited:continue
            visited.add(owner);queue_order.append(i)
            scoped_report=a.inner.run_rules_scoped_delta_report(scopes[i],CAP,False);reports.append(scoped_report)
            if scoped_report["hit_progress_budget"] or scoped_report["deferred_effects_pending"]:raise RuntimeError("scoped report capped or deferred effects pending")
            for next_owner in scoped_report["affected_microtheories"]:
                next_owner=int(next_owner)
                if next_owner not in visited and next_owner in consumer_ids:todo.append(consumer_ids[next_owner])
        consumer_schedule_ns=time.perf_counter_ns()-consumer0
        pre=project(a,tasks)
        if arm=="native_omitted":recovery=a.inner.run_rules_report(CAP,False);recovery_steps=int(recovery["progress_steps"])
        else:recovery=a.inner.run_rules_report(CAP,False);recovery_steps=int(recovery["progress_steps"])
        report=writer_report
        oracle_report=None
        oracle_call_ns=None
    else:raise ValueError(arm)
    final=project(a,tasks);terminal=a.inner.run_rules_report(CAP,False)
    values={j:float(j+1) for j in range(n-1)};values[0]=4.0
    expected=[]
    for i in range(n):
        js=([i-1] if i>0 else [])+([i] if i<n-1 else [])
        j=max(js,key=lambda x:values[x]);expected.append(f"shared_answer_{j}_at_{i}")
    decisions=[row["selection"]==[winner] and row["status"]=="selected" for row,winner in zip(final,expected)]
    if terminal["status"]!="fixed_point" or terminal["progress_steps"]!=0:raise RuntimeError("terminal full probe not zero-work fixed point")
    if float(a.s.node(boundary[0])["attrs"]["boundary_value"])!=4.0 or float(a.s.node(trigger)["attrs"]["active"])!=0.0:raise RuntimeError("writer effect did not persist expected values")
    native=Path(_native.__file__).resolve()
    def names(ids):return sorted(id_names[i] for i in map(int,ids) if i in id_names)
    if arm=="full_oracle":
        write_report={"progress_steps":report["progress_steps"],"status":report["status"],"affected_nodes":report["affected_nodes"],"affected_edges":report["affected_edges"],"affected_microtheories":names(report["affected_microtheories"]),"unmapped_owner_ids":sorted(int(x) for x in report["affected_microtheories"] if int(x) not in id_names),"exact_graph_state_diff":report["exact_graph_state_diff"]}
        recovery_steps=0;queue_order=[]
    else:
        write_report={"progress_steps":writer_report["progress_steps"],"status":"scoped","affected_nodes":writer_report["affected_nodes"],"affected_edges":writer_report["affected_edges"],"affected_microtheories":names(writer_report["affected_microtheories"]),"unmapped_owner_ids":unmapped_owner_ids,"hit_progress_budget":writer_report["hit_progress_budget"],"deferred_effects_pending":writer_report["deferred_effects_pending"],"frame_notifications_complete":writer_report["frame_notifications_complete"],"exact_graph_state_diff":False}
    return {"size":n,"replicate":rep,"arm":arm,"pid":os.getpid(),"baseline_status":baseline_run["status"],"baseline_projection":baseline_proj,"baseline_expected":baseline_ok,"pre_repair_projection":pre,"final_projection":final,"expected_final_winners":expected,"all_final_decisions":all(decisions),"writer_report":write_report,"oracle_report":oracle_report,"recovery_steps":recovery_steps,"recovery_outcome":recovery if arm!="full_oracle" else None,"terminal_probe":terminal,"queue_order":queue_order,"notified_consumers":queue_order,"controller_name":"writer_controller","expected_writer_owners":["frame_0","frame_1","writer_controller"],"boundary_value":float(a.s.node(boundary[0])["attrs"]["boundary_value"]),"trigger_active":float(a.s.node(trigger)["attrs"]["active"]),"oracle_call_ns":oracle_call_ns,"writer_call_ns":writer_call_ns,"consumer_schedule_ns":consumer_schedule_ns,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"native_extension_sha256":sha(native),"score_rule_reads_boundary":score_read}
def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True));return
    locked={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"analyzer_sha256":sha(ROOT/"scripts/analyze_substrate_conversation_native_write_owner_v1.py"),"base_runner_sha256":sha(ROOT/"scripts/substrate_conversation_readonly_boundary_v1.py"),"seed_sha256":sha(SEED),"materializer_sha256":sha(MATERIALIZER),"rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),"py_binding_sha256":sha(ROOT/"runners/dsl/src/py.rs")}
    if sys.argv[1:]==["--lock"]:print(json.dumps(locked,indent=2,sort_keys=True));return
    if json.loads(LOCK.read_text())!=locked:raise SystemExit("missing lock or locked inputs changed")
    env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    stale=json.loads(subprocess.check_output([sys.executable,"-c","import json,domains.engine_provenance as ep; print(json.dumps(ep.build_is_stale('.')))"],cwd=ROOT,env=env,text=True))
    if stale:raise SystemExit("native build stale: "+str(stale))
    jobs=[(n,r,a) for n in SIZES for r in range(REPS) for a in ARMS];random.Random(20261001).shuffle(jobs);runs=[]
    for n,r,arm in jobs:
        q=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(r),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True);row=json.loads(q.stdout);runs.append(row);print(f"n={n} rep={r} arm={arm} pid={row['pid']} owners={row['writer_report']['affected_microtheories']}",flush=True)
    cells={(x["size"],x["replicate"],x["arm"]):x for x in runs};pairs=[]
    for n in SIZES:
      for r in range(REPS):
        f,req,omit=cells[n,r,"full_oracle"],cells[n,r,"native_required"],cells[n,r,"native_omitted"]
        pairs.append({"size":n,"replicate":r,"required_full_parity":req["final_projection"]==f["final_projection"],"native_owner_set_matches_oracle":req["writer_report"]["affected_microtheories"]==f["writer_report"]["affected_microtheories"],"observer_nodes_cover_oracle_diff":set(req["writer_report"]["affected_nodes"])<=set(f["writer_report"]["affected_nodes"]),"observer_edges_cover_oracle_diff":set(map(tuple,req["writer_report"]["affected_edges"]))<=set(map(tuple,f["writer_report"]["affected_edges"])),"omission_detected":omit["pre_repair_projection"]!=f["final_projection"],"omitted_catchup_positive":omit["recovery_steps"]>0,"omission_recovers":omit["final_projection"]==f["final_projection"]})
    checks={"worker_count_27":len(runs)==27,"unique_pids":len({x["pid"] for x in runs})==27,"complete_matrix":len(cells)==27,"baseline_valid":all(x["baseline_status"]=="fixed_point" and x["baseline_expected"] for x in runs),"writer_and_read_rules_work":all(x["score_rule_reads_boundary"] and x["boundary_value"]==4.0 and x["trigger_active"]==0.0 for x in runs),"full_exact_oracle":all(x["oracle_report"]["exact_graph_state_diff"] is True and x["oracle_report"]["status"]=="fixed_point" for x in runs if x["arm"]=="full_oracle") and all(not x["writer_report"]["unmapped_owner_ids"] for x in runs if x["arm"]=="full_oracle"),"native_writer_report_complete":all(x["writer_report"]["progress_steps"]>0 and not x["writer_report"]["hit_progress_budget"] and not x["writer_report"]["deferred_effects_pending"] and x["writer_report"]["frame_notifications_complete"] is False and x["writer_report"]["affected_microtheories"]==x["expected_writer_owners"] and not x["writer_report"]["unmapped_owner_ids"] for x in runs if x["arm"]!="full_oracle"),"required_frames_exact":all(x["notified_consumers"]==[0,1] for x in runs if x["arm"]=="native_required"),"omitted_control_exact":all(x["notified_consumers"]==[0] for x in runs if x["arm"]=="native_omitted"),"terminal_probes_zero_work":all(x["terminal_probe"]["status"]=="fixed_point" and x["terminal_probe"]["progress_steps"]==0 for x in runs),"mapped_state_matches_full":all(p["required_full_parity"] for p in pairs),"native_report_matches_full_owner_oracle":all(p["native_owner_set_matches_oracle"] for p in pairs),"native_write_targets_cover_full_graph_diff":all(p["observer_nodes_cover_oracle_diff"] and p["observer_edges_cover_oracle_diff"] for p in pairs),"omission_detected_recovered":all(p["omission_detected"] and p["omitted_catchup_positive"] and p["omission_recovers"] for p in pairs),"all_expected_outcomes":all(x["all_final_decisions"] for x in runs)}
    payload={"schema_version":1,"run_id":"conversation-native-write-owner-20260926-v1","claim_boundary":"existing native scoped mutation observer tested on one rule-authored shared evidence write; callers still drive queue; not automatic notification completeness","locked_inputs":locked,"lock_sha256":sha(LOCK),"schedule":[list(x) for x in jobs],"checks":checks,"pairs":pairs,"runs":runs,"native_extension_sha256":runs[0]["native_extension_sha256"]}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"pairs":pairs},indent=2))
    if not all(checks.values()):raise SystemExit("native write-to-owner gate failed; preserve raw report")

if __name__=="__main__": main()
