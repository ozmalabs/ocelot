"""HELD CADENCE LIBRARY ACROSS SPEAKERS — does recalling against OTHER speakers' arcs read a held-out speaker?

The AR predictor beat the repetition-dependence by fitting the test stream's own local dynamics. This is the OTHER
repetition-free route, the one mirroring "read OOV from held parts": bank a LIBRARY of cadence arcs from a set of
TRAINING speakers, then predict a HELD-OUT test speaker's cadence by recalling the nearest UNIVERSAL arc in the
library. Repetition-free by construction (the library is from other speakers; the test speaker is not in it) and
speaker-independent (z-normalised contours -> matching is on prosodic SHAPE, not absolute rate/pitch).

The test: on test speakers NOT in the library, does HELD-LIBRARY recall beat persistence + shuffled -- as well as
AR, and far better than SAME-STREAM recall (the repetition-hungry baseline)? If yes, a universal cross-speaker
cadence exists and transfers; the library reads a new speaker it never banked.

All predictors evaluated on the SECOND HALF of each test contour (fair: AR fits the first half). Library is built
once and cached to disk (the "held" library).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_cadence_library
"""
from __future__ import annotations

import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from domains.cadence_library import CadenceLibrary, W
from scripts.jabberwock_ear_ignition import FS
from scripts.jabberwock_cadence_predictor import contour_from_audio, ar_fit, P
from scripts.librispeech_wer import load_flac

DEV = "/home/matt/data/LibriSpeech/dev-clean"
LIB_PATH = "/home/matt/data/cadence_library.npz"
MAXLEN = 240
N_TRAIN = 6        # speakers banked into the library
N_TEST = 4         # held-out speakers (disjoint) the library must read
UTTS = 16
LIB_CAP = 1500     # cap bank size for a fast vectorised nearest-arc query
KNN = 20           # k nearest arcs averaged (denoise the single-arc follower)


def speaker_streams(spk_ids, utts=UTTS):
    """One concatenated contour per speaker (gaps between utts), same regime as the transfer test."""
    by_spk = {}
    for f in sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True)):
        by_spk.setdefault(os.path.basename(f).split("-")[0], []).append(f)
    out = []
    for sp in spk_ids:
        xs = []
        for f in by_spk.get(sp, [])[:utts]:
            try:
                x, _fs = load_flac(f)
            except Exception:
                continue
            xs.append(np.asarray(x, dtype=np.float64))
            xs.append(np.zeros(int(0.15 * FS)))
        if xs:
            c = contour_from_audio(np.concatenate(xs))
            if c is not None:
                out.append((sp, c[:MAXLEN]))
    return out


def all_speakers():
    ss = set()
    for f in glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True):
        ss.add(os.path.basename(f).split("-")[0])
    return sorted(ss)


def same_stream_recall(c, k, w=W):
    """Repetition-hungry baseline: nearest EARLIER window of THIS stream -> follower (euclidean, like the library)."""
    q = c[k - w + 1:k + 1].reshape(-1)
    best, bj = 1e18, None
    for j in range(w - 1, k):
        d = ((c[j - w + 1:j + 1].reshape(-1) - q) ** 2).sum()
        if d < best and j + 1 < len(c):
            best, bj = d, j
    return c[bj + 1] if bj is not None else c[k]


def errors(c, lib):
    n = len(c)
    start = max(W + 1, n // 2)
    ars = [ar_fit(c[:start, d], P) for d in range(3)]
    e = {"persist": [], "same_recall": [], "ar": [], "held_library": [], "fused": []}
    for k in range(start, n - 1):
        true = c[k + 1]
        e["persist"].append(np.abs(c[k] - true).mean())
        e["same_recall"].append(np.abs(same_stream_recall(c, k) - true).mean())
        ar_pred = np.array([np.dot(ars[d], c[k - P + 1:k + 1, d][::-1]) for d in range(3)])
        e["ar"].append(np.abs(ar_pred - true).mean())
        lib_pred = lib.predict_follower(c[k - W + 1:k + 1].reshape(-1), k=KNN)
        e["held_library"].append(np.abs(lib_pred - true).mean())
        # FUSE the speaker-adaptive AR with the universal library cue (combine-all)
        e["fused"].append(np.abs((0.65 * ar_pred + 0.35 * lib_pred) - true).mean())
    return {k: float(np.mean(v)) if v else 0.0 for k, v in e.items()}


def shuffled_persist(c):
    rng = np.random.RandomState(0)
    vals = []
    for _ in range(4):
        cs = c[rng.permutation(len(c))]
        n = len(cs); st = max(W + 1, n // 2)
        vals.append(np.mean([np.abs(cs[k] - cs[k + 1]).mean() for k in range(st, n - 1)]))
    return float(np.mean(vals))


def build_library(train_ids, rebuild=False):
    if os.path.exists(LIB_PATH) and not rebuild:
        lib = CadenceLibrary.load(LIB_PATH)
        print(f"  loaded held library: {len(lib)} arcs (cached {LIB_PATH})")
        return lib
    print(f"  banking library from {len(train_ids)} training speakers {train_ids} ...")
    lib = CadenceLibrary()
    lib.bank([c for _sp, c in speaker_streams(train_ids)])
    lib.subsample(LIB_CAP)
    lib.save(LIB_PATH)
    print(f"  banked {len(lib)} arcs -> {LIB_PATH}")
    return lib


def main():
    rebuild = "--rebuild" in sys.argv
    print("=" * 100)
    print("HELD CADENCE LIBRARY — predict a held-out speaker's cadence by recalling OTHER speakers' universal arcs")
    print("=" * 100)
    spk = all_speakers()
    train_ids, test_ids = spk[:N_TRAIN], spk[N_TRAIN:N_TRAIN + N_TEST]
    lib = build_library(train_ids, rebuild=rebuild)
    print(f"  held-out TEST speakers (NOT in library): {test_ids}\n")

    rows = []
    for sp, c in speaker_streams(test_ids):
        e = errors(c, lib); sh = shuffled_persist(c)
        rows.append((e, sh))
        sk = lambda key: max(0.0, (sh - e[key]) / max(sh, 1e-9) * 100)
        print(f"    spk {sp:6} ({len(c):3d} onsets)  persist {e['persist']:.3f} | same_recall {sk('same_recall'):+.0f}% "
              f" ar {sk('ar'):+.0f}%  held_library {sk('held_library'):+.0f}%  fused {sk('fused'):+.0f}%")

    agg = {k: float(np.mean([max(0.0, (sh - e[k]) / max(sh, 1e-9) * 100) for (e, sh) in rows]))
           for k in ("same_recall", "ar", "held_library", "fused")}
    print("\n" + "=" * 100)
    print("  prediction skill over chance on HELD-OUT speakers (mean cadence-beats-shuffle %):")
    for k in ("same_recall", "ar", "held_library", "fused"):
        print(f"    {k:14} {agg[k]:+.0f}%")
    print("\n" + "=" * 100)
    hl, sr, ar, fu = agg["held_library"], agg["same_recall"], agg["ar"], agg["fused"]
    if hl > 5 and hl > sr + 3 and fu > ar + 1:
        print(f"  UNIVERSAL CADENCE + IT COMPLEMENTS AR: the held library reads a held-out speaker ({hl:+.0f}%, above")
        print(f"  same-stream recall {sr:+.0f}%), and FUSING it with AR beats AR alone ({fu:+.0f}% > {ar:+.0f}%). The library")
        print("  carries cross-speaker shape AR's per-stream fit misses -- two repetition-free routes that ADD.")
    elif hl > 5 and hl > sr + 3:
        print(f"  THE HELD LIBRARY READS A NEW SPEAKER ({hl:+.0f}%, above same-stream recall {sr:+.0f}%) -- a universal")
        print(f"  cross-speaker cadence transfers. But AR ({ar:+.0f}%) is the stronger repetition-free route and fusing")
        print(f"  the library in does not beat it ({fu:+.0f}%): the universal cue is real but subsumed by the stream's own")
        print("  dynamics. Honest: the library proves universality; AR is what to predict with.")
    else:
        print(f"  THE HELD LIBRARY DOES NOT TRANSFER ({hl:+.0f}% on held-out speakers): cross-speaker arcs don't predict a")
        print(f"  new speaker's cadence beyond chance. The repetition-free win stays with AR ({ar:+.0f}%). Honest negative.")
    print("=" * 100)


if __name__ == "__main__":
    main()
