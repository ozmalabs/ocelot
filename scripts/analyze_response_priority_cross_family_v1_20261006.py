#!/usr/bin/env python3
"""Independent checks for the source-locked cross-family scheduler capture."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/"evaluation/reports/response_priority_cross_family_v1_20261006/capture.json.gz"
LOCK=ROOT/"evaluation/substrate_capability/response_priority_cross_family_v1_20261006_lock.json"
OUT=ROOT/"evaluation/reports/response_priority_cross_family_v1_20261006/analysis.json"
ANALYZER=Path(__file__).resolve()
HARVEST=ROOT/"evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),default=str)
def load_harvest():
 spec=importlib.util.spec_from_file_location("live_conversation_harvest_v2",HARVEST)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def load_harvest_analyzer():
 spec=importlib.util.spec_from_file_location("live_conversation_harvest_v2_analyzer",ROOT/"evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v2.py")
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

raw=CAPTURE.read_bytes();capture=json.loads(gzip.decompress(raw));runs=capture["runs"]
locked=json.loads(LOCK.read_text());conditions=locked["design"]["conditions"]
checks={
 "twenty_workers":len(runs)==20,
 "four_workers_per_condition":all(sum(r["condition"]==c for r in runs)==4 for c in conditions),
 "ten_workers_per_arm":all(sum(r["arm"]==a for r in runs)==10 for a in ("global","priority")),
 "distinct_pids":len({r["pid"] for r in runs})==20,
 "source_lock_matches":locked==capture["locked_inputs"],
 "source_stable":capture["post_run_inputs"]==locked and all(r["worker_source_stable"] for r in runs),
 "worker_input_hash_stable":all(len(r["worker_input_sha256"])==64 for r in runs),
 "hash_seed_fixed":all(r["environment"].get("PYTHONHASHSEED")=="0" for r in runs),
 "order_counterbalanced":all([[r["arm"] for r in runs if r["condition"]==c and r["replicate"]==rep]
     for rep in (0,1)]==[["global","priority"],["priority","global"]] for c in conditions),
 "mutation_journaling_disabled":all(not r["selected_calls"] or
     locked["design"]["rule_write_attribution"] is False for r in runs),
}
harvest=load_harvest();harvest_analyzer=load_harvest_analyzer();task_utility={};paired=[];costs=[]
for row in runs:
    ui=row["utility_check_input"]
    valid_inputs=(ui.get("source_stable") and ui.get("locked_inputs")==locked["harvest_inputs"]==ui.get("post_run_inputs")
        and ui.get("boot_loaded",0)>0 and ui.get("error") is None and len(ui.get("turns",[]))==1)
    oracle=bool(valid_inputs and harvest_analyzer.task_oracle(ui))
    if row["condition"]=="scene_description":
        oracle=oracle and len(ui.get("faculty_build_calls",[]))==1 and ui["faculty_build_calls"][0].get("rule_delta")==18
    key=f"{row['condition']}__{row['arm']}__{row['replicate']}"
    task_utility[key]=bool(oracle)
    checks[f"stored_utility_matches_oracle__{key}"]=task_utility[key]==bool(row["task_utility_pass"])
baseline_utility={"scene_description":False,"held_self_knowledge_answer":True,
    "self_report_action":True,"unknown_word_clarification":True,"concern_authoring":False}
checks["source_harvest_utility_profile_reproduced"]=all(
    task_utility[f"{condition}__{arm}__{rep}"]==baseline_utility[condition]
    for condition in conditions for arm in ("global","priority") for rep in (0,1))
checks["priority_has_no_paired_utility_regression"]=all(
    not task_utility[f"{condition}__global__{rep}"] or task_utility[f"{condition}__priority__{rep}"]
    for condition in conditions for rep in (0,1))
checks["paired_utility_profile_equal"]=all(
    task_utility[f"{condition}__global__{rep}"]==task_utility[f"{condition}__priority__{rep}"]
    for condition in conditions for rep in (0,1))
for condition in conditions:
    for rep in (0,1):
        pair={r["arm"]:r for r in runs if r["condition"]==condition and r["replicate"]==rep}
        g=pair.get("global",{});p=pair.get("priority",{})
        checks[f"pair_present__{condition}__{rep}"]=set(pair)=={"global","priority"}
        if len(pair)!=2: continue
        checks[f"reply_parity__{condition}__{rep}"]=g["reply"]==p["reply"]
        checks[f"action_route_parity__{condition}__{rep}"]=[(x.get("route"),x.get("goal_kind"),x.get("reply")) for x in g["action_results"]]==[(x.get("route"),x.get("goal_kind"),x.get("reply")) for x in p["action_results"]]
        checks[f"turn_outcome_parity__{condition}__{rep}"]=canonical(g["turns"])==canonical(p["turns"])
        checks[f"final_semantic_graph_parity__{condition}__{rep}"]=g["final_graph"]["fingerprint"]==p["final_graph"]["fingerprint"]
        checks[f"final_cardinality_parity__{condition}__{rep}"]=(g["final_graph"]["nodes"],g["final_graph"]["edges"])==(p["final_graph"]["nodes"],p["final_graph"]["edges"])
        checks[f"priority_continuation_converges__{condition}__{rep}"]=not p["continuation"]["hit_max_rounds"] and not p["continuation"]["residual_by_area"]
        checks[f"source_inputs_same_within_pair__{condition}__{rep}"]=g["worker_input_sha256"]==p["worker_input_sha256"]
        pair_cost={}
        for arm,r in (("global",g),("priority",p)):
            pair_cost[arm]={"response_ms":r["response_wall_ns"]/1e6,
                "continuation_ms":r["continuation_wall_ns"]/1e6,
                "phase_total_ms":(r["response_wall_ns"]+r["continuation_wall_ns"])/1e6,
                "response_cpu_ms":r["response_process_cpu_ns"]/1e6,
                "continuation_steps":r["continuation"]["steps"],
                "selected_calls":len(r["selected_calls"]),
                "selected_attempts":sum(x["attempts"] for x in r["selected_calls"]),
                "selected_steps":sum(x["steps"] for x in r["selected_calls"]),
                "pre_continuation_residual":sum(x["residual"] for x in r["selected_calls"][-1]["residual_by_area"]) if r["selected_calls"] else 0}
        paired.append({"condition":condition,"replicate":rep,"order":[r["arm"] for r in runs if r["condition"]==condition and r["replicate"]==rep],"cost":pair_cost})
for condition in conditions:
    group=[r for r in runs if r["condition"]==condition]
    record={"condition":condition,"workers":len(group),"utility_pass_by_arm":{
        arm:all(task_utility[f"{condition}__{arm}__{rep}"] for rep in (0,1)) for arm in ("global","priority")}}
    for arm in ("global","priority"):
        rows=[r for r in group if r["arm"]==arm]
        for phase,field in (("response","response_wall_ns"),("continuation","continuation_wall_ns")):
            record[f"{arm}_{phase}_median_ms"]=round(statistics.median(r[field] for r in rows)/1e6,3)
        record[f"{arm}_boot_median_s"]=round(statistics.median(r["boot_wall_ns"] for r in rows)/1e9,3)
        record[f"{arm}_graph_nodes_edges"]=[[r["final_graph"]["nodes"],r["final_graph"]["edges"]] for r in rows]
    costs.append(record)
failed=[k for k,v in checks.items() if not v]
analysis={"schema_version":1,"capture":str(CAPTURE.relative_to(ROOT)),"capture_sha256":hashlib.sha256(raw).hexdigest(),
 "capture_bytes_gzip":CAPTURE.stat().st_size,"lock_sha256":sha(LOCK),"analyzer_sha256":sha(ANALYZER),
 "checks":checks,"capture_integrity_pass":all(checks[k] for k in ("twenty_workers","four_workers_per_condition","ten_workers_per_arm","distinct_pids","source_lock_matches","source_stable","worker_input_hash_stable","hash_seed_fixed","order_counterbalanced","mutation_journaling_disabled")),
 "task_utility":task_utility,"per_condition":costs,"paired_runs":paired,"all_checks_pass":not failed,
 "failed_checks":failed,"interpretation":"Finite result over five repository-authored conversation routes. It does not estimate natural-task prevalence or prove that frame cuts are cheap separators."}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"capture_integrity_pass":analysis["capture_integrity_pass"],"all_checks_pass":analysis["all_checks_pass"],"failed_checks":failed},indent=2))
