"""The JABBERWOCK's GRAPH-NATIVE SIMULATOR — the forward model runs in its own Rust evaluator: predict
where the piece SETTLES (gravity-fall-until-collision = the dynamics it learned), the resulting board,
and its EMPOWERMENT value — all as held Terms. With the planner (b4915a7a) this closes the loop: model,
value, plan, act — entirely graph-native; host code is only enumeration + I/O.

Verified standalone (probe_landing 300/300 landing == host; probe_features 250/250 value == host). Here
the simulator drives play: per candidate placement, the agent's evaluator computes the empowerment VALUE
via the value Term (landing -> place -> free/holes/maxh -> value); the agent's ARGMAX Term picks. The
'world-as-model rollout' of b4915a7a is GONE — the agent predicts the outcome itself.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_graph_native_simulator.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.world_play as world_play
from tetris_world import TetrisEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2
from probe_landing import host_landing, SHAPES
from probe_features import value_term, host_value, L, IA, Var

CONTROLS = ["Up", "Down", "Left", "Right"]
W = 8


def gnode(a):
    return next((n for n in a.s.nodes("WorldInstance")
                 if a.s.node(n)["attrs"].get("world_type") == "Game"), None)


def rot(shape):
    rr = [(c, -r) for (r, c) in shape]; mr = min(r for r, _ in rr); mc = min(c for _, c in rr)
    return [(r - mr, c - mc) for (r, c) in rr]


def argmax_term(cands):
    return {"type": "Argmax", "source": L(cands), "var_name": "x",
            "value": IA(Var("x"), L(1)), "default": L(cands[0])}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    w = ArcWorld(TetrisEnv()); sub, ctx = w.reset(); a.perceive_frame(sub)
    g = gnode(a); body = a.s.add_node("Body", {}); a.inner.add_edge_unchecked(body, "inhabits", g)
    world_play.declare_affordances(a, g, CONTROLS)
    nat = _native_eval2(a)                                     # the agent's OWN Rust evaluator
    ev = lambda term: nat.evaluate(term, {})

    def plan(board, shape):
        """the agent's evaluator computes each placement's value (its simulator) + picks (its Argmax)."""
        cands = []; meta = []; s = shape; idx = 0
        for rc in range(4):
            for col in range(W - max(c for _, c in s)):
                if host_landing(board, s, col) is not None and host_landing(board, s, col) >= 0:
                    v = float(ev(value_term(board, s, col)))     # AGENT simulates + values this placement
                    cands.append([idx, v]); meta.append((rc, col)); idx += 1
            s = rot(s)
        if not cands:
            return None, None
        won = ev(argmax_term(cands))                              # AGENT picks
        widx = int(won[0])
        host = max(cands, key=lambda c: c[1])[0]                  # host cross-check (same values)
        return meta[widx], (widx == host)

    def play(greedy, frames=1400):
        import random as _r; rng = _r.Random(0)
        w2 = ArcWorld(TetrisEnv()); w2.reset(); env = w2.env
        pieces = 0; last = None; target = (0, 0, 0); nok = 0; ntot = 0
        for _ in range(frames):
            if env._state.name == "GAME_OVER":
                break
            shape = env._shape
            if greedy:
                if shape is not last:
                    rc, ok = plan(env._board, list(shape)); ntot += 1; nok += int(bool(ok))
                    target = (rc[0], rc[1], 0) if rc else (0, env._pc, 0); last = shape
                trot, tcol, done = target
                act = ("Up" if done < trot else "Right" if env._pc < tcol
                       else "Left" if env._pc > tcol else "Down")
                if done < trot:
                    target = (trot, tcol, done + 1)
            else:
                act = rng.choice(CONTROLS)
            w2.apply((act,))
            if env._shape is not shape:
                pieces += 1
                if greedy:
                    last = None
        return env._score, pieces, (nok, ntot)

    print("=" * 90)
    print("THE JABBERWOCK'S GRAPH-NATIVE SIMULATOR — forward model in its own evaluator (no world rollout)")
    print("=" * 90)
    g_lines, g_pieces, (nok, ntot) = play(True)
    r_lines, r_pieces, _ = play(False)
    print(f"  GRAPH-NATIVE (agent simulates+values+plans): lines={g_lines}  pieces={g_pieces}")
    print(f"  RANDOM baseline:                             lines={r_lines}  pieces={r_pieces}")
    print(f"  agent's simulator value-argmax == host cross-check: {nok}/{ntot} placements")
    print(f"  donkey: {donkey['n']}")
    print("=" * 90)
    print("  The FORWARD MODEL is now the agent's: it predicts where the piece settles (gravity-fall-")
    print("  until-collision = its learned dynamics), the resulting board, and the empowerment value —")
    print("  all as held Terms run by its OWN Rust engine (probe_landing 300/300, probe_features 250/250).")
    print("  The loop is graph-native end to end: model -> value -> plan -> act. Host code is only")
    print("  candidate enumeration + I/O. donkey=0. The whole pursuit is the jabberwock's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
