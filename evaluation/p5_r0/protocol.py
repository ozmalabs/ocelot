"""Closed canonical protocol primitives for P5-R0."""
from __future__ import annotations
from typing import Any, Mapping
from evaluation.p0a.canonical import canonical_bytes, object_hash, sha256
TERMINAL_OUTCOMES = frozenset({"complete_correct", "complete_wrong", "abstain", "protocol_error", "resource_exhausted", "safety_violation", "negative_transfer", "leakage_detected", "containment_failure", "rollback_impasse"})
SPLITS = ("train", "development", "held_out")
ARMS = ("cold_reset", "frozen_transfer", "warm_adaptive")
DOMAINS = ("opaque-domain-01", "opaque-domain-02")
AXES = {"modality": ("grid_discrete", "embodied_sensorimotor"), "latent_mechanics": ("memory_reset", "memory_persistent", "causal_absent", "causal_present"), "action_effect_algebra": ("flat_primitive", "compositional"), "reward_constraints": ("sparse_goal", "constrained_progress"), "tool_vocabulary": ("primitive_tools", "composed_tools")}
class P5R0Error(ValueError): pass
def digest(value: Any) -> str: return sha256(value if isinstance(value, (bytes, bytearray)) else canonical_bytes(value))
def is_digest(value: Any) -> bool: return isinstance(value, str) and len(value) == 71 and value.startswith("sha256:") and all(c in "0123456789abcdef" for c in value[7:])
def closed(value: Mapping[str, Any], fields: set[str], schema: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields or value.get("schema") != schema: raise P5R0Error(f"closed {schema}")
    return dict(value)
def validate_digest(value: Any, label: str) -> str:
    if not is_digest(value): raise P5R0Error(label)
    return value
def hash_without(value: Mapping[str, Any], *fields: str) -> str: return object_hash(dict(value), *fields)
