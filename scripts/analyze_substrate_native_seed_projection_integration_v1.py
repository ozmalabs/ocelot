#!/usr/bin/env python3
"""Validate native seed projection integration parity report."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_native_seed_projection_integration_v1_20260925.json"
BASE=ROOT/"evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json"
LOCK=ROOT/"evaluation/substrate_capability/native_seed_projection_integration_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_native_seed_projection_integration_v1_analysis_20260925.json"
KEYS=("report","node_count","edge_count","graph_sha256","grammar_sha256","rule_store_sha256","rule_access_sha256","active_rule_count","rule_order","rule_order_sha256")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def state(w):return {k:w[k] for k in KEYS}
def main():
    raw=json.loads(RAW.read_text());base=json.loads(BASE.read_text());lock=json.loads(LOCK.read_text());errors=[]
    if raw["lock"]!=lock:errors.append("raw lock mismatch")
    if raw["source_hashes_after"]!=lock["sources"]:errors.append("source hashes changed during measurement")
    post_measurement_source_drift=[p for p,h in lock["sources"].items() if sha(ROOT/p)!=h]
    runner=ROOT/"scripts/substrate_native_seed_projection_integration_probe_v1.py"
    if sha(runner)!=lock["runner_sha256"] or raw.get("runner_sha256_after")!=lock["runner_sha256"]:errors.append("runner hash differs from lock")
    protocol=ROOT/"docs/research/engine_substrate/SUBSTRATE_NATIVE_SEED_PROJECTION_INTEGRATION_PREREG_20260925.md"
    if sha(protocol)!=lock["protocol_sha256"]:errors.append("protocol differs from lock")
    if sha(BASE)!=lock["baseline_raw_sha256"]:errors.append("baseline raw file differs from lock")
    if raw["protocol_sha256_after"]!=lock["protocol_sha256"]:errors.append("protocol changed during measurement")
    old=next(x["worker"] for x in base["arms"] if x["requested_size"]==737)
    if len(raw["arms"])!=4 or len({x["worker"]["pid"] for x in raw["arms"]})!=4:errors.append("expected four unique workers")
    if any(state(x["worker"])!=state(old) for x in raw["arms"]):errors.append("frozen baseline state parity mismatch")
    if not raw["within_run_state_parity"] or not raw["frozen_baseline_state_parity"]:errors.append("runner parity gate failed")
    labels={x["label"] for x in raw["contract_probes"]}
    expected={"present_optional_"+k for k in ("nodes","edges","productions","rules","reflexes","id","self_modification_patchable_rules","area","order","latency_class")}
    expected|={"absent_optional_"+k for k in ("nodes","edges","productions","rules","reflexes","id","self_modification_patchable_rules","area","order","latency_class")}
    expected|={"unknown_json","unknown_non_json","non_dict_root","malformed_consumed_node","malformed_consumed_edges","malformed_consumed_productions","malformed_consumed_rules","malformed_consumed_reflexes"}
    if labels!=expected:errors.append("contract probe coverage differs from preregistered matrix")
    for c in raw["contract_probes"]:
        if c["label"].startswith("unknown_") and not c.get("caller_manifest_unchanged"):errors.append(f"caller mutation: {c['label']}")
        if c["label"]=="non_dict_root" and c["error"]!={"class":"ValueError","message":"seed manifest must be a JSON object"}:errors.append("root type error contract changed")
        if c["label"]=="malformed_consumed_node" and c["error"]!={"class":"ValueError","message":"seed node missing local_id"}:errors.append("node error contract changed")
    bymode={m:[x["worker"] for x in raw["arms"] if x["cache_mode"]==m] for m in ("cold","warm")}
    if any(len(v)!=2 for v in bymode.values()):errors.append("expected two cold and two warm runs")
    summary={}
    for mode,rows in bymode.items():
        summary[mode]={"wall_seconds":[x["wall_ns"]/1e9 for x in rows],"wall_median_seconds":statistics.median(x["wall_ns"] for x in rows)/1e9,
                       "cpu_seconds":[x["cpu_ns"]/1e9 for x in rows],"cpu_median_seconds":statistics.median(x["cpu_ns"] for x in rows)/1e9,
                       "peak_rss_kib":[x["peak_rss_native_units"] for x in rows]}
    report={"schema_version":1,"analysis_id":"native-seed-projection-integration-v1-analysis-20260925","raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),
            "all_checks_pass":not errors,"validation_errors":errors,"state_fingerprint_keys":list(KEYS),"contract_probe_count":len(labels),
            "state_parity":"exact against 737-ID frozen baseline and all four current workers" if not errors else "failed",
            "boot_report_failed_seed_count":len(old["report"].get("failed",[])),"boot_report_loaded_seed_count":old["report"].get("loaded"),
            "current_tree_source_drift_since_measurement":post_measurement_source_drift,
            "node_count":old["node_count"],"edge_count":old["edge_count"],"active_rule_count":old["active_rule_count"],"timings":summary,
            "timing_limit":"single-host four-worker before/after envelope; run variation prevents a strong speed claim; timing is secondary to exact parity."}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":report["all_checks_pass"],"validation_errors":errors,"analysis":str(OUT)}));return 0 if not errors else 2
if __name__=="__main__":raise SystemExit(main())
