"""P15 scorecard integrity analyzer; no outcomes are imputed or rescored."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs/research/engine_substrate/COGNITION_LINEAR_P15_PREREG.md"
ARMS = {"unchanged_operator", "adaptive_curriculum", "full_system"}
ARM_ORDER = ("unchanged_operator", "adaptive_curriculum", "full_system")


def _wilson(successes, n):
    if n == 0:
        return None
    z = 1.959963984540054
    p = successes / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [center - radius, center + radius]


def _mcnemar_exact(groups, left, right):
    b = c = 0
    for group in groups.values():
        a, z = bool(group[left]["solved"]), bool(group[right]["solved"])
        b += int(a and not z)
        c += int(z and not a)
    discordant = b + c
    if not discordant:
        return {"left_only": b, "right_only": c, "p_two_sided": 1.0}
    tail = sum(math.comb(discordant, i) for i in range(min(b, c) + 1)) / 2 ** discordant
    return {"left_only": b, "right_only": c, "p_two_sided": min(1.0, 2 * tail)}


def _trend(groups):
    """Conditional logistic arm-by-generation interaction, paired by task seed."""
    features = {
        "unchanged_operator": (0.0, 0.0, 0.0, 0.0),
        "adaptive_curriculum": (0.0, 0.0, 1.0, 0.0),
        "full_system": (1.0, 0.0, 0.0, 0.0),
    }
    strata = []
    for group in groups.values():
        generation = float(group["full_system"]["generation"])
        x = {arm: (features[arm][0], generation if arm == "full_system" else 0.0,
                   features[arm][2], generation if arm == "adaptive_curriculum" else 0.0)
             for arm in ARM_ORDER}
        outcomes = {arm: int(bool(group[arm]["solved"])) for arm in ARM_ORDER}
        successes = sum(outcomes.values())
        if successes in (0, len(ARM_ORDER)):
            continue
        strata.append((x, outcomes, successes))
    beta = [0.0] * 4
    info = None
    for _ in range(80):
        gradient = [0.0] * 4
        info = [[0.0] * 4 for _ in range(4)]
        for x, outcomes, successes in strata:
            subsets = [mask for mask in range(1 << 3)
                       if mask.bit_count() == successes]
            vectors = []
            logits = []
            for mask in subsets:
                vec = [sum(x[ARM_ORDER[j]][k] for j in range(3) if mask & (1 << j))
                       for k in range(4)]
                vectors.append(vec)
                logits.append(sum(beta[k] * vec[k] for k in range(4)))
            peak = max(logits)
            weights = [math.exp(value - peak) for value in logits]
            total = sum(weights)
            probs = [value / total for value in weights]
            observed = [sum(x[arm][k] * outcomes[arm] for arm in ARM_ORDER)
                        for k in range(4)]
            expected = [sum(p * vec[k] for p, vec in zip(probs, vectors))
                        for k in range(4)]
            for i in range(4):
                gradient[i] += observed[i] - expected[i]
                for j in range(4):
                    second = sum(p * vec[i] * vec[j]
                                 for p, vec in zip(probs, vectors))
                    info[i][j] += second - expected[i] * expected[j]
        # Small pivoted elimination for the four-parameter Newton step.
        matrix = [info[i][:] + [gradient[i]] for i in range(4)]
        singular = False
        for col in range(4):
            pivot = max(range(col, 4), key=lambda row: abs(matrix[row][col]))
            if abs(matrix[pivot][col]) < 1e-10:
                singular = True
                break
            matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
            scale = matrix[col][col]
            matrix[col] = [v / scale for v in matrix[col]]
            for row in range(4):
                if row == col:
                    continue
                factor = matrix[row][col]
                matrix[row] = [a - factor * b for a, b in zip(matrix[row], matrix[col])]
        if singular:
            return {"estimable": False, "reason": "singular_conditional_information"}
        step = [matrix[i][4] for i in range(4)]
        beta = [b + max(-2.0, min(2.0, d)) for b, d in zip(beta, step)]
        if max(abs(d) for d in step) < 1e-8:
            break
        if max(abs(b) for b in beta) > 25:
            return {"estimable": False, "reason": "complete_or_near_complete_separation"}
    # Re-invert the observed information to obtain the conditional slope SE.
    matrix = [info[i][:] + [1.0 if i == j else 0.0 for j in range(4)]
              for i in range(4)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda row: abs(matrix[row][col]))
        if abs(matrix[pivot][col]) < 1e-10:
            return {"estimable": False, "reason": "singular_conditional_information"}
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        scale = matrix[col][col]
        matrix[col] = [v / scale for v in matrix[col]]
        for row in range(4):
            if row == col:
                continue
            factor = matrix[row][col]
            matrix[row] = [a - factor * b for a, b in zip(matrix[row], matrix[col])]
    variance = matrix[1][5]
    if variance <= 0:
        return {"estimable": False, "reason": "nonpositive_slope_variance"}
    se = math.sqrt(variance)
    z = beta[1] / se
    p_one_sided = 0.5 * math.erfc(z / math.sqrt(2))
    return {"estimable": True, "model": "seed-stratified conditional logistic, arm_by_generation",
            "full_vs_unchanged_generation_slope_log_odds": beta[1],
            "standard_error": se, "one_sided_99pct_lower_bound": beta[1] - 2.326347874 * se,
            "p_one_sided": p_one_sided, "holm_adjusted_p": p_one_sided,
            "families_in_holm_family": 1}


def _bootstrap_differences(groups, samples=10_000):
    pairs = list(groups.values())
    rng = random.Random(15_151)
    work_diffs, latency_diffs = [], []
    for _ in range(samples):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        work_diffs.append(sum(g["full_system"]["agent_work_units"] -
                              g["unchanged_operator"]["agent_work_units"] for g in sample) / len(sample))
        latency_diffs.append(sum(g["full_system"].get("task_seconds", 0.0) -
                                 g["unchanged_operator"].get("task_seconds", 0.0)
                                 for g in sample) / len(sample))
    work_diffs.sort()
    latency_diffs.sort()
    lo, hi = int(0.025 * samples), int(0.975 * samples)
    return {"resamples": samples,
            "full_minus_unchanged_work_units_ci95": [work_diffs[lo], work_diffs[hi]],
            "full_minus_unchanged_latency_seconds_ci95": [latency_diffs[lo], latency_diffs[hi]]}


def _verify_frozen_hashes(meta):
    if not PREREG.is_file():
        raise ValueError("frozen P15 preregistration is missing")
    frozen = {}
    for line in PREREG.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*`?(\w+)`?\s*\|\s*`?([0-9a-f]{64})`?\s*\|", line)
        if match:
            frozen[match.group(1)] = match.group(2)
    provenance = meta.get("artifact_provenance", {})
    required = ("source_bundle_sha256", "runner_sha256", "analyzer_sha256",
                "profile_sha256", "world_adapter_sha256", "engine_binary_sha256",
                "dependency_closure_sha256", "engine_source_sha256")
    missing = [name for name in required if name not in frozen]
    mismatches = {name: (provenance.get(name), frozen.get(name)) for name in required
                  if provenance.get(name) != frozen.get(name)}
    if missing or mismatches:
        raise ValueError(f"held-out artifact hash mismatch: missing={missing}, mismatches={mismatches}")


def _integrity_controls(payload):
    controls = []
    fields = ("world", "access", "input", "invariant", "action")
    for draw in range(100):
        kind = fields[draw % len(fields)]
        altered = deepcopy(payload)
        row = altered["records"][draw % len(altered["records"])]
        if kind == "world":
            row["world_sha256"] = "tampered-world"
        elif kind == "access":
            row["world_access_sha256"] = "tampered-access"
        elif kind == "input":
            row["input_audit"]["answer_fields_absent"] = False
        elif kind == "invariant":
            row["invariant_checks_passed"] = 0
        else:
            row["actions"] = 1
        detected = analyze(altered, _skip_controls=True)["integrity_status"] == "FAIL"
        controls.append({"seed": 25_113_000 + draw, "control": kind,
                         "tampering_detected": detected})
    return {"n": len(controls), "passed": sum(x["tampering_detected"] for x in controls),
            "failed": sum(not x["tampering_detected"] for x in controls),
            "seed_start": 25_113_000, "seed_end_exclusive": 25_113_100,
            "controls": controls}


def analyze(payload, _skip_controls=False):
    if payload.get("schema") != "pmb-scorecard-v1":
        raise ValueError("expected pmb-scorecard-v1")
    meta = payload.get("metadata", {})
    if meta.get("phase") != "linear-p15-v1" or meta.get("split") not in {"development", "heldout"}:
        raise ValueError("scorecard phase/split mismatch")
    if meta.get("human_comparison") != "UNAVAILABLE_PROTOCOL_NOT_MATCHED":
        raise ValueError("unsupported human comparison claim")
    rows = payload.get("records")
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty scorecard")
    paired = defaultdict(dict)
    failures = {"status": 0, "pairing": 0, "world": 0, "inputs": 0,
                "invariants": 0, "actions": 0, "work": 0, "family": 0}
    for row in rows:
        if row.get("family") != "permutation_process_macro":
            failures["family"] += 1
        arm, seed = row.get("profile"), row.get("seed")
        if arm not in ARMS or arm in paired[seed]:
            failures["pairing"] += 1
            continue
        paired[seed][arm] = row
        failures["status"] += row.get("status") != "COMPLETED"
        audit = row.get("input_audit", {})
        failures["inputs"] += int(not all(audit.get(k) is True for k in
            ("answer_fields_absent", "hidden_strategy_absent", "sealed_ids_absent")))
        failures["inputs"] += int(audit.get("same_primitive_access_hash") !=
                                   row.get("world_access_sha256"))
        failures["invariants"] += int(row.get("invariant_checks_passed") != 1)
        failures["actions"] += int(row.get("actions") != 0)
        failures["status"] += int(row.get("graph_nodes_end", 0) >
                                   meta.get("limits", {}).get("max_nodes", 0))
        failures["status"] += int(row.get("graph_serialized_bytes", 0) >
                                   meta.get("limits", {}).get("max_graph_bytes", 0))
        expected_work = (int(row.get("generation", 0)) + 2
                         if arm == "full_system" else 2)
        failures["work"] += int(row.get("agent_work_units") != expected_work)
        failures["work"] += int(row.get("world_generation_work_units") != 2)
        failures["work"] += int(row.get("scorer_evaluation_calls") != 1)
        remaining = row.get("budget_remaining")
        max_budget = 100_000 if arm == "full_system" else 400_000
        failures["work"] += int(not isinstance(remaining, (int, float)) or
                                not math.isfinite(remaining) or remaining < 0 or
                                remaining > max_budget)
        elapsed = row.get("task_seconds")
        failures["status"] += int(not isinstance(elapsed, (int, float)) or
                                   not math.isfinite(elapsed) or elapsed < 0)
    n_per_generation = int(meta.get("n_per_generation_per_arm", 0))
    generations = meta.get("completed_generations", [])
    if generations != [1, 2, 3]:
        raise ValueError("P15 scorecard must contain all three registered generations")
    if meta["split"] == "heldout" and n_per_generation != 200:
        raise ValueError("held-out scorecard must contain 200 tasks per generation and arm")
    block = 1 if meta["split"] == "development" else 2
    if meta.get("family_codes") != [11, 12, 13] or meta.get("task_control_block") != block:
        raise ValueError("P15 family or split allocation does not match the preregistration")
    if meta.get("integrity_control_seeds") != {
            "family_code": 11, "start": 25_113_000, "end_exclusive": 25_113_100}:
        raise ValueError("P15 integrity-control allocation differs from the preregistration")
    expected_selection = {f"generation_{generation}": [800, 801] for generation in generations}
    if meta.get("candidate_selection_draws") != expected_selection or \
            meta.get("training_seed_base") != 25_110_000:
        raise ValueError("P15 training/selection allocation differs from the preregistration")
    expected_seeds = {25_000_000 + (10 + generation) * 10_000 + block * 1_000 + draw
                      for generation in generations for draw in range(n_per_generation)}
    if {int(seed) for seed in paired} != expected_seeds:
        raise ValueError("P15 task seed list differs from its fixed allocation")
    if meta["split"] == "heldout":
        _verify_frozen_hashes(meta)
    expected_n = n_per_generation * len(generations)
    for seed, group in paired.items():
        failures["pairing"] += int(set(group) != ARMS)
        failures["world"] += int(len({r.get("world_sha256") for r in group.values()}) != 1)
        failures["world"] += int(len({r.get("world_access_sha256") for r in group.values()}) != 1)
    failures["pairing"] += int(len(paired) != expected_n)
    rates = {}
    for arm in sorted(ARMS):
        values = [bool(group[arm].get("solved")) for group in paired.values() if arm in group]
        rates[arm] = {"solved": sum(values), "n": len(values),
                      "accuracy": sum(values) / len(values) if values else None}
    by_generation = {}
    paired_by_generation = {}
    for generation in generations:
        paired_by_generation[generation] = {
            seed: group for seed, group in paired.items()
            if next(iter(group.values())).get("generation") == generation}
        by_generation[str(generation)] = {}
        for arm in sorted(ARMS):
            values = [bool(row.get("solved")) for row in rows
                      if row.get("generation") == generation and row.get("profile") == arm]
            successes = sum(values)
            by_generation[str(generation)][arm] = {
                "solved": successes, "n": len(values),
                "accuracy": successes / len(values) if values else None,
                "wilson_95": _wilson(successes, len(values))}
        by_generation[str(generation)]["paired_full_vs_unchanged_mcnemar"] = _mcnemar_exact(
            paired_by_generation[generation], "full_system", "unchanged_operator")
    integrity_failures = sum(failures.values())
    result = {"schema": "pmb-linear-p15-v1-analysis-v1", "phase": meta["phase"],
            "split": meta["split"], "family": "permutation_process_macro",
            "paired_tasks": len(paired), "arms": rates, "by_generation": by_generation,
            "trend": _trend(paired), "paired_bootstrap_cost_latency": _bootstrap_differences(paired),
            "integrity_failures": failures,
            "integrity_status": "PASS" if integrity_failures == 0 else "FAIL",
            "full_vs_unchanged_difference": (
                rates["full_system"]["accuracy"] - rates["unchanged_operator"]["accuracy"]
                if rates["full_system"]["accuracy"] is not None
                and rates["unchanged_operator"]["accuracy"] is not None else None),
            "human_comparison": "UNAVAILABLE_PROTOCOL_NOT_MATCHED",
            "claim_boundary": "finite permutation process-macro family only; report registered trend and costs without general capability or human-comparison claims"}
    if meta["split"] == "heldout" and not _skip_controls:
        controls = _integrity_controls(payload)
        result["integrity_controls"] = controls
        if controls["failed"]:
            result["integrity_status"] = "FAIL"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        from evaluation.process_mastery.linear_p15_v1 import run
        payload = run(n=2, self_check=True)
    elif args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        parser.error("provide a scorecard or --self-check")
    result = analyze(payload)
    if result["integrity_status"] != "PASS":
        raise SystemExit(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
