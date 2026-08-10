"""narrative_structure — THE STORY-GRAMMAR ARC, ONE LEVEL UP FROM COHERENCE.

`discourse_coherence` decodes the RELATION between two adjacent spans
(elaboration/contrast/cause/sequence/condition) by ShapeDecode over a
dedicated `ShapeSignatureCoherence` codebook. `reading_collapse` decodes a
CLAUSE's CONSTRUCTION the same way, one level further down. This module is
the construction ONE LEVEL UP from discourse: the story-grammar arc
(Rumelhart / Mandler & Johnson: SETTING -> GOAL -> ATTEMPT -> OUTCOME;
Trabasso & van den Broek's causal network read as narrative FUNCTION rather
than bare centrality) recognised over the comprehension graph
`comprehension_reader.read_and_comprehend` already built.

Nothing here re-derives meaning the six comprehension components already
decided. Every input is a graph fact some other component's own collapse
already committed:

  · the GOAL and its remedy — `inference_generation.resolve_goal_gap`'s own
    decode (goal-from-state: thirsty -> drink), read off the goal record
    `comprehension_reader.read_and_comprehend` already produced;
  · the GOAL -> ATTEMPT -> ATTEMPT backbone (which sentence stated the need,
    which later sentences the same entity acts in, in text order) —
    `comprehension_reader._mint_goal_action_enabling_chain`'s own mechanical
    scan, reused verbatim, never re-derived;
  · the COMPLICATION signal — `discourse_coherence.read_discourse`'s own
    decoded coherence relation ('contrast') INTO an attempt sentence (the
    textual "But..." that sets a complication against the just-stated goal);
  · the CAUSAL-HINGE signal — an attempt sentence's own OUTGOING `causes`
    edge (minted by `inference_generation.resolve_causal_gap`'s physical-
    effect decode, or by `discourse_coherence`'s own marked/unmarked cause
    decode) toward a later sentence;
  · the OUTCOME signal — whether a causal-chain effect sentence's own
    recognised words (`comprehend_text._recognise_words`, no regex) include
    the goal's own remedy token.

EACH of those four facts is turned into ONE TOKEN per narrative "slot" (the
goal sentence, then each of the goal-holder's own action-chain sentences, in
order) — the SAME "mechanical signal -> single-token skeleton" shape
`discourse_coherence._unmarked_signal` already uses to build ITS decode
input. The token is then decoded by `ShapeDecode` against a dedicated
`ShapeSignatureNarrative` codebook (`seeds/narrative_structure.json`, its OWN
codebook_type -- kept separate from both the clause-construction and the
coherence-relation pools, the same separation `discourse_coherence` already
established relative to `reading_collapse`). The WINNING schema's own `role`
attr (setup / problem / solution / action / consequence / resolution) is
the story-grammar role — read off the decode's own verdict via
`reading_collapse._winner` (reused, not reimplemented), never assigned by a
Python if/else naming the role directly. A slot whose token no schema covers
mints NOTHING (an honest, discriminative null — a wolf's plain "attempt" and
a goalless event list both leave roles unassigned rather than fabricated).

Each recognised role is minted as a `NarrativeRole` node (a graph node
tagging the underlying `DiscourseEvent`'s function in the arc) plus a
`has_narrative_role` edge from that event — reusing
`discourse_coherence._mint_edge` verbatim for the write, the SAME
admissibility-gated idiom the rest of the reading stack uses.

ARCHITECTURE (CLAUDE.md). The decision that carries content — WHICH role a
sentence plays in the arc — is the `ShapeDecode` collapse's own verdict, read
off its `plan`/`shape_fit` via the held `reading_collapse._winner` (reused).
This module only (a) reads already-committed graph facts (the goal record,
the enabling chain, the discourse-coherence pairs, the causal edges, the
recognised words of a sentence) — mechanical, no new meaning decided; (b)
builds the SIGNAL TOKEN from those facts, exactly the shape
`discourse_coherence._unmarked_signal` already uses (an existence check, not
a role assignment); (c) mints the resulting `NarrativeRole` node/edge
(mechanical graph I/O). No `if`/`else` anywhere in this module compares
against a role string ("setup"/"problem"/"solution"/...) or returns one —
every role string used by a caller comes from the seed's own `role` attr,
read back through `_role_for`. No `import re`; donkey = 0.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import discourse_coherence as dc
from domains import reading_collapse as rc
from domains import situation_model_reader as smr

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CODEBOOK_SEED = os.path.join(_ROOT, "seeds", "narrative_structure.json")
_CODEBOOK_TYPE = "ShapeSignatureNarrative"


# --------------------------------------------------------------------------- #
#  resolution + codebook install (mechanical adapter I/O — no decision).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def ensure_codebook(agent) -> None:
    """Idempotently install the narrative-structure codebook (`ShapeSignature
    Narrative` nodes) plus its dependency (`coherence_relations`, for the
    discourse-pairs mechanism the complication/solution signals read).
    Guarded by a graph-resident `Seed{id:'narrative_structure'}` sentinel —
    the SAME idempotency idiom `discourse_coherence.ensure_codebook` uses.
    Mechanical seed I/O."""
    sub, native, ag_node = _resolve(agent)
    dc.ensure_codebook(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "narrative_structure":
            return
    with open(_CODEBOOK_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "narrative_structure", "version": manifest.get("version", "1.0.0")})


# --------------------------------------------------------------------------- #
#  DECODE — a thin ShapeDecode shim pointed at the narrative codebook_type,
#  kept SEPARATE from both reading_collapse's clause-construction pool and
#  discourse_coherence's coherence-relation pool (mirrors dc._decode exactly).
# --------------------------------------------------------------------------- #
def _decode(agent, skeleton: list) -> dict:
    _, native, _ = _resolve(agent)
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": [list(x) for x in (skeleton or [])]},
            "codebook_type": _CODEBOOK_TYPE, "beam": 1, "max_steps": 1, "cand_k": 4}
    res = native.evaluate(term)
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(skeleton or []), "ordered_parts": []}
    return res


def _role_for(agent, name: str) -> Optional[str]:
    sub, _, _ = _resolve(agent)
    for n in sub.nodes(_CODEBOOK_TYPE):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return at.get("role")
    return None


def decode_slot(agent, token: str) -> dict:
    """Decode ONE narrative slot's token against the codebook. Returns
    {token, construction, role, shape_fit}. WHICH role is the decode's own
    verdict (`reading_collapse._winner`, reused) — this only builds the
    one-element skeleton and reads the winner's `role` attr back."""
    ensure_codebook(agent)
    res = _decode(agent, [[token]])
    name, fit = rc._winner(res)
    role = _role_for(agent, name) if (name is not None and fit > 0) else None
    return {"token": token, "construction": name, "role": role, "shape_fit": max(fit, 0)}


# --------------------------------------------------------------------------- #
#  MECHANICAL SIGNALS — each an EXISTENCE check over already-committed graph
#  facts (the same shape discourse_coherence._unmarked_signal already uses).
#  These build the TOKEN; they never assign a story-grammar ROLE.
# --------------------------------------------------------------------------- #
def _node_by_order(sub, order: int, unit=None):
    for n in sub.nodes("DiscourseEvent"):
        at = sub.node(n)["attrs"]
        if at.get("order") == order and (unit is None or at.get("unit") == unit):
            return n
    return None


def _incoming_contrast(discourse_pairs: list, idx: int) -> bool:
    return any(p.get("relation") == "contrast" and p.get("j") == idx for p in discourse_pairs)


def _outgoing_causal_targets(sub, idx: int) -> list:
    node = _node_by_order(sub, idx)
    if node is None:
        return []
    targets = []
    for nb in sub.neighbours(node, "causes"):
        at = sub.node(nb)["attrs"]
        order = at.get("order")
        if order is not None:
            targets.append(int(order))
    return targets


def _mentions_remedy(agent, sub, idx: int, remedy: Optional[str]) -> bool:
    """Does DiscourseEvent(idx)'s own recognised-word set include the goal's
    remedy token (lemma-matched via the held WordNet morphy,
    `situation_model_reader._lemma` — the SAME lemmatiser `cos_membership`
    uses)? No regex, no substring heuristic."""
    if not remedy:
        return False
    node = _node_by_order(sub, idx)
    if node is None:
        return False
    text = sub.node(node)["attrs"].get("text") or ""
    words = ct._recognise_words(agent, text)
    remedy_lemma = smr._lemma(str(remedy))
    return any(smr._lemma(w) == remedy_lemma for w in words)


def _slot_token(sub, discourse_pairs: list, idx: int) -> tuple:
    """The token for ONE action-chain slot: which mechanical signal fires,
    read off already-committed facts. Mirrors `discourse_coherence.
    _unmarked_signal`'s own shape exactly (an existence-check ladder building
    a TOKEN, never the final role)."""
    if _incoming_contrast(discourse_pairs, idx):
        return ("NARR_CONTRAST", "incoming discourse_coherence relation "
                "'contrast' into sentence %d -- a complication set against "
                "the just-stated goal" % idx)
    if _outgoing_causal_targets(sub, idx):
        return ("NARR_CAUSAL", "sentence %d carries an outgoing 'causes' "
                "edge toward a later sentence" % idx)
    return ("NARR_ATTEMPT", "sentence %d carries neither an incoming "
            "contrast nor an outgoing causal edge -- a bare goal-pursuit "
            "attempt" % idx)


def _effect_token(agent, sub, idx: int, remedy: Optional[str]) -> tuple:
    if _mentions_remedy(agent, sub, idx, remedy):
        return ("NARR_GOAL_MET", "sentence %d's recognised words include "
                "the goal's remedy token %r -- the goal is achieved" % (idx, remedy))
    return ("NARR_EFFECT", "sentence %d is a causal consequence of the "
            "solution attempt, but its recognised words do not include the "
            "goal's remedy token %r" % (idx, remedy))


# --------------------------------------------------------------------------- #
#  MINT — a recognised role becomes a `NarrativeRole` node + `has_narrative_
#  role` edge from the DiscourseEvent it tags. Mechanical graph write, reusing
#  discourse_coherence._mint_edge verbatim (the same admissibility-gated
#  write idiom the rest of the reading stack uses).
# --------------------------------------------------------------------------- #
def _existing_role(sub, entity: str, order: int, role: str, unit=None):
    for n in sub.nodes("NarrativeRole"):
        at = sub.node(n)["attrs"]
        if at.get("entity") == entity and at.get("order") == order and at.get("role") == role \
                and (unit is None or at.get("unit") == unit):
            return n
    return None


def _mint_slot(agent, sub, native, node, entity: str, order: int, token: str, note: str,
               unit=None) -> dict:
    dec = decode_slot(agent, token)
    role = dec["role"]
    if role is None:
        return {"order": order, "token": token, "role": None, "note": note,
                "minted": False, "reason": "no ShapeSignatureNarrative schema "
                "covers token %r -- honest null, nothing fabricated" % token}
    existing = _existing_role(sub, entity, order, role, unit)
    if existing is not None:
        return {"order": order, "token": token, "role": role, "note": note,
                "minted": False, "reason": "already held", "node": _v(existing)}
    rn_attrs = {"entity": entity, "order": order, "role": role,
                "token": token, "schema": dec["construction"], "note": note}
    if unit is not None:
        rn_attrs["unit"] = unit
    rn = sub.add_node("NarrativeRole", rn_attrs)
    dc._mint_edge(sub, native, node, rn, "has_narrative_role", {"role": role})
    return {"order": order, "token": token, "role": role, "schema": dec["construction"],
            "note": note, "minted": True, "node": _v(rn)}


# --------------------------------------------------------------------------- #
#  THE DRIVER — recognise the arc over an already-built comprehension graph.
# --------------------------------------------------------------------------- #
def recognize_narrative_structure(agent, graph: dict, unit=None) -> dict:
    """Recognise the story-grammar arc over the comprehension graph
    `comprehension_reader.read_and_comprehend` already built. `graph` is
    (a slice of) that function's own return dict — `goal`, `enabling_chain`,
    `discourse` (with its `pairs`) — every one of those already decided by
    the six comprehension components' own collapses; this function derives
    no new meaning, only recognises which story-grammar role each
    already-placed event plays and mints the corresponding `NarrativeRole`.

    Returns {arcs: [{entity, goal_sentence, remedy, roles: [...]}]} — one arc
    per character carrying a MINTED goal (an entity with no goal contributes
    no arc at all: the honest, discriminative null for a non-narrative event
    list)."""
    ensure_codebook(agent)
    sub, native, _ = _resolve(agent)
    discourse_pairs = (graph.get("discourse") or {}).get("pairs") or []

    goal_by_entity: dict[str, dict] = {}
    for g in graph.get("goal") or []:
        if g.get("minted"):
            goal_by_entity[g["gap"]["entity"]] = g

    arcs = []
    for chain in graph.get("enabling_chain") or []:
        entity = chain.get("entity")
        g = goal_by_entity.get(entity)
        remedy = (g.get("supplies") or {}).get("remedy") if g else None
        goal_idx = chain.get("goal_sentence")
        roles: list = []

        if goal_idx is not None:
            gnode = _node_by_order(sub, goal_idx, unit)
            if gnode is not None:
                roles.append(_mint_slot(agent, sub, native, gnode, entity, goal_idx,
                                        "NARR_GOAL", "goal-establishing sentence -- "
                                        "already minted by inference_generation."
                                        "resolve_goal_gap", unit))

        minted_effects: set = set()
        for idx in chain.get("action_sentences") or []:
            anode = _node_by_order(sub, idx, unit)
            if anode is None:
                continue
            token, note = _slot_token(sub, discourse_pairs, idx)
            roles.append(_mint_slot(agent, sub, native, anode, entity, idx, token, note, unit))
            if token == "NARR_CAUSAL":
                for eff_idx in _outgoing_causal_targets(sub, idx):
                    if eff_idx in minted_effects:
                        continue
                    enode = _node_by_order(sub, eff_idx, unit)
                    if enode is None:
                        continue
                    minted_effects.add(eff_idx)
                    etoken, enote = _effect_token(agent, sub, eff_idx, remedy)
                    roles.append(_mint_slot(agent, sub, native, enode, entity, eff_idx,
                                            etoken, enote, unit))

        arcs.append({"entity": entity, "goal_sentence": goal_idx, "remedy": remedy,
                    "roles": roles})
    return {"arcs": arcs}


# --------------------------------------------------------------------------- #
#  READ BACK — plain graph query (no decision), for callers/gates/demos.
# --------------------------------------------------------------------------- #
def read_narrative_roles(agent, entity: Optional[str] = None, unit=None) -> list:
    """Every resident `NarrativeRole` node's attrs, sorted by (entity, order).
    A pure graph read for a caller to print or assert against. UNIT-SCOPED
    (MOVE 2b): when `unit` is given, only that StoryUnit's roles are returned."""
    sub, _, _ = _resolve(agent)
    out = []
    for n in sub.nodes("NarrativeRole"):
        at = dict(sub.node(n)["attrs"])
        if entity is not None and at.get("entity") != entity:
            continue
        if unit is not None and at.get("unit") != unit:
            continue
        out.append(at)
    out.sort(key=lambda r: (str(r.get("entity") or ""),
                            r.get("order") if r.get("order") is not None else -1))
    return out


# --------------------------------------------------------------------------- #
#  THE ARC-ROLE PROTAGONIST — WHO THE STORY IS ABOUT, not who is named most.
#
#  The QA/roster read-off ranks characters by MENTION COUNT (frequency), so on
#  'The Travelling Musicians' it names robbers(x5)/mistress(x4) over the four
#  animal MUSICIANS who DRIVE the tale. The protagonist is not the most-frequent
#  entity — it is the AGENT of the narrative ARC: the entity whose agency runs
#  ACROSS the arc (setup -> conflict -> resolution). A bystander acts in ONE
#  scene (a tight band of the arc); the protagonist acts THROUGHOUT it.
#
#  This is a graph computation over the arc's agent structure, NOT a Python
#  frequency-max and NOT an LLM. The decision is ONE `Argmax` Term over the
#  resident character pool (the SAME graph-native discipline `discourse_
#  coherence.most_central` / `coref_entities.antecedent_argmax_term` use — the
#  DSL evaluator picks the winner, Python never calls `max()`/`sorted()` for the
#  decision). The score is composed from already-committed graph facts:
#
#    ARC-AGENCY   = Count(InNeighbours(e, "agent")) -- the number of eventive
#                   SmEvents `e` is the AGENT of (situation_model_reader mints an
#                   `agent` edge SmEvent -> SmEntity for every eventive
#                   predication; a STATIVE verb mints none -- the discriminative
#                   null). This is agency, not mention count.
#    ARC-SPAN     = MaxOver(agent-events, t) + MaxOver(agent-events, -t)
#                 = max_t - min_t -- the ARC-CENTRALITY weight: how much of the
#                   narrative arc (first-to-last acted-in event time) the entity
#                   spans. An actor through the whole arc has a WIDE span; a
#                   single-scene bystander a span of ~0. This is what separates
#                   the protagonist from a frequently-named-but-local bystander.
#
#  The composite score is span-dominant, then agency, then (only as a genuine-tie
#  breaker, well below both arc terms) salience (coref_mentions) -- so frequency
#  NEVER decides a protagonist that arc-agency can separate; it only breaks a
#  dead heat where every candidate acts in exactly one instant (e.g. a tale whose
#  every character has a single logged action). The pool is the CLEAN, CATEGORISED
#  character set (coref_category in {animal, person} AND coref_cleanliness == 1.0)
#  -- a graph `Filter`, so unresolved pronouns ('he'/'she') and parse-glom junk
#  are excluded by their own graph attrs, not by Python.
# --------------------------------------------------------------------------- #
def _V(n):
    return {"type": "Var", "name": n}


def _Lit(v):
    return {"type": "Lit", "value": v}


def _Attr(node, k):
    return {"type": "Attr", "node": node, "key": k}


def _Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def _Or(items):
    return {"type": "Or", "items": items}


def _And(items):
    return {"type": "And", "items": items}


def _Plus(items):
    return {"type": "Plus", "items": items}


def _Times(items):
    return {"type": "Times", "items": items}


def _Neg(a):
    return {"type": "Neg", "arg": a}


def _InNeighbours(node, edge_type):
    return {"type": "InNeighbours", "node": node, "edge_type": edge_type, "any_type": False}


def _Count(src):
    return {"type": "Count", "source": src}


def _MaxOver(src, var, val):
    return {"type": "MaxOver", "source": src, "var_name": var, "value": val,
            "default": _Lit(0.0)}


def _Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


def _Argmax(src, var, val):
    return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": None}


def _NodesOfType(t):
    return {"type": "NodesOfType", "node_type": t}


# span dominates agency dominates (only as a tie-breaker) salience. Times are
# per-predication turn counts (up to ~a few hundred), agency a small integer,
# mentions a small integer -- so W_SPAN * 1 outweighs any realistic agency, and
# W_AGENCY * 1 outweighs any realistic mention count. The arc decides; salience
# only breaks an exact arc tie.
_W_SPAN = 10_000.0
_W_AGENCY = 100.0


def _Not(a):
    return {"type": "Not", "arg": a}


def _is_function_word(name: str) -> bool:
    """Is `name`'s head a CLOSED-CLASS function word (a pronoun / determiner —
    'i'/'him'/'myself'/'you'/'we'/'it')? Read off the held closed-class lexicon
    (`function_word_reference.classify` — the SAME faculty consumption_quality.
    _function_of consults), a mechanical lexical lookup, NOT a hand-authored stop
    list and NOT a decision over graph state. A content noun (crow/dog/sparrow/
    robbers) classifies None. This is the reason the un-grounded `unknown` category
    can be admitted to the character pool WITHOUT admitting first/second-person
    pronoun surfaces that also grounded `unknown` + clean (WordNet reads 'i' as a
    nominal — iodine): the pronoun is filtered by its closed-class lexical status,
    the honest signal, while a proper-named character ('Crow') is kept."""
    from domains import function_word_reference as fw
    head = str(name).split("_")[-1]
    try:
        return bool((fw.classify(head, "en") or {}).get("function"))
    except Exception:
        return False


def _is_nonnominal(name: str) -> bool:
    """Is `name`'s head an OPEN-CLASS NON-NOMINAL — a predicative adjective / verb /
    adverb ('asleep', 'bolder', 'quiet', 'see', 'out') rather than a noun/name? A
    CHARACTER is a NOMINAL referent; a property value or a predicate that a mis-parse
    deposited into an argument slot is NOT a character and must not be admitted to the
    resonance pool (where it would draw spurious agency and win the arc-role Argmax).

    Read off the SAME held POS faculty the reader uses (reading_collapse._primary_pos
    -> consumption_quality._pos) — a mechanical lexical lookup, NOT a decision over
    graph state, the same admissible status as `_is_function_word` reading the
    closed-class lexicon. Every real character (dog / cat / cock / ass / wolf /
    robbers / carter / sparrow / crow / sultan / ...) is noun- or name-primary and is
    KEPT; an adjective/verb/adverb-primary surface is dropped. An OOV surface (no
    primary POS) is KEPT (a proper name WordNet cannot ground stays a candidate)."""
    from domains import reading_collapse as rc
    head = str(name).split("_")[-1]
    try:
        p = rc._primary_pos(head)
    except Exception:
        return False
    # ADJECTIVE- or ADVERB-primary only: a predicative property ('asleep', 'bolder',
    # 'quiet', 'mad', 'great', 'out') is not a character. VERB-primary is NOT excluded
    # — many real animate nouns tag verb-primary in the coarse POS faculty ('crowd',
    # 'hero', 'see'->the Holy See), and a mis-parsed verb in an argument slot is denied
    # entity status upstream (the complementizer / REL-thread parse fixes), not here.
    return p in ("adj", "adv")


def _character_pool(agent, unit=None) -> dict:
    """The CLEAN, ANIMATE character set as a graph `Filter`: every resident
    SmEntity whose coref_category is animal / person / unknown (an animate
    character, INCLUDING a proper-named one WordNet could not ground — 'Crow',
    'Sultan' — but NOT an inanimate `object`), whose coref_cleanliness is 1.0
    (a groundable nominal, not a parse glom), AND whose name is not a closed-class
    function word (an unresolved pronoun 'i'/'him'/'it' that grounded unknown+clean
    is excluded by its lexical status, not by Python picking a winner). UNIT-SCOPED
    when `unit` is given (order-N isolation), mirroring coref_entities.candidate_term.
    This is the resonance pool the protagonist Argmax ranges over.

    The function-word exclusion is built by a MECHANICAL scan of the resident
    SmEntity names against the closed-class lexicon (`_is_function_word`) that emits
    a `Not(Eq(name, form))` guard per excluded form — the DECISION stays the Argmax
    over this pool; the pool CONSTRUCTION only reads a closed-class lexicon, the same
    admissible status as coref_entities reading `_PRONOUNS`."""
    sub, _, _ = _resolve(agent)
    conds = [
        _Or([_Eq(_Attr(_V("e"), "coref_category"), _Lit("animal")),
             _Eq(_Attr(_V("e"), "coref_category"), _Lit("person")),
             _Eq(_Attr(_V("e"), "coref_category"), _Lit("unknown"))]),
        _Eq(_Attr(_V("e"), "coref_cleanliness"), _Lit(1.0)),
    ]
    excluded = set()
    for n in sub.nodes("SmEntity"):
        nm = sub.node(n)["attrs"].get("name")
        if isinstance(nm, str) and nm and (_is_function_word(nm) or _is_nonnominal(nm)):
            excluded.add(nm)
    for form in sorted(excluded):
        conds.append(_Not(_Eq(_Attr(_V("e"), "name"), _Lit(form))))
    if unit is not None:
        conds.append(_Eq(_Attr(_V("e"), "unit"), _Lit(unit)))
    return _Filter(_NodesOfType("SmEntity"), "e", _And(conds))


def _arc_span_term(var: str) -> dict:
    """ARC-SPAN(e) = max_t - min_t over the SmEvents e is the AGENT of, as one
    Term: MaxOver(t) + MaxOver(-t). For a single-scene agent both extrema are the
    same instant -> span 0; for an agent acting across the arc the span is wide.
    (min_t = -MaxOver(-t), so max_t - min_t = MaxOver(t) + MaxOver(-t).)"""
    src = _InNeighbours(_V(var), "agent")
    max_t = _MaxOver(src, "ev", _Attr(_V("ev"), "t"))
    neg_min_t = _MaxOver(src, "ev", _Neg(_Attr(_V("ev"), "t")))
    return _Plus([max_t, neg_min_t])


def _agency_term(var: str) -> dict:
    """ARC-AGENCY(e) = the number of eventive SmEvents e is the AGENT of —
    Count(InNeighbours(e, 'agent')). Agency, not mention count."""
    return _Count(_InNeighbours(_V(var), "agent"))


def _protagonist_score_term(var: str) -> dict:
    """The composite protagonist score, span-dominant then agency then salience —
    ONE Term the Argmax maximises (the SAME Count/MaxOver/Times/Plus idiom
    discourse_coherence._degree_term composes). No Python arithmetic decides it."""
    return _Plus([
        _Times([_Lit(_W_SPAN), _arc_span_term(var)]),
        _Times([_Lit(_W_AGENCY), _agency_term(var)]),
        _Attr(_V(var), "coref_mentions"),
    ])


def protagonist_by_arc_agency(agent, unit=None) -> dict:
    """WHO THE STORY IS ABOUT — the ARC-ROLE protagonist, decided graph-natively.

    The WINNER is one `Argmax` Term over the clean, categorised character pool,
    scored by ARC-AGENCY weighted by ARC-SPAN (arc-centrality) — the DSL evaluator
    picks it (native Rust), Python never calls `max()`/`sorted()` for the decision.
    The descending `ranking` is Python `sorted()` for DISPLAY ONLY (the SAME
    Argmax-decides/sort-displays precedent discourse_coherence.centrality_ranking
    establishes), verified below to agree with the Argmax pick.

    Returns {protagonist, category, agency, arc_span, score, cohort, ranking,
    argmax_matches_top_of_sort}. `cohort` is the acting co-characters of the
    winner's kind (the GROUP handling: a quartet of animal musicians surfaces as
    the winning lead animal PLUS its acting cohort). An empty pool (no categorised
    character acts) yields protagonist=None — the honest null, never fabricated."""
    sub, native, _ = _resolve(agent)
    pool = _character_pool(agent, unit)
    winner = native.evaluate(_Argmax(pool, "e", _protagonist_score_term("e")), {})
    win_v = _v(winner) if winner is not None else None
    win_name = sub.node(winner)["attrs"].get("name") if winner is not None else None
    win_cat = sub.node(winner)["attrs"].get("coref_category") if winner is not None else None

    # DISPLAY ranking — evaluate the SAME score per pool member (mechanical read).
    members = native.evaluate(pool, {}) or []
    rows = []
    for m in members:
        at = sub.node(m)["attrs"]
        rows.append({
            "name": at.get("name"),
            "category": at.get("coref_category"),
            "agency": int(native.evaluate(_agency_term("e"), {"e": m}) or 0),
            "arc_span": float(native.evaluate(_arc_span_term("e"), {"e": m}) or 0.0),
            "mentions": float(at.get("coref_mentions", 0.0) or 0.0),
            "score": float(native.evaluate(_protagonist_score_term("e"), {"e": m}) or 0.0),
        })
    rows.sort(key=lambda r: -r["score"])   # DISPLAY-ONLY order; the decision was Argmax's.

    win_row = next((r for r in rows if r["name"] == win_name), None)
    # cohort = the acting co-characters of the winner's kind (the GROUP handling:
    # a quartet surfaces as the winning lead PLUS its cohort — 'The Travelling
    # Musicians' names the dog and its co-agents cat/donkey). A DISPLAY hint, not
    # the decision; for a proper-named (`unknown`) winner it also carries the
    # over-segmentation residue of the same category (an honest, documented limit).
    cohort = [r["name"] for r in rows
              if r["category"] == win_cat and r["name"] != win_name and r["agency"] > 0]
    return {
        "protagonist": win_name, "category": win_cat, "node": win_v,
        "agency": (win_row or {}).get("agency"), "arc_span": (win_row or {}).get("arc_span"),
        "score": (win_row or {}).get("score"), "cohort": cohort, "ranking": rows,
        "argmax_matches_top_of_sort": bool(rows) and rows[0]["name"] == win_name,
    }


# --------------------------------------------------------------------------- #
#  THE ARC-ROLE ANTAGONIST — THE OPPOSING AGENCY the protagonist overcomes.
#
#  A story's shape is PROTAGONIST vs ANTAGONIST. `protagonist_by_arc_agency`
#  already names WHO THE STORY IS ABOUT (the arc-agent). The antagonist is the
#  OTHER pole: the entity (EXCLUDING the protagonist) that stands in OPPOSITION
#  to it — the opposing agency the arc's conflict is fought against. On the
#  frequency-named tales this is exactly the entity the arc-role protagonist
#  computation correctly REJECTED as the lead: Travelling Musicians' robbers,
#  Old Sultan's wolf, Dog-and-Sparrow's man — the recurring opposing force.
#
#  Like the protagonist, this is a graph computation over the arc's structure,
#  NOT a Python frequency-max and NOT an LLM: ONE `Argmax` Term over the clean,
#  animate character pool (EXCLUDING the protagonist), scored from the arc's
#  OPPOSITION structure — the same Argmax-decides / sort-displays discipline the
#  protagonist uses. The score is composed from already-committed graph facts:
#
#    OPPOSITION   = Count(Intersect(events(e), events(p))) -- the number of
#                   SmEvents the candidate `e` SHARES with the protagonist `p`
#                   (events(x) = the SmEvents x is agent/theme/goal of, a Union
#                   of three InNeighbours). This is DIRECT opposition-TO-the-
#                   protagonist -- the antagonist engages the protagonist in the
#                   arc's conflict scenes. It is the DOMINANT term (weight 1000):
#                   where coref preserves the interaction (Old Sultan's wolf,
#                   Dog-and-Sparrow's man both share an event with the lead) it
#                   decides the antagonist outright, over any bystander.
#    CONFLICT-TGT = Count(InNeighbours(e, "theme")) -- how often the candidate is
#                   the TARGET/patient of the arc's actions. A recurring object of
#                   conflict (the mouse the cat eats) is opposition even when coref
#                   broke the direct protagonist link. Weight 30.
#    ARC-AGENCY   = Count(InNeighbours(e, "agent")) -- the candidate's own agency:
#                   the antagonist ACTS (conflict recurs from BOTH sides). Weight 3.
#                   On the all-pronoun conflict (Travelling Musicians, where coref
#                   dissolved every dog<->robber edge) this + salience is the ONLY
#                   surviving signal -- the honest limit, reported.
#    SALIENCE     = coref_mentions -- the antagonist RECURS because the conflict
#                   recurs. A raw tiebreak (weight 1), never the decider.
#
#  QUALIFICATION (the honest NULL). A character is an antagonist-candidate iff it
#  ACTS (agency >= 1 -- a purely PASSIVE rescued object, e.g. Old Sultan's saved
#  child at agency 0, is a victim the protagonist HELPS, NOT an adversary) AND
#  shows sustained opposition: direct engagement that RECURS (co-participation >= 1
#  AND mentions >= 3 -- the recurrence floor rejects an INCIDENTAL setup co-mention
#  like the crow fable's 'birds', one action shared in the opening clause) OR
#  independent recurring agency (>= 2) OR a recurring conflict-target (theme >= 2).
#  A pool with no qualifying candidate yields antagonist=None -- the honest null
#  for a single-character fable (the crow, alone with a pitcher), never fabricated.
#  This mirrors the protagonist's empty-pool null: the DECISION is the Argmax over
#  the qualified `Filter`; the qualification only reads committed graph facts.
# --------------------------------------------------------------------------- #
def _Union(a, b):
    return {"type": "Union", "a": a, "b": b}


def _Intersect(a, b):
    return {"type": "Intersect", "a": a, "b": b}


def _Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


# co-participation dominates conflict-target dominates agency dominates (raw)
# salience -- the SAME weight-separated composition the protagonist score uses.
_W_OPP_CO = 1_000.0
_W_OPP_THEME = 30.0
_W_OPP_AGENCY = 3.0
_ANTAG_MIN_AGENCY = 2.0     # an INDEPENDENT recurring actor (Travelling Musicians' robbers)
_ANTAG_MIN_THEME = 2.0      # a recurring conflict-target (the mouse the cat eats)
_ANTAG_MIN_SALIENCE = 3.0   # recurrence floor on the CO path (rejects a setup co-mention)


def _participation_events(var: str) -> dict:
    """events(x) = the SmEvents x is a PARTICIPANT of (agent OR theme OR goal) —
    Union(Union(InNeighbours(x,'agent'), InNeighbours(x,'theme')),
    InNeighbours(x,'goal')). The set whose pairwise intersection with the
    protagonist's own event set measures direct opposition."""
    return _Union(_Union(_InNeighbours(_V(var), "agent"),
                         _InNeighbours(_V(var), "theme")),
                  _InNeighbours(_V(var), "goal"))


def _co_term(var: str) -> dict:
    """OPPOSITION(e) = |events(e) ∩ events(p)| — the count of SmEvents the
    candidate shares with the protagonist `p` (bound in the eval env), as one
    Term: Count(Intersect(events(e), events(p))). Direct opposition-to-the-
    protagonist. `p` is the outer-env binding the Argmax/Filter push `e` around."""
    return _Count(_Intersect(_participation_events(var), _participation_events("p")))


def _theme_term(var: str) -> dict:
    """CONFLICT-TARGET(e) = Count(InNeighbours(e, 'theme')) — times the candidate
    is the target/patient of an arc action."""
    return _Count(_InNeighbours(_V(var), "theme"))


def _antagonist_score_term(var: str) -> dict:
    """The composite OPPOSITION score, co-participation-dominant then conflict-
    target then agency then salience — ONE Term the Argmax maximises (the SAME
    Count/Intersect/Times/Plus idiom the protagonist score composes). No Python
    arithmetic decides it."""
    return _Plus([
        _Times([_Lit(_W_OPP_CO), _co_term(var)]),
        _Times([_Lit(_W_OPP_THEME), _theme_term(var)]),
        _Times([_Lit(_W_OPP_AGENCY), _agency_term(var)]),
        _Attr(_V(var), "coref_mentions"),
    ])


def _antagonist_qualifies(var: str) -> dict:
    """Q(e): the candidate ACTS (agency >= 1) AND shows sustained opposition —
    recurring direct engagement (CO >= 1 AND salience >= 3) OR independent
    recurring agency (>= 2) OR a recurring conflict-target (theme >= 2). A Term,
    read off committed facts; the DECISION stays the Argmax over the qualified
    pool. Rejects the passive rescued victim (agency 0) and the incidental setup
    co-mention (CO 1 but salience < 3) — the two honest-null discriminations."""
    return _And([
        _Gte(_agency_term(var), _Lit(1.0)),
        _Or([
            _And([_Gte(_co_term(var), _Lit(1.0)),
                  _Gte(_Attr(_V(var), "coref_mentions"), _Lit(_ANTAG_MIN_SALIENCE))]),
            _Gte(_agency_term(var), _Lit(_ANTAG_MIN_AGENCY)),
            _Gte(_theme_term(var), _Lit(_ANTAG_MIN_THEME)),
        ]),
    ])


def _antagonist_pool(agent, prot_name: Optional[str], unit=None) -> dict:
    """The qualified opposition pool as a graph `Filter`: the clean animate
    character pool, EXCLUDING the protagonist by name, AND passing the antagonist
    qualification. The exclusion is a `Not(Eq(name, prot))` guard — the antagonist
    is never the protagonist. Empty -> Argmax default None (the honest null)."""
    base = _character_pool(agent, unit)
    conds = [_antagonist_qualifies("e")]
    if prot_name is not None:
        conds.insert(0, _Not(_Eq(_Attr(_V("e"), "name"), _Lit(prot_name))))
    return _Filter(base, "e", _And(conds))


def antagonist_by_arc_opposition(agent, prot: Optional[dict] = None, unit=None) -> dict:
    """THE OPPOSING AGENCY — the ARC-ROLE antagonist, decided graph-natively.

    The WINNER is one `Argmax` Term over the clean animate character pool
    (EXCLUDING the protagonist, AND qualified as sustained opposition), scored by
    OPPOSITION (co-participation with the protagonist) then conflict-target then
    agency then salience — the DSL evaluator picks it (native Rust, with the
    protagonist node bound as `p` in the eval env), Python never calls
    `max()`/`sorted()` for the decision. The descending `ranking` is Python
    `sorted()` for DISPLAY ONLY (verified to agree with the Argmax pick), the SAME
    Argmax-decides / sort-displays precedent `protagonist_by_arc_agency` sets.

    `prot` is the protagonist result (reused if passed, else computed). Returns
    {antagonist, category, co_participation, conflict_target, agency, mentions,
    score, decided_by, ranking, argmax_matches_top_of_sort, protagonist}. An empty
    qualified pool (no opposing character acts) yields antagonist=None — the honest
    null for a single-character fable, never fabricated.

    `decided_by` is an HONEST provenance read (not a decision): 'opposition' when
    the winner shares an event with the protagonist (CO >= 1, the direct opposition
    structure decided it — Old Sultan's wolf, Dog-and-Sparrow's man); 'conflict'
    when it is a recurring target with no surviving direct edge (the cat's mouse);
    'agency+salience' when coref dissolved every protagonist<->antagonist edge and
    only the strongest independent opposing actor remains (Travelling Musicians'
    robbers) — the honest limit of a pronoun-heavy conflict."""
    sub, native, _ = _resolve(agent)
    # BRIDGING (set-membership): make any individuated member's participation
    # visible as its group's, so a member's conflict ('the dog bit the [robber]')
    # counts as the group's opposition. Idempotent mechanical graph read — a no-op
    # unless a member_of edge exists (every non-bridged tale is byte-identical).
    from domains import coref_entities as _ce
    _ce.propagate_member_participation(agent, unit)
    if prot is None:
        prot = protagonist_by_arc_agency(agent, unit)
    prot_name = prot.get("protagonist")
    prot_node = prot.get("node")
    pnode = None
    if prot_name is not None:
        for n in sub.nodes("SmEntity"):
            if sub.node(n)["attrs"].get("name") == prot_name:
                pnode = n
                break
    env = {"p": pnode} if pnode is not None else {}

    pool = _antagonist_pool(agent, prot_name, unit)
    winner = native.evaluate(_Argmax(pool, "e", _antagonist_score_term("e")), dict(env))
    win_name = sub.node(winner)["attrs"].get("name") if winner is not None else None
    win_cat = sub.node(winner)["attrs"].get("coref_category") if winner is not None else None

    # DISPLAY ranking — evaluate the SAME score per qualified member (mechanical).
    members = native.evaluate(pool, dict(env)) or []
    rows = []
    for m in members:
        at = sub.node(m)["attrs"]
        menv = dict(env); menv["e"] = m
        rows.append({
            "name": at.get("name"),
            "category": at.get("coref_category"),
            "co_participation": int(native.evaluate(_co_term("e"), menv) or 0),
            "conflict_target": int(native.evaluate(_theme_term("e"), menv) or 0),
            "agency": int(native.evaluate(_agency_term("e"), menv) or 0),
            "mentions": float(at.get("coref_mentions", 0.0) or 0.0),
            "score": float(native.evaluate(_antagonist_score_term("e"), menv) or 0.0),
        })
    rows.sort(key=lambda r: -r["score"])   # DISPLAY-ONLY order; the decision was Argmax's.

    win_row = next((r for r in rows if r["name"] == win_name), None)
    decided_by = None
    if win_row is not None:
        if win_row["co_participation"] >= 1:
            decided_by = "opposition"
        elif win_row["conflict_target"] >= int(_ANTAG_MIN_THEME):
            decided_by = "conflict"
        else:
            decided_by = "agency+salience"
    return {
        "antagonist": win_name, "category": win_cat, "node": _v(winner) if winner is not None else None,
        "co_participation": (win_row or {}).get("co_participation"),
        "conflict_target": (win_row or {}).get("conflict_target"),
        "agency": (win_row or {}).get("agency"),
        "mentions": (win_row or {}).get("mentions"),
        "score": (win_row or {}).get("score"),
        "decided_by": decided_by, "ranking": rows, "protagonist": prot_name,
        "argmax_matches_top_of_sort": (win_name is None and not rows)
                                      or (bool(rows) and rows[0]["name"] == win_name),
    }


# --------------------------------------------------------------------------- #
#  RESIDUAL GROUNDING — the agent SAYS what's wrong, then FIXES ITSELF when the
#  reader supplies the missing grounding.
# --------------------------------------------------------------------------- #
def opposition_residual(agent, prot: Optional[dict] = None, unit=None) -> dict:
    """WHAT'S WRONG, in the agent's OWN terms (a mechanical read-off, no decision):
    the arc names an antagonist but the OPPOSITION EDGE IS UNBOUND -- the winning
    opponent shares ZERO events with the protagonist (decided_by ==
    'agency+salience'), while the protagonist's own conflict-verb events point
    their THEME at a NON-CHARACTER junk token (the pronoun / over-segmentation
    mis-parse that dissolved the conflict). That junk-bound theme is the RESIDUAL
    the reader can ground: 'subject opposes object' rebinds it and the agent's own
    Argmax re-derives 'opposition'. Returns the diagnosis + the repairable
    conflict events."""
    from domains import coref_entities as ce
    sub, native, _ = _resolve(agent)
    if prot is None:
        prot = protagonist_by_arc_agency(agent, unit)
    ant = antagonist_by_arc_opposition(agent, prot=prot, unit=unit)
    pnode = None
    for n in sub.nodes("SmEntity"):
        if sub.node(n)["attrs"].get("name") == prot.get("protagonist"):
            pnode = n
            break
    ant_name = ant.get("antagonist")
    conflict_events = []
    if pnode is not None:
        for e in native.in_neighbours(pnode, "agent"):
            ea = native.node(e)["attrs"]
            themes = [str(native.node(t)["attrs"].get("name") or "")
                      for t in native.neighbours(e, "theme")]
            # a conflict event whose theme is NOT the named opponent is a candidate
            # residual — the opposition it should carry is bound elsewhere.
            if ant_name not in themes:
                conflict_events.append({"verb": ea.get("verb"), "theme": themes})
    unbound = (ant.get("decided_by") == "agency+salience"
               and int(ant.get("co_participation") or 0) == 0)
    return {"protagonist": prot.get("protagonist"), "antagonist": ant_name,
            "decided_by": ant.get("decided_by"),
            "co_participation": ant.get("co_participation"),
            "opposition_unbound": unbound, "protagonist_conflict_events": conflict_events,
            "diagnosis": (("'%s' is named the antagonist by frequency/agency but shares "
                           "NO bound event with the protagonist '%s'; none of '%s's own "
                           "action events bind their object to '%s' (the parse scattered "
                           "the conflict onto %s) -- supply the grounding (the protagonist "
                           "opposes '%s') to rebind and re-derive")
                          % (ant_name, prot.get("protagonist"), prot.get("protagonist"),
                             ant_name, [c["theme"] for c in conflict_events], ant_name)
                          if unbound else "opposition is bound (nothing to ground)")}


__all__ = ["ensure_codebook", "decode_slot", "recognize_narrative_structure",
           "read_narrative_roles", "protagonist_by_arc_agency",
           "antagonist_by_arc_opposition", "opposition_residual"]
