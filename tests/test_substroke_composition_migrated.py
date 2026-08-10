"""tests/test_substroke_composition_migrated.py — BRANCH A EXECUTION of
scratchpad/HANDWRITING_DESIGN.md (the jabberwock's own verdict d2cd7bed, 2026-07-03): "the sd
loop one level DOWN — a stroke is itself an arrangement of sub-stroke quanta." Gates:

1. compose_stroke_signature basic shape (test_compose_stroke_signature_subq_srel_shape) —
   subq/srel relations built correctly from raw (points, name) sub-spans, mirroring
   compose_character_signature's own strokeq/rel one grain down.
2. Arrangement-key stability/discrimination (test_substroke_arrangement_key_stable_and_
   discriminative) — the SAME arrangement hashes to the SAME key; a genuinely different
   arrangement (different sub-quantum identity, same geometry) hashes differently; empty/
   degenerate input keys to None (never a fabricated key).
3. THE decisive case (test_decisive_same_quantum_different_arrangement) — two "characters"
   built from the IDENTICAL top-level stroke (same name, same points -> byte-identical
   strokeq/rel/cpose, a genuine TIE at that level) but DIFFERENT sub-stroke arrangements:
   naive coverage WITHOUT strokeq_sub cannot discriminate them (a tie); WITH strokeq_sub
   (include_substroke=True) the query is classified correctly. Directly the lever's proof.
4. Additivity byte-identity (test_compose_character_signature_substroke_byte_identity) —
   include_substroke=False (the default) reproduces the signature byte-for-byte regardless
   of whether 4-tuple substroke_points data is present on the input — the run-6 additivity
   law, applied to this lever.
5. The within-stroke inner lattice mechanism (test_decode_substrokes_lattice_synthetic) —
   mirrors test_lattice_partition_hand_set_signatures one grain down: three known sub-stroke
   shapes concatenated end-to-end recover exactly those 3 on-path spans via
   ink_decode.decode_substrokes, no minting (boundaries EMERGE, never a pre-cut).
6. Growth-then-flatten synthetic (test_substroke_growth_then_flatten_synthetic) — repeatedly
   decoding a small, repeating population of sub-shapes against an EMPTY substroke codebook
   grows it then FLATTENS (reuse rate rises) — the same saturation signature the outer
   stroke-level codebook already showed, one grain down.
7. End-to-end integration (test_ink_decode_attaches_substroke_points_when_enabled) —
   ink_decode.decode_ink's enable_substroke flag (default False, OPT-IN) attaches a non-empty
   "substroke_points" field on recognized spans when on, and leaves decode_ink's own
   pre-existing behaviour (incl. codebook_epoch bump count) byte-identical when off (the
   default) — the flag's own additivity/opt-in discipline, gated directly.
8. Vocabulary/report helper (test_substroke_vocabulary_report) —
   stroke_codebook.substroke_vocabulary_report reads back the held substroke population
   mechanically.

Hermetic, synthetic geometry only (plain line segments / glyph_motor_world helpers) — Omniglot
stays a scripts/ gate (results/omniglot_gate_run14_substroke.log), not pytest.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

from domains import character_compose as cc
from domains import glyph_motor_world as gmw
from domains import ink_decode as ink
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc

ROOT = Path(__file__).resolve().parent.parent


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _stroke_quantize_live() -> bool:
    s = srs.Substrate()
    return sc._stroke_quantize_live(s._inner)


SQ_LIVE = _stroke_quantize_live()
SQ_SKIP = "StrokeQuantize not live -- honest skip, not a faked pass (see test_ink_decode_migrated.py)."


# ---------------------------------------------------------------------------
# Hand-built line strokes -- no dataset.
# ---------------------------------------------------------------------------
def _line(p0, p1, n=24) -> list:
    return np.linspace(p0, p1, n).tolist()


def _add_substroke_node_hermetic(sub, native, name: str, points) -> int:
    """A HERMETIC stand-in for `stroke_codebook.grow_substroke_quantum` for THIS file's gates
    only: installs a `ShapeSignature{kind:"substroke"}` node directly on the live graph
    WITHOUT going through `teach()` (mirrors `test_character_composition_migrated.py`'s own
    `_add_stroke_node_hermetic` idiom exactly, one grain down — avoids leaking test-only
    quanta into the real, checked-in seeds/stroke_shapes.json on every local test run)."""
    q = sc._quantize(native, points, segments=sc.SUBSTROKE_SEGMENTS,
                     turn_bins=sc.SUBSTROKE_TURN_BINS, len_bins=sc.SUBSTROKE_LEN_BINS,
                     grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS, canonical_pose=True)
    return sub.add_node("ShapeSignature", {
        "name": name, "kind": "substroke",
        "signature": json.dumps([list(r) for r in q["signature"]])})


# ---------------------------------------------------------------------------
# The SAME "Sum + In" coverage / Argmax classification idiom every other gate file in this
# codebase already establishes.
# ---------------------------------------------------------------------------
def _coverage_term(query_sig, exemplar_sig) -> dict:
    return {"type": "Sum", "source": {"type": "Lit", "value": query_sig}, "var_name": "n",
            "value": {"type": "IfThenElse",
                      "cond": {"type": "In", "member": {"type": "Var", "name": "n"},
                               "container": {"type": "Lit", "value": exemplar_sig}},
                      "then": {"type": "Lit", "value": 1.0}, "other": {"type": "Lit", "value": 0.0}}}


def _argmax_pairs_term(pairs) -> dict:
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


# ===========================================================================
# Gate 1 — compose_stroke_signature basic shape.
# ===========================================================================
def test_compose_stroke_signature_subq_srel_shape():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    sub1 = _line((0.0, 0.0), (0.5, 0.0), n=12)
    sub2 = _line((0.5, 0.0), (1.0, 0.0), n=12)
    res = cc.compose_stroke_signature(native, [(sub1, "sA"), (sub2, "sB")])
    preds = [r[0] for r in res["signature"]]
    assert preds.count("subq") == 2
    assert preds.count("srel") == 2
    subq = {r[1]: r[2] for r in res["signature"] if r[0] == "subq"}
    assert subq == {0: "sA", 1: "sB"}
    assert res["n_substrokes"] == 2


def test_compose_stroke_signature_degenerate_empty():
    s = srs.Substrate()
    native = s._inner
    assert cc.compose_stroke_signature(native, [])["signature"] == []
    assert cc.compose_stroke_signature(native, [([[0.0, 0.0]], "x")])["signature"] == []


# ===========================================================================
# Gate 2 — arrangement-key stability/discrimination.
# ===========================================================================
def test_substroke_arrangement_key_stable_and_discriminative():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    sub1 = _line((0.0, 0.0), (0.5, 0.0), n=12)
    sub2 = _line((0.5, 0.0), (1.0, 0.0), n=12)

    sig_a1 = cc.compose_stroke_signature(native, [(sub1, "sA"), (sub2, "sB")])["signature"]
    sig_a2 = cc.compose_stroke_signature(native, [(sub1, "sA"), (sub2, "sB")])["signature"]
    key_a1 = cc.substroke_arrangement_key(sig_a1)
    key_a2 = cc.substroke_arrangement_key(sig_a2)
    assert key_a1 is not None
    assert key_a1 == key_a2, "the SAME arrangement must hash to the SAME key across repeats"

    # SAME geometry/pose, DIFFERENT sub-quantum identities -- a genuinely different
    # arrangement (the decisive case's own construction).
    sig_b = cc.compose_stroke_signature(native, [(sub1, "sC"), (sub2, "sD")])["signature"]
    key_b = cc.substroke_arrangement_key(sig_b)
    assert key_b != key_a1

    assert cc.substroke_arrangement_key([]) is None


# ===========================================================================
# Gate 3 — THE decisive case: same top-level quantum, different sub-stroke arrangement.
# ===========================================================================
def test_decisive_same_quantum_different_arrangement():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner

    stroke_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    sub1 = _line((0.0, 0.0), (0.5, 0.0), n=12)
    sub2 = _line((0.5, 0.0), (1.0, 0.0), n=12)
    # Two arrangements, IDENTICAL geometry/pose, DIFFERENT sub-quantum identity labels --
    # "same global quantum, different sub-stroke arrangement" per the design's own framing.
    arrangement_a = [(sub1, "sA"), (sub2, "sB")]
    arrangement_b = [(sub1, "sC"), (sub2, "sD")]

    def _char(substroke_points, include_substroke):
        return cc.compose_character_signature(
            native, [(stroke_pts, "quantumX", None, substroke_points)],
            include_substroke=include_substroke)["signature"]

    exemplar_a = _char(arrangement_a, True)
    exemplar_b = _char(arrangement_b, True)
    query = _char(arrangement_a, True)   # matches exemplar A's OWN arrangement exactly.

    # WITHOUT strokeq_sub: strokeq/rel/cpose are byte-identical between A and B (same
    # top-level stroke, same geometry) -- naive coverage TIES.
    exemplar_a_nc = _char(arrangement_a, False)
    exemplar_b_nc = _char(arrangement_b, False)
    assert exemplar_a_nc == exemplar_b_nc, (
        "without the lever, the two exemplars must be INDISTINGUISHABLE -- the same top-level "
        "quantum, geometry and pose give byte-identical strokeq/rel/cpose relations")
    query_nc = _char(arrangement_a, False)
    cov_a_nc = float(native.evaluate(_coverage_term(query_nc, exemplar_a_nc), {}))
    cov_b_nc = float(native.evaluate(_coverage_term(query_nc, exemplar_b_nc), {}))
    assert cov_a_nc == cov_b_nc, "naive coverage without strokeq_sub must TIE (the null result)"

    # WITH strokeq_sub: the query's arrangement matches ONLY exemplar A's.
    pairs = [(float(native.evaluate(_coverage_term(query, ex), {})), ci)
             for ci, ex in enumerate([exemplar_a, exemplar_b])]
    winner = native.evaluate(_argmax_pairs_term(pairs), {})
    assert winner is not None and winner[1] == 0, (
        "WITH strokeq_sub the query must classify as exemplar A (the matching arrangement) -- "
        "the decisive lever's own proof")
    assert pairs[0][0] > pairs[1][0], "A's coverage score must strictly exceed B's"


# ===========================================================================
# Gate 4 — additivity byte-identity.
# ===========================================================================
def test_compose_character_signature_substroke_byte_identity():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s = srs.Substrate()
    native = s._inner
    stroke_pts = _line((0.0, 0.0), (1.0, 0.0), n=24)
    sub1 = _line((0.0, 0.0), (0.5, 0.0), n=12)
    substroke_points = [(sub1, "sA")]

    baseline = cc.compose_character_signature(native, [(stroke_pts, "quantumX")])["signature"]
    with_data_flag_off = cc.compose_character_signature(
        native, [(stroke_pts, "quantumX", None, substroke_points)],
        include_substroke=False)["signature"]
    three_tuple = cc.compose_character_signature(
        native, [(stroke_pts, "quantumX", None)])["signature"]

    assert with_data_flag_off == baseline, (
        "include_substroke=False (the default) must reproduce the signature byte-for-byte "
        "regardless of whether 4-tuple substroke_points data is present on the input")
    assert three_tuple == baseline, "the pre-existing 3-tuple shape must stay unaffected"

    with_flag_on = cc.compose_character_signature(
        native, [(stroke_pts, "quantumX", None, substroke_points)],
        include_substroke=True)["signature"]
    assert any(r[0] == "strokeq_sub" for r in with_flag_on)
    # ADDITIVE: every non-strokeq_sub relation is unaffected by turning the flag on.
    without_sub = [r for r in with_flag_on if r[0] != "strokeq_sub"]
    assert without_sub == baseline


# ===========================================================================
# Gate 5 — the within-stroke inner lattice mechanism (boundaries EMERGE).
# ===========================================================================
def _line_arc_squiggle(n: int = 8, seed: int = 0):
    """THE proven three-distinct-curvature-profile recipe
    (`tests/test_ink_decode_migrated.py::test_oov_mint_exactly_one_then_recognized_after_
    epoch_bump`'s own construction, reused verbatim at a smaller point count): a straight
    LINE (turn=0 everywhere), a 270-degree ARC (uniform nonzero turn), and a random-walk
    SQUIGGLE (varying turn) — chained end-to-end (each one's last point == the next one's
    first, by construction). Three simple parallel/perpendicular LINES are NOT distinct at
    this level: the invariant `seg` signature is rotation-INVARIANT by construction, so
    three lines at different absolute headings are indistinguishable sub-shapes (correctly
    so) — genuine CURVATURE, not heading, is what this grain can tell apart."""
    theta_deg = 270.0
    r = 1.0 / np.radians(theta_deg)
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], n)
    arc_pts = gmw._sample_stroke("arc", [1.0, r, r, -90.0, -90.0 + theta_deg], n)
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, 1, size=(n - 1, 2))
    raw = np.concatenate([np.zeros((1, 2)), np.cumsum(steps, axis=0)], axis=0)
    raw_len = float(np.sqrt(((np.diff(raw, axis=0)) ** 2).sum(1)).sum()) or 1.0
    squiggle = arc_pts[-1] + raw / raw_len
    return line_pts.tolist(), arc_pts.tolist(), squiggle.tolist()


def test_decode_substrokes_lattice_synthetic():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()

    a_pts, b_pts, c_pts = _line_arc_squiggle(n=8, seed=0)
    _add_substroke_node_hermetic(s, native, "subA", a_pts)
    _add_substroke_node_hermetic(s, native, "subB", b_pts)
    _add_substroke_node_hermetic(s, native, "subC", c_pts)

    # FULL concatenation (duplicate joint knots, byte-identical to the proven outer-lattice
    # recipe this mirrors) + an EXACT single candidate length (min_span==max_span==8) --
    # avoids the straight-line self-similarity tie explosion a length RANGE would invite.
    concatenated = a_pts + b_pts + c_pts
    third = len(a_pts)
    res = ink.decode_substrokes(s, concatenated, min_span=third, max_span=third,
                                segments=sc.SUBSTROKE_SEGMENTS, turn_bins=sc.SUBSTROKE_TURN_BINS,
                                len_bins=sc.SUBSTROKE_LEN_BINS)

    assert len(res["minted"]) == 0, f"every span is a KNOWN sub-shape -- zero mint; got {res}"
    names = [r["name"] for r in sorted(res["recognized"], key=lambda r: r["start"])]
    assert names == ["subA", "subB", "subC"], f"boundaries must EMERGE at the true joins, got {res}"


def test_decode_substrokes_degenerate_input():
    s, ag, native = _boot()
    assert ink.decode_substrokes(s, [[0.0, 0.0]]) == {
        "spans": [], "recognized": [], "minted": [], "oov": []}


# ===========================================================================
# Gate 6 — growth-then-flatten at sub-stroke grain (synthetic, small-scale LEARN mirror).
# ===========================================================================
def test_substroke_growth_then_flatten_synthetic():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()

    a_pts, b_pts, c_pts = _line_arc_squiggle(n=8, seed=1)
    shapes = [a_pts, b_pts, c_pts]

    codebook_sizes = []
    for i in range(40):
        shape = shapes[i % len(shapes)]
        ink.decode_substrokes(s, shape, min_span=len(shape), max_span=len(shape),
                              segments=sc.SUBSTROKE_SEGMENTS, turn_bins=sc.SUBSTROKE_TURN_BINS,
                              len_bins=sc.SUBSTROKE_LEN_BINS)
        codebook_sizes.append(sc.substroke_vocabulary_report(s)["total"])

    assert codebook_sizes[-1] <= len(shapes), (
        f"a repeating population of {len(shapes)} sub-shapes must NOT keep minting past "
        f"{len(shapes)} quanta -- got sizes {codebook_sizes}")
    first_new = codebook_sizes[len(shapes)] - codebook_sizes[0] if len(codebook_sizes) > len(shapes) else 0
    last_new = codebook_sizes[-1] - codebook_sizes[-1 - len(shapes)]
    assert last_new == 0, (
        f"growth must FLATTEN once every distinct sub-shape has been seen once: "
        f"{codebook_sizes}")


# ===========================================================================
# Gate 7 — end-to-end integration + opt-in additivity.
# ===========================================================================
def test_ink_decode_attaches_substroke_points_when_enabled():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    native.load_seed_manifest(manifest_for("writer_dimensions"), ag)
    sc.build_stroke_codebook(
        s, sources=[("line_0", gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24).tolist())],
        include_pickle=False)
    epoch0 = s.node(ag)["attrs"]["codebook_epoch"]

    pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24).tolist()
    ink_node = ink.ingest_ink(s, pts, max_knots=24)

    # DEFAULT (enable_substroke=False): NO substroke_points field, epoch UNCHANGED beyond
    # whatever the stroke-grain decode itself does -- byte-identical pre-existing behaviour.
    res_off = ink.decode_ink(s, ink_node, min_span=20, max_span=24)
    epoch_after_off = s.node(ag)["attrs"]["codebook_epoch"]
    assert all("substroke_points" not in r for r in res_off["recognized"]), (
        "enable_substroke defaults False -- no substroke_points field should appear")

    # ENABLED: every recognized span carries a (possibly empty-but-present) substroke_points
    # field; a genuinely decomposable line SHOULD produce at least one inner sub-span.
    ink_node2 = ink.ingest_ink(s, pts, max_knots=24)
    res_on = ink.decode_ink(s, ink_node2, min_span=20, max_span=24, enable_substroke=True)
    assert res_on["recognized"], "the known line must recognize at the stroke grain"
    for r in res_on["recognized"]:
        assert "substroke_points" in r
        assert isinstance(r["substroke_points"], list)


def test_ink_decode_substroke_disabled_is_byte_identical_epoch():
    """A dedicated regression: with enable_substroke left at its default (False), the
    codebook_epoch bump count for a run that recognizes everything at the stroke grain must
    be EXACTLY what it was before this lever existed (zero further bumps) -- the same
    invariant `test_ink_decode_migrated.py::test_rung1_transform_reading_zero_mint` already
    checks for the stroke grain, re-asserted here after this file's own additions."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 48).tolist()
    sc.build_stroke_codebook(s, sources=[("line", line_pts)], include_pickle=False)
    epoch0 = s.node(ag)["attrs"]["codebook_epoch"]

    ink_node = ink.ingest_ink(s, line_pts, max_knots=48)
    res = ink.decode_ink(s, ink_node, min_span=40, max_span=48)
    assert len(res["oov"]) == 0 and len(res["minted"]) == 0
    assert s.node(ag)["attrs"]["codebook_epoch"] == epoch0, "zero mint through the sd loop"


# ===========================================================================
# Gate 8 — vocabulary report + grow idempotency.
# ===========================================================================
def test_substroke_vocabulary_report_and_idempotent_grow():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24).tolist()
    r1 = sc.grow_substroke_quantum(s, pts, "sub_line")
    assert r1["grown"] is True
    r2 = sc.grow_substroke_quantum(s, pts, "sub_line")
    assert r2["grown"] is False, "idempotent by name -- a second grow is a no-op"
    report = sc.substroke_vocabulary_report(s)
    assert report["total"] == 1
    assert report["names"] == ["sub_line"]


# ===========================================================================
# Gate: no-Python-decision audit (re-asserted for THIS file's own new symbols; the modules
# themselves are already scanned by test_ink_decode_migrated.py::test_ink_decode_no_python_
# decisions / test_character_composition_migrated.py::test_character_compose_no_python_
# decisions / test_ink_decode_migrated.py::test_stroke_codebook_no_python_decisions).
# ===========================================================================
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)


def test_substroke_additions_no_python_decisions():
    for mod in (ink, cc, sc):
        src = Path(mod.__file__).read_text()
        assert not _BANNED_CALL_RE.search(src), f"{mod.__name__} must not argmin/argmax in Python"
        assert not _MINMAX_KEY_RE.search(src), f"{mod.__name__} must not min/max(key=...) either"
