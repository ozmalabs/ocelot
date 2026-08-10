"""WALL B (cmsg121) — pi1_from_cw + the commutator-subgroup free rank, VERIFIED vs
KNOWN groups. The operators reduce to the held SNF / arithmetic; these tests pin the
known-case verifications (NEVER the exemplar's answer)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import commutator_rank as CR


def test_pi1_from_cw_known_words():
    """pi_1 from the CW attaching word -> the one-relator presentation, vs KNOWN."""
    for word, (name, gens, rels) in CR.KNOWN_PI1.items():
        p = CR.pi1_from_polygon_word(word)
        assert p.generators == gens, f"{name}: gens {p.generators} != {gens}"
        assert p.relators == rels, f"{name}: rels {p.relators} != {rels}"


def test_h1_of_presentation_finite_and_infinite():
    """H_1 via the held SNF over abelianized relations: finite (RP^2) + infinite."""
    rp2 = CR.pi1_from_polygon_word("aa")            # <a | a^2> -> H_1 = Z/2
    h = CR.h1_of_presentation(rp2)
    assert h.finite and h.order == 2 and h.torsion == [2]
    torus = CR.pi1_from_polygon_word("aba-b-")      # <a,b | abAB> -> H_1 = Z^2
    h2 = CR.h1_of_presentation(torus)
    assert not h2.finite and h2.free_rank == 2


def test_commutator_rank_known_free_products():
    """The commutator free rank vs KNOWN groups (rational Euler char): D_inf -> 1,
    modular Z/2*Z/3 -> 2, Z/3^3 -> 28. The compute is held arithmetic over the read
    formula; NONE is the exemplar's answer."""
    for name, orders, known in CR.KNOWN_FREE_PRODUCT_RANK:
        r = CR.free_product_commutator_rank(orders)
        assert r.derived and r.rank == known, f"{name}: rank {r.rank} != {known}"


def test_commutator_rank_guards_stall():
    """The honest GUARDS: (i) an infinite-H_1 presentation STALLS (no finite rank);
    (ii) a proper-power presentation is NOT aspherical and STALLS (the presentation-chi
    is not the group chi). Neither emits a wrong number."""
    # (i) infinite H_1 (the exemplar amalgam): STALL.
    amalgam = CR.pi1_from_relators("abc", ["aaaaaBBBBBBBB", "bbbbbbbbCC"])
    r = CR.commutator_free_rank(amalgam)
    assert not r.derived and "INFINITE" in r.stall
    # (ii) proper-power presentation (modular as <a,b|a^2,b^3>): STALL the presentation
    # route (must use the structural free-product operator instead).
    mod = CR.pi1_from_relators("ab", ["aa", "bbb"])
    r2 = CR.commutator_free_rank(mod)
    assert not r2.derived and "aspherical" in r2.stall


def test_amalgam_connected_sum_verifies_klein():
    """The amalgam connected-sum construction a^2=b^2 reproduces the KNOWN RP^2#RP^2 =
    Klein (H_1 = Z + Z/2). The construction is REFUSED if it fails this known."""
    klein = CR.pi1_from_relators("ab", ["aaBB"])     # a^2 = b^2
    h = CR.h1_of_presentation(klein)
    assert h.free_rank == 1 and h.torsion == [2]
