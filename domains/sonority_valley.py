"""Sonority-valley seed — word boundaries from envelope geometry +
an agent-driven auto-tuner for the boundary-depth threshold.

The op sums per-band envelope buffers and emits SonorityValley graph
nodes at deep minima of the smoothed total envelope. Used by
lexical_access as word-boundary candidates in place of BroadbandOnset
clustering when present — critical for continuous speech.

The seed also installs two graph-resident Rules that the agent fires
on every `sub.tick()`. They read the AcousticLexicon's shape and
nudge the sonority_valley op's `depth_threshold` attr:

  raise — when the lexicon is singleton-dominated (most signs heard
          once → segmenter is cutting mid-word, fragments don't
          generalise), raise the threshold so cuts are fewer and
          deeper.
  lower — when the lexicon is over-collapsed (very few signs, each
          heard many times → whole phrases sharing one trajectory),
          lower the threshold so cuts are more numerous and shallower.

Cooldown is measured in fresh lexicon entries — the agent waits for
the lexicon to grow by `_TUNE_COOLDOWN_SIGNS` more entries before
re-tuning, so the signal it reads reflects the new threshold.

The `tunes` edge from the per-stream sonority_valley op to the
shared AcousticLexicon is the binding the Rules match against;
lexical_access creates the edge after ensuring the lexicon.
"""
from __future__ import annotations


_SV_PRODUCTIONS = [
    ("AudioStream", "has_sonority_valley", "SonorityValley",
     "sonority_valley:stream_valley"),
    # `tunes` binds a sonority_valley Operation to the AcousticLexicon
    # whose shape drives its own depth_threshold.
    ("Operation", "tunes", "AcousticLexicon",
     "sonority_valley:op_tunes_lexicon"),
    # Defensive re-declarations (cheap; idempotent).
    ("AudioStream", "has_pipeline_entry", "Operation",
     "sonority_valley:stream_pipeline_entry"),
    ("Operation", "feeds_into", "Operation",
     "sonority_valley:operation_feeds_into"),
]


# Tuner constants. Conservative — the agent nudges and re-evaluates
# after enough new signs have accumulated to read the lexicon shape
# again.
_TUNE_STEP = 0.05
_TUNE_UPPER = 0.60
_TUNE_LOWER = 0.10
_TUNE_COOLDOWN_SIGNS = 20
_TUNE_MIN_SIGNS_TO_JUDGE = 30
_SINGLETON_FRACTION_HIGH = 0.40    # > this → over-segmented / noisy
_MEAN_HEARINGS_HIGH = 200.0        # > this → too-coarse, under-segmenting


def _enc(v):
    """Effect-argument encoder: wrap DSL Terms as {"__term__": term_json}
    so the Rust rule engine knows to evaluate them at fire-time."""
    from substrate_rs import Term
    if isinstance(v, Term):
        return {"__term__": v.to_dict()}
    return v


def _build_raise_rule_attrs() -> dict:
    """Rule: when the lexicon is dominated by signs heard exactly once
    AND there's headroom to raise, bump depth_threshold up by one
    step. Singleton-heavy lexicons happen when the segmenter cuts
    mid-word and trajectory matching can't reuse fragments.

    Bounds + step are read from the TunableParameter node attached
    to the sv Op via has_tunable, so the agent can edit them as
    graph data.
    """
    from substrate_rs import (
        And, Attr, Count, Div, Eq, Filter, Gte, Lit, Lt, Neighbours, Not,
        Minus, Or, Plus, Var,
    )
    where = And(items=(
        Eq(a=Attr(Var("sv"), "kind"), b=Lit("sonority_valley")),
        Eq(a=Attr(Var("tp"), "attr_name"), b=Lit("depth_threshold")),
        Gte(a=Attr(Var("lex"), "n_signs"),
            b=Lit(_TUNE_MIN_SIGNS_TO_JUDGE)),
        Lt(a=Attr(Var("sv"), "depth_threshold"),
           b=Attr(Var("tp"), "max")),
        Gte(
            a=Div(
                a=Count(source=Filter(
                    source=Neighbours(Var("lex"), "has_entry"),
                    var_name="s",
                    predicate=Eq(a=Attr(Var("s"), "hearings"), b=Lit(1)),
                )),
                b=Count(source=Neighbours(Var("lex"), "has_entry")),
            ),
            b=Lit(_SINGLETON_FRACTION_HIGH),
        ),
        Or(items=(
            Not(arg=Attr(Var("sv"), "tuned_at_n_signs")),
            Gte(a=Minus(a=Attr(Var("lex"), "n_signs"),
                          b=Attr(Var("sv"), "tuned_at_n_signs")),
                b=Lit(_TUNE_COOLDOWN_SIGNS)),
        )),
    ))
    new_thr = Plus(items=(Attr(Var("sv"), "depth_threshold"),
                            Attr(Var("tp"), "step")))
    return {
        "id": "tune_sonority_raise",
        "match": [
            ["sv", "tunes", "lex"],
            ["sv", "has_tunable", "tp"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "sv", "depth_threshold", _enc(new_thr)],
            ["set_attr", "sv", "tuned_at_n_signs",
             _enc(Attr(Var("lex"), "n_signs"))],
            ["set_attr", "sv", "last_tune_direction", "raise"],
        ],
    }


def _build_lower_rule_attrs() -> dict:
    """Rule: when mean hearings per sign is very high (whole phrases
    collapsing into the same trajectory) AND there's headroom to
    lower, bump depth_threshold down. Bounds + step read from the
    TunableParameter on the sv Op."""
    from substrate_rs import (
        And, Attr, Count, Div, Eq, Gte, Lit, Neighbours, Not, Minus, Or,
        Sum, Var,
    )
    mean_hearings = Div(
        a=Sum(
            source=Neighbours(Var("lex"), "has_entry"),
            var_name="s",
            value=Attr(Var("s"), "hearings"),
        ),
        b=Count(source=Neighbours(Var("lex"), "has_entry")),
    )
    where = And(items=(
        Eq(a=Attr(Var("sv"), "kind"), b=Lit("sonority_valley")),
        Eq(a=Attr(Var("tp"), "attr_name"), b=Lit("depth_threshold")),
        Gte(a=Attr(Var("lex"), "n_signs"),
            b=Lit(_TUNE_MIN_SIGNS_TO_JUDGE)),
        Gte(a=Attr(Var("sv"), "depth_threshold"),
            b=Attr(Var("tp"), "min")),
        Gte(a=mean_hearings, b=Lit(_MEAN_HEARINGS_HIGH)),
        Or(items=(
            Not(arg=Attr(Var("sv"), "tuned_at_n_signs")),
            Gte(a=Minus(a=Attr(Var("lex"), "n_signs"),
                          b=Attr(Var("sv"), "tuned_at_n_signs")),
                b=Lit(_TUNE_COOLDOWN_SIGNS)),
        )),
    ))
    new_thr = Minus(a=Attr(Var("sv"), "depth_threshold"),
                      b=Attr(Var("tp"), "step"))
    return {
        "id": "tune_sonority_lower",
        "match": [
            ["sv", "tunes", "lex"],
            ["sv", "has_tunable", "tp"],
        ],
        "where": where.to_dict(),
        "effect": [
            ["set_attr", "sv", "depth_threshold", _enc(new_thr)],
            ["set_attr", "sv", "tuned_at_n_signs",
             _enc(Attr(Var("lex"), "n_signs"))],
            ["set_attr", "sv", "last_tune_direction", "lower"],
        ],
    }


def install_sonority_valley(substrate) -> None:
    """Productions + the two auto-tuning Rules. Per-stream pipeline op
    wiring happens via attach_sonority_valley."""
    for src_t, et, tgt_t, prov in _SV_PRODUCTIONS:
        try:
            substrate.add_production({
                "src": {"type": src_t, "var": "src"},
                "edge_type": et,
                "tgt": {"type": tgt_t, "var": "tgt"},
                "provenance": prov,
            })
        except Exception:
            pass
    substrate.add_node("Rule", _build_raise_rule_attrs())
    substrate.add_node("Rule", _build_lower_rule_attrs())


def attach_sonority_valley(
    substrate, audio_stream_nid,
    *,
    smoothing_ms: float = 30.0,
    min_separation_ms: float = 80.0,
    depth_threshold: float = 0.30,
) -> dict:
    """Wire the sonority_valley Operation into this stream's pipeline.
    The op is SHARED across all streams: if one already exists, reuse
    it and wire the new stream's envelope ops in. That way the agent's
    auto-tuner mutates a single attr that every future stream picks up.

    lexical_access adds the `tunes` edge after ensuring the
    AcousticLexicon, closing the agent-driven tuning loop.
    """
    sv_nid = None
    for op in substrate.nodes("Operation"):
        if substrate.node(op)["attrs"].get("kind") == "sonority_valley":
            sv_nid = op
            break
    if sv_nid is None:
        sv_nid = substrate.add_node("Operation", {
            "kind": "sonority_valley",
            "smoothing_ms": float(smoothing_ms),
            "min_separation_ms": float(min_separation_ms),
            "depth_threshold": float(depth_threshold),
        })
        # Document depth_threshold as a TunableParameter so the
        # tuning Rules can read bounds + step from graph data (and
        # the agent can introspect what's tunable).
        from .tunable_parameter import mint_tunable
        mint_tunable(
            substrate, sv_nid,
            attr_name="depth_threshold",
            min_value=_TUNE_LOWER, max_value=_TUNE_UPPER, step=_TUNE_STEP,
            description="Relative drop (peak-valley)/peak required "
                        "for a sonority minimum to count as a word "
                        "boundary. Lower = more cuts, higher = fewer.",
        )
    # Wire feeds_into from every envelope op on this stream (the new
    # ones won't have it yet; existing edges from prior streams stay
    # as-is — pipeline walker only visits ops reachable from the
    # current stream's has_pipeline_entry).
    stream_entries = set(substrate.neighbours(
        audio_stream_nid, "has_pipeline_entry"))
    for op in substrate.nodes("Operation"):
        if substrate.node(op)["attrs"].get("kind") != "envelope":
            continue
        # Only this stream's envelopes — find via the gammatone that
        # feeds into it (gammatones are the stream's pipeline entries).
        upstream = set(substrate.in_neighbours(op, "feeds_into"))
        if not upstream.isdisjoint(stream_entries):
            substrate.add_edge(op, "feeds_into", sv_nid)
    return {"op": sv_nid}


__all__ = [
    "install_sonority_valley",
    "attach_sonority_valley",
    "_SV_PRODUCTIONS",
]
