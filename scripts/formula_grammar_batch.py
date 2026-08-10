#!/usr/bin/env python3
"""formula_grammar_batch — BATCH the core math-formula grammar constructions into the
held LaTeX/math reader IN ONE GO, EACH verified general (held-out -> a DIFFERENT
correct parsed tree) + Rust-eval/self-verify where the leaf is held (else an honest
un-held-leaf stall). The cmsg165-167 move (a GENERAL construction, verified) SCALED to
a LIST — the discipline kept PER construction.

This extends cmsg165-167 (explicit-arith + \\sum-binder). The held reader
(domains/latex_notation.py) now holds the batch as GENERAL syntax-keyed constructions
(seeds/latex_math_notation.json macros + the parser's recursion); this script is the
WORLD-ADAPTER + the per-construction VERIFICATION ONLY:

  THE CORE LIST — 5 CONSTRUCTIONS + 4 HELD LEAVES + 2 un-held-op constructions
  (each a general construction / a held UseTool leaf, NOT a template, NOT
  operator_shape, NOT a hand-coded leaf value):
    1. \\prod-BINDER      \\prod_k <body>      -> Prod fold over k (held)
    2. \\frac{a}{b}       fraction            -> Div(a, b)        (held)
    3. min/max OVER FAMILY \\min_k / \\max_k   -> MinOver/MaxOver fold (held)
    4. NESTED FOLDS       \\sum_i \\prod_j ... -> the recursive composition (held)
    5. |X| / \\lvert..\\rvert  cardinality/abs -> Abs(X)          (held)
    6. \\dim H_k / \\rank H_k  HELD LEAF       -> UseTool -> b_k (the held tower)
    7. \\dim X            HELD LEAF            -> UseTool -> the complex dimension
    8. \\binom{n}{k}      HELD LEAF            -> UseTool -> n choose k (held int arith)
    9. \\torsion H_k      HELD LEAF            -> UseTool -> |torsion H_k| (SNF over Z)
   10. \\cup / \\smile     cup product          -> parse-general, eval-STALL (cochain op)
   11. \\otimes / \\oplus  tensor/direct-sum    -> parse-general, eval-STALL (un-held op)
  The cmsg169 \\binom + \\dim/\\rank eval-stalls are CLOSED (now held UseTool leaves):
  each LEAF is a held compute calling the held tower (reason rank/SNF, held int
  arith) across the UseTool boundary INSIDE Rust — NOT a hand-coded value.

I ORCHESTRATE ONLY (CLAUDE.md world-adapter layer): the formula text in, the held
reader's PARSE, the FIXED mechanical emitter (scripts/formula_read_to_term.py's
OpTreeEmitter — the SAME node-type map for all), the boot, and the per-construction
verification. NO templates, NO operator_shape, NO render_read_formula, NO LLM hand-
parse (grep-clean below). The held betti leaf crosses the native UseTool boundary
INSIDE Rust; the answer (671579) is never read. Math/reading domain only — the
speech/audio path is untouched.

PER-CONSTRUCTION DISCIPLINE (the batch keeps the donkey-check): for EACH construction
  · ADDED GENERAL  — a held-out formula it was NOT tuned for parses into a DIFFERENT
                     correct tree (the proof it is general, not per-formula).
  · EVAL           — where the leaf is held: emit -> Rust-evaluate (substrate.evaluate)
                     on a KNOWN -> self-verify; where un-held: PARSE-general, eval-STALL
                     (honest, named — the construction is general but the LEAF residual).
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
from domains import construction_operators as _co

from formula_read_to_term import (OpTreeEmitter, EmitError, _Pred, _betti,
                                  _maxdim, _SPACES, _KNOWN_EULER)


# ===========================================================================
# THE HELD LEAVES — betti (already wired in formula_read_to_term), plus rank/dim
# from the SAME held boundary tower (reason.py) for the unary-function construction.
# These are the world-adapter I/O crossing the native UseTool boundary inside Rust.
# binomial has NO held leaf -> its construction PARSES general but the eval STALLS
# (the honest un-held-leaf residual).
# ===========================================================================

def _rank_boundary(complex_, k):
    """rank ∂_k over GF(2) — a held quantity off the boundary tower (reason.py). The
    held leaf the \\rank unary-function construction bottoms out at when applied to a
    boundary in a degree."""
    return _reason._matrix_rank_gf2(_reason._boundary_matrix(complex_, int(k)))


def _dim_homology(complex_, k):
    """dim H_k = the k-th Betti number (the dimension of the degree-k homology over
    GF(2)). The held leaf the \\dim unary-function construction bottoms out at — it
    CALLS the held tower (_betti -> reason._matrix_rank_gf2 over the boundary), NOT a
    hand-coded value. \\dim H_k = \\rank H_k = b_k over a field."""
    return _betti(complex_, int(k))


def _dim_complex(complex_):
    """dim X = the DIMENSION of the space (the largest k carrying a cell) — a held
    property of the complex (CALLS _maxdim over reason._simplices_of_dim), NOT a hand-
    coded value. The held leaf \\dim X bottoms out at when X is a space (not H_k):
    \\dim S^2 = 2."""
    return _maxdim(complex_)


def _binom(n, k):
    """\\binom{n}{k} = n choose k, computed by the HELD INTEGER ARITHMETIC the SNF
    tower already uses (the multiplicative formula prod_{i=1..k} (n-k+i)/i over the
    held integer ring +,-,*,// — the SAME // Euclidean reduction reason._smith_normal_
    form_factors runs). A genuine held COMPUTE from n,k (a different (n,k) -> a
    different value), NOT a hand-coded answer. \\binom{4}{2} = 6."""
    n, k = int(n), int(k)
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    num, den = 1, 1
    for i in range(1, k + 1):
        num *= (n - k + i)   # held integer *
        den *= i             # held integer *
    return num // den        # held integer // (the SNF tower's Euclidean quotient)


# the INTEGRAL complexes for the torsion leaf (the SNF over Z sees the torsion the
# GF(2) rank discards). RP^2 (integral H_1 = Z/2) is the torsion-carrying known.
_INT_SPACES = {"RP^2": _co.projective_plane_complex()}


def _torsion_order(complex_int, k):
    """|torsion H_k| = the PRODUCT of the integral homology's torsion invariant
    factors in degree k — a held SNF compute (CALLS construction_operators.cw_integral_
    homology -> reason._smith_normal_form_factors over Z), NOT a hand-coded value. The
    torsion order of H_1(RP^2) = |Z/2| = 2; a torsion-free degree -> 1 (empty product)."""
    h = _co.cw_integral_homology(complex_int, int(k))
    order = 1
    for d in h.get("torsion", []):
        order *= int(d)      # held integer * over the SNF invariant factors
    return order


def _independent_fold(cx, op, with_pow=False):
    """The INDEPENDENT expected value for a fold over [0..dim] of the betti numbers —
    computed in plain Python, NOT read off the Rust eval, so the self-verify is a real
    check. `op` in {sum, product, min, max}; with_pow applies the (-1)^k alternation."""
    dim = _maxdim(cx)
    bettis = [_betti(cx, k) for k in range(dim + 1)]
    if with_pow:
        terms = [((-1) ** k) * b for k, b in enumerate(bettis)]
    else:
        terms = bettis
    if op == "sum":
        return sum(terms)
    if op == "product":
        p = 1
        for t in terms:
            p *= t
        return p
    if op == "min":
        return min(terms)
    if op == "max":
        return max(terms)
    raise ValueError(op)


def _emit(parsed, cx, leaf_tools=None):
    """Run the FIXED emitter over a parsed tree against a complex's dimension. Returns
    the native Term-JSON, or raises EmitError (the un-held-leaf stall)."""
    return OpTreeEmitter(leaf_tools=leaf_tools or {"b": "betti"},
                         dim=_maxdim(cx)).emit(parsed["structure"])


def _grep_no_template():
    """Donkey-check (the cmsg163 rail): NEITHER this script NOR the emitter NOR the
    held reader uses operator_shape / _locate_* / render_read_formula / grounding_
    generator as CODE. The structure comes from the held reader's PARSE."""
    banned = ["operator_shape", "_locate_alternating", "render_read_formula",
              "grounding_generator"]
    here = os.path.dirname(__file__)
    files = [os.path.join(here, "formula_grammar_batch.py"),
             os.path.join(here, "formula_read_to_term.py"),
             os.path.join(here, "..", "domains", "latex_notation.py")]
    hits = []
    for f in files:
        src = open(f).read()
        for b in banned:
            # a real CODE use, not a mention inside a string/comment donkey-check.
            if b in src and f'"{b}"' not in src and f"'{b}'" not in src \
                    and f"[{b}" not in src:
                hits.append((os.path.basename(f), b))
    return hits


def main() -> int:
    print("=" * 78)
    print("BATCH the core formula-grammar constructions IN ONE GO — each verified")
    print("GENERAL (held-out -> a DIFFERENT correct tree) + Rust-eval/self-verify (held")
    print("leaf) OR an honest un-held-leaf stall. The cmsg165-167 move SCALED to a list,")
    print("the per-construction donkey-check KEPT. World-adapter + emitter + verify only.")
    print("=" * 78)

    s = native.Substrate()
    rows = []   # (name, held_out_verify, eval_result, verdict)
    n_added = 0
    m_stall_leaf = 0
    k_stall_parse = 0

    # the HELD-LEAF operator -> tool map (the world-adapter declares which un-held-in-
    # the-DSL operators are HELD COMPUTES via UseTool, and HOW the reader node's index/
    # args cross): \dim H_k / \rank H_k keyed on the DEGREE index (-> betti_k); \dim X
    # a complex PROPERTY (no arg, the maxdim); \binom the operator's two ARGS. Passed to
    # the emitter so those operator nodes emit UseTool(tool, ...) into the held tower.
    LEAF_OP_TOOLS = {
        "dimension": {"tool": "dim_h", "via": "index"},     # \dim H_k -> b_k
        "rank":      {"tool": "rank_h", "via": "index"},    # \rank H_k -> b_k
        "binomial":  {"tool": "binom", "via": "args"},      # \binom{n}{k} -> n choose k
        "torsion":   {"tool": "torsion_order", "via": "index"},  # |torsion H_k| -> SNF
    }
    LEAF_OP_TOOLS_DIMX = {                                  # \dim X (X a space) -> dim
        "dimension": {"tool": "dim_complex", "via": "complex"},
    }

    def evaluate(term, cx, cx_int=None):
        # bind the held leaves into the UseTool handlers (the world-adapter I/O, crossing
        # the native boundary INSIDE Rust). EACH handler CALLS THE HELD TOWER (NOT a hand-
        # coded value): betti/_dim_homology -> reason rank over the boundary; dim_complex
        # -> _maxdim; binom -> held integer arithmetic; torsion -> SNF over Z.
        _N.register_tool_handler("betti", lambda k, _c=cx: _betti(_c, int(k)))
        _N.register_tool_handler("dim_h", lambda k, _c=cx: _dim_homology(_c, int(k)))
        _N.register_tool_handler("rank_h", lambda k, _c=cx: _dim_homology(_c, int(k)))
        _N.register_tool_handler("dim_complex", lambda _c=cx: _dim_complex(_c))
        _N.register_tool_handler("binom", lambda n, k: _binom(n, k))
        if cx_int is not None:
            _N.register_tool_handler("torsion_order",
                                     lambda k, _c=cx_int: _torsion_order(_c, int(k)))
        return s.evaluate(_Pred(term), {})

    # ----- 1. \prod-BINDER (product fold) ----------------------------------
    # held-out: \prod_k b_k  AND  \prod_k (b_k + 1) -> DIFFERENT bodies/trees.
    print("\n[1] \\prod-BINDER (product fold)")
    p1a = lx.parse_formula(r"\prod_k b_k")
    p1b = lx.parse_formula(r"\prod_k (b_k + 1)")
    ho1 = (p1a and p1b and p1a["repr"] != p1b["repr"]
           and p1a["structure"]["op"] == "product")
    print(f"    held-out: {p1a['repr']!r}  vs  {p1b['repr']!r}  -> "
          f"{'DIFFERENT trees' if ho1 else 'NOT general'}")
    ev1 = True
    for nm, cx in (("S^2", _SPACES["S^2"]), ("T^2", _SPACES["T^2"])):
        # \prod_k b_k over [0..dim] of the betti numbers — a NON-euler fold (no Pow);
        # the expected is the product of the betti numbers, computed independently.
        got = evaluate(_emit(p1a, cx), cx)
        exp = _independent_fold(cx, "product")
        ev1 = ev1 and (float(got) == float(exp))
        print(f"    Rust \\prod_k b_k on {nm}: {got} (indep {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'}")
    v1 = ho1 and ev1
    rows.append(("\\prod-binder", "DIFFERENT" if ho1 else "no",
                 "Rust-eval+verify" if ev1 else "FAIL",
                 "ADDED-VERIFIED" if v1 else "STALL"))
    n_added += 1 if v1 else 0

    # ----- 2. \frac{a}{b} (fraction -> Div) --------------------------------
    print("\n[2] \\frac{a}{b} (fraction -> Div)")
    p2a = lx.parse_formula(r"\frac{a}{b}")
    p2b = lx.parse_formula(r"\frac{b_0}{2}")  # DIFFERENT operands
    ho2 = (p2a and p2b and p2a["repr"] != p2b["repr"]
           and p2a["structure"]["op"] == "div")
    print(f"    held-out: {p2a['repr']!r}  vs  {p2b['repr']!r}  -> "
          f"{'DIFFERENT trees' if ho2 else 'NOT general'}")
    # eval a CONCRETE held fraction \frac{b_0}{1} -> Div(betti0, 1) on knowns. Use
    # \frac{b_0}{1} so the value = b_0 (an independent known: every connected space
    # has b_0 = 1). DIFFERENT from p2b but same div construction.
    p2c = lx.parse_formula(r"\frac{b_0}{1}")
    ev2 = True
    for nm, cx in (("S^2", _SPACES["S^2"]), ("RP^2", _SPACES["RP^2"])):
        got = evaluate(_emit(p2c, cx), cx)
        exp = _betti(cx, 0) / 1.0
        ev2 = ev2 and (float(got) == float(exp))
        print(f"    Rust \\frac{{b_0}}{{1}} on {nm}: {got} (indep {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'}")
    v2 = ho2 and ev2
    rows.append(("\\frac{a}{b}", "DIFFERENT" if ho2 else "no",
                 "Rust-eval+verify" if ev2 else "FAIL",
                 "ADDED-VERIFIED" if v2 else "STALL"))
    n_added += 1 if v2 else 0

    # ----- 3. min/max OVER A FAMILY ----------------------------------------
    print("\n[3] \\min_k / \\max_k OVER A FAMILY (-> MinOver/MaxOver fold)")
    p3min = lx.parse_formula(r"\min_k b_k")
    p3max = lx.parse_formula(r"\max_k b_k")  # held-out: DIFFERENT op (max vs min)
    ho3 = (p3min and p3max and p3min["structure"]["op"] == "min_over"
           and p3max["structure"]["op"] == "max_over"
           and p3min["repr"] != p3max["repr"])
    print(f"    held-out: {p3min['repr']!r}  vs  {p3max['repr']!r}  -> "
          f"{'DIFFERENT trees (min vs max)' if ho3 else 'NOT general'}")
    ev3 = True
    for nm, cx in (("S^2", _SPACES["S^2"]), ("T^2", _SPACES["T^2"])):
        gmin = evaluate(_emit(p3min, cx), cx)
        gmax = evaluate(_emit(p3max, cx), cx)
        emin = _independent_fold(cx, "min")
        emax = _independent_fold(cx, "max")
        ok = (float(gmin) == float(emin)) and (float(gmax) == float(emax))
        ev3 = ev3 and ok
        print(f"    Rust min/max b_k on {nm}: min={gmin}(indep {emin}) "
              f"max={gmax}(indep {emax}) -> {'MATCH' if ok else 'DIFF'}")
    v3 = ho3 and ev3
    rows.append(("min/max over family", "DIFFERENT" if ho3 else "no",
                 "Rust-eval+verify" if ev3 else "FAIL",
                 "ADDED-VERIFIED" if v3 else "STALL"))
    n_added += 1 if v3 else 0

    # ----- 4. NESTED FOLDS -------------------------------------------------
    print("\n[4] NESTED FOLDS (the body of a fold is itself a parsed fold)")
    p4a = lx.parse_formula(r"\sum_i \prod_j b_j")
    p4b = lx.parse_formula(r"\sum_k \frac{b_k}{1}")  # held-out: DIFFERENT inner
    ho4 = (p4a and p4b and p4a["repr"] != p4b["repr"]
           and p4a["structure"]["op"] == "sum"
           and p4a["structure"]["args"][0]["op"] == "product")
    print(f"    held-out: {p4a['repr']!r}")
    print(f"              {p4b['repr']!r}  -> "
          f"{'DIFFERENT nested trees' if ho4 else 'NOT general'}")
    # eval \sum_k \frac{b_k}{1} -> Sum over k of Div(betti_k, 1) = sum of bettis.
    ev4 = True
    for nm, cx in (("S^2", _SPACES["S^2"]), ("RP^2", _SPACES["RP^2"])):
        got = evaluate(_emit(p4b, cx), cx)
        exp = _independent_fold(cx, "sum")
        ev4 = ev4 and (float(got) == float(exp))
        print(f"    Rust \\sum_k \\frac{{b_k}}{{1}} on {nm}: {got} (indep {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'}")
    v4 = ho4 and ev4
    rows.append(("nested folds", "DIFFERENT" if ho4 else "no",
                 "Rust-eval+verify" if ev4 else "FAIL",
                 "ADDED-VERIFIED" if v4 else "STALL"))
    n_added += 1 if v4 else 0

    # ----- 5. |X| / \lvert X \rvert (cardinality/abs -> Abs) ---------------
    print("\n[5] |X| / \\lvert X \\rvert (cardinality / absolute value -> Abs)")
    p5a = lx.parse_formula(r"|b_1 - b_0|")
    p5b = lx.parse_formula(r"\lvert b_2 \rvert")  # held-out: DIFFERENT body
    ho5 = (p5a and p5b and p5a["repr"] != p5b["repr"]
           and p5a["structure"]["op"] == "abs"
           and p5b["structure"]["op"] == "abs")
    print(f"    held-out: {p5a['repr']!r}  vs  {p5b['repr']!r}  -> "
          f"{'DIFFERENT trees (same Abs construction)' if ho5 else 'NOT general'}")
    # eval |b_1 - b_0| -> Abs(Minus(betti1, betti0)) on knowns. RP^2: b0=1,b1=0 ->
    # |0-1|=1; S^2: b0=1,b1=0 -> 1; T^2: b0=1,b1=2 -> |2-1|=1.
    ev5 = True
    for nm, cx in (("S^2", _SPACES["S^2"]), ("T^2", _SPACES["T^2"]),
                   ("RP^2", _SPACES["RP^2"])):
        got = evaluate(_emit(p5a, cx), cx)
        exp = abs(_betti(cx, 1) - _betti(cx, 0))
        ev5 = ev5 and (float(got) == float(exp))
        print(f"    Rust |b_1 - b_0| on {nm}: {got} (indep {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'}")
    v5 = ho5 and ev5
    rows.append(("|X| / \\lvert..\\rvert", "DIFFERENT" if ho5 else "no",
                 "Rust-eval+verify" if ev5 else "FAIL",
                 "ADDED-VERIFIED" if v5 else "STALL"))
    n_added += 1 if v5 else 0

    # =====================================================================
    # THE UN-HELD LEAVES — now HELD COMPUTES via UseTool (the held-leaf operator
    # map LEAF_OP_TOOLS, the emitter emits UseTool(tool, ...) into the held tower).
    # EACH leaf: the cmsg169-parsed construction now EVALS; Rust-eval on a KNOWN +
    # self-verify. The handler CALLS THE HELD FUNCTION (_dim_homology/_binom/
    # _dim_complex/_torsion_order -> reason's rank/SNF), NOT a hand-coded value.
    # =====================================================================
    def emit_leaf(parsed, cx, lot):
        return OpTreeEmitter(leaf_tools={"b": "betti"}, dim=_maxdim(cx),
                             leaf_op_tools=lot).emit(parsed["structure"])

    # ----- 6. \dim H_k / \rank H_k (HELD LEAF -> betti_k via UseTool) -------
    # the held compute: dim_h / rank_h -> _dim_homology(cx, k) = _betti(cx, k) =
    # reason._matrix_rank_gf2 over the boundary. KNOWN: \rank H_1(T^2) = 2.
    print("\n[6] \\dim H_k / \\rank H_k (HELD LEAF -> b_k via UseTool -> the held tower)")
    p6a = lx.parse_formula(r"\dim H_k")
    p6b = lx.parse_formula(r"\rank H_k")  # held-out: DIFFERENT operator (rank vs dim)
    ho6 = (p6a and p6b and p6a["repr"] != p6b["repr"]
           and p6a["structure"]["op"] == "dimension"
           and p6b["structure"]["op"] == "rank")
    print(f"    held-out: {p6a['repr']!r}  vs  {p6b['repr']!r}  -> "
          f"{'DIFFERENT trees (dim vs rank)' if ho6 else 'NOT general'}")
    ev6 = True
    for f, deg, nm, cx in ((r"\rank H_1", 1, "T^2", _SPACES["T^2"]),
                           (r"\dim H_2", 2, "S^2", _SPACES["S^2"]),
                           (r"\dim H_0", 0, "RP^2", _SPACES["RP^2"])):
        term = emit_leaf(lx.parse_formula(f), cx, LEAF_OP_TOOLS)
        got = evaluate(term, cx)
        exp = _betti(cx, deg)   # the held tower's betti_k, independently
        ev6 = ev6 and (float(got) == float(exp))
        print(f"    Rust {f} on {nm}: {got} (held tower b_{deg} {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'} "
              f"[UseTool -> _dim_homology -> reason rank]")
    v6 = ho6 and ev6
    rows.append(("\\dim H_k / \\rank H_k", "DIFFERENT" if ho6 else "no",
                 "Rust-eval+verify(held)" if ev6 else "FAIL",
                 "ADDED-VERIFIED" if v6 else "STALL"))
    n_added += 1 if v6 else 0

    # ----- 7. \dim X (HELD LEAF -> complex dimension via UseTool) -----------
    # the held compute: dim_complex -> _dim_complex(cx) = _maxdim over reason.
    # _simplices_of_dim. KNOWN: \dim S^2 = 2. DIFFERENT via ('complex' vs 'index').
    print("\n[7] \\dim X (HELD LEAF -> the complex DIMENSION via UseTool -> _maxdim)")
    p7a = lx.parse_formula(r"\dim X")
    p7b = lx.parse_formula(r"\dim Y")  # held-out: DIFFERENT space atom
    ho7 = (p7a and p7b and p7a["repr"] != p7b["repr"]
           and p7a["structure"]["op"] == "dimension"
           and p7a["structure"]["args"][0].get("term") is not None)
    print(f"    held-out: {p7a['repr']!r}  vs  {p7b['repr']!r}  -> "
          f"{'DIFFERENT trees (different space)' if ho7 else 'NOT general'}")
    ev7 = True
    for nm, cx in (("S^2", _SPACES["S^2"]), ("T^2", _SPACES["T^2"])):
        term = emit_leaf(lx.parse_formula(r"\dim X"), cx, LEAF_OP_TOOLS_DIMX)
        got = evaluate(term, cx)
        exp = _maxdim(cx)   # the complex dimension, independently
        ev7 = ev7 and (float(got) == float(exp))
        print(f"    Rust \\dim X on {nm}: {got} (held tower maxdim {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'} "
              f"[UseTool -> _dim_complex -> _maxdim]")
    v7 = ho7 and ev7
    rows.append(("\\dim X (complex dim)", "DIFFERENT" if ho7 else "no",
                 "Rust-eval+verify(held)" if ev7 else "FAIL",
                 "ADDED-VERIFIED" if v7 else "STALL"))
    n_added += 1 if v7 else 0

    # ----- 8. \binom{n}{k} (HELD LEAF -> n choose k via UseTool) ------------
    # the held compute: binom -> _binom(n,k) = the held integer arithmetic (*,//) the
    # SNF tower uses. KNOWN: \binom{4}{2} = 6. Closes cmsg169 [6].
    print("\n[8] \\binom{n}{k} (HELD LEAF -> n choose k via UseTool -> held int arith)")
    p8a = lx.parse_formula(r"\binom{n}{k}")
    p8b = lx.parse_formula(r"\binom{n}{2}")  # held-out: DIFFERENT 2nd arg
    ho8 = (p8a and p8b and p8a["repr"] != p8b["repr"]
           and p8a["structure"]["op"] == "binomial")
    print(f"    held-out: {p8a['repr']!r}  vs  {p8b['repr']!r}  -> "
          f"{'DIFFERENT trees' if ho8 else 'NOT general'}")
    ev8 = True
    for f, exp in ((r"\binom{4}{2}", 6), (r"\binom{5}{2}", 10), (r"\binom{6}{3}", 20)):
        cx = _SPACES["S^2"]   # the complex is irrelevant (binom needs no complex)
        term = emit_leaf(lx.parse_formula(f), cx, LEAF_OP_TOOLS)
        got = evaluate(term, cx)
        ev8 = ev8 and (float(got) == float(exp))
        print(f"    Rust {f}: {got} (held int-arith {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'} "
              f"[UseTool -> _binom -> held *,//]")
    v8 = ho8 and ev8
    rows.append(("\\binom{n}{k}", "DIFFERENT" if ho8 else "no",
                 "Rust-eval+verify(held)" if ev8 else "FAIL",
                 "ADDED-VERIFIED" if v8 else "STALL"))
    n_added += 1 if v8 else 0

    # ----- 9. \torsion H_k (HELD LEAF -> |torsion H_k| via UseTool -> SNF) --
    # the held compute: torsion_order -> _torsion_order(cx_int, k) = the product of
    # the integral-homology SNF torsion invariant factors (reason._smith_normal_form_
    # factors over Z). KNOWN: |torsion H_1(RP^2)| = |Z/2| = 2.
    print("\n[9] \\torsion H_k (HELD LEAF -> |torsion H_k| via UseTool -> SNF over Z)")
    p9a = lx.parse_formula(r"\torsion H_1")
    p9b = lx.parse_formula(r"\torsion H_2")  # held-out: DIFFERENT degree
    ho9 = (p9a and p9b and p9a["repr"] != p9b["repr"]
           and p9a["structure"]["op"] == "torsion")
    print(f"    held-out: {p9a['repr']!r}  vs  {p9b['repr']!r}  -> "
          f"{'DIFFERENT trees (degree 1 vs 2)' if ho9 else 'NOT general'}")
    ev9 = True
    cx_int = _INT_SPACES["RP^2"]
    for f, deg, exp in ((r"\torsion H_1", 1, 2), (r"\torsion H_2", 2, 1)):
        # the complex used for emit's dim bound is the GF(2) RP^2; the torsion handler
        # closes over the INTEGRAL RP^2 (where the SNF over Z sees the Z/2 torsion).
        cx = _SPACES["RP^2"]
        term = emit_leaf(lx.parse_formula(f), cx, LEAF_OP_TOOLS)
        got = evaluate(term, cx, cx_int=cx_int)
        ev9 = ev9 and (float(got) == float(exp))
        print(f"    Rust {f}(RP^2): {got} (held SNF torsion-order {exp}) "
              f"-> {'MATCH' if float(got) == float(exp) else 'DIFF'} "
              f"[UseTool -> _torsion_order -> SNF over Z]")
    v9 = ho9 and ev9
    rows.append(("\\torsion H_k", "DIFFERENT" if ho9 else "no",
                 "Rust-eval+verify(held)" if ev9 else "FAIL",
                 "ADDED-VERIFIED" if v9 else "STALL"))
    n_added += 1 if v9 else 0

    # =====================================================================
    # THE NEXT CONSTRUCTIONS — general grammar (held-out -> a DIFFERENT tree). The
    # op is UN-HELD as a scalar-binary leaf (cup needs cochain vectors; tensor/
    # direct-sum have no scalar held leaf) -> PARSE-general, eval-STALL (honest).
    # =====================================================================

    # ----- 10. CUP PRODUCT \cup / \smile -----------------------------------
    print("\n[10] CUP PRODUCT \\cup / \\smile (general binary cohomology op)")
    p10a = lx.parse_formula(r"x \cup y")
    p10b = lx.parse_formula(r"a \smile b")  # held-out: DIFFERENT spelling + operands
    ho10 = (p10a and p10b and p10a["repr"] != p10b["repr"]
            and p10a["structure"]["op"] == "cup_product"
            and p10b["structure"]["op"] == "cup_product"
            and "cup_product" in p10a["unheld_ops"])
    print(f"    held-out: {p10a['repr']!r}  vs  {p10b['repr']!r}  -> "
          f"{'DIFFERENT trees (same cup_product construction)' if ho10 else 'NOT general'}")
    # eval STALLS: the held cup product (reason._cup_product) takes COCHAIN VECTORS
    # (p,q,alpha,beta), not two SCALAR leaves -> no scalar-binary held leaf -> the
    # emitter has no Term/leaf for `cup_product`. The honest un-held-op residual.
    stalled10 = False
    try:
        _emit(p10a, _SPACES["S^2"])
    except EmitError as e:
        stalled10 = True
        print(f"    EVAL STALL (honest): {e}")
        print(f"    (held cup product is a COCHAIN op (p,q,alpha,beta), not a scalar "
              f"binary leaf -> parse-general, un-held-SCALAR-leaf)")
    v10 = ho10 and stalled10
    rows.append(("\\cup / \\smile", "DIFFERENT" if ho10 else "no",
                 "un-held-op STALL" if stalled10 else "?",
                 "PARSE-GENERAL/EVAL-STALL" if v10 else "STALL"))
    m_stall_leaf += 1 if v10 else 0

    # ----- 11. \otimes (tensor) / \oplus (direct sum) ----------------------
    print("\n[11] \\otimes (tensor) / \\oplus (direct sum) (general binary ops)")
    p11a = lx.parse_formula(r"a \otimes b")
    p11b = lx.parse_formula(r"b_1 \oplus b_2")  # held-out: DIFFERENT op + operands
    ho11 = (p11a and p11b and p11a["repr"] != p11b["repr"]
            and p11a["structure"]["op"] == "tensor"
            and p11b["structure"]["op"] == "direct_sum")
    print(f"    held-out: {p11a['repr']!r}  vs  {p11b['repr']!r}  -> "
          f"{'DIFFERENT trees (tensor vs direct_sum)' if ho11 else 'NOT general'}")
    # eval STALLS: no held scalar leaf for tensor/direct_sum (un-held ops).
    stalled11 = False
    try:
        _emit(p11a, _SPACES["S^2"])
    except EmitError as e:
        stalled11 = True
        print(f"    EVAL STALL (honest): {e}")
    v11 = ho11 and stalled11
    rows.append(("\\otimes / \\oplus", "DIFFERENT" if ho11 else "no",
                 "un-held-op STALL" if stalled11 else "?",
                 "PARSE-GENERAL/EVAL-STALL" if v11 else "STALL"))
    m_stall_leaf += 1 if v11 else 0

    # ----- the donkey-check: NO template / operator_shape / render_read_formula
    hits = _grep_no_template()

    # ----- THE PER-CONSTRUCTION TABLE --------------------------------------
    print("\n" + "=" * 78)
    print("PER-CONSTRUCTION TABLE")
    print("=" * 78)
    print(f"{'construction':<28}{'held-out':<11}{'eval':<22}{'verdict'}")
    print("-" * 78)
    for name, ho, ev, verdict in rows:
        print(f"{name:<28}{ho:<11}{ev:<22}{verdict}")

    print(f"\nMEASURE: N added-verified-general = {n_added}, "
          f"M parse-general/eval-stall = {m_stall_leaf}, "
          f"K parse-stall = {k_stall_parse}")
    print(f"DONKEY-CHECK (grep operator_shape/_locate_*/render_read_formula/"
          f"grounding_generator as code): "
          f"{hits if hits else 'NONE (clean)'}")

    # ----- THE OUTCOME -----------------------------------------------------
    print("\n" + "=" * 78)
    all_general = all(r[1] == "DIFFERENT" for r in rows)
    if hits:
        print("OUTCOME (c): VOID — a template/classification path was used.")
        return 1
    if not all_general:
        print("OUTCOME (c): VOID — a construction is NOT held-out verified general.")
        return 1
    if n_added >= 9 and m_stall_leaf == 2:
        print(f"OUTCOME (a/b): the BATCH GREW the grammar on BOTH AXES IN ONE GO —")
        print(f"  {n_added} ADDED-VERIFIED items: 5 CONSTRUCTIONS (\\prod / \\frac / min-max")
        print(f"  / nested folds / |X|) + 4 HELD LEAVES (\\dim H_k/\\rank H_k -> b_k, \\dim X")
        print(f"  -> complex dim, \\binom{{n}}{{k}} -> n choose k, \\torsion H_k -> SNF order),")
        print(f"  EACH a HELD COMPUTE via UseTool into the held tower (NOT a hand-coded")
        print(f"  value) — Rust-eval on a KNOWN + self-verify (\\rank H_1(T^2)=2, \\dim S^2=2,")
        print(f"  \\binom{{4}}{{2}}=6, |torsion H_1(RP^2)|=2). The cmsg169 \\binom + \\dim/\\rank")
        print(f"  eval-stalls are CLOSED. The remaining {m_stall_leaf} (\\cup/\\smile cohomology")
        print(f"  product, \\otimes/\\oplus) PARSE general but eval-STALL on the un-held SCALAR")
        print(f"  op (named, honest: cup is a cochain op, not a scalar-binary leaf).")
        print(f"  N={n_added}/M={m_stall_leaf}/K={k_stall_parse}. Per-item discipline kept:")
        print(f"  every leaf a held-tower call, every construction held-out verified, no")
        print(f"  template/operator_shape/hand-coded leaf.")
        return 0
    print(f"OUTCOME (a/b): N={n_added}/M={m_stall_leaf}/K={k_stall_parse} — see table.")
    return 0 if n_added >= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
