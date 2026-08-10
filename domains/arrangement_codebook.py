"""arrangement_codebook — RUN 28 LEVER 2: the sd loop at ARRANGEMENT (character) grain.

THE WALL THIS CLOSES (run 27's own traced diagnosis): `domains/character_compose.py` already
builds a full, unit-tested character-grain sd-loop path — `recognize_or_mint_character` (a
direct `TransformDecode` read-off for rung-1 pose transforms, falling to
`domains.reflective_faculty.induce_concern` for genuinely novel arrangements) and
`grow_character_quantum` (the install primitive, mirroring `stroke_codebook.grow_stroke_
quantum` one level up) — but NEITHER has a single call site outside `tests/
test_character_composition_migrated.py`. `domains/homework_loop.py`'s `mark_characters`/
`babble_characters`/`cycle_characters` compose a character's signature and score its own
render/re-decode ROUND-TRIP stability, but never ask "does this arrangement match anything
already held" or "should this arrangement be REMEMBERED" — every one of run 27's 6 reading
cycles therefore left `grain_vocabulary_report`'s own STROKE-grain codebook delta at
`(+0, +0, +0, +0)` and had no CHARACTER-grain codebook to report at all: the residual run 27
diagnosed as "arrangement grain" (character round-trip arrangement subscore 0.80-0.84 vs
family/count 0.99) had no learning channel wired to it whatsoever.

THE FIX: this module is a THIN WIRING layer — it invents no new recognition/mint machinery
(per CLAUDE.md's "reuse held machinery, never build a parallel engine"; the SAME instruction
this arc's own commit history already enforced for the stroke-grain sd loop). Two pieces:

  1. `mint_or_recognize_character_reading` — the CHARACTER-grain twin of `ink_decode.decode_ink`'s
     own `if res.get("minted"): grow_stroke_quantum(...)` idiom, one level up: call the EXISTING
     `character_compose.recognize_or_mint_character` (which itself reuses the EXISTING
     `sd_decode`/`sd_recognize`/`sd_transform_decode`/`sd_infer_dimension`/`sd_mint_quantum`
     rule ladder via `induce_concern`, generic over `kind` — no rule changes needed, confirmed
     directly: `seeds/shape_decode_loop.json`'s rules read `NodesOfType("ShapeSignature")` with
     no `kind` filter at all), and when it decided to mint, INSTALL what it decided via the
     EXISTING `character_compose.grow_character_quantum` — exactly the "rule decides, Python
     installs" split every mint path in this codebase already follows. The COVERAGE-FRACTION
     lever the run-28 header calls for is the ALREADY-ESTABLISHED one: `sd_mint_quantum`'s own
     guard is `Count(residual) == 0` (exact, full coverage) fails first through the
     transform/dimension-inference rungs before minting — a coverage fraction of EXACTLY 1.0,
     pre-registered by the existing, already-battle-tested stroke-grain ladder this module
     reuses verbatim rather than inventing a fractional-coverage rule of its own (CLAUDE.md:
     "reuse held machinery, never build a parallel engine" — a SEPARATE fractional-coverage
     mint gate at character grain would be exactly that parallel engine).

  2. Stability-weighted arrangement persistence (the run-28 header's own "stability-weighted
     relation attrs" requirement): `update_relation_stability` nudges a PER-RELATION weight
     (one float per `rel:<k>:<x|y|o|s>` / `cpose_*` key) on a character quantum's own graph
     node toward 1.0 on agreement / toward a floor on disagreement, EMA-style fixed-formula
     arithmetic over a held `Eq`-decided match (mirrors `stroke_codebook.grow_stroke_quantum`'s
     own multi-grain-signature "one motion" convention: weights ride ALONGSIDE the quantum's
     signature, never a second codebook). `weighted_arrangement_score` is the round-trip
     comparator's own weighted twin — a held `Sum`+`IfThenElse` Term over (weight, ref_value,
     obs_value) triples (mirrors `character_compose.assignment_coverage_term`'s own Sum+
     IfThenElse idiom exactly), so a relation that has PROVEN unstable under repeated re-render
     contributes less to the score than one that has proven stable, instead of every relation
     being weighted equally regardless of its own observed reliability.

ARCHITECTURE (CLAUDE.md): every decision here is either (a) already made by the EXISTING seeded
`sd_*` rule ladder (this module reads the verdict back, never re-decides it) or (b) a held Term
evaluate over already-fetched values (`_weighted_score_term`, the SAME `Sum`/`IfThenElse`/`Eq`
idiom `character_compose.assignment_coverage_term` already establishes) or (c) fixed-formula
EMA arithmetic on a plain equality of two already-fetched scalar graph values — the SAME class
of "compare two already-decided values" idiom `homework_loop._resolved_key`/`babble`'s own
`if _family_root(sub, re_name) == _family_root(sub, orig_name):` already use throughout this
codebase (never an argmin/argmax/sort-by-score ranking, which is what would make it a
DECISION rather than a comparison of two already-known facts)."""
from __future__ import annotations

from typing import Any, Optional

from domains import character_compose as cc
from domains import frame_weights as fw
from domains import ink_decode as ink
from domains.stroke_codebook import _find_stroke_node, _native, _sub

DEFAULT_WEIGHT = 1.0
MIN_WEIGHT = 0.1
MAX_WEIGHT = 1.0
# Pre-registered EMA step (symmetric up/down) -- same "small, deliberate nudge, never a single-
# observation snap decision" scale `stroke_codebook`'s own pose-jitter bins use elsewhere in
# this arc. Never tuned against eval/practice-alphabet outcomes.
DEFAULT_STABILITY_STEP = 0.15

CHARACTER_KIND = "character"


# --------------------------------------------------------------------------- #
#  1. READING-SIDE RECOGNIZE-OR-MINT — the thin wiring the run-28 header asks for.
# --------------------------------------------------------------------------- #
def mint_or_recognize_character_reading(agent, composed_sig: list, *,
                                         name_hint_prefix: str = "character_shape",
                                         category: str = cc.DEFAULT_CATEGORY,
                                         max_dims: int = cc.DEFAULT_CHARACTER_MAX_DIMS
                                         ) -> dict[str, Any]:
    """ONE call per composed character signature: try to recognize it against the held
    character codebook (`character_compose.recognize_or_mint_character`, EXISTING, unchanged);
    when it decided to mint, INSTALL the new quantum (`character_compose.grow_character_quantum`,
    EXISTING, unchanged) under a CONTENT-KEYED name (`ink_decode._signature_key`, the SAME
    stable content hash the stroke-grain OOV path already uses for its own idempotent-by-name
    dedup — "mints once, not per span, key the observation") so a REPEAT of the identical
    arrangement across items/cycles installs exactly once. `name_hint_prefix` feeds
    `induce_concern`'s own `key` (mirrors `ink_decode.decode_ink`'s own
    `name_hint=f"ink_shape_{sig_key}"` convention one level up) so two DISTINCT arrangements
    get DISTINCT capability keys and therefore both mint (never spuriously deduped against each
    other by the novelty-guard's own same-key check, `seeds/shape_decode_loop.json`'s
    `sd_mint_quantum`/`sd_dedup_existing`).

    Returns `{"minted": bool, "installed": bool, "name": str|None, ...}` — `"installed"` is
    `False` on the recognize path (nothing new to install) and on the (should-not-happen)
    honest case where a decided mint's own install call reports `grown=False` (already held
    under that exact content hash — idempotent, not an error)."""
    if not composed_sig:
        return {"minted": False, "installed": False, "name": None,
                "reason": "empty composed signature — nothing to recognize or mint"}
    sig_key = ink._signature_key(composed_sig)
    name_hint = f"{name_hint_prefix}_{sig_key}"
    res = cc.recognize_or_mint_character(agent, composed_sig, name_hint=name_hint,
                                          max_dims=max_dims)
    out = dict(res)
    out["installed"] = False
    if res.get("minted"):
        new_name = f"character_{sig_key}"
        grow_res = cc.grow_character_quantum(agent, new_name, composed_sig, category=category)
        out["name"] = new_name
        out["installed"] = bool(grow_res.get("grown"))
        out["grow"] = grow_res
    else:
        out["name"] = res.get("covered_by")
    return out


def character_vocabulary_report(sub) -> dict[str, Any]:
    """Mechanical read-back (no decision), the character-grain twin of `stroke_codebook.
    grain_vocabulary_report`: how many `ShapeSignature{kind:"character"}` quanta are held."""
    names = set()
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == CHARACTER_KIND:
            nm = at.get("name")
            if nm:
                names.add(nm)
    return {"total": len(names), "names": sorted(names)}


# --------------------------------------------------------------------------- #
#  2. STABILITY-WEIGHTED ARRANGEMENT PERSISTENCE.
# --------------------------------------------------------------------------- #
def _relation_map(sig: list) -> dict:
    """Mechanical extraction (no decision — a fixed structural re-packaging of relations a
    held Term already produced, the same kind of translation `ink_decode._extract_dim_delta`/
    `character_compose._stroke_records` already perform): every `rel:<k>:<x|y|o|s>` value plus
    every whole-character `cpose_*` value, from ONE composed character signature. Accepts BOTH
    `list` and `tuple` relation entries (a LIVE `native.evaluate(...)` result surfaces Rust
    sequences as Python `tuple`s — `ink_decode._fine_seg_relations`'s own documented gotcha;
    a bare-list-only isinstance filter here would silently drop every relation of a live
    signature, exactly the bug that module's docstring warns against)."""
    out: dict[str, Any] = {}
    for r in sig:
        if not (isinstance(r, (list, tuple)) and r):
            continue
        pred = r[0]
        if pred == "rel" and len(r) >= 6:
            k = r[1]
            for slot, label in enumerate(("x", "y", "o", "s")):
                out[f"rel:{k}:{label}"] = r[2 + slot]
        elif pred in cc._CPOSE_PREDS and len(r) >= 2:
            out[pred] = r[1]
    return out


def _weighted_score_term(triples: list) -> dict:
    """Held `Sum` + `IfThenElse` over `(weight, ref_value, obs_value)` triples — mirrors
    `character_compose.assignment_coverage_term`'s own `Sum`+`IfThenElse` scoring idiom exactly,
    one relation-key at a time instead of one stroke-record at a time: a relation's own already-
    looked-up WEIGHT contributes to the sum iff its reference and observed values agree (a held
    `Eq`), zero otherwise. The scoring DECISION (which relations matched) is this Term's, not
    Python's — this module only assembles the `(weight, ref, obs)` literal triples beforehand
    (already-fetched dict values, no ranking)."""
    def _idx(i: int) -> dict:
        return {"type": "IndexAt", "seq": {"type": "Var", "name": "t"},
                "index": {"type": "Lit", "value": i}}
    return {"type": "Sum", "source": {"type": "Lit", "value": triples}, "var_name": "t",
            "value": {"type": "IfThenElse",
                      "cond": {"type": "Eq", "a": _idx(1), "b": _idx(2)},
                      "then": _idx(0), "other": {"type": "Lit", "value": 0.0}}}


def _quantum_node(sub, quantum_name: str):
    return _find_stroke_node(sub, quantum_name, kind=CHARACTER_KIND)


def relation_weights(sub, quantum_name: str) -> dict:
    """Mechanical read-back: the character quantum's own held FRAME (RUN 30 — `domains.
    frame_weights`, replacing run 29's Python-mutated `relation_weights` dict attr), read out
    as the same `{key: weight}` shape every existing caller already expects. `{}` if the
    quantum or its frame does not exist yet. A freshly-minted quantum's frame already carries
    every relation key at `DEFAULT_WEIGHT` (`grow_character_quantum`'s own mint-time install,
    `domains.frame_weights.ensure_quantum_frame`) — numerically IDENTICAL to run 29's own
    `.get(key, DEFAULT_WEIGHT)` fallback for an as-yet-unobserved key, so every existing
    caller of this function sees the same values whether a key was ever explicitly updated or
    not."""
    node = _quantum_node(sub, quantum_name)
    if node is None:
        return {}
    frame_node = fw._frame_node_by_key(sub, fw.quantum_frame_key(quantum_name))
    if frame_node is None:
        return {}
    return fw.frame_axis_weights(sub, frame_node)


def update_relation_stability(agent, quantum_name: str, ref_sig: list, observed_sig: list, *,
                               step: float = DEFAULT_STABILITY_STEP,
                               min_weight: float = MIN_WEIGHT,
                               max_weight: float = MAX_WEIGHT) -> dict[str, Any]:
    """ONE stability-update pass — RUN 30: the WEIGHT UPDATE ITSELF is now a graph rule
    (`fw_update`, `seeds/frame_weights.json`), fired by `run_rules` from inside `domains.
    frame_weights.update_quantum_frame`, never Python arithmetic on a weight value. This
    function's own remaining job is exactly the adapter's: decide `agree` for every relation
    key BOTH `ref_sig` (the quantum's own stored/reference arrangement) and `observed_sig` (a
    fresh re-render/re-decode of the SAME quantum) carry — a PLAIN comparison of two
    already-fetched scalar graph values (the SAME class of comparison `homework_loop.
    _resolved_key`/`babble`'s own `_family_root(...)==_family_root(...)` checks already use
    throughout this codebase — not a ranking, not an argmin/argmax) — and hand that decided
    fact to `update_quantum_frame`, which writes it as `AxisEvidence` graph data and ticks.
    Honestly reported no-op if the quantum does not exist. `step`/`min_weight`/`max_weight`
    are accepted for API compatibility with every pre-existing call site but MUST equal this
    module's own defaults — the actual EMA arithmetic is now a fixed constant baked into the
    seeded `fw_update` rule (mirroring run 29's own fixed-formula EMA exactly, so the
    migration-equivalence gate can hold this reform to an EXACT numeric match), no longer a
    per-call parameter a caller can vary; every existing call site in this codebase (verified)
    already calls this with the defaults."""
    if (step, min_weight, max_weight) != (DEFAULT_STABILITY_STEP, MIN_WEIGHT, MAX_WEIGHT):
        raise NotImplementedError(
            "update_relation_stability: step/min_weight/max_weight are no longer per-call "
            "parameters — the EMA arithmetic is a fixed constant inside the seeded fw_update "
            "graph rule (RUN 30 representation reform); pass the module defaults or change "
            "seeds/frame_weights.json's own literals instead")
    sub = _sub(agent)
    node = _quantum_node(sub, quantum_name)
    if node is None:
        return {"updated": False, "reason": "no such character quantum", "name": quantum_name}

    before = relation_weights(sub, quantum_name)
    ref_map = _relation_map(ref_sig)
    obs_map = _relation_map(observed_sig)
    agreements = {key: (ref_map[key] == obs_map[key])
                  for key in ref_map if key in obs_map}
    fw.update_quantum_frame(agent, node, quantum_name, agreements)
    weights = relation_weights(sub, quantum_name)
    changed = {key: (float(before.get(key, DEFAULT_WEIGHT)), float(weights.get(key, DEFAULT_WEIGHT)),
                     bool(agree)) for key, agree in agreements.items()}
    return {"updated": True, "name": quantum_name, "weights": weights, "changed": changed}


def weighted_arrangement_score(agent, quantum_name: str, ref_sig: list, observed_sig: list
                                ) -> dict[str, Any]:
    """The stability-weighted twin of `homework_loop._character_round_trip_score`'s own
    `arrangement_score` — same per-relation agreement test, but each relation's contribution is
    WEIGHTED by its own persisted reliability (`relation_weights`, default `DEFAULT_WEIGHT` for
    an as-yet-unobserved key) instead of counted uniformly, via ONE held `_weighted_score_term`
    evaluate. `score = 1.0` (vacuously perfect) when there is no comparable relation on both
    sides — the same honest-edge-case convention `homework_loop._round_trip_score` already
    establishes for its own `n==0` case."""
    sub = _sub(agent)
    native = _native(agent)
    weights = relation_weights(sub, quantum_name)
    ref_map = _relation_map(ref_sig)
    obs_map = _relation_map(observed_sig)
    keys = [k for k in ref_map if k in obs_map]
    if not keys:
        return {"score": 1.0, "n": 0, "total_weight": 0.0}

    triples = [(float(weights.get(k, DEFAULT_WEIGHT)), ref_map[k], obs_map[k]) for k in keys]
    matched_weight = float(native.evaluate(_weighted_score_term(triples), {}) or 0.0)
    total_weight = sum(t[0] for t in triples)
    score = (matched_weight / total_weight) if total_weight > 0 else 1.0
    return {"score": score, "n": len(keys), "total_weight": total_weight,
            "matched_weight": matched_weight}


# --------------------------------------------------------------------------- #
#  3. POOLED RELIABILITY PRIOR — RUN 29 (CONSUME) arm 3's own mechanism: the eval proposal
#  path (`scripts/jabberwock_omniglot_run29_consume.py`) reads only the STROKE codebook
#  (`abs_read.propose_top_k`'s naive coverage over `strokeq`/`rel`/`cpose_*` relations) — the
#  40-quantum CHARACTER codebook this module grows is invisible to it. A DIRECT per-quantum
#  match signal against eval material would be honestly near-zero (the character codebook holds
#  ONLY practice-alphabet arrangements, none from eval alphabets — a query character from a
#  held-out evaluation alphabet cannot literally match any of the 40). What DOES generalize
#  across alphabets is WHICH RELATION KIND has proven reliable under re-render, POOLED over
#  every held quantum's own `relation_weights` — a global, content-free reliability prior
#  ("orientation relations wobble more than position relations", say), not a per-quantum
#  lookup. `pooled_relation_kind_reliability` computes that pool; `pooled_prior_coverage_term`
#  is `abs_read._coverage_term`'s WEIGHTED twin, reusing the SAME `Sum`+`IfThenElse`+`In` idiom
#  with a per-relation weight substituted for the naive metric's uniform `1.0` credit — a
#  relation whose KIND has proven unstable contributes LESS to a candidate's proposal score, one
#  that has proven stable contributes more (bounded by `default_weight` for `strokeq`/
#  `strokeq_fine`/`rel2` — no persisted stability channel exists for those, so they keep their
#  pre-existing uniform contribution, untouched). `propose_top_k_pooled_prior` is `abs_read.
#  propose_top_k`'s own repeated-held-`Argmax` shortlist loop, verbatim, over this weighted term
#  instead of the naive one — a SEPARATE proposal MODALITY the eval script unions with the
#  existing naive-coverage shortlist (the run-25 "different angles don't overlap" precedent,
#  `sorted(set(a) | set(b))`), never a replacement for it.
# --------------------------------------------------------------------------- #
def pooled_relation_kind_reliability(sub) -> dict[str, float]:
    """RUN 30: the shared/pooled FRAME (`domains.frame_weights.pooled_reliability`) — one
    axis per relation KIND, log-additive evidence combination computed by the seeded
    `fw_pool` graph rule (mean of every held quantum's own `scope="quantum"` FrameAxis of
    that kind, in log space via Sum(Exp(...))/Count then Log(...) back), never a Python
    `sum(ws)/len(ws)` reduction. Returns `{}` when no quantum holds any axis yet (nothing to
    pool — an honest empty prior, never a fabricated uniform one; `pooled_prior_coverage_
    term`'s own `default_weight` covers the caller's fallback in that case) — the SAME
    contract run 29's own dict-path implementation established."""
    return fw.pooled_reliability(sub)


def _relation_kind_of(rel) -> Optional[str]:
    """Mechanical: the pooled-prior KIND a whole composed-signature relation TUPLE (as it
    appears literally in `propose_top_k`'s own `query_sig`/`exemplar_sig` lists, e.g.
    `["rel", k, x_q, y_q, o_q, s_q]` or `["cpose_x", v]`) maps to — `'rel'` for a whole `rel`
    4-tuple (it only ever matches/misses as ONE atomic unit at THIS scoring layer, unlike
    `_relation_map`'s own per-slot explosion used for `update_relation_stability`/
    `weighted_arrangement_score` — so its own weight is the pooled MEAN of the four `x`/`y`/`o`/
    `s` sub-kind priors, `_rel_kind_weight`), the bare predicate for a `cpose_*` singleton, or
    `None` for every other relation kind (`strokeq`/`strokeq_fine`/`rel2` — no persisted
    stability channel exists for those; the caller's `default_weight` applies unchanged)."""
    if not (isinstance(rel, (list, tuple)) and rel):
        return None
    pred = rel[0]
    if pred == "rel":
        return "rel"
    if pred in cc._CPOSE_PREDS:
        return pred
    return None


def _rel_kind_weight(prior: dict, default_weight: float) -> float:
    """Mechanical arithmetic: the MEAN of whichever of the four `x`/`y`/`o`/`s` pooled sub-kind
    priors are present — a whole `rel` 4-tuple's own single weight for `pooled_prior_coverage_
    term` (see `_relation_kind_of`'s own docstring for why one relation gets one weight here).
    `default_weight` when NONE of the four sub-kinds have been pooled yet (an honest fallback,
    never a fabricated partial mean)."""
    vals = [prior[k] for k in ("x", "y", "o", "s") if k in prior]
    return (sum(vals) / len(vals)) if vals else default_weight


def pooled_prior_coverage_term(query_sig: list, exemplar_sig: list, prior: dict, *,
                                default_weight: float = 1.0) -> dict:
    """`abs_read._coverage_term`'s WEIGHTED twin — held `Sum` + `IfThenElse` + `In` over the
    SAME "does this query relation appear anywhere in the exemplar's own relation list"
    membership test, except each relation's own credit is its POOLED-KIND reliability
    (`_relation_kind_of`/`_rel_kind_weight`, already looked up in Python from `prior` — a
    mechanical dict read, never a ranking) instead of a uniform `1.0`. The scoring DECISION
    (which relations are actually present in `exemplar_sig`) is the held `In` Term's, not
    Python's — this function only assembles the `(weight, relation)` literal pairs beforehand."""
    def _idx(i: int) -> dict:
        return {"type": "IndexAt", "seq": {"type": "Var", "name": "wr"},
                "index": {"type": "Lit", "value": i}}
    rel_w = _rel_kind_weight(prior, default_weight)
    weighted = []
    for r in query_sig:
        kind = _relation_kind_of(r)
        if kind == "rel":
            w = rel_w
        elif kind is not None:
            w = float(prior.get(kind, default_weight))
        else:
            w = default_weight
        weighted.append((w, r))
    return {"type": "Sum", "source": {"type": "Lit", "value": weighted}, "var_name": "wr",
            "value": {"type": "IfThenElse",
                      "cond": {"type": "In", "member": _idx(1),
                               "container": {"type": "Lit", "value": exemplar_sig}},
                      "then": _idx(0), "other": {"type": "Lit", "value": 0.0}}}


def _argmax_pairs_term(pairs) -> dict:
    """Duplicated locally per this codebase's own established convention (see `abs_read.py`'s
    own identical copy's docstring) rather than a cross-module import for a 6-line Term
    builder."""
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}}, "default": None}


DEFAULT_POOLED_TOPK = 10


def propose_top_k_pooled_prior(native, query_sig: list, exemplar_sigs: list, prior: dict, *,
                                k: int = DEFAULT_POOLED_TOPK,
                                default_weight: float = 1.0) -> list[int]:
    """`abs_read.propose_top_k`'s own repeated-held-`Argmax` shortlist loop, verbatim, scored by
    `pooled_prior_coverage_term` instead of the naive `_coverage_term` — a SEPARATE proposal
    MODALITY (arm 3's own mechanism), meant to be UNIONED with the naive-coverage shortlist by
    the caller (`sorted(set(a) | set(b))`, the run-25 precedent), never a replacement. `k` is a
    LOGGED CONSTANT, never tuned per-query; stops early (an honest, non-crashing shortlist,
    never padded) if fewer than `k` exemplars exist or a round returns no winner."""
    remaining = list(range(len(exemplar_sigs)))
    order: list[int] = []
    for _ in range(min(k, len(exemplar_sigs))):
        pairs = [(float(native.evaluate(
                     pooled_prior_coverage_term(query_sig, exemplar_sigs[i], prior,
                                                 default_weight=default_weight), {}) or 0.0), i)
                 for i in remaining]
        winner = native.evaluate(_argmax_pairs_term(pairs), {})
        if winner is None:
            break
        idx = int(winner[1])
        order.append(idx)
        remaining.remove(idx)
    return order


__all__ = ["mint_or_recognize_character_reading", "character_vocabulary_report",
           "relation_weights", "update_relation_stability", "weighted_arrangement_score",
           "DEFAULT_WEIGHT", "MIN_WEIGHT", "MAX_WEIGHT", "DEFAULT_STABILITY_STEP",
           "CHARACTER_KIND", "pooled_relation_kind_reliability", "pooled_prior_coverage_term",
           "propose_top_k_pooled_prior", "DEFAULT_POOLED_TOPK"]
