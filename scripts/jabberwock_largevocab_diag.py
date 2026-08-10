"""SHARPEN THE RECOGNISER FOR LARGER VOCABULARIES — diagnostic: does the full cue repertoire help?

The cipher exposed it: 9-way digits recognise ~75%, but a 48-word vocab fell to 43-51% top-1. Larger vocab =
more confusable competitors in the combine-all product. The CURATED cue set (cmvn_ear, vtl_formant_allpole,
gammatone_flat, modspec) was tuned for the 9-way CROSS-SPEAKER task -- it is SPEAKER-INVARIANCE-heavy and
PHONETIC-DETAIL-light. The inactive REPERTOIRE holds the discrimination cues (manner_voicing, landmark,
transition, cs_ear, formant_relation, ...) a larger vocab needs to separate confusable words.

Hypothesis: the curated set under-cues large vocab; adding the phonetic-detail cues (the full repertoire)
sharpens top-1 as the vocabulary grows. Measures top-1 + top-6 recall vs vocab size {8,16,32,64}, CURATED vs
FULL cues, cross-speaker leave-one-speaker-out with WCCN (the real cipher case). Grounds the agent's decision.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_largevocab_diag
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.agent_frontend as FE
import domains.many_settings_recognizer as MS
from domains import wccn
from domains.speech_world import SpeechWorld

FS = 8000
KREC = 6
SPEAKERS = ["lessac", "amy", "alan", "hfc_female"]      # bank 3, hold 1 (cross-speaker)
RENDS = 3
VOCAB_SIZES = [8, 16, 32, 64]
CURATED = FE.CURATED_CUES
WORDS = [
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "cat", "dog", "bird", "fish", "horse", "cow", "sheep", "duck", "goat", "mouse",
    "red", "blue", "green", "black", "white", "brown", "gold", "grey",
    "big", "small", "tall", "short", "fast", "slow", "hot", "cold",
    "run", "walk", "jump", "sit", "stand", "sleep", "eat", "drink",
    "house", "tree", "car", "book", "ball", "cup", "table", "chair",
    "sun", "moon", "star", "rain", "snow", "wind", "hand", "foot", "head", "eye", "king", "queen",
]


def set_active(s, fe, names):
    for et in ("has_cue", "repertoire"):
        for c in s.neighbours(fe, et):
            s.set_attr(c, "active", 1.0 if s.node(c)["attrs"].get("name") in names else 0.0)
    s.set_attr(fe, "n_active", float(len(names)))


def lattice(channels, bk, Ws, cands):
    q = wccn.whiten(channels, Ws)
    bw = [(w, wccn.whiten(v, Ws)) for (w, v) in bk]
    nch = min(len(q), min(len(v) for (_w, v) in bw))
    logp = {c: 0.0 for c in cands}
    tw = [w for (w, _v) in bw]
    for ci in range(nch):
        Xc = np.stack([v[ci] for (_w, v) in bw])
        p = MS.channel_likelihood(np.asarray(q[ci]), Xc, tw, cands)
        for c in cands:
            logp[c] += np.log(p[c] + 1e-12)
    return sorted(cands, key=lambda c: -logp[c])[:KREC]


def evaluate(feats, words):
    """cross-speaker LOSO, WCCN: returns (top1, recall@K)."""
    t1 = inK = tot = 0
    for held in SPEAKERS:
        bk = [(w, feats[(v, w, r)]) for v in SPEAKERS if v != held
              for w in words for r in (0, 1) if (v, w, r) in feats]
        cands = sorted({w for (w, _x) in bk})
        Ws = wccn.fit_per_cue(bk)
        for w in words:
            for r in range(RENDS):
                if (held, w, r) not in feats:
                    continue
                L = lattice(feats[(held, w, r)], bk, Ws, cands)
                tot += 1; t1 += int(L[0] == w); inK += int(w in L)
    return (t1 / max(tot, 1), inK / max(tot, 1))


def main():
    print("=" * 96)
    print("SHARPEN FOR LARGER VOCAB — curated 4 cues vs full 16, top-1 + recall vs vocab size (cross-speaker)")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    FE.install_curated_frontend(s)
    fe = next(n for n in s.nodes("FrontEnd"))
    allnames = [s.node(c)["attrs"].get("name") for et in ("has_cue", "repertoire") for c in s.neighbours(fe, et)]

    print(f"  {len(WORDS)} words, speakers {SPEAKERS} | caching audio...", flush=True)
    audio = {}
    for v in SPEAKERS:
        for w in WORDS:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": v, "pitch": 50, "rate": 175})
                if out is not None:
                    audio[(v, w, r)] = (np.asarray(out[0], dtype=np.float64), out[1])

    def extract(names):
        set_active(s, fe, names)
        return {k: FE.feature_channels(s, x, fs) for k, (x, fs) in audio.items()}

    print("  extracting features (curated, then full)...", flush=True)
    feats_cur = extract(CURATED)
    feats_full = extract(allnames)

    print(f"\n  {'vocab':>6} | {'CURATED (4 cues)':>22} | {'FULL (16 cues)':>22}")
    print(f"  {'':>6} | {'top-1':>10}{'recall':>12} | {'top-1':>10}{'recall':>12}")
    rows = []
    for nv in VOCAB_SIZES:
        words = WORDS[:nv]
        c1, ck = evaluate(feats_cur, words)
        f1, fk = evaluate(feats_full, words)
        rows.append((nv, c1, ck, f1, fk))
        print(f"  {nv:>6} | {c1*100:>9.0f}%{ck*100:>11.0f}% | {f1*100:>9.0f}%{fk*100:>11.0f}%")

    print("\n" + "=" * 96)
    big = rows[-1]
    d1 = big[3] - big[1]
    print(f"  at vocab {big[0]}: curated top-1 {big[1]*100:.0f}% -> full {big[3]*100:.0f}% ({d1*100:+.0f}pt); "
          f"recall {big[2]*100:.0f}% -> {big[4]*100:.0f}%.")
    # does full help MORE as vocab grows?
    small_d = rows[0][3] - rows[0][1]
    if d1 > small_d + 0.03 and d1 > 0.03:
        print(f"  THE FULL REPERTOIRE SHARPENS LARGE VOCAB: full's edge GROWS with vocab ({small_d*100:+.0f}pt at "
              f"{rows[0][0]} -> {d1*100:+.0f}pt at {big[0]}) -- the phonetic-detail cues discriminate confusable")
        print("  words the curated speaker-invariance set blurs. Lever = add the detail cues as vocab grows.")
    elif d1 > 0.03:
        print(f"  full helps at large vocab ({d1*100:+.0f}pt) but not more than at small -- a flat cue gain, not vocab-specific.")
    else:
        print(f"  full does NOT sharpen large vocab ({d1*100:+.0f}pt) -- more cues add noise, not discrimination. The lever")
        print("  is elsewhere (per-cue weighting, banking depth, or a discriminative not generative score).")
    print("=" * 96)


if __name__ == "__main__":
    main()
