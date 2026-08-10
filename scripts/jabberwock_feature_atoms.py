"""TINY FEATURE-ATOM DETECTORS + GRAPH RECOGNITION — the floor, the agent's way.

NOT a small conv net embedding a glyph. A LIBRARY of TINY single-purpose detectors -- each a learned atom (a
7x7 feature template: an edge, a curve, a junction, an endpoint) from the agent's OWN sparse_dict_learn Rust
primitive -- and a glyph is the COMPOSITION of which atoms fire WHERE. Recognition runs IN THE GRAPH: a
substrate Argmax over supports by Dot of the spatial firing maps (shared feature-firings). No borrowed nets,
no torch -- the agent's dictionary primitive + graph composition.

Run: PYTHONPATH=runners/dsl/python:. python3 scripts/jabberwock_feature_atoms.py [n_chars]
"""
from __future__ import annotations
import glob, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
import numpy as np
import substrate_rs as srs
from substrate_rs import _native

OMNI = "/tmp/omniglot"; SZ = 28; P = 7; STRIDE = 2; K = 128; BINS = 4
TARGET, GEOM = 95.0, 81.0


def load_strokes(path):
    st, cur = [], []
    for line in open(path):
        s = line.strip()
        if not s or s == "START":
            continue
        if s == "BREAK":
            if cur:
                st.append(np.asarray(cur, float)); cur = []
            continue
        q = s.split(",")
        if len(q) >= 2:
            cur.append((float(q[0]), float(q[1])))
    if cur:
        st.append(np.asarray(cur, float))
    return [s for s in st if len(s) >= 1]


def render(path):
    strokes = load_strokes(path)
    allp = np.concatenate([s for s in strokes if len(s)], 0) if strokes else np.zeros((0, 2))
    a = np.zeros((SZ, SZ), np.float32)
    if len(allp):
        mn, mx = allp.min(0), allp.max(0); span = np.maximum(mx - mn, 1e-6)
        for s in strokes:
            q = (s - mn) / span * (SZ - 4) + 2
            for i in range(len(q) - 1):
                for t in np.linspace(0, 1, 30):
                    x, y = (q[i] * (1 - t) + q[i + 1] * t).astype(int)
                    a[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] = 1.0
    return a


def patches(img):
    locs = list(range(0, SZ - P + 1, STRIDE)); out = []
    for y in locs:
        for x in locs:
            out.append(img[y:y + P, x:x + P].reshape(-1))
    return np.asarray(out), len(locs)            # (npatch, P*P), grid side


def chars(split):
    out = []
    for al in sorted(glob.glob(f"{OMNI}/strokes_{split}/*")):
        for c in sorted(glob.glob(al + "/*")):
            dr = sorted(glob.glob(c + "/*.txt"))
            if len(dr) >= 2:
                out.append(dr)
    return out


def firing_map(codes, gside):
    """codes (npatch,K) -> spatial-binned max-pooled firing map (BINS*BINS*K,), L2-normalised = the composition."""
    C = codes.reshape(gside, gside, K)
    fm = np.zeros((BINS, BINS, K), np.float32)
    for by in range(BINS):
        for bx in range(BINS):
            ys = slice(by * gside // BINS, (by + 1) * gside // BINS)
            xs = slice(bx * gside // BINS, (bx + 1) * gside // BINS)
            blk = C[ys, xs].reshape(-1, K)
            if len(blk):
                fm[by, bx] = blk.max(0)
    v = fm.reshape(-1)
    return (v / (np.linalg.norm(v) + 1e-9)).astype(np.float64)


def main():
    n_chars = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    print("=" * 96)
    print("TINY FEATURE-ATOM DETECTORS (agent's sparse_dict_learn) + GRAPH-NATIVE composition recognition.")
    print("=" * 96, flush=True)
    rng = np.random.default_rng(0)

    # --- learn the tiny feature-atom detectors from background patches (the agent's dictionary primitive) ---
    print("\n  learning tiny feature atoms from background patches...", flush=True)
    bg = chars("background"); bg = [bg[i] for i in rng.permutation(len(bg))[:300]]
    pool = []
    for dr in bg:
        ph, _ = patches(render(dr[0]))
        ph = ph[ph.sum(1) > 0.5]                 # keep patches with stroke content
        pool.append(ph)
    pool = np.concatenate(pool, 0)
    pool = pool[rng.permutation(len(pool))[:20000]]
    d = P * P
    t0 = time.time()
    dic = np.asarray(_native.sparse_dict_learn(pool.reshape(-1).tolist(), len(pool), d, K,
                                               0.10, 4, 0.05, 40, 0.02)).reshape(K, d)
    print(f"    learned {K} tiny atom-detectors (each a {P}x{P} feature template) from {len(pool)} patches "
          f"in {time.time()-t0:.0f}s", flush=True)

    dn = dic / (np.linalg.norm(dic, axis=1, keepdims=True) + 1e-9)    # unit atom-detectors

    def encode_glyph(path):
        ph, g = patches(render(path))
        pn = ph / (np.linalg.norm(ph, axis=1, keepdims=True) + 1e-6)
        resp = np.maximum(pn @ dn.T, 0.0)        # DENSE atom responses (each tiny detector fires by correlation)
        return firing_map(resp, g)               # which atoms fire where (spatial-pooled), robust

    # --- represent eval glyphs by their feature-firing composition ---
    ev = chars("evaluation"); ev = [ev[i] for i in np.random.default_rng(1).permutation(len(ev))[:n_chars]]
    print(f"  encoding {n_chars} held-out glyphs into feature-firing maps...", flush=True)
    sup = np.stack([encode_glyph(dr[0]) for dr in ev])
    qry = np.stack([encode_glyph(dr[1]) for dr in ev])

    # --- recognition IN THE GRAPH: Argmax over supports by Dot of firing maps (graph composition) ---
    def _V(n): return {"type": "Var", "name": n}
    def _A(n, k): return {"type": "Attr", "node": _V(n), "key": k}
    def _L(v): return {"type": "Lit", "value": v}

    class _Pr:
        __slots__ = ("_json",)

        def __init__(s, j): s._json = j
    rng2 = np.random.default_rng(123); cor = tot = 0
    print("  recognising (substrate Argmax over supports by Dot of feature-firings)...", flush=True)
    for _ in range(1000):
        cl = rng2.choice(n_chars, 20, replace=False); qi = int(rng2.integers(20))
        s = srs.Substrate(); sids = []
        for j, c in enumerate(cl):
            n = s.add_node("Sup", {"is_s": 1.0, "fire": sup[c].tolist(), "cls": float(j)}); sids.append(n)
        qn = s.add_node("Qry", {"fire": qry[cl[qi]].tolist()})
        val = {"type": "Dot", "a": _A("s", "fire"), "b": _A("q", "fire")}
        win = s.evaluate(_Pr({"type": "Argmax", "source": {"type": "NodesWhere", "node_type": "Sup",
                              "attr_key": "is_s", "value": _L(1.0)}, "var_name": "s", "value": val,
                              "default": _L(-1.0)}), {"q": qn})
        cor += int(s.node(win)["attrs"]["cls"] == qi); tot += 1
    acc = 100 * cor / tot

    print("\n" + "=" * 96)
    print(f"  20-way 1-shot, held-out Omniglot ({n_chars}-char pool):")
    print(f"    TINY feature-atoms + graph composition : {acc:5.1f}%   ({K} atoms x {P}x{P}, deployed cost ~{K*d/1000:.1f}K weights)")
    print(f"    geometric ceiling ~{GEOM:.0f}   human bar ~{TARGET:.0f}")
    print(f"\n  Each detector is TINY ({P}x{P}={d} weights), dedicated to one feature; the glyph is the graph")
    print(f"  COMPOSITION of which atoms fire where, and recognition runs IN THE GRAPH (substrate Argmax/Dot).")
    print(f"  Agent's own faculties (sparse_dict_learn + graph), no borrowed net.")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
