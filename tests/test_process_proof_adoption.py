"""P14.03 proof gate tests for explicitly registered domains."""
from evaluation.process_mastery.harness import Agent


def _setup(*, require_proof=False, proof_for_target=False):
    agent = Agent(extra_seeds=("process_laws", "process_proof_adoption"),
                  policy_overrides={"ProcessProofAdoptionPolicy": {"enabled": 1.0}})
    domain = agent.add_domain("proof_domain", "permutation", [[0, 1, 2]], {
        "held_a": [1, 2, 0], "held_b": [0, 2, 1],
    }, family_digest="family-sha256", model_digest="model-sha256",
       model_epoch=2, frame_epoch=3)
    target = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "domain": "proof_domain", "name": "candidate",
        "params": [1, 0, 2], "status": "active", "invented": 1,
        "operator": "commutator", "source_epoch": 0, "model_epoch": 2, "frame_epoch": 3,
    })
    agent.s.add_edge(agent.ag, "has_process_schema", target, {})
    agent.s.add_edge(domain, "has_invented_process", target, {})
    requirement = None
    if require_proof:
        policy = agent.s.neighbours(agent.ag, "has_process_proof_adoption_policy")[0]
        requirement = agent.s.add_node("ProcessProofRequirement", {
            "name": "proof_domain_requirement", "required": 1, "required_law": "commutator_even",
        })
        agent.s.add_edge(policy, "requires_proof_for", requirement, {})
        agent.s.add_edge(requirement, "applies_to", domain, {})
    if proof_for_target:
        _attach_proof(agent, target)
    return agent, domain, target, requirement


def _attach_proof(agent, process):
    law = agent.s.add_node("ProcessLaw", {
        "status": "checked", "proven": 1, "claim": "commutator_even",
        "proof_kind": "native_structural_rule", "proof_rule": "parity_commutator_even_v1",
        "family": "proof_domain", "statement_digest": "statement-sha256",
        "assumptions_digest": "assumptions-sha256",
    })
    agent.s.add_edge(agent.ag, "has_process_law", law, {})
    agent.s.add_edge(law, "about_process", process, {})
    proof = agent.s.add_node("LawProofReference", {
        "status": "checked", "checker": "process_laws_seed_v1", "rule": "parity_commutator_even_v1",
        "family": "proof_domain", "family_digest": "family-sha256",
        "model_digest": "model-sha256", "family_epoch": 0, "process_epoch": 0,
        "model_epoch": 2, "frame_epoch": 3,
        "process_params": agent.attrs(process)["params"],
        "statement_digest": "statement-sha256", "assumptions_digest": "assumptions-sha256",
    })
    agent.s.add_edge(law, "has_proof_reference", proof, {})
    return law, proof


def test_no_required_proof_no_adoption():
    agent, _domain, process, _requirement = _setup()
    agent.run(max_ticks=12)
    attrs = agent.attrs(process)
    assert attrs["status"] == "active"
    assert "proof_adoption_status" not in attrs


def test_wrong_process_proof_rejected():
    agent, _domain, target, _requirement = _setup(require_proof=True)
    other = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "domain": "proof_domain", "name": "other",
        "params": [0, 2, 1], "status": "active", "invented": 1,
        "operator": "commutator", "source_epoch": 0, "model_epoch": 2, "frame_epoch": 3,
    })
    agent.s.add_edge(agent.ag, "has_process_schema", other, {})
    _attach_proof(agent, other)
    agent.run(max_ticks=12)
    assert agent.attrs(target)["status"] == "proof_blocked"
    assert agent.attrs(target)["proof_adoption_status"] == "blocked"


def test_changed_process_invalidates_proof():
    agent, _domain, process, _requirement = _setup(require_proof=True, proof_for_target=True)
    agent.run(max_ticks=12)
    assert agent.attrs(process)["status"] == "active"
    assert agent.attrs(process)["proof_adoption_status"] == "approved"
    agent.s.set_attr(process, "params", [2, 1, 0])
    agent.run(max_ticks=12)
    attrs = agent.attrs(process)
    assert attrs["status"] == "proof_blocked"
    assert attrs["proof_adoption_status"] == "invalidated"
    assert attrs["proof_adoption_reason"] == "process_parameters_changed"


def test_proof_does_not_authorize_external_action():
    agent, _domain, process, _requirement = _setup(require_proof=True, proof_for_target=True)
    request = agent.s.add_node("ExternalActionRequest", {"status": "pending"})
    agent.run(max_ticks=12)
    assert agent.attrs(process)["proof_adoption_status"] == "approved"
    assert agent.attrs(process)["external_action_authorized"] == 0
    assert agent.attrs(request)["status"] == "pending"
