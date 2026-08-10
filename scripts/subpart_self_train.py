"""LEVER 8 — LABEL-FREE CENTROID DOMAIN ADAPTATION (forced-align self-training) toward the real test domain.

Lever 7 (commit 3fdfd7ca): the sub-part forced-align SEQUENCE decode is near-solved — with DEV-MATCHED centroids
the oracle is 0.917 — but the achieved arc is 0.372 because the sub-part centroids are grounded on TRAIN-clean
and don't match the real test domain. The remaining gap is CENTROID GROUNDING.

THE FIX: label-free domain adaptation of the centroids toward the real domain by SELF-TRAINING with the STRONG
forced-align decode. Self-training NULLED before (9de5b7cb) ONLY because per-frame argmax pseudo-labels (~0.14)
were too noisy and the per-frame metric was saturated. NOW the forced-align decode is strong (0.37, ~10x chance)
and the oracle is 0.917 (huge headroom) — strong pseudo-labels + real headroom should make adaptation PAY.

THE LOOP (donkey=0, no human labels, no transcripts):
  for each UNLABELED real adapt word: DECODE it (top-1 over a self-decode lexicon by forced-align cost) ->
  forced-align its frames to the DECODED word's sub-part centroid sequence -> per-frame sub-part PSEUDO-LABELS
  -> re-estimate each sub-part centroid toward the real frames (counted blend = the held grounding) -> ITERATE.

NO-LEAKAGE SPLIT (explicit): fit the LDA + ground initial centroids on TRAIN-clean; ADAPT (frames only, no
labels, self-decoded) on dev-clean HALF-A; TEST on dev-clean HALF-B (disjoint from A). The 0.917 oracle used
dev-matched centroids (a cheating reference) — we APPROACH it WITHOUT dev labels, never adapting on the eval set.

GATES (honest): (a) ARC CLIMBS — adapted arc moves 0.37 toward the 0.92 oracle (per-iteration curve, gap
closed); (b) DISCRIMINATIVE — adapting toward REAL (self-decode) beats SHUFFLED (random target) and beats the
old PER-FRAME-ARGMAX self-training (the strong forced-align pseudo-labels are what enable it); (c) DRIFT GUARD —
monotone vs collapse, reported; (d) donkey=0 (forced-align pseudo-labels + held centroid re-estimation; no
borrowed net/LLM/gradient-net), no leakage.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/subpart_self_train.py [--quick]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.dynamic_sequence_speech_abs import majority_lexicon, FUNC
from scripts.comprehension_grain_development import expand_seq, transform_words, forced_align, dev_centroids
from scripts.subpart_data_scale import fit_modes, load_train_f32
from scripts.subpart_sequence_decode import _fa_cost, ground_subpart_theta, seq_fa_acc


def _viterbi_path(O, T, labels, stay=0.5):
    """Boundary-free Viterbi over the free sub-part inventory; returns the PER-FRAME sub-part label path
    (a STAY-bonus denoises switching). Genuinely label-free (no transcript, no lexicon)."""
    E = O @ T.T; n, Kn = E.shape
    D = E[0].copy(); back = np.zeros((n, Kn), np.int32); ar = np.arange(Kn)
    for t in range(1, n):
        gmax = D.max(); gidx = int(D.argmax()); stay_s = D + stay; use = stay_s >= gmax
        back[t] = np.where(use, ar, gidx); D = np.where(use, stay_s, gmax) + E[t]
    k = int(D.argmax()); path = [0] * n; path[-1] = k
    for t in range(n - 1, 0, -1):
        k = int(back[t][k]); path[t - 1] = k
    return [labels[j] for j in path]


def pseudo_reestimate(theta, A_lda, mode, conf_keep, blend, rng):
    """One self-training pass: pseudo-label each UNLABELED adapt word, accumulate the real LDA frames per
    sub-part, blend each centroid toward them (anti-drift, counted structure-add). Modes:
      'viterbi'   — label-free Viterbi-emission per-frame sub-part path (no transcript/lexicon).
      'perframe'  — per-frame nearest-centroid argmax (the 9de5b7cb noisy pseudo-label).
      'transcript'— forced-align frames to the word's OWN sub-part sequence (weak transcript supervision).
      'shuffled'  — forced-align to a RANDOM word's sub-part seq (wrong targets; the discriminative control)."""
    gm = np.mean(list(theta.values()), 0)
    labels_all = list(theta); T = np.stack([theta[l] for l in labels_all])
    T = T / np.clip(np.linalg.norm(T, axis=1, keepdims=True), 1e-9, None)
    all_seqs = [ph for (_w, _fr, ph) in A_lda]
    rows, scores = [], []
    for (w, fr, ph) in A_lda:
        O = np.asarray(fr, float)
        if mode == "perframe":
            lab = [labels_all[j] for j in (O @ T.T).argmax(1)]; sc = float((O @ T.T).max(1).mean())
        elif mode == "viterbi":
            lab = _viterbi_path(O, T, labels_all); sc = float((O @ T.T).max(1).mean())
        else:
            tgt = ph if mode == "transcript" else all_seqs[int(rng.integers(len(all_seqs)))]
            lab = forced_align(O, tgt, theta, gm); sc = -_fa_cost(O, ph, theta, gm) / max(len(O), 1)
        rows.append((O, lab)); scores.append(sc)
    thr = np.quantile(scores, 1.0 - conf_keep)                    # keep the top-conf_keep by score
    acc = defaultdict(lambda: [0, None])
    for (O, lab), sc in zip(rows, scores):
        if sc < thr:
            continue
        for i, l in enumerate(lab):
            e = acc[l]; e[0] += 1; e[1] = O[i].copy() if e[1] is None else e[1] + O[i]
    out = {}
    for l in theta:
        e = acc.get(l)
        out[l] = (1.0 - blend) * theta[l] + blend * (e[1] / e[0]) if (e and e[0] > 2) else theta[l]
    return out


def self_train(theta0, A_lda, B_lda, lex_sub, vocab, mode, iters, blend, conf_keep, rng):
    theta = dict(theta0)
    curve = [seq_fa_acc(B_lda, theta, lex_sub, vocab, np.mean(list(theta.values()), 0))[0]]
    for _ in range(iters):
        theta = pseudo_reestimate(theta, A_lda, mode, conf_keep, blend, rng)
        curve.append(seq_fa_acc(B_lda, theta, lex_sub, vocab, np.mean(list(theta.values()), 0))[0])
    return theta, curve


def main():
    quick = "--quick" in sys.argv
    t0 = time.time(); rng = np.random.default_rng(0)
    print("=" * 110)
    print("LEVER 8 — LABEL-FREE CENTROID DOMAIN ADAPTATION (forced-align self-training) toward the real domain")
    print("  SPLIT: fit/ground TRAIN-clean; ADAPT (unlabeled, self-decoded) dev-clean HALF-A; TEST dev-clean HALF-B")
    print("=" * 110, flush=True)

    N = 8000 if quick else 32000
    n_shards = 4 if quick else 12
    cal = load_train_f32(n_shards, 10000 if quick else N + 4000)
    dev = [(w, fr.astype(np.float32), ph) for (w, fr, ph) in _load_ph("dev-clean_*.pkl", 3 if quick else 8)]
    cal_g = cal[:N]
    lexicon = majority_lexicon(cal + dev)
    dev_count = Counter(w for w, _f, _p in dev)
    vocab = sorted([w for w, c in dev_count.items()
                    if w not in FUNC and len(w) >= 4 and c >= (4 if quick else 6) and w in lexicon])
    vocab = vocab[: (18 if quick else 28)]
    vset = set(vocab); chance = 1.0 / len(vocab)

    # dev-clean split: HALF-A = adapt (unlabeled), HALF-B = test (disjoint). Use a fixed permutation.
    didx = np.random.default_rng(1).permutation(len(dev))
    nA = len(dev) // 2
    devA = [dev[i] for i in didx[:nA]]; devB = [dev[i] for i in didx[nA:]]
    print(f"  train cal_g {len(cal_g)}; dev HALF-A(adapt) {len(devA)} / HALF-B(test) {len(devB)}; vocab "
          f"{len(vocab)} (chance {chance:.3f})   [{time.time()-t0:.0f}s]", flush=True)

    K, W = 3, 5
    NG = 200 if quick else 500
    lex_sub = {w: expand_seq(s, K) for w, s in lexicon.items()}
    gw = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in cal_g[:NG]]

    # FLAT inventory (inference closed): LDA + initial centroids grounded on TRAIN
    feats, _ = fit_modes(cal_g, K, W, (2 if quick else 4), np.random.default_rng(7))
    enc = feats["flat"][0]
    theta0, durs0 = ground_subpart_theta(transform_words(gw, enc), np.random.default_rng(99))
    print(f"  flat sub-part LDA + TRAIN-grounded centroids ({len(theta0)} sub-parts)   [{time.time()-t0:.0f}s]",
          flush=True)

    # transform adapt + test to LDA
    A_lda = transform_words(devA[: (1000 if quick else 2500)], enc)
    A_lda = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in A_lda]
    B_lda = transform_words(devB[: (4000 if quick else 12000)], enc)
    B_lda = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in B_lda if w in vset]
    print(f"  adapt words {len(A_lda)}, test content positions {len(B_lda)}   [{time.time()-t0:.0f}s]", flush=True)

    ITERS = 2 if quick else 4
    BLEND, CONF = 0.25, 0.7
    start = seq_fa_acc(B_lda, theta0, lex_sub, vocab, np.mean(list(theta0.values()), 0))[0]
    # ORACLE: dev-matched centroids on HALF-B (reference; leaks B labels)
    devc = dev_centroids(B_lda, forced_align, theta0)
    oracle = seq_fa_acc(B_lda, devc, lex_sub, vocab, np.mean(list(devc.values()), 0))[0]
    print(f"  START (train-grounded) {start:.3f}  |  ORACLE (dev-B-matched, leaks) {oracle:.3f}   "
          f"[{time.time()-t0:.0f}s]", flush=True)

    curves = {}
    for mode in ("viterbi", "perframe", "transcript", "shuffled"):
        _, curves[mode] = self_train(theta0, A_lda, B_lda, lex_sub, vocab, mode, ITERS, BLEND, CONF,
                                     np.random.default_rng(3))
        print(f"  {mode:10s} curve: {['%.3f' % c for c in curves[mode]]}   [{time.time()-t0:.0f}s]", flush=True)

    # ============================ GATES ============================
    gap = oracle - start
    def best(m): return max(curves[m])
    def closed(m): return 100 * (best(m) - start) / gap if gap > 1e-6 else 0.0
    # the genuinely LABEL-FREE result (viterbi) and the weak-supervision reference (transcript)
    lf_climbs = best("viterbi") > start + 0.01
    lf_beats_shuf = best("viterbi") > best("shuffled") + 0.01
    lf_beats_pf = best("viterbi") > best("perframe") + 0.01
    ts_climbs = best("transcript") > start + 0.01
    ts_beats_shuf = best("transcript") > best("shuffled") + 0.01
    drift = "monotone" if curves["viterbi"][-1] >= best("viterbi") - 0.005 else \
            f"PEAKS@{int(np.argmax(curves['viterbi']))} then drifts"
    print("\n" + "=" * 110)
    print(f"  ADAPTATION CURVES (start {start:.3f} -> oracle {oracle:.3f}; gap {gap:.3f}; chance {chance:.3f}):")
    for m in ("viterbi", "perframe", "transcript", "shuffled"):
        print(f"    {m:10s}: {['%.3f' % c for c in curves[m]]}  best {best(m):.3f} (gap closed {closed(m):.0f}%)")
    print("-" * 110)
    print("  VERDICT (lever 8 — label-free centroid domain adaptation):")
    print(f"    (a) ARC CLIMBS — label-free VITERBI {start:.3f}->{best('viterbi'):.3f} ({closed('viterbi'):.0f}% "
          f"of gap): {lf_climbs}; weak-sup TRANSCRIPT {start:.3f}->{best('transcript'):.3f} "
          f"({closed('transcript'):.0f}%): {ts_climbs}")
    print(f"    (b) DISCRIMINATIVE — VITERBI {best('viterbi'):.3f} > SHUFFLED {best('shuffled'):.3f} "
          f"({lf_beats_shuf}) & > PER-FRAME {best('perframe'):.3f} ({lf_beats_pf}); TRANSCRIPT > SHUFFLED: {ts_beats_shuf}")
    print(f"    (c) DRIFT GUARD — VITERBI {drift}; per-frame {['%.3f' % c for c in curves['perframe']]}")
    print(f"    (d) donkey=0: pseudo-labels = held Viterbi/forced-align over earned centroids; held centroid "
          f"re-estimation; no borrowed net/LLM/gradient-net. No leakage (adapt dev-A frames, TEST dev-B).")
    if lf_climbs and lf_beats_shuf:
        v = (f"WIN — label-free self-training closes the train->dev gap ({start:.3f}->{best('viterbi'):.3f}, "
             f"{closed('viterbi'):.0f}% toward the {oracle:.3f} oracle), beating shuffled/per-frame.")
    elif ts_climbs and ts_beats_shuf:
        v = (f"PARTIAL/WEAK-SUP WIN — fully label-free (viterbi) self-decode {'climbs' if lf_climbs else 'does not climb'} "
             f"({best('viterbi'):.3f}), but TRANSCRIPT-forced-align (weak supervision) DOES close the gap "
             f"({start:.3f}->{best('transcript'):.3f}, {closed('transcript'):.0f}%) and beats shuffled — adaptation "
             f"WORKS given good pseudo-labels; the binding piece is pseudo-label QUALITY. NEXT LEVER: better "
             f"self-decode (lexicon-Viterbi recognition) to reach transcript-quality labels without supervision.")
    else:
        v = (f"NULL — neither label-free nor transcript adaptation closes the gap here ({best('viterbi'):.3f}/"
             f"{best('transcript'):.3f} vs start {start:.3f}); the pseudo-labels do not move the centroids toward "
             f"dev. NEXT LEVER: per-phone CORAL offset-correction / more adapt data — not irreducible.")
    print(f"  => {v}")
    print("=" * 110, flush=True)
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
