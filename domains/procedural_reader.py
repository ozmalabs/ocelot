"""PROCEDURAL COMPREHENSION -> a MethodModel (K1).

The narrative situation-model reader (situation_model_reader.read_scope) is built
for declarative story clauses; on a *procedural* passage it drops the trigger
clause ("when X, ...") and yields nothing for a bare imperative ("Recompute ...")
- verified empirically. So a procedure needs its own shallow reader.

This module is a MECHANICAL world-adapter parser (no agent decision, no rule
engine, no agent state): it tokenises a procedural passage, recognises each
token's grammatical CLASS by looking it up in the HELD procedural-grammar
vocabulary (seeds/procedural_grammar.json - Concept nodes carrying proc_role),
segments each sentence at a recognised trigger-connective, and writes a
MethodModel / MethodStep subgraph. The vocabulary lives in the graph, not in a
Python literal set: to teach a synonym you drop a Concept into the seed. This is
the same "read the class off held graph data" idiom situation_model_reader uses
for its verb frames and the relation-cue lexicon uses for its keyword classes.

What it recognises (a BOUNDED grammar - stated honestly):
  · trigger connective   when / if / after / once / whenever   -> splits a clause
  · dependency verb       depends / relies / derives            -> a relation fact
  · change verb           changes / updates / modified          -> a trigger event
  · state marker          becomes / is / marked / gets          -> a state predicate
  · staleness marker      stale / dirty / outdated / invalid    -> a guard condition
  · effect verb           add / remove / recompute / set / mark -> an action (+proc_effect)
  · role preposition      from / to / of / into                 -> a role slot
  · object marker         edge / node / link                    -> the structural object
  · determiner/possessive/particle                              -> skipped

The DECISION of what an action DOES lives downstream in the synthesiser
(method_synthesis.synthesise_rule_from_method), which turns the MethodModel into
real RewriteRule JSON. This module only extracts structure.
"""
from __future__ import annotations

import json
import os
from typing import Optional

# On-demand seed (NOT under the seeds/*.json flat glob load_all_seeds uses), so a
# normal agent boot does not carry the procedural-grammar Concepts (several share
# common words like "set"/"the"/"index" with existing Concepts). ensure_proc_grammar
# installs it only when a procedure is actually read. Move it up into seeds/ if you
# want it globally resident.
_SEED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "seeds", "procedural", "procedural_grammar.json")

# On-demand extension grammar for the CLASSIFY-BY-CODEBOOK-JOIN shape (join_verb +
# classify effect_verb). Loaded alongside the base grammar, guarded by its OWN
# sentinel (a held join_verb Concept) so it is idempotent and never carried by a
# normal boot. Same whole-file on-demand discipline as _SEED_PATH.
_CLASSIFY_SEED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "seeds", "procedural", "procedural_classify_grammar.json")

# The agent MINTS new procedural effect-verb Concepts via the teach() facility
# (domains.teach) into this companion seed. It is a NEW resident seed (whole-file
# isolated — never rewrites the hand-authored boot grammar above). See
# _load_taught_proc_vocab for the donkey=0 boundary note.
_TAUGHT_VOCAB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "seeds", "procedural_effect_verbs.json")


# --------------------------------------------------------------------------- #
#  resolve + seed install (mechanical, idempotent)
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", None)
    ag_node = getattr(agent, "agent", None)
    return sub, native, ag_node


def _has_concept(sub, name: str) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("name") == name:
            return True
    return False


def _has_proc_concept(sub) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("proc_role"):
            return True
    return False


def _has_join_concept(sub) -> bool:
    for n in sub.nodes("Concept"):
        if sub.node(n)["attrs"].get("proc_role") == "join_verb":
            return True
    return False


def _has_base_proc_grammar(sub) -> bool:
    """Base-grammar sentinel: a Concept named 'when' carrying proc_role
    'trigger_connective'. The bare `_has_proc_concept` (ANY proc_role) misfires
    once a TAUGHT proc-effect seed (seeds/procedural_effect_verbs.json, a flat
    seed load_all_seeds boot-loads) is present - those taught effect-verbs carry
    proc_role but do NOT define the base connective/determiner grammar, so the
    base seed would be skipped and every passage would parse as 'bare'. The
    name+role signature is unique to the base grammar (no other seed assigns
    'when' the trigger_connective role), so it does not misfire on a stray
    same-named Concept the way a bare name-guard would."""
    for n in sub.nodes("Concept"):
        at = sub.node(n)["attrs"]
        if at.get("name") == "when" and at.get("proc_role") == "trigger_connective":
            return True
    return False


def ensure_proc_grammar(agent) -> None:
    """Install seeds/procedural_grammar.json (idempotent, guarded by the sentinel
    Concept 'when') and wire agent -knows_concept-> every Concept so the intent
    referent rule can also resolve procedural mentions. Mechanical seed I/O - the
    same idiom situation_model_reader.ensure_seeds uses."""
    sub, native, ag_node = _resolve(agent)
    # sentinel = my seed's signature (any Concept carrying proc_role); common words
    # like "when"/"set" pre-exist as Concepts in other seeds so a name-guard misfires.
    if not _has_base_proc_grammar(sub):
        with open(_SEED_PATH) as f:
            manifest = json.load(f)
        if native is not None and hasattr(native, "load_seed_manifest") and ag_node is not None:
            native.load_seed_manifest(manifest, ag_node)
    # Extension grammar for the classify-by-codebook-join shape (join_verb +
    # classify effect_verb), guarded by its own join_verb sentinel. Mechanical
    # seed I/O, same idiom as the base grammar load above.
    if not _has_join_concept(sub) and os.path.exists(_CLASSIFY_SEED_PATH):
        with open(_CLASSIFY_SEED_PATH) as f:
            cmanifest = json.load(f)
        if native is not None and hasattr(native, "load_seed_manifest") and ag_node is not None:
            native.load_seed_manifest(cmanifest, ag_node)
    # Load whatever effect-verb Concepts the agent has TAUGHT itself since (the
    # teach()-minted companion seed). Runs every call, idempotent by name.
    _load_taught_proc_vocab(sub, native, ag_node)
    # knows_concept backfill (the referent rule iterates knows_concept)
    if hasattr(agent, "_backfill_knows_concept"):
        try:
            agent._backfill_knows_concept()
        except Exception:
            pass


def _load_taught_proc_vocab(sub, native, ag_node) -> None:
    """DONKEY=0 BOUNDARY (flagged): the agent MINTS procedural effect-verb
    Concepts itself via teach() into `_TAUGHT_VOCAB_PATH`; this loads any it does
    not already hold onto a fresh boot. The agent cannot rewire this Python
    on-demand loader, so wiring its own taught vocab into the grammar is the
    minimal mechanical fill. Pure seed I/O — reads held Concept names, loads the
    not-yet-held taught nodes, makes NO decision over graph state (the effect KIND
    of each verb was the agent's call, recorded on the taught Concept)."""
    if not (native is not None and hasattr(native, "load_seed_manifest")
            and ag_node is not None):
        return
    if not os.path.exists(_TAUGHT_VOCAB_PATH):
        return
    try:
        with open(_TAUGHT_VOCAB_PATH) as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        return
    held = set()
    for n in sub.nodes("Concept"):
        nm = sub.node(n)["attrs"].get("name")
        if nm:
            held.add(str(nm).lower())
    missing = [n for n in manifest.get("nodes", [])
               if str(n.get("attrs", {}).get("name", "")).lower() not in held]
    if not missing:
        return
    sub_manifest = dict(manifest)
    sub_manifest["nodes"] = missing
    native.load_seed_manifest(sub_manifest, ag_node)


def held_proc_vocab(agent) -> dict:
    """Read the HELD procedural-grammar classes straight off the graph:
    {word: {proc_role, proc_effect?, proc_slot?, proc_relation?, proc_object?}}.
    This IS the recognition table - graph-resident, data-driven, no Python literal
    keyword set (add a Concept -> a new recognised word)."""
    sub, _, _ = _resolve(agent)
    vocab: dict = {}
    for n in sub.nodes("Concept"):
        at = sub.node(n)["attrs"]
        role = at.get("proc_role")
        if not role:
            continue
        nm = str(at.get("name", "")).lower()
        if not nm:
            continue
        vocab[nm] = {k: v for k, v in at.items()
                     if k in ("proc_role", "proc_effect", "proc_slot",
                              "proc_relation", "proc_object", "proc_agg")}
    return vocab


# --------------------------------------------------------------------------- #
#  tokenising + shallow-clause parse (mechanical, grammar-table-driven)
# --------------------------------------------------------------------------- #
_SKIP_ROLES = {"determiner", "possessive", "particle"}


def _depossess(w: str) -> str:
    """Strip a trailing possessive marker: 'signal's -> signal, tags' -> tags.
    Mechanical suffix trim (no regex) so a join clause reads the bare noun."""
    for suf in ("'s", "’s"):
        if w.endswith(suf):
            return w[: -len(suf)]
    for suf in ("'", "’"):
        if w.endswith(suf) and len(w) > 1:
            return w[: -len(suf)]
    return w


def _has_possessive(w: str) -> bool:
    """True iff the token bears a possessive marker ('s or a trailing '). This is
    the boundary the reader splits a join-clause side on: the OWNER carries the
    possessive, the possessed field follows it. Mechanical suffix test (no regex)."""
    if any(w.endswith(s) for s in ("'s", "’s")):
        return True
    return any(w.endswith(s) for s in ("'", "’")) and len(w) > 1


def _join_side(side_tagged: list):
    """Split ONE side of a join clause into (collection_type, join_key).

    A join side names an owner + a possessed field ("an actor action's VERB"):
    the OWNER is the collection TYPE, the possessed noun the join KEY, and the
    possessive 's marks the boundary. So the TYPE is the (possibly COMPOUND) run
    of content nouns up to AND INCLUDING the possessive-bearing token, space-
    joined ('actor action'); the KEY is the content noun(s) after it ('verb').
    Space-joined so the downstream naming (TitleCase / has_<snake>) reads it
    exactly as it reads any multi-word type.

    Byte-identical to the old left[0]/left[-1] read for a single-word owner:
    'a signal's kind' -> possessive on 'signal's' (index 0) -> type 'signal',
    key 'kind'. Falls back to all-but-last / last when no possessive is marked
    (an honest degenerate case, never reached by a well-formed join clause)."""
    nouns = [w for (w, role, _) in side_tagged if role is None]
    pi = next((i for i, w in enumerate(nouns) if _has_possessive(w)), None)
    if pi is None:
        if len(nouns) >= 2:
            return " ".join(_depossess(w) for w in nouns[:-1]), _depossess(nouns[-1])
        return (_depossess(nouns[0]) if nouns else None), None
    typ = " ".join(_depossess(w) for w in nouns[: pi + 1]) or None
    after = [_depossess(w) for w in nouns[pi + 1:]]
    return typ, (" ".join(after) if after else None)


def _trailing_compound_np(tagged: list, idx: int) -> Optional[str]:
    """The full trailing noun phrase after `idx` as a space-joined compound: every
    plain content noun (role None) to the end, depossessed, stopping at a comma or
    role preposition. 'classify an actor goal' -> 'actor goal'; 'classify a hit' ->
    'hit'. Used only to read a COMPOUND classification TYPE off the classify clause
    (the head-noun read alone would drop 'goal' and mis-name the minted type)."""
    words = []
    for j in range(idx + 1, len(tagged)):
        w, role, _ = tagged[j]
        if role in ("comma", "role_prep"):
            break
        if role is None:
            words.append(_depossess(w))
    return " ".join(words) if words else None


def _split_sentences(text: str) -> list:
    out, cur = [], []
    for ch in text:
        cur.append(ch)
        if ch in ".!?":
            out.append("".join(cur).strip())
            cur = []
    tail = "".join(cur).strip()
    if tail:
        out.append(tail)
    return [s for s in out if s]


def _tokenise(sentence: str) -> list:
    """Whitespace tokenise; keep commas as their own token; strip trailing
    sentence punctuation. Pure mechanical text->token translation."""
    toks = []
    for raw in sentence.replace(",", " , ").split():
        w = raw.strip().lower()
        w = w.strip(".!?;:")
        if w:
            toks.append(w)
    return toks


def _classify(toks: list, vocab: dict) -> list:
    """[(word, role_or_None, meta)] - role read from the held vocab table."""
    out = []
    for w in toks:
        if w == ",":
            out.append((w, "comma", {}))
            continue
        meta = vocab.get(w)
        out.append((w, (meta or {}).get("proc_role"), meta or {}))
    return out


def _content_noun_before(tagged: list, idx: int) -> Optional[str]:
    """Nearest content word (a token with NO proc_role) left of idx."""
    for j in range(idx - 1, -1, -1):
        w, role, _ = tagged[j]
        if role is None:
            return w
    return None


def _content_noun_after(tagged: list, idx: int) -> Optional[str]:
    """Nearest content word right of idx, skipping determiner/possessive/particle
    and stopping at a comma or a role preposition."""
    for j in range(idx + 1, len(tagged)):
        w, role, _ = tagged[j]
        if role in _SKIP_ROLES:
            continue
        if role in ("comma", "role_prep"):
            break
        if role is None:
            return w
        # a marker word (state/stale/object) is not a plain content noun
        break
    return None


def _head_noun_after(tagged: list, idx: int, skip=()) -> Optional[str]:
    """The HEAD content noun of the NP right of idx: walk forward skipping
    determiners/possessives/particles AND any adjectival marker roles in `skip`
    (stale_marker/state_marker/object_marker act as modifiers here), stop at a
    comma or role preposition, return the first plain content word."""
    skipset = set(_SKIP_ROLES) | set(skip)
    for j in range(idx + 1, len(tagged)):
        w, role, _ = tagged[j]
        if role in ("comma", "role_prep"):
            break
        if role is None:
            return w
        if role in skipset:
            continue
        break
    return None


def _first_index(tagged: list, roles) -> Optional[int]:
    for i, (_, role, _) in enumerate(tagged):
        if role in roles:
            return i
    return None


def _role_fillers(tagged: list) -> dict:
    """Every role-preposition -> its filler content noun (skip det/possessive)."""
    out = {}
    for i, (_, role, meta) in enumerate(tagged):
        if role == "role_prep":
            slot = meta.get("proc_slot", "arg")
            noun = _content_noun_after(tagged, i)
            if noun is not None and slot not in out:
                out[slot] = noun
    return out


def _parse_span(tagged: list) -> dict:
    """Shallow predicate parse of ONE clause span.

    Returns {kind, subject, verb, ...} where kind is one of:
      relation        (dependency verb): subject, relation, object
      change_event    (change verb):     subject, verb='change'
      state           (state marker):    subject, state (the complement marker word)
      action          (effect verb):     effect, patient, edge_type?, roles, condition?
      definition      (agg word):        subject, aggregate_op, collection
      bare            (nothing recognised)
    """
    # -1. codebook-JOIN clause ("a signal's kind matches a tag's kind") - the
    #     trigger of a classify-by-codebook-join method: two TYPED collections
    #     joined on a shared FIELD. Recognised by a join_verb; on each side the
    #     OWNER (up to and INCLUDING the possessive-marked noun) is the collection
    #     TYPE — COMPOUND when multi-word ('actor action') — and the possessed
    #     noun after it is the join KEY ('verb'). The possessive 's marks the
    #     boundary (_join_side). Checked first: the join_verb is exclusive to this
    #     shape, so no existing passage reaches it.
    ji = _first_index(tagged, {"join_verb"})
    if ji is not None:
        fact_type, fact_key = _join_side(tagged[:ji])
        codebook_type, codebook_key = _join_side(tagged[ji + 1:])
        return {"kind": "join",
                "fact_type": fact_type, "fact_key": fact_key,
                "codebook_type": codebook_type, "codebook_key": codebook_key}

    # 0. definitional aggregate ("A view holds the count of its source's mentions")
    #    A DEFINITION names WHAT a derived value IS (the aggregate op + the collection
    #    it ranges over) without naming the concrete edge/attr - that binding is
    #    grounded downstream against the domain graph. Checked first because a
    #    definition may also carry a state marker ("a view IS the count of ...").
    ai = _first_index(tagged, {"agg_word"})
    if ai is not None:
        op = tagged[ai][2].get("proc_agg", "Count")
        dv = _first_index(tagged, {"def_verb"})
        subj = _content_noun_before(tagged, dv if dv is not None else ai)
        # collection = the counted/summed thing: the LAST plain content noun.
        coll = None
        for j in range(len(tagged) - 1, -1, -1):
            w, role, _ = tagged[j]
            if role is None:
                coll = w
                break
        return {"kind": "definition", "subject": subj,
                "aggregate_op": op, "collection": coll}

    # 1. dependency relation ("view depends on its source")
    di = _first_index(tagged, {"dep_verb"})
    if di is not None:
        rel = tagged[di][2].get("proc_relation", "depends_on")
        subj = _content_noun_before(tagged, di)
        obj = _content_noun_after(tagged, di)
        return {"kind": "relation", "subject": subj, "relation": rel, "object": obj}

    # 2. effect action ("add a completed edge ...", "recompute a stale view ...")
    ei = _first_index(tagged, {"effect_verb"})
    if ei is not None:
        meta = tagged[ei][2]
        effect = meta.get("proc_effect", "set_attr")
        roles = _role_fillers(tagged)
        # staleness condition anywhere in the span
        cond = next((w for (w, role, _) in tagged if role == "stale_marker"), None)
        # object: an object_marker (edge/node) => structural object; its modifier
        # (the content word just before it) is the edge/attr TYPE. Otherwise the
        # patient is the content noun after the verb.
        oi = _first_index(tagged, {"object_marker"})
        patient = None
        edge_type = None
        obj_kind = None
        if oi is not None:
            obj_kind = tagged[oi][2].get("proc_object")
            edge_type = _content_noun_before(tagged, oi)   # "completed" in "completed edge"
        # patient = HEAD content noun after the verb, skipping adjectival markers
        # ("stale" in "a stale view", "completed" in "a completed edge").
        patient = _head_noun_after(tagged, ei,
                                   skip=("stale_marker", "state_marker", "object_marker"))
        # a classify clause names a (possibly COMPOUND) classification TYPE —
        # "classify an actor goal" is an ActorGoal, not an Actor — so read the
        # full trailing NP as the node_type for this effect (the head-noun read
        # patient alone drops 'goal'). Single-word types are byte-unchanged
        # ('classify a hit' -> 'hit'). No other effect uses node_type here.
        classify_type = None
        if tagged[ei][2].get("proc_effect") == "classify":
            classify_type = _trailing_compound_np(tagged, ei) or patient
        # add_node discrimination: an add-family verb that MINTS A NODE, not an
        # edge. Signalled by (a) the object_marker word 'node', OR (b) no edge
        # marker AND a single 'from'/'of' SOURCE role with no 'to' TARGET ("create
        # a ticket FROM the request" — a mint of a typed node whose attrs are
        # sourced from the subject). An edge-add always names both endpoints
        # (from...to) or the word 'edge', so the existing add_edge path is
        # byte-unchanged. The created TYPE is the patient noun ("ticket").
        node_type = classify_type
        if effect == "add_edge" and (
                obj_kind == "node"
                or (obj_kind != "edge" and roles.get("source")
                    and not roles.get("target"))):
            effect = "add_node"
            node_type = patient
        return {"kind": "action", "effect": effect, "verb": tagged[ei][0],
                "patient": patient, "node_type": node_type,
                "object_kind": obj_kind, "edge_type": edge_type,
                "roles": roles, "condition": cond}

    # 3. state marker ("the view becomes stale", "a task is marked done")
    si = _first_index(tagged, {"state_marker"})
    if si is not None:
        subj = _content_noun_before(tagged, si)
        # the state complement: a stale_marker if present ("becomes stale"), else
        # the head content word past any further state markers ("is marked done").
        state = next((w for (w, role, _) in tagged[si + 1:] if role == "stale_marker"), None)
        if state is None:
            state = _head_noun_after(tagged, si, skip=("state_marker",))
        return {"kind": "state", "subject": subj, "state": state}

    # 4. change event ("the source changes")
    ci = _first_index(tagged, {"change_verb"})
    if ci is not None:
        subj = _content_noun_before(tagged, ci)
        return {"kind": "change_event", "subject": subj, "verb": "change"}

    return {"kind": "bare", "tokens": [w for (w, _, _) in tagged]}


def _split_on_trigger(tagged: list):
    """Split a tagged clause at the trigger connective: returns (trigger_span,
    main_span). No connective -> (None, whole). The trigger span runs from just
    after the connective to the comma; the main span is the remainder."""
    ti = _first_index(tagged, {"trigger_connective"})
    if ti is None:
        return None, tagged
    strip = lambda xs: [t for t in xs if t[1] != "comma"]
    if ti > 0:
        # TRAILING trigger ("do Y when X"): main precedes the connective, trigger
        # runs from just after it to the end.
        return strip(tagged[ti + 1:]), strip(tagged[:ti])
    # FRONTED trigger ("when X, do Y"): the comma closes the trigger clause.
    comma = None
    for j in range(ti + 1, len(tagged)):
        if tagged[j][1] == "comma":
            comma = j
            break
    if comma is None:
        return strip(tagged[ti + 1:]), []
    return strip(tagged[ti + 1:comma]), strip(tagged[comma + 1:])


# --------------------------------------------------------------------------- #
#  THE READER: text -> MethodModel subgraph
# --------------------------------------------------------------------------- #
def read_method(agent, text: str, *, name: str = "method") -> dict:
    """Read a procedural passage into a MethodModel (K1). Emits a MethodModel node
    and one MethodStep node per sentence (model -has_step-> step, ordered by
    step_index), and ALSO runs the intent referent rule so the graph independently
    resolves the procedural mentions (cross-check reported as referent_resolved).
    Returns the structured model for the synthesiser + a human-readable trace."""
    ensure_proc_grammar(agent)
    sub, native, ag_node = _resolve(agent)
    vocab = held_proc_vocab(agent)

    model_id = sub.add_node("MethodModel", {"name": name, "source_text": text})
    steps = []
    trace = []
    for si, sent in enumerate(_split_sentences(text)):
        toks = _tokenise(sent)
        tagged = _classify(toks, vocab)
        trig_tags, main_tags = _split_on_trigger(tagged)
        trigger = _parse_span(trig_tags) if trig_tags else None
        main = _parse_span(main_tags)

        # normalise into a step record
        step = {"sentence": sent, "step_index": si, "trigger": trigger, "main": main}
        steps.append(step)
        trace.append({"sentence": sent, "trigger": trigger, "main": main})

        # write the step subgraph (attrs are scalars/json - mechanical)
        st = sub.add_node("MethodStep", {
            "step_index": float(si),
            "sentence": sent,
            "main_kind": main.get("kind"),
            "main_json": json.dumps(main),
            "trigger_json": json.dumps(trigger) if trigger else "",
        })
        native.add_edge_unchecked(model_id, "has_step", st)

    # graph-native cross-check: ingest the passage as a Message + Mentions and run
    # the referent rule; count how many tokens the graph itself resolved to a proc
    # Concept (demonstrates the recognition is not just the table read).
    referent_resolved = _referent_crosscheck(agent, text, vocab)

    return {"model_id": model_id, "name": name, "text": text,
            "steps": steps, "trace": trace,
            "vocab_size": len(vocab), "referent_resolved": referent_resolved}


def _referent_crosscheck(agent, text: str, vocab: dict) -> dict:
    """Ingest the passage tokens as a Message + Mention chain, run rules, and read
    back how many Mentions the intent referent rule resolved (Mention -refers_to->
    Concept) to a HELD proc Concept. Pure demonstration that the graph's own
    recognition agrees with the table read."""
    sub, native, ag_node = _resolve(agent)
    try:
        mid = sub.add_node("Message", {"text": text, "proc_probe": 1.0})
        for w in _tokenise(text):
            if w == ",":
                continue
            mn = sub.add_node("Mention", {"text": w})
            native.add_edge_unchecked(mid, "has_mention", mn)
        native.run_rules(10000)
        resolved = 0
        total_proc = 0
        for mn in native.neighbours(mid, "has_mention"):
            w = sub.node(mn)["attrs"].get("text", "")
            if w in vocab:
                total_proc += 1
                if native.neighbours(mn, "refers_to"):
                    resolved += 1
        # SCRATCH LIFECYCLE: the probe Message + its Mentions are a demonstration
        # cross-check, now consumed (the count is read). Mark the probe DONE and
        # tick -- the `retire_proc_probe_scratch` rule (seeds/procedural/
        # procedural_grammar.json) then DELETES the scratch, so this conversation-
        # typed demonstration leaves NO Mention behind when read_method runs
        # inside the reading pipeline (whose invariant is SmMention only, never
        # conversation Mention). Mechanical mark + tick; the retire is the rule's
        # decision. Gated on proc_done so the rule never fires during the resolve
        # tick above (proc_done unset there).
        sub.set_attr(mid, "proc_done", 1.0)
        native.run_rules(10000)
        return {"proc_tokens": total_proc, "resolved_by_referent_rule": resolved}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, e)}


__all__ = ["ensure_proc_grammar", "held_proc_vocab", "read_method"]
