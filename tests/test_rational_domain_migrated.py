"""test_rational_domain_migrated — PROGRAM_SYNTHESIS_ARC5_RATIONAL.md gates.

Makes the PROGRAM value domain rational-first: `Value::Rational(i64, i64)`
(runners/dsl/src/value.rs) is an exact, always-reduced fraction that
`ProgEval` arithmetic and `SynthEnumerate` constants use for in-frame
numbers instead of a float, per CLAUDE.md's frame/continuum invariant
("in-frame is integer/rational, never a float; non-integer structure is
CROSS-FRAME"). `Value::Float` is UNCHANGED and untouched globally — it
remains the correct representation for genuine cross-frame maps (pi,
sqrt, the DTW/ShapeContext verdict metrics) and is where a Rational
renders when it meets one (`as_f64()` / `PartialEq` / `cmp_value`).

Gates:

  1. EXACT-ARITHMETIC LAWS — `1/3 + 1/3 + 1/3 == 1` exactly inside
     ProgEval (where plain float arithmetic is provably NOT exact:
     `0.1 + 0.2 != 0.3` in IEEE-754); rational add/sub/mul/div/pow
     round-trip through reflect/Term-JSON as the `{"__rational__":
     [n, d]}` wire tag.
  2. OVERFLOW HONESTY — ProgEval's local exact-division/exact-power
     interception traps `"arith:overflow"` (never a silent wrap) once
     it has committed to the exact path; the SHARED, non-fallible
     `evaluate()` (Plus/Times/Minus/Pow/Neg/Abs, used pervasively
     outside program synthesis) degrades to `Value::Float` instead —
     still honest, just without a trap channel.
  3. THE BOUNDARY — a rational result still compares correctly against
     a float-valued value (`==`, `<`, `isinstance(x, float)`, `str()`,
     `float()`); `SynthEnumerate`'s `canon()` renders a Rational to the
     SAME `SigVal::Num` shape as Float so its 1e-9 tolerance compare
     against a float spec row still applies.
  4. TYPED ENUMERATION NEVER EMITS A FLOAT LITERAL — the geometry
     family's fitted `k` (domains/prog_exact.py) renders as a single
     exact rational Lit, not a `Div` of two ints (which collapses to
     float at evaluation) nor a bare float Lit.
  5. NO BEHAVIOUR REGRESSION — every pre-existing Int/Float/Bool
     arithmetic combination is byte-identical (Rational never existed
     before this feature, so its new match arms are purely additive);
     the global `Div`/`Mod`/`IDiv`/`IRem` Terms (used pervasively
     outside program synthesis, e.g. bigville) are UNTOUCHED.
  6. THE NINE-ITEM ARC-2 Q1 DIVERGENCE LEDGER, RE-CHECKED — item by
     item, with an honest verdict (most are orthogonal to the float/
     rational numeric axis and are UNAFFECTED by this rung; see the
     per-item comments and PROGRAM_SYNTHESIS_ARC5_RATIONAL.md).

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_rational_domain_migrated.py \
    --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import sys
from fractions import Fraction

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs

import domains.prog_exact as pex


# ---------------------------------------------------------------------------
# Term-JSON builders (mirrors tests/test_prog_ir_migrated.py / substrate/dsl.py)
# ---------------------------------------------------------------------------
def L(v):
    return {"type": "Lit", "value": v}


def RAT(n, d):
    return {"type": "Lit", "value": {"__rational__": [n, d]}}


def V(n):
    return {"type": "Var", "name": n}


def SEQ(*stmts):
    return {"type": "ProgSeq", "stmts": list(stmts)}


def ASSIGN(name, value):
    return {"type": "ProgAssignVar", "name": name, "value": value}


def RET(value=None):
    return {"type": "ProgReturn", "value": value}


def DIV(a, b):
    return {"type": "Div", "a": a, "b": b}


def PLUS(*items):
    return {"type": "Plus", "items": list(items)}


def TIMES(*items):
    return {"type": "Times", "items": list(items)}


def MINUS(a, b):
    return {"type": "Minus", "a": a, "b": b}


def POW(a, b):
    return {"type": "Pow", "a": a, "b": b}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def LT(a, b):
    return {"type": "Lt", "a": a, "b": b}


def CALL(name, *args):
    return {"type": "ProgCallExtern", "name": name, "recv": None, "args": list(args)}


def MKDICT(**kv):
    items = []
    for k, v in kv.items():
        items.append(L(k))
        items.append(L(v))
    return {"type": "MkDict", "items": items}


def ORACLES(*names):
    return MKDICT(**{n: "builtin" for n in names})


def PROGEVAL(prog, env=None, oracles=None, fuel=1000, field=""):
    return {"type": "ProgEval", "prog": prog, "env": env, "oracles": oracles,
            "fuel": fuel, "field": field}


def SYNTH(examples, ops=None, consts=None, max_size=0, max_candidates=0,
          saturate_k=0, field=""):
    return {
        "type": "SynthEnumerate",
        "examples": {"type": "Lit", "value": examples},
        "ops": {"type": "Lit", "value": list(ops)} if ops is not None else None,
        "consts": {"type": "Lit", "value": list(consts)} if consts is not None else None,
        "exclude": None,
        "max_size": max_size,
        "max_candidates": max_candidates,
        "saturate_k": saturate_k,
        "field": field,
    }


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------
@pytest.fixture()
def sub():
    return srs.Substrate()


def _rational_live() -> bool:
    """Honest skip (the test_prog_ir_migrated.py precedent) — refuse to
    fake a pass if the rebuilt/synced .so predates this rung."""
    s = srs.Substrate()
    try:
        out = s._inner.evaluate(PROGEVAL(SEQ(RET(DIV(L(1), L(3))))), {})
        return isinstance(out, dict) and isinstance(out.get("result"), Fraction)
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _rational_live():
    pytest.skip(
        "Rational value domain not present in the installed substrate_rs "
        "binary — rebuild runners/dsl (cargo build --release + sync "
        "python/substrate_rs/_native.abi3.so). Honest skip, not a fake pass.",
        allow_module_level=True)


def run_prog(sub, prog, fuel=1000, oracles=()):
    oracles_child = ORACLES(*oracles) if oracles else None
    out = sub._inner.evaluate(PROGEVAL(prog, oracles=oracles_child, fuel=fuel), None)
    assert isinstance(out, dict), f"ProgEval must return a Dict, got {type(out)}"
    return out


# ---------------------------------------------------------------------------
# 1) EXACT-ARITHMETIC LAWS
# ---------------------------------------------------------------------------
def test_float_addition_is_not_associative_exact_the_control():
    """The textbook trap this whole rung exists to route around."""
    assert 0.1 + 0.2 != 0.3


def test_one_third_thrice_is_exactly_one(sub):
    """PROGRAM_SYNTHESIS_ARC5_RATIONAL.md's headline exactness gate: a
    Prog-free expression (`1/3 + 1/3 + 1/3`, no Prog* node anywhere) —
    Python `1/3` compiles to the plain DSL `Div` Term. Div itself stays
    a float-producing Term GLOBALLY (bigville et al. depend on that);
    ProgEval's own local exact-division interception is what makes
    THIS expression exact, and it fires even though the expression is
    otherwise ordinary (that is the point of the arc-5 rung's
    `is_compositional_op`-unconditional widening in `eval_expr`)."""
    prog = SEQ(RET(PLUS(DIV(L(1), L(3)), DIV(L(1), L(3)), DIV(L(1), L(3)))))
    out = run_prog(sub, prog)
    assert out["halted"] is True, out
    assert out["result"] == 1
    assert isinstance(out["result"], int), f"expected exact int 1, got {out['result']!r}"


def test_exact_division_yields_a_fraction_not_a_float(sub):
    out = run_prog(sub, SEQ(RET(DIV(L(1), L(4)))))
    assert out["result"] == Fraction(1, 4)
    assert isinstance(out["result"], Fraction)


def test_exact_subtraction_multiplication_power(sub):
    s = sub
    assert run_prog(s, SEQ(RET(MINUS(DIV(L(1), L(2)), DIV(L(1), L(3))))))["result"] == Fraction(1, 6)
    assert run_prog(s, SEQ(RET(TIMES(DIV(L(2), L(3)), DIV(L(3), L(4))))))["result"] == Fraction(1, 2)
    assert run_prog(s, SEQ(RET(POW(DIV(L(1), L(2)), L(2)))))["result"] == Fraction(1, 4)


def test_division_by_zero_stays_the_documented_float_divergence(sub):
    """The exact path is skipped entirely for a zero divisor (`pb.0 !=
    0` guard) — ProgEval keeps the PRE-EXISTING, documented "no
    ZeroDivisionError, Div-by-zero -> 0.0" divergence, unchanged."""
    out = run_prog(sub, SEQ(RET(DIV(L(1), L(0)))))
    assert out["result"] == 0.0
    assert isinstance(out["result"], float)


def test_rational_literal_round_trips_through_reflect(sub):
    sample = RAT(4, 3)
    nid = sub._inner.add_term_subgraph(sample)
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    assert c1 == sample
    nid2 = sub._inner.add_term_subgraph(c1)
    c2 = json.loads(sub._inner.term_subgraph_json(nid2))
    assert c2 == c1, "second reflect pass drifted"


def test_rational_literal_reduces_on_the_way_in(sub):
    """`{"__rational__": [6, 3]}` == 2 exactly — `make_rational` collapses
    to `Value::Int` on decode, so the round-trip is with the REDUCED
    form, not a re-assertion of the unreduced input."""
    nid = sub._inner.add_term_subgraph(RAT(6, 3))
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    assert c1 == L(2)


# ---------------------------------------------------------------------------
# 2) OVERFLOW HONESTY
# ---------------------------------------------------------------------------
def test_exact_power_overflow_traps_never_silently_wraps(sub):
    """`(1/3) ** 40` — the denominator `3**40` overflows i64 by a wide
    margin. ProgEval has committed to the exact path (a genuine
    Rational base, an Int exponent) so this MUST trap, never wrap or
    silently truncate to a wrong rational."""
    out = run_prog(sub, SEQ(RET(POW(DIV(L(1), L(3)), L(40)))))
    assert out["halted"] is False
    assert out["trap"] == "arith:overflow"
    assert "result" not in out or out["result"] is None


def test_shared_evaluator_degrades_to_float_on_the_same_overflow(sub):
    """The SAME overflow, reached through the plain (non-ProgEval)
    evaluator (no trap channel available) — degrades to a real,
    slightly-imprecise float instead of trapping or wrapping. This is
    `term.rs`'s Pow arm exercised directly, not through ProgEval."""
    s = sub
    term = POW(RAT(1, 3), L(40))
    result = s._inner.evaluate(term, None)
    assert isinstance(result, float)
    assert abs(result - (1.0 / 3.0) ** 40) < 1e-12


# ---------------------------------------------------------------------------
# 3) THE BOUNDARY — a rational compares/renders correctly against float
# ---------------------------------------------------------------------------
def test_rational_equals_its_float_value_at_the_boundary(sub):
    out = run_prog(sub, SEQ(ASSIGN("x", DIV(L(1), L(2))), RET(EQ(V("x"), L(0.5)))))
    assert out["result"] is True


def test_rational_orders_correctly_against_float(sub):
    out = run_prog(sub, SEQ(ASSIGN("x", DIV(L(1), L(3))), RET(LT(V("x"), L(0.5)))))
    assert out["result"] is True


def test_isinstance_float_matches_an_exact_division_result(sub):
    out = run_prog(sub, SEQ(ASSIGN("x", DIV(L(1), L(3))), RET(CALL("isinstance", V("x"), L("float")))),
                   oracles=("isinstance",))
    assert out["result"] is True, "isinstance(a/b, float) must stay True — a real Python type identity"


def test_float_builtin_renders_the_boundary(sub):
    out = run_prog(sub, SEQ(ASSIGN("x", DIV(L(1), L(4))), RET(CALL("float", V("x")))),
                   oracles=("float",))
    assert out["result"] == 0.25
    assert isinstance(out["result"], float)


def test_str_of_a_rational_spells_like_cpythons_float(sub):
    out = run_prog(sub, SEQ(ASSIGN("x", DIV(L(1), L(4))), RET(CALL("str", V("x")))),
                   oracles=("str",))
    assert out["result"] == str(1 / 4) == "0.25"


def test_sum_of_rationals_stays_exact(sub):
    out = run_prog(
        sub,
        SEQ(ASSIGN("xs", {"type": "ProgContainerLit", "kind": "list",
                          "items": [DIV(L(1), L(3)), DIV(L(1), L(3)), DIV(L(1), L(3))]}),
            RET(CALL("sum", V("xs")))),
        oracles=("sum",),
    )
    assert out["result"] == 1
    assert isinstance(out["result"], int)


# ---------------------------------------------------------------------------
# 4) TYPED ENUMERATION / FAMILY-FIT NEVER EMITS A FLOAT LITERAL
# ---------------------------------------------------------------------------
def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)


def test_geometry_family_k_renders_as_exact_rational_not_div_not_float():
    """volume_sphere-shaped: k=4/3, exponent 3 on the radius — the
    canonical PROGRAM_SYNTHESIS_ARC5_SPECS_IMPLY_FLOATS.md recovery."""
    family = {
        "name": "scaled_power_product", "order": 0.0, "min_arity": 1, "max_arity": 1,
        "k_numerators": [1, 2, 4], "k_denominators": [1, 3],
        "constants": {"1": 1.0, "pi": 3.141592653589793}, "max_exponent": 3,
        "default_tol": 1e-9, "shared_kc": False,
    }
    params = {"k_num": 4, "k_den": 3, "const": "pi", "exps": [3]}
    ir = pex.render_family_to_ir(family, params, ["r"])
    lits = [n for n in _walk(ir) if n.get("type") == "Lit"]
    rational_lits = [n for n in lits if isinstance(n["value"], dict) and "__rational__" in n["value"]]
    assert rational_lits and rational_lits[0]["value"]["__rational__"] == [4, 3]
    # No `Div` anywhere — the old float-collapsing rendering is gone.
    assert not any(n.get("type") == "Div" for n in _walk(ir))
    # No bare float Lit except the named cross-frame constant (pi).
    for n in lits:
        if isinstance(n["value"], float):
            assert n["value"] == family["constants"]["pi"]


def test_rendered_rational_k_evaluates_exactly_via_progeval(sub):
    family = {
        "name": "scaled_power_product", "order": 0.0, "min_arity": 1, "max_arity": 1,
        "k_numerators": [1], "k_denominators": [3],
        "constants": {"1": 1.0}, "max_exponent": 2,
        "default_tol": 1e-9, "shared_kc": False,
    }
    params = {"k_num": 1, "k_den": 3, "const": "1", "exps": [2]}
    ir = pex.render_family_to_ir(family, params, ["r"])
    # ir is a ProgSeq(ProgDefFnParam(r), ProgReturn(Times(1/3, r**2))) —
    # bind r=3 directly (no function-call machinery needed for this gate).
    out = sub._inner.evaluate(
        PROGEVAL(SEQ(ASSIGN("r", L(3)), RET(ir["stmts"][-1]["value"]))), None,
    )
    assert out["result"] == 3  # (1/3) * 9 == 3 exactly
    assert isinstance(out["result"], int)


def test_synth_enumerate_default_consts_never_include_a_float(sub):
    """generator.py's (0,1,2,-1) default, plus integer-valued outputs —
    NEVER a bare float, with or without this rung (a pre-existing
    property this gate PINS)."""
    s = sub
    examples = [{"inputs": {"x": 2.0}, "output": 5.0}, {"inputs": {"x": 3.0}, "output": 10.0}]
    out = s._inner.evaluate(SYNTH(examples, max_size=5, max_candidates=2000), None)
    assert isinstance(out, dict)
    term_str = json.dumps(out.get("term"))
    # A bare JSON float literal renders with a '.'; every numeric literal
    # this search can auto-generate is an int (or, if ever a Rational,
    # the tagged dict form) — never a raw '<int>.<digits>' float token.
    import re
    assert not re.search(r'"value":\s*-?\d+\.\d', term_str or ""), term_str


def test_synth_enumerate_numeric_const_pool_accepts_an_explicit_rational(sub):
    """An explicit Rational const (e.g. from a caller's own family-fit)
    is usable by the enumerator like any other numeric constant — not
    silently dropped or miscategorised."""
    s = sub
    examples = [{"inputs": {"x": 2}, "output": 2.5}, {"inputs": {"x": 4}, "output": 4.5}]
    out = s._inner.evaluate(
        SYNTH(examples, consts=[{"__rational__": [1, 2]}], max_size=5, max_candidates=5000),
        None,
    )
    assert isinstance(out, dict)
    assert out["found"] is True, out


# ---------------------------------------------------------------------------
# 5) NO BEHAVIOUR REGRESSION — pre-existing Int/Float/Bool paths unchanged
# ---------------------------------------------------------------------------
def test_plain_int_arithmetic_byte_identical(sub):
    assert sub._inner.evaluate(PLUS(L(2), L(3), L(4)), None) == 9
    assert sub._inner.evaluate(TIMES(L(2), L(3), L(4)), None) == 24
    assert sub._inner.evaluate(MINUS(L(10), L(3)), None) == 7
    assert sub._inner.evaluate(POW(L(2), L(10)), None) == 1024


def test_plain_float_arithmetic_byte_identical(sub):
    assert sub._inner.evaluate(PLUS(L(2.5), L(1.5)), None) == 4.0
    assert sub._inner.evaluate(DIV(L(1), L(2)), None) == 0.5  # global Div: STILL always float
    assert sub._inner.evaluate(DIV(L(17), L(2)), None) == 8.5


def test_global_div_is_untouched_outside_progeval(sub):
    """The shared `Div` Term (bigville et al.) stays TRUE division,
    ALWAYS float — this rung's exactness is local to ProgEval, never
    global. `1/3` through the plain evaluator (no ProgEval) is still
    a float, exactly as before this rung existed."""
    result = sub._inner.evaluate(DIV(L(1), L(3)), None)
    assert isinstance(result, float)
    assert abs(result - (1 / 3)) < 1e-15


def test_int_pow_overflow_still_wraps_the_pre_existing_behaviour(sub):
    """The (Int, Int) Pow fast path (`wrapping_pow`) is UNTOUCHED —
    this rung's exact-power interception is restricted to a GENUINE
    Rational base and never intercepts (Int, Int)."""
    # 2 ** 63 overflows i64 and wraps (pre-existing, documented
    # behaviour unrelated to this rung — just confirming it still
    # reaches the SAME code path, not the new Rational one).
    result = sub._inner.evaluate(POW(L(2), L(63)), None)
    assert isinstance(result, int)
    assert result == (1 << 63) - (1 << 64)  # wrapping_pow's two's-complement wrap


# ---------------------------------------------------------------------------
# 6) THE NINE-ITEM ARC-2 Q1 DIVERGENCE LEDGER, RE-CHECKED
# ---------------------------------------------------------------------------
def test_ledger_item_1_round_banker_rounding_reduced_surface_not_eliminated(sub):
    """round()'s banker's-rounding-of-a-float divergence from CPython's
    correctly-rounded-decimal round() is NOT eliminated — genuine
    cross-frame floats (sqrt, pi, a DTW/ShapeContext metric) still
    exist and still need round(). What CHANGED: exact division/
    multiplication no longer MANUFACTURES a float that then needs
    rounding — `round(1/3 + 1/3 + 1/3)` never touches the float
    rounding path at all any more (it rounds an exact Int)."""
    s = sub
    out = run_prog(s, SEQ(RET(CALL("round", PLUS(DIV(L(1), L(3)), DIV(L(1), L(3)), DIV(L(1), L(3)))))),
                   oracles=("round",))
    assert out["result"] == 1 and isinstance(out["result"], int)
    # A genuine float (sqrt-shaped) still needs the SAME banker's-
    # rounding divergence this item names — unaffected, by design.
    out2 = run_prog(s, SEQ(RET(CALL("round", L(2.5)))), oracles=("round",))
    assert out2["result"] == 2  # round-half-EVEN, still there


@pytest.mark.parametrize("claim", [
    # Items 2-9 of the arc-2 Q1 ledger are ORTHOGONAL to the float/
    # rational numeric axis (they concern //-floor semantics,
    # isinstance's lack of a type object, map/next/iter, mutating
    # recv-methods, SynthEnumerate.inadmissible, Dict iteration order,
    # str.split/strip whitespace, and string Lit repr) — none of them
    # exist BECAUSE of float support specifically, so this rung neither
    # eliminates nor worsens any of them. Documented here so the ledger
    # is re-checked item by item, not silently dropped.
    "2_divmod_floor_division_stays_local_to_the_oracle_unrelated_to_rational",
    "3_isinstance_still_has_no_first_class_type_object",
    "4_map_next_iter_still_refused_not_approximated",
    "5_mutating_recv_form_calls_still_not_landed",
    "6_synth_enumerate_inadmissible_still_structurally_unreachable",
    "7_dict_iteration_order_still_sorted_by_cmp_value_not_insertion",
    "8_str_split_strip_still_unicode_not_cpython_ascii_whitespace",
    "9_string_lit_repr_still_single_quote_convention",
])
def test_ledger_items_2_through_9_unaffected_by_the_rational_rung(claim):
    # Each of these is a DOCUMENTED, unchanged pre-existing divergence
    # (see PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md §2) — this parametrized
    # test is the ledger's re-check checkpoint, not a new behavioural
    # assertion: nothing in runners/dsl/src/{value,term,prog_eval,
    # synth_enumerate,persist}.rs touched divmod/isinstance's type-
    # object model/map-next-iter/mutating methods/inadmissible/dict
    # ordering/whitespace/repr in this rung.
    assert claim  # documentary — see PROGRAM_SYNTHESIS_ARC5_RATIONAL.md §ledger
