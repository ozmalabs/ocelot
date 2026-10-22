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
            continue
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
    grouped = paired_generation_deltas(rows, candidate=candidate, ancestor=ancestor)
    generations = sorted(generation for fam, generation in grouped if fam == family)
    if len(generations) < 2:
        return {"status": "NOT_ESTABLISHED", "reason": "insufficient_generations"}
    ids_by_gen = [set(grouped[(family, generation)]) for generation in generations]
    common = sorted(set.intersection(*ids_by_gen))
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
    return {"status": "ESTIMATED", "family": family,
            "generations": generations, "world_clusters": len(common),
            "paired_gain_by_generation": gen_means,
            "final_paired_gain": final_gain, "generation_slope": slope,
            "generation_slope_one_sided_99_lower": slopes[lower_index],
            "final_gain_one_sided_99_lower": gains[lower_index],
            "bootstrap_draws": bootstrap_draws,
            "bootstrap_unit": "world_id_cluster"}


def validate_efficiency_match(rows, *, work_key="primitive_work", tolerance=0.0):
    """Efficiency comparisons require equal paired work within declared tolerance."""
    by = defaultdict(dict)
    for row in rows:
        by[(row["family"], row["generation"], row["world_id"])][row["arm"]] = row
    for key, arms in by.items():
        if "full" not in arms or "unchanged" not in arms:
            return False, {"reason": "unpaired_work", "key": key}
        a, b = arms["full"].get(work_key), arms["unchanged"].get(work_key)
        if a is None or b is None or abs(a - b) > tolerance:
            return False, {"reason": "cost_mismatch", "key": key,
                           "candidate_work": a, "ancestor_work": b}
    return True, {"reason": "matched"}
