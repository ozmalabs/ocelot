"""tests/test_homework_characters_migrated.py — run-27 gates for domains/homework_loop.py's
CHARACTER-GRAIN extension (`mark_characters`/`babble_characters`/`cycle_characters`). Hermetic,
synthetic ink only (`glyph_motor_world._sample_stroke`), same live-geometry precedent
`tests/test_homework_loop_migrated.py`/`tests/test_ink_decode_migrated.py` use — no dataset.

COUNT-MISMATCH TOLERANCE (the coordinator's own required fix, landed here): run 26's final
report found every one of its 5 surviving residuals was a span-COUNT mismatch, and the OLD
stroke-grain `babble` alignment guard (`if len(re_spans) != n: continue`) discarded every rep
whose re-decode changed the span count — exactly the residual class that survives marking.
The character-grain functions align by ARC-LENGTH OVERLAP (`_align_spans_by_overlap`), never by
positional index/count-equality, so a merge (N->1) or split (1->N) is itself the residual to
practice, never a reason to skip. Gates below exercise both directions directly."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import glyph_motor_world as gmw
from domains import homework_loop as hl
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc
from domains.teach import teach as _real_teach


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    """Redirect teach() persistence to a tmp dir — this suite's mints must never land in
    the boot seed (seeds/stroke_shapes.json); the live graph install is unaffected. Belt-
    and-suspenders alongside the session-wide conftest.py guard (mirrors
    test_arrangement_codebook_migrated.py's own established fixture)."""
    monkeypatch.setattr(
        sc, "teach",
        lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _corner_char_fixture(s):
    """ONE raw pen-stroke, two perpendicular lines concatenated — the SAME empirically-grounded
    induced-instability geometry `test_homework_loop_migrated.py::_corner_fixture` uses (a
    straight line's rotation-symmetric invariant signature ties "down"/"right"), wrapped as a
    single-raw-stroke CHARACTER item. Returns `(char_items, dk)`."""
    down_pts = gmw._sample_stroke("line", [0.0, 0.0, 0.0, -1.0], 24)
    right_start = down_pts[-1]
    right_pts = gmw._sample_stroke(
        "line", [right_start[0], right_start[1], right_start[0] + 1.0, right_start[1]], 24)
    sc.build_stroke_codebook(
        s, sources=[("down", down_pts.tolist()), ("right", right_pts.tolist())],
        include_pickle=False)
    concatenated = np.concatenate([down_pts, right_pts], axis=0)
    n_knots = len(concatenated)
    half = n_knots // 2
    dk = hl._default_dk()
    dk.update(min_span=half, max_span=half, max_knots=n_knots)
    char_items = [{"id": "char0", "class_id": "A", "strokes": [concatenated.tolist()]}]
    return char_items, dk


# ===========================================================================
# Gate 1 — arrangement disagreement is detected EVEN WHEN every stroke family agrees.
# ===========================================================================
def test_arrangement_disagreement_detected_when_families_agree():
    s, ag, native = _boot()
    orig_sig = [["strokeq", 0, "a"], ["strokeq", 1, "b"],
                ["rel", 0, 1, 2, 3, 4], ["rel", 1, 5, 6, 7, 8],
                ["cpose_x", 1], ["cpose_y", 2], ["cpose_o", 3], ["cpose_s", 4]]
    # SAME identities, ONE relation (stroke 1's scale bin) perturbed -- pure arrangement drift.
    re_sig = [["strokeq", 0, "a"], ["strokeq", 1, "b"],
              ["rel", 0, 1, 2, 3, 4], ["rel", 1, 5, 6, 7, 99],
              ["cpose_x", 1], ["cpose_y", 2], ["cpose_o", 3], ["cpose_s", 4]]
    orig_groups = [[(0, 1, "a")], [(1, 2, "b")]]
    re_groups = [[(0, 1, "a")], [(1, 2, "b")]]
    scored = hl._character_round_trip_score(s, native, orig_groups, re_groups, orig_sig, re_sig)
    assert scored["family_score"] == 1.0, "identities are IDENTICAL -- family must score perfect"
    assert scored["count_score"] == 1.0
    assert scored["arrangement_score"] < 1.0, "a perturbed 'rel' value must show up in ARRANGEMENT"
    assert scored["overall"] < 1.0
    labels = {r[0] for r in scored["residual_spans"]}
    assert "arrangement" in labels


def test_arrangement_agreement_is_perfect_on_identical_signatures():
    s, ag, native = _boot()
    sig = [["strokeq", 0, "a"], ["rel", 0, 1, 2, 3, 4], ["cpose_x", 1]]
    groups = [[(0, 1, "a")]]
    scored = hl._character_round_trip_score(s, native, groups, groups, sig, sig)
    assert scored["overall"] == 1.0
    assert scored["residual_spans"] == []


# ===========================================================================
# Gate 2 — the READING pass mints on genuinely novel ink, and it is COUNTED (not silently
# absorbed) — the run's own headline measurement ("reading as practice imports information").
# ===========================================================================
def test_reading_pass_mints_and_reports():
    s, ag, native = _boot()
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24)
    sc.build_stroke_codebook(s, sources=[("I_0", line_pts.tolist())], include_pickle=False)

    rng = np.random.default_rng(0)
    steps = rng.normal(0, 1, size=(23, 2))
    raw = np.concatenate([np.zeros((1, 2)), np.cumsum(steps, axis=0)], axis=0)
    raw_len = float(np.sqrt(((np.diff(raw, axis=0)) ** 2).sum(1)).sum()) or 1.0
    squiggle = raw / raw_len   # a genuinely novel shape -- not a line, not close to one.

    dk = hl._default_dk()
    dk.update(min_span=24, max_span=24, max_knots=24)
    char_items = [{"id": "char0", "class_id": "A", "strokes": [squiggle.tolist()]}]

    marked = hl.mark_characters(s, char_items, dk=dk)
    assert marked[0].n_mints_reading == 1, (
        "a genuinely novel stroke must OOV-mint during the READING pass, and the mint must be "
        "counted on the MarkedItem")

    # A fresh cycle_characters run on a NEW substrate aggregates it into mints_during_reading.
    s2, ag2, native2 = _boot()
    sc.build_stroke_codebook(s2, sources=[("I_0", line_pts.tolist())], include_pickle=False)
    rep = hl.cycle_characters(s2, char_items, reps_per_item=4, rng_seed=1, dk=dk, jitter_bins=0)
    assert rep.mints_during_reading >= 1


# ===========================================================================
# Gate 3 — correlated jitter is ACTUALLY correlated: one shared component, added into every
# span's own final jitter, deterministically reproducible from the same rng state.
# ===========================================================================
def test_correlated_jitter_is_correlated():
    rng = np.random.default_rng(42)
    shared, jitter_by_idx = hl._character_jitter_by_idx(rng, jitter_bins=5, n=3)
    assert any(shared), "the shared character-level component must be genuinely nonzero here"

    rng2 = np.random.default_rng(42)
    expected_shared = tuple(int(x) for x in rng2.integers(-5, 6, size=4))
    assert shared == expected_shared
    for i in range(3):
        expected_per = tuple(int(x) for x in rng2.integers(-5, 6, size=4))
        expected = tuple(expected_shared[d] + expected_per[d] for d in range(4))
        assert jitter_by_idx[i] == expected, f"span {i} must carry the SAME shared delta"


def test_jitter_bins_zero_is_all_zero_and_still_shared():
    rng = np.random.default_rng(7)
    shared, jitter_by_idx = hl._character_jitter_by_idx(rng, jitter_bins=0, n=4)
    assert shared == (0, 0, 0, 0)
    assert all(v == (0, 0, 0, 0) for v in jitter_by_idx.values())


# ===========================================================================
# Gate 4 — frontier assign() works UNCHANGED on character-grain MarkedItems.
# ===========================================================================
def test_frontier_assign_works_on_character_marked_items():
    s, ag, native = _boot()
    char_items, dk = _corner_char_fixture(s)
    marked = hl.mark_characters(s, char_items, dk=dk)
    assert 0.0 < marked[0].round_trip_score < 1.0, (
        "the corner-character fixture must show a genuine partial residual")
    ws = hl.assign(marked)
    assert [wi.item_id for wi in ws.items] == ["char0"]
    assert all(isinstance(sp, hl.SpanParse) for sp in ws.items[0].spans)


# ===========================================================================
# Gate 5 — eval isolation on the character-grain entry points.
# ===========================================================================
def test_eval_isolation_raises_on_mark_characters():
    s, ag, native = _boot()
    char_items, dk = _corner_char_fixture(s)
    with pytest.raises(hl.EvalLeakageError):
        hl.mark_characters(s, char_items, dk=dk, eval_class_ids={"A"})


def test_eval_isolation_raises_on_babble_characters():
    wi = hl.WorksheetItem(item_id="x", class_id="EVAL_CLASS", round_trip_score=0.5,
                          residual_spans=[], spans=[], dk=hl._default_dk())
    ws = hl.Worksheet(items=[wi])
    s, ag, native = _boot()
    with pytest.raises(hl.EvalLeakageError):
        hl.babble_characters(s, ws, reps_per_item=1, rng_seed=0, eval_class_ids={"EVAL_CLASS"})


def test_eval_isolation_is_a_noop_on_mark_characters_when_class_not_held_out():
    s, ag, native = _boot()
    char_items, dk = _corner_char_fixture(s)
    marked = hl.mark_characters(s, char_items, dk=dk, eval_class_ids={"SOME_OTHER_CLASS"})
    assert len(marked) == 1


# ===========================================================================
# Gate 6 — MERGE (N spans -> 1) is aligned by overlap, never dropped, at the primitive level.
# ===========================================================================
def test_align_spans_by_overlap_handles_merge():
    s, ag, native = _boot()
    orig = [(0, 10, "a"), (10, 20, "b")]     # two original spans
    re = [(0, 20, "merged")]                  # re-decode MERGED them into one
    align = hl._align_spans_by_overlap(native, orig, re)
    assert len(align) == 2, "both original spans must be accounted for, never silently dropped"
    matched = [(o, r) for (o, r, _ov) in align if o is not None and r is not None]
    unmatched_orig = [o for (o, r, _ov) in align if r is None]
    assert len(matched) == 1
    assert len(unmatched_orig) == 1


def test_align_spans_by_overlap_handles_split():
    s, ag, native = _boot()
    orig = [(0, 20, "whole")]                 # one original span
    re = [(0, 10, "half_a"), (10, 20, "half_b")]   # re-decode SPLIT it into two
    align = hl._align_spans_by_overlap(native, orig, re)
    assert len(align) == 2
    matched = [(o, r) for (o, r, _ov) in align if o is not None and r is not None]
    unmatched_re = [r for (o, r, _ov) in align if o is None]
    assert len(matched) == 1
    assert len(unmatched_re) == 1


def test_align_spans_by_overlap_no_overlap_is_all_unmatched():
    s, ag, native = _boot()
    orig = [(0, 5, "a")]
    re = [(50, 60, "b")]
    align = hl._align_spans_by_overlap(native, orig, re)
    assert sorted(align, key=lambda t: (t[0] is None, t[1] is None)) or True  # no crash
    kinds = {(o is None, r is None) for (o, r, _ov) in align}
    assert (False, True) in kinds and (True, False) in kinds


# ===========================================================================
# Gate 7 — mark_characters on a real MERGE-inducing fixture: not dropped, not silently perfect.
# ===========================================================================
def test_mark_characters_captures_merge_instability_without_crashing():
    s, ag, native = _boot()
    char_items, dk = _corner_char_fixture(s)
    marked = hl.mark_characters(s, char_items, dk=dk)
    m = marked[0]
    assert 0.0 < m.round_trip_score < 1.0
    assert m.family_score is not None and m.count_score is not None
    assert m.arrangement_score is not None
    assert m.residual_spans, "the instability must be CAPTURED, not silently perfect"
    assert m.n_orig_spans == 2


# ===========================================================================
# Gate 8 — babble_characters on a SPLIT-inducing worksheet: NOT skipped (the coordinator's own
# required fix) -- produces a segmentation_split_instability correction and completes all reps.
# ===========================================================================
def test_babble_characters_split_not_skipped():
    s, ag, native = _boot()
    char_items, dk = _corner_char_fixture(s)
    marked = hl.mark_characters(s, char_items, dk=dk)
    ws = hl.assign(marked)
    assert ws.items
    wi = ws.items[0]
    # Force a SMALLER max_span than each span's own point count so every re-render/re-decode
    # of a single 24-point span SPLITS into >=2 sub-spans, deterministically, every rep.
    dk2 = dict(wi.dk)
    dk2["min_span"] = 8
    dk2["max_span"] = 12
    wi.dk = dk2

    log = hl.babble_characters(s, ws, reps_per_item=6, rng_seed=1, jitter_bins=0)
    entry = log.per_item[wi.item_id]
    assert entry["reps"] == 6, "a count-mismatching re-decode must NOT skip/abort the rep"
    types = {c["type"] for c in entry["corrections"]}
    assert "segmentation_split_instability" in types, (
        f"a majority-consistent split must be persisted as its own instability signal, "
        f"got correction types {types!r}")


def test_babble_characters_no_ground_ink_signature():
    """API-shape guarantee mirroring `test_babble_signature_takes_no_ground_ink_items` one
    level up."""
    import inspect
    sig = inspect.signature(hl.babble_characters)
    param_names = set(sig.parameters)
    assert not (param_names & {"items", "ground_items", "points", "char_items"}), (
        f"babble_characters() must not accept a raw-ink/ground-items parameter: {param_names!r}")


# ===========================================================================
# Gate 9 — cycle_characters end-to-end: reports mint/babble counts, never crashes, surviving
# residual count never RISES.
# ===========================================================================
def test_cycle_characters_reports_mint_and_babble_counts_and_does_not_regress():
    s, ag, native = _boot()
    char_items, dk = _corner_char_fixture(s)
    rep1 = hl.cycle_characters(s, char_items, reps_per_item=6, rng_seed=1, dk=dk, jitter_bins=0)
    assert isinstance(rep1.mints_during_reading, int)
    assert isinstance(rep1.mints_during_babble, int)
    assert rep1.mints_during_reading >= 0 and rep1.mints_during_babble >= 0
    assert rep1.surviving_residual_count <= rep1.surviving_residual_count_before

    rep2 = hl.cycle_characters(s, char_items, reps_per_item=6, rng_seed=1, dk=dk, jitter_bins=0)
    assert rep2.surviving_residual_count <= rep1.surviving_residual_count, (
        "teacher-information metric must not RISE across character-grain cycles either")
