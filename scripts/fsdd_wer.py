"""Wire the whole stack into an end-to-end RECOGNIZER and measure WER on a tractable
continuous task (FSDD digit 'sentences' from a Markov source so the LM has signal).
LibriSpeech open-vocab is beyond the stack (the WER reality-check showed it); this is the
small-vocab continuous recognizer that produces real, NON-empty output.

The stack, end to end:
  shape front-end -> frames
  -> JOINT compositional decode: a duration-constrained Viterbi that SEARCHES the
     production space (digit lexicon x boundaries) for the best digit SEQUENCE, scored by
     acoustic match (segment mean shape vs digit prototype) + the LM bigram.
  -> digit sequence -> WER vs truth.
The joint decoder is the agent's derived 'search over the production space' — segment +
recognize TOGETHER, which avoids the catastrophic over-segmentation of segment-then-classify
(that naive wiring gave WER>3; the boundaries fire at phoneme scale, not word scale).
A/B: SHAPE vs ENERGY front-end, and WITH vs WITHOUT the LM. Test = HELD-OUT speakers.

Run: python scripts/fsdd_wer.py [n_sent]
"""
from __future__ import annotations
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from scripts.fsdd_segmentation_realspeech import frames, shape
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN

N_BANDS = 24
LM_WEIGHTS = (0.0, 0.3, 1.0)
# Two digit "languages" of different predictability (Dirichlet concentration): a low alpha
# gives sharp, predictable transitions (an LM can help); a high alpha is near-uniform (an
# LM has nothing to add). Tests the prediction that the LM pays iff the language is
# predictable — the same thing the controlled recognition_layer LM test isolated.
def make_trans(alpha):
    return np.random.RandomState(7).dirichlet(np.ones(10) * alpha, size=10)

SOURCES = [("predictable (a=0.04)", make_trans(0.04)),
           ("free (a=0.6)", make_trans(0.6))]


def decode(M, Pn, lm, lm_w, beta=12.0, min_d=5, max_d=24):
    """JOINT compositional decode (the agent's 'search over the production space'): a
    duration-constrained Viterbi over frames that picks the digit SEQUENCE + its segment
    boundaries TOGETHER, scored by a proper acoustic POSTERIOR (sharpened softmax of
    segment-mean shape vs digit prototype) + lm_w * the LM bigram. Avoids the
    over-segmentation of segment-then-classify; lm_w balances the two log-scores (the
    standard ASR LM weight — an unweighted bigram dwarfs the acoustic posterior)."""
    T = len(M)
    pref = np.vstack([np.zeros(M.shape[1]), np.cumsum(M, axis=0)])

    def segfeat(a, b):
        f = (pref[b] - pref[a]) / max(b - a, 1)
        return f / (np.linalg.norm(f) + 1e-9)

    NEG = -1e18
    best = [(NEG, [])] * (T + 1)
    best[0] = (0.0, [])
    for t in range(min_d, T + 1):
        bs, bseq = NEG, []
        for s in range(max(0, t - max_d), t - min_d + 1):
            ps, pseq = best[s]
            if ps <= NEG / 2:
                continue
            f = segfeat(s, t)
            sim = beta * (Pn @ f)
            ac = sim - (sim.max() + np.log(np.exp(sim - sim.max()).sum()))  # log-posterior
            prev = pseq[-1] if pseq else None
            for d in range(10):
                sc = ps + ac[d] + (lm_w * lm[prev, d] if prev is not None else 0.0)
                if sc > bs:
                    bs, bseq = sc, pseq + [d]
        best[t] = (bs, bseq)
    return best[T][1]


def wer(ref, hyp):
    d = np.zeros((len(ref) + 1, len(hyp) + 1), int)
    d[:, 0] = np.arange(len(ref) + 1); d[0, :] = np.arange(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1,
                          d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
    return d[len(ref), len(hyp)] / max(len(ref), 1)


def feats(s, bank, x, front):
    M = front(frames(s, bank, x))
    return M


def main():
    n_sent = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    files = {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < 25:
            files.setdefault(m.group(2), []).append((int(m.group(1)), os.path.join(DATA, fn)))
    spks = sorted(files); test_spk = set(spks[:2]); train_spk = [p for p in spks if p not in test_spk]

    def train_proto(front):
        proto = {d: [] for d in range(10)}
        for sp in train_spk:
            for d, path in files[sp]:
                proto[d].append(feats(s, bank, load_wav(path)[0], front).mean(0))
        P = np.array([np.mean(proto[d], axis=0) for d in range(10)])
        return P / (np.linalg.norm(P, axis=1, keepdims=True) + 1e-9)

    def test(Pn, front, trans):
        lm = np.log(trans + 1e-6)
        rng = random.Random(0); ref_tot = 0; errs = {w: 0.0 for w in LM_WEIGHTS}
        for _ in range(n_sent):
            seq, cur = [], rng.randrange(10)
            for _ in range(6):
                seq.append(cur); cur = int(np.array([rng.random() < trans[cur][:k+1].sum()
                                                     for k in range(10)]).argmax())
            xs = []
            for d in seq:
                cand = [p for (dd, p) in files[rng.choice(list(test_spk))] if dd == d]
                xs.append(load_wav(rng.choice(cand))[0])
            M = feats(s, bank, np.concatenate(xs), front)
            ref_tot += len(seq)
            for w in LM_WEIGHTS:
                errs[w] += wer(seq, decode(M, Pn, lm, lm_w=w)) * len(seq)
        return {w: errs[w] / ref_tot for w in LM_WEIGHTS}

    fronts = [("energy", lambda M: M), ("shape", shape)]
    protos = {name: train_proto(front) for name, front in fronts}

    print("=" * 66)
    print(f"FSDD continuous-digit WER — full-stack JOINT decoder, {n_sent} sentences x6")
    print(f"  held-out speakers={sorted(test_spk)}; baseline (empty output) WER = 1.000")
    print("=" * 66)
    for src_name, trans in SOURCES:
        print(f"\n  digit language: {src_name}")
        hdr = "  ".join(f"LM={w:g}".rjust(8) for w in LM_WEIGHTS)
        print(f"  {'front-end':10s} {hdr}")
        print("  " + "-" * 50)
        for name, front in fronts:
            r = test(protos[name], front, trans)
            print(f"  {name:10s} " + "  ".join(f"{r[w]:8.3f}" for w in LM_WEIGHTS))
    print("=" * 66)
    print("  LM=0 = acoustic only; LM>0 weights the held digit-bigram LM.")
    print("  shape vs energy = the cross-speaker front-end; LM helps iff language predictable.")


if __name__ == "__main__":
    main()
