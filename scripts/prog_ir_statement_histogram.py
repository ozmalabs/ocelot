#!/usr/bin/env python3
"""prog_ir_statement_histogram.py — P0 (part B): the statement-shape histogram
that PICKS the P1 IR variant set (PROGRAM_SYNTHESIS_PLAN.md §4 P0).

Deterministic, stdlib-ast-based MEASUREMENT script. No network, no substrate
boot, no agent logic — pure corpus analysis (the same status as the plan's
"histogram in results/" gate). Over every function (FunctionDef +
AsyncFunctionDef, nested + methods included) in all .py files under
domains/ + substrate/ (the code_curriculum.scan_repo_functions corpus scope,
extended to substrate/ per the P0 task), it measures:

  1. the statement-type multiset + ordered (nested) statement shape;
  2. expression-level blocker features per the CURRENT emitter boundary
     (Call classified builtin/attribute/name, Attribute, Subscript, Lambda,
     comprehensions by kind, f-strings, With/Try/Raise/While, Global/Nonlocal,
     Yield/Await, star-args, kwargs, default args, decorators, methods);
  3. whether the CURRENT emitter takes it — measured by running the REAL
     emitter dispatch imported from domains/code_reading.py +
     domains/ast_to_term.py (never reimplemented/approximated):
     _single_return_value → emit_term, else _multi_stmt_skeleton_and_kind →
     emit_let_chain / emit_accumulation / emit_branching_return — exactly
     `code_reading._read_one`'s emission ladder, on a minimal mechanical
     graph container satisfying the same add_node/add_edge/node/neighbours
     contract `ingest_ast` + `AstTermEmitter` require (the container is
     bookkeeping; every DECISION is the imported real code);
  4. per-function REQUIRED IR variants (candidate set per the plan's P1
     list, extended with the extra variants the corpus forces), the ranked
     blocking-feature histogram by function mass, sole-blocker mass, and a
     greedy cumulative-coverage curve (add the variant unlocking the most
     functions, recompute, repeat).

Output: results/prog_ir_histogram.json — byte-deterministic (sorted keys,
sorted file walk, fixed date field): running the script twice must produce
byte-identical JSON.
"""
from __future__ import annotations

import ast
import builtins
import json
import os
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))

from domains import ast_to_term                      # noqa: E402 — the REAL emitter
from domains import code_reading as cdr              # noqa: E402 — the REAL classifier

DATE = "2026-07-31"
ROOTS = ["domains", "substrate"]
_BUILTINS = frozenset(dir(builtins))

# --------------------------------------------------------------------------- #
#  Minimal mechanical graph container — the same add_node/add_edge/node/
#  neighbours contract ingest_ast + AstTermEmitter use. Pure bookkeeping;
#  every decision below is the imported real emitter/classifier code.
# --------------------------------------------------------------------------- #
class _Shim:
    def __init__(self):
        self._nodes: list[dict] = []
        self._out: dict[tuple, list] = defaultdict(list)

    def add_node(self, ntype, attrs):
        self._nodes.append({"type": ntype, "attrs": dict(attrs)})
        return len(self._nodes) - 1

    def add_edge(self, src, etype, tgt):
        self._out[(src, etype)].append(tgt)

    def node(self, nid):
        return self._nodes[nid]

    def neighbours(self, nid, etype):
        return list(self._out[(nid, etype)])


def current_emitter_takes(func_node: ast.AST) -> tuple[bool, str | None, str | None]:
    """Run the REAL current-emitter dispatch (code_reading._read_one's
    emission ladder, verbatim calls) on one function. Returns
    (emittable, path, error_head)."""
    try:
        src = ast.unparse(func_node)
        shim = _Shim()
        ast_to_term.ingest_ast(shim, src, root_label="p0_histogram")
    except Exception as e:  # noqa: BLE001 — honest non-count, recorded
        return False, None, "ingest_failed: %s" % type(e).__name__
    froot = None
    for nid, n in enumerate(shim._nodes):
        if n["attrs"].get("ast_type") in ("FunctionDef", "AsyncFunctionDef"):
            froot = nid   # preorder ingest: the OUTER def has the smallest nid
            break
    if froot is None:
        return False, None, "no function root after ingest"
    em = ast_to_term.AstTermEmitter(shim, held_leaves={}, range_bind=None)
    try:
        ret_val = cdr._single_return_value(em, froot)
        if ret_val is not None:
            em.emit_term(ret_val)
            return True, "single_return", None
        skeleton, kind = cdr._multi_stmt_skeleton_and_kind(em, froot)
        if kind == "let_chain":
            em.emit_let_chain(froot)
            return True, "let_chain", None
        if kind == "accumulation":
            em.emit_accumulation(froot)
            return True, "accumulation", None
        if kind == "branching_return":
            em.emit_branching_return(froot)
            return True, "branching_return", None
        return False, None, ("out_of_scope" if skeleton is None
                             else "multi_stmt_kind:%s" % kind)
    except ast_to_term.EmitError as e:
        return False, None, "EmitError: %s" % str(e).split("\n")[0][:120]
    except Exception as e:  # noqa: BLE001
        return False, None, "error: %s" % type(e).__name__


# --------------------------------------------------------------------------- #
#  Corpus enumeration — scan_repo_functions' walk (sorted *.py under roots),
#  widened per the P0 task to EVERY FunctionDef/AsyncFunctionDef (nested +
#  methods), with qualnames.
# --------------------------------------------------------------------------- #
def enumerate_functions():
    funcs = []          # (fid, node, meta)
    n_files = 0
    n_syntax_err = 0
    all_paths = []
    for rel in ROOTS:
        base = os.path.join(_ROOT, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            for fn in filenames:
                if fn.endswith(".py"):
                    all_paths.append(os.path.join(dirpath, fn))
    all_paths.sort()
    for path in all_paths:
        try:
            src = open(path).read()
        except OSError:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            n_syntax_err += 1
            continue
        n_files += 1
        rel = os.path.relpath(path, _ROOT)

        def visit(node, qual, in_class, depth):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    q = (qual + "." if qual else "") + child.name
                    meta = {"file": rel, "qualname": q, "lineno": child.lineno,
                            "is_async": isinstance(child, ast.AsyncFunctionDef),
                            "is_method": in_class, "is_nested": depth > 0,
                            "is_toplevel": depth == 0 and not in_class}
                    fid = "%s::%s@%d" % (rel, q, child.lineno)
                    funcs.append((fid, child, meta))
                    visit(child, q, False, depth + 1)
                elif isinstance(child, ast.ClassDef):
                    visit(child, (qual + "." if qual else "") + child.name,
                          True, depth)
                else:
                    visit(child, qual, in_class, depth)

        visit(tree, "", False, 0)
    return funcs, n_files, n_syntax_err


# --------------------------------------------------------------------------- #
#  Statement shape (ordered, nested) + multiset. Docstring peeled (the same
#  peel body_statements does). Nested def/class bodies are atomic tokens in
#  the SHAPE (else shapes explode) but counted in the multiset + features.
# --------------------------------------------------------------------------- #
_BLOCK_FIELDS = ("body", "orelse", "finalbody", "handlers", "cases")


def _peel_docstring(body):
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1:], True
    return body, False


def _stmt_shape(stmt) -> str:
    t = type(stmt).__name__
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return t
    inner = []
    for f in _BLOCK_FIELDS:
        blk = getattr(stmt, f, None)
        if not blk:
            continue
        for s in blk:
            if isinstance(s, ast.excepthandler):
                inner.append("Handler[%s]" % ",".join(_stmt_shape(x) for x in s.body))
            elif isinstance(s, ast.stmt):
                inner.append(_stmt_shape(s))
            elif hasattr(s, "body"):   # match_case
                inner.append("Case[%s]" % ",".join(_stmt_shape(x) for x in s.body))
    if inner:
        return "%s[%s]" % (t, ",".join(inner))
    return t


def statement_shape(func_node):
    body, _ = _peel_docstring(func_node.body)
    return [_stmt_shape(s) for s in body]


def statement_multiset(func_node):
    c: Counter = Counter()
    body, _ = _peel_docstring(func_node.body)
    for s in body:
        for n in ast.walk(s):
            if isinstance(n, ast.stmt):
                c[type(n).__name__] += 1
    return dict(sorted(c.items()))


# --------------------------------------------------------------------------- #
#  Blocker features + required IR variants per function.
# --------------------------------------------------------------------------- #
# ops the current emitter already maps (ast_to_term._BINOP/_UNARYOP/_COMPAREOP)
_OK_BINOPS = {"Add", "Sub", "Mult", "Div", "FloorDiv", "Pow", "Mod"}
_OK_UNARY = {"USub", "Not"}
_OK_CMP = {"Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "In", "NotIn"}

_COMP_KIND = {"ListComp": "ComprehensionList", "SetComp": "ComprehensionSet",
              "DictComp": "ComprehensionDict", "GeneratorExp": "ComprehensionGen"}


def analyse(func_node, meta):
    """One pure-ast pass over the WHOLE function subtree (nested defs/classes
    included — representing the outer honestly requires them): blocker
    features (facts) + required IR variants (candidate-set mapping)."""
    feats: Counter = Counter()
    req: set[str] = set()

    # ---- signature / definition-level ----
    a = func_node.args
    if a.defaults or a.kw_defaults:
        feats["default_args"] += 1
        req.add("DefFnParam")
    if a.vararg or a.kwarg or a.kwonlyargs or getattr(a, "posonlyargs", []):
        feats["star_or_kwonly_params"] += 1
        req.add("DefFnParam")
    if func_node.decorator_list:
        feats["decorators"] += 1
        req.add("Decorator")
    if meta["is_method"]:
        feats["is_method"] += 1
        argnames = [x.arg for x in a.posonlyargs + a.args]
        if argnames and argnames[0] in ("self", "cls"):
            uses = any(isinstance(n, ast.Name) and n.id == argnames[0]
                       for s in func_node.body for n in ast.walk(s))
            if uses:
                feats["uses_self"] += 1
    if meta["is_async"]:
        feats["async_def"] += 1
        req.add("Await")

    body, has_doc = _peel_docstring(func_node.body)
    if has_doc:
        feats["docstring"] += 1
    n_top = len(body)
    feats["n_top_statements"] = n_top
    if n_top != 1:
        feats["multi_statement_body"] += 1
        req.add("Seq")

    has_return = False

    def block_stmts(node):
        out = []
        for f in _BLOCK_FIELDS:
            blk = getattr(node, f, None)
            if blk:
                out.append(blk)
        return out

    def visit_stmt(s):
        nonlocal has_return
        t = type(s).__name__
        if isinstance(s, ast.Return):
            has_return = True
            req.add("Return")
            if s.value is not None:
                visit_expr(s.value)
        elif isinstance(s, ast.Assign):
            feats["assign"] += 1
            for tgt in s.targets:
                visit_target(tgt)
            visit_expr(s.value)
        elif isinstance(s, ast.AnnAssign):
            feats["assign"] += 1
            req.add("AssignVar")
            visit_target(s.target, ann=True)
            if s.value is not None:
                visit_expr(s.value)
        elif isinstance(s, ast.AugAssign):
            feats["augassign"] += 1
            req.add("AugAssign")
            visit_target(s.target, aug=True)
            visit_expr(s.value)
        elif isinstance(s, ast.If):
            feats["if_stmt"] += 1
            req.add("IfStmt")
            visit_expr(s.test)
            walk_blocks(s)
        elif isinstance(s, (ast.For, ast.AsyncFor)):
            feats["for_loop"] += 1
            req.add("ForEach")
            if isinstance(s, ast.AsyncFor):
                req.add("Await")
            visit_target(s.target)
            visit_expr(s.iter)
            walk_blocks(s)
        elif isinstance(s, ast.While):
            feats["while_loop"] += 1
            req.add("While")
            visit_expr(s.test)
            walk_blocks(s)
        elif isinstance(s, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            feats["try_stmt"] += 1
            req.add("TryOr")
            for h in s.handlers:
                if h.type is not None:
                    visit_expr(h.type)
                for hs in h.body:
                    visit_stmt(hs)
            for blk in (s.body, s.orelse, s.finalbody):
                for x in blk:
                    visit_stmt(x)
        elif isinstance(s, ast.Raise):
            feats["raise_stmt"] += 1
            req.add("Raise")
            if s.exc is not None:
                visit_expr(s.exc)
            if s.cause is not None:
                visit_expr(s.cause)
        elif isinstance(s, (ast.With, ast.AsyncWith)):
            feats["with_stmt"] += 1
            req.add("With")
            if isinstance(s, ast.AsyncWith):
                req.add("Await")
            for item in s.items:
                visit_expr(item.context_expr)
                if item.optional_vars is not None:
                    visit_target(item.optional_vars)
            walk_blocks(s)
        elif isinstance(s, ast.Assert):
            feats["assert_stmt"] += 1
            req.add("Assert")
            visit_expr(s.test)
            if s.msg is not None:
                visit_expr(s.msg)
        elif isinstance(s, ast.Delete):
            feats["delete_stmt"] += 1
            req.add("Delete")
            for tgt in s.targets:
                visit_target(tgt, delete=True)
        elif isinstance(s, (ast.Import, ast.ImportFrom)):
            feats["import_in_body"] += 1
            req.add("ImportStmt")
        elif isinstance(s, (ast.Global, ast.Nonlocal)):
            feats["global_nonlocal"] += 1
            req.add("GlobalNonlocal")
        elif isinstance(s, ast.Expr):
            feats["expr_stmt"] += 1
            req.add("Seq")
            visit_expr(s.value)
        elif isinstance(s, ast.Pass):
            feats["pass_stmt"] += 1
            req.add("Seq")
        elif isinstance(s, (ast.Break, ast.Continue)):
            feats["break_continue"] += 1
            req.add("LoopCtl")
        elif isinstance(s, ast.Match):
            feats["match_stmt"] += 1
            req.add("Match")
            visit_expr(s.subject)
            for case in s.cases:
                for cs in case.body:
                    visit_stmt(cs)
        elif isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
            feats["nested_def"] += 1
            req.add("DefFn")
            sub_meta = {"is_method": False,
                        "is_async": isinstance(s, ast.AsyncFunctionDef)}
            sub_feats, sub_req = analyse(s, {**sub_meta, "is_nested": True,
                                             "is_toplevel": False})
            req.update(sub_req)
        elif isinstance(s, ast.ClassDef):
            feats["class_in_body"] += 1
            req.add("ClassDef")
            for cs in s.body:
                visit_stmt(cs)
        else:
            feats["other_stmt_%s" % t] += 1
            req.add("Other:%s" % t)

    def walk_blocks(s):
        for blk in block_stmts(s):
            if len(blk) > 1:
                req.add("Seq")
            for x in blk:
                if isinstance(x, ast.stmt):
                    visit_stmt(x)

    def visit_target(tgt, ann=False, aug=False, delete=False):
        if isinstance(tgt, ast.Name):
            if not delete:
                req.add("AssignVar")
        elif isinstance(tgt, (ast.Tuple, ast.List, ast.Starred)):
            feats["tuple_unpack_target"] += 1
            req.add("TupleUnpack")
            for e in getattr(tgt, "elts", [getattr(tgt, "value", None)]):
                if e is not None:
                    visit_target(e, delete=delete)
        elif isinstance(tgt, ast.Attribute):
            feats["attribute_store"] += 1
            req.add("AttrSet")
            visit_expr(tgt.value)
        elif isinstance(tgt, ast.Subscript):
            feats["subscript_store"] += 1
            req.add("SubscriptSet")
            visit_expr(tgt.value)
            visit_expr(tgt.slice)

    def visit_expr(e):
        for n in ast.walk(e):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    if f.id in _BUILTINS:
                        feats["call_builtin"] += 1
                    else:
                        feats["call_name"] += 1
                elif isinstance(f, ast.Attribute):
                    feats["call_attribute"] += 1
                else:
                    feats["call_other"] += 1
                req.add("CallExtern")
                if any(isinstance(x, ast.Starred) for x in n.args):
                    feats["star_args_call"] += 1
                if n.keywords:
                    feats["kwargs_call"] += 1
            elif isinstance(n, ast.Attribute):
                if not isinstance(getattr(n, "ctx", None), (ast.Store, ast.Del)):
                    feats["attribute_load"] += 1
                    req.add("AttrGet")
            elif isinstance(n, ast.Subscript):
                if isinstance(getattr(n, "ctx", None), ast.Store):
                    feats["subscript_store"] += 1
                    req.add("SubscriptSet")
                elif isinstance(getattr(n, "ctx", None), ast.Del):
                    pass  # counted at the Delete statement
                else:
                    feats["subscript_load"] += 1
                    req.add("Subscript")
            elif isinstance(n, ast.Lambda):
                feats["lambda"] += 1
                req.add("Lambda")
            elif type(n).__name__ in _COMP_KIND:
                feats["comp_%s" % type(n).__name__.lower()] += 1
                req.add(_COMP_KIND[type(n).__name__])
            elif isinstance(n, ast.JoinedStr):
                feats["fstring"] += 1
                req.add("FString")
            elif isinstance(n, (ast.Yield, ast.YieldFrom)):
                feats["yield_expr"] += 1
                req.add("Yield")
            elif isinstance(n, ast.Await):
                feats["await_expr"] += 1
                req.add("Await")
            elif isinstance(n, ast.NamedExpr):
                feats["named_expr"] += 1
                req.add("AssignVar")
            elif isinstance(n, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
                if not isinstance(getattr(n, "ctx", None), (ast.Store, ast.Del)):
                    feats["container_literal"] += 1
                    req.add("ContainerLit")
            elif isinstance(n, ast.BinOp):
                op = type(n.op).__name__
                if op not in _OK_BINOPS:
                    feats["binop_ext_%s" % op.lower()] += 1
                    req.add("OpExt")
            elif isinstance(n, ast.UnaryOp):
                op = type(n.op).__name__
                if op not in _OK_UNARY:
                    feats["unaryop_ext_%s" % op.lower()] += 1
                    req.add("OpExt")
            elif isinstance(n, ast.Compare):
                for op in n.ops:
                    opn = type(op).__name__
                    if opn in ("Is", "IsNot"):
                        feats["is_comparison"] += 1
                        req.add("IsOp")
                    elif opn not in _OK_CMP:
                        feats["cmp_ext_%s" % opn.lower()] += 1
                        req.add("OpExt")

    for s in body:
        visit_stmt(s)
    if not has_return:
        feats["no_return"] += 1
        req.add("Seq")   # a procedure: implicit None return needs sequencing
    return dict(feats), req


# --------------------------------------------------------------------------- #
#  Aggregation: ranked masses, sole blockers, greedy coverage curve.
# --------------------------------------------------------------------------- #
# Variants whose IR representation is structural-only for now: ProgEval cannot
# PREDICT through them (extern semantics / effects gapped) even once the IR
# holds them. Kept separate so the two claims never blur.
PREDICTION_GAPPED = frozenset({
    "CallExtern", "Yield", "Await", "With", "ImportStmt", "ClassDef",
    "Decorator", "GlobalNonlocal", "IsOp", "Match", "Delete",
})


def greedy_curve(functions, total):
    """functions: list of (fid, emittable_now, req_set). Start from current
    coverage; repeatedly add the candidate variant unlocking the most
    additional functions (primary key: immediate unlocks; when no single
    variant completes any function alone — coverage needs SETS — fall back
    to missing-set mass; ties alphabetical). Functions whose requirements
    include an un-candidated construct (Other:*) are never unlockable and
    are reported as such."""
    baseline = sum(1 for _, e, _ in functions if e)
    locked = [(fid, req) for fid, e, req in functions if not e]
    never = [(fid, req) for fid, req in locked
             if any(v.startswith("Other:") for v in req)]
    remaining = [(fid, req) for fid, req in locked
                 if not any(v.startswith("Other:") for v in req)]
    chosen: list[str] = []
    covered = baseline
    curve = []
    while remaining:
        chosen_set = set(chosen)
        unlock: Counter = Counter()
        mass: Counter = Counter()
        for fid, req in remaining:
            missing = req - chosen_set
            for v in missing:
                mass[v] += 1
            if len(missing) == 1:
                unlock[next(iter(missing))] += 1
        if not mass:
            break
        best = sorted(mass, key=lambda v: (-unlock.get(v, 0), -mass[v], v))[0]
        chosen.append(best)
        chosen_set.add(best)
        newly = sum(1 for fid, req in remaining if req <= chosen_set)
        remaining = [(fid, req) for fid, req in remaining
                     if not req <= chosen_set]
        covered += newly
        curve.append({"variant_added": best, "newly_unlocked": newly,
                      "cumulative_unlocked": covered,
                      "cumulative_pct": round(100.0 * covered / total, 2),
                      "prediction_gapped_variant": best in PREDICTION_GAPPED})
    return baseline, curve, chosen, never


def main():
    funcs, n_files, n_syntax_err = enumerate_functions()
    total = len(funcs)

    rows = []
    shape_hist: Counter = Counter()
    stmt_type_mass: Counter = Counter()     # functions using each stmt type
    feat_mass: Counter = Counter()          # functions using each feature
    feat_ids: dict[str, list] = defaultdict(list)
    variant_mass: Counter = Counter()       # non-emittable functions needing v
    variant_ids: dict[str, list] = defaultdict(list)
    sole_blocker: Counter = Counter()
    sole_ids: dict[str, list] = defaultdict(list)
    emit_paths: Counter = Counter()
    n_emittable = 0
    n_emittable_toplevel_domains = 0

    for fid, node, meta in funcs:
        emit_ok, path, err = current_emitter_takes(node)
        feats, req = analyse(node, meta)
        if not emit_ok and not req:
            # the real emitter is STRICTER than the candidate-variant map
            # for this function (a shape inside the mapped constructs it
            # still refuses) — honest never-unlock bucket, not a free pass.
            req = {"Other:emitter_stricter_than_variant_map"}
        shape = statement_shape(node)
        shape_hist["|".join(shape) if shape else "<empty>"] += 1
        for st in statement_multiset(node):
            stmt_type_mass[st] += 1
        for f in feats:
            if f == "n_top_statements":
                continue
            feat_mass[f] += 1
            feat_ids[f].append(fid)
        if emit_ok:
            n_emittable += 1
            emit_paths[path] += 1
            if meta["is_toplevel"] and meta["file"].startswith("domains/"):
                n_emittable_toplevel_domains += 1
        else:
            named = sorted(v for v in req if not v.startswith("Other:"))
            for v in named:
                variant_mass[v] += 1
                variant_ids[v].append(fid)
            if len(req) == 1 and named:
                sole_blocker[named[0]] += 1
                sole_ids[named[0]].append(fid)
        rows.append((fid, emit_ok, req))

    baseline, curve, chosen, never_unlocked = greedy_curve(rows, total)

    def recommend(threshold):
        cum = round(100.0 * baseline / total, 2)
        picked = []
        for step in curve:
            picked.append(step["variant_added"])
            cum = step["cumulative_pct"]
            if cum >= threshold:
                return {"threshold_pct": threshold, "reached_pct": cum,
                        "variants": picked, "n_variants": len(picked)}
        return {"threshold_pct": threshold, "reached_pct": cum,
                "variants": picked, "n_variants": len(picked),
                "note": "threshold not reachable with the candidate set"}

    top_feats = [f for f, _ in feat_mass.most_common(15)]
    top_variants = [v for v, _ in variant_mass.most_common(15)]

    out = {
        "date": DATE,
        "corpus": {
            "roots": ROOTS,
            "n_files_parsed": n_files,
            "n_files_syntax_error": n_syntax_err,
            "n_functions_total": total,
            "n_functions_toplevel": sum(1 for _, _, m in funcs if m["is_toplevel"]),
            "n_functions_toplevel_domains_only":
                sum(1 for _, _, m in funcs
                    if m["is_toplevel"] and m["file"].startswith("domains/")),
            "n_methods": sum(1 for _, _, m in funcs if m["is_method"]),
            "n_nested": sum(1 for _, _, m in funcs if m["is_nested"]),
            "n_async": sum(1 for _, _, m in funcs if m["is_async"]),
            "note": ("code_curriculum.scan_repo_functions scope was domains/ "
                     "toplevel FunctionDef only (6252 at the curriculum run); "
                     "this histogram adds substrate/ + nested + methods + "
                     "async per the P0 task."),
        },
        "current_emitter": {
            "measured_by": ("REAL dispatch imported from domains/code_reading"
                            ".py + domains/ast_to_term.py (_single_return_value"
                            " -> emit_term; _multi_stmt_skeleton_and_kind -> "
                            "emit_let_chain/emit_accumulation/"
                            "emit_branching_return); held_leaves={}, "
                            "range_bind=None — scan_repo_functions' exact "
                            "configuration"),
            "n_emittable": n_emittable,
            "pct": round(100.0 * n_emittable / total, 2),
            "by_path": dict(sorted(emit_paths.items())),
            "n_emittable_toplevel_domains_only": n_emittable_toplevel_domains,
            "emittable_ids": sorted(fid for fid, ok, _ in rows if ok),
        },
        "statement_type_mass": [
            {"stmt_type": k, "mass": v} for k, v in
            sorted(stmt_type_mass.items(), key=lambda kv: (-kv[1], kv[0]))],
        "ordered_shape_top50": [
            {"shape": s, "count": c} for s, c in
            sorted(shape_hist.items(), key=lambda kv: (-kv[1], kv[0]))[:50]],
        "n_distinct_ordered_shapes": len(shape_hist),
        "blocker_features": {
            "note": ("mass = number of functions using the feature (a "
                     "function counts toward every feature it uses); ids "
                     "listed for the top 15 features"),
            "ranked": [{"feature": k, "mass": v} for k, v in
                       sorted(feat_mass.items(), key=lambda kv: (-kv[1], kv[0]))],
            "ids_top15": {f: sorted(feat_ids[f]) for f in top_feats},
        },
        "required_variants": {
            "note": ("mass = number of NON-emittable functions whose full "
                     "representation requires the variant; sole_blocker = "
                     "functions where that single variant is the only "
                     "missing one; ids listed for the top 15 variants"),
            "ranked": [{"variant": k, "mass": v} for k, v in
                       sorted(variant_mass.items(), key=lambda kv: (-kv[1], kv[0]))],
            "sole_blocker": [{"variant": k, "mass": v} for k, v in
                             sorted(sole_blocker.items(),
                                    key=lambda kv: (-kv[1], kv[0]))],
            "sole_blocker_ids": {v: sorted(ids) for v, ids in
                                 sorted(sole_ids.items())},
            "ids_top15": {v: sorted(variant_ids[v]) for v in top_variants},
            "prediction_gapped_variants": sorted(PREDICTION_GAPPED),
        },
        "greedy_curve": {
            "note": ("start = current emitter coverage; each step adds the "
                     "candidate IR variant unlocking the most additional "
                     "functions (function unlocked when its ENTIRE required "
                     "set is chosen); prediction_gapped_variant marks "
                     "variants that are IR-representable but NOT ProgEval-"
                     "predictable (extern/effect semantics gapped)"),
            "baseline_unlocked": baseline,
            "baseline_pct": round(100.0 * baseline / total, 2),
            "steps": curve,
            "final_pct": (curve[-1]["cumulative_pct"] if curve
                          else round(100.0 * baseline / total, 2)),
            "never_unlocked": len(never_unlocked),
            "never_unlocked_reason_sample": sorted(
                {v for _, req in never_unlocked for v in req
                 if v.startswith("Other:")})[:20],
        },
        "recommended": {
            "at_60": recommend(60.0),
            "at_70": recommend(70.0),
            "at_80": recommend(80.0),
        },
    }

    out_path = os.path.join(_ROOT, "results", "prog_ir_histogram.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s" % out_path)
    print("corpus: %d functions over %d files (%d toplevel; curriculum "
          "cross-check domains-toplevel=%d)"
          % (total, n_files, out["corpus"]["n_functions_toplevel"],
             out["corpus"]["n_functions_toplevel_domains_only"]))
    print("current emitter: %d emittable (%.2f%%) by_path=%s"
          % (n_emittable, out["current_emitter"]["pct"], dict(emit_paths)))
    print("greedy: baseline %.2f%% -> final %.2f%% over %d steps"
          % (out["greedy_curve"]["baseline_pct"],
             out["greedy_curve"]["final_pct"], len(curve)))
    for step in curve[:12]:
        print("  +%-18s +%5d -> %6.2f%%" % (step["variant_added"],
                                            step["newly_unlocked"],
                                            step["cumulative_pct"]))


if __name__ == "__main__":
    main()
