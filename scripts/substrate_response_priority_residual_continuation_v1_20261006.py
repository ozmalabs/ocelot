#!/usr/bin/env python3
"""Compare full closure with selected-area response plus ambient continuation."""
from __future__ import annotations
import base64, gzip, hashlib, importlib.util, json, os, platform, subprocess, sys, time, zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_PREREG_20261006.md"
RUNNER=Path(__file__).resolve()
BASE_PATH=ROOT/"scripts/substrate_live_held_topic_evidence_v1_6.py"
FINGERPRINT_PATH=ROOT/"scripts/substrate_graph_semantic_fingerprint.py"
LOCK=ROOT/"evaluation/substrate_capability/response_priority_residual_continuation_v1_20261006_lock.json"
OUTDIR=ROOT/"evaluation/reports/response_priority_residual_continuation_v1_20261006"
CAPTURE=OUTDIR/"capture.json.gz"
ARMS=("global","priority")
AMBIENT_RULES={"slang_variant_bind_denotes","curiosity_targets_ambivalent_nodes","gr_condition_lapse","sd_decode","sd_transform_decode","sd_infer_dimension"}
RULE_LIFECYCLE_TRACE=os.environ.get("OZMA_RULE_LIFECYCLE_TRACE")=="1"
TRACE_RULES={"retire_duplicate_gap","assess_compromised_boot","reuse_boot_integrity_concern",
    "register_gap_recurrence_identity","register_recurrent_gap_identity",
    "assess_recurrent_gap_for_supervised_promotion","open_human_review_for_recurrent_gap",
    *AMBIENT_RULES}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def object_sha(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def load_base():
    spec=importlib.util.spec_from_file_location("held_topic_base_v16",BASE_PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def lock_payload():
    from substrate_rs import _native
    base=load_base()
    return {"schema_version":1,"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(RUNNER),
        "base_runner_sha256":sha(BASE_PATH),"base_inputs":base.fingerprint(),
        "native_extension_sha256":sha(Path(_native.__file__).resolve()),
        "semantic_fingerprint_source_sha256":sha(FINGERPRINT_PATH),
        "design":{"arms":list(ARMS),"workers_per_arm":3,"turns_per_worker":7,
            "worker_environment":{"PYTHONHASHSEED":"0"},"ambient_rules":sorted(AMBIENT_RULES),
            "selected_areas":["response_critical","global"],"continuation":"unbounded all-area settlement",
            "host_adapter_hooks":"preserved; only inner.run_rules intercepted",
            "rule_lifecycle_trace":RULE_LIFECYCLE_TRACE,
            "event_summary_types":["SelfConcern","GapRecurrence","GapLearningAssessment","HumanReview",
                "Observation","MessageShapeRequest","MonitorRequest","Verdict","Committed"]}}

def digest_graph(agent):
    from substrate_graph_semantic_fingerprint import semantic_graph_fingerprint
    graph=agent.s.graph_to_dict()
    return semantic_graph_fingerprint(graph)[0],len(graph.get("nodes",[])),len(graph.get("edges",[])),graph

EVENT_KEYS={
    "SelfConcern":("gap_identity","status","recurrence_registered","recurrence_counted","learning_stage"),
    "GapRecurrence":("gap_identity","recurrence_count","assessment_recorded","status"),
    "GapLearningAssessment":("gap_identity","recurrence_count","promotion_status"),
    "HumanReview":("gap_identity","decision","review_status"),
    "Observation":("key","status","gen_checked","transform_checked","dim_checked"),
    "MessageShapeRequest":("status",),"MonitorRequest":("status",),
    "Verdict":("recoverable","perlocutionary_goal","mode"),"Committed":("utterance",),
}

def summarize_event_state(agent):
    """Compact state at the recurrence/learning and host-scan boundaries."""
    summary={}
    for node_type,keys in EVENT_KEYS.items():
        rows=[]
        for node in agent.s.nodes(node_type):
            if not agent.s.has_node(node): continue
            attrs=agent.s.node(node)["attrs"]
            rows.append({key:attrs.get(key) for key in keys if key in attrs})
        rows.sort(key=lambda row:json.dumps(row,sort_keys=True,default=str))
        summary[node_type]={"count":len(rows),"records":rows}
    return summary

def begin_rule_lifecycle_trace(agent):
    if not RULE_LIFECYCLE_TRACE: return
    native=agent.inner._native
    native.begin_experiment_delta_journal_with_rule_attribution()
    native.checkpoint_experiment_delta_journal()

def finish_rule_lifecycle_trace(agent):
    if not RULE_LIFECYCLE_TRACE: return []
    report=agent.inner.finish_experiment_delta_journal()
    rows=[]
    for event in report.get("rule_write_events",[]):
        name=event.get("rule_name")
        if name not in TRACE_RULES: continue
        node_types=sorted({(v.get("after") or {}).get("type") for v in event.get("node_values",[])
                           if (v.get("after") or {}).get("type")})
        edge_types=sorted({e[1] for e in event.get("edges",[]) if len(e)>1})
        rows.append({"rule_name":name,"progressed":event.get("progressed"),
                     "node_types":node_types,"edge_types":edge_types,
                     "values_truncated":event.get("values_truncated",False)})
    return rows

def assign_areas(agent):
    rows=agent.inner.rule_areas()
    names=[str(row[0]) for row in rows]
    missing=AMBIENT_RULES-set(names)
    if missing: raise RuntimeError(f"ambient rules missing: {sorted(missing)}")
    readback={}
    for name in names:
        area="ambient_work" if name in AMBIENT_RULES else "response_critical"
        if not agent.inner.set_rule_area(name,area): raise RuntimeError(f"area assignment failed: {name}")
        readback[name]=area
    actual={str(row[0]):str(row[1]) for row in agent.inner.rule_areas()}
    if any(actual.get(name)!=area for name,area in readback.items()):
        raise RuntimeError("area assignment readback mismatch")
    return actual

def install_priority_calls(agent):
    calls=[]
    def settle_selected(budget=0):
        started=time.perf_counter_ns()
        report=agent.inner.run_rules_settle_selected(
            ["response_critical","global"],budget_per_area=budget,max_rounds=100000,snapshot_round=False)
        calls.append({"api":"selected_area","elapsed_ns":time.perf_counter_ns()-started,
            "budget_per_area":budget,"steps":int(report["steps"]),"rounds":int(report["n_rounds"]),
            "requested_areas":["response_critical","global"],
            "selected_areas":report["areas"],"round_rows":report["rounds"],
            "hit_max_rounds":bool(report["hit_max_rounds"]),
            "residual_by_area":report["residual_by_area"]})
        return int(report["steps"])
    old_run=agent.inner.run_rules
    old_instance=agent.inner.__dict__.get("run_rules",None)
    had_instance="run_rules" in agent.inner.__dict__
    def prioritized_run_rules(*args,**kwargs):
        budget=kwargs.pop("max_steps",args[0] if args else 0)
        if kwargs or len(args)>1: raise TypeError("unsupported run_rules invocation in priority capture")
        return settle_selected(int(budget or 0))
    # Keep WorldAdapter.comprehend intact: it performs host-side
    # conceptualization/monitoring around the substrate closure. Only replace
    # the substrate facade's rule-run entrypoint so those hooks still execute.
    agent.inner.run_rules=prioritized_run_rules
    def restore():
        if had_instance: agent.inner.run_rules=old_instance
        else: delattr(agent.inner,"run_rules")
    return calls,restore

def worker(arm,rep):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    base=load_base();started_inputs=lock_payload()
    agent=WorldAdapter(seeds=())
    t0=time.perf_counter_ns();load_all_seeds(agent);boot_ns=time.perf_counter_ns()-t0
    teaching=[]
    for topic,answer in base.FACTS.items():
        result,work=base.measured(agent,lambda topic=topic,answer=answer:agent.learn_from_teacher(
            topic,{"answer":answer,"learn":[{"phrase":topic,"answer":answer}]}))
        teaching.append({"topic":topic,"returned_answer":result,"work":work})
    area_readback=assign_areas(agent) if arm=="priority" else {str(row[0]):str(row[1]) for row in agent.inner.rule_areas()}
    turns=[]
    for index,task in enumerate(base.TASKS):
        pre_response_events=summarize_event_state(agent)
        if index==0: begin_rule_lifecycle_trace(agent)
        if arm=="priority": calls,restore=install_priority_calls(agent)
        else: calls=[];restore=lambda:None
        row=base.capture_turn(agent,*task)
        restore()
        response_rule_trace=finish_rule_lifecycle_trace(agent) if index==0 else []
        pre_continuation_events=summarize_event_state(agent)
        pre_sha,pre_nodes,pre_edges,_=digest_graph(agent)
        cont_start=time.perf_counter_ns()
        if index==0: begin_rule_lifecycle_trace(agent)
        continuation=agent.inner.run_rules_settle(0,100000,False,False)
        continuation_ns=time.perf_counter_ns()-cont_start
        continuation_rule_trace=finish_rule_lifecycle_trace(agent) if index==0 else []
        post_sha,nodes,edges,graph=digest_graph(agent)
        post_continuation_events=summarize_event_state(agent)
        row["response_priority"]={"arm":arm,"turn_index":index,
            "response_elapsed_ns":row.get("work",{}).get("elapsed_ns"),
            "selected_calls":calls,"pre_continuation_semantic_sha256":pre_sha,
            "pre_continuation_node_count":pre_nodes,"pre_continuation_edge_count":pre_edges,
            "continuation_elapsed_ns":continuation_ns,"continuation_steps":int(continuation["steps"]),
            "continuation_rounds":int(continuation["n_rounds"]),
            "continuation_round_rows":continuation["rounds"],
            "continuation_hit_max_rounds":bool(continuation["hit_max_rounds"]),
            "continuation_residual_by_area":continuation["residual_by_area"],
            "event_state_pre_response":pre_response_events,
            "event_state_pre_continuation":pre_continuation_events,
            "event_state_post_continuation":post_continuation_events,
            "rule_trace_response":response_rule_trace,
            "rule_trace_continuation":continuation_rule_trace,
            "post_continuation_semantic_sha256":post_sha,"post_continuation_node_count":nodes,
            "post_continuation_edge_count":edges}
        if index==0:
            row["response_priority"]["pre_continuation_snapshot_zlib_b64"]=base64.b64encode(zlib.compress(
                json.dumps(_,sort_keys=True,separators=(",",":"),default=str).encode(),6)).decode()
            row["response_priority"]["post_continuation_snapshot_zlib_b64"]=base64.b64encode(zlib.compress(
                json.dumps(graph,sort_keys=True,separators=(",",":"),default=str).encode(),6)).decode()
        if index==len(base.TASKS)-1:
            row["response_priority"]["final_snapshot_zlib_b64"]=base64.b64encode(zlib.compress(
                json.dumps(graph,sort_keys=True,separators=(",",":"),default=str).encode(),6)).decode()
        row.pop("task_frame",None)
        turns.append(row)
    finished_inputs=lock_payload()
    return {"arm":arm,"replicate":rep,"pid":os.getpid(),"boot_ns":boot_ns,
        "teaching":teaching,"turns":turns,"area_assignments":area_readback,
        "worker_input_sha256":object_sha(started_inputs),"worker_source_stable":started_inputs==finished_inputs,
        "environment":{"python":sys.version,"platform":platform.platform(),"PYTHONHASHSEED":os.environ.get("PYTHONHASHSEED")}}

def main():
    if sys.argv[1:]==["--lock"]:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(lock_payload(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
    if len(sys.argv)==4 and sys.argv[1]=="--worker":
        print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,default=str));return
    locked=lock_payload()
    if not LOCK.exists() or json.loads(LOCK.read_text())!=locked: raise SystemExit("source lock absent or stale")
    if CAPTURE.exists(): raise SystemExit(f"refusing to overwrite {CAPTURE}")
    env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
    env["PYTHONHASHSEED"]="0";env["PYTHONPATH"]=os.pathsep.join([str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts"),env.get("PYTHONPATH","")])
    runs=[]
    for arm in ARMS:
        for rep in range(3):
            proc=subprocess.run([sys.executable,str(RUNNER),"--worker",arm,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
            runs.append(json.loads(proc.stdout))
    ended=lock_payload();payload={"schema":"ResponsePriorityResidualContinuationV1","locked_inputs":locked,"post_run_inputs":ended,"runs":runs}
    OUTDIR.mkdir(parents=True,exist_ok=True);CAPTURE.write_bytes(gzip.compress(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode(),6,mtime=0))
    print(json.dumps({"capture":str(CAPTURE.relative_to(ROOT)),"workers":len(runs),"source_stable":ended==locked},indent=2))
    if ended!=locked: raise SystemExit("source changed during capture")

if __name__=="__main__": main()
