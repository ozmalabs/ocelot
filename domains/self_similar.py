"""Self-similar (automaton) groups — groups beyond finite presentations.

The finitely-presented machinery (Knuth–Bendix, Todd–Coxeter, low-index) needs
finite relators. The Grigorchuk group — the famous group of intermediate growth
— has none: it is finitely GENERATED but infinitely PRESENTED, defined instead
by its action on the infinite rooted binary tree via a WREATH RECURSION
(a finite automaton). This module adds that representation.

A tree automorphism g is given by a top permutation σ(g) ∈ S₂ and two SECTIONS
(g₀, g₁) — its action on the two subtrees — themselves group elements:
    g·(x w) = σ(g)(x) · (g_x · w).
Grigorchuk's generators:  a = σ (rooted swap),  b = (a, c),  c = (a, d),
    d = (1, b)  — a,b,c,d are involutions and bc=d, cd=b, bd=c (so bcd=1).

The WORD PROBLEM is decidable by recursion (the group is contracting): a word is
trivial iff its top permutation is identity and both its sections are trivial.
Here we decide "trivial on the tree up to depth n" — exact for any nontriviality
that surfaces by depth n (the group is residually finite, so it always does).
"""
from __future__ import annotations

from itertools import product

# generator → (top permutation, section on 0, section on 1).
# "swap" flips the leading bit; sections are words ('' = identity).
GRIGORCHUK = {
    "a": ("swap", "", ""),
    "b": ("id", "a", "c"),
    "c": ("id", "a", "d"),
    "d": ("id", "", "b"),
}


def _act_gen(g: str, leaf: list, recur: dict) -> list:
    """Apply one generator to a leaf (a list of bits): permute the leading bit,
    then act on the suffix with the section indexed by the original leading bit."""
    if not leaf:
        return leaf
    sigma, s0, s1 = recur[g]
    x, rest = leaf[0], leaf[1:]
    nx = (1 - x) if sigma == "swap" else x
    sec = s0 if x == 0 else s1
    nrest = list(act(sec, rest, recur)) if sec else rest
    return [nx] + nrest


def act(word: str, leaf, recur: dict = GRIGORCHUK) -> tuple:
    """The action of a word (read as a left action: rightmost generator first)
    on a tree-leaf — returns where the leaf is sent."""
    cur = list(leaf)
    for g in reversed(word):
        cur = _act_gen(g, cur, recur)
    return tuple(cur)


def is_trivial(word: str, depth: int, recur: dict = GRIGORCHUK) -> bool:
    """Does ``word`` act trivially on the tree up to ``depth`` — i.e. fix every
    one of the 2^depth leaves? The word problem (exact once depth is deep enough
    to surface any nontriviality)."""
    return all(act(word, leaf, recur) == leaf
               for leaf in product((0, 1), repeat=depth))


def equal(u: str, v: str, depth: int, recur: dict = GRIGORCHUK) -> bool:
    """Do two words name the same element? (u·v⁻¹ trivial; generators here are
    involutions so the inverse of a word is its reverse.)"""
    return is_trivial(u + v[::-1], depth, recur)


def order(word: str, depth: int, cap: int = 64, recur: dict = GRIGORCHUK):
    """The order of the element's action on the depth-``depth`` tree (a finite
    quotient): the least k with word^k trivial there, or None if > ``cap``.
    A STABLE value across depths is the element's true order (Grigorchuk's
    a,b,c,d have order 2, and (ad)⁴=1 — a genuine relation); a value that GROWS
    with depth signals infinite order (e.g. ab)."""
    for k in range(1, cap + 1):
        if is_trivial(word * k, depth, recur):
            return k
    return None
