"""SUPPORT TOPOLOGY: WHICH CONTACTS EXIST, NOT HOW HARD — the migrated gate.

`surface_contact_mapping` (ordinal 3) sat at 61 attempts / 0 successes reading
`receipt.development_support_topology_changed` — 73 reads, 0 writes. Three more
fields in the same family were equally dark and are answerable from the SAME
measurement: the set of links in ground contact before and after a trial.

The trap this family is especially prone to: a body resting on the floor has a
STABLE topology, so "changed" is genuinely 0 most of the time and that zero is a
real measurement. An ABSENT reading must not report "unchanged" — unobserved and
unchanged are different facts, and conflating them is what made stage 0
unsatisfiable for thirteen hours.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from domains.pybullet_humanoid_trial_transducer import _support_topology       # noqa: E402
from substrate.seed_loader import manifest_for                                 # noqa: E402
from substrate.world_adapter import WorldAdapter                               # noqa: E402


# ------------------------------------------- the boundary extraction

def test_topology_is_the_link_set_not_the_force():
    obs = {"whole_body_support_contacts": (
        {"link_index": 7, "normal_force": 0.1},
        {"link_index": 3, "normal_force": 90.0},
    )}
    assert _support_topology(obs) == (3, 7)


def test_the_same_topology_always_compares_equal():
    a = {"whole_body_support_contacts": ({"link_index": 5}, {"link_index": 2})}
    b = {"whole_body_support_contacts": ({"link_index": 2}, {"link_index": 5})}
    assert _support_topology(a) == _support_topology(b)


def test_an_unreported_topology_is_empty_not_invented():
    assert _support_topology({}) == ()


# ------------------------------------------------- the graph's decision

def _agent():
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(manifest_for("embodied_learning_session"),
                                   agent.agent)
    return agent


def _receipt(agent, **evidence_attrs):
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt",
                               {"status": "closed", "integer_native": 1})
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence",
                                {"integer_native": 1, **evidence_attrs})
    agent.inner.add_edge_unchecked(
        receipt, "grounded_in_external_trial_evidence", evidence)
    agent.inner.run_rules()
    return agent.s.node(receipt)["attrs"]


def _observed(before, after):
    return {
        "support_contact_links_before": list(before),
        "support_contact_links_after": list(after),
        "support_contact_count_before": len(before),
        "support_contact_count_after": len(after),
        "support_contact_observed": 1,
    }


def test_a_changed_topology_is_reported_changed():
    attrs = _receipt(agent := _agent(), **_observed((3, 7), (3,)))  # noqa: F841
    assert attrs["development_support_topology_changed"] == 1
    assert attrs["development_post_support_count"] == 1
    assert attrs["development_support_gain"] == -1
    assert attrs["development_support_extent_gain"] == 0


def test_a_stable_topology_reports_a_REAL_zero():
    """A body resting on the floor is genuinely unchanged. That zero is a
    measurement, and it must be recorded as one."""
    attrs = _receipt(_agent(), **_observed((3, 7), (3, 7)))
    assert attrs["development_support_topology_changed"] == 0
    assert attrs["development_support_observed"] == 1
    assert attrs["development_post_support_count"] == 2


def test_gaining_support_is_an_extent_gain():
    attrs = _receipt(_agent(), **_observed((3,), (3, 7, 9)))
    assert attrs["development_support_gain"] == 2
    assert attrs["development_support_extent_gain"] == 1


# ------------------------------------------------------------ the trap

def test_an_UNOBSERVED_topology_writes_nothing_at_all():
    """THE HEADLINE. Unobserved is not unchanged. The fields stay ABSENT, so
    every consumer reading them through `+ 0` refuses rather than scoring a
    success against a measurement that was never taken."""
    attrs = _receipt(_agent())
    for key in ("development_support_topology_changed",
                "development_post_support_count",
                "development_support_gain",
                "development_support_extent_gain",
                "development_support_observed"):
        assert key not in attrs, f"{key} fabricated without an observation"


def test_a_partial_reading_is_refused_rather_than_half_written():
    attrs = _receipt(_agent(), support_contact_observed=1,
                     support_contact_links_before=[3])
    assert "development_support_topology_changed" not in attrs


def test_unchanged_and_unobserved_are_distinguishable_in_the_graph():
    stable = _receipt(_agent(), **_observed((3,), (3,)))
    blind = _receipt(_agent())
    assert stable["development_support_topology_changed"] == 0
    assert stable["development_support_observed"] == 1
    assert "development_support_observed" not in blind


def test_the_carry_is_idempotent_under_a_re_run_fixpoint():
    agent = _agent()
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt",
                               {"status": "closed", "integer_native": 1})
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence",
                                {"integer_native": 1, **_observed((3,), (3, 7))})
    agent.inner.add_edge_unchecked(
        receipt, "grounded_in_external_trial_evidence", evidence)
    for _ in range(4):
        agent.inner.run_rules()
    attrs = agent.s.node(receipt)["attrs"]
    assert attrs["development_support_topology_changed"] == 1
    assert attrs["development_support_gain"] == 1
