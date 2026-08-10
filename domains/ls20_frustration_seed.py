"""ls20_frustration_seed — BLOCK 226000: FUTILE repetition triggers FRUSTRATION
-> STOP, the PSI regress-breaker (Dörner/Bach) wired to the 221000 understanding
signal. Frustration is the emotional COMPLEMENT to curiosity: understanding
rewards compression, frustration PUNISHES futile repetition.

This is a SEED BUILDER (emits graph data — the allowed Python under the
architecture rule, exactly like ls20_understanding_seed.py / the 215000 grievance
seed). Every DECISION is a rule `where`-clause over graph state. The host adapter
(domains/frustration_world.py) only ADDS immutable Step nodes carrying RAW
per-step observables, advances now_epoch, and READS frustration/break_now — NO
Python agent decision, NO `if repeated: stop`.

THE DISCRIMINATOR IS THE WHOLE POINT (not a repeat-counter). A step is FUTILE iff
it RECURS (a graph MATCH over the step history) AND yields NO understanding-gain
(d_hyp==0 AND d_state==0 AND s_drop==0 — the three RAW observables the adapter
stamps, exactly as the 208000 narration adapter stamps ev_*). A PRODUCTIVE repeat
(a gain observable set) is NOT marked futile -> frustration stays flat. That is
the teeth: a plain repeat-counter would fire on any recurrence and fail the
productive-repetition control.

THE ACCUMULATOR is the 215000 gs_grievance_from_slights pattern verbatim in
shape: a LEAKY scale2 (Ashr, x2^-k) decayed Sum over FUTILE steps only. THE
BREAK is a rule reading the modulator cross a threshold -> STOP. THE NARRATION is
the 208000 template lexicon keyed by emotion_code.

Integer-native; NO Rust; every Term pre-existing (Sum/Ashr/IDiv/Times/Plus/Minus/
Max/Eq/Gt/Gte/Lt/And/Not/Exists/Attr/Lit). self_load_only, depends_on []:
default-OFF and byte-identical when absent (skipped by load_all_seeds; nothing
depends_on it; every rule guards on HeldFrustrationParams.enabled==1).
"""
from __future__ import annotations

import json
from pathlib import Path


# ---- Term-tree helpers (graph data emitters) ------------------------------
def V(name):
    return {"type": "Var", "name": name}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def L(x):
    return {"type": "Lit", "value": x}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def GTE(a, b):
    return {"type": "Gte", "a": a, "b": b}


def LT(a, b):
    return {"type": "Lt", "a": a, "b": b}


def AND(*items):
    return {"type": "And", "items": list(items)}


def NOT(arg):
    return {"type": "Not", "arg": arg}


def _enabled(gp="gp"):
    return EQ(A(gp, "enabled"), L(1.0))


def build_rules():
    # 1. fr_mark_futile — THE DISCRIMINATOR. Recurrence (a MATCH over the step
    #    history via Exists) AND no-gain (the three raw observables) -> futile.
    fr_mark_futile = {
        "name": "fr_mark_futile",
        "area": "retina",
        "order": 0,
        "latency_class": "hard_realtime",
        "comment": (
            "A step is FUTILE iff it RECURS (Exists an earlier has_step Step with "
            "the same sig) AND yields NO understanding-gain (d_hyp==0 AND "
            "d_state==0 AND s_drop==0). Recurrence is a graph match; no-gain is "
            "the three raw observables the adapter stamps. A PRODUCTIVE repeat has "
            "a gain observable set -> this rule does NOT fire -> not futile. THE "
            "TEETH: a plain repeat-counter would fire on any recurrence."),
        "match": [
            ["hub", "has_frustration_params", "gp"],
            ["hub", "has_frustration", "m"],
            ["m", "has_step", "st"],
        ],
        "where": AND(
            _enabled(),
            EQ(A("st", "d_hyp"), L(0.0)),
            EQ(A("st", "d_state"), L(0.0)),
            EQ(A("st", "s_drop"), L(0.0)),
            {
                "type": "Exists",
                "source": {"type": "Neighbours", "node": V("m"),
                           "edge_type": "has_step", "any_type": False},
                "var_name": "st2",
                "predicate": AND(
                    EQ(A("st2", "sig"), A("st", "sig")),
                    LT(A("st2", "epoch"), A("st", "epoch")),
                ),
            },
        ),
        "effects": [["set_attr", "st", "futile", 1.0]],
    }

    # 2. fr_accumulate — the LEAKY scale2 accumulator (215000 pattern). Only
    #    futile steps contribute (Times by st.futile in {0,1}); older futile
    #    events decay via Ashr. Productive repetition -> every futile==0 -> 0.
    accum_term = {
        "type": "Sum",
        "source": {"type": "Neighbours", "node": V("m"),
                   "edge_type": "has_step", "any_type": False},
        "var_name": "st",
        "value": {
            "type": "Times",
            "items": [
                A("st", "futile"),
                {
                    "type": "Ashr",
                    "a": A("gp", "frust_unit"),
                    "b": {
                        "type": "IDiv",
                        "a": {"type": "Minus",
                              "a": A("m", "now_epoch"),
                              "b": A("st", "epoch")},
                        "b": {"type": "Max",
                              "items": [L(1.0), A("gp", "half_life")]},
                    },
                },
            ],
        },
    }
    fr_accumulate = {
        "name": "fr_accumulate",
        "area": "retina",
        "order": 1,
        "latency_class": "hard_realtime",
        "comment": (
            "frustration = Sum over has_step of Times(futile, Ashr(frust_unit, "
            "age/half_life)) -- the 215000 gs_grievance_from_slights leaky scale2 "
            "accumulator, restricted to FUTILE steps. Idempotent (pure function of "
            "immutable Step facts + adapter-advanced now_epoch)."),
        "match": [
            ["hub", "has_frustration_params", "gp"],
            ["hub", "has_frustration", "m"],
        ],
        "where": _enabled(),
        "effects": [["set_attr", "m", "frustration", {"__term__": accum_term}]],
    }

    # 3. fr_break — THE REGRESS-BREAK. frustration >= threshold -> STOP. The
    #    emotion converts "futile" into "stop"; the decision is THIS RULE reading
    #    the modulator, never Python.
    fr_break = {
        "name": "fr_break",
        "area": "retina",
        "order": 2,
        "latency_class": "hard_realtime",
        "comment": (
            "The emotional STOP: frustration crossing frustration_thresh sets "
            "break_now/hit_frustration/action_tendency=STOP/emotion_code=1. The "
            "adapter mechanically reads break_now and stops the loop. NO Python "
            "decides the stop -- this rule does."),
        "match": [
            ["hub", "has_frustration_params", "gp"],
            ["hub", "has_frustration", "m"],
        ],
        "where": AND(
            _enabled(),
            GTE(A("m", "frustration"), A("gp", "frustration_thresh")),
        ),
        "effects": [
            ["set_attr", "m", "break_now", 1.0],
            ["set_attr", "m", "hit_frustration", 1.0],
            ["set_attr", "m", "action_tendency", "STOP"],
            ["set_attr", "m", "emotion_code", 1.0],
        ],
    }

    return [fr_mark_futile, fr_accumulate, fr_break]


def manifest():
    return {
        "id": "ls20_frustration",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": [],
        "area": "retina",
        "description": (
            "FRUSTRATION as the PSI REGRESS-BREAKER (block 226000): futile "
            "repetition -- repetition WITHOUT understanding-gain -- raises a "
            "leaky scale2-decayed frustration modulator that, past a threshold, "
            "BREAKS the loop (STOP). Frustration is the emotional COMPLEMENT to "
            "the 221000 understanding drive (understanding rewards compression; "
            "frustration punishes futile repetition). THE DISCRIMINATOR: a step "
            "is FUTILE iff it RECURS (an Exists MATCH over the has_step history) "
            "AND yields no gain (d_hyp==0 AND d_state==0 AND s_drop==0 -- the raw "
            "observables the adapter stamps, the 208000 ev_* pattern); a "
            "PRODUCTIVE repeat is NOT marked futile so frustration stays flat -- "
            "NOT a repeat-counter. fr_mark_futile marks it; fr_accumulate is the "
            "215000 gs_grievance_from_slights leaky Sum(Times(futile, Ashr(unit, "
            "age/half_life))); fr_break reads the modulator across the threshold "
            "and sets break_now=STOP. Integer-native, NO Rust, NO new Term. "
            "self_load_only + depends_on [] + every rule guarded on "
            "HeldFrustrationParams.enabled==1: default-OFF and byte-identical "
            "when absent."),
        "microtheory": {
            "name": "ls20_frustration",
            "description": (
                "Frustration is a leaky accumulator of FUTILE-repeat events "
                "(recurrence with no understanding-gain); crossing a threshold it "
                "breaks the current strategy (stop/switch). It is the emotional "
                "regress-breaker -- the complement of curiosity: the same "
                "understanding signal that rewards compression, read with the "
                "opposite sign on futile repetition."),
        },
        "nodes": [
            {
                "local_id": 1,
                "type": "FrustrationNarration",
                "attrs": {
                    "code": 1.0,
                    "emotion_name": "frustration",
                    "tendency": "STOP",
                    "template": ("Same thing over and over, no progress — "
                                 "this is frustrating. Stop and try something "
                                 "else."),
                },
            }
        ],
        "edges": [],
        "productions": [
            {
                "provenance": "seed:ls20_frustration:fparams",
                "src": {"type": "EmotionHub", "var": "hub"},
                "edge_type": "has_frustration_params",
                "tgt": {"type": "HeldFrustrationParams", "var": "fp"},
            },
            {
                "provenance": "seed:ls20_frustration:modulator",
                "src": {"type": "EmotionHub", "var": "hub"},
                "edge_type": "has_frustration",
                "tgt": {"type": "FrustrationModulator", "var": "m"},
            },
            {
                "provenance": "seed:ls20_frustration:step",
                "src": {"type": "FrustrationModulator", "var": "m"},
                "edge_type": "has_step",
                "tgt": {"type": "Step", "var": "st"},
            },
        ],
        "rules": build_rules(),
    }


def write_seed(path=None):
    p = (Path(path) if path else
         Path(__file__).resolve().parent.parent / "seeds" / "ls20_frustration.json")
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
