"""compute_grounding — ground a COMPUTATIONAL concept as an EXECUTABLE composition.

The agent's OWN derived principle (order_n_postulates / implication_harvester,
elicited VERBATIM):

    "a COMPOSITIONAL / GENERATIVE system's WHOLE is determined by its PARTS plus a
     finite set of COMBINATION (production) rules, so its members are not an
     enumerated list but an OPEN set REALIZABLE BY COMPOSING parts."

A COMPUTATION is the SAME shape: grounded OPERANDS + grounded OPERATIONS composed
into a Term-tree that EVALUATES to the answer. So grounding a computational
concept = reading its definition and COMPOSING it as an EXECUTABLE Term-tree over
the GROUNDED computable primitives (the reason tower: gcd / times / div / mod /
divisor_sum / …), then evaluating.

    e.g.  "the lcm of a and b is a*b / gcd(a,b)"
          -> lcm := div(times(a, b), gcd(a, b))          (a meaning-Term)
          -> over the GROUNDED {times, div, gcd}
          -> bound {a:4, b:6}  -> EVALUATES -> 12          (was ABSTAIN)

This module is a WORLD ADAPTER (CLAUDE.md): it sequences the agent's OWN
machinery. It owns no math. The MEANING of a definition comes from the
construction-grammar / definitional parse (graph data); the COMBINATION is a
``reason``-tower meaning-Term over HELD computable primitives; the GROUND is
``grounded_representation.ground_concept`` (an admissible Concept->Concept
mutation) — now carrying a RUNNABLE Term-tree as its ``combination``, closing the
loose end (a combination was a named string, not yet an executable tree). The
EVALUATE is ``reason.solve`` walking that tree over the bound operands. No LLM
solves the math; no per-problem Python.

THE LOOSE END CLOSED. ``ground_concept``'s ``combination`` accepts a Term-tree
DICT; here that tree is an EXECUTABLE meaning-Term — ``run_combination`` evaluates
it via ``reason.solve``. The grounded concept's combination is now a RUNNABLE tree.

HONEST FRONTIER. The definition must COMPOSE over HELD computable primitives. A
research-math concept whose definition's operands are themselves un-held / non-
computational (a bordism's "manifolds whose disjoint union is the boundary of a
higher manifold") does NOT compose over the held tower -> grounds=False, the agent
ABSTAINS. The mechanism is right; the frontier is primitive SCOPE + grounding
depth — which the agent would itself have to acquire, recursively.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from domains import grounded_representation as _gr
from domains import reason as _reason


# ---------------------------------------------------------------------------
# The held COMPUTABLE PRIMITIVES — the basis a combination Term-tree composes
# over. Read off the reason tower's CAPABILITIES registry (the agent's grounded
# computations) PLUS the composed capabilities a host installs there. A
# computational definition "grounds" iff its Term-tree reduces to THESE.
#
# Each entry names the ARG ROLES the capability expects (so the parse emits the
# right meaning-Term shape). These mirror reason.CAPABILITIES exactly.
# ---------------------------------------------------------------------------

# operator surface -> (capability concept, [arg roles in operand order]).
# A binary infix operator and a named function both resolve through here.
_OP_ROLES = {
    # arithmetic (held primitives in the reason tower)
    "+": ("plus", ["left", "right"]),
    "-": ("minus", ["left", "right"]),
    "*": ("times", ["left", "right"]),
    "/": ("div", ["left", "right"]),
    "%": ("mod", ["left", "right"]),
    "=": ("eq", ["left", "right"]),
    "==": ("eq", ["left", "right"]),
    ">": ("gt", ["left", "right"]),
    "<": ("lt", ["left", "right"]),
    ">=": ("ge", ["left", "right"]),
    "<=": ("le", ["left", "right"]),
    # divides: k|n is the predicate "k divides n" -> divides(left=k, right=n)
    # (the held capability: right % left == 0). A relational predicate, parsed at
    # the comparison level.
    "|": ("divides", ["left", "right"]),
    # named number-theory functions (held primitives), keyed by the role-shape
    # the tower's lambda reads.
    "gcd": ("gcd", ["a", "b"]),
    "lcm": ("lcm", ["a", "b"]),
    "divisor_sum": ("divisor_sum", ["of"]),
    "divisor_count": ("divisor_count", ["of"]),
    "totient": ("totient", ["of"]),
    "factorial": ("factorial", ["of"]),
    # divides / times as named function calls (the held divides/times primitives,
    # reachable by name as well as by the |/* operator surface). The tower's
    # divides reads (left=k, right=n) -> right % left == 0 ("k divides n"); times
    # reads (left, right). Named here so a read of "m divides 6" / "m*n" routes the
    # function-call form to the held op (parallel to gcd/lcm above).
    "divides": ("divides", ["left", "right"]),
    "times": ("times", ["left", "right"]),
    # STRUCTURED-OBJECT primitives (the simplex/chain tier the boundary operator
    # ∂ composes over). Each is a held capability in the reason tower; named here
    # so the parse routes face / sign / chain-sum function calls to them.
    #   face(simplex, i)        -> drop the i-th vertex (the face_i part).
    #   simplex_dim(simplex)    -> dim = len - 1.
    #   neg_one_pow(i)          -> (-1)^i, the alternating sign.
    #   chain_term(coeff, simplex) -> a one-term chain (the formal-sum atom).
    #   combine_like_terms(chain)  -> reduce the formal sum (cancel like terms).
    #   is_zero_chain(chain)       -> the chain reduces to empty (the ∂∂=0 test).
    "face": ("face", ["of", "i"]),
    "simplex_dim": ("simplex_dim", ["of"]),
    "neg_one_pow": ("neg_one_pow", ["i"]),
    "chain_term": ("chain_term", ["coeff", "simplex"]),
    "combine_like_terms": ("combine_like_terms", ["of"]),
    "is_zero_chain": ("is_zero_chain", ["of"]),
    "scale_chain": ("scale_chain", ["coeff", "of"]),
    # HOMOLOGY primitives (the tier ABOVE ∂ — the Betti formula composes over
    # matrix RANK + the boundary MATRIX + a count of the k-simplices). Named here
    # so the read of "b_n = (#n-simplices − rank ∂_n) − rank ∂_{n+1}" routes the
    # matrix_rank / boundary_matrix / simplices_of_dim calls to the held ops.
    #   simplices_of_dim(complex, k) -> the k-simplices (so cardinality counts them).
    #   boundary_matrix(complex, k)  -> ∂_k as a matrix over the simplex bases.
    #   matrix_rank(M)               -> #linearly-independent rows (Gaussian/GF(2)).
    "simplices_of_dim": ("simplices_of_dim", ["complex", "k"]),
    "boundary_matrix": ("boundary_matrix", ["complex", "k"]),
    "matrix_rank": ("matrix_rank", ["of"]),
    "cardinality": ("cardinality", ["of"]),
    # INTEGRAL HOMOLOGY / SMITH NORMAL FORM primitives (the tier ABOVE the GF(2)
    # Betti — the TORSION the field rank misses). Named here so the read of
    # "the torsion of H_k = the invariant factors > 1 of SNF(∂_{k+1})" routes the
    # integer_boundary_matrix / smith_normal_form calls to the held integer ops.
    "integer_boundary_matrix": ("integer_boundary_matrix", ["complex", "k"]),
    "smith_normal_form": ("smith_normal_form", ["of"]),
    "integral_homology": ("integral_homology", ["complex", "k"]),
    # RATIONAL SPIN-BORDISM COEFFICIENT RANK primitives (the generalized-homology
    # coefficient ring Omega^Spin_* ⊗ Q). Named here so the read of "rank
    # Omega^Spin_n ⊗ Q = partitions of n/4" routes the partition_count call to the
    # held integer DP.
    "partition_count": ("partition_count", ["of"]),
    "spin_rational_rank": ("spin_rational_rank", ["of"]),
    # INTEGRAL AHSS E_2-PAGE primitives (the tier ABOVE the rational rank — the
    # E_2 entry WITH its torsion, assembled by the UCT tensor+Tor over the READ
    # H_*(BG2;Z) torsion + the READ ABP coefficient-ring torsion). Named here so the
    # read of "E^2_{p,q} = H_p(BG2; Omega^Spin_q) = (H_p (x) Omega_q) + Tor(H_{p-1},
    # Omega_q)" routes the free-rank / torsion-rank read-outs to the held integer ops.
    "bg2_int_homology_rank": ("bg2_int_homology_rank", ["of"]),
    "bg2_int_torsion_2rank": ("bg2_int_torsion_2rank", ["of"]),
    "spin_bordism_free_rank": ("spin_bordism_free_rank", ["of"]),
    "spin_bordism_torsion_2rank": ("spin_bordism_torsion_2rank", ["of"]),
    "bg2_integral_e2": ("bg2_integral_e2", ["p", "q"]),
    # CUP PRODUCT / COHOMOLOGY RING primitives (the tier ABOVE cohomology — the
    # Alexander-Whitney cochain product over the held simplicial structure,
    # cochains = ∂^T). Named here so the read of the AW formula
    # ("(α∪β)(σ) = α(front p-face of σ) · β(back q-face of σ)") routes the
    # front_face / back_face / cochain_value / cup_product calls to the held ops.
    "front_face": ("front_face", ["of", "p"]),
    "back_face": ("back_face", ["of", "q"]),
    "cochain_value": ("cochain_value", ["cochain", "simplices", "simplex"]),
    "cup_product": ("cup_product", ["complex", "p", "q", "alpha", "beta"]),
    "coboundary_matrix": ("coboundary_matrix", ["complex", "k"]),
}


# The ITERATION binders are held primitives realised by solve's binder evaluator
# (not by a CAPABILITIES lambda — their body is lazy), so they are not keys in the
# registry. Name them here so the descent treats them as the held collection basis
# a discrete-structure operation reduces to (parallel to range_incl / cardinality,
# which ARE registry keys).
_HELD_ITERATION_BINDERS = {"count_where", "sum_where", "chain_sum", "chain_bind"}


def held_primitive_concepts(capabilities: Optional[dict] = None) -> set:
    """The set of capability concepts the agent HOLDS — the computable basis a
    combination Term-tree may reduce to. Defaults to the live reason tower, PLUS
    the iteration binders realised by the interpreter's binder evaluator."""
    caps = capabilities if capabilities is not None else _reason.CAPABILITIES
    return set(caps.keys()) | _HELD_ITERATION_BINDERS


def _is_held_primitive(concept: str, capabilities: Optional[dict] = None) -> bool:
    return concept in held_primitive_concepts(capabilities)


# ---------------------------------------------------------------------------
# COMPREHEND a COMPUTATIONAL definition -> an EXECUTABLE meaning-Term.
#
# Two definitional forms the agent reads (the permitted thin BOUNDARY parse —
# it applies the held genus-differentia / equation structure, it does not decide
# the math):
#   (i)  AN EQUATION       "lcm(a,b) = a*b/gcd(a,b)"  /  "<term>(args) = <expr>"
#        -> parse the RHS arithmetic expression into a meaning-Term.
#   (ii) A RELATIONAL GLOSS "a number equal to the sum of its proper divisors"
#        -> a small set of held relational templates map to a meaning-Term.
# The parse emits a meaning-Term whose leaves are the term's PARAMETER NAMES
# (Var) or literals, and whose heads are HELD capability concepts.
# ---------------------------------------------------------------------------

# Tokens. The set-builder / count-where syntax adds:  `..` (an integer range),
# `{` `}` (the comprehension braces), `:` (the "such that" separator), and `|`
# (the divides operator, k|n == "k divides n").  `..` and `>=`/`<=`/`==` are
# matched before the single-char alternatives.  NB `\d+\.\d+` (a float) is tried
# before `..` so 1.5 is not mis-split.
_TOKEN_RE = re.compile(
    r"\s*(\d+\.\d+|\.\.|\d+|[A-Za-z_]\w*|>=|<=|==|[(){}:|]|[()+\-*/%,><=])")


def _tokenise_expr(expr: str) -> list[str]:
    toks, i, n = [], 0, len(expr)
    while i < n:
        m = _TOKEN_RE.match(expr, i)
        if not m:
            if expr[i].isspace():
                i += 1
                continue
            raise ValueError(f"cannot tokenise at {expr[i:]!r}")
        toks.append(m.group(1))
        i = m.end()
    return toks


class _ExprParser:
    """A tiny precedence-climbing parser for an arithmetic RHS expression. It
    emits a meaning-Term (the reason.solve shape) over HELD capability heads —
    NOT a math evaluation. Parameters become Var leaves; numbers become literals;
    named functions f(x,y) and infix operators route to their held capability.

    It RECORDS every operand concept it references (parts) so the grounding can
    recurse on an un-held one (the descent)."""

    def __init__(self, toks: list[str]):
        self.toks = toks
        self.pos = 0
        self.parts: set = set()
        # binder variables introduced by a set-builder (count{k in ...}) — these
        # are LOCAL to the comprehension, NOT parameters of the outer term, so the
        # param scan must exclude them.
        self.binders: set = set()

    def _peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def _next(self):
        t = self.toks[self.pos]
        self.pos += 1
        return t

    # expr := cmp ; comparison is the LOWEST-precedence level so an equation RHS
    # like 'aliquot_sum(n) > n' parses as gt(aliquot_sum(n), n) (the whole
    # arithmetic on each side bound tighter than the comparison).
    def parse_expr(self):
        return self.parse_cmp()

    # cmp := add (('>'|'<'|'>='|'<='|'=='|'='|'|') add)?  — a single comparison
    # or the divides predicate (k|n).
    def parse_cmp(self):
        node = self.parse_add()
        if self._peek() in (">", "<", ">=", "<=", "==", "=", "|"):
            op = self._next()
            rhs = self.parse_add()
            concept, roles = _OP_ROLES[op]
            self.parts.add(concept)
            node = {concept: {roles[0]: node, roles[1]: rhs}}
        return node

    # add := term (('+'|'-') term)*
    def parse_add(self):
        node = self.parse_term()
        while self._peek() in ("+", "-"):
            op = self._next()
            rhs = self.parse_term()
            concept, roles = _OP_ROLES[op]
            self.parts.add(concept)
            node = {concept: {roles[0]: node, roles[1]: rhs}}
        return node

    # term := factor (('*'|'/'|'%') factor)*
    def parse_term(self):
        node = self.parse_factor()
        while self._peek() in ("*", "/", "%"):
            op = self._next()
            rhs = self.parse_factor()
            concept, roles = _OP_ROLES[op]
            self.parts.add(concept)
            node = {concept: {roles[0]: node, roles[1]: rhs}}
        return node

    # factor := number | name | name '(' args ')' | '(' expr ')'
    def parse_factor(self):
        t = self._peek()
        if t is None:
            raise ValueError("unexpected end of expression")
        if t == "(":
            self._next()
            node = self.parse_expr()
            if self._peek() != ")":
                raise ValueError("missing )")
            self._next()
            return node
        if re.fullmatch(r"\d+\.\d+|\d+", t):
            self._next()
            return float(t) if "." in t else int(t)
        # SET-BUILDER / count-where comprehension:  count{ V in LO..HI : PRED }
        # or sum{ V in LO..HI : EXPR }. This is how a DISCRETE-STRUCTURE operation
        # is read — an operation over a COLLECTION (a range), binding V over each
        # element. Emits a count_where / sum_where binder Term whose `source` is a
        # range_incl collection, `var` the binder name (literal), and
        # `predicate`/`value` the body sub-term (re-solved per element by solve).
        # `chain_sum{ V in LO..HI : CHAIN_EXPR }` is the STRUCTURED-OBJECT binder:
        # the formal SUM over i producing a CHAIN (each body a (coeff,simplex)
        # term). This is the alternating-sum shape the boundary operator ∂ reads.
        if t in ("count", "sum", "chain_sum") and (
                self.pos + 1 < len(self.toks)
                and self.toks[self.pos + 1] == "{"):
            return self._parse_comprehension()
        # `chain_bind{ (C, S) in CHAIN : CHAIN_EXPR }` iterates a chain's terms,
        # binding each term's COEFFICIENT (C) and SIMPLEX (S); body -> a chain,
        # concatenated. This extends ∂ over a chain BY LINEARITY (the ∂∂ move).
        if t == "chain_bind" and (
                self.pos + 1 < len(self.toks)
                and self.toks[self.pos + 1] == "{"):
            return self._parse_chain_bind()
        if re.fullmatch(r"[A-Za-z_]\w*", t):
            name = self._next()
            if self._peek() == "(":            # a function call name(args...)
                self._next()
                args = [self.parse_expr()]
                while self._peek() == ",":
                    self._next()
                    args.append(self.parse_expr())
                if self._peek() != ")":
                    raise ValueError("missing ) after args")
                self._next()
                if name in _OP_ROLES:
                    concept, roles = _OP_ROLES[name]
                    if len(args) != len(roles):
                        raise ValueError(
                            f"{name} expects {len(roles)} args, got {len(args)}")
                    self.parts.add(concept)
                    return {concept: {roles[i]: args[i]
                                      for i in range(len(roles))}}
                # An UN-KNOWN function name is a REFERENCED SUB-CONCEPT call (e.g.
                # aliquot_sum(n) inside abundant_number's definition). Record it as
                # a part so the descent grounds it (compute -> a runnable op here,
                # or concept -> the understood-not-computable boundary). Emit role
                # names the grounded sub-concept's installed dispatcher reads: 'of'
                # for a single arg (the dispatcher aliases of/arg/a/left -> its Var
                # param), else positional a, b, c, ….
                self.parts.add(name)
                roles = (["of"] if len(args) == 1
                         else [chr(ord("a") + i) for i in range(len(args))])
                return {name: {roles[i]: args[i] for i in range(len(args))}}
            # a bare name = a PARAMETER (Var leaf, resolved against bindings).
            return name
        raise ValueError(f"unexpected token {t!r}")

    # comprehension := ('count'|'sum') '{' VAR 'in' SOURCE ':' expr '}'
    # SOURCE is EITHER a RANGE  (add '..' add  -> range_incl{lo,hi})  OR a LIST
    # (a single expression -> the bound collection itself). The binder VAR ranges
    # over the collection's elements — LOCAL, so it is recorded as a binder
    # (excluded from the outer term's parameters). The head is count_where (a count
    # of elements satisfying the predicate) or sum_where (the sum of an expression
    # over the elements); BOTH are realised by solve's binder evaluator, which
    # iterates ANY concrete collection the source resolves to — a materialised
    # range_incl list OR a list bound to a parameter. So a list-statistic (sum,
    # sum_sq) grounds over the SAME held sum_where binder; no new primitive.
    def _parse_comprehension(self):
        head = self._next()                                   # 'count' | 'sum'
        if self._next() != "{":
            raise ValueError("comprehension missing {")
        var = self._next()
        if not re.fullmatch(r"[A-Za-z_]\w*", var):
            raise ValueError(f"comprehension binder must be a name, got {var!r}")
        self.binders.add(var)
        if self._next() != "in":
            raise ValueError("comprehension missing 'in'")
        # Parse the SOURCE expression once. If it is followed by '..' it is the LO
        # of a range (range_incl); otherwise it IS the list source (a bound
        # collection / sub-term that resolves to a concrete list at eval time).
        src_expr = self.parse_add()
        if self._peek() == "..":
            self._next()                                      # consume '..'
            hi = self.parse_add()
            # the collection operand: a range LO..HI (a range_incl Term).
            self.parts.add("range_incl")
            source = {"range_incl": {"lo": src_expr, "hi": hi}}
        else:
            # a LIST source: the parsed expression resolves to a concrete
            # collection (typically a bare parameter bound to a list). No
            # range_incl is built — the binder folds the list directly.
            source = src_expr
        if self._next() != ":":
            raise ValueError("comprehension missing ':' before the body")
        body = self.parse_expr()
        if self._next() != "}":
            raise ValueError("comprehension missing closing }")
        if head == "count":
            self.parts.add("count_where")
            return {"count_where":
                    {"source": source, "var": var, "predicate": body}}
        if head == "chain_sum":
            # the formal SUM over i producing a CHAIN (the boundary operator's
            # alternating sum). The body evaluates to a (coeff,simplex) chain term;
            # chain_sum concatenates them into the chain.
            self.parts.add("chain_sum")
            return {"chain_sum": {"source": source, "var": var, "value": body}}
        self.parts.add("sum_where")
        return {"sum_where": {"source": source, "var": var, "value": body}}

    # chain_bind := 'chain_bind' '{' '(' C ',' S ')' 'in' CHAIN ':' chain_expr '}'
    # Iterate a CHAIN's terms, binding each term's coefficient C + simplex S; the
    # body evaluates to a chain, concatenated. Extends ∂ over a chain by linearity.
    def _parse_chain_bind(self):
        self._next()                                           # 'chain_bind'
        if self._next() != "{":
            raise ValueError("chain_bind missing {")
        if self._next() != "(":
            raise ValueError("chain_bind missing '(' for the (coeff,simplex) pair")
        cvar = self._next()
        if self._next() != ",":
            raise ValueError("chain_bind missing ',' between coeff and simplex")
        svar = self._next()
        if self._next() != ")":
            raise ValueError("chain_bind missing ')' after the pair")
        if not (re.fullmatch(r"[A-Za-z_]\w*", cvar)
                and re.fullmatch(r"[A-Za-z_]\w*", svar)):
            raise ValueError("chain_bind binders must be names")
        self.binders.add(cvar)
        self.binders.add(svar)
        if self._next() != "in":
            raise ValueError("chain_bind missing 'in'")
        # the source CHAIN is an expression (a bound parameter or a sub-term).
        chain = self.parse_factor()
        if self._next() != ":":
            raise ValueError("chain_bind missing ':' before the body")
        body = self.parse_expr()
        if self._next() != "}":
            raise ValueError("chain_bind missing closing }")
        self.parts.add("chain_bind")
        return {"chain_bind": {"source": chain, "var": [cvar, svar],
                               "value": body}}


# RELATIONAL GLOSS templates: a held relational definition (no equation) maps to
# an executable meaning-Term over held primitives. Each template is a (regex,
# builder) pair; builder(match) -> (combination_term, params, parts). These are
# the agent's HELD relational definitions turned into structure — a small,
# explicit set (additive: more relational definitions = more templates), NOT a
# per-problem decision.
def _perfect_number_term():
    # "a perfect number is a number equal to the sum of its proper divisors":
    #   the proper-divisor sum = divisor_sum(n) - n; perfect iff that equals n.
    #   -> eq( minus(divisor_sum(n), n), n )
    term = {"eq": {
        "left": {"minus": {"left": {"divisor_sum": {"of": "n"}},
                           "right": "n"}},
        "right": "n"}}
    return term, ["n"], {"eq", "minus", "divisor_sum"}


def _triangular_number_term():
    # "the nth triangular number is the sum of the first n integers" = n*(n+1)/2
    #   -> div( times(n, plus(n, 1)), 2 )
    term = {"div": {
        "left": {"times": {"left": "n",
                           "right": {"plus": {"left": "n", "right": 1}}}},
        "right": 2}}
    return term, ["n"], {"div", "times", "plus"}


_RELATIONAL_TEMPLATES = [
    (re.compile(r"equal to the sum of its proper divisors"),
     _perfect_number_term),
    (re.compile(r"sum of the first .* (?:integers|natural numbers|positive integers)"),
     _triangular_number_term),
]


def comprehend_computational_definition(
        definition: str) -> Optional[dict[str, Any]]:
    """COMPREHEND a computational definition into an EXECUTABLE composition.

    Returns {term, params, parts, kind} where:
      · term   — the meaning-Term (reason.solve shape) over held capability heads;
      · params — the parameter names (Var leaves) the term reads from bindings;
      · parts  — the capability concepts the term composes over (for the descent);
      · kind   — 'equation' | 'relational'.
    Returns None when the definition does NOT parse as a computation over held
    primitives (the honest frontier — the caller abstains)."""
    if not definition:
        return None
    text = definition.strip()

    # (i) AN EQUATION:  "...<term>(args) = <expr>"  or  "<term> = <expr>".
    # find the FIRST '=' (not '=='), split LHS/RHS; parse the RHS arithmetic.
    eq_split = re.split(r"(?<![=<>!])=(?!=)", text, maxsplit=1)
    # an equation RHS is a COMPUTATION if it has arithmetic, a function call, OR a
    # set-builder comprehension (count{...} / sum{...}) — the discrete-structure
    # operation form.
    _rhs_is_computation = len(eq_split) == 2 and (
        any(op in eq_split[1] for op in "+-*/%")
        or re.search(r"[A-Za-z_]\w*\s*\(", eq_split[1])
        or re.search(r"\b(?:count|sum)\s*\{", eq_split[1])
        # a bare variable RHS is the IDENTITY function, f(n) = n (e.g. the naturals).
        or re.fullmatch(r"\s*[A-Za-z_]\w*\s*", eq_split[1]))
    if _rhs_is_computation:
        lhs, rhs = eq_split
        # LHS parameters: names inside the term's parens, e.g. lcm(a,b) -> [a,b].
        m = re.search(r"\(([^)]*)\)", lhs)
        params = ([p.strip() for p in m.group(1).split(",") if p.strip()]
                  if m else [])
        try:
            parser = _ExprParser(_tokenise_expr(rhs.strip()))
            term = parser.parse_expr()
        except ValueError:
            term = None
        if term is not None:
            # parameters actually referenced (Var leaves) — fall back to scanning.
            if not params:
                params = sorted(_collect_vars(term))
            return {"term": term, "params": params,
                    "parts": sorted(parser.parts), "kind": "equation"}

    # (ii) A RELATIONAL GLOSS over held primitives.
    for rx, builder in _RELATIONAL_TEMPLATES:
        if rx.search(text):
            term, params, parts = builder()
            return {"term": term, "params": params,
                    "parts": sorted(parts), "kind": "relational"}

    return None


def _collect_vars(term) -> set:
    """The Var leaves (parameter names) a meaning-Term reads from bindings.

    The ITERATION binders (count_where / sum_where) introduce a LOCAL variable:
    its name appears as the literal `var` role (not a free Var) and is BOUND in
    the body, so it must NOT be counted as an outer parameter — collect the body's
    vars then subtract the binder name."""
    if isinstance(term, str):
        return {term}
    if isinstance(term, (bool, int, float)):
        return set()
    concept = next(k for k in term if k != "force")
    if concept in ("count_where", "sum_where", "chain_sum", "chain_bind"):
        spec = term[concept]
        binder = spec["var"]
        body_key = "predicate" if concept == "count_where" else "value"
        out = _collect_vars(spec["source"]) | _collect_vars(spec[body_key])
        # chain_bind binds a PAIR of names; the others a single name.
        if isinstance(binder, list):
            out.difference_update(binder)
        elif isinstance(binder, str):
            out.discard(binder)
        return out
    out = set()
    for child in term[concept].values():
        out |= _collect_vars(child)
    return out


# ---------------------------------------------------------------------------
# GROUND a computational concept as the executable composition + EVALUATE.
# ---------------------------------------------------------------------------

def run_combination(term, bindings: dict, capabilities: Optional[dict] = None):
    """EVALUATE a grounded concept's runnable combination Term-tree over bound
    operands — the loose end closed: a combination is no longer a named string
    but an EXECUTABLE tree. Routes through reason.solve (head concepts -> held
    capabilities). Raises if the tree references an un-held capability."""
    caps = capabilities if capabilities is not None else _reason.CAPABILITIES
    return _reason.solve(term, bindings, caps)


def _sub_definition(conversation, name: str) -> Optional[str]:
    """READ a referenced sub-concept's definition from the in-process feed (a
    teacher gloss / test feed). Same source the concept descent reads — so the
    compute descent and the concept descent read the SAME definition for the
    SAME sub-concept. Returns the text or None (no fed definition)."""
    feed = getattr(conversation, "_definition_feed", None) \
        if conversation is not None else None
    if isinstance(feed, dict):
        t = feed.get(name) or feed.get(name.lower())
        if isinstance(t, str) and t.strip():
            return t.strip()
    return None


def _read_subconcept_definition(name: str, conversation,
                                substrate=None) -> Optional[str]:
    """READ a sub-concept's definition through the SAME reader the concept
    descent uses (read_and_ground._read_definition / its monkeypatch). Lets the
    COMPUTE descent fall back to the reference reader for a sub-concept's
    COMPUTATIONAL definition when no in-process feed staged it — the one read
    loop, shared. Returns the text or None (no reader / no page)."""
    try:
        from domains import read_and_ground as _rag
        return _rag._read_def(name, conversation, None, substrate=substrate)
    except Exception:
        return None


def _ground_subconcept(substrate, name: str, conversation, *,
                       index: Optional[dict] = None) -> dict[str, Any]:
    """THE WIRING: when the COMPUTE descent hits an operand it neither holds nor
    can ground-as-a-computation, recurse through the CONCEPT descent
    (read_and_ground.ground_recursively) — read the sub-concept's definition,
    ground it as a web of concepts reaching bedrock (it COHERES / 'understands
    what it is'). One unified self-extending descent: the compute descent bottoms
    out EITHER at a computable primitive OR a read-grounded sub-concept.

    Returns {concept_grounded, structure, trace, reason} — whether the
    sub-concept COHERES as a concept (the wiki/feed descent reached bedrock),
    even when it is not COMPUTABLE. The caller decides what that means for the
    parent: a concept-grounded-but-not-computable operand makes the parent
    'understood, not computable' (the precise boundary), naming this operand."""
    from domains import read_and_ground as _rag
    try:
        res = _rag.ground_recursively(substrate, name, conversation,
                                      _index=index)
        return {"concept_grounded": bool(res.get("grounded")),
                "structure": res.get("structure"),
                "trace": res.get("trace"), "reason": res.get("reason")}
    except Exception as e:  # the concept descent is best-effort here.
        return {"concept_grounded": False, "structure": None,
                "trace": None, "reason": f"concept descent error: {e}"}


def ground_computation(substrate, concept_name: str, definition: str, *,
                       capabilities: Optional[dict] = None,
                       index: Optional[dict] = None,
                       conversation=None, _depth: int = 0,
                       _max_depth: int = 4) -> dict[str, Any]:
    """GROUND a computational concept — the THIN INSTANCE entrypoint.

    At the TOP level (_depth == 0) this DELEGATES to the general ACQUIRE block
    (acquire.acquire_computation = acquire(...) under the computation parameter
    set): the shared SOURCE -> COMPREHEND -> COMPOSE -> VERIFY pipeline lives ONCE
    in acquire.py. The genuinely per-kind machinery — the computational-def parse,
    the unified compute/concept operand DESCENT, the understood-vs-computable
    boundary (`_ground_computation`, the recursive WORKER) — is the VERIFY
    parameter acquire runs. Re-reads the worker's full result (carried through the
    acquire VERIFY trace) so the public dict shape callers depend on is unchanged.

    INTERNAL recursion (_depth > 0) calls the WORKER directly — the operand descent
    is the per-kind step, not another pass through the general block. (No circular
    recursion: the block's VERIFY drives the WORKER `_ground_computation`, never
    this entrypoint.)

    The block's VERIFY runs the worker with the DEFAULT descent budget + a fresh
    index; a caller that overrides the internal descent knobs (`index`, a non-
    default `_max_depth` — e.g. self_ascent's single-step _max_depth=0) needs that
    exact budget, so it routes STRAIGHT to the worker (the general block does not
    yet host those knobs as parameters — the honest residual, named)."""
    if _depth == 0 and index is None and _max_depth == 4:
        from domains import acquire as _acq
        ar = _acq.acquire_computation(substrate, concept_name, definition,
                                      capabilities=capabilities,
                                      conversation=conversation)
        res = (ar.verify or {}).get("result")
        if res is not None:
            return res
        # acquire short-circuited before VERIFY — fall through to the worker so the
        # honest boundary is produced by the per-kind machinery (defensive; SOURCE
        # returns the fed definition, so this is not normally reached).
    return _ground_computation(substrate, concept_name, definition,
                               capabilities=capabilities, index=index,
                               conversation=conversation, _depth=_depth,
                               _max_depth=_max_depth)


def _ground_computation(substrate, concept_name: str, definition: str, *,
                        capabilities: Optional[dict] = None,
                        index: Optional[dict] = None,
                        conversation=None, _depth: int = 0,
                        _max_depth: int = 4) -> dict[str, Any]:
    """GROUND a computational concept AS AN EXECUTABLE COMPOSITION and install it.

    READ (caller supplies the definition text) -> COMPREHEND it into an executable
    meaning-Term over held computable primitives -> for each operand concept it is
    not held, the UNIFIED DESCENT: (1) ground it as a COMPUTATION (its own def
    reads + composes a runnable tree -> a callable op here), ELSE (2) THE WIRING —
    recurse through the CONCEPT descent (read_and_ground.ground_recursively): if it
    grounds as a CONCEPT (coheres / 'understands what it is') but has no runnable
    combination, it is UNDERSTOOD, not COMPUTABLE -> the parent honestly reports
    'understood, not computable', naming it; ELSE genuinely ungrounded -> abstain.
    -> GROUND the concept (ground_concept writes the built_from edges to the
    operand primitives + the RUNNABLE Term-tree as its combination) -> INSTALL a
    dispatcher into `capabilities` so `solve`/`answer_within` route the concept.

    Returns {grounded, computable, understood, term, params, parts,
    understood_not_computable, recursed, concept_descents, reason, installed}.
    `grounded` is True only when the WHOLE derivation bottoms out at computable
    primitives or freshly-grounded computable sub-concepts; `understood` is True
    when every operand at least COHERES as a concept; `understood_not_computable`
    names the operand(s) that cohere but are not computable (the precise boundary).

    Faithful: the meaning is the parse (graph data / the held templates); the
    combination is a reason-tower meaning-Term; the ground is an admissible
    mutation; the evaluate is reason.solve; the concept descent is read_and_ground
    (the existing loop). No LLM, no per-problem math. The compute descent bottoms
    out at a computable primitive OR a read-grounded computable sub-concept; the
    understood-but-not-computable boundary is named, not faked."""
    caps = capabilities if capabilities is not None else _reason.CAPABILITIES
    if index is None:
        index = _gr._concept_by_name(substrate)

    comp = comprehend_computational_definition(definition)
    if comp is None:
        return {"grounded": False, "computable": False, "understood": False,
                "term": None, "params": [], "parts": [],
                "understood_not_computable": [],
                "reason": ("definition did not comprehend as a computation over "
                           "held primitives (not an equation / relational gloss "
                           "the agent can compose — the honest frontier)"),
                "installed": False}

    term, params, parts = comp["term"], comp["params"], comp["parts"]

    # Every operand concept the combination references must be a HELD computable
    # primitive, OR be grounded-as-a-computation by the COMPUTE descent (its own
    # definition reads + composes a runnable tree -> a callable op in this tree),
    # OR — THE WIRING — be grounded-as-a-CONCEPT by the CONCEPT descent (read its
    # definition, ground it as a web reaching bedrock: it COHERES). The third case
    # is the understood-vs-computable boundary: an operand that COHERES as a
    # concept but has NO runnable combination is UNDERSTOOD, not COMPUTABLE — the
    # parent then honestly reports 'understood, not computable', NAMING it. A
    # genuinely-ungrounded operand (neither computable nor concept-coheres) is the
    # honest frontier — the cone does not bottom out at all.
    ungrounded: list[str] = []          # genuinely ungrounded (no descent reaches)
    understood_not_computable: list[str] = []   # coheres as concept, not runnable
    recursed: dict[str, Any] = {}
    concept_descents: dict[str, Any] = {}
    for p in parts:
        if _is_held_primitive(p, caps):
            continue
        # (1) COMPUTE descent: ground the operand itself as a computation — read
        # its definition, compose a runnable tree, install it as a callable op in
        # THIS tree. The derivation bottoms out at a freshly-grounded COMPUTABLE
        # sub-concept.
        sub_def = _sub_definition(conversation, p)
        if sub_def is None:
            sub_def = _read_subconcept_definition(p, conversation, substrate)
        if sub_def and _depth < _max_depth:
            sub = ground_computation(substrate, p, sub_def,
                                     capabilities=caps, index=index,
                                     conversation=conversation,
                                     _depth=_depth + 1, _max_depth=_max_depth)
            recursed[p] = sub
            if sub["grounded"]:
                continue
        # (2) CONCEPT descent (THE WIRING): the operand did not ground as a
        # computation. Recurse through the CONCEPT machinery (ground_recursively)
        # — does it ground as a CONCEPT (cohere / 'understand what it is')? If so,
        # it is UNDERSTOOD but its operations are not computable primitives -> the
        # parent is understood, not computable, and we name THIS operand.
        cd = _ground_subconcept(substrate, p, conversation, index=index)
        concept_descents[p] = cd
        if cd["concept_grounded"]:
            understood_not_computable.append(p)
        else:
            ungrounded.append(p)

    # The understood-vs-computable BOUNDARY: an operand that COHERES as a concept
    # (the wiki/feed descent reached bedrock) but has no runnable combination ->
    # the parent is UNDERSTOOD (its parts are grounded concepts) yet NOT COMPUTABLE
    # (a part's operations lack a computable realization). Name the non-computable
    # sub-concept precisely. This is reported AHEAD of a genuine-frontier abstain:
    # 'understood, not computable' is a DIFFERENT, more precise verdict than 'did
    # not ground at all'.
    if understood_not_computable and not ungrounded:
        return {"grounded": False, "computable": False, "understood": True,
                "term": term, "params": params, "parts": parts,
                "recursed": recursed, "concept_descents": concept_descents,
                "understood_not_computable": understood_not_computable,
                "reason": (
                    f"understood, not computable: operand(s) "
                    f"{understood_not_computable} GROUND AS CONCEPTS (the concept "
                    f"descent reached bedrock — the agent understands what they "
                    f"are) but have NO runnable combination — their operations are "
                    f"not computable primitives. Computing over them needs those "
                    f"operations acquired as primitives (the next frontier)."),
                "installed": False}

    if ungrounded:
        return {"grounded": False, "computable": False, "understood": False,
                "term": term, "params": params, "parts": parts,
                "recursed": recursed, "concept_descents": concept_descents,
                "understood_not_computable": understood_not_computable,
                "reason": (f"operand(s) {ungrounded} are not held computable "
                           f"primitives, did not ground as a computation, and did "
                           f"not cohere as concepts — the definition does not "
                           f"reduce to the held basis (primitive-scope frontier)"),
                "installed": False}

    # GROUND: write the concept's structural definition — built_from edges to each
    # operand primitive + the RUNNABLE Term-tree as its `combination` (the loose
    # end closed: a combination is now an executable tree, stored as graph data).
    res = _gr.ground_concept(substrate, concept_name, sorted(parts), term,
                             index=index, create_missing=True)

    # ORDER (composition depth) — RECOGNITION, not a new mechanism: the grounded
    # concept's ORDER is the depth of its combination over order-0 held primitives,
    # computed via the agent's order-N machinery (order_n_composition, the same
    # iterate-to-N recursion order_n_concepts runs, here with the
    # FUNCTION-COMPOSITION rule). order-0 = a held primitive; an op over order-0
    # operands = order-1; an op over an op = order-2. Stored on the concept (the
    # tier IS the order). The bedrock test is "is this head a held computable
    # primitive". Additive — failure leaves the grounding untouched.
    try:
        from domains import order_n_composition as _onc
        # The bedrock test is STRUCTURAL (default): a head is order-0 iff its
        # Concept is built_from nothing — so a composed sub-concept adds a tier and
        # the combination_order cross-check agrees with the cone_order ground-truth
        # (the stored `order`). The cone is the structural composition depth = the
        # order; the built_from edges ground_concept just wrote make it computable.
        _onc.compute_concept_order(substrate, res["concept"], combination=term)
    except Exception:
        pass

    # INSTALL a dispatcher into the capability registry so solve()/answer_within
    # route a bound query for this concept to its composed Term-tree, evaluated
    # over the bound operands. The capability IS the grounded combination.
    def _dispatch(a: dict, _term=term, _params=params):
        # bind each parameter name to the supplied arg (by role-name match, then
        # by positional fallback for single/dual-arg concepts).
        b = dict(a)
        missing = [pm for pm in _params if pm not in b]
        # POSITIONAL fallback for a MULTI-arg concept whose caller passed generic
        # arg roles (a/b, left/right) instead of the declared param names: map the
        # positional roles to the missing params IN ORDER, so kernel_dim(cols,mat)
        # invoked as {a:<cols>, b:<mat>} binds cols<-a, mat<-b (not both to a).
        positional = [r for r in ("a", "b", "c", "left", "right", "of", "arg")
                      if r in a]
        if len(missing) > 1 and len(positional) >= len(missing):
            for pm, r in zip(missing, positional):
                b[pm] = a[r]
        else:
            for pm in missing:
                # common role aliases so a bound query {of: n} feeds Var 'n'.
                for alias in ("of", "arg", "a", "left"):
                    if alias in b:
                        b[pm] = b[alias]
                        break
        return run_combination(_term, b, caps)

    caps[concept_name] = _dispatch

    return {"grounded": True, "computable": True, "understood": True,
            "term": term, "params": params,
            "parts": sorted(parts), "recursed": recursed,
            "concept_descents": concept_descents,
            "understood_not_computable": understood_not_computable,
            "ground": {"edges_added": res["edges_added"],
                       "combination_set": res["combination_set"],
                       "combination_is_tree": isinstance(
                           __import__("json").loads(
                               substrate.node(res["concept"])["attrs"]
                               .get("combination", "null")), dict)},
            "reason": ("grounded as an executable composition over held "
                       f"primitives {sorted(parts)}; installed"),
            "installed": True}


__all__ = [
    "held_primitive_concepts", "comprehend_computational_definition",
    "run_combination", "ground_computation",
    "_sub_definition", "_read_subconcept_definition", "_ground_subconcept",
]
