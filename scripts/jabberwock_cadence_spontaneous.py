"""SPONTANEOUS-SPEECH TRANSFER — does the cadence predictor carry to UNSCRIPTED speech? (the last regime).

The arc so far: SONG (nursery refrains) -> READ (LibriSpeech) showed the repetition-free predictors (AR local
dynamics, held cross-speaker library) transfer where the repetition-hungry recall halves. The open rung was
SPONTANEOUS speech -- conversational, disfluent, irregular timing, the hardest case -- which had no corpus on disk.
This uses the AMI Meeting Corpus headset audio (/home/matt/data/ami): each close-talking headset is ONE speaker,
genuinely unscripted meeting speech. The test:
  (1) Do the predictors beat persistence + shuffled on spontaneous contours at all (does cadence survive disfluency)?
  (2) Does the READ-built held library read a SPONTANEOUS speaker -- cross-DOMAIN (read->spontaneous) and
      cross-SPEAKER (the AMI speakers are not in the library)? That is the universal-cadence claim at its hardest.

Same predictors + metric as the library experiment, evaluated on the second half of each spontaneous contour.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_cadence_spontaneous
"""
from __future__ import annotations

import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from domains.cadence_library import CadenceLibrary
from scripts.jabberwock_ear_ignition import load, FS
from scripts.jabberwock_cadence_predictor import contour_from_audio
from scripts.jabberwock_cadence_library import errors, shuffled_persist, LIB_PATH, MAXLEN

AMI = "/home/matt/data/ami"
SECS = 900         # cap audio per speaker before VAD (meeting headsets are ~20 min)


def rms_norm(x, target=0.08):
    """Meeting headsets are quiet (peak-norm leaves speech near the floor) -- bring RMS up so onsets fire."""
    return np.clip(x * (target / (np.sqrt(np.mean(x ** 2)) + 1e-9)), -1.0, 1.0)


def vad_concat(x, frame=0.025, k=3.0, hang=0.20):
    """Energy VAD: keep speech-active frames, drop the long inter-turn silences -> a CONTINUOUS spontaneous
    stream per speaker (the AMI analogue of concatenating LibriSpeech utterances). Mechanical I/O."""
    fl = int(frame * FS)
    n = len(x) // fl
    fr = x[:n * fl].reshape(n, fl)
    e = np.sqrt((fr ** 2).mean(1))
    med = np.median(e) + 1e-9
    act = e > k * med
    hb = int(hang / frame)
    keep = np.zeros(n, bool)
    last = -10 ** 9
    for i in range(n):
        if act[i]:
            last = i
        if i - last <= hb:
            keep[i] = True
    return fr[keep].reshape(-1)


def spontaneous_contours():
    """One contour per AMI headset = one spontaneous speaker stream (close-talking mic, VAD'd to active speech)."""
    out = []
    for f in sorted(glob.glob(os.path.join(AMI, "*.wav"))):
        v = vad_concat(rms_norm(load(f)[:int(SECS * FS)]))
        c = contour_from_audio(v)
        if c is not None and len(c) >= 40:
            out.append((os.path.basename(f).replace(".wav", ""), c[:MAXLEN]))
    return out


def main():
    print("=" * 104)
    print("SPONTANEOUS-SPEECH TRANSFER — AMI meeting headsets; does cadence survive unscripted speech?")
    print("=" * 104)
    if not os.path.exists(LIB_PATH):
        print(f"  no held library at {LIB_PATH} -- run scripts.jabberwock_cadence_library --rebuild first."); return
    lib = CadenceLibrary.load(LIB_PATH)
    contours = spontaneous_contours()
    if not contours:
        print(f"  no AMI wavs in {AMI} -- still downloading?"); return
    print(f"  held library: {len(lib)} arcs (READ speakers); {len(contours)} SPONTANEOUS speakers from AMI "
          f"(NONE in the library)\n")

    rows = []
    for label, c in contours:
        e = errors(c, lib); sh = shuffled_persist(c)
        rows.append((e, sh))
        sk = lambda key: max(0.0, (sh - e[key]) / max(sh, 1e-9) * 100)
        print(f"    {label:22} ({len(c):3d} onsets)  persist {e['persist']:.3f} | same_recall {sk('same_recall'):+.0f}% "
              f" ar {sk('ar'):+.0f}%  held_library {sk('held_library'):+.0f}%  fused {sk('fused'):+.0f}%")

    agg = {k: float(np.mean([max(0.0, (sh - e[k]) / max(sh, 1e-9) * 100) for (e, sh) in rows]))
           for k in ("same_recall", "ar", "held_library", "fused")}
    print("\n" + "=" * 104)
    print("  MEAN prediction skill over chance on SPONTANEOUS speech (cadence-beats-shuffle %):")
    for k in ("same_recall", "ar", "held_library", "fused"):
        print(f"    {k:14} {agg[k]:+.0f}%")
    print("  (for reference, on READ held-out speakers it was: same_recall +4%, ar +30%, held_library +30%, fused +31%)")
    print("\n" + "=" * 104)
    sr, ar, hl = agg["same_recall"], agg["ar"], agg["held_library"]
    if ar > 8 and hl > 8 and hl > sr + 5:
        print(f"  CADENCE TRANSFERS TO SPONTANEOUS SPEECH: on unscripted meeting speech the repetition-free predictors")
        print(f"  hold -- AR (stream dynamics) {ar:+.0f}% and the READ-built held library {hl:+.0f}% both well above the")
        print(f"  repetition-hungry recall ({sr:+.0f}%). The held library reads a spontaneous speaker cross-DOMAIN")
        print("  (read->spontaneous) and cross-SPEAKER -- a universal cadence survives disfluency. The arc lands:")
        print("  song -> read -> spontaneous, the repetition-free cadence carries all the way.")
    elif ar > 8 or hl > 8:
        print(f"  CADENCE PARTLY TRANSFERS: on spontaneous speech AR {ar:+.0f}% / held_library {hl:+.0f}% beat chance but")
        print(f"  weaker than on read (+30%) -- disfluency/irregular timing erodes the predictable contour. Recall {sr:+.0f}%.")
        print("  Honest: the shape is still there in spontaneous speech but fainter; the predictors read it less well.")
    else:
        print(f"  CADENCE DOES NOT TRANSFER TO SPONTANEOUS SPEECH (ar {ar:+.0f}%, held_library {hl:+.0f}%): unscripted")
        print("  timing is too irregular for the contour to be predictable beyond chance. Honest negative -- the")
        print("  repetition-free cadence was a read/song property; spontaneous speech needs a richer model.")
    print("=" * 104)


if __name__ == "__main__":
    main()
