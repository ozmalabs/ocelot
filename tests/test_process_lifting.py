"""P10.02 witnessed process-family lifting and native instance checks."""
from evaluation.process_mastery.harness import Agent


def _family_agent():
    return Agent(extra_seeds=("process_lifting",),
                 policy_overrides={"ProcessLiftingPolicy": {"enabled": 1.0},
                                   "InventionPolicy": {"enabled": 0.0}})


def _cycle(n):
    return [(i + 1) % n for i in range(n)]


def _swap(n):
    p = list(range(n))
    p[0], p[1] = p[1], p[0]
    return p


def _compose(a, b):
    return [b[a[i]] for i in range(len(a))]


def _inverse(p):
    out = [0] * len(p)
    for i, j in enumerate(p):
        out[j] = i
    return out


def _commutator(n):
    a, b = _cycle(n), _swap(n)
    return _compose(_compose(_compose(a, b), _inverse(a)), _inverse(b))


def _pair(agent, right_kind="permutation"):
    agent.add_domain("train-3", "permutation", [[0, 1, 2]], {"c0": _commutator(3)}, size=3)
    agent.add_domain("train-5", right_kind, [[0, 1, 2, 3, 4]], {"c1": _commutator(5)}, size=5)
    for domain, size in (("train-3", 3), ("train-5", 5)):
        schema = agent.schemas(domain)[0]
        agent.s.set_attr(schema, "operator", "commutator")
        agent.s.set_attr(schema, "expr_tree", [
            "commutator", ["cycle", size, 0, size], ["swap", size, 0, 1]])
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
    assert attrs["template"][0] == ("commutator", ("cycle", ("·?·",), 0, ("·?·",)),
                                     ("swap", ("·?·",), 0, 1))


def test_unseen_size_verified():
    agent = _family_agent()
    _pair(agent)
    agent.s.set_attr(agent.nodes("ProcessLiftingPolicy")[0], "unseen_size_enabled", 1.0)
    agent.add_domain("test-6", "permutation", [[0, 1, 2, 3, 4, 5]],
                     {"identity": list(range(6))}, size=6)
    for _ in range(5):
        agent.s.tick(1000)
    lifted = [s for s in agent.schemas("test-6")
              if agent.attrs(s).get("provenance") == "lifted_from_witness"]
    assert len(lifted) == 1
    attrs = agent.attrs(lifted[0])
    assert list(attrs["params"]) == _commutator(6)
    assert attrs["effect_evaluation"] == "exact:native_lift_on_target_probes"
    assert attrs["verification_receipt"] == "native_target_domain_fingerprint"
    assert len(attrs["params"]) == 6


def test_mismatched_kind_rejected():
    agent = _family_agent()
    _pair(agent, right_kind="integer_matrix")
    assert not agent.nodes("LiftedProcessFamily")


def test_bad_binding_rejected():
    agent = _family_agent()
    _pair(agent)
    agent.s.set_attr(agent.nodes("ProcessLiftingPolicy")[0], "unseen_size_enabled", 1.0)
    family = agent.nodes("LiftedProcessFamily")[0]
    witness = list(agent.attrs(family)["template"])
    sigmas = list(witness[1])
    first = dict(sigmas[0])
    first[(1, 3)] = 2
    sigmas[0] = first
    agent.s.set_attr(family, "template", (witness[0], tuple(sigmas)))
    agent.add_domain("bad-6", "permutation", [[0, 1, 2, 3, 4, 5]],
                     {"identity": list(range(6))}, size=6)
    for _ in range(5):
        agent.s.tick(1000)
    assert not [s for s in agent.schemas("bad-6")
                if agent.attrs(s).get("provenance") == "lifted_from_witness"]


def test_lifted_provenance_retained():
    agent = _family_agent()
    _pair(agent)
    family = agent.nodes("LiftedProcessFamily")[0]
    parents = agent.s.neighbours(family, "has_source_schema")
    assert len(parents) == 2
    assert agent.attrs(family)["provenance"] == "anti_unify_witness"
    assert len(set(agent.attrs(family)["source_domains"])) == 2
