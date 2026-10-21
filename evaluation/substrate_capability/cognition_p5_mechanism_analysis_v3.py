#!/usr/bin/env python3
"""Registered paired analysis for P5 mechanism adapters; nulls block decisions."""
from __future__ import annotations

import json
import hashlib
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from evaluation.substrate_capability.cognition_p5_mechanism_eval_v3 import FROZEN, ITEM_ARMS, N_CONTROL, _hashes


def _mcnemar(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if isinstance(x, bool) and isinstance(y, bool)]
    on_only = sum(x and not y for x, y in pairs)
    off_only = sum(not x and y for x, y in pairs)
    n = on_only + off_only
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(on_only, off_only) + 1)) / 2**n)
    return {"n_pairs": len(pairs), "on_only": on_only, "off_only": off_only, "p": p}


def _mean(values):
    vals = [float(v) for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def _wilson(successes, n):
    if n == 0:
        return None
    z = 1.959963984540054
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _paired_bootstrap(on, off, label):
    pairs = [(float(a), float(b)) for a, b in zip(on, off)
             if isinstance(a, (int, float)) and isinstance(b, (int, float))]
    if not pairs:
        return {"n_pairs": 0, "mean_difference": None, "ci95": None, "resamples": 10000}
    differences = [a - b for a, b in pairs]
    rng = random.Random(int(hashlib.sha256(label.encode()).hexdigest()[:16], 16))
    means = []
    for _ in range(10000):
        means.append(sum(differences[rng.randrange(len(differences))] for _ in differences) / len(differences))
    means.sort()
    return {"n_pairs": len(pairs), "mean_difference": sum(differences) / len(differences),
            "ci95": [means[249], means[9749]], "resamples": 10000}


def analyze(report):
    if report.get("protocol") != "cognition_p5_mechanism_eval_v3":
        raise ValueError("protocol mismatch")
    if set(report.get("artifact_sha256", {})) != set(FROZEN) or report["artifact_sha256"] != _hashes():
        raise ValueError("frozen artifact hash manifest is absent, incomplete or altered")
    if set(report.get("items", {})) != set(ITEM_ARMS):
        raise ValueError("one or more registered families are missing")
    items = {}
    overall = "PASS"
    superiority_p = {}
    for item, arms in ITEM_ARMS.items():
        payload = report["items"][item]
        rows, controls = payload["primary"], payload["controls"]
        nulls = sum(result is None for row in rows + controls for result in row["arms"].values())
        arm_errors = [f"{row['case_id']}:{arm}" for row in rows + controls
                      for arm in arms if not isinstance(row.get("arms", {}).get(arm), dict)]
        arm_errors.extend(f"{row['case_id']}:{arm}:{message}" for row in rows + controls
                          for arm, message in row.get("arm_errors", {}).items())
        if item == "F1":
            on = [r["arms"][arms[0]] for r in rows]
            metrics = {"exact_conformance": _mean([x["conformance"] for x in on]),
                       "exact_conformance_wilson95": _wilson(sum(bool(x["conformance"]) for x in on), len(on)),
                       "control_conformance": _mean([r["arms"][arms[0]]["conformance"] for r in controls]),
                       "source_loss": sum(not x["source_unchanged"] for x in on),
                       "belief_truth_leaks": sum(x["belief_truth_leak"] for x in on)}
            passed = (metrics["exact_conformance"] is not None and metrics["exact_conformance"] >= .95
                      and metrics["control_conformance"] == 1.0 and not metrics["source_loss"]
                      and not metrics["belief_truth_leaks"])
        elif item == "F2":
            expected = [r["scoring_oracle"]["query_status"] for r in rows]
            on = [r["arms"][arms[0]] for r in rows]; off = [r["arms"][arms[1]] for r in rows]
            on_ok = [x["answer"] == y and x["actual_world_unchanged"] for x, y in zip(on, expected)]
            off_ok = [x["answer"] == y for x, y in zip(off, expected)]
            delta = _mean(on_ok) - _mean(off_ok)
            stats = _mcnemar(on_ok, off_ok)
            metrics = {"on_accuracy": _mean(on_ok), "off_accuracy": _mean(off_ok), "gain": delta,
                       "on_accuracy_wilson95": _wilson(sum(on_ok), len(on_ok)),
                       "off_accuracy_wilson95": _wilson(sum(off_ok), len(off_ok)),
                       "paired_gain_bootstrap95": _paired_bootstrap(on_ok, off_ok, report["prereg_hash"] + item),
                       "mcnemar": stats, "actual_world_overwrites": sum(not x["actual_world_unchanged"] for x in on),
                       "inaccessible_control_unknown": sum(r["arms"][arms[0]]["answer"] == "unknown" for r in controls),
                       "inaccessible_control_n": len(controls),
                       "control_actual_world_overwrites": sum(not r["arms"][arms[0]]["actual_world_unchanged"] for r in controls)}
            passed = (metrics["on_accuracy"] is not None and metrics["on_accuracy"] >= .8 and delta >= .2
                      and metrics["actual_world_overwrites"] == 0
                      and metrics["inaccessible_control_unknown"] == len(controls)
                      and metrics["control_actual_world_overwrites"] == 0)
            superiority_p[item] = stats["p"]
        elif item == "G2":
            supported = [bool(r["agent_input"]["supported"]) for r in rows]
            on = [r["arms"][arms[0]] for r in rows]; off = [r["arms"][arms[1]] for r in rows]
            on_ok = [x["view_count"] > 0 and not x["unsupported_accepted"] for x, s in zip(on, supported) if s]
            off_ok = [x["view_count"] > 0 for x, s in zip(off, supported) if s]
            gain = ((_mean(on_ok) - _mean(off_ok))
                    if _mean(on_ok) is not None and _mean(off_ok) is not None else None)
            stats = _mcnemar(on_ok, off_ok)
            unsafe = sum(x["unsupported_accepted"] or not x["source_unchanged"] for x in on + off)
            metrics = {"supported_on_rate": _mean(on_ok), "supported_off_rate": _mean(off_ok),
                       "on_rate_wilson95": _wilson(sum(on_ok), len(on_ok)),
                       "off_rate_wilson95": _wilson(sum(off_ok), len(off_ok)),
                       "gain": gain, "paired_gain_bootstrap95": _paired_bootstrap(on_ok, off_ok, report["prereg_hash"] + item),
                       "mcnemar": stats, "unsupported_or_source_violations": unsafe}
            passed = gain is not None and gain >= .2 and unsafe == 0
            superiority_p[item] = stats["p"]
        elif item == "G3":
            stop_rows = [r for r in rows + controls if r["agent_input"]["schedule"] == "stop_before"]
            go_rows = [r for r in rows + controls if r["agent_input"]["schedule"] == "go"]
            on_stop = sum(r["arms"][arms[0]]["status"] == "withheld" and r["arms"][arms[0]]["emissions"] == 0 for r in stop_rows)
            on_go = sum(r["arms"][arms[0]]["status"] == "emitted" and r["arms"][arms[0]]["emissions"] == 1 for r in go_rows)
            duplicate = sum(r["arms"][arms[0]]["emissions"] > 1 for r in rows + controls)
            late = sum(r["arms"][arms[0]]["late_stop_status"] not in (None, "already_emitted") for r in rows + controls)
            metrics = {"timely_stop_withheld": on_stop, "timely_stop_n": len(stop_rows),
                       "timely_stop_wilson95": _wilson(on_stop, len(stop_rows)),
                       "valid_go_emitted": on_go, "valid_go_n": len(go_rows),
                       "valid_go_wilson95": _wilson(on_go, len(go_rows)),
                       "duplicate_emissions": duplicate, "late_stop_anomalies": late}
            passed = len(stop_rows) > 0 and on_stop == len(stop_rows) and len(go_rows) > 0 and on_go / len(go_rows) >= .95 and duplicate == 0 and late == 0
        elif item == "E3":
            identified = [r for r in rows + controls if r["agent_input"]["model_kind"] != "nonidentified"]
            unsupported = [r for r in rows + controls if r["agent_input"]["model_kind"] == "nonidentified"]
            correct = sum(r["arms"][arms[0]]["status"] == "identified"
                          and r["arms"][arms[0]]["values"] == r["scoring_oracle"]["effect_values"]
                          and r["arms"][arms[0]]["live_model_unchanged"] for r in identified)
            abstained = sum(r["arms"][arms[0]]["status"] == "unknown" for r in unsupported)
            leaks = sum(r["arms"][arms[0]]["truth_entered_graph"] or not r["arms"][arms[0]]["live_model_unchanged"] for r in rows + controls)
            metrics = {"identified_correct": correct, "identified_n": len(identified),
                       "identified_agreement_wilson95": _wilson(correct, len(identified)),
                       "unsupported_unknown": abstained, "unsupported_n": len(unsupported), "truth_leaks": leaks}
            passed = len(identified) > 0 and correct / len(identified) >= .95 and abstained == len(unsupported) and leaks == 0
        elif item == "E4":
            on = [r["arms"][arms[0]]["observed_success"] for r in rows]
            off = [r["arms"][arms[1]]["observed_success"] for r in rows]
            gain = _mean(on) - _mean(off); stats = _mcnemar(on, off)
            bounds = sum(r["arms"][arms[0]]["expanded"] > 256 for r in rows)
            metrics = {"planner_observed_success": _mean(on), "one_step_observed_success": _mean(off),
                       "planner_success_wilson95": _wilson(sum(on), len(on)),
                       "one_step_success_wilson95": _wilson(sum(off), len(off)),
                       "gain": gain, "mcnemar": stats, "bound_violations": bounds,
                       "paired_gain_bootstrap95": _paired_bootstrap(on, off, report["prereg_hash"] + item),
                       "expansion_count_distribution": {"min": min(r["arms"][arms[0]]["expanded"] for r in rows),
                           "median": sorted(r["arms"][arms[0]]["expanded"] for r in rows)[len(rows)//2],
                           "max": max(r["arms"][arms[0]]["expanded"] for r in rows)},
                       "planner_minus_one_step_expansions_bootstrap95": _paired_bootstrap(
                           [r["arms"][arms[0]]["expanded"] for r in rows],
                           [r["arms"][arms[1]]["expanded"] for r in rows], report["prereg_hash"] + item + "-work"),
                       "predicted_success": _mean([r["arms"][arms[0]]["predicted_reachable"] for r in rows])}
            metrics["missing_edge_control_false_positives"] = sum(
                r["arms"][arms[0]]["predicted_reachable"] or r["arms"][arms[0]]["observed_success"]
                for r in controls)
            metrics["missing_edge_control_n"] = len(controls)
            passed = gain is not None and gain >= .2 and bounds == 0 and metrics["missing_edge_control_false_positives"] == 0
            superiority_p[item] = stats["p"]
        elif item == "A2":
            on = [r["arms"][arms[0]] for r in rows + controls]
            correct = sum(x["witness"] == x["expected_complete"] and x["resolved"] == x["expected_complete"] for x in on)
            premature = sum(x["premature_settlement"] for x in on)
            metrics = {"valid_decisions": correct, "decision_n": len(on), "premature_settlements": premature}
            metrics["decision_agreement_wilson95"] = _wilson(correct, len(on))
            passed = correct == len(on) and premature == 0
        else:
            on = [r["arms"][arms[0]] for r in rows]
            control_on = [r["arms"][arms[0]] for r in controls]
            exact = sum(x["exact"] and x["shape_verified"] and x["status"] == "proposed" for x in on)
            control_rejected = sum(x["control_rejected"] and x["status"] == "unresolved"
                                   and not x["grounded"] for x in control_on)
            work = [x["work"] for x in on]
            grounded = sum(x["grounded"] for x in on + control_on)
            shortest = [min(r["agent_input"]["angle"] // 90, 4 - r["agent_input"]["angle"] // 90)
                        for r in rows]
            metrics = {"exact_verified": exact, "n": len(on), "exact_verified_wilson95": _wilson(exact, len(on)),
                       "control_receipt_rejections": control_rejected, "control_n": len(control_on),
                       "grounded_buffers": grounded,
                       "actual_transform_work": {"total": sum(work), "mean": _mean(work)}}
            metrics["shortest_angle_work"] = {"total": sum(shortest), "mean": _mean(shortest)}
            metrics["work_difference_bootstrap95"] = _paired_bootstrap(
                work, shortest, report["prereg_hash"] + item + "-transform-work")
            passed = (len(on) > 0 and exact / len(on) >= .95
                      and control_rejected == len(control_on) and grounded == 0)
        coverage = len(rows) == report["end"] - report["first"] and len(controls) == N_CONTROL
        decision = "NOT_ESTABLISHED" if nulls or arm_errors or not coverage else ("PASS" if passed else "FAIL")
        if decision == "NOT_ESTABLISHED":
            overall = "NOT_ESTABLISHED"
        elif decision == "FAIL" and overall == "PASS":
            overall = "FAIL"
        items[item] = {"decision": decision, "coverage": {"primary": len(rows), "controls": len(controls), "complete": coverage},
                       "null_arm_results": nulls, "arm_errors": arm_errors, "metrics": metrics,
                       "criteria_passed": bool(passed), "claim_boundary": "registered mechanism fixtures only"}
    ordered = sorted(superiority_p.items(), key=lambda pair: pair[1])
    running_max = 0.0
    for rank, (item, p_value) in enumerate(ordered):
        adjusted = min(1.0, (len(ordered) - rank) * p_value)
        running_max = max(running_max, adjusted)
        entry = items[item]
        entry["metrics"]["holm_adjusted_p"] = running_max
        if running_max >= .01 and entry["decision"] == "PASS":
            entry["decision"] = "FAIL"
            entry["criteria_passed"] = False
            if overall == "PASS":
                overall = "FAIL"
    return {"protocol": "cognition_p5_mechanism_analysis_v3", "prereg_hash": report["prereg_hash"],
            "overall_decision": overall, "items": items}


def _self_check():
    from evaluation.substrate_capability.cognition_p5_mechanism_eval_v3 import run
    sample = run("analysis-self-check-v3", 21000, 21001, development=True)
    result = analyze(sample)
    assert set(result["items"]) == set(ITEM_ARMS)
    assert result["overall_decision"] in {"PASS", "FAIL", "NOT_ESTABLISHED"}
    bad = dict(sample); bad["artifact_sha256"] = {}
    try:
        analyze(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("analysis accepted missing artifact hashes")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--self-check"]:
        _self_check(); print("cognition_p5_mechanism_analysis_v3 self-check passed"); return
    if len(args) != 1:
        raise SystemExit("usage: cognition_p5_mechanism_analysis_v3.py <report.json> | --self-check")
    report = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    analyzed = analyze(report)
    out = Path(args[0]).with_name(Path(args[0]).stem + "_analysis.json")
    out.write_text(json.dumps(analyzed, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
