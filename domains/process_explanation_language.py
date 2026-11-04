"""Bounded, auditable two-step explanation surface for the P20 receiver.

The format intentionally carries each precondition as an explicit header and
uses two independently monitored sentences. The receiver reparses those
sentences through LanguageProduction's grounded comprehension path; it never
receives source process nodes or native expressions.
"""
from __future__ import annotations


def produce_ordered_explanation(language: str, steps: list[dict], production) -> dict:
    if len(steps) != 2:
        return {"status": "unsupported", "reason": "exactly_two_steps_required"}
    rendered = []
    receipts = []
    for step in steps:
        precondition = step.get("precondition")
        frame = step.get("frame")
        if not isinstance(precondition, str) or not precondition or not isinstance(frame, dict):
            return {"status": "unsupported", "reason": "step_needs_precondition_and_frame"}
        result = production.produce(language, frame)
        if not result.get("accepted"):
            return {"status": "unmonitored", "reason": "sentence_failed_self_monitor"}
        rendered.append(f"{precondition} :: {result['overt_speech']}")
        receipts.append(result)
    return {"status": "produced", "text": " THEN ".join(rendered),
            "language": language,
            "supported_vocabulary": sorted({str(event) for event in
                                              (step["frame"].get("event") for step in steps)}),
            "production_receipts": receipts}


def parse_ordered_explanation(text: str, language: str, production) -> dict:
    parts = text.split(" THEN ")
    if len(parts) != 2:
        return {"parse_status": "ambiguous"}
    frames, preconditions = [], []
    for part in parts:
        if " :: " not in part:
            return {"parse_status": "ambiguous"}
        precondition, sentence = part.split(" :: ", 1)
        precondition = precondition.strip()
        if not precondition or not sentence.strip():
            return {"parse_status": "ambiguous"}
        frame = production._comprehend(language, sentence.strip())
        if not frame.get("event"):
            return {"parse_status": "ambiguous"}
        frames.append(frame)
        preconditions.append(precondition)
    events = [frame["event"] for frame in frames]
    return {"parse_status": "parsed", "explanation_kind": "ordered_two_step",
            "semantic_sequence": ["seq", events],
            "required_preconditions": preconditions,
            "semantic_frames": frames}
