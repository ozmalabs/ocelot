"""bigville R25 (block 312000): generic decision-by-collapse. Any agent forms its
own conclusion about a matter by an Argmax collapse over stances, valued by a Term
that reads the agent's OWN held dispositions; different agents diverge on the same
matter; condemning agents act. Gates mirror BIGVILLE_JUDGMENT_PREREG.md. Every
verdict/action is a seed rule (jc_conclude / jc_act).
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_judgment_world import BigvilleJudgmentWorld   # noqa: E402

# A disposition-spread population: harsh->lenient, varying credence + deference.
_POP = [
    ("Harsh",    dict(credence=2.0, punitiveness=1.5, deference=0.0, sanction=0.5)),
    ("Fair",     dict(credence=1.0, punitiveness=0.0, deference=0.2, sanction=0.5)),
    ("Skeptic",  dict(credence=0.6, punitiveness=-0.4, deference=0.3, sanction=0.5)),
    ("Lenient",  dict(credence=0.5, punitiveness=-1.0, deference=0.5, sanction=0.5)),
    ("Loyalist", dict(credence=0.3, punitiveness=-1.5, deference=0.8, sanction=0.5)),
]


def _town(pop=_POP, subject_standing=3.0):
    w = BigvilleJudgmentWorld()
    w.add_subject("Accused", standing=subject_standing)
    for name, d in pop:
        w.add_agent(name, **d)
    return w


# ------------------------------------------------------ G-divergent-conclusions (headline)
def test_agents_diverge_on_one_matter():
    w = _town()
    m = w.raise_matter("stole the harvest", weight=1.0, subject="Accused")
    w.consider_all(m)
    w.run()
    verdicts = w.verdicts()
    assert sum(verdicts.values()) == len(_POP), "every agent concluded once"
    assert len(verdicts) >= 2, f"agents did not diverge on one matter: {verdicts}"


# ------------------------------------------------------ G-evidence-is-one-input (headline)
def test_evidence_is_not_decisive_alone():
    """At HIGH evidence weight, a harsh agent condemns but a lenient/deferential
    agent still exonerates the SAME matter -- evidence is one input, not the gate."""
    w = _town(subject_standing=4.0)
    m = w.raise_matter("burned the mill", weight=1.0, subject="Accused")
    w.consider_all(m)
    w.run()
    harsh_v, _ = w.conclusion_of("Harsh")
    loyal_v, _ = w.conclusion_of("Loyalist")
    assert harsh_v in ("denounce", "condemn"), f"harsh agent should condemn strong evidence: {harsh_v}"
    assert loyal_v in ("doubt", "exonerate"), f"loyal agent should not convict on the same evidence: {loyal_v}"


# ------------------------------------------------------ G-subject-identity-matters
def test_who_the_subject_is_changes_the_verdicts():
    """The same population at the same evidence condemns a low-standing subject more
    than a high-standing one -- the deference channel is real."""
    low = _town(subject_standing=0.0)
    m1 = low.raise_matter("cheated at market", weight=1.0, subject="Accused")
    low.consider_all(m1); low.run()
    high = _town(subject_standing=6.0)
    m2 = high.raise_matter("cheated at market", weight=1.0, subject="Accused")
    high.consider_all(m2); high.run()
    assert low.condemn_count() > high.condemn_count(), \
        f"standing did not shield the subject: low={low.condemn_count()} high={high.condemn_count()}"


# ------------------------------------------------------ G-collapse-is-graded
def test_the_collapse_is_graded_not_binary():
    """Across the population the verdicts span more than two poles -- a genuine
    multi-candidate collapse, not a sign test between two options."""
    w = _town()
    m = w.raise_matter("poached the king's deer", weight=1.0, subject="Accused")
    w.consider_all(m); w.run()
    labels = set(w.verdicts())
    assert len(labels) >= 3, f"collapse degenerated to <=2 verdicts: {w.verdicts()}"
    # and at least one condemning AND one exonerating verdict both occur.
    assert labels & {"denounce", "condemn"} and labels & {"doubt", "exonerate"}, w.verdicts()


# ------------------------------------------------------ G-citizenry-acts
def test_condemning_agents_strip_standing_once():
    w = _town(subject_standing=5.0)
    m = w.raise_matter("spread sedition", weight=1.0, subject="Accused")
    w.consider_all(m); w.run()
    n_condemn = w.condemn_count()
    assert n_condemn > 0, "test needs at least one condemning agent"
    s0 = w.standing_of("Accused")
    w.enact()
    s1 = w.standing_of("Accused")
    # each condemning agent stripped its own sanction (0.5 here).
    assert abs((s0 - s1) - 0.5 * n_condemn) < 1e-9, \
        f"standing drop {s0-s1} != condemners*sanction {0.5*n_condemn}"
    # a second enact does not double-strip (the acted guard).
    w.enact()
    assert abs(w.standing_of("Accused") - s1) < 1e-9, "sanction applied more than once"


# ------------------------------------------------------ G-dispositions-load-bearing (falsifier)
def test_identical_dispositions_collapse_to_unanimity():
    """Give every agent IDENTICAL dispositions -> the verdict is unanimous. Proves
    divergence comes from the agents' held params, not from noise in the collapse."""
    clones = [(f"C{i}", dict(credence=1.0, punitiveness=0.0, deference=0.2, sanction=0.5))
              for i in range(5)]
    w = _town(pop=clones)
    m = w.raise_matter("stole the harvest", weight=1.0, subject="Accused")
    w.consider_all(m); w.run()
    assert len(w.verdicts()) == 1, f"identical agents should agree, got {w.verdicts()}"


# ------------------------------------------------------ G-no-python-decision (source audit)
def test_no_python_decides_the_conclusion():
    src = open(os.path.join(_ROOT, "worlds", "bigville_judgment_world.py")).read()
    # strip docstrings/comments so prose describing the mechanism isn't flagged.
    import ast
    tree = ast.parse(src)
    code_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Call, ast.Compare, ast.BinOp)):
            code_lines.add(getattr(node, "lineno", -1))
    code = "\n".join(src.splitlines()[i - 1] for i in sorted(code_lines) if i > 0)
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "_match", "_apply",
                      "argmax", "max(", "sorted("):
        # the adapter must not run a rule engine nor compute a selection in Python.
        assert forbidden not in code.lower(), f"adapter must not decide the verdict: {forbidden!r}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "agent_judgment.json")))
    names = {r["name"] for r in seed["rules"]}
    assert {"jc_conclude", "jc_act"} <= names, names
    # the collapse must be an Argmax in the SEED, not in Python.
    assert "Argmax" in json.dumps(seed), "the decision must be an Argmax collapse in the seed"
