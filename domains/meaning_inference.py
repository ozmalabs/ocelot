"""meaning_inference — INFER MEANING FROM CONTEXT for out-of-vocabulary fillers.

reading_review._predication_selectional_incoherence runs a seeded
`SelectionalRestriction` BACKWARD: a KNOWN subject that violates a mental-state
verb's animacy requirement ('the report infers ...') is scored incoherent. It
explicitly SKIPS an OOV/pronoun subject (the `_groundable_noun` guard) — there
is nothing to violate when the filler is unknown.

This module is the FORWARD twin. 'The glarn feared the storm.' — 'feared' is
verb.emotion; a held (verb_class -> requires_class) selectional pair says
verb.emotion admits a noun.person/noun.animal subject; 'glarn' has NO WordNet
sense at all. Instead of silently skipping it, the pair's `requires_class` is
read FORWARD as 'glarn'-s PROVISIONAL semantic type, held as a REVISABLE,
confidence-graded `InferredSense` — the same ReadingBelief shape
`reading_collapse._record_reading_belief` already uses for the passive/stative
collapse (value/confidence/source/revisable; idempotent; a later grounding
supersedes it in one `set_attr`), so a provisional meaning is HELD AND USED,
not a disposable placeholder (contrast `phase_composer_language_rules.py`'s
`context_typed` Concepts, which `read_and_ground.py` treats as permanently
UNGROUNDED and never reconsiders).

ARCHITECTURE BOUNDARY (CLAUDE.md) — ZERO Python decisions:
  · PYTHON (this module) is PURE ANNOTATION, exactly like the reader already
    annotates lexname/PPART via WordNet reads. For every grounded predication
    argument it writes FACTS, unconditionally, never branching on what OTHER
    graph data says:
      - on the filler Concept: `oov` (1.0 iff WordNet has no sense at all —
        a capability read, `reading_review._lexname`) and `is_pronoun` (1.0
        iff the head is in the closed pronoun class — the same structural
        membership test `reading_review._PRONOUNS` already performs).
      - a `PredicationSlot{slot, rel_verb_class, relation}` node per argument:
        `rel_verb_class` is the relation's WordNet verb-class (a capability
        read; simply `None`/null for a non-verb relation like 'of' — NOT
        Python deciding "skip non-verbs", the null just never joins anything
        downstream); `slot` ('subject'/'object') is the argument's POSITIONAL
        role in the predication (`pred[1]`/`pred[2]` — a mechanical structural
        fact fixed by `_ground`'s own template, not a decision this module
        makes). This node is ALWAYS written, whether or not any restriction
        will ever match it.
    There is no `if rel_class in verb_classes` anywhere here — that JOIN is
    the rule's, below. SLICE 3 (morphology) adds `annotate_affix_candidates`,
    the same shape again: an OOV filler's head is mechanically sliced into
    every 2..6-char suffix / 2..4-char prefix (`str` slicing, no regex, no
    preference) and written as `AffixCandidate{affix, position, term}` facts.
    There is no `if affix in {...}` here either — whether any slice means
    something is `infer_sense_from_morphology`'s join against `MorphemeClass`.
  · GRAPH RULE (seeds/meaning_inference.json, Rust `run_rules`) makes the
    WHOLE decision: `infer_sense_mint`/`infer_sense_combine` JOIN a
    PredicationSlot to a `SelectionalClassPair{verb_class, slot,
    requires_class, weight}` row by `Eq(ps.rel_verb_class, cp.verb_class)`
    AND `Eq(ps.slot, cp.slot)` (the graph join that replaces the Python `in`
    test), gated on the filler being OOV and not a pronoun, ABSTAINING when
    the term is already a genuinely grounded Concept (`grounded==1.0` — a flag
    any real grounding process may set; the placeholder Concept
    `_write_predications` mints for EVERY argument, known or not, never
    carries it), and MINTING (when no `InferredSense` yet exists for this
    exact `(term, sense_class)`) or COMBINING (raising `confidence` when one
    already does). `infer_sense_supersede` flips an existing `InferredSense`
    to `status:'superseded'` — ONE `set_attr` — the instant its term becomes
    genuinely grounded. All three are plain `Eq`/`And`/`Not`/`Exists`/
    `NodesOfType`/`Attr`/`Plus` Term-trees; nothing here decides.

Wired ADDITIVELY off the byte-parity path: `reading_collapse.read_clause`
calls `annotate_predication_slots` only `if write` (the exact gate
`_record_reading_belief`'s passive-lean mint already uses), so the frozen
parity corpus (which reads with `write=False`) never touches this module —
new node types only (`PredicationSlot`, `SelectionalClassPair`,
`InferredSense`); no existing predication/event/decompose/read_clause/heads
field is read or written.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import reading_review as rr
from domains import reflective_faculty as rf

_SEED_ID = "meaning_inference"


# --------------------------------------------------------------------------- #
#  resolution + idempotent seed load (mirrors reading_review.ensure_review_seed).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    return sub, native, ag_node


def _wire_class_pairs_to_agent(sub, ag_node) -> None:
    """Every `SelectionalClassPair` the agent HOLDS (seeded, or minted later by
    `teach()`) must be reachable from `agent` via `has_selectional_class_pair`
    for the join rules to see it (`match` binds via real edges, not a bare
    type scan). Mechanical reconcile-by-presence — the SAME idiom
    `jabberwock_daemon._reconcile_seed_concepts` / `phase_composer_language_rules.
    wire_unknown` already use for "wire this held node to its anchor if not
    already wired": no decision about WHICH pairs matter, every held pair gets
    wired, unconditionally, idempotently (skips ones already wired)."""
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, "has_selectional_class_pair"))
    for cp in sub.nodes("SelectionalClassPair"):
        if cp not in wired:
            sub.add_edge(ag_node, "has_selectional_class_pair", cp)


def _wire_morpheme_classes_to_agent(sub, ag_node) -> None:
    """The SAME reconcile-by-presence idiom as `_wire_class_pairs_to_agent`,
    for `MorphemeClass` (slice 3): every held row — seeded, or minted later by
    `teach()` (e.g. a new '-onium' element/metal row) — is wired to `agent` via
    `has_morpheme_class` so `infer_sense_from_morphology`'s join sees it without
    a fresh boot."""
    if ag_node is None:
        return
    wired = set(sub.neighbours(ag_node, "has_morpheme_class"))
    for mc in sub.nodes("MorphemeClass"):
        if mc not in wired:
            sub.add_edge(ag_node, "has_morpheme_class", mc)


def ensure_meaning_inference_seed(agent) -> None:
    """Idempotently install the meaning-inference rules + the seeded
    `SelectionalClassPair` join rows (seeds/meaning_inference.json), and
    reconcile-wire every held `SelectionalClassPair` (seeded or taught since)
    to the agent root. The rule-install is guarded on the 'infer_sense_mint'
    rule name already being present in the live rule set — the same
    `export_rules()`-by-name probe `world_adapter._ensure_comprehension_seeds`
    uses (this seed is rules-only, no Program node to probe) — but the
    reconcile-wire runs every call (cheap, idempotent) so a `teach()`-minted
    SelectionalClassPair becomes visible to the join without a fresh boot.
    Mechanical seed I/O, not a decision."""
    sub, native, ag_node = _resolve(agent)
    rr.ensure_review_seed(agent)          # the codebook read_clause needs
    try:
        names = {r.get("name") for r in native.export_rules()}
    except Exception:
        names = set()
    if "infer_sense_mint" not in names:
        from substrate.seed_loader import manifest_for
        native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
    _wire_class_pairs_to_agent(sub, ag_node)
    _wire_morpheme_classes_to_agent(sub, ag_node)


# --------------------------------------------------------------------------- #
#  PURE ANNOTATION — facts only, no decision. Mirrors the reader's existing
#  WordNet/morphology annotation style (e.g. _lexname reads used elsewhere).
# --------------------------------------------------------------------------- #
def _concept_index(sub) -> dict:
    idx: dict = {}
    for n in sub.nodes("Concept"):
        nm = sub.node(n)["attrs"].get("name")
        if nm:
            idx.setdefault(nm, n)
    return idx


def _existing_slot_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("PredicationSlot"):
        at = sub.node(nd)["attrs"]
        fills = sub.neighbours(nd, "fills")
        for f in fills:
            out.add((str(at.get("relation")), str(at.get("slot")), f))
    return out


_SLOT_POSITIONS = (("subject", 1), ("object", 2))


def annotate_predication_slots(agent, read: dict) -> list:
    """For every grounded predication `[rel, subj, obj?]` in
    `read['predications']`, write the FACTS a selectional-inference rule needs
    to join against: the filler Concept's `oov`/`is_pronoun`, and a
    `PredicationSlot{slot, rel_verb_class, relation}` per argument, linked
    `agent -has_predication_slot-> ps -fills-> filler_concept`. Written
    UNCONDITIONALLY (every argument, every predication) — this function never
    branches on what a `SelectionalClassPair` says; the JOIN lives in the seed
    rules (`seeds/meaning_inference.json`), run via `native.run_rules()` at
    the end of this call (the same synchronous-drive precedent
    `reflective_faculty.induce_concern` already uses). Idempotent by
    (relation, slot, filler) across repeated calls on the same reading.
    Returns the list of newly-added PredicationSlot node ids."""
    sub, native, ag_node = _resolve(agent)
    preds = read.get("predications") or []
    if not preds or ag_node is None:
        return []
    ensure_meaning_inference_seed(agent)
    concept_idx = _concept_index(sub)
    existing = _existing_slot_keys(sub)
    created: list = []
    for pred in preds:
        if len(pred) < 2:
            continue
        rel = str(pred[0]).lower()
        rel_class = rr._lexname(rel, "event")          # capability read; None for a non-verb relation
        for slot_name, idx in _SLOT_POSITIONS:
            if len(pred) <= idx:
                continue
            head = rr._head(pred[idx])                 # mechanical: last word of the role span
            if not head:
                continue
            fc = concept_idx.get(head)
            if fc is None:
                continue                                # grounding minted no Concept for this arg
            oov = 1.0 if rr._lexname(head, "patient") is None else 0.0
            is_pronoun = 1.0 if head in rr._PRONOUNS else 0.0
            sub.set_attr(fc, "oov", oov)
            sub.set_attr(fc, "is_pronoun", is_pronoun)
            key = (rel, slot_name, fc)
            if key in existing:
                continue
            ps = sub.add_node("PredicationSlot", {
                "slot": slot_name, "rel_verb_class": rel_class, "relation": rel,
            })
            sub.add_edge(ps, "fills", fc)
            sub.add_edge(ag_node, "has_predication_slot", ps)
            existing.add(key)
            created.append(ps)
    if created:
        native.run_rules()
    return created


def _existing_predication_fact_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("Predication"):
        at = sub.node(nd)["attrs"]
        out.add((str(at.get("relation")), str(at.get("subj_name")), str(at.get("genus_full"))))
    return out


def annotate_predication_facts(agent, read: dict) -> list:
    """INFER MEANING FROM CONTEXT, slice 2 — DEFINITIONAL inference. For every
    grounded predication `[rel, subj, obj]` in `read['predications']` that HAS an
    object, write ONE `Predication{relation, subj_name, genus_full, genus_head,
    subj_oov, genus_head_grounded, genus_head_class}` fact node, linked
    `agent -has_predication_fact-> pred -subject_concept-> subj_concept`. This is
    the SUBJECT<->OBJECT pairing slice 1's per-argument `PredicationSlot` cannot
    express (each `PredicationSlot` carries only one argument in isolation).

    Written UNCONDITIONALLY for every predication with an object — `len(pred) < 3`
    is a STRUCTURAL arity check fixed by `_ground`'s own template (mirrors the
    `len(pred) <= idx` guard `annotate_predication_slots` already uses), never a
    branch on WHAT the relation is. The RELATION SELECTION (`relation == 'is_a'`)
    is NOT decided here — it is an `Eq` in the seed rule
    (`infer_sense_from_definition`, seeds/meaning_inference.json).

    `genus_head` is the object's LAST underscore-token
    (`reading_review._head` — mechanical, `str.split('_')`, no regex), so a
    compound genus ('small_bird') resolves to its HEAD noun ('bird') the same way
    the reader's own `_head` faculty already resolves every other role span.
    `genus_head_grounded`/`genus_head_class` are a WordNet CAPABILITY read
    (`reading_review._lexname(genus_head, 'patient')`) — the SAME kind of read
    `annotate_predication_slots` already performs for `oov`, not a graph lookup:
    `_write_predications` mints the object's OWN Concept under its FULL phrase
    name ('small_bird'), never under just its head, so there is no 'bird' Concept
    node to look up — the genus's grounded-ness is read straight from WordNet,
    exactly as `oov` already is. `subj_oov` is the same WordNet capability read
    applied to the subject's head (a duplicate of the read
    `annotate_predication_slots` performs on the same Concept — decoupled on
    purpose, so this function has no ordering dependency on that one).

    Idempotent by (relation, subj_name, genus_full). Returns the newly-added
    `Predication` node ids."""
    sub, native, ag_node = _resolve(agent)
    preds = read.get("predications") or []
    if not preds or ag_node is None:
        return []
    ensure_meaning_inference_seed(agent)
    concept_idx = _concept_index(sub)
    existing = _existing_predication_fact_keys(sub)
    created: list = []
    for pred in preds:
        if len(pred) < 3:
            continue                                    # no object -- arity, not a relation decision
        rel = str(pred[0]).lower()
        subj_name = str(pred[1])
        genus_full = str(pred[2])
        subj_concept = concept_idx.get(subj_name)
        if subj_concept is None:
            continue                                    # grounding minted no Concept for the subject
        key = (rel, subj_name, genus_full)
        if key in existing:
            continue
        subj_head = rr._head(subj_name)
        genus_head = rr._head(genus_full)
        subj_oov = 1.0 if rr._lexname(subj_head, "patient") is None else 0.0
        genus_head_class = rr._lexname(genus_head, "patient")     # None unless grounded
        genus_head_grounded = 1.0 if genus_head_class is not None else 0.0
        pn = sub.add_node("Predication", {
            "relation": rel, "subj_name": subj_name,
            "genus_full": genus_full, "genus_head": genus_head,
            "subj_oov": subj_oov,
            "genus_head_grounded": genus_head_grounded,
            "genus_head_class": genus_head_class,
        })
        sub.add_edge(pn, "subject_concept", subj_concept)
        sub.add_edge(ag_node, "has_predication_fact", pn)
        existing.add(key)
        created.append(pn)
    if created:
        native.run_rules()
    return created


_AFFIX_SUFFIX_LENS = (2, 3, 4, 5, 6)
_AFFIX_PREFIX_LENS = (2, 3, 4)


def _existing_affix_candidate_keys(sub) -> set:
    out = set()
    for nd in sub.nodes("AffixCandidate"):
        at = sub.node(nd)["attrs"]
        fills = sub.neighbours(nd, "affix_fills")
        for f in fills:
            out.add((str(at.get("affix")), str(at.get("position")), f))
    return out


def annotate_affix_candidates(agent, read: dict) -> list:
    """INFER MEANING FROM CONTEXT, slice 3 — MORPHOLOGICAL inference. For every
    grounded predication argument whose filler is an OOV, non-pronoun content
    word (the SAME `oov`/`is_pronoun` facts `annotate_predication_slots` already
    writes on the filler Concept — read again here, not re-decided), write an
    `AffixCandidate{affix, position, term, affix_len}` node for EVERY
    2..6-character SUFFIX and EVERY 2..4-character PREFIX of the filler's head
    — mechanical `str` slicing (`head[-n:]` / `head[:n]`; `affix_len` is just
    `len(affix)`, a structural fact the longest-match guard reads, not a
    preference), no regex, no preference among the candidates. 'florbitis'
    therefore gets candidates 's', 'is', 'tis', 'itis', 'bitis', 'rbitis'
    (suffixes) and 'fl', 'flo', 'flor' (prefixes) — ALL of them,
    unconditionally; whether any one of them MEANS something (and which one
    wins when several of the SAME class match) is entirely the seed rule's
    join against `MorphemeClass`, never decided here. Linked
    `agent -has_affix_candidate-> ac -affix_fills-> filler_concept` — a
    DEDICATED edge type, not `PredicationSlot`'s `fills` (a filler word can
    carry many AffixCandidate in-edges at once; CLAUDE.md documents that
    "two same-type incoming edges on one node can break run_rules matching
    for that edge type", so morphology never shares PredicationSlot's edge).

    Only OOV, non-pronoun fillers get candidates at all — this is the SAME
    scope-narrowing `annotate_predication_slots` performs by omission (a slot
    is written for every argument regardless; here we skip entirely for a
    known/closed-class filler) purely to avoid enumerating substrings of
    words that could never be OOV-inferred anyway. It is not a decision about
    AFFIXES — it is the identical oov/is_pronoun read already used elsewhere,
    and `infer_sense_from_morphology` re-checks both guards independently (so
    the rule's correctness never depends on this scoping choice).

    Idempotent by (affix, position, filler). Returns the newly-added
    `AffixCandidate` node ids."""
    sub, native, ag_node = _resolve(agent)
    preds = read.get("predications") or []
    if not preds or ag_node is None:
        return []
    ensure_meaning_inference_seed(agent)
    concept_idx = _concept_index(sub)
    existing = _existing_affix_candidate_keys(sub)
    created: list = []
    for pred in preds:
        if len(pred) < 2:
            continue
        for slot_name, idx in _SLOT_POSITIONS:
            if len(pred) <= idx:
                continue
            head = rr._head(pred[idx])
            if not head:
                continue
            fc = concept_idx.get(head)
            if fc is None:
                continue
            oov = 1.0 if rr._lexname(head, "patient") is None else 0.0
            if oov != 1.0 or head in rr._PRONOUNS:
                continue                            # nothing to enumerate — not a candidate filler
            for n in _AFFIX_SUFFIX_LENS:
                if len(head) <= n:
                    continue
                affix = head[-n:]
                key = (affix, "suffix", fc)
                if key in existing:
                    continue
                ac = sub.add_node("AffixCandidate", {
                    "affix": affix, "position": "suffix", "term": head,
                    "affix_len": float(len(affix)),
                })
                sub.add_edge(ac, "affix_fills", fc)
                sub.add_edge(ag_node, "has_affix_candidate", ac)
                existing.add(key)
                created.append(ac)
            for n in _AFFIX_PREFIX_LENS:
                if len(head) <= n:
                    continue
                affix = head[:n]
                key = (affix, "prefix", fc)
                if key in existing:
                    continue
                ac = sub.add_node("AffixCandidate", {
                    "affix": affix, "position": "prefix", "term": head,
                    "affix_len": float(len(affix)),
                })
                sub.add_edge(ac, "affix_fills", fc)
                sub.add_edge(ag_node, "has_affix_candidate", ac)
                existing.add(key)
                created.append(ac)
    if created:
        native.run_rules()
    return created


def _fills_map(sub) -> dict:
    """concept-node-id -> {(slot, relation), ...} this concept fills, read
    straight off the ALREADY-WRITTEN `PredicationSlot` facts (slice 1's own
    mechanical annotation, re-aggregated here, never re-decided)."""
    out: dict = {}
    for nd in sub.nodes("PredicationSlot"):
        at = sub.node(nd)["attrs"]
        slot = at.get("slot")
        rel = at.get("relation")
        if slot != "subject" or not rel:
            continue
        for f in sub.neighbours(nd, "fills"):
            out.setdefault(f, set()).add((slot, rel))
    return out


def annotate_relational_signatures(agent, read: dict) -> list:
    """SLICE 4 STRETCH — UNMARKED STRUCTURAL analogy support (no "like"/
    "resembles" cue anywhere; the term's own accumulated RELATIONAL PROFILE
    is the evidence). Every filler Concept's participation across the
    already-written `PredicationSlot` facts (slice 1 — read again here, never
    re-decided) is re-aggregated into `own_relations`: the sorted,
    deduplicated tuple of `(slot, relation)` pairs this concept has filled as
    a SUBJECT, across every read so far in this session — a pure structural
    fact about what has been SAID about the word, nothing about what it
    means. Written unconditionally on every Concept that fills at least one
    subject `PredicationSlot` — OOV and grounded fillers alike, symmetric.

    For a GROUNDED filler only (`oov==0.0` — the SAME scope-narrowing
    `annotate_affix_candidates` already documents for its OOV-only scope,
    mirrored: an ungrounded filler has no class to LEND, so indexing it would
    be pointless codebook data, never a decision about which transfers
    happen) with a non-empty `own_relations`, this ALSO holds (idempotent,
    find-or-create by name) a `ConceptSignature{name, signature, concept}`
    codebook node — `concept` carries the grounded filler's own WordNet class
    (`rr._lexname`, the SAME capability read `annotate_predication_facts`
    already performs for a genus head) — linked
    `agent -has_concept_signature-> cs`. This is the DEDICATED codebook
    `infer_sense_from_structural_analogy`'s `ShapeDecode` Term reads
    (`codebook_type='ConceptSignature'`, never the composer's own
    'ShapeSignature' codebook — no cross-contamination): an OOV term whose
    own multi-relation profile is FULLY, SINGLY explained by one held
    grounded concept's profile (empty residual, one-part plan) has that
    concept's class transferred to it. The JOIN/scoring/argmax-over-coverage
    is entirely the rule's `ShapeDecode` Term; this function only writes the
    (slot, relation) facts and the codebook entries — the same "facts in,
    decision in Rust" split as every earlier slice.

    Idempotent: `own_relations` is recomputed (a pure function of the
    current PredicationSlot facts) every call; a `ConceptSignature` is
    created once per grounded term name and its `signature`/`concept`
    refreshed in place. Returns the newly-created `ConceptSignature` ids."""
    sub, native, ag_node = _resolve(agent)
    if ag_node is None:
        return []
    ensure_meaning_inference_seed(agent)
    fills = _fills_map(sub)
    if not fills:
        return []
    existing_cs = {}
    for nd in sub.nodes("ConceptSignature"):
        nm = sub.node(nd)["attrs"].get("name")
        if nm:
            existing_cs[nm] = nd
    wired_cs = set(sub.neighbours(ag_node, "has_concept_signature"))
    created: list = []
    touched = False
    for fc, pairs in fills.items():
        at = sub.node(fc)["attrs"]
        name = at.get("name")
        if not name:
            continue
        rel_sig = tuple(sorted(pairs))
        sub.set_attr(fc, "own_relations", rel_sig)
        touched = True
        if at.get("oov") != 0.0 or not rel_sig:
            continue                                    # nothing to lend -- scope, not a decision
        sense_class = rr._lexname(name, "patient")
        cs = existing_cs.get(name)
        if cs is None:
            cs = sub.add_node("ConceptSignature", {
                "name": name, "signature": rel_sig, "concept": sense_class,
            })
            existing_cs[name] = cs
            created.append(cs)
        else:
            sub.set_attr(cs, "signature", rel_sig)
            sub.set_attr(cs, "concept", sense_class)
        if cs not in wired_cs:
            sub.add_edge(ag_node, "has_concept_signature", cs)
            wired_cs.add(cs)
    if touched:
        native.run_rules()
    return created


# --------------------------------------------------------------------------- #
#  MECHANICAL READER — query the held InferredSense beliefs back out (mirrors
#  the "iterate + filter" shape reading_review._selectional_specs /
#  _license_policy already use; there is no dedicated ReadingBelief getter to
#  mirror more directly).
# --------------------------------------------------------------------------- #
def held_inferred_senses(agent, term: Optional[str] = None) -> list:
    """The agent's held `InferredSense` beliefs, optionally filtered to one
    `term`, each as {term, sense_class, confidence, via, source, status,
    revisable}. ONE node per (term, sense_class) — a term with several
    admissible classes (e.g. noun.person AND noun.animal) holds several
    entries; a caller wanting the whole class set unions `sense_class` across
    the returned rows. Pure graph read — no decision. A `status=='superseded'`
    entry is still returned (inspectable, per the revisable-belief contract)."""
    sub, _, _ = _resolve(agent)
    out: list = []
    key = str(term).lower() if term is not None else None
    for nd in sub.nodes("InferredSense"):
        at = sub.node(nd)["attrs"]
        t = at.get("term")
        if key is not None and str(t).lower() != key:
            continue
        out.append({"term": t, "sense_class": at.get("sense_class"),
                    "confidence": at.get("confidence"), "via": at.get("via"),
                    "source": at.get("source"), "status": at.get("status"),
                    "revisable": at.get("revisable"), "genus": at.get("genus")})
    return out
