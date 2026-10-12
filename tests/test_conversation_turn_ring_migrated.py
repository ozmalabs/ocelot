"""The conversation turn ring: the reading aperture applied to dialogue.

Pinned on the production conversation profile:
  * the ring capacity N comes from the SAME held reading_derive_trace_capacity
    Program, over the conversational ApertureBudget row's turn_capacity_*
    attrs, and widens once;
  * the attended set (`agent received m`) stays bounded while archived turns
    (`agent remembers m`) keep their attrs and edges;
  * a turn is never evicted before it is folded into its shapes (no
    turn_salience -> never evicted);
  * the unanswered recurrence is read from a TurnShape and its oldest member,
    and still files exactly one concern per class.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "evaluation", "substrate_capability")):
    if p not in sys.path:
        sys.path.insert(0, p)

import endemic_rsi_daemon_v1 as E               # noqa: E402
from domains import conversation_aperture as ca  # noqa: E402
from domains import reading_norms as rn          # noqa: E402

TURNS = ["That would be fun!", "The sky is blue.", "That sounds great!", "I like to watch movies.",
         "I love The Walking Dead.", "Me too!", "Great! I'll call you later.", "I agree.",
         "It's a battle royale game.", "I loved Frozen 2!", "Sure, that sounds like fun.",
         "I like to ride my bike.", "I know what you mean.", "Those sound like fun things to do."]


@pytest.fixture(scope="module")
def st():
    s = E.boot(True, promote=False)
    E.say(s, "Hello.")
    for t in TURNS:
        E.say(s, t)
    return s


def _inbound(a, edge):
    return [m for m in a.inner.neighbours(a.agent, edge) if a.s.node(m)["attrs"].get("from") == "interlocutor"]


def test_capacity_is_the_reading_program_over_the_turn_budget(st):
    a = st.adapter
    assert rn.effective_turn_capacity(a, "conversational", widened=False) == 8
    assert rn.effective_turn_capacity(a, "conversational", widened=True) == 12


def test_attended_set_is_bounded_and_archive_keeps_the_turn(st):
    a = st.adapter
    attended, archived = _inbound(a, "received"), _inbound(a, "remembers")
    eligible = [m for m in attended if a.s.node(m)["attrs"].get("turn_salience") is not None]
    ring = next(iter(a.inner.neighbours(a.agent, "has_turn_ring")))
    widened = a.s.node(ring)["attrs"].get("capacity_widened") == 1.0
    assert len(eligible) <= rn.effective_turn_capacity(a, "conversational", widened=widened)
    assert archived, "a 15-turn session must have evicted some turns"
    for m in archived:
        at = a.s.node(m)["attrs"]
        assert at.get("turn_evicted") == 1.0 and at.get("text") and at.get("turn_outcome")
        assert not a.inner.has_edge(a.agent, "received", m)
        assert at.get("turn_salience") is not None, "only shape-folded turns are evicted"


def test_unanswered_shape_files_one_concern_per_class(st):
    a = st.adapter
    shapes = [sh for sh in a.s.nodes("TurnShape") if a.s.node(sh)["attrs"].get("shape_kind") == "unanswered"]
    assert shapes
    for sh in shapes:
        members = list(a.inner.neighbours(sh, "has_member"))
        firsts = list(a.inner.neighbours(sh, "first_member"))
        assert len(firsts) == 1 and firsts[0] == min(members, key=lambda n: int(n.value))
    concerns = [n for n in a.s.nodes("SelfConcern") if a.s.node(n)["attrs"].get("kind") == "unanswered"]
    sigs = [tuple(a.s.node(n)["attrs"].get(k) for k in sorted(a.s.node(n)["attrs"]) if k.startswith("sig_"))
            for n in concerns]
    assert concerns and len(sigs) == len(set(sigs)), "one concern per class"
    recurring = [sh for sh in shapes if len(list(a.inner.neighbours(sh, "has_member"))) >= 2]
    assert len(concerns) == len(recurring)


def test_enforce_is_a_noop_when_disabled(st):
    a = st.adapter
    pol = next(iter(a.inner.neighbours(a.agent, "has_turn_ring_policy")))
    a.s.set_attr(pol, "enabled", 0)
    try:
        assert ca.enforce_turn_buffer(a, capacity=0) == []
    finally:
        a.s.set_attr(pol, "enabled", 1)
