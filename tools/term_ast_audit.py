#!/usr/bin/env python3
"""AST-BASED STRUCTURAL AUDIT OF SEED TERM TREES.

Specified in `VISION_TRIPWIRE_REPAIR_PREREG.md` (committed BEFORE the run at
`7c920c42`) and built to repair the five substring-matching assertions inventoried
there.

THE DEFECT THIS REPLACES
------------------------
L1b asserted `'"type": "Lte"' not in json.dumps(rule)` with the note *"if a bound was
added, re-run the audit"*. A bound WAS added and was composed as `Lt` inside
`Not(Exists(...))` — semantically a bound, structurally invisible to that scan. Every
assertion of the form "is Term type X present in this serialized seed" is evadable the
same way: re-spell the comparator, negate it, nest it, swap its operands, or move it to
a sibling rule.

WHAT THIS MODULE DOES INSTEAD
-----------------------------
Parses the Term trees (walking `dict`/`list` recursively, so it reaches `match`,
`where`, `effects` and every nesting under `Not`/`Exists`/`And`/`Or`/`Filter`) and
classifies each comparator BY THE SHAPE OF ITS OPERANDS.

Two tiers, BOTH reported, because they answer different questions and because each
alone is a degenerate gate (a detect-nothing build scores a perfect false-positive
arm; a detect-everything build scores a perfect evasion arm):

  T0 ANY-COMPARATOR  every {Lt,Lte,Gt,Gte} at any depth, any position, under any
                     number of `Not`s. The strictly-stronger drop-in replacement for
                     the string test. Has false positives BY CONSTRUCTION.

  T1 BOUND-LIKE      a T0 node where NEITHER operand is rooted at `Count` AND at least
                     one operand is DERIVED (a computed expression).

The two T1 exclusions are DECLARED SEMANTICS matching verdicts L1b already published:
`Count`-rooted is cardinality (L1b's own similarity row calls `Count(residual)==0`
"exact equality", explicitly NOT a verdict bound); atomic-vs-atomic is a flag or epoch
read (`Gt(Attr(identity), Lit(0.0))`), which cannot refuse a candidate on how far it
sits from the codebook. What survives both exclusions is a comparison against a
COMPUTED MAGNITUDE — which is what a bound structurally is.

  T2 CODEBOOK-CROSSING  ADDED by the Attr-threshold rung (`VISION_AST_ATTR_PREREG.md`)
                     to close T1's own measured false negative: a bound whose THRESHOLD
                     IS A STORED ATTRIBUTE (`Lte(Attr(c,'v0hi'), Attr(R,'v0'))`) is
                     atomic-vs-atomic, so T1 reads it as a flag/epoch read and MISSES
                     it. T2's concrete case is T2-category box containment — FOUR such
                     `Lte(Attr,Attr)` predicates, measured load-bearing by
                     `VISION_CATEGORY_RESULTS.md` arm E(c).

                     T2 fires ONLY on `Attr`-vs-`Attr` (the exact class T1 misses), and
                     requires the comparator to CROSS the candidate/observation
                     boundary — one operand a `NodesOfType`-quantified codebook
                     candidate, the other not — AND to compare DIFFERENT attribute keys.
                     `T2 ⊇ T1` and `T2 ⊆ T0` by construction, so T2 reverses no verdict
                     either existing tier reaches; it only PROMOTES.

`ATOMIC` is defined by its small closed complement so an UNRECOGNISED Term counts as
DERIVED: for a tripwire, a false positive costs a re-run and a false negative costs a
wrong landed verdict.

WHAT REMAINS UNDECIDABLE — AND IS REPORTED AS A RANGE, NOT A VERDICT
-------------------------------------------------------------------
T2 does NOT close the class in general, and this is DERIVED rather than conceded:

    Lt( Attr(h,'dist'),  Attr(ag,'bound')          )   # a GENUINE bound
    Lt( Attr(h,'epoch'), Attr(ag,'codebook_epoch') )   # a DECLARED NON-bound (N3_epoch)

Erase the attribute names — the only thing that differs — and the two ASTs are
IDENTICAL. No structural predicate separates them; the distinction is what the names
MEAN. So `audit_seed` reports `bound_range = [T2, T0]` and `undecidable_residual` for
every scope, and a caller that needs a verdict on that class must supply semantics this
module does not have. BOUND-PRESENCE IS ALSO NOT BOUND-EFFICACY: nothing here detects a
NEAR-VACUOUS bound (`Lte(Attr(d), Attr(huge))` is promoted and admits everything).

This is static analysis of committed JSON. It holds no agent state and makes no agent
decision (CLAUDE.md) — it is audit tooling, in the same class as the AST scan L1b
already applies to the adapter's Python.
"""
from __future__ import annotations

import json
from typing import Any, Iterator, NamedTuple

COMPARATORS = ("Lt", "Lte", "Gt", "Gte")

#: Operand roots that are a STORED VALUE or a LITERAL. Everything else is DERIVED.
#: Closed and small BY DESIGN — see the module docstring on the conservative direction.
ATOMIC = ("Lit", "Const", "Attr", "Var")

#: Operand roots that make the comparison a CARDINALITY test rather than a bound.
CARDINALITY = ("Count",)

#: Keys under which a comparator's operands live, across the comparator spellings in
#: this codebase. `a`/`b` is the standard binary form.
OPERAND_KEYS = ("a", "b")

#: Quantifier `source` roots that enumerate a CODEBOOK — a global collection of held
#: candidates. See `is_codebook_crossing` for why `Neighbours`/`InNeighbours` is NOT
#: here: it is navigation WITHIN the matched observation's own locality, so a comparison
#: against it is "observation vs its own parts", not "observation vs codebook".
CODEBOOK_SOURCES = ("NodesOfType",)

#: Keys under which an `Attr` Term stores the attribute it reads. Real seeds use `key`;
#: the tripwire rung's synthetic batteries use `name`. Both are accepted.
ATTR_KEYS = ("key", "name")


class Comparison(NamedTuple):
    """One comparator found in a Term tree, with everything needed to judge it.

    Fields are APPEND-ONLY: `t2_bound_like` / `codebook_crossing` were added by the
    Attr-threshold rung and sit at the end so existing positional unpacking is unaffected.
    """

    rule: str            # enclosing rule name ("" when scanning a bare term)
    op: str              # Lt / Lte / Gt / Gte
    path: str            # JSON path from the scan root
    operand_roots: tuple  # root `type` of each operand, in order
    not_depth: int       # how many `Not` nodes enclose it (polarity)
    bound_like: bool     # the T1 verdict
    codebook_crossing: bool = False  # the T2 ADDITION (Attr-vs-Attr only)
    t2_bound_like: bool = False      # T1 ∨ codebook_crossing

    @property
    def negated(self) -> bool:
        return self.not_depth % 2 == 1

    @property
    def undecidable_residual(self) -> bool:
        """Atomic `Attr`-vs-`Attr` that T2 could NOT resolve.

        This is the class proven NOT structurally decidable in
        `VISION_AST_ATTR_PREREG.md` §1.5: a genuine `Lt(Attr(dist), Attr(bound))` and
        the tripwire rung's DECLARED non-bound `Lt(Attr(epoch), Attr(codebook_epoch))`
        have IDENTICAL ASTs once attribute names are erased. Members of this class are
        the reason the audit table reports a RANGE `[T2, T0]` rather than a verdict.
        """
        return (tuple(self.operand_roots) == ("Attr", "Attr")
                and not self.t2_bound_like)


def _root_type(operand: Any) -> str:
    """The operand's own root Term type. Non-dict operands are inline literals."""
    if isinstance(operand, dict):
        t = operand.get("type")
        return t if isinstance(t, str) else "<untyped>"
    return "<inline>"


def is_derived(operand: Any) -> bool:
    """True when the operand is a COMPUTED expression rather than a stored value.

    Unrecognised Terms are DERIVED — the conservative direction (see docstring).
    """
    root = _root_type(operand)
    if root == "<inline>":
        return False
    return root not in ATOMIC


def is_cardinality(operand: Any) -> bool:
    return _root_type(operand) in CARDINALITY


def classify(node: dict) -> bool:
    """T1: is this comparator node BOUND-LIKE?

    A bound compares against a COMPUTED MAGNITUDE. So: not a cardinality test, and at
    least one side must be derived.
    """
    operands = [node.get(k) for k in OPERAND_KEYS]
    if any(is_cardinality(o) for o in operands):
        return False
    return any(is_derived(o) for o in operands)


def _attr_key(operand: Any) -> str | None:
    """The attribute an `Attr` Term reads, under either spelling. None if not an Attr."""
    if not isinstance(operand, dict) or operand.get("type") != "Attr":
        return None
    for k in ATTR_KEYS:
        v = operand.get(k)
        if isinstance(v, str):
            return v
    return None


def vars_referenced(node: Any, acc: set | None = None) -> set:
    """Every `Var` name appearing anywhere inside `node`."""
    if acc is None:
        acc = set()
    if isinstance(node, dict):
        if node.get("type") == "Var" and isinstance(node.get("name"), str):
            acc.add(node["name"])
        for v in node.values():
            vars_referenced(v, acc)
    elif isinstance(node, list):
        for v in node:
            vars_referenced(v, acc)
    return acc


def _source_root(node: dict) -> str | None:
    src = node.get("source")
    return src.get("type") if isinstance(src, dict) else None


def is_codebook_crossing(node: dict, scope: dict) -> bool:
    """T2: does this comparator relate a CODEBOOK CANDIDATE to the observation?

    Derived in `VISION_AST_ATTR_PREREG.md` §1.2-1.4 and adopted only after four rival
    discriminators were rejected BY MEASUREMENT. All four conditions are required:

      1. BOTH operands rooted at `Attr` — this is EXACTLY the class T1 misses, so T2
         changes no verdict T1 already reaches.
      2. one operand references a variable bound by a quantifier ranging over a
         CODEBOOK enumeration (`NodesOfType`) — the candidate;
      3. the OTHER operand does not reference that candidate, so it reaches the matched
         observation — the comparison CROSSES the candidate/observation boundary;
      4. the two operands read DIFFERENT attribute keys — a bound is measurement vs
         threshold (`v0` vs `v0hi`), never like-for-like (`glabel` vs `glabel`, which is
         ordering / dedup / flood propagation).

    Condition 3 is what excludes `sd_redecode`'s
    `Lt(Attr(obs,'decoded_epoch'), Attr(ag,'codebook_epoch'))`: both its operands are
    match-bound, so no candidate is in scope and no admission is being decided.
    """
    a, b = (node.get(k) for k in OPERAND_KEYS)
    if _root_type(a) != "Attr" or _root_type(b) != "Attr":
        return False                                            # (1)
    ka, kb = _attr_key(a), _attr_key(b)
    if ka is None or kb is None or ka == kb:
        return False                                            # (4)
    va, vb = vars_referenced(a), vars_referenced(b)
    for owner, other in ((va, vb), (vb, va)):
        candidates = {v for v in owner
                      if scope.get(v, (None, None))[0] == "QUANT"
                      and scope[v][1] in CODEBOOK_SOURCES}       # (2)
        if candidates and not (candidates & other):
            return True                                         # (3)
    return False


def scope_from_match(rule: Any) -> dict:
    """Variables a rule's `match` triples bind. Absence-tolerant: a bare Term has none."""
    scope: dict = {}
    if not isinstance(rule, dict):
        return scope
    for triple in rule.get("match", []) or []:
        if not isinstance(triple, (list, tuple)):
            continue
        for name in triple:
            if isinstance(name, str):
                scope[name] = ("MATCH", None)
    return scope


def walk_terms_scoped(node: Any, scope: dict, path: str = "",
                      not_depth: int = 0) -> Iterator[tuple]:
    """`walk_terms`, additionally threading the VARIABLE SCOPE in force at each node.

    A Term carrying `var_name` binds that name over its own subtree (`Exists`, `Filter`,
    `Argmin`, `MaxOver`, …), recorded together with the root type of what it ranges over
    so `is_codebook_crossing` can ask whether that is a codebook.

    Kept SEPARATE from `walk_terms` rather than replacing it: `walk_terms` yields
    3-tuples that callers outside this module unpack positionally.
    """
    if isinstance(node, dict):
        t = node.get("type")
        inner = scope
        if isinstance(node.get("var_name"), str):
            inner = dict(scope)
            inner[node["var_name"]] = ("QUANT", _source_root(node))
        if isinstance(t, str):
            yield node, path, not_depth, scope
            if t == "Not":
                not_depth += 1
        for key, value in node.items():
            yield from walk_terms_scoped(
                value, inner, f"{path}.{key}" if path else key, not_depth)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk_terms_scoped(value, scope, f"{path}[{i}]", not_depth)


def walk_terms(node: Any, path: str = "", not_depth: int = 0) -> Iterator[tuple]:
    """Yield `(term_dict, path, not_depth)` for every typed Term in the tree.

    Recurses through dicts AND lists, so `where` clause lists, `Filter` predicates,
    `And`/`Or` operand lists and `effects` are all reached. `not_depth` counts
    enclosing `Not` nodes so a negated bound is visible AS negated.
    """
    if isinstance(node, dict):
        t = node.get("type")
        if isinstance(t, str):
            yield node, path, not_depth
            if t == "Not":
                not_depth += 1
        for key, value in node.items():
            yield from walk_terms(value, f"{path}.{key}" if path else key, not_depth)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk_terms(value, f"{path}[{i}]", not_depth)


def comparisons_in(tree: Any, rule: str = "", path: str = "") -> list:
    """Every comparator in `tree`, classified. This is T0; `.bound_like` is T1."""
    out = []
    for node, npath, ndepth, scope in walk_terms_scoped(tree, scope_from_match(tree), path):
        if node.get("type") in COMPARATORS:
            t1 = classify(node)
            crossing = is_codebook_crossing(node, scope)
            out.append(Comparison(
                rule=rule,
                op=node["type"],
                path=npath,
                operand_roots=tuple(_root_type(node.get(k)) for k in OPERAND_KEYS),
                not_depth=ndepth,
                bound_like=t1,
                codebook_crossing=crossing,
                t2_bound_like=t1 or crossing,
            ))
    return out


def audit_seed(seed: dict, rule_name: str | None = None) -> dict:
    """Audit a loaded seed dict. `rule_name` scopes to one rule; None scans them ALL.

    Scanning ALL rules by default is itself part of the repair: a rule-scoped
    assertion is evaded by relocating the bound into a sibling rule (inventory S1/S3).
    """
    rules = seed.get("rules", [])
    if rule_name is not None:
        rules = [r for r in rules if r.get("name") == rule_name]
    found: list = []
    for r in rules:
        found.extend(comparisons_in(r, rule=r.get("name", "")))
    bounds = [c for c in found if c.bound_like]
    t2_bounds = [c for c in found if c.t2_bound_like]
    residual = [c for c in found if c.undecidable_residual]
    return {
        "scope": rule_name or "<whole seed>",
        "n_rules_scanned": len(rules),
        "T0_any_comparator": len(found),
        "T1_bound_like": len(bounds),
        "T2_bound_like": len(t2_bounds),
        "T2_promoted_over_T1": len(t2_bounds) - len(bounds),
        # The class §1.5 proves NOT structurally decidable. Its members are why the
        # audit table reports a RANGE for this scope rather than a verdict.
        "undecidable_residual": len(residual),
        # BOUND-PRESENCE IS NOT BOUND-EFFICACY (§8): the true count of load-bearing
        # bounds lies in [T2, T0] and NO structural instrument narrows it further.
        "bound_range": [len(t2_bounds), len(found)],
        "range_is_tight": len(t2_bounds) == len(found),
        "has_bound": bool(bounds),
        "T2_has_bound": bool(t2_bounds),
        "T2_detail": [
            {"rule": c.rule, "op": c.op, "operands": list(c.operand_roots),
             "not_depth": c.not_depth, "negated": c.negated, "path": c.path,
             "via": "T1" if c.bound_like else "T2_codebook_crossing"}
            for c in t2_bounds
        ],
        "undecidable_residual_detail": [
            {"rule": c.rule, "op": c.op, "path": c.path,
             "why": "atomic Attr-vs-Attr with no codebook candidate in scope; "
                    "AST-identical to a declared non-bound once names are erased"}
            for c in residual
        ],
        "T0_by_op": {op: sum(1 for c in found if c.op == op) for op in COMPARATORS},
        "T1_detail": [
            {"rule": c.rule, "op": c.op, "operands": list(c.operand_roots),
             "not_depth": c.not_depth, "negated": c.negated, "path": c.path}
            for c in bounds
        ],
        "T0_non_bound_detail": [
            {"rule": c.rule, "op": c.op, "operands": list(c.operand_roots),
             "reason": ("cardinality"
                        if any(r in CARDINALITY for r in c.operand_roots)
                        else "atomic-vs-atomic (flag/epoch read)")}
            for c in found if not c.bound_like
        ],
    }


def audit_seed_file(path: str, rule_name: str | None = None) -> dict:
    with open(path) as fh:
        seed = json.load(fh)
    out = audit_seed(seed, rule_name)
    out["seed"] = path
    return out


def legacy_string_test(tree: Any, op: str = "Lte") -> bool:
    """THE OLD, BLIND TEST — kept so the repair can be measured AGAINST it.

    Returns True when the old assertion `'"type": "<op>"' not in blob` would PASS,
    i.e. when it reports 'no bound'. This is the instrument being replaced, retained
    as the control rather than deleted.
    """
    return f'"type": "{op}"' not in json.dumps(tree)
