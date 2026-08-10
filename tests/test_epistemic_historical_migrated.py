"""EPISTEMIC LAYER AGAINST HISTORICAL NEWS WHERE WE HAVE CONTEXT (2026-07-12).

The epistemic-gap layer (deception vs introspection-gap humility architecture)
auto-produces its structural EVIDENCE on a plain read_and_comprehend (the
coordination proxy from the temporal conflict the reads already build), and the
VERDICT is the context-dependent `assess_epistemic_lean` COMBINE. "Context" is
the actor's class/environment the reader is TOLD (annotate_actor_class /
internal-knowledge trace) -- the user's thesis: a better model of the actor's
environment than the actor's self-model makes a reasonable confidence interval
almost trivial, while CERTAINTY stays out of reach.

These gates use real documented cases (the fossil-fuel industry funding then
opposing the very technology/science -- the "Exxon Knew" pattern; the tobacco
industry funding prevention while its own documents showed it knew) and show the
verdict ESCALATING with the context available, always as a REVISABLE interval,
never certain:

    no context (structural signal only)  -> UNDETERMINED
    + institutional class prior          -> weak_deception   (the money/power prior)
    + documentary internal acknowledgment-> strong_deception (they KNEW)

and the humility floor: a plain read with no context stays UNDETERMINED, and
`residual_other_mass` (the "could be the other mechanism" mass) is > 0 ALWAYS.

The classify-by-join evidence rule is AGENT-AUTHORED (never seeded); the codebook
(EpistemicSignal / ForcedChoiceExpectation / ClassBaseline) self-loads.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_epistemic_historical_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import comprehension_reader as cr        # noqa: E402
from domains import actor_goals as ag                 # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


# A documented fossil-fuel pattern: the same actor funds the technology, then
# opposes it (support-then-undermine across actions -> a temporal conflict).
OIL = ("The technology was funded by the oil company. "
       "The technology was opposed by the oil company.")

# Tobacco: same support-then-undermine structure.
TOBACCO = ("The programme was funded by the tobacco company. "
           "The programme was opposed by the tobacco company.")


def _assess(article, *, actor=None, actor_class=None, internal_ack=False):
    s, node = boot_core()
    ad = _Agent(s, node)
    cr.read_and_comprehend(ad, article)
    if actor_class:
        ag.annotate_actor_class(ad, actor, actor_class)
    if internal_ack:
        ag.annotate_internal_knowledge_trace(ad, acknowledged=True)
    readings = ag.assess_epistemic_lean(ad)
    return readings[0] if readings else None


def _never_certain(r):
    assert r["verdict"] != "certain", r
    assert r["residual_other_mass"] > 0.0, r
    assert r["revisable"] == 1.0, r
    lo, hi = r["interval"]
    assert hi > lo, r["interval"]


# --------------------------------------------------------------------------- #
#  1. EVIDENCE auto-produces on the read (no manual injection).
# --------------------------------------------------------------------------- #
def test_read_auto_produces_the_coordination_proxy(agent):
    cr.read_and_comprehend(agent, OIL)
    ev = {e.get("signal_name") for e in ag.held_epistemic_evidence(agent)}
    assert "coordination_requires_dual_goal" in ev, ev


# --------------------------------------------------------------------------- #
#  2. HUMILITY FLOOR — no context -> UNDETERMINED (structural signal alone does
#     not conclude deception), never certain.
# --------------------------------------------------------------------------- #
def test_no_context_stays_undetermined(agent):
    r = _assess(OIL)
    assert r is not None
    assert r["verdict"] == "undetermined", r
    _never_certain(r)


# --------------------------------------------------------------------------- #
#  3. CONTEXT ESCALATES the verdict — institutional class prior, then documentary
#     acknowledgment — each a wider commitment, never to certainty.
# --------------------------------------------------------------------------- #
def test_class_prior_moves_to_weak_deception():
    r = _assess(OIL, actor="oil_company", actor_class="corporation")
    assert r["verdict"] == "weak_deception", r
    _never_certain(r)


def test_documentary_internal_ack_reaches_strong_deception():
    # "they KNEW" -- the documentary internal-knowledge trace is the near-decisive
    # cue; still a revisable interval, residual_other_mass > 0 (never certain).
    r = _assess(OIL, actor="oil_company", actor_class="corporation", internal_ack=True)
    assert r["verdict"] == "strong_deception", r
    _never_certain(r)


def test_context_monotonically_widens_commitment():
    # the interval's lower bound (the committed lean) rises as context accrues.
    lo0 = _assess(OIL)["interval"][0]
    lo1 = _assess(OIL, actor="oil_company", actor_class="corporation")["interval"][0]
    lo2 = _assess(OIL, actor="oil_company", actor_class="corporation", internal_ack=True)["interval"][0]
    assert lo0 < lo1 < lo2, (lo0, lo1, lo2)


# --------------------------------------------------------------------------- #
#  4. GENERALISES beyond oil — the same structure + corporate prior on a
#     different sector (tobacco) leans deception too.
# --------------------------------------------------------------------------- #
def test_generalises_to_tobacco():
    r = _assess(TOBACCO, actor="tobacco_company", actor_class="corporation")
    assert r["verdict"] == "weak_deception", r
    _never_certain(r)


# --------------------------------------------------------------------------- #
#  5. THE HUMILITY CONTRAST — the SAME structural situation (opposing a
#     technology one is structurally forced against) routes to OPPOSITE verdicts
#     by the actor's capacity to introspect. The forced-choice path fires from
#     natural text when the object carries a head noun after its premodifier
#     ("renewable energy PROJECT" -> object 'renewable_energy'; a bare
#     "renewable energy" under-extracts to 'renewable' -- a documented object-
#     domain phrasing sensitivity, not a blocker).
# --------------------------------------------------------------------------- #
def _forced_verdict(article):
    s, node = boot_core()
    ad = _Agent(s, node)
    cr.read_and_comprehend(ad, article)
    ag.ensure_epistemic_defaults(ad)        # the ForcedChoiceExpectation codebook
    ag.annotate_forced_choice_probes(ad)
    readings = ag.assess_epistemic_lean(ad)
    return readings[0] if readings else None


def test_institution_that_knows_leans_deception():
    # oil company (actor_can_introspect=1.0) opposing what it is forced against
    # -> the deception route, structural_forcing basis.
    r = _forced_verdict("The renewable energy project was opposed by the oil company.")
    assert r is not None and "structural_forcing" in (r.get("basis") or []), r
    assert r["verdict"].endswith("deception"), r
    assert r["interval"][0] > 0, r           # leans deception (positive)
    _never_certain(r)


def test_individual_who_cannot_introspect_leans_opacity_not_deception():
    # factory worker (actor_can_introspect=0.0) -- the SAME structural divergence,
    # but routed to OPACITY (introspection-gap / sincere), NEVER deception: no bad
    # faith is imputed to someone who cannot see their own forced choice.
    r = _forced_verdict("The automation support programme was opposed by the factory worker.")
    assert r is not None and "structural_forcing" in (r.get("basis") or []), r
    assert "opacity" in r["verdict"], r
    assert "deception" not in r["verdict"], r
    assert r["interval"][1] < 0, r           # leans opacity (negative)
    _never_certain(r)
