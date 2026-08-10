"""Compositional chunking seed — recurring sign sequences become signs.

The next layer above lexical_access. Everything in this seed is
graph-resident: lexical_access (Rust) already adds a `follows` edge
between consecutive Utterances on a stream — that one edge is the
only Rust contribution. All four cognitive moves are graph Rules
that fire on every `sub.tick()`:

  1. count_bigram_existing — increment an existing BigramObservation
     when a counted-this-tick utterance pair maps to one
  2. count_bigram_new — mint a fresh BigramObservation when no
     existing one covers this pair
  3. promote_bigram_to_sign — when a bigram's count crosses
     threshold, mint an AcousticSign whose first_component /
     second_component edges record the chunk's structure
  4. compose_utterance — when an utterance pair matches an existing
     compositional sign's components, mint an Utterance heard_as
     that compositional sign covering the pair's combined span

Dedup via per-Utterance boolean attrs (`bigram_counted`,
`composed_emitted`) — once a base Utterance has participated, the
where-clauses gate further firings out.

Biology: HVC sequence chunks in birds; Broca's-area syntactic
chunking in humans. The substrate doesn't impose a depth — once a
chunk is a sign, the same rules can match over chunks of chunks
(future work: have lexical_access wire `follows` from compositional
Utterances too, enabling true recursion).
"""
from __future__ import annotations


_CHUNK_PRODUCTIONS = [
    # The new `follows` edge that lexical_access lays down: each
    # Utterance points back to the one that came before it on the
    # same stream. This is the temporal-order skeleton the rules
    # pattern-match against.
    ("Utterance", "follows", "Utterance",
     "compositional_chunking:utterance_follows"),
    # BigramObservation tracks how often a (first_sign, second_sign)
    # pair has co-occurred — substrate-wide, across all streams.
    ("BigramObservation", "first_sign", "AcousticSign",
     "compositional_chunking:bigram_first"),
    ("BigramObservation", "second_sign", "AcousticSign",
     "compositional_chunking:bigram_second"),
    ("BigramObservation", "promoted_to", "AcousticSign",
     "compositional_chunking:bigram_promoted_to"),
    # A compositional sign's two parts. Distinct edge types so the
    # order of composition is the edge type's identity (and Rule
    # lookups are unambiguous).
    ("AcousticSign", "first_component", "AcousticSign",
     "compositional_chunking:sign_first_comp"),
    ("AcousticSign", "second_component", "AcousticSign",
     "compositional_chunking:sign_second_comp"),
    # The lex tracks every bigram it sees so the tuning Rules can
    # count promotion-rate. The has_entry edge from lex to chunked
    # signs lets the promote rule bring the lex into its match.
    ("AcousticLexicon", "tracks_bigram", "BigramObservation",
     "compositional_chunking:lex_tracks_bigram"),
]


# Default promotion threshold — the bigram count at which a
# recurring pair gets promoted to a compositional AcousticSign.
# The LIVE value is stored as `lex.promotion_threshold` on each
# AcousticLexicon so the agent's tuning Rules can edit it as graph
# data. This constant is only the default seeded into the lex when
# it's first created (via lexical_access.attach_lexical_access).
_DEFAULT_PROMOTION_THRESHOLD = 8

# Tuning bounds for the agent's threshold-tuning Rules. Live as
# attrs on the lex's TunableParameter — the agent can edit them.
_PROMOTION_THRESHOLD_MIN = 4
_PROMOTION_THRESHOLD_MAX = 64
_PROMOTION_THRESHOLD_STEP = 2

# Per-tick wall-cost budget the chunking Capability declares to
# Reconsider. When tick cost rises above this, the Reconsider Rule
# flips the Capability's mode from "active" to "passive" — the
# count + promote Rules switch off, the cheaper compose Rule keeps
# firing. World adapter measures actual tick wall-time and writes
# it to SubstrateRoot.last_tick_ms.
_CHUNKING_TICK_BUDGET_MS = 80.0

# Promotion-rate bounds. If the fraction of bigrams that have been
# promoted strays outside [low, high], the agent retunes the
# threshold to bring the rate back into band.
_PROMOTION_RATE_HIGH = 0.50    # > this → noisy promotion, raise threshold
_PROMOTION_RATE_LOW = 0.05     # < this → too few chunks, lower threshold
_TUNE_COOLDOWN_BIGRAMS = 50    # wait for 50 fresh bigrams before re-tuning
_TUNE_MIN_BIGRAMS_TO_JUDGE = 30


def _enc(v):
    from substrate_rs import Term
    if isinstance(v, Term):
        return {"__term__": v.to_dict()}
    if isinstance(v, dict):
        return {k: _enc(x) for k, x in v.items()}
    return v


def _count_bigram_existing_rule() -> dict:
    """When a base Utterance pair already has a BigramObservation
    binding their two signs, bump its count and mark the pair
    counted so the rule doesn't refire next tick. Gated on the
    chunking Capability's mode — only fires when mode == "active"
    (Reconsider flips to "passive" when per-tick wall cost exceeds
    the Capability's budget)."""
    from substrate_rs import And, Attr, Eq, Lit, Not, Plus, Var
    where = And(items=(
        Eq(a=Attr(Var("cap"), "mode"), b=Lit("active")),
        Not(arg=Eq(a=Attr(Var("utt_a"), "bigram_counted"), b=Lit(True))),
        # Only count over base Utterances — compositional ones (those
        # minted by the compose_utterance rule) carry composed=True
        # and would otherwise double-count via their components.
        Not(arg=Eq(a=Attr(Var("utt_a"), "composed"), b=Lit(True))),
        Not(arg=Eq(a=Attr(Var("utt_b"), "composed"), b=Lit(True))),
    ))
    return {
        "id": "count_bigram_existing",
        "match": [
            ["utt_b", "follows", "utt_a"],
            ["utt_a", "heard_as", "sign_a"],
            ["utt_b", "heard_as", "sign_b"],
            ["b", "first_sign", "sign_a"],
            ["b", "second_sign", "sign_b"],
            ["lex", "has_entry", "sign_a"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "b", "count",
             _enc(Plus(items=(Attr(Var("b"), "count"), Lit(1))))],
            ["set_attr", "utt_a", "bigram_counted", True],
        ],
    }


def _count_bigram_new_rule() -> dict:
    """When a base Utterance pair has no existing BigramObservation
    for its (sign_a, sign_b), mint one with count=1. Also wire the
    new bigram to the AcousticLexicon via `tracks_bigram` so the
    promotion-threshold tuning Rules can count bigrams + promoted
    bigrams to compute promotion-rate.
    """
    from substrate_rs import (
        And, Attr, Eq, Exists, In, InNeighbours, Lit, Neighbours, Not, Var,
    )
    bigram_exists = Exists(
        source=InNeighbours(node=Var("sign_a"), edge_type="first_sign"),
        var_name="cand",
        predicate=In(
            member=Var("sign_b"),
            container=Neighbours(Var("cand"), "second_sign"),
        ),
    )
    where = And(items=(
        Eq(a=Attr(Var("cap"), "mode"), b=Lit("active")),
        Not(arg=Eq(a=Attr(Var("utt_a"), "bigram_counted"), b=Lit(True))),
        Not(arg=Eq(a=Attr(Var("utt_a"), "composed"), b=Lit(True))),
        Not(arg=Eq(a=Attr(Var("utt_b"), "composed"), b=Lit(True))),
        Not(arg=bigram_exists),
    ))
    return {
        "id": "count_bigram_new",
        "match": [
            ["utt_b", "follows", "utt_a"],
            ["utt_a", "heard_as", "sign_a"],
            ["utt_b", "heard_as", "sign_b"],
            ["lex", "has_entry", "sign_a"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["add_node", "b", "BigramObservation", {"count": 1}],
            ["add_edge", "b", "first_sign", "sign_a"],
            ["add_edge", "b", "second_sign", "sign_b"],
            ["add_edge", "lex", "tracks_bigram", "b"],
            ["set_attr", "utt_a", "bigram_counted", True],
        ],
    }


def _promote_bigram_rule() -> dict:
    """When a BigramObservation's count exceeds the promotion
    threshold AND it hasn't been promoted yet, mint a compositional
    AcousticSign with first_component / second_component edges
    recording the chunk.

    The threshold lives on the AcousticLexicon (`lex.promotion_threshold`)
    so the agent's tuning Rules can adjust it as graph data. The
    rule pulls the lex into the match via `(lex, has_entry, first)`.
    """
    from substrate_rs import (
        And, Attr, Eq, Gte, Lit, Not, Var,
    )
    where = And(items=(
        Eq(a=Attr(Var("cap"), "mode"), b=Lit("active")),
        Gte(a=Attr(Var("b"), "count"),
            b=Attr(Var("lex"), "promotion_threshold")),
        Not(arg=Eq(a=Attr(Var("b"), "promoted"), b=Lit(True))),
    ))
    return {
        "id": "promote_bigram_to_sign",
        "match": [
            ["lex", "has_entry", "first"],
            ["lex", "regulated_by", "cap"],
            ["b", "first_sign", "first"],
            ["b", "second_sign", "second"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["add_node", "sign", "AcousticSign", {
                "hearings": 0,
                "composed": True,
                "promoted_at_count": _enc(Attr(Var("b"), "count")),
            }],
            ["add_edge", "sign", "first_component", "first"],
            ["add_edge", "sign", "second_component", "second"],
            ["add_edge", "lex", "has_entry", "sign"],
            ["add_edge", "b", "promoted_to", "sign"],
            ["set_attr", "b", "promoted", True],
        ],
    }


def _compose_utterance_rule() -> dict:
    """When a base Utterance pair matches an existing compositional
    AcousticSign's component edges, mint a new Utterance heard_as
    that sign spanning the pair's combined time window. The
    compositional sign's hearings counter ticks up too. Gated on
    cap.mode != "off" — when the agent's Assessment-driven Rule
    has escalated to off, even compose stops walking the
    follows-pile."""
    from substrate_rs import (
        And, Attr, Eq, Lit, Minus, Not, Plus, Var,
    )
    where = And(items=(
        Not(arg=Eq(a=Attr(Var("cap"), "mode"), b=Lit("off"))),
        Not(arg=Eq(a=Attr(Var("utt_a"), "composed_emitted"),
                    b=Lit(True))),
        Not(arg=Eq(a=Attr(Var("utt_a"), "composed"), b=Lit(True))),
        Not(arg=Eq(a=Attr(Var("utt_b"), "composed"), b=Lit(True))),
    ))
    return {
        "id": "compose_utterance",
        "match": [
            ["utt_b", "follows", "utt_a"],
            ["utt_a", "from_stream", "stream"],
            ["utt_a", "heard_as", "sign_a"],
            ["utt_b", "heard_as", "sign_b"],
            ["sign", "first_component", "sign_a"],
            ["sign", "second_component", "sign_b"],
            ["lex", "regulated_by", "cap"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["add_node", "utt_c", "Utterance", {
                "start_time_s": _enc(Attr(Var("utt_a"), "start_time_s")),
                "end_time_s": _enc(Attr(Var("utt_b"), "end_time_s")),
                "duration_s": _enc(Minus(
                    a=Attr(Var("utt_b"), "end_time_s"),
                    b=Attr(Var("utt_a"), "start_time_s"))),
                "composed": True,
            }],
            ["add_edge", "utt_c", "from_stream", "stream"],
            ["add_edge", "utt_c", "heard_as", "sign"],
            ["set_attr", "sign", "hearings",
             _enc(Plus(items=(Attr(Var("sign"), "hearings"), Lit(1))))],
            ["set_attr", "utt_a", "composed_emitted", True],
        ],
    }


def _tune_promotion_threshold_raise_rule() -> dict:
    """When too many bigrams are promoting (rate > _PROMOTION_RATE_HIGH)
    the threshold is too permissive — chunks become noise. Raise it
    by tp.step. Cooldown via lex.promotion_tuned_at_n_bigrams."""
    from substrate_rs import (
        And, Attr, Count, Div, Eq, Filter, Gte, Lit, Lt, Minus, Neighbours,
        Not, Or, Plus, Var,
    )
    n_bigrams = Count(source=Filter(
        source=Neighbours(Var("lex"), "has_promoted_bigram_in"),
        var_name="x",
        predicate=Lit(True),
    ))
    # Bigram count via type filter — every BigramObservation in the
    # substrate that has first_sign pointing into this lex's signs.
    # Simpler: track all bigrams as a list — count via "any_bigram"
    # edge on a stable index node. For V1 we count bigrams by
    # matching them in the lex's "tracks_bigram" set.
    # Pragmatic alternative: use the n_bigrams attr maintained on the
    # lex by a separate counter rule. To keep this Rule self-contained,
    # we count BigramObservations connected via the new
    # `lex tracks_bigram b` edge laid down at bigram-creation time.
    bigrams_in_lex = Neighbours(Var("lex"), "tracks_bigram")
    n_total = Count(source=bigrams_in_lex)
    n_promoted = Count(source=Filter(
        source=bigrams_in_lex,
        var_name="b",
        predicate=Eq(a=Attr(Var("b"), "promoted"), b=Lit(True)),
    ))
    rate = Div(a=n_promoted, b=n_total)
    where = And(items=(
        Gte(a=n_total, b=Lit(_TUNE_MIN_BIGRAMS_TO_JUDGE)),
        Lt(a=Attr(Var("lex"), "promotion_threshold"),
           b=Attr(Var("tp"), "max")),
        Gte(a=rate, b=Lit(_PROMOTION_RATE_HIGH)),
        Eq(a=Attr(Var("tp"), "attr_name"), b=Lit("promotion_threshold")),
        Or(items=(
            Not(arg=Attr(Var("lex"), "promotion_tuned_at_n_bigrams")),
            Gte(a=Minus(a=n_total,
                          b=Attr(Var("lex"),
                                  "promotion_tuned_at_n_bigrams")),
                b=Lit(_TUNE_COOLDOWN_BIGRAMS)),
        )),
    ))
    new_thr = Plus(items=(
        Attr(Var("lex"), "promotion_threshold"),
        Attr(Var("tp"), "step"),
    ))
    return {
        "id": "tune_promotion_threshold_raise",
        "match": [["lex", "has_tunable", "tp"]],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "lex", "promotion_threshold", _enc(new_thr)],
            ["set_attr", "lex", "promotion_tuned_at_n_bigrams",
             _enc(n_total)],
            ["set_attr", "lex", "last_promotion_tune_direction", "raise"],
        ],
    }


def _tune_promotion_threshold_lower_rule() -> dict:
    """When few bigrams are promoting (rate < _PROMOTION_RATE_LOW)
    the threshold is too strict — recurring chunks aren't being
    captured. Lower it by tp.step."""
    from substrate_rs import (
        And, Attr, Count, Div, Eq, Filter, Gte, Lit, Lt, Lte, Minus, Neighbours,
        Not, Or, Var,
    )
    bigrams_in_lex = Neighbours(Var("lex"), "tracks_bigram")
    n_total = Count(source=bigrams_in_lex)
    n_promoted = Count(source=Filter(
        source=bigrams_in_lex,
        var_name="b",
        predicate=Eq(a=Attr(Var("b"), "promoted"), b=Lit(True)),
    ))
    rate = Div(a=n_promoted, b=n_total)
    where = And(items=(
        Gte(a=n_total, b=Lit(_TUNE_MIN_BIGRAMS_TO_JUDGE)),
        Gte(a=Attr(Var("lex"), "promotion_threshold"),
            b=Attr(Var("tp"), "min")),
        Lte(a=rate, b=Lit(_PROMOTION_RATE_LOW)),
        Eq(a=Attr(Var("tp"), "attr_name"), b=Lit("promotion_threshold")),
        Or(items=(
            Not(arg=Attr(Var("lex"), "promotion_tuned_at_n_bigrams")),
            Gte(a=Minus(a=n_total,
                          b=Attr(Var("lex"),
                                  "promotion_tuned_at_n_bigrams")),
                b=Lit(_TUNE_COOLDOWN_BIGRAMS)),
        )),
    ))
    new_thr = Minus(a=Attr(Var("lex"), "promotion_threshold"),
                      b=Attr(Var("tp"), "step"))
    return {
        "id": "tune_promotion_threshold_lower",
        "match": [["lex", "has_tunable", "tp"]],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "lex", "promotion_threshold", _enc(new_thr)],
            ["set_attr", "lex", "promotion_tuned_at_n_bigrams",
             _enc(n_total)],
            ["set_attr", "lex", "last_promotion_tune_direction", "lower"],
        ],
    }


def _gc_follows_when_assessed_rule() -> dict:
    """When the agent's Assessment has diagnosed compute pressure
    with cause `follows_pile_unbounded`, delete `follows` edges to
    shrink the match-enumeration surface. The Rule fires once per
    follows edge (engine iterates them); per-tick fire-cap bounds
    how many get deleted at once, so the pile drains across a few
    ticks rather than blocking on a single huge tick.

    Recovery (n_signs growth) deletes the Assessment + returns
    mode=active; if pressure builds again later the cycle repeats.
    """
    from substrate_rs import And, Attr, Eq, Lit, Var
    where = And(items=(
        Eq(a=Attr(Var("a"), "kind"), b=Lit("compute_pressure")),
        Eq(a=Attr(Var("a"), "cause"),
           b=Lit("follows_pile_unbounded")),
    ))
    return {
        "id": "gc_follows_when_assessed",
        "match": [
            ["cap", "has_assessment", "a"],
            ["utt_b", "follows", "utt_a"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["del_edge", "utt_b", "follows", "utt_a"],
        ],
    }


def _gc_utterances_when_assessed_rule() -> dict:
    """When the agent's Assessment has escalated to
    `utterance_pile_unbounded`, delete the Utterance pile itself.
    This subsumes follows GC (deleting a node also drops its
    edges) AND addresses the broader stream-data accumulation —
    compose can't run (mode=off), so the utts aren't load-bearing;
    the pipeline mints fresh ones for the next ingest.

    Per-tick fire-cap bounds how many utts go per tick — pile
    drains across a few ticks rather than blocking on one huge
    tick."""
    from substrate_rs import And, Attr, Eq, Lit, Var
    where = And(items=(
        Eq(a=Attr(Var("a"), "kind"), b=Lit("compute_pressure")),
        Eq(a=Attr(Var("a"), "cause"),
           b=Lit("utterance_pile_unbounded")),
    ))
    return {
        "id": "gc_utterances_when_assessed",
        "match": [
            ["cap", "has_assessment", "a"],
            ["utt", "from_stream", "stream"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["del_node", "utt"],
        ],
    }


def install_compositional_chunking(substrate) -> None:
    """Productions + the six Rules. The wall-cost loop (Reconsider)
    lives in domains/reconsider.py; the chunking Rules above gate
    on `Capability.mode` via the lex's `regulated_by` edge."""
    for src_t, et, tgt_t, prov in _CHUNK_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass
    for builder in (_count_bigram_existing_rule,
                     _count_bigram_new_rule,
                     _promote_bigram_rule,
                     _compose_utterance_rule,
                     _tune_promotion_threshold_raise_rule,
                     _tune_promotion_threshold_lower_rule,
                     _gc_follows_when_assessed_rule,
                     _gc_utterances_when_assessed_rule):
        substrate.add_node("Rule", builder())


__all__ = [
    "install_compositional_chunking",
    "_CHUNK_PRODUCTIONS",
    "_DEFAULT_PROMOTION_THRESHOLD",
    "_PROMOTION_THRESHOLD_MIN",
    "_PROMOTION_THRESHOLD_MAX",
    "_PROMOTION_THRESHOLD_STEP",
    "_CHUNKING_TICK_BUDGET_MS",
]
