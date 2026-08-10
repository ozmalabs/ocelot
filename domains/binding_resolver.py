"""derive_binding - GROUND the synthesiser's binding from the READ TEXT + the
DOMAIN GRAPH, so a caller supplies NOTHING but the domain to apply to.

This is a MECHANICAL RESOLVER (a world-adapter reader), the same legal category
as procedural_reader: it makes no decision over graph state that picks agent
behaviour - it READS the domain graph (what node/edge/attr vocabulary actually
exists) and the comprehended MethodModel (what the text named / defined), and
maps each abstract role in the method to the concrete domain vocabulary it best
matches. No hardcoded "if role=='owner' use owned_by": the candidate edges come
from the graph (only edges that actually exist on the anchor node), and the pick
is a character-overlap Argmax over those candidates against the grounded role
noun - the same character-overlap-Argmax idiom cue_route_pick uses, and the same
"resolve to a concrete node/edge present in the domain graph" the referent
cross-check already leans on.

What it grounds, and from WHERE (reported per-piece in the returned provenance):

  role-noun -> concrete node     from the DOMAIN GRAPH (a node whose kind/name/
                                 type equals the role noun read from text)
  value_attr (recompute)         from the DOMAIN GRAPH (the numeric slot on the
                                 concrete patient node - the definition says the
                                 view HOLDS a value but never names the attr)
  aggregate.op (recompute)       from the READ DEFINITION ("holds the COUNT of
                                 ...": the agg word -> Count/Sum/...)
  aggregate.edge (recompute)     the definition's collection noun ("...of its
                                 source's MENTIONS") grounded to an edge PRESENT
                                 on the concrete source node (overlap Argmax)
  role_relation (add/del edge)   a possessive target ("its OWNER") grounded to an
                                 edge PRESENT on the concrete source node
  state_attr (trigger state)     the trigger state word grounded to an attr
                                 PRESENT on the concrete source node (identity,
                                 confirmed by the graph)

Grounding-faculty note: derive_binding also calls agent.ground_unknowns on the
role nouns (the documented per-word teacher loop) so the agent grounds their
MEANING and memoises it. Offline (OZMA_NO_LLM, no self-teacher) that is a no-op -
reported honestly - because the abstract->concrete BINDING is resolved against
the domain graph + read definition, which need no teacher.
"""
from __future__ import annotations

from typing import Any, Optional


# --------------------------------------------------------------------------- #
#  domain-graph reads (mechanical)
# --------------------------------------------------------------------------- #
def _node_int(nd) -> int:
    v = getattr(nd, "value", None)
    if isinstance(v, int):
        return v
    return int(str(nd).lstrip("#"))


def _graph(agent) -> dict:
    sub = getattr(agent, "s", agent)
    return sub.graph_to_dict()


def _resolve_role_node(gd: dict, role_noun: Optional[str]) -> Optional[dict]:
    """A concrete node in the domain graph that the abstract role noun names:
    match on the node's `kind` attr, its `name` attr, or its type (lowercased).
    Returns {id, type, attrs, via} or None. Pure graph read."""
    if not role_noun:
        return None
    want = str(role_noun).lower()
    nodes = gd.get("nodes", [])
    # Prefer a `kind`-attr match (the domain application nodes) over a stray seed
    # Concept that happens to share the name, then name, then bare type.
    for key in ("kind", "name", "__type__"):
        for n in nodes:
            at = n.get("attrs", {}) or {}
            if key == "__type__":
                if str(n.get("type", "")).lower() == want:
                    return {"id": n["id"], "type": n["type"], "attrs": at, "via": "node type"}
            elif str(at.get(key, "")).lower() == want:
                return {"id": n["id"], "type": n["type"], "attrs": at, "via": "%s attr" % key}
    return None


def _collection_member(gd: dict, noun: Optional[str], agent_id: Optional[int]):
    """Resolve an abstract collection type to (edge_type, node) where the node is
    of that TYPE and is reached by an edge FROM the agent hub — the agent-held
    collection pattern this classify shape matches. Type compared by lowercased
    name with word separators removed, so a COMPOUND read type matches its
    CamelCase node type across snake/space/camel ('actor action' or 'actor_action'
    both match type 'ActorAction'). Returns None if no such collection member
    exists. Pure domain-graph read (mechanical name normalisation, no decision)."""
    if not noun or agent_id is None:
        return None
    want = str(noun).lower().replace(" ", "").replace("_", "")
    nid_by = {n["id"]: n for n in gd.get("nodes", [])}
    for e in gd.get("edges", []):
        if e.get("src") != agent_id:
            continue
        tgt = nid_by.get(e.get("tgt"))
        if tgt is None:
            continue
        if str(tgt.get("type", "")).lower().replace(" ", "").replace("_", "") == want:
            return e["type"], {"id": tgt["id"], "type": tgt["type"],
                               "attrs": tgt.get("attrs", {}) or {}}
    return None


def _out_edge_types(gd: dict, node_id: int) -> list:
    return sorted({e["type"] for e in gd.get("edges", []) if e.get("src") == node_id})


def _in_edge_types(gd: dict, node_id: int) -> list:
    """Edge types whose TARGET is `node_id` — the anchors a hub uses to REACH this
    node (for an add_node mint the rule matches hub -REL-> subject)."""
    return sorted({e["type"] for e in gd.get("edges", []) if e.get("tgt") == node_id})


# --------------------------------------------------------------------------- #
#  character-overlap Argmax (the abstract-noun -> concrete-name bridge)
# --------------------------------------------------------------------------- #
def _lcs_len(a: str, b: str) -> int:
    """Longest common CONTIGUOUS substring length (mechanical string metric)."""
    a, b = a.lower(), b.lower()
    if not a or not b:
        return 0
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def _score(noun: str, edge: str) -> int:
    """Overlap of a role noun with an edge type: best over the edge name and its
    '_'-split tokens (so 'owner' scores on 'owned_by' via 'owned', 'mentions' on
    'has_mention' via 'mention')."""
    cands = [edge] + [t for t in edge.split("_") if t]
    return max(_lcs_len(noun, c) for c in cands)


# --------------------------------------------------------------------------- #
#  SEMANTIC-relatedness Argmax (the MEANING bridge — the agent's grounding)
#
#  When names don't rhyme (character overlap below floor) the noun->edge link is
#  decided by MEANING, grounded through the agent's OWN WordNet faculty (the same
#  offline synset/gloss/hypernym/derivational data domains/dictionary_lexicon
#  reads for sense selection — donkey=0, no LLM teacher). Each word is grounded
#  to a "sense bag": its synset glosses + lemma names + hypernym lemmas, every
#  token normalised to its root lemma across POS + derivational forms (so the
#  noun "owner"'s {own, ownership, possess, possessor} region MEETS the verb
#  "belongs"' gloss "be OWNED by; be in the POSSESSION of" once both are reduced
#  to {own, possess}). Relatedness = the size of that grounded-meaning overlap;
#  the pick is an Argmax over it — the SAME "count" shape the character metric
#  argmaxes, just a semantic count. NO hardcoded synonym table: the relatedness
#  comes entirely from grounding.
# --------------------------------------------------------------------------- #
_SEM_STOP = frozenset(
    "a an the of to in on at by for with from into onto over under and or but "
    "not no nor be been being am is are was were do does did have has had it its "
    "this that these those he she they them his her their you your i we us our me "
    "my one any some all each which who whom whose what when where why how than "
    "then if else also such per about up out off down between through before "
    "after above below again more most other same own too very can will just "
    "someone something somebody rightly right place situation".split()
)


def _wn():
    """The agent's offline WordNet corpus accessor (the same lazy loader the
    dictionary_lexicon grounding faculty uses). Returns None if unavailable."""
    try:
        from .dict_teacher import _wordnet
        return _wordnet()
    except Exception:
        return None


def _roots(tok: str, wn) -> set:
    """Normalise a surface token to its root-lemma set: the token, its morphy
    lemma across every POS, and the derivationally related forms of those lemmas
    (noun<->verb<->adj of one root collapse together — ownership/owned/owns/own,
    possession/possessor/possess). Pure WordNet morphology, no decision."""
    w = "".join(c for c in tok.lower() if c.isalnum())
    if not w or len(w) < 2 or w in _SEM_STOP:
        return set()
    base = {w}
    for pos in (wn.NOUN, wn.VERB, wn.ADJ, wn.ADV):
        m = wn.morphy(w, pos)
        if m:
            base.add(m)
    out = set(base)
    for b in list(base):
        for pos in (wn.NOUN, wn.VERB, wn.ADJ):
            for s in wn.synsets(b, pos=pos):
                for lem in s.lemmas("eng"):
                    if lem.name().lower() == b:
                        for d in lem.derivationally_related_forms():
                            out.add(d.name().replace("_", " ").lower())
    return out


def _norm_bag(text: str, wn) -> set:
    """Root-normalised content-word bag of a gloss / phrase."""
    b = set()
    for tok in text.replace("_", " ").split():
        b |= _roots(tok, wn)
    return b


def _sense_bag(word: str, wn) -> set:
    """Ground a WORD to its meaning bag: over its noun+verb senses, the
    root-normalised gloss + the root forms of its lemma names + hypernym lemmas.
    This IS the agent's grounding of the word — WordNet's own definitional data."""
    bag = set()
    for pos in (wn.NOUN, wn.VERB):
        lem = wn.morphy(word, pos) or word
        for s in wn.synsets(lem, pos=pos):
            bag |= _norm_bag(s.definition(), wn)
            for l in s.lemmas("eng"):
                bag |= _roots(l.name(), wn)
            for h in s.hypernyms():
                for l in h.lemmas("eng"):
                    bag |= _roots(l.name(), wn)
    return bag


def _edge_content_tokens(edge: str) -> list:
    """The MEANING-bearing tokens of an edge name: '_'-split, drop function words
    (owned_BY -> owned; HAS_mention -> mention; belongs_TO -> belongs). Falls back
    to all tokens if every token is a function word."""
    toks = [t for t in edge.split("_") if t and t not in _SEM_STOP]
    return toks or [t for t in edge.split("_") if t]


def _sem_score(noun: str, edge: str, wn, _noun_bag=None) -> int:
    """Semantic relatedness of a role noun and an edge type: the size of the
    overlap between the noun's grounded meaning bag and the union of the edge's
    content tokens' meaning bags. An Argmax-able count grounded in WordNet."""
    nbag = _noun_bag if _noun_bag is not None else _sense_bag(noun, wn)
    ebag = set()
    for t in _edge_content_tokens(edge):
        ebag |= _sense_bag(t, wn)
    return len(nbag & ebag)


# --------------------------------------------------------------------------- #
#  STRUCTURAL Argmax (the LAST resort — grounding by USE, not name)
#
#  When BOTH the character and the semantic stages decline (a coined / opaque
#  edge name like `rel_42` carries no lexical or definitional signal), the
#  noun->edge link is decided by the relation's STRUCTURE: what it CONNECTS. This
#  is the Jabberwocky principle made mechanical — a nonsense-named relation is
#  grounded by its ENDPOINT TYPES matching the role's EXPECTED FILLER TYPE, not
#  by what it is called.
#
#  Two graph-resident pieces, one Argmax:
#    (a) role-noun -> expected filler TYPE, from the noun's WordNet HYPERNYM chain
#        ("owner" is_a person/individual/... ; the noun's own is_a). Same offline
#        WordNet faculty the semantic stage grounds through — donkey=0.
#    (b) each candidate edge -> its TARGET-node TYPE, read mechanically from the
#        domain graph (src -> tgt, then the tgt node's type).
#  The match score is the SEMANTIC relatedness of the target type NAME to the
#  role's expected-type region — the semantic stage reused one level up, on the
#  TYPE names. Argmax over it; accept the UNIQUELY-best above a floor; DECLINE on
#  a tie (two opaque edges to same-typed targets: structure cannot disambiguate —
#  the honest wall past this, needs role-in-rules / co-occurrence grounding).
# --------------------------------------------------------------------------- #
def _tgt_types_by_edge(gd: dict, node_id: int) -> dict:
    """Map each out-edge TYPE on `node_id` to the set of its target node TYPES.
    Pure domain-graph read: src -> tgt, then the target node's declared type."""
    ntype = {n["id"]: n.get("type") for n in gd.get("nodes", [])}
    out: dict = {}
    for e in gd.get("edges", []):
        if e.get("src") == node_id:
            tt = ntype.get(e.get("tgt"))
            if tt:
                out.setdefault(e["type"], set()).add(tt)
    return out


def _role_type_words(noun: str, wn, levels: int = 2) -> set:
    """The role noun's EXPECTED FILLER TYPE, inferred from its WordNet HYPERNYM
    chain (owner -> {person, individual, someone, ...}; the noun's own is_a, up to
    `levels` levels). Pure WordNet morphology + taxonomy, no decision. Empty when
    the noun is not a WordNet noun or has no hypernyms — an honest 'type not
    inferable', reported by the caller."""
    words: set = set()
    lem = wn.morphy(noun, wn.NOUN) or noun
    for s in wn.synsets(lem, pos=wn.NOUN):
        frontier, depth = [s], 0
        while frontier and depth < levels:
            nxt = []
            for syn in frontier:
                for h in syn.hypernyms():
                    for l in h.lemmas("eng"):
                        words.add(l.name().replace("_", " ").lower())
                    nxt.append(h)
            frontier, depth = nxt, depth + 1
    return words


def _role_type_bag(noun: str, wn) -> set:
    """The grounded MEANING region of the role's expected filler type: the union
    of sense bags of the noun's hypernym type words. The SAME grounding idiom as
    the semantic stage, lifted one level — onto the TYPE, not the word."""
    bag: set = set()
    for w in _role_type_words(noun, wn):
        bag |= _sense_bag(w, wn)
    return bag


def _struct_score(role_type_bag: set, target_type: str, wn) -> int:
    """Structural match of a candidate edge to the role: the semantic relatedness
    of the edge's TARGET-node type NAME to the role's expected filler-type region
    — the semantic overlap count, reused on the type name. Argmax-able."""
    return len(role_type_bag & _sense_bag(str(target_type).lower(), wn))


def _ground_edge(gd: dict, anchor_id: int, noun: Optional[str], *,
                 floor: int = 3, sem_floor: int = 2, struct_floor: int = 5):
    """Ground the abstract role `noun` to a concrete edge PRESENT on the anchor
    node — character fast-path first, MEANING second, STRUCTURE last.

    Returns a dict:
      {edge, score, path, char_scored, sem_scored, struct_scored, reason}
    where `path` is 'character' (a rhyming name cleared `floor`), 'semantic' (the
    meaning-Argmax cleared `sem_floor`), 'structural' (both name stages declined;
    the target-type Argmax cleared `struct_floor` UNIQUELY), or None (declined —
    reported honestly via `reason`, NEVER fabricated). `char_scored` /
    `sem_scored` / `struct_scored` are the full candidate score tables for
    provenance; later tables are None when an earlier stage already decided.

    The DECISION is a mechanical Argmax over a score in EVERY stage — a character
    count, then a grounded-meaning count, then a target-type-match count. No
    if/else picks a named edge; no hardcoded synonym or type map."""
    none = {"edge": None, "score": 0, "path": None, "char_scored": [],
            "sem_scored": None, "struct_scored": None, "reason": None}
    cands = _out_edge_types(gd, anchor_id)
    if not cands or not noun:
        return none

    # --- stage 1: character overlap (cheap; right when names rhyme) ----------
    char_scored = sorted(((c, _score(noun, c)) for c in cands), key=lambda x: -x[1])
    best_edge, best = char_scored[0]
    if best >= floor:
        return {"edge": best_edge, "score": best, "path": "character",
                "char_scored": char_scored, "sem_scored": None,
                "struct_scored": None, "reason": None}

    # --- stage 2: semantic relatedness (grounded meaning; names differ) ------
    wn = _wn()
    if wn is None:
        return {**none, "score": best, "char_scored": char_scored,
                "reason": "no WordNet (offline faculty unavailable)"}
    noun_bag = _sense_bag(noun, wn)
    sem_scored = sorted(((c, _sem_score(noun, c, wn, noun_bag)) for c in cands),
                        key=lambda x: -x[1])
    sem_edge, sem_best = sem_scored[0]
    if sem_best >= sem_floor:
        return {"edge": sem_edge, "score": sem_best, "path": "semantic",
                "char_scored": char_scored, "sem_scored": sem_scored,
                "struct_scored": None, "reason": None}

    # --- stage 3: STRUCTURAL (grounding by USE; both name stages declined) ---
    role_type_bag = _role_type_bag(noun, wn)
    base = {"score": sem_best, "path": None, "char_scored": char_scored,
            "sem_scored": sem_scored}
    if not role_type_bag:
        return {**base, "edge": None, "struct_scored": [],
                "reason": "role %r has no inferable WordNet filler-type "
                          "(no noun hypernym)" % noun}

    tgt_types = _tgt_types_by_edge(gd, anchor_id)
    struct_scored = []
    for c in cands:
        best_tt, best_s = None, 0
        for tt in tgt_types.get(c, set()):
            sc = _struct_score(role_type_bag, tt, wn)
            if best_tt is None or sc > best_s:
                best_tt, best_s = tt, sc
        struct_scored.append((c, best_tt, best_s))
    struct_scored.sort(key=lambda x: -x[2])

    top = struct_scored[0]
    # UNIQUENESS: a rival tied at the top score is structural ambiguity — two
    # opaque edges to same-scoring (typically same-typed) targets. Structure
    # cannot disambiguate -> DECLINE (the honest wall; needs use/co-occurrence).
    ambiguous = len(struct_scored) > 1 and struct_scored[1][2] == top[2]
    if top[2] < struct_floor:
        return {**base, "edge": None, "struct_scored": struct_scored,
                "reason": "best target-type match %r->%s scored %d, below "
                          "struct_floor %d (no edge to a role-typed node)"
                          % (top[0], top[1], top[2], struct_floor)}
    if ambiguous:
        return {**base, "edge": None, "struct_scored": struct_scored,
                "reason": "structural AMBIGUITY - edges %r and %r both reach a "
                          "%s-typed target (score %d): structure cannot "
                          "disambiguate" % (top[0], struct_scored[1][0],
                                            top[1], top[2])}
    return {"edge": top[0], "score": top[2], "path": "structural",
            "char_scored": char_scored, "sem_scored": sem_scored,
            "struct_scored": struct_scored, "reason": None}


def _score_table(g: dict) -> str:
    """Human-readable candidate score table for provenance: the character scores
    always, plus the semantic and structural scores when those stages ran."""
    parts = ["char=%s" % g["char_scored"]]
    if g.get("sem_scored") is not None:
        parts.append("semantic=%s" % g["sem_scored"])
    if g.get("struct_scored") is not None:
        parts.append("structural[(edge,tgt_type,score)]=%s" % g["struct_scored"])
    if g.get("reason"):
        parts.append("declined: %s" % g["reason"])
    return "; ".join(parts)


# --------------------------------------------------------------------------- #
#  the model reads (mechanical)
# --------------------------------------------------------------------------- #
def _steps(model) -> list:
    return model.get("steps", []) if isinstance(model, dict) else list(model)


def _action(model) -> Optional[dict]:
    for st in _steps(model):
        if (st.get("main") or {}).get("kind") == "action":
            return st
    return None


def _definition(model) -> Optional[dict]:
    for st in _steps(model):
        if (st.get("main") or {}).get("kind") == "definition":
            return st["main"]
    return None


def _relation_between(model, a, b) -> Optional[str]:
    for st in _steps(model):
        m = st.get("main") or {}
        if m.get("kind") == "relation":
            if (m.get("subject"), m.get("object")) in ((a, b), (b, a)):
                return m.get("relation")
    return None


def _numeric_value_attr(attrs: dict, exclude=("kind",)) -> Optional[str]:
    """The concrete value slot on the patient node: a numeric attr that is not a
    discriminator. Returns the attr name or None."""
    for k, v in attrs.items():
        if k in exclude:
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return k
    return None


def _element_value_attr(gd: dict, src_id: int, edge: str) -> Optional[str]:
    """The reduced-over VALUE attr for a Sum/Mean/Max/Min aggregate: the numeric
    slot on a COLLECTION ELEMENT node reached by `edge` from the source. Read from
    the domain graph (the definition names the collection — 'sum of the readings'
    — the graph names WHICH numeric slot is summed), so the synthesiser no longer
    falls back to a hardcoded 'value'. Returns the attr name or None."""
    nid_by = {n["id"]: n for n in gd.get("nodes", [])}
    for e in gd.get("edges", []):
        if e.get("src") == src_id and e.get("type") == edge:
            el = nid_by.get(e.get("tgt"))
            if el is not None:
                va = _numeric_value_attr(el.get("attrs", {}) or {})
                if va:
                    return va
    return None


# --------------------------------------------------------------------------- #
#  the resolver
# --------------------------------------------------------------------------- #
def derive_binding(agent, model) -> dict:
    """Ground the binding for `model` from the domain graph + read text. Returns
    {binding, provenance, role_nodes, grounded_forms, underspecified}."""
    gd = _graph(agent)
    prov: list = []
    binding: dict = {}
    underspecified: list = []

    act = _action(model)
    if act is None:
        return {"binding": binding, "provenance": ["no action step - nothing to bind"],
                "underspecified": ["action"], "role_nodes": {}, "grounded_forms": []}
    main = act["main"]
    effect = main.get("effect")
    patient = main.get("patient")
    roles = main.get("roles") or {}
    trig = act.get("trigger") or {}

    # (a) attempt to GROUND the role nouns' meaning via the teacher loop (memoised).
    role_nouns = [n for n in [patient, roles.get("source"), roles.get("target")] if n]
    grounded_forms: list = []
    if hasattr(agent, "ground_unknowns"):
        try:
            grounded_forms = agent.ground_unknowns(" ".join(role_nouns))
        except Exception:
            grounded_forms = []
    prov.append("grounding faculty: ground_unknowns(%s) -> %s%s"
                % (role_nouns, grounded_forms,
                   "  (offline no-op; binding uses the domain graph, not the teacher)"
                   if not grounded_forms else ""))

    # (b) role-noun -> concrete node (domain-graph read)
    role_nodes: dict = {}
    for rn in [patient, roles.get("source"), roles.get("target")]:
        if not rn or rn in role_nodes:
            continue
        node = _resolve_role_node(gd, rn)
        role_nodes[rn] = node
        if node:
            prov.append("role %r -> node #%d (%s) via %s"
                        % (rn, node["id"], node["type"], node["via"]))
        else:
            prov.append("role %r -> (no direct node; a possessive target reached by an edge)" % rn)

    # ---- recompute: value_attr + aggregate ---------------------------------
    if effect == "recompute":
        src_noun = roles.get("source")
        pat_node = role_nodes.get(patient)
        src_node = role_nodes.get(src_noun)

        # value_attr from the concrete patient node's numeric slot
        if pat_node:
            va = _numeric_value_attr(pat_node["attrs"])
            if va:
                binding["value_attr"] = va
                prov.append("value_attr = %r  <- numeric slot on the concrete %r node "
                            "(the definition says the view HOLDS a value but never names the attr; "
                            "read from the domain graph)" % (va, patient))
            else:
                underspecified.append("value_attr")
                prov.append("value_attr UNDERSPECIFIED - no numeric slot on the %r node" % patient)

        # aggregate.op from the read definition
        defn = _definition(model)
        if defn and defn.get("aggregate_op"):
            op = defn["aggregate_op"]
            coll = defn.get("collection")
            prov.append("aggregate.op = %r  <- READ DEFINITION %r (agg word -> %s)"
                        % (op, defn.get("subject"), op))
            # aggregate.edge: ground the definition's collection noun to an edge on source
            if src_node:
                g = _ground_edge(gd, src_node["id"], coll)
                if g["edge"]:
                    binding["aggregate"] = {"op": op, "edge": g["edge"]}
                    prov.append("aggregate.edge = %r  <- collection noun %r grounded to an edge "
                                "PRESENT on the %r node via the %s Argmax (%s, score %d)"
                                % (g["edge"], coll, src_noun, g["path"],
                                   _score_table(g), g["score"]))
                    # a value-reducing op (Sum/Mean/Max/Min) reduces over a NUMERIC
                    # slot on each element — ground WHICH slot from the graph, so
                    # the synthesiser stops defaulting to a hardcoded 'value'.
                    if op != "Count":
                        va2 = _element_value_attr(gd, src_node["id"], g["edge"])
                        if va2:
                            binding["aggregate"]["value_attr"] = va2
                            prov.append("aggregate.value_attr = %r  <- numeric slot on a %r "
                                        "element (read from the domain graph; the definition "
                                        "names the collection, the graph names the reduced attr)"
                                        % (va2, coll))
                        else:
                            underspecified.append("aggregate.value_attr")
                            prov.append("aggregate.value_attr UNDERSPECIFIED - no numeric slot on "
                                        "the %r elements (synthesiser falls back to 'value')" % coll)
                else:
                    underspecified.append("aggregate.edge")
                    prov.append("aggregate.edge UNDERSPECIFIED - collection %r matched no edge on %r "
                                "above floor (%s)" % (coll, src_noun, _score_table(g)))
            else:
                underspecified.append("aggregate.edge")
                prov.append("aggregate.edge UNDERSPECIFIED - no concrete %r node" % src_noun)
        else:
            underspecified.append("aggregate")
            prov.append("aggregate UNDERSPECIFIED - the maintenance method alone does not say WHICH "
                        "function; supply a DEFINITION sentence ('A view holds the count of ...')")

    # ---- add / del edge: role_relation (possessive target) + state_attr ----
    if effect in ("add_edge", "del_edge"):
        src_noun = roles.get("source")
        tgt_noun = roles.get("target")
        src_node = role_nodes.get(src_noun)

        # role_relation: only needed for a POSSESSIVE target the text names no
        # relation for. If a relation step already binds source<->target, leave it
        # (synthesise reads it from the model).
        named = _relation_between(model, src_noun, tgt_noun)
        if named:
            prov.append("role_relation from a READ relation step: %r -%s-> %r (no grounding needed)"
                        % (src_noun, named, tgt_noun))
        elif src_node:
            # ground the possessive noun's meaning (memoised) then match to a domain edge
            if hasattr(agent, "ground_unknowns"):
                try:
                    agent.ground_unknowns(str(tgt_noun))
                except Exception:
                    pass
            g = _ground_edge(gd, src_node["id"], tgt_noun)
            if g["edge"]:
                binding["role_relation"] = g["edge"]
                prov.append("role_relation = %r  <- possessive target %r grounded to an edge "
                            "PRESENT on the %r node via the %s Argmax (%s, score %d)"
                            % (g["edge"], tgt_noun, src_noun, g["path"],
                               _score_table(g), g["score"]))
            else:
                underspecified.append("role_relation")
                prov.append("role_relation UNDERSPECIFIED - target %r matched no edge on %r "
                            "above floor (%s)" % (tgt_noun, src_noun, _score_table(g)))
        else:
            underspecified.append("role_relation")
            prov.append("role_relation UNDERSPECIFIED - no concrete %r node to anchor on" % src_noun)

        # state_attr: the trigger state word -> an attr present on the source node
        if trig.get("kind") == "state" and trig.get("state"):
            state = trig["state"]
            if src_node and state in (src_node["attrs"] or {}):
                binding["state_attr"] = {state: state}
                prov.append("state_attr[%r] = %r  <- trigger state grounded to an attr PRESENT on "
                            "the %r node (identity, confirmed by the domain graph)"
                            % (state, state, src_noun))
            else:
                underspecified.append("state_attr")
                prov.append("state_attr UNDERSPECIFIED - trigger state %r is not an attr on the %r node"
                            % (state, src_noun))

    # ---- add_node: subject_relation (anchor) + carry_attrs + node_type --------
    if effect == "add_node":
        src_noun = roles.get("source")
        src_node = role_nodes.get(src_noun)
        node_type_abs = main.get("node_type") or patient

        # subject_relation: the anchor edge a hub uses to REACH the subject, read
        # from the domain graph (the incoming edge to the concrete subject node).
        if src_node:
            in_edges = _in_edge_types(gd, src_node["id"])
            if in_edges:
                binding["subject_relation"] = in_edges[0]
                prov.append("subject_relation = %r  <- incoming edge REACHING the concrete "
                            "%r node (read from the domain graph; the rule matches hub -%s-> %s)"
                            % (in_edges[0], src_noun, in_edges[0], src_noun))
            else:
                underspecified.append("subject_relation")
                prov.append("subject_relation UNDERSPECIFIED - no incoming edge reaches the %r node"
                            % src_noun)
            # carry_attrs: the subject's non-discriminator SCALAR slots — the data
            # the minted node mirrors (attr-propagation source), read from the graph.
            carry = [k for k, v in (src_node["attrs"] or {}).items()
                     if k != "kind" and isinstance(v, (int, float, str))
                     and not isinstance(v, bool)]
            if carry:
                binding["carry_attrs"] = carry
                prov.append("carry_attrs = %r  <- scalar slots on the concrete %r node "
                            "(the minted node carries the subject's data; attr-propagation)"
                            % (carry, src_noun))
        else:
            underspecified.append("subject_relation")
            prov.append("subject_relation UNDERSPECIFIED - no concrete %r node to anchor on" % src_noun)

        # node_type: TitleCase of the read noun, confirmed if a node of that type
        # already exists in the domain graph.
        if node_type_abs:
            concrete = "".join(w[:1].upper() + w[1:] for w in str(node_type_abs).split())
            exists = any(str(n.get("type", "")) == concrete for n in gd.get("nodes", []))
            binding["node_types"] = {node_type_abs: concrete}
            prov.append("node_type[%r] = %r  <- TitleCase of the read noun%s"
                        % (node_type_abs, concrete,
                           " (confirmed: a node of that type exists)" if exists
                           else " (no such node yet; the type is minted fresh)"))

        # state_attr: the trigger state word -> an attr present on the source node
        if trig.get("kind") == "state" and trig.get("state"):
            state = trig["state"]
            if src_node and state in (src_node["attrs"] or {}):
                binding["state_attr"] = {state: state}
                prov.append("state_attr[%r] = %r  <- trigger state grounded to an attr PRESENT on "
                            "the %r node (identity, confirmed by the domain graph)"
                            % (state, state, src_noun))
            else:
                underspecified.append("state_attr")
                prov.append("state_attr UNDERSPECIFIED - trigger state %r is not an attr on the %r node"
                            % (state, src_noun))

    # ---- classify: fact/codebook/classification edges + types + copied fields --
    if effect == "classify":
        # The join clause (act.trigger, kind=='join') names the FACT and CODEBOOK
        # collection types + the join keys; the main clause names the
        # classification type. Ground each abstract collection type to a concrete
        # domain node type + the has_ edge REACHING it from the agent hub (read
        # from the domain graph), and default the copied fields to the concrete
        # nodes' scalar slots. The rename/guard detail the minimal text does not
        # name is left honestly underspecified (same contract as every branch).
        trig = act.get("trigger") or {}
        fact_abs = trig.get("fact_type")
        cb_abs = trig.get("codebook_type")
        fk = trig.get("fact_key")
        ck = trig.get("codebook_key")
        cls_abs = main.get("node_type") or patient
        node_types: dict = {}
        ag_id = getattr(agent, "agent", None)
        ag_id = _node_int(ag_id) if ag_id is not None else None

        # This shape matches TWO agent-held COLLECTIONS, so resolve each abstract
        # collection type to a node of that TYPE reached by an incoming edge FROM
        # the agent hub — the collection pattern — not a stray same-named seed
        # Concept's kind/name attr (which the generic _resolve_role_node would
        # collide with for common words). Returns (edge_type, node) or (None,None).
        fmember = _collection_member(gd, fact_abs, ag_id)
        cmember = _collection_member(gd, cb_abs, ag_id)

        if fmember:
            fedge, fnode = fmember
            node_types[fact_abs] = fnode["type"]
            binding["fact_edge"] = fedge
            prov.append("fact_edge = %r  <- the agent-hub edge REACHING a %r-typed collection "
                        "member (%s) (read from the domain graph; the collection pattern, not a "
                        "same-named Concept)" % (fedge, fact_abs, fnode["type"]))
            fcarry = [k for k, v in (fnode["attrs"] or {}).items()
                      if k != "kind" and isinstance(v, (int, float, str)) and not isinstance(v, bool)]
            if fk and fk not in fcarry and fk in (fnode["attrs"] or {}):
                fcarry.append(fk)
            if fcarry:
                binding["fact_carry"] = fcarry
                prov.append("fact_carry = %r  <- scalar slots on the concrete %r node "
                            "(the classification mirrors the fact's data)" % (fcarry, fact_abs))
        else:
            underspecified.append("fact_edge")
            prov.append("fact_edge UNDERSPECIFIED - no agent-held %r collection in the domain graph" % fact_abs)

        if cmember:
            cedge, cnode = cmember
            node_types[cb_abs] = cnode["type"]
            binding["codebook_edge"] = cedge
            prov.append("codebook_edge = %r  <- the agent-hub edge REACHING a %r-typed collection "
                        "member (%s) (read from the domain graph)" % (cedge, cb_abs, cnode["type"]))
            ccarry = {k: k for k, v in (cnode["attrs"] or {}).items()
                      if k != ck and k != "kind"
                      and isinstance(v, (int, float, str)) and not isinstance(v, bool)}
            if ccarry:
                binding["codebook_carry"] = ccarry
                prov.append("codebook_carry = %r  <- non-join scalar slots on the concrete %r "
                            "node (the classification carries the codebook's verdict)" % (ccarry, cb_abs))
        else:
            underspecified.append("codebook_edge")
            prov.append("codebook_edge UNDERSPECIFIED - no agent-held %r collection in the domain graph" % cb_abs)

        # classification edge: minted nodes do not exist yet to read an edge from,
        # so the has_ edge is derived by the graph's own naming convention
        # ('has_<snake type>') — confirmed if a node/edge of that shape exists.
        if cls_abs:
            concrete_cls = "".join(w[:1].upper() + w[1:] for w in str(cls_abs).split())
            node_types[cls_abs] = concrete_cls
            cls_edge = "has_" + "_".join(str(cls_abs).lower().split())
            binding["classification_edge"] = cls_edge
            existing = any(e.get("type") == cls_edge for e in gd.get("edges", []))
            prov.append("classification_edge = %r  <- 'has_<type>' naming convention for the "
                        "minted %r node%s" % (cls_edge, concrete_cls,
                        " (confirmed: an edge of that type exists)" if existing
                        else " (minted fresh; no such edge yet)"))

        if node_types:
            binding["node_types"] = node_types

    return {"binding": binding, "provenance": prov, "role_nodes": role_nodes,
            "grounded_forms": grounded_forms, "underspecified": underspecified}


__all__ = ["derive_binding"]
