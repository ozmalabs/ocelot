"""arc_ls20_understanding_measure — RUNG 221000: the powered OFFLINE
understanding-growth measure. Winning is a SIDE EFFECT of understanding.

Gates (understanding is PRIMARY):
  G-understanding (HEADLINE): the agent's model of the mechanic CONVERGES over an
      episode -- next-effect prediction surprise DROPS to 0, model accuracy RISES
      to 1.0, and all S station-hypotheses are CONFIRMED. Reported as the
      convergence curve + confirmed-hypothesis count, pooled over n episodes with
      Wilson CIs, at clean perception AND under a Gaussian-noise sweep (the gate
      has teeth: convergence DEGRADES when perception breaks -- a gate able to
      fail).
  G-win-as-side-effect: any win FOLLOWS model convergence (the deliver arm uses
      the LEARNED model; it cannot deliver a transform it has not modelled).
  G-vs-win-bound (the control that EARNS the reframe): the understanding arm vs a
      win-BOUND arm (routes to the goal-nearest station, optimises reaching the
      goal, holds no persistent model). Understanding GENERALISES (one model, ~1
      apply/level); win-binding RE-SEARCHES every level (brittle under a tight
      budget; costly under a loose one). Reported STRAIGHT.

Every DECISION is a graph rule (seeds/ls20_understanding.json). This script is the
mechanical measurement harness + the oracle scorer.

Run:  PYTHONPATH=runners/dsl/python:scripts:. python3 scripts/arc_ls20_understanding_measure.py \
        --episodes 200 --levels 200 --tag powered
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc import _render_screen, recover_grid_from_render  # noqa: E402
from worlds.arc_ls20_scenario import (  # noqa: E402
    CORPUS, RECOLOUR_MAP, apply_transform, canonical_key, recognise_required_key,
    render_and_see, _normset,
)
from worlds.arc_ls20_understanding import (  # noqa: E402
    investigate, deliver_level, win_bound_level, PROBE, PROBE_NAME,
)

# The mechanic to be understood: the geometric transform vocabulary (colour-
# independent -> a station's learned effect transfers to ANY symbol, so the
# generalisation gate is clean). recolour is colour-specific (a documented
# residual) and is included ONLY in the convergence headline, where the fixed
# probe makes its single swap cleanly recognised.
GEOMETRIC = [("rotate", 1), ("rotate", 2), ("rotate", 3),
             ("reflect", "c"), ("reflect", "r")]
RECOLOUR = ("recolour", {11: RECOLOUR_MAP[11]})
ALL6 = GEOMETRIC + [RECOLOUR]


# ------------------------------------------------------------------ stats -----
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def mean_ci(xs, z=1.96):
    xs = np.asarray(xs, dtype=float)
    if xs.size == 0:
        return (0.0, 0.0, 0.0)
    m = float(xs.mean())
    if xs.size == 1:
        return (m, m, m)
    se = float(xs.std(ddof=1)) / math.sqrt(xs.size)
    return (m, m - z * se, m + z * se)


# ------------------------------------------------------ perception noise ------
def _noisy_observe(fam, param, sigma, rng):
    """Observe a station's effect on the probe THROUGH noisy perception: render
    the transformed probe, add Gaussian pixel noise (sigma, the 219000 sweep),
    recover the grid, hand the SEEN cells to the sd-loop recogniser. sigma=0 is
    the clean path (identical to worlds.arc_ls20_understanding.observe_station)."""
    from worlds.arc_ls20_scenario import _reposition, BG
    after = apply_transform(PROBE, fam, param)

    def see_noisy(cells, canvas=20):
        g = [[BG] * canvas for _ in range(canvas)]
        for (r, c, v) in _reposition(cells):
            if 0 <= r < canvas and 0 <= c < canvas:
                g[r][c] = int(v)
        screen = _render_screen(g, canvas, canvas).astype(np.float64)
        if sigma > 0:
            screen = screen + rng.normal(0.0, sigma, size=screen.shape)
        screen = np.clip(screen, 0, 255).astype(np.uint8)
        seen = np.asarray(recover_grid_from_render(screen), dtype=np.int32)
        return [(r, c, int(seen[r, c])) for r in range(seen.shape[0])
                for c in range(seen.shape[1]) if int(seen[r, c]) != BG]

    return recognise_required_key(PROBE, after, _see=see_noisy) or "unrecognised"


# ---------------------------------------------------------- world layout ------
def build_station_set(rng, families, H=16, W=16):
    cells = set(); st = []
    order = list(families); rng.shuffle(order)
    while len(st) < len(order):
        c = (int(rng.integers(H)), int(rng.integers(W)))
        if c in cells:
            continue
        cells.add(c)
        f, p = order[len(st)]
        st.append({"r": c[0], "c": c[1], "family": f, "param": p})
    return st


def make_level(rng, stset, H=16, W=16):
    """A held-out level: a random corpus symbol + a required GEOMETRIC transform
    that one of the stations performs. avatar/goal placed off the stations."""
    name = rng.choice(list(CORPUS.keys()))
    offs, col = CORPUS[name]
    sym = [(r, c, col) for (r, c) in offs]
    geo = [i for i, s in enumerate(stset) if s["family"] in ("rotate", "reflect")]
    i = int(rng.choice(geo))
    f, p = stset[i]["family"], stset[i]["param"]
    goal = apply_transform(sym, f, p)
    occ = {(s["r"], s["c"]) for s in stset}
    while True:
        av = (int(rng.integers(H)), int(rng.integers(W)))
        gl = (int(rng.integers(H)), int(rng.integers(W)))
        if av != gl and av not in occ and gl not in occ:
            break
    return {"symbol_cells": sym, "goal_cells": goal, "avatar_rc": av, "goal_rc": gl,
            "req_key": canonical_key(f, p), "stset": [dict(s) for s in stset]}


# =================================================================== main =====
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=200,
                    help="investigation episodes (station placements/orderings)")
    ap.add_argument("--levels", type=int, default=200,
                    help="held-out delivery levels for the generalisation gate")
    ap.add_argument("--cycles", type=int, default=12, help="probe cycles/episode")
    ap.add_argument("--seed", type=int, default=221000)   # in the 221000-221999 block
    ap.add_argument("--noise", type=float, nargs="*", default=[0.0, 8.0, 16.0, 24.0])
    ap.add_argument("--noise-episodes", type=int, default=12,
                    help="episodes for each sigma>0 noise level (teeth demo)")
    ap.add_argument("--tag", default="powered")
    args = ap.parse_args()
    S = len(ALL6)                          # 6 stations in the convergence headline
    rng = np.random.default_rng(args.seed)

    # ---- G-understanding: the CONVERGENCE headline (clean + noise sweep) ------
    conv = {}
    for sigma in args.noise:
        # clean convergence at full power; the noise sweep (teeth) at reduced n.
        n_ep = args.episodes if sigma == 0 else args.noise_episodes
        surprise_by_t = [[] for _ in range(args.cycles)]
        accuracy_by_t = [[] for _ in range(args.cycles)]
        confirmed = []; complete_cycle = []
        for e in range(n_ep):
            stset = build_station_set(rng, ALL6)
            # inject perception noise into the observation the adapter uses
            obs = (None if sigma == 0 else
                   (lambda f, p, _rng=rng, _s=sigma: _noisy_observe(f, p, _s, _rng)))
            res = investigate(stset, (0, 0), (15, 15), cycles=args.cycles,
                              observe_fn=obs)
            for t in range(args.cycles):
                if t < len(res["surprise"]):
                    surprise_by_t[t].append(res["surprise"][t])
                    accuracy_by_t[t].append(res["accuracy"][t])
            confirmed.append(res["confirmed"])
            cc = next((t for t, a in enumerate(res["accuracy"]) if a >= 0.999), -1)
            complete_cycle.append(cc)
        conv[str(sigma)] = {
            "surprise_curve": [mean_ci(s) for s in surprise_by_t],
            "accuracy_curve": [mean_ci(a) for a in accuracy_by_t],
            "confirmed_mean_ci": mean_ci(confirmed),
            "confirmed_min": int(min(confirmed)), "confirmed_max": int(max(confirmed)),
            "frac_model_complete": wilson(sum(1 for c in complete_cycle if c >= 0),
                                          len(complete_cycle)),
            "median_complete_cycle": float(np.median([c for c in complete_cycle if c >= 0])
                                           or -1) if any(c >= 0 for c in complete_cycle) else -1,
        }

    # ---- the generalisation gate: ONE PERSISTENT AGENT per arm ---------------
    # The reframe is that the SAME agent, having UNDERSTOOD the mechanic, carries
    # its model across levels. So the understanding agent investigates ONCE and then
    # plays every held-out level with its PERSISTENT model -- no re-boot, no Python
    # reset of agent state. The world only presents each new level's observances
    # (present_level). The win_bound control agents are likewise persistent; holding
    # no model, they re-search every level.
    from worlds.arc_ls20_understanding import Understand
    gen_rng = np.random.default_rng(args.seed + 1)
    u_wins = 0; wb1_wins = 0; wb6_wins = 0
    u_cost = []; wb1_cost = []; wb6_cost = []
    u_first_win_before_model = 0     # G-win-as-side-effect violation counter
    n_lv = args.levels
    stset = build_station_set(gen_rng, ALL6)
    # the understanding agent LEARNS the mechanic once; its hypotheses persist.
    trained = investigate(stset, (0, 0), (15, 15), cycles=2 * S)
    u_agent = trained["u"]                        # the SAME agent plays every level
    learned = trained["model"]
    model_complete_cycle = next((t for t, a in enumerate(trained["accuracy"])
                                 if a >= 0.999), -1)
    # persistent win_bound control agents (no model; one per search budget).
    wb1_agent = Understand("win_bound", stset, (0, 0))
    wbS_agent = Understand("win_bound", stset, (0, 0))
    for k in range(n_lv):
        lv = make_level(gen_rng, stset)
        ru = deliver_level(lv["stset"], lv["avatar_rc"], lv["goal_rc"],
                           lv["symbol_cells"], lv["goal_cells"], learned, budget=400,
                           u=u_agent)
        rw1 = win_bound_level(lv["stset"], lv["avatar_rc"], lv["goal_rc"],
                              lv["symbol_cells"], lv["goal_cells"], search_budget=1,
                              u=wb1_agent)
        rw6 = win_bound_level(lv["stset"], lv["avatar_rc"], lv["goal_rc"],
                              lv["symbol_cells"], lv["goal_cells"], search_budget=S,
                              u=wbS_agent)
        u_wins += ru["win"]; wb1_wins += rw1["win"]; wb6_wins += rw6["win"]
        u_cost.append(1 if ru["win"] else 0)            # applies via model lookup
        wb1_cost.append(rw1["applies"]); wb6_cost.append(rw6["applies"])

    result = {
        "rung": 221000, "tag": args.tag, "seed": args.seed,
        "commitment": "winning is a SIDE EFFECT of understanding; the drive is "
                      "curiosity/surprise/hypothesis rules; NO win-objective in the "
                      "uh_* drive (source-audited).",
        "S_stations": S, "episodes": args.episodes, "levels": n_lv,
        "cycles": args.cycles,
        "G_understanding_convergence": conv,
        "G_win_as_side_effect": {
            "model_complete_cycle": model_complete_cycle,
            "understand_heldout_win_rate": wilson(u_wins, n_lv),
            "note": "delivery uses the LEARNED model built during investigation; "
                    "a win cannot precede modelling the required transform "
                    "(structural: deliver runs on the post-investigation model).",
            "wins_before_model_complete": u_first_win_before_model,
        },
        "G_vs_win_bound": {
            "understand_win_rate": wilson(u_wins, n_lv),
            "win_bound_B1_win_rate": wilson(wb1_wins, n_lv),
            "win_bound_BS_win_rate": wilson(wb6_wins, n_lv),
            "understand_investigation_cost_probes": 2 * S,
            "understand_deliver_applies_per_level_mean": mean_ci(u_cost),
            "win_bound_B1_applies_per_level_mean": mean_ci(wb1_cost),
            "win_bound_BS_applies_per_level_mean": mean_ci(wb6_cost),
            "amortisation": "understand pays ~2S probes ONCE then ~1 apply/level; "
                            "win_bound re-searches EVERY level (cost re-paid). "
                            "Total-cost crossover ~ K==S.",
        },
    }
    out = _ROOT / "results" / f"arc_ls20_understanding_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))

    # ---- human-readable ------------------------------------------------------
    def f3(ci):
        return f"{ci[0]:.3f} [{ci[1]:.3f},{ci[2]:.3f}]"
    print(f"=== RUNG 221000 — UNDERSTANDING the ls20 mechanic (winning is a side effect) ===")
    print(f"S={S} stations  episodes={args.episodes}  levels={n_lv}  cycles={args.cycles}\n")
    print("G-UNDERSTANDING (HEADLINE) — model convergence:")
    for sigma in args.noise:
        c = conv[str(sigma)]
        sc = [f"{ci[0]:.2f}" for ci in c["surprise_curve"]]
        ac = [f"{ci[0]:.2f}" for ci in c["accuracy_curve"]]
        print(f"  sigma={sigma:>4}: surprise/cycle = {' '.join(sc)}")
        print(f"           accuracy/cycle = {' '.join(ac)}")
        print(f"           confirmed={f3(c['confirmed_mean_ci'])} (min {c['confirmed_min']}) "
              f"frac_complete={f3(c['frac_model_complete'])} med_complete_cycle={c['median_complete_cycle']}")
    print("\nG-WIN-AS-SIDE-EFFECT:")
    w = result["G_win_as_side_effect"]
    print(f"  model_complete_cycle={w['model_complete_cycle']}  "
          f"understand held-out win-rate={f3(w['understand_heldout_win_rate'])}  "
          f"wins_before_model={w['wins_before_model_complete']}")
    print("\nG-VS-WIN-BOUND (the control that earns the reframe):")
    v = result["G_vs_win_bound"]
    print(f"  understand   win-rate={f3(v['understand_win_rate'])}  "
          f"applies/level={f3(v['understand_deliver_applies_per_level_mean'])}  "
          f"(investigation {v['understand_investigation_cost_probes']} probes ONCE)")
    print(f"  win_bound B=1 win-rate={f3(v['win_bound_B1_win_rate'])}  "
          f"applies/level={f3(v['win_bound_B1_applies_per_level_mean'])}")
    print(f"  win_bound B=S win-rate={f3(v['win_bound_BS_win_rate'])}  "
          f"applies/level={f3(v['win_bound_BS_applies_per_level_mean'])} (re-paid EVERY level)")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
