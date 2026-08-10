"""conjecture — the CONFIDENCE CONTINUUM and PURE-CONJECTURE generator.

The project's admissibility thesis is binary FOR A SPECIFIC STRUCTURE: the
substrate admits a grounded structure or it does not — there is no "60 %
admissible" KnownFact ([[ozma_recognition_is_a_conjunction]]). This module does
NOT soften that. It adds a SECOND thing the agent can hold ALONGSIDE the
(absent) grounded structure: a LOW-WEIGHT CONJECTURED structure — an
abstract-shape guess carried at an explicit epsilon confidence.

So the answer calculus becomes a CONTINUUM, not a binary:

    grounded fact        confidence ~1.0       HIGH         -> "X."
    order-N chain        product of hops       HIGH/MID     -> "X." / "Probably X."
    conjecture (shape)   epsilon (~0.05-0.15)  LOW          -> "I think it's like X."
    no shape at all      —                     INADMISSIBLE -> "I don't know."

"I don't know" is RESERVED for the categorical no: no grounded fact, no chain,
AND no abstract shape to even guess from (the structure is genuinely
inadmissible — there is nothing to instantiate a guess over). Everything that
HAS a shape gets a conjecture with its confidence interval, not silence.

WHERE THE GUESSES COME FROM (the agent's OWN shape machinery — no hardcoded
guess table):

  * TYPE / ROLE conjecture — the queried slot's EXPECTED filler category, read
    off the graph-resident RolePrior nodes (seeds/conceptual_categories.json:
    slot -> expected_categories / proper_category). A 'location' query expects a
    place; an 'agent' query expects a person/animal. A type-level guess: "I
    think it's a <category>." This is the role's selectional prior, the same
    graph data phase_composer_language_rules consults to TYPE an unknown — here
    reused to GUESS a missing filler.

  * ANALOGY conjecture — structural transfer from same-type-same-slot grounded
    facts (the shape-transfer idea of domains/analogy.py, applied to KnownFact
    role slots). Asked where Mary lives with no fact, but OTHER persons live in
    cities -> conjecture one of those places ("maybe a city, like Paris"). The
    basis is the analogue fact the guess was transferred from.

Both carry weight = EPSILON and a `basis` string (why this guess). The weight
ENTERS THE CALCULATION: a conjectured link is exposed at epsilon so the order-N
reasoner can compose a chain with ONE conjectured hop and return confidence =
product(grounded_hops) * epsilon — the guess participates, it is not excluded.

HONEST: a conjecture is GENUINELY low confidence. Always reported with its
weight + basis; never presented as a grounded fact. "I think it's like X" =
admissible-at-epsilon; "I don't know" = inadmissible (no shape).

See [[ozma_recognition_is_a_conjunction]] (binary-for-a-structure) /
[[ozma_analogical_transfer]] (shape transfer) / [[ozma_order_n_reasoning]].
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from domains import order_n_reasoning as onr

try:
    from domains import interrogative_reference as _ireg
    _WH = _ireg.ALL_PLACEHOLDERS
except Exception:  # pragma: no cover
    _WH = ("?WHO", "?WHAT", "?WHERE", "?WHEN", "?WHY", "?HOW")


# ---------------------------------------------------------------------------
# The confidence model — one number in [0,1] on every answer/inference, and
# the BANDS that map a confidence to a reply form.
# ---------------------------------------------------------------------------

# Per-grounded-hop weight: a directly stored fact is near-certain, but each
# composition hop in an order-N chain shaves a little off (the chain is only as
# strong as the joins). product over hops => confidence decays with depth.
GROUNDED_HOP: float = 0.9
# Conjecture weight — extreme low. A shape-guess, not a fact.
EPSILON: float = 0.1

# Band thresholds (on the [0,1] confidence).
BAND_HIGH: float = 0.7      # >= HIGH      -> assert
BAND_MID: float = 0.3       # >= MID       -> probably / I think
# < MID and > 0                -> LOW       -> conjecture ("I think it's like X")
# no candidate at all          -> INADMISSIBLE -> "I don't know"


def chain_confidence(order: int, hop: float = GROUNDED_HOP) -> float:
    """Confidence of an all-grounded order-N chain = product of `order` grounded
    hops. order-1 (a stored fact read directly) = hop**1 ≈ 0.9; order-2 ≈ 0.81;
    decaying with depth, exactly 'an order-N chain decays with hops'."""
    return float(hop) ** max(1, int(order))


def grounded_confidence() -> float:
    """A directly stored, directly read grounded fact = full confidence."""
    return 1.0


def band(confidence: float, has_candidate: bool = True) -> str:
    """Map a confidence to its band. With NO candidate -> INADMISSIBLE
    (the categorical no, regardless of number). Otherwise HIGH/MID/LOW."""
    if not has_candidate or confidence <= 0.0:
        return "INADMISSIBLE"
    if confidence >= BAND_HIGH:
        return "HIGH"
    if confidence >= BAND_MID:
        return "MID"
    return "LOW"


# ---------------------------------------------------------------------------
# The abstract-shape sources — read graph-resident RolePrior + KnownFact data.
# ---------------------------------------------------------------------------

def _nodes_with_attr(s, node_type: str, key: str, value: Any) -> list[Any]:
    """Find nodes of `node_type` whose attr `key` == `value`. Tries the indexed
    nodes_where first, but FALLS BACK to a full scan when the index is absent or
    returns empty (nodes_where returns [] for an undeclared index — it does not
    scan), so the read is correct whether or not the index was declared."""
    try:
        hit = s.nodes_where(node_type, key, value)
    except Exception:
        hit = []
    if hit:
        return list(hit)
    return [n for n in s.nodes(node_type)
            if s.node(n)["attrs"].get(key) == value]


def _role_prior(s, slot: str) -> Optional[dict[str, Any]]:
    """The RolePrior node for `slot` (graph data, seeds/conceptual_categories):
    {slot, category, expected_categories, proper_category}. None if absent."""
    rids = _nodes_with_attr(s, "RolePrior", "slot", slot)
    if not rids:
        return None
    return dict(s.node(rids[0])["attrs"])


def _expected_categories(s, slot: str) -> list[str]:
    """The categories a correctly-sensed filler of `slot` may have — straight
    off the RolePrior's expected_categories (the role's selectional prior)."""
    rp = _role_prior(s, slot)
    if not rp:
        return []
    ec = rp.get("expected_categories")
    if isinstance(ec, (list, tuple)):
        return [c for c in ec if isinstance(c, str)]
    cat = rp.get("category")
    return [cat] if isinstance(cat, str) else []


def _concept_category(s, name: str) -> Optional[str]:
    """The `category` attr of the Concept named `name` (animal/person/object/
    event/...), read off the graph. None if the concept is untyped/absent."""
    cids = _nodes_with_attr(s, "Concept", "name", name)
    for c in cids:
        cat = s.node(c)["attrs"].get("category")
        if isinstance(cat, str):
            return cat
    return None


# A readable type-name for a guessed category, used in the "I think it's a X"
# surface. Pure presentation (the category attr is the graph-resident source).
_CATEGORY_GLOSS = {
    "person": "a person", "animal": "an animal", "object": "a thing",
    "location": "a place", "place": "a place", "event": "an event",
}


def _category_gloss(cat: str) -> str:
    return _CATEGORY_GLOSS.get(cat, f"a {cat}")


# ---------------------------------------------------------------------------
# The conjecture generator — when grounded + chain fail, generate shape-guesses
# at epsilon weight from the role's type prior and from analogous facts.
# ---------------------------------------------------------------------------

def conjecture(s, queried_relation: Optional[str], queried_slot: str,
               anchor_entity: Optional[str] = None,
               anchor_slot: Optional[str] = None
               ) -> list[tuple[Any, float, str]]:
    """Generate shape-guesses for a queried slot that NO grounded fact and NO
    order-N chain resolved. Returns [(candidate, weight, basis)] at epsilon
    weight; EMPTY when there is no abstract shape to guess from at all (the
    INADMISSIBLE case -> the caller emits "I don't know").

    Two shape sources, both from the agent's own graph-resident machinery:

      1. ANALOGY (concrete) — same-slot fillers of the SAME relation in OTHER
         KnownFacts, preferring fillers whose Concept category matches the
         slot's expected category. A concrete guess ("maybe Paris, like John").

      2. TYPE / ROLE (abstract) — the slot's expected category from the
         RolePrior. A type-level guess ("I think it's a place"). Always emitted
         when the role has a prior, so a slot the agent UNDERSTANDS the type of
         is never a flat "I don't know".

    INADMISSIBLE = neither fires: no analogous fact AND no role prior (the agent
    has no shape — genuinely nothing to guess from)."""
    out: list[tuple[Any, float, str]] = []
    expected = set(_expected_categories(s, queried_slot))

    # ---- 0. COMMONSENSE (ConceptNet): a CONCRETE guess grounded in a real
    # commonsense relation about the ANCHOR entity, not a bare type prior. A
    # 'location' query about a known dog -> AtLocation house/kennel; an identity
    # query -> IsA animal/canine. Still a CONJECTURE (epsilon weight,
    # basis="conceptnet <Relation>") — ConceptNet is a weighted commonsense
    # PRIOR, crowd-sourced + noisy, NOT ground truth — but now grounded in real
    # commonsense rather than a generic category. Emitted FIRST so a concrete,
    # entity-specific guess leads the generic type gloss. Best-effort: any
    # failure (slab absent / offline) falls through to the existing sources.
    # Fire ONLY for a queried slot that maps to a commonsense relation
    # (location->AtLocation, agent/patient/topic->IsA). A slot with NO commonsense
    # mapping (cause/manner/time/...) does NOT trigger ConceptNet — a 'why' gap is
    # not a commonsense-relation lookup, so it must stay inadmissible-able. (Never
    # default to IsA for an arbitrary slot — that would surface noise like
    # 'Mary IsA female name' for a cause query and break the categorical no.)
    if anchor_entity:
        try:
            from domains import conceptnet_reference as _cn
            relation = _cn.SLOT_RELATION.get(queried_slot)
            if relation is not None:
                for tgt in _cn._targets_for(anchor_entity, relation)[:2]:
                    if tgt in _WH or tgt == anchor_entity:
                        continue
                    basis = (f"conceptnet {relation}: {anchor_entity} "
                             f"{relation} {tgt} (commonsense prior)")
                    out.append((tgt, EPSILON, basis))
        except Exception:
            pass

    # ---- 1. ANALOGY: same-slot fillers of the same relation elsewhere -------
    # Transfer the shape "an X of <relation> is a <category>" from grounded
    # facts that DO fill this slot for this relation. Prefer typed fillers in
    # the slot's expected categories.
    seen_fillers: set[str] = set()
    analog_typed: list[tuple[str, str]] = []     # (filler, basis)
    analog_untyped: list[tuple[str, str]] = []
    for fid in s.nodes("KnownFact"):
        a = s.node(fid)["attrs"]
        if queried_relation and a.get("event") != queried_relation:
            continue
        v = a.get(queried_slot)
        if not isinstance(v, str) or v in _WH or v in seen_fillers:
            continue
        if anchor_entity is not None and v == anchor_entity:
            continue
        seen_fillers.add(v)
        # Who fills this fact's anchor slot (the entity the analogue is about)?
        other = a.get(anchor_slot) if anchor_slot else None
        rel = a.get("event", queried_relation or "?")
        cat = _concept_category(s, v)
        basis = (f"analogy: {rel}({other}) -> {queried_slot}={v}"
                 if isinstance(other, str)
                 else f"analogy: another {rel} has {queried_slot}={v}")
        if cat in expected or not expected:
            analog_typed.append((v, basis + (f" ({cat})" if cat else "")))
        else:
            analog_untyped.append((v, basis + f" ({cat})"))
    # Emit at most a couple of concrete analogues (typed first), at epsilon.
    for v, basis in (analog_typed + analog_untyped)[:2]:
        out.append((v, EPSILON, basis))

    # ---- 2. TYPE / ROLE: the slot's expected category (abstract guess) ------
    if expected:
        # Prefer the role's single best category (its `category` attr) for the
        # gloss; fall back to the first expected.
        rp = _role_prior(s, queried_slot) or {}
        head_cat = rp.get("category")
        if not isinstance(head_cat, str) or head_cat not in expected:
            head_cat = sorted(expected)[0]
        gloss = _category_gloss(head_cat)
        basis = (f"type/role prior: a {queried_slot} is "
                 f"{'/'.join(sorted(expected))} (RolePrior)")
        out.append((gloss, EPSILON, basis))

    return out


# ---------------------------------------------------------------------------
# Order-N WITH a conjectured fallback hop — the weight enters the calculation.
# ---------------------------------------------------------------------------

def reason_with_conjecture(
        s, anchor_entity: str, queried_relation: str, queried_slot: str,
        anchor_slot: str = "agent", max_order: int = 4
) -> Optional[dict[str, Any]]:
    """Order-N inference that, when the all-grounded chain misses, tries to
    COMPLETE a partial chain with ONE conjectured final hop at epsilon — so a
    chain that grounds part-way (e.g. Mary -> John, but live(John,?) unknown)
    returns an answer at REDUCED confidence instead of failing.

    Returns a resolution dict with `confidence` set, or None if not even a
    partial chain reaches a conjecturable final hop. The conjectured-hop
    confidence = product(grounded_hops) * EPSILON — the conjecture weight
    PARTICIPATING in the chain calculus, exactly as required.

    HONEST: this is only reached AFTER the pure-grounded onr.reason has missed;
    the returned answer is explicitly flagged conjectured=True and carries its
    basis."""
    # Walk grounded chains up to max_order-1 (leave one hop for the conjecture),
    # find a chain that reaches an entity which COULD fill the queried relation,
    # then conjecture that final fact at epsilon.
    seeds = list(s.nodes("KnownFact"))
    if not seeds:
        return None
    for order in range(1, max_order):
        chains = onr.chain_to_order(s, seeds, order)
        if not chains:
            break
        for p in chains:
            first = onr._fact_attrs(s, p.facts[0])
            if anchor_slot and first.get(anchor_slot) != anchor_entity:
                continue
            if anchor_entity not in onr._entities(first):
                continue
            # The entity reached at the end of this grounded prefix.
            last = onr._fact_attrs(s, p.facts[-1])
            reached_entity = None
            for r in onr._ROLE_SLOTS:
                v = last.get(r)
                if isinstance(v, str) and v not in _WH and v != anchor_entity:
                    reached_entity = v
            if reached_entity is None:
                continue
            # Conjecture the final hop: queried_relation(reached_entity, ?slot).
            cands = conjecture(s, queried_relation, queried_slot,
                               anchor_entity=reached_entity,
                               anchor_slot="agent")
            if not cands:
                continue
            cand, w, basis = cands[0]
            grounded_conf = chain_confidence(p.order)
            conf = grounded_conf * w
            chain_str = " ⇒ ".join(onr._fact_str(s, f) for f in p.facts)
            chain_str += (f" ⇒ ⟨conjecture⟩ {queried_relation}"
                          f"({reached_entity}, {queried_slot}≈{cand})")
            return {
                "answer": cand,
                "queried_slot": queried_slot,
                "queried_relation": queried_relation,
                "order": p.order + 1,
                "grounded_order": p.order,
                "confidence": conf,
                "conjectured": True,
                "basis": (f"{p.order} grounded hop(s) to {reached_entity}, "
                          f"then {basis}"),
                "chain_str": chain_str,
                "facts": list(p.facts),
            }
    return None


# ---------------------------------------------------------------------------
# The graded ANSWER — the single entry point conversation_world calls. Tries
# grounded -> chain -> conjecture, attaching a confidence + band + basis.
# ---------------------------------------------------------------------------

def answer(s, anchor_entity: Optional[str], queried_relation: Optional[str],
           queried_slot: str, anchor_slot: Optional[str] = "agent",
           grounded: Optional[dict[str, Any]] = None,
           record: bool = True) -> dict[str, Any]:
    """The graded answer calculus. Returns a dict with at least:
        {answer, confidence, band, conjectured, basis, source}
    where source ∈ {grounded, chain, conjecture, inadmissible}.

    Order of escalation (each weaker than the last):
      1. grounded single fact      (caller passes it in)   conf 1.0   HIGH
      2. order-N grounded chain    (onr.reason)            product    HIGH/MID
      3. partial chain + conjecture (reason_with_conjecture) prod*eps  LOW
      4. pure conjecture           (conjecture)            epsilon    LOW
      5. nothing                   -> INADMISSIBLE                     "I don't know"

    INADMISSIBLE fires ONLY at step 5 — no grounded fact, no chain, no shape."""
    # 1. grounded fact supplied by the caller (single-hop match).
    if grounded is not None:
        conf = grounded_confidence()
        return {**grounded, "confidence": conf, "band": band(conf),
                "conjectured": False, "basis": "grounded fact (single hop)",
                "source": "grounded"}

    # 2. order-N grounded chain.
    if anchor_entity and queried_relation:
        res = onr.reason(s, anchor_entity=anchor_entity,
                         queried_relation=queried_relation,
                         queried_slot=queried_slot, anchor_slot=anchor_slot or "agent",
                         record=record)
        if res is not None:
            conf = chain_confidence(res["order"])
            return {**res, "confidence": conf, "band": band(conf),
                    "conjectured": False,
                    "basis": f"order-{res['order']} grounded chain",
                    "source": "chain"}

        # 3. partial grounded chain completed by one conjectured hop.
        res = reason_with_conjecture(
            s, anchor_entity=anchor_entity, queried_relation=queried_relation,
            queried_slot=queried_slot, anchor_slot=anchor_slot or "agent")
        if res is not None:
            res["band"] = band(res["confidence"])
            res["source"] = "conjecture"
            return res

    # 4. pure conjecture from the abstract shape (type/role + analogy).
    cands = conjecture(s, queried_relation, queried_slot,
                       anchor_entity=anchor_entity, anchor_slot=anchor_slot)
    if cands:
        cand, w, basis = cands[0]
        return {"answer": cand, "queried_slot": queried_slot,
                "queried_relation": queried_relation or "",
                "confidence": w, "band": band(w), "conjectured": True,
                "basis": basis, "source": "conjecture",
                "alternatives": cands}

    # 5. INADMISSIBLE — no grounded fact, no chain, no shape. The categorical no.
    return {"answer": None, "queried_slot": queried_slot,
            "queried_relation": queried_relation or "",
            "confidence": 0.0, "band": "INADMISSIBLE", "conjectured": False,
            "basis": "no grounded fact, no chain, no abstract shape "
                     "(inadmissible — nothing to guess from)",
            "source": "inadmissible"}


# ---------------------------------------------------------------------------
# Graded REPLY FORM — load + read the held epistemic markers (graph data).
# ---------------------------------------------------------------------------

def load_epistemic_markers(s) -> int:
    """Load seeds/epistemic_markers.json (band -> surface marker per language)
    into the substrate as EpistemicMarker nodes. Idempotent against an already-
    loaded (band, language) pair. Returns the count added. Mechanical seed
    install (same idiom as _load_category_seed)."""
    seed_path = (Path(__file__).resolve().parent.parent
                 / "seeds" / "epistemic_markers.json")
    if not seed_path.exists():
        return 0
    with seed_path.open() as f:
        manifest = json.load(f)
    existing: set[tuple[str, str]] = set()
    for nid in s.nodes("EpistemicMarker"):
        a = s.node(nid)["attrs"]
        existing.add((a.get("band"), a.get("language")))
    added = 0
    for entry in manifest.get("nodes", []):
        if entry.get("type") != "EpistemicMarker":
            continue
        attrs = dict(entry.get("attrs", {}))
        key = (attrs.get("band"), attrs.get("language"))
        if key in existing:
            continue
        try:
            s.add_node("EpistemicMarker", attrs)
            existing.add(key)
            added += 1
        except Exception:
            pass
    return added


def marker_prefix(s, band_name: str, language: str = "en"
                  ) -> tuple[str, Optional[str]]:
    """Read the EpistemicMarker for (band, language) off the graph and return
    (prefix, concept_realised). Empty prefix for HIGH (bare assertion) / when no
    marker is present. Pure graph read — no decision."""
    cands = _nodes_with_attr(s, "EpistemicMarker", "band", band_name)
    fallback: Optional[Any] = None
    for nid in cands:
        a = s.node(nid)["attrs"]
        if a.get("language") == language:
            return a.get("prefix", "") or "", a.get("concept")
        if a.get("language") == "en":
            fallback = nid
    if fallback is not None:
        a = s.node(fallback)["attrs"]
        return a.get("prefix", "") or "", a.get("concept")
    return "", None


def hedge(s, utterance: str, band_name: str, language: str = "en") -> str:
    """Wrap a produced utterance with its band's held-epistemic marker. HIGH ->
    bare; MID -> 'Probably, X'; LOW -> 'I think it's like X'. The marker surface
    is read from the graph (EpistemicMarker nodes), not hardcoded."""
    prefix, _concept = marker_prefix(s, band_name, language)
    if not prefix:
        return utterance
    body = utterance[0].lower() + utterance[1:] if utterance else utterance
    sep = "" if prefix.endswith(("～",)) else " "
    return f"{prefix}{sep}{body}"


# ---------------------------------------------------------------------------
# Record a conjecture as graph data — inspectable, like a ReasoningChain.
# ---------------------------------------------------------------------------

def record_conjecture(s, res: dict[str, Any]):
    """Mint a Conjecture node carrying the guessed answer + its weight + basis +
    band. Returns the node id. Best-effort (the same idiom order_n_reasoning
    uses for its ReasoningChain trace)."""
    try:
        cid = s.add_node("Conjecture", {
            "answer": "" if res.get("answer") is None else str(res["answer"]),
            "confidence": float(res.get("confidence", 0.0)),
            "weight": float(res.get("confidence", 0.0)),
            "band": res.get("band", ""),
            "queried_slot": res.get("queried_slot", ""),
            "queried_relation": res.get("queried_relation", ""),
            "basis": res.get("basis", ""),
            "conjectured": bool(res.get("conjectured", False)),
            "source": res.get("source", ""),
            "origin": "conjecture",
            "composed_by": "agent",
        })
        return cid
    except Exception:
        return None


__all__ = ["GROUNDED_HOP", "EPSILON", "BAND_HIGH", "BAND_MID",
           "chain_confidence", "grounded_confidence", "band",
           "conjecture", "reason_with_conjecture", "answer",
           "load_epistemic_markers", "marker_prefix", "hedge",
           "record_conjecture"]
