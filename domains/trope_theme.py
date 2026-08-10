"""trope_theme — TROPE RECOGNITION + THEME, ONE LEVEL UP FROM THE NARRATIVE ARC.

`narrative_structure` decodes WHICH STORY-GRAMMAR ROLE one event plays in a
character's goal-pursuit chain (setup/problem/solution/action/consequence/
resolution). This module is the construction ONE LEVEL UP: a TROPE — a
recognisable, recurring PATTERN of arc-roles + action-character features
(Dodgson's "nonsense" read straight: tropes are the admissibility grammar of
narrative, the same way a Jabberwocky sentence's grammaticality survives its
lexical content). A trope is recognised over the ARC `narrative_structure.
recognize_narrative_structure` already built, by `ShapeDecode`'s SET-COVER
search against a dedicated `ShapeSignatureTrope` codebook
(`seeds/narrative_tropes.json`) — the SAME collapse `discourse_coherence` and
`narrative_structure` already use, one level further up the construction
stack. Nothing here re-derives meaning any earlier component's own collapse
already committed.

Every input is a graph fact some other component's own collapse already
decided:

  · the PROBLEM / RESOLUTION signal — whether the arc (`narrative_structure`'s
    own minted `NarrativeRole` nodes, read via `read_narrative_roles`) carries
    a role=='problem' / role=='resolution' — narrative_structure's own
    ShapeDecode verdict, reused verbatim;
  · the INDIRECT-MECHANISM signal — whether the arc's 'solution' role's own
    sentence carries a MINTED `causes` edge whose provenance is
    `inference_generation.resolve_causal_gap`'s own PHYSICAL-EFFECT
    displacement decode (drop a solid -> a level rises) — read off `graph
    ['causal']`, that component's own already-committed record, never
    re-decided here;
  · the INCREMENTAL signal — whether the arc's 'solution' sentence carries a
    change-of-state SmEvent whose tracked entity is PLURAL, read GRAPH-NATIVE
    off the durable `coref_number=='plural'` marker `situation_model_reader.
    ingest_predication` stamps on the SmEvent (+ the `sentence_order` stamp) —
    a plural affected entity, evidence of many small units acted on one at a
    time rather than one decisive blow; an honest, imperfect PROXY for
    "incremental/repeated action" (see the module docstring's honesty note),
    never a lexical match on the literal phrase "one by one";
  · the BLOCKED signal — whether a `inference_generation.resolve_precondition_
    gap` gap was MINTED for this entity, read GRAPH-NATIVE off the durable
    `blocked_gap=1` marker stamped on the entity's SmEntity node — the direct
    route was genuinely blocked, not merely bypassed by preference.

EACH of those four facts becomes ONE TOKEN (an existence check, the SAME
"mechanical signal -> single-token skeleton" shape `discourse_coherence.
_unmarked_signal` / `narrative_structure._slot_token` already use) and the
resulting TOKEN SET (order-independent; a small, fixed vocabulary) is decoded
in ONE `ShapeDecode` call against `ShapeSignatureTrope`. The decode's own
SET-COVER search (see `runners/dsl/src/shape_decode.rs`) can return a
MULTI-STEP `plan` — each step names ONE recognised trope, covering the
subset of tokens that trope's own held signature matches. Because the three
seeded tropes' signatures are pairwise near-disjoint over the four-token
vocabulary (`INGENUITY_OVER_STRENGTH` = {PROBLEM, INDIRECT};
`PERSISTENCE_PAYS` = {INCREMENTAL, RESOLUTION}; `NECESSITY_INVENTION` =
{BLOCKED, INDIRECT}), a story whose arc fires several of these signals at
once (the crow: problem + indirect + incremental + resolution, no blocked)
is recognised as instantiating SEVERAL tropes in one decode — the decode's
own greedy coverage-maximising steps, never a Python loop trying trope names
one by one. A token set no schema covers decodes to an EMPTY plan: an
honest, discriminative null (no trope forced onto an arc that does not
instantiate one).

THEME. The abstract moral/lesson is read off, mechanically, from the
recognised trope(s)' own held `theme` attr (this module's one-line authored
gloss, held DATA, never re-derived from free text) plus the resolution
evidence — never invented per-story. A `Theme` node is minted ONLY when at
least one trope was recognised (no trope -> no theme, the same honest-null
discipline).

LABELLING. `domains/tropes_teacher.py`'s TV-Tropes lookup supplies a citable
NAME + definition for a recognised trope — a LABEL, applied AFTER the
decode already decided which trope fired, exactly as instructed: "use
tropes_teacher to supply the trope's NAME/definition, the RECOGNITION being
the structured decode." `label_candidates` (seed data, a short list of
TVTropes search phrases per trope) is tried in order via `TropesTeacher.
lookup`; the first hit's own `name`/`definition` becomes the citable label.
No candidate hits -> the codebook's own authored `theme`/`note` is the label,
honestly marked as self-authored rather than TVTropes-sourced.

GRAPH-CHECKABLE (the anti-hallucination gate). Every minted `Trope` node
carries `instantiates_trope` edges FROM the actual `NarrativeRole` nodes (and,
where the signal came from a causal/blocking record rather than a role, a
`TropeEvidence` node holding that record) that supplied its covered tokens —
a trope is never a free-floating label; a caller can always walk backward
from the `Trope` node to the arc structure that earned it.

ARCHITECTURE (CLAUDE.md). The decision that carries content — WHICH trope(s)
an arc instantiates — is `ShapeDecode`'s own set-cover verdict, read off its
`plan`. This module only (a) reads already-committed graph facts (the arc's
roles, the causal/blocking records, the situation-model ingest state) —
mechanical, no new meaning decided; (b) builds the token set from those facts
(existence checks, never a trope name); (c) mints the resulting `Trope`/
`Theme` nodes and their evidence edges (mechanical graph I/O); (d) looks up a
citable label for an ALREADY-DECIDED trope name (mechanical dictionary
lookup, not a decision about which trope). No `if`/`else` anywhere in this
module compares against a trope-name string or returns one — every trope
name a caller sees comes from the seed's own `name` attr, read back through
the decode's `plan`. No `import re`; donkey = 0.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import discourse_coherence as dc
from domains import narrative_structure as ns
from domains import situation_model_reader as smr

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CODEBOOK_SEED = os.path.join(_ROOT, "seeds", "narrative_tropes.json")
_CODEBOOK_TYPE = "ShapeSignatureTrope"

# ---- SEMANTIC (content-relation) tropes -- one axis ACROSS from the arc-shape
# tropes above. The arc-shape path (everything up to __all__'s recognize_tropes_
# and_theme) is UNTOUCHED (crow/generic byte-identity); this is an additive
# recogniser over the situation model's participant relations + outcome valence.
_SEM_CODEBOOK_SEED = os.path.join(_ROOT, "seeds", "semantic_tropes.json")
_SEM_CODEBOOK_TYPE = "ShapeSignatureSemanticTrope"

_TEACHER = None
_TEACHER_LOADED = False


# --------------------------------------------------------------------------- #
#  resolution + codebook install (mechanical adapter I/O — no decision).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def ensure_codebook(agent) -> None:
    """Idempotently install the trope codebook (`ShapeSignatureTrope` nodes)
    plus its dependency (`narrative_structure`, for the arc/role mechanism
    this codebook's tokens read). Guarded by a graph-resident
    `Seed{id:'narrative_tropes'}` sentinel — the SAME idempotency idiom
    `narrative_structure.ensure_codebook` uses. Mechanical seed I/O."""
    sub, _ = _resolve(agent)
    ns.ensure_codebook(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "narrative_tropes":
            return
    with open(_CODEBOOK_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "narrative_tropes", "version": manifest.get("version", "1.0.0")})


# --------------------------------------------------------------------------- #
#  DECODE — a thin ShapeDecode shim pointed at the trope codebook_type, kept
#  SEPARATE from narrative_structure's role pool / discourse_coherence's
#  relation pool / reading_collapse's construction pool (mirrors ns._decode).
#  max_steps > 1: a story can instantiate SEVERAL tropes; the decode's own
#  set-cover search finds however many the token set actually supports.
# --------------------------------------------------------------------------- #
def _decode(agent, skeleton: list) -> dict:
    _, native = _resolve(agent)
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": [list(x) for x in (skeleton or [])]},
            "codebook_type": _CODEBOOK_TYPE, "beam": 1, "max_steps": 6, "cand_k": 4}
    res = native.evaluate(term)
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(skeleton or []), "ordered_parts": []}
    return res


def _schema_attr(sub, name: str, attr: str):
    for n in sub.nodes(_CODEBOOK_TYPE):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return at.get(attr)
    return None


def _signature_width(sub, name: str) -> int:
    """How many relations the schema's OWN held `signature` requires — read
    straight off the seed data (never a Python literal). Used to gate a
    `plan` step on FULL coverage of that schema's own relations (order-
    independent — `ShapeDecode`'s `covers` is a per-relation SET membership
    test, unaffected by list order; `shape_fit`, by contrast, anti-unifies
    the residual/signature PREFIXES POSITIONALLY, so it is NOT a reliable
    full-vs-partial gate once a residual has been reordered by an earlier
    covering step — see the module honesty note). A PARTIAL cover (this
    story earns some but not all of a trope's own required relations) is an
    honest non-match, not a weaker version of the trope."""
    sig = _schema_attr(sub, name, "signature")
    try:
        return len(json.loads(sig)) if isinstance(sig, str) else len(sig or [])
    except Exception:
        return 0


# --------------------------------------------------------------------------- #
#  MECHANICAL SIGNALS — each an EXISTENCE check over already-committed graph
#  facts (the same shape narrative_structure._slot_token already uses). These
#  build TOKENS; they never assign a trope name.
# --------------------------------------------------------------------------- #
def _has_role(arc: dict, role: str) -> bool:
    return any(r.get("role") == role for r in (arc.get("roles") or []))


def _role_order(arc: dict, role: str) -> Optional[int]:
    for r in arc.get("roles") or []:
        if r.get("role") == role:
            return r.get("order")
    return None


def _causal_evidence(graph: dict, order: Optional[int]) -> Optional[dict]:
    """A `causal` record (inference_generation.resolve_causal_gap's own,
    already-committed) minted BECAUSE its physical-effect schema fired,
    whose gap starts at this sentence order -- the INDIRECT-mechanism
    signal's evidence, reused verbatim."""
    if order is None:
        return None
    for rec in graph.get("causal") or []:
        if rec.get("minted") and (rec.get("gap") or {}).get("i") == order:
            return rec
    return None


def _blocking_evidence(sub, entity: str) -> Optional[dict]:
    """The BLOCKED signal, read GRAPH-NATIVE off the durable `blocked_gap`
    marker `inference_generation.resolve_precondition_gap` stamps on the
    entity's SmEntity node when it mints a precondition gap (the direct route
    was genuinely blocked). Replaces the transient `graph['blocking']` record:
    the marker is on the node now, so a precondition gap minted for entity X is
    graph-readable directly."""
    for n in sub.nodes("SmEntity"):
        at = sub.node(n)["attrs"]
        if at.get("name") == entity and at.get("blocked_gap") == 1:
            return {"minted": True, "entity": entity, "node": _v(n),
                    "gap": {"entity": entity}}
    return None


def _incremental_evidence(sub, order: Optional[int]) -> Optional[dict]:
    """The INCREMENTAL signal, read GRAPH-NATIVE: does the solution sentence
    carry a change-of-state SmEvent whose tracked entity is PLURAL
    (`coref_number == 'plural'`) -- an honest, imperfect PROXY for "repeated
    small action" (see module docstring), never a lexical "one by one" match.
    `situation_model_reader.ingest_predication` now stamps the tracked
    entity's `coref_number` durably onto the SmEvent, and `reading_drive`'s
    spine stage stamps each SmEvent's `sentence_order`, so the plural-affected-
    entity signal is read off the event node itself -- replacing the transient
    per-predication ingest `state` dict."""
    if order is None:
        return None
    for n in sub.nodes("SmEvent"):
        at = sub.node(n)["attrs"]
        so = at.get("sentence_order")
        if so is None:
            continue
        try:
            same = int(so) == int(order)
        except (TypeError, ValueError):
            same = False
        if same and at.get("coref_number") == "plural":
            return {"event": _v(n), "sentence_order": int(order),
                    "coref_number": "plural"}
    return None


# --------------------------------------------------------------------------- #
#  TOKEN BUILD — one arc -> its present-signal token set + the evidence each
#  token traces back to (for the graph-checkable mint below).
# --------------------------------------------------------------------------- #
_TOKEN_ORDER = ("TROPE_PROBLEM", "TROPE_BLOCKED", "TROPE_INDIRECT",
               "TROPE_INCREMENTAL", "TROPE_RESOLUTION")


def _build_tokens(sub, graph: dict, arc: dict, unit=None) -> tuple:
    entity = arc.get("entity")
    solution_order = _role_order(arc, "solution")
    evidence: dict = {}

    if _has_role(arc, "problem"):
        node = ns._existing_role(sub, entity, _role_order(arc, "problem"), "problem", unit)
        evidence["TROPE_PROBLEM"] = {"kind": "NarrativeRole", "node": node,
                                     "note": "arc carries a 'problem' role"}
    blocked = _blocking_evidence(sub, entity)
    if blocked is not None:
        evidence["TROPE_BLOCKED"] = {"kind": "precondition_gap", "record": blocked,
                                     "note": "a precondition/blocking gap was minted for %r" % entity}
    causal = _causal_evidence(graph, solution_order)
    if causal is not None:
        node = ns._existing_role(sub, entity, solution_order, "solution", unit)
        evidence["TROPE_INDIRECT"] = {"kind": "NarrativeRole+causal", "node": node,
                                      "record": causal,
                                      "note": "solution's outgoing causal edge traces to "
                                              "physical-effect schema %r" % causal.get("schema")}
    incremental = _incremental_evidence(sub, solution_order)
    if incremental is not None:
        node = ns._existing_role(sub, entity, solution_order, "solution", unit)
        evidence["TROPE_INCREMENTAL"] = {"kind": "NarrativeRole+ingest", "node": node,
                                         "record": incremental,
                                         "note": "solution sentence's ingest carries a plural "
                                                 "affected entity"}
    if _has_role(arc, "resolution"):
        node = ns._existing_role(sub, entity, _role_order(arc, "resolution"), "resolution", unit)
        evidence["TROPE_RESOLUTION"] = {"kind": "NarrativeRole", "node": node,
                                        "note": "arc carries a 'resolution' role"}

    tokens = [t for t in _TOKEN_ORDER if t in evidence]
    return tokens, evidence


# --------------------------------------------------------------------------- #
#  LABEL — a citable TV-Tropes name/definition for an ALREADY-DECIDED trope.
#  Mechanical dictionary lookup; never decides WHICH trope fired.
# --------------------------------------------------------------------------- #
def _teacher():
    global _TEACHER, _TEACHER_LOADED
    if not _TEACHER_LOADED:
        _TEACHER_LOADED = True
        try:
            from domains.tropes_teacher import TropesTeacher
            _TEACHER = TropesTeacher.from_cache()
        except Exception:
            _TEACHER = None
    return _TEACHER


def _label_for(sub, trope_name: str) -> dict:
    candidates = _schema_attr(sub, trope_name, "label_candidates")
    try:
        candidates = json.loads(candidates) if isinstance(candidates, str) else (candidates or [])
    except Exception:
        candidates = []
    teacher = _teacher()
    if teacher is not None:
        for phrase in candidates:
            rec = teacher.lookup(phrase)
            if rec is not None:
                return {"source": "tvtropes", "name": rec.get("name"),
                       "definition": rec.get("definition"), "searched": phrase}
    return {"source": "self_authored", "name": trope_name,
           "definition": _schema_attr(sub, trope_name, "note"), "searched": None}


# --------------------------------------------------------------------------- #
#  MINT — a recognised trope becomes a `Trope` node with `instantiates_trope`
#  edges FROM the evidence nodes that earned its covered tokens (GRAPH-
#  CHECKABLE: never a free-floating label). Reuses discourse_coherence.
#  _mint_edge verbatim for the write.
# --------------------------------------------------------------------------- #
def _existing_trope(sub, entity: str, name: str, unit=None):
    for n in sub.nodes("Trope"):
        at = sub.node(n)["attrs"]
        if at.get("entity") == entity and at.get("name") == name \
                and (unit is None or at.get("unit") == unit):
            return n
    return None


def _mint_evidence_node(sub, native, kind: str, payload: dict):
    flat = {k: v for k, v in payload.items()
           if isinstance(v, (str, int, float, bool)) or v is None}
    en = sub.add_node("TropeEvidence", {"kind": kind, "record_json": json.dumps(payload, default=str),
                                        **flat})
    return en


def _mint_trope(agent, sub, native, entity: str, name: str, fit: int,
                covered_tokens: list, evidence: dict, unit=None) -> dict:
    existing = _existing_trope(sub, entity, name, unit)
    if existing is not None:
        return {"entity": entity, "name": name, "minted": False, "reason": "already held",
               "node": _v(existing), "_node_obj": existing, "theme": _schema_attr(sub, name, "theme")}
    label = _label_for(sub, name)
    theme_line = _schema_attr(sub, name, "theme")
    tr_attrs = {"entity": entity, "name": name, "shape_fit": fit,
                "covered_tokens": list(covered_tokens),
                "theme": theme_line, "label_source": label["source"],
                "label_name": label["name"], "label_definition": label["definition"]}
    if unit is not None:
        tr_attrs["unit"] = unit
    tn = sub.add_node("Trope", tr_attrs)
    evidence_nodes = []
    for tok in covered_tokens:
        ev = evidence.get(tok)
        if ev is None:
            continue
        src_node = ev.get("node")
        if src_node is not None:
            dc._mint_edge(sub, native, src_node, tn, "instantiates_trope",
                          {"token": tok, "note": ev.get("note")})
            evidence_nodes.append({"token": tok, "kind": ev.get("kind"), "node": _v(src_node)})
        elif ev.get("record") is not None:
            en = _mint_evidence_node(sub, native, ev.get("kind"), ev.get("record"))
            dc._mint_edge(sub, native, en, tn, "instantiates_trope",
                          {"token": tok, "note": ev.get("note")})
            evidence_nodes.append({"token": tok, "kind": ev.get("kind"), "node": _v(en)})
    return {"entity": entity, "name": name, "minted": True, "shape_fit": fit,
           "covered_tokens": list(covered_tokens), "theme": theme_line, "label": label,
           "evidence": evidence_nodes, "node": _v(tn), "_node_obj": tn}


def _learned_theme_line(tokens: list) -> str:
    """A GENERIC theme, ABSTRACTED from the arc's own recurring structure — NOT a
    canned per-trope seed gloss (there is none for a learned trope). Reads off the
    signal tokens the arc actually earned (each names a structural feature the
    reader already committed): a problem faced, a blocked path, an indirect
    mechanism, an incremental effort, a reached resolution. Honest: this is a
    COARSE structural abstraction, not a hand-authored moral — the price of
    learning a trope the seed never held."""
    phrase = {"TROPE_PROBLEM": "a problem is faced",
              "TROPE_BLOCKED": "the direct path is blocked",
              "TROPE_INDIRECT": "it is met by an indirect means",
              "TROPE_INCREMENTAL": "through repeated small effort",
              "TROPE_RESOLUTION": "and reaches a resolution"}
    parts = [phrase[t] for t in _TOKEN_ORDER if t in tokens]
    body = ", ".join(parts) if parts else "a recurring structure recurs"
    return ("A recurring narrative structure the reader learned from this story: "
            + body + " -- an abstracted structural pattern, coarser than a "
            "hand-authored moral.")


def _existing_signature_trope(sub, signature: str):
    """A held ShapeSignatureTrope whose signature EXACTLY matches -- so a learned
    quantum is minted ONCE (idempotent codebook growth, the sd_mint_quantum
    'no minted edge yet' fixpoint-safety idiom, one level up)."""
    for n in sub.nodes(_CODEBOOK_TYPE):
        if sub.node(n)["attrs"].get("signature") == signature:
            return n
    return None


def _learned_trope_name(tokens: list) -> str:
    """A stable structural NAME for a learned trope, keyed on its OWN signal
    tokens (the residual structure that earned it) -- never a hardcoded trope
    string. tropes_teacher supplies a citable label AFTER the mint (a lookup on
    an already-decided structure), exactly as the seeded path names a decided
    trope; this is only the graph key."""
    return "LEARNED_" + "_".join(t.replace("TROPE_", "") for t in
                                 [x for x in _TOKEN_ORDER if x in tokens])


def _mint_learned_trope(agent, sub, native, residual_tokens: list) -> Optional[dict]:
    """DYNAMIC QUANTIZATION at the ARC/TROPE level (the sd_mint_quantum precedent,
    seeds/shape_decode_loop.json, one level up): the arc's structure is a RESIDUAL
    -- a recurring pattern of signal tokens NO held trope covers. Rather than force
    it onto a near-miss seeded trope (a partial cover is an honest non-match) or
    leave the arc trope-less, MINT A NEW ShapeSignatureTrope QUANTUM whose signature
    IS that residual structure. The DECISION that there IS a residual is ShapeDecode's
    own verdict (the tokens no full-coverage plan step claimed); this only writes the
    new codebook node (mechanical graph I/O, exactly as ensure_codebook / the sd loop's
    grow_part_library add codebook nodes). Idempotent: a signature already held is not
    re-minted (the codebook grows once per novel structure). Returns the learned
    schema's name + node, or None if nothing to learn."""
    sig_tokens = [t for t in _TOKEN_ORDER if t in residual_tokens]
    if not sig_tokens:
        return None
    signature = json.dumps([[t] for t in sig_tokens])
    existing = _existing_signature_trope(sub, signature)
    if existing is not None:
        return {"name": sub.node(existing)["attrs"].get("name"), "node": _v(existing),
                "minted": False, "reason": "learned quantum already held"}
    name = _learned_trope_name(sig_tokens)
    attrs = {"name": name, "kind": "trope", "signature": signature, "learned": 1,
             "theme": _learned_theme_line(sig_tokens),
             "label_candidates": json.dumps([]),
             "note": ("A trope LEARNED from an arc whose structure no seeded trope "
                      "covered -- dynamic quantization at the trope level: the residual "
                      "structure %s minted its own ShapeSignatureTrope quantum." % sig_tokens)}
    nid = sub.add_node(_CODEBOOK_TYPE, attrs)
    return {"name": name, "node": _v(nid), "minted": True, "signature": signature}


def _existing_theme(sub, entity: str, unit=None):
    for n in sub.nodes("Theme"):
        at = sub.node(n)["attrs"]
        if at.get("entity") == entity and (unit is None or at.get("unit") == unit):
            return n
    return None


def _mint_theme(sub, native, entity: str, tropes: list, unit=None) -> Optional[dict]:
    """The abstract moral, read off the recognised trope(s)' own held
    `theme` line + traced to each via `expresses_theme` -- never invented
    per-story. No trope recognised -> no Theme (honest null)."""
    if not tropes:
        return None
    existing = _existing_theme(sub, entity, unit)
    if existing is not None:
        return {"entity": entity, "minted": False, "reason": "already held",
               "node": _v(existing)}
    lines = [t["theme"] for t in tropes if t.get("theme")]
    th_attrs = {"entity": entity, "lines": lines, "tropes": [t["name"] for t in tropes]}
    if unit is not None:
        th_attrs["unit"] = unit
    thn = sub.add_node("Theme", th_attrs)
    for t in tropes:
        node_obj = t.get("_node_obj")
        if node_obj is not None:
            dc._mint_edge(sub, native, node_obj, thn, "expresses_theme", {"trope": t["name"]})
    return {"entity": entity, "minted": True, "node": _v(thn), "lines": lines,
           "tropes": [t["name"] for t in tropes]}


# --------------------------------------------------------------------------- #
#  THE DRIVER — recognise trope(s) + theme over an already-built arc.
# --------------------------------------------------------------------------- #
def recognize_tropes_and_theme(agent, graph: dict, unit=None) -> dict:
    """Recognise the trope(s) + theme over the narrative arc(s)
    `narrative_structure.recognize_narrative_structure` already built
    (`graph['narrative_arc']['arcs']`). Derives no new comprehension meaning:
    every token is an existence check over facts other components' own
    collapses already committed (the arc's roles, the causal/blocking
    records, the situation-model ingest state). Returns
    {results: [{entity, tokens, tropes: [...], theme}]} — an arc with no
    mechanical trope signal contributes an honest null (no forced trope)."""
    ensure_codebook(agent)
    sub, native = _resolve(agent)
    arcs = (graph.get("narrative_arc") or {}).get("arcs") or []

    results = []
    for arc in arcs:
        entity = arc.get("entity")
        tokens, evidence = _build_tokens(sub, graph, arc, unit)
        if not tokens:
            results.append({"entity": entity, "tokens": [], "tropes": [], "theme": None,
                           "reason": "no mechanical trope signal present on this arc -- "
                                     "honest null, nothing fabricated"})
            continue
        tropes, covered_tokens = _decode_and_mint(agent, sub, native, entity,
                                                   tokens, evidence, unit)
        # SD-LOOP LEARNING (2026-07-07): an arc OUTSIDE every seeded trope (NO seeded
        # trope covered any of its structure -- `tropes` empty, yet it DOES carry
        # signal tokens) is a RESIDUAL the held codebook does not know. Rather than
        # leave it trope-less (the old honest null), MINT a LEARNED ShapeSignatureTrope
        # quantum FROM that residual structure (dynamic quantization at the trope
        # level, the sd_mint_quantum precedent) and mint its Trope -- so the reader
        # reads ANY story via a learned category. SCOPED to fully-uncovered arcs: an
        # arc that DID instantiate a seeded trope (e.g. persistence) keeps its verdict
        # and its leftover token stays an honest null (byte-identical reports). Crow:
        # fully covered by the seeded tropes -> nothing learned.
        residual_tokens = [t for t in tokens if t not in covered_tokens]
        learned = None
        if not tropes and residual_tokens:
            learned = _mint_learned_trope(agent, sub, native, residual_tokens)
            if learned is not None:
                # THE MINT IS THE RECOGNITION (sd_mint_quantum precedent): the learned
                # quantum's signature IS the residual, so it covers it EXACTLY by
                # construction -- mint the learned Trope directly over the residual
                # tokens (a full-coverage mint), rather than re-decode. A blind
                # re-decode would let the set-cover greedily reassign a residual token
                # to a WIDER seeded schema that only PARTIALLY covers it (then gets
                # width-dropped) -- starving the exact learned quantum. Minting from
                # the residual the decode itself reported avoids that ambiguity while
                # keeping the DECISION (which tokens are residual) the decode's own.
                sig_tokens = [t for t in _TOKEN_ORDER if t in residual_tokens]
                tr = _mint_trope(agent, sub, native, entity, learned["name"], 1,
                                 sig_tokens, evidence, unit)
                tropes.append(tr)
                covered_tokens = sorted(set(covered_tokens) | set(sig_tokens))
                residual_tokens = [t for t in tokens if t not in covered_tokens]
        theme = _mint_theme(sub, native, entity, tropes, unit)
        results.append({"entity": entity, "tokens": tokens, "tropes": tropes,
                        "residual": residual_tokens, "learned": learned, "theme": theme})
    return {"results": results}


def _decode_and_mint(agent, sub, native, entity, tokens, evidence, unit):
    """Decode the arc's token set against the CURRENT ShapeSignatureTrope codebook
    (seeded + any learned quanta) and mint a Trope per FULL-coverage plan step.
    Returns (tropes, covered_tokens). A partial cover is an honest non-match
    (never a weaker trope) -- its tokens stay in the residual. The WHICH-trope
    decision is ShapeDecode's own set-cover verdict, read off its plan."""
    res = _decode(agent, [[t] for t in tokens])
    plan = res.get("plan") or []
    tropes = []
    covered_tokens: set = set()
    for step in plan:
        name = step.get("part")
        covered = [c[0] if isinstance(c, (list, tuple)) and c else c for c in (step.get("covers") or [])]
        fit = step.get("shape_fit", 0)
        if not name or not covered:
            continue
        if len(covered) < _signature_width(sub, name):
            continue
        tropes.append(_mint_trope(agent, sub, native, entity, name, fit, covered, evidence, unit))
        covered_tokens.update(covered)
    return tropes, sorted(covered_tokens)


# --------------------------------------------------------------------------- #
#  READ BACK — plain graph query (no decision), for callers/gates/demos.
# --------------------------------------------------------------------------- #
def read_tropes(agent, entity: Optional[str] = None) -> list:
    sub, _ = _resolve(agent)
    out = []
    for n in sub.nodes("Trope"):
        at = dict(sub.node(n)["attrs"])
        if entity is not None and at.get("entity") != entity:
            continue
        out.append(at)
    return out


def read_theme(agent, entity: str, unit=None) -> Optional[dict]:
    sub, _ = _resolve(agent)
    n = _existing_theme(sub, entity, unit)
    if n is None:
        return None
    return dict(sub.node(n)["attrs"])


def trope_evidence(agent, trope_node) -> list:
    """Walk BACKWARD from a `Trope` node's own `instantiates_trope` incoming
    edges to the graph structure that earned it -- the GRAPH-CHECKABLE trace
    a caller/gate asserts against. Pure graph read, no decision."""
    sub, _ = _resolve(agent)
    out = []
    for n in sub.nodes("NarrativeRole"):
        for nb in sub.neighbours(n, "instantiates_trope"):
            if _v(nb) == _v(trope_node):
                out.append({"kind": "NarrativeRole", "node": _v(n), "attrs": dict(sub.node(n)["attrs"])})
    for n in sub.nodes("TropeEvidence"):
        for nb in sub.neighbours(n, "instantiates_trope"):
            if _v(nb) == _v(trope_node):
                out.append({"kind": "TropeEvidence", "node": _v(n), "attrs": dict(sub.node(n)["attrs"])})
    return out


# =========================================================================== #
#  SEMANTIC (content-relation) TROPES — the MORAL from CONTENT RELATIONS, not
#  arc shape. Where the arc-shape path above learns LEARNED_PROBLEM /
#  LEARNED_INCREMENTAL (a COARSE structural pattern), this path decodes the
#  PARTICIPANT-RELATION pattern (who acts on whom, in what order) + the OUTCOME
#  VALENCE (which protagonist ends acting/gaining vs passive), read GRAPH-NATIVE
#  off the situation model's own already-committed SmEvent nodes, against a
#  dedicated ShapeSignatureSemanticTrope codebook that GROWS via the same
#  sd_mint_quantum loop (one axis across). Reuses nested_reading's own
#  RETURN_ACTION reversal (as the REVERSAL token) + tropes_teacher (for naming).
# =========================================================================== #
def ensure_semantic_codebook(agent) -> None:
    """Idempotently install the semantic-trope codebook (guarded by a graph-
    resident Seed{id:'semantic_tropes'} sentinel — the same idiom
    ensure_codebook uses). Mechanical seed I/O."""
    sub, _ = _resolve(agent)
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == "semantic_tropes":
            return
    with open(_SEM_CODEBOOK_SEED) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": "semantic_tropes",
                          "version": manifest.get("version", "1.0.0")})


def _sem_schema_attr(sub, name: str, attr: str):
    for n in sub.nodes(_SEM_CODEBOOK_TYPE):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return at.get(attr)
    return None


def _sem_signature_width(sub, name: str) -> int:
    sig = _sem_schema_attr(sub, name, "signature")
    try:
        return len(json.loads(sig)) if isinstance(sig, str) else len(sig or [])
    except Exception:
        return 0


# --------------------------------------------------------------------------- #
#  CONTENT EVENTS — the participant-relation records, read GRAPH-NATIVE off the
#  situation model's own SmEvent nodes (idx_protagonist=agent, arg1=patient,
#  verb via WordNet lexname). A pure query; no meaning decided here.
# --------------------------------------------------------------------------- #
def _lexname(agent, verb) -> Optional[str]:
    """The verb's WordNet lexicographer-file class (verb.communication /
    verb.possession / verb.consumption / ...), read off the SAME
    situation_model_reader.eventive_membership the generic-event mint uses —
    NOT a hardcoded verb list."""
    if not verb:
        return None
    try:
        return smr.eventive_membership(agent, str(verb)).get("lexname")
    except Exception:
        return None


def _content_events(agent) -> list:
    """Every SmEvent as a participant-relation record, in story order. Order key
    is (unit, t) — unit node-ids increase with story order, t within a unit —
    so a cross-episode reversal reads in the right direction. A mechanical read
    off already-committed nodes."""
    sub, _ = _resolve(agent)
    evs = []
    for n in sub.nodes("SmEvent"):
        at = sub.node(n)["attrs"]
        a = at.get("idx_protagonist")
        b = at.get("arg1")
        verb = at.get("verb") or at.get("surface")
        try:
            unit_k = int(at.get("unit")) if at.get("unit") is not None else -1
        except (TypeError, ValueError):
            unit_k = -1
        try:
            t_k = float(at.get("t")) if at.get("t") is not None else 0.0
        except (TypeError, ValueError):
            t_k = 0.0
        evs.append({"node": n, "agent": a, "patient": b, "verb": verb,
                    "lex": _lexname(agent, verb), "order": (unit_k, t_k)})
    evs.sort(key=lambda e: e["order"])
    return evs


def _final_agent(events: list) -> Optional[str]:
    """The OUTCOME-VALENCE read: the agent of the LAST event — the protagonist
    who ends ACTING/gaining. The one left passive at the end is the thwarted
    party. A coarse but graph-native met/thwarted signal (honest note in the
    ledger)."""
    return events[-1]["agent"] if events else None


def _is_comm(lex) -> bool:
    return lex == "verb.communication"


# --------------------------------------------------------------------------- #
#  CONTENT TOKENS — each an EXISTENCE check over the participant-relation
#  records (the SAME 'mechanical signal -> single token' shape _build_tokens
#  uses one axis across). Each returns (present, evidence) with the SmEvent
#  nodes that earned it. NONE names a moral.
# --------------------------------------------------------------------------- #
def _reversal_signal(events: list) -> Optional[dict]:
    """REVERSAL (reciprocity): an earlier NON-communication DEED A->B and a
    later reversed DEED B->A over the same pair — nested_reading's own
    RETURN_ACTION reversal, DEEDS only (words excluded) so a mutual-flattery
    exchange is not mistaken for a returned kindness."""
    deeds = [e for e in events if e["agent"] and e["patient"]
             and e["agent"] != e["patient"] and not _is_comm(e["lex"])]
    for i in range(len(deeds)):
        a, b = deeds[i]["agent"], deeds[i]["patient"]
        for j in range(len(deeds)):
            if j == i:
                continue
            if deeds[j]["agent"] == b and deeds[j]["patient"] == a:
                early, late = (deeds[i], deeds[j]) if deeds[i]["order"] <= deeds[j]["order"] \
                    else (deeds[j], deeds[i])
                return {"nodes": [early["node"], late["node"]], "a": a, "b": b,
                        "note": "deed (%s -> %s) is later reversed as (%s -> %s) — "
                                "the actor/recipient role-reversal" % (a, b, b, a)}
    return None


def _speech_deed_signal(events: list) -> Optional[dict]:
    """SPEECH_DEED (flattery): ONE agent A does a verb.communication act toward
    a SECOND entity B, then a LATER non-communication eventive act — talk
    converted into a deed."""
    for i, e in enumerate(events):
        if not _is_comm(e["lex"]):
            continue
        a, b = e["agent"], e["patient"]
        if not a or not b or a == b:
            continue
        for f in events[i + 1:]:
            if f["agent"] == a and not _is_comm(f["lex"]):
                return {"nodes": [e["node"], f["node"]], "a": a, "b": b,
                        "note": "agent %r speaks to %r then converts talk into the deed %r"
                                % (a, b, f["verb"])}
    return None


def _store_consume_signal(events: list) -> Optional[dict]:
    """STORE_CONSUME (foresight): ONE agent A does a verb.possession (store) act
    over an object X and a LATER verb.consumption act over the SAME object X —
    provision then consumption of its own store."""
    for i, e in enumerate(events):
        if e["lex"] != "verb.possession" or not e["agent"] or not e["patient"]:
            continue
        a, x = e["agent"], e["patient"]
        for f in events[i + 1:]:
            if f["agent"] == a and f["patient"] == x and f["lex"] == "verb.consumption":
                return {"nodes": [e["node"], f["node"]], "a": a, "x": x,
                        "note": "agent %r stores %r (possession) then consumes the same %r"
                                % (a, x, x)}
    return None


def _mutual_speech_signal(events: list) -> Optional[dict]:
    """MUTUAL_SPEECH: A speaks to B and B speaks to A (a communication reversal)
    — NOT a returned kindness, NOT a seeded moral: an UNSEEDED content relation
    that the sd loop must LEARN (the general novel-content path)."""
    comm = [e for e in events if _is_comm(e["lex"]) and e["agent"] and e["patient"]
            and e["agent"] != e["patient"]]
    for i in range(len(comm)):
        a, b = comm[i]["agent"], comm[i]["patient"]
        for j in range(len(comm)):
            if j != i and comm[j]["agent"] == b and comm[j]["patient"] == a:
                return {"nodes": [comm[i]["node"], comm[j]["node"]], "a": a, "b": b,
                        "note": "agent %r speaks to %r and %r speaks back to %r — "
                                "mutual words, no deed returned" % (a, b, b, a)}
    return None


_CONTENT_SIGNALS = (
    ("REVERSAL", _reversal_signal),
    ("SPEECH_DEED", _speech_deed_signal),
    ("STORE_CONSUME", _store_consume_signal),
    ("MUTUAL_SPEECH", _mutual_speech_signal),
)


def _build_content_tokens(agent) -> tuple:
    """The story's content-token set + the SmEvent evidence each token traces
    back to. Each token is an existence check over participant relations; NONE
    is a moral name. Returns (tokens, evidence, final_agent)."""
    events = _content_events(agent)
    final_actor = _final_agent(events)
    evidence: dict = {}
    tokens = []
    for name, fn in _CONTENT_SIGNALS:
        sig = fn(events)
        if sig is not None:
            evidence[name] = sig
            tokens.append(name)
    return tokens, evidence, final_actor


# --------------------------------------------------------------------------- #
#  DECODE + MINT — the SAME ShapeDecode set-cover + sd_mint_quantum shape the
#  arc-shape path uses, pointed at the ShapeSignatureSemanticTrope codebook.
# --------------------------------------------------------------------------- #
def _decode_semantic(agent, skeleton: list) -> dict:
    _, native = _resolve(agent)
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": [list(x) for x in (skeleton or [])]},
            "codebook_type": _SEM_CODEBOOK_TYPE, "beam": 1, "max_steps": 6, "cand_k": 4}
    res = native.evaluate(term)
    if not isinstance(res, dict):
        return {"plan": [], "residual": list(skeleton or []), "ordered_parts": []}
    return res


def _sem_label_for(sub, name: str) -> dict:
    candidates = _sem_schema_attr(sub, name, "label_candidates")
    try:
        candidates = json.loads(candidates) if isinstance(candidates, str) else (candidates or [])
    except Exception:
        candidates = []
    teacher = _teacher()
    if teacher is not None:
        for phrase in candidates:
            rec = teacher.lookup(phrase)
            if rec is not None:
                return {"source": "tvtropes", "name": rec.get("name"),
                        "definition": rec.get("definition"), "searched": phrase}
    return {"source": "self_authored", "name": name,
            "definition": _sem_schema_attr(sub, name, "note"), "searched": None}


def _existing_semantic_trope(sub, name: str, protagonist):
    for n in sub.nodes("SemanticTrope"):
        at = sub.node(n)["attrs"]
        if at.get("name") == name and at.get("protagonist") == protagonist:
            return n
    return None


def _mint_semantic_trope(agent, sub, native, name: str, protagonist, valence_outcome: str,
                         covered_tokens: list, evidence: dict) -> dict:
    existing = _existing_semantic_trope(sub, name, protagonist)
    theme = _sem_schema_attr(sub, name, "theme")
    line = _sem_schema_attr(sub, name, "line")
    valence = _sem_schema_attr(sub, name, "valence")
    learned = _sem_schema_attr(sub, name, "learned")
    if existing is not None:
        return {"name": name, "protagonist": protagonist, "minted": False,
                "reason": "already held", "node": _v(existing), "_node_obj": existing,
                "theme": theme, "line": line, "valence": valence,
                "learned": bool(learned), "covered_tokens": list(covered_tokens)}
    label = _sem_label_for(sub, name)
    attrs = {"name": name, "protagonist": protagonist, "theme": theme, "line": line,
             "valence": valence, "outcome": valence_outcome,
             "covered_tokens": list(covered_tokens),
             "label_source": label["source"], "label_name": label["name"],
             "label_definition": label["definition"], "learned": 1 if learned else 0}
    tn = sub.add_node("SemanticTrope", attrs)
    for tok in covered_tokens:
        ev = evidence.get(tok)
        if not ev:
            continue
        for src in ev.get("nodes") or []:
            dc._mint_edge(sub, native, src, tn, "instantiates_semantic_trope",
                          {"token": tok, "note": ev.get("note")})
    return {"name": name, "protagonist": protagonist, "minted": True, "theme": theme,
            "line": line, "valence": valence, "outcome": valence_outcome,
            "learned": bool(learned), "label": label,
            "covered_tokens": list(covered_tokens), "node": _v(tn), "_node_obj": tn}


def _existing_learned_semantic(sub, signature: str):
    for n in sub.nodes(_SEM_CODEBOOK_TYPE):
        if sub.node(n)["attrs"].get("signature") == signature:
            return n
    return None


def _learned_semantic_name(tokens: list) -> str:
    return "LEARNED_" + "_".join(tokens)


def _learned_semantic_theme_line(tokens: list) -> str:
    """A GENERIC content-relation theme, abstracted from the participant tokens
    the story actually earned — richer than an arc-SHAPE abstraction (it names
    WHO-acts-on-WHOM structure, not problem/resolution), but still COARSE next to
    a hand-authored moral (the honest price of learning a moral the seed never
    held)."""
    phrase = {"REVERSAL": "one party returns another's deed",
              "SPEECH_DEED": "an actor turns words into a deed",
              "STORE_CONSUME": "an actor provides then consumes its own store",
              "MUTUAL_SPEECH": "two parties exchange words with no deed returned"}
    parts = [phrase.get(t, t.lower().replace("_", " ")) for t in tokens]
    body = "; ".join(parts) if parts else "a recurring content relation recurs"
    return ("A content-relation moral the reader LEARNED from this story: "
            + body + " -- abstracted from the participant relations + outcome "
            "valence, coarser than a hand-authored moral.")


def _mint_learned_semantic_trope(agent, sub, native, residual_tokens: list) -> Optional[dict]:
    """DYNAMIC QUANTIZATION at the CONTENT level (the sd_mint_quantum precedent,
    one axis across from the arc-shape learned quantum): a content relation NO
    seeded semantic pattern covers is a RESIDUAL — mint a NEW
    ShapeSignatureSemanticTrope quantum whose signature IS that residual content
    relation. Idempotent (a signature already held is not re-minted). Returns the
    learned schema's name/node, or None."""
    toks = list(residual_tokens or [])
    if not toks:
        return None
    signature = json.dumps([[t] for t in toks])
    existing = _existing_learned_semantic(sub, signature)
    if existing is not None:
        return {"name": sub.node(existing)["attrs"].get("name"), "node": _v(existing),
                "minted": False, "reason": "learned quantum already held"}
    name = _learned_semantic_name(toks)
    attrs = {"name": name, "kind": "semantic_trope", "signature": signature, "learned": 1,
             "theme": _learned_semantic_theme_line(toks), "valence": "learned",
             "line": _learned_semantic_theme_line(toks),
             "label_candidates": json.dumps([]),
             "note": ("A semantic trope LEARNED from a content relation no seeded "
                      "pattern covered — dynamic quantization at the content level: the "
                      "residual %s minted its own ShapeSignatureSemanticTrope quantum." % toks)}
    nid = sub.add_node(_SEM_CODEBOOK_TYPE, attrs)
    return {"name": name, "node": _v(nid), "minted": True, "signature": signature}


def _decode_and_mint_semantic(agent, sub, native, tokens, evidence, final_actor):
    """Decode the content tokens against the CURRENT ShapeSignatureSemanticTrope
    codebook (seeded + learned) and mint a SemanticTrope per FULL-coverage plan
    step. The WHICH-trope decision is ShapeDecode's own set-cover verdict."""
    res = _decode_semantic(agent, [[t] for t in tokens])
    plan = res.get("plan") or []
    tropes = []
    covered: set = set()
    for step in plan:
        name = step.get("part")
        cov = [c[0] if isinstance(c, (list, tuple)) and c else c for c in (step.get("covers") or [])]
        if not name or not cov:
            continue
        if len(cov) < _sem_signature_width(sub, name):
            continue
        protagonist = _protagonist_of(evidence, cov, final_actor)
        outcome = _outcome_note(evidence, cov, final_actor)
        tropes.append(_mint_semantic_trope(agent, sub, native, name, protagonist,
                                            outcome, cov, evidence))
        covered.update(cov)
    return tropes, sorted(covered)


def _protagonist_of(evidence: dict, covered: list, final_actor) -> Optional[str]:
    """The pattern's protagonist A (the actor the content relation is about),
    read off the covered tokens' own evidence — the flatterer/provider/returner."""
    for tok in covered:
        ev = evidence.get(tok)
        if ev and ev.get("a"):
            return ev.get("a")
    return final_actor


def _outcome_note(evidence: dict, covered: list, final_actor) -> str:
    """The computed OUTCOME VALENCE cross-check: who ends acting/gaining (the
    final actor) vs the other party left passive. Coarse but graph-native."""
    a = _protagonist_of(evidence, covered, final_actor)
    if final_actor and a and final_actor == a:
        return "protagonist %r is the final actor (acts/gains); the other party is left passive" % a
    if final_actor:
        return "the final actor is %r" % final_actor
    return "no final actor read"


def recognize_semantic_trope(agent) -> dict:
    """Recognise the CONTENT-RELATION moral(s) over the situation model the
    reader already built (its SmEvent participant relations + outcome valence).
    Full-coverage content tokens decode to a seeded semantic trope (a RICH moral,
    read off the winning schema's own theme/line — reciprocity/flattery/
    foresight); a content relation NO seeded pattern covers mints a LEARNED
    semantic quantum (the sd_mint_quantum precedent, content level) and mints its
    SemanticTrope. tropes_teacher NAMES an already-decided trope. No content
    signal -> honest null. The WHICH-moral decision is ShapeDecode's own verdict;
    no moral-name literal drives the mint."""
    ensure_semantic_codebook(agent)
    sub, native = _resolve(agent)
    tokens, evidence, final_actor = _build_content_tokens(agent)
    if not tokens:
        return {"tropes": [], "tokens": [], "learned": None, "final_actor": final_actor,
                "reason": "no content-relation signal on the situation model — honest null"}
    tropes, covered = _decode_and_mint_semantic(agent, sub, native, tokens, evidence, final_actor)
    residual = [t for t in tokens if t not in covered]
    learned = None
    if residual:
        learned = _mint_learned_semantic_trope(agent, sub, native, residual)
        if learned is not None:
            # THE MINT IS THE RECOGNITION (sd_mint_quantum precedent): the learned
            # quantum's signature IS the residual, covering it EXACTLY. Re-decode so
            # the learned schema's own name/theme is minted onto the SemanticTrope.
            more, cov2 = _decode_and_mint_semantic(agent, sub, native, residual,
                                                   evidence, final_actor)
            tropes.extend(more)
            covered = sorted(set(covered) | set(cov2))
            residual = [t for t in tokens if t not in covered]
    return {"tropes": tropes, "tokens": tokens, "covered": covered, "residual": residual,
            "learned": learned, "final_actor": final_actor}


def read_semantic_tropes(agent, protagonist: Optional[str] = None) -> list:
    """A pure graph read of the minted SemanticTrope nodes. For gates/demos."""
    sub, _ = _resolve(agent)
    out = []
    for n in sub.nodes("SemanticTrope"):
        at = dict(sub.node(n)["attrs"])
        if protagonist is not None and at.get("protagonist") != protagonist:
            continue
        out.append(at)
    return out


def semantic_trope_evidence(agent, trope_node) -> list:
    """Walk BACKWARD from a SemanticTrope node's own instantiates_semantic_trope
    incoming edges to the SmEvent structure that earned it — the graph-checkable
    trace. Pure graph read."""
    sub, _ = _resolve(agent)
    out = []
    for n in sub.nodes("SmEvent"):
        for nb in sub.neighbours(n, "instantiates_semantic_trope"):
            if _v(nb) == _v(trope_node):
                at = dict(sub.node(n)["attrs"])
                out.append({"kind": "SmEvent", "node": _v(n),
                            "agent": at.get("idx_protagonist"), "patient": at.get("arg1"),
                            "verb": at.get("verb")})
    return out


__all__ = ["ensure_codebook", "recognize_tropes_and_theme", "read_tropes",
          "read_theme", "trope_evidence",
          "ensure_semantic_codebook", "recognize_semantic_trope",
          "read_semantic_tropes", "semantic_trope_evidence"]
