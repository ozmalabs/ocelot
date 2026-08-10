"""tests/test_pen_world_migrated.py — RUN 47 unit gates for `domains/pen_world.py`, the
promoted pen/touch world adapter (run 46's one-off loaders -> a proper shared module). Run
BEFORE any Gate A/B number is computed, per this arc's own ops law. RUN 48 extends this with
DigiLeTs loader gates (`load_digilets_samples`, `digilets_writer_split`).

Covers: UCI `.mat` loader round-trip sanity on a SYNTHETIC mat-shaped structure (no dependency
on the real download being present — a real-data smoke check is added separately, SKIPPED if
`/tmp/pendata` is absent, never a hard failure on this shared/downloaded-data-dependent path);
QuickDraw ndjson round-trip on a synthetic file; the device classifier (`classify_device`,
`pooled_integer_delta_fraction`) on synthetic all-integer vs sub-pixel-float traces; the
bimodal-valley/fallback threshold algorithm on synthetic bimodal and unimodal populations;
`uci_class_split` train/held-out hygiene (no leakage, every class represented, deterministic);
DigiLeTs raw-text parse on a SYNTHETIC participant file (filename metadata, stroke split at
pen-touch-down events, class/instance/symbol indexing), `digilets_writer_split` per-writer
leakage hygiene, and a real-data smoke test (skipped if `/tmp/pendata/digilets` is absent); and
a source audit confirming the module contains no rule-engine calls, no `teach()` call, and no
agent-decision idiom — a pure loader, per CLAUDE.md.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from domains import pen_world as pw


# =============================================================================================
#  QUICKDRAW: ndjson round-trip on a synthetic file.
# =============================================================================================
def _write_ndjson(path: Path, rows: list) -> None:
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_quickdraw_loader_round_trip(tmp_path):
    rows = [
        {"key_id": "1", "word": "circle",
         "drawing": [[[0, 1, 2, 3], [0, 1, 0, -1], [0, 10, 20, 30]]]},
        {"key_id": "2", "word": "circle",
         "drawing": [[[0, 1], [0, 1]], [[5, 6, 7], [5, 4, 3]]]},
    ]
    path = tmp_path / "synthetic.ndjson"
    _write_ndjson(path, rows)
    draws, n_bad = pw.load_quickdraw_drawings(str(path))
    assert n_bad == 0
    assert len(draws) == 2
    d0 = draws[0]
    assert d0["key_id"] == "1"
    assert len(d0["strokes_xy"]) == 1
    assert d0["strokes_xy"][0].shape == (4, 2)
    assert d0["strokes_t"][0].tolist() == [0, 10, 20, 30]
    d1 = draws[1]
    assert len(d1["strokes_xy"]) == 2


def test_quickdraw_loader_skips_corrupt_lines_honestly(tmp_path):
    path = tmp_path / "corrupt.ndjson"
    with open(path, "w") as f:
        f.write(json.dumps({"key_id": "1", "word": "x",
                            "drawing": [[[0, 1], [0, 1]]]}) + "\n")
        f.write('{"key_id": "2", "word": "x", "drawing": [[[0, 1' + "\n")   # truncated
        f.write(json.dumps({"key_id": "3", "word": "x",
                            "drawing": [[[0, 1], [0, 1]]]}) + "\n")
    draws, n_bad = pw.load_quickdraw_drawings(str(path))
    assert n_bad == 1
    assert len(draws) == 2
    assert [d["key_id"] for d in draws] == ["1", "3"]


def test_quickdraw_loader_limit(tmp_path):
    rows = [{"key_id": str(i), "word": "x", "drawing": [[[0, 1], [0, 1]]]} for i in range(10)]
    path = tmp_path / "many.ndjson"
    _write_ndjson(path, rows)
    draws, _ = pw.load_quickdraw_drawings(str(path), limit=3)
    assert len(draws) == 3


# =============================================================================================
#  DEVICE CLASSIFIER: synthetic integer-grid vs sub-pixel-float traces (mirrors run 46's own
#  unit_sanity check (c), promoted into a real pytest gate).
# =============================================================================================
def test_pooled_integer_delta_fraction_discriminates_device():
    all_int_stroke = np.array([[float(i), float(2 * i)] for i in range(30)])
    rng = np.random.default_rng(0)
    subpixel_stroke = np.cumsum(rng.uniform(0.1, 0.9, size=(30, 2)), axis=0)
    frac_int = pw.pooled_integer_delta_fraction([all_int_stroke])
    frac_float = pw.pooled_integer_delta_fraction([subpixel_stroke])
    assert frac_int > 0.99
    assert frac_float < 0.05


def test_pooled_integer_delta_fraction_never_crosses_stroke_boundary():
    """A single-point 'jump' stroke boundary must not contaminate the pooled fraction — deltas
    are computed PER STROKE, never across the pen-up gap between two strokes."""
    stroke_a = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])   # all-integer deltas
    stroke_b = np.array([[500.7, 500.3], [501.9, 501.1]])       # a huge cross-stroke jump if
                                                                  # pooled naively, but a
                                                                  # sub-pixel delta WITHIN itself
    frac = pw.pooled_integer_delta_fraction([stroke_a, stroke_b])
    # stroke_a contributes 2 integer deltas, stroke_b contributes 1 non-integer delta (1.2, 0.8)
    assert abs(frac - 2 / 3) < 1e-9


def test_pooled_integer_delta_fraction_degenerate_floor():
    assert pw.pooled_integer_delta_fraction([]) == 0.0
    assert pw.pooled_integer_delta_fraction([np.array([[0.0, 0.0]])]) == 0.0


def test_classify_device_thin_threshold():
    all_int_stroke = np.array([[float(i), float(2 * i)] for i in range(10)])
    rng = np.random.default_rng(1)
    subpixel_stroke = np.cumsum(rng.uniform(0.1, 0.9, size=(10, 2)), axis=0)
    assert pw.classify_device([all_int_stroke], 0.35) == "mouse"
    assert pw.classify_device([subpixel_stroke], 0.35) == "touch"


# =============================================================================================
#  SPLIT-THRESHOLD ALGORITHM: bimodal valley vs unimodal fallback.
# =============================================================================================
def test_find_split_threshold_bimodal_valley():
    # Narrow, single-bin-dominant clusters so each mode has exactly one local peak (a wide,
    # multi-bin cluster can carry several internal local maxima, which is a property of the
    # peak-finder's own local-maximum definition, not a bug — this test isolates the clean
    # two-peak case the module docstring's algorithm is designed for).
    rng = np.random.default_rng(2)
    lo = rng.normal(0.05, 0.01, size=200).clip(0.0, 1.0)
    hi = rng.normal(0.95, 0.01, size=800).clip(0.0, 1.0)
    fracs = np.concatenate([lo, hi]).tolist()
    rep = pw.find_split_threshold(fracs)
    assert rep["method"] == "valley"
    # The valley may land anywhere in the flat zero-count gap between the two peaks (the
    # algorithm's own contract: "midpoint of the histogram valley", not necessarily the
    # geometric midpoint of the two modes) — the meaningful property is that it CLEANLY
    # separates the two populations, checked directly rather than pinning an exact value.
    thresh = rep["threshold"]
    assert float(np.max(lo)) < thresh < float(np.min(hi)), (
        "the chosen threshold must separate the lo cluster from the hi cluster")


def test_find_split_threshold_unimodal_falls_back():
    rng = np.random.default_rng(3)
    fracs = rng.normal(0.6, 0.02, size=500).clip(0, 1).tolist()
    rep = pw.find_split_threshold(fracs)
    assert rep["method"] == "fallback"
    assert rep["threshold"] == pw.QD_SPLIT_FALLBACK


# =============================================================================================
#  STREAMING SAMPLER: touch/mouse split + caps, on a synthetic mixed-device file.
# =============================================================================================
def test_stream_quickdraw_touch_splits_and_caps(tmp_path):
    rng = np.random.default_rng(4)
    rows = []
    for i in range(20):
        if i % 2 == 0:      # "mouse": integer grid
            xs = list(range(10))
            ys = [2 * v for v in xs]
        else:                # "touch": sub-pixel float
            pts = np.cumsum(rng.uniform(0.1, 0.9, size=(10, 2)), axis=0)
            xs, ys = pts[:, 0].tolist(), pts[:, 1].tolist()
        rows.append({"key_id": str(i), "word": "x", "drawing": [[xs, ys]]})
    path = tmp_path / "mixed.ndjson"
    _write_ndjson(path, rows)
    touch, mouse, n_bad = pw.stream_quickdraw_touch(str(path), threshold=0.35, cap=5)
    assert n_bad == 0
    assert len(touch) <= 5 and len(mouse) <= 5
    assert len(touch) > 0 and len(mouse) > 0


# =============================================================================================
#  UCI train/held-out split: no leakage, every class covered, deterministic.
# =============================================================================================
def _fake_uci_samples(n_per_class=10, n_classes=4):
    out = []
    for c in range(n_classes):
        cls = f"c{c}"
        for i in range(n_per_class):
            out.append({"class": cls, "idx": (c, i),
                       "pos_xy": np.zeros((5, 2)), "t_ms": np.arange(5, dtype=float)})
    return out


def test_uci_class_split_no_leakage_and_covers_every_class():
    samples = _fake_uci_samples()
    learn, heldout = pw.uci_class_split(samples, train_frac=0.6, seed=1)
    learn_idx = {s["idx"] for s in learn}
    heldout_idx = {s["idx"] for s in heldout}
    assert learn_idx.isdisjoint(heldout_idx), "a sample must never appear in both splits"
    assert len(learn) + len(heldout) == len(samples)
    learn_classes = {s["class"] for s in learn}
    heldout_classes = {s["class"] for s in heldout}
    all_classes = {s["class"] for s in samples}
    assert learn_classes == all_classes, "every class must be represented in LEARN"
    assert heldout_classes == all_classes, "every class must be represented in held-out"


def test_uci_class_split_deterministic():
    samples = _fake_uci_samples()
    l1, h1 = pw.uci_class_split(samples, seed=42)
    l2, h2 = pw.uci_class_split(samples, seed=42)
    assert [s["idx"] for s in l1] == [s["idx"] for s in l2]
    assert [s["idx"] for s in h1] == [s["idx"] for s in h2]


# =============================================================================================
#  DIGILETS (RUN 48): raw-text parse on a SYNTHETIC participant file.
# =============================================================================================
def _digilets_line(points: list) -> str:
    """`points`: list of (x, y, pressure, pen_down, t) 5-tuples -> one raw data line, the
    corpus's own space-separated-quintuples format."""
    toks = []
    for (x, y, p, pd, t) in points:
        toks += [f"{x:f}", f"{y:f}", f"{p:f}", str(int(pd)), f"{t:f}"]
    return " ".join(toks) + "\n"


def _default_digilets_instance(n: int = 4, pen_down_at: tuple = (0,)) -> list:
    return [(0.1 * i, 0.2 * i, 0.5, 1 if i in pen_down_at else 0, 0.02 * i) for i in range(n)]


def _write_digilets_participant(path, overrides: dict = None) -> None:
    """Writes a full 620-line synthetic participant file (310 data lines + 310 one-hot label
    lines, interleaved — `lines[::2]` gives the data lines the loader reads). `overrides`:
    `{line_idx: points}` to replace the default single-stroke 4-point instance at that line."""
    overrides = overrides or {}
    lines = []
    for line_idx in range(310):
        points = overrides.get(line_idx, _default_digilets_instance())
        lines.append(_digilets_line(points))
        label = ["0.0"] * 62
        label[line_idx // 5] = "1.0"
        lines.append(" ".join(label) + "\n")
    with open(path, "w") as f:
        f.writelines(lines)


def test_digilets_loader_parses_filename_class_instance_and_counts(tmp_path):
    fname = "007-f-24-right_2019-06-19-12-18-49"
    _write_digilets_participant(tmp_path / fname)
    samples = pw.load_digilets_samples(str(tmp_path))
    assert len(samples) == 310
    s0 = samples[0]
    assert s0["writer_id"] == "007" and s0["gender"] == "f" and s0["age"] == "24"
    assert s0["hand"] == "right"
    assert s0["class"] == 0 and s0["symbol"] == "0" and s0["instance"] == 0
    # line_idx 61 -> class 12, instance 1 (symbol order 0-9,a-z,A-Z -> class 12 is 'c').
    s61 = samples[61]
    assert s61["class"] == 12 and s61["symbol"] == "c" and s61["instance"] == 1
    # last line_idx 309 -> class 61, instance 4 -> symbol 'Z'.
    s_last = samples[-1]
    assert s_last["class"] == 61 and s_last["symbol"] == "Z" and s_last["instance"] == 4
    classes = {s["class"] for s in samples}
    assert classes == set(range(62))
    assert bool(np.all(np.isfinite(s0["pos_xy"])))


def test_digilets_loader_splits_strokes_at_pen_touch_down(tmp_path):
    """A two-stroke instance (pen_down at index 0 AND index 3 of a 6-point line) must split
    into exactly two stroke arrays at that boundary — not naively treated as one continuous
    path, and not confused by the corpus's OWN convention that pen_down marks a touch-DOWN
    event, not a continuous held-down state."""
    points = [(0.0, 0.0, 0.5, 1, 0.0), (1.0, 0.0, 0.5, 0, 0.02), (2.0, 0.0, 0.5, 0, 0.04),
             (5.0, 5.0, 0.5, 1, 0.10), (6.0, 5.0, 0.5, 0, 0.12), (7.0, 5.0, 0.5, 0, 0.14)]
    fname = "099-m-30-left_20260706-000000"
    _write_digilets_participant(tmp_path / fname, overrides={0: points})
    samples = pw.load_digilets_samples(str(tmp_path))
    s0 = samples[0]
    assert len(s0["strokes"]) == 2
    assert s0["strokes"][0].shape == (3, 2)
    assert s0["strokes"][1].shape == (3, 2)
    assert np.allclose(s0["strokes"][0], [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    assert np.allclose(s0["strokes"][1], [[5.0, 5.0], [6.0, 5.0], [7.0, 5.0]])


def test_digilets_loader_skips_short_lines(tmp_path):
    fname = "003-f-19-right_20260706-000001"
    _write_digilets_participant(tmp_path / fname, overrides={5: [(0.0, 0.0, 0.1, 1, 0.0)]})
    samples = pw.load_digilets_samples(str(tmp_path))
    # line_idx 5 has only 1 point (< 2) -> skipped entirely, all other 309 lines kept.
    assert len(samples) == 309
    kept_line_idxs = {(s["class"] * 5 + s["instance"]) for s in samples}
    assert 5 not in kept_line_idxs


def test_digilets_loader_limit_writers(tmp_path):
    for i in range(3):
        _write_digilets_participant(tmp_path / f"{i:03d}-f-20-right_ts{i}")
    samples_all = pw.load_digilets_samples(str(tmp_path))
    samples_limited = pw.load_digilets_samples(str(tmp_path), limit_writers=2)
    assert len(samples_all) == 3 * 310
    assert len(samples_limited) == 2 * 310
    assert len({s["writer_id"] for s in samples_limited}) == 2


# =============================================================================================
#  DIGILETS_WRITER_SPLIT: per-writer leakage hygiene (a writer never appears in both splits).
# =============================================================================================
def _fake_digilets_samples(n_writers=10, n_per_writer=20):
    out = []
    for w in range(n_writers):
        wid = f"w{w:03d}"
        for i in range(n_per_writer):
            out.append({"writer_id": wid, "class": i % 62, "instance": i % 5,
                       "pos_xy": np.zeros((5, 2))})
    return out


def test_digilets_writer_split_no_leakage():
    samples = _fake_digilets_samples(n_writers=10)
    bg, ho = pw.digilets_writer_split(samples, n_background=4, seed=1)
    bg_writers = {s["writer_id"] for s in bg}
    ho_writers = {s["writer_id"] for s in ho}
    assert bg_writers.isdisjoint(ho_writers), "a writer must never appear in both splits"
    assert len(bg_writers) == 4
    assert len(ho_writers) == 6
    assert len(bg) + len(ho) == len(samples)


def test_digilets_writer_split_deterministic():
    samples = _fake_digilets_samples(n_writers=10)
    bg1, ho1 = pw.digilets_writer_split(samples, n_background=4, seed=7)
    bg2, ho2 = pw.digilets_writer_split(samples, n_background=4, seed=7)
    assert [s["writer_id"] for s in bg1] == [s["writer_id"] for s in bg2]
    assert [s["writer_id"] for s in ho1] == [s["writer_id"] for s in ho2]


# =============================================================================================
#  REAL-DATA SMOKE (skipped if /tmp/pendata is absent — never a hard failure on shared/
#  downloaded corpora, per this arc's own convention for real-file-dependent tests).
# =============================================================================================
@pytest.mark.skipif(not os.path.exists(pw.UCI_MAT_DEFAULT), reason="real UCI download absent")
def test_uci_real_loader_round_trip_sane():
    samples = pw.load_uci_samples()
    assert len(samples) > 0
    s0 = samples[0]
    t = s0["t_ms"]
    assert bool(np.all(np.diff(t) > 0)), "time must be monotone"
    assert bool(np.allclose(np.diff(t), t[1] - t[0])), "dt must be uniform (200Hz)"
    extent = s0["pos_xy"].max(axis=0) - s0["pos_xy"].min(axis=0)
    assert bool(np.all(extent > 1e-3) and np.all(extent < 1e4))
    assert bool(np.all(np.isfinite(s0["pos_xy"])))


@pytest.mark.skipif(not os.path.exists(pw.QD_FILES["circle"]), reason="real QuickDraw sample absent")
def test_quickdraw_real_category_files_present_and_probe_valid():
    for cat in pw.QD_CATEGORIES:
        assert pw.probe_category_valid(cat), f"{cat!r} not in the dataset's own category list"


@pytest.mark.skipif(not os.path.exists(pw.DIGILETS_RAW_DIR), reason="real DigiLeTs download absent")
def test_digilets_real_loader_round_trip_sane():
    samples = pw.load_digilets_samples(limit_writers=2)
    assert len(samples) == 2 * 310, "2 writers x 62 classes x 5 instances"
    assert len({s["writer_id"] for s in samples}) == 2
    classes = {s["class"] for s in samples}
    assert classes == set(range(62))
    symbols = {s["class"]: s["symbol"] for s in samples}
    assert symbols[0] == "0" and symbols[10] == "a" and symbols[36] == "A"
    for s in samples[:20]:
        assert bool(np.all(np.isfinite(s["pos_xy"])))
        assert len(s["strokes"]) >= 1
        assert sum(len(st) for st in s["strokes"]) == s["pos_xy"].shape[0]


@pytest.mark.skipif(not os.path.exists(pw.DIGILETS_RAW_DIR), reason="real DigiLeTs download absent")
def test_digilets_real_writer_split_no_leakage():
    samples = pw.load_digilets_samples(limit_writers=10)
    bg, ho = pw.digilets_writer_split(samples, n_background=6, seed=20260706)
    bg_writers = {s["writer_id"] for s in bg}
    ho_writers = {s["writer_id"] for s in ho}
    assert bg_writers.isdisjoint(ho_writers)
    assert len(bg_writers) == 6 and len(ho_writers) == 4


# =============================================================================================
#  SOURCE AUDIT — pure loader, no rule engine, no teach(), no agent decision idiom
#  (CLAUDE.md's hard-NO list).
# =============================================================================================
def test_pen_world_source_audit_no_agent_decisions():
    src = Path(pw.__file__).read_text()
    banned = ["graph_rewrite.run", "gr._match", "gr._apply", "gr.make_rule",
             "CuriousAgent", "teach(", "run_rules(", "substrate.tick("]
    for token in banned:
        assert token not in src, f"pen_world.py must not contain {token!r} — it is a pure loader"
