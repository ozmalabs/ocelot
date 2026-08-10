"""The reasoning loop — comprehend an HLE-domain question, then ANSWER it by
routing the meaning to the substrate's grounded capabilities.

This closes language ⟶ computation: the speech faculty parses the question, and
the math tower computes the result (determinant on the search layer, coset index
by Todd–Coxeter, the next term by recurrence inference, …). It is the capstone
that makes the vocabulary actionable.
"""
from __future__ import annotations

from domains import reason

_S3 = ("ab", ["aa", "bb", "ababab"])      # ⟨a,b | a²,b²,(ab)³⟩, order 6


def test_linear_algebra_questions():
    assert reason.answer("the determinant of M", {"M": [[1, 2], [3, 4]]}) == -2
    assert reason.answer("the trace of M", {"M": [[1, 2], [3, 4]]}) == 5
    assert reason.answer("the rank of M", {"M": [[1, 2], [2, 4]]}) == 1
    assert reason.answer("is M invertible?", {"M": [[1, 2], [3, 4]]}) is True


def test_number_theory_questions():
    assert reason.answer("the gcd of A and B", {"A": 12, "B": 18}) == 6
    assert reason.answer("is p prime?", {"p": 7}) is True
    assert reason.answer("is p prime?", {"p": 9}) is False


def test_group_theory_questions():
    # |S3| via Todd–Coxeter coset enumeration, and [S3 : <a>]
    assert reason.answer("the order of G", {"G": _S3}) == 6
    assert reason.answer("the index of H in G", {"H": ["a"], "G": _S3}) == 3


def test_inference_question():
    # the next term, via recurrence inference (Fibonacci → 13)
    assert reason.answer("the next term of the sequence",
                         {"sequence": [1, 1, 2, 3, 5, 8]}) == 13


def test_equation_solving_question():
    # comprehend the request, then solve the bound equation by rewriting
    assert reason.answer("the solution of the equation",
                         {"equation": (("+", ("*", 2, "x"), 3), 7)}) == 2
    assert reason.answer("the solution of the equation",
                         {"equation": (("+", ("/", "x", 3), 2), 5)}) == 9


def test_linear_system_question():
    # the same 'solution' concept dispatches to Cramer's rule for a system
    assert reason.answer("the solution of the system",
                         {"system": ([[2, 1], [1, 3]], [5, 10])}) == [1, 3]


def test_factorization_from_text_alone():
    # HLE i=496: "the largest prime divisor of 8139881" — answered straight from
    # the question text (the number is parsed, no external binding)
    assert reason.answer("what is the largest prime divisor of 8139881", {}) == 5003
    assert reason.answer("the prime factors of 360", {}) == [2, 3, 5]


def test_continuous_distribution_questions():
    from fractions import Fraction
    assert reason.answer("the expectation of X", {"X": ("gamma", 3, 1)}) == 3
    assert reason.answer("the variance of X", {"X": ("uniform", 0, 1)}) == Fraction(1, 12)


def test_unknown_concept_is_reported():
    import pytest
    with pytest.raises(KeyError):
        reason.answer("the genus of X", {"X": "surface"})   # no capability yet
