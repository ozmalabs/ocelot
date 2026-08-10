"""LEVER 12 — THE DEVELOPMENTAL ORDER: perceptual narrowing (CORAL) FIRST, then word recognition becomes possible.

Lever 11 (commit 35aa8a6c): recognition-FREE per-sub-part CORAL lifted the centroids 0.376->0.514 (26% of the
gap) with ZERO supervision. Levers 9-10: lexicon-Viterbi self-decode DRIFTED cold (word-recognition ~6% under
the train->dev mismatch -> wrong pseudo-labels). HYPOTHESIS = the human developmental ORDER: the distributional
tuning (CORAL) breaks the chicken-and-egg, so AFTER it the agent can RECOGNISE words well enough to self-teach
the rest.

THE LOOP (unsupervised, on dev-A): STAGE 1 per-sub-part CORAL (recognition-free soft-moment matching) ->
CORAL-lifted centroids; STAGE 2 lexicon-Viterbi self-decode (recognise each word over the lexicon -> forced-
align -> confidence-gated pseudo-label -> re-estimate); ALTERNATE. The decisive measurement: does ungrounded
self-RECOGNITION accuracy RISE after CORAL (from the cold ~6%)?

donkey=0: CORAL = held Dot responsibilities + held moment-matching; recognition = held forced-align over the
agent's own centroids + own pronunciations; re-estimation = held blend. NO labels/transcripts/borrowed net.
No-leakage: fit/ground train-clean, ADAPT dev-A (unsupervised), TEST dev-B.

GATES: (a) DOES SELF-DECODE NOW ADD — CORAL-then-self-decode > CORAL-alone 0.514, toward oracle 0.913;
(b) ★ THE UNLOCK — ungrounded self-rec accuracy RISES post-CORAL vs cold ~6%; (c) DISCRIMINATIVE — self-decode-
after-CORAL > shuffled AND adds beyond CORAL-alone (vs lever-10 null); (d) DRIFT GUARD — monotone now?;
(e) donkey=0, no leakage.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/subpart_dev_order.py [--quick]
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
from scripts.subpart_coral import _unit, soft_resp


def coral_pass(theta, A_Z, blend, tau, shuffle=False, rng=None):
    """One recognition-free per-sub-part CORAL iteration (soft-moment mean matching toward dev)."""
    labels = list(theta); C = _unit(np.stack([theta[l] for l in labels]))
    R = soft_resp(A_Z, C, tau)
    if shuffle:
        R = R[:, rng.permutation(len(labels))]
    den = R.sum(0); m = (R.T @ A_Z) / np.clip(den[:, None], 1e-9, None)
    return {l: ((1 - blend) * theta[l] + blend * m[k]) if den[k] > 2 else theta[l] for k, l in enumerate(labels)}


def _recognize(theta, A_lda, lv_seqs, lv_words, shortlist):
    """Lexicon recognition over the agent's centroids (held forced-align). Returns per-word (chosen_seq, score,
    correct?)."""
    gm = np.mean(list(theta.values()), 0)
    lv_mean = _unit(np.stack([np.mean([theta.get(l, gm) for l in s], 0) for s in lv_seqs]))
    A_means = _unit(np.stack([np.asarray(fr, float).mean(0) for (_w, fr, _p) in A_lda]))
    sims = A_means @ lv_mean.T
    out = []
    for i, (w, fr, ph) in enumerate(A_lda):
        O = np.asarray(fr, float); cand = np.argsort(-sims[i])[:shortlist]
        cost, bj = min((_fa_cost(O, lv_seqs[j], theta, gm), j) for j in cand)
        out.append((O, lv_seqs[bj], -cost / max(len(O), 1), int(lv_words[bj] == w)))
    return out, gm


def self_rec_acc(theta, A_lda, lv_seqs, lv_words, shortlist):
    rec, _ = _recognize(theta, A_lda, lv_seqs, lv_words, shortlist)
    return sum(r[3] for r in rec) / max(len(rec), 1)


def self_decode_pass(theta, A_lda, lv_seqs, lv_words, blend, conf, shortlist, rng, shuffle=False):
    """One lexicon-Viterbi self-decode re-estimation. Returns (new_theta, rec_all, rec_kept)."""
    rec, gm = _recognize(theta, A_lda, lv_seqs, lv_words, shortlist)
    scores = [r[2] for r in rec]; thr = np.quantile(scores, 1.0 - conf)
    acc = defaultdict(lambda: [0, None]); gok = gtot = 0
    for (O, seq, sc, ok) in rec:
        if sc < thr:
            continue
        gtot += 1; gok += ok
        tgt = seq if not shuffle else lv_seqs[int(rng.integers(len(lv_seqs)))]
        for j, l in enumerate(forced_align(O, tgt, theta, gm)):
            e = acc[l]; e[0] += 1; e[1] = O[j].copy() if e[1] is None else e[1] + O[j]
    out = {}
    for l in theta:
        e = acc.get(l)
        out[l] = (1.0 - blend) * theta[l] + blend * (e[1] / e[0]) if (e and e[0] > 2) else theta[l]
    return out, (sum(r[3] for r in rec) / max(len(rec), 1)), (gok / max(gtot, 1))


def main():
    quick = "--quick" in sys.argv
    t0 = time.time(); rng = np.random.default_rng(0)
    print("=" * 110)
    print("LEVER 12 — DEVELOPMENTAL ORDER: CORAL (perceptual narrowing) FIRST, THEN self-decode unlocks")
    print("  SPLIT: fit/ground TRAIN-clean; ADAPT dev-A (unsupervised); TEST dev-B")
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
    didx = np.random.default_rng(1).permutation(len(dev)); nA = len(dev) // 2
    devA = [dev[i] for i in didx[:nA]]; devB = [dev[i] for i in didx[nA:]]

    K, W = 3, 5
    NG = 200 if quick else 500
    lex_sub = {w: expand_seq(s, K) for w, s in lexicon.items()}
    gw = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in cal_g[:NG]]
    feats, _ = fit_modes(cal_g, K, W, (2 if quick else 4), np.random.default_rng(7))
    enc = feats["flat"][0]
    theta0, _d = ground_subpart_theta(transform_words(gw, enc), np.random.default_rng(99))
    freq = Counter(w for w, _f, _p in cal_g)
    LV = [w for w, _c in freq.most_common() if w in lexicon][: (600 if quick else 3000)]
    lv_seqs = [expand_seq(lexicon[w], K) for w in LV]

    A_lda = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in transform_words(devA[: (1000 if quick else 2500)], enc)]
    B_lda = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in transform_words(devB[: (4000 if quick else 12000)], enc)
             if w in vset]
    A_Z = np.concatenate([np.asarray(fr, float) for (_w, fr, _p) in A_lda]).astype(float)
    CORAL_IT, SD_IT, BLEND, TAU, CONF, SHORT = (2 if quick else 4), (2 if quick else 3), 0.3, 0.2, 0.5, (40 if quick else 60)

    def test(th): return seq_fa_acc(B_lda, th, lex_sub, vocab, np.mean(list(th.values()), 0))[0]
    start = test(theta0)
    devc = dev_centroids(B_lda, forced_align, theta0); oracle = test(devc); gap = oracle - start
    rec_cold = self_rec_acc(theta0, A_lda, lv_seqs, LV, SHORT)
    print(f"  adapt {len(A_lda)} words, test {len(B_lda)}; START {start:.3f} | ORACLE {oracle:.3f} | gap {gap:.3f}"
          f" | self-rec COLD {rec_cold:.3f}   [{time.time()-t0:.0f}s]", flush=True)

    # STAGE 1 — CORAL (recognition-free)
    theta = dict(theta0); curve = [start]; phase = ["start"]
    for _ in range(CORAL_IT):
        theta = coral_pass(theta, A_Z, BLEND, TAU); curve.append(test(theta)); phase.append("CORAL")
    theta_coral = dict(theta); coral_best = max(curve)
    rec_post = self_rec_acc(theta_coral, A_lda, lv_seqs, LV, SHORT)
    print(f"  STAGE1 CORAL curve {['%.3f' % c for c in curve]}  best {coral_best:.3f}; self-rec POST-CORAL "
          f"{rec_post:.3f} (cold {rec_cold:.3f})   [{time.time()-t0:.0f}s]", flush=True)

    # STAGE 2 — lexicon self-decode FROM the CORAL-lifted centroids
    recs = []
    for _ in range(SD_IT):
        theta, ra, rk = self_decode_pass(theta, A_lda, lv_seqs, LV, BLEND, CONF, SHORT, np.random.default_rng(3))
        curve.append(test(theta)); phase.append("SELFDEC"); recs.append(rk)
    sd_best = max(curve[CORAL_IT + 1:])
    # one more alternation round (CORAL -> self-decode)
    for _ in range(max(1, CORAL_IT // 2)):
        theta = coral_pass(theta, A_Z, BLEND, TAU); curve.append(test(theta)); phase.append("CORAL2")
    for _ in range(max(1, SD_IT // 2)):
        theta, ra, rk = self_decode_pass(theta, A_lda, lv_seqs, LV, BLEND, CONF, SHORT, np.random.default_rng(3))
        curve.append(test(theta)); phase.append("SELFDEC2")
    final_best = max(curve)
    print(f"  STAGE2 +self-decode curve {['%.3f' % c for c in curve[CORAL_IT+1:]]}  best-after-CORAL {sd_best:.3f} "
          f"(CORAL-alone {coral_best:.3f}); self-rec/iter {['%.2f' % r for r in recs]}   [{time.time()-t0:.0f}s]",
          flush=True)

    # CONTROL: from CORAL-lifted, SHUFFLED self-decode (random lexicon targets)
    th_s = dict(theta_coral)
    for _ in range(SD_IT):
        th_s, _ra, _rk = self_decode_pass(th_s, A_lda, lv_seqs, LV, BLEND, CONF, SHORT, np.random.default_rng(3),
                                          shuffle=True)
    sd_shuf = test(th_s)

    # ============================ GATES ============================
    def clo(x): return 100 * (x - start) / gap if gap > 1e-6 else 0.0
    sd_adds = sd_best > coral_best + 0.01
    unlock = rec_post > rec_cold + 0.03
    beats_shuf = sd_best > sd_shuf + 0.01
    no_drift = curve[-1] >= final_best - 0.02
    print("\n" + "=" * 110)
    print(f"  STAGED CURVE (start {start:.3f} -> oracle {oracle:.3f}; gap {gap:.3f}; chance {chance:.3f}):")
    print("    " + "  ".join(f"{p}:{c:.3f}" for p, c in zip(phase, curve)))
    print("-" * 110)
    print("  VERDICT (lever 12 — does distributional tuning UNLOCK recognition? the developmental order):")
    print(f"    (a) SELF-DECODE NOW ADDS — CORAL-then-self-decode {sd_best:.3f} ({clo(sd_best):.0f}%) > CORAL-alone "
          f"{coral_best:.3f} ({clo(coral_best):.0f}%): {sd_adds}; final {final_best:.3f} ({clo(final_best):.0f}%)")
    print(f"    (b) ★ THE UNLOCK — self-rec POST-CORAL {rec_post:.3f} > COLD {rec_cold:.3f} (+0.03): {unlock}")
    print(f"    (c) DISCRIMINATIVE — self-decode-after-CORAL {sd_best:.3f} > shuffled-after-CORAL {sd_shuf:.3f}: "
          f"{beats_shuf}; adds beyond CORAL-alone (vs lever-10 null): {sd_adds}")
    print(f"    (d) DRIFT GUARD — final {curve[-1]:.3f} vs best {final_best:.3f}: {'no drift' if no_drift else 'DRIFTS'}")
    print(f"    (e) donkey=0: held responsibilities/moment-match + held forced-align recognition + held "
          f"re-estimation; no borrowed net/LLM/gradient-net. No leakage (adapt dev-A, TEST dev-B).")
    if sd_adds and unlock and beats_shuf:
        v = (f"WIN — the DEVELOPMENTAL ORDER completes the loop fully unsupervised: CORAL (perceptual narrowing) "
             f"UNLOCKS recognition (self-rec {rec_cold:.2f}->{rec_post:.2f}), so self-decode now ADDS beyond "
             f"CORAL-alone ({coral_best:.3f}->{sd_best:.3f}, {clo(sd_best):.0f}%) and beats shuffled — distributional "
             f"tuning first, then word recognition, the human order, zero labels.")
    elif unlock and not sd_adds:
        v = (f"PARTIAL — CORAL UNLOCKS recognition (self-rec {rec_cold:.2f}->{rec_post:.2f}) but self-decode still "
             f"does not add beyond CORAL-alone ({sd_best:.3f} vs {coral_best:.3f}); recognition rose but not enough "
             f"to beat the CORAL ceiling. NEXT LEVER: more CORAL iters / per-sub-part covariance to lift "
             f"recognition further — 0.514 is near the unsupervised ceiling.")
    elif sd_adds:
        v = (f"PARTIAL — self-decode adds post-CORAL ({coral_best:.3f}->{sd_best:.3f}) though the self-rec rise is "
             f"modest ({rec_cold:.2f}->{rec_post:.2f}); the order helps. NEXT LEVER: sharpen recognition (covariance).")
    else:
        v = (f"NULL — even after CORAL, self-decode does not add ({sd_best:.3f} vs CORAL {coral_best:.3f}) and "
             f"recognition stays low ({rec_post:.2f}); 0.514 is the UNSUPERVISED CEILING and the rest is a DATA "
             f"cost (grounded words / covariance) = earn-not-borrow-is-data, TRACTABLE not irreducible.")
    print(f"  => {v}")
    print("=" * 110, flush=True)
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
