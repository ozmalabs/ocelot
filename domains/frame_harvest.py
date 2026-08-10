"""frame_harvest — a WORLD ADAPTER that harvests machine-readable lexical-semantic
frameworks (VerbNet selectional restrictions, a WordNet-derived CoreLex of
systematic-polysemy dot-types, WordNet meronymy) into graph-resident
SelectionalFrame + MetonymyPattern SEED DATA, in the EXACT shape the committed
coherence-repair coercion rule family consumes (seeds/metonymy_patterns.json v2,
domains/cognitive_disambiguation.py: ensure_metonymy_codebook / _wire_satisfied_by).

This is NOT agent code. It FETCHES (the corpus APIs), PARSES (VerbNet themroles +
selrestrs; WordNet lexfile spans; meronymy), MAPS the harvested TYPES onto the
substrate's coref_category vocabulary + WordNet synset roots the rule already uses,
and EMITS graph nodes. No conditional over graph state, no decision about MEANING —
the coercion DECISION stays in the committed rule (unchanged); only the DATA grows.
donkey=0 (no LLM), no `import re` (the corpus APIs + str ops suffice), NEVER git.

Mapping (the crux):
  · VerbNet role  -> substrate slot:  Agent/Actor/Cause -> "agent";
    Theme/Topic/Patient/Proposition/Product/Stimulus -> "theme". (The rule only
    fires over theme/agent — `_prep_frames` wires only those.)
  · VerbNet +selrestr type -> substrate coref_category set (the frame's `accepts`),
    e.g. +animate -> {person,animal}; +organization -> {institution,government,
    group,organization}; +communication -> {communication,text,work}; +concrete ->
    {object}; +comestible -> {food,beverage,substance}; +location -> {location}.
  · the frame's `meton_target_root` — the WordNet root a metonymic shift must PRODUCE
    to satisfy the slot — is chosen from the accept family: a communication slot ->
    communication.n.02 (author_works produces text.n.01, which descends from it); an
    organisation-agent slot -> government.n.01 (place_government); a person slot ->
    person.n.01 (no active pattern produces a person from a violator -> a safe
    NON-shifting "meet" family); an object slot -> product.n.02 (producer_product,
    reserved). So a harvested frame FIRES iff an UNRESERVED pattern's target descends
    from its root AND the pattern's source is the violating arg's type — the same
    gate the hand-seeded frames use.

  · CoreLex dot-type (a noun whose WordNet senses span two disjoint lexicographer
    files = systematic polysemy) -> a MetonymyPattern (source-category -> target
    synset/category), the qualia_role inferred from the lexfile pair (person•work =
    AGENTIVE, container/whole•content/part = CONSTITUTIVE, artifact•function = TELIC).
    Harvested dot-type + meronymy patterns are emitted RESERVED (the seed's own
    convention for a pattern with no exercised slot) — a large candidate inventory
    that a future slot un-reserves via the SAME rule, no code change.

English-only: VerbNet / CoreLex / WordNet are the English concept+lexical layer;
multilingual grounding (Open-Multilingual-WordNet / BabelNet) is a noted future
extension, NOT this task.
"""
from __future__ import annotations

import json
import os
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_METON_SEED = os.path.join(_ROOT, "seeds", "metonymy_patterns.json")
_CACHE_DIR = os.path.join(_ROOT, "var", "frame_harvest")


# --------------------------------------------------------------------------- #
#  the type-vocabulary maps (the crux) — VerbNet -> substrate coref_category.
# --------------------------------------------------------------------------- #
# a VerbNet +selrestr type -> the substrate coref_category set it licenses.
_SELRESTR_CATS = {
    "animate": {"person", "animal"},
    "human": {"person"},
    "int_control": {"person"},
    "animal": {"animal"},
    "organization": {"institution", "government", "group", "organization"},
    "concrete": {"object"},
    "solid": {"object"},
    "nonrigid": {"object"},
    "elongated": {"object"},
    "pointy": {"object"},
    "machine": {"machine", "object"},
    "vehicle": {"vehicle", "object"},
    "currency": {"money", "object"},
    "body_part": {"object"},
    "garment": {"object"},
    "comestible": {"food", "beverage", "substance"},
    "substance": {"substance"},
    "location": {"location"},
    "region": {"location"},
    "communication": {"communication", "text", "work"},
    "abstract": {"abstraction"},
    "sound": {"sound"},
    "time": {"time"},
    "scalar": {"abstraction"},
    "force": {"abstraction"},
    "refl": set(),
    "plural": set(),
    "int": set(),
}

# VerbNet thematic role -> substrate slot the coercion rule fires over.
_AGENT_ROLES = {"Agent", "Actor", "Actor1", "Actor2", "Cause"}
# roles whose filler is inherently a MESSAGE / proposition (a communication slot).
_TOPIC_ROLES = {"Topic", "Proposition"}
_THEME_ROLES = {"Theme", "Theme1", "Theme2", "Patient", "Patient1", "Patient2",
                "Stimulus", "Product"} | _TOPIC_ROLES

# the WordNet roots the committed rule + patterns already turn on.
_ROOT_COMMUNICATION = "communication.n.02"   # author_works produces text.n.01
_ROOT_GOVERNMENT = "government.n.01"          # place_government
_ROOT_PERSON = "person.n.01"                  # safe non-shift ("meet") family
_ROOT_PRODUCT = "product.n.02"                # producer_product (reserved)

# hand-seeded (verb_synset, role) pairs whose authored frame is AUTHORITATIVE —
# NEVER shadow them, and NEVER pre-empt the mint-as-data drink demo.
_SKIP_FRAMES = {
    ("read.v.01", "theme"), ("meet.v.01", "theme"), ("win.v.01", "theme"),
    ("announce.v.01", "agent"), ("drink.v.01", "theme"),
}
# lemmas whose behaviour a hand-authored gate pins (read/meet/win/announce) or the
# mint-as-data demo installs at runtime (drink). WordNet's `verb_frame` matches a
# verb against a frame whose synset is ANY ANCESTOR of the verb's dominant sense, so
# a harvested frame keyed on a HYPERNYM of a pinned verb (e.g. inform.v.01, announce's
# hypernym) would silently shadow it. Reconciliation (the hand gate wins): exclude the
# whole ancestor-closure of every pinned verb from the harvest, on both slots.
_PROTECTED_LEMMAS = ("read", "meet", "win", "announce", "drink")


def _protected_synsets() -> set:
    """The union of the ancestor-or-self synset names of each pinned verb's dominant
    sense(s) — the set a harvested frame must not be keyed on (it would shadow a hand
    gate via WordNet ancestry)."""
    from nltk.corpus import wordnet as wn
    out = set()
    for lemma in _PROTECTED_LEMMAS:
        for s in wn.synsets(lemma, pos="v")[:2]:
            for path in s.hypernym_paths():
                out.update(x.name() for x in path)
    return out


def _role_slot(vn_role: str) -> Optional[str]:
    if vn_role in _AGENT_ROLES:
        return "agent"
    if vn_role in _THEME_ROLES:
        return "theme"
    return None


def _plus_types(themrole) -> set:
    """The +restriction type names on a VerbNet themrole (mechanical parse)."""
    out = set()
    for m in themrole.get("modifiers", []):
        if m.get("value") == "+" and m.get("type"):
            out.add(m["type"])
    return out


def _theme_frame(cats: set, is_topic: bool):
    """(accepts, root) for a THEME slot from its restriction categories, or None to
    emit no frame (an unrestricted, non-topic theme imposes no useful expectation —
    the safe default is silence, so a plain 'see X' never coerces)."""
    if is_topic or "communication" in cats:
        accepts = set(cats) | {"object", "text", "work", "communication", "proposition"}
        return sorted(accepts), _ROOT_COMMUNICATION
    if cats & {"person", "animal"}:
        return sorted({"person", "animal"} | (cats & {"person", "animal"})), _ROOT_PERSON
    if cats:                                  # concrete/object/substance/... slot
        return sorted(set(cats) | {"object"}), _ROOT_PRODUCT
    return None


def _agent_frame(cats: set):
    """(accepts, root) for an AGENT slot — an animate/institutional agent; a place
    there is a selectional violation the place_government pattern repairs."""
    accepts = (set(cats) | {"person", "animal", "institution", "government",
                            "group", "organization"})
    return sorted(accepts), _ROOT_GOVERNMENT


# --------------------------------------------------------------------------- #
#  1. FETCH + PARSE VerbNet -> SelectionalFrame records.
# --------------------------------------------------------------------------- #
def harvest_verbnet_frames() -> tuple:
    """[{verb_synset, role, accepts, meton_target_root, gloss}] deduped by
    (verb_synset, role), + a coverage report. Each VerbNet class member lemma is
    resolved to its dominant WordNet verb synset (the key the rule's `verb_frame`
    WordNet-descent matches). Returns (frames, report)."""
    from nltk.corpus import verbnet as vn
    from nltk.corpus import wordnet as wn

    protected = _protected_synsets()
    frames: dict = {}                         # (verb_synset, role) -> attrs
    n_classes = 0
    n_members = 0
    n_protected = 0
    for cid in vn.classids():
        try:
            c = vn.vnclass(cid)
        except Exception:
            continue
        n_classes += 1
        roles = vn.themroles(c)
        # gather the per-slot (accepts, root) this class imposes.
        slot_specs = []                       # (slot, accepts, root)
        for tr in roles:
            slot = _role_slot(tr["type"])
            if slot is None:
                continue
            plus = _plus_types(tr)
            cats = set()
            for t in plus:
                cats |= _SELRESTR_CATS.get(t, set())
            if slot == "agent":
                # PRECISION: only emit an agent frame for a verb VerbNet marks as
                # admitting an ORGANISATIONAL agent (+organization) — the class where a
                # place standing for its government/institution is sensible. A generic
                # agent verb ('the river flooded') is NOT coerced.
                if "organization" not in plus:
                    continue
                spec = _agent_frame(cats)
            else:
                spec = _theme_frame(cats, tr["type"] in _TOPIC_ROLES)
            if spec is None:
                continue
            slot_specs.append((slot, spec[0], spec[1]))
        if not slot_specs:
            continue
        for lemma in vn.lemmas(cid):
            n_members += 1
            syns = wn.synsets(str(lemma).replace("_", " "), pos="v")
            if not syns:
                continue
            vsyn = syns[0].name()             # dominant sense — the rule's key
            if vsyn in protected:
                n_protected += 1
                continue                      # would shadow a hand gate via ancestry
            for slot, accepts, root in slot_specs:
                key = (vsyn, slot)
                if key in _SKIP_FRAMES:
                    continue                  # hand-seeded frame is authoritative
                if key in frames:
                    # merge accepts (union) so a repeated verb widens, never narrows.
                    frames[key]["accepts"] = sorted(
                        set(frames[key]["accepts"]) | set(accepts))
                    continue
                frames[key] = {
                    "verb_synset": vsyn, "role": slot,
                    "accepts": list(accepts), "meton_target_root": root,
                    "gloss": "harvested VerbNet %s: %s slot" % (cid, slot),
                }
    report = {"vn_classes": n_classes, "vn_members": n_members,
              "frames_protected_excluded": n_protected,
              "frames_deduped": len(frames)}
    return list(frames.values()), report


# --------------------------------------------------------------------------- #
#  2. FETCH + PARSE a WordNet-DERIVED CoreLex (systematic-polysemy dot-types) ->
#     MetonymyPattern records (reserved candidate inventory).
# --------------------------------------------------------------------------- #
# lexfile -> substrate coref_category (the source/target type tag).
_LEXFILE_CAT = {
    "noun.person": "person", "noun.animal": "animal", "noun.plant": "plant",
    "noun.food": "food", "noun.substance": "substance", "noun.artifact": "object",
    "noun.communication": "work", "noun.group": "group", "noun.location": "location",
    "noun.body": "object", "noun.object": "object", "noun.possession": "object",
    "noun.shape": "object", "noun.quantity": "abstraction",
    "noun.cognition": "abstraction", "noun.attribute": "abstraction",
    "noun.event": "event", "noun.act": "event", "noun.phenomenon": "event",
    "noun.state": "abstraction", "noun.time": "time", "noun.motive": "abstraction",
    "noun.feeling": "abstraction", "noun.relation": "abstraction",
    "noun.process": "event",
}
# a representative target synset per target category (what the shift PRODUCES).
_CAT_TARGET_SYN = {
    "work": "text.n.01", "object": "artifact.n.01", "food": "food.n.02",
    "substance": "substance.n.01", "group": "group.n.01", "location": "location.n.01",
    "person": "person.n.01", "animal": "animal.n.01", "event": "event.n.01",
    "abstraction": "abstraction.n.06", "time": "time.n.03", "plant": "plant.n.02",
}
# systematic lexfile pairs -> qualia_role (Generative-Lexicon inference).
#   AGENTIVE   = creator -> creation ; CONSTITUTIVE = whole/material -> part/content ;
#   TELIC      = artifact -> function/purpose.
_QUALIA_BY_PAIR = {
    frozenset({"noun.person", "noun.communication"}): "AGENTIVE",
    frozenset({"noun.person", "noun.act"}): "AGENTIVE",
    frozenset({"noun.artifact", "noun.communication"}): "CONSTITUTIVE",
    frozenset({"noun.group", "noun.artifact"}): "CONSTITUTIVE",
    frozenset({"noun.animal", "noun.food"}): "CONSTITUTIVE",
    frozenset({"noun.plant", "noun.food"}): "CONSTITUTIVE",
    frozenset({"noun.substance", "noun.food"}): "CONSTITUTIVE",
    frozenset({"noun.artifact", "noun.substance"}): "CONSTITUTIVE",
    frozenset({"noun.artifact", "noun.group"}): "CONSTITUTIVE",
    frozenset({"noun.location", "noun.group"}): "CONSTITUTIVE",
    frozenset({"noun.artifact", "noun.act"}): "TELIC",
    frozenset({"noun.artifact", "noun.event"}): "TELIC",
}


def _qualia_for(pair: frozenset) -> Optional[str]:
    if pair in _QUALIA_BY_PAIR:
        return _QUALIA_BY_PAIR[pair]
    # default: any pair with a person/creator side reads AGENTIVE, else CONSTITUTIVE.
    labels = {x.split(".", 1)[1] for x in pair}
    if "person" in labels:
        return "AGENTIVE"
    if labels & {"substance", "group", "animal", "plant", "location", "body"}:
        return "CONSTITUTIVE"
    return None


def harvest_corelex_dottypes(max_words: int = 60000) -> tuple:
    """Derive a light CoreLex — the systematic-polysemy DOT-TYPE CLASSES (a noun whose
    senses span two disjoint lexicographer files), deduped to the lexfile PAIR (the
    class, not the word) — and map each to a MetonymyPattern (source-category ->
    target synset/category, qualia_role inferred). Buitelaar's CoreLex proper is a
    Brandeis distribution; this is the WordNet-derived fallback the task specifies,
    self-contained + licensing-clean (WordNet license). Returns (patterns, report)."""
    from nltk.corpus import wordnet as wn
    pair_example: dict = {}                    # frozenset(lexfiles) -> (a_lex, b_lex, word)
    seen_words = 0
    for lemma in wn.all_lemma_names(pos="n"):
        seen_words += 1
        if seen_words > max_words:
            break
        syns = wn.synsets(lemma, pos="n")
        if len(syns) < 2:
            continue
        lexes = {s.lexname() for s in syns}
        lexes = {lx for lx in lexes if lx in _LEXFILE_CAT}
        if len(lexes) < 2:
            continue
        lex_list = sorted(lexes)
        for i in range(len(lex_list)):
            for j in range(i + 1, len(lex_list)):
                pair = frozenset({lex_list[i], lex_list[j]})
                pair_example.setdefault(pair, (lex_list[i], lex_list[j], lemma))
    patterns = []
    n_class = 0
    for pair, (a_lex, b_lex, word) in sorted(pair_example.items(),
                                             key=lambda kv: sorted(kv[0])):
        qual = _qualia_for(pair)
        if qual is None:
            continue
        a_cat, b_cat = _LEXFILE_CAT[a_lex], _LEXFILE_CAT[b_lex]
        # orient source->target: AGENTIVE person->creation; else the more "concrete"
        # / whole side -> the derived side. Deterministic by lexfile sort otherwise.
        if qual == "AGENTIVE" and a_cat != "person" and b_cat == "person":
            src, tgt_cat = b_cat, a_cat
        elif qual == "AGENTIVE" and a_cat == "person":
            src, tgt_cat = a_cat, b_cat
        else:
            src, tgt_cat = a_cat, b_cat
        if src == tgt_cat:
            continue
        tsyn = _CAT_TARGET_SYN.get(tgt_cat)
        if not tsyn:
            continue
        n_class += 1
        rel = "%s_of" % tgt_cat
        patterns.append({
            "pattern": "corelex_%s_%s" % (src, tgt_cat),
            "source_category": src, "target_synset": tsyn, "target_category": tgt_cat,
            "target_animate": 1.0 if tgt_cat in ("person", "animal") else 0.0,
            "suffix": tgt_cat, "read_as": "the %s of %%s" % tgt_cat,
            "read_as_pre": "the %s of " % tgt_cat, "read_as_post": "",
            "relation": rel, "qualia_role": qual, "reserved": 1,
            "gloss": "harvested CoreLex dot-type %s x %s (example lemma: %s)"
                     % (a_lex, b_lex, word),
        })
    return patterns, {"corelex_words_scanned": min(seen_words, max_words),
                      "corelex_dot_classes": n_class}


# --------------------------------------------------------------------------- #
#  3. WordNet meronymy -> CONSTITUTIVE MetonymyPattern candidates (reserved).
# --------------------------------------------------------------------------- #
def harvest_meronymy_patterns(max_patterns: int = 400) -> tuple:
    """part/substance meronymy -> CONSTITUTIVE whole->part patterns (a whole stands
    for a salient part / its material), keyed by the whole synset's lexfile CATEGORY
    (a TYPE, never a name) -> the part synset. Reserved candidate inventory."""
    from nltk.corpus import wordnet as wn
    out = []
    seen = set()
    for s in wn.all_synsets(pos="n"):
        mers = list(s.part_meronyms()) + list(s.substance_meronyms())
        if not mers:
            continue
        whole_cat = _LEXFILE_CAT.get(s.lexname())
        if not whole_cat:
            continue
        part = mers[0]
        part_cat = _LEXFILE_CAT.get(part.lexname(), "object")
        key = (whole_cat, part_cat)
        if key in seen or whole_cat == part_cat:
            continue
        seen.add(key)
        out.append({
            "pattern": "meronym_%s_%s" % (whole_cat, part_cat),
            "source_category": whole_cat, "target_synset": part.name(),
            "target_category": part_cat, "target_animate": 0.0,
            "suffix": "part", "read_as": "a part of %s", "read_as_pre": "a part of ",
            "read_as_post": "", "relation": "part_of", "qualia_role": "CONSTITUTIVE",
            "reserved": 1,
            "gloss": "harvested WordNet meronymy: %s (%s) -> %s (%s)"
                     % (s.name(), s.lexname(), part.name(), part.lexname()),
        })
        if len(out) >= max_patterns:
            break
    return out, {"meronymy_pattern_classes": len(out)}


# --------------------------------------------------------------------------- #
#  4. EMIT — merge harvested nodes AFTER the hand-authored ones (preserved,
#     byte-order intact) into seeds/metonymy_patterns.json.
# --------------------------------------------------------------------------- #
def build_and_emit(write: bool = True) -> dict:
    """The full harvest: read the committed seed (hand-authored nodes + rules kept
    verbatim), append harvested SelectionalFrame + MetonymyPattern nodes, write back.
    Idempotent — a re-run strips prior `harvested:1` nodes first, then re-appends, so
    the hand-authored head (local_id 1-15 + rules) is never touched."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    with open(_METON_SEED) as f:
        seed = json.load(f)

    hand = [n for n in seed["nodes"] if not n.get("attrs", {}).get("harvested")]
    hand_frame_keys = {(n["attrs"].get("verb_synset"), n["attrs"].get("role"))
                       for n in hand if n["type"] == "SelectionalFrame"}
    hand_pattern_names = {n["attrs"].get("pattern")
                          for n in hand if n["type"] == "MetonymyPattern"}
    next_id = max(n.get("local_id", 0) for n in hand) + 1

    vn_frames, vn_rep = harvest_verbnet_frames()
    cl_pats, cl_rep = harvest_corelex_dottypes()
    mer_pats, mer_rep = harvest_meronymy_patterns()

    nodes = list(hand)
    n_frames = 0
    for fr in vn_frames:
        if (fr["verb_synset"], fr["role"]) in hand_frame_keys:
            continue
        at = dict(fr)
        at["harvested"] = 1
        nodes.append({"local_id": next_id, "type": "SelectionalFrame", "attrs": at})
        next_id += 1
        n_frames += 1

    n_pats = 0
    pat_names = set(hand_pattern_names)
    for pat in cl_pats + mer_pats:
        if pat["pattern"] in pat_names:
            continue
        pat_names.add(pat["pattern"])
        at = dict(pat)
        at["harvested"] = 1
        nodes.append({"local_id": next_id, "type": "MetonymyPattern", "attrs": at})
        next_id += 1
        n_pats += 1

    seed["nodes"] = nodes
    report = {"hand_nodes": len(hand), "harvested_frames": n_frames,
              "harvested_patterns": n_pats, "total_nodes": len(nodes),
              **vn_rep, **cl_rep, **mer_rep}
    with open(os.path.join(_CACHE_DIR, "harvest_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    if write:
        with open(_METON_SEED, "w") as f:
            json.dump(seed, f, indent=2)
    return report


if __name__ == "__main__":
    rep = build_and_emit(write=True)
    print(json.dumps(rep, indent=2))
