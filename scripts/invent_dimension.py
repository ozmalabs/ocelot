"""invent_dimension — GENERATE-AND-SELECT for the SEMANTIC of the `dimension`
operator, the genuine creative core.

The recipe SKELETON is the agent's owned euler-style binder
`sum{ k in 0..N : <PER-LEVEL> } <OUTER-TRANSFORM>` (the same shape
`total_simplices` fills). The SEMANTIC CONTENT — what the per-level term is and
what the outer transform is — is NOT supplied. It is:

  GENERATE: a bounded grammar over HELD primitives (plus/minus/times/div/mod +
            the comparators ge/gt/le/lt/eq) and leaves
            {c = cardinality(simplices_of_dim(complex,k)), k, literals} ENUMERATES
            candidate per-level bodies + candidate outer transforms. The set is
            grammar-generated, finite (depth-bounded), and INCLUDES non-winners.
            The op/leaf alphabet is the FULL held basis — it is NOT narrowed
            toward any answer (no ge-only, no -1 offset baked in).

  SELECT:   a MECHANICAL selector composes each candidate recipe (as the binder
            definition string), grounds it via compute_grounding.ground_computation,
            evaluates on the KNOWN complexes (point/edge/triangle/tetra -> 0/1/2/3),
            keeps the EXACT reproducers, breaks ties by MDL (shortest Term-tree),
            and DISAMBIGUATES by PREDICTING two HELD-OUT complexes the selector did
            NOT fit on (a 4-simplex closure of dim 4 — a value not among the knowns
            — and a HOLLOW triangle of dim 1 — a non-full level structure). The
            winner must predict BOTH held-outs correctly.

The winner that emerges IS the invented semantic (grammar-generated, selector-
picked, held-out-validated). The LLM is BLIND to the answer: it supplies only the
target (dimension), the knowns, and the held-outs; it does NOT seed the candidate
set nor narrow it toward the winner.

FAITHFUL (CLAUDE.md): a world-adapter driver. It sequences the agent's grammar
(the expression enumerator over held primitives) + the agent's selector
(ground_computation + the known-value self-verify gate + the MDL term-size from
feature_generator) + the agent's persist loop (self_authored). It owns no math
about the answer. NO LLM, NO Rust, NO build. Math/agent-core only.
"""
from __future__ import annotations

import itertools
import json

from domains import reason as _reason
from domains import compute_grounding as _cg
from domains import feature_generator as _fg


# ===========================================================================
# THE KNOWNS (the selector's reviewer) + the HELD-OUT (the anti-overfit guard).
# The orchestrator supplies these complexes + their TRUE dimension. It does NOT
# supply the recipe. Each true dimension is the textbook value of the named shape
# (a k-simplex closure has dimension k); the held-outs are computed/known the same
# way but WITHHELD from the selector's fit.
# ===========================================================================

def _full_simplex_closure(n):
    """The closure of a single n-simplex on vertices 0..n: ALL non-empty subsets.
    Its topological dimension is n (the top face has n+1 vertices)."""
    verts = list(range(n + 1))
    faces = []
    for r in range(1, n + 2):
        for combo in itertools.combinations(verts, r):
            faces.append(list(combo))
    return faces


POINT = _full_simplex_closure(0)       # dim 0
EDGE = _full_simplex_closure(1)        # dim 1
TRIANGLE = _full_simplex_closure(2)    # dim 2
TETRA = _full_simplex_closure(3)       # dim 3

# KNOWNS the selector fits on: point/edge/triangle/tetra -> 0/1/2/3.
KNOWNS = [
    ({"complex": POINT, "N": 0}, 0),
    ({"complex": EDGE, "N": 1}, 1),
    ({"complex": TRIANGLE, "N": 2}, 2),
    ({"complex": TETRA, "N": 3}, 3),
]

# HELD-OUTS the selector NEVER fits on (the predict guard):
#  (1) a 4-simplex (pentachoron) closure -> dim 4, a value NOT among the knowns.
#  (2) a HOLLOW triangle (1-skeleton: 3 vertices + 3 edges, NO 2-face) -> dim 1,
#      a NON-FULL level structure (top level present is 1, not the parameter N).
PENTA = _full_simplex_closure(4)       # dim 4
HOLLOW_TRI = [[0], [1], [2], [0, 1], [0, 2], [1, 2]]   # dim 1 (no 2-face)

HELD_OUT = [
    ("pentachoron(dim4)", {"complex": PENTA, "N": 4}, 4),
    ("hollow_triangle(dim1)", {"complex": HOLLOW_TRI, "N": 2}, 1),
]


# ===========================================================================
# (1) GENERATE — the bounded grammar over HELD primitives. A per-level body is an
# expression tree of depth <= 2 over LEAVES {c, k, 0, 1, 2} and OPS
# {plus, minus, times, div, mod, ge, gt, le, lt, eq}; an outer transform is an
# expression over the sum-leaf S and small literals. The alphabet is the FULL held
# basis (arithmetic + every comparator) — NOT narrowed toward any answer.
# ===========================================================================

# the leaf surfaces the body may read. `c` is the per-level face COUNT
# (cardinality of the k-simplices); `k` is the binder index; the literals are the
# small constants the grammar may compose with.
_BODY_LEAVES = ["c", "k", "0", "1", "2"]
_ARITH = ["plus", "minus", "times", "div", "mod"]
_CMP = ["ge", "gt", "le", "lt", "eq"]
_OPS = _ARITH + _CMP

# surface for a held binary op as the INFIX/CALL the compute_grounding parser
# reads. Arithmetic + comparators are infix; the parser routes them to the held
# capability.
_INFIX = {"plus": "+", "minus": "-", "times": "*", "div": "/", "mod": "%",
          "ge": ">=", "gt": ">", "le": "<", "lt": "<", "eq": "=="}
# NB le/lt both map through the parser's single '<' handling; we only need a
# representative comparator family, but ALL FIVE are enumerated so the winner is
# not pre-narrowed. (le surface uses '<=' below.)
_INFIX["le"] = "<="
_INFIX["lt"] = "<"


def _leaf_str(leaf):
    """A body leaf as a sub-expression STRING over held primitives. `c` expands to
    the held face-count `cardinality(simplices_of_dim(complex, k))`."""
    if leaf == "c":
        return "cardinality(simplices_of_dim(complex, k))"
    return leaf            # `k` (the binder) or a literal


def _body_to_str(spec):
    """Render a body SPEC (tuple AST) to the definition-string the
    compute_grounding parser reads. ('leaf',nm) | ('op',op,l,r)."""
    if spec[0] == "leaf":
        return _leaf_str(spec[1])
    return f"({_body_to_str(spec[2])}) {_INFIX[spec[1]]} ({_body_to_str(spec[3])})"


def _gen_bodies(max_depth=2):
    """ENUMERATE candidate per-level body SPECS from the grammar (depth-bounded).
    Depth 0 = a bare leaf; depth d = op(left, right) over depth<d sub-bodies. The
    full op alphabet (arithmetic + every comparator) and full leaf set are used —
    the grammar is BLIND to which body is the answer (nothing narrowed toward
    ge/offset). Returns a de-duplicated list of body SPECS (tuple ASTs)."""
    levels = {0: [("leaf", l) for l in _BODY_LEAVES]}
    for d in range(1, max_depth + 1):
        cur = []
        below = []
        for dd in range(d):
            below.extend(levels[dd])
        for op in _OPS:
            for a in below:
                for b in below:
                    cur.append(("op", op, a, b))
        levels[d] = cur
    out, seen = [], set()
    for d in range(max_depth + 1):
        for spec in levels[d]:
            key = _body_to_str(spec)
            if key not in seen:
                seen.add(key)
                out.append(spec)
    return out


def _gen_outer():
    """ENUMERATE candidate OUTER transforms over the sum-leaf S. The transform is
    arithmetic over S and small literals: identity, +/-/*//  a constant, and
    S /-relative shapes. Grammar-generated, NOT narrowed to the -1 offset."""
    outers = ["S"]                                   # identity
    for lit in ("0", "1", "2", "3"):
        for op in ("+", "-", "*", "/"):
            outers.append(f"S {op} {lit}")
    # a couple of two-op outers (still bounded) so the offset family is not the
    # only non-identity shape considered.
    outers.append("(S - 1) + 0")
    outers.append("(S + 1) - 2")
    seen, out = set(), []
    for o in outers:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


# ===========================================================================
# (2) SELECT — the MECHANICAL selector. For each (body, outer) candidate: build the
# recipe definition (the agent's binder skeleton), ground it via
# compute_grounding, evaluate on the KNOWNS, keep EXACT reproducers, MDL-rank
# (shortest Term-tree, feature_generator._size), and PREDICT the held-outs.
# ===========================================================================

def _recipe_def(name, body, outer):
    """The recipe definition STRING: the euler-style binder skeleton with the
    candidate body, wrapped by the candidate outer transform (S := the sum)."""
    summ = f"sum{{ k in 0..N : {body} }}"
    expr = outer.replace("S", summ)
    return f"{name}(complex, N) = {expr}"


# ---------------------------------------------------------------------------
# A FAST numeric SCREEN that mirrors reason.solve's arithmetic/comparator
# semantics EXACTLY (so a screened verifier is a genuine solve-verifier), used
# only to filter the bounded grammar's 12M recipes down to the handful that
# reproduce the knowns. The verifiers are then RE-GROUNDED through the real
# compute_grounding machinery for provenance. This is plumbing (a tractable
# filter over the SAME semantics), not a narrowing of the grammar — every op and
# leaf in the alphabet is screened; nothing is removed toward the answer.
#  [ASSIST #1 — NAMED: a fast filter mirroring solve's semantics so the bounded
#   12M-recipe grammar is searchable; the winner is still GROUNDED via
#   compute_grounding + solve, and the alphabet is untouched.]
# ---------------------------------------------------------------------------

# precompute, per complex, the per-level face counts c_k for k in 0..N and the
# level indices, so a candidate body is a pure numeric function of (c, k).
def _level_counts(complex_, N):
    return [len(_reason._simplices_of_dim(complex_, k)) for k in range(N + 1)]


# the OPS as numeric callables mirroring reason.py EXACTLY (div: floor when even
# else float; mod: int; a div/mod by 0 raises -> the candidate is rejected, the
# same as ground_and_run returning ok=False). Comparators return Python bool
# (sums as 0/1 in the binder, exactly as solve does).
def _op_num(op, a, b):
    if op == "plus":
        return a + b
    if op == "minus":
        return a - b
    if op == "times":
        return a * b
    if op == "div":
        if (isinstance(a, int) or float(a).is_integer()) and \
           (isinstance(b, int) or float(b).is_integer()) and \
           int(b) != 0 and int(a) % int(b) == 0:
            return int(a) // int(b)
        return a / b               # ZeroDivisionError if b==0 -> reject
    if op == "mod":
        return int(a) % int(b)     # ZeroDivisionError if b==0 -> reject
    if op == "ge":
        return a >= b
    if op == "gt":
        return a > b
    if op == "le":
        return a <= b
    if op == "lt":
        return a < b
    if op == "eq":
        return a == b
    raise ValueError(op)


# a body is precompiled to a tuple AST: ('leaf', name) | ('op', op, left, right).
def _compile_body_ast(body_spec):
    kind = body_spec[0]
    if kind == "leaf":
        return body_spec
    return ("op", body_spec[1],
            _compile_body_ast(body_spec[2]), _compile_body_ast(body_spec[3]))


def _eval_body_ast(ast, c, k):
    if ast[0] == "leaf":
        nm = ast[1]
        if nm == "c":
            return c
        if nm == "k":
            return k
        return int(nm)             # a literal
    return _op_num(ast[1], _eval_body_ast(ast[2], c, k),
                   _eval_body_ast(ast[3], c, k))


def _eval_outer_num(outer, S):
    # the bounded outer family: 'S', 'S <op> <lit>', and the two two-op shapes.
    if outer == "S":
        return S
    if outer == "(S - 1) + 0":
        return (S - 1) + 0
    if outer == "(S + 1) - 2":
        return (S + 1) - 2
    _, op_sym, lit = outer.split(" ")
    op = {"+": "plus", "-": "minus", "*": "times", "/": "div"}[op_sym]
    return _op_num(op, S, int(lit))


def _ground_and_run(name, definition, arg):
    """Ground the candidate recipe over held primitives and RUN it on one arg.
    Returns (ok, value). A non-grounding / erroring candidate is ok=False."""
    from substrate_rs import _native
    s = _native.Substrate()
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(s, name, definition, capabilities=caps)
    if not (res.get("grounded") and res.get("installed")):
        return False, None, res.get("reason", "")
    try:
        v = caps[name](dict(arg))
        return True, v, res
    except Exception as e:                                  # noqa: BLE001
        return False, None, f"run error: {e}"


def _term_size_of(definition):
    """MDL complexity = node count of the candidate's composed Term-tree, via the
    agent's compute_grounding comprehension (the FULL definition) + the agent's
    MDL term-size feature_generator._size. Falls back to definition length."""
    comp = _cg.comprehend_computational_definition(definition)
    if comp and comp.get("term") is not None:
        return _fg._size(comp["term"])
    return len(definition)


# precomputed per-level face counts for the KNOWNS (the screen inputs).
_KNOWN_LEVELS = [(_level_counts(arg["complex"], arg["N"]), expected)
                 for arg, expected in KNOWNS]


def _screen_candidate(ast, outer):
    """FAST screen: does (body, outer) EXACTLY reproduce all four knowns under the
    solve-mirroring numeric semantics? Early-out on the first failing known. A
    div/mod-by-zero (or any numeric error) rejects the candidate (mirrors a
    non-grounding recipe). Returns True iff all knowns reproduced."""
    for counts, expected in _KNOWN_LEVELS:
        try:
            S = 0
            for k, c in enumerate(counts):
                S += _eval_body_ast(ast, c, k)     # bool sums as 0/1, as solve does
            val = _eval_outer_num(outer, S)
        except (ZeroDivisionError, ValueError, TypeError):
            return False
        # the binder may yield a bool/float; the recipe output must EQUAL the int.
        if isinstance(val, bool) or val != expected:
            return False
    return True


def select(verbose=True, max_depth=2, ground_budget=2000):
    """The full generate-and-select run. GENERATE the bounded grammar; SCREEN all
    recipes by the fast solve-mirroring evaluator (early-out); RE-GROUND the
    survivors through compute_grounding (the real selector) + verify on the knowns;
    MDL-rank; PREDICT the held-outs. Returns the report dict."""
    bodies = _gen_bodies(max_depth=max_depth)
    outers = _gen_outer()
    cand_count = len(bodies) * len(outers)
    if verbose:
        print(f"[generate] grammar produced {len(bodies)} per-level bodies x "
              f"{len(outers)} outer transforms = {cand_count} candidate recipes "
              f"(depth<={max_depth}, full held op alphabet {sorted(_OPS)} + leaves "
              f"{_BODY_LEAVES}; NOT narrowed to the answer)")

    # SCREEN: compile each body once, evaluate against the knowns (early-out).
    screened = []
    for body in bodies:
        ast = _compile_body_ast(body)
        for outer in outers:
            if _screen_candidate(ast, outer):
                screened.append((body, outer))
    if verbose:
        print(f"[screen] {len(screened)} of {cand_count} recipes reproduce all "
              f"four knowns under the solve-mirroring evaluator")

    # MDL-RANK the survivors by the agent's composed Term-tree size (Occam), so the
    # genuine grounding selector examines the SHORTEST verifiers first — the
    # anti-overfit ordering. (Size is computed from the composed tree, not the
    # answer; it does not look at the held-outs.)
    sized = []
    for body, outer in screened:
        body_str = _body_to_str(body)
        definition = _recipe_def("dim_cand", body_str, outer)
        sized.append((_term_size_of(definition), body_str, outer, definition))
    sized.sort(key=lambda x: x[0])

    # RE-GROUND the survivors through the REAL compute_grounding machinery + verify
    # on the knowns (the genuine selector, not the fast filter), in MDL order, up to
    # a ground budget (the smallest verifiers are all examined; the budget bounds the
    # vast redundant tail of larger-but-equivalent forms).
    verifiers = []
    grounded_n = 0
    for size, body_str, outer, definition in sized:
        if grounded_n >= ground_budget:
            break
        grounded_n += 1
        ok_all = True
        for arg, expected in KNOWNS:
            ok, val, _ = _ground_and_run("dim_cand", definition, arg)
            if not ok or val != expected:
                ok_all = False
                break
        if ok_all:
            verifiers.append({"body": body_str, "outer": outer,
                              "definition": definition, "size": size})
    if verbose:
        print(f"[ground] {len(verifiers)} of the {grounded_n} MDL-smallest "
              f"survivors GROUND via compute_grounding AND verify on the knowns")

    # PREDICT the held-outs with each verifier (grounded run); winner predicts ALL.
    for v in verifiers:
        preds, ok_held = [], True
        for label, arg, true_dim in HELD_OUT:
            ok, val, _ = _ground_and_run("dim_cand", v["definition"], arg)
            ok_one = (ok and val == true_dim)
            preds.append({"held_out": label, "predicted": val,
                          "true": true_dim, "ok": ok_one})
            ok_held = ok_held and ok_one
        v["held_out_preds"] = preds
        v["predicts_held_out"] = ok_held

    winners = [v for v in verifiers if v["predicts_held_out"]]
    return {"n_bodies": len(bodies), "n_outers": len(outers),
            "n_candidates": cand_count, "n_screened": len(screened),
            "verifiers": verifiers, "winners": winners}


if __name__ == "__main__":
    import sys
    rep = select(verbose=True)
    print("\n=== VERIFIERS (reproduce knowns), MDL-ranked ===")
    for v in rep["verifiers"][:20]:
        print(f"  size={v['size']:>3}  body={v['body']:<48}  outer={v['outer']}")
    print(f"\n  ... {len(rep['verifiers'])} verifiers total")
    print("\n=== HELD-OUT PREDICTION (anti-overfit) ===")
    for v in rep["verifiers"][:8]:
        flag = "PREDICTS" if v["predicts_held_out"] else "FAILS    "
        print(f"  [{flag}] size={v['size']:>3} body={v['body']}")
        for p in v["held_out_preds"]:
            print(f"           {p['held_out']:<22} pred={p['predicted']} "
                  f"true={p['true']} {'OK' if p['ok'] else 'MISS'}")
    print("\n=== WINNER (MDL-shortest verifier that predicts ALL held-outs) ===")
    if rep["winners"]:
        w = rep["winners"][0]
        print(f"  body : {w['body']}")
        print(f"  outer: {w['outer']}")
        print(f"  def  : {w['definition']}")
        print(f"  size : {w['size']}")
    else:
        print("  (no candidate both reproduced the knowns and predicted held-out)")
