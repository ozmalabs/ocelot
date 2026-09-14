"""literary_analysis — THE JABBERWOCK WRITES A LITERARY ANALYSIS, ONE LEVEL UP
FROM TROPE+THEME. donkey = 0, graph-native, GRAPH-CHECKABLE, no `import re`.

`comprehension_reader.read_and_comprehend` already builds the whole
comprehension graph: the situation model (SmEntity/SmEvent), the inferred goal
+ remedy, the causal-weighted centrality SUMMARY, the story-grammar arc
(`NarrativeRole` setup/problem/solution/resolution), and the recognised TROPES
+ THEME (`Trope`/`Theme` nodes with graph-checkable evidence). This module is
the construction ONE LEVEL UP: it renders that graph as a short literary
ANALYSIS — SUMMARY, NARRATIVE STRUCTURE, TECHNIQUE/TROPES, THEME — where every
CONTENT word of every sentence is READ OFF A GRAPH NODE, never invented.

THE PRODUCTION FACULTY (reused, not reimplemented). The affirmative event
clauses (setup: "the crow found the pitcher"; solution: "the crow dropped the
pebbles"; resolution: "the water rose") are realised by the agent's OWN
production faculty — `domains.language_production.LanguageProduction.produce`,
the generation-is-reading-reversed grammar-over-grounded-vocabulary renderer
the self-account demo (`scripts/drive_self_account_fluent.py`) already drives.
The producer is fed goal FRAMES `{event, agent, patient, tense, intent}` whose
fillers are read off the comprehension graph (the arc's role predications, the
goal record). The producer's vocabulary is grounded (stub teacher, NO LLM)
from a corpus MECHANICALLY DERIVED from those same graph predications — the
corpus grounds word<->concept + SVO grammar; the analysis frames come from the
graph; the produced sentence is the faculty's realisation, never a hand-written
literary phrase.

TENSE (past-from-surface, not literary present — chosen honestly). Inflection
is realised by the lexicon-in-reverse (`language_production`'s own documented
mechanism: "the grounded LexEntry surface IS already the inflected form"); it
falls out for free ONLY when the grounded surface fed to the producer is
itself inflected. The comprehension textbase's per-sentence predication already
carries the sentence's OWN inflected verb token in its relation slot
(`situation_model_reader` mints the matching `SmEvent` with BOTH `verb`=the
canonical lemma AND `surface`=this exact same token — 'dropped'/'rose'/'took'/
'ate' — confirming the textbase relation already IS that graph-held surface,
not a code guess). So the event FRAME's `event` filler is that raw relation
token, UNCHANGED — no lemmatisation — and the producer's corpus is built with
that same inflected word as the literal text token, so concept<->surface
grounds as an inflected identity and "dropped"/"rose"/"took"/"ate" fall out of
the SAME morphophonological_encoding stage the self-account demo drives. There
is no grounded PRESENT-tense surface anywhere in these two short fables (no
seed grounds "drops"/"rises" against a 3rd-singular -s morphology generator —
`language_production` deliberately has none, see its own HONEST ledger), so
PAST — the tense the source text and the situation-model surfaces already
carry — is the tense that is actually realisable without inventing morphology;
literary present was rejected as unrealisable-without-faking, not preferred.
HONEST RESIDUAL: two events have no better grounded surface than their bare
lemma — 'found' (an irregular WordNet morphy already keeps as its own lemma;
the crow story's setup token literally already IS 'found', so nothing is
lost) and the GOAL-remedy clause's word when the resolution sentence's own
recognised words hold no inflected form of it (the crow fable's own text for
"drink" is itself the bare modal-complement "...he could drink" — no 'drank'
token exists anywhere in the source, so the bare form is the textually FAITHFUL
surface, not an unfixed bug; the mouse fable's remedy 'eat' DOES have its own
sentence's recognised inflected token 'ate', so that one is realised properly
— see `_verb_surface_from_words`).

WHAT IS FIXED FRAME (disclosed honestly — see the HONEST ledger in the test and
`kind=='framed'` claims). Two constructions the frame producer genuinely cannot
render are surfaced by a FIXED CONNECTIVE with GRAPH-SOURCED content-word slots:

  · NEGATION ("the crow cannot reach the water") — the frame producer has no
    polarity/negation; the problem role and the summary's central-obstacle
    sentence use the fixed connective "... cannot ... the ...", filling
    agent/event/patient from the problem role's own predication (graph-sourced).
  · ABSTRACT TROPE / THEME attribution — the technique sentence names the
    recognised trope's own graph-held `label_name` (MacGyvering / Determinator)
    + `name` (INGENUITY_OVER_STRENGTH / PERSISTENCE_PAYS) and derives its
    mechanism descriptor from the trope's own covered TOKEN names
    (TROPE_INDIRECT -> "indirect", TROPE_INCREMENTAL -> "incremental"); the
    theme sentence surfaces the `Theme` node's own held `lines` verbatim. All
    of these are graph DATA (a seed's authored gloss, read back), never a
    literary phrase this module writes.

GRAPH-CHECKABLE (the headline gate — 'coherence is not correctness'). Every
sentence the analysis emits is a `Claim` carrying `graph_pointers`: the node
id(s) it is read off. A claim is EMITTED ONLY WITH a non-empty pointer set
(`_emit` refuses an ungrounded claim), and `claim_map` covers every sentence.
A caller/gate can walk each sentence back to the exact `NarrativeRole` /
`Trope` / `Theme` / `DiscourseEvent` / `SmEntity` node that grounds it — a
fluent-but-ungrounded sentence cannot appear.

ARCHITECTURE (CLAUDE.md). This is a WORLD-ADAPTER read path over an
already-built comprehension graph: it reads graph facts (roles, tropes, theme,
centrality, predications) other components' own collapses already committed,
marshals frame fillers, and drives the held production faculty. It makes NO new
comprehension decision — no if/else decides a meaning, no rule engine runs in
Python, no trope/role name is chosen here (every one comes from a graph node's
own attr). No `import re`; donkey = 0.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import comprehend_text as ct
from domains import comprehension_reader as cr
from domains import narrative_structure as ns
from domains import situation_model_reader as smr
from domains import trope_theme as tt


# --------------------------------------------------------------------------- #
#  resolution helpers (mechanical adapter I/O — no decision).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


_PRONOUNS = frozenset({"he", "him", "his", "she", "her", "it", "its",
                       "they", "them", "their", "i", "me", "we", "us",
                       "you", "himself", "herself", "itself", "themselves"})
_PROPERTY_RELS = frozenset({"is_a", "is", "cop", "as", "to"})


# --------------------------------------------------------------------------- #
#  GRAPH READS — pull the already-committed facts each section renders. Pure
#  graph queries; no meaning decided here.
# --------------------------------------------------------------------------- #
def _sentence_predications(graph: dict) -> list[list]:
    """One list of raw (relation, subj, obj) predications per sentence order,
    read off the spine's textbase (`coref_entities.read_into_situation_model`'s
    own already-committed per-sentence parse). RAW (pre-coref) predications are
    used deliberately: the coref pass can bind a bare pronoun to a wrong plural
    antecedent (an honest, known limitation — see the HONEST ledger), so the
    solution patient is instead sourced from the sentence's recognised nouns."""
    tb = (graph.get("spine") or {}).get("textbase") or []
    return [list(t.get("predications") or []) for t in tb]


def _discourse_node_id(sub, order: int) -> Optional[int]:
    for n in sub.nodes("DiscourseEvent"):
        if sub.node(n)["attrs"].get("order") == order:
            return _v(n)
    return None


def _sm_entity_node(sub, name: str) -> Optional[int]:
    for n in sub.nodes("SmEntity"):
        if sub.node(n)["attrs"].get("name") == name:
            return _v(n)
    return None


def _role_node_id(sub, entity: str, order: int, role: str) -> Optional[int]:
    n = ns._existing_role(sub, entity, order, role)
    return _v(n) if n is not None else None


def _is_content_noun(agent, word: str, sub, exclude: set) -> bool:
    """A groundable content noun: not a pronoun, not the protagonist/excluded,
    and WordNet knows it as a noun (`dictionary_lexicon` morphy, the SAME
    lemmatiser the reading stack uses)."""
    w = str(word).lower()
    if w in _PRONOUNS or w in exclude or len(w) < 2:
        return False
    return bool(smr._lemma(w) and _sm_entity_node(sub, w) is not None) or _wn_is_noun(w)


def _wn_is_noun(word: str) -> bool:
    try:
        from nltk.corpus import wordnet as wn
        return bool(wn.synsets(str(word).lower(), pos=wn.NOUN))
    except Exception:
        return False


# --------------------------------------------------------------------------- #
#  FRAME FILLERS — every filler is a graph-sourced content word. Pronoun agents
#  fall back to the arc's protagonist; the solution patient is the plural
#  recognised noun (tying to the INCREMENTAL signal), lemmatised.
# --------------------------------------------------------------------------- #
def _lemma(word: str) -> str:
    return smr._lemma(str(word)) or str(word)


def _verb_lemma(word: str) -> str:
    """Lemmatise an event verb through WordNet's VERB morphy (dropped -> drop,
    rose -> rise). Used for (a) the NEGATION frame's modal complement
    ("cannot reach" wants the bare infinitive, which this already computes
    correctly since 'reach' has no inflection to lose), and (b) as the LOOKUP
    KEY `_verb_surface_from_words` matches a sentence's recognised words
    against (never as the word actually rendered for an affirmative event
    clause — those use the graph's own inflected relation token directly, see
    `_frames_for`). Irregulars WordNet keeps as their own lemma
    (found -> found) are left as grounded — an honest surface==lemma
    coincidence, disclosed in the HONEST ledger, not a re-lemmatisation bug."""
    w = str(word).lower()
    try:
        from nltk.corpus import wordnet as wn
        m = wn.morphy(w, wn.VERB)
        if m:
            return m
    except Exception:
        pass
    return _lemma(w)


def _verb_surface_from_words(words: list, lemma: str) -> Optional[str]:
    """Among a sentence's recognised words (graph-sourced: `ct._recognise_words`,
    the SAME scan `_recognised_nouns` uses for patients), the one token whose
    WordNet VERB morphy equals `lemma` — the sentence's OWN inflected surface
    for that event ('ate' for lemma 'eat', read off the actual text). Used for
    the GOAL-remedy clause, whose word is schema-supplied (not a textbase
    predication) so it has no relation-slot surface of its own; this recovers
    one from the resolution sentence's own words when the text holds an
    inflected form. Returns None (an honest residual — the bare lemma is then
    the only realisable word) when no recognised word lemmatises to `lemma`,
    e.g. the crow fable's own text for 'drink' is itself the bare modal
    complement "...he could drink" — no inflected form exists to find."""
    for w in words:
        wl = str(w).lower()
        if _verb_lemma(wl) == lemma:
            return wl
    return None


def _noun_lemma(word: str) -> str:
    """WordNet NOUN morphy (pebbles -> pebble). `situation_model_reader._lemma`
    does not singularise plural nouns, so the plural-affected patient (the
    INCREMENTAL signal's own many small units) needs the noun morphy."""
    w = str(word).lower()
    try:
        from nltk.corpus import wordnet as wn
        m = wn.morphy(w, wn.NOUN)
        if m:
            return m
    except Exception:
        pass
    return _lemma(w)


def _pick_agent(pred: list, protagonist: str) -> str:
    subj = str(pred[1]) if len(pred) > 1 else protagonist
    if subj.lower() in _PRONOUNS or "_" in subj:
        return protagonist
    return subj


# object-like coref categories: a clean patient is a thing/being acted upon,
# NOT a degree word (`higher`) or a discourse residue (category 'unknown').
_OBJECT_CATS = frozenset({"object", "person", "animal", "thing"})


def _select_pred(sub, preds_order: list, entity: str) -> Optional[list]:
    """Among a sentence's predications, the key EVENT predication: prefer the
    one whose (pronoun-resolved) subject is the protagonist, else the first
    non-property predication. A predication whose RELATION slot is itself a
    resident SmEntity name (a degenerate parse like ['mouse','so','ate_cheese']
    where 'mouse' landed in the verb slot) is rejected — the relation must be a
    verb, not an entity. No meaning decided — a mechanical pick over the
    already-parsed predications, keyed on the already-decided protagonist."""
    cand = [p for p in preds_order
            if len(p) >= 2 and str(p[0]) not in _PROPERTY_RELS
            and _sm_entity_node(sub, str(p[0]).lower()) is None]
    if not cand:
        return None
    for p in cand:
        if _pick_agent(p, entity) == entity and str(p[1]).lower() not in _PRONOUNS:
            return p
    for p in cand:
        if _pick_agent(p, entity) == entity:
            return p
    return cand[0]


def _problem_patient(agent, sub, pred: list, sentence: str, protagonist: str) -> Optional[str]:
    """The obstacle's object for the (transitive) problem clause 'cannot <verb>
    the <object>'. The direct object if it is a clean object-category SmEntity;
    else — when it is an unresolved pronoun ('it') — the first clean object-
    category noun the sentence recognises that is not the protagonist. Unlike
    the general patient this always seeks an object (a 'cannot reach' obstacle
    is transitive), never falling back to an intransitive null."""
    obj = str(pred[2]).lower() if len(pred) > 2 else ""
    if _clean_object(sub, obj):
        return _lemma(obj)
    exclude = {protagonist, _lemma(protagonist)}
    for w in _recognised_nouns(agent, sub, sentence, exclude):
        if _clean_object(sub, w):
            return _noun_lemma(w)
    return None


def _recognised_nouns(agent, sub, sentence: str, exclude: set) -> list[str]:
    words = ct._recognise_words(agent, sentence)
    out = []
    for w in words:
        wl = str(w).lower()
        if wl in _PRONOUNS or wl in exclude or len(wl) < 2:
            continue
        if (_wn_is_noun(wl) or _wn_is_noun(_noun_lemma(wl))
                or _sm_entity_node(sub, wl) is not None):
            out.append(wl)
    return out


def _clean_object(sub, obj: str) -> bool:
    """`obj` is a clean patient noun: a resident SmEntity whose coref category
    is object-like (the situation model's own already-committed classification)
    — this rejects degree words ('higher', category 'unknown') and unresolved
    pronouns while accepting real things ('water'/'pitcher')."""
    if not obj or obj.lower() in _PRONOUNS or "_" in obj:
        return False
    node = None
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("name") == obj.lower():
            node = at
            break
    return bool(node and node.get("coref_category") in _OBJECT_CATS)


def _pick_patient(agent, sub, pred: list, sentence: str, protagonist: str,
                  prefer_plural: bool) -> Optional[str]:
    exclude = {protagonist, _lemma(protagonist)}
    obj = str(pred[2]).lower() if len(pred) > 2 else ""
    # a clean object-category SmEntity is the patient (graph-sourced).
    if _clean_object(sub, obj):
        return _lemma(obj)
    # the solution acts on MANY small units (the INCREMENTAL signal): source
    # the plural recognised noun (pebbles -> pebble) from the sentence's own
    # recognised words. A gerund like 'picking' is excluded (not plural-'s').
    if prefer_plural:
        for w in _recognised_nouns(agent, sub, sentence, exclude):
            lem = _noun_lemma(w)
            if lem != w and w.endswith("s"):     # a real plural noun surface
                return lem
    # otherwise INTRANSITIVE — no patient rather than a spurious one.
    return None


# --------------------------------------------------------------------------- #
#  THE PRODUCTION FACULTY — grounded stub-teacher LanguageWorld + producer,
#  vocabulary grounded from a corpus MECHANICALLY derived from the frames we
#  will render (adapter I/O, no LLM). Reused verbatim; nothing reimplemented.
# --------------------------------------------------------------------------- #
# A GENERIC SVO grammar-grounding pair (no story content — deliberately unrelated
# nouns/verbs) that establishes word order + the determiner for the producer. The
# STORY vocabulary is grounded separately, from a corpus mechanically derived from
# the graph's own predications (see `_build_producer`).
_GRAMMAR_BANK = [
    {"text": "The cat found the mat.", "language": "en",
     "expected_meaning": {"event": "find", "agent": "cat", "patient": "mat", "tense": "past"}},
    {"text": "The dog chased the ball.", "language": "en",
     "expected_meaning": {"event": "chase", "agent": "dog", "patient": "ball", "tense": "past"}},
    # COPULAR clause shape (block 344) — grounds the "X is a Y" order so an is-a /
    # class-membership frame realizes as an ORDERED grammatical clause (not a bag).
    # Teacher-free via teacher_stub; carries the copula 'is' + the subject/complement
    # order grammatical_encoding reads in reverse for a copular goal.
    {"text": "The cat is a mammal.", "language": "en",
     "expected_meaning": {"event": "is", "agent": "cat", "patient": "mammal", "tense": "present"}},
    {"text": "The dog is a mammal.", "language": "en",
     "expected_meaning": {"event": "is", "agent": "dog", "patient": "mammal", "tense": "present"}},
]


def _build_producer(frames: list[dict]):
    """Ground the story vocabulary + SVO grammar (stub teacher, NO LLM) from a
    corpus mechanically derived from `frames`, then hand back a
    `LanguageProduction` over it. donkey = 0 (teacher_stub makes no model
    call)."""
    import substrate_rs as srs
    from domains.language_world import LanguageWorld, teacher_stub
    from domains.language_production import LanguageProduction

    corpus = list(_GRAMMAR_BANK)
    seen = set()
    for fr in frames:
        ev, ag = fr.get("event"), fr.get("agent")
        pt = fr.get("patient")
        key = (ev, ag, pt)
        if not ev or not ag or key in seen:
            continue
        seen.add(key)
        if pt:
            text = "The %s %s the %s." % (ag, ev, pt)
            mean = {"event": ev, "agent": ag, "patient": pt, "tense": "past"}
        else:
            text = "The %s %s." % (ag, ev)
            mean = {"event": ev, "agent": ag, "tense": "past"}
        corpus.append({"text": text, "language": "en", "expected_meaning": mean})

    s = srs._native.Substrate()
    world = LanguageWorld(s, corpus, teacher_stub)
    world.run()
    return LanguageProduction(world)


def _produce(producer, frame: dict) -> Optional[str]:
    """Realise one graph-sourced frame via the production faculty. PAST tense
    (see the module docstring's HONEST tense ledger) — the frame's `event` is
    already the graph's own inflected surface, grounded identically in the
    producer's corpus, so the lexicon-in-reverse realises it verbatim. Returns
    the overt speech with its terminal '.' stripped so it can compose into a
    larger analytical sentence."""
    goal = {"event": frame["event"], "agent": frame["agent"], "intent": "inform"}
    if frame.get("patient"):
        goal["patient"] = frame["patient"]
    r = producer.produce("en", goal)
    overt = (r or {}).get("overt_speech") or ""
    core = overt.rstrip(".!?").strip()
    if not core:
        return None
    # lower the leading capital so it composes mid-sentence ("the crow ...").
    return core[:1].lower() + core[1:]


# --------------------------------------------------------------------------- #
#  CLAIM MODEL — every emitted sentence carries the graph node(s) it reads off.
#  `_emit` REFUSES an ungrounded claim (the graph-checkable discipline).
# --------------------------------------------------------------------------- #
def _emit(claims: list, section: str, sentence: str, kind: str,
          pointers: list, *, fillers: dict = None, connective: str = "",
          note: str = "") -> None:
    ptrs = []
    for p in (pointers or []):
        if p is None:
            continue
        norm = int(str(p).lstrip("#")) if str(p).lstrip("#").isdigit() else p
        if norm not in ptrs:
            ptrs.append(norm)
    if not ptrs:
        raise ValueError(
            "refusing to emit an ungrounded claim (no graph pointer): %r" % sentence)
    if not sentence or not sentence.strip():
        return
    claims.append({
        "section": section, "sentence": sentence.strip(), "kind": kind,
        "produced": kind == "produced", "graph_pointers": ptrs,
        "fillers": fillers or {}, "connective": connective, "note": note,
    })


# --------------------------------------------------------------------------- #
#  SECTION BUILDERS — each reads graph facts + emits grounded claims. The
#  producer renders affirmative frames; framed claims fill fixed connectives
#  from graph content words (negation / abstract trope + theme attribution).
# --------------------------------------------------------------------------- #
_ROLE_ORDER = ("setup", "problem", "solution", "resolution")


def _role_map(roles: list) -> dict:
    out = {}
    for r in roles:
        if r.get("role") and r.get("role") not in out:
            out[r["role"]] = r
    return out


def _frames_for(agent, graph: dict, entity: str, roles_by: dict,
                preds: list[list], sentences: list) -> dict:
    """Build the graph-sourced frames for the affirmative-renderable roles
    (setup / solution / resolution) + the goal. Returns {role_or_key: frame}
    with each frame carrying `_pointers` for the claim it will ground."""
    sub, _ = _resolve(agent)
    frames: dict[str, dict] = {}
    for role in ("setup", "solution", "resolution"):
        r = roles_by.get(role)
        if r is None:
            continue
        order = r.get("order")
        if order is None or order >= len(preds):
            continue
        # pick the role sentence's key event predication (protagonist-keyed)
        pred = _select_pred(sub, preds[order], entity)
        if pred is None:
            continue
        # THE FIX: the raw relation token IS ALREADY the sentence's own
        # inflected surface ('dropped'/'rose'/'took'/'ate') -- the SAME string
        # situation_model_reader stamps onto its SmEvent node's `surface` attr
        # for this exact predication (verified: SmEvent{verb:canon,
        # surface:rel} where rel is this same textbase relation slot). Do NOT
        # lemmatise it for rendering -- that discards the graph's own grounded
        # tense and is what produced the bare 'drop'/'rise'/'take' bug. An
        # irregular whose own surface coincides with its lemma ('found') is
        # unaffected either way -- disclosed, not hidden.
        ev = str(pred[0]).lower()
        ag = _pick_agent(pred, entity)
        sentence = sentences[order] if order < len(sentences) else ""
        pt = _pick_patient(agent, sub, pred, sentence, entity,
                           prefer_plural=(role == "solution"))
        frames[role] = {"event": ev, "agent": ag, "patient": pt,
                        "_pointers": [_role_node_id(sub, entity, order, role),
                                      _discourse_node_id(sub, order)],
                        "_order": order}
    # GOAL clause (the remedy achieved): read off the goal record's remedy.
    # The remedy word is SCHEMA-supplied (need_remedy_* -> "drink"/"eat"), not
    # a textbase predication, so it carries no relation-slot surface of its
    # own. Recover one from the RESOLUTION sentence's own recognised words
    # (graph-sourced text scan) when the text holds an inflected form of it
    # ('ate' for the mouse fable); else the bare lemma is the only realisable
    # word -- an honest residual (the crow fable's own text for 'drink' is
    # itself the bare modal complement "...he could drink"; no 'drank' token
    # exists anywhere in the source to recover).
    remedy = None
    for g in graph.get("goal") or []:
        if g.get("minted") and g["gap"]["entity"] == entity:
            remedy = (g.get("supplies") or {}).get("remedy")
    if remedy:
        lemma = _lemma(remedy)
        surface = None
        res_role = roles_by.get("resolution")
        if res_role is not None:
            r_order = res_role.get("order")
            if r_order is not None and r_order < len(sentences):
                words = ct._recognise_words(agent, sentences[r_order])
                surface = _verb_surface_from_words(words, lemma)
        frames["goal"] = {"event": surface or lemma, "agent": entity, "patient": None,
                          "_pointers": [_sm_entity_node(sub, entity)],
                          "_surface_used": surface is not None}
    return frames


def _build_summary(agent, graph: dict, entity: str, roles_by: dict,
                   preds: list[list], produced: dict, frames: dict) -> list:
    sub, _ = _resolve(agent)
    claims: list = []
    # 1. protagonist + need (framed: the need is graph state on the SmEntity /
    #    goal record; "follows a / which is" is the fixed connective).
    need = None
    goal_ptr = None
    for g in graph.get("goal") or []:
        if g.get("minted") and g["gap"]["entity"] == entity:
            need = g["gap"].get("need_attr")
            goal_ptr = g["gap"].get("node")
    ent_ptr = _sm_entity_node(sub, entity)
    if need:
        _emit(claims, "SUMMARY",
              "The story follows a %s, which is %s." % (entity, need),
              "framed", [ent_ptr, goal_ptr],
              fillers={"protagonist": entity, "need": need},
              connective="The story follows a ___, which is ___.",
              note="protagonist + need-state read off the SmEntity/goal node")
    # 2. central obstacle (framed negation): the top-centrality event IS the
    #    problem role's sentence; fill agent/event/patient from its predication.
    prob = roles_by.get("problem")
    ranking = (graph.get("centrality") or {}).get("ranking") or []
    top_node = ranking[0]["node"] if ranking else None
    if prob is not None:
        order = prob.get("order")
        clause, fillers = _problem_clause(agent, sub, graph, preds, order, entity)
        if clause is not None:
            _emit(claims, "SUMMARY",
                  "Its central difficulty, the most causally connected event, "
                  "is that %s." % clause,
                  "framed",
                  [top_node, _role_node_id(sub, entity, order, "problem"),
                   _discourse_node_id(sub, order)],
                  fillers=fillers,
                  connective="Its central difficulty ... is that the ___ cannot ___ the ___.",
                  note="negation is fixed frame; content words from the problem predication; "
                       "central-event claim from the causal-weighted centrality ranking")
    # 3. resolution (produced affirmative; falls back to the goal-met clause
    #    when the resolution sentence's own predication is unusable).
    res, goalc, rptrs = _resolution_clause(sub, entity, roles_by, produced, frames)
    if res is not None:
        sent = "In the end, %s" % res
        if goalc is not None:
            sent += ", and %s" % goalc
        sent += "."
        _emit(claims, "SUMMARY", sent, "produced", rptrs,
              fillers={"resolution": res, "goal": goalc},
              connective="In the end, ___(, and ___).",
              note="event clauses realised by the production faculty")
    return claims


def _build_structure(agent, graph: dict, entity: str, roles_by: dict,
                     preds: list[list], produced: dict, frames: dict) -> list:
    sub, _ = _resolve(agent)
    claims: list = []
    for role in _ROLE_ORDER:
        r = roles_by.get(role)
        if r is None:
            continue
        order = r.get("order")
        role_ptr = _role_node_id(sub, entity, order, role)
        disc_ptr = _discourse_node_id(sub, order)
        if role == "problem":
            clause, fillers = _problem_clause(agent, sub, graph, preds, order, entity)
            if clause is None:
                continue
            fillers = {"role": role, **fillers}
            _emit(claims, "STRUCTURE",
                  "The %s is that %s." % (role, clause),
                  "framed", [role_ptr, disc_ptr],
                  fillers=fillers,
                  connective="The ___ is that the ___ cannot ___ the ___.",
                  note="role name from the NarrativeRole node; negation fixed; "
                       "content words from the role predication")
            continue
        if role == "resolution":
            res, goalc, rptrs = _resolution_clause(sub, entity, roles_by, produced, frames)
            if res is None:
                continue
            sent = "In the %s, %s" % (role, res)
            if goalc is not None:
                sent += ", and %s" % goalc
            sent += "."
            _emit(claims, "STRUCTURE", sent, "produced", rptrs,
                  fillers={"role": role, "resolution": res, "goal": goalc},
                  connective="In the ___, ___(, and ___).",
                  note="role name from the NarrativeRole node; clause realised by the production faculty")
            continue
        core = produced.get(role)
        if core is None:
            continue
        lead = {"setup": "In the %s, %s.",
                "solution": "The %s comes when %s."}[role]
        sent = lead % (role, core)
        _emit(claims, "STRUCTURE", sent, "produced", [role_ptr, disc_ptr],
              fillers={"role": role, "clause": core},
              connective=lead.replace("%s", "___"),
              note="role name from the NarrativeRole node; clause realised by the production faculty")
    return claims


def _problem_clause(agent, sub, graph: dict, preds: list, order, entity: str):
    """The (negated) obstacle clause 'the <agent> cannot <verb>[ the <object>]',
    content words from the problem role's own predication (graph-sourced);
    negation is fixed frame. Returns (clause_str|None, fillers)."""
    if order is None or order >= len(preds):
        return None, {}
    pred = _select_pred(sub, preds[order], entity)
    if pred is None:
        return None, {}
    sentences = graph.get("sentences") or []
    sentence = sentences[order] if order < len(sentences) else ""
    ev = _verb_lemma(pred[0])
    ag = _pick_agent(pred, entity)
    pt = _problem_patient(agent, sub, pred, sentence, entity)
    if pt:
        clause = "the %s cannot %s the %s" % (ag, ev, pt)
    else:
        clause = "the %s cannot %s" % (ag, ev)
    return clause, {"agent": ag, "event": ev, "patient": pt}


def _resolution_clause(sub, entity: str, roles_by: dict, produced: dict, frames: dict):
    """The resolution's produced clause + the goal-met clause, with pointers.
    When the resolution sentence's own predication is unusable (a degenerate
    parse), the goal-met clause (the remedy achieved — 'the crow drinks')
    stands in for it. Returns (res_clause|None, goal_clause|None, pointers)."""
    res_clause = produced.get("resolution")
    goal_clause = produced.get("goal")
    r = roles_by.get("resolution")
    ptrs = []
    if r is not None:
        ptrs += [_role_node_id(sub, entity, r.get("order"), "resolution"),
                 _discourse_node_id(sub, r.get("order"))]
    if res_clause is not None:
        ptrs += list(frames.get("resolution", {}).get("_pointers") or [])
        if goal_clause is not None:
            ptrs += list(frames.get("goal", {}).get("_pointers") or [])
        return res_clause, goal_clause, ptrs
    if goal_clause is not None:                # resolution unusable -> goal stands in
        ptrs += list(frames.get("goal", {}).get("_pointers") or [])
        return goal_clause, None, ptrs
    return None, None, ptrs


def _build_technique(agent, graph: dict, entity: str, tropes: list) -> list:
    sub, _ = _resolve(agent)
    claims: list = []
    for t in tropes:
        name = t.get("name")
        label = (t.get("label") or {}).get("name") or name
        covered = t.get("covered_tokens") or []
        # mechanism descriptor derived from the trope's OWN covered token names
        # (TROPE_INDIRECT -> "indirect"), graph-sourced, never a literary phrase.
        descriptors = [str(tok).split("_", 1)[-1].lower() for tok in covered]
        desc_str = " and ".join(descriptors) if descriptors else "structural"
        node = t.get("_node_obj")
        ev_ptrs = [e["node"] for e in tt.trope_evidence(agent, node)] if node is not None else []
        ptrs = [_v(node) if node is not None else None] + ev_ptrs
        _emit(claims, "TECHNIQUE",
              "Through its %s structure, the story instantiates %s (%s)."
              % (desc_str, label, name),
              "framed", ptrs,
              fillers={"descriptors": descriptors, "label": label, "name": name},
              connective="Through its ___ structure, the story instantiates ___ (___).",
              note="trope label + name from the Trope node; descriptor from its covered tokens; "
                   "evidence pointers are the NarrativeRole/TropeEvidence nodes that earned it")
    return claims


def _build_theme(agent, graph: dict, entity: str, theme: dict, tropes: list) -> list:
    sub, _ = _resolve(agent)
    claims: list = []
    if not theme or not theme.get("minted"):
        return claims
    node = None
    ttv = tt._existing_theme(sub, entity)
    node = _v(ttv) if ttv is not None else None
    lines = theme.get("lines") or []
    trope_ptrs = [t.get("_node_obj") and _v(t["_node_obj"]) for t in tropes]
    body = " ".join(str(l) for l in lines)
    _emit(claims, "THEME",
          "Read from the trope(s) it instantiates, the story's theme is: %s" % body,
          "framed", [node] + trope_ptrs,
          fillers={"lines": lines},
          connective="Read from the trope(s) it instantiates, the story's theme is: ___",
          note="theme lines are the Theme node's own held `lines` (a seed-authored gloss, graph data), "
               "surfaced verbatim; pointers are the Theme node + the Trope nodes that express it")
    return claims


# --------------------------------------------------------------------------- #
#  THE DRIVER.
# --------------------------------------------------------------------------- #
def produce_analysis(agent, text: Optional[str] = None, *,
                     graph: Optional[dict] = None, window: int = 2) -> dict:
    """Render a short literary analysis of `text` (or an already-built
    comprehension `graph`) from the agent's comprehension graph. Every content
    word of every sentence is read off a graph node; affirmative event clauses
    are realised by the production faculty; negation + abstract trope/theme
    attribution are fixed connectives with graph-sourced fillers. Returns
    {entity, text, sections, claims, claim_map, produced_count, framed_count}.

    GOAL-DRIVEN (2026-07, the migration): this function's OLD section-marshalling
    loop (per entity: _build_summary(); _build_structure(); _build_technique();
    _build_theme(), then assemble by section order) is DELETED. It now seeds a
    `produce_analysis` Goal and runs the comprehension->production FIXPOINT
    (`reading_drive`, seeds/literary_analysis_driving.json): each SECTION is its
    OWN stage fired by a rule (no imposed order between the four), and the section
    builders below are REUSED unchanged as those stages' shims. This function is a
    thin world-adapter: seed the goal, PUMP, then read the emitted claims back out
    and assemble section-ordered prose (mechanical I/O — the section order is a
    read-off, not a faculty sequence).

    GRAPH-CHECKABLE: `claim_map` maps every emitted sentence to its graph
    pointers; a claim with no pointer is refused (`_emit`)."""
    from domains import reading_drive as rd
    if graph is not None:
        bb = rd.run_produce_over_graph(agent, graph)          # produce over a built graph
    else:
        if text is None:
            raise ValueError("produce_analysis needs `text` or a prebuilt `graph`")
        bb = rd.run_reading_flow(agent, text, report="analysis", window=window)

    all_claims = bb.get("claims") or []
    sections = bb.get("sections") or {}
    # per-entity list, re-read off the graph (the old bb['_produce_ctx'] cache
    # is gone — each produce stage re-derives its contexts from nodes): the arc
    # entities that carried an affirmative-renderable role set.
    per_entity = []
    for arc in rd._narrative_arc_from_graph(agent)["arcs"]:
        entity = arc.get("entity")
        if _role_map([r for r in arc.get("roles") or [] if r.get("role")]) and entity not in per_entity:
            per_entity.append(entity)

    # assemble the prose (fixed section headers — the ONLY non-graph text, and
    # not a claim: headers carry no story content). The section ORDER is a
    # mechanical read-off of already-emitted Claim sentences, not a faculty run.
    order = ["SUMMARY", "STRUCTURE", "TECHNIQUE", "THEME"]
    titles = {"SUMMARY": "Summary", "STRUCTURE": "Narrative structure",
              "TECHNIQUE": "Technique", "THEME": "Theme"}
    parts: list[str] = []
    for sec in order:
        sents = sections.get(sec)
        if not sents:
            continue
        parts.append(titles[sec] + ". " + " ".join(sents))
    prose = "\n\n".join(parts)

    claim_map = {c["sentence"]: {"pointers": c["graph_pointers"], "kind": c["kind"],
                                 "section": c["section"], "fillers": c["fillers"],
                                 "connective": c["connective"], "note": c["note"]}
                 for c in all_claims}

    return {
        "entity": per_entity[0] if per_entity else None,
        "entities": per_entity,
        "text": prose,
        "sections": sections,
        "claims": all_claims,
        "claim_map": claim_map,
        "produced_count": sum(1 for c in all_claims if c["produced"]),
        "framed_count": sum(1 for c in all_claims if not c["produced"]),
    }


def verify_grounding(agent, analysis: dict) -> dict:
    """GRAPH-CHECKABLE verifier: assert every emitted sentence has >=1 pointer
    AND every pointer resolves to a resident graph node. Returns
    {ok, checked, unresolved:[...]} — a pure graph read, no decision."""
    sub, _ = _resolve(agent)
    resident = set()
    for nid in range(0, 0):   # placeholder; we resolve per-pointer below
        pass
    unresolved = []
    checked = 0
    for c in analysis.get("claims") or []:
        if not c.get("graph_pointers"):
            unresolved.append((c["sentence"], "NO_POINTER"))
            continue
        for p in c["graph_pointers"]:
            checked += 1
            if not _node_exists(sub, p):
                unresolved.append((c["sentence"], p))
    return {"ok": not unresolved, "checked": checked, "unresolved": unresolved}


def _node_exists(sub, nid) -> bool:
    try:
        from substrate_rs import NodeID
        node = sub.node(NodeID(int(nid)) if not hasattr(nid, "value") else nid)
        return node is not None
    except Exception:
        try:
            return sub.node(nid) is not None
        except Exception:
            return False


__all__ = ["produce_analysis", "verify_grounding"]
