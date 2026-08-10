"""XTTS pipeline, step 1/3 — PREP (main venv): target speaker reference + held-out words + real comparison wavs.

Saves to the scratchpad: reference.wav (target X's voice, held out from the test words), per held-out word the real X
segment + control speakers' real segments, and a manifest the XPU-venv gen step reads. Held-out words are spoken by X AND
>=1 control speaker (for the cross-speaker FFT control).
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

from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

OUT = os.environ.get("XTTS_DATA", "/tmp/claude-1000/-home-matt-ozma-internal-research-experiments-gamma-substrate/"
                     "c0315161-a04e-4a46-9c86-b2c94e589dbb/scratchpad/xtts_data")
N_WORDS = 25
N_REF_UTT = 4


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

    # reference = first N_REF_UTT utterances of the target (held out from the test words)
    ref = []
    for (f, t) in by_spk[target][:N_REF_UTT]:
        x, fs = load_flac(f); ref.append(np.asarray(x, np.float32))
    ref = np.concatenate(ref)[: 14 * 16000]
    sf.write(os.path.join(OUT, "reference.wav"), ref, 16000)

    def words_of(pairs):
        out = defaultdict(list)
        for (f, t) in pairs:
            x, fs = load_flac(f); x = np.asarray(x, np.float32)
            try:
                for (w, t0, t1) in align_utt(x, fs, t):
                    if len(w) >= MINW and (t1 - t0) >= 0.18:
                        out[w].append(x[int(t0 * fs):int(t1 * fs)])
            except Exception:
                pass
        return out

    Xw = words_of(by_spk[target][N_REF_UTT:])           # held-out words (NOT the reference utterances)
    oth = {sp: words_of(by_spk[sp][:40]) for sp in others}
    held = [w for w in Xw if any(w in oth[sp] for sp in others)][:N_WORDS]

    manifest = {"target": target, "reference": "reference.wav", "words": []}
    for w in held:
        inst = sorted(Xw[w], key=len)
        sf.write(os.path.join(OUT, f"realX_{w}.wav"), inst[-1], 16000)
        entry = {"word": w, "realX": f"realX_{w}.wav", "realY": []}
        if len(inst) >= 2:                                       # 2nd real-X instance = the within-speaker reference
            sf.write(os.path.join(OUT, f"realX2_{w}.wav"), inst[-2], 16000)
            entry["realX2"] = f"realX2_{w}.wav"
        for sp in others:
            if w in oth[sp]:
                ry = max(oth[sp][w], key=len)
                p = f"realY_{sp}_{w}.wav"; sf.write(os.path.join(OUT, p), ry, 16000); entry["realY"].append(p)
        manifest["words"].append(entry)

    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"  PREP done: target {target}; reference {len(ref)/16000:.1f}s; {len(held)} held-out words; -> {OUT}")
    print(f"  words: {[m['word'] for m in manifest['words']]}")


if __name__ == "__main__":
    main()
