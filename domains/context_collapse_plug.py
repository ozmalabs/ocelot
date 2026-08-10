"""context_collapse_plug — ORDER-N CONTEXT as a DomainPlug into the agent's EXISTING collapse
engine (scripts/collapse_engine.run_collapse) — NOT a new schema/classifier/enum.

Creator's reframe (2026-07-04): "there is also order N context ... which need salience to identify
the relevance. the context should include ARBITRARY context — and critically it should include the
ability to ADD NEW CONTEXTS." Two further reframes pin the mechanism:

  * LEARNING IS COLLAPSE AT DIFFERENT TIMESCALES — so the context model is the agent's OWN collapse
    faculty pointed at the conversation's context, consolidating over turns (the same predict ->
    surprise -> learn move_space_collapse_plug/interlocutor_collapse_plug already make, one level up).
  * ADDING A NEW CONTEXT IS DYNAMIC QUANTIZATION (the project's core loop) — the context DIMENSIONS
    are a CODEBOOK; a context cue whose residual fits NO existing dimension MINTS a new context
    dimension (residual -> new context quantum), exactly like the sd loop's sd_mint_quantum. The
    codebook grows; a re-decode recognizes the minted dimension. This is what makes context
    OPEN-ENDED rather than a fixed enum.
  * SALIENCE FOR RELEVANCE (Relevance Theory) — the residual/surprise on a context dimension IS its
    salience; the salient dims are the RELEVANT context for the current turn.

THE DECODE IS TWO-LEVEL, ONE run_collapse PASS. Each observed context cue (dim, value) is a
length-3 target sequence  ( ("ROOT",) , ("D", dim) , ("V", dim, value) )  revealed symbol-by-symbol
by run_collapse. next_dist predicts the NEXT symbol from the revealed prefix, so the loop asks two
questions and records the two kinds of residual as GAPS (run_collapse's own learning-hook):

  LEVEL 1 — the DIMENSION.  ctx == (("ROOT",),) -> next_dist predicts the DIMENSION symbols the held
    CODEBOOK carries ({("D", d): mass for d in codebook}). A cue whose dimension is NOT in the
    codebook is a next symbol with zero mass -> run_collapse records a GAP -> on_gap flags it a MINT
    candidate (a new context quantum). This is dynamic quantization: the residual that fits no held
    dimension mints one. (The codebook is seeded non-empty, so LEVEL 1 always makes a prediction —
    the move_space precedent's "unlearned context -> no surprise" would silently swallow a novel
    dimension, so we predict over the held codebook instead and a novelty is a real gap.)

  LEVEL 2 — the VALUE / SALIENCE.  ctx == (("ROOT",), ("D", d)) for a HELD dim d -> next_dist
    predicts the value distribution the accumulated model expects for d (model[d]). A turn whose
    value has no learned mass is a GAP -> on_gap flags dim d SALIENT (it shifted). A steady dim
    (the value the model already expects) collapses cleanly — no gap, not salient. A held-but-
    unvalued dim (just registered, no counts) makes no prediction ({}), so its FIRST value is
    established, not "salient" — a shift needs a prior expectation to break, the move_space precedent
    exactly (first sight is never a gap).

on_gap is the residual read-off; the LEARN step (mint the dimension / consolidate the value) is the
caller's (context_model), reading these gaps — the move_space/interlocutor precedent exactly.

DONKEY: the predict/surprise is run_collapse's, unchanged. No math.exp, no fit, no bespoke residual
engine, no fixed context enum — the DECISION (mint vs salient vs steady) is the collapse residual.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from collapse_engine import DomainPlug, run_collapse   # the agent's domain-general collapse loop

_ROOT_SYM = ("ROOT",)


def _dim_sym(dim: str):
    return ("D", dim)


def _val_sym(dim: str, value):
    return ("V", dim, value)


def make_plug(codebook, model: dict, turn: dict) -> tuple:
    """Build the DomainPlug that decodes `turn`'s context cues against the held `codebook`
    (registered dimensions) + accumulated `model` (per-dim value counts), in ONE run_collapse pass.

    `codebook` : iterable[str]        — the held context dimensions (the quantization codebook).
    `model`    : {dim: {value: count}} — the consolidated value counts per dimension (the homework).
    `turn`     : {dim: value}          — this turn's observed context cues (arbitrary keys allowed).

    Returns (plug, residual) where `residual` is the dict the plug's on_gap fills:
      residual["mint"]    : [dim, ...]        — cue dims NOT in the codebook (new context quanta).
      residual["salient"] : [(dim, value), ...] — held dims whose value the model did NOT expect.
    """
    codebook = list(dict.fromkeys(str(d) for d in codebook))
    cbset = set(codebook)

    targets = [(_ROOT_SYM, _dim_sym(d), _val_sym(d, v)) for d, v in turn.items()]
    pool = list(targets)
    seen = set(pool)
    # the codebook's own decodable sequences (held dims + any values the model has seen), so the
    # pool spans the held space, not only this turn (mirrors move_space including every transition).
    for d in codebook:
        for v in (model.get(d) or {"_"}):
            s = (_ROOT_SYM, _dim_sym(d), _val_sym(d, v))
            if s not in seen:
                seen.add(s)
                pool.append(s)

    residual = {"mint": [], "salient": []}
    fired = set()

    def next_dist(ctx):
        if not ctx:
            return {}
        last = ctx[-1]
        # LEVEL 1 — predict the DIMENSION over the held codebook.
        if last == _ROOT_SYM:
            if not codebook:
                return {}
            mass = 1.0 / float(len(codebook))
            return {_dim_sym(d): mass for d in codebook}
        # LEVEL 2 — predict the VALUE the accumulated model expects for a held dimension.
        if isinstance(last, tuple) and last and last[0] == "D":
            dim = last[1]
            vc = model.get(dim)
            if not vc:
                return {}                    # registered-but-unvalued -> first value, not a shift
            tot = float(sum(vc.values()))
            if tot <= 0.0:
                return {}
            return {_val_sym(dim, v): n / tot for v, n in vc.items()}
        return {}

    def on_gap(ctx, missing):
        if not ctx:
            return
        last = ctx[-1]
        if last == _ROOT_SYM and isinstance(missing, tuple) and missing and missing[0] == "D":
            dim = missing[1]
            if dim in cbset:                 # already held (belt-and-braces) — not a mint
                return
            key = ("mint", dim)
            if key in fired:
                return
            fired.add(key)
            residual["mint"].append(dim)
        elif (isinstance(last, tuple) and last and last[0] == "D"
              and isinstance(missing, tuple) and len(missing) == 3):
            dim, val = missing[1], missing[2]
            key = ("salient", dim, val)
            if key in fired:
                return
            fired.add(key)
            residual["salient"].append((dim, val))

    plug = DomainPlug(name="context", pool=pool, train=pool, targets=targets,
                      seq_logprob=lambda seq: 0.0, next_dist=next_dist, on_gap=on_gap)
    return plug, residual


def collapse_context(codebook, model: dict, turn: dict) -> dict:
    """Run the agent's collapse loop over `turn`'s context cues against the held `codebook`/`model`
    and return the residual — {"mint": [novel dims], "salient": [(dim, value), ...]}. This IS
    predict->surprise (run_collapse); the LEARN (mint the dimension / consolidate the value) is the
    caller's read-off, the move_space/interlocutor precedent exactly. Empty turn -> empty residual."""
    if not turn:
        return {"mint": [], "salient": []}
    plug, residual = make_plug(codebook, model, turn)
    seq_lp = {s: 0.0 for s in plug.pool}
    run_collapse(plug, seq_lp)               # predict + surprise; on_gap fills `residual`
    return residual


__all__ = ["make_plug", "collapse_context", "run_collapse"]
