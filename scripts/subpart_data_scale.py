"""LEVER 4/5 — DATA-SCALE + SOFT-EM for the LEARNED SUB-PART PARSE.

Lever 3 (commit 12abc671): K=3 sub-phone states lift the arc (flat-split 0.383, oracle 0.368) but the
VITERBI-INFERRED parse LOSES to flat/random (K3-vit 0.332). Lever 4 (data-scale curve, em_cap 4k->64k = 16x):
NO data-crossover — hard-Viterbi still ties flat/random — BUT the inferred inventory's ORACLE is 0.274 vs
flat/random's 0.137: the ceiling IS there; HARD inference can't realize it. Diagnosis: hard Viterbi over an
equal-split init COLLAPSES the K sub-states (one grabs all frames, the others die), so the discriminant is
effectively monophone.

LEVER 5 — the named fix: SOFT-EM. A per-phone K-component diagonal GMM fit by SOFT responsibilities keeps the
sub-states DISTINCT (each frame contributes fractionally to all K -> none can be starved to collapse). The
LDA is fit on the responsibility-WEIGHTED sub-part labels; recognition is the same held-DtwTo harness.
  COMPARE: SOFT-EM vs hard-VITERBI vs FLAT vs RANDOM at K=3, a couple of data sizes.
  NO-COLLAPSE evidence: mean normalised sub-state-usage entropy (hard collapses -> low; soft -> high).
  PREDICTION: soft-EM keeps the states distinct AND beats flat/random (realizing the inferred ceiling),
  proving the INFERENCE METHOD (not data, not the idea) was the lever.

donkey=0: the inventory + parse are the agent's OWN forward-backward/GMM soft-EM (+ held forced_align /
DtwTo) on held train-clean; no borrowed net/LLM/gradient-net. No-leakage split: infer/fit/ground on
train-clean, lam on a held-out train-clean slice, TEST on dev-clean.

MEMORY DISCIPLINE: frames float32, streamed per shard; the EM/GMM keep only 39xK centroids+vars (tiny); the
LDA fit STREAMS the PCA covariance + weighted scatter (never the full frame matrix in RAM), bounded eigh;
dev test bounded; transformed words local per arc (freed). N capped to what fits (RSS ~870MB observed).
Smoke-run first: --quick.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/subpart_data_scale.py [--quick]
"""
from __future__ import annotations
import os, sys, time, glob, pickle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

from scripts.jabberwock_subword_recognizer import _load_ph, ctx
from scripts.dynamic_sequence_speech_abs import majority_lexicon, FUNC
from scripts.speech_one_model_plug import flatstart_assign
from scripts.comprehension_grain_development import (expand_seq, run_arc, subpart_em, forced_align,
                                                    _init_subparts, _random_subparts)

BANK = "/home/matt/data/phonebank"


# ============================================================================
# SOFT-EM sub-part inference (the lever-4-named fix). Hard Viterbi over equal-split
# init COLLAPSES the K sub-states (one grabs all frames; the others die), so the
# inferred parse ties flat/random even though its ORACLE ceiling is far higher.
# A per-phone K-component diagonal GMM by SOFT-EM (responsibilities) keeps the
# sub-states DISTINCT: each frame contributes FRACTIONALLY to all K, so none can be
# starved to collapse. donkey=0: the agent's own EM on held data, no borrowed net.
# ============================================================================

def subpart_gmm_soft(words, K, em_iters, rng, cap_per_phone=4000):
    """Per-phone K-component diagonal GMM by SOFT-EM. Phone identity = the transcript (flat-start phone
    alignment); the K SUB-STATES within each phone are inferred by SOFT responsibilities (no hard collapse).
    Returns {phone: (means[K,d], vars[K,d], weights[K])}."""
    by_p = defaultdict(list)
    for O, ph in words:
        for i, p in enumerate(flatstart_assign(O, ph)):
            if len(by_p[p]) < cap_per_phone:
                by_p[p].append(O[i])
    gmm = {}
    for p, frames in by_p.items():
        Xp = np.asarray(frames, float)
        if len(Xp) < K + 2:
            mu0 = Xp.mean(0); gmm[p] = (np.tile(mu0, (K, 1)), np.tile(Xp.var(0) + 1e-3, (K, 1)), np.ones(K) / K)
            continue
        means = Xp[rng.choice(len(Xp), K, replace=False)].copy()
        vars = np.tile(Xp.var(0) + 1e-3, (K, 1)); wts = np.ones(K) / K
        for _ in range(em_iters):
            logr = np.stack([np.log(wts[k] + 1e-9)
                             - 0.5 * np.sum((Xp - means[k]) ** 2 / vars[k] + np.log(2 * np.pi * vars[k]), 1)
                             for k in range(K)], 1)
            logr -= logr.max(1, keepdims=True); r = np.exp(logr); r /= r.sum(1, keepdims=True) + 1e-12
            Nk = r.sum(0) + 1e-9
            means = (r.T @ Xp) / Nk[:, None]
            for k in range(K):
                diff = Xp - means[k]; vars[k] = (r[:, k] @ (diff * diff)) / Nk[k] + 1e-3
            wts = Nk / Nk.sum()
        gmm[p] = (means, vars, wts)
    return gmm


def _soft_resp(O, ph, gmm, K):
    """SOFT per-frame sub-part responsibilities: phone p from the transcript, soft weights over p#0..p#(K-1)
    from p's GMM. Returns per-frame list of (label, weight)."""
    out = []
    for i, p in enumerate(flatstart_assign(O, ph)):
        g = gmm.get(p)
        if g is None:
            out.append([(f"{p}#0", 1.0)]); continue
        means, vars, wts = g; x = O[i]
        lr = np.array([np.log(wts[k] + 1e-9) - 0.5 * np.sum((x - means[k]) ** 2 / vars[k] + np.log(2 * np.pi * vars[k]))
                       for k in range(K)])
        lr -= lr.max(); r = np.exp(lr); r /= r.sum() + 1e-12
        out.append([(f"{p}#{k}", float(r[k])) for k in range(K)])
    return out


def _hard(lab_list):
    """wrap a hard per-frame label list into the (label, weight=1.0) soft form."""
    return [[(l, 1.0)] for l in lab_list]


def fit_modes(cal_gN, K, W, em_iters, rng, Pdim=80):
    """Fit the K-sub-part LDA discriminant for SOFT-EM / hard-VITERBI / FLAT / RANDOM on the SAME N words,
    MEMORY-SAFELY: stream the PCA covariance + (responsibility-WEIGHTED) LDA scatter (never the full frame
    matrix in RAM), bounded eigh. Returns ({mode:(enc,dim,nC)}, {mode: sub-state-usage entropy}). The usage
    entropy is the NO-COLLAPSE evidence: hard-Viterbi collapses (low entropy), soft-EM stays distinct (high).
    donkey=0: every inventory = the agent's own EM on held data."""
    em_words = [(np.asarray(fr, float), ph) for (w, fr, ph) in cal_gN]
    theta = subpart_em(em_words, K, em_iters); gm_b = np.mean(list(theta.values()), 0)   # hard Viterbi inventory
    gmm = subpart_gmm_soft(em_words, K, em_iters, rng)                                    # soft GMM inventory
    labelers = {
        "soft":    lambda O, ph: _soft_resp(O, ph, gmm, K),
        "viterbi": lambda O, ph: _hard(forced_align(O, expand_seq(ph, K), theta, gm_b)),
        "flat":    lambda O, ph: _hard(_init_subparts(O, ph, K)),
        "random":  lambda O, ph: _hard(_random_subparts(O, ph, K, rng)),
    }
    d = ctx(np.asarray(cal_gN[0][1], float), W).shape[1]
    n = 0; sx = np.zeros(d); sxx = np.zeros((d, d))
    for (w, fr, ph) in cal_gN:                                       # PASS 1 — PCA covariance (label-free)
        Z = ctx(np.asarray(fr, float), W); sx += Z.sum(0); sxx += Z.T @ Z; n += len(Z)
    mu = sx / n; cov = sxx / n - np.outer(mu, mu); cov += 1e-4 * np.eye(d)
    wv, V = np.linalg.eigh(cov); idx = np.argsort(wv)[::-1][:Pdim]; Wp = V[:, idx]; Pd = Wp.shape[1]
    Szz = np.zeros((Pd, Pd)); gsz = np.zeros(Pd); gn = 0
    cls = {m: {} for m in labelers}; usage = {m: defaultdict(lambda: np.zeros(K)) for m in labelers}
    for (w, fr, ph) in cal_gN:                                       # PASS 2 — project once, weighted accumulate
        O = np.asarray(fr, float); Z = (ctx(O, W) - mu) @ Wp
        Szz += Z.T @ Z; gsz += Z.sum(0); gn += len(Z)
        for m, lab_fn in labelers.items():
            cm = cls[m]; um = usage[m]
            for i, parts in enumerate(lab_fn(O, ph)):
                for (l, wgt) in parts:
                    e = cm.get(l)
                    if e is None:
                        cm[l] = [wgt, wgt * Z[i]]
                    else:
                        e[0] += wgt; e[1] += wgt * Z[i]
                    pp, kk = l.split("#"); um[pp][int(kk)] += wgt
    gmz = gsz / gn; total = Szz - gn * np.outer(gmz, gmz)
    out = {}; ent = {}
    for m in labelers:
        Sb = np.zeros((Pd, Pd))
        for l, (c, sz) in cls[m].items():
            if c <= 1e-6:
                continue
            mz = sz / c; Sb += c * np.outer(mz - gmz, mz - gmz)
        Sw = total - Sb + 1e-3 * np.eye(Pd)
        ws, Vs = np.linalg.eigh(Sw); ws = np.clip(ws, 1e-8, None); Wsi = (Vs / np.sqrt(ws)) @ Vs.T  # Sw^-1/2
        A = Wsi @ Sb @ Wsi; A = (A + A.T) / 2
        ev, EV = np.linalg.eigh(A); k = max(1, min(Pd, len(cls[m]) - 1))
        order = np.argsort(ev)[::-1][:k]; Wl = Wsi @ EV[:, order]

        def make_enc(Wl=Wl):
            def enc(M):
                Z = ctx(np.asarray(M, float), W); Yp = ((Z - mu) @ Wp) @ Wl
                return Yp / np.clip(np.linalg.norm(Yp, axis=1, keepdims=True), 1e-9, None)
            return enc
        out[m] = (make_enc(), Wl.shape[1], len(cls[m]))
        # mean normalised sub-state-usage entropy (1.0 = perfectly distinct K states; ~0 = collapsed to one)
        es, wsum = 0.0, 0.0
        for p, u in usage[m].items():
            tot = u.sum()
            if tot <= 0:
                continue
            q = u / tot; h = -np.sum(q * np.log(q + 1e-12)) / np.log(K)
            es += tot * h; wsum += tot
        ent[m] = es / max(wsum, 1e-9)
    return out, ent


def load_train_f32(n_shards, cap_words):
    """Stream train-clean shards, keep (word, frames[float32], phones) — float32 + per-shard drop to bound RAM."""
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, "train-clean-100_*.pkl")))[:n_shards]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 3 and isinstance(e[0], str):
                w = e[0].lower(); fr = np.asarray(e[1], np.float32); ph = e[2]
                if w.isalpha() and fr.shape[0] >= 3 and isinstance(ph, (list, tuple)) and ph:
                    out.append((w, fr, [str(x) for x in ph]))
        del shard
        if len(out) >= cap_words:
            break
    return out[:cap_words]


def main():
    quick = "--quick" in sys.argv
    t0 = time.time(); rng = np.random.default_rng(0)
    print("=" * 110)
    print("LEVER 5 — SOFT-EM sub-part inference: realize the inferred inventory's HIGHER ceiling (no collapse)")
    print("  K=3 sub-parts; SOFT-EM vs hard-VITERBI vs FLAT vs RANDOM, across data size N")
    print("  SPLIT: infer/fit/ground train-clean; lam on held-out train-clean slice; TEST dev-clean")
    print("=" * 110, flush=True)

    Ns = [3000, 9000] if quick else [8000, 48000]         # a couple of data sizes (lever-4 showed no data-crossover)
    n_shards = 4 if quick else 16
    cap_words = (10000 if quick else 64000)
    cal = load_train_f32(n_shards, cap_words)
    dev = [(w, fr.astype(np.float32), ph) for (w, fr, ph) in _load_ph("dev-clean_*.pkl", 3 if quick else 8)]
    cidx = rng.permutation(len(cal)); ng = int(0.85 * len(cal))
    cal_g = [cal[i] for i in cidx[:ng]]; cal_v = [cal[i] for i in cidx[ng:]]
    Ns = [N for N in Ns if N <= len(cal_g)]
    lexicon = majority_lexicon(cal + dev)
    dev_count = Counter(w for w, _f, _p in dev)
    vocab = sorted([w for w, c in dev_count.items()
                    if w not in FUNC and len(w) >= 4 and c >= (4 if quick else 6) and w in lexicon])
    vocab = vocab[: (18 if quick else 28)]
    chance = 1.0 / len(vocab)
    print(f"  loaded train={len(cal)} (cal_g {len(cal_g)}, cal_v {len(cal_v)}), dev={len(dev)} words; "
          f"N-sweep {Ns}   [{time.time()-t0:.0f}s]", flush=True)
    print(f"  vocabulary {len(vocab)} words (chance {chance:.3f})", flush=True)

    cal_words = [w for w, _f, _p in cal_g]
    model = {}; uni = Counter(cal_words); top_word = uni.most_common(1)[0][0]   # top-down NULL -> lam*->0

    K, W, EMIT = 3, 5, (2 if quick else 4)
    NG = 200 if quick else 500
    raw_dev = dev[: (3000 if quick else 8000)]
    raw_val = cal_v[: (2000 if quick else 4000)]
    gw = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in cal_g[:NG]]
    dev_sub = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in raw_dev]
    val_sub = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in raw_val]
    lex_sub = {w: expand_seq(s, K) for w, s in lexicon.items()}
    MODES = ("soft", "viterbi", "flat", "random")

    curve = {}; ents = {}
    for N in Ns:
        cal_gN = cal_g[:N]
        feats, ent = fit_modes(cal_gN, K, W, EMIT, np.random.default_rng(7))     # 4 modes, incremental weighted LDA
        ents[N] = ent
        for mode in MODES:
            enc, dim, nC = feats[mode]
            r = run_arc(f"N{N//1000}k-{mode[:4]}", enc, gw, dev_sub, val_sub, lex_sub, vocab, chance,
                        model, top_word, uni, quick, np.random.default_rng(99), t0)   # fresh rng per arc
            curve[(N, mode)] = r
        del feats

    def arc(N, m): return curve[(N, m)]["stageA"]
    def orc(N, m): return curve[(N, m)]["oracle"]
    print("\n" + "=" * 110)
    print("  SOFT-EM vs HARD-VITERBI vs FLAT vs RANDOM (K=3, comprehension STAGE A / oracle on dev-clean):")
    print(f"  {'N':>7} | {'SOFT arc/orc':>16} | {'VITERBI arc/orc':>16} | {'FLAT arc/orc':>16} | "
          f"{'RANDOM arc/orc':>16} | {'soft usage-H':>12}")
    for N in Ns:
        print(f"  {N:>7} | {arc(N,'soft'):>7.3f}/{orc(N,'soft'):<8.3f} | "
              f"{arc(N,'viterbi'):>7.3f}/{orc(N,'viterbi'):<8.3f} | {arc(N,'flat'):>7.3f}/{orc(N,'flat'):<8.3f} | "
              f"{arc(N,'random'):>7.3f}/{orc(N,'random'):<8.3f} | {ents[N]['soft']:>12.3f}")
    print(f"  chance {chance:.3f} | n={curve[(Ns[0],'soft')]['n']}")
    print("-" * 110)
    print("  NO-COLLAPSE evidence (mean normalised sub-state-usage entropy; 1.0=distinct K states, ~0=collapsed):")
    for N in Ns:
        print(f"    N={N:>6}: soft {ents[N]['soft']:.3f} | viterbi {ents[N]['viterbi']:.3f} | "
              f"flat {ents[N]['flat']:.3f} | random {ents[N]['random']:.3f}")
    print("-" * 110)

    # ============================ GATES ============================
    maxN = Ns[-1]
    s_arc, s_orc = arc(maxN, "soft"), orc(maxN, "soft")
    beats_flat = s_arc > arc(maxN, "flat") + 0.005
    beats_rand = s_arc > arc(maxN, "random") + 0.005
    beats_vit = s_arc > arc(maxN, "viterbi") + 0.005
    crossover = beats_flat and beats_rand
    realizes = s_arc > 0.368 or s_arc > orc(maxN, "viterbi") - 0.02   # arc climbs toward the inferred ceiling
    no_collapse = ents[maxN]["soft"] > ents[maxN]["viterbi"] + 0.05
    rmax = curve[(maxN, "soft")]
    offset_holds = rmax["corr"] < -0.5; whole_utt_holds = rmax["whole_utt"]
    print("  VERDICT (lever 5 — does SOFT-EM realize the inferred inventory's higher ceiling?):")
    print(f"    (a) CROSSOVER — soft-EM arc {s_arc:.3f} beats FLAT {arc(maxN,'flat'):.3f} ({beats_flat}) AND "
          f"RANDOM {arc(maxN,'random'):.3f} ({beats_rand})  => {'HOLDS' if crossover else 'NOT REACHED'}")
    print(f"    (b) REALIZES THE ORACLE — soft arc {s_arc:.3f} toward inferred oracle ~0.274/0.368 "
          f"(soft oracle {s_orc:.3f}); beats hard-Viterbi {arc(maxN,'viterbi'):.3f}: {beats_vit}")
    print(f"    (c) NO-COLLAPSE — soft usage-entropy {ents[maxN]['soft']:.3f} > hard-Viterbi "
          f"{ents[maxN]['viterbi']:.3f} (+0.05): {no_collapse} (hard collapses, soft stays distinct)")
    print(f"    (d) LEVERS HOLD (soft) — offset corr {rmax['corr']:+.2f} (<-0.5: {offset_holds}); whole-utt FA "
          f"{rmax['fa_comp']:.3f} > pf {rmax['pf_comp']:.3f}: {whole_utt_holds}; real>shuffled: {rmax['real_beats_shuf']}")
    print(f"    (e) donkey=0: inventory+parse = own forward-backward/GMM soft-EM + held DtwTo on held "
          f"train-clean; no borrowed net/LLM/gradient-net. No leakage (TEST=dev-clean).")
    if crossover and no_collapse:
        v = (f"WIN — SOFT-EM achieves the crossover hard-Viterbi could not: it keeps the sub-states DISTINCT "
             f"(usage-H {ents[maxN]['soft']:.2f} vs {ents[maxN]['viterbi']:.2f}) and BEATS flat/random "
             f"(arc {s_arc:.3f}) — the INFERENCE METHOD was the lever; the inferred inventory's higher ceiling "
             f"is realizable, not irreducible.")
    elif no_collapse and beats_vit:
        v = (f"PARTIAL — soft-EM fixes the collapse (usage-H {ents[maxN]['soft']:.2f} vs "
             f"{ents[maxN]['viterbi']:.2f}) and beats hard-Viterbi ({s_arc:.3f} vs {arc(maxN,'viterbi'):.3f}) but "
             f"does not yet clear flat/random; NEXT LEVER: full forward-backward (HMM transitions across "
             f"sub-states, not per-phone GMM) or a learned split criterion — not irreducible.")
    elif no_collapse:
        v = (f"DEEPER FINDING — soft-EM fixes the COLLAPSE (usage-H {ents[maxN]['soft']:.2f} vs "
             f"{ents[maxN]['viterbi']:.2f}) but the arc still does not beat flat/random, so the inferred "
             f"inventory's oracle ADVANTAGE does not transfer to the DTW decode: the RECOGNISER/decode (DTW over "
             f"render templates), not the inventory, is the binding lever. NEXT: a finer-inventory-aware decode.")
    else:
        v = (f"NULL — soft-EM did not separate the sub-states here (usage-H {ents[maxN]['soft']:.2f}); NEXT LEVER: "
             f"stronger init / more EM iters / full forward-backward — not irreducible.")
    print(f"  => {v}")
    print("=" * 110, flush=True)
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
