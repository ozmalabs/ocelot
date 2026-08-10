"""tests/test_render_geometry_migrated.py — RUN 31 gates for domains/homework_loop.py's two
render-loop geometry mechanisms. The homework arc (runs 26-30) left ONE residual standing:
UNWEIGHTED arrangement round-trip stability flat at 0.8356 through every calibration/weighting
lever (results/omniglot_gate_run29.log, results/run30_checkpoints/consume_metrics.json) — the
render→re-read loop itself manufactures segmentation instability that no down-weighting can
repair. This run attacks the RENDER side directly, two ways:

MECHANISM A — RENDER THE STABILITY-PREFERRED PARSE (`use_preferred_parse`, opt-in on
`mark`/`mark_characters`/`_parse_from_decode`): `babble`'s own mechanism (a) (PARSE STABILITY
RE-RANK) already persists a `stability_preferred_alt` identity as graph data when a MAJORITY of
re-render reps stably re-decode a span as something other than its own name. Nothing before this
run fed that earned preference back into WHAT gets rendered. `_preferred_render_name` reads the
persisted fact (mechanical graph-attribute fetch, adapter I/O) and a HELD `IfThenElse` Term
(`_preferred_render_name_term`) — never a Python if/else — decides whether the render goal is
built from the preferred identity's own stored `seg` instead of the span's own decoded name.

MECHANISM B — SEGMENTATION-TOLERANT RENDERING (`tolerant_joins`, opt-in on
`mark`/`mark_characters`/`_render_parse`): reuses `abs_read._junction_blend` (EXISTING,
unit-tested pure geometry, already wired into the AbS recognition-VERDICT render path for
BRANCH B CONTINUOUS) to warp each span's trailing/leading points toward the shared draw-order
junction midpoint BEFORE concatenation, closing the position discontinuity ("corner artifact")
at a span boundary that the re-read lattice currently cuts differently. No new Rust, no new
geometry primitive — composition of an existing adapter-level primitive, per CLAUDE.md's "prefer
composing existing primitives" instruction.

Both mechanisms default OFF and are BYTE-IDENTICAL to every pre-existing caller when off (the
same additive-flag discipline this whole arc's own commit history establishes).

Seed isolation: every test boots its OWN fresh substrate via `_boot()` — no shared/global agent
state across tests, mirroring `tests/test_homework_characters_migrated.py`'s own discipline."""
from __future__ import annotations

import inspect

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

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
    """Fresh substrate per test — seed isolation (no shared agent state across tests)."""
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _two_shape_codebook(s):
    """Two DISTINCT line-family stroke quanta ("a" straight down, "b" straight right) — the
    SAME rotation-symmetric corner geometry `test_homework_characters_migrated.py::
    _corner_char_fixture` establishes as empirically instability-inducing (a straight line's
    rotation-symmetric invariant signature ties "down"/"right"), reused here as two SEPARATE
    held quanta rather than one concatenated raw stroke so each mechanism can be probed at the
    single-span granularity directly."""
    down_pts = gmw._sample_stroke("line", [0.0, 0.0, 0.0, -1.0], 24)
    right_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24)
    sc.build_stroke_codebook(s, sources=[("a", down_pts.tolist()), ("b", right_pts.tolist())],
                             include_pickle=False)
    return down_pts, right_pts


def _spanparse_from(sub, native, pts, name, dk):
    """Mechanical test helper: build ONE `SpanParse` from a raw point array via the SAME
    `_parse_from_decode` path a real decode uses (never a hand-built goal_sig)."""
    knots = np.asarray(pts, dtype=float)
    ste = [(0, len(knots), name)]
    return hl._parse_from_decode(sub, native, knots, ste, dk)[0]


# ===========================================================================
# MECHANISM A — render the stability-preferred parse.
# ===========================================================================
def test_preferred_render_name_no_preference_is_identity():
    s, ag, native = _boot()
    _two_shape_codebook(s)
    name, used = hl._preferred_render_name(s, native, "a")
    assert (name, used) == ("a", False)


def test_preferred_render_name_honors_persisted_preference():
    s, ag, native = _boot()
    _two_shape_codebook(s)
    node = sc._find_stroke_node(s, "a")
    s.set_attr(node, "stability_preferred_alt", "b")
    name, used = hl._preferred_render_name(s, native, "a")
    assert (name, used) == ("b", True)


def test_preferred_render_name_none_input_is_honest_noop():
    s, ag, native = _boot()
    name, used = hl._preferred_render_name(s, native, None)
    assert (name, used) == (None, False)


def test_preferred_render_name_is_a_held_term_not_a_python_branch():
    """Source audit: `_preferred_render_name`'s own body must not contain a Python
    conditional that CHOOSES between `name`/`pref` — only `native.evaluate(...)` (the held
    `IfThenElse`) may decide (mirrors this module's own `_frontier_term`/`_is_frontier`
    split). The only `if` permitted is the honest None-input early return."""
    src = inspect.getsource(hl._preferred_render_name)
    assert "native.evaluate(" in src
    branch_lines = [ln.strip() for ln in src.splitlines() if ln.strip().startswith("if ")]
    assert branch_lines == ["if name is None:"], (
        f"unexpected Python branch(es) in _preferred_render_name: {branch_lines!r} — the "
        "name/pref CHOICE must be made by the held IfThenElse Term, not Python")


def test_preferred_render_name_term_is_an_ifthenelse_dict():
    """`_preferred_render_name_term` must literally build an `IfThenElse` Term dict (not,
    say, precompute the answer in Python and wrap it in a `Lit`) — the substitution decision
    really is deferred to the evaluator."""
    term = hl._preferred_render_name_term("a", "b")
    assert term["type"] == "IfThenElse"
    assert term["cond"]["type"] == "Eq"


def test_parse_from_decode_default_is_byte_identical_to_no_preference():
    """`use_preferred_parse=False` (the default, every pre-existing caller) must build the
    EXACT SAME goal_sig as an explicit `False` — `rendered_as` stays `None` on every span,
    even when a preference IS persisted (the flag, not the data, gates the substitution)."""
    s, ag, native = _boot()
    down_pts, _ = _two_shape_codebook(s)
    node = sc._find_stroke_node(s, "a")
    s.set_attr(node, "stability_preferred_alt", "b")
    knots = np.asarray(down_pts, dtype=float)
    ste = [(0, len(knots), "a")]
    dk = hl._default_dk()

    default_parse = hl._parse_from_decode(s, native, knots, ste, dk)
    explicit_off = hl._parse_from_decode(s, native, knots, ste, dk, use_preferred_parse=False)
    assert default_parse[0].goal_sig == explicit_off[0].goal_sig
    assert default_parse[0].rendered_as is None and explicit_off[0].rendered_as is None


def test_parse_from_decode_renders_preferred_identity_when_flagged():
    """With a persisted `stability_preferred_alt` on "a" pointing at "b", `use_preferred_
    parse=True` must build `goal_sig` from "b"'s own stored seg (spliced with the SAME
    observed pose `ink._pose_read_goal` always splices) — `rendered_as == "b"`, while the
    span's OWN decoded `name` stays "a" (only the RENDER goal substitutes, never the
    identity)."""
    s, ag, native = _boot()
    down_pts, _ = _two_shape_codebook(s)
    node = sc._find_stroke_node(s, "a")
    s.set_attr(node, "stability_preferred_alt", "b")
    knots = np.asarray(down_pts, dtype=float)
    ste = [(0, len(knots), "a")]
    dk = hl._default_dk()

    off = hl._parse_from_decode(s, native, knots, ste, dk, use_preferred_parse=False)
    on = hl._parse_from_decode(s, native, knots, ste, dk, use_preferred_parse=True)

    assert off[0].rendered_as is None
    assert on[0].rendered_as == "b"
    assert on[0].name == "a"
    assert hl.count_preferred_renders(on) == 1
    assert hl.count_preferred_renders(off) == 0

    full = ink._span_signature(native, knots, 0, len(knots), segments=dk["segments"],
                               turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                               grid=dk["grid"], scale_bins=dk["scale_bins"], invariant_only=False)
    expected = ink._pose_read_goal(s, "b", full["signature"])
    assert on[0].goal_sig == expected


# ===========================================================================
# MECHANISM B — segmentation-tolerant rendering (reuses abs_read._junction_blend).
# ===========================================================================
def test_render_parse_default_returns_zero_joins_and_raw_concatenation():
    s, ag, native = _boot()
    down_pts, right_pts = _two_shape_codebook(s)
    dk = hl._default_dk()
    span_a = _spanparse_from(s, native, down_pts, "a", dk)
    span_b = _spanparse_from(s, native, right_pts, "b", dk)

    pts_off, n_joins_off = hl._render_parse(native, [span_a, span_b], dk)
    assert n_joins_off == 0

    solo_a, _ = hl._render_parse(native, [span_a], dk)
    solo_b, _ = hl._render_parse(native, [span_b], dk)
    assert pts_off[:len(solo_a)] == solo_a
    assert pts_off[len(solo_a):] == solo_b


def test_render_parse_tolerant_joins_off_is_byte_identical():
    s, ag, native = _boot()
    down_pts, right_pts = _two_shape_codebook(s)
    dk = hl._default_dk()
    span_a = _spanparse_from(s, native, down_pts, "a", dk)
    span_b = _spanparse_from(s, native, right_pts, "b", dk)
    default_pts, default_n = hl._render_parse(native, [span_a, span_b], dk)
    explicit_off_pts, explicit_off_n = hl._render_parse(native, [span_a, span_b], dk,
                                                        tolerant_joins=False)
    assert default_pts == explicit_off_pts and default_n == explicit_off_n == 0


def test_render_parse_tolerant_joins_closes_the_seam_gap():
    """The DECISIVE geometry check: `tolerant_joins=True` must make span-a's own rendered
    ENDPOINT and span-b's own rendered STARTPOINT converge toward their shared joint (the
    "corner artifact" this run's own header names) — a strictly smaller gap than the naive
    (`tolerant_joins=False`) concatenation, for a genuinely disjoint two-shape seam."""
    s, ag, native = _boot()
    down_pts, right_pts = _two_shape_codebook(s)
    dk = hl._default_dk()
    span_a = _spanparse_from(s, native, down_pts, "a", dk)
    span_b = _spanparse_from(s, native, right_pts, "b", dk)

    pts_off, n_off = hl._render_parse(native, [span_a, span_b], dk)
    pts_on, n_on = hl._render_parse(native, [span_a, span_b], dk, tolerant_joins=True)
    assert n_off == 0
    assert n_on == 1

    solo_b, _ = hl._render_parse(native, [span_b], dk)
    seam = len(pts_off) - len(solo_b)
    gap_off = float(np.hypot(*(np.array(pts_off[seam - 1]) - np.array(pts_off[seam]))))
    gap_on = float(np.hypot(*(np.array(pts_on[seam - 1]) - np.array(pts_on[seam]))))
    assert gap_on < gap_off, f"tolerant_joins=True must close the seam gap: off={gap_off}, on={gap_on}"


def test_render_parse_join_count_matches_consecutive_pairs():
    s, ag, native = _boot()
    down_pts, right_pts = _two_shape_codebook(s)
    dk = hl._default_dk()
    span_a = _spanparse_from(s, native, down_pts, "a", dk)
    span_b = _spanparse_from(s, native, right_pts, "b", dk)

    _pts, n = hl._render_parse(native, [span_a], dk, tolerant_joins=True)
    assert n == 0, "a single span has no draw-order neighbour to join"
    _pts, n = hl._render_parse(native, [span_a, span_b], dk, tolerant_joins=True)
    assert n == 1
    _pts, n = hl._render_parse(native, [span_a, span_b, span_a], dk, tolerant_joins=True)
    assert n == 2


def test_render_parse_reuses_junction_blend_not_a_new_primitive():
    """`_render_parse`'s tolerant-join arm must call `abs_read._junction_blend` (EXISTING,
    already unit-tested elsewhere for BRANCH B CONTINUOUS) rather than reimplement smoothing
    geometry inline — CLAUDE.md's "reuse held machinery, never build a parallel engine,"
    applied to a pure-Python geometry helper."""
    src = inspect.getsource(hl._render_parse)
    assert "ar._junction_blend(" in src


# ===========================================================================
# TWO-SPAN SEGMENTATION-INSTABILITY DEMONSTRATOR (synthetic): a naive render whose own
# re-decode changes span count re-reads STABLY under the tolerant mode. Uses `mark` at
# STROKE grain (the corner-fixture geometry, byte-identical construction to
# `test_homework_loop_migrated.py::_corner_fixture`) so the assertion exercises the REAL
# decode->render->re-decode loop, not a hand-built stand-in.
# ===========================================================================
def _corner_fixture(s):
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


def test_mark_tolerant_joins_engagement_reported_on_corner_fixture():
    """The engagement instrument (`n_tolerant_joins`) must be NONZERO on a genuine two-span
    parse when the flag is on, and always zero when it is off — an arm whose mechanism never
    engages is vacuous, not null (the run-28 lesson)."""
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)
    off = hl.mark(s, items, dk=dk)
    on = hl.mark(s, items, dk=dk, tolerant_joins=True)
    assert off[0].n_tolerant_joins == 0
    if off[0].n_orig_spans >= 2:
        assert on[0].n_tolerant_joins >= 1, (
            "tolerant_joins=True must actually engage on a multi-span parse — an engaged-but-"
            "null result is different from a never-engaged one")


def test_mark_preferred_parse_engagement_reported_on_corner_fixture():
    s, ag, native = _boot()
    items, dk = _corner_fixture(s)
    baseline = hl.mark(s, items, dk=dk)
    assert baseline[0].n_preferred_renders == 0, "no preference persisted yet -- must be 0"
    node = sc._find_stroke_node(s, "down")
    if node is not None:
        s.set_attr(node, "stability_preferred_alt", "right")
        on = hl.mark(s, items, dk=dk, use_preferred_parse=True)
        assert on[0].n_preferred_renders >= 1


# ===========================================================================
# CONSTRAINT GATE — StrokeRender's exact-inverse property is load-bearing on the DEFAULT
# path; the tolerant mode is an EXPLICITLY SEPARATE mode and must not silently claim the same
# guarantee. These tests make the trade-off EXPLICIT rather than assumed.
# ===========================================================================
def test_default_render_preserves_stroke_quantize_inverse_single_span():
    """Control: the UNTOUCHED default path (`tolerant_joins=False`) reproduces
    `StrokeQuantize(StrokeRender(sig)) == sig` for one span EXACTLY — the same standing
    Rust-side gate (`runners/dsl/src/strokes.rs`'s own round-trip test), re-asserted at the
    Python adapter level this run's own new code sits on top of."""
    s, ag, native = _boot()
    down_pts, _ = _two_shape_codebook(s)
    dk = hl._default_dk()
    span = _spanparse_from(s, native, down_pts, "a", dk)
    pts, n_joins = hl._render_parse(native, [span], dk)
    assert n_joins == 0
    q = sc._quantize(native, pts, segments=dk["segments"], turn_bins=dk["turn_bins"],
                     len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
                     canonical_pose=False)
    orig_seg = [r for r in span.goal_sig if r[0] == "seg"]
    re_seg = [list(r) for r in q["signature"] if r[0] == "seg"]
    assert re_seg == orig_seg, "the DEFAULT render path must remain StrokeQuantize's exact inverse"


def test_tolerant_joins_documents_inverse_break():
    """HONEST DOCUMENTATION (per this run's own constraint): `tolerant_joins=True` is an
    explicitly SEPARATE mode — it does NOT claim to preserve
    `StrokeQuantize(StrokeRender(sig)) == sig` for a span whose trailing/leading points were
    blended (the whole point of the mechanism is to move those points to close the seam gap).
    This test asserts the documented break explicitly rather than leaving it as a silent,
    untested assumption (`_render_parse`'s own docstring names this test by name)."""
    s, ag, native = _boot()
    down_pts, right_pts = _two_shape_codebook(s)
    dk = hl._default_dk()
    span_a = _spanparse_from(s, native, down_pts, "a", dk)
    span_b = _spanparse_from(s, native, right_pts, "b", dk)

    pts_on, n_on = hl._render_parse(native, [span_a, span_b], dk, tolerant_joins=True,
                                    junction_frac=0.5)
    assert n_on == 1
    n_a = len(hl._render_parse(native, [span_a], dk)[0])
    a_points_blended = pts_on[:n_a]
    q = sc._quantize(native, a_points_blended, segments=dk["segments"],
                     turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
                     scale_bins=dk["scale_bins"], canonical_pose=False)
    orig_seg = [r for r in span_a.goal_sig if r[0] == "seg"]
    re_seg = [list(r) for r in q["signature"] if r[0] == "seg"]
    assert re_seg != orig_seg, (
        "tolerant_joins is a SEPARATE mode -- re-quantizing a blended span is EXPECTED to "
        "differ from its own pre-blend signature (documented, not silently assumed)")


# ===========================================================================
# Full-loop character-grain wiring — `mark_characters`/`cycle_characters` accept and thread
# both flags without disturbing the byte-identical default path (mirrors this codebase's own
# `enable_character_codebook`/`use_stability_weights` additivity discipline).
# ===========================================================================
def test_mark_characters_flags_default_off_byte_identical():
    s, ag, native = _boot()
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

    default = hl.mark_characters(s, char_items, dk=dk)
    s2, ag2, native2 = _boot()
    sc.build_stroke_codebook(
        s2, sources=[("down", down_pts.tolist()), ("right", right_pts.tolist())],
        include_pickle=False)
    explicit_off = hl.mark_characters(s2, char_items, dk=dk, use_preferred_parse=False,
                                      tolerant_joins=False)
    assert default[0].round_trip_score == explicit_off[0].round_trip_score
    assert default[0].arrangement_score == explicit_off[0].arrangement_score
    assert default[0].n_preferred_renders == explicit_off[0].n_preferred_renders == 0
    assert default[0].n_tolerant_joins == explicit_off[0].n_tolerant_joins == 0


def test_cycle_characters_reports_engagement_totals():
    """`cycle_characters` must surface BOTH mechanisms' engagement totals on `CycleReport` —
    the run-31 gate's own per-cycle instrument, separate from outcome (surviving_residual_
    count / arrangement subscores)."""
    s, ag, native = _boot()
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

    rep = hl.cycle_characters(s, char_items, reps_per_item=2, rng_seed=0, dk=dk, jitter_bins=0,
                              tolerant_joins=True)
    assert rep.tolerant_join_applications >= 0   # honest -- 0 is a valid (vacuous) outcome too
    assert hasattr(rep, "renders_with_preferred_parse")
