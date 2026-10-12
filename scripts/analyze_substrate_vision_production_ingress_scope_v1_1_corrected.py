#!/usr/bin/env python3
"""Independent integrity and capability readout for visual ingress pilot v1."""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/vision_production_ingress_scope_v1_1_20260929_raw.json"
OUT = ROOT / "evaluation/reports/vision_production_ingress_scope_v1_1_corrected_analysis_20260929.json"
LOCK = ROOT / "evaluation/substrate_capability/vision_production_ingress_scope_v1_1_20260929_lock.json"
SEEDS = (20260935, 20260936, 20260937)
ANGLES = (0, 45, 90, 135)
SCOPES = ("global", "root_scoped")
FIELDS = ("act", "act_next", "rate")
CHECKPOINT_DIR = ROOT / "evaluation/reports/vision_multiseed_checkpoints_v2_0"

def max_diff(a, b):
    if len(a) != len(b): return float("inf")
    return max((abs(float(x)-float(y)) for x,y in zip(a,b)), default=0.0)

def canonical_graph(value):
    if isinstance(value, dict): return {k: canonical_graph(v) for k,v in value.items()}
    if isinstance(value, list): return [canonical_graph(v) for v in value]
    if isinstance(value, float): return round(value, 12)
    return value

def graph_digest(value):
    payload=json.dumps(canonical_graph(value),sort_keys=True,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()

def main():
    data = json.loads(RAW.read_text()); locked = json.loads(LOCK.read_text())["locked_inputs"]
    rows = data["workers"]
    checkpoints={str(s):json.loads((CHECKPOINT_DIR/f"seed_{s}.json").read_text()) for s in SEEDS}
    expected = 3 * 5 * 2 + 2
    keys = [(r["seed"], r["condition"], r["scope"], r["omission"]) for r in rows]
    checks = {
        "complete_worker_matrix": len(rows) == expected and len(set(keys)) == expected and data.get("expected_workers") == expected,
        "run_lock_matches": data.get("locked_inputs") == locked,
        "source_stable": data.get("source_stable") is True and all(r.get("source_stable") for r in rows),
        "checkpoint_identity": all(
            hashlib.sha256((CHECKPOINT_DIR/f"seed_{r['seed']}.json").read_bytes()).hexdigest()==locked["checkpoints"][str(r["seed"])]
            and r.get("checkpoint_sha256")==checkpoints[str(r["seed"])]["prepared_graph_sha256"]
            and graph_digest(checkpoints[str(r["seed"])]["graph"])==r.get("checkpoint_sha256")
            for r in rows),
        "matched_unit_counts": all(r["target_unit_count"] == 16 and r["sibling_unit_count"] == 16 for r in rows),
        "phase_schedule_complete": all(len(r["phases"]) == 4 and [p["phase_index"] for p in r["phases"]] == [0,1,2,3] for r in rows),
        "pixel_ingress_exact": all(c["lum_raw_mismatches"] == 0 for r in rows for p in r["phases"] for c in p["calls"]),
        "rate_phase_fields_present": all(all(len(c["state"][k]) == r["target_unit_count"] if c["label"] == "target" else len(c["state"][k]) == r["sibling_unit_count"] for k in ("act", "theta", "rate", "act_step", "rate_step")) for r in rows for p in r["phases"] for c in p["calls"]),
        "omission_membership_visible": all(r["omission"] and r["target_member_count"] == 15 and r["target_unit_count"] == 16 for r in rows if r["omission"]),
        "all_calls_measured": all(c["wall_ns"] > 0 and c["process_cpu_ns"] >= 0 for r in rows for p in r["phases"] for c in p["calls"]),
    }
    indexed={(r["seed"],r["condition"],r["scope"],r["omission"]):r for r in rows}
    sibling_deltas=[]
    for seed in SEEDS:
        for scope in SCOPES:
            blank=indexed[(seed,"blank",scope,False)]
            for angle in ANGLES:
                row=indexed[(seed,f"orientation_{angle}",scope,False)]
                for phase_i,(a,b) in enumerate(zip(row["phases"],blank["phases"])):
                    sibling_delta=max(max_diff(a["calls"][1]["state"][field],b["calls"][1]["state"][field]) for field in FIELDS)
                    sibling_deltas.append({"seed":seed,"scope":scope,"angle":angle,"phase_index":phase_i,"max_abs_sibling_delta":sibling_delta})
    scoped_max=max((x["max_abs_sibling_delta"] for x in sibling_deltas if x["scope"]=="root_scoped"),default=0.0)
    checks["root_scoped_sibling_invariance"] = scoped_max <= 1e-9
    global_deltas=[x["max_abs_sibling_delta"] for x in sibling_deltas if x["scope"]=="global"]
    omission_diagnostics=[]
    for row in rows:
        if not row["omission"]: continue
        ref=indexed[(row["seed"],row["condition"],row["scope"],False)]
        orphan=f"#{row['omitted_unit']}"
        unit_ids=row["topology"]["unit_ids"][0]
        idx=unit_ids.index(orphan)
        phase_deltas=[]
        for p,q in zip(row["phases"],ref["phases"]):
            phase_deltas.append(abs(p["calls"][0]["state"]["act_next"][idx]-q["calls"][0]["state"]["act_next"][idx]))
        omission_diagnostics.append({"scope":row["scope"],"orphan_unit_index":idx,"act_next_delta_by_phase":phase_deltas,
                                    "orphan_act_next_by_phase":[p["calls"][0]["state"]["act_next"][idx] for p in row["phases"]]})
    checks["owner_omission_changes_projection"] = len(omission_diagnostics)==2 and all(any(v>1e-9 for v in d["act_next_delta_by_phase"]) for d in omission_diagnostics)
    rate_residuals=[]; aligned_rate_count=0
    for row in rows:
        for phase in row["phases"]:
            for call in phase["calls"]:
                state=call["state"]
                for act,theta,rate,act_step,rate_step in zip(state["act"],state["theta"],state["rate"],state["act_step"],state["rate_step"]):
                    if act_step==rate_step:
                        aligned_rate_count+=1
                        rate_residuals.append(abs(rate-max(act-theta,0.0)))
    scores={}; predictions={}
    for seed in SEEDS:
        for scope in SCOPES:
            by_angle={}
            for angle in ANGLES:
                row=indexed[(seed,f"orientation_{angle}",scope,False)]
                phase_sums=[sum(call["state"]["rate"]) for phase in row["phases"] for call in phase["calls"][:1]]
                by_angle[angle]=sum(phase_sums)/len(phase_sums)
            predicted=max(ANGLES,key=lambda a:by_angle[a])
            scores[f"{seed}:{scope}"]={"mean_phase_rate_sum_by_orientation":{str(k):v for k,v in by_angle.items()},"predicted_orientation_deg":predicted}
            predictions[f"{seed}:{scope}"]=predicted
    # Each seed/scope produces one four-way prediction; report prediction coverage and
    # whether each orientation ever wins, avoiding pseudo-replication across phases.
    accuracy_by_scope={}
    for scope in SCOPES:
        accuracy_by_scope[scope]={"predictions":{str(s):predictions[f"{s}:{scope}"] for s in SEEDS},
                                  "orientation_wins":{str(a):sum(predictions[f"{s}:{scope}"]==a for s in SEEDS) for a in ANGLES}}
    out={"run_id":data["run_id"],"checks":checks,"passed_checks":sum(checks.values()),"total_checks":len(checks),
         "pass":all(checks.values()),"worker_count":len(rows),"sibling_deltas":sibling_deltas,
         "root_scoped_max_abs_sibling_delta":scoped_max,
         "global_sibling_max_abs_delta":max(global_deltas,default=0.0),
         "global_sibling_nonzero_comparisons":sum(x>1e-9 for x in global_deltas),
         "owner_omission_diagnostics":omission_diagnostics,
         "rate_equation_posthoc_diagnostic":{"samples_with_equal_act_rate_step":aligned_rate_count,
             "max_abs_residual":max(rate_residuals,default=0.0),"mismatches_over_1e_9":sum(x>1e-9 for x in rate_residuals),
             "interpretation":"Final snapshots only; equal update stamps do not establish same-internal-phase observation. This is diagnostic, not an equation-pass claim."},
         "orientation_response_scores":scores,
         "orientation_decoder_summary":accuracy_by_scope,
         "timing_summary":{scope:{"worker_wall_median_s":sorted(r["worker_wall_ns"]/1e9 for r in rows if r["scope"]==scope and not r["omission"])[len([r for r in rows if r["scope"]==scope and not r["omission"]])//2],
                                "peak_rss_max_bytes":max(r["peak_rss_bytes"] for r in rows if r["scope"]==scope and not r["omission"])} for scope in SCOPES},
         "claim_boundary":"Production WaveWorld frame ingestion, four iterative phase inputs, and paired two-sheet settlement measured on three adapted checkpoints. Roots are supplied, stimuli are synthetic gratings, and the schedule is sequential. Orientation decoding is descriptive and has only three checkpoint-level predictions per scope."}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"passed_checks":out["passed_checks"],"total_checks":out["total_checks"],"orientation_decoder_summary":accuracy_by_scope,"root_scoped_max_abs_sibling_delta":scoped_max},indent=2))
    if not out["pass"]: raise SystemExit("visual ingress integrity gate failed")

if __name__=="__main__": main()
