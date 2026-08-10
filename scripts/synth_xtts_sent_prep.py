"""XTTS SENTENCE pipeline, step 1/3 — PREP: clone target X, synth X's HELD-OUT SENTENCES (XTTS's strength, natural speech).

Single-word XTTS degraded the speaker conditioning (44% WavLM, cos 0.26 vs 0.714 within). Natural sentences are what XTTS
clones well + give stable speaker embeddings. Saves: reference.wav, the held-out sentence TEXTS to synth, enrollment wavs for
the target X centroid + within-band, and per control speaker enrollment wavs for the between-speaker control.
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

OUT = os.environ.get("XTTS_SENT", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_sent")
N_REF = 4         # reference utterances (cloning conditioning)
N_SYNTH = 12      # held-out sentences to synthesise
N_ENROLL = 6      # X enrollment sentences (centroid + within)


def main():
    os.makedirs(OUT, exist_ok=True)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk)
    target = spks[-1]; others = spks[:-1][-6:]
    utt = by_spk[target]

    # reference (held out from everything tested)
    ref = np.concatenate([np.asarray(load_flac(f)[0], np.float32) for (f, t) in utt[:N_REF]])[: 16 * 16000]
    sf.write(os.path.join(OUT, "reference.wav"), ref, 16000)

    man = {"target": target, "reference": "reference.wav", "synth": [], "enrollX": [], "enrollY": {}}
    # held-out sentences to synthesise (their text) + the real recording (for same-sentence FFT)
    for i, (f, t) in enumerate(utt[N_REF:N_REF + N_SYNTH]):
        x = np.asarray(load_flac(f)[0], np.float32)
        p = f"realX_sent{i}.wav"; sf.write(os.path.join(OUT, p), x, 16000)
        man["synth"].append({"id": i, "text": t, "realX": p})
    # X enrollment (centroid + within band)
    for i, (f, t) in enumerate(utt[N_REF + N_SYNTH:N_REF + N_SYNTH + N_ENROLL]):
        x = np.asarray(load_flac(f)[0], np.float32)
        p = f"enrollX_{i}.wav"; sf.write(os.path.join(OUT, p), x, 16000); man["enrollX"].append(p)
    # control speakers enrollment
    for sp in others:
        man["enrollY"][sp] = []
        for i, (f, t) in enumerate(by_spk[sp][:N_ENROLL]):
            x = np.asarray(load_flac(f)[0], np.float32)
            p = f"enrollY_{sp}_{i}.wav"; sf.write(os.path.join(OUT, p), x, 16000); man["enrollY"][sp].append(p)

    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(man, fh, indent=1)
    print(f"  PREP done: target {target}; ref {len(ref)/16000:.0f}s; {len(man['synth'])} held-out sentences to synth; "
          f"{len(man['enrollX'])} X-enroll; {len(others)} control speakers -> {OUT}")
    print(f"  sample sentence: \"{man['synth'][0]['text'][:70]}...\"")


if __name__ == "__main__":
    main()
