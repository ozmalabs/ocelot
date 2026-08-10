"""name_variant_merge — UNIFY A PERSON'S NAME FORMS INTO ONE ENTITY, and make
gender PER-ENTITY precise, as an ADDITIVE post-read refinement over the coref
graph. Generic (any person), NOT a name table, donkey=0, no `import re`.

THE PROBLEM (the Marie-Curie residuals 2 + 3, measured on the full article):

  · NAME-VARIANT FRAGMENTATION — one person surfaces as FOUR entities: the full
    name `marie_curie`, the surname `curie`, the first name `maria`/`marie`, the
    maiden name `skłodowska` (introduced 'née Skłodowska'). The salience read then
    splits the subject four ways.
  · GENDER-LEAK — the dominant female 'she' bleeds female onto non-animate
    entities (a date `1891`, a substance `radium`, an institution `university`)
    and onto other people, because the read-time dequant is first-pronoun-wins.

THE FIX, two graph passes (run AFTER comprehension, on the encyclopedic route):

  (1) NAME-VARIANT MERGE. A person's name forms are linked by MECHANICAL name
      structure — the SAME reference-I/O status as coref's own cleanliness /
      function-word grounding, not an agent decision over meaning:

        · CONTAINMENT (name-part overlap): a surname/first-name is a TOKEN of a
          full name ('curie' ⊂ 'marie_curie', 'pierre' ⊂ 'pierre_curie').
        · FIRST-NAME VARIANT: two single-token names one edit apart, same initial
          ('maria' ~ 'marie').
        · ALIAS INTRODUCTION: 'née X' / 'born X' / 'known as X' names an alias of
          the subject (maiden name) — a mechanical text-cue scan.

      Full names seed the clusters; a SHARED surname ('curie', a token of BOTH
      'marie_curie' and 'pierre_curie') attaches to the MOST-SALIENT cluster, so
      two different people who merely share a surname stay DISTINCT (the
      no-over-merge discipline). Links are real graph edges (`name_part_of` /
      `name_variant_of` / `alias_of`); the canonical (most-salient) member of each
      cluster is picked by a NATIVE Argmax (not a Python max); the merge then sums
      `coref_mentions` onto the canonical, redirects every `refers_to` Mention onto
      it, and drops the absorbed forms from the salient pool
      (coref_cleanliness := 0, `merged_into` recorded) so the subject read returns
      ONE unified entity.

  (2) GENDER PRECISION. Gender is decoded PER-ENTITY from ITS OWN evidence, never
      the ambient dominant gender:

        · a NON-animate entity (a date/substance/institution — coref_animate 0)
          carries NO gender (coref_gender := '').
        · an ANIMATE entity's gender is its OWN object-property gender (WordNet:
          woman->female, king->male) if any, else the majority of the gendered
          pronouns that refer to it — preferring the pronouns anchored to its
          LEAST-AMBIGUOUS (full-name) form, since a bare given/surname attracts
          stray binds. The gender pick is a native Argmax over {male, female}
          candidate nodes scored by the entity's own evidence, else '' (honest
          underspecified).

ARCHITECTURE (CLAUDE.md): this is a world-adapter refinement over graph data.
Name structure + WordNet are mechanical reads (the coref-grounding idiom); every
DECISION that ranges over graph state — the canonical pick, the gender pick — is a
graph-native Argmax the Rust evaluator runs, never a Python max/sorted. No agent
if/else decides meaning. Scoped to the encyclopedic subject read, so the fable /
crow path never calls it (byte-identical).
"""
from __future__ import annotations

from typing import Optional

from domains import coref_entities as ce
from domains import gender_shape as gs

_ALIAS_CUES = frozenset(("née", "nee"))               # the specific maiden-name cue
_ALIAS_PHRASE_HEAD = frozenset(("known", "called"))   # 'better known as X' / 'called X'
_HE_FORMS = frozenset(("he", "him", "his"))
_SHE_FORMS = frozenset(("she", "her", "hers"))


# --------------------------------------------------------------------------- #
#  resolve + small graph helpers (the domains/*.py idiom).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _name_tokens(name: str) -> list:
    """The de-underscored, possessive-stripped tokens of a name. Mechanical string
    split (no regex): 'marie_curie'->[marie,curie], \"curie's\"->[curie]."""
    out = []
    for raw in str(name).split("_"):
        t = raw.strip().lower()
        if t.endswith("'s"):
            t = t[:-2]
        t = t.strip("'.,")
        if t:
            out.append(t)
    return out


def _V(n):
    return {"type": "Var", "name": n}


def _Lit(v):
    return {"type": "Lit", "value": v}


def _Attr(node, k):
    return {"type": "Attr", "node": node, "key": k}


def _Argmax(src, var, val):
    return {"type": "Argmax", "source": src, "var_name": var, "value": val,
            "default": None}


# --------------------------------------------------------------------------- #
#  proper-name entities + name structure — mechanical reads over the graph/text.
# --------------------------------------------------------------------------- #
def _case_stats(text: str) -> dict:
    """Per-surface (capitalised_count, lowercase_count) over the text's standalone
    tokens — a mechanical case scan (no regex). A DOMINANTLY-capitalised surface is
    a PROPER name ('Curie' cap 60 / low 3, the stray unit); a dominantly-lowercase
    surface is a common noun ('radium','university')."""
    stats: dict = {}
    for tok in str(text).split():
        t = tok.strip(".,!?;:\"'()[]«»").strip()
        if not t or not t.isalpha():
            continue
        key = t.lower()
        cap, low = stats.get(key, (0, 0))
        if t[0].isupper():
            stats[key] = (cap + 1, low)
        else:
            stats[key] = (cap, low + 1)
    return stats


def _is_proper_token(t: str, stats: dict) -> bool:
    cap, low = stats.get(t, (0, 0))
    return cap >= 1 and cap >= low            # dominantly capitalised => proper


def _is_common_token(t: str, stats: dict) -> bool:
    cap, low = stats.get(t, (0, 0))
    return low >= 1 and low >= cap            # dominantly lowercase => common noun


def _is_proper_name_entity(sub, nid, stats: dict) -> bool:
    """Is this SmEntity a PROPER personal-name form? Every token is alphabetic and
    DOMINANTLY capitalised in the text (a proper name, robust to a stray lowercase
    homonym like the 'curie' radioactivity unit), it is not a long parse-glom, and
    it is a plausible animate name. A common role-noun ('scientist','woman') is
    dominantly lowercase -> excluded; a date/substance is non-animate -> excluded."""
    at = sub.node(nid)["attrs"]
    nm = at.get("name")
    if not isinstance(nm, str) or not nm:
        return False
    toks = _name_tokens(nm)
    if not toks or len(toks) > 4:
        return False
    for t in toks:
        if not t.isalpha() or not _is_proper_token(t, stats):
            return False
    return True


def _edit_distance_one(a: str, b: str) -> bool:
    """Are `a` and `b` within edit distance 1 (a first-name spelling variant:
    maria~marie)? A tiny mechanical DP, same initial letter, both length >= 3."""
    if not a or not b or a[0] != b[0] or min(len(a), len(b)) < 3:
        return False
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    # count mismatches under best alignment
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    # one insertion/deletion
    short, long = (a, b) if la < lb else (b, a)
    i = j = 0
    skips = 0
    while i < len(short) and j < len(long):
        if short[i] == long[j]:
            i += 1
            j += 1
        else:
            skips += 1
            j += 1
            if skips > 1:
                return False
    return True


# --------------------------------------------------------------------------- #
#  ALIAS scan — 'née X' / 'born X' / 'better known as X' link X to the subject.
# --------------------------------------------------------------------------- #
def _alias_surfaces(text: str) -> set:
    """The proper tokens introduced by an ALIAS cue ('née Skłodowska',
    'better known as Marie', 'formerly Smith') — a mechanical cue scan (no regex).
    Each such token is a maiden/alias name of the document SUBJECT."""
    aliases = set()
    toks = str(text).split()
    stripped = [t.strip(".,!?;:\"'()[]«»") for t in toks]
    lows = [s.lower() for s in stripped]
    for i, w in enumerate(lows):
        take = False
        if w in _ALIAS_CUES:
            take = True
        elif w == "as" and i >= 1 and lows[i - 1] in _ALIAS_PHRASE_HEAD:
            take = True
        if not take:
            continue
        # the following capitalised alphabetic token(s) are the alias
        j = i + 1
        while (j < len(stripped) and j < i + 4
               and stripped[j][:1].isupper() and stripped[j].isalpha()
               and len(stripped[j]) >= 3):
            aliases.add(lows[j])
            j += 1
    return aliases


# --------------------------------------------------------------------------- #
#  CLUSTERING — full names seed; single tokens attach to their distinctive
#  full-name cluster; a shared surname attaches to the most-salient cluster.
# --------------------------------------------------------------------------- #
def _cluster(sub, native, ents: list, subject_name: Optional[str], aliases: set) -> list:
    """Group proper-name entities into person clusters by name structure. Returns
    a list of clusters, each a set of entity-names. No over-merge: two full names
    that are not token-compatible (differ in their distinctive token) stay in
    DIFFERENT clusters even when they share a surname."""
    names = {sub.node(n)["attrs"].get("name"): n for n in ents}
    toks = {nm: _name_tokens(nm) for nm in names}
    ment = {nm: float(sub.node(n)["attrs"].get("coref_mentions", 0.0) or 0.0)
            for nm, n in names.items()}
    full = [nm for nm in names if len(toks[nm]) >= 2]
    singles = [nm for nm in names if len(toks[nm]) == 1]

    # 1. seed clusters from full names; two full names merge iff one token-set is a
    #    subset of the other (same person named more/less fully). {marie,curie} and
    #    {pierre,curie} are NOT subsets -> distinct.
    clusters = [set([nm]) for nm in full]

    def _tokset(nm):
        return set(toks[nm])

    merged = True
    while merged:
        merged = False
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                ta = set().union(*[_tokset(x) for x in clusters[a]])
                tb = set().union(*[_tokset(x) for x in clusters[b]])
                if ta <= tb or tb <= ta:
                    clusters[a] |= clusters[b]
                    clusters.pop(b)
                    merged = True
                    break
            if merged:
                break

    # token -> which cluster indices contain a full name with that token
    tok_clusters: dict = {}
    for ci, cl in enumerate(clusters):
        cl_toks = set().union(*[_tokset(x) for x in cl]) if cl else set()
        for t in cl_toks:
            tok_clusters.setdefault(t, set()).add(ci)

    def _cluster_saliency(ci):
        return sum(ment[x] for x in clusters[ci])

    # 2. attach single-token names.
    unattached = []
    for nm in singles:
        t = toks[nm][0]
        owners = tok_clusters.get(t, set())
        if len(owners) == 1:
            clusters[next(iter(owners))].add(nm)          # distinctive token
        elif len(owners) > 1:
            best = max(owners, key=_cluster_saliency)      # shared surname -> most salient
            clusters[best].add(nm)
        else:
            unattached.append(nm)

    # 3. first-name variants: attach an unattached single to a cluster holding a
    #    variant single (maria ~ marie).
    still = []
    for nm in unattached:
        t = toks[nm][0]
        placed = False
        for ci, cl in enumerate(clusters):
            for other in cl:
                ots = toks[other]
                if len(ots) == 1 and _edit_distance_one(t, ots[0]):
                    cl.add(nm)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            still.append(nm)

    # 4. alias tokens -> the SUBJECT's cluster (maiden name 'née Skłodowska'). The
    #    subject cluster is the one that holds the subject as an EXACT member (a bare
    #    surname 'curie' was placed on the most-salient cluster in step 2) — NEVER a
    #    cluster that merely shares the surname TOKEN (that is Pierre's cluster, which
    #    also contains the 'curie' token; matching it would over-merge Pierre in).
    subj_ci = None
    if subject_name is not None:
        for ci, cl in enumerate(clusters):
            if subject_name in cl:
                subj_ci = ci
                break
    for nm in list(still):
        if nm in aliases and subj_ci is not None:
            clusters[subj_ci].add(nm)
            still.remove(nm)

    # PERSON-CLUSTER filter: keep a cluster only if it is pronominalised as a PERSON
    # — its members carry >= 2 gendered person-pronouns (he/she/him/her/his) — and
    # is animate. This drops institution/place proper-name clusters (academy, press,
    # united states, a book title) that share the full-name SHAPE but are never a
    # he/she referent, so the merge stays a PERSON unification (no over-merge of an
    # institution into a person). WordNet is NOT used to gate person-ness (it types
    # 'pierre'->location, 'maria'->lunar-mare, 'curie'->unit — actively misleading
    # for names); the discourse's own pronoun use is the honest signal.
    out = []
    for cl in clusters:
        if len(cl) < 2:
            continue
        if _cluster_is_person(sub, native, names, cl):
            out.append(cl)
    return out


def _cluster_is_person(sub, native, names: dict, cluster: set) -> bool:
    """A cluster is a PERSON iff its members are collectively referred to by >= 2
    gendered person-pronouns (he/she/him/her/his/hers) and its canonical is animate.
    A mechanical read of refers_to Mention surfaces — the pronoun evidence decides,
    not a name table."""
    g = 0
    animate = False
    for nm in cluster:
        node = names.get(nm)
        if node is None:
            continue
        if float(sub.node(node)["attrs"].get("coref_animate", 1.0) or 0.0) == 1.0:
            animate = True
        for m in native.in_neighbours(node, "refers_to"):
            surf = str(sub.node(m)["attrs"].get("surface", "")).lower()
            if surf in _HE_FORMS or surf in _SHE_FORMS:
                g += 1
    return animate and g >= 2


# --------------------------------------------------------------------------- #
#  canonical pick + merge (graph-native Argmax + mechanical rewrite).
# --------------------------------------------------------------------------- #
def _canonical(agent, cluster_names: set):
    """The most-salient cluster member, picked by a NATIVE Argmax over the SmEntity
    pool filtered to the cluster names (not a Python max)."""
    sub, native = _resolve(agent)
    conds = [{"type": "Eq", "a": _Attr(_V("e"), "name"), "b": _Lit(nm)}
             for nm in cluster_names]
    pred = conds[0] if len(conds) == 1 else {"type": "Or", "items": conds}
    pool = {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "SmEntity"},
            "var_name": "e", "predicate": pred}
    winner = native.evaluate(
        _Argmax(pool, "e", _Attr(_V("e"), "coref_mentions")), {})
    return winner


def _entity_by_name(sub, name: str):
    for n in sub.nodes("SmEntity"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


def _redirect_mentions(sub, native, src_node, dst_node):
    """Redirect every `refers_to` Mention from src onto dst — a mechanical edge
    rewrite (the coref idiom), so dst inherits src's pronoun evidence."""
    for m in list(native.in_neighbours(src_node, "refers_to")):
        sub.remove_edge(m, "refers_to", src_node)
        native.add_edge_unchecked(m, "refers_to", dst_node)


def merge_name_variants(agent, text: str) -> dict:
    """Cluster + merge a person's name forms into ONE entity. Returns a ledger:
    {clusters:[{canonical, absorbed, mentions_before, mentions_after}], ...}."""
    sub, native = _resolve(agent)
    from domains import register_source as rs
    subj = rs.subject_by_salience(agent).get("subject")
    stats = _case_stats(text)
    aliases = _alias_surfaces(text)
    ents = [n for n in sub.nodes("SmEntity") if _is_proper_name_entity(sub, n, stats)]
    clusters = _cluster(sub, native, ents, subj, aliases)
    ledger = []
    for cl in clusters:
        canon = _canonical(agent, cl)
        if canon is None:
            continue
        canon_name = sub.node(canon)["attrs"].get("name")
        # DECIDE the cluster's gender BEFORE redirecting mentions, from the members'
        # OWN pre-merge evidence: the LEAST-AMBIGUOUS (most-token full-name) member
        # that carries a gendered pronoun / object-property gender decides — a bare
        # given/surname attracts stray binds ('pierre' catches Marie's 'she'), the
        # full name 'Pierre Curie' does not. This is how Pierre resolves MALE though
        # the reduced 'pierre' leaked female.
        cgender = _cluster_gender(agent, sub, native, cl)
        m_before = float(sub.node(canon)["attrs"].get("coref_mentions", 0.0) or 0.0)
        absorbed = []
        added_ment = 0.0
        for nm in cl:
            if nm == canon_name:
                continue
            node = _entity_by_name(sub, nm)
            if node is None:
                continue
            native.add_edge_unchecked(node, "name_variant_of", canon)
            added_ment += float(sub.node(node)["attrs"].get("coref_mentions", 0.0) or 0.0)
            _redirect_mentions(sub, native, node, canon)
            sub.set_attr(node, "coref_cleanliness", 0.0)     # drop from the salient pool
            sub.set_attr(node, "coref_gender", "")           # the canonical carries gender
            sub.set_attr(node, "merged_into", canon_name)
            absorbed.append(nm)
        sub.set_attr(canon, "coref_mentions", m_before + added_ment)
        sub.set_attr(canon, "coref_gender", cgender)
        sub.set_attr(canon, "gender_authoritative", 1.0)     # refine_gender keeps this
        ledger.append({"canonical": canon_name, "absorbed": sorted(absorbed),
                       "gender": cgender,
                       "mentions_before": m_before,
                       "mentions_after": m_before + added_ment})
    return {"subject": subj, "clusters": ledger, "aliases": sorted(aliases)}


def _cluster_gender(agent, sub, native, cluster: set) -> str:
    """The cluster's gender from members' OWN pre-merge evidence, preferring the
    most-token (least-ambiguous) member: object-property gender is decisive, else
    the member's own gendered-pronoun majority. Members are considered in order of
    DESCENDING token count, so 'pierre_curie' (he) outweighs 'pierre' (leaked she)."""
    names = {sub.node(n)["attrs"].get("name"): n for n in
             [_entity_by_name(sub, nm) for nm in cluster] if n is not None}
    ordered = sorted(cluster, key=lambda nm: -len(_name_tokens(nm)))
    for nm in ordered:
        node = names.get(nm)
        if node is None:
            continue
        prop = gs.object_property_gender(nm)
        if prop in ("male", "female"):
            return prop
        m = f = 0
        for men in native.in_neighbours(node, "refers_to"):
            surf = str(sub.node(men)["attrs"].get("surface", "")).lower()
            if surf in _HE_FORMS:
                m += 1
            elif surf in _SHE_FORMS:
                f += 1
        if m or f:
            return "male" if m >= f else "female"
    return ""


# --------------------------------------------------------------------------- #
#  GENDER PRECISION — per-entity, own-evidence, via a native Argmax.
# --------------------------------------------------------------------------- #
def _gender_evidence(sub, native, node) -> tuple:
    """(male_ev, female_ev) — the entity's OWN gendered-pronoun votes, preferring
    the FULL-NAME (multi-token) form's pronouns when this is a merged canonical
    (a bare given/surname attracts stray binds, so a full-name anchor is trusted
    over the reduced form). Reads refers_to Mention surfaces off the graph."""
    def votes(target):
        m = f = 0
        for men in native.in_neighbours(target, "refers_to"):
            surf = str(sub.node(men)["attrs"].get("surface", "")).lower()
            if surf in _HE_FORMS:
                m += 1
            elif surf in _SHE_FORMS:
                f += 1
        return m, f
    # full-name variants that merged INTO this node
    full_anchor = None
    for v in native.in_neighbours(node, "name_variant_of"):
        nm = sub.node(v)["attrs"].get("name")
        if isinstance(nm, str) and len(_name_tokens(nm)) >= 2:
            full_anchor = v
            break
    if full_anchor is not None:
        fm, ff = votes(full_anchor)
        if fm or ff:
            return fm, ff                     # trust the least-ambiguous anchor
    return votes(node)


def _pick_gender(agent, male_ev: float, female_ev: float, prop: str) -> str:
    """Decide the entity's gender by a NATIVE Argmax over {male, female} Gender
    candidate nodes scored from the entity's OWN evidence (object-property gender
    is decisive; else the pronoun majority, requiring a floor so a single stray
    pronoun does not gender the entity). '' when there is no clear evidence."""
    sub, native = _resolve(agent)
    if prop in ("male", "female"):
        return prop
    # ensure two Gender candidate nodes exist (idempotent)
    have = {sub.node(n)["attrs"].get("g") for n in sub.nodes("GenderCand")}
    for g in ("male", "female"):
        if g not in have:
            sub.add_node("GenderCand", {"g": g})
    score = {"type": "IfThenElse",
             "cond": {"type": "Eq", "a": _Attr(_V("x"), "g"), "b": _Lit("male")},
             "then": _V("m"), "other": _V("f")}
    winner = native.evaluate(
        _Argmax({"type": "NodesOfType", "node_type": "GenderCand"}, "x", score),
        {"m": float(male_ev), "f": float(female_ev)})
    if winner is None:
        return ""
    g = sub.node(winner)["attrs"].get("g")
    hi, lo = (male_ev, female_ev) if g == "male" else (female_ev, male_ev)
    # a floor + margin: a lone stray pronoun (hi < 2 with no separation) is not
    # enough to gender an entity — stays underspecified.
    if hi <= 0 or (hi < 2 and hi <= lo):
        return ""
    return g


def refine_gender(agent, text: str) -> dict:
    """Set every entity's coref_gender from its OWN evidence: non-animate -> '';
    animate -> object-property gender, else own-pronoun majority. A merged PERSON
    canonical (`gender_authoritative`) keeps the gender the cluster decided (the
    full-name-anchored gender — this is what protects Pierre's MALE and Curie's
    FEMALE). Returns a ledger of the changes for the report."""
    sub, native = _resolve(agent)
    changes = []
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if not isinstance(nm, str) or not nm:
            continue
        if at.get("merged_into"):                  # absorbed form — its canonical carries gender
            if at.get("coref_gender"):
                sub.set_attr(n, "coref_gender", "")
            continue
        if float(at.get("gender_authoritative", 0.0) or 0.0) == 1.0:
            continue                               # a merged person — keep the cluster gender
        old = at.get("coref_gender") or ""
        # ANIMACY GATE (whole-graph): a date/substance/institution is NOT animate and
        # carries NO gender. A merged/absorbed PERSON is already skipped above, so the
        # dictionary demotion here is safe to be CASE-INDEPENDENT — an institution the
        # reader knows only as a concrete inanimate ('university','poland','legion')
        # is demoted even when always capitalised, while a person name not in the
        # dictionary ('espci','bronisława') is never demoted.
        if float(at.get("coref_animate", 1.0) or 0.0) == 0.0:
            new = ""
        elif _wordnet_inanimate(nm):
            sub.set_attr(n, "coref_animate", 0.0)
            new = ""
        else:
            prop = gs.object_property_gender(nm)
            me, fe = _gender_evidence(sub, native, n)
            new = _pick_gender(agent, me, fe, prop)
        if new != old:
            sub.set_attr(n, "coref_gender", new)
            changes.append({"name": nm, "from": old, "to": new})
    return {"changes": changes}


def _wordnet_inanimate(name: str) -> bool:
    """The reader's dictionary types this single-token name ONLY as a concrete
    inanimate thing (substance/location/group/artifact/...), with NO person/animal
    sense -> not an animate referent. A name the dictionary does not know (a proper
    surname / acronym) returns False (never demoted). CASE-INDEPENDENT — a merged
    person is filtered out before this is called, so an institution that is always
    capitalised ('University','Poland') is still demoted."""
    toks = _name_tokens(name)
    if len(toks) != 1:
        return False
    try:
        from nltk.corpus import wordnet as wn
        syns = wn.synsets(toks[0], pos=wn.NOUN)
    except Exception:
        return False
    if not syns:
        return False
    lexes = {s.lexname() for s in syns}
    if "noun.person" in lexes or "noun.animal" in lexes:
        return False
    return bool(lexes & ce._INANIMATE_LEXNAMES)


def refine_reading(agent, text: str) -> dict:
    """The whole post-read refinement: merge name variants, then make gender
    per-entity precise. Returns both ledgers. Idempotent."""
    merge = merge_name_variants(agent, text)
    gender = refine_gender(agent, text)
    return {"merge": merge, "gender": gender}


__all__ = ["merge_name_variants", "refine_gender", "refine_reading"]
