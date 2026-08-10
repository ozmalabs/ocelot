"""remote_causal_ground_seed — RUNG 229000: OBSERVE-AND-GROUND remote causality.

THE CORRECTION (owner). Block 228000 proved remote causation, but it established
the causal link by running a probe WORLD-MODEL to SIMULATE the act-vs-no-op
counterfactual (`eff_act`/`eff_noop` from re-running a deterministic world under
(do) vs (no-op)). That is model-based and works only OFFLINE where you can REWIND.
On the REAL game there is NO rewind, so 228's live path ran the model-probe, got
`eff_act=0`, and grounded NOTHING.

Owner: "What it needs to do is OBSERVE the causality and ADD that grounded
understanding to the graph in the context, so it KNOWS that the cross causes
rotation." So the causal link must be GROUNDED FROM REAL OBSERVATION:

  - The agent interacts with the cross FOR REAL, OBSERVES the actual before->after
    in the real frames (perception — the 216/217 pixel eye / real-frame onset
    stream), and if the remote thing (its shape) rotated, MINTS a persistent
    grounded causal fact `causes(cross, rotation)` into the graph.
  - The no-op / negative evidence comes from the NATURAL TIMELINE — real timesteps
    where the agent did NOT interact AND the remote thing did NOT change — NOT a
    simulated counterfactual. That is what refutes coincidence.
  - Once grounded, the fact PERSISTS and the agent KNOWS it — and acts on knowing.

This is a SEED BUILDER (emits graph data — the allowed Python under the
architecture rule). It contains NO agent decision in Python: every decision (ground
the fact from the observed effect; refuse when the natural timeline shows
spontaneous change; act on the grounded fact; pass) is a rule `where`-clause over
graph state. The host adapter (worlds/remote_causal_ground.py) only writes the
OBSERVED perception facts (per-step Observation nodes: interact + remote_changed +
cause_id + effect_kind, all observed from real before->after), steps toward the
rule-chosen waypoint, and applies the effect on operate.

THE OBSERVATION STREAM IS THE NATURAL TIMELINE. Each real step the adapter mints an
`Observation{interact, remote_changed, cause_id, effect_kind}` node (edge
`g -has_obs-> obs`). `interact` and `remote_changed` are OBSERVED — never simulated:
`remote_changed` is 1 iff the real before->after perception showed a DISTAL change.
The whole stream of Observations is the natural timeline as first-class graph data.

THE RULES:

  GROUND (rcg_ground) — THE HEADLINE. An Observation with interact==1 AND
    remote_changed==1 (a real interact->distal-change), AND NO Observation in the
    natural timeline with interact==0 AND remote_changed==1 (nothing changed
    spontaneously — the natural-timeline no-op / negative evidence), AND no
    CausalFact yet for this cause->effect -> MINT
    CausalFact{cause, effect, status:"grounded", source:"observation"} + edge
    `g -has_causal_fact-> cf` + `causes` edge from the cause object to the fact. The
    fact PERSISTS (node + edges; the Not-Exists guard makes it mint-once).

  KNOWS-AND-ACTS (rcg_knows_and_acts -> rcg_pass) — with a grounded CausalFact for
    the cause object and not-yet-matching, the agent READS the fact, seeks the cause
    object to OPERATE it (the action that furthers the grounded knowledge), obtains
    the effect, and passes. Without a grounded fact it cannot.

THE CONTROLS (arms):
  * no_natural_timeline — grounds on any co-observed interact->change, IGNORING the
    natural-timeline no-op -> false-positive on Family B (coincidence).
  * blind             — its Observations always have remote_changed==0 (never
    observes the effect) -> never grounds -> misses Family A.
  * (the 228 sim_probe path is the model-probe contrast, driven from the 228 rules.)

Domain-agnostic: the rules name NO ls20/doom/cross/lever/rotation constant — the
`effect` kind is carried through from the OBSERVED Observation attr. Guarded on
game.ground_on==1 (default-OFF; byte-identical to any graph that does not set the
flag) + game.arm. Integer-native. No Rust, no new Term — reuses the 227
posit/confirm pattern, the 210 operate seek/use, the 220 nav step.
"""
from __future__ import annotations

import json
from pathlib import Path


# --- Term-tree builders (same vocabulary as domains/remote_causal_seed.py) -----
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
    return And(Eq(A("g", "ground_on"), L(1.0)), Eq(A("g", "arm"), L(arm)))


def _enabled_any(*arms):
    return And(Eq(A("g", "ground_on"), L(1.0)),
               Or(*[Eq(A("g", "arm"), L(a)) for a in arms]))


# --------------------------------------------------------------------------
# THE RULES — observe-and-ground remote causality.
# --------------------------------------------------------------------------
def _rules():
    rules = []

    # A grounded CausalFact minted from ONE observed interact->distal-change,
    # carrying the OBSERVED cause id + effect kind. Mint-once (Not Exists guard).
    def _ground_effects():
        return [
            ["add_node", "cf", "CausalFact", {
                "cause": T(A("obs", "cause_id")),
                "effect": T(A("obs", "effect_kind")),
                "status": T(L("grounded")),
                "source": T(L("observation")),
            }],
            ["add_edge", "g", "has_causal_fact", "cf"],
            ["add_edge", "o", "causes", "cf"],
            ["set_attr", "g", "grounded", 1.0],
            ["set_attr", "g", "grounded_cause", T(A("obs", "cause_id"))],
            ["set_attr", "g", "grounded_effect", T(A("obs", "effect_kind"))],
        ]

    # ---- GROUND (HEADLINE) — the OBSERVATION path ------------------------
    # An Observation that OBSERVED interact==1 AND remote_changed==1, whose cause
    # object exists, with NO natural-timeline Observation that observed a change
    # WITHOUT interaction (interact==0 AND remote_changed==1 — spontaneous), and
    # no CausalFact yet for this cause -> GROUND the fact from the observed effect.
    rules.append({
        "name": "rcg_ground",
        "comment": "GROUND (headline): a REAL observed interact->distal-change + a clean "
                   "natural timeline (no spontaneous change observed) -> mint a persistent "
                   "grounded causes(cause,effect) fact FROM the observed effect. Not simulated.",
        "match": [["g", "has_obs", "obs"], ["g", "has_object", "o"]],
        "where": And(_enabled_any("observe"),
                     Eq(A("obs", "interact"), L(1.0)),
                     Eq(A("obs", "remote_changed"), L(1.0)),
                     Eq(A("o", "obj_id"), A("obs", "cause_id")),
                     # NATURAL-TIMELINE NO-OP: refuse if anything changed with no interaction.
                     Not(_exists("g", "has_obs", "o2",
                                 And(Eq(A("o2", "interact"), L(0.0)),
                                     Eq(A("o2", "remote_changed"), L(1.0))))),
                     # mint-once
                     Not(_exists("g", "has_causal_fact", "cf2",
                                 Eq(A("cf2", "cause"), A("obs", "cause_id"))))),
        "effects": _ground_effects(),
    })

    # ---- GROUND — no_natural_timeline CONTROL ----------------------------
    # Ignores the natural-timeline no-op: grounds on ANY co-observed interact->change
    # -> false-positive on Family B (a spontaneously-changing remote thing).
    rules.append({
        "name": "rcg_ground_no_timeline",
        "comment": "CONTROL (no_natural_timeline): ground on ANY co-observed interact->change, "
                   "IGNORING the natural-timeline no-op -> confabulates on coincidence (Family B).",
        "match": [["g", "has_obs", "obs"], ["g", "has_object", "o"]],
        "where": And(_enabled("no_natural_timeline"),
                     Eq(A("obs", "interact"), L(1.0)),
                     Eq(A("obs", "remote_changed"), L(1.0)),
                     Eq(A("o", "obj_id"), A("obs", "cause_id")),
                     Not(_exists("g", "has_causal_fact", "cf2",
                                 Eq(A("cf2", "cause"), A("obs", "cause_id"))))),
        "effects": _ground_effects(),
    })

    # ---- KNOWS-AND-ACTS — read the grounded fact and seek the cause ------
    # A grounded CausalFact for an object + still not matching -> seek that object to
    # OPERATE it (the action that furthers the grounded knowledge). Joins the fact to
    # its object by cause==obj_id. All arms may act on whatever they grounded.
    rules.append({
        "name": "rcg_knows_and_acts",
        "comment": "KNOWS-AND-ACTS: a grounded causes(cause,effect) fact + not matching -> read "
                   "it and seek the cause object to operate it (act on knowing).",
        "match": [["g", "has_causal_fact", "cf"], ["g", "has_object", "o"]],
        "where": And(_enabled_any("observe", "no_natural_timeline", "blind"),
                     Eq(A("cf", "status"), L("grounded")),
                     Eq(A("cf", "cause"), A("o", "obj_id")),
                     Eq(A("g", "symbol_matches_goal"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "object"],
                    ["set_attr", "g", "wp_r", T(A("o", "r"))],
                    ["set_attr", "g", "wp_c", T(A("o", "c"))],
                    ["set_attr", "g", "seek_obj", T(A("o", "obj_id"))],
                    ["set_attr", "g", "act_on_grounded", 1.0]],
    })

    # ---- PASS ------------------------------------------------------------
    rules.append({
        "name": "rcg_pass",
        "comment": "PASS: the carried thing matches the requirement -> route to the block and pass.",
        "match": [["g", "has_ping", "p"]],
        "where": And(_enabled_any("observe", "no_natural_timeline", "blind"),
                     Eq(A("g", "symbol_matches_goal"), L(1.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "remote_causal_ground",
        "version": "1.0.0",
        "depends_on": [],
        "area": "retina",
        "description": (
            "OBSERVE-AND-GROUND remote causality (block 229000): the 228 correction. Ground "
            "causes(cross,rotation) from the REAL observed before->after (perception), NOT a "
            "simulated counterfactual. Per real step the adapter mints an Observation{interact, "
            "remote_changed, cause_id, effect_kind} (all OBSERVED) — the stream IS the natural "
            "timeline. rcg_ground mints a persistent CausalFact{cause,effect,status:grounded, "
            "source:observation} + `causes` edge iff a real interact->distal-change is observed "
            "AND no Observation shows a change without interaction (the natural-timeline no-op) "
            "AND no fact exists yet. rcg_knows_and_acts reads the grounded fact and seeks the "
            "cause to operate it; rcg_pass passes. Controls: no_natural_timeline (ignores the "
            "no-op -> confabulates on coincidence), blind (never observes the effect -> never "
            "grounds). Domain-agnostic (effect kind carried from the OBSERVED attr; no "
            "cross/rotation constant). Guarded on game.ground_on==1 (default-OFF, byte-identical) "
            "+ game.arm. Integer-native; no Rust; reuses 216/217 perception + 227 posit + 210 "
            "operate + 220 nav."),
        "microtheory": {
            "name": "remote_causal_ground",
            "description": "A remote-causal link is GROUNDED FROM OBSERVATION: the agent "
                           "interacts for real, OBSERVES the actual before->after remote change, "
                           "and mints a persistent grounded causes(cause,effect) fact — refusing "
                           "when the natural timeline shows the remote thing changing on its own. "
                           "The grounded fact persists and the agent acts on knowing it. Every "
                           "decision is a rule; grounding is perception -> graph write.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "seeds" / "remote_causal_ground.json"
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
