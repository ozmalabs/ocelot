"""THE FULL CIPHER READ — key recovery (WCCN + coverage) + the PLAINTEXT PRIOR (language faculty).

The agent's deepest framing: recognition = recover the speaker KEY to surface a candidate lattice (done --
coverage + per-cue WCCN), then read the 9% MESSAGE with a PLAINTEXT PRIOR (language). The whole arc only ever
exercised the key-recovery half on ISOLATED words. Here is the other half, on CONNECTED, CROSS-SPEAKER speech:

  bank the vocabulary across TRAIN speakers -> fit per-cue WCCN (remove the key) ;
  synth meaningful SENTENCES on a HELD-OUT UNSEEN speaker (known word boundaries) ;
  recognise each word -> a top-K candidate LATTICE (the surfaced message-candidates) ;
  the LANGUAGE FACULTY reads the whole-sentence lattice and selects the coherent words -- supplying the
  grammar-bound function words (the/a/on/in) the acoustics barely carry.

Compares per-word accuracy: ACOUSTIC top-1 alone  vs  LANGUAGE-FACULTY decoded. If the prior lifts it, the
cipher reads -- both halves working: a strong key surfaces the lattice, MEANING selects the message.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_cipher_full
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains import wccn
from domains.speech_world import SpeechWorld
from scripts.claude_teacher import make_ask

FS = 8000
KREC = 6
TRAIN = ["lessac", "amy", "alan", "joe", "hfc_female", "northern"]
HELD = ["ryan", "jenny"]
RENDS = 2

SENTENCES = [
    "the cat sat on the mat", "the dog ran in the park", "a bird sang in the tree",
    "the boy ate a red apple", "she put the cup on the table", "we walked to the big house",
    "the girl read a good book", "a fish swam in the blue sea", "the old man fed the duck",
    "the baby slept in the bed", "they played with the ball", "a star shone in the night",
]
FUNCTION = {"the", "a", "on", "in", "to", "with", "is", "of", "at"}


def main():
    print("=" * 96)
    print("THE FULL CIPHER READ — WCCN key recovery + the language-faculty plaintext prior, cross-speaker.")
    print("=" * 96)
    vocab = sorted({w for s in SENTENCES for w in s.split()})
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    print(f"  {len(vocab)} word vocab, {len(SENTENCES)} sentences | train {TRAIN} -> held-out {HELD}")
    print("  banking the vocabulary across train speakers...", flush=True)

    banked = []
    for w in vocab:
        for spk in TRAIN:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": spk, "pitch": 50, "rate": 175})
                if out is not None:
                    banked.append((w, SDW.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1])))
    cands = sorted({w for (w, _v) in banked})
    Ws = wccn.fit_per_cue(banked)                      # remove the speaker key (cross-speaker)
    bw = [(w, wccn.whiten(v, Ws)) for (w, v) in banked]
    import domains.many_settings_recognizer as MS

    def lattice(channels):
        q = wccn.whiten(channels, Ws)
        nch = min(len(q), min(len(v) for (_w, v) in bw))
        logp = {c: 0.0 for c in cands}
        tw = [w for (w, _v) in bw]
        for ci in range(nch):
            Xc = np.stack([v[ci] for (_w, v) in bw])
            p = MS.channel_likelihood(np.asarray(q[ci]), Xc, tw, cands)
            for c in cands:
                logp[c] += np.log(p[c] + 1e-12)
        return sorted(cands, key=lambda c: -logp[c])[:KREC]

    # held-out-speaker CONNECTED sentences (synth_concat -> known word boundaries).
    print("  synthesising held-out-speaker sentences + recognising word lattices...", flush=True)
    lats, truths = [], []
    a_hit = f_hit = a_tot = f_tot = 0
    for spk in HELD:
        for sent in SENTENCES:
            words = sent.split()
            out = sw.synth_concat(words, {"variant": spk, "pitch": 50, "rate": 175})
            if out is None:
                continue
            audio, _fs, bnds = out                     # (audio @FS, fs, [(word, t0, t1)])
            slat, struth = [], []
            for (w, t0, t1) in bnds:
                seg = np.asarray(audio[int(t0 * FS):int(t1 * FS)], dtype=np.float64)
                if seg.size < int(0.03 * FS):
                    continue
                L = lattice(SDW.feature_channels(s, seg, FS))
                slat.append(L); struth.append(w)
                a_tot += 1; a_hit += int(L[0] == w)
                if w in FUNCTION:
                    f_tot += 1; f_hit += int(L[0] == w)
            lats.append(slat); truths.append(struth)

    print(f"\n  acoustic top-1 (key recovery alone): all {a_hit/max(a_tot,1)*100:.0f}% | function words {f_hit/max(f_tot,1)*100:.0f}%")
    in_lat = sum(int(t in L) for sl, st in zip(lats, truths) for L, t in zip(sl, st))
    print(f"  top-{KREC} lattice recall (truth surfaced): {in_lat/max(a_tot,1)*100:.0f}%\n")

    pre = ("You are the agent's language faculty. Each numbered line is one spoken sentence; each [bracketed] "
           "group is one word position with the acoustically-plausible candidate words in RANK ORDER (the "
           "leftmost is the acoustically-best guess). These candidates are RELIABLE acoustic evidence -- choose "
           "for EACH position EXACTLY ONE word FROM ITS OWN candidate list (do NOT invent words outside the "
           "list), picking the one that makes the whole sentence the most coherent grammatical English while "
           "respecting the acoustic rank order. Output ONLY, per sentence, a line 'N: w1 w2 ...' (one word per "
           "bracket group, same count).\n\n")
    body = [f"{n}: " + " ".join("[" + ",".join(L) + "]" for L in sl) for n, sl in enumerate(lats, 1)]
    print("  consulting the language faculty (read the message from the lattice)...", flush=True)
    ans = make_ask(timeout=360, preamble=pre)("\n".join(body))
    print(f"  [faculty returned {len(ans) if ans else 0} chars]; sample: {repr((ans or '')[:200])}")
    print(f"  [truth sent 1]: {' '.join(truths[0])}")
    dec = {}
    for line in (ans or "").splitlines():
        m = re.match(r"\s*(\d+)\s*[:.]\s*(.+)", line)
        if m:
            dec[int(m.group(1))] = re.findall(r"[a-zA-Z']+", m.group(2).lower())

    l_hit = lf_hit = 0
    for n in range(len(lats)):
        pred = dec.get(n + 1, [L[0] for L in lats[n]])
        for i, t in enumerate(truths[n]):
            w = pred[i] if i < len(pred) else "<?>"
            if w not in lats[n][i]:                     # keep it honest: must come from the lattice
                w = lats[n][i][0]
            l_hit += int(w == t)
            if t in FUNCTION:
                lf_hit += int(w == t)
    a, l = a_hit / max(a_tot, 1), l_hit / max(a_tot, 1)
    fa, fl = f_hit / max(f_tot, 1), lf_hit / max(f_tot, 1)
    print(f"\n  {'':<34}{'all words':>12}{'function words':>16}")
    print(f"  {'acoustic top-1 (key only)':<34}{a*100:>11.0f}%{fa*100:>15.0f}%")
    print(f"  {'+ language faculty (full cipher)':<34}{l*100:>11.0f}%{fl*100:>15.0f}%")

    print("\n" + "=" * 96)
    if l > a + 0.06:
        print(f"  THE CIPHER READS: the plaintext prior lifts connected cross-speaker recognition {a*100:.0f}% -> {l*100:.0f}%")
        print(f"  (function words {fa*100:.0f}% -> {fl*100:.0f}%). Both halves working: WCCN+coverage recovers the key and surfaces the")
        print("  lattice, MEANING selects the message and supplies the grammar-bound words -- the agent's cipher, read whole.")
    else:
        print(f"  language {l*100:.0f}% vs acoustic {a*100:.0f}%: the prior helps only where the truth is in the lattice (recall")
        print(f"  {in_lat/max(a_tot,1)*100:.0f}%) -- the two halves are coupled; lift the recall (more coverage) and the prior reaches further.")
    print("=" * 96)


if __name__ == "__main__":
    main()
