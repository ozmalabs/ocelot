"""HOW HIGH DOES IT GO — coverage AND the agent's per-cue WCCN together, vs N.

The two findings compound: COVERAGE gives the speaker bank to estimate the key from; per-cue WCCN PROJECTS THE
KEY OUT of every cue. Map held-out recognition of UNSEEN speakers vs N banked speakers, PLAIN product vs WCCN
product, to the ceiling -- is cross-speaker isolated-word recognition essentially SOLVED with enough coverage +
the whitening? Real English speakers, scored against the known word, multiple renditions to damp VITS noise.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_wccn_curve
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

FS = 8000
WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
TRAIN_POOL = ["lessac", "amy", "alan", "joe", "alba", "hfc_female", "northern", "john",
              "kusal", "cori", "norman", "hfc_male", "sam", "bryce", "ljspeech", "danny"]   # 16
HELD = ["ryan", "jenny", "kristin", "kathleen"]
N_VALUES = [2, 4, 8, 16]
RENDS = 5            # bank 0-2, test 3-4


def main():
    print("=" * 96)
    print("WCCN COVERAGE CURVE — coverage + per-cue key-removal together; how high does cross-speaker go?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    print(f"  train pool {len(TRAIN_POOL)} | held-out UNSEEN {HELD} | {len(WORDS)} words | {RENDS} renditions")
    print("  synthesising + per-cue features...", flush=True)
    feats = {}
    for spk in TRAIN_POOL + HELD:
        for w in WORDS:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": spk, "pitch": 50, "rate": 175})
                if out is not None:
                    feats[(spk, w, r)] = SDW.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1])

    def banked_for(train):
        return [(w, feats[(spk, w, r)]) for spk in train for w in WORDS for r in (0, 1, 2) if (spk, w, r) in feats]

    def recall(train, project):
        bk = banked_for(train); cands = sorted({w for (w, _v) in bk})
        Ws = wccn.fit_per_cue(bk) if project else None
        accs = []
        for rend in (3, 4):
            hits = tot = 0
            for spk in HELD:
                for w in WORDS:
                    if (spk, w, rend) not in feats:
                        continue
                    g = wccn.recognise(feats[(spk, w, rend)], bk, Ws, cands)
                    tot += 1; hits += int(g == w)
            accs.append(hits / tot if tot else 0)
        return float(np.mean(accs))

    print(f"\n  held-out recall vs N (avg over 2 test renditions, chance {100/len(WORDS):.0f}%):")
    print(f"    {'N speakers':>11}{'PLAIN product':>16}{'+ per-cue WCCN':>16}")
    pl, pj = [], []
    for N in N_VALUES:
        p = recall(TRAIN_POOL[:N], False); q = recall(TRAIN_POOL[:N], True)
        pl.append(p); pj.append(q)
        print(f"    {N:>11}{p*100:>15.0f}%{q*100:>15.0f}%")

    print("\n" + "=" * 96)
    best = pj[-1]
    print(f"  CEILING (N={N_VALUES[-1]}): plain {pl[-1]*100:.0f}% | +WCCN {best*100:.0f}%  (coverage {pl[0]*100:.0f}->{pl[-1]*100:.0f}%, "
          f"WCCN adds +{(pj[-1]-pl[-1])*100:.0f}pt).")
    if best >= 0.85:
        print(f"  CROSS-SPEAKER ESSENTIALLY SOLVED: {best*100:.0f}% on UNSEEN speakers with coverage + the agent's key-removal.")
        print("  Isolated-word recognition across never-heard talkers is near human-level once the key is sampled + projected out.")
    elif best >= 0.7:
        print(f"  STRONG: {best*100:.0f}% on unseen speakers -- coverage + WCCN compound well; the residual gap to human-level")
        print("  is more speakers / renditions, or the connected-speech LANGUAGE PRIOR (the cipher's other half), not the key.")
    else:
        print(f"  {best*100:.0f}%: coverage + WCCN help but a ceiling remains -- the next lever is the plaintext prior or a sharper cue.")
    print("=" * 96)


if __name__ == "__main__":
    main()
