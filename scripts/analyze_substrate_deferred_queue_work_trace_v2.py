#!/usr/bin/env python3
"""Independent conservation, semantic, and operation-work analysis."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_deferred_queue_work_trace_v2_20261001.json"
OUT=ROOT/"evaluation/reports/substrate_deferred_queue_work_trace_v2_analysis_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/deferred_queue_work_trace_v2_lock_20261001.json"
FAMILIES=("rule_patches","track_identity","net_collapses")
FAMILY_CODES={"rule_patches":2,"track_identity":4,"net_collapses":5}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def metric(audit, name): return int(audit.get("global",{}).get(name,0))

def family_conservation(audit, family, enqueued, drained, batches):
    return (metric(audit,f"deferred_queue:{family}:enqueued_items")==enqueued
            and metric(audit,f"deferred_queue:{family}:drained_items")==drained
            and metric(audit,f"deferred_queue:{family}:drain_batches")==batches
            and metric(audit,f"deferred_queue:{family}:drain_ns")>=0)

def work_trace_checks(row,phase):
    trace=row.get("runtime_work_traces",{}).get(phase,{})
    rows=trace.get("rows",[]);counts={};operations={};valid=True
    for item in rows:
        scope=int(item["scope"]);op=int(item["operation_id"]);uid=int(item["producer_rule_uid"])
        kind=str(item["kind"]);subject=item.get("subject");units=int(item["units"])
        valid &= scope>0 and op>0 and uid>=0 and units>0
        operations.setdefault((scope,op),[]).append(item)
        counts[(kind,subject)]=counts.get((kind,subject),0)+units
    operation_kind_codes={1,2,3};markers_ok=True
    for group in operations.values():
        markers=[x for x in group if x["kind"]=="operation_kind"]
        markers_ok &= len(markers)==1 and int(markers[0]["units"])==1 and int(markers[0]["subject"]) in operation_kind_codes
    operation_ok=len(operations)>0 and markers_ok
    audit=row["audits"][phase];matches=True;queue_work={}
    for family in FAMILIES:
        code=FAMILY_CODES[family]
        expected={"deferred_queue_enqueue_items":metric(audit,f"deferred_queue:{family}:enqueued_items"),
                  "deferred_queue_drained_items":metric(audit,f"deferred_queue:{family}:drained_items"),
                  "deferred_queue_drain_batches":metric(audit,f"deferred_queue:{family}:drain_batches")}
        observed={kind:counts.get((kind,code),0) for kind in expected}
        matches &= observed==expected
        queue_work[family]={"expected_from_scale_audit":expected,"observed_in_operation_trace":observed,"reconciles":observed==expected}
    return {"dropped_zero":int(trace.get("dropped",-1))==0,"row_values_valid":bool(valid),
            "operation_markers_valid":bool(operation_ok),"queue_rows_reconcile":bool(matches),
            "rows":len(rows),"operations":len(operations),"queue_work_by_family":queue_work}

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
      "captured_work_trace_analyzer_sha256_matches":raw["locked_inputs"]["analyzer"]==sha(Path(__file__).resolve()),
    }
    by={(r["count"],r["replicate"],r["arm"]):r for r in runs}
    work_trace_reports={}
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
          wt=work_trace_checks(row,phase)
          work_trace_reports[f"{prefix}_{arm_name}"]=wt
          for gate,value in wt.items():
            if gate in {"dropped_zero","row_values_valid","operation_markers_valid","queue_rows_reconcile"}:
              checks[f"{prefix}_{arm_name}_operation_work_{gate}"]=bool(value)
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
      "operation_work_trace_reconciliation":work_trace_reports,
      "all_checks_pass":all(checks.values()),
      "summary":{"workers":len(runs),"checks_passed":sum(checks.values()),"checks_total":len(checks),
        "families":list(FAMILIES),
        "claim_boundary":"One authored workload queues three deferred-effect families. Operation-work event units reconcile with independent family counters in full, scoped-only, and fallback phases. Enqueues are attributed by RuleIdx in separate scale-audit counters; drain rows have no producer identity. This is not complete CPU work, natural-task prevalence, or safe partition evidence."}}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT),"all_checks_pass":payload["all_checks_pass"],
      "checks_passed":sum(checks.values()),"checks_total":len(checks)},indent=2))
    if not payload["all_checks_pass"]: raise SystemExit(1)

if __name__=="__main__": main()
