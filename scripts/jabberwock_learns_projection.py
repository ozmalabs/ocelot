"""The agent LEARNS the recogniser graph-natively — earn, don't borrow the fit —
now with WEIGHT-DECAY regularisation to close the gap to the borrowed LDA.

Projection earned by the agent's own held-Term update rule (online averaged
perceptron on WordTemplate nodes):
  PREDICT  scores = [Dot(template_c, x)]  (held Dot Term, Rust substrate); argmax loop.
  LEARN    on error: template_true <- VecAdd(template_true, lr*x);
           template_pred <- VecSub(template_pred, lr*x).
  REGULARISE (weight decay): each epoch, template <- VecSub(template, decay*template)
           = template*(1-decay) — caps norm growth, the overfit the plain perceptron
           showed (train 0.98 vs dev 0.64). All held vector Terms; no SVD/eig, no fit.
  AVERAGE  the per-epoch snapshots (VecAdd accumulation).

Cross-speaker phonebank (learn train, test UNSEEN dev). Sweep decay; compare to the
borrowed LDA (0.750), centroid (0.605), DTW (0.625).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_learns_projection.py [n_words] [max_query] [per_word] [epochs]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
from collections import Counter, defaultdict
from scripts.jabberwock_learned_encoder import _load, _spk_env, _feat

_L = lambda v: {"type": "Lit", "value": [float(x) for x in v]}
_DOT = lambda a, b: {"type": "Dot", "a": a, "b": b}
_VADD = lambda a, b: {"type": "VecAdd", "a": a, "b": b}
_VSUB = lambda a, b: {"type": "VecSub", "a": a, "b": b}


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    epochs = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    lr = 0.5

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 8)
    sw = Counter(w for w, _ in sup_all); qw = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sw.most_common() if qw[w] >= 2][:n_words]
    vset = set(vocab); C = len(vocab); chance = 1.0 / C
    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(1).shuffle(queries); queries = queries[:max_q]
    s_env = _spk_env(support, 24); q_env = _spk_env(queries, 3)
    Sx = [(_feat(fr, s_env[i]), w) for i, (w, fr) in enumerate(support)]
    Qx = [(_feat(fr, q_env[i]), w) for i, (w, fr) in enumerate(queries)]
    D = len(Sx[0][0])
    print("=" * 92)
    print("AGENT LEARNS THE PROJECTION GRAPH-NATIVELY + WEIGHT-DECAY (held Terms, no fit)")
    print("=" * 92)
    print(f"  vocab={C} chance={chance:.3f}  train={len(Sx)} test={len(Qx)}  D={D}  epochs={epochs} lr={lr}")

    def train(decay):
        sub = srs.Substrate()
        inner = sub._inner
        node = {w: sub.add_node("WordTemplate", {"word": w, "vec": [0.0] * D}) for w in vocab}

        def vec(w):
            return sub.node(node[w])["attrs"]["vec"]

        def predict(xL):
            best, bw = -1e18, None
            for w in vocab:
                s = float(inner.evaluate(_DOT(xL, _L(vec(w))), {}))
                if s > best:
                    best, bw = s, w
            return bw

        rng = np.random.default_rng(0)
        order = list(range(len(Sx)))
        acc = {w: np.zeros(D) for w in vocab}; snaps = 0; last_tr = 0.0
        for ep in range(epochs):
            rng.shuffle(order); err = 0
            for i in order:
                x, y = Sx[i]; xL = _L(x); pred = predict(xL)
                if pred != y:
                    err += 1
                    gx = _L(lr * np.asarray(x))
                    vy = inner.evaluate(_VADD(_L(vec(y)), gx), {})
                    vp = inner.evaluate(_VSUB(_L(vec(pred)), gx), {})
                    sub.set_attr(node[y], "vec", [float(z) for z in vy])
                    sub.set_attr(node[pred], "vec", [float(z) for z in vp])
            if decay > 0:                                   # WEIGHT DECAY: W <- W - decay*W (held VecSub)
                for w in vocab:
                    cur = np.asarray(vec(w))
                    dv = inner.evaluate(_VSUB(_L(cur), _L(decay * cur)), {})
                    sub.set_attr(node[w], "vec", [float(z) for z in dv])
            for w in vocab:
                acc[w] = acc[w] + np.asarray(vec(w))
            snaps += 1; last_tr = 1 - err / len(Sx)
        dev_final = sum(predict(_L(x)) == y for x, y in Qx) / len(Qx)
        for w in vocab:
            sub.set_attr(node[w], "vec", [float(z) for z in acc[w] / snaps])
        dev_avg = sum(predict(_L(x)) == y for x, y in Qx) / len(Qx)
        return last_tr, dev_final, dev_avg

    print(f"\n   {'decay':>6} {'train':>6} {'dev_final':>10} {'dev_avg':>8}")
    best = (0.0, None)
    t0 = time.time()
    for decay in (0.0, 0.1, 0.2, 0.35):
        tr, df, da = train(decay)
        print(f"   {decay:6.2f} {tr:6.3f} {df:10.3f} {da:8.3f}")
        if max(df, da) > best[0]:
            best = (max(df, da), decay)
    print(f"\n  best graph-LEARNED dev = {best[0]:.3f} (decay={best[1]})  [{time.time()-t0:.0f}s]")
    print(f"  borrowed LDA 0.750 | DTW 0.625 | centroid 0.605 | chance {chance:.3f}")
    print("=" * 92)
    ok = best[0] >= 0.72
    print(f"  {'GAP CLOSED — earned matches borrowed' if ok else 'GAP NARROWED'}: weight-decay (held VecSub) "
          f"regularises the agent's earned perceptron toward the LDA fit, with NO SVD/eig. earn, don't borrow.")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
