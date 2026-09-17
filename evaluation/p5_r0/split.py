"""Evaluator-owned taxonomy and exact factorized split commitments."""
from __future__ import annotations
from typing import Any
from .protocol import AXES, DOMAINS, P5R0Error, digest, is_digest

COMBINATIONS = {"T01": {"memory": "reset", "causal": "present", "action_effect": "flat_primitive", "reward": "sparse_goal", "tools": "primitive_tools"}, "T02": {"memory": "persistent", "causal": "present", "action_effect": "flat_primitive", "reward": "sparse_goal", "tools": "primitive_tools"}, "T03": {"memory": "persistent", "causal": "absent", "action_effect": "flat_primitive", "reward": "sparse_goal", "tools": "primitive_tools"}, "T04": {"memory": "reset", "causal": "present", "action_effect": "compositional", "reward": "constrained_progress", "tools": "primitive_tools"}, "D01": {"memory": "persistent", "causal": "present", "action_effect": "compositional", "reward": "constrained_progress", "tools": "primitive_tools"}, "D02": {"memory": "reset", "causal": "absent", "action_effect": "flat_primitive", "reward": "constrained_progress", "tools": "composed_tools"}, "H01": {"memory": "reset", "causal": "absent", "action_effect": "compositional", "reward": "constrained_progress", "tools": "composed_tools"}, "H02": {"memory": "persistent", "causal": "absent", "action_effect": "compositional", "reward": "constrained_progress", "tools": "composed_tools"}}

# This is part of the signed split commitment, not an inferred graph.  The
# catalog currently contains five one-factor edges; adding/removing an edge is
# therefore a lock-breaking protocol change.
CONTRAST_MATRIX = (
    {"pair_id": "T01_T02_memory", "left": "T01", "right": "T02", "factor": "memory", "relation": "non_invariant"},
    {"pair_id": "T02_T03_causal", "left": "T02", "right": "T03", "factor": "causal", "relation": "non_invariant"},
    {"pair_id": "T04_D01_memory", "left": "T04", "right": "D01", "factor": "memory", "relation": "non_invariant"},
    {"pair_id": "D02_H01_action_effect", "left": "D02", "right": "H01", "factor": "action_effect", "relation": "non_invariant"},
    {"pair_id": "H01_H02_memory", "left": "H01", "right": "H02", "factor": "memory", "relation": "non_invariant"},
)

def contrast_matrix() -> list[dict[str, Any]]:
    return [dict(row, arms=["cold_reset", "frozen_transfer", "warm_adaptive"], domains=list(DOMAINS), ordinals=[0, 1, 2]) for row in CONTRAST_MATRIX]

def build_taxonomy() -> dict[str, Any]:
    taxonomy = {"schema": "P5R0TaxonomyV1", "version": 1, "axes": {k: list(v) for k, v in AXES.items()}, "display_permutation_allowed": True}; taxonomy["taxonomy_digest"] = digest(taxonomy); return taxonomy

def validate_taxonomy(taxonomy: dict[str, Any]) -> dict[str, Any]:
    if set(taxonomy) != {"schema", "version", "axes", "display_permutation_allowed", "taxonomy_digest"} or taxonomy["schema"] != "P5R0TaxonomyV1" or taxonomy["version"] != 1 or taxonomy["axes"] != {k: list(v) for k, v in AXES.items()} or taxonomy["display_permutation_allowed"] is not True or taxonomy["taxonomy_digest"] != digest({k: v for k, v in taxonomy.items() if k != "taxonomy_digest"}): raise P5R0Error("taxonomy commitment")
    return taxonomy

def build_split_commitment(seed: str = "p5-r0-v2") -> dict[str, Any]:
    if not isinstance(seed, str) or not seed: raise P5R0Error("split seed")
    split = {"schema": "P5R0SplitCommitmentV1", "seed": seed, "taxonomy_digest": build_taxonomy()["taxonomy_digest"], "combinations": [{"combination_id": cid, "split": "train" if cid.startswith("T") else "development" if cid.startswith("D") else "held_out", "factors": dict(factors), "case_count_per_domain": 3} for cid, factors in COMBINATIONS.items()], "domain_tokens": list(DOMAINS), "contrast_matrix": contrast_matrix()}; split["split_digest"] = digest(split); return split

def validate_split_commitment(split: dict[str, Any]) -> dict[str, Any]:
    if set(split) != {"schema", "seed", "taxonomy_digest", "combinations", "domain_tokens", "contrast_matrix", "split_digest"} or split["schema"] != "P5R0SplitCommitmentV1" or split["taxonomy_digest"] != build_taxonomy()["taxonomy_digest"] or split["domain_tokens"] != list(DOMAINS) or split["contrast_matrix"] != contrast_matrix() or split["split_digest"] != digest({k: v for k, v in split.items() if k != "split_digest"}): raise P5R0Error("split commitment")
    if [r["combination_id"] for r in split["combinations"]] != list(COMBINATIONS): raise P5R0Error("split order")
    factors = {r["combination_id"]: r["factors"] for r in split["combinations"]}
    for pair in split["contrast_matrix"]:
        if pair["left"] not in factors or pair["right"] not in factors: raise P5R0Error("contrast pair combination")
        changed = [key for key in factors[pair["left"]] if factors[pair["left"]][key] != factors[pair["right"]][key]]
        if changed != [pair["factor"]]: raise P5R0Error("contrast pair factor")
    return split

def build_case_index(split: dict[str, Any], cards: list[dict[str, Any]], *, cases_per_domain: int = 3) -> list[dict[str, Any]]:
    validate_split_commitment(split)
    if len(cards) != 2 or cases_per_domain != 3: raise P5R0Error("canonical case cardinality")
    rows = []
    for card in cards:
        for combo in split["combinations"]:
            for ordinal in range(cases_per_domain):
                factors = dict(combo["factors"])
                body = {"schema": "P5R0CaseCommitmentV1", "case_id": f"{card['domain_token']}:{combo['combination_id']}:{ordinal+1:02d}", "domain_token": card["domain_token"], "combination_id": combo["combination_id"], "split": combo["split"], "ordinal": ordinal, "factors": factors, "generator_seed": digest({"seed": split["seed"], "card": card["card_digest"], "combo": combo["combination_id"], "ordinal": ordinal}), "source_commitment": digest({"source": card["generator_digest"], "seed": split["seed"], "combo": combo["combination_id"], "ordinal": ordinal, "factors": factors}), "mechanics_digest": digest({"domain": card["modality"], "factors": factors, "oracle": "P5R0MechanicsSpecV2"})}
                body["case_digest"] = digest(body); rows.append(body)
    return rows
