"""A DERIVED RELATION MUST NOT OUTLIVE ITS PREMISE — the migrated gate.

`cp_recognize_relational_dominance` records "alternative dominates candidate"
as a permanent edge and then stops re-scanning the candidate, reasoning that
"more dominators cannot change frontier membership". True for an immutable
frontier; false for a learning one, whose candidates have their Pareto values
rewritten by every receipt.

Measured on a live grounded humanoid: the motor frontier accumulated dominance
until 43 of 43 candidates were dominated (dominator counts 7-42, none zero), no
motor program could be selected, and trial production stopped dead at 48-52
trials on three separate runs. A finite non-empty set under a strict partial
order always has a maximal element, so an EMPTY frontier is never a fact about
the candidates — it is proof the relation being read is stale.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.seed_loader import manifest_for                          # noqa: E402
from substrate.world_adapter import WorldAdapter                        # noqa: E402


DIMENSIONS = 2


def _agent():
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(manifest_for("cognitive_pareto"), agent.agent)
    return agent


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _profile(agent):
    return agent.s.add_node("ParetoProfile", {
        "dimension_count": DIMENSIONS, "pareto_suspended": 0,
        "integer_native": 1})


def _candidate(agent, profile, values):
    candidate = agent.s.add_node("ParetoCandidate", {
        "verified": 1, "dominated": 0, "integer_native": 1})
    _edge(agent, profile, "has_pareto_candidate", candidate)
    for ordinal, value in enumerate(values):
        node = agent.s.add_node("ParetoValue", {
            "dimension_ordinal": ordinal, "signed_value": value,
            "verified": 1, "integer_native": 1})
        _edge(agent, candidate, "has_pareto_value", node)
    return candidate


def _revalue(agent, candidate, values):
    """Rewrite a candidate's Pareto values, as a receipt does on a live run."""
    for node in agent.inner.neighbours(candidate, "has_pareto_value"):
        ordinal = agent.s.node(node)["attrs"]["dimension_ordinal"]
        agent.inner.set_attr(node, "signed_value", values[ordinal])


def _dominators(agent, candidate):
    return agent.inner.neighbours(candidate, "is_dominated_by_pareto_candidate")


def _frontier(agent, profile):
    return [c for c in agent.inner.neighbours(profile, "has_pareto_candidate")
            if not _dominators(agent, c)]


def _run(agent):
    agent.inner.run_rules()


# ------------------------------------------------------- recognition stands

def test_a_genuine_counterexample_is_still_recognised():
    """The fix must not weaken recognition — only withdraw what became false."""
    agent = _agent()
    profile = _profile(agent)
    weak = _candidate(agent, profile, [1, 1])
    strong = _candidate(agent, profile, [5, 5])
    _run(agent)
    assert _dominators(agent, weak) == [strong]
    assert agent.s.node(weak)["attrs"]["dominated"] == 1
    assert _frontier(agent, profile) == [strong]


# ------------------------------------------------------------ the defect

def test_dominance_is_withdrawn_when_the_values_no_longer_support_it():
    """THE DEFECT, GATED.

    The dominated candidate improves past its dominator. Under the cached
    relation it stayed dominated forever; it must now return to the frontier.
    """
    agent = _agent()
    profile = _profile(agent)
    climber = _candidate(agent, profile, [1, 1])
    incumbent = _candidate(agent, profile, [5, 5])
    _run(agent)
    assert _dominators(agent, climber) == [incumbent]

    _revalue(agent, climber, [9, 9])
    _run(agent)
    assert _dominators(agent, climber) == []
    assert agent.s.node(climber)["attrs"]["dominated"] == 0
    assert climber in _frontier(agent, profile)


def test_the_frontier_can_never_empty():
    """A finite non-empty set under a strict partial order has a maximal
    element. An empty frontier is proof of staleness, never a fact."""
    agent = _agent()
    profile = _profile(agent)
    cands = [_candidate(agent, profile, [n, 10 - n]) for n in range(1, 6)]
    _run(agent)
    assert _frontier(agent, profile)
    # Rewrite every candidate's values repeatedly, as receipts do.
    for step in range(1, 6):
        for index, candidate in enumerate(cands):
            _revalue(agent, candidate, [(index + step) % 7, (step * 2 + index) % 7])
        _run(agent)
        assert _frontier(agent, profile), f"frontier emptied at step {step}"


def test_a_stale_flag_cannot_outlive_the_edge_it_summarises():
    agent = _agent()
    profile = _profile(agent)
    climber = _candidate(agent, profile, [1, 1])
    _candidate(agent, profile, [5, 5])
    _run(agent)
    assert agent.s.node(climber)["attrs"]["dominated"] == 1
    _revalue(agent, climber, [9, 9])
    _run(agent)
    assert agent.s.node(climber)["attrs"]["dominated"] == 0


def test_completed_history_is_neither_re_tested_nor_edited():
    """A suspended profile is immutable history to BOTH rules, symmetrically."""
    agent = _agent()
    profile = _profile(agent)
    climber = _candidate(agent, profile, [1, 1])
    _candidate(agent, profile, [5, 5])
    _run(agent)
    assert _dominators(agent, climber)
    agent.inner.set_attr(profile, "pareto_suspended", 1)
    _revalue(agent, climber, [9, 9])
    _run(agent)
    assert _dominators(agent, climber), "history was edited"


def test_retraction_is_idempotent_under_a_re_run_fixpoint():
    agent = _agent()
    profile = _profile(agent)
    climber = _candidate(agent, profile, [1, 1])
    _candidate(agent, profile, [5, 5])
    _run(agent)
    _revalue(agent, climber, [9, 9])
    for _ in range(4):
        _run(agent)
        assert _dominators(agent, climber) == []
