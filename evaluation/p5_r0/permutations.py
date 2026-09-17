"""Semantics-preserving and semantic-alteration controls."""
from __future__ import annotations
from typing import Any
from .protocol import P5R0Error, digest

def label_permutation(labels: list[str]) -> dict[str, Any]:
    if len(set(labels)) != len(labels): raise P5R0Error("labels not bijective")
    # Reverse is deterministic; inverse_normalize restores canonical labels.
    mapping = dict(zip(labels, reversed(labels)))
    return {"schema": "P5R0LabelPermutationV1", "mapping": mapping, "permutation_digest": digest(mapping)}

def mechanics_permutation(catalog: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [row.get("combination_id") for row in catalog]
    if any(not isinstance(v, str) for v in ids) or len(set(ids)) != len(ids): raise P5R0Error("mechanics catalog")
    mapping = dict(zip(ids, reversed(ids)))
    return {"schema": "P5R0MechanicsPermutationV1", "mapping": mapping, "permutation_digest": digest(mapping)}

def altered_semantics(case: dict[str, Any]) -> dict[str, Any]:
    altered = dict(case); altered["source_commitment"] = digest({"altered": case["source_commitment"]}); altered["altered"] = True; altered["case_digest"] = digest(altered)
    return altered

def inverse_normalize(value: Any, permutation: dict[str, Any]) -> Any:
    if not isinstance(permutation, dict) or "mapping" not in permutation: raise P5R0Error("permutation")
    inverse = {v: k for k, v in permutation["mapping"].items()}
    if isinstance(value, str): return inverse.get(value, value)
    if isinstance(value, list): return [inverse_normalize(v, permutation) for v in value]
    if isinstance(value, dict): return {k: inverse_normalize(v, permutation) for k, v in value.items()}
    return value
