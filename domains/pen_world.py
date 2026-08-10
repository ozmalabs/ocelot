"""pen_world — RUN 47: the pen/touch WORLD ADAPTER, promoting run 46's one-off loaders
(`scripts/jabberwock_pendata_run46.py`) into a proper shared module per this run's own launch
brief ("a proper world adapter (promote run 46's loaders)"). RUN 48 adds a third corpus
(DigiLeTs — see below). Corpora:

  - UCI Character Trajectories (`.mat`, 200Hz Wacom pen, ONE writer, 20 single-stroke classes —
    see the UCI CAVEAT in run 46's own docstring, unchanged here): `mixout` is a `(1, N)` object
    array of `(3, T)` [x-velocity, y-velocity, pen-tip force] arrays; position is recovered by
    `pos = cumsum(vel_xy, axis=0) * dt` (verified sane in run 46's `unit_sanity` stage; the same
    check is re-asserted here by `tests/test_pen_world_migrated.py`).
  - QuickDraw raw ndjson (streaming per-category files under $PENDATA_DIR (default
    <repo>/data/pendata), mixed mouse+touch
    contributors): device-split via `domains.mouse_model.integer_delta_fraction`, pooled PER
    STROKE (never across a pen-up gap) then averaged over a drawing — `pooled_integer_delta_
    fraction`, moved here verbatim from run 46. `find_split_threshold` is run 46's own
    pre-registered bimodal-valley-or-fallback algorithm, unmodified.
  - DigiLeTs (`load_digilets_samples`, RUN 48): 200Hz Wacom pen, MANY writers (77 participants,
    62 classes [0-9, a-z, A-Z] x 5 instances each = 23,870 trajectories total — matches the
    published corpus size cited in `LITERATURE_POSITIONING.md`), the corpus purpose-built by
    Fabi/Otte/Butz to give Omniglot's mouse-drawn challenge a real cross-writer pen-native
    twin. Raw format (`data/raw/complete/<wid>-<gender>-<age>-<hand>_<ts>`, verified against
    the corpus's own `scripts/data.py::read_original_data`): 620 lines per participant file,
    interleaved data-line / one-hot-label-line pairs (`lines[::2]` = the 310 data lines, one
    per `symbol_index*5 + instance_index`, symbols in RECORDING order 0-9/a-z/A-Z); each data
    line is `x y pressure pen_down t` quintuples, space-separated, concatenated per point, NOT
    padded (unlike the corpus's own padded-to-250 numpy array format). `pen_down` marks a
    PEN-TOUCH-DOWN EVENT (1 at the first point of every stroke, 0 elsewhere) — verified directly
    against real multi-stroke letters ('x', 't', 'i', 'A' each show exactly two 1s, at stroke
    starts); `_split_digilets_strokes` splits on it. Per-point `t` is a SEMI-uniform relative
    timestamp (~20ms median dt on a real sample, but with rare multi-second outliers — sanity-
    checked, not assumed, per this module's own convention of never trusting raw-file dt
    blindly).

ARCHITECTURE (CLAUDE.md): this module does exactly two adapter things — INGEST (parse an
external file format into plain Python/numpy structures a caller then hands to `ink.ingest_ink`
etc.) and a THIN device classifier (`classify_device`, explicitly the kind of "opaque external
form -> smallest graph token" thin I/O-boundary classifier CLAUDE.md's own carve-out covers —
it converts a continuous sensor artifact into one of two device tokens, no graph-state
conditional, no agent decision). No rule engine, no agent state, no reasoning. Every non-trivial
decision downstream (codebook growth, quantization, one-shot verdicts) lives in the calling
run-47 script or the existing held Rust/graph machinery this module never touches directly.

Consistent with run 46's own CLAUDE.md self-check (restated here): this is pure numerical/
data-science research-corpus I/O over pre-built world-adapter-class feature extractors,
explicitly out of scope for the "no Python decisions" rule in the same way
`domains/adaptive_bins.py`/`domains/ink_dynamics.py`/`domains/mouse_model.py` already are —
measurement and format-translation code, never an agent's real-time choice about what to do
next. No `torch`, no borrowed model, anywhere in this module.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import numpy as np

from domains.dataset_root import dataset_dir
from domains.mouse_model import integer_delta_fraction

DATA_DIR = os.environ.get("PENDATA_DIR", dataset_dir("pendata"))
UCI_MAT_DEFAULT = os.path.join(DATA_DIR, "uci_chartraj", "mixoutALL_shifted.mat")

# The run-47 QuickDraw corpus (extended from run 46's original 6-category background sample):
# a mix of stroke-simple geometric shapes and complex multi-stroke objects, per this run's own
# launch brief ("mix of stroke-simple and complex"). Split into a LEARN/background subset (used
# ONLY to fit the codebook) and a HELD-OUT subset (no contact until Gate B), decided BEFORE any
# eval number is computed — stated here, not tuned after seeing results.
QD_CATEGORIES_BACKGROUND = ["circle", "square", "triangle", "line", "zigzag", "star",
                            "hexagon", "octagon", "diamond", "house"]
QD_CATEGORIES_HELDOUT = ["umbrella", "envelope", "key", "moon", "cloud", "fish", "apple",
                         "crown"]
QD_CATEGORIES = QD_CATEGORIES_BACKGROUND + QD_CATEGORIES_HELDOUT   # 18 total

QD_FILES = {c: os.path.join(DATA_DIR, f"{c}_sample.ndjson") for c in QD_CATEGORIES}


# ============================================================================================= #
#  UCI CHARACTER TRAJECTORIES — mechanical .mat parse.
# ============================================================================================= #
def load_uci_samples(mat_path: str = UCI_MAT_DEFAULT) -> list[dict]:
    """`mixout` (1, N) object array of (3, T) [xvel, yvel, force] -> per-sample dict with
    integrated position, real time (ms), raw velocity, and raw speed. Verbatim promotion of
    `jabberwock_pendata_run46.load_uci_samples` (format verified by that run's own
    `unit_sanity` stage; re-asserted by `tests/test_pen_world_migrated.py`)."""
    import scipy.io as sio
    d = sio.loadmat(mat_path)
    consts = d["consts"][0, 0]
    key = [str(k[0]) for k in consts["key"][0]]
    charlabels = consts["charlabels"][0]
    dt_s = float(consts["dt"][0, 0])
    mixout = d["mixout"]
    n = mixout.shape[1]
    out = []
    for idx in range(n):
        arr = np.asarray(mixout[0, idx], dtype=float)
        vel_xy = arr[:2, :].T
        force = arr[2, :]
        cls = key[int(charlabels[idx]) - 1]
        t_ms = np.arange(vel_xy.shape[0], dtype=float) * dt_s * 1000.0
        pos_xy = np.cumsum(vel_xy, axis=0) * dt_s
        speed = np.sqrt((vel_xy ** 2).sum(axis=1))
        out.append({"class": cls, "idx": idx, "pos_xy": pos_xy, "t_ms": t_ms,
                    "vel_xy": vel_xy, "speed": speed, "force": force, "dt_s": dt_s})
    return out


def uci_class_split(samples: list, *, train_frac: float = 0.6, seed: int = 20260706
                    ) -> tuple[list, list]:
    """PER-CLASS train/held-out split (mechanical shuffle-and-slice, seeded, no leakage): for
    each class, shuffle its own sample indices and take the first `train_frac` as LEARN, the
    rest as held-out. Returns (learn_samples, heldout_samples). A sample never appears in both
    lists (asserted by `tests/test_pen_world_migrated.py`)."""
    rng = np.random.default_rng(seed)
    by_class: dict[str, list] = {}
    for s in samples:
        by_class.setdefault(s["class"], []).append(s)
    learn, heldout = [], []
    for cls, insts in sorted(by_class.items()):
        idxs = rng.permutation(len(insts))
        n_train = max(1, int(round(train_frac * len(insts))))
        for i in idxs[:n_train]:
            learn.append(insts[i])
        for i in idxs[n_train:]:
            heldout.append(insts[i])
    return learn, heldout


# ============================================================================================= #
#  DIGILETS — RUN 48: mechanical raw-text parse (many-writer pen corpus).
# ============================================================================================= #
DIGILETS_DIR = os.path.join(DATA_DIR, "digilets")
DIGILETS_RAW_DIR = os.path.join(DIGILETS_DIR, "data", "raw", "complete")

# Recording order, verbatim from the corpus README ("we recorded numbers 0-9, lowercase letters
# a-z and uppercase letters A-Z, in that order"): symbol index (0-61) -> character.
DIGILETS_SYMBOLS = ([str(d) for d in range(10)] +
                    [chr(c) for c in range(ord("a"), ord("z") + 1)] +
                    [chr(c) for c in range(ord("A"), ord("Z") + 1)])
assert len(DIGILETS_SYMBOLS) == 62


def _digilets_participant_files(raw_dir: str = DIGILETS_RAW_DIR) -> list:
    """Every raw participant DATA file, excluding the `_info` sidecar files (cleaned/
    extrapolated/sampled flags for PREPROCESSED data — not produced for, or consumed from, the
    `raw/complete` files this loader reads). Sorted for determinism."""
    if not os.path.isdir(raw_dir):
        return []
    return sorted(f for f in os.listdir(raw_dir)
                 if os.path.isfile(os.path.join(raw_dir, f)) and not f.endswith("_info"))


def _parse_digilets_filename(fname: str) -> dict:
    """`<wid>-<gender>-<age>-<hand>_<timestamp>` -> the participant's own recorded metadata
    (mechanical split on the corpus's own two filename separators)."""
    stem, _, ts = fname.partition("_")
    parts = stem.split("-")
    return {"writer_id": parts[0], "gender": parts[1], "age": parts[2], "hand": parts[3],
           "recording_time": ts}


def _split_digilets_strokes(pos_xy: np.ndarray, pen_down: np.ndarray) -> list:
    """Split one instance's point sequence into per-stroke `(k, 2)` arrays at every index where
    `pen_down == 1` (a pen-TOUCH-DOWN event, not a continuous down/up state — verified against
    real multi-stroke letters: index 0 is always 1, and each further 1 marks the start of the
    next stroke after a pen lift the corpus does not otherwise record as a discrete point)."""
    starts = [i for i, v in enumerate(pen_down) if v == 1]
    if not starts or starts[0] != 0:
        starts = [0] + starts
    strokes = []
    for k, start in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(pos_xy)
        if end > start:
            strokes.append(pos_xy[start:end])
    return strokes


def load_digilets_samples(raw_dir: str = DIGILETS_RAW_DIR, *,
                          limit_writers: Optional[int] = None) -> list:
    """DigiLeTs raw-format loader (mechanical adapter): one dict per (writer, symbol, instance).
    Each participant file has 620 lines, interleaved data-line / one-hot-label-line pairs;
    `lines[::2]` gives the 310 data lines (`symbol_index*5 + instance_index`, symbol order per
    `DIGILETS_SYMBOLS`), each a whitespace-separated, NOT-padded run of `x y pressure pen_down t`
    quintuples (one point per 5 tokens). A line with fewer than 2 points is skipped (an honest
    partial-data floor, never a crash — `raw/complete` is documented usable-in-full but this
    guards malformed input the same way `load_quickdraw_drawings` does).

    Returns list of `{"writer_id", "gender", "age", "hand", "class" (0-61), "symbol" (the
    character), "instance" (0-4), "pos_xy" (N,2), "pressure" (N,), "pen_down" (N,), "t_ms" (N,),
    "strokes" (list of (k,2) arrays split at every pen-touch-down)}`. `limit_writers` caps the
    number of participant files read (None = all 77) — for cheap smoke tests / fast iteration."""
    files = _digilets_participant_files(raw_dir)
    if limit_writers is not None:
        files = files[:limit_writers]
    out = []
    for fname in files:
        meta = _parse_digilets_filename(fname)
        with open(os.path.join(raw_dir, fname)) as f:
            lines = f.readlines()
        data_lines = lines[::2]     # odd lines are one-hot symbol labels (see module docstring).
        for line_idx, line in enumerate(data_lines):
            toks = line.split()
            n_pts = len(toks) // 5
            if n_pts < 2:
                continue
            arr = np.asarray([float(t) for t in toks[:n_pts * 5]], dtype=float).reshape(n_pts, 5)
            pos_xy, pressure, pen_down, t = arr[:, 0:2], arr[:, 2], arr[:, 3], arr[:, 4]
            cls = line_idx // 5
            inst = line_idx % 5
            symbol = DIGILETS_SYMBOLS[cls] if cls < len(DIGILETS_SYMBOLS) else str(cls)
            strokes = _split_digilets_strokes(pos_xy, pen_down)
            out.append({"writer_id": meta["writer_id"], "gender": meta["gender"],
                       "age": meta["age"], "hand": meta["hand"], "class": cls, "symbol": symbol,
                       "instance": inst, "pos_xy": pos_xy, "pressure": pressure,
                       "pen_down": pen_down, "t_ms": t * 1000.0, "strokes": strokes})
    return out


def digilets_writer_split(samples: list, *, n_background: int = 40, seed: int = 20260706
                          ) -> tuple:
    """PER-WRITER background/held-out split (mechanical shuffle-and-slice, seeded, no leakage):
    every unique `writer_id` is assigned ENTIRELY to background or ENTIRELY to held-out (a
    writer never appears in both — the point of this split, unlike `uci_class_split`'s
    per-CLASS split, since DigiLeTs' whole value over UCI is genuine cross-writer variation).
    Returns `(background_samples, heldout_samples)`."""
    writer_ids = sorted({s["writer_id"] for s in samples})
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(writer_ids))
    n_bg = max(1, min(n_background, len(writer_ids) - 1))
    background_writers = {writer_ids[i] for i in order[:n_bg]}
    background, heldout = [], []
    for s in samples:
        (background if s["writer_id"] in background_writers else heldout).append(s)
    return background, heldout


# ============================================================================================= #
#  QUICKDRAW — mechanical ndjson parse (raw format: strokes + per-point timestamps).
# ============================================================================================= #
def load_quickdraw_drawings(path: str, limit: Optional[int] = None) -> tuple[list, int]:
    """One ndjson line -> `{"key_id", "word", "strokes_xy": [(N,2) arrays], "strokes_t":
    [(N,) arrays]}`. A line that fails `json.loads` (a truncated/partial download, or any other
    corruption) is silently skipped — an honest partial-data floor, never a crash, never a
    silently-wrong parse. Verbatim promotion of
    `jabberwock_pendata_run46.load_quickdraw_drawings`."""
    out = []
    n_bad = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                n_bad += 1
                continue
            drawing = obj.get("drawing")
            if not drawing:
                continue
            strokes_xy, strokes_t = [], []
            ok = True
            for st in drawing:
                if len(st) < 2 or len(st[0]) == 0:
                    ok = False
                    break
                strokes_xy.append(np.asarray([st[0], st[1]], dtype=float).T)
                t = np.asarray(st[2], dtype=float) if len(st) > 2 else \
                    np.arange(len(st[0]), dtype=float)
                strokes_t.append(t)
            if not ok:
                continue
            out.append({"key_id": obj.get("key_id"), "word": obj.get("word"),
                       "strokes_xy": strokes_xy, "strokes_t": strokes_t})
            if limit and len(out) >= limit:
                break
    return out, n_bad


def pooled_integer_delta_fraction(strokes_xy: list) -> float:
    """`mouse_model.integer_delta_fraction`'s own formula, applied PER STROKE then pooled
    (never across a pen-up gap between two strokes). Returns 0.0 (honest floor) if no stroke
    has >= 2 points. Verbatim promotion of run 46's function of the same name (this module
    reuses `mouse_model.integer_delta_fraction` per-stroke rather than re-deriving the
    integer-delta formula)."""
    deltas = []
    for s in strokes_xy:
        if s.shape[0] < 2:
            continue
        d = np.diff(s[:, :2], axis=0).flatten()
        deltas.append(d)
    if not deltas:
        return 0.0
    d = np.concatenate(deltas)
    if d.size == 0:
        return 0.0
    return float(np.mean(np.abs(d - np.round(d)) < 1e-6))


QD_SPLIT_HIST_BINS = 20
QD_SPLIT_FALLBACK = 0.35


def find_split_threshold(fracs: list, n_bins: int = QD_SPLIT_HIST_BINS,
                         fallback: float = QD_SPLIT_FALLBACK) -> dict:
    """Pre-registered ALGORITHM (run 46's own, unmodified): valley between the two largest
    histogram peaks over `[0, 1]` (boundary bins ARE eligible peak candidates); falls back to a
    fixed constant if the distribution isn't resolvably bimodal. Verbatim promotion of
    `jabberwock_pendata_run46._find_split_threshold`."""
    arr = np.asarray(fracs, dtype=float)
    hist, edges = np.histogram(arr, bins=n_bins, range=(0.0, 1.0))
    peaks = []
    for i in range(n_bins):
        if hist[i] <= 0:
            continue
        left_ok = (i == 0) or (hist[i] >= hist[i - 1])
        right_ok = (i == n_bins - 1) or (hist[i] >= hist[i + 1])
        if left_ok and right_ok:
            peaks.append(i)
    method = "fallback"
    thresh = fallback
    if len(peaks) >= 2:
        top2 = sorted(sorted(peaks, key=lambda i: -hist[i])[:2])
        lo, hi = top2
        if hi - lo >= 2:
            valley_i = lo + int(np.argmin(hist[lo:hi + 1]))
            thresh = float((edges[valley_i] + edges[valley_i + 1]) / 2.0)
            method = "valley"
    return {"threshold": thresh, "method": method,
            "histogram": hist.tolist(), "edges": edges.tolist()}


def classify_device(strokes_xy: list, threshold: float) -> str:
    """THIN I/O-boundary classifier (CLAUDE.md's own carve-out: "converting an opaque external
    form into the smallest graph token, AND there's no Rust primitive that can do the job") —
    a drawing's pooled integer-delta fraction below `threshold` -> "touch", else "mouse"."""
    frac = pooled_integer_delta_fraction(strokes_xy)
    return "touch" if frac < threshold else "mouse"


def stream_quickdraw_touch(path: str, threshold: float, *, cap: Optional[int] = None,
                           raw_cap: Optional[int] = None) -> tuple[list, list, int]:
    """Stream a category's ndjson, classify each drawing by device, and return
    `(touch_drawings, mouse_drawings, n_bad_lines)` — touch/mouse lists each capped at `cap`
    (None = uncapped) once enough are found; the underlying file read stops early once BOTH
    caps are met or `raw_cap` raw lines have been consulted (whichever first), a mechanical
    early-exit, not a decision over graph state."""
    touch, mouse = [], []
    n_bad = 0
    n_raw = 0
    with open(path) as f:
        for line in f:
            if raw_cap is not None and n_raw >= raw_cap:
                break
            line = line.strip()
            if not line:
                continue
            n_raw += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                n_bad += 1
                continue
            drawing = obj.get("drawing")
            if not drawing:
                continue
            strokes_xy, strokes_t = [], []
            ok = True
            for st in drawing:
                if len(st) < 2 or len(st[0]) == 0:
                    ok = False
                    break
                strokes_xy.append(np.asarray([st[0], st[1]], dtype=float).T)
                t = np.asarray(st[2], dtype=float) if len(st) > 2 else \
                    np.arange(len(st[0]), dtype=float)
                strokes_t.append(t)
            if not ok:
                continue
            d = {"key_id": obj.get("key_id"), "word": obj.get("word"),
                "strokes_xy": strokes_xy, "strokes_t": strokes_t}
            dev = classify_device(strokes_xy, threshold)
            bucket = touch if dev == "touch" else mouse
            if cap is None or len(bucket) < cap:
                bucket.append(d)
            if cap is not None and len(touch) >= cap and len(mouse) >= cap:
                break
    return touch, mouse, n_bad


def probe_category_valid(cat: str, categories_txt: str = os.path.join(DATA_DIR, "categories.txt")
                         ) -> bool:
    """Mechanical membership check against the dataset's own published category list (cached
    at `categories_txt`) — not a decision, a lookup."""
    if not os.path.exists(categories_txt):
        return True   # no cached list -> cannot rule it out, mechanical fallback
    with open(categories_txt) as f:
        names = {line.strip() for line in f if line.strip()}
    return cat in names


__all__ = ["load_uci_samples", "uci_class_split", "load_quickdraw_drawings",
           "pooled_integer_delta_fraction", "find_split_threshold", "classify_device",
           "stream_quickdraw_touch", "probe_category_valid",
           "QD_CATEGORIES_BACKGROUND", "QD_CATEGORIES_HELDOUT", "QD_CATEGORIES", "QD_FILES",
           "UCI_MAT_DEFAULT", "DATA_DIR",
           "load_digilets_samples", "digilets_writer_split", "DIGILETS_SYMBOLS",
           "DIGILETS_DIR", "DIGILETS_RAW_DIR"]
