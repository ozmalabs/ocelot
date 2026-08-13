"""interlocutor_model — the PERSISTENT model of WHO the agent is talking to, built as the agent's
OWN COLLAPSE FACULTY pointed at the person at TWO TIMESCALES (creator's reframe 2026-07-04:
learning is the collapse model at different timescales, literally homework).

This is a WORLD-ADAPTER-SHAPED host layer (CLAUDE.md): it OBSERVES the interlocutor's features
from each utterance (mechanical text->graph), writes them onto a persistent Party (Interlocutor)
node that ACCUMULATES across turns, and routes the same-vs-different DECISION through the agent's
domain-general collapse loop (`domains.interlocutor_collapse_plug.collapse_residual` ->
`scripts/collapse_engine.run_collapse`). It contains NO bespoke residual engine and NO hand-rolled
same-vs-different classifier: the decision IS the collapse residual, at two timescales.

  * PERTURBATION (same person, state changed)  = a FAST/graded residual (affect/energy) against
    the party's short-horizon model -> record a mood/state shift on the SAME party.
  * IDENTIFICATION (likely another person)      = a SLOW/STRUCTURED residual (register/cadence/
    style + salient context: a time gap, a place change) against the conversation-consolidated
    model -> RE-ATTRIBUTE to a DIFFERENT party.

IDENTITY IS THE SLOW TIMESCALE — it must be STABLE (creator's collapse-at-timescales framing).
A single turn's style/cadence residual is a FAST perturbation (mood/state, SAME person), NOT a new
identity: a long formal intro followed by a short formal question is one person whose cadence
varied, not two people. Re-attribution therefore clears a raised EVIDENCE BAR — it fires only on:
  (a) a real DISCONTINUITY cue — a CONTEXT gap (time_gap / place / channel), the genuine evidence
      for a different person, occurring ALONGSIDE a style break; OR
  (b) a SUSTAINED style mismatch — a coherent style break that PERSISTS across MULTIPLE turns (the
      slow signal), tracked as a consecutive-style-mismatch counter on the party.
A single-turn style-only shift with NO discontinuity cue is a PERTURBATION, never an identity
switch. An ESTABLISHED party (observed / self-identified) therefore keeps INERTIA: it is never
abandoned on one turn's residual — only a discontinuity or a sustained break re-attributes away
from it.

Context evidence ENTERS the residual (not a side-channel if/else): the context dims (time_gap,
place, channel) are members of the SLOW model, so a time gap the model consolidated as "none" is
itself a slow gap. A style break therefore re-attributes WITH a context gap (a) and — without one —
consolidates (mood/steady) until it PERSISTS (b). The sustained signal is measured against the
party's accumulated PLURALITY (the value the consolidated model most expects), which survives
consolidation: a single-dim wobble is absorbed and clears, a coherent multi-dim break keeps
contradicting the plurality and accrues the streak.

THE FEED (why this exists): the accumulated Party carries `observed=True` + `known_concepts`, the
exact `{id, observed, known_concepts}` shape `world_adapter._interlocutor_snapshot` reads and
`domains.audience_driven_production.audience_model` grounds. So a MODELLED interlocutor becomes a
GROUNDED audience, and the Conceptualizer (domains/conceptualizer.py) finally designs for a real,
accumulating person instead of an empty audience every turn.

DONKEY=0: no fit, no gradient, no LM. The predict/surprise/learn is run_collapse's; the learning
is structure-accumulation (counts onto the Party) + re-attribution (mint a new Party = grow Γ),
the move_space_collapse_plug precedent exactly.
"""
from __future__ import annotations

import re
from typing import Optional

from domains.interlocutor_collapse_plug import collapse_residual

# --------------------------------------------------------------------------- #
#  Feature dimensions, split by TIMESCALE.
# --------------------------------------------------------------------------- #
FAST_DIMS = ("affect",)                              # mood/state — the perturbation timescale
STYLE_DIMS = ("register", "cadence", "style")        # slow structural identity markers
CONTEXT_DIMS = ("time_gap", "place", "channel")      # salient context that WEIGHTS identity
#   (Build-3 seam: `channel` is the extra order-N context dim beyond time_gap/place that
#   `domains.context_model` feeds in — a richer context shift now enters the slow residual and tips
#   re-attribution more decisively. It defaults to "same" and only gaps when context_model marks the
#   channel salient, so a caller that passes no channel context is unaffected — no regression.)
SLOW_DIMS = STYLE_DIMS + CONTEXT_DIMS                 # the identity timescale (style + context)

# A COHERENT break = a multi-dimensional style contradiction (>= _COHERENCE style dims differ from
# the party's accumulated plurality). A single style-dim shift is sub-coherent — natural
# within-person variation — and does NOT advance the identity signal.
_COHERENCE = 2

# SUSTAINED = a coherent style break that PERSISTS this many consecutive turns before it counts as
# the SLOW identity signal (re-attribution without a discontinuity cue). One or two turns of drift
# is still the same person; the identity timescale is slower than a couple of turns.
_SUSTAINED = 3

_AGITATED = frozenset("angry furious hate stupid damn annoyed frustrated idiot ridiculous "
                      "outrageous unacceptable enough".split())
_WARM = frozenset("thanks thank love wonderful appreciate glad happy delighted grateful "
                  "kind lovely please".split())


# --------------------------------------------------------------------------- #
#  OBSERVE — mechanical text -> feature dict (no decision over graph state).
# --------------------------------------------------------------------------- #

def _register_of(agent, toks: set) -> str:
    cas = len(toks & agent._CASUAL_CUES)
    frm = len(toks & agent._FORMAL_CUES)
    return "casual" if cas > frm else "formal" if frm > cas else "neutral"


def _affect_of(toks: set, text: str) -> str:
    if (toks & _AGITATED) or "!!" in text or text.count("!") >= 2:
        return "agitated"
    if toks & _WARM:
        return "warm"
    return "calm"


def _cadence_of(nwords: int) -> str:
    return "short" if nwords <= 4 else "medium" if nwords <= 12 else "long"


def _style_of(words: list, text: str) -> str:
    if not words:
        return "plain"
    long_words = any(len(w) >= 8 for w in words)
    punctuated = ("," in text) or (";" in text) or ("—" in text)
    return "ornate" if (long_words or punctuated) else "plain"


def _self_id(text: str) -> Optional[str]:
    m = (re.search(r"\b[Ii](?:\s+am|['’]m)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)", text)
         or re.search(r"\b[Cc]all me ([A-Z][a-zA-Z]+)", text))
    return m.group(1).strip() if m else None


def _content_concepts(words: list) -> list:
    seen, out = set(), []
    for w in words:
        lw = w.lower()
        if len(lw) >= 5 and lw not in seen and lw.isalpha():
            seen.add(lw)
            out.append(lw)
    return out[:8]


def observe_features(agent, text: str, context: Optional[dict] = None) -> dict:
    """Extract the interlocutor's features from one utterance + salient context. Mechanical
    text->graph translation, no conditional over graph state. Returns
    {register, cadence, style, affect, time_gap, place} + '_name'/'_concepts' side-channels."""
    context = context or {}
    text = str(text)
    words = re.findall(r"[A-Za-z']+", text)
    toks = {w.lower() for w in words}
    feats = {
        "register": _register_of(agent, toks),
        "cadence": _cadence_of(len(words)),
        "style": _style_of(words, text),
        "affect": _affect_of(toks, text),
        "time_gap": "long" if context.get("time_gap") else "none",
        "place": "changed" if context.get("place_changed") else "same",
        "channel": "changed" if context.get("channel_changed") else "same",
    }
    feats["_name"] = _self_id(text)
    feats["_concepts"] = _content_concepts(words)
    return feats


# --------------------------------------------------------------------------- #
#  PARTY graph — persistent, accumulating, and the GROUNDED audience feed.
# --------------------------------------------------------------------------- #

def _parties(agent):
    return list(agent.s.nodes("Interlocutor"))


def _ensure_party_anchor(agent, party) -> None:
    """Mechanical BOUNDARY EDGE (composer-capability wave): anchor `party` to
    the agent root via a dedicated `has_interlocutor` edge. A graph RULE can
    only MATCH real edges (never a bare NodesOfType) — the datum-feedback
    composer family needs to match "every party I model" the same way other
    rules match "every X I hold" (agent -edge-> X). Deliberately its OWN edge
    type, not a reuse of `_BOUNDARY_RELATIONS` (senses/models/acts_on,
    world_adapter.py) — those three feed load-bearing count invariants
    (`_bootstrap_theorem_candidates`'s senses_ge_models / models_ge_acts_on)
    that a party joining "models" would silently perturb. Idempotent: added
    once per party (checked via the existing edge set, never duplicated —
    CLAUDE.md's own documented engine gotcha: two same-type incoming edges on
    one node can break run_rules matching for that edge type)."""
    agent_node = getattr(agent, "agent", None)
    if agent_node is None:
        return
    try:
        if party in agent.inner.neighbours(agent_node, "has_interlocutor"):
            return
        agent.inner.add_edge_unchecked(agent_node, "has_interlocutor", party)
    except Exception:  # noqa: BLE001 — provenance is best-effort, never load-bearing
        pass


def _active_party(agent):
    for n in _parties(agent):
        if agent.s.node(n)["attrs"].get("active"):
            _ensure_party_anchor(agent, n)
            return n
    # fall back to the canonical 'user' node the register layer already tracks.
    node = agent._interlocutor("user")
    agent.inner.set_attr(node, "active", True)
    _ensure_party_anchor(agent, node)
    return node


def _model_of(agent, party, dims) -> dict:
    """Read the party's accumulated feature counts for `dims` into the plug's {dim:{val:cnt}}
    shape (a cache of graph-resident counts — allowed adapter read)."""
    fc = agent.s.node(party)["attrs"].get("feat_counts") or {}
    return {d: dict(fc.get(d, {})) for d in dims if fc.get(d)}


def _consolidate(agent, party, feats):
    """LEARN (homework): count this turn's features onto the party (grow its model), accumulate
    known_concepts + name, and mark it observed so it grounds the audience. Native graph write."""
    at = agent.s.node(party)["attrs"]
    fc = {k: dict(v) for k, v in (at.get("feat_counts") or {}).items()}
    for d in FAST_DIMS + SLOW_DIMS:
        v = feats[d]
        fc.setdefault(d, {})
        fc[d][v] = fc[d].get(v, 0) + 1
    agent.inner.set_attr(party, "feat_counts", fc)

    known = list(at.get("known_concepts") or [])
    for c in feats.get("_concepts", []):
        if c not in known:
            known.append(c)
    agent.inner.set_attr(party, "known_concepts", known)
    if feats.get("_name"):
        agent.inner.set_attr(party, "name", feats["_name"])
        agent.inner.set_attr(party, "self_identified", feats["_name"])
        # NORMALIZED KEY (Wave: interlocutor-as-modeled-participant, task 3,
        # creator-reliability refinement): a mechanical text form (lowercase,
        # spaces->underscores — "Matthew Parslow" -> "matthew_parslow") a
        # GRAPH RULE can compare against a held Concept's `name` by EQUALITY,
        # so recognising "this party is the creator" stays graph-native data
        # (seeds/interlocutor_trust.json), never a hardcoded Python name check.
        agent.inner.set_attr(party, "name_key",
                             feats["_name"].strip().lower().replace(" ", "_"))
    turns_now = int(at.get("turns", 0)) + 1
    agent.inner.set_attr(party, "turns", turns_now)
    # GROUND the party (feed a grounded audience) only after genuine accumulation — a few
    # observed turns or an explicit self-identification. Never flip an existing flag to False:
    # a pre-grounded party stays grounded, an unobserved one is not grounded by a single turn.
    if turns_now >= 2 or feats.get("_name"):
        agent.inner.set_attr(party, "observed", True)


def _reattribute(agent, feats):
    """RE-ATTRIBUTE to a DIFFERENT party (grow Γ with a new identity) — the identity timescale's
    learn step. Mints a fresh Interlocutor party, makes it the active one, and consolidates this
    turn into it (its model starts from the residual that split it off)."""
    for n in _parties(agent):
        agent.inner.set_attr(n, "active", False)
    idx = len(_parties(agent)) + 1
    party = agent.s.add_node("Interlocutor",
                             {"name": feats.get("_name") or f"speaker_{idx}", "active": True})
    _ensure_party_anchor(agent, party)
    _consolidate(agent, party, feats)
    return party


def _record_mood_shift(agent, party, affect):
    """PERTURBATION learn step: record the mood/state shift on the SAME party (grow its state)."""
    agent.inner.set_attr(party, "mood", affect)
    at = agent.s.node(party)["attrs"]
    agent.inner.set_attr(party, "mood_shifts", int(at.get("mood_shifts", 0)) + 1)


def _style_break_size(agent, party, feats) -> int:
    """The COHERENCE of this turn's break from the party's ESTABLISHED style: the number of style
    dimensions whose accumulated PLURALITY (the value the consolidated model most expects) the turn
    contradicts. This is the SLOW/identity read that drives the sustained-mismatch counter — unlike
    the zero-mass collapse gap it survives consolidation (absorbing one casual turn does not flip a
    formal plurality), so a single-dim wobble is absorbed and clears while a coherent multi-dim
    break keeps contradicting the plurality across turns. Reading the party's counts is an allowed
    adapter read — the same graph-resident feat_counts _model_of caches. An unestablished dim (no
    counts yet) carries no expectation and is never a break (first sight), mirroring the collapse
    plug's 'unlearned dim -> no surprise'."""
    fc = agent.s.node(party)["attrs"].get("feat_counts") or {}
    n = 0
    for d in STYLE_DIMS:
        vc = fc.get(d)
        if not vc:
            continue                              # unestablished dim -> no expectation, no break
        dominant = max(vc, key=lambda v: vc[v])   # the plurality the model most expects
        if feats[d] != dominant:
            n += 1
    return n


# --------------------------------------------------------------------------- #
#  THE TURN — observe, collapse at two timescales, decide from the residual.
# --------------------------------------------------------------------------- #

def observe_turn(agent, text: str, context: Optional[dict] = None) -> dict:
    """One turn of interlocutor modelling. OBSERVE features; PREDICT them from the active party's
    accumulated model at TWO timescales via the collapse loop; the RESIDUAL decides, with identity
    on the SLOW/STABLE timescale (a raised evidence bar):
      * DISCONTINUITY (context gap + style break) or SUSTAINED break (>= _SUSTAINED turns)
        -> RE-ATTRIBUTE (new party);
      * else fast residual -> PERTURBATION (mood shift, same party);
      * else -> STEADY (consolidate, same party).
    A single-turn style-only shift is a PERTURBATION, never an identity switch. Then LEARN:
    consolidate the turn into whichever party now holds it. Returns a report dict."""
    feats = observe_features(agent, text, context)
    party = _active_party(agent)

    fast_model = _model_of(agent, party, FAST_DIMS)
    slow_model = _model_of(agent, party, SLOW_DIMS)
    fast_turn = {d: feats[d] for d in FAST_DIMS}
    slow_turn = {d: feats[d] for d in SLOW_DIMS}

    # PREDICT + SURPRISE via the agent's OWN collapse loop (run_collapse), at each timescale.
    fast_residual = collapse_residual(fast_model, fast_turn)
    slow_residual = collapse_residual(slow_model, slow_turn)

    style_gaps = [g for g in slow_residual if g[0] in STYLE_DIMS]
    context_gaps = [g for g in slow_residual if g[0] in CONTEXT_DIMS]

    # RE-ATTRIBUTION (the SLOW identity decision) clears a raised evidence bar — a single turn's
    # style residual is NOT enough. It fires only on:
    #   (a) DISCONTINUITY — a context gap (time/place/channel) ALONGSIDE a style break, the genuine
    #       evidence a different party is speaking; OR
    #   (b) SUSTAINED — a coherent style break (>= _COHERENCE style dims vs the party's plurality)
    #       that PERSISTS for _SUSTAINED consecutive turns (the slow signal). The streak is graph
    #       state about the observation on the party ('style_mismatch_streak').
    # An established party thereby keeps INERTIA: neither path fires on one turn's style-only blip.
    discontinuity = bool(style_gaps) and bool(context_gaps)

    prior_streak = int(agent.s.node(party)["attrs"].get("style_mismatch_streak", 0))
    break_size = _style_break_size(agent, party, feats)
    streak = (prior_streak + 1) if break_size >= _COHERENCE else 0
    sustained = streak >= _SUSTAINED

    structured = discontinuity or sustained

    decision, mood_shift = "steady", None
    if structured:
        decision = "identity"
        party = _reattribute(agent, feats)          # fresh party -> streak resets to 0
    else:
        # Same party: carry the sustained-mismatch streak forward (a coherent break advances it, a
        # matched/wobble turn resets it), then LEARN — a fast residual is a mood/state shift.
        agent.inner.set_attr(party, "style_mismatch_streak", streak)
        if fast_residual:
            decision = "perturbation"
            mood_shift = feats["affect"]
            _record_mood_shift(agent, party, mood_shift)
        _consolidate(agent, party, feats)

    _record_shape_fit(agent, party)

    return {
        "party": party,
        "party_name": agent.s.node(party)["attrs"].get("name"),
        "decision": decision,
        "mood_shift": mood_shift,
        "fast_residual": fast_residual,
        "slow_residual": slow_residual,
        "style_gaps": style_gaps,
        "context_gaps": context_gaps,
        "discontinuity": discontinuity,
        "break_size": break_size,
        "style_mismatch_streak": streak,
        "sustained": sustained,
        "structured": structured,
        "features": feats,
    }


def wanted_by(agent, goal):
    """PROVENANCE (Wave: interlocutor-as-modeled-participant, task 2): mechanically
    record `goal -wanted_by-> the active Interlocutor party` — the request's
    provenance is a FACT at mint time, never a decision. Deliberately does NOT
    call `_active_party` (which get-or-creates a party) when no Interlocutor has
    ever been tracked on this substrate: a Goal minted by a non-conversational
    caller (a bare reading flow, a test harness that never ran `converse()`)
    stays byte-unchanged — no party is invented just to own it. Returns the
    party node or None."""
    try:
        if not _parties(agent):
            return None
        party = _active_party(agent)
        agent.inner.add_edge_unchecked(goal, "wanted_by", party)
        return party
    except Exception:  # noqa: BLE001 -- provenance is best-effort, never load-bearing
        return None


# --------------------------------------------------------------------------- #
#  SELF-REPORT RELIABILITY — a PER-PARTY revisable belief (course correction
#  2026-07-11, task 3: "my introspection is higher than most... most centroid
#  introspection is surface level at best" + "not just a track record - by
#  shape matching and priors. you can assume a lot about a person within a
#  confidence interval based on a lot of things."). THREE strata, checked in
#  order:
#    1. STRUCTURAL EVIDENCE — a directly-set belief (today: the creator-origin
#       rule, seeds/interlocutor_trust.json, keyed on the party's `name_key`
#       resolving to a held creator Concept) is independent of population
#       priors and wins outright.
#    2. SHAPE PRIOR — `decode_shape` matches the party's ACCUMULATED dominant
#       register/cadence/style/affect (the SAME feat_counts `observe_turn`
#       already grows) against the held InterlocutorShape codebook
#       (seeds/interlocutor_shapes.json); the winning shape supplies a prior
#       self_report_reliability + its own confidence-interval width. A
#       fit below _SHAPE_FIT_MIN honestly ABSTAINS to the codebook's own
#       'default_uncalibrated' entry (data, not a Python magic number).
#    3. INDIVIDUAL TRACK RECORD — `effective_reliability` blends the shape
#       prior with the party's own observed record (the fraction of their
#       self-reports NOT since contradicted), n-weighted so the prior's
#       influence DECAYS as individual evidence accrues (weight = n/(n+k),
#       k = the WINNING SHAPE'S OWN evidence_decay_k, never a Python literal).
#
# `decode_shape`/`effective_reliability`/`_dominant_features` are called from
# BOTH the live WorldAdapter (`.s`/`.inner` present) and the reflective
# reader (handed the bare substrate) -- the `getattr(agent, "s", agent)`
# duck-type every domains/*.py module already uses lets one implementation
# serve both, without a second reader-side copy.
#
# ARCHITECTURE NOTE: fit-scoring is mechanical ARITHMETIC over graph-READ
# counts (sum of per-dimension equality checks against the party's own
# accumulated plurality) -- the EXACT class this module's own
# `_style_break_size` already uses for the identity/style-break read (see its
# docstring), not a new "Python decides" pattern. This module's own header
# names the discipline explicitly: "DONKEY=0: no fit, no gradient, no LM...
# structure-accumulation... the move_space_collapse_plug precedent exactly."
# --------------------------------------------------------------------------- #
_SHAPE_DIMS = ("register", "cadence", "style", "affect")
_SHAPE_FIT_MIN = 2                      # of 4 dims must agree to claim a real shape
_DEFAULT_SHAPE_NAME = "default_uncalibrated"
_DEFAULT_SELF_REPORT_RELIABILITY = 0.5
_DEFAULT_RELIABILITY_INTERVAL = 0.35
_DEFAULT_TOM_CAPACITY = 0.5
_LOW_TOM_THRESHOLD = 0.4
_HEDGE_CUES = frozenset({"maybe", "probably", "perhaps", "possibly", "guess", "supposedly"})


def is_hedged(text: str) -> bool:
    """Cheap, mechanical hedge-cue scan (course correction 2026-07-11: 'most
    centroid introspection is surface level' — hedged self-report phrasing
    should discount confidence). NOT full pragmatics/irony — an honest scope
    boundary: the verbatim content is recorded regardless (Level 1, the
    Assertion), so later machinery can reinterpret. A simple lower-cased
    whitespace-token membership check against a small held cue set."""
    toks = {w.strip(",.;:!?\"'()").lower() for w in str(text).split()}
    return bool(toks & _HEDGE_CUES)


def _shape_sub(agent):
    return getattr(agent, "s", agent)


def _dominant_features(agent, party) -> dict:
    """Mechanical PLURALITY read (mirrors `_style_break_size`'s own dominant-
    value read exactly): the value each of register/cadence/style/affect's
    accumulated counts most support. An unestablished dim (no counts yet) is
    simply absent from the result — no forced/guessed value."""
    sub = _shape_sub(agent)
    fc = sub.node(party)["attrs"].get("feat_counts") or {}
    out = {}
    for d in _SHAPE_DIMS:
        vc = fc.get(d)
        if vc:
            out[d] = max(vc, key=lambda v: vc[v])
    return out


def decode_shape(agent, party) -> dict:
    """Match `party`'s accumulated dominant features against the held
    InterlocutorShape codebook; fit = count of dimensions agreeing with a
    shape's signature. Returns {shape, name, fit, prior, interval,
    expected_domains, precision_prior, decay_k} — the winning shape's PRIOR
    expectations, or the codebook's own 'default_uncalibrated' entry (widest
    interval) when no shape reaches `_SHAPE_FIT_MIN`, or the hardcoded
    floor-of-floors when the codebook seed isn't even loaded (an agent that
    never installed seeds/interlocutor_shapes.json — an honest absence, not
    an error)."""
    sub = _shape_sub(agent)
    dom = _dominant_features(agent, party)
    best, best_fit, default_shape = None, -1, None
    for n in sub.nodes("InterlocutorShape"):
        at = sub.node(n)["attrs"]
        if at.get("name") == _DEFAULT_SHAPE_NAME:
            default_shape = n
        fit = sum(1 for d in _SHAPE_DIMS if dom.get(d) and dom.get(d) == at.get("sig_" + d))
        if fit > best_fit:
            best, best_fit = n, fit
    if best is None:
        return {"shape": None, "name": None, "fit": 0,
                "prior": _DEFAULT_SELF_REPORT_RELIABILITY,
                "interval": _DEFAULT_RELIABILITY_INTERVAL,
                "expected_domains": [], "precision_prior": None, "decay_k": 5.0,
                "tom_capacity_prior": _DEFAULT_TOM_CAPACITY}
    if best_fit < _SHAPE_FIT_MIN and default_shape is not None:
        best, best_fit = default_shape, 0
    at = sub.node(best)["attrs"]
    return {"shape": best, "name": at.get("name"), "fit": best_fit,
            "prior": float(at.get("self_report_reliability_prior",
                                  _DEFAULT_SELF_REPORT_RELIABILITY)),
            "interval": float(at.get("reliability_interval",
                                     _DEFAULT_RELIABILITY_INTERVAL)),
            "expected_domains": list(at.get("expected_domains") or []),
            "precision_prior": at.get("precision_prior"),
            "decay_k": float(at.get("evidence_decay_k", 5.0)),
            "tom_capacity_prior": float(at.get("tom_capacity_prior", _DEFAULT_TOM_CAPACITY))}


def _record_shape_fit(agent, party) -> None:
    """Mechanical DATUM (composer-capability wave, R4): record whether this
    party's CURRENT accumulated features fit NO held InterlocutorShape
    (decode_shape's own `_SHAPE_FIT_MIN` floor) — a poor-fit residual on the
    party, never a decision (which shape to mint, if any, is the composer's
    call, not this reader's). Counts a running total (`poor_fit_count`) plus
    a CONSECUTIVE streak (`poor_fit_streak`, mirroring `_style_break_size`'s
    own streak shape) — a turn that DOES fit resets the streak, so the
    streak reflects CURRENT poor fit, not stale history. Called once per
    turn (`observe_turn`, after the turn's own consolidation, so the fit
    read reflects THIS turn's contribution to the party's plurality)."""
    decoded = decode_shape(agent, party)
    at = agent.s.node(party)["attrs"]
    poor = decoded.get("fit", 0) < _SHAPE_FIT_MIN
    if poor:
        streak = int(at.get("poor_fit_streak", 0) or 0) + 1
        agent.inner.set_attr(party, "poor_fit_streak", streak)
        agent.inner.set_attr(party, "poor_fit_count", int(at.get("poor_fit_count", 0) or 0) + 1)
    else:
        agent.inner.set_attr(party, "poor_fit_streak", 0)


def effective_tom_capacity(agent, party) -> float:
    """The party's THEORY-OF-MIND CAPACITY (course correction 2026-07-11, 4th
    refinement: 'realistically, some humans barely have theory of mind') --
    how much this party is expected to model the agent/others (track what was
    already said, adapt phrasing to it) vs. not (repeat identically, ignore
    answers). SCOPE (explicit instruction: 'do not build elaborate
    pragmatics'): this wave wires ONLY the shape-matched PRIOR
    (`decode_shape`'s `tom_capacity_prior`) — a party who behaviourally
    demonstrates high/low ToM (tracked via, e.g., repeat-vs-novel questions)
    does NOT yet revise this value; that blend is a NAMED RESIDUAL, the exact
    shape `effective_reliability`'s n-weighted blend already establishes for
    self-report reliability, deferred here rather than duplicated
    speculatively. Consumed by seeds/conversation_grice.json's
    reply_topic_repeat_known guard: a low-tom party's literal repeat is
    licensed as a genuine re-ask, not a signal the prior answer failed."""
    return decode_shape(agent, party).get("tom_capacity_prior", _DEFAULT_TOM_CAPACITY)


def effective_reliability(agent, party) -> dict:
    """The party's EFFECTIVE self-report reliability. STRUCTURAL evidence
    (creator-origin) is a direct, undiluted override — independent structural
    evidence outranks a population prior. Otherwise BLEND the matched shape's
    PRIOR with the party's own INDIVIDUAL track record (the fraction of their
    self-reports not since contradicted: `self_report_contradiction_count` /
    `self_report_count`, both mechanical per-turn counters — see
    world_adapter._shadow_read_turn / _record_interlocutor_correction),
    n-weighted so the prior's influence DECAYS as individual evidence accrues
    (weight = n/(n+decay_k), the WINNING SHAPE's own decay constant — never a
    Python literal). A re-attributed party (a fresh Interlocutor node, task
    1/identity machinery) starts with empty feat_counts/counters, so this
    recomputes from scratch every call rather than caching a frozen verdict —
    priors and the blend both naturally FOLLOW a re-attribution. Returns
    {value, source, interval, shape_name, fit, n}."""
    sub = _shape_sub(agent)
    at = sub.node(party)["attrs"]
    if at.get("self_report_reliability_source") == "creator_origin":
        return {"value": float(at.get("self_report_reliability", 0.9)),
                "source": "creator_origin", "interval": 0.05,
                "shape_name": None, "fit": None, "n": None}
    if at.get("self_report_reliability_source") == "learned":
        # R3 (composer-capability wave): a datum_feedback_rule the agent
        # AUTHORED (domains/reflective_faculty._compose_datum_feedback_rule)
        # has fed the party's own recorded contradiction datum back into a
        # HELD belief (`self_report_reliability`, stamped 'learned' by the
        # SAME rule effect that moved it) — read it directly, in preference
        # to the shape/track-record blend below, exactly like the
        # 'creator_origin' branch above. A party no authored rule has ever
        # touched carries no such marker and falls through unchanged.
        decoded = decode_shape(agent, party)
        return {"value": float(at.get("self_report_reliability",
                                      _DEFAULT_SELF_REPORT_RELIABILITY)),
                "source": "learned", "interval": decoded["interval"],
                "shape_name": decoded["name"], "fit": decoded["fit"],
                "n": int(at.get("self_report_count", 0) or 0)}
    decoded = decode_shape(agent, party)
    prior = decoded["prior"]
    n = int(at.get("self_report_count", 0) or 0)
    # `decay_k` is ALWAYS present on `decoded` (every decode_shape return path
    # sets it), so `.get(..., 5.0)` was a dead fallback that could never fire
    # -- read it directly (2026-08-14, SHAPE_AUDIT.md §6.1 fix).
    k = decoded["decay_k"]
    contradictions = int(at.get("self_report_contradiction_count", 0) or 0)
    # Krichevsky-Trofimov (add-1/2) smoothed individual success rate -- the
    # textbook parameter-free Bernoulli-rate estimator, not a swept/tuned
    # constant. UNCONDITIONAL (no more `if n > 0 else prior` special case):
    # at n=0, w below is EXACTLY 0 (n/(n+k) with n=0), so `individual`'s
    # value is multiplied out regardless and `value == prior` exactly,
    # byte-identical to the old special case.
    #
    # SHAPE_AUDIT.md §6.1 (F-16 regress, "1/n asserts stationarity -> declare
    # a floor 0.05 ... each rate needs a rate") named the old code here
    # verbatim: `individual = 1 - contradictions/n` (a raw MLE that CAN hit
    # exactly 0.0 or 1.0 at small n) plus an unrelated flat
    # `max(0.05, min(0.95, value))` clamp bolted on to hide it. The root
    # cause was the MLE, not the blended output -- KT-smoothing keeps
    # `individual` strictly inside the open interval (0, 1) for every finite
    # n, and since `prior` is itself always inside (0, 1) (every seeded
    # InterlocutorShape and every Python default here is), their convex
    # combination `value` is ALREADY strictly inside (0, 1) with no output
    # clamp needed -- the floor is derived from the estimator, not asserted
    # on the estimate. (Residual, stated honestly: this relies on `prior`
    # never being authored as exactly 0.0 or 1.0; no shape in
    # seeds/interlocutor_shapes.json does, and nothing here defends against
    # a future one that would -- an explicit assumption, not a silent one.)
    individual = (n - contradictions + 0.5) / (n + 1.0)
    w = (n / (n + k)) if (n + k) > 0 else 0.0
    value = prior * (1 - w) + individual * w
    return {"value": value, "source": ("shape_prior" if n == 0 else "shape_prior+track_record"),
            "interval": decoded["interval"], "shape_name": decoded["name"],
            "fit": decoded["fit"], "n": n}


def self_report_reliability(agent, party) -> tuple:
    """(value, source) — the compact form `character_tom`/`world_adapter`
    consume when tagging a Level-2 modeled belief's confidence. A thin
    wrapper over `effective_reliability` (kept as its own entry point since
    it's the one most callers need)."""
    eff = effective_reliability(agent, party)
    return (eff["value"], eff["source"])


def snapshot(agent, party=None) -> dict:
    """The GROUNDED audience feed: the party's accumulated {id, observed, known_concepts} — the
    exact shape audience_driven_production.audience_model grounds. This is what the Conceptualizer
    now designs against (grounded=True after observation; grounded=False for an unobserved party)."""
    party = party if party is not None else _active_party(agent)
    at = agent.s.node(party)["attrs"]
    return {"id": at.get("name", "user"),
            "observed": bool(at.get("observed", False)),
            "known_concepts": list(at.get("known_concepts") or [])}


__all__ = ["observe_features", "observe_turn", "snapshot", "wanted_by",
           "is_hedged", "decode_shape", "effective_reliability", "self_report_reliability",
           "effective_tom_capacity",
           "FAST_DIMS", "STYLE_DIMS", "CONTEXT_DIMS", "SLOW_DIMS"]
