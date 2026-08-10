"""epistemic_access — the "I don't know for sure, but I know how to GET it"
stance + the ask-now / bank-for-later / drop decision, built to the taught
``epistemic_access`` model (seeds/epistemic_access.json).

This EXTENDS the confidence continuum of domains/conjecture.py. That module
ends at a binary: a conjecturable SHAPE (LOW band) or a categorical
INADMISSIBLE "I don't know" when there is no shape. But many gaps the agent
cannot answer NOW are nonetheless GETTABLE — there is a person who'd know, an
external reference that covers the kind, or it's a lookupable class of question.
This module inserts a band BETWEEN conjecture and inadmissible:

    grounded fact        conf ~1.0      HIGH               -> "X."
    order-N chain        product/hops   HIGH/MID           -> "X." / "Probably X."
    conjecture (shape)   epsilon ~0.1   LOW                -> "I think it's like X."
    --- NEW: a route exists ---------- RESOLVABLE_VIA_ROUTE -> ask / bank / drop
    no route, no shape   —              INADMISSIBLE        -> "I don't know."

The KEY point of the taught model: whether to SURFACE the question to the
current audience (ask now) vs BANK it for off-path resolution vs DROP it is a
SOCIAL cost-benefit over the CONVERSATION, NOT just "does a source exist". A
material, route-having question gets BANKED when social capital is low — the
agent is a good conversational citizen, not a constant-questioner.

ARCHITECTURE (CLAUDE.md). Like domains/reference_resolution.py and
domains/conjecture.py, this is a WORLD-SIDE helper that implements a NAMED
taught procedure as a graph walk. The state is GRAPH DATA:

  * ``SocialCapital`` node — one per conversation; ``balance`` (depletes on a
    surfaced ask, regenerates slowly per turn), ``recent_asks`` (for the
    cumulative_question_burden), ``turn``.
  * ``PendingGap`` node — a banked gap (query + route + cost), ``resolved`` +
    ``answer`` once resolved off-path.
  * ``EpistemicAccessStance`` node — the per-query verdict trace (the band +
    the decision + the rationale), inspectable like a Conjecture node.

The routing reads the discourse referent store (domains/reference_resolution —
the interlocutor-source map) and the agent's reference coverage. No ML, no Rust.

HONEST framing (which half is which):
  * VERIFIED-ACCESS half (grounded in the taught model's settled research):
    feeling_of_findability (external locatability), transactive_memory (route
    to the entity who'd know), knowing_where_vs_what, value-based seek control.
    The route-finder is built on these.
  * SCAFFOLDING social-cost half (standard pragmatics, flagged in the seed as
    not-verified-in-this-pass): social_capital / conversational_flow_cost /
    face_imposition / cumulative_question_burden / audience_appropriateness /
    materiality / solved_class. These are HEURISTIC WEIGHTS (numbers below),
    calibratable, NOT ground truth. They are reported, not hidden.

See domains/conjecture.py (the continuum this extends) /
domains/reference_resolution.py (the interlocutor-source map) /
seeds/epistemic_access.json (the taught concept names this mirrors).
"""
from __future__ import annotations

from typing import Any, Optional

try:
    from domains import interrogative_reference as _ireg
    _WH = set(_ireg.ALL_PLACEHOLDERS)
except Exception:  # pragma: no cover
    _WH = {"?WHO", "?WHAT", "?WHERE", "?WHEN", "?WHY", "?HOW"}


# ===========================================================================
# HEURISTIC WEIGHTS — the SCAFFOLDING social-cost half. These are NOT learned
# and NOT ground truth; they are calibratable conversational-economics dials.
# Reported by the test so the numbers are explicit, not hidden in behaviour.
# ===========================================================================

# social_capital budget.
SC_INITIAL: float = 1.0          # starting balance (full budget)
SC_MAX: float = 1.0              # cap on regeneration
SC_ASK_COST: float = 0.20       # spent per surfaced ask (face_imposition base)
SC_REGEN_PER_TURN: float = 0.15  # slow regeneration each turn not spent
# cumulative_question_burden: each recent ask raises the NEXT ask's cost. The
# burden term added to the ask cost = BURDEN_PER_RECENT * recent_asks, decaying
# one step of "recent" per turn.
BURDEN_PER_RECENT: float = 0.20
# recent_asks is a FLOAT pressure: an ask adds 1.0; each turn it decays by this
# rate. Decay < 1.0 so rapid asking ACCUMULATES burden (the cumulative cost
# rises faster than it cools) while a run of quiet turns lets it fall to ~0.
RECENT_DECAY_PER_TURN: float = 0.5

# acquisition_route cost-to-obtain (the value side weighs against this + social).
ROUTE_COST = {
    "interlocutor": 0.20,   # asking a present person — cheap to obtain, social
    "reference": 0.10,      # off-path lookup — cheap, NO social cost
    "solved_class": 0.50,   # general lookupable — vaguer, higher obtain cost
}

# materiality: the VALUE of the answer to the current exchange. A question ABOUT
# an entity in the current frame is material; an out-of-frame curiosity is not.
MATERIAL_VALUE: float = 0.80     # value of a material gap
IMMATERIAL_VALUE: float = 0.05  # value of an immaterial gap -> DROP

# conversational_flow_cost: a question that fits the current topic is cheap; an
# off-topic interruption costs more. Coarse: on-topic if the route's source is
# the entity the question is about / the current interlocutor.
FLOW_COST_ON_TOPIC: float = 0.05
FLOW_COST_OFF_TOPIC: float = 0.30


# ===========================================================================
# acquisition_route — a concrete way to obtain a missing answer.
# ===========================================================================

class AcquisitionRoute:
    """A route to obtain a missing answer (the taught ``acquisition_route``):
    one of INTERLOCUTOR / REFERENCE / SOLVED_CLASS, with the source label, the
    location (knowing_where_vs_what), and a cost-to-obtain. Carries enough to
    surface a hedged question OR to resolve it off-path later."""

    def __init__(self, route_type: str, source: str, *,
                 cost: float, basis: str,
                 reference_key: Optional[str] = None):
        self.route_type = route_type       # interlocutor | reference | solved_class
        self.source = source               # the entity / store name (the LABEL)
        self.cost = float(cost)            # cost-to-obtain
        self.basis = basis                 # why this route (the FOF/transactive read)
        self.reference_key = reference_key  # for a REFERENCE route: what to look up

    def as_dict(self) -> dict[str, Any]:
        return {"route_type": self.route_type, "source": self.source,
                "cost": self.cost, "basis": self.basis,
                "reference_key": self.reference_key}

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (f"AcquisitionRoute({self.route_type}, source={self.source!r}, "
                f"cost={self.cost})")


# ===========================================================================
# THE ROUTE-FINDER — the FOF / transactive step (the VERIFIED-ACCESS half).
# ===========================================================================

def _query_entities(query: dict[str, Any]) -> list[str]:
    """The bound (non-wh) entities a query is ABOUT — the transactive anchors.
    Read straight off the query frame's content slots (the entity the question
    grounds out from is the natural transactive source for facts about itself)."""
    ents: list[str] = []
    for slot, v in query.items():
        if slot.startswith("_") or slot in ("event", "tense", "speech_act",
                                             "polar"):
            continue
        if isinstance(v, str) and v and v not in _WH:
            ents.append(v)
    return ents


def _discourse_concepts(discourse_store) -> set[str]:
    """The concepts currently in the discourse referent store (the entities in
    play) — read off the store's DiscourseReferent nodes. The interlocutor-
    source map: a discourse entity is a plausible source for facts about itself
    (transactive_memory)."""
    if discourse_store is None:
        return set()
    try:
        return set(discourse_store._ref_nodes.keys())
    except Exception:
        return set()


# ===========================================================================
# REFERENCE STORES BY KIND — the agent's epistemic_access source-by-kind
# registry (the table it asked for in cmsg102). Each entry maps a need KIND to a
# REFERENCE store: its label, the FETCH world-adapter module (ingest external
# reference data -> the cited fact), and the cost-to-obtain (the
# acquisition_route fields the model already has). Graph-adjacent registry data;
# the FETCH is a world-adapter (Python is the world-adapter — CLAUDE.md), the
# route-finder (held epistemic_access) does the routing.
#
# Registered (#3 supply-line, cmsg102):
#   · OEIS  covers {integer-sequence, sequence} — domains/oeis_reference (REAL,
#     local: the downloaded christopher/oeis dump via domains/oeis_local).
#   · LMFDB covers {elliptic-curve, torsion-subgroup, modular-form,
#     number-field, arithmetic-object} — domains/lmfdb_local (REAL fetch: the
#     live LMFDB API, cached to data/lmfdb; honest live-fetch boundary if gated).
REFERENCE_STORES_BY_KIND: dict[str, dict[str, Any]] = {
    "integer-sequence": {
        "store": "oeis (On-Line Encyclopedia of Integer Sequences)",
        "fetch_adapter": "domains.oeis_reference",
        "cost": ROUTE_COST["reference"], "tier": "local"},
    "sequence": {
        "store": "oeis (On-Line Encyclopedia of Integer Sequences)",
        "fetch_adapter": "domains.oeis_reference",
        "cost": ROUTE_COST["reference"], "tier": "local"},
    "elliptic-curve": {
        "store": "lmfdb (L-functions and Modular Forms Database)",
        "fetch_adapter": "domains.lmfdb_local",
        "cost": ROUTE_COST["reference"], "tier": "web"},
    "torsion-subgroup": {
        "store": "lmfdb (L-functions and Modular Forms Database)",
        "fetch_adapter": "domains.lmfdb_local",
        "cost": ROUTE_COST["reference"], "tier": "web"},
    "modular-form": {
        "store": "lmfdb (L-functions and Modular Forms Database)",
        "fetch_adapter": "domains.lmfdb_local",
        "cost": ROUTE_COST["reference"], "tier": "web"},
    "number-field": {
        "store": "lmfdb (L-functions and Modular Forms Database)",
        "fetch_adapter": "domains.lmfdb_local",
        "cost": ROUTE_COST["reference"], "tier": "web"},
    "arithmetic-object": {
        "store": "lmfdb (L-functions and Modular Forms Database)",
        "fetch_adapter": "domains.lmfdb_local",
        "cost": ROUTE_COST["reference"], "tier": "web"},
}


def _math_reference_covers(query: dict[str, Any]
                           ) -> Optional[tuple[str, str]]:
    """feeling_of_findability over the MATH reference stores (the cmsg102
    registry): classify the gap's KIND and, if a registered store covers it,
    return (store_label, lookup_key). knowing_where_vs_what — the route + the
    key, not the answer (the fetch happens at resolve time via the adapter).

      · an integer-SEQUENCE gap (an OEIS id 'A012345' in a slot, or an explicit
        kind/topic naming a sequence) -> OEIS (key = the id / the sequence name).
      · an ELLIPTIC-CURVE / TORSION-SUBGROUP / arithmetic-object gap over a
        number field -> LMFDB (key = the field surface / label, e.g.
        'Q(sqrt(-3))'). The agent's elliptic-curve deep-read wall (cmsg100)
        routes here."""
    import re as _re
    topic = query.get("topic")
    event = query.get("event")
    # gather the bound, non-wh string slot values to scan for keys/cues.
    slot_vals = [v for v in _query_entities(query)]
    blob = " ".join(str(query.get(k, "")) for k in
                    ("topic", "patient", "agent", "_question_text", "event")
                    if isinstance(query.get(k), str)).lower()

    # OEIS — an explicit OEIS id ('A012345') is the strongest signal; else an
    # integer-sequence cue ('sequence') with a name to look up.
    for v in slot_vals + ([topic] if isinstance(topic, str) else []):
        if isinstance(v, str) and _re.match(r"^A\d{6}$", v.strip(), _re.I):
            return (REFERENCE_STORES_BY_KIND["integer-sequence"]["store"],
                    v.strip().upper())
    if "sequence" in blob or (isinstance(topic, str)
                              and "sequence" in topic.lower()):
        # the lookup key = the bound name/topic the sequence question is about.
        for v in slot_vals:
            if isinstance(v, str) and v and v not in _WH:
                return (REFERENCE_STORES_BY_KIND["sequence"]["store"], v)
        qt = query.get("_question_text")
        if isinstance(qt, str) and qt.strip():
            return (REFERENCE_STORES_BY_KIND["sequence"]["store"], qt.strip())

    # LMFDB — an elliptic-curve / torsion / arithmetic-object gap over a number
    # field. Cue on the topic/question naming the arithmetic kind + a field
    # surface to look up. The key is the field surface (LMFDB routes by field).
    ec_cue = any(k in blob for k in
                 ("elliptic", "torsion", "modular form", "number field",
                  "arithmetic"))
    if ec_cue or (isinstance(topic, str)
                  and any(k in topic.lower() for k in
                          ("elliptic", "torsion", "modular", "arithmetic"))):
        try:
            from domains import lmfdb_local as _lm
        except Exception:
            _lm = None
        # find a field surface/label to look up (the route key).
        key = None
        cand = " ".join(str(query.get(k, "")) for k in
                        ("_question_text", "patient", "topic", "agent")
                        if isinstance(query.get(k), str))
        if _lm is not None:
            m = _re.search(r"Q\(sqrt\(-?\d+\)\)|Q\(zeta_?\d+\)|\b\d+\.\d+\.\d+\.\d+\b",
                           cand, _re.I)
            if m:
                key = m.group(0)
            elif "sqrt(-3)" in cand.lower() or "zeta_3" in cand.lower() \
                    or "zeta3" in cand.lower():
                key = "Q(sqrt(-3))"
        if key is None:
            # default the elliptic-curve-torsion question to its field (the
            # cmsg100 wall is over Q(sqrt(-3))); the adapter resolves the label.
            key = "Q(sqrt(-3))"
        return (REFERENCE_STORES_BY_KIND["elliptic-curve"]["store"], key)
    return None


def _reference_covers(substrate, query: dict[str, Any]
                      ) -> Optional[tuple[str, str]]:
    """feeling_of_findability over the external REFERENCE stores: does an
    external store plausibly cover this gap? Returns (store_name, lookup_key)
    or None.

    GROUNDED coverage signal (not a literal live lookup here — that happens at
    resolve time, off-path): a WORD-MEANING gap (a 'mean'/'define' relation, or
    a query whose queried token is a lexical item) is covered by the dictionary
    reference (Wiktionary / WordNet); the agent's own reference modules
    (dictionary_lexicon / wiktionary_reference) are the stores. We report the
    store as the LABEL + the queried token as the lookup key (knowing_where_vs_
    what: we hold the route, not the answer).

    The MATH reference stores (the cmsg102 source-by-kind registry —
    REFERENCE_STORES_BY_KIND) are checked FIRST: an integer-SEQUENCE gap routes
    to OEIS, an elliptic-curve / torsion / arithmetic-object gap routes to
    LMFDB. So a math reference need PULLS the cited fact (the #3 supply line),
    not just NAMES the route."""
    # MATH reference stores (OEIS / LMFDB) — the registered source-by-kind table.
    math_cov = _math_reference_covers(query)
    if math_cov is not None:
        return math_cov
    event = query.get("event")
    queried = query.get("_queried_slot")
    # A definitional / lexical-meaning question -> a dictionary reference.
    if isinstance(event, str) and event in ("mean", "define", "meaning"):
        # the word being asked about = the bound patient/topic/agent.
        for slot in ("patient", "topic", "agent"):
            v = query.get(slot)
            if isinstance(v, str) and v and v not in _WH:
                return ("dictionary_reference (WordNet/Wiktionary)", v)
    # A 'what is X' identity question over a lexical item -> dictionary.
    if isinstance(queried, str):
        v = query.get(queried)
        # the queried slot itself names a word whose meaning a reference holds.
        if isinstance(v, str) and v in _WH and event in (None, "be", "is"):
            for slot in ("agent", "patient", "topic"):
                w = query.get(slot)
                if isinstance(w, str) and w and w not in _WH:
                    return ("dictionary_reference (WordNet/Wiktionary)", w)
    # COMMONSENSE reference (ConceptNet): a relation gap about a known entity
    # whose ConceptNet START node carries the queried relation — where is a dog
    # (AtLocation), what is a dog (IsA), what is a knife for (UsedFor). FOF
    # positive ONLY when ConceptNet actually holds the relation for the bound
    # entity (a real coverage signal, not a blanket claim). Returns the store +
    # the START concept as the lookup key (the off-path resolver re-derives the
    # relation from the queried slot). Checked here so a commonsense gap routes
    # off the social path (a reference lookup), not to the audience.
    if isinstance(queried, str):
        try:
            from domains import conceptnet_reference as _cn
            relation = _cn.SLOT_RELATION.get(queried)
            if relation is not None:
                for slot in ("agent", "patient", "topic"):
                    w = query.get(slot)
                    if (isinstance(w, str) and w and w not in _WH
                            and slot != queried):
                        if _cn._targets_for(w, relation):
                            return ("conceptnet_reference (commonsense)", w)
        except Exception:
            pass
    return None


def _wiki_covers(substrate, query: dict[str, Any]
                 ) -> Optional[tuple[str, str]]:
    """WIKIPEDIA reference (encyclopedic) coverage. A DEFINITIONAL / 'what is the
    <X> of <Y>' / factual question about a NAMED entity is covered by the open-
    web encyclopedia: the lead extract of the entity's page carries the
    definition or the salient value (a capital, a characteristic). Returns
    ('web_world (wikipedia)', lookup_key) or None.

    This is the LOOKUPABLE subset; the actual fetch happens at resolve time
    (off-path), tagged at the WEB tier so the relevance gate only admits it when
    the depth budget affords the costly tier.

    SCOPE GUARD (``_wiki_kind``) — only the ENCYCLOPEDIC kinds, so a PERSON's
    private contingent fact ('where does Mary live', 'who broke the vase') still
    routes to the transactive interlocutor / conjecture, NOT to Wikipedia."""
    if _wiki_kind(query):
        key = _wiki_lookup_key(query)
        if key is not None:
            return ("web_world (wikipedia)", key)
    return None


def _wiki_kind(query: dict[str, Any]) -> bool:
    """Is this an ENCYCLOPEDIC / DEFINITIONAL question kind (vs a person's
    private contingent fact)? Wikipedia covers 'what is an X' / 'what is the
    <value> of X' — NOT 'where does Mary live' / 'when did Mary arrive' / 'who
    does Mary love' (a contingent fact about a discourse person -> ask the
    interlocutor). Guards, in order:
      * a cause/manner gap is never a lead-extractable encyclopedia answer;
      * a contingent relational queried slot (location/time/recipient) is the
        transactive-interlocutor kind;
      * the question SURFACE (when supplied as `_question_text`) gates it to the
        DEFINITIONAL wh-frame: a where/when/who-fronted question is a contingent
        fact (interlocutor), only a 'what is/are' / 'which' / cue'd question is
        encyclopedic. With no surface text, the slot guard alone applies."""
    event = query.get("event")
    if isinstance(event, str) and event in ("cause", "why", "manner", "how"):
        return False
    queried = query.get("_queried_slot")
    if queried in ("location", "time", "recipient"):
        return False
    qtext = query.get("_question_text")
    if isinstance(qtext, str) and qtext.strip():
        low = qtext.strip().lower()
        # where/when/who/whom/whose-fronted -> a contingent fact, not encyclopedic.
        if low.split()[0] in ("where", "when", "who", "whom", "whose"):
            return False
    return True


def _wiki_lookup_key(query: dict[str, Any]) -> Optional[str]:
    """Pick the salient bound-entity SURFACE to look up on Wikipedia for a
    definitional/factual gap. Coarse, mechanical: prefer the bound patient/topic
    (the thing the 'what is the X of <thing>' asks about), then the agent, then
    the EVENT lemma itself for a bare 'what is a <noun>' question whose noun the
    parser put in the event slot ('what is a rabbit' -> event 'rabbit'). Skips
    the generic placeholder lemmas the grounded parser emits for an under-
    comprehended noun ('feature', 'group', 'set', 'thing') so a degenerate parse
    does not fabricate a lookup."""
    skip = {"feature", "thing", "group", "set", "object", "entity",
            "be", "is", "do", "have"}
    for slot in ("patient", "topic", "agent"):
        v = query.get(slot)
        if (isinstance(v, str) and v and v not in _WH
                and v.lower() not in skip):
            return v
    # Bare 'what is a <noun>' — the parser may put the noun in the event slot.
    ev = query.get("event")
    if (isinstance(ev, str) and ev and ev not in _WH
            and ev.lower() not in skip):
        return ev
    return None


def _solved_class(substrate, query: dict[str, Any]) -> Optional[str]:
    """solved_class_judgment (SCAFFOLDING): general confidence the gap is of a
    LOOKUPABLE class even with no specific source — graded against the agent's
    reference coverage (which question-kinds its stores can answer in principle).

    Coarse grounding: if the agent HOLDS any dictionary/lexicon reference data
    at all (LexEntry / Concept nodes), then word/fact questions are 'a
    lookupable class'. Returns a class label or None."""
    queried = query.get("_queried_slot")
    if queried is None:
        return None
    # Only FACTUAL / LOOKUPABLE queried kinds are a 'solved class'. A who/what/
    # where/when question is the kind a reference/authority can answer; a
    # why(cause) / how(manner) question is NOT a generic-lookup class (no
    # authority holds 'why Mary loved John') -> not solved_class. This keeps the
    # solved-class judgment honest rather than firing on every query.
    if queried not in ("agent", "patient", "topic", "location", "time"):
        return None
    # Does the agent have ANY reference coverage at all? (LexEntry nodes are the
    # grounded reference store; their presence means 'word/fact gaps are a
    # lookupable class' even with no specific source pinned.)
    try:
        has_lex = any(True for _ in substrate.nodes("LexEntry"))
    except Exception:
        has_lex = False
    if not has_lex:
        try:
            has_lex = any(True for _ in substrate.nodes("Concept"))
        except Exception:
            has_lex = False
    if has_lex:
        return "lookupable (reference-class: the agent holds reference stores)"
    return None


# A reference store-label -> its cost TIER (the relevance gate compares the
# tier against the depth budget's affordable tiers). A local grounded store is
# the cheapest; ConceptNet is crowd-sourced commonsense; a dictionary is
# costlier; the open web is the most expensive. Coarse mapping off the store
# label (mechanical, no decision over graph state).
def _reference_tier(store: str) -> str:
    low = (store or "").lower()
    if "conceptnet" in low:
        return "conceptnet"
    if "wiktionary" in low or "wordnet" in low or "dictionary" in low:
        return "wiktionary"
    # OEIS is a LOCAL store (the downloaded dump) — cheapest tier.
    if "oeis" in low:
        return "local"
    # LMFDB is a remote API (a WEB-tier reference) — costliest tier.
    if "lmfdb" in low or "web" in low:
        return "web"
    return "local"


def _tier_affordable(tier: str, depth_budget: Optional[dict[str, Any]]) -> bool:
    """The relevance gate: is `tier` within the depth budget's affordable
    reference tiers? With no budget supplied, all tiers are affordable (the
    legacy, un-gated behaviour). A LOW-relevance budget admits only 'local'."""
    if not depth_budget:
        return True
    affordable = depth_budget.get("ref_tiers")
    if not affordable:
        return True
    return tier in affordable


def _reference_route_from(cov: tuple[str, str],
                          depth_budget: Optional[dict[str, Any]]
                          ) -> Optional[AcquisitionRoute]:
    """Build a REFERENCE AcquisitionRoute from a (store, key) coverage tuple,
    applying the RELEVANCE GATE: a costlier reference tier (conceptnet /
    wiktionary / web) is admitted ONLY when the query's depth budget affords it.
    Returns None when the tier is gated out (the caller falls through to cheaper
    routes) — the choice_stage value-vs-cost, cheaper-tiers-first discipline."""
    store, key = cov
    tier = _reference_tier(store)
    if not _tier_affordable(tier, depth_budget):
        return None
    return AcquisitionRoute(
        "reference", store, cost=ROUTE_COST["reference"],
        basis=(f"feeling_of_findability: the gap is a kind {store} covers "
               f"(tier '{tier}', lookup key '{key}') — gettable off the social "
               f"path"),
        reference_key=key)


def find_route(substrate, query: dict[str, Any], discourse_store,
               interlocutor: Optional[str] = None,
               depth_budget: Optional[dict[str, Any]] = None
               ) -> Optional[AcquisitionRoute]:
    """The FOF / transactive route-finder. For a query UNRESOLVED by grounded +
    chain + conjecture, find an acquisition_route, or None (truly inadmissible).

    Order (cheapest / most-specific first):
      1. INTERLOCUTOR (transactive_memory) — a discourse entity who'd plausibly
         know: the entity the question is ABOUT (a question about Mary's life ->
         Mary), or the current interlocutor. Read off the discourse store.
      2. REFERENCE (feeling_of_findability) — the gap is a kind an external
         store covers (a word meaning -> Wiktionary/WordNet). FOF positive.
      3. SOLVED_CLASS (scaffolding) — general confidence the gap-type is
         lookupable even with no specific source.
    None -> no route at all (the categorical INADMISSIBLE).

    `query` is the comprehended question frame ({event, agent, ..., queried});
    pass `_queried_slot` in it for the reference/solved-class judgments."""
    in_play = _discourse_concepts(discourse_store)
    about = _query_entities(query)

    # 0a. MATH REFERENCE (the cmsg102 source-by-kind registry) — checked FIRST,
    #     ABOVE the generic Wikipedia encyclopedic catch-all: an integer-SEQUENCE
    #     gap is covered by OEIS, an elliptic-curve / torsion / arithmetic-object
    #     gap by LMFDB. These are MORE SPECIFIC reference stores than Wikipedia
    #     for these kinds (you look a sequence up in the OEIS, a curve's torsion
    #     in the LMFDB — not in an encyclopedia lead), so they take priority. The
    #     #3 supply line: the route PULLS the cited fact (OEIS values / LMFDB
    #     empirical max), not just NAMES the route.
    mcov = _math_reference_covers(query)
    if mcov is not None:
        route = _reference_route_from(mcov, depth_budget)
        if route is not None:
            return route

    # 0b. WIKIPEDIA (encyclopedic) REFERENCE — checked FIRST for a DEFINITIONAL /
    #    'what is the <X> of <Y>' gap. An encyclopedic fact is a REFERENCE LOOKUP,
    #    not something the topic-entity is 'a source for itself' about — you do
    #    not ASK France what its capital is, you look it up. So a Wikipedia-
    #    covered definitional gap routes off the social path BEFORE the discourse-
    #    entity step (which would otherwise grab the freshly-introduced topic
    #    entity). The scope guard (_wiki_kind) keeps a person's private contingent
    #    fact OUT of this branch, so 'where does Mary live' / 'who broke the vase'
    #    fall through to the interlocutor / conjecture exactly as before.
    wcov = _wiki_covers(substrate, query)
    if wcov is not None:
        route = _reference_route_from(wcov, depth_budget)
        if route is not None:
            return route

    # 1. INTERLOCUTOR — transactive routing to the entity the question is ABOUT.
    #    Prefer an entity already in the discourse (in play / a source we can
    #    reach), then the current interlocutor as a general source.
    for ent in about:
        if ent in in_play:
            return AcquisitionRoute(
                "interlocutor", ent, cost=ROUTE_COST["interlocutor"],
                basis=(f"transactive_memory: the question is about {ent}, a "
                       f"discourse entity in play -> {ent} is a source for "
                       f"facts about itself"))

    # 2. REFERENCE — FOF over the LOCAL stores (dictionary / ConceptNet). Checked
    #    BEFORE the generic interlocutor fallback: a word MEANING / a commonsense
    #    relation is a reference lookup, not something the user-as-entity is 'a
    #    source for itself' about — so a word/commonsense gap routes off the
    #    social path, not to the audience.
    cov = _reference_covers(substrate, query)
    if cov is not None:
        route = _reference_route_from(cov, depth_budget)
        if route is not None:
            return route
        # else: gated — fall through to cheaper routes.

    # 3. The current interlocutor is a fallback source ONLY when the question has
    #    a concrete bound subject to ask ABOUT (something coherent to pose) — a
    #    contentless query (no entity, an unlookupable kind) is NOT routed to the
    #    interlocutor generically, so it can fall through to INADMISSIBLE.
    #    (Without this guard the interlocutor would be a universal source and the
    #    categorical 'I don't know' could never fire.)
    if interlocutor and about:
        return AcquisitionRoute(
            "interlocutor", interlocutor, cost=ROUTE_COST["interlocutor"],
            basis=(f"transactive_memory: the current interlocutor "
                   f"({interlocutor}) is a present source to ask about "
                   f"{about[0]}"))

    # 4. SOLVED_CLASS — general lookupability (scaffolding).
    sc = _solved_class(substrate, query)
    if sc is not None:
        return AcquisitionRoute(
            "solved_class", sc, cost=ROUTE_COST["solved_class"],
            basis=(f"solved_class_judgment (scaffolding): {sc}"))

    return None


# ===========================================================================
# social_capital — the budget node (graph state on the conversation).
# ===========================================================================

def _get_or_create_social_capital(substrate) -> Any:
    """The single SocialCapital node for the conversation (graph state). Created
    at SC_INITIAL on first access. Idempotent (returns the existing one)."""
    for nid in substrate.nodes("SocialCapital"):
        return nid
    return substrate.add_node("SocialCapital", {
        "balance": SC_INITIAL,
        "recent_asks": 0,
        "turn": 0,
    })


def social_capital_balance(substrate) -> float:
    nid = _get_or_create_social_capital(substrate)
    return float(substrate.node(nid)["attrs"].get("balance", SC_INITIAL))


def social_capital_snapshot(substrate) -> dict[str, Any]:
    nid = _get_or_create_social_capital(substrate)
    a = substrate.node(nid)["attrs"]
    return {"balance": float(a.get("balance", SC_INITIAL)),
            "recent_asks": float(a.get("recent_asks", 0) or 0),
            "turn": int(a.get("turn", 0) or 0)}


def tick_social_capital(substrate) -> dict[str, Any]:
    """Advance the budget one turn: regenerate balance slowly toward SC_MAX and
    decay the recent-ask count (cumulative_question_burden cools over turns).
    Called once per conversational turn by the world adapter. Pure graph
    mutation (regeneration is mechanical, not a decision)."""
    nid = _get_or_create_social_capital(substrate)
    a = substrate.node(nid)["attrs"]
    bal = min(SC_MAX, float(a.get("balance", SC_INITIAL)) + SC_REGEN_PER_TURN)
    recent = max(0.0, float(a.get("recent_asks", 0) or 0) - RECENT_DECAY_PER_TURN)
    turn = int(a.get("turn", 0) or 0) + 1
    for k, v in (("balance", bal), ("recent_asks", recent), ("turn", turn)):
        try:
            substrate.set_attr(nid, k, v)
        except Exception:
            pass
    return {"balance": bal, "recent_asks": recent, "turn": turn}


def _spend_social_capital(substrate, amount: float) -> float:
    """Spend on a surfaced ask: deplete the balance + bump recent_asks (the
    cumulative_question_burden term). Returns the new balance."""
    nid = _get_or_create_social_capital(substrate)
    a = substrate.node(nid)["attrs"]
    bal = max(0.0, float(a.get("balance", SC_INITIAL)) - float(amount))
    recent = float(a.get("recent_asks", 0) or 0) + 1.0
    for k, v in (("balance", bal), ("recent_asks", recent)):
        try:
            substrate.set_attr(nid, k, v)
        except Exception:
            pass
    return bal


def _ask_cost(substrate, route: AcquisitionRoute) -> dict[str, float]:
    """The full social COST of surfacing THIS ask now, decomposed (so the test
    can print WHY). cost = route.cost (obtain) + flow_cost + face_imposition
    base (SC_ASK_COST) + cumulative_question_burden (rises with recent asks).
    All HEURISTIC weights."""
    snap = social_capital_snapshot(substrate)
    burden = BURDEN_PER_RECENT * snap["recent_asks"]
    # flow cost: an interlocutor route is on-topic (the audience IS the source);
    # a reference/solved-class ask would be off the social path (off-topic to
    # voice aloud), so surfacing it is a flow disruption.
    flow = (FLOW_COST_ON_TOPIC if route.route_type == "interlocutor"
            else FLOW_COST_OFF_TOPIC)
    face = SC_ASK_COST                      # face_imposition base (per ask)
    total = route.cost + flow + face + burden
    return {"obtain": route.cost, "flow_cost": flow, "face_imposition": face,
            "cumulative_burden": burden, "total": total}


# ===========================================================================
# materiality + audience_appropriateness — the VALUE + the precondition.
# ===========================================================================

def materiality(query: dict[str, Any], discourse_store,
                route: Optional["AcquisitionRoute"] = None) -> dict[str, Any]:
    """The VALUE side (SCAFFOLDING, Grice relevance): is the answer relevant to
    the CURRENT exchange? Coarse grounding:
      * an explicit immaterial mark -> immaterial (the world adapter may flag an
        aside / curiosity);
      * a gap ABOUT an entity in play (in the discourse store) -> material;
      * a REFERENCE-route gap whose lookup token is bound in the query (the user
        just asked about that word) -> material (it IS the current exchange);
      * otherwise -> immaterial (a curiosity, not needed now).
    Returns {material, value, why}."""
    # explicit override (the world adapter may mark a gap immaterial).
    if query.get("_immaterial"):
        return {"material": False, "value": IMMATERIAL_VALUE,
                "why": "marked immaterial to the current exchange"}
    in_play = _discourse_concepts(discourse_store)
    about = _query_entities(query)
    is_mat = bool(about) and any(e in in_play for e in about)
    if is_mat:
        return {"material": True, "value": MATERIAL_VALUE,
                "why": (f"about {[e for e in about if e in in_play]} — "
                        f"in play in the current exchange")}
    # A reference gap the user is asking about right now (e.g. a word meaning) is
    # material to the exchange even though the word is not a discourse 'entity'.
    if route is not None and route.route_type == "reference":
        return {"material": True, "value": MATERIAL_VALUE,
                "why": (f"reference gap (lookup '{route.reference_key}') asked in "
                        f"the current exchange — material")}
    return {"material": False, "value": IMMATERIAL_VALUE,
            "why": (f"about {about or '(no entity)'} — not in the current "
                    f"discourse (immaterial here)")}


def audience_is_source(route: AcquisitionRoute,
                       interlocutor: Optional[str]) -> bool:
    """audience_appropriateness precondition (Clark, SCAFFOLDING): is the
    CURRENT audience the route's source (so the ask can be voiced to THEM)?
    True only for an INTERLOCUTOR route whose source is reachable in this
    conversation — a reference/solved-class route's 'source' is NOT the present
    audience, so it must be banked (resolved off the social path)."""
    return route.route_type == "interlocutor"


# ===========================================================================
# surface_vs_bank_vs_drop — the cost-benefit control output.
# ===========================================================================

def surface_vs_bank_vs_drop(substrate, route: AcquisitionRoute,
                            query: dict[str, Any], turn: int,
                            discourse_store=None,
                            interlocutor: Optional[str] = None
                            ) -> dict[str, Any]:
    """The control output (the taught ``surface_vs_bank_vs_drop``): ASK / BANK /
    DROP for a resolvable_via_route gap. A cost-benefit over the CONVERSATION,
    NOT a confidence cutoff.

      VALUE = materiality (immaterial -> DROP).
      SOCIAL COST = route.cost + flow_cost + face_imposition +
                    cumulative_question_burden, weighed against social_capital.
      DECIDE:
        DROP  iff immaterial.
        ASK   iff material AND the current audience IS the route's source AND
              value > social cost AND the budget can afford the ask.
        BANK  otherwise (material but: audience is NOT the source -> a reference/
              off-path route; or value <= cost; or budget too low) — defer the
              gap off the social path.

    Returns {decision, value, cost (decomposed), balance, affordable, why}.
    Spending of social_capital happens in `decide_and_record` (the caller that
    actually surfaces), so this function is a pure read (no mutation)."""
    mat = materiality(query, discourse_store, route)
    cost = _ask_cost(substrate, route)
    bal = social_capital_balance(substrate)
    affordable = bal >= cost["total"]
    aud = audience_is_source(route, interlocutor)

    # DROP — immaterial to the exchange (value side fails). Never surface.
    if not mat["material"]:
        return {"decision": "drop", "value": mat["value"], "cost": cost,
                "balance": bal, "affordable": affordable,
                "materiality": mat, "audience_is_source": aud,
                "why": (f"DROP: immaterial ({mat['why']}); an immaterial gap is "
                        f"never surfaced (Gricean relevance)")}

    # Material from here. Surface only if the audience is the source AND the
    # value beats the social cost AND the budget can afford it.
    value_beats_cost = mat["value"] > cost["total"]
    if aud and value_beats_cost and affordable:
        return {"decision": "ask", "value": mat["value"], "cost": cost,
                "balance": bal, "affordable": affordable,
                "materiality": mat, "audience_is_source": aud,
                "why": (f"ASK: material ({mat['why']}); audience IS the route "
                        f"source; value {mat['value']:.2f} > social cost "
                        f"{cost['total']:.2f}; balance {bal:.2f} affords it")}

    # BANK — material + a route exists, but surfacing now is wrong: either the
    # audience is not the source (reference/off-path), or the value doesn't beat
    # the social cost (incl. cumulative burden), or the budget is too low.
    if not aud:
        reason = (f"route source is {route.source} (a {route.route_type}), NOT "
                  f"the current audience -> resolve off the social path")
    elif not affordable:
        reason = (f"budget {bal:.2f} < ask cost {cost['total']:.2f} (social "
                  f"capital depleted / cumulative burden "
                  f"{cost['cumulative_burden']:.2f}) -> too costly to ask now")
    else:
        reason = (f"value {mat['value']:.2f} <= social cost {cost['total']:.2f} "
                  f"-> not worth surfacing now")
    return {"decision": "bank", "value": mat["value"], "cost": cost,
            "balance": bal, "affordable": affordable,
            "materiality": mat, "audience_is_source": aud,
            "why": f"BANK: {reason}"}


# ===========================================================================
# bank_for_later — the PendingGap node + off-path resolution.
# ===========================================================================

def bank_for_later(substrate, query: dict[str, Any],
                   route: AcquisitionRoute) -> Any:
    """Record a banked gap as a PendingGap NODE (the deliberate babble loop):
    the query + its route, to be resolved later off the social path (a reference
    lookup, or a future turn whose interlocutor is the source). Returns the node
    id. Graph mutation only."""
    qslot = query.get("_queried_slot", "")
    attrs = {
        "queried_slot": qslot if isinstance(qslot, str) else "",
        "event": query.get("event") if isinstance(query.get("event"), str) else "",
        "route_type": route.route_type,
        "route_source": route.source,
        "reference_key": route.reference_key or "",
        "cost": route.cost,
        "basis": route.basis,
        "resolved": False,
        "answer": "",
    }
    # Carry the bound entities so an off-path resolver can re-pose the query.
    for slot in ("agent", "patient", "topic", "location", "recipient"):
        v = query.get(slot)
        if isinstance(v, str) and v and v not in _WH:
            attrs[slot] = v
    return substrate.add_node("PendingGap", attrs)


def pending_gaps(substrate, resolved: Optional[bool] = None) -> list[Any]:
    """The banked PendingGap nodes (optionally filtered by resolved state)."""
    out = []
    for nid in substrate.nodes("PendingGap"):
        a = substrate.node(nid)["attrs"]
        if resolved is None or bool(a.get("resolved", False)) == resolved:
            out.append(nid)
    return out


def resolve_banked_gaps(substrate, discourse_store=None,
                        interlocutor: Optional[str] = None,
                        reference_lookup=None) -> list[dict[str, Any]]:
    """Resolve banked gaps OFF the social path — the deliberate babble loop. For
    each unresolved PendingGap, try its route's source WITHOUT burdening the
    audience:

      * REFERENCE route -> call `reference_lookup(store, key)` (a world-adapter
        supplied callable that consults the external store, e.g. dictionary/
        wiktionary). If it returns a value, GROUND it (a KnownFact node) and
        mark the gap resolved.
      * INTERLOCUTOR route -> resolvable only when that source is now reachable
        (its concept is in the discourse store / equals the interlocutor) AND a
        grounding becomes available; otherwise it stays pending (HONEST: a
        banked person-question is NOT faked).

    Returns a list of resolution traces. Only resolves when a REAL route
    supplies the answer — nothing is fabricated."""
    traces: list[dict[str, Any]] = []
    for nid in pending_gaps(substrate, resolved=False):
        a = substrate.node(nid)["attrs"]
        rtype = a.get("route_type")
        if rtype == "reference" and reference_lookup is not None:
            key = a.get("reference_key") or ""
            store = a.get("route_source") or ""
            try:
                val = reference_lookup(store, key)
            except Exception:
                val = None
            if val:
                _ground_resolved_gap(substrate, nid, a, str(val))
                traces.append({
                    "gap": str(nid), "resolved": True, "route": "reference",
                    "source": store, "key": key, "answer": str(val),
                    "how": (f"off-path reference lookup ({store}['{key}']) -> "
                            f"{val}; grounded as a KnownFact, NO question to "
                            f"the audience")})
                continue
            traces.append({
                "gap": str(nid), "resolved": False, "route": "reference",
                "source": store, "key": key,
                "how": f"reference {store} returned nothing for '{key}' "
                       f"(stays pending — not faked)"})
            continue
        if rtype == "interlocutor":
            traces.append({
                "gap": str(nid), "resolved": False, "route": "interlocutor",
                "source": a.get("route_source"),
                "how": (f"interlocutor route to {a.get('route_source')}: stays "
                        f"pending until that source is the live audience "
                        f"(not fabricated)")})
            continue
        traces.append({
            "gap": str(nid), "resolved": False, "route": rtype,
            "source": a.get("route_source"),
            "how": "no off-path resolver available for this route type"})
    return traces


def _ground_resolved_gap(substrate, gap_nid, gap_attrs: dict[str, Any],
                         answer: str) -> None:
    """Ground a resolved banked gap: mark the PendingGap resolved + mint a
    KnownFact carrying the answer in the queried slot (so a LATER turn answers
    it from the grounded store, with no question asked). Graph mutation only."""
    try:
        substrate.set_attr(gap_nid, "resolved", True)
        substrate.set_attr(gap_nid, "answer", answer)
    except Exception:
        pass
    # Mint the grounded fact: the bound slots + the queried slot filled.
    fact_attrs: dict[str, Any] = {"language": "en", "origin": "banked_resolution"}
    ev = gap_attrs.get("event")
    if isinstance(ev, str) and ev:
        fact_attrs["event"] = ev
    for slot in ("agent", "patient", "topic", "location", "recipient"):
        v = gap_attrs.get(slot)
        if isinstance(v, str) and v:
            fact_attrs[slot] = v
    qslot = gap_attrs.get("queried_slot")
    if isinstance(qslot, str) and qslot:
        fact_attrs[qslot] = answer
    try:
        substrate.add_node("KnownFact", fact_attrs)
    except Exception:
        pass


# ===========================================================================
# THE STANCE — the top-level entry the conversation calls when grounded+chain+
# conjecture have all missed (escalation BELOW conjecture, ABOVE inadmissible).
# ===========================================================================

def decide_and_record(substrate, query: dict[str, Any], turn: int,
                      discourse_store=None,
                      interlocutor: Optional[str] = None,
                      depth_budget: Optional[dict[str, Any]] = None,
                      reference_lookup=None,
                      reference_detail=None) -> dict[str, Any]:
    """The epistemic_access_stance for a gap with no grounded/chain/conjecture
    answer. Finds a route, decides ask/bank/drop by the social cost-benefit,
    SPENDS social_capital on an ask, BANKS a PendingGap when banked, and records
    an EpistemicAccessStance trace node. Returns the stance dict the world
    adapter turns into a reply:

      {band, route?, decision, materiality, cost, balance, why, pending_gap?}

    band = RESOLVABLE_VIA_ROUTE when a route exists; INADMISSIBLE when none.

    `depth_budget` (from domains.dynamic_depth) RELEVANCE-GATES the reference
    escalation: a costly reference tier is only admitted when the query's
    relevance affords it, so a low-relevance gap never routes to the web.

    `reference_lookup` (a world-adapter callable ``(store, key) -> answer|None``)
    AUTO-RESOLVES a *reference* route IN THIS TURN: when the route is a REFERENCE
    (not ask-the-interlocutor) and the resolver returns an answer, the gap is
    banked-then-resolved off the social path (PendingGap.resolved + .answer set,
    a KnownFact minted) and the stance becomes ``decision="answered"`` carrying
    the answer — so an 'I-don't-know-but-could-look-it-up' becomes an ANSWER with
    NO question to the audience. ask-the-interlocutor routes are untouched; a
    resolver returning None leaves the existing bank/ask behaviour unchanged."""
    route = find_route(substrate, query, discourse_store, interlocutor,
                       depth_budget=depth_budget)
    if route is None:
        stance = {"band": "INADMISSIBLE", "route": None, "decision": "decline",
                  "why": "no acquisition route (no source, no reference, not a "
                         "lookupable class) -> categorical 'I don't know'"}
        _record_stance(substrate, query, stance)
        return stance

    # AUTO-RESOLVE a REFERENCE route in-turn: the taught 'reference' route is an
    # off-path lookup with NO social cost (audience is not the source). If a
    # resolver is supplied and the store answers, RESOLVE NOW rather than hedge.
    if route.route_type == "reference" and reference_lookup is not None:
        answer, provenance = _resolve_reference_now(
            substrate, query, route, reference_lookup,
            reference_detail=reference_detail)
        if answer is not None:
            where = provenance.get("where") if provenance else None
            stance = {
                "band": "RESOLVABLE_VIA_ROUTE",
                "route": route.as_dict(),
                "decision": "answered",
                "answer": answer,
                # PROVENANCE: the agent knows WHAT it read — the answer carries
                # WHERE/WHO/HOW/WHAT/WHEN + the source's epistemic weight, so it
                # is ATTRIBUTABLE ('I read in Wikipedia that …'), not a bare
                # assertion. Read off the held source understanding.
                "provenance": provenance,
                "materiality": {"material": True, "value": MATERIAL_VALUE,
                                "why": "resolved off-path via the reference "
                                       "route"},
                "value": MATERIAL_VALUE,
                "balance": social_capital_balance(substrate),
                "audience_is_source": False,
                "why": (f"ANSWERED: reference route ({route.source}, "
                        + (f"article '{where}', " if where else "")
                        + f"key '{route.reference_key}') resolved off the social "
                        f"path -> {answer!r}; NO question put to the audience "
                        + ("(attributable to the source)" if provenance else "")),
            }
            _record_stance(substrate, query, stance)
            return stance

    dec = surface_vs_bank_vs_drop(substrate, route, query, turn,
                                  discourse_store, interlocutor)
    stance: dict[str, Any] = {
        "band": "RESOLVABLE_VIA_ROUTE",
        "route": route.as_dict(),
        "decision": dec["decision"],
        "materiality": dec["materiality"],
        "value": dec["materiality"]["value"],
        "cost": dec["cost"],
        "balance": dec["balance"],
        "audience_is_source": dec["audience_is_source"],
        "why": dec["why"],
    }

    if dec["decision"] == "ask":
        new_bal = _spend_social_capital(substrate, dec["cost"]["total"])
        stance["balance_after"] = new_bal
        stance["spent"] = dec["cost"]["total"]
    elif dec["decision"] == "bank":
        gap = bank_for_later(substrate, query, route)
        stance["pending_gap"] = str(gap)
    # drop spends nothing, banks nothing.

    _record_stance(substrate, query, stance)
    return stance


def _answer_coheres_with_queried_property(query: dict[str, Any],
                                          detail: Optional[dict[str, Any]]
                                          ) -> bool:
    """Gap 2: an answer COHERES WITH THE QUERIED PROPERTY iff the read produced a
    VALUE that fills the question's queried (WH) slot — NOT merely the entity's
    definitional lead.

    The reference reader tags every hit with its KIND (reference_route.
    _extract_answer): "value" means a value-cue in the question matched and a
    salient VALUE was pulled (it FILLS the queried property/slot); "definition"
    means no queried property matched, so only the entity's lead sentence came
    back (the entity's DEFINITION, which fills no queried slot).

    'what is the capital of France' -> kind "value" (Paris fills the queried
    slot) -> coheres. 'largest order of a ... torsion subgroup of an elliptic
    curve' -> kind "definition" (the elliptic-curve lead, no value for the
    queried 'largest order' property) -> does NOT cohere -> reject -> abstain.

    When no detail/kind is available (a resolver that does not report kind, e.g.
    ConceptNet), we do not block — only a positively-identified entity-definition
    lead is rejected. Nothing fabricated either way."""
    if not isinstance(detail, dict):
        return True  # no kind reported -> do not block (additive, conservative)
    kind = detail.get("kind")
    if kind is None:
        return True
    # the read must have filled the queried property with a value, not returned
    # the entity's definitional lead.
    return kind == "value"


def _reference_provenance(substrate, route: AcquisitionRoute,
                          detail: Optional[dict[str, Any]]
                          ) -> Optional[dict[str, Any]]:
    """The PROVENANCE of a reference-resolved answer: WHERE/WHO/HOW/WHAT/WHEN it
    came from + the source's epistemic status. Read off the agent's HELD
    understanding of the source (the `wikipedia` concept's provenance template +
    reliability — graph data) via source_provenance, with WHERE filled from the
    reference hit's title. So the agent knows what it read and can ATTRIBUTE it
    ("I read in Wikipedia that …") carrying the consensus-tertiary weight, not a
    bare assertion. None when the source isn't a held/modeled one."""
    try:
        from domains import source_provenance as _sp
    except Exception:
        return None
    where = None
    if isinstance(detail, dict):
        where = detail.get("title") or detail.get("where")
    prov = _sp.provenance_for_source(substrate, route.source, where=where)
    if prov is None:
        return None
    epi = _sp.epistemic_status_for_source(substrate, route.source)
    if epi is not None:
        prov = dict(prov)
        prov["epistemic_status"] = epi.get("status")
        prov["reliability"] = epi.get("reliability")
    return prov


def _resolve_reference_now(substrate, query: dict[str, Any],
                           route: AcquisitionRoute,
                           reference_lookup,
                           reference_detail=None
                           ) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    """Try the reference route's resolver immediately (off the social path). On
    a hit: CHECK the answer coheres with the queried property (Gap 2 — it must
    FILL the queried slot with a value, not be the entity's definitional lead),
    then bank the gap and ground it (PendingGap.resolved + .answer set + a
    KnownFact minted via _ground_resolved_gap). Returns (answer, provenance), or
    (None, None) (web unreachable / no extract / resolver declined / answer does
    NOT cohere with the queried property) so the caller falls back to the normal
    bank/ask behaviour. Nothing fabricated. The PROVENANCE (WHERE/WHO/HOW/WHAT/
    WHEN + epistemic status) is read off the agent's HELD source understanding so
    the answer can be ATTRIBUTED.

    `reference_detail` (optional ``(store, key) -> hit-dict|None``) returns the
    full reference hit so the queried-property coherence check can read the
    answer's KIND. When absent, the string `reference_lookup` is used and the
    coherence check does not block (conservative additive default)."""
    store = route.source
    key = route.reference_key or ""
    detail: Optional[dict[str, Any]] = None
    val: Optional[Any] = None
    if reference_detail is not None:
        try:
            detail = reference_detail(store, key)
        except Exception:
            detail = None
        if isinstance(detail, dict):
            val = detail.get("answer")
    if not val:
        try:
            val = reference_lookup(store, key)
        except Exception:
            val = None
    if not val:
        return None, None
    # Gap 2: the answer must COHERE WITH THE QUERIED PROPERTY — fill the queried
    # slot with a value, not merely name the entity (its definitional lead). An
    # entity-definition lead is rejected here -> the turn falls through to an
    # honest abstain rather than "answering" with the entity's definition.
    if not _answer_coheres_with_queried_property(query, detail):
        return None, None
    answer = str(val)
    provenance = _reference_provenance(substrate, route, detail)
    # Record the resolved gap as graph state (bank-then-resolve), so a later turn
    # answers it from the grounded KnownFact with NO question asked. Carry the
    # provenance onto the PendingGap so a later answer is still attributable.
    gap = bank_for_later(substrate, query, route)
    if provenance:
        try:
            import json as _json
            substrate.set_attr(gap, "provenance", _json.dumps(provenance))
        except Exception:
            pass
    gap_attrs = substrate.node(gap)["attrs"]
    _ground_resolved_gap(substrate, gap, dict(gap_attrs), answer)
    return answer, provenance


def _record_stance(substrate, query: dict[str, Any],
                   stance: dict[str, Any]) -> Any:
    """Mint an EpistemicAccessStance node (graph-resident, inspectable like a
    Conjecture node): the band + decision + route + rationale. Best-effort."""
    route = stance.get("route") or {}
    cost = stance.get("cost") or {}
    try:
        return substrate.add_node("EpistemicAccessStance", {
            "band": stance.get("band", ""),
            "decision": stance.get("decision", ""),
            "route_type": route.get("route_type", "") if route else "",
            "route_source": route.get("source", "") if route else "",
            "queried_slot": query.get("_queried_slot", "") or "",
            "event": query.get("event") if isinstance(query.get("event"), str) else "",
            "value": float(stance.get("materiality", {}).get("value", 0.0))
            if stance.get("materiality") else 0.0,
            "social_cost": float(cost.get("total", 0.0)) if cost else 0.0,
            "balance": float(stance.get("balance", 0.0)),
            "why": stance.get("why", ""),
            "origin": "epistemic_access",
        })
    except Exception:
        return None


# ===========================================================================
# Reply forms — integrate with the conjecture hedges (read from the graph).
# ===========================================================================

# Per-language surface for the resolvable-via-route reply forms. These are
# fixed grounded discourse tokens (like conjecture's _DONT_KNOW_TOKEN), used
# only where there is no propositional frame to produce. The hedged ASK wording
# realises the held face_imposition concept (an indirect, hedged request).
_ASK_GENERIC = {
    "en": "I don't know — I'd need to check.",
    "es": "No lo sé — tendría que comprobarlo.",
    "ja": "わかりません — 確認が必要です。",
}
_BANK_TOKEN = {
    "en": "I'm not sure — I'll find out.",
    "es": "No estoy seguro — lo averiguaré.",
    "ja": "わかりませんが — 調べておきます。",
}
_DONT_KNOW_TOKEN = {
    "en": "I don't know.", "es": "No lo sé.",
    "zh": "我不知道。", "ja": "わかりません。",
}

# ATTRIBUTION lead — a per-language "I read in <SOURCE> that …" prefix. The
# SOURCE name comes from the provenance (read off the held source understanding),
# not hardcoded per concept. A reference-route answer carries its provenance +
# the consensus-tertiary epistemic weight, not a bare assertion.
_ATTRIBUTION_LEAD = {
    "en": "I read in {source} that {claim}",
    "es": "Leí en {source} que {claim}",
    "ja": "{source}で{claim}と読みました。",
}

# A held provenance `source` tag -> its readable, capitalised name for the
# attribution surface (the WHERE/genre the agent holds). Coarse label map; the
# UNDERSTANDING is the held graph data, this only renders the name.
_SOURCE_DISPLAY = {"wikipedia": "Wikipedia", "oeis": "the OEIS",
                   "lmfdb": "the LMFDB"}


def _attribute(claim: str, provenance: Optional[dict[str, Any]],
               language: str = "en") -> str:
    """Prefix `claim` with the source ATTRIBUTION when provenance is present
    ("I read in Wikipedia that <claim>"), else return the claim unchanged (a
    bare assertion when the source is not held/attributable). The source NAME is
    read off the provenance the agent holds, not hardcoded per answer. The agent
    knows what it read — the source is part of the meaning."""
    if not isinstance(provenance, dict):
        return claim
    src = provenance.get("source")
    if not isinstance(src, str) or not src:
        return claim
    name = _SOURCE_DISPLAY.get(src.lower(), src.replace("_", " ").title())
    lead = _ATTRIBUTION_LEAD.get(language, _ATTRIBUTION_LEAD["en"])
    # lowercase the leading article of the claim so it reads "… that the capital
    # … is Paris" rather than "… that Paris." for a bare value: keep the claim as
    # given (it is a short value/sentence); just strip a trailing period for the
    # 'that …' embedding, then restore terminal punctuation.
    body = claim.strip()
    if language == "ja":
        return lead.format(source=name, claim=body.rstrip("."))
    embedded = body[:-1] if body.endswith(".") else body
    return lead.format(source=name, claim=embedded) + "."


def _surface_token_for_slot(query: dict[str, Any]) -> Optional[str]:
    """A readable name for what the question is about, for an ASK reply ("do you
    know where Mary lives?"). Coarse: the queried slot + the bound subject."""
    subj = None
    for slot in ("agent", "patient", "topic"):
        v = query.get(slot)
        if isinstance(v, str) and v and v not in _WH:
            subj = v
            break
    qslot = query.get("_queried_slot")
    ev = query.get("event")
    wh = {"location": "where", "agent": "who", "patient": "what",
          "time": "when", "cause": "why", "manner": "how"}.get(qslot or "", "")
    if subj and isinstance(ev, str) and ev and wh:
        return f"{wh} {subj} {ev}s"          # "where Mary lives"
    if subj and wh:
        return f"{wh} {subj} is"
    return None


def reply_for_stance(stance: dict[str, Any], query: dict[str, Any],
                     language: str = "en",
                     conjecture_reply: Optional[str] = None) -> str:
    """Turn the epistemic_access stance into a reply, integrating with the
    conjecture fallback where natural:

      RESOLVABLE + ASK  -> a hedged surfaced question. If a conjecture exists,
                           COMBINE: "I think it's like X — want me to find out?"
      RESOLVABLE + BANK -> a brief deferral (or just proceed); the PendingGap is
                           already recorded.
      RESOLVABLE + DROP -> fall back to the conjecture if any, else proceed.
      INADMISSIBLE      -> the conjecture if any, else "I don't know."

    `conjecture_reply` is the LOW-band conjecture surface (from conjecture.hedge)
    when the agent ALSO holds a shape; passed so the forms can combine."""
    band = stance.get("band")
    decision = stance.get("decision")

    if band == "INADMISSIBLE":
        if conjecture_reply:
            return conjecture_reply
        return _DONT_KNOW_TOKEN.get(language, "I don't know.")

    # RESOLVABLE_VIA_ROUTE.
    # ANSWERED — a reference route resolved off-path IN THIS TURN. The extracted
    # answer IS the reply (the lookupable/definitional gap converted to a fact).
    # ATTRIBUTION: a competent reader says WHERE it read it. When the stance
    # carries provenance (read off the held source understanding), the reply is
    # PREFIXED with the attribution ("I read in Wikipedia that …") carrying the
    # consensus-tertiary epistemic weight — not a bare assertion.
    if decision == "answered":
        ans = stance.get("answer")
        if isinstance(ans, str) and ans.strip():
            core = ans.strip() if ans.strip().endswith((".", "!", "?")) \
                else ans.strip() + "."
            return _attribute(core, stance.get("provenance"), language)
        # No answer string (shouldn't happen) -> fall through to bank/conjecture.
        if conjecture_reply:
            return conjecture_reply
        return _BANK_TOKEN.get(language, _BANK_TOKEN["en"])

    if decision == "ask":
        route = stance.get("route") or {}
        # Audience IS the source -> a direct hedged question to them.
        about = _surface_token_for_slot(query)
        if language == "en" and about:
            q = f"I don't know — do you know {about}?"
        else:
            q = _ASK_GENERIC.get(language, _ASK_GENERIC["en"])
        if conjecture_reply:
            # COMBINE conjecture + route: "I think it's like X — want me to
            # find out for sure?"
            base = conjecture_reply.rstrip(".")
            if language == "en":
                return f"{base} — want me to find out for sure?"
            return f"{conjecture_reply} {q}"
        return q

    if decision == "bank":
        if conjecture_reply:
            # proceed with the conjecture; the gap is banked silently.
            return conjecture_reply
        return _BANK_TOKEN.get(language, _BANK_TOKEN["en"])

    # drop.
    if conjecture_reply:
        return conjecture_reply
    # immaterial + no shape: proceed with the honest don't-know (no question).
    return _DONT_KNOW_TOKEN.get(language, "I don't know.")


__all__ = [
    "AcquisitionRoute", "find_route",
    "SC_INITIAL", "SC_MAX", "SC_ASK_COST", "SC_REGEN_PER_TURN",
    "BURDEN_PER_RECENT", "ROUTE_COST", "MATERIAL_VALUE", "IMMATERIAL_VALUE",
    "social_capital_balance", "social_capital_snapshot",
    "tick_social_capital",
    "materiality", "audience_is_source", "surface_vs_bank_vs_drop",
    "bank_for_later", "pending_gaps", "resolve_banked_gaps",
    "decide_and_record", "reply_for_stance",
]
