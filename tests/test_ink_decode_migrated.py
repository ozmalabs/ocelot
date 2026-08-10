"""tests/test_ink_decode_migrated.py — T of scratchpad/HANDWRITING_DESIGN.md: the 7 gates
for the handwriting instance of dynamic quantization (domains/stroke_codebook.py +
domains/ink_decode.py + seeds/writer_dimensions.json). Hermetic, synthetic ink only
(glyph_motor_world's GLYPHS motor programs + write_with_hand/rotate_traj — no dataset).

LANDING STATUS (2026-07-02): two Rust pieces this suite depends on are being built/fixed in
PARALLEL and were NOT YET LANDED as of this writing:
  - `StrokeQuantize` (the geometry Term itself, including its NEW `canonical_pose` option —
    `domains/stroke_codebook.py`'s codebook-authoring convention depends on it). Probed by
    `_stroke_quantize_live()`.
  - `TransformDecode`'s in-flight fix — pooling per-dimension deltas by `(predicate, slot)`
    instead of a raw global slot index, so the design's literal 4-relation pose schema
    (`pose_x`/`pose_y`/`pose_o`/`pose_s`) composes correctly (an EARLIER pass of
    `domains/ink_decode.py` found, and reported, that it did not compose under the
    PRE-fix semantics — see that module's docstring). Probed by
    `_transformdecode_pools_by_predicate()`.

This file does NOT module-skip: gates that need neither Rust piece (the lattice/emission
mechanism, the writer-dimension RULE, the content-keyed mint dedup, the no-Python-decision
audit) stay live and green regardless. Gates 1/3/4/5 need only `StrokeQuantize`
(`canonical_pose`); gates 2/7 need `TransformDecode`'s fix too (they read pose deltas). Each
gate skips INDIVIDUALLY and honestly when its dependency is missing — never a faked pass.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

from domains import glyph_motor_world as gmw
from domains import ink_decode as ink
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Live-Term probes (per-test skip, not module-level — see module docstring).
# ---------------------------------------------------------------------------
def _stroke_quantize_live() -> bool:
    s = srs.Substrate()
    return sc._stroke_quantize_live(s._inner)


def _transformdecode_pools_by_predicate() -> bool:
    """Probes the IN-FLIGHT TransformDecode fix directly (no StrokeQuantize needed): a PURE
    rotation (only `pose_o`'s own value differs; `seg` + `pose_x`/`pose_y`/`pose_s` all
    identical) must be `explained=True` once dims pool by `(predicate, slot)` rather than a
    raw global slot index — empirically `False` before the fix (see
    `domains/ink_decode.py`'s module docstring)."""
    s = srs.Substrate()
    native = s._inner
    held = _full_sig([(1, 1), (2, 1), (3, 1)], x=4, y=4, o=2, sc_=3)
    s.add_node("ShapeSignature", {"name": "probe", "kind": "stroke", "signature": json.dumps(held)})
    goal = _full_sig([(1, 1), (2, 1), (3, 1)], x=4, y=4, o=7, sc_=3)   # ONLY orient differs
    res = native.evaluate({"type": "TransformDecode", "goal": {"type": "Lit", "value": goal},
                            "max_dims": 4}, {})
    return bool(res.get("explained"))


# ---------------------------------------------------------------------------
# Hand-built stroke-shaped relation systems (the design's LITERAL schema) — no
# StrokeQuantize needed; these mirror exactly what it is expected to emit.
# ---------------------------------------------------------------------------
def _seg_relations(turns_lens) -> list:
    # Matches the REAL landed StrokeQuantize output exactly: ("seg", i, turn_q, len_q) --
    # arity 4, no trailing pad slot (verified live: `native.evaluate({"type":
    # "StrokeQuantize", ..., "canonical_pose": True}, {})`).
    return [["seg", i, float(t), float(l)] for i, (t, l) in enumerate(turns_lens)]


def _full_sig(turns_lens, x=0, y=0, o=0, sc_=0) -> list:
    return _seg_relations(turns_lens) + [["pose_x", x], ["pose_y", y], ["pose_o", o], ["pose_s", sc_]]


def _add_stroke(s, name: str, turns_lens, pose=(0, 0, 0, 0)) -> int:
    """A hand-built `ShapeSignature{kind:'stroke'}` codebook entry at the given canonical
    pose — mirrors `stroke_codebook.grow_stroke_quantum`'s installed shape exactly."""
    sig = _full_sig(turns_lens, *pose)
    return s.add_node("ShapeSignature", {"name": name, "kind": "stroke", "signature": json.dumps(sig)})


SQ_LIVE = _stroke_quantize_live()
TD_FIX_LIVE = _transformdecode_pools_by_predicate()
SQ_SKIP = ("StrokeQuantize (with its `canonical_pose` option) not yet landed -- "
           "runners/dsl/src/shape_decode.rs family, built in parallel against "
           "scratchpad/HANDWRITING_DESIGN.md's exact schema. Honest skip, not a faked pass; "
           "the schema/lattice/rule/audit gates in this file do NOT depend on it and stay live.")
TD_SKIP = ("TransformDecode's (predicate,slot) pooling fix not yet landed -- see "
           "domains/ink_decode.py's module docstring. Honest skip, not a faked pass.")


def _boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("writer_dimensions"), ag)
    # NOTE: seeds/ink_refinement.json is NOT loaded here -- domains/ink_decode.py's
    # `_refine_or_note` self-ensures it (Seed-node-guarded `_ensure_ink_refinement`, the same
    # pattern rf._ensure_shape_decode_loop uses) precisely so callers that predate the seed
    # (e.g. the Omniglot gate script's own boot()) still get the ir_* rules; loading it here
    # TOO would double-install them (this manifest_for path adds no Seed guard node).
    return s, ag, native


def _add_coarse_stroke(s, name: str, coarse_turns_lens, *, turn_bins=6, len_bins=4) -> int:
    """The COARSE-companion twin of `_add_stroke` — a hand-built
    `ShapeSignatureCoarse{name, signature}` codebook entry, mirroring
    `stroke_codebook.grow_stroke_quantum`'s coarse-grain installation exactly (a SEPARATE
    node TYPE, same `name`, so `ShapeDecode(codebook_type='ShapeSignatureCoarse')` reads it
    without touching the fine `ShapeSignature` codebook at all — see stroke_codebook.py's
    module docstring for why a second node type, not a second attr key, is the mechanical
    consequence of Rust `load_parts` hard-coding the `signature` attr key)."""
    sig = _seg_relations(coarse_turns_lens)
    return s.add_node("ShapeSignatureCoarse",
                      {"name": name, "kind": "stroke_coarse", "signature": json.dumps(sig),
                       "turn_bins": turn_bins, "len_bins": len_bins})


def _add_mid_stroke(s, name: str, mid_turns_lens, *, turn_bins=10, len_bins=6) -> int:
    """RUN-4 LEVERS "LEVER 2" (GRAIN LADDER)'s MID-companion twin of `_add_coarse_stroke` — a
    hand-built `ShapeSignatureMid{name, signature}` codebook entry, mirroring
    `stroke_codebook.grow_stroke_quantum`'s mid-grain installation exactly (a SEPARATE node
    TYPE, same `name`, so `ShapeDecode(codebook_type='ShapeSignatureMid')` reads it without
    touching the fine/coarse codebooks at all)."""
    sig = _seg_relations(mid_turns_lens)
    return s.add_node("ShapeSignatureMid",
                      {"name": name, "kind": "stroke_mid", "signature": json.dumps(sig),
                       "turn_bins": turn_bins, "len_bins": len_bins})


# ===========================================================================
# ALWAYS-LIVE gates — no StrokeQuantize / TransformDecode-fix dependency.
# ===========================================================================

# ---------------------------------------------------------------------------
# Gate: ShapeDecode emission scoring against the NEW full-canonical-pose codebook
# convention (the empirical check `domains/stroke_codebook.py`'s docstring names).
# ---------------------------------------------------------------------------
def test_shapedecode_scores_invariant_goal_against_full_codebook_entry():
    """`stroke_codebook.py`'s codebook convention (2026-07-02 reconciliation): the codebook
    entry carries the FULL signature (seg + pose_x/y/o/s) at canonical pose, but
    `ink_decode.py`'s per-span EMISSION scoring only has an INVARIANT (seg-only) span
    signature to offer. `ShapeDecode` (a coverage/composition scorer, not an equal-count
    matcher, ALREADY LANDED) must still report full coverage + the correct winning name —
    the codebook entry's own pose relations simply go uncovered (a constant per-candidate
    overhead, harmless to the Argmax-style ranking `_score_span` performs)."""
    s = srs.Substrate()
    native = s._inner
    _add_stroke(s, "A", [(1, 1), (2, 1), (3, 1)], pose=(4, 4, 2, 3))
    _add_stroke(s, "B", [(4, 1), (5, 1), (6, 1)], pose=(1, 1, 0, 1))

    exact_a = _seg_relations([(1, 1), (2, 1), (3, 1)])   # invariant-only goal, no pose
    count, name = ink._score_span(native, exact_a)
    assert (count, name) == (3, "A")

    mismatch = _seg_relations([(9, 9), (9, 9), (9, 9)])
    count2, name2 = ink._score_span(native, mismatch)
    assert (count2, name2) == (0, None)


# ---------------------------------------------------------------------------
# Gate 6 — no-Python-decision audit of ink_decode.py.
# ---------------------------------------------------------------------------
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")
# ALLOWLIST: ordering already-decided on_path segments by POSITION (mirrors the committed
# scripts/jabberwock_dynamic_quantization.py::viterbi_partition precedent's identical
# `segs.sort(key=lambda x: x[1])` line) is NOT a decision -- the decision (which segments
# are on_path) was already made by the graph rules; this only orders the final read-back.
_ALLOWED_SORT_KEYS = {"x[1]", "x[0]"}


def test_ink_decode_no_python_decisions():
    """Gate 6: domains/ink_decode.py contains no argmin/argmax/sort-on-scores Python
    decisions -- every choice is a held Term (ShapeDecode/TransformDecode/Argmax-as-JSON) or
    a graph rule (vit_step/vit_backtrace/sd_*/wd_infer_writer). A source-scan assertion, with
    a documented allowlist for the one benign position-ordering sort (see _ALLOWED_SORT_KEYS)."""
    src = Path(ink.__file__).read_text()

    assert not _BANNED_CALL_RE.search(src), (
        "ink_decode.py must not call argmin/argmax in Python -- every ranking choice is a "
        "held Term (ShapeDecode's covered_count/covered_by, TransformDecode, or an Argmax "
        "JSON Term dict), never a Python argmin/argmax over scores")
    assert not _MINMAX_KEY_RE.search(src), (
        "ink_decode.py must not use Python's builtin min()/max(key=...) as a scoring "
        "decision either")

    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, (
        f"sort(key=...) over an apparent SCORE expression found: {violations!r} -- add to "
        "_ALLOWED_SORT_KEYS only if it is provably a position/order read-back, not a decision")


def test_stroke_codebook_no_python_decisions():
    """The same audit applied to domains/stroke_codebook.py (S1's builder) -- a seed
    builder converts a FIXED source unconditionally; it must not rank/choose between
    candidates via Python argmin/argmax either."""
    src = Path(sc.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)


# ---------------------------------------------------------------------------
# Gate: the content-keyed mint dedup mechanism (`_signature_key`) — the "mints once, not
# per span -- key the observation" design requirement, unit-tested directly.
# ---------------------------------------------------------------------------
def test_signature_key_deterministic_and_discriminative():
    sig_a1 = _seg_relations([(1, 1), (2, 2), (3, 3)])
    sig_a2 = _seg_relations([(1, 1), (2, 2), (3, 3)])
    sig_b = _seg_relations([(9, 9), (8, 8), (7, 7)])
    assert ink._signature_key(sig_a1) == ink._signature_key(sig_a2), (
        "the SAME (quantized) shape must hash to the SAME content key across repeats")
    assert ink._signature_key(sig_a1) != ink._signature_key(sig_b)


# ---------------------------------------------------------------------------
# Gate 3's MECHANISM (Hyp/LatEdge + vit_step/vit_backtrace + ShapeDecode emission), hand-set —
# bypasses StrokeQuantize's geometry entirely, so it stays green regardless of landing status.
# ---------------------------------------------------------------------------
def test_lattice_partition_hand_set_signatures():
    """SEGMENTATION-BY-RECOGNITION's mechanism: three known stroke shapes concatenated
    end-to-end (knots 0-3="A", 3-6="B", 6-9="C", no gaps) must recover exactly those 3
    on-path spans -- boundaries EMERGE from the decode among many candidate spans of
    overlapping length, never a pre-cut."""
    s, ag, native = _boot()
    _add_stroke(s, "A", [(1, 1), (2, 1), (3, 1)])
    _add_stroke(s, "B", [(4, 1), (5, 1), (6, 1)])
    _add_stroke(s, "C", [(7, 1), (8, 1), (9, 1)])

    true_join = {(0, 3): [(1, 1), (2, 1), (3, 1)], (3, 6): [(4, 1), (5, 1), (6, 1)],
                 (6, 9): [(7, 1), (8, 1), (9, 1)]}

    def sig_for(st, e):
        # Every candidate span resamples to a FIXED segment count (3, mirroring
        # StrokeQuantize's own `segments` parameter) regardless of its knot length; only
        # the TRUE join spans reproduce a known stroke's exact turn/len profile, every
        # OTHER (mismatched-length or straddling) candidate is a clearly non-matching
        # profile -- exactly what a real StrokeQuantize resampling of a WRONG sub-path
        # would produce (never a plausible codebook entry by coincidence).
        return _seg_relations(true_join.get((st, e), [(0, 0), (0, 0), (0, 0)]))

    L = 9
    min_span, max_span = 2, 4
    spans = []
    for e in range(min_span, L + 1):
        for st in range(max(0, e - max_span), e - min_span + 1):
            count, name = ink._score_span(native, sig_for(st, e))
            spans.append((st, e, count, name))

    on_path = ink._lattice_partition(spans, L, word_penalty=-1.0, oov_score=0.0)
    assert on_path == [(0, 3, "A"), (3, 6, "B"), (6, 9, "C")], (
        f"boundaries did not emerge at the true joins: {on_path!r}")


def test_lattice_partition_discriminative_null_hand_set():
    """Discriminative null (gate 5's mechanism): NO span anywhere matches any known
    stroke -- the whole path decodes as OOV throughout (every on-path span has name=None),
    nothing recognized."""
    s, ag, native = _boot()
    _add_stroke(s, "A", [(1, 1), (2, 1), (3, 1)])

    L = 6
    spans = []
    for e in range(2, L + 1):
        for st in range(max(0, e - 4), e - 2 + 1):
            noise = _seg_relations([(99, 99), (98, 98), (97, 97)])
            count, name = ink._score_span(native, noise)
            spans.append((st, e, count, name))
    on_path = ink._lattice_partition(spans, L, word_penalty=-1.0, oov_score=0.0)
    assert on_path, "a full partition must still be found (OOV fillers cover the whole path)"
    assert all(name is None for (_st, _e, name) in on_path), "pure noise must decode OOV throughout"


# ---------------------------------------------------------------------------
# S3's DECISION (wd_infer_writer), hand-set — bypasses StrokeQuantize/TransformDecode/
# decode_ink entirely, so it stays green regardless of landing status.
# ---------------------------------------------------------------------------
def test_writer_style_rule_hand_set():
    """Gate 7's RULE (wd_infer_writer): two writers, >=3 explained pose-read Transforms
    each, agreeing orient_delta PER WRITER, DIFFERENT ACROSS writers -- each writer mints
    exactly ONE WriterStyle with its own orient_delta; no cross-writer pollution (a
    Transform is never explained_by a style minted for a DIFFERENT writer); fewer than 3
    agreeing Transforms does not mint."""
    s, ag, native = _boot()

    def add_writer_transforms(writer_name, orient_delta, n=3):
        w = s.add_node("Writer", {"name": writer_name})
        ts = []
        for _ in range(n):
            t = s.add_node("Transform", {
                "explained": True, "identity": False, "orient_delta": int(orient_delta),
                "scale_delta": 0, "dims": [ink.ORIENT_DIM], "transforms": [
                    {"dim": ink.ORIENT_DIM, "pred": ink.ORIENT_PRED, "kind": "shift",
                     "delta": int(orient_delta)}],
                "source": "ink_pose_read",
            })
            s.add_edge_unchecked(w, "wrote_transform", t)
            ts.append(t)
        return w, ts

    wA, tsA = add_writer_transforms("hand_A", 5)
    wB, tsB = add_writer_transforms("hand_B", -3)
    native.run_rules()

    styles = list(s.nodes("WriterStyle"))
    assert len(styles) == 2, f"expected exactly one WriterStyle per writer, got {len(styles)}"
    by_writer = {s.node(n)["attrs"]["writer"]: s.node(n)["attrs"] for n in styles}
    assert by_writer["hand_A"]["orient_delta"] == 5
    assert by_writer["hand_B"]["orient_delta"] == -3

    for t in tsA:
        assert s.node(t)["attrs"].get("explained_by_writer") == 1
        peers = list(s.neighbours(t, "explained_by"))
        assert len(peers) == 1
        assert s.node(peers[0])["attrs"]["writer"] == "hand_A", "no cross-writer pollution"
    for t in tsB:
        peers = list(s.neighbours(t, "explained_by"))
        assert s.node(peers[0])["attrs"]["writer"] == "hand_B", "no cross-writer pollution"

    # Fewer than 3 agreeing Transforms -> no mint yet (the >=3 pooling guard).
    add_writer_transforms("hand_C", 9, n=2)
    native.run_rules()
    assert len(list(s.nodes("WriterStyle"))) == 2, (
        "a writer with only 2 agreeing Transforms must NOT mint a WriterStyle")


# ---------------------------------------------------------------------------
# The OOV mint / recognize DECISION (sd_decode/sd_recognize/sd_mint_quantum) against our
# stroke schema, hand-set -- exercises the EXISTING ladder, no StrokeQuantize needed.
# ---------------------------------------------------------------------------
def test_induce_concern_recognize_and_mint_hand_set_stroke_schema():
    s, ag, native = _boot()
    _add_stroke(s, "A", [(1, 1), (2, 1), (3, 1)])
    baseline_axes = len(list(s.nodes("CapabilityAxis")))

    known = _seg_relations([(1, 1), (2, 1), (3, 1)])
    res_known = rf.induce_concern(s, known, name_hint="probe_known_stroke")
    assert res_known["minted"] is False
    # NOTE (pre-existing ladder limitation, not introduced here): `covered_by`'s convenience
    # Term (sd_recognize's own Argmax(FixedCount(AntiUnify(Attr(obs,"signature"),
    # Attr(sig,"signature")))), shape_decode_loop.json) compares a RAW-LIST observation
    # signature against a JSON-STRING codebook `signature` attr via the GENERIC (non-
    # JSON-aware) `Attr`/`AntiUnify` Terms -- verified live to score 0 for EVERY candidate
    # regardless of match (only `ShapeDecode`'s own `load_parts` parses the JSON string
    # properly). With `_ensure_shape_decode_loop` also seeding unrelated math/faculty
    # ShapeSignature entries (e.g. "fractal"), the all-zero tie can resolve to any of them,
    # not necessarily "A" -- the STATUS decision (minted=False, i.e. fully covered) is
    # still correct and is what this gate actually asserts.
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes

    novel = _seg_relations([(42, 42), (43, 43), (44, 44)])
    res_novel = rf.induce_concern(s, novel, name_hint="probe_novel_stroke")
    assert res_novel["minted"] is True
    assert len(list(s.nodes("CapabilityAxis"))) == baseline_axes + 1


# ===========================================================================
# LIVE gates (need StrokeQuantize; 2/7 additionally need TransformDecode's fix).
# ===========================================================================

# ---------------------------------------------------------------------------
# Gate 1 — StrokeQuantize invariance.
# ---------------------------------------------------------------------------
def test_strokequantize_invariance():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    base_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 1.0], 48)
    rotated = gmw.rotate_traj(base_pts, 37.0)
    scaled = base_pts * 2.0
    translated = base_pts + np.array([5.0, -3.0])

    def inv_sig(pts):
        return sc._quantize(native, pts, segments=sc.DEFAULT_SEGMENTS,
                             turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                             grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS,
                             invariant_only=True)["signature"]

    base_sig = inv_sig(base_pts)
    assert inv_sig(rotated) == base_sig, "rotation must not change the invariant signature"
    assert inv_sig(scaled) == base_sig, "scale must not change the invariant signature"
    assert inv_sig(translated) == base_sig, "translation must not change the invariant signature"

    def pose_of(pts):
        return sc._quantize(native, pts, segments=sc.DEFAULT_SEGMENTS,
                             turn_bins=sc.DEFAULT_TURN_BINS, len_bins=sc.DEFAULT_LEN_BINS,
                             grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS,
                             invariant_only=False)["pose"]

    base_pose, rot_pose = pose_of(base_pts), pose_of(rotated)
    assert base_pose["orient_q"] != rot_pose["orient_q"], "rotation must change orient_q"


# ---------------------------------------------------------------------------
# Gate 2 — rung-1 transform reading, zero mint through the sd loop.
# ---------------------------------------------------------------------------
def test_rung1_transform_reading_zero_mint():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not TD_FIX_LIVE:
        pytest.skip(TD_SKIP)
    s, ag, native = _boot()
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 48).tolist()
    sc.build_stroke_codebook(s, sources=[("line", line_pts)], include_pickle=False)
    epoch0 = s.node(ag)["attrs"]["codebook_epoch"]

    moved = (gmw.rotate_traj(np.asarray(line_pts), 25.0) + np.array([2.0, -1.0])).tolist()
    ink_node = ink.ingest_ink(s, moved, max_knots=48)
    res = ink.decode_ink(s, ink_node, min_span=40, max_span=48)

    assert len(res["oov"]) == 0 and len(res["minted"]) == 0, "recognized, not OOV/minted"
    assert s.node(ag)["attrs"]["codebook_epoch"] == epoch0, "zero mint through the sd loop"
    assert len(res["recognized"]) == 1
    t = res["recognized"][0]["transform"]
    assert t["explained"] is True
    assert set(t["dims"]) <= {ink.ORIENT_DIM}.union({1})  # pose_o and/or pose_x/pose_y slots


# ---------------------------------------------------------------------------
# Gate 3 (headline, live pipeline) — SEGMENTATION-BY-RECOGNITION over real ink.
# ---------------------------------------------------------------------------
def test_segmentation_by_recognition_headline_live():
    """3 strokes concatenated into ONE continuous pen path (each ending exactly where the
    next starts -- a genuinely continuous stroke, not merely 3 unrelated point-sets stacked
    together) must decode with boundaries EMERGING at the true joins. Strokes 1 and 3 are
    both STRAIGHT LINES: a straight line's invariant signature is, BY CONSTRUCTION,
    rotation-invariant (zero relative turn regardless of absolute direction) -- "up" and
    "down" are the SAME shape category under this representation, a genuine, expected
    property of the design (not a bug), so this gate checks each line span resolves to
    SOME held line-shape name (never the other, curved, shape's name and never OOV), while
    stroke 2 (an ARC, genuine nonzero curvature) gets an EXACT, unambiguous name. The
    BOUNDARY POSITIONS -- the actual headline claim, 'boundaries emerge, never a pre-cut'
    -- are asserted exactly for all three."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()

    # EQUAL ARC LENGTH for all 3 strokes (each length 1.0): `ingest_ink` resamples the
    # WHOLE concatenated path UNIFORMLY BY ARC LENGTH into `max_knots` knots (mechanical
    # geometry, glyph_motor_world._resample_arclen) -- unequal per-stroke arc lengths
    # would allocate unequal KNOT COUNTS per stroke, so equalising arc length up front is
    # what makes "boundaries at the true joins" a meaningful, checkable claim in KNOT
    # index space rather than an artifact of how many raw points each stroke happened to
    # be sampled with.
    # A LARGE sweep angle (270 degrees) is needed for genuine per-segment curvature to
    # survive `turn_bins` quantization (a shallow arc's tiny per-segment turn rounds to
    # the SAME zero bin as a straight line -- empirically verified: a ~115-degree sweep
    # over 12 segments quantized to all-zero turn_q, indistinguishable from "up"/"down").
    # `r` is chosen so arc length r*theta stays 1.0, matching the two straight lines.
    theta_deg = 270.0
    r = 1.0 / np.radians(theta_deg)
    up_pts = gmw._sample_stroke("line", [0.0, 0.0, 0.0, 1.0], 24)          # (0,0) -> (0,1), length 1
    bulge_pts = gmw._sample_stroke("arc", [r, 1.0, r, 180.0, 180.0 - theta_deg], 24)  # length 1
    down_start = bulge_pts[-1]
    down_pts = gmw._sample_stroke(
        "line", [down_start[0], down_start[1], down_start[0], down_start[1] - 1.0], 24)  # length 1
    assert np.allclose(up_pts[-1], bulge_pts[0], atol=1e-6)
    assert np.allclose(bulge_pts[-1], down_pts[0], atol=1e-6)
    sc.build_stroke_codebook(
        s, sources=[("up", up_pts.tolist()), ("bulge", bulge_pts.tolist()),
                    ("down", down_pts.tolist())],
        include_pickle=False)

    concatenated = np.concatenate([up_pts, bulge_pts, down_pts], axis=0)
    n_knots = len(concatenated)
    ink_node = ink.ingest_ink(s, concatenated.tolist(), max_knots=n_knots)
    third = n_knots // 3
    # EXACT single candidate length (equal arc lengths -> equal knot shares, 1/3 each): a
    # straight line's invariant signature is IDENTICAL for every window length (turn=0,
    # len-fraction uniform, regardless of absolute length) -- a RANGE of candidate lengths
    # would tie an enormous number of overlapping same-length-independent sub-windows of
    # the straight strokes against each other (a property of straight lines, not a decode
    # bug: verified directly against the seeded, UNCHANGED vit_step/vit_backtrace, which
    # correctly fans out ALL joint-best paths on a genuine tie -- see
    # test_lattice_partition_hand_set_signatures for the same mechanism exercised
    # cleanly). Fixing min_span==max_span==third makes 0->third->2*third->n_knots the
    # UNIQUE full-length partition, so boundaries still EMERGE (chosen over every OTHER
    # candidate START POSITION at that length), never a hardcoded position.
    res = ink.decode_ink(s, ink_node, min_span=third, max_span=third)

    names = [nm for (_st, _e, nm) in res["spans"]]
    assert len(names) == 3, f"expected exactly 3 recognized/OOV spans, got: {res['spans']!r}"
    assert names[0] in ("up", "down"), f"span 1 (a straight line) must resolve to a held line shape: {names!r}"
    assert names[1] == "bulge", f"span 2 (the curved stroke) must resolve EXACTLY: {names!r}"
    assert names[2] in ("up", "down"), f"span 3 (a straight line) must resolve to a held line shape: {names!r}"

    true_joins = {0, third, 2 * third, n_knots}
    emergent = {0} | {e for (_st, e, _nm) in res["spans"]}
    for tj in true_joins:
        assert any(abs(tj - b) <= 2 for b in emergent), f"join {tj} missed by >2 knots: {emergent!r}"


# ---------------------------------------------------------------------------
# Gate 4 — OOV mint exactly one; re-decode recognizes after epoch bump.
# ---------------------------------------------------------------------------
def test_oov_mint_exactly_one_then_recognized_after_epoch_bump():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    # EQUAL ARC LENGTH (1.0) for line/arc/squiggle -- see gate 3's identical rationale
    # (ingest_ink resamples the WHOLE path uniformly by arc length; unequal per-stroke
    # lengths would allocate unequal knot shares, making a fixed span window meaningless).
    # theta=270 degrees (a LARGE sweep, see gate 3's identical rationale): a shallow arc's
    # tiny per-segment turn quantizes to the SAME zero bin as a straight line.
    theta_deg = 270.0
    r = 1.0 / np.radians(theta_deg)
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24)                    # length 1
    arc_pts = gmw._sample_stroke("arc", [1.0, r, r, -90.0, -90.0 + theta_deg], 24)      # length 1
    assert np.allclose(line_pts[-1], arc_pts[0], atol=1e-6)
    sc.build_stroke_codebook(
        s, sources=[("I_0", line_pts.tolist()), ("bulge_0", arc_pts.tolist())],
        include_pickle=False)
    epoch0 = s.node(ag)["attrs"]["codebook_epoch"]
    lib0 = sc._existing_names(s, "stroke")

    rng = np.random.default_rng(0)
    steps = rng.normal(0, 1, size=(23, 2))
    raw = np.concatenate([np.zeros((1, 2)), np.cumsum(steps, axis=0)], axis=0)
    raw_len = float(np.sqrt(((np.diff(raw, axis=0)) ** 2).sum(1)).sum()) or 1.0
    squiggle = arc_pts[-1] + raw / raw_len         # rescaled to total arc length 1.0, same as line/arc
    assert np.allclose(squiggle[0], arc_pts[-1], atol=1e-6)
    concatenated = np.concatenate([line_pts, arc_pts, squiggle], axis=0)
    n_knots = len(concatenated)
    ink_node = ink.ingest_ink(s, concatenated.tolist(), max_knots=n_knots)
    third = n_knots // 3
    # EXACT single candidate length -- see gate 3's identical rationale (avoids the
    # straight-line self-similarity tie explosion under a length RANGE).
    res = ink.decode_ink(s, ink_node, min_span=third, max_span=third)

    assert len(res["recognized"]) == 2
    assert len(res["minted"]) == 1, f"expected exactly one mint, got {len(res['minted'])}"
    assert s.node(ag)["attrs"]["codebook_epoch"] == epoch0 + 1
    lib1 = sc._existing_names(s, "stroke")
    assert lib1 - lib0 == {res["minted"][0]["name"]}

    # RE-DECODE the SAME ink NODE a second time (same stored knots -- no re-resampling
    # round-trip, which is NOT guaranteed bit-idempotent and would test an unrelated
    # `_resample_arclen` property, not the mint/recognize loop): after the epoch bump,
    # the previously-OOV span now recognizes as the newly-minted quantum.
    mint_span = res["minted"][0]
    res2 = ink.decode_ink(s, ink_node, min_span=third, max_span=third)
    assert len(res2["minted"]) == 0, "the SAME observation must not mint a second time"
    matching = [r for r in res2["recognized"]
                if r["start"] == mint_span["start"] and r["end"] == mint_span["end"]]
    assert len(matching) == 1, "the newly-minted quantum must now be recognized at the same span"
    assert matching[0]["name"] == mint_span["name"]


# ---------------------------------------------------------------------------
# Gate 5 — discriminative null (pure noise, live pipeline).
# ---------------------------------------------------------------------------
def test_noise_discriminative_null_live():
    """Pure noise decodes OOV throughout (never recognizes a known stroke). 'Mints once —
    not per span, key the observation' is exercised as: re-decoding the EXACT SAME noise
    path a second time (after the codebook already grew from the first decode) must mint
    NOTHING NEW -- the content-keyed dedup (`_signature_key` + `grow_stroke_quantum`'s
    by-name idempotency) recognizes the repeat rather than minting again. (A single decode
    of a long noise path may legitimately split into >1 on-path OOV span with genuinely
    DIFFERENT quantized content -- each distinct novel shape minting once is correct; the
    dedup guarantee this gate checks is against RE-cutting the SAME content, not against
    a long path ever splitting into more than one novel shape.)"""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24)
    sc.build_stroke_codebook(s, sources=[("I_0", line_pts.tolist())], include_pickle=False)

    rng = np.random.default_rng(1)
    noise = np.cumsum(rng.normal(0, 1, size=(48, 2)), axis=0)
    ink_node = ink.ingest_ink(s, noise.tolist(), max_knots=len(noise))
    res = ink.decode_ink(s, ink_node, min_span=18, max_span=30)

    assert len(res["recognized"]) == 0, "pure noise must never recognize a known stroke"
    n_minted_first = len(res["minted"])
    assert n_minted_first >= 1, "genuine novelty must mint at least once"

    # RE-DECODE the EXACT SAME noise path: content-keyed dedup must mint NOTHING NEW.
    ink_node2 = ink.ingest_ink(s, noise.tolist(), max_knots=len(noise))
    res2 = ink.decode_ink(s, ink_node2, min_span=18, max_span=30)
    assert len(res2["minted"]) == 0, (
        "re-decoding the SAME noise must not mint again -- 'mints once, key the observation'")
    assert len(res2["recognized"]) == n_minted_first, (
        "the previously-minted quantum(s) must now be RECOGNIZED, not re-minted")


# ---------------------------------------------------------------------------
# Gate 7 (live pipeline) — two hands, writer dimensions.
# ---------------------------------------------------------------------------
def test_two_hands_writer_dimension_live():
    """A CLEAN writer-dimension signal needs the SAME underlying stroke shape recognized
    consistently every time (so every reading's orient_delta measures ONLY the hand's own
    rotation bias, not a confound from different base strokes having different absolute
    orientations to begin with) -- one canonical stroke, written 3 TIMES by each of 2
    hands at each hand's own FIXED rotation bias (`rotate_traj`, deterministic -- 'two
    hands with distinct fixed slants', design S3)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    if not TD_FIX_LIVE:
        pytest.skip(TD_SKIP)
    s, ag, native = _boot()
    prim, args = gmw.GLYPHS["I"][0]
    canon = gmw._sample_stroke(prim, args, 24)
    sc.build_stroke_codebook(s, sources=[("I_0", canon.tolist())], include_pickle=False)

    HAND_A_DEG, HAND_B_DEG = 20.0, -15.0
    for hand, deg in (("hand_A", HAND_A_DEG), ("hand_B", HAND_B_DEG)):
        for _rep in range(3):
            traj = gmw.rotate_traj(canon, deg)
            ink_node = ink.ingest_ink(s, traj.tolist(), writer=hand, max_knots=len(traj))
            res = ink.decode_ink(s, ink_node, min_span=int(len(traj) * 0.8),
                                  max_span=int(len(traj) * 1.2), writer=hand)
            assert len(res["recognized"]) == 1 and res["recognized"][0]["name"] == "I_0"

    styles = list(s.nodes("WriterStyle"))
    by_writer = {s.node(n)["attrs"]["writer"]: s.node(n)["attrs"] for n in styles}
    assert set(by_writer) == {"hand_A", "hand_B"}
    assert by_writer["hand_A"]["orient_delta"] != by_writer["hand_B"]["orient_delta"]

    for hand in ("hand_A", "hand_B"):
        w = next(n for n in s.nodes("Writer") if s.node(n)["attrs"]["name"] == hand)
        for t in s.neighbours(w, "wrote_transform"):
            peers = list(s.neighbours(t, "explained_by"))
            if peers:
                assert s.node(peers[0])["attrs"]["writer"] == hand, "no cross-writer pollution"


# ===========================================================================
# REFINEMENT RUNG (scratchpad/HANDWRITING_DESIGN.md's "REFINEMENT RUNG" section, the
# Omniglot residual, commit 26f74039) — gates (a)-(e). ADDITIVE: every gate above this line
# is unchanged. Hand-set where possible (deterministic, no StrokeQuantize dependency, mirrors
# this file's own "ALWAYS-LIVE" mechanism-gate style) — StrokeQuantize's REAL geometry is
# already exercised end-to-end by gates 1-5/7 above; these gates isolate the NEW mechanism
# (coarse tier / refinement mint / DtwTo fallback / family pooling) precisely.
# ===========================================================================

# ---------------------------------------------------------------------------
# Gate (a) — a jittered (non-uniform ±1 fine-bin) stroke recognizes at the COARSE grain,
# NOT minted as a new top-level quantum.
# ---------------------------------------------------------------------------
def test_gate_a_coarse_recognition_not_minted():
    """`_choose_span_tier` (REFINEMENT RUNG item 2's dispatch): a span whose FINE grain
    mismatches (non-uniform jitter, so no fine candidate scores a full match) but whose
    COARSE grain (independently quantized at coarser bins -- 'coarse-grain exact match IS
    the principled near-miss band') exactly matches a held family must be recognized at
    that COARSE tier (`chosen_name` is the coarse family's name, NOT None) -- `decode_ink`'s
    own code structure then makes minting IMPOSSIBLE for this span (its post-decode loop
    only ever calls `induce_concern`/`grow_stroke_quantum` in the `name is None` branch;
    tier=='coarse' never takes that branch)."""
    s = srs.Substrate()
    native = s._inner
    _add_stroke(s, "A", [(1, 1), (2, 1), (3, 1)])              # fine codebook entry
    _add_coarse_stroke(s, "A", [(0, 0), (1, 0), (1, 0)])       # its coarse companion

    # A non-uniform jitter: segment 0's turn shifted by a fine amount that does NOT survive
    # to a full fine match (mismatches "A"'s fine seg[0]=(1,1)) but the SAME jittered
    # instance's COARSE-grain signature (independently computed at coarser resolution, as
    # `decode_ink` would from real geometry) still lands on "A"'s exact coarse buckets.
    jittered_fine = _seg_relations([(2, 1), (2, 1), (3, 1)])    # seg[0] turn 1->2, non-uniform
    jittered_coarse = _seg_relations([(0, 0), (1, 0), (1, 0)])  # identical to A's coarse entry

    fine_count, fine_name = ink._score_span(native, jittered_fine)
    assert fine_name is None, "the jittered instance must NOT score a full fine match"

    coarse_count, coarse_name = ink._score_span_coarse(native, jittered_coarse)
    assert coarse_name == "A", "the SAME jittered instance's coarse grain must exact-match A"

    tier, chosen_name, emit = ink._choose_span_tier(fine_count, fine_name, coarse_count, coarse_name)
    assert (tier, chosen_name) == ("coarse", "A"), (
        "a coarse-only match must recognize at the coarse tier, not fall through to OOV")


# ---------------------------------------------------------------------------
# Gate (b) — a fine mismatch confined to ONE dimension mints a per-dimension CHILD quantum
# (turn-only when len matches; len-only when turn matches), refines_quantum edge.
# ---------------------------------------------------------------------------
def test_gate_b_refinement_mint_per_dimension():
    s, ag, native = _boot()
    parent_pts = [(1, 1), (2, 1), (3, 1)]
    _add_stroke(s, "A", parent_pts)          # the coarse-recognized PARENT quantum

    # (1) TURN mismatches, LEN matches everywhere -> a TURN-ONLY child.
    span_turn_mismatch = _full_sig([(9, 1), (2, 1), (3, 1)])   # seg[0] turn 1->9, len untouched
    res_turn = ink._refine_or_note(s, s, native, ag, s.add_node("Stroke", {}), "A",
                                   span_turn_mismatch, segments=3, turn_bins=sc.DEFAULT_TURN_BINS,
                                   len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                                   scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_turn is not None and res_turn["minted"] is True
    assert res_turn["status"] == "refine_turn"
    child = sc._find_stroke_node(s, res_turn["name"])
    assert child is not None
    assert s.node(child)["attrs"]["refined_dim"] == "turn"
    assert s.node(child)["attrs"]["refines"] == "A"
    parents = list(s.neighbours(child, "refines_quantum"))
    assert len(parents) == 1
    assert s.node(parents[0])["attrs"]["name"] == "A"

    # (2) LEN mismatches, TURN matches everywhere -> a LEN-ONLY child.
    span_len_mismatch = _full_sig([(1, 9), (2, 1), (3, 1)])    # seg[0] len 1->9, turn untouched
    res_len = ink._refine_or_note(s, s, native, ag, s.add_node("Stroke", {}), "A",
                                  span_len_mismatch, segments=3, turn_bins=sc.DEFAULT_TURN_BINS,
                                  len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                                  scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_len is not None and res_len["minted"] is True
    assert res_len["status"] == "refine_len"
    assert s.node(sc._find_stroke_node(s, res_len["name"]))["attrs"]["refined_dim"] == "len"

    # (3) BOTH mismatch -> a 'both' child (still linked to the coarse family, not a
    # wholly independent top-level mint).
    span_both_mismatch = _full_sig([(9, 9), (2, 1), (3, 1)])
    res_both = ink._refine_or_note(s, s, native, ag, s.add_node("Stroke", {}), "A",
                                   span_both_mismatch, segments=3, turn_bins=sc.DEFAULT_TURN_BINS,
                                   len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                                   scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_both is not None and res_both["status"] == "refine_both"

    # (4) An EXACT fine match (nothing to refine) -> no Observation, no mint.
    exact = _full_sig([(1, 1), (2, 1), (3, 1)])
    res_exact = ink._refine_or_note(s, s, native, ag, s.add_node("Stroke", {}), "A", exact,
                                    segments=3, turn_bins=sc.DEFAULT_TURN_BINS,
                                    len_bins=sc.DEFAULT_LEN_BINS, grid=sc.DEFAULT_GRID,
                                    scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_exact == {"status": "exact_at_fine", "minted": False}


# ---------------------------------------------------------------------------
# Gate (c) — the DtwTo near-miss fallback (tier 3): catches a near-miss even coarse
# exact-match misses; true noise still falls through to OOV/mint.
# ---------------------------------------------------------------------------
def test_gate_c_dtw_fallback_near_and_far():
    s, ag, native = _boot()
    proto_a = [[0.0, 0.0], [0.5, 0.0], [1.0, 0.0]]
    s.add_node("ShapeSignature", {"name": "A", "kind": "stroke",
                                  "prototype": json.dumps(proto_a)})

    # NEAR: a small numeric perturbation of A's own prototype (well within a generous
    # threshold) -- close in real-valued shape distance even though nothing about it would
    # exact-match at ANY quantized grain.
    near = [[0.0, 0.01], [0.51, -0.01], [1.0, 0.02]]
    name, dist, is_near = ink._dtw_fallback(s, native, ag, near)
    assert name == "A" and is_near is True, f"a small perturbation of A must read as near: {dist!r}"

    # FAR: a genuinely different, much larger/differently-shaped path -- true novelty, not a
    # near-miss (default threshold DEFAULT_DTW_THRESHOLD, unchanged).
    far = [[0.0, 0.0], [3.0, 4.0], [-2.0, 5.0]]
    name2, dist2, is_far_near = ink._dtw_fallback(s, native, ag, far)
    assert is_far_near is False, f"a genuinely different shape must NOT read as near: {dist2!r}"
    assert dist2 > dist, "the far path's DTW distance must exceed the near path's"

    # No candidates at all (no stored prototypes) -> honest (None, None, False), never a crash.
    s2 = srs.Substrate()
    name3, dist3, is_near3 = ink._dtw_fallback(s2, s2._inner, None, near)
    assert (name3, dist3, is_near3) == (None, None, False)


def test_gate_c_dtw_true_noise_still_oov_mints_live():
    """Integration check (LIVE pipeline): when NEITHER grain nor DtwTo recognizes anything
    (true noise, far from every held prototype), `decode_ink` must still fall through to the
    EXISTING OOV/mint path -- this is exactly gate 5's own noise-discriminative-null
    property, re-asserted here to confirm the NEW DtwTo tier does not accidentally swallow
    genuine novelty into a false 'near' verdict."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24)
    sc.build_stroke_codebook(s, sources=[("I_0", line_pts.tolist())], include_pickle=False)

    rng = np.random.default_rng(2)
    noise = np.cumsum(rng.normal(0, 1, size=(48, 2)), axis=0)
    ink_node = ink.ingest_ink(s, noise.tolist(), max_knots=len(noise))
    res = ink.decode_ink(s, ink_node, min_span=18, max_span=30)

    assert len(res["recognized"]) == 0, "pure noise must never recognize (fine/coarse/dtw)"
    assert len(res["minted"]) >= 1, "genuine novelty must still mint at least once"


# ---------------------------------------------------------------------------
# Gate (d) — coarse-grain signatures make TWO jittered instances of the same stroke
# CLASSIFY TOGETHER (both resolve to the SAME coarse family name).
# ---------------------------------------------------------------------------
def test_gate_d_two_jittered_instances_classify_together():
    s = srs.Substrate()
    native = s._inner
    _add_coarse_stroke(s, "A", [(0, 0), (1, 0), (1, 0)])

    jitter_1 = _seg_relations([(0, 0), (1, 0), (1, 0)])   # exact
    jitter_2 = _seg_relations([(0, 0), (1, 0), (1, 0)])   # a SECOND instance, independently
                                                            # "observed" (different fine noise
                                                            # upstream, same coarse bucket)
    _count1, name1 = ink._score_span_coarse(native, jitter_1)
    _count2, name2 = ink._score_span_coarse(native, jitter_2)
    assert name1 == name2 == "A", (
        "two independently-jittered instances of the same stroke must classify to the SAME "
        "coarse family")


# ---------------------------------------------------------------------------
# Gate (e) — family-grain writer pooling: styles per (hand, family), more coherent than the
# global pool (which conflates families that happen to share a numeric orient_delta).
# ---------------------------------------------------------------------------
def test_gate_e_family_grain_writer_pooling():
    s, ag, native = _boot()

    def add_writer_transforms(writer_name, family, orient_delta, n=3):
        w = None
        for existing in s.nodes("Writer"):
            if s.node(existing)["attrs"].get("name") == writer_name:
                w = existing
        if w is None:
            w = s.add_node("Writer", {"name": writer_name})
        ts = []
        for _ in range(n):
            t = s.add_node("Transform", {
                "explained": True, "identity": False, "orient_delta": int(orient_delta),
                "scale_delta": 0, "base": family, "dims": [ink.ORIENT_DIM],
                "transforms": [{"dim": ink.ORIENT_DIM, "pred": ink.ORIENT_PRED, "kind": "shift",
                               "delta": int(orient_delta)}],
                "source": "ink_pose_read",
            })
            s.add_edge_unchecked(w, "wrote_transform", t)
            ts.append(t)
        return w, ts

    # hand_A writes TWO families, both happening to measure the SAME numeric orient_delta
    # (5) -- a real scenario the design names: 'a real hand is a family of implied
    # dimensions, not one slant'. Global pooling's dedup key ignores family entirely, so it
    # CONFLATES both families into one style; family-grain pooling correctly keeps them
    # separate (two distinct, correctly-attributed styles).
    wA, ts_f1 = add_writer_transforms("hand_A", "F1", 5)
    _wA2, ts_f2 = add_writer_transforms("hand_A", "F2", 5)
    # hand_B: a single family, for the no-cross-writer/no-cross-family-pollution check.
    wB, ts_b = add_writer_transforms("hand_B", "F1", -7)
    native.run_rules()

    # GLOBAL pool (wd_infer_writer, pre-existing rule): conflates F1+F2 for hand_A into ONE
    # global WriterStyle (kept as the documented secondary/fallback report).
    global_styles_A = [n for n in s.nodes("WriterStyle")
                       if s.node(n)["attrs"].get("writer") == "hand_A"
                       and "family" not in s.node(n)["attrs"]]
    assert len(global_styles_A) == 1, (
        f"global pooling must CONFLATE hand_A's two same-valued families into one style, "
        f"got {len(global_styles_A)}")

    # FAMILY-GRAIN pool (wd_infer_writer_family, NEW): keeps F1 and F2 separate -- MORE
    # coherent (correctly attributed) than the single blended global style above.
    family_styles_A = [n for n in s.nodes("WriterStyle")
                       if s.node(n)["attrs"].get("writer") == "hand_A"
                       and s.node(n)["attrs"].get("family") is not None]
    families = {s.node(n)["attrs"]["family"] for n in family_styles_A}
    assert families == {"F1", "F2"}, f"expected one family-style per family, got {families!r}"
    assert len(family_styles_A) == 2, (
        f"family-grain pooling must recover TWO distinct styles for hand_A's two families, "
        f"got {len(family_styles_A)} -- 'a real hand is a family of implied dimensions, not "
        f"one slant'")

    # No cross-writer / no cross-family pollution: every family-style-explained Transform's
    # OWN family (base) matches the style it is explained by.
    for t in ts_f1 + ts_f2 + ts_b:
        peers = list(s.neighbours(t, "explained_by_family"))
        if not peers:
            continue
        ws_at = s.node(peers[0])["attrs"]
        assert ws_at["family"] == s.node(t)["attrs"]["base"]
        assert ws_at["writer"] == ("hand_A" if t in ts_f1 + ts_f2 else "hand_B")


# ===========================================================================
# RUN-4 LEVERS "LEVER 2" (GRAIN LADDER, scratchpad/HANDWRITING_DESIGN.md, 2026-07-02 — the
# c1b83669 residual: "more refinement rungs = more vocabulary"). ADDITIVE: every gate above
# this line is unchanged. A THIRD grain, MID (strictly between COARSE and FINE), is inserted
# into `decode_ink`'s post-lattice second look, tried BEFORE coarse.
# ===========================================================================

# ---------------------------------------------------------------------------
# Gate (lever2-a) — "distinct-at-mid identities": two quanta that COLLIDE at the coarse grain
# (identical coarse buckets) still resolve to the RIGHT one at the mid grain.
# ---------------------------------------------------------------------------
def test_lever2_distinct_at_mid_identities():
    s = srs.Substrate()
    native = s._inner
    _add_stroke(s, "A", [(1, 1), (2, 1), (3, 1)])
    _add_stroke(s, "B", [(1, 1), (2, 1), (4, 1)])
    # A and B COLLIDE at the coarse grain (identical coarse buckets) -- coarse alone cannot
    # tell them apart -- but DIFFER at the mid grain (each keeps its own mid companion).
    _add_coarse_stroke(s, "A", [(0, 0), (1, 0), (1, 0)])
    _add_coarse_stroke(s, "B", [(0, 0), (1, 0), (1, 0)])
    _add_mid_stroke(s, "A", [(0, 0), (1, 0), (2, 0)])
    _add_mid_stroke(s, "B", [(0, 0), (1, 0), (3, 0)])

    mid_query_a = _seg_relations([(0, 0), (1, 0), (2, 0)])   # exact-matches A's mid, not B's
    mid_query_b = _seg_relations([(0, 0), (1, 0), (3, 0)])   # exact-matches B's mid, not A's

    _count_a, name_a = ink._score_span_mid(native, mid_query_a)
    _count_b, name_b = ink._score_span_mid(native, mid_query_b)
    assert name_a == "A", f"mid grain must resolve to A specifically, got {name_a!r}"
    assert name_b == "B", f"mid grain must resolve to B specifically, got {name_b!r}"
    assert name_a != name_b, (
        "two quanta identical at coarse must still resolve to DISTINCT identities at mid")

    # The COARSE grain, on its own, genuinely cannot discriminate them (both entries are an
    # EXACT coarse match) -- confirms the mid lookup is doing real discriminative work, not
    # merely duplicating what coarse already provided.
    coarse_query = _seg_relations([(0, 0), (1, 0), (1, 0)])
    _cc, coarse_name = ink._score_span_coarse(native, coarse_query)
    assert coarse_name in ("A", "B"), "coarse must still recognize SOME family (not OOV)"


# ---------------------------------------------------------------------------
# Gate (lever2-b) — `_choose_span_tier`'s three-way Occam dispatch: fine > mid > coarse > oov,
# and the pre-existing 4-positional-arg call (no mid) keeps behaving byte-identically.
# ---------------------------------------------------------------------------
def test_lever2_choose_span_tier_prefers_mid_over_coarse():
    # Backward compatibility: the ORIGINAL 4-arg call (no mid) is untouched -- fine then
    # coarse, exactly as every pre-existing caller/test already relies on.
    assert ink._choose_span_tier(0, None, 5, "coarse_name") == ("coarse", "coarse_name", 5)
    assert ink._choose_span_tier(3, "fine_name", 5, "coarse_name") == ("fine", "fine_name", 3)

    # NEW: mid wins over coarse (a finer net, tried first) when both are present.
    tier, name, emit = ink._choose_span_tier(0, None, 5, "coarse_name", 7, "mid_name")
    assert (tier, name, emit) == ("mid", "mid_name", 7)

    # fine still wins over mid+coarse combined.
    tier, name, emit = ink._choose_span_tier(2, "fine_name", 5, "coarse_name", 7, "mid_name")
    assert (tier, name, emit) == ("fine", "fine_name", 2)

    # neither fine nor mid nor coarse -> oov, unchanged.
    assert ink._choose_span_tier(0, None, 0, None, 0, None) == ("oov", None, 0)


# ---------------------------------------------------------------------------
# Gate (lever2-c) — jitter that fails BOTH fine and mid still folds at coarse (no top-level
# mint) — the ladder's coarsest net remains the final backstop before DtwTo/OOV.
# ---------------------------------------------------------------------------
def test_lever2_jitter_still_folds_at_coarse_when_mid_fails():
    s = srs.Substrate()
    native = s._inner
    _add_stroke(s, "A", [(1, 1), (2, 1), (3, 1)])              # fine codebook entry
    _add_coarse_stroke(s, "A", [(0, 0), (1, 0), (1, 0)])       # its coarse companion
    _add_mid_stroke(s, "A", [(0, 0), (1, 0), (2, 0)])          # its mid companion

    # Fine mismatches (as in gate (a)); MID ALSO mismatches (a jitter big enough to miss the
    # mid grain too); COARSE still exact-matches -- the ladder's coarsest net.
    jittered_fine = _seg_relations([(2, 1), (2, 1), (3, 1)])
    jittered_mid = _seg_relations([(9, 0), (1, 0), (2, 0)])     # does NOT match A's mid
    jittered_coarse = _seg_relations([(0, 0), (1, 0), (1, 0)])  # DOES match A's coarse

    fine_count, fine_name = ink._score_span(native, jittered_fine)
    assert fine_name is None

    mid_count, mid_name = ink._score_span_mid(native, jittered_mid)
    assert mid_name is None, "this jitter must ALSO miss the mid grain (by construction)"

    coarse_count, coarse_name = ink._score_span_coarse(native, jittered_coarse)
    assert coarse_name == "A"

    tier, chosen_name, _emit = ink._choose_span_tier(
        fine_count, fine_name, coarse_count, coarse_name, mid_count, mid_name)
    assert (tier, chosen_name) == ("coarse", "A"), (
        "when fine AND mid both fail, coarse must still recognize (no top-level mint)")


# ---------------------------------------------------------------------------
# Gate (lever2-d) — live integration: `grow_stroke_quantum` installs the THIRD (mid)
# companion node + `grain_vocabulary_report` reports vocabulary PER LEVEL.
# ---------------------------------------------------------------------------
def test_lever2_grow_stroke_quantum_installs_mid_companion_and_vocabulary_report():
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line_pts = gmw._sample_stroke("line", [0.0, 0.0, 1.0, 0.0], 24).tolist()
    res = sc.grow_stroke_quantum(s, line_pts, "line_0")
    assert res["grown"] is True
    assert res.get("mid_node") is not None, "grow_stroke_quantum must install a MID companion"

    mid_nodes = [n for n in s.nodes("ShapeSignatureMid") if s.node(n)["attrs"]["name"] == "line_0"]
    assert len(mid_nodes) == 1
    assert s.node(mid_nodes[0])["attrs"]["kind"] == "stroke_mid"
    # `has_mid_grain` is a fine->mid edge (mirrors has_coarse_grain).
    fine_node = res["node"]
    assert mid_nodes[0] in list(s.neighbours(fine_node, "has_mid_grain"))

    fine_attrs = s.node(fine_node)["attrs"]
    assert fine_attrs.get("mid_signature") is not None
    assert fine_attrs.get("mid_turn_bins") == sc.MID_TURN_BINS
    assert fine_attrs.get("mid_len_bins") == sc.MID_LEN_BINS

    report = sc.grain_vocabulary_report(s)
    assert report["top"] == 1
    assert report["distinct_coarse"] == 1
    assert report["distinct_mid"] == 1
    assert report["distinct_fine"] == 1
    assert report["total"] == len(sc._existing_names(s, "stroke")) == 1

    # A SECOND, geometrically DIFFERENT stroke grows the fine/mid/coarse vocabulary together.
    arc_pts = gmw._sample_stroke("arc", [1.0, 1.0, 1.0, -90.0, 90.0], 24).tolist()
    sc.grow_stroke_quantum(s, arc_pts, "arc_0")
    report2 = sc.grain_vocabulary_report(s)
    assert report2["top"] == 2
    assert report2["distinct_fine"] == 2
    # distinct_coarse/distinct_mid may or may not collapse depending on real geometry, but
    # must never EXCEED the fine count (a grain can only coarsen, never invent distinctions).
    assert report2["distinct_coarse"] <= report2["distinct_fine"]
    assert report2["distinct_mid"] <= report2["distinct_fine"]


# ===========================================================================
# EAGER CHILD MINTING (scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING" section,
# 2026-07-02 — the a6fe069b residual). ADDITIVE: every gate above this line is unchanged.
# STEP 0 found a FINE-tier recognition is ALWAYS exact-signature equality (0/2595 real
# Omniglot fine recognitions carried any residual against their parent's stored fine `seg`) —
# so a genuinely FINER grain (SUB-FINE, `sc.SUBFINE_TURN_BINS`/`SUBFINE_LEN_BINS`) is needed to
# expose within-tier variation; `ink_decode._eager_child_or_note` is a thin parameterization
# of the EXISTING `_refine_or_note` pointed at that grain, installing into a DELIBERATELY
# separate `ShapeSignatureFineChild` node type (never `ShapeSignature`) so it can never
# compete in `_score_span`'s primary fine-grain scan — "detail enters as children only, base
# grains untouched" as a STRUCTURAL guarantee.
# ===========================================================================
def _add_subfine_parent(s, name: str, seg_turns_lens, subfine_turns_lens, *,
                        subfine_turn_bins=sc.SUBFINE_TURN_BINS,
                        subfine_len_bins=sc.SUBFINE_LEN_BINS) -> int:
    """A hand-built `ShapeSignature{kind:'stroke'}` codebook entry carrying BOTH its fine
    `signature` and a `subfine_signature` attr — mirrors `grow_stroke_quantum`'s own
    'ONE MOTION' convention (fine + coarse + mid + subfine, all computed together) without
    needing a live `StrokeQuantize` call."""
    sig = _full_sig(seg_turns_lens)
    subfine_sig = _seg_relations(subfine_turns_lens)
    return s.add_node("ShapeSignature", {
        "name": name, "kind": "stroke", "signature": json.dumps(sig),
        "subfine_signature": json.dumps(subfine_sig),
        "subfine_turn_bins": subfine_turn_bins, "subfine_len_bins": subfine_len_bins})


def test_eager_child_gate1_per_dimension_mint_separate_node_type():
    """A fine-tier-recognized parent whose SUB-FINE grain mismatches mints a per-dimension
    CHILD into the SEPARATE `ShapeSignatureFineChild` node type (never `ShapeSignature`),
    `refines_quantum`-edged to the parent, exactly mirroring gate (b)'s coarse/mid mechanism
    one ladder step finer. An exact sub-fine match mints nothing."""
    s, ag, native = _boot()
    parent_pts = [(1, 1), (2, 1), (3, 1)]
    _add_subfine_parent(s, "A", parent_pts, [(1, 1), (2, 1), (3, 1)])
    baseline_primary = sc._existing_names(s, "stroke")

    # TURN mismatches at sub-fine, LEN matches -> a turn-only eager child.
    span_turn = _full_sig([(9, 1), (2, 1), (3, 1)])
    res_turn = ink._eager_child_or_note(
        s, s, native, ag, s.add_node("Stroke", {}), "A", span_turn,
        segments=3, subfine_turn_bins=sc.SUBFINE_TURN_BINS, subfine_len_bins=sc.SUBFINE_LEN_BINS,
        grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_turn is not None and res_turn["minted"] is True
    assert res_turn["status"] == "refine_turn"
    child = sc._find_stroke_node(s, res_turn["name"], kind="stroke_fine_child",
                                 node_type="ShapeSignatureFineChild")
    assert child is not None, "the eager child must live under ShapeSignatureFineChild"
    assert s.node(child)["attrs"]["kind"] == "stroke_fine_child"
    assert s.node(child)["attrs"]["refined_dim"] == "turn"
    assert s.node(child)["attrs"]["refines"] == "A"
    parents = list(s.neighbours(child, "refines_quantum"))
    assert len(parents) == 1 and s.node(parents[0])["attrs"]["name"] == "A"

    # NEVER installed into the PRIMARY codebook -- "base grains untouched" (structural, not
    # merely a `kind` convention): the primary `ShapeSignature{kind:'stroke'}` set is
    # byte-identical before/after the mint.
    assert sc._existing_names(s, "stroke") == baseline_primary
    assert sc._find_stroke_node(s, res_turn["name"]) is None, (
        "an eager child must be INVISIBLE to the primary (kind='stroke') lookup")

    # LEN mismatches, TURN matches -> a len-only eager child.
    span_len = _full_sig([(1, 9), (2, 1), (3, 1)])
    res_len = ink._eager_child_or_note(
        s, s, native, ag, s.add_node("Stroke", {}), "A", span_len,
        segments=3, subfine_turn_bins=sc.SUBFINE_TURN_BINS, subfine_len_bins=sc.SUBFINE_LEN_BINS,
        grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_len is not None and res_len["minted"] is True
    assert res_len["status"] == "refine_len"
    assert res_len["name"] != res_turn["name"]

    # An EXACT sub-fine match -> nothing to refine, honest "exact_at_subfine" label (not the
    # fine-grain wording, so a reader never confuses the two mechanisms).
    exact = _full_sig([(1, 1), (2, 1), (3, 1)])
    res_exact = ink._eager_child_or_note(
        s, s, native, ag, s.add_node("Stroke", {}), "A", exact,
        segments=3, subfine_turn_bins=sc.SUBFINE_TURN_BINS, subfine_len_bins=sc.SUBFINE_LEN_BINS,
        grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_exact == {"status": "exact_at_subfine", "minted": False}

    # A parent with NO subfine_signature (a stale/pre-eager-child entry) -> honest no-op,
    # never a crash.
    s.add_node("ShapeSignature", {"name": "B", "kind": "stroke",
                                  "signature": json.dumps(_full_sig(parent_pts))})
    res_stale = ink._eager_child_or_note(
        s, s, native, ag, s.add_node("Stroke", {}), "B", span_turn,
        segments=3, subfine_turn_bins=sc.SUBFINE_TURN_BINS, subfine_len_bins=sc.SUBFINE_LEN_BINS,
        grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res_stale is None


def test_eager_child_gate2_dedup_bounded_on_repeated_jitter():
    """'children bounded (no over-minting on jitter)': repeating the EXACT SAME sub-fine-
    mismatched observation N times must mint exactly ONCE (content-keyed dedup, the SAME
    idempotent-by-name guarantee the OOV mint path already gives) -- N-1 further calls find
    the SAME child, they never grow the fine-child population."""
    s, ag, native = _boot()
    _add_subfine_parent(s, "A", [(1, 1), (2, 1), (3, 1)], [(1, 1), (2, 1), (3, 1)])
    span_turn = _full_sig([(9, 1), (2, 1), (3, 1)])

    names = set()
    for _ in range(5):
        res = ink._eager_child_or_note(
            s, s, native, ag, s.add_node("Stroke", {}), "A", span_turn,
            segments=3, subfine_turn_bins=sc.SUBFINE_TURN_BINS,
            subfine_len_bins=sc.SUBFINE_LEN_BINS, grid=sc.DEFAULT_GRID,
            scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
        assert res is not None and res.get("name")
        names.add(res["name"])

    assert len(names) == 1, f"the SAME jitter must dedup to ONE child, got {names!r}"
    fine_children = [n for n in s.nodes("ShapeSignatureFineChild")
                     if s.node(n)["attrs"].get("name") == list(names)[0]]
    assert len(fine_children) == 1, (
        "re-observing the SAME sub-fine content must not grow the FineChild population "
        f"(found {len(fine_children)} nodes for the one dedup'd name)")

    # A GENUINELY DIFFERENT sub-fine mismatch (a distinct turn value) DOES mint a distinct,
    # SECOND child -- discrimination, not fragmentation.
    span_turn2 = _full_sig([(8, 1), (2, 1), (3, 1)])
    res2 = ink._eager_child_or_note(
        s, s, native, ag, s.add_node("Stroke", {}), "A", span_turn2,
        segments=3, subfine_turn_bins=sc.SUBFINE_TURN_BINS, subfine_len_bins=sc.SUBFINE_LEN_BINS,
        grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")
    assert res2["name"] not in names
    all_children_of_a = [n for n in s.nodes("ShapeSignatureFineChild")
                         if s.node(n)["attrs"].get("refines") == "A"]
    assert len(all_children_of_a) == 2, (
        f"exactly two DISTINCT sub-fine mismatches must yield exactly two children, "
        f"got {len(all_children_of_a)}")


def test_eager_child_gate3_grain_vocabulary_reports_fine_children():
    """`grain_vocabulary_report`'s NEW `fine_children`/`fine_children_by_parent` fields count
    the SEPARATE `ShapeSignatureFineChild` population, excluded from `top`/`children`/`total`
    (which describe the PRIMARY recognition library, untouched by eager minting)."""
    s, ag, native = _boot()
    _add_subfine_parent(s, "A", [(1, 1), (2, 1), (3, 1)], [(1, 1), (2, 1), (3, 1)])
    report0 = sc.grain_vocabulary_report(s)
    assert report0["fine_children"] == 0
    assert report0["total"] == len(sc._existing_names(s, "stroke"))

    ink._eager_child_or_note(
        s, s, native, ag, s.add_node("Stroke", {}), "A", _full_sig([(9, 1), (2, 1), (3, 1)]),
        segments=3, subfine_turn_bins=sc.SUBFINE_TURN_BINS, subfine_len_bins=sc.SUBFINE_LEN_BINS,
        grid=sc.DEFAULT_GRID, scale_bins=sc.DEFAULT_SCALE_BINS, category="stroke_shapes")

    report1 = sc.grain_vocabulary_report(s)
    assert report1["fine_children"] == 1
    assert report1["fine_children_by_parent"] == {"A": 1}
    # The PRIMARY library counts are UNCHANGED by an eager mint -- "base grains untouched".
    assert report1["top"] == report0["top"]
    assert report1["total"] == report0["total"]


def test_eager_child_gate4_live_decode_ink_additive_identity():
    """LIVE integration: two real arcs with DIFFERENT sweep angles (150deg / 330deg, chosen
    empirically so their FINE-grain `seg` quantization ties exactly at `DEFAULT_TURN_BINS`/
    `DEFAULT_LEN_BINS` but their SUB-FINE quantization does not) both recognize the SAME
    codebook parent at the FINE tier (additive identity: `"name"` never changes because of
    eager minting) while ONLY the geometrically-different one mints/carries a `fine_child` —
    "within-tier variation is the mint signal now that misses have stopped." The PRIMARY
    stroke codebook's size stays unaffected by however many eager children mint underneath
    it ("base grains untouched")."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    r = 1.0

    def arc(sweep_deg):
        return gmw._sample_stroke("arc", [r, r, r, -sweep_deg / 2, sweep_deg / 2], 200)

    sc.build_stroke_codebook(s, sources=[("bulge", arc(150.0).tolist())], include_pickle=False)
    primary_before = sc._existing_names(s, "stroke")

    results = {}
    for sweep in (150.0, 330.0):
        ink_node = ink.ingest_ink(s, arc(sweep).tolist(), max_knots=48)
        res = ink.decode_ink(s, ink_node, min_span=40, max_span=48)
        assert len(res["recognized"]) == 1, f"expected a single recognized span, got {res!r}"
        results[sweep] = res["recognized"][0]

    assert results[150.0]["tier"] == results[330.0]["tier"] == "fine"
    assert results[150.0]["name"] == results[330.0]["name"] == "bulge", (
        "the PARENT identity must stay the SAME across both instances regardless of eager "
        f"child minting, got {results[150.0]['name']!r} / {results[330.0]['name']!r}")
    assert "fine_child" not in results[150.0], (
        "the geometrically-IDENTICAL-to-its-own-codebook-entry instance must not mint an "
        "eager child (exact at sub-fine too)")
    assert results[330.0].get("fine_child"), (
        "the geometrically-DIFFERENT-at-sub-fine instance must carry a fine_child")

    # The primary codebook is unaffected by however many eager children happened to mint.
    assert sc._existing_names(s, "stroke") == primary_before

    # `enable_eager_children=False` must produce IDENTICAL parent recognition (the
    # non-negotiable "parent relations byte-identical with the flag off/on") -- just with no
    # `fine_child` field ever populated, even for the variant that DOES carry one when on.
    ink_node_off = ink.ingest_ink(s, arc(330.0).tolist(), max_knots=48)
    res_off = ink.decode_ink(s, ink_node_off, min_span=40, max_span=48,
                             enable_eager_children=False)
    assert len(res_off["recognized"]) == 1
    assert res_off["recognized"][0]["name"] == "bulge"
    assert "fine_child" not in res_off["recognized"][0]


# ===========================================================================
# RUN 23 -- CONTINUOUS-NOVELTY MINTING gates (scratchpad's own run-16 law, "continuous beats
# quantized," applied to GROWTH — commit 9762130f's closing clause, the runs-19-22 identity-
# grain wall's LEARN-side attack): `stroke_codebook.continuous_mint_or_note` /
# `ink_decode`'s `enable_continuous_mint` flag. Additive, default OFF — every gate above this
# section is unaffected; these gates exercise ONLY the new opt-in path.
# ===========================================================================
def _bow(amp: float, n: int = 13) -> np.ndarray:
    """A gently-curved path whose per-segment relative turn stays within the SAME quantized
    bin as a straight line's (`turn_q == 0` on every segment, verified directly against
    `stroke_codebook._quantize` at `CMINT_DK`'s own bins for `|amp| <= 0.14`) while its real-
    valued (DTW) shape is visibly, measurably different — the SAME "ties at a discrete grain,
    differs continuously" structure the eager-child gate's own 150/330-degree arcs already
    exploit empirically (`test_eager_child_gate4_live_decode_ink_additive_identity`), built
    directly here instead (amplitude is a continuous, directly-controllable knob — no angle
    search needed). `amp=+0.14` and `amp=-0.14` tie with the `amp=0.0` line at the SAME
    discrete signature (empirically verified: DTW distance from the line is 0.123 either way)
    while being mutually FAR from each other (DTW 0.238) — a textbook 'discrete bin collapses
    continuous diversity' case, the exact shape of the runs-19-22 wall."""
    x = np.linspace(0.0, 1.0, n)
    y = amp * np.sin(np.pi * x)
    return np.stack([x, y], axis=1)


CMINT_DK = dict(segments=8, turn_bins=16, len_bins=6, grid=6, scale_bins=6)


def test_run23_continuous_mint_or_note_near_no_mint_far_mints_and_dedups():
    """Unit gate (mirrors `test_gate_c_dtw_fallback_near_and_far`'s own style, one level up
    the growth ladder): a NEAR observation (small perturbation of the parent's own prototype)
    must NOT mint; a FAR observation (well beyond `threshold`) MUST mint a peer quantum tagged
    `continuous_parent`; a THIRD call with the SAME far points must NOT mint again (the
    family-nearest-neighbour check IS the dedup — the just-minted sibling is now the nearest,
    well under threshold, so a repeat recognizes it instead of minting a third)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line = _bow(0.0)
    res = sc.grow_stroke_quantum(s, line.tolist(), "cmint_unit_line", **CMINT_DK)
    assert res["grown"]
    before = sc._existing_names(s, "stroke")

    near = _bow(0.01)
    r_near = sc.continuous_mint_or_note(s, "cmint_unit_line", near.tolist(), threshold=0.10,
                                        **CMINT_DK)
    assert r_near["checked"] is True and r_near["minted"] is False
    assert r_near["nearest"] == "cmint_unit_line" and r_near["family_size"] == 1
    assert sc._existing_names(s, "stroke") == before, "a near observation must not mint"

    far = _bow(0.14)
    r_far = sc.continuous_mint_or_note(s, "cmint_unit_line", far.tolist(), threshold=0.10,
                                       **CMINT_DK)
    assert r_far["minted"] is True
    new_name = r_far["name"]
    assert new_name == "cmint_unit_line__cont_1"
    assert sc._existing_names(s, "stroke") == before | {new_name}
    new_node = sc._find_stroke_node(s, new_name)
    assert s.node(new_node)["attrs"].get("continuous_parent") == "cmint_unit_line"

    # A REPEAT of the SAME far observation must dedup against the sibling it just minted --
    # NOT mint a third quantum (the family Argmin now finds the sibling nearest, near-zero).
    r_far2 = sc.continuous_mint_or_note(s, "cmint_unit_line", far.tolist(), threshold=0.10,
                                        **CMINT_DK)
    assert r_far2["minted"] is False, "a repeat of the SAME variant must dedup, not re-mint"
    assert r_far2["nearest"] == new_name
    assert sc._existing_names(s, "stroke") == before | {new_name}


def test_run23_continuous_mint_honest_non_crash_no_quantum_no_prototype():
    """Honest non-crash (mirrors `_dtw_fallback`'s own 'no candidates' branch): a `chosen_name`
    with no held node, or one whose family carries no `prototype` attr at all, returns
    `checked=False` — never a crash, never a fabricated mint."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    res = sc.continuous_mint_or_note(s, "cmint_no_such_quantum", _bow(0.1).tolist(),
                                     threshold=0.1, **CMINT_DK)
    assert res == {"minted": False, "checked": False, "reason": "no such quantum"}

    s.add_node("ShapeSignature", {"name": "cmint_no_proto", "kind": "stroke"})
    res2 = sc.continuous_mint_or_note(s, "cmint_no_proto", _bow(0.1).tolist(), threshold=0.1,
                                      **CMINT_DK)
    assert res2["checked"] is False and res2["minted"] is False


def test_run23_continuous_mint_two_far_shared_signature_strokes_mint_two_quanta_live():
    """LIVE integration through the FULL `decode_ink` pipeline — the launch instructions' own
    literal gate: 'two strokes sharing a quantized signature but DtwTo-far mint two quanta
    with the flag on, one with it off.' `_bow(+0.14)`/`_bow(-0.14)` tie with the straight-line
    parent's own discrete signature (see `_bow`'s own docstring) while being mutually far in
    continuous shape. Matching (`"family"`, the chosen recognition identity) stays IDENTICAL
    with the flag on vs off; only the codebook's own vocabulary differs — the non-negotiable
    "no bin change anywhere" the design requires."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    line = _bow(0.0)

    def _run(enable: bool):
        s, ag, native = _boot()
        res = sc.grow_stroke_quantum(s, line.tolist(), "cmint_pipe_line", **CMINT_DK)
        assert res["grown"]
        before = sc._existing_names(s, "stroke")
        families = []
        for amp in (0.14, -0.14):
            b = _bow(amp)
            ink_node = ink.ingest_ink(s, b.tolist(), max_knots=13)
            r = ink.decode_ink(s, ink_node, min_span=13, max_span=13,
                               enable_continuous_mint=enable,
                               continuous_mint_threshold=0.10, **CMINT_DK)
            assert len(r["recognized"]) == 1
            families.append(r["recognized"][0]["family"])
            if not enable:
                assert r["continuous"] == [], "the flag OFF must never populate 'continuous'"
        after = sc._existing_names(s, "stroke")
        new_top = {n for n in (after - before) if "__cont_" in n}
        return families, new_top

    families_on, new_on = _run(True)
    families_off, new_off = _run(False)

    assert families_on == families_off == ["cmint_pipe_line", "cmint_pipe_line"], (
        "recognition/matching (the FAMILY identity) must be IDENTICAL with the flag on/off -- "
        "continuous minting only ever grows the codebook, never changes what a span recognizes "
        f"as, got on={families_on!r} off={families_off!r}")
    assert len(new_on) == 2, f"exactly two NEW continuous-mint quanta expected, got {new_on!r}"
    assert new_off == set(), "the flag OFF must grow the codebook by exactly zero"


def test_run23_continuous_mint_growth_curve_sanity():
    """Growth-curve sanity at the smallest scale (the phase-1 'growth-then-flatten' concern,
    unit-level): decoding the SAME far variant N times must mint exactly ONCE, never grow
    linearly with N — the family-nearest-neighbour dedup IS what makes growth SATURATE
    (directly the mechanism the run-23 LEARN sweep's own growth-curve diagnostic depends on)."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line = _bow(0.0)
    sc.grow_stroke_quantum(s, line.tolist(), "cmint_growth_line", **CMINT_DK)
    before = sc._existing_names(s, "stroke")

    far = _bow(0.14)
    mints = []
    for _ in range(5):
        r = sc.continuous_mint_or_note(s, "cmint_growth_line", far.tolist(), threshold=0.10,
                                       **CMINT_DK)
        mints.append(r["minted"])
    assert mints == [True, False, False, False, False], (
        f"repeated identical far observations must mint EXACTLY once, got {mints!r}")
    assert len(sc._existing_names(s, "stroke") - before) == 1


def test_run23_continuous_mint_anchors_through_prototype_less_refinement_child():
    """Honest bug found empirically against real Omniglot ink (see the run-23 gate script's
    own commentary): `ink_decode._refine_or_note`'s coarse/mid/DtwTo-triggered path installs a
    refinement CHILD via `grow_stroke_refinement_quantum`'s DEFAULT `node_type`/`kind` — a
    TOP-LEVEL `ShapeSignature{kind:"stroke"}` peer that competes as a "fine" candidate in
    LATER decodes, per that function's own docstring — but that install path stores only the
    already-quantized signature, never a continuous prototype. `continuous_mint_or_note` must
    still work when `chosen_name` IS such a prototype-less child: `_prototype_anchor` walks
    the child's own `refines` attr up to the nearest ancestor that DOES carry a prototype (the
    original `grow_stroke_quantum`-installed root, in this construction) and anchors the
    family/mint/dedup there — `checked` must be `True`, never silently `False`."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line = _bow(0.0)
    sc.grow_stroke_quantum(s, line.tolist(), "cmint_anchor_root", **CMINT_DK)

    # A hand-built refinement CHILD, mirroring `grow_stroke_refinement_quantum`'s own DEFAULT
    # top-level install exactly (no `prototype` attr — the honest gap this gate targets).
    sc.grow_stroke_refinement_quantum(
        s, "cmint_anchor_root__ref_turn_x", "cmint_anchor_root", "turn",
        sc._quantize(native, line.tolist(), canonical_pose=True, **CMINT_DK)["signature"],
        **CMINT_DK)
    child_node = sc._find_stroke_node(s, "cmint_anchor_root__ref_turn_x")
    assert child_node is not None
    assert not s.node(child_node)["attrs"].get("prototype"), (
        "the hand-built child must reproduce the real gap -- no prototype attr")

    anchor = sc._prototype_anchor(s, "cmint_anchor_root__ref_turn_x")
    assert anchor == "cmint_anchor_root"

    near = _bow(0.01)
    r_near = sc.continuous_mint_or_note(s, "cmint_anchor_root__ref_turn_x", near.tolist(),
                                        threshold=0.10, **CMINT_DK)
    assert r_near["checked"] is True, f"must anchor through the child, got {r_near!r}"
    assert r_near["minted"] is False
    assert r_near["anchor"] == "cmint_anchor_root"
    assert r_near["requested_as"] == "cmint_anchor_root__ref_turn_x"

    far = _bow(0.14)
    r_far = sc.continuous_mint_or_note(s, "cmint_anchor_root__ref_turn_x", far.tolist(),
                                       threshold=0.10, **CMINT_DK)
    assert r_far["minted"] is True
    assert r_far["name"] == "cmint_anchor_root__cont_1", (
        "a mint requested THROUGH a refinement child must be named off the ANCHOR, not the "
        f"prototype-less child, got {r_far['name']!r}")
    new_node = sc._find_stroke_node(s, r_far["name"])
    assert s.node(new_node)["attrs"].get("continuous_parent") == "cmint_anchor_root"


def test_run23_continuous_mint_default_off_decode_ink_byte_identical():
    """Additivity: `decode_ink`'s DEFAULT call (no `enable_continuous_mint` kwarg at all) must
    carry a `"continuous": []` field and mint NOTHING new, even when fed a far-shaped stroke
    that WOULD mint if the flag were on — the non-negotiable "every existing caller behaves
    byte-identically" this codebase's every opt-in flag has required so far."""
    if not SQ_LIVE:
        pytest.skip(SQ_SKIP)
    s, ag, native = _boot()
    line = _bow(0.0)
    sc.grow_stroke_quantum(s, line.tolist(), "cmint_default_line", **CMINT_DK)
    before = sc._existing_names(s, "stroke")

    far = _bow(0.14)
    ink_node = ink.ingest_ink(s, far.tolist(), max_knots=13)
    r = ink.decode_ink(s, ink_node, min_span=13, max_span=13, **CMINT_DK)
    assert r["continuous"] == []
    # No "__cont_" continuous-mint quantum may appear (the pre-existing, UNRELATED refinement
    # rung may still mint its own "__ref_*" child at the "mid" tier this span recognizes at --
    # that mechanism predates this run and is untouched; this gate is scoped to CONTINUOUS
    # mints only).
    new_cont = {n for n in (sc._existing_names(s, "stroke") - before) if "__cont_" in n}
    assert new_cont == set()
