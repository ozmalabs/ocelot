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
  * Six base models, rank k = form_index*2 + reflect: velocity (x + dx),
    acceleration (x + 2dx - pdx: a constant change in displacement) or ratio
    (x + dx*dx/pdx: a constant ratio of displacements), each with or without
    `reflect` (fold a prediction that leaves the box back in).
  * Predictor{mask, model}: the agent's held model -- the set of base models
    it composes (bit k). One bit is a base model; more is a composite that
    uses, per body and axis, whichever component predicted that body best
    last frame (1.1.0).
  * PredictorCandidate{mask, name, rank, authored}: the models the agent may
    try, in MDL order. The six base models and the composition operator are
    human-written; which model to try, when, which composites to author, and
    whether to keep one is the agent's.
  * predict_body_next: the predictor itself.

seeds/prediction_self_improvement.json (frozen; the loop -- the agent may not
change how it judges itself)
  * PredictionCurriculum{current_level, max_level, last_change_seq} and
    PredictionPolicy{self_improvement, surprise_floor, window, min_gain,
    min_abs_gain}.
  * pw_advance_level: `window` consecutive episodes at the level at or under
    the floor -> the next level.
  * pw_file_surprise_concern: `window` episodes since the predictor last
    changed and the level not mastered -> SelfConcern{kind:'prediction_surprise'}.
    Endemic: nothing but the agent's own surprise files it.
  * pw_propose_predictor_edit: an open concern, self-improvement on -> one
    Experiment + SeedDelta per candidate not yet tried against the current
    model for this concern.
  * pw_concern_exhausted: no candidate left -> the concern says so.
  * pw_author_composite_predictor (1.1.0): an exhausted concern whose best
    local trial cleared the bar at the level and was refuted only on its
    retention cost -> the agent authors a new candidate, its current model
    composed with that winner, and reopens the concern. Composites compose
    further; one it already holds is not re-authored, so it terminates.
  * pw_request_residual_fit / pw_author_context_layer (1.2.0): an exhausted
    concern with nothing to compose -> the agent asks where its own model's
    surprise lives (ResidualFit: per context atom, the summed error of the
    frames where it holds, and the least-squares fit of those frames,
    x' - x = c0*dx + c1*pdx + c2*ppdx + c3, written by the mechanical
    half as ResidualCells); it then authors its current model plus a layer on
    the atom holding the most residual where the fit helps, and reopens the
    concern. The context atoms (reversal: dx*pdx < 0; after_reversal:
    pdx*ppdx < 0) and the linear layer form are human-written; which atom,
    the coefficients (from its own episodes), and whether to keep it are not.
  * pw_master_last_level (1.2.0): the last level is mastered like the others.
  * PredictionPolicy.authoring (1.2.0): 0 switches both authoring rules off
    (the no_authoring ablation).
  * Revision (1.3.0): residual fits also cover layers the model holds
    (refit one, or refit_all), each fit offered on the level alone and pooled
    with the mastered levels, one candidate per helpful fit;
    pw_author_pruned_component (the model minus one base component) and
    pw_author_dropped_layer (minus its last layer); layers gain a fifth term,
    the body's running acceleration estimate on the axis.
  * Robust mastery (1.4.0): the one-sided 95% upper confidence bound of the
    mean surprise of the last `mastery_window` (5) episodes under the current
    model at or under the floor; concerns filed on the mean of the last
    `window` episodes since the change, or after 2*mastery_window episodes
    without robust mastery.
  * Meta search (1.4.0): PredictionOperatorStat per authoring operator
    (tried / supported / adopted, updated by pw_count_operator_trial and
    pw_count_operator_adoption); with meta_search on, trials go in batches by
    operator yield (supported+1)/(tried+2), best first, and an operator tried
    meta_min_trials times with yield under meta_min_yield is skipped.
  * 1.5.0: experts (up to N_EXPERTS more full models on the Predictor, gated
    per body and axis by cumulative error; authored by pw_author_expert from
    the local winner and pw_author_specialist_expert from a level-only fit,
    both only once a concern's single-model fits are spent); provenance
    credit (`enabled`) in the operator record, and skipping only as a last
    resort; self-proposed policy changes (MetaProposal from META_GRAMMAR,
    measured on the agent's own practice levels by the mechanical half,
    judged and adopted by pw_judge_policy_change / pw_adopt_policy_change_*).
  * 1.6.0: the operator record per kind of world (box / open, read from the
    level's latest episode); skipping a real skip again (skip_last_resort 0);
    policy proposals in rounds (meta_round / meta_max_rounds, closed by
    pw_close_policy_round), supported only when they win on more practice
    levels than they lose.
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
FORMS = ("velocity", "acceleration", "ratio")
N_BASE = len(FORMS) * 2


def base_prediction(k, pos, disp, prev, size):
    """Base model k (rank k = form_index*2 + reflect) on one axis."""
    x, dx, pdx, w = A("b", pos), A("b", disp), A("b", prev), A("b", size)
    form, reflect = FORMS[k // 2], k % 2
    if form == "acceleration":
        raw = Minus(Plus(x, Times(L(2.0), dx)), pdx)
    elif form == "ratio":
        raw = Ite(Eq(pdx, L(0.0)), Plus(x, dx), Plus(x, Div(Times(dx, dx), pdx)))
    else:
        raw = Plus(x, dx)
    if not reflect:
        return raw
    edge = Minus(w, L(1.0))
    return Let("raw", raw, Ite(Lt(V("raw"), L(0.0)), Minus(L(0.0), V("raw")),
                               Ite(Gt(V("raw"), edge), Minus(Times(L(2.0), edge), V("raw")), V("raw"))))


def in_mask(k, pre=""):
    return Not(Eq({"type": "BitAnd", "a": A("p", pre + "mask"), "b": L(1 << k)}, L(0)))


def fold(raw, size):
    edge = Minus(A("b", size), L(1.0))
    return Let("raw", raw, Ite(Lt(V("raw"), L(0.0)), Minus(L(0.0), V("raw")),
                               Ite(Gt(V("raw"), edge), Minus(Times(L(2.0), edge), V("raw")), V("raw"))))


# Context atoms the agent's layers can be conditioned on (bit, name, test on the
# displacement history d0 = dx, d1 = pdx, d2 = ppdx). Human-written, like the base forms.
CONTEXT_ATOMS = ((1, "reversal", ("dx", "pdx")), (2, "after_reversal", ("pdx", "ppdx")))
N_SLOTS = len(CONTEXT_ATOMS)
# x' = x + c0*dx + c1*pdx + c2*ppdx + c3 + c4*acc, folded into the box; acc (1.3.0) is the body's own
# running acceleration estimate on this axis (dx - pdx on its last frame with no reversal)
COEFS = ("0", "1", "2", "3", "4")
LAYER_KEYS = [f"l{i}_bit" for i in range(N_SLOTS)] + [f"l{i}_{ax}{c}" for i in range(N_SLOTS) for ax in "xy"
                                                       for c in COEFS]
# (1.5.0) experts: besides its primary model (mask + layers), the Predictor may hold N_EXPERTS more, each a full
# model of its own under the prefix x<e>_ (mask 0 = empty slot); per body and axis the prediction is the
# expert's whose last prediction there was best
N_EXPERTS = 2
EXPERT_KEYS = ["mask", "n_layers", "ctx_bits"] + LAYER_KEYS
X_KEYS = [f"x{e}_{k}" for e in range(1, N_EXPERTS + 1) for k in EXPERT_KEYS]
SLOT_KEYS = ["n_layers", "ctx_bits", "sig"] + LAYER_KEYS + X_KEYS
HIST = {"x": ("dx", "pdx", "ppdx"), "y": ("dy", "pdy", "ppdy")}


def ctx_term(pos):
    d = dict(zip(("dx", "pdx", "ppdx"), HIST[pos]))
    parts = [Ite(Lt(Times(A("b", d[a]), A("b", d[b2])), L(0.0)), L(bit), L(0)) for bit, _n, (a, b2) in CONTEXT_ATOMS]
    return Plus(*parts)


def layer_applies(i, pos, pre=""):
    bit = A("p", f"{pre}l{i}_bit")
    return And(NN(bit), Gt(bit, L(0)), Not(Eq({"type": "BitAnd", "a": A("b", f"ctx_{pos}"), "b": bit}, L(0))))


def layer_prediction(i, pos, size, pre=""):
    h = HIST[pos]
    q = lambda c: A("p", f"{pre}l{i}_{pos}{c}")
    lin = Plus(A("b", pos), *[Times(q(c), A("b", h[j])) for j, c in enumerate(COEFS[:3])],
               q("3"), Times(q("4"), A("b", f"acc_{pos}")))
    return fold(lin, size)


def expert_prediction(pos, size, pre):
    """One expert's prediction: its first context layer that applies, else among its base components the one
    whose last error on this body and axis was lowest (ties: the simpler). Base predictions are read from the
    body (n<axis><k>, computed once per frame)."""
    score = lambda k: Ite(in_mask(k, pre), Plus(A("b", f"e{pos}{k}"), L(k * 1e-9)), L(1e18))
    best = {"type": "Min", "items": [score(k) for k in range(N_BASE)]}
    pick = A("b", f"n{pos}{N_BASE - 1}")
    for k in reversed(range(N_BASE - 1)):
        pick = Ite(Eq(score(k), V("best")), A("b", f"n{pos}{k}"), pick)
    pred = Let("best", best, pick)
    for i in reversed(range(N_SLOTS)):
        pred = Ite(layer_applies(i, pos, pre), layer_prediction(i, pos, size, pre), pred)
    return pred


def axis_effects(pos, disp, prev, size):
    """Per axis: (1) the error each base model's last prediction made on this
    observation; (2) the context of this frame (which atoms hold); (3) the
    prediction of the held model -- the first of its context layers whose
    context holds, else, among its base components (Predictor.mask), the one
    whose last error on this body and axis was lowest (ties: the simpler);
    (4) every base model's prediction, kept for the next frame's errors.
    Effects are evaluated in order."""
    eff = []
    for k in range(N_BASE):
        last = A("b", f"c{pos}{k}")
        eff.append(["set_attr", "b", f"e{pos}{k}", T(Ite(NN(last), {"type": "Abs", "arg": Minus(last, A("b", pos))},
                                                          L(0.0)))])
    eff.append(["set_attr", "b", f"ctx_{pos}", T(ctx_term(pos))])
    last_acc = A("b", f"acc_{pos}")
    eff.append(["set_attr", "b", f"acc_{pos}", T(Ite(And(Eq(A("b", f"ctx_{pos}"), L(0)), Gte(A("b", "obs_frame"), L(2))),
                                                    Minus(A("b", disp), A("b", prev)),
                                                    Ite(NN(last_acc), last_acc, L(0.0))))])
    for k in range(N_BASE):
        eff.append(["set_attr", "b", f"n{pos}{k}", T(base_prediction(k, pos, disp, prev, size))])
    prefixes = [""] + [f"x{e}_" for e in range(1, N_EXPERTS + 1)]
    for e, pre in enumerate(prefixes):
        last = A("b", f"cp{e}{pos}")
        # an expert's evidence on this body and axis: the sum of its errors since the body was first seen
        prev_sum = A("b", f"ee{e}{pos}")
        eff.append(["set_attr", "b", f"ee{e}{pos}", T(Plus(Ite(NN(prev_sum), prev_sum, L(0.0)),
                                                           Ite(NN(last), {"type": "Abs", "arg": Minus(last, A("b", pos))},
                                                               L(0.0))))])
    for e, pre in enumerate(prefixes):
        active = L(True) if e == 0 else And(NN(A("p", pre + "mask")), Gt(A("p", pre + "mask"), L(0)))
        eff.append(["set_attr", "b", f"cp{e}{pos}", T(Ite(active, expert_prediction(pos, size, pre), L(None)))])
    xscore = lambda e: (Plus(A("b", f"ee{e}{pos}"), L(e * 1e-9)) if e == 0 else
                        Ite(NN(A("b", f"cp{e}{pos}")), Plus(A("b", f"ee{e}{pos}"), L(e * 1e-9)), L(1e18)))
    xbest = {"type": "Min", "items": [xscore(e) for e in range(len(prefixes))]}
    xpick = A("b", f"cp{len(prefixes) - 1}{pos}")
    for e in reversed(range(len(prefixes) - 1)):
        xpick = Ite(Eq(xscore(e), V("xb")), A("b", f"cp{e}{pos}"), xpick)
    eff.append(["set_attr", "b", f"pred_{pos}", T(Let("xb", xbest, xpick))])
    for k in range(N_BASE):
        eff.append(["set_attr", "b", f"c{pos}{k}", T(A("b", f"n{pos}{k}"))])
    return eff


PREDICT = {
    "name": "predict_body_next",
    "comment": "The agent's predictor: where each observed body will be next frame, from the held Predictor "
               "model -- a context layer the agent fitted, where its context holds; else one base model, or a "
               "composite the agent authored that uses, per body and axis, whichever of its components predicted "
               "that body best last frame.",
    "match": [["agent", "has_predictor", "p"], ["agent", "observes", "b"]],
    "where": And(NN(A("b", "obs_frame")), Not(Eq(A("b", "pred_frame"), A("b", "obs_frame")))),
    "effects": axis_effects("x", "dx", "pdx", "w") + axis_effects("y", "dy", "pdy", "h")
               + [["set_attr", "b", "pred_frame", T(A("b", "obs_frame"))]],
}

NO_LAYERS = {"n_layers": 0, "ctx_bits": 0, "sig": "", **{f"l{i}_bit": 0 for i in range(N_SLOTS)},
             **{f"l{i}_{ax}{c}": 0.0 for i in range(N_SLOTS) for ax in "xy" for c in COEFS},
             **{k: (0 if k.split("_", 1)[1] in ("mask", "n_layers", "ctx_bits") or k.endswith("_bit") else 0.0)
                for k in X_KEYS}}
candidates = []
for fi, form in enumerate(FORMS):
    for reflect in (0, 1):
        rank = fi * 2 + reflect
        candidates.append({"form": form, "reflect": reflect, "rank": rank, "mask": 1 << rank,
                           "name": form + ("+reflect" if reflect else ""), "authored": 0, **NO_LAYERS})
world_nodes = [{"local_id": 0, "type": "Predictor", "attrs": {
    "name": "motion_predictor", "form": "velocity", "reflect": 0, "mask": 1, "model": "velocity", **NO_LAYERS,
    "description": "The agent's held model of how bodies move (the newborn prior: constant velocity). `mask` "
                   "is the set of base models it composes (bit k = base model of rank k)."}}]
world_edges = [{"src": {"role": "agent_root"}, "type": "has_predictor", "tgt": {"local": 0}, "attrs": {}}]
for i, c in enumerate(candidates, start=1):
    world_nodes.append({"local_id": i, "type": "PredictorCandidate", "attrs": c})
    world_edges.append({"src": {"role": "agent_root"}, "type": "has_predictor_candidate", "tgt": {"local": i},
                        "attrs": {}})
world = {"id": "prediction_world", "version": "1.6.0", "depends_on": [],
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
# (1.4.0) robust mastery: the last `mastery_window` episodes at the level, all under the current model, with
# the one-sided upper confidence bound of their mean surprise (mean + mastery_z * sd / sqrt(n)) at or under the
# floor -- so a lucky streak on a model whose true surprise is above the floor does not count.
MW = A("pol", "mastery_window")
LAST_M = Filter(LVL_EPS, "e", Gt(A("e", "level_index"), Minus(N_LVL, MW)))
M_MEAN = Div({"type": "Sum", "source": LAST_M, "var_name": "e", "value": A("e", "mean_surprise")}, MW)
M_VAR = Div({"type": "Sum", "source": LAST_M, "var_name": "e", "value": {"type": "Pow", "a": Minus(
    A("e", "mean_surprise"), V("mm")), "b": L(2.0)}}, Minus(MW, L(1)))
M_UCB = Let("mm", M_MEAN, Plus(V("mm"), Times(A("pol", "mastery_z"), {"type": "Sqrt", "arg": Div(M_VAR, MW)})))
MASTERED = And(Gte(N_LVL, MW), Eq(Count(Filter(LAST_M, "e", Lte(A("e", "seq"), A("cur", "last_change_seq")))), L(0)),
               Lte(M_UCB, A("pol", "surprise_floor")))
LAST_W_SINCE = Filter(SINCE, "e", Gt(A("e", "level_index"), Minus(N_LVL, A("pol", "window"))))
W_MEAN = Div({"type": "Sum", "source": LAST_W_SINCE, "var_name": "e", "value": A("e", "mean_surprise")},
             A("pol", "window"))
OPEN_CONCERN = Exists(Nodes("SelfConcern"), "c", And(
    Eq(A("c", "kind"), L("prediction_surprise")), Eq(A("c", "level"), A("cur", "current_level")),
    Or(Eq(A("c", "status"), L("open")),
       And(Eq(A("c", "status"), L("exhausted")), Eq(A("c", "filed_change_seq"), A("cur", "last_change_seq"))))))

ADVANCE = {
    "name": "pw_advance_level",
    "comment": "The level is mastered (1.4.0: robustly -- the upper confidence bound of the mean surprise of "
               "the last `mastery_window` episodes under the current model at or under the floor).",
    "match": CUR,
    "where": And(Lt(A("cur", "current_level"), A("cur", "max_level")), MASTERED),
    "effects": [["set_attr", "cur", "mastered_through", T(A("cur", "current_level"))],
                ["set_attr", "cur", "current_level", T(Plus(A("cur", "current_level"), L(1)))]],
}
MASTER_LAST = {
    "name": "pw_master_last_level",
    "comment": "The last level is mastered the same way; there is nowhere to advance to.",
    "match": CUR,
    "where": And(Eq(A("cur", "current_level"), A("cur", "max_level")), MASTERED,
                 Not(Eq(A("cur", "mastered_through"), A("cur", "max_level")))),
    "effects": [["set_attr", "cur", "mastered_through", T(A("cur", "max_level"))]],
}
FILE = {
    "name": "pw_file_surprise_concern",
    "comment": "Endemic supply: `window` episodes since the predictor last changed and the level still not "
               "mastered (its last `window` episodes not all at or under the floor) files the agent's own "
               "concern. Nothing but its surprise decides this. (1.2.0: was 'none under the floor', which one "
               "lucky episode blocked forever.)",
    "match": CUR,
    # 1.4.0: the evidence of a miss is the mean of the last `window` episodes since the change above the floor;
    # or, after 2*mastery_window episodes, a level still not robustly mastered
    "where": And(Gte(Count(SINCE), A("pol", "window")), Not(OPEN_CONCERN),
                 Not(Eq(A("cur", "mastered_through"), A("cur", "current_level"))),
                 Or(Gt(W_MEAN, A("pol", "surprise_floor")),
                    And(Gte(Count(SINCE), Times(L(2), MW)), Not(MASTERED)))),
    "effects": [["add_node", "sc", "SelfConcern", {
        "kind": "prediction_surprise", "status": "open", "source": "prediction_world",
        "level": T(A("cur", "current_level")), "filed_change_seq": T(A("cur", "last_change_seq")),
        "content": T({"type": "StringConcat", "parts": [
            L("my predictions keep missing at level "), {"type": "Str", "value": A("cur", "current_level")}]})}],
        ["add_edge", "agent", "has_self_concern", "sc"]],
}

# candidates not yet tried for this concern against the current model, and not the current model itself
# a model's identity: its base components and its context layers
SAME = lambda m1, s1, m2, s2: And(Eq(m1, m2), Eq(s1, s2))
IS_P = lambda node, pre="": SAME(A(node, pre + "mask"), A(node, pre + "sig"), A("p", "mask"), A("p", "sig"))
TRIED = lambda c: Exists(Nb("sc", "tested_by"), "x", Exists(Nb(V("x"), "has_delta"), "d", And(
    SAME(A("d", "candidate_mask"), A("d", "candidate_sig"), A(c, "mask"), A(c, "sig")), IS_P("d", "control_"))))
IS_CURRENT = lambda c: IS_P(c)
UNTRIED = Filter(Nodes("PredictorCandidate"), "k", And(Not(IS_CURRENT(V("k"))), Not(TRIED(V("k")))))
# (1.4.0) the agent's record of its own search: per authoring operator, how many of its candidates were
# tried and how many the judge supported; a candidate's operator is how it was authored ('base' if born-with)
OP_KIND = lambda c: Ite(Eq(A(c, "authored"), L(1)), A(c, "authored_by"), L("base"))
# (1.6.0) the record is kept per kind of world: a box (walls, w < 1000) or open space, read from the level's
# latest episode -- what worked in one kind of world is not taken as evidence about the other
LATEST_EP = Argmax(LVL_EPS, "le", A("le", "seq"))
CUR_KIND = Let("lep", LATEST_EP, Ite(And(NN(V("lep")), Lt(A("lep", "w"), L(999.0))), L("box"), L("open")))
OP_STAT = lambda c: Argmax(Filter(Nodes("PredictionOperatorStat"), "os", And(
    Eq(A("os", "kind"), OP_KIND(c)), Eq(A("os", "world_kind"), CUR_KIND))),
                           "os", L(0))
# (1.5.0) an operator's yield counts the trials it enabled: a supported candidate authored FROM one of its
# trials (a composite or expert built on a refuted local winner) is credited to it as well
YIELD = lambda c: Let("st", OP_STAT(c), Ite(NN(V("st")), Div(Plus(A("st", "supported"), A("st", "enabled"), L(1.0)),
                                                            Plus(A("st", "tried"), L(2.0))), L(0.5)))
OP_ENABLED = lambda c: Let("st", OP_STAT(c), Ite(NN(V("st")), A("st", "enabled"), L(0)))
OP_TRIED = lambda c: Let("st", OP_STAT(c), Ite(NN(V("st")), A("st", "tried"), L(0)))
# with meta_search on, a candidate is not worth a trial when its operator has been tried meta_min_trials times
# and its yield is under meta_min_yield
SKIPPED = lambda c: And(Eq(A("pol", "meta_search"), L(1)), Gte(OP_TRIED(c), A("pol", "meta_min_trials")),
                        Lt(YIELD(c), A("pol", "meta_min_yield")),
                        # (1.5.0) never skip an operator whose trials other operators have built on
                        Eq(OP_ENABLED(c), L(0)))
UNTRIED_NONSKIP = Filter(UNTRIED, "un", Not(SKIPPED(V("un"))))
# (1.5.0) with skip_last_resort on, a skipped operator is a last resort, not a ban: once nothing else is left
# untried, its candidates are trialled too. (1.6.0: off by default -- the per-kind record and the `enabled`
# credit are the safety instead)
VIABLE = lambda c: Or(Not(SKIPPED(c)), And(Eq(A("pol", "skip_last_resort"), L(1)), Eq(Count(UNTRIED_NONSKIP), L(0))))
UNTRIED_VIABLE = Filter(UNTRIED, "uv", VIABLE(V("uv")))
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
                L("predicting with the "), A("k", "name"), L(" model lowers my surprise")]}),
            "candidate_mask": T(A("k", "mask")), "control_mask": T(A("p", "mask")),
            "candidate_sig": T(A("k", "sig")), "control_sig": T(A("p", "sig")),
            "candidate_operator": T(OP_KIND("k")), "candidate_parent_operator": T(A("k", "parent_operator")),
            "world_kind": T(CUR_KIND),
            "candidate_name": T(A("k", "name"))}],
        ["add_node", "delta", "SeedDelta", {
            "variation_op": "predictor_edit", "candidate_form": T(A("k", "form")),
            "candidate_reflect": T(A("k", "reflect")), "candidate_rank": T(A("k", "rank")),
            "candidate_mask": T(A("k", "mask")), "candidate_name": T(A("k", "name")),
            "control_form": T(A("p", "form")), "control_reflect": T(A("p", "reflect")),
            "control_mask": T(A("p", "mask")), "control_name": T(A("p", "model")),
            **{f"candidate_{key}": T(A("k", key)) for key in SLOT_KEYS},
            **{f"control_{key}": T(A("p", key)) for key in SLOT_KEYS}}],
        ["add_edge", "exp", "has_delta", "delta"],
        ["add_edge", "sc", "tested_by", "exp"]],
}
SAME_CONTROL = lambda d: IS_P(d, "control_")
SUPPORTED_OPEN = Exists(Nb("sc", "tested_by"), "o", And(
    Eq(A("o", "outcome"), L("supported")), Not(Eq(A("o", "adopted"), L(1))),
    Exists(Nb(V("o"), "has_delta"), "od", SAME_CONTROL(V("od")))))
# (1.4.0) meta search: with meta_search on, trials go in batches -- only the untried candidates whose operator
# has the best yield so far, and the next batch only once this one is judged with nothing to adopt
BEST_YIELD = {"type": "MaxOver", "source": UNTRIED_VIABLE, "var_name": "u", "value": YIELD("u"), "default": L(0.0)}
PROPOSE["where"] = And(CONCERN_OPEN, Eq(A("pol", "self_improvement"), L(1)), Not(IS_CURRENT(V("k"))),
                       Not(TRIED(V("k"))), VIABLE(V("k")),
                       Or(Not(Eq(A("pol", "meta_search"), L(1))),
                          And(Not(PENDING), Not(SUPPORTED_OPEN), Gte(YIELD("k"), BEST_YIELD))))
PROPOSE["comment"] += (" 1.4.0: with meta_search on, in batches by the yield of the operator that authored "
                       "each candidate (its own record), best first.")
STAT_MATCH = [["agent", "has_operator_stat", "os"], ["sc", "tested_by", "exp"]]
COUNT_TRIAL = {
    "name": "pw_count_operator_trial",
    "comment": "The agent's record of its own search: a judged trial counts against the operator that authored "
               "its candidate (tried, and supported if the judge supported it).",
    "match": STAT_MATCH,
    "where": And(NN(A("exp", "outcome")), Not(Eq(A("exp", "op_counted"), L(1))),
                 Eq(A("os", "kind"), A("exp", "candidate_operator")), Eq(A("os", "world_kind"), A("exp", "world_kind"))),
    "effects": [["set_attr", "os", "tried", T(Plus(A("os", "tried"), L(1)))],
                ["set_attr", "os", "supported", T(Plus(A("os", "supported"),
                                                       Ite(Eq(A("exp", "outcome"), L("supported")), L(1), L(0))))],
                ["set_attr", "exp", "op_counted", 1]],
}
COUNT_ENABLED = {
    "name": "pw_count_operator_enabled",
    "comment": "1.5.0: a supported trial of a candidate authored from another operator's trial credits that "
               "operator too -- its trials are what the authoring built on.",
    "match": STAT_MATCH,
    "where": And(Eq(A("exp", "outcome"), L("supported")), Not(Eq(A("exp", "op_enabled_counted"), L(1))),
                 NN(A("exp", "candidate_parent_operator")),
                 Eq(A("os", "kind"), A("exp", "candidate_parent_operator")),
                 Eq(A("os", "world_kind"), A("exp", "world_kind"))),
    "effects": [["set_attr", "os", "enabled", T(Plus(A("os", "enabled"), L(1)))],
                ["set_attr", "exp", "op_enabled_counted", 1]],
}
COUNT_ADOPT = {
    "name": "pw_count_operator_adoption",
    "comment": "An adopted trial also counts as an adoption for its operator.",
    "match": STAT_MATCH,
    "where": And(Eq(A("exp", "adopted"), L(1)), Not(Eq(A("exp", "op_adopt_counted"), L(1))),
                 Eq(A("os", "kind"), A("exp", "candidate_operator")), Eq(A("os", "world_kind"), A("exp", "world_kind"))),
    "effects": [["set_attr", "os", "adopted", T(Plus(A("os", "adopted"), L(1)))],
                ["set_attr", "exp", "op_adopt_counted", 1]],
}
EXHAUSTED = {
    "name": "pw_concern_exhausted",
    "comment": "Every candidate model has been tried against the current one and none was supported: the concern "
               "says so honestly.",
    "match": CONCERN_MATCH,
    "where": And(CONCERN_OPEN, Not(PENDING), Eq(Count(UNTRIED_VIABLE), L(0)), Not(SUPPORTED_OPEN)),
    "effects": [["set_attr", "sc", "status", "exhausted"]],
}
# The local winner: this concern's refuted trial (against the current model) that cleared the bar AT the level
# -- it was refuted only on what it cost the levels already mastered -- with the lowest surprise there.
LOCAL_WINNER = Argmin(Filter(Nb("sc", "tested_by"), "lw", And(
    IS_P("lw", "control_"), Eq(A("lw", "outcome"), L("refuted")),
    Lte(A("lw", "variant_surprise"), Times(A("lw", "control_surprise"), Minus(L(1.0), A("pol", "min_gain")))))),
    "lw", A("lw", "variant_surprise"))
W_MASK = A("w", "candidate_mask")
UNION = Minus(Plus(A("p", "mask"), W_MASK), {"type": "BitAnd", "a": A("p", "mask"), "b": W_MASK})
COMPOSITE_AVAILABLE = Let("w", LOCAL_WINNER, And(NN(V("w")), Not(Exists(Nodes("PredictorCandidate"), "q", SAME(
    A("q", "mask"), A("q", "sig"), UNION, A("p", "sig"))))))
AUTHOR = {
    "name": "pw_author_composite_predictor",
    "comment": "An exhausted concern whose best local trial was refuted only on its retention cost: the agent "
               "authors a new model -- its current model and that winner, composed (per body and axis, whichever "
               "component predicted best last frame) -- adds it to its own candidate space and reopens the "
               "concern to try it. Composites compose further; a composite it already holds is not re-authored, "
               "so the concern stays exhausted when composition has nothing new to offer.",
    "match": CONCERN_MATCH,
    "where": And(Eq(A("sc", "kind"), L("prediction_surprise")), Eq(A("sc", "status"), L("exhausted")),
                 Eq(A("sc", "level"), A("cur", "current_level")), Eq(A("pol", "self_improvement"), L(1)),
                 Eq(A("pol", "authoring"), L(1)), COMPOSITE_AVAILABLE),
    "effects": [
        ["add_node", "k", "PredictorCandidate", {
            "form": "select", "reflect": -1, "authored": 1, "authored_level": T(A("sc", "level")),
            "authored_by": "composition", "parent_operator": T(Let("w", LOCAL_WINNER, A("w", "candidate_operator"))),
            **{key: T(A("p", key)) for key in SLOT_KEYS},
            "mask": T(Let("w", LOCAL_WINNER, UNION)),
            "rank": T(Plus(L(N_BASE), Count(Nodes("PredictorCandidate")))),
            "name": T(Let("w", LOCAL_WINNER, {"type": "StringConcat", "parts": [
                A("p", "model"), L(" | "), A("w", "candidate_name")]}))}],
        ["add_edge", "agent", "has_predictor_candidate", "k"],
        ["add_edge", "sc", "authored", "k"],
        ["set_attr", "sc", "composed", 1],
        ["set_attr", "sc", "status", "open"]],
}
EXHAUSTED_HERE = And(Eq(A("sc", "kind"), L("prediction_surprise")), Eq(A("sc", "status"), L("exhausted")),
                     Eq(A("sc", "level"), A("cur", "current_level")), Eq(A("pol", "self_improvement"), L(1)))
# a concern under revision: exhausted with nothing to compose; the revision operators then all author in the
# same pass (the first to reopen the concern marks it `revising`, so the others still see it)
REVISABLE = And(Eq(A("sc", "kind"), L("prediction_surprise")), Eq(A("sc", "level"), A("cur", "current_level")),
                Eq(A("pol", "self_improvement"), L(1)), Eq(A("pol", "authoring"), L(1)),
                Or(And(Eq(A("sc", "status"), L("exhausted")), Not(COMPOSITE_AVAILABLE)),
                   And(Eq(A("sc", "status"), L("open")), Eq(A("sc", "revising"), L(1)))))
REQUEST_FIT = {
    "name": "pw_request_residual_fit",
    "comment": "An exhausted concern with nothing left to compose (no local winner, or its composite is already "
               "held): the agent asks where its own model's surprise lives -- its residual on its own recorded "
               "episodes at the level, per context atom, both for atoms it does not yet condition on and for "
               "the layers it already holds (1.3.0: so it can revise what it built).",
    "match": CONCERN_MATCH,
    "where": And(REVISABLE, Not(Eq(A("sc", "fit_requested"), L(1)))),
    "effects": [["add_node", "rf", "ResidualFit", {
        "status": "requested", "level": T(A("sc", "level")), "control_mask": T(A("p", "mask")),
        "control_sig": T(A("p", "sig")), "control_ctx_bits": T(A("p", "ctx_bits"))}],
        ["add_edge", "sc", "has_residual_fit", "rf"],
        ["set_attr", "sc", "fit_requested", 1]],
}
K_BIT_IN_P = Not(Eq({"type": "BitAnd", "a": A("p", "mask"), "b": A("k", "mask")}, L(0)))
PRUNED_MASK = Minus(A("p", "mask"), A("k", "mask"))
PRUNE_COMPONENT = {
    "name": "pw_author_pruned_component",
    "comment": "Revision (1.3.0): an exhausted concern with nothing to compose -- the agent authors its current "
               "model with one of its base components removed (its layers kept), one candidate per component, "
               "and reopens the concern; the judge weighs them like any other. A model it already holds is not "
               "re-authored.",
    "match": CONCERN_MATCH + [["agent", "has_predictor_candidate", "k"]],
    "where": And(REVISABLE, Eq(A("k", "authored"), L(0)), K_BIT_IN_P, Not(Eq(A("k", "mask"), A("p", "mask"))),
                 Not(Exists(Nodes("PredictorCandidate"), "q", SAME(A("q", "mask"), A("q", "sig"),
                                                                   PRUNED_MASK, A("p", "sig"))))),
    "effects": [
        ["add_node", "nk", "PredictorCandidate", {
            "form": "pruned", "reflect": -1, "authored": 1, "authored_level": T(A("sc", "level")),
            "authored_by": "prune_component", **{key: T(A("p", key)) for key in SLOT_KEYS},
            "mask": T(PRUNED_MASK), "rank": T(Plus(L(N_BASE), Count(Nodes("PredictorCandidate")))),
            "name": T({"type": "StringConcat", "parts": [A("p", "model"), L(" - "), A("k", "name")]})}],
        ["add_edge", "agent", "has_predictor_candidate", "nk"],
        ["add_edge", "sc", "authored", "nk"],
        ["set_attr", "sc", "revising", 1],
        ["set_attr", "sc", "status", "open"]],
}
LAST = lambda key: Ite(Eq(A("p", "n_layers"), L(2)), A("p", f"l1_{key}"), A("p", f"l0_{key}"))
DROP_SIG = {"type": "StringConcat", "parts": [A("p", "sig"), L("-L"), {"type": "Str", "value": LAST("bit")}]}
DROP_LAYER = {
    "name": "pw_author_dropped_layer",
    "comment": "Revision (1.3.0): an exhausted concern with nothing to compose and a model with layers -- the "
               "agent authors its current model without its last layer, and reopens the concern.",
    "match": CONCERN_MATCH,
    "where": And(REVISABLE, Gt(A("p", "n_layers"), L(0)),
                 Not(Exists(Nodes("PredictorCandidate"), "q", SAME(A("q", "mask"), A("q", "sig"),
                                                                   A("p", "mask"), DROP_SIG)))),
    "effects": [
        ["add_node", "nk", "PredictorCandidate", {
            "form": "pruned", "reflect": -1, "authored": 1, "authored_level": T(A("sc", "level")),
            "authored_by": "drop_layer", **{key: T(A("p", key)) for key in SLOT_KEYS}, "mask": T(A("p", "mask")),
            "n_layers": T(Minus(A("p", "n_layers"), L(1))),
            "ctx_bits": T(Minus(A("p", "ctx_bits"), LAST("bit"))), "sig": T(DROP_SIG),
            **{f"l{i}_bit": T(Ite(Eq(A("p", "n_layers"), L(i + 1)), L(0), A("p", f"l{i}_bit"))) for i in range(N_SLOTS)},
            "rank": T(Plus(L(N_BASE), Count(Nodes("PredictorCandidate")))),
            "name": T({"type": "StringConcat", "parts": [A("p", "model"), L(" - last layer")]})}],
        ["add_edge", "agent", "has_predictor_candidate", "nk"],
        ["add_edge", "sc", "authored", "nk"],
        ["set_attr", "sc", "revising", 1],
        ["set_attr", "sc", "status", "open"]],
}
XSIG = {"type": "StringConcat", "parts": [A("p", "sig"), L("&"), {"type": "Str", "value": A("wd", "candidate_mask")},
                                         A("wd", "candidate_sig")]}
FREE1 = Eq(A("p", "x1_mask"), L(0))
# experts are a last resort (simpler explanations first): only for an exhausted concern whose residual fit is done
# and whose single-model fits have all been authored (and so tried and refuted)
FITS_SPENT = And(Eq(A("sc", "status"), L("exhausted")), Eq(A("sc", "fit_requested"), L(1)),
                 Exists(Nb("sc", "has_residual_fit"), "rf2", Eq(A("rf2", "status"), L("done"))),
                 Not(Exists(Nb("sc", "has_residual_fit"), "rf2", Exists(Nb(V("rf2"), "has_cell"), "c2", And(
                     Not(Eq(A("c2", "kind"), L("specialist"))), Not(Eq(A("c2", "used"), L(1))),
                     Gt(A("c2", "fit_gain"), L(0.0)))))))
X_TARGET = lambda e: FREE1 if e == 1 else And(Not(FREE1), Eq(A("p", f"x{e}_mask"), L(0)))
ADD_EXPERT = {
    "name": "pw_author_expert",
    "comment": "1.5.0: scope-confined change. A concern whose best local trial cleared the bar at the level but "
               "was refuted on its retention cost: the agent authors its current model plus that winner as an "
               "EXPERT in a free slot -- per body and axis, the expert whose last prediction was best predicts -- "
               "so the specialist mostly acts only where it fits. The judge weighs it like any other candidate.",
    "match": CONCERN_MATCH + [["sc", "tested_by", "wx"], ["wx", "has_delta", "wd"]],
    "where": And(Eq(A("sc", "kind"), L("prediction_surprise")), Eq(A("sc", "level"), A("cur", "current_level")),
                 Eq(A("pol", "self_improvement"), L(1)), Eq(A("pol", "authoring"), L(1)),
                 Eq(A("pol", "experts"), L(1)),
                 FITS_SPENT, Eq(V("wx"), LOCAL_WINNER),
                 Or(FREE1, Eq(A("p", f"x{N_EXPERTS}_mask"), L(0))),
                 Not(Exists(Nodes("PredictorCandidate"), "q", SAME(A("q", "mask"), A("q", "sig"),
                                                                   A("p", "mask"), XSIG)))),
    "effects": [
        ["add_node", "nk", "PredictorCandidate", {
            "form": "experts", "reflect": -1, "authored": 1, "authored_level": T(A("sc", "level")),
            "authored_by": "add_expert", "parent_operator": T(A("wx", "candidate_operator")),
            **{key: T(A("p", key)) for key in SLOT_KEYS}, "mask": T(A("p", "mask")), "sig": T(XSIG),
            **{f"x{e}_{k}": T(Ite(X_TARGET(e), A("wd", "candidate_" + k), A("p", f"x{e}_{k}")))
               for e in range(1, N_EXPERTS + 1) for k in EXPERT_KEYS},
            "rank": T(Plus(L(N_BASE), Count(Nodes("PredictorCandidate")))),
            "name": T({"type": "StringConcat", "parts": [A("p", "model"), L(" & expert("),
                                                          A("wd", "candidate_name"), L(")")]})}],
        ["add_edge", "agent", "has_predictor_candidate", "nk"],
        ["add_edge", "sc", "authored", "nk"],
        ["set_attr", "sc", "revising", 1],
        ["set_attr", "sc", "status", "open"]],
}
SPEC_SIG = {"type": "StringConcat", "parts": [A("p", "sig"), L("&spec"), {"type": "Str", "value": A("cl", "specialist_mask")},
                                             L("@"), {"type": "Str", "value": A("rf", "level")}]}
SPEC_SLOT = lambda e, k: {"mask": A("cl", "specialist_mask"), "n_layers": L(2), "ctx_bits": L(3),
                          "l0_bit": L(1), "l1_bit": L(2)}.get(k, A("cl", "s" + k[1:]) if k.startswith("l") else None)
ADD_SPECIALIST = {
    "name": "pw_author_specialist_expert",
    "comment": "1.5.0: scope-confined change. From a ResidualFit's specialist cell -- its own base components "
               "with both context layers fitted from scratch on this level's frames alone -- the agent authors its "
               "current model plus that specialist as an expert in a free slot; per body and axis the expert whose "
               "last prediction was best predicts, so the specialist mostly acts only where it fits.",
    "match": CONCERN_MATCH + [["sc", "has_residual_fit", "rf"], ["rf", "has_cell", "cl"]],
    "where": And(Eq(A("rf", "status"), L("done")), Eq(A("rf", "control_sig"), A("p", "sig")),
                 Eq(A("rf", "control_mask"), A("p", "mask")), Eq(A("sc", "kind"), L("prediction_surprise")),
                 Eq(A("sc", "level"), A("cur", "current_level")), Eq(A("pol", "experts"), L(1)),
                 Eq(A("cl", "kind"), L("specialist")), Not(Eq(A("cl", "used"), L(1))), FITS_SPENT,
                 Gt(A("cl", "fit_gain"), L(0.0)), Or(FREE1, Eq(A("p", f"x{N_EXPERTS}_mask"), L(0))),
                 Not(Exists(Nodes("PredictorCandidate"), "q", SAME(A("q", "mask"), A("q", "sig"),
                                                                   A("p", "mask"), SPEC_SIG)))),
    "effects": [
        ["add_node", "nk", "PredictorCandidate", {
            "form": "experts", "reflect": -1, "authored": 1, "authored_level": T(A("sc", "level")),
            "authored_by": "add_expert", **{key: T(A("p", key)) for key in SLOT_KEYS},
            "mask": T(A("p", "mask")), "sig": T(SPEC_SIG),
            **{f"x{e}_{k}": T(Ite(X_TARGET(e), SPEC_SLOT(e, k), A("p", f"x{e}_{k}")))
               for e in range(1, N_EXPERTS + 1) for k in EXPERT_KEYS},
            "rank": T(Plus(L(N_BASE), Count(Nodes("PredictorCandidate")))),
            "name": T({"type": "StringConcat", "parts": [A("p", "model"), L(" & specialist@"),
                                                          {"type": "Str", "value": A("rf", "level")}]})}],
        ["add_edge", "agent", "has_predictor_candidate", "nk"],
        ["add_edge", "sc", "authored", "nk"],
        ["set_attr", "cl", "used", 1],
        ["set_attr", "sc", "status", "open"]],
}
IS_NEW = Eq(A("cl", "kind"), L("new"))
IS_REFIT = Eq(A("cl", "kind"), L("refit"))
IS_ALL = Eq(A("cl", "kind"), L("refit_all"))
HAS_BIT = Not(Eq({"type": "BitAnd", "a": A("p", "ctx_bits"), "b": A("cl", "ctx_bit")}, L(0)))
MODE_TAG = Ite(Eq(A("cl", "mode"), L("pooled")), L("/pooled"), L(""))
REVISES = Or(IS_REFIT, IS_ALL)
NEW_SIG = {"type": "StringConcat", "parts": [
    A("p", "sig"), Ite(REVISES, {"type": "StringConcat", "parts": [
        L("~"), A("cl", "atom"), L("@"), {"type": "Str", "value": A("rf", "level")}]}, L("+")),
    Ite(REVISES, L(""), A("cl", "atom")), MODE_TAG]}
NEW_NAME = {"type": "StringConcat", "parts": [
    A("p", "model"), Ite(REVISES, {"type": "StringConcat", "parts": [
        L(" ~ "), A("cl", "atom"), L(" refit@"), {"type": "Str", "value": A("rf", "level")}]},
        {"type": "StringConcat", "parts": [L(" + "), A("cl", "atom"), L(" layer")]}),
    Ite(Eq(A("cl", "mode"), L("pooled")), L(" (pooled)"), L(""))]}


def is_target(i):
    return Or(And(IS_NEW, Eq(A("p", "n_layers"), L(i))), And(IS_REFIT, Eq(A("p", f"l{i}_bit"), A("cl", "ctx_bit"))))


def slot_attr(i, key_slot, key_cell):
    """Slot i of the new model: the cell's fit where the cell targets it; for a joint refit (refit_all),
    the cell's per-slot fit for every slot the model holds; otherwise the current model's."""
    if key_slot == "bit":
        return T(Ite(is_target(i), A("cl", key_cell), A("p", f"l{i}_{key_slot}")))
    joint = And(IS_ALL, Gt(A("p", "n_layers"), L(i)))
    return T(Ite(joint, A("cl", f"s{i}_{key_cell}"),
                 Ite(is_target(i), A("cl", key_cell), A("p", f"l{i}_{key_slot}"))))


AUTHOR_LAYER = {
    "name": "pw_author_context_layer",
    "comment": "The agent authors new models from its own residual, one per ResidualCell where the fit helps: "
               "its current model with a NEW context layer on an atom it does not yet use, or (1.3.0) with one of "
               "its own layers REFITTED; each fitted on the level's frames alone or pooled with the levels it has "
               "mastered. It reopens the concern, and the judge weighs the alternatives against each other. A "
               "model it already holds is not re-authored.",
    "match": CONCERN_MATCH + [["sc", "has_residual_fit", "rf"], ["rf", "has_cell", "cl"]],
    "where": And(Eq(A("rf", "status"), L("done")), Eq(A("rf", "control_sig"), A("p", "sig")),
                 Eq(A("rf", "control_mask"), A("p", "mask")), Eq(A("sc", "kind"), L("prediction_surprise")),
                 Eq(A("sc", "level"), A("cur", "current_level")),
                 Not(Eq(A("cl", "used"), L(1))), Gt(A("cl", "fit_gain"), L(0.0)),
                 Or(And(IS_NEW, Not(HAS_BIT), Lt(A("p", "n_layers"), L(N_SLOTS))), And(IS_REFIT, HAS_BIT),
                    And(IS_ALL, Gt(A("p", "n_layers"), L(1)))),
                 Not(Exists(Nodes("PredictorCandidate"), "q", SAME(A("q", "mask"), A("q", "sig"),
                                                                   A("p", "mask"), NEW_SIG)))),
    "effects": [
        ["add_node", "k", "PredictorCandidate", {
            "form": "layered", "reflect": -1, "authored": 1, "authored_level": T(A("sc", "level")),
            "authored_by": T(Ite(IS_REFIT, L("residual_refit"), Ite(IS_ALL, L("residual_refit_all"),
                                                                    L("residual_fit")))), "mask": T(A("p", "mask")),
            "rank": T(Plus(L(N_BASE), Count(Nodes("PredictorCandidate")))),
            "n_layers": T(Ite(IS_NEW, Plus(A("p", "n_layers"), L(1)), A("p", "n_layers"))),
            "ctx_bits": T(Ite(IS_NEW, Plus(A("p", "ctx_bits"), A("cl", "ctx_bit")), A("p", "ctx_bits"))),
            "sig": T(NEW_SIG), "name": T(NEW_NAME), **{key: T(A("p", key)) for key in X_KEYS},
            **{f"l{i}_bit": slot_attr(i, "bit", "ctx_bit") for i in range(N_SLOTS)},
            **{f"l{i}_{ax}{c}": slot_attr(i, f"{ax}{c}", f"{ax}{c}")
               for i in range(N_SLOTS) for ax in "xy" for c in COEFS}}],
        ["add_edge", "agent", "has_predictor_candidate", "k"],
        ["add_edge", "sc", "authored", "k"],
        ["set_attr", "cl", "used", 1],
        ["set_attr", "sc", "status", "open"]],
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
        ["set_attr", "p", "mask", T(A("delta", "candidate_mask"))],
        ["set_attr", "p", "model", T(A("delta", "candidate_name"))],
        *[["set_attr", "p", key, T(A("delta", f"candidate_{key}"))] for key in SLOT_KEYS],
        ["set_attr", "exp", "adopted", 1],
        ["set_attr", "sc", "status", "resolved"],
        ["set_attr", "cur", "last_change_seq", T(A(Argmax(Nodes("PredictionEpisode"), "q", A("q", "seq")), "seq"))],
        ["add_node", "ad", "Adoption", {
            "kind": "predictor_edit", "rule_added": "", "rule_removed": "",
            "from_form": T(A("delta", "control_form")), "from_reflect": T(A("delta", "control_reflect")),
            "to_form": T(A("delta", "candidate_form")), "to_reflect": T(A("delta", "candidate_reflect")),
            "from_model": T(A("delta", "control_name")), "to_model": T(A("delta", "candidate_name")),
            "level": T(A("exp", "level"))}],
        ["add_edge", "exp", "adopted_as", "ad"]],
}

# ---------------------------------------------------------------- (1.5.0) self-proposed policy changes
# The grammar of changes the agent may propose to its own search policy (human-written): each scales one
# policy parameter. The agent proposes them all once its curriculum is mastered; the mechanical half measures
# each on practice levels the agent draws itself (forks of the agent, control vs variant: practice-level
# surprise + surprise added on its mastered levels, and experiments spent); the graph judges and adopts the
# best trade, if any.
META_GRAMMAR = (("retention_weight", 0.5), ("retention_weight", 2.0), ("meta_min_yield", 0.5),
                ("meta_min_yield", 2.0), ("meta_min_trials", 0.5), ("meta_min_trials", 2.0), ("min_gain", 0.5))
META_PROPOSE = {
    "name": "pw_propose_policy_change",
    "comment": "1.5.0: with its curriculum mastered and meta_proposals on, the agent proposes changes to its own "
               "search policy -- each a MetaProposal the mechanical half measures on practice levels.",
    "match": CUR,
    # 1.6.0: in rounds -- one set of proposals per round, from the policy the earlier rounds left
    "where": And(Eq(A("pol", "meta_proposals"), L(1)), NN(A("cur", "mastered_through")),
                 Eq(A("cur", "mastered_through"), A("cur", "max_level")),
                 Lt(A("pol", "meta_round"), A("pol", "meta_max_rounds")),
                 Not(Exists(Nodes("MetaProposal"), "mp", Eq(A("mp", "round"), A("pol", "meta_round"))))),
    "effects": [eff for i, (param, factor) in enumerate(META_GRAMMAR) for eff in (
        ["add_node", f"mp{i}", "MetaProposal", {"param": param, "factor": factor, "status": "requested",
                                               "current": T(A("pol", param)), "round": T(A("pol", "meta_round"))}],
        ["add_edge", "agent", "has_meta_proposal", f"mp{i}"])],
}
META_NET = Plus(Minus(A("mp", "control_total"), A("mp", "variant_total")),
                Times(A("pol", "experiment_cost"), Minus(A("mp", "control_experiments"), A("mp", "variant_experiments"))))
META_JUDGE = {
    "name": "pw_judge_policy_change",
    "comment": "1.5.0: a measured policy change, weighed: practice surprise plus retention harm saved, plus "
               "experiment_cost per experiment saved; supported when the net reaches meta_min_net and (1.6.0) "
               "the change wins on more practice levels than it loses, so no one level carries it.",
    "match": [["agent", "has_prediction_policy", "pol"], ["agent", "has_meta_proposal", "mp"]],
    "where": And(Eq(A("mp", "status"), L("done")), Eq(A("mp", "outcome"), L(None))),
    "effects": [["set_attr", "mp", "net", T(META_NET)],
                ["set_attr", "mp", "outcome", T(Ite(And(Gte(META_NET, A("pol", "meta_min_net")),
                                                        Gt(A("mp", "level_wins"), A("mp", "level_losses"))),
                                                    L("supported"), L("refuted")))]],
}
META_PENDING = Exists(Nodes("MetaProposal"), "o", And(Eq(A("o", "round"), A("mp", "round")),
                                                      Eq(A("o", "outcome"), L(None))))
META_BEST = Not(Exists(Nodes("MetaProposal"), "o", And(
    Eq(A("o", "round"), A("mp", "round")), Eq(A("o", "outcome"), L("supported")), Not(Eq(V("o"), V("mp"))),
    Or(Gt(A("o", "net"), A("mp", "net")), And(Eq(A("o", "net"), A("mp", "net")), Lt(A("o", "factor"), A("mp", "factor")))))))
META_ADOPT = [{
    "name": f"pw_adopt_policy_change_{param}",
    "comment": f"1.5.0: once every proposal is judged, the best supported one is adopted (here: {param}).",
    "match": [["agent", "has_prediction_policy", "pol"], ["agent", "has_meta_proposal", "mp"]],
    "where": And(Eq(A("mp", "param"), L(param)), Eq(A("mp", "outcome"), L("supported")),
                 Not(Eq(A("mp", "adopted"), L(1))), Not(META_PENDING), META_BEST),
    "effects": [["set_attr", "pol", param, T(Times(A("pol", param), A("mp", "factor")))],
                ["set_attr", "mp", "adopted", 1],
                ["set_attr", "pol", "meta_adopted", T({"type": "StringConcat", "parts": [
                    Ite(NN(A("pol", "meta_adopted")), {"type": "StringConcat", "parts": [A("pol", "meta_adopted"), L("; ")]}, L("")),
                    A("mp", "param"), L(" x"), {"type": "Str", "value": A("mp", "factor")}]})]],
} for param in sorted({p for p, _f in META_GRAMMAR})]
ROUND_OF = lambda r: Filter(Nodes("MetaProposal"), "ro", Eq(A("ro", "round"), r))
META_CLOSE_ROUND = {
    "name": "pw_close_policy_round",
    "comment": "1.6.0: a round of policy proposals closes once every proposal in it is judged and its best "
               "supported one (if any) is adopted; the next round proposes from the policy as it now stands.",
    "match": [["agent", "has_prediction_policy", "pol"]],
    "where": And(Gt(Count(ROUND_OF(A("pol", "meta_round"))), L(0)),
                 Not(Exists(ROUND_OF(A("pol", "meta_round")), "o", Eq(A("o", "outcome"), L(None)))),
                 Or(Not(Exists(ROUND_OF(A("pol", "meta_round")), "o", Eq(A("o", "outcome"), L("supported")))),
                    Exists(ROUND_OF(A("pol", "meta_round")), "o", Eq(A("o", "adopted"), L(1))))),
    "effects": [["set_attr", "pol", "meta_round", T(Plus(A("pol", "meta_round"), L(1)))]],
}

loop_nodes = [
    {"local_id": 0, "type": "PredictionCurriculum", "attrs": {
        "name": "prediction_curriculum", "current_level": 1, "max_level": 5, "last_change_seq": -1}},
    {"local_id": 1, "type": "PredictionPolicy", "attrs": {
        "name": "prediction_policy", "self_improvement": 1, "surprise_floor": 0.15, "window": 3,
        "min_gain": 0.2, "min_abs_gain": 0.05, "retention_weight": 1.0, "authoring": 1,
        "mastery_window": 5, "mastery_z": 1.645, "meta_search": 1,
        "meta_min_trials": 8, "meta_min_yield": 0.15, "experts": 1,
        "meta_proposals": 0, "experiment_cost": 0.001, "meta_min_net": 0.002,
        "skip_last_resort": 0, "meta_round": 0, "meta_max_rounds": 3,
        "description": "The agent's own bar: mean surprise per body-frame (cells) at or under the floor masters a "
                       "level; a model must cut it by 20%, and by 0.05 cells net of any surprise it adds on the "
                       "levels already mastered, to be adopted."}}]
loop_edges = [{"src": {"role": "agent_root"}, "type": "has_prediction_curriculum", "tgt": {"local": 0}, "attrs": {}},
              {"src": {"role": "agent_root"}, "type": "has_prediction_policy", "tgt": {"local": 1}, "attrs": {}}]
OPERATOR_KINDS = ("base", "composition", "residual_fit", "residual_refit", "residual_refit_all", "prune_component",
                  "drop_layer", "add_expert")
WORLD_KINDS = ("box", "open")
for j, (wk, kind) in enumerate(((wk, kind) for wk in WORLD_KINDS for kind in OPERATOR_KINDS), start=2):
    loop_nodes.append({"local_id": j, "type": "PredictionOperatorStat",
                       "attrs": {"kind": kind, "world_kind": wk, "tried": 0, "supported": 0, "adopted": 0,
                                 "enabled": 0}})
    loop_edges.append({"src": {"role": "agent_root"}, "type": "has_operator_stat", "tgt": {"local": j}, "attrs": {}})
# no depends_on: the loop reads the predictor's nodes at run time, and a dependency
# would freeze the predictor seed by closure (it is the part the agent changes)
loop = {"id": "prediction_self_improvement", "version": "1.6.0", "depends_on": [],
        "description": __doc__, "nodes": loop_nodes, "edges": loop_edges, "productions": [],
        "rules": [ADVANCE, MASTER_LAST, FILE, PROPOSE, EXHAUSTED, AUTHOR, REQUEST_FIT, AUTHOR_LAYER, PRUNE_COMPONENT, DROP_LAYER, ADD_EXPERT, ADD_SPECIALIST, JUDGE, ADOPT, COUNT_TRIAL, COUNT_ENABLED, COUNT_ADOPT,
                  META_PROPOSE, META_JUDGE, *META_ADOPT, META_CLOSE_ROUND]}

P_WORLD.write_text(json.dumps(world, indent=1, ensure_ascii=True) + "\n")
P_LOOP.write_text(json.dumps(loop, indent=1, ensure_ascii=True) + "\n")
print("prediction_world", len(candidates), "candidates; prediction_self_improvement", len(loop["rules"]), "rules")
