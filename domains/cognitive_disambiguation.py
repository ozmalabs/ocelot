"""cognitive_disambiguation — the reader UNDERSTANDING a grounding, not parsing it.

THE CREATOR'S POINT (the `nobel` residual): the reader grounded 'Nobel' to Alfred
Nobel the PERSON and then let the ambient female 'she' bleed onto it, so a bare
`nobel` entity carried 18 mentions and read FEMALE — while 'Nobel Prize' is an
inanimate PRIZE, not a person at all. The grounding (Nobel -> a person) is NOT
wrong; the reader FAILS TO UNDERSTAND what the text says. A program tokenises
'Nobel Prize' and moves on; a READER knows it is an award named for a chemist, that
you can WIN it, and that it is not a woman.

Two GENERAL cognitive moves (Nobel is the driving example, never a special case):

  (a) COHERENCE-CHECK. After grounding, check whether the grounding COHERES with the
      entity's predicated role / animacy. An INCOHERENT reading is a RESIDUAL, a
      signal to re-decode (the async-revisable collapse, at the grounding level):
        · a NON-animate thing carrying a gender (a substance 'radium' read female);
        · a PERSON as the THEME of an acquisition verb ('won'/'received' — you win a
          prize, you do not win a person);
        · a PERSON conflated with an award NAMED AFTER them (the 'Nobel Prize'
          absorbed into the person 'Nobel', dragging the ambient female leak onto
          the honoree).
      The residual is a GRAPH PREDICATE over the SmEntity pool (a native Filter),
      not a Python if/else, and it RE-DECODES (clears the incoherent gender / restores
      the award's inanimacy).

  (b) NAMED-COMPOUND COMPOSITION. 'X <head-type>' (modifier + head) is a
      CONSTRUCTION: the ENTITY is the HEAD-type (an award / institution / proposition
      / law — inanimate), and X is who it HONOURS — a `named_after` relation the
      reader can STATE. 'Nobel Prize' = a prize named after Nobel; 'Fields Medal' = a
      medal named after Fields; 'Curie Institute' = an institution named after Curie;
      "Boyle's Law" = a law named after Boyle. The head-type set is WordNet-DERIVED
      (a head word is a member iff its noun senses descend from a graph-resident
      HeadTypeRoot synset — award.n.02 / organization.n.01 / proposition.n.01 /
      law.n.01), EXTENSIBLE (drop another root), NOT a hardcoded name table.

  (c) THE DISAMBIGUATION FALLS OUT. The coherence-check flags the person-as-prize
      incoherence; the compound-composition resolves it (the entity is the prize,
      inanimate; Nobel is the honoree); the nobel-female-leak DISSOLVES as a
      COMPREHENSION consequence — no 'Nobel'->prize table anywhere.

ARCHITECTURE (CLAUDE.md). A world-adapter refinement over graph data, scoped to the
encyclopedic read (the fable/crow path never calls it — byte-identical). WordNet
hypernymy + the case scan are mechanical reference reads (the coref idiom); the
head-type roots + acquisition-verb roots are graph-resident seed data
(`domain_data/named_compound_heads.json`); the coherence residual is a native Filter Term
the Rust evaluator runs; the composition writes real graph edges (`named_after`).
No Python if/else decides MEANING, and there is no 'nobel' literal in the decision
path — the fix is generic comprehension. donkey=0 (no LLM), no `import re`.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import gender_shape as gs
from domains import name_variant_merge as nvm
from substrate_rs import ext

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED = os.path.join(_ROOT, "domain_data", "named_compound_heads.json")
_METON_SEED = os.path.join(_ROOT, "seeds", "metonymy_patterns.json")


# --------------------------------------------------------------------------- #
#  resolve + Term helpers (the domains/*.py idiom).
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


def _V(n):
    return {"type": "Var", "name": n}


def _Lit(v):
    return {"type": "Lit", "value": v}


def _Attr(node, k):
    return {"type": "Attr", "node": node, "key": k}


def _Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def _Not(x):
    return {"type": "Not", "arg": x}


def _And(items):
    return {"type": "And", "items": items}


def _Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


def _NodesOfType(t):
    return {"type": "NodesOfType", "node_type": t}


# --------------------------------------------------------------------------- #
#  the head-type + acquisition-verb codebook — graph-resident seed data.
# --------------------------------------------------------------------------- #
def ensure_head_codebook(agent) -> None:
    """Idempotently install the named-compound head-type roots (`HeadTypeRoot`) +
    acquisition-verb roots (`AcquireVerbRoot`/`AcquireVerbLex`) from
    domain_data/named_compound_heads.json. Guarded by a `Seed{id:'named_compound_heads'}`
    sentinel — the same seed-I/O idiom register_source uses. Mechanical."""
    sub, _native, _ag = _resolve(agent)
    if any(sub.node(n)["attrs"].get("id") == "named_compound_heads"
           for n in sub.nodes("Seed")):
        return
    with open(_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "named_compound_heads",
                          "version": manifest.get("version", "1.0.0")})


def _head_roots(agent) -> list:
    """[(root_synset_name, category, animate)] read OFF the graph HeadTypeRoot
    nodes — the codebook is graph data, not a Python list."""
    sub, _native, _ag = _resolve(agent)
    out = []
    for n in sub.nodes("HeadTypeRoot"):
        at = sub.node(n)["attrs"]
        out.append((at.get("synset"), at.get("category"),
                    float(at.get("animate", 0.0) or 0.0)))
    return out


def _acquire_roots(agent) -> tuple:
    """({root verb synset names}, {acquire lexnames}) read off the graph — the
    WIN/RECEIVE/EARN class the role coherence-check uses."""
    sub, _native, _ag = _resolve(agent)
    roots, lexes = set(), set()
    for n in sub.nodes("AcquireVerbRoot"):
        s = sub.node(n)["attrs"].get("synset")
        if s:
            roots.add(s)
    for n in sub.nodes("AcquireVerbLex"):
        lx = sub.node(n)["attrs"].get("lexname")
        if lx:
            lexes.add(lx)
    return roots, lexes


# --------------------------------------------------------------------------- #
#  head_type — the WordNet-DERIVED membership test (not a head-word table).
# --------------------------------------------------------------------------- #
def head_type(agent, word: str) -> Optional[tuple]:
    """(category, animate) if `word`'s noun senses descend from a graph-resident
    HeadTypeRoot synset, else None. WordNet hypernymy decides — 'prize'/'medal'/
    'award' land under award.n.02, 'university'/'institute'/'committee' under
    organization.n.01, 'theorem' under proposition.n.01, 'law' under law.n.01. A
    plural head is lemmatised via WordNet morphy ('prizes'->'prize'). A person head
    ('laureate' -> noun.person, under no inanimate root) returns None — it is NOT
    demoted (the anti-over-fire nuance: a 'Nobel laureate' stays a person)."""
    ensure_head_codebook(agent)
    roots = _head_roots(agent)
    if not roots:
        return None
    try:
        from nltk.corpus import wordnet as wn
        w = str(word).replace("_", " ").strip().lower()
        lemma = wn.morphy(w.replace(" ", "_"), wn.NOUN) or w
        root_syns = {}
        for name, cat, anim in roots:
            try:
                root_syns[wn.synset(name)] = (cat, anim)
            except Exception:
                continue
        for s in wn.synsets(lemma.replace(" ", "_"), pos=wn.NOUN):
            anc = set()
            for path in s.hypernym_paths():
                anc.update(path)
            for rs_syn, (cat, anim) in root_syns.items():
                if rs_syn in anc:
                    return (cat, anim)
    except Exception:
        return None
    return None


def is_acquire_verb(agent, verb: str) -> bool:
    """Is `verb` an ACQUISITION verb (win/receive/award/earn/get) — the class whose
    THEME is normally an inanimate thing, so a PERSON theme is incoherent? WordNet
    decides: the verb's dominant sense descends from a graph-resident AcquireVerbRoot
    (get.v.01) OR its lexname is an AcquireVerbLex (verb.competition/verb.possession).
    Not a verb list — a WordNet root/lexname read."""
    roots, lexes = _acquire_roots(agent)
    try:
        from nltk.corpus import wordnet as wn
        lemma = wn.morphy(str(verb).lower(), "v") or str(verb).lower()
        syns = wn.synsets(lemma, pos="v")
        if not syns:
            return False
        if syns[0].lexname() in lexes:
            return True
        root_syns = set()
        for name in roots:
            try:
                root_syns.add(wn.synset(name))
            except Exception:
                continue
        for s in syns[:3]:
            for path in s.hypernym_paths():
                if root_syns & set(path):
                    return True
    except Exception:
        return False
    return False


# --------------------------------------------------------------------------- #
#  SELECTIONAL EXPECTATION — a verb imposes a TYPE on its arguments. This is the
#  signal the role RE-DECODE acts on: an acquisition verb (win/receive/award/earn)
#  expects a WINNABLE/GRANTABLE thing in its THEME slot (a prize/award/title/money
#  — inanimate), so a PERSON (animate) in that slot is a selectional VIOLATION.
#  Graph-native: the verb class is the WordNet-derived AcquireVerbRoot membership
#  (`is_acquire_verb`, NOT a verb table); the expectation it names is a small
#  type record. Extensible — a new verb class + its expected argument type is a
#  new AcquireVerbRoot/HeadTypeRoot pair, no code change.
# --------------------------------------------------------------------------- #
def selectional_expectation(agent, verb: str) -> Optional[dict]:
    """The type a verb imposes on its THEME argument, or None when the verb imposes
    no such constraint. An ACQUISITION verb (WordNet-derived via `is_acquire_verb`)
    expects an INANIMATE WINNABLE/GRANTABLE thing — you WIN a prize, not a person —
    so `expect_animate` is 0.0. WordNet verb frame, not a hardcoded verb table: the
    class is read off the graph AcquireVerbRoot/AcquireVerbLex codebook."""
    if is_acquire_verb(agent, str(verb)):
        return {"role": "theme", "expect_animate": 0.0, "winnable": True}
    return None


def _violates_theme_expectation(theme_attrs: dict, expectation: Optional[dict]) -> bool:
    """Does a theme binding VIOLATE the verb's selectional expectation? An acquire
    verb expects `expect_animate == 0.0`; a PERSON theme (coref_category 'person'
    OR coref_animate 1.0) violates it. Pure attr read over the bound node — a graph
    predicate, not a decision about MEANING (the re-decode below decides that)."""
    if not expectation:
        return False
    if expectation.get("expect_animate") != 0.0:
        return False
    is_person = (theme_attrs.get("coref_category") == "person"
                 or float(theme_attrs.get("coref_animate", 0.0) or 0.0) == 1.0)
    return bool(is_person)


def _mark_subject(agent, subject: Optional[str]) -> None:
    """Stamp `is_doc_subject=1.0` on the subject SmEntity so the role rule's
    subject-guard (`Not(Eq(person.is_doc_subject, 1.0))`) reads it off the graph.
    Mechanical ingest data-prep — no decision. Clears stale marks first so a
    re-run with a different subject is coherent."""
    sub, _native, _ = _resolve(agent)
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if float(at.get("is_doc_subject", 0.0) or 0.0) != 0.0 and at.get("name") != subject:
            sub.set_attr(n, "is_doc_subject", 0.0)
    if subject:
        node = _entity_by_name(sub, subject)
        if node is not None:
            sub.set_attr(node, "is_doc_subject", 1.0)


def _prep_acquire(agent) -> None:
    """Ingest data-prep for the ROLE leg: stamp `sel_acquire=1.0` on every SmEvent
    whose verb is a WordNet-derived acquisition verb (`is_acquire_verb`). The rule's
    role-gate (`Eq(ev.sel_acquire, 1.0)`) then reads it off the graph — the WordNet
    lookup is here, at ingest, NEVER inside the rule. Mechanical, idempotent."""
    sub, _native, _ = _resolve(agent)
    for ev in list(sub.nodes("SmEvent")):
        eat = sub.node(ev)["attrs"]
        verb = eat.get("verb") or eat.get("surface")
        if not verb:
            continue
        if float(eat.get("sel_acquire", 0.0) or 0.0) != 0.0:
            continue
        if is_acquire_verb(agent, str(verb)):
            sub.set_attr(ev, "sel_acquire", 1.0)


def _prep_frames(agent) -> None:
    """Ingest data-prep for the METONYMY legs: for every SmEvent, write an
    `ev --frames_theme/frames_agent--> SelectionalFrame` edge for each role the
    verb frames (WordNet-synset descent via `verb_frame`). The coerce_theme /
    coerce_agent rules then match over these edges with NO WordNet lookup inside
    them. Mechanical, idempotent (skips an edge already present)."""
    sub, native, _ = _resolve(agent)
    for ev in list(sub.nodes("SmEvent")):
        eat = sub.node(ev)["attrs"]
        verb = eat.get("verb") or eat.get("surface")
        if not verb:
            continue
        for role in ("theme", "agent"):
            frame = verb_frame(agent, str(verb), role)
            if frame is None:
                continue
            fn = _frame_node(agent, frame)
            if fn is None:
                continue
            et = "frames_%s" % role
            if _v(fn) not in {_v(x) for x in native.neighbours(ev, et)}:
                native.add_edge_unchecked(ev, et, fn)


def _frame_node(agent, frame: dict) -> Any:
    """The SelectionalFrame NODE matching a frame record (verb_synset + role) —
    so `_prep_frames` can wire the event to the graph-resident frame the rule
    reads. Mechanical lookup."""
    sub, _native, _ = _resolve(agent)
    for n in sub.nodes("SelectionalFrame"):
        at = sub.node(n)["attrs"]
        if at.get("verb_synset") == frame.get("verb_synset") and at.get("role") == frame.get("role"):
            return n
    return None


def event_theme(agent, event_node) -> Optional[dict]:
    """The current THEME binding of an SmEvent (name + animacy + category) — a pure
    graph read, so a test can show the theme VERBATIM before/after the re-decode
    (a BOUND theme, not a flag). None when the event has no theme edge."""
    sub, native, _ = _resolve(agent)
    for th in native.neighbours(event_node, "theme"):
        at = sub.node(th)["attrs"]
        return {"name": at.get("name"),
                "animate": float(at.get("coref_animate", 0.0) or 0.0),
                "category": at.get("coref_category")}
    return None


# --------------------------------------------------------------------------- #
#  small graph helpers.
# --------------------------------------------------------------------------- #
def _entity_by_name(sub, name: str):
    for n in sub.nodes("SmEntity"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


def _find_or_mint_namesake(agent, name: str, stats: dict):
    """The person entity the compound HONOURS. Reuse the resident bare-modifier
    entity ('nobel') if it exists — so the coherence-check can clear ITS leaked
    gender — else mint a person entity for the namesake. Mechanical."""
    sub, native, _ = _resolve(agent)
    node = _entity_by_name(sub, name)
    if node is not None:
        return node
    node = sub.add_node("SmEntity", {"name": name, "coref_category": "person",
                                     "coref_animate": 1.0, "coref_gender": "",
                                     "coref_mentions": 0.0, "coref_cleanliness": 1.0,
                                     "minted_namesake": 1.0})
    return node


def _own_gender(name: str) -> str:
    """The namesake's OWN natural gender from WordNet object-properties (king->male,
    queen->female), '' when the word carries none — so a legitimately-gendered
    namesake keeps its gender and only an ambient-leaked one is cleared."""
    return gs.object_property_gender(str(name)) or ""


# --------------------------------------------------------------------------- #
#  TITLE-CASE CONSTRUCTIONS read straight off the TEXT — so a compound the reader
#  glommed wrong ('Turing Award' -> a bare `award`; 'Curie Institute' ->
#  `at_curie_institute`) is still recognised as the construction it is. A named
#  compound is TITLE-CASED: a run of proper-capitalised modifier tokens (optionally
#  a possessive "Boyle's") immediately before a capitalised HEAD-type word. The
#  Title-Case + head-type gate is the precision guard (a lowercase 'the french law'
#  does NOT fire; 'Marie Curie' does not — 'curie' is no head-type). Mechanical char
#  scan, no regex.
# --------------------------------------------------------------------------- #
def _is_adjectival(word: str) -> bool:
    """Does WordNet know `word` primarily as an ADJECTIVE/adverb (a nationality or
    descriptor: 'russian', 'national', 'flying', 'higher', 'floating', 'french')
    rather than a proper NAME? True iff it has an adjective/satellite/adverb sense —
    the signal that a capitalised modifier is a DESCRIPTOR, not a person/place
    namesake ('X Prize' honours a NAME, not an adjective). A real surname
    ('nobel'/'fields'/'curie'/'turing') has no adjective sense. WordNet-derived, not
    a stoplist."""
    try:
        from nltk.corpus import wordnet as wn
        w = str(word).replace("_", " ").lower()
        if wn.synsets(w.replace(" ", "_"), pos="a") or wn.synsets(w.replace(" ", "_"), pos="s") \
                or wn.synsets(w.replace(" ", "_"), pos="r"):
            return True
    except Exception:
        return False
    return False


def _namesake_ok(mod: str, stats: dict) -> bool:
    """Is `mod` a plausible person/place NAMESAKE (not an adjective/descriptor)?
    Dominantly-capitalised in the text (a proper name — `_is_proper_token`) AND not a
    WordNet adjective. This is the precision guard that keeps 'Nobel'/'Fields'/'Curie'
    and drops 'Russian'/'Flying'/'National'."""
    return nvm._is_proper_token(mod, stats) and not _is_adjectival(mod)


def _title_constructions(agent, text: str) -> dict:
    """{canonical_name: (mods, head, category)} for every title-case 'Proper+ Head'
    named compound in `text`, head-type decided by WordNet, modifier a proper-name
    NAMESAKE (case-dominant + non-adjectival). Deduplicated by canonical name."""
    from domains import narrative_structure as _ns
    raws = str(text).split()
    cores = [r.strip(".,!?;:\"'()[]«»").strip() for r in raws]
    stats = nvm._case_stats(text)
    _CLAUSE_END = (",", ";", ":", ".", "!", "?")
    out: dict = {}
    for i, core in enumerate(cores):
        if not core or not core[:1].isupper() or not core.replace("_", "").isalpha():
            continue
        ht = head_type(agent, core)
        if ht is None:
            continue
        category, _anim = ht
        # walk back over proper-name modifier tokens (allow one possessive), stopping
        # at a function word, an adjective, a clause boundary, or a non-namesake.
        mods = []
        j = i - 1
        while j >= 0:
            raw_j = raws[j]
            cj = cores[j]
            if raw_j.rstrip("\"')]»").endswith(_CLAUSE_END):
                break                            # a clause boundary closes the phrase
            is_poss = cj.lower().endswith("'s")
            stem = cj[:-2] if is_poss else cj
            stem = stem.strip("'").lower()
            # a possessive ("Boyle's") IS the namesake marker, so it needs only to be
            # capitalised + non-adjectival (its apostrophe keeps it out of the case
            # stats); a bare modifier must also be dominantly-capitalised (a proper
            # name, `_is_proper_token`).
            ok = (stem and cores[j][:1].isupper() and stem.replace("_", "").isalpha()
                  and not _ns._is_function_word(stem) and not _is_adjectival(stem)
                  and (is_poss or nvm._is_proper_token(stem, stats)))
            if ok:
                mods.insert(0, stem)
                if is_poss:
                    j -= 1
                    break                        # possessive closes the modifier
                j -= 1
            else:
                break
        if not mods:
            continue
        canon = "_".join(mods + [core.lower()])
        out[canon] = (mods, core.lower(), category)
    return out


# --------------------------------------------------------------------------- #
#  (b) NAMED-COMPOUND COMPOSITION — 'X <head>' -> head-type entity + named_after.
# --------------------------------------------------------------------------- #
def _get_or_mint_compound(agent, canon: str) -> Any:
    """The SmEntity for a canonical compound name — reuse the reader's if present,
    else mint one (the correctly-understood compound the reader glommed away)."""
    sub, _native, _ = _resolve(agent)
    node = _entity_by_name(sub, canon)
    if node is not None:
        return node, False
    node = sub.add_node("SmEntity", {"name": canon, "coref_mentions": 1.0,
                                     "coref_cleanliness": 1.0, "minted_compound": 1.0})
    return node, True


def _constructions(agent, text: str) -> dict:
    """{canonical_name: (mods, head, category)} — every named compound the reader
    should understand, from TWO sources unified: (1) the reader's own compound
    ENTITIES whose name is MOD(proper)+HEAD(head-type) ('nobel_prize',
    'nobel_prizes'); (2) TITLE-CASE constructions read straight off the text
    ('Turing Award', 'Curie Institute' the reader glommed away). Proper-modifier +
    head-type is the shared gate."""
    sub, _native, _ = _resolve(agent)
    stats = nvm._case_stats(text)
    cons = dict(_title_constructions(agent, text))
    for n in sub.nodes("SmEntity"):
        nm = sub.node(n)["attrs"].get("name")
        if not isinstance(nm, str) or not nm:
            continue
        toks = nvm._name_tokens(nm)
        if len(toks) < 2:
            continue
        head, mods = toks[-1], toks[:-1]
        ht = head_type(agent, head)
        if ht is None or not all(_namesake_ok(t, stats) for t in mods):
            continue
        cons.setdefault(nm, (mods, head, ht[0]))
    return cons


def compose_named_compounds(agent, text: str) -> dict:
    """Recognise every 'X <head-type>' as a CONSTRUCTION: the entity IS the head-type
    (inanimate award/institution/proposition/law); X is the honoree, wired by a real
    `named_after` edge; the composed meaning is STATED. When an inanimate compound had
    been INCOHERENTLY absorbed into its own namesake (the person-as-prize merge — an
    award folded into the person 'Nobel'), the merge is UNDONE (the award restored as
    a first-class inanimate entity). Returns the ledger."""
    ensure_head_codebook(agent)
    sub, native, _ = _resolve(agent)
    stats = nvm._case_stats(text)
    compositions = []
    for canon, (mods, head, category) in _constructions(agent, text).items():
        n, minted = _get_or_mint_compound(agent, canon)
        at = sub.node(n)["attrs"]
        _anim, _root = head_type(agent, head) or (category, 0.0)
        animate = 0.0                            # award/institution/proposition/law
        namesake_name = "_".join(mods)
        namesake = _find_or_mint_namesake(agent, namesake_name, stats)
        old_animate = float(at.get("coref_animate", 1.0) or 0.0)
        old_gender = at.get("coref_gender") or ""
        incoherence = None
        sub.set_attr(n, "coref_animate", 0.0)
        sub.set_attr(n, "coref_gender", "")
        sub.set_attr(n, "coref_category", "object")
        # UNDO the person-as-prize merge if this inanimate award was absorbed into
        # its own namesake — the coherence residual at the grounding level.
        if str(at.get("merged_into") or "") == namesake_name:
            incoherence = "absorbed_into_namesake"
            sub.set_attr(n, "coref_cleanliness", 1.0)
            sub.set_attr(n, "merged_into", "")
            try:
                sub.remove_edge(n, "name_variant_of", namesake)
            except Exception:
                pass
            back = float(at.get("coref_mentions", 0.0) or 0.0)
            cur = float(sub.node(namesake)["attrs"].get("coref_mentions", 0.0) or 0.0)
            sub.set_attr(namesake, "coref_mentions", max(0.0, cur - back))
        if _v(namesake) not in {_v(h) for h in native.neighbours(n, "named_after")}:
            native.add_edge_unchecked(n, "named_after", namesake)
        try:
            from nltk.corpus import wordnet as _wn
            head_disp = _wn.morphy(head, _wn.NOUN) or head
        except Exception:
            head_disp = head
        _art = "an" if head_disp[:1] in "aeiou" else "a"
        stated = ("%s = %s %s named after %s"
                  % (canon.replace("_", " "), _art, head_disp,
                     namesake_name.replace("_", " ")))
        sub.set_attr(n, "compound_head", head)
        sub.set_attr(n, "compound_category", category)
        sub.set_attr(n, "composed_meaning", stated)
        compositions.append({
            "compound": canon, "head": head, "category": category,
            "honours": namesake_name, "stated": stated, "minted": minted,
            "animate_before": old_animate, "animate_after": 0.0,
            "gender_before": old_gender, "incoherence": incoherence})
    return {"compositions": compositions}


# --------------------------------------------------------------------------- #
#  (a) COHERENCE-CHECK — the grounding-vs-role residual, a graph predicate.
# --------------------------------------------------------------------------- #
def _inanimate_gendered(agent) -> list:
    """The RESIDUAL SET as a native Filter Term (the Rust evaluator runs it): every
    SmEntity that is NON-animate (coref_animate == 0) yet carries a gender — an
    incoherent grounding (a substance/date/institution cannot be male/female). This
    is the coherence-check AS A GRAPH PREDICATE, not a Python if/else."""
    sub, native, _ = _resolve(agent)
    pred = _And([
        _Eq(_Attr(_V("e"), "coref_animate"), _Lit(0.0)),
        _Not(_Eq(_Attr(_V("e"), "coref_gender"), _Lit(""))),
    ])
    res = native.evaluate(_Filter(_NodesOfType("SmEntity"), "e", pred), {})
    out = []
    for r in (res or []):
        at = sub.node(r)["attrs"]
        g = at.get("coref_gender") or ""
        if g:                                    # guard the Lit("") vs None edge
            out.append(r)
    return out


def coherence_check(agent, text: str = "") -> dict:
    """Re-decode every incoherent grounding. THREE residual kinds, each a graph read:

      · ANIMACY-GENDER: a non-animate entity carrying a gender (native Filter) ->
        clear the gender (a substance/date/institution has no sex).
      · NAMESAKE-LEAK: a person who is the `named_after` honoree of an inanimate
        head-type compound, is NOT the document subject, and has NO own natural
        gender -> the gender is an ambient leak (the 'Nobel'-reads-female bug) ->
        cleared. The subject-guard is what keeps a legitimately-female SUBJECT who
        also lends her name to an institute ('Curie Institute') female.
      · ROLE (win/receive): a PERSON as the THEME of an acquisition verb -> flagged
        as incoherent (you win a prize, not a person; the theme should be the award).

    Returns the residual ledger. RE-decoding is the point: the flag CHANGES the
    reading."""
    sub, native, _ = _resolve(agent)
    residuals = []

    # -- head-type-word residual: a bare head-type word ('award','institute') the
    #    reader left animate/gendered by ambient leak IS an inanimate thing (an award
    #    is not a person) -> demote to inanimate + clear gender. WordNet-typed head.
    for n in list(sub.nodes("SmEntity")):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if not isinstance(nm, str) or not nm:
            continue
        toks = nvm._name_tokens(nm)
        if len(toks) != 1:
            continue
        ht = head_type(agent, toks[0])
        if ht is None or ht[1] != 0.0:
            continue
        anim = float(at.get("coref_animate", 1.0) or 0.0)
        g = at.get("coref_gender") or ""
        if anim == 1.0 or g:
            sub.set_attr(n, "coref_animate", 0.0)
            sub.set_attr(n, "coref_gender", "")
            sub.set_attr(n, "coref_category", "object")
            residuals.append({"kind": "head_type_word", "entity": nm,
                              "category": ht[0], "gender_before": g,
                              "why": "a %s is an inanimate thing, not an animate "
                                     "person" % ht[0]})

    # -- animacy-gender residual (graph predicate) -----------------------------
    for nid in _inanimate_gendered(agent):
        at = sub.node(nid)["attrs"]
        old = at.get("coref_gender") or ""
        sub.set_attr(nid, "coref_gender", "")
        residuals.append({"kind": "animacy_gender", "entity": at.get("name"),
                          "gender_before": old, "gender_after": "",
                          "why": "a non-animate grounding cannot carry a gender"})

    # -- namesake-leak residual (person-as-prize / ambient leak) ---------------
    subject = None
    try:
        from domains import register_source as rs
        subject = rs.subject_by_salience(agent).get("subject")
    except Exception:
        subject = None
    for n in list(sub.nodes("SmEntity")):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if not isinstance(nm, str) or not nm:
            continue
        honoured = [h for h in native.in_neighbours(n, "named_after")]
        if not honoured:
            continue
        # only honorees of an INANIMATE head-type compound are eligible
        inan = any(float(sub.node(h)["attrs"].get("coref_animate", 1.0) or 0.0) == 0.0
                   for h in honoured)
        if not inan:
            continue
        g = at.get("coref_gender") or ""
        if not g:
            continue
        if nm == subject:                        # the SUBJECT keeps her own gender
            continue
        if _own_gender(nm):                      # a naturally-gendered namesake keeps it
            continue
        sub.set_attr(n, "coref_gender", "")
        residuals.append({"kind": "namesake_leak", "entity": nm,
                          "gender_before": g, "gender_after": "",
                          "why": "an award's honoree inherited the ambient gender; "
                                 "the namesake's own gender is unstated -> underspecified"})

    # -- role residual (person as theme of an acquisition verb) — the ROLE LEG of
    #    the COERCION PAIR, now a GRAPH-RESIDENT RULE (`coerce_role_named_after`)
    #    fired by `run_rules`. The selectional VIOLATION (a person in a winnable
    #    slot) resolved by the named_after qualia (the inanimate compound the person
    #    is the eponym of) — the DECISION (match the violation, guard subject +
    #    inanimacy, re-point the theme) lives in the rule. Python here does only
    #    (1) ingest data-prep (mark the acquire verbs + the subject), (2) fire the
    #    rule engine, (3) read the ledger back off the graph. No Python decides the
    #    re-bind.
    ensure_metonymy_codebook(agent)
    _prep_acquire(agent)                          # sel_acquire attr (WordNet), ingest
    _mark_subject(agent, subject)                 # is_doc_subject attr, ingest
    # snapshot the pre-run theme bindings (for the ledger, in node-iteration order).
    pre = []
    for ev in list(sub.nodes("SmEvent")):
        eat = sub.node(ev)["attrs"]
        verb = eat.get("verb") or eat.get("surface")
        if not verb:
            continue
        expect = selectional_expectation(agent, str(verb))
        if expect is None:
            continue
        for th in list(native.neighbours(ev, "theme")):
            tat = sub.node(th)["attrs"]
            if not _violates_theme_expectation(tat, expect):
                continue                          # a COHERENT theme is not a residual
            pre.append((ev, str(verb), tat.get("name")))
    native_steps = ext.run_rules(sub)             # THE RE-BIND FIRES (coerce_role)
    sub.add_node("NativeDisambiguationReceipt", {
        "schema": "native_disambiguation_receipt.v1",
        "cluster": "cognitive_disambiguation.coherence_settlement",
        "provenance": "native_rule_readback:coherence_check",
        "native_rule": "coerce_role_named_after",
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    # read the verdict back off the graph — a rebind left `ev -coerced_role_from->
    # person`; its absence is a held-open. Mechanical readback, not a decision.
    for ev, verb, pname in pre:
        rec = {"kind": "role", "entity": pname, "verb": verb,
               "why": "a PERSON is the theme of an acquisition verb -- "
                      "incoherent (you win a prize, not a person); the theme "
                      "should be an inanimate award"}
        rebound = any(sub.node(p)["attrs"].get("name") == pname
                      for p in native.neighbours(ev, "coerced_role_from"))
        if rebound:
            comp_name = None
            for th in native.neighbours(ev, "theme"):
                comp_name = sub.node(th)["attrs"].get("name")
                break
            rec["verdict"] = "re_decoded"
            rec["rebound_from"] = pname
            rec["rebound_to"] = comp_name
            rec["resolution"] = ("the theme is the winnable thing %r named after "
                                 "the person %r, not the person"
                                 % (comp_name, pname))
        else:
            rec["verdict"] = "held_open"
            rec["held_reason"] = ("no coherent winnable re-reading (no named "
                                  "compound, or the person is the document "
                                  "subject) — held open, not force-bound")
        residuals.append(rec)
    return {"residuals": residuals}


# --------------------------------------------------------------------------- #
#  the whole disambiguation — compose, then re-decode the incoherences.
# --------------------------------------------------------------------------- #
def disambiguate(agent, text: str) -> dict:
    """The full cognitive pass: COMPOSE named compounds (b), then COHERENCE-CHECK (a)
    and re-decode. Order matters — composition establishes the `named_after`
    honorees the namesake-leak residual then re-decodes. Returns both ledgers +
    the STATED inferences. Idempotent (re-running composes nothing new, finds no
    residual). Scoped to the encyclopedic read; the fable path never calls it."""
    ensure_head_codebook(agent)
    ensure_metonymy_codebook(agent)
    comp = compose_named_compounds(agent, text)
    coh = coherence_check(agent, text)
    meton = metonymic_redecode(agent, text)              # the 2nd re-reading source
    return {"compose": comp, "coherence": coh, "metonymy": meton,
            "stated": stated_inferences(agent),
            "stated_shifts": metonymic_inferences(agent)}


def stated_inferences(agent) -> list:
    """Read the composed meanings back off the graph — the reader STATING what it
    understood ('Nobel Prize = a prize named after Nobel'), a `named_after`
    relation, not a re-label. Cognitive output, not a data dump."""
    sub, _native, _ = _resolve(agent)
    out = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        meaning = at.get("composed_meaning")
        if meaning:
            out.append({"compound": at.get("name"), "meaning": meaning,
                        "category": at.get("compound_category")})
    out.sort(key=lambda d: str(d["compound"]))
    return out


def named_after(agent, compound_name: str) -> Optional[str]:
    """The honoree an `X <head>` compound is named after — the stated relation read
    off the graph. None if the entity is not a composed compound."""
    sub, native, _ = _resolve(agent)
    node = _entity_by_name(sub, compound_name)
    if node is None:
        return None
    for h in native.neighbours(node, "named_after"):
        return sub.node(h)["attrs"].get("name")
    return None


# --------------------------------------------------------------------------- #
#  METONYMY — the SECOND coherence re-reading source (task-121). A verb's
#  selectional expectation on a SLOT (a THEME that should be a text, an AGENT that
#  should be an institution) is violated by an entity of the WRONG TYPE (a person as
#  the theme of 'read'; a place as the theme of 'won'; a place as the agent of
#  'announce'). The named compound (task-120) is the first re-reading source; when it
#  does not fit, PRODUCTIVE, TYPE-KEYED metonymy is the second: shift X to a related Y
#  of the type the slot wants, via a graph-resident MetonymyPattern (source-TYPE ->
#  target-TYPE — author->works, place->team, place->government), re-bind the slot, and
#  STATE the shift ('read Shakespeare = read Shakespeare's works'). It is GATED by the
#  selectional coherence: it fires ONLY on a violation ('read Shakespeare' shifts;
#  'met Shakespeare' does not — 'meet' expects a person, so a person coheres). No
#  author/place NAME literal in the decision path — the patterns are keyed on the
#  entity's WordNet TYPE (its coref_category), and applicability is a WordNet-synset
#  descent, both read off the graph codebook (seeds/metonymy_patterns.json).
# --------------------------------------------------------------------------- #
def ensure_metonymy_codebook(agent) -> None:
    """Idempotently install the coercion codebook + the COHERENCE-REPAIR RULES from
    seeds/metonymy_patterns.json, guarded by a `Seed{id:'metonymy_patterns'}`
    sentinel. `load_seed_manifest` installs the SelectionalFrame / MetonymyPattern
    nodes AND registers the coerce_theme / coerce_agent / coerce_role_named_after
    engine Rules (the `"rules"` manifest key) so `run_rules` fires them. Applicability
    (`SelectionalFrame -satisfied_by-> MetonymyPattern`) is wired here, once, as graph
    edges — the WordNet descent runs at install, never inside the rule. Mechanical."""
    sub, _native, ag = _resolve(agent)
    if any(sub.node(n)["attrs"].get("id") == "metonymy_patterns"
           for n in sub.nodes("Seed")):
        return
    with open(_METON_SEED) as f:
        manifest = json.load(f)
    sub.load_seed_manifest(manifest, ag)
    _wire_satisfied_by(agent)
    sub.add_node("Seed", {"id": "metonymy_patterns",
                          "version": manifest.get("version", "1.0.0")})


def _wire_satisfied_by(agent) -> None:
    """Compute `SelectionalFrame -satisfied_by-> MetonymyPattern` GRAPH EDGES: a
    pattern satisfies a frame iff (a) it is not reserved and (b) the thing it
    PRODUCES (`target_synset`) descends from the frame's `meton_target_root` — the
    WordNet-synset descent, run ONCE over the seed codebook so the rule matches over
    edges. Idempotent (skips an edge already present) and re-callable after new
    codebook data lands (the mint-as-data path: un-reserve container_content, add a
    drinking frame, re-wire — the SAME rule then fires, no code change)."""
    sub, native, _ = _resolve(agent)
    frames = [(n, sub.node(n)["attrs"]) for n in sub.nodes("SelectionalFrame")]
    pats = [(n, sub.node(n)["attrs"]) for n in sub.nodes("MetonymyPattern")]
    for fn, fa in frames:
        root = fa.get("meton_target_root")
        if not root:
            continue
        existing = {_v(p) for p in native.neighbours(fn, "satisfied_by")}
        for pn, pa in pats:
            if float(pa.get("reserved", 0.0) or 0.0) != 0.0:
                continue
            if _v(pn) in existing:
                continue
            tsyn = pa.get("target_synset")
            if tsyn and _descends(tsyn, root):
                native.add_edge_unchecked(fn, "satisfied_by", pn)


def _sel_frames(agent) -> list:
    """The selectional-frame codebook read OFF the graph SelectionalFrame nodes —
    [{verb_synset, role, accepts:set, meton_target_root}]. Graph data, not a Python
    verb table."""
    sub, _native, _ag = _resolve(agent)
    out = []
    for n in sub.nodes("SelectionalFrame"):
        at = sub.node(n)["attrs"]
        out.append({"verb_synset": at.get("verb_synset"),
                    "role": at.get("role"),
                    "accepts": set(at.get("accepts") or []),
                    "meton_target_root": at.get("meton_target_root")})
    return out


def _metonymy_patterns(agent) -> list:
    """The metonymy-pattern codebook read OFF the graph MetonymyPattern nodes — each a
    source-TYPE -> target-TYPE productive relation. Reserved patterns (no exercised
    slot) are carried but flagged. Graph data, not a Python author/place table."""
    sub, _native, _ag = _resolve(agent)
    out = []
    for n in sub.nodes("MetonymyPattern"):
        at = sub.node(n)["attrs"]
        out.append({"pattern": at.get("pattern"),
                    "source_category": at.get("source_category"),
                    "target_synset": at.get("target_synset"),
                    "target_category": at.get("target_category"),
                    "target_animate": float(at.get("target_animate", 0.0) or 0.0),
                    "suffix": at.get("suffix"), "read_as": at.get("read_as"),
                    "relation": at.get("relation"),
                    "reserved": float(at.get("reserved", 0.0) or 0.0)})
    return out


def _descends(syn_name: str, root_name: str) -> bool:
    """Does WordNet synset `syn_name` descend from (or equal) `root_name`? A pure
    hypernymy read — the SAME idiom `head_type` uses. Both names are graph/WordNet
    data, never a Python literal in the decision path."""
    try:
        from nltk.corpus import wordnet as wn
        s = wn.synset(syn_name)
        anc = set()
        for path in s.hypernym_paths():
            anc.update(x.name() for x in path)
        return root_name in anc
    except Exception:
        return False


def verb_frame(agent, verb: str, role: str) -> Optional[dict]:
    """The SelectionalFrame a verb+role fits, or None. Membership is WordNet-synset
    descent: the verb's dominant sense equals or descends from the frame's
    `verb_synset` — the same 'WordNet root, not a verb list' idiom `is_acquire_verb`
    uses. 'read'/'reads'/'reading' all lemmatise to read.v.01; 'won' -> win.v.01."""
    frames = [f for f in _sel_frames(agent) if f["role"] == role]
    if not frames:
        return None
    try:
        from nltk.corpus import wordnet as wn
        lemma = wn.morphy(str(verb).lower(), "v") or str(verb).lower()
        syns = wn.synsets(lemma, pos="v")
        if not syns:
            return None
        anc = set()
        for s in syns[:2]:
            for path in s.hypernym_paths():
                anc.update(x.name() for x in path)
        for f in frames:
            if f["verb_synset"] in anc:
                return f
    except Exception:
        return None
    return None


def _violates_frame(bound_category: Optional[str], frame: dict) -> bool:
    """Does a binding of category `bound_category` VIOLATE the frame's accept set?
    A pure category read — the selectional coherence check as a predicate, not a
    decision about MEANING."""
    return bool(bound_category) and bound_category not in frame["accepts"]


def _cat_of(sub, node) -> Optional[str]:
    return sub.node(node)["attrs"].get("coref_category")


def _pattern_by_name(agent, name: Optional[str]) -> Optional[dict]:
    """The MetonymyPattern record for a pattern name — read off the graph codebook
    so the shift readback can STATE the reading (`read_as`, `relation`). Mechanical."""
    if not name:
        return None
    for p in _metonymy_patterns(agent):
        if p["pattern"] == name:
            return p
    return None


def metonymic_redecode(agent, text: str = "") -> dict:
    """RE-DECODE every selectional violation a metonymy resolves — now the METONYMY
    LEGS of the COERCION PAIR, GRAPH-RESIDENT RULES (`coerce_theme` / `coerce_agent`)
    fired by `run_rules`. For each SELECTIONAL SLOT a verb frames (theme/agent):

      · COHERENT (bound type is accepted) -> untouched: 'met Shakespeare' coheres.
      · VIOLATION with a qualia path (the frame is `satisfied_by` a pattern whose
        source is the arg's type) -> the RULE SHIFTS: mint a metonymic Y of the type
        the slot wants ('read Shakespeare' -> his WORKS; 'won France' -> the French
        TEAM; 'Washington announced' -> the GOVERNMENT) and re-bind the slot.
      · VIOLATION with NO qualia path -> HELD-OPEN (anti-hallucination).

    The DECISION lives in the rule (match a violation, WHERE a qualia path exists,
    EFFECT the re-bind + mint). Python here does (1) ingest data-prep (`_prep_frames`
    writes the `frames_theme/frames_agent` edges the rule matches — the WordNet verb
    frame, at ingest, never inside the rule), (2) fire `run_rules`, (3) read the
    ledger back off the graph (the minted metonym + the moved edge). Idempotent — a
    re-run sees the metonym (accepted type) and the rule does nothing."""
    ensure_metonymy_codebook(agent)
    sub, native, _ = _resolve(agent)
    # snapshot the pre-run slot bindings (node-iteration order == the ledger order).
    pre = []
    for ev in list(sub.nodes("SmEvent")):
        eat = sub.node(ev)["attrs"]
        verb = eat.get("verb") or eat.get("surface")
        surface = eat.get("surface") or eat.get("verb")
        if not verb:
            continue
        for role in ("theme", "agent"):
            frame = verb_frame(agent, str(verb), role)
            if frame is None:
                continue
            for arg in list(native.neighbours(ev, role)):
                pre.append((ev, surface, str(verb), role,
                            sub.node(arg)["attrs"].get("name"), _cat_of(sub, arg), frame))
    _prep_frames(agent)                           # frames_theme/frames_agent (WordNet), ingest
    native_steps = ext.run_rules(sub)             # THE SHIFT FIRES (coerce_theme / coerce_agent)
    sub.add_node("NativeDisambiguationReceipt", {
        "schema": "native_disambiguation_receipt.v1",
        "cluster": "cognitive_disambiguation.metonymic_settlement",
        "provenance": "native_rule_readback:metonymic_redecode",
        "native_rule": "coerce_theme_and_agent",
        "native_steps": int(native_steps),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    # read the ledger back off the graph — a shift left a minted metonym on the slot.
    shifts, coherent, held = [], [], []
    for ev, surface, verb, role, aname, cat, frame in pre:
        if not _violates_frame(cat, frame):
            coherent.append({"event": _v(ev), "role": role, "verb": verb,
                             "entity": aname, "category": cat,
                             "why": "the %s coheres with what %r expects"
                                    % (role, verb)})
            continue
        meton = None
        for t in native.neighbours(ev, role):
            tat = sub.node(t)["attrs"]
            if float(tat.get("minted_metonym", 0.0) or 0.0) == 1.0 \
                    and tat.get("metonym_of") == aname:
                meton = t
                break
        if meton is None:
            held.append({"event": _v(ev), "role": role, "verb": verb,
                         "entity": aname, "category": cat, "verdict": "held_open",
                         "held_reason": "a %s violates what %r expects but "
                         "neither a named compound nor a metonymy fits — held "
                         "open, not force-bound" % (cat, verb)})
            continue
        mat = sub.node(meton)["attrs"]
        mname = mat.get("name")
        pat = _pattern_by_name(agent, mat.get("metonym_pattern")) or {}
        read_as = pat.get("read_as", "%s")
        if role == "theme":
            reading = "%s %s = %s %s" % (surface, aname, surface, read_as % aname)
        else:
            reading = "%s %s = %s %s" % (aname, surface, read_as % aname, surface)
        shifts.append({"event": _v(ev), "role": role, "verb": verb,
                       "verdict": "re_decoded", "pattern": pat.get("pattern"),
                       "rebound_from": aname, "rebound_to": mname,
                       "relation": pat.get("relation"),
                       "stated": mat.get("metonymic_meaning"),
                       "reading": reading})
    return {"shifts": shifts, "coherent": coherent, "held_open": held}


def metonymic_shift(agent, name: str) -> Optional[str]:
    """The STATED metonymic shift a metonym entity carries ('france stands for the
    team representing france'), or None if `name` is not a minted metonym. Read off
    the graph — the reader STATING what it understood, a `stands_for` relation, not a
    re-label."""
    sub, _native, _ = _resolve(agent)
    node = _entity_by_name(sub, name)
    if node is None:
        return None
    return sub.node(node)["attrs"].get("metonymic_meaning")


def stands_for(agent, source_name: str) -> Optional[str]:
    """The metonymic referent a source entity stands for (france -> france_team), read
    off the `stands_for` edge. None when the source has no metonymic shift."""
    sub, native, _ = _resolve(agent)
    node = _entity_by_name(sub, source_name)
    if node is None:
        return None
    for m in native.neighbours(node, "stands_for"):
        return sub.node(m)["attrs"].get("name")
    return None


def metonymic_inferences(agent) -> list:
    """Every STATED metonymic shift, read back off the graph — the reader's cognitive
    output ('shakespeare stands for shakespeare's works'), a `stands_for` relation."""
    sub, _native, _ = _resolve(agent)
    out = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        m = at.get("metonymic_meaning")
        if m:
            out.append({"metonym": at.get("name"), "meaning": m,
                        "pattern": at.get("metonym_pattern")})
    out.sort(key=lambda d: str(d["metonym"]))
    return out


__all__ = ["ensure_head_codebook", "head_type", "is_acquire_verb",
           "selectional_expectation", "event_theme",
           "compose_named_compounds", "coherence_check", "disambiguate",
           "stated_inferences", "named_after",
           "ensure_metonymy_codebook", "verb_frame", "metonymic_redecode",
           "metonymic_shift", "stands_for", "metonymic_inferences"]
