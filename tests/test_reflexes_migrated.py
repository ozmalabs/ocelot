"""Reflexes, migrated — run in the WorldAdapter (no CuriousAgent).
Covers tests/test_reflexes.

A reflex is stimulus -> response, graph-resident: its WHEN is a Term-tree on a
Reflex node, editable as graph data, never a Python branch. Under the burn
discipline that maps onto the adapter exactly as the master thread does:

  • A REFLEX is a first-class ``Reflex`` node hung off the agent by a
    ``has_reflex`` edge, carrying a stimulus TERM the SUBSTRATE evaluates over
    the agent node (a ``stimulus_term`` edge to the Term subgraph). The firing
    DECISION is that Term — the adapter never reads the metric in Python.
  • The RESPONSE is a registered callable keyed by name — the genuine I/O
    boundary, a side effect that lives outside the graph.
  • THE CLOCK is mechanical bookkeeping: ``master_tick`` advances it and
    surfaces it as the agent's ``tick`` attr so a stimulus Term can read it.
    The tests set the clock the same mechanical way (master tick + ``tick``
    attr) to trip a stimulus on a chosen tick.

The agent can install ANY predicate it likes for ANY registered response, and
can REPLACE a reflex's stimulus in place (same node, new Term) — that is what
makes it graph-native rather than Python.

The original ``test_reflexes`` also exercised CuriousAgent-only machinery that
has no analogue on the seed-booted adapter — a pre-seeded ``surprise_investigate``
reflex, the 7-rule surprise->investigation cascade (``rule_17b2`` Subroutine),
the ``insight_layer_1`` insight layer, and the ``resolve_impasse`` registry
entry. Those are agent-internal reasoning faculties (graph data / Rules the
CuriousAgent boots), not reflex-machinery contracts, and the WorldAdapter does
not boot them. The migratable contract those tests stood on — a response is an
arbitrary side-effect dispatch run through the substrate's stimulus evaluation,
and Reflex nodes persist while response callables are re-registered — is covered
below against the adapter's own surface.
"""
from __future__ import annotations

import substrate_rs as srs
from substrate.dsl import Attr, Eq, Gt, Lit, Var
from substrate.jsonio import term_to_json
from substrate.world_adapter import WorldAdapter

_REFLEX_TYPE = "Reflex"


def _set_clock(a: WorldAdapter, tick: int) -> None:
    """Advance the master clock to ``tick`` the mechanical way: the master-state
    counter plus the agent ``tick`` attr a stimulus Term reads (this is what
    ``master_tick`` does, here driven to an exact value)."""
    a._master["tick"] = tick
    a.inner.set_attr(a.agent, "tick", tick)


# --- a reflex lives in the graph -------------------------------------------

def test_installed_reflex_lives_in_the_graph():
    # the WorldAdapter ships NO reflexes (cleaner than the CuriousAgent, which
    # seeds system reflexes); an installed one IS graph-resident.
    a = WorldAdapter()
    assert a.reflexes() == []
    nid = a.install_reflex("note",
                           term_to_json(Gt(Attr(Var("agent"), "tick"), Lit(0))),
                           response="note_it")
    assert nid is not None
    # it IS a Reflex node, reachable from the agent via has_reflex
    assert a.s.node(nid)["type"] == _REFLEX_TYPE
    has_reflex_targets = set(a.inner.neighbours(a.agent, "has_reflex"))
    assert nid in has_reflex_targets
    # the WHEN is graph data — a Term-tree on a single stimulus_term edge
    stim = a.inner.neighbours(nid, "stimulus_term")
    assert len(stim) == 1
    assert a.reflex("note") == nid


def test_reflex_fires_when_arbitrary_stimulus_is_satisfied():
    a = WorldAdapter()
    log = []
    a.register_reflex_response("note_it",
                               lambda ad: log.append(ad.activity_tick))
    # arbitrary stimulus — tick attr > 0 on the agent node
    a.install_reflex("note", term_to_json(Gt(Attr(Var("agent"), "tick"), Lit(0))),
                     response="note_it")
    _set_clock(a, 1)
    fired = a.fire_reflexes()
    assert "note" in fired
    assert log == [1]


def test_reflex_does_not_fire_when_stimulus_false():
    a = WorldAdapter()
    log = []
    a.register_reflex_response("note_it", lambda _: log.append("fired"))
    # stimulus that never trips
    a.install_reflex("never", term_to_json(Lit(False)), response="note_it")
    _set_clock(a, 5)
    # the adapter installs no system reflexes, so nothing fires at all
    assert a.fire_reflexes() == []
    assert "never" not in a.fire_reflexes()
    assert log == []


def test_refractory_debounces_consecutive_fires():
    a = WorldAdapter()
    log = []
    a.register_reflex_response("count", lambda _: log.append("x"))
    a.install_reflex("always", term_to_json(Lit(True)), response="count",
                     refractory_ticks=10)
    _set_clock(a, 100)
    a.fire_reflexes()              # fires
    _set_clock(a, 105)            # still inside refractory
    a.fire_reflexes()              # skipped
    _set_clock(a, 111)            # past refractory
    a.fire_reflexes()              # fires again
    assert log == ["x", "x"]


def test_reflex_stimulus_reads_agent_attrs_and_runs_response():
    # the load-bearing contract behind the old insight-layer test: the stimulus
    # is a Term over agent attrs (here tick == 3, an arbitrary condition) and a
    # registered response runs a real side effect when it trips — no exception,
    # no Python branch over the metric.
    a = WorldAdapter()
    ran = []
    a.register_reflex_response("on_three", lambda ad: ran.append(ad.activity_tick))
    a.install_reflex("tri",
                     term_to_json(Eq(Attr(Var("agent"), "tick"), Lit(3))),
                     response="on_three")
    _set_clock(a, 2)
    assert "tri" not in a.fire_reflexes()   # 2 != 3, stimulus false
    _set_clock(a, 3)
    assert "tri" in a.fire_reflexes()        # 3 == 3, stimulus true
    assert ran == [3]


def test_agent_can_rewrite_a_reflex_stimulus():
    # what makes this graph-native: the agent can REPLACE the predicate in place
    a = WorldAdapter()
    rid = a.install_reflex("surprise", term_to_json(Lit(True)),
                           response="investigate")
    assert rid is not None
    # install a different stimulus on the same name — same node, new term
    again = a.install_reflex("surprise", term_to_json(Lit(False)),
                             response="investigate", refractory_ticks=20)
    # node identity preserved
    assert again == rid
    assert a.reflex("surprise") == rid
    assert len(a.reflexes()) == 1
    # the old stimulus_term edge replaced — there is still exactly one
    stims = a.inner.neighbours(rid, "stimulus_term")
    assert len(stims) == 1
    # the new policy took: refractory + response were rewritten on the node
    attrs = a.s.node(rid)["attrs"]
    assert attrs["response"] == "investigate"
    assert attrs["refractory_ticks"] == 20


def test_response_is_an_arbitrary_side_effect_dispatch():
    # the migratable kernel of the surprise->investigation end-to-end test: a
    # reflex's response is the I/O boundary — an arbitrary registered side
    # effect dispatched the moment the substrate-evaluated stimulus trips. Here
    # the side effect mints a node (standing in for the cascade's output);
    # the gating remains the Term, never Python.
    a = WorldAdapter()

    def dispatch(ad):
        ad.s.add_node("InvestigationStarted", {"at_tick": ad.activity_tick})

    a.register_reflex_response("noop_dispatched", dispatch)
    a.install_reflex("surprise_investigate", term_to_json(Lit(True)),
                     response="noop_dispatched", refractory_ticks=0)

    def n_built():
        return sum(1 for n in a.s.nodes()
                   if a.s.node(n)["type"] == "InvestigationStarted")

    before = n_built()
    _set_clock(a, 1000)
    a.fire_reflexes()
    assert n_built() == before + 1


def test_reflex_fires_through_the_master_tick():
    # end-to-end through the orchestrator: master_tick advances the clock,
    # surfaces it as the agent tick attr, and fires reflexes whose substrate
    # stimulus has tripped — exactly the path the master thread drives.
    a = WorldAdapter()
    fires = []
    a.register_reflex_response("rec", lambda ad: fires.append(ad.activity_tick))
    # stimulus: agent.tick > 2 (false on 1,2; true from 3)
    a.install_reflex("after_two",
                     term_to_json(Gt(Attr(Var("agent"), "tick"), Lit(2))),
                     response="rec")
    for _ in range(4):
        a.master_tick()
    assert fires == [3, 4]
    rid = a.reflex("after_two")
    assert a.s.node(rid)["attrs"]["fire_count"] == 2


def test_reflex_survives_persistence_round_trip():
    # Reflex nodes persist in the stored graph; the name index + response
    # registry are rebuilt on load (the response CALLABLE is not serialisable —
    # the agent re-registers it next run — but the reflex NODE is graph data).
    a = WorldAdapter()
    a.register_reflex_response("note_it", lambda _: None)
    a.install_reflex("noted",
                     term_to_json(Gt(Attr(Var("agent"), "tick"), Lit(0))),
                     response="note_it", refractory_ticks=4)

    # serialise the whole substrate (graph_to_dict) and reload into a fresh one.
    dumped = a.s.graph_to_dict()
    s2 = srs.Substrate()
    s2.graph_from_dict(dumped)

    # the reflex node came back, carrying its policy + a stimulus_term subgraph
    reflexes = [n for n in s2.nodes() if s2.node(n)["type"] == _REFLEX_TYPE]
    assert len(reflexes) == 1
    rid = reflexes[0]
    ra = s2.node(rid)["attrs"]
    assert ra["name"] == "noted"
    assert ra["response"] == "note_it"
    assert ra["refractory_ticks"] == 4
    # its stimulus Term survived and still evaluates over the reloaded graph
    stim = s2._inner.neighbours(rid, "stimulus_term")
    assert len(stim) == 1
    # re-index by name the way a reload would (name -> node id), then confirm
    # the persisted stimulus is live: set the reloaded agent's tick and eval it.
    by_name = {s2.node(n)["attrs"]["name"]: n for n in reflexes}
    assert by_name["noted"] == rid
    agent2 = [n for n in s2.nodes() if s2.node(n)["type"] == "Agent"][0]
    s2._inner.set_attr(agent2, "tick", 7)
    eval_stim = {"type": "EvalSubgraph", "node": {"type": "Pick", "source": {
        "type": "Neighbours", "node": {"type": "Var", "name": "n"},
        "edge_type": "stimulus_term"}}}
    assert bool(s2._inner.evaluate(eval_stim, {"n": rid, "agent": agent2}))
