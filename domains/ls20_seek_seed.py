"""ls20_seek_seed — RUNG 227000: THE GAME IS COMMUNICATING — posit-and-test
semiosis that DISCOVERS the flash's meaning, then acts (seek-and-transform), as
GRAPH RULES.

This is a SEED BUILDER (emits graph data — the allowed Python under the
architecture rule, exactly like domains/ls20_planning_seed.py). It contains NO
agent decision in Python: every decision (which meaning the flash carries; whether
to seek; which move) is a rule `where`-clause over graph state. The host adapter
(worlds/arc_ls20_seek.py) only writes PERCEPTION facts (is a flash present; the
general communicative vocabulary it knows; the observed test outcome; the required
transform the graph-native 217000 sd-loop recognised) and world PHYSICS (route to
the rule-chosen waypoint; apply a transform; pass at the block; observe the probe).

THE STANCE (owner correction, block 227000). The game is a cooperative
COMMUNICATIVE partner; the flash is a SIGN/MESSAGE, NOT a fact with a built-in
meaning. 225000 hardcoded "flash = per-cell consume" and got a live null; the fix
is not a different hardcoded reading but to DISCOVER the meaning by semiosis:

  POSIT      — the flash is a MESSAGE; mint MULTIPLE candidate meanings as `Posit`
               Hypothesis nodes from a GENERAL communicative vocabulary
               {requirement, reward, warning, location, acknowledgement}, each
               carrying its OWN general prediction (`sg_mint_posits`). NOTHING
               ls20-specific — the same vocabulary interprets any sign.
  TEST       — each posit PREDICTS an outcome; the agent ACTS to test it (probe the
               block with its shape AS-IS, `sg_want_test`) and OBSERVES; the
               RESIDUAL (predicted − observed) REFUTES the wrong posits
               (`sg_refute`) and CONFIRMS the surviving one (`sg_confirm`). This is
               the 221/222 sd-loop / understanding drive applied to a SIGN.
  ACT        — a CONFIRMED posit that implies an unmet condition (`implies_change`)
               DRIVES the behaviour: transform_required=1 (`sg_act_requirement`) ->
               seek the ONLY-OTHER salient shape whose transform matches the
               recognised req_key (`sk_seek`, the 218000 plan_seek_station pattern)
               -> apply -> pass the block (`sk_pass`). Refuted posits are dropped;
               salience drives the seek so the agent does NOT cycle (226000).

THE CONTROLS it must beat:
  * `cycling` — the "just cycling" baseline the owner saw: no interpretation, no
    rule fires, the adapter cycles a fixed action sequence -> (almost) never passes.
  * `hardcode_reward` — HARDCODES a wrong posit (the flash means "reward: collect
    as-is") and acts on it: routes to the block as-is, never transforms -> fails.
    Hardcoding the wrong meaning LOSES.
  * `no_test` — POSITS the full vocabulary but never TESTS (no probe -> no
    observation -> nothing refuted/confirmed) -> transform_required never set ->
    never seeks -> cycles. Positing without testing is not discovering.

Every rule is guarded on `game.seek_on==1` (default-OFF; byte-identical to any
graph that does not set the flag) and on the arm (`game.arm`). Integer-native. No
Rust, no new Term — the recognition reuses shape_decode_loop (217000); the flash
detection reuses the onset stream (223000); the nav reuses quanta_navigation
(220000); the anti-cycle reuses ls20_frustration (226000); the posit lifecycle is
the substrate's own mint/confirm/revise pattern. Ordinary match+where+effect rules.
"""
from __future__ import annotations

import json
from pathlib import Path


# --- Term-tree builders (same vocabulary as domains/ls20_planning_seed.py) -----
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
    return And(Eq(A("g", "seek_on"), L(1.0)), Eq(A("g", "arm"), L(arm)))


def _enabled_any(*arms):
    return And(Eq(A("g", "seek_on"), L(1.0)),
               Or(*[Eq(A("g", "arm"), L(a)) for a in arms]))


# --------------------------------------------------------------------------
# THE GENERAL COMMUNICATIVE VOCABULARY (seed data, NOT one ls20 answer).
# Each meaning carries its OWN GENERAL prediction about the world — properties of
# the communicative meaning, applicable to ANY sign, not an ls20 constant:
#   pred_accept  — does this meaning predict the current state is ALREADY ACCEPTED
#                  (the sign says "you're done / you gained / you are at the target")?
#   pred_harm    — does this meaning predict HARM from proceeding (danger/warning)?
#   implies_change — does CONFIRMING this meaning imply an UNMET condition the agent
#                  must CHANGE its carried thing to satisfy?
# --------------------------------------------------------------------------
VOCAB = [
    {"meaning": "requirement",     "pred_accept": 0.0, "pred_harm": 0.0, "implies_change": 1.0},
    {"meaning": "reward",          "pred_accept": 1.0, "pred_harm": 0.0, "implies_change": 0.0},
    {"meaning": "acknowledgement", "pred_accept": 1.0, "pred_harm": 0.0, "implies_change": 0.0},
    {"meaning": "location",        "pred_accept": 1.0, "pred_harm": 0.0, "implies_change": 0.0},
    {"meaning": "warning",         "pred_accept": 0.0, "pred_harm": 1.0, "implies_change": 0.0},
]


# --------------------------------------------------------------------------
# THE RULES — the semiosis loop (posit -> test -> confirm/refute -> act).
# --------------------------------------------------------------------------
def _rules():
    rules = []

    # POSIT: the flash is a MESSAGE. For each general communicative meaning the
    # agent knows (`knows_meaning`), mint ONE Posit Hypothesis carrying that
    # meaning + its general prediction — UNLESS one already exists (dedup, the
    # sd_dedup_existing pattern). MULTIPLE posits are generated; NONE is privileged.
    rules.append({
        "name": "sg_mint_posits",
        "comment": "POSIT: mint a Posit Hypothesis per known communicative meaning (dedup). "
                   "The flash is a SIGN with many candidate meanings; none is hardcoded.",
        "match": [["g", "has_ping", "p"], ["g", "knows_meaning", "sm"]],
        "where": And(_enabled_any("semiosis", "no_test"),
                     Eq(A("g", "flash_present"), L(1.0)),
                     Not(_exists("g", "has_posit", "q2",
                                 Eq(A("q2", "meaning"), A("sm", "meaning"))))),
        "effects": [
            ["add_node", "q", "Posit", {
                "meaning": T(A("sm", "meaning")),
                "pred_accept": T(A("sm", "pred_accept")),
                "pred_harm": T(A("sm", "pred_harm")),
                "implies_change": T(A("sm", "implies_change")),
                "status": T(L("open")),
            }],
            ["add_edge", "g", "has_posit", "q"],
        ],
    })

    # TEST (want): open posits exist and the probe has not been run yet -> route to
    # the block and probe with the shape AS-IS (the discriminating action: a
    # reward/location/ack meaning predicts pass-as-is; a requirement/warning does
    # not). The DECISION to test is a rule; the adapter only executes the probe and
    # OBSERVES.
    rules.append({
        "name": "sg_want_test",
        "comment": "TEST(want): open posits + no observation yet -> probe the block AS-IS to "
                   "discriminate the posits. Routing is execution; the want is a rule.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled("semiosis"),
                     Eq(A("g", "test_observed"), L(0.0)),
                     _exists("g", "has_posit", "q2", Eq(A("q2", "status"), L("open")))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })

    # REFUTE: after the probe (test_observed==1), a still-open Posit whose prediction
    # DISAGREES with the observation (accept OR harm mismatch) is REFUTED. The
    # residual kills it.
    rules.append({
        "name": "sg_refute",
        "comment": "REFUTE: an open Posit whose predicted (accept,harm) != observed -> refuted. "
                   "The predict-and-residual test (221/222 sd-loop applied to a SIGN).",
        "match": [["g", "has_posit", "q"]],
        "where": And(_enabled("semiosis"),
                     Eq(A("g", "test_observed"), L(1.0)),
                     Eq(A("q", "status"), L("open")),
                     Or(Not(Eq(A("q", "pred_accept"), A("g", "observed_accept"))),
                        Not(Eq(A("q", "pred_harm"), A("g", "observed_harm"))))),
        "effects": [["set_attr", "q", "status", "refuted"]],
    })

    # CONFIRM: after the probe, an open Posit whose prediction MATCHES the
    # observation on BOTH observables is CONFIRMED. (The general vocabulary is
    # discriminating: only ONE meaning matches (accept,harm)=(observed).)
    rules.append({
        "name": "sg_confirm",
        "comment": "CONFIRM: an open Posit whose predicted (accept,harm) == observed -> confirmed. "
                   "The surviving meaning is the DISCOVERED interpretation.",
        "match": [["g", "has_posit", "q"]],
        "where": And(_enabled("semiosis"),
                     Eq(A("g", "test_observed"), L(1.0)),
                     Eq(A("q", "status"), L("open")),
                     Eq(A("q", "pred_accept"), A("g", "observed_accept")),
                     Eq(A("q", "pred_harm"), A("g", "observed_harm"))),
        "effects": [["set_attr", "q", "status", "confirmed"]],
    })

    # ACT (on the confirmed posit): a CONFIRMED meaning that implies an unmet
    # condition (implies_change==1) DRIVES the behaviour — transform_required=1 +
    # surprise->ORIENT + record the discovered meaning. This is the bridge from the
    # discovered SIGN to the seek behaviour.
    rules.append({
        "name": "sg_act_requirement",
        "comment": "ACT: a CONFIRMED posit implying an unmet condition -> transform_required=1 "
                   "(the discovered meaning drives the seek). NO hardcoded flash->requirement.",
        "match": [["g", "has_posit", "q"]],
        "where": And(_enabled("semiosis"),
                     Eq(A("q", "status"), L("confirmed")),
                     Eq(A("q", "implies_change"), L(1.0))),
        "effects": [["set_attr", "g", "transform_required", 1.0],
                    ["set_attr", "g", "salient_seek", 1.0],
                    ["set_attr", "g", "affect", "surprise_orient"],
                    ["set_attr", "g", "confirmed_meaning", T(A("q", "meaning"))]],
    })

    # SEEK the ONLY-OTHER salient shape (the transform provider). Because a
    # requirement was DISCOVERED (transform_required), route to the station/shape
    # whose transform key MATCHES the recognised req_key (217000). The 218000
    # plan_seek_station INVESTIGATION pattern, now downstream of the posit loop.
    rules.append({
        "name": "sk_seek",
        "comment": "SEEK: transform_required (DISCOVERED) -> route to the only-other salient "
                   "shape whose key matches the recognised required transform.",
        "match": [["g", "has_station", "s"]],
        "where": And(_enabled("semiosis"),
                     Eq(A("g", "transform_required"), L(1.0)),
                     Eq(A("g", "symbol_matches_goal"), L(0.0)),
                     Eq(A("s", "key"), A("g", "req_key")),
                     Eq(A("s", "used"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "station"],
                    ["set_attr", "g", "wp_r", T(A("s", "r"))],
                    ["set_attr", "g", "wp_c", T(A("s", "c"))]],
    })

    # PASS: the carried shape now matches the block's requirement -> route to the
    # block and pass.
    rules.append({
        "name": "sk_pass",
        "comment": "PASS: carried shape matches the requirement -> route to the block and pass.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled("semiosis"), Eq(A("g", "symbol_matches_goal"), L(1.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })

    # CONTROL — HARDCODE the WRONG posit: act on a fixed belief "the flash means
    # reward: collect as-is." Route straight to the block, never transform. It
    # never confirms `requirement` and never passes. Hardcoding the wrong meaning
    # LOSES.
    rules.append({
        "name": "sg_hardcode_reward",
        "comment": "CONTROL: hardcode the flash = reward (collect as-is) -> route to the block, "
                   "never transform. Never discovers requirement; never passes.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled("hardcode_reward"), Eq(A("g", "flash_present"), L(1.0))),
        "effects": [["set_attr", "g", "confirmed_meaning", "reward"],
                    ["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "ls20_seek",
        "version": "1.0.0",
        "depends_on": ["ls20_planning", "ls20_flash"],
        "area": "retina",
        "description": (
            "ls20 THE GAME IS COMMUNICATING (block 227000): the flash is a SIGN, not a fact "
            "with a built-in meaning. POSIT multiple candidate meanings (Posit Hypothesis nodes) "
            "from a GENERAL communicative vocabulary (sg_mint_posits); TEST by acting+residual "
            "(sg_want_test probe as-is -> sg_refute/sg_confirm, the 221/222 sd-loop applied to a "
            "sign); ACT on the confirmed meaning (sg_act_requirement -> transform_required -> "
            "sk_seek the only-other salient shape -> sk_pass). Controls: cycling (no interp), "
            "hardcode_reward (fixed wrong posit), no_test (posits but never tests). Guarded on "
            "game.seek_on==1 (default-OFF, byte-identical) + game.arm. Integer-native; no Rust; "
            "reuses shape_decode_loop (217) + onset (223) + quanta_navigation (220) + "
            "ls20_frustration (226) + the substrate's hypothesis mint/confirm/revise pattern."),
        "microtheory": {
            "name": "ls20_seek",
            "description": "The game is a communicative partner; its signs mean nothing until "
                           "interpreted. The agent posits candidate meanings, tests them by "
                           "acting, confirms the one whose prediction survives the residual, and "
                           "acts on it — seek the only-other salient shape, apply, pass. The "
                           "interpretation is discovered; every decision is a rule.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "seeds" / "ls20_seek.json"
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
