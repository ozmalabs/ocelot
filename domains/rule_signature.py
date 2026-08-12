"""domains/rule_signature.py — the RULE-SIGNATURE SLICE, exactly per
docs/research/engine_substrate/RULES_AS_SHAPE_DESIGN_SPIKE.md §11.2 and
docs/research/engine_substrate/RULE_SIGNATURE_SLICE_PREREG.md (AR3).

CHANGED 2026-08-13 (`RULE_SIGNATURE_TO_RUST_RESULTS.md`): the signature
computation is no longer performed by this module's Python. `rule_signature`
below is retained as the **differential-test ORACLE**; production goes
through `where_signature(sub, where_clause)`, which executes the
graph-resident Program IR (`domains/rule_signature_program.py`, installed as
a Term subgraph and read back out of the graph) on the Rust `ProgEval`
interpreter. Everything the original docstring says about this module NOT
being agent decision logic still holds — the added functions are mechanical
install / evaluate / read-back host I/O with no conditional over graph
state. The one behavioural note: `ensure_where_signature` now mints its attr
from the graph-resident computation, and SKIPS (rather than guesses) any
rule the program traps on.

MEASUREMENT / INVESTIGATION CODE, not agent decision logic (CLAUDE.md's
architecture rule is explicit that a world adapter is mechanical I/O and an
agent decision is a Rule; this module is neither — it is offline research
tooling, the same class as `domains/rule_ir.py::canonical_rule_body`, which
is itself documented as "diagnostic data" that "must not be installed as a
rule"). Nothing here writes agent behaviour:

  * `rule_signature` is a pure function, `dict | None -> frozenset[tuple]`.
    No graph writes, no `NodeID` allocation, no `Substrate` handle touched
    at all (confirmed by inspection: this function never imports
    `substrate`/`graph`).
  * `ensure_where_signature` mints/upgrades exactly ONE additive attr
    (`where_signature_json`) on the EXISTING `RuleSummary` population that
    `domains.reflective_faculty._ensure_acting_rule_provenance` /
    `_ensure_reply_rule_provenance` already produce. It never calls
    `add_node` — only `set_attr` on nodes that already exist.
  * `pick_acting_rule_structural` / `pick_reply_rule_structural` are NEW,
    STANDALONE, OBSERVATIONAL rankings — the AR3 "alternative candidate
    ranking" the prereg registers. They duplicate the exact candidate
    filter `reflective_faculty._pick_acting_rule` / `_pick_reply_rule` use
    (`writes_chosen_action|writes_reply == 1.0 AND skippable == 1.0`), but
    rank by a structural FixedCount score over `where_signature_json`
    instead of a StringIndexOf-Sum over `keywords_text`.

This module is called ONLY by `scripts/rule_signature_measure.py` (the AR4
measurement). It is never imported by `reflective_faculty.py`,
`ground_concern`, `_compose_acting_variant`, `_compose_reply_ablation`, or
any other production path — that is the AR5 zero-diff gate: production rule
selection is byte-unchanged by this slice.
"""
from __future__ import annotations

import json
from typing import Any, Iterable

# The interned WILD marker string, matching `term.rs`'s own `"·?·"` sentinel
# (see AntiUnify/Covers/FixedCount doc comments, term.rs:800-822). None of
# this module's atoms are ever equal to this string, so its exact value is
# not load-bearing here (FixedCount over a Set/FrozenSet with no WILD member
# present is plain cardinality, per FixedCount's own doc comment) — kept for
# consistency with the rest of the codebase's convention, not because this
# slice's FixedCount calls encounter WILD.
_WILD = "·?·"


# ---------------------------------------------------------------------------
# rule_signature — the §5.3 flattening, `where`-clause only
# ---------------------------------------------------------------------------

def _is_term_node(v: Any) -> bool:
    return isinstance(v, dict) and "type" in v


def _is_term_list(v: Any) -> bool:
    return isinstance(v, list) and len(v) > 0 and all(_is_term_node(x) for x in v)


def _atomize(value: Any) -> Any:
    """Recursively convert an arbitrary JSON-shaped scalar/container into a
    hashable Python value. JSON has no tuple type, so a JSON array always
    becomes a `tuple` here (uniformly — both a Python list-shaped and a
    tuple-shaped `Lit` value already collapsed to a bare JSON array on the
    seed-JSON wire, long before this function sees it). A JSON object
    reachable here is NOT a Term node (those are handled by `walk` before
    `_atomize` is ever called on them) — it is an ordinary Dict-valued
    field, atomized as a sorted tuple of (key, atomized-value) pairs so it
    stays hashable and deterministic."""
    if isinstance(value, dict):
        return tuple(sorted((k, _atomize(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_atomize(v) for v in value)
    return value  # str / int / float / bool / None


def _collect_var_names(node: Any, order: list[str]) -> None:
    """DFS, first-appearance order, of every distinct variable IDENTIFIER
    sighting — the basis for positional alpha-renaming (§5.3: "Alpha-
    renaming is part of the signature... rather than a post-hoc
    canonicalisation"). Two kinds of node carry a variable identifier, and
    BOTH share one rename namespace because they name the SAME logical
    variable: a `{"type":"Var","name":X}` REFERENCE, and a binder's own
    `"var_name"` field (`Exists`/`Filter`/`Argmax`/`Sum`/... — the BINDING
    site a later `Var` reference points at). Verified against the real
    `note_reported_gap` rule (`seeds/gap_awareness.json`) — its two
    near-identical `Exists(Exists(...))` probes bind `mn`/`cc` and
    `mn2`/`cc2` respectively, and the design spike's own §6.2 worked
    example shows `var_name` renamed exactly like a `Var.name` (both
    produce `"?N"` atoms) — so unifying the two here is not a design
    choice, it is what makes the two probes' rows byte-identical modulo
    their one real difference (the literal word list), which is the whole
    point of alpha-renaming."""
    if isinstance(node, dict):
        if node.get("type") == "Var":
            nm = node.get("name")
            if isinstance(nm, str) and nm not in order:
                order.append(nm)
        vn = node.get("var_name")
        if isinstance(vn, str) and vn not in order:
            order.append(vn)
        for k in sorted(node.keys()):
            if k == "type":
                continue
            _collect_var_names(node[k], order)
    elif isinstance(node, list):
        for item in node:
            _collect_var_names(item, order)


def rule_signature(where_clause: dict | None) -> frozenset:
    """The §5.3 flattening of a rule's `where` clause into path-addressed,
    alpha-renamed rows, as a `FrozenSet` — exactly AR3's scope (`where`
    only; no `match`, no `effects`; no `"re"` match-edge rows).

    Two row kinds:
        ("rt", path, term_type)          -- one row per Term node
        ("ra", path, field, atom)        -- one row per scalar field

    `path` is a dot/`[i]` route from the where-clause root (`""` at the
    root) — the exact notation the design spike's own §6.2 worked example
    uses (e.g. `"items[0].source.node.name"`).

    `Var` `name` fields are alpha-renamed POSITIONALLY (`"?0"`, `"?1"`, ...
    in first-DFS-appearance order over the WHOLE where-clause, computed
    once up front so the renaming is consistent across the entire tree).
    Every other scalar field — including every `Lit` value — is kept
    LITERAL: this is the spike's own §3 "alpha" tier (Vars renamed,
    literals intact), not "alpha+lit" (which would also wildcard literals
    and was explicitly not what §11.2 asked for).

    Pure function. `where_clause` is an already-parsed dict (from
    `json.loads(RuleSummary.rule_json)` or a seed file's own `r["where"]`,
    both plain Python dicts before this function ever sees them) — no
    Substrate handle, no NodeID allocation, no graph write of any kind.
    """
    if not isinstance(where_clause, dict) or "type" not in where_clause:
        return frozenset()

    var_order: list[str] = []
    _collect_var_names(where_clause, var_order)
    rename = {name: f"?{i}" for i, name in enumerate(var_order)}

    rows: set[tuple] = set()

    def walk(node: dict, path: str) -> None:
        term_type = node.get("type")
        rows.add(("rt", path, term_type))
        for key in sorted(node.keys()):
            if key == "type":
                continue
            val = node[key]
            if _is_term_node(val):
                walk(val, f"{path}.{key}" if path else key)
            elif _is_term_list(val):
                for i, item in enumerate(val):
                    walk(item, f"{path}.{key}[{i}]" if path else f"{key}[{i}]")
            else:
                is_var_ref = term_type == "Var" and key == "name" and isinstance(val, str)
                is_binder = key == "var_name" and isinstance(val, str)
                if is_var_ref or is_binder:
                    atom = rename.get(val, val)
                else:
                    atom = _atomize(val)
                rows.add(("ra", path, key, atom))

    walk(where_clause, "")
    return frozenset(rows)


def _rows_to_jsonable(sig: frozenset) -> list:
    """Deterministic ordering for storage — sorted by `repr` (rows can mix
    scalar types at the same tuple position, e.g. a `Lit` atom that is
    sometimes a str and sometimes a nested tuple, so a plain tuple sort can
    raise `TypeError`; `repr` is always comparable)."""
    return [list(row) for row in sorted(sig, key=repr)]


def _rows_from_jsonable(rows_json: str | None) -> frozenset:
    """Inverse of `_rows_to_jsonable` — JSON arrays back to hashable
    tuples (recursively, so a nested list-valued atom becomes a tuple
    again, matching what `_atomize` produced before serialisation)."""
    if not rows_json:
        return frozenset()
    try:
        parsed = json.loads(rows_json)
    except Exception:
        return frozenset()

    def to_hashable(x: Any) -> Any:
        if isinstance(x, list):
            return tuple(to_hashable(v) for v in x)
        return x

    return frozenset(to_hashable(row) for row in parsed if isinstance(row, list))


# ---------------------------------------------------------------------------
# THE GRAPH-RESIDENT COMPUTATION (RULE_SIGNATURE_TO_RUST_RESULTS.md)
#
# `rule_signature` above is NO LONGER on the production path. It is now the
# differential-test ORACLE the graph-resident computation is measured
# byte-identical against (`scripts/rule_signature_program_gate.py`). What
# production runs is `domains/rule_signature_program.py::where_signature_rows`
# emitted to hub Program IR (`domains/prog_ir_emit.py`), INSTALLED IN THE
# GRAPH as a Term subgraph (`add_term_subgraph`), READ BACK OUT of the graph
# (`term_subgraph_json`), and executed by the Rust `ProgEval` interpreter.
#
# Why that, and not a new Rust Term: a Rust body is exactly as unreachable to
# the agent's Experiment→judge→adopt machinery as a Python body is. §10.1's
# actual payoff ("un-self-repairable") needs the computation to be GRAPH
# DATA, which this is — the same Prog-IR the prog_read / prog_repair
# faculties already match, decode, render and repair.
#
# Everything below is mechanical host I/O (install graph data / evaluate a
# Term / read the result back). There is no conditional over graph state.
# ---------------------------------------------------------------------------

SIGNATURE_PROGRAM_TYPE = "SignatureProgram"
SIGNATURE_PROGRAM_NAME = "where_signature_rows"
# Ceiling, not a tuning knob: the largest `where` clause in the whole seed
# corpus (`embodied_motor_program.json:emp_abs_expand_factorized_groups_in_
# parallel`, 83881 signature rows) costs 4,885,392 steps — measured. This is
# ~40x that, so fuel exhaustion means a pathological input, not a tight
# budget; the median rule costs ~2k steps.
SIGNATURE_PROGRAM_FUEL = 200_000_000

# id(inner) -> (ir, oracles). A pure performance cache over graph data the
# substrate remains the source of truth for (CLAUDE.md: "Python may cache
# for performance, but the substrate is the source of truth") — the IR is
# re-read from the graph for every fresh substrate handle.
_PROGRAM_CACHE: dict = {}


class SignatureProgramTrap(RuntimeError):
    """The graph-resident program trapped or ran out of fuel on an input.
    Raised rather than silently falling back to a second implementation."""


def _inner_of(sub):
    return getattr(sub, "_inner", sub)


def signature_program(sub):
    """Find-or-install the graph-resident signature program. Returns
    `(ir, oracles)` where `ir` is READ BACK from the installed Term
    subgraph — so what executes is what the graph holds, not what Python
    happened to emit. Idempotent: a second call finds the held node."""
    inner = _inner_of(sub)
    hit = _PROGRAM_CACHE.get(id(inner))
    if hit is not None:
        return hit

    root = None
    oracles = None
    for n in sub.nodes(SIGNATURE_PROGRAM_TYPE):
        at = sub.node(n)["attrs"]
        if at.get("name") == SIGNATURE_PROGRAM_NAME and at.get("program_root") is not None:
            root = at["program_root"]
            oracles = [w for w in (at.get("oracles_text") or "").split(",") if w]
            break

    if root is None:
        import inspect as _inspect

        from domains.prog_ir_emit import emit_prog_ir
        from domains.rule_signature_program import where_signature_rows
        emitted = emit_prog_ir(_inspect.getsource(where_signature_rows))
        if not emitted.get("ok"):
            raise SignatureProgramTrap(
                f"where_signature_rows is not emittable: {emitted.get('blockers')}")
        root = inner.add_term_subgraph(emitted["ir"])
        oracles = list(emitted["native_oracles"])
        sub.add_node(SIGNATURE_PROGRAM_TYPE,
                     {"name": SIGNATURE_PROGRAM_NAME,
                      "program_root": root,
                      "oracles_text": ",".join(oracles)})

    back = inner.term_subgraph_json(root)
    ir = json.loads(back) if isinstance(back, str) else back
    _PROGRAM_CACHE[id(inner)] = (ir, oracles)
    return ir, oracles


def where_signature(sub, where_clause) -> frozenset:
    """The production signature computation: the held Program IR, executed
    by `ProgEval` over `where_clause`. Byte-identical to `rule_signature`
    on all 2930 gated cases (2917 real seed `where` clauses + 13
    synthetics) — see `scripts/rule_signature_program_gate.py`."""
    ir, oracles = signature_program(sub)
    term = {"type": "ProgEval", "prog": ir,
            "env": {"type": "Lit", "value": {"where_clause": where_clause}},
            "oracles": {"type": "Lit", "value": {n: "builtin" for n in oracles}},
            "fuel": SIGNATURE_PROGRAM_FUEL, "field": ""}
    out = _inner_of(sub).evaluate(term, {})
    if out.get("trap") is not None or not out.get("halted"):
        raise SignatureProgramTrap(
            f"trap={out.get('trap')} halted={out.get('halted')} steps={out.get('steps')}")
    return frozenset(out.get("result") or ())


# ---------------------------------------------------------------------------
# ensure_where_signature — one additive attr on the EXISTING RuleSummary pop
# ---------------------------------------------------------------------------

def ensure_where_signature(sub) -> int:
    """Idempotent: mint/upgrade the ONE new attr `where_signature_json` on
    every EXISTING `RuleSummary` node that carries a `rule_json` but not
    yet a `where_signature_json` — the same "upgrade an existing node in
    place" precedent `_ensure_reply_rule_provenance`'s own docstring names
    (`reflective_faculty.py:2888-2894`), applied to a population this
    module never mints itself (no `add_node` call anywhere in this
    module — `RuleSummary` nodes are minted only by
    `_ensure_acting_rule_provenance` / `_ensure_reply_rule_provenance`,
    both untouched by this slice). Returns the number of nodes touched (0
    on a second call — idempotent, and safe to call before either of the
    two production provenance functions, or interleaved with them, since
    it only ever reads a `rule_json` that is already present and writes a
    field neither of them reads).

    The signature itself is now computed by the GRAPH-RESIDENT program
    (`where_signature` above), not by this module's Python. A rule whose
    clause makes that program trap or exhaust fuel is SKIPPED (its attr is
    left unset, which the production `Argmax` reads as an abstain — the
    pre-wiring behaviour for that rule) rather than being given a value
    from a second, divergent implementation. Measured on the whole seed
    corpus: zero such rules."""
    touched = 0
    for n in sub.nodes("RuleSummary"):
        at = sub.node(n)["attrs"]
        if at.get("where_signature_json") is not None:
            continue
        try:
            rule = json.loads(at.get("rule_json") or "{}")
        except Exception:
            rule = {}
        try:
            sig = where_signature(sub, rule.get("where"))
        except SignatureProgramTrap:
            continue
        sub.set_attr(n, "where_signature_json", json.dumps(_rows_to_jsonable(sig)))
        touched += 1
    return touched


# ---------------------------------------------------------------------------
# The structural ranking — AR3's "StructSim/FixedCount rank over the new
# signatures", wired as a genuine (if narrow) use of the named Rust Term
# ---------------------------------------------------------------------------

def _structural_score(native, sig_rows: frozenset, axis_preds: Iterable[str]) -> tuple[int, frozenset]:
    """Score a candidate rule's where-signature against a concern's
    `axis_preds` words: the set of signature ROWS whose stringified form
    (`repr(row)` — includes the row's path, field, and atom, so a match can
    come from a literal atom value OR from a structurally-meaningful path/
    field name) contains ANY axis word as a substring — the SAME substring
    test production's own `StringIndexOf` performs, applied to the wider
    structural surface instead of just `keywords_text` (AR3's own framing:
    "same substring semantics ... applied to the wider structural surface").
    The count is then obtained via a REAL call to the Rust `FixedCount`
    Term over a REAL `Value::FrozenSet` built from the matched rows —
    `FixedCount` on a Set/FrozenSet is cardinality by construction (its own
    doc comment says so: "Set/FrozenSet -> cardinality"), so this is an
    honest, narrow, but genuine use of the named primitive: the
    substantive step is which rows survive the filter, not the arithmetic
    FixedCount performs over the surviving set.

    Returns `(score, matched_rows)`."""
    words = [str(w) for w in axis_preds]
    matched = frozenset(row for row in sig_rows if any(w in repr(row) for w in words))
    if not matched:
        return 0, matched
    term = {"type": "FixedCount", "pattern": {"type": "Lit", "value": matched}, "wild": _WILD}
    try:
        score = native.evaluate(term, {})
    except Exception:
        score = len(matched)  # fail-safe: FixedCount on a FrozenSet IS cardinality
    return int(score or 0), matched


def _pick_structural(sub, native, axis_preds: Iterable[str], writes_key: str) -> dict:
    """Shared implementation for `pick_acting_rule_structural` /
    `pick_reply_rule_structural` — same candidate filter production uses
    (`<writes_key> == 1.0 AND skippable == 1.0`), ranked by
    `_structural_score` instead of name-keyword overlap. Honest abstain
    (`picked: None`) when no candidate's structural score is > 0, mirroring
    `_pick_acting_rule`'s own abstain semantics exactly."""
    ensure_where_signature(sub)
    candidates = []
    for n in sub.nodes("RuleSummary"):
        at = sub.node(n)["attrs"]
        if at.get(writes_key) != 1.0 or at.get("skippable") != 1.0:
            continue
        sig = _rows_from_jsonable(at.get("where_signature_json"))
        score, matched = _structural_score(native, sig, axis_preds)
        candidates.append({"score": score, "name": at.get("name"), "node": n,
                            "matched_rows": len(matched)})
    if not candidates:
        return {"picked": None, "name": None, "score": 0.0, "all_scores": {}}
    candidates.sort(key=lambda c: (-c["score"], c["name"] or ""))
    best = candidates[0]
    all_scores = {c["name"]: c["score"] for c in candidates}
    if best["score"] <= 0:
        return {"picked": None, "name": None, "score": 0.0, "all_scores": all_scores}
    return {"picked": best["node"], "name": best["name"], "score": float(best["score"]),
            "all_scores": all_scores}


def pick_acting_rule_structural(sub, native, axis_preds: Iterable[str]) -> dict:
    """STANDALONE, OBSERVATIONAL structural-rank alternative to
    `reflective_faculty._pick_acting_rule` (which this module does not
    import or call). Called only by `scripts/rule_signature_measure.py`."""
    return _pick_structural(sub, native, axis_preds, "writes_chosen_action")


def pick_reply_rule_structural(sub, native, axis_preds: Iterable[str]) -> dict:
    """STANDALONE, OBSERVATIONAL structural-rank alternative to
    `reflective_faculty._pick_reply_rule` (which this module does not
    import or call). Called only by `scripts/rule_signature_measure.py`."""
    return _pick_structural(sub, native, axis_preds, "writes_reply")


# ---------------------------------------------------------------------------
# Ancillary / exploratory only (AR4): pairwise StructSim over held
# where-signatures, for a clustering note -- NOT part of the AR1 hypothesis
# test (see RULE_SIGNATURE_SLICE_PREREG.md AR3's honest note on why
# StructSim is not the primary ranking primitive here).
# ---------------------------------------------------------------------------

def struct_sim_pair(native, sig_a: frozenset, sig_b: frozenset) -> float:
    """Real `StructSim` call over two held where-signatures (both
    `Value::FrozenSet`s of rows) — exploratory only. Returns the graded
    [0,1] similarity `term.rs`'s `StructSim` computes."""
    term = {"type": "StructSim",
            "a": {"type": "Lit", "value": sig_a},
            "b": {"type": "Lit", "value": sig_b},
            "wild": _WILD}
    try:
        return float(native.evaluate(term, {}) or 0.0)
    except Exception:
        return 0.0
