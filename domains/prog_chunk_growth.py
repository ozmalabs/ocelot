"""prog_chunk_growth — P7-C: the IDIOM-GRAIN chunk layer's mechanical rim.

PROGRAM_SYNTHESIS_P7C.md §1 (registered rules). The layer between P3's
statement-variant grain (saturation-at-16; family-collapsing 2/3 join at
depth 1) and whole-function grain: recurring 2-4-statement windows and
single compound statements with their bodies, leaves role-abstracted
(variable names → positional roles v0/v1/…, literal values → slot tokens),
extern/attribute/op names kept CONCRETE (idiom identity).

CLAUDE.md admissibility — this module contains NO decisions over graph
state. It is:

  (a) a FIXED extraction walk (`chunk_candidates` / `chunk_record`): hub-IR
      Term-JSON → role-abstracted chunk records — the `prog_ir_signature`
      precedent one grain up; deterministic, table-driven, no conditionals
      over graph state;
  (b) mechanical installers (`install_mined_chunks`, `ensure_chunk_growth`)
      — the `ensure_write_codebook` / `_ensure_shape_decode_loop` idiom,
      Seed-marker guarded, plus the sanctioned three-line
      `write_codebook_epoch` bump (`code_write_growth._teach_shape`'s own
      counter — a Python builder bumping an epoch is the established move);
  (c) mechanical Observation ingest (`scan_marked_programs`) applied ONLY
      to Programs a RULE marked (`ckg_mark_scan` in
      seeds/prog_chunk_growth.json) — decision in rules, application in
      the adapter, the documented P3 split;
  (d) engine-computed names (`chunk_entry_name`): StringConcat/SnakeCase/
      ToJsonString via `native.evaluate` — the P3 naming law (bounded,
      never a Python namer).

The recognize/mint DECISIONS live in seeds/prog_chunk_growth.json
(`ckg_recognize` / `ckg_mint`), in Rust, at `run_rules` fixpoint. The
self-taught mint is FULLY in-rule (the observation carries the prepared
facts; the rule decides novelty via Not-Exists `Covers` over `chunk_rels`
and applies the mint + epoch bump itself).
"""
from __future__ import annotations

import json
import os
import re
from fractions import Fraction
from typing import Any, Dict, Iterator, List, Optional, Tuple

from domains import prog_ir_signature as pis
from domains.code_writing import _STOPWORDS
from domains.prog_ir_emit import NATIVE_ORACLES

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_ID = "prog_chunk_growth"
_CODEBOOK_SEED_ID = "prog_chunk_codebook"
_ARTIFACT = os.path.join(_ROOT, "results", "prog_chunk_mine.json")
_KIND = "prog_chunk"
_WILD = ["·?·"]

# --------------------------------------------------------------------------- #
#  Fixed tables (the only knowledge in this module).
# --------------------------------------------------------------------------- #
# fields that carry VARIABLE NAMES (role-abstracted). Extern names
# (ProgCallExtern.name), attribute names, import modules, enum ops stay
# CONCRETE — idiom identity (registered §1.2).
_ROLE_FIELDS: Dict[str, Tuple[str, ...]] = {
    "Var": ("name",),
    "ProgAssignVar": ("name",),
    "ProgAugAssign": ("name",),
    "ProgForEach": ("var",),
    "ProgTryOr": ("exc_var",),
    "Fold": ("var_name", "acc_name"),
}
_ROLE_LIST_FIELDS: Dict[str, Tuple[str, ...]] = {
    "ProgTupleUnpack": ("targets",),
}
_COMPOUND_TYPES = ("ProgIfStmt", "ProgWhile", "ProgForEach", "ProgTryOr")
_WINDOW_SIZES = (2, 3, 4)


# --------------------------------------------------------------------------- #
#  Role/slot abstraction (fixed, deterministic walk — sorted dict keys).
# --------------------------------------------------------------------------- #
def _abstract(node: Any, roles: Dict[str, str], lits: List[Any]):
    """Deep-copy `node` with variable names → roles and Lit values → slot
    markers ({"__slot__": k}); records literal values in walk order."""
    if isinstance(node, dict):
        t = node.get("type")
        out: Dict[str, Any] = {}
        role_fields = _ROLE_FIELDS.get(str(t), ())
        role_list_fields = _ROLE_LIST_FIELDS.get(str(t), ())
        for k in sorted(node.keys()):
            v = node[k]
            if t == "Lit" and k == "value":
                out[k] = {"__slot__": len(lits)}
                lits.append(v)
            elif k in role_fields and isinstance(v, str):
                out[k] = roles.setdefault(v, "v%d" % len(roles))
            elif k in role_list_fields and isinstance(v, (list, tuple)):
                out[k] = [roles.setdefault(x, "v%d" % len(roles))
                          if isinstance(x, str) else _abstract(x, roles, lits)
                          for x in v]
            else:
                out[k] = _abstract(v, roles, lits)
        return out
    if isinstance(node, (list, tuple)):
        return [_abstract(x, roles, lits) for x in node]
    return node


def abstract_expr(term: Any) -> Tuple[Any, List[Any]]:
    """Public wrapper over `_abstract` for a single EXPRESSION subtree (not
    a statement list) — Arc 2 Q3's starter-shape affinity match reuses the
    SAME role/slot abstraction the chunk grain uses, one level down (an
    expression, not a statement window), so a train task's one-line
    `return <expr>` body compares structurally against a starter
    construction's `ground_template.term` on EQUAL footing (both walked
    with a fresh empty roles map, so variable names never matter — only
    shape does). Returns (abstract_json, lit_values_in_walk_order)."""
    lits: List[Any] = []
    abstract = _abstract(term, {}, lits)
    return abstract, lits


def _fill_slots(node: Any, values: List[Any]) -> Any:
    """Inverse of the slot abstraction: {"__slot__": k} → values[k]."""
    if isinstance(node, dict):
        if set(node.keys()) == {"__slot__"}:
            return values[int(node["__slot__"])]
        return {k: _fill_slots(v, values) for k, v in node.items()}
    if isinstance(node, (list, tuple)):
        return [_fill_slots(x, values) for x in node]
    return node


def _leaf_atom(v: Any) -> Any:
    if isinstance(v, str):
        return v
    return json.dumps(v, sort_keys=True, separators=(",", ":"))


def _flatten_rels(abstract_stmts: List[Any], labels: List[str]) -> List[List[Any]]:
    """Chunk → flat relation-system (["ckstmt", i, label] head rows +
    ["ck", i, path, atom] leaf rows) — positional, equal-shape aligned, the
    AntiUnify/FixedCount/Covers representation (registered §1.2)."""
    rels: List[List[Any]] = []

    def walk(node: Any, i: int, path: str):
        if isinstance(node, dict):
            if set(node.keys()) == {"__slot__"}:
                rels.append(["ck", i, path, "slot%d" % int(node["__slot__"])])
                return
            for k in sorted(node.keys()):
                walk(node[k], i, (path + "." + k) if path else k)
            return
        if isinstance(node, (list, tuple)):
            for j, x in enumerate(node):
                walk(x, i, "%s.%d" % (path, j) if path else str(j))
            return
        rels.append(["ck", i, path, _leaf_atom(node)])

    for i, (st, lb) in enumerate(zip(abstract_stmts, labels)):
        rels.append(["ckstmt", i, lb])
        walk(st, i, "")
    return rels


# --------------------------------------------------------------------------- #
#  Free-role detection (fixed binding walk — args of the chunk template).
# --------------------------------------------------------------------------- #
def _free_names(stmts: List[Any]) -> List[str]:
    bound: set = set()
    free: List[str] = []

    def read(e: Any):
        if isinstance(e, dict):
            t = e.get("type")
            if t == "Var":
                n = e.get("name")
                if isinstance(n, str) and n not in bound and n not in free:
                    free.append(n)
                return
            if t == "Fold":
                read(e.get("source"))
                read(e.get("init"))
                saved = set(bound)
                for f in ("var_name", "acc_name"):
                    if isinstance(e.get(f), str):
                        bound.add(e[f])
                read(e.get("body"))
                bound.clear()
                bound.update(saved)
                return
            for k in sorted(e.keys()):
                if k == "type":
                    continue
                read(e[k])
            return
        if isinstance(e, (list, tuple)):
            for x in e:
                read(x)

    def block(b: Any):
        for s in pis.iter_block_statements(b):
            stmt(s)

    def stmt(s: Any):
        if not isinstance(s, dict):
            read(s)
            return
        t = str(s.get("type"))
        if t == "ProgAssignVar":
            read(s.get("value"))
            bound.add(s.get("name"))
        elif t == "ProgAugAssign":
            read(s.get("value"))
            n = s.get("name")
            if isinstance(n, str) and n not in bound and n not in free:
                free.append(n)
            bound.add(n)
        elif t == "ProgTupleUnpack":
            read(s.get("value"))
            for n in s.get("targets") or []:
                bound.add(n)
        elif t == "ProgForEach":
            read(s.get("iter"))
            bound.add(s.get("var"))
            block(s.get("body"))
            block(s.get("orelse"))
        elif t in ("ProgIfStmt",):
            read(s.get("cond"))
            block(s.get("then"))
            block(s.get("orelse"))
        elif t == "ProgWhile":
            read(s.get("cond"))
            block(s.get("body"))
            block(s.get("orelse"))
        elif t == "ProgTryOr":
            block(s.get("body"))
            if isinstance(s.get("exc_var"), str):
                bound.add(s["exc_var"])
            block(s.get("handler"))
        elif t == "ProgReturn":
            read(s.get("value"))
        elif t == "ProgRaise":
            read(s.get("exc"))
        elif t == "ProgAttrSet":
            read(s.get("obj"))
            read(s.get("value"))
        elif t == "ProgSubscriptSet":
            read(s.get("obj"))
            read(s.get("index"))
            read(s.get("value"))
        elif t in ("ProgLoopCtl", "ProgImportStmt", "ProgDefFnParam"):
            pass
        else:
            read(s)

    for s in stmts:
        stmt(s)
    return free


# --------------------------------------------------------------------------- #
#  Trigger derivation (mechanical; registered §1.5 incl. the honesty clause:
#  head/extern/op words only — no NL-request corpus exists for this code
#  corpus, so cueing is expected weak; duplicate-label chunks are not
#  cueable under the P4-B lattice's distinct-label contract and get []).
# --------------------------------------------------------------------------- #
_CAMEL = re.compile(r"[A-Z][a-z0-9]*|[a-z0-9]+")


def _words(s: str) -> List[str]:
    return _CAMEL.findall(s or "")


def _collect_externs_ops(node: Any, ext: List[str], ops: List[str]):
    if isinstance(node, dict):
        t = node.get("type")
        if t == "ProgCallExtern" and isinstance(node.get("name"), str):
            if node["name"] not in ext:
                ext.append(node["name"])
        if t == "ProgAugAssign" and isinstance(node.get("op"), str):
            if node["op"] not in ops:
                ops.append(node["op"])
        for k in sorted(node.keys()):
            _collect_externs_ops(node[k], ext, ops)
    elif isinstance(node, (list, tuple)):
        for x in node:
            _collect_externs_ops(x, ext, ops)


def _has_bare_loopctl(stmts: List[Any]) -> bool:
    """Fixed structural check: a ProgLoopCtl not nested under a loop WITHIN
    the chunk — such a chunk cannot be a whole-function body (ProgEval traps
    on bare break/continue), so it is not cueable (hole-fill only)."""

    def visit(s: Any, in_loop: bool) -> bool:
        if not isinstance(s, dict):
            return False
        t = str(s.get("type"))
        if t == "ProgLoopCtl":
            return not in_loop
        spec = pis._STMT_FIELDS.get(t) or {}
        inner_loop = in_loop or t in ("ProgForEach", "ProgWhile")
        for f in spec.get("block", ()):
            for child in pis.iter_block_statements(s.get(f)):
                if visit(child, inner_loop):
                    return True
        return False

    return any(visit(s, False) for s in stmts)


def cue_exclusion_reason(labels: List[str], stmts: List[Any]) -> Optional[str]:
    """Cueability = top-level proposability, three FIXED structural checks
    (P7C §1.5 + the post-mine amendment §2.3): (1) distinct labels — the
    P4-B ordering lattice connects only distinct labels; (2) extern names
    ⊆ the evaluator's NATIVE_ORACLES — an unsuppliable extern traps every
    row by construction; (3) no bare loop-control — traps outside a loop.
    A non-cueable chunk is still minted (descent hole-fill data); it just
    carries no trigger vocabulary."""
    if len(set(labels)) != len(labels):
        return "duplicate_labels_lattice_contract"
    ext: List[str] = []
    ops: List[str] = []
    _collect_externs_ops(stmts, ext, ops)
    if any(name not in NATIVE_ORACLES for name in ext):
        return "extern_outside_native_oracles"
    if _has_bare_loopctl(stmts):
        return "bare_loop_control"
    return None


def raw_trigger_tokens(labels: List[str], stmts: List[Any]) -> List[str]:
    """The mechanical token derivation (head words + extern words + op
    words, stopword-images dropped) — reported for EVERY chunk in the
    artifact regardless of cueability (honesty: the derivation is weak,
    and the reader can see what it would have been)."""
    toks: List[str] = []
    for lb in labels:
        base = lb[4:] if lb.startswith("Prog") else lb
        for w in _words(base):
            toks.append(w.upper())
    ext: List[str] = []
    ops: List[str] = []
    _collect_externs_ops(stmts, ext, ops)
    for name in ext:
        for w in _words(name):
            toks.append(w.upper())
    for op in ops:
        for w in _words(op):
            toks.append(w.upper())
    out: List[str] = []
    for t in toks:
        if not t or t.lower() in _STOPWORDS:
            continue     # a stopword token can never match a request token
        if t not in out:
            out.append(t)
    return out


def derive_triggers(labels: List[str], stmts: List[Any]) -> List[str]:
    if cue_exclusion_reason(labels, stmts) is not None:
        return []
    return raw_trigger_tokens(labels, stmts)


# --------------------------------------------------------------------------- #
#  Candidate enumeration (the registered grain, §1.2).
# --------------------------------------------------------------------------- #
def _blocks(ir: Dict[str, Any]) -> Iterator[List[Any]]:
    """Every statement block in the function: top level + nested, params
    excluded, ProgSeq flattened — the P3 walk's block enumeration."""
    top = pis.function_statements(ir)
    stack: List[List[Any]] = [top]
    while stack:
        blk = stack.pop(0)
        yield blk
        for s in blk:
            if not isinstance(s, dict):
                continue
            spec = pis._STMT_FIELDS.get(str(s.get("type"))) or {}
            for f in spec.get("block", ()):
                inner = list(pis.iter_block_statements(s.get(f)))
                if inner:
                    stack.append(inner)


def _is_compound(s: Any) -> bool:
    if not isinstance(s, dict) or str(s.get("type")) not in _COMPOUND_TYPES:
        return False
    spec = pis._STMT_FIELDS.get(str(s.get("type"))) or {}
    return any(s.get(f) is not None for f in spec.get("block", ()))


def chunk_record(stmt_list: List[Any]) -> Dict[str, Any]:
    """One candidate chunk → its full record (fixed walk, no decisions)."""
    labels = [str(pis.statement_signature(s)[0][1]) for s in stmt_list]
    roles: Dict[str, str] = {}
    lits: List[Any] = []
    abstract = [_abstract(s, roles, lits) for s in stmt_list]
    key = json.dumps(abstract, sort_keys=True, separators=(",", ":"))
    rels = _flatten_rels(abstract, labels)
    free = _free_names(stmt_list)
    args = [roles[n] for n in free if n in roles]
    return {
        "chunk_key": key,
        "labels": labels,
        "abstract": abstract,
        "rels": rels,
        "args": args,
        "triggers": derive_triggers(labels, stmt_list),
        "derived_tokens": raw_trigger_tokens(labels, stmt_list),
        "cue_excluded": cue_exclusion_reason(labels, stmt_list),
        "lit_values": lits,
        "n_stmts": len(stmt_list),
    }


def chunk_candidates(ir: Dict[str, Any]) -> List[Dict[str, Any]]:
    """All candidate chunks of one function IR, deterministic order."""
    out: List[Dict[str, Any]] = []
    for blk in _blocks(ir):
        n = len(blk)
        for w in _WINDOW_SIZES:
            for j in range(0, n - w + 1):
                out.append(chunk_record(blk[j:j + w]))
        for s in blk:
            if _is_compound(s):
                out.append(chunk_record([s]))
    return out


def ground_template_for(rec: Dict[str, Any], fill_values: List[Any]) -> Dict[str, Any]:
    """The proposable write-codebook template: role-named stmts with the
    given slot fills (corpus-modal at mine time; the occurrence's own at
    self-teach time), args = the chunk's free roles."""
    stmts = _fill_slots(rec["abstract"], list(fill_values))
    return {
        "desc": "mined idiom: " + " + ".join(rec["labels"]),
        "mode": "code_write_stmts",
        "args": list(rec["args"]),
        "stmts": stmts,
    }


# --------------------------------------------------------------------------- #
#  Engine-computed names (the P3 naming law — never a Python namer).
# --------------------------------------------------------------------------- #
def chunk_entry_name(native, head_label: str, n_stmts: int, idx: int) -> str:
    """`ck_<snake(head)>_n<stmts>_q<idx>` via StringConcat/SnakeCase/
    ToJsonString — bounded by construction (gated)."""
    return native.evaluate({
        "type": "StringConcat", "parts": [
            {"type": "Lit", "value": "ck_"},
            {"type": "SnakeCase", "text": {"type": "Lit", "value": head_label}},
            {"type": "Lit", "value": "_n"},
            {"type": "ToJsonString", "value": {"type": "Lit", "value": int(n_stmts)}},
            {"type": "Lit", "value": "_q"},
            {"type": "ToJsonString", "value": {"type": "Lit", "value": int(idx)}},
        ]}, {})


def mbpp_chunk_entry_name(native, head_label: str, n_stmts: int, idx: int) -> str:
    """Arc 2 Q3: the SAME engine naming law as `chunk_entry_name` (never a
    Python namer), prefixed `mck_` (MBPP-train-mined Chunk) instead of
    `ck_` — a DISTINCT namespace from the arc-1 corpus-mined chunks (`ck_`)
    and the self-taught chunks (`ckt_`), so installing both diets alongside
    each other (the task's additive-install requirement) can never collide
    on name even when head/n_stmts/idx happen to coincide."""
    return native.evaluate({
        "type": "StringConcat", "parts": [
            {"type": "Lit", "value": "mck_"},
            {"type": "SnakeCase", "text": {"type": "Lit", "value": head_label}},
            {"type": "Lit", "value": "_n"},
            {"type": "ToJsonString", "value": {"type": "Lit", "value": int(n_stmts)}},
            {"type": "Lit", "value": "_q"},
            {"type": "ToJsonString", "value": {"type": "Lit", "value": int(idx)}},
        ]}, {})


# --------------------------------------------------------------------------- #
#  Install (mechanical adapter I/O; Seed-marker idempotent; epoch bump —
#  the code_write_growth `write_codebook_epoch` three-line move).
# --------------------------------------------------------------------------- #
def install_mined_chunks(sub, artifact: str = _ARTIFACT) -> int:
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == _CODEBOOK_SEED_ID:
            return 0
    with open(artifact) as f:
        art = json.load(f)
    installed = 0
    for row in art["chunks"]:
        sub.add_node("ShapeSignature", {
            "name": row["name"],
            "kind": "code_write_construction",
            "provenance": "chunk_mined",
            "chunk_key": row["chunk_key"],
            "chunk_rels": row["chunk_rels"],
            "signature": json.dumps([[t] for t in row["trigger_tokens"]]),
            "trigger_tokens": list(row["trigger_tokens"]),
            "ground_template": json.dumps(row["ground_template"]),
            "spine": 1.0,
            "support": int(row["support"]),
            "source": os.path.basename(artifact),
        })
        installed += 1
    sub.add_node("Seed", {"id": _CODEBOOK_SEED_ID,
                          "version": art.get("version", "1.0.0")})
    ag = _agent_node(sub)
    if ag is not None:
        cur = sub.node(ag)["attrs"].get("write_codebook_epoch", 0) or 0
        sub.set_attr(ag, "write_codebook_epoch", cur + 1)
    return installed


_MBPP_DIET_SEED_ID = "mbpp_train_diet"


def ensure_mbpp_train_diet(sub, native, ag_node=None) -> int:
    """Arc 2 Q3: idempotently install the MBPP-train-mined diet (chunks +
    triggers + bigrams + starter-shape affinity rows,
    `seeds/mbpp_train_diet.json` — a plain node-manifest, no rules; built
    by `scripts/mbpp_train_diet.py`) — the `install_mined_chunks` /
    `ensure_chunk_growth` Seed-marker idiom, additive: this seed's
    `ConstructionBigram` rows carry `provenance:'mbpp_train'` /
    `source:'mbpp_train_diet.json'`, distinct from the arc-1 corpus rows
    `ensure_construction_bigrams` boards (`source:'prog_construction_
    scan.json'`) — installing both leaves BOTH populations of
    ConstructionBigram nodes on the graph (never destructive); a consumer
    reading ALL ConstructionBigram nodes by (prev,next) key sees whichever
    seed loaded LAST win on an exact-key collision (a documented residual,
    `PROGRAM_SYNTHESIS_ARC2_Q3_NOTES.md` — `domains/prog_synthesis.py`'s
    `_bigram_tables` is out of this phase's file-ownership scope to change
    into a blend). Returns the number of nodes installed (0 if already
    installed)."""
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == _MBPP_DIET_SEED_ID:
            return 0
    from substrate.seed_loader import manifest_for
    manifest = manifest_for(_MBPP_DIET_SEED_ID)
    summary = native.load_seed_manifest(manifest, ag_node)
    if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
        raise RuntimeError(
            "mbpp_train_diet did not install cleanly: %r" % (summary,))
    sub.add_node("Seed", {"id": _MBPP_DIET_SEED_ID,
                          "version": manifest.get("version", "1.0.0")})
    ag = ag_node if ag_node is not None else _agent_node(sub)
    if ag is not None:
        cur = sub.node(ag)["attrs"].get("write_codebook_epoch", 0) or 0
        sub.set_attr(ag, "write_codebook_epoch", cur + 1)
    return int(summary.get("nodes", 0))


def ensure_chunk_growth(sub, native, ag_node) -> None:
    """Idempotently load the self-teach seed + default the epoch counter
    (a default init, not a decision)."""
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == _SEED_ID:
            break
    else:
        from substrate.seed_loader import manifest_for
        summary = native.load_seed_manifest(manifest_for(_SEED_ID), ag_node)
        if summary.get("rules_skipped") or summary.get("reflexes_skipped"):
            raise RuntimeError(
                "prog_chunk_growth did not install cleanly: %r" % (summary,))
        sub.add_node("Seed", {"id": _SEED_ID, "version": "1.0.0"})
    if ag_node is not None:
        if sub.node(ag_node)["attrs"].get("write_codebook_epoch") is None:
            sub.set_attr(ag_node, "write_codebook_epoch", 0.0)


def _agent_node(sub):
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            return n
    return None


# --------------------------------------------------------------------------- #
#  Self-teach scan (application half of the rule-marked decision).
# --------------------------------------------------------------------------- #
def scan_marked_programs(sub, ag_node) -> int:
    """For every Program the `ckg_mark_scan` RULE marked and this adapter
    has not yet scanned: run the SAME fixed extraction walk over its IR and
    ingest one pending prog_chunk Observation per distinct chunk_key
    (occurrence-tallied — the P3 dedup-at-the-I/O-boundary precedent).
    Mechanical; the recognize/mint decisions are the seed's rules."""
    scanned = 0
    for p in sub.nodes("Program"):
        at = sub.node(p)["attrs"]
        if at.get("ck_scan_marked") != 1.0 or at.get("ck_chunks_scanned"):
            continue
        try:
            ir = json.loads(_text(at.get("program")) or "null")
        except Exception:
            ir = None
        recs: Dict[str, Dict[str, Any]] = {}
        occ: Dict[str, int] = {}
        if isinstance(ir, dict):
            for rec in chunk_candidates(ir):
                k = rec["chunk_key"]
                occ[k] = occ.get(k, 0) + 1
                recs.setdefault(k, rec)
        for k, rec in recs.items():
            tmpl = ground_template_for(rec, rec["lit_values"])
            obs = sub.add_node("Observation", {
                "kind": _KIND,
                "pk_status": "pending",
                "chunk_key": k,
                "chunk_rels": rec["rels"],
                "chunk_head": rec["labels"][0],
                "sig_str": json.dumps([[t] for t in rec["triggers"]]),
                "trigger_tokens": list(rec["triggers"]),
                "ground_template": json.dumps(tmpl),
                "spine": 1.0,
                "occurrences": int(occ[k]),
            })
            sub.add_edge_unchecked(ag_node, "observed", obs)
        sub.set_attr(p, "ck_chunks_scanned", 1.0)
        scanned += 1
    return scanned


def chunk_pump(sub, ag_node, *, max_rounds: int = 8) -> None:
    """run_rules → apply the pending mechanical scan → repeat to quiescence
    (ingest → tick → query, CLAUDE.md's own loop)."""
    for _ in range(max_rounds):
        sub._inner.run_rules(400000)
        if not scan_marked_programs(sub, ag_node):
            break
    sub._inner.run_rules(400000)


# --------------------------------------------------------------------------- #
#  Mechanical readers.
# --------------------------------------------------------------------------- #
def held_chunk_entries(sub) -> List[Dict[str, Any]]:
    out = []
    for q in sub.nodes("ShapeSignature"):
        at = sub.node(q)["attrs"]
        if at.get("kind") != "code_write_construction":
            continue
        if at.get("chunk_key") is None:
            continue
        out.append({
            "name": _text(at.get("name")),
            "provenance": _text(at.get("provenance")),
            "chunk_key": _text(at.get("chunk_key")),
            "trigger_tokens": [_text(t) for t in _plain(at.get("trigger_tokens")) or []],
            "support": at.get("support"),
        })
    out.sort(key=lambda r: r["name"] or "")
    return out


def read_chunk_observations(sub) -> List[Dict[str, Any]]:
    out = []
    for o in sub.nodes("Observation"):
        at = sub.node(o)["attrs"]
        if at.get("kind") != _KIND:
            continue
        minted = None
        for q in sub.neighbours(o, "minted"):
            minted = _text(sub.node(q)["attrs"].get("name"))
        out.append({
            "status": _text(at.get("pk_status")),
            "chunk_key": _text(at.get("chunk_key")),
            "covered_by": _text(at.get("covered_by")),
            "minted": minted,
        })
    out.sort(key=lambda r: (r["chunk_key"] or "", r["status"] or ""))
    return out


def _text(v) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v)


def _plain(v):
    """JSON-safe, deliberately LOSSY flattener for display/re-set_attr use
    (never a round-trip codec — see `prog_synthesis.py::_plain`, the
    reference implementation this mirrors for parity).

    WIRE_BOUNDARY_SYSTEMIC_AUDIT (2026-08): brought to parity with
    `prog_synthesis.py::_plain`'s set/frozenset/Fraction handling — this
    copy was an independently-reinvented, narrower flattener (the same
    "own cache, no cross-import" duplication pattern found across
    `domains/*.py`) missing the exact two type cases three separate
    rungs added to the `prog_synthesis.py` original. This module's own
    call sites (`trigger_tokens`) are string-shaped in practice, so this
    was a latent gap, not a live failure — closed here so it can't
    become one silently if a future caller routes a set/Fraction-valued
    attribute through it."""
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
    "chunk_candidates", "chunk_record", "ground_template_for",
    "derive_triggers", "chunk_entry_name", "install_mined_chunks",
    "ensure_chunk_growth", "scan_marked_programs", "chunk_pump",
    "held_chunk_entries", "read_chunk_observations",
    "abstract_expr", "mbpp_chunk_entry_name", "ensure_mbpp_train_diet",
]
