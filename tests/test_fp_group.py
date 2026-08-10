"""Tests for finitely-presented groups by REWRITING.

A presentation ⟨generators | relations⟩ and each word live in the graph; an
element is a word, and computing in the group is rewriting words to a normal
form by applying the relations. The (infinite) group is never enumerated.
"""
from __future__ import annotations

import itertools

from domains import fp_group as fp
from substrate import TypedGraph


def _Dinf():
    """The infinite dihedral group ⟨a, b | a²=e, b²=e⟩."""
    g = TypedGraph()
    pres = fp.present(g, "Dinf", "ab", [("aa", ""), ("bb", "")])
    return g, pres


def test_words_reduce_to_normal_form():
    g, pres = _Dinf()
    cases = {"aabba": "a", "abba": "", "abab": "abab", "bbbb": "", "aab": "b"}
    for spelling, nf in cases.items():
        word = fp.make_word(g, spelling, spelling)
        assert fp.normal_form(g, word, pres) == nf


def test_equality_by_normal_form():
    g, pres = _Dinf()
    assert fp.equal(g, fp.make_word(g, "a1", "aabba"),
                    fp.make_word(g, "a2", "a"), pres) is True
    assert fp.equal(g, fp.make_word(g, "b1", "abab"),
                    fp.make_word(g, "b2", "ba"), pres) is False


def test_group_operation_is_concat_and_reduce():
    g, pres = _Dinf()
    # ab · ba = abba = e  (the relations make it the identity)
    prod = fp.multiply(g, "p", fp.make_word(g, "ab", "ab"),
                       fp.make_word(g, "ba", "ba"), pres)
    assert prod == ""


def test_free_reduction_with_inverses():
    g = TypedGraph()
    # free group ⟨a, b⟩ with A = a⁻¹, B = b⁻¹: cancel inverse pairs
    F = fp.present(g, "F", "abAB",
                   [("aA", ""), ("Aa", ""), ("bB", ""), ("Bb", "")])
    assert fp.normal_form(g, fp.make_word(g, "w1", "abAB"), F) == "abAB"
    assert fp.normal_form(g, fp.make_word(g, "w2", "aAbB"), F) == ""
    assert fp.normal_form(g, fp.make_word(g, "w3", "abBA"), F) == ""


def _normal_forms(graph, pres, gens, upto=7):
    forms = set()
    for L in range(upto + 1):
        for tup in itertools.product(gens, repeat=L):
            spelling = "".join(tup)
            w = fp.make_word(graph, f"t_{spelling}_{L}", spelling)
            forms.add(fp.normal_form(graph, w, pres))
    return forms


def test_knuth_bendix_makes_finite_groups_confluent():
    """An arbitrary presentation isn't confluent (too many normal forms); after
    KB completion the number of distinct normal forms equals the group order."""
    # Klein four-group V4 = ⟨a,b | a²=e, b²=e, (ab)²=e⟩, order 4
    g = TypedGraph()
    raw = fp.present(g, "V4r", "ab", [("aa", ""), ("bb", ""), ("abab", "")])
    assert len(_normal_forms(g, raw, "ab")) > 4          # non-confluent
    kb = fp.present(g, "V4k", "ab", [("aa", ""), ("bb", ""), ("abab", "")])
    fp.complete_presentation(g, kb)
    assert len(_normal_forms(g, kb, "ab")) == 4          # captures V4 exactly

    # Symmetric group S3 = ⟨a,b | a²=e, b²=e, (ab)³=e⟩, order 6 (non-abelian)
    g2 = TypedGraph()
    raw2 = fp.present(g2, "S3r", "ab", [("aa", ""), ("bb", ""), ("ababab", "")])
    assert len(_normal_forms(g2, raw2, "ab")) > 6
    kb2 = fp.present(g2, "S3k", "ab", [("aa", ""), ("bb", ""), ("ababab", "")])
    fp.complete_presentation(g2, kb2)
    assert len(_normal_forms(g2, kb2, "ab")) == 6


def test_completion_resolves_all_critical_pairs():
    """The completed system is confluent: every critical pair reduces to a
    single result (no further rule needed)."""
    rules = fp.complete([("aa", ""), ("bb", ""), ("ababab", "")])
    for p, q in fp._critical_pairs(rules):
        assert fp._reduce_str(p, rules) == fp._reduce_str(q, rules)


def test_cosets_lagrange_and_quotient():
    """In S3 (KB-completed), cosets/quotients computed entirely by rewriting:
    Lagrange holds, ⟨a⟩ is non-normal (3 cosets), ⟨ab⟩ is normal (quotient ≅ Z2)."""
    g = TypedGraph()
    S3 = fp.present(g, "S3", "ab", [("aa", ""), ("bb", ""), ("ababab", "")])
    fp.complete_presentation(g, S3)
    G = fp.elements(g, S3, "ab")
    assert len(G) == 6

    H = fp.subgroup_closure(g, S3, ["a"])            # order-2 subgroup
    cosets_H = fp.left_cosets(g, S3, G, H)
    assert len(H) == 2
    assert len(cosets_H) == 3                         # index 3
    assert len(G) == len(cosets_H) * len(H)           # Lagrange
    assert fp.is_normal(g, S3, G, H) is False         # ⟨a⟩ not normal in S3

    N = fp.subgroup_closure(g, S3, ["ab"])            # the rotation subgroup A3
    cosets_N = fp.left_cosets(g, S3, G, N)
    assert len(N) == 3
    assert len(cosets_N) == 2                          # index 2
    assert fp.is_normal(g, S3, G, N) is True           # normal → quotient S3/N
    # the quotient has order = index = 2 (≅ Z2)
    assert len(cosets_N) == 2


def test_todd_coxeter_indices():
    """Coset enumeration computes [G:H] — including the order |G|=[G:1]."""
    S3 = ["aa", "bb", "ababab"]            # involution generators: self-inverse
    assert fp.coset_index("ab", S3, []) == 6          # |S3|
    assert fp.coset_index("ab", S3, ["a"]) == 3       # [S3:⟨a⟩]
    assert fp.coset_index("ab", S3, ["ab"]) == 2      # [S3:⟨ab⟩]
    assert fp.coset_index("ab", ["aa", "bb", "abab"], []) == 4   # |V4|
    # D4: a has order 4, NOT an involution — declare its inverse
    inv = {"a": "A", "A": "a", "b": "b"}
    assert fp.coset_index("ab", ["aaaa", "bb", "abab"], [], inverses=inv) == 8
    assert fp.coset_index("ab", ["aaaa", "bb", "abab"], ["a"], inverses=inv) == 2


def test_todd_coxeter_finite_index_in_infinite_group():
    """The point of TC: a FINITE index inside an INFINITE group — [ℤ:nℤ]=n —
    which enumeration/rewriting could never compute (ℤ is infinite)."""
    invZ = {"a": "A", "A": "a"}
    assert fp.coset_index("a", [], ["aaa"], inverses=invZ) == 3      # [ℤ:3ℤ]
    assert fp.coset_index("a", [], ["aaaaa"], inverses=invZ) == 5    # [ℤ:5ℤ]
    # infinite index does not close — reported, not hung
    import pytest
    with pytest.raises(ValueError):
        fp.coset_index("ab", ["aa", "bb"], ["a"], max_cosets=5000)   # ⟨a⟩ in D∞


def test_index_in_graph_matches():
    g = TypedGraph()
    S3 = fp.present(g, "S3", "ab", [("aa", ""), ("bb", ""), ("ababab", "")])
    assert fp.index_in_graph(g, S3, []) == 6
    assert fp.index_in_graph(g, S3, ["ab"]) == 2


def test_low_index_subgroups_counts():
    """Enumerate subgroups up to a given index, each counted once."""
    # Free group F2: the Hall numbers 1, 3, 13, 71 for index 1..4
    f2 = fp.low_index_subgroups("ab", [], 4,
                                inverses={"a": "A", "A": "a", "b": "B", "B": "b"})
    assert f2 == {1: 1, 2: 3, 3: 13, 4: 71}

    # S3: G (idx1), A3 (idx2), three order-2 (idx3), trivial (idx6) — 6 total
    s3 = fp.low_index_subgroups("ab", ["aa", "bb", "ababab"], 6)
    assert s3 == {1: 1, 2: 1, 3: 3, 4: 0, 5: 0, 6: 1}
    assert sum(s3.values()) == 6

    # Z (infinite): exactly one subgroup nZ of each index
    z = fp.low_index_subgroups("a", [], 4, inverses={"a": "A", "A": "a"})
    assert z == {1: 1, 2: 1, 3: 1, 4: 1}
