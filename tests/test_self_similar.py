"""Self-similar (automaton) groups — the Grigorchuk group, which has NO finite
presentation. Represented by its wreath recursion on the binary tree; the word
problem is decided by recursion (trivial-up-to-depth). This is group machinery
beyond the finitely-presented floor.
"""
from __future__ import annotations

from domains import self_similar as ss

_D = 7


def test_grigorchuk_relations():
    # a,b,c,d are involutions, and bcd = 1 (the Klein-four among b,c,d)
    for w in ("aa", "bb", "cc", "dd", "bcd"):
        assert ss.is_trivial(w, _D)
    assert ss.equal("bc", "d", _D)
    assert ss.equal("bd", "c", _D)
    assert ss.equal("cd", "b", _D)


def test_word_problem_distinguishes_elements():
    assert not ss.is_trivial("a", _D)
    assert not ss.is_trivial("ad", _D)
    assert not ss.equal("b", "c", _D)        # distinct generators
    assert ss.equal("a", "aaa", _D)          # a involution: a == a³


def test_element_orders():
    assert ss.order("a", _D) == 2            # involution
    # (ad)⁴ = 1 — a genuine Grigorchuk relation; ad is order 4, not less
    assert ss.order("ad", _D) == 4
    assert not ss.is_trivial("ad", _D) and not ss.is_trivial("adad", _D)
    assert ss.is_trivial("adadadad", _D)


def test_infinite_order_signature():
    # ab's truncated order GROWS with depth — the signature of infinite order
    assert ss.order("ab", 3) < ss.order("ab", 6)
