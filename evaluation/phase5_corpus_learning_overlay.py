"""Explicit learning-observation overlay for the fixed communication corpus.

The base 74-event corpus remains unchanged and correctly reports no learning
contract.  This separate overlay supplies independently authored typed learning
observations keyed to existing event IDs, then reuses the live ingress and
native Phase 5 recurrence/assessment authorities.  Identities are fixture
annotations, never inferred from signal text or event similarity.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase5_corpus_runner import run_phase5_recurrence_measurement


SCHEMA = "phase5-corpus-learning-overlay.v1"
PROTOCOL_ID = "phase5o-explicit-corpus-learning-overlay-v1"

# The identity and verification fields are explicit fixture evidence.  They
# intentionally use opaque identities so the runner cannot derive recurrence
# from lexical overlap or event ordering.
OVERLAY: tuple[dict[str, Any], ...] = (
    {
        "event_id": "question_unknown",
        "gap_identity": "knowledge|opaque-corpus-alpha|turn:none",
        "kind": "knowledge", "source": "question",
        "content": "opaque-corpus-alpha", "learning_stage": "observed",
        "verification_status": "unverified", "event_stage": "initial_observation",
    },
    {
        "event_id": "info_unknown",
        "gap_identity": "knowledge|opaque-corpus-alpha|turn:none",
        "kind": "knowledge", "source": "question",
        "content": "opaque-corpus-alpha", "learning_stage": "recurrent",
        "verification_status": "unverified", "event_stage": "repeated_observation",
    },
    {
        "event_id": "action_unknown",
        "gap_identity": "planning|opaque-corpus-beta|turn:none",
        "kind": "planning", "source": "action",
        "content": "opaque-corpus-beta", "learning_stage": "observed",
        "verification_status": "unverified", "event_stage": "initial_observation",
    },
    {
        "event_id": "action_world_unknown",
        "gap_identity": "planning|opaque-corpus-beta|turn:none",
        "kind": "planning", "source": "action",
        "content": "opaque-corpus-beta", "learning_stage": "recurrent",
        "verification_status": "unverified", "event_stage": "repeated_observation",
    },
    {
        "event_id": "unresolved_reference",
        "gap_identity": "reference|opaque-corpus-gamma|turn:none",
        "kind": "reference", "source": "reference",
        "content": "opaque-corpus-gamma", "learning_stage": "observed",
        "verification_status": "unverified", "event_stage": "initial_observation",
    },
    {
        "event_id": "action_pronoun",
        "gap_identity": "reference|opaque-corpus-gamma|turn:none",
        "kind": "reference", "source": "reference",
        "content": "opaque-corpus-gamma", "learning_stage": "recurrent",
        "verification_status": "unverified", "event_stage": "repeated_observation",
    },
)


def overlay_corpus(base: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a copied corpus with only explicit overlay observations added."""
    base = load_corpus() if base is None else base
    by_id = {str(event["id"]): event for event in base.get("events", ())}
    missing = [item["event_id"] for item in OVERLAY if item["event_id"] not in by_id]
    if missing:
        raise ValueError(f"overlay event IDs missing from base corpus: {missing}")
    events = []
    for item in OVERLAY:
        event = deepcopy(by_id[item["event_id"]])
        event["learning_observation"] = dict(item)
        events.append(event)
    return {
        "schema": SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "base_corpus_event_ids": [event["id"] for event in events],
        "events": events,
    }


def run_overlay() -> dict[str, Any]:
    """Measure the overlay through the existing production recurrence runner."""
    report = run_phase5_recurrence_measurement(overlay_corpus())
    report["overlay_schema"] = SCHEMA
    report["overlay_protocol_id"] = PROTOCOL_ID
    report["base_corpus_unchanged"] = True
    return report


__all__ = ["OVERLAY", "PROTOCOL_ID", "SCHEMA", "overlay_corpus", "run_overlay"]
