"""P14.01 contract guards. These tests pin the frozen boundary before P14.02 implementation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/research/engine_substrate/COGNITION_PROOF_OPERATOR_CONTRACT.md"


def _contract():
    return CONTRACT.read_text()


def test_empirical_invariant_not_theorem():
    text = _contract()
    empirical = text.split("An **empirical invariant**", 1)[1].split("A **conjecture**", 1)[0]
    assert "not a theorem" in empirical
    assert "cannot satisfy a proof obligation" in empirical


def test_proof_assumptions_bound():
    text = _contract()
    assert "assumption digest" in text
    assert "family/model digest" in text
    assert "Any change to a bound input invalidates the proof reference" in text
    assert "missing assumptions" in text


def test_operator_cannot_edit_verifier():
    text = _contract()
    boundaries = text.split("An authored invention operator", 1)[1].split("Candidate selection", 1)[0]
    for protected in ("verifier", "checker", "evaluation harness", "held-out allocation", "criteria"):
        assert protected in boundaries


def test_human_gate_not_bypassed():
    text = _contract()
    assert "requires the existing human approval gate" in text
    assert "policies remain disabled by default" in text
    assert "held-out results remain untouched" in text


def _agent():
    from evaluation.process_mastery.harness import Agent
    return Agent(extra_seeds=("process_laws",),
                 policy_overrides={"ProcessLawsPolicy": {"enabled": 1.0}})


def _commutator_case(*, family="permutation_fixture", status="conjecture",
                     evidence_kind="structural_derivation", counterexample_count=0,
                     forged_params=False):
    agent = _agent()
    domain = agent.add_domain(family, "permutation", [[0, 1, 2]], {
        "held_a": [1, 2, 0], "held_b": [0, 2, 1],
    }, family_digest="family-sha256-fixture", model_digest="model-sha256-fixture",
       model_epoch=0, frame_epoch=0)
    a, b = [n for n in agent.schemas(family) if agent.attrs(n)["provenance"] == "held"]
    from scripts.track_i_seed_lib import A, PCommutator
    exact_commutator = agent.native.evaluate(PCommutator(A("a", "params"), A("b", "params")),
                                             {"a": a, "b": b})
    schema = agent.s.add_node("ProcessSchema", {
        "kind": "permutation", "domain": family, "domain_kind": "permutation",
        "name": "commutator_ab", "operator": "commutator", "status": "active",
        "params": [0, 1, 2] if forged_params else exact_commutator,
        "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
        "provenance": "invented_by:commutator",
    })
    agent.s.add_edge(agent.ag, "has_process_schema", schema, {})
    agent.s.add_edge(schema, "has_arg0", a, {})
    agent.s.add_edge(schema, "has_arg1", b, {})
    law = agent.s.add_node("ProcessLaw", {
        "claim": "commutator_even", "family": family, "family_epoch": 0,
        "family_digest": "family-sha256-fixture", "model_digest": "model-sha256-fixture",
        "model_epoch": 0, "frame_epoch": 0, "process_epoch": 0,
        "statement_digest": "4e3f9f19059a7254dbc8b885e464eccf69cec770eec50cb43a4d89e01415adb2",
        "assumptions_digest": "d055b01ab1e76e1190f7b04e01fe250ab42f5ce6ccc24eaf4dfd84263ec96077",
        "assumptions": "permutation_group;parity_homomorphism_Z2;operator_semantics_v1",
        "evidence_kind": evidence_kind, "status": status,
        "counterexample_count": counterexample_count, "proven": 0,
    })
    agent.s.add_edge(agent.ag, "has_process_law_candidate", law, {})
    agent.s.add_edge(law, "about_process", schema, {})
    return agent, domain, law


def test_parity_law_checked():
    agent, _domain, law = _commutator_case()
    agent.run(max_ticks=12)
    attrs = agent.attrs(law)
    assert attrs["status"] == "checked"
    assert attrs["proof_kind"] == "native_structural_rule"
    assert attrs["proof_rule"] == "parity_commutator_even_v1"
    refs = agent.native.neighbours(law, "has_proof_reference")
    assert len(refs) == 1 and agent.attrs(refs[0])["status"] == "checked"
    proof = agent.attrs(refs[0])
    assert proof["statement_digest"] == agent.attrs(law)["statement_digest"]
    assert proof["assumptions_digest"] == agent.attrs(law)["assumptions_digest"]
    assert proof["family_digest"] == "family-sha256-fixture"
    assert proof["model_digest"] == "model-sha256-fixture"
    process = agent.native.neighbours(law, "about_process")[0]
    assert proof["process_params"] == agent.attrs(process)["params"]


def test_false_finite_sample_law_rejected():
    agent, _domain, law = _commutator_case(
        evidence_kind="finite_sample", counterexample_count=1)
    agent.run(max_ticks=12)
    attrs = agent.attrs(law)
    assert attrs["status"] == "rejected"
    assert attrs["verdict"] == "counterexample"
    assert attrs["proven"] == 0


def test_law_proof_bound_to_family():
    agent, _domain, law = _commutator_case()
    agent.s.set_attr(law, "family", "different_family")
    agent.run(max_ticks=12)
    assert agent.attrs(law)["status"] == "conjecture"
    assert not agent.native.neighbours(law, "has_proof_reference")


def test_commutator_proof_checks_exact_constructor_output():
    agent, _domain, law = _commutator_case(forged_params=True)
    agent.run(max_ticks=12)
    assert agent.attrs(law)["status"] == "conjecture"
    assert not agent.native.neighbours(law, "has_proof_reference")


def test_counterexample_downgrades_conjecture():
    agent, _domain, law = _commutator_case()
    agent.run(max_ticks=12)
    assert agent.attrs(law)["status"] == "checked"
    ce = agent.s.add_node("LawCounterexample", {"validated": 1, "source": "held_out_probe"})
    agent.s.add_edge(law, "has_counterexample", ce, {})
    agent.run(max_ticks=12)
    attrs = agent.attrs(law)
    assert attrs["status"] == "rejected"
    assert attrs["verdict"] == "counterexample" and attrs["proven"] == 0
