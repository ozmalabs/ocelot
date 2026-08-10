"""prog_ir_emit — P2 (python frame): the MECHANICAL AST -> hub Program-IR emitter.

PROGRAM_SYNTHESIS_PLAN.md §4-P2 / PROGRAM_SYNTHESIS_PREREG.md §4. A NEW,
ADDITIVE emission path beside the frozen CODE-arc emitter (`ast_to_term.
AstTermEmitter` + `code_reading`'s dispatch — byte-untouched; the P0 baseline
gate pins it). This module emits the P1 hub Program IR (the `Prog*` TermNode
variants landed in prog_eval.rs / reflect.rs, mirrored in substrate/dsl.py)
as Term-JSON, from either a Python `ast` function node (or source) or an
`ingest_ast`-shaped AstNode subgraph.

CLAUDE.md admissibility: this is a FIXED CORRESPONDENCE WALK — a mechanical
translation of an opaque external form (Python source) into graph data
(hub-IR Term-JSON the substrate reflects via `add_term_subgraph`), the
`ast_to_term.ingest_ast` precedent at IR grain. There are no decisions over
graph state and no agent logic: every branch below dispatches on the AST
node type by a fixed table, the same for every function. The rule-based
bottom-up fold (extending `ast_term_rules.CORRESPONDENCE` to statement
grain so the ENGINE does this walk) is the recorded future migration — see
PROGRAM_SYNTHESIS_P2_PYTHON.md.

HONESTY CONTRACT (the task's "enumerable, never a partial silent emit"):
`emit_prog_ir` returns either

    {"ok": True, "ir": <Term-JSON>, "externs": [...], "predictable": bool,
     "variants": [...], "params": [...], "has_recv_call": bool}

with the WHOLE function represented, or

    {"ok": False, "blockers": [<feature name>, ...]}

with EVERY out-of-scope feature named (the walk continues past a blocked
construct precisely so the blocker list is complete). It never returns a
partial IR.

THE P1 VARIANT SET (P0 histogram at_80 + the registered While/Raise
deviation — PROGRAM_SYNTHESIS_P1_NOTES.md §1): ProgSeq ProgAssignVar
ProgAugAssign ProgTupleUnpack ProgIfStmt ProgForEach ProgWhile ProgLoopCtl
ProgReturn ProgTryOr ProgRaise ProgImportStmt ProgSubscript(+Set)
ProgAttrGet(+Set) ProgContainerLit ProgComprehensionList ProgComprehensionGen
ProgFString ProgIsOp ProgCallExtern ProgDefFnParam. Pure expressions emit as
ordinary DSL Terms (Plus/Minus/Times/Div/Mod/Pow/Neg/Not/Eq/Lt/Lte/Gt/Gte/
In/IfThenElse — the `ast_to_term`/`ast_term_rules` CORRESPONDENCE, reused).

SEMANTICS-PINNED MAPPING CHOICES (probed against the installed P1 engine,
recorded in PROGRAM_SYNTHESIS_P2_PYTHON.md; each avoids a silent-wrong emit):

  * `and`/`or` desugar to right-nested IfThenElse with OPERAND semantics
    (`a or b` == `a if a else b`) — the ast_term_rules `boolop_rules`
    precedent. DSL And/Or return BOOLS (measured), which is unfaithful in
    value position; IfThenElse truthiness is Python-like (measured: 0/""/
    None/[] falsy).
  * `//` — DSL `Div` is TRUE division (measured 17/2 -> 8.5) and there is
    no floordiv expression Term; the frozen CODE-arc emitter's FloorDiv->Div
    fold is a documented approximation this path refuses to repeat.
    Instead, a floordiv with a statically-POSITIVE literal divisor and
    Prog-free (pure-arithmetic) operands LIFTS to the CPython-exact
    composite prelude `__uN = a - (a % b); __uN //= b` read back as
    `Var __uN` — see `_emit_floordiv` for the measured semantics chain and
    the exact soundness conditions (armed in statement values + If tests;
    disarmed in While tests and comprehensions). Everything else blocks
    `OpExt:FloorDiv`.
  * `+`/`*` with a STATICALLY-string operand (str literal / f-string) is a
    blocker (`StrArithStatic`): DSL Plus/Times are numeric (measured:
    'a'+'b' -> 0). Unknown-typed operands emit Plus/Times under the
    registered P1 convention (DSL arithmetic governs expressions).
  * `x in <str literal>` is a blocker (`InStrStatic`): DSL In is collection
    membership, not substring (measured).
  * `except <NarrowType>` is a blocker (`TypedExcept`): ProgTryOr catches
    ANY trap; only bare/`Exception`/`BaseException` handlers mean the same
    thing. Multiple handlers / else / finally block likewise.
  * `raise X(...)` emits mechanically (`ProgRaise{exc: ProgCallExtern...}`);
    at ProgEval time the constructor is an undeclared extern, so the raise
    surfaces as an `extern:` trap rather than `raise:` — still a trap, still
    catchable, never a value (documented divergence).
  * multi-target `a = b = expr` desugars to `a = expr; b = a` (observably
    identical for plain Names under ProgEval's no-aliasing value semantics);
    tuple loop targets desugar via a synthetic `__u<N>` unpack variable
    (deterministic; the extra env key is documented).
  * `obj.attr op= v` / `obj[i] op= v` desugar to read-modify-write ONLY when
    the target subexpressions contain no extern call (double evaluation of a
    pure subtree is observationally safe; an extern-bearing one is not).

ProgCallExtern: the extern name is captured VERBATIM — dotted for
attribute-chain calls rooted at a Name (`math.sqrt`), `recv`-form for
computed receivers (`(a+b).bit_length()` -> name "bit_length", recv the
receiver's IR). The P1 native-oracle set (len/abs/min/max/range/sum/str/
int/float/bool/sorted) is exported as NATIVE_ORACLES so coverage can compute
the ProgEval-predictable subset ("no undeclared externs": every extern name
in the native set and no recv-form call).

GRAPH-MODE ENTRY (`emit_prog_ir_from_graph`): walks an `ingest_ast` AstNode
subgraph (the `child` edges + `child_field`/`child_index` attrs). The graph
representation does not carry every AST scalar (`_SCALAR_FIELDS` is value/
id/arg/name/n/s/attr), so facts the graph cannot see block honestly with a
`GraphRepr:` prefix (f-string conversion flags, `from X import` module
names) rather than being guessed; `import x as y` aliasing (asname) is
carried as absent — ProgImportStmt is a ProgEval no-op, recorded caveat.

ARC 2 Q1.5 WIDENING (PROGRAM_SYNTHESIS_ARC2_Q15_NOTES.md): this emitter now
targets the Q1-widened engine (PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md) —
additively, over the SAME fixed-table-walk discipline, never touching a
previously-ok function's emitted `ir` shape (only the `predictable`
classification widens, by construction, since it is derived from the
NATIVE_ORACLES/NATIVE_RECV_ORACLES tables below):

  * `x[a:b:c]` (read position) -> `ProgSlice{obj, start, stop, step}`
    (each of start/stop/step is `None` when the AST slot is absent — the
    engine clamps OOB bounds and traps `slice:zero_step`/`slice:type:<kind>`
    honestly). A slice WRITE target (`x[a:b] = v`) has no engine write-back
    path (§3 of the Q1 notes) — still `SliceSubscript`, unchanged.
  * `&`/`|`/`^` -> the plain DSL `BitAnd`/`BitOr`/`BitXor` Terms (added to
    `_BINOP_AB`, the SAME {a,b} shape Sub/Div/Mod/Pow already use).
    Emission is TYPE-BLIND (int vs Set dispatch is the engine's runtime
    concern, per the Q1 notes' task-2 finding) — no static check here, by
    design, the same discipline as the pre-existing unknown-typed Plus/Times
    convention. `<<`/`>>` are NOT part of this widening (the Q1 notes only
    landed set-algebra reach for `&`/`|`/`^`; `OpExt:LShift`/`OpExt:RShift`
    stay honest blockers).
  * Recv-form method calls now split into two classes by NAME (still
    type-blind on the RECEIVER — dispatch is the engine's job):
    `NATIVE_RECV_ORACLES` (the Q1 string_methods + read-only dict_methods
    set) emit exactly as before (`ProgCallExtern` with `recv` set); any
    OTHER method name — most importantly every mutating collection/dict
    method (`append`/`sort`/`add`/`setdefault`/...), which the engine
    structurally refuses (no lvalue write-back path for a recv-form call,
    Q1 notes §3) — is now an honest, NAMED blocker (`RecvMethod:<name>`)
    at EMISSION time rather than a runtime `extern:unimplemented:<name>`
    trap. This is a genuine behaviour change from the pre-Q1.5 emitter
    (which emitted every recv-form call unconditionally); it does not
    touch any function in the frozen P2 fixture corpus (none of those 13
    fixtures use a recv-form call at all — verified), so the arc-1
    byte-identity invariant holds for that corpus, but it DOES lower the
    repo-corpus "ok" count for functions that call an un-landed method —
    named and measured, not silently absorbed (see the Q1.5 notes).
  * `isinstance(x, T)` — the engine's type argument is a TYPE-NAME STRING
    (Q1 notes §2 item 3), never a real type object. A bare `Name` second
    argument (`isinstance(x, int)`) is now translated to `Lit("int")`
    (previously this would have emitted a nonsensical `Var("int")`, never
    exercised because the whole recv/native-call widening didn't exist
    pre-Q1.5). A tuple-of-types second argument (`isinstance(x, (int,
    float))`) has no OR-of-type-names convention in the engine — honest
    `IsinstanceMultiType` blocker. Any other second-argument shape
    (a dotted `module.Class`, a variable, ...) — `IsinstanceComplexType`.
  * `list`/`tuple`/`set`/`frozenset`/`dict`/`all`/`any`/`enumerate`/`zip`/
    `reversed`/`round`/`pow`/`divmod`/`ord`/`chr`/`math.sqrt`/`math.floor`/
    `math.ceil`/`math.pow`/`math.trunc` need NO emission-shape change (a
    Name-form or dotted-Name-form call already emits generically) — they
    are added to `NATIVE_ORACLES` so the `predictable` classification
    reflects that the engine now has a real oracle for them.
  * Still honest blockers, unchanged by this phase: `kwargs`/star-args
    (`KwargsCall`/`StarArgsCall`/`StarArgsParam`), `Lambda`,
    `OpExt:FloorDiv` outside the exact-lift guard, `TypedExcept`, and every
    other P2-documented residual — none of this widening touches them.
"""
from __future__ import annotations

import ast
import textwrap
from typing import Any, Dict, List, Optional, Tuple

from domains.ast_to_term import _ast_node_type

# --------------------------------------------------------------------------- #
#  Fixed tables (the correspondence — the only knowledge in this module).
# --------------------------------------------------------------------------- #
# The P1 native-oracle set (PROGRAM_SYNTHESIS_P1_NOTES.md §3, CallExtern),
# widened by Q1.5 with every Name-form / dotted-Name-form call the Q1
# engine (PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md) landed a real native oracle
# for: math_native, container_ctor, general_builtins (module docstring
# "ARC 2 Q1.5 WIDENING"). No emission-shape change accompanies this widening
# — these names already emitted as ordinary Name-form ProgCallExtern calls;
# only the `predictable` classification moves.
NATIVE_ORACLES = frozenset({
    "len", "abs", "min", "max", "range", "sum", "str", "int", "float",
    "bool", "sorted",
    # Q1 math_native
    "round", "pow", "divmod", "ord", "chr",
    "math.sqrt", "math.floor", "math.ceil", "math.pow", "math.trunc",
    # Q1 container_ctor
    "list", "tuple", "set", "frozenset", "dict",
    # Q1 general_builtins (map/next/iter are REFUSED by the engine itself —
    # never added here, per the Q1 notes' honest-refusal list)
    "all", "any", "isinstance", "enumerate", "zip", "reversed"})

# The Q1 recv-form (method-call) native-oracle set: string_methods + the
# READ-ONLY half of dict_methods (`prog_eval.rs::call_recv_oracle`). A
# recv-form call whose method name is NOT in this set is now an honest,
# NAMED emission-time blocker (`RecvMethod:<name>`, see `_emit_call`) —
# most importantly every MUTATING collection/dict method, which the engine
# structurally refuses (no lvalue write-back path for a pure expression
# call, Q1 notes §3).
NATIVE_RECV_ORACLES = frozenset({
    # string_methods
    "upper", "lower", "capitalize", "strip", "lstrip", "rstrip", "split",
    "join", "replace", "startswith", "endswith", "find", "count",
    "isdigit", "isalpha", "isupper", "islower",
    # dict_methods (read-only)
    "items", "keys", "values", "get"})

# Method names the Q1 engine structurally REFUSES (no lvalue write-back
# path for a pure `ProgCallExtern` — Q1 notes §3 "the mutating-recv-call
# gap"): `collection_methods`'s mutating half + `dict_methods`'s mutating
# half. Recognised by NAME (see `_emit_call`) so `xs.append(v)`/`d.
# setdefault(k, v)` become a named, honest `RecvMethod:<name>` blocker at
# emission time — not an emit-and-let-it-trap. `copy`/`index`/`count`
# (list) are deliberately NOT here: they are non-mutating but simply not
# landed, so they keep falling through to the pre-Q1.5 dotted-name
# fallback UNCHANGED (a bare-Name receiver still resolves as a dotted
# extern, same as any other not-yet-native method — no new blocker, no
# regression either way).
_RECV_BLOCKED_METHODS = frozenset({
    # collection_methods (mutating)
    "append", "extend", "insert", "remove", "pop", "clear", "sort",
    "reverse", "add", "discard", "popitem",
    # dict_methods (mutating half)
    "setdefault", "update"})

# The P1 IR variant set this emitter targets (P0 at_80 + While + Raise).
P1_VARIANT_SET = frozenset({
    "Seq", "AssignVar", "AugAssign", "TupleUnpack", "IfStmt", "ForEach",
    "While", "LoopCtl", "Return", "TryOr", "Raise", "ImportStmt",
    "Subscript", "SubscriptSet", "AttrGet", "AttrSet", "ContainerLit",
    "ComprehensionList", "ComprehensionGen", "FString", "IsOp",
    "CallExtern", "DefFnParam"})

# BinOp -> DSL Term (expression grain; DSL semantics govern — P1 §3).
_BINOP_ITEMS = {"Add": "Plus", "Mult": "Times"}          # variadic {items}
# Q1.5: BitAnd/BitOr/BitXor join the {a,b}-shaped table — the SAME plain
# DSL Terms Sub/Div/Mod/Pow already use. Emission is type-blind (int vs
# Set dispatch is the engine's runtime concern, module docstring). `<<`/`>>`
# are deliberately NOT here — the Q1 notes only landed set-algebra reach
# for `&`/`|`/`^`; OpExt:LShift/OpExt:RShift stay honest blockers.
_BINOP_AB = {"Sub": "Minus", "Div": "Div", "Mod": "Mod", "Pow": "Pow",
             "BitAnd": "BitAnd", "BitOr": "BitOr", "BitXor": "BitXor"}
# AugAssign op name (ast) -> ProgAugAssign op string (prog_eval native set).
_AUGOP = {"Add": "add", "Sub": "sub", "Mult": "mult", "Div": "div",
          "FloorDiv": "floordiv", "Mod": "mod", "Pow": "pow",
          "LShift": "lshift", "RShift": "rshift", "BitAnd": "bitand",
          "BitOr": "bitor", "BitXor": "bitxor"}
# AugAssign ops that ALSO exist at expression grain (needed for the
# read-modify-write desugar of attribute/subscript aug-targets).
_AUGOP_EXPR = {"Add", "Sub", "Mult", "Div", "Mod", "Pow"}
# Compare op -> comparator Term (chained -> And of pairs, the CODE-2 precedent).
_CMPOP = {"Eq": "Eq", "Lt": "Lt", "LtE": "Lte", "Gt": "Gt", "GtE": "Gte"}
# Exception names ProgTryOr faithfully means (it catches ANY trap).
_CATCH_ALL_EXC = frozenset({"Exception", "BaseException"})

_MISSING = object()   # a scalar the view cannot see (graph representation gap)
_SKIP = object()      # a legitimately-empty statement (Pass / bare AnnAssign)


# --------------------------------------------------------------------------- #
#  Views — ONE walker, two mechanical backends (ast objects / AstNode graph).
# --------------------------------------------------------------------------- #
class _AstView:
    """Accessor over stdlib ast objects (full fidelity)."""

    graph_mode = False

    def kind(self, n) -> str:
        return _ast_node_type(n)

    def child(self, n, field):
        v = getattr(n, field, None)
        return v if isinstance(v, ast.AST) else None

    def indexed_children(self, n, field) -> List[Tuple[int, Any]]:
        v = getattr(n, field, None) or []
        return [(i, x) for i, x in enumerate(v) if isinstance(x, ast.AST)]

    def children(self, n, field) -> List[Any]:
        return [x for _, x in self.indexed_children(n, field)]

    def list_len(self, n, field) -> int:
        v = getattr(n, field, None) or []
        return len(v)

    def scalar(self, n, key):
        if not hasattr(n, key):
            return _MISSING
        v = getattr(n, key)
        if v is None or isinstance(v, (int, float, str, bool)):
            return v
        return _MISSING


class _GraphView:
    """Accessor over an `ingest_ast` AstNode subgraph. Needs only the
    node/neighbours contract (a Substrate or any mechanical shim)."""

    graph_mode = True

    def __init__(self, container):
        self.s = container

    def _attrs(self, nid) -> Dict[str, Any]:
        return self.s.node(nid)["attrs"]

    def kind(self, nid) -> str:
        return self._attrs(nid).get("ast_type", "")

    def child(self, nid, field):
        for c in self.s.neighbours(nid, "child"):
            a = self._attrs(c)
            if a.get("child_field") == field and a.get("child_index") == -1:
                return c
        return None

    def indexed_children(self, nid, field) -> List[Tuple[int, Any]]:
        out = []
        for c in self.s.neighbours(nid, "child"):
            a = self._attrs(c)
            if a.get("child_field") == field and a.get("child_index", -1) >= 0:
                out.append((a["child_index"], c))
        out.sort(key=lambda p: p[0])
        return out

    def children(self, nid, field) -> List[Any]:
        return [c for _, c in self.indexed_children(nid, field)]

    def list_len(self, nid, field) -> int:
        # the graph only holds AST items (ingest skips None slots), so a
        # None-bearing list (dict ** keys) shows as a LENGTH MISMATCH the
        # walker checks pairwise instead.
        return len(self.indexed_children(nid, field))

    def scalar(self, nid, key):
        a = self._attrs(nid)
        if key in a:
            return a[key]
        return _MISSING


# --------------------------------------------------------------------------- #
#  Term-JSON constructors (the emission dialect: optional children explicit
#  None, optional identifier sentinels explicit "" — the P1 reflect dialect).
# --------------------------------------------------------------------------- #
def _lit(v):
    return {"type": "Lit", "value": v}


def _var(name):
    return {"type": "Var", "name": name}


class ProgIrEmitter:
    """The fixed correspondence walk. Collects blockers instead of failing
    fast so the residual is fully enumerated; never yields a partial IR."""

    def __init__(self, view):
        self.v = view
        self.blockers: set[str] = set()
        self.extern_names: set[str] = set()
        self.recv_methods: set[str] = set()
        self.has_recv_call = False
        self.variants: set[str] = set()
        self.params: List[str] = []
        self._synth = 0
        # floordiv statement-lift context: prelude statements minted by an
        # expression lift, and whether the current expression position is
        # evaluated exactly once at statement entry (see module docstring).
        self._prelude: List[Dict[str, Any]] = []
        self._once = False

    # ---- bookkeeping -------------------------------------------------------
    def _blk(self, name: str):
        self.blockers.add(name)
        return None

    def _use(self, variant: str):
        self.variants.add(variant)

    def _synth_name(self) -> str:
        n = "__u%d" % self._synth
        self._synth += 1
        return n

    def _stmt_value(self, node):
        """Emit a statement-value expression with the floordiv lift armed.
        Returns (term, prelude_stmts) — the caller prepends the prelude."""
        saved_prelude, saved_once = self._prelude, self._once
        self._prelude, self._once = [], True
        term = self.emit_expr(node)
        pre = self._prelude
        self._prelude, self._once = saved_prelude, saved_once
        return term, pre

    def _with_prelude(self, pre, stmt):
        if not pre:
            return stmt
        self._use("Seq")
        return {"type": "ProgSeq", "stmts": pre + [stmt]}

    def _emit_once_off(self, node):
        """Emit an expression in a NOT-always-evaluated position (a branch,
        a per-iteration subtree): the floordiv lift is disarmed inside."""
        saved = self._once
        self._once = False
        try:
            return self.emit_expr(node)
        finally:
            self._once = saved

    # ---- function entry ----------------------------------------------------
    def emit_function(self, froot) -> Optional[Dict[str, Any]]:
        v = self.v
        k = v.kind(froot)
        if k == "AsyncFunctionDef":
            self._blk("Await")
        elif k != "FunctionDef":
            return self._blk("Other:not_a_function:%s" % k)
        if v.children(froot, "decorator_list"):
            self._blk("Decorator")
        stmts: List[Dict[str, Any]] = []
        stmts.extend(self._emit_params(v.child(froot, "args")))
        body = self._peel_docstring(v.children(froot, "body"))
        for s in body:
            t = self.emit_stmt(s)
            if t is not None and t is not _SKIP:
                stmts.append(t)
        self._use("Seq")
        return {"type": "ProgSeq", "stmts": stmts}

    def _emit_params(self, args_node) -> List[Dict[str, Any]]:
        v = self.v
        out: List[Dict[str, Any]] = []
        if args_node is None:
            return out
        if v.child(args_node, "vararg") is not None or \
                v.child(args_node, "kwarg") is not None:
            self._blk("StarArgsParam")
        pos = v.children(args_node, "posonlyargs") + v.children(args_node, "args")
        defaults = v.children(args_node, "defaults")
        n_no_default = len(pos) - len(defaults)
        for i, p in enumerate(pos):
            name = v.scalar(p, "arg")
            d = None
            if i >= n_no_default:
                d = self.emit_expr(defaults[i - n_no_default])
            self._use("DefFnParam")
            self.params.append(name if isinstance(name, str) else "?")
            out.append({"type": "ProgDefFnParam", "name": name, "default": d})
        kwonly = v.indexed_children(args_node, "kwonlyargs")
        kw_defaults = dict(v.indexed_children(args_node, "kw_defaults"))
        for idx, p in kwonly:
            name = v.scalar(p, "arg")
            d = None
            if idx in kw_defaults:
                d = self.emit_expr(kw_defaults[idx])
            self._use("DefFnParam")
            self.params.append(name if isinstance(name, str) else "?")
            out.append({"type": "ProgDefFnParam", "name": name, "default": d})
        return out

    def _peel_docstring(self, body):
        v = self.v
        if body and v.kind(body[0]) == "Expr":
            val = v.child(body[0], "value")
            if val is not None and v.kind(val) == "Constant" and \
                    isinstance(v.scalar(val, "value"), str):
                return body[1:]
        return body

    # ---- statement blocks --------------------------------------------------
    def _emit_block(self, stmts) -> Dict[str, Any]:
        terms = []
        for s in stmts:
            t = self.emit_stmt(s)
            if t is not None and t is not _SKIP:
                terms.append(t)
        if len(terms) == 1:
            return terms[0]
        self._use("Seq")
        return {"type": "ProgSeq", "stmts": terms}

    def _opt_block(self, stmts) -> Optional[Dict[str, Any]]:
        if not stmts:
            return None
        return self._emit_block(stmts)

    # ---- statements ---------------------------------------------------------
    def emit_stmt(self, s):
        v = self.v
        kind = v.kind(s)
        base = kind.split(":", 1)[0]

        if base == "Return":
            val = v.child(s, "value")
            self._use("Return")
            if val is None:
                return {"type": "ProgReturn", "value": None}
            value_t, pre = self._stmt_value(val)
            return self._with_prelude(pre, {"type": "ProgReturn",
                                            "value": value_t})

        if base == "Assign":
            targets = v.children(s, "targets")
            value_t, pre = self._stmt_value(v.child(s, "value"))
            if len(targets) == 1:
                return self._with_prelude(
                    pre, self._assign_target(targets[0], value_t))
            # a = b = expr  ->  a = expr; b = a  (all-plain-Name only).
            if all(v.kind(t) == "Name" for t in targets):
                names = [v.scalar(t, "id") for t in targets]
                stmts = pre + [self._mk_assign(names[0], value_t)]
                for nm in names[1:]:
                    stmts.append(self._mk_assign(nm, _var(names[0])))
                self._use("Seq")
                return {"type": "ProgSeq", "stmts": stmts}
            return self._blk("MultiTargetAssign")

        if base == "AnnAssign":
            val = v.child(s, "value")
            if val is None:
                return _SKIP    # bare annotation: not evaluated at runtime
            value_t, pre = self._stmt_value(val)
            return self._with_prelude(
                pre, self._assign_target(v.child(s, "target"), value_t))

        if base == "AugAssign":
            return self._emit_aug_assign(s, kind)

        if base == "If":
            # the test re-evaluates WITH the statement: lift armed, prelude
            # precedes the ProgIfStmt (re-runs whenever the if re-runs).
            cond, pre = self._stmt_value(v.child(s, "test"))
            then = self._emit_block(v.children(s, "body"))
            orelse = self._opt_block(v.children(s, "orelse"))
            self._use("IfStmt")
            return self._with_prelude(pre, {"type": "ProgIfStmt",
                                            "cond": cond, "then": then,
                                            "orelse": orelse})

        if base == "For":
            return self._emit_for(s)
        if base == "AsyncFor":
            return self._blk("Await")

        if base == "While":
            cond = self.emit_expr(v.child(s, "test"))
            body = self._emit_block(v.children(s, "body"))
            orelse = self._opt_block(v.children(s, "orelse"))
            self._use("While")
            return {"type": "ProgWhile", "cond": cond, "body": body,
                    "orelse": orelse}

        if base in ("Break", "Continue"):
            self._use("LoopCtl")
            return {"type": "ProgLoopCtl", "kind": base.lower()}

        if base == "Try":
            return self._emit_try(s)
        if base == "TryStar":
            return self._blk("TryStar")

        if base == "Raise":
            if v.child(s, "cause") is not None:
                return self._blk("RaiseFrom")
            exc = v.child(s, "exc")
            self._use("Raise")
            return {"type": "ProgRaise",
                    "exc": self.emit_expr(exc) if exc is not None else None}

        if base == "Import":
            return self._emit_import(s)
        if base == "ImportFrom":
            return self._emit_import_from(s)

        if base == "Expr":
            # a bare expression statement: emitted as-is (ProgSeq evaluates
            # and discards it — probed engine convention).
            value_t, pre = self._stmt_value(v.child(s, "value"))
            if value_t is None:
                return None
            return self._with_prelude(pre, value_t)

        if base == "Pass":
            return _SKIP
        if base == "Assert":
            return self._blk("Assert")
        if base == "Delete":
            return self._blk("Delete")
        if base in ("Global", "Nonlocal"):
            return self._blk("GlobalNonlocal")
        if base in ("With", "AsyncWith"):
            if base == "AsyncWith":
                self._blk("Await")
            return self._blk("With")
        if base == "Match":
            return self._blk("Match")
        if base in ("FunctionDef", "AsyncFunctionDef"):
            return self._blk("DefFn")
        if base == "ClassDef":
            return self._blk("ClassDef")
        return self._blk("Other:stmt_%s" % base)

    def _mk_assign(self, name, value_t):
        self._use("AssignVar")
        return {"type": "ProgAssignVar", "name": name, "value": value_t}

    def _assign_target(self, tgt, value_t):
        v = self.v
        k = v.kind(tgt)
        if k == "Name":
            return self._mk_assign(v.scalar(tgt, "id"), value_t)
        if k in ("Tuple", "List"):
            names = []
            for e in v.children(tgt, "elts"):
                ek = v.kind(e)
                if ek == "Starred":
                    return self._blk("StarUnpack")
                if ek != "Name":
                    return self._blk("NestedUnpack")
                names.append(v.scalar(e, "id"))
            self._use("TupleUnpack")
            return {"type": "ProgTupleUnpack", "targets": names,
                    "value": value_t}
        if k == "Attribute":
            obj = self.emit_expr(v.child(tgt, "value"))
            self._use("AttrSet")
            return {"type": "ProgAttrSet", "obj": obj,
                    "attr": v.scalar(tgt, "attr"), "value": value_t}
        if k == "Subscript":
            sl = v.child(tgt, "slice")
            if sl is None or v.kind(sl) == "Slice":
                return self._blk("SliceSubscript")
            obj = self.emit_expr(v.child(tgt, "value"))
            idx = self.emit_expr(sl)
            self._use("SubscriptSet")
            return {"type": "ProgSubscriptSet", "obj": obj, "index": idx,
                    "value": value_t}
        if k == "Starred":
            return self._blk("StarUnpack")
        return self._blk("Other:target_%s" % k)

    def _emit_aug_assign(self, s, kind):
        v = self.v
        opname = kind.split(":", 1)[1] if ":" in kind else ""
        op = _AUGOP.get(opname)
        if op is None:
            return self._blk("OpExt:%s" % (opname or "aug_unknown"))
        tgt = v.child(s, "target")
        value_t, pre = self._stmt_value(v.child(s, "value"))
        if pre:
            inner = self._emit_aug_target(s, opname, op, tgt, value_t)
            if inner is None:
                return None
            return self._with_prelude(pre, inner)
        return self._emit_aug_target(s, opname, op, tgt, value_t)

    def _emit_aug_target(self, s, opname, op, tgt, value_t):
        v = self.v
        tk = v.kind(tgt)
        if tk == "Name":
            self._use("AugAssign")
            return {"type": "ProgAugAssign", "name": v.scalar(tgt, "id"),
                    "op": op, "value": value_t}
        # obj.attr op= v / obj[i] op= v -> read-modify-write, PURE targets only.
        if opname not in _AUGOP_EXPR:
            return self._blk("OpExt:%s" % opname)
        if tk == "Attribute":
            obj = self.emit_expr(v.child(tgt, "value"))
            if _contains_extern(obj):
                return self._blk("AugAssignImpureTarget")
            attr = v.scalar(tgt, "attr")
            self._use("AttrGet")
            get = {"type": "ProgAttrGet", "obj": obj, "attr": attr}
            self._use("AttrSet")
            return {"type": "ProgAttrSet", "obj": obj, "attr": attr,
                    "value": self._binop_term(opname, get, value_t)}
        if tk == "Subscript":
            sl = v.child(tgt, "slice")
            if sl is None or v.kind(sl) == "Slice":
                return self._blk("SliceSubscript")
            obj = self.emit_expr(v.child(tgt, "value"))
            idx = self.emit_expr(sl)
            if _contains_extern(obj) or _contains_extern(idx):
                return self._blk("AugAssignImpureTarget")
            self._use("Subscript")
            get = {"type": "ProgSubscript", "obj": obj, "index": idx}
            self._use("SubscriptSet")
            return {"type": "ProgSubscriptSet", "obj": obj, "index": idx,
                    "value": self._binop_term(opname, get, value_t)}
        return self._blk("Other:aug_target_%s" % tk)

    def _emit_for(self, s):
        v = self.v
        tgt = v.child(s, "target")
        it = self.emit_expr(v.child(s, "iter"))
        tk = v.kind(tgt)
        body_stmts = v.children(s, "body")
        orelse = self._opt_block(v.children(s, "orelse"))
        if tk == "Name":
            body = self._emit_block(body_stmts)
            self._use("ForEach")
            return {"type": "ProgForEach", "var": v.scalar(tgt, "id"),
                    "iter": it, "body": body, "orelse": orelse}
        if tk in ("Tuple", "List"):
            names = []
            for e in v.children(tgt, "elts"):
                if v.kind(e) != "Name":
                    return self._blk("StarUnpack" if v.kind(e) == "Starred"
                                     else "NestedUnpack")
                names.append(v.scalar(e, "id"))
            tmp = self._synth_name()
            self._use("TupleUnpack")
            unpack = {"type": "ProgTupleUnpack", "targets": names,
                      "value": _var(tmp)}
            inner = [unpack]
            for b in body_stmts:
                t = self.emit_stmt(b)
                if t is not None and t is not _SKIP:
                    inner.append(t)
            self._use("Seq")
            self._use("ForEach")
            return {"type": "ProgForEach", "var": tmp, "iter": it,
                    "body": {"type": "ProgSeq", "stmts": inner},
                    "orelse": orelse}
        return self._blk("Other:for_target_%s" % tk)

    def _emit_try(self, s):
        v = self.v
        if v.children(s, "finalbody"):
            return self._blk("TryFinally")
        if v.children(s, "orelse"):
            return self._blk("TryElse")
        handlers = v.children(s, "handlers")
        if len(handlers) != 1:
            return self._blk("MultiExcept")
        h = handlers[0]
        htype = v.child(h, "type")
        if htype is not None:
            if not (v.kind(htype) == "Name"
                    and v.scalar(htype, "id") in _CATCH_ALL_EXC):
                return self._blk("TypedExcept")
        exc_var = v.scalar(h, "name")
        if exc_var is _MISSING or exc_var is None:
            exc_var = ""
        body = self._emit_block(v.children(s, "body"))
        handler = self._opt_block(v.children(h, "body"))
        self._use("TryOr")
        return {"type": "ProgTryOr", "body": body, "exc_var": exc_var,
                "handler": handler}

    def _emit_import(self, s):
        v = self.v
        imps = []
        for al in v.children(s, "names"):
            name = v.scalar(al, "name")
            asname = v.scalar(al, "asname")
            # graph mode cannot see asname (not a _SCALAR_FIELDS member) —
            # carried as absent; ProgImportStmt is a ProgEval no-op (caveat
            # documented in the module docstring).
            if asname is _MISSING or asname is None:
                asname = ""
            self._use("ImportStmt")
            imps.append({"type": "ProgImportStmt", "module": name,
                         "alias": asname, "names": []})
        if len(imps) == 1:
            return imps[0]
        self._use("Seq")
        return {"type": "ProgSeq", "stmts": imps}

    def _emit_import_from(self, s):
        v = self.v
        module = v.scalar(s, "module")
        if module is _MISSING:
            if self.v.graph_mode:
                return self._blk("GraphRepr:importfrom_module")
            module = None
        level = v.scalar(s, "level")
        if level is _MISSING or not isinstance(level, int):
            level = 0
        mod_str = "." * level + (module or "")
        names = []
        alias = ""
        aliases = v.children(s, "names")
        for al in aliases:
            names.append(v.scalar(al, "name"))
            asn = v.scalar(al, "asname")
            if isinstance(asn, str) and asn:
                if len(aliases) == 1:
                    alias = asn
                else:
                    return self._blk("ImportAsName")
        self._use("ImportStmt")
        return {"type": "ProgImportStmt", "module": mod_str, "alias": alias,
                "names": names}

    # ---- expressions ---------------------------------------------------------
    def emit_expr(self, e):
        if e is None:
            return self._blk("Other:missing_expr")
        v = self.v
        kind = v.kind(e)
        base = kind.split(":", 1)[0]

        if base == "Constant":
            val = v.scalar(e, "value")
            if val is _MISSING:
                return self._blk("ConstantNonScalar")
            return _lit(val)

        if base == "Name":
            return _var(v.scalar(e, "id"))

        if base == "BinOp":
            return self._emit_binop(e, kind)

        if base == "UnaryOp":
            opname = kind.split(":", 1)[1] if ":" in kind else ""
            operand = self.emit_expr(v.child(e, "operand"))
            if opname == "USub":
                return {"type": "Neg", "arg": operand}
            if opname == "Not":
                return {"type": "Not", "arg": operand}
            return self._blk("OpExt:%s" % (opname or "unary_unknown"))

        if base == "BoolOp":
            return self._emit_boolop(e, kind)

        if base == "Compare":
            return self._emit_compare(e)

        if base == "IfExp":
            # branch lifting is sound: lifted preludes are Prog-free pure
            # arithmetic (cannot trap/effect — see _emit_floordiv guard)
            return {"type": "IfThenElse",
                    "cond": self.emit_expr(v.child(e, "test")),
                    "then": self.emit_expr(v.child(e, "body")),
                    "other": self.emit_expr(v.child(e, "orelse"))}

        if base == "Call":
            return self._emit_call(e)

        if base == "Attribute":
            self._use("AttrGet")
            return {"type": "ProgAttrGet",
                    "obj": self.emit_expr(v.child(e, "value")),
                    "attr": v.scalar(e, "attr")}

        if base == "Subscript":
            sl = v.child(e, "slice")
            if sl is None:
                return self._blk("SliceSubscript")
            if v.kind(sl) == "Slice":
                return self._emit_slice(e, sl)
            self._use("Subscript")
            return {"type": "ProgSubscript",
                    "obj": self.emit_expr(v.child(e, "value")),
                    "index": self.emit_expr(sl)}

        if base in ("List", "Tuple", "Set"):
            items = []
            for x in v.children(e, "elts"):
                if v.kind(x) == "Starred":
                    return self._blk("StarElement")
                items.append(self.emit_expr(x))
            self._use("ContainerLit")
            return {"type": "ProgContainerLit", "kind": base.lower(),
                    "items": items}

        if base == "Dict":
            keys = v.children(e, "keys")
            values = v.children(e, "values")
            if len(keys) != v.list_len(e, "keys") or len(keys) != len(values):
                return self._blk("DictUnpack")   # a None key (dict **spread)
            items = []
            for k, val in zip(keys, values):
                items.append(self.emit_expr(k))
                items.append(self.emit_expr(val))
            self._use("ContainerLit")
            return {"type": "ProgContainerLit", "kind": "dict",
                    "items": items}

        if base in ("ListComp", "GeneratorExp"):
            return self._emit_comprehension(e, base)
        if base == "SetComp":
            return self._blk("ComprehensionSet")
        if base == "DictComp":
            return self._blk("ComprehensionDict")

        if base == "JoinedStr":
            return self._emit_fstring(e)
        if base == "FormattedValue":
            return self._emit_formatted_value(e)

        if base == "Lambda":
            return self._blk("Lambda")
        if base in ("Yield", "YieldFrom"):
            return self._blk("Yield")
        if base == "Await":
            return self._blk("Await")
        if base == "NamedExpr":
            return self._blk("NamedExpr")
        if base == "Starred":
            return self._blk("StarElement")
        if base == "Slice":
            return self._blk("SliceSubscript")
        return self._blk("Other:expr_%s" % base)

    def _statically_string(self, e) -> bool:
        v = self.v
        k = v.kind(e)
        if k == "JoinedStr":
            return True
        if k == "Constant":
            val = v.scalar(e, "value")
            return isinstance(val, str)
        return False

    def _binop_term(self, opname, a_t, b_t):
        if opname in _BINOP_ITEMS:
            return {"type": _BINOP_ITEMS[opname], "items": [a_t, b_t]}
        return {"type": _BINOP_AB[opname], "a": a_t, "b": b_t}

    def _emit_binop(self, e, kind):
        v = self.v
        opname = kind.split(":", 1)[1] if ":" in kind else ""
        left, right = v.child(e, "left"), v.child(e, "right")
        if opname == "FloorDiv":
            return self._emit_floordiv(left, right)
        if opname not in _BINOP_ITEMS and opname not in _BINOP_AB:
            # walk operands anyway so nested blockers are still enumerated
            self.emit_expr(left)
            self.emit_expr(right)
            return self._blk("OpExt:%s" % (opname or "binop_unknown"))
        if opname in ("Add", "Mult") and (self._statically_string(left)
                                          or self._statically_string(right)):
            # DSL Plus/Times are numeric ('a'+'b' -> 0, measured): a
            # statically-string operand would be a silent wrong emit.
            self.emit_expr(left)
            self.emit_expr(right)
            return self._blk("StrArithStatic")
        return self._binop_term(opname, self.emit_expr(left),
                                self.emit_expr(right))

    def _statically_positive_number(self, e) -> bool:
        if self.v.kind(e) != "Constant":
            return False
        val = self.v.scalar(e, "value")
        return (isinstance(val, (int, float)) and not isinstance(val, bool)
                and val > 0)

    def _emit_floordiv(self, left, right):
        """`a // b` lifts to the CPython-EXACT composite prelude

            __uN = a - (a % b) ; __uN //= b

        (DSL Mod is Python-exact for POSITIVE divisors — measured; the
        native ProgAugAssign floordiv is trunc-division — measured — but
        trunc of an exact multiple IS floor), when:
          * the divisor is a statically-POSITIVE number literal (Mod
            diverges from CPython on negative divisors — measured),
          * both operand trees are Prog-free (pure DSL arithmetic: no
            extern/subscript/attr — cannot trap, cannot effect; measured:
            engine arithmetic never raises, so pre-evaluating a branch
            Python would skip is observationally invisible),
          * the position re-evaluates with its STATEMENT (`_once`): any
            statement-value slot incl. conditional subexpressions, and If
            tests — but NOT While tests (per-iteration staleness) and NOT
            comprehension subtrees (loop-var capture).
        Else: honest `OpExt:FloorDiv` blocker; DSL Div is TRUE division and
        never a substitute (the frozen emitter's fold is not repeated).
        Known residual: a float dividend yields an int-typed (value-equal)
        result — recorded in PROGRAM_SYNTHESIS_P2_PYTHON.md."""
        a_t = self.emit_expr(left)
        b_t = self.emit_expr(right)
        if (not self._once or not self._statically_positive_number(right)
                or _contains_prog(a_t) or _contains_prog(b_t)):
            return self._blk("OpExt:FloorDiv")
        tmp = self._synth_name()
        self._use("AssignVar")
        self._use("AugAssign")
        self._prelude.append(
            {"type": "ProgAssignVar", "name": tmp,
             "value": {"type": "Minus", "a": a_t,
                       "b": {"type": "Mod", "a": a_t, "b": b_t}}})
        self._prelude.append({"type": "ProgAugAssign", "name": tmp,
                              "op": "floordiv", "value": b_t})
        return _var(tmp)

    def _emit_boolop(self, e, kind):
        # OPERAND semantics (ast_term_rules boolop_rules precedent):
        #   a or b  == a if a else b ;  a and b == b if a else a
        # right-nested for N; pure re-use of the value subtree is safe
        # (expressions are unfueled; oracle calls are pure).
        v = self.v
        opname = kind.split(":", 1)[1] if ":" in kind else ""
        values = [self.emit_expr(x) for x in v.children(e, "values")]
        if len(values) < 2:
            return self._blk("Other:boolop_arity")
        out = values[-1]
        for val in reversed(values[:-1]):
            if opname == "Or":
                out = {"type": "IfThenElse", "cond": val, "then": val,
                       "other": out}
            else:
                out = {"type": "IfThenElse", "cond": val, "then": out,
                       "other": val}
        return out

    def _emit_compare(self, e):
        v = self.v
        left = v.child(e, "left")
        ops = v.children(e, "ops")
        comparators = v.children(e, "comparators")
        if not ops or len(ops) != len(comparators):
            return self._blk("Other:compare_malformed")
        terms = []
        prev = left
        for op_node, comp in zip(ops, comparators):
            opk = v.kind(op_node)
            a_t = self.emit_expr(prev)
            b_t = self.emit_expr(comp)
            if opk in _CMPOP:
                terms.append({"type": _CMPOP[opk], "a": a_t, "b": b_t})
            elif opk == "NotEq":
                terms.append({"type": "Not",
                              "arg": {"type": "Eq", "a": a_t, "b": b_t}})
            elif opk in ("In", "NotIn"):
                if self._statically_string(comp):
                    # DSL In is collection membership, not substring (measured).
                    self._blk("InStrStatic")
                t = {"type": "In", "member": a_t, "container": b_t}
                terms.append(t if opk == "In" else {"type": "Not", "arg": t})
            elif opk in ("Is", "IsNot"):
                self._use("IsOp")
                terms.append({"type": "ProgIsOp", "a": a_t, "b": b_t,
                              "negated": opk == "IsNot"})
            else:
                self._blk("OpExt:%s" % opk)
            prev = comp
        if len(terms) == 1:
            return terms[0]
        return {"type": "And", "items": terms}

    def _emit_slice(self, sub_node, slice_node):
        """`x[a:b:c]` (read position) -> `ProgSlice{obj, start, stop, step}`
        — Q1.5, targets the Q1 `ProgSlice` engine Term (module docstring
        "ARC 2 Q1.5 WIDENING"). Each of start/stop/step is emitted when
        present, `None` when the AST slot is absent (`a[:2]`, `a[1:]`,
        `a[::2]`, ...) — the SAME optional-child convention every other
        Prog* node in this emitter already uses. A slice used as an
        ASSIGNMENT target has no engine write-back path and stays the
        `SliceSubscript` blocker (`_assign_target`, unchanged)."""
        v = self.v
        obj = self.emit_expr(v.child(sub_node, "value"))
        lower = v.child(slice_node, "lower")
        upper = v.child(slice_node, "upper")
        step = v.child(slice_node, "step")
        start_t = self.emit_expr(lower) if lower is not None else None
        stop_t = self.emit_expr(upper) if upper is not None else None
        step_t = self.emit_expr(step) if step is not None else None
        self._use("Slice")
        return {"type": "ProgSlice", "obj": obj, "start": start_t,
                "stop": stop_t, "step": step_t}

    def _dotted_name(self, f) -> Optional[str]:
        v = self.v
        parts = []
        cur = f
        while v.kind(cur) == "Attribute":
            attr = v.scalar(cur, "attr")
            if not isinstance(attr, str):
                return None
            parts.append(attr)
            cur = v.child(cur, "value")
            if cur is None:
                return None
        if v.kind(cur) == "Name":
            base = v.scalar(cur, "id")
            if isinstance(base, str):
                parts.append(base)
                return ".".join(reversed(parts))
        return None

    def _emit_call(self, e):
        v = self.v
        if v.children(e, "keywords"):
            return self._blk("KwargsCall")
        args_nodes = v.children(e, "args")
        if any(v.kind(a) == "Starred" for a in args_nodes):
            return self._blk("StarArgsCall")
        f = v.child(e, "func")
        if f is None:
            return self._blk("Other:call_no_func")
        fk = v.kind(f)
        name = None
        recv = None
        if fk == "Name":
            name = v.scalar(f, "id")
        elif fk == "Attribute":
            attr_name = v.scalar(f, "attr")
            # Q1.5 (module docstring "ARC 2 Q1.5 WIDENING"): recognise a
            # recv-form call by the METHOD NAME FIRST, before falling back
            # to `_dotted_name`'s Name-rooted walk. This matters because
            # `_dotted_name` cannot tell a local variable (`word.split()`)
            # from a module (`math.sqrt()`) apart — both are bare Names —
            # so without this, the Q1 recv-oracle widening below would
            # almost never fire on real code (MBPP receivers are
            # overwhelmingly local variables, not modules). A method name
            # in the Q1 recv-oracle set, OR a KNOWN MUTATING collection/
            # dict method the engine structurally refuses (Q1 notes §3,
            # `_RECV_BLOCKED_METHODS`), is ALWAYS resolved as recv-form
            # regardless of receiver shape. Any OTHER method name
            # (`self.foo()`, `match.group()`, a custom class method, ...)
            # keeps the ORIGINAL dotted-vs-recv resolution byte-unchanged —
            # this widening never reclassifies a call the pre-Q1.5 emitter
            # already handled correctly.
            if isinstance(attr_name, str) and (
                    attr_name in NATIVE_RECV_ORACLES
                    or attr_name in _RECV_BLOCKED_METHODS):
                recv_expr = v.child(f, "value")
                self.has_recv_call = True
                if attr_name not in NATIVE_RECV_ORACLES:
                    # A named, honest emission-time blocker — not an
                    # emit-and-trap. Still walk the receiver + args so
                    # nested blockers stay fully enumerated (the module's
                    # own "walk continues past a blocked construct" rule).
                    self.emit_expr(recv_expr)
                    for a in args_nodes:
                        self.emit_expr(a)
                    return self._blk("RecvMethod:%s" % attr_name)
                name = attr_name
                recv = self.emit_expr(recv_expr)
                self.recv_methods.add(name)
            else:
                dotted = self._dotted_name(f)
                if dotted is not None:
                    name = dotted
                else:
                    name = attr_name
                    recv_expr = v.child(f, "value")
                    self.has_recv_call = True
                    recv = self.emit_expr(recv_expr)
                    if isinstance(name, str):
                        self.recv_methods.add(name)
        else:
            return self._blk("CallFuncComplex")
        if not isinstance(name, str):
            return self._blk("Other:call_name_unreadable")
        if recv is None:
            self.extern_names.add(name)
        if recv is None and name == "isinstance" and len(args_nodes) == 2:
            return self._emit_isinstance_call(args_nodes)
        args = [self.emit_expr(a) for a in args_nodes]
        self._use("CallExtern")
        return {"type": "ProgCallExtern", "name": name, "recv": recv,
                "args": args}

    def _emit_isinstance_call(self, args_nodes):
        """`isinstance(x, T)` — Q1.5. The engine's type argument is a
        TYPE-NAME STRING (Q1 notes §2 item 3), never a real type object.
        A bare `Name` second argument translates to `Lit(name)`; a
        tuple-of-types has no OR-of-type-names engine convention
        (`IsinstanceMultiType`); anything else is `IsinstanceComplexType`.
        Runtime validity of the name itself (`extern:isinstance:
        unknown_type:<name>`) is the engine's honest concern, not this
        emitter's — emission is type-blind here too."""
        v = self.v
        arg0 = self.emit_expr(args_nodes[0])
        type_node = args_nodes[1]
        k = v.kind(type_node)
        if k == "Name":
            tid = v.scalar(type_node, "id")
            if not isinstance(tid, str):
                return self._blk("Other:isinstance_type_unreadable")
            type_t = _lit(tid)
        elif k in ("Tuple", "List"):
            for el in v.children(type_node, "elts"):
                self.emit_expr(el)
            return self._blk("IsinstanceMultiType")
        else:
            self.emit_expr(type_node)
            return self._blk("IsinstanceComplexType")
        # `extern_names` already carries "isinstance" (added by the caller
        # before dispatching here, since `recv is None`).
        self._use("CallExtern")
        return {"type": "ProgCallExtern", "name": "isinstance", "recv": None,
                "args": [arg0, type_t]}

    def _emit_comprehension(self, e, base):
        v = self.v
        gens = v.children(e, "generators")
        if len(gens) != 1:
            return self._blk("CompMultiClause")
        gen = gens[0]
        is_async = v.scalar(gen, "is_async")
        if isinstance(is_async, int) and is_async:
            return self._blk("Await")
        tgt = v.child(gen, "target")
        if v.kind(tgt) != "Name":
            return self._blk("CompTargetComplex")
        ifs = v.children(gen, "ifs")
        if len(ifs) > 1:
            return self._blk("CompMultiClause")
        cond = self._emit_once_off(ifs[0]) if ifs else None
        variant = ("ProgComprehensionList" if base == "ListComp"
                   else "ProgComprehensionGen")
        self._use(variant[4:])
        return {"type": variant, "var": v.scalar(tgt, "id"),
                "source": self._emit_once_off(v.child(gen, "iter")),
                "expr": self._emit_once_off(v.child(e, "elt")), "cond": cond}

    def _emit_fstring(self, e):
        v = self.v
        parts = []
        for p in v.children(e, "values"):
            pk = v.kind(p)
            if pk == "Constant":
                val = v.scalar(p, "value")
                if not isinstance(val, str):
                    self._blk("ConstantNonScalar")
                    continue
                parts.append(_lit(val))
            elif pk == "FormattedValue":
                t = self._emit_formatted_value(p)
                if t is not None:
                    parts.append(t)
            else:
                self._blk("Other:fstring_part_%s" % pk)
        self._use("FString")
        return {"type": "ProgFString", "parts": parts}

    def _emit_formatted_value(self, p):
        v = self.v
        if v.child(p, "format_spec") is not None:
            return self._blk("FStringFormatSpec")
        conv = v.scalar(p, "conversion")
        if conv is _MISSING:
            if v.graph_mode:
                # ingest_ast does not carry the conversion flag; guessing
                # would silently drop !r/!s/!a. Honest graph-mode refusal.
                return self._blk("GraphRepr:fstring_conversion")
            conv = -1
        if isinstance(conv, int) and conv != -1:
            return self._blk("FStringConversion")
        return self.emit_expr(v.child(p, "value"))


# --------------------------------------------------------------------------- #
#  Mechanical helpers + public entry points.
# --------------------------------------------------------------------------- #
def _contains_extern(term) -> bool:
    """True iff the built Term-JSON subtree contains a ProgCallExtern —
    the purity guard for read-modify-write desugars (double evaluation of
    an extern-bearing subtree is not observationally safe)."""
    if isinstance(term, dict):
        if term.get("type") == "ProgCallExtern":
            return True
        return any(_contains_extern(v) for v in term.values())
    if isinstance(term, (list, tuple)):
        return any(_contains_extern(x) for x in term)
    return False


def _contains_prog(term) -> bool:
    """True iff the subtree contains ANY Prog* node — the strict purity
    guard for the floordiv statement-lift (only trap-free, effect-free DSL
    arithmetic may be hoisted ahead of its statement)."""
    if isinstance(term, dict):
        t = term.get("type", "")
        if isinstance(t, str) and t.startswith("Prog"):
            return True
        return any(_contains_prog(v) for v in term.values())
    if isinstance(term, (list, tuple)):
        return any(_contains_prog(x) for x in term)
    return False


def _resolve_function_node(fn, name: Optional[str] = None):
    if isinstance(fn, ast.AST):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return fn
        raise ValueError("emit_prog_ir needs a FunctionDef node, got %s"
                         % type(fn).__name__)
    tree = ast.parse(textwrap.dedent(fn))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if name is None or node.name == name:
                return node
    raise ValueError("no top-level function%s in source"
                     % ("" if name is None else " named %r" % name))


def _finish(em: ProgIrEmitter, ir) -> Dict[str, Any]:
    if em.blockers:
        return {"ok": False, "blockers": sorted(em.blockers)}
    # Q1.5: a recv-form call is now predictable too, as long as EVERY
    # method name used is in the Q1 recv-oracle set (module docstring)
    # — `em.recv_methods` can in practice never hold anything else, since
    # `_emit_call` blocks an out-of-set method name at emission time; the
    # subset check is kept anyway as the honest, self-documenting
    # invariant this classification actually depends on.
    predictable = (em.extern_names <= NATIVE_ORACLES
                   and em.recv_methods <= NATIVE_RECV_ORACLES)
    # Q1.5 BUG FIX (found while verifying real execution, not just the
    # ok/predictable label): `native_oracles` is the set a CALLER must
    # declare in ProgEval's `oracles` Dict to actually run this program.
    # Pre-Q1.5 this was `extern_names & NATIVE_ORACLES` only, which was
    # correct BY CONSTRUCTION because a recv-form call always made
    # `predictable` False (so no predictable program ever needed a recv
    # oracle declared). Now that a recv-form call can itself be
    # predictable, a caller who declares only `extern_names & NATIVE_
    # ORACLES` and skips `recv_methods` gets an honest but SPURIOUS
    # `extern:<method>` trap on an otherwise-predictable program — this
    # union is the actual, complete oracle-declaration set.
    native_oracles = sorted((em.extern_names & NATIVE_ORACLES) | em.recv_methods)
    return {"ok": True, "ir": ir,
            "externs": sorted(em.extern_names),
            "recv_methods": sorted(em.recv_methods),
            "has_recv_call": em.has_recv_call,
            "native_oracles": native_oracles,
            "predictable": predictable,
            "params": list(em.params),
            "variants": sorted(em.variants)}


def emit_prog_ir(fn, *, name: Optional[str] = None) -> Dict[str, Any]:
    """Source string or ast.FunctionDef -> hub Program-IR Term-JSON.
    {"ok": True, "ir": ..., ...} or {"ok": False, "blockers": [...]}."""
    node = _resolve_function_node(fn, name)
    em = ProgIrEmitter(_AstView())
    ir = em.emit_function(node)
    return _finish(em, ir)


def emit_prog_ir_from_graph(container, func_root) -> Dict[str, Any]:
    """An `ingest_ast` AstNode subgraph (any node/neighbours container:
    a Substrate or a mechanical shim) -> the same contract as
    `emit_prog_ir`. Graph-representation gaps block with `GraphRepr:`."""
    em = ProgIrEmitter(_GraphView(container))
    ir = em.emit_function(func_root)
    return _finish(em, ir)


__all__ = ["emit_prog_ir", "emit_prog_ir_from_graph", "ProgIrEmitter",
           "NATIVE_ORACLES", "NATIVE_RECV_ORACLES", "P1_VARIANT_SET"]
