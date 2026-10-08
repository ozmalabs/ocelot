#!/usr/bin/env python3
"""Compare global and response-priority settlement on five live task routes."""
from __future__ import annotations
import gzip, hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_RESPONSE_PRIORITY_CROSS_FAMILY_V1_PREREG_20261006.md"
RUNNER=Path(__file__).resolve()
HARVEST=ROOT/"evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py"
HARVEST_ANALYZER=ROOT/"evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v2.py"
ANALYZER=ROOT/"scripts/analyze_response_priority_cross_family_v1_20261006.py"
FINGERPRINT=ROOT/"scripts/substrate_graph_semantic_fingerprint.py"
LOCK=ROOT/"evaluation/substrate_capability/response_priority_cross_family_v1_20261006_lock.json"
OUTDIR=ROOT/"evaluation/reports/response_priority_cross_family_v1_20261006"
CAPTURE=OUTDIR/"capture.json.gz"
ARMS=("global","priority")
CONDITIONS=("scene_description","held_self_knowledge_answer","self_report_action",
            "unknown_word_clarification","concern_authoring")
AMBIENT={"slang_variant_bind_denotes","curiosity_targets_ambivalent_nodes",
         "gr_condition_lapse","retire_duplicate_gap"}
AREAS=("response_critical","global")

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def obj_sha(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def load_harvest():
    spec=importlib.util.spec_from_file_location("live_conversation_harvest_v2",HARVEST)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def load_harvest_analyzer():
    spec=importlib.util.spec_from_file_location("live_conversation_harvest_v2_analyzer",HARVEST_ANALYZER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def lock_payload():
    from substrate_rs import _native
    harvest=load_harvest()
    order=[["global","priority"],["priority","global"]]
    return {"schema_version":1,"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(RUNNER),
        "native_extension_sha256":sha(Path(_native.__file__).resolve()),
        "semantic_fingerprint_sha256":sha(FINGERPRINT),
        "analyzer_sha256":sha(ANALYZER),"harvest_runner_sha256":sha(HARVEST),
        "harvest_analyzer_sha256":sha(HARVEST_ANALYZER),
        "harvest_inputs":harvest.inputs(),
        "design":{"conditions":list(CONDITIONS),"arms":list(ARMS),"replicates_per_condition":2,
            "workers_per_condition":4,"workers_total":20,"arm_order_by_replicate":order,
            "ambient_rules":sorted(AMBIENT),"selected_areas":list(AREAS),
            "continuation":"unbounded all-area settlement","pythonhashseed":"0",
            "rule_write_attribution":False,"host_adapter_hooks":"preserved"}}

def digest(agent):
    from substrate_graph_semantic_fingerprint import semantic_graph_fingerprint
    graph=agent.inner.graph_to_dict()
    fp,meta=semantic_graph_fingerprint(graph)
    return fp,meta["node_count"],meta["edge_count"]

def assign_areas(agent):
    rows=agent.inner.rule_areas();names=[str(row[0]) for row in rows]
    missing=AMBIENT-set(names)
    if missing: raise RuntimeError(f"partition rules missing: {sorted(missing)}")
    for name in names:
        area="ambient_work" if name in AMBIENT else "response_critical"
        if not agent.inner.set_rule_area(name,area): raise RuntimeError(f"area assignment failed: {name}")
    readback={str(n):str(a) for n,a in agent.inner.rule_areas()}
    if any(readback.get(n)!=("ambient_work" if n in AMBIENT else "response_critical") for n in names):
        raise RuntimeError("area assignment readback mismatch")
    return readback

def worker(condition,arm,rep):
    from domains.engine_provenance import assert_measuring_engine
    assert_measuring_engine()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.conversation_action as ca
    harvest=load_harvest();harvest_analyzer=load_harvest_analyzer()
    started=lock_payload();harvest_inputs=started["harvest_inputs"]
    agent=WorldAdapter(seeds=())
    t=time.perf_counter_ns();cpu=time.process_time_ns();boot=load_all_seeds(agent)
    boot_wall=time.perf_counter_ns()-t;boot_cpu=time.process_time_ns()-cpu
    if condition=="scene_description": ca.attach_scene(agent,harvest.SCENE)
    teacher_calls={"count":0}
    try: agent.set_self_teacher(lambda q:(teacher_calls.__setitem__("count",teacher_calls["count"]+1),"teacher")[1])
    except Exception: pass
    area_readback=assign_areas(agent) if arm=="priority" else {str(n):str(a) for n,a in agent.inner.rule_areas()}
    old_action=ca.act_on_instruction;old_ensure=ca._ensure_describe
    actions=[];ensure=[]
    def action_wrap(a,comp,inbound=None):
        out=old_action(a,comp,inbound)
        actions.append({k:out.get(k) for k in ("route","goal_kind","reply","concern")})
        return out
    def ensure_wrap(a):
        before=int(a.inner.rule_count());out=old_ensure(a)
        ensure.append({"rule_delta":int(a.inner.rule_count())-before,"available":out is not None})
        return out
    ca.act_on_instruction=action_wrap;ca._ensure_describe=ensure_wrap
    selected_calls=[];old_run=None;old_instance=None;had_instance=False
    if arm=="priority":
        old_run=agent.inner.run_rules;had_instance="run_rules" in agent.inner.__dict__
        old_instance=agent.inner.__dict__.get("run_rules")
        def settle_selected(*args,**kwargs):
            budget=kwargs.pop("max_steps",args[0] if args else 0)
            if kwargs or len(args)>1: raise TypeError("unsupported run_rules call")
            start=time.perf_counter_ns()
            report=agent.inner.run_rules_settle_selected(list(AREAS),budget_per_area=int(budget or 0),
                max_rounds=100000,snapshot_round=False)
            attempts=sum(row["attempted"] for rnd in report["rounds"] for row in rnd["rows"])
            selected_calls.append({"elapsed_ns":time.perf_counter_ns()-start,"budget_per_area":int(budget or 0),
                "steps":int(report["steps"]),"attempts":attempts,"rounds":int(report["n_rounds"]),
                "hit_max_rounds":bool(report["hit_max_rounds"]),"selected_areas":report["areas"],
                "residual_by_area":report["residual_by_area"]})
            return int(report["steps"])
        agent.inner.run_rules=settle_selected
    text,speech_act=harvest.TASKS[condition]
    rules_before=int(agent.inner.rule_count());start=time.perf_counter_ns();cpu=time.process_time_ns();error=None
    try: reply=str(agent.converse(text,speech_act=speech_act,speaker="alice"))
    except BaseException as exc: reply="";error=f"{type(exc).__name__}: {exc}"
    response_wall=time.perf_counter_ns()-start;response_cpu=time.process_time_ns()-cpu
    if arm=="priority":
        if had_instance: agent.inner.run_rules=old_instance
        else: delattr(agent.inner,"run_rules")
    ca.act_on_instruction=old_action;ca._ensure_describe=old_ensure
    rules_after=int(agent.inner.rule_count())
    before_fp,before_nodes,before_edges=digest(agent)
    start=time.perf_counter_ns();cpu=time.process_time_ns()
    continuation=agent.inner.run_rules_settle(0,100000,False,False)
    continuation_wall=time.perf_counter_ns()-start;continuation_cpu=time.process_time_ns()-cpu
    after_fp,nodes,edges=digest(agent)
    inbound=[m for m in agent.s.nodes("Message") if agent.s.node(m)["attrs"].get("from")=="interlocutor" and agent.s.node(m)["attrs"].get("text")==text]
    inbound.sort(key=lambda n:int(n.value if hasattr(n,"value") else n));turn=[]
    for msg in inbound:
        ma=agent.s.node(msg)["attrs"];iid=ma.get("communication_interpretation_id")
        interp=dict(agent.s.node(iid)["attrs"]) if iid is not None and agent.s.has_node(iid) else {}
        goals=[];outbound=[]
        for g in agent.s.nodes("Goal"):
            if msg not in agent.inner.neighbours(g,"comprehends"): continue
            ga=agent.s.node(g)["attrs"];state=ma.get("discourse_state_id");events=[]
            if state is not None:
                for e in agent.inner.neighbours(state,"has_event"):
                    if g in agent.inner.neighbours(e,"for_goal"):events.append(agent.s.node(e)["attrs"].get("kind"))
            goals.append({"kind":ga.get("kind"),"status":ga.get("lifecycle_status"),"events":events})
        for m in agent.s.nodes("Message"):
            aa=agent.s.node(m)["attrs"]
            if aa.get("from") in ("agent","adapter") and msg in agent.inner.neighbours(m,"responds_to"):
                acts=[agent.s.node(x)["attrs"].get("name") for x in agent.inner.neighbours(m,"has_speech_act")]
                outbound.append({"text":aa.get("text"),"trouble_source":aa.get("trouble_source"),
                    "expects_response":aa.get("expects_response"),"speech_acts":acts})
        turn.append({"goal_count":len(goals),"goals":goals,
            "interpretation":{k:interp.get(k) for k in ("kind","dispatch_path","cognitive_disposition","arbitration_basis")},
            "communication_route":ma.get("communication_route"),"outbound_messages":outbound})
    task_row={"condition":condition,"replicate":rep,"pid":os.getpid(),"prompt":text,"speech_act":speech_act,
        "locked_inputs":harvest_inputs,"post_run_inputs":harvest.inputs(),"source_stable":started==lock_payload(),
        "boot_loaded":boot.get("loaded"),"boot_failures":len(boot.get("failed",[])),"boot_wall_ns":boot_wall,
        "boot_process_cpu_ns":boot_cpu,"task_wall_ns":response_wall,"task_process_cpu_ns":response_cpu,
        "rule_count_delta":rules_after-rules_before,"faculty_build_calls":ensure,"action_results":actions,
        "reply":reply,"error":error,"teacher_calls":teacher_calls["count"],"turns":turn,
        "environment":{"python":sys.version,"platform":platform.platform(),"PYTHONHASHSEED":os.environ.get("PYTHONHASHSEED")}}
    # The harvest analyzer is the independent task oracle. Its self-report
    # route check correctly tests membership in the route-name list; the
    # harvest runner's task_ok currently calls .get() on those route strings.
    # Preserve the runner's extra scene-faculty build contract explicitly.
    utility=bool(task_row["source_stable"] and task_row["locked_inputs"]==harvest_inputs==task_row["post_run_inputs"]
        and task_row["boot_loaded"] and task_row["error"] is None and len(task_row["turns"])==1
        and harvest_analyzer.task_oracle(task_row))
    if condition=="scene_description":
        utility=utility and len(ensure)==1 and ensure[0]["rule_delta"]==18
    ended=lock_payload()
    return {"condition":condition,"arm":arm,"replicate":rep,"pid":os.getpid(),"prompt":text,
        "speech_act":speech_act,"reply":reply,"error":error,"task_utility_pass":utility,
        "utility_check_input":task_row,
        "action_results":actions,"faculty_build_calls":ensure,"teacher_calls":teacher_calls["count"],
        "turns":turn,"boot_wall_ns":boot_wall,"boot_process_cpu_ns":boot_cpu,
        "response_wall_ns":response_wall,"response_process_cpu_ns":response_cpu,
        "continuation_wall_ns":continuation_wall,"continuation_process_cpu_ns":continuation_cpu,
        "selected_calls":selected_calls,"area_assignments":area_readback,
        "pre_continuation_graph":{"fingerprint":before_fp,"nodes":before_nodes,"edges":before_edges},
        "final_graph":{"fingerprint":after_fp,"nodes":nodes,"edges":edges},
        "continuation":{"steps":int(continuation["steps"]),"rounds":int(continuation["n_rounds"]),
            "hit_max_rounds":bool(continuation["hit_max_rounds"]),"residual_by_area":continuation["residual_by_area"]},
        "worker_source_stable":started==ended,"worker_input_sha256":obj_sha(started),
        "environment":{"python":sys.version,"platform":platform.platform(),"PYTHONHASHSEED":os.environ.get("PYTHONHASHSEED")}}

def main():
    if sys.argv[1:]==["--lock"]:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(lock_payload(),indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT));return
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        print(json.dumps(worker(sys.argv[2],sys.argv[3],int(sys.argv[4])),sort_keys=True,default=str));return
    locked=lock_payload()
    if not LOCK.exists() or json.loads(LOCK.read_text())!=locked: raise SystemExit("source lock absent or stale")
    if CAPTURE.exists(): raise SystemExit(f"refusing to overwrite {CAPTURE}")
    env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
    env.pop("OZMA_RULE_LIFECYCLE_TRACE",None);env["PYTHONHASHSEED"]="0"
    env["PYTHONPATH"]=os.pathsep.join([str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts"),env.get("PYTHONPATH","")])
    runs=[];orders=(("global","priority"),("priority","global"))
    for condition in CONDITIONS:
        for rep,order in enumerate(orders):
            for arm in order:
                try:
                    proc=subprocess.run([sys.executable,str(RUNNER),"--worker",condition,arm,str(rep)],
                        cwd=ROOT,env=env,text=True,capture_output=True,check=True)
                except subprocess.CalledProcessError as exc:
                    sys.stderr.write(exc.stderr or "worker failed without stderr\n")
                    raise
                runs.append(json.loads(proc.stdout))
    ended=lock_payload();payload={"schema":"ResponsePriorityCrossFamilyV1","locked_inputs":locked,
        "post_run_inputs":ended,"runs":runs}
    OUTDIR.mkdir(parents=True,exist_ok=True)
    CAPTURE.write_bytes(gzip.compress(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode(),6,mtime=0))
    print(json.dumps({"capture":str(CAPTURE.relative_to(ROOT)),"workers":len(runs),"source_stable":ended==locked},indent=2))
    if ended!=locked: raise SystemExit("source changed during capture")

if __name__=="__main__": main()
