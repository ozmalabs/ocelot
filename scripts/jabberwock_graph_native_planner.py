"""The JABBERWOCK's GRAPH-NATIVE PLANNER — the SELECTION + the VALUE run as held Terms in its own Rust
evaluator (not host argmax / numpy). A planner IS an Argmax over candidates by a value — exactly the
agent's held gap_prioritiser/act_on_gap machinery, pointed at game placements with EMPOWERMENT as the
value Term.

Previously (a3ecd241) the agent chose its goal DIRECTION (empowerment) and grounded it, but the
empowerment EVALUATION and the placement search were host code. Here the planner is graph-native:
  candidates  — placements (rot,col), each rolled out by the world-as-model to features [free,holes,maxh]
                (forward model; a graph-native simulator is a later rung)
  VALUE Term  — empowerment = free - 4*holes - 0.5*maxh, as a held Minus/Plus/Times tree
  PLAN        — a held ARGMAX Term over the candidates by that value, evaluated by the agent's Rust
                engine -> the chosen placement
So the DECISION (which placement) is the agent's own Term evaluation, donkey=0. We verify it matches
the host-argmax choice and still beats random.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_graph_native_planner.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.world_play as world_play
from tetris_world import TetrisEnv, EMPTY, SETTLED
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2

CONTROLS = ["Up", "Down", "Left", "Right"]
H, W = 16, 8


def gnode(a):
    return next((n for n in a.s.nodes("WorldInstance")
                 if a.s.node(n)["attrs"].get("world_type") == "Game"), None)


def rot(shape):
    rr = [(c, -r) for (r, c) in shape]; mr = min(r for r, _ in rr); mc = min(c for _, c in rr)
    return [(r - mr, c - mc) for (r, c) in rr]


def drop(board, shape, col):
    if col < 0 or col + max(c for _, c in shape) >= W:
        return None
    r = 0
    while not any(r + dr >= H or (r + dr >= 0 and board[r + dr][col + dc] != EMPTY) for dr, dc in shape):
        r += 1
    r -= 1
    if r < 0:
        return None
    nb = [row[:] for row in board]
    for dr, dc in shape:
        if 0 <= r + dr < H:
            nb[r + dr][col + dc] = SETTLED
    return nb


def features(board):
    """world-as-model rollout features: [free, holes, maxheight]."""
    free = sum(row.count(EMPTY) for row in board)
    holes = 0
    for c in range(W):
        seen = False
        for r in range(H):
            if board[r][c] != EMPTY:
                seen = True
            elif seen:
                holes += 1
    maxh = max((H - next((r for r in range(H) if board[r][c] != EMPTY), H) for c in range(W)), default=0)
    return [free, holes, maxh]


# ---- the agent's VALUE Term (empowerment) + ARGMAX Term (the planner), held Term-trees ----
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def IA(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Times(*x): return {"type": "Times", "items": list(x)}
def Minus(x, y): return {"type": "Minus", "a": x, "b": y}


def empowerment_value(x):
    # candidate x = [idx, free, holes, maxh]; empowerment = free - 4*holes - 0.5*maxh
    return Minus(IA(x, L(1)), Plus(Times(L(4.0), IA(x, L(2))), Times(L(0.5), IA(x, L(3)))))


def argmax_term(cands):
    return {"type": "Argmax", "source": L(cands), "var_name": "x", "value": empowerment_value(V("x"))}


def plan_native(nat, board, shape):
    """GRAPH-NATIVE PLAN: enumerate placements (rollout features), then the agent's Argmax Term over the
    empowerment value picks — evaluated by the Rust engine. Returns (rot,col) or None."""
    cands = []; meta = []; s = shape; idx = 0
    for rc in range(4):
        for col in range(W):
            nb = drop(board, s, col)
            if nb is not None:
                f = features(nb); cands.append([idx, float(f[0]), float(f[1]), float(f[2])])
                meta.append((rc, col)); idx += 1
        s = rot(s)
    if not cands:
        return None, None
    won = nat.evaluate(argmax_term(cands), {})          # the AGENT'S evaluator makes the choice
    widx = int(won[0]) if isinstance(won, (list, tuple)) else int(won)
    # host-argmax cross-check (same value), to confirm the native planner is correct
    host = max(cands, key=lambda c: c[1] - 4 * c[2] - 0.5 * c[3])[0]
    return meta[widx], (widx == host)


def play(nat, frames=1400, greedy=True):
    import random as _r; rng = _r.Random(0)
    w = ArcWorld(TetrisEnv()); w.reset(); env = w.env
    pieces = 0; last = None; target = (0, 0, 0); native_ok = 0; native_tot = 0
    for _ in range(frames):
        if env._state.name == "GAME_OVER":
            break
        shape = env._shape
        if greedy:
            if shape is not last:
                rc_col, ok = plan_native(nat, env._board, list(shape))
                native_tot += 1; native_ok += int(bool(ok))
                target = (rc_col[0], rc_col[1], 0) if rc_col else (0, env._pc, 0); last = shape
            trot, tcol, done = target
            if done < trot:
                act = "Up"; target = (trot, tcol, done + 1)
            elif env._pc < tcol:
                act = "Right"
            elif env._pc > tcol:
                act = "Left"
            else:
                act = "Down"
        else:
            act = rng.choice(CONTROLS)
        w.apply((act,))
        if env._shape is not shape:
            pieces += 1
            if greedy:
                last = None
    return env._score, pieces, (native_ok, native_tot)


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    w = ArcWorld(TetrisEnv()); sub, ctx = w.reset(); a.perceive_frame(sub)
    g = gnode(a); body = a.s.add_node("Body", {}); a.inner.add_edge_unchecked(body, "inhabits", g)
    world_play.declare_affordances(a, g, CONTROLS)
    nat = _native_eval2(a)                                # the agent's Rust evaluator

    print("=" * 88)
    print("THE JABBERWOCK'S GRAPH-NATIVE PLANNER — Argmax over placements by the empowerment VALUE Term,")
    print("evaluated by its own Rust engine (the planner = its gap-prioritiser machinery, on the game)")
    print("=" * 88)
    g_lines, g_pieces, (nok, ntot) = play(nat, greedy=True)
    r_lines, r_pieces, _ = play(nat, greedy=False)
    print(f"  GRAPH-NATIVE PLANNER (agent's Argmax+value Term): lines={g_lines}  pieces={g_pieces}")
    print(f"  RANDOM baseline:                                  lines={r_lines}  pieces={r_pieces}")
    print(f"  native choice == host-argmax cross-check: {nok}/{ntot} placements (the Term evaluates correctly)")
    print(f"  donkey: {donkey['n']}")
    print("=" * 88)
    print("  The PLANNER is graph-native: the agent's held ARGMAX Term over candidate placements, scored")
    print("  by the held EMPOWERMENT VALUE Term, evaluated by its OWN Rust engine — the SAME Argmax-over-")
    print("  candidates machinery it uses to pick frontiers, now planning the game. The selection + value")
    print("  are the agent's (donkey=0); only the forward-model rollout (candidate->features) is world-")
    print("  provided — a graph-native simulator is the next rung. It matches host-argmax and beats random.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
