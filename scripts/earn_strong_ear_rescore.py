"""STRONG-EAR UNLOCK — meaning-prior rescoring: does the gemma prior now CORRECT the ear, where the weak ear made it impossible?

The jabberwock's design (b): rescoring is RERANKING — it can only help when the right word is already in the N-best. At the
old ~20-25% cross-speaker the right word was usually ABSENT (no prior could grab it); at the strong ear's 80-95% it's PRESENT,
so the gemma meaning_vec's coherence with utterance context can pull it to argmax. The unlock is the CROSS-EAR DELTA, not the
absolute — the identical rescorer on the WEAK ear must fail (its oracle top-k can't contain the word). Three runs on the
cached rig: strong/acoustic, strong/rescored, weak/rescored. PRE-COMMITTED BAR (jabberwock): UNLOCKED iff strong-rescored
>= +3 over strong-acoustic AND weak-rescored <= +0.5 over weak-acoustic. lambda tuned on a DEV split (held-out train spk), not test.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.earn_strong_ear_rescore
"""
from __future__ import annotations

import json
import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import dtw, fit_pca, pca_apply, KMAX, NWAY, PRUNE

CACHE = "/tmp/p0lat_cache_L6.pkl"
LEX = os.path.join(ROOT, "seeds", "grounded_lexicon.json")
KBEST = 10
PCA_D = 64
LAMBDAS = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)


def _l2(M):
    M = np.asarray(M, np.float32); n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def load_lexicon():
    with open(LEX) as f:
        d = json.load(f)
    nodes = d.get("graph", {}).get("nodes", [])
    lex = {}
    for nd in nodes:
        a = nd.get("attrs", nd)
        mv = a.get("meaning_vec")
        if mv is None:
            continue
        v = mv["__tuple__"] if isinstance(mv, dict) and "__tuple__" in mv else mv
        nm = (a.get("name") or "").lower()
        if nm:
            x = np.asarray(v, np.float32); lex[nm] = x / (np.linalg.norm(x) + 1e-9)
    return lex


def nbest(fr, bank, vocab, PW, k=KBEST):
    pv = fr.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
    top = np.argsort(-(PW @ pv))[:PRUNE]
    scored = []
    for i in top:
        c = vocab[i]
        d = min(dtw(fr, e) for e in bank[c])
        scored.append((c, float(d)))
    scored.sort(key=lambda x: x[1])
    return scored[:k]


def build_ear(words_feat):
    """words_feat: list of (w, sp, uid, traj). returns bank, vocab, PW."""
    vc = defaultdict(int)
    for (w, sp, uid, tr) in words_feat:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)
    bank = defaultdict(list); cnt = defaultdict(int)
    for (w, sp, uid, tr) in words_feat:
        if w in vset and cnt[w] < KMAX:
            bank[w].append(tr); cnt[w] += 1
    vocab = [w for w in vocab if bank[w]]
    PW = np.stack([np.stack([e.mean(0) for e in bank[w]]).mean(0) for w in vocab]); PW /= (np.linalg.norm(PW, axis=1, keepdims=True) + 1e-9)
    return bank, vocab, set(vocab), PW


def nbest_all(words_feat, bank, vocab, vset, PW):
    """returns per-token: (gold, uid, [(cand,dist),...])"""
    out = []
    for (w, sp, uid, tr) in words_feat:
        if w not in vset:
            continue
        out.append((w, uid, nbest(tr, bank, vocab, PW)))
    return out


def rescore_eval(nb, lex, lam, oracle_ctx=False):
    """nb: list of (gold, uid, nbest). Context from acoustic-argmax (honest) or GOLD words (oracle upper bound)."""
    # acoustic argmax + per-utterance context (sum of lexicon vecs of the argmax word per token)
    by_utt = defaultdict(list)
    for idx, (gold, uid, cand) in enumerate(nb):
        by_utt[uid].append(idx)
    argmax_vec = [None] * len(nb)
    for idx, (gold, uid, cand) in enumerate(nb):
        ctx_word = gold if oracle_ctx else cand[0][0]      # oracle: build context from the TRUE words
        argmax_vec[idx] = lex.get(ctx_word)
    utt_sum = {}; utt_cnt = {}
    for uid, idxs in by_utt.items():
        vs = [argmax_vec[i] for i in idxs if argmax_vec[i] is not None]
        if vs:
            utt_sum[uid] = np.sum(vs, 0); utt_cnt[uid] = len(vs)
        else:
            utt_sum[uid] = None; utt_cnt[uid] = 0
    ok_ac = ok_re = 0
    for idx, (gold, uid, cand) in enumerate(nb):
        # leave-one-out context centroid
        s, c = utt_sum.get(uid), utt_cnt.get(uid, 0)
        own = argmax_vec[idx]
        if s is not None and own is not None and c > 1:
            ctx = (s - own) / (c - 1)
        elif s is not None and (own is None or c >= 1):
            ctx = s / max(c, 1)
        else:
            ctx = None
        ctx = ctx / (np.linalg.norm(ctx) + 1e-9) if ctx is not None else None
        cands = [w for (w, d) in cand]; dists = np.array([d for (w, d) in cand], np.float32)
        a = -dists; a = (a - a.mean()) / (a.std() + 1e-6)
        if ctx is None or lam == 0.0:
            p = np.zeros(len(cands), np.float32)
        else:
            p = np.array([float(lex[w] @ ctx) if w in lex else 0.0 for w in cands], np.float32)
            p = (p - p.mean()) / (p.std() + 1e-6)
        comb = a + lam * p
        ok_ac += int(cands[0] == gold)               # acoustic argmax (lam-independent)
        ok_re += int(cands[int(np.argmax(comb))] == gold)
    n = len(nb)
    return 100 * ok_ac / n, 100 * ok_re / n


def main():
    print("=" * 100)
    print("STRONG-EAR UNLOCK — meaning-prior rescoring (strong vs weak ear; the cross-ear delta is the result)")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]          # (w, sp, uid, cold_feat, lat768)
    lex = load_lexicon()
    print(f"  lexicon: {len(lex)} meaning concepts")

    # speaker split: hold out ~20% of train speakers as DEV (lambda tune), rest = bank.
    tr_spk = sorted({t[1] for t in train})
    n_dev = max(1, len(tr_spk) // 5)
    dev_spk = set(tr_spk[-n_dev:]); bank_spk = set(tr_spk[:-n_dev])
    bank_rows = [t for t in train if t[1] in bank_spk]
    dev_rows = [t for t in train if t[1] in dev_spk]
    print(f"  split: {len(tr_spk)} train spk -> {len(bank_spk)} bank ({len(bank_rows)} words) / {len(dev_spk)} dev ({len(dev_rows)} words); test {len(test)} words", flush=True)

    # per-speaker CMVN on the STRONG (wav2vec) latent (768) then PCA64; WEAK ear = cold_feat (cochleagram CMVN) directly.
    def spk_cmvn(rows):
        bysp = defaultdict(list)
        for (w, sp, uid, cf, lat) in rows:
            bysp[sp].append(lat)
        return {sp: (np.concatenate(v, 0).mean(0), np.concatenate(v, 0).std(0) + 1e-5) for sp, v in bysp.items()}
    # STRONG ear = RAW wav2vec latent (the jabberwock's premised ~81% regime, with HEADROOM for the prior).
    # (per-speaker oracle CMVN pushes it to ~95.5% = near-ceiling, no room for rescoring to show; raw is the fair test.)
    st = spk_cmvn(train + test)
    USE_CMVN = False
    def scmvn(t):
        if USE_CMVN:
            mu, sd = st[t[1]]; return (t[4] - mu) / sd
        return t[4]                                    # raw latent (~81%)
    mu_p, V_p = fit_pca([scmvn(t) for t in bank_rows])

    def strong_words(rows):
        return [(t[0], t[1], t[2], pca_apply(scmvn(t), mu_p, V_p)) for t in rows]
    def weak_words(rows):
        return [(t[0], t[1], t[2], _l2(t[3])) for t in rows]

    print("  building strong + weak ears (bank=30 train spk)...", flush=True)
    s_bank, s_vocab, s_vset, s_PW = build_ear(strong_words(bank_rows))
    w_bank, w_vocab, w_vset, w_PW = build_ear(weak_words(bank_rows))

    print("  N-best on dev (lambda tune) + test (both ears)...", flush=True)
    s_dev = nbest_all(strong_words(dev_rows), s_bank, s_vocab, s_vset, s_PW)
    s_test = nbest_all(strong_words(test), s_bank, s_vocab, s_vset, s_PW)
    w_test = nbest_all(weak_words(test), w_bank, w_vocab, w_vset, w_PW)

    # tune lambda on DEV (strong)
    best_lam, best_dev = 0.0, -1
    print("\n  lambda tune on dev (strong ear):")
    for lam in LAMBDAS:
        ac, re = rescore_eval(s_dev, lex, lam)
        print(f"    lam {lam:>4}:  acoustic {ac:.1f}  rescored {re:.1f}  ({re-ac:+.1f})")
        if re > best_dev:
            best_dev, best_lam = re, lam
    print(f"  chosen lambda* = {best_lam}\n")

    s_ac, s_re = rescore_eval(s_test, lex, best_lam)
    _, s_re_or = rescore_eval(s_test, lex, best_lam, oracle_ctx=True)   # ORACLE-context upper bound
    w_ac, w_re = rescore_eval(w_test, lex, best_lam)

    print("=" * 100)
    print(f"  @lambda*={best_lam}, cross-speaker test ({len(s_test)} strong / {len(w_test)} weak tokens):")
    print(f"    STRONG ear  acoustic {s_ac:.1f}  -> rescored {s_re:.1f}   ({s_re-s_ac:+.1f})")
    print(f"    STRONG ear  ORACLE-context rescored {s_re_or:.1f}   ({s_re_or-s_ac:+.1f})   <- upper bound on the prior")
    print(f"    WEAK   ear  acoustic {w_ac:.1f}  -> rescored {w_re:.1f}   ({w_re-w_ac:+.1f})")
    print(f"    CROSS-EAR UNLOCK (strong gain - weak gain): {(s_re-s_ac)-(w_re-w_ac):+.1f}")
    print("-" * 100)
    if (s_re - s_ac) >= 3.0 and (w_re - w_ac) <= 0.5:
        print(f"  UNLOCKED — the meaning prior CORRECTS the strong ear (+{s_re-s_ac:.1f}) but cannot help the weak ear ({w_re-w_ac:+.1f}):")
        print("  the prior is no longer STARVED. The strong (borrowed-midpoint) ear made the gemma meaning prior usable downstream —")
        print("  a capability the weak ear physically could not produce. Justifies the graph-native rescorer (the faculty).")
    elif (s_re - s_ac) >= 1.0:
        print(f"  PARTIAL — strong-ear rescoring +{s_re-s_ac:.1f} (< +3 bar), weak {w_re-w_ac:+.1f}. The prior helps a little; real but")
        print("  under the bar (coverage ~44%, context thin). The unlock direction is right; not decisively cleared.")
    else:
        print(f"  NOT UNLOCKED — strong-ear rescoring {s_re-s_ac:+.1f} (~0): even with the right word present, the gemma prior + this")
        print("  context doesn't correct the ear. The prior-rescoring path adds nothing here; honest negative, reported as-is.")
    print("=" * 100)


if __name__ == "__main__":
    main()
