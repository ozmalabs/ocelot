"""stroke_codebook — S1 of scratchpad/HANDWRITING_DESIGN.md: quantize GLYPHS-derived pen
strokes into the SAME held ShapeSignature codebook seeds/shape_decode_loop.json's ladder
already reads (dynamic quantization: "shape matching is DEQUANTIZATION; order-N growth is
DYNAMIC QUANTIZATION" — the handwriting instance of the SAME loop the math/faculty capability
shapes already use, domains/reflective_faculty.py:grow_part_library).

Reuses the Rust `StrokeQuantize` Term (`shape_decode.rs` family, built in PARALLEL against
this design — not yet landed as of this writing; see `_stroke_quantize_live()` below, the
same "authored, not yet operative" pattern `seeds/shape_decode_loop.json`'s
`sd_transform_decode`/`sd_infer_dimension` used before `TransformDecode`/`DimInfer` landed).
`StrokeQuantize` does ALL the geometry (arc-length resample, relative-turn quantization,
pose quantization) — this module only calls it and writes the result into the graph.

Per CLAUDE.md this is a SEED BUILDER: a Python builder that emits graph data from a FIXED
source (the GLYPHS motor programs; optionally the legacy `.bigtmp/gemma_stroke_inventory.pkl`
medoid pickle, migrated in). No conditional here reads graph STATE and decides what the agent
should do next — every stroke source is quantized and installed the same way, unconditionally.
The RECOGNITION-TIME decision (mint vs recognize a stroke) lives in the seeded `sd_*` rules
(`seeds/shape_decode_loop.json`), not here.

CODEBOOK CONVENTION (reconciled with the parallel Rust work, 2026-07-02 — supersedes an
earlier `StrokePoseRef`-auxiliary-node draft of this module): a `ShapeSignature{kind:"stroke"}`
codebook entry stores the FULL signature (`seg` + `pose_x`/`pose_y`/`pose_o`/`pose_s`
relations, the design's literal 4-relation pose schema — see `domains/ink_decode.py`'s module
docstring for why that schema needed a Rust-side fix to compose correctly under
`TransformDecode`, now in flight) at the stroke's CANONICAL/REFERENCE POSE — via
`StrokeQuantize`'s new `canonical_pose: true` option, NOT `invariant_only`. Rationale (the
Rust team's, adopted here): relation COUNTS then match an OBSERVED span's own full signature
one-for-one, so a single `TransformDecode(goal=observed_full_signature)` against this SAME
codebook directly reads the observed pose as a delta from the canonical reference — no second
auxiliary node/type needed at all. `invariant_only` remains useful ONLY for `ink_decode.py`'s
per-span LATTICE EMISSION scoring (`ShapeDecode`, a coverage/composition scorer, not an
equal-count matcher): an invariant-only (seg-only) SPAN goal against this FULL codebook entry
still scores `covered_count == segments` on an exact seg match (empirically verified directly
against the ALREADY-LANDED `ShapeDecode` Term, no `StrokeQuantize` needed — see
`tests/test_ink_decode_migrated.py::test_shapedecode_scores_invariant_goal_against_full_codebook_entry`)
— the codebook entry's own pose relations simply go uncovered (a constant per-candidate
overhead that never contributes to `covered_count` and so never skews the Argmax-style
ranking `beam=1/max_steps=1/cand_k=1` performs)."""
from __future__ import annotations

import json
import math
import os
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np

from domains.reflective_faculty import _agent_root_node
from domains.teach import teach

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PICKLE = ROOT / ".bigtmp" / "gemma_stroke_inventory.pkl"
SEEDS_DIR_DEFAULT = ROOT / "seeds"

DEFAULT_SEGMENTS = 12
DEFAULT_TURN_BINS = 16
DEFAULT_LEN_BINS = 8
DEFAULT_GRID = 8
DEFAULT_SCALE_BINS = 8
DEFAULT_CATEGORY = "stroke_shapes"

# REFINEMENT RUNG (scratchpad/HANDWRITING_DESIGN.md, 2026-07-02 -- the Omniglot residual,
# commit 26f74039): every stroke quantum now carries its signature at a COARSE grain (jitter
# vanishes by construction -- "tolerance = COARSENESS, not fuzzy matching: coarse-grain EXACT
# match IS the principled near-miss band") IN ADDITION TO the existing fine grain, plus a
# PROTOTYPE polyline for the DtwTo near-miss fallback. Grain settings are DATA (attrs on each
# entry), these are just the DEFAULTS a builder call uses when the caller doesn't override them.
COARSE_TURN_BINS = 6
COARSE_LEN_BINS = 4
PROTOTYPE_LEN = 16
# Diagnostics-driven (empirical, not blind): banded-DTW distance between two
# `_invariant_points` prototypes (arc-length-normalized to length 1, PROTOTYPE_LEN=16
# frames) measured directly against a real StrokeQuantize'd line -- a REALISTIC small pen
# jitter (numpy normal(0, 0.01) per point) scores ~0.108; a genuinely DIFFERENT shape class
# (a line vs. a 270-degree arc) scores ~0.50; unrelated random-walk noise slices scored
# 0.21-0.39. 0.15 sits just above the realistic-jitter band and comfortably below every
# observed false-positive case (verified against tests/test_ink_decode_migrated.py's own
# gate 5 / gate (c) / oov-mint gates, which regressed at the initial 0.35 default).
DEFAULT_DTW_THRESHOLD = 0.15

# GRAIN LADDER (RUN-4 LEVERS, scratchpad/HANDWRITING_DESIGN.md's "LEVER 2 — GRAIN LADDER"
# section, 2026-07-02): "replace the two-level coarse/fine with a data-driven ladder attr on
# the codebook/game (default [(6,4),(10,6),(16,8)])" — a MID grain, strictly between COARSE
# and FINE, inserted so a coarse-level TIE between two genuinely different quanta (their
# coarse buckets collide, "distinct-at-mid identities") still resolves correctly one net
# finer, without paying FINE's exact-match brittleness to jitter. `MID_TURN_BINS`/
# `MID_LEN_BINS` are the DEFAULT bin counts a builder call uses when a caller doesn't
# override them (mirrors `COARSE_TURN_BINS`/`COARSE_LEN_BINS`'s own doc); `DEFAULT_GRAIN_LADDER`
# names the full ladder as DATA (coarsest-first tuples of `(turn_bins, len_bins, level_name)`)
# for callers/reports that want to walk it generically rather than hard-code three separate
# grains — `grow_stroke_quantum`/`ink_decode.py` still address COARSE/MID/FINE by their own
# explicit params+companion node types below (a fixed 3-level ladder, not yet a truly
# open-ended N-level walk — see those functions' docstrings for the honest scope).
MID_TURN_BINS = 10
MID_LEN_BINS = 6
DEFAULT_GRAIN_LADDER = ((COARSE_TURN_BINS, COARSE_LEN_BINS, "coarse"),
                        (MID_TURN_BINS, MID_LEN_BINS, "mid"),
                        (DEFAULT_TURN_BINS, DEFAULT_LEN_BINS, "fine"))

# EAGER CHILD MINTING (scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING" section,
# 2026-07-02 — the a6fe069b residual: vocabulary capped at 5 top-level quanta because
# recognition-before-mint stops misses at the FINE grain; run 5 proved a finer BASE grain
# hurts matching, so detail must enter as CHILDREN, never a base-grain change). STEP 0
# (instrumented empirically against real Omniglot ink, `/tmp/step0_instrument.py`, 400 real
# strokes, 2595 fine-tier recognitions): a FINE-tier recognition is ALWAYS exact-signature
# equality (`runners/dsl/src/shape_decode.rs`'s own `covered_by = residual.is_empty() &&
# plan.len()==1` — `ShapeDecode`'s `covered_by` NEVER returns a name on a partial/coverage-
# Argmax match, only on full coverage) — ZERO fine-tier recognitions carried ANY residual
# against their parent's stored fine `seg` relations (0/2595 violations observed). So there is
# NO already-carried quantized variation to key a child on at the FINE grain itself — a
# genuinely FINER grain (SUB-FINE, below fine on the ladder, "an entry NOT a base-grain
# change") is required to expose it, exactly as the design's own fallback branch anticipated.
# The SAME instrumentation found REAL variation there: the dominant real stroke family (2592
# fine recognitions) resolved to only 6 DISTINCT sub-fine signatures — genuine detail exists,
# and quantization (not raw jitter) naturally BOUNDS how many distinct children a real
# population produces (2592 occurrences -> 6 buckets, not 2592) — the dedup-by-signature
# mechanism below inherits that natural bound for free, no separate cap needed.
SUBFINE_TURN_BINS = 20
SUBFINE_LEN_BINS = 10

# Per-slot typing (design's `["pred","idx","val","val"]`, one entry per slot of a `["seg", i,
# turn_q, len_q, 0]` relation — a stroke's `seg` relations carry no `coord:*`-typed slot, they
# are rotation/scale/translation INVARIANT by construction, so `DimInfer`'s coordinate
# generators never have anything to act on here; set for schema-completeness/documentation,
# not because rung-2 dimension-inference is expected to fire on a stroke's `seg` relations).
INVARIANT_DIM_TYPES = ["pred", "idx", "val", "val", "val"]

# BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (scratchpad/HANDWRITING_DESIGN.md's section of
# the same name, the jabberwock's verdict d2cd7bed, 2026-07-03): "the sd loop one level DOWN --
# a stroke is itself an arrangement of sub-stroke quanta." A sub-stroke quantum is the SAME
# `ShapeSignature` machinery one grain finer, `kind="substroke"` -- deliberately the SIMPLEST
# possible grow (ONE grain, no coarse/mid/subfine companions, no refinement ladder): "coarse
# bins per run-5's law" -- detail belongs in the ARRANGEMENT (character_compose.py's "subq"/
# "srel" relations, the composition itself), never in a finer sub-stroke BASE grain (run 5
# already proved a finer base grain hurts MATCHING at the stroke level; the same law applies
# one level down). `SUBSTROKE_SEGMENTS` is deliberately far from every stroke-grain `segments`
# setting used anywhere in this codebase (8 in the Omniglot gate's reduced-bin DK, 12 default)
# so a substroke's own relation-count (arity) can never coincide with a real stroke's --
# `ShapeDecode`'s exact-relation-count structural prefilter (`runners/dsl/src/shape_decode.rs
# ::build_candidate`) then EXCLUDES cross-grain matches automatically, the SAME reasoning
# `character_compose.py`'s own module docstring already establishes for `kind="character"`
# entries safely sharing the SAME `ShapeSignature` node type as stroke quanta ("NO NEW
# MACHINERY" -- no companion node type needed here either, by the identical argument).
SUBSTROKE_SEGMENTS = 4
SUBSTROKE_TURN_BINS = COARSE_TURN_BINS
SUBSTROKE_LEN_BINS = COARSE_LEN_BINS

# CONTINUOUS-NOVELTY MINTING (RUN 23, the LEARN-side attack on the runs-19-22 identity-grain
# wall, commit 9762130f's own closing clause): "run 16 proved continuous beats quantized for
# VERDICTS -- apply it to GROWTH." A decoded stroke that RECOGNIZES at some tier (its quantized
# signature matches an existing quantum) but whose held `DtwTo` distance to that quantum's own
# continuous PROTOTYPE exceeds a threshold now MINTS a new quantum ANYWAY -- a peer, TOP-LEVEL
# `ShapeSignature{kind:"stroke"}` entry (via the SAME `grow_stroke_quantum` install path every
# other mint uses), tagged `continuous_parent` so it can be found again as part of its own
# quantum's growing "continuous family" (see `continuous_mint_or_note` below). Recognition/
# matching tiers (`ink_decode._score_span`/`_score_span_mid`/`_score_span_coarse`) are NOT
# touched by this at all -- a discrete bucket that used to collapse many genuinely-different
# continuous shapes into ONE quantum (the runs-19-22 wall: "14,675/14,676 observations share a
# single identity") now has SEVERAL top-level peers sharing that bucket, one per continuous
# "cluster" the DtwTo threshold discovers, and `ShapeDecode`'s own tie-break among exact-
# signature-matching candidates still resolves matching deterministically ("no bin change
# anywhere" — the design's own words). DEFAULT OFF everywhere (`enable_continuous_mint=False`
# at every `decode_ink` call site) -- every existing caller/test behaves byte-identically with
# the flag untouched; `DEFAULT_CONTINUOUS_MINT_THRESHOLD` is a STARTING value only, run 23's own
# launch instructions require sweeping it honestly on BACKGROUND-ONLY LEARN data and picking by
# diagnostics (vocabulary size, observation histogram, growth-curve saturation, identity
# diversity), never by test accuracy.
DEFAULT_CONTINUOUS_MINT_THRESHOLD = 0.30
# A mechanical COST BOUND on how many family members' prototypes a single decision scans (DtwTo
# calls), not a decision -- mirrors `DEFAULT_MAX_SPAN`'s own "bounded, not a choice" role
# elsewhere in this module. Large enough to be inert at every vocabulary size this arc has ever
# produced (single digits to low tens); exists only so a pathological runaway mint sequence
# cannot make ONE decision's own cost unbounded.
MAX_CONTINUOUS_FAMILY_SCAN = 200


def _teach_agent(agent):
    """`teach()` (domains/teach.py) requires `agent.s` — the established idiom for calling
    it from a bare Substrate (no WorldAdapter wrapper) is a throwaway shim object carrying
    just that attribute (see domains/construction_grammar.py:3539's identical idiom)."""
    if hasattr(agent, "s"):
        return agent
    return type("_TeachAgent", (), {"s": agent})()


def _sub(agent):
    return getattr(agent, "s", agent)


def _native(agent):
    s = _sub(agent)
    return getattr(s, "_inner", s)


def _stroke_quantize_live(native) -> bool:
    """Cheap probe: is the Rust `StrokeQuantize` Term (WITH the `canonical_pose` option the
    codebook convention above depends on) callable yet? Mirrors
    `tests/test_dimension_inference_migrated.py::_dim_infer_live`'s pattern: a plain
    `StrokeQuantize` call could in principle land before `canonical_pose` does, so this probes
    the SPECIFIC option this module needs, not just the Term's bare existence."""
    try:
        native.evaluate(
            {"type": "StrokeQuantize",
             "points": {"type": "Lit", "value": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]},
             "canonical_pose": True},
            {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e) or "unknown field" in str(e).lower() or "canonical_pose" in str(e):
            return False
        raise


def _quantize(native, points, *, segments, turn_bins, len_bins, grid, scale_bins,
              invariant_only: bool = False, canonical_pose: bool = False,
              bounds: Optional[tuple] = None,
              turn_edges: Optional[list] = None, len_edges: Optional[list] = None,
              emit_residual: bool = False) -> dict:
    """One call to the held `StrokeQuantize` Term — pure geometry (arc-length resample,
    relative-turn quantization, pose quantization), no decision. `points` is a plain list of
    `[x, y]` pairs (one stroke's sampled pen path). `invariant_only` and `canonical_pose` are
    mutually-informative but distinct: `invariant_only` DROPS the pose relations entirely
    (emission scoring); `canonical_pose` KEEPS them but pins them to the stroke's fixed
    reference pose regardless of the input points' actual position/orientation/scale (codebook
    authoring — an observed instance's ACTUAL pose then reads as a pure delta from this).
    `bounds` (DISCRIMINATION lever (c), `domains/character_compose.py`): an optional external
    `(x0, y0, x1, y1)` — when given, `pose_x`/`pose_y` (and the informational `pose.x_q`/
    `pose.y_q`) quantize the points' position against THIS bbox instead of the point-set's own
    (the Rust `StrokeQuantize` Term's pre-existing `bounds` field, unused until now) — the
    mechanism `character_compose.py` uses to read a stroke's position on the CHARACTER's own
    grid rather than that one stroke's own local bbox.

    RUN 32 -- ADAPTIVE EDGES (OPTION R, "attack the bin grain"): `turn_edges`/`len_edges`
    (optional, default `None` — every pre-existing caller keeps byte-identical uniform-count
    behaviour) are plain lists of ascending bin-boundary floats, threaded straight through to
    the Rust `StrokeQuantize` Term's own new `turn_edges`/`len_edges` fields (see
    `runners/dsl/src/term.rs`'s doc for the full semantics — quantile/equal-mass edges computed
    over the LEARN population by `domains/adaptive_bins.py`, held as graph data, never computed
    here). `emit_residual` (default `False`, additive) threads through to the Term's own
    `emit_residual` flag — the output dict then also carries a `"residuals"` key."""
    term = {
        "type": "StrokeQuantize",
        "points": {"type": "Lit", "value": [[float(x), float(y)] for (x, y) in points]},
        "segments": segments, "turn_bins": turn_bins, "len_bins": len_bins,
        "grid": grid, "scale_bins": scale_bins,
    }
    if invariant_only:
        term["invariant_only"] = True
    if canonical_pose:
        term["canonical_pose"] = True
    if bounds is not None:
        term["bounds"] = {"type": "Lit", "value": [float(v) for v in bounds]}
    if turn_edges is not None:
        term["turn_edges"] = {"type": "Lit", "value": [float(v) for v in turn_edges]}
    if len_edges is not None:
        term["len_edges"] = {"type": "Lit", "value": [float(v) for v in len_edges]}
    if emit_residual:
        term["emit_residual"] = True
    return native.evaluate(term, {})


def _existing_names(sub, kind: str, node_type: str = "ShapeSignature") -> set:
    """`node_type` (EAGER CHILD MINTING, optional, default `"ShapeSignature"` — every
    pre-existing call keeps behaving byte-identically): the node TYPE to scan. Eager
    fine-grain children live under a DELIBERATELY SEPARATE node type
    (`"ShapeSignatureFineChild"`, see `grow_stroke_refinement_quantum`'s docstring) so they
    never compete in the PRIMARY `ShapeDecode` fine-grain scan `_score_span` performs — this
    param lets the SAME dedup-by-name idiom address that separate type too."""
    out = set()
    for n in sub.nodes(node_type):
        at = sub.node(n)["attrs"]
        if at.get("kind") == kind:
            nm = at.get("name")
            if nm:
                out.add(nm)
    return out


def _find_stroke_node(sub, name: str, kind: str = "stroke",
                       node_type: str = "ShapeSignature") -> Optional[int]:
    """Mechanical find-by-name (mirrors `_writer_node`'s idiom) -- the graph node for a
    held `ShapeSignature{kind:'stroke'}` quantum, or `None` if no such quantum exists yet.
    `kind`/`node_type` (EAGER CHILD MINTING, optional, defaults preserve the exact
    pre-existing behaviour) generalize the same lookup to the separate
    `ShapeSignatureFineChild` type (see `grow_stroke_refinement_quantum`'s docstring)."""
    for n in sub.nodes(node_type):
        at = sub.node(n)["attrs"]
        if at.get("kind") == kind and at.get("name") == name:
            return n
    return None


def _invariant_points(points, n: int = PROTOTYPE_LEN) -> list:
    """Pure geometry (mechanical, no decision): the SAME invariance construction
    `StrokeQuantize` performs in Rust (translate-to-start, rotate-to-initial-heading,
    arc-length-scale-to-1) but kept CONTINUOUS instead of quantized -- the design's DtwTo
    near-miss fallback (item 4) needs a real-valued shape distance, not a binned relation
    count. Reuses `glyph_motor_world._resample_arclen`, the SAME Python-side pure-geometry
    precedent `domains/ink_decode.py`'s own `_knots` already established (arc-length
    resampling has always been a Python-side mechanical operation in this codebase, never a
    Rust primitive) -- this is that same precedent extended one step (translate/rotate/scale
    normalization), not a new kind of thing. Degenerate (<2 points) input returns a fixed
    2-point placeholder at the origin (never raises -- callers treat an all-zero prototype as
    "no real shape info", naturally scoring poorly against everything, same discipline
    `_knots` already applies to degenerate spans)."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return [[0.0, 0.0]] * max(2, n)
    from domains import glyph_motor_world as gmw
    rs = gmw._resample_arclen(pts, max(2, n))
    rs = rs - rs[0]
    seg0 = rs[1] - rs[0] if len(rs) > 1 else np.array([1.0, 0.0])
    theta = -np.arctan2(seg0[1], seg0[0])
    c, s_ = np.cos(theta), np.sin(theta)
    rot = np.array([[c, -s_], [s_, c]])
    rs = rs @ rot.T
    arclen = float(np.sum(np.linalg.norm(np.diff(rs, axis=0), axis=1))) or 1.0
    rs = rs / arclen
    return rs.tolist()


def _bump_codebook_epoch(sub, ag_node) -> None:
    """Mechanical set_attr — the SAME dynamic-quantization epoch bump
    `grow_part_library` does (domains/reflective_faculty.py:2546-2553) so
    `sd_redecode` re-arms any Observation last decoded under an older codebook."""
    if ag_node is None:
        return
    cur = sub.node(ag_node)["attrs"].get("codebook_epoch") or 0.0
    sub.set_attr(ag_node, "codebook_epoch", float(cur) + 1.0)


def grow_stroke_quantum(agent, points, name: str, *,
                         segments: int = DEFAULT_SEGMENTS, turn_bins: int = DEFAULT_TURN_BINS,
                         len_bins: int = DEFAULT_LEN_BINS, grid: int = DEFAULT_GRID,
                         scale_bins: int = DEFAULT_SCALE_BINS,
                         coarse_turn_bins: int = COARSE_TURN_BINS,
                         coarse_len_bins: int = COARSE_LEN_BINS,
                         mid_turn_bins: int = MID_TURN_BINS,
                         mid_len_bins: int = MID_LEN_BINS,
                         subfine_turn_bins: int = SUBFINE_TURN_BINS,
                         subfine_len_bins: int = SUBFINE_LEN_BINS,
                         category: str = DEFAULT_CATEGORY,
                         continuous_parent: Optional[str] = None,
                         turn_edges: Optional[list] = None,
                         len_edges: Optional[list] = None) -> dict[str, Any]:
    """The single-span GROWTH twin `build_stroke_codebook` uses per-entry, and ALSO the OOV
    MINT path's own quantum-minting primitive (`domains/ink_decode.py` calls this when the
    seeded `sd_mint_quantum` fires for a span the ladder could not explain — the mint DECISION
    is the rule's, this only INSTALLS what the rule already decided is novel). Quantizes ONE
    stroke via the held `StrokeQuantize` Term (`canonical_pose=True` — see module docstring's
    codebook convention) and installs it as a new `ShapeSignature{kind:"stroke"}`, teach()-
    persisted under `category` (default `"stroke_shapes"`), codebook epoch bumped exactly
    once. Idempotent by name — a name already held is a no-op, reported not re-grown.

    REFINEMENT RUNG (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "REFINEMENT RUNG"
    section): every quantum now ALSO carries (1) a COARSE-grain signature (a SECOND
    `StrokeQuantize` call at `coarse_turn_bins`/`coarse_len_bins` — "tolerance = COARSENESS,
    not fuzzy matching: coarse-grain exact match IS the principled near-miss band") and (2) a
    continuous PROTOTYPE polyline (`_invariant_points`, for the DtwTo near-miss fallback).
    The coarse grain is installed as a COMPANION `ShapeSignatureCoarse`-typed node (SAME
    `name`, own `signature` attr holding the COARSE relations) rather than a second attr key
    on this node — a mechanical consequence of `ShapeDecode`/`TransformDecode`'s Rust
    `load_parts` hard-coding the `signature` attr key on whatever `codebook_type` it is
    pointed at (see `runners/dsl/src/shape_decode.rs::load_parts`); pointing a SECOND decode
    at `codebook_type="ShapeSignatureCoarse"` gives the SAME held Term a genuinely separate
    coarse codebook to decode against with ZERO Rust changes. Both nodes are taught together
    as one motion (one quantum, two grains) and are never minted independently of each other.

    GRAIN LADDER (RUN-4 LEVERS, "LEVER 2"): a THIRD companion `ShapeSignatureMid`-typed node
    (`mid_turn_bins`/`mid_len_bins`, DEFAULT strictly between COARSE and FINE — "more
    refinement rungs = more vocabulary") is installed the SAME way, `has_mid_grain`-edged to
    the fine node, for exactly the same mechanical reason (a genuinely separate `codebook_type`
    a `ShapeDecode`/`TransformDecode` call can point at). All three grains are taught together
    as ONE motion (one quantum, three grains); `ink_decode.py`'s post-lattice second look now
    tries FINE, then MID, then COARSE (Occam: the finest net that still exact-matches wins) —
    "distinct-at-mid identities": two quanta that collide at the COARSE grain (same coarse
    bucket values) but differ at MID still resolve to the RIGHT one, one net finer than coarse
    alone could tell apart, without paying fine's exact-match brittleness to jitter.

    EAGER CHILD MINTING (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING"
    section — the a6fe069b residual): a FOURTH grain, SUB-FINE (`subfine_turn_bins`/
    `subfine_len_bins`, DEFAULT strictly FINER than fine — "an entry NOT a base-grain change"),
    is stored the SAME way, as a `subfine_signature` ATTR on the fine node (NOT a fifth
    companion NODE TYPE the way coarse/mid are): STEP 0 (this module's own module-docstring-
    adjacent constant comment) found a FINE-tier recognition is ALWAYS exact-signature
    equality, so there is never anything to Argmax-decode a sub-fine CANDIDATE against at
    decode time the way coarse/mid genuinely are separate decode targets — sub-fine is only
    ever compared DIRECTLY against ONE already-identified parent (`ink_decode._refine_or_note`,
    generalized), never scanned as a codebook by `ShapeDecode` — so it needs no companion node
    type, just this one comparison-reference attr, computed alongside fine/mid/coarse as the
    SAME one motion.

    CONTINUOUS-NOVELTY MINTING (RUN 23, optional, default `None` — every pre-existing call
    keeps its byte-identical behaviour): `continuous_parent`, when given, tags the installed
    entry as a peer TOP-LEVEL quantum grown from `continuous_mint_or_note`'s own DtwTo-distance
    decision rather than the discrete OOV ladder — `name` is still a genuinely NEW, independent
    `ShapeSignature{kind:"stroke"}` node (same install path, same multi-grain signatures, its
    own prototype), just additionally attr-tagged to the quantum whose discrete bucket it
    shares (`continuous_mint_or_note` reads this attr back to find a quantum's own growing
    continuous family)."""
    sub = _sub(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    native = _native(agent)
    tagent = _teach_agent(agent)

    if name in _existing_names(sub, "stroke"):
        return {"grown": False, "name": name, "reason": "already a held stroke quantum"}

    # RUN 32 -- ADAPTIVE EDGES: applied to the FINE grain ONLY (the grain that carries
    # recognition identity, and the grain run 28's calibration measured the collapse on) --
    # coarse/mid/subfine stay on their existing uniform-count bins, unaffected, deliberately
    # out of this lever's scope (they are near-miss TOLERANCE bands, not identity carriers).
    q = _quantize(native, points, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
                  grid=grid, scale_bins=scale_bins, canonical_pose=True,
                  turn_edges=turn_edges, len_edges=len_edges)
    sig = q["signature"]
    coarse_q = _quantize(native, points, segments=segments, turn_bins=coarse_turn_bins,
                         len_bins=coarse_len_bins, grid=grid, scale_bins=scale_bins,
                         canonical_pose=True)
    coarse_sig = coarse_q["signature"]
    mid_q = _quantize(native, points, segments=segments, turn_bins=mid_turn_bins,
                      len_bins=mid_len_bins, grid=grid, scale_bins=scale_bins,
                      canonical_pose=True)
    mid_sig = mid_q["signature"]
    subfine_q = _quantize(native, points, segments=segments, turn_bins=subfine_turn_bins,
                          len_bins=subfine_len_bins, grid=grid, scale_bins=scale_bins,
                          canonical_pose=True)
    subfine_sig = subfine_q["signature"]
    proto = _invariant_points(points)
    attrs = {
        "name": name, "kind": "stroke",
        "signature": json.dumps([list(rel) for rel in sig]),
        "dim_types": list(INVARIANT_DIM_TYPES),
        "segments": segments, "turn_bins": turn_bins, "len_bins": len_bins,
        "grid": grid, "scale_bins": scale_bins,
        "arc_len": q.get("arc_len"), "n_points": q.get("n_points"),
        "coarse_signature": json.dumps([list(rel) for rel in coarse_sig]),
        "coarse_turn_bins": coarse_turn_bins, "coarse_len_bins": coarse_len_bins,
        "mid_signature": json.dumps([list(rel) for rel in mid_sig]),
        "mid_turn_bins": mid_turn_bins, "mid_len_bins": mid_len_bins,
        "subfine_signature": json.dumps([list(rel) for rel in subfine_sig]),
        "subfine_turn_bins": subfine_turn_bins, "subfine_len_bins": subfine_len_bins,
        "prototype": json.dumps([[float(x), float(y)] for (x, y) in proto]),
        "prototype_len": len(proto),
    }
    if continuous_parent is not None:
        attrs["continuous_parent"] = continuous_parent
    if turn_edges is not None:
        attrs["turn_edges"] = json.dumps([float(v) for v in turn_edges])
    if len_edges is not None:
        attrs["len_edges"] = json.dumps([float(v) for v in len_edges])
    res = teach(tagent, "ShapeSignature", attrs, category=category)

    coarse_attrs = {
        "name": name, "kind": "stroke_coarse",
        "signature": json.dumps([list(rel) for rel in coarse_sig]),
        "dim_types": list(INVARIANT_DIM_TYPES),
        "segments": segments, "turn_bins": coarse_turn_bins, "len_bins": coarse_len_bins,
        "grid": grid, "scale_bins": scale_bins,
    }
    coarse_res = teach(tagent, "ShapeSignatureCoarse", coarse_attrs, category=category)

    mid_attrs = {
        "name": name, "kind": "stroke_mid",
        "signature": json.dumps([list(rel) for rel in mid_sig]),
        "dim_types": list(INVARIANT_DIM_TYPES),
        "segments": segments, "turn_bins": mid_turn_bins, "len_bins": mid_len_bins,
        "grid": grid, "scale_bins": scale_bins,
    }
    mid_res = teach(tagent, "ShapeSignatureMid", mid_attrs, category=category)

    fine_node, coarse_node = res.get("node"), coarse_res.get("node")
    mid_node = mid_res.get("node")
    if fine_node is not None and coarse_node is not None:
        sub.add_edge_unchecked(fine_node, "has_coarse_grain", coarse_node)
    if fine_node is not None and mid_node is not None:
        sub.add_edge_unchecked(fine_node, "has_mid_grain", mid_node)

    _bump_codebook_epoch(sub, ag_node)
    return {"grown": True, "name": name, "node": fine_node, "coarse_node": coarse_node,
            "mid_node": mid_node, "seed": res.get("seed"), "signature_relations": len(sig),
            "pose": q.get("pose")}


# --------------------------------------------------------------------------- #
# CONTINUOUS-NOVELTY MINTING (RUN 23, scratchpad/HANDWRITING_DESIGN.md-adjacent, the run-16
# law -- "continuous beats quantized for VERDICTS" -- applied to GROWTH, per commit
# 9762130f's own closing clause): a span that RECOGNIZED at some tier (`ink_decode`'s ladder
# already decided its discrete identity, UNCHANGED) but whose real-valued shape differs enough
# from what that identity's own continuous PROTOTYPE (or one of its already-minted continuous
# siblings) actually looks like MINTS a peer quantum. The DECISION (which family member is
# nearest; whether the nearest distance exceeds the threshold) is a HELD Term evaluation
# (`DtwTo` + `Argmin` + `Lt`, the EXACT idiom `ink_decode._dtw_fallback` already established)
# -- this function only INSTALLS what that decision produced, the SAME
# "rule decides, Python installs" discipline every mint path in this codebase follows.
# --------------------------------------------------------------------------- #
def _prototype_anchor(sub, chosen_name: str, *, kind: str = "stroke",
                      node_type: str = "ShapeSignature", max_hops: int = 8) -> Optional[str]:
    """Resolve `chosen_name` to the nearest ancestor (walking `refines` — a refinement CHILD's
    own attr naming its COARSE/MID/DtwTo-triggered parent, `grow_stroke_refinement_quantum`'s
    own convention) that actually carries a continuous `prototype`. WHY this is needed: a
    refinement child minted off the coarse/mid/DtwTo path (`ink_decode._refine_or_note`) is
    installed, by that function's own DEFAULT `node_type`/`kind`, into the SAME top-level
    `ShapeSignature{kind:"stroke"}` population `_score_span`'s fine-tier Argmax scans — so a
    LATER span can recognize the CHILD directly at "fine" — but `grow_stroke_refinement_
    quantum` stores only the span's already-QUANTIZED signature, never a continuous prototype
    (there is no raw-points argument to derive one from at that call site). Continuous-novelty
    minting needs a REAL prototype to DTW-compare against, so it anchors on whichever ancestor
    in the refinement tree actually has one — in every case this codebase currently produces,
    that is the ORIGINAL `grow_stroke_quantum`-installed family root. Returns the deepest name
    reached (even without a prototype) if the chain ends without ever finding one — an honest
    "nothing to anchor to", letting the caller's own "no prototypes in family" branch report
    it — or `None` only when `chosen_name` itself has no held node at all."""
    name = chosen_name
    seen: set = set()
    for _ in range(max_hops):
        if name in seen:
            break
        seen.add(name)
        node = _find_stroke_node(sub, name, kind=kind, node_type=node_type)
        if node is None:
            return None if name == chosen_name else name
        at = sub.node(node)["attrs"]
        if at.get("prototype"):
            return name
        parent = at.get("refines")
        if not parent:
            return name
        name = parent
    return name


def _continuous_family(sub, chosen_name: str, *, kind: str = "stroke",
                       node_type: str = "ShapeSignature",
                       max_scan: int = MAX_CONTINUOUS_FAMILY_SCAN) -> list[tuple[str, int]]:
    """Mechanical read-back (no decision): `chosen_name`'s own node, PLUS every already-minted
    continuous sibling (`continuous_parent == chosen_name`) — the growing "cluster set" a new
    observation is compared against. Bounded by `max_scan` (a cost bound, not a choice — see
    `MAX_CONTINUOUS_FAMILY_SCAN`'s own module-level comment)."""
    parent_node = _find_stroke_node(sub, chosen_name, kind=kind, node_type=node_type)
    if parent_node is None:
        return []
    family = [(chosen_name, parent_node)]
    for n in sub.nodes(node_type):
        if len(family) >= max_scan:
            break
        at = sub.node(n)["attrs"]
        if at.get("kind") == kind and at.get("continuous_parent") == chosen_name:
            nm = at.get("name")
            if nm:
                family.append((nm, n))
    return family


def continuous_mint_or_note(agent, chosen_name: str, points, *,
                            threshold: float = DEFAULT_CONTINUOUS_MINT_THRESHOLD,
                            segments: int = DEFAULT_SEGMENTS, turn_bins: int = DEFAULT_TURN_BINS,
                            len_bins: int = DEFAULT_LEN_BINS, grid: int = DEFAULT_GRID,
                            scale_bins: int = DEFAULT_SCALE_BINS,
                            coarse_turn_bins: int = COARSE_TURN_BINS,
                            coarse_len_bins: int = COARSE_LEN_BINS,
                            mid_turn_bins: int = MID_TURN_BINS, mid_len_bins: int = MID_LEN_BINS,
                            subfine_turn_bins: int = SUBFINE_TURN_BINS,
                            subfine_len_bins: int = SUBFINE_LEN_BINS,
                            category: str = DEFAULT_CATEGORY, kind: str = "stroke",
                            node_type: str = "ShapeSignature",
                            max_family_scan: int = MAX_CONTINUOUS_FAMILY_SCAN) -> dict[str, Any]:
    """THE continuous-mint decision + install, for ONE recognized span. `chosen_name` is a
    decision ALREADY MADE by `ink_decode`'s ladder (the fine/mid/coarse/DtwTo tier's own
    winner) -- this call never touches recognition. `points` is the span's OWN raw pen-path
    points (the same geometry `ink_decode` already resampled into `knots[st:e]`).

    Mechanism: gather `chosen_name`'s own continuous FAMILY (`_continuous_family` — itself plus
    every quantum already minted off it by a PRIOR call to this function); compute this
    observation's own continuous invariant PROTOTYPE (`_invariant_points`, the SAME real-valued
    normalization `_dtw_fallback`'s own near-miss candidates use); ONE held `DtwTo` evaluate per
    family member, a held `Argmin` picks the NEAREST, a held `Lt` decides whether that nearest
    distance still EXCEEDS `threshold` (mint) or not (the observation is adequately explained
    by an existing family member — no bin change, no install). A mint installs a genuinely NEW
    TOP-LEVEL quantum via `grow_stroke_quantum` (own multi-grain signatures + own prototype,
    `continuous_parent=chosen_name`), NAMED by the family's own current size (`chosen_name
    __cont_<n>`, mechanical bookkeeping — `_existing_names` provides idempotency/collision
    safety, the SAME guard every other mint path relies on) -- there is no discrete content to
    hash for dedup (that is the WHOLE point: the discrete signature is, by construction,
    IDENTICAL to an existing family member's, since this span already recognized against it);
    the threshold-gated family-nearest-neighbour check IS the dedup mechanism instead — a
    SUBSEQUENT occurrence of the SAME "new" continuous variant lands near the sibling THIS call
    just minted and will not mint again.

    ANCHORING (RUN 23, honest fix found empirically against real Omniglot ink -- a refinement
    CHILD, per its own docstring, competes as a top-level "fine" candidate but carries no
    prototype of its own): `chosen_name` is first resolved to its nearest prototype-bearing
    ANCHOR via `_prototype_anchor` (walks `refines` upward when needed) — the family, the mint
    decision, and any new quantum's own `continuous_parent`/naming are all relative to that
    ANCHOR, never to a prototype-less refinement child. `"requested_as"` in the return value
    preserves the ORIGINAL `chosen_name` for provenance/debugging when it differs from the
    resolved anchor.

    Returns `{"minted": bool, "checked": bool, ...}` — `checked=False` only when `chosen_name`
    (or its resolved anchor) has no held node, or no member of its family carries a prototype
    at all (an honest non-crash, mirrors `_dtw_fallback`'s own "no candidates" branch)."""
    sub = _sub(agent)
    native = _native(agent)

    anchor = _prototype_anchor(sub, chosen_name, kind=kind, node_type=node_type)
    if anchor is None:
        return {"minted": False, "checked": False, "reason": "no such quantum"}

    family = _continuous_family(sub, anchor, kind=kind, node_type=node_type,
                                max_scan=max_family_scan)
    if not family:
        return {"minted": False, "checked": False, "reason": "no such quantum"}

    dist_pairs = []
    for (nm, node) in family:
        proto_json = sub.node(node)["attrs"].get("prototype")
        if not proto_json:
            continue
        try:
            proto = json.loads(proto_json)
        except (TypeError, ValueError):
            continue
        dist_pairs.append((nm, proto))
    if not dist_pairs:
        return {"minted": False, "checked": False, "reason": "no prototypes in family",
                "family_size": len(family)}

    obs_proto = _invariant_points(points)
    scored = [
        (float(native.evaluate({"type": "DtwTo", "a": {"type": "Lit", "value": obs_proto},
                                "b": {"type": "Lit", "value": proto}}, {}) or 0.0), nm)
        for (nm, proto) in dist_pairs
    ]
    winner = native.evaluate({
        "type": "Argmin", "source": {"type": "Lit", "value": scored}, "var_name": "c",
        "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                  "index": {"type": "Lit", "value": 0}},
        "default": None,
    }, {})
    if winner is None:
        return {"minted": False, "checked": False, "reason": "argmin returned nothing",
                "family_size": len(family)}
    min_dist, nearest_name = float(winner[0]), winner[1]

    # Held Lt: mint iff the NEAREST family member is still further than `threshold` away
    # (`Lt(a=threshold, b=min_dist)` == threshold < min_dist == min_dist > threshold — the
    # SAME a/b convention `_dtw_fallback` uses, just the inverse verdict).
    should_mint = bool(native.evaluate({
        "type": "Lt", "a": {"type": "Lit", "value": float(threshold)},
        "b": {"type": "Lit", "value": min_dist}}, {}))

    if not should_mint:
        return {"minted": False, "checked": True, "min_dist": min_dist,
                "nearest": nearest_name, "family_size": len(family), "anchor": anchor,
                "requested_as": chosen_name}

    existing = _existing_names(sub, kind, node_type=node_type)
    new_name = f"{anchor}__cont_{len(family)}"
    bump = len(family)
    while new_name in existing:
        bump += 1
        new_name = f"{anchor}__cont_{bump}"

    grow_res = grow_stroke_quantum(
        agent, points, new_name, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
        grid=grid, scale_bins=scale_bins, coarse_turn_bins=coarse_turn_bins,
        coarse_len_bins=coarse_len_bins, mid_turn_bins=mid_turn_bins, mid_len_bins=mid_len_bins,
        subfine_turn_bins=subfine_turn_bins, subfine_len_bins=subfine_len_bins,
        category=category, continuous_parent=anchor)
    return {"minted": bool(grow_res.get("grown")), "checked": True, "name": new_name,
            "min_dist": min_dist, "nearest": nearest_name, "family_size": len(family),
            "anchor": anchor, "requested_as": chosen_name, "grow": grow_res}


def grow_stroke_refinement_quantum(agent, name: str, parent_name: str, refined_dim: str,
                                    fine_signature: list, *,
                                    segments: int = DEFAULT_SEGMENTS,
                                    turn_bins: int = DEFAULT_TURN_BINS,
                                    len_bins: int = DEFAULT_LEN_BINS, grid: int = DEFAULT_GRID,
                                    scale_bins: int = DEFAULT_SCALE_BINS,
                                    category: str = DEFAULT_CATEGORY,
                                    refined_from_tier: Optional[str] = None,
                                    node_type: str = "ShapeSignature", kind: str = "stroke",
                                    parent_node_type: str = "ShapeSignature",
                                    parent_kind: str = "stroke") -> dict[str, Any]:
    """REFINEMENT MINT install (design item 3): the PER-DIMENSION CHILD quantum for a coarse
    family whose fine grain did not exact-match — `seeds/ink_refinement.json`'s `ir_*` rules
    ALREADY DECIDED whether/which dimension needed refining (turn-only / len-only / both);
    this call only INSTALLS that decision, exactly like `grow_stroke_quantum` installs
    `sd_mint_quantum`'s OOV decision. `fine_signature` is the SPAN'S OWN already-quantized
    full signature (`domains/ink_decode.py` already ran `StrokeQuantize` for the span — no
    re-quantization here, pure graph install). A refinement child does NOT get its own
    coarse-grain companion node: it stays IN its parent's coarse family by construction (a
    future span jittered the SAME way now gets an EXACT FINE match on this child directly,
    `_score_span`'s existing full-codebook scan already covers it — no new fallback tier
    needed for that case) — it inherits the parent's `coarse_signature` purely for
    provenance/introspection. `refines_quantum` edges the child to its coarse parent (when the
    parent is still held); `refined_dim` in {"turn","len","both"} records which dimension(s)
    the rule found could not be explained at the parent's fine grain. Idempotent by name (the
    content-keyed dedup name `ink_decode.py`'s caller computes, mirroring the OOV path's own
    `stroke_<sig_key>` naming).

    `refined_from_tier` (RUN-4 LEVERS, "LEVER 2" — GRAIN LADDER, optional, mechanical
    bookkeeping only): which tier (`"coarse"` or `"mid"`) actually recognized the span before
    this refinement fired (`ink_decode._refine_or_note`'s own already-decided `tier` value —
    not a new decision here, just recorded so `grain_vocabulary_report` can report vocabulary
    PER LEVEL).

    `node_type`/`kind` (EAGER CHILD MINTING, 2026-07-02, optional — every pre-existing call
    keeps its byte-identical default `"ShapeSignature"`/`"stroke"`, installing a competing
    TOP-LEVEL entry in the PRIMARY fine-grain codebook, exactly as before): an eager
    (fine-tier-triggered) child is minted with `node_type="ShapeSignatureFineChild"`,
    `kind="stroke_fine_child"` instead — a DELIBERATELY SEPARATE node type. WHY: an eager
    child's own `fine_signature` (its `signature` attr here) is, by construction, quantized at
    a SUB-FINE grain that DIFFERS from whatever bins the primary fine-tier decode uses — but
    installing it into the SAME `"ShapeSignature"` node type would still make it a candidate
    `_score_span`'s default `ShapeDecode` scan iterates (Rust's `load_parts` filters by node
    TYPE, never by a `kind` attr — see `character_compose.py`'s module docstring for the same
    observation at character grain), risking an accidental tie/fragmentation of the PRIMARY
    fine-grain recognition the run-5 lesson says must stay untouched. A genuinely separate node
    TYPE makes that PROVABLY impossible (the default `codebook_type="ShapeSignature"` never
    even enumerates `ShapeSignatureFineChild` nodes) rather than merely improbable — "detail
    enters as CHILDREN only, base grains untouched" as a structural guarantee, not a
    probabilistic one. `parent_node_type`/`parent_kind` (same defaults) generalize the PARENT
    lookup + `coarse_signature` inheritance the same way (an eager child's parent is still an
    ordinary top-level `ShapeSignature{kind:'stroke'}` entry — only the CHILD's own type
    changes)."""
    sub = _sub(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    tagent = _teach_agent(agent)

    if name in _existing_names(sub, kind, node_type=node_type):
        return {"grown": False, "name": name, "reason": "already a held stroke quantum"}

    parent_node = _find_stroke_node(sub, parent_name, kind=parent_kind, node_type=parent_node_type)
    parent_coarse_sig = None
    if parent_node is not None:
        parent_coarse_sig = sub.node(parent_node)["attrs"].get("coarse_signature")

    attrs = {
        "name": name, "kind": kind,
        "signature": json.dumps([list(rel) for rel in fine_signature]),
        "dim_types": list(INVARIANT_DIM_TYPES),
        "segments": segments, "turn_bins": turn_bins, "len_bins": len_bins,
        "grid": grid, "scale_bins": scale_bins,
        "coarse_signature": parent_coarse_sig,
        "refines": parent_name, "refined_dim": refined_dim,
    }
    if refined_from_tier is not None:
        attrs["refined_from_tier"] = refined_from_tier
    res = teach(tagent, node_type, attrs, category=category)
    node = res.get("node")
    if node is not None and parent_node is not None:
        sub.add_edge_unchecked(node, "refines_quantum", parent_node)

    _bump_codebook_epoch(sub, ag_node)
    return {"grown": True, "name": name, "node": node, "parent": parent_name,
            "refined_dim": refined_dim}


def grow_substroke_quantum(agent, points, name: str, *, segments: int = SUBSTROKE_SEGMENTS,
                            turn_bins: int = SUBSTROKE_TURN_BINS,
                            len_bins: int = SUBSTROKE_LEN_BINS, grid: int = DEFAULT_GRID,
                            scale_bins: int = DEFAULT_SCALE_BINS,
                            category: str = DEFAULT_CATEGORY) -> dict[str, Any]:
    """BRANCH A EXECUTION's sub-stroke mint primitive -- `domains/ink_decode.py`'s
    `decode_substrokes` calls this when the WITHIN-stroke inner lattice's own OOV path (the
    SAME `induce_concern` -> `sd_mint_quantum` ladder the outer stroke-level OOV path already
    uses, one level down) decides a sub-span is genuinely novel; the DECISION is the seeded
    rule's, this only INSTALLS it (mirrors `grow_stroke_quantum`'s own idiom exactly).
    Deliberately the SIMPLEST possible grow: ONE grain (the coarse-per-run-5's-law
    `SUBSTROKE_TURN_BINS`/`SUBSTROKE_LEN_BINS` bins), no coarse/mid/subfine companion nodes,
    no refinement ladder -- a sub-stroke's IDENTITY is meant to recur in many different
    ARRANGEMENTS (that is the whole point of composing one level down), not to itself carry
    fine-grained per-instance detail. `canonical_pose=True` (the SAME codebook-authoring
    convention `grow_stroke_quantum` uses) so an observed sub-span's ACTUAL within-stroke pose
    reads as a plain re-quantization against the stroke's own frame
    (`character_compose.compose_stroke_signature`'s "srel" relation), never a delta search --
    sub-strokes get NO `TransformDecode` pose-reading of their own this phase (the design's own
    scope note: "check whether re-rank even needs changing this phase; report" -- it does not,
    see `ink_decode.decode_substrokes`'s docstring). Idempotent by name."""
    sub = _sub(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    native = _native(agent)
    tagent = _teach_agent(agent)

    if name in _existing_names(sub, "substroke"):
        return {"grown": False, "name": name, "reason": "already a held substroke quantum"}

    q = _quantize(native, points, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
                  grid=grid, scale_bins=scale_bins, canonical_pose=True)
    sig = q["signature"]
    attrs = {
        "name": name, "kind": "substroke",
        "signature": json.dumps([list(rel) for rel in sig]),
        "dim_types": list(INVARIANT_DIM_TYPES),
        "segments": segments, "turn_bins": turn_bins, "len_bins": len_bins,
        "grid": grid, "scale_bins": scale_bins,
        "arc_len": q.get("arc_len"), "n_points": q.get("n_points"),
    }
    res = teach(tagent, "ShapeSignature", attrs, category=category)
    _bump_codebook_epoch(sub, ag_node)
    return {"grown": True, "name": name, "node": res.get("node"), "seed": res.get("seed"),
            "signature_relations": len(sig), "pose": q.get("pose")}


def substroke_vocabulary_report(sub) -> dict[str, Any]:
    """BRANCH A EXECUTION's read-back twin of `grain_vocabulary_report`, one grain down:
    mechanical count of the held `ShapeSignature{kind:"substroke"}` population -- "sub-stroke
    vocabulary >> 7 arrangement keys" is the design's own stated payoff signal, this is the
    quantum-COUNT half of that (the caller separately counts DISTINCT `strokeq_sub`
    arrangement-key values seen in composed character signatures for the other half)."""
    names = _existing_names(sub, "substroke")
    return {"total": len(names), "names": sorted(names)}


def grain_vocabulary_report(sub) -> dict[str, Any]:
    """RUN-4 LEVERS, "LEVER 2" — GRAIN LADDER: 'LEARN should now report vocabulary size PER
    LEVEL (top/mid/fine counts)'. Mechanical read-back over the held `ShapeSignature{kind:
    "stroke"}` codebook (no decision): `top` = quanta with no `refines` attr (the
    coarse-grain-installed families themselves — one COARSE bucket each, by construction);
    `distinct_coarse`/`distinct_mid`/`distinct_fine` = the number of DISTINCT quantized
    signature VALUES seen among those top-level quanta at each grain — how many buckets a
    query could actually land in at that resolution (a smaller `distinct_coarse` than
    `distinct_mid` than `distinct_fine` is the ladder doing its job: coarser grains collapse
    more of the earned vocabulary together). `children` = refinement quanta (`refines` set),
    broken down by `refined_from_tier` (which tier's near-miss triggered the mint) — `total`
    is the full deepest-grain library size (`len(_existing_names(sub, "stroke"))`, the SAME
    count every other report in this module already uses as 'the codebook size').

    EAGER CHILD MINTING (2026-07-02): `fine_children`/`fine_children_by_parent` report the
    SEPARATE `ShapeSignatureFineChild` population (`kind="stroke_fine_child"`,
    `grow_stroke_refinement_quantum`'s `node_type` param) — DELIBERATELY excluded from
    `top`/`children`/`total` above, which describe the PRIMARY recognition library an eager
    child never joins (see that function's docstring for why a separate node type is the
    structural guarantee "base grains untouched" needs)."""
    tops, children = [], []
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") != "stroke":
            continue
        if at.get("refines"):
            children.append(at)
        else:
            tops.append(at)

    def _distinct(attrs_list, key):
        vals = set()
        for at in attrs_list:
            v = at.get(key)
            if v is not None:
                vals.add(v)
        return len(vals)

    children_by_tier: dict[str, int] = {}
    for at in children:
        tier = at.get("refined_from_tier") or "unspecified"
        children_by_tier[tier] = children_by_tier.get(tier, 0) + 1

    fine_children = [sub.node(n)["attrs"] for n in sub.nodes("ShapeSignatureFineChild")
                     if sub.node(n)["attrs"].get("kind") == "stroke_fine_child"]
    fine_children_by_parent: dict[str, int] = {}
    for at in fine_children:
        p = at.get("refines") or "?"
        fine_children_by_parent[p] = fine_children_by_parent.get(p, 0) + 1

    return {
        "top": len(tops),
        "distinct_coarse": _distinct(tops, "coarse_signature"),
        "distinct_mid": _distinct(tops, "mid_signature"),
        "distinct_fine": _distinct(tops, "signature"),
        "children": len(children),
        "children_by_tier": children_by_tier,
        "total": len(tops) + len(children),
        "fine_children": len(fine_children),
        "fine_children_by_parent": fine_children_by_parent,
    }


def _glyph_stroke_sources(n_per_prim: int = 48) -> list[tuple[str, list]]:
    """Mechanical: one (name, points) source PER STROKE of every GLYPHS motor program
    (domains/glyph_motor_world.py) — the synthetic, deterministic, no-dataset source the
    design names ("Sources: glyph_motor_world GLYPHS motor programs")."""
    from domains import glyph_motor_world as gmw
    out: list[tuple[str, list]] = []
    for glyph_name, strokes in gmw.GLYPHS.items():
        for i, (prim, args) in enumerate(strokes):
            pts = gmw._sample_stroke(prim, args, n_per_prim)
            out.append((f"{glyph_name}_{i}", pts.tolist()))
    return out


def _pickle_medoid_sources(pickle_path: Path) -> list[tuple[str, list]]:
    """Mechanical: migrate the legacy `.bigtmp/gemma_stroke_inventory.pkl` medoid inventory
    (domains/bootstrapped_stroke_inventory.py's teacher-bootstrapped stroke-identity medoids,
    `{"medoids": [...]}`) into (name, points) sources, IF the pickle exists — guarded, no
    error if absent (synthetic GLYPHS sources are the default path)."""
    if not os.path.exists(pickle_path):
        return []
    with open(pickle_path, "rb") as fh:
        cache = pickle.load(fh)
    medoids = cache.get("medoids") or []
    out = []
    for i, m in enumerate(medoids):
        pts = [[float(p[0]), float(p[1])] for p in m]
        out.append((f"medoid_{i}", pts))
    return out


def build_stroke_codebook(agent, sources: Optional[list[tuple[str, list]]] = None, *,
                           include_pickle: bool = True,
                           pickle_path: Path = DEFAULT_PICKLE,
                           category: str = DEFAULT_CATEGORY,
                           segments: int = DEFAULT_SEGMENTS, turn_bins: int = DEFAULT_TURN_BINS,
                           len_bins: int = DEFAULT_LEN_BINS, grid: int = DEFAULT_GRID,
                           scale_bins: int = DEFAULT_SCALE_BINS) -> dict[str, Any]:
    """Build (or extend) the held stroke codebook: quantize every source stroke
    (`canonical_pose`) into a `ShapeSignature{kind:"stroke"}` node, teach()-persisted,
    codebook epoch bumped per new entry.

    `sources` — optional explicit `[(name, points), ...]`; defaults to every GLYPHS stroke
    (`_glyph_stroke_sources`). When `include_pickle` and the legacy medoid pickle exists, its
    medoids are ALSO migrated in (retiring the pickle as the source of truth per the design —
    the pickle itself is left untouched, only its content is copied into the graph).

    Returns `{grown: [names], skipped: [(name, reason)], library_size: N}` — honest about
    which sources actually installed a new quantum vs. were already held."""
    if sources is None:
        sources = _glyph_stroke_sources()
    if include_pickle:
        sources = list(sources) + _pickle_medoid_sources(pickle_path)

    grown, skipped = [], []
    for name, points in sources:
        try:
            res = grow_stroke_quantum(agent, points, name, segments=segments,
                                       turn_bins=turn_bins, len_bins=len_bins,
                                       grid=grid, scale_bins=scale_bins, category=category)
        except ValueError as e:
            if "UnknownTermType" in str(e) or "canonical_pose" in str(e):
                # StrokeQuantize (or its canonical_pose option) not yet landed (see
                # _stroke_quantize_live) — honest report, not a silent swallow: every
                # remaining source will fail the same way.
                skipped.append((name, "StrokeQuantize (canonical_pose) Term not yet landed"))
                continue
            raise
        if res["grown"]:
            grown.append(name)
        else:
            skipped.append((name, res["reason"]))

    sub = _sub(agent)
    return {"grown": grown, "skipped": skipped,
            "library_size": len(_existing_names(sub, "stroke")),
            "how": ("each source stroke quantized via the held StrokeQuantize Term "
                    "(canonical_pose) and installed as a ShapeSignature{kind:'stroke'}; "
                    "no Python geometry, no decision.")}


# --------------------------------------------------------------------------- #
# MIGRATION: upgrade the PRE-EXISTING (pre-refinement-rung) `seeds/stroke_shapes.json`
# entries in place — the 67 real Omniglot-earned quanta + 44 GLYPHS-authored quanta must not
# be silently discarded just because they predate the coarse-grain/prototype fields
# `grow_stroke_quantum` now writes for every NEW mint. One-off, mechanical, idempotent
# (skips anything that already carries `coarse_signature`).
# --------------------------------------------------------------------------- #
def _rebin_signed(v_fine: float, fine_bins: int, coarse_bins: int) -> int:
    """Best-effort REBIN of an already-quantized SIGNED angle bin (turn_q / pose_o) from one
    bin resolution to another, used ONLY when the original raw geometry is not recoverable
    (see `migrate_multigrain_codebook`'s docstring) — an APPROXIMATION, not a re-quantization
    of the true continuous angle (that would need the original points, which pre-refinement
    entries never stored). Mirrors `runners/dsl/src/strokes.rs::quantize_signed_angle`'s own
    bin-width-then-wrap arithmetic, just re-run at `coarse_bins` against the bin-center angle
    the fine value implies (`v_fine * 360/fine_bins`)."""
    if fine_bins <= 0 or coarse_bins <= 0:
        return 0
    approx_deg = float(v_fine) * (360.0 / fine_bins)
    wrapped = ((approx_deg + 180.0) % 360.0) - 180.0
    if wrapped <= -180.0:
        wrapped += 360.0
    bin_width = 360.0 / coarse_bins
    raw = int(math.floor(abs(wrapped) / bin_width + 0.5))
    if wrapped < 0:
        raw = -raw
    half = coarse_bins // 2
    while raw > half:
        raw -= coarse_bins
    while raw < -half:
        raw += coarse_bins
    return raw


def _rebin_bucket(v_fine: float, fine_bins: int, coarse_bins: int) -> int:
    """Best-effort REBIN of an already-quantized UNSIGNED bucket index (len_q) — same
    approximation caveat as `_rebin_signed`: estimates the fine bucket's MIDPOINT fraction
    and re-buckets it at `coarse_bins`, mirroring `strokes.rs::quantize_bucket`'s floor
    digitization."""
    if fine_bins <= 0 or coarse_bins <= 0:
        return 0
    frac = (float(v_fine) + 0.5) / fine_bins
    idx = int(math.floor(frac * coarse_bins))
    return max(0, min(coarse_bins - 1, idx))


def _rebin_signature(sig: list, fine_turn_bins: int, fine_len_bins: int,
                     coarse_turn_bins: int, coarse_len_bins: int) -> list:
    """Apply `_rebin_signed`/`_rebin_bucket` to every `seg`/`pose_o` relation of an
    already-quantized FINE signature, leaving `pose_x`/`pose_y`/`pose_s` UNTOUCHED (the
    design's coarse grain only widens turn_bins/len_bins — grid/scale_bins are shared across
    grains). Pure arithmetic, no geometry, no decision."""
    out = []
    for rel in sig:
        if not (isinstance(rel, list) and rel):
            out.append(rel)
            continue
        pred = rel[0]
        if pred == "seg" and len(rel) >= 4:
            out.append(["seg", rel[1],
                        _rebin_signed(rel[2], fine_turn_bins, coarse_turn_bins),
                        _rebin_bucket(rel[3], fine_len_bins, coarse_len_bins)])
        elif pred == "pose_o" and len(rel) >= 2:
            out.append(["pose_o", _rebin_signed(rel[1], fine_turn_bins, coarse_turn_bins)])
        else:
            out.append(rel)
    return out


def migrate_multigrain_codebook(seeds_dir: Path = None, category: str = DEFAULT_CATEGORY,
                                 coarse_turn_bins: int = COARSE_TURN_BINS,
                                 coarse_len_bins: int = COARSE_LEN_BINS) -> dict[str, Any]:
    """ONE-OFF, idempotent migration: upgrade every PRE-EXISTING `ShapeSignature{kind:"stroke"}`
    entry in `seeds/<category>.json` that predates the refinement rung (no `coarse_signature`
    attr yet) to carry the SAME coarse-grain + prototype fields `grow_stroke_quantum` now
    writes for new mints, PLUS install the missing companion `ShapeSignatureCoarse` node —
    without discarding the 67 real Omniglot-earned + 44 GLYPHS-authored quanta already held.

    Raw pen-path POINTS were never part of the pre-refinement schema (only the already-
    quantized `signature` + meta were persisted), so an EXACT re-derivation needs the
    original geometry back. Two honest paths, reported per-entry:

    - REGENERATED (exact): the entry's `name` matches a `_glyph_stroke_sources()` name (the
      deterministic GLYPHS builder is REPRODUCIBLE — same source, same output, always) — the
      real points are regenerated, re-quantized at both grains via the held StrokeQuantize
      Term, verified to reproduce the STORED fine signature bit-for-bit (a safety check catching
      any drift in `glyph_motor_world` since minting), and a real invariant-normalized
      PROTOTYPE is stored.
    - REBINNED (approximate): every other entry (the 67 real Omniglot strokes + any ad hoc
      test-authored name) has no recoverable source — the coarse signature is
      APPROXIMATED by rebinning the stored FINE quantized values (`_rebin_signature`, pure
      arithmetic, not a re-quantization of real geometry) and NO prototype is installed
      (`prototype_available: False`, honestly reported, not silently defaulted to zeros) —
      DtwTo simply skips these entries as fallback candidates, degrading gracefully.

    Returns `{regenerated: [names], rebinned: [names], skipped_already_migrated: [names],
    verify_mismatch: [names]}` for an honest report. Mutates `seeds/<category>.json` in
    place (a fresh `srs.Substrate()` supplies the held StrokeQuantize Term for the
    regenerated path; no live agent graph is touched — this is a SEED FILE migration, load a
    fresh boot afterward to see it)."""
    import substrate_rs as srs

    path = (seeds_dir or SEEDS_DIR_DEFAULT) / f"{category}.json"
    if not path.exists():
        return {"regenerated": [], "rebinned": [], "skipped_already_migrated": [],
                "verify_mismatch": [], "note": f"{path} does not exist -- nothing to migrate"}
    manifest = json.loads(path.read_text())
    nodes = manifest.setdefault("nodes", [])

    reproducible = dict(_glyph_stroke_sources())
    s = srs.Substrate()
    native = s._inner

    by_name_fine = {n["attrs"]["name"]: n for n in nodes
                    if n.get("type") == "ShapeSignature" and n.get("attrs", {}).get("kind") == "stroke"}
    existing_coarse_names = {n["attrs"]["name"] for n in nodes if n.get("type") == "ShapeSignatureCoarse"}
    next_local_id = 1 + max([n.get("local_id", -1) for n in nodes], default=-1)

    regenerated, rebinned, skipped, mismatch = [], [], [], []
    new_coarse_nodes = []
    for name, node in by_name_fine.items():
        attrs = node["attrs"]
        if attrs.get("coarse_signature"):
            skipped.append(name)
            continue
        turn_bins = int(attrs.get("turn_bins") or DEFAULT_TURN_BINS)
        len_bins = int(attrs.get("len_bins") or DEFAULT_LEN_BINS)
        segments = int(attrs.get("segments") or DEFAULT_SEGMENTS)
        grid = int(attrs.get("grid") or DEFAULT_GRID)
        scale_bins = int(attrs.get("scale_bins") or DEFAULT_SCALE_BINS)
        fine_sig = json.loads(attrs["signature"])

        pts = reproducible.get(name)
        if pts is not None:
            q = _quantize(native, pts, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
                          grid=grid, scale_bins=scale_bins, canonical_pose=True)
            if [list(r) for r in q["signature"]] != fine_sig:
                mismatch.append(name)   # geometry drifted since minting -- fall back to rebin
            else:
                coarse_q = _quantize(native, pts, segments=segments, turn_bins=coarse_turn_bins,
                                     len_bins=coarse_len_bins, grid=grid, scale_bins=scale_bins,
                                     canonical_pose=True)
                proto = _invariant_points(pts)
                attrs["coarse_signature"] = json.dumps([list(r) for r in coarse_q["signature"]])
                attrs["coarse_turn_bins"], attrs["coarse_len_bins"] = coarse_turn_bins, coarse_len_bins
                attrs["prototype"] = json.dumps([[float(x), float(y)] for (x, y) in proto])
                attrs["prototype_len"] = len(proto)
                attrs["migration"] = "regenerated_exact"
                regenerated.append(name)
                if name not in existing_coarse_names:
                    new_coarse_nodes.append({
                        "local_id": next_local_id, "type": "ShapeSignatureCoarse",
                        "attrs": {"name": name, "kind": "stroke_coarse",
                                  "signature": attrs["coarse_signature"],
                                  "dim_types": list(INVARIANT_DIM_TYPES), "segments": segments,
                                  "turn_bins": coarse_turn_bins, "len_bins": coarse_len_bins,
                                  "grid": grid, "scale_bins": scale_bins}})
                    next_local_id += 1
                continue
        # REBIN fallback (no reproducible source, or a verify mismatch).
        coarse_sig = _rebin_signature(fine_sig, turn_bins, len_bins, coarse_turn_bins, coarse_len_bins)
        attrs["coarse_signature"] = json.dumps(coarse_sig)
        attrs["coarse_turn_bins"], attrs["coarse_len_bins"] = coarse_turn_bins, coarse_len_bins
        attrs["migration"] = "rebinned_approx"
        attrs["prototype_available"] = False
        rebinned.append(name)
        if name not in existing_coarse_names:
            new_coarse_nodes.append({
                "local_id": next_local_id, "type": "ShapeSignatureCoarse",
                "attrs": {"name": name, "kind": "stroke_coarse", "signature": attrs["coarse_signature"],
                          "dim_types": list(INVARIANT_DIM_TYPES), "segments": segments,
                          "turn_bins": coarse_turn_bins, "len_bins": coarse_len_bins,
                          "grid": grid, "scale_bins": scale_bins, "migration": "rebinned_approx"}})
            next_local_id += 1

    nodes.extend(new_coarse_nodes)
    path.write_text(json.dumps(manifest, indent=1))
    return {"regenerated": regenerated, "rebinned": rebinned,
            "skipped_already_migrated": skipped, "verify_mismatch": mismatch,
            "n_coarse_nodes_added": len(new_coarse_nodes)}


__all__ = ["build_stroke_codebook", "grow_stroke_quantum", "grow_stroke_refinement_quantum",
           "migrate_multigrain_codebook", "grain_vocabulary_report", "INVARIANT_DIM_TYPES",
           "DEFAULT_SEGMENTS", "DEFAULT_TURN_BINS", "DEFAULT_LEN_BINS", "DEFAULT_GRID",
           "DEFAULT_SCALE_BINS", "DEFAULT_CATEGORY", "DEFAULT_PICKLE",
           "COARSE_TURN_BINS", "COARSE_LEN_BINS", "PROTOTYPE_LEN", "DEFAULT_DTW_THRESHOLD",
           "MID_TURN_BINS", "MID_LEN_BINS", "DEFAULT_GRAIN_LADDER",
           "SUBFINE_TURN_BINS", "SUBFINE_LEN_BINS",
           "SUBSTROKE_SEGMENTS", "SUBSTROKE_TURN_BINS", "SUBSTROKE_LEN_BINS",
           "grow_substroke_quantum", "substroke_vocabulary_report",
           "DEFAULT_CONTINUOUS_MINT_THRESHOLD", "MAX_CONTINUOUS_FAMILY_SCAN",
           "continuous_mint_or_note", "_continuous_family", "_prototype_anchor",
           "_teach_agent", "_sub", "_native", "_stroke_quantize_live", "_quantize",
           "_invariant_points", "_find_stroke_node", "_existing_names"]
