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
    return {"minted": True, "name": nm, "node": node, "parsed": parsed}


__all__ = ["parse_conditional", "mint_logical_schema"]
