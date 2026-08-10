"""substroke_codebook — WORLD ADAPTER for the LEARNED sub-stroke primitive library (BPL's vocabulary).

The honest gap to BPL is a learned PER-PART model. BPL's core is a library of sub-stroke PRIMITIVES
learned from the background corpus, that characters are composed from. This adapter extracts sub-
stroke shape descriptors (mechanical perception — resample + normalise) and hands them to the RUST
learning primitive `kmeans` (the agent's library is learned in Rust, NOT Python — an earlier numpy
k-means was deleted for that reason). A character is then encoded as a soft BAG-OF-PRIMITIVES
histogram over the learned library (the Rust `bow_histogram` primitive) — a writer-invariant feature
the recognition DECISION fuses (graph Term) alongside the geometric cues.

This file does ONLY: resample sub-strokes to fixed-dim descriptors (mechanical), call the Rust
primitives, return their output. No clustering / decision logic here — that is the Rust primitive.
"""
from __future__ import annotations

import numpy as np

import substrate_rs._native as _N
from domains.glyph_motor_world import _resample_arclen
from domains import canonical_parse as cp
from domains import omniglot_world as ow

M = 8                       # points per sub-stroke descriptor (-> 2*M dim)


def substroke_descriptor(part, m: int = M) -> np.ndarray:
    """A canonical sub-stroke (k x 2) -> a position+scale-INVARIANT shape descriptor (re-centre to its
    own centroid, unit-RMS scale, arc-length resample to m, flatten -> 2*m). Mechanical perception."""
    p = np.asarray(part, dtype=float)[:, :2]
    if p.shape[0] < 2:
        return np.zeros(2 * m)
    p = p - p.mean(axis=0)
    s = float(np.sqrt((p ** 2).sum(axis=1).mean())) or 1.0
    return _resample_arclen(p / s, m).reshape(-1)


def descriptors_of(parts, m: int = M) -> np.ndarray:
    return (np.stack([substroke_descriptor(p, m) for p in parts])
            if parts else np.zeros((0, 2 * m)))


def learn_codebook(files, k: int = 64, m: int = M, theta: float = 70.0,
                   cap: int = 20000) -> np.ndarray:
    """Gather the canonical sub-strokes of the background drawings (mechanical) and LEARN the
    K-primitive library via the Rust `kmeans` primitive. Returns the (k x 2m) centroids."""
    descs = []
    for f in files:
        for part in cp.canonical_parts(ow.load_strokes(f), theta, per_part=12):
            descs.append(substroke_descriptor(part, m))
        if len(descs) >= cap:
            break
    X = np.asarray(descs[:cap], dtype=float)
    n, d = X.shape
    cent = _N.kmeans(X.reshape(-1).tolist(), int(n), int(d), int(k), 15)   # LEARNING in Rust
    return np.asarray(cent, dtype=float).reshape(k, d)


def bow(parts, cent: np.ndarray, m: int = M, beta: float = 8.0) -> np.ndarray:
    """A drawing's soft BAG-OF-PRIMITIVES histogram over the learned library (Rust `bow_histogram`),
    L2-normalised. Mechanical: extract descriptors, call the primitive."""
    k, d = cent.shape
    X = descriptors_of(parts, m)
    h = _N.bow_histogram(X.reshape(-1).tolist(), int(X.shape[0]), int(d),
                         cent.reshape(-1).tolist(), int(k), float(beta))
    return np.asarray(h, dtype=float)


def stroke_feature(part, cent: np.ndarray, m: int = M, beta: float = 8.0,
                   memw: float = 1.0) -> list:
    """A PER-PART learned feature that PRESERVES structure: the part's POSITION (centroid in the
    shared character frame — keeps layout) concatenated with its learned soft MEMBERSHIP over the
    primitive library (a continuous, writer-noise-suppressing shape encoding — same primitive across
    writers -> similar membership). The part match measures squared-Euclidean over this, so it keeps
    WHERE each part is AND uses the learned per-primitive tolerance. Mechanical (calls Rust bow)."""
    p = np.asarray(part, dtype=float)[:, :2]
    pos = p.mean(axis=0) if p.shape[0] else np.zeros(2)
    mem = bow([part], cent, m, beta)                      # K-dim soft membership of this sub-stroke
    return np.concatenate([pos, memw * mem]).tolist()


__all__ = ["substroke_descriptor", "learn_codebook", "bow", "stroke_feature", "M"]
