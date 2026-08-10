"""SHARPEN LARGE VOCAB — stack the levers: 16kHz ear + positional cues (now that the onset is IN the signal).

At 8kHz the positional onset/nucleus/coda cues gave only +2-3pt because the onset detail was low-passed away.
With the 16kHz ear restoring the 4-8kHz fricative band, the onset is NOW in the signal -- so the positional
cues should finally bite. Measures, all at 16kHz, cross-speaker LOSO + WCCN: full cues vs full + positional,
on the onset-confusable CVC vocab + realistic. The cumulative picture vs the 8kHz/curated starting point.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_hifi_combo
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
from domains.speech_world import _resample
from scripts.jabberwock_largevocab_diag import WORDS, SPEAKERS, RENDS, set_active
from scripts.jabberwock_positional_cues import CVC, evaluate, positional_cues
from scripts.jabberwock_hifi_ear import synth_native

HIFI = 16000


def main():
    print("=" * 96)
    print("STACK — 16kHz ear + positional cues (onset now in-band); how high does large-vocab top-1 go?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    FE.install_curated_frontend(s)
    fe = next(n for n in s.nodes("FrontEnd"))
    allnames = [s.node(c)["attrs"].get("name") for et in ("has_cue", "repertoire") for c in s.neighbours(fe, et)]
    set_active(s, fe, allnames)
    n_full = len(allnames)
    full = list(range(n_full))
    pos = list(range(n_full, n_full + 3))

    vocab = sorted(set(CVC) | set(WORDS))
    print(f"  synth native -> 16kHz, full({n_full}) + positional(3) cues for {len(vocab)} words...", flush=True)
    feats = {}
    for v in SPEAKERS:
        for w in vocab:
            for r in range(RENDS):
                got = synth_native(w, {"variant": v, "pitch": 50, "rate": 175})
                if got is not None:
                    x = _resample(got[0], got[1], HIFI)
                    x = np.asarray(x, dtype=np.float64)
                    feats[(v, w, r)] = FE.feature_channels(s, x, HIFI) + positional_cues(x, HIFI)

    print(f"\n  {'vocab':<26}{'config':>22}{'top-1':>9}{'recall':>9}")
    out = {}
    for label, words in (("CVC onset-confusable", CVC), ("realistic mixed", WORDS)):
        f1, fk = evaluate(feats, words, full)
        p1, pk = evaluate(feats, words, full + pos)
        out[label] = (f1, p1)
        print(f"  {label:<26}{'16kHz full':>22}{f1*100:>8.0f}%{fk*100:>8.0f}%")
        print(f"  {label:<26}{'16kHz full+positional':>22}{p1*100:>8.0f}%{pk*100:>8.0f}%  ({(p1-f1)*100:+.0f}pt)")

    print("\n" + "=" * 96)
    print("  CUMULATIVE (realistic 64-word, cross-speaker top-1):  8kHz/curated 36%  ->  16kHz/full "
          f"{out['realistic mixed'][0]*100:.0f}%  ->  +positional {out['realistic mixed'][1]*100:.0f}%")
    dp = out["CVC onset-confusable"][1] - out["CVC onset-confusable"][0]
    if dp > 0.03:
        print(f"  POSITIONAL NOW BITES at 16kHz (CVC {dp*100:+.0f}pt): the onset cues separate rhyming words once the")
        print("  fricative band exists -- the two levers compound. Ship both: 16kHz ear + the 3 positional cues.")
    else:
        print(f"  positional still flat at 16kHz (CVC {dp*100:+.0f}pt) -- the 16kHz ear already routes the fricative")
        print("  band into the existing cues; the EAR is the lever, the positional split is redundant. Ship 16kHz alone.")
    print("=" * 96)


if __name__ == "__main__":
    main()
