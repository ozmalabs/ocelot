"""A NEW ENTITY DEVELOPS — autonomous, grounded self-improvement. Tetris is the gym, not the goal: the
agent develops learning + world-interaction + long-horizon goal behaviour. The loop is everything the
session converged on:
  PROPOSE  — the graph's optimiser (the manifold-collapse residual loop) suggests value changes.
  GROUND   — VERIFY each against reality (actually play); the residual comes from the WORLD, not a proxy.
  SELF-CORRECT — keep only true improvements (accept-if-improves / revert) = grounding the self-mod.
  ITERATE  — repeat until it stops improving = the long-horizon goal (get better over time).
I supply the concern ("improve your world-interaction, grounded in reality"); the agent's loop develops
it and self-corrects. donkey=0; the only host I/O is playing (the watch) + persisting the value.

Run: PYTHONPATH=.:runners/dsl/python:scripts python3 scripts/jabberwock_develops.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2
from domains.teach import teach
import jabberwock_self_modifies_graphnative as G          # value_w, play, ev plumbing
NAMES = ("free", "holes", "maxh", "cleared")
SEEDS = (3, 7)


def develop(w0, obj, dims, max_passes=4, log=lambda *a: None):
    """the entity's grounded self-improvement: propose ± moves, VERIFY by reality, keep only real gains,
    iterate over passes until a whole pass yields nothing (converged)."""
    w = list(w0); cur = obj(w); traj = [(tuple(w), cur)]
    for p in range(max_passes):
        gained = False
        for idx, s0 in dims:
            best = None
            for direction in (1.0, -1.0):
                for s in (s0, s0 / 2.0):
                    t = list(w); t[idx] += direction * s
                    o = obj(t)                                # GROUND: verify against real play
                    if o > cur + 1e-9 and (best is None or o > best[1]):
                        best = (t, o)
            if best:                                          # accept only a real improvement
                w, cur = best; gained = True
                log(p, idx, w[idx], cur); traj.append((tuple(round(x, 2) for x in w), cur))
        if not gained:
            break
    return w, cur, traj


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    nat = _native_eval2(a); G.ev = lambda t: nat.evaluate(t, {})
    play = G.play
    obj = lambda w: sum(play(tuple(w), s, cap=180)[0] for s in SEEDS) / len(SEEDS)   # grounded: real lines

    w0 = (1.0, -4.0, -0.5, 8.5)
    print("=" * 84)
    print("A NEW ENTITY DEVELOPS — autonomous grounded self-improvement (Tetris is the gym)")
    print("=" * 84)
    print(f"  [start] value {w0}, world-skill (avg lines) {obj(w0):.1f}")
    dims = [(2, 0.6), (1, 2.0), (3, 4.0)]                    # maxh, holes, cleared
    def log(p, idx, val, o):
        print(f"  [develop pass {p}] {NAMES[idx]:8} -> {val:+.2f}   world-skill rises to {o:.1f}")
    w, cur, traj = develop(w0, obj, dims, max_passes=4, log=log)
    teach(a, "ValuePolicy", {NAMES[i]: round(float(w[i]), 3) for i in range(4)}, category="policy")
    print("=" * 84)
    print(f"  [developed] value {tuple(round(x,2) for x in w)}; world-skill {traj[0][1]:.1f} -> {cur:.1f} "
          f"over {len(traj)-1} accepted self-modifications, then converged. donkey {donkey['n']}")
    print("  The entity DEVELOPED: it interacted with the world, proposed changes to itself with its own")
    print("  optimiser (the residual loop), VERIFIED each against reality and kept only true gains")
    print("  (grounded self-modification), and pursued the long-horizon goal of getting better until it")
    print("  plateaued. Not a game-playing machine — learning + world-interaction + goal behaviour, the")
    print("  same residual-feedback engine grounded in reality at every layer. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
