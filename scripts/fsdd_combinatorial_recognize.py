"""Wire + measure the agent's COMBINATORIAL recogniser on FSDD cross-speaker.

This is the agent's OWN derived recognition strategy (domains/combinatorial_recognizer
+ the iter32 derivation): two COMPLEMENTARY channels read off the same observation —
  · FLAT (spectral detail, "what is this")     = the cochlear feature, flattened;
  · TRANSITION (order-1-over-time, "which word  = grown_representation.transition_channel
    across speakers")                              (late-minus-early per band + the two
                                                    formant-sweep terms) — the held op.
Each channel emits a scale-free softmax likelihood from its OWN 1-NN cosine exemplar
distance (channel_likelihood; temperature = the channel's median distance, no fit). The
DECISION is the agent's native graph Term-tree predict_combinatorial_term = Argmax over
candidate words of the BAYES PRODUCT P_flat(w)·P_trans(w), evaluated natively. No free
parameters; each channel keeps its role.

The shell supplies held cochlea features (world-adapter) and reads the agent's verdict.
We report each CHANNEL ALONE and the PRODUCT — the agent's claim is the product beats
either channel alone (complementary evidence, no fused-measure contamination).

Run: python scripts/fsdd_combinatorial_recognize.py [test_speaker] [n_per]
"""
from __future__ import annotations
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

from substrate_rs import Substrate
from substrate_rs.speech import _audio
import domains.combinatorial_recognizer as cr
from domains.grown_representation import transition_channel
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS

PATCHES = [(float(i), 1.0) for i in range(N_BANDS)]   # cochlear bands as freq-ordered patches


def channels(s, bank, samples, fs):
    f = feat(s, bank, samples, fs)                    # (bands x windows), held cochlea
    flat = f.flatten().astype(np.float64)             # "what is this"
    trans = transition_channel(f.T, PATCHES)          # held order-1-over-time, "which word"
    return flat, trans


def run(test_spk, n_per):
    files = []
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            files.append((os.path.join(DATA, fn), int(m.group(1)), m.group(2)))

    s = Substrate()
    _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)
    word_node = {d: s.add_node("Concept", {"name": f"d{d}", cr.WORD_ATTR: 1.0})
                 for d in range(10)}
    cands = list(range(10))

    tr_flat, tr_trans, tr_word = [], [], []
    test = []
    for path, digit, spk in files:
        samples, fs = load_wav(path)
        fl, tn = channels(s, bank, samples, fs)
        if spk == test_spk:
            test.append((digit, fl, tn))
        else:
            tr_flat.append(fl); tr_trans.append(tn); tr_word.append(digit)
    Xf = np.asarray(tr_flat); Xt = np.asarray(tr_trans); W = np.asarray(tr_word)

    predict_term = cr.predict_combinatorial_term()
    nflat = ntrans = nprod = 0
    for digit, fl, tn in test:
        p_flat = cr.channel_likelihood(fl, Xf, W, cands)      # the agent's per-channel
        p_trans = cr.channel_likelihood(tn, Xt, W, cands)     # 1-NN exemplar evidence
        # channels alone:
        nflat += (max(p_flat, key=p_flat.get) == digit)
        ntrans += (max(p_trans, key=p_trans.get) == digit)
        # the agent's NATIVE combinatorial decision (Argmax of the Bayes product):
        for d in cands:
            s.set_attr(word_node[d], cr.P_FLAT_ATTR, float(p_flat[d]))
            s.set_attr(word_node[d], cr.P_TRANS_ATTR, float(p_trans[d]))
        win = s._inner.evaluate(predict_term, {})
        pred = next(d for d, n in word_node.items() if n == win)
        nprod += (pred == digit)
    n = len(test)
    return nflat, ntrans, nprod, n


def main():
    test_spk = sys.argv[1] if len(sys.argv) > 1 else None
    n_per = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    speakers = [test_spk] if test_spk else ["george", "jackson", "theo", "nicolas"]
    print("=" * 78)
    print(f"FSDD cross-speaker — the agent's COMBINATORIAL recogniser (Bayes product of")
    print(f"  flat[what] x transition[which-word]); {n_per}/digit/speaker; native decision")
    print("=" * 78)
    agg = [0, 0, 0, 0]
    for spk in speakers:
        fl, tn, pr, n = run(spk, n_per)
        agg[0] += fl; agg[1] += tn; agg[2] += pr; agg[3] += n
        print(f"  [{spk:<9}] flat {fl/n:5.1%}   transition {tn/n:5.1%}   "
              f"PRODUCT {pr/n:5.1%}   (n={n})")
    N = agg[3]
    print("-" * 78)
    print(f"  {'OVERALL':<11}  flat {agg[0]/N:5.1%}   transition {agg[1]/N:5.1%}   "
          f"PRODUCT {agg[2]/N:5.1%}")
    best_ch = max(agg[0], agg[1]) / N
    print(f"\n  combinatorial product vs best single channel: "
          f"{agg[2]/N - best_ch:+.1%}  "
          f"({'product wins' if agg[2] > max(agg[0], agg[1]) else 'no gain over best channel'})")
    print("=" * 78)


if __name__ == "__main__":
    main()
