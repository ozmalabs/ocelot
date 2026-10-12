#!/usr/bin/env python3
"""Validate and summarize native seed projection measurement."""
from __future__ import annotations
import hashlib, json, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_native_seed_projection_probe_v1_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_native_seed_projection_probe_v1_analysis_20260925.json"
LOCK=ROOT/"evaluation/substrate_capability/native_seed_projection_lock_20260925.json"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fp(w): return {k:w[k] for k in ("report","node_count","edge_count","graph_sha256","grammar_sha256","rule_store_sha256","rule_access_sha256","active_rule_count","rule_order_sha256")}
def main():
    raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); errors=[]; summaries={}
    if raw["lock"]!=lock: errors.append("raw lock differs from lock file")
    if raw["source_hashes_after"]!=lock["sources"]: errors.append("source hashes changed during probe")
    if raw["protocol_sha256_after"]!=lock["protocol_sha256"]: errors.append("protocol changed during probe")
    if raw["runner_sha256_after"]!=lock["runner_sha256"]: errors.append("runner changed during probe")
    if len(raw["arms"])!=12 or not raw["unique_processes"]: errors.append("expected 12 unique worker processes")
    for size in (512,737):
        groups={mode:[a["worker"] for a in raw["arms"] if a["size"]==size and a["mode"]==mode] for mode in ("control","projection")}
        if any(len(rows)!=3 for rows in groups.values()): errors.append(f"N={size}: expected three workers per arm")
        allrows=groups["control"]+groups["projection"]
        if allrows and any(fp(w)!=fp(allrows[0]) for w in allrows): errors.append(f"N={size}: complete state/report parity failed")
        stats={m:{r["native_call_stats"]["calls"] for r in rows} for m,rows in groups.items()}
        if not all(len(x)==1 for x in stats.values()) or stats["control"]!=stats["projection"]: errors.append(f"N={size}: call counts differ across arms/repeats")
        measured={}
        for mode,rows in groups.items():
            wall=[r["wall_ns"] for r in rows]; cpu=[r["cpu_ns"] for r in rows]; rss=[r["peak_rss_native_units"] for r in rows]
            first=rows[0]["native_call_stats"]
            if any(r["native_call_stats"]["input_bytes"]!=first["input_bytes"] or r["native_call_stats"]["projected_bytes"]!=first["projected_bytes"] for r in rows): errors.append(f"N={size} {mode}: byte totals differ")
            measured[mode]={"wall_seconds": [x/1e9 for x in wall],"wall_median_seconds":statistics.median(wall)/1e9,
                            "cpu_seconds":[x/1e9 for x in cpu],"cpu_median_seconds":statistics.median(cpu)/1e9,
                            "peak_rss_kib":[x for x in rss],"native_calls":first["calls"],
                            "input_json_bytes":first["input_bytes"],"sent_json_bytes":first["projected_bytes"]}
        c=measured["control"]; p=measured["projection"]
        summaries[str(size)]={"state_parity":bool(allrows) and all(fp(w)==fp(allrows[0]) for w in allrows),"arms":measured,
            "byte_reduction_fraction":1-p["sent_json_bytes"]/c["input_json_bytes"],
            "wall_median_reduction_fraction":1-p["wall_median_seconds"]/c["wall_median_seconds"],
            "cpu_median_reduction_fraction":1-p["cpu_median_seconds"]/c["cpu_median_seconds"],
            "rss_note":"whole-process ru_maxrss; manifest references retained for post-timing byte accounting"}
    report={"schema_version":1,"analysis_id":"native-seed-projection-probe-v1-analysis-20260925",
            "raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"validation_errors":errors,
            "all_checks_pass":not errors,"sizes":summaries,
            "interpretation_limit":"Exploratory single-host startup intervention; three workers per arm/size; instrumentation retains manifest references and elevates RSS; results localize this PyO3 boundary only."}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"all_checks_pass":report["all_checks_pass"],"validation_errors":errors,"analysis":str(OUT)}))
    return 0 if not errors else 2
if __name__=="__main__": raise SystemExit(main())
