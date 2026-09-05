"""Relation grounding — DERIVE typed relational edges (telic / constitutive /
agentive) between EXISTING held concepts from their own definition + why prose,
with an ANTI-HALLUCINATION GATE.

WHY THIS EXISTS
---------------
`domains/analogy_search.concept_signature` reads a Concept's outgoing edges and
types each via the seeded DimensionEdgeRole map (seeds/qualia_space.json):

    used_for/enables/serves/regulates/gates/controls/produces/grounds/exhibits
                                                              -> lexical:telic
    has_part/part_of/made_of/composed_of/constitutes/contains/member_of
                                                              -> lexical:constitutive
    causes/caused_by/creates/created_by/depends_on/derived_from/…
                                                              -> lexical:agentive

Domain concepts (computer_architecture, …) hold NO such edges, so those three
relational qualia axes are DARK. Their meaning is written in prose the author
already supplied (`definition`, `why`) — "a cache … bridging the CPU-memory
speed gap", "register renaming … removes false dependencies", "OoO instructions
execute as soon as their inputs are ready". This pass reads that prose, finds a
relation CUE, extracts the object phrase, and — the hard part — RESOLVES that
phrase to a REAL HELD Concept. It emits the typed edge ONLY if the object grounds
to a held Concept node.

THE GATE (what makes this faithful, not Pattern-A fabrication)
--------------------------------------------------------------
The prior general extractor (relation_extractor.extract) grounds its arguments to
the NEAREST RAW TOKEN ("CPUs constitutes wide") — an invented target. Wiring that
FABRICATES structure. Here the object phrase must resolve, through a graded
resolver (exact -> normalised/underscore/lower -> stemmed -> head-noun of the
phrase -> alias), to a name that is ALREADY a held Concept. If it does not
ground, the candidate is DROPPED — no edge, no invented node. A HIGH drop rate
is EXPECTED and GOOD: it is the gate refusing to hallucinate. Copula 'is/are'
=> genus => routed to `genls` (the FORMAL role), NEVER to `constitutes`.

The predicate->edge_type map below is a strict SUBSET of the seeded
DimensionEdgeRole edge types, so every emitted edge lands on telic / constitutive
/ agentive (or formal for the copula). Idempotent, mt-scopable. Mirrors the shape
of grounded_representation.ground_categories (read held data -> mint nothing new
except via the resolver -> wire a typed edge idempotently -> return counts).

THE OTHER HALF — mint_referents_from_relations (section 6)
----------------------------------------------------------
ground_relations DROPS an object phrase whose referent is genuinely NOT a held
Concept — even when it is a real, nameable thing the corpus talks about ('a cache
requires periodic REFRESH', 'IOMMU used for VM PASSTHROUGH'). If those referents
WERE held, the relation would ground and the relational qualia axes would light
up. `mint_referents_from_relations` closes that gap the FAITHFUL way (exactly as
grounded_representation.ground_categories mints category:<value> hubs and wires
genls to them): it runs ground_relations, collects the DROPPED objects, and for
each phrase that passes a REAL-REFERENT test — a short noun phrase (1-3 content
words, head is a NOUN per the agent's own Wiktionary POS faculty, not a
clause/verb/stopword/adjective genus, not already held) — MINTS the referent as
a real Concept (minted_referent + a definition) and wires the SAME relation cue
to it. The target is now HELD, so ground_relations' gate is satisfied HONESTLY,
not bypassed. It does NOT loosen that gate; it makes a previously-ungroundable
object groundable by holding it. A HIGH refusal rate is EXPECTED and GOOD — the
mint gate refusing to fabricate garbage clause-fragment 'concepts'.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from domains.grounded_representation import _concept_by_name, _find_microtheory
from domains import construction_grammar as cg


# ---------------------------------------------------------------------------
# 1. THE CUE LEXICON — surface phrase -> edge_type. edge_type is drawn ONLY from
#    the seeded DimensionEdgeRole vocabulary so it lands on a real lexical role.
#    Ordered longest-first at match time so 'part of' wins over 'of' etc.
#    Reuses relation_extractor's sound cues where they exist (used to/for,
#    part of, made of, causes, enables, depends on, requires, regulates,
#    controls, produces) and extends only within the seeded edge vocabulary.
# ---------------------------------------------------------------------------

# predicate CUE (a surface connective) -> (edge_type, lexical_role). Every
# edge_type here is a key in the seeded DimensionEdgeRole map.
_CUE_EDGE: list[tuple[str, str, str]] = [
    # ---- TELIC (what it is FOR / its function) -------------------------
    ("used for",        "used_for",   "telic"),
    ("used to",         "used_for",   "telic"),
    ("used as",         "used_for",   "telic"),
    ("enables",         "enables",    "telic"),
    ("enable",          "enables",    "telic"),
    ("allows",          "enables",    "telic"),
    ("allow",           "enables",    "telic"),
    ("lets",            "enables",    "telic"),
    ("serves",          "serves",     "telic"),
    ("serves as",       "serves",     "telic"),
    ("regulates",       "regulates",  "telic"),
    ("regulate",        "regulates",  "telic"),
    ("controls",        "controls",   "telic"),
    ("control",         "controls",   "telic"),
    ("gates",           "gates",      "telic"),
    ("produces",        "produces",   "telic"),
    ("produce",         "produces",   "telic"),
    ("generates",       "produces",   "telic"),
    ("generate",        "produces",   "telic"),
    # ---- CONSTITUTIVE (what it is MADE OF / its parts) -----------------
    ("consists of",     "has_part",   "constitutive"),
    ("consist of",      "has_part",   "constitutive"),
    ("composed of",     "composed_of","constitutive"),
    ("comprises",       "has_part",   "constitutive"),
    ("comprise",        "has_part",   "constitutive"),
    ("made of",         "made_of",    "constitutive"),
    ("made up of",      "made_of",    "constitutive"),
    ("part of",         "part_of",    "constitutive"),
    ("member of",       "member_of",  "constitutive"),
    ("contains",        "contains",   "constitutive"),
    ("contain",         "contains",   "constitutive"),
    ("has part",        "has_part",   "constitutive"),
    # ---- AGENTIVE (how it COMES ABOUT / its cause) ---------------------
    ("caused by",       "caused_by",  "agentive"),
    ("causes",          "causes",     "agentive"),
    ("cause",           "causes",     "agentive"),
    ("leads to",        "causes",     "agentive"),
    ("lead to",         "causes",     "agentive"),
    ("creates",         "creates",    "agentive"),
    ("create",          "creates",    "agentive"),
    ("created by",      "created_by", "agentive"),
    ("derived from",    "derived_from","agentive"),
    ("depends on",      "depends_on", "agentive"),
    ("depend on",       "depends_on", "agentive"),
    ("requires",        "depends_on", "agentive"),
    ("require",         "depends_on", "agentive"),
]

# The set of edge types this pass may emit (used to open productions +
# to sanity-check against the seeded DimensionEdgeRole map).
RELATION_EDGE_TYPES = tuple(sorted({et for _, et, _ in _CUE_EDGE}))

# Determiners / light words to strip from the FRONT of an object phrase before
# resolution (the head noun is what must ground). Not a stopword filter over the
# whole phrase — only leading light words, so multi-word held names survive.
_LEADING_LIGHT = {
    "the", "a", "an", "this", "that", "these", "those", "its", "their", "his",
    "her", "our", "your", "some", "any", "each", "every", "all", "both",
    "one", "another", "other", "such", "same", "more", "most", "many", "few",
    "to", "of", "for",
}

# A phrase that is ONLY a pronoun / light word grounds to nothing — never a target.
_PRONOUNS = {
    "it", "this", "that", "these", "those", "they", "them", "one", "something",
    "anything", "he", "she", "i", "you", "we", "us", "which", "who", "what",
    "there", "here",
}

# Common VERBS whose presence marks an object span as a CLAUSE (a verb phrase),
# not a noun phrase naming a concept. When a head-noun fallback would otherwise
# fire on such a span ('programs USE more virtual memory'), we refuse — the span
# describes an action, and its trailing noun only ACCIDENTALLY matches a held
# compound's tail. Refusing is the honest drop over a fabricated target.
_CLAUSE_VERBS = {
    "use", "uses", "used", "execute", "executes", "run", "runs", "make", "makes",
    "let", "lets", "be", "is", "are", "have", "has", "do", "does", "go", "goes",
    "get", "gets", "take", "takes", "give", "gives", "keep", "keeps", "need",
    "needs", "want", "wants", "see", "sees", "know", "knows", "handle", "handles",
    "improve", "improves", "reduce", "reduces", "extract", "extracts", "fetch",
    "fetches", "decode", "decodes", "share", "shares", "hide", "hides",
}

# Where an object phrase ENDS: a clause/relation boundary. The object is the
# noun phrase from just after the cue up to the first boundary token.
_OBJECT_BOUNDARY = re.compile(
    r"\b(?:that|which|who|when|where|while|because|since|so|but|and|or|if|"
    r"before|after|via|through|without|with|into|onto|than|then|as|for|"
    r"by|from|at|in|on|of)\b|[,.;:()]"
)


def _tok(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+", text or "")


def _stem(w: str) -> str:
    """Light morphological stem (mirrors relation_extractor._norm's suffix
    stripping) so 'registers' -> 'register', 'caches' -> 'cache'."""
    w = w.lower().strip("-_'\".,;:()")
    for suf in ("ing", "ses", "es", "ed", "s"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            return w[: -len(suf)]
    return w


# ---------------------------------------------------------------------------
# 2. THE RESOLVER — the anti-hallucination gate. Resolve an object phrase to a
#    HELD Concept name, or return None (=> the candidate is dropped).
# ---------------------------------------------------------------------------

def _acronym_of_expansion(words: list[str]) -> Optional[str]:
    """The initialism of a multi-word expansion: first letter of each CONTENT
    word (light words like 'of'/'the' skipped), lowercased. 'memory management
    unit' -> 'mmu', 'translation lookaside buffer' -> 'tlb'. None for a single
    word (an acronym is by definition multi-word). A pure surface read — it
    NAMES an alias of an already-held expansion, mints nothing."""
    content = [w for w in words if w and w not in _LEADING_LIGHT]
    if len(content) < 2:
        return None
    return "".join(w[0] for w in content).lower()


def _build_resolver_index(index: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Build THREE lookups off the held-name index:
      · exact_map — normalised full-name keys (lower / underscore<->space /
        word-by-word stem). A hit here NAMES the concept outright.
      · head_map  — head-noun keys ('L1_cache' -> 'cache'), kept SEPARATE and
        only consulted in the deliberate head-noun fallback. A head noun shared
        by 2+ distinct held compounds ('execution' -> out_of_order / speculative
        / SIMT_GPU_execution) is genuinely ambiguous: resolving it to any one
        would FABRICATE a target the prose did not name, so an ambiguous head is
        DROPPED from head_map entirely.
      · acro_map  — bidirectional acronym<->expansion keys. A held ACRONYM
        compound ('MMU_memory_management_unit', or a bare 'MMU') gets an
        expansion key ('memory management unit'); a held multi-word EXPANSION
        ('memory_management_unit') gets its initialism key ('mmu'). Both name
        the SAME held concept, so resolving either surface to it is faithful —
        no node minted. Ambiguity-guarded exactly like head_map: an acronym /
        expansion key claimed by 2+ distinct held concepts is DROPPED.

    Keeping the maps separate is load-bearing: it stops a bare adjective genus
    ('shared') stem-matching a compound's head key ('share' -> false_sharing) via
    the whole-phrase path, and stops an acronym alias from leaking into the
    whole-phrase path. Only names that ARE held produce keys — nothing invented.
    Full keys keep first-writer-wins (shortest held name)."""
    exact_map: dict[str, str] = {}
    head_map: dict[str, str] = {}
    head_claims: dict[str, set] = {}
    acro_claims: dict[str, set] = {}

    def _register(key: str, canon: str):
        k = key.strip().lower()
        if not k:
            return
        if k not in exact_map:
            exact_map[k] = canon

    def _claim_acro(key: str, canon: str):
        k = (key or "").strip().lower()
        if k:
            acro_claims.setdefault(k, set()).add(canon)

    for name in sorted(index.keys(), key=len):
        if not isinstance(name, str) or not name:
            continue
        canon = name
        low = name.lower()
        spaced = low.replace("_", " ")
        underscored = low.replace(" ", "_")
        _register(low, canon)
        _register(spaced, canon)
        _register(underscored, canon)
        _register(" ".join(_stem(w) for w in spaced.split()), canon)
        words = spaced.split()
        if len(words) > 1:
            for hk in {words[-1], _stem(words[-1])}:
                head_claims.setdefault(hk, set()).add(canon)
            # ACRONYM<->EXPANSION aliases (both name THIS held concept):
            # · a held ACRONYM COMPOUND — a short all-caps leading token (raw
            #   name, e.g. 'MMU_memory_management_unit', 'SVE_scalable_vector_
            #   extension') — the REST is the expansion. Claim the expansion
            #   surface (+ its stem) as an alias, but ONLY when the expansion is
            #   genuinely MULTI-WORD: a single-word tail ('ECC_memory' -> 'memory',
            #   'DRAM_row' -> 'row') is just a common head noun, already handled
            #   (ambiguity-guarded) by head_map; aliasing it here would let a bare
            #   'memory' resolve to 'ECC_memory' — a fabrication. Multi-word only.
            raw = re.findall(r"[A-Za-z0-9]+", name)
            is_acro_compound = (len(raw) >= 2 and raw[0].isupper()
                                and raw[0].isalpha() and 2 <= len(raw[0]) <= 6)
            if is_acro_compound and len(raw) >= 3:
                expansion = raw[1:]
                exp_spaced = " ".join(w.lower() for w in expansion)
                _claim_acro(exp_spaced, canon)
                _claim_acro(" ".join(_stem(w) for w in exp_spaced.split()), canon)
            elif not is_acro_compound:
                # · a held plain EXPANSION ('memory_management_unit') — claim its
                #   INITIALISM ('mmu') as an alias. Only for a genuine multi-word
                #   expansion whose leading token is NOT itself an acronym head,
                #   and only an initialism of length >= 3 (a 2-letter initialism
                #   like 'fs' for 'false_sharing' collides too easily to be a
                #   safe unguarded alias).
                acr = _acronym_of_expansion(words)
                if acr and len(acr) >= 3:
                    _claim_acro(acr, canon)

    # head-noun key kept ONLY when a SINGLE held compound claims it AND it is not
    # already an exact full-name key (an exact name wins). Ambiguous heads dropped.
    for hk, claimants in head_claims.items():
        if hk in exact_map or hk in head_map:
            continue
        if len(claimants) == 1:
            head_map[hk] = next(iter(claimants))

    # acronym/expansion alias kept ONLY when a SINGLE held concept claims it and
    # it is not already an exact full-name key (a real name always wins). An
    # alias claimed by 2+ held concepts is genuinely ambiguous -> DROPPED, same
    # anti-fabrication discipline as the head map.
    acro_map: dict[str, str] = {}
    for ak, claimants in acro_claims.items():
        if ak in exact_map:
            continue
        if len(claimants) == 1:
            acro_map[ak] = next(iter(claimants))
    return exact_map, head_map, acro_map


def resolve_object(phrase: str, keymap, head_map: Optional[dict] = None, *,
                   acro_map: Optional[dict] = None,
                   head_noun: bool = True) -> Optional[str]:
    """Resolve an object PHRASE to a held Concept name via a graded ladder:
      1. exact normalised (lower / underscore / spaced) — from `keymap`,
      2. stemmed whole phrase — from `keymap`,
      3. acronym<->expansion alias for the WHOLE phrase — from `acro_map` (a
         held acronym compound's expansion surface, or a held expansion's
         initialism); each alias names exactly one held concept (ambiguous
         aliases were dropped when the map was built), so this is faithful,
      4. (only when `head_noun` and `head_map` given) head-noun fallback for a
         SHORT non-clause noun phrase — from `head_map` (kept separate so a bare
         adjective genus never reaches a head key via the whole-phrase path).
    Returns the canonical held name, or None (=> DROP: no held concept, no
    invented target). This IS the anti-hallucination gate.

    `head_noun=False` (COPULA GENUS): a genus names an is-a parent DIRECTLY, so
    only exact / stemmed WHOLE-phrase matches (and, faithfully, a whole-phrase
    acronym alias) are accepted — a bare adjective ('shared') must NOT resolve to
    a compound whose tail it matches ('false_sharing'). That leap is exactly the
    fabrication the gate refuses.

    Back-compat: `keymap` may be the combined dict (older callers); when
    `head_map` / `acro_map` is None the corresponding step is skipped."""
    if not phrase:
        return None
    words = [w for w in _tok(phrase)]
    if not words:
        return None
    low = [w.lower() for w in words]
    if all(w in _PRONOUNS or w in _LEADING_LIGHT for w in low):
        return None

    def _try(seq: list[str]) -> Optional[str]:
        if not seq:
            return None
        joined = " ".join(seq)
        for key in (joined, joined.replace(" ", "_"),
                    " ".join(_stem(w) for w in seq)):
            hit = keymap.get(key)
            if hit is not None:
                return hit
        return None

    def _try_acro(seq: list[str]) -> Optional[str]:
        """Whole-phrase acronym<->expansion alias. Consults acro_map with the
        phrase's spaced + stemmed forms (a held acronym compound's expansion),
        and — for a single-token phrase — the bare acronym itself (a held
        expansion's initialism). Only unambiguous aliases live in acro_map."""
        if not acro_map or not seq:
            return None
        joined = " ".join(seq)
        for key in (joined, " ".join(_stem(w) for w in seq)):
            hit = acro_map.get(key)
            if hit is not None:
                return hit
        if len(seq) == 1:
            hit = acro_map.get(seq[0])
            if hit is not None:
                return hit
        return None

    # 1+2: whole phrase (exact / stemmed). Safe at any length — names outright.
    hit = _try(low)
    if hit is not None:
        return hit
    # 3: whole-phrase acronym<->expansion alias (faithful: same held concept).
    hit = _try_acro(low)
    if hit is not None:
        return hit
    core = list(low)
    while core and core[0] in _LEADING_LIGHT:
        core = core[1:]
    if not core:
        return None
    hit = _try(core)
    if hit is not None:
        return hit
    hit = _try_acro(core)
    if hit is not None:
        return hit
    if not head_noun:
        # GENUS mode (head_noun=False): a genus is a HEAD-INITIAL noun phrase
        # ('a memory holding recently-used data' -> head 'memory'), so the parent
        # concept is its LEADING content noun. Resolve that leading head against
        # the EXACT name map only — never the head_map — so a trailing-adjective
        # genus ('shared') cannot leap to a compound whose tail it matches
        # ('false_sharing'). A leading head that is itself an adjective / verb /
        # light word does not name a concept and drops.
        lead = None
        for w in core:
            if w in _LEADING_LIGHT or w in _PRONOUNS:
                continue
            lead = w
            break
        if lead is None or lead in _CLAUSE_VERBS:
            return None
        for key in (lead, _stem(lead)):
            hit = keymap.get(key)
            if hit is not None:
                return hit
        return None
    if head_map is None:
        return None
    # HEAD-NOUN fallback — ONLY for a SHORT noun phrase (<= 3 content words) that
    # is not a clause. A long span ('programs use more virtual memory than physical
    # RAM') is a CLAUSE, not a name; matching its trailing head to a held compound
    # (memory -> ECC_memory) would FABRICATE a target. A phrase containing a VERB
    # cue is likewise a clause, not a noun phrase — reject.
    content = [w for w in core if w not in _LEADING_LIGHT and w not in _PRONOUNS]
    if len(content) > 3 or any(w in _CLAUSE_VERBS for w in content):
        return None
    head = core[-1]
    if head in _PRONOUNS or head in _LEADING_LIGHT:
        return None
    for key in (head, _stem(head)):
        hit = head_map.get(key)
        if hit is not None:
            return hit
    return None


# ---------------------------------------------------------------------------
# 3. CUE PARSE — find relation cues in prose and extract the object phrase.
# ---------------------------------------------------------------------------

def _find_cues(text: str) -> list[tuple[int, int, str, str, str]]:
    """Find every relation cue in `text`. Returns a list of
    (start_char, end_char, edge_type, role, cue_surface), longest-cue-first at
    each position so 'part of' beats 'of'-like fragments. Case-insensitive,
    word-boundary matched."""
    low = text.lower()
    hits: list[tuple[int, int, str, str, str]] = []
    # sort cues longest-first so a multi-word cue is preferred.
    for cue, et, role in sorted(_CUE_EDGE, key=lambda c: -len(c[0])):
        pat = re.compile(r"\b" + re.escape(cue) + r"\b")
        for m in pat.finditer(low):
            hits.append((m.start(), m.end(), et, role, cue))
    # keep non-overlapping, preferring earlier + longer cues.
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    kept: list[tuple[int, int, str, str, str]] = []
    last_end = -1
    for h in hits:
        if h[0] >= last_end:
            kept.append(h)
            last_end = h[1]
    return kept


def _object_after(text: str, end: int) -> str:
    """The object phrase = the span from just after the cue up to the first
    clause/relation boundary (a comma, another relation word, a subordinator)."""
    rest = text[end:]
    m = _OBJECT_BOUNDARY.search(rest)
    span = rest[: m.start()] if m else rest
    return span.strip()


def extract_relation_candidates(text: str) -> list[tuple[str, str, str]]:
    """Parse prose into (edge_type, role, object_phrase) candidates — BEFORE
    grounding. The object phrase is raw surface (grounding happens later). This
    is the honest parse: it does not yet know if the object is a held concept."""
    out: list[tuple[str, str, str]] = []
    for (_s, e, et, role, _cue) in _find_cues(text):
        obj = _object_after(text, e)
        if obj:
            out.append((et, role, obj))
    return out


# ---------------------------------------------------------------------------
# 4. PRODUCTIONS — admit the Concept -<rel>-> Concept edges this pass emits.
# ---------------------------------------------------------------------------

def open_relation_productions(substrate) -> int:
    """Open Γ productions admitting Concept -<rel>-> Concept for every relation
    edge type this pass emits (used_for, has_part, causes, …) plus genls (the
    copula-genus route). Idempotent; returns the number submitted."""
    n = 0
    for et in RELATION_EDGE_TYPES + ("genls",):
        try:
            substrate.add_production({
                "src": {"type": "Concept", "var": "a"},
                "edge_type": et,
                "tgt": {"type": "Concept", "var": "b"},
                "where": None,
                "provenance": "relation_grounding:relation",
            })
            n += 1
        except Exception:
            pass
    return n


def _has_edge(substrate, src, et, tgt) -> bool:
    try:
        return tgt in set(substrate.neighbours(src, et))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 5. THE PASS — ground_relations.
# ---------------------------------------------------------------------------

def ground_relations(substrate, mt_name: Optional[str] = None, *,
                     index: Optional[dict] = None,
                     prose_attrs: Iterable[str] = ("definition", "why"),
                     ) -> dict:
    """DERIVE typed relational edges between held concepts from their own prose.

    For each Concept (optionally restricted to Microtheory `mt_name`):
      · read its `definition` + `why` prose,
      · route the genus (copula 'is/are' via construction_grammar) to a `genls`
        edge when the genus grounds to a held Concept — NEVER to `constitutes`,
      · find relation cues (used for / part of / causes / …), extract each
        object phrase, and RESOLVE it to a held Concept,
      · emit the typed edge (used_for/has_part/causes/…) ONLY when the object
        grounds; otherwise DROP it (the anti-hallucination gate).

    Idempotent (an edge already present is not re-added). mt-scopable. Emits no
    new nodes — a candidate whose object does not resolve to a HELD concept is
    dropped, never invented.

    Returns {edges_added, emitted:[(src_name, edge_type, tgt_name)],
             dropped:[(src_name, edge_type, object_phrase)],
             telic, constitutive, agentive, formal,
             candidates, grounded, drop_rate, mt}."""
    if index is None:
        index = _concept_by_name(substrate)
    keymap, head_map, acro_map = _build_resolver_index(index)
    try:
        open_relation_productions(substrate)
    except Exception:
        pass

    # the concept set: one Mt's concepts, or all.
    concept_ids: list = []
    if mt_name is not None:
        mt = _find_microtheory(substrate, mt_name)
        if mt is None:
            return {"edges_added": 0, "emitted": [], "dropped": [],
                    "telic": 0, "constitutive": 0, "agentive": 0, "formal": 0,
                    "candidates": 0, "grounded": 0, "drop_rate": 0.0,
                    "mt": mt_name}
        try:
            concept_ids = list(substrate.neighbours(mt, "has_concept"))
        except Exception:
            concept_ids = []
    else:
        try:
            concept_ids = list(substrate.nodes("Concept"))
        except Exception:
            concept_ids = []

    role_count = {"telic": 0, "constitutive": 0, "agentive": 0, "formal": 0}
    emitted: list[tuple[str, str, str]] = []
    dropped: list[tuple[str, str, str]] = []
    edges_added = 0
    candidates = 0

    for cid in concept_ids:
        try:
            a = substrate.node(cid)["attrs"]
        except Exception:
            continue
        src_name = a.get("name")
        if not isinstance(src_name, str) or not src_name:
            continue
        prose = " ".join(str(a.get(k)) for k in prose_attrs
                         if isinstance(a.get(k), str) and a.get(k))
        if not prose.strip():
            continue

        # --- COPULA -> GENUS -> genls (formal), never constitutes. ---------
        # Read the first definitional sentence's genus; if it grounds to a held
        # concept (and is not the concept itself), wire a genls edge.
        try:
            defn = a.get("definition")
            if isinstance(defn, str) and defn:
                parsed = cg.extract_definition(defn, substrate=substrate,
                                               term=src_name)
                genus = (parsed or {}).get("genus")
                if genus:
                    candidates += 1
                    g = resolve_object(genus, keymap, head_map,
                                       acro_map=acro_map, head_noun=False)
                    if g and g != src_name:
                        tgt = index.get(g)
                        if tgt is not None and tgt != cid:
                            if not _has_edge(substrate, cid, "genls", tgt):
                                try:
                                    substrate.add_edge(cid, "genls", tgt, {})
                                    edges_added += 1
                                except Exception:
                                    pass
                            emitted.append((src_name, "genls", g))
                            role_count["formal"] += 1
                        else:
                            dropped.append((src_name, "genls", genus))
                    else:
                        dropped.append((src_name, "genls", genus))
        except Exception:
            pass

        # --- RELATION CUES -> telic / constitutive / agentive edges --------
        for (et, role, obj) in extract_relation_candidates(prose):
            candidates += 1
            g = resolve_object(obj, keymap, head_map, acro_map=acro_map)
            if not g or g == src_name:
                # DROP: no held concept resolved (or self-loop). No invented node.
                dropped.append((src_name, et, obj))
                continue
            tgt = index.get(g)
            if tgt is None or tgt == cid:
                dropped.append((src_name, et, obj))
                continue
            if not _has_edge(substrate, cid, et, tgt):
                try:
                    substrate.add_edge(cid, et, tgt, {})
                    edges_added += 1
                except Exception:
                    # if the edge is rejected, treat as dropped (no fabrication).
                    dropped.append((src_name, et, obj))
                    continue
            emitted.append((src_name, et, g))
            role_count[role] += 1

    grounded = len(emitted)
    drop_rate = (len(dropped) / candidates) if candidates else 0.0
    return {"edges_added": edges_added, "emitted": emitted, "dropped": dropped,
            "telic": role_count["telic"], "constitutive": role_count["constitutive"],
            "agentive": role_count["agentive"], "formal": role_count["formal"],
            "candidates": candidates, "grounded": grounded,
            "drop_rate": drop_rate, "mt": mt_name}


# ---------------------------------------------------------------------------
# 6. THE MINT PASS — the OTHER half of the sparse-relational-witness problem.
#
# ground_relations DROPS an object phrase whose referent is genuinely NOT a held
# Concept — even when it is a real, nameable thing the corpus talks about ('a
# cache requires periodic REFRESH', 'IOMMU used for VM PASSTHROUGH'). If those
# referents WERE held, the relation would ground and the relational qualia axes
# would light up. The faithful move (mirroring grounded_representation.
# ground_categories, which mints category:<value> hub Concepts and wires genls to
# them): MINT the missing referent as a real Concept when it passes a REAL-
# REFERENT test, then let the SAME relation cue wire the edge to it — so the
# target IS held and ground_relations' gate is satisfied HONESTLY, not bypassed.
#
# The danger is minting garbage/clause-fragment 'concepts' that pollute the
# graph. So we mint ONLY a phrase that passes `_referent_candidate`: a short noun
# phrase (1-3 content words) whose HEAD is a NOUN (per the agent's own POS
# faculty, wiktionary_reference.wiktionary_pos — the SAME oracle
# construction_grammar._pos_token consults), whose non-head content words are
# nominal MODIFIERS (adj/noun), that is NOT a clause/verb-led span, NOT a bare
# stopword/pronoun, and does NOT already resolve to a held concept. A HIGH refusal
# rate is EXPECTED and GOOD — it is the mint gate refusing to fabricate.
#
# This ADDS a pass; it does NOT loosen ground_relations' gate. ground_relations
# still only wires to HELD concepts — we simply make a previously-ungroundable
# object HELD first (when it is a genuine referent), so the edge then grounds.
# ---------------------------------------------------------------------------

# The relation edge types whose dropped objects we may mint a referent for. The
# copula-genus route (genls) is DELIBERATELY excluded: a genus is an is-a parent,
# and the genls drops are overwhelmingly bare adjectives / clause fragments
# ('complex', 'standard', 'not', 'shared', 'dirty modified relative') — minting
# an is-a parent from those would inject a FALSE taxonomy. We mint referents only
# for the telic/constitutive/agentive relation cues, where the object is a THING
# the source relates to (what it is FOR / made OF / caused BY).
_MINTABLE_EDGE_TYPES = frozenset(RELATION_EDGE_TYPES)

# POS tags (from the agent's Wiktionary POS faculty) that a MODIFIER content word
# may carry: a nominal pre-modifier is an adjective ('periodic refresh',
# 'accurate prediction') or a noun ('matrix tile blocking', 'register names').
_MODIFIER_POS = {"adj", "noun", "name"}

# Adjective/adverb/number-ish surfaces that are NOT real referents on their own
# even though Wiktionary may list a rare noun sense. A single such word as the
# whole phrase is a genus/quality fragment, not a thing — refuse. (Kept small;
# the primary gate is the POS oracle + the noun-head requirement.)
_NON_REFERENT_HEADS = {
    "not", "same", "common", "wide", "complex", "standard", "present",
    "sparse", "concurrent", "independent", "clean", "dirty", "sign",
}


def _wiktionary_pos(word: str) -> list:
    """The agent's OWN POS faculty (Wiktionary, dominant sense first) — the SAME
    oracle construction_grammar._pos_token consults. Returns a POS list (possibly
    empty). Isolated here so the mint gate reuses the held faculty, inventing no
    parallel tagger."""
    try:
        from domains import wiktionary_reference as _wikt
        return _wikt.wiktionary_pos(word.lower(), "en") or []
    except Exception:
        return []


def _normalise_referent_name(core: list[str]) -> str:
    """The minted referent's NAME: the content words joined by underscores,
    lowercased. A surface->name convention (mirrors ground_categories'
    'category:<value>'), not a meaning decision — the phrase IS the name."""
    return "_".join(w.lower() for w in core)


# ---------------------------------------------------------------------------
# 6a. THE MINT GATE POLICY NODE — the strictness of the anti-hallucination mint
# gate, made a GRAPH-RESIDENT, inspectable, tuneable knob instead of Python
# constants. Mirrors stopping_policy.SufficiencyPolicy / issue_reopen.ReopenPolicy
# (a singleton policy node, minted-if-absent with safe defaults, a mechanical
# reader + writer, no decision in the boundary I/O) and auto_approve's
# off-by-default discipline (the DEFAULT node reproduces TODAY's behaviour
# EXACTLY, so a fresh graph behaves identically to now unless the agent tunes it).
#
# WHY INDIVIDUAL KNOBS, NOT A SINGLE `strictness` PRESET ENUM (design choice).
# The three knobs are genuinely ORTHOGONAL decision points already present in
# _referent_candidate: min_recurrence gates on corpus frequency, max_content_words
# gates on phrase length, require_noun_dominant_head gates on the head's POS
# dominance. A single preset enum would either HIDE the individual dials (the task
# requires each be individually inspectable/settable) or DUPLICATE state (preset +
# per-knob overrides), creating a "which wins" consistency problem the moment a
# caller sets both. Exposing the three knobs directly — the exact shape
# auto_approve.DEFAULTS uses — keeps each dial inspectable and settable with no
# hidden coupling. The main strictness dial is require_noun_dominant_head (the
# bright-line noun-dominance rule); the other two are secondary tuning.
#
# EACH KNOB MAPS TO A REAL DECISION POINT in _referent_candidate (no invented
# knob maps to nothing):
#   · min_recurrence            -> the RECURRENCE gate (appear >= N times).
#   · max_content_words         -> the SHORT-noun-phrase cut ('> N => reject').
#   · require_noun_dominant_head-> the BRIGHT-LINE noun-DOMINANCE rule
#       (head_pos[0] must be noun/name). When False (permissive) it relaxes to
#       'noun in head_pos' — accept a head that merely HAS a noun sense even if a
#       verb sense is dominant, recovering genuine-but-verb-dominant referents
#       ('periodic refresh', 'matrix tile blocking') at the cost of some clause
#       risk. THIS is the main precision<->recall dial.
# ---------------------------------------------------------------------------

MINT_POLICY_NODE_TYPE = "MintPolicy"

# The SAFE DEFAULT INVARIANT: these values reproduce TODAY's hard-coded gate
# EXACTLY (min_recurrence=1, max_content_words=3, require_noun_dominant_head=True).
# A freshly-minted MintPolicy therefore changes nothing until the agent tunes it.
MINT_POLICY_DEFAULTS: dict[str, Any] = {
    "min_recurrence": 1,
    "max_content_words": 3,
    "require_noun_dominant_head": True,
}

# fields a caller (the agent / web route) may set directly on the policy node.
MINT_GATE_SETTABLE_FIELDS = tuple(MINT_POLICY_DEFAULTS.keys())

# The provenance sentinel that records WHICH knobs a caller has EXPLICITLY pinned
# via set_mint_gate. Precedence (see mint_gate_params + _disposition_derived_gate
# below): safe-defaults < disposition-derived-defaults < EXPLICIT PIN. A pinned
# knob is one the agent chose deliberately, so it always wins over the
# temperament-derived default — a caller can still nail a dial down and the
# self-regulating disposition will not silently move it. An UNPINNED knob (a
# freshly-minted default placeholder, or an untouched field) follows the agent's
# standing disposition when a disposition exists. Kept as a graph-resident list
# attr on the MintPolicy node (mechanical provenance, no decision).
MINT_GATE_PINNED_ATTR = "pinned_fields"


# ---------------------------------------------------------------------------
# 6b. THE MINT GATE <- DISPOSITION DERIVATION (blend layer 2).
#
# The mint gate's strictness is no longer only a static config node. When the
# agent carries a standing dynamical DISPOSITION (domains/disposition.py — a
# CAN-relaxable qualia axis, conservative <-> permissive), the gate READS that
# temperament and DERIVES its effective strictness from it, so the gate is a
# TEMPERAMENT that responds to state, not just a knob. An EXPLICIT MintPolicy pin
# still wins (see precedence above) — the disposition only supplies the DEFAULT
# for a knob the agent has not deliberately nailed down.
#
# THE MAPPING — disposition_level (integer step in [-4,+4]) -> gate defaults.
# HONEST and MONOTONE: more permissive disposition => a looser gate; more
# conservative => today's strict defaults. The two dials the disposition moves
# are the two that _referent_candidate exposes as a precision<->recall trade:
#
#   · require_noun_dominant_head — the BRIGHT-LINE dial. Conservative (the
#     default True) demands the head's DOMINANT sense be a noun; permissive
#     (False) accepts a head that merely HAS a noun sense, recovering
#     genuine-but-verb-dominant referents ('periodic refresh'). It FLIPS to
#     False once the disposition is clearly permissive (level >= +1) — a
#     permissive temperament is willing to admit verb-dominant nominals.
#   · max_content_words — the phrase-length dial. Conservative keeps today's
#     cut of 3; a permissive temperament widens it (a longer noun phrase is
#     admitted), a conservative temperament (level <= -2) tightens it to 2.
#
# min_recurrence is left at the default (1) across the disposition range: it is
# a corpus-frequency gate, orthogonal to temperament, and moving it from
# disposition would conflate 'how open am I' with 'how often did I see it'.
#
# THE SAFE-DEFAULT INVARIANT (proved by decision-equivalence in the tests): the
# SEEDED-neutral/absent disposition maps to EXACTLY today's defaults. The seeded
# default disposition_level is -1 (DEFAULT_DISPOSITION_SEED = -1.0, mildly
# conservative), and level -1 (and 0, and any negative down to -1) maps to
# {min_recurrence:1, max_content_words:3, require_noun_dominant_head:True} —
# byte-identical to MINT_POLICY_DEFAULTS. An agent with no disposition at all
# reads the safe defaults directly (the derivation is skipped entirely). So a
# default agent, tuned or not, behaves EXACTLY like today.
# ---------------------------------------------------------------------------

def _disposition_derived_gate(agent) -> Optional[dict]:
    """Derive gate-param DEFAULTS from the agent's standing disposition_level, or
    return None when this graph has NO disposition (then the caller falls back to
    MINT_POLICY_DEFAULTS == today). A pure, monotone read of the produced,
    quantised standing trait — NO decision here beyond the documented mapping;
    the disposition_level itself was produced by CAN relaxation.

    Reads with ensure=False so a bare read NEVER mints a disposition Mt (the
    off-by-default discipline): a graph that has not built a disposition adds
    nothing and behaves like today.

    The mapping (see the block comment above) — MONOTONE in the level:
        level <= -2  : STRICT+   (max_content_words=2, noun-dominant head)
        level in {-1,0,1... up to 0}: TODAY's defaults exactly
        level == +1 or +2         : relax the bright-line head rule (permissive)
        level >= +2               : also widen max_content_words to 4
    Conservative (the seeded default -1) == today, EXACTLY."""
    try:
        import domains.disposition as _disp
    except Exception:
        return None
    sub = _sub(agent)
    if sub is None:
        return None
    # only derive when a disposition ACTUALLY EXISTS on this graph — never mint
    # one from a mint pass. A graph with no disposition Mt -> None -> today.
    try:
        ag = _disp._agent_node(agent)
        mt = _disp._find_disposition_mt(sub, ag)
        if mt is None or _disp._disposition_concept(sub, mt) is None:
            return None
    except Exception:
        return None
    try:
        level = _disp.disposition_level(agent, ensure=False)
    except Exception:
        return None

    out = dict(MINT_POLICY_DEFAULTS)  # start from today's conservative defaults
    # PERMISSIVE side — a temperament that is opening up loosens the gate.
    if level >= 1:
        out["require_noun_dominant_head"] = False   # accept verb-dominant nominals
    if level >= 2:
        out["max_content_words"] = 4                 # admit a longer noun phrase
    # CONSERVATIVE side — a temperament that has tightened past the default cuts
    # the gate harder than today (shorter phrases only). level -1/0 stay == today.
    if level <= -2:
        out["max_content_words"] = 2
    return out


def _sub(agent):
    """The substrate handle. Callers pass either a raw substrate (the mint pass's
    own `substrate` argument, as the tests do) or an agent wrapper carrying `.s`
    — accept both, mirroring auto_approve._sub / stopping_policy._resolve."""
    return getattr(agent, "s", agent)


def _mint_policy_node(agent, *, create: bool = True):
    """Return the singleton MintPolicy node, minting it (safe defaults) if absent
    and `create` is True, else None. Mechanical boundary I/O — mirrors
    stopping_policy._policy_node / auto_approve.ensure_policy_node. Never mints a
    second node once one exists (first-found wins)."""
    sub = _sub(agent)
    try:
        for n in sub.nodes(MINT_POLICY_NODE_TYPE):
            if not hasattr(sub, "has_node") or sub.has_node(n):
                return n
    except Exception:  # noqa: BLE001 -- type not present in this graph yet
        pass
    if not create:
        return None
    return sub.add_node(MINT_POLICY_NODE_TYPE, dict(MINT_POLICY_DEFAULTS))


def ensure_mint_policy(agent):
    """Idempotent: return the single MintPolicy node, minting it with SAFE
    DEFAULTS (which reproduce today's behaviour exactly) if this graph has none.
    Safe to call on every mint pass — never mints a second node once one exists.
    The off-by-default discipline of auto_approve.ensure_policy_node: a fresh
    graph gets a node whose defaults == today, so nothing changes until tuned."""
    return _mint_policy_node(agent, create=True)


def _pinned_fields(sub, pid) -> set:
    """The set of knobs a caller has EXPLICITLY pinned via set_mint_gate, read off
    the MintPolicy node's `pinned_fields` provenance attr. Empty when the node is
    absent or was only minted with placeholder defaults (never explicitly tuned).
    Mechanical read of provenance — no decision."""
    if pid is None:
        return set()
    try:
        raw = sub.node(pid)["attrs"].get(MINT_GATE_PINNED_ATTR)
    except Exception:
        return set()
    if not raw:
        return set()
    if isinstance(raw, str):
        return {p for p in raw.split(",") if p}
    try:
        return {str(p) for p in raw}
    except Exception:
        return set()


def mint_gate_params(agent, *, ensure: bool = True) -> dict:
    """Read the current EFFECTIVE mint-gate strictness params. Returns a plain
    dict {min_recurrence, max_content_words, require_noun_dominant_head} with
    types normalised (ints for the counts, bool for the flag).

    PRECEDENCE (blend layer 2) — three layers, low to high:
      1. SAFE DEFAULTS (MINT_POLICY_DEFAULTS) — today's conservative gate.
      2. DISPOSITION-DERIVED DEFAULTS — when the agent carries a standing
         disposition, `_disposition_derived_gate` maps its produced, quantised
         disposition_level to gate defaults (permissive temperament => looser
         gate). This layer supplies the DEFAULT for any knob the agent has not
         explicitly pinned, so absent a pin the gate FOLLOWS the temperament.
      3. EXPLICIT PINS — a knob the caller deliberately set via set_mint_gate
         (recorded in the node's `pinned_fields` provenance) ALWAYS wins. A
         pinned dial is never silently moved by the self-regulating disposition.

    The SAFE-DEFAULT INVARIANT holds by construction: a graph with NO disposition
    skips layer 2 entirely (reads layer 1 == today); a SEEDED-neutral/absent
    disposition (level -1) maps in layer 2 to EXACTLY MINT_POLICY_DEFAULTS. So a
    default agent behaves byte-identically to today (proved by decision-
    equivalence in tests/test_disposition_homeostasis.py).

    `ensure=True` (default) mints the MintPolicy node with safe defaults first if
    absent. `ensure=False` reads a MISSING node WITHOUT minting — the
    auto_approve.get_policy discipline (a fresh graph gains no node). The mint
    pass uses `ensure=False` so a default run adds NOTHING to the graph. Reading
    the disposition here is also non-minting (ensure=False), so a default run
    that has a disposition still adds no MintPolicy node. Mechanical read + the
    documented monotone mapping — NO decision beyond that."""
    sub = _sub(agent)
    if ensure:
        pid = ensure_mint_policy(agent)
    else:
        pid = _mint_policy_node(agent, create=False)
    attrs: dict[str, Any] = {}
    if pid is not None:
        try:
            attrs = dict(sub.node(pid)["attrs"])
        except Exception:  # noqa: BLE001
            attrs = {}

    # LAYER 1 -> LAYER 2: the base defaults are today's, unless the agent's
    # standing disposition derives a (monotone) looser/tighter default.
    base = _disposition_derived_gate(agent) or dict(MINT_POLICY_DEFAULTS)

    # LAYER 3: an EXPLICITLY pinned knob overrides the derived default. An
    # unpinned attr (a placeholder default the node was minted with) does NOT —
    # it defers to the disposition-derived default so the temperament is followed.
    pinned = _pinned_fields(sub, pid)

    out: dict[str, Any] = {}
    for k, safe_default in MINT_POLICY_DEFAULTS.items():
        default = base.get(k, safe_default)
        v = attrs.get(k, default) if k in pinned else default
        if k == "require_noun_dominant_head":
            out[k] = bool(default if v is None else v)
        else:
            try:
                out[k] = int(v)
            except Exception:
                out[k] = int(default)
    return out


def set_mint_gate(agent, **kwargs) -> dict:
    """Tune the mint-gate POLICY: mint-if-absent, then write the given knobs
    (min_recurrence / max_content_words / require_noun_dominant_head) onto the
    MintPolicy node (graph data). Unknown keys and None values are ignored (a
    caller passes only what it wants to change). Returns the resulting param dict.
    Mechanical boundary write — the strictness stance is graph-resident POLICY,
    tuned here, NOT a decision made in Python. Mirrors
    stopping_policy.set_sufficiency_threshold / auto_approve.set_policy.

    Each knob written here is recorded as an EXPLICIT PIN (in the node's
    `pinned_fields` provenance attr), so it wins over any disposition-derived
    default in mint_gate_params — the agent has deliberately nailed this dial, and
    the self-regulating disposition must NOT silently move it. Knobs the caller
    does not pass stay UNpinned and continue to follow the agent's temperament."""
    sub = _sub(agent)
    pid = ensure_mint_policy(agent)
    newly_pinned = set()
    for k, v in kwargs.items():
        if k not in MINT_GATE_SETTABLE_FIELDS or v is None:
            continue
        try:
            if k == "require_noun_dominant_head":
                sub.set_attr(pid, k, bool(v))
            else:
                sub.set_attr(pid, k, int(v))
            newly_pinned.add(k)
        except Exception:
            pass
    if newly_pinned:
        try:
            pinned = _pinned_fields(sub, pid) | newly_pinned
            # store as a comma-joined string (a scalar attr the substrate accepts
            # everywhere; _pinned_fields reads either a string or a list).
            sub.set_attr(pid, MINT_GATE_PINNED_ATTR,
                         ",".join(sorted(pinned)))
        except Exception:
            pass
    return mint_gate_params(agent)


def _referent_candidate(phrase: str, keymap, *, min_recurrence: int = 1,
                        max_content_words: int = 3,
                        require_noun_dominant_head: bool = True,
                        recurrence: Optional[dict] = None
                        ) -> Optional[tuple[str, list[str]]]:
    """THE REAL-REFERENT TEST. Decide whether a dropped object `phrase` names a
    genuine, mintable referent. Returns (normalised_name, core_words) when it
    passes, else None (=> REFUSE — the phrase is a clause fragment / verb /
    stopword / adjective genus, and minting it would pollute the graph).

    A phrase passes iff ALL hold:
      · after stripping leading light words it has 1..`max_content_words` content
        words (default 3 — the current cut; a longer span is a clause, not a name),
      · it contains NO clause verb (a verb cue marks a VERB PHRASE, not a name),
      · it is not all pronoun/light words,
      · its HEAD (last content word) has a NOUN sense in the agent's POS faculty
        AND — when `require_noun_dominant_head` (default True, TODAY's bright-line
        rule) — the head's DOMINANT sense is a noun/name; when False (permissive)
        the head need only HAVE a noun sense ('noun' in head_pos) even if a verb
        sense is dominant, recovering genuine-but-verb-dominant referents
        ('periodic refresh', 'matrix tile blocking') at the cost of some clause
        risk. For a single content word the known quality/adjective blocklist
        still refuses a lone adjective genus ('complex', 'not'),
      · every NON-head content word is a nominal modifier (adj/noun) — a verb-led
        span ('detect load-store violations') is a clause, refused,
      · it does NOT already resolve to a held Concept (that is ground_relations'
        job; we only mint the genuinely-UNHELD referent),
      · it recurs at least `min_recurrence` times across the corpus prose (the
        default 1 accepts a clean NP on first sight; a caller may require >=2 to
        demand recurrence). `recurrence` maps normalised-name -> count.

    The three gate knobs (`min_recurrence`, `max_content_words`,
    `require_noun_dominant_head`) are the tuneable strictness dials — normally
    read off the graph-resident MintPolicy node (see mint_gate_params) and threaded
    in by mint_referents_from_relations. The DEFAULTS here reproduce TODAY's
    hard-coded gate EXACTLY, so a caller that passes nothing (or passes only the
    long-standing min_recurrence) behaves identically to before.

    This mirrors the discipline of ground_relations' resolver: read held data,
    invent nothing, and REFUSE rather than fabricate."""
    if not phrase:
        return None
    words = _tok(phrase)
    if not words:
        return None
    low = [w.lower() for w in words]
    # all light/pronoun -> nothing named.
    if all(w in _PRONOUNS or w in _LEADING_LIGHT for w in low):
        return None
    # strip leading light words; the head noun is what must ground.
    core = list(low)
    while core and core[0] in _LEADING_LIGHT:
        core = core[1:]
    if not core:
        return None
    content = [w for w in core if w not in _LEADING_LIGHT and w not in _PRONOUNS]
    # drop 1-character alphabetic fragments (a possessive 's', a stray 'a'): they
    # are morphological debris ("another's result" -> ['another','s','result']),
    # not content — never part of a real referent name.
    content = [w for w in content if not (len(w) == 1 and w.isalpha())]
    # SHORT noun phrase only: a long span is a clause, not a name. The cut is the
    # tuneable `max_content_words` knob (default 3 = today's hard-coded rule).
    if not content or len(content) > max_content_words:
        return None
    # a VERB cue anywhere marks a verb phrase (an action), not a thing.
    if any(w in _CLAUSE_VERBS for w in content):
        return None
    head = content[-1]
    if head in _PRONOUNS or head in _LEADING_LIGHT:
        return None
    head_pos = _wiktionary_pos(head)
    # the head MUST be able to be a noun.
    if "noun" not in head_pos and "name" not in head_pos:
        return None
    # NOUN-HEAD RULE (the main strictness dial, `require_noun_dominant_head`).
    #
    # CONSERVATIVE (default True) — TODAY's BRIGHT-LINE rule: the head's DOMINANT
    # (primary) Wiktionary sense must be a noun/name. A head whose dominant sense
    # is a VERB ('coordinate', 'continue', 'result', 'refresh') is, in a relation
    # object span, almost always the VERB of a CLAUSE ('multiple cores
    # COORDINATE', 'the application CONTINUE') — even when a noun sense exists.
    # Requiring noun-DOMINANCE is the conservative, honest cut: it refuses a
    # genuine but verb-dominant referent ('periodic refresh') rather than risk
    # minting a clause. Mirrors the held POS faculty's dominant-sense reading
    # (construction_grammar._pos_token reads posset[0] as `dom`). A high refusal
    # rate here is the gate working.
    #
    # PERMISSIVE (False) — the dominance check RELAXES to 'noun in head_pos': a
    # head that merely HAS a noun sense is admitted even when a verb sense is
    # dominant. This recovers genuine-but-verb-dominant referents ('periodic
    # refresh', 'matrix tile blocking') at the cost of admitting some borderline
    # clauses. This is the precision<->recall dial the caller turns via MintPolicy.
    # (The 'noun in head_pos' floor above still holds either way, so a head with
    # NO noun sense at all is refused at both settings.)
    if require_noun_dominant_head and head_pos and head_pos[0] not in ("noun", "name"):
        return None
    if len(content) == 1:
        # a lone content word is a known quality surface? refuse (adjective genus).
        if head in _NON_REFERENT_HEADS:
            return None
    else:
        # multi-word: every pre-head content word must be a nominal MODIFIER
        # (adjective or noun); a verb-led modifier makes it a clause.
        for w in content[:-1]:
            wp = _wiktionary_pos(w)
            if not wp:
                # an unknown modifier (a proper compound part, a symbol) is
                # allowed only if it is not a clause verb (already checked) —
                # treat as a nominal compound part.
                continue
            if not (set(wp) & _MODIFIER_POS):
                return None
    name = _normalise_referent_name(content)
    if not name:
        return None
    # ALREADY HELD? then it is ground_relations' job to wire it, not ours to mint.
    low_join = " ".join(content)
    for key in (name, low_join, low_join.replace(" ", "_"),
                " ".join(_stem(w) for w in content)):
        if keymap.get(key) is not None:
            return None
    # RECURRENCE gate (optional): require the referent to appear >= N times.
    if min_recurrence > 1:
        cnt = (recurrence or {}).get(name, 0)
        if cnt < min_recurrence:
            return None
    return name, content


def mint_referents_from_relations(substrate, mt_name: Optional[str] = None, *,
                                  index: Optional[dict] = None,
                                  prose_attrs: Iterable[str] = ("definition", "why"),
                                  min_recurrence: Optional[int] = None,
                                  gate_params: Optional[dict] = None) -> dict:
    """MINT the missing referents that ground_relations DROPS, then wire the
    relation edge to them — the OTHER half of the sparse-relational-witness
    problem. Faithful, gated, idempotent.

    Pipeline:
      1. run ground_relations (mt-scoped) to collect the DROPPED object phrases
         (src_name, edge_type, object_phrase);
      2. for each drop whose edge_type is a telic/constitutive/agentive relation
         cue (NOT the genls copula-genus route) and whose phrase passes
         `_referent_candidate` (a clean short noun phrase, head is a noun, not a
         clause/verb/stopword, not already held): MINT a Concept named for the
         normalised phrase — idempotent, reusing a referent already minted this
         pass — with `minted_referent: true` provenance + `definition` = the
         phrase, and OPEN the relation production (defensively);
      3. wire the SAME relation edge (used_for / has_part / causes / depends_on /
         …, exactly the cue ground_relations detected) from the source Concept to
         the newly-held referent, so the edge grounds HONESTLY (the target is now
         a held Concept — the gate is satisfied, not bypassed);
      4. REFUSE (do not mint, leave dropped) every phrase that fails the test.

    The minted referent is THIN by design — name + definition only — so it lights
    up `lexical:formal` (its type) and, on the SOURCE, the incoming relation's
    role (telic/constitutive/agentive). The referent itself stays a sparse LEAF;
    that is honest (it is a leaf the corpus named but did not elaborate).

    Returns {minted, refused, refusal_rate, edges_added, wired:[(src,et,name)],
             minted_names:[...], refused_phrases:[(src,et,phrase)],
             reused, mt, gate}.

    STRICTNESS is graph-resident POLICY. The gate's three knobs (min_recurrence,
    max_content_words, require_noun_dominant_head) are read off the singleton
    MintPolicy node (minted with SAFE DEFAULTS that reproduce today's behaviour
    EXACTLY if absent — see ensure_mint_policy). A caller may OVERRIDE the graph
    policy for one call by passing `gate_params={...}` (any subset of knobs), and
    the long-standing `min_recurrence=` keyword still overrides just that knob for
    back-compat with existing callers/tests. Nothing changes vs. before unless the
    agent tunes the node (or passes an override) — the off-by-default discipline."""
    if index is None:
        index = _concept_by_name(substrate)
    # defensively ensure the relation productions are open (idempotent).
    try:
        open_relation_productions(substrate)
    except Exception:
        pass

    # STRICTNESS — read the graph-resident MintPolicy node WITHOUT minting it
    # (mint_gate_params(ensure=False)): a graph with no node reads as all-safe-
    # defaults == today AND gains no node, so a default run is a pure no-op on the
    # graph shape (the off-by-default discipline of auto_approve.get_policy). Once
    # the agent has tuned the gate (ensure_mint_policy/set_mint_gate mints it), its
    # values are read here. Per-call overrides layer on top. The node read is
    # mechanical boundary I/O; the DECISION stays inside _referent_candidate.
    # `min_recurrence=` (long-standing kwarg) and an explicit `gate_params=` dict
    # both override just the knobs they name, so existing callers/tests keep working.
    params = mint_gate_params(substrate, ensure=False)
    if gate_params:
        for k, v in gate_params.items():
            if k in MINT_POLICY_DEFAULTS and v is not None:
                params[k] = v
    if min_recurrence is not None:
        params["min_recurrence"] = int(min_recurrence)
    eff_min_recurrence = int(params["min_recurrence"])
    eff_max_content_words = int(params["max_content_words"])
    eff_require_noun_dominant = bool(params["require_noun_dominant_head"])

    # 1. collect the dropped object phrases from ground_relations.
    gr = ground_relations(substrate, mt_name, index=index, prose_attrs=prose_attrs)
    dropped = gr.get("dropped", [])

    keymap, _head_map, _acro_map = _build_resolver_index(index)

    # RECURRENCE tally (only needed when min_recurrence > 1): how many distinct
    # drops name each normalised referent. Cheap first pass over the drops. Tally
    # with min_recurrence=1 (count all candidates) but the SAME length/head knobs,
    # so the count reflects what the effective gate would otherwise admit.
    recurrence: dict[str, int] = {}
    if eff_min_recurrence > 1:
        for (_src, et, phrase) in dropped:
            if et not in _MINTABLE_EDGE_TYPES:
                continue
            cand = _referent_candidate(
                phrase, keymap, min_recurrence=1,
                max_content_words=eff_max_content_words,
                require_noun_dominant_head=eff_require_noun_dominant)
            if cand is not None:
                recurrence[cand[0]] = recurrence.get(cand[0], 0) + 1

    minted = 0
    reused = 0
    refused = 0
    edges_added = 0
    wired: list[tuple[str, str, str]] = []
    minted_names: list[str] = []
    refused_phrases: list[tuple[str, str, str]] = []
    minted_this_pass: dict[str, Any] = {}

    for (src_name, et, phrase) in dropped:
        # only mint for the relation cues (not the genls copula-genus route).
        if et not in _MINTABLE_EDGE_TYPES:
            refused += 1
            refused_phrases.append((src_name, et, phrase))
            continue
        cand = _referent_candidate(
            phrase, keymap, min_recurrence=eff_min_recurrence,
            max_content_words=eff_max_content_words,
            require_noun_dominant_head=eff_require_noun_dominant,
            recurrence=recurrence)
        if cand is None:
            refused += 1
            refused_phrases.append((src_name, et, phrase))
            continue
        name, content = cand
        src = index.get(src_name)
        if src is None:
            refused += 1
            refused_phrases.append((src_name, et, phrase))
            continue

        # 2. MINT (idempotent): reuse a referent minted this pass or already held.
        ref = minted_this_pass.get(name) or index.get(name)
        if ref is None:
            ref = substrate.add_node("Concept", {
                "name": name,
                "origin": "relation_grounding",
                "minted_referent": True,
                "definition": " ".join(content),
            })
            index[name] = ref
            minted_this_pass[name] = ref
            minted += 1
            minted_names.append(name)
        else:
            if name in minted_this_pass:
                reused += 1
            # else: name collided with an already-held concept created between
            # ground_relations' resolve and now — treat as reuse of held.

        if ref == src:
            # self-loop guard (a source whose own name normalises to the phrase).
            refused += 1
            refused_phrases.append((src_name, et, phrase))
            continue

        # 3. WIRE the SAME relation edge to the now-held referent (idempotent).
        if not _has_edge(substrate, src, et, ref):
            try:
                substrate.add_edge(src, et, ref, {})
                edges_added += 1
            except Exception:
                # edge rejected -> no fabrication; count the phrase as refused.
                refused += 1
                refused_phrases.append((src_name, et, phrase))
                continue
        wired.append((src_name, et, name))

    total = minted + refused
    refusal_rate = (refused / total) if total else 0.0
    return {"minted": minted, "reused": reused, "refused": refused,
            "refusal_rate": refusal_rate, "edges_added": edges_added,
            "wired": wired, "minted_names": minted_names,
            "refused_phrases": refused_phrases, "mt": mt_name,
            "gate": {"min_recurrence": eff_min_recurrence,
                     "max_content_words": eff_max_content_words,
                     "require_noun_dominant_head": eff_require_noun_dominant},
            "ground_relations": {k: gr[k] for k in
                                 ("telic", "constitutive", "agentive", "formal",
                                  "candidates", "grounded", "drop_rate")}}


__all__ = [
    "RELATION_EDGE_TYPES",
    "MINT_POLICY_NODE_TYPE", "MINT_POLICY_DEFAULTS", "MINT_GATE_SETTABLE_FIELDS",
    "open_relation_productions",
    "resolve_object",
    "extract_relation_candidates",
    "ground_relations",
    "mint_referents_from_relations",
    "ensure_mint_policy", "mint_gate_params", "set_mint_gate",
    "_mint_policy_node",
    "MINT_GATE_PINNED_ATTR", "_disposition_derived_gate",
]
