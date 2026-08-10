"""bigville R24 v2 (block 313000): the council sits as court, REWIRED onto the
generic decision-by-collapse. The verdict is the council's aggregated collapse:
each councillor forms its OWN conclusion about the charge (jc_conclude), and guilty
iff the condemning councillors reach the charge's threshold. Supersedes v1's
evidence>=bar threshold. Gates mirror BIGVILLE_COURT_PREREG.md (v2).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_court_world import BigvilleCourtWorld   # noqa: E402

# A disposition-spread bench: three punitive-leaning, two lenient. deference 0.5,
# so a high-standing defendant is shielded.
_BENCH = [
    ("H1", dict(bloc="rich", credence=1.5, punitiveness=1.5, deference=0.5)),
    ("H2", dict(bloc="rich", credence=1.5, punitiveness=1.0, deference=0.5)),
    ("H3", dict(bloc="poor", credence=1.2, punitiveness=0.8, deference=0.5)),
    ("L1", dict(bloc="poor", credence=0.5, punitiveness=-1.0, deference=0.5)),
    ("L2", dict(bloc="poor", credence=0.4, punitiveness=-1.5, deference=0.5)),
]


def _court(bench=_BENCH):
    w = BigvilleCourtWorld()
    for n, d in bench:
        w.add_councillor(n, **d)
    w.add_constable("Dogberry")
    return w


# ------------------------------------------------------ G-guilty-when-enough-condemn (headline)
def test_enough_condemning_councillors_convict_and_sentence():
    w = _court()
    w.add_resident("Lowly", coin=30.0, standing=0.0)     # a low-standing defendant
    ch = w.prosecute("Lowly", "stealing a goose", evidence=1.0, penalty=6.0,
                     standing_penalty=1.0, threshold=3)
    w.run()
    assert w.verdict(ch) == "guilty", f"a condemning majority should convict, got {w.verdict(ch)}"
    assert w.convict_votes(ch) >= 3, w.convict_votes(ch)
    assert abs(w.coin_of("Lowly") - 24.0) < 1e-9, "defendant fined"
    assert abs(w.standing_of("Lowly") - (-1.0)) < 1e-9, "defendant loses standing"
    assert abs(w.treasury_collected() - 6.0) < 1e-9, "the fine goes to the treasury"


# ------------------------------------------------------ G-acquit / identity-shields (headline)
def test_who_the_defendant_is_can_acquit_the_same_charge():
    """The SAME bench, the SAME evidence -- but a high-standing defendant is shielded
    by the councillors' deference; too few condemn; acquitted, untouched. Evidence is
    not decisive alone."""
    w = _court()
    w.add_resident("Esteemed", coin=30.0, standing=8.0)
    ch = w.prosecute("Esteemed", "stealing a goose", evidence=1.0, penalty=6.0, threshold=3)
    w.run()
    assert w.verdict(ch) == "acquitted", f"a well-regarded defendant should be acquitted, got {w.verdict(ch)}"
    assert abs(w.coin_of("Esteemed") - 30.0) < 1e-9, "an acquittal takes no coin"
    assert abs(w.standing_of("Esteemed") - 8.0) < 1e-9, "an acquittal costs no standing"
    assert abs(w.treasury_collected() - 0.0) < 1e-9


# ------------------------------------------------------ G-verdict-is-the-collapse
def test_councillors_diverge_the_verdict_is_their_aggregate():
    """The councillors reach different conclusions on ONE charge -- the verdict is
    their collective collapse, not a monotone function of the evidence."""
    w = _court()
    w.add_resident("Suspect", coin=30.0, standing=0.0)
    ch = w.prosecute("Suspect", "poaching", evidence=1.0, threshold=3)
    w.run()
    concls = w.councillor_conclusions(ch)
    assert len(concls) == len(_BENCH), f"every councillor concluded: {concls}"
    assert len(set(concls.values())) >= 2, f"councillors did not diverge: {concls}"


# ------------------------------------------------------ G-sentence-applies-once (falsifier)
def test_sentence_applies_exactly_once():
    w = _court()
    w.add_resident("Repeat", coin=30.0, standing=0.0)
    ch = w.prosecute("Repeat", "brawling", evidence=1.0, penalty=4.0, threshold=3)
    w.run()
    coin1, standing1, tre1 = w.coin_of("Repeat"), w.standing_of("Repeat"), w.treasury_collected()
    assert w.verdict(ch) == "guilty"
    for _ in range(3):
        w.run()
    assert abs(w.coin_of("Repeat") - coin1) < 1e-9, "fine double-applied"
    assert abs(w.standing_of("Repeat") - standing1) < 1e-9, "standing double-docked"
    assert abs(w.treasury_collected() - tre1) < 1e-9, "treasury double-credited"


# ------------------------------------------------------ G-same-council-both-jobs
def test_same_council_legislates_and_judges():
    w = _court()
    w.add_law("land_tax", 2.0)
    w.add_resident("Culprit", coin=30.0, standing=0.0)
    # legislate: the poor bloc (H3,L1,L2) carries a relief bill (threshold 3).
    bill = w.propose_bill("amend", target="land_tax", new_value=1.0,
                          aids_bloc="poor", threshold=3)
    w.run()
    assert w.bill_status(bill) == "enacted", "the council legislated"
    # judge: the same bench convicts a low-standing defendant by collapse.
    ch = w.prosecute("Culprit", "arson", evidence=1.0, penalty=5.0, threshold=3)
    w.run()
    assert w.verdict(ch) == "guilty", "the same council judged by collapse"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_verdict():
    src = open(os.path.join(_ROOT, "worlds", "bigville_court_world.py")).read()
    import ast
    code_lines = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Call, ast.Compare, ast.BinOp)):
            code_lines.add(getattr(node, "lineno", -1))
    code = "\n".join(src.splitlines()[i - 1] for i in sorted(code_lines) if i > 0).lower()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply",
                      "argmax", "max(", "sorted("):
        assert forbidden not in code, f"adapter must not decide the verdict: {forbidden!r}"
    court = json.load(open(os.path.join(_ROOT, "seeds", "bigville_court.json")))
    names = {r["name"] for r in court["rules"]}
    assert {"ct_hear", "ct_condemn", "ct_verdict_guilty", "ct_verdict_acquit", "ct_sentence"} <= names, names
    # the actual verdict is the collapse in agent_judgment, not a court threshold.
    judg = json.load(open(os.path.join(_ROOT, "seeds", "agent_judgment.json")))
    assert "Argmax" in json.dumps(judg), "the verdict must be an Argmax collapse (agent_judgment)"
    assert {"jc_conclude"} <= {r["name"] for r in judg["rules"]}
