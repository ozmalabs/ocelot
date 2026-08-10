"""ink_decode — S2 of scratchpad/HANDWRITING_DESIGN.md: SEGMENTATION-BY-RECOGNITION for ink,
the handwriting instance of the speech precedent's dynamic-quantization loop (commit
9f1fc077, scripts/jabberwock_dynamic_quantization.py): word-SHAPES decode the stream and
boundaries EMERGE from the decode, never a pre-cut. Here stroke-SHAPES (the held codebook,
domains/stroke_codebook.py) decode a pen path.

ARCHITECTURE (CLAUDE.md): `ingest_ink`/`decode_ink` are a WORLD ADAPTER. Every choice — which
shape a span is, whether a span is on the best path, whether an OOV observation mints or
recognizes, whether a pool of Transforms implies a WriterStyle — is a HELD TERM (ShapeDecode /
TransformDecode / the seeded `vit_step`/`vit_backtrace` / `sd_*` / `wd_infer_writer` rules).
Python here only: (1) resamples the raw pen path into candidate-span cut points (mechanical
arc-length geometry — the SAME operation `glyph_motor_world._resample_arclen` already
performs); (2) stamps `Hyp`/`LatEdge` lattice nodes per candidate span (mechanical graph
construction, mirroring `scripts/jabberwock_dynamic_quantization.py::viterbi_partition`
structurally); (3) ticks `lat.active_pos` / calls `run_rules()` (the reflex loop, CLAUDE.md's
own canonical example); (4) reads the resulting `on_path` nodes back (mechanical query); (5) a
FIXED FORMULA turning a Term's own numeric output into a lattice emission value (`emit =
covered_count if full else covered_count - segments`, the exact same kind of arithmetic
`jabberwock_dynamic_quantization.py`'s own `emit = -d*dur` already does — not a decision over
graph state, a translation of an already-computed score). `if minted: grow_stroke_quantum(...)`
gates a mechanical INSTALL on a decision the seeded `sd_mint_quantum` rule already made,
exactly like `teach()`'s own `if saved:` idiom — never a re-decision.

SCHEMA NOTE (reconciled with the parallel Rust work, 2026-07-02): an earlier pass of this
module found — empirically, via direct `TransformDecode` `evaluate()` calls, no
`StrokeQuantize` needed — that the design's literal 4-relation pose schema
(`["pose_x",x_q]`/`["pose_y",y_q]`/`["pose_o",orient_q]`/`["pose_s",scale_q]`, each arity 2)
did NOT compose correctly: `TransformDecode`'s per-dimension consistency check aligned
relations by a GLOBAL canonical sort and required one uniform delta across every aligned pair
sharing a given raw SLOT INDEX, regardless of predicate — since `seg` (arity 5) and every
`pose_*` singleton (arity 2) all touch slot index 1, a rotation confined to `pose_o` collided
with the `delta==0` constraint every OTHER slot-1-bearing relation contributed. THE ROOT FIX
IS LANDING IN RUST (not worked around here): `TransformDecode` pools dimensions per
`(predicate, slot)` instead of raw slot index, so the design's literal 4-relation schema
composes correctly once that fix is live — this module is written AGAINST THE LITERAL DESIGN
SCHEMA accordingly. `ORIENT_PRED`/`ORIENT_DIM` and `SCALE_PRED`/`SCALE_DIM` below name the
`(predicate, slot)` pair this module reads off a `TransformDecode` result's `transforms` list;
a `transforms` entry MAY additionally carry a `pred` key on a multi-predicate signature (the
fixed Term's own disambiguator) — `_extract_dim_delta` reads it mechanically when present and
falls back to `dim`-only matching otherwise (still correct for a single-predicate signature,
and harmless before the fix lands, since nothing currently returns `explained=True` for our
schema to read a `pred` off in the first place). UPDATE (later the same session): BOTH pieces
landed — `StrokeQuantize` (with `canonical_pose`) and `TransformDecode`'s `(predicate, slot)`
pooling fix — and every gate in `tests/test_ink_decode_migrated.py` (including the
pose-transform-dependent ones) passes live against them. `_stroke_quantize_live()` (probes
`StrokeQuantize`'s `canonical_pose` option specifically) and
`_transformdecode_pools_by_predicate()` in `tests/test_ink_decode_migrated.py` (probes the
`TransformDecode` pooling fix independently) are kept as-is — cheap per-test readiness probes,
not module-skip gates — so this file degrades gracefully if either is ever rolled back or run
against an older wheel.

Legacy note: `trace_segmenter`/`canonical_parse` are superseded in ROLE (recognition boundary-
finding) by this lattice decode; they are left untouched (their callers are unrelated
scripts).

REFINEMENT RUNG (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "REFINEMENT RUNG" section —
the Omniglot gate's residual, commit 26f74039: exact-match-only recognition at ONE grain gave
81% held-out OOV / one-shot at chance despite LEARN saturation PASS). `decode_ink`'s per-span
emission now tries TWO grains before falling to OOV (`_choose_span_tier`): FINE first
(unchanged), then COARSE (`_score_span_coarse`, against the companion `ShapeSignatureCoarse`
codebook `stroke_codebook.grow_stroke_quantum` now installs alongside every fine entry —
"tolerance = COARSENESS, not fuzzy matching"). When BOTH grains fail for an on-path span, ONE
`DtwTo` near-miss look (`_dtw_fallback`, against stored invariant-normalized PROTOTYPEs) gets
a last look before OOV/mint (a held `Argmin` picks the nearest candidate, a held `Lt` against
a DATA threshold — `agent.dtw_near_threshold` — decides the verdict). A coarse or DtwTo
recognition additionally gets ONE refinement-rung look (`_refine_or_note`,
`seeds/ink_refinement.json`'s `ir_*` rules) that mints a PER-DIMENSION child quantum
(`refines_quantum` edge) when the fine mismatch is confined to turn-only / len-only / both —
the SAME `sd_mint_quantum` rule-decides/Python-installs pattern the pre-existing OOV path
already used. `decode_ink` now returns an additional `refined` list alongside
`{spans, recognized, oov, minted}`.

DISCRIMINATION (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "DISCRIMINATION" section — the
26df120c residual: OOV 0%/saturation PASS but one-shot 3.8% vs 5% chance, coarse multisets
can't carry 20-way discrimination). Two levers land here (the third, character composition,
lives in `domains/character_compose.py`): (b) POSE READ-OFF IN ALL TIERS — `_pose_read_goal`
splices the OBSERVED pose relations onto the CHOSEN parent's own stored `seg` before every
`_install_pose_transform` call (coarse/DtwTo tiers now get the SAME high transform-explanation
rate the fine tier always had — see that helper's docstring for why the raw signature alone
regressed it to ~7%); (a) REFINEMENT-TREE SIGNATURES — `_resolved_identity` prefers a
refinement CHILD's name (the deepest match a `RefinementObservation` rule already decided,
`_refine_or_note`) over the coarse FAMILY name for every `recognized` entry's `"name"` field —
downstream signature construction (character composition) then carries the finer identity;
`"family"` preserves the coarse parent for provenance.

RUN-4 LEVERS "LEVER 2" (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "RUN-4 LEVERS" section
— the c1b83669 residual: 33.8% composed one-shot, "more refinement rungs = more vocabulary").
GRAIN LADDER: `decode_ink`'s post-lattice second look now tries a THIRD grain, MID
(`_score_span_mid`, `stroke_codebook.MID_TURN_BINS`/`MID_LEN_BINS`, strictly between COARSE
and FINE), BEFORE falling to COARSE — Occam order, finest-net-that-still-exact-matches wins.
'Distinct-at-mid identities': two quanta whose COARSE buckets happen to collide are still
told apart at MID, one net finer than coarse alone could manage, without paying fine's
exact-match brittleness to jitter. `_refine_or_note`'s `tier` param (forwarded to
`grow_stroke_refinement_quantum`'s `refined_from_tier`) records which tier actually
recognized a span before refinement fired, purely for `stroke_codebook.grain_vocabulary_
report`'s PER-LEVEL vocabulary reporting — a mechanical bookkeeping addition, not a new
decision (the SAME `_choose_span_tier` presence-check dispatch, now three-way).

EAGER CHILD MINTING (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING"
section — the a6fe069b residual: composed one-shot capped at 33.8%, vocabulary capped at 5
top-level quanta because recognition-before-mint now stops almost every span at the FINE
tier). STEP 0 instrumented 400 real Omniglot strokes / 2595 fine-tier recognitions and found a
fine match is ALWAYS exact-signature equality (0 residuals against the parent's own stored
fine `seg`, `ShapeDecode`'s `covered_by` field is only ever non-None on full coverage) — no
already-carried variation exists AT the fine grain to key a child on; genuine, BOUNDED
variation only appeared one ladder step FINER (`stroke_codebook.SUBFINE_TURN_BINS`/
`SUBFINE_LEN_BINS`, a NEW rung below fine, "an entry NOT a base-grain change" — run 5 already
proved a finer BASE grain hurts matching). `decode_ink`'s fine branch now ALSO takes one
sub-fine look (`_eager_child_or_note`, a thin parameterization of `_refine_or_note` pointed at
the parent's stored `subfine_signature` instead of a fine-vs-coarse comparison, SAME
grain-agnostic `ir_*` rules, SAME `grow_stroke_refinement_quantum` install path) — a genuine
sub-fine mismatch mints a per-dimension CHILD into a DELIBERATELY SEPARATE node type
(`ShapeSignatureFineChild`, never `ShapeSignature`) so it can never compete in `_score_span`'s
primary fine-grain scan (see `stroke_codebook.grow_stroke_refinement_quantum`'s docstring for
why a distinct node TYPE, not merely a distinct `kind` attr, is the STRUCTURAL guarantee
"detail enters as children only, base grains untouched" needs). IDENTITY STAYS ADDITIVE: a
recognized entry's `"name"` (what `character_compose`'s `["strokeq", k, name]` uses) never
changes because of an eager child — the child surfaces only as an EXTRA `"fine_child"` field
`character_compose.py` turns into a SEPARATE `["strokeq_fine", k, child]` relation, gated by
its own `include_fine_children` flag (the ablation ordered by the design: "the gate logs BOTH
scores every episode").

BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (2026-07-03, scratchpad/HANDWRITING_DESIGN.md's
section of the same name, the jabberwock's own verdict d2cd7bed, "have the jabberwock decide
and execute it"): "the sd loop one level DOWN -- a stroke is itself an arrangement of
sub-stroke quanta." `decode_substrokes` runs the IDENTICAL segmentation-by-recognition
machinery (`_span_signature`/`_score_span`/`_lattice_partition`, all fully generic, reused
byte-for-byte) over a recognized/minted OUTER stroke span's OWN knot slice
(`knots[st:e]` — no new resampling, no fabricated detail) against a companion, deliberately
ARITY-DISTINCT `ShapeSignature{kind:"substroke"}` codebook, ONE grain only (coarse-per-run-5's-
law bins, `stroke_codebook.SUBSTROKE_*`) — no refinement ladder, no pose-Transform reading (see
that function's own docstring for why). `decode_ink`'s new `enable_substroke` flag (default
`False` — OPT-IN, the SAME "many existing unflagged callers" reasoning `include_rel2`
established: a substroke OOV mint bumps the SAME shared `agent.codebook_epoch` counter every
other grain's mint does, which would silently change every PRE-EXISTING caller's/test's own
epoch-bump-count assertions if it fired by default) attaches the result, when on, as an
ADDITIVE `entry["substroke_points"]` field on every recognized span (fine AND coarse/mid/dtw
tiers alike) — RAW `(points, name)` pairs only; the
RELATION-building one level up (`["subq", m, name]` / `["srel", m, ...]` + the additive
`["strokeq_sub", k, <arrangement key>]` on the CHARACTER signature) is `character_compose.py`'s
job, per file ownership — this module only decodes+mints, exactly mirroring the outer/inner
split `decode_ink`/`character_compose.compose_character_signature` already establish one grain
up."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import numpy as np
import substrate_rs as srs

from domains import glyph_motor_world as gmw
from domains import stroke_codebook as sc
from domains.reflective_faculty import _agent_root_node, induce_concern
from domains.stroke_codebook import (
    COARSE_LEN_BINS, COARSE_TURN_BINS, DEFAULT_CATEGORY, DEFAULT_CONTINUOUS_MINT_THRESHOLD,
    DEFAULT_DTW_THRESHOLD, DEFAULT_GRID, DEFAULT_LEN_BINS, DEFAULT_SCALE_BINS, DEFAULT_SEGMENTS,
    DEFAULT_TURN_BINS, MID_LEN_BINS, MID_TURN_BINS, SUBFINE_LEN_BINS, SUBFINE_TURN_BINS,
    SUBSTROKE_LEN_BINS, SUBSTROKE_SEGMENTS, SUBSTROKE_TURN_BINS,
    _native, _quantize, _sub, continuous_mint_or_note, grow_stroke_quantum,
)
from substrate.seed_loader import manifest_for

DEFAULT_MAX_KNOTS = 24
DEFAULT_MIN_SPAN = 2
DEFAULT_MAX_SPAN = 16
DEFAULT_WORD_PENALTY = -1.0
DEFAULT_OOV_SCORE = 0.0

# The two (predicate, slot) pairs domains/ink_decode.py and seeds/writer_dimensions.json ever
# read off a TransformDecode-with-pose result (see module docstring's schema note) — the
# design's literal `["pose_o", orient_q]` / `["pose_s", scale_q]` singleton relations, slot 1
# in each (arity 2: predicate + one value).
ORIENT_PRED, ORIENT_DIM = "pose_o", 1
SCALE_PRED, SCALE_DIM = "pose_s", 1


# --------------------------------------------------------------------------- #
#  INGEST — mechanical translation, no decision.
# --------------------------------------------------------------------------- #
def _knots(points, max_knots: int = DEFAULT_MAX_KNOTS) -> np.ndarray:
    """Arc-length resample the raw pen path to <= `max_knots` points — the candidate CUT
    POINTS `decode_ink` spans between (design: 'bounded, e.g. every resample knot, max ~24
    knots phase 1'). Reuses `glyph_motor_world._resample_arclen` (the SAME geometry the motor
    world's own synthesis/normalization already performs) rather than re-implementing it."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return pts.reshape(-1, 2) if pts.size else np.zeros((2, 2))
    n = max(2, min(max_knots, pts.shape[0]))
    return gmw._resample_arclen(pts, n)


def _writer_node(sub, writer_name: str) -> int:
    """Mechanical find-or-create-by-name — the same idiom `teach()`'s category manifests and
    `stroke_codebook`'s named-quantum dedup already use."""
    for n in sub.nodes("Writer"):
        if sub.node(n)["attrs"].get("name") == writer_name:
            return n
    return sub.add_node("Writer", {"name": writer_name})


def ingest_ink(agent, points, *, writer: Optional[str] = None,
               max_knots: int = DEFAULT_MAX_KNOTS, denoise: bool = False,
               denoise_kwargs: Optional[dict] = None) -> int:
    """INGEST: a raw pen path (`[[x,y], ...]`) -> an `Ink` node carrying its arc-length-
    resampled KNOTS. `writer` (optional) tags the ink with WHO wrote it (a `Writer` node,
    find-or-create) for S3's writer-dimension inference. Mechanical translation only.

    RUN 34 (`denoise=False` default — every pre-existing caller, including
    `scripts/jabberwock_omniglot_dynamic_quantization.decode_char_signature`, is byte-
    identical): when `True`, the raw points are reconstructed via `mouse_model.denoise_path`
    (the mouse observation model's inverse — removes pixel-lattice/event-rate quantization)
    BEFORE arc-length knotting, so every downstream span/signature/decode consumes the
    denoised path instead of the raw browser-sampled one. This is the DENOISE-FEATURES arm's
    own wiring point."""
    sub = _sub(agent)
    pts = points
    if denoise:
        from domains import mouse_model as mm
        pts = mm.denoise_path(np.asarray(points, dtype=float), **(denoise_kwargs or {})).tolist()
    knots = _knots(pts, max_knots)
    ink = sub.add_node("Ink", {
        "points": [[float(x), float(y)] for x, y in np.asarray(pts, dtype=float)],
        "knots": knots.tolist(), "n_knots": int(len(knots)),
    })
    if writer is not None:
        wn = _writer_node(sub, writer)
        sub.add_edge_unchecked(wn, "writes", ink)
    return ink


# --------------------------------------------------------------------------- #
#  PER-SPAN QUANTIZATION + EMISSION (held Terms only).
# --------------------------------------------------------------------------- #
def _span_signature(native, knots, st: int, e: int, *, segments, turn_bins, len_bins, grid,
                     scale_bins, invariant_only: bool,
                     turn_edges: Optional[list] = None, len_edges: Optional[list] = None,
                     emit_residual: bool = False) -> dict:
    # EXCLUSIVE of `e` (knots[st:e], not st:e+1) -- matches
    # scripts/jabberwock_dynamic_quantization.py's own `region[st:e]` span convention
    # exactly, so adjacent chained spans (dst.start==src.end in `_lattice_partition`)
    # tile the knot sequence with NO overlap and NO gap (an off-by-one INCLUSIVE slice
    # would double-count the boundary knot between every pair of chained spans).
    # RUN 32 -- ADAPTIVE EDGES (optional, default None -- byte-identical uniform behaviour
    # for every pre-existing caller): threaded straight through to `stroke_codebook._quantize`.
    pts = knots[st:e]
    return _quantize(native, pts, segments=segments, turn_bins=turn_bins, len_bins=len_bins,
                      grid=grid, scale_bins=scale_bins, invariant_only=invariant_only,
                      turn_edges=turn_edges, len_edges=len_edges, emit_residual=emit_residual)


def _signature_key(sig) -> str:
    """A STABLE, content-derived key for an invariant signature (design: OOV mint 'mints
    once — not per span, key the observation'). `induce_concern` mints a fresh
    `CapabilityAxis` for every `Observation` node regardless of repeats (that dedup is out
    of this module's scope — it belongs to the pre-existing shape_decode_loop ladder), but
    naming the NEW stroke quantum after the SIGNATURE'S OWN CONTENT (not the fresh axis id)
    means `grow_stroke_quantum`'s existing by-name idempotency guard correctly collapses
    repeats of the SAME (quantized) novel shape into ONE codebook install — the same kind
    of content-keyed dedup `teach()` already does for taught items."""
    return hashlib.sha1(json.dumps([list(rel) for rel in sig], sort_keys=True).encode()).hexdigest()[:12]


def _score_span(native, sig) -> tuple[int, Optional[str]]:
    """The LADDER's verdict for one span, via ONE held `ShapeDecode` evaluate per field
    (Occam: `beam=1/max_steps=1/cand_k=1` — term.rs's own 'the old greedy composer', a
    SINGLE best-fitting codebook stroke, never a spurious cross-stroke composite plan).
    Returns `(covered_count, covered_by)` — `covered_by` is only meaningful when
    `covered_count == segments` (a full, exact invariant match)."""
    goal = {"type": "Lit", "value": sig}
    base = {"goal": goal, "beam": 1, "max_steps": 1, "cand_k": 1, "wild_objects": False,
            "type": "ShapeDecode"}
    count = native.evaluate({**base, "field": "covered_count"}, {})
    name = native.evaluate({**base, "field": "covered_by"}, {})
    return int(count or 0), name


def _choose_span_tier(fine_count: int, fine_name: Optional[str], coarse_count: int,
                      coarse_name: Optional[str], mid_count: int = 0,
                      mid_name: Optional[str] = None) -> tuple[str, Optional[str], int]:
    """REFINEMENT RUNG item 2's tier dispatch, extended by RUN-4 LEVERS "LEVER 2" (GRAIN
    LADDER): Occam order, an exact FINE match always wins, then MID (the ladder's new
    in-between net — 'distinct-at-mid identities': two quanta whose COARSE buckets collide
    still resolve correctly one net finer), then COARSE. `mid_count`/`mid_name` are trailing
    OPTIONAL kwargs (default `0`/`None`) precisely so every PRE-EXISTING 4-positional-arg call
    site (this function's own committed callers/tests) keeps behaving byte-identically —
    fine-then-coarse, mid simply never in the running. A presence check on THREE values a held
    `ShapeDecode` Term already computed (`_score_span`/`_score_span_mid`/`_score_span_coarse`)
    — not a ranking/argmax, the SAME kind of branch this module's original `if name is None`
    OOV/recognized dispatch always was."""
    if fine_name is not None:
        return "fine", fine_name, fine_count
    if mid_name is not None:
        return "mid", mid_name, mid_count
    if coarse_name is not None:
        return "coarse", coarse_name, coarse_count
    return "oov", None, 0


def _score_span_coarse(native, sig) -> tuple[int, Optional[str]]:
    """REFINEMENT RUNG item 2's COARSE-grain twin of `_score_span` — the SAME ONE-held-
    ShapeDecode-per-field Occam pattern, pointed at the companion `ShapeSignatureCoarse`
    codebook (`stroke_codebook.grow_stroke_quantum`'s coarse-grain installation,
    `codebook_type` param) instead of the default `ShapeSignature` codebook. 'Tolerance =
    COARSENESS, not fuzzy matching': a full COARSE match IS the principled near-miss band, by
    construction — jitter that would break an exact FINE match vanishes at this grain."""
    goal = {"type": "Lit", "value": sig}
    base = {"goal": goal, "beam": 1, "max_steps": 1, "cand_k": 1, "wild_objects": False,
            "codebook_type": "ShapeSignatureCoarse", "type": "ShapeDecode"}
    count = native.evaluate({**base, "field": "covered_count"}, {})
    name = native.evaluate({**base, "field": "covered_by"}, {})
    return int(count or 0), name


def _score_span_mid(native, sig) -> tuple[int, Optional[str]]:
    """RUN-4 LEVERS "LEVER 2" (GRAIN LADDER)'s MID-grain twin of `_score_span_coarse` — the
    SAME ONE-held-ShapeDecode-per-field Occam pattern, pointed at the companion
    `ShapeSignatureMid` codebook (`stroke_codebook.grow_stroke_quantum`'s mid-grain
    installation) instead of `ShapeSignatureCoarse`/`ShapeSignature`. Tried BETWEEN fine and
    coarse (`_choose_span_tier`'s Occam order): finer than coarse (so two quanta that collide
    at the coarse grain can still be told apart), coarser than fine (so it still folds jitter
    that would break an exact fine match)."""
    goal = {"type": "Lit", "value": sig}
    base = {"goal": goal, "beam": 1, "max_steps": 1, "cand_k": 1, "wild_objects": False,
            "codebook_type": "ShapeSignatureMid", "type": "ShapeDecode"}
    count = native.evaluate({**base, "field": "covered_count"}, {})
    name = native.evaluate({**base, "field": "covered_by"}, {})
    return int(count or 0), name


# --------------------------------------------------------------------------- #
#  LATTICE DECODE — Hyp/LatEdge + vit_step/vit_backtrace (seeds/viterbi_decode.json,
#  UNCHANGED). Structure mirrors scripts/jabberwock_dynamic_quantization.py's own
#  `viterbi_partition` (the speech precedent) on a FRESH, throwaway substrate (freed after —
#  the same memory discipline that precedent's module docstring names).
# --------------------------------------------------------------------------- #
def _lattice_partition(spans, L: int, *, word_penalty: float,
                        oov_score: float) -> list[tuple[int, int, Optional[str]]]:
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    s._inner.load_seed_manifest(manifest_for("viterbi_decode"), ag)
    lat = s.add_node("Lattice", {})
    s.set_attr(lat, "lm_weight", 1.0)
    hyp_by_end: dict[int, list[int]] = {}
    info: dict[int, tuple[int, int, Optional[str]]] = {}
    for (st, e, count, name) in spans:
        # FIXED FORMULA (mechanical — mirrors jabberwock_dynamic_quantization.py's own
        # `emit = -d*dur`): a full match scores its raw covered_count (segments, positive) —
        # `name` is only non-None when ShapeDecode already reports full coverage (see
        # `_score_span`'s doc), so a genuine partial/non-match never gets a "real" hyp at
        # all here (it would be indistinguishable from — and strictly worse than — the OOV
        # filler at its default 0.0, so only the filler is added for those spans).
        candidates = ((name, float(count)),) if name is not None else ()
        for (sym_name, emit) in (*candidates, (None, float(oov_score))):
            h = s.add_node("Hyp", {})
            s.set_attr(h, "pos", float(e))
            s.set_attr(h, "sym", 1.0 if sym_name is not None else -1.0)
            s.set_attr(h, "emission", float(emit))
            s.set_attr(h, "seg_start", float(st))
            for k in ("scored", "vscore", "best_in", "on_path"):
                s.set_attr(h, k, 0.0)
            s.add_edge_unchecked(h, "in_lattice", lat)
            hyp_by_end.setdefault(e, []).append(h)
            info[h] = (st, e, sym_name)
    for h, (st, e, sym_name) in info.items():
        if st == 0:
            continue
        for ph in hyp_by_end.get(st, []):
            ed = s.add_node("LatEdge", {})
            s.set_attr(ed, "trans_logp", float(word_penalty))
            s.add_edge_unchecked(ed, "src", ph)
            s.add_edge_unchecked(ed, "dst", h)
    for p in range(0, L + 1):                                  # FORWARD: tick active_pos left->right
        s.set_attr(lat, "active_pos", float(p))
        s._inner.run_rules(400000)
    # The winning terminal Hyp (pos==L, max vscore) — Argmax over the Hyp NODE itself (not
    # its vscore value) so the host can seed on_path=1 on it for the backtrace below.
    winner_term = {
        "type": "Argmax",
        "source": {"type": "NodesWhere", "node_type": "Hyp", "attr_key": "pos",
                   "value": {"type": "Lit", "value": float(L)}},
        "var_name": "h", "value": {"type": "Attr", "node": {"type": "Var", "name": "h"}, "key": "vscore"},
        "default": None,
    }
    term_node = s._inner.evaluate(winner_term, {})
    if term_node is None:
        return []
    s.set_attr(term_node, "on_path", 1.0)
    s._inner.run_rules(400000)                                  # BACKTRACE (graph-native)
    segs = [(st, e, sym_name) for h, (st, e, sym_name) in info.items()
            if s.node(h)["attrs"].get("on_path") == 1.0]
    segs.sort(key=lambda x: x[1])
    return segs


# --------------------------------------------------------------------------- #
#  POSE READ-OFF — one direct TransformDecode evaluate per recognized on-path span.
# --------------------------------------------------------------------------- #
def _extract_dim_delta(transforms: list, dim: int, pred: Optional[str] = None) -> float:
    """Mechanical projection (a fixed lookup, not a decision about MEANING) of one
    `(predicate, slot)` pair's delta out of a TransformDecode result's own `transforms` list
    (`[{dim,kind,delta[,pred]}, ...]`) — the smallest graph token the seeded `wd_infer_writer`
    rule needs (CLAUDE.md's own 'thin I/O-boundary classifier' allowance: converting an opaque
    Term result into the smallest queryable attr, no Rust primitive does this projection). When
    an entry carries a `pred` key (the fixed Term's multi-predicate disambiguator — see module
    docstring), matching requires BOTH `pred` and `dim`; entries without a `pred` key match on
    `dim` alone (graceful pre-fix / single-predicate fallback). Defaults to 0.0 when absent (no
    delta at that slot — either genuinely zero, or unread; callers gate on
    `explained`/`identity` before trusting this)."""
    for t in transforms or []:
        if not isinstance(t, dict) or t.get("dim") != dim:
            continue
        if "pred" in t and pred is not None and t.get("pred") != pred:
            continue
        d = t.get("delta")
        if isinstance(d, (int, float)):
            return float(d)
    return 0.0


def _read_pose_transform(native, full_sig) -> dict:
    """ONE direct `TransformDecode` evaluate against the codebook (default
    `codebook_type="ShapeSignature"` — the SAME `kind="stroke"` entries `_score_span` scans,
    now holding the FULL canonical-pose signature per `stroke_codebook.py`'s codebook
    convention) — pose deltas read OFF the decode, never searched. `max_dims=4` (the four
    pose dimensions: `pose_x`/`pose_y`/`pose_o`/`pose_s`)."""
    return native.evaluate({
        "type": "TransformDecode",
        "goal": {"type": "Lit", "value": full_sig},
        "max_dims": 4,
    }, {})


def _pose_read_goal(sub, chosen_name: Optional[str], full_sig: list) -> list:
    """DISCRIMINATION item (b) — 'pose read-off in ALL tiers': splice the OBSERVED pose
    relations onto the CHOSEN PARENT's own stored (canonical, fine-grain) `seg` relations
    before handing the signature to `_read_pose_transform`. `chosen_name` is a decision
    ALREADY MADE by the ladder (the fine exact match, or the coarse/DtwTo near-miss verdict —
    `_choose_span_tier`/`_dtw_fallback`'s own return value); this is a mechanical substitution
    of already-decided values, not a new decision (the same 'smallest graph token' translation
    CLAUDE.md's thin-I/O-boundary allowance names).

    WHY: for a FINE-tier recognition the observed span's fine `seg` relations already exact-
    match `chosen_name`'s stored `seg` relations BY CONSTRUCTION (that is what 'fine' means) —
    this substitution is then a no-op, byte-identical to the pre-existing behaviour. For a
    COARSE/DtwTo-tier recognition the observed fine `seg` DELIBERATELY does not exact-match
    (that mismatch is the refinement rung's own, separately-tracked residual — see
    `_refine_or_note`) — asking `TransformDecode` to explain the RAW observed full signature
    against the whole codebook then sees delta on `seg` slots too, which is NOT a consistent
    single-dimension pose delta, so `explained` comes back `False` almost always (the
    DISCRIMINATION section's measured '100% -> 6.9%' regression). Pinning the goal's `seg` to
    the CHOSEN parent's own stored seg isolates the POSE reading from that unrelated seg
    mismatch, restoring the SAME high explain rate the fine tier always had — pose is read off
    the decode, never searched, exactly as before; only the INPUT signature handed to that one
    `TransformDecode` evaluate changes."""
    parent_node = sc._find_stroke_node(sub, chosen_name) if chosen_name else None
    if parent_node is None:
        return full_sig
    try:
        parent_sig = json.loads(sub.node(parent_node)["attrs"].get("signature") or "[]")
    except (TypeError, ValueError):
        return full_sig
    parent_seg = _fine_seg_relations(parent_sig)
    if not parent_seg:
        return full_sig
    # NOTE: `full_sig` may be a LIVE `native.evaluate(...)` result (Rust Tuples surface as
    # Python `tuple`s, not `list`s -- see `_fine_seg_relations`'s identical note) rather than
    # a JSON-round-tripped signature (always plain `list`s) -- accept both.
    observed_pose = [list(r) for r in full_sig
                     if isinstance(r, (list, tuple)) and r and r[0] != "seg"]
    return parent_seg + observed_pose


def _resolved_identity(chosen_name: Optional[str], refine_res: Optional[dict]) -> Optional[str]:
    """DISCRIMINATION item (a) — 'refinement-tree signatures': where the refinement rung
    matched (or just minted) a per-dimension CHILD quantum for this span (`refine_res['name']`
    set — `grow_stroke_refinement_quantum`'s content-keyed name, present whether this call
    minted it fresh or found it already held, see `_refine_or_note`'s docstring), downstream
    signatures (character composition) must use the CHILD id — the DEEPEST match, the
    stroke's identity resolved as far as the refinement tree goes — not merely the coarse
    FAMILY it was first recognized under. Where nothing deeper resolved (`refine_res` is
    `None`, or its status is `'exact_at_fine'` — the DtwTo/coarse near-miss happened to land
    exactly on the parent's own fine grain, nothing to refine), the coarse/fine parent's own
    `chosen_name` stands unchanged. A plain presence check on a value a rule (`ir_*`,
    `seeds/ink_refinement.json`) already decided — not a ranking."""
    if refine_res is not None and refine_res.get("name"):
        return refine_res["name"]
    return chosen_name


def _install_pose_transform(sub, native, stroke_node: int, writer_node: Optional[int],
                            chosen_name: Optional[str], full_sig) -> dict:
    """The Transform-node install shared by EVERY recognized tier (fine / coarse / dtw) —
    factored out of what was previously the fine-only branch of `decode_ink`'s post-decode
    loop so the refinement rung's new tiers get the SAME pose read-off for free. One direct
    `TransformDecode` evaluate (`_read_pose_transform`), never searched, against the
    tier-corrected goal (`_pose_read_goal`, DISCRIMINATION item (b)); the DIRECT
    `writer -wrote_transform-> transform` shortcut edge is DELIBERATELY a distinct edge type
    from `has_transform` (see module docstring's engine-gotcha note)."""
    goal_sig = _pose_read_goal(sub, chosen_name, full_sig)
    transform = _read_pose_transform(native, goal_sig)
    t_node = sub.add_node("Transform", {
        "dims": list(transform.get("dims") or []),
        "deltas": list(transform.get("deltas") or []),
        "transforms": list(transform.get("transforms") or []),
        "base": transform.get("base"),
        "identity": bool(transform.get("identity")),
        "explained": bool(transform.get("explained")),
        "orient_delta": _extract_dim_delta(transform.get("transforms"), ORIENT_DIM, ORIENT_PRED),
        "scale_delta": _extract_dim_delta(transform.get("transforms"), SCALE_DIM, SCALE_PRED),
        "source": "ink_pose_read",
    })
    sub.add_edge_unchecked(stroke_node, "has_transform", t_node)
    if writer_node is not None:
        sub.add_edge_unchecked(writer_node, "wrote_transform", t_node)
    return transform


# --------------------------------------------------------------------------- #
#  REFINEMENT RUNG (scratchpad/HANDWRITING_DESIGN.md's "REFINEMENT RUNG" section, the
#  Omniglot residual, commit 26f74039): a span recognized at the COARSE grain (or via the
#  DtwTo near-miss fallback below) whose FINE grain does not exact-match its family gets a
#  PER-DIMENSION refinement look from seeds/ink_refinement.json's `ir_*` rules — WHETHER and
#  WHICH dimension to mint a child for is the RULE's decision (mirrors sd_mint_quantum's
#  pattern exactly, seeds/shape_decode_loop.json); this module only computes the mechanical
#  FACTS the rule reads (`turn_all_match`/`len_all_match` — a fixed structural comparison of
#  two ALREADY-QUANTIZED relation-lists whose IDENTITY was already decided by a held Term
#  upstream, not a ranking) and installs whatever the rule decided
#  (`grow_stroke_refinement_quantum`), exactly like the pre-existing OOV path's own
#  `if res.get('minted'): grow_stroke_quantum(...)` idiom.
# --------------------------------------------------------------------------- #
_REFINE_STATUS_TO_DIM = {"refine_turn": "turn", "refine_len": "len", "refine_both": "both"}


def _ensure_ink_refinement(sub, native, ag_node) -> None:
    """Idempotently load the `ink_refinement` seed onto `sub`, guarded by a graph-resident
    `Seed{id}` node — the EXACT idempotency pattern
    `reflective_faculty._ensure_shape_decode_loop` uses, and for the same reason: a caller
    that boots via `boot_core()` without explicitly listing this seed (e.g.
    `scripts/jabberwock_omniglot_dynamic_quantization.py`'s own `boot()`, which predates it)
    must still get the `ir_*` rules the refinement look depends on — without them every
    `RefinementObservation` sits at status 'pending' forever and no child ever mints, which
    is EXACTLY what the FIRST refinement-rung Omniglot rerun showed on real ink (zero
    children minted). Mechanical seed I/O — admissible world-adapter work, not a decision."""
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "ink_refinement":
            return
    native.load_seed_manifest(manifest_for("ink_refinement"), ag_node)
    sub.add_node("Seed", {"id": "ink_refinement", "version": "1.0.0"})


def _fine_seg_relations(sig) -> list:
    # `sig` may be a LIVE `native.evaluate(...)` result (Rust Tuples surface as Python
    # `tuple`s) OR a JSON-round-tripped signature (`list`s) -- accept both, normalize to
    # `list` (this bug -- `isinstance(r, list)` silently dropping every relation of a live
    # signature, making `_refine_or_note` return `None` for EVERY real `decode_ink` call --
    # is exactly why the refinement rung never actually minted a child against real ink
    # before the DISCRIMINATION-lever pass that added this note).
    return [list(r) for r in sig if isinstance(r, (list, tuple)) and r and r[0] == "seg"]


def _refine_or_note(agent, sub, native, ag_node, stroke_node: int, parent_name: str,
                    span_full_sig, *, segments, turn_bins, len_bins, grid, scale_bins,
                    category, tier: Optional[str] = None,
                    parent_sig_key: str = "signature", parent_kind: str = "stroke",
                    parent_node_type: str = "ShapeSignature",
                    child_node_type: str = "ShapeSignature", child_kind: str = "stroke",
                    name_suffix: str = "ref", no_diff_status: str = "exact_at_fine",
                    refined_as_attr: str = "refined_as") -> Optional[dict]:
    """Push one `RefinementObservation`, tick, read the rule's verdict back, install if it
    decided to mint. Returns `None` when there is nothing comparable (no held parent, or an
    arity mismatch — different `segments` counts, never expected within one `decode_ink` call
    since `segments` is fixed for the whole decode, but guarded honestly regardless).

    `tier` (RUN-4 LEVERS "LEVER 2", optional, default `None` — every pre-existing call site
    keeps behaving identically): the tier (`"coarse"`/`"mid"`) that recognized this span
    BEFORE this refinement look — `_choose_span_tier`'s own already-decided value, forwarded
    mechanically to `grow_stroke_refinement_quantum`'s `refined_from_tier` bookkeeping so
    `grain_vocabulary_report` can report children PER LEVEL.

    EAGER CHILD MINTING (2026-07-02, optional kwargs, every default byte-identical to the
    pre-existing signature/behaviour): `parent_sig_key`/`parent_kind`/`parent_node_type`
    generalize WHICH of the parent's stored grains this call compares `span_full_sig` against
    (the coarse/mid/dtw refinement callers below still compare the span's FINE `seg` relations
    to the parent's stored fine `"signature"`, unchanged); the EAGER caller instead passes
    `parent_sig_key="subfine_signature"` to compare a SUB-FINE-quantized `span_full_sig`
    against the parent's stored sub-fine reference — the SAME turn_all_match/len_all_match
    facts, the SAME `seeds/ink_refinement.json` `ir_*` rules (grain-agnostic: they only ever
    read the two booleans this function computes, never which grain produced them), just one
    ladder step finer. `child_node_type`/`child_kind` (EAGER caller:
    `"ShapeSignatureFineChild"`/`"stroke_fine_child"`) route the INSTALL to a DELIBERATELY
    separate node type so an eager child never competes in `_score_span`'s primary fine-grain
    scan (see `stroke_codebook.grow_stroke_refinement_quantum`'s docstring for why this must be
    a distinct node TYPE, not merely a distinct `kind` attr). `name_suffix` keeps eager child
    names visually distinct (`__eager_` vs `__ref_`) for anyone reading the graph.
    `no_diff_status` lets the eager caller report `"exact_at_subfine"` instead of the
    fine-grain wording `"exact_at_fine"` when there is nothing to refine (a plain string label,
    no behaviour change)."""
    _ensure_ink_refinement(sub, native, ag_node)
    parent_node = sc._find_stroke_node(sub, parent_name, kind=parent_kind,
                                       node_type=parent_node_type)
    if parent_node is None:
        return None
    try:
        parent_sig = json.loads(sub.node(parent_node)["attrs"].get(parent_sig_key) or "[]")
    except (TypeError, ValueError):
        return None
    span_seg = _fine_seg_relations(span_full_sig)
    parent_seg = _fine_seg_relations(parent_sig)
    if not span_seg or len(span_seg) != len(parent_seg):
        return None

    turn_all_match = all(a[2] == b[2] for a, b in zip(span_seg, parent_seg))
    len_all_match = all(a[3] == b[3] for a, b in zip(span_seg, parent_seg))
    if turn_all_match and len_all_match:
        # The span turned out identical to its parent's stored grain after all (e.g. a DtwTo
        # near-miss that happens to land exactly on the codebook prototype, or a fine-tier
        # recognition whose sub-fine grain also happens to reproduce the parent exactly) —
        # nothing to refine.
        return {"status": no_diff_status, "minted": False}

    obs = sub.add_node("RefinementObservation", {
        "parent": parent_name, "turn_all_match": bool(turn_all_match),
        "len_all_match": bool(len_all_match), "status": "pending",
    })
    sub.add_edge_unchecked(stroke_node, "refinement_observation", obs)
    if ag_node is not None:
        sub.add_edge_unchecked(ag_node, "refines", obs)
    native.run_rules()

    status = sub.node(obs)["attrs"].get("status")
    refined_dim = _REFINE_STATUS_TO_DIM.get(status)
    if refined_dim is None:
        return {"status": status, "minted": False}

    sig_key = _signature_key(span_full_sig)
    child_name = f"{parent_name}__{name_suffix}_{refined_dim}_{sig_key}"
    grow_res = sc.grow_stroke_refinement_quantum(
        agent, child_name, parent_name, refined_dim, span_full_sig,
        segments=segments, turn_bins=turn_bins, len_bins=len_bins, grid=grid,
        scale_bins=scale_bins, category=category, refined_from_tier=tier,
        node_type=child_node_type, kind=child_kind,
        parent_node_type=parent_node_type, parent_kind=parent_kind)
    if grow_res.get("grown"):
        sub.set_attr(stroke_node, refined_as_attr, child_name)
    return {"status": status, "minted": bool(grow_res.get("grown")), "name": child_name,
            "grow": grow_res}


# --------------------------------------------------------------------------- #
#  EAGER CHILD MINTING (scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING" section,
#  2026-07-02 — the a6fe069b residual): vocabulary capped at 5 top-level quanta because
#  recognition-before-mint now stops nearly every span at the FINE tier ("misses have
#  stopped") — the coarse/mid/dtw-triggered `_refine_or_note` calls above almost never fire
#  any more. STEP 0 (instrumented against 400 real Omniglot strokes / 2595 fine-tier
#  recognitions, see stroke_codebook.py's SUBFINE_TURN_BINS/SUBFINE_LEN_BINS comment): a
#  FINE-tier recognition is ALWAYS exact-signature equality (0/2595 residuals against the
#  parent's own stored fine `seg` — `ShapeDecode`'s `covered_by` field is only ever non-None
#  on full coverage, `runners/dsl/src/shape_decode.rs`), so there is NO already-carried
#  variation to key a child on AT the fine grain itself — genuine, BOUNDED variation only
#  showed up one ladder step FINER (the dominant real family's 2592 fine recognitions
#  resolved to just 6 distinct sub-fine signatures). `_eager_child_or_note` is a THIN
#  parameterization of `_refine_or_note` (NO NEW MACHINERY: same RefinementObservation node
#  type, same grain-agnostic `seeds/ink_refinement.json` `ir_*` rules, same
#  `grow_stroke_refinement_quantum` install path) pointed at the SUB-FINE grain instead of
#  the fine-vs-coarse comparison, installing into the SEPARATE `ShapeSignatureFineChild` node
#  type so the parent's own fine-grain recognition is structurally untouched.
# --------------------------------------------------------------------------- #
def _eager_child_or_note(agent, sub, native, ag_node, stroke_node: int, parent_name: str,
                         span_subfine_sig, *, segments, subfine_turn_bins, subfine_len_bins,
                         grid, scale_bins, category) -> Optional[dict]:
    """`span_subfine_sig` is the SAME span already re-quantized by the caller
    (`decode_ink`'s fine branch) at `subfine_turn_bins`/`subfine_len_bins` (one ladder step
    finer than whatever bins matched at the fine tier) — mechanical, no decision. Compares it
    to the PARENT's own stored `subfine_signature` attr (written by
    `stroke_codebook.grow_stroke_quantum` alongside fine/mid/coarse, 'ONE MOTION'); when the
    parent predates that attr (e.g. a hand-built test fixture, or a stale pre-eager-child seed
    entry), `parent_sig_key`'s lookup comes back empty and this returns `None` — an honest,
    non-crashing no-op, exactly like `_refine_or_note`'s own arity-mismatch guard."""
    return _refine_or_note(
        agent, sub, native, ag_node, stroke_node, parent_name, span_subfine_sig,
        segments=segments, turn_bins=subfine_turn_bins, len_bins=subfine_len_bins,
        grid=grid, scale_bins=scale_bins, category=category, tier="fine",
        parent_sig_key="subfine_signature", child_node_type="ShapeSignatureFineChild",
        child_kind="stroke_fine_child", name_suffix="eager",
        no_diff_status="exact_at_subfine", refined_as_attr="fine_child_as")


# --------------------------------------------------------------------------- #
#  RUN 23 -- CONTINUOUS-NOVELTY MINTING (the run-16 law, "continuous beats quantized," applied
#  to GROWTH: a span that RECOGNIZED at some tier but whose real-valued shape sits far from
#  that identity's own continuous prototype/family MINTS a peer quantum anyway). DEFAULT OFF
#  (`enable_continuous_mint=False` at every `decode_ink` call site) — every existing caller/
#  test behaves byte-identically with the flag untouched. The DECISION (nearest family member,
#  threshold comparison) is `stroke_codebook.continuous_mint_or_note`'s own held-Term
#  evaluation (`DtwTo`+`Argmin`+`Lt`, the SAME idiom `_dtw_fallback` already established); this
#  thin wrapper only threads `decode_ink`'s own already-decided `chosen_name` (whichever tier
#  recognized the span — fine/mid/coarse/DtwTo, ALL eligible, matching stays untouched) and the
#  span's own raw points through to it.
# --------------------------------------------------------------------------- #
def _continuous_mint_or_note(agent, chosen_name: Optional[str], points, *,
                             threshold: float, segments, turn_bins, len_bins, grid, scale_bins,
                             coarse_turn_bins, coarse_len_bins, mid_turn_bins, mid_len_bins,
                             subfine_turn_bins, subfine_len_bins, category) -> Optional[dict]:
    if chosen_name is None:
        return None
    return continuous_mint_or_note(
        agent, chosen_name, points, threshold=threshold, segments=segments,
        turn_bins=turn_bins, len_bins=len_bins, grid=grid, scale_bins=scale_bins,
        coarse_turn_bins=coarse_turn_bins, coarse_len_bins=coarse_len_bins,
        mid_turn_bins=mid_turn_bins, mid_len_bins=mid_len_bins,
        subfine_turn_bins=subfine_turn_bins, subfine_len_bins=subfine_len_bins,
        category=category)


# --------------------------------------------------------------------------- #
#  DTW NEAR-MISS FALLBACK (design item 4, emission tier 3): only ever called on the FEW
#  on-path spans that BOTH the fine and coarse tiers already failed to recognize (post-
#  lattice, never during the O(candidate-span) pre-lattice enumeration — DtwTo is real-valued
#  and comparatively expensive, so this stays off the hot path the coarse tier already
#  optimises). The VERDICT (near-quantum vs true OOV) is a held `Lt` Term evaluate against a
#  DATA threshold (`agent.dtw_near_threshold`, a gate can sweep it honestly) — never a Python
#  score comparison; the WINNER among candidates is a held `Argmin` evaluate (the SAME
#  `Argmin(Lit(pairs), IndexAt(Var,0))` idiom `scripts/jabberwock_omniglot_dynamic_quantization
#  .py`'s own `_argmax_pairs_term` precedent already established for Argmax).
# --------------------------------------------------------------------------- #
def _ensure_dtw_threshold(sub, ag_node: Optional[int], threshold: float) -> None:
    if ag_node is None:
        return
    if sub.node(ag_node)["attrs"].get("dtw_near_threshold") is None:
        sub.set_attr(ag_node, "dtw_near_threshold", float(threshold))


def _resolve_dtw_threshold(sub, ag_node: Optional[int], family_name: Optional[str]) -> float:
    """RUN 28 LEVER 1 (CFAR novelty calibration, `domains/novelty_calibration.py`): a
    mechanical graph-attr lookup CHAIN — never a decision — that picks WHICH threshold value
    `_dtw_fallback`'s own held `Lt` Term reads, preferring the MOST SPECIFIC calibrated data
    available: (1) a PER-FAMILY threshold (`dtw_reject_threshold`, set by
    `novelty_calibration.calibrate_dtw_thresholds` on the winning candidate's own top-level
    stroke-quantum node — the family had enough LEARN observations to support its own
    max-distance estimate); (2) the POOLED GLOBAL calibrated threshold
    (`dtw_near_threshold_calibrated` on the agent root — every data-starved family's own
    fallback); (3) the PRE-EXISTING engineering-guessed override (`dtw_near_threshold`,
    `_ensure_dtw_threshold`); (4) the hard `DEFAULT_DTW_THRESHOLD` constant. Every caller that
    never ran calibration sees BYTE-IDENTICAL behaviour to before this lever existed — neither
    new attr is ever set without an explicit `calibrate_dtw_thresholds` call, so this chain
    falls straight through to (3)/(4) exactly as `_dtw_fallback` always did. The ACCEPT/REJECT
    verdict itself stays exactly where it always was: a held `Lt` Term evaluate in
    `_dtw_fallback`, unchanged — this function only supplies one of that Term's two operands."""
    if family_name is not None:
        node = sc._find_stroke_node(sub, family_name)
        if node is not None:
            per_family = sub.node(node)["attrs"].get("dtw_reject_threshold")
            if per_family is not None:
                return float(per_family)
    if ag_node is not None:
        at = sub.node(ag_node)["attrs"]
        calibrated = at.get("dtw_near_threshold_calibrated")
        if calibrated is not None:
            return float(calibrated)
        legacy = at.get("dtw_near_threshold")
        if legacy is not None:
            return float(legacy)
    return DEFAULT_DTW_THRESHOLD


def _dtw_fallback(sub, native, ag_node: Optional[int],
                  span_proto: list) -> tuple[Optional[str], Optional[float], bool]:
    candidates = []
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") != "stroke":
            continue
        proto_json = at.get("prototype")
        if not proto_json:
            continue
        try:
            proto = json.loads(proto_json)
        except (TypeError, ValueError):
            continue
        candidates.append((at.get("name"), proto))
    if not candidates:
        return None, None, False

    dist_pairs = [
        (float(native.evaluate({"type": "DtwTo", "a": {"type": "Lit", "value": span_proto},
                                "b": {"type": "Lit", "value": proto}}, {}) or 0.0), name)
        for (name, proto) in candidates]
    winner = native.evaluate({
        "type": "Argmin", "source": {"type": "Lit", "value": dist_pairs}, "var_name": "c",
        "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                  "index": {"type": "Lit", "value": 0}},
        "default": None,
    }, {})
    if winner is None:
        return None, None, False
    min_dist, name = float(winner[0]), winner[1]

    threshold = _resolve_dtw_threshold(sub, ag_node, name)
    verdict = native.evaluate({"type": "Lt", "a": {"type": "Lit", "value": min_dist},
                               "b": {"type": "Lit", "value": threshold}}, {})
    return name, min_dist, bool(verdict)


# --------------------------------------------------------------------------- #
#  BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (scratchpad/HANDWRITING_DESIGN.md's section of
#  the same name, the jabberwock's verdict d2cd7bed, 2026-07-03): "the sd loop one level DOWN --
#  a stroke is itself an arrangement of sub-stroke quanta." `decode_substrokes` is the
#  WITHIN-stroke twin of `decode_ink`'s own outer segmentation-by-recognition loop, run over
#  the OUTER lattice's already-decided knot span for ONE recognized/minted stroke
#  (`knots[st:e]`, "the finer arc-length knots WITHIN the stroke" ARE these -- no new
#  resampling, no fabricated detail beyond what the outer decode already committed to as this
#  stroke's own boundary). MAXIMAL REUSE, per the design's own instruction: `_span_signature`/
#  `_score_span`/`_lattice_partition` are ALL fully generic over their `knots`/`spans`/`L`
#  arguments already -- reused HERE byte-identically, just fed the coarse `SUBSTROKE_*` bins
#  and a `kind="substroke"` OOV mint path (`stroke_codebook.grow_substroke_quantum`) instead of
#  the outer stroke-grain ones. NO refinement tiers (coarse/mid/dtw) -- ONE grain only ("coarse
#  bins per run-5's law": detail belongs in the ARRANGEMENT `character_compose.py` builds from
#  this function's own output, never in a finer sub-stroke base grain); NO pose-Transform
#  reading (sub-strokes get no `has_transform`/`wrote_transform` graph data of their own this
#  phase -- see this module's RUN-14 integration note in `decode_ink` for why AbS re-rank does
#  not need to change).
# --------------------------------------------------------------------------- #
def decode_substrokes(agent, span_knots, *, segments: int = SUBSTROKE_SEGMENTS,
                      turn_bins: int = SUBSTROKE_TURN_BINS, len_bins: int = SUBSTROKE_LEN_BINS,
                      grid: int = DEFAULT_GRID, scale_bins: int = DEFAULT_SCALE_BINS,
                      min_span: int = DEFAULT_MIN_SPAN, max_span: Optional[int] = None,
                      category: str = DEFAULT_CATEGORY,
                      ) -> dict[str, Any]:
    """The WITHIN-stroke inner lattice: `span_knots` is the OUTER stroke span's own knot
    slice (`decode_ink`'s `knots[st:e]`, already resampled/decided geometry -- reused as the
    inner decode's OWN candidate-cut-point sequence, exactly mirroring how `decode_ink`
    itself uses the ink's own knots). Runs the IDENTICAL segmentation-by-recognition
    machinery one level down:
      1. candidate inner sub-spans between EVERY pair of inner knot indices (cheap -- inner
         point counts are already small, bounded by the OUTER `max_span`, so this stays a
         tiny O(L^2) scan, no separate windowing needed);
      2. `_span_signature`/`_score_span` (BYTE-IDENTICAL functions, reused as-is) score each
         sub-span's invariant signature against the held `ShapeSignature{kind:"substroke"}`
         codebook (arity-distinct from every stroke-grain entry, see `stroke_codebook.
         SUBSTROKE_SEGMENTS`'s own comment for why this is safe without a companion node
         type — "NO NEW MACHINERY");
      3. `_lattice_partition` (BYTE-IDENTICAL function, reused as-is -- it is already fully
         generic over `spans`/`L`) decides the on-path partition via the SAME
         `vit_step`/`vit_backtrace` seed rules;
      4. an on-path OOV sub-span -> `induce_concern` -> `sd_mint_quantum` (the SAME sd loop
         the outer OOV path already uses, unchanged) -> `stroke_codebook.
         grow_substroke_quantum` (the mint DECISION is the rule's, this only installs it,
         exactly like `decode_ink`'s own outer `if res.get('minted'):
         grow_stroke_quantum(...)` idiom).

    Returns `{spans, recognized, minted, oov}` — `recognized`/`minted` entries are
    `{"start","end","name"}` in INNER draw order (mirrors `decode_ink`'s own top-level
    return shape one grain down); degenerate input (`< 2` inner knots) returns all-empty
    lists, never raises."""
    sub = _sub(agent)
    native = _native(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    knots = np.asarray(span_knots, dtype=float)
    L = len(knots)
    if L < 2:
        return {"spans": [], "recognized": [], "minted": [], "oov": []}
    eff_max_span = L if max_span is None else max_span

    spans = []
    for e in range(min_span, L + 1):
        for st in range(max(0, e - eff_max_span), e - min_span + 1):
            inv = _span_signature(native, knots, st, e, segments=segments, turn_bins=turn_bins,
                                   len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                                   invariant_only=True)
            count, name = _score_span(native, inv["signature"])
            spans.append((st, e, count, name))

    on_path = _lattice_partition(spans, L, word_penalty=DEFAULT_WORD_PENALTY,
                                  oov_score=DEFAULT_OOV_SCORE)

    recognized, minted, oov = [], [], []
    for (st, e, name) in on_path:
        if name is not None:
            recognized.append({"start": st, "end": e, "name": name})
            continue
        inv = _span_signature(native, knots, st, e, segments=segments, turn_bins=turn_bins,
                               len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                               invariant_only=True)
        sig_key = _signature_key(inv["signature"])
        res = induce_concern(agent, inv["signature"], name_hint=f"substroke_shape_{sig_key}")
        oov.append({"start": st, "end": e, "induce": res})
        if res.get("minted"):
            new_name = f"substroke_{sig_key}"
            points = knots[st:e].tolist()
            grow_res = sc.grow_substroke_quantum(agent, points, new_name, segments=segments,
                                                  turn_bins=turn_bins, len_bins=len_bins,
                                                  grid=grid, scale_bins=scale_bins,
                                                  category=category)
            minted.append({"start": st, "end": e, "name": new_name, "grow": grow_res})

    return {"spans": [(st, e, name) for (st, e, name) in on_path],
            "recognized": recognized, "minted": minted, "oov": oov}


def _substroke_points_from_result(span_knots, sub_res: dict) -> list[tuple[list, str]]:
    """Mechanical merge (mirrors `character_compose.decode_result_to_stroke_points` exactly,
    one grain down, kept LOCAL per this codebase's own small-duplicated-helper convention —
    see `domains/abs_read.py`'s module docstring for the precedent — rather than importing
    `character_compose` into `ink_decode`, which owns DECODE, not RELATION-composition):
    `decode_substrokes`'s own `{recognized, minted}` lists into a single INNER-draw-order
    `(points, name)` sequence, ordered by start position (the inner lattice's own already-
    decided order, not a ranking of this function's own)."""
    knots = np.asarray(span_knots, dtype=float)
    items = [(r["start"], r["end"], r["name"]) for r in sub_res.get("recognized", [])]
    items += [(m["start"], m["end"], m["name"]) for m in sub_res.get("minted", [])]
    items.sort(key=lambda x: x[0])
    return [(knots[st:e].tolist(), name) for (st, e, name) in items]


# --------------------------------------------------------------------------- #
#  DECODE — the full loop.
# --------------------------------------------------------------------------- #
def decode_ink(agent, ink: int, *, writer: Optional[str] = None,
               min_span: int = DEFAULT_MIN_SPAN, max_span: int = DEFAULT_MAX_SPAN,
               segments: int = DEFAULT_SEGMENTS, turn_bins: int = DEFAULT_TURN_BINS,
               len_bins: int = DEFAULT_LEN_BINS, grid: int = DEFAULT_GRID,
               scale_bins: int = DEFAULT_SCALE_BINS,
               coarse_turn_bins: int = COARSE_TURN_BINS, coarse_len_bins: int = COARSE_LEN_BINS,
               mid_turn_bins: int = MID_TURN_BINS, mid_len_bins: int = MID_LEN_BINS,
               subfine_turn_bins: int = SUBFINE_TURN_BINS,
               subfine_len_bins: int = SUBFINE_LEN_BINS,
               enable_eager_children: bool = True,
               enable_substroke: bool = False,
               substroke_segments: int = SUBSTROKE_SEGMENTS,
               substroke_turn_bins: int = SUBSTROKE_TURN_BINS,
               substroke_len_bins: int = SUBSTROKE_LEN_BINS,
               dtw_threshold: float = DEFAULT_DTW_THRESHOLD,
               enable_continuous_mint: bool = False,
               continuous_mint_threshold: float = DEFAULT_CONTINUOUS_MINT_THRESHOLD,
               word_penalty: float = DEFAULT_WORD_PENALTY,
               oov_score: float = DEFAULT_OOV_SCORE, category: str = DEFAULT_CATEGORY,
               turn_edges: Optional[list] = None, len_edges: Optional[list] = None,
               ) -> dict[str, Any]:
    """DECODE: segmentation-by-recognition over the held stroke codebook.

    RUN 23 -- CONTINUOUS-NOVELTY MINTING (`enable_continuous_mint`, default `False`, additive/
    opt-in — the SAME "many existing unflagged callers" discipline `include_rel2`/
    `enable_substroke` established): when on, EVERY recognized span (fine/mid/coarse/DtwTo
    tiers alike — matching itself is UNCHANGED) gets one extra look,
    `stroke_codebook.continuous_mint_or_note`, comparing the span's own real-valued shape to
    its recognized identity's continuous prototype family; a genuinely far observation mints a
    PEER top-level quantum (`continuous_mint_threshold`, DATA, swept honestly per run 23's own
    launch instructions — never tuned against accuracy). Recorded additively in the returned
    `"continuous"` list (mirrors `"refined"`'s own shape) — never changes `"name"`/`"tier"`/any
    existing field.

    1. Candidate spans between arc-length KNOTS; each span's INVARIANT signature scored at
       FINE grain only (`_score_span`, exact, Occam: a full fine match always wins) —
       'tolerance = COARSENESS, not fuzzy matching'. A fine match gives the lattice a REAL
       (non-OOV) candidate — the emission; the MID/COARSE grains (RUN-4 LEVERS "LEVER 2",
       GRAIN LADDER) are DELIBERATELY NOT in this pre-lattice loop (see its own comment for
       the documented combinatorial-hunting wall a coarser grain caused here empirically).
    2. A `Hyp`/`LatEdge` lattice (mirrors the speech precedent) ticked through
       `vit_step`/`vit_backtrace` (seeds/viterbi_decode.json, UNCHANGED) to the best
       PARTITION — on-path spans are the EMERGENT stroke boundaries.
    3. Post-decode, per on-path span:
       - FINE recognized: pose Transform read via `_install_pose_transform` (unchanged from
         before the refinement rung), PLUS (EAGER CHILD MINTING, `enable_eager_children`,
         default on) one SUB-FINE look — a fine match is, BY CONSTRUCTION, exact (`_score_span`
         only ever returns a name on full coverage), so there is nothing to refine AT the fine
         grain; quantizing the SAME span one ladder step finer (`subfine_turn_bins`/
         `subfine_len_bins`) and comparing to the parent's own stored sub-fine reference
         (`_eager_child_or_note`, the SAME grain-agnostic `ir_*` rules) exposes genuine,
         bounded within-tier variation instead (see stroke_codebook.py's
         SUBFINE_TURN_BINS comment for the empirical justification). A recognized entry's own
         `"name"` (the value `["strokeq", k, ...]` uses) is UNCHANGED either way — the eager
         child is recorded as an ADDITIONAL `"fine_child"` field only.
       - MID or COARSE recognized (fine failed; MID tried first — the GRAIN LADDER's
         Occam-ordered net, finer than coarse alone, "distinct-at-mid identities"): the SAME
         pose read, PLUS one refinement-rung look (`_refine_or_note`, design item 3) — a fine
         mismatch confined to ONE dimension mints a per-dimension CHILD quantum
         (`refines_quantum` edge, tagged `refined_from_tier`); a graph RULE
         (`seeds/ink_refinement.json`) decides whether/which dimension, this only installs
         what it decided.
       - No grain matched: ONE DtwTo near-miss look (design item 4, `_dtw_fallback`) —
         only on this handful of on-path OOV spans, never during the O(candidate-span)
         enumeration. A near-quantum verdict is treated exactly like a coarse recognition
         (pose read + refinement look); true OOV falls through to the EXISTING
         `induce_concern` -> `sd_mint_quantum` -> `grow_stroke_quantum` ladder, UNCHANGED.

    Returns `{spans, recognized, oov, minted, refined}` — every field a mechanical read-back
    of graph state this function itself just wrote.

    RUN 32 -- ADAPTIVE EDGES (`turn_edges`/`len_edges`, optional, default `None` — every
    pre-existing caller keeps byte-identical uniform-count behaviour): threaded through to the
    FOUR pre-lattice/post-lattice FINE-grain `_span_signature` calls ONLY (the pre-lattice
    emission loop, the OOV-branch fine invariant sig, the coarse/mid/dtw-recognized-branch full
    sig, and the fine-recognized-branch full sig) — NOT the MID/COARSE/SUBFINE grains, which
    stay on their existing uniform bins (near-miss tolerance bands, deliberately out of this
    lever's scope). A caller enabling this MUST also pass the SAME edges to whatever built the
    codebook (`stroke_codebook.grow_stroke_quantum`'s own `turn_edges`/`len_edges`) — otherwise
    query and codebook FINE signatures are quantized under different bins and fine-tier
    recognition never matches."""
    sub = _sub(agent)
    native = _native(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    _ensure_dtw_threshold(sub, ag_node, dtw_threshold)
    at = sub.node(ink)["attrs"]
    knots = np.asarray(at.get("knots") or [], dtype=float)
    # L = the KNOT COUNT (exclusive upper bound, matching _span_signature's exclusive
    # knots[st:e] slicing) -- NOT len(knots)-1. A valid span needs e<=L and st>=0 with
    # at least `min_span` knots between them.
    L = len(knots)
    if L < 2:
        return {"spans": [], "recognized": [], "oov": [], "minted": [], "refined": [],
                "continuous": []}

    # PRE-LATTICE: FINE-ONLY emission (UNCHANGED from before the refinement rung, byte-for-
    # byte) -- boundaries EMERGE from the fine grain exactly as they always did. The COARSE
    # tier is DELIBERATELY NOT in this loop: an earlier pass of the refinement rung offered
    # it here (per the design's literal 'span emission matches at the COARSE grain' phrasing)
    # and it was a genuine WALL, empirically, against real Omniglot ink -- COARSE quantization
    # creates large equivalence classes of raw geometry, and this loop's own combinatorial
    # freedom (every (st,e) window from min_span to max_span) lets the lattice search HUNT for
    # some sub-window of almost ANY stroke that happens to exact-match a held coarse family,
    # collapsing the live codebook to 3 degenerate "generic" entries and 0% test-time OOV /
    # chance-level one-shot accuracy on a real rerun (results/omniglot_gate_refinement_rerun
    # .log's FIRST attempt, kept as the diagnostic record). The FIX restores the coarse (and
    # DtwTo) tiers to a POST-LATTICE second look at already-decided on-path OOV spans only
    # (mirrors how the DtwTo tier was always scoped) -- no combinatorial windowing freedom
    # left to exploit, and boundary emergence is provably unaffected (identical to the
    # pre-refinement-rung fine-only lattice).
    spans = []
    for e in range(min_span, L + 1):
        for st in range(max(0, e - max_span), e - min_span + 1):
            inv = _span_signature(native, knots, st, e, segments=segments, turn_bins=turn_bins,
                                   len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                                   invariant_only=True, turn_edges=turn_edges, len_edges=len_edges)
            count, name = _score_span(native, inv["signature"])
            spans.append((st, e, count, name))

    on_path = _lattice_partition(spans, L, word_penalty=word_penalty, oov_score=oov_score)

    writer_node = _writer_node(sub, writer) if writer is not None else None
    recognized, oov, minted, refined, continuous = [], [], [], [], []
    for (st, e, name) in on_path:
        stroke_node = sub.add_node("Stroke", {"start": int(st), "end": int(e),
                                              "recognized_as": name})
        sub.add_edge_unchecked(ink, "has_span", stroke_node)

        if name is None:
            # POST-LATTICE second look (only ever a handful of on-path spans, never the
            # O(candidate-span) enumeration above): MID, then COARSE, then DtwTo, before
            # OOV/mint (RUN-4 LEVERS "LEVER 2" — GRAIN LADDER: MID is tried BEFORE coarse,
            # the Occam-ordered finer net).
            inv = _span_signature(native, knots, st, e, segments=segments, turn_bins=turn_bins,
                                   len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                                   invariant_only=True, turn_edges=turn_edges, len_edges=len_edges)
            mid_inv = _span_signature(native, knots, st, e, segments=segments,
                                       turn_bins=mid_turn_bins, len_bins=mid_len_bins,
                                       grid=grid, scale_bins=scale_bins, invariant_only=True)
            mid_count, mid_name = _score_span_mid(native, mid_inv["signature"])
            coarse_inv = _span_signature(native, knots, st, e, segments=segments,
                                          turn_bins=coarse_turn_bins, len_bins=coarse_len_bins,
                                          grid=grid, scale_bins=scale_bins, invariant_only=True)
            coarse_count, coarse_name = _score_span_coarse(native, coarse_inv["signature"])
            tier, chosen_name, _emit = _choose_span_tier(0, None, coarse_count, coarse_name,
                                                          mid_count, mid_name)

            dtw_dist = None
            if tier == "oov":
                proto = sc._invariant_points(knots[st:e].tolist())
                dtw_name, dtw_dist, dtw_near = _dtw_fallback(sub, native, ag_node, proto)
                if dtw_near:
                    tier, chosen_name = "dtw", dtw_name

            if tier != "oov":
                # A coarse or DtwTo near-miss recognition -- treated identically: pose read
                # + one refinement-rung look, never OOV/mint.
                sub.set_attr(stroke_node, "recognized_as", chosen_name)
                sub.set_attr(stroke_node, "tier", tier)
                if dtw_dist is not None:
                    sub.set_attr(stroke_node, "dtw_distance", dtw_dist)
                full = _span_signature(native, knots, st, e, segments=segments,
                                        turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                                        scale_bins=scale_bins, invariant_only=False,
                                        turn_edges=turn_edges, len_edges=len_edges)
                # DISCRIMINATION item (b): pose read-off IN THIS TIER TOO, tier-corrected
                # (_pose_read_goal splices the observed pose onto chosen_name's own stored
                # seg -- see that helper's docstring for why the raw full signature alone
                # regressed the explain rate here).
                transform = _install_pose_transform(sub, native, stroke_node, writer_node,
                                                    chosen_name, full["signature"])
                refine_res = _refine_or_note(
                    agent, sub, native, ag_node, stroke_node, chosen_name, full["signature"],
                    segments=segments, turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                    scale_bins=scale_bins, category=category, tier=tier)
                if refine_res is not None:
                    refined.append({"start": st, "end": e, "parent": chosen_name, **refine_res})
                # RUN 23 -- CONTINUOUS-NOVELTY MINTING: this span already recognized (coarse/
                # mid/DtwTo tier); ALSO compare its own real-valued shape to chosen_name's
                # continuous family (`decode_ink`'s own module docstring). Additive/opt-in.
                if enable_continuous_mint:
                    cont_res = _continuous_mint_or_note(
                        agent, chosen_name, knots[st:e].tolist(),
                        threshold=continuous_mint_threshold, segments=segments,
                        turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                        scale_bins=scale_bins, coarse_turn_bins=coarse_turn_bins,
                        coarse_len_bins=coarse_len_bins, mid_turn_bins=mid_turn_bins,
                        mid_len_bins=mid_len_bins, subfine_turn_bins=subfine_turn_bins,
                        subfine_len_bins=subfine_len_bins, category=category)
                    if cont_res is not None:
                        continuous.append({"start": st, "end": e, "parent": chosen_name,
                                           "tier": tier, **cont_res})
                # DISCRIMINATION item (a): the DEEPEST match (a refinement CHILD, when one
                # resolved) is the identity downstream signatures (character composition)
                # use -- chosen_name (the coarse/DtwTo FAMILY) stays available as "family"
                # for provenance.
                identity_name = _resolved_identity(chosen_name, refine_res)
                entry = {"start": st, "end": e, "name": identity_name, "family": chosen_name,
                         "tier": tier, "transform": transform}
                if refine_res is not None:
                    entry["refine"] = {"status": refine_res.get("status"),
                                       "minted": refine_res.get("minted")}
                if dtw_dist is not None:
                    entry["dtw_distance"] = dtw_dist
                # BRANCH A EXECUTION -- SUB-STROKE COMPOSITION: the WITHIN-stroke inner
                # lattice over this span's OWN knot slice, one level down (see
                # decode_substrokes's own docstring). Raw (points, name) pairs only --
                # relation-building (subq/srel + the strokeq_sub arrangement key) is
                # character_compose.py's job, per file ownership.
                if enable_substroke:
                    sub_res = decode_substrokes(
                        agent, knots[st:e], segments=substroke_segments,
                        turn_bins=substroke_turn_bins, len_bins=substroke_len_bins,
                        grid=grid, scale_bins=scale_bins, category=category)
                    entry["substroke_points"] = _substroke_points_from_result(
                        knots[st:e], sub_res)
                recognized.append(entry)
            else:
                sig_key = _signature_key(inv["signature"])
                res = induce_concern(agent, inv["signature"], name_hint=f"ink_shape_{sig_key}")
                oov.append({"start": st, "end": e, "induce": res})
                if res.get("minted"):
                    # Reading the mint straight off the graph (induce_concern already ran
                    # sd_mint_quantum) -- growing the codebook is a mechanical install, not a
                    # re-decision. Named after the SIGNATURE'S OWN CONTENT (see
                    # `_signature_key`), not the fresh axis id, so a repeat of the SAME
                    # (quantized) novel shape across several spans installs exactly once.
                    new_name = f"stroke_{sig_key}"
                    points = knots[st:e].tolist()
                    grow_res = grow_stroke_quantum(agent, points, new_name, segments=segments,
                                                    turn_bins=turn_bins, len_bins=len_bins,
                                                    grid=grid, scale_bins=scale_bins,
                                                    category=category, turn_edges=turn_edges,
                                                    len_edges=len_edges)
                    sub.set_attr(stroke_node, "minted_as", new_name)
                    minted.append({"start": st, "end": e, "name": new_name, "grow": grow_res})
        else:
            full = _span_signature(native, knots, st, e, segments=segments, turn_bins=turn_bins,
                                    len_bins=len_bins, grid=grid, scale_bins=scale_bins,
                                    invariant_only=False, turn_edges=turn_edges, len_edges=len_edges)
            transform = _install_pose_transform(sub, native, stroke_node, writer_node,
                                                name, full["signature"])
            sub.set_attr(stroke_node, "tier", "fine")
            entry = {"start": st, "end": e, "name": name, "transform": transform,
                     "tier": "fine"}
            # EAGER CHILD MINTING (2026-07-02): a fine match is EXACT by construction (nothing
            # to refine AT this grain, see decode_ink's own docstring) -- look one ladder step
            # FINER instead. `refined.append(...)` mirrors the coarse/mid/dtw branch's own
            # bookkeeping so callers scanning `refined` see every refinement attempt in one
            # place, tagged by which grain triggered it (`refine_res["status"]` starts with
            # "exact_at_subfine"/"refine_" here vs "exact_at_fine"/"refine_" there).
            if enable_eager_children:
                subfine_full = _span_signature(native, knots, st, e, segments=segments,
                                               turn_bins=subfine_turn_bins,
                                               len_bins=subfine_len_bins, grid=grid,
                                               scale_bins=scale_bins, invariant_only=False)
                eager_res = _eager_child_or_note(
                    agent, sub, native, ag_node, stroke_node, name, subfine_full["signature"],
                    segments=segments, subfine_turn_bins=subfine_turn_bins,
                    subfine_len_bins=subfine_len_bins, grid=grid, scale_bins=scale_bins,
                    category=category)
                if eager_res is not None:
                    refined.append({"start": st, "end": e, "parent": name, **eager_res})
                    if eager_res.get("name"):
                        entry["fine_child"] = eager_res["name"]
            # RUN 23 -- CONTINUOUS-NOVELTY MINTING: a FINE-tier match is EXACT at the fine
            # grain by construction, but that discrete equality can still hide real-valued
            # diversity (the run-19..22 wall: "14,675/14,676 share ONE identity") -- compare
            # this span's own shape to `name`'s continuous family exactly like the coarse/mid/
            # dtw branch above. Additive/opt-in.
            if enable_continuous_mint:
                cont_res = _continuous_mint_or_note(
                    agent, name, knots[st:e].tolist(), threshold=continuous_mint_threshold,
                    segments=segments, turn_bins=turn_bins, len_bins=len_bins, grid=grid,
                    scale_bins=scale_bins, coarse_turn_bins=coarse_turn_bins,
                    coarse_len_bins=coarse_len_bins, mid_turn_bins=mid_turn_bins,
                    mid_len_bins=mid_len_bins, subfine_turn_bins=subfine_turn_bins,
                    subfine_len_bins=subfine_len_bins, category=category)
                if cont_res is not None:
                    continuous.append({"start": st, "end": e, "parent": name, "tier": "fine",
                                       **cont_res})
            # BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (see decode_substrokes's own
            # docstring): the SAME within-stroke inner lattice, run here too so a FINE-tier
            # recognized span also composes -- the design's own mechanism doesn't distinguish
            # tiers for sub-stroke composition, only for the (unrelated) refinement ladder.
            if enable_substroke:
                sub_res = decode_substrokes(
                    agent, knots[st:e], segments=substroke_segments,
                    turn_bins=substroke_turn_bins, len_bins=substroke_len_bins,
                    grid=grid, scale_bins=scale_bins, category=category)
                entry["substroke_points"] = _substroke_points_from_result(knots[st:e], sub_res)
            recognized.append(entry)

    # TICK the main substrate (CLAUDE.md's own ChatWorld example: "hand off to the Rust
    # agent" after ingest) -- lets seeds/writer_dimensions.json's wd_infer_writer react to
    # the Transform/Writer graph data this call just wrote (pool >=3 agreeing
    # orient_deltas -> mint a WriterStyle), a reflex, not a re-decision here.
    native.run_rules()

    return {"spans": [(st, e, name) for (st, e, name) in on_path],
            "recognized": recognized, "oov": oov, "minted": minted, "refined": refined,
            "continuous": continuous}


__all__ = ["ingest_ink", "decode_ink", "ORIENT_PRED", "ORIENT_DIM", "SCALE_PRED", "SCALE_DIM",
           "DEFAULT_MAX_KNOTS", "DEFAULT_MIN_SPAN", "DEFAULT_MAX_SPAN",
           "DEFAULT_WORD_PENALTY", "DEFAULT_OOV_SCORE",
           "_score_span", "_score_span_coarse", "_score_span_mid", "_choose_span_tier",
           "_lattice_partition",
           "_signature_key", "_extract_dim_delta", "_span_signature", "_read_pose_transform",
           "_pose_read_goal", "_resolved_identity",
           "_install_pose_transform", "_refine_or_note", "_eager_child_or_note", "_dtw_fallback",
           "_ensure_dtw_threshold", "_resolve_dtw_threshold", "_ensure_ink_refinement",
           "_fine_seg_relations",
           "decode_substrokes", "_substroke_points_from_result",
           "_continuous_mint_or_note", "DEFAULT_CONTINUOUS_MINT_THRESHOLD"]
