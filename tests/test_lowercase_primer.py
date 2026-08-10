"""Recognition by INTENDED CONSTRUCTION -- the lowercase primer (the instruction sheet).

A letter is recognised against its ductus (the handwriting-primer formation: "an a is a bowl +
a stem down the right"), not against a stored exemplar. These gates check that (1) the verdict
reads each bowl-family construction as itself, (2) it separates the a/o pair that exemplar
ink-mass drowns, and (3) `author_primer` installs each construction into the substrate as a real
ShapeSignature carrying its `strokeq` skeleton -- the agent holds the instruction sheet as data.
"""
from __future__ import annotations

import numpy as np

from domains import lowercase_primer as lp


def _native():
    from substrate_rs import _native as n
    return n.Substrate()


def _perturb(strokes, seed):
    g = np.random.default_rng(seed)
    s = 1.0 + g.uniform(-0.05, 0.05)
    return [np.asarray(pts, float) * s + g.normal(0, 0.01, np.asarray(pts).shape)
            for _role, pts in strokes]


def test_each_construction_reads_as_itself():
    """A slightly perturbed rendering of each primer construction reads back as that letter --
    the render-compare verdict recognises the intended form."""
    native = _native()
    for c in lp.PRIMER:
        q = _perturb(lp.PRIMER[c], seed=hash(c) % 1000)
        r = lp.read_by_construction(native, q)
        assert r["winner"] == c, f"{c!r} misread as {r['winner']!r}: {r['scores'][:3]}"


def test_a_and_o_separate_on_the_stem():
    """The pair exemplar ink-mass drowns: an a-shaped query (bowl + a stem that pokes below)
    reads a, an o-shaped query (bowl only) reads o -- the intended stem, however small, decides."""
    native = _native()
    a_q = _perturb(lp.PRIMER["a"], seed=1)
    o_q = _perturb(lp.PRIMER["o"], seed=2)
    ra = lp.read_by_construction(native, a_q, candidates=["a", "o"])
    ro = lp.read_by_construction(native, o_q, candidates=["a", "o"])
    assert ra["winner"] == "a", ra
    assert ro["winner"] == "o", ro


def test_closure_intent_separates_o_from_c():
    """o and c have the same bowl shape; the CLOSURE INTENT (does the stroke return to its start)
    decides. A closed bowl reads o, an open bowl reads c -- the motor trace, not the shape."""
    native = _native()
    o_q = _perturb(lp.PRIMER["o"], seed=5)
    c_q = _perturb(lp.PRIMER["c"], seed=6)
    assert lp.bowl_closure(o_q) < 0.30 < lp.bowl_closure(c_q), \
        (lp.bowl_closure(o_q), lp.bowl_closure(c_q))
    assert not lp._closes("c") and lp._closes("o")
    ro = lp.read_by_construction(native, o_q, candidates=["o", "c"])
    rc = lp.read_by_construction(native, c_q, candidates=["o", "c"])
    assert ro["winner"] == "o" and rc["winner"] == "c", (ro, rc)


def test_prototypes_are_nondegenerate():
    """Every primer letter renders to a real whole-figure point set."""
    for c in lp.PRIMER:
        proto = lp.prototype(c)
        assert proto is not None and len(proto) == lp._N
        assert np.abs(proto).max() <= 1.0 + 1e-6


def test_author_primer_installs_constructions_into_the_substrate():
    """`author_primer` grows each construction into the character codebook as a real
    ShapeSignature with a `strokeq` skeleton -- the substrate now HOLDS the instruction sheet."""
    from substrate.boot_core import boot_core
    s, _ag = boot_core()
    lp.author_primer(s, letters=["o", "a"])
    chars = {s.node(n)["attrs"]["name"]: s.node(n)["attrs"]
             for n in s.nodes("ShapeSignature")
             if s.node(n)["attrs"].get("kind") == "character"}
    assert "lc_o" in chars and "lc_a" in chars
    import json
    o_sig = json.loads(chars["lc_o"]["signature"])
    a_sig = json.loads(chars["lc_a"]["signature"])
    strokeqs = lambda sig: [t for t in sig if t and t[0] == "strokeq"]
    assert len(strokeqs(o_sig)) == 1, "o is one intended stroke (the bowl)"
    assert len(strokeqs(a_sig)) == 2, "a is two intended strokes (bowl + stem)"
