"""propositional_deduction — GENERAL propositional modus ponens, minted as a
`ShapeSignature{kind:"knowledge_logical"}` schema the GENERAL inference_generation
collapse pipeline (domains/inference_generation.py) already knows how to decode
against, mint from, and re-run the fixpoint over.

WHY THIS MODULE EXISTS (see docs/research/engine_substrate/
DEDUCTION_GENERALIZATION_PREREG.md / _RESULTS.md for the full design record).
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
share (SHAPE_TYPE_VOCABULARY_SPIKE.md's corrected finding: node TYPE partitions
a decode pool, `kind` is a label within it — a new `kind` is an ADDITION, not a
new mechanism) — with `signature` holding the antecedent fact pattern
(`[["holds", <attr>]]`, decoded structurally via the existing `ShapeDecode`
Term's `Covers`, never executed as a callable) and `supplies` holding the
consequent in the BYTE-IDENTICAL `{"relation": "is_a", "attr": ...}` shape the
`knowledge_enabling` schemas already use — so the eventual MINT reuses
`situation_model_reader.ingest_predication` completely unchanged (the same call
`inference_generation.resolve_precondition_gap` already makes). The
ORDERING ground_reductions.compute implements with a bespoke "first clause that
holds wins" Python loop is likewise not re-implemented: the general pipeline
already has a strictly more general analogue (`reading_collapse._winner`,
best-shape-fit selection among every covering schema in the pool), which every
existing gap kind already relies on, so `knowledge_logical` gets ordering for
free by joining the same pool.

WHAT THIS MODULE DOES (mechanical, two parts, no agent decision beyond parsing
the sentence's own words — the general reader's own job, same discipline
`comprehend_theorem.py` documents for its own parser):

  1. `parse_conditional(statement)` — a SMALL, independent construction-grammar
     mini-parser (2 surface forms) for ORDINARY propositional conditionals
     ("if X is a bird, X can fly" / "a fish can swim"), NOT calling into or
     modifying `comprehend_theorem.py` (which stays scoped to group-theory
     theorem prose). Binds an antecedent attribute and a consequent
     relation+attribute; a statement no seeded form parses is the NAMED
     residual (returns None — never hand-wired around, mirroring
     comprehend_theorem's own honesty discipline).

  2. `mint_logical_schema(agent, statement)` — installs ONE `ShapeSignature
     {kind:"knowledge_logical"}` node from the parsed implication (idempotent
     by `name`, mechanical graph write — the SAME idiom every other
     `domains/*.py ensure_seeds` uses for find-or-create).

Nothing here executes a rule engine, holds agent state, or decides WHICH
schema wins a gap — that decision is entirely `inference_generation.py`'s
existing `decode_gap` -> `ShapeDecode` -> `reading_collapse._winner` collapse,
called unmodified. This module only supplies KNOWLEDGE (parsed from prose or
hand-seeded in `seeds/inference_logical.json`), never a decision.
"""
from __future__ import annotations

import json
from typing import Any, Optional


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
#  (0) TOKENISE — a mechanical surface normalisation, NO `import re` (the same
#  discipline inference_generation.py's own source audit already holds itself
#  to). Lower-case; split on whitespace, comma, and period; punctuation kept as
#  its own token so a construction pattern can require a literal comma.
# --------------------------------------------------------------------------- #
def _tokenize(text: str) -> list[str]:
    out: list[str] = []
    cur = ""
    for ch in (text or "").lower():
        if ch.isalnum() or ch == "_":
            cur += ch
            continue
        if cur:
            out.append(cur)
            cur = ""
        if ch in (",",):
            out.append(ch)
    if cur:
        out.append(cur)
    return out


# --------------------------------------------------------------------------- #
#  (1) PARSE — the seeded conditional CONSTRUCTIONS (a small, general grammar
#  over ORDINARY propositional conditionals — genus distinct from
#  comprehend_theorem's theorem-statement grammar). Each form is a token
#  pattern with '{slot}' captures; a slot greedily captures up to the next
#  literal (the SAME literal+slot semantics comprehend_theorem._match_pattern
#  uses, reimplemented small and independently here so this module never
#  imports comprehend_theorem's internals).
# --------------------------------------------------------------------------- #
_FORMS: list[dict] = [
    # "if X is a bird, X can fly" -- explicit instance-quantified conditional,
    # 'can'-consequent (a CAPABILITY/DISPOSITION: minted as is_a(X, can_<verb>)).
    {"name": "if_is_a_can", "relation": "can",
     "pattern": ["if", "{subj1}", "is", "a", "{ante}", ",",
                 "{subj2}", "can", "{cons}"]},
    {"name": "if_is_an_can", "relation": "can",
     "pattern": ["if", "{subj1}", "is", "an", "{ante}", ",",
                 "{subj2}", "can", "{cons}"]},
    # "if X is a mammal, X is warm-blooded" -- explicit conditional, 'is'-consequent
    # (a PROPERTY: minted as is_a(X, <property>)).
    {"name": "if_is_a_is", "relation": "is",
     "pattern": ["if", "{subj1}", "is", "a", "{ante}", ",",
                 "{subj2}", "is", "{cons}"]},
    {"name": "if_is_an_is", "relation": "is",
     "pattern": ["if", "{subj1}", "is", "an", "{ante}", ",",
                 "{subj2}", "is", "{cons}"]},
    # "a fish can swim" / "a mammal is warm-blooded" -- BARE UNIVERSAL form (no
    # explicit "if X ... X ..." repetition), the paraphrase comprehend_theorem's
    # own generality bar demands one seeded form hold out against.
    {"name": "bare_a_can", "relation": "can",
     "pattern": ["a", "{ante}", "can", "{cons}"]},
    {"name": "bare_an_can", "relation": "can",
     "pattern": ["an", "{ante}", "can", "{cons}"]},
    {"name": "bare_a_is", "relation": "is",
     "pattern": ["a", "{ante}", "is", "{cons}"]},
    {"name": "bare_an_is", "relation": "is",
     "pattern": ["an", "{ante}", "is", "{cons}"]},
]


def _match_pattern(pattern: list[str], toks: list[str]) -> Optional[dict]:
    """Match a construction PATTERN (literals + '{slot}') against `toks`. A
    slot greedily captures up to the next literal (or, for the final slot, to
    the end). Returns {slot: 'joined_surface'} on a FULL match, else None."""
    binds: dict[str, str] = {}
    i = 0
    n = len(pattern)
    for j, pt in enumerate(pattern):
        is_slot = pt.startswith("{") and pt.endswith("}")
        if not is_slot:
            if i >= len(toks) or toks[i] != pt:
                return None
            i += 1
            continue
        slot = pt[1:-1]
        nxt = None
        for k in range(j + 1, n):
            if not (pattern[k].startswith("{") and pattern[k].endswith("}")):
                nxt = pattern[k]
                break
        cap: list[str] = []
        while i < len(toks) and (nxt is None or toks[i] != nxt):
            cap.append(toks[i])
            i += 1
        if not cap:
            return None
        binds[slot] = "_".join(cap)          # multi-token slot -> one attr name
    if i != len(toks):
        return None
    return binds


def parse_conditional(statement: str) -> Optional[dict]:
    """PARSE an ordinary propositional CONDITIONAL statement into a graph-
    mintable implication: {antecedent_attr, consequent_relation,
    consequent_attr, chain, form}. Tries each seeded form in `_FORMS`
    (longest/most-specific first, by construction — the explicit "if X ... X
    ..." forms precede the bare-universal forms so a statement carrying the
    explicit repetition is not mis-parsed as bare). Returns None (the NAMED
    residual — a conditional-form to acquire as a construction, never
    hand-wired around) when no seeded form parses the statement."""
    toks = _tokenize(statement)
    if not toks:
        return None
    for form in _FORMS:
        binds = _match_pattern(form["pattern"], toks)
        if binds is None:
            continue
        ante = binds.get("ante")
        cons = binds.get("cons")
        if not ante or not cons:
            continue
        rel = form["relation"]
        # the consequent ATTRIBUTE the fact is minted under. A 'can'-relation
        # consequent is a CAPABILITY ("X can fly" -> attr "can_fly"); an
        # 'is'-relation consequent is a bare PROPERTY ("X is warm_blooded" ->
        # attr "warm_blooded"). Both mint via the SAME is_a(entity, attr)
        # property-predication shape ingest_predication already handles.
        consequent_attr = ("can_" + cons) if rel == "can" else cons
        chain = ("PARSE %r -> form %s -> ANTECEDENT is_a(X,%s) => CONSEQUENT "
                 "is_a(X,%s) [propositional, held, PARSED not hand-wired]"
                 % (statement, form["name"], ante, consequent_attr))
        return {"antecedent_attr": ante, "consequent_relation": rel,
                "consequent_attr": consequent_attr, "chain": chain,
                "form": form["name"]}
    return None


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
    """PARSE `statement` (parse_conditional) and, on success, install ONE
    `ShapeSignature{kind:"knowledge_logical"}` node holding the antecedent
    fact-pattern (`signature`) and the consequent fact (`supplies`) — the SAME
    two-field shape the codebook's other 5 knowledge_* kinds already use, so
    `inference_generation.decode_gap` picks it up with NO change to that
    module. Idempotent by `name` (find-or-create, mirroring every other
    domains/*.py ensure_seeds idiom). Returns {minted, name, node, parsed} on
    success; {minted: False, reason} when the statement does not parse (the
    honest residual) or the schema already exists (already=True)."""
    parsed = parse_conditional(statement)
    if parsed is None:
        return {"minted": False, "reason":
                ("no seeded conditional construction parses %r -- the NAMED "
                 "residual (a conditional-form to acquire; never hand-wired "
                 "around)") % statement}
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
