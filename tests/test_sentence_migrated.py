"""bigville R27 (block 315000): sentencing by collapse, bounded by law. On a guilty
verdict the council DECIDES the custodial term by an Argmax collapse whose option
set is the offence's statutory [min_term, max_term]. Gates mirror
BIGVILLE_SENTENCE_PREREG.md. The sentence is the sn_sentence seed rule.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_sentence_world import BigvilleSentenceWorld   # noqa: E402

# a bench that convicts a low-standing defendant 3/5.
_BENCH = [
    ("H1", dict(bloc="rich", credence=1.5, punitiveness=1.5, deference=0.5)),
    ("H2", dict(bloc="rich", credence=1.5, punitiveness=1.0, deference=0.5)),
    ("H3", dict(bloc="poor", credence=1.2, punitiveness=0.8, deference=0.5)),
    ("L1", dict(bloc="poor", credence=0.5, punitiveness=-1.0, deference=0.5)),
    ("L2", dict(bloc="poor", credence=0.4, punitiveness=-1.5, deference=0.5)),
]
# a bench where all five convict (5/5).
_ALL_HARSH = [
    (f"A{i}", dict(bloc="poor" if i % 2 else "rich", credence=1.5,
                   punitiveness=1.2, deference=0.3)) for i in range(5)
]


def _court(bench=_BENCH):
    w = BigvilleSentenceWorld()
    for n, d in bench:
        w.add_councillor(n, **d)
    w.add_constable("Dogberry")
    return w


# ------------------------------------------------------ G-sentence-is-decided (headline)
def test_council_sets_a_custodial_term_by_collapse():
    w = _court()
    w.add_sentence_law("theft", min_term=1, max_term=10)
    w.add_resident("Nym", coin=30.0, standing=0.0)
    ch = w.prosecute("Nym", "theft", evidence=1.0, penalty=4.0, threshold=3, base_days=4)
    w.run()
    assert w.verdict(ch) == "guilty"
    # no jail_term was prescribed on the charge -- the council chose it.
    assert w.sentence_term(ch) == 4, w.sentence_term(ch)
    assert w.jail_roll() == ["Nym"] and w.remaining("Nym") == 4


# ------------------------------------------------------ G-upper-bound-by-law (headline)
def test_sentence_is_capped_at_the_statutory_maximum():
    w = _court()
    w.add_sentence_law("theft", min_term=1, max_term=5)
    w.add_resident("Greedy", coin=30.0, standing=0.0)
    # base_days 20 -> desired far above the ceiling.
    ch = w.prosecute("Greedy", "theft", evidence=1.0, threshold=3, base_days=20)
    w.run()
    assert w.verdict(ch) == "guilty"
    assert w.sentence_term(ch) == 5, f"the ceiling must hold: {w.sentence_term(ch)} != 5"


# ------------------------------------------------------ G-lower-bound-by-law
def test_sentence_is_floored_at_the_statutory_minimum():
    w = _court()
    w.add_sentence_law("theft", min_term=4, max_term=10)
    w.add_resident("Minor", coin=30.0, standing=0.0)
    # base_days 0 -> desired below the floor.
    ch = w.prosecute("Minor", "theft", evidence=1.0, threshold=3, base_days=0)
    w.run()
    assert w.verdict(ch) == "guilty"
    assert w.sentence_term(ch) == 4, f"a guilty verdict carries at least the minimum: {w.sentence_term(ch)} != 4"


# ------------------------------------------------------ G-within-range-tracks-the-council
def test_within_range_a_harsher_council_gives_a_longer_term():
    divided = _court(_BENCH)                 # 3/5 condemn
    divided.add_sentence_law("theft", min_term=1, max_term=10)
    divided.add_resident("D", coin=30.0, standing=0.0)
    cd = divided.prosecute("D", "theft", evidence=1.0, threshold=3, base_days=2)
    divided.run()

    united = _court(_ALL_HARSH)              # 5/5 condemn
    united.add_sentence_law("theft", min_term=1, max_term=10)
    united.add_resident("D", coin=30.0, standing=0.0)
    cu = united.prosecute("D", "theft", evidence=1.0, threshold=3, base_days=2)
    united.run()

    assert divided.verdict(cd) == "guilty" and united.verdict(cu) == "guilty"
    assert divided.sentence_term(cd) == 2, divided.sentence_term(cd)     # desired 2+(3-3)
    assert united.sentence_term(cu) == 4, united.sentence_term(cu)       # desired 2+(5-3)
    assert united.sentence_term(cu) > divided.sentence_term(cd), "a harsher council should sentence longer"


# ------------------------------------------------------ G-amending-the-law-moves-the-ceiling
def test_amending_the_law_lowers_the_ceiling():
    w = _court()
    w.add_sentence_law("theft", min_term=1, max_term=10)
    w.add_resident("First", coin=30.0, standing=0.0)
    c1 = w.prosecute("First", "theft", evidence=1.0, threshold=3, base_days=20)
    w.run()
    assert w.sentence_term(c1) == 10, "capped at the original ceiling"
    # the council lowers the maximum sentence for theft.
    w.amend_sentence_law("theft", max_term=3)
    w.add_resident("Second", coin=30.0, standing=0.0)
    c2 = w.prosecute("Second", "theft", evidence=1.0, threshold=3, base_days=20)
    w.run()
    assert w.sentence_term(c2) == 3, f"the new ceiling must bind: {w.sentence_term(c2)} != 3"


# ------------------------------------------------------ G-acquitted-not-sentenced (falsifier)
def test_acquitted_defendant_gets_no_term():
    w = _court()
    w.add_sentence_law("theft", min_term=1, max_term=10)
    w.add_resident("Esteemed", coin=30.0, standing=8.0)   # deference shields -> acquittal
    ch = w.prosecute("Esteemed", "theft", evidence=1.0, threshold=3, base_days=6)
    w.run()
    assert w.verdict(ch) == "acquitted"
    assert w.sentence_term(ch) == 0 and w.jail_roll() == []


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_sentence():
    src = open(os.path.join(_ROOT, "worlds", "bigville_sentence_world.py")).read()
    import ast
    lines = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Call, ast.Compare, ast.BinOp)):
            lines.add(getattr(node, "lineno", -1))
    code = "\n".join(src.splitlines()[i - 1] for i in sorted(lines) if i > 0).lower()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply",
                      "argmax", "min(", "max(", "sorted("):
        assert forbidden not in code, f"adapter must not decide/clamp the sentence: {forbidden!r}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_sentence.json")))
    assert {"sn_sentence"} <= {r["name"] for r in seed["rules"]}
    # the sentence is an Argmax whose option set is bounded by the law (IfThenElse on min/max).
    body = json.dumps(seed)
    assert "Argmax" in body and "IfThenElse" in body and "min_term" in body and "max_term" in body
