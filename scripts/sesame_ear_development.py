"""THE JABBERWOCK DEVELOPS ITS EAR ON REAL SPEECH — effect-gated discriminative cue growth.

CMVN didn't lift the real-speech ceiling: the bottleneck is the EAR (seed cochleagram/FFT/all-pole
can't discriminate real words). The agent's front end (domains/agent_frontend) carries a REPERTOIRE
of richer phonetic cues it can grow into — vtl_formant (vocal-tract-length speaker normalisation),
formant_relation, manner_voicing, landmark, f0_contour, cs_ear, ... This is the agent DEVELOPING
its ear: it lays each repertoire cue's labelled response over real Sesame words and the seeded
`keep_discriminative_cue` Rule KEEPS the cues that separate words better (graph-native discrimination,
the effect-gate is a Rule). Then we re-measure held-out recognition — did growing the ear help?

Streams Sesame once (reuses the cmvn-probe cache). Recogniser: 1-NN over the concatenation of the
agent's ACTIVE front-end cues (handles a growing cue set), bucketed by training frequency.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.sesame_ear_development [train_min]
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
import domains.agent_frontend as FE
import domains.feature_field as FF
from domains.filter_settings import cochleagram
from domains.self_directed_speech_world import _MIDDLE
from scripts.sesame_cmvn_probe import extract       # cached Sesame segment extractor

SEP = "=" * 88
FS = 8000


def _l2(v):
    v = np.asarray(v, dtype=np.float64).ravel()
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def feat(s, seg):
    """1-NN feature = concatenation of the agent's ACTIVE front-end cues (L2 per cue)."""
    chans = FE.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)
    return np.concatenate([_l2(c) for c in chans]) if chans else np.zeros(8)


def recall_by_freq(s, train, test):
    """Bank train (current ear), measure held-out in-vocab recall bucketed by training frequency."""
    bank = {}
    for (w, seg) in train:
        bank.setdefault(w, []).append(feat(s, seg))
    wcount = Counter(w for (w, _segs) in train)
    mats = {w: np.stack(v) for w, v in bank.items()}
    buckets = {"1": [0, 0], "2": [0, 0], "3-5": [0, 0], "6+": [0, 0]}

    def bk(c):
        return "1" if c == 1 else "2" if c == 2 else "3-5" if c <= 5 else "6+"
    c = t = 0
    for (w, seg) in test:
        if w not in mats:
            continue
        q = feat(s, seg)
        best, bw = -2.0, None
        for cw, M in mats.items():
            sim = float((M @ q).max() / (np.linalg.norm(q) + 1e-9))
            if sim > best:
                best, bw = sim, cw
        t += 1
        ok = bw == w
        c += int(ok)
        b = buckets[bk(wcount[w])]
        b[1] += 1; b[0] += int(ok)
    return (c / t if t else 0.0), buckets


def develop_ear(s, train):
    """The agent grows its ear: lay each repertoire cue's response over the frequent words, let the
    keep_discriminative_cue Rule select the cues that separate words better, gate them active."""
    fe = FE.install_frontend(s)
    addable = [c for c in s.neighbours(fe, "repertoire")
               if float(s.node(c)["attrs"].get("active", 0.0)) < 1.0]
    wcount = Counter(w for (w, _s) in train)
    frequent = [w for w, n in wcount.items() if n >= 6]
    _, env_cut, dur_cut, nf = _MIDDLE
    cue_feats = {}
    by_word = {}
    for (w, seg) in train:
        if w in frequent:
            by_word.setdefault(w, []).append(seg)
    for w, segs in by_word.items():
        for seg in segs[:8]:
            x = np.asarray(seg, dtype=np.float64)
            M = cochleagram(x, FS, env_cut, dur_cut, nf)
            resp = {}
            for c in addable:
                a = s.node(c)["attrs"]
                fn = FE.CUE_EXTRACTORS.get(a.get("extractor"))
                if fn is None:
                    continue
                try:
                    resp[c] = np.asarray(fn(x, FS, M, a), dtype=np.float64).ravel().tolist()
                except Exception:
                    pass
            cue_feats.setdefault(w, []).append(resp)
    kept = FF.select_cues(s, cue_feats)
    for c in kept:
        s.set_attr(c, "active", 1.0)
    return [s.node(c)["attrs"].get("name") for c in kept]


def main():
    train_min = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print(SEP)
    print("THE JABBERWOCK DEVELOPS ITS EAR ON REAL SPEECH — discriminative cue growth, effect-gated.")
    print(SEP)
    train, test = extract(train_min)
    print(f"  {len(train)} train tokens, {len(test)} test tokens\n")

    s = srs.Substrate()
    FE.install_frontend(s)
    base, bb = recall_by_freq(s, train, test)
    print(f"  baseline ear ({FE.n_active(s)} seed cues): in-vocab recall {base*100:.0f}%   "
          f"[6+x: {bb['6+'][0]}/{bb['6+'][1]}={bb['6+'][0]/max(bb['6+'][1],1)*100:.0f}%]\n")

    kept = develop_ear(s, train)
    print(f"  the agent DEVELOPED its ear — kept {len(kept)} discriminative cues: {kept}")
    dev, db = recall_by_freq(s, train, test)
    print(f"  developed ear ({FE.n_active(s)} cues): in-vocab recall {dev*100:.0f}%   "
          f"[6+x: {db['6+'][0]}/{db['6+'][1]}={db['6+'][0]/max(db['6+'][1],1)*100:.0f}%]")
    print(f"\n{SEP}")
    delta = (dev - base) * 100
    print(f"  ear development: recall {base*100:.0f}% -> {dev*100:.0f}% ({delta:+.0f}pt), "
          f"6+x bucket {bb['6+'][0]/max(bb['6+'][1],1)*100:.0f}% -> {db['6+'][0]/max(db['6+'][1],1)*100:.0f}%.")
    print(f"  {'The agent grew a more discriminative ear on real speech.' if delta > 1 else 'Cue growth did not crack it — the ceiling is deeper (metric learning / a trained model).'}")
    print(SEP)


if __name__ == "__main__":
    main()
