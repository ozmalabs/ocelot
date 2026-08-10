"""CLEAN 16 kHz isolated-digit corpus selector — the re-grounding corpus.

The 8 kHz FSDD runs DELETED the frication band (4-8 kHz): half the sonority
evidence (unvoiced obstruents /s/ /f/) thrown away before the agent saw it
(memory ozma_train_on_clean_test_on_degraded). This module hands the SAME
isolated single-digit task back to the curriculum on FULL 16 kHz audio — the
Google Speech Commands digits (zero..nine), native 16 kHz, real speakers, NOT
downsampled. The whole point is the INTACT frication band.

World-adapter I/O only (mechanical bytes -> array). No agent code, no decisions.
A fixed deterministic speaker/token selection (top speakers by digit coverage,
capped per digit/speaker for balance) so the cross-speaker coherence test is
meaningful and the run is reproducible.
"""
from __future__ import annotations

import os
import wave
from collections import defaultdict

import numpy as np

SC_DIR = "/tmp/sc"
DIGITS = ["zero", "one", "two", "three", "four", "five",
          "six", "seven", "eight", "nine"]
FS = 16000                       # native Speech Commands rate — NOT downsampled

N_SPEAKERS = 30                  # multi-speaker (vs FSDD 6) — stronger invariance test
CAP_PER_DIGIT = 8                # tokens/digit/speaker, for class balance


def _speaker_of(fn: str) -> str:
    return fn.split("_nohash_")[0]


def select_corpus(n_speakers: int = N_SPEAKERS, cap: int = CAP_PER_DIGIT):
    """Deterministic clean-16k corpus: top `n_speakers` by full-digit coverage,
    `cap` tokens/digit/speaker. Returns a list of (path, digit, speaker, idx)."""
    cov = defaultdict(lambda: defaultdict(list))
    for di, d in enumerate(DIGITS):
        ddir = os.path.join(SC_DIR, d)
        if not os.path.isdir(ddir):
            continue
        for fn in sorted(os.listdir(ddir)):
            if not fn.endswith(".wav"):
                continue
            cov[_speaker_of(fn)][di].append(fn)
    ranked = []
    for sp, dc in cov.items():
        if all(len(dc.get(di, [])) >= 1 for di in range(10)):
            mn = min(len(dc[di]) for di in range(10))
            tot = sum(len(v) for v in dc.values())
            ranked.append((mn, tot, sp))
    ranked.sort(reverse=True)
    speakers = [sp for _, _, sp in ranked[:n_speakers]]

    out = []
    for sp in speakers:
        for di, d in enumerate(DIGITS):
            ddir = os.path.join(SC_DIR, d)
            for k, fn in enumerate(sorted(cov[sp][di])[:cap]):
                out.append((os.path.join(ddir, fn), di, sp, k))
    return out, speakers


def load_wav(path):
    """Mechanical bytes -> float array (peak-normalised), with native rate."""
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float64) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float64), fs


if __name__ == "__main__":
    files, speakers = select_corpus()
    rates = set()
    for p, *_ in files[:50]:
        with wave.open(p, "rb") as w:
            rates.add(w.getframerate())
    print(f"CLEAN 16 kHz corpus (Google Speech Commands digits, NOT downsampled)")
    print(f"  sample rates observed (first 50): {sorted(rates)}")
    print(f"  digit set : {DIGITS}")
    print(f"  speakers  : {len(speakers)}")
    print(f"  tokens    : {len(files)}")
    perdig = defaultdict(int)
    for _, di, _, _ in files:
        perdig[di] += 1
    print(f"  per digit : {{ " + ", ".join(f'{DIGITS[d]}:{perdig[d]}' for d in range(10)) + " }")
