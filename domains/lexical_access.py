"""Lexical access seed — phoneme sequences bind to AcousticSigns.

Top of the biology-aligned auditory pathway. Takes the
PhonemeInstance time-series produced by categorical_perception,
collapses it to a phoneme-NodeID sequence (deduping consecutive
identical phonemes — a held vowel doesn't make a new word), then
looks for an existing AcousticSign in the substrate's
AcousticLexicon whose `phoneme_sequence` attr matches. If found,
its `hearings` counter increments; if not, a new sign is minted.

Re-using the speech module's AcousticSign / Utterance node types
means this layer slots straight into the existing lexicon
machinery — Concept grounding via `denotes` edges, the
speech-bridge Rule that translates AcousticSign to Mention for the
intent rules, all the chat-side infrastructure works unchanged
once a sign is grounded.

The lexicon grows monotonically across runs. Hearing the same
audio a second time hits the same AcousticSign + bumps hearings.
"""
from __future__ import annotations


_LA_PRODUCTIONS = [
    # Utterance / AcousticSign / Lexicon edges already declared by
    # the speech seed; here we just add the new "contains_phoneme"
    # edge from AcousticSign back to the Phonemes it's made of —
    # graph-level audit trail.
    ("AcousticSign", "contains_phoneme", "Phoneme",
     "lexical_access:sign_phoneme"),
    # The lexical_access Op points at the AcousticLexicon it
    # writes into. Lets the threshold-tuning Rules bring the lex
    # into their match (so they can read n_signs / singletons).
    ("Operation", "uses_lexicon", "AcousticLexicon",
     "lexical_access:op_uses_lexicon"),
    # Re-declare the per-stream pipeline-entry edge so the seed
    # loader doesn't complain if the cochlear seed wasn't loaded
    # first (defensive; cheap).
    ("AudioStream", "has_pipeline_entry", "Operation",
     "lexical_access:stream_pipeline_entry"),
    ("Operation", "feeds_into", "Operation",
     "lexical_access:operation_feeds_into"),
]


def _enc(v):
    from substrate_rs import Term
    if isinstance(v, Term):
        return {"__term__": v.to_dict()}
    return v


# Thresholds for the agent's distance_threshold-tuning Rules.
# Singleton fraction = signs heard exactly once / total signs.
_LA_SINGLETON_FRACTION_HIGH = 0.50    # raise threshold (loosen)
_LA_MIN_SIGNS_TO_LOWER = 8            # below this → lower threshold
_LA_MIN_SIGNS_TO_JUDGE = 20           # need this many to evaluate
_LA_TUNE_COOLDOWN_SIGNS = 30


def _build_raise_distance_rule() -> dict:
    """Singleton-dominated lexicon → threshold too tight → loosen.
    Bumps la_op.distance_threshold up by tp.step."""
    from substrate_rs import (
        And, Attr, Count, Div, Eq, Filter, Gte, Lit, Lt, Neighbours, Not,
        Minus, Or, Plus, Var,
    )
    where = And(items=(
        Eq(a=Attr(Var("tp"), "attr_name"),
           b=Lit("distance_threshold")),
        Gte(a=Attr(Var("lex"), "n_signs"),
            b=Lit(_LA_MIN_SIGNS_TO_JUDGE)),
        Lt(a=Attr(Var("la"), "distance_threshold"),
           b=Attr(Var("tp"), "max")),
        Gte(
            a=Div(
                a=Count(source=Filter(
                    source=Neighbours(Var("lex"), "has_entry"),
                    var_name="s",
                    predicate=Eq(a=Attr(Var("s"), "hearings"),
                                   b=Lit(1)),
                )),
                b=Count(source=Neighbours(Var("lex"), "has_entry")),
            ),
            b=Lit(_LA_SINGLETON_FRACTION_HIGH),
        ),
        Or(items=(
            Not(arg=Attr(Var("la"), "la_tuned_at_n_signs")),
            Gte(a=Minus(a=Attr(Var("lex"), "n_signs"),
                          b=Attr(Var("la"), "la_tuned_at_n_signs")),
                b=Lit(_LA_TUNE_COOLDOWN_SIGNS)),
        )),
    ))
    new_thr = Plus(items=(
        Attr(Var("la"), "distance_threshold"),
        Attr(Var("tp"), "step"),
    ))
    return {
        "id": "tune_la_distance_raise",
        "match": [
            ["la", "uses_lexicon", "lex"],
            ["la", "has_tunable", "tp"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "la", "distance_threshold", _enc(new_thr)],
            ["set_attr", "la", "la_tuned_at_n_signs",
             _enc(Attr(Var("lex"), "n_signs"))],
            ["set_attr", "la", "last_la_tune_direction", "raise"],
        ],
    }


def _build_lower_distance_rule() -> dict:
    """Too few signs (clustering too tight) → tighten the threshold
    further would only make it worse; LOWER it (tighter cluster
    criterion → more signs minted). Used when n_signs < min and
    threshold has headroom downward."""
    from substrate_rs import (
        And, Attr, Eq, Gte, Lit, Lt, Minus, Not, Or, Var,
    )
    where = And(items=(
        Eq(a=Attr(Var("tp"), "attr_name"),
           b=Lit("distance_threshold")),
        Lt(a=Attr(Var("lex"), "n_signs"),
           b=Lit(_LA_MIN_SIGNS_TO_LOWER)),
        Gte(a=Attr(Var("la"), "distance_threshold"),
            b=Attr(Var("tp"), "min")),
        Or(items=(
            Not(arg=Attr(Var("la"), "la_tuned_at_n_signs")),
            Gte(a=Minus(a=Attr(Var("lex"), "n_signs"),
                          b=Attr(Var("la"), "la_tuned_at_n_signs")),
                b=Lit(_LA_TUNE_COOLDOWN_SIGNS)),
        )),
    ))
    new_thr = Minus(a=Attr(Var("la"), "distance_threshold"),
                      b=Attr(Var("tp"), "step"))
    return {
        "id": "tune_la_distance_lower",
        "match": [
            ["la", "uses_lexicon", "lex"],
            ["la", "has_tunable", "tp"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "la", "distance_threshold", _enc(new_thr)],
            ["set_attr", "la", "la_tuned_at_n_signs",
             _enc(Attr(Var("lex"), "n_signs"))],
            ["set_attr", "la", "last_la_tune_direction", "lower"],
        ],
    }


def install_lexical_access(substrate) -> None:
    """Productions + the two distance-threshold tuning Rules. The
    per-stream pipeline op is wired by attach_lexical_access."""
    for src_t, et, tgt_t, prov in _LA_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass
    substrate.add_node("Rule", _build_raise_distance_rule())
    # NB: the symmetric lower-distance Rule existed but over-fires
    # at startup (n_signs starts at 0 and the lower-trigger covers
    # the whole pre-saturation phase), pushing the threshold below
    # its calibrated default. The raise-only loop suffices: the
    # calibrated default of 0.10 only ever needs adjustment UP
    # (when singleton fraction reveals over-segmentation). Re-enable
    # if a corpus comes along where the default is too tight.


def attach_lexical_access(
    substrate, audio_stream_nid,
    *,
    lexicon_name: str = "stt",
) -> dict:
    """Wire one lexical_access Operation downstream of the
    categorical_perception op. The lexical_access op walks
    PhonemeInstances on its stream, builds sequences, matches
    against existing AcousticSigns in the named lexicon, mints
    new signs as needed.

    Returns the op NodeID + the AcousticLexicon's NodeID.
    """
    cp_ops = [
        op for op in substrate.nodes("Operation")
        if substrate.node(op)["attrs"].get("kind") == "categorical_perception"
    ]

    # Find or create the lexicon. Multiple streams sharing the
    # substrate share the lexicon — that's how the vocabulary
    # accumulates across runs.
    lex_nid = None
    for n in substrate.nodes("AcousticLexicon"):
        if substrate.node(n)["attrs"].get("name") == lexicon_name:
            lex_nid = n
            break
    if lex_nid is None:
        from .compositional_chunking import (
            _DEFAULT_PROMOTION_THRESHOLD as _PT_DEFAULT,
            _PROMOTION_THRESHOLD_MIN as _PT_MIN,
            _PROMOTION_THRESHOLD_MAX as _PT_MAX,
            _PROMOTION_THRESHOLD_STEP as _PT_STEP,
            _CHUNKING_TICK_BUDGET_MS as _CHUNK_BUDGET,
        )
        from .tunable_parameter import mint_tunable
        from .reconsider import ensure_substrate_root, ensure_capability
        rust = substrate._inner if hasattr(substrate, "_inner") else substrate
        lex_nid = rust.add_node("AcousticLexicon", {
            "name": lexicon_name,
            "origin": "lexical_access_seed",
            "n_signs": 0,
            "match_threshold": 1.0,  # sequence equality, not cosine
            # Compositional-chunking promotion threshold. Lives on
            # the lex so the chunking tuning Rules can read + edit
            # it as graph data (via the TunableParameter below).
            "promotion_threshold": int(_PT_DEFAULT),
        })
        mint_tunable(
            substrate, lex_nid,
            attr_name="promotion_threshold",
            min_value=_PT_MIN, max_value=_PT_MAX, step=_PT_STEP,
            description="Bigram count required to promote a recurring "
                        "sign pair into a compositional AcousticSign.",
        )
        # Reconsider regulation — the chunking Rules gate on a
        # Capability node whose mode is flipped by the substrate's
        # tick-cost budget loop. Lex --regulated_by--> Capability
        # is the binding the gated Rules read from.
        root = ensure_substrate_root(substrate)
        chunking_cap = ensure_capability(
            substrate, root,
            name="chunking",
            tick_budget_ms=float(_CHUNK_BUDGET),
        )
        substrate.add_edge(lex_nid, "regulated_by", chunking_cap)

    la_nid = substrate.add_node("Operation", {
        "kind": "lexical_access",
        "lexicon_name": lexicon_name,
    })
    substrate.add_edge(la_nid, "uses_lexicon", lex_nid)
    # TunableParameter for distance_threshold — the DTW-Euclidean
    # match cut-off. Range tuned for unit-normalised multi-channel
    # trajectories: under ~0.02 mints a sign per utterance (no
    # clustering); over ~0.20 collapses everything to a few signs.
    try:
        from .tunable_parameter import mint_tunable
        mint_tunable(
            substrate, la_nid,
            attr_name="distance_threshold",
            min_value=0.02, max_value=0.30, step=0.02,
            description="DTW-Euclidean cut-off for matching a new "
                        "trajectory to an existing AcousticSign. "
                        "Lower = tighter clusters / more signs; "
                        "higher = looser clusters / fewer signs.",
        )
    except Exception:
        pass
    # Wire feeds_into from:
    #  - every patch_evaluate op (lexical_access reads their
    #    multi-channel envelope buffers as the trajectory),
    #  - every broadband_coincidence op (so BroadbandOnset events
    #    exist before lexical_access dispatches; used to slice the
    #    trajectory at word boundaries),
    #  - every categorical_perception op (so Phonemes are minted
    #    for graph introspection; not load-bearing for matching).
    for op in substrate.nodes("Operation"):
        kind = substrate.node(op)["attrs"].get("kind")
        if kind in ("patch_evaluate", "broadband_coincidence",
                      "categorical_perception", "sonority_valley"):
            substrate.add_edge(op, "feeds_into", la_nid)
        # Bind sonority_valley ops to this lexicon — the auto-tuning
        # Rules match (sv, tunes, lex) and rewrite sv.depth_threshold
        # based on the lexicon shape they produce.
        if kind == "sonority_valley":
            substrate.add_edge(op, "tunes", lex_nid)
    return {"op": la_nid, "lexicon": lex_nid}


__all__ = [
    "install_lexical_access",
    "attach_lexical_access",
    "_LA_PRODUCTIONS",
]
