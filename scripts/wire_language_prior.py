"""WIRE THE LANGUAGE PRIOR INTO THE STRONGER EAR — the cipher's two halves, finally composed.

The creator added the prediction support (scripts/abs_language_decode: the bigram LM lm_logp as a graph-callable
UseTool + a Viterbi over the per-word acoustic lattice) and found it needs a STRONGER acoustic front-end -- on
weak-acoustic (17% top-1) LibriSpeech a gentle LM lifted only +3pts and HURT content words. That stronger
front-end is the ear work: 16kHz + a multi-speaker bank + per-cue WCCN (which pushed cross-speaker digits to
83%). This composes the SAME decode (the creator's acoustic_logp + viterbi + lm_logp) over the SHARPER lattice
that ear produces, on connected MEANINGFUL sentences (where the bigram has real structure), held-out speaker:

  bank the sentence vocabulary across TRAIN speakers @16kHz -> fit per-cue WCCN (remove the speaker key) ;
  synth each sentence on a HELD-OUT speaker (known word boundaries) ;
  per word: WHITENED combine-all product -> top-K acoustic lattice (acoustic_logp) ;
  the creator's Viterbi decodes the best SEQUENCE = acoustic_logp + weight * lm_logp(word|prev).

Compares per-word accuracy: acoustic top-1 ALONE vs + the language prior, sweeping the LM weight. If the prior
now lifts CONTENT words too (not just function words), the cipher reads -- both halves working.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.wire_language_prior
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains import wccn
from domains.speech_world import SpeechWorld
from scripts.abs_language_decode import acoustic_logp, viterbi, register_language_prior
from scripts.language_prior import LanguagePrior
from scripts.jabberwock_cipher_full import SENTENCES, FUNCTION

FS = 16000
KCAND = 5
TRAIN = ["lessac", "amy", "alan", "joe", "hfc_female", "northern", "kusal", "bryce",
         "john", "norman", "cori", "alba"]            # the coverage lever (12 speakers, the digit-push setup)
HELD = ["ryan", "jenny"]
RENDS = 3                                              # 3 renditions/speaker (was 1-2) -- sharpen content words
WEIGHTS = [0.0, 0.1, 0.3, 0.6, 1.0, 1.6]


def main():
    print("=" * 96)
    print("WIRE THE LANGUAGE PRIOR INTO THE STRONGER EAR — acoustic (16kHz+WCCN) + the creator's bigram decode")
    print("=" * 96)
    lp = LanguagePrior()
    register_language_prior(lp)                  # the LM is graph-callable (UseTool lm_logp) -- the creator's seam
    vocab = sorted({w for s in SENTENCES for w in s.split()})
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    sw = SpeechWorld(s, source_world=None)
    print(f"  {len(vocab)} word vocab, {len(SENTENCES)} sentences | train {TRAIN} -> held-out {HELD} @ {FS}Hz")
    print(f"  LM: {len(lp.vocab)} word Brown bigram | banking vocabulary across train speakers...", flush=True)

    banked = []
    for w in vocab:
        for v in TRAIN:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": v, "pitch": 50, "rate": 175})
                if out is not None:
                    banked.append((w, SDW.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1])))
    cands = sorted({w for (w, _v) in banked})
    Ws = wccn.fit_per_cue(banked)                # remove the speaker key (the ear work's cross-speaker lever)
    bw = [(w, wccn.whiten(v, Ws)) for (w, v) in banked]

    print("  synthesising held-out sentences + building the acoustic lattice (whitened combine-all product)...",
          flush=True)
    utts = []                                    # [(truth_words, lattice)]
    for spk in HELD:
        for sent in SENTENCES:
            words = sent.split()
            out = sw.synth_concat(words, {"variant": spk, "pitch": 50, "rate": 175})
            if out is None:
                continue
            audio, _fs, bnds = out
            seq_t, seq_l = [], []
            for (w, t0, t1) in bnds:
                seg = np.asarray(audio[int(t0 * FS):int(t1 * FS)], dtype=np.float64)
                if seg.size < int(0.03 * FS):
                    continue
                q = wccn.whiten(SDW.feature_channels(s, seg, FS), Ws)
                lo = acoustic_logp(q, bw, cands)            # the creator's combine-all log-likelihood, whitened
                top = dict(sorted(lo.items(), key=lambda kv: -kv[1])[:KCAND])
                seq_t.append(w); seq_l.append(top)
            if len(seq_t) >= 3:
                utts.append((seq_t, seq_l))

    def accuracy(weight):
        ok = tot = c_ok = c_tot = f_ok = f_tot = 0
        for truth, lattice in utts:
            pred = viterbi(lattice, lp, weight)
            for tr, p in zip(truth, pred):
                tot += 1; ok += int(p == tr)
                if tr in FUNCTION:
                    f_tot += 1; f_ok += int(p == tr)
                else:
                    c_tot += 1; c_ok += int(p == tr)
        return (ok / max(tot, 1), c_ok / max(c_tot, 1), f_ok / max(f_tot, 1), tot, c_tot, f_tot)

    # lattice RECALL: is the truth even surfaced in the top-K? (the LM can only pick what the ear surfaced)
    r_all = r_c = c_all = c_c = 0
    for truth, lattice in utts:
        for tr, lat in zip(truth, lattice):
            r_all += int(tr in lat); c_all += 1
            if tr not in FUNCTION:
                r_c += int(tr in lat); c_c += 1
    print(f"  lattice recall@{KCAND}: overall {r_all/max(c_all,1)*100:.0f}% | content {r_c/max(c_c,1)*100:.0f}% "
          f"(the LM can only choose truth the ear surfaced)\n")

    base = accuracy(0.0)
    swept = [(w, accuracy(w)) for w in WEIGHTS[1:]]
    best_w, best = max(swept, key=lambda x: x[1][0])

    for (truth, lattice) in utts[:3]:
        print(f"\n  truth    = {' '.join(truth)}")
        print(f"  acoustic = {' '.join(viterbi(lattice, lp, 0.0))}")
        print(f"  +LM      = {' '.join(viterbi(lattice, lp, best_w))}")

    print("\n" + "=" * 96)
    print(f"  word accuracy ({base[3]} words, {len(cands)}-word vocab) — overall | content({base[4]}) | function({base[5]}):")
    print(f"    acoustic top-1 ALONE     : {base[0]*100:5.1f}% | {base[1]*100:5.1f}% | {base[2]*100:5.1f}%")
    for w, r in swept:
        mark = "  <- best" if w == best_w else ""
        print(f"    + LM (weight {w:>4})       : {r[0]*100:5.1f}% | {r[1]*100:5.1f}% | {r[2]*100:5.1f}%{mark}")
    dall, dcon, dfun = (best[0]-base[0])*100, (best[1]-base[1])*100, (best[2]-base[2])*100
    print(f"\n  best lift {dall:+.1f}pts overall (weight {best_w}); content {dcon:+.1f}pts, function {dfun:+.1f}pts.")
    if dall > 3 and dcon >= -1:
        print("  THE CIPHER READS: with the stronger 16kHz+WCCN ear, the creator's bigram prior lifts recognition")
        print("  WITHOUT wrecking content words -- the sharper lattice gives the LM a real choice, not a frequency")
        print("  override. Both halves composed: the ear surfaces the candidates, the language prior reads them.")
    elif dall > 0:
        print(f"  the prior helps overall (+{dall:.1f}) but the content-word cost ({dcon:+.1f}) shows the lattice is still")
        print("  not sharp enough for them -- more coverage/cues on the content words, or the larger bank.")
    else:
        print(f"  no overall lift here ({dall:+.1f}) -- on this sharp synth lattice the acoustic top-1 is already strong;")
        print("  the LM's room is where the acoustics are weak (connected/reduced words), not clean isolated synth.")
    print("=" * 96)


if __name__ == "__main__":
    main()
