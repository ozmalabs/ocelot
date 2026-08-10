"""DYNAMIC SEQUENCE-LEVEL GENERATOR-INVERSION for speech recognition — the reframe made falsifiable.

THE REFRAME (the spec): per-frame STATIC discriminative recognition is DOUBLY wrong-shape — (a) the
forward model must be DYNAMIC (phone identity lives in coarticulation / the smooth trajectory, not a
static band-warp), and (b) recognition must happen at the SEQUENCE level (identity is carried
REDUNDANTLY across frames), not per-frame. KEY UNIFICATION: speech articulation is the SAME minimum-jerk
physical-effector model as handwriting ("model the writer's physical limits") — coarticulation = the
smooth physical trajectory of the articulator through gestural targets (bounded velocity/jerk, undershoot
toward neighbours when a phone is short). Build that generator and INVERT it at the sequence level.

WHAT THIS BUILDS (donkey=0, earn-not-borrow):
  GESTURAL TARGETS  — per-phone target region in the held cochlear band space, calibrated from a FEW
                      exemplar words (proportional flat-start alignment -> per-phone centroid + duration).
  DYNAMIC GENERATOR — render a phone SEQUENCE as a SMOOTH minimum-jerk trajectory through the targets,
                      with COARTICULATORY UNDERSHOOT (short phones pulled toward neighbours; the low-pass
                      smoothing IS the bounded-jerk physics). Same writer-physics motor model as
                      handwriting (domains/earned_augmentation._smooth_warp).
  SEQUENCE INVERSION— recognize an observed word by argmin over the vocabulary of DTW(observed frames,
                      rendered trajectory). Decision = the HELD DtwTo Term + argmin (graph-native).

EVAL is at the SEQUENCE granularity: WORD accuracy over a held vocabulary + PHONE-SEQUENCE edit accuracy
(NOT per-frame accuracy). The data-practicality curve sweeps the CALIBRATION SIZE N.

GATES (controls):
  MAIN          — word-accuracy vs N for DYNAMIC-SEQUENCE-AbS vs a DISCRIMINATIVE phone classifier
                  (PCA->LDA centroids -> decode -> word by edit, the existing sub-word recognizer).
                  Prediction: structure is DATA-EFFICIENT (good at small N) where discriminative is hungry.
  DYNAMICS      — dynamic (min-jerk + coarticulation) render beats a STATIC (step, per-frame-independent
                  canonical target) render.
  SEQUENCE      — the DTW sequence decode beats per-frame argmax of the SAME targets.
  DISCRIMINATIVE— a DEGENERATE generator (scrambled phone->target map) does NOT get the data-efficiency.

Lexicon (word -> phone-seq) and targets are EARNED from the held phonebank (no CMU, no borrowed net, no
LLM). The min-jerk render + VTL-free band match are numpy ADAPTER measurement (like the held AbS scripts);
the DECISION is the held DtwTo + argmin. donkey=0.

Run (smoke):  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/dynamic_sequence_speech_abs.py [--quick]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

import substrate_rs as _srs
from scripts.jabberwock_subword_recognizer import _load_ph, ctx, norm_edit
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda

# ----- held DtwTo decision path (graph-native; the ONLY decision machinery) -------------------
_NS = _srs._NativeSubstrate()
_L = lambda v: {"type": "Lit", "value": v}
def dtw(a, b):
    """Held DtwTo Term: time-align two frame sequences, return alignment distance (the decision)."""
    return float(_NS.evaluate({"type": "DtwTo", "a": _L(a), "b": _L(b)}, {}))

FUNC = {"the","and","of","to","his","he","in","was","that","she","had","her","it","as","at","for",
        "with","not","but","you","him","they","this","which","is","be","on","by","from","or","an","a",
        "all","we","are","so","no","up","out","one","there","what","when","were","their","them","i"}


# ----------------------------------------------------------------- calibration (EARN) --------
def majority_lexicon(words):
    """word -> its MOST COMMON banked phone sequence (earned lexicon; no CMU/borrowed dict)."""
    seqs = defaultdict(Counter)
    for w, _fr, ph in words:
        seqs[w][tuple(ph)] += 1
    return {w: list(c.most_common(1)[0][0]) for w, c in seqs.items()}


def collect_targets(words):
    """GESTURAL TARGETS from a few exemplars: proportional flat-start align each word's frames to its
    phones, accumulate the per-phone frame centroid (the target region) + mean duration (frames/phone).
    Small N -> few exemplars per phone. This is the calibrated generative target set."""
    acc = defaultdict(list); dur = defaultdict(list)
    for w, fr, ph in words:
        fr = np.asarray(fr, float); n = len(fr); P = len(ph)
        assign = [ph[int(i * P / n)] for i in range(n)]
        for i, p in enumerate(assign):
            acc[p].append(fr[i])
        for p, ct in Counter(assign).items():
            dur[p].append(ct)
    targets = {p: np.mean(v, 0) for p, v in acc.items() if v}
    durs = {p: float(np.mean(d)) for p, d in dur.items() if d}
    return targets, durs


# ----------------------------------------------------------------- the GENERATOR -------------
def _smooth(traj, w):
    """min-jerk-like low-pass (bounded velocity/jerk) — the handwriting writer-physics smoothing,
    applied per band. The smoothing IS the articulatory inertia; it also blurs short phones toward
    neighbours = coarticulatory undershoot emerging from the physics."""
    if w < 3 or len(traj) < 3:
        return traj
    ker = np.ones(w) / w
    return np.stack([np.convolve(traj[:, b], ker, "same") for b in range(traj.shape[1])], 1)


def render_dynamic(seq, targets, durs, gmean, dmean, undershoot=0.35):
    """DYNAMIC coarticulation render: a SMOOTH minimum-jerk trajectory through the gestural targets
    with COARTICULATORY UNDERSHOOT (short phones pulled toward neighbours), bounded jerk via low-pass.
    The generative model of the observed frame trajectory for a phone SEQUENCE."""
    K = len(seq)
    canon = [targets.get(p, gmean) for p in seq]
    d = [max(1.0, durs.get(p, dmean)) for p in seq]
    # coarticulatory undershoot: shorter phone -> pulled MORE toward its neighbours' targets
    eff = []
    for k in range(K):
        if K == 1:
            eff.append(canon[k]); continue
        left = canon[k - 1] if k > 0 else canon[k]
        right = canon[k + 1] if k < K - 1 else canon[k]
        u = undershoot / (1.0 + d[k] / 3.0)
        eff.append((1.0 - u) * canon[k] + 0.5 * u * left + 0.5 * u * right)
    starts = np.cumsum([0.0] + d); M = max(2, int(round(starts[-1])))
    centers = np.array([(starts[k] + starts[k + 1]) / 2.0 for k in range(K)])
    E = np.stack(eff); t = np.arange(M)
    traj = np.stack([np.interp(t, centers, E[:, b]) for b in range(E.shape[1])], 1)
    return _smooth(traj, max(3, int(0.6 * dmean)))


def render_static(seq, targets, durs, gmean, dmean):
    """STATIC (no-dynamics) render: a STEP function of the canonical per-phone targets — per-frame
    INDEPENDENT target, no smoothing, no coarticulation. The ablation that ignores the trajectory."""
    blocks = []
    for p in seq:
        d = max(1, int(round(durs.get(p, dmean))))
        blocks.append(np.tile(targets.get(p, gmean), (d, 1)))
    return np.vstack(blocks) if blocks else np.zeros((2, len(gmean)))


# ----------------------------------------------------------------- recognisers ---------------
def classify_render(O, rendered):
    """SEQUENCE INVERSION: argmin over the vocabulary of DTW(observed, rendered-trajectory). The
    held DtwTo + argmin decision (graph-native)."""
    Ol = O.tolist()
    return int(np.argmin([dtw(Ol, R) for R in rendered]))


def decode_perframe(O, phlist, T):
    """per-frame argmax of the SAME targets: nearest-target phone per frame, collapse repeats ->
    phone string. The granularity ablation (frame, not sequence)."""
    idx = ((O[:, None, :] - T[None]) ** 2).sum(2).argmin(1)
    seq, prev = [], -1
    for k in idx:
        if k != prev:
            seq.append(phlist[k]); prev = k
    return seq


def word_by_edit(decoded, vocab_seqs):
    """map a decoded phone string to a vocabulary word by min normalised edit distance."""
    return int(np.argmin([norm_edit(decoded, s) for s in vocab_seqs]))


# ----------------------------------------------------------------- evaluation ----------------
def eval_set(test, recog):
    """recog: observed-frames -> predicted vocab index. Returns (word_acc, phone_edit_acc)."""
    correct = 0; edits = []
    for O, wi, true_seq, vocab_seqs in test:
        pi = recog(O)
        correct += (pi == wi)
        edits.append(1.0 - norm_edit(vocab_seqs[pi], true_seq))
    return correct / len(test), float(np.mean(edits))


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 96)
    print("DYNAMIC SEQUENCE-LEVEL GENERATOR-INVERSION — min-jerk coarticulation + DTW sequence decode")
    print("=" * 96, flush=True)

    cal_pool = _load_ph("train-clean-100_*.pkl", 6 if quick else 14)
    dev = _load_ph("dev-clean_*.pkl", 4 if quick else 10)
    print(f"  calibration pool: {len(cal_pool)} words   dev: {len(dev)} words   [{time.time()-t0:.0f}s]",
          flush=True)

    lex = majority_lexicon(cal_pool + dev)

    # vocabulary: content words (>=4 chars, not function) with enough DEV exemplars + a phone-seq -----
    dev_by_word = defaultdict(list)
    for w, fr, ph in dev:
        if w not in FUNC and len(w) >= 4 and w in lex and len(lex[w]) >= 3:
            dev_by_word[w].append(np.asarray(fr, float))
    K_EX = 8 if quick else 12
    vocab = sorted([w for w, exs in dev_by_word.items() if len(exs) >= K_EX])
    vocab = vocab[:24 if quick else 36]
    vocab_seqs = [lex[w] for w in vocab]
    vset = set(vocab)
    test = []
    for wi, w in enumerate(vocab):
        for O in dev_by_word[w][:K_EX]:
            test.append((O, wi, lex[w], vocab_seqs))
    print(f"  vocabulary: {len(vocab)} content words   test exemplars: {len(test)}   "
          f"(e.g. {vocab[:8]})", flush=True)
    chance = 1.0 / len(vocab)

    Ns = [25, 50, 100, 200] if quick else [25, 50, 100, 200, 400, 800]
    rng = np.random.default_rng(0)
    cal_idx = rng.permutation(len(cal_pool))

    def build_at(N):
        words = [cal_pool[i] for i in cal_idx[:N]]
        targets, durs = collect_targets(words)
        gmean = np.mean(list(targets.values()), 0); dmean = float(np.mean(list(durs.values())))
        return words, targets, durs, gmean, dmean

    # ---- EARNED phone-discriminant encoder (PCA->LDA on calibration; shared by two recognisers) -
    def fit_encoder(words):
        X, Y = [], []
        for w, fr, ph in words:
            cx = ctx(fr); n = len(cx); P = len(ph)
            for i in range(n):
                X.append(cx[i]); Y.append(ph[int(i * P / n)])
        X = np.asarray(X); phones_set = sorted(set(Y)); pj = {p: i for i, p in enumerate(phones_set)}
        nP = len(phones_set)
        if nP < 2 or len(X) < nP + 5:
            return None
        Pdim = min(80, X.shape[0] - nP - 1)
        mu, Wp = _fit_pca(X, Pdim)
        Wl = _fit_lda((X - mu) @ Wp, Y, k=min(Pdim, nP - 1))
        def enc(Z):
            Yp = ((np.asarray(Z) - mu) @ Wp) @ Wl
            return Yp / np.clip(np.linalg.norm(Yp, axis=1, keepdims=True), 1e-9, None)
        return enc, X, Y, phones_set, pj, nP

    def discriminative(fit):
        """Discriminative baseline: per-phone LDA centroid -> per-frame argmax -> collapse -> word by
        edit (the existing sub-word recogniser)."""
        enc, X, Y, phones_set, pj, nP = fit
        E = enc(X); cent, cph = [], []
        for p in phones_set:
            m = E[[i for i in range(len(Y)) if Y[i] == p]]
            cent.append(m.mean(0)); cph.append(pj[p])
        cent = np.asarray(cent); cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)
        cph = np.asarray(cph)
        def decode(M):
            idx = cph[(enc(ctx(M)) @ cent.T).argmax(1)]
            seq, prev = [], -1
            for k in idx:
                if k != prev:
                    seq.append(phones_set[k]); prev = k
            return seq
        return lambda O: word_by_edit(decode(O), vocab_seqs)

    def abs_lda(fit, durs, dmean):
        """SAME dynamic sequence generator-inversion, but in the EARNED phone-discriminant LDA space
        (targets = per-phone LDA centroid; render min-jerk trajectory; observed = enc(ctx(O))); the
        feature-richness test — does giving the generator an adequate space rescue the AbS?"""
        enc, X, Y, phones_set, pj, nP = fit
        E = enc(X)
        tgt = {p: E[[i for i in range(len(Y)) if Y[i] == p]].mean(0) for p in phones_set}
        gm = np.mean(list(tgt.values()), 0)
        rend = [render_dynamic(s, tgt, durs, gm, dmean).tolist() for s in vocab_seqs]
        return lambda O: classify_render(enc(ctx(O)), rend)

    print("\n  MAIN — DATA-PRACTICALITY (word accuracy, the SEQUENCE metric) vs calibration N:")
    print(f"  {'N':>5} | {'AbS-band w/p':>14} | {'AbS-LDA w/p':>13} | {'DISCRIM w/p':>13}  "
          f"(chance {chance:.3f})")
    rows = []
    for N in Ns:
        ts = time.time()
        words, targets, durs, gmean, dmean = build_at(N)
        rendered = [render_dynamic(s, targets, durs, gmean, dmean).tolist() for s in vocab_seqs]
        abs_w, abs_p = eval_set(test, lambda O: classify_render(O, rendered))
        fit = fit_encoder(words)
        if fit is not None:
            absl_w, absl_p = eval_set(test, abs_lda(fit, durs, dmean))
            dis_w, dis_p = eval_set(test, discriminative(fit))
        else:
            absl_w = absl_p = dis_w = dis_p = float("nan")
        rows.append((N, abs_w, abs_p, absl_w, absl_p, dis_w, dis_p))
        print(f"  {N:>5} | {abs_w:>6.3f}/{abs_p:>6.3f} | {absl_w:>6.3f}/{absl_p:>6.3f} | "
              f"{dis_w:>6.3f}/{dis_p:>6.3f}   [{time.time()-ts:.0f}s]", flush=True)

    # ---- DYNAMICS / SEQUENCE / DEGENERATE controls at a representative small N ----------------
    # Run in BOTH the raw cochlear-band space AND the earned phone-discriminant (LDA) space — the
    # LDA space is the regime where the generator actually works, so it is the meaningful control.
    Nc = 100
    words, targets, durs, gmean, dmean = build_at(Nc)
    fit = fit_encoder(words)

    def controls_in(tgt, gm, featfn, label):
        phl = sorted(tgt.keys()); T = np.stack([tgt[p] for p in phl])
        r_dyn = [render_dynamic(s, tgt, durs, gm, dmean).tolist() for s in vocab_seqs]
        r_sta = [render_static(s, tgt, durs, gm, dmean).tolist() for s in vocab_seqs]
        dyn_w, dyn_p = eval_set(test, lambda O: classify_render(featfn(O), r_dyn))
        sta_w, sta_p = eval_set(test, lambda O: classify_render(featfn(O), r_sta))
        pf_w, pf_p = eval_set(test, lambda O: word_by_edit(decode_perframe(featfn(O), phl, T), vocab_seqs))
        perm = rng.permutation(len(phl))
        scr = {phl[i]: T[perm[i]] for i in range(len(phl))}
        r_scr = [render_dynamic(s, scr, durs, gm, dmean).tolist() for s in vocab_seqs]
        scr_w, scr_p = eval_set(test, lambda O: classify_render(featfn(O), r_scr))
        print(f"\n  CONTROLS in {label} space (word acc / phone-edit acc):")
        print(f"   DYNAMICS  — dynamic(min-jerk+coartic) {dyn_w:.3f}/{dyn_p:.3f}  vs  static(step) "
              f"{sta_w:.3f}/{sta_p:.3f}   => dynamics help: {dyn_w > sta_w}")
        print(f"   SEQUENCE  — DTW sequence decode {dyn_w:.3f}/{dyn_p:.3f}  vs  per-frame argmax "
              f"{pf_w:.3f}/{pf_p:.3f}   => sequence helps: {dyn_w > pf_w}")
        print(f"   DEGENERATE— scrambled phone->target {scr_w:.3f}/{scr_p:.3f}  vs  real targets "
              f"{dyn_w:.3f}/{dyn_p:.3f}   => structure does the work: {dyn_w > scr_w + 0.03}")

    print("\n" + "=" * 96)
    print(f"  CONTROLS at N={Nc} (donkey=0; chance {chance:.3f}, vocab {len(vocab)}, test {len(test)}):")
    controls_in(targets, gmean, lambda O: O, "raw-band")
    if fit is not None:
        enc, X, Y, phones_set, pj, nP = fit
        E = enc(X)
        tgtL = {p: E[[i for i in range(len(Y)) if Y[i] == p]].mean(0) for p in phones_set}
        gmL = np.mean(list(tgtL.values()), 0)
        controls_in(tgtL, gmL, lambda O: enc(ctx(O)), "earned-LDA")
    print(f"  [{time.time()-t0:.0f}s]")

    # ---- VERDICT: small-N data-efficiency of structure vs discriminative ----------------------
    print("=" * 96)
    small = rows[0]
    structure_wins_small = (small[1] > small[5] + 0.02) if small[5] == small[5] else True
    lda_wins_small = (small[3] > small[5] + 0.02) if small[5] == small[5] else False
    print(f"  AbS-band curve (wacc): " + "  ".join(f"{r[0]}:{r[1]:.2f}" for r in rows))
    print(f"  AbS-LDA  curve (wacc): " + "  ".join(f"{r[0]}:{r[3]:.2f}" for r in rows))
    print(f"  DISCRIM  curve (wacc): " + "  ".join(f"{r[0]}:{r[5]:.2f}" for r in rows))
    print(f"  at smallest N={small[0]}: AbS-band {small[1]:.3f} / AbS-LDA {small[3]:.3f} vs "
          f"discrim {small[5]:.3f}  => raw-band structure wins small N: {structure_wins_small}; "
          f"LDA-space structure wins small N: {lda_wins_small}")
    print(f"  donkey=0: targets+lexicon EARNED from held phonebank; min-jerk render = numpy adapter; "
          f"DECISION = held DtwTo Term + argmin (graph-native). No LLM, no borrowed net.")
    print("=" * 96, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
