"""dynamic_depth — make the agent's reasoning / acquisition DEPTH dynamic and
RELEVANCE-weighted, and abandon a dead dive early.

The two existing depth knobs were STATIC:

  * order_n_reasoning.reason ran to a fixed ``max_order`` (= content-slots+1),
    regardless of how material the question was, and ran the chain to the cap
    even when the last hops added nothing.
  * the reference deep-dive (local slab -> ConceptNet -> Wiktionary -> web) in
    epistemic_access / conversation escalated by COVERAGE, not by whether the
    question was worth the costlier tier.

This module is the CONTROLLER that allocates depth by RELEVANCE and cuts a dive
that stops paying off. It is the taught ``value_based_seeking`` model made
operational over the existing operators:

  relevance(query, context)            -> [0,1]   (materiality + asked-vs-aside)
       │  choice_stage: whether/how-far to dive (value vs cost)
       ▼
  depth_budget(relevance)              -> {max_order, ref_tiers, max_lookups}
       │  a budget PROPORTIONAL to relevance (high -> deep + costly tiers; low
       │  -> order-1, local only, few lookups). Heuristic mapping (printed).
       ▼
  perseverance cutoff (jROL)           -> stop EARLY when the last K steps added
       │  nothing (RATE of progress ~ 0), even if the budget allowed more —
       │  perseverance_stage: keep while 'on a roll', abandon 'going nowhere'.
       ▼
  relevance-gated reference escalation -> a costlier tier is reached ONLY when
            relevance justifies its cost AND cheaper tiers missed; a low-relevance
            gap never reaches the web (choice_stage value-vs-cost on each tier).

The depth decision is recorded as graph data (a ``DepthDecision`` node:
relevance, budget, order reached, tiers used, stop reason) — inspectable like a
ReasoningChain / EpistemicAccessStance trace.

ARCHITECTURE (CLAUDE.md). A WORLD-SIDE controller: it READS graph state (the
discourse store, the KnownFact graph) + the taught concepts and SEQUENCES the
existing operators (order_n_reasoning, the reference tiers). It holds no agent
knowledge of its own; every weight below is a HEURISTIC dial (calibratable, like
the social_capital weights in epistemic_access), printed by the test, NOT ground
truth. No ML, no Rust, no rebuild.

HONEST framing: relevance + the budget mapping + the jROL threshold are
CALIBRATABLE WEIGHTS. The win is the MECHANISM — depth allocated by relevance +
early-stop on no-progress — not the specific numbers. A low-relevance query
GENUINELY should not resolve a hard answer the deep path would (its budget is
small on purpose); that is correct behaviour, not a failure.

See domains/epistemic_access.py (value_based_seeking / choice / perseverance /
materiality + the reference route), domains/order_n_reasoning.py (the static
max_order this makes dynamic), domains/conjecture.py (a resolved dive beats a
conjecture), seeds/epistemic_access.json (the taught concept names).
"""
from __future__ import annotations

from typing import Any, Optional

from domains import epistemic_access as epa
from domains import order_n_reasoning as onr

try:
    from domains import interrogative_reference as _ireg
    _WH = set(_ireg.ALL_PLACEHOLDERS)
except Exception:  # pragma: no cover
    _WH = {"?WHO", "?WHAT", "?WHERE", "?WHEN", "?WHY", "?HOW"}


# ===========================================================================
# HEURISTIC WEIGHTS — the calibratable depth-budget dials. NOT learned, NOT
# ground truth (the same status as epistemic_access's social-cost weights). The
# test prints these so the mapping is explicit, not hidden in behaviour.
# ===========================================================================

# relevance bands (on the [0,1] relevance score). A material, asked question is
# HIGH; a material-but-incidental gap is MID; an immaterial aside is LOW.
RELEVANCE_HIGH: float = 0.7
RELEVANCE_MID: float = 0.3

# The depth_budget MAPPING: relevance band -> {max_order, ref tiers, lookups}.
# max_order: how many hops the order-N chain may take.
# ref_tiers: which reference tiers the deep-dive may escalate through, cheapest
#   first. A LOW gap never reaches the costly (web/conceptnet) tiers.
# max_lookups: how many reference lookups the dive may spend.
#
# Reference-tier cost order (cheapest -> costliest), the route the deep dive
# escalates along: a local grounded slab, then crowd-sourced commonsense
# (ConceptNet), then a dictionary (Wiktionary/WordNet), then the open web.
REF_TIERS_ORDERED = ("local", "conceptnet", "wiktionary", "web")
# Per-tier cost-to-consult (heuristic; mirrors epistemic_access.ROUTE_COST in
# spirit). The relevance gate compares relevance against the NEXT tier's cost.
REF_TIER_COST = {
    "local": 0.05,        # a grounded local slab — nearly free
    "conceptnet": 0.30,   # crowd-sourced commonsense — cheap but noisy
    "wiktionary": 0.50,   # a dictionary lookup — costlier external store
    "web": 0.90,          # the open web — the most expensive tier
}

# The budget per band. max_order scales with relevance; ref_tiers is the SLICE of
# REF_TIERS_ORDERED affordable at this relevance; max_lookups bounds the spend.
_BUDGET_BY_BAND = {
    "HIGH": {"max_order": 4, "max_tier": "web",        "max_lookups": 4},
    "MID":  {"max_order": 2, "max_tier": "conceptnet", "max_lookups": 2},
    "LOW":  {"max_order": 1, "max_tier": "local",      "max_lookups": 1},
}

# perseverance cutoff (jROL): abandon the dive when the last K steps each added
# NOTHING (zero progress-rate), even if the budget allowed more depth. K = the
# patience window — how many no-progress steps to tolerate before 'going
# nowhere'. K=1 means: one wholly-unproductive step ends the dive.
JROL_PATIENCE: int = 1


def weights_snapshot() -> dict[str, Any]:
    """The full set of heuristic weights, for the test to PRINT (flagged
    calibratable). Returns the relevance bands, the budget mapping, the tier
    costs, and the jROL patience — every dial in one inspectable dict."""
    return {
        "relevance_bands": {"HIGH>=": RELEVANCE_HIGH, "MID>=": RELEVANCE_MID},
        "budget_by_band": {k: dict(v) for k, v in _BUDGET_BY_BAND.items()},
        "ref_tiers_ordered": list(REF_TIERS_ORDERED),
        "ref_tier_cost": dict(REF_TIER_COST),
        "jrol_patience": JROL_PATIENCE,
        "_note": "HEURISTIC weights — calibratable, not ground truth.",
    }


# ===========================================================================
# 1. relevance(query, context) -> [0,1]
# ===========================================================================

def relevance(query: dict[str, Any], discourse_store=None,
              interlocutor: Optional[str] = None) -> dict[str, Any]:
    """The materiality / VALUE of this query to the current goal/exchange, in
    [0,1]. REUSES epistemic_access.materiality (the taught materiality model:
    a gap about an entity in play is material; an out-of-frame curiosity is not)
    and ADDS the asked-vs-aside distinction:

      * the user's ACTUAL question (``_asked``) -> HIGH relevance — the agent
        owes a real answer, so a deep dive is warranted;
      * a material incidental gap (an entity in play but not the asked question)
        -> MID relevance — worth a shallow dive;
      * an immaterial aside / curiosity (``_immaterial`` or out-of-frame) -> LOW
        relevance — a quick conjecture or drop, no expensive dive.

    Returns {score, band, why}. The score is a HEURISTIC weight (calibratable).
    The world adapter marks ``_asked`` True on the turn's actual question and
    ``_immaterial`` True on a flagged aside; absent either, materiality decides."""
    mat = epa.materiality(query, discourse_store)
    asked = bool(query.get("_asked"))
    immaterial = bool(query.get("_immaterial"))

    # An explicit aside overrides — immaterial is LOW no matter what.
    if immaterial:
        return {"score": 0.10, "band": "LOW",
                "why": f"immaterial aside ({mat['why']}) -> LOW relevance"}

    # The user's actual question is HIGH — the agent owes a real answer.
    if asked and mat["material"]:
        return {"score": 0.90, "band": "HIGH",
                "why": (f"the user's asked question AND material "
                        f"({mat['why']}) -> HIGH relevance (deep dive warranted)")}
    if asked:
        # asked but not about an in-play entity (e.g. a word-meaning question):
        # still the user's actual question -> HIGH, the agent must try.
        return {"score": 0.80, "band": "HIGH",
                "why": (f"the user's asked question ({mat['why']}) -> HIGH "
                        f"relevance (the agent owes an answer)")}

    # Not the asked question. Material incidental -> MID; immaterial -> LOW.
    if mat["material"]:
        return {"score": 0.50, "band": "MID",
                "why": (f"a material incidental gap ({mat['why']}) -> MID "
                        f"relevance (a shallow dive)")}
    return {"score": 0.10, "band": "LOW",
            "why": (f"an immaterial gap ({mat['why']}) -> LOW relevance "
                    f"(conjecture or drop, no dive)")}


def relevance_band(score: float) -> str:
    """Map a relevance score to its band (HIGH/MID/LOW)."""
    if score >= RELEVANCE_HIGH:
        return "HIGH"
    if score >= RELEVANCE_MID:
        return "MID"
    return "LOW"


# ===========================================================================
# 2. depth_budget(relevance) -> {max_order, ref_tiers, max_lookups}
# ===========================================================================

def depth_budget(relevance_result: dict[str, Any]) -> dict[str, Any]:
    """A depth budget PROPORTIONAL to relevance. High relevance -> deep
    (max_order high, costly reference tiers incl. web/ConceptNet allowed, more
    lookups); low relevance -> shallow (max_order 1, local stores only, few
    lookups). The mapping is the heuristic _BUDGET_BY_BAND table (printed).

    Returns {band, max_order, ref_tiers (the AFFORDABLE slice, cheapest first),
    max_tier, max_lookups, why}. ``ref_tiers`` is REF_TIERS_ORDERED truncated at
    the band's max affordable tier — the relevance gate on escalation."""
    band = relevance_result.get("band") or relevance_band(
        float(relevance_result.get("score", 0.0)))
    spec = _BUDGET_BY_BAND.get(band, _BUDGET_BY_BAND["LOW"])
    max_tier = spec["max_tier"]
    # The affordable tier slice: cheapest..max_tier (inclusive).
    cut = REF_TIERS_ORDERED.index(max_tier) + 1
    ref_tiers = list(REF_TIERS_ORDERED[:cut])
    return {
        "band": band,
        "max_order": int(spec["max_order"]),
        "ref_tiers": ref_tiers,
        "max_tier": max_tier,
        "max_lookups": int(spec["max_lookups"]),
        "why": (f"relevance {band} -> max_order={spec['max_order']}, "
                f"reference tiers {ref_tiers} (up to '{max_tier}'), "
                f"max_lookups={spec['max_lookups']}"),
    }


# ===========================================================================
# 3. perseverance cutoff (jROL) — the dynamic order-N chain with early-stop.
# ===========================================================================

def reason_dynamic(s, anchor_entity: str, queried_relation: str,
                   queried_slot: str, anchor_slot: str = "agent",
                   budget: Optional[dict[str, Any]] = None,
                   record: bool = True) -> dict[str, Any]:
    """Order-N inference with a DYNAMIC max_order (from the budget) and a jROL
    PERSEVERANCE cutoff. Delegates to the (now budget-aware) order_n_reasoning.
    reason: the taught perseverance_stage made operational over the iterate-to-N
    operator — continue while the chain set GROWS (a hop added a new usable
    composition = progress) AND the budget remains; STOP early when the last
    JROL_PATIENCE order-steps added nothing (RATE of progress ~ 0, 'going
    nowhere') — even if max_order is not exhausted.

    Returns the resolution dict augmented with:
        {order_reached, stop_reason, max_order, progress_trace}
    where stop_reason ∈ {resolved, no_progress, budget, no_chain}. On no
    resolution ``answer`` is None (honest — never fabricated)."""
    max_order = int((budget or {}).get("max_order", 4))
    progress: list[dict[str, Any]] = []
    res = onr.reason(s, anchor_entity=anchor_entity,
                     queried_relation=queried_relation,
                     queried_slot=queried_slot, anchor_slot=anchor_slot,
                     max_order=max_order, record=record,
                     jrol_patience=JROL_PATIENCE, progress_trace=progress)
    # Derive the order reached + stop reason from the progress trace (the jROL
    # derivative the operator filled in).
    order_reached = progress[-1]["order"] if progress else 0
    if res is not None:
        stop_reason = "resolved"
        out = dict(res)
    else:
        # the last trace step carries the abandon reason; else the budget cap.
        last_stop = progress[-1].get("stop") if progress else None
        if last_stop in ("no_progress", "no_chain"):
            stop_reason = last_stop
        elif order_reached >= max_order:
            stop_reason = "budget"
        else:
            stop_reason = last_stop or "no_chain"
        out = {"answer": None, "queried_slot": queried_slot,
               "queried_relation": queried_relation}
    out["order_reached"] = order_reached
    out["stop_reason"] = stop_reason
    out["max_order"] = max_order
    out["progress_trace"] = progress
    return out


# ===========================================================================
# 4. relevance-gated reference escalation.
# ===========================================================================

def affordable_tiers(budget: dict[str, Any]) -> list[str]:
    """The reference tiers this budget can escalate through, cheapest first —
    just the budget's ``ref_tiers`` slice. A LOW-relevance budget returns only
    ['local']; a HIGH budget returns the full ladder up to 'web'."""
    return list(budget.get("ref_tiers", ["local"]))


def reference_escalate(budget: dict[str, Any], tier_lookups: dict[str, Any],
                       record_steps: Optional[list] = None) -> dict[str, Any]:
    """Relevance-GATED reference escalation: walk the tiers cheapest-first,
    consulting each ONLY while (a) it is within the budget's affordable slice
    (the relevance gate — a low-relevance gap never reaches the costly tiers),
    (b) the lookup budget remains, and (c) cheaper tiers have NOT resolved.
    Stop at the first tier that resolves (choice_stage value-vs-cost per tier).

    ``tier_lookups`` maps a tier name -> a zero-arg callable that consults that
    store and returns a non-empty value (resolved) or a falsy value (miss). Only
    the world adapter supplies these (external I/O); this function holds the
    GATING logic, no store knowledge.

    Returns {resolved, answer?, tier?, tiers_tried, lookups_used, stop_reason}.
    stop_reason ∈ {resolved, exhausted_tiers, lookup_budget, relevance_gated}."""
    affordable = affordable_tiers(budget)
    max_lookups = int(budget.get("max_lookups", 1))
    tiers_tried: list[str] = []
    lookups_used = 0

    for tier in REF_TIERS_ORDERED:
        if tier not in affordable:
            # The relevance gate: this (costlier) tier is NOT justified by the
            # query's relevance. Never reached -> stop the escalation here.
            step = {"tier": tier, "consulted": False,
                    "why": (f"'{tier}' (cost {REF_TIER_COST.get(tier)}) is above "
                            f"the relevance budget (max '{budget.get('max_tier')}') "
                            f"-> NOT escalated (relevance-gated)")}
            if record_steps is not None:
                record_steps.append(step)
            return {"resolved": False, "tiers_tried": tiers_tried,
                    "lookups_used": lookups_used,
                    "stop_reason": "relevance_gated",
                    "gated_at": tier}
        if lookups_used >= max_lookups:
            if record_steps is not None:
                record_steps.append({"tier": tier, "consulted": False,
                                     "why": "lookup budget exhausted"})
            return {"resolved": False, "tiers_tried": tiers_tried,
                    "lookups_used": lookups_used,
                    "stop_reason": "lookup_budget"}
        fn = tier_lookups.get(tier)
        if fn is None:
            if record_steps is not None:
                record_steps.append({"tier": tier, "consulted": False,
                                     "why": "no lookup supplied for this tier"})
            tiers_tried.append(tier)
            continue
        tiers_tried.append(tier)
        lookups_used += 1
        try:
            val = fn()
        except Exception:
            val = None
        step = {"tier": tier, "consulted": True,
                "cost": REF_TIER_COST.get(tier),
                "result": ("RESOLVED" if val else "miss")}
        if record_steps is not None:
            record_steps.append(step)
        if val:
            return {"resolved": True, "answer": val, "tier": tier,
                    "tiers_tried": tiers_tried, "lookups_used": lookups_used,
                    "stop_reason": "resolved"}
    return {"resolved": False, "tiers_tried": tiers_tried,
            "lookups_used": lookups_used, "stop_reason": "exhausted_tiers"}


# ===========================================================================
# 5. The depth decision — sequence (1)->(2)->(3)/(4) + record graph data.
# ===========================================================================

def decide_depth(s, query: dict[str, Any], discourse_store=None,
                 interlocutor: Optional[str] = None,
                 record: bool = True) -> dict[str, Any]:
    """The top-level depth controller for a query: compute its relevance, derive
    a proportional depth budget, and return the controller decision (the budget +
    the relevance band) the caller uses to drive reason_dynamic / the gated
    reference escalation. Records a DepthDecision trace node (graph data).

    Returns {relevance, budget}. The CALLER (conversation_world /
    epistemic_access) then runs reason_dynamic(budget=...) and
    reference_escalate(budget=...) and reports the order reached / tiers used /
    stop reason back into the same DepthDecision via record_outcome."""
    rel = relevance(query, discourse_store, interlocutor)
    budget = depth_budget(rel)
    decision = {"relevance": rel, "budget": budget}
    if record:
        decision["node"] = _record_decision(s, query, rel, budget)
    return decision


def _record_decision(s, query: dict[str, Any], rel: dict[str, Any],
                     budget: dict[str, Any]) -> Any:
    """Mint a DepthDecision node (graph-resident, inspectable like a
    ReasoningChain / EpistemicAccessStance): the relevance + the budget. The
    outcome (order reached, tiers used, why stopped) is written back later by
    record_outcome. Best-effort, the same idiom the sibling traces use."""
    try:
        return s.add_node("DepthDecision", {
            "relevance_score": float(rel.get("score", 0.0)),
            "relevance_band": rel.get("band", ""),
            "relevance_why": rel.get("why", ""),
            "max_order": int(budget.get("max_order", 0)),
            "ref_tiers": ",".join(budget.get("ref_tiers", [])),
            "max_tier": budget.get("max_tier", ""),
            "max_lookups": int(budget.get("max_lookups", 0)),
            "queried_slot": query.get("_queried_slot", "") or "",
            "event": (query.get("event")
                      if isinstance(query.get("event"), str) else ""),
            # the outcome fields, filled by record_outcome.
            "order_reached": 0,
            "stop_reason": "",
            "tiers_used": "",
            "resolved": False,
            "origin": "dynamic_depth",
        })
    except Exception:
        return None


def record_outcome(s, decision: dict[str, Any], *,
                   order_reached: Optional[int] = None,
                   stop_reason: Optional[str] = None,
                   tiers_used: Optional[list] = None,
                   resolved: Optional[bool] = None) -> None:
    """Write the dive OUTCOME back onto the DepthDecision node (order reached,
    why it stopped, which tiers were consulted, whether it resolved) — so the
    trace records both the allocated budget AND what the dive actually spent.
    Graph mutation only, best-effort."""
    nid = decision.get("node")
    if nid is None:
        return
    updates: dict[str, Any] = {}
    if order_reached is not None:
        updates["order_reached"] = int(order_reached)
    if stop_reason is not None:
        updates["stop_reason"] = str(stop_reason)
    if tiers_used is not None:
        updates["tiers_used"] = ",".join(tiers_used)
    if resolved is not None:
        updates["resolved"] = bool(resolved)
    for k, v in updates.items():
        try:
            s.set_attr(nid, k, v)
        except Exception:
            pass


__all__ = [
    "RELEVANCE_HIGH", "RELEVANCE_MID", "REF_TIERS_ORDERED", "REF_TIER_COST",
    "JROL_PATIENCE", "weights_snapshot",
    "relevance", "relevance_band", "depth_budget",
    "reason_dynamic", "affordable_tiers", "reference_escalate",
    "decide_depth", "record_outcome",
]
