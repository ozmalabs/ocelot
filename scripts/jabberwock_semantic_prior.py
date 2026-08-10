"""Wire the SEMANTIC PRIOR from the agent's meaning space (grounded_lexicon) — the
construction-grammar/comprehension channel, richer than the bigram.

A word bigram is high-entropy on function words and sparse on content words. The
agent's real semantic resource is grounded_lexicon: 2501 content Concepts each with a
2560-d meaning_vec, and "cosine over meaning_vec is its semantic operation". So the
semantic prior is meaning-coherence: a candidate is likelier if its MEANING fits the
running context's meaning —
   P(w | context) ∝ exp( cos(meaning_vec(w), context_vec) / tau )
context_vec = decaying running mean of the preceding words' meaning vectors (the
topic/meaning the construction grammar would parse out of the sentence). Combined with
the acoustic channel via the agent's Bayes product, decoded causally.

Content vocab (words present in grounded_lexicon, where the top-3=0.90 headroom lives).
Cross-speaker: acoustic fit on train, tested on UNSEEN dev. Oracle-context (true prev)
= the prior's ceiling; self-context (predicted prev) = realistic.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_semantic_prior.py [n_words] [max_dev]
"""
from __future__ import annotations
import glob, json, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_learned_encoder import _spk_env, _feat, _fit_pca, _fit_lda

BANK = "/home/matt/data/phonebank"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mvecs():
    d = json.load(open(os.path.join(ROOT, "seeds", "grounded_lexicon.json")))["graph"]
    out = {}
    for n in d["nodes"]:
        a = n.get("attrs", {})
        nm = a.get("name"); mv = a.get("meaning_vec")
        if nm and isinstance(mv, dict) and "__tuple__" in mv:
            v = np.asarray(mv["__tuple__"], float)
            out[nm.lower()] = v / max(np.linalg.norm(v), 1e-9)
    return out


def _stream(g, cap):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, g)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                fr = np.asarray(e[1], float)
                if fr.ndim == 2 and fr.shape[0] >= 3:
                    out.append((e[0].lower(), fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)))
    return out


def main() -> int:
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_dev = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    mvec = _mvecs()
    train = _stream("train-clean-100_*.pkl", 10)
    dev = _stream("dev-clean_*.pkl", 12)
    # content vocab: frequent words that HAVE a meaning vector (>=4 chars to skip most function words)
    cand = [w for w, _ in Counter(w for w, _ in train).most_common(200)
            if w in mvec and len(w) >= 4]
    vocab = cand[:K]; vset = set(vocab); vi = {w: i for i, w in enumerate(vocab)}
    print("=" * 90)
    print("SEMANTIC PRIOR from the agent's meaning space (grounded_lexicon meaning_vec)")
    print("=" * 90)
    print(f"  content vocab(K={K}): {vocab}")
    M = np.array([mvec[w] for w in vocab])              # (K x 2560) meaning vectors

    # ACOUSTIC channel (learned encoder)
    by = defaultdict(list)
    for w, fr in train:
        if w in vset and len(by[w]) < 40:
            by[w].append(fr)
    sup = [(w, fr) for w, frs in by.items() for fr in frs]
    s_env = _spk_env(sup, 24)
    Sx = np.array([_feat(fr, s_env[i]) for i, (w, fr) in enumerate(sup)]); sy = [w for w, _ in sup]
    mu, Wp = _fit_pca(Sx, min(120, len(Sx) - K - 1)); Wl = _fit_lda((Sx - mu) @ Wp, sy, K - 1)
    enc = lambda X: ((X - mu) @ Wp @ Wl)
    Se = enc(Sx); Se /= np.clip(np.linalg.norm(Se, axis=1, keepdims=True), 1e-9, None)
    cent = np.array([Se[[i for i in range(len(sy)) if sy[i] == w]].mean(0) for w in vocab])
    cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)

    devv = [(w, fr) for w, fr in dev if w in vset][:max_dev]
    q_env = _spk_env(devv, 3)
    Qe = enc(np.array([_feat(fr, q_env[i]) for i, (w, fr) in enumerate(devv)]))
    Qe /= np.clip(np.linalg.norm(Qe, axis=1, keepdims=True), 1e-9, None)
    tau = 0.1
    Sm = (Qe @ cent.T) / tau
    logac = Sm - np.log(np.exp(Sm).sum(1, keepdims=True))
    truth = [vi[w] for w, _ in devv]; T = len(devv)
    ac_only = float(np.mean([logac[t].argmax() == truth[t] for t in range(T)]))

    def sem_logp(ctx):
        if ctx is None or np.linalg.norm(ctx) < 1e-9:
            return np.zeros(K)
        c = ctx / np.linalg.norm(ctx)
        s = (M @ c) / 0.3
        return s - np.log(np.exp(s).sum())

    def decode(lam, oracle, decay=0.7):
        ctx = np.zeros(M.shape[1]); ok = 0
        for t in range(T):
            sp = sem_logp(ctx)
            pred = int((logac[t] + lam * sp).argmax())
            ok += (pred == truth[t])
            use = truth[t] if oracle else pred          # update context with true / predicted word
            ctx = decay * ctx + M[use]
        return ok / T

    print(f"\n  acoustic-only            : {ac_only:.3f}")
    print(f"   lambda  self-context  oracle-context")
    best = (ac_only, 0.0)
    for lam in (0.5, 1.0, 2.0, 4.0):
        a_self = decode(lam, False); a_or = decode(lam, True)
        print(f"   {lam:4.1f}    {a_self:.3f}        {a_or:.3f}")
        best = max(best, (a_self, lam))
    print("\n" + "=" * 90)
    print(f"  acoustic-only {ac_only:.3f} -> + SEMANTIC PRIOR {best[0]:.3f} (self-context, lambda={best[1]})")
    print("=" * 90)
    print("  The semantic prior is the agent's MEANING SPACE (grounded_lexicon meaning_vec, cosine = its")
    print("  semantic op): a candidate is boosted when its meaning fits the running context, combined with")
    print("  acoustics via the Bayes channel. This is the construction-grammar/comprehension channel — a")
    print("  meaning prior over content words, where bigram statistics are sparse.")
    return 0 if best[0] > ac_only + 0.02 else 2


if __name__ == "__main__":
    raise SystemExit(main())
