"""OPEN-ENDED COMPLEXITY — a world that ADDS A LAW each level. The entity carries its model; when a new
law appears its predictions FAIL (the residual spikes); it DISCOVERS the new law's structure and RE-
LEARNS it (grounded continual learning), then the error drops. The residual from the world signals
"the rules changed; learn the new one" — the session's thesis, now across a growing curriculum.

  L1: walls block, hazards kill              (the base dynamics it already learns)
  L2: + ICE  — stepping onto ice SLIDES one more cell in the move direction (a CELL-conditioned law)
  L3: + WIND — every step also drifts one cell in a fixed direction (a GLOBAL law)
The entity distinguishes a CELL-conditioned law (residual tied to a cell-type, in the move direction)
from a GLOBAL law (constant residual everywhere) by the STRUCTURE of its prediction residual. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_levels.py
"""
from __future__ import annotations
import os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
HG, WG = 12, 12
FREE, WALL, HAZ, ICE = 0, 1, 2, 3
EFF = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def make_level(level, seed):
    rng = random.Random(seed)
    g = [[WALL if rng.random() < 0.18 else FREE for _ in range(WG)] for _ in range(HG)]
    for _ in range(8):
        g[rng.randrange(HG)][rng.randrange(WG)] = HAZ
    if level >= 2:
        for _ in range(14):
            r, c = rng.randrange(HG), rng.randrange(WG)
            if g[r][c] == FREE:
                g[r][c] = ICE
    wind = (0, 1) if level >= 3 else None                       # the L3 global law
    return g, wind


def free_at(g, r, c):
    return 0 <= r < HG and 0 <= c < WG and g[r][c] != WALL


def world_step(g, wind, pos, ctrl):
    """the WORLD's true dynamics for this level (the entity does NOT see this)."""
    dr, dc = EFF[ctrl]; r, c = pos
    nr, nc = r + dr, c + dc
    if not free_at(g, nr, nc):
        nr, nc = r, c                                          # wall/edge blocks
    if 0 <= nr < HG and 0 <= nc < WG and g[nr][nc] == ICE:     # L2: ice slides one more
        sr, sc = nr + dr, nc + dc
        if free_at(g, sr, sc):
            nr, nc = sr, sc
    if wind is not None:                                       # L3: global drift
        wr, wc = nr + wind[0], nc + wind[1]
        if free_at(g, wr, wc):
            nr, nc = wr, wc
    ended = (g[nr][nc] == HAZ)
    return (nr, nc), ended


def model_step(g, model, pos, ctrl):
    """the ENTITY's prediction using the laws it has learned so far."""
    dr, dc = EFF[ctrl]; r, c = pos
    nr, nc = r + dr, c + dc
    if not free_at(g, nr, nc):
        nr, nc = r, c
    if model.get("slide_type") is not None and 0 <= nr < HG and 0 <= nc < WG and g[nr][nc] == model["slide_type"]:
        sr, sc = nr + dr, nc + dc
        if free_at(g, sr, sc):
            nr, nc = sr, sc
    if model.get("wind") is not None:
        wr, wc = nr + model["wind"][0], nc + model["wind"][1]
        if free_at(g, wr, wc):
            nr, nc = wr, wc
    ended = (g[nr][nc] == HAZ)
    return (nr, nc), ended


def explore(g, wind, model, steps=700):
    """play; record where the entity's MODEL mispredicts (the residual)."""
    rng = random.Random(0); pos = (HG // 2, WG // 2)
    if g[pos[0]][pos[1]] == WALL:
        g[pos[0]][pos[1]] = FREE
    errs = []; n = 0
    for _ in range(steps):
        ctrl = rng.choice(list(EFF))
        pred, _pe = model_step(g, model, pos, ctrl)
        act, ended = world_step(g, wind, pos, ctrl)
        n += 1
        if pred != act:
            onto = None
            tr, tc = pos[0] + EFF[ctrl][0], pos[1] + EFF[ctrl][1]
            if 0 <= tr < HG and 0 <= tc < WG:
                onto = g[tr][tc]
            errs.append((ctrl, pred, act, onto))
        pos = act
        if ended:
            pos = (HG // 2, WG // 2)
            if g[pos[0]][pos[1]] == WALL:
                g[pos[0]][pos[1]] = FREE
    return errs, n


def relearn(errs, model):
    """DISCOVER the new law from the residual's STRUCTURE: a CONSTANT residual everywhere = a GLOBAL law
    (wind); a residual equal to the move-direction concentrated on one cell-type = a CELL law (slide)."""
    res = [(a[0] - p[0], a[1] - p[1]) for ctrl, p, a, onto in errs]
    if not res:
        return None
    # GLOBAL? the residual is the same vector regardless of control
    if len(set(res)) == 1:
        return ("wind", res[0])
    # CELL-conditioned? errors concentrate on one cell-type, residual == that move's effect (a slide)
    from collections import Counter
    ontos = Counter(o for c, p, a, o in errs if o is not None)
    if ontos:
        cell, cnt = ontos.most_common(1)[0]
        slide_like = sum(1 for ctrl, p, a, o in errs if o == cell and (a[0]-p[0], a[1]-p[1]) == EFF[ctrl])
        if cnt / len(errs) > 0.6 and slide_like / max(cnt, 1) > 0.6:
            return ("slide", cell)
    return ("unknown", None)


def main():
    model = {"slide_type": None, "wind": None}                 # base laws (walls/hazards) already in model_step
    print("=" * 84)
    print("OPEN-ENDED COMPLEXITY — the world adds a law each level; the entity detects + re-learns")
    print("=" * 84)
    for level in (1, 2, 3):
        g, wind = make_level(level, 100 + level)
        errs0, n = explore(g, wind, model)
        rate0 = len(errs0) / n
        learned = None
        if rate0 > 0.02:                                       # a new law: predictions fail -> re-learn
            kind, val = relearn(errs0, model)
            if kind == "wind":
                model["wind"] = val; learned = f"GLOBAL law: a constant drift {val} every step (wind)"
            elif kind == "slide":
                tname = {ICE: "ice"}.get(val, f"cell{val}")
                model["slide_type"] = val; learned = f"CELL law: stepping onto {tname} SLIDES one more"
        errs1, n1 = explore(g, wind, model)                    # re-measure with the updated model
        rate1 = len(errs1) / n1
        tag = "(base, already known)" if level == 1 else "(NEW LAW added this level)"
        print(f"\n  LEVEL {level} {tag}")
        print(f"     prediction error with current model: {rate0:.2f}", end="")
        if learned:
            print(f"  -> DETECTED + re-learned: {learned}")
            print(f"     prediction error after re-learning:  {rate1:.2f}  (adapted)")
        else:
            print("   (model already explains it; nothing new to learn)")
    print("=" * 84)
    print("  The world grew in complexity; each new law made the entity's predictions FAIL (the residual")
    print("  spiked); it DISCOVERED the law's structure from the residual (cell-conditioned slide vs a")
    print("  global drift) and RE-LEARNED it, dropping the error back down. Grounded continual learning")
    print("  across a growing curriculum — the same residual-from-the-world thesis, now open-ended. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
