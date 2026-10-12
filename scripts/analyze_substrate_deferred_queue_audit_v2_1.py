#!/usr/bin/env python3
"""Independent conservation and semantic analysis for deferred queue audit v2."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_deferred_queue_audit_v2_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_deferred_queue_audit_v2_1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/deferred_queue_audit_v2_lock_20260926.json"
FAMILIES=("rule_patches","track_identity","net_collapses")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def metric(audit, name): return int(audit.get("global",{}).get(name,0))

def family_conservation(audit, family, enqueued, drained, batches):
    return (metric(audit,f"deferred_queue:{family}:enqueued_items")==enqueued
            and metric(audit,f"deferred_queue:{family}:drained_items")==drained
            and metric(audit,f"deferred_queue:{family}:drain_batches")==batches
            and metric(audit,f"deferred_queue:{family}:drain_ns")>=0)

def main():
    raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); runs=raw["runs"]
    checks={
      "three_sizes_two_replicates_three_arms":len(runs)==18 and
        {(r["count"],r["replicate"],r["arm"]) for r in runs}==
        {(n,rep,arm) for n in (1,2,4) for rep in range(2) for arm in ("full","scoped_only","scoped_fallback")},
      "fresh_process_per_arm":len({r["pid"] for r in runs})==18,
      "source_lock_unchanged":raw["locked_inputs"]==lock==raw["post_run_inputs"],
      "native_artifact_current_and_constant":len({r["native_extension_sha256"] for r in runs})==1 and
        runs[0]["native_extension_sha256"]==raw["locked_inputs"]["native_extension"],
      "captured_v2_analyzer_sha256_matches":raw["locked_inputs"]["analyzer"]==sha(ROOT/"scripts/analyze_substrate_deferred_queue_audit_v2.py"),
    }
    by={(r["count"],r["replicate"],r["arm"]):r for r in runs}
    all_signatures=[]
    for n in (1,2,4):
      for rep in range(2):
        full=by[n,rep,"full"]; scoped=by[n,rep,"scoped_only"]; fallback=by[n,rep,"scoped_fallback"]
        prefix=f"n{n}_r{rep}"
        checks[f"{prefix}_scoped_reports_deferred_pending"]=bool(scoped["scoped_report"]["deferred_effects_pending"])
        checks[f"{prefix}_fallback_control_started_with_pending"]=bool(fallback["scoped_report"]["deferred_effects_pending"])
        checks[f"{prefix}_full_and_fallback_state_equal"]=full["state"]==fallback["state"]
        checks[f"{prefix}_terminal_fixedpoint"]=full["terminal_status"]==fallback["terminal_status"]=="fixed_point"
        writer_idx=int(full["writer_rule_index"])
        for arm_name, row, phase, enq, drain, batch in (
          ("full",full,"full",1,1,1),("scoped",scoped,"scoped",1,0,0),
          ("fallback",fallback,"fallback",0,1,1)):
          audit=row["audits"][phase]
          for family in FAMILIES:
            checks[f"{prefix}_{arm_name}_{family}_queue_conservation"]=family_conservation(
              audit,family,enq,drain,batch)
            producer_metric=f"deferred_queue_enqueued:{family}"
            produced=sum(int(count) for idx,metric_name,count in audit["per_rule"]
                         if int(idx)==writer_idx and metric_name==producer_metric)
            checks[f"{prefix}_{arm_name}_{family}_producer_rule_attribution"]=produced==enq
          checks[f"{prefix}_{arm_name}_pass_and_enumeration_counters_present"]=(
            "epochs" in audit["global"] and "rule_enumerations" in audit["global"])
        all_signatures.append(json.dumps({"full":full["state"],"fallback":fallback["state"]},sort_keys=True))
    checks["semantic_results_repeat_by_size_and_arm"]=all(
      len({json.dumps(by[n,rep,arm]["state"],sort_keys=True) for rep in range(2)})==1
      for n in (1,2,4) for arm in ("full","scoped_fallback"))
    checks["same_rep_full_fallback_oracle_all_sizes"]=all(
      by[n,rep,"full"]["state"]==by[n,rep,"scoped_fallback"]["state"]
      for n in (1,2,4) for rep in range(2))
    payload={"schema_version":1,"raw_capture_sha256":sha(RAW),
      "analysis_script_sha256":sha(Path(__file__).resolve()),
      "checks":checks,
      "all_checks_pass":all(checks.values()),
      "summary":{"workers":len(runs),"checks_passed":sum(checks.values()),"checks_total":len(checks),
        "families":list(FAMILIES),
        "claim_boundary":"One authored workload queues three deferred-effect families. Family counters conserve those records and attribute enqueues to the producer RuleIdx in this fixture. Drain timing includes audit overhead and this does not measure all scheduler/host work or establish a safe partition."}}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT),"all_checks_pass":payload["all_checks_pass"],
      "checks_passed":sum(checks.values()),"checks_total":len(checks)},indent=2))
    if not payload["all_checks_pass"]: raise SystemExit(1)

if __name__=="__main__": main()
