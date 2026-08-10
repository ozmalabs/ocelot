"""character_compose — DISCRIMINATION lever (c) of scratchpad/HANDWRITING_DESIGN.md:
"CHARACTER COMPOSITION = THE SAME LOOP ONE LEVEL UP." A character is an order-N object of
stroke quanta + RELATIVE poses; this module is the MECHANICAL builder that turns a decoded
ink's per-stroke results (each already recognized/refined/minted by `domains/ink_decode.py`,
each carrying its own OBSERVED geometry) into a ShapeSignature-format relation-system at the
CHARACTER grain:

  ["strokeq", k, <quantum-or-child name>]      one per stroke, k = draw order — the
                                                composition SKELETON (which quantum, in what
                                                order); analogous to nothing at stroke grain
                                                (a stroke has no sub-parts), this is what is
                                                genuinely NEW one level up.
  ["rel", k, dx_q, dy_q, do_q, ds_q]           stroke k's pose relative to the CHARACTER's
                                                OWN translate+rotate+scale-normalized frame
                                                (`_character_frame`) — ROTATION/TRANSLATION/
                                                SCALE-INVARIANT to how the WHOLE character was
                                                drawn, analogous to a stroke's own invariant
                                                `seg` relations; this is what CARRIES the
                                                arrangement (identity) a bare multiset of
                                                stroke names cannot (the T-vs-L-vs-+ proof).
  ["cpose_x", x_q] / ["cpose_y", y_q] /
  ["cpose_o", o_q] / ["cpose_s", s_q]          the CHARACTER's own ABSOLUTE placement/
                                                orientation/scale (own-bbox-relative, same
                                                "self-bbox limitation" a stroke's own `pose_*`
                                                already documents) — analogous to a stroke's
                                                separate `pose_x`/`pose_y`/`pose_o`/`pose_s`
                                                singleton relations, installed at whatever
                                                NATURAL absolute pose the first authored
                                                instance actually had (see
                                                `compose_character_signature`'s docstring for
                                                why a fixed zero PIN — the stroke-level
                                                `canonical_pose` convention — does NOT carry
                                                over cleanly to characters) so a LATER
                                                genuinely-transformed instance's residual is
                                                confined to the dims that transform actually
                                                touched — "a shifted/scaled/rotated WHOLE
                                                character = rung-1 pose deltas at CHARACTER
                                                level."
  ["strokeq_fine", k, <fine child name>]       EAGER CHILD MINTING (2026-07-02,
                                                scratchpad/HANDWRITING_DESIGN.md's "EAGER
                                                CHILD MINTING" section, the a6fe069b residual)
                                                — an ADDITIONAL relation, present only when
                                                stroke k's fine-tier recognition ALSO minted/
                                                matched a sub-fine `ShapeSignatureFineChild`
                                                (`ink_decode._eager_child_or_note`). NEVER a
                                                substitute for "strokeq" above — "IDENTITY IS
                                                ADDITIVE" (the run-5 lesson): the generalizing
                                                parent-level `strokeq` signal that earned 33.8%
                                                stays byte-identical whether or not a child
                                                exists; `strokeq_fine` only ever ADDS
                                                discrimination. Gated by
                                                `compose_character_signature`'s
                                                `include_fine_children` flag — the ablation
                                                the design asks for ("the gate logs BOTH
                                                scores every episode").
  ["rel2", i, j, dx_q, dy_q, do_q, ds_q]       HIGHER-ORDER ARRANGEMENT RELATIONS (2026-07-03,
                                                scratchpad/HANDWRITING_DESIGN.md's "HIGHER-
                                                ORDER ARRANGEMENT RELATIONS" section, the
                                                97d54623 residual): ONE relation per NON-
                                                ADJACENT stroke pair (`j > i+1` in draw order —
                                                consecutive pairs stay carried by "rel" above,
                                                unchanged) encoding stroke `j`'s pose RELATIVE
                                                TO stroke `i`, mechanically DERIVED from the
                                                two strokes' own already-computed "rel" pose
                                                bins (`x_q`/`y_q`/`orient_q`/`scale_q`, in the
                                                SAME character frame, at the SAME bins this
                                                call already used for "rel" — no second
                                                quantization, no new geometry, pure integer
                                                arithmetic on values a held Term already
                                                produced: `dx_q = x_q[j]-x_q[i]`,
                                                `dy_q = y_q[j]-y_q[i]`,
                                                `do_q = wrap_signed(orient_q[j]-orient_q[i],
                                                turn_bins)` [the SAME signed-bin wraparound
                                                `runners/dsl/src/strokes.rs::
                                                quantize_signed_angle` uses for `pose_o` itself
                                                — `orient_q` is a SIGNED bin in `(-turn_bins/2,
                                                turn_bins/2]`, so a plain difference of two such
                                                values can leave that range and must be
                                                re-wrapped into it, or two orientations near the
                                                +180/-180 seam would spuriously look maximally
                                                far apart], `ds_q = scale_q[j]-scale_q[i]`
                                                (`x_q`/`y_q`/`scale_q` are plain UNSIGNED
                                                buckets — no wraparound). WHY: naive coverage
                                                (`_coverage_term`) tests each relation
                                                INDEPENDENTLY — it can verify stroke `i`'s own
                                                "rel" and stroke `j`'s own "rel" separately but
                                                has no single atomic fact JOINTLY constraining
                                                the two (`scripts/jabberwock_omniglot_
                                                arrangement_diag.py`'s Phase-A diagnosis: 52.8%
                                                of misses decided by a TIE — two candidates
                                                agreeing on every INDIVIDUAL stroke's own pose
                                                while differing on how far-apart strokes relate
                                                to EACH OTHER go unresolved). `rel2` gives the
                                                held Sum+In coverage metric a direct,
                                                independently-checkable fact about that
                                                non-adjacent PAIR, without touching the metric
                                                itself (still "the SAME naive strict coverage",
                                                per the design's own wording — STRICTNESS IS
                                                THE SIGNAL, partial credit measured worse
                                                twice, so `rel2` is exact-match, whole-tuple,
                                                same as every other relation here). Gated by
                                                `compose_character_signature`'s `include_rel2`
                                                flag (default `False` — OPT-IN, not a silent
                                                default-behaviour change for the many existing
                                                unflagged callers across this codebase; a
                                                caller wanting the new lever passes
                                                `include_rel2=True` explicitly, mirroring
                                                `canonical`'s own opt-in convention below) —
                                                strictly ADDITIVE: the default (flag off)
                                                reproduces the pre-`rel2` signature byte-for-
                                                byte, flag on only ever APPENDS `rel2` tuples
                                                at the end.

NO NEW MACHINERY (design's own constraint): every relation above is built by ONE reused
primitive — the held `StrokeQuantize` Term (via `stroke_codebook._quantize`, including its
`bounds` field, landed but UNUSED until this module) — called once per stroke plus once for
the whole character; no new Rust, no new DSL vocabulary. Character quanta are `ShapeSignature`
nodes with `kind="character"` (the SAME node type stroke quanta use, just a different `kind`
value) so the EXISTING `shape_decode_loop.json` ladder (`sd_decode`/`sd_recognize`/
`sd_transform_decode`/`sd_mint_quantum`/`sd_redecode`, unchanged) recognizes/transform-
recognizes/mints them via `domains.reflective_faculty.induce_concern` exactly like a stroke
observation — "characters are just ShapeSignature kind='character' + Observations."

ARCHITECTURE (CLAUDE.md): every function here is a MECHANICAL translation of already-decided
values (per-stroke identities `ink_decode.py`'s ladder already resolved, raw pen-path geometry)
into graph data — no ranking, no argmin/argmax, no conditional over graph STATE deciding what
to do next. `grow_character_quantum` mirrors `stroke_codebook.grow_stroke_quantum`'s own
idempotent-by-name install + `teach()` persistence + codebook-epoch bump; the RECOGNIZE-vs-MINT
decision for a composed signature is, as for strokes, a HELD Term's (`recognize_or_mint_
character`'s own direct `TransformDecode` read for the identity/rung-1-transform case — RUN-4
LEVERS "LEVER 1" — falling to the seeded `sd_*` rules via `induce_concern` only for genuinely
novel arrangements), never this module's Python."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import numpy as np

from domains.reflective_faculty import _agent_root_node, induce_concern
from domains.stroke_codebook import (
    DEFAULT_GRID, DEFAULT_LEN_BINS, DEFAULT_SCALE_BINS, DEFAULT_SEGMENTS, DEFAULT_TURN_BINS,
    _existing_names, _native, _quantize, _sub, _teach_agent,
)
from domains.teach import teach

DEFAULT_CATEGORY = "character_shapes"
_POSE_PREDS = ("pose_x", "pose_y", "pose_o", "pose_s")


# --------------------------------------------------------------------------- #
#  CHARACTER FRAME — pure geometry (translate-to-start + rotate-to-initial-
#  heading + arc-length-scale-normalize), the SAME construction
#  `stroke_codebook._invariant_points` performs for one stroke's own DTW
#  prototype, applied here to the WHOLE character's point cloud WITHOUT
#  resampling (so per-stroke (start, end) index ranges into the input stay
#  valid slices of the output — `_invariant_points`'s own fixed-length
#  resample would scramble those indices, which is why this is a separate,
#  small function rather than a reused call).
# --------------------------------------------------------------------------- #
def _character_frame(points, n_probe: int = 16) -> np.ndarray:
    """Translate/rotate/scale-normalize `points` (a plain `[[x, y], ...]` array covering the
    WHOLE character, every stroke's points concatenated in draw order) into a canonical frame:
    origin at the first point, heading zeroed to the initial direction (estimated via a SHORT
    arc-length resample probe, `n_probe` points — robust to a noisy first two raw points,
    mirrors `_invariant_points`'s own probe), and arc length scaled to 1. Applied to the
    ORIGINAL (unresampled) point array, preserving every index — `compose_character_signature`
    slices per-stroke sub-ranges straight out of the result. Degenerate (<2 points) input is
    returned unchanged (nothing to normalize; callers fall back to the raw points' own bbox)."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return pts
    from domains import glyph_motor_world as gmw
    probe = gmw._resample_arclen(pts, max(2, n_probe))
    origin = probe[0]
    heading_vec = probe[1] - probe[0]
    theta = -np.arctan2(heading_vec[1], heading_vec[0])
    c, si = np.cos(theta), np.sin(theta)
    rot = np.array([[c, -si], [si, c]])
    total = float(np.sum(np.linalg.norm(np.diff(probe, axis=0), axis=1))) or 1.0
    return ((pts - origin) @ rot.T) / total


def _frame_bbox(frame: np.ndarray) -> tuple:
    if frame.ndim != 2 or frame.shape[0] < 2:
        return (0.0, 0.0, 1.0, 1.0)
    x0, y0 = float(frame[:, 0].min()), float(frame[:, 1].min())
    x1, y1 = float(frame[:, 0].max()), float(frame[:, 1].max())
    if x1 <= x0:
        x1 = x0 + 1.0
    if y1 <= y0:
        y1 = y0 + 1.0
    return (x0, y0, x1, y1)


# --------------------------------------------------------------------------- #
#  COMPOSE — mechanical: stroke identities + geometry -> the character-grain
#  relation-system.
# --------------------------------------------------------------------------- #
def compose_character_signature(native, stroke_points: list, *,
                                 segments: int = DEFAULT_SEGMENTS,
                                 turn_bins: int = DEFAULT_TURN_BINS,
                                 len_bins: int = DEFAULT_LEN_BINS, grid: int = DEFAULT_GRID,
                                 scale_bins: int = DEFAULT_SCALE_BINS,
                                 canonical: bool = False,
                                 include_fine_children: bool = True,
                                 include_rel2: bool = False,
                                 include_substroke: bool = False) -> dict[str, Any]:
    """`stroke_points`: `[(points, identity_name), ...]` OR `[(points, identity_name,
    fine_child_name_or_None), ...]` OR `[(points, identity_name, fine_child_name_or_None,
    substroke_points_or_None), ...]` (BRANCH A EXECUTION, see `include_substroke` below) in
    DRAW ORDER k=0..n-1 — each item's OWN raw pen-path
    points (already recognized/refined/minted by `ink_decode.decode_ink`'s per-pen-stroke
    lattice; `identity_name` is that decode's OWN resolved identity, the DISCRIMINATION item
    (a) deepest-match name where refinement applies). Concatenates all strokes' points (draw
    order) for ONE whole-character `StrokeQuantize` call (the CHARACTER's own absolute
    `cpose_*`) and ONE `_character_frame` normalization (the invariant `rel` frame), then
    quantizes each stroke's OWN slice of the normalized frame against the character's own bbox
    (`bounds`) for its `rel` relation. Returns `{signature, bbox, n_strokes}` — `signature` is
    the composed relation-system, `ShapeSignature`-format, ready to install
    (`grow_character_quantum`) or observe (`domains.reflective_faculty.induce_concern`).

    EAGER CHILD MINTING (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING"
    section, the a6fe069b residual — "IDENTITY IS ADDITIVE"): a per-stroke 3-tuple's third
    element, when present and `include_fine_children` (default `True`), ADDS a SEPARATE
    `["strokeq_fine", k, fine_child_name]` relation ALONGSIDE the existing
    `["strokeq", k, identity_name]` — `identity_name`/`["strokeq", k, ...]` is NEVER
    substituted or altered by this (the run-5 lesson, non-negotiable: the generalizing
    parent-level signal that earned 33.8% stays exactly as it was). `include_fine_children`
    lets a caller (the Omniglot gate script) log BOTH the with- and without-children composed
    accuracy from the SAME decode, by composing once and (for "without") simply filtering
    `strokeq_fine` relations back out — see that script's `decode_char_signature` for the
    ablation this enables. A 2-tuple item (no third element — every pre-existing caller/test)
    behaves byte-identically (nothing to add, flag or no flag).

    `canonical` (default `False` — QUERY convention; see RUN-4 LEVERS "LEVER 1" below for the
    now-RECOMMENDED codebook-authoring convention): mirrors `stroke_codebook.grow_stroke_
    quantum`'s `canonical_pose` — pins `cpose_*` to a FIXED `(0, 0, 0, mid-scale)` reference
    instead of the instance's own observed absolute pose. A QUERY signature (an instance being
    classified/observed) always wants its OWN actual pose (`canonical=False`), never a pin —
    this default is for callers building a query, not a codebook entry.

    RUN-4 LEVERS "LEVER 1" — ROTATION-INVARIANT CHARACTER FRAME (2026-07-02,
    scratchpad/HANDWRITING_DESIGN.md, the c1b83669 residual: "cpose_x/y are axis-aligned-bbox-
    relative... character rung 1 only survives translate/scale within the seeded max_dims=2").
    An EARLIER pass of this module reasoned that pinning `cpose_*` to zero for codebook entries
    could never work because a general character's natural placement would show a residual on
    all 4 `cpose_*` predicates AT ONCE, exceeding the GENERIC seeded `sd_transform_decode`
    rule's `max_dims=2` — TRUE for that generic rule, but the fix ("mirror the stroke pose_*
    solution exactly") is the SAME one strokes already use: `ink_decode._read_pose_transform`
    does NOT go through the generic seeded rule either — it is a DIRECT `TransformDecode`
    evaluate with its OWN `max_dims=4` (the four pose dimensions). `read_character_transform`/
    `recognize_or_mint_character` below are that SAME direct-read-off pattern at character
    grain: with `max_dims=4` available, a SINGLE relation per `cpose_*` predicate is ALWAYS a
    self-consistent (trivially-uniform, nothing-to-check-against) dimension regardless of its
    magnitude (see `runners/dsl/src/shape_decode.rs::build_candidate`'s per-`(predicate,slot)`
    pooling — a lone-member group can never be internally INCONSISTENT), so ALL FOUR `cpose_*`
    predicates differing simultaneously is `explained` as long as `max_dims>=4` — the
    axis-aligned-bbox-reshaping-under-rotation concern the earlier reasoning worried about
    affects the SEMANTIC cleanliness of the delta VALUE, never whether recognition succeeds.
    `canonical=True` is therefore now the RECOMMENDED convention for codebook-authoring calls
    (mirrors the stroke convention exactly: the codebook entry's `cpose_*` all read `0`/the mid
    scale bin, so an observed instance's delta against it just IS that instance's own absolute
    pose) — used together with `recognize_or_mint_character`'s wider `max_dims`, NOT with the
    generic `induce_concern` ladder (which still only offers `max_dims=2` and stays correct for
    the narrower translate-only/scale-only cases `tests/test_character_composition_migrated.py
    ::test_character_level_rung1_zero_mint` exercises — see that test's own updated docstring).
    `canonical=False` remains the default here (a QUERY'S own convention, unaffected) and
    stays available for a caller with an EXTERNAL canonical reference frame in mind.

    HIGHER-ORDER ARRANGEMENT RELATIONS (2026-07-03, scratchpad/HANDWRITING_DESIGN.md's
    "HIGHER-ORDER ARRANGEMENT RELATIONS" section, the 97d54623 residual — see this module's
    OWN top-of-file docstring for the full "rel2" rationale): `include_rel2` (default
    `False` — OPT-IN, deliberately UNLIKE `include_fine_children`'s default-True: rel2 is a
    NEW, still-under-test lever, and this codebase has MANY existing unflagged callers of
    this function — scripts/jabberwock_omniglot_arrangement_diag.py,
    scripts/jabberwock_omniglot_dynamic_quantization.py's OTHER logged arms (child ablation,
    stroke-order ablation, rotation spot-check), every pre-existing pytest gate — flipping the
    DEFAULT would silently change ALL of their historical numbers, not just add a new one) —
    ADDS, for every NON-ADJACENT stroke pair `j > i+1`, one `["rel2", i, j, dx_q, dy_q, do_q,
    ds_q]` relation mechanically derived from the two strokes' own already-computed "rel" pose
    bins — no new geometry, no second `StrokeQuantize` call, pure integer arithmetic (see
    `_rel2_relations`). Strictly ADDITIVE: `include_rel2=False` (the default) reproduces the
    signature byte-for-byte as if `rel2` did not exist; a caller wanting the NEW headline
    passes `include_rel2=True` EXPLICITLY (`scripts/jabberwock_omniglot_dynamic_
    quantization.py`'s RUN 9 section does exactly this, alongside the UNCHANGED default-False
    call for its own "33.8%" control — the mirror image of how `include_fine_children`'s own
    ablation control is obtained by FILTERING a default-True call, just flipped because this
    flag's default is the other way).

    BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (2026-07-03, scratchpad/HANDWRITING_DESIGN.md's
    section of the same name, the jabberwock's own verdict d2cd7bed): `include_substroke`
    (default `False` — OPT-IN, the SAME "many existing unflagged callers" reasoning
    `include_rel2` already documents) accepts a 4th tuple element per stroke, `substroke_points`
    (`ink_decode.decode_ink`'s own `entry["substroke_points"]` field — raw `(points, name)`
    pairs from the WITHIN-stroke inner lattice, `None`/absent for every pre-existing 2-/3-tuple
    caller). When present, `compose_stroke_signature` (this module's own twin of THIS function,
    one grain down — "compose_character_signature's exact pattern one level down") builds the
    stroke's OWN `subq`/`srel` relation-system, and `substroke_arrangement_key` reduces it to a
    single stable content hash — added as an ADDITIVE `["strokeq_sub", k, <arrangement key>]`
    relation ALONGSIDE (never replacing) `["strokeq", k, name]` — "a stroke's identity ...
    additive relations, never replacing." Two strokes sharing the SAME top-level quantum
    `name` but composed from a DIFFERENT sub-stroke arrangement get DIFFERENT `strokeq_sub`
    keys — the decisive lever this section exists for. `include_substroke=False` (the default)
    reproduces the signature byte-for-byte as if this paragraph did not exist."""
    if not stroke_points:
        return {"signature": [], "bbox": None, "n_strokes": 0}

    # Normalize every item to a uniform 4-tuple (points, identity_name, fine_child_or_None,
    # substroke_points_or_None) -- accepts the pre-existing 2-/3-tuple shapes (every committed
    # caller/test) OR the NEW 4-tuple shape (`ink_decode`'s "substroke_points" field) mechanically,
    # once, up front -- not a decision, a fixed-arity normalization.
    norm_points = [(item[0], item[1], item[2] if len(item) > 2 else None,
                    item[3] if len(item) > 3 else None)
                  for item in stroke_points]

    all_pts = np.concatenate(
        [np.asarray(pts, dtype=float).reshape(-1, 2) for (pts, _n, _fc, _sp) in norm_points], axis=0)
    if all_pts.shape[0] < 2:
        return {"signature": [], "bbox": None, "n_strokes": len(stroke_points)}

    # The CHARACTER's own ABSOLUTE pose ("cpose_*", mirrors a stroke's separate pose_x/y/o/s):
    # canonical-pinned for codebook AUTHORING, the actual observed values otherwise — the part
    # rung-1 TransformDecode reads a delta on when the WHOLE character is shifted/scaled/
    # rotated. `segments=1` here: only the `pose` sub-dict / pose_* relations are read back,
    # the (irrelevant at this call) `seg` relations are dropped below.
    q_whole = _quantize(native, all_pts.tolist(), segments=max(1, segments), turn_bins=turn_bins,
                        len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                        invariant_only=False, canonical_pose=canonical)
    # `q_whole["signature"]` is a LIVE `native.evaluate(...)` result -- Rust Tuples surface as
    # Python `tuple`s, not `list`s -- accept both (see `ink_decode._fine_seg_relations`'s
    # identical note; the same silent-drop bug would otherwise make `cpose_rels` ALWAYS empty).
    cpose_rels = [["c" + rel[0], rel[1]] for rel in q_whole.get("signature", [])
                  if isinstance(rel, (list, tuple)) and rel and rel[0] in _POSE_PREDS]

    # The per-stroke INVARIANT arrangement ("rel", mirrors a stroke's own invariant `seg`):
    # each stroke's pose relative to the character's OWN normalized frame — carries the
    # ARRANGEMENT, never pinned (a rotated/scaled/translated instance of the SAME character
    # reproduces the SAME `rel` relations by construction, since the frame co-transforms).
    frame = _character_frame(all_pts)
    bbox = _frame_bbox(frame)

    strokeq_rels, strokeq_fine_rels, rel_rels, strokeq_sub_rels = [], [], [], []
    pose_by_k: dict[int, dict] = {}
    offset = 0
    for k, (pts, name, fine_child, substroke_points) in enumerate(norm_points):
        n = np.asarray(pts, dtype=float).reshape(-1, 2).shape[0]
        strokeq_rels.append(["strokeq", k, name])
        # EAGER CHILD MINTING -- ADDITIVE: an extra "strokeq_fine" relation, never a
        # substitution for "strokeq" above (see this function's own docstring).
        if include_fine_children and fine_child:
            strokeq_fine_rels.append(["strokeq_fine", k, fine_child])
        # BRANCH A EXECUTION -- SUB-STROKE COMPOSITION -- ADDITIVE: an extra "strokeq_sub"
        # relation keyed on the sub-stroke ARRANGEMENT (never a substitution for "strokeq").
        if include_substroke and substroke_points:
            sub_composed = compose_stroke_signature(
                native, substroke_points, segments=segments, turn_bins=turn_bins,
                len_bins=len_bins, grid=grid, scale_bins=scale_bins)
            arrangement_key = substroke_arrangement_key(sub_composed["signature"])
            if arrangement_key is not None:
                strokeq_sub_rels.append(["strokeq_sub", k, arrangement_key])
        span_frame_pts = frame[offset:offset + n]
        if span_frame_pts.shape[0] >= 2:
            qk = _quantize(native, span_frame_pts.tolist(), segments=segments,
                           turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                           scale_bins=scale_bins, invariant_only=False, bounds=bbox)
            pose = qk["pose"]
            rel_rels.append(["rel", k, pose["x_q"], pose["y_q"], pose["orient_q"],
                             pose["scale_q"]])
            pose_by_k[k] = pose        # HIGHER-ORDER ARRANGEMENT RELATIONS: kept for rel2.
        offset += n

    # HIGHER-ORDER ARRANGEMENT RELATIONS -- strictly ADDITIVE, see this function's own
    # docstring + this module's top-of-file docstring for the "rel2" rationale.
    rel2_rels = _rel2_relations(pose_by_k, turn_bins) if include_rel2 else []

    return {"signature": (strokeq_rels + rel_rels + cpose_rels + strokeq_fine_rels + rel2_rels
                          + strokeq_sub_rels),
            "bbox": bbox, "n_strokes": len(stroke_points)}


# --------------------------------------------------------------------------- #
#  BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (2026-07-03, scratchpad/HANDWRITING_DESIGN.md's
#  section of the same name, the jabberwock's own verdict d2cd7bed): "the sd loop one level
#  DOWN -- a stroke is itself an arrangement of sub-stroke quanta." `compose_stroke_signature`
#  is `compose_character_signature`'s EXACT pattern one level down -- it reuses THIS module's
#  own `_character_frame`/`_frame_bbox` (pure geometry, generic over any point cloud despite
#  the "character" naming — the SAME helpers, unchanged) to build a STROKE's own normalized
#  frame from its sub-stroke points, then quantizes each sub-span's pose against the stroke's
#  own bbox exactly as `compose_character_signature`'s "rel" loop does one level up. NO NEW
#  MACHINERY: the ONLY reused primitive is the held `StrokeQuantize` Term (via `_quantize`),
#  called once per sub-stroke -- same discipline as the character-grain function.
# --------------------------------------------------------------------------- #
def compose_stroke_signature(native, substroke_points: list, *,
                             segments: int = DEFAULT_SEGMENTS, turn_bins: int = DEFAULT_TURN_BINS,
                             len_bins: int = DEFAULT_LEN_BINS, grid: int = DEFAULT_GRID,
                             scale_bins: int = DEFAULT_SCALE_BINS) -> dict[str, Any]:
    """`substroke_points`: `[(points, name), ...]` in INNER draw order (`ink_decode.
    decode_substrokes`'s own `_substroke_points_from_result` output, already recognized/minted
    by the within-stroke inner lattice). Returns `{signature, bbox, n_substrokes}` — `signature`
    is `["subq", m, name]` (the composition SKELETON, one per sub-stroke, `m` = inner draw
    order — the sub-stroke twin of "strokeq") plus `["srel", m, dx_q, dy_q, do_q, ds_q]`
    (sub-stroke `m`'s pose relative to the STROKE's own translate+rotate+scale-normalized
    frame — the sub-stroke twin of "rel", carrying the ARRANGEMENT a bare sequence of
    sub-stroke names cannot). Degenerate (`< 2` total points, or empty) input returns an empty
    signature, never raises — the caller (`substroke_arrangement_key`) treats that as "nothing
    to key", adding no `strokeq_sub` relation for that stroke."""
    if not substroke_points:
        return {"signature": [], "bbox": None, "n_substrokes": 0}
    all_pts = np.concatenate(
        [np.asarray(pts, dtype=float).reshape(-1, 2) for (pts, _n) in substroke_points], axis=0)
    if all_pts.shape[0] < 2:
        return {"signature": [], "bbox": None, "n_substrokes": len(substroke_points)}

    frame = _character_frame(all_pts)
    bbox = _frame_bbox(frame)

    subq_rels, srel_rels = [], []
    offset = 0
    for m, (pts, name) in enumerate(substroke_points):
        n = np.asarray(pts, dtype=float).reshape(-1, 2).shape[0]
        subq_rels.append(["subq", m, name])
        span_frame_pts = frame[offset:offset + n]
        if span_frame_pts.shape[0] >= 2:
            qk = _quantize(native, span_frame_pts.tolist(), segments=segments,
                           turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                           scale_bins=scale_bins, invariant_only=False, bounds=bbox)
            pose = qk["pose"]
            srel_rels.append(["srel", m, pose["x_q"], pose["y_q"], pose["orient_q"],
                              pose["scale_q"]])
        offset += n

    return {"signature": subq_rels + srel_rels, "bbox": bbox, "n_substrokes": len(substroke_points)}


def substroke_arrangement_key(signature: list) -> Optional[str]:
    """A STABLE, content-derived key for a composed sub-stroke signature — mirrors
    `ink_decode._signature_key` exactly, one grain up: two strokes whose sub-stroke ARRANGEMENT
    is IDENTICAL (same `subq`/`srel` content) get the SAME key; a genuinely different
    arrangement (different sub-quantum sequence, or the same sub-quanta at a different relative
    pose) gets a different key. Returns `None` for an empty/degenerate signature — the caller
    adds no `strokeq_sub` relation for that stroke, never a fabricated key."""
    if not signature:
        return None
    return hashlib.sha1(
        json.dumps([list(rel) for rel in signature], sort_keys=True).encode()).hexdigest()[:12]


# --------------------------------------------------------------------------- #
#  HIGHER-ORDER ARRANGEMENT RELATIONS (2026-07-03, scratchpad/HANDWRITING_DESIGN.md's
#  "HIGHER-ORDER ARRANGEMENT RELATIONS" section, the 97d54623 residual) -- see this module's
#  top-of-file docstring for the full "rel2" rationale/format.
# --------------------------------------------------------------------------- #
def _wrap_signed_bin(delta: int, bins: int) -> int:
    """Wrap an integer difference of two SIGNED angle bins (`orient_q`/`pose_o`, each already
    in `(-bins/2, bins/2]` per `runners/dsl/src/strokes.rs::quantize_signed_angle`) back into
    that SAME signed range -- the identical modular arithmetic that Rust function's own
    wrap-then-clamp loop performs, just applied here to a DIFFERENCE of two already-quantized
    bins rather than a raw angle. Without this, two orientations straddling the +180/-180 seam
    (e.g. bins `+7` and `-7` at `turn_bins=16`) would subtract to a spuriously huge value
    (`14`) instead of the true short-way-around difference (`-2`)."""
    bins = max(1, int(bins))
    half = bins // 2
    d = int(delta)
    while d > half:
        d -= bins
    while d < -half:
        d += bins
    return d


def _rel2_relations(pose_by_k: dict, turn_bins: int) -> list:
    """Mechanical (no decision): one `["rel2", i, j, dx_q, dy_q, do_q, ds_q]` relation per
    NON-ADJACENT stroke-index pair (`j > i+1`, both present in `pose_by_k` -- a stroke with no
    "rel" entry, i.e. a degenerate <2-point span, contributes no rel2 relation either, same
    exclusion `compose_character_signature`'s own "rel" loop already applies), derived purely
    by arithmetic on the two strokes' own already-computed "rel" pose bins -- NO second
    `StrokeQuantize` call, no new geometry. `dx_q`/`dy_q`/`ds_q` are plain integer differences
    of UNSIGNED buckets (position/scale never wrap); `do_q` wraps the SIGNED `orient_q`
    difference back into its own bin range (`_wrap_signed_bin`) so two nearly-identical
    headings straddling the +180/-180 seam read as nearly-zero, not maximally far apart.
    Pairs are emitted in ascending `(i, j)` order -- deterministic, not a ranking."""
    ks = sorted(pose_by_k)
    out = []
    for a, i in enumerate(ks):
        for j in ks[a + 1:]:
            if j <= i + 1:
                continue
            pi, pj = pose_by_k[i], pose_by_k[j]
            dx_q = int(pj["x_q"]) - int(pi["x_q"])
            dy_q = int(pj["y_q"]) - int(pi["y_q"])
            do_q = _wrap_signed_bin(int(pj["orient_q"]) - int(pi["orient_q"]), turn_bins)
            ds_q = int(pj["scale_q"]) - int(pi["scale_q"])
            out.append(["rel2", i, j, dx_q, dy_q, do_q, ds_q])
    return out


def decode_result_to_stroke_points(knots, res: dict) -> list[tuple[list, str, Optional[str], Optional[list]]]:
    """Mechanical merge of ONE `ink_decode.decode_ink` call's own `{recognized, minted}`
    lists into a single draw-order `(points, identity_name, fine_child_name_or_None,
    substroke_points_or_None)` sequence for `compose_character_signature` — a freshly MINTED
    span is a real, named stroke identity the instant `decode_ink` installs it, so it
    contributes exactly like a `recognized` span (with no `fine_child`/`substroke_points`,
    EAGER CHILD MINTING and BRANCH A EXECUTION's sub-stroke composition only ever fire on
    RECOGNIZED spans, never the OOV/mint branch); a never-recognized-or-minted OOV span (should
    not happen — every on-path OOV span either recognizes near-miss or mints, see
    `ink_decode.decode_ink`'s own post-lattice loop) contributes nothing (no identity to compose
    a `strokeq` relation from). Ordered by START POSITION (`x[0]`) — the spans' own on-path
    ORDER, already decided by the lattice, not a ranking of this function's own.

    BRANCH A EXECUTION (2026-07-03): `r.get("substroke_points")` (present on every recognized
    span when `ink_decode.decode_ink`'s `enable_substroke` is on, `None` otherwise/on a minted
    span) is threaded through as the 4th tuple element unchanged — `compose_character_signature`
    only reads it when its own `include_substroke=True` is passed."""
    knots = np.asarray(knots, dtype=float)
    items = [(r["start"], r["end"], r["name"], r.get("fine_child"), r.get("substroke_points"))
             for r in res.get("recognized", [])]
    items += [(m["start"], m["end"], m["name"], None, None) for m in res.get("minted", [])]
    items.sort(key=lambda x: x[0])
    return [(knots[st:e].tolist(), name, fine_child, substroke_points)
            for (st, e, name, fine_child, substroke_points) in items]


# --------------------------------------------------------------------------- #
#  RECOGNIZE — RUN-4 LEVERS "LEVER 1": a DIRECT TransformDecode read-off at CHARACTER grain,
#  mirroring `ink_decode._read_pose_transform`/`_install_pose_transform` exactly (own
#  `max_dims`, bypassing the generic seeded `sd_transform_decode` rule's `max_dims=2`) — see
#  `compose_character_signature`'s docstring for why this is the fix, not a workaround.
# --------------------------------------------------------------------------- #
DEFAULT_CHARACTER_MAX_DIMS = 4


def read_character_transform(native, query_sig: list, *,
                              max_dims: int = DEFAULT_CHARACTER_MAX_DIMS) -> dict:
    """ONE direct `TransformDecode` evaluate against the held character codebook (default
    `codebook_type="ShapeSignature"` — the SAME node type stroke quanta use; a structural
    relation-COUNT mismatch already excludes every stroke entry as a candidate for a
    character-shaped goal, see `runners/dsl/src/shape_decode.rs::build_candidate`'s own
    exact-count prefilter — no `codebook_type`/`kind` filter needed, "NO NEW MACHINERY").
    `max_dims=4` (the four `cpose_*` predicates) by default — the mirror of `ink_decode.
    _read_pose_transform`'s own `max_dims=4` for the four `pose_*` predicates, at one level
    up. Pure mechanical read, never a decision: the RESULT's `explained`/`identity` booleans
    are what a caller branches on (`recognize_or_mint_character`), not this function."""
    return native.evaluate({
        "type": "TransformDecode",
        "goal": {"type": "Lit", "value": query_sig},
        "max_dims": max_dims,
    }, {})


def recognize_or_mint_character(agent, query_sig: list, *, name_hint: Optional[str] = None,
                                 max_dims: int = DEFAULT_CHARACTER_MAX_DIMS) -> dict[str, Any]:
    """The character-grain twin of `ink_decode.decode_ink`'s own per-span dispatch idiom (a
    presence/boolean check on a value a HELD Term already computed, never a Python ranking —
    CLAUDE.md's own sanctioned "thin I/O-boundary" pattern, already used throughout this
    codebase): try the DIRECT `read_character_transform` first (own `max_dims`, closes the
    RUN-4 LEVERS "LEVER 1" residual — a whole-character rotate+scale+translate can move all
    four `cpose_*` predicates at once, which the GENERIC seeded `sd_transform_decode` rule's
    `max_dims=2` cannot absorb); only when NEITHER identity NOR an explained transform is
    found does this fall through to `domains.reflective_faculty.induce_concern` — the SAME
    `sd_*` mint/recognize ladder `grow_character_quantum`'s callers already used, UNCHANGED,
    for genuinely novel arrangements. Returns a dict shaped like `induce_concern`'s own
    (`minted`, plus `covered_by`/`transform` on the direct-recognized path) so existing
    callers checking `res["minted"]` keep working regardless of which path resolved it."""
    direct = read_character_transform(native=_native(agent), query_sig=query_sig,
                                       max_dims=max_dims)
    if direct.get("identity") or direct.get("explained"):
        return {"minted": False, "covered_by": direct.get("base"),
                "transform": {"dims": list(direct.get("dims") or []),
                              "deltas": list(direct.get("deltas") or []),
                              "transforms": list(direct.get("transforms") or []),
                              "base": direct.get("base"),
                              "identity": bool(direct.get("identity")),
                              "explained": bool(direct.get("explained"))},
                "observation": query_sig, "path": "direct_character_transform",
                "note": (f"held character {direct.get('base')!r} covers the observation "
                         "directly (identity or a rung-1 cpose-dimension transform) — no new "
                         "concern, resolved WITHOUT the generic sd_transform_decode ladder")}
    res = induce_concern(agent, query_sig, name_hint=name_hint)
    res["path"] = "induce_concern"
    return res


# --------------------------------------------------------------------------- #
#  INSTALL — mirrors stroke_codebook.grow_stroke_quantum exactly, one level up.
# --------------------------------------------------------------------------- #
def _bump_codebook_epoch(sub, ag_node) -> None:
    if ag_node is None:
        return
    cur = sub.node(ag_node)["attrs"].get("codebook_epoch") or 0.0
    sub.set_attr(ag_node, "codebook_epoch", float(cur) + 1.0)


def grow_character_quantum(agent, name: str, signature: list, *,
                           category: str = DEFAULT_CATEGORY, **meta) -> dict[str, Any]:
    """Install a composed CHARACTER signature as a new `ShapeSignature{kind:"character"}`
    node, `teach()`-persisted, codebook epoch bumped exactly once — the mint path's own
    quantum-install primitive (a caller reads `induce_concern`'s `minted` verdict, exactly
    like `ink_decode.py`'s stroke OOV path calls `stroke_codebook.grow_stroke_quantum`; the
    DECISION is the seeded `sd_*` rules', this only installs it). Idempotent by name.

    RUN 30 (creator directive: "a frame is N dimensions/axes with relative weighting") — a
    freshly-installed quantum ALSO gets its own Frame (`domains.frame_weights.
    ensure_quantum_frame`): one FrameAxis node per relation key its OWN composed `signature`
    already carries (`_relation_map`'s own key set, duplicated locally here as `_frame_axis_
    keys` — a ~10-line mechanical extraction, per this codebase's own "small local
    duplication beats an import cycle" convention: `arrangement_codebook` already imports
    THIS module, so this module importing `arrangement_codebook` back would close a loop).
    Graph DATA EMISSION from an already-composed signature's own already-known structure —
    legal seed-builder work (CLAUDE.md), never a re-decision; weight VALUES start at
    `DEFAULT_WEIGHT` and change ONLY via the `fw_update` graph rule reading evidence data
    (`domains.arrangement_codebook.update_relation_stability`), never here."""
    sub = _sub(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    tagent = _teach_agent(agent)

    if name in _existing_names(sub, "character"):
        return {"grown": False, "name": name, "reason": "already a held character quantum"}

    attrs = {"name": name, "kind": "character",
             "signature": json.dumps([list(rel) for rel in signature]), **meta}
    res = teach(tagent, "ShapeSignature", attrs, category=category)
    _bump_codebook_epoch(sub, ag_node)
    node = res.get("node")
    if node is not None:
        from domains import frame_weights as fw
        fw.ensure_quantum_frame(agent, node, name, _frame_axis_keys(signature))
    return {"grown": True, "name": name, "node": node, "seed": res.get("seed")}


def _frame_axis_keys(signature: list) -> list:
    """Mechanical (no decision): every `rel:<k>:<x|y|o|s>` / `cpose_*` weight-key a composed
    CHARACTER signature carries — duplicated from `arrangement_codebook._relation_map`'s own
    key extraction (see `grow_character_quantum`'s own docstring for why: avoiding an
    `arrangement_codebook` <-> `character_compose` import cycle). Accepts both `list` and
    `tuple` relation entries (a LIVE `native.evaluate(...)` result surfaces Rust sequences as
    Python `tuple`s — the same documented gotcha `ink_decode._fine_seg_relations`/
    `arrangement_codebook._relation_map` already guard against)."""
    out: list = []
    for r in signature:
        if not (isinstance(r, (list, tuple)) and r):
            continue
        pred = r[0]
        if pred == "rel" and len(r) >= 6:
            k = r[1]
            out.extend(f"rel:{k}:{label}" for label in ("x", "y", "o", "s"))
        elif pred in _CPOSE_PREDS and len(r) >= 2:
            out.append(pred)
    return out


# --------------------------------------------------------------------------- #
#  ARRANGEMENT FIDELITY (2026-07-03, scratchpad/HANDWRITING_DESIGN.md's "ARRANGEMENT
#  FIDELITY" section, the accb0d47 residual): PHASE A (scripts/jabberwock_omniglot_
#  arrangement_diag.py, run against the COMMITTED seeds/stroke_shapes.json codebook,
#  reproducing the real gate's own 33.8%/66.2% miss rate) ranked THREE candidate levers by
#  fraction of the 53 real misses explained: coverage-metric TIES 52.8%, coverage-metric
#  SMALL-GAP 32.1%, frame-anchor instability 18.9% (also structural stroke-COUNT mismatches
#  47.2% of misses, which a metric fix subsumes -- see below). LEVER 2 (coverage metric) wins:
#  `scripts/jabberwock_omniglot_dynamic_quantization.py`'s own `_coverage_term` is "Sum + In"
#  over the FLAT relation list -- a query relation counts ONLY if it appears as an EXACT,
#  WHOLE-TUPLE match anywhere in the candidate's own relation list. Two consequences the
#  diagnosis measured directly: (1) a single mismatched SLOT (e.g. one `rel` tuple's `do_q`
#  off by one bin) zeroes out the ENTIRE relation's contribution (no partial credit) --
#  exactly the "small gap" / "tie" signature the diagnosis found in >50% of misses; (2) a
#  query/exemplar pair that decoded to a DIFFERENT STROKE COUNT (segmentation/pen-lift
#  variance across real drawers, 47.2% of misses) can never align most of its `strokeq`/`rel`
#  relations at all, since they are keyed by DRAW-ORDER ORDINAL `k` and the whole-tuple
#  membership test has no notion of "close enough" or "matches a DIFFERENT k".
#
#  `assignment_coverage_term` fixes BOTH by scoring per-STROKE best-match (assignment) instead
#  of per-RELATION exact membership: each query stroke's record -- `(identity, dx_q, dy_q,
#  do_q, ds_q, fine_child_or_empty)` -- is scored against EVERY exemplar stroke record
#  (identity match worth 2, each of the four `rel` slots worth 1, a genuine `strokeq_fine`
#  match worth 1 more), and the query keeps its BEST-matching exemplar stroke (`MaxOver`) --
#  a per-slot near-miss now loses only that slot's own point, not the whole relation, and a
#  stroke-count mismatch just means some query/exemplar strokes go unmatched or share a
#  best-match, never a hard structural failure. Matching is by CONTENT, not by shared `k` --
#  order/count-robust by construction (still additive: `strokeq`/`rel`/`cpose_*`/
#  `strokeq_fine` themselves are UNCHANGED, `_stroke_records` only reads them). The whole-
#  character `cpose_*` predicates (a single record, not per-stroke) are scored the same
#  per-slot-match way and added on top -- `Plus` of two held Sum-type subterms, ONE Term
#  evaluate per (query, exemplar) pair. NO NEW RUST: `Sum`/`MaxOver`/`Plus`/`IfThenElse`/`Eq`/
#  `And`/`Not`/`IndexAt` are all pre-existing DSL Terms (verified directly against the live
#  wheel before writing this, per CLAUDE.md's "report a genuine wall first" -- there was none).
#  ADDITIVITY: the pre-existing `_coverage_term` (naive Sum+In) is UNCHANGED and stays the
#  LOGGED CONTROL every episode (scripts/jabberwock_omniglot_dynamic_quantization.py's `_ms`/
#  `_comp`/`_comp_nc`/`_sorted` arms keep their exact pre-existing meaning; `_comp_assign` is
#  purely additive, RUN 7 only).
# --------------------------------------------------------------------------- #
_MISSING_REL = -999
_CPOSE_PREDS = ("cpose_x", "cpose_y", "cpose_o", "cpose_s")


def _stroke_records(sig: list) -> list[tuple]:
    """Mechanical extraction (no decision -- a fixed structural re-packaging of relations a
    held Term already produced, the same kind of translation `ink_decode._extract_dim_delta`
    already does) of one composed CHARACTER signature's PER-STROKE records: `(identity, dx_q,
    dy_q, do_q, ds_q, fine_child_or_"")` per stroke `k`, returned in NO PARTICULAR ORDER (see
    `assignment_coverage_term`'s own docstring for why order/count independence is exactly the
    point). A stroke with no `rel` entry (a degenerate <2-point span, `compose_character_
    signature`'s own documented gate) gets the fixed sentinel `_MISSING_REL` on all four slots
    -- a value quantized bins never legitimately take, so it can never accidentally MATCH a
    real bin value on either side."""
    strokeq, rel, fine = {}, {}, {}
    for r in sig:
        pred = r[0]
        if pred == "strokeq":
            strokeq[r[1]] = r[2]
        elif pred == "rel":
            rel[r[1]] = tuple(r[2:6])
        elif pred == "strokeq_fine":
            fine[r[1]] = r[2]
    return [(strokeq[k], *rel.get(k, (_MISSING_REL,) * 4), fine.get(k, "")) for k in strokeq]


def _cpose_pairs(query_sig: list, exemplar_sig: list) -> list[tuple]:
    """Mechanical extraction of the WHOLE-CHARACTER `cpose_*` value pairs present on BOTH
    sides (a predicate only one side carries contributes nothing either way -- there is
    nothing to compare it against)."""
    q = {r[0]: r[1] for r in query_sig if r[0] in _CPOSE_PREDS}
    e = {r[0]: r[1] for r in exemplar_sig if r[0] in _CPOSE_PREDS}
    return [(q[p], e[p]) for p in _CPOSE_PREDS if p in q and p in e]


# RUN 52 -- THE MINIMAL LOOP-FLIP: `["rel_x", "rel_y", "rel_o", "rel_s"]`, the SAME slot names
# `domains/relational_variation.py`'s `REL_SLOTS`/`CPOSE_SLOTS`/`ALL_SLOTS` already use for its
# background-learned per-slot tightness weights (not imported here -- `relational_variation`
# imports THIS module for `_wrap_signed_bin`, so importing back would close a cycle; the slot
# NAMES are duplicated as a plain string tuple, the same "small local duplication beats an
# import cycle" convention `grow_character_quantum`'s own `_frame_axis_keys` already documents).
_ASSIGNMENT_REL_SLOTS = ("rel_x", "rel_y", "rel_o", "rel_s")   # index 1..4 of a `_stroke_records`
                                                                # tuple, in that exact order.


def assignment_coverage_term(query_sig: list, exemplar_sig: list, *,
                             identity_weight: float = 2.0,
                             weights: Optional[dict] = None) -> dict:
    """ARRANGEMENT FIDELITY's Phase-B Term (see this module's own section docstring above for
    the full diagnosis/rationale): ONE held Term evaluate scoring `query_sig` against
    `exemplar_sig` by PER-STROKE ASSIGNMENT (best-match) instead of the pre-existing per-
    RELATION exact-membership `_coverage_term` (scripts/jabberwock_omniglot_dynamic_
    quantization.py, UNCHANGED, kept as the logged control). For every query stroke record,
    `MaxOver` the per-slot match score against every exemplar stroke record (identity match
    worth `identity_weight` points, each of `dx_q`/`dy_q`/`do_q`/`ds_q` worth its OWN `weights`
    entry [default `1.0`, EQUAL for all four -- see RUN 52 below], a genuine non-empty
    `strokeq_fine` match worth 1 more -- Occam weights, not a fitted hyperparameter: identity
    is the strongest single signal of correspondence, the four pose slots are the arrangement
    detail this section is named for), `Sum` over query strokes, plus the same per-slot match
    score over the whole-character `cpose_*` pair. A near-miss on ONE slot now loses only that
    slot's point (not the whole stroke's contribution, unlike `_coverage_term`'s all-or-
    nothing whole-tuple membership); matching by CONTENT rather than shared draw-order ordinal
    `k` means a query/exemplar pair that decoded to a DIFFERENT STROKE COUNT can still align
    whatever strokes genuinely correspond, rather than failing structurally. Never a Python
    ranking -- the whole score is one native `evaluate()` call away from being fed straight
    into the SAME held `Argmax` idiom (`_argmax_pairs_term`) every classification loop in this
    codebase already uses.

    RUN 52 -- THE MINIMAL LOOP-FLIP (`weights`, default `None` -- every pre-existing call site
    reproduces the BYTE-IDENTICAL equal-weight score): a `{slot: float}` mapping over
    `domains.relational_variation.ALL_SLOTS` (`"rel_x"/"rel_y"/"rel_o"/"rel_s"/"cpose_x"/
    "cpose_y"/"cpose_o"/"cpose_s"`), meant to be `relational_variation.slot_weights(...)`'s own
    frozen, BACKGROUND-learned per-slot TIGHTNESS output (a tight/identity-bearing slot's weight
    sits above `1.0`, a loose/free-to-vary slot's below) -- read-only DATA, never recomputed
    here. This REPLACES the four hardcoded `1.0` rel-field weights and the four hardcoded `1.0`
    cpose weights with `weights.get(slot, 1.0)`; an absent slot (or `weights=None` entirely)
    falls back to `1.0`, the ORIGINAL constant -- so `weights=None` and
    `weights={s: 1.0 for s in ALL_SLOTS}` both reproduce the PRE-RUN-52 score EXACTLY (the
    critical invariant `tests/test_varcomp_migrated.py` gates on). This is the SAME verdict
    structure (`MaxOver`/`Sum`/`Plus`/`IfThenElse`, unchanged) with LEARNED per-relation
    weights substituted for a constant -- not a new stage, not a term added after the fact
    (CLAUDE.md's own "primitive in Rust, composition in graph" discipline: no new machinery,
    only a data substitution inside the existing composition Term)."""
    w = weights or {}

    def _gw(slot: str) -> float:
        return float(w.get(slot, 1.0))

    def _idx(v: str, i: int) -> dict:
        return {"type": "IndexAt", "seq": {"type": "Var", "name": v},
                "index": {"type": "Lit", "value": i}}

    def _field_score(i: int, weight: float) -> dict:
        return {"type": "IfThenElse",
                "cond": {"type": "Eq", "a": _idx("q", i), "b": _idx("e", i)},
                "then": {"type": "Lit", "value": weight}, "other": {"type": "Lit", "value": 0.0}}

    fine_score = {"type": "IfThenElse",
                  "cond": {"type": "And", "items": [
                      {"type": "Not", "arg": {"type": "Eq", "a": _idx("q", 5),
                                              "b": {"type": "Lit", "value": ""}}},
                      {"type": "Eq", "a": _idx("q", 5), "b": _idx("e", 5)}]},
                  "then": {"type": "Lit", "value": 1.0}, "other": {"type": "Lit", "value": 0.0}}
    # identity_weight parameterized (RUN-8 adjustment, diagnostics-driven: at the gate's own
    # 7-quantum LEARN codebook the multiset ablation proves stroke identity is at-chance, so
    # weighting it dilutes the arrangement signal — identity_weight=0.0 scores ARRANGEMENT ONLY).
    # RUN 52: the four pose-slot weights are now `_gw(slot)` (default 1.0, EQUAL -- byte-
    # identical to the pre-existing hardcoded 1.0s) instead of a bare literal.
    pair_score = {"type": "Plus", "items": [
        _field_score(0, identity_weight),
        _field_score(1, _gw(_ASSIGNMENT_REL_SLOTS[0])), _field_score(2, _gw(_ASSIGNMENT_REL_SLOTS[1])),
        _field_score(3, _gw(_ASSIGNMENT_REL_SLOTS[2])), _field_score(4, _gw(_ASSIGNMENT_REL_SLOTS[3])),
        fine_score]}

    q_records = _stroke_records(query_sig)
    e_records = _stroke_records(exemplar_sig)
    assignment_term = {
        "type": "Sum", "source": {"type": "Lit", "value": q_records}, "var_name": "q",
        "value": {"type": "MaxOver", "source": {"type": "Lit", "value": e_records},
                  "var_name": "e", "value": pair_score, "default": {"type": "Lit", "value": 0.0}},
    }

    # RUN 52: per-`cpose_*`-PREDICATE weighted terms (`_gw(pred)`, default 1.0) replace the
    # prior single `Sum` over `_cpose_pairs`' UNLABELLED (value, value) tuples -- `_cpose_pairs`
    # itself is UNCHANGED (kept for its own existing callers/tests), simply not used by this
    # function any more since scoring per-PREDICATE weight requires the predicate NAME, which
    # `_cpose_pairs`' own tuple shape discards. Same value set, same "present on both sides"
    # filter, so `weights=None`/all-1.0 sums to the IDENTICAL scalar as the prior `Sum`-based
    # Term (a `Plus` of the same terms in a different but value-equivalent shape).
    q_cpose_w = {r[0]: r[1] for r in query_sig if r[0] in _CPOSE_PREDS}
    e_cpose_w = {r[0]: r[1] for r in exemplar_sig if r[0] in _CPOSE_PREDS}
    cpose_scores = []
    for pred in _CPOSE_PREDS:
        if pred not in q_cpose_w or pred not in e_cpose_w:
            continue
        cpose_scores.append({
            "type": "IfThenElse",
            "cond": {"type": "Eq", "a": {"type": "Lit", "value": q_cpose_w[pred]},
                     "b": {"type": "Lit", "value": e_cpose_w[pred]}},
            "then": {"type": "Lit", "value": _gw(pred)}, "other": {"type": "Lit", "value": 0.0}})
    cpose_term = {"type": "Plus", "items": cpose_scores} if cpose_scores else {"type": "Lit",
                                                                                "value": 0.0}

    return {"type": "Plus", "items": [assignment_term, cpose_term]}


__all__ = ["compose_character_signature", "decode_result_to_stroke_points",
           "grow_character_quantum", "read_character_transform",
           "recognize_or_mint_character", "DEFAULT_CATEGORY", "DEFAULT_CHARACTER_MAX_DIMS",
           "_character_frame", "_frame_bbox", "assignment_coverage_term", "_stroke_records",
           "_cpose_pairs", "_rel2_relations", "_wrap_signed_bin",
           "compose_stroke_signature", "substroke_arrangement_key"]
