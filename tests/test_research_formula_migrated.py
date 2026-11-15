"""Strict scientific formula to native Term translation tests."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
             os.path.join(ROOT, "scripts")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from ocelot_research_formula import FormulaTranslationError, translate_formula
from substrate_rs import Substrate


@pytest.mark.parametrize(("source", "expected"), [
    ("p and not q", True),
    ("p or q and r", True),  # Python precedence: and binds more tightly than or.
    ("¬p ∨ q", False),
    ("$x + 2 * y = 8 \\land x < y$", True),
    ("\\neg(p) \\lor q", False),
])
def test_translation_runs_as_native_term(source, expected):
    result = translate_formula(source)
    if source == "p and not q":
        assert result.residuals == ()
    native = Substrate()
    env = {"p": True, "q": False, "r": True, "x": 2, "y": 3}
    assert native._inner.evaluate(result.term, env) is expected


def test_reports_sorted_variables_and_native_shape():
    result = translate_formula("z and (a or not z)")
    assert result.variables == ("a", "z")
    assert result.variable_sorts == {"a": "bool", "z": "bool"}
    assert result.result_sort == "bool"
    assert result.term["type"] == "And"


@pytest.mark.parametrize("source", [
    "", "p and", "f(p)", "p.x", "p implies q", "x < y < z",
    r"p \landevil q", r"p \land_foo q",
    "p and __import__('os').system('true')",
])
def test_unsupported_or_incomplete_formula_is_rejected(source):
    with pytest.raises(FormulaTranslationError) as err:
        translate_formula(source)
    assert err.value.residuals


def test_single_math_equals_and_integer_arithmetic_compile_to_arithmetic_term():
    result = translate_formula("$n = (2 + 3) * 4$")
    assert result.variables == ("n",)
    assert result.term["type"] == "Eq"
    assert Substrate()._inner.evaluate(result.term, {"n": 20}) is True
    assert Substrate()._inner.evaluate(result.term, {"n": 19}) is False


def test_sort_inference_marks_equality_operands_unknown_and_detects_conflict():
    unknown_eq = translate_formula("a = b")
    assert unknown_eq.variable_sorts == {"a": "unknown", "b": "unknown"}
    assert unknown_eq.equality_sort_constraints == (("a", "b"),)
    assert any("unknown required sort" in item for item in unknown_eq.residuals)
    assert any("same runtime sort" in item for item in unknown_eq.residuals)
    assert translate_formula("a = a").equality_sort_constraints == ()
    with pytest.raises(FormulaTranslationError, match="both number and bool"):
        translate_formula("x + 1 = 2 and x")
    with pytest.raises(FormulaTranslationError, match="requires bool"):
        translate_formula("not p + 1")
    with pytest.raises(FormulaTranslationError, match="requires bool"):
        translate_formula("p and (x + 1)")
    constrained = translate_formula("x = y and x + 1 = 2")
    assert constrained.variable_sorts == {"x": "number", "y": "number"}
    assert constrained.equality_sort_constraints == (("x", "y"),)
    assert any("float precision" in item for item in constrained.residuals)


def test_floats_division_fraction_and_integer_power_use_native_numeric_terms():
    native = Substrate()
    frac = translate_formula(r"$\frac{x + 1}{2} = 1.5$")
    assert frac.term["type"] == "IfThenElse"  # zero divisor is unresolved (null)
    assert native._inner.evaluate(frac.term, {"x": 2.0}) is True
    assert native._inner.evaluate(frac.term, {"x": 1.0}) is False
    power = translate_formula("x^2 = 9")
    assert native._inner.evaluate(power.term, {"x": 3}) is True
    assert native._inner.evaluate(power.term, {"x": 2}) is False
    assert native._inner.evaluate(translate_formula("0.1 + 0.2 = 0.3").term, {}) is False


def test_division_by_zero_is_guarded_and_unsafe_power_domains_are_rejected():
    result = translate_formula("x / (y - y) > 2")
    assert Substrate()._inner.evaluate(result.term, {"x": 4, "y": 3}) is None
    assert Substrate()._inner.evaluate(translate_formula("1 / 0 != 1").term, {}) is None
    assert result.preconditions
    nested = translate_formula("x / (y / z) > 2")
    assert Substrate()._inner.evaluate(nested.term, {"x": 4, "y": 1, "z": 0}) is None
    with pytest.raises(FormulaTranslationError, match="non-negative integer literal"):
        translate_formula("x ^ -1 > 0")
    with pytest.raises(FormulaTranslationError, match="non-negative integer literal"):
        translate_formula("x ^ 0.5 > 0")


@pytest.mark.parametrize("source", ["1e309 = 0", "9223372036854775808 = 0",
                                    "-9223372036854775809 = 0"])
def test_nonfinite_float_and_out_of_range_integer_literals_are_rejected(source):
    with pytest.raises(FormulaTranslationError):
        translate_formula(source)


def test_signed_64_bit_integer_boundaries_are_accepted():
    native = Substrate()
    assert native._inner.evaluate(translate_formula("9223372036854775807 = 9223372036854775807").term, {}) is True
    assert native._inner.evaluate(translate_formula("-9223372036854775808 = -9223372036854775808").term, {}) is True


def test_safe_numeric_functions_and_static_scalar_index_notation():
    native = Substrate()
    absolute = translate_formula("abs(x) = 3")
    assert absolute.variables == ("x",)
    assert native._inner.evaluate(absolute.term, {"x": -3}) is True
    extrema = translate_formula("min(x_1, 4) < max(y[2], 5)")
    assert extrema.variables == ("x_1", "y_2")
    assert native._inner.evaluate(extrema.term, {"x_1": 3, "y_2": 6}) is True
    latex_subscript = translate_formula(r"x_{i} = 2")
    assert latex_subscript.variables == ("x_i",)
    assert native._inner.evaluate(latex_subscript.term, {"x_i": 2}) is True


@pytest.mark.parametrize("source", ["sqrt(x) > 0", "log(x) > 0", "exp(x) > 0",
                                    "min(x) > 0", "abs(x, y) > 0", "x[i] > 0"])
def test_unsafe_functions_or_dynamic_indices_remain_rejected(source):
    with pytest.raises(FormulaTranslationError):
        translate_formula(source)


def test_real_paper_boxed_latex_scalar_equalities_preserve_symbolic_identifiers():
    with pytest.raises(FormulaTranslationError, match="ambiguous between an index and exponent"):
        translate_formula(r"\boxed{\delta^P=a,}")
    delta = translate_formula(r"\boxed{\delta_P=a,}")
    assert delta.variables == ("a", "delta_P")
    assert delta.term["type"] == "Eq"
    assert delta.equality_sort_constraints == (("delta_P", "a"),)

    energy = translate_formula(r"\[\boxed{U_{\mathcal F}=0.}\]")
    assert energy.variables == ("U_F",)
    assert energy.variable_sorts == {"U_F": "int"}
    assert Substrate()._inner.evaluate(energy.term, {"U_F": 0}) is True


def test_latex_text_symbols_spacing_and_delimiters_keep_opaque_label_semantics():
    result = translate_formula(r"$\boxed{\mathrm{NULL}\;\neq\;\mathrm{undetermined}.}$")
    assert Substrate()._inner.evaluate(result.term, {}) is True
    assert any("opaque string symbols" in item for item in result.residuals)
    text_symbols = translate_formula(r"\(\text{determinable}\neq\text{determined}\)")
    assert Substrate()._inner.evaluate(text_symbols.term, {}) is True
    typed_symbol = translate_formula(r"x=\mathrm{NULL}")
    assert typed_symbol.variable_sorts == {"x": "symbol"}
    assert Substrate()._inner.evaluate(typed_symbol.term, {"x": "NULL"}) is True


def test_ambiguous_implicit_products_get_residual_and_uninterpreted_functions_reject():
    result = translate_formula(r"E_0=mc^2")
    assert result.variables == ("E_0", "mc")
    assert any("not implicit products" in item for item in result.residuals)
    with pytest.raises(FormulaTranslationError, match="uninterpreted function"):
        translate_formula(r"\operatorname{Id}_W(G)=G")


@pytest.mark.parametrize("source", [r"\boxed{G=(g,r,\Gamma),}",
                                    r"\boxed{T\in\mathcal F}",
                                    r"\boxed{a<b<c}"])
def test_structural_or_chained_latex_notation_is_not_flattened_to_a_false_formula(source):
    with pytest.raises(FormulaTranslationError):
        translate_formula(source)


def test_compact_letters_report_implicit_multiplication_ambiguity():
    from scripts.ocelot_research_formula import translate_formula
    result = translate_formula('E_0 = mc^2')
    assert 'mc' in result.variables
    assert any('not implicit products' in item for item in result.residuals)


def test_explicit_implicit_product_mapping_preserves_power_precedence_and_records_choice():
    source = "E_0=mc^2"
    default = translate_formula(source)
    assert default.variables == ("E_0", "mc")
    assert any("not implicit products" in item for item in default.residuals)

    translated = translate_formula(source, implicit_products={"mc": ["m", "c"]})
    assert translated.term["type"] == "Eq"
    rhs = translated.term["b"]
    assert rhs["type"] == "Times"
    assert rhs["items"][0] == {"type": "Var", "name": "m"}
    assert rhs["items"][1]["type"] == "Pow"
    assert translated.variables == ("E_0", "c", "m")
    assert any("user-selected implicit product mapping 'mc' -> m * c" in item
               for item in translated.residuals)
    native = Substrate()
    assert native._inner.evaluate(translated.term, {"E_0": 18, "m": 2, "c": 3}) is True
    assert native._inner.evaluate(translated.term, {"E_0": 36, "m": 2, "c": 3}) is False


def test_implicit_product_rewriting_changes_name_tokens_only_not_text_labels():
    label = translate_formula(r"\text{mc}=\mathrm{mc}", implicit_products={"mc": ["m", "c"]})
    assert label.variables == ()
    assert label.term["a"]["value"] == label.term["b"]["value"] == "mc"
    assert Substrate()._inner.evaluate(label.term, {}) is True
    other_name = translate_formula("amc=6", implicit_products={"mc": ["m", "c"]})
    assert other_name.variables == ("amc",)


@pytest.mark.parametrize("mapping", [
    {"mc": ["m"]}, {"mc": "m*c"}, {"m*c": ["m", "c"]},
    {"mc": ["m", "c"], "m": ["a", "b"]}, {"mc": ["mc", "c"]},
    {"True": ["m", "c"]},
])
def test_invalid_implicit_product_mappings_are_refused(mapping):
    with pytest.raises(FormulaTranslationError):
        translate_formula("E_0=mc^2", implicit_products=mapping)


def test_distinct_greek_glyphs_are_not_silently_identified():
    from scripts.ocelot_research_formula import translate_formula
    result = translate_formula(r'\epsilon = \varepsilon')
    assert set(result.variables) == {'epsilon', 'varepsilon'}
    assert any('Greek' in x for x in result.residuals)
