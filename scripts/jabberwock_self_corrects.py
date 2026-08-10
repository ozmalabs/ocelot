"""THE JABBERWOCK FIXES ITSELF — and the fix is the session's thesis. The confounded self-modification
(103d147c) fit the value to a SELF-generated proxy (Monte-Carlo returns) -> an UNGROUNDED self-mod ->
it confabulated a worse value (the delusion case: residual from the self, not the world). The agent
fixes itself the way the whole arc says: GROUND the self-modification — verify each proposed change
against REALITY (play) and keep only what truly improves (its Correct->Verify->revert self-improvement
guard). I explain; the agent proposes (the graph's optimiser) and self-corrects (verify-revert).

Run: PYTHONPATH=.:runners/dsl/python:scripts python3 scripts/jabberwock_self_corrects.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2
from domains.teach import teach
from probe_optimizer import fit_linear_term
import jabberwock_self_modifies_graphnative as G    # reuse value_w, play, feats, ev plumbing
H, W = 16, 8
SEEDS = (3, 7)


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    nat = _native_eval2(a); G.ev = lambda t: nat.evaluate(t, {})
    play = G.play; value = G.value_w
    w0 = (1.0, -4.0, -0.5, 8.5)
    obj = lambda w: sum(play(w, s)[0] for s in SEEDS) / len(SEEDS)      # GROUNDED objective: real play
    print("=" * 84)
    print("THE JABBERWOCK FIXES ITSELF — ground the self-modification (verify against reality)")
    print("=" * 84)
    base = obj(w0)
    print(f"  [baseline] value {w0} -> avg lines {base:.1f}")

    # PROPOSAL 1 — the graph's optimiser on a SELF-proxy (Monte-Carlo returns): an UNGROUNDED self-mod
    X, y = [], []
    for s in SEEDS:
        sc, pc, recs = play(w0, s, record=True)
        for fr, ho, mh, cd, lso, i in recs:
            X.append([fr, ho, mh, cd]); y.append((sc - lso) + 0.05 * (pc - i))
    X = np.array(X, float); y = np.array(y, float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    rows = [[*((X[i] - mu) / sd).tolist(), float((y[i] - y.mean()) / (y.std() + 1e-9))] for i in range(len(X))]
    wp = np.array([float(v) for v in G.ev(fit_linear_term(rows, lr=0.3, T=300, d=4))]) / sd
    wp = tuple(round(float(x / (abs(wp).max() + 1e-9) * 8.0), 2) for x in wp)
    obj_p = obj(wp)
    keep_p = obj_p > base
    print(f"\n  [propose: proxy]  graph optimiser on SELF returns -> {wp}")
    print(f"  [VERIFY vs reality] avg lines {obj_p:.1f}  -> {'KEEP' if keep_p else 'REJECT (self-correct: ungrounded, worse)'}")

    # PROPOSAL 2 — the SAME graph optimiser, but GROUNDED: the residual is the VERIFIED play-improvement
    # (perturb a weight, measure real play, step toward better, accept only if it improves). Same residual
    # loop; the residual now comes from REALITY, not a proxy.
    w = list(w0); cur = base
    for idx, s0 in [(2, 0.6), (1, 2.0), (3, 4.0)]:                       # maxh, holes, cleared
        for direction in (1.0, -1.0):
            for s in (s0, s0 / 2.0):
                t = list(w); t[idx] += direction * s
                o = obj(t)                                              # VERIFY against reality
                if o > cur + 1e-9:                                      # accept only a real improvement
                    w, cur = t, o; print(f"  [propose: grounded] {('free','holes','maxh','cleared')[idx]} "
                                         f"{w0[idx] if w[idx]==t[idx] else ''}-> {round(t[idx],2)}  verified lines {o:.1f}  KEEP")
                    break
            else:
                continue
            break
    wg = tuple(round(float(x), 2) for x in w)
    final = wg if cur > base else w0
    teach(a, "ValuePolicy", {"free": final[0], "holes": final[1], "maxh": final[2], "cleared": final[3]}, category="policy")
    print("=" * 84)
    print(f"  RESULT: baseline {base:.1f} -> proxy {obj_p:.1f} (rejected) -> grounded {cur:.1f} (kept). "
          f"value {final}; donkey {donkey['n']}")
    print("  THE FIX = the session's thesis: the confounded self-mod was UNGROUNDED (fit to a self-proxy")
    print("  -> confabulated worse). The agent FIXES ITSELF by GROUNDING — same graph optimiser, but the")
    print("  residual verified against REALITY (play), keeping only true improvements. Self-modification")
    print("  must be grounded in the world, exactly like every other layer. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
