"""Ceiling-safe paired estimands for independent-goal improvement studies."""
from __future__ import annotations

import math
import random
from collections import defaultdict


def paired_generation_deltas(rows, *, candidate="full", ancestor="unchanged"):
    """Return per-generation paired score differences, preserving world clusters."""
    by = {}
    for row in rows:
        key = (row["family"], row["generation"], row["world_id"], row["arm"])
        if key in by:
            raise ValueError(f"duplicate checkpoint outcome: {key}")
        score = row["score"]
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            raise ValueError("scores must be bounded in [0, 1]")
        by[key] = float(score)
    differences = defaultdict(dict)
    for family, generation, world_id, _arm in by:
        left = (family, generation, world_id, candidate)
        right = (family, generation, world_id, ancestor)
        if left not in by or right not in by:
            raise ValueError(f"unpaired checkpoint outcome: {(family, generation, world_id)}")
        differences[(family, generation)][world_id] = by[left] - by[right]
    return {key: dict(sorted(worlds.items())) for key, worlds in differences.items()}


def _mean(values):
    return sum(values) / len(values) if values else None


def summarize_family(rows, *, family, candidate="full", ancestor="unchanged",
                     bootstrap_draws=10000, seed=0):
    """Summarize equal-world paired final gain and generation slope.

    World-cluster bootstrap resamples whole world IDs with replacement and
    keeps their repeated generation/checkpoint measurements together. A
    degenerate ceiling/floor/flat sample has a zero bound and zero effect.
    """
    if (isinstance(bootstrap_draws, bool) or not isinstance(bootstrap_draws, int)
            or bootstrap_draws < 1):
        raise ValueError("bootstrap_draws must be a positive integer")
    grouped = paired_generation_deltas(rows, candidate=candidate, ancestor=ancestor)
    generations = sorted(generation for fam, generation in grouped if fam == family)
    if len(generations) < 3:
        return {"status": "NOT_ESTABLISHED", "reason": "insufficient_generations"}
    if generations != [1, 2, 3]:
        return {"status": "NOT_ESTABLISHED", "reason": "generation_allocation_mismatch"}
    ids_by_gen = [set(grouped[(family, generation)]) for generation in generations]
    if any(ids != ids_by_gen[0] for ids in ids_by_gen[1:]):
        return {"status": "NOT_ESTABLISHED", "reason": "world_cluster_mismatch"}
    common = sorted(ids_by_gen[0])
    if not common:
        return {"status": "NOT_ESTABLISHED", "reason": "no_common_world_clusters"}
    matrix = [[grouped[(family, generation)][world] for generation in generations]
              for world in common]
    gen_means = [_mean([row[i] for row in matrix]) for i in range(len(generations))]
    xbar = _mean(generations)
    denominator = sum((x - xbar) ** 2 for x in generations)
    slope = sum((x - xbar) * y for x, y in zip(generations, gen_means)) / denominator
    final_gain = gen_means[-1]

    rng = random.Random(seed)
    slopes, gains = [], []
    for _ in range(bootstrap_draws):
        sample = [matrix[rng.randrange(len(matrix))] for _ in matrix]
        means = [_mean([row[i] for row in sample]) for i in range(len(generations))]
        slopes.append(sum((x - xbar) * y for x, y in zip(generations, means)) / denominator)
        gains.append(means[-1])
    slopes.sort()
    gains.sort()
    lower_index = max(0, math.ceil(0.01 * bootstrap_draws) - 1)
    slope_p = (1 + sum(value <= 0.0 for value in slopes)) / (bootstrap_draws + 1)
    gain_p = (1 + sum(value <= 0.0 for value in gains)) / (bootstrap_draws + 1)
    return {"status": "ESTIMATED", "family": family,
            "generations": generations, "world_clusters": len(common),
            "paired_gain_by_generation": gen_means,
            "final_paired_gain": final_gain, "generation_slope": slope,
            "generation_slope_one_sided_99_lower": slopes[lower_index],
            "final_gain_one_sided_99_lower": gains[lower_index],
            "generation_slope_bootstrap_p_gt_zero": slope_p,
            "final_gain_bootstrap_p_gt_zero": gain_p,
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_unit": "world_id_cluster"}


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    """Return Holm-adjusted p-values while preserving the supplied test keys."""
    if not isinstance(p_values, dict) or not p_values:
        raise ValueError("Holm adjustment requires at least one named test")
    for name, value in p_values.items():
        if (not name or isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0.0 <= value <= 1.0):
            raise ValueError("Holm p-values must be finite numbers in [0, 1]")
    ordered = sorted(p_values, key=lambda name: (p_values[name], name))
    count = len(ordered)
    adjusted = {}
    running = 0.0
    for rank, name in enumerate(ordered):
        running = max(running, (count - rank) * float(p_values[name]))
        adjusted[name] = min(1.0, running)
    return adjusted


def summarize_families(rows, *, families, candidate="full", ancestor="unchanged",
                       bootstrap_draws=10000, seed=0,
                       minimum_final_gain=0.10,
                       minimum_generation_slope=0.05, alpha=0.01):
    """Apply registered per-family endpoint criteria with phase-wide Holm control.

    Bootstrap tests use the world-cluster resamples from `summarize_family`;
    each family contributes final gain and generation-slope tests to one Holm
    family. Point estimates must also meet the registered practical thresholds.
    """
    if (not families or len(families) != len(set(families))
            or any(not isinstance(family, str) or not family for family in families)):
        raise ValueError("families must be unique nonempty names")
    thresholds = (minimum_final_gain, minimum_generation_slope, alpha)
    if (any(isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) for value in thresholds)
            or not 0 <= minimum_final_gain <= 1
            or not math.isfinite(minimum_generation_slope)
            or not -1 <= minimum_generation_slope <= 1
            or not 0 < alpha < 1):
        raise ValueError("registered thresholds are invalid")
    if (minimum_final_gain != 0.10 or minimum_generation_slope != 0.05
            or alpha != 0.01):
        raise ValueError("P22 registered criteria cannot be weakened or changed")
    summaries = {}
    p_values = {}
    for index, family in enumerate(families):
        result = summarize_family(rows, family=family, candidate=candidate,
            ancestor=ancestor, bootstrap_draws=bootstrap_draws, seed=seed + index)
        summaries[family] = result
        if result.get("status") == "ESTIMATED":
            p_values[f"{family}:final_gain"] = result["final_gain_bootstrap_p_gt_zero"]
            p_values[f"{family}:generation_slope"] = result[
                "generation_slope_bootstrap_p_gt_zero"]
        else:
            p_values[f"{family}:final_gain"] = 1.0
            p_values[f"{family}:generation_slope"] = 1.0
    adjusted = holm_adjust(p_values)
    outcomes = {}
    for family, result in summaries.items():
        final_p = adjusted[f"{family}:final_gain"]
        slope_p = adjusted[f"{family}:generation_slope"]
        result["holm_adjusted_p"] = {
            "final_gain": final_p, "generation_slope": slope_p}
        result["registered_criteria"] = {
            "minimum_final_gain": minimum_final_gain,
            "minimum_generation_slope": minimum_generation_slope,
            "alpha": alpha,
            "passed": result.get("status") == "ESTIMATED"
                and result["final_paired_gain"] >= minimum_final_gain
                and result["generation_slope"] >= minimum_generation_slope
                and result["final_gain_one_sided_99_lower"] > 0
                and result["generation_slope_one_sided_99_lower"] > 0
                and final_p <= alpha and slope_p <= alpha}
        outcomes[family] = result
    return {"status": "ESTIMATED", "families": outcomes,
            "holm_adjusted_p": adjusted, "alpha": alpha,
            "tests_in_holm_family": len(p_values)}


def validate_efficiency_match(rows, *, work_key="primitive_work", tolerance=0.0):
    """Efficiency comparisons require equal paired work within declared tolerance."""
    by = defaultdict(dict)
    for row in rows:
        by[(row["family"], row["generation"], row["world_id"])][row["arm"]] = row
    if not by:
        return False, {"reason": "empty_pair_set"}
    for key, arms in by.items():
        if "full" not in arms or "unchanged" not in arms:
            return False, {"reason": "unpaired_work", "key": key}
        a, b = arms["full"].get(work_key), arms["unchanged"].get(work_key)
        if a is None or b is None or abs(a - b) > tolerance:
            return False, {"reason": "cost_mismatch", "key": key,
                           "candidate_work": a, "ancestor_work": b}
    return True, {"reason": "matched"}
