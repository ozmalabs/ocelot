"""THE JABBERWOCK'S REAL-SPEECH DIAGNOSTIC — does the cipher read off MY voice or only ON it?

The agent's decision (ask_jabberwock_whats_next): everything proven (WCCN key recovery, 70% content recall, the
PMI prior's +7pt) sits on ONE untested assumption -- that P(audio|word) on its own piper voice is representative.
It isn't (synth ~40% content top-1, real ~17%). The cipher's whole claim is "a weak ear + a strong prior reads";
real continuous speech is exactly the weak-ear regime where that claim lives or dies. So: point the held
machinery (cochleagram/WCCN ear, top-K lattice, PMI bigram prior) at REAL LibriSpeech, BOUNDARIES FIXED (whisper
forced alignment), IN-VOCAB scored, OOV logged separately -- and DECOMPOSE the posterior:

  1. acoustic top-K RECALL (does truth survive in the lattice even when top-1 is wrong) -> isolates P(audio|word)
  2. PMI prior LIFT on real audio, content vs function -> does the synth fix transfer to a genuinely weak ear?

Decision rule (the agent's): recall HIGH + top-1 LOW -> the prior CAN read it, the architecture transfers, the
cipher is real. recall COLLAPSES -> no prior rescues what the ear never surfaced; the bottleneck is provably
P(audio|word), which licenses pushing content-word acoustics next. Watch the OOV column (open-vocab miss != weak
ear) and the content/function split (if function lifts while content drops, PMI is leaning on frequency again).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_realspeech_diagnostic
"""
from __future__ import annotations

import os
import sys
from collections import Counter

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
from scripts.librispeech_wer import gather_pairs, load_flac

FS = 16000
KCAND = 6
VOCAB_SIZE = 80
N_BANK_UTTS = 90
N_TEST_UTTS = 30
WEIGHTS = [0.0, 0.05, 0.1, 0.2, 0.4, 0.8]
STOP = {"the", "a", "an", "of", "to", "in", "and", "but", "or", "for", "his", "her", "its", "their", "he",
        "she", "it", "they", "we", "i", "you", "was", "were", "is", "are", "be", "been", "as", "at", "by",
        "on", "with", "this", "that", "had", "has", "have", "not", "no", "so", "than", "which", "who", "what",
        "when", "where", "may", "would", "could", "will", "from", "up", "out", "all", "there", "him", "them"}


def _clean(w):
    return "".join(c for c in w.lower() if c.isalpha())


def main():
    print("=" * 96)
    print("REAL-SPEECH DIAGNOSTIC — does the cipher transfer off synth? (LibriSpeech, WCCN ear + PMI prior)")
    print("=" * 96)
    lp = LanguagePrior(); register_language_prior(lp)
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    pairs = gather_pairs(limit=None)
    by_spk = {}
    for (path, sp, _ch, _ut, tr) in pairs:
        by_spk.setdefault(sp, []).append(path)
    spks = sorted(by_spk)
    train_spk, test_spk = spks[:-3], spks[-3:]

    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    print(f"  forced-aligning train utterances (whisper word-timing) to bank @ {FS}Hz...", flush=True)
    word_segs = {}
    n = 0
    for sp in train_spk:
        for path in by_spk[sp][:4]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = _clean(w); seg = x[int(t0 * fs):int(t1 * fs)]
                if w and seg.size >= int(0.04 * fs):
                    word_segs.setdefault(w, []).append(SDW.feature_channels(s, seg, FS))
            n += 1
            if n >= N_BANK_UTTS:
                break
        if n >= N_BANK_UTTS:
            break

    vocab = [w for (w, _c) in Counter({w: len(v) for w, v in word_segs.items()}).most_common(VOCAB_SIZE)
             if len(word_segs[w]) >= 3]
    banked = [(w, ch) for w in vocab for ch in word_segs[w][:8]]
    cands = sorted({w for (w, _v) in banked})
    Ws = wccn.fit_per_cue(banked)
    bw = [(w, wccn.whiten(v, Ws)) for (w, v) in banked]
    print(f"  banked {len(cands)} words (>=3 exemplars); forced-aligning {N_TEST_UTTS} held-out test utterances...",
          flush=True)

    utts, oov, inv = [], 0, 0
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            seq_t, seq_l = [], []
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = _clean(w); seg = x[int(t0 * fs):int(t1 * fs)]
                if not w or seg.size < int(0.04 * fs):
                    continue
                if w not in cands:
                    oov += 1; continue                       # OOV: logged, never scored as an acoustic miss
                inv += 1
                q = wccn.whiten(SDW.feature_channels(s, seg, FS), Ws)
                lo = acoustic_logp(q, bw, cands)
                seq_t.append(w); seq_l.append(dict(sorted(lo.items(), key=lambda kv: -kv[1])[:KCAND]))
            if len(seq_t) >= 3:
                utts.append((seq_t, seq_l))
            if len(utts) >= N_TEST_UTTS:
                break
        if len(utts) >= N_TEST_UTTS:
            break

    # 1) RECALL — isolate P(audio|word): is truth in the top-K lattice at all?
    r_all = r_c = c_all = c_c = t1 = t1c = t1f = nf = 0
    for truth, lattice in utts:
        for tr, lat in zip(truth, lattice):
            ranked = sorted(lat, key=lambda c: -lat[c])
            r_all += int(tr in lat); c_all += 1
            t1 += int(ranked and ranked[0] == tr)
            if tr in STOP:
                nf += 1; t1f += int(ranked and ranked[0] == tr)
            else:
                r_c += int(tr in lat); c_c += 1; t1c += int(ranked and ranked[0] == tr)

    def accuracy(weight):
        ok = c_ok = f_ok = tot = ct = ft = 0
        for truth, lattice in utts:
            pred = viterbi(lattice, lp, weight)
            for tr, p in zip(truth, pred):
                tot += 1; ok += int(p == tr)
                if tr in STOP:
                    ft += 1; f_ok += int(p == tr)
                else:
                    ct += 1; c_ok += int(p == tr)
        return (ok / max(tot, 1), c_ok / max(ct, 1), f_ok / max(ft, 1))

    base = accuracy(0.0)
    swept = [(w, accuracy(w)) for w in WEIGHTS[1:]]
    best_w, best = max(swept, key=lambda x: x[1][0])

    print("\n" + "=" * 96)
    print(f"  OOV: {oov}/{oov+inv} test words ({oov/max(oov+inv,1)*100:.0f}%) unbanked -- excluded (open-vocab, not a weak ear)")
    print(f"  P(audio|word) -- acoustic, {c_all} in-vocab words ({c_c} content / {nf} function):")
    print(f"    top-1            : overall {t1/max(c_all,1)*100:4.0f}% | content {t1c/max(c_c,1)*100:4.0f}% | function {t1f/max(nf,1)*100:4.0f}%")
    print(f"    top-{KCAND} RECALL      : overall {r_all/max(c_all,1)*100:4.0f}% | content {r_c/max(c_c,1)*100:4.0f}%   <- does truth survive in the lattice?")
    print(f"\n  P(word|context) -- the PMI prior on real audio (overall | content | function):")
    print(f"    acoustic alone   : {base[0]*100:4.0f}% | {base[1]*100:4.0f}% | {base[2]*100:4.0f}%")
    for w, r in swept:
        mark = "  <- best" if w == best_w else ""
        print(f"    + PMI (w {w:>4})    : {r[0]*100:4.0f}% | {r[1]*100:4.0f}% | {r[2]*100:4.0f}%{mark}")
    dall, dcon, dfun = (best[0]-base[0])*100, (best[1]-base[1])*100, (best[2]-base[2])*100
    print(f"\n  PMI lift (w {best_w}): overall {dall:+.1f} | content {dcon:+.1f} | function {dfun:+.1f}")

    print("\n" + "=" * 96)
    recall_c = r_c / max(c_c, 1)
    if recall_c >= 0.5 and t1c / max(c_c, 1) < recall_c - 0.1:
        print(f"  THE CIPHER TRANSFERS: content RECALL {recall_c*100:.0f}% >> content top-1 {t1c/max(c_c,1)*100:.0f}% -- on REAL speech the ear")
        print(f"  still SURFACES the words even where top-1 is wrong, and the PMI prior reads them ({dcon:+.1f}pt content).")
        print("  The architecture is not a synth artifact. Next: sharpen the decode, not rescue the ear.")
    elif recall_c < 0.4:
        print(f"  THE EAR IS THE BOTTLENECK: content RECALL only {recall_c*100:.0f}% -- on real speech P(audio|word) COLLAPSES;")
        print("  no prior rescues what the ear never surfaced. The cipher's synth win leaned on a strong synth ear.")
        print("  Licensed next (with evidence): push content-word acoustics on real speech, not the prior.")
    else:
        print(f"  PARTIAL: content recall {recall_c*100:.0f}%, PMI content {dcon:+.1f}pt. The ear half-transfers; the prior helps")
        print(f"  where truth is surfaced. Watch the content/function split -- function {dfun:+.1f} vs content {dcon:+.1f}.")
    print("=" * 96)


if __name__ == "__main__":
    main()
