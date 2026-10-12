#!/usr/bin/env python3
"""Independent integrity and outcome analyzer for the Stacks code panel."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FRAME=ROOT/"evaluation/reports/stacks_code_reading_frame_v1_20260927.json"
RAW=ROOT/"evaluation/reports/stacks_code_reading_panel_v1_20260927.json"
LOG=None
DATA=ROOT/"data/stacks/repo/scripts"
def sha(b): return hashlib.sha256(b).hexdigest()
def reconstructed():
    rows=[]
    for p in sorted(DATA.glob("*.py")):
        raw=p.read_bytes(); text=raw.decode("utf-8"); tree=ast.parse(text,filename=p.name)
        for n in tree.body:
            if isinstance(n,ast.FunctionDef):
                segment=ast.get_source_segment(text,n)
                rows.append({"file":p.relative_to(ROOT).as_posix(),"module_sha256":sha(raw),"line":n.lineno,
                    "function":n.name,"function_sha256":sha(segment.encode("utf-8"))})
    return rows
def main():
    frame=json.loads(FRAME.read_text());raw=json.loads(RAW.read_text()); rows=reconstructed()
    runs=raw.get("runs",[])
    manifest=raw.get("run_manifest",{}); capture=manifest.get("stdout_stderr_capture") or {}
    log_path=ROOT/capture.get("path", "__missing_console_capture__")
    log_bytes=log_path.read_bytes() if log_path.is_file() else b""
    expected=[(r["file"],r["function"],r["function_sha256"],r["module_sha256"]) for r in rows]
    checks={"candidate_census_37":len(rows)==37,
      "independent_frame_reconstruction":frame.get("candidate_count")==len(rows) and frame.get("selected")==rows,
      "two_fresh_workers":len(runs)==2 and len({r.get("pid") for r in runs})==2,
      "workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in runs),
      "all_tasks_per_worker":all(len(r.get("tasks",[]))==len(rows) for r in runs),
      "source_locks_stable":raw.get("post_run_inputs")==raw.get("locked_inputs") and all(r.get("source_stable") and r.get("locked_inputs_before")==raw.get("locked_inputs")==r.get("locked_inputs_after") for r in runs),
      "shared_manifest_and_hashed_console":manifest.get("manifest_schema")=="substrate-run-manifest-v1" and manifest.get("exit_status")==0 and bool(log_bytes) and capture.get("bytes")==len(log_bytes) and capture.get("sha256")==sha(log_bytes) and all(f"completed=worker{i} rc=0".encode() in log_bytes for i in (0,1)),
      "source_hash_schedule_exact":all([(t["file"],t["function"],t["function_sha256_expected"],t["module_sha256_expected"]) for t in r.get("tasks",[]) ]==expected and all(t["module_sha256_observed"]==t["module_sha256_expected"] and t["error"] is None for t in r.get("tasks",[])) for r in runs),
      "worker_outcome_parity":len(runs)==2 and [[(t["construction_present"],t["route_minted"],t["term_present"],t["error"]) for t in r.get("tasks",[])] for r in runs][0]==[[(t["construction_present"],t["route_minted"],t["term_present"],t["error"]) for t in r.get("tasks",[])] for r in runs][1]}
    summaries=[]
    for run in runs:
        ts=run.get("tasks",[]); post=ts[1:]
        durations=sorted(t["task_wall_ns"] for t in ts)
        summaries.append({"replicate":run.get("replicate"),"tasks":len(ts),"construction_count":sum(t["construction_present"] for t in ts),
          "term_count":sum(t["term_present"] for t in ts),"minted_route_count":sum(t["route_minted"] for t in ts),
          "receipt_count":sum(t["receipt_delta"] for t in ts),"post_cold_receipt_tasks":sum(t["receipt_delta"]>0 for t in post),
          "post_cold_mint_tasks":sum(t["route_minted"] for t in post),"median_wall_ns":durations[len(durations)//2] if durations else None,
          "p95_wall_ns":durations[min(len(durations)-1,int(.95*len(durations)))] if durations else None,
          "boot_loaded":run.get("boot",{}).get("loaded"),"boot_total":run.get("boot",{}).get("total"),
          "boot_failures":len(run.get("boot",{}).get("failed",[])),"peak_rss_bytes":run.get("runtime",{}).get("peak_rss_bytes"),
          "by_file":{f:{"functions":sum(t["file"]==f for t in ts),"constructions":sum(t["file"]==f and t["construction_present"] for t in ts),"terms":sum(t["file"]==f and t["term_present"] for t in ts)} for f in sorted({t["file"] for t in ts})}})
    result={"checks":checks,"pass":all(checks.values()),"summary":{"candidate_count":len(rows),"workers":summaries,
      "claim_boundary":raw.get("claim_boundary")}}
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result["pass"]: raise SystemExit("Stacks code-reading analysis failed")
if __name__=="__main__":main()
