#!/usr/bin/env python3
"""WINDOW-AS-A-KNOB seed builder (block 241000).

Authoring tool ONLY: it EMITS `seeds/window_knob_coreg.json` (graph data) — no
agent decisions, no rule engine, no graph state. It writes the eleven graph
RULES that ride the REAL `AffectiveState.arousal` (affective_state_core) and
239000's `WindowOfTolerance` node, reusing the SAME `sd_blend` leaky-EMA pull
form (`x <- x + k·(target − x)`) as block 239000, extended to be BIDIRECTIONAL
(the infant's arousal pulls the caregiver's) and GATED (co-regulation engages
only while the caregiver is itself regulated). NO Rust, NO new Term — every Term
below (Plus/Times/Minus/Attr/Var/Lit/Eq/Gt/Lt/And/Or/Not) is already in 239000's
engine.

Run:  python scripts/window_knob_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "window_knob_coreg.json")


# ---- Term constructors (mechanical JSON shape, identical to 239000's) --------
def var(name):
    return {"type": "Var", "name": name}


def attr(node, key):
    return {"type": "Attr", "node": var(node), "key": key}


def lit(v):
    return {"type": "Lit", "value": float(v)}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def times(*items):
    return {"type": "Times", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def or_(*items):
    return {"type": "Or", "items": list(items)}


def not_(arg):
    return {"type": "Not", "arg": arg}


def term(t):
    """A Term used as an effect VALUE is wrapped in __term__ (239000 form)."""
    return {"__term__": t}


def leaky(node, gain_key, target_term):
    """The reused sd_blend leaky-EMA pull: node.arousal += gain·(target − arousal)."""
    a = attr(node, "arousal")
    return term(plus(a, times(attr(node, gain_key), minus(target_term, a))))


# outside/inside the tolerated band [lo, hi] of a WindowOfTolerance var `w`,
# for an arousal on AffectiveState var `s`.
def outside_window(s, w):
    return or_(gt(attr(s, "arousal"), attr(w, "hi")),
               lt(attr(s, "arousal"), attr(w, "lo")))


def inside_window(s, w):
    return and_(not_(gt(attr(s, "arousal"), attr(w, "hi"))),
                not_(lt(attr(s, "arousal"), attr(w, "lo"))))


def epoch_open(s, guard_key):
    """A leaky-pull epoch guard — fire once per tick (239000 pattern)."""
    return lt(attr(s, guard_key), attr(s, "tick_epoch"))


def is_infant(s="iaff"):
    """Scope an infant rule to the INFANT's affect. In a BIDIRECTIONAL dyad BOTH
    agents carry an AffectiveState + a WindowOfTolerance, so a rule matched only
    on has_affective_state / has_window would ALSO fire on the caregiver's nodes
    (unlike 239000, where only the infant had a window). This discriminator
    (is_infant==1) keeps the infant rules on the infant."""
    return eq(attr(s, "is_infant"), lit(1.0))


def set_epoch(s, guard_key):
    return ["set_attr", s, guard_key, term(attr(s, "tick_epoch"))]


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# ---------------------------------------------------------------- the rules ---
RULES = [
    # R1 — a stressor pushes the infant's REAL arousal (reused 239000 form).
    rule("wk_arousal_stressor_push", 2,
         [["infant", "has_affective_state", "iaff"],
          ["infant", "has_stressor", "sx"]],
         and_(is_infant(), eq(attr("sx", "armed"), lit(1.0))),
         [["set_attr", "iaff", "arousal",
           term(plus(attr("iaff", "arousal"), attr("sx", "magnitude")))],
          ["set_attr", "sx", "armed", 0.0]]),

    # R2 — hyperarousal onset: arousal ABOVE the window's hi (width = hi−lo).
    rule("wk_infant_dysreg_onset_hyper", 3,
         [["infant", "has_affective_state", "iaff"],
          ["infant", "has_window", "wot"]],
         and_(is_infant(), eq(attr("iaff", "in_episode"), lit(0.0)),
              gt(attr("iaff", "arousal"), attr("wot", "hi"))),
         [["set_attr", "iaff", "dysregulated", 1.0],
          ["set_attr", "iaff", "dysreg_kind", 1.0],
          ["set_attr", "iaff", "in_episode", 1.0]]),

    # R3 — hypoarousal onset: arousal BELOW the window's lo.
    rule("wk_infant_dysreg_onset_hypo", 3,
         [["infant", "has_affective_state", "iaff"],
          ["infant", "has_window", "wot"]],
         and_(is_infant(), eq(attr("iaff", "in_episode"), lit(0.0)),
              lt(attr("iaff", "arousal"), attr("wot", "lo"))),
         [["set_attr", "iaff", "dysregulated", 1.0],
          ["set_attr", "iaff", "dysreg_kind", -1.0],
          ["set_attr", "iaff", "in_episode", 1.0]]),

    # R4 — caregiver re-regulates when its OWN arousal is back in its window.
    #      (order 3: checked BEFORE the pull, so a recovered caregiver resumes.)
    #      NB: the written node (caff) is bound FIRST — the engine applies
    #      set_attr to the first-bound match node (as 239000's coreg_pull does).
    rule("wk_caregiver_reregulate", 3,
         [["cg", "has_affective_state", "caff"],
          ["cg", "has_window", "cgwot"],
          ["infant", "attended_by", "cg"]],
         and_(eq(attr("caff", "regulated"), lit(0.0)),
              inside_window("caff", "cgwot")),
         [["set_attr", "caff", "regulated", 1.0],
          ["set_attr", "caff", "dysregulated", 0.0],
          ["set_attr", "caff", "dysreg_kind", 0.0]]),

    # R5 — BIDIRECTIONAL: the infant's arousal PULLS the caregiver's (mutual
    #      entrainment). Reused sd_blend leaky-EMA pull toward the infant.
    rule("wk_caregiver_pull_by_infant", 4,
         [["cg", "has_affective_state", "caff"],
          ["infant", "attended_by", "cg"],
          ["infant", "has_affective_state", "iaff"]],
         epoch_open("caff", "cp_epoch"),
         [["set_attr", "caff", "arousal",
           leaky("caff", "k_cg", attr("iaff", "arousal"))],
          set_epoch("caff", "cp_epoch")]),

    # R6 — a REGULATED caregiver self-regulates toward its setpoint (the anchor
    #      a WIDE window preserves; a NARROW one loses when it dysregulates).
    rule("wk_caregiver_selfreg_pull", 5,
         [["cg", "has_affective_state", "caff"],
          ["infant", "attended_by", "cg"]],
         and_(epoch_open("caff", "cs_epoch"),
              eq(attr("caff", "regulated"), lit(1.0))),
         [["set_attr", "caff", "arousal",
           leaky("caff", "k_cg_self", attr("caff", "setpoint"))],
          set_epoch("caff", "cs_epoch")]),

    # R7 — CO-DYSREGULATION onset: the caregiver's OWN arousal left its OWN
    #      window → it stops being regulated (co-regulation capacity lost).
    #      Narrow window ⇒ this fires on tick 1, BEFORE the infant's coreg pull.
    rule("wk_caregiver_dysreg_onset", 6,
         [["cg", "has_affective_state", "caff"],
          ["cg", "has_window", "cgwot"],
          ["infant", "attended_by", "cg"]],
         and_(eq(attr("caff", "regulated"), lit(1.0)),
              outside_window("caff", "cgwot")),
         [["set_attr", "caff", "regulated", 0.0],
          ["set_attr", "caff", "dysregulated", 1.0],
          ["set_attr", "caff", "dysreg_kind", 1.0]]),

    # R8 — co-regulation pull: the infant's arousal is entrained toward the
    #      caregiver's — GATED on the caregiver being regulated. Reused pull.
    rule("wk_infant_coreg_pull", 7,
         [["infant", "has_affective_state", "iaff"],
          ["infant", "attended_by", "cg"],
          ["cg", "has_affective_state", "caff"]],
         and_(is_infant(), epoch_open("iaff", "cr_epoch"),
              eq(attr("caff", "regulated"), lit(1.0))),
         [["set_attr", "iaff", "arousal",
           leaky("iaff", "k_co", attr("caff", "arousal"))],
          set_epoch("iaff", "cr_epoch")]),

    # R9 — self-regulation: the infant's arousal leaks toward its setpoint.
    rule("wk_infant_selfreg_pull", 8,
         [["infant", "has_affective_state", "iaff"]],
         and_(is_infant(), epoch_open("iaff", "sr_epoch")),
         [["set_attr", "iaff", "arousal",
           leaky("iaff", "k_self", attr("iaff", "setpoint"))],
          set_epoch("iaff", "sr_epoch")]),

    # R10 — return to the window: arousal back inside [lo,hi] ⇒ no longer
    #       dysregulated (the return_ticks metric reads this).
    rule("wk_infant_return_to_window", 9,
         [["infant", "has_affective_state", "iaff"],
          ["infant", "has_window", "wot"]],
         and_(is_infant(), eq(attr("iaff", "in_episode"), lit(1.0)),
              eq(attr("iaff", "dysregulated"), lit(1.0)),
              inside_window("iaff", "wot")),
         [["set_attr", "iaff", "dysregulated", 0.0],
          ["set_attr", "iaff", "dysreg_kind", 0.0]]),

    # R11 — episode close: arousal settled near setpoint ⇒ the episode ends
    #       (in_episode back to 0, so the window can breach again).
    rule("wk_infant_episode_close", 9,
         [["infant", "has_affective_state", "iaff"],
          ["infant", "has_window", "wot"]],
         and_(is_infant(), eq(attr("iaff", "in_episode"), lit(1.0)),
              eq(attr("iaff", "dysregulated"), lit(0.0)),
              not_(gt(attr("iaff", "arousal"), attr("wot", "min_half_width"))),
              not_(lt(attr("iaff", "arousal"),
                      minus(lit(0.0), attr("wot", "min_half_width"))))),
         [["set_attr", "iaff", "in_episode", 0.0]]),
]


PRODUCTIONS = [
    {"provenance": "window_knob_coreg:infant_window",
     "src": {"type": "Agent", "var": "infant"}, "edge_type": "has_window",
     "tgt": {"type": "WindowOfTolerance", "var": "wot"}},
    {"provenance": "window_knob_coreg:infant_stressor",
     "src": {"type": "Agent", "var": "infant"}, "edge_type": "has_stressor",
     "tgt": {"type": "Stressor", "var": "sx"}},
    {"provenance": "window_knob_coreg:attended_by",
     "src": {"type": "Agent", "var": "infant"}, "edge_type": "attended_by",
     "tgt": {"type": "Agent", "var": "cg"}},
    {"provenance": "window_knob_coreg:caregiver_window",
     "src": {"type": "Agent", "var": "cg"}, "edge_type": "has_window",
     "tgt": {"type": "WindowOfTolerance", "var": "cgwot"}},
]


SEED = {
    "id": "window_knob_coreg",
    "version": "1.0.0",
    "depends_on": ["affective_state_core"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "WINDOW-AS-A-KNOB (block 241000). Deepens block 239000's "
        "arousal/window-of-tolerance/co-regulation dyad into its genuine "
        "prior-art delta: the window of tolerance rendered as a FORMAL, "
        "settable, inspectable window-WIDTH knob (width = hi-lo = 2*half_width, "
        "a settable node attr) with a measured onset-vs-width dose-response, and "
        "a BIDIRECTIONAL dyad. Rides the REAL affective_state_core "
        "AffectiveState.arousal and reuses 239000's WindowOfTolerance node + "
        "the same sd_blend leaky-EMA pull form (x <- x + k*(target-x)). NEW vs "
        "239000: (1) the infant's arousal PULLS the caregiver's "
        "(wk_caregiver_pull_by_infant -- mutual entrainment); (2) the caregiver "
        "has its OWN dynamic arousal + window + regulated flag that flips when "
        "its arousal leaves its OWN [lo,hi] (wk_caregiver_dysreg_onset -- "
        "co-dysregulation); (3) the infant's co-regulation pull is GATED on the "
        "caregiver being regulated (wk_infant_coreg_pull), so a NARROW-window "
        "caregiver is pulled into co-dysregulation and FAILS to co-regulate "
        "while a WIDE-window one stays regulated and succeeds -- the SAME width "
        "knob governs single-agent tolerance AND two-agent co-regulation "
        "capacity. Concedes co-regulation-the-mechanism as prior art "
        "(coupled-oscillator dyads; active-inference CPC; arousal-caregiver "
        "robot); claims ONLY the settable window-width knob + the "
        "single<->two-agent unification. 'Kids do well if they can' (Greene): "
        "dysregulation is a STATE, never a badness -- NO reward/punishment. "
        "self_load_only, default-OFF; NO Rust, NO new Term."),
    "microtheory": {
        "name": "window_of_tolerance_as_a_settable_knob",
        "description": (
            "The window of tolerance is a settable WIDTH (hi-lo). The stressor "
            "magnitude at which an agent dysregulates is a monotonic function of "
            "that width. In a bidirectional dyad the caregiver's OWN width sets "
            "how much of the infant's distress it can absorb before being pulled "
            "into co-dysregulation -- one knob, single-agent tolerance and "
            "two-agent co-regulation capacity.")},
    "nodes": [],
    "edges": [],
    "productions": PRODUCTIONS,
    "rules": RULES,
}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(SEED, f, indent=2)
    print(f"wrote {OUT}: {len(RULES)} rules, {len(PRODUCTIONS)} productions")


if __name__ == "__main__":
    main()
