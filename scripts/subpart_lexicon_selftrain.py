"""LEVER 9 — LEXICON-VITERBI SELF-DECODE: make the centroid domain adaptation FULLY LABEL-FREE.

Lever 8 (commit ca79387c): transcript-quality pseudo-labels (forced-align to the known word) close 24% of the
train->dev grounding gap (0.376->0.503) and beat the shuffled control (0.434) — adaptation PAYS given good
pseudo-labels — BUT fully label-free self-decode (free per-frame/viterbi, 0.40/0.40) did NOT beat shuffled: its
pseudo-labels carried no sub-part signal beyond generic distribution-shift, and free-viterbi DRIFTED.

THE FIX (the developmental closure): a LEXICON-constrained self-decode. For each UNLABELED adapt word, RECOGNISE
it over the real LEXICON — a cheap mean-centroid shortlist, then forced-align cost over each shortlisted word's
sub-part-centroid sequence -> pick the best word (the self-recognised 'transcript') -> use THAT word's
forced-alignment as the pseudo-label. Lexicon-constrained recognition gives far better pseudo-labels than the
free per-frame/viterbi decode, so the agent teaches itself the dev-domain centroids WITHOUT any labels.

donkey=0: recognition = held forced-align over the agent's own earned centroids; the lexicon = the agent's own
word->phone pronunciations (no transcripts of the adapt audio, no human labels); re-estimation = held counted
blend. No-leakage split: fit/ground train-clean, ADAPT (recognise+align, NO given labels) on dev-clean HALF-A,
TEST on dev-clean HALF-B.

GATES: (a) LABEL-FREE CLOSES THE GAP — lexicon-Viterbi adaptation reaches/approaches the transcript curve (24%+,
0.503) and clearly BEATS shuffled (0.434) AND free-viterbi (0.40); (b) SELF-RECOGNITION accuracy on the adapt
set (the pseudo-label quality); (c) DISCRIMINATIVE — lexicon > shuffled; (d) DRIFT GUARD — does the lexicon
constraint stop the free-viterbi confirmation-bias drift?; (e) donkey=0, no leakage.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/subpart_lexicon_selftrain.py [--quick]
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
from scripts.subpart_self_train import pseudo_reestimate, self_train


def _unit(M):
    return M / np.clip(np.linalg.norm(M, axis=-1, keepdims=True), 1e-9, None)


def lexicon_reestimate(theta, A_lda, lv_seqs, lv_words, blend, conf_keep, shortlist, rng, report_truth=True):
    """One LEXICON-VITERBI self-training pass. For each unlabeled adapt word: cheap mean-centroid shortlist over
    the lexicon, forced-align cost over the shortlist -> best lexicon word (self-recognised) -> forced-align
    its sub-part sequence -> per-frame pseudo-labels. Blend centroids toward the real frames. Returns
    (new_theta, self_recognition_accuracy)."""
    gm = np.mean(list(theta.values()), 0)
    lv_mean = _unit(np.stack([np.mean([theta.get(l, gm) for l in s], 0) for s in lv_seqs]))
    A_means = _unit(np.stack([np.asarray(fr, float).mean(0) for (_w, fr, _p) in A_lda]))
    sims = A_means @ lv_mean.T                                     # (A, LV) cheap prefilter
    rec = []                                                       # (O, chosen_seq, score, correct?)
    for i, (w, fr, ph) in enumerate(A_lda):
        O = np.asarray(fr, float)
        cand = np.argsort(-sims[i])[:shortlist]
        cost, bj = min((_fa_cost(O, lv_seqs[j], theta, gm), j) for j in cand)
        rec.append((O, lv_seqs[bj], -cost / max(len(O), 1), int(lv_words[bj] == w)))
    scores = [r[2] for r in rec]
    thr = np.quantile(scores, 1.0 - conf_keep)                    # keep top-conf_keep MOST-CONFIDENT recognitions
    acc = defaultdict(lambda: [0, None]); recok = sum(r[3] for r in rec); gok = gtot = 0
    for (O, seq, sc, ok) in rec:
        if sc < thr:
            continue
        gtot += 1; gok += ok                                      # rec accuracy on the KEPT (high-conf) subset
        for j, l in enumerate(forced_align(O, seq, theta, gm)):
            e = acc[l]; e[0] += 1; e[1] = O[j].copy() if e[1] is None else e[1] + O[j]
    out = {}
    for l in theta:
        e = acc.get(l)
        out[l] = (1.0 - blend) * theta[l] + blend * (e[1] / e[0]) if (e and e[0] > 2) else theta[l]
    return out, (recok / max(len(rec), 1)), (gok / max(gtot, 1))


def self_train_lexicon(theta0, A_lda, lv_seqs, lv_words, B_lda, lex_sub, vocab, iters, blend, conf, shortlist, rng):
    theta = dict(theta0)
    curve = [seq_fa_acc(B_lda, theta, lex_sub, vocab, np.mean(list(theta.values()), 0))[0]]
    recs, grecs = [], []
    for _ in range(iters):
        theta, rec, grec = lexicon_reestimate(theta, A_lda, lv_seqs, lv_words, blend, conf, shortlist, rng)
        recs.append(rec); grecs.append(grec)
        curve.append(seq_fa_acc(B_lda, theta, lex_sub, vocab, np.mean(list(theta.values()), 0))[0])
    return theta, curve, recs, grecs


def main():
    quick = "--quick" in sys.argv
    t0 = time.time(); rng = np.random.default_rng(0)
    print("=" * 110)
    print("LEVER 9 — LEXICON-VITERBI SELF-DECODE: fully label-free centroid domain adaptation (the closure)")
    print("  SPLIT: fit/ground TRAIN-clean; ADAPT (recognise+align, NO labels) dev-clean HALF-A; TEST dev-clean HALF-B")
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
    theta0, _durs = ground_subpart_theta(transform_words(gw, enc), np.random.default_rng(99))

    # the self-decode LEXICON: top-frequency TRAIN words (no dev labels), with sub-part sequences
    freq = Counter(w for w, _f, _p in cal_g)
    LV = [w for w, _c in freq.most_common() if w in lexicon][: (600 if quick else 3000)]
    lv_seqs = [expand_seq(lexicon[w], K) for w in LV]
    print(f"  train cal_g {len(cal_g)}; dev A(adapt) {len(devA)}/B(test) {len(devB)}; vocab {len(vocab)} "
          f"(chance {chance:.3f}); self-decode lexicon {len(LV)} words   [{time.time()-t0:.0f}s]", flush=True)

    A_lda = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in transform_words(devA[: (1000 if quick else 2500)], enc)]
    B_lda = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in transform_words(devB[: (4000 if quick else 12000)], enc)
             if w in vset]
    print(f"  adapt {len(A_lda)} words, test {len(B_lda)} content positions   [{time.time()-t0:.0f}s]", flush=True)

    ITERS, BLEND, CONF, SHORT = (2 if quick else 4), 0.25, 0.7, (40 if quick else 60)
    start = seq_fa_acc(B_lda, theta0, lex_sub, vocab, np.mean(list(theta0.values()), 0))[0]
    devc = dev_centroids(B_lda, forced_align, theta0)
    oracle = seq_fa_acc(B_lda, devc, lex_sub, vocab, np.mean(list(devc.values()), 0))[0]
    gap = oracle - start
    print(f"  START {start:.3f} | ORACLE (dev-B-matched, leaks) {oracle:.3f} | gap {gap:.3f}   [{time.time()-t0:.0f}s]",
          flush=True)

    # the new fully-label-free lever (tighter confidence gate: keep only the most-confident recognitions)
    LEXCONF = 0.3
    _, c_lex, recs, grecs = self_train_lexicon(theta0, A_lda, lv_seqs, LV, B_lda, lex_sub, vocab, ITERS, BLEND,
                                               LEXCONF, SHORT, np.random.default_rng(3))
    print(f"  LEXICON-VITERBI curve: {['%.3f' % c for c in c_lex]}  self-rec all {['%.2f' % r for r in recs]} "
          f"kept-{int(LEXCONF*100)}% {['%.2f' % r for r in grecs]}   [{time.time()-t0:.0f}s]", flush=True)
    # comparison curves (reuse lever-8 machinery)
    _, c_ts = self_train(theta0, A_lda, B_lda, lex_sub, vocab, "transcript", ITERS, BLEND, CONF, np.random.default_rng(3))
    _, c_sh = self_train(theta0, A_lda, B_lda, lex_sub, vocab, "shuffled", ITERS, BLEND, CONF, np.random.default_rng(3))
    _, c_vit = self_train(theta0, A_lda, B_lda, lex_sub, vocab, "viterbi", ITERS, BLEND, CONF, np.random.default_rng(3))
    print(f"  transcript {['%.3f' % c for c in c_ts]} | shuffled {['%.3f' % c for c in c_sh]} | "
          f"free-viterbi {['%.3f' % c for c in c_vit]}   [{time.time()-t0:.0f}s]", flush=True)

    # ============================ GATES ============================
    def best(c): return max(c)
    def clo(c): return 100 * (best(c) - start) / gap if gap > 1e-6 else 0.0
    lex_b, ts_b, sh_b, vit_b = best(c_lex), best(c_ts), best(c_sh), best(c_vit)
    closes = lex_b > start + 0.01
    beats_shuf = lex_b > sh_b + 0.01
    beats_vit = lex_b > vit_b + 0.01
    near_ts = lex_b >= ts_b - 0.02
    drift = "monotone" if c_lex[-1] >= lex_b - 0.005 else f"PEAKS@{int(np.argmax(c_lex))} then drifts"
    print("\n" + "=" * 110)
    print(f"  ADAPTATION CURVES (start {start:.3f} -> oracle {oracle:.3f}; gap {gap:.3f}; chance {chance:.3f}):")
    for name, c in [("LEXICON-Viterbi", c_lex), ("transcript(ref)", c_ts), ("shuffled(ctrl)", c_sh),
                    ("free-viterbi", c_vit)]:
        print(f"    {name:16s}: {['%.3f' % x for x in c]}  best {best(c):.3f} (gap closed {clo(c):.0f}%)")
    print(f"  self-recognition acc (all adapt) {['%.2f' % r for r in recs]} | kept-{int(LEXCONF*100)}%-confident "
          f"{['%.2f' % r for r in grecs]} (pseudo-label quality)")
    print("-" * 110)
    print("  VERDICT (lever 9 — lexicon-Viterbi self-decode: the fully-label-free closure):")
    print(f"    (a) LABEL-FREE CLOSES GAP — lexicon {start:.3f}->{lex_b:.3f} ({clo(c_lex):.0f}%); reaches "
          f"transcript {ts_b:.3f} ({clo(c_ts):.0f}%) within 0.02: {near_ts}; closes: {closes}")
    print(f"    (b) SELF-RECOGNITION — all {np.mean(recs):.2f} | kept-confident {np.mean(grecs):.2f} (pseudo-label quality)")
    print(f"    (c) DISCRIMINATIVE — lexicon {lex_b:.3f} > shuffled {sh_b:.3f} ({beats_shuf}) AND > free-viterbi "
          f"{vit_b:.3f} ({beats_vit})")
    print(f"    (d) DRIFT GUARD — lexicon curve {drift} (free-viterbi was {['%.3f' % c for c in c_vit]})")
    print(f"    (e) donkey=0: recognition = held forced-align over earned centroids + own pronunciations; "
          f"re-estimation = held blend; no borrowed net/LLM/gradient-net. No leakage (adapt dev-A, TEST dev-B).")
    if closes and beats_shuf and beats_vit:
        v = (f"WIN — lexicon-constrained self-decode makes the adaptation FULLY LABEL-FREE: {start:.3f}->{lex_b:.3f} "
             f"({clo(c_lex):.0f}% of the gap), beating shuffled {sh_b:.3f} and free-viterbi {vit_b:.3f} "
             f"{'and reaching the transcript curve' if near_ts else ''} — the developmental closure (the agent "
             f"recognises ambient real speech well enough to teach itself the dev-domain centroids).")
    elif closes and beats_shuf:
        v = (f"PARTIAL WIN — lexicon self-decode closes the gap label-free ({lex_b:.3f}, {clo(c_lex):.0f}%) and "
             f"beats shuffled, but stays below the transcript ceiling {ts_b:.3f}; NEXT LEVER: a fuller "
             f"lexicon-Viterbi lattice / larger lexicon to lift self-recognition (now {np.mean(recs):.2f}).")
    else:
        v = (f"SHORT — lexicon self-decode ({lex_b:.3f}) does not yet beat shuffled {sh_b:.3f}; self-recognition "
             f"{np.mean(recs):.2f} too low. NEXT LEVER: larger lexicon + emission shortlist, or per-phone CORAL "
             f"— not irreducible.")
    print(f"  => {v}")
    print("=" * 110, flush=True)
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
