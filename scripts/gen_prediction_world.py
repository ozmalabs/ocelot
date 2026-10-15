#!/usr/bin/env python3
"""Emit the prediction world (2026-10-10): a graded, closed world in which to
demonstrate ENDEMIC self-improvement -- the agent improving itself from its
own operation, judged by its own criterion, with an off arm.

The world (domains/prediction_world.py, mechanical): bodies move in a box;
each frame the agent observes their positions and its PREDICTOR -- graph
rules -- predicts where each will be next. Its criterion is its own surprise:
the distance between where it predicted a body would be and where it was.
Levels get harder: 1 drift (constant velocity), 2 bounce (walls), 3 fall
(gravity), 4 glide (damping), 5 bounce under gravity.

seeds/prediction_world.json (skippable; the part the agent changes)
  * Predictor{form, reflect}: the agent's held model of motion. `form` is
    velocity (x + dx), acceleration (x + 2dx - pdx: a constant change in
    displacement) or ratio (x + dx*dx/pdx: a constant ratio of
    displacements); `reflect` folds a prediction that leaves the box back in.
  * PredictorCandidate{form, reflect, rank}: the space of models the agent
    may try, in MDL order (fewest parts first). A human wrote this grammar;
    which model to try, when, and whether to keep it is the agent's.
  * predict_body_next: the predictor itself, one Term per axis.

seeds/prediction_self_improvement.json (frozen; the loop -- the agent may not
change how it judges itself)
  * PredictionCurriculum{current_level, max_level, last_change_seq} and
    PredictionPolicy{self_improvement, surprise_floor, window, min_gain,
    min_abs_gain}.
  * pw_advance_level: `window` consecutive episodes at the level at or under
    the floor -> the next level.
  * pw_file_surprise_concern: `window` episodes since the predictor last
    changed, none under the floor -> SelfConcern{kind:'prediction_surprise'}.
    Endemic: nothing but the agent's own surprise files it.
  * pw_propose_predictor_edit: an open concern, self-improvement on -> one
    Experiment + SeedDelta per candidate not yet tried against the current
    model for this concern.
  * pw_concern_exhausted: no candidate left -> the concern says so.
  * pw_judge_predictor_edit: the replay's variant surprise against its control
    surprise, on the agent's own recorded episodes at the level AND on its
    recorded episodes of the levels it has already mastered (retention):
    supported only when it is lower at the level by min_gain (relative) and
    its gain, net of retention_weight x the surprise it adds on mastered
    levels (summed per level, so one level's regression is neither diluted nor
    traded against another's improvement), reaches min_abs_gain. Weighed,
    not vetoed.
  * pw_adopt_predictor_edit: once every trial is judged, the supported trial
    with the best weighed net (ties: the simpler model) is adopted in the
    graph -- the Predictor takes the candidate's form -- and the concern is
    resolved.
Idempotent.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P_WORLD = ROOT / "seeds/prediction_world.json"
P_LOOP = ROOT / "seeds/prediction_self_improvement.json"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def NN(x): return Not(Eq(x, L(None)))
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Let(n, v, b): return {"type": "Let", "name": n, "value": v, "body": b}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Count(s): return {"type": "Count", "source": s}
def Nodes(t): return {"type": "NodesOfType", "node_type": t}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Argmin(src, var, val): return {"type": "Argmin", "source": src, "var_name": var, "value": val, "default": None}
def Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": None}
def Nb(n, e): return {"type": "Neighbours", "node": V(n) if isinstance(n, str) else n, "edge_type": e}
def InNb(n, e): return {"type": "InNeighbours", "node": V(n) if isinstance(n, str) else n, "edge_type": e}
def T(x): return {"__term__": x}


# ---------------------------------------------------------------- the predictor
def axis_prediction(pos, disp, prev, size):
    x, dx, pdx, w = A("b", pos), A("b", disp), A("b", prev), A("b", size)
    form = A("p", "form")
    raw = Ite(Eq(form, L("acceleration")), Minus(Plus(x, Times(L(2.0), dx)), pdx),
              Ite(Eq(form, L("ratio")),
                  Ite(Eq(pdx, L(0.0)), Plus(x, dx), Plus(x, Div(Times(dx, dx), pdx))),
                  Plus(x, dx)))
    edge = Minus(w, L(1.0))
    folded = Ite(Lt(V("raw"), L(0.0)), Minus(L(0.0), V("raw")),
                 Ite(Gt(V("raw"), edge), Minus(Times(L(2.0), edge), V("raw")), V("raw")))
    return Let("raw", raw, Ite(Eq(A("p", "reflect"), L(1)), folded, V("raw")))


PREDICT = {
    "name": "predict_body_next",
    "comment": "The agent's predictor: where each observed body will be next frame, from the held Predictor "
               "model (form, reflect).",
    "match": [["agent", "has_predictor", "p"], ["agent", "observes", "b"]],
    "where": And(NN(A("b", "obs_frame")), Not(Eq(A("b", "pred_frame"), A("b", "obs_frame")))),
    "effects": [["set_attr", "b", "pred_x", T(axis_prediction("x", "dx", "pdx", "w"))],
                ["set_attr", "b", "pred_y", T(axis_prediction("y", "dy", "pdy", "h"))],
                ["set_attr", "b", "pred_frame", T(A("b", "obs_frame"))]],
}

FORMS = ("velocity", "acceleration", "ratio")
candidates = []
for fi, form in enumerate(FORMS):
    for reflect in (0, 1):
        candidates.append({"form": form, "reflect": reflect, "rank": fi * 2 + reflect})
world_nodes = [{"local_id": 0, "type": "Predictor", "attrs": {
    "name": "motion_predictor", "form": "velocity", "reflect": 0,
    "description": "The agent's held model of how bodies move (the newborn prior: constant velocity)."}}]
world_edges = [{"src": {"role": "agent_root"}, "type": "has_predictor", "tgt": {"local": 0}, "attrs": {}}]
for i, c in enumerate(candidates, start=1):
    world_nodes.append({"local_id": i, "type": "PredictorCandidate", "attrs": c})
    world_edges.append({"src": {"role": "agent_root"}, "type": "has_predictor_candidate", "tgt": {"local": i},
                        "attrs": {}})
world = {"id": "prediction_world", "version": "1.0.0", "depends_on": [],
         "description": "The prediction world's predictor (see scripts/gen_prediction_world.py): the held Predictor "
                        "model, the candidate models in MDL order, and the prediction rule. This is the part of "
                        "the agent its self-improvement loop changes.",
         "nodes": world_nodes, "edges": world_edges, "productions": [], "rules": [PREDICT]}

# ---------------------------------------------------------------- the loop
CUR = [["agent", "has_prediction_curriculum", "cur"], ["agent", "has_prediction_policy", "pol"]]
LVL_EPS = Filter(Nodes("PredictionEpisode"), "e", Eq(A("e", "level"), A("cur", "current_level")))
SINCE = Filter(LVL_EPS, "e", Gt(A("e", "seq"), A("cur", "last_change_seq")))
UNDER = lambda src: Count(Filter(src, "u", Lte(A("u", "mean_surprise"), A("pol", "surprise_floor"))))
N_LVL = Count(LVL_EPS)
RECENT = Filter(LVL_EPS, "e", Gt(A("e", "level_index"), Minus(N_LVL, A("pol", "window"))))
OPEN_CONCERN = Exists(Nodes("SelfConcern"), "c", And(
    Eq(A("c", "kind"), L("prediction_surprise")), Eq(A("c", "level"), A("cur", "current_level")),
    Or(Eq(A("c", "status"), L("open")),
       And(Eq(A("c", "status"), L("exhausted")), Eq(A("c", "filed_change_seq"), A("cur", "last_change_seq"))))))

ADVANCE = {
    "name": "pw_advance_level",
    "comment": "`window` consecutive episodes at the level at or under the floor: the level is mastered.",
    "match": CUR,
    "where": And(Lt(A("cur", "current_level"), A("cur", "max_level")), Gte(N_LVL, A("pol", "window")),
                 Eq(UNDER(RECENT), A("pol", "window"))),
    "effects": [["set_attr", "cur", "mastered_through", T(A("cur", "current_level"))],
                ["set_attr", "cur", "current_level", T(Plus(A("cur", "current_level"), L(1)))]],
}
FILE = {
    "name": "pw_file_surprise_concern",
    "comment": "Endemic supply: `window` episodes since the predictor last changed, none under the floor, files the "
               "agent's own concern. Nothing but its surprise decides this.",
    "match": CUR,
    "where": And(Gte(Count(SINCE), A("pol", "window")), Eq(UNDER(SINCE), L(0)), Not(OPEN_CONCERN)),
    "effects": [["add_node", "sc", "SelfConcern", {
        "kind": "prediction_surprise", "status": "open", "source": "prediction_world",
        "level": T(A("cur", "current_level")), "filed_change_seq": T(A("cur", "last_change_seq")),
        "content": T({"type": "StringConcat", "parts": [
            L("my predictions keep missing at level "), {"type": "Str", "value": A("cur", "current_level")}]})}],
        ["add_edge", "agent", "has_self_concern", "sc"]],
}

# candidates not yet tried for this concern against the current model, and not the current model itself
TRIED = lambda c: Exists(Nb("sc", "tested_by"), "x", Exists(Nb(V("x"), "has_delta"), "d", And(
    Eq(A("d", "candidate_form"), A(c, "form")), Eq(A("d", "candidate_reflect"), A(c, "reflect")),
    Eq(A("d", "control_form"), A("p", "form")), Eq(A("d", "control_reflect"), A("p", "reflect")))))
IS_CURRENT = lambda c: And(Eq(A(c, "form"), A("p", "form")), Eq(A(c, "reflect"), A("p", "reflect")))
UNTRIED = Filter(Nodes("PredictorCandidate"), "k", And(Not(IS_CURRENT(V("k"))), Not(TRIED(V("k")))))
PENDING = Exists(Nb("sc", "tested_by"), "x", Eq(A("x", "outcome"), L(None)))
CONCERN_MATCH = CUR + [["agent", "has_self_concern", "sc"], ["agent", "has_predictor", "p"]]
CONCERN_OPEN = And(Eq(A("sc", "kind"), L("prediction_surprise")), Eq(A("sc", "status"), L("open")))
BEST = Argmin(UNTRIED, "k", A("k", "rank"))

PROPOSE = {
    "name": "pw_propose_predictor_edit",
    "comment": "The agent's own trials for its concern: every candidate model it has not yet tried against its "
               "current one, each in its own experiment, so the alternatives are weighed against each other.",
    "match": CONCERN_MATCH + [["agent", "has_predictor_candidate", "k"]],
    "where": And(CONCERN_OPEN, Eq(A("pol", "self_improvement"), L(1)), Not(IS_CURRENT(V("k"))), Not(TRIED(V("k")))),
    "effects": [
        ["add_node", "exp", "Experiment", {
            "game": "prediction_world", "status": "requested", "level": T(A("sc", "level")),
            "hypothesis": T({"type": "StringConcat", "parts": [
                L("predicting with the "), A("k", "form"), L(" model (reflect "),
                {"type": "Str", "value": A("k", "reflect")}, L(") lowers my surprise")]})}],
        ["add_node", "delta", "SeedDelta", {
            "variation_op": "predictor_edit", "candidate_form": T(A("k", "form")),
            "candidate_reflect": T(A("k", "reflect")), "candidate_rank": T(A("k", "rank")),
            "control_form": T(A("p", "form")), "control_reflect": T(A("p", "reflect"))}],
        ["add_edge", "exp", "has_delta", "delta"],
        ["add_edge", "sc", "tested_by", "exp"]],
}
SAME_CONTROL = lambda d: And(Eq(A(d, "control_form"), A("p", "form")), Eq(A(d, "control_reflect"), A("p", "reflect")))
SUPPORTED_OPEN = Exists(Nb("sc", "tested_by"), "o", And(
    Eq(A("o", "outcome"), L("supported")), Not(Eq(A("o", "adopted"), L(1))),
    Exists(Nb(V("o"), "has_delta"), "od", SAME_CONTROL(V("od")))))
EXHAUSTED = {
    "name": "pw_concern_exhausted",
    "comment": "Every candidate model has been tried against the current one and none was supported: the concern "
               "says so honestly.",
    "match": CONCERN_MATCH,
    "where": And(CONCERN_OPEN, Not(PENDING), Eq(Count(UNTRIED), L(0)), Not(SUPPORTED_OPEN)),
    "effects": [["set_attr", "sc", "status", "exhausted"]],
}
RET_HARM = A("exp", "retention_harm")
NET = Minus(Minus(A("exp", "control_surprise"), A("exp", "variant_surprise")),
            Times(A("pol", "retention_weight"), RET_HARM))
JUDGE = {
    "name": "pw_judge_predictor_edit",
    "comment": "The agent's own criterion on its own recorded episodes, weighed: the variant must lower surprise at "
               "the level by min_gain (relative), and its gain, net of any surprise it adds on levels already "
               "mastered (retention_weight), must reach min_abs_gain.",
    "match": [["agent", "has_prediction_policy", "pol"], ["sc", "tested_by", "exp"]],
    "where": And(Eq(A("exp", "game"), L("prediction_world")), Eq(A("exp", "status"), L("done")),
                 Eq(A("exp", "outcome"), L(None)), NN(A("exp", "control_surprise")),
                 NN(A("exp", "variant_surprise")), NN(A("exp", "retention_harm"))),
    "effects": [["set_attr", "exp", "weighed_net", T(NET)],
                ["set_attr", "exp", "outcome", T(Ite(And(
                    Lte(A("exp", "variant_surprise"), Times(A("exp", "control_surprise"),
                                                            Minus(L(1.0), A("pol", "min_gain")))),
                    Gte(NET, A("pol", "min_abs_gain"))),
                    L("supported"), L("refuted")))]],
}
ADOPT = {
    "name": "pw_adopt_predictor_edit",
    "comment": "Once every trial is judged, the best supported trade is adopted in the graph: the Predictor takes "
               "the candidate model, the concern is resolved, and the episodes since are counted afresh.",
    "match": CUR + [["agent", "has_predictor", "p"], ["sc", "tested_by", "exp"], ["exp", "has_delta", "delta"]],
    "where": And(Eq(A("exp", "outcome"), L("supported")), Not(Eq(A("exp", "adopted"), L(1))),
                 SAME_CONTROL("delta"), Not(PENDING),
                 # the best weighed trade among this concern's supported trials (ties: the simpler model)
                 Not(Exists(Nb("sc", "tested_by"), "o", And(
                     Eq(A("o", "outcome"), L("supported")), Not(Eq(V("o"), V("exp"))),
                     Exists(Nb(V("o"), "has_delta"), "od", And(SAME_CONTROL(V("od")), Or(
                         Gt(A("o", "weighed_net"), A("exp", "weighed_net")),
                         And(Eq(A("o", "weighed_net"), A("exp", "weighed_net")),
                             Lt(A("od", "candidate_rank"), A("delta", "candidate_rank")))))))))),
    "effects": [
        ["set_attr", "p", "form", T(A("delta", "candidate_form"))],
        ["set_attr", "p", "reflect", T(A("delta", "candidate_reflect"))],
        ["set_attr", "exp", "adopted", 1],
        ["set_attr", "sc", "status", "resolved"],
        ["set_attr", "cur", "last_change_seq", T(A(Argmax(Nodes("PredictionEpisode"), "q", A("q", "seq")), "seq"))],
        ["add_node", "ad", "Adoption", {
            "kind": "predictor_edit", "rule_added": "", "rule_removed": "",
            "from_form": T(A("delta", "control_form")), "from_reflect": T(A("delta", "control_reflect")),
            "to_form": T(A("delta", "candidate_form")), "to_reflect": T(A("delta", "candidate_reflect")),
            "level": T(A("exp", "level"))}],
        ["add_edge", "exp", "adopted_as", "ad"]],
}

loop_nodes = [
    {"local_id": 0, "type": "PredictionCurriculum", "attrs": {
        "name": "prediction_curriculum", "current_level": 1, "max_level": 5, "last_change_seq": -1}},
    {"local_id": 1, "type": "PredictionPolicy", "attrs": {
        "name": "prediction_policy", "self_improvement": 1, "surprise_floor": 0.15, "window": 3,
        "min_gain": 0.2, "min_abs_gain": 0.05, "retention_weight": 1.0,
        "description": "The agent's own bar: mean surprise per body-frame (cells) at or under the floor masters a "
                       "level; a model must cut it by 20%, and by 0.05 cells net of any surprise it adds on the "
                       "levels already mastered, to be adopted."}}]
loop_edges = [{"src": {"role": "agent_root"}, "type": "has_prediction_curriculum", "tgt": {"local": 0}, "attrs": {}},
              {"src": {"role": "agent_root"}, "type": "has_prediction_policy", "tgt": {"local": 1}, "attrs": {}}]
# no depends_on: the loop reads the predictor's nodes at run time, and a dependency
# would freeze the predictor seed by closure (it is the part the agent changes)
loop = {"id": "prediction_self_improvement", "version": "1.0.0", "depends_on": [],
        "description": __doc__, "nodes": loop_nodes, "edges": loop_edges, "productions": [],
        "rules": [ADVANCE, FILE, PROPOSE, EXHAUSTED, JUDGE, ADOPT]}

P_WORLD.write_text(json.dumps(world, indent=1, ensure_ascii=True) + "\n")
P_LOOP.write_text(json.dumps(loop, indent=1, ensure_ascii=True) + "\n")
print("prediction_world", len(candidates), "candidates; prediction_self_improvement", len(loop["rules"]), "rules")
