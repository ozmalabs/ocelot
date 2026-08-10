"""THE TRACE WAS QUADRATIC IN THE GRAPH IT RECORDED — the migrated gate.

Measured 2026-08-07, from the checkpoints of three growth daemons that died
(one killed by the kernel OOM killer at 8.4 GB anon-rss):

    growth7   1,000,067 nodes  ->  960,663  (96.1%)  ImaginedConclusion
    growth9     541,773 nodes  ->  513,578  (94.8%)  ImaginedConclusion

`imagine()` mints one `ImaginedConclusion` per graph_diff entry as a durable
trace on the LIVE graph, and nothing removed them. The diff scales with the
graph, so the trace grew quadratically and permanently — visible directly in
growth9's own fanout: first imagination 66 conclusions, median 1,057, last 2,123,
and by then the imaginations were exhausting their step budget without
converging.

Of 513,578 conclusions, 513,578 SURVIVED and 0 were discarded — nearly all
reading "novel structure -- nothing live to contradict by identity". Structure
with no live counterpart cannot be contradicted by construction, so that verdict
is the null one. The informative record is the DISCARDED conclusion — the caught
fantasy regrounding exists to find.

So the retirement is a signal filter, not a retention window, and these tests
pin the three things that keep it honest: caught fantasies are never retired,
the newest trace is never touched (which is what keeps this clear of
`commit_imagination`, which writes SURVIVORS' content and always operates on the
newest imagination), and the parent's summary counts are preserved so nothing is
silently lost.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.world_adapter import WorldAdapter     # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402


def _agent():
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(
        manifest_for("imagination_trace_retention"), agent.agent)
    return agent


def _imagination(agent, ts, statuses, status="regrounded"):
    survived = sum(1 for s in statuses if s == "survived")
    node = agent.s.add_node("Imagination", {
        "status": status, "ts": ts,
        "n_conclusions": len(statuses),
        "n_survived": survived,
        "n_discarded": len(statuses) - survived,
    })
    conclusions = []
    for state in statuses:
        c = agent.s.add_node("ImaginedConclusion",
                             {"status": state, "kind": "edge_added"})
        agent.inner.add_edge_unchecked(node, "imagined", c)
        conclusions.append((state, c))
    return node, conclusions


# ------------------------------------------------------------- the headline

def test_null_conclusions_of_a_superseded_imagination_are_retired():
    """THE HEADLINE. 513,578 records saying 'nothing contradicted this' are the
    absence of a finding, and they must not outlive the imagination that made
    them."""
    agent = _agent()
    old, conclusions = _imagination(agent, 100, ["survived", "survived", "discarded"])
    _imagination(agent, 200, ["survived"])
    agent.inner.run_rules()

    survived = [c for state, c in conclusions if state == "survived"]
    assert not any(agent.s.has_node(c) for c in survived), (
        "the null verdicts outlived their imagination")


def test_a_CAUGHT_FANTASY_is_never_retired():
    """The informative outcome. Regrounding exists to catch these; retiring them
    would throw away the only thing the trace ever found."""
    agent = _agent()
    old, conclusions = _imagination(agent, 100, ["survived", "discarded"])
    _imagination(agent, 200, ["survived"])
    agent.inner.run_rules()

    discarded = [c for state, c in conclusions if state == "discarded"]
    assert all(agent.s.has_node(c) for c in discarded), (
        "a caught fantasy was retired as though it were noise")


def test_the_NEWEST_trace_is_never_touched():
    """What keeps this clear of `commit_imagination`: that call writes the
    SURVIVORS' content into the live graph and always operates on the
    imagination just made, which is by definition the newest. If the newest
    trace could be compacted, commit could race it."""
    agent = _agent()
    _imagination(agent, 100, ["survived"])
    newest, conclusions = _imagination(agent, 200, ["survived", "survived"])
    agent.inner.run_rules()

    assert all(agent.s.has_node(c) for _, c in conclusions)
    assert "trace_compacted" not in agent.s.node(newest)["attrs"]


def test_a_lone_imagination_is_not_compacted():
    """With nothing newer, there is no supersession — the only trace in the
    graph is the live one."""
    agent = _agent()
    only, conclusions = _imagination(agent, 100, ["survived", "survived"])
    agent.inner.run_rules()

    assert all(agent.s.has_node(c) for _, c in conclusions)
    assert "trace_compacted" not in agent.s.node(only)["attrs"]


def test_an_UNREGROUNDED_imagination_is_left_alone():
    """Status `regrounded` is the completion marker `reground()` writes. An
    imagination still in flight has not had its conclusions judged, so
    `survived` cannot yet mean anything about them."""
    agent = _agent()
    pending, conclusions = _imagination(
        agent, 100, ["survived"], status="in_flight")
    _imagination(agent, 200, ["survived"])
    agent.inner.run_rules()

    assert all(agent.s.has_node(c) for _, c in conclusions)


# ---------------------------------------------------------- nothing is silent

def test_the_summary_counts_survive_the_compaction():
    """The parent already records how many conclusions there were and how they
    fell out. That is what makes retiring the individual null records lossless
    in the only sense that matters."""
    agent = _agent()
    old, _ = _imagination(agent, 100, ["survived", "survived", "discarded"])
    _imagination(agent, 200, ["survived"])
    agent.inner.run_rules()

    attrs = agent.s.node(old)["attrs"]
    assert attrs["n_conclusions"] == 3
    assert attrs["n_survived"] == 2
    assert attrs["n_discarded"] == 1


def test_compaction_is_marked_rather_than_silent():
    """A reader must be able to tell 'this imagination's null records were
    retired' from 'this imagination concluded nothing'."""
    agent = _agent()
    old, _ = _imagination(agent, 100, ["survived"])
    _imagination(agent, 200, ["survived"])
    agent.inner.run_rules()

    assert agent.s.node(old)["attrs"].get("trace_compacted") == 1


def test_compaction_reaches_a_fixed_point():
    """Re-running must not thrash: once the null records are gone there is
    nothing left to retire."""
    agent = _agent()
    old, conclusions = _imagination(agent, 100, ["survived", "discarded"])
    _imagination(agent, 200, ["survived"])
    for _ in range(4):
        agent.inner.run_rules()

    kept = [c for state, c in conclusions if state == "discarded"]
    assert all(agent.s.has_node(c) for c in kept)
    assert agent.s.node(old)["attrs"].get("trace_compacted") == 1


def test_the_bound_holds_across_many_superseded_imaginations():
    """The shape of the live failure: many imaginations, each with a fanout, all
    retained. Only the newest fanout should remain."""
    agent = _agent()
    for ts in range(1, 11):
        _imagination(agent, ts * 10, ["survived"] * 20)
    agent.inner.run_rules()

    remaining = len(agent.s.nodes("ImaginedConclusion"))
    assert remaining == 20, (
        f"expected only the newest imagination's 20 conclusions, got {remaining}")
