"""spatial_priors — RUN 21's LEARNED SPATIAL PRIORS lever (scratchpad/HANDWRITING_DESIGN.md does
not carry a "RUN 21" section by name; the design is commit 5bca81be's own closing paragraph:
"the next move on the 96.7 road is LEARNED SPATIAL PRIORS layered ON the winning arm (mine the
background LEARN decodes for rel/position statistics; prior enters the marginal verdict as a
held term; priors learned from background data ONLY)" — the FIRST lever this arc has aimed at
the WINNING verdict (`domains.abs_read.parse_marginal_verdict`, 79-80.5% across runs 17b/19/20)
rather than at one of its falsified rivals (token-refit, run 19/20).

THE IDEA (BPL's own "along/at-start/at-end" part-position models, EARNED here rather than
hand-specified): a stroke QUANTUM (one of the earned `ShapeSignature{kind:"stroke"}` codebook
entries, the SAME 7-quantum vocabulary `stroke_codebook`/`ink_decode`/`character_compose` already
share) tends to appear at CHARACTER-EXTRINSIC positions/orientations more often than others —
where does a "long straight stroke" USUALLY sit in a character's own normalized frame, and where
does the stroke that comes AFTER it usually land relative to it? Both questions are answered by
mining the SAME `character_compose.compose_character_signature` "rel" relations
(`["rel", k, dx_q, dy_q, do_q, ds_q]`, already-quantized, already keyed by stroke quantum
identity via the co-emitted "strokeq" relations) over BACKGROUND characters — the SAME 5
background alphabets `stroke_codebook`'s own LEARN pass earns the stroke vocabulary from
(hygiene: mining reads ONLY `omniglot_world.characters(alphabet, MINE_SPLIT)` with
`MINE_SPLIT = "background"`, a module CONSTANT never a caller-supplied flag, asserted at
runtime by every caller exactly as `scripts/jabberwock_omniglot_run17_close.py`'s own
tuning/test disjointness assertion) — never the evaluation/test split.

TWO EARNED DISTRIBUTIONS (both per-DIMENSION marginals, not a single joint bin — the joint bin
space at this codebook's own `grid`x`grid`x`turn_bins`x`scale_bins` resolution is far sparser
than the mined sample count would ever populate meaningfully; per-dimension categorical
histograms are the honest, tractable EARNED model BPL's own per-part positional distributions
also factor as, and every histogram is reported with its own peakedness/coverage diagnostic
BEFORE any accuracy number is read, per the standing "intermediate gate" discipline):

  POSITION  — per stroke-quantum NAME, four independent histograms over its OWN "rel" bins
              (`dx_q`, `dy_q`, `do_q`, `ds_q` — where does THIS quantum sit in the character's
              own normalized frame, pooled over every background character it appears in).
  TRANSITION — per stroke-quantum NAME (the PRECEDING stroke's identity, draw order), four
              independent histograms over the delta-to-its-successor's own "rel" bins
              (`ddx_q`, `ddy_q`, `ddo_q`, `dds_q` — mechanically DERIVED from two already-
              quantized "rel" pose tuples via the SAME arithmetic `character_compose.
              _rel2_relations` already uses for its own non-adjacent pairs, here applied to
              ADJACENT pairs instead — no new geometry, no second `StrokeQuantize` call).

Both tables are Laplace-smoothed categorical distributions (`_logprob`), keyed by stroke-quantum
IDENTITY so a genuinely UNSEEN identity (should not occur at scoring time — every candidate's
strokes are drawn from the SAME earned codebook the tables are keyed on) falls back to a POOLED
GLOBAL marginal (`_global_histograms`) rather than a fabricated zero-count table — an honest
non-crash, never a fake number.

PERSISTENCE (CLAUDE.md's "teach" facility, "seed byproduct expected" per the design): the mined
histograms are `teach()`-installed as `SpatialPrior` graph nodes (`persist_spatial_priors`,
category `"spatial_priors"`, one node per (kind, quantum-name) pair — 2 kinds x however many
quanta the LEARN pass earned, ~14 nodes at this codebook's own 7-quantum size) — GRAPH DATA the
agent HOLDS, not a Python dict the host keeps alive; `load_spatial_priors` reads them straight
back off the graph (a mechanical query, the SAME `s.nodes(type)` + `json.loads(attr)` idiom
`writer_report`/`_candidate_seg` already use elsewhere in this codebase) for scoring.

THE VERDICT (held Term, no new decision procedure): `arrangement_log_prior` is a MECHANICAL
staging value (see `HANDWRITING_DESIGN.md`'s own launch note for this run: "precomputed-per-
candidate as staged data if Term composition is too heavy... the DECISION stays the held
Argmin") — one candidate's own composed signature's `strokeq`/`rel` relations, looked up against
the mined histograms and SUMMED (log-domain, so independence across dimensions/strokes composes
by addition) into ONE Python float. This is staging, not a decision: no candidate is compared to
another, no branching happens on the VALUE, it is simply computed once per candidate exactly as
`_earned_parts_from_stroke_points`/`_rich_parts` (abs_read.py, run 19) already compute plain
Python data ingredients for a downstream held Term. `spatial_prior_plus_marginal_term` composes
that value into the SAME held-Term shape `abs_read.joined_refit_marginal_term` (run 20) already
established for combining a graph-staged score with a bare-Python one: `Plus([base_error_term,
Times([Lit(-lambda), Lit(log_prior_value)])])` — `base_error_term` is
`abs_read.parse_marginal_pair_error_term` (run 20's own per-pair exposure of the WINNING verdict's
fused error, reused VERBATIM) in the real gate, or any stand-in `Lit` in a synthetic gate that
wants to hold the base error FIXED (a controlled TIE) to isolate the prior's own separating
power. `lambda=0.0` multiplies the log-prior contribution by exactly zero (`Times(Lit(0.0), ...)`
is the numeric identity regardless of the log-prior's own value) — BYTE-IDENTICAL to
`base_error_term` alone, the additivity/control-reproduction discipline every lever in this arc
has followed. The final pick is `spatial_prior_marginal_rerank`'s held `Argmin`
(`abs_read._argmin_pairs_term`, the SAME idiom every rerank in this codebase already uses) over
the per-candidate combined scores — never a Python min/sort/argmin."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from domains import abs_read as ar
from domains import character_compose as cc
from domains import ink_decode as ink
from domains import omniglot_world as ow
from domains.stroke_codebook import _native, _quantize, _sub, _teach_agent
from domains.teach import SEEDS as _DEFAULT_TEACH_SEEDS
from domains.teach import teach

CATEGORY = "spatial_priors"
MINE_SPLIT = "background"          # hygiene: a MODULE CONSTANT, never a caller-supplied flag —
                                    # mining reads ONLY this split, asserted at every call site.
DIMS = ("dx", "dy", "do", "ds")
DEFAULT_PRIOR_ALPHA = 1.0          # Laplace smoothing pseudo-count — unit, not tuned.
DEFAULT_PRIOR_LAMBDA = 1.0         # unit weight, tried FIRST per the launch instructions.

# --------------------------------------------------------------------------- #
#  RUN 22 — FINE-KEYED CONDITIONING (git show -s d46ac9b3, run 21's diagnosis): the position/
#  transition tables above are keyed on `strokeq` — the COARSE/MATCHED quantum identity — and
#  run 21 found that key collapses to ONE value (14,675/14,676 background observations shared
#  a single identity), so the learned prior degenerates to flat + a spurious spike. The
#  committed fix (run 6's own matching/identity split, restated in run 21's own commit message):
#  MATCHING stays coarse (untouched — no change to `ink_decode`/`stroke_codebook`/
#  `character_compose`, none of which this module touches), but CONDITIONING keys on a FINE
#  identity instead — every decoded stroke's own SUB-FINE invariant `StrokeQuantize` signature
#  (the SAME `SUBFINE_TURN_BINS`/`SUBFINE_LEN_BINS` ladder rung `stroke_codebook.py`'s "EAGER
#  CHILD MINTING" section already found carries genuine, BOUNDED within-family variation — "the
#  dominant real stroke family... resolved to only 6 DISTINCT sub-fine signatures"), content-
#  hashed the SAME way `ink_decode._signature_key`/`character_compose.substroke_arrangement_key`
#  already hash a signature into a stable name. Fine identity does NOT gate recognition (a
#  stroke recognized as coarse quantum "line" is STILL "line" for `strokeq`/matching purposes,
#  byte-identically) — it only ever selects WHICH conditioning table a lookup consults — so the
#  run-5 fragmentation law (finer BASE grain hurts MATCHING) does not apply to it.
#
#  Every new function below is ADDITIVE: `mine_spatial_priors`/`persist_spatial_priors`/
#  `load_spatial_priors`/`arrangement_log_prior`/`spatial_prior_marginal_rerank` (run 21, keyed
#  on the coarse `strokeq` identity) are UNCHANGED, byte-for-byte, and remain the CONTROL/
#  coarse-only comparison point; `_accumulate_character_stats` grows exactly one new OPTIONAL
#  kwarg (`identity_by_k`, default `None` reproducing the pre-existing `strokeq`-keyed behaviour
#  exactly) so the SAME counting primitive serves both grains without duplication.
# --------------------------------------------------------------------------- #
CATEGORY_FINE = "spatial_priors_fine"
FINE_MIN_OBS = 10                  # pre-registered (run-22 launch instructions): a fine
                                    # identity's OWN table is trusted only once it has this many
                                    # background observations; below that, a lookup backs off
                                    # to the coarse table (run 21's), then the pooled global —
                                    # a BACKOFF LEVEL decision, not the Laplace `alpha` smoothing
                                    # (a separate, already-existing concern) and not tuned.
MIN_DISTINCT_FINE_KEYS = 20         # pre-registered branch: STOP (no accuracy arm) if fewer
                                    # than this many distinct fine keys carry >= FINE_MIN_OBS
                                    # background observations.
MIN_MEAN_PEAKEDNESS = 0.15          # pre-registered branch: STOP if mean per-identity
                                    # peakedness (dx/dy/do dims) stays below this.
MIN_TEST_COVERAGE = 0.30            # pre-registered branch: STOP if fewer than this fraction
                                    # of TEST-time decoded strokes have a matching fine key with
                                    # >= FINE_MIN_OBS background observations.


# --------------------------------------------------------------------------- #
#  MINING — mechanical statistics gathering over BACKGROUND decode results (no agent decision:
#  a plain counting pass, the SAME kind of mechanical aggregation `run_learn`'s own growth-curve
#  bookkeeping already performs over the LEARN pass's decode results).
# --------------------------------------------------------------------------- #
def _rel_maps(composed_sig: list) -> tuple[dict, dict]:
    """Mechanical extraction (mirrors `abs_read._strokeq_map`/`_rel_map`, duplicated locally
    per this codebase's own small-pure-call-site-local-builder convention) of ONE composed
    character signature's `strokeq`/`rel` relations, keyed by draw-order ordinal `k`."""
    strokeq, rel = {}, {}
    for r in composed_sig:
        if not r:
            continue
        if r[0] == "strokeq":
            strokeq[r[1]] = r[2]
        elif r[0] == "rel":
            rel[r[1]] = (r[2], r[3], r[4], r[5])
    return strokeq, rel


def _decode_character_stroke_points(s, dk: dict, path: str) -> list:
    """Mechanical ingest+decode of ONE character file's every pen-down stroke — the SAME
    per-stroke `ink.ingest_ink`/`ink.decode_ink` loop
    `scripts/jabberwock_omniglot_dynamic_quantization.decode_char_signature` already performs
    (here WITHOUT `enable_substroke` — mining only needs the outer stroke-grain `strokeq`/`rel`
    relations, not the within-stroke inner lattice, so the substroke lattice is skipped for
    speed; a purely mechanical omission, not a behaviour change to the outer decode). Returns
    the draw-order `(points, identity_name[, fine_child])` sequence
    `character_compose.compose_character_signature` accepts."""
    stroke_points: list = []
    for st in ow.load_strokes(path):
        if st.shape[0] < 2:
            continue
        ink_node = ink.ingest_ink(s, st.tolist(), max_knots=dk["max_knots"])
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"],
                              scale_bins=dk["scale_bins"])
        knots = s.node(ink_node)["attrs"].get("knots") or []
        stroke_points.extend(cc.decode_result_to_stroke_points(knots, res))
    return stroke_points


def _accumulate_character_stats(composed_sig: list, position_counts: dict, position_totals: dict,
                                 transition_counts: dict, transition_totals: dict,
                                 turn_bins: int, identity_by_k: Optional[dict] = None) -> None:
    """THE pure counting step (mechanical, no decision) — factored out of `mine_spatial_priors`'s
    own file-walking loop so it is directly unit-testable on hand-built synthetic composed
    signatures (`tests/test_spatial_priors_migrated.py`), the SAME "Omniglot stays a scripts/
    gate, pytest is synthetic" discipline every other decode module in this codebase follows.
    Mutates the four accumulator dicts in place (`defaultdict(lambda: {d: defaultdict(int) for
    d in DIMS})` shape for the `*_counts` dicts, plain `defaultdict(int)` for the `*_totals`).

    `identity_by_k` (RUN 22, optional — every pre-existing call site keeps its byte-identical
    default `None`, keying on the composed signature's own `strokeq` relation exactly as
    before): a caller-supplied `{k: identity_name}` map that OVERRIDES the identity a draw-order
    ordinal `k` is counted under — `mine_spatial_priors_fine` passes each stroke's own FINE
    (sub-fine-signature-content-hashed) identity here instead of the coarse `strokeq` name,
    reusing this SAME counting arithmetic unchanged. `rel`'s own bin values (the THING being
    counted) are always read off the composed signature exactly as before; only WHICH KEY a
    stroke's counts are pooled under changes."""
    strokeq, rel = _rel_maps(composed_sig)
    ks = sorted(rel)
    for k in ks:
        name = identity_by_k.get(k) if identity_by_k is not None else strokeq.get(k)
        if name is None:
            continue
        dx, dy, do, ds = rel[k]
        position_counts[name]["dx"][dx] += 1
        position_counts[name]["dy"][dy] += 1
        position_counts[name]["do"][do] += 1
        position_counts[name]["ds"][ds] += 1
        position_totals[name] += 1
    for a, b in zip(ks, ks[1:]):
        name_i = identity_by_k.get(a) if identity_by_k is not None else strokeq.get(a)
        if name_i is None:
            continue
        dxa, dya, doa, dsa = rel[a]
        dxb, dyb, dob, dsb = rel[b]
        transition_counts[name_i]["dx"][dxb - dxa] += 1
        transition_counts[name_i]["dy"][dyb - dya] += 1
        transition_counts[name_i]["do"][cc._wrap_signed_bin(dob - doa, turn_bins)] += 1
        transition_counts[name_i]["ds"][dsb - dsa] += 1
        transition_totals[name_i] += 1


def _fine_identity_key(native, points: list, coarse_name: str, *, segments: int, grid: int,
                        scale_bins: int, subfine_turn_bins: int = ink.SUBFINE_TURN_BINS,
                        subfine_len_bins: int = ink.SUBFINE_LEN_BINS) -> str:
    """RUN 22's FINE identity key: ONE stroke's own SUB-FINE (`SUBFINE_TURN_BINS`/
    `SUBFINE_LEN_BINS` — one ladder step finer than the fine grain matching uses)
    INVARIANT-ONLY `StrokeQuantize` signature (rotation/translation/scale-invariant SHAPE only
    — never pose, so identity never conflates with the very position being modelled), content-
    hashed via the SAME `ink_decode._signature_key` convention `character_compose.
    substroke_arrangement_key` and the OOV-mint path already use for stable, content-derived
    names. Computed DIRECTLY from the stroke's own raw points (a plain `StrokeQuantize`
    evaluate — pure geometry, no graph mutation, no dependency on whether an eager-child mint
    happened to fire/persist for this exact occurrence during decode), so the SAME stroke
    instance always yields the SAME key regardless of decode order or codebook-epoch state.
    Prefixed with `coarse_name` (the stroke's OWN matched top-level quantum — never a decision,
    just the identity `ink_decode`'s ladder already resolved) purely to keep keys human-legible
    and to make cross-family hash collisions structurally impossible (astronomically unlikely
    with a 12-hex-digit sha1 prefix regardless, but free to rule out entirely)."""
    q = _quantize(native, points, segments=segments, turn_bins=subfine_turn_bins,
                  len_bins=subfine_len_bins, grid=grid, scale_bins=scale_bins,
                  invariant_only=True)
    return f"{coarse_name}::{ink._signature_key(q['signature'])}"


def mine_spatial_priors(agent, dk: dict, alphabets: list[str], drawers: list[str], *,
                         max_chars_per_alphabet: Optional[int] = None) -> dict[str, Any]:
    """THE miner: for every (alphabet, character, drawer) in the BACKGROUND split (hygiene
    asserted below), decode the character (`_decode_character_stroke_points`) and compose its
    signature (`character_compose.compose_character_signature`, the SAME machinery every other
    Omniglot run's `decode_char_signature` already calls) — then accumulate two per-dimension
    count tables (POSITION, TRANSITION, see this module's own top-of-file docstring). Purely
    mechanical: a counting pass over already-decoded, already-quantized relations a HELD
    `StrokeQuantize`/`ShapeDecode` evaluate already produced — no ranking, no decision.

    `alphabets` MUST be a subset of `omniglot_world.alphabets(MINE_SPLIT)` — asserted here
    (the hygiene gate: background data ONLY), never silently coerced."""
    valid_bg = set(ow.alphabets(MINE_SPLIT))
    assert set(alphabets) <= valid_bg, (
        f"mine_spatial_priors hygiene violation: {sorted(set(alphabets) - valid_bg)} are not "
        f"{MINE_SPLIT!r}-split alphabets — spatial priors must be mined from background data "
        f"ONLY (never evaluation/test).")

    s = _sub(agent)
    turn_bins = dk["turn_bins"]
    position_counts: dict = defaultdict(lambda: {d: defaultdict(int) for d in DIMS})
    position_totals: dict = defaultdict(int)
    transition_counts: dict = defaultdict(lambda: {d: defaultdict(int) for d in DIMS})
    transition_totals: dict = defaultdict(int)
    n_chars = 0

    for alph in alphabets:
        chars = ow.characters(alph, MINE_SPLIT)
        if max_chars_per_alphabet:
            chars = chars[:max_chars_per_alphabet]
        for cdir in chars:
            files_by_drawer: dict = {}
            for f in ow.drawings(cdir):
                d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
                files_by_drawer[d] = f
            for d in drawers:
                f = files_by_drawer.get(d)
                if f is None:
                    continue
                stroke_points = _decode_character_stroke_points(s, dk, f)
                if not stroke_points:
                    continue
                composed = cc.compose_character_signature(
                    _native(agent), stroke_points, segments=dk["segments"],
                    turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
                    scale_bins=dk["scale_bins"])
                _accumulate_character_stats(composed["signature"], position_counts,
                                             position_totals, transition_counts,
                                             transition_totals, turn_bins)
                n_chars += 1

    return {
        "position_counts": {n: {d: dict(c) for d, c in dm.items()} for n, dm in position_counts.items()},
        "position_totals": dict(position_totals),
        "transition_counts": {n: {d: dict(c) for d, c in dm.items()} for n, dm in transition_counts.items()},
        "transition_totals": dict(transition_totals),
        "n_chars": n_chars,
        "turn_bins": turn_bins,
        "grid": dk["grid"],
        "scale_bins": dk["scale_bins"],
    }


def _plain_counts(counts: dict) -> dict:
    return {n: {d: dict(c) for d, c in dm.items()} for n, dm in counts.items()}


def mine_spatial_priors_fine(agent, dk: dict, alphabets: list[str], drawers: list[str], *,
                              max_chars_per_alphabet: Optional[int] = None) -> dict[str, Any]:
    """RUN 22's miner: the SAME (alphabet, character, drawer) walk `mine_spatial_priors` performs
    (byte-identical hygiene assertion, byte-identical file selection), but for EACH decoded
    background stroke ALSO computes its own FINE identity (`_fine_identity_key`, this module's
    own top-of-file "RUN 22" section) and accumulates a SECOND pair of (position, transition)
    tables keyed on THAT instead of the coarse `strokeq` name — via the SAME
    `_accumulate_character_stats` counting primitive, just passed a per-character
    `identity_by_k` override. Decodes EACH background character exactly ONCE (no doubled decode
    cost): the coarse table (byte-identical to what `mine_spatial_priors` alone would produce
    over the same inputs — the run's own CONTROL-reproduction cross-check) and the fine table
    are both accumulated off that ONE decode's `composed_sig`.

    Returns `{"fine": {...}, "coarse": {...}, "n_chars", "turn_bins", "grid", "scale_bins"}` —
    `"fine"` additionally carries `"fine_to_coarse"` (a `{fine_key: coarse_name}` map, mechanical
    provenance/diagnostics bookkeeping — which coarse family each fine key belongs to, never
    used to make a decision, only to report/backoff)."""
    valid_bg = set(ow.alphabets(MINE_SPLIT))
    assert set(alphabets) <= valid_bg, (
        f"mine_spatial_priors_fine hygiene violation: {sorted(set(alphabets) - valid_bg)} are "
        f"not {MINE_SPLIT!r}-split alphabets — spatial priors must be mined from background "
        f"data ONLY (never evaluation/test).")

    s = _sub(agent)
    native = _native(agent)
    turn_bins = dk["turn_bins"]
    fine_position_counts: dict = defaultdict(lambda: {d: defaultdict(int) for d in DIMS})
    fine_position_totals: dict = defaultdict(int)
    fine_transition_counts: dict = defaultdict(lambda: {d: defaultdict(int) for d in DIMS})
    fine_transition_totals: dict = defaultdict(int)
    coarse_position_counts: dict = defaultdict(lambda: {d: defaultdict(int) for d in DIMS})
    coarse_position_totals: dict = defaultdict(int)
    coarse_transition_counts: dict = defaultdict(lambda: {d: defaultdict(int) for d in DIMS})
    coarse_transition_totals: dict = defaultdict(int)
    fine_to_coarse: dict = {}
    n_chars = 0

    for alph in alphabets:
        chars = ow.characters(alph, MINE_SPLIT)
        if max_chars_per_alphabet:
            chars = chars[:max_chars_per_alphabet]
        for cdir in chars:
            files_by_drawer: dict = {}
            for f in ow.drawings(cdir):
                d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
                files_by_drawer[d] = f
            for d in drawers:
                f = files_by_drawer.get(d)
                if f is None:
                    continue
                stroke_points = _decode_character_stroke_points(s, dk, f)
                if not stroke_points:
                    continue
                composed = cc.compose_character_signature(
                    native, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
                    len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
                identity_by_k: dict = {}
                for k, item in enumerate(stroke_points):
                    pts, coarse_name = item[0], item[1]
                    fine_name = _fine_identity_key(native, pts, coarse_name,
                                                    segments=dk["segments"], grid=dk["grid"],
                                                    scale_bins=dk["scale_bins"])
                    identity_by_k[k] = fine_name
                    fine_to_coarse[fine_name] = coarse_name
                _accumulate_character_stats(composed["signature"], fine_position_counts,
                                             fine_position_totals, fine_transition_counts,
                                             fine_transition_totals, turn_bins,
                                             identity_by_k=identity_by_k)
                _accumulate_character_stats(composed["signature"], coarse_position_counts,
                                             coarse_position_totals, coarse_transition_counts,
                                             coarse_transition_totals, turn_bins)
                n_chars += 1

    return {
        "fine": {
            "position_counts": _plain_counts(fine_position_counts),
            "position_totals": dict(fine_position_totals),
            "transition_counts": _plain_counts(fine_transition_counts),
            "transition_totals": dict(fine_transition_totals),
            "fine_to_coarse": dict(fine_to_coarse),
        },
        "coarse": {
            "position_counts": _plain_counts(coarse_position_counts),
            "position_totals": dict(coarse_position_totals),
            "transition_counts": _plain_counts(coarse_transition_counts),
            "transition_totals": dict(coarse_transition_totals),
        },
        "n_chars": n_chars, "turn_bins": turn_bins, "grid": dk["grid"],
        "scale_bins": dk["scale_bins"],
    }


# --------------------------------------------------------------------------- #
#  PERSIST / LOAD — teach() facility (CLAUDE.md: "the ONE recurring facility"), category
#  "spatial_priors" — a seed byproduct, exactly the `character_shapes.json` precedent.
# --------------------------------------------------------------------------- #
def persist_spatial_priors(agent, mined: dict[str, Any], *, category: str = CATEGORY,
                            seeds_dir: Optional[Path] = None) -> dict[str, Any]:
    """Install every (kind, name) histogram as ONE `SpatialPrior` node — mirrors
    `character_compose.grow_character_quantum`'s own `teach()`-persist idiom. Idempotent by
    `teach`'s own (type, attrs) dedup — re-mining IDENTICAL data is a no-op. `seeds_dir`
    (optional, forwarded straight to `teach()`) lets a caller (a test) redirect the seed-
    manifest WRITE away from the real checked-in `seeds/` directory — the SAME isolation
    `tests/test_character_composition_migrated.py`'s own `_add_stroke_node_hermetic` note
    documents needing (`teach()`'s own default `seeds_dir=teach.SEEDS` would otherwise leak
    test-only histograms into the real, checked-in `seeds/spatial_priors.json`)."""
    kw = {"seeds_dir": seeds_dir if seeds_dir is not None else _DEFAULT_TEACH_SEEDS}
    tagent = _teach_agent(agent)
    installed = 0
    for name, dims in mined["position_counts"].items():
        attrs = {"kind": "position", "name": name, "histograms": json.dumps(dims),
                 "total": mined["position_totals"].get(name, 0)}
        teach(tagent, "SpatialPrior", attrs, category=category, **kw)
        installed += 1
    for name, dims in mined["transition_counts"].items():
        attrs = {"kind": "transition", "name": name, "histograms": json.dumps(dims),
                 "total": mined["transition_totals"].get(name, 0)}
        teach(tagent, "SpatialPrior", attrs, category=category, **kw)
        installed += 1
    return {"installed": installed}


def load_spatial_priors(agent) -> dict[str, Any]:
    """Mechanical read-back (mirrors `writer_report`'s own `s.nodes(type)` + attr-read idiom):
    every `SpatialPrior` node the graph currently holds, re-assembled into the SAME nested-dict
    shape `mine_spatial_priors` returns (minus `n_chars`/`turn_bins` bookkeeping), plus the
    pooled GLOBAL fallback histograms (`_global_histograms`) an unseen identity falls back to."""
    s = _sub(agent)
    position_counts, position_totals = {}, {}
    transition_counts, transition_totals = {}, {}
    for n in s.nodes("SpatialPrior"):
        at = s.node(n)["attrs"]
        try:
            hist = json.loads(at.get("histograms") or "{}")
        except (TypeError, ValueError):
            continue
        hist = {dim: {int(k): v for k, v in bins.items()} for dim, bins in hist.items()}
        name = at.get("name")
        total = int(at.get("total") or 0)
        if at.get("kind") == "position":
            position_counts[name] = hist
            position_totals[name] = total
        elif at.get("kind") == "transition":
            transition_counts[name] = hist
            transition_totals[name] = total
    return {
        "position_counts": position_counts, "position_totals": position_totals,
        "transition_counts": transition_counts, "transition_totals": transition_totals,
        "_position_global": _global_histograms(position_counts),
        "_transition_global": _global_histograms(transition_counts),
    }


def persist_spatial_priors_fine(agent, mined_fine: dict[str, Any], *, category: str = CATEGORY_FINE,
                                 seeds_dir: Optional[Path] = None) -> dict[str, Any]:
    """RUN 22's fine-keyed twin of `persist_spatial_priors` — installs `mined_fine`
    (`mine_spatial_priors_fine`'s own `"fine"` sub-dict) as `SpatialPrior` nodes tagged
    `kind="position_fine"`/`"transition_fine"` (a DIFFERENT `kind` value from the coarse
    `"position"`/`"transition"` nodes `persist_spatial_priors` writes — `load_spatial_priors`'s
    own kind-dispatch loop already ignores any kind it doesn't recognise, so the two families
    coexist on the SAME `SpatialPrior` node type with zero collision risk) plus a `coarse_name`
    provenance attr (`mined_fine["fine_to_coarse"]`, mechanical bookkeeping only — never read
    to make a decision, only for backoff/reporting)."""
    kw = {"seeds_dir": seeds_dir if seeds_dir is not None else _DEFAULT_TEACH_SEEDS}
    tagent = _teach_agent(agent)
    installed = 0
    f2c = mined_fine.get("fine_to_coarse", {})
    for name, dims in mined_fine["position_counts"].items():
        attrs = {"kind": "position_fine", "name": name, "histograms": json.dumps(dims),
                 "total": mined_fine["position_totals"].get(name, 0),
                 "coarse_name": f2c.get(name, "")}
        teach(tagent, "SpatialPrior", attrs, category=category, **kw)
        installed += 1
    for name, dims in mined_fine["transition_counts"].items():
        attrs = {"kind": "transition_fine", "name": name, "histograms": json.dumps(dims),
                 "total": mined_fine["transition_totals"].get(name, 0),
                 "coarse_name": f2c.get(name, "")}
        teach(tagent, "SpatialPrior", attrs, category=category, **kw)
        installed += 1
    return {"installed": installed}


def load_spatial_priors_fine(agent) -> dict[str, Any]:
    """Mechanical read-back twin of `load_spatial_priors`, scoped to `kind in {"position_fine",
    "transition_fine"}` — NO global-fallback histograms of its OWN (a fine identity's backoff
    target is the COARSE table, `load_spatial_priors`'s own output, not a fine-level global
    pool — `arrangement_log_prior_fine` takes both dicts explicitly and does the ladder)."""
    s = _sub(agent)
    position_counts, position_totals = {}, {}
    transition_counts, transition_totals = {}, {}
    fine_to_coarse: dict = {}
    for n in s.nodes("SpatialPrior"):
        at = s.node(n)["attrs"]
        kind = at.get("kind")
        if kind not in ("position_fine", "transition_fine"):
            continue
        try:
            hist = json.loads(at.get("histograms") or "{}")
        except (TypeError, ValueError):
            continue
        hist = {dim: {int(k): v for k, v in bins.items()} for dim, bins in hist.items()}
        name = at.get("name")
        total = int(at.get("total") or 0)
        if at.get("coarse_name"):
            fine_to_coarse[name] = at["coarse_name"]
        if kind == "position_fine":
            position_counts[name] = hist
            position_totals[name] = total
        else:
            transition_counts[name] = hist
            transition_totals[name] = total
    return {"position_counts": position_counts, "position_totals": position_totals,
            "transition_counts": transition_counts, "transition_totals": transition_totals,
            "fine_to_coarse": fine_to_coarse}


def _global_histograms(counts_by_name: dict) -> dict:
    """Mechanical pooling (not a decision) — the fallback marginal an identity ABSENT from the
    mined table falls back to (should not occur at scoring time, since a candidate's own
    strokes are always drawn from the SAME earned codebook the tables are keyed by; an honest
    non-crash floor, never a fabricated zero-count table)."""
    out = {d: defaultdict(int) for d in DIMS}
    for dims in counts_by_name.values():
        for d, hist in dims.items():
            for b, c in hist.items():
                out[d][b] += c
    return {d: dict(h) for d, h in out.items()}


# --------------------------------------------------------------------------- #
#  DIAGNOSTICS — "how peaked are the learned distributions" (design: "report entropy/coverage
#  of the mined statistics BEFORE reading accuracy"). Pure read-only reporting, no decision.
# --------------------------------------------------------------------------- #
def _entropy_bits(hist: dict, total: int) -> float:
    if total <= 0:
        return 0.0
    h = 0.0
    for c in hist.values():
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log2(p)
    return h


def prior_diagnostics(priors: dict[str, Any], *, dims: tuple = DIMS) -> dict[str, Any]:
    """Per-(kind, name, dim) sample count + Shannon entropy (bits) + distinct-bin coverage —
    a FLAT prior (entropy near log2(distinct observed bins), every bin near-equally likely)
    cannot help the verdict; a PEAKED one (low entropy relative to its own observed-bin count)
    carries real position/transition signal. Reported per the design's own "intermediate gate"
    discipline: read this BEFORE the accuracy numbers, not after.

    `dims` (RUN 22, optional, default `DIMS` — every pre-existing call keeps its byte-identical
    behaviour): restrict which of the four rel dims are scanned/pooled into `mean_peakedness` —
    the run-22 branch's own pre-registered wording names "dx/dy/do" specifically (excluding
    `ds`, scale), so its caller passes `dims=("dx","dy","do")`; this is a pure FILTER over which
    rows are computed/averaged, never a different computation."""
    rows = []
    for kind, counts, totals in (("position", priors["position_counts"], priors["position_totals"]),
                                  ("transition", priors["transition_counts"], priors["transition_totals"])):
        for name, dm in counts.items():
            total = totals.get(name, 0)
            for d in dims:
                hist = dm.get(d, {})
                n_bins = len(hist)
                ent = _entropy_bits(hist, total)
                max_ent = math.log2(n_bins) if n_bins > 1 else 0.0
                rows.append({"kind": kind, "name": name, "dim": d, "total": total,
                             "distinct_bins": n_bins, "entropy_bits": round(ent, 3),
                             "max_entropy_bits": round(max_ent, 3),
                             "peakedness": round(1.0 - (ent / max_ent), 3) if max_ent > 0 else 1.0})
    return {"rows": rows,
            "mean_peakedness": (sum(r["peakedness"] for r in rows) / len(rows)) if rows else 0.0,
            "mean_total_samples": (sum(r["total"] for r in rows) / len(rows)) if rows else 0.0}


# --------------------------------------------------------------------------- #
#  RUN 22 — FINE-IDENTITY DIAGNOSTICS (the "intermediate gate" this run's launch instructions
#  add on top of `prior_diagnostics`'s existing peakedness report): identity DIVERSITY (how
#  many distinct fine keys, and how many carry enough observations to be trusted) and TEST-time
#  RECALL (what fraction of held-out strokes actually land on a well-observed fine key) — both
#  read BEFORE any accuracy number, exactly like `prior_diagnostics`.
# --------------------------------------------------------------------------- #
def fine_identity_diagnostics(mined_fine: dict[str, Any], *,
                               min_obs: int = FINE_MIN_OBS) -> dict[str, Any]:
    """Identity-DIVERSITY report over `mined_fine["position_counts"]`'s own key population
    (the transition table shares the same key space, keyed on the PREDECESSOR's fine identity)
    — the direct numeric answer to "did fine-keying actually break run 21's ONE-identity
    collapse" (run 21's own diagnostic: 14,675/14,676 background observations shared a single
    coarse identity; this reports the SAME kind of concentration at the fine grain: `
    dominant_key_share`, the top single key's own fraction of all observations, is run 21's
    "14,675/14,676" restated generically)."""
    totals = mined_fine.get("position_totals", {})
    counts_sorted = sorted(totals.values(), reverse=True)
    total_obs = sum(counts_sorted)
    return {
        "n_distinct_fine_keys": len(totals),
        "n_fine_keys_with_min_obs": sum(1 for v in totals.values() if v >= min_obs),
        "min_obs_threshold": min_obs,
        "total_observations": total_obs,
        "top10_observation_counts": counts_sorted[:10],
        "dominant_key_share": (counts_sorted[0] / total_obs) if counts_sorted else 0.0,
    }


def fine_key_coverage(native, stroke_points_by_char: list, position_totals: dict, *,
                       segments: int, grid: int, scale_bins: int,
                       min_obs: int = FINE_MIN_OBS) -> dict[str, Any]:
    """RECALL of the mined fine-key position table against a HELD-OUT (TEST-time) stroke
    population — what fraction of TEST-time decoded strokes have a matching fine identity key
    carrying `>= min_obs` BACKGROUND observations (the run-22 branch's own pre-registered
    "TEST-time key coverage" test). `stroke_points_by_char` is a list of per-character
    `[(points, coarse_name, ...), ...]` sequences — the SAME shape `decode_char_signature`'s
    own `"stroke_points"` field already returns, and the SAME shape `mine_spatial_priors_fine`
    consumes internally — this function only READS them (each stroke's own fine key, computed
    the identical way mining computed it) and checks table membership + the observation-count
    threshold; no mining, no mutation, no ranking."""
    n_total, n_covered = 0, 0
    for stroke_points in stroke_points_by_char:
        for item in stroke_points:
            pts, coarse_name = item[0], item[1]
            fine_name = _fine_identity_key(native, pts, coarse_name, segments=segments,
                                            grid=grid, scale_bins=scale_bins)
            n_total += 1
            if position_totals.get(fine_name, 0) >= min_obs:
                n_covered += 1
    return {"n_total_strokes": n_total, "n_covered": n_covered,
            "coverage": (n_covered / n_total) if n_total > 0 else 0.0}


def fine_prior_branch_verdict(identity_diag: dict, dxdydo_diag: dict, coverage_diag: dict, *,
                               min_distinct_with_min_obs: int = MIN_DISTINCT_FINE_KEYS,
                               min_mean_peakedness: float = MIN_MEAN_PEAKEDNESS,
                               min_coverage: float = MIN_TEST_COVERAGE) -> dict[str, Any]:
    """THE run-22 pre-registered decision branch, read BEFORE any accuracy number: a plain
    boolean combination of three already-computed diagnostic VALUES (`fine_identity_diagnostics`,
    `prior_diagnostics(mined_fine["fine"], dims=("dx","dy","do"))`, `fine_key_coverage`) — never
    a search, never a comparison between competing candidates. "The wall holds at fine grain
    too" (STOP, no accuracy arm) iff ANY of: (a) fewer than `min_distinct_with_min_obs` distinct
    fine keys carry `>= FINE_MIN_OBS` background observations; (b) mean per-identity peakedness
    on dx/dy/do stays below `min_mean_peakedness`; (c) TEST-time fine-key coverage stays below
    `min_coverage`."""
    fails_diversity = identity_diag["n_fine_keys_with_min_obs"] < min_distinct_with_min_obs
    fails_peakedness = dxdydo_diag["mean_peakedness"] < min_mean_peakedness
    fails_coverage = coverage_diag["coverage"] < min_coverage
    proceed = not (fails_diversity or fails_peakedness or fails_coverage)
    return {"proceed_to_accuracy": proceed, "fails_diversity": fails_diversity,
            "fails_peakedness": fails_peakedness, "fails_coverage": fails_coverage}


# --------------------------------------------------------------------------- #
#  THE LOG-PRIOR — mechanical staging value (see this module's own top-of-file docstring for
#  the "precomputed as staged data" rationale).
# --------------------------------------------------------------------------- #
def _logprob(hist: dict, total: int, value, domain_size: int, alpha: float) -> float:
    count = hist.get(value, 0)
    p = (count + alpha) / (total + alpha * max(1, domain_size))
    return math.log(p)


def arrangement_log_prior(composed_sig: list, priors: dict[str, Any], *, grid: int,
                           turn_bins: int, scale_bins: int,
                           alpha: float = DEFAULT_PRIOR_ALPHA) -> float:
    """ONE candidate's own arrangement log-likelihood under the mined POSITION + TRANSITION
    distributions — a plain lookup+sum (mechanical staging, never a comparison to another
    candidate, never a branch on the resulting VALUE). Higher (less negative) = the candidate's
    OWN strokeq/rel relations are more plausible under what background characters actually do.

    NORMALIZATION (mirrors `abs_read.program_refit_bidir_term`'s own run-20 precedent
    verbatim: "PART-COUNT NORMALIZATION is the MEAN each direction already takes... the
    simplest of the design's two named options... no new tuned weight"): a RAW sum of
    per-dimension log-probabilities grows with the number of strokes/transitions a character
    happens to decode into, and its magnitude (tens of nats, one term per dimension per
    stroke/transition) is not naturally comparable to the parse-marginal fusion's own
    distance-like error scale (O(0.1-5), per `recognition_graph`'s own smoothdeform/
    shape-context/part terms) — the SAME "badly mismatched error scales" risk run 20's own
    docstring flags for its unweighted `Plus`. Returning the MEAN log-prob per considered
    (stroke-or-transition, dimension) term keeps this function's OWN output on a per-item
    scale close to a single distance term regardless of how many strokes a character has,
    making `lambda=1.0` ("unit first," per the launch instructions) a sane starting point
    rather than an arbitrarily large or small multiplier chosen by ACCIDENT of scale."""
    strokeq, rel = ar._strokeq_map(composed_sig), ar._rel_map(composed_sig)
    ks = sorted(rel)
    pos_counts, pos_totals = priors["position_counts"], priors["position_totals"]
    pos_global = priors["_position_global"]
    pos_global_total = sum(pos_totals.values())
    tr_counts, tr_totals = priors["transition_counts"], priors["transition_totals"]
    tr_global = priors["_transition_global"]
    tr_global_total = sum(tr_totals.values())

    logp_sum, n_terms = 0.0, 0
    for k in ks:
        name = strokeq.get(k)
        dx, dy, do, ds = rel[k]
        dims, total = pos_counts.get(name), pos_totals.get(name, 0)
        if not dims or total <= 0:
            dims, total = pos_global, pos_global_total
        for dim, value, dsize in (("dx", dx, grid), ("dy", dy, grid), ("do", do, turn_bins),
                                   ("ds", ds, scale_bins)):
            logp_sum += _logprob(dims.get(dim, {}), total, value, dsize, alpha)
            n_terms += 1

    for a, b in zip(ks, ks[1:]):
        name_i = strokeq.get(a)
        dxa, dya, doa, dsa = rel[a]
        dxb, dyb, dob, dsb = rel[b]
        ddx, ddy = dxb - dxa, dyb - dya
        ddo = cc._wrap_signed_bin(dob - doa, turn_bins)
        dds = dsb - dsa
        dims, total = tr_counts.get(name_i), tr_totals.get(name_i, 0)
        if not dims or total <= 0:
            dims, total = tr_global, tr_global_total
        for dim, value, dsize in (("dx", ddx, 2 * grid - 1), ("dy", ddy, 2 * grid - 1),
                                   ("do", ddo, turn_bins), ("ds", dds, 2 * scale_bins - 1)):
            logp_sum += _logprob(dims.get(dim, {}), total, value, dsize, alpha)
            n_terms += 1
    return logp_sum / n_terms if n_terms > 0 else 0.0


# --------------------------------------------------------------------------- #
#  THE COMBINED VERDICT — mirrors `abs_read.joined_refit_marginal_term`/
#  `refit_bidir_plus_marginal_rerank`'s exact combinator shape, a THIRD ingredient
#  (`log_prior_value`, already-computed DATA) summed into the SAME held Term.
# --------------------------------------------------------------------------- #
def spatial_prior_plus_marginal_term(base_error_term: dict, log_prior_value: float,
                                      lam: float) -> dict:
    """`base_error_term` (the real gate: `abs_read.parse_marginal_pair_error_term`, reused
    VERBATIM, unbound `s`/`w` Vars for the caller's own evaluate env; a synthetic gate may pass
    any stand-in, e.g. a `Lit` held FIXED across candidates to isolate the prior's own
    separating power) PLUS `Times([Lit(-lambda), Lit(log_prior_value)])` — ONE nested `Plus`,
    ONE `evaluate` call downstream, `abs_read.joined_refit_marginal_term`'s own "one nested
    composition, one evaluate" discipline extended with a bare-Python-computed third
    ingredient. LOWER = jointly better under BOTH the base error (smaller) and the mined
    arrangement prior (higher log-likelihood — the sign flip via `-lambda` is what turns
    "higher log-prior" into "lower combined error", the SAME Argmax(-err)==Argmin(err)
    convention every verdict in this codebase already uses). `lam=0.0` is the numeric identity
    (`Times(Lit(0.0), Lit(logp)) == 0` regardless of `logp`) — BYTE-IDENTICAL to
    `base_error_term` alone, the control-reproduction discipline."""
    return {"type": "Plus", "items": [
        base_error_term,
        {"type": "Times", "items": [{"type": "Lit", "value": -float(lam)},
                                     {"type": "Lit", "value": float(log_prior_value)}]}]}


def spatial_prior_marginal_rerank(scratch, query_node: int, cand_nodes: dict[int, int],
                                   candidate_composed: list, shortlist: list, priors: dict,
                                   *, lam: float = DEFAULT_PRIOR_LAMBDA, grid: int,
                                   turn_bins: int, scale_bins: int,
                                   alpha: float = DEFAULT_PRIOR_ALPHA,
                                   part_w: float = ar.DEFAULT_PARSE_PART_W,
                                   sc_w: float = ar.DEFAULT_PARSE_SC_W,
                                   beta: float = ar.DEFAULT_PARSE_BETA) -> dict[str, Any]:
    """THE multi-candidate verdict: for each candidate index in `shortlist`, ONE
    `spatial_prior_plus_marginal_term` evaluate combines the REAL parse-marginal error
    (`abs_read.parse_marginal_pair_error_term`, over `scratch`'s already-`stage_parse_char`-
    staged nodes — the SAME staging `abs_read.refit_bidir_plus_marginal_rerank` already
    consumes) with that candidate's OWN `arrangement_log_prior` (mechanical staging, computed
    once per candidate from its already-decoded `candidate_composed[ci]` signature) — held
    `Argmin` (`abs_read._argmin_pairs_term`, the SAME idiom every rerank in this module family
    uses) over the resulting pairs, never a Python min/sort/argmin. `cand_nodes` maps candidate
    index -> the staged Concept node id (`stage_parse_char`'s own return value). `lam=0.0`
    reproduces the PLAIN parse-marginal control's own ranking byte-for-byte (every combined
    score reduces to the base error alone) — the additivity discipline this run's CONTROL arm
    checks statistically (CI overlap) and this module's own synthetic gate checks exactly."""
    native = getattr(scratch, "_inner", scratch)
    pairs: list = []
    for ci in shortlist:
        cand_node = cand_nodes.get(ci)
        if cand_node is None or ci >= len(candidate_composed):
            continue
        logp = arrangement_log_prior(candidate_composed[ci], priors, grid=grid,
                                      turn_bins=turn_bins, scale_bins=scale_bins, alpha=alpha)
        base = ar.parse_marginal_pair_error_term(part_w=part_w, sc_w=sc_w, beta=beta)
        term = spatial_prior_plus_marginal_term(base, logp, lam)
        score = float(native.evaluate(term, {"s": query_node, "w": cand_node}) or 0.0)
        pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native.evaluate(ar._argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


# --------------------------------------------------------------------------- #
#  RUN 22 — FINE-KEYED LOG-PRIOR + VERDICT, with a THREE-LEVEL BACKOFF ladder (fine -> coarse
#  -> global) per term. Mirrors `arrangement_log_prior`/`spatial_prior_marginal_rerank`'s exact
#  shape; the only new thing is WHICH TABLE a given (stroke-or-transition, dimension) term's
#  lookup consults, decided by a plain presence+threshold check on data already computed
#  (`FINE_MIN_OBS`) — never a comparison between candidates.
# --------------------------------------------------------------------------- #
def arrangement_log_prior_fine(composed_sig: list, stroke_points: list, priors_fine: dict[str, Any],
                                priors_coarse: dict[str, Any], *, native, grid: int, turn_bins: int,
                                scale_bins: int, segments: int, alpha: float = DEFAULT_PRIOR_ALPHA,
                                min_obs: int = FINE_MIN_OBS) -> float:
    """`arrangement_log_prior`'s fine-keyed twin. `stroke_points` is the candidate's OWN
    `[(points, coarse_name, ...), ...]` sequence (`decode_char_signature`'s `"stroke_points"`
    field — already computed by the caller for OTHER purposes, e.g. the AbS re-rank; this
    function does not re-decode anything, it only re-quantizes each stroke's OWN already-
    available points at the SUB-FINE grain to derive its fine key, the SAME `_fine_identity_key`
    call `mine_spatial_priors_fine` makes). `priors_coarse` is `load_spatial_priors`'s own
    return shape (run 21's coarse table, complete with its `_position_global`/
    `_transition_global` pooled fallbacks) — the BACKOFF target when a stroke's fine key either
    is not held or carries fewer than `min_obs` background observations (a stroke's fine key
    should always exist as a VALUE — content hashes don't fail — but a genuinely novel
    sub-fine variant the mining pass never happened to observe is exactly the case backoff
    exists for). Per-term MEAN normalization, identical rationale to `arrangement_log_prior`."""
    strokeq, rel = ar._strokeq_map(composed_sig), ar._rel_map(composed_sig)
    ks = sorted(rel)

    fine_pos_counts, fine_pos_totals = priors_fine["position_counts"], priors_fine["position_totals"]
    fine_tr_counts, fine_tr_totals = priors_fine["transition_counts"], priors_fine["transition_totals"]
    coarse_pos_counts, coarse_pos_totals = priors_coarse["position_counts"], priors_coarse["position_totals"]
    coarse_pos_global = priors_coarse["_position_global"]
    coarse_pos_global_total = sum(coarse_pos_totals.values())
    coarse_tr_counts, coarse_tr_totals = priors_coarse["transition_counts"], priors_coarse["transition_totals"]
    coarse_tr_global = priors_coarse["_transition_global"]
    coarse_tr_global_total = sum(coarse_tr_totals.values())

    fine_key_by_k: dict = {}
    for k, item in enumerate(stroke_points):
        if k not in rel:
            continue
        pts, coarse_name = item[0], item[1]
        fine_key_by_k[k] = _fine_identity_key(native, pts, coarse_name, segments=segments,
                                               grid=grid, scale_bins=scale_bins)

    logp_sum, n_terms = 0.0, 0
    for k in ks:
        dx, dy, do, ds = rel[k]
        fine_name = fine_key_by_k.get(k)
        dims, total = fine_pos_counts.get(fine_name), fine_pos_totals.get(fine_name, 0)
        if not dims or total < min_obs:
            coarse_name = strokeq.get(k)
            dims, total = coarse_pos_counts.get(coarse_name), coarse_pos_totals.get(coarse_name, 0)
            if not dims or total <= 0:
                dims, total = coarse_pos_global, coarse_pos_global_total
        for dim, value, dsize in (("dx", dx, grid), ("dy", dy, grid), ("do", do, turn_bins),
                                   ("ds", ds, scale_bins)):
            logp_sum += _logprob(dims.get(dim, {}), total, value, dsize, alpha)
            n_terms += 1

    for a, b in zip(ks, ks[1:]):
        dxa, dya, doa, dsa = rel[a]
        dxb, dyb, dob, dsb = rel[b]
        ddx, ddy = dxb - dxa, dyb - dya
        ddo = cc._wrap_signed_bin(dob - doa, turn_bins)
        dds = dsb - dsa
        fine_name_i = fine_key_by_k.get(a)
        dims, total = fine_tr_counts.get(fine_name_i), fine_tr_totals.get(fine_name_i, 0)
        if not dims or total < min_obs:
            coarse_name_i = strokeq.get(a)
            dims, total = coarse_tr_counts.get(coarse_name_i), coarse_tr_totals.get(coarse_name_i, 0)
            if not dims or total <= 0:
                dims, total = coarse_tr_global, coarse_tr_global_total
        for dim, value, dsize in (("dx", ddx, 2 * grid - 1), ("dy", ddy, 2 * grid - 1),
                                   ("do", ddo, turn_bins), ("ds", dds, 2 * scale_bins - 1)):
            logp_sum += _logprob(dims.get(dim, {}), total, value, dsize, alpha)
            n_terms += 1
    return logp_sum / n_terms if n_terms > 0 else 0.0


def spatial_prior_marginal_rerank_fine(scratch, query_node: int, cand_nodes: dict[int, int],
                                        candidate_composed: list, candidate_stroke_points: list,
                                        shortlist: list, priors_fine: dict, priors_coarse: dict,
                                        *, native, lam: float = DEFAULT_PRIOR_LAMBDA, grid: int,
                                        turn_bins: int, scale_bins: int, segments: int,
                                        alpha: float = DEFAULT_PRIOR_ALPHA,
                                        min_obs: int = FINE_MIN_OBS,
                                        part_w: float = ar.DEFAULT_PARSE_PART_W,
                                        sc_w: float = ar.DEFAULT_PARSE_SC_W,
                                        beta: float = ar.DEFAULT_PARSE_BETA) -> dict[str, Any]:
    """`spatial_prior_marginal_rerank`'s fine-keyed (+backoff) twin — identical shape, one extra
    per-candidate ingredient (`candidate_stroke_points[ci]`, feeding `arrangement_log_prior_fine`
    instead of `arrangement_log_prior`). `lam=0.0` reproduces the base parse-marginal ranking
    byte-for-byte, the SAME additivity discipline every rerank in this module follows."""
    native_ev = getattr(scratch, "_inner", scratch)
    pairs: list = []
    for ci in shortlist:
        cand_node = cand_nodes.get(ci)
        if cand_node is None or ci >= len(candidate_composed):
            continue
        sp_pts = candidate_stroke_points[ci] if ci < len(candidate_stroke_points) else []
        logp = arrangement_log_prior_fine(candidate_composed[ci], sp_pts, priors_fine,
                                           priors_coarse, native=native, grid=grid,
                                           turn_bins=turn_bins, scale_bins=scale_bins,
                                           segments=segments, alpha=alpha, min_obs=min_obs)
        base = ar.parse_marginal_pair_error_term(part_w=part_w, sc_w=sc_w, beta=beta)
        term = spatial_prior_plus_marginal_term(base, logp, lam)
        score = float(native_ev.evaluate(term, {"s": query_node, "w": cand_node}) or 0.0)
        pairs.append((score, ci))
    winner = shortlist[0] if shortlist else None
    if pairs:
        w = native_ev.evaluate(ar._argmin_pairs_term(pairs), {})
        if w is not None:
            winner = int(w[1])
    return {"winner": winner, "shortlist": shortlist, "scores": pairs, "n_compared": len(pairs)}


__all__ = ["CATEGORY", "MINE_SPLIT", "DIMS", "DEFAULT_PRIOR_ALPHA", "DEFAULT_PRIOR_LAMBDA",
           "mine_spatial_priors", "persist_spatial_priors", "load_spatial_priors",
           "prior_diagnostics", "arrangement_log_prior", "spatial_prior_plus_marginal_term",
           "spatial_prior_marginal_rerank", "_rel_maps", "_accumulate_character_stats",
           "_global_histograms", "_logprob", "_entropy_bits",
           "CATEGORY_FINE", "FINE_MIN_OBS", "MIN_DISTINCT_FINE_KEYS", "MIN_MEAN_PEAKEDNESS",
           "MIN_TEST_COVERAGE", "_fine_identity_key", "mine_spatial_priors_fine",
           "persist_spatial_priors_fine", "load_spatial_priors_fine",
           "fine_identity_diagnostics", "fine_key_coverage", "fine_prior_branch_verdict",
           "arrangement_log_prior_fine", "spatial_prior_marginal_rerank_fine"]
