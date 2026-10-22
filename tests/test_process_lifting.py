"""P10.02 witnessed process-family lifting boundaries."""
import pytest

from evaluation.process_mastery.harness import Agent


def _family_agent():
    return Agent(extra_seeds=("process_lifting",),
                 policy_overrides={"ProcessLiftingPolicy": {"enabled": 1.0},
                                   "InventionPolicy": {"enabled": 0.0}})


def _pair(agent, left_kind="permutation", right_kind="permutation"):
    agent.add_domain("train-3", left_kind, [[0, 1, 2]], {"c0": [1, 2, 0]})
    agent.add_domain("train-5", right_kind, [[0, 1, 2, 3, 4]], {"c1": [1, 2, 3, 4, 0]})
    for domain, idx, size in (("train-3", 0, 3), ("train-5", 0, 5)):
        schema = agent.schemas(domain)[0]
        agent.s.set_attr(schema, "operator", "commutator")
        agent.s.set_attr(schema, "expr_tree", ["commutator", ["cycle", idx, size]])
    for _ in range(5):
        agent.s.tick(1000)


def test_parameterized_commutator_lifts():
    agent = _family_agent()
    _pair(agent)
    families = agent.nodes("LiftedProcessFamily")
    assert len(families) == 1
    attrs = agent.attrs(families[0])
    assert attrs["status"] == "witnessed_candidate"
    assert attrs["witness_count"] == 2
    assert attrs["effect_evaluation"] == "unverified_template"
    assert attrs["template"][0] == ("commutator", ("cycle", 0, ("·?·",)))


def test_unseen_size_verified():
    pytest.skip("Symbolic family-to-process construction is not implemented; no unseen-size effect is claimed")


def test_bad_binding_rejected():
    agent = _family_agent()
    _pair(agent, right_kind="integer_matrix")
    assert not agent.nodes("LiftedProcessFamily")


def test_lifted_provenance_retained():
    agent = _family_agent()
    _pair(agent)
    family = agent.nodes("LiftedProcessFamily")[0]
    parents = agent.s.neighbours(family, "has_source_schema")
    assert len(parents) == 2
    assert agent.attrs(family)["provenance"] == "anti_unify_witness"
    assert len(set(agent.attrs(family)["source_domains"])) == 2
