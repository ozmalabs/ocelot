"""prog_exact -- the EXACT-FIRST rung's mechanical half (PROGRAM_SYNTHESIS_
ARC5_EXACT_FIRST.md, the shape-first proposal layer PROGRAM_SYNTHESIS_
ARCH_DIAGNOSIS.md names as missing: "shape -> IR").

CLAUDE.md's frame/continuum invariant is the law this module honours: a
family's PARAMETERS (the rational coefficient k, the per-argument integer
exponents) are always integers/rationals -- IN-FRAME data. A family's named
CROSS-FRAME CONSTANT (pi, sqrt2, sqrt3) is a fixed double, applied once at
the render boundary (`render_family_to_ir`), never stored as a fitted
parameter. "You can apply pi, but any given circle is stepped."

ARCHITECTURE (CLAUDE.md). Every function here is MECHANICAL:

  interval_rows        read `mbpp_spec`-shaped rows ({"inputs","expected",
                        ["tol"]}) into (arg_values, expected, tolerance)
                        triples in a fixed argument order -- pure
                        translation, exactly the `mbpp_spec.parse_asserts`
                        class of function (ast-shaped in, tuple-shaped out,
                        no branching on agent/graph state).

  family_from_substrate /
  all_families_ordered  Mechanical graph QUERY: read one/all `ExactFamily`
                        seed node(s) (seeds/exact_families.json) into a
                        plain dict -- a lookup, never a decision (the
                        `_template_by_name` precedent in prog_synthesis.py).

  fit_family            A BOUNDED, DETERMINISTIC numeric search over the
                        family's OWN declared parameter grid (read from the
                        `ExactFamily` node, never hand-tuned per task),
                        returning the FIRST parameter vector that satisfies
                        every row within its tolerance, plus an honest
                        candidate count whether it succeeds or exhausts.
                        This is a fixed ALGORITHM applied to DATA -- the
                        same class of computation as `_decode_order`'s
                        Viterbi lattice or `_row_cmp_ok`'s fixed-formula
                        comparator, both already-admissible Python in this
                        domain: it never reads agent/graph STATE to decide
                        what the agent should do next (that decision --
                        whether a fit counts as a rung success, what
                        happens on failure -- lives entirely in
                        seeds/program_synthesis.json's ps_exact_* rules,
                        which only ever consume the recorded outcome FACT).

  render_family_to_ir   Mechanical shape -> IR: instantiate a family's
                        template with its found parameters into hub IR
                        (ProgSeq/ProgReturn over Times/Plus/Pow/Lit/Var
                        Terms, `k` an exact rational Lit -- not a runtime
                        `Div`, PROGRAM_SYNTHESIS_ARC5_RATIONAL.md) -- the
                        missing "shape -> IR" step the
                        diagnosis names. No decision: one family, one
                        parameter vector, one deterministic IR shape.

Two families only (seeds/exact_families.json's own docstring), in Occam
order (`order` attr ascending): `scaled_power_product` (k*C^p*prod(arg^e),
one term) tried first; `sum_of_two_terms` (two scaled_power_product terms
SHARING one (k,C), PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md's one measured
gap, task 574) tried only once the first exhausts. `sum_of_two_terms` is
scoped to arity<=2 -- the single measured case (574, cylinder surface,
r and h) needs no more, and an unscoped two-independent-term family would
both blow up the search and raise the coincidental-fit risk with no
measured justification (named as a residual in the design doc, not built
speculatively, per CLAUDE.md's "no speculative extras" law already applied
once in this arc -- PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md's own
"zero MBPP tasks need an in-frame float").
"""
from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Tuple

_ABS_TOL_FLOOR = 1e-9


# --------------------------------------------------------------------------- #
#  tiny local helpers (this module is deliberately self-contained -- no
#  import of domains.prog_synthesis, which imports THIS module).
# --------------------------------------------------------------------------- #
def _text(v) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v)


def _plain_list(v) -> list:
    if v is None:
        return []
    return [x for x in v]


# --------------------------------------------------------------------------- #
#  interval_rows -- mechanical: a float assert IS an interval constraint.
# --------------------------------------------------------------------------- #
def interval_rows(rows: Sequence[Dict[str, Any]],
                  args: Sequence[str]) -> List[Tuple[List[Any], Any, Optional[float]]]:
    """Translate `mbpp_spec`-shaped rows (`{"inputs": {...}, "expected": ...,
    ["tol": float]}`) into `(arg_values, expected, tol)` triples, argument
    values taken in the fixed `args` order. `tol` is the row's OWN declared
    tolerance (an interval half-width around `expected` -- PROGRAM_SYNTHESIS_
    ARC5_SPECS_IMPLY_FLOATS.md's "read a float assert as an interval
    constraint") when present, else `None` (the caller applies its own
    documented default). Pure translation -- rows missing one of `args`
    raise KeyError rather than silently padding, since that shape is a
    genuine spec/argument-order mismatch, not a fitting decision."""
    out: List[Tuple[List[Any], Any, Optional[float]]] = []
    for r in rows:
        inputs = r["inputs"]
        out.append(([inputs[a] for a in args], r["expected"], r.get("tol")))
    return out


# --------------------------------------------------------------------------- #
#  ExactFamily lookup -- mechanical graph query (the `_template_by_name`
#  precedent), never a decision.
# --------------------------------------------------------------------------- #
def family_from_substrate(sub, name: str) -> Optional[Dict[str, Any]]:
    """Read one `ExactFamily` seed node (seeds/exact_families.json) into a
    plain dict describing its parameter schema. Returns None if `name`
    names no held family (an honest "this shape does not exist" datum, not
    an exception -- the same style as `_template_by_name`'s `{}`)."""
    for n in sub.nodes("ExactFamily"):
        at = sub.node(n)["attrs"]
        if _text(at.get("name")) != name:
            continue
        return {
            "name": name,
            "order": float(at.get("order") or 0.0),
            "min_arity": int(at.get("min_arity") or 1),
            "max_arity": int(at.get("max_arity") or 1),
            "k_numerators": [int(x) for x in _plain_list(at.get("k_numerators"))],
            "k_denominators": [int(x) for x in _plain_list(at.get("k_denominators"))],
            "constants": json.loads(_text(at.get("constants_json")) or "{}"),
            "max_exponent": int(at.get("max_exponent") or 0),
            "default_tol": float(at.get("default_tol") or _ABS_TOL_FLOOR),
            "shared_kc": at.get("shared_kc") == 1.0,
        }
    return None


def all_families_ordered(sub) -> List[Dict[str, Any]]:
    """Every held `ExactFamily`, in Occam order (`order` ascending -- a
    fixed declared field on the seed data, not a fitness score). Mechanical
    read-back; the CALLER decides what to do with the list."""
    names = []
    for n in sub.nodes("ExactFamily"):
        at = sub.node(n)["attrs"]
        names.append((float(at.get("order") or 0.0), _text(at.get("name"))))
    names.sort(key=lambda pair: pair[0])
    out = []
    for _, name in names:
        fam = family_from_substrate(sub, name)
        if fam is not None:
            out.append(fam)
    return out


# --------------------------------------------------------------------------- #
#  the rational/constant/exponent grid -- built once per fit_family call
#  from the family's OWN declared data (never a hand-tuned literal here).
# --------------------------------------------------------------------------- #
def _rational_grid(family: Dict[str, Any]) -> List[Fraction]:
    seen: set = set()
    out: List[Fraction] = []
    pairs = sorted(
        ((d, n) for d in family["k_denominators"] for n in family["k_numerators"]))
    for d, n in pairs:
        fr = Fraction(n, d)
        if fr in seen:
            continue
        seen.add(fr)
        out.append(fr)
    return out


def _close(v: float, expected: Any, tol: Optional[float], default_tol: float) -> bool:
    t = tol if tol is not None else default_tol
    try:
        return math.isclose(v, float(expected), rel_tol=t, abs_tol=_ABS_TOL_FLOOR)
    except (TypeError, ValueError):
        return False


# --------------------------------------------------------------------------- #
#  fit_family -- bounded, deterministic search. Returns (params, n_tested).
#  params is None on exhaustion; n_tested is reported EITHER way (honest
#  budget accounting, the SynthEnumerate halt_reason precedent).
# --------------------------------------------------------------------------- #
def fit_family(family: Dict[str, Any],
               rows: Sequence[Tuple[Sequence[Any], Any, Optional[float]]]
               ) -> Tuple[Optional[Dict[str, Any]], int]:
    """Search `family`'s own declared (k, C, exponent) grid for the FIRST
    vector every row agrees with (within that row's own declared tolerance,
    or the family's `default_tol`). `rows` is `interval_rows`'s own output
    shape. Returns `(params, n_tested)`; `params` is a plain dict
    (`k_num`/`k_den`/`const`/`exps` for `scaled_power_product`,
    `k_num`/`k_den`/`const`/`exps1`/`exps2` for `sum_of_two_terms`) or
    `None` on exhaustion -- `n_tested` is reported in both cases, never
    swallowed (the SynthEnumerate `halt_reason` precedent: exhaustion is an
    honest outcome, not a silent gap)."""
    if not rows:
        return None, 0
    nargs = len(rows[0][0])
    if not (family["min_arity"] <= nargs <= family["max_arity"]):
        return None, 0
    ks = _rational_grid(family)
    consts = list(family["constants"].items())  # [(name, value), ...]
    exps_range = list(range(0, family["max_exponent"] + 1))
    default_tol = family["default_tol"]
    name = family["name"]

    n_tested = 0
    if name == "scaled_power_product":
        for kf in ks:
            for cname, cval in consts:
                variants = (0,) if cname == "1" else (0, 1)
                for p in variants:
                    base = float(kf) * (cval ** p if cname != "1" else 1.0)
                    for exps in itertools.product(exps_range, repeat=nargs):
                        n_tested += 1
                        ok = True
                        for vals, expected, tol in rows:
                            v = base
                            for a, e in zip(vals, exps):
                                v *= a ** e
                            if not _close(v, expected, tol, default_tol):
                                ok = False
                                break
                        if ok:
                            return ({"k_num": kf.numerator, "k_den": kf.denominator,
                                    "const": cname, "exps": list(exps)}, n_tested)
        return None, n_tested

    if name == "sum_of_two_terms":
        if nargs > family["max_arity"]:
            return None, 0
        vecs = list(itertools.product(exps_range, repeat=nargs))
        for kf in ks:
            for cname, cval in consts:
                variants = (0,) if cname == "1" else (0, 1)
                for p in variants:
                    base = float(kf) * (cval ** p if cname != "1" else 1.0)
                    table = []
                    for exps in vecs:
                        vals_per_row = []
                        for vals, _expected, _tol in rows:
                            v = base
                            for a, e in zip(vals, exps):
                                v *= a ** e
                            vals_per_row.append(v)
                        table.append((exps, vals_per_row))
                    for e1, v1 in table:
                        for e2, v2 in table:
                            n_tested += 1
                            ok = True
                            for ci, (_vals, expected, tol) in enumerate(rows):
                                if not _close(v1[ci] + v2[ci], expected, tol,
                                              default_tol):
                                    ok = False
                                    break
                            if ok:
                                return ({"k_num": kf.numerator, "k_den": kf.denominator,
                                        "const": cname, "exps1": list(e1),
                                        "exps2": list(e2)}, n_tested)
        return None, n_tested

    return None, 0


# --------------------------------------------------------------------------- #
#  render_family_to_ir -- shape -> IR, the missing level.
# --------------------------------------------------------------------------- #
def _render_pow_product(k_num: int, k_den: int, const_name: str,
                        const_val: float, exps: Sequence[int],
                        args: Sequence[str]) -> Dict[str, Any]:
    """`k * C^p * prod(arg_i ** e_i)` as hub IR. `k` renders as an INTEGER
    Lit (k_den==1) or a single EXACT RATIONAL Lit (`{"__rational__":
    [k_num, k_den]}`, the wire tag `persist::decode_value`/`ProgEval`
    read as `Value::Rational` -- PROGRAM_SYNTHESIS_ARC5_RATIONAL.md).
    This CARRIES `k` as an exact rational through evaluation instead of
    a `Div` term (Div is a runtime division that ALWAYS collapses to a
    float, by design -- it stays untouched globally because it is used
    pervasively outside program synthesis); the Times this factor feeds
    into is Rational-aware (`term.rs::numeric_variadic`), so the family's
    fitted `k` (e.g. 4/3, 1/3, 1/180) survives multiplication by the
    integer `arg**e` factors exactly, never a bare float Lit for a
    fitted parameter. `C` (when not the trivial "1") renders as its
    pre-computed double -- the ONE legitimate float in this tree, a
    named cross-frame constant applied at the render boundary, not a
    fitted parameter. Each `e_i==0` factor is OMITTED (not
    `Pow(arg, 0)`); `e_i==1` renders as the bare `Var` (not
    `Pow(arg, 1)`) -- the simplest IR for the recovered structure, not
    a stylistic choice."""
    factors: List[Dict[str, Any]] = []
    if not (k_num == 1 and k_den == 1):
        if k_den == 1:
            factors.append({"type": "Lit", "value": k_num})
        else:
            factors.append({"type": "Lit", "value": {"__rational__": [k_num, k_den]}})
    if const_name != "1":
        factors.append({"type": "Lit", "value": const_val})
    for a, e in zip(args, exps):
        if e == 0:
            continue
        var = {"type": "Var", "name": a}
        factors.append(var if e == 1 else
                       {"type": "Pow", "a": var, "b": {"type": "Lit", "value": e}})
    if not factors:
        return {"type": "Lit", "value": 1}
    if len(factors) == 1:
        return factors[0]
    return {"type": "Times", "items": factors}


def render_family_to_ir(family: Dict[str, Any], params: Dict[str, Any],
                        args: Sequence[str]) -> Optional[Dict[str, Any]]:
    """Instantiate `family`'s template with `params` (fit_family's own
    output shape) into a complete `ProgSeq` (params as `ProgDefFnParam`,
    body a single `ProgReturn`) -- the shape -> IR step
    PROGRAM_SYNTHESIS_ARCH_DIAGNOSIS.md names as missing. Returns None for
    an unrecognised family name (defensive only; `fit_family` never returns
    params for a family it does not itself implement)."""
    const_name = params["const"]
    const_val = family["constants"].get(const_name, 1.0)
    if family["name"] == "scaled_power_product":
        term = _render_pow_product(params["k_num"], params["k_den"], const_name,
                                   const_val, params["exps"], args)
    elif family["name"] == "sum_of_two_terms":
        t1 = _render_pow_product(params["k_num"], params["k_den"], const_name,
                                 const_val, params["exps1"], args)
        t2 = _render_pow_product(params["k_num"], params["k_den"], const_name,
                                 const_val, params["exps2"], args)
        term = {"type": "Plus", "items": [t1, t2]}
    else:
        return None
    stmts: List[Dict[str, Any]] = [
        {"type": "ProgDefFnParam", "name": a, "default": None} for a in args]
    stmts.append({"type": "ProgReturn", "value": term})
    return {"type": "ProgSeq", "stmts": stmts}


__all__ = [
    "interval_rows", "family_from_substrate", "all_families_ordered",
    "fit_family", "render_family_to_ir",
]
