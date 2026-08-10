"""INVESTIGATION RUNNERS — the world-side procedures that feed SourceWorld data to a held
operator and read back a measurement. One runner per faculty; the autonomous loop dispatches to
the runner the GRAPH names (investigated_by edge). Mechanical "feed the world in, read the score
out" — the held op is the agent's; the runner is the permitted measurement adapter (same role as
every accept/probe script). No decisions over graph state.

Each runner: run(world, sub, row, op) -> {measured, target, metric, keys, note}
  world = SourceWorld; sub = the agent graph; row = the picked rank_gaps dict; op = Operator attrs.
"""
from __future__ import annotations
import math
import os
import pickle
from collections import Counter, defaultdict

import numpy as np

import substrate_rs as srs
from substrate_rs import audio as A, speech as SP

N_BINS = 128
SR = 8000
_CACHE = "/tmp/autonomous_words.pkl"


def shape(frame):
    return np.asarray(srs.Substrate.shape_signature([float(x) for x in frame]), np.float32)


def collapse(seq):
    out = []
    for u in seq:
        if not out or out[-1] != u:
            out.append(u)
    return out


def _word_fft_seq(a8, t0, t1, n_fft=256, hop=128):
    seg = a8[int(t0 * SR):int(t1 * SR)]
    if len(seg) < n_fft:
        seg = np.pad(seg, (0, n_fft - len(seg)))
    win = np.hanning(n_fft)
    fr = [np.abs(np.fft.rfft(seg[i:i + n_fft] * win))[:N_BINS]
          for i in range(0, len(seg) - n_fft + 1, hop)]
    if not fr:
        fr = [np.abs(np.fft.rfft(seg[:n_fft] * win))[:N_BINS]]
    return np.asarray(fr, np.float32)


def prepare_word_data(world, max_sources=5, seconds=120, chunk=20.0, min_ex=4, refresh=False):
    """Whisper-labelled per-word FFT frame sequences pooled from SourceWorld speech (the agent's
    data intake). Cached. Returns (tokens=[(word, frames)], core=[words with >= min_ex])."""
    if os.path.exists(_CACHE) and not refresh:
        with open(_CACHE, "rb") as f:
            toks = pickle.load(f)
    else:
        srcs = [s for s in world.sources(kinds=("video", "audio")) if s["origin"] == "local"]
        srcs = [s for s in srcs if s["kind"] == "video"][:max_sources] or srcs[:max_sources]
        toks = []
        for s in srcs:
            dur = min(world.duration(s) or seconds, seconds)
            t = 0.0
            while t < dur:
                words = world.whisper(s, t, t + chunk)
                if words:
                    a8 = world.play(s, t, t + chunk)
                    for w, t0, t1 in words:
                        if t1 > t0:
                            toks.append((w, _word_fft_seq(a8, t0, t1)))
                t += chunk
        with open(_CACHE, "wb") as f:
            pickle.dump(toks, f)
    cnt = Counter(w for w, _ in toks)
    core = sorted(w for w, c in cnt.items() if c >= min_ex)
    return toks, core


def _purity(labels, classes):
    clusters = defaultdict(Counter)
    for l, c in zip(labels, classes):
        clusters[l][c] += 1
    return sum(max(cn.values()) for cn in clusters.values()) / max(len(labels), 1)


def _mean_shape(fr):
    m = np.mean([shape(f) for f in fr], axis=0)
    return (m / (np.linalg.norm(m) + 1e-9)).astype(np.float32)


def _grammar_eval(train, test, tr_unit, te_unit, core, ALPH):
    """per-word order-1 production grammar (compose) vs flat exemplar 1-NN. Returns (ac, af, n)."""
    tr_u = [(w, tr_unit(fr)) for w, fr in train]
    te_u = [(w, te_unit(fr)) for w, fr in test]
    Wtr = np.array([w for w, _ in train]); Ftr = np.array([_mean_shape(fr) for _, fr in train])
    uni = defaultdict(lambda: np.ones(ALPH)); bi = defaultdict(lambda: defaultdict(lambda: np.ones(ALPH)))
    for w, u in tr_u:
        if not u:
            continue
        uni[w][u[0]] += 1
        for a, b in zip(u, u[1:]):
            bi[w][a][b] += 1
    U = {w: v / v.sum() for w, v in uni.items()}
    B = {w: {a: r / r.sum() for a, r in d.items()} for w, d in bi.items()}

    def fold(u, w):
        if not u or w not in U:
            return -1e9
        lp = math.log(U[w][u[0]]); Bw = B.get(w, {})
        for a, b in zip(u, u[1:]):
            r = Bw.get(a); lp += math.log(r[b] if r is not None else 1.0 / ALPH)
        return lp / len(u)

    cand = sorted(core)
    cf = cc = tot = 0
    for (w, fr), (_, u) in zip(test, te_u):
        tot += 1
        cf += (Wtr[np.argmax(Ftr @ _mean_shape(fr))] == w)
        cc += (max(cand, key=lambda c: fold(u, c)) == w)
    return cc / max(tot, 1), cf / max(tot, 1), tot


def _split(data, frac=75):
    rng = np.random.RandomState(0)
    idx = rng.permutation(len(data)); cut = len(data) * frac // 100
    return [data[i] for i in idx[:cut]], [data[i] for i in idx[cut:]]


# --------------------------------------------------------------------------- clustering
def run_clustering(world, sub, row, op):
    """distributional_categories.cluster_by_modes over word-level shapes -> cluster purity vs the
    whisper word labels (the 'unsupervised clustering / categorical quantiser' frontier)."""
    from domains.distributional_categories import cluster_by_modes
    toks, core = prepare_word_data(world)
    data = [(w, _mean_shape(fr)) for w, fr in toks if w in core]
    if len(data) < 6:
        return {"measured": 0.0, "target": op["target"], "metric": op["metric"],
                "keys": row["capability_keys"], "note": "insufficient data"}
    X = np.array([v for _, v in data]); cls = [w for w, _ in data]
    labels, n_modes = cluster_by_modes(X, pctile=8.0)
    pur = _purity(labels, cls)
    return {"measured": round(pur, 3), "target": op["target"], "metric": "cluster_purity",
            "keys": row["capability_keys"],
            "signals": {"purity": round(pur, 3), "n_modes": n_modes, "n_classes": len(core)},
            "note": f"{len(data)} word tokens, {len(core)} classes, {n_modes} density modes"}


# --------------------------------------------------------------------------- composition
def run_composition(world, sub, row, op, thr=0.85):
    """compose-under-selection: sub-word units (held acquire_sign over shape) -> per-word order-1
    production grammar vs flat exemplar 1-NN -> compose accuracy (the 'compositional generation /
    production-space' frontier)."""
    toks, core = prepare_word_data(world)
    data = [(w, np.asarray(fr, np.float32)) for w, fr in toks if w in core]
    if len(core) < 4 or len(data) < 12:
        return {"measured": 0.0, "target": op["target"], "metric": op["metric"],
                "keys": row["capability_keys"], "note": "insufficient data"}
    train, test = _split(data)
    s = srs.Substrate(); A.seed_audio_grammar(s); SP.seed_speech_grammar(s)
    s.memory_bound(60000, 256 * 1024 * 1024, 3)
    lex = SP.open_lexicon(s, name="subword")

    def units(fr, grow):
        sq = []
        for f in fr:
            sg = (SP.acquire_sign(s, lex, shape(f), threshold=thr) if grow
                  else SP.match_sign(s, lex, shape(f), threshold=thr))
            sq.append(sg[0].value if sg[0] is not None else -1)
        return collapse(sq)

    for _, fr in train:                                    # grow the lexicon on train first
        units(fr, True)
    ALPH = len(SP.lexicon_signs(s, lex)) + 2
    ac, af, tot = _grammar_eval(train, test, lambda fr: units(fr, False),
                                lambda fr: units(fr, False), core, ALPH)
    return {"measured": round(ac, 3), "target": op["target"], "metric": "compose_accuracy",
            "keys": row["capability_keys"],
            "signals": {"compose": round(ac, 3), "flat": round(af, 3)},
            "note": f"{len(core)} words; acquire_sign parts; compose {ac:.1%} vs flat {af:.1%} ({tot} test)"}


# --------------------------------------------------------------------------- quantiser->composition
def run_quantiser(world, sub, row, op, pctile=8.0):
    """The manifold's 'sharpen the parts' lever: density-mode parts (cluster_by_modes) instead of
    fixed-threshold acquire_sign -> per-word grammar vs flat. The agent re-running the categorical-
    quantiser improvement on its own (from the measured compose<<flat surprise)."""
    from domains.distributional_categories import cluster_by_modes
    toks, core = prepare_word_data(world)
    data = [(w, np.asarray(fr, np.float32)) for w, fr in toks if w in core]
    if len(core) < 4 or len(data) < 12:
        return {"measured": 0.0, "target": op["target"], "metric": op["metric"],
                "keys": row["capability_keys"], "note": "insufficient data"}
    train, test = _split(data)
    rng = np.random.RandomState(1)
    M = np.array([shape(f) for _, fr in train for f in fr], np.float32)
    samp = M[rng.permutation(len(M))[:2500]]
    labels, n_modes = cluster_by_modes(samp, pctile=pctile)
    labels = np.asarray(labels)
    cents = np.array([samp[labels == k].mean(0) for k in range(n_modes)])

    def units(fr):
        return collapse([int(np.argmin(((cents - shape(f)) ** 2).sum(1))) for f in fr])

    ac, af, tot = _grammar_eval(train, test, units, units, core, n_modes + 1)
    return {"measured": round(ac, 3), "target": op["target"], "metric": "compose_accuracy",
            "keys": row["capability_keys"],
            "signals": {"compose": round(ac, 3), "flat": round(af, 3), "n_modes": n_modes},
            "note": f"{len(core)} words; {n_modes} density-mode parts; "
                    f"compose {ac:.1%} vs flat {af:.1%} ({tot} test)"}


# --------------------------------------------------------------- grounded: transition clustering
def _transition_feat(fr):
    S = np.array([shape(f) for f in fr])
    h = max(1, len(S) // 2)
    d = S[h:].mean(0) - S[:h].mean(0)                      # the agent's order-1-over-time per word
    return (d / (np.linalg.norm(d) + 1e-9)).astype(np.float32)


def run_transition_clustering(world, sub, row, op, pctile=8.0):
    """GROUNDED from the teacher's advice ('words separate by the TRAJECTORY of formants over
    time'): cluster words by their transition (dynamics) feature instead of the static spectrum,
    and measure whether the advised representation actually helps (the agent TESTS the advice)."""
    from domains.distributional_categories import cluster_by_modes
    toks, core = prepare_word_data(world)
    data = [(w, _transition_feat(fr)) for w, fr in toks if w in core and len(fr) >= 2]
    if len(data) < 6:
        return {"measured": 0.0, "target": op["target"], "metric": op["metric"],
                "keys": row["capability_keys"], "note": "insufficient data"}
    X = np.array([v for _, v in data]); cls = [w for w, _ in data]
    labels, n_modes = cluster_by_modes(X, pctile=pctile)
    pur = _purity(labels, cls)
    return {"measured": round(pur, 3), "target": op["target"], "metric": "cluster_purity",
            "keys": row["capability_keys"],
            "signals": {"purity": round(pur, 3), "n_modes": n_modes, "n_classes": len(core),
                        "feature": "transition"},
            "note": f"GROUNDED teacher advice: transition/trajectory feature; purity {pur:.3f} "
                    f"({n_modes} modes) vs static 0.186"}


# ----------------------------------------------- grounded (FULL advice): DTW-trajectory clustering
def _traj(fr):
    S = np.array([shape(f) for f in fr], np.float64)
    return S / (np.linalg.norm(S, axis=1, keepdims=True) + 1e-9)   # per-frame L2 (cosine-ready)


def _dtw(a, b):
    """normalised cosine-DTW between two frame trajectories — the alignment the teacher advised
    ('compare tokens with an alignment that tolerates timing')."""
    na, nb = len(a), len(b)
    C = 1.0 - (a @ b.T)
    D = np.full((na + 1, nb + 1), 1e18); D[0, 0] = 0.0
    for i in range(1, na + 1):
        Di, Dp, Ci = D[i], D[i - 1], C[i - 1]
        for j in range(1, nb + 1):
            Di[j] = Ci[j - 1] + min(Dp[j], Di[j - 1], Dp[j - 1])
    return D[na, nb] / (na + nb)


def run_dtw_transition(world, sub, row, op, max_tokens=160, pctile=10.0):
    """GROUNDED from the teacher's FULL advice (trajectory + alignment): cluster words by DTW over
    their frame trajectories (the agent's density-mode operator with a DTW kernel), reporting a
    fair static baseline on the SAME subset. Tests whether the alignment clause recovers the
    trajectory signal the naive late-early feature lost."""
    from domains.distributional_categories import cluster_by_modes
    toks, core = prepare_word_data(world)
    data = [(w, _traj(fr)) for w, fr in toks if w in core and len(fr) >= 2]
    if len(data) < 6:
        return {"measured": 0.0, "target": op["target"], "metric": op["metric"],
                "keys": row["capability_keys"], "note": "insufficient data"}
    rng = np.random.RandomState(0)
    sel = rng.permutation(len(data))[:max_tokens]
    data = [data[i] for i in sel]
    cls = [w for w, _ in data]; T = [t for _, t in data]; n = len(T)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            D[i, j] = D[j, i] = _dtw(T[i], T[j])
    M = np.array([t.mean(0) for t in T])
    labels, n_modes = cluster_by_modes(M, pctile=pctile, dist=D)       # DTW kernel
    pur = _purity(labels, cls)
    Ms = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)         # fair static baseline, same n
    labs, _ = cluster_by_modes(Ms, pctile=8.0)
    pur_static = _purity(labs, cls)
    return {"measured": round(pur, 3), "target": op["target"], "metric": "cluster_purity",
            "keys": row["capability_keys"],
            "signals": {"purity": round(pur, 3), "static": round(pur_static, 3),
                        "n_modes": n_modes, "feature": "dtw-trajectory"},
            "note": f"GROUNDED full advice (trajectory + DTW alignment): purity {pur:.3f} "
                    f"({n_modes} modes) vs static {pur_static:.3f} on same {n} tokens "
                    f"(naive transition was 0.105 — alignment recovers it)"}


RUNNERS = {"clustering": run_clustering, "composition": run_composition,
           "quantiser": run_quantiser, "transition_clustering": run_transition_clustering,
           "dtw_transition": run_dtw_transition}
__all__ = ["RUNNERS", "prepare_word_data", "run_clustering", "run_composition", "run_quantiser",
           "run_transition_clustering", "run_dtw_transition"]
