"""ls20_percell_seed — RUNG 222000: the PER-CELL live-mechanic model as graph
rules. Attacks 221000's honestly-flagged residual: its live model converged
TRIVIALLY because it modelled the aggregate CHANGE-MAGNITUDE (~52 cells/action);
predicting "~52" is always right and says NOTHING about the mechanic.

This seed builds a model that predicts WHICH cells change and to WHAT value:
each ACTION carries a `Hypothesis{key, region_colour, gen, k, dr, dc, subst}` --
a full 217000 `Transform{dim,delta}` the agent DISCOVERED (the sd-loop recognised
the observed object before->after) plus the region-selector (the object colour).
The adapter applies that graph-held Transform to the CURRENT frame to predict the
per-cell next frame; the residual is scored on the CHANGE-SET (never raw accuracy).

This is a SEED BUILDER (emits graph data -- the allowed Python under the
architecture rule, exactly like ls20_understanding_seed.py / ls20_planning_seed
.py). Every DECISION is a rule `where`-clause over graph state:

  CURIOSITY  — pc_probe_pick routes to the LEAST-observed ACTION (Argmin visits;
               NO win/goal term -- the 221000 uh_probe_pick pattern over actions).
  PREDICT    — pc_predict: the probed action's hypothesis `key` is the prediction
               (adapter presets "none" so an unmodelled action predicts a
               guaranteed residual = max surprise).
  MODEL      — pc_mint mints a Hypothesis carrying the DISCOVERED transform spec
               (the sd-loop's generator / k / shift deltas / subst, copied from
               the perception facts the adapter stamped); pc_confirm compresses
               (conf += 1) on a matched prediction; pc_revise overwrites on a
               surprise. This is the sd-loop predict-and-residual applied to the
               game's per-cell DYNAMICS.

The host adapter (worlds/arc_ls20_percell.py) does ONLY mechanical I/O: PERCEIVE
(the sd-loop recognises the observed object's transform; stamp obs_* facts),
APPLY (read the graph-held Transform and render the predicted frame -- like
221000's apply_transform/render_and_see), and MEASURE (change-set F1 vs the
truth -- a scored diagnostic, never fed to a decision). NO Python agent decision:
there is NO action->transform table anywhere; the map is minted from observation.

Every rule is guarded on `game.percell_on==1` (default-OFF; byte-identical to any
graph that does not set the flag), the arm (`game.arm=="percell"`), and the tick
PHASE (`game.phase`, the adapter's mechanical scheduler -- predict strictly
precedes observe strictly precedes advance). Integer-native; no Rust, no new Term
-- recognition reuses the EXISTING shape_decode_loop; these are ordinary
match+where+effect rules.
"""
from __future__ import annotations

import json
from pathlib import Path


# --- Term-tree builders (same vocabulary as ls20_understanding_seed.py) --------
def V(n):        return {"type": "Var", "name": n}
def A(n, k):     return {"type": "Attr", "node": V(n), "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def And(*x):     return {"type": "And", "items": list(x)}
def Not(a):      return {"type": "Not", "arg": a}
def Plus(a, b):  return {"type": "Plus", "items": [a, b]}


def Neigh(node, et):
    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}


def Exists(source, var="_x"):
    return {"type": "Exists", "source": source, "var_name": var,
            "predicate": {"type": "Lit", "value": True}}


def Argmin(source, var, value):
    return {"type": "Argmin", "source": source, "var_name": var,
            "value": value, "default": None}


def T(term):
    return {"__term__": term}


def _on():
    """Common guard: per-cell modelling switched ON for this game AND arm."""
    return And(Eq(A("g", "percell_on"), L(1.0)), Eq(A("g", "arm"), L("percell")))


def _phase(name):
    return Eq(A("g", "phase"), L(name))


# The full discovered transform spec the Hypothesis carries (copied from the
# adapter-stamped perception facts). key is the STABLE categorical mechanic (used
# by confirm/revise); the rest is the applicable Transform{dim,delta} the adapter
# reads back to render the per-cell prediction. region_colour is the region-
# selector (which object the action acts on -- discovered, not given).
def _spec_attrs():
    return {
        "key": T(A("g", "observed_key")),
        "region_colour": T(A("g", "obs_region")),
        "gen": T(A("g", "obs_gen")),
        "k": T(A("g", "obs_k")),
        "dr": T(A("g", "obs_dr")),
        "dc": T(A("g", "obs_dc")),
        "subst": T(A("g", "obs_subst")),
        "conf": 1.0,
        # confirmed_epoch = the observation this hyp was last touched. The adapter
        # bumps game.obs_epoch once per observation; confirm fires iff the hyp has
        # NOT already been touched this epoch, so conf counts true RE-predictions
        # (once per observation) instead of re-firing to the fixpoint cap.
        "confirmed_epoch": T(A("g", "obs_epoch")),
        "kind": "action_effect",
    }


def _rules():
    rules = []

    # -- CURIOSITY: probe the LEAST-observed action (Argmin visits) --------------
    # Under-modelled == under-observed == fewest visits. NO win/goal term: pure
    # novelty curiosity over the game's actions. One action per pick cycle.
    rules.append({
        "name": "pc_probe_pick",
        "comment": "CURIOSITY: probe the least-observed action (Argmin visits). "
                   "Novelty drive -- NO goal/win objective. One action per cycle.",
        "match": [["g", "has_action", "a"]],
        "where": And(_on(), _phase("pick"),
                     Not(Exists(Neigh(V("g"), "probing"), "p")),
                     Eq(V("a"), Argmin(Neigh(V("g"), "has_action"), "C",
                                       A("C", "visits")))),
        "effects": [["add_edge", "g", "probing", "a"],
                    ["set_attr", "g", "probe_action", T(A("a", "name"))]],
    })

    # -- ATTEND (live path): the ENVIRONMENT dictates the action -----------------
    # On the live game the action is chosen by the world (available_actions), not
    # by curiosity. This rule points `probing` at the named action so the same
    # predict/observe/advance machinery runs. (Offline uses pc_probe_pick instead;
    # both just set the probing attention edge.)
    rules.append({
        "name": "pc_attend",
        "comment": "LIVE: attend the environment-dictated action (probing edge to "
                   "the action whose name == game.attend_action). One at a time.",
        "match": [["g", "has_action", "a"]],
        "where": And(_on(), _phase("attend"),
                     Not(Exists(Neigh(V("g"), "probing"), "p")),
                     Eq(A("a", "name"), A("g", "attend_action"))),
        "effects": [["add_edge", "g", "probing", "a"]],
    })

    # -- PREDICT: the model's expectation for the probed action ------------------
    # If the probed action already has a hypothesis, its `key` IS the prediction.
    # (Adapter presets game.predicted_key="none" so an unmodelled action predicts
    # "none" -> a guaranteed residual = max surprise.)
    rules.append({
        "name": "pc_predict",
        "comment": "TEST(predict): the probed action's hypothesis key is the "
                   "predicted effect. Unmodelled -> stays 'none' (adapter preset).",
        "match": [["g", "probing", "a"], ["a", "has_hyp", "h"]],
        "where": And(_on(), _phase("predict")),
        "effects": [["set_attr", "g", "predicted_key", T(A("h", "key"))]],
    })

    # -- RESIDUAL -> MINT: an action with NO hypothesis, observed for the first ---
    # time -> mint a Hypothesis carrying the DISCOVERED transform spec. The
    # surprise (predicted 'none' != observed) is what mints it.
    rules.append({
        "name": "pc_mint",
        "comment": "RESIDUAL->MODEL: first observation of an unmodelled action "
                   "mints a Hypothesis carrying the sd-loop-recognised Transform "
                   "spec. add_node_if_absent guards against a double-mint.",
        "match": [["g", "probing", "a"]],
        "where": And(_on(), _phase("observe"),
                     Not(Exists(Neigh(V("a"), "has_hyp"), "h"))),
        "effects": [["add_node_if_absent", "hyp", "Hypothesis", _spec_attrs()],
                    ["add_edge", "a", "has_hyp", "hyp"],
                    ["add_edge", "g", "minted", "hyp"]],
    })

    # -- RESIDUAL -> CONFIRM: prediction matched observation ---------------------
    # -> COMPRESS the model (conf += 1). A confirmed hypothesis (conf>=2) is an
    # action whose per-cell Transform the agent correctly RE-predicted.
    rules.append({
        "name": "pc_confirm",
        "comment": "RESIDUAL->COMPRESS: predicted key == observed key -> the "
                   "hypothesis is confirmed (conf += 1). Zero-residual = learning.",
        "match": [["g", "probing", "a"], ["a", "has_hyp", "h"]],
        "where": And(_on(), _phase("observe"),
                     Eq(A("h", "key"), A("g", "observed_key")),
                     Not(Eq(A("h", "confirmed_epoch"), A("g", "obs_epoch")))),
        "effects": [["set_attr", "h", "conf", T(Plus(A("h", "conf"), L(1.0)))],
                    ["set_attr", "h", "confirmed_epoch", T(A("g", "obs_epoch"))]],
    })

    # -- RESIDUAL -> REVISE: prediction WRONG -> revise the whole spec -----------
    rules.append({
        "name": "pc_revise",
        "comment": "RESIDUAL->REVISE: predicted key != observed key -> the "
                   "hypothesis was wrong; revise to the observed Transform spec, "
                   "reset conf.",
        "match": [["g", "probing", "a"], ["a", "has_hyp", "h"]],
        "where": And(_on(), _phase("observe"),
                     Not(Eq(A("h", "key"), A("g", "observed_key")))),
        "effects": [["set_attr", "h", "key", T(A("g", "observed_key"))],
                    ["set_attr", "h", "region_colour", T(A("g", "obs_region"))],
                    ["set_attr", "h", "gen", T(A("g", "obs_gen"))],
                    ["set_attr", "h", "k", T(A("g", "obs_k"))],
                    ["set_attr", "h", "dr", T(A("g", "obs_dr"))],
                    ["set_attr", "h", "dc", T(A("g", "obs_dc"))],
                    ["set_attr", "h", "subst", T(A("g", "obs_subst"))],
                    ["set_attr", "h", "conf", 1.0],
                    ["set_attr", "h", "confirmed_epoch", T(A("g", "obs_epoch"))]],
    })

    # -- ADVANCE: count the visit, release the probe -----------------------------
    rules.append({
        "name": "pc_advance",
        "comment": "advance the investigation: visits += 1, release the probing "
                   "edge so the next Argmin(visits) picks a fresher action.",
        "match": [["g", "probing", "a"]],
        "where": And(_on(), _phase("advance")),
        "effects": [["set_attr", "a", "visits", T(Plus(A("a", "visits"), L(1.0)))],
                    ["del_edge", "g", "probing", "a"]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "ls20_percell",
        "version": "1.0.0",
        "depends_on": ["shape_decode_loop"],
        "area": "retina",
        "description": (
            "ls20 PER-CELL live mechanic (block 222000): the richer model that "
            "attacks 221000's trivially-converging aggregate-count residual. Each "
            "ACTION carries a Hypothesis{key, region_colour, gen, k, dr, dc, "
            "subst} -- the full 217000 Transform{dim,delta} the agent DISCOVERED "
            "by sd-loop recognition of the observed object before->after, plus the "
            "region-selector (object colour). pc_probe_pick routes to the least-"
            "observed action (Argmin visits, NO win term); pc_predict/pc_mint/"
            "pc_confirm/pc_revise grow the model by predict-and-residual. The "
            "adapter applies the graph-held Transform to the CURRENT frame to "
            "predict the per-cell next frame; the residual is scored on the "
            "CHANGE-SET (which cells change to what value), NEVER raw accuracy. NO "
            "action->transform table -- the map is minted from observation. "
            "Guarded on percell_on==1 (default-OFF, byte-identical otherwise), the "
            "arm, and the tick phase. Integer-native; no Rust; reuses the existing "
            "shape_decode_loop."),
        "microtheory": {
            "name": "ls20_percell",
            "description": "Predict WHICH cells change and to WHAT value: action x "
                           "current-frame -> per-cell next-frame. The mechanic is a "
                           "discovered per-action Transform applied to the current "
                           "frame; surprise is the per-cell change-set residual.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = (Path(path) if path else
         Path(__file__).resolve().parent.parent / "seeds" / "ls20_percell.json")
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
