#!/usr/bin/env python3
"""AUTHOR the bigville rung-1 Bond update seed (block 277000).

One-off authoring tool (deletable; NOT agent runtime). Emits
`seeds/bigville_bond_update.json` -- the graph-native update DYNAMICS for the
directed, held Bond(A->B). Every DECISION (how an event / gossip / similarity /
proximity moves a bond) is a seed RULE composing existing DSL Terms only
(Attr / Plus / Times / Minus / Gt / Eq / And / IfThenElse / Abs / Argmax /
Neighbours) -- the exact palette of `af_choose_action` and `bd_mary_infers`.
ZERO new Rust.

The falsifier is uniform: EVERY update rule multiplies its delta by the bond's
`update_gain` and is guarded on `update_gain > 0`, so zeroing it freezes every
bond to its static seed prior (the old bare-label behavior) -- mirroring
`af_choose_action`'s `affect_gain` knob.
"""
from __future__ import annotations
import json
import os

SEED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "seeds", "bigville_bond_update.json")


# ---- Term constructors -----------------------------------------------------
def var(n):        return {"type": "Var", "name": n}
def lit(v):        return {"type": "Lit", "value": v}
def rawattr(v, k): return {"type": "Attr", "node": var(v), "key": k}
def a(v, k):       # missing-safe numeric attr: (attr + 0.0)
    return {"type": "Plus", "items": [rawattr(v, k), lit(0.0)]}
def plus(*xs):     return {"type": "Plus", "items": list(xs)}
def times(*xs):    return {"type": "Times", "items": list(xs)}
def minus(x, y):   return {"type": "Minus", "a": x, "b": y}
def gt(x, y):      return {"type": "Gt", "a": x, "b": y}
def eq(x, y):      return {"type": "Eq", "a": x, "b": y}
def andt(*xs):     return {"type": "And", "items": list(xs)}
def absv(x):       return {"type": "Abs", "arg": x}
def ite(c, t, o):  return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


def term(t):       # wrap a term as an effect value
    return {"__term__": t}


def argmax_gen(bond_var, key):
    """Attr `key` of the bond's Argmax DispositionGenerator -- the generator
    whose predicted harm rate best fits B's observed harm rate. Generalizes
    bd_mary_infers' held-codebook decode to a PER-BOND codebook (Neighbours over
    `has_gen`), so it is 'any A about any known B', not 'Mary about John'."""
    return {
        "type": "Attr",
        "node": {
            "type": "Argmax",
            "source": {"type": "Neighbours", "node": var(bond_var),
                       "edge_type": "has_gen", "any_type": False},
            "var_name": "g",
            "value": minus(lit(0.0),
                           absv(minus(a("g", "predicts_harm_rate"),
                                      a("g", "observed_harm_rate")))),
        },
        "key": key,
    }


GAIN_ON = gt(a("bond", "update_gain"), lit(0.0))   # the falsifier guard


def rules():
    R = []

    # ---- R1: belief slot -- the generalized ToM disposition decode ----------
    R.append({
        "name": "bond_belief_infer",
        "batch": False,
        "comment": "BELIEF SLOT (ToM, generalizes bd_mary_infers to any A about any "
                   "known B): decode B's observed harm signature against THIS bond's "
                   "held DispositionGenerator codebook (Argmax by -|predicts-observed|) "
                   "-> belief_disposition + belief_trust. Guarded on update_gain>0 "
                   "(falsifier) and re-armable via obs_armed.",
        "match": [["holder", "holds_bond", "bond"]],
        "where": andt(GAIN_ON, eq(a("bond", "obs_armed"), lit(1.0))),
        "effects": [
            # numeric disp_code (benign=+1 / hostile=-1) -- adapter maps to a name;
            # avoids setting a string attr from a term.
            ["set_attr", "bond", "belief_disp_code", term(argmax_gen("bond", "disp_code"))],
            ["set_attr", "bond", "belief_trust", term(argmax_gen("bond", "trust_level"))],
            ["set_attr", "bond", "obs_armed", 0.0],
        ],
    })

    # ---- R2: DIRECT positive event -- reciprocity raises --------------------
    dpos = times(a("bond", "update_gain"), a("bond", "pos_weight"), a("ev", "magnitude"))
    R.append({
        "name": "bond_event_benefit",
        "batch": False,
        "comment": "DIRECT dyadic update, reciprocity (A3): a positive appraised event by "
                   "B toward A raises gratitude/trust/affection/attraction and tie_strength "
                   "by update_gain*pos_weight*magnitude. One-shot per event (applied). The "
                   "has_event edge is the grounding trace (A6.3).",
        "match": [["holder", "holds_bond", "bond"], ["bond", "has_event", "ev"]],
        "where": andt(GAIN_ON, eq(a("ev", "applied"), lit(0.0)),
                      gt(a("ev", "valence"), lit(0.0))),
        "effects": [
            ["set_attr", "bond", "affect_gratitude", term(plus(a("bond", "affect_gratitude"), dpos))],
            ["set_attr", "bond", "affect_trust", term(plus(a("bond", "affect_trust"), dpos))],
            ["set_attr", "bond", "affect_affection",
             term(plus(a("bond", "affect_affection"), times(dpos, lit(0.5))))],
            ["set_attr", "bond", "attraction", term(plus(a("bond", "attraction"), dpos))],
            ["set_attr", "bond", "tie_strength",
             term(plus(a("bond", "tie_strength"),
                       times(a("bond", "update_gain"), a("ev", "magnitude"))))],
            ["set_attr", "ev", "applied", 1.0],
        ],
    })

    # ---- R3: DIRECT negative event -- negativity bias, re-appraisal ---------
    dneg = times(a("bond", "update_gain"), a("bond", "neg_weight"), a("ev", "magnitude"))
    R.append({
        "name": "bond_event_betrayal",
        "batch": False,
        "comment": "DIRECT dyadic update, negativity bias 'bad is stronger than good' "
                   "(A3): a negative appraised event (loan default, eviction) LOWERS "
                   "trust+attraction by update_gain*NEG_weight*magnitude (neg_weight > "
                   "pos_weight -- a TUNABLE knob, no magic ratio), raises "
                   "resentment/contempt/fear, drops belief_trust, and triggers a GLOBAL "
                   "re-appraisal (existing affection+gratitude scaled by "
                   "reappraise_factor<1, not a single decrement). One-shot per event.",
        "match": [["holder", "holds_bond", "bond"], ["bond", "has_event", "ev"]],
        "where": andt(GAIN_ON, eq(a("ev", "applied"), lit(0.0)),
                      gt(lit(0.0), a("ev", "valence"))),
        "effects": [
            ["set_attr", "bond", "affect_trust", term(minus(a("bond", "affect_trust"), dneg))],
            ["set_attr", "bond", "affect_resentment", term(plus(a("bond", "affect_resentment"), dneg))],
            ["set_attr", "bond", "affect_contempt",
             term(plus(a("bond", "affect_contempt"), times(dneg, lit(0.5))))],
            ["set_attr", "bond", "affect_fear",
             term(plus(a("bond", "affect_fear"), times(dneg, lit(0.25))))],
            ["set_attr", "bond", "attraction", term(minus(a("bond", "attraction"), dneg))],
            ["set_attr", "bond", "belief_trust",
             term(minus(a("bond", "belief_trust"), times(dneg, lit(0.5))))],
            # global re-appraisal: scale down the standing warm affect wholesale
            ["set_attr", "bond", "affect_affection",
             term(times(a("bond", "affect_affection"), a("bond", "reappraise_factor")))],
            ["set_attr", "bond", "affect_gratitude",
             term(times(a("bond", "affect_gratitude"), a("bond", "reappraise_factor")))],
            # betrayal ERODES the earned tie (creator sharpening 2: tie decays with
            # betrayal/neglect) -- but only partially, so a deep tie stays strong
            # enough to keep its band while affect goes negative (decoupling).
            ["set_attr", "bond", "tie_strength",
             term(minus(a("bond", "tie_strength"),
                        times(a("bond", "update_gain"), a("bond", "tie_erode"),
                              a("ev", "magnitude"))))],
            ["set_attr", "ev", "applied", 1.0],
        ],
    })

    # ---- R4: INDIRECT third-party gossip -- generalizes the reputation loop -
    gshift = times(a("bond", "update_gain"), a("g", "content_valence"),
                   a("g", "source_trust"), a("g", "gossip_weight"))
    R.append({
        "name": "bond_gossip_update",
        "batch": False,
        "comment": "INDIRECT third-party update (B4, generalizes bl_badmouth/"
                   "bl_townsfolk_opinion): C tells A about B; A revises Bond(A->B) "
                   "belief/affect/attraction by update_gain*content_valence*source_trust*"
                   "gossip_weight -- WITHOUT A directly experiencing B. source_trust = A's "
                   "trust in C (stamped by the adapter off Bond(A->C)); gossip is EVIDENCE "
                   "WEIGHTED BY THE SOURCE, never ground truth. One-shot per gossip.",
        "match": [["holder", "holds_bond", "bond"], ["bond", "has_gossip", "g"]],
        "where": andt(GAIN_ON, eq(a("g", "applied"), lit(0.0))),
        "effects": [
            ["set_attr", "bond", "belief_trust", term(plus(a("bond", "belief_trust"), gshift))],
            ["set_attr", "bond", "affect_trust",
             term(plus(a("bond", "affect_trust"), times(gshift, lit(0.5))))],
            ["set_attr", "bond", "attraction",
             term(plus(a("bond", "attraction"), times(gshift, lit(0.5))))],
            ["set_attr", "g", "applied", 1.0],
        ],
    })

    # ---- R5: similarity / homophily -> attraction ---------------------------
    sim = a("bond", "similarity")
    R.append({
        "name": "bond_similarity_attraction",
        "batch": False,
        "comment": "SIMILARITY/homophily (C1) -> attraction: attribute overlap raises the "
                   "approach pull; dissimilarity lowers it weighing SLIGHTLY MORE "
                   "(dissim_weight>sim_weight -- the defensible residue of the repulsion "
                   "hypothesis, NOT Rosenbaum's refuted strong form). One-shot per "
                   "arming (sim_armed).",
        "match": [["holder", "holds_bond", "bond"]],
        "where": andt(GAIN_ON, eq(a("bond", "sim_armed"), lit(1.0))),
        "effects": [
            ["set_attr", "bond", "attraction",
             term(plus(a("bond", "attraction"),
                       ite(gt(sim, lit(0.0)),
                           times(a("bond", "update_gain"), a("bond", "sim_weight"), sim),
                           times(a("bond", "update_gain"), a("bond", "dissim_weight"), sim))))],
            ["set_attr", "bond", "sim_armed", 0.0],
        ],
    })

    # ---- R6: proximity x mere-exposure -> tie_strength + attraction ---------
    drift = times(a("bond", "update_gain"), a("bond", "exposure_weight"), a("bond", "enc_delta"))
    R.append({
        "name": "bond_proximity_familiarity",
        "batch": False,
        "comment": "PROXIMITY x mere-exposure (C1, B7.1): benign co-presence frequency "
                   "drifts tie_strength and attraction up -- with the familiarity-breeds-"
                   "contempt caveat (Finkel 2015): exposure DEEPENS an already-negative "
                   "attraction. One-shot per arming (prox_armed).",
        "match": [["holder", "holds_bond", "bond"]],
        "where": andt(GAIN_ON, eq(a("bond", "prox_armed"), lit(1.0))),
        "effects": [
            ["set_attr", "bond", "tie_strength", term(plus(a("bond", "tie_strength"), drift))],
            ["set_attr", "bond", "attraction",
             term(plus(a("bond", "attraction"),
                       ite(gt(a("bond", "attraction"), lit(0.0)),
                           drift, minus(lit(0.0), drift))))],
            ["set_attr", "bond", "prox_armed", 0.0],
        ],
    })

    # ---- R7: band assignment -- an EARNED, graded tie-strength ladder, and
    # INDEPENDENT of the affect/attraction slots (both creator sharpenings):
    #   * EARNED (not genetic): band is derived PURELY from tie_strength, which the
    #     update rules BUILD from accumulated care / cohabitation / positive
    #     investment (R2, R6) and ERODE on betrayal (R3). Genetic relatedness is
    #     only a small starting tie_strength prior -- so a chosen/adopted/step tie
    #     can reach or exceed the strongest blood band, and a neglected blood tie
    #     withers to a weak band. "A step-brother can be MORE kin than kin."
    #   * INDEPENDENT of affect: attraction/resentment do NOT enter the band, so a
    #     deeply-bonded (high-tie_strength) family member who is RESENTED and
    #     AVOIDED keeps their strong band. "You do not need to LIKE your kin."
    # family(5)/intimate(4)/friend(3)/acquaintance(2)/consequential_stranger(1)/
    # stranger(0).
    ts = a("bond", "tie_strength")
    band = ite(gt(ts, lit(7.0)), lit(5.0),                       # family (strongest, earned)
           ite(gt(ts, lit(5.0)), lit(4.0),                       # intimate
            ite(gt(ts, lit(3.0)), lit(3.0),                      # friend
             ite(gt(ts, lit(1.5)), lit(2.0),                     # acquaintance
              ite(gt(ts, lit(0.4)), lit(1.0),                    # consequential_stranger
               lit(0.0))))))                                     # stranger
    R.append({
        "name": "bond_band_assign",
        "batch": False,
        "comment": "BAND (B2 spectrum) -- EARNED and INDEPENDENT of affect. Derived "
                   "PURELY from tie_strength (built by care/cohabitation R2/R6, eroded by "
                   "betrayal R3), NOT from a genetic edge: an adopted/chosen tie can reach "
                   "family(5) and a neglected blood tie withers -- 'a step-brother can be "
                   "MORE kin than kin'. Attraction/resentment do NOT enter the band, so a "
                   "resented+avoided deep tie keeps its strong band -- 'you do not need to "
                   "like your kin'. family(5)/intimate(4)/friend(3)/acquaintance(2)/"
                   "consequential_stranger(1)/stranger(0). Idempotent.",
        "match": [["holder", "holds_bond", "bond"]],
        "where": eq(a("bond", "update_gain"), a("bond", "update_gain")),   # trivially true
        "effects": [
            ["set_attr", "bond", "band_code", term(band)],
        ],
    })

    return R


def build():
    return {
        "id": "bigville_bond_update",
        "version": "1.0.0",
        "depends_on": [],
        "self_load_only": True,
        "description": (
            "BIGVILLE RUNG 1/3 (block 277000) -- THE HELD BOND update dynamics. "
            "Relationships move out of the sim as bare symmetric kin/hates edges and into "
            "the agent graph as a per-agent, DIRECTED, subjective, updatable Bond(A->B) "
            "with THREE dissociable slots (belief/ToM-decode generalizing bd_mary_infers; "
            "six signed relational emotions; one signed approach-avoidance attraction + a "
            "romantic sub-value) over a graded tie_strength/band. Seven bond_* rules: "
            "belief decode, reciprocity-up, betrayal-down-HARDER (negativity bias + global "
            "re-appraisal), third-party gossip weighted by source trust (generalizes "
            "bl_badmouth), homophily->attraction (dissimilarity weighs more), "
            "proximity->familiarity (contempt caveat), band assignment. Every DECISION is "
            "a rule composing existing Terms; the adapter only ingests/arms/reads. "
            "Falsifier: update_gain=0 freezes every bond to its static seed prior = the "
            "OLD bare-label behavior (mirrors af_choose_action's affect_gain). Composes "
            "existing DSL Terms only; ZERO new Rust. OFF by default (self_load_only)."),
        "nodes": [],
        "edges": [],
        "productions": [],
        "concepts": [],
        "rules": rules(),
    }


if __name__ == "__main__":
    with open(SEED_PATH, "w") as f:
        json.dump(build(), f, indent=1)
    print("wrote", SEED_PATH, "with", len(build()["rules"]), "rules")
