"""ast_to_term — the WORLD-ADAPTER + MECHANICAL AST->TERM EMITTER (cmsg160 fix).

THE CORRECTION (cmsg160). This session's "faculties" (grounding_generator,
ground_definition, the compute-cores) were PYTHON authored by LLM subagents — NOT
graph-resident, NOT agent-owned. That violates CLAUDE.md (the agent is a graph
running in Rust; Python is only the world adapter). A Python AST IS a typed graph;
the fix is to GIVE the faculties' compute-cores to the agent as graph data and have
the AGENT's graph machinery refactor them into NATIVE Term-trees (the DSL,
Rust-evaluated, agent-owned), keeping ONLY the I/O as world-adapter Python.

THIS MODULE PROVIDES ONLY (CLAUDE.md world-adapter layer):

  (1) THE WORLD-ADAPTER — `ingest_ast`: parse a Python compute-core's source into
      its `ast` and INGEST it as a TYPED GRAPH into the substrate (AST node ->
      typed substrate node; parent/child -> edges). MECHANICAL translation, no
      decisions ("a diagram is a graph", cmsg78). This is the legitimate
      world-adapter: code-as-graph.

  (2) THE MECHANICAL AST->TERM EMITTER — `emit_term`: a FIXED map from AST node
      TYPES to DSL Term node TYPES, the SAME for every faculty (NOT a per-faculty
      rewrite). ast.BinOp(Add)->Plus, Sub->Minus, Mult->Times, Div/FloorDiv->Div,
      Pow->Pow; UnaryOp(USub)->Neg; Constant->Lit; Name->Var; a held-leaf Call
      (betti_number) -> the held UseTool leaf; a sum(<genexp over range>) ->
      the held Sum-fold; a recursive faculty Call -> the already-emitted sub-tree.
      The emitter walks the INGESTED AST-GRAPH (not the Python objects) and
      composes the native Term-tree by the fixed map. The agent OWNS the result
      (a Term-tree, graph data in the substrate); the Rust substrate EVALUATES it.

THE LEAF BOUNDARY. The compute-core's COMPOSITION (the alternating sum, the
(2-chi)/2 divide) becomes native Term-tree, Rust-evaluated. Its held LEAF-quantity
(betti_number — Python, the held boundary/rank tower) crosses the held `UseTool`
boundary (term.rs: an effectful Term that dispatches to a registered Python
handler from INSIDE the Rust evaluator; tools.tool_fire_count proves it fired
natively). So the held tower stays Python (the world-adapter I/O), the compute
graph composition is the agent's native Term-tree.

NO LLM rewrites the faculties. NO per-faculty hand-composed Term-tree. The emitter
is a fixed node-type map; the agent applies it over the ingested AST-graph. The
output is Term-trees in the substrate, Rust-evaluated, self-verified on knowns.

See CLAUDE.md (world-adapter only) / [[ozma_order_n_concepts]] (the existing native
Term-tree composition this follows) / [[ozma_agent_writes_its_own_code]] /
[[ozma_dont_author_seeds_agent_designs_them]].
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Tuple


# ===========================================================================
# (1) THE WORLD-ADAPTER — Python compute-core -> AST -> typed substrate graph.
# Mechanical: each ast node becomes an `AstNode` substrate node carrying its node
# type + scalar fields; parent->child becomes a `child` edge tagged with the field
# role. No decisions over graph state — a pure code-as-graph translation.
# ===========================================================================

# the scalar (leaf-value) ast fields we copy onto the substrate node verbatim.
_SCALAR_FIELDS = ("value", "id", "arg", "name", "n", "s", "attr")


def open_ast_productions(substrate) -> int:
    """Open the Γ production admitting the AstNode -child-> AstNode edge — the
    code-as-graph vocabulary ('a diagram is a graph', cmsg78). Before this, the
    substrate's grammar rejects the edge (Type-2: 'AstNode' not in vocabulary).
    Idempotent. Part of the world-adapter boot (not an agent decision)."""
    try:
        substrate.add_production({
            "src": {"type": "AstNode", "var": "a"},
            "edge_type": "child",
            "tgt": {"type": "AstNode", "var": "b"},
            "where": None,
            "provenance": "ast_to_term:code_as_graph",
        })
        return 1
    except Exception:
        return 0


def _ast_node_type(node: ast.AST) -> str:
    """The ast node's class name (Module / FunctionDef / BinOp / Call / ...) — the
    TYPE the mechanical emitter keys off. For an operator node (BinOp/UnaryOp) we
    suffix the op class so Add/Sub/Mult/... are distinct types in the graph."""
    t = type(node).__name__
    op = getattr(node, "op", None)
    if op is not None:
        return f"{t}:{type(op).__name__}"
    return t


def ingest_ast(substrate, source: str, *, root_label: str = "") -> Dict[str, Any]:
    """WORLD-ADAPTER: parse `source` (a Python compute-core) into its `ast` and
    INGEST it as a typed graph. Each ast node -> an `AstNode` substrate node
    (attrs: ast_type + any scalar field + child field-roles); each parent->child
    edge -> a `child` edge carrying the field role + list index. Returns the ingest
    record {tree (the ast), root (the FunctionDef substrate node id per function),
    n_nodes}. Pure mechanical translation, no decisions."""
    tree = ast.parse(source)
    n_nodes = 0
    func_roots: Dict[str, int] = {}

    def _ingest(node: ast.AST, child_field: str, child_index: int) -> int:
        nonlocal n_nodes
        # the field-role + list index of THIS node under its parent are written into
        # its OWN attrs at creation (the substrate node attrs are write-once at
        # add_node; mutating node()['attrs'] afterwards is not write-through). The
        # emitter reads child_field/child_index to know operand roles (a vs b, the
        # genexp elt, ...). Mechanical, no decision.
        attrs = {"ast_type": _ast_node_type(node), "origin": "world_adapter_ast",
                 "child_field": child_field, "child_index": child_index}
        if root_label:
            attrs["module"] = root_label
        for f in _SCALAR_FIELDS:
            if hasattr(node, f):
                v = getattr(node, f)
                if isinstance(v, (int, float, str, bool)) or v is None:
                    attrs[f] = v
        # CODE-1 (code as a read register): the docstring is mechanical I/O — the
        # stdlib's own `ast.get_docstring` reads the function's leading string
        # literal (a Python parser fact, not a decision). Attached verbatim so a
        # reader can later comprehend it (domains/code_reading.py); every other
        # caller of ingest_ast is unaffected (an ADDITIVE attr, never read by the
        # existing emitter).
        if isinstance(node, ast.FunctionDef):
            attrs["docstring"] = ast.get_docstring(node)
        nid = substrate.add_node("AstNode", attrs)
        n_nodes += 1
        if isinstance(node, ast.FunctionDef):
            func_roots[node.name] = nid
        # children: walk each field; list fields carry an index, scalar fields -1.
        for field, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                cid = _ingest(value, field, -1)
                substrate.add_edge(nid, "child", cid)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, ast.AST):
                        cid = _ingest(item, field, i)
                        substrate.add_edge(nid, "child", cid)
        return nid

    module_root = _ingest(tree, "", -1)
    return {"tree": tree, "root": module_root, "func_roots": func_roots,
            "n_nodes": n_nodes}


# ===========================================================================
# (2) THE MECHANICAL AST->TERM EMITTER — the FIXED node-type -> Term-type map,
# the SAME for every faculty. Walks the INGESTED AST-GRAPH (the substrate AstNodes)
# and composes a native Term-tree (raw Term-JSON dicts the Rust evaluator ingests
# via term_from_json — the SAME path order_n_concepts' composed Terms take).
#
# THE MAP (node-type -> Term-type), fixed for all faculties:
#   BinOp:Add  -> Plus        BinOp:Sub  -> Minus     BinOp:Mult -> Times
#   BinOp:Div  -> Div         BinOp:FloorDiv -> Div   BinOp:Pow  -> Pow
#   BinOp:BitAnd/BitOr/BitXor -> matching native bitwise Term (concrete i64 gate)
#   UnaryOp:USub -> Neg       Constant   -> Lit       Name       -> Var
#   Call(<held-leaf>, args)        -> UseTool (the held leaf, Rust dispatch)
#   Call(sum, [GeneratorExp/...])  -> Sum  (the alternating-fold over range)
#   Call(<another faculty>, args)  -> that faculty's already-emitted Term-tree
#                                     (the recursive floor: a built core is a leaf)
# ===========================================================================

# the FIXED BinOp map. The SAME for every faculty.
_BINOP = {
    "Add": "Plus", "Sub": "Minus", "Mult": "Times",
    "Div": "Div", "FloorDiv": "Div", "Pow": "Pow", "Mod": "Mod",
    "BitAnd": "BitAnd", "BitOr": "BitOr", "BitXor": "BitXor",
}
# the binary Term-types take (a, b); the variadic take (items,).
_VARIADIC = {"Plus", "Times", "And", "Or"}

# CODE-2: the FIXED unary-op map (USub was the only CODE-1 case; Not is
# additive). SAME shape (an `arg` child) for both, so one dispatch covers it.
_UNARYOP = {"USub": "Neg", "Not": "Not"}

# CODE-2: the FIXED Compare-op map (ast.Compare.ops element type -> Term
# type). Is/IsNot have no faithful Term (identity != our value equality) and
# are left as a named residual rather than approximated.
_COMPAREOP = {"Eq": "Eq", "NotEq": "Eq", "Lt": "Lt", "LtE": "Lte",
             "Gt": "Gt", "GtE": "Gte"}

# CODE-2: the FIXED AugAssign/accumulate-BinOp -> Term map (the accumulation
# construction's per-step operator). A strict subset of _BINOP (only the
# operators that make sense as a running accumulator combinator).
_ACCUMOP = dict(_BINOP)


class EmitError(Exception):
    """The mechanical map cannot translate this AST node type — the named residual
    (un-translatable Python / a missing held Term-variant)."""


class AstTermEmitter:
    """The agent's graph machinery applying the FIXED AST->Term map over an ingested
    AST-graph. `held_leaves` = the leaf-quantity names whose Call maps to a held
    UseTool (e.g. {'betti_number': 'betti'}). `faculties` = names of OTHER emitted
    faculties whose Call splices their built Term-tree (the recursive floor).
    When a complete module root is supplied, a narrow module-scope index also
    permits unique integer literals and bounded expansion of pure local helpers;
    arbitrary module execution and unbounded/dynamic lookup remain residuals."""

    def __init__(self, substrate, *, held_leaves: Dict[str, str],
                 faculties: Optional[Dict[str, "AstTermEmitter"]] = None,
                 range_bind: Optional[Dict[str, int]] = None,
                 input_types: Optional[Dict[str, str]] = None,
                 input_values: Optional[Dict[str, Any]] = None,
                 module_root: Optional[int] = None):
        self.s = substrate
        self.held_leaves = dict(held_leaves)
        self.faculties = dict(faculties or {})
        # concrete integer binds for any range(...) upper bound the genexp ranges
        # over (the iteration domain materialises to a SetT of Lits). Mechanical.
        self.range_bind = dict(range_bind or {})
        # Concrete call-site type names are used only as a refusal gate for
        # operations whose Python semantics require a specific input type.
        self.input_types = dict(input_types or {})
        self.input_values = dict(input_values or {})
        self.module_root = module_root
        self.module_constants: Dict[str, int] = {}
        self.module_functions: Dict[str, int] = {}
        self._ambiguous_module_names: set[str] = set()
        self._bound_names: set[str] = set()
        self._name_terms: Dict[str, Dict[str, Any]] = {}
        self._name_types: Dict[str, Optional[str]] = {}
        self._name_values: Dict[str, Any] = {}
        self._module_helper_stack: List[str] = []
        self._max_module_helper_depth = 4
        self.parts: List[str] = []     # the Term-types the emitter produced (provenance)
        self.leaf_calls: List[str] = []
        self._index_module_scope()

    # ---- the ingested-graph accessors (read the AstNode substrate nodes) ----

    def _attrs(self, nid: int) -> Dict[str, Any]:
        return self.s.node(nid)["attrs"]

    def _children(self, nid: int) -> List[int]:
        return list(self.s.neighbours(nid, "child"))

    def _child_by_field(self, nid: int, field: str, index: int = -1) -> Optional[int]:
        for c in self._children(nid):
            a = self._attrs(c)
            if a.get("child_field") == field and a.get("child_index") == index:
                return c
        return None

    def _children_of_field(self, nid: int, field: str) -> List[int]:
        out = [(self._attrs(c).get("child_index", -1), c)
               for c in self._children(nid)
               if self._attrs(c).get("child_field") == field]
        out.sort()
        return [c for _, c in out]

    def _index_module_scope(self) -> None:
        """Index unique top-level integer literals and undecorated function defs.

        Any duplicate/reassignment or dynamic top-level write makes that name
        unavailable. This deliberately favors a named residual over guessing
        which module binding Python leaves visible at a call site.
        """
        if self.module_root is None:
            return

        seen: set[str] = set()
        dynamic_scope = False

        def invalidate(name: Optional[str]) -> None:
            if not name:
                return
            self.module_constants.pop(name, None)
            self.module_functions.pop(name, None)
            self._ambiguous_module_names.add(name)
            seen.add(name)

        def bind(name: Optional[str], *, kind: str, node: int) -> None:
            if not name:
                return
            if name in seen or dynamic_scope:
                invalidate(name)
                return
            seen.add(name)
            if kind == "constant":
                self.module_constants[name] = self._attrs(node).get("value")
            elif kind == "function":
                self.module_functions[name] = node
            else:
                invalidate(name)

        def stored_names(node: int) -> set[str]:
            result: set[str] = set()

            def walk(current: int, *, top: bool = False) -> None:
                attrs = self._attrs(current)
                kind = attrs.get("ast_type", "")
                if kind in ("FunctionDef", "AsyncFunctionDef", "ClassDef", "Lambda") and not top:
                    return
                if kind == "Name":
                    ctx = self._child_by_field(current, "ctx")
                    ctx_type = self._attrs(ctx).get("ast_type") if ctx is not None else None
                    if ctx_type in ("Store", "Del") and attrs.get("id"):
                        result.add(attrs["id"])
                for child in self._children(current):
                    walk(child)

            walk(node, top=True)
            return result

        for item in self._children_of_field(self.module_root, "body"):
            attrs = self._attrs(item)
            kind = attrs.get("ast_type")
            if kind == "Assign":
                targets = self._children_of_field(item, "targets")
                value = self._child_by_field(item, "value")
                value_attrs = self._attrs(value) if value is not None else {}
                if (len(targets) == 1 and self._attrs(targets[0]).get("ast_type") == "Name"
                        and value_attrs.get("ast_type") == "Constant"
                        and type(value_attrs.get("value")) is int):
                    bind(self._attrs(targets[0]).get("id"), kind="constant", node=value)
                    continue
                for name in stored_names(item):
                    invalidate(name)
            elif kind == "FunctionDef":
                bind(attrs.get("name"), kind="function", node=item)
            elif kind == "ClassDef":
                invalidate(attrs.get("name"))
            elif kind in ("Import", "ImportFrom"):
                aliases = self._children_of_field(item, "names")
                for alias in aliases:
                    alias_attrs = self._attrs(alias)
                    import_name = alias_attrs.get("name", "")
                    alias_name = alias_attrs.get("asname")
                    if import_name == "*":
                        dynamic_scope = True
                        for existing in tuple(seen):
                            invalidate(existing)
                        self.module_constants.clear()
                        self.module_functions.clear()
                    else:
                        bound_name = alias_name or (import_name.split(".", 1)[0]
                                                    if kind == "Import" else import_name)
                        invalidate(bound_name)
            else:
                for name in stored_names(item):
                    invalidate(name)

    def _known_type(self, nid: int) -> Optional[str]:
        attrs = self._attrs(nid)
        kind = attrs.get("ast_type", "")
        if kind == "Constant":
            return type(attrs.get("value")).__name__
        if kind == "Name":
            name = attrs.get("id")
            if name in self._name_types:
                return self._name_types[name]
            if name in self._bound_names:
                return self.input_types.get(name)
            if name in self.module_constants:
                return "int"
        return None

    def _known_int_value(self, nid: int) -> Optional[int]:
        attrs = self._attrs(nid)
        kind = attrs.get("ast_type", "")
        if kind == "Constant":
            value = attrs.get("value")
            return value if type(value) is int else None
        if kind == "Name":
            name = attrs.get("id")
            if name in self._name_values:
                value = self._name_values[name]
                return value if type(value) is int else None
            if name in self._bound_names:
                value = self.input_values.get(name)
                return value if type(value) is int else None
            if name in self.module_constants:
                return self.module_constants[name]
        return None

    def _require_bounded_integer_bitwise(self, nid: int) -> None:
        """Require exact Python ints representable in the native signed-i64 domain."""
        if self._known_type(nid) != "int":
            raise EmitError("bitwise Term emission requires an exact int operand")
        value = self._known_int_value(nid)
        if value is None or value < -(1 << 63) or value > (1 << 63) - 1:
            raise EmitError("bitwise Term emission requires a concrete signed-i64 operand")

    def prepare_function(self, func_root: int) -> None:
        """Establish parameter scope before any direct AST-node emission."""
        args_node = self._child_by_field(func_root, "args")
        self._bound_names = ({self._attrs(arg).get("arg")
                              for arg in self._children_of_field(args_node, "args")}
                             if args_node is not None else set())
        self._name_terms = {}
        self._name_types = {}
        self._name_values = {}

    # ---- the entry: emit a function's compute-core (its single Return) ----

    def emit_function(self, func_root: int) -> Dict[str, Any]:
        """Emit the native Term-tree for a FunctionDef AstNode: locate its single
        `Return` body node and emit that expression. Returns the Term-JSON dict."""
        self.prepare_function(func_root)
        body = self._children_of_field(func_root, "body")
        ret = None
        for b in body:
            bt = self._attrs(b).get("ast_type")
            if bt == "Return":
                ret = b
                break
            # ANY statement before the Return (assignment, loop, branch, comprehension
            # target, mutation, ...) means the compute-core is NOT a single pure
            # expression. The fixed map would SILENTLY emit only the returned Var and
            # DROP the rest (the loop in `collapse_runs` -> a bare `Var out`), which is a
            # confidently-wrong move, not a translation. Refuse with a named residual:
            # complex Python belongs in a graph Rule (a decision) or a new primitive
            # (Layer B), never a lossy Term.
            raise EmitError(
                f"compute-core is not a pure single-Return expression: statement "
                f"{bt!r} precedes the Return. Complex Python (loops/branches/"
                f"comprehensions/mutation) is the named residual — move it as a graph "
                f"Rule or a new primitive, not a lossy Term-tree.")
        if ret is None:
            raise EmitError("the compute-core has no single Return expression")
        value = self._child_by_field(ret, "value")
        if value is None:
            raise EmitError("the Return has no value expression")
        return self.emit_term(value)

    # ---- THE FIXED MAP — node-type -> Term-type ----

    def emit_term(self, nid: int) -> Dict[str, Any]:
        a = self._attrs(nid)
        t = a.get("ast_type", "")

        # Constant -> Lit
        if t == "Constant":
            self.parts.append("Lit")
            return {"type": "Lit", "value": a.get("value")}

        # Name -> Var (the bound iteration variable / parameter)
        if t == "Name":
            name = a.get("id")
            if name in self._name_terms:
                import copy
                self.parts.append("Bound")
                return copy.deepcopy(self._name_terms[name])
            if name in self._bound_names:
                self.parts.append("Var")
                return {"type": "Var", "name": name}
            if name in self._ambiguous_module_names:
                raise EmitError(f"module name {name!r} has an ambiguous or dynamic binding")
            if name in self.module_constants:
                self.parts.append("Lit")
                return {"type": "Lit", "value": self.module_constants[name]}
            self.parts.append("Var")
            return {"type": "Var", "name": name}

        # UnaryOp:<op> -> Neg / Not (CODE-1 had only USub; Not is additive,
        # same one-child `arg` shape so one dispatch covers both).
        if t.startswith("UnaryOp:"):
            opname = t.split(":", 1)[1]
            term_t = _UNARYOP.get(opname)
            if term_t is None:
                raise EmitError(f"no Term for UnaryOp {opname!r}")
            operand = self._child_by_field(nid, "operand")
            self.parts.append(term_t)
            return {"type": term_t, "arg": self.emit_term(operand)}

        # BinOp:<op> -> the mapped binary/variadic Term
        if t.startswith("BinOp:"):
            opname = t.split(":", 1)[1]
            term_t = _BINOP.get(opname)
            if term_t is None:
                raise EmitError(f"no Term for BinOp {opname!r}")
            left = self._child_by_field(nid, "left")
            right = self._child_by_field(nid, "right")
            if opname in ("BitAnd", "BitOr", "BitXor"):
                self._require_bounded_integer_bitwise(left)
                self._require_bounded_integer_bitwise(right)
            self.parts.append(term_t)
            if term_t in _VARIADIC:
                return {"type": term_t,
                        "items": [self.emit_term(left), self.emit_term(right)]}
            return {"type": term_t,
                    "a": self.emit_term(left), "b": self.emit_term(right)}

        # CODE-2: BoolOp:<And|Or> -> And/Or (variadic, values field).
        if t.startswith("BoolOp:"):
            opname = t.split(":", 1)[1]
            term_t = {"And": "And", "Or": "Or"}.get(opname)
            if term_t is None:
                raise EmitError(f"no Term for BoolOp {opname!r}")
            values = self._children_of_field(nid, "values")
            if len(values) < 2:
                raise EmitError("BoolOp has fewer than 2 operands")
            self.parts.append(term_t)
            return {"type": term_t, "items": [self.emit_term(v) for v in values]}

        # CODE-2: Compare (incl. chained a<b<c -> And of each pairwise Term).
        if t == "Compare":
            return self._emit_compare(nid)

        # CODE-2: IfExp -> IfThenElse (a Python ternary).
        if t == "IfExp":
            test = self._child_by_field(nid, "test")
            body = self._child_by_field(nid, "body")
            orelse = self._child_by_field(nid, "orelse")
            self.parts.append("IfThenElse")
            return {"type": "IfThenElse", "cond": self.emit_term(test),
                    "then": self.emit_term(body), "other": self.emit_term(orelse)}

        # Call -> a held leaf (UseTool), a sum-fold (Sum), or a faculty sub-tree.
        if t == "Call":
            return self._emit_call(nid)

        raise EmitError(f"un-translatable AST node type {t!r} "
                        f"(the named residual: the fixed map has no Term for it. "
                        f"NOTE for Attribute/Subscript (the FIELD construction): "
                        f"deliberately NOT mapped to the held `Attr` Term -- `Attr` "
                        f"reads a SUBSTRATE GRAPH NODE's attrs dict by key, a "
                        f"different domain than Python's general object.attribute "
                        f"access over an arbitrary argument value. Mapping it would "
                        f"be an approximation, not a translation -- the honest "
                        f"boundary this project requires. FIELD stays READ (the "
                        f"construction recognises the shape) but not Term-evaluable.)")

    # ---- CODE-2: Compare, incl. chained comparisons ----

    def _emit_compare(self, nid: int) -> Dict[str, Any]:
        """Compare(left, ops, comparators) -> the mapped comparator Term; a
        CHAINED comparison (`a < b < c`, len(ops) > 1) -> And of each
        pairwise Term (Python's own chained-comparison semantics: `a<b<c`
        means `a<b and b<c`, never a transitive single relation). NotEq ->
        Not(Eq). In/NotIn -> the held `In` Term (sound: Python's `in` and
        the Term's membership test are the SAME operation, unlike Attr's
        mismatch above). Is/IsNot have no faithful Term (identity vs value
        equality) and raise -- a genuine, not lazy, residual."""
        left = self._child_by_field(nid, "left")
        ops = self._children_of_field(nid, "ops")
        comparators = self._children_of_field(nid, "comparators")
        if not ops or len(ops) != len(comparators):
            raise EmitError("Compare has malformed ops/comparators")
        pairs = []
        prev = left
        for op_nid, comp_nid in zip(ops, comparators):
            pairs.append((self._attrs(op_nid).get("ast_type"), prev, comp_nid))
            prev = comp_nid
        terms = []
        for opname, a_nid, b_nid in pairs:
            a_term = self.emit_term(a_nid)
            b_term = self.emit_term(b_nid)
            if opname == "In":
                self.parts.append("In")
                terms.append({"type": "In", "member": a_term, "container": b_term})
            elif opname == "NotIn":
                self.parts.append("Not(In)")
                terms.append({"type": "Not",
                              "arg": {"type": "In", "member": a_term, "container": b_term}})
            elif opname == "NotEq":
                self.parts.append("Not(Eq)")
                terms.append({"type": "Not",
                              "arg": {"type": "Eq", "a": a_term, "b": b_term}})
            elif opname in _COMPAREOP:
                term_t = _COMPAREOP[opname]
                self.parts.append(term_t)
                terms.append({"type": term_t, "a": a_term, "b": b_term})
            else:
                raise EmitError(f"no Term for comparison operator {opname!r} "
                                f"(Is/IsNot are the named residual: identity != "
                                f"value equality, never approximated)")
        if len(terms) == 1:
            return terms[0]
        self.parts.append("And")
        return {"type": "And", "items": terms}

    def _emit_call(self, nid: int) -> Dict[str, Any]:
        func = self._child_by_field(nid, "func")
        fname = self._attrs(func).get("id") if func is not None else None
        args = self._children_of_field(nid, "args")

        # sum(<generator over range>) -> the held Sum-fold (the alternating sum).
        if fname == "sum":
            return self._emit_sum_fold(args)

        # a held leaf-quantity Call (betti_number, ...) -> the held UseTool leaf.
        if fname in self.held_leaves:
            tool = self.held_leaves[fname]
            self.leaf_calls.append(fname)
            self.parts.append("UseTool")
            # the leaf's arg that VARIES (the index k) is the last arg; the held
            # handler closes over the object (complex). We pass the non-object args
            # (those that are not the bound object name) as UseTool args. The object
            # arg (the complex) is bound in the handler, so only the index crosses.
            tool_args = [self.emit_term(c) for c in args
                         if self._attrs(c).get("ast_type") != "Name"
                         or self._attrs(c).get("id") != self._object_param()]
            return {"type": "UseTool", "tool": tool, "args": tool_args}

        # a Call to ANOTHER emitted faculty (the recursive floor) -> splice its tree.
        if fname in self.faculties:
            self.parts.append(f"<{fname}>")
            return self.faculties[fname].last_term

        # Expand only bounded, pure, module-local helpers. This composes the
        # helper's ingested AST graph into the caller's native Term without
        # executing arbitrary Python.
        if fname in self.module_functions:
            return self._emit_module_helper(fname, args, nid)

        raise EmitError(f"Call to {fname!r} is neither a held leaf, the sum-fold, "
                        f"nor an emitted faculty (un-translatable: the held DSL "
                        f"lacks a leaf for it — the named residual)")

    def _emit_module_helper(self, name: str, args: List[int], call_nid: int) -> Dict[str, Any]:
        if self._children_of_field(call_nid, "keywords"):
            raise EmitError("module helper expansion refuses keyword arguments")
        if name in self._module_helper_stack:
            raise EmitError(f"recursive module helper {name!r} is outside the bounded fragment")
        if len(self._module_helper_stack) >= self._max_module_helper_depth:
            raise EmitError("module helper expansion exceeded the fixed depth limit")

        fn_root = self.module_functions[name]
        if self._children_of_field(fn_root, "decorator_list"):
            raise EmitError("decorated module helpers are outside the bounded fragment")
        args_node = self._child_by_field(fn_root, "args")
        if args_node is None:
            raise EmitError("module helper has no explicit argument record")
        positional_only = self._children_of_field(args_node, "posonlyargs")
        parameters = self._children_of_field(args_node, "args")
        kwonly = self._children_of_field(args_node, "kwonlyargs")
        defaults = (self._children_of_field(args_node, "defaults")
                    + self._children_of_field(args_node, "kw_defaults"))
        if positional_only or kwonly or defaults:
            raise EmitError("module helper requires undecorated required positional parameters")
        if (self._child_by_field(args_node, "vararg") is not None
                or self._child_by_field(args_node, "kwarg") is not None):
            raise EmitError("variadic module helpers are outside the bounded fragment")
        if len(args) != len(parameters):
            raise EmitError("module helper call arity does not match its positional signature")

        body = self._children_of_field(fn_root, "body")
        if body and self._attrs(body[0]).get("ast_type") == "Expr":
            doc_value = self._child_by_field(body[0], "value")
            doc_attrs = self._attrs(doc_value) if doc_value is not None else {}
            if doc_attrs.get("ast_type") == "Constant" and isinstance(doc_attrs.get("value"), str):
                body = body[1:]
        if len(body) != 1 or self._attrs(body[0]).get("ast_type") != "Return":
            raise EmitError("module helper must contain one return after its docstring")
        return_value = self._child_by_field(body[0], "value")
        if return_value is None:
            raise EmitError("module helper return has no value")

        self._module_helper_stack.append(name)
        try:
            arg_types = [self._known_type(arg) for arg in args]
            arg_values = [self._known_int_value(arg) for arg in args]
            arg_terms = [self.emit_term(arg) for arg in args]
            old_terms, old_types, old_values, old_bound = (
                self._name_terms, self._name_types, self._name_values, self._bound_names)
            self._name_terms = dict(old_terms)
            self._name_types = dict(old_types)
            self._name_values = dict(old_values)
            self._bound_names = set(old_bound)
            try:
                for parameter, term, typ, value in zip(parameters, arg_terms, arg_types, arg_values):
                    parameter_name = self._attrs(parameter).get("arg")
                    if not parameter_name:
                        raise EmitError("module helper parameter has no name")
                    self._name_terms[parameter_name] = term
                    self._name_types[parameter_name] = typ
                    self._name_values[parameter_name] = value
                    self._bound_names.add(parameter_name)
                return self.emit_term(return_value)
            finally:
                self._name_terms, self._name_types, self._name_values, self._bound_names = (
                    old_terms, old_types, old_values, old_bound)
        finally:
            self._module_helper_stack.pop()

    # the object parameter name (the complex / presentation the leaf closes over).
    _object_param_name = "complex"

    def _object_param(self) -> str:
        return self._object_param_name

    def _emit_sum_fold(self, args: List[int]) -> Dict[str, Any]:
        """sum(<elt> for <var> in range(<hi>)) -> Sum{source: SetT[Lit 0..hi-1],
        var_name: <var>, value: emit(<elt>)}. The range upper bound materialises to
        a SetT of Lits from the concrete bind (mechanical). The held alternating-fold
        the euler compute-core is."""
        if len(args) != 1 or self._attrs(args[0]).get("ast_type") != "GeneratorExp":
            raise EmitError("sum(...) is not over a single generator expression")
        gen = args[0]
        elt = self._child_by_field(gen, "elt")
        comps = self._children_of_field(gen, "generators")
        if len(comps) != 1:
            raise EmitError("the sum genexp has != 1 comprehension clause")
        comp = comps[0]
        target = self._child_by_field(comp, "target")
        var_name = self._attrs(target).get("id")
        it = self._child_by_field(comp, "iter")
        domain = self._emit_range_domain(it)
        self.parts.append("Sum")
        return {"type": "Sum",
                "source": {"type": "SetT", "items": domain},
                "var_name": var_name,
                "value": self.emit_term(elt)}

    def _emit_range_domain(self, it_nid: int) -> List[Dict[str, Any]]:
        """range(<hi>) -> the materialised [Lit 0 .. Lit hi-1]. <hi> is an int
        expression over bound names (e.g. n + 1); we evaluate it against range_bind
        (the concrete iteration bind) — a mechanical materialisation of the
        iteration domain, NOT a decision."""
        if self._attrs(it_nid).get("ast_type") != "Call":
            raise EmitError("the genexp iterator is not a range(...) call")
        func = self._child_by_field(it_nid, "func")
        if self._attrs(func).get("id") != "range":
            raise EmitError("the genexp iterator is not range(...)")
        rargs = self._children_of_field(it_nid, "args")
        hi = self._eval_int(rargs[-1])
        return [{"type": "Lit", "value": k} for k in range(hi)]

    def _eval_int(self, nid: int) -> int:
        """Evaluate a small integer AST expression (Constant / Name in range_bind /
        BinOp Add/Sub/Mult) for the range upper bound. Mechanical materialisation."""
        a = self._attrs(nid)
        t = a.get("ast_type", "")
        if t == "Constant":
            return int(a.get("value"))
        if t == "Name":
            nm = a.get("id")
            if nm in self.range_bind:
                return int(self.range_bind[nm])
            raise EmitError(f"range bound name {nm!r} has no concrete bind")
        if t.startswith("BinOp:"):
            op = t.split(":", 1)[1]
            l = self._eval_int(self._child_by_field(nid, "left"))
            r = self._eval_int(self._child_by_field(nid, "right"))
            if op == "Add":
                return l + r
            if op == "Sub":
                return l - r
            if op == "Mult":
                return l * r
        raise EmitError(f"cannot materialise range bound from {t!r}")

    # =======================================================================
    # CODE-2: STATEMENT-SEQUENCE EMISSION — a function body wider than one
    # pure-expression Return. Two RECOGNISED shapes (Let-chain,
    # accumulation-Fold); every other multi-statement shape is a named
    # residual raised by the caller's own dispatch (domains/code_reading.py),
    # not silently approximated here.
    # =======================================================================

    def body_statements(self, func_root: int) -> List[int]:
        """The function's body statement AstNode ids, with a leading
        docstring statement (an `Expr` whose sole child is a string
        `Constant`) peeled off -- metadata, not code, the SAME peel
        `code_reading._single_return_value` already does for the
        single-expression path, exposed here so every multi-statement
        recognizer/emitter (this class + code_reading's skeleton builder)
        shares ONE peel instead of three copies of it."""
        body = self._children_of_field(func_root, "body")
        if body and self._attrs(body[0]).get("ast_type") == "Expr":
            val = self._child_by_field(body[0], "value")
            if (val is not None and self._attrs(val).get("ast_type") == "Constant"
                    and isinstance(self._attrs(val).get("value"), str)):
                body = body[1:]
        return body

    def emit_let_chain(self, func_root: int) -> Dict[str, Any]:
        """A straight-line body of simple `Name = <pure expr>` assignments
        followed by a single `Return <expr>` emits as NESTED Let bindings:
        each statement becomes the BODY of the previous one, so statement
        order == nesting order. Sequential REBINDING of the same name (`x =
        1; x = x + 1; return x`) is honest shadowing, not mutation: a later
        Let's `value` is evaluated inside the earlier Let's already-pushed
        env (the SAME env `body` sees), so it observes the prior binding --
        exactly Python's own sequential-rebind semantics, verified by the
        native evaluator's existing Let (`v = value.evaluate(env)`; new_env
        binds `name`; `body.evaluate(new_env)`).

        THE BOUNDARY (named EmitError, never silent loss): a tuple/list-
        unpacking target, a multi-target assignment (`a = b = expr`), an
        attribute/subscript store target, or ANY non-Assign/Return statement
        (AugAssign outside the accumulation shape, For/While/Try/With, ...)
        refuses by name."""
        stmts = self.body_statements(func_root)
        if len(stmts) < 2:
            raise EmitError("not a multi-statement let-chain body (need at "
                            "least one assignment followed by a Return)")
        *assigns, last = stmts
        if self._attrs(last).get("ast_type") != "Return":
            raise EmitError(f"a let-chain body must end in a Return, found "
                            f"{self._attrs(last).get('ast_type')!r} -- named "
                            f"residual, not silently ignored")
        bindings: List[Tuple[str, int]] = []
        for a in assigns:
            at = self._attrs(a).get("ast_type")
            if at != "Assign":
                raise EmitError(
                    f"non-assignment statement {at!r} in a straight-line body -- "
                    f"named residual: only plain `Name = expr` assignments chain "
                    f"into Let bindings (AugAssign/For/While/Try/With are the "
                    f"honest boundary, never approximated as a Let)")
            targets = self._children_of_field(a, "targets")
            if len(targets) != 1:
                raise EmitError("a multi-target assignment (`a = b = expr`) is "
                                f"the named residual, not a Let-chain")
            tgt = targets[0]
            ttype = self._attrs(tgt).get("ast_type")
            if ttype != "Name":
                raise EmitError(
                    f"assignment target is {ttype!r}, not a plain Name -- "
                    f"tuple/list-unpacking and attribute/subscript stores are "
                    f"the named residual, never silently dropped")
            value_nid = self._child_by_field(a, "value")
            if value_nid is None:
                raise EmitError("assignment has no value expression")
            bindings.append((self._attrs(tgt).get("id"), value_nid))
        ret_val = self._child_by_field(last, "value")
        if ret_val is None:
            raise EmitError("the Return has no value expression")
        # innermost-out: the Return expr is the deepest body; each binding
        # wraps around it in REVERSE statement order so the FIRST assignment
        # ends up OUTERMOST (statement order == nesting order).
        body_term = self.emit_term(ret_val)
        for name, value_nid in reversed(bindings):
            self.parts.append("Let")
            body_term = {"type": "Let", "name": name,
                        "value": self.emit_term(value_nid), "body": body_term}
        return body_term

    def emit_accumulation(self, func_root: int) -> Dict[str, Any]:
        """The accumulation idiom: `acc = <init>` ; `for x in <iterable>:
        acc += <expr>` (or `acc = acc OP expr`) ; `return acc` emits as a
        native `Fold(source, var_name=x, acc_name=acc, init, body=OP(Var
        acc, expr))`. STRUCTURAL recognition here is independent of (and
        stricter than) the statement-skeleton construction recognition in
        domains/code_reading.py -- exactly CODE-1's "Term emission is a
        separate, stricter concern" precedent: a shape the skeleton
        recognises as `accumulation_loop` may still honestly abstain here
        (e.g. the init/iterable involves a Call the fixed map can't
        translate).

        SCOPE (named residual outside it): the iterable is a bare Name (a
        list/tuple argument -- Fold's `source` is `Var(name)`, evaluated
        against whatever collection Value the caller binds it to) or
        `range(<int-bindable expr>)` (materialised via the SAME
        `_eval_int` bound-evaluation the Sum-fold already uses, into an
        ORDER-PRESERVING `Vec` literal -- NOT `SetT`/frozenset, because a
        non-commutative accumulate op (Minus/Div/Pow/Mod) needs the
        original iteration order, unlike the pre-existing Sum-fold's
        domain which is always summed, commutatively). The for-loop body
        must be EXACTLY one accumulate statement; an early break/continue/
        condition inside the loop is a genuinely different shape and
        honestly abstains rather than being partially translated."""
        stmts = self.body_statements(func_root)
        if len(stmts) != 3:
            raise EmitError(f"accumulation body must be exactly [init "
                            f"assign, for loop, return] (found {len(stmts)} "
                            f"statements)")
        init_stmt, for_stmt, ret_stmt = stmts

        if self._attrs(init_stmt).get("ast_type") != "Assign":
            raise EmitError("accumulation body must open with an "
                            "accumulator init assignment")
        init_targets = self._children_of_field(init_stmt, "targets")
        if len(init_targets) != 1 or self._attrs(init_targets[0]).get("ast_type") != "Name":
            raise EmitError("accumulator init must assign a plain Name "
                            "(not a tuple-unpack / attribute / subscript)")
        acc_name = self._attrs(init_targets[0]).get("id")
        init_val = self._child_by_field(init_stmt, "value")
        if init_val is None:
            raise EmitError("accumulator init has no value expression")

        if self._attrs(for_stmt).get("ast_type") != "For":
            raise EmitError("accumulation body's second statement must be a For loop")
        for_target = self._child_by_field(for_stmt, "target")
        if self._attrs(for_target).get("ast_type") != "Name":
            raise EmitError("the for-loop target must be a plain Name -- "
                            "tuple-unpacking the loop variable is the named "
                            "residual")
        var_name = self._attrs(for_target).get("id")
        for_body = self._children_of_field(for_stmt, "body")
        if len(for_body) != 1:
            raise EmitError("the for-loop body must be EXACTLY one "
                            "accumulate statement -- an early break/continue/"
                            "condition inside the loop is the named residual, "
                            "never partially translated")
        loop_stmt = for_body[0]
        lt = self._attrs(loop_stmt).get("ast_type", "")
        op_term_type = None
        rhs_nid = None
        if lt.startswith("AugAssign:"):
            tgt = self._child_by_field(loop_stmt, "target")
            if self._attrs(tgt).get("ast_type") != "Name" or \
                    self._attrs(tgt).get("id") != acc_name:
                raise EmitError("the loop's AugAssign target does not match "
                                "the accumulator")
            op_term_type = _ACCUMOP.get(lt.split(":", 1)[1])
            rhs_nid = self._child_by_field(loop_stmt, "value")
        elif lt == "Assign":
            tgts = self._children_of_field(loop_stmt, "targets")
            if len(tgts) != 1 or self._attrs(tgts[0]).get("ast_type") != "Name" \
                    or self._attrs(tgts[0]).get("id") != acc_name:
                raise EmitError("the loop's assignment target does not match "
                                "the accumulator")
            rhs = self._child_by_field(loop_stmt, "value")
            rhs_type = self._attrs(rhs).get("ast_type", "")
            if not rhs_type.startswith("BinOp:"):
                raise EmitError("the loop assigns the accumulator to a "
                                "non-binary expression -- named residual, not "
                                "the `acc = acc OP expr` accumulation shape")
            left = self._child_by_field(rhs, "left")
            if self._attrs(left).get("ast_type") != "Name" or \
                    self._attrs(left).get("id") != acc_name:
                raise EmitError("the loop's `acc = acc OP expr` form must have "
                                "the accumulator as the LEFT operand")
            op_term_type = _ACCUMOP.get(rhs_type.split(":", 1)[1])
            rhs_nid = self._child_by_field(rhs, "right")
        else:
            raise EmitError(f"the for-loop body statement {lt!r} is not an "
                            f"accumulate step (AugAssign or `acc = acc OP "
                            f"expr`) -- named residual, an early-break/"
                            f"condition/other loop body honestly abstains "
                            f"rather than being approximated")
        if op_term_type is None:
            raise EmitError(f"no Term for accumulate operator in {lt!r}")

        if self._attrs(ret_stmt).get("ast_type") != "Return":
            raise EmitError("accumulation body's third statement must be a Return")
        ret_val = self._child_by_field(ret_stmt, "value")
        if ret_val is None or self._attrs(ret_val).get("ast_type") != "Name" \
                or self._attrs(ret_val).get("id") != acc_name:
            raise EmitError("the Return must return the accumulator by name")

        iter_nid = self._child_by_field(for_stmt, "iter")
        source_term = self._emit_iterable(iter_nid)
        init_term = self.emit_term(init_val)
        acc_t = {"type": "Var", "name": acc_name}
        rhs_term = self.emit_term(rhs_nid)
        if op_term_type in _VARIADIC:
            body_term = {"type": op_term_type, "items": [acc_t, rhs_term]}
        else:
            body_term = {"type": op_term_type, "a": acc_t, "b": rhs_term}
        self.parts.append("Fold")
        return {"type": "Fold", "source": source_term, "var_name": var_name,
                "acc_name": acc_name, "init": init_term, "body": body_term}

    # ---- WAVE 2: BRANCHING RETURN STATEMENTS -- `if cond: return a`
    # [`elif ...: return b`]* `else: return c`, statement-grain, emits as
    # NESTED `IfThenElse` Terms (the SAME Term type CODE-1's ternary
    # `IfExp` path already produces -- the meaning of a branching return is
    # identical whether spelled as an if/elif/else block or a ternary
    # chain, so this reuses that Term shape rather than inventing a new
    # one; only the WRITE-side surface differs, see code_writing.py's
    # `branch_style`). ----
    def is_return_chain(self, if_nid: int) -> bool:
        """True iff `if_nid` (an `If` AstNode) is EXHAUSTIVELY a return
        chain: its `body` is exactly one `Return` statement, and its
        `orelse` is either exactly one `Return` (the terminal `else`) or
        exactly one nested `If` that is ITSELF a return chain (an
        `elif`). Anything else -- a non-Return branch statement, more
        than one statement in a branch, or a fall-through with NO `else`
        at all (`orelse` empty) -- is honestly NOT this shape; the caller
        refuses by name rather than partially translating a branch that
        does not return."""
        body = self._children_of_field(if_nid, "body")
        if len(body) != 1 or self._attrs(body[0]).get("ast_type") != "Return":
            return False
        orelse = self._children_of_field(if_nid, "orelse")
        if len(orelse) != 1:
            return False
        ot = self._attrs(orelse[0]).get("ast_type")
        if ot == "Return":
            return True
        if ot == "If":
            return self.is_return_chain(orelse[0])
        return False

    def _emit_if_chain(self, if_nid: int) -> Dict[str, Any]:
        """Recursive Term builder over an already-validated (`is_return_chain`)
        If/elif/else return chain: each level becomes one `IfThenElse`,
        nested in the `other` slot for an `elif`."""
        cond_nid = self._child_by_field(if_nid, "test")
        cond_term = self.emit_term(cond_nid)
        then_body = self._children_of_field(if_nid, "body")
        then_ret = self._child_by_field(then_body[0], "value")
        if then_ret is None:
            raise EmitError("a branch's Return has no value expression")
        then_term = self.emit_term(then_ret)
        orelse = self._children_of_field(if_nid, "orelse")
        ot = self._attrs(orelse[0]).get("ast_type")
        if ot == "If":
            other_term = self._emit_if_chain(orelse[0])
        else:
            other_ret = self._child_by_field(orelse[0], "value")
            if other_ret is None:
                raise EmitError("a branch's Return has no value expression")
            other_term = self.emit_term(other_ret)
        self.parts.append("IfThenElse")
        return {"type": "IfThenElse", "cond": cond_term, "then": then_term,
               "other": other_term}

    def emit_branching_return(self, func_root: int) -> Dict[str, Any]:
        """Emit the native Term-tree for a body that is EXACTLY one
        exhaustive if/elif/else return chain (`code_reading.
        _multi_stmt_skeleton_and_kind`'s `branching_return` kind already
        validated the shape via `is_return_chain`; this re-validates
        independently, the same "Term emission is a separate, stricter
        concern" precedent `emit_let_chain`/`emit_accumulation` follow)."""
        stmts = self.body_statements(func_root)
        if len(stmts) != 1 or self._attrs(stmts[0]).get("ast_type") != "If":
            raise EmitError("a branching-return body must be EXACTLY one "
                            "top-level if/elif/else statement")
        if not self.is_return_chain(stmts[0]):
            raise EmitError(
                "the if-chain does not return in EVERY branch (a "
                "non-Return branch statement, or a fall-through with no "
                "final else) -- named residual, never partially translated")
        return self._emit_if_chain(stmts[0])

    def is_string_find_branch(self, func_root: int) -> bool:
        """Recognize exactly `n = arg.find(<literal str>); if n < 0: return x;
        return y` or the corresponding `n == 0` branch. This is a mechanical
        structural predicate; Term emission below separately requires a
        concrete `str` input type and the safe comparison boundary."""
        stmts=self.body_statements(func_root)
        if len(stmts)!=3 or [self._attrs(s).get("ast_type") for s in stmts] != ["Assign","If","Return"]:
            return False
        assign,branch,tail=stmts
        targets=self._children_of_field(assign,"targets")
        if len(targets)!=1 or self._attrs(targets[0]).get("ast_type")!="Name": return False
        target=self._attrs(targets[0]).get("id"); call=self._child_by_field(assign,"value")
        if self._attrs(call).get("ast_type")!="Call": return False
        fn=self._child_by_field(call,"func"); args=self._children_of_field(call,"args")
        if self._attrs(fn).get("ast_type")!="Attribute" or self._attrs(fn).get("attr")!="find" or len(args)!=1: return False
        base=self._child_by_field(fn,"value")
        if self._attrs(base).get("ast_type")!="Name" or self._attrs(args[0]).get("ast_type")!="Constant" or type(self._attrs(args[0]).get("value")) is not str: return False
        if self._children_of_field(call,"keywords"): return False
        test=self._child_by_field(branch,"test")
        if self._attrs(test).get("ast_type")!="Compare": return False
        left=self._child_by_field(test,"left"); ops=self._children_of_field(test,"ops"); comps=self._children_of_field(test,"comparators")
        if len(ops)!=1 or len(comps)!=1 or self._attrs(left).get("ast_type")!="Name" or self._attrs(left).get("id")!=target: return False
        op=self._attrs(ops[0]).get("ast_type")
        if op not in ("Lt","Eq") or self._attrs(comps[0]).get("ast_type")!="Constant" or type(self._attrs(comps[0]).get("value")) is not int or self._attrs(comps[0]).get("value")!=0: return False
        branch_body=self._children_of_field(branch,"body")
        if len(branch_body)!=1 or self._attrs(branch_body[0]).get("ast_type")!="Return" or self._children_of_field(branch,"orelse"): return False
        if self._attrs(tail).get("ast_type")!="Return": return False
        # The byte offset from native StringIndexOf is observationally
        # equivalent to Python's Unicode-code-point offset only for tests of
        # presence (< 0) or start position (== 0); prevent any other use of n.
        ret_values=[self._child_by_field(branch_body[0],"value"),self._child_by_field(tail,"value")]
        if any(v is None for v in ret_values): return False
        def uses_target(nid):
            if self._attrs(nid).get("ast_type")=="Name" and self._attrs(nid).get("id")==target: return True
            return any(uses_target(c) for c in self._children(nid))
        return not any(uses_target(v) for v in ret_values)

    def emit_string_find_branch(self, func_root: int) -> Dict[str, Any]:
        """Lower the validated string-find early-return form to existing
        StringIndexOf + Let + IfThenElse Terms. `find` is emitted only when
        the concrete call binds the receiver to a Python `str`; otherwise
        Python's TypeError could not be preserved by the native operation."""
        if not self.is_string_find_branch(func_root):
            raise EmitError("not the supported string-find early-return shape")
        assign,branch,tail=self.body_statements(func_root)
        target=self._children_of_field(assign,"targets")[0]
        target_name=self._attrs(target).get("id")
        call=self._child_by_field(assign,"value"); fn=self._child_by_field(call,"func")
        base=self._child_by_field(fn,"value"); base_name=self._attrs(base).get("id")
        args_node=self._child_by_field(func_root,"args")
        parameter_names={self._attrs(n).get("arg") for n in self._children_of_field(args_node,"args")} if args_node is not None else set()
        if base_name not in parameter_names:
            raise EmitError("string-find receiver must be a declared function parameter")
        if self.input_types.get(base_name)!="str":
            raise EmitError("string-find lowering requires a concrete str input bind")
        needle=self._children_of_field(call,"args")[0]
        find_term={"type":"StringIndexOf","haystack":{"type":"Var","name":base_name},"needle":{"type":"Lit","value":self._attrs(needle).get("value")}}
        self.parts.extend(["StringIndexOf","Let","IfThenElse"])
        branch_ret=self._children_of_field(branch,"body")[0]
        cond=self.emit_term(self._child_by_field(branch,"test"))
        then=self.emit_term(self._child_by_field(branch_ret,"value"))
        other=self.emit_term(self._child_by_field(tail,"value"))
        return {"type":"Let","name":target_name,"value":find_term,
                "body":{"type":"IfThenElse","cond":cond,"then":then,"other":other}}

    def _emit_iterable(self, it_nid: int) -> Dict[str, Any]:
        """The accumulation loop's iterable: a bare Name (Fold's `source` is
        `Var(name)`) or `range(<int-bindable expr>)` (materialised into an
        ORDER-PRESERVING `Vec` literal via `_eval_int` -- see
        `emit_accumulation`'s docstring for why `Vec`, not `SetT`). Any
        other iterable (a comprehension, a method call, a Subscript, a
        2-arg `zip`/`enumerate`, ...) is the named residual: the
        accumulation construction's documented scope is range(n)/list-arg
        iterables, nothing wider."""
        at = self._attrs(it_nid).get("ast_type")
        if at == "Name":
            self.parts.append("Var")
            return {"type": "Var", "name": self._attrs(it_nid).get("id")}
        if at == "Call":
            func = self._child_by_field(it_nid, "func")
            if func is not None and self._attrs(func).get("id") == "range":
                rargs = self._children_of_field(it_nid, "args")
                if not rargs:
                    raise EmitError("range() needs at least one argument")
                hi = self._eval_int(rargs[-1])
                lo = self._eval_int(rargs[0]) if len(rargs) >= 2 else 0
                self.parts.append("Vec")
                return {"type": "Vec",
                        "items": [{"type": "Lit", "value": k} for k in range(lo, hi)]}
        raise EmitError(f"the loop iterable ({at!r}) is not a bare Name or "
                        f"range(...) -- named residual, the accumulation "
                        f"construction's scope is range(n)/list-arg iterables")

    last_term: Dict[str, Any] = None  # type: ignore[assignment]


__all__ = ["ingest_ast", "open_ast_productions", "AstTermEmitter", "EmitError"]
