"""GAMMA_COLLAPSE_ALGORITHM spike: Type-1 Gamma rejection residual capture +
recurrence-gated proposal, end to end through the REAL agent boot path and the
REAL human-gated promotion pipeline.

See docs/research/engine_substrate/GAMMA_COLLAPSE_ALGORITHM_PREREG.md and
_RESULTS.md for the full design and findings. This file is the "the slice"
regression gate named in the PREREG's own house-discipline section: recurrence
-> mint -> promote -> manual adopt -> check_edge before/after, on a live
`WorldAdapter` (not just the raw `substrate_rs` object used during the spike's
own exploratory scripting).

Safety invariant checked explicitly throughout: no rule ever calls
`add_production`; the "adopt" step in every test here is an explicit, manual,
out-of-band call standing in for a human/experiment decision, never something
a rule triggers.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from substrate_rs import NodeID as _NodeID

jd = pytest.importorskip("jabberwock_daemon")


@pytest.fixture()
def agent():
    # A fresh, isolated agent per test (unlike the module-scoped fixture in
    # test_self_concern_promote_migrated.py) -- this spike mutates a global,
    # process-wide flag on the Rust substrate (gamma_residual_capture) and
    # wants a clean GammaResidual population per test, not one shared across
    # a whole module's test order.
    a = WorldAdapter(seeds=())
    load_all_seeds(a)  # sweeps every seeds/*.json, including gamma_residual.json
    return a


def _self_concerns(agent, kind=None):
    out = []
    for n in agent.s.nodes("SelfConcern"):
        attrs = agent.s.node(n)["attrs"]
        if kind is None or attrs.get("kind") == kind:
            out.append((n, attrs))
    return out


def _register_vocab_for_clean_type1(agent, edge_type):
    """Register GammaSpikeFoo, GammaSpikeBar, and `edge_type` in the live
    grammar's vocabulary WITHOUT admitting GammaSpikeFoo -[edge_type]->
    GammaSpikeBar -- the setup for a genuine Type-1 rejection (vocab
    present, no admitting production), never a Type-2 (vocab absent).
    `check_edge`'s vocab check (`checker.rs:68-76`) is GLOBAL across every
    production's node/edge-type vocabulary, not scoped per triple, so a
    decoy production using `edge_type` on an unrelated (Bar, Bar) pair is
    enough to register it without admitting the tested triple."""
    agent.s.add_production({"src": {"type": "GammaSpikeFoo", "var": "x"},
                             "edge_type": "gs_unrelated",
                             "tgt": {"type": "GammaSpikeFoo", "var": "y"}})
    agent.s.add_production({"src": {"type": "GammaSpikeBar", "var": "x"},
                             "edge_type": edge_type,
                             "tgt": {"type": "GammaSpikeBar", "var": "y"}})


def test_capture_off_by_default_mints_nothing(agent):
    """Default path (capture flag untouched): a real agent boot does not
    spontaneously start writing GammaResidual nodes for every mundane Type-1
    rejection that already happens during normal operation (there are many --
    e.g. malformed edges the conversation pipeline tries and discards)."""
    before = len(list(agent.s.nodes("GammaResidual")))
    agent.converse("This is an ordinary sentence with nothing pathological in it.",
                    speech_act="statement")
    agent.comprehend()
    after = len(list(agent.s.nodes("GammaResidual")))
    assert after == before, "capture must stay off unless explicitly enabled"


def test_single_rejection_does_not_mint(agent):
    agent.s._inner.set_gamma_residual_capture(True)
    a_node = agent.s.add_node("GammaSpikeFoo", {})
    b_node = agent.s.add_node("GammaSpikeBar", {})
    _register_vocab_for_clean_type1(agent, "gs_lonely_edge")
    with pytest.raises(Exception):
        agent.s.add_edge(a_node, "gs_lonely_edge", b_node)
    agent.s.tick()
    concerns = _self_concerns(agent, kind="gamma_production")
    assert not concerns, "support 1 must not mint -- TWO is the smallest cardinality 'recurs' is defined at"


def test_recurrence_mints_exactly_one_self_concern(agent):
    agent.s._inner.set_gamma_residual_capture(True)
    a_node = agent.s.add_node("GammaSpikeFoo", {})
    targets = [agent.s.add_node("GammaSpikeBar", {}) for _ in range(4)]
    _register_vocab_for_clean_type1(agent, "gs_recurring_edge")
    for t in targets:
        with pytest.raises(Exception):
            agent.s.add_edge(a_node, "gs_recurring_edge", t)
        agent.s.tick()

    concerns = _self_concerns(agent, kind="gamma_production")
    matching = [(n, a) for n, a in concerns
                if "GammaSpikeFoo" in a["content"] and "gs_recurring_edge" in a["content"]
                and "GammaSpikeBar" in a["content"]]
    assert len(matching) == 1, (
        "recurrence (support >= 2) must mint EXACTLY ONE SelfConcern, "
        f"regardless of how many further times the SAME triple is rejected; got {matching}"
    )
    _, attrs = matching[0]
    assert attrs["source"] == "implicit"
    assert attrs["status"] == "noted"


def test_promote_self_concern_accepts_the_minted_gap_with_zero_code_changes(agent):
    """Q2's GO bar: `promote_self_concern` (the real, standing, human-gated
    pipeline entry point) accepts a `kind:'gamma_production'` SelfConcern
    exactly like it accepts a gap_awareness-minted one -- no code change to
    that function was needed to make this work."""
    agent.s._inner.set_gamma_residual_capture(True)
    a_node = agent.s.add_node("GammaSpikeFoo", {})
    b1 = agent.s.add_node("GammaSpikeBar", {})
    b2 = agent.s.add_node("GammaSpikeBar", {})
    _register_vocab_for_clean_type1(agent, "gs_promote_edge")
    for t in (b1, b2):
        with pytest.raises(Exception):
            agent.s.add_edge(a_node, "gs_promote_edge", t)
        agent.s.tick()

    concerns = _self_concerns(agent, kind="gamma_production")
    target = next((n, a) for n, a in concerns if "gs_promote_edge" in a["content"])
    node_id, attrs = target
    # `promote_self_concern` parses `id_str` via `int(id_str)` -- a raw
    # `NodeID` from `agent.s.nodes(...)` needs its `.value` int, the same
    # helper (`_nid_value`) `jabberwock_daemon.py` itself uses internally.
    id_str = str(node_id.value if hasattr(node_id, "value") else node_id)

    res = jd.promote_self_concern(agent, id_str)
    assert res["ok"], f"promote_self_concern must accept a gamma_production concern: {res}"
    # `promote_self_concern` returns a plain int (`_nid_value`); `agent.s.node`
    # wants a `NodeID` object back.
    standing_id = _NodeID(res["standing_concern"])
    standing = agent.s.node(standing_id)["attrs"]
    assert standing["status"] == "pending"
    assert standing["source"] == "conversation_promoted"
    # Honest, named residual (see RESULTS.md Q2): no gamma_production-specific
    # StandingConcern handler exists (unlike code_write/prog_read), so this
    # falls through to the generic comprehend_first pipeline. That is
    # EXPECTED, not a bug -- asserted here so a future handler addition is a
    # deliberate change to this assertion, not a silent behaviour change.
    assert standing["pipeline"] == "comprehend_first"


def test_manual_adopt_flips_check_edge_and_theorem_xii_holds(agent):
    """The live before/after demonstration, at the WorldAdapter grain. The
    adopt step is an explicit, out-of-band call -- never something a rule
    triggers -- so Theorem XII (reference-monitor containment) holds
    identically before and after: nothing becomes admissible except through
    this manual call, and everything that was inadmissible stays inadmissible
    until it is made."""
    agent.s._inner.set_gamma_residual_capture(True)
    a_node = agent.s.add_node("GammaSpikeFoo", {})
    b_node = agent.s.add_node("GammaSpikeBar", {})
    _register_vocab_for_clean_type1(agent, "gs_adopt_edge")

    assert agent.s.is_edge_admissible(a_node, "gs_adopt_edge", "GammaSpikeBar", None) is False
    with pytest.raises(Exception):
        agent.s.add_edge(a_node, "gs_adopt_edge", b_node)
    assert agent.s.is_edge_admissible(a_node, "gs_adopt_edge", "GammaSpikeBar", None) is False, (
        "a single rejection must NOT change admissibility -- no rule, no side effect, does this")

    # The MANUAL, human/experiment-equivalent adopt step.
    agent.s.add_production({
        "src": {"type": "GammaSpikeFoo", "var": "x"},
        "edge_type": "gs_adopt_edge",
        "tgt": {"type": "GammaSpikeBar", "var": "y"},
        "provenance": "gamma_collapse_spike:test_manual_adopt",
    })

    assert agent.s.is_edge_admissible(a_node, "gs_adopt_edge", "GammaSpikeBar", None) is True
    agent.s.add_edge(a_node, "gs_adopt_edge", b_node)  # must not raise now

    # An UNRELATED triple that was never adopted must still be rejected --
    # adoption is scoped to the exact triple, not a blanket relaxation.
    c_node = agent.s.add_node("GammaSpikeBar", {})
    assert agent.s.is_edge_admissible(b_node, "gs_adopt_edge", "GammaSpikeFoo", None) is False
