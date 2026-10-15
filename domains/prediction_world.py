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
            b[3] += spec["gravity"]
            b[0] += b[2]
            b[1] += b[3]
            if spec["walls"]:
                for i, (vi, size) in ((0, (2, w)), (1, (3, h))):
                    if b[i] < 0:
                        b[i], b[vi] = -b[i], -b[vi]
                    elif b[i] > size - 1:
                        b[i], b[vi] = 2 * (size - 1) - b[i], -b[vi]
            b[2] *= (1.0 - spec["damping"])
            b[3] *= (1.0 - spec["damping"])
    return {"w": w, "h": h, "frames": frames}


def _feed(agent, trace) -> tuple:
    """Run the agent's predictor over an observation trace. Returns (mean
    surprise, scored count)."""
    S, I = agent.s, agent.inner
    n = len(trace["frames"][0])
    bodies = []
    for _ in range(n):
        b = S.add_node("Body", {"w": float(trace["w"]), "h": float(trace["h"])})
        I.add_edge_unchecked(agent.agent, "observes", b)
        bodies.append(b)
    prev = [None] * n
    prev_d = [(0.0, 0.0)] * n
    total, count = 0.0, 0
    for t, obs in enumerate(trace["frames"]):
        for i, b in enumerate(bodies):
            x, y = obs[i]
            if t > WARMUP:
                at = S.node(b)["attrs"]
                if at.get("pred_frame") == t - 1:
                    total += math.hypot(float(at["pred_x"]) - x, float(at["pred_y"]) - y)
                    count += 1
            d = (x - prev[i][0], y - prev[i][1]) if prev[i] is not None else (0.0, 0.0)
            for k, v in (("x", x), ("y", y), ("dx", d[0]), ("dy", d[1]), ("pdx", prev_d[i][0]),
                         ("pdy", prev_d[i][1]), ("obs_frame", t)):
                I.set_attr(b, k, float(v) if k != "obs_frame" else int(v))
            prev[i], prev_d[i] = (x, y), d
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
    ep = S.add_node("PredictionEpisode", {"seq": seq, "level": level, "level_index": len(prior) + 1,
                                          "mean_surprise": round(mean, 6), "scored": count, "seed": seed,
                                          "trace": json.dumps(trace)})
    I.add_edge_unchecked(agent.agent, "has_prediction_episode", ep)
    I.run_rules()
    return {"seq": seq, "level": level, "mean_surprise": mean}


def replay(trace, mask: int) -> float:
    """The agent's predictor rule, in a fresh agent holding only the predictor
    seed with the given model (its component mask), over a recorded trace."""
    from substrate.world_adapter import WorldAdapter
    child = WorldAdapter(seeds=("prediction_world",))
    p = child.s.nodes("Predictor")[0]
    child.inner.set_attr(p, "mask", int(mask))
    mean, _n = _feed(child, trace)
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
        control = sum(replay(t, da["control_mask"]) for t in traces) / len(traces)
        variant = sum(replay(t, da["candidate_mask"]) for t in traces) / len(traces)
        # retention: per level below this one, its most recent `window`
        # episodes; harm = the sum over those levels of the surprise the
        # variant adds (an improvement on one level does not offset another)
        per_level = {}
        for lv in range(1, level):
            lv_eps = sorted((e for e in S.nodes("PredictionEpisode") if S.node(e)["attrs"].get("level") == lv),
                            key=lambda e: S.node(e)["attrs"]["seq"])[-(k // 2):]
            ts = [json.loads(S.node(e)["attrs"]["trace"]) for e in lv_eps]
            if ts:
                c = sum(replay(t, da["control_mask"]) for t in ts) / len(ts)
                v = sum(replay(t, da["candidate_mask"]) for t in ts) / len(ts)
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
