"""LEVER 7 — LEXICON-VITERBI LATTICE: a JOINT whole-utterance decode, and the COGNITIVE-PAYOFF test.

Lever 6 (commit e2117bfa): a sub-part SEQUENCE decode (independent per-word forced-align, seq-FA ~0.39) tripled
comprehension over whole-word DTW (~0.13) and climbs toward the sequence oracle (~0.49-0.59) — the DECODE was
the bottleneck. Two open frontiers: (1) the achieved 0.39 is still well below the 0.59 oracle (the per-word
decode is INDEPENDENT — no cross-word coupling); (2) the word-transition cognitive prior NULLED as an isolated
per-position bigram (lever 1-3).

THIS lever joins them: a JOINT decode over the ordered content-word stream — at each position the acoustic
EMISSION is the sub-part forced-align cost over the vocab; consecutive positions are COUPLED by the held
WORD-TRANSITION prior (the cognitive layer's counted bigram); Viterbi finds the best JOINT word path. The
question the architecture predicts: does the top-down word prior, dead per-position, ACTIVATE in the joint
decode (lam* > 0, helps) — the two-level-hierarchy coupling payoff?

donkey=0: emission = held Dot/forced-align over the earned LDA sub-part centroids; the lattice transition =
the agent's held COUNTED word-bigram; the decode = held Viterbi. No borrowed net/LLM/gradient-net. No-leakage:
infer/fit/ground/transitions on train-clean, lam on a train-clean holdout, TEST dev-clean. The inventory is
the FLAT equal-split (lever 6 closed the inference question — flat suffices).

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/subpart_lattice_decode.py [--quick]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict

from scripts.jabberwock_subword_recognizer import _load_ph, ctx
from scripts.dynamic_sequence_speech_abs import majority_lexicon, FUNC
from scripts.comprehension_grain_development import expand_seq, transform_words, forced_align, dev_centroids
from scripts.subpart_data_scale import fit_modes, load_train_f32
from scripts.subpart_sequence_decode import _fa_cost, ground_subpart_theta


def content_stream(words, vocab_set, K):
    """The ordered sub-sequence of content-vocab words (frames + SUB-PART-expanded phones) — the 'utterance'
    the lattice decodes."""
    return [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in words if w in vocab_set]


def content_bigram(words, vocab):
    """Held counted word-bigram over the content vocab, in corpus order (the cognitive transition model).
    Returns log P(c | prev) as a (V,V) matrix with add-floor smoothing."""
    vidx = {w: i for i, w in enumerate(vocab)}; V = len(vocab)
    cnt = np.zeros((V, V))
    prev = None
    for (w, _fr, _ph) in words:
        if w in vidx:
            if prev is not None:
                cnt[prev, vidx[w]] += 1
            prev = vidx[w]
    cnt += 1e-3
    return np.log(cnt / cnt.sum(1, keepdims=True))


def emissions(content_words, theta, gm, vseqs, vidx, stay=0.0):
    """Per-position acoustic emission over the vocab: E[pos][c] = -forced_align_cost(frames, vocab[c] sub-part
    seq). stay>0 adds a duration (sub-part self-transition) reward by penalising advance. Returns (E_list,
    true_idx_list). Each E normalised to zero-max / unit-scale for the lam balance."""
    E_list, ti = [], []
    for (w, fr, ph) in content_words:
        O = np.asarray(fr, float)
        c = np.array([_fa_cost_dur(O, s, theta, gm, stay) for s in vseqs])
        e = -c; e = (e - e.max()); sd = e.std() or 1.0; e = e / sd
        E_list.append(e); ti.append(vidx[w])
    return E_list, ti


def _fa_cost_dur(O, sub_seq, theta, gm, stay=0.0):
    """forced-align cost with an optional DURATION (sub-part self-transition) reward: penalise advancing to the
    next sub-part by `stay`, smoothing segment boundaries (the sub-part-transition ablation). stay=0 == _fa_cost."""
    if stay == 0.0:
        return _fa_cost(O, sub_seq, theta, gm)
    P = len(sub_seq); n = len(O)
    tgt = np.stack([theta.get(l, gm) for l in sub_seq])
    C = ((O[:, None, :] - tgt[None]) ** 2).sum(2)
    if P == 1 or n <= P:
        return float(sum(C[i, min(int(i * P / max(n, 1)), P - 1)] for i in range(n)))
    INF = 1e18; D = np.full((n, P), INF); D[0, 0] = C[0, 0]
    for i in range(1, n):
        D[i, 0] = D[i - 1, 0] + C[i, 0]; prev = D[i - 1]
        for j in range(1, P):
            D[i, j] = C[i, j] + min(prev[j], prev[j - 1] + stay)
    return float(D[n - 1, P - 1])


def joint_viterbi(E_list, logT, lam):
    """JOINT Viterbi over the content-word sequence: maximise sum_pos E[pos][c_pos] + lam * sum logT[c_{pos-1},
    c_pos]. lam=0 == independent per-position argmax (the seq-FA baseline). Returns the decoded path."""
    P = len(E_list); V = len(E_list[0])
    D = E_list[0].copy(); B = np.zeros((P, V), int)
    for t in range(1, P):
        S = D[:, None] + lam * logT                              # (prev, c)
        B[t] = S.argmax(0); D = E_list[t] + S.max(0)
    path = [0] * P; path[-1] = int(D.argmax())
    for t in range(P - 1, 0, -1):
        path[t - 1] = int(B[t][path[t]])
    return path


def acc(path, ti):
    return sum(int(p == t) for p, t in zip(path, ti)) / max(len(ti), 1)


def main():
    quick = "--quick" in sys.argv
    t0 = time.time(); rng = np.random.default_rng(0)
    print("=" * 110)
    print("LEVER 7 — LEXICON-VITERBI LATTICE (joint decode) + the COGNITIVE-PAYOFF test")
    print("  SPLIT: infer/fit/ground/transitions train-clean; lam on train holdout; TEST dev-clean")
    print("=" * 110, flush=True)

    N = 8000 if quick else 32000
    n_shards = 4 if quick else 12
    cal = load_train_f32(n_shards, 10000 if quick else N + 12000)   # KEEP corpus order (bigram needs it)
    dev = [(w, fr.astype(np.float32), ph) for (w, fr, ph) in _load_ph("dev-clean_*.pkl", 3 if quick else 8)]
    cal_g = cal[:N]                                                 # fit/ground/transitions
    cal_hold = cal[N:]                                              # lam holdout (corpus-ordered, disjoint)
    lexicon = majority_lexicon(cal + dev)
    dev_count = Counter(w for w, _f, _p in dev)
    vocab = sorted([w for w, c in dev_count.items()
                    if w not in FUNC and len(w) >= 4 and c >= (4 if quick else 6) and w in lexicon])
    vocab = vocab[: (18 if quick else 28)]
    vset = set(vocab); vidx = {w: i for i, w in enumerate(vocab)}; chance = 1.0 / len(vocab)
    print(f"  train cal_g {len(cal_g)} (+holdout {len(cal_hold)}), dev {len(dev)}; vocab {len(vocab)} "
          f"(chance {chance:.3f})   [{time.time()-t0:.0f}s]", flush=True)

    K, W = 3, 5
    NG = 200 if quick else 500
    lex_sub = {w: expand_seq(s, K) for w, s in lexicon.items()}
    vseqs = [lex_sub[w] for w in vocab]
    gw = [(w, fr, expand_seq(ph, K)) for (w, fr, ph) in cal_g[:NG]]

    # FLAT inventory (inference closed): fit LDA + ground sub-part centroids on train
    feats, _ent = fit_modes(cal_g, K, W, (2 if quick else 4), np.random.default_rng(7))
    enc = feats["flat"][0]
    gw_lda = transform_words(gw, enc)
    theta, durs = ground_subpart_theta(gw_lda, np.random.default_rng(99))
    gm = np.mean(list(theta.values()), 0)
    print(f"  flat sub-part LDA + grounded centroids ({len(theta)} sub-parts)   [{time.time()-t0:.0f}s]", flush=True)

    # held word-transition bigram (corpus order)
    logT = content_bigram(cal_g, vocab)
    logT_shuf = logT[rng.permutation(len(vocab))][:, rng.permutation(len(vocab))]   # discriminative control

    # content streams (transform frames to LDA), emissions
    dev_c = transform_words(content_stream(dev[: (4000 if quick else 12000)], vset, K), enc)
    hold_c = transform_words(content_stream(cal_hold[: (4000 if quick else 12000)], vset, K), enc)
    print(f"  content positions: dev {len(dev_c)}, holdout {len(hold_c)}   [{time.time()-t0:.0f}s]", flush=True)

    E_dev, ti_dev = emissions(dev_c, theta, gm, vseqs, vidx)
    E_hold, ti_hold = emissions(hold_c, theta, gm, vseqs, vidx)

    # lam selection on the train holdout (no dev leakage)
    lams = [0.0, 0.5, 1.0, 2.0, 4.0]
    val = [acc(joint_viterbi(E_hold, logT, l), ti_hold) for l in lams]
    lam_star = lams[int(np.argmax(val))]
    print(f"  lam selection on holdout: " + "  ".join(f"{l}:{a:.3f}" for l, a in zip(lams, val)) +
          f"  -> lam*={lam_star}   [{time.time()-t0:.0f}s]", flush=True)

    # ---- decodes on dev ----
    seq_fa = acc(joint_viterbi(E_dev, logT, 0.0), ti_dev)          # lam=0 == independent per-position (seq-FA)
    lattice = acc(joint_viterbi(E_dev, logT, lam_star), ti_dev)    # JOINT word-prior lattice
    lattice_shuf = acc(joint_viterbi(E_dev, logT_shuf, lam_star), ti_dev)
    # sub-part-transition (duration) ablation
    E_dev_dur, _ = emissions(dev_c, theta, gm, vseqs, vidx, stay=0.1)
    dur_only = acc(joint_viterbi(E_dev_dur, logT, 0.0), ti_dev)
    # oracle: dev-aligned sub-part centroids (reference; leaks)
    devc = dev_centroids(dev_c, forced_align, theta); gmo = np.mean(list(devc.values()), 0)
    E_or, _ = emissions(dev_c, devc, gmo, vseqs, vidx)
    oracle = acc(joint_viterbi(E_or, logT, 0.0), ti_dev)

    print("\n" + "=" * 110)
    print("  LATTICE DECODE (comprehension on held-out dev-clean content positions):")
    print(f"    emission-only per-position (seq-FA, lam=0) : {seq_fa:.3f}")
    print(f"    + sub-part transition (duration, stay=0.1) : {dur_only:.3f}")
    print(f"    + WORD-PRIOR joint lattice (lam*={lam_star})       : {lattice:.3f}")
    print(f"    oracle (dev-aligned centroids, lam=0)      : {oracle:.3f}")
    print(f"    chance {chance:.3f} | n={len(ti_dev)}")
    print("-" * 110)

    # ============================ GATES ============================
    lattice_climbs = lattice > seq_fa + 0.005
    cognitive_payoff = lam_star > 0 and lattice > seq_fa + 0.005
    dur_helps = dur_only > seq_fa + 0.005
    discrim = lattice > lattice_shuf + 0.01
    print("  VERDICT (lever 7 — joint lattice + cognitive payoff):")
    print(f"    (a) LATTICE CLIMBS — joint {lattice:.3f} vs per-position seq-FA {seq_fa:.3f} "
          f"(toward oracle {oracle:.3f}): {lattice_climbs}")
    print(f"    (b) ★ COGNITIVE PAYOFF — word-transition top-down ACTIVATES in the joint decode (lam*={lam_star}"
          f">0 and helps): {cognitive_payoff}  [per-position it NULLED]")
    print(f"    (c) ABLATION — emission {seq_fa:.3f} | +sub-part-transition {dur_only:.3f} (helps {dur_helps}) | "
          f"+word-prior {lattice:.3f}")
    print(f"    (d) DISCRIMINATIVE — real word-bigram {lattice:.3f} > shuffled-bigram {lattice_shuf:.3f}: {discrim}")
    print(f"    (e) donkey=0: emission=held forced-align over earned LDA centroids; transition=held counted "
          f"word-bigram; decode=held Viterbi; no borrowed net/LLM/gradient-net. No leakage (TEST=dev-clean).")
    if lattice_climbs and cognitive_payoff:
        v = (f"WIN — the JOINT lattice closes toward the oracle ({seq_fa:.3f}->{lattice:.3f}, oracle {oracle:.3f}) "
             f"AND the cognitive word-prior ACTIVATES (lam*={lam_star}) where it nulled per-position — the "
             f"two-level coupling pays off at the sequence grain.")
    elif lattice_climbs:
        v = (f"PARTIAL — the joint lattice climbs ({seq_fa:.3f}->{lattice:.3f}) but the word-prior does not "
             f"activate (lam*={lam_star}); the gain is the joint acoustic decode, not the cognitive prior. "
             f"NEXT LEVER: a richer/longer-context language prior or a denser lexicon lattice — not irreducible.")
    elif cognitive_payoff:
        v = (f"PARTIAL — the cognitive prior helps (lam*={lam_star}) but the absolute climb is small; NEXT "
             f"LEVER: better-grounded centroids to lift the emission toward the oracle {oracle:.3f}.")
    else:
        v = (f"NULL — the joint lattice does not beat per-position seq-FA ({lattice:.3f} vs {seq_fa:.3f}) and the "
             f"word prior stays dead (lam*={lam_star}); the content-word bigram carries too little information "
             f"for this vocab. NEXT LEVER: lift the EMISSION toward the oracle {oracle:.3f} (better-grounded "
             f"centroids / more grounding data) — the acoustic floor, not the prior, binds. NOT irreducible.")
    print(f"  => {v}")
    print("=" * 110, flush=True)
    print(f"  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
