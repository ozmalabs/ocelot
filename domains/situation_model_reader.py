"""situation_model_reader — THE WIRE: read text -> TEXTBASE -> SITUATION MODEL.

The reader (domains/reading_collapse / reading_scope) is PARSING-COMPLETE and
grounding-strong: it builds a Kintsch TEXTBASE — grounded predications like
`drop(john, glass)` — but it never builds the SITUATION MODEL (the state of
affairs the text denotes: the glass is now on the floor, broken). The machinery
for the situation model already exists and is GREEN in isolation:

  · seeds/situation_model.json — sm_entity carries mutable STATE; sm_event is a
    pre/post-state TRANSITION whose graph rules (sm_drop / sm_move / sm_take /
    sm_put / sm_give / sm_shatter) apply the DELTA, indexed on the five
    Zwaan & Radvansky axes (protagonist / space / time / causation / intention).
  · seeds/event_reasoning.json — the REAL 3-hop inference fixpoint over the model:
    `fell` -> on_floor -> (+fragile) broken -> worthless (infer_on_floor /
    infer_broken / infer_worthless), fired to fixpoint by run_rules.

...but NOTHING fed those seeds a single node from parsed text. This module is the
ONE WIRE. It runs AFTER a sentence commits and, for each grounded predication
whose relation is a CHANGE-OF-STATE verb, mints the sm_event + sm_entity nodes the
seeds' rules match on — then lets `run_rules` (the existing fixpoint, NOT
reimplemented) build the situation model FROM the read text.

WHAT MINTS WHEN
  1. CHANGE-OF-STATE IS A CLASS. A predication's verb (lemmatised by the held
     WordNet morphy) is tested against the `COS` MarkerClass in
     seeds/reading_constructions.json: a SEED member directly, else JOIN-BY-
     ADJACENCY (reusing reading_collapse's WordNet path-similarity nearness to the
     class anchor — the SAME signal DESIGNATE/POSSESS use). NOT a hardcoded Python
     verb list; the members live in the seed, an unseen synonym joins by nearness.
  2. The member's `canon` names the canonical situation_model rule verb
     (drop/move/take/put/give/shatter). We mint an SmEvent{verb:canon, active:1}
     and SmEntity nodes (each with the `is_entity` SELF-EDGE event_reasoning
     matches on), wiring the ROLE edges the situation_model rule for that verb
     expects — the role FRAME (theme vs goal) is read from the seed rule's OWN
     match pattern, not guessed here.
  3. The event's five INDICES are filled from the predication's arguments
     (protagonist<-agent, entity<-theme, space<-goal); an index the text does not
     supply is a RESIDUAL (recorded, not silently blank — salience = surprise).
  4. For the fall-family canon (`fell_canon`) the theme is stamped `fell` — the one
     bridge attr event_reasoning's chain keys on. `fragile` (the other premise of
     the broken inference) is WORLD KNOWLEDGE: it is filled only when a stated
     property predication supplies it (`is_a(glass, fragile)` -> glass.fragile),
     else it is an honest residual (the knowledge-codebook follow-on).
  5. run_rules() — the situation_model deltas AND the event_reasoning 3-hop chain
     fire to fixpoint over the minted nodes. The situation model now holds what the
     text did NOT state.

ARCHITECTURE (CLAUDE.md). The mint is graph nodes/edges (mechanical adapter I/O);
the INFERENCE is the existing `run_rules` fixpoint over the two seeds (NOT
reimplemented here); the change-of-state trigger is the `COS` MarkerClass +
join-by-adjacency (NOT a regex, NOT a hardcoded verb list). No `if`/`else` decides
a state delta — the seed RULES do. This module only (a) lemmatises + classifies the
verb against the seed class, (b) mints the nodes the rules match on, (c) runs the
fixpoint, (d) reads the resulting state back out.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import reading_collapse as rc
from domains import reading_scope as rs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SM_SEED = os.path.join(_ROOT, "seeds", "situation_model.json")

# the five Zwaan & Radvansky event-indexing axes the situation model hangs on.
_INDICES = ("protagonist", "entity", "space", "time", "causation", "intentionality")


# --------------------------------------------------------------------------- #
#  resolution + seed install (mechanical adapter I/O — no decision).
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


def _has_concept(sub, name: str) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return True
    return False


def ensure_seeds(agent) -> None:
    """Idempotently install the situation_model + event_reasoning seeds (their
    rules ARE the fixpoint this wire feeds) and the reading construction codebook
    (which carries the `COS` MarkerClass). Guarded by a natural sentinel Concept
    from each seed, so a boot that already loaded them (WorldAdapter persona boot)
    is not double-loaded. Mechanical seed I/O — the same idiom rc.ensure_codebook
    uses."""
    from substrate.seed_loader import manifest_for
    sub, native, ag_node = _resolve(agent)
    rc.ensure_codebook(agent)                      # the COS MarkerClass lives here
    # situation_model (sentinel: Concept 'sm_entity'), then event_reasoning
    # (sentinel: Concept 'fabula'). Loaded in dependency order.
    for sid, sentinel in (("situation_model", "sm_entity"), ("event_reasoning", "fabula")):
        if not _has_concept(sub, sentinel):
            try:
                native.load_seed_manifest(manifest_for(sid), ag_node)
            except Exception:
                pass


# --------------------------------------------------------------------------- #
#  COS MEMBERSHIP — the change-of-state class read off the seed + join-by-adjacency.
# --------------------------------------------------------------------------- #
def _cos_node(sub):
    for n in sub.nodes("MarkerClass"):
        if sub.node(n)["attrs"].get("cls") == "COS":
            return n
    return None


def _lemma(verb: str) -> str:
    """The verb's citation lemma via the held WordNet morphy (the SAME lemmatiser
    reading_collapse's _clean_head / _wordnet_nearness rely on) — 'dropped'->'drop',
    'went'->'go'. No regex, no stemming table. Falls back to the surface."""
    w = str(verb).lower().strip()
    try:
        from nltk.corpus import wordnet as wn
        lem = wn.morphy(w, "v")
        if lem:
            return lem
    except Exception:
        pass
    return w


def _verb_lexname(lemma: str) -> Optional[str]:
    """The dominant WordNet lexicographer-file (`lexname`) of `lemma`'s verb
    senses — WordNet's OWN semantic classification of the verb (`verb.stative`,
    `verb.motion`, `verb.contact`, `verb.change`, ...). The dominant sense is
    synset[0] (WordNet orders synsets most-frequent-first), the SAME held
    WordNet reference `_lemma` / rc._wordnet_nearness read. None when the verb
    is out-of-vocabulary (no verb synset). Not a hardcoded verb list — the
    class is WordNet's, read off the lexname."""
    try:
        from nltk.corpus import wordnet as wn
        syns = wn.synsets(lemma, pos="v")
        if syns:
            return syns[0].lexname()
    except Exception:
        pass
    return None


def eventive_membership(agent, verb: str) -> dict:
    """Is `verb` EVENTIVE (a dynamic action/change that mints an SmEvent) or
    STATIVE (a state that does not)? The DECISION is read off WordNet's own verb
    lexicographer-file classification (`_verb_lexname`), NOT a seeded verb list:
    a verb whose DOMINANT sense's lexname is `verb.stative` (be/seem/belong/own/
    matter/...) is STATIVE — everything else (motion/contact/change/communication/
    social/possession/cognition/...) is EVENTIVE, an action or change that mints
    an event. An out-of-vocabulary verb defaults EVENTIVE (an unknown main-clause
    verb in a narrative is almost always an action — the same 'OOV -> content'
    default is_nominal takes for an unknown noun head). Returns {lemma, eventive,
    lexname, stative, oov}."""
    lemma = _lemma(verb)
    lexname = _verb_lexname(lemma)
    oov = lexname is None
    stative = (lexname == "verb.stative")
    return {"lemma": lemma, "eventive": (not stative), "lexname": lexname,
            "stative": stative, "oov": oov}


def cos_membership(agent, verb: str) -> dict:
    """Is `verb` a change-of-state verb? Returns {lemma, cos, canon, nearness,
    nearest, joined, via}. A SEED member resolves directly (via='member'); an
    unseen verb JOINS by adjacency — reusing rc._wordnet_nearness (the SAME WordNet
    path-similarity signal DESIGNATE/POSSESS use) to the class anchor >= threshold,
    inheriting its nearest anchor's `canon` (via='adjacency'), and is placed into
    the class live (rc._join_class) so it is a member thereafter. Below threshold ->
    not a change of state (cos=False)."""
    rc.ensure_codebook(agent)                     # the COS MarkerClass must be installed
    sub, _, _ = _resolve(agent)
    lemma = _lemma(verb)
    node = _cos_node(sub)
    if node is None:
        return {"lemma": lemma, "cos": False, "canon": None, "nearness": 0.0,
                "nearest": None, "joined": False, "via": None}
    at = sub.node(node)["attrs"]
    forms = [str(f).lower() for f in (at.get("forms") or [])]
    canon = dict(at.get("canon") or {})
    if lemma in forms:
        return {"lemma": lemma, "cos": True, "canon": canon.get(lemma, lemma),
                "nearness": 1.0, "nearest": lemma, "joined": False, "via": "member"}
    # JOIN-BY-ADJACENCY — the class-learning mechanism (not a hardcoded list).
    anchors = [str(a).lower() for a in (at.get("cos_anchor") or [])]
    try:
        thr = float(at.get("cos_threshold", 0.75))
    except (TypeError, ValueError):
        thr = 0.75
    score, member = rc._wordnet_nearness(lemma, anchors)
    if member is not None and score >= thr:
        rc._join_class(sub, node, lemma, score, member)     # place it into the class, live
        joined_canon = canon.get(member, member)
        # the class LEARNS the canon too: persist lemma->canon so a later occurrence
        # of the same verb resolves via the member path to the SAME situation_model
        # rule verb (else the member lookup would fall back to the lemma itself).
        canon[lemma] = joined_canon
        try:
            sub.set_attr(node, "canon", canon)
        except Exception:
            pass
        return {"lemma": lemma, "cos": True, "canon": joined_canon,
                "nearness": float(score), "nearest": member, "joined": True,
                "via": "adjacency"}
    return {"lemma": lemma, "cos": False, "canon": None, "nearness": float(score),
            "nearest": member, "joined": False, "via": None}


# --------------------------------------------------------------------------- #
#  ROLE FRAMES — read from the situation_model rules' OWN match patterns, so the
#  object-role (theme vs goal) the wire assigns is the one the rule expects. Not
#  guessed here; the seed rule decides which edge label its delta reads.
# --------------------------------------------------------------------------- #
_FRAME_CACHE: Optional[dict] = None


def _verb_frames() -> dict:
    """{canon_verb: set(role_labels)} parsed from seeds/situation_model.json — the
    edge labels each rule matches (agent/theme/goal/recipient) keyed by the verb its
    `where` clause requires. Mechanical seed read (like rc reads its codebook)."""
    global _FRAME_CACHE
    if _FRAME_CACHE is not None:
        return _FRAME_CACHE
    frames: dict[str, set] = {}
    try:
        with open(_SM_SEED) as f:
            seed = json.load(f)
    except Exception:
        seed = {"rules": []}
    for rule in seed.get("rules", []):
        verb = None
        where = rule.get("where", {})
        items = where.get("items", [where]) if isinstance(where, dict) else []
        for it in items:
            if it.get("type") == "Eq" and it.get("a", {}).get("key") == "verb":
                verb = it.get("b", {}).get("value")
        roles = {m[1] for m in rule.get("match", []) if len(m) >= 2}
        if verb:
            frames.setdefault(verb, set()).update(roles)
    _FRAME_CACHE = frames
    return frames


# --------------------------------------------------------------------------- #
#  ENTITY POOL — sm_entity nodes are keyed by name and PERSIST across sentences
#  (the situation model is not per-clause). Each carries the `is_entity` self-edge
#  event_reasoning's rules match on.
# --------------------------------------------------------------------------- #
def _entity(agent, name: str, *, unit=None):
    """The sm_entity for `name`. UNIT-SCOPED (MOVE 2b): when `unit` is given,
    the name-lookup is confined to entities carrying that `unit` attr and a
    fresh mint is stamped with it -- so the lion of episode 1 and the
    re-introduced lion of episode 2 are DISTINCT graph nodes (order-N isolation:
    a name resolves WITHIN its StoryUnit). `unit=None` (the depth-1 default) is
    the flat case, byte-for-byte the pre-2b behaviour: no `unit` attr is read or
    written and the global name pool is consulted exactly as before."""
    sub, native, _ = _resolve(agent)
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("name") == name and (unit is None or at.get("unit") == unit):
            return n
    attrs = {"name": name}
    if unit is not None:
        attrs["unit"] = unit
    nid = sub.add_node("SmEntity", attrs)
    _edge(native, nid, "is_entity", nid)          # the self-edge event_reasoning keys on
    return nid


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def _edge(native, src, label, tgt):
    try:
        native.add_edge_unchecked(src, label, tgt)
    except TypeError:
        native.add_edge_unchecked(src, label, tgt, {})


def entity_state(agent, name: str) -> dict:
    """Read the current state slice of an sm_entity (its attrs minus bookkeeping) —
    a pure graph query, the test of comprehension: what is true NOW."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return {k: v for k, v in at.items() if k != "name"}
    return {}


# --------------------------------------------------------------------------- #
#  INGEST ONE PREDICATION — mint the sm_* nodes, run the fixpoint.
# --------------------------------------------------------------------------- #
def _existing_generic_event(sub, unit, surface: str, a0: str, a1: str):
    """A held GENERIC SmEvent for this unit's exact (surface, protagonist, arg1) —
    so a generic event is minted ONCE per re-read (the streaming-idempotency guard,
    the same 'no duplicate node' discipline _entity uses for SmEntity). Returns the
    node or None."""
    for n in sub.nodes("SmEvent"):
        at = sub.node(n)["attrs"]
        if at.get("generic") == 1 and at.get("surface") == surface \
                and at.get("idx_protagonist") == a0 and at.get("arg1") == a1 \
                and (unit is None or at.get("unit") == unit):
            return n
    return None


def _is_property_pred(rel: str) -> bool:
    # a stated PROPERTY predication ('the glass is fragile' -> is_a(glass, fragile)):
    # its complement is state the entity carries (fragile), the premise event_reasoning
    # needs for `broken`. Copular/definitional relations only.
    #
    # `designate` is the naming/is_a relation the DESIGNATE class-construction emits
    # ('described/known/termed/called as X' — the construction note: "Binds the subject
    # to what it is CALLED (a naming/is_a relation)"). It is STATIVE naming, NOT an
    # action, so it routes here (a state attr, no agent edge) instead of minting a
    # generic SmEvent that would confer spurious AGENCY on an epithet ('wretch' in
    # "'Not wretch enough yet!' said the sparrow" is a name uttered, not a character
    # that acts).
    return rel in ("is_a", "is", "cop", "designate")


def ingest_predication(agent, pred: list, *, t: int = 0, unit=None) -> dict:
    """Wire ONE grounded predication [rel, arg0, arg1] into the situation model.

    · PROPERTY (is_a / copular): the complement becomes a STATE ATTR on the subject
      entity (`is_a(glass, fragile)` -> glass.fragile = 1) — entities carry state.
    · CHANGE-OF-STATE (rel's lemma is in the COS class): mint SmEvent{verb:canon} +
      the SmEntity role nodes, fill the five indices, stamp `fell` for the fall
      family, and run the fixpoint (situation_model deltas + event_reasoning chain).
    · otherwise: NO state transition (the discriminative case).

    Returns the mint record: event node, filled indices, residual indices, the COS
    verdict, and the entity state slice after the fixpoint."""
    ensure_seeds(agent)
    sub, native, _ = _resolve(agent)
    if not pred or len(pred) < 3:
        return {"cos": False, "kind": "degenerate", "predication": pred}
    rel, a0, a1 = str(pred[0]), str(pred[1]), str(pred[2])

    if _is_property_pred(rel):
        ent = _entity(agent, a0, unit=unit)
        sub.set_attr(ent, a1, 1)                  # 'fragile' etc. becomes state=1
        native.run_rules(10000)                   # a property may complete a stalled chain
        return {"cos": False, "kind": "property", "predication": pred,
                "entity": a0, "property": a1, "state": entity_state(agent, a0)}

    mem = cos_membership(agent, rel)
    if not mem["cos"]:
        # GENERIC EVENTIVE (2026-07-07): the COS class only carries the verbs
        # whose canon has a state-DELTA rule. A non-COS predication is NOT
        # necessarily eventless — a dynamic ACTION verb should mint an SmEvent (so
        # the per-episode arc fills), while a STATIVE (be/seem/resemble) should
        # not. The eventive-vs-stative DECISION is WordNet's own verb
        # classification (`eventive_membership` -> the verb lexicographer file),
        # NOT a seeded verb list. An eventive non-COS verb mints a GENERIC SmEvent
        # (no canonical state delta — there is no rule for it — but the event
        # EXISTS for the narrative arc); a stative mints nothing (the
        # discriminative null, exactly the old non_change_of_state).
        ev = eventive_membership(agent, rel)
        if not ev["eventive"]:
            return {"cos": False, "kind": "non_change_of_state", "predication": pred,
                    "membership": mem, "eventive": ev,
                    "note": "%r is a STATIVE verb (WordNet %r) — no event minted"
                    % (ev["lemma"], ev["lexname"])}
        # IDEMPOTENT (2026-07-07): a generic event is held ONCE — a re-read of the
        # same prefix (the incremental-streaming harness re-dispatches the spine over
        # the grown source each increment) must NOT duplicate it, else Count(SmEvent)
        # inflates on every re-read and the material-triggered order-N re-collapse
        # can no longer tell genuine growth from a re-read. Dedup key: this unit's
        # (surface, protagonist, arg1) — the same predication, same episode. A flat
        # single read never hits an existing match, so the non-streaming path is
        # byte-identical.
        existing = _existing_generic_event(sub, unit, rel, a0, a1)
        if existing is not None:
            return {"cos": False, "kind": "generic_event", "predication": pred,
                    "membership": mem, "eventive": ev, "canon": ev["lemma"],
                    "object_role": "theme", "event": _v(existing), "tracked_entity": a1,
                    "already": True, "state": entity_state(agent, a1)}
        ag_ent = _entity(agent, a0, unit=unit)
        ob_ent = _entity(agent, a1, unit=unit)
        ev_attrs = {"verb": ev["lemma"], "surface": rel, "t": float(t), "active": 0,
                    "generic": 1, "arg1": a1}
        if unit is not None:
            ev_attrs["unit"] = unit
        event = sub.add_node("SmEvent", ev_attrs)
        _edge(native, event, "agent", ag_ent)
        _edge(native, event, "theme", ob_ent)
        filled = {"protagonist": a0, "entity": a1, "time": float(t)}
        residual = [k for k in _INDICES if k not in filled]
        for k, val in filled.items():
            sub.set_attr(event, "idx_" + k, val)
        sub.set_attr(event, "residual_indices", json.dumps(residual))
        cn = sub.node(ob_ent)["attrs"].get("coref_number")
        if cn is not None:
            sub.set_attr(event, "coref_number", cn)
        # no canonical delta rule matches a generic verb, but run the fixpoint so
        # any event_reasoning follow-on over already-stated state still reaches
        # fixpoint (mechanical, idempotent — no generic-specific branch).
        native.run_rules(10000)
        return {"cos": False, "kind": "generic_event", "predication": pred,
                "membership": mem, "eventive": ev, "canon": ev["lemma"],
                "object_role": "theme", "event": _v(event), "tracked_entity": a1,
                "indices": filled, "residual_indices": residual,
                "state": entity_state(agent, a1)}

    canon = mem["canon"]
    frame = _verb_frames().get(canon, {"theme"})
    # arg0 (the surface SUBJECT) is the agent/protagonist; arg1 (the OBJECT) is the
    # goal iff the seed rule for this verb reads a `goal` edge (a motion verb —
    # move/put), else the theme (drop/take/shatter/give). The seed rule decides.
    obj_role = "goal" if "goal" in frame else "theme"
    ag_ent = _entity(agent, a0, unit=unit)
    ob_ent = _entity(agent, a1, unit=unit)
    ev_attrs = {"verb": canon, "surface": rel, "t": float(t), "active": 0}
    if unit is not None:
        ev_attrs["unit"] = unit
    event = sub.add_node("SmEvent", ev_attrs)
    _edge(native, event, "agent", ag_ent)
    _edge(native, event, obj_role, ob_ent)

    # the thing whose STATE changes (the 5-index 'entity'): the theme, or the mover
    # (agent) for a pure motion verb where arg1 is the goal.
    tracked_name = a1 if obj_role == "theme" else a0
    # fill the five indices; an index the text did not supply is a residual.
    filled = {"protagonist": a0, "entity": tracked_name}
    if obj_role == "goal":
        filled["space"] = a1
    filled["time"] = float(t)
    residual = [k for k in _INDICES if k not in filled]   # causation, intentionality, (space)
    for k, val in filled.items():
        sub.set_attr(event, "idx_" + k, val)
    sub.set_attr(event, "residual_indices", json.dumps(residual))

    # ADDITIVE DURABLE MARKER (blackboard dissolution): stamp the tracked
    # entity's grounded coref_number onto THIS SmEvent so the "many small
    # units acted on one at a time" (INCREMENTAL) signal is graph-readable
    # off the event itself -- today it lived only in the transient per-
    # predication ingest record's `state` dict (coref_entities stamps
    # coref_number on the tracked SmEntity BEFORE ingest, so it is resident
    # here). No existing attr semantics change; a pure-smr path with no coref
    # bookkeeping simply stamps nothing (the guard).
    tracked_ent = ob_ent if obj_role == "theme" else ag_ent
    cn = sub.node(tracked_ent)["attrs"].get("coref_number")
    if cn is not None:
        sub.set_attr(event, "coref_number", cn)

    # the fall-family bridge: the theme ends up fallen -> the one attr event_reasoning
    # keys on. Data-driven (COS.fell_canon), not a Python verb branch.
    cos_at = sub.node(_cos_node(sub))["attrs"] if _cos_node(sub) is not None else {}
    fell_canon = [str(c).lower() for c in (cos_at.get("fell_canon") or [])]
    fell_set = False
    if canon in fell_canon and obj_role == "theme":
        sub.set_attr(ob_ent, "fell", 1)
        fell_set = True

    # RUN THE FIXPOINT — situation_model deltas + event_reasoning 3-hop chain. The
    # now-frame: only this event is active while its delta applies (the script idiom).
    sub.set_attr(event, "active", 1)
    native.run_rules(10000)
    sub.set_attr(event, "active", 0)
    # a fresh `fell` may have completed the on_floor->broken->worthless chain; a
    # second sweep lets event_reasoning reach fixpoint over the whole model.
    native.run_rules(10000)

    return {"cos": True, "kind": "change_of_state", "predication": pred,
            "membership": mem, "canon": canon, "verb_frame": sorted(frame),
            "object_role": obj_role, "event": _v(event), "tracked_entity": tracked_name,
            "indices": filled, "residual_indices": residual, "fell_set": fell_set,
            "state": entity_state(agent, tracked_name)}


# --------------------------------------------------------------------------- #
#  READ TEXT INTO THE SITUATION MODEL — the driver: reader -> textbase -> ingest.
# --------------------------------------------------------------------------- #
def read_into_situation_model(agent, text: str, *, max_sentences: int = 40, unit=None) -> dict:
    """THE WIRE end-to-end. Segment `text`, read each sentence by the HELD scoped
    collapse (reading_scope.read_scope — UNCHANGED, used as-is), then ingest every
    committed predication into the situation model. Returns the per-sentence
    textbase (the grounded predications) and, after the fixpoint, the situation
    model (each entity's state slice) — including the state the text never stated."""
    ensure_seeds(agent)
    sentences = rc._split_sentences(text)
    textbase: list = []
    ingests: list = []
    t = 0
    for s in sentences[:max_sentences]:
        if not s.strip():
            continue
        rec = rs.read_scope(agent, s)
        preds = rec.get("predications") or []
        source = "read_scope"
        if not preds:
            # the scoped reader HELD THE SENTENCE OPEN (e.g. reading_review judges a
            # copular property 'glass is fragile' selectionally incoherent as an is_a).
            # Fall back to the single-pass held clause reader (rc.read_clause, used
            # AS-IS) so a stated property still reaches the model.
            fb = rc.read_clause(agent, s, write=False)
            preds = fb.get("predications") or []
            source = "read_clause_fallback"
        textbase.append({"sentence": s, "predications": preds, "source": source})
        for p in preds:
            t += 1
            ingests.append(ingest_predication(agent, p, t=t, unit=unit))
    # the final situation model: every entity's current state slice (UNIT-SCOPED
    # when a unit is given -- only this StoryUnit's entities).
    sub, _, _ = _resolve(agent)
    model: dict[str, dict] = {}
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if unit is not None and at.get("unit") != unit:
            continue
        if nm:
            model[nm] = {k: v for k, v in at.items() if k != "name"}
    return {"text": text, "sentences": sentences, "textbase": textbase,
            "ingests": ingests, "situation_model": model}


__all__ = ["ensure_seeds", "cos_membership", "eventive_membership",
           "ingest_predication", "read_into_situation_model", "entity_state"]
