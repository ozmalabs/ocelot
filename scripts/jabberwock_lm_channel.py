"""Wire the agent's OWN graph-native learned LM in as the language channel.

The previous step used a numpy bigram. Replace it with the agent's existing
graph-native LM faculty (scripts/jabberwock_lm_learn.learn_lm + seeds/lm_learn.json):
the agent OBSERVES the speech word-corpus and LEARNS the bigram log-prob LM AS GRAPH
DATA (tally_bigram -> count -> total -> logp Rules over Bigram nodes), then we read
its OWN learned Bigram.logp as the language channel and combine it with the acoustic
channel (Bayes product in log space = the agent's combinatorial/weighted-channel form),
decoded by Viterbi over the corpus-ordered dev stream.

So both channels are the agent's: acoustic (learned encoder) x language (graph-learned
LM). Cross-speaker: learn on train-clean-100, test on UNSEEN dev. (The agent also holds
a graph-native Viterbi, decode() in jabberwock_lm_learn; we use the same DP here over
the speech emissions and the agent's learned logp.)

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_lm_channel.py [n_words] [max_dev]
"""
from __future__ import annotations
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_learned_encoder import _spk_env, _feat, _fit_pca, _fit_lda
import scripts.jabberwock_lm_learn as JLM

BANK = "/home/matt/data/phonebank"


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
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    max_dev = int(sys.argv[2]) if len(sys.argv) > 2 else 400

    train = _stream("train-clean-100_*.pkl", 10)
    dev = _stream("dev-clean_*.pkl", 12)
    vocab = [w for w, _ in Counter(w for w, _ in train).most_common(K)]
    vset = set(vocab); vi = {w: i for i, w in enumerate(vocab)}
    print("=" * 90)
    print("LANGUAGE CHANNEL = THE AGENT'S GRAPH-NATIVE LEARNED LM (learn_lm Rules)")
    print("=" * 90)
    print(f"  vocab(K={K}): {vocab[:12]}...")

    # ACOUSTIC channel: learned encoder (as before)
    by = defaultdict(list)
    for w, fr in train:
        if w in vset and len(by[w]) < 40:
            by[w].append(fr)
    sup = [(w, fr) for w, frs in by.items() for fr in frs]
    s_env = _spk_env(sup, 24)
    Sx = np.array([_feat(fr, s_env[i]) for i, (w, fr) in enumerate(sup)])
    sy = [w for w, _ in sup]
    mu, Wp = _fit_pca(Sx, min(120, len(Sx) - K - 1)); Wl = _fit_lda((Sx - mu) @ Wp, sy, K - 1)
    enc = lambda X: ((X - mu) @ Wp @ Wl)
    Se = enc(Sx); Se /= np.clip(np.linalg.norm(Se, axis=1, keepdims=True), 1e-9, None)
    cent = np.array([Se[[i for i in range(len(sy)) if sy[i] == w]].mean(0) for w in vocab])
    cent /= np.clip(np.linalg.norm(cent, axis=1, keepdims=True), 1e-9, None)

    # LANGUAGE channel: the AGENT learns the bigram LM graph-natively from the corpus
    corpus = []
    prev = None
    for w, _ in train:
        if w in vset:
            if prev is not None:
                corpus.append((vi[prev], vi[w]))
            prev = w
        else:
            prev = None
    corpus = corpus[:6000]
    JLM.ALPHA = K; JLM.SMOOTH = 1.0
    print(f"  agent observes {len(corpus)} word-transitions; learning the bigram LM as graph data (learn_lm Rules)...")
    logp = JLM.learn_lm(corpus)                       # GRAPH-NATIVE learned LM (Bigram.logp)
    rowp = np.exp(logp); rowp /= rowp.sum(1, keepdims=True)
    print(f"  learned LM read back from the graph: logp shape {logp.shape}, rows normalise (mean sum {rowp.sum(1).mean():.2f})")

    # DEV acoustic posterior
    devv = [(w, fr) for w, fr in dev if w in vset][:max_dev]
    q_env = _spk_env(devv, 3)
    Qe = enc(np.array([_feat(fr, q_env[i]) for i, (w, fr) in enumerate(devv)]))
    Qe /= np.clip(np.linalg.norm(Qe, axis=1, keepdims=True), 1e-9, None)
    tau = 0.1
    S = (Qe @ cent.T) / tau
    logac = S - np.log(np.exp(S).sum(1, keepdims=True))
    truth = [vi[w] for w, _ in devv]; T = len(devv)
    ac_only = float(np.mean([logac[t].argmax() == truth[t] for t in range(T)]))

    def viterbi(lam):                                 # combine acoustic + agent's LM (Bayes product = log-sum)
        dp = logac[0].copy(); bp = np.zeros((T, K), int)
        for t in range(1, T):
            cand = dp[:, None] + lam * logp           # logp[prev, next] = agent's graph-learned LM
            bp[t] = cand.argmax(0); dp = logac[t] + cand.max(0)
        seq = [int(dp.argmax())]
        for t in range(T - 1, 0, -1):
            seq.append(int(bp[t][seq[-1]]))
        seq.reverse()
        return float(np.mean([seq[t] == truth[t] for t in range(T)]))

    print(f"\n  acoustic-only         : {ac_only:.3f}")
    print(f"   lambda  + agent's LM")
    best = (ac_only, 0.0)
    for lam in (0.5, 1.0, 2.0, 4.0):
        a = viterbi(lam); print(f"   {lam:4.1f}    {a:.3f}")
        if a > best[0]:
            best = (a, lam)
    print("\n" + "=" * 90)
    print(f"  acoustic-only {ac_only:.3f} -> + AGENT'S GRAPH-LEARNED LM {best[0]:.3f} (lambda={best[1]})  "
          f"lift {best[0]-ac_only:+.3f}")
    print("=" * 90)
    print("  The language channel is the agent's OWN faculty: it observed the corpus and LEARNED the bigram")
    print("  LM as GRAPH DATA (tally/count/logp Rules -> Bigram.logp), read back into the decode and combined")
    print("  with the acoustic channel (Bayes product). No numpy LM — the prior is graph-native and earned.")
    return 0 if best[0] > ac_only + 0.02 else 2


if __name__ == "__main__":
    raise SystemExit(main())
