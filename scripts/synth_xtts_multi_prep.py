"""XTTS multi-speaker test — PREP: clean single-utterance references + enrollment for several target speakers.

Decisive diagnostic: does XTTS-v2 clone SOME LibriSpeech speakers well (then 8842 was hard / my concatenated ref), or does
it systematically underperform? Each speaker gets a clean longest-single-utterance reference (~8-15s) + enrollment sentences
for its WavLM centroid. The gen step clones a fixed sentence pool per speaker; compare builds the verification matrix.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import soundfile as sf

from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV

OUT = os.environ.get("XTTS_MULTI", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_multi")
N_SPK = 6
N_ENROLL = 4
SENTS = [
    "the morning sun rose over the quiet village by the river",
    "he opened the heavy door and stepped into the silent hall",
    "she could hardly believe what the stranger had just told her",
]


def main():
    os.makedirs(OUT, exist_ok=True)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk)[-N_SPK:]

    man = {"sentences": SENTS, "speakers": {}}
    for sp in spks:
        utt = by_spk[sp]
        # reference = longest single utterance (clean, no concatenation)
        durs = []
        for (f, t) in utt[:12]:
            x = np.asarray(load_flac(f)[0], np.float32); durs.append((len(x), f, x))
        durs.sort(key=lambda z: -z[0])
        refx = durs[0][2][: 15 * 16000]
        rp = f"ref_{sp}.wav"; sf.write(os.path.join(OUT, rp), refx, 16000)
        enroll = []
        for j, (n, f, x) in enumerate(durs[1:1 + N_ENROLL]):
            p = f"enroll_{sp}_{j}.wav"; sf.write(os.path.join(OUT, p), x, 16000); enroll.append(p)
        man["speakers"][sp] = {"reference": rp, "enroll": enroll}
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    print(f"  PREP done: {len(spks)} speakers {spks}; clean single-utt references + {N_ENROLL} enroll each -> {OUT}")


if __name__ == "__main__":
    main()
