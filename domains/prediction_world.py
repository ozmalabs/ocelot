"""The prediction world (2026-10-10): the mechanical half of a graded, closed
world for demonstrating endemic self-improvement. See
scripts/gen_prediction_world.py for the design; the decisions (what the
agent predicts, when it is surprised enough to file a concern, which model it
tries, whether it keeps it, when it moves on) are graph rules in
seeds/prediction_world.json and seeds/prediction_self_improvement.json.

This module only:
  * simulates the levels (deterministic per seed);
  * runs an episode: each frame it writes the observed position, the
    displacement since the last frame and the one before (dx, pdx) onto a Body
    node the agent observes, runs the agent's rules, and measures the surprise
    -- the distance between the agent's committed prediction and the next
    observation (frames before the first two observations are not scored);
  * records the episode on a PredictionEpisode node (mean surprise and the
    observation trace);
  * runs a requested predictor-edit Experiment: replays the agent's own
    recorded episodes at the experiment's level, and of the levels below it
    (retention), through a fresh agent holding only the predictor seed, once
    with the control model and once with the candidate, and writes the mean
    surprises on the Experiment.
"""
from __future__ import annotations

import json
import math
import random

LEVELS = {
    1: {"name": "drift", "w": 1000.0, "h": 1000.0, "gravity": 0.0, "damping": 0.0, "walls": False, "frames": 20},
    2: {"name": "bounce", "w": 20.0, "h": 20.0, "gravity": 0.0, "damping": 0.0, "walls": True, "frames": 40},
    3: {"name": "fall", "w": 1000.0, "h": 1000.0, "gravity": 0.5, "damping": 0.0, "walls": False, "frames": 20},
    4: {"name": "glide", "w": 1000.0, "h": 1000.0, "gravity": 0.0, "damping": 0.3, "walls": False, "frames": 15,
        "speed": (6.0, 10.0)},
    5: {"name": "bounce under gravity", "w": 30.0, "h": 30.0, "gravity": 0.5, "damping": 0.0, "walls": True,
        "frames": 40},
}
N_BODIES = 3
WARMUP = 2          # the first frames carry no displacement history to predict from


def heldout_levels(draw_seed: int, k: int = 8, first_id: int = 101) -> dict:
    """K held-out level specs drawn from a physics family broader than the
    curriculum: open space or a box (15-40 cells), downward and sideways
    gravity, damping, and bounces that lose energy (restitution < 1), in any
    combination. The draw seed is fixed by the pre-registration protocol
    (docs/research/engine_substrate/PREDICTION_WORLD_HELDOUT_PROTOCOL_20261010.md),
    not chosen by whoever runs it."""
    rnd = random.Random(draw_seed)
    out = {}
    for j in range(k):
        walls = rnd.random() < 0.6
        size = float(rnd.randint(15, 40)) if walls else 1000.0
        spec = {"name": f"heldout_{j}", "w": size, "h": size, "walls": walls,
                "gravity": round(rnd.uniform(0.1, 0.8), 3) if rnd.random() < 0.6 else 0.0,
                "gravity_x": round(rnd.choice([-1, 1]) * rnd.uniform(0.05, 0.4), 3) if rnd.random() < 0.3 else 0.0,
                "damping": round(rnd.uniform(0.05, 0.35), 3) if rnd.random() < 0.4 else 0.0,
                "restitution": round(rnd.uniform(0.6, 0.95), 3) if walls and rnd.random() < 0.5 else 1.0,
                "frames": rnd.randint(20, 40)}
        if spec["damping"] and rnd.random() < 0.5:
            spec["speed"] = (4.0, 8.0)
        out[first_id + j] = spec
    return out


def simulate(level: int, seed: int) -> dict:
    """{w, h, frames: [[(x, y) per body] per frame]} for one episode."""
    spec = LEVELS[level]
    rnd = random.Random(seed * 1009 + level)
    w, h = spec["w"], spec["h"]
    bodies = []
    for _ in range(N_BODIES):
        if spec["walls"]:
            x, y = rnd.uniform(2, w - 3), rnd.uniform(2, h - 3)
        else:
            x, y = rnd.uniform(w * 0.4, w * 0.6), rnd.uniform(h * 0.4, h * 0.6)
        lo, hi = spec.get("speed", (0.6, 2.0))
        vx, vy = rnd.choice([-1, 1]) * rnd.uniform(lo, hi), rnd.choice([-1, 1]) * rnd.uniform(lo, hi)
        bodies.append([x, y, vx, vy])
    frames = []
    for _t in range(spec["frames"]):
        frames.append([(round(b[0], 6), round(b[1], 6)) for b in bodies])
        for b in bodies:
            b[2] += spec.get("gravity_x", 0.0)
            b[3] += spec["gravity"]
            b[0] += b[2]
            b[1] += b[3]
            if spec["walls"]:
                e = spec.get("restitution", 1.0)
                for i, (vi, size) in ((0, (2, w)), (1, (3, h))):
                    if e == 1.0:
                        if b[i] < 0:
                            b[i], b[vi] = -b[i], -b[vi]
                        elif b[i] > size - 1:
                            b[i], b[vi] = 2 * (size - 1) - b[i], -b[vi]
                    elif b[i] < 0:      # a bounce that loses energy: overshoot and speed scaled by e
                        b[i], b[vi] = -e * b[i], -e * b[vi]
                    elif b[i] > size - 1:
                        b[i], b[vi] = (size - 1) - e * (b[i] - (size - 1)), -e * b[vi]
            b[2] *= (1.0 - spec["damping"])
            b[3] *= (1.0 - spec["damping"])
    return {"w": w, "h": h, "frames": frames}


def _feed(agent, trace, collect=None) -> tuple:
    """Run the agent's predictor over an observation trace. Returns (mean
    surprise, scored count). With `collect`, appends one row per scored body,
    axis and frame: the context and history the prediction was made from,
    and its error (for a ResidualFit)."""
    S, I = agent.s, agent.inner
    n = len(trace["frames"][0])
    bodies = []
    for _ in range(n):
        b = S.add_node("Body", {"w": float(trace["w"]), "h": float(trace["h"])})
        I.add_edge_unchecked(agent.agent, "observes", b)
        bodies.append(b)
    prev = [None] * n
    prev_d = [(0.0, 0.0)] * n
    prev_pd = [(0.0, 0.0)] * n
    total, count = 0.0, 0
    for t, obs in enumerate(trace["frames"]):
        for i, b in enumerate(bodies):
            x, y = obs[i]
            if t > WARMUP:
                at = S.node(b)["attrs"]
                if at.get("pred_frame") == t - 1:
                    total += math.hypot(float(at["pred_x"]) - x, float(at["pred_y"]) - y)
                    count += 1
                    if collect is not None:
                        for ax, nxt in (("x", x), ("y", y)):
                            h = {"x": ("dx", "pdx", "ppdx"), "y": ("dy", "pdy", "ppdy")}[ax]
                            collect.append({"axis": ax, "ctx": int(at.get(f"ctx_{ax}") or 0),
                                            "pos": float(at[ax]),
                                            "hist": [float(at[k]) for k in h] + [float(at.get(f"acc_{ax}") or 0.0)],
                                            "size": float(at["w" if ax == "x" else "h"]), "next": nxt,
                                            "err": abs(float(at[f"pred_{ax}"]) - nxt)})
            d = (x - prev[i][0], y - prev[i][1]) if prev[i] is not None else (0.0, 0.0)
            for k, v in (("x", x), ("y", y), ("dx", d[0]), ("dy", d[1]), ("pdx", prev_d[i][0]),
                         ("pdy", prev_d[i][1]), ("ppdx", prev_pd[i][0]), ("ppdy", prev_pd[i][1]),
                         ("obs_frame", t)):
                I.set_attr(b, k, float(v) if k != "obs_frame" else int(v))
            prev[i], prev_d[i], prev_pd[i] = (x, y), d, prev_d[i]
        I.run_rules()
    for b in bodies:
        remover = getattr(I, "remove_node", None) or S.remove_node
        remover(b)
    return (total / count if count else 0.0), count


def run_episode(agent, seed: int) -> dict:
    """One live episode at the agent's current level; recorded as a
    PredictionEpisode the loop rules read."""
    S, I = agent.s, agent.inner
    cur = S.nodes("PredictionCurriculum")[0]
    level = int(S.node(cur)["attrs"]["current_level"])
    trace = simulate(level, seed)
    mean, count = _feed(agent, trace)
    prior = [e for e in S.nodes("PredictionEpisode") if S.node(e)["attrs"].get("level") == level]
    seq = len(S.nodes("PredictionEpisode"))
    ep = S.add_node("PredictionEpisode", {"seq": seq, "level": level, "level_index": len(prior) + 1, "w": float(trace["w"]),
                                          "mean_surprise": round(mean, 6), "scored": count, "seed": seed,
                                          "trace": json.dumps(trace)})
    I.add_edge_unchecked(agent.agent, "has_prediction_episode", ep)
    I.run_rules()
    return {"seq": seq, "level": level, "mean_surprise": mean}


# the Predictor attributes that define a model (mirrors scripts/gen_prediction_world.py SLOT_KEYS)
N_SLOTS = 2
_LAYER_KEYS = [f"l{i}_bit" for i in range(N_SLOTS)] + [
    f"l{i}_{ax}{c}" for i in range(N_SLOTS) for ax in "xy" for c in "01234"]
N_EXPERTS = 2   # (1.5.0) mirrors the generator: expert e's model under the prefix x<e>_
MODEL_KEYS = ["mask", "n_layers", "ctx_bits", "sig"] + _LAYER_KEYS + [
    f"x{e}_{k}" for e in range(1, N_EXPERTS + 1) for k in ["mask", "n_layers", "ctx_bits"] + _LAYER_KEYS]


def model_of(attrs: dict, prefix: str = "") -> dict:
    """The model a node holds (a Predictor, a PredictorCandidate, or the
    candidate_/control_ side of a SeedDelta)."""
    return {k: attrs.get(prefix + k) for k in MODEL_KEYS if attrs.get(prefix + k) is not None}


def replay(trace, model, collect=None) -> float:
    """The agent's predictor rule, in a fresh agent holding only the predictor
    seed with the given model (a mask, or a model_of dict), over a recorded
    trace."""
    from substrate.world_adapter import WorldAdapter
    child = WorldAdapter(seeds=("prediction_world",))
    p = child.s.nodes("Predictor")[0]
    for k, v in ({"mask": int(model)} if isinstance(model, int) else model).items():
        child.inner.set_attr(p, k, v)
    mean, _n = _feed(child, trace, collect)
    return mean


def run_experiments(agent, window: int | None = None) -> list:
    """Run every requested prediction-world Experiment: control and variant
    replay over the agent's recorded episodes at that level (the most recent
    `window`*2), mean surprise written onto the Experiment."""
    S, I = agent.s, agent.inner
    pol = S.node(S.nodes("PredictionPolicy")[0])["attrs"]
    k = int(window or pol.get("window") or 3) * 2
    out = []
    for exp in S.nodes("Experiment"):
        at = S.node(exp)["attrs"]
        if at.get("game") != "prediction_world" or at.get("status") != "requested":
            continue
        deltas = list(I.neighbours(exp, "has_delta"))
        da = S.node(deltas[0])["attrs"]
        level = int(at.get("level"))
        eps = sorted((e for e in S.nodes("PredictionEpisode") if S.node(e)["attrs"].get("level") == level),
                     key=lambda e: S.node(e)["attrs"]["seq"])[-k:]
        traces = [json.loads(S.node(e)["attrs"]["trace"]) for e in eps]
        control = sum(replay(t, model_of(da, "control_")) for t in traces) / len(traces)
        variant = sum(replay(t, model_of(da, "candidate_")) for t in traces) / len(traces)
        # retention: per level below this one, its most recent `window`
        # episodes; harm = the sum over those levels of the surprise the
        # variant adds (an improvement on one level does not offset another)
        per_level = {}
        for lv in range(1, level):
            lv_eps = sorted((e for e in S.nodes("PredictionEpisode") if S.node(e)["attrs"].get("level") == lv),
                            key=lambda e: S.node(e)["attrs"]["seq"])[-(k // 2):]
            ts = [json.loads(S.node(e)["attrs"]["trace"]) for e in lv_eps]
            if ts:
                c = sum(replay(t, model_of(da, "control_")) for t in ts) / len(ts)
                v = sum(replay(t, model_of(da, "candidate_")) for t in ts) / len(ts)
                per_level[lv] = [round(c, 6), round(v, 6)]
        harm = sum(max(0.0, v - c) for c, v in per_level.values())
        I.set_attr(exp, "retention_by_level", json.dumps(per_level))
        I.set_attr(exp, "retention_harm", round(harm, 6))
        I.set_attr(exp, "control_surprise", round(control, 6))
        I.set_attr(exp, "variant_surprise", round(variant, 6))
        I.set_attr(exp, "replayed_episodes", len(traces))
        I.set_attr(exp, "status", "done")
        out.append({"level": level, "candidate": da.get("candidate_name"),
                    "control": control, "variant": variant, "retention_harm": harm})
    if out:
        I.run_rules()
    return out


CONTEXT_ATOMS = ((1, "reversal"), (2, "after_reversal"))   # mirrors the generator
MIN_FIT_ROWS = 8


def _fit_axis(R):
    """Least squares x' - x = c0*dx + c1*pdx + c2*ppdx + c3 + c4*acc over rows R
    (None when too few)."""
    import numpy as np
    if len(R) < MIN_FIT_ROWS:
        return None
    X = np.array([r["hist"][:3] + [1.0, r["hist"][3]] for r in R])
    y = np.array([r["next"] - r["pos"] for r in R])
    return [round(float(c), 6) for c in np.linalg.lstsq(X, y, rcond=None)[0]]


def _fit_error(coef, R):
    tot = 0.0
    for r in R:
        e = r["size"] - 1.0
        h = r["hist"]
        raw = r["pos"] + coef[0] * h[0] + coef[1] * h[1] + coef[2] * h[2] + coef[3] + coef[4] * h[3]
        raw = -raw if raw < 0 else (2 * e - raw if raw > e else raw)
        tot += abs(raw - r["next"])
    return tot


def _rows(S, model, level, n):
    eps = sorted((e for e in S.nodes("PredictionEpisode") if S.node(e)["attrs"].get("level") == level),
                 key=lambda e: S.node(e)["attrs"]["seq"])[-n:]
    rows = []
    for e in eps:
        replay(json.loads(S.node(e)["attrs"]["trace"]), model, rows)
    return rows, len(eps)


def run_residual_fits(agent, window: int | None = None) -> list:
    """Run every requested ResidualFit: replay the agent's recorded episodes at
    the level with its current model and write ResidualCells, one per context
    atom and fit mode:
      kind 'new'    an atom the model does not condition on: the frames where it
                    holds and no existing layer applies;
      kind 'refit'  (1.3.0) a layer the model holds: the frames that layer
                    predicts (its atom holds, no earlier layer applies);
      mode 'level'  fitted on the level's frames alone;
      mode 'pooled' (1.3.0) fitted on those frames pooled with the same frames
                    from the agent's recorded episodes of the levels below
                    (the ones its retention is weighed on).
    Each cell carries the summed error of the current model on the level's
    frames (residual_sum), the per-axis least-squares coefficients
    x' - x = c0*dx + c1*pdx + c2*ppdx + c3 + c4*acc, and the error the fit would make
    on the level's frames (fit_gain = residual_sum - fit_sum). Which cells
    become candidate models, and which candidate is kept, is the graph's."""
    S, I = agent.s, agent.inner
    pol = S.node(S.nodes("PredictionPolicy")[0])["attrs"]
    k = int(window or pol.get("window") or 3) * 2
    model = model_of(S.node(S.nodes("Predictor")[0])["attrs"])
    out = []
    for rf in S.nodes("ResidualFit"):
        at = S.node(rf)["attrs"]
        if at.get("status") != "requested":
            continue
        level = int(at["level"])
        rows, n_eps = _rows(S, model, level, k)
        others = []
        for lv in range(1, level):
            others += _rows(S, model, lv, k // 2)[0]
        used = int(model.get("ctx_bits") or 0)
        slot_bits = [int(model.get(f"l{i}_bit") or 0) for i in range(int(model.get("n_layers") or 0))]
        for bit, name in CONTEXT_ATOMS:
            if used & bit:
                earlier = sum(b for b in slot_bits[:slot_bits.index(bit)])
                kind, sel = "refit", (lambda r, bit=bit, earlier=earlier: r["ctx"] & bit and not r["ctx"] & earlier)
            else:
                kind, sel = "new", (lambda r, bit=bit: r["ctx"] & bit and not r["ctx"] & used)
            for mode in ("level", "pooled"):
                cell = {"ctx_bit": bit, "atom": name, "kind": kind, "mode": mode, "n": 0, "n_pooled": 0,
                        "residual_sum": 0.0, "fit_sum": 0.0}
                for ax in "xy":
                    R = [r for r in rows if r["axis"] == ax and sel(r)]
                    P = R + ([r for r in others if r["axis"] == ax and sel(r)] if mode == "pooled" else [])
                    resid = sum(r["err"] for r in R)
                    coef = _fit_axis(P)
                    fit = _fit_error(coef, R) if coef is not None else resid
                    cell["n"] += len(R)
                    cell["n_pooled"] += len(P)
                    cell["residual_sum"] += resid
                    cell["fit_sum"] += fit
                    for j, c in enumerate(coef or [0.0] * 5):
                        cell[f"{ax}{j}"] = c
                cell["residual_sum"] = round(cell["residual_sum"], 6)
                cell["fit_sum"] = round(cell["fit_sum"], 6)
                cell["fit_gain"] = round(cell["residual_sum"] - cell["fit_sum"], 6)
                node = S.add_node("ResidualCell", cell)
                I.add_edge_unchecked(rf, "has_cell", node)
                out.append(cell)
        # (1.5.0) a specialist for an expert slot: the best base model the agent has trialled at this level
        # (else its own components) with both context layers fitted from scratch on this level's frames alone
        # (no retention pooling)
        base_trials = [S.node(x)["attrs"] for x in S.nodes("Experiment")
                       if S.node(x)["attrs"].get("level") == level
                       and S.node(x)["attrs"].get("candidate_operator") == "base"
                       and S.node(x)["attrs"].get("variant_surprise") is not None]
        best_base = min(base_trials, key=lambda x: x["variant_surprise"]) if base_trials else None
        spec_model = {"mask": int(best_base["candidate_mask"]) if best_base else int(model.get("mask") or 1)}
        srows, _n = _rows(S, spec_model, level, k)
        cell = {"ctx_bit": 0, "atom": "specialist", "kind": "specialist", "mode": "level", "n": 0, "n_pooled": 0,
                "residual_sum": 0.0, "fit_sum": 0.0, "specialist_mask": spec_model["mask"]}
        ok = True
        for i, (bit, earlier) in enumerate(((1, 0), (2, 1))):
            for ax in "xy":
                R = [r for r in srows if r["axis"] == ax and r["ctx"] & bit and not r["ctx"] & earlier]
                coef = _fit_axis(R)
                ok = ok and coef is not None
                resid = sum(r["err"] for r in R)
                cell["n"] += len(R)
                cell["residual_sum"] += resid
                cell["fit_sum"] += _fit_error(coef, R) if coef is not None else resid
                for j, c in enumerate(coef or [0.0] * 5):
                    cell[f"s{i}_{ax}{j}"] = c
        if ok:
            cell["residual_sum"] = round(cell["residual_sum"], 6)
            cell["fit_sum"] = round(cell["fit_sum"], 6)
            cell["fit_gain"] = round(cell["residual_sum"] - cell["fit_sum"], 6)
            node = S.add_node("ResidualCell", cell)
            I.add_edge_unchecked(rf, "has_cell", node)
            out.append(cell)
        # (1.3.0) a joint refit: every layer the model holds refitted at once, on the frames each predicts
        if len(slot_bits) > 1:
            for mode in ("level", "pooled"):
                cell = {"ctx_bit": 0, "atom": "all", "kind": "refit_all", "mode": mode, "n": 0, "n_pooled": 0,
                        "residual_sum": 0.0, "fit_sum": 0.0}
                for i, bit in enumerate(slot_bits):
                    earlier = sum(slot_bits[:i])
                    sel = (lambda r, bit=bit, earlier=earlier: r["ctx"] & bit and not r["ctx"] & earlier)
                    for ax in "xy":
                        R = [r for r in rows if r["axis"] == ax and sel(r)]
                        P = R + ([r for r in others if r["axis"] == ax and sel(r)] if mode == "pooled" else [])
                        resid = sum(r["err"] for r in R)
                        coef = _fit_axis(P)
                        cell["n"] += len(R)
                        cell["n_pooled"] += len(P)
                        cell["residual_sum"] += resid
                        cell["fit_sum"] += _fit_error(coef, R) if coef is not None else resid
                        cur_coef = [float(model.get(f"l{i}_{ax}{j}") or 0.0) for j in range(5)]
                        for j, c in enumerate(coef if coef is not None else cur_coef):
                            cell[f"s{i}_{ax}{j}"] = c
                cell["residual_sum"] = round(cell["residual_sum"], 6)
                cell["fit_sum"] = round(cell["fit_sum"], 6)
                cell["fit_gain"] = round(cell["residual_sum"] - cell["fit_sum"], 6)
                node = S.add_node("ResidualCell", cell)
                I.add_edge_unchecked(rf, "has_cell", node)
                out.append(cell)
        I.set_attr(rf, "replayed_episodes", n_eps)
        I.set_attr(rf, "status", "done")
    if out:
        I.run_rules()
    return out
