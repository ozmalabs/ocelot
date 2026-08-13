"""propositional_deduction — GENERAL propositional modus ponens, minted as a
`ShapeSignature{kind:"knowledge_logical"}` schema the GENERAL inference_generation
collapse pipeline (domains/inference_generation.py) already knows how to decode
against, mint from, and re-run the fixpoint over.

WHY THIS MODULE EXISTS (see docs/research/engine_substrate/
DEDUCTION_GENERALIZATION_PREREG.md / _RESULTS.md for the original design
record, and DEDUCTION_GENERAL_READER_CORRECTION_RESULTS.md for THIS module's
own correction — read that doc first if you are wondering why this file no
longer contains a hand-rolled token-pattern grammar).
`domains/ground_reductions.py` already proves REAL, EXECUTING propositional
deduction: `ImplicationClause`/`GroundedReduction.compute` evaluate an ordered
list of (antecedent held-predicate => consequent value) clauses and return the
first consequent whose antecedent holds — genuine modus ponens, verified against
known objects. `domains/comprehend_theorem.py` PARSES theorem PROSE into that
same clause shape. Both are entirely bound to ONE domain (group-theory
invariants) because their antecedent predicates are Python callables composed
over ONE fixed object representation (`{"orders": [...]}` / `{"rank": n}`,
`ground_reductions._factors`) — there is no route from an arbitrary graph fact
(an SmEntity's attrs, a stated sentence) into that evaluator, and this module
does NOT try to build one (that would mean rewriting ground_reductions, which is
explicitly out of scope and stays exactly as-is).

Instead: the antecedent/consequent SEPARATION `ImplicationClause` proves is the
right shape for a held implication is reused as the MODEL, not the
implementation. A held implication becomes graph DATA — a `ShapeSignature`
node, the SAME node type + decode pool the inference_generation codebook's
other 5 kinds (knowledge_enabling/elaborative/partwhole/goal/causal) already
share — with `signature` holding the antecedent fact pattern
(`[["holds", <attr>]]`, decoded structurally via the existing `ShapeDecode`
Term's `Covers`, never executed as a callable) and `supplies` holding the
consequent in the BYTE-IDENTICAL `{"relation": "is_a", "attr": ...}` shape the
`knowledge_enabling` schemas already use — so the eventual MINT reuses
`situation_model_reader.ingest_predication` completely unchanged.

THE CORRECTION (2026-08-13). The FIRST landing of this module (commit
2f3e872/a20e334) built `parse_conditional` as an INDEPENDENT, hand-rolled
token-pattern mini-grammar (8 literal surface forms, its own tokenizer). That
was a real miss: `seeds/reading_constructions.json` (`local_id: 48`) already
declares a GENERAL `ShapeSignature{kind:"construction", name:"conditional"}`
construction (`signature: [["IF"],["THEN"]]`, `predication: "implies"`) that
`domains/reading_collapse.py` decodes GENERICALLY, through the exact same
`ShapeDecode`-based mechanism every other construction (attributive / event /
definitional / ...) uses — proven live and tested TODAY, independent of this
module, at `tests/test_reading_collapse.py:57`
(`"if it rains then the ground is wet" -> ["implies", "it_rains", "ground"]`).
Building a second grammar duplicated a capability the general reader already
had. See the correction doc for the full measurement; the summary that
matters for reading the code below:

  - The general reader's OWN top-level `conditional` construction (the one
    `tests/test_reading_collapse.py:57` exercises) grounds via a `"pair"`
    ground_template that only ever reads roles[0]/roles[1] — PROVEN, by
    running it, to be too coarse for THIS module's need (a capability/
    property CONSEQUENT on a copular ANTECEDENT): on every phrasing this
    module actually mints from ("if X is a fish, X can swim", "if X is a
    mammal, X is warm blooded", "if it is a fish then it can swim") it drops
    the consequent's own predicate entirely, or fuses unrelated words into one
    blob concept. This is a real, load-bearing gap in the SHARED `conditional`
    construction, not a defect of this module — and it is explicitly NOT
    fixed here (that ground_template is shared by the byte-parity-tested
    battery in `tests/test_reading_collapse.py`; changing it is out of this
    correction's scope and risks that shared test).
  - What DOES cleanly reach this module's need, with ZERO bespoke grammar,
    is the GENERAL multi-clause SPLITTER already used for every other
    multi-clause sentence in the corpus (`reading_collapse.decompose_sentence`
    -> `_segment_into_clauses`, which already treats `IF` as a clause-opener
    and a comma as a clause boundary) handing each half to the FULLY GENERAL
    `reading_collapse.read_clause` (fragment mode, `write=False` — the SAME
    idiom `decompose_sentence`'s own `_read_clause_clean` and every order-N
    descent call already use for a clause fragment). Each half then grounds
    through whichever construction the decode picks for IT (`definitional` /
    `event`), unmodified. `parse_conditional` below is a THIN ADAPTER over
    those two calls' own predication output — not a construction grammar of
    its own. The bare-universal form ("a fish can swim") needs no split at
    all: a single `read_clause` call already grounds subject + relation +
    consequent in one predication.

WHAT THIS MODULE DOES (mechanical adapter, no agent decision beyond mapping a
decode's own predicate name onto this schema's two supported consequent
relations — see `_relation_and_attr`'s docstring for exactly why that mapping
is not a "decision" in the sense CLAUDE.md forbids):

  1. `parse_conditional(agent, statement)` — ingests `statement` through the
     GENERAL reading pipeline (`reading_collapse.decompose_sentence` +
     `reading_collapse.read_clause`), and reads OFF the antecedent/consequent
     shape this module's schema needs from the predication(s) that grounding
     already produces. A statement whose general reading does not yield an
     antecedent `is_a` predication AND a consequent `is_a`/`can` predication
     is the NAMED residual (returns None — never hand-wired around).

  2. `mint_logical_schema(agent, statement)` — installs ONE `ShapeSignature
     {kind:"knowledge_logical"}` node from the parsed implication (idempotent
     by `name`, mechanical graph write — the SAME idiom every other
     `domains/*.py ensure_seeds` uses for find-or-create).

Nothing here executes a rule engine, holds agent state, or decides WHICH
schema wins a gap — that decision is entirely `inference_generation.py`'s
existing `decode_gap` -> `ShapeDecode` -> `reading_collapse._winner` collapse,
called unmodified. This module only supplies KNOWLEDGE (parsed from prose via
the general reader, or hand-seeded in `seeds/inference_logical.json`), never a
decision.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from domains import reading_collapse as rc


# --------------------------------------------------------------------------- #
#  resolution (mechanical adapter I/O — the SAME idiom every domains/*.py
#  module duplicates locally; see situation_model_reader._resolve).
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


# --------------------------------------------------------------------------- #
#  (1) PARSE — via the GENERAL reading pipeline (reading_collapse.py), never a
#  second grammar. Two shapes, both reached by calling the SAME functions
#  every ordinary sentence in the corpus already goes through:
#
#    (a) explicit conditional, "if X is a/an P, X can/is Q" — the comma IS a
#        recognised clause boundary (`decompose_sentence`'s own general
#        `_segment_into_clauses`, which already treats IF as a clause-opener,
#        untouched by this module); the antecedent clause and consequent
#        clause each re-ground independently via `read_clause` (fragment
#        mode, the SAME idiom `_read_clause_clean`/order-N descent already use
#        for a clause fragment — plain `read_clause`, not `_read_clause_clean`,
#        because `_read_clause_clean`'s stricter `intransitive_ok=False` event
#        path drops a bare-intransitive capability clause like "X can fly",
#        measured directly — see the correction RESULTS doc);
#    (b) bare universal, "a/an P can/is Q" — no clause-opener present, so
#        `decompose_sentence` reports a single clause and a SINGLE top-level
#        `read_clause` call already grounds subject + relation + consequent
#        as one predication (event: `[can, subj, obj]`; definitional:
#        `[is_a, subj, obj]`) — no split needed at all.
# --------------------------------------------------------------------------- #
def _norm_attr(tok: Any) -> str:
    """Mechanical normalisation only — collapse a hyphen or space the SAME way
    every multi-word role span the reader itself produces is already joined
    (`reading_collapse._norm` underscores spaces; a literal hyphenated token
    like 'warm-blooded' survives the reader's own tokenizer unsplit, so this
    is the one place that convention is completed). No decision: a straight
    character substitution, not a re-parse."""
    return str(tok).lower().replace("-", "_").replace(" ", "_")


def _relation_and_attr(pred: list) -> Optional[tuple]:
    """From ONE grounded predication `[relation, subj, obj]` — already produced
    by the general reader, not re-derived here — read off the
    (consequent_relation, tail_attr) pair this module's schema supports: a
    CAPABILITY (`can`, "X can fly" -> ("can", "fly")) or a bare PROPERTY
    (`is_a`, "X is warm-blooded" -> ("is", "warm_blooded")). This is a
    NAME-KEYED MAPPING of the decode's OWN verdict onto this module's two
    supported relation labels — not a decision about what the sentence means
    (the general reader already decided that; this only reads its label).
    Any other grounded relation (an ordinary transitive event, a comparison,
    ...) is OUTSIDE this rung's pre-registered scope (single-antecedent
    PROPERTY/CAPABILITY modus ponens only) and returns None — the honest
    residual, never forced."""
    if not pred or len(pred) < 3:
        return None
    rel, _subj, obj = pred[0], pred[1], pred[2]
    if rel == "can":
        return "can", _norm_attr(obj)
    if rel == "is_a":
        return "is", _norm_attr(obj)
    return None


def parse_conditional(agent, statement: str) -> Optional[dict]:
    """PARSE an ordinary propositional CONDITIONAL statement into a graph-
    mintable implication: {antecedent_attr, consequent_relation,
    consequent_attr, chain, form} — by INGESTING it through the general
    reading pipeline (`reading_collapse.decompose_sentence` + `.read_clause`)
    and reading off the predication(s) grounding already produces, per the
    module docstring above. Returns None (the NAMED residual — a shape to
    acquire, never hand-wired around) when the general reading of `statement`
    does not yield an antecedent `is_a` predication together with a consequent
    `is_a`/`can` predication."""
    if not statement or not str(statement).strip():
        return None
    dec = rc.decompose_sentence(agent, statement)
    clauses = dec.get("clauses") or []
    if dec.get("multi_clause") and len(clauses) == 2:
        form = "conditional_split"
        ante_r = rc.read_clause(agent, clauses[0], write=False, learn=False)
        ante_preds = ante_r.get("predications") or []
        if not ante_preds or ante_preds[0][0] != "is_a" or len(ante_preds[0]) < 3:
            return None
        antecedent_attr = _norm_attr(ante_preds[0][2])
        cons_r = rc.read_clause(agent, clauses[1], write=False, learn=False)
        cons_preds = cons_r.get("predications") or []
        if not cons_preds:
            return None
        pair = _relation_and_attr(cons_preds[0])
        if pair is None:
            return None
        consequent_relation, cons_tail = pair
    else:
        form = "bare_universal"
        whole = rc.read_clause(agent, statement, write=False, learn=False)
        preds = whole.get("predications") or []
        if not preds or len(preds[0]) < 3:
            return None
        pair = _relation_and_attr(preds[0])
        if pair is None:
            return None
        antecedent_attr = _norm_attr(preds[0][1])
        consequent_relation, cons_tail = pair

    if not antecedent_attr or not cons_tail:
        return None
    consequent_attr = ("can_" + cons_tail) if consequent_relation == "can" else cons_tail
    chain = ("READ %r via the GENERAL reading pipeline "
             "(reading_collapse.decompose_sentence/read_clause, form=%s) -> "
             "ANTECEDENT is_a(X,%s) => CONSEQUENT is_a(X,%s) "
             "[propositional, held, general-reader]"
             % (statement, form, antecedent_attr, consequent_attr))
    return {"antecedent_attr": antecedent_attr, "consequent_relation": consequent_relation,
            "consequent_attr": consequent_attr, "chain": chain, "form": form}


# --------------------------------------------------------------------------- #
#  (2) MINT — install the parsed implication as ONE ShapeSignature node in the
#  SAME codebook pool inference_generation.decode_gap already scans
#  (sub.nodes("ShapeSignature")) — mechanical, idempotent graph I/O; the
#  DECISION (which schema a gap collapses to) stays entirely
#  inference_generation.py's, unchanged.
# --------------------------------------------------------------------------- #
def _schema_by_name(sub, name: str):
    for n in sub.nodes("ShapeSignature"):
        if sub.node(n)["attrs"].get("name") == name:
            return n
    return None


def mint_logical_schema(agent, statement: str, *, name: Optional[str] = None) -> dict:
    """PARSE `statement` (parse_conditional, via the general reading pipeline)
    and, on success, install ONE `ShapeSignature{kind:"knowledge_logical"}`
    node holding the antecedent fact-pattern (`signature`) and the consequent
    fact (`supplies`) — the SAME two-field shape the codebook's other 5
    knowledge_* kinds already use, so `inference_generation.decode_gap` picks
    it up with NO change to that module. Idempotent by `name` (find-or-create,
    mirroring every other domains/*.py ensure_seeds idiom). Returns {minted,
    name, node, parsed} on success; {minted: False, reason} when the statement
    does not parse (the honest residual) or the schema already exists
    (already=True)."""
    parsed = parse_conditional(agent, statement)
    if parsed is None:
        return {"minted": False, "reason":
                ("the general reading pipeline does not ground %r into an "
                 "antecedent is_a + consequent is_a/can predication pair -- "
                 "the NAMED residual (a reading shape to acquire; never "
                 "hand-wired around)") % statement}
    sub, _, _ = _resolve(agent)
    nm = name or ("logical_%s_%s" % (parsed["antecedent_attr"],
                                      parsed["consequent_attr"]))
    existing = _schema_by_name(sub, nm)
    if existing is not None:
        return {"minted": False, "already": True, "name": nm,
                "node": existing, "parsed": parsed}
    attrs = {
        "name": nm,
        "kind": "knowledge_logical",
        "coherence": "blocking",
        "signature": json.dumps([["holds", parsed["antecedent_attr"]]]),
        "supplies": json.dumps({"relation": "is_a",
                                "attr": parsed["consequent_attr"]}),
        "statement": statement,
        "chain": parsed["chain"],
    }
    node = sub.add_node("ShapeSignature", attrs)
    derive_contrapositive(agent, nm)
    return {"minted": True, "name": nm, "node": node, "parsed": parsed}


# --------------------------------------------------------------------------- #
#  (3) MODUS TOLLENS — the contrapositive is MECHANICALLY DERIVED from the
#  SAME held implication, not a second interpretive schema kind. P=>Q entails
#  (classical logic, not a new decision) ~Q=>~P. Reusing the SAME `not_`
#  name-prefix regularity the general reader's OWN complement-span joining
#  already produces for a negated copular statement (`domains/reading_
#  collapse.py`'s glue-join step; confirmed live: "the ground is not wet" ->
#  is_a(ground, not_wet) -- see DEDUCTION_EXTENSION_PREREG.md Sec1/RESULTS
#  Sec1 for the measurement), the contrapositive companion is a SECOND
#  `ShapeSignature{kind:"knowledge_logical"}` node in the SAME codebook pool
#  (no new kind, no new node type) whose `signature` is the NEGATED
#  consequent and whose `supplies` is the NEGATED antecedent. Once installed,
#  `inference_generation.py`'s EXISTING, UNCHANGED `detect_implication_gaps`
#  -> `decode_gap` -> `resolve_implication_gap` pipeline runs modus tollens
#  with ZERO new gap-detection code: a stated `not_wet==1` fact is already
#  offered as a breadth candidate exactly like `bird==1` is, and `Covers`
#  matches it against the contrapositive's `signature` exactly like any
#  other antecedent (measured live, not assumed -- see the RESULTS doc).
# --------------------------------------------------------------------------- #
def _negate_attr(attr: str) -> str:
    """Negate a held attr NAME using the SAME `not_`/`can_` prefix convention
    this module's OWN `parse_conditional`/`_relation_and_attr` already use
    (`can_fly` for a capability consequent, the bare tail for a property
    one) -- reading this module's OWN naming convention back out, not a new
    decision about text. A capability-shaped attr (`can_X`) negates to
    `not_X` (matching what the general reader's event-construction actually
    produces for "cannot X" -- `can(subj, not_X)`, measured live); any other
    attr (an antecedent, always a bare `is_a` tail, or a property
    consequent) negates to the plain `not_` prefix (matching what the
    general reader's definitional construction produces for "is not X" ->
    `is_a(subj, not_X)`, also measured live). Double-negation is not
    attempted (an attr already prefixed `not_` is left as-is by every
    caller here -- `ensure_contrapositives` never re-derives FROM a
    contrapositive, see its own guard)."""
    s = str(attr)
    if s.startswith("can_"):
        return "not_" + s[len("can_"):]
    return "not_" + s


def _schema_signature(sub, node) -> Optional[list]:
    try:
        return json.loads(sub.node(node)["attrs"].get("signature") or "null")
    except Exception:
        return None


def _schema_supplies(sub, node) -> Optional[dict]:
    try:
        return json.loads(sub.node(node)["attrs"].get("supplies") or "null")
    except Exception:
        return None


def derive_contrapositive(agent, schema_name: str) -> dict:
    """Mechanically derive and install the CONTRAPOSITIVE companion of ONE
    held `knowledge_logical` schema (by name): P=>Q becomes ~Q=>~P. Scoped to
    the single-antecedent shape this whole arc supports (`signature` of
    length exactly 1, `supplies.relation == "is_a"`) -- a schema outside that
    shape (e.g. an already-derived contrapositive, or -- forward-looking --
    a conjunctive schema, whose contrapositive is a DISJUNCTION this rung
    does not represent) is an honest no-op, never a wrong answer. Idempotent
    by name (`<name>_contrapositive`, find-or-create). Returns {derived:
    bool, name, node|None, reason}."""
    sub, _, _ = _resolve(agent)
    node = _schema_by_name(sub, schema_name)
    if node is None:
        return {"derived": False, "reason": "no such schema %r" % schema_name}
    at = sub.node(node)["attrs"]
    if at.get("contrapositive_of"):
        return {"derived": False, "reason": "schema %r is itself a derived "
                "contrapositive -- not re-derived (no double-negation)" % schema_name}
    sig = _schema_signature(sub, node)
    supplies = _schema_supplies(sub, node)
    if not sig or len(sig) != 1 or not isinstance(sig[0], (list, tuple)) \
            or len(sig[0]) < 2 or sig[0][0] != "holds":
        return {"derived": False, "reason": "signature %r is not the single-"
                "antecedent ['holds', attr] shape -- contrapositive not "
                "derived (out of this rung's scope)" % (sig,)}
    if not supplies or supplies.get("relation") != "is_a" or not supplies.get("attr"):
        return {"derived": False, "reason": "supplies %r is not the plain "
                "is_a shape -- contrapositive not derived" % (supplies,)}
    antecedent_attr = str(sig[0][1])
    consequent_attr = str(supplies["attr"])
    cp_name = schema_name + "_contrapositive"
    existing = _schema_by_name(sub, cp_name)
    if existing is not None:
        return {"derived": False, "already": True, "name": cp_name, "node": existing}
    attrs = {
        "name": cp_name,
        "kind": "knowledge_logical",
        "coherence": at.get("coherence") or "blocking",
        "signature": json.dumps([["holds", _negate_attr(consequent_attr)]]),
        "supplies": json.dumps({"relation": "is_a",
                                "attr": _negate_attr(antecedent_attr)}),
        "statement": at.get("statement"),
        "chain": ("CONTRAPOSITIVE of %r: held P=>Q (%s => %s) entails "
                   "~Q=>~P (%s => %s) [classical logic, mechanically derived, "
                   "not a new interpretive schema]"
                   % (schema_name, antecedent_attr, consequent_attr,
                      _negate_attr(consequent_attr), _negate_attr(antecedent_attr))),
        "contrapositive_of": schema_name,
    }
    cp_node = sub.add_node("ShapeSignature", attrs)
    return {"derived": True, "name": cp_name, "node": cp_node}


def ensure_contrapositives(agent) -> list:
    """Batch form: derive the contrapositive companion for EVERY resident
    `knowledge_logical` schema that does not already have one and is not
    itself a derived contrapositive. Additive, idempotent, safe on an
    already-loaded graph -- the SAME idiom `inference_generation._ensure_
    warning_lexicon`/`_ensure_trust_lexicon` already use for a belt-and-
    braces post-load install. Returns the list of `derive_contrapositive`
    results (including no-ops), for callers/tests that want to inspect
    what happened."""
    sub, _, _ = _resolve(agent)
    names = []
    for n in sub.nodes("ShapeSignature"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == "knowledge_logical" and not at.get("contrapositive_of"):
            nm = at.get("name")
            if nm:
                names.append(nm)
    return [derive_contrapositive(agent, nm) for nm in names]


# --------------------------------------------------------------------------- #
#  (4) QUANTIFIED PREMISES — universal + existential instantiation.
#  See docs/research/engine_substrate/QUANTIFIED_DEDUCTION_PREREG.md/_RESULTS.md
#  for the full design record. Summary:
#
#  UNIVERSAL ("All X are Y" / "Every X can Y"): the quantifier word is
#  STRIPPED FROM THE RAW STATEMENT STRING before decompose_sentence/
#  read_clause ever see it (measured live: the whole-clause bare_universal
#  path does NOT strip "all"/"some"/"every" from the subject the way the
#  isolated-span primitives _arg_head/_clean_head already do -- a narrow,
#  pre-existing inconsistency in the general reader, NOT fixed here, see the
#  PREREG doc Sec1), then the REMAINDER is handed to the EXISTING, UNCHANGED
#  parse_conditional -- a thin adapter over its own output, the SAME idiom
#  parse_conditional itself already uses for the conditional-split form. The
#  resulting schema is STRUCTURALLY IDENTICAL to any other single-antecedent
#  knowledge_logical schema, so inference_generation.py's EXISTING detect_
#  implication_gaps/resolve_implication_gap/decode_gap run universal
#  instantiation with ZERO new gap-detection code -- the SAME finding the
#  modus-tollens rung already made for the contrapositive extension.
#
#  EXISTENTIAL ("Some X is Y"): the SAME quantifier-strip + delegate-to-
#  parse_conditional adapter, but the resulting (antecedent, consequent) pair
#  is installed as a DIFFERENT kind ("knowledge_existential") with a
#  DISTINCT relation label ("holds_some", not "holds"/"holds_all") in its
#  `signature` -- consumed by a NEW detect/resolve pair in
#  inference_generation.py that performs a genuine WITNESS SEARCH (find one
#  qualifying entity, or mint a fresh witness constant if none exists) rather
#  than the "apply to every qualifying entity" breadth MP already does --
#  see inference_generation.py's own module comment on detect_existential_
#  gaps/resolve_existential_gap for why this is a materially different
#  operation, not a copy of the MP breadth-scan under a new name.
# --------------------------------------------------------------------------- #
def _singular_attr(attr: str) -> str:
    """The attr's SINGULAR noun form via the held WordNet morphy reference --
    the SAME lemmatiser situation_model_reader._lemma/reading_collapse.
    _clean_head already depend on, applied to the NOUN pos tag ('n') instead
    of the verb one ('v') _lemma already uses. Mechanical morphological
    normalisation, not a decision: 'philosophers' -> 'philosopher', 'mortal'
    -> 'mortal' (already singular, a safe no-op), 'can_fly' -> unchanged (not
    a noun form, morphy returns None, falls back to the surface). KNOWN,
    NAMED LIMITATION (QUANTIFIED_DEDUCTION_PREREG.md Sec1): an IRREGULAR
    plural ('men' -> 'man') is NOT reached by plain morphy lookups the way a
    regular '-s' plural is -- 'men' round-trips to 'men' unchanged. Not
    papered over here; the live demo is built on a regular-plural noun for
    this reason."""
    s = str(attr)
    try:
        from nltk.corpus import wordnet as wn
        lem = wn.morphy(s, "n")
        if lem:
            return lem
    except Exception:
        pass
    return s


def _quantifier_lexicon(agent) -> dict:
    """{"universal": [...], "existential": [...]} read off the resident
    QuantifierLexicon node (seeds/inference_logical.json), with the SAME
    defaults baked in if the node is somehow absent -- graph-native
    codebook, never a hardcoded story rule, mirroring inference_generation.
    _warning_lexicon/_trust_lexicon's exact idiom. SCOPED, deliberately:
    'a'/'an' are NOT members here -- they stay owned by the EXISTING
    bare_universal generic reading ('a bird can fly' already grounds and
    fires today), so there is no ambiguity about which path a bare
    indefinite-article sentence takes (unchanged, byte-identical)."""
    sub, _, _ = _resolve(agent)
    for n in sub.nodes("QuantifierLexicon"):
        at = sub.node(n)["attrs"]
        universal = [str(w).lower() for w in (at.get("universal") or [])]
        existential = [str(w).lower() for w in (at.get("existential") or [])]
        if universal or existential:
            return {"universal": universal, "existential": existential}
    return {"universal": ["all", "every", "each"], "existential": ["some"]}


def _split_leading_quantifier(agent, statement: str):
    """Recognise + strip a LEADING quantifier word from `statement` (a thin
    I/O-boundary classifier -- CLAUDE.md's own named carve-out: converting an
    opaque surface cue into the smallest graph token, and no reading-
    pipeline construction already does this, measured in the PREREG doc
    Sec2). Returns (force, remainder) where force is 'universal'/
    'existential'/None (no recognised leading quantifier -- the honest
    residual) and remainder is the statement with that ONE leading token
    removed (unchanged otherwise). Plain str.split/lower -- no regex."""
    s = str(statement or "").strip()
    if not s:
        return None, s
    parts = s.split(None, 1)
    if not parts:
        return None, s
    head = parts[0].lower().strip(".,;:!?")
    rest = parts[1] if len(parts) > 1 else ""
    lex = _quantifier_lexicon(agent)
    if head in lex["universal"]:
        return "universal", rest
    if head in lex["existential"]:
        return "existential", rest
    return None, s


def parse_universal(agent, statement: str) -> Optional[dict]:
    """PARSE a UNIVERSAL quantified premise ('All philosophers are mortal',
    'Every bird can fly'): strip the leading universal quantifier word
    (_split_leading_quantifier), delegate the remainder to the EXISTING,
    UNCHANGED parse_conditional (a thin adapter over its own output, exactly
    the same reuse discipline parse_conditional itself already documents for
    its own conditional-split form), then SINGULARISE the antecedent (always)
    and the consequent (only for a plain property relation -- a capability
    consequent is already the bare verb form, never plural-inflected).
    Returns None (the honest residual) when the statement has no recognised
    leading universal quantifier, or when the remainder does not parse via
    parse_conditional."""
    force, rest = _split_leading_quantifier(agent, statement)
    if force != "universal":
        return None
    parsed = parse_conditional(agent, rest)
    if parsed is None:
        return None
    antecedent_attr = _singular_attr(parsed["antecedent_attr"])
    consequent_attr = parsed["consequent_attr"]
    if parsed["consequent_relation"] == "is":
        consequent_attr = _singular_attr(consequent_attr)
    chain = ("UNIVERSAL(%r): stripped leading quantifier -> delegated remainder "
             "%r to parse_conditional [reused, unchanged] -> singularised "
             "ANTECEDENT is_a(X,%s) => CONSEQUENT is_a(X,%s) [propositional, "
             "held, general-reader + noun-lemma normalisation]"
             % (statement, rest, antecedent_attr, consequent_attr))
    out = dict(parsed)
    out["antecedent_attr"] = antecedent_attr
    out["consequent_attr"] = consequent_attr
    out["chain"] = chain
    return out


def mint_universal_schema(agent, statement: str, *, name: Optional[str] = None) -> dict:
    """Install a UNIVERSAL premise (parse_universal) as ONE ShapeSignature
    {kind:"knowledge_logical", quantifier:"universal"} node -- STRUCTURALLY
    IDENTICAL in shape to a `mint_logical_schema` node (same signature/
    supplies fields, same node type, same codebook pool), so inference_
    generation.py's EXISTING detect_implication_gaps/resolve_implication_gap/
    decode_gap pick it up with NO change to that module -- the SAME finding
    the modus-tollens rung already made. A SELF-CONTAINED sibling of mint_
    logical_schema (not a refactor of it) to keep that existing, tested
    function's body byte-for-byte unchanged. Idempotent by name. Calls
    derive_contrapositive at the end, exactly like mint_logical_schema
    already does -- a universally-quantified premise composes with the
    modus-tollens extension for free (same kind, same length-1 signature
    shape)."""
    parsed = parse_universal(agent, statement)
    if parsed is None:
        return {"minted": False, "reason":
                ("%r does not parse as a universal premise (no recognised "
                 "leading universal quantifier, or the remainder does not "
                 "ground via parse_conditional) -- the NAMED residual") % statement}
    sub, _, _ = _resolve(agent)
    nm = name or ("logical_universal_%s_%s" % (parsed["antecedent_attr"],
                                                 parsed["consequent_attr"]))
    existing = _schema_by_name(sub, nm)
    if existing is not None:
        return {"minted": False, "already": True, "name": nm,
                "node": existing, "parsed": parsed}
    attrs = {
        "name": nm,
        "kind": "knowledge_logical",
        "quantifier": "universal",
        "coherence": "blocking",
        "signature": json.dumps([["holds", parsed["antecedent_attr"]]]),
        "supplies": json.dumps({"relation": "is_a",
                                "attr": parsed["consequent_attr"]}),
        "statement": statement,
        "chain": parsed["chain"],
    }
    node = sub.add_node("ShapeSignature", attrs)
    derive_contrapositive(agent, nm)
    return {"minted": True, "name": nm, "node": node, "parsed": parsed}


def parse_existential(agent, statement: str) -> Optional[dict]:
    """PARSE an EXISTENTIAL quantified premise ('Some bird is a penguin'):
    strip the leading existential quantifier word, delegate the remainder to
    parse_conditional (reused, unchanged), singularise the same way parse_
    universal does. Returns None (the honest residual) when the statement
    has no recognised leading existential quantifier or the remainder does
    not parse."""
    force, rest = _split_leading_quantifier(agent, statement)
    if force != "existential":
        return None
    parsed = parse_conditional(agent, rest)
    if parsed is None:
        return None
    antecedent_attr = _singular_attr(parsed["antecedent_attr"])
    consequent_attr = parsed["consequent_attr"]
    if parsed["consequent_relation"] == "is":
        consequent_attr = _singular_attr(consequent_attr)
    chain = ("EXISTENTIAL(%r): stripped leading quantifier -> delegated remainder "
             "%r to parse_conditional [reused, unchanged] -> singularised "
             "ANTECEDENT is_a(X,%s) AND CONSEQUENT is_a(X,%s), witness "
             "unresolved [propositional, held, general-reader + noun-lemma "
             "normalisation]" % (statement, rest, antecedent_attr, consequent_attr))
    out = dict(parsed)
    out["antecedent_attr"] = antecedent_attr
    out["consequent_attr"] = consequent_attr
    out["chain"] = chain
    return out


def mint_existential_premise(agent, statement: str, *, name: Optional[str] = None) -> dict:
    """Install an EXISTENTIAL premise (parse_existential) as ONE
    ShapeSignature{kind:"knowledge_existential", quantifier:"existential"}
    node. Reuses the SAME signature/supplies field SHAPE as knowledge_
    logical (consistency with the rest of the codebook pool), but a
    DISTINCT relation label in `signature` ("holds_some", not "holds"/
    "holds_all") so this schema can NEVER become a candidate decoder for
    detect_implication_gaps'/detect_conjunctive_gaps' own goals -- the SAME
    per-gap-kind labelling discipline that closed the conjunction rung's own
    cross-contamination bug (DEDUCTION_EXTENSION_RESULTS.md Sec3.3). Marked
    `witnessed: 0` -- inference_generation.detect_existential_gaps/resolve_
    existential_gap perform the actual witness search/mint (this function
    only installs the PREMISE, mirroring mint_logical_schema's own
    parse-then-install split). Idempotent by name. NOT decoded via
    ShapeDecode/decode_gap (an honest architectural choice, not an
    oversight -- see the PREREG doc Sec4: there is no competing schema to
    choose among once a single existential premise is parsed, so a
    collapse would be overhead with no discriminative work to do) and NOT
    given a contrapositive (derive_contrapositive's own kind=="knowledge_
    logical" scan skips it by construction)."""
    parsed = parse_existential(agent, statement)
    if parsed is None:
        return {"minted": False, "reason":
                ("%r does not parse as an existential premise (no recognised "
                 "leading existential quantifier, or the remainder does not "
                 "ground via parse_conditional) -- the NAMED residual") % statement}
    sub, _, _ = _resolve(agent)
    nm = name or ("existential_%s_%s" % (parsed["antecedent_attr"],
                                          parsed["consequent_attr"]))
    existing = _schema_by_name(sub, nm)
    if existing is not None:
        return {"minted": False, "already": True, "name": nm,
                "node": existing, "parsed": parsed}
    attrs = {
        "name": nm,
        "kind": "knowledge_existential",
        "quantifier": "existential",
        "coherence": "blocking",
        "signature": json.dumps([["holds_some", parsed["antecedent_attr"]]]),
        "supplies": json.dumps({"relation": "is_a",
                                "attr": parsed["consequent_attr"]}),
        "statement": statement,
        "chain": parsed["chain"],
        "witnessed": 0,
    }
    node = sub.add_node("ShapeSignature", attrs)
    return {"minted": True, "name": nm, "node": node, "parsed": parsed}


__all__ = ["parse_conditional", "mint_logical_schema",
           "derive_contrapositive", "ensure_contrapositives",
           "parse_universal", "mint_universal_schema",
           "parse_existential", "mint_existential_premise"]
