"""interlocutor_collapse_plug — MODELLING THE PERSON as a DomainPlug into the agent's EXISTING
collapse engine (scripts/collapse_engine.run_collapse) — NOT a new tracker/classifier.

Creator's reframe (2026-07-04): LEARNING IS THE COLLAPSE MODEL AT DIFFERENT TIMESCALES, literally
homework. The interlocutor model is a collapse PREDICTING the person; its residuals at two
timescales ARE the two required operations. So we do the SAME thing move_space_collapse_plug did
(predict -> residual = a gap -> learn), pointed at a person's features instead of a maze's
transitions:

  symbols   : per feature DIMENSION, a length-2 sequence ( ("D", dim) , ("V", dim, value) ).
              The revealed context is the dimension; the "next symbol" the model must predict is
              the value the ACCUMULATED model expects for that dimension this turn.
  next_dist : the agent's accumulated feature model for the active party. For a dimension it has
              seen, it returns the counted value-distribution (the GENERALISATION prior — "this
              person talks like THIS"). A turn whose value has no learned mass is a RESIDUAL the
              manifold cannot collapse: run_collapse records a GAP (== the surprise).
  on_gap    : the residual read-off. The gapped (dim, value) is the unexplained feature — the
              perturbation (fast model) or the identity break (slow model). The LEARN step
              (consolidation / re-attribution) is done by interlocutor_model reading these gaps,
              exactly as move_space's on_gap grows the transition model.

TWO TIMESCALES = TWO PLUGS over disjoint feature subsets, each with its OWN accumulated model:
  * FAST (mood/state): affect/energy dims, a short-horizon model. A gap here = the SAME person,
    state changed -> a mood/state shift (PERTURBATION).
  * SLOW (identity): register/cadence/style dims PLUS the salient context dims (time gap, place),
    a conversation-consolidated model. Identity is the STABLE timescale, so interlocutor_model
    reads this residual behind a raised bar: a style gap RE-ATTRIBUTES only WITH a context gap (a
    DISCONTINUITY cue — the context dims are members of the slow model, so a time gap the model
    predicted as "none" is itself a slow gap) OR when a coherent style break PERSISTS across
    multiple turns (SUSTAINED). A single-turn style-only gap is a PERTURBATION (same person), never
    an identity switch — the plug supplies the residual; the model raises the evidence bar on it.

DONKEY: the predict/surprise/learn is run_collapse's, unchanged; this file only supplies the
plug (next_dist over counted features, on_gap that records the residual). No math.exp, no fit,
no bespoke same-vs-different classifier — the DECISION is the collapse residual, read out by
interlocutor_model.
"""
from __future__ import annotations

import os
import sys
from typing import Callable

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from collapse_engine import DomainPlug, run_collapse   # the agent's domain-general collapse loop


def _dim_sym(dim: str):
    return ("D", dim)


def _val_sym(dim: str, value: str):
    return ("V", dim, value)


def make_plug(model: dict, turn: dict) -> tuple:
    """Build the DomainPlug that collapses `turn`'s features against the accumulated `model`.

    `model` : {dim: {value: count}} — the party's accumulated feature counts (the homework).
    `turn`  : {dim: value} — this turn's observed features for THIS timescale's dims.

    Returns (plug, residual) where `residual` is the list the plug's on_gap fills with the
    (dim, value) pairs the model could NOT predict this turn — the collapse residual itself.
    """
    targets = [(_dim_sym(d), _val_sym(d, v)) for d, v in turn.items()]
    pool = list(targets)
    seen = set()
    for d, vc in model.items():
        for v in vc:
            s = (_dim_sym(d), _val_sym(d, v))
            if s not in seen:
                seen.add(s)
                pool.append(s)

    residual: list = []
    fired: set = set()

    def next_dist(ctx):
        # predict a value only once its dimension has been revealed as context.
        if not ctx:
            return {}
        last = ctx[-1]
        if not (isinstance(last, tuple) and last and last[0] == "D"):
            return {}
        dim = last[1]
        vc = model.get(dim)
        if not vc:
            return {}                      # UNLEARNED dim -> no prediction, no surprise (1st sight)
        tot = float(sum(vc.values()))
        if tot <= 0.0:
            return {}
        return {_val_sym(dim, v): n / tot for v, n in vc.items()}

    def on_gap(ctx, missing):
        # the residual: a dimension whose accumulated value the turn did NOT match.
        if not ctx:
            return
        last = ctx[-1]
        if not (isinstance(last, tuple) and last and last[0] == "D"):
            return
        dim = last[1]
        val = missing[2] if (isinstance(missing, tuple) and len(missing) == 3) else missing
        key = (dim, val)
        if key in fired:                   # dedup: run_collapse revisits k=1 across fractions
            return
        fired.add(key)
        residual.append(key)

    plug = DomainPlug(name="interlocutor", pool=pool, train=pool, targets=targets,
                      seq_logprob=lambda seq: 0.0, next_dist=next_dist, on_gap=on_gap)
    return plug, residual


def collapse_residual(model: dict, turn: dict) -> list:
    """Run the agent's collapse loop over `turn` against `model` and return the residual — the
    (dim, value) pairs the model could not collapse (the gaps). This IS predict->surprise; the
    LEARN (consolidate / re-attribute) is the caller's read-off of this residual, the move_space
    precedent exactly. Returns [] when the model explains the whole turn (no surprise)."""
    if not turn:
        return []
    plug, residual = make_plug(model, turn)
    seq_lp = {s: 0.0 for s in plug.pool}
    run_collapse(plug, seq_lp)             # predict + surprise; on_gap fills `residual`
    return residual


__all__ = ["make_plug", "collapse_residual", "run_collapse"]
