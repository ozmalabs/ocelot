#!/usr/bin/env python3
"""Registered P4 report analysis; nulls and incomplete draws stay visible."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


FAMILIES = ("graph_role", "numeric_sequence")
ARMS = ("recall_on", "recall_off", "mismatched_source")
REGISTERED_END = 200
REGISTERED_DECOYS = 100


def _scored_solved(row: dict, arm: str, outcome: dict):
    if "selected_candidate" not in outcome:
        return outcome.get("solved")
    target_key = (row.get("scoring_oracle") or {}).get("target_candidate_key")
    return (outcome.get("selected_candidate") is not None and target_key is not None
            and outcome.get("selected_candidate") == target_key
            and arm != "mismatched_source")


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> dict:
    if n <= 0:
        return {"rate": None, "lower": None, "upper": None, "n": 0,
                "successes": int(successes)}
    p = successes / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"rate": p, "lower": max(0.0, centre - half),
            "upper": min(1.0, centre + half), "n": n,
            "successes": int(successes)}


def _classify_family(rows: list[dict], family: str) -> dict:
    selected = [row for row in rows if row.get("family") == family]
    targets = [row for row in selected if row.get("case_kind") == "target"]
    decoys = [row for row in selected if row.get("case_kind") == "incompatible_decoy"]
    required_targets = REGISTERED_END
    required_decoys = REGISTERED_DECOYS
    coverage_ok = len(targets) == required_targets and len(decoys) == required_decoys

    nulls = 0
    timeouts = 0
    invalid = []
    false_grounded = {"incompatible_decoy": 0, "mismatched_source": 0,
                      "wrong_target_selection": 0}
    solve_rates = {}
    for arm in ARMS:
        solved, n = 0, 0
        for row in selected:
            outcome = (row.get("arms") or {}).get(arm)
            if outcome is None:
                nulls += 1
                continue
            if outcome.get("timeout"):
                timeouts += 1
                # The protocol counts timeout as an unsolved failure.
            selected_candidate = outcome.get("selected_candidate")
            oracle = row.get("scoring_oracle") or {}
            if "selected_candidate" in outcome:
                target_key = oracle.get("target_candidate_key")
                value = _scored_solved(row, arm, outcome)
                false_grounded_result = (selected_candidate is not None and (
                    row.get("case_kind") == "incompatible_decoy"
                    or arm == "mismatched_source"
                    or target_key is None or selected_candidate != target_key))
            else:
                value = outcome.get("solved")
                false_grounded_result = bool(outcome.get("false_grounded"))
            if value is None:
                nulls += 1
                continue
            if not isinstance(value, bool):
                invalid.append({"paired_id": row.get("paired_id"), "arm": arm,
                                "problem": "solved must be boolean or null"})
                continue
            if row.get("case_kind") == "target":
                solved += int(value)
                n += 1
            if false_grounded_result:
                if row.get("case_kind") == "incompatible_decoy":
                    false_grounded["incompatible_decoy"] += 1
                if arm == "mismatched_source":
                    false_grounded["mismatched_source"] += 1
                if row.get("case_kind") == "target" and target_key is not None \
                        and selected_candidate is not None and selected_candidate != target_key:
                    false_grounded["wrong_target_selection"] += 1
            digest = outcome.get("target_digest")
            paired_digests = {value.get("target_digest")
                              for value in (row.get("arms") or {}).values()
                              if isinstance(value, dict)}
            if digest is None or len(paired_digests) != 1:
                invalid.append({"paired_id": row.get("paired_id"), "arm": arm,
                                "problem": "paired arms must carry one shared target_digest"})
            checks = outcome.get("exact_candidate_checks")
            if checks is not None and (not isinstance(checks, int) or checks < 0):
                invalid.append({"paired_id": row.get("paired_id"), "arm": arm,
                                "problem": "exact_candidate_checks must be a non-negative integer"})
        solve_rates[arm] = wilson(solved, n)

    savings_pairs = []
    for row in targets:
        arms = row.get("arms") or {}
        on_result, off_result = arms.get("recall_on"), arms.get("recall_off")
        if not on_result or not off_result:
            continue
        if (_scored_solved(row, "recall_on", on_result) is True
                and _scored_solved(row, "recall_off", off_result) is True):
            a, b = on_result.get("exact_candidate_checks"), off_result.get("exact_candidate_checks")
            if isinstance(a, int) and isinstance(b, int) and b > 0:
                savings_pairs.append((a, b))
    candidate_savings = (sum(b - a for a, b in savings_pairs) / sum(b for _, b in savings_pairs)
                         if savings_pairs and sum(b for _, b in savings_pairs) > 0 else None)
    on_rate, off_rate = solve_rates["recall_on"]["rate"], solve_rates["recall_off"]["rate"]
    solve_loss = (off_rate - on_rate) if on_rate is not None and off_rate is not None else None

    hard_violation = bool(invalid or any(false_grounded.values()))
    established = coverage_ok and nulls == 0 and not invalid
    decision = "NOT_ESTABLISHED"
    if hard_violation:
        decision = "FAIL"
    elif established:
        decision = "PASS" if (not hard_violation and candidate_savings is not None
                               and candidate_savings >= 0.25 and solve_loss is not None
                               and solve_loss <= 0.02) else "FAIL"
    return {
        "decision": decision, "coverage": {"targets": len(targets),
            "required_targets": required_targets, "decoys": len(decoys),
            "required_decoys": required_decoys, "complete": coverage_ok},
        "null_results": nulls, "timeouts": timeouts, "invalid_results": invalid,
        "solve_rate": solve_rates, "solve_loss_off_minus_on": solve_loss,
        "successful_paired_targets": len(savings_pairs),
        "candidate_check_savings": candidate_savings,
        "false_grounded": false_grounded,
        "criteria": {"candidate_savings_ge_25_percent": candidate_savings is not None
                      and candidate_savings >= 0.25,
                      "solve_loss_le_2pp": solve_loss is not None and solve_loss <= 0.02,
                      "zero_false_grounded_decoys": false_grounded["incompatible_decoy"] == 0,
                      "zero_mismatched_source_acceptance": false_grounded["mismatched_source"] == 0},
    }


def _exact_mcnemar(on: list[bool], off: list[bool]) -> dict:
    b = sum(a and not c for a, c in zip(on, off))
    c = sum(not a and d for a, d in zip(on, off))
    n = b + c
    if n == 0:
        p = 1.0
    else:
        tail = sum(math.comb(n, k) for k in range(min(b, c) + 1)) / (2 ** n)
        p = min(1.0, 2.0 * tail)
    return {"on_only": b, "off_only": c, "discordant": n, "p_two_sided": p}


def _analyze_c5(payload) -> dict:
    if not isinstance(payload, dict):
        return {"decision": "NOT_ESTABLISHED",
                "reason": "runner did not emit C5 hidden-residual and forced-frame rows"}
    episodes = payload.get("hidden_residual_episodes", [])
    controls = payload.get("forced_frame_controls", [])
    on_values, off_values = [], []
    nulls = timeouts = unfunded_on = unfunded_off = forced_changes = 0
    for row in episodes:
        on, off = row.get("adapter_on"), row.get("adapter_off")
        for label, result, values in (("on", on, on_values), ("off", off, off_values)):
            if not isinstance(result, dict) or result.get("resolved_hidden_residual") is None:
                nulls += 1
                continue
            if result.get("timeout"):
                timeouts += 1
                values.append(False)
            else:
                values.append(bool(result["resolved_hidden_residual"]))
            if label == "on" and result.get("unfunded_probe"):
                unfunded_on += 1
            if label == "off" and result.get("unfunded_probe"):
                unfunded_off += 1
    for row in controls:
        for arm in ("adapter_on", "adapter_off"):
            result = row.get(arm)
            if not isinstance(result, dict):
                nulls += 1
            elif result.get("forced_frame_changed"):
                forced_changes += 1
    gain = (sum(on_values) / len(on_values) - sum(off_values) / len(off_values)
            if on_values and off_values and len(on_values) == len(off_values) else None)
    mcnemar = _exact_mcnemar(on_values, off_values) if len(on_values) == len(off_values) else None
    # Fixed Bonferroni family: the three registered inferential claims are C5,
    # E1/E2 and D1. Applying the fixed factor does not depend on which runners
    # have emitted reports yet.
    p_corrected = min(1.0, mcnemar["p_two_sided"] * 3) if mcnemar is not None else None
    complete = len(episodes) == REGISTERED_END and len(controls) == REGISTERED_DECOYS
    if unfunded_on or forced_changes:
        decision = "FAIL"
    elif not complete or nulls:
        decision = "NOT_ESTABLISHED"
    else:
        decision = "PASS" if gain is not None and gain >= 0.20 and p_corrected < 0.01 else "FAIL"
    return {"decision": decision,
            "coverage": {"hidden_residual_episodes": len(episodes),
                         "required_hidden_residual_episodes": REGISTERED_END,
                         "forced_frame_controls": len(controls),
                         "required_forced_frame_controls": REGISTERED_DECOYS,
                         "complete": complete},
            "null_results": nulls, "timeouts": timeouts,
            "resolution_rate": {"adapter_on": wilson(sum(on_values), len(on_values)),
                                "adapter_off": wilson(sum(off_values), len(off_values))},
            "absolute_gain": gain, "mcnemar": mcnemar,
            "p_corrected_bonferroni_3": p_corrected,
            "unfunded_adapter_on_probes": unfunded_on,
            "unfunded_adapter_off_probes": unfunded_off,
            "forced_frame_changes": forced_changes,
            "criteria": {"gain_ge_20pp_and_corrected_p_lt_01": gain is not None and gain >= 0.20
                         and p_corrected is not None and p_corrected < 0.01,
                         "zero_unfunded_adapter_on_probes": unfunded_on == 0,
                         "zero_forced_frame_changes": forced_changes == 0}}


def _analyze_d1(payload) -> dict:
    if not isinstance(payload, dict):
        return {"decision": "NOT_ESTABLISHED",
                "reason": "runner did not emit D1 orbit and unsupported-control rows"}
    episodes, controls = payload.get("orbit_sequences", []), payload.get("unsupported_controls", [])
    on_values, off_values = [], []
    nulls = timeouts = exact_unsupported = unfunded = bad_restore = 0
    for row in episodes:
        on, off = row.get("bridge_on"), row.get("bridge_off")
        for result, values in ((on, on_values), (off, off_values)):
            if not isinstance(result, dict) or result.get("exact_continuation") is None:
                nulls += 1
                continue
            if result.get("timeout"):
                timeouts += 1
                values.append(False)
            else:
                values.append(bool(result["exact_continuation"]))
            if result.get("bridge_count", 0) > result.get("funded_steps", 0) or (
                    result.get("funded_steps", 0) > 0 and not result.get("all_debits_epoch_2")):
                unfunded += 1
            if not result.get("time_infer_restored", False):
                bad_restore += 1
    control_kinds = {kind: 0 for kind in ("shuffled", "no_frame", "irregular")}
    for row in controls:
        kind = row.get("control_kind")
        if kind in control_kinds:
            control_kinds[kind] += 1
        for arm in ("bridge_on", "bridge_off"):
            result = row.get(arm)
            if not isinstance(result, dict):
                nulls += 1
                continue
            if result.get("unsupported_exact_claim") or result.get("exact_continuation"):
                exact_unsupported += 1
            if result.get("bridge_count", 0) > result.get("funded_steps", 0) or (
                    result.get("funded_steps", 0) > 0 and not result.get("all_debits_epoch_2")):
                unfunded += 1
            if not result.get("time_infer_restored", False):
                bad_restore += 1
    gain = (sum(on_values) / len(on_values) - sum(off_values) / len(off_values)
            if on_values and off_values and len(on_values) == len(off_values) else None)
    mcnemar = _exact_mcnemar(on_values, off_values) if len(on_values) == len(off_values) else None
    p_corrected = min(1.0, mcnemar["p_two_sided"] * 3) if mcnemar else None
    complete = (len(episodes) == REGISTERED_END and len(controls) == REGISTERED_DECOYS
                and control_kinds == {"shuffled": 34, "no_frame": 33, "irregular": 33})
    if exact_unsupported or unfunded or bad_restore:
        decision = "FAIL"
    elif not complete or nulls:
        decision = "NOT_ESTABLISHED"
    else:
        decision = "PASS" if gain is not None and gain >= 0.50 and p_corrected < 0.01 else "FAIL"
    return {"decision": decision,
            "coverage": {"orbit_sequences": len(episodes), "required_orbit_sequences": REGISTERED_END,
                         "unsupported_controls": len(controls),
                         "required_unsupported_controls": REGISTERED_DECOYS,
                         "control_kinds": control_kinds, "complete": complete},
            "null_results": nulls, "timeouts": timeouts,
            "exact_continuation_rate": {"bridge_on": wilson(sum(on_values), len(on_values)),
                                         "bridge_off": wilson(sum(off_values), len(off_values))},
            "absolute_gain": gain, "mcnemar": mcnemar,
            "p_corrected_bonferroni_3": p_corrected,
            "unsupported_exact_claims": exact_unsupported,
            "unfunded_inferences": unfunded, "unrestored_time_infer_flags": bad_restore,
            "criteria": {"gain_ge_50pp_and_corrected_p_lt_01": gain is not None
                         and gain >= 0.50 and p_corrected is not None and p_corrected < 0.01,
                         "zero_unsupported_exact_claims": exact_unsupported == 0,
                         "all_inferences_funded": unfunded == 0,
                         "all_leases_restored": bad_restore == 0}}


def _analyze_e1e2(payload) -> dict:
    if not isinstance(payload, dict):
        return {"decision": "NOT_ESTABLISHED",
                "reason": "runner did not emit E1/E2 model-world rows"}
    worlds = payload.get("model_worlds", [])
    counts = {kind: 0 for kind in ("feasible", "infeasible", "missing_model")}
    nulls = timeouts = false_escapes = parity_failures = 0
    candidate_projection_count = refinement_requests = funded_refinements = 0
    feasible_on, feasible_off = [], []
    for row in worlds:
        kind = row.get("world_kind")
        if kind in counts:
            counts[kind] += 1
        arms = row.get("arms") or {}
        on, off, parity = (arms.get("bridge_on"), arms.get("bridge_off"),
                           arms.get("supplied_path_parity"))
        if kind == "feasible":
            for value, result in ((feasible_on, on), (feasible_off, off)):
                if not isinstance(result, dict):
                    continue
                elif result.get("verified_feasible_candidate") is None:
                    nulls += 1
                elif result.get("timeout"):
                    timeouts += 1
                    value.append(False)
                else:
                    value.append(bool(result["verified_feasible_candidate"]))
        for result in (on, off):
            if result is None:
                nulls += 1
            elif isinstance(result, dict):
                false_escapes += int(bool(result.get("false_certified_escape")))
                timeouts += int(bool(result.get("timeout")) and kind != "feasible")
                invalid_receipts = result.get("invalid_feasibility_receipt_count", 0)
                if (not isinstance(invalid_receipts, int) or isinstance(invalid_receipts, bool)
                        or invalid_receipts < 0):
                    nulls += 1
                elif invalid_receipts:
                    nulls += invalid_receipts
                counters = (result.get("candidate_count"),
                            result.get("refinement_request_count"),
                            result.get("funded_refinement_count"))
                if any(not isinstance(value, int) or isinstance(value, bool) or value < 0
                       for value in counters):
                    nulls += 1
                else:
                    candidate_projection_count += counters[0]
                    refinement_requests += counters[1]
                    funded_refinements += counters[2]
        if kind != "missing_model":
            if parity is None:
                nulls += 1
            elif isinstance(parity, dict):
                equal = parity.get("projection_equal")
                if equal is False:
                    parity_failures += 1
                elif equal is None:
                    nulls += 1
    gain = (sum(feasible_on) / len(feasible_on) - sum(feasible_off) / len(feasible_off)
            if feasible_on and len(feasible_on) == len(feasible_off) else None)
    mcnemar = (_exact_mcnemar(feasible_on, feasible_off)
               if len(feasible_on) == len(feasible_off) else None)
    p_corrected = min(1.0, mcnemar["p_two_sided"] * 3) if mcnemar else None
    complete = (len(worlds) == REGISTERED_END
                and counts == {"feasible": 80, "infeasible": 60, "missing_model": 60})
    if false_escapes or parity_failures:
        decision = "FAIL"
    elif not complete or nulls:
        decision = "NOT_ESTABLISHED"
    else:
        decision = ("PASS" if gain is not None and gain >= 0.20
                    and p_corrected is not None and p_corrected < 0.01 else "FAIL")
    return {"decision": decision,
            "coverage": {"model_worlds": len(worlds), "required_model_worlds": REGISTERED_END,
                         "world_kinds": counts, "complete": complete},
            "null_results": nulls, "timeouts": timeouts,
            "false_certified_escapes": false_escapes,
            "supplied_path_parity_failures": parity_failures,
            "candidate_projection_count": candidate_projection_count,
            "refinement_requests": refinement_requests,
            "funded_refinements": funded_refinements,
            "feasible_candidate_rate": {
                "bridge_on": wilson(sum(feasible_on), len(feasible_on)),
                "bridge_off": wilson(sum(feasible_off), len(feasible_off))},
            "absolute_gain": gain, "mcnemar": mcnemar,
            "p_corrected_bonferroni_3": p_corrected}


def analyze(report: dict) -> dict:
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("report.rows must be a list")
    by_family = {family: _classify_family(rows, family) for family in FAMILIES}
    measured_d2d3 = report.get("d2_d3")
    if isinstance(measured_d2d3, dict):
        streams = measured_d2d3.get("parity_streams", [])
        controls = measured_d2d3.get("collision_controls", [])
        summary = measured_d2d3.get("summary", {})
        d2d3_timeouts = sum(bool(row.get("timeout")) for row in streams)
        d2d3_complete = (len(streams) == REGISTERED_END
                         and len(controls) == REGISTERED_DECOYS
                         and summary.get("parity_n") == REGISTERED_END
                         and summary.get("collision_n") == REGISTERED_DECOYS)
        d2d3_pass = (d2d3_complete
                     and summary.get("parity_passes") == REGISTERED_END
                     and summary.get("collision_passes") == REGISTERED_DECOYS
                     and summary.get("epochs_auditable") is True
                     and d2d3_timeouts == 0)
        d2d3 = {"decision": "PASS" if d2d3_pass else
                "FAIL" if d2d3_complete else "NOT_ESTABLISHED",
                "coverage": {"parity_streams": len(streams),
                             "required_parity_streams": REGISTERED_END,
                             "collision_controls": len(controls),
                             "required_collision_controls": REGISTERED_DECOYS},
                "timeouts": d2d3_timeouts,
                "summary": summary}
    else:
        d2d3 = {"decision": "NOT_ESTABLISHED",
                "reason": "runner did not emit D2/D3 parity and collision-control evidence"}
    c5 = _analyze_c5(report.get("c5"))
    d1 = _analyze_d1(report.get("d1"))
    e1e2 = _analyze_e1e2(report.get("e1_e2"))
    other = {}
    return {"protocol": "cognition_p4_heldout_v1",
            "prereg_hash": report.get("prereg_hash"),
            "draw_range": [report.get("first"), report.get("end")],
            "d5_transfer": by_family,
            "d2_d3": d2d3,
            "c5": c5,
            "d1": d1,
            "e1_e2": e1e2,
            "overall_d5": ("PASS" if all(x["decision"] == "PASS" for x in by_family.values())
                           else "FAIL" if any(x["decision"] == "FAIL" for x in by_family.values())
                           else "NOT_ESTABLISHED"),
            "other_registered_families": {name: {"decision": "NOT_ESTABLISHED",
                "reason": reason} for name, reason in other.items()},
            "limits": ["analysis does not create or infer missing agent outcomes",
                       "timeouts count as unsolved; nulls prevent an established decision",
                       "runner and registered report are prerequisites for phase-level claims"]}


def _self_check() -> None:
    empty = analyze({"rows": [], "prereg_hash": "development", "first": 1000, "end": 1000})
    assert empty["overall_d5"] == "NOT_ESTABLISHED"
    assert all(x["decision"] == "NOT_ESTABLISHED" for x in empty["d5_transfer"].values())
    assert empty["c5"]["decision"] == "NOT_ESTABLISHED"
    assert empty["d1"]["decision"] == "NOT_ESTABLISHED"
    assert empty["e1_e2"]["decision"] == "NOT_ESTABLISHED"
    d2_timeout = analyze({"rows": [], "d2_d3": {
        "parity_streams": [{"timeout": True}], "collision_controls": [],
        "summary": {}}})
    assert d2_timeout["d2_d3"]["timeouts"] == 1
    e1_escape = _analyze_e1e2({"model_worlds": [{"world_kind": "infeasible",
        "arms": {"bridge_on": {"false_certified_escape": True,
                                  "candidate_count": 1,
                                  "refinement_request_count": 0,
                                  "funded_refinement_count": 0},
                 "bridge_off": {"false_certified_escape": False,
                                   "candidate_count": 0,
                                   "refinement_request_count": 0,
                                   "funded_refinement_count": 0},
                 "supplied_path_parity": {"projection_equal": True}}}]})
    assert e1_escape["decision"] == "FAIL"
    e1_stale_receipt = _analyze_e1e2({"model_worlds": [{"world_kind": "feasible",
        "arms": {"bridge_on": {"verified_feasible_candidate": None,
                                  "invalid_feasibility_receipt_count": 1,
                                  "candidate_count": 1, "refinement_request_count": 0,
                                  "funded_refinement_count": 0},
                 "bridge_off": {"verified_feasible_candidate": False,
                                   "candidate_count": 0, "refinement_request_count": 0,
                                   "funded_refinement_count": 0},
                 "supplied_path_parity": {"projection_equal": True}}}]})
    assert e1_stale_receipt["null_results"] > 0
    assert e1_stale_receipt["decision"] == "NOT_ESTABLISHED"
    e1_parity = _analyze_e1e2({"model_worlds": [{"world_kind": "feasible",
        "arms": {"bridge_on": {"false_certified_escape": False,
                                  "candidate_count": 1,
                                  "refinement_request_count": 0,
                                  "funded_refinement_count": 0},
                 "bridge_off": {"false_certified_escape": False,
                                   "candidate_count": 0,
                                   "refinement_request_count": 0,
                                   "funded_refinement_count": 0},
                 "supplied_path_parity": {"projection_equal": False}}}]})
    assert e1_parity["decision"] == "FAIL"
    null_row = {"family": "graph_role", "case_kind": "target", "paired_id": "dev-null",
                "arms": {"recall_on": None, "recall_off": None,
                         "mismatched_source": None}}
    result = _classify_family([null_row], "graph_role")
    assert result["null_results"] == len(ARMS)
    assert result["decision"] == "NOT_ESTABLISHED"
    timeout = {"family": "graph_role", "case_kind": "target", "paired_id": "dev-timeout",
               "arms": {arm: {"solved": False, "timeout": True,
                               "exact_candidate_checks": 0,
                               "target_digest": "same-target"} for arm in ARMS}}
    result = _classify_family([timeout], "graph_role")
    assert result["timeouts"] == len(ARMS)
    assert result["decision"] == "NOT_ESTABLISHED"
    invariant = {"family": "graph_role", "case_kind": "incompatible_decoy",
                 "paired_id": "dev-invariant",
                 "arms": {arm: {"solved": False, "false_grounded": arm == "recall_on",
                                 "exact_candidate_checks": 1,
                                 "target_digest": "same-target"} for arm in ARMS}}
    result = _classify_family([invariant], "graph_role")
    assert result["false_grounded"]["incompatible_decoy"] == 1
    assert result["decision"] == "FAIL"  # a witnessed invariant violation fails at any n.
    d1_timeout = {"orbit_sequences": [{"bridge_on": {"exact_continuation": False,
                      "timeout": True, "bridge_count": 0, "funded_steps": 0,
                      "time_infer_restored": True},
                      "bridge_off": {"exact_continuation": False, "bridge_count": 0,
                      "funded_steps": 0, "time_infer_restored": True}}],
                  "unsupported_controls": []}
    assert _analyze_d1(d1_timeout)["timeouts"] == 1
    d1_invariant = {"orbit_sequences": [], "unsupported_controls": [{
        "control_kind": "no_frame", "bridge_on": {"unsupported_exact_claim": True,
            "exact_continuation": True, "bridge_count": 0, "funded_steps": 0,
            "time_infer_restored": True},
        "bridge_off": {"unsupported_exact_claim": False, "exact_continuation": False,
            "bridge_count": 0, "funded_steps": 0, "time_infer_restored": True}}]}
    assert _analyze_d1(d1_invariant)["decision"] == "FAIL"
    assert analyze({"rows": [timeout], "prereg_hash": "development"})["d1"]["decision"] == "NOT_ESTABLISHED"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--self-check"]:
        _self_check()
        print("cognition_p4_analysis_v1 self-check passed (development-only)")
        return
    if len(argv) != 1:
        raise SystemExit("usage: cognition_p4_analysis_v1.py <heldout_report.json> | --self-check")
    src = Path(argv[0])
    result = analyze(json.loads(src.read_text()))
    out = src.with_name(src.stem + "_analysis.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
