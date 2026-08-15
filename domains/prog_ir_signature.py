"""prog_ir_signature — P3: hub Program-IR -> construction relation-systems.

PROGRAM_SYNTHESIS_PLAN.md §4-P3 / PROGRAM_SYNTHESIS_P3_PREREG.md §1. A FIXED,
MECHANICAL extraction walk from hub-IR Term-JSON (domains/prog_ir_emit /
prog_ir_rust / prog_ir_lua output — the shared IR, so every frame lands in
the SAME signature space) to the relation-system signatures the
`prog_construction` sd loop (seeds/prog_construction_loop.json) decodes.

CLAUDE.md admissibility: this module contains NO decisions over graph state.
It is (a) a fixed table-driven walk (the `prog_ir_emit` correspondence
precedent, one level up), (b) a mechanical seed loader
(`ensure_prog_construction_loop`, the `_ensure_shape_decode_loop` idiom), and
(c) mechanical Observation ingest / read-back (world-adapter I/O). The
recognize / merge / mint DECISIONS live in the seed's rules, in Rust, at
`run_rules` fixpoint.

THE GRAIN (registered in the prereg before anything ran):

  statement grain — one signature per statement; head relation
    ["pstmt", <variant>] first, then depth-1 structural relations:
    ["parg", field, abskind] per expression field (VAR/LIT/EXTERN/NONE or the
    node type — identifiers/literals/extern names NEVER appear: shape, not
    content), ["pop", op] for enum scalars, ["parity", field, n] for
    structural arities, ["pblock", field] PRESENCE-ONLY per non-empty block
    (block contents are their own observations — the run-5 fragmentation
    lesson). Predicates are pstmt/parg/pop/parity/pblock — namespaced so no
    other codebook's relations can cover or be covered by these.

  function grain — the ordered sequence of statement-grain construction
    labels of the top-level body (params excluded; bare ProgSeq desugar
    containers flattened) — the character-composition precedent one level up;
    the bigram corpus for the P4 lattice.
"""
from __future__ import annotations

import json
from fractions import Fraction
from typing import Any, Dict, Iterator, List, Optional

# --------------------------------------------------------------------------- #
#  Fixed tables (the only knowledge in this module).
# --------------------------------------------------------------------------- #
# statement variant -> (expr fields, enum-scalar fields, arity fields, block fields)
# Field names are the P1/P2 emission dialect verbatim (prog_ir_emit.py).
_STMT_FIELDS: Dict[str, Dict[str, tuple]] = {
    "ProgAssignVar":    {"expr": ("value",)},
    "ProgAugAssign":    {"expr": ("value",), "op": ("op",)},
    "ProgTupleUnpack":  {"expr": ("value",), "arity": ("targets",)},
    "ProgIfStmt":       {"expr": ("cond",), "block": ("then", "orelse")},
    "ProgWhile":        {"expr": ("cond",), "block": ("body", "orelse")},
    "ProgForEach":      {"expr": ("iter",), "block": ("body", "orelse")},
    "ProgLoopCtl":      {"op": ("kind",)},
    "ProgReturn":       {"expr": ("value",)},
    "ProgTryOr":        {"block": ("body", "handler")},
    "ProgRaise":        {"expr": ("exc",)},
    "ProgImportStmt":   {},
    "ProgAttrSet":      {"expr": ("obj", "value")},
    "ProgSubscriptSet": {"expr": ("obj", "index", "value")},
    "ProgDefFnParam":   {"expr": ("default",)},
}

_SEED_ID = "prog_construction_loop"
_KIND = "prog_construction"


def _abskind(e: Any) -> str:
    """Content-invariant kind token for an expression subtree (depth 1)."""
    if e is None:
        return "NONE"
    if not isinstance(e, dict):
        return "OPAQUE"
    t = e.get("type")
    if t == "Var":
        return "VAR"
    if t == "Lit":
        return "LIT"
    if t == "ProgCallExtern":
        return "EXTERN"
    return str(t)


def statement_signature(stmt: Any) -> List[List[Any]]:
    """One statement's relation-system. Head relation FIRST (the naming rule
    and the merge candidate-filter read it positionally); the remaining
    relations follow the fixed field order of `_STMT_FIELDS` — deterministic
    by construction, no sorting, no decisions."""
    if not isinstance(stmt, dict):
        return [["pstmt", "ExprStmt"], ["parg", "value", _abskind(stmt)]]
    t = str(stmt.get("type"))
    spec = _STMT_FIELDS.get(t)
    if spec is None:
        # a bare expression in statement position (Expr statements emit as
        # bare Terms — the P2 dialect), including EXTERN calls for effect.
        return [["pstmt", "ExprStmt"], ["parg", "value", _abskind(stmt)]]
    rels: List[List[Any]] = [["pstmt", t]]
    for f in spec.get("op", ()):
        rels.append(["pop", str(stmt.get(f))])
    for f in spec.get("arity", ()):
        v = stmt.get(f)
        rels.append(["parity", f, int(len(v)) if isinstance(v, (list, tuple)) else 0])
    for f in spec.get("expr", ()):
        rels.append(["parg", f, _abskind(stmt.get(f))])
    for f in spec.get("block", ()):
        if stmt.get(f) is not None:
            rels.append(["pblock", f])
    return rels


def sig_key(signature: List[List[Any]]) -> str:
    """Canonical JSON string of a signature — the mechanical dedup key."""
    return json.dumps(signature, separators=(",", ":"), sort_keys=False)


def iter_block_statements(block: Any) -> Iterator[Dict[str, Any]]:
    """Statements of a block, flattening bare ProgSeq desugar containers
    (the lua ipairs / prelude case) and skipping None. A non-Seq single
    statement IS the block (the P2 `_emit_block` collapse)."""
    if block is None:
        return
    if isinstance(block, dict) and block.get("type") == "ProgSeq":
        for s in block.get("stmts") or []:
            yield from iter_block_statements(s)
        return
    yield block


def function_statements(ir: Dict[str, Any], *, include_params: bool = False
                        ) -> List[Dict[str, Any]]:
    """Top-level statements of a function IR (the emit root ProgSeq),
    params excluded by default (prereg §1)."""
    out = []
    for s in iter_block_statements(ir):
        if not include_params and isinstance(s, dict) \
                and s.get("type") == "ProgDefFnParam":
            continue
        out.append(s)
    return out


def walk_statements(ir: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """EVERY statement in the function, recursively (nested blocks too —
    each is its own observation), params excluded, Seqs flattened."""
    for s in function_statements(ir):
        yield from _walk_stmt(s)


def _walk_stmt(stmt: Any) -> Iterator[Dict[str, Any]]:
    yield stmt
    if not isinstance(stmt, dict):
        return
    spec = _STMT_FIELDS.get(str(stmt.get("type"))) or {}
    for f in spec.get("block", ()):
        for child in iter_block_statements(stmt.get(f)):
            yield from _walk_stmt(child)


def function_signature(labels: List[str]) -> List[List[Any]]:
    """Function-grain relation-system: the ordered label sequence
    (character-composition, one level up). Provided for the P4 lattice /
    gates; not decoded by this phase's loop."""
    return [["fstmt", int(i), str(lb)] for i, lb in enumerate(labels)]


# --------------------------------------------------------------------------- #
#  Seed load + Observation ingest / read-back (mechanical adapter I/O).
# --------------------------------------------------------------------------- #
def ensure_prog_construction_loop(sub, native, ag_node) -> None:
    """Idempotently load the prog_construction_loop seed (Seed{id} marker
    guard — the `_ensure_shape_decode_loop` idiom) and default the agent's
    `prog_codebook_epoch` to 0 (a default init, not a decision). The DISTINCT
    epoch attr keeps this loop's re-decode arm entirely off the frozen
    shape_decode_loop seed."""
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == _SEED_ID:
            break
    else:
        from substrate.seed_loader import manifest_for
        summary = native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
        if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
            raise RuntimeError(
                "prog_construction_loop did not install cleanly: %r" % (summary,))
        sub.add_node("Seed", {"id": _SEED_ID, "version": "1.0.0"})
    if ag_node is not None:
        if sub.node(ag_node)["attrs"].get("prog_codebook_epoch") is None:
            sub.set_attr(ag_node, "prog_codebook_epoch", 0.0)


def observe_construction(sub, ag_node, signature: List[List[Any]], *,
                          key: Optional[str] = None,
                          occurrences: int = 1):
    """Mechanical ingest: one pending prog_construction Observation, wired
    `ag -observed-> obs`. pc_* statuses + the `kind` guard keep it invisible
    to the frozen sd loop's rules (which match `status == "pending"`)."""
    obs = sub.add_node("Observation", {
        "kind": _KIND,
        "signature": [list(r) for r in signature],
        "sig_key": key if key is not None else sig_key(signature),
        "occurrences": int(occurrences),
        "pc_status": "pending",
    })
    sub.add_edge(ag_node, "observed", obs)
    return obs


def read_observation(sub, obs) -> Dict[str, Any]:
    """Mechanical read-back of one observation's loop outcome."""
    at = sub.node(obs)["attrs"]
    minted_name = None
    for q in sub.neighbours(obs, "minted"):
        minted_name = _text(sub.node(q)["attrs"].get("name"))
    return {
        "status": at.get("pc_status"),
        "covered_by": _text(at.get("covered_by")),
        "minted": minted_name,
        "merge_with": _text(at.get("merge_with")),
        "merge_lgg": at.get("merge_lgg"),
        "sig_key": at.get("sig_key"),
    }


def construction_label(sub, obs) -> Optional[str]:
    """The construction label the loop assigned (minted quantum's name, or
    covered_by for a recognized/merged observation)."""
    r = read_observation(sub, obs)
    return r["minted"] or r["covered_by"]


def apply_marked_merge(sub, ag_node, obs) -> Optional[str]:
    """MECHANICAL application of a rule-decided merge (the prereg §2 split:
    decision in rules — pc_mark_merge computed merge_with + merge_lgg — the
    adapter only copies the verdict onto the graph and bumps the epoch).
    Returns the merged quantum's name, or None if the observation carries no
    complete verdict."""
    at = sub.node(obs)["attrs"]
    if at.get("pc_status") != "merge_marked":
        return None
    name = _text(at.get("merge_with"))
    lgg = at.get("merge_lgg")
    if not name or lgg is None:
        return None
    target = None
    for q in sub.nodes("ShapeSignature"):
        qa = sub.node(q)["attrs"]
        if qa.get("kind") == _KIND and _text(qa.get("name")) == name:
            target = q
            break
    if target is None:
        return None
    sub.set_attr(target, "signature", _plain(lgg))
    sub.set_attr(target, "provenance", "merged")
    sub.set_attr(target, "sig_key", "")
    sub.set_attr(target, "merged_count",
                 float(sub.node(target)["attrs"].get("merged_count") or 0.0) + 1.0)
    cur = sub.node(ag_node)["attrs"].get("prog_codebook_epoch") or 0.0
    sub.set_attr(ag_node, "prog_codebook_epoch", float(cur) + 1.0)
    return name


def prog_codebook(sub) -> List[Dict[str, Any]]:
    """Mechanical listing of the held prog_construction codebook, sorted by
    name (the determinism-artifact order)."""
    out = []
    for q in sub.nodes("ShapeSignature"):
        at = sub.node(q)["attrs"]
        if at.get("kind") != _KIND:
            continue
        out.append({
            "name": _text(at.get("name")),
            "signature": _plain(at.get("signature")),
            "provenance": at.get("provenance"),
            "induced": at.get("induced"),
            "merged_count": at.get("merged_count") or 0,
        })
    out.sort(key=lambda r: r["name"] or "")
    return out


def _text(v) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v)


def _plain(v):
    """tuples -> lists recursively (native.evaluate / attr read-back returns
    TUPLES, the documented gotcha) — for JSON artifacts and re-set_attr.
    Deliberately LOSSY (never a round-trip codec) — see
    `prog_synthesis.py::_plain`, the reference implementation this
    mirrors for parity.

    WIRE_BOUNDARY_SYSTEMIC_AUDIT (2026-08): brought to parity with
    `prog_synthesis.py::_plain`'s set/frozenset/Fraction handling — see
    `prog_chunk_growth.py::_plain`'s docstring for the full account of
    why this sibling copy existed and what it was missing. This module's
    own call sites (`signature`, a statement's structural LGG) are
    tuple/str/int-shaped in practice, so this was a latent gap, not a
    live failure — closed here so it can't become one silently."""
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, (set, frozenset)):
        try:
            return [_plain(x) for x in sorted(v)]
        except TypeError:
            return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {_plain(k): _plain(x) for k, x in v.items()}
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if isinstance(v, Fraction):
        return float(v)
    return v


__all__ = [
    "statement_signature", "sig_key", "iter_block_statements",
    "function_statements", "walk_statements", "function_signature",
    "ensure_prog_construction_loop", "observe_construction",
    "read_observation", "construction_label", "apply_marked_merge",
    "prog_codebook",
]
