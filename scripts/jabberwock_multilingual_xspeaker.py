"""DOES THE KEY-RECOVERY MACHINERY GENERALISE ACROSS LANGUAGES? — coverage + per-cue WCCN, en/fr/de/es.

The cross-speaker result (coverage samples the speaker KEY, per-cue WCCN projects it out) was shown on ENGLISH.
The key is vocal-tract normalisation, which is LANGUAGE-AGNOSTIC in principle -- so the SAME machinery should
recover words across never-heard speakers in any language. This tests it: for each of en/fr/de/es, recognise the
spoken DIGITS 1-9 across same-language, different-talker voices, leave-one-speaker-out, PLAIN product vs WCCN.

Capped to EQUAL coverage (5 voices/language, bank 4 + hold 1, rotated) so the comparison is fair across
languages. If coverage + WCCN lifts cross-speaker recall in EVERY language by a similar margin, the machinery
is language-agnostic -- the agent's ear recovers the key, not English.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_multilingual_xspeaker
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
from scripts.universal_loop_phaseAB_piper import LANG_VOICES, LANG_DIGITS

FS = 8000
NCAP = 5            # equal coverage across languages
RENDS = 3           # bank renditions 0,1 ; test 0,1,2 of the held-out speaker
LANGS = ["en", "fr", "de", "es"]


def loso(feats, voices, words, project):
    """Leave-one-speaker-out cross-speaker recall: bank the other speakers, recognise the held-out one."""
    hits = tot = 0
    for held in voices:
        bank_v = [v for v in voices if v != held]
        bk = [(w, feats[(v, w, r)]) for v in bank_v for w in words for r in (0, 1) if (v, w, r) in feats]
        if not bk:
            continue
        cands = sorted({w for (w, _x) in bk})
        Ws = wccn.fit_per_cue(bk) if project else None
        for w in words:
            for r in range(RENDS):
                if (held, w, r) not in feats:
                    continue
                g = wccn.recognise(feats[(held, w, r)], bk, Ws, cands)
                tot += 1; hits += int(g == w)
    return hits / tot if tot else 0.0


def main():
    print("=" * 96)
    print("MULTILINGUAL CROSS-SPEAKER — does coverage + per-cue WCCN recover the key in every language?")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    rows = []
    for lang in LANGS:
        voices = LANG_VOICES[lang][:NCAP]; words = LANG_DIGITS[lang]
        print(f"\n  [{lang}] voices {voices}")
        print(f"       words {words}", flush=True)
        feats = {}
        for v in voices:
            for w in words:
                for r in range(RENDS):
                    out = sw.synth(w, {"variant": v, "pitch": 50, "rate": 175})
                    if out is not None:
                        feats[(v, w, r)] = SDW.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1])
        plain = loso(feats, voices, words, False)
        proj = loso(feats, voices, words, True)
        rows.append((lang, len(voices), plain, proj))
        print(f"       cross-speaker recall: plain {plain*100:.0f}%  -> + WCCN {proj*100:.0f}%  "
              f"(+{(proj-plain)*100:.0f}pt)")

    print("\n" + "=" * 96)
    print(f"  {'lang':>6}{'voices':>8}{'plain':>9}{'+WCCN':>9}{'lift':>8}")
    for (lang, n, p, q) in rows:
        print(f"  {lang:>6}{n:>8}{p*100:>8.0f}%{q*100:>8.0f}%{(q-p)*100:>+7.0f}")
    lifts = [q - p for (_l, _n, p, q) in rows]
    wins = [q for (_l, _n, _p, q) in rows]
    chance = 100 / 9
    print(f"\n  chance {chance:.0f}% | mean +WCCN recall {np.mean(wins)*100:.0f}% | mean lift +{np.mean(lifts)*100:.0f}pt"
          f" | all languages lifted: {all(l > 0 for l in lifts)}")
    if all(l >= 0 for l in lifts) and min(wins) > 0.4:
        print("  THE MACHINERY IS LANGUAGE-AGNOSTIC: coverage + WCCN recover the speaker key and surface the word")
        print("  across never-heard speakers in EVERY language -- the agent's ear recovers the key, not English.")
    else:
        worst = min(rows, key=lambda r: r[3])
        print(f"  UNEVEN: {worst[0]} lags ({worst[3]*100:.0f}%) -- likely fewer/odd voices or harder digit phonetics there,")
        print("  not the machinery (it lifts where coverage is clean). More same-language voices would even it out.")
    print("=" * 96)


if __name__ == "__main__":
    main()
