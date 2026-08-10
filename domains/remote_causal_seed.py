"""remote_causal_seed — RUNG 228000: REMOTE CAUSATION — "the switch affects a
remote thing" — the actions that FURTHER the agent's posits, as GRAPH RULES.

This is a SEED BUILDER (emits graph data — the allowed Python under the
architecture rule, exactly like domains/ls20_seek_seed.py). It contains NO agent
decision in Python: every decision (try the known option; exhaust; explore the
novel salient object; posit a remote-causal link; confirm/refute by intervention;
act; pass) is a rule `where`-clause over graph state. The host adapter
(worlds/remote_causal.py) only writes PERCEPTION facts, runs the interventional
PROBES as world physics (observe whether the REMOTE target B changed when the agent
DID vs did NOT interact), steps toward the rule-chosen waypoint, and applies the
remote effect on interact.

THE PROBLEM (block 228000). 227000 proved the agent DISCOVERS the flash's meaning,
but its ACTIONS were all LOCAL (probe the block; apply the transform on a co-located
station). It modelled NO remote causation. The real ls20 mechanic: the only-other
salient thing is a CROSS = a SWITCH; interacting with it affects a REMOTE thing (the
carried shape / a block elsewhere). This is the DEFERRED DOOM PROBLEM ("switch here
→ door opens there").

THE CHICKEN-AND-EGG FIX (owner). You cannot posit "cross → remote effect" before you
have been to the cross and interacted. So EXPLORATION comes FIRST, driven by
EXHAUSTION + SALIENCE, independent of any causal hypothesis. The loop:

  0. TRY KNOWN     — rc_try_known: probe the block AS-IS (the known option). The
                     adapter observes it did NOT pass.
  1. EXHAUST       — rc_exhausted: the known option failed and understanding stopped
                     (226 frustration breaks the futile cycle) -> explore_mode=1.
  2. EXPLORE       — rc_seek_novel_salient: among salient objects pick the ONE that
                     is UN-VISITED (novel) -> go there. Reads ONLY visited + salience,
                     NEVER a prior belief about what the object does.
  3. INTERVENE     — (adapter) on arrival, interact; the world PROBE observes whether
                     the REMOTE target B changed when the agent DID interact (eff_act)
                     vs did NOT (eff_noop, from the pre-interaction history).
  4. POSIT+CONFIRM — rc_posit_link mints a RemoteCausalPosit (the causal model is BORN
                     here, from the interaction); rc_confirm_interventional CONFIRMS it
                     iff eff_act==1 AND eff_noop==0 (the do-contrast: intervention makes
                     the difference -> attribute B's change to the object ACROSS SPACE);
                     rc_refute_interventional REFUTES iff eff_act==eff_noop (coincidence
                     / non-cause). rc_attribute_remote records a CONFIRMED link whose
                     object is spatially SEPARATED from B (is_local==0).
  5. ACT           — rc_act_seek_confirmed: seek the confirmed remote cause to operate
                     it (the action that FURTHERS the posit); the remote effect
                     transforms B; rc_pass routes to the block and passes.

THE CONTROLS it must beat:
  * causal_prior     — does NOT do exhaustion-driven exploration; only moves toward an
                       object it ALREADY has a causal hypothesis for. It never forms a
                       hypothesis for an un-visited object -> never goes -> cycles.
  * local_only       — explores + interacts, but attributes B's change ONLY to
                       something at B's LOCATION (is_local==1). The remote cross is out
                       of scope -> never posited -> never attributed / acted across
                       space. (Also the 227-style local model for G-pass-via-remote.)
  * no_intervention  — explores + reaches the cross but performs NO do-probe; attributes
                       by PASSIVE co-occurrence -> confabulates a link without
                       intervention (confirms coincidental + confounded causes).

The rules are DOMAIN-AGNOSTIC by construction: they name NO ls20/doom/cross/lever/
door/rotation constant. The SAME rules run on an ls20-shaped board (cross -> shape)
and a Doom-shaped board (lever -> remote door). Guarded on game.remote_on==1
(default-OFF; byte-identical to any graph that does not set the flag) and on the arm.
Integer-native. No Rust, no new Term — reuses the 227 posit/confirm/refute pattern,
the 210 operate seek/use, the 220 nav step, and the 226 frustration break.
"""
from __future__ import annotations

import json
from pathlib import Path


# --- Term-tree builders (same vocabulary as domains/ls20_seek_seed.py) ---------
def V(n):        return {"type": "Var", "name": n}
def A(n, k):     return {"type": "Attr", "node": V(n), "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def And(*x):     return {"type": "And", "items": list(x)}
def Or(*x):      return {"type": "Or", "items": list(x)}
def Not(a):      return {"type": "Not", "arg": a}
def T(term):     return {"__term__": term}


def _nb(node_var, edge):
    return {"type": "Neighbours", "node": V(node_var), "edge_type": edge, "any_type": False}


def _exists(node_var, edge, sub_var, predicate):
    return {"type": "Exists", "source": _nb(node_var, edge), "var_name": sub_var,
            "predicate": predicate}


def _enabled(arm):
    """Guard: the loop is switched ON for this game AND this arm."""
    return And(Eq(A("g", "remote_on"), L(1.0)), Eq(A("g", "arm"), L(arm)))


def _enabled_any(*arms):
    return And(Eq(A("g", "remote_on"), L(1.0)),
               Or(*[Eq(A("g", "arm"), L(a)) for a in arms]))


# --------------------------------------------------------------------------
# THE RULES — the exhaustion-first interventional remote-causal loop.
# --------------------------------------------------------------------------
def _rules():
    rules = []

    # ---- 0. TRY THE KNOWN OPTION -----------------------------------------
    # Before any exploration: probe the block AS-IS (the known move). The adapter
    # observes it did NOT pass, and sets known_option_tried=1. All exploring arms
    # AND the causal_prior control try their known option first (fair control).
    rules.append({
        "name": "rc_try_known",
        "comment": "TRY KNOWN: probe the block as-is (the known option) before exploring.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled_any("remote", "local_only", "no_intervention", "causal_prior"),
                     Eq(A("g", "known_option_tried"), L(0.0)),
                     Eq(A("g", "symbol_matches_goal"), L(0.0)),
                     Eq(A("g", "explore_mode"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })

    # ---- 1. EXHAUST -> EXPLORE MODE --------------------------------------
    # The known option failed (known_option_tried==1, still not matching) and the
    # futile cycle is broken (226 frustration). Enter explore_mode. NO causal model
    # is consulted — this is exhaustion + salience only. NOT for causal_prior (its
    # defining ablation: it never enters exhaustion-driven exploration).
    rules.append({
        "name": "rc_exhausted",
        "comment": "EXHAUST: known option failed + futile cycle broken -> explore_mode=1. "
                   "Exhaustion+salience only; NO causal model. (Not causal_prior.)",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled_any("remote", "local_only", "no_intervention"),
                     Eq(A("g", "known_option_tried"), L(1.0)),
                     Eq(A("g", "symbol_matches_goal"), L(0.0)),
                     Eq(A("g", "explore_mode"), L(0.0))),
        "effects": [["set_attr", "g", "explore_mode", 1.0],
                    ["set_attr", "g", "affect", "frustrated_explore"]],
    })

    # ---- 2. EXPLORE THE NOVEL SALIENT OBJECT -----------------------------
    # In explore_mode, route to a SALIENT object that is UN-VISITED (novel). Reads
    # ONLY visited + salient — never a causal attr, never "which object is the
    # switch". The only unexplored salient object is the cross -> go there.
    rules.append({
        "name": "rc_seek_novel_salient",
        "comment": "EXPLORE: explore_mode + an un-visited salient object -> go there. "
                   "Reads ONLY visited/salience; no prior causal belief.",
        "match": [["g", "has_object", "o"]],
        "where": And(_enabled_any("remote", "local_only", "no_intervention"),
                     Eq(A("g", "explore_mode"), L(1.0)),
                     Eq(A("g", "symbol_matches_goal"), L(0.0)),
                     Eq(A("o", "salient"), L(1.0)),
                     Eq(A("o", "visited"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "object"],
                    ["set_attr", "g", "wp_r", T(A("o", "r"))],
                    ["set_attr", "g", "wp_c", T(A("o", "c"))],
                    ["set_attr", "g", "seek_obj", T(A("o", "obj_id"))]],
    })

    # ---- 4a. POSIT the remote-causal link (BORN from the interaction) ----
    # An interacted object with no posit yet -> mint a RemoteCausalPosit carrying
    # the OBSERVED interventional facts (eff_act, eff_noop, passive_cooccur) + the
    # object's spatial relation to B (is_local). The causal model is minted only
    # AFTER interaction. Full spatial scope (remote, no_intervention).
    def _posit_effects():
        return [
            ["add_node", "q", "RemoteCausalPosit", {
                "obj_id": T(A("o", "obj_id")),
                "is_local": T(A("o", "is_local")),
                "eff_act": T(A("o", "eff_act")),
                "eff_noop": T(A("o", "eff_noop")),
                "passive_cooccur": T(A("o", "passive_cooccur")),
                "status": T(L("posited")),
            }],
            ["add_edge", "g", "has_posit", "q"],
        ]

    rules.append({
        "name": "rc_posit_link",
        "comment": "POSIT: interacted object, no posit yet -> mint a RemoteCausalPosit "
                   "(full spatial scope). The causal model is BORN from the interaction.",
        "match": [["g", "has_object", "o"]],
        "where": And(_enabled_any("remote", "no_intervention"),
                     Eq(A("o", "interacted"), L(1.0)),
                     Not(_exists("g", "has_posit", "q2",
                                 Eq(A("q2", "obj_id"), A("o", "obj_id"))))),
        "effects": _posit_effects(),
    })

    # ---- 4a'. POSIT — LOCAL-ONLY scope (control) -------------------------
    # local_only can only attribute B's change to something at B's LOCATION: it
    # posits ONLY objects with is_local==1. The remote cross is never posited.
    rules.append({
        "name": "rc_posit_link_local",
        "comment": "CONTROL (local_only): posit ONLY local (is_local==1) objects. A "
                   "spatially-separated object is out of scope -> never posited -> never attributed.",
        "match": [["g", "has_object", "o"]],
        "where": And(_enabled("local_only"),
                     Eq(A("o", "interacted"), L(1.0)),
                     Eq(A("o", "is_local"), L(1.0)),
                     Not(_exists("g", "has_posit", "q2",
                                 Eq(A("q2", "obj_id"), A("o", "obj_id"))))),
        "effects": _posit_effects(),
    })

    # ---- 4b. CONFIRM by INTERVENTION (the do-contrast) -------------------
    # A posit whose object CHANGED B under intervention (eff_act==1) but NOT without
    # it (eff_noop==0) -> CONFIRMED. Intervention makes the difference; this rules
    # out coincidence and local confounds. Location-agnostic: the REMOTE cross is
    # confirmed across space.
    rules.append({
        "name": "rc_confirm_interventional",
        "comment": "CONFIRM: eff_act==1 AND eff_noop==0 (intervention makes the difference) "
                   "-> confirmed. The do-contrast; a spatially-separated cause is confirmed "
                   "across space.",
        "match": [["g", "has_posit", "q"]],
        "where": And(_enabled_any("remote", "local_only"),
                     Eq(A("q", "status"), L("posited")),
                     Eq(A("q", "eff_act"), L(1.0)),
                     Eq(A("q", "eff_noop"), L(0.0))),
        "effects": [["set_attr", "q", "status", "confirmed"]],
    })

    # ---- 4b'. REFUTE by INTERVENTION -------------------------------------
    # A posit whose object changed B the SAME whether or not intervened on
    # (eff_act==eff_noop) -> REFUTED (it does not control B: either never changes,
    # or changes regardless = coincidence).
    rules.append({
        "name": "rc_refute_interventional",
        "comment": "REFUTE: eff_act==eff_noop (no interventional difference) -> refuted "
                   "(coincidence / non-cause).",
        "match": [["g", "has_posit", "q"]],
        "where": And(_enabled_any("remote", "local_only"),
                     Eq(A("q", "status"), L("posited")),
                     Eq(A("q", "eff_act"), A("q", "eff_noop"))),
        "effects": [["set_attr", "q", "status", "refuted"]],
    })

    # ---- 4b''. CONFIRM by PASSIVE co-occurrence (no-intervention control) -
    # no_intervention performs NO do-probe; it confirms any posit whose object
    # merely CO-OCCURRED with an observed B-change (passive_cooccur==1). Without the
    # do-contrast it cannot separate cause from coincidence -> confabulates.
    rules.append({
        "name": "rc_confirm_passive",
        "comment": "CONTROL (no_intervention): confirm on passive co-occurrence "
                   "(passive_cooccur==1), no do-probe -> confabulates a link.",
        "match": [["g", "has_posit", "q"]],
        "where": And(_enabled("no_intervention"),
                     Eq(A("q", "status"), L("posited")),
                     Eq(A("q", "passive_cooccur"), L(1.0))),
        "effects": [["set_attr", "q", "status", "confirmed"]],
    })

    # ---- 4c. ATTRIBUTE ACROSS SPACE --------------------------------------
    # A CONFIRMED posit whose object is spatially SEPARATED from B (is_local==0) ->
    # record that B's change is attributed to a remote action across space.
    rules.append({
        "name": "rc_attribute_remote",
        "comment": "ATTRIBUTE: a confirmed link on a spatially-separated object -> "
                   "attributed_remote=1 (B's change attributed across space).",
        "match": [["g", "has_posit", "q"]],
        "where": And(_enabled_any("remote", "local_only", "no_intervention"),
                     Eq(A("q", "status"), L("confirmed")),
                     Eq(A("q", "is_local"), L(0.0))),
        "effects": [["set_attr", "g", "attributed_remote", 1.0],
                    ["set_attr", "g", "attributed_obj", T(A("q", "obj_id"))]],
    })

    # ---- 5. ACT on the confirmed remote link -----------------------------
    # A confirmed remote link + the carried thing still not matching -> seek that
    # object to OPERATE it (the action that furthers the posit). Joins the posit to
    # its object by obj_id.
    rules.append({
        "name": "rc_act_seek_confirmed",
        "comment": "ACT: confirmed remote link + not matching -> seek the confirmed remote "
                   "cause to operate it (furthers the posit).",
        "match": [["g", "has_posit", "q"], ["g", "has_object", "o"]],
        "where": And(_enabled_any("remote", "local_only", "no_intervention"),
                     Eq(A("q", "status"), L("confirmed")),
                     Eq(A("q", "is_local"), L(0.0)),
                     Eq(A("q", "obj_id"), A("o", "obj_id")),
                     Eq(A("g", "symbol_matches_goal"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "object"],
                    ["set_attr", "g", "wp_r", T(A("o", "r"))],
                    ["set_attr", "g", "wp_c", T(A("o", "c"))],
                    ["set_attr", "g", "seek_obj", T(A("o", "obj_id"))],
                    ["set_attr", "g", "act_on_confirmed", 1.0]],
    })

    # ---- 6. PASS ---------------------------------------------------------
    rules.append({
        "name": "rc_pass",
        "comment": "PASS: the carried thing matches the requirement -> route to the block "
                   "and pass.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled_any("remote", "local_only", "no_intervention"),
                     Eq(A("g", "symbol_matches_goal"), L(1.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })

    # ---- CONTROL: causal_prior — only move toward an ALREADY-hypothesised object.
    # It has NO exhaustion-driven exploration (no rc_exhausted / rc_seek_novel /
    # rc_posit for it): after its known option fails it can only move toward an
    # object with a CONFIRMED link — but it never forms one (never interacts an
    # un-visited object) -> never moves -> cycles forever.
    rules.append({
        "name": "rc_prior_seek",
        "comment": "CONTROL (causal_prior): move ONLY toward an object with an ALREADY "
                   "confirmed link. None ever forms -> never goes -> cycles.",
        "match": [["g", "has_posit", "q"], ["g", "has_object", "o"]],
        "where": And(_enabled("causal_prior"),
                     Eq(A("q", "status"), L("confirmed")),
                     Eq(A("q", "obj_id"), A("o", "obj_id")),
                     Eq(A("g", "symbol_matches_goal"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "object"],
                    ["set_attr", "g", "wp_r", T(A("o", "r"))],
                    ["set_attr", "g", "wp_c", T(A("o", "c"))]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "remote_causal",
        "version": "1.0.0",
        "depends_on": [],
        "area": "retina",
        "description": (
            "REMOTE CAUSATION (block 228000): the only-other salient thing is a SWITCH; "
            "interacting with it affects a REMOTE thing (the deferred Doom problem: switch "
            "here -> door there). EXHAUSTION-FIRST: try the known option (rc_try_known), "
            "exhaust + break the futile cycle (rc_exhausted, 226), EXPLORE the un-visited "
            "salient object (rc_seek_novel_salient — visited/salience only, NO causal model), "
            "INTERVENE on arrival, POSIT+CONFIRM the remote-causal link by the do-contrast "
            "(rc_posit_link -> rc_confirm_interventional: eff_act==1 AND eff_noop==0, "
            "attributing across space; rc_refute_interventional; rc_attribute_remote), then "
            "ACT (rc_act_seek_confirmed -> rc_pass). Controls: causal_prior (no exploration), "
            "local_only (attributes only at B's location), no_intervention (passive "
            "co-occurrence -> confabulates). Domain-agnostic (no ls20/doom/cross/lever "
            "token); same rules run ls20 cross->shape AND Doom lever->door. Guarded on "
            "game.remote_on==1 (default-OFF, byte-identical) + game.arm. Integer-native; no "
            "Rust; reuses the 227 posit/confirm + 210 operate + 220 nav + 226 frustration."),
        "microtheory": {
            "name": "remote_causal",
            "description": "A salient object can affect a REMOTE thing across space. The agent "
                           "explores the un-visited salient object out of exhaustion (no prior "
                           "causal belief), intervenes, and DISCOVERS the remote-causal link by "
                           "the interventional do-contrast (act->effect vs no-op->no-effect), "
                           "attributing B's change to the remote action across space; then acts "
                           "on the confirmed link. Every decision is a rule.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "seeds" / "remote_causal.json"
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
