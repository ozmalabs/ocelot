#!/usr/bin/env python3
"""Emit seeds/blink_bridge.json — THE BLINK: a temporal hole bridged by grounding.

The temporal twin of the blind spot (`vision_ground`) and the COMPOSITION of the
grounded-field fill with `TimeInfer`'s transition generator. A blink is a run of
frames with NO visual input; its belief is the pre-blink generator `G` CONTINUED
through the gap (`G^t(f0)`), NOT the frozen last frame (persistence) and NOT an
invented value (confabulation).

CONFABULATE BY DEFAULT (the creator's correction). Perception FILLS the temporal
hole with a best-guess; grounding only CONSTRAINS that guess — there is NO "hold
open". One rule, the fill always fires; grounding decides only how CONSTRAINED and
CONFIDENT the guess is (PROTOCOL §0, the decision is graph data):
  * `blink_bridge_fill` — on a blink sequence, ALWAYS confabulate a continuation.
    A CONSISTENT motion (BlinkBridge.constrained==1) pins the guess to G^t(f0) at a
    confidence that FALLS OUT of support (confirm_run/(confirm_run+gap), RELATIVE);
    an ungrounded prefix (accelerating / shuffled) still fills, but with the freeze
    default at confidence 0 (UNCONSTRAINED — the seed of hallucination, NOT silence
    and NOT held-open). Writes the guess `bridged`, the persistence baseline
    `frozen`, the resume-divergence tick `diverged_at` (change blindness) and the
    correction magnitude `correction` (the perceptible jump on data return).

Flag `blink_bridge_enabled` on the agent, OFF by default (§9): the rule matches
only status=='blink_seq', which the normal decode ladder never produces, and fires
nothing at the defaults. Run:  python tools/build_blink_bridge.py
"""
from __future__ import annotations
import json
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "seeds" / "blink_bridge.json"

FRAMES = {"type": "Attr", "node": {"type": "Var", "name": "obs"}, "key": "frames"}


def BB(field: str) -> dict:
    """A BlinkBridge Term reading `field` off the observation's frames."""
    return {"type": "BlinkBridge", "sequence": FRAMES,
            "codebook_type": "ShapeSignature", "max_b": 8, "field": field}


def lit(v):
    return {"type": "Lit", "value": v}


def attr(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


# --- shared where-clause atoms ---
IS_BLINK_SEQ = eq(attr("obs", "status"), lit("blink_seq"))
FLAG_ON = eq(attr("ag", "blink_bridge_enabled"), lit(1))
CONSTRAINED = eq(BB("constrained"), lit(True))

# constrained -> 1.0 else 0.0 (a numeric witness alongside the confidence float)
CONSTRAINED_I = {"type": "IfThenElse", "cond": CONSTRAINED, "then": lit(1.0), "other": lit(0.0)}

fill = {
    "name": "blink_bridge_fill",
    "comment": (
        "CONFABULATE BY DEFAULT. Flag ON (agent.blink_bridge_enabled==1). On a "
        "blink-sequence Observation (status=='blink_seq'), ALWAYS fill the temporal "
        "hole with a best-guess continuation -- perception does not go silent when "
        "ungrounded, it guesses (predictive coding: the prediction stands where "
        "there is no data). Grounding only CONSTRAINS the guess: a consistent "
        "motion (BlinkBridge.constrained==1) pins bridged to G^t(f0) at a "
        "confidence that FALLS OUT of support (confirm_run/(confirm_run+gap), "
        "RELATIVE, no constant); an ungrounded prefix (accelerating / shuffled) "
        "still fills, with the freeze default at confidence 0 -- UNCONSTRAINED, the "
        "seed of hallucination, NOT held-open and NOT silence. Writes the guess, "
        "the persistence baseline (frozen), the resume-divergence tick "
        "(diverged_at: -1 == invisible; >=0 == a change bridged over during the "
        "blink and revised on data return -> change blindness) and the correction "
        "magnitude (the perceptible 'jump'). status flips to 'blink_bridged'."),
    "match_type": "Observation",
    "match": [["ag", "observed", "obs"]],
    "where": {"type": "And", "items": [IS_BLINK_SEQ, FLAG_ON]},
    "effects": [
        ["set_attr", "obs", "bridged", {"__term__": BB("bridged")}],
        ["set_attr", "obs", "frozen", {"__term__": BB("frozen")}],
        ["set_attr", "obs", "diverged_at", {"__term__": BB("diverged_at")}],
        ["set_attr", "obs", "correction", {"__term__": BB("correction")}],
        ["set_attr", "obs", "confidence", {"__term__": BB("confidence")}],
        ["set_attr", "obs", "bridge_kind", {"__term__": BB("kind")}],
        ["set_attr", "obs", "bridge_gap", {"__term__": BB("gap")}],
        ["set_attr", "obs", "bridge_confirm", {"__term__": BB("confirm_run")}],
        ["set_attr", "obs", "bridge_prefix", {"__term__": BB("prefix_len")}],
        ["set_attr", "obs", "constrained", {"__term__": CONSTRAINED_I}],
        ["set_attr", "obs", "status", "blink_bridged"],
    ],
}

manifest = {
    "id": "blink_bridge",
    "version": "1.0.0",
    "depends_on": ["time_axis"],
    "description": (
        "THE BLINK -- a temporal hole bridged by grounding, the TEMPORAL TWIN of "
        "the blind spot (vision_ground) and the COMPOSITION of the grounded-field "
        "fill with TimeInfer's transition generator. Every few seconds the eyelid "
        "closes and there is NO visual input for ~100-400 ms, yet no shutter is "
        "experienced. A blink is a hole in the TEMPORAL orbit "
        "(f0,f1,[BLINK],f4,f5); it is bridged by CONTINUING the transition "
        "generator G that carries frame(t)->frame(t+1): the belief during blink "
        "tick t is CONFABULATED as a best-guess. Perception FILLS the hole by "
        "default (predictive coding: the prediction stands where there is no data "
        "-- that IS change blindness; an ungrounded fill IS hallucination, not "
        "silence). Grounding only CONSTRAINS the guess: consistent motion pins it "
        "to G^t(f0) at high confidence (invisible); an ungrounded prefix still "
        "fills, with the freeze default at confidence 0 (UNCONSTRAINED). When data "
        "RESUMES the guess is CONFIRMED (invisible) or REVISED where reality "
        "diverges (the perceptible 'jump'). The Rust BlinkBridge Term supplies the "
        "generator+continuation (reusing TimeInfer's infer/verify and "
        "apply_generator_k); the single fill rule always fires, grounding decides "
        "only constraint+confidence. Confidence is RELATIVE (confirm_run/"
        "(confirm_run+gap), the confirmed-transition support), never a fixed-K "
        "constant. In-frame/integer only (continuous motion is cross-frame, "
        "deferred -- the frame/continuum invariant). Flag-gated on "
        "agent.blink_bridge_enabled==1, OFF by default (PROTOCOL §9); inert without "
        "it AND matches only status=='blink_seq'."),
    "microtheory": {
        "name": "blink_bridge",
        "description": (
            "the eye CONFABULATES across a temporal hole; grounding constrains the "
            "guess. A blink's belief is a best-guess continuation -- pinned to the "
            "pre-blink transition generator (G^t(f0), high confidence, invisible) "
            "under consistent motion, or the unconstrained freeze default (low "
            "confidence, the seed of hallucination) without one. Motion-continuing "
            "(belief at G^k(last), not frozen) when grounded; change-blind (a "
            "change during the blink is missed until divergence, then corrected -- "
            "the perceptible jump). PERCEPTION is liberal (fill by default); "
            "DISCOVERY (time_axis minting) stays conservative. The same "
            "grounded-field operation as the blind spot, with the surround in TIME "
            "and the grounding the transition generator."),
    },
    "nodes": [],
    "edges": [],
    "productions": [
        {"provenance": "seed:blink_bridge:observed-0",
         "src": {"type": "Agent", "var": "s"}, "edge_type": "observed",
         "tgt": {"type": "Observation", "var": "t"}},
    ],
    "rules": [fill],
}


def main() -> None:
    SEED.write_text(json.dumps(manifest, indent=1))
    print(f"wrote {SEED}  ({SEED.stat().st_size} bytes, {len(manifest['rules'])} rules)")


if __name__ == "__main__":
    main()
