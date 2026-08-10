"""relational_variation -- RUN 50 GATE 0's own PART 1 build: the AMORTIZED, background-learned
RELATIONAL-VARIATION prior the launch brief asks for -- "a model of how a class's form VARIES"
(entry 38/49's own framing of BPL's real edge), estimated ONCE from background alphabets via
mechanical statistics (mean/variance per relation slot), never per-decision MCMC/search.

SCOPE (deliberate, documented): this module reads ONLY the ARRANGEMENT relations
`domains/character_compose.py` already composes -- `["rel", k, x_q, y_q, o_q, s_q]` (a stroke's
pose relative to the character's own invariant frame) and `["cpose_x"/"cpose_y"/"cpose_o"/
"cpose_s", v]` (the whole character's own absolute pose) -- NEVER `["strokeq", k, name]` (stroke
IDENTITY). This mirrors `character_compose.assignment_coverage_term`'s own precedent exactly:
that Term's `identity_weight` is tunable down to `0.0` specifically because "the multiset
ablation proves stroke identity is at-chance, so weighting it dilutes the arrangement signal --
identity_weight=0.0 scores ARRANGEMENT ONLY." The candidate layer RUN 50 tests is arrangement
variation, not identity -- so this module is arrangement-only by construction, matching that
precedent's own reasoning rather than re-deriving it.

TWO MECHANICAL STAGES, both plain statistics over already-decoded values (no ranking, no
decision, no live-agent mutation -- pure analysis, the SAME discipline runs 26/36/44/49's own
gate scripts already use for aggregate stats):

  1. `class_slot_variances(...)` -- per BACKGROUND CLASS: align every drawer instance's decoded
     strokes to one reference instance (`domains.relational_variation.align_stroke_points`, a
     thin wrapper over `scripts.jabberwock_omniglot_run36_failures._greedy_stroke_match` -- the
     SAME order/count-robust per-stroke greedy assignment this arc's own contrastive-verdict
     machinery already reuses verbatim), pool the aligned `rel`/`cpose` bin values across every
     matched stroke position and every instance, and return ONE variance number per (class, slot
     type) -- 8 slot types: rel_x/rel_y/rel_o/rel_s, cpose_x/cpose_y/cpose_o/cpose_s. `rel_o`/
     `cpose_o` use CIRCULAR variance (`_circular_spread`, unwrapping every value relative to the
     class's own first observed value via `character_compose._wrap_signed_bin` -- a bin near the
     +/-turn_bins/2 seam must not look maximally different from its neighbour on the other side).

  2. `pool_variation(...)` -- pools the per-class variances (SIMPLE mean across classes -- no
     per-class weighting scheme to fit, the whole point is a MECHANICAL, non-search estimate)
     into ONE class-general variance per slot type, then `slot_weights(...)` converts that into
     a fixed per-slot TIGHTNESS weight (`1 / (var + EPS_VAR)`, normalized to mean 1) -- a tight
     (low-variance, identity-bearing) slot gets a weight above 1, a loose (free-to-vary) slot
     below 1. `tight_loose_split(...)` reports which slots land on which side of the pooled
     median -- "is there structure to learn at all."

THE DISTANCE -- `relational_distance(...)`: a per-candidate scalar, LOWER = the candidate's own
observed arrangement better explains the query's (the SAME "lower is closer" convention
`abs_read.sctps_verdict_term`/`per_stroke_abs.program_score` already use, so it is directly
comparable to -- and, for the orthogonality diagnostic, correlatable against -- the geo_score
this run's own script computes independently). Built from: (a) the mean WEIGHTED bin-mismatch
over every stroke pair the greedy matcher aligned (a mismatch on a slot the background model
found TIGHT costs more than an equal mismatch on a LOOSE slot -- Mahalanobis-in-relation-space,
at the compositional grain rather than the whole-shape/affine grain RUN 44's own version tested
and nulled); (b) the SAME weighted mismatch over the four `cpose_*` slots (one comparison, the
character is one object); (c) a STRUCTURAL term for any stroke the greedy matcher left unmatched
(a stroke-count mismatch is itself arrangement evidence a bin-only comparison would silently
drop) -- weighted by the MEAN of the four rel weights (so one unmatched stroke costs "one
average full-stroke mismatch"), scaled by the unmatched fraction of the total.

FALSY-ZERO DISCIPLINE (the launch brief's own flagged pitfall): TWO separate guards.
  (1) index/bin lookups -- stroke index `k=0` and every quantized bin value (`x_q`/`y_q`/`o_q`/
      `s_q`, all of which legitimately take the value `0`) are looked up with `.get(k)`/dict
      membership and compared with `is not None`, NEVER a bare `if k` / `if value` truthiness
      check -- a stroke-0 or a zero-bin would otherwise be silently dropped as "falsy".
  (2) the greedy matcher itself -- `scripts.jabberwock_omniglot_run36_failures.
      _greedy_stroke_match` computes each pairwise cost as `float(native.evaluate(term, {}) or
      float("nan"))`: a GENUINE zero-cost match (two strokes that are point-for-point identical,
      the exact case a class's own reference instance produces against itself, or two near-
      duplicate strokes across drawers) evaluates to `0.0`, and `0.0 or float("nan")` is `nan` in
      Python -- the real best match is silently coerced to "missing" and can be mis-sorted or
      dropped. `scripts.jabberwock_omniglot_run39_motorplan.greedy_match` already carries the
      fix (`_pointset_cost`: `float(v) if v is not None else float("nan")`, never `or`, plus a
      NaN-last sort key and an explicit `c != c` skip) -- per
      `tests/test_motor_verdict_migrated.py`'s own precedent ("this is a regression guard on the
      REUSE, not a new fix"), `align_stroke_points` below reuses THAT fixed matcher rather than
      run36's own buggy one, normalizing inputs first via run36's own (unaffected)
      `_normalize_glyph`. See
      `tests/test_relational_variation_migrated.py::test_greedy_matcher_keeps_a_genuine_zero_cost_match`.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from domains.character_compose import _wrap_signed_bin
from scripts import jabberwock_omniglot_run36_failures as run36
from scripts import jabberwock_omniglot_run39_motorplan as run39

REL_SLOTS = ("rel_x", "rel_y", "rel_o", "rel_s")
CPOSE_SLOTS = ("cpose_x", "cpose_y", "cpose_o", "cpose_s")
ALL_SLOTS = REL_SLOTS + CPOSE_SLOTS
_CIRCULAR_SLOTS = ("rel_o", "cpose_o")

EPS_VAR = 0.25          # a quarter-bin^2 floor -- prevents a perfectly-tight (var=0) slot from
                         # producing an infinite/unstable weight; documented, not fitted.
STRUCTURAL_UNMATCHED_WEIGHT_UNITS = 1.0   # one unmatched stroke costs "one average rel-slot
                                           # mismatch worth" per unit of unmatched fraction --
                                           # a fixed, documented convention, never tuned.


# --------------------------------------------------------------------------------------------- #
#  EXTRACTION -- mechanical re-packaging of relations a held decode already produced (the same
#  kind of translation `character_compose._stroke_records`/`_cpose_pairs` already perform).
# --------------------------------------------------------------------------------------------- #
def rel_by_k(sig: list) -> dict:
    """`{k: (x_q, y_q, o_q, s_q)}` from a composed signature's own `"rel"` relations. Accepts
    both `list` and `tuple` relation entries (a LIVE `native.evaluate(...)` result surfaces Rust
    sequences as Python `tuple`s -- the same documented gotcha every reader of a composed
    signature in this codebase already guards against)."""
    out = {}
    for r in sig:
        if isinstance(r, (list, tuple)) and r and r[0] == "rel" and len(r) >= 6:
            out[r[1]] = (r[2], r[3], r[4], r[5])
    return out


def cpose_values(sig: list) -> dict:
    """`{"cpose_x": v, ...}` -- only the predicates actually present."""
    out = {}
    for r in sig:
        if isinstance(r, (list, tuple)) and len(r) >= 2 and r[0] in CPOSE_SLOTS:
            out[r[0]] = r[1]
    return out


def stroke_points_only(stroke_points: list) -> list:
    """`gate.decode_char_signature(...)["stroke_points"]` is `[(points, name, fine_child,
    substroke_points), ...]` -- this is exactly the `k`-ordinal input `character_compose.
    compose_character_signature` consumed to produce the `"rel"`/`"strokeq"` relations (SAME
    enumeration order), so aligning THESE point arrays via the greedy matcher yields indices
    directly usable as `rel_by_k`'s own keys. Extracts just the point arrays, order preserved."""
    return [item[0] for item in stroke_points]


# --------------------------------------------------------------------------------------------- #
#  ALIGNMENT -- thin wrapper over run36's own order/count-robust greedy per-stroke assignment.
# --------------------------------------------------------------------------------------------- #
def align_stroke_points(native, ref_points: list, other_points: list) -> dict:
    """Normalize both sides (`run36._normalize_glyph`, unaffected by the falsy-zero bug -- pure
    centre+scale, no cost computation), then align via `run39.greedy_match` (the FIXED matcher,
    see this module's own top-of-file docstring). Returns a run36-`_greedy_stroke_match`-SHAPED
    dict (`matched`: `[(i, j, None), ...]` with `i` indexing `ref_points`, `j` indexing
    `other_points`; `unmatched_true`/`unmatched_pred`; `n_true`/`n_pred`) so every caller below
    is agnostic to which matcher produced it -- the `cost` slot of each `matched` tuple is
    unused downstream (this module never ranks by match cost, only by WHICH strokes correspond),
    kept as `None` rather than re-deriving a value nothing reads."""
    ref_norm, _, _ = run36._normalize_glyph(ref_points)
    other_norm, _, _ = run36._normalize_glyph(other_points)
    mapping = run39.greedy_match(native, ref_norm, other_norm)   # {other_idx: ref_idx}
    used_i = set(mapping.values())
    used_j = set(mapping.keys())
    matched = [(i, j, None) for j, i in mapping.items()]
    unmatched_true = [i for i in range(len(ref_norm)) if i not in used_i]
    unmatched_pred = [j for j in range(len(other_norm)) if j not in used_j]
    return dict(matched=matched, unmatched_true=unmatched_true, unmatched_pred=unmatched_pred,
                n_true=len(ref_norm), n_pred=len(other_norm))


# --------------------------------------------------------------------------------------------- #
#  CIRCULAR SPREAD -- orientation bins wrap; a plain variance would overstate the spread of a
#  tightly-oriented class whose bin values happen to straddle the +/-turn_bins/2 seam.
# --------------------------------------------------------------------------------------------- #
def _circular_spread(values: list, turn_bins: int) -> float:
    """Unwrap every value RELATIVE TO THE FIRST value (`_wrap_signed_bin(v - values[0],
    turn_bins)` -- the SAME modular arithmetic `character_compose._rel2_relations` already uses
    for a signed-bin difference), then return the plain variance of those unwrapped deltas. A
    class whose true orientation sits near the seam (e.g. bins `+5,+6,-6,-5` at `turn_bins=12`)
    unwraps to `{0,+1,0,+1}`-scale deltas (tight), not the raw values' own inflated spread."""
    if len(values) < 2:
        return 0.0
    ref = values[0]
    deltas = [_wrap_signed_bin(v - ref, turn_bins) for v in values]
    return float(np.var(np.asarray(deltas, dtype=float)))


def _spread(values: list, slot: str, turn_bins: int) -> float:
    if slot in _CIRCULAR_SLOTS:
        return _circular_spread(values, turn_bins)
    if len(values) < 2:
        return 0.0
    return float(np.var(np.asarray(values, dtype=float)))


# --------------------------------------------------------------------------------------------- #
#  STAGE 1 -- per-class variance, pooling every matched stroke position and every drawer
#  instance into ONE number per (class, slot type). Pure statistics -- no decision.
# --------------------------------------------------------------------------------------------- #
def class_slot_variances(native, ref_stroke_points: list, ref_sig: list,
                          other_instances: list, turn_bins: int) -> Optional[dict]:
    """`other_instances`: `[(stroke_points, composed_sig), ...]` -- every OTHER drawer's own
    decode of the SAME class (the reference's own decode contributes its `rel`/`cpose` values
    too, folded in as "instance 0" against itself with a trivial identity alignment, so a
    class's own reference doesn't silently drop out of its own pooled statistic). Returns
    `{slot: variance}` for all 8 `ALL_SLOTS`, or `None` if fewer than 2 total instances (nothing
    to estimate a spread from -- an honest skip, never a fabricated 0.0).

    PER-POSITION FIRST, THEN POOL (load-bearing, not a style choice): `rel_*` variance is
    computed WITHIN one reference stroke position `k` across drawers FIRST (`_by_k` below), and
    only those per-position variances are averaged into the class's own `rel_*` number -- pooling
    the RAW values across different `k` directly (before taking a variance) would mix "how much
    this drawer varies" with "stroke 0's own pose differs from stroke 1's own pose", inventing
    spurious variance out of the character's own arrangement rather than measuring drawer-to-
    drawer spread. `cpose_*` has no such position axis (one whole-character value per instance)
    so its raw values pool directly, unchanged."""
    ref_pts = stroke_points_only(ref_stroke_points)
    ref_rel = rel_by_k(ref_sig)
    ref_cpose = cpose_values(ref_sig)

    pooled_rel_by_k: dict = {k: {s: [] for s in REL_SLOTS} for k in ref_rel}
    pooled_cpose: dict = {s: [] for s in CPOSE_SLOTS}

    for k, vals in ref_rel.items():
        for slot, v in zip(REL_SLOTS, vals):
            pooled_rel_by_k[k][slot].append(v)
    for slot, v in ref_cpose.items():
        if v is not None:
            pooled_cpose[slot].append(v)

    n_instances = 1
    for stroke_points, sig in other_instances:
        pts = stroke_points_only(stroke_points)
        if not pts:
            continue
        gm = align_stroke_points(native, ref_pts, pts)
        other_rel = rel_by_k(sig)
        for (i, j, _c) in gm["matched"]:
            vals = other_rel.get(j)
            if vals is None or i not in pooled_rel_by_k:
                continue
            for slot, v in zip(REL_SLOTS, vals):
                pooled_rel_by_k[i][slot].append(v)
        other_cpose = cpose_values(sig)
        for slot, v in other_cpose.items():
            if v is not None:
                pooled_cpose[slot].append(v)
        n_instances += 1

    if n_instances < 2:
        return None

    out = {}
    n_rel_samples = {s: 0 for s in REL_SLOTS}
    for slot in REL_SLOTS:
        per_k_vars = []
        for k, slotmap in pooled_rel_by_k.items():
            vals = slotmap[slot]
            n_rel_samples[slot] += len(vals)
            if len(vals) >= 2:
                per_k_vars.append(_spread(vals, slot, turn_bins))
        out[slot] = float(np.mean(per_k_vars)) if per_k_vars else 0.0
    for slot in CPOSE_SLOTS:
        out[slot] = _spread(pooled_cpose[slot], slot, turn_bins)
    out["_n_instances"] = n_instances
    out["_n_rel_samples"] = n_rel_samples
    return out


# --------------------------------------------------------------------------------------------- #
#  STAGE 2 -- pool per-class variances into ONE class-general number per slot, then weights.
# --------------------------------------------------------------------------------------------- #
def pool_variation(per_class_variances: list) -> dict:
    """Simple mean across classes (no per-class weighting to fit -- deliberately mechanical).
    `per_class_variances`: a list of `class_slot_variances(...)` outputs (`None` entries
    skipped)."""
    rows = [d for d in per_class_variances if d is not None]
    out = {}
    for slot in ALL_SLOTS:
        vals = [d[slot] for d in rows if slot in d]
        out[slot] = float(np.mean(vals)) if vals else EPS_VAR
    out["_n_classes"] = len(rows)
    return out


def slot_weights(pooled_variance: dict) -> dict:
    """`weight[slot] = 1 / (var[slot] + EPS_VAR)`, normalized so the mean weight across the 8
    slots is exactly 1 -- a TIGHT (low-variance) slot's weight sits above 1, a LOOSE slot's
    below 1, on a scale where "one average slot mismatch" costs 1.0 (the unit
    `relational_distance`'s own structural term also uses)."""
    raw = {slot: 1.0 / (pooled_variance[slot] + EPS_VAR) for slot in ALL_SLOTS}
    mean_w = float(np.mean(list(raw.values()))) or 1.0
    return {slot: raw[slot] / mean_w for slot in ALL_SLOTS}


def tight_loose_split(pooled_variance: dict) -> dict:
    """Median split of the 8 pooled variances -- slots AT OR BELOW the median are TIGHT
    (identity-bearing), slots ABOVE are LOOSE (free to vary). Reports both sets plus the raw
    variances, sorted tightest-first -- "is there structure to learn at all" (a flat variance
    profile across all 8 slots would mean no)."""
    ordered = sorted(ALL_SLOTS, key=lambda s: pooled_variance[s])
    med = float(np.median([pooled_variance[s] for s in ALL_SLOTS]))
    tight = [s for s in ordered if pooled_variance[s] <= med]
    loose = [s for s in ordered if pooled_variance[s] > med]
    return {"ordered_tightest_first": ordered, "median_variance": med,
            "tight": tight, "loose": loose,
            "variances": {s: pooled_variance[s] for s in ALL_SLOTS}}


# --------------------------------------------------------------------------------------------- #
#  THE DISTANCE -- relational-variation-WEIGHTED arrangement mismatch. Lower = more similar.
# --------------------------------------------------------------------------------------------- #
def relational_distance(native, query_stroke_points: list, query_sig: list,
                         cand_stroke_points: list, cand_sig: list, weights: dict) -> dict:
    """`weights`: `slot_weights(...)`'s own output (or any `{slot: float}` mapping over
    `ALL_SLOTS` -- the synthetic unit tests pass a hand-built one). Returns `{"r": scalar,
    "n_matched": int, "n_unmatched": int, "mismatch_bits": {...}}` -- `r` is the mean weighted
    rel-slot mismatch bit over every matched stroke pair, PLUS the mean weighted cpose mismatch
    bit, PLUS a structural term for any unmatched stroke (weighted by the mean of the four
    `rel_*` weights, scaled by the unmatched fraction) -- see this module's own top-of-file
    docstring for the full rationale. IDENTITY (`strokeq`) is never read here -- arrangement
    only, by construction (see docstring)."""
    q_pts = stroke_points_only(query_stroke_points)
    c_pts = stroke_points_only(cand_stroke_points)
    q_rel = rel_by_k(query_sig)
    c_rel = rel_by_k(cand_sig)

    gm = align_stroke_points(native, q_pts, c_pts)
    rel_bits: list = []
    for (i, j, _c) in gm["matched"]:
        qv = q_rel.get(i)
        cv = c_rel.get(j)
        if qv is None or cv is None:
            continue
        for slot, a, b in zip(REL_SLOTS, qv, cv):
            mismatch = 1.0 if a != b else 0.0     # exact bin equality -- wrap-agnostic by
                                                   # construction (same bin id or not).
            rel_bits.append(weights[slot] * mismatch)

    q_cpose = cpose_values(query_sig)
    c_cpose = cpose_values(cand_sig)
    cpose_bits = []
    for slot in CPOSE_SLOTS:
        a, b = q_cpose.get(slot), c_cpose.get(slot)
        if a is None or b is None:
            continue
        mismatch = 1.0 if a != b else 0.0
        cpose_bits.append(weights[slot] * mismatch)

    n_unmatched = len(gm["unmatched_true"]) + len(gm["unmatched_pred"])
    n_total_strokes = gm["n_true"] + gm["n_pred"]
    unmatched_frac = (n_unmatched / n_total_strokes) if n_total_strokes else 0.0
    mean_rel_w = float(np.mean([weights[s] for s in REL_SLOTS]))
    structural = STRUCTURAL_UNMATCHED_WEIGHT_UNITS * mean_rel_w * unmatched_frac

    rel_component = float(np.mean(rel_bits)) if rel_bits else 0.0
    cpose_component = float(np.mean(cpose_bits)) if cpose_bits else 0.0
    r = rel_component + cpose_component + structural
    return {"r": r, "n_matched": len(gm["matched"]), "n_unmatched": n_unmatched,
            "rel_component": rel_component, "cpose_component": cpose_component,
            "structural": structural}


__all__ = ["REL_SLOTS", "CPOSE_SLOTS", "ALL_SLOTS", "EPS_VAR",
           "STRUCTURAL_UNMATCHED_WEIGHT_UNITS", "rel_by_k", "cpose_values",
           "stroke_points_only", "align_stroke_points", "class_slot_variances",
           "pool_variation", "slot_weights", "tight_loose_split", "relational_distance"]
