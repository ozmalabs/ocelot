"""omniglot_world — the WORLD ADAPTER for REAL online handwriting (Omniglot stroke data).

Scales the motor analysis-by-synthesis writing recogniser (domains/glyph_motor_world +
domains/recognition_graph.predict_synth_term) from synthetic stroke programs to REAL human pen
trajectories: the Omniglot dataset (Lake, Salakhutdinov & Tenenbaum 2015), 1623 characters across
50 alphabets, each drawn by 20 people as ONLINE strokes (sequences of pen points). The strokes ARE
the agent's "how to write", recorded from real hands.

This file is ONLY a world adapter: it locates the data on disk, parses a drawing's motor file into
a pen trajectory, and hands it to the SAME graph recogniser. No decisions, no agent state.

Motor file format (strokes_{background,evaluation}/<alphabet>/<character>/<charid>_<drawer>.txt):
  START                 begins the drawing
  x,y,t                 one pen sample (we use x,y)
  BREAK                 ends a stroke (pen lift)
We collect all samples in pen order (inter-stroke lifts kept as straight segments, as the synthetic
pen does) and resample/normalise via glyph_motor_world.to_trajectory.

Data: downloaded once into the gitignored dataset dir ($OMNIGLOT_DIR, default
<repo>/data/omniglot) -- strokes_background.zip / strokes_evaluation.zip from
https://github.com/brendenlake/omniglot. On-disk, deterministic, no network at run time.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np

from domains import glyph_motor_world as gm
from domains.dataset_root import dataset_dir

DATA = os.environ.get("OMNIGLOT_DIR", dataset_dir("omniglot"))


def split_dir(split: str = "evaluation") -> str:
    return os.path.join(DATA, f"strokes_{split}")


def alphabets(split: str = "evaluation") -> list[str]:
    d = split_dir(split)
    if not os.path.isdir(d):
        return []
    return sorted(a for a in os.listdir(d) if os.path.isdir(os.path.join(d, a)))


def characters(alphabet: str, split: str = "evaluation") -> list[str]:
    """Character directory paths within an alphabet (each holds 20 drawings)."""
    ad = os.path.join(split_dir(split), alphabet)
    return sorted(os.path.join(ad, c) for c in os.listdir(ad)
                  if os.path.isdir(os.path.join(ad, c)))


def drawings(char_dir: str) -> list[str]:
    """The 20 drawing files for a character (one per drawer), sorted by drawer index."""
    return sorted(os.path.join(char_dir, f) for f in os.listdir(char_dir)
                  if f.endswith(".txt"))


def load_points(path: str) -> np.ndarray:
    """Parse a motor file -> (m, 2) array of pen samples in pen order (START/BREAK dropped;
    inter-stroke pen-lifts kept implicitly as the gap between consecutive samples)."""
    pts = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line in ("START", "BREAK"):
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                pts.append((float(parts[0]), float(parts[1])))
    return np.asarray(pts, dtype=float) if pts else np.zeros((0, 2))


def _is_degenerate_stroke(xy: np.ndarray) -> bool:
    """RUN 37C -- ingest-hygiene criterion, PRE-REGISTERED here (the gate script cites this
    docstring verbatim): a stroke is DEGENERATE iff it is a single recorded sample (m==1 --
    no motion is even representable) OR every recorded sample sits at the exact same (x, y)
    (m>=2 but zero arc length -- the pointer never moved between BREAKs, a stray click/drag-
    noop in the raw mouse trace, not a drawn mark). This is NOT a size threshold: a short-but-
    real stroke that moves even one sub-pixel (a dot, a tick -- genuine glyph elements in
    several alphabets) has nonzero arc length and is NOT degenerate -- it MUST survive.
    `xy` is the (m, 2) point array (any time column already stripped by the caller)."""
    if xy.shape[0] <= 1:
        return True
    d = np.diff(xy, axis=0)
    return bool(np.sqrt((d ** 2).sum(axis=1)).sum() == 0.0)


def load_strokes(path: str, *, drop_degenerate: bool = False) -> list[np.ndarray]:
    """Parse a motor file -> list of (m_i, 2) per-stroke point arrays (split on BREAK).

    RUN 37C (`drop_degenerate=False` default -- every pre-existing caller reproduces
    byte-identical output): when True, DEGENERATE strokes (`_is_degenerate_stroke` --
    single-point, or zero arc length across >=2 points) are dropped from the returned list.
    Ingest-hygiene fix for a real artifact in the raw Omniglot mouse traces (stray single-
    point 'strokes', Keble/Kannada -- run 36, commit 5aa6bcb6) that a downstream per-stroke
    matcher can latch onto as the 'distinguishing' element between two candidates."""
    strokes, cur = [], []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line == "START":
                continue
            if line == "BREAK":
                if len(cur) >= 1:
                    strokes.append(np.asarray(cur, dtype=float))
                cur = []
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                cur.append((float(parts[0]), float(parts[1])))
    if len(cur) >= 1:
        strokes.append(np.asarray(cur, dtype=float))
    out = [s for s in strokes if s.shape[0] >= 1]
    if drop_degenerate:
        out = [s for s in out if not _is_degenerate_stroke(s)]
    return out


def _synthetic_arclen_time(xy: np.ndarray) -> np.ndarray:
    """Fallback clock for a stroke whose own recorded timestamps are unusable: arc-length-
    proportional 'time' (the SAME constant-speed assumption every pre-existing caller of this
    file already made when it silently dropped the t column). Mechanical geometry, not a
    decision — used only to give a bad stroke SOME monotone t so downstream dt-based code
    never divides by a negative or zero span."""
    if xy.shape[0] < 2:
        return np.zeros(xy.shape[0])
    d = np.sqrt(((np.diff(xy, axis=0)) ** 2).sum(axis=1))
    return np.concatenate([[0.0], np.cumsum(d)])


def load_strokes_t(path: str, *, drop_degenerate: bool = False
                    ) -> tuple[list[np.ndarray], list[bool]]:
    """RUN 33 -- parse a motor file -> (strokes_xyt, fallback_flags): like `load_strokes` (same
    BREAK-splitting convention, same point filter) but KEEPS the third column (millisecond pen-
    sample timestamp, `domains/omniglot_world.py`'s own module docstring format note) instead of
    silently dropping it. `strokes_xyt[i][:, :2]` is byte-identical to `load_strokes(path)[i]`.

    Guard (pre-registered): a stroke whose recorded t is MISSING (a malformed/short line — real
    Omniglot files always carry 3 columns per sample, but this stays honest against a truncated
    file) or NON-MONOTONE (`np.diff(t) < 0` anywhere -- real sample-clock glitches, ~1% of files
    in a 200-file audit) gets its whole stroke's t REPLACED by `_synthetic_arclen_time` (the
    pre-existing constant-speed assumption every OLD caller made, now applied only to the one
    bad stroke) and `fallback_flags[i] = True` -- callers COUNT this (the >5% data-quality wall
    the run-33 falsifier reports on), never silently absorb it.

    RUN 37C (`drop_degenerate=False` default -- every pre-existing caller reproduces byte-
    identical output): when True, strokes DEGENERATE per `_is_degenerate_stroke` (checked on
    the xy columns only, ignoring t) are dropped from both `strokes_xyt` and `fallback_flags`
    (kept aligned by index) -- the SAME ingest-hygiene criterion `load_strokes` applies."""
    strokes, cur = [], []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line == "START":
                continue
            if line == "BREAK":
                if len(cur) >= 1:
                    strokes.append(np.asarray(cur, dtype=float))
                cur = []
                continue
            parts = line.split(",")
            if len(parts) >= 3:
                cur.append((float(parts[0]), float(parts[1]), float(parts[2])))
            elif len(parts) >= 2:
                cur.append((float(parts[0]), float(parts[1]), float("nan")))
    if len(cur) >= 1:
        strokes.append(np.asarray(cur, dtype=float))
    strokes = [s for s in strokes if s.shape[0] >= 1]

    out, fallback = [], []
    for s in strokes:
        xy = s[:, :2]
        t = s[:, 2] if s.shape[1] >= 3 else np.full(s.shape[0], np.nan)
        used_fallback = bool(s.shape[0] < 2 or np.any(np.isnan(t)) or np.any(np.diff(t) < 0.0))
        if used_fallback:
            t = _synthetic_arclen_time(xy)
        out.append(np.concatenate([xy, t[:, None]], axis=1))
        fallback.append(used_fallback)
    if drop_degenerate:
        keep = [i for i, s in enumerate(out) if not _is_degenerate_stroke(s[:, :2])]
        out = [out[i] for i in keep]
        fallback = [fallback[i] for i in keep]
    return out, fallback


def trajectory(path: str, n: int = gm.N_POINTS, per_stroke: bool = False, *,
                denoise: bool = False, denoise_kwargs: Optional[dict] = None,
                drop_degenerate: bool = False) -> np.ndarray:
    """One drawing -> a normalized (n x 2) pen trajectory for the AbS recogniser. Boundary I/O.
    per_stroke=True conditions each stroke on its own length (drops the inter-stroke jump geometry).

    RUN 34 (`denoise=False` default, byte-identical otherwise): forwarded mechanically to
    `glyph_motor_world.to_trajectory[_strokes]` — see that module for the mouse observation
    model's inverse (latent-path reconstruction) this opts into.

    RUN 37C (`drop_degenerate=False` default, byte-identical otherwise): forwarded to
    `load_strokes` in the `per_stroke=True` branch only -- the `per_stroke=False` branch reads
    raw, unsplit points via `load_points` and has no stroke boundaries to filter."""
    if per_stroke:
        return gm.to_trajectory_strokes(load_strokes(path, drop_degenerate=drop_degenerate), n,
                                         denoise=denoise, denoise_kwargs=denoise_kwargs)
    return gm.to_trajectory(load_points(path), n, denoise=denoise, denoise_kwargs=denoise_kwargs)


def strokes_normalized(path: str, per_stroke: int = 12) -> list[np.ndarray]:
    """Parse a drawing into its strokes, JOINTLY normalise the whole figure (one centroid + RMS
    over ALL points), and resample each stroke to ~`per_stroke` points by arc length. Returns the
    list of per-stroke (k_i x 2) point sets in the SHARED normalised frame — so a stroke's position
    is part of its point set and the part match respects stroke LAYOUT (relations). Boundary I/O."""
    strokes = [s[:, :2] for s in load_strokes(path) if s.shape[0] >= 1]
    if not strokes:
        return []
    allp = np.concatenate(strokes, axis=0)
    c = allp.mean(axis=0, keepdims=True)
    rms = float(np.sqrt(((allp - c) ** 2).sum(axis=1).mean()))
    rms = rms if rms > 1e-9 else 1.0
    out = []
    for s in strokes:
        s = (s - c) / rms
        if s.shape[0] >= 2:
            s = gm._resample_arclen(s, per_stroke)
        else:
            s = np.repeat(s, per_stroke, axis=0)
        out.append(s)
    return out


def install_drawing_parts(sub, path: str, name: str, *, is_word: float = 0.0,
                          per_stroke: int = 12) -> int:
    """Install a drawing as a node with its STROKE PARTS in the graph: node --has_stroke-->
    Stroke{stroke_pts}, jointly normalised. This is the hierarchical (part-composed) form the
    agent's part-nested recogniser reads. Mechanical graph construction; no decision."""
    node = sub.add_node("Concept", {"name": name, "is_word": float(is_word)})
    for ss in strokes_normalized(path, per_stroke):
        st = sub.add_node("Stroke", {"stroke_pts": ss.tolist()})
        sub.add_edge_unchecked(node, "has_stroke", st)
    return node


def have_data(split: str = "evaluation") -> bool:
    return len(alphabets(split)) > 0


__all__ = ["DATA", "split_dir", "alphabets", "characters", "drawings",
           "load_points", "load_strokes", "load_strokes_t", "trajectory", "have_data"]
