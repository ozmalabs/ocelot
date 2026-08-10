"""homework_loop — the BABBLE SELF-IMPROVEMENT WITH PERIODIC GROUNDING loop (run-26 scope,
the ink/Omniglot arc's two live residuals: (1) reproducer segmentation instability across
re-render -- the reading model parses the agent's OWN renders differently than the
original; (2) proposal recall). The creator's frame, load-bearing:

  1. HOMEWORK IS ASSIGNED: the grounding/marking session emits residuals, and the next
     practice batch (worksheet) is DERIVED from those residuals -- never sampled freely.
  2. ECONOMICS: practice (render -> re-read, ~ms) is cheap and high-volume; grounding
     against real ink is dear and rare -- many babble reps per grounding contact.
  3. MARKING CONSUMES ONLY THE SURVIVING RESIDUAL: everything the round-trip check itself
     catches is self-corrected before a human/real-ink contact is spent on it; what reaches
     marking is only what self-consistency couldn't fix. The tracked metric (surviving-
     residual count per marking session) must FALL over cycles if the loop is learning.
  4. FRONTIER SCHEDULING (zone of proximal development): the worksheet is items with
     PARTIAL credit (0 < round_trip_score < 1) -- not the hardest (0/n, waits for a later,
     richer lesson) and not the solved (n/n, excluded, nothing left to learn there).

ARCHITECTURE (CLAUDE.md): this module is a WORLD ADAPTER over the EXISTING ink pipeline --
`domains/ink_decode.py` (parse), `domains/abs_read.py` (render, `StrokeRender`),
`domains/stroke_codebook.py` (codebook growth: `grow_stroke_quantum` /
`continuous_mint_or_note`). It adds NO new Rust, NO new rule engine, and NO new cognitive
machinery: every "decision" here is either (a) a HELD Term evaluate (Argmax/Argmin/And/Gt/
Lt/FilterList over an already-computed numeric score, the SAME idiom `abs_read.py`/
`character_compose.py` already establish) or (b) a call into an EXISTING, already-rule-gated
mint/refine function (`stroke_codebook.continuous_mint_or_note`, `ink_decode._refine_or_note`)
whose OWN seeded rule (`sd_*`/`ir_*`) makes the mint/no-mint call -- this module only
threads already-decided values and installs what a rule already decided, exactly like
`decode_ink`'s own `if res.get("minted"): grow_stroke_quantum(...)` idiom.

THE THREE-PHASE LOOP:

  `mark(agent, items)` -- THE GROUNDING/MARKING SESSION. For each real-ink item: parse it
  (`ink.decode_ink`), render the parse straight back (`abs_read`'s `StrokeRender`, via the
  SAME `ink_decode._pose_read_goal` splice `abs_read.abs_render_compare_term` already uses
  to build a render-ready goal signature), re-read the render (`ink.decode_ink` again), and
  SCORE round-trip agreement via a held comparator Term (`_residual_pairs_term`: held
  `FilterList(Not(Eq(...)))` over aligned-by-draw-order-index (orig_name, reread_name) pairs
  -- segmentation/count/identity agreement collapse into ONE positional comparison, since a
  dropped/shifted span already shows up as a positional mismatch). `MarkedItem.round_trip_score`
  is a FIXED FORMULA on that Term's own output (`(n - len(residual)) / n`, the exact same
  "arithmetic on an already-Term-computed count" idiom `ink_decode.py`'s own module
  docstring names for its lattice emission formula) -- never a second Python decision.

  `assign(marked)` -- THE WORKSHEET, derived ONLY from `marked`'s own residuals. The
  FRONTIER filter (0 < score < 1) is a held `And(Gt(score,0), Lt(score,max))` Term (never a
  bare Python threshold branch) over each item's ALREADY-COMPUTED score; ordering under a
  `capacity` cap is a REPEATED held `Argmax` over (residual_magnitude, index) pairs -- the
  SAME "remove an already-decided winner from a remaining list" idiom `abs_read.propose_top_k`
  already establishes, applied to residual magnitude instead of coverage.

  `babble(agent, worksheet)` -- THE SELF-PRACTICE PHASE. Touches NO real ink: a
  `WorksheetItem` carries only the PARSE (per-span render-ready `goal_sig` + `bbox` +
  `n_points`, the smallest graph-derived data `StrokeRender` needs), never the original raw
  points array (see the module's own `WorksheetItem` dataclass -- there is no `points` field
  to touch, an API-SHAPE guarantee, not a runtime check). Per rep: render the item's current
  parse with small per-span writer-dimension pose jitter (`pose_x`/`pose_y`/`pose_o`/`pose_s`
  bin deltas, mirroring `seeds/writer_dimensions.json`'s own pose-dimension vocabulary),
  re-read, and:
    (a) PARSE STABILITY RE-RANK -- tally, per span position, which identity the re-read
        returns across reps (held `Argmax` over (count, name) pairs decides the winner); a
        REPRODUCIBLE (majority) alternate identity is PERSISTED as a `stability_preferred_alt`
        attr on the codebook entry (graph data, never Python state) -- an honest, additive
        candidate-stability signal for a later consumer to read (this phase does not yet
        wire a reader for it; see the module's own closing note).
    (b) MINT AT INSTABILITY -- where the SAME (majority, by `_signature_key`) residual
        signature recurs at a span position across reps, `ink_decode._refine_or_note` (the
        EXISTING per-dimension refinement-mint machinery, UNCHANGED) is called once with
        that majority signature; the SEEDED `ir_*` rule decides whether/which dimension
        refines, this only installs what it decided -- exactly `decode_ink`'s own idiom, one
        level up (across REPS instead of within one decode).
    (c) VARIANT COVERAGE -- a jittered render that STILL decodes to the ORIGINAL identity
        is fed straight to `stroke_codebook.continuous_mint_or_note` (EXISTING, UNCHANGED):
        genuinely-far continuous geometry earns a peer prototype, widening proposal coverage
        for free, exactly as that function already does for a live decode.

  `cycle(agent, ground_items)` -- mark -> assign -> babble -> RE-MARK the same ground set.
  `CycleReport.surviving_residual_count` (items still `< 1.0` at re-mark) is the TEACHER-
  INFORMATION metric: what marking sees when the codebook already reflects this cycle's
  self-correction. Falling across repeated `cycle()` calls on the SAME ground set is the
  loop's own "is this working" signal (gate 4).

HONEST SCOPE NOTE: "parse candidates" in mechanism (a) are realized as the SET of identities
actually OBSERVED for a span position across babble's own re-render reps (original union
whatever an alternate jittered rendering re-decodes to) -- `ink_decode.decode_ink` itself
only ever exposes its OWN single Viterbi-best parse per call (no N-best beam surface), so a
literal "multiple candidates from ONE lattice decode" was not available without extending
`ink_decode.py`'s own lattice beyond a single best path, which this phase does not do (no
Rust changes, no ink_decode.py changes -- every existing gate stays green, verified). This
is a faithful, reasonably-scoped realization of "prefer the candidate most stable under
re-render" given the existing decode surface, not a literal beam-search reimplementation."""
from __future__ import annotations

import numpy as np
import substrate_rs as srs

from dataclasses import dataclass
from typing import Any, Optional

from domains import abs_read as ar
from domains import arrangement_codebook as ac
from domains import character_compose as cc
from domains import ink_decode as ink
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc
from domains.stroke_codebook import _native, _sub

DEFAULT_MAX_KNOTS = 24
DEFAULT_JITTER_BINS = 1          # +-1 quantized bin, the SAME small-perturbation scale
                                  # seeds/writer_dimensions.json's own pose vocabulary uses.
DEFAULT_MAX_SCORE = 1.0
_POSE_JITTER_PREDS = ("pose_x", "pose_y", "pose_o", "pose_s")


def _default_dk() -> dict:
    return {
        "min_span": ink.DEFAULT_MIN_SPAN, "max_span": ink.DEFAULT_MAX_SPAN,
        "segments": sc.DEFAULT_SEGMENTS, "turn_bins": sc.DEFAULT_TURN_BINS,
        "len_bins": sc.DEFAULT_LEN_BINS, "grid": sc.DEFAULT_GRID,
        "scale_bins": sc.DEFAULT_SCALE_BINS, "max_knots": DEFAULT_MAX_KNOTS,
        "category": sc.DEFAULT_CATEGORY,
        "continuous_mint_threshold": sc.DEFAULT_CONTINUOUS_MINT_THRESHOLD,
    }


class EvalLeakageError(RuntimeError):
    """Raised when a marked/babbled item's class is in the caller's declared eval set --
    the homework loop must never practice or grind on held-out data."""


# --------------------------------------------------------------------------- #
#  DATA -- the worksheet/log/report shapes. `WorksheetItem`/`Worksheet` carry a PARSE
#  (spans of render-ready data) and NEVER the item's raw ink points -- the structural
#  guarantee gate 8 audits (there is no `points`/`raw_points` field to remove).
# --------------------------------------------------------------------------- #
@dataclass
class SpanParse:
    """One recognized/minted span's render-ready parse -- no raw ink points. `goal_sig` is
    `ink_decode._pose_read_goal`'s own output (the chosen identity's stored seg + this span's
    OBSERVED pose relations) -- exactly what `abs_read._render_term` needs to reconstruct the
    span via `StrokeRender`.

    RUN 31 MECHANISM A (`rendered_as`) -- `None` for every existing caller / every span where
    no preference applied (byte-identical): set to the identity `goal_sig` was ACTUALLY built
    from when `_parse_from_decode`'s own held-Term substitution (`_preferred_render_name`)
    chose a persisted `stability_preferred_alt` over `name` itself -- an honest, additive
    engagement record riding on the span's own parse (see `count_preferred_renders`)."""
    start: int
    end: int
    name: str
    goal_sig: list
    bbox: tuple
    n_points: int
    rendered_as: Optional[str] = None


@dataclass
class MarkedItem:
    item_id: Any
    class_id: Any
    round_trip_score: float
    n_orig_spans: int
    n_reread_spans: int
    residual_spans: list           # [(index, orig_name_or_None, reread_name_or_None), ...]
    partial_credit: bool           # held frontier verdict: 0 < score < 1
    spans: list                    # [SpanParse, ...] -- the PARSE, no raw points
    dk: dict                       # decode-kwargs this item was marked under
    # CHARACTER-GRAIN (run 27) additions -- optional/defaulted, byte-compatible with every
    # existing stroke-grain caller (`mark`/`assign`/`babble`/`cycle` never set these, so they
    # stay `None`/`0` there): the three subscores `mark_characters`'s `overall` formula
    # averages, and the READING-pass mint count (this run's own headline measurement -- native
    # OOV minting fired while DECODING the item's own real strokes, before any render/babble).
    family_score: Optional[float] = None
    count_score: Optional[float] = None
    arrangement_score: Optional[float] = None
    n_mints_reading: int = 0
    # RUN 28 LEVER 2 (arrangement-grain sd loop, domains/arrangement_codebook.py) additions --
    # 0/None for every existing caller that never passes `enable_character_codebook=True`.
    # `n_mints_character_reading`: this item's own composed signature minted a NEW character-
    # grain quantum during THIS mark_characters call (0 or 1 -- one composed signature per
    # item, never per-span). `character_quantum`: the name of the quantum this item's own
    # arrangement recognized OR was just minted as (None when the lever is off).
    n_mints_character_reading: int = 0
    character_quantum: Optional[str] = None
    # RUN 29 (CONSUME) addition -- `None` for every caller that never passes
    # `use_stability_weights=True` on `mark_characters`/`cycle_characters` (byte-identical
    # default). When the flag IS on and the item's arrangement was scored against a HELD
    # quantum's persisted `relation_weights` (`arrangement_codebook.weighted_arrangement_score`),
    # `arrangement_score` above carries the WEIGHTED value and this field carries what the
    # PLAIN unweighted `_character_round_trip_score` formula would have reported for the SAME
    # (orig_sig, re_sig) pair -- reported side-by-side so the weighting effect is visible
    # separately from any real learning effect, never conflated into one number.
    arrangement_score_unweighted: Optional[float] = None
    # RUN 31 (GEOMETRY) additions -- 0 for every caller that never passes
    # `use_preferred_parse=True` / `tolerant_joins=True` to `mark`/`mark_characters`
    # (byte-identical default). Mechanism-engagement instruments (never scoring inputs
    # themselves): how many spans in THIS item's own parse rendered via a persisted
    # `stability_preferred_alt` identity (A), and how many draw-order-consecutive span pairs
    # (within one raw stroke) were junction-blended before concatenation (B).
    n_preferred_renders: int = 0
    n_tolerant_joins: int = 0


@dataclass
class WorksheetItem:
    item_id: Any
    class_id: Any
    round_trip_score: float
    residual_spans: list
    spans: list                    # [SpanParse, ...] -- the PARSE, no raw points, no ink
    dk: dict
    # RUN 29 (CONSUME) addition -- the character-grain quantum this item's own arrangement was
    # recognized as OR minted as at mark_characters() time (`None` for every stroke-grain `mark`
    # caller and every character-grain caller with `enable_character_codebook=False`, byte-
    # identical). Threading this through the worksheet lets `babble_characters` persist its own
    # per-rep arrangement-instability observations onto the SAME graph-resident quantum
    # `mark_characters` reads back next cycle -- closing the loop between "practice observes an
    # instability" and "the codebook's own stability weights reflect it."
    character_quantum: Optional[Any] = None


@dataclass
class Worksheet:
    items: list
    capacity: Optional[int] = None


@dataclass
class PracticeLog:
    per_item: dict                 # item_id -> {"reps","corrections","round_trip_before","round_trip_after"}
    total_corrections: int = 0


@dataclass
class CycleReport:
    pre_scores: dict
    post_scores: dict
    worksheet_size: int
    corrections: int
    surviving_residual_count: int
    surviving_residual_count_before: int
    practice_log: Optional[PracticeLog] = None
    # CHARACTER-GRAIN (run 27) additions -- 0 for every existing stroke-grain `cycle()` caller.
    # `mints_during_reading`: native OOV mints fired while DECODING real ink (the mark/re-mark
    # passes) -- "reading as practice" imports new information. `mints_during_babble`: mints
    # fired by the self-practice phase alone (mint_at_instability / variant_coverage
    # corrections) -- kept SEPARATE per the coordinator's own note: decode-side eager-child
    # minting during a babble decode is a READING event, not itself a correction, so it must
    # never be silently folded into this count.
    mints_during_reading: int = 0
    mints_during_babble: int = 0
    # RUN 28 LEVER 2 -- 0 for every existing caller (`enable_character_codebook` defaults
    # False on `mark_characters`/`cycle_characters`, byte-identical pre-existing behaviour).
    mints_character_reading: int = 0
    # RUN 31 (GEOMETRY) additions -- 0 for every caller that never passes
    # `use_preferred_parse=True` / `tolerant_joins=True` (byte-identical default). Summed over
    # BOTH the pre- and post-babble `mark`/`mark_characters` passes -- the per-cycle mechanism-
    # engagement instrument the run-31 gate reports separately from outcome (an arm whose
    # mechanism never engages is vacuous, not null).
    renders_with_preferred_parse: int = 0
    tolerant_join_applications: int = 0


# --------------------------------------------------------------------------- #
#  EVAL ISOLATION -- mechanical guard, adapter-legal (a fixed check over a caller-declared
#  set, never a decision over graph state).
# --------------------------------------------------------------------------- #
def _class_id_of(item) -> Any:
    if isinstance(item, dict):
        return item.get("class_id")
    return getattr(item, "class_id", None)


def _guard_eval(items, eval_class_ids) -> None:
    if not eval_class_ids:
        return
    for it in items:
        cid = _class_id_of(it)
        if cid in eval_class_ids:
            raise EvalLeakageError(
                f"item {getattr(it, 'item_id', it.get('id') if isinstance(it, dict) else it)!r} "
                f"belongs to eval class {cid!r} -- the homework loop must never mark or "
                "babble on held-out data")


# --------------------------------------------------------------------------- #
#  HELD-TERM COMPARATORS -- every "which spans agree / how many / which wins" decision is
#  one of these, never a bare Python score branch (mirrors abs_read.py's own
#  _argmax_pairs_term/_argmin_pairs_term/_max_score_term/_within_margin_term idiom set).
# --------------------------------------------------------------------------- #
def _bare_native():
    """A fresh, throwaway substrate's evaluator for STATELESS Lit-only Terms (Argmax/And/Gt/
    Lt over Python-assembled literal data, no graph read) -- the SAME idiom
    `ink_decode._lattice_partition` already uses ('a fresh, throwaway substrate ... freed
    after') for its own internal Term evaluation."""
    return srs.Substrate()._inner


def _argmax_pairs_term(pairs) -> dict:
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


def _residual_pairs_term(pairs) -> dict:
    """Held `FilterList(Not(Eq(orig, reread)))`: the (index, orig_name, reread_name) triples
    whose LAST TWO elements disagree -- the segmentation/identity round-trip's own residual
    set, read straight off a held Term, never a Python `!=` scan."""
    return {"type": "FilterList", "source": {"type": "Lit", "value": pairs}, "var_name": "p",
            "predicate": {"type": "Not", "arg": {"type": "Eq",
                "a": {"type": "IndexAt", "seq": {"type": "Var", "name": "p"},
                      "index": {"type": "Lit", "value": 1}},
                "b": {"type": "IndexAt", "seq": {"type": "Var", "name": "p"},
                      "index": {"type": "Lit", "value": 2}}}}}


def _frontier_term(score: float, max_score: float) -> dict:
    """Held `And(Gt(score,0), Lt(score,max))` -- the FRONTIER verdict (zone of proximal
    development: not solved, not zero-credit), never a bare Python `0 < score < max`."""
    return {"type": "And", "items": [
        {"type": "Gt", "a": {"type": "Lit", "value": float(score)},
         "b": {"type": "Lit", "value": 0.0}},
        {"type": "Lt", "a": {"type": "Lit", "value": float(score)},
         "b": {"type": "Lit", "value": float(max_score)}}]}


def _is_frontier(native, score: float, max_score: float = DEFAULT_MAX_SCORE) -> bool:
    return bool(native.evaluate(_frontier_term(score, max_score), {}))


def _family_root(sub, name: Optional[str]) -> Optional[str]:
    """Normalize a resolved identity to its FAMILY ROOT via `stroke_codebook.
    _prototype_anchor` (EXISTING, unchanged -- authored for continuous-mint anchoring, reused
    here for its own documented general behaviour: 'resolve to the nearest ancestor ... in
    every case this codebase currently produces, that is the ORIGINAL grow_stroke_quantum-
    installed family root'). Round-trip agreement is scored at FAMILY grain, not literal
    quantum-instance identity: a render that re-decodes to a freshly-minted REFINEMENT CHILD
    of the original family (exactly what `decode_ink`'s own per-decode refinement rung, and
    this module's own mechanism (b), are DESIGNED to produce) is a real re-identification of
    the SAME shape, not a miss -- literal string equality would otherwise punish the
    refinement ladder for doing its job. `None` (an unrecognized/absent span) maps to `None`
    unchanged (never fabricates a root for a genuine miss)."""
    if name is None:
        return None
    return sc._prototype_anchor(sub, name) or name


def _resolved_key(sub, orig_name: Optional[str], name: Optional[str]) -> Optional[str]:
    """`_family_root(name)`, additionally substituted to `orig_name`'s OWN family root when
    a PERSISTED stability preference (mechanism (a)'s own graph data, `babble`'s
    `stability_preferred_alt` attr) says the two are equivalent -- the round-trip
    comparator's own use of mechanism (a)'s learned preference, closing the loop between
    'persist a preference' and 'the preference is consulted' (both graph-data-driven,
    mechanical lookups of an ALREADY-decided value, never a new recognition). Without this,
    a genuinely independent top-level peer quantum a real re-render OOV-mints (structurally
    unrelated to `orig_name`'s own family by construction -- `_family_root` alone cannot
    reach it) would count as a residual FOREVER even after babble has explicitly learned and
    recorded that this peer consistently stands in for `orig_name` here."""
    root = _family_root(sub, name)
    orig_root = _family_root(sub, orig_name)
    if orig_name is not None and root is not None and root != orig_root:
        node = sc._find_stroke_node(sub, orig_name)
        pref = sub.node(node)["attrs"].get("stability_preferred_alt") if node is not None else None
        if pref is not None and _family_root(sub, pref) == root:
            return orig_root
    return root


def _round_trip_score(sub, native, orig_names: list, re_names: list) -> tuple[float, list]:
    """THE round-trip comparator: aligns `orig_names`/`re_names` by DRAW-ORDER POSITION
    (a dropped/shifted span already surfaces as a positional mismatch -- segmentation
    agreement, stroke-count agreement and per-stroke identity agreement all collapse into
    ONE positional comparison, exactly as `abs_render_compare_term`'s own draw-order
    correspondence already establishes one level up). Each name is normalized (`_resolved_key`:
    FAMILY ROOT first, `_family_root`, so a refinement child correctly counts as agreement
    with its own parent; then mechanism (a)'s own persisted `stability_preferred_alt`
    substitution) BEFORE the held comparator runs. `residual` is the held-Term-decided
    mismatch set (`_residual_pairs_term`); `round_trip_score` is the FIXED FORMULA
    `(n - len(residual)) / n` on that Term's own output count -- the same "arithmetic on an
    already-Term-computed value" idiom `ink_decode.py`'s own lattice-emission formula
    establishes, never a second scoring decision. `n == 0` (both sides empty -- a degenerate
    item) is vacuously perfect, an honest edge case, never a crash."""
    orig_roots = [_family_root(sub, nm) for nm in orig_names]
    re_roots = [_resolved_key(sub, orig_names[i] if i < len(orig_names) else None, nm)
               for i, nm in enumerate(re_names)]
    n = max(len(orig_roots), len(re_roots))
    if n == 0:
        return 1.0, []
    pairs = [(i, orig_roots[i] if i < len(orig_roots) else None,
              re_roots[i] if i < len(re_roots) else None) for i in range(n)]
    residual = native.evaluate(_residual_pairs_term(pairs), {}) or ()
    residual = [tuple(r) for r in residual]
    score = (n - len(residual)) / n
    return score, residual


# --------------------------------------------------------------------------- #
#  MECHANICAL DECODE/RENDER PLUMBING -- thin reuse of ink_decode/abs_read, no new geometry.
# --------------------------------------------------------------------------- #
def _spans_from_result(res: dict) -> list:
    """The SAME recognized+minted merge-by-start-position `character_compose.
    decode_result_to_stroke_points` already establishes, reduced to (start, end, name)
    triples (this module needs identities/positions, not points, at this stage)."""
    items = [(r["start"], r["end"], r["name"]) for r in res.get("recognized", [])]
    items += [(m["start"], m["end"], m["name"]) for m in res.get("minted", [])]
    items.sort(key=lambda x: x[0])
    return items


# --------------------------------------------------------------------------- #
#  RUN 31 MECHANISM A -- RENDER THE STABILITY-PREFERRED PARSE. `babble`'s own mechanism (a)
#  (PARSE STABILITY RE-RANK, above) already persists `stability_preferred_alt` as graph data
#  on a codebook entry when a MAJORITY of re-render reps stably re-decode as a different
#  identity. Every existing consumer of that data (`_resolved_key`, the round-trip SCORE
#  comparator) only ever reads it AFTER the fact, to avoid double-punishing an already-learned
#  equivalence. Nothing, before this run, fed it back into WHAT gets rendered -- the render
#  goal was always built from the span's own decoded `name`, even when the agent's own earned
#  evidence says that identity's canonical shape is the LESS stable thing to draw. This
#  section closes that loop: a HELD `IfThenElse` (never a Python `if`) substitutes the
#  preferred identity's stored `seg` for the render goal's shape, keeping the SAME observed
#  pose (`ink._pose_read_goal`'s own splice, unchanged) -- so the render is repositioned onto
#  the identity the agent's own babble evidence already found more reproducible, without
#  fabricating a new recognition (the substitution reads a fact `babble` already decided).
# --------------------------------------------------------------------------- #
def _preferred_render_name_term(name: Optional[str], pref: Optional[str]) -> dict:
    """Held `IfThenElse(Eq(pref, None), name, pref)` -- use the persisted
    `stability_preferred_alt` when present, else the decoded identity itself. Mirrors this
    module's own `_frontier_term`/`_residual_pairs_term` idiom: the SUBSTITUTION decision is
    the held Term's, Python only supplies the two already-known literal values (never a bare
    Python `pref or name` branch)."""
    return {"type": "IfThenElse",
            "cond": {"type": "Eq", "a": {"type": "Lit", "value": pref},
                     "b": {"type": "Lit", "value": None}},
            "then": {"type": "Lit", "value": name}, "other": {"type": "Lit", "value": pref}}


def _preferred_render_name(sub, native, name: Optional[str]) -> tuple:
    """Mechanical read (a graph-attribute fetch -- adapter I/O, not a decision) of `name`'s
    own persisted `stability_preferred_alt` (`babble`'s mechanism (a)), then the held Term
    above chooses between it and `name` itself. Returns `(render_name, used)` -- `used=True`
    iff a preference was actually applied (this run's own mechanism-A engagement signal)."""
    if name is None:
        return None, False
    node = sc._find_stroke_node(sub, name)
    pref = sub.node(node)["attrs"].get("stability_preferred_alt") if node is not None else None
    chosen = native.evaluate(_preferred_render_name_term(name, pref), {})
    return chosen, bool(chosen is not None and chosen != name)


def count_preferred_renders(parse: list) -> int:
    """Mechanical read-back (RUN 31 MECHANISM A engagement instrument): how many spans in a
    parse rendered via a persisted `stability_preferred_alt` identity instead of their own
    decoded name -- `SpanParse.rendered_as` is set only when `_preferred_render_name`'s own
    held Term actually chose the alternative (see `_parse_from_decode`)."""
    return sum(1 for s in parse if getattr(s, "rendered_as", None) is not None)


def _parse_from_decode(sub, native, knots, spans_st_e_name: list, dk: dict,
                       use_preferred_parse: bool = False) -> list:
    """Build the render-ready PARSE (`SpanParse` list) for one decode's own on-path spans --
    `ink._span_signature` (full, `invariant_only=False`) recomputes each span's own full
    signature from the SAME knots `decode_ink` itself just partitioned (mechanical re-read,
    not a re-decision), and `ink._pose_read_goal` (EXISTING, unchanged) splices the observed
    pose onto the chosen identity's own stored seg -- the identical render-goal construction
    `abs_read.abs_render_compare_term` already performs one call site up.

    RUN 31 MECHANISM A (`use_preferred_parse`, default `False` -- every pre-existing caller
    reproduces the BYTE-IDENTICAL render goal): when `True`, the identity handed to
    `ink._pose_read_goal` is `_preferred_render_name`'s own held-Term choice (`name`'s
    persisted `stability_preferred_alt` when present) instead of `name` itself -- the OBSERVED
    pose spliced on is unchanged either way."""
    parse = []
    for (st, e, name) in spans_st_e_name:
        full = ink._span_signature(native, knots, st, e, segments=dk["segments"],
                                    turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                                    grid=dk["grid"], scale_bins=dk["scale_bins"],
                                    invariant_only=False)
        render_name, preferred_used = (name, False)
        if use_preferred_parse:
            render_name, preferred_used = _preferred_render_name(sub, native, name)
        goal_sig = ink._pose_read_goal(sub, render_name, full["signature"])
        bbox = cc._frame_bbox(np.asarray(knots[st:e], dtype=float))
        parse.append(SpanParse(start=int(st), end=int(e), name=name, goal_sig=goal_sig,
                               bbox=bbox, n_points=max(2, int(e - st)),
                               rendered_as=(render_name if preferred_used else None)))
    return parse


_JITTER_KEY = {"pose_x": 0, "pose_y": 1, "pose_o": 2, "pose_s": 3}


def _jitter_goal_sig(goal_sig: list, jitter: tuple) -> list:
    """Mechanical arithmetic (no decision): add a small integer BIN delta to whichever
    `pose_x`/`pose_y`/`pose_o`/`pose_s` relations are present -- the writer-dimension pose
    vocabulary `seeds/writer_dimensions.json` already names, never touching `seg` (a
    stroke's shape identity), so this can only ever probe POSE robustness, never fabricate a
    new shape."""
    deltas = dict(zip(_POSE_JITTER_PREDS, jitter))
    out = []
    for rel in goal_sig:
        rel = list(rel)
        d = deltas.get(rel[0]) if rel else None
        if d:
            rel[1] = rel[1] + d
        out.append(rel)
    return out


def _render_parse(native, parse: list, dk: dict, jitter_by_idx: Optional[dict] = None,
                  tolerant_joins: bool = False,
                  junction_frac: float = ar.DEFAULT_JUNCTION_FRAC) -> tuple:
    """Render every span (in draw order) via ONE held `StrokeRender` evaluate each
    (`abs_read._render_term`, reused verbatim) and concatenate -- the SAME per-span render
    `abs_render_compare_term` performs, just concatenated into one pen path here instead of
    compared per-candidate. `jitter_by_idx`, when given, perturbs span `i`'s goal pose bins
    before rendering (mechanical substitution of an already-computed goal, never a new
    decision -- see `_jitter_goal_sig`). An empty/degenerate render for any span is skipped
    (honest non-crash, mirrors every other render-degrades-gracefully path in this codebase).

    RUN 31 MECHANISM B (`tolerant_joins`, default `False` -- every pre-existing call site
    reproduces the BYTE-IDENTICAL raw concatenation, `n_joins_applied` always `0`): reuses
    `abs_read._junction_blend` (EXISTING, unit-tested pure geometry -- already wired into the
    AbS recognition-VERDICT render path for BRANCH B CONTINUOUS, `abs_render_compare_term`) to
    warp each span's trailing/leading points toward the shared draw-order junction midpoint
    BEFORE concatenation -- the SAME mechanism, now applied to the PRACTICE render->re-read
    loop that manufactures this arc's own segmentation-instability residual (corner/knot
    artifacts at span boundaries the re-read lattice cuts differently), never a new geometry
    primitive and no Rust change. NOTE (honest scope): this is a SEPARATE, explicitly-flagged
    render mode -- it does NOT preserve `StrokeQuantize(StrokeRender(sig)) == sig` for a span
    whose trailing/leading points were blended (the blend deliberately moves points near the
    seam so the re-read segmenter lands differently there; see `tests/
    test_render_geometry_migrated.py::test_tolerant_joins_documents_inverse_break` for the
    explicit, gated documentation of that break) -- the DEFAULT `tolerant_joins=False` path
    remains the exact-inverse-preserving one, untouched.

    Returns `(points, n_joins_applied)` -- `n_joins_applied` counts the draw-order-consecutive
    span PAIRS actually blended (both sides rendered >=2 points -- `_junction_blend`'s own
    honest-skip condition), the run-31 gate's own mechanism-B engagement instrument."""
    rendered_by_idx: dict = {}
    for i, span in enumerate(parse):
        goal = span.goal_sig
        if jitter_by_idx and i in jitter_by_idx:
            goal = _jitter_goal_sig(goal, jitter_by_idx[i])
        term = ar._render_term(goal, n_points=span.n_points, bounds=span.bbox,
                               turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                               grid=dk["grid"], scale_bins=dk["scale_bins"])
        pts = native.evaluate(term, {})
        if pts:
            rendered_by_idx[i] = [list(p) for p in pts]

    n_joins = 0
    if tolerant_joins and len(rendered_by_idx) >= 2:
        before = rendered_by_idx
        rendered_by_idx = ar._junction_blend(before, junction_frac)
        ks = sorted(before)
        n_joins = sum(1 for a, b in zip(ks, ks[1:])
                     if len(before[a]) >= 2 and len(before[b]) >= 2)

    out: list = []
    for i in sorted(rendered_by_idx):
        out.extend(rendered_by_idx[i])
    return out, n_joins


def _decode_stroke_full(agent, points: list, dk: dict) -> tuple:
    """INGEST -> DECODE for ONE raw pen-stroke, returning `(knots, res)` -- the FULL
    `decode_ink` result dict (`recognized`/`oov`/`minted`/`refined`), needed at CHARACTER
    grain to thread `fine_child`/`substroke_points` through `character_compose.
    decode_result_to_stroke_points` and to count READING-pass mints
    (`len(res.get("minted", []))`) -- `_decode_points` below keeps only the (start,end,name)
    triples the stroke-grain loop needs, discarding exactly the fields character grain uses."""
    sub = _sub(agent)
    ink_node = ink.ingest_ink(agent, points, max_knots=dk["max_knots"])
    knots = np.asarray(sub.node(ink_node)["attrs"].get("knots") or [], dtype=float)
    res = ink.decode_ink(agent, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                         segments=dk["segments"], turn_bins=dk["turn_bins"],
                         len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
    return knots, res


def _decode_points(agent, points: list, dk: dict) -> tuple:
    """INGEST -> DECODE (mechanical world-adapter step, mirrors every existing Omniglot
    script call site): returns `(knots, spans_st_e_name)`."""
    knots, res = _decode_stroke_full(agent, points, dk)
    return knots, _spans_from_result(res)


# --------------------------------------------------------------------------- #
#  CHARACTER-GRAIN PLUMBING (run 27) -- COUNT-MISMATCH-TOLERANT ALIGNMENT.
#
#  Run 26's own final report named the mechanism hole this section closes: EVERY one of its
#  5 surviving residuals was a span-COUNT mismatch (orig->reread, e.g. 13->8), and `babble`'s
#  own alignment guard (`if len(re_spans) != n: continue`) DISCARDS every rep whose re-decode
#  changes the span count -- exactly the residual class that survives marking. "Corrections=0"
#  there wasn't "nothing to learn," it was "the learner's safety filter excludes its own
#  homework." At CHARACTER grain this would be even more costly (one raw stroke's own
#  segmentation-by-recognition lattice re-partitioning under re-render is exactly the
#  documented reproducer residual `character_compose.decode_result_to_stroke_points` composes
#  from). The fix: align by ARC-LENGTH OVERLAP, never by positional index -- a merged/split
#  span pair becomes its own residual entry (the thing to practice), never a reason to drop the
#  whole comparison. `_align_spans_by_overlap` is a REPEATED held Argmax over a Python-managed
#  "remaining" pool -- the SAME "remove an already-decided winner from a remaining list" idiom
#  `assign()`'s own capacity ordering and `abs_read.propose_top_k` already establish, applied
#  to overlap length instead of coverage/residual magnitude -- never a Python argmax/sort.
# --------------------------------------------------------------------------- #
def _overlap(a_st, a_e, b_st, b_e) -> float:
    """Mechanical arithmetic (no decision): the length of the intersection of two half-open
    index ranges sharing ONE coordinate space -- here, always two spans whose knots arrays came
    from the SAME `max_knots` (an original raw stroke's own knots vs. that SAME stroke's
    rendered-then-re-ingested knots), so index overlap IS arc-length overlap. `0.0` for
    disjoint/degenerate ranges, never negative."""
    return max(0.0, min(a_e, b_e) - max(a_st, b_st))


def _align_spans_by_overlap(native, orig_ste: list, re_ste: list) -> list:
    """COUNT-MISMATCH-TOLERANT alignment between two `(start, end, name)` span lists sharing
    ONE coordinate space: a REPEATED held `Argmax` over `(overlap, orig_idx, re_idx)` triples
    picks the single best-overlapping UNUSED pair each round (never a Python argmax/sort by
    overlap), removing both indices from their remaining pools, until no positive-overlap pair
    remains among what's left. Returns a list of `(orig_idx_or_None, re_idx_or_None, overlap)`
    triples covering EVERY index on both sides exactly once -- an unmatched original span (one
    that VANISHED / got MERGED into a neighbour) surfaces as `(i, None, 0.0)`; an unmatched
    reread span (a NEW one that appeared / got SPLIT out) surfaces as `(None, j, 0.0)`. A
    span-count mismatch is never a reason to drop anything -- it IS this function's own
    residual output, consumed by callers as the instability signal to practice on."""
    remaining_o = list(range(len(orig_ste)))
    remaining_r = list(range(len(re_ste)))
    pairs_all = []
    for i in remaining_o:
        for j in remaining_r:
            ov = _overlap(orig_ste[i][0], orig_ste[i][1], re_ste[j][0], re_ste[j][1])
            if ov > 0:
                pairs_all.append((float(ov), i, j))

    out: list = []
    while True:
        candidates = [p for p in pairs_all if p[1] in remaining_o and p[2] in remaining_r]
        if not candidates:
            break
        winner = native.evaluate(_argmax_pairs_term(candidates), {})
        if winner is None:
            break
        ov, i, j = winner
        i, j = int(i), int(j)
        out.append((i, j, float(ov)))
        remaining_o.remove(i)
        remaining_r.remove(j)
    out.extend((i, None, 0.0) for i in remaining_o)
    out.extend((None, j, 0.0) for j in remaining_r)
    return out


def _composed_names(signature: list) -> list:
    """Draw-order `strokeq` identity names extracted from a composed CHARACTER signature
    (`character_compose.compose_character_signature`'s own output) -- mechanical read-back,
    ordered by draw-order index `k`."""
    by_k = {r[1]: r[2] for r in signature if r and r[0] == "strokeq"}
    return [by_k[k] for k in sorted(by_k)]


def _composed_rel_by_k(signature: list) -> dict:
    """`k -> (x_q, y_q, orient_q, scale_q)` from a composed CHARACTER signature's own `rel`
    relations -- mechanical read-back."""
    return {r[1]: tuple(r[2:6]) for r in signature if r and r[0] == "rel"}


def _composed_cpose(signature: list) -> dict:
    """`predicate -> value` from a composed CHARACTER signature's own whole-character
    `cpose_*` relations -- mechanical read-back."""
    return {r[0]: r[1] for r in signature if r and r[0] in cc._CPOSE_PREDS}


def _character_jitter_by_idx(rng, jitter_bins: int, n: int) -> tuple:
    """CORRELATED pose jitter for ONE babble rep: a writer writes the WHOLE character with one
    hand, so a real re-render's pose noise is correlated across its strokes, not independent
    per stroke as stroke-grain `babble`'s own per-span-independent draws. Draws ONE shared
    character-level bin-delta tuple PLUS an independent per-span component, summed -- mechanical
    arithmetic on rng draws, never a decision. Returns `(shared, jitter_by_idx)` -- `shared` is
    exposed so a caller/test can confirm the SAME shared component was added to every span
    (`tests/test_homework_characters_migrated.py::test_correlated_jitter_is_correlated`).
    `jitter_bins<=0` returns an all-zero jitter per span (a legitimate, fully deterministic
    dwell, mirrors `babble`'s own `jitter_bins=0` convention) and an all-zero `shared`."""
    if jitter_bins <= 0:
        return (0, 0, 0, 0), {i: (0, 0, 0, 0) for i in range(n)}
    shared = tuple(int(x) for x in rng.integers(-jitter_bins, jitter_bins + 1, size=4))
    out = {}
    for i in range(n):
        per = tuple(int(x) for x in rng.integers(-jitter_bins, jitter_bins + 1, size=4))
        out[i] = tuple(shared[d] + per[d] for d in range(4))
    return shared, out


def _render_spans_per_stroke(native, spans: list, dk: dict,
                             jitter_by_idx: Optional[dict] = None) -> list:
    """Render EACH span (`SpanParse`) to its OWN point list (never concatenated) -- the
    CHARACTER-grain twin of `_render_parse`, needed because re-decode must treat each rendered
    stroke as its OWN pen-lift-delimited ink (mirroring how the original character's strokes
    were ingested/decoded independently). An empty/degenerate render for any span is an empty
    list at that position (honest non-crash, never a fabricated point), mirroring
    `_render_parse`'s own per-span skip."""
    out: list = []
    for i, span in enumerate(spans):
        goal = span.goal_sig
        if jitter_by_idx and i in jitter_by_idx:
            goal = _jitter_goal_sig(goal, jitter_by_idx[i])
        term = ar._render_term(goal, n_points=span.n_points, bounds=span.bbox,
                               turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                               grid=dk["grid"], scale_bins=dk["scale_bins"])
        pts = native.evaluate(term, {})
        out.append([list(p) for p in pts] if pts else [])
    return out


def _character_round_trip_score(sub, native, orig_groups: list, re_groups: list,
                                 orig_sig: list, re_sig: list) -> dict:
    """THE character-grain round-trip comparator -- three held-Term subscores built over a
    COUNT-MISMATCH-TOLERANT alignment (never positional/index correspondence):

      `orig_groups`/`re_groups`: one `(start,end,name)` span list per RAW pen-stroke (same
      order both sides -- pen-lift boundaries are hard external facts this module never
      merges/splits across), each pair aligned independently via `_align_spans_by_overlap`
      (so a WITHIN-one-raw-stroke segmentation-count change -- the documented reproducer
      residual -- is aligned by overlap, not discarded); the per-group alignments are
      concatenated (running offsets) into one GLOBAL `(orig_k_or_None, re_k_or_None)`
      correspondence over the composed signatures' own draw-order indices.

      FAMILY: `_residual_pairs_term` (the SAME `FilterList(Not(Eq))` idiom `_round_trip_score`
      already establishes) over `(label, orig_family_root_or_None, re_family_root_or_None)`
      triples built from the alignment -- an unmatched (merged-away/split-new) span
      contributes a `None` on one side, an honest residual, never silently dropped.

      COUNT: the FRACTION of the global correspondence that matched CLEANLY on both sides --
      fixed-formula arithmetic on the alignment's own output, `1.0` for a perfectly stable
      decode, falling as merges/splits accumulate.

      ARRANGEMENT: `_residual_pairs_term` over the `rel`/`cpose_*` VALUES of MATCHED pairs only
      (an unmatched span has no counterpart to compare a pose against -- that instability is
      already counted once, by FAMILY/COUNT; comparing it again here would double-penalize).

    `overall` is the FIXED FORMULA mean of the three subscores -- arithmetic on
    already-Term-computed values, never a second scoring decision, mirroring
    `_round_trip_score`'s own "(n-len(residual))/n" idiom one level up."""
    orig_names_flat = _composed_names(orig_sig)
    re_names_flat = _composed_names(re_sig)
    orig_rel = _composed_rel_by_k(orig_sig)
    re_rel = _composed_rel_by_k(re_sig)

    global_pairs: list = []
    o_off = r_off = 0
    for og, rg in zip(orig_groups, re_groups):
        align = _align_spans_by_overlap(native, og, rg)
        for (oi, ri, _ov) in align:
            global_pairs.append((o_off + oi if oi is not None else None,
                                 r_off + ri if ri is not None else None))
        o_off += len(og)
        r_off += len(rg)

    fam_pairs = []
    for (ok, rk) in global_pairs:
        oname = orig_names_flat[ok] if (ok is not None and ok < len(orig_names_flat)) else None
        rname = re_names_flat[rk] if (rk is not None and rk < len(re_names_flat)) else None
        label = ok if ok is not None else f"new@{rk}"
        fam_pairs.append((label, _family_root(sub, oname), _family_root(sub, rname)))
    n_fam = len(fam_pairs)
    fam_residual = [tuple(r) for r in
                    (native.evaluate(_residual_pairs_term(fam_pairs), {}) or ())] if n_fam else []
    family_score = (n_fam - len(fam_residual)) / n_fam if n_fam else 1.0

    matched = [(ok, rk) for (ok, rk) in global_pairs if ok is not None and rk is not None]
    count_score = (len(matched) / len(global_pairs)) if global_pairs else 1.0

    arr_pairs = []
    for (ok, rk) in matched:
        ov, rv = orig_rel.get(ok), re_rel.get(rk)
        for slot, label in enumerate(("x", "y", "o", "s")):
            arr_pairs.append((f"rel:{ok}:{label}", ov[slot] if ov is not None else None,
                              rv[slot] if rv is not None else None))
    orig_cpose, re_cpose = _composed_cpose(orig_sig), _composed_cpose(re_sig)
    for pred in cc._CPOSE_PREDS:
        if pred in orig_cpose or pred in re_cpose:
            arr_pairs.append((pred, orig_cpose.get(pred), re_cpose.get(pred)))
    n_arr = len(arr_pairs)
    arr_residual = [tuple(r) for r in
                    (native.evaluate(_residual_pairs_term(arr_pairs), {}) or ())] if n_arr else []
    arrangement_score = (n_arr - len(arr_residual)) / n_arr if n_arr else 1.0

    overall = (family_score + count_score + arrangement_score) / 3.0
    residual_spans = [("family", *r) for r in fam_residual] + \
                     [("arrangement", *r) for r in arr_residual]
    return dict(overall=overall, family_score=family_score, count_score=count_score,
                arrangement_score=arrangement_score, residual_spans=residual_spans,
                n_orig_strokes=len(orig_names_flat), n_reread_strokes=len(re_names_flat))


# --------------------------------------------------------------------------- #
#  1. MARK -- the grounding/marking session (real ink only).
# --------------------------------------------------------------------------- #
def mark(agent, items: list, *, dk: Optional[dict] = None,
         eval_class_ids: Optional[set] = None, use_preferred_parse: bool = False,
         tolerant_joins: bool = False,
         junction_frac: float = ar.DEFAULT_JUNCTION_FRAC) -> list:
    """`items`: `[{"id":..., "class_id":..., "points": [[x,y], ...]}, ...]` -- one REAL ink
    pen-stroke per item (the unit `ink_decode.decode_ink` natively partitions). For each:
    decode -> build the render-ready parse -> render it straight back -> re-decode the
    render -> score round-trip agreement (`_round_trip_score`). Returns one `MarkedItem`
    per input item, in input order.

    RUN 31 (GEOMETRY) -- `use_preferred_parse`/`tolerant_joins` (both default `False`, every
    pre-existing caller byte-identical): threaded straight to `_parse_from_decode` (MECHANISM
    A) and `_render_parse` (MECHANISM B); engagement counts land on the returned `MarkedItem`
    (`n_preferred_renders`/`n_tolerant_joins`)."""
    dk = {**_default_dk(), **(dk or {})}
    _guard_eval(items, eval_class_ids)
    sub = _sub(agent)
    native = _native(agent)

    out = []
    for item in items:
        knots, spans = _decode_points(agent, item["points"], dk)
        parse = _parse_from_decode(sub, native, knots, spans, dk,
                                   use_preferred_parse=use_preferred_parse)
        n_preferred = count_preferred_renders(parse)

        rendered, n_joins = _render_parse(native, parse, dk, tolerant_joins=tolerant_joins,
                                          junction_frac=junction_frac)
        if rendered:
            _re_knots, re_spans = _decode_points(agent, rendered, dk)
        else:
            re_spans = []

        orig_names = [s[2] for s in spans]
        re_names = [s[2] for s in re_spans]
        score, residual = _round_trip_score(sub, native, orig_names, re_names)
        frontier = _is_frontier(native, score)

        out.append(MarkedItem(
            item_id=item.get("id"), class_id=item.get("class_id"), round_trip_score=score,
            n_orig_spans=len(spans), n_reread_spans=len(re_spans), residual_spans=residual,
            partial_credit=frontier, spans=parse, dk=dk,
            n_preferred_renders=n_preferred, n_tolerant_joins=n_joins))
    return out


# --------------------------------------------------------------------------- #
#  2. ASSIGN -- the worksheet, derived ONLY from marking's own residuals.
# --------------------------------------------------------------------------- #
def assign(marked: list, *, capacity: Optional[int] = None,
           max_score: float = DEFAULT_MAX_SCORE) -> Worksheet:
    """Frontier filter (held `And(Gt,Lt)`, `_is_frontier`) keeps only 0 < score < max_score
    -- excludes both the SOLVED (score==max_score, nothing left to learn) and the ZERO-CREDIT
    (score==0, too hard for practice alone, waits for a richer lesson). Under a `capacity`
    cap, dwell is allocated to the LARGEST residual first via a REPEATED held `Argmax` over
    (residual_magnitude, index) pairs -- `abs_read.propose_top_k`'s own "remove an
    already-decided winner from a remaining list" idiom, applied to `1 - score` instead of
    coverage. Every returned `WorksheetItem` is one of `marked`'s own entries (by
    construction: this function only ever reads from `marked`, never invents an item) --
    the "worksheet is DERIVED from marking" contract gate 1 audits."""
    native = _bare_native()
    frontier = [m for m in marked if _is_frontier(native, m.round_trip_score, max_score)]

    if capacity is None or capacity >= len(frontier):
        chosen = frontier
    else:
        pairs_all = [(1.0 - m.round_trip_score, i) for i, m in enumerate(frontier)]
        remaining = list(range(len(frontier)))
        chosen_idx: list = []
        for _ in range(capacity):
            pairs = [pairs_all[i] for i in remaining]
            winner = native.evaluate(_argmax_pairs_term(pairs), {})
            if winner is None:
                break
            idx = int(winner[1])
            chosen_idx.append(idx)
            remaining.remove(idx)
        chosen = [frontier[i] for i in chosen_idx]

    items = [WorksheetItem(item_id=m.item_id, class_id=m.class_id,
                           round_trip_score=m.round_trip_score,
                           residual_spans=m.residual_spans, spans=m.spans, dk=m.dk,
                           character_quantum=getattr(m, "character_quantum", None))
            for m in chosen]
    return Worksheet(items=items, capacity=capacity)


# --------------------------------------------------------------------------- #
#  3. BABBLE -- self-practice, no real ink.
# --------------------------------------------------------------------------- #
def babble(agent, worksheet: Worksheet, *, reps_per_item: int, rng_seed: int,
           jitter_bins: int = DEFAULT_JITTER_BINS,
           eval_class_ids: Optional[set] = None, tolerant_joins: bool = False,
           junction_frac: float = ar.DEFAULT_JUNCTION_FRAC) -> PracticeLog:
    """Touches NO real ink -- every render is built from a `WorksheetItem`'s own stored
    `SpanParse` list (`goal_sig`/`bbox`/`n_points`), never from an original points array
    (there is none on this dataclass to read). Per item, per rep: jitter each span's pose
    bins by a small integer delta (`jitter_bins`, default `DEFAULT_JITTER_BINS`; `0` is a
    legitimate, fully-deterministic dwell -- decode_ink/StrokeRender are pure functions, so
    repeated zero-jitter reps confirm the SAME residual with 100% consistency, useful both
    as a controllability knob and as this module's own gate for mechanism (b)), render,
    re-decode, and:
      (a) tally the re-decoded identity at each span position (a held `Argmax` over
          (count, name) pairs picks the majority winner; a REPRODUCIBLE non-original winner
          is persisted as `stability_preferred_alt` graph data on that codebook entry);
      (b) where the SAME (by `_signature_key` over the SEG-only, pose-invariant portion --
          pose bins vary by construction under jitter even when the underlying SHAPE is
          identical, so keying on the full signature would never repeat) residual signature
          recurs at a span position across a MAJORITY of reps, `ink_decode._refine_or_note`
          (existing, unchanged) is invoked ONCE with that majority observation's own FULL
          signature -- the seeded rule decides mint/no-mint;
      (c) a jittered render that STILL decodes to the span's ORIGINAL identity (at FAMILY
          grain, `_family_root` -- a refinement child of the original family counts as
          agreement here too) is fed to `stroke_codebook.continuous_mint_or_note` (existing,
          unchanged) -- genuinely-far geometry earns a peer prototype.
    A span position is only ever bookkept when THIS rep's re-decode produced the SAME
    SPAN COUNT as the original parse (an honest alignment guard -- a dropped/added span
    shifts every subsequent position, and slicing a shifted `(start,end)` would feed the
    WRONG geometry into (b)/(c); an untrustworthy rep contributes nothing, mirroring
    `abs_render_compare_term`'s own "stroke-count mismatch -> fall through" discipline).
    Finally, a ZERO-jitter render/re-decode of the (possibly now better-served-by-the-grown-
    codebook) SAME parse gives `round_trip_after`, compared against the worksheet item's own
    recorded `round_trip_before`."""
    _guard_eval(worksheet.items, eval_class_ids)
    sub = _sub(agent)
    native = _native(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    rng = np.random.default_rng(rng_seed)

    per_item: dict = {}
    total_corrections = 0

    for wi in worksheet.items:
        orig_names = [s.name for s in wi.spans]
        n = len(wi.spans)
        alt_counts: list = [dict() for _ in range(n)]
        residual_sig_counts: list = [dict() for _ in range(n)]
        corrections: list = []

        for _rep in range(reps_per_item):
            if jitter_bins > 0:
                jitter_by_idx = {
                    i: tuple(int(x) for x in
                             rng.integers(-jitter_bins, jitter_bins + 1, size=4))
                    for i in range(n)}
            else:
                jitter_by_idx = None
            rendered, _n_joins = _render_parse(native, wi.spans, wi.dk,
                                               jitter_by_idx=jitter_by_idx,
                                               tolerant_joins=tolerant_joins,
                                               junction_frac=junction_frac)
            if not rendered:
                continue
            re_knots, re_spans = _decode_points(agent, rendered, wi.dk)
            if len(re_spans) != n:
                continue          # untrustworthy alignment this rep -- an honest skip.

            for i, orig_name in enumerate(orig_names):
                st, e, re_name = re_spans[i]
                alt_counts[i][re_name] = alt_counts[i].get(re_name, 0) + 1

                if _family_root(sub, re_name) == _family_root(sub, orig_name):
                    # (c) VARIANT COVERAGE -- still recognized (at family grain); widen
                    # coverage via the EXISTING continuous-novelty mint (a held
                    # DtwTo/Argmin/Lt decision).
                    variant_pts = re_knots[st:e].tolist()
                    cont_res = sc.continuous_mint_or_note(
                        agent, orig_name, variant_pts,
                        threshold=wi.dk.get("continuous_mint_threshold",
                                            sc.DEFAULT_CONTINUOUS_MINT_THRESHOLD),
                        segments=wi.dk["segments"], turn_bins=wi.dk["turn_bins"],
                        len_bins=wi.dk["len_bins"], grid=wi.dk["grid"],
                        scale_bins=wi.dk["scale_bins"], category=wi.dk["category"])
                    if cont_res.get("minted"):
                        corrections.append({"type": "variant_coverage", "span": i,
                                            "name": cont_res.get("name")})
                else:
                    # (b) candidate residual signature -- tallied by its SEG-ONLY content
                    # key (pose-invariant), a majority-consistent one gets ONE refinement
                    # look after the rep loop.
                    full = ink._span_signature(
                        native, re_knots, st, e, segments=wi.dk["segments"],
                        turn_bins=wi.dk["turn_bins"], len_bins=wi.dk["len_bins"],
                        grid=wi.dk["grid"], scale_bins=wi.dk["scale_bins"],
                        invariant_only=False)
                    seg_only = ink._fine_seg_relations(full["signature"])
                    key = ink._signature_key(seg_only)
                    cnt, _sig = residual_sig_counts[i].get(key, (0, None))
                    residual_sig_counts[i][key] = (cnt + 1, full["signature"])

        # (a) PARSE STABILITY RE-RANK -- held Argmax between tallied candidates; a
        # reproducible (majority) non-original winner is PERSISTED as codebook data.
        for i, orig_name in enumerate(orig_names):
            pairs = [(float(c), nm) for nm, c in alt_counts[i].items() if nm is not None]
            if not pairs:
                continue
            winner = native.evaluate(_argmax_pairs_term(pairs), {})
            if winner is None:
                continue
            best_count, best_name = winner
            if best_name != orig_name and best_count > reps_per_item / 2.0:
                node = sc._find_stroke_node(sub, orig_name)
                if node is not None:
                    sub.set_attr(node, "stability_preferred_alt", best_name)
                    sub.set_attr(node, "stability_confidence", float(best_count) / reps_per_item)
                corrections.append({"type": "stability_rerank", "span": i,
                                    "preferred": best_name,
                                    "confidence": best_count / reps_per_item})

        # (b) MINT AT INSTABILITY -- ONE refinement look at the majority-consistent
        # residual signature per span (never per-rep noise); the SEEDED ir_* rule decides.
        for i, orig_name in enumerate(orig_names):
            sig_counts = residual_sig_counts[i]
            if not sig_counts:
                continue
            pairs = [(float(cnt), key) for key, (cnt, _sig) in sig_counts.items()]
            winner = native.evaluate(_argmax_pairs_term(pairs), {})
            if winner is None:
                continue
            top_count, top_key = winner
            if top_count > reps_per_item / 2.0:
                _cnt, majority_sig = sig_counts[top_key]
                stroke_node = sub.add_node("Stroke", {"start": -1, "end": -1,
                                                      "recognized_as": orig_name,
                                                      "practice_probe": True})
                refine_res = ink._refine_or_note(
                    agent, sub, native, ag_node, stroke_node, orig_name, majority_sig,
                    segments=wi.dk["segments"], turn_bins=wi.dk["turn_bins"],
                    len_bins=wi.dk["len_bins"], grid=wi.dk["grid"],
                    scale_bins=wi.dk["scale_bins"], category=wi.dk["category"])
                if refine_res is not None and refine_res.get("minted"):
                    corrections.append({"type": "mint_at_instability", "span": i,
                                        "name": refine_res.get("name")})

        # After-babble check: ZERO-jitter re-render/re-decode of the SAME parse, against the
        # SAME original identities -- did the (possibly grown) codebook improve the read?
        after_score = wi.round_trip_score
        rendered, _n_joins = _render_parse(native, wi.spans, wi.dk, tolerant_joins=tolerant_joins,
                                           junction_frac=junction_frac)
        if rendered:
            _knots2, re_spans2 = _decode_points(agent, rendered, wi.dk)
            re_names2 = [s[2] for s in re_spans2]
            after_score, _res2 = _round_trip_score(sub, native, orig_names, re_names2)

        per_item[wi.item_id] = {"reps": reps_per_item, "corrections": corrections,
                                "round_trip_before": wi.round_trip_score,
                                "round_trip_after": after_score}
        total_corrections += len(corrections)

    return PracticeLog(per_item=per_item, total_corrections=total_corrections)


# --------------------------------------------------------------------------- #
#  4. CYCLE -- mark -> assign -> babble -> re-mark, the teacher-information metric.
# --------------------------------------------------------------------------- #
def cycle(agent, ground_items: list, *, reps_per_item: int, rng_seed: int,
          dk: Optional[dict] = None, capacity: Optional[int] = None,
          jitter_bins: int = DEFAULT_JITTER_BINS,
          eval_class_ids: Optional[set] = None, use_preferred_parse: bool = False,
          tolerant_joins: bool = False,
          junction_frac: float = ar.DEFAULT_JUNCTION_FRAC) -> CycleReport:
    marked_before = mark(agent, ground_items, dk=dk, eval_class_ids=eval_class_ids,
                         use_preferred_parse=use_preferred_parse, tolerant_joins=tolerant_joins,
                         junction_frac=junction_frac)
    worksheet = assign(marked_before, capacity=capacity)
    log = babble(agent, worksheet, reps_per_item=reps_per_item, rng_seed=rng_seed,
                jitter_bins=jitter_bins, eval_class_ids=eval_class_ids,
                tolerant_joins=tolerant_joins, junction_frac=junction_frac)
    marked_after = mark(agent, ground_items, dk=dk, eval_class_ids=eval_class_ids,
                       use_preferred_parse=use_preferred_parse, tolerant_joins=tolerant_joins,
                       junction_frac=junction_frac)

    surviving_before = sum(1 for m in marked_before if m.round_trip_score < DEFAULT_MAX_SCORE)
    surviving_after = sum(1 for m in marked_after if m.round_trip_score < DEFAULT_MAX_SCORE)
    renders_with_preferred_parse = (sum(m.n_preferred_renders for m in marked_before)
                                    + sum(m.n_preferred_renders for m in marked_after))
    tolerant_join_applications = (sum(m.n_tolerant_joins for m in marked_before)
                                  + sum(m.n_tolerant_joins for m in marked_after))

    return CycleReport(
        pre_scores={m.item_id: m.round_trip_score for m in marked_before},
        post_scores={m.item_id: m.round_trip_score for m in marked_after},
        worksheet_size=len(worksheet.items), corrections=log.total_corrections,
        surviving_residual_count=surviving_after,
        surviving_residual_count_before=surviving_before, practice_log=log,
        renders_with_preferred_parse=renders_with_preferred_parse,
        tolerant_join_applications=tolerant_join_applications)


# --------------------------------------------------------------------------- #
#  5. MARK_CHARACTERS -- the CHARACTER-grain grounding/marking session (run 27).
#
#  Practices the creator's own frame directly: "the connectedness of the speech and language
#  cortex means you get better at speaking by reading as well" -- decode and render share ONE
#  codebook (AbS), so decode-side exposure to NOVEL real ink (this function) is production
#  practice AND the only arm importing new information. Every raw pen-stroke of a character is
#  decoded independently (native OOV minting is allowed to fire -- `n_mints_reading` counts
#  it), composed (`character_compose.compose_character_signature`), rendered back ONE RAW
#  STROKE AT A TIME (`_render_parse` over that stroke's own spans, preserving its pen-lift
#  boundary -- mirrors `mark`'s own single-motor-stroke framing one level up), independently
#  re-decoded, re-composed, and scored via `_character_round_trip_score` (COUNT-MISMATCH-
#  TOLERANT: a within-stroke segmentation-count change is aligned by overlap, never dropped).
# --------------------------------------------------------------------------- #
def _apply_stability_weighting(agent, scored: dict, character_quantum: Optional[str],
                               character_recognized_held: bool, orig_sig: list, re_sig: list,
                               use_weights: bool) -> dict:
    """RUN 29 (CONSUME) -- mechanical override, no new scoring decision: when `use_weights` and
    the item's arrangement was scored against a HELD (already-recognized-by-the-codebook, never
    a just-this-call mint -- a freshly minted quantum's weights are all still `DEFAULT_WEIGHT`,
    so overriding there would be a costless no-op, but the run's own pre-registered contract is
    "weighted ... when HELD, unweighted otherwise") character quantum, this item's own
    `arrangement_score` is REPLACED by `arrangement_codebook.weighted_arrangement_score`'s read
    of that quantum's persisted `relation_weights` against the SAME `(orig_sig, re_sig)` pair
    already computed by the caller (never a second composition) -- the plain unweighted value
    moves to `arrangement_score_unweighted` (reported, never discarded) and `overall` is
    recomputed by the SAME fixed-formula mean `_character_round_trip_score` itself uses, on the
    new arrangement value. A no-op (returns `scored` with `arrangement_score_unweighted=None`,
    every existing field byte-identical) when `use_weights` is False or the quantum was not a
    HELD recognition this call -- every pre-existing caller (flag untouched) is unaffected."""
    out = dict(scored)
    out.setdefault("arrangement_score_unweighted", None)
    if use_weights and character_recognized_held and character_quantum:
        weighted = ac.weighted_arrangement_score(agent, character_quantum, orig_sig, re_sig)
        out["arrangement_score_unweighted"] = out["arrangement_score"]
        out["arrangement_score"] = weighted["score"]
        out["overall"] = (out["family_score"] + out["count_score"] + out["arrangement_score"]) / 3.0
    return out


def mark_characters(agent, char_items: list, *, dk: Optional[dict] = None,
                    eval_class_ids: Optional[set] = None,
                    enable_character_codebook: bool = False,
                    use_stability_weights: bool = False,
                    use_preferred_parse: bool = False, tolerant_joins: bool = False,
                    junction_frac: float = ar.DEFAULT_JUNCTION_FRAC) -> list:
    """`char_items`: `[{"id":..., "class_id":..., "strokes": [[[x,y],...], ...]}, ...]` -- one
    REAL character's pen-strokes (draw order) per item. Returns one `MarkedItem` per input
    item, in input order -- `n_orig_spans`/`n_reread_spans` are the composed STROKE counts at
    this grain (`_character_round_trip_score`'s own `n_orig_strokes`/`n_reread_strokes`),
    `family_score`/`count_score`/`arrangement_score` its three subscores, `spans` the flat
    (across all raw strokes) render-ready PARSE `assign()`/`babble_characters` consume
    unchanged (grain-agnostic), `n_mints_reading` the READING-pass mint count.

    RUN 28 LEVER 2 (`enable_character_codebook`, default `False` -- OPT-IN, the SAME "many
    existing unflagged callers" discipline `include_rel2`/`enable_substroke`/
    `enable_continuous_mint` already establish throughout this codebase, so every pre-existing
    caller/test behaves byte-identically with the flag untouched): when on, this item's own
    `orig_sig` (already composed for the round-trip score, no second composition) is handed to
    `arrangement_codebook.mint_or_recognize_character_reading` -- the ARRANGEMENT-grain twin of
    the stroke-grain OOV mint this function's own inner loop already performs one level down.
    `n_mints_character_reading`/`character_quantum` on the returned `MarkedItem` report what
    happened; when a quantum was recognized OR just minted, this item's own render/re-decode
    round trip (`orig_sig` vs `re_sig`, already computed below for the UNCHANGED subscores) ALSO
    updates that quantum's own PERSISTED per-relation stability weights
    (`arrangement_codebook.update_relation_stability`) -- the SAME round-trip data, now ALSO
    fed into the arrangement-grain persistence channel the run-28 header calls for.

    RUN 29 (CONSUME) -- `use_stability_weights` (default `False`, OPT-IN, byte-identical to
    every pre-existing caller): recognition happens FIRST (before scoring, reordered from run
    28's own recognize-after-score sequence) so a HELD quantum's *already-persisted* (this call's
    own observation not yet folded in) `relation_weights` can be consulted by
    `_apply_stability_weighting` for THIS item's own `arrangement_score` -- reading last cycle's
    reliability, never this round's own outcome (persisting THIS round's update happens
    afterward, so a relation cannot be down-weighted by its own current disagreement and then
    scored as if that down-weighting already applied -- see `_apply_stability_weighting`'s own
    docstring). `arrangement_score_unweighted` on the returned `MarkedItem` always carries what
    the plain (all-weights-1.0) formula would have reported, so the weighting effect is visible
    separately from any real learning effect.

    RUN 31 (GEOMETRY) -- `use_preferred_parse` (MECHANISM A)/`tolerant_joins` (MECHANISM B),
    both default `False` (every pre-existing caller byte-identical): threaded to
    `_parse_from_decode`/`_render_parse` at the per-raw-stroke render step below -- the exact
    render/re-decode pass this arc's own diagnosed "arrangement round-trip stability" residual
    comes from. Engagement lands on the returned `MarkedItem` (`n_preferred_renders`/
    `n_tolerant_joins`, summed over every raw stroke in the item)."""
    dk = {**_default_dk(), **(dk or {})}
    _guard_eval(char_items, eval_class_ids)
    sub = _sub(agent)
    native = _native(agent)

    out = []
    for item in char_items:
        orig_groups, re_groups = [], []
        orig_stroke_points, re_stroke_points = [], []
        all_spans: list = []
        n_mints = 0
        n_preferred = 0
        n_joins_total = 0

        for raw_points in item["strokes"]:
            knots, res = _decode_stroke_full(agent, raw_points, dk)
            n_mints += len(res.get("minted", []))
            ste = _spans_from_result(res)
            orig_groups.append(ste)
            orig_stroke_points.extend(cc.decode_result_to_stroke_points(knots, res))
            spans_i = _parse_from_decode(sub, native, knots, ste, dk,
                                         use_preferred_parse=use_preferred_parse)
            n_preferred += count_preferred_renders(spans_i)
            all_spans.extend(spans_i)

            # Render THIS raw stroke's own spans back into ONE continuous path (mirrors
            # `mark`'s own single-motor-stroke framing) and re-decode independently -- pen-lift
            # boundaries across DIFFERENT raw strokes are never merged/split by this loop.
            rendered, n_joins = _render_parse(native, spans_i, dk, tolerant_joins=tolerant_joins,
                                              junction_frac=junction_frac)
            n_joins_total += n_joins
            if rendered:
                re_knots, re_res = _decode_stroke_full(agent, rendered, dk)
                re_ste = _spans_from_result(re_res)
                re_groups.append(re_ste)
                re_stroke_points.extend(cc.decode_result_to_stroke_points(re_knots, re_res))
            else:
                re_groups.append([])

        orig_sig = cc.compose_character_signature(
            native, orig_stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
            len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])["signature"]
        re_sig = cc.compose_character_signature(
            native, re_stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
            len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])["signature"]

        # RUN 29 (CONSUME) -- recognize/mint FIRST, using this quantum's own weights as they
        # stood BEFORE this call's own observation is folded in (see `_apply_stability_
        # weighting`'s docstring for why the ordering matters).
        n_mints_character = 0
        character_quantum = None
        character_recognized_held = False
        if enable_character_codebook and orig_sig:
            char_res = ac.mint_or_recognize_character_reading(agent, orig_sig)
            character_quantum = char_res.get("name")
            if char_res.get("installed"):
                n_mints_character = 1
            else:
                character_recognized_held = bool(character_quantum)

        scored = _character_round_trip_score(sub, native, orig_groups, re_groups, orig_sig,
                                             re_sig)
        scored = _apply_stability_weighting(agent, scored, character_quantum,
                                            character_recognized_held, orig_sig, re_sig,
                                            use_stability_weights)
        frontier = _is_frontier(native, scored["overall"])

        # Persist THIS call's own round-trip observation onto the quantum's weights AFTER
        # scoring -- next cycle's mark_characters reads it back, this one never scores itself
        # against its own not-yet-recorded outcome.
        if enable_character_codebook and character_quantum and re_sig:
            ac.update_relation_stability(agent, character_quantum, orig_sig, re_sig)

        out.append(MarkedItem(
            item_id=item.get("id"), class_id=item.get("class_id"),
            round_trip_score=scored["overall"], n_orig_spans=scored["n_orig_strokes"],
            n_reread_spans=scored["n_reread_strokes"], residual_spans=scored["residual_spans"],
            partial_credit=frontier, spans=all_spans, dk=dk,
            family_score=scored["family_score"], count_score=scored["count_score"],
            arrangement_score=scored["arrangement_score"], n_mints_reading=n_mints,
            n_mints_character_reading=n_mints_character, character_quantum=character_quantum,
            arrangement_score_unweighted=scored.get("arrangement_score_unweighted"),
            n_preferred_renders=n_preferred, n_tolerant_joins=n_joins_total))
    return out


# --------------------------------------------------------------------------- #
#  6. BABBLE_CHARACTERS -- whole-character self-practice (run 27).
#
#  `assign()` is REUSED UNCHANGED (`MarkedItem`/`WorksheetItem` are grain-agnostic) --
#  `cycle_characters` below calls it exactly as `cycle` does. `worksheet.items[i].spans` is the
#  flat (across raw strokes) parse `mark_characters` built; per-raw-stroke grouping does NOT
#  survive `assign()`'s own unchanged construction, so this function treats EACH `SpanParse`
#  as its own independently-rendered/re-decoded unit -- still COUNT-MISMATCH-TOLERANT (a
#  render that re-partitions into >1 span is aligned via `_align_spans_by_overlap` against a
#  single full-extent "original" entry, never discarded as a skipped rep): a SPLIT (1->N) is
#  directly observed and practiced here; a MERGE (>=2 adjacent spans from the SAME raw stroke
#  collapsing into one) needs the raw-stroke grouping only `mark_characters`'s own per-item
#  loop has, so it is corrected THERE, at the next mark_characters call after this practice
#  session's identity/geometry corrections have had a chance to change how that span reads.
# --------------------------------------------------------------------------- #
def babble_characters(agent, worksheet: Worksheet, *, reps_per_item: int, rng_seed: int,
                      jitter_bins: int = DEFAULT_JITTER_BINS,
                      eval_class_ids: Optional[set] = None) -> PracticeLog:
    """Whole-character babble: renders the character's parse with CORRELATED pose jitter
    (`_character_jitter_by_idx` -- per-stroke jitter PLUS a shared CHARACTER-level component),
    re-reads (pen-lift boundaries preserved, one independent ingest/decode per span), and fires
    the SAME three mechanisms `babble` establishes -- (a) stability re-rank, (b) mint-at-
    instability, (c) variant coverage -- at the per-span IDENTITY channel (fires
    unconditionally per span per rep, never gated on a whole-item count match), PLUS two NEW
    channels: (d) SEGMENTATION-SPLIT INSTABILITY (a majority-consistent split is itself
    persisted graph data, `segmentation_split_prone`/`segmentation_split_rate` on the span's
    codebook node) and (e) ARRANGEMENT INSTABILITY (a majority-mismatched `rel`/`cpose` value
    across reps -- computed only on reps where every span matched cleanly, a strictly lighter
    gate than the OLD whole-rep count-equality skip -- persists `arrangement_unstable`/
    `arrangement_instability_rate` on the relevant stroke node, or an aggregate
    `cpose_instability_events` counter on the agent root for the whole-character case, since no
    character-level codebook node exists at this grain to attach to)."""
    _guard_eval(worksheet.items, eval_class_ids)
    sub = _sub(agent)
    native = _native(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    rng = np.random.default_rng(rng_seed)

    per_item: dict = {}
    total_corrections = 0

    for wi in worksheet.items:
        orig_names = [s.name for s in wi.spans]
        n = len(wi.spans)
        alt_counts: list = [dict() for _ in range(n)]
        residual_sig_counts: list = [dict() for _ in range(n)]
        split_counts: list = [0 for _ in range(n)]
        rel_agree = [0 for _ in range(n)]
        rel_total = [0 for _ in range(n)]
        cpose_agree = 0
        cpose_total = 0
        corrections: list = []

        # ZERO-JITTER reference composition -- WorksheetItem carries no raw ink (module
        # docstring), so this is the graph-resident stand-in for "what this stored parse's own
        # canonical arrangement reads as right now" -- the target the arrangement channel (e)
        # and the after-babble check both measure against.
        ref_rendered = _render_spans_per_stroke(native, wi.spans, wi.dk)
        ref_stroke_points, ref_ok = [], True
        for rp in ref_rendered:
            if not rp:
                ref_ok = False
                break
            knots_i, res_i = _decode_stroke_full(agent, rp, wi.dk)
            sp_i = cc.decode_result_to_stroke_points(knots_i, res_i)
            if len(sp_i) != 1:
                ref_ok = False
                break
            ref_stroke_points.extend(sp_i)
        ref_sig = cc.compose_character_signature(
            native, ref_stroke_points, segments=wi.dk["segments"], turn_bins=wi.dk["turn_bins"],
            len_bins=wi.dk["len_bins"], grid=wi.dk["grid"],
            scale_bins=wi.dk["scale_bins"])["signature"] if ref_ok else []
        ref_rel = _composed_rel_by_k(ref_sig)
        ref_cpose = _composed_cpose(ref_sig)

        for _rep in range(reps_per_item):
            _shared, jitter_by_idx = _character_jitter_by_idx(rng, jitter_bins, n)
            rendered = _render_spans_per_stroke(native, wi.spans, wi.dk,
                                                jitter_by_idx=jitter_by_idx)
            matched_names: list = [None] * n

            for i, rp in enumerate(rendered):
                if not rp:
                    continue          # this span's render degenerated this rep -- an honest
                                        # skip of just THIS span/rep, never the whole rep.
                knots_i, res_i = _decode_stroke_full(agent, rp, wi.dk)
                re_ste_i = _spans_from_result(res_i)
                orig_extent = [(0, max(1, len(knots_i)), orig_names[i])]
                align_i = _align_spans_by_overlap(native, orig_extent, re_ste_i)
                matched = [(oi, ri) for (oi, ri, _ov) in align_i
                          if oi is not None and ri is not None]
                extra = [ri for (oi, ri, _ov) in align_i if oi is None]
                if extra:
                    split_counts[i] += 1   # SEGMENTATION-SPLIT INSTABILITY -- itself an
                                            # instability signal, never a discarded rep.
                if not matched:
                    continue                # this span vanished entirely this rep -- honest
                                             # skip (e.g. a wholly-OOV render), rare.
                _oi, ri = matched[0]
                st, e, re_name = re_ste_i[ri]
                matched_names[i] = re_name
                alt_counts[i][re_name] = alt_counts[i].get(re_name, 0) + 1

                if _family_root(sub, re_name) == _family_root(sub, orig_names[i]):
                    variant_pts = knots_i[st:e].tolist()
                    cont_res = sc.continuous_mint_or_note(
                        agent, orig_names[i], variant_pts,
                        threshold=wi.dk.get("continuous_mint_threshold",
                                            sc.DEFAULT_CONTINUOUS_MINT_THRESHOLD),
                        segments=wi.dk["segments"], turn_bins=wi.dk["turn_bins"],
                        len_bins=wi.dk["len_bins"], grid=wi.dk["grid"],
                        scale_bins=wi.dk["scale_bins"], category=wi.dk["category"])
                    if cont_res.get("minted"):
                        corrections.append({"type": "variant_coverage", "span": i,
                                            "name": cont_res.get("name")})
                else:
                    full = ink._span_signature(
                        native, knots_i, st, e, segments=wi.dk["segments"],
                        turn_bins=wi.dk["turn_bins"], len_bins=wi.dk["len_bins"],
                        grid=wi.dk["grid"], scale_bins=wi.dk["scale_bins"], invariant_only=False)
                    seg_only = ink._fine_seg_relations(full["signature"])
                    key = ink._signature_key(seg_only)
                    cnt, _sig = residual_sig_counts[i].get(key, (0, None))
                    residual_sig_counts[i][key] = (cnt + 1, full["signature"])

            # (e) ARRANGEMENT-INSTABILITY tally -- only when EVERY span matched cleanly this
            # rep (a lighter-weight gate than the OLD hard count-equality guard: it only skips
            # this OPTIONAL rel/cpose channel for the rep, never the per-span identity channels
            # above, which already fired unconditionally).
            if ref_ok and all(nm is not None for nm in matched_names):
                re_stroke_points_rep = []
                for i in range(n):
                    knots_i2, res_i2 = _decode_stroke_full(agent, rendered[i], wi.dk)
                    re_stroke_points_rep.extend(cc.decode_result_to_stroke_points(knots_i2, res_i2))
                if len(re_stroke_points_rep) == n:
                    re_sig_rep = cc.compose_character_signature(
                        native, re_stroke_points_rep, segments=wi.dk["segments"],
                        turn_bins=wi.dk["turn_bins"], len_bins=wi.dk["len_bins"],
                        grid=wi.dk["grid"], scale_bins=wi.dk["scale_bins"])["signature"]
                    re_rel_rep = _composed_rel_by_k(re_sig_rep)
                    re_cpose_rep = _composed_cpose(re_sig_rep)
                    for i in range(n):
                        rel_total[i] += 1
                        if ref_rel.get(i) == re_rel_rep.get(i):
                            rel_agree[i] += 1
                    cpose_total += 1
                    if all(ref_cpose.get(p) == re_cpose_rep.get(p) for p in cc._CPOSE_PREDS):
                        cpose_agree += 1
                    # RUN 29 (CONSUME) -- persist THIS rep's own arrangement observation onto
                    # the RECOGNIZED character quantum's graph-resident `relation_weights`
                    # (`arrangement_codebook.update_relation_stability`, unchanged, the SAME
                    # primitive `mark_characters` calls) -- `wi.character_quantum` is set only
                    # when `mark_characters` was called with `enable_character_codebook=True`
                    # and this item's arrangement was recognized/minted (`assign()`'s own
                    # unchanged-shape threading); every pre-existing worksheet item (the flag
                    # untouched) carries `character_quantum=None` and this is a no-op. Without
                    # this, babble's own per-rep re-render/re-decode instability signal (already
                    # computed above for the `rel_agree`/`rel_total` tally) was measured but
                    # never written back to the graph -- the "surviving weight machinery that
                    # nothing feeds" hole this run closes.
                    if wi.character_quantum:
                        ac.update_relation_stability(agent, wi.character_quantum, ref_sig,
                                                     re_sig_rep)

        # (a) PARSE STABILITY RE-RANK -- unchanged mechanism, per span.
        for i, orig_name in enumerate(orig_names):
            pairs = [(float(c), nm) for nm, c in alt_counts[i].items() if nm is not None]
            if not pairs:
                continue
            winner = native.evaluate(_argmax_pairs_term(pairs), {})
            if winner is None:
                continue
            best_count, best_name = winner
            if best_name != orig_name and best_count > reps_per_item / 2.0:
                node = sc._find_stroke_node(sub, orig_name)
                if node is not None:
                    sub.set_attr(node, "stability_preferred_alt", best_name)
                    sub.set_attr(node, "stability_confidence", float(best_count) / reps_per_item)
                corrections.append({"type": "stability_rerank", "span": i,
                                    "preferred": best_name, "confidence": best_count / reps_per_item})

        # (b) MINT AT INSTABILITY -- unchanged mechanism.
        for i, orig_name in enumerate(orig_names):
            sig_counts = residual_sig_counts[i]
            if not sig_counts:
                continue
            pairs = [(float(cnt), key) for key, (cnt, _sig) in sig_counts.items()]
            winner = native.evaluate(_argmax_pairs_term(pairs), {})
            if winner is None:
                continue
            top_count, top_key = winner
            if top_count > reps_per_item / 2.0:
                _cnt, majority_sig = sig_counts[top_key]
                stroke_node = sub.add_node("Stroke", {"start": -1, "end": -1,
                                                      "recognized_as": orig_name,
                                                      "practice_probe": True})
                refine_res = ink._refine_or_note(
                    agent, sub, native, ag_node, stroke_node, orig_name, majority_sig,
                    segments=wi.dk["segments"], turn_bins=wi.dk["turn_bins"],
                    len_bins=wi.dk["len_bins"], grid=wi.dk["grid"],
                    scale_bins=wi.dk["scale_bins"], category=wi.dk["category"])
                if refine_res is not None and refine_res.get("minted"):
                    corrections.append({"type": "mint_at_instability", "span": i,
                                        "name": refine_res.get("name")})

        # (d) SEGMENTATION-SPLIT INSTABILITY -- NEW: a majority-consistent split is persisted,
        # never discarded (the coordinator's own required fix).
        for i, orig_name in enumerate(orig_names):
            if split_counts[i] > reps_per_item / 2.0:
                node = sc._find_stroke_node(sub, orig_name)
                rate = float(split_counts[i]) / reps_per_item
                if node is not None:
                    sub.set_attr(node, "segmentation_split_prone", True)
                    sub.set_attr(node, "segmentation_split_rate", rate)
                corrections.append({"type": "segmentation_split_instability", "span": i,
                                    "rate": rate})

        # (e) ARRANGEMENT INSTABILITY -- NEW: persisted graph data, an honest additive signal
        # (same "not yet wired to a reader" scope as mechanism (a)'s own `stability_preferred_alt`).
        for i, orig_name in enumerate(orig_names):
            if rel_total[i] == 0:
                continue
            if rel_agree[i] < rel_total[i] / 2.0:
                node = sc._find_stroke_node(sub, orig_name)
                rate = 1.0 - (rel_agree[i] / rel_total[i])
                if node is not None:
                    sub.set_attr(node, "arrangement_unstable", True)
                    sub.set_attr(node, "arrangement_instability_rate", float(rate))
                corrections.append({"type": "arrangement_instability", "span": i, "rate": rate})
        if cpose_total > 0 and cpose_agree < cpose_total / 2.0:
            cur = sub.node(ag_node)["attrs"].get("cpose_instability_events") or 0.0
            sub.set_attr(ag_node, "cpose_instability_events", float(cur) + 1.0)
            corrections.append({"type": "cpose_instability",
                                "rate": 1.0 - cpose_agree / max(1, cpose_total)})

        # AFTER-BABBLE CHECK -- zero-jitter re-render/re-decode/re-compose of the SAME parse,
        # against `ref_sig` (this item's OWN pre-practice zero-jitter canonical reading) --
        # "did the (possibly grown) codebook improve THIS stored parse's own reading."
        after_score = wi.round_trip_score
        after_rendered = _render_spans_per_stroke(native, wi.spans, wi.dk)
        after_stroke_points, after_ok = [], True
        for rp in after_rendered:
            if not rp:
                after_ok = False
                break
            knots_a, res_a = _decode_stroke_full(agent, rp, wi.dk)
            sp_a = cc.decode_result_to_stroke_points(knots_a, res_a)
            if len(sp_a) != 1:
                after_ok = False
                break
            after_stroke_points.extend(sp_a)
        if after_ok and ref_ok:
            after_sig = cc.compose_character_signature(
                native, after_stroke_points, segments=wi.dk["segments"],
                turn_bins=wi.dk["turn_bins"], len_bins=wi.dk["len_bins"], grid=wi.dk["grid"],
                scale_bins=wi.dk["scale_bins"])["signature"]
            trivial_ref_groups = [[(0, 1, nm)] for nm in _composed_names(ref_sig)]
            trivial_after_groups = [[(0, 1, nm)] for nm in _composed_names(after_sig)]
            after_scored = _character_round_trip_score(
                sub, native, trivial_ref_groups, trivial_after_groups, ref_sig, after_sig)
            after_score = after_scored["overall"]

        per_item[wi.item_id] = {"reps": reps_per_item, "corrections": corrections,
                                "round_trip_before": wi.round_trip_score,
                                "round_trip_after": after_score}
        total_corrections += len(corrections)

    return PracticeLog(per_item=per_item, total_corrections=total_corrections)


# --------------------------------------------------------------------------- #
#  7. CYCLE_CHARACTERS -- mark_characters -> assign -> babble_characters -> re-mark_characters.
# --------------------------------------------------------------------------- #
def cycle_characters(agent, char_items: list, *, reps_per_item: int, rng_seed: int,
                     dk: Optional[dict] = None, capacity: Optional[int] = None,
                     jitter_bins: int = DEFAULT_JITTER_BINS,
                     eval_class_ids: Optional[set] = None,
                     enable_character_codebook: bool = False,
                     use_stability_weights: bool = False,
                     use_preferred_parse: bool = False, tolerant_joins: bool = False,
                     junction_frac: float = ar.DEFAULT_JUNCTION_FRAC) -> CycleReport:
    """`assign()` is REUSED UNCHANGED (MarkedItem is grain-agnostic). `mints_during_reading`
    sums `n_mints_reading` over BOTH the pre- and post-babble `mark_characters` passes (both
    are real decode-of-real-ink events -- "reading as practice"). `mints_during_babble` counts
    only corrections that installed a NEW codebook entry (`mint_at_instability`/
    `variant_coverage`) -- kept separate from reading-pass mints per the coordinator's own
    note: decode-side eager-child minting fired BY a babble decode is a reading event carried
    in `n_mints_reading`, never double-counted here as a "correction".

    RUN 28 LEVER 2 (`enable_character_codebook`, default `False`, threaded straight through to
    BOTH `mark_characters` calls -- byte-identical pre-existing behaviour when off):
    `mints_character_reading` sums `n_mints_character_reading` over both passes, the
    ARRANGEMENT-grain twin of `mints_during_reading`.

    RUN 29 (CONSUME) -- `use_stability_weights` (default `False`, byte-identical when off),
    threaded to BOTH `mark_characters` calls: the pre-babble pass scores against whatever
    weights this quantum held BEFORE this cycle (last cycle's `babble_characters`/its own prior
    `mark_characters` calls); the post-babble pass scores against weights THIS cycle's own
    `babble_characters` call (which persists per-rep, see that function's own RUN 29 note) has
    since updated -- so `post_scores`' own arrangement component can move even when the
    underlying geometry hasn't, purely from the codebook's own reliability model improving."""
    marked_before = mark_characters(agent, char_items, dk=dk, eval_class_ids=eval_class_ids,
                                    enable_character_codebook=enable_character_codebook,
                                    use_stability_weights=use_stability_weights,
                                    use_preferred_parse=use_preferred_parse,
                                    tolerant_joins=tolerant_joins, junction_frac=junction_frac)
    worksheet = assign(marked_before, capacity=capacity)
    log = babble_characters(agent, worksheet, reps_per_item=reps_per_item, rng_seed=rng_seed,
                            jitter_bins=jitter_bins, eval_class_ids=eval_class_ids)
    marked_after = mark_characters(agent, char_items, dk=dk, eval_class_ids=eval_class_ids,
                                   enable_character_codebook=enable_character_codebook,
                                   use_stability_weights=use_stability_weights,
                                   use_preferred_parse=use_preferred_parse,
                                   tolerant_joins=tolerant_joins, junction_frac=junction_frac)

    surviving_before = sum(1 for m in marked_before if m.round_trip_score < DEFAULT_MAX_SCORE)
    surviving_after = sum(1 for m in marked_after if m.round_trip_score < DEFAULT_MAX_SCORE)
    mints_during_reading = (sum(m.n_mints_reading for m in marked_before)
                            + sum(m.n_mints_reading for m in marked_after))
    mints_during_babble = sum(
        1 for entry in log.per_item.values() for c in entry["corrections"]
        if c["type"] in ("mint_at_instability", "variant_coverage"))
    mints_character_reading = (sum(m.n_mints_character_reading for m in marked_before)
                               + sum(m.n_mints_character_reading for m in marked_after))
    renders_with_preferred_parse = (sum(m.n_preferred_renders for m in marked_before)
                                    + sum(m.n_preferred_renders for m in marked_after))
    tolerant_join_applications = (sum(m.n_tolerant_joins for m in marked_before)
                                  + sum(m.n_tolerant_joins for m in marked_after))

    return CycleReport(
        pre_scores={m.item_id: m.round_trip_score for m in marked_before},
        post_scores={m.item_id: m.round_trip_score for m in marked_after},
        worksheet_size=len(worksheet.items), corrections=log.total_corrections,
        surviving_residual_count=surviving_after,
        surviving_residual_count_before=surviving_before, practice_log=log,
        mints_during_reading=mints_during_reading, mints_during_babble=mints_during_babble,
        mints_character_reading=mints_character_reading,
        renders_with_preferred_parse=renders_with_preferred_parse,
        tolerant_join_applications=tolerant_join_applications)


__all__ = ["EvalLeakageError", "SpanParse", "MarkedItem", "WorksheetItem", "Worksheet",
           "PracticeLog", "CycleReport", "mark", "assign", "babble", "cycle",
           "mark_characters", "babble_characters", "cycle_characters",
           "DEFAULT_MAX_KNOTS", "DEFAULT_JITTER_BINS", "DEFAULT_MAX_SCORE",
           "count_preferred_renders"]
