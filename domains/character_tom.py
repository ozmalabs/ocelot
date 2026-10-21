"""character_tom — CHARACTER THEORY OF MIND: nested belief-worlds + goals.

situation_model_reader.py builds a SITUATION MODEL (the state of the STORY
WORLD: the glass is now on the floor, broken) and coref_entities.py wires
coreference into it, but neither represents what a CHARACTER believes/wants/
knows — a propositional attitude. domains/psychology.py has a real belief/
desire/intention/knowledge taxonomy, but it is aimed at the AGENT's own mind
(and its interlocutor's), not narrative characters; reading_collapse's
construction codebook (domain_data/reading_constructions.json) has no propositional-
attitude construction, so "Sally thinks the ball is in the basket" has nowhere
to ground — the sentence decodes (if at all) as a bare copular definitional
clause, losing "thinks" entirely.

THE CONSTRUCTION. 'SUBJ ATTITUDE-VERB COMPLEMENT' is a ShapeSignature
(domain_data/character_tom.json: `propositional_attitude`, signature [["ATTITUDE"]])
in the SAME codebook designation/possession live in — recognised by the SAME
`reflective_faculty.compose_design_for_goal` ShapeDecode Term reading_collapse
already uses (reused here via `rc._decode`/`rc._winner`, not reimplemented).
The ATTITUDE marker-class (believes/thinks/knows/wants/hopes/fears/wishes/
doubts) mirrors domain_data/reading_constructions.json's COS class exactly: it is
NOT wired into reading_collapse's reading-time `_SKELETON` set (an attitude
verb sitting in a clause's main-verb slot would otherwise collide with the
clause's OTHER markers — the embedded "is" of "...the ball IS in the basket"
— and corrupt the decode of ordinary clauses). Instead this module runs its
OWN scan over the clause's recognised words (mirroring
situation_model_reader.cos_membership's structure exactly): a SEED member
resolves directly; an UNSEEN attitude verb (suspects/presumes/...) JOINS the
class by ADJACENCY — reusing reading_collapse._wordnet_nearness, the SAME
WordNet path-similarity signal COS/DESIGNATE/POSSESS use — inheriting its
nearest anchor's `flavor` (belief/desire/knowledge). Only THEN is the
[["ATTITUDE"]] skeleton handed to the ShapeDecode collapse, which reads off
the `propositional_attitude` construction as its own verdict (fit=1, zero
residual) — the DECISION that carries meaning is the collapse's, never a
Python if/else on the verb surface.

THE NESTED WORLD. The COMPLEMENT (everything after the attitude verb) is
handed to reading_collapse.read_clause UNCHANGED (write=False, learn=False —
this module never grows the shared construction codebook as a side effect of
reading a character's mental content) to ground it as a predication exactly
the way any other clause grounds. For a BELIEF/KNOWLEDGE attitude, that
predication is minted as a FRESH nested SmEntity (never deduped against the
real-world SmEntity of the same name — see `_nested_entity`) linked from the
character's own (real, shared) SmEntity via a `belief_world` edge, so a false
belief ("Sally thinks the ball is in the basket") and the real world ("the
ball is in the box") coexist as two DISTINCT graph nodes rather than one
overwriting the other. For a DESIRE attitude, the complement grounds the
character's GOAL: an SmEvent{verb:'want'} carrying `idx_protagonist`/
`idx_intentionality` — the Zwaan & Radvansky intentionality index
situation_model_reader's five-index scheme has always left as a residual
(nothing fills it until now) — plus a direct `goal` attr on the character's
SmEntity for a one-hop query. Both flavors additionally edge the grounded
node/event to the matching psychology.py Concept (belief/desire/knowledge,
installed by the `psychology` seed) via `is_a` — REUSING psychology's node
types, never forking a parallel taxonomy.

THE COMPLEMENT-KIND GATE. WordNet path-similarity is coarse: 'have' clears the
ATTITUDE class's adjacency threshold to 'know' (nearness 0.5), so a plain
possession statement ("the pitcher... had a narrow neck") would otherwise mint
a BOGUS knowledge belief-world from a bare NOUN complement. The fix mirrors
the slot-gate discipline DESIGNATE/POSSESS already use: a BELIEF/KNOWLEDGE
attitude fires ONLY over a PROPOSITIONAL complement — one that grounds as its
own clause/event predication ("thinks [the ball is in the basket]") — never a
bare NOMINAL one ("had [a narrow neck]"). DESIRE keeps the noun-GOAL path
valid regardless ("wanted water" is a real goal, not a proposition).
`_complement_is_propositional` decides this GRAPH-NATIVELY: the complement is
re-grounded (the SAME read-only `rc.read_clause` call `_ground_attitude_
complement` uses) and its OWN shape is read off the held nominal faculty
(`consumption_quality.is_nominal`) — never a Python branch on the attitude
verb's surface ('have' vs 'think'). `ingest_attitude_sentence` applies this
gate BEFORE minting anything, so a gated sentence mints no subject entity, no
belief-world, nothing — it falls straight through to the ordinary factual
reading path, exactly like a sentence with no attitude verb at all.

A FACTUAL sentence (no attitude verb found by the scan) is NOT this module's
business: `read_character_tom` falls through to the UNCHANGED situation-model
reading path (reading_scope.read_scope / reading_collapse.read_clause +
situation_model_reader.ingest_predication, exactly as
situation_model_reader.read_into_situation_model and
coref_entities.read_into_situation_model already do) so it updates the ACTUAL
world, not a character's belief-world.

ARCHITECTURE (CLAUDE.md). The construction WINNER is the ShapeDecode
collapse's verdict (reused, not reimplemented); the ATTITUDE class membership
test mirrors the existing COS class's join-by-adjacency mechanism (reused
WordNet signal, reused `_join_class` graph write); the nested belief-world and
the goal are graph NODES (SmEntity / SmEvent), not a Python dict. This module
only (a) scans recognised words for the class boundary (mechanical, mirrors
`cos_membership`), (b) hands the two spans to the held decode + the held
clause reader, (c) mints the nested/goal graph structure the seeded taxonomy
(psychology.py) and the seeded situation model (situation_model_reader.py)
already define shapes for. No `import re`.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import instruction_reading as ir
from domains import reading_collapse as rc
from domains import reading_scope as rs
from domains import situation_model_reader as smr

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_FILE = os.path.join(_ROOT, "domain_data", "character_tom.json")


# --------------------------------------------------------------------------- #
#  resolution + seed install (mechanical adapter I/O — the same idiom every
#  domains/*.py module in this codebase uses).
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


def ensure_seeds(agent) -> None:
    """Idempotently install everything this module reuses (reading_collapse's
    codebook, situation_model + event_reasoning, psychology's belief/desire/
    knowledge Concepts) and this module's OWN seed (the ATTITUDE MarkerClass +
    the `propositional_attitude` ShapeSignature). Guarded by a Seed sentinel,
    the SAME idempotency idiom situation_model_reader.ensure_seeds /
    reading_collapse.ensure_codebook use."""
    from substrate.seed_loader import manifest_for
    from domains.reflective_faculty import _ensure_seed_chain
    sub, native, ag_node = _resolve(agent)
    rc.ensure_codebook(agent)                      # COP/DET/.../DESIGNATE/POSSESS + the codebook
    smr.ensure_seeds(agent)                        # situation_model + event_reasoning
    # PROPOSITION-CAPTURE (blind-spot closure R9, 2026-07-12): the rule that
    # marks a Level-2 belief/goal node ELIGIBLE for full-proposition
    # rendering (seeds/proposition_capture.json) — the ablatable DECISION
    # surface; `_nested_entity`/`_ground_attitude_complement`'s own mint
    # always stamps the raw data regardless of whether this rule is present.
    _ensure_seed_chain(sub, native, ag_node, ("proposition_capture",))
    if not smr._has_concept(sub, "belief"):
        try:
            native.load_seed_manifest(manifest_for("psychology"), ag_node)
        except Exception:
            pass
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "character_tom":
            return
    with open(_SEED_FILE) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "character_tom", "version": manifest.get("version", "1.0.0")})


def _attitude_node(sub):
    for n in sub.nodes("MarkerClass"):
        if sub.node(n)["attrs"].get("cls") == "ATTITUDE":
            return n
    return None


def _concept_node(sub, name: str):
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


# --------------------------------------------------------------------------- #
#  ATTITUDE MEMBERSHIP — mirrors situation_model_reader.cos_membership exactly,
#  for the ATTITUDE class instead of COS.
# --------------------------------------------------------------------------- #
def attitude_membership(agent, verb: str) -> dict:
    """Is `verb` a propositional-attitude verb? Returns {lemma, attitude,
    flavor, nearness, nearest, joined, via}. A SEED member resolves directly
    (via='member'); an unseen verb JOINS by adjacency — reusing
    rc._wordnet_nearness (the SAME WordNet path-similarity signal COS/
    DESIGNATE/POSSESS use) to the class anchor >= threshold, inheriting its
    nearest anchor's `flavor`, and is placed into the class live (rc._join_class)
    so it is a member thereafter. Below threshold -> not an attitude verb."""
    ensure_seeds(agent)
    sub, _, _ = _resolve(agent)
    lemma = smr._lemma(verb)
    node = _attitude_node(sub)
    if node is None:
        return {"lemma": lemma, "attitude": False, "flavor": None, "nearness": 0.0,
                "nearest": None, "joined": False, "via": None}
    at = sub.node(node)["attrs"]
    forms = [str(f).lower() for f in (at.get("forms") or [])]
    flavor_map = dict(at.get("flavor") or {})
    if lemma in forms:
        return {"lemma": lemma, "attitude": True, "flavor": flavor_map.get(lemma, "belief"),
                "nearness": 1.0, "nearest": lemma, "joined": False, "via": "member"}
    anchors = [str(a).lower() for a in (at.get("adjacency_anchor") or [])]
    try:
        thr = float(at.get("adjacency_threshold", 0.5))
    except (TypeError, ValueError):
        thr = 0.5
    score, member = rc._wordnet_nearness(lemma, anchors)
    if member is not None and score >= thr:
        rc._join_class(sub, node, lemma, score, member)
        flavor = flavor_map.get(member, "belief")
        flavor_map[lemma] = flavor
        try:
            sub.set_attr(node, "flavor", flavor_map)
        except Exception:
            pass
        return {"lemma": lemma, "attitude": True, "flavor": flavor,
                "nearness": float(score), "nearest": member, "joined": True,
                "via": "adjacency"}
    return {"lemma": lemma, "attitude": False, "flavor": None, "nearness": float(score),
            "nearest": member, "joined": False, "via": None}


def _find_attitude_marker(agent, words: list[str]) -> Optional[tuple]:
    """Scan `words` (a recognised clause) left-to-right for the FIRST word that
    is an ATTITUDE-class verb: skip anything ALREADY claimed by a DIFFERENT
    MarkerClass (COP/DET/COS/...) — a word already classified elsewhere is not
    a fresh attitude candidate, the same discipline that keeps COS's
    membership check from firing on a word the reading skeleton already owns
    — require it sit in the MAIN-VERB slot (held POS check,
    `ir.is_verb_headed`, mirroring POSSESS's 'other'/main-verb distributional
    gate) with a non-empty subject span before it and a non-empty complement
    span after it. Returns (index, membership) or None (no attitude verb —
    the discriminative, factual case).

    BUGFIX (Wave: interlocutor-as-modeled-participant, task 3): the guard
    used to read `lex.get(w.lower()) is not None`, which ALSO excludes a word
    the ATTITUDE class ITSELF already owns — and the class's own SEED forms
    (believe/think/know/want/hope/fear/wish/doubt, domain_data/character_tom.json)
    are registered into this SAME shared marker lexicon at install time. That
    silently broke every BASE-FORM first-person self-report ("I think X" /
    "I want Y") while a conjugated third-person form ("Sally thinks X")
    happened to slip through only because "thinks" (unlike "think") isn't
    itself a literal lexicon entry — an accident, not the intended
    discrimination. The guard now excludes a word ONLY when a DIFFERENT class
    owns it; a word the ATTITUDE class itself owns is exactly what this scan
    is looking for."""
    sub, _, _ = _resolve(agent)
    lex = rc._marker_lexicon(sub)
    for i, w in enumerate(words):
        if i == 0 or i == len(words) - 1:
            continue
        cls = lex.get(w.lower())
        if cls is not None and cls != "ATTITUDE":
            continue
        if not ir.is_verb_headed(w):
            continue
        mem = attitude_membership(agent, w)
        if mem["attitude"]:
            return i, mem
    return None


# --------------------------------------------------------------------------- #
#  THE CONSTRUCTION DECODE — the collapse, reused verbatim (rc._decode /
#  rc._winner), never reimplemented.
# --------------------------------------------------------------------------- #
def decode_attitude_construction(agent, subject_words: list, complement_words: list) -> dict:
    """Decode the [["ATTITUDE"]] skeleton against the held construction
    codebook via reading_collapse's OWN ShapeDecode call
    (`reflective_faculty.compose_design_for_goal`, reached through
    `rc._decode`/`rc._winner` exactly as reading_collapse.read_clause reads its
    own decode's verdict). The construction the decode picks — never a Python
    if/else on the attitude verb's surface — is `propositional_attitude` (the
    ONE held construction whose signature is exactly [["ATTITUDE"]])."""
    ensure_seeds(agent)
    skeleton = [["ATTITUDE"]]
    res = rc._decode(agent, skeleton)
    name, fit = rc._winner(res)
    residual = [list(r) for r in (res.get("residual") or [])]
    return {"skeleton": skeleton, "roles": [" ".join(subject_words), " ".join(complement_words)],
            "construction": name, "shape_fit": fit, "residual": residual}


# --------------------------------------------------------------------------- #
#  span cleanup (DET-stripping) — mechanical, reuses rc's own marker lexicon +
#  normaliser; no regex.
# --------------------------------------------------------------------------- #
def _clean_span(agent, words: list[str]) -> str:
    sub, _, _ = _resolve(agent)
    lex = rc._marker_lexicon(sub)
    kept = [w for w in words if lex.get(w.lower()) not in ("DET", "TO")]
    if not kept:
        kept = list(words)
    return rc._norm(" ".join(kept))


# --------------------------------------------------------------------------- #
#  COMPLEMENT-KIND GATE — a BELIEF/KNOWLEDGE attitude fires ONLY over a
#  PROPOSITIONAL complement ('thinks [the ball is in the basket]'), never a
#  bare NOMINAL one ('had [a narrow neck]'); DESIRE keeps its noun-GOAL path
#  regardless ('wanted water' is a valid goal). Mirrors the slot-gate
#  discipline POSSESS/DESIGNATE already use (a marker only fires in the slot
#  shape its construction requires) — here the gate is on the COMPLEMENT's
#  own grounded shape, read off the held nominal faculty
#  (consumption_quality.is_nominal), never a Python check on the attitude
#  verb's surface.
# --------------------------------------------------------------------------- #
def _complement_is_propositional(agent, comp_words: list) -> bool:
    """Does the complement ground as a PROPOSITION (a clause/event predication)
    rather than a NOMINAL? The complement is re-grounded by the UNCHANGED
    rc.read_clause (write=False, learn=False — a read-only probe, no side
    effect) exactly as `_ground_attitude_complement` does; the KIND decision is
    read off that grounding, never the attitude verb:

      * preds POPULATED — a predication was recognised. Its RELATION HEAD is
        checked against the held nominal faculty: a genuine relational
        predicate (`is_a`/`in`/`as`/`has_property`/...) is NOT a nominal, so
        the predication is propositional. A relation head that IS a nominal
        ('neck' — reading_collapse's coarse VERB-marker lexicon occasionally
        admits a noun's rare verb sense, e.g. 'neck' meaning 'kiss', mis-
        parsing a coordinated noun-phrase-plus-clause complement as a verb
        clause) means the 'predication' is really a mis-grounded noun phrase,
        not a clause — NOT propositional.
      * preds EMPTY — no clause recognised at all. Fall back to is_nominal on
        the complement's OWN cleaned surface: a bare noun phrase ('a narrow
        neck') is NOT propositional; anything else is an honest UNPARSED
        proposition (no deeper parse available, but not nominal-shaped
        either) — propositional.
    """
    from domains import consumption_quality as cq
    comp_read = rc.read_clause(agent, comp_words, write=False, learn=False)
    preds = comp_read.get("predications") or []
    if preds:
        rel = str(preds[0][0])
        return not cq.is_nominal(rel)
    surface = _clean_span(agent, comp_words)
    return not cq.is_nominal(surface)


# --------------------------------------------------------------------------- #
#  NESTED BELIEF-WORLD / GOAL grounding — graph nodes, never a Python dict.
# --------------------------------------------------------------------------- #
def _scoped_name(character_name: str, referent: str) -> str:
    """A nested SmEntity's OWN `name` attr must NEVER collide with the shared
    real-world namespace situation_model_reader._entity searches by plain
    name (it iterates ALL SmEntity nodes, nested or not) — else a later
    FACTUAL sentence about the same referent ('the ball is in the box') would
    find and mutate the character's NESTED node instead of minting/updating a
    real one, silently merging the two worlds. Scoping the name per
    (character, referent) makes that collision structurally impossible; the
    real referent is kept separately as `referent` for querying."""
    return "%s#%s_belief" % (referent, character_name)


def _nested_entity(agent, character_ent, character_name: str, flavor: str, pred: list,
                   *, verbatim: Optional[str] = None):
    """Mint a FRESH SmEntity for the complement's subject, scoped to this
    character's belief-world — deliberately NOT deduped against the real-world
    SmEntity of the same referent (situation_model_reader._entity's global
    name index is for the ACTUAL world only), so 'ball' inside Sally's belief
    and 'ball' in reality are two DISTINCT nodes that can hold conflicting
    state.

    PROPOSITION-GRAIN (blind-spot closure R9, 2026-07-12): alongside the
    head-grain `referent` (kept, unchanged — every existing reader of it is
    byte-identical), the FULL predication triple the reader's own clause
    parse already produced is stamped as `proposition` (json [rel, a0, a1])
    and, when the caller supplies the complement's verbatim span (`verbatim`
    — never re-derived here, just plumbed through), as `proposition_span` —
    the natural-language phrase a renderer can use instead of the bare head.
    A fresh `is_attitude_level2` self-edge (the SAME single-node self-match
    idiom `situation_model_reader._entity`'s `is_entity` and
    `reading_drive`'s `is_sentence_parse` already use) lets the
    `proposition_capture` seed rule mark this node ELIGIBLE for full-
    proposition rendering — the rule is the DECISION surface an ablation can
    remove; this mint is mechanical data I/O regardless of whether that rule
    is present."""
    sub, native, _ = _resolve(agent)
    rel, a0 = pred[0], pred[1]
    a1 = pred[2] if len(pred) > 2 else None
    attrs = {"name": _scoped_name(character_name, a0),
             "referent": a0, "nested": 1,
             "belief_holder": character_name,
             "flavor": flavor, "predicate": rel,
             "proposition": json.dumps(pred)}
    if verbatim is not None:
        attrs["proposition_span"] = verbatim
    nested = sub.add_node("SmEntity", attrs)
    if a1 is not None:
        sub.set_attr(nested, a1, 1)
    smr._edge(native, character_ent, "belief_world", nested)
    smr._edge(native, nested, "is_attitude_level2", nested)
    from domains.tom_meta_shape import project_character_tom_node
    project_character_tom_node(agent, nested)
    flavor_concept = _concept_node(sub, flavor)
    if flavor_concept is not None:
        smr._edge(native, nested, "is_a", flavor_concept)
    return nested


def _ground_attitude_complement(agent, character_ent, character_name: str,
                                flavor: str, comp_words: list, *, t: int) -> dict:
    """Ground the COMPLEMENT. The complement clause is read by the UNCHANGED
    reading_collapse.read_clause (write=False so it never lands on the shared
    graph directly, learn=False so a character's mental content never grows
    the shared construction codebook as a side effect). BELIEF/KNOWLEDGE mints
    a nested proposition; DESIRE mints the character's GOAL (the
    intentionality index)."""
    sub, native, _ = _resolve(agent)
    comp_read = rc.read_clause(agent, comp_words, write=False, learn=False)
    preds = comp_read.get("predications") or []
    # VERBATIM SPAN (R9): the complement's own words, joined as spoken — NOT
    # `_clean_span`'s DET-stripped/underscored concept-token form (that stays
    # the head-grain `referent`'s job). Plumbed through unchanged to whichever
    # branch mints the Level-2 node; never re-derived per-branch.
    verbatim = " ".join(comp_words) if comp_words else None
    out: dict[str, Any] = {"complement_construction": comp_read.get("construction"),
                           "complement_predications": preds}

    if flavor in ("belief", "knowledge"):
        if preds:
            nested = _nested_entity(agent, character_ent, character_name, flavor, preds[0],
                                    verbatim=verbatim)
            out["belief_world"] = smr._v(nested)
            out["belief_world_state"] = {k: v for k, v in sub.node(nested)["attrs"].items()
                                          if k not in ("name", "referent")}
        else:
            # a bare-nominal / unparsed complement — the residual proposition is
            # the complement's own cleaned surface (honest: no deeper parse).
            content = _clean_span(agent, comp_words)
            attrs = {"name": _scoped_name(character_name, content),
                     "referent": content, "nested": 1,
                     "belief_holder": character_name, "flavor": flavor}
            if verbatim is not None:
                attrs["proposition_span"] = verbatim
            nested = sub.add_node("SmEntity", attrs)
            smr._edge(native, character_ent, "belief_world", nested)
            smr._edge(native, nested, "is_attitude_level2", nested)
            from domains.tom_meta_shape import project_character_tom_node
            project_character_tom_node(agent, nested)
            flavor_concept = _concept_node(sub, flavor)
            if flavor_concept is not None:
                smr._edge(native, nested, "is_a", flavor_concept)
            out["belief_world"] = smr._v(nested)
            out["belief_world_state"] = {"referent": content}
    elif flavor == "desire":
        if preds and len(preds[0]) > 1:
            content = preds[0][1]
        else:
            content = _clean_span(agent, comp_words)
        event = sub.add_node("SmEvent", {"verb": "want", "surface": "want",
                                         "active": 0, "t": float(t)})
        smr._edge(native, event, "agent", character_ent)
        if verbatim is not None:
            sub.set_attr(event, "proposition_span", verbatim)
            if preds:
                sub.set_attr(event, "proposition", json.dumps(preds[0]))
        smr._edge(native, event, "is_attitude_level2", event)
        sub.set_attr(event, "idx_protagonist", character_name)
        sub.set_attr(event, "idx_intentionality", content)
        sub.set_attr(character_ent, "goal", content)
        flavor_concept = _concept_node(sub, "desire")
        if flavor_concept is not None:
            smr._edge(native, event, "is_a", flavor_concept)
        out["goal_event"] = smr._v(event)
        out["goal"] = content
    return out


# --------------------------------------------------------------------------- #
#  PER-SENTENCE DRIVER — attitude sentence, or None (factual / discriminative).
# --------------------------------------------------------------------------- #
# First-person subject forms whose REAL referent, in a live conversation turn,
# is whoever is SPEAKING — never a literal character named "I"/"we". Mirrors
# the deictic-centre discipline coref_entities.arm_deictic_centre/
# _resolve_pron_name already apply to ordinary factual clauses; this module's
# subject extraction (`_clean_span` over the recognised words) does not run
# through that resolver, so a caller that KNOWS the real speaker (the world
# adapter, armed with the turn's provenance) passes it directly instead.
_FIRST_PERSON_SUBJECTS = frozenset({"i", "we"})


def _ingest_attitude_sentence(agent, sentence: str, *, t: int = 0, unit=None,
                              character_name: Optional[str] = None,
                              recursive_holder_path: Optional[list[str]] = None,
                              actual_world_version: Optional[int] = None,
                              recursive_event_id: Optional[str] = None,
                              accessible: bool = True) -> Optional[dict]:
    """Try to ground `sentence` as a propositional-attitude construction.
    Returns None (not an attitude clause) so the caller falls through to the
    ordinary situation-model reading path — the discriminative case. A
    BELIEF/KNOWLEDGE attitude additionally requires a PROPOSITIONAL complement
    (`_complement_is_propositional`, the held nominal faculty's verdict on the
    complement's own grounding) — a bare-nominal complement ('had a narrow
    neck') is gated out HERE, before anything is minted, so no orphan
    subject/belief-world node is written for a non-attitude reading.

    `character_name` (optional, Wave: interlocutor-as-modeled-participant,
    task 3): the REAL identity of a first-person subject ("I think X" / "we
    want Y"), supplied by a caller that already knows who is speaking (e.g. the
    world adapter's live turn — the interlocutor's tracked Party name). Used
    ONLY when the parsed subject is literally "I"/"we"; a third-person subject
    ("Sally thinks X") is UNCHANGED — every existing corpus-reading caller
    (which passes no override) is byte-identical."""
    ensure_seeds(agent)
    words = ct._recognise_words(agent, sentence)
    found = _find_attitude_marker(agent, words)
    if found is None:
        return None
    idx, mem = found
    subj_words = words[:idx]
    comp_words = words[idx + 1:]
    if mem["flavor"] in ("belief", "knowledge") and not _complement_is_propositional(agent, comp_words):
        return None
    decode = decode_attitude_construction(agent, subj_words, comp_words)
    parsed_subject = _clean_span(agent, subj_words)
    if character_name and parsed_subject.lower() in _FIRST_PERSON_SUBJECTS:
        subject_name = str(character_name)
    else:
        subject_name = parsed_subject
    character_ent = smr._entity(agent, subject_name, unit=unit)  # REAL, shared SmEntity
    if recursive_holder_path is not None and mem["flavor"] in ("belief", "knowledge"):
        if actual_world_version is None:
            raise ValueError("recursive ToM ingestion requires an explicit actual_world_version")
        comp_read = rc.read_clause(agent, comp_words, write=False, learn=False)
        predications = comp_read.get("predications") or []
        content_ref = json.dumps(predications[0] if predications else comp_words,
                                 ensure_ascii=False, separators=(",", ":"))
        pred = predications[0] if predications else []
        referent = str(pred[1]) if len(pred) > 1 else _clean_span(agent, comp_words)
        value = str(pred[2]) if len(pred) > 2 else "true"
        path = [str(holder) for holder in recursive_holder_path]
        event_id = recursive_event_id or json.dumps(
            [path, sentence, int(actual_world_version)], ensure_ascii=False,
            separators=(",", ":"))
        submit_recursive_tom_event(
            agent, event_id=event_id, holder_path=path, referent=referent,
            content_ref=content_ref, value=value,
            actual_world_version=actual_world_version, accessible=accessible,
        )
        answer = query_recursive_tom(
            agent, query_id=f"{event_id}:readback", holder_path=path,
            referent=referent, content_ref=content_ref, expected_value=value,
            actual_world_version=actual_world_version,
        )
        return {"sentence": sentence, "kind": "attitude", "subject": subject_name,
                "attitude_verb": mem["lemma"], "membership": mem, "decode": decode,
                "recursive_answer": answer, "recursive_event_id": event_id,
                "complement_predications": predications}
    grounded = _ground_attitude_complement(agent, character_ent, subject_name,
                                           mem["flavor"], comp_words, t=t)
    return {"sentence": sentence, "kind": "attitude", "subject": subject_name,
            "attitude_verb": mem["lemma"], "membership": mem, "decode": decode,
            **grounded}


def ingest_attitude_sentence(agent, sentence: str, *, t: int = 0, unit=None,
                             character_name: Optional[str] = None,
                             recursive_holder_path: Optional[list[str]] = None,
                             actual_world_version: Optional[int] = None,
                             recursive_event_id: Optional[str] = None,
                             accessible: bool = True) -> Optional[dict]:
    """Run the ToM reader with its scoped English lexical fallback enabled.

    The fallback is active only for this attitude-reading transaction; normal
    dialogue parsing continues to use its existing POS reference behavior.
    """
    from domains.wiktionary_reference import english_pos_fallback_scope
    with english_pos_fallback_scope():
        return _ingest_attitude_sentence(
            agent, sentence, t=t, unit=unit, character_name=character_name,
            recursive_holder_path=recursive_holder_path,
            actual_world_version=actual_world_version,
            recursive_event_id=recursive_event_id, accessible=accessible,
        )


# --------------------------------------------------------------------------- #
#  READ TEXT — attitude sentences grounded as nested belief-worlds/goals;
#  factual sentences fall through to the UNCHANGED situation-model path.
# --------------------------------------------------------------------------- #
def read_character_tom(agent, text: str, *, max_sentences: int = 40) -> dict:
    ensure_seeds(agent)
    sentences = rc._split_sentences(text)
    results: list = []
    t = 0
    for s in sentences[:max_sentences]:
        if not s.strip():
            continue
        t += 1
        rec = ingest_attitude_sentence(agent, s, t=t)
        if rec is not None:
            results.append(rec)
            continue
        # FACTUAL — no attitude verb found: the ordinary situation-model
        # reading path, UNCHANGED (reading_scope.read_scope, falling back to
        # reading_collapse.read_clause, then situation_model_reader.
        # ingest_predication) — exactly what situation_model_reader.
        # read_into_situation_model / coref_entities.read_into_situation_model
        # already do for every sentence.
        rs_rec = rs.read_scope(agent, s)
        preds = rs_rec.get("predications") or []
        source = "read_scope"
        if not preds:
            fb = rc.read_clause(agent, s, write=False)
            preds = fb.get("predications") or []
            source = "read_clause_fallback"
        ingests = [smr.ingest_predication(agent, p, t=t) for p in preds]
        results.append({"sentence": s, "kind": "factual", "predications": preds,
                        "source": source, "ingests": ingests})

    sub, _, _ = _resolve(agent)
    actual_world: dict[str, dict] = {}
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("nested"):
            continue
        nm = at.get("name")
        if nm:
            actual_world[nm] = {k: v for k, v in at.items() if k != "name"}
    return {"text": text, "sentences": sentences, "results": results,
            "actual_world": actual_world}


# --------------------------------------------------------------------------- #
#  QUERY HELPERS — pure graph reads.
# --------------------------------------------------------------------------- #
def _character_entity(sub, character_name: str):
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("name") == character_name and not at.get("nested"):
            return n
    return None


def character_belief_world(agent, character_name: str) -> dict:
    """{referent: state_slice} for every proposition nested under
    `character_name`'s belief_world edges — the character's NESTED situation
    model, keyed by the REAL-WORLD referent name for readability, distinct
    from (and never colliding with) the actual world's own SmEntity of that
    name."""
    sub, _, _ = _resolve(agent)
    char_ent = _character_entity(sub, character_name)
    if char_ent is None:
        return {}
    out: dict[str, dict] = {}
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if not at.get("nested") or at.get("belief_holder") != character_name:
            continue
        nm = at.get("referent") or at.get("name")
        if nm:
            out[nm] = {k: v for k, v in at.items()
                      if k not in ("name", "referent", "belief_holder")}
    return out


def character_goal(agent, character_name: str):
    """The `idx_intentionality` content of `character_name`'s most recent
    grounded desire — 'what did the crow want' as a one-hop graph query."""
    sub, _, _ = _resolve(agent)
    char_ent = _character_entity(sub, character_name)
    if char_ent is None:
        return None
    return sub.node(char_ent)["attrs"].get("goal")


def submit_recursive_tom_event(agent, *, event_id: str, holder_path: list[str],
                               referent: str, content_ref: str, value: str,
                               actual_world_version: int, accessible: bool,
                               has_cycle: bool = False):
    """Translate a parsed/access event into the native recursive-ToM graph.

    This is a mechanical adapter: it copies caller-supplied fields and runs
    the seeded rules. Access, cycle, depth and path decisions belong to the
    event producer and native rule guards; this function does no inference.
    The recursive_tom seed must be loaded and its policy explicitly enabled.
    """
    sub, native, ag_node = _resolve(agent)
    path = [str(holder) for holder in holder_path]
    event = sub.add_node("RecursiveTomEvent", {
        "schema_version": 1,
        "event_id": str(event_id),
        "holder_path": path,
        "holder_path_key": json.dumps(path, separators=(",", ":")),
        "depth": len(path),
        "referent": str(referent),
        "content_ref": str(content_ref),
        "value": str(value),
        "actual_world_version": int(actual_world_version),
        "accessible": bool(accessible),
        "has_cycle": bool(has_cycle),
    })
    native.add_edge_unchecked(ag_node, "has_recursive_tom_event", event)
    native.run_rules()
    return event


def query_recursive_tom(agent, *, query_id: str, holder_path: list[str],
                        referent: str, content_ref: str, expected_value: str,
                        actual_world_version: int) -> dict:
    """Submit a scoped recursive query and read back its native answer.

    An absent answer is returned as unknown. The adapter does not search for
    beliefs or decide their truth; the matching is performed by native rules.
    """
    sub, native, ag_node = _resolve(agent)
    path = [str(holder) for holder in holder_path]
    query = sub.add_node("RecursiveTomQuery", {
        "query_id": str(query_id),
        "holder_path_key": json.dumps(path, separators=(",", ":")),
        "referent": str(referent),
        "content_ref": str(content_ref),
        "expected_value": str(expected_value),
        "actual_world_version": int(actual_world_version),
    })
    native.add_edge_unchecked(ag_node, "has_recursive_tom_query", query)
    native.run_rules()
    for answer in sub.nodes("RecursiveTomAnswer"):
        answer_node = sub.node(answer)["attrs"]
        if answer_node.get("query_id") == str(query_id):
            return {"query_id": str(query_id), "status": answer_node.get("status", "unknown"),
                    "evidence_event_id": answer_node.get("evidence_event_id")}
    return {"query_id": str(query_id), "status": "unknown", "evidence_event_id": None}


__all__ = ["ensure_seeds", "attitude_membership", "decode_attitude_construction",
           "ingest_attitude_sentence", "read_character_tom",
           "character_belief_world", "character_goal",
           "submit_recursive_tom_event", "query_recursive_tom"]
