"""salient_cache — THE SALIENT ORDER-N CONTEXT CACHE: a graph-resident WORKING
MEMORY holding the salient entities at NESTED order-N levels, that MANY faculties
read. The generic capability long-form coreference was compensating for.

Long-form coref is NOT a coref-specific algorithm — it is a MISSING GENERIC
CAPABILITY. A pronoun ('he'/'the ass'/'they') 50 sentences into a tale must bind
to the entity the discourse is still ABOUT, not the most-recently-named bystander.
A FLAT recent-entities list (coref's `coref_recency`, a monotone turn stamp) is
exactly why a recurring bystander out-ranks a threading protagonist: salience must
be NESTED. This module is that nested working memory, built from the machinery the
reader already has (the situation-model entity pool, the salience/mint idiom
context_model established, the StoryUnit order-N levels story_tree builds) UNIFIED
into ONE generic cache — NOT reinvented.

THE CACHE (graph DATA):
  · a singleton `SalienceClock{turn}` — the current reading tick.
  · one `SalienceCell` per tracked entity, carrying its per-level salience:
    `local_salience` (rises on mention, decays fast with distance) and
    `story_salience` (the order-N level a persisting entity is PROMOTED to). Each
    cell edges `is_scell` (self, for single-node rule matching), `on_clock` (-> the
    clock, so a rule reads the turn) and `scell_of` (-> its SmEntity, so the
    promote rule writes story-salience back onto the entity).

THE SALIENCE DYNAMICS (graph RULES, seeds/salient_cache.json, fired per tick via
run_rules — NOT a Python loop deciding salience):
  · RISE    — a cell touched THIS turn: local_salience += 1, sc_mentions += 1,
              last_turn = turn (idempotent: guarded rise_turn < turn).
  · DECAY   — a cell NOT touched this turn: local_salience *= 0.5 (idempotent:
              guarded decay_turn < turn). A one-scene bystander bleeds out.
  · PROMOTE — a cell that has PERSISTED across a wide span (last_turn - first_turn
              >= 10) AND recurred (sc_mentions >= 3): promoted = 1. This is the
              ORDER-N nesting — story-level salience REQUIRES cross-span recurrence,
              which a short fable structurally cannot have (its whole span < 10),
              so a short fable promotes NOTHING (the byte-identity guard).
  · MIRROR  — a promoted cell writes story_salience onto its SmEntity as
              `coref_story_salience` (+ the `coref_story_salience_on` flag) — where
              the coref Argmax reads it.

WHAT PYTHON DOES HERE (mechanical adapter I/O — no decision, no if/else over graph
state deciding salience): install the seed; mint the clock + cells; MARK which
cells were observed this turn (touched_turn = turn — the observation, "I saw this
entity"); advance the clock; call run_rules (the RULES decide rise/decay/promote);
read the salient cells back out. donkey = 0, no `import re`, no LLM, never git.

GENERIC: coref reads the mirrored `coref_story_salience` (its Argmax factor);
`salient_entities()` / `salient_working_memory()` expose the SAME cells straight
off the graph for a prediction/context/arc faculty to read. Two faculties, one
cache — a working memory, not a coref-specific thing.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import situation_model_reader as smr

_SEED_ID = "salient_cache"
_SENTINEL_CONCEPT = "salient_order_n_cache"

# story-level promotion thresholds (mirrored in seeds/salient_cache.json's
# scell_promote rule — kept here only for documentation / the gate's read-off).
_PROMOTE_MIN_SPAN = 10.0
_PROMOTE_MIN_MENTIONS = 3.0


# --------------------------------------------------------------------------- #
#  resolution (the same idiom every domains/*.py adapter uses).
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


# --------------------------------------------------------------------------- #
#  INSTALL — load the seed (nodes + the rise/decay/promote/mirror RULES) and mint
#  the singleton clock. Guarded by the sentinel Concept, the same idempotency
#  idiom situation_model_reader.ensure_seeds uses. Mechanical seed I/O.
# --------------------------------------------------------------------------- #
def _has_concept(sub, name: str) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return True
    return False


def _clock(agent):
    """The singleton SalienceClock node, or None if the cache is not installed."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("SalienceClock"):
        return n
    return None


def installed(agent) -> bool:
    return _clock(agent) is not None


def install(agent) -> None:
    """Install the salient order-N cache: load seeds/salient_cache.json (its
    RULES into the Rust rule set) and mint the SalienceClock singleton. Idempotent
    — a second call is a no-op. Mechanical seed I/O."""
    sub, native, ag_node = _resolve(agent)
    if _clock(agent) is not None:
        return
    if not _has_concept(sub, _SENTINEL_CONCEPT):
        from substrate.seed_loader import manifest_for
        try:
            native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
        except Exception:
            pass
    if _clock(agent) is None:
        sub.add_node("SalienceClock", {"turn": 0.0})


# --------------------------------------------------------------------------- #
#  CELLS — mint-or-fetch a SalienceCell for a tracked SmEntity, wired to the
#  clock + the entity. Mechanical graph I/O (mint-or-fetch, the same discipline
#  situation_model_reader._entity uses for SmEntity).
# --------------------------------------------------------------------------- #
def _find_entity(sub, name: str, unit=None):
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("name") == name and (unit is None or at.get("unit") == unit):
            return n
    return None


def _find_cell(sub, name: str, unit=None):
    for n in sub.nodes("SalienceCell"):
        at = sub.node(n)["attrs"]
        if at.get("entity") == name and (unit is None or at.get("unit") == unit):
            return n
    return None


def _edge(native, src, label, tgt):
    try:
        native.add_edge_unchecked(src, label, tgt)
    except TypeError:
        native.add_edge_unchecked(src, label, tgt, {})


# the CHARACTER gate — the working memory holds CHARACTERS, not parse junk. The
# SAME predicate narrative_structure._character_pool applies: an animate
# character (coref_category animal / person / unknown — incl. a proper-named one
# WordNet could not ground, but NOT an inanimate `object`), a groundable nominal
# (coref_cleanliness == 1.0, not a parse glom), and NOT a closed-class function
# word (an unresolved pronoun 'he'/'i'/'it'/'they' that grounded unknown+clean is
# excluded by its lexical status). Without this gate the cache would promote the
# most-RECURRING junk (the unresolved-pronoun surface 'he' minted as its own
# SmEntity, the parse-glom 'way'/'saw'/'face'), swamping the real protagonist.
_CHAR_CATEGORIES = frozenset({"animal", "person", "unknown"})


def _is_character(sub, ent, name: str) -> bool:
    at = sub.node(ent)["attrs"]
    if at.get("coref_category") not in _CHAR_CATEGORIES:
        return False
    if float(at.get("coref_cleanliness", 0.0) or 0.0) < 1.0:
        return False
    try:
        from domains import narrative_structure as ns
        if ns._is_function_word(name):
            return False
    except Exception:
        pass
    return True


def _touch_cell(agent, name: str, turn: int, unit=None):
    """Ensure a SalienceCell exists for the CHARACTER SmEntity `name` and MARK it
    observed this turn (touched_turn = turn). Mints the cell + its is_scell /
    on_clock / scell_of edges on first sight. Returns the cell node, or None when
    no SmEntity of that name exists yet OR it is not a trackable character (a
    numeral / parse-glom / pronoun-surface junk arg — not held in working
    memory)."""
    sub, native, _ = _resolve(agent)
    ent = _find_entity(sub, name, unit)
    if ent is None or not _is_character(sub, ent, name):
        return None
    clock = _clock(agent)
    if clock is None:
        return None
    cell = _find_cell(sub, name, unit)
    if cell is None:
        attrs = {"entity": name, "level": "local",
                 "local_salience": 0.0, "story_salience": 0.0, "sc_mentions": 0.0,
                 "first_turn": float(turn), "last_turn": float(turn),
                 "touched_turn": -1.0, "rise_turn": -1.0, "decay_turn": -1.0,
                 "promote_turn": -1.0, "promoted": 0.0}
        if unit is not None:
            attrs["unit"] = unit
        cell = sub.add_node("SalienceCell", attrs)
        _edge(native, cell, "is_scell", cell)         # single-node rule matching
        _edge(native, cell, "on_clock", clock)        # rule reads the turn
        _edge(native, cell, "scell_of", ent)          # promote rule writes back
    sub.set_attr(cell, "touched_turn", float(turn))
    return cell


# --------------------------------------------------------------------------- #
#  THE TICK — advance the clock, run the salience RULES to fixpoint. The RULES
#  decide rise/decay/promote/mirror; Python only advances the clock + dispatches.
# --------------------------------------------------------------------------- #
def tick(agent, turn: int) -> None:
    """Advance the SalienceClock to `turn` and fire the salience RULES (rise on
    touched cells, decay on untouched, promote on cross-span persistence, mirror
    story-salience onto the SmEntities). No-op when the cache is not installed."""
    clock = _clock(agent)
    if clock is None:
        return
    sub, native, _ = _resolve(agent)
    sub.set_attr(clock, "turn", float(turn))
    native.run_rules(10000)


# --------------------------------------------------------------------------- #
#  THE HOOK — one predication's entities into the cache, then one tick. Called
#  from coref_entities' per-predication loop (opt-in: no-op when the cache is
#  absent, so the crow / every existing test is byte-identical).
# --------------------------------------------------------------------------- #
def _pred_entities(pred) -> list:
    """The entity-argument surfaces of a [rel, a0, a1, ...] predication — a0 (the
    subject) plus a1 unless the predication is a bare PROPERTY statement (is_a /
    copular, whose a1 is an attribute, not an entity). Mechanical arg read, the
    same shape coref_entities._predication_roles uses."""
    if not pred or len(pred) < 2:
        return []
    rel = str(pred[0])
    names = [str(pred[1])]
    if len(pred) > 2 and not smr._is_property_pred(rel.lower()):
        names.append(str(pred[2]))
    return names


def after_predication(agent, pred, turn: int, unit=None) -> None:
    """Refresh the working memory for `pred`'s entities and advance one tick.
    No-op unless the cache is installed. Mechanical adapter I/O; the salience
    decision is the seed's rules."""
    if not installed(agent):
        return
    for name in _pred_entities(pred):
        _touch_cell(agent, name, turn, unit)
    tick(agent, turn)


# --------------------------------------------------------------------------- #
#  READ-OFFS — the GENERIC interface any faculty reads (coref reads the mirrored
#  coref_story_salience; a prediction/context/arc faculty reads these). Pure
#  graph queries.
# --------------------------------------------------------------------------- #
def _cell_view(sub, n) -> dict:
    at = sub.node(n)["attrs"]
    return {"entity": at.get("entity"),
            "local_salience": float(at.get("local_salience", 0.0) or 0.0),
            "story_salience": float(at.get("story_salience", 0.0) or 0.0),
            "sc_mentions": float(at.get("sc_mentions", 0.0) or 0.0),
            "promoted": bool(float(at.get("promoted", 0.0) or 0.0) >= 1.0),
            "first_turn": float(at.get("first_turn", 0.0) or 0.0),
            "last_turn": float(at.get("last_turn", 0.0) or 0.0),
            "level": "story" if float(at.get("promoted", 0.0) or 0.0) >= 1.0 else "local",
            "node": _v(n)}


def cells(agent, unit=None) -> list:
    """Every SalienceCell's current view — the raw working-memory contents, for
    the order-N trajectory read-off. Pure graph read."""
    sub, _, _ = _resolve(agent)
    out = []
    for n in sub.nodes("SalienceCell"):
        at = sub.node(n)["attrs"]
        if unit is not None and at.get("unit") != unit:
            continue
        out.append(_cell_view(sub, n))
    return out


def _effective_salience(view: dict) -> float:
    """The effective salience of a cell: its STORY-level salience if promoted (the
    higher order-N level dominates), else its LOCAL salience — the nesting."""
    return view["story_salience"] if view["promoted"] else view["local_salience"]


def salient_entities(agent, *, unit=None, top: Optional[int] = None) -> list:
    """The working memory, MOST-SALIENT FIRST — the RELEVANT entities the reader is
    holding now, at their effective (nested) salience. The GENERIC read a
    prediction / context / arc faculty consults ('what is salient now'). Python
    `sorted()` here is DISPLAY ordering only (the same Argmax-decides / sort-
    displays precedent discourse_coherence.centrality_ranking sets); the single
    winner is decided graph-natively by `salient_working_memory`."""
    rows = cells(agent, unit=unit)
    rows.sort(key=lambda r: -_effective_salience(r))
    return rows[:top] if top is not None else rows


def salient_working_memory(agent, *, unit=None) -> dict:
    """THE MOST-SALIENT ENTITY, decided graph-natively — an `Argmax` Term over the
    SalienceCell pool by effective salience (story if promoted, else local),
    evaluated natively (Python never calls max()/sorted() for the decision). The
    single entity the working memory is most focused on. Returns {entity, level,
    salience, node} or entity=None on an empty cache (the honest null)."""
    sub, native, _ = _resolve(agent)
    # effective salience = promoted ? story_salience : local_salience, as ONE Term.
    def V(n): return {"type": "Var", "name": n}
    def A(node, k): return {"type": "Attr", "node": node, "key": k}
    score = {"type": "IfThenElse",
             "cond": {"type": "Gte", "a": A(V("c"), "promoted"),
                      "b": {"type": "Lit", "value": 1.0}},
             "then": A(V("c"), "story_salience"),
             "other": A(V("c"), "local_salience")}
    src = {"type": "NodesOfType", "node_type": "SalienceCell"}
    if unit is not None:
        src = {"type": "Filter", "source": src, "var_name": "c",
               "predicate": {"type": "Eq", "a": A(V("c"), "unit"),
                             "b": {"type": "Lit", "value": unit}}}
    term = {"type": "Argmax", "source": src, "var_name": "c", "value": score,
            "default": None}
    winner = native.evaluate(term, {})
    if winner is None:
        return {"entity": None, "level": None, "salience": 0.0, "node": None}
    view = _cell_view(sub, winner)
    return {"entity": view["entity"], "level": view["level"],
            "salience": _effective_salience(view), "node": view["node"]}


__all__ = ["install", "installed", "after_predication", "tick", "cells",
           "salient_entities", "salient_working_memory"]
