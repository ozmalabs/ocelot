"""Evaluator-owned baseline controls with immutable provenance."""
from __future__ import annotations
from typing import Any
from .protocol import P5R0Error, digest

def exact_memorizer(train_hashes: set[str], case_digest: str) -> dict[str, Any]:
    return {"baseline_id": "exact_memorizer", "action": "recognize" if case_digest in train_hashes else "abstain", "provenance_digest": digest({"baseline": "exact_memorizer", "train_hashes": sorted(train_hashes)})}

def label_blind_random(seed: int, legal_actions: list[str]) -> dict[str, Any]:
    if not legal_actions: raise P5R0Error("random baseline legal actions")
    return {"baseline_id": "label_blind_random", "action": legal_actions[seed % len(legal_actions)], "seed": seed, "provenance_digest": digest({"baseline": "label_blind_random", "seed": seed, "actions": legal_actions})}

def template_memorizer(train_templates: set[str], template: str) -> dict[str, Any]:
    return {"baseline_id": "template_memorizer", "action": "template_match" if template in train_templates else "abstain", "provenance_digest": digest({"baseline": "template_memorizer", "train_templates": sorted(train_templates)})}
