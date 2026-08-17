#!/usr/bin/env python3
"""BUILDER for seeds/core_emotions.json (seed block 204000).

Emits a graph-data seed manifest — the CORE-EMOTION SET as APPRAISAL -> ACTION-
TENDENCY rules over the EXISTING signal economy. This is a pure seed BUILDER
(admissible: emits graph data, no agent decision, no Rust). Every emotion is a
RULE; every op is integer-native and already in the DSL (term.rs diff EMPTY).

The atoms REUSED (same Term structure, verbatim):
  * 196000 staleness_decay:  freshness = Ashr(c0, IDiv(now - last_refresh, half_life))
                             (the scale2 half-life decay) + the 199000 present
                             readout (freshness >= t_present) -> whether a threat
                             precision DECAYS (fear) or WON'T (anxiety).
  * 202000 learning_progress: learning_progress = residual_prev - residual
                             (integer backward-difference) -> curiosity / boredom.
  * 202000 commit-net value:  value = V_max - Ashr(V_max, step) (diminishing
                             returns) -> joy's value_progress; the scale2 decay
                             Ashr(v0, k) -> sadness's un-re-groundable loss.

Run:  python3 scripts/build_core_emotions_seed.py   (writes seeds/core_emotions.json)
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "core_emotions.json")


# ---------------------------------------------------------------- Term helpers
def A(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def L(v):
    return {"type": "Lit", "value": float(v)}


def Eq(a, b):   return {"type": "Eq", "a": a, "b": b}
def Gt(a, b):   return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):   return {"type": "Lt", "a": a, "b": b}
def Gte(a, b):  return {"type": "Gte", "a": a, "b": b}
def And(*it):   return {"type": "And", "items": list(it)}
def Or(*it):    return {"type": "Or", "items": list(it)}
def Not(x):     return {"type": "Not", "arg": x}
def Plus(*it):  return {"type": "Plus", "items": list(it)}
def Minus(a, b):return {"type": "Minus", "a": a, "b": b}
def Times(*it): return {"type": "Times", "items": list(it)}
def IDiv(a, b): return {"type": "IDiv", "a": a, "b": b}
def Ashr(a, b): return {"type": "Ashr", "a": a, "b": b}
def Abs(x):     return {"type": "Abs", "arg": x}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": "hard_realtime",
            "match": match, "where": where,
            "effects": [[e[0], e[1], e[2], {"__term__": e[3]}] for e in effects]}


HUB_EP = ["hub", "has_emotion_params", "ep"]
HUB_AP = ["hub", "has_appraisal", "ap"]
ENABLED = Eq(A("ep", "enabled"), L(1))


def m():
    return [list(HUB_EP), list(HUB_AP)]


# ------------------------------------------------------------ signal-economy helpers
helpers = [
    # PRECISION / FRESHNESS on a threat — the 196000 scale2 atom, verbatim shape.
    rule("em_threat_precision", 0, m(),
         And(ENABLED, Eq(A("ap", "threat"), L(1))),
         [("set_attr", "ap", "threat_precision",
           Ashr(A("ap", "threat_c0"),
                IDiv(Minus(A("ap", "threat_now_epoch"), A("ap", "threat_last_refresh")),
                     A("ap", "threat_half_life"))))]),
    # PRESENT / PERSISTS readout — the 199000 freshness>=t_present decision, verbatim.
    rule("em_threat_persist", 1, m(),
         And(ENABLED, Eq(A("ap", "threat"), L(1))),
         [("set_attr", "ap", "threat_persists",
           Ite(Gte(A("ap", "threat_precision"), A("ap", "t_present")), L(1), L(0)))]),
    # LEARNING PROGRESS — the 202000 integer backward-difference, verbatim.
    rule("em_learning_progress", 0, m(), ENABLED,
         [("set_attr", "ap", "learning_progress",
           Minus(A("ap", "residual_prev"), A("ap", "residual")))]),
    # JOY value_progress — the 202000 diminishing-returns value atom delta:
    #   value = V_max - Ashr(V_max, step);  d(value) = Ashr(V_max,step_prev) - Ashr(V_max,step) > 0 as step rises.
    rule("em_joy_progress", 0, m(),
         And(ENABLED, Eq(A("ap", "valued_goal"), L(1)), Eq(A("ap", "goal_blocked"), L(0))),
         [("set_attr", "ap", "value_progress",
           Minus(Ashr(A("ap", "v_max"), A("ap", "step_prev")),
                 Ashr(A("ap", "v_max"), A("ap", "step"))))]),
    # SADNESS value_progress — a decaying, un-re-groundable attachment: the scale2
    #   decay atom Ashr(v0,k); d(value) = Ashr(v0,k_now) - Ashr(v0,k_prev) < 0 as k rises.
    rule("em_loss_progress", 0, m(),
         And(ENABLED, Eq(A("ap", "attachment"), L(1)), Eq(A("ap", "regroundable"), L(0))),
         [("set_attr", "ap", "value_progress",
           Minus(Ashr(A("ap", "attach_v0"), A("ap", "attach_k_now")),
                 Ashr(A("ap", "attach_v0"), A("ap", "attach_k_prev"))))]),
    # INDIVIDUAL HAPPINESS (individual reference frame) + mood_bias knob.
    rule("em_happiness", 2, m(), ENABLED,
         [("set_attr", "ap", "happiness",
           Plus(Minus(A("ap", "individual_benefit"), A("ap", "individual_cost")),
                A("ep", "mood_bias")))]),
    # WEIGHTED CONTRIBUTION: w_supergraph genuinely WEIGHTS contribution, not just
    #   gates its sign. w_supergraph_q/w_scale_bits are the INTEGER LATTICE
    #   rendering of the continuous [0,1] trait (domains/core_emotions_weight.py,
    #   computed once at each consumer's HeldEmotionParams construction site --
    #   CLAUDE.md's BASE-AS-DIMENSION: in-frame is integer, the continuum lives
    #   in the map that produces the step, never in the frame). Fixed-point
    #   Times+Ashr: at w=1.0 (the reference weight, w_supergraph_q == 2**B),
    #   this recovers contribution EXACTLY (Ashr undoes Times by the same B);
    #   at w=0, this is exactly 0 -- both endpoints byte-identical to the old
    #   sign gate. ATTENUATION-ONLY above w=1.0 (quantize_weight clamps), so
    #   every existing consumer (w in {0} u [1,inf), see
    #   SUPERGRAPH_WEIGHT_MAGNITUDE_PREREG.md sec0) is unaffected; only w in
    #   (0,1) -- previously indistinguishable from w=1 -- now genuinely varies.
    #   CORRECTED (design-review + user steering, phase A): was
    #   IfThenElse(Gt(w,0), contribution, 0) -- a SIGN GATE that discarded
    #   magnitude for ~99.4% of a drawn bigville population.
    rule("em_weighted_contribution", 1, m(), ENABLED,
         [("set_attr", "ap", "weighted_contribution",
           Ashr(Times(A("ep", "w_supergraph_q"), A("ap", "supergraph_contribution")),
                A("ep", "w_scale_bits")))]),
    rule("em_fulfilment_value", 2, m(), ENABLED,
         [("set_attr", "ap", "fulfilment_value",
           Plus(A("ap", "weighted_contribution"), A("ep", "mood_bias")))]),
    # TOTAL VALUE + ENDORSE — the somatic-marker decision bias: an act is endorsed
    #   iff individual+supergraph value >= 0. A healthy agent DECLINES a supergraph-
    #   harmful act; w_supergraph~0 removes the brake (instrumentalising).
    rule("em_total_value", 3, m(), ENABLED,
         [("set_attr", "ap", "total_value",
           Plus(A("ap", "happiness"), A("ap", "fulfilment_value")))]),
    rule("em_endorse", 4, m(), ENABLED,
         [("set_attr", "ap", "act_endorsed",
           Ite(Gte(A("ap", "total_value"), L(0)), L(1), L(0)))]),
]


# ------------------------------------------------------------------- the emotion rules
def hit(name):
    return [("set_attr", "ap", "hit_" + name, L(1))]


emotion_rules = [
    # surprise — the raw residual spike, NOT yet appraised (pre-appraisal orienting).
    rule("em_surprise", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(0)),
             Gt(A("ap", "residual"), A("ep", "residual_thresh"))),
         hit("surprise")),
    # fear [individual survival] — threat precision that DECAYS (short horizon).
    rule("em_fear", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Eq(A("ap", "threat"), L(1)), Eq(A("ap", "threat_persists"), L(0))),
         hit("fear")),
    # anxiety [individual] — threat precision that WON'T decay (sustained vigilance).
    rule("em_anxiety", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Eq(A("ap", "threat"), L(1)), Eq(A("ap", "threat_persists"), L(1))),
         hit("anxiety")),
    # anger [individual] — blocked VALUED goal + an approachable blocker.
    rule("em_anger", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Eq(A("ap", "valued_goal"), L(1)), Eq(A("ap", "goal_blocked"), L(1)),
             Eq(A("ap", "blocker_present"), L(1))),
         hit("anger")),
    # frustration [individual] — blocked VALUED goal, NO approachable blocker, still engaged.
    rule("em_frustration", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Eq(A("ap", "valued_goal"), L(1)), Eq(A("ap", "goal_blocked"), L(1)),
             Eq(A("ap", "blocker_present"), L(0))),
         hit("frustration")),
    # disgust [individual] — contamination / violation.
    rule("em_disgust", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)), Eq(A("ap", "contamination"), L(1))),
         hit("disgust")),
    # joy [individual progress] — value-progress > 0 on an unblocked valued outcome.
    rule("em_joy", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Eq(A("ap", "valued_goal"), L(1)), Eq(A("ap", "goal_blocked"), L(0)),
             Gt(A("ap", "value_progress"), L(0))),
         hit("joy")),
    # sadness / grief [individual] — un-re-groundable attachment, value falling.
    rule("em_sadness", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Eq(A("ap", "attachment"), L(1)), Eq(A("ap", "regroundable"), L(0)),
             Lt(A("ap", "value_progress"), L(0))),
         hit("sadness")),
    # curiosity [individual progress] — learning-progress > 0 (the 202000 signal).
    rule("em_curiosity", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Gt(A("ap", "learning_progress"), L(0))),
         hit("curiosity")),
    # boredom [individual] — learning-progress -> 0 while engaged (the 202000 cut).
    rule("em_boredom", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Eq(A("ap", "learning_progress"), L(0)), Eq(A("ap", "was_engaged"), L(1))),
         hit("boredom")),
    # fulfilment [SUPERGRAPH] — the agent's action increased the COLLECTIVE's success,
    #   and the agent VALUES the supergraph (w_supergraph > 0). Deep, low-hedonic.
    # Both gates read weighted_contribution (em_weighted_contribution, order 1,
    #   already settled) instead of the raw contribution+sign-gate conjunction --
    #   Gt(weighted,0) == Gt(contribution,0) AND Gt(w,0) exactly for every w in
    #   {0} u [1,inf) (SUPERGRAPH_WEIGHT_MAGNITUDE_PREREG.md sec0/sec2), so this
    #   is byte-identical everywhere except bigville's continuous w in (0,1),
    #   where a small-w resident's tiny weighted_contribution can now floor to
    #   0 and correctly NOT fire -- a truncation artifact of the lattice
    #   resolution, not a designed threshold (documented, not hidden).
    rule("em_fulfilment", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Gt(A("ap", "weighted_contribution"), L(0)),
             Gt(A("ap", "collective_success"), A("ap", "collective_success_prev"))),
         hit("fulfilment")),
    # pride [SOCIAL frame] — supergraph contribution ATTRIBUTED to self AND observed
    #   by another (minimal self+other model). Co-occurs with fulfilment by design
    #   (both supergraph-frame); presented OUTSIDE the G1 confusion matrix.
    rule("em_pride", 5, m(),
         And(ENABLED, Eq(A("ap", "appraised"), L(1)),
             Gt(A("ap", "weighted_contribution"), L(0)),
             Eq(A("ap", "contribution_by_self"), L(1)),
             Eq(A("ap", "observed_by_other"), L(1))),
         hit("pride")),
]

CORE = ["surprise", "fear", "anxiety", "anger", "frustration", "disgust",
        "joy", "sadness", "curiosity", "boredom", "fulfilment"]
TEND = {"surprise": 1, "fear": 2, "anxiety": 3, "anger": 4, "frustration": 5,
        "disgust": 6, "joy": 7, "sadness": 8, "curiosity": 9, "boredom": 10,
        "fulfilment": 11}


# --------------------------------------------------------------------- read-off (mux)
def tend_mux():
    expr = L(0)
    for nm in reversed(CORE):
        expr = Ite(Eq(A("ap", "hit_" + nm), L(1)), L(TEND[nm]), expr)
    return expr


def valence_mux():
    pos = Or(Eq(A("ap", "hit_joy"), L(1)), Eq(A("ap", "hit_curiosity"), L(1)),
             Eq(A("ap", "hit_fulfilment"), L(1)))
    return Ite(Eq(A("ap", "n_fired"), L(0)), L(0),
               Ite(Eq(A("ap", "hit_surprise"), L(1)), L(0),
                   Ite(pos, L(1), L(-1))))


def arousal_mux():
    return Ite(Eq(A("ap", "hit_surprise"), L(1)), A("ap", "residual"),
           Ite(Or(Eq(A("ap", "hit_fear"), L(1)), Eq(A("ap", "hit_anxiety"), L(1))),
               A("ap", "threat_precision"),
           Ite(Eq(A("ap", "hit_curiosity"), L(1)), A("ap", "learning_progress"),
           Ite(Eq(A("ap", "hit_joy"), L(1)), A("ap", "value_progress"),
           Ite(Eq(A("ap", "hit_fulfilment"), L(1)), Abs(A("ap", "weighted_contribution")),
           Ite(Or(Eq(A("ap", "hit_anger"), L(1)), Eq(A("ap", "hit_frustration"), L(1))),
               A("ep", "high_arousal"),
           Ite(Eq(A("ap", "hit_disgust"), L(1)), A("ep", "mid_arousal"),
               A("ep", "low_arousal"))))))))


readoff = [
    rule("em_nfired", 8, m(), ENABLED,
         [("set_attr", "ap", "n_fired",
           Plus(*[A("ap", "hit_" + nm) for nm in CORE]))]),
    rule("em_readoff", 9, m(), ENABLED,
         [("set_attr", "ap", "action_tendency", tend_mux()),
          ("set_attr", "ap", "emotion", tend_mux()),
          ("set_attr", "ap", "valence", valence_mux()),
          ("set_attr", "ap", "arousal", arousal_mux())]),
]


PRODUCTIONS = [
    {"provenance": "seed:core_emotions:hub-params",
     "src": {"type": "EmotionHub", "var": "hub"},
     "edge_type": "has_emotion_params",
     "tgt": {"type": "HeldEmotionParams", "var": "ep"}},
    {"provenance": "seed:core_emotions:hub-appraisal",
     "src": {"type": "EmotionHub", "var": "hub"},
     "edge_type": "has_appraisal",
     "tgt": {"type": "Appraisal", "var": "ap"}},
    {"provenance": "seed:core_emotions:agent-supergraph",
     "src": {"type": "EmotionHub", "var": "hub"},
     "edge_type": "member_of",
     "tgt": {"type": "Supergraph", "var": "sg"}},
]


MANIFEST = {
    "id": "core_emotions",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": [],
    "area": "retina",
    "description": (
        "THE CORE-EMOTION SET (block 204000) as APPRAISAL -> ACTION-TENDENCY "
        "rules over the EXISTING signal economy -- NOT a new module. Each emotion "
        "is a RULE reading the same integer atoms already in the tree: the 196000 "
        "staleness_decay freshness = Ashr(c0, IDiv(now-last_refresh, half_life)) "
        "(scale2 half-life) + the 199000 present readout (freshness>=t_present) "
        "-> a threat precision that DECAYS is FEAR, one that WON'T is ANXIETY "
        "(the same PTSD knob, appraised as emotion); the 202000 learning_progress "
        "= residual_prev - residual -> CURIOSITY(>0)/BOREDOM(->0) (the noisy-TV "
        "cut); the 202000 diminishing-returns value = V_max - Ashr(V_max, step) "
        "-> JOY's value_progress, and the scale2 decay Ashr(v0,k) -> SADNESS's "
        "un-re-groundable loss. Appraisal theory (Scherer/Lazarus/Frijda action "
        "tendencies); the circumplex (valence=sign of progress/value, "
        "arousal=magnitude of surprise/precision) read off in-graph. THE "
        "REFERENCE-FRAME-PER-EMOTION PRINCIPLE: each emotion's value function "
        "reads value at a LEVEL OF SELECTION -- the individual emotions read the "
        "individual ledger (happiness = benefit-cost); FULFILMENT reads the "
        "SUPERGRAPH (w_supergraph gates the contribution term), fires when the agent's action "
        "raised the COLLECTIVE's success, and is DISTINCT from joy. G4 value-side "
        "disorder glass-box (ties 199000): PSYCHOPATHY = the w_supergraph knob at "
        "~0 (reads others -- contribution still computed -- but does not VALUE "
        "them -> fulfilment collapses, the somatic brake on supergraph-harmful "
        "acts is removed); pure-knob reversal restores it. mood_bias suppresses "
        "(depression) / inflates (mania) value across BOTH frames. The behavioural "
        "factors are SHADOWS of the state-knobs. Integer-native "
        "(Ashr/IDiv/Minus/Plus/Abs/IfThenElse/Eq/Gt/Lt/Gte/And/Or/Not only); "
        "NO Rust, NO new Term. OFF by default: every rule guards on a "
        "HeldEmotionParams.enabled node the measure adapter creates only on "
        "opt-in; absent it every existing path is byte-identical. Understanding "
        "not judgment; the FUNCTIONAL regulator, NOT a claim to felt qualia."),
    "microtheory": {
        "name": "core_emotions",
        "description": (
            "An emotion is an appraisal of the signal economy that produces an "
            "action tendency; its value function reads a level of selection "
            "(individual vs supergraph). Same integer decay/progress/value atoms "
            "as perception/curiosity; fulfilment is the supergraph frame, "
            "psychopathy the supergraph-value knob at zero.")},
    "nodes": [],
    "edges": [],
    "productions": PRODUCTIONS,
    "rules": helpers + emotion_rules + readoff,
}


def main():
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print("wrote", OUT, "-", len(MANIFEST["rules"]), "rules,",
          len(MANIFEST["productions"]), "productions")


if __name__ == "__main__":
    main()
