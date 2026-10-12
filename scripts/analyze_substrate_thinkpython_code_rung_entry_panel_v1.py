#!/usr/bin/env python3
"""Independent frame and outcome audit for the Think Python code panel."""
from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/think_python_2e"
FRAME=ROOT/"evaluation/reports/thinkpython_code_rung_frame_v1_20260927.json"
RAW=ROOT/"evaluation/reports/thinkpython_code_rung_entry_panel_v1_20260927.json"
BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
def sha(b): return hashlib.sha256(b).hexdigest()

def independently_select():
    rows=[]
    for path in sorted(DATA.glob("ch*.txt")):
        text=path.read_text(encoding="utf-8")
        for i,m in enumerate(BLOCK.finditer(text)):
            src=m.group(1)
            try: tree=ast.parse(src)
            except SyntaxError: continue
            names=[n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
            if not names: continue
            ident=[path.name,i]
            rows.append({"id":ident,"chapter":path.name,"block_index":i,
                "source_sha256":sha(src.encode()),"selection_rank":sha(json.dumps(ident,separators=(",",":")).encode()),
                "function_count":len(names),"selected_function":names[0]})
    return sorted(rows,key=lambda x:(x["selection_rank"],x["chapter"],x["block_index"]))

def summarize(run):
    tasks=run["tasks"]; post=tasks[1:]
    def count_mints(ts): return sum(1 for t in ts for o in t.get("new_observations",[]) if o.get("minted_axis_ids"))
    kinds={}
    for t in tasks:
        for a in t.get("new_capability_axes",[]): kinds[str(a.get("kind") or "missing")]=kinds.get(str(a.get("kind") or "missing"),0)+1
    return {"replicate":run["replicate"],"task_count":len(tasks),
        "post_cold_denominator":len(post),"post_cold_receipt_tasks":sum(bool(t["receipt_delta"]) for t in post),
        "post_cold_entry_rate":sum(bool(t["receipt_delta"]) for t in post)/len(post),
        "post_cold_observation_linked_mints":count_mints(post),"all_task_receipt_count":sum(t["receipt_delta"] for t in tasks),
        "cold_receipt_count":tasks[0]["receipt_delta"],"all_task_mints":count_mints(tasks),
        "construction_count":sum(bool(t["construction_present"]) for t in tasks),
        "term_count":sum(bool(t["term_present"]) for t in tasks),"route_minted_count":sum(bool(t["route_minted"]) for t in tasks),
        "new_shape_signature_count":sum(len(t["new_shape_signatures"]) for t in tasks),
        "new_transform_count":sum(len(t["new_transforms"]) for t in tasks),"capability_axis_type_nodes_added":sum(len(t["new_capability_axes"]) for t in tasks),
        "axis_kind_counts":kinds,"errors":sum(t["error"] is not None for t in tasks),
        "task_wall_ns_median":sorted(t["task_wall_ns"] for t in tasks)[len(tasks)//2],
        "task_wall_ns_p95_nearest_rank":sorted(t["task_wall_ns"] for t in tasks)[(95*len(tasks)+99)//100-1],
        "task_cpu_ns_median":sorted(t["task_cpu_ns"] for t in tasks)[len(tasks)//2],
        "boot_wall_ns":run["boot"]["wall_ns"],"peak_rss_bytes":run["runtime"]["peak_rss_bytes"]}

def main():
    frame=json.loads(FRAME.read_text()); raw=json.loads(RAW.read_text()); candidates=independently_select()
    expected=candidates[:64]
    frame_matches=(frame.get("candidate_count")==len(candidates) and frame.get("selected")==expected)
    checks={"eligible_count_124":len(candidates)==124,"frame_independent_hash_selection":frame_matches,
        "frame_size_64":len(frame.get("selected",[]))==64,"two_workers":len(raw.get("runs",[]))==2,
        "unique_worker_pids":len({r.get("pid") for r in raw.get("runs",[])})==2,
        "all_workers_64_rows":all(len(r.get("tasks",[]))==64 for r in raw.get("runs",[])),
        "source_hashes_match_frame":all(t.get("source_sha256_expected")==t.get("source_sha256_observed")==frame["selected"][t["index"]]["source_sha256"] for r in raw.get("runs",[]) for t in r.get("tasks",[])),
        "schedule_ids_match":all([t["sample_id"] for t in r["tasks"]]==[x["id"] for x in expected] for r in raw.get("runs",[])),
        "worker_source_locks_stable":all(r.get("source_stable") and r.get("locked_inputs_before")==raw.get("locked_inputs")==r.get("locked_inputs_after") for r in raw.get("runs",[])),
        "parent_lock_stable":raw.get("post_run_inputs")==raw.get("locked_inputs"),
        "all_workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in raw.get("runs",[])),
        "no_task_errors":all(t.get("error") is None for r in raw.get("runs",[]) for t in r.get("tasks",[])),
        "worker_schedule_parity":len(raw.get("runs",[]))==2 and [[(t["source_sha256_observed"],t["receipt_delta"],t["construction"],t["route_minted"],t["term_present"],[(o["status"],bool(o["minted_axis_ids"])) for o in t["new_observations"]]) for t in r["tasks"]] for r in raw["runs"]][0]==[[(t["source_sha256_observed"],t["receipt_delta"],t["construction"],t["route_minted"],t["term_present"],[(o["status"],bool(o["minted_axis_ids"])) for o in t["new_observations"]]) for t in r["tasks"]] for r in raw["runs"]][1],
        "raw_excludes_code_text":all(not any(k in t for k in ("source","rendered_python","docstring","what_does")) for r in raw.get("runs",[]) for t in r.get("tasks",[]))}
    result={"checks":checks,"pass":all(checks.values()),"summary":{"candidate_count":len(candidates),"selected_count":len(expected),
        "claim_boundary":raw.get("claim_boundary"),"workers":[summarize(r) for r in raw.get("runs",[])]}}
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result["pass"]: raise SystemExit("independent analysis failed")

if __name__=="__main__": main()
