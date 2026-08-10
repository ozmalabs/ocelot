"""ls20_understanding_seed — RUNG 221000: UNDERSTANDING the ls20 mechanic as
graph rules. Winning is a SIDE EFFECT of understanding, never the objective.

Owner steer (non-negotiable): *"Not win condition — winning is a side effect of
understanding. The true victory is knowledge."* The objective is to UNDERSTAND
the game's mechanic (which station applies which transform; the terminal
predicate), NOT to reach the win state. This seed is the project's own curiosity
drive + compression-as-quality + predict-and-residual (the sd-loop / order-N)
applied to the LIVE game DYNAMICS.

This is a SEED BUILDER (emits graph data — the allowed Python under the
architecture rule, exactly like ls20_planning_seed.py). Every DECISION is a rule
`where`-clause over graph state. The host adapter (worlds/arc_ls20_understanding
.py) only writes PERCEPTION facts (the transform the graph-native 217000 sd-loop
recognised at a probed station; whether the carried symbol matches the goal) and
world PHYSICS (apply a station's transform; step toward the rule-chosen waypoint;
score at the goal). NO Python agent decision.

THE UNDERSTANDING LOOP (assembled from existing machinery, NOT a new model):

  PERCEIVE   — the 216000 pixel-eye sees the probe/goal; the 217000 sd-loop
               (TransformDecode/DimInfer) RECOGNISES the transform a station
               applies (before->after). Graph-native, dimension-arbitrary.
  MODEL      — a station's effect is a `Hypothesis{key, conf}` minted as graph
               data (the qf_* `msp CLOSED -> mint-Hypothesis` precedent). Each
               hypothesis carries a PREDICTION (its `key`).
  CURIOSITY  — the drive routes to the LEAST-modelled station (Argmin visits —
               under-modelled = under-observed), the ae_frontier_goal Argmax
               precedent, NOT to the goal. There is NO win/goal-reach objective
               anywhere in the `uh_*` drive rules (source-audited).
  TEST       — predict the station's effect from the model (uh_predict), OBSERVE
               the actual effect, the RESIDUAL is the surprise. A confirmed
               prediction COMPRESSES the model (uh_confirm: conf += 1); a surprise
               MINTS (uh_mint) or REVISES (uh_revise) a hypothesis. This is the
               sd-loop predict-and-residual applied to the game's dynamics.
  DELIVER    — winning FALLS OUT: uh_deliver_route consults the LEARNED model to
               find the station whose hypothesis applies the required transform,
               routes there, applies, delivers. Winning is logged downstream of
               model-convergence; it is NEVER an objective function.

THE CONTROL (the arm that EARNS the reframe): `win_bound` (wb_*) optimises
goal-reach directly — wb_probe_pick picks the station NEAREST THE GOAL (the
win-objective), applies it, delivers if it happens to match. It builds NO
persistent model, so it re-searches every level (overfits per level). It is the
labelled baseline the understanding arm is measured against; the win-objective
lives ONLY in the wb_* control rules, never in the uh_* drive.

Every rule is guarded on `game.understand_on==1` (default-OFF; byte-identical to
any graph that does not set the flag) and on the arm (`game.arm`) and the tick
PHASE (`game.phase`, set by the adapter's mechanical tick scheduler so predict
strictly precedes observe strictly precedes advance — no intra-fixpoint race).
Integer-native; no Rust, no new Term — recognition reuses the EXISTING
shape_decode_loop; these are ordinary match+where+effect rules.
"""
from __future__ import annotations

import json
from pathlib import Path


# --- Term-tree builders (same vocabulary as ls20_planning_seed.py) ------------
def V(n):        return {"type": "Var", "name": n}
def A(n, k):     return {"type": "Attr", "node": V(n), "key": k}
def L(v):        return {"type": "Lit", "value": v}
def Eq(a, b):    return {"type": "Eq", "a": a, "b": b}
def And(*x):     return {"type": "And", "items": list(x)}
def Not(a):      return {"type": "Not", "arg": a}
def Plus(a, b):  return {"type": "Plus", "items": [a, b]}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Abs(a):      return {"type": "Abs", "arg": a}


def Neigh(node, et):
    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}


def Exists(source, var="_x"):
    return {"type": "Exists", "source": source, "var_name": var,
            "predicate": {"type": "Lit", "value": True}}


def Filter(source, var, pred):
    return {"type": "Filter", "source": source, "var_name": var, "predicate": pred}


def Argmin(source, var, value):
    return {"type": "Argmin", "source": source, "var_name": var,
            "value": value, "default": None}


def T(term):
    """Wrap a Term so it is EVALUATED in an effect's attr value (the __term__
    convention ls20_planning_seed uses)."""
    return {"__term__": term}


def _on(arm):
    """Common guard: understanding switched ON for this game AND this arm."""
    return And(Eq(A("g", "understand_on"), L(1.0)), Eq(A("g", "arm"), L(arm)))


def _phase(name):
    return Eq(A("g", "phase"), L(name))


# --------------------------------------------------------------------------
# THE RULES — perceive / curiosity / predict / residual / model / deliver.
# --------------------------------------------------------------------------
def _rules():
    rules = []

    # -- CURIOSITY DRIVE (understand): route to the LEAST-modelled station -------
    # Under-modelled == under-observed == fewest visits. Argmin(visits) over the
    # game's stations (the ae_frontier_goal Argmax-by-interest precedent, here an
    # Argmin-by-novelty). NO distance-to-goal, NO win term: pure novelty curiosity.
    # Binds exactly the station that IS the Argmin (one probe per pick cycle).
    rules.append({
        "name": "uh_probe_pick",
        "comment": "CURIOSITY: probe the least-observed station (Argmin visits). "
                   "Novelty drive -- NO goal/win objective. One station per pick cycle.",
        "match": [["g", "has_station", "s"]],
        "where": And(_on("understand"), _phase("pick"),
                     Not(Exists(Neigh(V("g"), "probing"), "p")),
                     Eq(V("s"), Argmin(Neigh(V("g"), "has_station"), "C",
                                       A("C", "visits")))),
        "effects": [["add_edge", "g", "probing", "s"],
                    ["set_attr", "g", "probe_r", T(A("s", "r"))],
                    ["set_attr", "g", "probe_c", T(A("s", "c"))]],
    })

    # -- PREDICT (understand): the model's expectation for the probed station ----
    # If the probed station already has a hypothesis, its `key` IS the prediction.
    # (The adapter presets game.predicted_key="none" before this phase, so an
    # unmodelled station predicts "none" -> a guaranteed residual = max surprise.)
    rules.append({
        "name": "uh_predict",
        "comment": "TEST(predict): the probed station's hypothesis key is the "
                   "predicted effect. Unmodelled -> stays 'none' (adapter preset).",
        "match": [["g", "probing", "s"], ["s", "has_hyp", "h"]],
        "where": And(_on("understand"), _phase("predict")),
        "effects": [["set_attr", "g", "predicted_key", T(A("h", "key"))]],
    })

    # -- RESIDUAL -> MINT (understand): a station with NO hypothesis, observed ----
    # for the first time -> mint Hypothesis{key=observed, conf=1}. The surprise
    # (predicted 'none' != observed) is what mints it. (msp/qf mint-Hypothesis.)
    rules.append({
        "name": "uh_mint",
        "comment": "RESIDUAL->MODEL: first observation of an unmodelled station "
                   "mints a Hypothesis carrying the recognised transform as its "
                   "prediction. add_node_if_absent guards against a double-mint.",
        "match": [["g", "probing", "s"]],
        "where": And(_on("understand"), _phase("observe"),
                     Not(Exists(Neigh(V("s"), "has_hyp"), "h"))),
        "effects": [["add_node_if_absent", "hyp", "Hypothesis",
                     {"key": T(A("g", "observed_key")), "conf": 1.0,
                      "kind": "station_effect"}],
                    ["add_edge", "s", "has_hyp", "hyp"],
                    ["add_edge", "g", "minted", "hyp"]],
    })

    # -- RESIDUAL -> CONFIRM (understand): prediction matched observation --------
    # -> COMPRESS the model (conf += 1). A confirmed hypothesis (conf>=2) is a
    # station whose transform the agent has correctly RE-predicted.
    rules.append({
        "name": "uh_confirm",
        "comment": "RESIDUAL->COMPRESS: predicted key == observed key -> the "
                   "hypothesis is confirmed (conf += 1). Zero-residual = learning.",
        "match": [["g", "probing", "s"], ["s", "has_hyp", "h"]],
        "where": And(_on("understand"), _phase("observe"),
                     Eq(A("h", "key"), A("g", "observed_key"))),
        "effects": [["set_attr", "h", "conf", T(Plus(A("h", "conf"), L(1.0)))]],
    })

    # -- RESIDUAL -> REVISE (understand): prediction WRONG -> revise -------------
    # A held hypothesis contradicted by observation (should not happen for a clean
    # deterministic station, but is the honest surprise path) -> overwrite the key
    # and reset conf. This is the general revise-on-surprise the sd-loop does.
    rules.append({
        "name": "uh_revise",
        "comment": "RESIDUAL->REVISE: predicted key != observed key -> the "
                   "hypothesis was wrong; revise to the observed key, reset conf.",
        "match": [["g", "probing", "s"], ["s", "has_hyp", "h"]],
        "where": And(_on("understand"), _phase("observe"),
                     Not(Eq(A("h", "key"), A("g", "observed_key")))),
        "effects": [["set_attr", "h", "key", T(A("g", "observed_key"))],
                    ["set_attr", "h", "conf", 1.0]],
    })

    # -- ADVANCE (understand): count the visit, release the probe ----------------
    # Separate phase so the probing edge survives predict+observe, then is removed
    # so the next pick cycle's Argmin moves on. Increment visits (the curiosity key).
    rules.append({
        "name": "uh_advance",
        "comment": "advance the investigation: visits += 1, release the probing "
                   "edge so the next Argmin(visits) picks a fresher station.",
        "match": [["g", "probing", "s"]],
        "where": And(_on("understand"), _phase("advance")),
        "effects": [["set_attr", "s", "visits", T(Plus(A("s", "visits"), L(1.0)))],
                    ["del_edge", "g", "probing", "s"]],
    })

    # -- DELIVER (understand): winning FALLS OUT of the model --------------------
    # Consult the LEARNED model: the station whose hypothesis key == the recognised
    # required transform is the one to use. Route to it; the adapter applies it and
    # then delivers. This is understanding -> winning, NOT a win objective: the
    # station is chosen by MODEL MATCH (h.key == req_key), never by goal proximity.
    rules.append({
        "name": "uh_deliver_route",
        "comment": "WIN AS SIDE EFFECT: the station the LEARNED model says applies "
                   "the required transform (h.key == req_key). Model lookup, not search.",
        "match": [["g", "has_station", "s"], ["s", "has_hyp", "h"]],
        "where": And(_on("understand"), _phase("deliver"),
                     Eq(A("g", "symbol_matches_goal"), L(0.0)),
                     Eq(A("h", "key"), A("g", "req_key")),
                     Eq(A("s", "used"), L(0.0))),
        "effects": [["set_attr", "g", "waypoint", "station"],
                    ["set_attr", "g", "wp_r", T(A("s", "r"))],
                    ["set_attr", "g", "wp_c", T(A("s", "c"))]],
    })
    rules.append({
        "name": "uh_deliver_goal",
        "comment": "WIN AS SIDE EFFECT: carried matches goal -> route to the goal "
                   "cell and deliver (the terminal act of the understood model).",
        "match": [["g", "has_ping", "p"]],
        "where": And(_on("understand"), _phase("deliver"),
                     Eq(A("g", "symbol_matches_goal"), L(1.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })

    # -- LEVEL START: the agent clears its OWN stale attention (both arms) -------
    # When the WORLD presents a new level (phase==level_start), the agent releases
    # any lingering `probing` attention edge itself -- the model (hypotheses)
    # persists, only the per-tick attention is cleared. This is the agent resetting
    # its OWN working state in response to a world observation, never a Python reset.
    rules.append({
        "name": "uh_level_start",
        "comment": "on a new level the agent releases its stale attention; the "
                   "learned model persists (understanding carries across levels).",
        "match": [["g", "probing", "s"]],
        "where": And(_on("understand"), _phase("level_start")),
        "effects": [["del_edge", "g", "probing", "s"]],
    })
    rules.append({
        "name": "wb_level_start",
        "comment": "CONTROL: on a new level the win-bound agent releases its "
                   "attention (it holds no model to carry -- it re-searches).",
        "match": [["g", "probing", "s"]],
        "where": And(_on("win_bound"), _phase("level_start")),
        "effects": [["del_edge", "g", "probing", "s"]],
    })

    # -- THE CONTROL (win_bound): optimise GOAL-REACH, no model -----------------
    # wb_probe_pick picks the UNTRIED station NEAREST THE GOAL (Manhattan) -- the
    # win-objective, by design, to be beaten. No hypotheses minted: nothing is
    # learned, so every level is re-searched from scratch (overfits per level).
    rules.append({
        "name": "wb_probe_pick",
        "comment": "CONTROL (win-bound baseline): pick the unvisited station NEAREST "
                   "THE GOAL (the win-objective). No model -> re-search every level.",
        "match": [["g", "has_station", "s"]],
        "where": And(_on("win_bound"), _phase("pick"),
                     Not(Exists(Neigh(V("g"), "probing"), "p")),
                     Eq(A("s", "visited"), L(0.0)),
                     Eq(V("s"),
                        Argmin(Filter(Neigh(V("g"), "has_station"), "C",
                                      Eq(A("C", "visited"), L(0.0))), "C",
                               Plus(Abs(Minus(A("C", "r"), A("g", "goal_r"))),
                                    Abs(Minus(A("C", "c"), A("g", "goal_c"))))))),
        "effects": [["add_edge", "g", "probing", "s"],
                    ["set_attr", "g", "waypoint", "station"],
                    ["set_attr", "g", "wp_r", T(A("s", "r"))],
                    ["set_attr", "g", "wp_c", T(A("s", "c"))]],
    })
    rules.append({
        "name": "wb_deliver_goal",
        "comment": "CONTROL: carried matches goal -> deliver (win-bound terminal).",
        "match": [["g", "has_ping", "p"]],
        "where": And(_on("win_bound"), _phase("deliver"),
                     Eq(A("g", "symbol_matches_goal"), L(1.0))),
        "effects": [["set_attr", "g", "waypoint", "goal"],
                    ["set_attr", "g", "wp_r", T(A("g", "goal_r"))],
                    ["set_attr", "g", "wp_c", T(A("g", "goal_c"))]],
    })
    rules.append({
        "name": "wb_advance",
        "comment": "CONTROL: mark the station visited (win-bound learns nothing "
                   "persistent), release the probe so the next-nearest is picked.",
        "match": [["g", "probing", "s"]],
        "where": And(_on("win_bound"), _phase("advance")),
        "effects": [["set_attr", "s", "visited", 1.0],
                    ["del_edge", "g", "probing", "s"]],
    })

    return rules


RULES = _rules()


def manifest():
    return {
        "id": "ls20_understanding",
        "version": "1.0.0",
        "depends_on": ["shape_decode_loop"],
        "area": "retina",
        "description": (
            "ls20 UNDERSTANDING (block 221000): winning is a SIDE EFFECT of "
            "understanding. The curiosity drive (uh_probe_pick, Argmin visits -- "
            "least-modelled first, NO goal/win term) routes the agent to probe "
            "stations; the 217000 sd-loop recognises each station's transform; "
            "uh_mint/uh_confirm/uh_revise build a station->transform MODEL by "
            "predict-and-residual (uh_predict is the prediction, the residual is "
            "the surprise); uh_deliver_route consults the LEARNED model so winning "
            "FALLS OUT. The win_bound (wb_*) control optimises goal-reach directly "
            "(Argmin distance-to-goal) with no persistent model -- the labelled "
            "baseline the reframe is measured against. Guarded on understand_on==1 "
            "(default-OFF, byte-identical otherwise), the arm, and the tick phase. "
            "Integer-native; no Rust; reuses the existing shape_decode_loop."),
        "microtheory": {
            "name": "ls20_understanding",
            "description": "Understand the mechanic; winning is downstream. "
                           "Curiosity routes to the under-modelled; predict-and-"
                           "residual grows the model; the goal is never an "
                           "objective function -- only a thing to model and, once "
                           "understood, to satisfy as a consequence.",
        },
        "nodes": [], "edges": [], "productions": [],
        "rules": RULES,
    }


def write_seed(path=None):
    p = (Path(path) if path else
         Path(__file__).resolve().parent.parent / "seeds" / "ls20_understanding.json")
    p.write_text(json.dumps(manifest(), indent=1))
    return p


if __name__ == "__main__":
    print("wrote", write_seed())
