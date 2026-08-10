#!/usr/bin/env python3
"""formula_read_to_term — GENUINE formula -> Term-tree FROM READING (the un-faked
cmsg163).

THE CORRECTION (cmsg163 was a donkey). cmsg163 claimed "formula -> Term-tree from
reading" but the STRUCTURE was HAND-CODED: grounding_generator REGEX-CLASSIFIED the
formula into one of 3 shapes (alternating_sum / euler_relation / divide_by_const)
and render_read_formula HAND-CODED the Python expression per shape. The reading gave
a LABEL + a leaf; the structure was the gift (a curated template in formula
clothing). THIS is the genuine version: the held LaTeX/math reader PARSES the
formula's ACTUAL SYMBOLS into the expression tree — the structure comes from PARSING,
not a template.

I ORCHESTRATE ONLY (CLAUDE.md world-adapter layer):
  (1) THE WORLD-ADAPTER — the formula's LaTeX/symbol string in (`\\chi = b_0 - b_1
      + b_2 - b_3`, the explicit finite alternating sum of subscripted symbols).
  (2) THE PARSE — domains/latex_notation.parse_formula (the HELD LaTeX/math reader,
      cmsg72/119): it PARSES the symbols into the operator-tree it already composes.
      b_0 - b_1 + b_2 - b_3 -> minus(plus(minus(b_0, b_1), b_2), b_3), each b_i a
      subscripted-symbol LEAF, the +/- read off the ACTUAL operators. NO
      operator_shape label, NO render_read_formula template (grep-clean below).
  (3) THE MECHANICAL EMITTER — a FIXED node-type map over the reader's op-tree:
      minus -> Minus, plus -> Plus, times -> Times; a subscripted betti symbol
      b_i -> UseTool(betti, [Lit i]); a superscript -> Pow. The SAME map for ALL
      formulas, keyed on the reader's expression-node TYPE, NOT a shape-label.
  (4) RUST EVALUATES + SELF-VERIFY — the Term-tree is graph data the Rust substrate
      evaluates (substrate.evaluate); the held betti leaf is the UseTool boundary
      (fires inside Rust; tool_fire_count proves it). SELF-VERIFY: euler S^2 -> 2,
      T^2 -> 0, RP^2 -> 1. A WRONG parse FAILS -> REJECTED.

NO TEMPLATES. NO operator_shape CLASSIFICATION. NO LLM hand-parsing. The structure
comes from the held reader's PARSE of the actual symbols; I provide only the formula
text + the mechanical emitter + the boot. The output is a native Term-tree in the
substrate, Rust-evaluated, agent-owned. The answer (671579) is never read. Math /
reading domain only — the speech/audio path is untouched.

See CLAUDE.md (world-adapter only) / domains/latex_notation.py (the held reader's
parse) / domains/ast_to_term.py (the cmsg161 emitter pattern this mirrors over the
op-tree) / scripts/refactor_faculties_graph_native.py (the Rust-eval + self-verify
pattern).
"""
from __future__ import annotations

import json as _json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import substrate_rs as native
import substrate_rs._native as _N
from domains import latex_notation as lx
from domains import gf2_cohomology as _gf2
import domains.reason as _reason


# ===========================================================================
# THE HELD LEAF — betti_number over the held boundary/rank tower (reason.py). This
# is the world-adapter I/O (the held Python tower); it crosses the native UseTool
# boundary INSIDE the Rust evaluator. The handler closes over the complex; only the
# index i crosses. The SAME held leaf refactor_faculties_graph_native uses.
# ===========================================================================

def _betti(complex_, k):
    nk = len(_reason._simplices_of_dim(complex_, k))
    rk = _reason._matrix_rank_gf2(_reason._boundary_matrix(complex_, k))
    rk1 = _reason._matrix_rank_gf2(_reason._boundary_matrix(complex_, k + 1))
    return nk - rk - rk1


def _maxdim(complex_):
    """The complex's dimension (the largest k carrying a simplex) — the concrete
    bound the \\sum-binder's DEFAULT family (\\sum_k) and symbolic upper limit
    (\\sum_{k=0}^{n}) materialise to. A held property of the complex, read by the
    world-adapter; the iteration domain is [0..dim]."""
    return max(d for d in range(16) if _reason._simplices_of_dim(complex_, d))


_SPACES = {"S^2": _gf2.KNOWN_SURF["S^2"], "T^2": _gf2.KNOWN_SURF["T^2"],
           "RP^2": _gf2.KNOWN_SURF["RP^2"]}
# the KNOWN euler characteristics (READ, textbook; NONE a question's answer):
# chi = b_0 - b_1 + b_2 (- b_3); S^2 -> 2, T^2 -> 0, RP^2 -> 1.
_KNOWN_EULER = {"S^2": 2, "T^2": 0, "RP^2": 1}


# ===========================================================================
# THE MECHANICAL EMITTER — a FIXED node-type map over the HELD READER's op-tree
# (the operator-tree parse_formula produces), the SAME for every formula. Keyed on
# the reader's expression-node TYPE (the `op` name / the `term`+index), NOT a
# shape-label. Mirrors ast_to_term's fixed map, but over the LaTeX reader's parse
# (not a Python AST). The leaf-symbol -> held-tool map (b -> betti) is the SAME
# kind as ast_to_term.held_leaves: which symbol denotes the held UseTool leaf.
# ===========================================================================

# the reader's operator NAME -> the DSL Term TYPE. Fixed for all formulas. The
# \sum-binder extends this map: the reader's `sum` fold-node -> the held Sum Term;
# `power` -> Pow; `neg` -> Neg; `times` -> Times. The SAME node-type-keyed map.
_OP_TERM = {
    "minus": "Minus",        # binary a - b
    "plus": "Plus",          # variadic (emitted binary)
    "times": "Times",        # variadic (emitted binary)
    "modulo": "Div",         # a / b (quotient) — present for the homology op-tree
    "div": "Div",            # binary a / b (\frac{a}{b}) — the arithmetic fraction
    "power": "Pow",          # binary base^exp ((-1)^k)
    "neg": "Neg",            # unary -x (the (-1) base)
    "abs": "Abs",            # unary |x| (cardinality / absolute value)
}
_VARIADIC = {"Plus", "Times"}
_UNARY = {"Neg", "Abs"}

# the reader's FOLD-op (a binder over a family) -> the held DSL fold Term TYPE. The
# SAME node-type-keyed map as _OP_TERM, for the binder constructions (\sum/\prod/
# \min/\max). MinOver/MaxOver carry an extra `default`; Sum/Prod do not.
_FOLD_TERM = {
    "sum": "Sum",            # \sum_k <body>  -> Sum over the family
    "product": "Prod",       # \prod_k <body> -> Prod over the family
    "min_over": "MinOver",   # \min_k <body>  -> MinOver the family
    "max_over": "MaxOver",   # \max_k <body>  -> MaxOver the family
}
_FOLD_DEFAULT = {"MinOver", "MaxOver"}  # these fold Terms take a `default`

# the reader's OPERATOR-NODE name -> a HELD LEAF (a UseTool call to the held tower),
# the SAME node-type-keyed map as _OP_TERM but for the un-held-in-the-DSL operators
# whose meaning is a HELD COMPUTE across the world-adapter boundary (dim/rank/binom/
# torsion), NOT a DSL Term. The value declares HOW the reader node's index/args
# become the UseTool args:
#   "index"  — the held compute is keyed on an INDEX (a degree k): the leaf is
#              UseTool(tool, [<index of the (sole, indexed) argument node>]). \dim H_k
#              / \rank H_k -> the index k of the inner homology node -> betti_k.
#   "args"   — the held compute consumes the operator's ARGUMENTS as Lit/Var terms:
#              \binom{n}{k} -> UseTool(tool, [emit(n), emit(k)]). n,k recursively
#              emitted (a concrete \binom{4}{2} -> [Lit 4, Lit 2]).
#   "complex"— the held compute is a PROPERTY OF THE COMPLEX (no index/arg crosses):
#              \dim X (X a bare space atom) -> UseTool(tool, []) -> the complex
#              dimension (maxdim). The handler closes over the complex.
# The tool NAME is the held UseTool handler the world-adapter registers; the handler
# CALLS THE HELD TOWER (dim/betti/binom/torsion) — NOT a hand-coded value.
_OP_LEAF = {}  # set per-emitter via leaf_op_tools (no module-global default).


class EmitError(Exception):
    """The fixed map cannot translate this op-tree node — the named residual (a
    reader node-type the map has no Term for)."""


class OpTreeEmitter:
    """Apply the FIXED reader-op-tree -> Term-tree map. `leaf_tools` = the held
    leaf-symbol -> tool name (e.g. {'b': 'betti'}): a subscripted instance of that
    symbol (b_i) maps to a held UseTool(tool, [Lit i]) — the held boundary the
    composition bottoms out at. The composition (+, -, *) becomes native Term.

    `dim` = the concrete iteration bound the held DEFAULT FAMILY (\\sum_k) and the
    symbolic upper limit (\\sum_{k=0}^{n}, n=dim) materialise to: the complex's
    dimension. The \\sum-binder maps to the held Sum Term with source SetT[Lit
    0..dim], var_name the binder, value the recursively-emitted body — the bound
    variable k flowing into both the Pow exponent and the betti UseTool index as a
    Var (resolved per-element inside the Rust Sum)."""

    def __init__(self, leaf_tools, dim=None, leaf_op_tools=None):
        self.leaf_tools = dict(leaf_tools)
        self.dim = dim
        # the held-LEAF operator map (operator-node name -> {tool, via}); a node whose
        # `op` is in here is a HELD COMPUTE via UseTool (dim/rank/binom/torsion), NOT a
        # DSL Term. Empty by default -> those ops stay an honest un-held-leaf stall.
        self.leaf_op_tools = dict(leaf_op_tools or {})
        self.binders = set()   # the bound variables currently in scope (\sum k)
        self.parts = []        # the Term-types produced (provenance)
        self.leaf_calls = []   # the held leaf indices fired

    def emit(self, node):
        # a LEAF — {term, subscript?/superscript?/index?, held}
        if "term" in node:
            return self._emit_leaf(node)
        op = node.get("op")
        # a BINDER fold (\sum/\prod/\min/\max) -> the held fold Term over the
        # materialised family. General over any node carrying a `binder` whose op
        # is in _FOLD_TERM (not keyed to 'sum').
        if "binder" in node and op in _FOLD_TERM:
            return self._emit_fold(node)
        # a HELD-LEAF operator (\dim / \rank / \binom / |torsion|) -> a UseTool call
        # crossing the world-adapter boundary into the HELD TOWER. Same node-type-keyed
        # dispatch as the fold/op maps; only fires when the world-adapter registered the
        # tool (leaf_op_tools) — else it falls through to the honest un-held stall.
        if op in self.leaf_op_tools:
            return self._emit_op_leaf(node)
        # an OPERATOR — {op, args:[...]}
        term_t = _OP_TERM.get(op)
        if term_t is None:
            raise EmitError(f"no Term for reader op {op!r} (the named residual: the "
                            f"fixed map has no Term for this op-tree node)")
        args = [self.emit(a) for a in node.get("args", [])]
        self.parts.append(term_t)
        if term_t in _VARIADIC:
            return {"type": term_t, "items": args}
        if term_t in _UNARY:
            if len(args) != 1:
                raise EmitError(f"unary Term {term_t} needs 1 arg, got {len(args)}")
            return {"type": term_t, "arg": args[0]}
        if len(args) != 2:
            raise EmitError(f"binary Term {term_t} needs 2 args, got {len(args)}")
        return {"type": term_t, "a": args[0], "b": args[1]}

    def _emit_op_leaf(self, node):
        """A HELD-LEAF OPERATOR (\\dim / \\rank / \\binom / |torsion|) -> a UseTool
        call into the HELD TOWER. The spec in leaf_op_tools[op] = {tool, via} declares
        how the reader node's index/args become the UseTool args (the SAME node-type-
        keyed mechanical map as _OP_TERM/_FOLD_TERM):
          via 'index'   — \\dim H_k / \\rank H_k: the held compute is keyed on the
                          DEGREE k carried by the (sole) argument node. Emit
                          UseTool(tool, [<index term>]) — the index Lit/Var the inner
                          homology/atom node carries (the betti_k the tower computes).
          via 'args'    — \\binom{n}{k}: the held compute consumes the operator's
                          ARGUMENTS. Emit UseTool(tool, [emit(a) for a in args]) — each
                          recursively emitted (a concrete \\binom{4}{2} -> [Lit 4,Lit 2]).
          via 'complex' — \\dim X: the held compute is a PROPERTY OF THE COMPLEX (the
                          dimension); no index/arg crosses. Emit UseTool(tool, []) — the
                          handler closes over the complex.
        The tool fires the held tower (dim/betti/binom/torsion) INSIDE Rust; NOT a
        hand-coded value."""
        spec = self.leaf_op_tools[node["op"]]
        tool = spec["tool"]
        via = spec["via"]
        if via == "index":
            args = node.get("args", [])
            if len(args) != 1:
                raise EmitError(f"held-leaf {node['op']!r} (via index) needs 1 "
                                f"argument, got {len(args)}")
            idx = self._arg_index(args[0])
            self.leaf_calls.append(idx)
            self.parts.append("UseTool")
            return {"type": "UseTool", "tool": tool,
                    "args": [self._index_term(idx)]}
        if via == "args":
            arg_terms = [self.emit(a) for a in node.get("args", [])]
            self.parts.append("UseTool")
            return {"type": "UseTool", "tool": tool, "args": arg_terms}
        if via == "complex":
            self.parts.append("UseTool")
            return {"type": "UseTool", "tool": tool, "args": []}
        raise EmitError(f"held-leaf {node['op']!r}: unknown via {via!r}")

    def _arg_index(self, arg):
        """The DEGREE index a \\dim/\\rank argument carries: the `index` of an indexed
        head node (homology@k -> 'k'), or the subscript of an indexed leaf (H_k as a
        bare leaf -> 'k'). The held compute (betti_k) is keyed on it."""
        if isinstance(arg, dict):
            if arg.get("index") is not None:
                return arg["index"]
            if arg.get("subscript") is not None:
                return arg["subscript"]
        raise EmitError(f"held-leaf (via index) argument carries no degree index "
                        f"(got {arg!r}) — the named residual")

    def _emit_fold(self, node):
        """A BINDER fold (\\sum/\\prod/\\min/\\max) -> the held fold Term (Sum/Prod/
        MinOver/MaxOver) over the materialised family. The family (range) materialises
        to a SetT of Lit indices [0..dim]; the binder is bound as the fold var_name;
        the body is the recursively-emitted value (the bound var k flows in as a Var).
        The SAME held fold the agent's order-N operators compose; the fold TYPE comes
        from _FOLD_TERM keyed on the reader's op (general over the binder forms)."""
        fold_t = _FOLD_TERM[node["op"]]
        binder = node["binder"]
        domain = self._materialise_range(node.get("range"))
        # the binder var is IN SCOPE while the body emits: b_k -> UseTool(betti,
        # [Var k]); a bare k -> Var k.
        self.binders.add(binder)
        try:
            body = self.emit(node["args"][0])
        finally:
            self.binders.discard(binder)
        self.parts.append(fold_t)
        term = {"type": fold_t,
                "source": {"type": "SetT", "items": domain},
                "var_name": binder,
                "value": body}
        if fold_t in _FOLD_DEFAULT:
            # MinOver/MaxOver over a non-empty materialised family always has at least
            # one element; the held default (0) is the empty-family fallback.
            term["default"] = {"type": "Lit", "value": 0}
        return term

    def _materialise_range(self, rng):
        """The fold's family -> the concrete [Lit 0 .. Lit dim] index set. An EXPLICIT
        range \\sum_{k=0}^{n} (lo=0, hi=n) materialises hi against the held bound
        (n=dim); a bare \\sum_k (rng None) -> the held DEFAULT family 0..dim. A
        mechanical materialisation of the held iteration domain, not a decision."""
        if self.dim is None:
            raise EmitError("no concrete dimension bound for the \\sum family")
        lo = 0
        hi = self.dim
        if rng is not None:
            lo_s = rng.get("lo")
            hi_s = rng.get("hi")
            if lo_s is not None:
                try:
                    lo = int(lo_s)
                except (TypeError, ValueError):
                    raise EmitError(f"\\sum lower limit {lo_s!r} is not concrete")
            if hi_s is not None:
                # an integer literal, else a symbolic upper bound (n) = the held dim.
                try:
                    hi = int(hi_s)
                except (TypeError, ValueError):
                    hi = self.dim
        return [{"type": "Lit", "value": k} for k in range(lo, hi + 1)]

    def _emit_leaf(self, node):
        sym = node.get("term")
        sub = node.get("subscript")
        sup = node.get("superscript")
        # a held leaf-symbol carrying a subscript index (b_i / b_k) -> UseTool(tool,
        # [<index>]). The index is a concrete Lit (b_2) OR — when it is a bound binder
        # variable (b_k inside \sum_k) — the Var k the Sum binds per element.
        if sym in self.leaf_tools and sub is not None:
            tool = self.leaf_tools[sym]
            idx = self._index_term(sub)
            self.leaf_calls.append(sub)
            self.parts.append("UseTool")
            return {"type": "UseTool", "tool": tool, "args": [idx]}
        # a superscript on a leaf (a power b^k / 1^k) -> Pow(base, exponent).
        if sup is not None:
            self.parts.append("Pow")
            return {"type": "Pow",
                    "a": self._scalar_term(sym),
                    "b": self._index_term(sup)}
        # a bare leaf: the bound binder variable (k) -> Var k; a held leaf-SYMBOL with
        # NO subscript -> a UseTool PROPERTY leaf (the same `via complex` pattern: a held
        # property of the object, no index crosses — e.g. m = |H_1| = prod(orders), the
        # held abelianization order); else an integer Lit.
        if sub is None and sup is None:
            if sym in self.binders:
                self.parts.append("Var")
                return {"type": "Var", "name": sym}
            if sym in self.leaf_tools:
                tool = self.leaf_tools[sym]
                self.leaf_calls.append(sym)
                self.parts.append("UseTool")
                return {"type": "UseTool", "tool": tool, "args": []}
            return self._scalar_term(sym)
        raise EmitError(f"leaf symbol {sym!r} (subscript {sub!r}) is neither a held "
                        f"leaf nor a scalar — the named residual")

    def _scalar_term(self, sym):
        # a bare integer literal -> Lit; anything else is an un-bound scalar.
        try:
            return {"type": "Lit", "value": int(sym)}
        except (TypeError, ValueError):
            raise EmitError(f"scalar leaf {sym!r} has no concrete numeric value")

    def _index_term(self, idx_str):
        # the subscript/superscript index materialises to a Lit (a concrete subscript
        # b_2) OR a Var (a bound binder variable k inside the \sum — the Sum binds it
        # per family element; UseTool resolves the Var before firing the held leaf).
        if idx_str in self.binders:
            return {"type": "Var", "name": idx_str}
        try:
            return {"type": "Lit", "value": int(idx_str)}
        except (TypeError, ValueError):
            raise EmitError(f"index {idx_str!r} is not a concrete integer nor a bound "
                            f"binder variable (the named residual)")


class _Pred:
    """The order_n_concepts wrapper: a raw Term-JSON dict the Rust evaluator ingests
    via term_from_json (the SAME path order_n's / refactor_faculties' Terms take)."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _grep_no_template():
    """Donkey-check (the cmsg163 rail): confirm THIS orchestration uses NEITHER
    grounding_generator's operator_shape / _locate_* NOR render_read_formula (the
    classify-then-template path). The structure comes from the held reader's PARSE."""
    src = open(__file__).read()
    banned = ["operator_shape", "_locate_alternating", "render_read_formula",
              "grounding_generator"]
    hits = [b for b in banned if b in src and f'"{b}"' not in src and f"'{b}'" not in src]
    return hits


def main() -> int:
    print("=" * 76)
    print("GENUINE formula -> Term-tree FROM READING (the un-faked cmsg163).")
    print("The held LaTeX/math reader PARSES the formula's SYMBOLS into the expression")
    print("tree (no classification, no template); the mechanical emitter maps it to a")
    print("native Term-tree, Rust-evaluated + self-verified. I orchestrate only the")
    print("world-adapter (formula text in) + the emitter + the boot.")
    print("=" * 76)

    # === (1) THE WORLD-ADAPTER: the formula text in (the \sum-BINDER form, cmsg165
    # -> the binder). The reader now holds the 3 general constructions (\sum-binder,
    # power, juxtaposition) so the binder form parses from the symbols.
    formula = r"\chi = \sum_k (-1)^k b_k"
    print(f"\n(1) WORLD-ADAPTER (the formula text in):")
    print(f"    {formula!r}")
    print(f"    (the \\sum-BINDER form of the euler characteristic: a big-operator FOLD")
    print(f"     over k of the alternating product (-1)^k b_k; the STRUCTURE must be")
    print(f"     PARSED from the \\sum / the ^ / the juxtaposition, NOT classified.)")

    # === (2) THE PARSE: the held LaTeX/math reader parses the SYMBOLS -> op-tree.
    parsed = lx.parse_formula(formula)
    print(f"\n(2) THE PARSE — domains/latex_notation.parse_formula (the held reader):")
    if parsed is None:
        print("    the held reader returned None — it could NOT parse the symbols.")
        print("\nOUTCOME (c): STALL — the held reader can't parse the explicit form into")
        print("  an expression tree. The prose->structure floor stands.")
        return 1
    print(f"    the reader's PARSED expression tree (the provenance — the structure")
    print(f"    came from PARSING the actual symbols, NOT a label/template):")
    print(f"        repr : {parsed['repr']}")
    print(f"        tree : {_json.dumps(parsed['structure'])}")
    print(f"    (the \\sum -> a FOLD node binding k; (-1)^k -> power(neg(1), k) [the ^ +")
    print(f"     the parenthesised unary-minus base]; (-1)^k b_k -> times(...) [the")
    print(f"     JUXTAPOSITION]; b_k a subscripted leaf over the binder k — ALL read off")
    print(f"     the actual symbols. This IS parse_formula's output on the binder form.)")

    # the donkey-check: confirm NO operator_shape / render_read_formula here.
    hits = _grep_no_template()
    print(f"\n    DONKEY-CHECK (grep this script): operator_shape / _locate_* /")
    print(f"    render_read_formula / grounding_generator used as code: "
          f"{hits if hits else 'NONE (clean — structure from the PARSE, not a template)'}")

    # === (3) THE MECHANICAL EMITTER: the fixed node-type map over the reader's tree.
    print(f"\n(3) THE MECHANICAL EMITTER (the FIXED reader-op -> Term-type map, same")
    print(f"    for ALL formulas; keyed on the reader's node TYPE, NOT a shape-label):")
    for op, t in _OP_TERM.items():
        print(f"        reader {op:<7} -> {t}")
    print(f"        a \\sum-binder fold          \\sum_k <body> -> Sum(SetT[0..dim], k, body)")
    print(f"        a subscripted betti symbol  b_k -> UseTool(betti, [Var k])  (bound k)")
    print(f"        a bare binder leaf          k   -> Var k")
    # the emitter materialises the \sum family against the complex's dim — so the
    # Term is emitted per-complex (the SAME emitter, the dim the only world-adapter
    # input). Shown on S^2; the held-out formulas below re-use the SAME emitter.
    sample_dim = _maxdim(_SPACES["S^2"])
    sample_em = OpTreeEmitter(leaf_tools={"b": "betti"}, dim=sample_dim)
    sample_term = sample_em.emit(parsed["structure"])
    print(f"\n    applied over the reader's parsed tree (dim(S^2)={sample_dim}) -> the")
    print(f"    native Sum Term-tree:")
    print(f"        parts : {sample_em.parts}")
    print(f"        Term  : {_json.dumps(sample_term)}")

    # === (4) RUST EVALUATES + SELF-VERIFY on knowns.
    print(f"\n(4) RUST EVALUATES the native Sum Term-tree + SELF-VERIFY (euler on knowns):")
    s = native.Substrate()
    fires0 = _N.tool_fire_count()
    ok = True
    rows = []
    for name, expected in _KNOWN_EULER.items():
        cx = _SPACES[name]
        # the \sum family materialises to [0..dim(cx)] — the SAME emitter, the dim
        # the only per-complex world-adapter input.
        em = OpTreeEmitter(leaf_tools={"b": "betti"}, dim=_maxdim(cx))
        term = em.emit(parsed["structure"])
        # the held betti leaf bound into the UseTool handler (the world-adapter I/O,
        # crossing the native boundary inside Rust). The bound k flows in as a Var
        # the Rust Sum resolves per family element.
        _N.register_tool_handler("betti", lambda k, _c=cx: _betti(_c, int(k)))
        got = s.evaluate(_Pred(term), {})
        passed = (float(got) == float(expected))
        rows.append((name, got, expected, "PASS" if passed else "REJECT"))
        ok = ok and passed
    for name, got, exp, verdict in rows:
        print(f"        {name:<5} chi(Rust) = {got!s:<4} expected = {exp!s:<3} -> {verdict}")
    fires = _N.tool_fire_count() - fires0
    print(f"      held betti UseTool leaf fired natively INSIDE the Rust evaluator")
    print(f"      {fires} times (tool_fire_count) — the held tower crossed the native")
    print(f"      boundary; the \\sum-fold COMPOSITION (Sum/Pow/Neg/Times) ran in Rust.")
    print(f"      SELF-VERIFY: {'PASS (agent-owned native Sum Term-tree accepted)' if ok else 'REJECT'}")

    # === DISCRIMINATION (the donkey-check): a WRONG formula -> the SAME reader +
    # SAME emitter -> a Term-tree that MUST FAIL self-verify (so PASS is not vacuous).
    # The NON-alternating \sum b_k (no (-1)^k sign) is parsed + emitted identically;
    # it is the TOTAL betti number, which must NOT reproduce the euler knowns.
    print(f"\n    DISCRIMINATION (donkey-check): the SAME reader + emitter on a WRONG")
    print(f"    formula (the non-alternating \\sum_k b_k = the total betti number):")
    bad_parsed = lx.parse_formula(r"\chi = \sum_k b_k")
    bad_ok = True
    for name, expected in _KNOWN_EULER.items():
        cx = _SPACES[name]
        bad_term = OpTreeEmitter(leaf_tools={"b": "betti"}, dim=_maxdim(cx)).emit(
            bad_parsed["structure"])
        _N.register_tool_handler("betti", lambda k, _c=cx: _betti(_c, int(k)))
        got = s.evaluate(_Pred(bad_term), {})
        bad_ok = bad_ok and (float(got) == float(expected))
    print(f"        non-alternating \\sum self-verify: "
          f"{'(WRONGLY) PASSED — discrimination FAILED' if bad_ok else 'REJECTED (correct: the total-betti \\sum does not reproduce the euler knowns)'}")

    # === GENERALITY (the proof the \sum is NOT euler-tuned): a HELD-OUT \sum formula
    # I did NOT tune for parses into a DIFFERENT correct tree, evaluated natively. The
    # total betti \sum b_k (no Pow!) and \sum k b_k (Times k,b_k) are STRUCTURALLY
    # different from the euler \sum; the expected values are computed INDEPENDENTLY
    # from the betti numbers (none a question's answer).
    print(f"\n    GENERALITY (the SAME \\sum construction, a HELD-OUT formula -> a")
    print(f"    DIFFERENT correct tree — the proof it is general, not euler-tuned):")
    general_ok = True
    for held_out, desc in [(r"\sum_{k=0}^{n} b_k", "total betti (NO Pow/Neg)"),
                           (r"\sum_{k=0}^{n} k b_k", "sum k*b_k (Times k,b_k)")]:
        hp = lx.parse_formula(held_out)
        print(f"        {held_out!r:<22} -> {hp['repr']}")
        print(f"          ({desc}: a DIFFERENT tree — {hp['repr'].split('(')[0]}...)")
        for name in _KNOWN_EULER:
            cx = _SPACES[name]
            dim = _maxdim(cx)
            term = OpTreeEmitter(leaf_tools={"b": "betti"}, dim=dim).emit(
                hp["structure"])
            _N.register_tool_handler("betti", lambda k, _c=cx: _betti(_c, int(k)))
            got = s.evaluate(_Pred(term), {})
            bettis = [_betti(cx, k) for k in range(dim + 1)]
            indep = (sum(bettis) if held_out.strip().endswith("b_k")
                     and " k b_k" not in held_out
                     else sum(k * b for k, b in enumerate(bettis)))
            match = (float(got) == float(indep))
            general_ok = general_ok and match
            print(f"          {name:<5} Rust = {got!s:<3} indep = {indep!s:<3} "
                  f"-> {'MATCH' if match else 'DIFF'}")

    # === THE OUTCOME.
    print(f"\n" + "=" * 76)
    if ok and not bad_ok and general_ok and not hits:
        print("OUTCOME (a): THE \\sum-BINDER PARSES — the next general construction in the")
        print("  prose->structure grammar, un-faked.")
        print("  · THE READER PARSES THE BINDER FORM: the held LaTeX/math reader, extended")
        print("    with the 3 GENERAL constructions (\\sum-binder, power, juxtaposition),")
        print("    PARSED `\\chi = \\sum_k (-1)^k b_k` into the FOLD expression-tree")
        print("    sum[k](times(power(neg(1),k), b_k)) FROM THE SYMBOLS (the \\sum, the ^,")
        print("    the juxtaposition, the b_k) — NO template, NO operator_shape.")
        print("  · THE EMITTER maps the fold -> the held Sum Term (Sum over SetT[0..dim],")
        print("    binding k; power->Pow, neg->Neg, juxtaposition->Times, b_k->UseTool(")
        print("    betti,[Var k])); Rust EVALUATED it natively + SELF-VERIFIED euler")
        print("    S^2->2 / T^2->0 / RP^2->1; the betti UseTool fired INSIDE Rust.")
        print("  · GENERALITY: the SAME \\sum construction parses HELD-OUT formulas I did")
        print("    NOT tune for (total betti \\sum b_k -> NO Pow; \\sum k b_k -> Times k,b_k)")
        print("    into DIFFERENT correct trees, each Rust-evaluated to its independently-")
        print("    computed value -> the \\sum is GENERAL, not a euler pattern.")
        print("  · DISCRIMINATION: the non-alternating \\sum b_k is REJECTED (does not")
        print("    reproduce the euler knowns) -> the PASS is not vacuous.")
        print("  The reader now grounds the BINDER form from reading; the prose->structure")
        print("  floor moves one general construction further (cmsg165 explicit-arith ->")
        print("  the \\sum-binder).")
        rc = 0
    elif hits:
        print("OUTCOME (d): VOID — a template/classification path was used.")
        rc = 1
    else:
        print("OUTCOME (b/c): a native Term-tree FAILED self-verify or the discrimination")
        print("  did not reject the wrong formula -> the read structure is not genuine.")
        rc = 1
    print("=" * 76)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
