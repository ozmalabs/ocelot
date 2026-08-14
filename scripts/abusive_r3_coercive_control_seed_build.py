#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R3 -- COERCIVE CONTROL seed builder (block 289000).

Authoring tool ONLY: it EMITS `seeds/abusive_r3_coercive_control.json` (graph
data) -- no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md` for the full
design rationale. In brief, this seed adds FOUR new rules riding two
already-built, unmodified seeds (`snap_frustration`, block 242000;
`arousal_window_coreg`, block 239000), reusing R2's own genuine composition
finding (`ABUSIVE_R2_CYCLE_LIMIT_PREREG.md` Sec. 3.0 -- routing the victim's
entrainment through `frustration` rather than fighting `snap_arousal_track`'s
unconditional `arousal := setpoint+frustration` commit):

  * `r3_victim_entrainment_solo`     -- SINGLE-ANCHOR arm: victim entrained
    ONLY by the abuser (byte-identical formula to R2's own
    `r2_victim_entrainment_via_frustration`), gated OFF when a second,
    outside regulator is present (`vaff.has_outside_regulator==0`).
  * `r3_victim_entrainment_dyad`     -- OUTSIDE-REGULATOR arm: victim
    entrained by BOTH the abuser AND a second, fixed-calm, always-regulated
    outside source in ONE combined Term (avoids the two-separate-instances
    last-write-wins hazard a naive per-edge composition would hit -- see the
    prereg Sec. 3 for the empirical pilot that found this), distinguished
    from the solo rule's abuser-only binding via an explicit `is_abuser`
    role attribute (1.0 on the abuser's AffectiveState, 0.0 on the outside
    regulator's) so the two attended_by targets cannot cross-bind.
  * `r3_prior_track_narrow` / `r3_prior_track_widen` -- ride the ALREADY-BUILT,
    UNMODIFIED `arousal_window_coreg` `narrow_count`/`widen_count` counters
    (bumped by `episode_resolve_narrow`/`episode_resolve_widen`, block
    239000) via a counter-DELTA observer (fires exactly once per genuine
    increment, robust to `run_rules()`'s repeating-fixpoint pass structure --
    R2's own documented finding, Sec. 3.0) to step `others_trust`/
    `self_worth` (new WindowOfTolerance attrs) down on an unsupported
    (narrowed) episode resolution and up on a supported (widened) one --
    the SAME `safety_prior` step-and-clamp pattern `episode_resolve_narrow`/
    `widen` already uses for `safety_prior`, and the SAME
    clamp01(Max(0,Min(1,...))) idiom `bigville_life_rearing.json`
    (block 262000) already uses for its own `prior_others_trust`/
    `prior_self_worth` (confirmed materialized there, on the Agent node, as
    a ONE-SHOT coming-of-age mint -- R3 needs a PROGRESSIVE, per-episode
    version, so it rides the counters directly rather than reusing that
    one-shot rule).

NO Rust, NO new Term -- every Term below (Plus/Minus/Times/Max/Min/Attr/Var/
Lit/Eq/Gt/And) is already in the engine and already used by
`arousal_window_coreg.json` / `abusive_r2_cycle_limit.json` /
`bigville_life_rearing.json`.

Run:  python3 scripts/abusive_r3_coercive_control_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_r3_coercive_control.json")


# ---- Term constructors (mechanical JSON shape, identical to prior rungs) -----
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


def maxt(*items):
    return {"type": "Max", "items": list(items)}


def mint(*items):
    return {"type": "Min", "items": list(items)}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def term(t):
    return {"__term__": t}


def clamp01(t):
    return maxt(lit(0.0), mint(lit(1.0), t))


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# --------------------------------------------------------- entrainment Term ---
def coreg_term(source_aff, gain_key="k_co"):
    """One source's contribution to the combined pull: k_co*(source.arousal -
    vaff.arousal). vaff is fixed as the local name 'vaff' throughout."""
    return times(attr("vaff", gain_key),
                 minus(attr(source_aff, "arousal"), attr("vaff", "arousal")))


def selfreg_term():
    return times(attr("vaff", "k_self"),
                 minus(attr("vaff", "setpoint"), attr("vaff", "arousal")))


# --- SOLO: single-anchor arm. Byte-identical formula to R2's own
# r2_victim_entrainment_via_frustration (one coreg pull + one selfreg pull,
# combined off the tick-start arousal, written to frustration so
# snap_arousal_track -- unmodified, order 5 -- becomes the mechanism that
# COMMITS the entrained value to arousal). Gated OFF when a second regulator
# is present so it never collides with the dyad rule below.
solo_frustration_term = term(
    minus(
        plus(attr("vaff", "arousal"), coreg_term("aaff"), selfreg_term()),
        attr("vaff", "setpoint")))

r3_victim_entrainment_solo = rule(
    "r3_victim_entrainment_solo", 8,
    [["victim", "has_affective_state", "vaff"],
     ["victim", "attended_by", "abuser"],
     ["abuser", "has_affective_state", "aaff"]],
    and_(lt(attr("vaff", "pcr_epoch"), attr("vaff", "tick_epoch")),
         eq(attr("aaff", "is_abuser"), lit(1.0)),
         eq(attr("vaff", "has_outside_regulator"), lit(0.0))),
    [["set_attr", "vaff", "frustration", solo_frustration_term],
     ["set_attr", "vaff", "pcr_epoch", term(attr("vaff", "tick_epoch"))]])

# --- DYAD: outside-regulator arm. BOTH sources' pulls combined in ONE Term,
# in ONE match instance (distinguished by the is_abuser role attribute, so
# the two attended_by edges cannot cross-bind into a spurious
# abuser==outside pairing) -- avoids the two-separate-rule-instances
# last-write-wins hazard a naive per-edge composition would hit (piloted and
# confirmed during R3's design; see prereg Sec. 3).
dyad_frustration_term = term(
    minus(
        plus(attr("vaff", "arousal"), coreg_term("aaff"), coreg_term("oaff"),
             selfreg_term()),
        attr("vaff", "setpoint")))

r3_victim_entrainment_dyad = rule(
    "r3_victim_entrainment_dyad", 8,
    [["victim", "has_affective_state", "vaff"],
     ["victim", "attended_by", "abuser"],
     ["abuser", "has_affective_state", "aaff"],
     ["victim", "also_attended_by", "outside"],
     ["outside", "has_affective_state", "oaff"]],
    and_(lt(attr("vaff", "pcr_epoch"), attr("vaff", "tick_epoch")),
         eq(attr("aaff", "is_abuser"), lit(1.0)),
         eq(attr("oaff", "is_abuser"), lit(0.0)),
         eq(attr("vaff", "has_outside_regulator"), lit(1.0))),
    [["set_attr", "vaff", "frustration", dyad_frustration_term],
     ["set_attr", "vaff", "pcr_epoch", term(attr("vaff", "tick_epoch"))]])

# --- Outside regulator's got_coreg attribution. arousal_window_coreg's own
# `mark_coreg_support` (UNMODIFIED) only matches the `attended_by` edge type,
# so it cannot see the outside regulator (deliberately connected via a
# DIFFERENT edge type, `also_attended_by` -- see the module docstring's
# hazard 4 for WHY: a second `attended_by` edge from the victim, sharing an
# edge TYPE with the first, was piloted and found to corrupt this rung's own
# entrainment rule's reads of OTHER nodes' attrs whenever
# `arousal_window_coreg`'s `selfreg_pull` was also loaded -- reproducible,
# isolated by bisection, not explained at the Rust level, and sidestepped by
# giving the outside regulator its own edge type rather than chasing the
# engine internals further; PREREG Sec. 3 has the full empirical trail).
# This is the SAME "smallest possible reader" precedent R1/R2 already used
# (R1's OPEN QUESTION #2; R2's Sec. 3.0): a literal edge-type substitution of
# `mark_coreg_support`'s own match pattern, same where/effect semantics,
# never editing the original rule.
r3_mark_coreg_support_outside = rule(
    "r3_mark_coreg_support_outside", 6,
    [["infant", "has_affective_state", "iaff"],
     ["infant", "also_attended_by", "cg"]],
    and_(eq(attr("iaff", "in_episode"), lit(1.0)),
         eq(attr("cg", "regulated"), lit(1.0))),
    [["set_attr", "iaff", "got_coreg", 1.0]])

# --------------------------------------------------- prior-tracking rules ----
TRUST_STEP = 0.03   # same order of magnitude as arousal_window_coreg's own
WORTH_STEP = 0.03   # safety_step (0.03) -- disclosed, matched, not re-tuned

r3_prior_track_narrow = rule(
    "r3_prior_track_narrow", 10,
    [["victim", "has_window", "wot"]],
    gt(attr("wot", "narrow_count"), attr("wot", "pn_last_narrow")),
    [["set_attr", "wot", "others_trust",
      term(clamp01(minus(attr("wot", "others_trust"), lit(TRUST_STEP))))],
     ["set_attr", "wot", "self_worth",
      term(clamp01(minus(attr("wot", "self_worth"), lit(WORTH_STEP))))],
     ["set_attr", "wot", "pn_last_narrow", term(attr("wot", "narrow_count"))]])

r3_prior_track_widen = rule(
    "r3_prior_track_widen", 10,
    [["victim", "has_window", "wot"]],
    gt(attr("wot", "widen_count"), attr("wot", "pn_last_widen")),
    [["set_attr", "wot", "others_trust",
      term(clamp01(plus(attr("wot", "others_trust"), lit(TRUST_STEP))))],
     ["set_attr", "wot", "self_worth",
      term(clamp01(plus(attr("wot", "self_worth"), lit(WORTH_STEP))))],
     ["set_attr", "wot", "pn_last_widen", term(attr("wot", "widen_count"))]])

RULES = [r3_victim_entrainment_solo, r3_victim_entrainment_dyad,
         r3_mark_coreg_support_outside,
         r3_prior_track_narrow, r3_prior_track_widen]

PRODUCTIONS = [
    {
        "provenance": "abusive_r3_coercive_control:victim_attended_by_abuser",
        "src": {"type": "Agent", "var": "victim"},
        "edge_type": "attended_by",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        # DELIBERATELY a DIFFERENT edge type from the abuser's -- see the
        # world adapter's module docstring, hazard 3: a second `attended_by`
        # edge from the victim (same type as the abuser's) was piloted and
        # found to corrupt this seed's own entrainment rule whenever
        # arousal_window_coreg's selfreg_pull is also loaded.
        "provenance": "abusive_r3_coercive_control:victim_also_attended_by_outside",
        "src": {"type": "Agent", "var": "victim"},
        "edge_type": "also_attended_by",
        "tgt": {"type": "Agent", "var": "outside"}
    }
]

SEED = {
    "id": "abusive_r3_coercive_control",
    "version": "1.0.0",
    "depends_on": ["snap_frustration", "arousal_window_coreg"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS R3 -- COERCIVE CONTROL: window-narrowing + "
        "prior-mis-setting + isolation/frontier-collapse (block 289000). "
        "Extends R2's OWN dyad-coupling pattern (block 286000; "
        "snap_frustration drives the abuser's tension-building->incident "
        "relaxation oscillator, arousal_window_coreg drives the victim's "
        "entrainment/self-regulation/window plasticity), reusing R2's own "
        "genuine composition finding (route the victim's entrainment "
        "through `frustration`, never write `arousal` directly, because "
        "snap_arousal_track unconditionally clobbers has_affective_state "
        "nodes). R2's OWN prereg (Sec. 7) already named the mechanism this "
        "rung measures as an honest, disclosed residual: 'the victim's "
        "window half_width narrows monotonically toward its floor... "
        "because the abuser never satisfies got_coreg's regulated==1 "
        "condition... consistent with R3's (out-of-scope) window-narrowing "
        "focus.' R3 makes that residual the headline: run the SAME "
        "single-anchor dyad for many incident cycles (window-narrowing OVER "
        "EPISODES) and add a SECOND, structurally distinct arm where a "
        "fixed-calm, always-regulated OUTSIDE regulator is ALSO connected "
        "to the victim, via a DIFFERENT edge type (`also_attended_by` -- a "
        "second same-typed `attended_by` edge was piloted and found to "
        "corrupt this seed's own entrainment rule whenever "
        "arousal_window_coreg's selfreg_pull is also loaded, see the world "
        "adapter's docstring) so the frontier is NOT collapsed to one "
        "source -- `r3_mark_coreg_support_outside` (an edge-type "
        "substitution of arousal_window_coreg's OWN unmodified "
        "mark_coreg_support) then attributes got_coreg via the outside "
        "source, so the window holds/widens (via arousal_window_coreg's "
        "own, UNMODIFIED episode_resolve_widen/narrow) instead of "
        "narrowing. THE SAFETY-ANCHOR "
        "INVERSION (B3/A7 of ABUSIVE_RELATIONSHIPS_SCOPING.md -- Main & "
        "Hesse's 'fright without solution': the only available regulator IS "
        "the threat) is the single-anchor arm's STRUCTURE itself (one "
        "attended_by edge, to the dysregulation source) -- measured as how "
        "closely the victim's entrained arousal tracks the abuser's, "
        "compared against the outside-regulator arm's tracking distance. "
        "PRIOR MIS-SETTING (others_trust/self_worth, B3's third coupled "
        "move) rides the SAME narrow_count/widen_count counters "
        "arousal_window_coreg ALREADY bumps (UNMODIFIED) via a counter-"
        "delta observer, using the SAME clamp01 step idiom "
        "bigville_life_rearing.json (block 262000) already uses for its own "
        "(one-shot, coming-of-age) prior_others_trust/prior_self_worth -- "
        "R3's version is PROGRESSIVE (per-episode), so it is a NEW pair of "
        "attrs on the victim's WindowOfTolerance node (others_trust/"
        "self_worth), not a reuse of bigville's Agent-node attrs of a "
        "similar name (disclosed naming choice, not a collision -- "
        "different node, different semantics, see prereg Sec. 2). NO "
        "reward/punishment anywhere; the tension trickle and the outside "
        "regulator's fixed calm arousal are both world-delivered facts "
        "(mechanically identical to a goal-block magnitude or a caregiver "
        "arousal reading in 239000/242000), never a scored choice. "
        "self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "coercive_control_window_narrowing_and_anchor_inversion",
        "description": (
            "Coercive control is not a new mechanism -- it is R2's own "
            "leaky-integrate-fire abuser + leaky-entrainment victim dyad, "
            "run over many incident cycles and read for what it does to the "
            "victim's window and priors when the ONLY available regulator "
            "is also the dysregulation source, versus what happens when a "
            "second, healthy regulator keeps the frontier open."
        )
    },
    "nodes": [],
    "edges": [],
    "productions": PRODUCTIONS,
    "rules": RULES,
}


def main():
    with open(OUT, "w") as f:
        json.dump(SEED, f, indent=2)
        f.write("\n")
    print(f"wrote {OUT} ({len(RULES)} rules)")


if __name__ == "__main__":
    main()
