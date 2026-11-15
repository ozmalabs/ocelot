"""Finite quantified formula translation and native execution."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if path not in sys.path: sys.path.insert(0, path)
pytest.importorskip("substrate_rs")

from ocelot_research_finite_formula import (FiniteFormulaError, MAX_DOMAIN_SIZE,
    translate_finite_formula, validate_environment)
from substrate_rs import Substrate


def evaluate(source, env):
    result = translate_finite_formula(source)
    validate_environment(result, env)
    return Substrate()._inner.evaluate(result.term, env)


def test_exists_and_forall_execute_natively_over_finite_domain():
    assert evaluate("exists(x, D, x > 2)", {"D": [1, 3]}) is True
    assert evaluate("forall(x, D, x > 0)", {"D": [1, 3]}) is True
    assert evaluate("forall(x, D, x > 0)", {"D": [0, 3]}) is False
    assert evaluate("forall(x, D, x > 0)", {"D": []}) is True
    assert evaluate("exists(x, D, x > 0)", {"D": []}) is False


def test_nested_shadowing_and_free_inputs_are_reported():
    result = translate_finite_formula("forall(x, D, exists(x, E, x > threshold))")
    assert result.variables == ("threshold",)
    assert result.domains == ("D", "E")
    assert result.variable_sorts["threshold"] == "int"
    assert Substrate()._inner.evaluate(result.term, {"D": [100], "E": [2, 5], "threshold": 4}) is True


def test_boolean_binder_sort_and_domain_validation():
    result = translate_finite_formula("forall(p, Flags, p or q)")
    assert result.domain_sorts == {"Flags": "bool"}
    assert result.variable_sorts == {"q": "bool"}
    validate_environment(result, {"Flags": [True, False], "q": False})
    for bad in ([True, 1], [1, "x"], 4, list(range(MAX_DOMAIN_SIZE + 1))):
        with pytest.raises(ValueError): validate_environment(result, {"Flags": bad, "q": False})


@pytest.mark.parametrize("source", ["forall(x, D, x + True > 0)",
                                    "__import__('os').system('true')", "exists(x, D, f(x))"])
def test_bad_types_and_calls_are_refused(source):
    with pytest.raises(FiniteFormulaError): translate_finite_formula(source)


def test_boolean_binder_rejects_integer_domain():
    result = translate_finite_formula("forall(x, D, x)")
    assert result.domain_sorts == {"D": "bool"}
    with pytest.raises(ValueError): validate_environment(result, {"D": [1, 2]})


def test_environment_checks_missing_inputs_and_cartesian_work_budget():
    with pytest.raises(ValueError, match="missing"):
        validate_environment(translate_finite_formula("p and exists(x, D, x > 0)"), {"D": [1]})
    result = translate_finite_formula("forall(x, D, exists(y, D, x < y))")
    with pytest.raises(ValueError, match="work"):
        validate_environment(result, {"D": list(range(101))})


def test_unknown_sorts_still_validate_native_runtime_values_and_i64_ranges():
    scalar = translate_finite_formula("a = b")
    with pytest.raises(ValueError): validate_environment(scalar, {"a": object(), "b": 1})
    with pytest.raises(ValueError, match="i64"):
        validate_environment(scalar, {"a": 2**63, "b": 2**63})
    domain = translate_finite_formula("forall(x, D, True)")
    with pytest.raises(ValueError, match="i64"):
        validate_environment(domain, {"D": [-(2**63) - 1]})


def test_equality_sort_constraints_do_not_include_binders():
    result = translate_finite_formula("forall(x, D, x > 0) and a = b")
    assert result.equality_sort_constraints == (("a", "b"),)


def test_integer_arithmetic_executes_when_validated_and_refuses_possible_overflow():
    source = "forall(x, D, x + 1 > 0)"
    assert evaluate(source, {"D": [1, 2]}) is True
    translated = translate_finite_formula(source)
    with pytest.raises(ValueError, match="overflow"):
        validate_environment(translated, {"D": [2**63 - 1]})
    scalar = translate_finite_formula("n * 2 > 0")
    with pytest.raises(ValueError, match="overflow"):
        validate_environment(scalar, {"n": 2**62})


@pytest.mark.parametrize("source", [
    "forall x in D: (x > 0)",
    "∀x ∈ D: (x > 0)",
    r"\forall x \in D: (x > 0)",
    "forall x in D: (exists y in E: (x < y))",
])
def test_strict_quantifier_notation_rewrites_to_native_terms(source):
    result = translate_finite_formula(source)
    env = {"D": [1, 2], "E": [3]}
    validate_environment(result, env)
    assert Substrate()._inner.evaluate(result.term, env) is True


def test_rejects_out_of_range_integer_literal():
    import pytest
    from scripts.ocelot_research_finite_formula import FiniteFormulaError, translate_finite_formula
    with pytest.raises(FiniteFormulaError, match='i64'):
        translate_finite_formula('forall(x, D, x < 9223372036854775808)')


def test_intermediate_overflow_rejected_even_if_final_interval_fits():
    import pytest
    from scripts.ocelot_research_finite_formula import translate_finite_formula, validate_environment
    tr = translate_finite_formula('forall(x, D, ((x + 1) - 1) > 0)')
    with pytest.raises(ValueError, match='overflow'):
        validate_environment(tr, {'D': [2**63 - 1]})
