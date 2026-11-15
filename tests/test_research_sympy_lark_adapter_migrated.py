from __future__ import annotations

import pytest

from scripts.ocelot_formula_sympy import sympy_lark_candidate


def test_adapter_rejects_invalid_and_oversized_input_without_sympy():
    assert sympy_lark_candidate("") ["status"] == "rejected"
    assert sympy_lark_candidate("x" * 10_001)["status"] == "rejected"
    assert sympy_lark_candidate(None)["status"] == "rejected"


def test_adapter_reports_optional_dependency_absence(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "sympy.parsing.latex":
            raise ModuleNotFoundError("optional test absence")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    result = sympy_lark_candidate(r"x^2 + 1")
    assert result["status"] == "unavailable"
    assert result["verified"] is False
    assert result["is_claim"] is False


def test_adapter_returns_unverified_lark_parse_when_dependencies_support_it():
    pytest.importorskip("sympy")
    pytest.importorskip("lark")
    result = sympy_lark_candidate(r"x^2 + 1")
    if result["status"] != "parsed":
        pytest.skip(result.get("reason", "installed SymPy has no working Lark backend"))
    assert result["adapter"] == "sympy_lark"
    assert result["verified"] is False
    assert result["semantics"] == "unverified_parser_candidate"
    assert "Pow" in result["expression_repr"]
    assert result["parser_versions"] == {"sympy": "1.14.0", "lark": "1.2.2"} or set(result["parser_versions"]) == {"sympy", "lark"}


def test_lark_ambiguity_preserves_each_alternative_and_flags_adjacent_names():
    pytest.importorskip("sympy")
    pytest.importorskip("lark")
    function = sympy_lark_candidate(r"f(x)")
    assert function["status"] == "ambiguous"
    assert len(function["alternatives"]) >= 2
    assert any("Function(Token('SYMBOL', 'f'))" in alternative
               for alternative in function["alternatives"])
    assert any("Mul(Symbol(Token('SYMBOL', 'f'))" in alternative
               for alternative in function["alternatives"])

    product = sympy_lark_candidate("mc")
    assert product["status"] == "ambiguous"
    assert product["has_alternative_parse_tree"] is False
    assert "multi-letter names may be products or single symbols" in product["ambiguity"]
    assert "Mul" in product["expression_repr"]


def test_complex_latex_and_invalid_latex_return_bounded_versioned_results():
    pytest.importorskip("sympy")
    pytest.importorskip("lark")
    integral = sympy_lark_candidate(r"\int_0^1 x^2 dx")
    assert integral["status"] in {"parsed", "ambiguous"}
    assert "Integral" in integral["expression_repr"]
    assert integral["parser_versions"]["sympy"] == "1.14.0"

    invalid = sympy_lark_candidate(r"\frac{")
    assert invalid["status"] == "unparsed"
    assert invalid["exception_type"] == "UnexpectedEOF"
    assert len(invalid["reason"]) <= 1_200
    assert invalid["reason_truncated"] is True
    assert invalid["parser_versions"]["lark"] == "1.2.2"


def test_representation_failure_is_reported_after_successful_parse(monkeypatch):
    sympy = pytest.importorskip("sympy")

    def fail(_expression):
        raise RuntimeError("representation failure")

    monkeypatch.setattr(sympy, "srepr", fail)
    result = sympy_lark_candidate("x^2")
    assert result["status"] == "representation_failed"
    assert result["parse_succeeded"] is True
    assert result["exception_type"] == "RuntimeError"
    assert "representation failure" in result["reason"]
