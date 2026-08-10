"""context_model — ORDER-N CONTEXT (the recent cadence/conversation, the place, the time on BOTH
ends) as the agent's OWN COLLAPSE FACULTY at the CONTEXT timescale, consolidating over turns, with
an OPEN-ENDED codebook that MINTS a new context dimension whenever a cue fits none of the held ones
(dynamic quantization at the context timescale). Creator's reframe (2026-07-04): "there is also
order N context ... which need salience to identify the relevance. the context should include
ARBITRARY context — and critically it should include the ability to ADD NEW CONTEXTS."

This is a WORLD-ADAPTER-SHAPED host layer (CLAUDE.md): it OBSERVES the turn's context cues
(mechanical text/context->graph), writes them onto a persistent, singleton `Context` node that
ACCUMULATES across turns, and routes EVERY decision (mint a new dimension / which dims are salient)
through the agent's domain-general collapse loop (`domains.context_collapse_plug.collapse_context`
-> `scripts/collapse_engine.run_collapse`). It contains NO bespoke residual engine, NO fixed context
enum, and NO hand-rolled quantizer — the decisions ARE the collapse residual.

THE THREE THINGS THE COLLAPSE RESIDUAL DECIDES (one run_collapse pass, see context_collapse_plug):

  1. ADD-NEW-CONTEXT == DYNAMIC QUANTIZATION.  A cue whose DIMENSION is not in the held codebook is
     a LEVEL-1 residual (a next-symbol the codebook could not predict) -> MINT that dimension (grow
     the codebook, the `Context.codebook` attr) -> RE-DECODE: the minted dimension is now held and
     recognized (residual["mint"] no longer names it). This is sd_mint_quantum -> codebook grows ->
     sd_redecode, one level up, realized through run_collapse's own learning-hook (on_gap) — the
     move_space_collapse_plug precedent (a residual grows Γ) pointed at context DIMENSIONS.

  2. SALIENCE -> RELEVANCE.  A held dimension whose VALUE the accumulated model did NOT expect is a
     LEVEL-2 residual -> that dimension is SALIENT this turn (it shifted). A steady dimension (the
     value the model already expects) collapses cleanly — not salient. The residual IS the salience;
     the salient dims are the RELEVANT context (Relevance Theory) the Conceptualizer/comprehension
     should consult.

  3. CONSOLIDATION (the homework).  Every cue's value is counted onto the Context node — the model
     grows turn over turn, so "steady vs shifted" is measured against a real accumulated expectation.

THE FEEDS:
  * interlocutor identity — `interlocutor_context(report)` turns the SALIENT context dims into the
    {time_gap, place_changed, channel_changed} flags `interlocutor_model.observe_features` reads, so
    a richer context shift enters the interlocutor's SLOW residual and tips re-attribution more
    decisively (the Build-2 seam: `interlocutor_model.CONTEXT_DIMS`, now extended with `channel`).
  * the Conceptualizer / audience design — `salient_context(agent)` exposes the relevant dims for
    the current turn; audience-design/relevance reads what context matters NOW.

DONKEY=0: no fit, no gradient, no LM. predict/surprise is run_collapse's; learning is
structure-accumulation (counts + codebook growth = grow Γ), the move_space/interlocutor precedent.
"""
from __future__ import annotations

import re
from typing import Optional

from domains import frame as _fr
from domains.context_collapse_plug import collapse_context

# --------------------------------------------------------------------------- #
#  SEEDED context dimensions — the order-N context the creator named.
# --------------------------------------------------------------------------- #
#   cadence      : the recent discourse RHYTHM (turn length bucket).
#   place        : the CHANNEL / SETTING of the conversation.
#   time_self    : the AGENT's local time-of-day (one end of "time on both ends").
#   time_other   : the INTERLOCUTOR's local time-of-day (the other end).
#   duration     : how long the conversation has been running.
#   gap          : the time gap since the last turn.
SEEDED_DIMS = ("cadence", "place", "time_self", "time_other", "duration", "gap")

# context keys consumed into the seeded dims above — every OTHER key in a context dict becomes an
# ARBITRARY cue (its own dimension), which is what makes the codebook open-ended: pass a new key,
# get a new context. `time_gap` is an alias the interlocutor path already uses for `gap`.
_CONTROL_KEYS = frozenset({"place", "time_self", "time_other", "duration", "gap", "time_gap",
                           "channel_changed", "place_changed"})


# --------------------------------------------------------------------------- #
#  OBSERVE — mechanical turn/context -> cue dict (no decision over graph state).
# --------------------------------------------------------------------------- #

def _cadence_of(nwords: int) -> str:
    return "short" if nwords <= 4 else "medium" if nwords <= 12 else "long"


def _tod(v) -> str:
    """Bucket a local time-of-day. Accepts an hour (int/float) or an explicit label."""
    if v is None:
        return "unknown"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        h = int(v) % 24
        return ("morning" if 5 <= h < 12 else "afternoon" if 12 <= h < 17
                else "evening" if 17 <= h < 21 else "night")
    return str(v)


def _duration_bucket(v) -> str:
    if v is None:
        return "unknown"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        n = float(v)
        return "brief" if n < 3 else "short" if n < 10 else "long"
    return str(v)


def _gap_bucket(v) -> str:
    if v is None:
        return "none"
    if isinstance(v, bool):
        return "long" if v else "none"
    if isinstance(v, (int, float)):
        n = float(v)
        return "none" if n <= 0 else "short" if n < 300 else "long"
    return str(v)


def observe_cues(agent, text: str, context: Optional[dict] = None) -> dict:
    """Extract this turn's context cues {dim: value}. Mechanical text/context->graph translation, no
    conditional over graph state. Seeded dims (cadence/place/time-both-ends/duration/gap) plus EVERY
    non-control key in `context` as its OWN arbitrary dimension (the open-ended part)."""
    context = context or {}
    nwords = len(re.findall(r"[A-Za-z']+", str(text)))
    cues = {
        "cadence": _cadence_of(nwords),
        "place": str(context.get("place") or "default"),
        "time_self": _tod(context.get("time_self")),
        "time_other": _tod(context.get("time_other")),
        "duration": _duration_bucket(context.get("duration")),
        "gap": _gap_bucket(context.get("gap", context.get("time_gap"))),
    }
    # ARBITRARY / open-ended cues — any other context key is a dimension of its own.
    for k, v in context.items():
        if k in _CONTROL_KEYS or k in cues:
            continue
        cues[str(k)] = str(v)
    return cues


# --------------------------------------------------------------------------- #
#  CONTEXT graph node — persistent, accumulating, codebook-carrying.
# --------------------------------------------------------------------------- #

def _context_node(agent):
    """The singleton persistent Context node — seeded with SEEDED_DIMS as its codebook. Created on
    first use, then accumulated across turns (name/known-shape parallels the Interlocutor Party)."""
    for n in agent.s.nodes("ConversationContext"):
        return n
    node = agent.s.add_node("ConversationContext", {
        "codebook": list(SEEDED_DIMS),
        "feat_counts": {},
        "turns": 0,
        "active": True,
    })
    return node


def _codebook(agent, node) -> list:
    return list(agent.s.node(node)["attrs"].get("codebook") or [])


def _model_of(agent, node) -> dict:
    fc = agent.s.node(node)["attrs"].get("feat_counts") or {}
    return {d: dict(v) for d, v in fc.items()}


def _mint_dim(agent, node, dim: str) -> None:
    """DYNAMIC QUANTIZATION learn step: a residual that fit no held dimension MINTS a new context
    dimension — grow the codebook (the `Context.codebook` attr). Idempotent."""
    cb = _codebook(agent, node)
    if dim not in cb:
        cb.append(dim)
        agent.inner.set_attr(node, "codebook", cb)


def _consolidate(agent, node, cues: dict) -> None:
    """LEARN (homework): count this turn's cue values onto the Context node (grow the model). Native
    graph write — the same count-accumulation `interlocutor_model._consolidate` performs."""
    at = agent.s.node(node)["attrs"]
    fc = {k: dict(v) for k, v in (at.get("feat_counts") or {}).items()}
    for d, v in cues.items():
        fc.setdefault(d, {})
        fc[d][v] = fc[d].get(v, 0) + 1
    agent.inner.set_attr(node, "feat_counts", fc)
    agent.inner.set_attr(node, "turns", int(at.get("turns", 0)) + 1)


# --------------------------------------------------------------------------- #
#  THE TURN — observe, collapse-decode, mint-on-residual, read salience, learn.
# --------------------------------------------------------------------------- #

def observe_turn(agent, text: str, context: Optional[dict] = None) -> dict:
    """One turn of context modelling. OBSERVE cues; DECODE them against the held codebook/model via
    the collapse loop; the RESIDUAL decides:
      * a cue dim not in the codebook -> MINT a new context dimension (grow the codebook), then
        RE-DECODE (the minted dim is now recognized — dynamic quantization closes);
      * a held dim whose value the model did not expect -> that dim is SALIENT (relevant) this turn.
    Then LEARN: consolidate every cue's value into the model. Returns a report dict."""
    cues = observe_cues(agent, text, context)
    node = _context_node(agent)
    codebook_before = _codebook(agent, node)
    model = _model_of(agent, node)

    # DECODE (predict -> surprise) — one run_collapse pass, both residual levels.
    residual = collapse_context(codebook_before, model, cues)
    minted = list(residual["mint"])
    salient = list(residual["salient"])

    # MINT: grow the codebook with each novel dimension (dynamic quantization).
    for d in minted:
        _mint_dim(agent, node, d)

    # RE-DECODE against the GROWN codebook: the minted dims are now held -> recognized (no longer a
    # mint). This is sd_redecode after codebook growth — the loop closes, no Python while-loop.
    codebook_after = _codebook(agent, node)
    residual_after = collapse_context(codebook_after, model, cues)
    recognized = [d for d in minted if d not in residual_after["mint"]]

    # SALIENCE -> RELEVANCE: the residual IS the salience; the salient dims are the relevant context.
    salient_dims = sorted({d for d, _v in salient})
    salience = {d: 1.0 for d in salient_dims}     # residual-driven (Relevance Theory), not a payoff

    # LEARN: consolidate the turn (grow the model for the next turn's expectation).
    _consolidate(agent, node, cues)

    report = {
        "node": node,
        "cues": cues,
        "minted": minted,
        "recognized_after_mint": recognized,
        "salient": salient,
        "salient_dims": salient_dims,
        "salience": salience,
        "codebook_before": codebook_before,
        "codebook_after": codebook_after,
    }
    agent._last_context_turn = report
    return report


# --------------------------------------------------------------------------- #
#  THE FEEDS — the salient context into the interlocutor identity + the Conceptualizer.
# --------------------------------------------------------------------------- #

def interlocutor_context(report: dict) -> dict:
    """Turn the SALIENT context dims (this turn's residual) into the context flags
    `interlocutor_model.observe_features` reads. A richer context shift -> more flags -> a bigger
    slow residual -> a more decisive re-attribution (the Build-2 seam). `channel` is the extra dim
    beyond time_gap/place that CONTEXT_DIMS was extended to carry."""
    sd = set(report.get("salient_dims") or [])
    ctx: dict = {}
    if "gap" in sd:
        ctx["time_gap"] = True
    if "place" in sd:
        ctx["place_changed"] = True
    if "channel" in sd:
        ctx["channel_changed"] = True
    return ctx


def salient_context(agent) -> dict:
    """The RELEVANT context for the current turn — the salient dims + their observed values — the
    Conceptualizer/audience-design reads this ("what context matters now"). Reads the last turn's
    report (mechanical query, no decision). Empty when nothing shifted."""
    report = getattr(agent, "_last_context_turn", None)
    if not report:
        return {"salient_dims": [], "values": {}}
    cues = report.get("cues") or {}
    dims = report.get("salient_dims") or []
    return {"salient_dims": list(dims), "values": {d: cues.get(d) for d in dims}}


def context_frame(agent):
    """EXPOSE THE ORDER-N CONTEXT AS A FRAME (the creator's Frame ontology, 2026-07-04). The context
    model is ALREADY a weighted set of dimensions — its codebook dims and their per-turn SALIENCE (the
    residual) — so this is a THIN adapter, not a rebuild: a graph-resident Frame node whose dimensions
    are the codebook dims, LOG-weighted so the SALIENT (relevant) dims sit above the steady ones. The
    Conceptualizer / audience-design read "what context matters now" as frame-membership + weight
    instead of a flag list. Refreshed each turn under a stable key."""
    snap = model_snapshot(agent)
    salient = set((getattr(agent, "_last_context_turn", None) or {}).get("salient_dims") or [])
    # SALIENCE -> relative weight: a salient dim carries more LINEAR weight than a steady one (the
    # residual is the relative weighting); build_frame LOG-scales it, so the salient dims sit strictly
    # above the steady ones. Equal (all-steady) dims -> equal weights (a flat context frame).
    dims = {d: (2.0 if d in salient else 1.0) for d in snap["codebook"]}
    return _fr.build_frame(agent, dims, "context_frame")


def model_snapshot(agent) -> dict:
    """The accumulated context model — the codebook (registered dims, seeded + minted) and the
    per-dim value counts consolidated over turns. Pure graph read for scripts/tests to print."""
    node = _context_node(agent)
    at = agent.s.node(node)["attrs"]
    return {"codebook": list(at.get("codebook") or []),
            "feat_counts": {d: dict(v) for d, v in (at.get("feat_counts") or {}).items()},
            "turns": int(at.get("turns", 0))}


__all__ = ["SEEDED_DIMS", "observe_cues", "observe_turn",
           "interlocutor_context", "salient_context", "context_frame", "model_snapshot"]
