"""gate_audit — CHECK THE INVARIANT, NOT A SPELLING OF IT.

PROTOCOL §13 (magic numbers fall OUT), §12 (a selector that matches by
substring is not a selector), §0 (no decision in Python).

--------------------------------------------------------------------------
THE PROBLEM THIS MODULE EXISTS TO SOLVE
--------------------------------------------------------------------------
Five AST/§13 gates in this tree failed, each found by accident:

  1. a gate went RED on a DOCSTRING -- the string was in prose, not code;
  2. a gate counted ARRAY INDICES as thresholds (3 of 6 flagged sites false),
     and its first fix was also wrong (`ast.walk` cannot prune);
  3. a gate's selector located its target BY SUBSTRING and silently selected
     the wrong subtree, so the supervisor's own injection test PASSED when it
     should have FAILED;
  4. a §13 threshold was closed BY NAMING IT -- bind the literal to a name and
     the walker goes green. A NAME BOUND TO A LITERAL IS A LITERAL;
  5. a substring assertion MATCHED ITSELF, inside the test written to warn
     about substring selectors.

A checklist of those five is the wrong instrument, and this project has that
on record from a real failure: six spellings felt like a pattern, were a
SAMPLE, and the seventh walked through within one commit.

--------------------------------------------------------------------------
THE CLASS -- what a §13 gate is ACTUALLY asserting
--------------------------------------------------------------------------
Not a pattern. A REACHABILITY property over a dataflow graph:

    NO PATH RUNS FROM AN AUTHOR-WRITTEN VALUE TO A DECISION SINK.

  * an AUTHOR-WRITTEN VALUE is a literal in the source -- a number the author
    chose. The legitimate alternative is a MEASUREMENT: a value read out of
    the graph, the data, or the system's own statistics.
  * a DECISION SINK is a position where a value changes what the program
    DOES: a comparison operand, a branch condition, a clip/saturation bound,
    a multiplicative coefficient on a decided quantity.

Every one of the five failures is one of exactly THREE approximation errors
made when that reachability question is replaced by a syntactic pattern:

  SOURCE approximated by a TOKEN.
      The gate looks for a literal AT the sink. Any indirection defeats it:
      a name binding, a default argument, a dict/tuple entry, a class
      attribute, arithmetic on literals. -> failure #4, and the widest hole.
      THE FIX IS TRANSITIVE CLOSURE OVER BINDINGS, not more spellings.

  SINK approximated by a CONTEXT.
      The gate inspects an enumerated set of AST positions -- classically
      only `ast.If` tests. Then `return x > 0.5`, `assert x > 0.5`,
      `min(x, 0.5)`, a comprehension guard and a ternary are all invisible.
      In the other direction, a position that is NOT a decision gets flagged:
      an array index, an arity, a `range()` bound, an enum size. -> failure #2,
      both directions of the same error.
      THE FIX IS TO TYPE THE SINK BY ITS PARENT CONTEXT, so non-decisions are
      excluded STRUCTURALLY rather than by an exemption list. An exemption
      list is a gate that cried wolf and was quieted instead of fixed.

  REGION approximated by a SUBSTRING.
      The gate finds its target subtree by matching text. It may select the
      wrong subtree (#3), may include docstrings and comments -- prose, not
      code (#1) -- or may match its own source (#5).
      THE FIX IS AST IDENTITY: resolve a dotted qualified name to a node, and
      strip docstrings by POSITION (first statement of a body), never by
      pattern.

The sixth spelling is covered because none of the three fixes is a spelling.

--------------------------------------------------------------------------
THE HONEST LIMIT, STATED UP FRONT
--------------------------------------------------------------------------
Backward constant propagation in Python is not decidable in general. This
module therefore resolves what it can and reports the rest as UNRESOLVED --
**counted, never discarded**, following `seed_claim`'s posture. A CLEAN
result from this tool means "no author-written value was TRACED to a decision
sink", never "none reaches one". Any consumer that reads a zero here as proof
of absence has made §12.1's error: inferring what code selects from a count.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

# --------------------------------------------------------------------------
# REGION -- selection by AST IDENTITY, never by substring.
# --------------------------------------------------------------------------


def resolve(tree: ast.Module, qualname: str) -> ast.AST:
    """Resolve a dotted qualified name (`Class.method`, `func`) to its node by
    walking the DEFINITION TREE, not by matching text.

    This is the fix for failure #3. A substring selector silently returns the
    wrong subtree and the caller cannot tell; this raises."""
    node: ast.AST = tree
    for part in qualname.split("."):
        body = getattr(node, "body", None)
        if body is None:
            raise LookupError(f"{qualname}: {part} has no body to search")
        for child in body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                    and child.name == part:
                node = child
                break
        else:
            raise LookupError(f"{qualname}: no definition named {part!r}")
    return node


def executable_body(node: ast.AST) -> list[ast.stmt]:
    """The statements of `node` MINUS its docstring, removed BY POSITION.

    This is the fix for failure #1. A docstring is the first statement of a
    body when that statement is a bare string expression -- a structural fact.
    Stripping prose by pattern is what put a gate red on a docstring, and
    stripping it by `startswith('#')` (the tree's current habit) does not
    remove docstrings at all."""
    body = list(getattr(node, "body", []))
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return body


# NOTE -- THE DOCSTRING FAILURE CLASS IS DISSOLVED, NOT DEFENDED AGAINST.
#
# A recorded failure had a gate go RED ON A DOCSTRING: the string it matched
# appeared in prose, not in code. The reflex is to strip docstrings before
# checking, and this module did that.
#
# A break-the-instrument probe showed the strip was dead: removing it flagged
# nothing new. The reason is structural and worth stating, because it retires
# the whole class rather than patching one instance -- **`ast.parse` does not
# parse the CONTENTS of a string literal**, so no `ast.Compare` node can exist
# inside a docstring, ever. Prose cannot produce a sink.
#
# So failure #1 is not a hazard an AST gate must defend against; it is a
# hazard that only exists for gates matching TEXT. The tree's flagship §13
# gate is a regex, which is exactly why it was vulnerable. Being AST-based is
# the fix, and carrying a docstring-strip alongside it is unreachable
# defensive code -- which §12.3 already named as a thing to remove rather than
# keep for comfort, since it reads as a live gate and is not one.
#
# `executable_body` survives because region selection genuinely uses it, and
# because stripping BY POSITION is the correct primitive if a text-based check
# is ever needed.


# --------------------------------------------------------------------------
# SINK -- typed by PARENT CONTEXT, so non-decisions are excluded structurally.
# --------------------------------------------------------------------------

#: Calls whose numeric arguments are saturation BOUNDS -- decision sinks that
#: contain no comparison operator at all, and are invisible to every
#: `if`-shaped gate in this tree.
_BOUND_CALLS = {"min", "max", "clip", "clamp", "bound", "np.clip", "numpy.clip"}

#: Calls whose numeric arguments are STRUCTURAL, not decisions: sizes, counts,
#: shapes, indices. Excluded by CONTEXT -- not by an exemption list of sites.
_STRUCTURAL_CALLS = {"range", "len", "reshape", "zeros", "ones", "empty", "full",
                     "arange", "linspace", "eye", "round", "enumerate", "repeat",
                     "seed", "default_rng", "RandomState"}


#: Calls and attributes that yield a COUNT. A comparison against one of these
#: is a cardinality test.
_COUNTING = {"len", "count", "size", "sum", "shape", "nnz", "numel"}


def _counts(node: ast.AST | None) -> bool:
    """Does this expression yield a CARDINALITY (a number of things) rather
    than a measured magnitude?"""
    if node is None:
        return False
    if isinstance(node, ast.Call):
        return _call_name(node) in _COUNTING
    if isinstance(node, ast.Attribute):
        return node.attr in _COUNTING
    return False


@dataclass
class Sink:
    kind: str          # compare | bound | coefficient
    lineno: int
    col: int
    expr: str          # the source segment of the sink expression
    operand: ast.AST   # the operand node whose provenance we trace
    sibling: ast.AST | None = None  # the OTHER side of a comparison


def _call_name(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def find_sinks(node: ast.AST, src: str) -> list[Sink]:
    """Every DECISION SINK in `node`, typed by the position it occupies.

    A sink is a position where a value changes what the program does. Array
    indices (`ast.Subscript.slice`), arities, `range()`/`len()`/shape
    arguments and RNG seeds are NOT sinks -- they are excluded because of
    WHERE THEY SIT, which is why this needs no exemption list. That is the fix
    for failure #2, and the reason it does not need the `ast.walk` pruning
    that failure's first fix wrongly attempted (`ast.walk` cannot prune;
    this classifies instead of pruning)."""
    sinks: list[Sink] = []

    # THE ARRAY-INDEX EXCLUSION THAT ISN'T HERE, and why its absence is the fix
    # ------------------------------------------------------------------------
    # The recorded failure was a gate that COUNTED ARRAY INDICES AS THRESHOLDS
    # -- 3 of 6 flagged sites false -- and whose first fix was also wrong,
    # because it tried to prune with `ast.walk`, which cannot prune.
    #
    # The obvious repair is a skip-set: collect everything under a
    # `Subscript.slice` and ignore it. This module HAD that, and a
    # by-construction probe showed it was doing nothing -- deleting it changed
    # no verdict on any of eleven non-threshold probes. The reason is that
    # typing the sink already solves it: an index literal is never a
    # COMPARISON OPERAND, so it is never a sink, so it is never traced. The
    # exclusion is structural and it happens one level up.
    #
    # Worse, the skip-set was not merely dead -- it was HARMFUL. `xs[i > 0.5]`
    # is a genuine threshold sitting inside a slice, and the skip-set silently
    # suppressed it. A defence against false positives that creates a false
    # NEGATIVE is a strictly bad trade, and it took a break-the-instrument
    # probe to see it, because reading the code it looks obviously correct.
    #
    # `_STRUCTURAL_CALLS` is retained below for the same reason it is named:
    # `range`/`len`/`zeros`/`default_rng` arguments are sizes and seeds, and
    # unlike slice contents they CAN reach a bound sink (`min(x, len(xs))`).
    skip: set[int] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and _call_name(n) in _STRUCTURAL_CALLS:
            for a in n.args:
                for sub in ast.walk(a):
                    skip.add(id(sub))

    def seg(x: ast.AST) -> str:
        return (ast.get_source_segment(src, x) or "").strip()

    for n in ast.walk(node):
        if id(n) in skip:
            continue
        # -- comparison operands. Covers EVERY syntactic host of a comparison:
        #    if / elif / while / ternary / comprehension guard / assert /
        #    return / assignment / boolean chain. We do not enumerate the
        #    hosts at all, which is exactly why none can be forgotten.
        #
        #    ONLY ORDERING comparisons (< <= > >=) are thresholds. `==` / `!=`
        #    / `is` / `in` are SENTINEL tests -- an exit code, an expected
        #    count, an emptiness check -- and a threshold is by definition a
        #    CUT POINT on an ordered quantity.
        #
        #    THIS NARROWING IS JUSTIFIED BY TWO MEASURED FALSE POSITIVES, and
        #    they are recorded here rather than in a changelog because a gate
        #    made less strict without its false positive attached is a gate
        #    that was QUIETED. Both came from auditing this module WITH
        #    ITSELF, which is how they were found at all:
        #      scripts/gate_inject.py:58   `found != count`  (count=1)
        #                                   -- an expected ARITY, not a cut point
        #      scripts/gate_inject.py:100  `proc.returncode == 0`
        #                                   -- a process EXIT SENTINEL
        #    Note this is a narrowing of the OPERATOR, which is structural,
        #    not an exemption list of SITES, which is what quieting looks like.
        if isinstance(n, ast.Compare):
            if any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in n.ops):
                operands = [n.left, *n.comparators]
                for i, operand in enumerate(operands):
                    others = [o for j, o in enumerate(operands) if j != i]
                    sinks.append(Sink("compare", n.lineno, n.col_offset, seg(n),
                                      operand, others[0] if others else None))
        # -- saturation bounds: min/max/clip arguments.
        elif isinstance(n, ast.Call) and _call_name(n) in _BOUND_CALLS:
            for a in n.args:
                sinks.append(Sink("bound", n.lineno, n.col_offset, seg(n), a))
    return sinks


# --------------------------------------------------------------------------
# SOURCE -- transitive closure over bindings, with an UNRESOLVED bucket.
# --------------------------------------------------------------------------


@dataclass
class Provenance:
    verdict: str                       # AUTHORED | MEASURED | ACCUMULATED | UNRESOLVED
    detail: str = ""
    chain: list[str] = field(default_factory=list)


#: Calls that constitute a MEASUREMENT: the value came from the graph, the
#: data, or the system's own statistics -- not from the author's hand.
_MEASURE_CALLS = {"node", "nodes", "neighbours", "attrs", "evaluate", "get_attr",
                  "mean", "std", "median", "percentile", "quantile", "var",
                  "sum", "count", "histogram", "read", "load", "loads"}


def _target_name(t: ast.AST) -> str:
    return t.id if isinstance(t, ast.Name) else "<aug>"


def _references(node: ast.AST, name: str) -> bool:
    """Does this bound expression READ the name it is bound to? That is the
    structural signature of an ACCUMULATION -- `x = x + C`, `x += C` (which
    `_Binder` records as `x + C`), `x = max(x, C)`. A plain reassignment
    (`x = 5`, `x = y`) does not, so it is NOT an accumulation."""
    return any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(node))


def _delta_operands(node: ast.AST, name: str) -> list[ast.AST]:
    """The operands of an accumulation that are NOT the self-reference -- the
    accumulated DELTA. For `x + C` -> `[C]`; for `max(x, C)` -> `[C]`. Used only
    to keep the accumulated literal REACHABLE in the reported detail; it never
    turns the accumulator itself into an authored value."""
    if isinstance(node, ast.BinOp):
        return [s for s in (node.left, node.right) if not _references(s, name)]
    if isinstance(node, ast.Call):
        return [a for a in node.args if not _references(a, name)]
    return []


class _Binder(ast.NodeVisitor):
    """Collects name -> bound-expression for a scope, plus default arguments,
    module-level constants and simple class attributes. This is the transitive
    part: `TAU = 0.5` then `if x > TAU` resolves through the binding, so
    NAMING A LITERAL NO LONGER HIDES IT."""

    def __init__(self) -> None:
        self.bindings: dict[str, list[ast.AST]] = {}

    def _bind(self, target: ast.AST, value: ast.AST) -> None:
        if isinstance(target, ast.Name):
            self.bindings.setdefault(target.id, []).append(value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for el in target.elts:
                self._bind(el, value)

    def visit_Assign(self, n: ast.Assign) -> None:
        for t in n.targets:
            self._bind(t, n.value)
        self.generic_visit(n)

    def visit_AnnAssign(self, n: ast.AnnAssign) -> None:
        if n.value is not None:
            self._bind(n.target, n.value)
        self.generic_visit(n)

    def visit_AugAssign(self, n: ast.AugAssign) -> None:
        # `x -= 1` binds x to `x - 1`, NOT to `1`. Binding to the bare RHS was
        # a real bug found by this module's own suite: it made `x` in
        # `while x > 0.5: x -= 1` trace to `literal 1`, so BOTH operands read
        # as authored and the comparison was discarded as constant-folded
        # dead code -- a threshold vanishing through a false trace, which is
        # the worst failure available to this instrument.
        self._bind(n.target, ast.BinOp(left=ast.Name(id=_target_name(n.target),
                                                     ctx=ast.Load()),
                                       op=n.op, right=n.value))
        self.generic_visit(n)

    def _defaults(self, n: ast.AST) -> None:
        a = n.args  # type: ignore[attr-defined]
        pos = list(a.posonlyargs) + list(a.args)
        for arg, default in zip(pos[len(pos) - len(a.defaults):], a.defaults):
            self.bindings.setdefault(arg.arg, []).append(default)
        for arg, default in zip(a.kwonlyargs, a.kw_defaults):
            if default is not None:
                self.bindings.setdefault(arg.arg, []).append(default)

    def visit_FunctionDef(self, n: ast.FunctionDef) -> None:
        self._defaults(n)
        self.generic_visit(n)

    def visit_AsyncFunctionDef(self, n: ast.AsyncFunctionDef) -> None:
        self._defaults(n)
        self.generic_visit(n)


def trace(expr: ast.AST, binder: _Binder, depth: int = 0,
          seen: set[str] | None = None) -> Provenance:
    """Trace a value BACKWARDS to its origin, through the binding graph.

    Terminates in exactly one of four states, and the last is the honest one:
      AUTHORED    -- a numeric literal the author wrote (possibly several
                     bindings away). A §13 finding.
      MEASURED    -- a graph/data read or a statistic of observed values. Fine.
      ACCUMULATED -- a name rebound from an expression that reads ITSELF
                     (`x = x + C`, `x += C`, `x = max(x, C)`). Its value is
                     init-plus-steps, a DERIVED quantity -- NOT a fixed authored
                     constant, so it must not read AUTHORED (which resolved it
                     to its initialiser and SUPPRESSED the real threshold on the
                     other side as dead code, and read a zero-init as a false
                     bound). The accumulated step stays reachable in `detail`.
      UNRESOLVED  -- could not be traced. COUNTED, NEVER DISCARDED. A tool that
                     silently calls this 'clean' is lying by omission.

    ON TERMINATION, AND ON A CONSTANT THIS FUNCTION USED TO CONTAIN
    ---------------------------------------------------------------
    The first version of this function guarded recursion with `if depth > 12`.
    Auditing this module WITH ITSELF flagged that `12` as AUTHORED-AT-SINK,
    and the accusation was correct: it was a hand-placed number that changed
    the verdict, chosen because it felt roomy. §13's instruction is not to
    tune such a number but to ask what it would FALL OUT of -- and the answer
    was NOTHING, which per §13 means the mechanism was incomplete, not that
    the knob needed a better value.

    It is now DELETED, because termination is already guaranteed structurally:
      * the NAME hop is the only step that jumps to another subtree, and
        `seen` admits each name at most once, so name hops are bounded by the
        number of distinct bindings -- a property of the input, not a choice;
      * every other step (UnaryOp, BinOp, Call arg) descends into a strictly
        smaller subtree of a finite AST.
    `depth` is retained as a reported diagnostic only; nothing branches on it.
    """
    seen = set() if seen is None else seen

    # A literal number the author wrote. Booleans are not thresholds.
    if isinstance(expr, ast.Constant):
        if isinstance(expr.value, bool) or expr.value is None:
            return Provenance("MEASURED", "boolean/None identity")
        if isinstance(expr.value, (int, float)):
            return Provenance("AUTHORED", f"literal {expr.value!r}")
        return Provenance("MEASURED", "non-numeric constant")

    if isinstance(expr, ast.UnaryOp):
        return trace(expr.operand, binder, depth + 1, seen)

    # Arithmetic on literals is still an authored number: `6 / 20` is 0.3 with
    # a costume on. Authored dominates -- if EITHER side is authored and the
    # other is not measured, the result is authored.
    if isinstance(expr, ast.BinOp):
        left = trace(expr.left, binder, depth + 1, seen)
        right = trace(expr.right, binder, depth + 1, seen)
        # Arithmetic ON an accumulated value is itself accumulated -- this is
        # what closes the `enc_cells / ncell > K` two-accumulator ratio: the
        # LEFT side is a derived quantity, so it must NOT read AUTHORED and let
        # the dead-code branch swallow the real threshold `K` on the right.
        if "ACCUMULATED" in (left.verdict, right.verdict):
            return Provenance("ACCUMULATED", "arithmetic on an accumulated value")
        if left.verdict == "AUTHORED" and right.verdict == "AUTHORED":
            return Provenance("AUTHORED", f"arithmetic on literals: {left.detail} / {right.detail}")
        if "UNRESOLVED" in (left.verdict, right.verdict):
            return Provenance("UNRESOLVED", "arithmetic with an untraced operand")
        return Provenance("MEASURED", "arithmetic involving a measurement")

    # A name: follow the binding. THIS is the transitive step that closes the
    # name-bound-literal hole. A name with several bindings is AUTHORED if ANY
    # binding is -- a threshold that is authored on one path is authored.
    if isinstance(expr, ast.Name):
        if expr.id in seen:
            return Provenance("UNRESOLVED", f"cyclic binding via {expr.id}")
        bindings = binder.bindings.get(expr.id)
        if not bindings:
            return Provenance("UNRESOLVED", f"free name {expr.id!r} (parameter or import)")
        # ACCUMULATION -- the fix for the FIRST-BINDING trace bug. If ANY binding
        # of this name READS the name itself (`x = x + C`, `x += C`,
        # `x = max(x, C)`), the name is an ACCUMULATOR: its value is init-plus-
        # steps, a DERIVED quantity, NEVER a fixed authored constant. Resolving
        # it to its initialiser literal (`x = 0`) is exactly what let a tuned
        # threshold on an accumulated value be SUPPRESSED as "both sides
        # authored => dead code", and made an accumulator's zero-init a FALSE
        # bound. So an accumulator is ACCUMULATED, and the initialiser no longer
        # stands in for it. The accumulated DELTA stays reachable in the detail
        # (so the literal is not lost), but the accumulator is not AUTHORED.
        accs = [b for b in bindings if _references(b, expr.id)]
        if accs:
            deltas = []
            for b in accs:
                for operand in _delta_operands(b, expr.id):
                    deltas.append(trace(operand, binder, depth + 1, seen | {expr.id}))
            lit = next((d.detail for d in deltas if d.verdict == "AUTHORED"), None)
            detail = f"{expr.id} accumulates" + (f" (step {lit})" if lit else "")
            return Provenance("ACCUMULATED", detail, [expr.id])
        results = [trace(b, binder, depth + 1, seen | {expr.id}) for b in bindings]
        for r in results:
            if r.verdict == "AUTHORED":
                return Provenance("AUTHORED", f"{expr.id} -> {r.detail}",
                                  [expr.id, *r.chain])
        if any(r.verdict == "UNRESOLVED" for r in results):
            return Provenance("UNRESOLVED", f"{expr.id} -> untraced")
        return Provenance("MEASURED", f"{expr.id} -> measured")

    if isinstance(expr, ast.Call):
        name = _call_name(expr)
        if name in _MEASURE_CALLS:
            return Provenance("MEASURED", f"{name}() reads the system")
        # `float(0.5)`, `int(3)` -- a cast does not launder a literal.
        if name in {"float", "int", "abs", "round"} and expr.args:
            inner = trace(expr.args[0], binder, depth + 1, seen)
            # A `.get(k, DEFAULT)` inside a cast: the DEFAULT is a fill, not a
            # threshold -- the cast's value is the graph read. Traced via arg 0.
            return inner
        return Provenance("UNRESOLVED", f"call {name or '<expr>'}()")

    # `attrs["phub"]` / `cfg[0]` -- a read. Whether it is a MEASUREMENT depends
    # on what is being subscripted, which we cannot always know.
    if isinstance(expr, ast.Subscript):
        return Provenance("MEASURED", "subscript read")

    if isinstance(expr, ast.Attribute):
        return Provenance("UNRESOLVED", f"attribute .{expr.attr}")

    return Provenance("UNRESOLVED", type(expr).__name__)


# --------------------------------------------------------------------------
# The audit.
# --------------------------------------------------------------------------


@dataclass
class Finding:
    file: str
    lineno: int
    kind: str
    expr: str
    verdict: str
    detail: str
    tier: str = "T1"


#: Float-equality guards. An epsilon is not a chosen cut point -- it is a
#: statement about machine precision, and it falls out of the float format.
_EPSILONS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8, 1e-9, 1e-10, 1e-12)


def _tier(sink: Sink, prov: Provenance) -> str:
    """Grade HOW STRONG the §13 claim against a finding is.

    THIS IS TIERING, NOT FILTERING, AND THE DIFFERENCE IS THE WHOLE POINT.
    Sweeping the vision adapters with an untiered version of this tool
    produced a flood in which `max(1, h - rf + 1)`, `np.clip(a, 0, 255)` and
    `abs(shear) > 1e-3` sat beside a genuine tuned cut point, all shouting
    equally. **A gate that cries wolf gets ROUTED AROUND, which is worse than
    no gate** -- so an untiered flood is a broken instrument even though every
    line in it is literally true.

    The tempting repair is to exclude the noisy shapes. That would be quieting,
    and it would eventually swallow a real threshold hiding in a clamp. So
    nothing is excluded; findings are GRADED, all of them are reported, and
    the grade is defended structurally:

      T1  A CHOSEN CUT POINT -- an ordering comparison against a literal that
          is neither the origin nor an epsilon. This is what §13 is about: a
          number fixed by the answer the author wanted.
      T2  A BOUND -- a min/max/clip argument. Usually a representation limit
          (`clip(a, 0, 255)` is the byte range, not a decision) but a tuned
          saturation point hides here, so it is reported, not dropped.
      T3  AN ORIGIN OR EPSILON TEST -- comparison against 0, or against a
          float epsilon. `x > 0` is a SIGN or EMPTINESS test and 0 is not
          chosen, it is the identity; `abs(d) > 1e-9` is a statement about
          the float format. Almost never a §13 violation, never silently
          dropped.

    A reader who wants the §13 headline reads T1. A reader auditing the
    instrument reads all three, which is the only way T2 and T3 can ever be
    shown to have been graded wrongly.
    """
    # CARDINALITY. `len(pairs) > 1`, `if ok.sum() < 3` -- comparing a COUNT
    # against a small integer asks "do I have enough items", which is a
    # structural minimum, not a tuned cut point on a measured signal.
    #
    # This category was not invented here. `tests/test_motion_sensor_gate_
    # migrated.py` carries a `CARDINALITY_NAMES` list for exactly this, with a
    # written derivation per entry and its length pinned by an assertion so
    # growth is loud. Two instruments reaching the same category independently
    # is the reason it is graded rather than guessed at -- and the difference
    # here is that this one recognises cardinality STRUCTURALLY (the sibling
    # operand is a count) instead of by a list of names that a seventh
    # spelling walks past.
    if sink.kind == "compare" and _counts(sink.sibling):
        return "T3"
    if sink.kind == "bound":
        return "T2"
    # The literal at the END of the binding chain is the value in question --
    # `shear -> literal 0.0` must grade on the 0.0, not on the name in front
    # of it. Matching the whole detail string missed every chained case, which
    # is how parameter defaults were arriving graded as tuned cut points.
    tail = prov.detail.rsplit("->", 1)[-1].strip()
    if tail.startswith("literal "):
        val = tail[len("literal "):].strip()
        try:
            num = abs(float(val))
        except ValueError:
            return "T1"
        if num == 0.0:
            return "T3"                       # the origin: a sign/emptiness test
        if num <= max(_EPSILONS):
            return "T3"                       # a float-format epsilon
    return "T1"


def audit_source(src: str, filename: str = "<src>",
                 qualname: str | None = None) -> tuple[list[Finding], list[Finding]]:
    """Audit source for authored values reaching decision sinks.

    Returns (authored, unresolved). The SECOND is not a footnote: a caller
    that reports the first and drops the second has built exactly the
    confidently-blind instrument this module was written against.
    """
    tree = ast.parse(src)
    binder = _Binder()
    binder.visit(tree)                      # bindings from the WHOLE module,
    region: ast.AST = tree                  # so module constants resolve.
    if qualname is not None:
        region = resolve(tree, qualname)    # by AST identity, never substring
    # (no docstring strip -- see the note above `Sink`: prose cannot produce
    #  an AST sink, so the class is dissolved rather than defended against.)

    authored: list[Finding] = []
    unresolved: list[Finding] = []

    # ONE FINDING PER SINK, NOT PER OPERAND -- and the reason is a measured
    # defect in this function's first version.
    #
    # `find_sinks` emits an operand at a time, so `abs(shear) > 1e-3` arrived
    # as TWO findings and each was graded on its own: the epsilon graded T3
    # correctly, while `shear -> literal 0.0` graded T1 and read as a tuned cut
    # point. It is nothing of the kind -- it is a PARAMETER DEFAULT, a knob
    # whose off-position happens to be zero.
    #
    # A comparison has at most ONE cut point, and it is the side that is
    # authored while the other side is not. When BOTH sides are authored the
    # comparison is constant-folded dead code, not a threshold; when the
    # authored side traces to a parameter default it is a default, not a cut.
    # Grading the SINK rather than the OPERAND is what makes those
    # distinguishable at all.
    by_sink: dict[tuple[int, int, str], list[tuple[Sink, Provenance]]] = {}
    for sink in find_sinks(region, src):
        by_sink.setdefault((sink.lineno, sink.col, sink.expr), []).append(
            (sink, trace(sink.operand, binder)))

    for (lineno, _col, expr), pairs in sorted(by_sink.items()):
        authored_sides = [(s, p) for s, p in pairs if p.verdict == "AUTHORED"]
        unresolved_sides = [(s, p) for s, p in pairs if p.verdict == "UNRESOLVED"]
        accumulated = any(p.verdict == "ACCUMULATED" for _, p in pairs)
        if authored_sides:
            # Both sides authored => constant comparison, no cut point. This must
            # NOT fire when either side is an ACCUMULATION: an accumulator is a
            # derived quantity, not a constant fold, so `x += C; if x > K` has a
            # real cut point at K and the comparison is NOT dead code. (The
            # `authored_sides == pairs` test already excludes an ACCUMULATED
            # operand, since ACCUMULATED is not AUTHORED; this makes it explicit
            # so the invariant is legible at the branch that used to swallow K.)
            if len(authored_sides) == len(pairs) and pairs[0][0].kind == "compare" \
                    and len(pairs) > 1 and not accumulated:
                continue
            s, p = authored_sides[0]
            authored.append(Finding(filename, lineno, s.kind, expr,
                                    p.verdict, p.detail, _tier(s, p)))
        elif unresolved_sides:
            s, p = unresolved_sides[0]
            unresolved.append(Finding(filename, lineno, s.kind, expr,
                                      p.verdict, p.detail, "T-UNRESOLVED"))
    return authored, unresolved


# --------------------------------------------------------------------------
# THE SECOND INVARIANT IN THIS TREE -- "the adapter takes NO DECISION over
# graph state" (CLAUDE.md's architecture rule) -- checked the SAME WAY.
# --------------------------------------------------------------------------
#
# It is the same shape as the §13 invariant and it fails the same three ways:
#
#     NO PATH RUNS FROM A GRAPH READ TO A CONDITION.
#
# SOURCE is a graph read (`s.node(x)`, `.get_attr(...)`, `["attrs"]`) instead
# of an author-written literal; SINK is a CONDITION instead of a threshold
# operand. The approximations are identical, and so are the fixes:
#
#   * SOURCE by a TOKEN -- `"get_attr" in ast.dump(node)` is defeated by
#     `v = s.node(x)["attrs"]["a"]` then `if v > 0`, which is EXACTLY the
#     defect measured at the paint gate (probe P4). Fixed by reusing `_Binder`,
#     so the binding chain is followed.
#   * SINK by a CONTEXT -- enumerating `ast.If` alone misses `while`, a
#     ternary, an `assert` and a comprehension guard. Fixed by enumerating the
#     TEST POSITION of every conditional construct the grammar has, which is a
#     closed list in the `ast` module rather than a guess.
#   * REGION by a SUBSTRING -- `"node(" in ast.dump(...)` is the terminal case:
#     **`ast.dump` renders `s.node(x)` as `attr='node'`, so the substring
#     `node(` CANNOT OCCUR IN ITS OUTPUT FOR ANY PROGRAM.** That predicate was
#     load-bearing in `tests/test_verdict_comparator_migrated.py` and had never
#     been able to fire. Fixed by matching the CALLED NAME on the AST node.
#
# One narrowing, shipped with the false positive that justifies it (§12.4 of
# the proposed amendments -- a loosening without its false positive is a gate
# that was QUIETED): the scope of the check is the condition's TEST, not the
# whole `if` subtree. `ast.dump(node)` on an `ast.If` includes its BODY, so the
# incumbent predicate would have flagged `if flag: x = s.node(a)` -- a
# conditional that does not branch ON graph state, it merely reads inside one.
# Measured false positive, in the file this gate audits:
#   domains/verdict_comparator_world.py:397  `for ... : at = self.s.node(grp)`
# sits inside `read()`, and any `if` wrapped around a read-back loop would be
# flagged by the subtree form while branching on nothing.
# This narrows the POSITION (structural), not a list of SITES (quieting) -- and
# it is a net STRENGTHENING: the name-bound, `while`, ternary, `assert` and
# comprehension-guard spellings all become visible, and none of them were.

#: Reads that return graph state. A CONDITION downstream of one of these is a
#: Python decision over the graph.
_GRAPH_READS = {"node", "nodes", "get_attr", "attrs", "node_attrs", "edges",
                "neighbours", "neighbors", "in_neighbours", "out_neighbours",
                "evaluate", "eval_term"}


def condition_tests(fn: ast.AST) -> list[ast.AST]:
    """Every TEST POSITION inside `fn` -- the closed list of conditional
    constructs Python's grammar has, not an enumeration someone remembered.

    `ast.If` alone is what every incumbent gate in this tree checks, and it is
    blind to four of these five."""
    tests: list[ast.AST] = []
    for n in ast.walk(fn):
        if isinstance(n, (ast.If, ast.IfExp, ast.While)):
            tests.append(n.test)
        elif isinstance(n, ast.Assert):
            tests.append(n.test)
        elif isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for gen in n.generators:
                tests.extend(gen.ifs)
    return tests


def reads_graph(expr: ast.AST, binder: _Binder, seen: set[str] | None = None) -> str | None:
    """Does `expr` trace back to a graph read? Returns the chain, or None.

    Transitive over bindings -- this is what makes binding the read to a name
    stop hiding it. Termination is structural, exactly as in `trace`: `seen`
    admits each name once, every other step descends a finite AST."""
    seen = set() if seen is None else seen
    if isinstance(expr, ast.Call):
        name = _call_name(expr)
        if name in _GRAPH_READS:
            return f"{name}()"
    if isinstance(expr, ast.Attribute) and expr.attr in _GRAPH_READS:
        return f".{expr.attr}"
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str) \
            and expr.value in _GRAPH_READS:
        # `d["attrs"]` -- the subscript KEY is how graph attrs are reached.
        return f'["{expr.value}"]'
    if isinstance(expr, ast.Name):
        if expr.id in seen:
            return None
        for b in binder.bindings.get(expr.id, []):
            hit = reads_graph(b, binder, seen | {expr.id})
            if hit:
                return f"{expr.id} -> {hit}"
        return None
    for child in ast.iter_child_nodes(expr):
        hit = reads_graph(child, binder, seen)
        if hit:
            return hit
    return None


def graph_decision_findings(src: str, exempt: frozenset[str] | set[str] = frozenset(),
                            ) -> list[tuple[str, int, str, str]]:
    """(function, lineno, test-source, chain) for every CONDITION that traces
    back to a graph read, outside `exempt` functions."""
    tree = ast.parse(src)
    binder = _Binder()
    binder.visit(tree)
    out: list[tuple[str, int, str, str]] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if fn.name in exempt:
            continue
        for test in condition_tests(fn):
            chain = reads_graph(test, binder)
            if chain:
                out.append((fn.name, test.lineno,
                            (ast.get_source_segment(src, test) or "").strip(), chain))
    return out


def report(path: str, qualname: str | None = None) -> str:
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    authored, unresolved = audit_source(src, path, qualname)
    lines = [f"{path}{'::' + qualname if qualname else ''}",
             f"  AUTHORED-AT-SINK: {len(authored)}    UNRESOLVED: {len(unresolved)}"]
    for f in authored:
        lines.append(f"  ! {f.file}:{f.lineno}  [{f.kind}]  {f.expr}    <- {f.detail}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        p, _, q = arg.partition("::")
        print(report(p, q or None))
