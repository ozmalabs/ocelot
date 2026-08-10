"""tests/test_homework_loop_migrated.py — the run-26 gates for domains/homework_loop.py, the
BABBLE SELF-IMPROVEMENT WITH PERIODIC GROUNDING loop. Hermetic, synthetic ink only
(`glyph_motor_world._sample_stroke`, the SAME live-geometry precedent
`tests/test_ink_decode_migrated.py` uses -- no dataset).

GATE 3/4's induced-instability fixture (`_corner_fixture`) is EMPIRICALLY grounded, not
hand-waved: two straight lines ("down" then "right") concatenated into one continuous pen
path. The ORIGINAL decode recognizes both spans as "down" (a straight line's invariant
signature is rotation-symmetric -- "down"/"right" tie, and "down" wins); re-rendering and
re-reading that SAME parse discretization-drifts the second span just enough to miss "down"'s
own fine/coarse/mid grains, OOV-minting a genuinely independent top-level peer quantum
(verified directly against the live `StrokeQuantize`/`StrokeRender` wheel while designing
this suite) -- a real instance of the arc's own documented "reproducer segmentation
instability across re-render" residual, not a synthetic construction. `babble`'s mechanism
(a) (persist a `stability_preferred_alt` learned from repeated, deterministic zero-jitter
practice) plus mechanism (b) (mint a refinement child off the majority-consistent residual
signature) together close it: a fresh re-mark after one `babble()` call resolves the item to a
perfect round trip."""
from __future__ import annotations

import inspect
import re
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from substrate.boot_core import boot_core
from domains import glyph_motor_world as gmw
from domains import homework_loop as hl
from domains import ink_decode as ink
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


# ---------------------------------------------------------------------------
# The induced-instability fixture (live geometry) -- see module docstring.
# ---------------------------------------------------------------------------
def _corner_fixture(s):
    """Two perpendicular straight lines, one continuous pen path. Returns
    `(items, dk)` -- `items` is a single-item ground set ready for `hl.mark`."""
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

    items = [{"id": "corner0", "class_id": "A", "points": concatenated.tolist()}]
    return items, dk


# ===========================================================================
# Gate 1 — assignment is DERIVED from marking (worksheet subset-of marked residuals).
# ===========================================================================
def test_worksheet_derived_from_marking_residuals():
    marked = [
        hl.MarkedItem(item_id="zero", class_id="A", round_trip_score=0.0, n_orig_spans=2,
                     n_reread_spans=0, residual_spans=[(0, "x", None), (1, "y", None)],
                     partial_credit=False, spans=[], dk={}),
        hl.MarkedItem(item_id="partial", class_id="A", round_trip_score=0.5, n_orig_spans=2,
                     n_reread_spans=2, residual_spans=[(1, "y", "z")], partial_credit=True,
                     spans=[], dk={}),
        hl.MarkedItem(item_id="solved", class_id="A", round_trip_score=1.0, n_orig_spans=2,
                     n_reread_spans=2, residual_spans=[], partial_credit=False, spans=[], dk={}),
    ]
    ws = hl.assign(marked)
    marked_ids = {m.item_id for m in marked}
    worksheet_ids = {wi.item_id for wi in ws.items}
    assert worksheet_ids <= marked_ids, "every worksheet item must come FROM marking"
    # And it must specifically be a RESIDUAL item (score < 1.0), never a solved one.
    marked_by_id = {m.item_id: m for m in marked}
    assert all(marked_by_id[i].round_trip_score < 1.0 for i in worksheet_ids)


# ===========================================================================
# Gate 2 — frontier scheduling (zone of proximal development): partial only.
# ===========================================================================
def test_frontier_scheduling_excludes_solved_and_zero():
    marked = [
        hl.MarkedItem(item_id="zero", class_id="A", round_trip_score=0.0, n_orig_spans=1,
                     n_reread_spans=0, residual_spans=[(0, "x", None)], partial_credit=False,
                     spans=[], dk={}),
        hl.MarkedItem(item_id="partial", class_id="A", round_trip_score=0.4, n_orig_spans=2,
                     n_reread_spans=2, residual_spans=[(1, "y", "z")], partial_credit=True,
                     spans=[], dk={}),
        hl.MarkedItem(item_id="solved", class_id="A", round_trip_score=1.0, n_orig_spans=1,
                     n_reread_spans=1, residual_spans=[], partial_credit=False, spans=[], dk={}),
    ]
    ws = hl.assign(marked)
    assert [wi.item_id for wi in ws.items] == ["partial"], (
        f"the worksheet must contain EXACTLY the partial-credit item(s), got "
        f"{[wi.item_id for wi in ws.items]!r}")


def test_frontier_scheduling_capacity_orders_by_residual_magnitude():
    """Under a `capacity` cap, the LARGEST residual (lowest score) is scheduled first --
    a repeated held Argmax over (1 - score, index), never a Python sort by score."""
    marked = [
        hl.MarkedItem(item_id="small_gap", class_id="A", round_trip_score=0.9, n_orig_spans=2,
                     n_reread_spans=2, residual_spans=[(1, "y", "z")], partial_credit=True,
                     spans=[], dk={}),
        hl.MarkedItem(item_id="big_gap", class_id="A", round_trip_score=0.2, n_orig_spans=2,
                     n_reread_spans=2, residual_spans=[(1, "y", "z")], partial_credit=True,
                     spans=[], dk={}),
        hl.MarkedItem(item_id="mid_gap", class_id="A", round_trip_score=0.5, n_orig_spans=2,
                     n_reread_spans=2, residual_spans=[(1, "y", "z")], partial_credit=True,
                     spans=[], dk={}),
    ]
    ws = hl.assign(marked, capacity=2)
    assert {wi.item_id for wi in ws.items} == {"big_gap", "mid_gap"}, (
        f"capacity must keep the LARGEST residuals first: {[w.item_id for w in ws.items]!r}")


# ===========================================================================
# Gate 3 — babble improves round-trip on a real, induced instability; corrections applied.
# ===========================================================================
def test_babble_improves_round_trip_on_induced_instability():
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)

    marked = hl.mark(s, items, dk=dk)
    before = marked[0]
    assert 0.0 < before.round_trip_score < 1.0, (
        f"the fixture must show a genuine PARTIAL round-trip residual before babble, got "
        f"{before.round_trip_score!r} -- the empirical basis for this gate has drifted")

    ws = hl.assign(marked)
    assert len(ws.items) == 1

    log = hl.babble(s, ws, reps_per_item=6, rng_seed=1, jitter_bins=0)
    entry = log.per_item["corner0"]
    assert entry["corrections"], "babble must have applied at least one self-correction"
    correction_types = {c["type"] for c in entry["corrections"]}
    assert "mint_at_instability" in correction_types or "stability_rerank" in correction_types

    assert entry["round_trip_after"] > entry["round_trip_before"], (
        f"round-trip score must IMPROVE after babble: before={entry['round_trip_before']!r} "
        f"after={entry['round_trip_after']!r}")

    # Re-marking confirms the improvement is REAL (reflected in the graph), not just the
    # babble-internal after-check.
    remarked = hl.mark(s, items, dk=dk)
    assert remarked[0].round_trip_score >= before.round_trip_score


def test_babble_no_corrections_on_already_solved_item_is_a_noop():
    """A worksheet built from a SOLVED item never reaches babble (gate 2's own frontier
    filter already excludes it) -- confirms assign() really is the gate, not babble()."""
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)
    marked = hl.mark(s, items, dk=dk)
    # Force a perfect score to simulate an already-solved item reaching assign().
    solved = hl.MarkedItem(item_id=marked[0].item_id, class_id=marked[0].class_id,
                          round_trip_score=1.0, n_orig_spans=marked[0].n_orig_spans,
                          n_reread_spans=marked[0].n_reread_spans, residual_spans=[],
                          partial_credit=False, spans=marked[0].spans, dk=marked[0].dk)
    ws = hl.assign([solved])
    assert ws.items == []


# ===========================================================================
# Gate 4 — teacher information falls across cycles (fully self-correctable -> reaches 0).
# ===========================================================================
def test_cycle_surviving_residual_falls_and_reaches_zero():
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)

    marked_before_any = hl.mark(s, items, dk=dk)
    surviving_baseline = sum(1 for m in marked_before_any if m.round_trip_score < 1.0)
    assert surviving_baseline == 1, "the fixture must start with a real, marked residual"

    report1 = hl.cycle(s, items, reps_per_item=6, rng_seed=1, dk=dk, jitter_bins=0)
    assert report1.corrections > 0, "cycle 1 must have actually corrected something"
    assert report1.surviving_residual_count <= report1.surviving_residual_count_before

    report2 = hl.cycle(s, items, reps_per_item=6, rng_seed=1, dk=dk, jitter_bins=0)
    assert report2.surviving_residual_count <= report1.surviving_residual_count, (
        "teacher-information metric (surviving residuals) must not RISE across cycles")

    # The synthetic set is fully self-correctable (empirically verified): reaches 0.
    assert report1.surviving_residual_count == 0
    assert report2.surviving_residual_count == 0


# ===========================================================================
# Gate 5 — eval isolation: mark()/babble() hard-raise on a held-out class.
# ===========================================================================
def test_eval_isolation_raises_on_mark():
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)
    with pytest.raises(hl.EvalLeakageError):
        hl.mark(s, items, dk=dk, eval_class_ids={"A"})


def test_eval_isolation_raises_on_babble():
    wi = hl.WorksheetItem(item_id="x", class_id="EVAL_CLASS", round_trip_score=0.5,
                          residual_spans=[], spans=[], dk=hl._default_dk())
    ws = hl.Worksheet(items=[wi])
    s, ag, native = _boot()
    with pytest.raises(hl.EvalLeakageError):
        hl.babble(s, ws, reps_per_item=1, rng_seed=0, eval_class_ids={"EVAL_CLASS"})


def test_eval_isolation_is_a_noop_when_class_not_held_out():
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)
    # Must NOT raise -- "A" is not in the (unrelated) eval set.
    marked = hl.mark(s, items, dk=dk, eval_class_ids={"SOME_OTHER_CLASS"})
    assert len(marked) == 1


# ===========================================================================
# Gate 6 — no-Python-decision source audit (mirrors
# test_ink_decode_migrated.py::test_ink_decode_no_python_decisions exactly).
# ===========================================================================
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")
# ALLOWLIST: ordering already-decided (start, end, name) triples by POSITION
# (`_spans_from_result`'s `items.sort(key=lambda x: x[0])`) is not a decision -- the SAME
# allowlisted pattern `test_ink_decode_migrated.py`'s own gate 6 establishes.
_ALLOWED_SORT_KEYS = {"x[0]", "x[1]"}


def test_homework_loop_no_python_decisions():
    src = Path(hl.__file__).read_text()

    assert not _BANNED_CALL_RE.search(src), (
        "homework_loop.py must not call argmin/argmax in Python -- every ranking choice is "
        "a held Term (Argmax/Argmin JSON), never a Python argmin/argmax over scores")
    assert not _MINMAX_KEY_RE.search(src), (
        "homework_loop.py must not use Python's builtin min()/max(key=...) as a scoring "
        "decision either")

    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, (
        f"sort(key=...) over an apparent SCORE expression found: {violations!r}")

    # No isinstance(..., list) filter anywhere -- native.evaluate() returns TUPLES, and an
    # isinstance(list) filter has silently disabled minting elsewhere in this codebase before
    # (see domains/ink_decode.py's own module-docstring note) -- gate 7's static half.
    for m in re.finditer(r"isinstance\(([^)]*)\)", src):
        args = m.group(1)
        assert "list" not in args, f"isinstance(..., list) found: {m.group(0)!r}"


# ===========================================================================
# Gate 7 — tuple-robustness: native.evaluate() results (Rust sequences -> Python tuples)
# must never be silently dropped by a list-only assumption.
# ===========================================================================
def test_round_trip_score_handles_tuple_inputs_live():
    s, ag, native = _boot()
    # Feed TUPLES (not lists) where a caller might otherwise assume lists -- the exact shape
    # a live `native.evaluate()` call returns for a sequence result.
    orig_names = ("a", "b", "c")
    re_names = ("a", "x", "c")
    score, residual = hl._round_trip_score(s, native, orig_names, re_names)
    assert score == pytest.approx(2.0 / 3.0)
    assert len(residual) == 1 and residual[0][0] == 1


def test_residual_pairs_term_result_is_consumed_without_list_assumption():
    s, ag, native = _boot()
    pairs = [(0, "a", "a"), (1, "b", "z")]
    result = native.evaluate(hl._residual_pairs_term(pairs), {})
    # A live Rust Tuple sequence result -- must not be a `list` (confirms the test is
    # actually exercising the tuple-surfacing behaviour homework_loop.py must tolerate).
    assert not isinstance(result, list)
    normalized = [tuple(r) for r in result]
    assert normalized == [(1, "b", "z")]


# ===========================================================================
# Gate 8 — babble touches NO real ink: API-shape guarantee, not a runtime check.
# ===========================================================================
def test_worksheet_item_and_span_parse_carry_no_raw_ink_points():
    forbidden = {"points", "raw_points", "pts", "ink_points"}
    span_fields = {f.name for f in fields(hl.SpanParse)}
    worksheet_fields = {f.name for f in fields(hl.WorksheetItem)}
    assert not (span_fields & forbidden), f"SpanParse must carry no raw ink field: {span_fields!r}"
    assert not (worksheet_fields & forbidden), (
        f"WorksheetItem must carry no raw ink field: {worksheet_fields!r}")


def test_babble_signature_takes_no_ground_ink_items():
    sig = inspect.signature(hl.babble)
    param_names = set(sig.parameters)
    assert not (param_names & {"items", "ground_items", "points"}), (
        f"babble() must not accept a raw-ink/ground-items parameter at all: {param_names!r}")


def test_babble_runs_from_worksheet_alone_no_ink_sentinel():
    """Construct a worksheet from a real mark() pass, then discard the original `items` list
    entirely (never pass it to babble) -- babble must still run to completion purely off the
    worksheet's own stored parses."""
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)
    marked = hl.mark(s, items, dk=dk)
    ws = hl.assign(marked)
    del items                          # the real ink is now unreachable from this scope.
    log = hl.babble(s, ws, reps_per_item=3, rng_seed=2, jitter_bins=0)
    assert "corner0" in log.per_item


# ===========================================================================
# Sanity: dk propagation / MarkedItem shape basics on the live fixture.
# ===========================================================================
def test_mark_reports_span_counts_and_dk():
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)
    marked = hl.mark(s, items, dk=dk)
    m = marked[0]
    assert m.item_id == "corner0"
    assert m.class_id == "A"
    assert m.n_orig_spans == 2
    assert m.dk["turn_bins"] == dk["turn_bins"]
    assert all(isinstance(sp, hl.SpanParse) for sp in m.spans)
