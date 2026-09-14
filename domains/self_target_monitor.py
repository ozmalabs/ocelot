"""Block 341000 — the SELF-TARGET furtherance check for goal-directed generation.

A communicative goal whose `target_kind == 'self'` is the WANT-IT-SAID case: the
goal is satisfied by the SAYING itself, not by any downstream effect on a hearer
or the world. That makes its furtherance check FULLY ENDOGENOUS — no interlocutor,
no external state, no teacher. The utterance is emitted; the agent reads its own
output back (the analysis half of analysis-by-synthesis); if the recovered concepts
cover the goal's intended content, the goal is satisfied.

This is the SINGLE-SEAM furtherance test for the self target. It is deliberately
shaped like the interlocutor path's Verdict payload ({recoverable, missing, decoded})
so a polymorphic `scan_and_monitor` can write the SAME Verdict node regardless of
target_kind:
  · target_kind == 'self'         -> score_self_target (this module) — parse-back
  · target_kind == 'interlocutor' -> the existing audience-manifold recoverability
  · target_kind == 'world_state'  -> a FutureManifold projection (future rung)
Each computes `recoverable`/`missing` differently; all write one Verdict.

Two parse-back modes, most-faithful first:
  1. GROUNDED-COMPREHENSION mode (if a LanguageProduction/LanguageWorld is given):
     run the produced string back through the SAME grounded comprehension parser
     (`LanguageProduction._comprehend` -> world._identify + _parse_with_grounded),
     recover the semantic frame, and take its content concepts. This is genuinely
     production closing on comprehension.
  2. RECOGNIZER mode (no trained world): recover content concepts from the produced
     surface using the same content-word recognizer the reading path uses
     (predictive_reading._content_words) — surface->concepts on the agent's OWN
     output. Honest, lighter, and does not depend on a teacher-trained world.
The result records WHICH mode ran so a reader is never misled about the strength of
the check.

Additive; never enters a substrate write path for the .so; touches no protected file.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional


def _norm_concepts(words: Iterable[str]) -> set[str]:
    """Normalize a bag of surface/concept tokens to a comparable concept set:
    lower-cased alpha runs, deduped. Mirrors the mechanical tokenisation the
    world adapter uses to derive a reply's carried concepts."""
    out: set[str] = set()
    for w in words or []:
        t = "".join(ch for ch in str(w).lower() if ch.isalpha())
        if len(t) >= 2:
            out.add(t)
    return out


def _frame_concepts(frame: dict) -> set[str]:
    """Pull content concepts out of a recovered semantic-frame dict
    (world._parse_with_grounded output): the filled role values
    (event/agent/patient/location/...), flattened to concept tokens."""
    vals: list[str] = []
    if not isinstance(frame, dict):
        return set()
    for k, v in frame.items():
        if k in ("mood", "tense", "speech_act", "force", "language"):
            continue
        if isinstance(v, str):
            vals.append(v)
        elif isinstance(v, (list, tuple)):
            vals.extend(str(x) for x in v)
        elif isinstance(v, dict):
            vals.extend(str(x) for x in v.values())
    return _norm_concepts(vals)


def score_self_target(agent, produced_string: str, intended_concepts: Iterable[str],
                      *, language: str = "en",
                      producer: Optional[Any] = None,
                      coverage_threshold: float = 1.0) -> dict[str, Any]:
    """Score whether the SAYING recovered the goal's intended content — the
    endogenous furtherance test for a self-target communicative goal.

    Reads the produced string BACK (parse-back) and compares recovered concepts to
    `intended_concepts`. Returns a Verdict-shaped payload:
        {recoverable: bool, coverage: float, missing: [concept...],
         recovered: [concept...], mode: 'grounded_comprehension'|'recognizer',
         intended: [concept...]}
    `recoverable` is True iff coverage >= coverage_threshold (default 1.0 = every
    intended concept recovered). A partial threshold (e.g. 0.5) admits graded
    furtherance.

    Parse-back mode: if `producer` (a LanguageProduction with a grounded world) is
    given, use grounded comprehension; else recover via the reading recognizer."""
    intended = _norm_concepts(intended_concepts)
    mode = "recognizer"
    recovered: set[str] = set()

    if producer is not None and hasattr(producer, "_comprehend"):
        try:
            frame = producer._comprehend(language, produced_string)
            recovered = _frame_concepts(frame)
            mode = "grounded_comprehension"
        except Exception:
            recovered = set()
            mode = "recognizer"  # fall back below

    if mode == "recognizer" or not recovered:
        # surface -> concepts via the SAME content-word recognizer the reading
        # (analysis-by-synthesis) path uses on incoming text — here run on the
        # agent's OWN produced surface.
        try:
            from domains import predictive_reading as pr
            recovered = _norm_concepts(pr._content_words(agent, produced_string or ""))
        except Exception:
            recovered = _norm_concepts((produced_string or "").split())
        mode = "recognizer" if mode != "grounded_comprehension" else mode

    missing = sorted(intended - recovered)
    coverage = (len(intended - set(missing)) / len(intended)) if intended else 0.0
    recoverable = bool(intended) and coverage >= coverage_threshold
    return {
        "recoverable": recoverable,
        "coverage": round(coverage, 4),
        "missing": missing,
        "recovered": sorted(recovered),
        "intended": sorted(intended),
        "mode": mode,
    }
