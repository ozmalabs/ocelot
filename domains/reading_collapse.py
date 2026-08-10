"""reading_collapse — READING AS COLLAPSE OVER A CONSTRUCTION CODEBOOK.

The escape from the trenchcoat. Concept/meaning extraction today is a stack of
construction-specific parsers (`gap_driven_acquisition.extract_microtheory` is
ENUM-CUE-ONLY: a regex over "such as / includes / consists of", which yields 0
on definitional prose). A parser returns 0 on an unseen construction. A READER
grounds it because it can LEARN the construction's shape.

This module makes reading the substrate's OWN core loop pointed at language:

  CLAUSE ─recognise→ MARKER SKELETON ─ShapeDecode→ WINNING CONSTRUCTION ─template→ PREDICATION
                              │
                              └─ residual (no construction covers) ─sd loop→ MINT ─install→ re-decode ─→ PREDICATION

  1. CLAUSE -> DECODABLE SHAPE. A clause is recognised into words by the held
     recognition tokenizer (`comprehend_text._recognise_words` /
     `_recognise_regions` — NO whitespace/regex). Each recognised construction
     MARKER (copula, subordinator, relativizer, preposition, the main verb —
     read against the held `MarkerClass` lexicon, recognition against graph data)
     becomes a SINGLE-ELEMENT relation whose PREDICATE is the marker's normalised
     class: `[["COP"]]`, `[["IF"],["THEN"]]`, `[["OF"]]`. Determiners and list
     conjunctions are role-glue, not skeleton markers. The marker sits in the
     PREDICATE slot on purpose — `sd_transform_decode` can substitute an ARGUMENT
     slot (a transform, no growth) but never the predicate, so a genuinely novel
     marker skeleton produces a real residual and MINTS rather than being
     explained away as a transform of a held construction.

  2. CONSTRUCTION CODEBOOK = held `ShapeSignature{kind:"construction"}` nodes
     (`seeds/reading_constructions.json`), one per predication construction
     (definitional / enumeration / causal / comparative / conditional /
     attributive / event). Each carries its distinctive marker skeleton as its
     `signature` and a construction-GENERAL `ground_template`.

  3. READING = ShapeDecode. The clause skeleton is DECODED against the codebook by
     `reflective_faculty.compose_design_for_goal` (the Rust `ShapeDecode` Term —
     the collapse op). The construction with the best `shape_fit` and zero residual
     WINS (the decode decides, not a Python branch); its `ground_template` fills the
     roles into a predication. The meaning EMERGES from the collapse.

  4. DYNAMICALLY LEARN (the headline). A clause whose skeleton NO construction
     covers has a non-empty residual. `reflective_faculty.induce_concern` drives the
     sd loop (`seeds/shape_decode_loop.json`: `sd_decode`/`sd_mint_quantum`) — the
     residual MINTS a CapabilityAxis quantum. This module then INSTALLS the skeleton
     as a NEW construction `ShapeSignature` and bumps `codebook_epoch` (the same
     "rule decides to mint, Python installs" split `arrangement_codebook`/`ink_decode`
     already use); `sd_redecode` re-arms and the re-decode GROUNDS it. A novel
     construction is LEARNED, not bolted on.

  5. FAULTY. A garbled clause decodes to the NEAREST construction (its recognisable
     markers cover part of the skeleton) and grounds that predication; the unmatched
     span is the flagged residual — robust the way recognition sees through bad
     spacing.

ARCHITECTURE (CLAUDE.md). The DECISION that carries meaning — WHICH construction —
is the ShapeDecode collapse's, read off its own `shape_fit`/`residual`; the LEARN is
the seeded `sd_*` rules via `run_rules`. This module only (a) turns a recognised
clause into a skeleton via held faculties (mechanical marker recognition + POS verb
head), (b) reads the decode's verdict, (c) fills the winning construction's own
`ground_template` (one general routine, mode-dispatched by DATA — never a
per-construction `if`/`else` deciding the predication), (d) installs a minted
construction as graph data. No new hardcoded per-construction regex; a novel
construction WINS by decode after it is MINTED.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import comprehend_text as ct
from domains import instruction_reading as ir
from domains import preposition_roles as pr
from domains import reflective_faculty as rf

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CODEBOOK_SEED = os.path.join(_ROOT, "seeds", "reading_constructions.json")

# Marker classes that CONTRIBUTE to a construction's identity skeleton (the
# construction-distinctive markers). Determiners / list-conjunctions are role
# glue (see _GLUE) — they bound roles but never identify a construction.
_SKELETON = {"COP", "INCL", "SUCH", "AS", "IF", "THEN", "REL", "OF", "TO", "FOR",
             "WITH", "BY", "FROM", "CAUSE_SUB", "CAUSE_V", "UNLIKE", "LIKE", "THAN",
             "DESIGNATE", "POSSESS", "PPART",
             # in-situ definition boundary markers (_ground_insitu_definition) --
             # mirrored here (not just in seeds/reading_constructions.json's
             # ReadingRoles node) so the FIRST-EVER `ensure_codebook` call on a
             # fresh agent (whose `_refresh_lexicon` runs BEFORE that call's own
             # seed install) already recognises them -- else only the SECOND
             # read_clause call in a session would see them.
             "BOUND_COMMA_DEF", "BOUND_PAREN_DEF"}
_GLUE = {"DET", "AND", "OR"}


# --------------------------------------------------------------------------- #
#  resolution + codebook install (mechanical adapter I/O — no decision).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    return sub, native, ag_node


def _refresh_lexicon(sub) -> None:
    """Populate the closed-class + marker-role caches FROM THE GRAPH (the
    `ClosedClass` / `ReadingRoles` nodes in seeds/reading_constructions.json). The
    GRAPH is the source of truth; these module names are a performance cache
    (CLAUDE.md permits Python caching of graph-resident data). Falls back to the
    in-code default per role when a node is absent (an older seed), so behaviour is
    unchanged. Cheap + idempotent; called unconditionally by ensure_codebook so a
    seed-booted agent (whose codebook install is skipped) still reads its lexicon
    off the graph, exactly as the reading rules will."""
    global _AUX, _PP_PREPS, _DETERMINERS, _LEAD_CONNECTIVES, _INVERSION_AUX, _WH_FRONTING
    global _SKELETON, _GLUE, _PREP, _STRUCTURING, _CLAUSE_OPENERS
    cc: dict = {}
    for n in sub.nodes("ClosedClass"):
        at = sub.node(n)["attrs"]
        role, forms = at.get("role"), at.get("forms")
        if role and forms:
            cc[role] = frozenset(str(f).lower() for f in forms)
    _AUX = cc.get("aux", _AUX)
    _PP_PREPS = cc.get("pp_prep", _PP_PREPS)
    _DETERMINERS = cc.get("determiner", _DETERMINERS)
    _LEAD_CONNECTIVES = cc.get("lead_connective", _LEAD_CONNECTIVES)
    _INVERSION_AUX = cc.get("inversion_aux", _INVERSION_AUX)
    _WH_FRONTING = cc.get("wh_fronting", _WH_FRONTING)
    roles = None
    for n in sub.nodes("ReadingRoles"):
        roles = sub.node(n)["attrs"]
        break
    if roles:
        _SKELETON = set(roles.get("skeleton") or _SKELETON)
        _GLUE = set(roles.get("glue") or _GLUE)
        _PREP = set(roles.get("prep") or _PREP)
        _CLAUSE_OPENERS = set(roles.get("clause_opener") or _CLAUSE_OPENERS)
    _STRUCTURING = _SKELETON - _PREP


def ensure_codebook(agent) -> None:
    """Idempotently install the reading construction codebook (`MarkerClass` +
    `ShapeSignature{kind:'construction'}` nodes) + arm the sd loop. Guarded by a
    graph-resident `Seed{id:'reading_constructions'}` node — the SAME idempotency
    idiom `reflective_faculty._ensure_shape_decode_loop` uses. Mechanical seed I/O."""
    sub, native, ag_node = _resolve(agent)
    _refresh_lexicon(sub)          # closed-class + marker-role caches from the graph
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "reading_constructions":
            return
    with open(_CODEBOOK_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "reading_constructions", "version": manifest.get("version", "1.0.0")})
    # arm the codebook epoch (sd_redecode's re-decode gate) if not yet set.
    if ag_node is not None and sub.node(ag_node)["attrs"].get("codebook_epoch") is None:
        sub.set_attr(ag_node, "codebook_epoch", 0.0)


_EVENT_FRAMES_SEED = os.path.join(os.path.dirname(__file__), "..", "seeds",
                                  "event_role_frames.json")
_ROLE_LOOP_SEED = os.path.join(os.path.dirname(__file__), "..", "seeds",
                               "role_decode_loop.json")


def _ensure_role_decode_loop(agent) -> None:
    """Idempotently install the role-growth rungs (`role_decode_loop`:
    rf_mint_role/rf_recognize/rf_redecode) so an uncaptured animate participant
    (a role residual) mints a RoleFrame via `run_rules()` — the role analogue of
    the shape sd-loop. Guarded by a `Seed{id:'role_decode_loop'}` node. Mechanical
    seed I/O; the growth DECISION lives in the seeded rules."""
    sub, native, ag_node = _resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "role_decode_loop":
            return
    with open(_ROLE_LOOP_SEED) as f:
        manifest = json.load(f)
    if native is not None and hasattr(native, "load_seed_manifest") and ag_node is not None:
        native.load_seed_manifest(manifest, ag_node)
    if ag_node is not None and sub.node(ag_node)["attrs"].get("codebook_epoch") is None:
        sub.set_attr(ag_node, "codebook_epoch", 0.0)
    sub.add_node("Seed", {"id": "role_decode_loop",
                          "version": manifest.get("version", "0.1.0")})


def ensure_event_frames(agent) -> None:
    """Idempotently install the EVENT-GROUNDING seed (`event_role_frames`): the
    clause-graph vocabulary (Phase 1: `EventClause`/`Token` node types + `has_token`/
    `next` edge productions) and, in later versions, the VerbFrame codebook + role
    rules. Loaded through the Rust `load_seed_manifest` (which registers the
    productions into \u0393 so the clause-graph edges the ingest writes are admissible)
    and the seeded rules so `run_rules()` fires them. Guarded by a graph-resident
    `Seed{id:'event_role_frames'}` node \u2014 the SAME idempotency idiom `ensure_codebook`
    uses. Mechanical seed I/O, no decision."""
    sub, native, ag_node = _resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "event_role_frames":
            return
    with open(_EVENT_FRAMES_SEED) as f:
        manifest = json.load(f)
    if native is not None and hasattr(native, "load_seed_manifest") and ag_node is not None:
        native.load_seed_manifest(manifest, ag_node)
    else:                              # no native loader (pure-Python test graph)
        for nd in manifest.get("nodes", []):
            sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    # Materialise the VerbFrame CODEBOOK as graph nodes (the DATA the decode reads):
    # one VerbFrame per role-assignment step, carrying its priority + guard/effect
    # Term JSON. Graph-resident so `_decode_roles_graph` reads them, `reading_trace`
    # introspects them, and Phase 3 can MINT a novel role frame alongside them.
    for fr in manifest.get("frames", []):
        sub.add_node("VerbFrame", dict(fr.get("attrs", {})))
    # RoleFrame EMIT codebook (Phase 3): growable participant roles (the thematic
    # oblique ships by default; a novel role is minted into this same set).
    for rf in manifest.get("role_emits", []):
        sub.add_node("RoleFrame", dict(rf.get("attrs", {})))
    sub.add_node("Seed", {"id": "event_role_frames",
                          "version": manifest.get("version", "0.1.0")})
    _ensure_role_decode_loop(agent)


def _marker_lexicon(sub) -> dict[str, str]:
    """Mechanical graph read: the held (surface -> normalised class) function-word
    lexicon (`MarkerClass` nodes). Recognition against held data, not a regex."""
    lex: dict[str, str] = {}
    for n in sub.nodes("MarkerClass"):
        at = sub.node(n)["attrs"]
        cls = at.get("cls")
        for form in (at.get("forms") or []):
            lex[str(form).lower()] = cls
    return lex


# --------------------------------------------------------------------------- #
#  MAIN-VERB / NESTED-OF PRECEDENCE — which token heads the main predication
#  when a finite verb and a nested preposition compete for the clause's skeleton
#  ('He promoted the burning OF fossil fuels' — the finite verb 'promoted'
#  should head the clause; 'of' is a nested-PP relation inside the object NP,
#  not the clause's own skeleton marker). The DECIDING fact — that OF yields
#  precedence to an already-seen finite verb — is HELD DATA on the OF
#  MarkerClass (`yields_to_finite_verb`, seeds/reading_constructions.json),
#  read by `_of_yields_to_finite_verb` below: absent that taught fact (an
#  older/ablated seed), the guard in `_skeleton_from_words` never fires and
#  every 'of' reads exactly as it did before this phase. Mirrors the QUANTIFIER
#  partitive-glue precedent just above it in `_skeleton_from_words`.
# --------------------------------------------------------------------------- #
def _of_yields_to_finite_verb(sub) -> bool:
    """Held fact read: does the OF MarkerClass declare `yields_to_finite_verb`?
    Graph read, not a hardcoded True — an agent that has not been taught this
    fact (or one where it has been ablated) sees this return False and the
    finite-verb-precedence guard below never fires."""
    for n in sub.nodes("MarkerClass"):
        at = sub.node(n)["attrs"]
        if at.get("cls") == "OF" and at.get("yields_to_finite_verb"):
            return True
    return False


_OF_PRECEDENCE_WINDOW = 5  # see docstring below — a LOCAL lookback bound, not the
                            # whole clause-so-far.


def _left_run_has_finite_verb(tokens: list, window: int = _OF_PRECEDENCE_WINDOW) -> bool:
    """Strict TIER-A-ONLY finite-verb detection (the strongest held signal an
    inflected form whose primary POS reads verb, held verb-headed — the same
    tier `_find_main_verb`'s (A) prefers) — deliberately NOT the full
    `_find_main_verb` ladder, whose looser tiers (B/C) would over-fire on a
    content word that merely CARRIES a rare verb sense (a gerund head noun like
    'burning' itself, or a bare content noun) rather than truly heading a finite
    predication. Skips AUX/PP/DET tokens the same way `_find_main_verb` does.

    Scoped to the last `window` tokens ONLY (a LOCAL lookback, not an unbounded
    scan of everything accumulated so far) — this is the caller's clause-local
    run (`cur`, reset at every skeleton marker), but a run can still be long
    when clause segmentation upstream has failed to break a multi-sentence
    span apart (a corpus artifact — nested-quote dialogue the sentence
    splitter did not separate). An unbounded scan there would find a genuine
    but IRRELEVANT finite verb many tokens back ('...they REPLIED, ... in a
    short time died OF hunger' — 'replied' is a real tier-A verb, but it does
    not compete with THIS 'of'; it belongs to an entirely different, already-
    reported clause). The window is measured empirically against the frozen
    Aesop+Grimm parity corpus (see the phase-1 diff audit): small enough to
    exclude that cross-clause false positive, large enough to admit a
    modifier run between a transitive verb and its direct-object head
    ('promoted the wasteful ongoing burning of ...').

    Used only to gate the OF finite-verb-precedence guard, over the content
    run BEFORE the token immediately preceding 'of' (that immediate head is
    the OF phrase's own governing noun/gerund, never itself the competing
    verb — see the caller). A bare `-ing` form is explicitly EXCLUDED even
    though `_inflected_verb` (via WordNet morphy) reads it as "inflected":
    English morphology requires an auxiliary for a progressive/gerund to be
    FINITE ('was saying' / 'the burning'), so a lone '-ing' word is never
    itself the finite verb — without this exclusion a participial adjunct
    ('...boasted very much of his philanthropy, SAYING that of all animals
    he...') or a gerund-headed subject ('the BURNING of fossil fuels...')
    would wrongly read as the clause's finite predicate (audited false
    positive against the frozen parity corpus).

    Scans BACKWARD (nearest token first) and STOPS at a preposition
    (`_PP_PREPS`) rather than skipping over it: an intervening preposition
    means the OF phrase's head noun is that preposition's own object, not the
    verb's direct object, so a verb on the FAR side of it does not actually
    compete for this 'of' ('the CONTROVERSY prevailed AMONG the beasts OF the
    field' — 'prevailed' is a real tier-A verb, but 'beasts' is the object of
    'among', not of 'prevailed'; stopping at 'among' correctly withholds the
    guard, leaving this genuine genitive-of NP — 'the beasts of the field' —
    untouched, the same status as 'the son of a man'). AUX/DET are still
    skipped (they never break a verb-direct-object relation: 'has PROMOTED
    the burning of...')."""
    for w in reversed(tokens[-window:]):
        wl = str(w).lower()
        if wl in _AUX or wl in _DETERMINERS:
            continue
        if wl in _PP_PREPS:
            return False
        if wl.endswith("ing"):
            continue
        if _inflected_verb(wl) and _primary_pos(wl) == "verb" and ir.is_verb_headed(wl):
            return True
    return False


def _clause_is_simple_svo(words: list) -> bool:
    """True iff the WHOLE clause `words` carries AT MOST ONE strict TIER-A
    finite verb — the proxy this guard requires for "this is a single simple
    clause, not a coordinated/compound multi-verb sentence" before it glues an
    'of' away. Without this gate, a compound sentence with several
    comma-joined VPs and no OTHER skeleton marker anywhere ('Hans took out his
    pocket-handkerchief, PUT the piece OF silver into it, THREW it over his
    shoulder, and JOGGED off...') would have its sole 'of' glued away, leaving
    the clause with ZERO skeleton markers — which routes the WHOLE compound
    sentence through the bare-S-V-O fallback's single-verb-pick ladder
    (`_find_main_verb`, whose own docstring documents it scans tier-by-tier
    ACROSS THE WHOLE SPAN), collapsing several independent coordinated
    predicates into one wrong giant predication (audited regression against
    the frozen parity corpus — a previously-honest "no covering construction"
    residual became a confidently WRONG multi-clause mash). A clause with only
    one finite verb has no such competing coordinate clause to swallow."""
    n = 0
    for w in words:
        wl = str(w).lower()
        if wl in _AUX or wl in _PP_PREPS or wl in _DETERMINERS or wl.endswith("ing"):
            continue
        if _inflected_verb(wl) and _primary_pos(wl) == "verb" and ir.is_verb_headed(wl):
            n += 1
            if n > 1:
                return False
    return True


def _no_later_skeleton_marker(lex: dict, words: list, i: int) -> bool:
    """True iff no token AFTER position `i` in `words` is itself a (plain,
    lexicon-recognised) skeleton-class marker. A conservative LOOKAHEAD gate
    for the OF finite-verb-precedence guard: a clause where some OTHER marker
    (a later copula, subordinator, preposition-marker, ...) still fires
    downstream already HAS its own real segmentation point there, and gluing
    THIS 'of' away would pull a genuine argument (the OF phrase) across that
    later boundary into the wrong role span ('the fox informed him OF the
    difficulty they WERE both in' — 'informed' precedes 'of' as a real
    transitive verb, but the clause's own later COP ('were') still fires and
    naturally isolates 'both in'; without this gate, the earlier glue drags
    'difficulty' into the SUBJECT-side role instead of remaining the verb's
    own object, and the real content word is lost from the final predication
    — an audited regression). Only a genuinely LAST-marker 'of' (nothing left
    to naturally close off the clause afterward) is eligible to become the
    fallback's own verb-finding boundary. A conservative PLAIN lexicon lookup
    (not the full adjacency/morphology join machinery) — erring toward
    leaving more 'of's untouched is safe under this phase's goal."""
    for j in range(i + 1, len(words)):
        if lex.get(str(words[j]).lower()) in _SKELETON:
            return False
    return True


# --------------------------------------------------------------------------- #
#  JOIN-BY-ADJACENCY — a NEW surface marker joins a MarkerClass by NEARNESS to
#  its members, NOT by editing a hardcoded list. The class-learning mechanism:
#  a MarkerClass may declare an `adjacency_anchor` (member base-verb lemmas) + an
#  `adjacency_threshold`; an UNRECOGNISED word whose verb sense is near the anchor
#  (WordNet path-similarity, the FUNCTIONAL/SEMANTIC nearness signal — the same
#  held WordNet faculty `_clean_head` reads) COLLAPSES INTO that class, so the ONE
#  class-construction over the class covers it without a new leaf. Any class can
#  gain join-by-adjacency by declaring an anchor; DESIGNATION is the one seeded.
# --------------------------------------------------------------------------- #
_ADJ_CACHE: dict[str, tuple] = {}     # word -> (cls|None, score, nearest_member)


def _class_anchors(sub) -> list:
    """The MarkerClasses that admit join-by-adjacency: those declaring an
    `adjacency_anchor` (a set of member base-verb lemmas defining the class's
    nearness target) + threshold + the distributional CONTEXT the class's markers
    occupy (`adjacency_context`, e.g. 'post_copular'). Graph read, not a hardcoded
    set."""
    out: list = []
    for n in sub.nodes("MarkerClass"):
        at = sub.node(n)["attrs"]
        anch = at.get("adjacency_anchor")
        if anch:
            try:
                thr = float(at.get("adjacency_threshold", 0.5))
            except (TypeError, ValueError):
                thr = 0.5
            ctx = at.get("adjacency_context")
            out.append((n, at.get("cls"), [str(a).lower() for a in anch], thr, ctx))
    return out


def _wordnet_nearness(word: str, anchors: list) -> tuple:
    """FUNCTIONAL/SEMANTIC nearness: the max WordNet verb-sense path-similarity of
    `word` to the class's anchor lemmas, with the nearest anchor. The held WordNet
    faculty is the distributional/semantic model already used across reading; no
    regex, no hand map. Returns (score, nearest_anchor)."""
    try:
        from nltk.corpus import wordnet as wn
    except Exception:
        return 0.0, None
    try:
        ws = wn.synsets(word, pos="v")
    except Exception:
        ws = []
    if not ws:
        return 0.0, None
    best, arg = 0.0, None
    for st in ws:
        for a in anchors:
            try:
                asyn = wn.synsets(a, pos="v")
            except Exception:
                asyn = []
            for sa in asyn:
                try:
                    v = st.path_similarity(sa) or 0.0
                except Exception:
                    v = 0.0
                if v > best:
                    best, arg = v, a
    return best, arg


def _compute_adjacency(sub, word: str, context: Optional[str] = None) -> tuple:
    """Best marker-class for `word` by adjacency, or (None, 0, None). Two functional
    signals must BOTH hold: (1) SEMANTIC nearness — the word's verb sense is near the
    class anchor (>= threshold); (2) DISTRIBUTIONAL slot — the word occupies the slot
    the class's markers occupy (`adjacency_context`; None = no positional constraint).
    The distributional gate rejects a polysemous noun ('report'/'point'/'saw') that
    carries a naming verb SENSE but is not in the marker's syntactic position. The
    DECODE-level analogue of `concept_graph._nearest_anchor`, lifted to marker-classes."""
    best_cls, best_score, best_member = None, 0.0, None
    for _n, cls, anchors, thr, ctx in _class_anchors(sub):
        if ctx is not None and ctx != context:
            continue                     # wrong distributional slot for this class
        score, member = _wordnet_nearness(word, anchors)
        if score >= thr and score > best_score:
            best_cls, best_score, best_member = cls, score, member
    return best_cls, best_score, best_member


def _marker_node_for_cls(sub, cls: str):
    for n in sub.nodes("MarkerClass"):
        if sub.node(n)["attrs"].get("cls") == cls:
            return n
    return None


def _join_class(sub, node, word: str, score: float, member) -> None:
    """Place `word` into the MarkerClass by ADJACENCY: extend the class's live forms
    (so it is now recognised as that class) + mint an `AdjacencyPlacement` evidence
    node recording the nearness signal + score. Idempotent. Mechanical graph write —
    the DECISION (nearness >= threshold) already happened in `_compute_adjacency`."""
    at = sub.node(node)["attrs"]
    forms = list(at.get("forms") or [])
    if word.lower() not in [str(f).lower() for f in forms]:
        forms.append(word.lower())
        try:
            sub.set_attr(node, "forms", forms)
        except Exception:
            pass
    already = False
    for p in sub.nodes("AdjacencyPlacement"):
        pa = sub.node(p)["attrs"]
        if str(pa.get("marker")).lower() == word.lower() and pa.get("cls") == at.get("cls"):
            already = True
            break
    if not already:
        sub.add_node("AdjacencyPlacement", {
            "marker": word.lower(), "cls": at.get("cls"), "nearness": float(score),
            "nearest_member": member, "signal": "wordnet_path_similarity",
            "joined_by": "adjacency"})


def _adjacency_place(agent, sub, word: str, context: Optional[str] = None) -> Optional[str]:
    """If `word` is unrecognised but ADJACENT to a marker-class (semantic nearness >=
    the class's threshold AND in the class's distributional slot `context`), collapse
    it INTO the class (live) and return the class; else None (it stays content).
    Cached by (word, context) (WordNet is deterministic); the graph join is re-applied
    per agent (idempotent)."""
    w = word.lower().strip()
    if len(w) < 3:
        return None
    key = (w, context)
    cached = _ADJ_CACHE.get(key)
    if cached is None:
        cached = _compute_adjacency(sub, w, context)
        _ADJ_CACHE[key] = cached
    cls, score, member = cached
    if cls is not None:
        node = _marker_node_for_cls(sub, cls)
        if node is not None:
            _join_class(sub, node, w, score, member)
    return cls


# --------------------------------------------------------------------------- #
#  JOIN-BY-MORPHOLOGY — a MarkerClass may declare a `morph_signal` (a held,
#  WordNet-driven MORPHOLOGICAL test) + a `morph_context` (the distributional slot
#  its markers occupy). An UNRECOGNISED word passing the signal's test IN that slot
#  COLLAPSES INTO the class. The GRAPH-NATIVE, agent-extensible analogue of
#  join-by-adjacency (above): past-participle-hood — the discriminator between a
#  PASSIVE predicate ('a page is EVICTED') and a copular adjective ('the glass is
#  FRAGILE') — is exposed as HELD DATA the agent TEACHES (a
#  MarkerClass{morph_signal:'past_participle', morph_context:'post_copular'}), so
#  the passive/copular distinction lives in graph data the agent extends, NOT in a
#  Python branch. The morphology TEST itself is a mechanical WordNet read (the same
#  held distributional/morphology model `_inflected_verb`/`_wordnet_nearness` use);
#  the name-keyed dispatch to it off the graph-declared `morph_signal` is the SAME
#  "name-keyed registry lookup on a graph verdict" split `composer_pick` uses.
# --------------------------------------------------------------------------- #
_PARTICIPLE_SUFFIXES = ("ed",)   # the PRODUCTIVE regular past-participle morphology.
#   IRREGULAR participles (eaten/given/beaten/shot/... -en/-wn/-rn/ablaut) now ALSO
#   join PPART via `_is_past_participle`'s irregular branch — held to a STRICTER
#   transitive-dominance MARGIN than the regular '-ed' bar (see that function's
#   docstring), which cleanly separates true irregular passive participles
#   (beaten/shot/struck/caught/eaten/stolen/given/hidden/driven/spoken/sold/bought/
#   brought) from ergative/resultative-leaning irregulars whose WordNet frame counts
#   run near-tied (grow/go/do/wear/tear — 'was grown very old', 'the food was gone',
#   'when we are done' stay STATIVE, gated by the margin, not a hand list). A SEPARATE
#   pre-existing routing fact (NOT this margin's job, left as a documented residual):
#   'broken'/'taken'/'held'/'written'/'known'/'chosen'/'seen'/'made' are claimed by
#   DESIGNATE's join-by-ADJACENCY (WordNet path-similarity to called/labeled/termed/
#   ...) before the morph path ever runs — a pre-existing DESIGNATE-adjacency
#   over-reach, unrelated to and unfixed by this change (see reading_collapse's
#   module docstring / commit history for the discriminator scope). Some irregulars
#   remain intentionally gated (e.g. 'torn': tear alternates ergatively like
#   break/grow and its WordNet ratio sits in the same ambiguous band) — the agent can
#   still teach specific irregular literal forms into the PPART MarkerClass when a
#   domain needs one the margin doesn't clear.
_MORPH_CACHE: dict = {}                          # (word, context) -> cls|None
# FINITE copula forms — those that head a MAIN predicate (so a following participle
# is the passive predicate). Non-finite be/been/being head embedded adjuncts.
_FINITE_COP = frozenset({"is", "are", "was", "were", "am", "'s"})


def _morph_classes(sub) -> list:
    """The MarkerClasses that admit join-by-MORPHOLOGY: those declaring a
    `morph_signal` (the held morphological test's name) + the distributional CONTEXT
    (`morph_context`) their markers occupy. Graph read, not a hardcoded set."""
    out: list = []
    for n in sub.nodes("MarkerClass"):
        at = sub.node(n)["attrs"]
        sig = at.get("morph_signal")
        if sig:
            out.append((at.get("cls"), str(sig), at.get("morph_context")))
    return out


_IRREGULAR_ITR_MARGIN = 0.3   # see docstring: irregular participles need a STRONGER
                              # transitive-dominance margin than the regular '-ed'
                              # form (bare majority is too weak off WordNet's noisy
                              # per-lemma frame counts for these high-polysemy verbs).
_NON_PARTICIPLE_TAILS = ("ing", "s")   # morphy is inflection-anonymous (it strips
                              # gerund/3sg-present tails the same way it strips an
                              # ablaut participle); these surface tails are NEVER a
                              # past-participle inflection, so the irregular branch
                              # excludes them before trusting morphy's lemma map.


def _is_past_participle(word: str) -> tuple:
    """HELD-faculty morphology (WordNet): is `word` the PAST-PARTICIPLE form of a
    TRANSITIVE verb? — the signal that a post-copular word is a PASSIVE predicate
    ('evicted'/'flushed'/'beaten'), NOT a copular adjective ('fragile'/'blue',
    whose verb-lemma via morphy is absent). Returns (is_ppart, base_lemma). Two held
    signals BOTH hold: (1) WordNet morphy maps `word` to a DISTINCT verb lemma (an
    inflected verb form — excludes a base-form adjective whose morphy_v is None or
    itself); (2) the base verb is TRANSITIVE (admits an object -> passivisable), read
    off WordNet's own verb frames (2/4/8/9/10/11/21..25 take an object) and DOMINATE
    the intransitive ones (a purely-ergative verb like 'grow' forms a RESULTATIVE
    'was grown very old', not a passive). A mechanical WordNet read, exactly the
    status of `_inflected_verb`.

    FORM: the PRODUCTIVE regular '-ed' morphology is unconditional (unchanged —
    parity-frozen); an IRREGULAR form (morphy maps it to a DISTINCT verb lemma via
    the WordNet exception list — beaten->beat, shot->shoot, caught->catch, ...) is
    ALSO admitted, but morphy is INFLECTION-ANONYMOUS: it strips '-ing'/'-s' just as
    readily as an ablaut past/participle ('hunting'->'hunt', same call shape as
    'beaten'->'beat'), so the irregular branch first EXCLUDES the '-ing'/'-s' surface
    tails (`_NON_PARTICIPLE_TAILS`) — those are GERUND/3sg-present inflections, never
    a participle, and admitting them was measured to misread active progressives
    ('A boy WAS HUNTING for locusts' -> wrongly hunt(_,boy)) as passive. Morphy's
    exception list also does not distinguish PAST TENSE from PAST PARTICIPLE (broke
    and broken both resolve to 'break'), so on top of the tail exclusion the
    irregular branch demands a STRICTER transitive-dominance MARGIN (not a bare
    majority) — the signal that separates true irregular passive participles
    (beat/shoot/strike/catch: itr/tr ~0.03-0.28, overwhelmingly object-taking) from
    ergative/resultative-leaning irregulars whose WordNet frame counts run close to
    tied (grow tr=20/itr=16 ratio .8; go(ne) tr=68/itr=57 ratio .84; do(ne) tr=31/
    itr=12 ratio .39; wear/tear sit in the same near-tied band) — 'was grown very
    old' / 'the food was gone' / 'when we are done' are RESULTATIVES/STATIVES, not
    passives, and the margin excludes them while admitting the clean cases. This is
    the SAME transitive-dominance signal the regular path already uses, just held to
    a tighter bar because the irregular surface form alone can't prove tense."""
    w = word.lower()
    try:
        from nltk.corpus import wordnet as wn
    except Exception:
        return False, None
    try:
        lem = wn.morphy(w, "v")
    except Exception:
        lem = None
    if not lem or lem == w:
        return False, None
    regular = w.endswith(_PARTICIPLE_SUFFIXES)
    if not regular and w.endswith(_NON_PARTICIPLE_TAILS):
        return False, None
    # TRANSITIVE-DOMINANT: passivisation requires an object slot, and the transitive
    # readings must DOMINATE the intransitive ones — a purely/predominantly
    # intransitive-ergative verb ('grow': 'the dog grew old') forms a RESULTATIVE
    # 'was grown', not a passive. Count WordNet verb frames: object-taking (2/4/8/9/
    # 10/11/21..25) vs subject-only (1/3/5/6/7). Held-faculty read, no hand map.
    tr = itr = 0
    try:
        for sy in wn.synsets(lem, pos="v"):
            for l in sy.lemmas():
                fr = l.frame_ids()
                if any(f in (2, 4, 8, 9, 10, 11, 21, 22, 23, 24, 25) for f in fr):
                    tr += 1
                if any(f in (1, 3, 5, 6, 7) for f in fr):
                    itr += 1
    except Exception:
        return False, None
    if regular:
        dominant = tr > itr
    else:
        dominant = tr > 0 and itr <= tr * _IRREGULAR_ITR_MARGIN
    return (dominant, lem if dominant else None)


def _participle_lemma(word: str) -> str:
    """The base verb lemma of a participle surface ('evicted'->'evict',
    'eaten'->'eat') via WordNet morphy — the passive event's predicate. Falls back
    to the lowered surface when morphy has no verb mapping. Mechanical WordNet read."""
    w = str(word).lower()
    try:
        from nltk.corpus import wordnet as wn
        lem = wn.morphy(w, "v")
        if lem:
            return lem
    except Exception:
        pass
    return w


# name -> held morphological faculty. The graph declares WHICH signal a class uses
# (`morph_signal`); Python mechanically runs that WordNet faculty (no decision).
_MORPH_TESTS = {"past_participle": _is_past_participle}


# --------------------------------------------------------------------------- #
#  PASSIVE/STATIVE COLLAPSE — CONFIDENCE-GRADED, the agent's JUDGMENT.
#  A post-copular transitive participle is passive-OR-stative. When the two are
#  genuinely balanced ('you are DIVIDED among yourselves'), the reading must COLLAPSE
#  (commit to one) yet stay a REVISABLE belief that flips trivially — the substrate's
#  own collapse framework (statement != belief != truth; held with confidence,
#  revisable). The JUDGMENT weighs HELD `PassiveLeanSignal` graph data (weights/leans
#  the agent extends by teaching) via named mechanical DETECTORS (WordNet / token
#  reads — the same status as `_wordnet_nearness`). confidence = clamp(prior +
#  Σ weight·lean·detector_value, 0, 1); >= `PassiveLeanPolicy.threshold` collapses
#  PASSIVE, else STATIVE. Clear cases stay confident ('a page is evicted' ~0.9);
#  '...divided among yourselves' collapses ~0.15 (reciprocal) → STATIVE, and the SAME
#  participle with a by-phrase strengthens → PASSIVE. Python is the mechanical
#  evaluator; the DECISION (signals, weights, threshold) is the agent's graph data.
# --------------------------------------------------------------------------- #
_EVENTIVE_LEX = frozenset({"verb.change", "verb.contact", "verb.motion",
                           "verb.possession", "verb.creation", "verb.consumption",
                           "verb.competition", "verb.body", "verb.social",
                           "verb.communication", "verb.weather"})
_STATIVE_LEX = frozenset({"verb.stative", "verb.cognition", "verb.emotion",
                          "verb.perception"})
_RECIPROCAL = frozenset({"themselves", "yourselves", "ourselves", "another",
                         "each", "other"})


def _det_eventive_lexname(sub, lem: str, words: list, i: int) -> float:
    """Eventiveness of the base verb by WordNet lexname: (eventive − stative senses)
    / total, in [-1, 1]. Purely eventive (evict = verb.contact) → +1; psych/stative
    tending → negative. Mechanical WordNet read."""
    try:
        from nltk.corpus import wordnet as wn
        lns = {s.lexname() for s in wn.synsets(lem, pos="v")}
    except Exception:
        return 0.0
    ev = len(lns & _EVENTIVE_LEX)
    st = len(lns & _STATIVE_LEX)
    return (ev - st) / (ev + st) if (ev + st) else 0.0


def _det_agent_by_phrase(sub, lem: str, words: list, i: int) -> float:
    """1.0 iff a `by`-phrase follows the participle (an explicit external agent →
    the hallmark of a canonical passive), else 0.0. Mechanical token read."""
    low = [str(w).lower() for w in words]
    return 1.0 if "by" in low[i + 1:] else 0.0


def _det_reciprocal(sub, lem: str, words: list, i: int) -> float:
    """1.0 iff the clause carries a reciprocal/reflexive marker (each other / one
    another / a -selves pronoun / 'among ...selves') → a mutual STATE, stative-
    leaning. Mechanical token read."""
    low = {str(w).lower() for w in words}
    return 1.0 if (low & _RECIPROCAL) else 0.0


def _det_transitive_dominance(sub, lem: str, words: list, i: int) -> float:
    """How strongly the base verb's WordNet frames are transitive over intransitive,
    normalized to [0, 1]. Mechanical WordNet read (same frames `_is_past_participle`
    weighs)."""
    try:
        from nltk.corpus import wordnet as wn
        tr = itr = 0
        for sy in wn.synsets(lem, pos="v"):
            for l in sy.lemmas():
                fr = l.frame_ids()
                if any(f in (2, 4, 8, 9, 10, 11, 21, 22, 23, 24, 25) for f in fr):
                    tr += 1
                if any(f in (1, 3, 5, 6, 7) for f in fr):
                    itr += 1
        return (tr - itr) / (tr + itr) if (tr + itr) and tr > itr else 0.0
    except Exception:
        return 0.0


def _det_psych_experiencer(sub, lem: str, words: list, i: int) -> float:
    """How strongly the base verb is a PSYCH/EXPERIENCER verb — a subject that 'is
    Verb-ed' is the EXPERIENCER of a mental STATE ('he was delighted/frightened'),
    not the patient of an external action → stative-leaning. Returns, in [0, 1], the
    FRACTION of the verb's WordNet senses that are `verb.emotion` (GRADED, so a verb
    DOMINATED by emotion — delight/please/frighten — leans strongly stative, while a
    physical verb with a MINOR incidental emotion sense — kill 'my feet are killing
    me', eat 'what's eating you' — barely moves and stays passive), OR 1.0 for a
    held `ExperiencerVerb` the AGENT teaches (the experiencer verbs WordNet files
    under cognition — surprise/amaze — so technical cognition verbs like reorder/
    compute are NOT swept in). Held-data + WordNet read; the roster is graph data."""
    # A by-phrase is decisive: an explicit external AGENT makes it a canonical
    # passive ('was DREADED BY all', 'was loved BY everyone'), not an experiencer
    # state — the psych lean must not override it, so suppress it here.
    if "by" in [str(w).lower() for w in words[i + 1:]]:
        return 0.0
    for n in sub.nodes("ExperiencerVerb"):
        if str(sub.node(n)["attrs"].get("name", "")).lower() == lem:
            return 1.0
    try:
        from nltk.corpus import wordnet as wn
        syns = wn.synsets(lem, pos="v")
        if syns:
            return sum(1 for s in syns if s.lexname() == "verb.emotion") / len(syns)
    except Exception:
        pass
    return 0.0


_DEGREE_WORDS = frozenset({"very", "quite", "rather", "so", "too", "more", "most",
                           "enough", "extremely", "highly", "fairly", "somewhat"})


def _det_resultative_complement(sub, lem: str, words: list, i: int) -> float:
    """1.0 iff the participle is followed by a RESULTATIVE adjective/degree complement
    ('was grown VERY OLD', 'was grown TALL') → the ergative/resultative reading (a
    state reached), stative-leaning, NOT an external agent's passive. The hallmark
    that separates an ergative 'was grown old' from a true passive 'was evicted'
    (clause-final / oblique). Mechanical: the next content token is a degree word or
    an adjective-primary word."""
    low = [str(w).lower() for w in words]
    j = i + 1
    if j < len(low) and low[j] in _DEGREE_WORDS:
        return 1.0
    if j < len(low):
        try:
            return 1.0 if _primary_pos(low[j]) in ("adj", "adjective", "a", "s") else 0.0
        except Exception:
            return 0.0
    return 0.0


# name -> held mechanical detector. The graph's PassiveLeanSignal declares WHICH
# detector + its weight/lean; Python runs the named faculty (no decision here).
_LEAN_DETECTORS = {"eventive_lexname": _det_eventive_lexname,
                   "psych_experiencer": _det_psych_experiencer,
                   "resultative_complement": _det_resultative_complement,
                   "agent_by_phrase": _det_agent_by_phrase,
                   "reciprocal": _det_reciprocal,
                   "transitive_dominance": _det_transitive_dominance}


def _passive_lean_policy(sub) -> tuple:
    """The held collapse policy (prior, threshold) — the agent's graph data."""
    for n in sub.nodes("PassiveLeanPolicy"):
        at = sub.node(n)["attrs"]
        try:
            return float(at.get("prior", 0.5)), float(at.get("threshold", 0.5))
        except (TypeError, ValueError):
            break
    return 0.5, 0.5


def _passive_confidence(sub, participle: str, words: list, i: int) -> float:
    """The agent's JUDGMENT: confidence that a post-copular participle is PASSIVE
    (vs stative), in [0, 1]. Reads the held `PassiveLeanSignal` weights/leans and
    combines the named mechanical detectors over the participle + clause. Graph data
    decides the weighting; the flip is one signal changing (add a by-phrase / a
    reciprocal marker). No policy node → a bare eventive+prior default."""
    lem = _participle_lemma(participle)
    prior, _thr = _passive_lean_policy(sub)
    signals = []
    for n in sub.nodes("PassiveLeanSignal"):
        at = sub.node(n)["attrs"]
        det = _LEAN_DETECTORS.get(at.get("detector"))
        if det is None:
            continue
        try:
            w = float(at.get("weight", 0.0)); ln = float(at.get("lean", 1.0))
        except (TypeError, ValueError):
            continue
        signals.append(w * ln * det(sub, lem, words, i))
    if not signals:                    # no held signals — fall back to eventiveness
        signals = [0.35 * _det_eventive_lexname(sub, lem, words, i)]
    conf = prior + sum(signals)
    return max(0.0, min(1.0, conf))


def _morph_place(agent, sub, word: str, context: Optional[str]) -> Optional[str]:
    """If `word` is unrecognised but passes a held MarkerClass's `morph_signal` test
    IN its declared `morph_context` slot, collapse it INTO that class (return the
    class). The morphology analogue of `_adjacency_place`; cached by (word, context)
    (WordNet is deterministic). No mutation of the class forms — the signal
    recomputes, so the class stays a MORPHOLOGICAL predicate, not a growing list."""
    w = word.lower().strip()
    if len(w) < 3:
        return None
    key = (w, context)
    if key in _MORPH_CACHE:
        return _MORPH_CACHE[key]
    cls: Optional[str] = None
    for c, sig, ctx in _morph_classes(sub):
        if ctx is not None and ctx != context:
            continue
        test = _MORPH_TESTS.get(sig)
        if test is not None and test(w)[0]:
            cls = c
            break
    _MORPH_CACHE[key] = cls
    return cls


def adjacency_evidence(agent, word: str) -> dict:
    """Introspection helper (for gates/demos): the SEMANTIC-nearness verdict for
    `word` IN ITS PROPER SLOT — {word, cls, nearness, nearest_member, signal, joined}.
    Evaluates each adjacency class in its own declared distributional context (so the
    naming-sense of `word` is measured as if it were in the marker slot). Does NOT
    mutate. (At parse time the distributional gate additionally requires the word to
    actually occupy that slot — a polysemous noun out of slot stays content.)"""
    sub, _, _ = _resolve(agent)
    w = str(word).lower().strip()
    best_cls, best_score, best_member = None, 0.0, None
    for _n, cls, anchors, thr, ctx in _class_anchors(sub):
        cls2, score, member = _compute_adjacency(sub, w, ctx)
        if cls2 is not None and score > best_score:
            best_cls, best_score, best_member = cls2, score, member
    return {"word": w, "cls": best_cls, "nearness": float(best_score),
            "nearest_member": best_member, "signal": "wordnet_path_similarity",
            "joined": best_cls is not None}


# --------------------------------------------------------------------------- #
#  CLAUSE -> SKELETON. Recognition tokenizer + held marker lexicon + POS verb head.
# --------------------------------------------------------------------------- #
def _skeleton_from_words(agent, words: list[str], *, speech_turn: bool = False) -> tuple[list, list, list]:
    """Turn a recognised word list into (skeleton, role_spans, marker_seq). The
    skeleton is the ordered list of single-element marker-predicate relations; the
    role spans are the content runs between markers; marker_seq pairs each skeleton
    class with its surface (the event VERB carries the predicate surface). Determiners
    and list conjunctions bound roles but never enter the skeleton. When NO skeleton
    marker fires (a bare S-V-O clause), the main VERB is found by the held POS faculty
    (`instruction_reading.is_verb_headed`) — the only construction whose marker is a
    content word, split so both role spans are non-empty.

    WAVE 1B — INTERROGATIVE / IMPERATIVE markers, all POSITIONAL (structural), never
    a lexical-only lookup that could clobber an existing class. The WH/AUXINV/OBL
    promotions additionally require `speech_turn=True` — set by read_clause ONLY
    when the input arrived as a WHOLE UTTERANCE STRING (a full communicative turn).
    A words-LIST input is a clause FRAGMENT handed in by the narrative descent
    (decompose_sentence / read_text regions / the parity capture), where a
    clause-initial copula is normally a SUBJECT-ELIDED coordination ('[the ass] was
    highly enchanted') and never subject-aux inversion — the grammatical licensor of
    inversion (a subject to invert around, in a root clause) only exists at the
    utterance grain. This is an I/O-boundary fact about what the input IS (turn vs
    fragment), not a semantic decision:
      · WH: a REL-class word (which/who/whom/whose/where), or a held `wh_fronting`
        form (what/when/why/how — kept OUT of the marker lexicon because they are
        common embedded complementizers mid-clause), promotes to WH iff at the true
        clause-initial boundary — a relativizer/subordinator can never open a matrix
        clause with nothing before it.
      · AUXINV (subject-aux inversion): a COP word, or a held `inversion_aux` word
        (do/does/did/can/could/will/...), promotes to AUXINV iff at the boundary —
        nothing precedes it, i.e. the aux fronts its subject. An ordinary mid-clause
        aux/cop ('the fox WILL return') is never touched.
      · OBL: once a WH or AUXINV marker has fired in this clause (`q_marker`), a
        held preposition (`_PP_PREPS`) becomes the OBL skeleton marker, splitting its
        object off as the oblique/focus role. Gated on already being inside a
        question skeleton, so an ordinary declarative PP ('into the pitcher') is
        never touched.
      · VERB_IMP (imperative): when the whole clause carries NO marker at all (the
        existing bare-S-V-O fallback below also finds nothing), and the FIRST token
        is confidently verb-primary and uninflected — the grammatical signature of
        English imperative mood (a declarative always has an overt subject before
        its finite verb). speech_turn-gated like the rest: a narrative fragment's
        bare verb ('stop' inside a fable clause split) is reported/quoted action at
        the fragment grain, and the frozen parity corpus fixes its reading as
        no-skeleton — only a whole chat turn is a directive TO the reader."""
    sub, _, _ = _resolve(agent)
    lex = _marker_lexicon(sub)
    markers: list = []
    roles: list = []
    cur: list = []
    content: list = []   # recognized content words in order (no join/split round-trip)
    _of_precedence_simple = _clause_is_simple_svo(words)  # see _clause_is_simple_svo —
        # computed once per clause; the OF finite-verb-precedence guard below only
        # fires on a genuinely single-finite-verb clause.
    prev_cls: Optional[str] = None
    last_tok_cop = False  # the IMMEDIATELY-preceding consumed token was a copula —
                          # the TRUE predicate slot for a passive participle ('is
                          # EVICTED'), distinct from `prev_cls=="COP"` which survives
                          # intervening DET glue ('is A deserted location', where
                          # 'deserted' is a prenominal adjective, NOT a passive).
    q_marker = False      # a WH or AUXINV has already fired in this clause
    # `at_boundary` is the TRUE clause-initial-position test — deliberately NOT
    # `not cur`: a determiner used PRONOMINALLY as the subject itself ('THIS is a
    # test') is absorbed as DET glue without ever touching `cur`, so `cur` alone
    # would still read "empty" once the copula is reached and wrongly fire AUXINV.
    # `at_boundary` tracks "nothing at all has occupied this clause position yet
    # (neither content nor a glued-away word)" and resets True only when a skeleton
    # marker just fired (the position right after a fronted wh-word, where a fronted
    # aux is expected) — never merely because `cur` happens to be empty.
    at_boundary = True
    for i, w in enumerate(words):
        wl = w.lower()
        prev_cop = last_tok_cop            # copula was the immediately-prior token?
        last_tok_cop = False               # updated per disposition below
        c = lex.get(wl)
        if c is None:
            # an unrecognised word may COLLAPSE into a marker-class by ADJACENCY
            # (semantic nearness to the class members AND the class's distributional
            # slot) — the class-learning path: a new designation surface
            # (termed/dubbed/...) in the post-copular slot joins DESIGNATE and is then
            # a skeleton marker, so the class-construction covers it (no new leaf). The
            # distributional context is the marker's current slot: post-copular iff the
            # previous skeleton marker was a copula.
            ctx = "post_copular" if prev_cls == "COP" else "other"
            c = _adjacency_place(agent, sub, w, ctx)
            if c is None:
                # MORPHOLOGY: a past-participle of a transitive verb IMMEDIATELY after
                # the copula ('is EVICTED') is a PASSIVE predicate (PPART), the
                # discriminator GAP B needs. The slot is STRICTER than adjacency's:
                # the participle must directly follow the copula (predicate slot) — a
                # prenominal participle after 'is A ...' ('a deserted location') has a
                # DET between and stays a content adjective. Held, graph-declared
                # (MarkerClass{morph_signal}); the test is WordNet. Runs after
                # adjacency so an existing class placement is unchanged.
                morph_ctx = "post_copular" if prev_cop else "other"
                c = _morph_place(agent, sub, w, morph_ctx)
                if c == "PPART":
                    # CONFIDENCE-GRADED COLLAPSE: passive vs stative is graded by the
                    # agent's held judgment. Below threshold (a stative-leaning
                    # balance — reciprocal context, psych verb) the reading COLLAPSES
                    # STATIVE (revert to a content adjective); at/above, it commits
                    # PASSIVE (a revisable belief read_clause records with its
                    # confidence). Same participle, add a by-phrase -> passive; add a
                    # reciprocal marker -> stative. The flip is one signal.
                    _prior, _thr = _passive_lean_policy(sub)
                    if _passive_confidence(sub, w, words, i) < _thr:
                        c = None
        # POSITIONAL reclassification (Wave 1B) — see docstring above and the
        # `at_boundary` note: this is the structural test for subject-aux/wh
        # inversion, not "cur is empty". Only at the SPEECH-TURN grain (see
        # docstring — a clause fragment's initial copula is subject-elided
        # coordination, not inversion).
        if speech_turn and at_boundary:
            if c == "REL" or (c is None and wl in _WH_FRONTING):
                c = "WH"
            elif c == "COP" or (c is None and wl in _INVERSION_AUX):
                c = "AUXINV"
            elif c == "DESIGNATE":
                # a DESIGNATE-class verb ('describe'/'define'/'classify'/...) can
                # only BE a designation POST-copula (the construction is
                # [[COP],[DESIGNATE]] — 'is described as'); clause-INITIAL with
                # nothing before it, it is the bare imperative verb ('Describe
                # yourself.'). Same positional-disambiguation status as REL→WH.
                c = "VERB_IMP"
        if q_marker and c is None and wl in _PP_PREPS:
            c = "OBL"
        # DESIGNATION GLUE: an AS/TO immediately following a DESIGNATE marker is part
        # of the designation frame ('described as', 'referred to as'), not a skeleton
        # marker — absorbed so the whole family shares the ONE [COP][DESIGNATE] shape.
        if c in ("AS", "TO") and prev_cls == "DESIGNATE":
            at_boundary = False
            continue
        # PARTITIVE GLUE: an OF immediately after a collective QUANTIFIER
        # ('hundreds OF protesters', 'thousands OF birds') is part of the
        # quantified noun phrase, NOT a skeleton OF marker -- absorbed (kept in
        # the role span) so 'hundreds of protesters were detained' reads as the
        # [COP][PPART] passive on head 'protesters', instead of an OF-attributive
        # that swallows the verb. Mirrors the DESIGNATION GLUE just above.
        # Guarded on the agent-held collective-QUANTIFIER MarkerClass, so absent
        # that taught class every 'of' is byte-identical.
        if c == "OF" and cur and lex.get(str(cur[-1]).lower()) == "QUANTIFIER":
            cur.append(w)
            content.append(w)
            prev_cls = None
            at_boundary = False
            continue
        # FINITE-VERB PRECEDENCE GLUE: an OF that competes with an ALREADY-SEEN
        # finite verb earlier in THIS SAME clause segment defers to it — the
        # finite verb heads the main predication, the OF is a nested-PP relation
        # inside the object NP ('He promoted the burning OF fossil fuels' keeps
        # 'promoted' as the clause's verb, via the bare-S-V-O fallback below,
        # instead of OF pre-empting it as the skeleton marker). Absorbed exactly
        # like the QUANTIFIER partitive glue just above (kept in the role span,
        # no new marker). Guarded on (a) the held OF MarkerClass{
        # yields_to_finite_verb} fact (`_of_yields_to_finite_verb`) — ablate it
        # and every 'of' reverts byte-identical to the pre-phase reading — and
        # (b) a genuine TIER-A finite verb in `cur` (the run since the LAST
        # skeleton marker fired — NOT the whole-clause-cumulative `content`,
        # which would reach across unrelated already-marked-off segments and
        # even across a mis-split multi-sentence run-on) BEFORE the token
        # immediately preceding 'of' (`_left_run_has_finite_verb(cur[:-1])`) —
        # the immediate pre-of head is the OF phrase's OWN governing noun/
        # gerund (never itself the competing verb, so it is excluded), meaning
        # a verbless genitive/partitive NP ('the son of a man') or a gerund-
        # headed subject ('the burning of fossil fuels harmed...') carries no
        # qualifying finite verb and is therefore UNCHANGED. (c) the clause
        # carries AT MOST ONE finite verb overall (`_of_precedence_simple`,
        # `_clause_is_simple_svo`) — a compound/coordinated multi-verb
        # sentence is left UNCHANGED too (see that function's docstring for
        # the audited regression this gate closes). (d) NO other skeleton
        # marker fires LATER in this clause (`_no_later_skeleton_marker`) —
        # a clause that still has its OWN downstream segmentation point is
        # left UNCHANGED (see that function's docstring for the audited
        # regression this gate closes: a real argument getting dragged across
        # a later copula/marker boundary). (e) NOT markers (no marker has
        # fired EARLIER in this clause either) — 'of' only glues away when it
        # is the clause's SOLE candidate skeleton marker altogether. An
        # earlier marker already anchors a multi-role construction (POSSESS/
        # COP/REL/...) that EXPECTS 'of' to supply its second role span; the
        # bare-S-V-O fallback this guard routes to only ever applies to a
        # totally UNMARKED clause, so an already-marked clause must keep its
        # own 'of' too ('a BEAR boasted very much OF his philanthropy' —
        # 'bear' already fired POSSESS; gluing 'of' away here starves the
        # possession construction of its second role and its has_property
        # predication is LOST entirely rather than merely reshaped — an
        # audited regression this gate closes).
        if (c == "OF" and cur and not markers and _of_yields_to_finite_verb(sub)
                and _of_precedence_simple
                and _no_later_skeleton_marker(lex, words, i)
                and _left_run_has_finite_verb(cur[:-1])):
            cur.append(w)
            content.append(w)
            prev_cls = None
            at_boundary = False
            continue
        if c in _GLUE:
            if c in ("AND", "OR") and cur:
                roles.append(" ".join(cur))
                cur = []
            at_boundary = False
            continue
        if c in _SKELETON:
            if cur:
                roles.append(" ".join(cur))
                cur = []
            markers.append((c, w))
            prev_cls = c
            # arm the passive-predicate slot ONLY after a FINITE copula (is/are/was/
            # were/am/'s) — a finite copula heads a main predicate ('a page IS
            # evicted'), so the following participle is the passive predicate. A
            # NON-finite copula (be/been/being) heads a perfect/progressive/infinitival
            # ADJUNCT ('having BEEN permitted to ...'), where the participle is embedded
            # and not the clause's predicate; firing there would misread embedded
            # participial adjuncts. All GAP-B targets are finite-copular passives.
            last_tok_cop = (c == "COP" and wl in _FINITE_COP)
            if c in ("WH", "AUXINV"):
                q_marker = True
                at_boundary = True
            else:
                at_boundary = False
        else:
            cur.append(w)
            content.append(w)
            prev_cls = None
            at_boundary = False
    if cur:
        roles.append(" ".join(cur))
    if not markers:
        # IMPERATIVE fallback (Wave 1B, speech_turn only — see docstring): no marker
        # anywhere in the clause, and the FIRST token is itself a verb-PRIMARY
        # reading (`_primary_pos` — the SAME tier-B signal `_find_main_verb` trusts
        # most) that is NOT a morphologically inflected form — a clause-initial bare
        # content verb with no subject, i.e. imperative mood. Deliberately tests
        # word0 DIRECTLY rather than calling `_find_main_verb` over the whole
        # clause: that ladder's tiers are scanned tier-by-tier ACROSS THE WHOLE SPAN
        # (every position tried at tier A/A2 before any position is tried at tier
        # B), so a LATER token that only LOOKS inflected via the weak '-ing'/morphy
        # heuristic ('reading', 'working', 'plates', 'left') can outrank the true
        # clause-initial imperative verb ('improve', 'stop', 'juggle') even though
        # the earlier word is the far stronger primary-verb reading — a real ladder
        # quirk this fallback must not inherit. Runs BEFORE the interior bare-SVO
        # scan at the speech-turn grain: that scan's loose `is_verb_headed` accepts
        # near-anything ('me' passes), so 'Tell ME about the moon' would otherwise
        # be hijacked into a subject-verb split at 'me' — but a turn whose FIRST
        # word is confidently verb-primary with no subject anywhere before it is
        # imperative-shaped by mood, which outranks a loose interior guess. A
        # words-list (narrative fragment) never takes this branch, so the interior
        # scan below is byte-identical for the whole frozen parity corpus. Reads
        # the RAW `words` (not the glue-filtered `content`): a PRONOMINAL object
        # the glue pass would otherwise eat ('Read THIS' — 'this' is DET-class glue
        # when it modifies a following noun, but here it IS the object) must
        # survive into `roles`.
        if speech_turn and words:
            w0 = str(words[0])
            if (not _inflected_verb(w0) and _primary_pos(w0) == "verb"
                    and ir.is_verb_headed(w0)):
                markers = [("VERB_IMP", words[0])]
                roles = [" ".join(str(x) for x in words[1:])] if len(words) > 1 else []
    if not markers:
        flat = content   # the recognized content words, in order — no whitespace re-split
        # Route the bare-S-V-O verb PICK through the SAME held-signal main-verb
        # ladder (`_find_main_verb`) the event-clause path already trusts, rather
        # than a crude "first is_verb_headed word from index 1" scan. The crude
        # scan uses the LOOSE `is_verb_headed` signal and stops at the FIRST
        # positional match, so a SUBJECT noun that merely carries a rare/archaic
        # verb SENSE ('company' can verb; so can 'crow') outranks the true finite
        # verb later in the clause ('funded') — 'The oil company funded a
        # renewable energy project.' misread 'company' as the predicate and
        # 'oil' as the whole subject. `_find_main_verb`'s Occam-ordered tiers
        # (inflected+verb-primary > any inflected > primary-verb > any verb-
        # headed-with-a-subject-before-it) prefer the finite/primary-verb
        # reading, so this is the SAME held POS signal already deciding verb
        # selection everywhere else in this file (event clauses, imperative
        # detection) — not a new heuristic.
        #
        # GUARD (measured against the frozen Aesop+Grimm CORPUS parity fixture,
        # not asserted a priori): `_find_main_verb` scans tier-by-tier ACROSS THE
        # WHOLE SPAN (every position tried at tier A before any position is tried
        # at tier B — the SAME quirk the imperative branch above already avoids
        # inheriting), so a LATER embedded-clause verb that happens to satisfy an
        # earlier tier can outrank an EARLIER word that is already the clause's
        # true finite verb but reads noun/adj-primary out of context ('saw' in
        # "he SAW them leaping" primary-tags noun — the tool sense — so tier A
        # skips it and tier A2's weak '-ing' heuristic grabs 'leaping' instead;
        # 'bark' in "they always BARK whenever..." is a verb-primary base form
        # with no inflection, so tier A2 jumps past it to an inflected verb
        # ('done') buried in a subordinate clause). The crude scan's pick is only
        # DISPLACED — never second-guessed — when it is itself weak by BOTH held
        # signals: not verb-primary AND not a genuinely inflected verb form (a
        # subject noun with a mere verb sense: company/crow/tailor/tom/cat/...),
        # or when it is a closed-class auxiliary the crude scan should never have
        # stopped on in the first place (had/did/do/can/...) — never when the
        # crude pick is already a real verb reading (lay/throw/bark, or an
        # inflected open-class verb like saw/caught/slipped), and only when the
        # ladder's replacement is ITSELF verb-primary (never a mistagged
        # participle like 'done', primary-tagged adj here). A THIRD-PERSON
        # PRONOUN immediately before the crude pick ('he saw', 'they lay') is an
        # extra held structural cue that shields it even when 'saw'/'lay' read
        # noun/verb-ambiguous by the primary_pos/inflection signals alone (a
        # pronoun subject can never head into a following noun-noun compound the
        # way 'oil company' or 'thirsty crow' can, so a pronoun-then-candidate
        # sequence is reliably subject+verb) — bypassed for a closed-class
        # auxiliary (still always displaceable). Falls back to the original scan
        # whenever the ladder finds nothing usable or the guard withholds — so no
        # clause the crude scan already reads correctly is ever regressed;
        # verified 0-diff on the CROW/DEFN/CONSTRUCT/VALIDATE gated groups and
        # improvement-only on the CORPUS oracle (see commit notes / the
        # reading-parity capture for the audited before/after list).
        def _crude_pick_is_weak(word: str, prev_word: Optional[str]) -> bool:
            if word in _AUX:
                return True
            if prev_word is not None and prev_word.lower() in _PRONOUN_FORMS:
                return False
            return _primary_pos(word) != "verb" and not _inflected_verb(word)

        ci = None
        for i in range(1, len(flat)):
            if ir.is_verb_headed(flat[i]) and flat[:i] and flat[i + 1:]:
                ci = i
                break
        vi = _find_main_verb(flat) if len(flat) > 1 else None
        if (vi is not None and flat[:vi] and flat[vi + 1:]
                and _primary_pos(flat[vi]) == "verb"
                and (ci is None or _crude_pick_is_weak(
                    flat[ci], flat[ci - 1] if ci > 0 else None))):
            markers = [("VERB", flat[vi])]
            roles = [" ".join(flat[:vi]), " ".join(flat[vi + 1:])]
        elif ci is not None:
            markers = [("VERB", flat[ci])]
            roles = [" ".join(flat[:ci]), " ".join(flat[ci + 1:])]
    skeleton = [[c] for c, _w in markers]
    return skeleton, roles, markers


# --------------------------------------------------------------------------- #
#  DECODE + WINNER read-off (the decode decides — this only reads its verdict).
# --------------------------------------------------------------------------- #
def _decode(agent, skeleton: list) -> dict:
    sub, _, _ = _resolve(agent)
    res = rf.compose_design_for_goal(sub, skeleton)
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(skeleton), "ordered_parts": []}
    return res


def _winner(res: dict) -> tuple[Optional[str], int]:
    """The construction the decode chose = the plan part with the greatest
    `shape_fit` (covers the most of the clause skeleton). Read off ShapeDecode's own
    ranking, never re-ranked here."""
    plan = res.get("plan") or []
    best_name, best_fit = None, -1
    for p in plan:
        try:
            fit = int(p.get("shape_fit", 0))
        except (TypeError, ValueError):
            fit = 0
        if fit > best_fit:
            best_fit, best_name = fit, p.get("part")
    return best_name, best_fit


def _construction_template(sub, name: str) -> dict:
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("name") == name and at.get("kind") == "construction":
            tmpl = at.get("ground_template")
            if tmpl:
                try:
                    return json.loads(tmpl)
                except Exception:
                    pass
    return {}


# --------------------------------------------------------------------------- #
#  GROUND — one construction-GENERAL routine, mode-dispatched by the template DATA.
# --------------------------------------------------------------------------- #
def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def _norm(span: str) -> str:
    # role spans are single-space-joined recognized words -> collapse to one concept
    # token by underscoring; no whitespace re-split (reading stays recognition-based).
    return span.lower().replace(" ", "_")


def _one_word(span: str) -> bool:
    # a single recognized token (no interior whitespace) -- a clean atom, not a
    # multi-word span needing head extraction. No whitespace .split().
    s = span.strip()
    return bool(s) and not any(c.isspace() for c in s)


def _ground_imperative(agent, marker_seq: list, roles: list) -> tuple[list, dict]:
    """Ground the IMPERATIVE (mode 'imperative'): predicate = the VERB_IMP marker's
    own surface; the implicit SUBJECT is the ADDRESSEE ('you' — the second-person
    slot, never present in the surface); the object is the clean head of the single
    remaining role (the clause tail), read via the SAME `_arg_head` faculty the
    event-clause path uses. Mechanical extraction, no decision: WHICH construction
    (imperative mood) is already the decode's verdict; this only fills its slots."""
    verbs = [w for c, w in marker_seq if c == "VERB_IMP"]
    verb = verbs[0].lower() if verbs else "acts_on"
    obj_span = roles[0] if roles else ""
    obj_head = _arg_head(agent, obj_span) if obj_span.strip() else None
    preds = [[verb, "you", obj_head]] if obj_head else [[verb, "you"]]
    return preds, {"addressee_role": "you", "focus": obj_head}


def _ground_question(agent, marker_seq: list, roles: list) -> tuple[list, dict]:
    """Ground a QUESTION (mode 'question', shared by wh_question / wh_question_oblique
    / polar_question): the inverted AUXINV marker leaves the subject and (for a
    do-support/modal aux) the real main verb JAMMED into roles[0] ('you know', 'you
    llm', 'you dance') — re-split it with the SAME held main-verb ladder
    (`_find_main_verb`) + head faculty (`_arg_head`) the event-clause path trusts,
    rather than a naive positional guess. When AUXINV was itself the copula (no
    separate main verb survives in roles[0], e.g. 'you llm'), the predicate defaults
    to 'is_a' (the same relation `definitional`/`designation` already use for a
    copular binding) and the remainder is the complement. roles[1], when present
    (the OBL-split oblique — 'about the moon'), is the wh-question's FOCUS and
    overrides any complement found inside the core span. Mechanical extraction over
    an already-decided construction; no decision here."""
    span = roles[0] if roles else ""
    toks = [t for t in span.split(" ") if t]
    vi = _find_main_verb(toks) if toks else None
    if vi is not None:
        subj_toks, verb_tok, obj_toks = toks[:vi], toks[vi], toks[vi + 1:]
        subject = _arg_head(agent, " ".join(subj_toks)) if subj_toks else "you"
        predicate = verb_tok.lower()
        obj_head = _arg_head(agent, " ".join(obj_toks)) if obj_toks else None
    else:
        subject = _arg_head(agent, toks[0]) if toks else "you"
        predicate = "is_a"
        obj_head = _arg_head(agent, " ".join(toks[1:])) if len(toks) > 1 else None
    oblique = roles[1] if len(roles) > 1 else ""
    focus = _clean_head(oblique) if oblique.strip() else obj_head
    if not subject:
        subject = "you"
    if focus:
        preds = [[predicate, subject, focus]]
    else:
        preds = [[predicate, subject]]
    return preds, {"addressee_role": subject if subject in _PRONOUN_FORMS else "you",
                   "focus": focus}


def _ground(agent, construction: str, template: dict, roles: list, marker_seq: list,
            *, write: bool = True) -> tuple[list, dict]:
    """Fill the winning construction's `ground_template` with the clause's role
    spans -> predications `[pred, arg0, arg1, ...]`. The mode is DATA (pair /
    pair_swap / enum_head_first / enum_head_last / question / imperative); `@verb`
    resolves the predicate to the event VERB surface. ONE routine for every
    construction — the per-construction behaviour is the template, never a Python
    branch. When `write`, each argument becomes a `Concept` node and each predication
    a typed relation edge (mechanical admissible graph mutation). Returns
    (predications, meta) — meta carries the construction's OWN `speech_act`/`polar`
    data (read straight off the template, never decided here) plus whatever
    `focus`/`addressee_role` the mode-specific grounder mechanically extracted
    (question/imperative only; every other mode leaves them None, additive)."""
    sub, _, _ = _resolve(agent)
    pred = template.get("pred") or construction
    mode = template.get("mode") or "pair"
    meta: dict[str, Any] = {"speech_act": template.get("speech_act") or "statement",
                            "polar": bool(template.get("polar", False)),
                            "focus": None, "addressee_role": None}
    if mode == "imperative":
        preds, extra = _ground_imperative(agent, marker_seq, roles)
        meta.update(extra)
    elif mode == "question":
        preds, extra = _ground_question(agent, marker_seq, roles)
        meta.update(extra)
    else:
        if pred == "@verb":
            verbs = [w for c, w in marker_seq if c == "VERB"]
            pred = verbs[0].lower() if verbs else "acts_on"
        elif pred == "@ppart":
            # PASSIVE: the predicate is the participle's BASE verb (WordNet morphy —
            # 'evicted' -> 'evict'); the surface SUBJECT (role 0) is the semantic
            # PATIENT/theme, the agent unspecified ('_'). Emits [verb, '_', patient],
            # a passive EVENT the situation model mints as an SmEvent (not an is_a
            # property) — the discriminator GAP B needs. (A by-phrase agent, when
            # present, is read separately and additively by
            # domains/media_analysis.py's write-gated annotator — see read_clause's
            # meaning_inference hook — rather than folded into this byte-parity-
            # frozen predication: the corpus contains multi-clause blobs where a
            # trailing BY belongs to an EMBEDDED reduced-relative participle, not
            # this predicate, so unconditionally filling role_ids[-1] here would
            # misattribute agency in exactly those cases — measured, not assumed.)
            parts = [w for c, w in marker_seq if c == "PPART"]
            pred = _participle_lemma(parts[0]) if parts else "acts_on"
        role_ids = [_norm(r) for r in roles if r.strip()]
        preds = []
        if mode == "passive_event" and role_ids:
            preds.append([pred, "_", role_ids[0]])
        elif mode in ("pair", "pair_swap") and len(role_ids) >= 2:
            a, b = role_ids[0], role_ids[1]
            preds.append([pred, b, a] if mode == "pair_swap" else [pred, a, b])
        elif mode == "enum_head_first" and len(role_ids) >= 2:
            head = role_ids[0]
            for item in role_ids[1:]:
                preds.append([pred, item, head])
        elif mode == "enum_head_last" and len(role_ids) >= 2:
            head = role_ids[-1]
            for item in role_ids[:-1]:
                preds.append([pred, item, head])
    if write and preds:
        _write_predications(sub, preds, construction)
    return preds, meta


def _record_reading_belief(sub, participle: str, confidence: float) -> None:
    """Hold the passive collapse as a REVISABLE belief — the FeatureBelief-shaped
    layer (value/source/confidence/revisable), applied to VOICE. Idempotent by
    participle: a later reading updates the confidence in place (the flip is one
    `set_attr`). Mechanical graph write; the JUDGMENT already happened. The belief
    node makes the collapse inspectable AND flippable: revising `value` to 'stative'
    (+ its confidence) is one cheap revision, exactly the revisable-belief law."""
    key = str(participle).lower()
    for n in sub.nodes("ReadingBelief"):
        at = sub.node(n)["attrs"]
        if at.get("feature") == "voice" and str(at.get("participle")).lower() == key:
            sub.set_attr(n, "confidence", float(confidence))
            sub.set_attr(n, "value", "passive")
            return
    sub.add_node("ReadingBelief", {
        "feature": "voice", "participle": key, "value": "passive",
        "confidence": float(confidence), "source": "passive_lean_judgment",
        "revisable": 1.0})


def _write_predications(sub, preds: list, construction: str) -> None:
    idx: dict[str, Any] = {}
    for n in sub.nodes("Concept"):
        nm = sub.node(n)["attrs"].get("name")
        if nm:
            idx.setdefault(nm, n)

    def concept(name: str):
        if name in idx:
            return idx[name]
        nid = sub.add_node("Concept", {"name": name, "surface": name.replace("_", " "),
                                       "source": "reading_collapse"})
        idx[name] = nid
        return nid

    native = getattr(sub, "_inner", sub)
    for p in preds:
        if len(p) < 3:
            continue
        rel, a, b = p[0], p[1], p[2]
        na, nb = concept(a), concept(b)
        if sub.has_edge(na, rel, nb):
            continue
        attrs = {"construction": construction, "source": "reading_collapse"}
        # admissibility-gated: try Γ first; a predication whose relation is not in
        # the admissibility vocabulary is recorded as an unchecked durable trace
        # (flagged gated=0) rather than dropped — the predication list is the
        # meaning; the edge is its durable trace.
        try:
            sub.add_edge(na, rel, nb, attrs)
        except Exception:
            try:
                native.add_edge_unchecked(_v(na), rel, _v(nb), {**attrs, "gated": 0})
            except Exception:
                pass


# --------------------------------------------------------------------------- #
#  LEARN — install a minted construction as a NEW codebook ShapeSignature.
# --------------------------------------------------------------------------- #
def _synthesise_template(skeleton: list, roles: list) -> dict:
    """A learned construction's role->predication template: the distinctive marker
    class (the last skeleton predicate — the one no held construction covered) names
    the relation, mode `pair`. Mechanical synthesis from the residual's own
    structure, not a hand-authored rule."""
    label = "related_to"
    if skeleton:
        label = str(skeleton[-1][0]).lower()
    return {"pred": label, "mode": "pair"}


def _install_construction(agent, skeleton: list, roles: list) -> dict:
    """Install the minted skeleton as a NEW `ShapeSignature{kind:'construction'}` and
    bump `codebook_epoch` (arms `sd_redecode`). `grow_part_library`'s own install +
    epoch-bump idiom, for a reading construction. Idempotent by content key."""
    sub, _, ag_node = _resolve(agent)
    key = json.dumps(skeleton)
    name = "learned_" + "_".join(s[0] for s in skeleton).lower()
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == "construction" and at.get("signature") == key:
            return {"installed": False, "name": at.get("name"), "reason": "already held"}
    tmpl = _synthesise_template(skeleton, roles)
    sub.add_node("ShapeSignature", {"name": name, "kind": "construction",
                                    "signature": key, "learned": 1.0,
                                    "ground_template": json.dumps(tmpl)})
    if ag_node is not None:
        cur = sub.node(ag_node)["attrs"].get("codebook_epoch") or 0.0
        sub.set_attr(ag_node, "codebook_epoch", float(cur) + 1.0)
    return {"installed": True, "name": name, "template": tmpl, "signature": key}


# --------------------------------------------------------------------------- #
#  IN-SITU DEFINITION (appositive 'X, a Y, ...' / parenthetical 'X (a Y) ...').
#
#  ADDITIVE, write-gated (called only from read_clause's existing write=True
#  block, alongside the meaning_inference annotators — see that block's own
#  docstring precedent: "OFF the byte-parity path... the frozen parity capture
#  always calls read_clause with write=False"). This NEVER touches
#  `comprehend_text._recognise_words`/`_recognise_regions` or the standard
#  `words` list every construction's skeleton is built from — it builds a
#  SEPARATE, boundary-preserving word stream from the clause's OWN comma/paren
#  regions and hands it to the SAME collapse pipeline (`_skeleton_from_words` +
#  `_decode`/`_winner` + `_construction_template` + `_ground`, all reused
#  UNCHANGED) every other construction already goes through. So the frozen
#  reading-parity corpus (whose capture always tokenises via the untouched
#  `_recognise_words` and calls `read_clause` with a pre-tokenised LIST,
#  skipping this string-only path entirely) is BYTE-IDENTICAL through this
#  addition.
#
#  THE DECISION — whether a comma/paren-flanked span IS an in-situ
#  definition — is the ShapeDecode collapse's, over the TAUGHT
#  `appositive_definition` / `parenthetical_definition` ShapeSignatures
#  (seeds/reading_constructions.json, authored via `domains.teach.teach`).
#  This module only recognises the MECHANICAL FACT a boundary rests on — is
#  the region it flanks DET-led? — via the SAME held `MarkerClass` lookup
#  `_skeleton_from_words` already performs on every word — and encodes that
#  fact as the boundary token's OWN class (`BOUND_COMMA_DEF`/`BOUND_PAREN_DEF`
#  vs an unrecognised plain boundary, which falls through as inert content).
#  A comma-appositive with no DET-led span ('the crow, tired and hungry,
#  flew') never emits a DEF-classed boundary, so the taught construction
#  offers ShapeDecode zero coverage and never fires — the GATING is the
#  decode's, not a Python if/else on what the clause means.
# --------------------------------------------------------------------------- #
def _region_is_det_led(sub, region: list) -> bool:
    """Mechanical graph read: does `region` (a region word-list) open with a
    held DET-class word? The SAME `_marker_lexicon` lookup `_skeleton_from_words`
    performs on every word already — not a new decision."""
    if not region:
        return False
    return _marker_lexicon(sub).get(str(region[0]).lower()) == "DET"


# Synthetic boundary tokens — never producible by `_recognise_words`/
# `_recognise_regions` (real text), so they can never collide with a genuine
# recognised word. Inserted directly as list elements (bypassing lattice
# decode entirely); their meaning is purely their taught MarkerClass.
_BOUND_COMMA_PLAIN_TOK = "‹bound_comma›"
_BOUND_COMMA_DEF_TOK = "‹bound_comma_def›"
_BOUND_PAREN_PLAIN_TOK = "‹bound_paren›"
_BOUND_PAREN_DEF_TOK = "‹bound_paren_def›"


def _boundary_words(sub, regions: list, plain_tok: str, def_tok: str) -> list:
    """Interleave `regions` (region word-lists, comma- or paren-delimited) with
    one boundary token between each consecutive pair. A boundary is classed
    DEF (`def_tok`) iff an INTERIOR neighbour region (never the first or last —
    the sentence's own leading subject/trailing tail never triggers this on
    its own) is DET-led (`_region_is_det_led`); otherwise it is the PLAIN token
    (unrecognised by any taught MarkerClass, so `_skeleton_from_words` folds it
    into ordinary content — inert). Mechanical per-boundary classification only
    (the same status as `_skeleton_from_words`'s own per-word lookup); WHICH
    construction (if any) grounds the resulting skeleton is entirely
    `_decode`'s call."""
    n = len(regions)
    out: list = []
    for i, reg in enumerate(regions):
        if i > 0:
            left_def = 0 < (i - 1) < n - 1 and _region_is_det_led(sub, regions[i - 1])
            right_def = 0 < i < n - 1 and _region_is_det_led(sub, regions[i])
            out.append(def_tok if (left_def or right_def) else plain_tok)
        out.extend(reg)
    return out


_INSITU_DEFINITION_FORMS = (
    # (regions-getter, plain boundary token, DEF boundary token, construction name)
    ("comma", _BOUND_COMMA_PLAIN_TOK, _BOUND_COMMA_DEF_TOK, "appositive_definition"),
    ("paren", _BOUND_PAREN_PLAIN_TOK, _BOUND_PAREN_DEF_TOK, "parenthetical_definition"),
)


def _ground_insitu_definition(agent, out: dict, raw_text: str, *, write: bool) -> None:
    """Ground an in-situ appositive/parenthetical definition (see module note
    above) and EXTEND `out['predications']` with whatever it grounds, so the
    meaning_inference write-gated annotators called immediately after this (in
    read_clause) see it and `infer_sense_from_definition` fires unmodified. A
    no-op (no predications added) when the clause has no such flanked span, or
    when the decode does not select one of the two taught constructions."""
    sub, _, _ = _resolve(agent)
    for kind, plain_tok, def_tok, cname in _INSITU_DEFINITION_FORMS:
        regions = (ct._recognise_regions(agent, raw_text) if kind == "comma"
                   else ct._paren_regions(agent, raw_text))
        if not regions or len(regions) < 3:
            continue
        bwords = _boundary_words(sub, regions, plain_tok, def_tok)
        skeleton, roles, marker_seq = _skeleton_from_words(agent, bwords, speech_turn=False)
        if not skeleton:
            continue
        res = _decode(agent, skeleton)
        name, fit = _winner(res)
        if name != cname or fit <= 0:
            continue
        template = _construction_template(sub, name)
        preds, _meta = _ground(agent, name, template, roles, marker_seq, write=write)
        if preds:
            out["predications"].extend(preds)


# --------------------------------------------------------------------------- #
#  READ ONE CLAUSE — the whole loop: decode -> (learn if novel) -> ground.
# --------------------------------------------------------------------------- #
def read_clause(agent, clause: str, *, write: bool = True, learn: bool = True) -> dict:
    """Read one clause by COLLAPSE. Returns {clause, skeleton, roles, construction,
    predications, learned, residual_before, minted, note, speech_act, focus,
    addressee_role, polar}. WHICH construction is the decode's verdict; a novel
    construction is MINTED then LEARNED then grounds.

    speech_act/focus/addressee_role/polar (Wave 1B) are ADDITIVE fields: every
    pre-existing construction defaults speech_act='statement' (declaratives are
    byte-identical — these are new keys, no existing key's value changes), and only
    the new question/imperative constructions set speech_act='question'/'instruction'
    via their OWN ground_template data (never a Python decision keyed on construction
    name). The one thin I/O-boundary fallback CLAUDE.md explicitly permits: when the
    ORIGINAL clause string ends '?' but the winning construction is structurally a
    statement (a declarative-order tag/fragment question the marker skeleton alone
    cannot distinguish from a statement — 'The sky is blue?'), speech_act stays/
    becomes 'question' from the surface mark alone; the mark is a corroborating
    SIGNAL only — it can never promote the construction to instruction, and it never
    overrides a structural verdict (question/instruction always wins over it).

    Input grain: a STRING is a whole SPEECH TURN — the interrogative/imperative
    marker promotions apply, and a colon splits the matrix clause from its `payload`
    ('Read this: the cat sat.'). A words-LIST is a narrative clause FRAGMENT (the
    decompose/descent/parity-capture path) and reads exactly as before Wave 1B."""
    ensure_codebook(agent)
    is_turn = isinstance(clause, str)
    ends_q = is_turn and clause.strip().endswith("?")
    payload: Optional[str] = None
    if isinstance(clause, (list, tuple)):
        words = list(clause)
    else:
        text = str(clause)
        # SPEECH-TURN COLON SEGMENTATION (mechanical, the same status as
        # _split_sentences' terminal-punctuation scan): a colon in a whole
        # utterance separates the matrix clause from its PAYLOAD ('Read this: the
        # cat sat.' — the directive is the pre-colon clause; what follows is the
        # complement content, surfaced additively as `payload`, never flattened
        # INTO the matrix clause's words as if one clause).
        ci = text.find(":")
        if ci > 0 and text[ci + 1:].strip():
            payload = text[ci + 1:].strip()
            text = text[:ci]
        words = ct._recognise_words(agent, text)
    skeleton, roles, marker_seq = _skeleton_from_words(agent, words, speech_turn=is_turn)
    out: dict[str, Any] = {"clause": clause if isinstance(clause, str) else " ".join(words),
                           "skeleton": skeleton, "roles": roles, "learned": False,
                           "minted": False, "predications": [], "construction": None,
                           "speech_act": "question" if ends_q else "statement",
                           "focus": None, "addressee_role": None, "polar": False}
    if payload is not None:
        out["payload"] = payload
    if write:
        # UNSAID ROLE (additive, OFF the byte-parity path — the frozen parity
        # capture always calls read_clause with write=False, so this never
        # runs there). Placed HERE — before the `if not skeleton:` gate below
        # and independent of `preds` — deliberately NOT reusing the existing
        # `if write and preds:` media_analysis hook further down: a
        # relational noun's own absent complement is a property of the
        # NOUN's local neighbourhood, not of whether the surrounding clause
        # happened to ground a full predication. "The crackdown continued."
        # has no VERB/COP the reader can construct at all (skeleton == []),
        # yet 'crackdown' still needs its 'on'-complement checked — the
        # preds-gated hook would never fire there. Local import: avoids a
        # module-load cycle (media_analysis imports reading_collapse). Mints
        # only a NEW node type (NominalMention); touches no existing
        # predication/event/decompose/read_clause/heads field. See
        # domains/media_analysis.py's UNSAID ROLE section for the full
        # architecture note.
        try:
            from domains import media_analysis as ma
            ma.annotate_relational_noun(agent, out, words)
        except Exception:
            pass
    if not skeleton:
        out["note"] = "no construction marker recognised (no copula/subordinator/verb) — no predication"
        out["residual_before"] = []
        return out

    res = _decode(agent, skeleton)
    residual = [list(r) for r in (res.get("residual") or [])]
    out["residual_before"] = residual
    name, fit = _winner(res)
    sub, _, _ = _resolve(agent)

    # LEARN only when NO held construction covers the skeleton (winner absent or
    # zero fit) — a genuinely novel construction. A PARTIAL cover (a construction
    # covers the head markers, a residual of glue/extra markers remains) is the
    # FAULTY/robust case: ground the nearest construction and FLAG the residual,
    # never mint (that would spuriously grow the codebook on every extra copula).
    if (name is None or fit <= 0) and learn:
        # NOVELTY: drive the sd loop (the mint DECISION is the seeded sd_* rules'),
        # then INSTALL the skeleton as a new construction + re-decode.
        ind = rf.induce_concern(agent, skeleton, name_hint="reading_" + "_".join(s[0] for s in skeleton).lower())
        out["minted"] = bool(ind.get("minted"))
        out["mint_axis"] = ind.get("axis_id")
        out["mint_residual_predicates"] = ind.get("residual_predicates")
        inst = _install_construction(agent, skeleton, roles)
        out["learned"] = bool(inst.get("installed")) or out["minted"]
        out["learned_construction"] = inst.get("name")
        res = _decode(agent, skeleton)  # re-decode against the grown codebook
        residual = [list(r) for r in (res.get("residual") or [])]
        out["residual_after"] = residual
        name, fit = _winner(res)

    out["construction"] = name
    out["shape_fit"] = fit
    out["residual"] = residual
    if name is None:
        out["note"] = "decode produced no covering construction (unlearnable skeleton)"
        return out
    template = _construction_template(sub, name)
    preds, meta = _ground(agent, name, template, roles, marker_seq, write=write)
    out["predications"] = preds
    if meta.get("speech_act") and meta["speech_act"] != "statement":
        out["speech_act"] = meta["speech_act"]
    out["focus"] = meta.get("focus")
    out["addressee_role"] = meta.get("addressee_role")
    out["polar"] = bool(meta.get("polar", False))
    if name == "passive":
        # REVISABLE COLLAPSE: the passive reading is held with the judgment's
        # confidence (statement != belief != truth). Recompute over the participle +
        # clause and record it; a borderline (~0.5) flips trivially when a signal
        # changes. On write, mint a `ReadingBelief` node (the FeatureBelief-shaped
        # revisable layer, applied to voice) so the flip is one cheap graph revision.
        parts = [(k, s) for k, s in marker_seq if k == "PPART"]
        if parts:
            surf = parts[0][1]
            try:
                pi = [str(x).lower() for x in words].index(str(surf).lower())
            except ValueError:
                pi = 0
            conf = _passive_confidence(sub, surf, words, pi)
            out["passive_confidence"] = conf
            out["voice"] = "passive"
            if write:
                _record_reading_belief(sub, surf, conf)
    if write and is_turn:
        # IN-SITU DEFINITION (appositive/parenthetical, additive — see that
        # function's own docstring for the full byte-parity argument). Only
        # reachable when `clause` arrived as a whole STRING (is_turn — the
        # ORIGINAL comma/paren punctuation is still in `text`); a words-LIST
        # clause fragment (decompose_sentence / the frozen parity capture)
        # never takes this branch. Mutates `out["predications"]` (== `preds`,
        # same list object) in place, so the `if preds:` guard below still
        # sees whatever it grounded.
        _ground_insitu_definition(agent, out, text, write=write)
    if write and preds:
        # INFER MEANING FROM CONTEXT (additive, OFF the byte-parity path — the
        # frozen parity capture always calls read_clause with write=False, so
        # this never runs there). Mechanical boundary application of seeded
        # SelectionalRestriction structure (slice 1), in-situ definitional
        # is_a structure (slice 2), AND derivational-morphology structure
        # (slice 3) to this reading's OWN predications; mints only NEW node
        # types (PredicationSlot/Predication/AffixCandidate/InferredSense) and
        # touches no existing predication/event/decompose/read_clause/heads
        # field. The DECISION (fold/abstain/supersede/relation-selection/
        # affix-join) is domains/meaning_inference.py's seeded rules, not this
        # call. Local import: avoids a module-load cycle (meaning_inference
        # imports reading_review, which imports this module).
        try:
            from domains import meaning_inference as mi
            mi.annotate_predication_slots(agent, out)
            mi.annotate_predication_facts(agent, out)
            mi.annotate_affix_candidates(agent, out)
            mi.annotate_relational_signatures(agent, out)
        except Exception:
            pass
        # AGENT DELETION (additive, OFF the byte-parity path — same gate as
        # meaning_inference above). A sibling try/except: a media_analysis
        # failure can never mask, or be masked by, meaning_inference's own.
        # Mints only a NEW node type (PassivePredication); touches no existing
        # predication/event/decompose/read_clause/heads field. See
        # domains/media_analysis.py for the full architecture note.
        try:
            from domains import media_analysis as ma
            ma.annotate_passive_predication(agent, out, marker_seq, roles)
        except Exception:
            pass
        # THIRD-PARTY ACTOR GOALS (additive, OFF the byte-parity path — same
        # gate as media_analysis above). A sibling try/except, one-line
        # handoff: a domains/actor_goals.py failure can never mask, or be
        # masked by, media_analysis's/meaning_inference's own. Mints only NEW
        # node types (ActorAction/ActorGoal); touches no existing
        # predication/event/decompose/read_clause/heads field. See
        # domains/actor_goals.py for the full architecture note.
        try:
            from domains import actor_goals as ag
            ag.annotate_actor_action(agent, out, marker_seq, roles)
        except Exception:
            pass
    flag = (" — flagged residual %s" % residual) if residual else ""
    out["note"] = ("recognised construction %r (fit %d) — grounded %d predication(s)%s"
                   % (name, fit, len(preds), flag))
    return out


# =========================================================================== #
#  ORDER-N DESCENT — the SAME collapse recursed into an argument's finer grain.
#
#  read_clause grounds a clause's TOP-LEVEL construction at ORDER 1. Some of the
#  arguments it fills carry RESIDUAL STRUCTURE — a coordinated LIST ("A, B and C"),
#  a compound causal TAIL (the [FROM],[OF] markers the winning construction left in
#  the residual), a nested clause. The sd loop's principle — "a remainder goes to
#  more detail; quanta are dynamic per dimension" — applies to reading: a structured
#  argument is a RESIDUAL that decodes at order N+1 into its constituents. The
#  descent REUSES the order-1 machinery (the marker lexicon, the glue split, the
#  construction's own relation) at a finer grain; it is NOT a new extractor and NOT
#  a cue-regex. The enum path's members are simply what the reader produces when it
#  recurses into an enumeration construction's list argument.
#
#  Order-N stops (a graph decision, not a regex): (a) max_order reached; (b) an
#  argument with NO residual structure (a plain nominal — no comma/AND list, no
#  sub-marker, passes the held nominal test) is NEVER recursed (no over-descent).
# --------------------------------------------------------------------------- #
_ENUM_MARKERS = {"INCL", "AS"}          # list-openers (includes/contains ... ; such AS)


def _clean_head(surface: str, language: str = "en") -> str:
    """The CLEAN nominal head of a (possibly participle-salad) role span, read off
    the held POS + lexical faculties — NOT a regex. Reproduces a genus/member as a
    clean nominal ('igneous_rock', 'calcium', 'lava'), not the flat order-1 NP
    ('aphanitic_fine-grained_extrusive_igneous_rock_formed'):

      1. drop trailing participle/adverb tokens (a verb/adv-primary tail like
         'formed' is a differentia predicate, not the head);
      2. drop a postmodifier PP — truncate at the first preposition that follows a
         noun ('lava rich in magnesium' -> head 'lava', not 'magnesium');
      3. the head is the rightmost token carrying a noun reading (OOV technical
         tokens count as nominal — the same convention consumption_quality.is_nominal
         uses);
      4. prefer the LONGEST held lexical compound ending at the head ('igneous rock'
         is a WordNet lemma -> 'igneous_rock'); else the bare head noun.

    All POS / compound lookups are held-faculty calls (consumption_quality._pos /
    _function_of + WordNet); no meaning decision lives here."""
    from domains import consumption_quality as cq
    toks = cq._tokens(surface)
    if not toks:
        return _norm(surface)

    def _primary(t: str) -> str:
        p = cq._pos(t, language)
        return p[0] if p else ""

    # (1) strip trailing participle / adverb / relativizer tokens ('formed' is a
    #     differentia predicate, a trailing 'that'/'which' a relativizer — neither is
    #     the head). Relativizer/determiner via the held function-word faculty.
    end = len(toks)
    while end > 1 and (_primary(toks[end - 1]) in ("verb", "adv", "conj", "det")
                       or cq._function_of(toks[end - 1], language)
                       in ("determiner", "conjunction")):
        end -= 1
    core = toks[:end]
    # (2) truncate a postmodifier PP: first preposition that has a preceding noun.
    seen_noun = False
    for i, t in enumerate(core):
        p = cq._pos(t, language)
        if "noun" in p or not p:
            seen_noun = True
        if seen_noun and cq._function_of(t, language) == "preposition":
            core = core[:i]
            break
    if not core:
        core = toks[:1]
    # (3) head = rightmost noun-reading token (OOV counts as nominal).
    head_i = None
    for i in range(len(core) - 1, -1, -1):
        p = cq._pos(core[i], language)
        if "noun" in p or not p:
            head_i = i
            break
    if head_i is None:
        head_i = len(core) - 1
    # (4) longest held lexical compound ending at the head, else the bare head.
    try:
        from nltk.corpus import wordnet as wn
        for start in range(0, head_i + 1):
            key = "_".join(core[start:head_i + 1])
            try:
                if wn.synsets(key):
                    return key
            except Exception:
                break
    except Exception:
        pass
    return core[head_i]


def _members_from_regions(agent, tail_regions: list) -> list:
    """Split a list-argument's regions into member surfaces. Each region is one
    comma-delimited group (the recogniser broke the list on the commas); within a
    region the held AND/OR glue splits conjuncts and DET glue is dropped. Each
    remaining word-run is one member surface. Reuses the SAME marker lexicon + glue
    split read_clause uses — the coordination structure decoded one order finer."""
    sub, _, _ = _resolve(agent)
    lex = _marker_lexicon(sub)
    members: list = []
    for reg in tail_regions:
        cur: list = []
        stop = False
        for w in reg:
            c = lex.get(w.lower())
            if c in ("COP", "REL"):
                # a copula or relativizer RESUMES the governing clause — the list has
                # ended ('...apatite may be present ...' / '...magnesium, which give
                # ...'): the member is what precedes it, the VP/relative clause is not
                # a list item. Flush + stop this region and the rest.
                stop = True
                break
            if c in ("AND", "OR"):
                if cur:
                    members.append(" ".join(cur))
                    cur = []
            elif c == "DET":
                continue
            else:
                cur.append(w)
        if cur:
            members.append(" ".join(cur))
        if stop:
            break
    return members


def _enumeration_members(agent, regions: list) -> tuple:
    """Locate the enumeration marker (INCL / AS) in the region stream and descend
    into its LIST argument. Returns (head_surface, [member_surface, ...]): the head
    is the nominal run just before the marker; the members are everything after it,
    split by the comma-region boundaries + AND/OR glue. Region-aware (so the commas
    the order-1 flatten discarded are recovered) — the descent that reproduces the
    enum members WITHOUT the enum cue-regex."""
    sub, _, _ = _resolve(agent)
    lex = _marker_lexicon(sub)
    # An enumeration OPENER is INCL (includes/contains/comprises/consists) or the
    # ADJACENT SUCH+AS collocation ('such as X, Y, Z'). A BARE 'as' is NOT an opener
    # — it is the comparative ('the same composition as gabbro'), or a tokenizer
    # artifact ('areas' -> 'are'+'as'). Require the AS to IMMEDIATELY follow a SUCH.
    # Rightmost opener wins.
    prev_cls = None
    marker_ri = marker_wi = None
    for ri, reg in enumerate(regions):
        for wi, w in enumerate(reg):
            cls = lex.get(w.lower())
            if cls == "INCL" or (cls == "AS" and prev_cls == "SUCH"):
                marker_ri, marker_wi = ri, wi
            prev_cls = cls
    if marker_ri is None:
        return None, []
    before = [w for w in regions[marker_ri][:marker_wi]
              if lex.get(w.lower()) not in _SKELETON and lex.get(w.lower()) not in _GLUE]
    head = " ".join(before) if before else ""
    tail_regions = [regions[marker_ri][marker_wi + 1:]] + [list(r) for r in regions[marker_ri + 1:]]
    members = _members_from_regions(agent, tail_regions)
    return head, members


def read_clause_order_n(agent, clause, *, max_order: int = 2, write: bool = True,
                        learn: bool = True) -> dict:
    """Read one clause by COLLAPSE at ORDER 1, then DESCEND into each argument that
    carries residual structure (the same collapse recursed, finer grain). Additive /
    opt-in: `read_clause` is unchanged; this wraps it and adds the order-N grounding.

    Descent kinds (each reuses order-1 machinery, no new extractor):
      · pair/pair_swap args -> re-grounded with CLEAN heads (`_clean_head`): the
        genus salad 'aphanitic_..._rock_formed' becomes the clean 'igneous_rock';
      · enumeration list arg -> `part_of(member, head)` per clean member, recovered
        from the comma-regions (`_enumeration_members`);
      · residual markers (the compound [FROM],[OF] tail the winning construction did
        not cover) -> `marker(role_i, role_{i+1})` predications, clean heads.

    Termination (graph decision, reported in `stop`/`depth`): max_order caps the
    descent; an argument with NO residual structure (a plain nominal) is not
    recursed. Returns the order-1 read plus order_n predications, members, compound
    tail, the clean genus, the depth reached and the stop reason."""
    ensure_codebook(agent)
    if isinstance(clause, (list, tuple)):
        words = list(clause)
        regions = [words]
    else:
        regions = ct._recognise_regions(agent, str(clause))
        words = [w for reg in regions for w in reg]
    base = read_clause(agent, words, write=False, learn=learn)
    skeleton, roles, marker_seq = base["skeleton"], base["roles"], None
    # recover marker_seq (read_clause does not surface it) via the same helper.
    _, _, marker_seq = _skeleton_from_words(agent, words)
    residual = base.get("residual") or []
    residual_classes = {r[0] for r in residual if r}
    name = base.get("construction")
    sub, _, _ = _resolve(agent)
    template = _construction_template(sub, name) if name else {}
    mode = template.get("mode") or "pair"

    out: dict[str, Any] = {
        "clause": base["clause"], "order1": {
            "construction": name, "predications": base.get("predications", []),
            "roles": roles, "skeleton": skeleton, "residual": residual},
        "order_n_predications": [], "members": [], "compound_tail": [],
        "genus": None, "depth": 1, "descended": [], "not_descended": [],
    }
    if not name:
        out["stop"] = "no construction at order 1 — nothing to descend"
        return out
    if max_order < 2:
        out["stop"] = "max_order<2 — order-1 only"
        return out

    order_n: list = []
    role_ids = [r for r in roles if r and r.strip()]

    # --- CLEAN pair heads (definitional genus, causal/comparative pair) ----------
    if mode in ("pair", "pair_swap") and len(role_ids) >= 2:
        pred = template.get("pred") or name
        if pred == "@verb":
            verbs = [w for c, w in (marker_seq or []) if c == "VERB"]
            pred = verbs[0].lower() if verbs else "acts_on"
        a_raw, b_raw = role_ids[0], role_ids[1]
        # the subject is a clean atom already; the complement (genus) is the salad.
        a = _norm(a_raw) if _one_word(a_raw) else _clean_head(a_raw)
        b = _clean_head(b_raw)
        cleaned = [pred, b, a] if mode == "pair_swap" else [pred, a, b]
        order_n.append(cleaned)
        out["descended"].append({"kind": "pair_clean_head", "role": b_raw, "head": b})
        if pred == "is_a":
            out["genus"] = b

    # --- ENUMERATION list descent -> one clean member per list item --------------
    # Fires whenever an enumeration marker (INCL / AS) is present — as the WINNING
    # construction ('a computer includes A, B, C') OR nested in the RESIDUAL of a
    # definitional/pair clause ('X is a Y that contains A and B', a relative-clause
    # enumeration). When the enum is the winner the head is the local nominal before
    # the marker; when it is nested in a residual the enumeration modifies the clause
    # SUBJECT (the 'that' relativizer refers back through the genus), so the head is
    # roles[0]. Same list descent either way.
    members_clean: list = []
    marker_classes = {c for c, _w in (marker_seq or [])}
    # enumeration present iff INCL, or the SUCH+AS pair (bare AS is comparative).
    enum_present = ("INCL" in marker_classes
                    or ("SUCH" in marker_classes and "AS" in marker_classes))
    enum_is_winner = mode in ("enum_head_first", "enum_head_last")
    if enum_present:
        head_surface, members = _enumeration_members(agent, regions)
        pred = "part_of"
        if enum_is_winner:
            pred = template.get("pred") or "part_of"
            head = _clean_head(head_surface) if head_surface else (
                _norm(role_ids[-1]) if mode == "enum_head_last" else _norm(role_ids[0]))
        else:
            # nested relative-clause enumeration: head = the clause subject.
            head = (_norm(role_ids[0]) if _one_word(role_ids[0])
                    else _clean_head(role_ids[0])) if role_ids else _clean_head(head_surface)
        for m in members:
            if not m.strip():
                continue
            # NO OVER-DESCENT: a plain nominal member is grounded, not recursed.
            if _is_real_nominal(m):
                mc = _clean_head(m)
                members_clean.append(mc)
                order_n.append([pred, mc, head])
            else:
                out["not_descended"].append({"kind": "non_nominal_member", "member": m})
        out["members"] = members_clean
        if members_clean:
            out["descended"].append({"kind": "enumeration_list", "head": head,
                                     "n_members": len(members_clean)})
            out["depth"] = 2

    # --- COMPOUND-TAIL descent -> ground the residual markers' predications -------
    if residual_classes and marker_seq:
        for k, (cls, _w) in enumerate(marker_seq):
            if cls not in residual_classes:
                continue
            if cls in _ENUM_MARKERS:        # an enum residual is the list descent, not a pair
                continue
            if k + 1 >= len(roles):
                continue
            left, right = roles[k], roles[k + 1]
            if not (left and right and left.strip() and right.strip()):
                continue
            lh, rh = _clean_head(left), _clean_head(right)
            rel = cls.lower()
            tail_pred = [rel, lh, rh]
            order_n.append(tail_pred)
            out["compound_tail"].append(tail_pred)
            out["descended"].append({"kind": "compound_tail_marker", "marker": cls,
                                     "pred": tail_pred})
        if out["compound_tail"]:
            out["depth"] = 2

    # dedup + record; a member/pair that is already a plain nominal is terminal.
    seen: set = set()
    uniq: list = []
    for p in order_n:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    out["order_n_predications"] = uniq
    out["stop"] = ("max_order=%d reached (order-N constituents are plain nominals — "
                   "no residual structure to descend further)" % max_order)
    if write and uniq:
        _write_predications(sub, uniq, "reading_collapse_order_n")
    return out


def _is_real_nominal(surface: str, language: str = "en") -> bool:
    """A member/argument is a REAL nominal (worth grounding, not a fragment) per the
    held POS faculty — reuse consumption_quality.is_nominal, the SAME leaf the enum
    path's nominal_filter uses. No new decision."""
    try:
        from domains import consumption_quality as cq
        return cq.is_nominal(surface, language)
    except Exception:
        return bool(surface and surface.strip())


def read_text_order_n(agent, text: str, *, write: bool = True, learn: bool = True,
                      max_clauses: int = 400, max_order: int = 2) -> dict:
    """Segment `text` (held recognition segmenter) and read each clause at ORDER N.
    Collects the order-N predications, the enumeration members (as part_of), and the
    is_a genera across the whole text — the reader-alone twin of the enum harvest."""
    ensure_codebook(agent)
    # Read at SENTENCE grain (commas stay inside a sentence so an enumeration list is
    # not pre-split): _recognise_regions breaks on every punctuation incl. commas,
    # which is too fine for the list descent. Sentence segmentation on terminal
    # punctuation is the SAME mechanical host split gap_driven_acquisition._first_
    # sentence uses; the WORD recognition inside each sentence stays recognition-based.
    sentences = _split_sentences(text)
    reads: list = []
    all_preds: list = []
    members: list = []
    genera: list = []
    seen_p: set = set()
    for s in sentences[:max_clauses]:
        if not s.strip():
            continue
        r = read_clause_order_n(agent, s, write=write, learn=learn, max_order=max_order)
        reads.append(r)
        for p in r.get("order_n_predications", []):
            key = tuple(p)
            if key not in seen_p:
                seen_p.add(key)
                all_preds.append(p)
                if p[0] == "part_of":
                    members.append(p[1])
                if p[0] == "is_a":
                    genera.append((p[1], p[2]))
    return {"reads": reads, "predications": all_preds, "members": members,
            "genera": genera, "n_predications": len(all_preds)}


_SENT_END = frozenset(".!?")


def _split_sentences(text: str) -> list:
    """Split text into sentences on strong terminal punctuation by a manual character
    scan (NO regex — reading stays recognition/scan-based): a '.', '!' or '?' followed
    by whitespace (or end) ends a sentence. Mechanical surface segmentation (no
    meaning), the coarse counterpart to _recognise_regions (which breaks on ALL
    punctuation incl. commas — too fine to keep an enumeration list intact)."""
    out: list = []
    buf: list = []
    n = len(text or "")
    for i, ch in enumerate(text or ""):
        buf.append(ch)
        if ch in _SENT_END and (i + 1 >= n or text[i + 1].isspace()):
            s = "".join(buf).strip()
            if s:
                out.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


# --------------------------------------------------------------------------- #
#  READ TEXT — recognition-based clause segmentation, then read each clause.
# --------------------------------------------------------------------------- #
def read_text(agent, text: str, *, write: bool = True, learn: bool = True,
              max_clauses: int = 40) -> dict:
    """Segment `text` into clauses by the held recognition segmenter
    (`comprehend_text._recognise_regions` — punctuation-delimited, NO whitespace
    regex) and read each by collapse. Returns {clauses:[read_clause...],
    predications:[deduped], constructions:{name:count}}."""
    ensure_codebook(agent)
    regions = ct._recognise_regions(agent, str(text))
    reads: list = []
    all_preds: list = []
    seen: set = set()
    constructions: dict[str, int] = {}
    for region in regions[:max_clauses]:
        if not region:
            continue
        r = read_clause(agent, region, write=write, learn=learn)
        reads.append(r)
        if r.get("construction"):
            constructions[r["construction"]] = constructions.get(r["construction"], 0) + 1
        for p in r.get("predications", []):
            key = tuple(p)
            if key not in seen:
                seen.add(key)
                all_preds.append(p)
    return {"clauses": reads, "predications": all_preds, "constructions": constructions,
            "n_predications": len(all_preds)}


# --------------------------------------------------------------------------- #
#  WIRING — a comprehension path extract_microtheory / consume_article call BESIDE
#  the enum parser (both feed the gate+teach; concepts deduped by name).
# --------------------------------------------------------------------------- #
def concepts_from_reading(agent, domain: str, source: dict, *, definition: str = "",
                          learn: bool = True) -> dict:
    """Read the source's definitional/enumeration/... prose by COLLAPSE and return
    concepts in `gap_driven_acquisition.extract_microtheory`'s own shape ({name,
    surface, definition}), so `consume_article`/`extract_microtheory` can merge them
    beside the enum-cue path. Each grounded predication argument that is a nominal
    role becomes a concept; the subject's genus (definitional is_a) is captured too."""
    text = (source or {}).get("text", "") or ""
    lead = (source or {}).get("lead") or definition or text[:400]
    read = read_text(agent, lead, write=False, learn=learn)
    concepts: list = []
    seen: set = set()
    for p in read["predications"]:
        for arg in p[1:]:
            if arg in seen or arg == domain:
                continue
            surface = str(arg).replace("_", " ")
            if 3 <= len(surface) <= 40:
                seen.add(arg)
                concepts.append({"name": arg, "surface": surface, "definition": lead})
    return {"domain": domain, "definition": lead, "concepts": concepts,
            "constructions": read["constructions"], "predications": read["predications"],
            "n_predications": read["n_predications"]}


# =========================================================================== #
#  CLAUSE DECOMPOSITION — order-N descent into a multi-clause sentence's CLAUSES.
#
#  read_clause / read_scope are tuned for a single SVO/copular clause. Real prose
#  packs several clauses per sentence (subordinate 'when ...', coordinate '... and
#  ...', participial 'Xing ..., ...', relative '... which ...'); the greedy
#  whole-sentence collapse GLOMS that structure into one underscore-joined blob
#  argument, so the real verbs never surface as a predication's relation. This is
#  the SAME order-N principle read_clause_order_n already applies to an argument's
#  finer grain ('a remainder goes to more detail'), lifted one level UP: a sentence
#  is a RESIDUAL that decodes into its CLAUSES at recognized boundaries.
#
#  The BOUNDARY is a MARKER-CLASS recognition (CLAUSE_LINK / IF / CAUSE_SUB / REL,
#  the comma regions the recogniser already produces, and an AND/OR joining two
#  verb-headed clauses) — NOT a hardcoded Python clause-splitter and NO regex. The
#  per-clause READING is the collapse: a copular/definitional clause routes through
#  the held read_clause (then its heads are cleaned); an EVENT clause has its main
#  verb found by the held is_verb_headed POS Term (+ WordNet inflection signal) and
#  its subject/object reduced to CLEAN NOMINAL HEADS by the held _clean_head faculty
#  (the ink twin of nominal_head_term). Additive: read_clause is UNCHANGED.
# --------------------------------------------------------------------------- #
from domains.reference_resolution import _PRONOUNS as _PRONOUN_FORMS   # closed-class pronoun forms

# closed-class reference facts (data, the same status as comprehend_text's
# _POLITENESS_MARKERS / function_word_reference's tables) the clause reader consults.
_PREP = {"OF", "TO", "FOR", "WITH", "BY", "FROM"}          # oblique-introducing marker classes
_STRUCTURING = _SKELETON - _PREP                           # construction-identity (clause-defining) markers
_CLAUSE_OPENERS = {"CLAUSE_LINK", "IF", "CAUSE_SUB", "REL"}  # marker classes that OPEN a dependent clause
# COMPLEMENTIZERS that open an embedded FINITE clause (a subject + finite verb
# follows). 'that' is the declarative complementizer; 'whether' the interrogative
# one ('asked him WHETHER he had had enough'). Both END the matrix clause so its
# main verb + subject stay unambiguous and the embedded clause reads on its own
# with its OWN subject — the embedded pronoun then never usurps the matrix subject
# slot. Detected by the SAME held main-verb test (`_is_complementizer_that`): a
# finite verb with a subject before it must follow, so 'whether' as a bare adjunct
# (rare) or 'that' as a determiner/relativizer does NOT split.
_COMPLEMENTIZERS = ("that", "whether")
_LEAD_CONNECTIVES = frozenset({"but", "and", "or", "so", "then", "yet", "nor",
                               "thus", "therefore", "however"})
_PP_PREPS = frozenset({"in", "into", "on", "onto", "at", "up", "upon", "with", "by",
                       "to", "of", "from", "for", "over", "under", "through", "across",
                       "about", "near", "around", "toward", "towards", "inside", "out",
                       "off", "down", "against", "between", "among", "without", "within"})
_DETERMINERS = frozenset({"a", "an", "the", "this", "that", "these", "those", "some",
                          "any", "each", "every", "his", "her", "its", "their", "my",
                          "your", "our", "no"})
_AUX = frozenset({"is", "are", "was", "were", "be", "been", "being", "am", "s",
                  "has", "have", "had", "do", "does", "did", "will", "would", "shall",
                  "should", "can", "could", "may", "might", "must", "not", "never",
                  "cannot"})
# SUBJECT-AUX INVERSION set (Wave 1B) -- do-support/modal/perfect aux only, NO
# copula (COP's own clause-initial position handles that) and NO negator (never
# fronts a clause). Fallback default; overwritten from the graph-resident
# ClosedClass{role:'inversion_aux'} node by _refresh_lexicon, same idiom as _AUX.
_INVERSION_AUX = frozenset({"do", "does", "did", "can", "could", "will", "would",
                            "shall", "should", "may", "might", "must",
                            "have", "has", "had"})
# WH-QUESTION FRONTING forms (Wave 1B), consulted POSITIONALLY only (see
# _skeleton_from_words) -- deliberately NOT MarkerClass forms (see the ClosedClass
# {role:'wh_fronting'} seed note): 'how'/'why'/'when'/'what' are common embedded-
# clause complementizers mid-sentence and must stay content there. Fallback
# default; overwritten from the graph by _refresh_lexicon, same idiom as _AUX.
_WH_FRONTING = frozenset({"what", "when", "why", "how"})


def _inflected_verb(word: str) -> bool:
    """The STRONG verb signal: WordNet morphy maps `word` to a DISTINCT verb lemma
    (dropped->drop, rose->rise, found->find, came->come) — a morphologically
    inflected verb, not a base-form noun that merely carries a verb sense
    (water/crow/rose-the-flower). Held-faculty (WordNet) read, no stemming table."""
    w = word.lower()
    try:
        from nltk.corpus import wordnet as wn
        lem = wn.morphy(w, "v")
        if lem and lem != w:
            return True
    except Exception:
        pass
    return w.endswith(("ing",)) and len(w) > 4


def _skip_leading_pp(low: list) -> int:
    """The index just past a LEADING prepositional phrase (a preposition + its
    (det/adj)* head noun), so the PP's noun object is not mistaken for the clause
    subject. 0 when the clause does not open with a preposition."""
    n = len(low)
    if not n or low[0] not in _PP_PREPS:
        return 0
    j = 1
    while j < n and (low[j] in _DETERMINERS or low[j] in _PP_PREPS):
        j += 1
    if j < n:
        j += 1                                      # consume the PP head noun
    return min(j, n)


def _primary_pos(word: str) -> str:
    """The token's PRIMARY POS tag ('' if OOV) via the held POS faculty."""
    try:
        from domains import consumption_quality as cq
        p = cq._pos(word, "en")
        return p[0] if p else ""
    except Exception:
        return ""


def _find_main_verb(flat: list) -> Optional[int]:
    """Index of the clause's MAIN verb in token list `flat`, or None. Held POS
    faculties only (is_verb_headed graph Term + WordNet inflection + primary-POS +
    closed-class aux/prep reference). Skips a LEADING prepositional phrase and
    auxiliaries/modals, then, in Occam order: (A) an INFLECTED verb (morphy maps to a
    distinct lemma — dropped/rose/tried/came); (B) a PRIMARY-verb content word
    (found/reach/drink/die — a base form whose first POS reading is verb); (C) any
    verb-headed non-aux word with a subject before it. The ladder keeps a noun-primary
    word with a mere verb SENSE (crow/water/rose-the-flower) from hijacking the
    predicate when a real verb is present."""
    n = len(flat)
    low = [str(w).lower() for w in flat]
    start = _skip_leading_pp(low)

    def _skippable(w):
        return w in _AUX or w in _PP_PREPS or w in _DETERMINERS

    # (A) inflected verb whose PRIMARY POS is verb -- the FINITE main verb wins over
    # an earlier inflected form that is a NOUN/adjective in situ ('as in uffish
    # thought he STOOD': 'thought' morphy-maps to 'think' but reads noun-primary here
    # (object of 'in'), 'stood' is the finite verb). Prefer the verb-primary one.
    for i in range(start, n):
        if _skippable(low[i]):
            continue
        if (_inflected_verb(low[i]) and _primary_pos(low[i]) == "verb"
                and ir.is_verb_headed(low[i])):
            return i
    # (A2) ANY inflected verb (a noun/adj-primary inflected form -- left/rested/rose,
    # which the POS faculty tags adj/noun-primary -- when no verb-primary inflected
    # verb is present). Byte-identical to the prior single (A) for a clause with
    # exactly one inflected verb; only a clause with TWO inflected verbs whose first
    # is non-verb-primary and a later one verb-primary changes (the thought/stood fix).
    for i in range(start, n):
        if _skippable(low[i]):
            continue
        if _inflected_verb(low[i]) and ir.is_verb_headed(low[i]):
            return i
    # (B) primary-POS verb.
    for i in range(start, n):
        if _skippable(low[i]):
            continue
        if _primary_pos(low[i]) == "verb" and ir.is_verb_headed(low[i]):
            return i
    # (C) any verb-headed word with a subject before it.
    for i in range(start, n):
        if _skippable(low[i]):
            continue
        if ir.is_verb_headed(low[i]) and any(not _skippable(low[k]) for k in range(start, i)):
            return i
    return None


def _arg_head(agent, span: str) -> str:
    """The CLEAN nominal head of a role span — a pronoun stays itself ('them'->them,
    the coref probe binds it), else the held _clean_head faculty reduces the phrase
    to its head noun ('the pitcher'->pitcher, 'a thirsty crow'->crow, 'some small
    pebbles'->pebbles) and a leading discourse connective ('but the pitcher'->pitcher)
    is dropped (it belongs to the coherence layer, not the entity)."""
    surface = str(span).replace("_", " ").strip()
    if not surface:
        return ""
    # the span is already-recognized words (underscore-joined, now spaced); tokenise
    # by the single-space delimiter (NOT a bare whitespace .split -- reading stayed
    # recognition-based upstream, this only re-splits a formed role span).
    toks = [t for t in surface.split(" ") if t]
    while toks and toks[0].lower() in _LEAD_CONNECTIVES:
        toks = toks[1:]
    # drop a leading prepositional phrase ('at last it' -> 'it', 'of thirst' -> ''):
    # the head of a role is its nominal, not the oblique PP that precedes it.
    pp = _skip_leading_pp([t.lower() for t in toks])
    if pp:
        toks = toks[pp:]
    for t in toks:
        tl = t.lower()
        if tl in _DETERMINERS:
            continue
        if tl in _PRONOUN_FORMS:
            return tl
        break
    if not toks:
        return ""
    return _clean_head(" ".join(toks))


def _clean_pred(agent, pred: list) -> Optional[list]:
    """Clean a [rel, a0, a1] predication's arguments to nominal heads. None if a
    head reduces to empty (nothing groundable)."""
    if not pred or len(pred) < 3:
        return None
    a0, a1 = _arg_head(agent, pred[1]), _arg_head(agent, pred[2])
    if not a0 or not a1:
        return None
    return [pred[0], a0, a1]


def _prenominal_states(span: str, head: str, language: str = "en") -> list:
    """The PRENOMINAL ADJECTIVES modifying the nominal `head` of a role `span` —
    each an implicit STATE the noun phrase asserts ('a thirsty crow' -> crow is
    thirsty; 'the narrow neck' -> neck is narrow). Recognised by the HELD POS
    faculty (consumption_quality._pos — an adjective-PRIMARY reading), NOT a
    hardcoded adjective list: a modifier before the head whose first POS tag is
    'adj' is a prenominal adjective. Returns `[["is_a", head, adj], ...]` — the
    SAME property-predication shape a copular clause ('the pitcher was high' ->
    is_a(pitcher, high)) produces, so situation_model_reader.ingest_predication's
    OWN property branch mints it as head.<adj>=1 (the state-mint is the graph, not
    a Python decision). Additive: this NEVER perturbs the role/entity extraction —
    it only surfaces the modifier the head-reduction would otherwise drop.

    Empty when the head is a pronoun (a bound pronoun has no surface modifiers) or
    the span carries no adjective-primary modifier before the head."""
    from domains import consumption_quality as cq
    surface = str(span).replace("_", " ").strip()
    if not surface or not head or head in _PRONOUN_FORMS:
        return []
    toks = [t for t in surface.split(" ") if t]
    while toks and toks[0].lower() in _LEAD_CONNECTIVES:
        toks = toks[1:]
    pp = _skip_leading_pp([t.lower() for t in toks])
    if pp:
        toks = toks[pp:]
    head_lead = str(head).split("_")[0].lower()
    states: list = []
    seen: set = set()
    for t in toks:
        tl = t.lower()
        if tl == head_lead:
            break                               # reached the head noun — stop
        if tl in _DETERMINERS or tl in _PRONOUN_FORMS or tl in _PP_PREPS:
            continue
        pos = cq._pos(tl, language)
        if pos[:1] == ["adj"] and tl not in seen:
            seen.add(tl)
            states.append(["is_a", head_lead, tl])
    return states


# --------------------------------------------------------------------------- #
#  ARGUMENT-STRUCTURE ROLE BINDING — role by CASE + AGREEMENT, not by position.
#
#  The clause reader must not assume SUBJECT-before-verb / OBJECT-after (SVO by
#  POSITION): archaic INVERTED verse mis-slots the subject ('the manxome foe he
#  sought' is OSV; 'rested he', 'Into the room walked a man' are VS). Grammatical
#  CASE is the held argument-structure signal: a NOMINATIVE pronoun (he/she/they,
#  reference_resolution._PRONOUNS['...']['case']=='subject') is the SUBJECT wherever
#  it sits; an ACCUSATIVE pronoun (him/her/them, case=='object') is the OBJECT (when
#  not itself the object of a preposition — 'to him' is oblique). Full nouns carry no
#  case, so their role stays POSITION-inferred (English default) — but the moment a
#  case signal fixes one core role, the OTHER full-noun argument fills the remaining
#  role even when FRONTED. No hardcoded inversion literal, no clause-position
#  assumption: the recognisers below key on POS + case only.
# --------------------------------------------------------------------------- #
def _clean_tok(w) -> str:
    """Strip leading/trailing NON-alphanumeric chars a recogniser left attached to a
    token (an em-dash/comma: 'sought-' -> 'sought'), preserving interior hyphens
    ('snicker-snack'). Mechanical surface cleanup — no meaning."""
    s = str(w).strip()
    a, b = 0, len(s)
    while a < b and not s[a].isalnum():
        a += 1
    while b > a and not s[b - 1].isalnum():
        b -= 1
    return s[a:b]


def _pron_case(w: str) -> Optional[str]:
    """The grammatical CASE of a pronoun surface ('subject'/'object'/'any') read off
    the held reference_resolution._PRONOUNS spec, or None if not a pronoun. The
    argument-structure case signal — closed-class data, the same status as the
    _PRONOUN_FORMS table the reader already consults."""
    spec = _PRONOUN_FORMS.get(str(w).lower())
    return spec.get("case") if isinstance(spec, dict) else None


# POS tags the held faculty (consumption_quality._pos) emits that CANNOT head or
# modify a noun phrase — an adverb / wh-word / verb / pronoun / function word. A
# content nominal reads 'noun' or 'adj' (the faculty tags many bare nouns 'adj', and
# an OOV coinage 'adj'/'') — so an NP-edge token is simply one whose primary tag is
# NOT one of these AND that is not a closed-class function word.
_NONHEAD_POS = frozenset({"adv", "verb", "pron", "article", "conj", "prep",
                          "det", "wh", "particle", "modal"})


def _heads_np(w: str) -> bool:
    """Can `w` be the RIGHT EDGE (head) of a fronted object DP? A content token
    (noun/adj/OOV per the held POS faculty), not an adverb/wh-word/pronoun/aux/
    preposition/determiner. This is the OSV discriminator: 'foe' (content) abuts the
    subject pronoun in 'the manxome foe he sought'; 'how' (adverb) abuts it in 'no
    matter how he tried' -> the latter is not an NP head, so no fronted object."""
    wl = str(w).lower()
    if (wl in _AUX or wl in _PP_PREPS or wl in _PRONOUN_FORMS
            or wl in _LEAD_CONNECTIVES or wl in _DETERMINERS):
        return False
    return _primary_pos(wl) not in _NONHEAD_POS


def _is_np_tok(w: str) -> bool:
    """A token that may sit inside a noun phrase (determiner / adjective / noun / OOV)
    — used to extend a fronted-object DP leftwards. Held POS faculty."""
    wl = str(w).lower()
    if wl in _AUX or wl in _PP_PREPS or wl in _PRONOUN_FORMS or wl in _LEAD_CONNECTIVES:
        return False
    if wl in _DETERMINERS:
        return True
    return _primary_pos(wl) not in _NONHEAD_POS


def _is_possessive_pronoun(low: list, i: int) -> bool:
    """Is the pronoun at `i` a possessive determiner rather than a core argument? 'her'
    is BOTH an object pronoun ('thanked her') and a possessive determiner ('her
    fortune') — the ONLY ambiguous form (his/its/their/my/your/our are determiner-only
    and not in the pronoun table). It is possessive iff it heads an NP: the next token
    is a noun/adjective (an NP continues) and NOT itself a determiner ('her a whistle'
    -> 'a' is a determiner, so 'her' is the recipient object, not possessive)."""
    w = low[i]
    if w not in _DETERMINERS:            # only determiner-form pronouns can be possessive
        return False
    j = i + 1
    return j < len(low) and low[j] not in _DETERMINERS and _heads_np(low[j])


def _core_case_pronoun(low: list, vi: int, case: str) -> Optional[int]:
    """Index of the first clause pronoun carrying grammatical `case` that is a CORE
    argument (NOT the object of a preposition — 'to him' / 'of them' is oblique — and
    NOT a possessive determiner — 'her fortune'). Returns the index or None.
    Position-free: the pronoun's CASE, not its slot, decides."""
    for i, w in enumerate(low):
        if i == vi:
            continue
        if _pron_case(w) == case:
            if i > 0 and low[i - 1] in _PP_PREPS:
                continue                       # oblique: object of a preposition
            if _is_possessive_pronoun(low, i):
                continue                       # possessive determiner, not an argument
            return i
    return None


def _fronted_object(agent, flat: list, low: list, subj_i: int, lo: int) -> tuple:
    """The FRONTED direct object of an OSV clause: the noun-headed DP IMMEDIATELY
    left-adjacent to the nominative subject pronoun at `subj_i` (search floor `lo`).
    Adjacency is the discriminator — 'the manxome foe he sought' fronts 'the manxome
    foe' (noun 'foe' abuts 'he'), while 'no matter how he tried' has the ADVERB 'how'
    abutting 'he' (not a nominal) -> no fronted object. Returns (span, head) or
    ('', '')."""
    j = subj_i - 1
    if j < lo or not _heads_np(low[j]):
        return "", ""
    start = j
    k = j - 1
    while k >= lo and _is_np_tok(low[k]):
        start = k
        if low[k] in _DETERMINERS:
            break                              # a determiner is the NP's left edge
        k -= 1
    span = " ".join(flat[start:j + 1])
    return span, _clean_head(span)


def _ditransitive_theme(agent, obj_toks: list) -> str:
    """The THEME (second object) head of a DOUBLE-OBJECT verb phrase
    'V NP_recipient NP_theme' ('gave her a whistle' -> theme 'whistle'; 'gave the
    dog her bread' -> theme 'bread'), or '' when the post-verbal material is not a
    double-object frame. The signal is a determiner-introduced NP with a recipient
    NP before it and NO preposition between the two verbs' objects: a preposition
    marks a PP goal/adjunct, so 'dropped them INTO the pitcher' is monotransitive +
    PP (NOT ditransitive) and yields ''. Held closed-class tables only (the SAME
    _DETERMINERS / _PP_PREPS the parser already consults) + the held _arg_head
    nominal reducer; ADDITIVE — it never perturbs the primary object, only recovers
    the theme the single-object read drops."""
    low = [str(w).lower() for w in obj_toks]
    for d in range(1, len(obj_toks)):
        if low[d] not in _DETERMINERS:
            continue
        # a preposition anywhere before the theme's determiner => a PP, not a
        # double-object frame (the crow's 'them into the pitcher' guard).
        if any(w in _PP_PREPS for w in low[:d]):
            return ""
        # the recipient run before the theme must carry a real nominal or pronoun,
        # not be pure glue (a bare determiner is not a recipient). A pronoun recipient
        # ('her'/'him'/'them') counts even though its surface doubles as a possessive
        # determiner form — it is the recipient object here, not a possessive.
        if not any(w in _PRONOUN_FORMS
                   or (w not in _DETERMINERS and w not in _AUX and w not in _PP_PREPS)
                   for w in low[:d]):
            return ""
        head = _arg_head(agent, " ".join(obj_toks[d:]))
        return head if head and head not in [str(w).lower() for w in obj_toks[:d]] else ""
    return ""


def _leading_adjunct(low: list, flat: list) -> tuple:
    """The full span + clean head of a FRONTED adjunct prepositional phrase (the
    opening preposition + det + adjective(s) + head noun), for the locative-inversion
    recogniser. Returns (end_index, head): end_index is the index of the first token
    AFTER the PP (so a pre-verb span WHOLLY consumed by the PP gives end_index >= the
    verb index -> no canonical subject), head is the PP's nominal head. (0, '') when
    the clause does not open with a preposition.

    A THOROUGH twin of _skip_leading_pp used ONLY on the inversion path: it consumes
    prenominal ADJECTIVES before the head ('down the DARK stair' -> whole PP), which
    the shallow _skip_leading_pp does not, so an adjective-modified fronted PP no
    longer leaks its head noun into the subject slot. _skip_leading_pp itself stays
    byte-identical (the SVO default reads it), so canonical prose is untouched. Held
    POS faculty only (primary-POS adjective test + _heads_np); no position assumption
    beyond 'a clause-initial preposition opens a PP'."""
    n = len(low)
    if not n or low[0] not in _PP_PREPS:
        return 0, ""
    j = 1
    while j < n and (low[j] in _DETERMINERS or low[j] in _PP_PREPS):
        j += 1
    while j < n and _primary_pos(low[j]) == "adj" and low[j] not in _PRONOUN_FORMS:
        j += 1
    if j < n and _heads_np(low[j]):
        return j + 1, _clean_head(" ".join(flat[1:j + 1]))
    return j, (_clean_head(" ".join(flat[1:j])) if j > 1 else "")


def _oblique_head(agent, flat: list, low: list, vi: int) -> str:
    """The nominal head of a POST-verbal prepositional-phrase complement/adjunct
    ('So rested he BY the Tumtum tree' -> 'tree'; 'Came whiffling THROUGH the tulgey
    wood' -> 'wood'), or '' when there is no post-verbal PP. Scans for the first
    _PP_PREPS token after the verb and reduces the NP it introduces to its clean head
    (an OOV coinage counts as a nominal, so a nonsense place-name still binds). Held
    faculties only; called ONLY on a genuinely INVERTED clause, so canonical prose is
    byte-identical (a canonical intransitive-with-PP clause never reaches it)."""
    n = len(low)
    for i in range(vi + 1, n):
        if low[i] in _PP_PREPS:
            tail = flat[i + 1:]
            return _clean_head(" ".join(tail)) if tail else ""
    return ""


def _oblique_prep_head(flat: list, low: list, vi: int) -> tuple:
    """(preposition, clean nominal head) of the FIRST post-verbal PP, or ('', '').
    The preposition is kept so the caller can read the PP's thematic role off the
    held VerbNet prep->role table (preposition_roles). Same first-PP scan as
    _oblique_head; a mechanical lexical read, no decision."""
    n = len(low)
    for i in range(vi + 1, n):
        if low[i] in _PP_PREPS:
            tail = flat[i + 1:]
            return low[i], (_clean_head(" ".join(tail)) if tail else "")
    return "", ""


def _animate_nominal(word: str) -> bool:
    """The reader's OWN WordNet knowledge: does `word` denote a WHOLE LIVING CREATURE
    — a noun.animal synset descended from chordate.n.01 / invertebrate.n.01, the SAME
    precise ancestry coref_entities._has_whole_animal_sense uses? This gates the
    thematic-oblique capture so an animate participant ('over the poor DOG', 'at the
    SPARROW') is registered but an inanimate adjunct ('with a little WATER', 'into
    the PITCHER') is NOT — keeping the crow byte-identical. A lexical reference read
    (a held WordNet lookup), the same status as _inflected_verb's morphy read; no
    graph-state conditional.

    SCOPE: whole-CREATURE only, NOT persons — because a person sense is unreliably
    polysemous at the surface ('pitcher'.n.01 is a baseball player; 'whip'.n.02 a
    party official), so admitting a first-sense-person would capture inanimate
    homonyms and perturb the crow. Person participants that appear only in an oblique
    PP are a documented residual, not yet captured here."""
    w = str(word).lower().strip()
    if not w:
        return False
    try:
        from nltk.corpus import wordnet as wn
        roots = (wn.synset("chordate.n.01"), wn.synset("invertebrate.n.01"))
        for s in wn.synsets(w, pos=wn.NOUN):
            if s.lexname() != "noun.animal":
                continue
            anc: set = set()
            for path in s.hypernym_paths():
                anc.update(path)
            if any(r in anc for r in roots):
                return True
    except Exception:
        return False
    return False


def _clause_graph_edge(sub, native, src, etype, tgt, attrs=None):
    """Add a clause-graph edge, falling back to an unchecked durable trace when the
    edge type is outside the admissibility vocabulary Γ (the SAME guarded-add idiom
    _write_predications uses). The clause-graph's `has_token` / `next` edges are
    structural scaffolding the event-role rules read, not semantic Γ relations."""
    try:
        sub.add_edge(src, etype, tgt, attrs or {})
    except Exception:
        try:
            native.add_edge_unchecked(_v(src), etype, _v(tgt), {**(attrs or {}), "gated": 0})
        except Exception:
            pass


def _event_clause_graph(agent, words: list, lex: dict):
    """PHASE-1 CLAUSE-GRAPH INGEST — adapter I/O, PURE TRANSLATION, no decision.

    Turn a recognised EVENT clause into the small graph the event-role RULES read: an
    `EventClause` hub + one `Token` node per cleaned word, carrying the HELD-FACULTY
    attrs the role ladder keys on, plus left→right `next` adjacency and clause→token
    `has_token` membership. EVERY attr is a mechanical held-faculty read — the SAME
    reads `_event_predication` performs today (consumption_quality._pos via
    `_primary_pos`, `ir.is_verb_headed`, `_inflected_verb`, `_pron_case`, the closed-
    class `_AUX`/`_PP_PREPS`/`_DETERMINERS`/`_PRONOUN_FORMS`/`_LEAD_CONNECTIVES`
    tables, `preposition_roles`, `_animate_nominal`, `_heads_np`/`_is_np_tok`) —
    precomputed here so the DECISION (which token fills which role) can move into
    graph data (Phase 2 rules over this graph). There is NO conditional over graph
    STATE here: the only branches are on the token's own held lexical/POS reads,
    exactly like the tokenizer. Returns the `EventClause` node id, or None for a
    verb-less clause (nothing to ground — the same early skip `_event_predication`
    takes when `_find_main_verb` is None)."""
    ensure_event_frames(agent)
    sub, native, ag_node = _resolve(agent)
    flat = [_clean_tok(w) for w in words if str(_clean_tok(w))]
    if not flat:
        return None
    low = [str(w).lower() for w in flat]
    vi = _find_main_verb(flat)
    lo = _skip_leading_pp(low)
    clause = sub.add_node("EventClause", {
        "text": " ".join(flat),
        "n_tokens": float(len(flat)),
        "main_verb_index": (float(vi) if vi is not None else -1.0),
        "main_verb": (low[vi] if vi is not None else ""),
        "pp_floor": float(lo),
        "has_verb": 1.0 if vi is not None else 0.0,
    })
    prev = None
    for i, w in enumerate(flat):
        wl = low[i]
        pos = _primary_pos(wl)
        attrs: dict[str, Any] = {
            "idx": float(i),
            "surface": str(w),
            "low": wl,
            "pos": pos,
            "is_verb": 1.0 if ir.is_verb_headed(wl) else 0.0,
            "inflected_verb": 1.0 if _inflected_verb(wl) else 0.0,
            "verb_primary": 1.0 if pos == "verb" else 0.0,
            "is_aux": 1.0 if wl in _AUX else 0.0,
            "is_prep": 1.0 if wl in _PP_PREPS else 0.0,
            "is_det": 1.0 if wl in _DETERMINERS else 0.0,
            "is_lead_connective": 1.0 if wl in _LEAD_CONNECTIVES else 0.0,
            "is_pronoun": 1.0 if wl in _PRONOUN_FORMS else 0.0,
            "is_adj": 1.0 if pos == "adj" else 0.0,
            "is_animate": 1.0 if _animate_nominal(wl) else 0.0,
            "heads_np": 1.0 if _heads_np(wl) else 0.0,
            "is_np_tok": 1.0 if _is_np_tok(wl) else 0.0,
            "is_main_verb": 1.0 if (vi is not None and i == vi) else 0.0,
        }
        case = _pron_case(wl)
        if case:
            attrs["case"] = case
        if wl in _PP_PREPS:
            role = pr.preposition_role(wl, "en")
            if role is not None:
                attrs["prep_role"] = role
        tok = sub.add_node("Token", attrs)
        _clause_graph_edge(sub, native, clause, "has_token", tok, {"idx": float(i)})
        if prev is not None:
            _clause_graph_edge(sub, native, prev, "next", tok)
        prev = tok
    if ag_node is not None:
        _clause_graph_edge(sub, native, ag_node, "has_clause", clause)
    if vi is not None:
        _precompute_role_candidates(agent, sub, clause, flat, low, vi, lo)
    return clause


def _precompute_role_candidates(agent, sub, clause, flat, low, vi, lo) -> None:
    """Precompute — MECHANICALLY, via the SAME held faculties `_event_predication`
    calls — every candidate role-filler the role ladder chooses among, and store them
    as `EventClause` attrs. This is PURE FACULTY APPLICATION over spans defined by
    faculty-read boundaries (`vi`/`lo`/case-pronoun indices/`_leading_adjunct`): a
    lexical/POS/WordNet read the same status as the tokenizer, NOT a decision. The
    DECISION — which candidate WINS — is the graph-native role-assignment RULES over
    these attrs (`_ground` mode:event reads the resolved roles). Reusing the SAME
    helpers guarantees each candidate is byte-identical to what the Python ladder
    would compute for the same span, so the rules only have to reproduce the SELECTION
    cascade, not the head reduction."""
    subj_toks = flat[lo:vi]
    obj_toks = flat[vi + 1:]
    subj_span = " ".join(subj_toks)
    obj_span = " ".join(obj_toks)
    def_subj = _arg_head(agent, subj_span) if subj_toks else ""
    def_obj = (_arg_head(agent, obj_span)
               if (obj_toks and low[vi + 1] not in _PP_PREPS) else "")
    nom_i = _core_case_pronoun(low, vi, "subject")
    acc_i = _core_case_pronoun(low, vi, "object")
    fronted_span, fronted_head = (_fronted_object(agent, flat, low, nom_i, lo)
                                  if nom_i is not None else ("", ""))
    lead_pp = bool(low and low[0] in _PP_PREPS and obj_toks)
    adj_end, pp_head = _leading_adjunct(low, flat) if lead_pp else (0, "")
    pp_span = " ".join(flat[:adj_end]) if lead_pp else ""
    inv_subj_head = _arg_head(agent, obj_span) if lead_pp else ""
    obl_inv_head = _oblique_head(agent, flat, low, vi)
    obl_prep, obl_canon_head = _oblique_prep_head(flat, low, vi)
    obl_role = pr.preposition_role(obl_prep, "en") if obl_prep else None
    dtrans_theme = _ditransitive_theme(agent, obj_toks) if obj_toks else ""
    attrs = {
        "verb": low[vi],
        "subj_span": subj_span,
        "obj_span": obj_span,
        "def_subj": def_subj,
        "def_obj": def_obj,
        "nom_idx": float(nom_i) if nom_i is not None else -1.0,
        "nom_surface": (low[nom_i] if nom_i is not None else ""),
        "acc_idx": float(acc_i) if acc_i is not None else -1.0,
        "acc_surface": (low[acc_i] if acc_i is not None else ""),
        "fronted_span": fronted_span,
        "fronted_head": fronted_head,
        "lead_pp": 1.0 if lead_pp else 0.0,
        "adj_end": float(adj_end),
        "pp_head": pp_head,
        "pp_span": pp_span,
        "has_post_verb": 1.0 if (vi + 1 < len(low)) else 0.0,
        "post_verb_is_prep": 1.0 if (vi + 1 < len(low) and low[vi + 1] in _PP_PREPS) else 0.0,
        "inv_subj_head": inv_subj_head,
        "obl_inv_head": obl_inv_head,
        "obl_prep": obl_prep,
        "obl_canon_head": obl_canon_head,
        "obl_role_ok": 1.0 if obl_role is not None else 0.0,
        "obl_animate": 1.0 if (obl_canon_head and _animate_nominal(obl_canon_head)) else 0.0,
        "dtrans_theme": dtrans_theme,
        # inversion applies when the leading PP consumes the whole pre-verb span
        # (adj_end >= vi) — the "no canonical subject" signal (Python `adj_end >= vi`).
        "inversion_applies": 1.0 if (lead_pp and adj_end >= vi) else 0.0,
    }
    for k, v in attrs.items():
        sub.set_attr(clause, k, v)


def _frame_truthy(v) -> bool:
    """A guard Term's verdict is truthy — True, or a non-zero number. Mechanical."""
    if v is True:
        return True
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v != 0
    return False


def _load_event_frames(sub) -> list:
    """Read the VerbFrame CODEBOOK out of the graph, priority-ascending. Mechanical
    graph query — no decision (the decision content is the frames' own guard/effect
    Terms). Grown role frames (Phase 3, `codebook == 'event_roles'`) join here
    automatically, so a minted role decodes alongside the seeded ladder."""
    frames = []
    for n in sub.nodes("VerbFrame"):
        at = sub.node(n)["attrs"]
        if at.get("codebook") != "event_roles":
            continue
        frames.append((float(at.get("priority", 0.0)),
                       str(at.get("guard_json", "")),
                       str(at.get("effects_json", "[]"))))
    frames.sort(key=lambda f: f[0])
    return frames


def _decode_roles_graph(agent, clause) -> dict:
    """DECODE role assignment over the VerbFrame codebook — the graph-native
    replacement for the Python role cascade. Reads the priority-ordered VerbFrame
    codebook out of the graph and, for each frame in turn, evaluates its guard Term
    against the clause node (its precomputed candidate attrs + the running-state
    `r_*` attrs) via the Rust `evaluate`; when the guard holds, the frame's effect
    Terms are evaluated (against the CURRENT running state) and written onto the
    clause — so a higher-priority frame OVERRIDES a lower one exactly as the
    sequential Python assignment did (applying the highest-priority applicable writer
    to each field is the argmax the decode performs). This driver holds NO role logic:
    it is a generic codebook interpreter (evaluate guard → name-keyed effect write),
    the same status as `ground_concern`'s name-keyed lookup on a Term's verdict. All
    role DECISIONS live in the frame DATA (`seeds/event_role_frames.json`). Returns
    the resolved subj/obj/spans + `inverted`; `_ground_event` emits from them."""
    sub, native, _ = _resolve(agent)
    env = {"c": clause}
    for _prio, guard_json, effects_json in _load_event_frames(sub):
        guard = json.loads(guard_json) if guard_json else None
        if guard is None or not _frame_truthy(native.evaluate(guard, env)):
            continue
        effects = json.loads(effects_json) if effects_json else []
        # Evaluate ALL effect values against the current state, THEN write — so a
        # frame's own effects read a consistent pre-write snapshot (matches the
        # simultaneous `subj, subj_span = ph, obj_span` assignments of the cascade).
        vals = [(field, native.evaluate(term, env)) for field, term in effects]
        for field, v in vals:
            sub.set_attr(clause, field, v)
    a = dict(sub.node(clause)["attrs"])
    return {"subj": a.get("r_subj", ""), "subj_span": a.get("r_subj_span", ""),
            "obj": a.get("r_obj", ""), "obj_span": a.get("r_obj_span", ""),
            "inverted": bool(float(a.get("r_inverted", 0.0)) >= 1.0)}


def _role_emit_frames(sub) -> list:
    """The RoleFrame EMIT codebook, graph query (no decision): (head_attr, guard_json)
    per participant-role frame. A minted role (Phase 3) joins automatically."""
    out = []
    for n in sub.nodes("RoleFrame"):
        at = sub.node(n)["attrs"]
        if at.get("codebook") != "event_roles" or at.get("kind") != "role_emit":
            continue
        out.append((str(at.get("head_attr", "")), str(at.get("guard_json", ""))))
    return out


def _ground_event(agent, clause, a: dict, r: dict, *, intransitive_ok: bool = False,
                  return_meta: bool = False):
    """EVENT ground_template (mode=event) — MECHANICAL emission of predications from
    the RESOLVED roles (`r`) + the precomputed candidate attrs (`a`), in the EXACT
    accumulation order `_event_predication` produced: the inverted-oblique / bare-
    intransitive early-returns; then core `[verb,subj,obj]` → ditransitive theme →
    DATA-DRIVEN participant RoleFrames (the thematic oblique, now graph data) →
    subject prenominal states → object prenominal states. This is grounding hygiene
    (formatting + degenerate/duplicate suppression + the held POS prenominal-state
    read) + a mechanical RoleFrame consult, NOT role decision. Returns preds (or
    (preds, inverted) when `return_meta`)."""
    def _ret(preds, inv):
        return (preds, inv) if return_meta else preds

    subj, subj_span = r["subj"], r["subj_span"]
    obj, obj_span = r["obj"], r["obj_span"]
    inverted = r["inverted"]
    verb = a.get("verb", "")
    if not subj:
        return _ret([], False)
    if not obj or obj == subj:
        if inverted:
            obl = a.get("obl_inv_head", "")
            if obl and obl != subj:
                out = [[verb, subj, obl]]
                out.extend(_prenominal_states(subj_span, subj))
                return _ret(out, True)
        if intransitive_ok and _pron_case(subj) == "subject":
            return _ret([[verb, subj]], True)
        return _ret([], inverted)
    out = [[verb, subj, obj]]
    if obj and a.get("has_post_verb", 0.0) >= 1.0 and a.get("post_verb_is_prep", 0.0) < 1.0:
        theme = a.get("dtrans_theme", "")
        if theme and theme != subj and theme != obj:
            out.append([verb, subj, theme])
    # PARTICIPANT ROLES — data-driven over the RoleFrame codebook. Each frame whose
    # guard holds emits [verb, subj, <head>]. The thematic oblique is the default
    # (and only seeded) RoleFrame; a novel role minted by the role sd-loop emits here
    # too. Guard evaluation is the Rust `evaluate`; no role logic in Python.
    sub, native, _ = _resolve(agent)
    captured = set()
    if native is not None and clause is not None:
        for head_attr, guard_json in _role_emit_frames(sub):
            if not guard_json:
                continue
            if _frame_truthy(native.evaluate(json.loads(guard_json), {"c": clause})):
                h = a.get(head_attr, "")
                if h:
                    out.append([verb, subj, h])
                    captured.add(h)
        # RESIDUAL OBSERVATION (Phase 3): an ANIMATE PP participant the precompute
        # observed (obl_animate/obl_role_ok/obl_canon_head, held faculty reads,
        # present regardless of which RoleFrames exist) that NO RoleFrame emitted is
        # an uncaptured role — mark it so the role sd-loop (`role_decode_loop`) can
        # MINT a RoleFrame back from it. Marking the residual is mechanical I/O; the
        # decision to grow a role is the graph rule. With the oblique RoleFrame
        # present this never fires (the frame captures the head, so `captured` holds
        # it and the corpus is byte-identical).
        obl = a.get("obl_canon_head", "")
        signal = (obl and obl != subj and obl != obj
                  and a.get("obl_animate", 0.0) >= 1.0 and a.get("obl_role_ok", 0.0) >= 1.0)
        if signal and obl not in captured:
            sub.set_attr(clause, "role_residual", 1.0)
            sub.set_attr(clause, "residual_head", obl)
    out.extend(_prenominal_states(subj_span, subj))
    out.extend(_prenominal_states(obj_span, obj))
    return _ret(out, inverted)


def _event_predication_graph(agent, words: list, lex: dict, *, intransitive_ok: bool = False,
                             return_meta: bool = False):
    """GRAPH-NATIVE event grounding: ingest the clause-graph (Phase 1) → decode roles
    over the VerbFrame codebook (`_decode_roles_graph`, graph data) → `_ground_event`
    emission. Byte-identical to the (now-deleted) Python `_event_predication` over the
    frozen Aesop+Grimm corpus. `return_meta` returns (preds, inverted)."""
    clause = _event_clause_graph(agent, words, lex)
    if clause is None:
        return ([], False) if return_meta else []
    sub, _, _ = _resolve(agent)
    a = dict(sub.node(clause)["attrs"])
    if a.get("has_verb", 0.0) < 1.0:
        return ([], False) if return_meta else []
    r = _decode_roles_graph(agent, clause)
    a = dict(sub.node(clause)["attrs"])   # re-read: decode wrote the r_* fields
    return _ground_event(agent, clause, a, r,
                         intransitive_ok=intransitive_ok, return_meta=return_meta)


def event_predication_for_sentence(agent, sentence, *, intransitive_ok: bool = True) -> list:
    """ARGUMENT-STRUCTURE event parse of a HELD-OPEN single clause — the coref
    fallback's entry BEFORE it drops to read_clause. Returns a parse ONLY for a
    genuinely NON-SVO clause (a fronted/post-posed subject or object, verb-subject, or
    a bare-intransitive pronoun subject — the orders read_clause's SVO grammar mis-
    slots); a CANONICAL SVO clause returns [] so read_clause keeps it byte-identical
    (the fallback only RESCUES inversions, it does not re-parse ordinary prose).
    ABSTAINS on a construction-marked clause (copula / subordinator / relativizer /
    enumerator) — that reading belongs to read_clause."""
    sub, _, _ = _resolve(agent)
    lex = _marker_lexicon(sub)
    if isinstance(sentence, (list, tuple)):
        words = [str(w) for w in sentence if str(w).strip()]
    else:
        words = [w for w in ct._recognise_words(agent, str(sentence)) if str(w).strip()]
    while words and str(words[0]).lower() in _LEAD_CONNECTIVES:
        words = words[1:]
    if not words:
        return []
    classes = [lex.get(_clean_tok(w).lower()) for w in words]
    if any(c in _STRUCTURING for c in classes):
        return []
    preds, inverted = _event_predication_graph(agent, words, lex,
                                               intransitive_ok=intransitive_ok, return_meta=True)
    return preds if inverted else []


def _read_clause_clean(agent, words: list) -> list:
    """Read ONE clause into clean-headed predication(s). A clause carrying a
    construction-identity (structuring) marker (copula/enumerator/conditional/...)
    routes through the HELD read_clause (the collapse decides the construction),
    then its role heads are cleaned; otherwise it is an EVENT clause and its SVO is
    extracted verb-first with clean heads. Leading discourse connectives are stripped
    first (coherence layer, not predication)."""
    words = [w for w in words if str(w).strip()]
    while words and str(words[0]).lower() in _LEAD_CONNECTIVES:
        words = words[1:]
    if not words:
        return []
    sub, _, _ = _resolve(agent)
    lex = _marker_lexicon(sub)
    classes = [lex.get(str(w).lower()) for w in words]
    if any(c in _STRUCTURING for c in classes):
        r = read_clause(agent, list(words), write=False, learn=False)
        out = []
        for p in (r.get("predications") or []):
            cp = _clean_pred(agent, p)
            if cp:
                out.append(cp)
                out.extend(_prenominal_states(str(p[1]), cp[1]))
                out.extend(_prenominal_states(str(p[2]), cp[2]))
        return out
    return _event_predication_graph(agent, words, lex)


def _run_has_verb(words: list) -> bool:
    return _find_main_verb([w for w in words if str(w).strip()]) is not None


def _is_complementizer_that(region: list, wi: int) -> bool:
    """Is the token at `region[wi]` (surface 'that') a COMPLEMENTIZER opening an
    embedded FINITE clause ('the robbers saw THAT the lights were out', 'they think
    THAT they were too bold')? True only when the span AFTER 'that' is a subject +
    finite verb — a full embedded clause with its OWN subject preceding the verb.

    This DISTINGUISHES the complementizer from 'that's other roles, which must NOT
    open a clause: the demonstrative pronoun subject ('THAT is good' — the finite
    verb is the FIRST token after 'that', no intervening subject) and the bare
    relativizer / determiner ('the man THAT ran', 'I saw THAT man' — no finite verb
    with a subject before it after 'that'). The signal is the SAME held main-verb
    faculty the segmenter already uses (_find_main_verb): a finite verb exists in
    the remainder AND a subject precedes it (main-verb index > 0)."""
    rest = [w for w in region[wi + 1:] if str(w).strip()]
    if not rest:
        return False
    mv = _find_main_verb(rest)
    return mv is not None and mv > 0


# --------------------------------------------------------------------------- #
#  REPORT-VERB IMPLICIT COMPLEMENT (Phase 2 of READER_PARSER_MIGRATION.md) --
#  'Public Citizen said Big Oil captured the government' carries NO explicit
#  'that' complementizer, so `_is_complementizer_that` above never fires and the
#  whole span reads as ONE flat clause: 'said' becomes the clause's sole
#  skeleton VERB marker and its finite-clause complement ('Big Oil captured the
#  government') is mashed into a single flat object NP -- the SAME kind of
#  mis-read `_is_complementizer_that` already fixes for the EXPLICIT-'that'
#  case, just missing its trigger token. The DECIDING fact -- that a REPORT/
#  communication verb (say/said/wrote/announced/...) ALSO opens an embedded
#  finite clause even with NO complementizer present -- is HELD DATA
#  (`MarkerClass{cls:'REPORT'}`, seeds/reading_constructions.json), read by
#  `report_membership` below: absent that class (an older/ablated seed), this
#  never fires and every report-verb sentence reads exactly as it did before
#  this phase (see the ablation test).
# --------------------------------------------------------------------------- #
def _report_class_node(sub):
    """The `ReportClass{cls:'REPORT'}` node, or None. A DEDICATED node type (not
    `MarkerClass`) on purpose -- see the seed note in seeds/reading_constructions.json:
    `_marker_lexicon` iterates `MarkerClass` nodes only and its `c = lex.get(word)`
    check runs BEFORE any class's own adjacency join, so a literal REPORT seed member
    living in that shared dict would silently pre-empt another class's (e.g.
    DESIGNATE's post-copular 'it is SAID') adjacency reach for the same surface form.
    Kept OUT of that dict entirely; `report_membership` is the only consultation
    path, called explicitly by `_segment_into_clauses`."""
    for n in sub.nodes("ReportClass"):
        if sub.node(n)["attrs"].get("cls") == "REPORT":
            return n
    return None


def report_membership(agent, verb: str) -> dict:
    """Is `verb` a REPORT/communication verb (say/said/wrote/announced/...)?
    Returns {lemma, report, nearness, nearest, joined, via}. A SEED member
    resolves directly (via='member'); an unseen verb JOINS by ADJACENCY --
    reusing `_wordnet_nearness` (the SAME WordNet path-similarity signal
    COS/DESIGNATE/POSSESS use) to the class's `report_anchor` >=
    `report_threshold`, placed into the class live (`_join_class`) -- mirrors
    situation_model_reader.cos_membership / character_tom.attitude_membership
    exactly; NOT a hardcoded Python verb list. Below threshold -> not a report
    verb (report=False)."""
    ensure_codebook(agent)
    sub, _, _ = _resolve(agent)
    w = str(verb).lower().strip()
    lemma = w
    try:
        from nltk.corpus import wordnet as wn
        lem = wn.morphy(w, "v")
        if lem:
            lemma = lem
    except Exception:
        pass
    node = _report_class_node(sub)
    if node is None:
        return {"lemma": lemma, "report": False, "nearness": 0.0,
                "nearest": None, "joined": False, "via": None}
    at = sub.node(node)["attrs"]
    forms = [str(f).lower() for f in (at.get("forms") or [])]
    if lemma in forms or w in forms:
        return {"lemma": lemma, "report": True, "nearness": 1.0,
                "nearest": lemma, "joined": False, "via": "member"}
    anchors = [str(a).lower() for a in (at.get("report_anchor") or [])]
    try:
        thr = float(at.get("report_threshold", 0.5))
    except (TypeError, ValueError):
        thr = 0.5
    score, member = _wordnet_nearness(lemma, anchors)
    if member is not None and score >= thr:
        _join_class(sub, node, lemma, score, member)
        return {"lemma": lemma, "report": True, "nearness": float(score),
                "nearest": member, "joined": True, "via": "adjacency"}
    return {"lemma": lemma, "report": False, "nearness": float(score),
            "nearest": member, "joined": False, "via": None}


def _report_literal_member(agent, word: str) -> bool:
    """Is `word` a LITERAL SEED member of the REPORT class -- a READ-ONLY check,
    unlike `report_membership` (which, on a miss, computes + PERSISTS an
    adjacency join via `_join_class`, mutating the class's `forms` for the REST
    of the session). `_is_report_complement_here` calls this instead of
    `report_membership` precisely to avoid that mutation: an accidental
    adjacency join (measured against the frozen parity corpus: common light
    verbs like 'have'/'give'/'know'/'hold' clear this class's own 0.5
    threshold against 'say'/'tell'/'announce'/'declare' by WordNet lexical
    accident) would otherwise, once joined, look identical to a genuine seed
    member on every LATER query in the same session -- silently re-opening the
    exact false-positive door `_is_report_complement_here`'s `via == 'member'`
    gate was written to close."""
    sub, _, _ = _resolve(agent)
    node = _report_class_node(sub)
    if node is None:
        return False
    forms = [str(f).lower() for f in (sub.node(node)["attrs"].get("forms") or [])]
    w = str(word).lower().strip()
    lemma = w
    try:
        from nltk.corpus import wordnet as wn
        lem = wn.morphy(w, "v")
        if lem:
            lemma = lem
    except Exception:
        pass
    return w in forms or lemma in forms


def _is_report_complement_here(agent, lex: dict, region: list, wi: int) -> bool:
    """Does `region[wi]` open an IMPLICIT (no 'that') finite-clause complement of a
    REPORT verb? True only when (a) `region[wi]` is a LITERAL SEED member of the
    REPORT class (`_report_literal_member`, a READ-ONLY check -- `report_membership`'s
    ADJACENCY-join arm is deliberately NOT used here, and not merely skipped:
    measured against the frozen parity corpus, WordNet path-similarity at this
    class's own 0.5 threshold puts common light verbs ('have'/'has'/'had', 'give',
    'know', 'hold'/'held') within reach of the 'say'/'tell'/'announce'/'declare'
    anchors by lexical accident, and because `_join_class` PERSISTS a join into the
    class's `forms` for the rest of the session, even gating on the RESULT's
    `via == 'member'` is not enough -- the mutation already happened as a side
    effect of computing it, so the SAME accidental word reads as a genuine literal
    member on every LATER query too; unlike COS/DESIGNATE's own documented
    accidental joins, which stay CONTAINED to one clause's construction, a false
    REPORT join here would mis-segment every later clause containing that word. The
    SEED list is hand-curated instead, exactly the "hand-written held DATA is
    acceptable bootstrapping" fallback this migration permits) NOT already claimed
    by a DIFFERENT marker class (mirrors character_tom.
    _find_attitude_marker's exact guard) sitting in the main-verb slot
    (`ir.is_verb_headed`); (b) the span AFTER it is itself subject+finite-verb shaped
    -- the SAME test `_is_complementizer_that` applies to the span after an explicit
    'that' (`_find_main_verb(rest) is not None and mv > 0`), so a bare NP object
    ('the fox told a LIE') is NOT mistaken for a clause; (c) that span contains NO
    explicit complementizer ('that'/'whether') before the embedded verb -- when one
    is present the PRE-EXISTING `_is_complementizer_that` branch is the correct
    handler (it keeps a ditransitive indirect object in the MATRIX clause: 'the Bat
    ASSURED HIM that he was not a bird' -- 'him' stays 'assured's object, the
    complement starts at 'that'; letting this branch fire instead would swallow
    'him' into a bogus complement subject -- an audited false positive); and (d) the
    candidate SUBJECT span between the report verb and the later finite verb
    contains NO preposition either (`_PP_PREPS`) -- the SAME ditransitive shape
    without an explicit 'that' ('the fox TOLD him OF the difficulty they were both
    in' -- 'of' introduces an ordinary oblique argument of 'told', not a clause
    subject; this exact sentence is the one `_left_run_has_finite_verb`'s own
    docstring names for the SAME reason). Genuine indirect speech has the embedded
    verb's subject IMMEDIATELY after the report verb, with no intervening object/PP/
    complementizer. The caller additionally requires a non-empty accumulated run
    before `wi` (a subject for the matrix predicate) -- a clause-initial report verb
    is left untouched here."""
    w = str(region[wi]).lower()
    cls = lex.get(w)
    if cls is not None and cls != "REPORT":
        return False
    if not ir.is_verb_headed(w):
        return False
    if not _report_literal_member(agent, w):
        return False
    rest = [t for t in region[wi + 1:] if str(t).strip()]
    if not rest:
        return False
    mv = _find_main_verb(rest)
    if mv is None or mv <= 0:
        return False
    pre = rest[:mv]
    # THE CANDIDATE SUBJECT SPAN MUST BE ENTIRELY UNMARKED CONTENT (audited false
    # positive, frozen parity corpus): a token in `pre` that the lexicon ALREADY
    # classifies as anything -- a complementizer, a preposition, a CLAUSE_LINK
    # temporal/subordinating connective ('now WHEN the forester comes home' --
    # 'when' opens its OWN clause a few tokens in; 'now' alone is a bare adverb,
    # never a clause subject, so treating 'now when the forester comes' as this
    # branch's embedded-clause subject span wrongly swallowed the genuine
    # 'say(i, now)' predication the pre-existing CLAUSE_LINK boundary handles a
    # few tokens later on its own), AND/OR, etc. -- means `pre` is not a clean
    # subject NP at all; some OTHER, already-correct mechanism owns this
    # boundary and this branch must defer to it (the SAME discipline as the
    # complementizer/PP checks above, generalised to every recognised class).
    if any(lex.get(str(t).lower()) is not None for t in pre):
        return False
    if any(str(t).lower() in _COMPLEMENTIZERS for t in pre):
        return False
    return not any(str(t).lower() in _PP_PREPS for t in pre)


def _clause_subject_words(agent, words: list) -> Optional[list]:
    """The SUBJECT word-run of a clause if it carries an EXPLICIT subject (content or
    a pronoun before its main verb, past a leading adjunct PP), else None — a
    subject-less VP (verb-initial). None is the VP-COORDINATION signal: 'The dog
    thanked her AND gave her a whistle' splits into two verb-headed clauses, but the
    SECOND ('gave her a whistle') has no subject of its own — it SHARES the first
    VP's subject. Held POS faculties only (the SAME _find_main_verb / _skip_leading_pp
    the event parser uses); no new decision. Distinguishes VP-coordination (shared
    subject) from CLAUSE-coordination ('the dog barked and the cat ran' — the second
    clause 'the cat ran' HAS a subject, so this returns it and no sharing fires)."""
    flat = [_clean_tok(w) for w in words if str(_clean_tok(w))]
    while flat and str(flat[0]).lower() in _LEAD_CONNECTIVES:
        flat = flat[1:]
    vi = _find_main_verb(flat)
    if vi is None:
        return None                                 # no verb — not a VP at all
    low = [str(w).lower() for w in flat]
    lo = _skip_leading_pp(low)
    # POST-POSED subject (inversion) FIRST -- a fronted adjunct PP whose head noun the
    # shallow lo skip leaks into the pre-verb slot must NOT be mistaken for the subject
    # ('Down the dark stair crept the CHILD': 'stair' is the PP head, 'child' the
    # subject). When the FULL fronted PP consumes the whole pre-verb span the subject
    # is the post-verbal nominal (returned as its clean head, so it threads as the
    # shared subject of a following subject-less coordinate VP -- '...clutching a
    # candle'). Same argument-structure signals the event parser uses.
    if low and low[0] in _PP_PREPS and flat[vi + 1:]:
        adj_end, _ = _leading_adjunct(low, flat)
        if adj_end >= vi:
            head = _arg_head(agent, " ".join(flat[vi + 1:]))
            if head:
                return [head]
    subj_toks = flat[lo:vi]
    for t in subj_toks:
        tl = str(t).lower()
        if tl in _AUX or tl in _PP_PREPS or tl in _DETERMINERS or tl in _LEAD_CONNECTIVES:
            continue
        return subj_toks                            # a content/pronoun subject before the verb
    # a post-posed NOMINATIVE PRONOUN subject ('So rested HE by the tree') threads too.
    nom_i = _core_case_pronoun(low, vi, "subject")
    if nom_i is not None and nom_i > vi:
        return [flat[nom_i]]
    return None                                     # verb-initial — a subject-less coordinate VP


def _segment_into_clauses(agent, regions: list, lex: dict) -> tuple:
    """Split the recognised regions into clause word-lists at recognised boundaries.
    A comma (a region break) ends a clause; a CLAUSE-OPENER marker (CLAUSE_LINK / IF
    / CAUSE_SUB / REL) ends the current clause and is dropped (boundary glue); an
    AND/OR is a clause boundary ONLY when both the accumulated run and the remaining
    run are verb-headed (else it is enumeration glue inside one clause, dropped).

    TEMPORAL vs CONDITIONAL 'then' (the P2 residual this extends): a bare THEN
    marker is AMBIGUOUS between the if/then CONDITIONAL construction's consequent
    marker and a temporal VP/clause-SEQUENCING coordinator ('he knocked THEN he
    entered'). The disambiguating signal is whether an IF marker governs it — `if_open`
    tracks "an IF clause-opener has been recognised somewhere earlier in this
    sentence" (never reset once set: the if/then pairing spans the whole sentence,
    commas included — 'If it rains, then the ground is wet.' still has 'then'
    governed). A 'then' with NO governing IF is treated EXACTLY like AND/OR: a
    clause boundary only when both the accumulated run and the remainder are
    verb-headed (so it drives the SAME shared-subject VP-coordination split
    `decompose_sentence` already does for 'and'); a governed 'then' is left in
    place (unchanged — it stays in the clause's marker skeleton for the held
    conditional construction to decode).

    Returns (clauses, n_boundaries) — n_boundaries>0 means a real multi-clause split
    was recognised (the gate that decides whether decomposition fires)."""
    clauses: list = []
    openers: list = []                              # opener class that began each clause (parallel)
    cur: list = []
    cur_opener = None                               # opener class that began `cur` (None = bare)
    boundaries = 0
    if_open = False
    for region in regions:
        region = [w for w in region if str(w).strip()]
        if not region:
            continue
        if cur:                                     # a comma ended the previous clause
            clauses.append(cur)
            openers.append(cur_opener)
            cur = []
            cur_opener = None
            boundaries += 1
        wi = 0
        while wi < len(region):
            w = region[wi]
            cls = lex.get(str(w).lower())
            if cls in _CLAUSE_OPENERS:
                if cur:
                    clauses.append(cur)
                    openers.append(cur_opener)
                    cur = []
                    boundaries += 1
                cur_opener = cls                    # the NEW clause is opened by this marker
                if cls == "IF":
                    if_open = True
                wi += 1
                continue
            if cls == "BUT":
                # CONTRAST COORDINATOR (agent-held MarkerClass data, e.g. 'but').
                # Only the LEADING case is unambiguous: a comma (or prior
                # boundary) has already ended the previous clause, so a 'but' at
                # the START of the new region ('X was suppressed, BUT Y was
                # published') is opener glue for a new INDEPENDENT clause -> drop
                # it, so it does not stick to that clause's leading role. A
                # MID-clause 'but' is left ALONE (kept, as before): it is
                # genuinely ambiguous between a coordinator ('he tried BUT
                # failed') and an adverbial 'only' ('had BUT touched me', 'had
                # BUT devoured us') that the surface verb-headedness test cannot
                # separate, and splitting the adverbial reading corrupts the
                # predication. So this fixes ONLY the leading-coordinator leak.
                # Additive: absent this taught MarkerClass a 'but' has cls==None
                # and falls through to `cur.append` exactly as before -- a boot
                # WITHOUT it is byte-identical, and every mid-clause 'but' is
                # byte-identical WITH it.
                if not cur:
                    cur_opener = None                # leading independent clause
                    wi += 1                          # drop the opener glue
                    continue
                cur.append(w)                        # mid-clause 'but': keep it
                wi += 1
                continue
            if cls in ("AND", "OR") or (cls == "THEN" and not if_open):
                rest = region[wi + 1:]
                if cur and _run_has_verb(cur) and _run_has_verb(rest):
                    clauses.append(cur)
                    openers.append(cur_opener)
                    cur = []
                    cur_opener = None
                    boundaries += 1
                wi += 1                              # drop the coordinator either way
                continue
            if cls is None and str(w).lower() in _COMPLEMENTIZERS and _is_complementizer_that(region, wi):
                # COMPLEMENTIZER ('that'/'whether') opens an embedded finite clause: end
                # the matrix clause here so its main verb is unambiguous ('the robbers
                # saw' — the matrix verb 'saw', not the embedded 'lights'/'were'; 'the
                # sparrow asked him' — not the embedded 'he had') and the embedded clause
                # reads on its own. Dropped like the other clause-opener glue.
                if cur:
                    clauses.append(cur)
                    openers.append(cur_opener)
                    cur = []
                    boundaries += 1
                cur_opener = "COMP"
                wi += 1
                continue
            if cur and _is_report_complement_here(agent, lex, region, wi):
                # REPORT-VERB IMPLICIT COMPLEMENT (Phase 2): a report/communication
                # verb (say/said/wrote/announced/...) directly followed by a
                # subject+finite-verb span (no 'that') ALSO opens an embedded finite
                # clause -- the same boundary the COMPLEMENTIZER branch above opens
                # for an explicit 'that', just triggered by REPORT-class membership
                # (held DATA, `report_membership`) instead of a literal token. Unlike
                # 'that' (dropped as glue), the report verb ITSELF is KEPT at the end
                # of the matrix clause (`decompose_sentence` reads it back out to
                # rebuild the matrix's own predication) -- a DISTINCT opener tag
                # ('COMP_REPORT', not the plain 'COMP' the 'that' branch above uses)
                # keeps this phase's own reconstruction step from ever touching the
                # pre-existing explicit-'that' path. Requires a non-empty `cur` (a
                # subject already accumulated) -- a clause-initial report verb has no
                # matrix subject and is left untouched.
                cur.append(w)
                clauses.append(cur)
                openers.append(cur_opener)
                cur = []
                cur_opener = "COMP_REPORT"
                boundaries += 1
                wi += 1
                continue
            cur.append(w)
            wi += 1
    if cur:
        clauses.append(cur)
        openers.append(cur_opener)
    # a comma that merely separated an appositive/PP from a single clause is not a
    # real multi-clause split unless >=2 of the resulting clauses actually read.
    return clauses, openers, boundaries


def _report_matrix_predication(agent, matrix_words: list, complement_pred: list) -> Optional[list]:
    """Rebuild the REPORT-verb matrix's OWN predication (`[report_verb,
    matrix_subject, complement_subject]`) after `_segment_into_clauses` has split it
    away from its finite-clause complement (the `COMP_REPORT` opener). `matrix_words`
    is the matrix clause AS SEGMENTED: subject words followed by the report verb
    itself (kept, not dropped the way a literal 'that' is). `complement_pred` is the
    complement clause's OWN already-cleaned leading predication
    (`[verb, subj, obj, ...]`), read moments earlier by the SAME `_read_clause_clean`
    call every other clause in this sentence goes through -- no re-parse, no second
    decision about the complement's meaning. The matrix's object is the complement's
    OWN subject (a0), not the flat mashed NP the pre-phase-2 single-clause read would
    have produced -- 'Public Citizen said Big Oil captured the government' becomes
    said(public_citizen, big_oil) ALONGSIDE the complement's own captured(big_oil,
    government), sharing the 'big_oil' entity (the graph link a downstream reader
    walks from the report to what was reported). Returns None when the matrix has no
    recognisable subject (nothing to report FROM) or the complement produced no
    predication (nothing to report)."""
    words = [w for w in matrix_words if str(w).strip()]
    if len(words) < 2:
        return None
    verb = str(words[-1]).lower()
    subj_words = words[:-1]
    subj = _arg_head(agent, " ".join(str(w) for w in subj_words))
    if not subj or not complement_pred or len(complement_pred) < 2:
        return None
    obj = str(complement_pred[1])
    if not obj:
        return None
    return [verb, subj, obj]


def decompose_sentence(agent, sentence, *, max_clauses: int = 12) -> dict:
    """Decompose a (possibly multi-clause) sentence at recognised clause boundaries
    and read each clause into clean-headed predications. Returns {clauses,
    predications, multi_clause, n_boundaries}. `multi_clause` is True only when a
    real clause boundary was recognised AND the decomposition grounds >=1
    predication (so a single-clause SVO sentence falls through untouched)."""
    ensure_codebook(agent)
    sub, _, _ = _resolve(agent)
    lex = _marker_lexicon(sub)
    regions = ct._recognise_regions(agent, str(sentence))
    clauses, openers, n_boundaries = _segment_into_clauses(agent, regions, lex)
    has_rel = "REL" in (openers or [])
    preds: list = []
    read_clauses: list = []
    # VP-COORDINATION shared subject: a subject-less verb-headed conjunct ('...AND gave
    # her a whistle') SHARES the subject of the most recent clause that had one ('the
    # dog'), so its predication binds to that subject instead of being dropped. The
    # shared subject is the FIRST VP's subject word-run; a clause with its OWN subject
    # (clause-coordination) updates the carry and is read unchanged. Reset per sentence.
    shared_subject: Optional[list] = None
    for idx, cl in enumerate(clauses[:max_clauses]):
        opener = openers[idx] if idx < len(openers) else None
        subj_words = _clause_subject_words(agent, cl)
        if opener == "REL" and shared_subject is not None:
            # a comma-delimited REL clause ('..., who was bolder than the rest, ...') is
            # a MODIFIER of its antecedent, not an independent clause: it shares the
            # antecedent's subject (the thread) and never becomes the thread itself, so
            # its predicate complement binds to the antecedent instead of minting a
            # spurious agent-entity out of the complement head ('bolder').
            cp = _read_clause_clean(agent, list(shared_subject) + list(cl))
        elif subj_words is None and shared_subject is not None and _run_has_verb(cl):
            cp = _read_clause_clean(agent, list(shared_subject) + list(cl))
        else:
            cp = _read_clause_clean(agent, cl)
            if subj_words is not None:
                shared_subject = subj_words
            elif has_rel and shared_subject is None and idx == 0 and not _run_has_verb(cl):
                # a sentence-initial verbless groundable NP that ANTECEDES a REL clause
                # ('One of them, who ...') seeds the shared-subject thread so the REL
                # modifier and the main VP both bind to it. Scoped to REL-bearing
                # sentences so the common appositive/fronted-adjunct cases are unchanged.
                head = _arg_head(agent, " ".join(str(w) for w in cl))
                if head:
                    shared_subject = [w for w in cl if str(w).strip()]
        if cp:
            read_clauses.append(cl)
            if opener == "COMP_REPORT" and idx > 0:
                # REPORT-VERB IMPLICIT COMPLEMENT (Phase 2): this clause is the
                # finite-clause complement `_segment_into_clauses` split off a
                # REPORT verb (say/said/wrote/...) for -- rebuild the matrix's own
                # predication from the matrix clause it was split away from
                # (`clauses[idx - 1]`) + this complement's own just-grounded
                # predication (`cp[0]`), so the report itself is not silently
                # dropped (see `_report_matrix_predication`'s docstring). Inserted
                # BEFORE the complement's own predications -- NOT after -- so a
                # downstream coref-aware ingest (coref_entities.resolve_and_ingest)
                # resolves the matrix predication's object (the complement's
                # subject, e.g. 'exxon') while it is STILL a first mention: that
                # module's `_quoted_subject_inversion` heuristic ('QUOTE said
                # SPEAKER' inversion) keys on which argument is ALREADY resident,
                # and complement-first ordering made it misread said(citizen,
                # exxon) as an inverted quote once 'exxon' had already been
                # minted by its own event moments earlier (audited regression
                # against the frozen parity corpus). Matrix-first avoids the
                # collision entirely; the complement's own event still shares the
                # SAME entity node once IT mints moments later (`_entity` dedups
                # by name regardless of order), so the graph link this phase
                # wants -- the say event's object and the capture event's agent
                # are the SAME node -- is unaffected by the swap.
                mp = _report_matrix_predication(agent, clauses[idx - 1], cp[0])
                if mp:
                    read_clauses.append(clauses[idx - 1])
                    preds.append(mp)
            preds.extend(cp)
    # dedup (preserve order).
    seen: set = set()
    uniq: list = []
    for p in preds:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    multi = bool(n_boundaries) and bool(uniq)
    return {"clauses": [list(c) for c in clauses], "read_clauses": read_clauses,
            "predications": uniq, "multi_clause": multi, "n_boundaries": n_boundaries}


__all__ = ["ensure_codebook", "read_clause", "read_text", "concepts_from_reading",
           "_skeleton_from_words", "_decode", "_winner",
           "decompose_sentence", "_read_clause_clean", "_event_predication_graph",
           "event_predication_for_sentence", "_find_main_verb", "_arg_head"]
