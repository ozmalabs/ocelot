"""A deterministic ELIZA-style reference floor for the Phase 8 corpus.

This adapter is intentionally not a cognitive model.  It applies a fixed,
ordered set of lexical/reflection patterns to each signal and emits the raw
rule trace.  It never reads corpus annotations and never labels a response as
an interpretation, grounding result, action, or repair.  Those dimensions are
therefore unavailable in the resulting scorecard.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Mapping

from evaluation.comparative_release_gate import (
    BASELINES,
    DIMENSIONS,
    CORPUS_PROTOCOL_ID,
    DimensionMeasurement,
    Scorecard,
    TARGET,
    comparison_summary,
    evaluate_release_gate,
)
from evaluation.conversational_manifold_phase0 import FIXTURE, load_corpus
from evaluation.phase8_corpus_runner import (
    CONTEXT_AWARE_PROTOCOL_ID, PROTOCOL_ID, scorecard_to_dict, unrun_scorecard,
)


ADAPTER_SYSTEM = "eliza_floor"
ADAPTER_ENTRYPOINT = "evaluation.reference_adapters.eliza_floor"
ADAPTER_SCHEMA = "phase8_eliza_floor_run.v2"
ANNOTATION_PROTOCOL = "phase8-reference-protocol-v1"
REPORT_SCHEMA = "phase8_eliza_floor_report.v2"

_WORD = re.compile(r"[A-Za-z0-9']+")


def _tokens(signal: str) -> list[str]:
    return _WORD.findall(signal.lower())


def _reflect(token: str) -> str:
    return {"i": "you", "me": "you", "my": "your", "mine": "yours",
            "you": "I", "your": "my", "yours": "mine"}.get(token, token)


def _reflected(tokens: list[str]) -> str:
    return " ".join(_reflect(token) for token in tokens)


def respond(signal: str, *, input_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic output and its complete input/rule trace.

    The v5 context is passed to the reference policy as a first-class input.
    The ELIZA floor intentionally remains stateless and signal-rule driven, so
    it records but does not use that additional context to choose its reply.
    """
    original = str(signal)
    tokens = _tokens(original)
    lowered = " ".join(tokens)
    rule = "fallback"
    output = "Please tell me more."
    capture: list[str] = []

    # Rule order is part of the adapter protocol and is intentionally stable.
    if any(token in {"hello", "hi", "hey", "greetings"} for token in tokens):
        rule, output = "greeting", "How does greeting you make you feel?"
    elif tokens and tokens[0] in {"why", "how", "what", "when", "where", "who", "which", "can", "could", "will", "did", "do", "does", "is", "are"}:
        rule, output = "question", "Why do you ask?"
    else:
        match = re.search(r"\bi am\s+(.+?)(?:\.|!|\?|$)", original, re.IGNORECASE)
        if match:
            capture = _tokens(match.group(1))
            rule, output = "i_am", f"How long have you been {_reflected(capture)}?"
        else:
            match = re.search(r"\bi feel\s+(.+?)(?:\.|!|\?|$)", original, re.IGNORECASE)
            if match:
                capture = _tokens(match.group(1))
                rule, output = "i_feel", f"Do you often feel {_reflected(capture)}?"
            elif any(token in {"sorry", "apologize", "apologies"} for token in tokens):
                rule, output = "apology", "Please do not apologize."
            elif any(token in {"remember", "recall", "memory"} for token in tokens):
                rule, output = "memory_keyword", "What does that memory bring to mind?"
            elif any(token in {"mother", "father", "family", "parent"} for token in tokens):
                rule, output = "family_keyword", "Tell me more about your family."
            elif "because" in tokens:
                rule, output = "because", "Is that the real reason?"
            elif any(token in {"dream", "dreams", "dreamed"} for token in tokens):
                rule, output = "dream_keyword", "What do you think that dream means?"
            elif "you" in tokens:
                rule, output = "you_keyword", "We are talking about you, not me."

    trace = {
        "input": original,
        "input_tokens": tokens,
        "rule_id": rule,
        "capture_tokens": capture,
        "output": output,
        "deterministic": True,
        "cognitive_labels": None,
        "failure": None,
    }
    if input_context is not None:
        trace["input_context"] = dict(input_context)
    return trace


def _unavailable(dimension: str, note: str) -> DimensionMeasurement:
    return DimensionMeasurement(
        dimension=dimension, mean=0.0, n=0, ci95_low=0.0, ci95_high=0.0,
        evidence_refs=(f"eliza-floor://{dimension}/not-scored",),
        raw_metric="", notes=note, status="unavailable",
    )


def _provenance_measurement(observations: list[dict[str, Any]]) -> DimensionMeasurement:
    successes = sum(
        bool(item.get("raw_trace_complete")) and item.get("adapter_entrypoint") == ADAPTER_ENTRYPOINT
        for item in observations
    )
    n = len(observations)
    mean = successes / n if n else 0.0
    return DimensionMeasurement(
        dimension="provenance", mean=mean, n=n, ci95_low=mean, ci95_high=mean,
        evidence_refs=(f"eliza-floor://raw-observations/{n}",),
        raw_metric="complete_deterministic_rule_trace",
        notes="Exact completeness check over the fixed raw-observation protocol; no cognitive capability is inferred.",
    )


def scorecard(observations: list[dict[str, Any]], *,
              protocol_id: str = PROTOCOL_ID) -> Scorecard:
    measurements = []
    for dimension in DIMENSIONS:
        if dimension == "provenance":
            measurements.append(_provenance_measurement(observations))
        else:
            measurements.append(
                _unavailable(
                    dimension,
                    "ELIZA floor emits lexical/reflection output without a protocol-authorized cognitive annotation for this dimension.",
                )
            )
    return Scorecard(
        system=ADAPTER_SYSTEM,
        protocol_id=protocol_id,
        reference_class=ADAPTER_SYSTEM,
        collection_status="measured",
        adapter_entrypoint=ADAPTER_ENTRYPOINT,
        annotation_protocol=ANNOTATION_PROTOCOL,
        measurements=tuple(measurements),
    )


def run_eliza_floor(corpus: Mapping[str, Any] | None = None, *,
                    protocol_id: str = PROTOCOL_ID) -> dict[str, Any]:
    """Run deterministic observations under signal-only v4 or matched v5.

    The ELIZA floor remains signal-rule driven. Its v5 raw envelope records the
    same event metadata, held setup answers, and bounded prior dialogue that
    are supplied to other v5 references; no corpus labels are exposed or
    converted into cognitive scores.
    """
    if protocol_id not in {PROTOCOL_ID, CONTEXT_AWARE_PROTOCOL_ID}:
        raise ValueError(f"unsupported ELIZA input protocol: {protocol_id}")
    corpus = load_corpus() if corpus is None else corpus
    observations: list[dict[str, Any]] = []
    history: list[dict[str, str]] = []
    started = time.perf_counter()
    for event in corpus["events"]:
        case_started = time.perf_counter()
        input_profile = ("event_context_v5_history8"
                         if protocol_id == CONTEXT_AWARE_PROTOCOL_ID
                         else "signal_only_v4")
        recent_history = history[-8:] if protocol_id == CONTEXT_AWARE_PROTOCOL_ID else []
        input_context = None
        if protocol_id == CONTEXT_AWARE_PROTOCOL_ID:
            setup = event.get("setup") or {}
            input_context = {
                "interaction": {
                    "mode": event.get("event_mode") or "turn_compatible",
                    "relation": event.get("interaction_relation") or "turn_compatible",
                },
                "held_answers": [
                    {"topic": str(item.get("topic") or ""),
                     "answer": str(item.get("answer") or "")}
                    for item in setup.get("held_answers") or ()
                    if isinstance(item, Mapping)
                ],
                "history": [dict(item) for item in recent_history],
            }
        try:
            trace = respond(event["signal"], input_context=input_context)
            failure = None
        except Exception as exc:  # Keep the required failure trace explicit.
            trace = {"input": str(event.get("signal", "")), "output": "", "rule_id": None,
                     "input_tokens": [], "capture_tokens": [], "deterministic": True,
                     "cognitive_labels": None}
            failure = {"type": type(exc).__name__, "message": str(exc)}
        raw_trace_complete = all(key in trace for key in (
            "input", "input_tokens", "rule_id", "capture_tokens", "output",
            "deterministic", "cognitive_labels")) and (
                bool(trace.get("output")) or failure is not None
            )
        observations.append({
            "case_id": event["id"],
            "signal": event["signal"],
            "input_profile": input_profile,
            "session_history_limit": 8 if protocol_id == CONTEXT_AWARE_PROTOCOL_ID else 0,
            "adapter_entrypoint": ADAPTER_ENTRYPOINT,
            "output": trace.get("output", ""),
            "rule_id": trace.get("rule_id"),
            "raw_trace": trace,
            "raw_trace_complete": raw_trace_complete,
            "failure": failure,
            "elapsed_ms": (time.perf_counter() - case_started) * 1000.0,
        })
        if protocol_id == CONTEXT_AWARE_PROTOCOL_ID:
            history.append({"signal": str(event["signal"]),
                            "response": str(trace.get("output", ""))})
    card = scorecard(observations, protocol_id=protocol_id)
    input_profile = ("event_context_v5_history8"
                     if protocol_id == CONTEXT_AWARE_PROTOCOL_ID
                     else "signal_only_v4")
    baselines = {
        baseline: scorecard_to_dict(
            Scorecard(
                system=baseline, protocol_id=protocol_id, reference_class=baseline,
                collection_status="unavailable", adapter_entrypoint="",
                annotation_protocol=ANNOTATION_PROTOCOL,
                measurements=tuple(_unavailable(d, "Baseline was not run in this increment; no score inferred.") for d in DIMENSIONS),
            )
        ) for baseline in BASELINES if baseline != ADAPTER_SYSTEM
    }
    return {
        "schema": ADAPTER_SCHEMA,
        "report_schema": REPORT_SCHEMA,
        "protocol_id": protocol_id,
        "corpus_protocol_id": CORPUS_PROTOCOL_ID,
        "input_profile": input_profile,
        "session_history_limit": 8 if protocol_id == CONTEXT_AWARE_PROTOCOL_ID else 0,
        "corpus": {"path": str(FIXTURE), "event_count": len(corpus["events"])},
        "adapter": {"system": ADAPTER_SYSTEM, "entrypoint": ADAPTER_ENTRYPOINT,
                    "deterministic": True, "input_profile": input_profile,
                    "session_history_limit": (8 if protocol_id == CONTEXT_AWARE_PROTOCOL_ID else 0),
                    "elapsed_ms": (time.perf_counter() - started) * 1000.0},
        "observations": observations,
        "scorecard": scorecard_to_dict(card),
        "other_baselines": baselines,
        "release_gate": evaluate_release_gate([
            # The target is intentionally unavailable in this baseline-only run.
            unrun_scorecard(TARGET, protocol_id=protocol_id), card,
            *[
                Scorecard(system=baseline, protocol_id=protocol_id, reference_class=baseline,
                          collection_status="unavailable", annotation_protocol=ANNOTATION_PROTOCOL,
                          measurements=tuple(_unavailable(d, "Baseline was not run in this increment; no score inferred.") for d in DIMENSIONS))
                for baseline in BASELINES if baseline != ADAPTER_SYSTEM
            ],
        ]),
        "comparison_summary": comparison_summary([
            unrun_scorecard(TARGET, protocol_id=protocol_id), card,
            *[
                Scorecard(system=baseline, protocol_id=protocol_id, reference_class=baseline,
                          collection_status="unavailable", annotation_protocol=ANNOTATION_PROTOCOL,
                          measurements=tuple(_unavailable(d, "Baseline was not run in this increment; no score inferred.") for d in DIMENSIONS))
                for baseline in BASELINES if baseline != ADAPTER_SYSTEM
            ],
        ]),
    }


def write_report(path: Path, corpus: Mapping[str, Any] | None = None, *,
                 protocol_id: str = PROTOCOL_ID) -> dict[str, Any]:
    report = run_eliza_floor(corpus, protocol_id=protocol_id)
    report["corpus"]["sha256"] = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run deterministic ELIZA floor over Phase 8 corpus")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol-id", choices=(PROTOCOL_ID, CONTEXT_AWARE_PROTOCOL_ID),
                        default=PROTOCOL_ID)
    args = parser.parse_args()
    result = write_report(args.output, protocol_id=args.protocol_id)
    print(json.dumps({"output": str(args.output), "events": result["corpus"]["event_count"],
                      "status": result["release_gate"]["status"]}))
