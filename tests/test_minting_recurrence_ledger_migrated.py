"""Native recurrence-ledger and held-out semantic counterfactual controls."""
from __future__ import annotations

import json
from pathlib import Path

from domains import minting_train_of_thought as mtot
from substrate.boot_core import boot_core, load_seeds_into
from substrate.seed_loader import manifest_for


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/capability/minting/fixtures/recurrence_relation_semantics.json").read_text())


def _native_case(case_name: str, *, load_demo: bool = True):
    """Three otherwise-isomorphic P, empty, P episodes, directly at the native ledger."""
    case = FIXTURE["cases"][case_name]
    substrate, agent = boot_core(seeds=())
    load_seeds_into(substrate, agent, ["minting_recurrence_ledger"])
    if load_demo:
        summary = substrate._inner.load_seed_manifest(manifest_for("minting_recurrence_semantic_demo"), agent)
        assert not summary.get("rules_skipped"), summary
    episode = substrate.add_node("MintingRecurrenceEpisode", {
        "mint_after_quanta": FIXTURE["threshold"], "integer_native": 1,
        "setpoint_topic": "held_out", "setpoint_observer": "test",
    })
    substrate.add_edge(agent, "has_minting_recurrence_episode", episode)
    request = substrate.add_node("OperationRequest", dict(FIXTURE["operation_request"]))
    substrate._inner.add_edge_unchecked(agent, "operation_request", request, {})

    for ordinal, present in enumerate((True, False, True)):
        if not present:
            substrate._inner.run_rules()
            continue
        evidence = substrate.add_node("ResidualSegmentEvidence", {
            "predicate": case["predicate"],
            "capability_key": "minted_bind", "segment_ordinal": ordinal,
            "display_name": case["display_name"], "integer_native": 1,
        })
        substrate.add_edge(episode, "has_residual_segment_evidence", evidence)
        if case["witness"] is not None:
            witness = substrate.add_node("ResidualRelationWitness", dict(case["witness"]))
            substrate.add_edge(evidence, "has_relation_witness", witness)
        substrate._inner.run_rules()
    substrate._inner.run_rules()  # explicit idempotence rerun
    return substrate, agent, episode, request


def _one(nodes, predicate):
    matches = list(nodes)
    assert len(matches) == 1
    return matches[0]


def test_native_ledger_is_idempotent_and_records_full_provenance():
    substrate, _agent, episode, request = _native_case("positive")
    candidate = _one(substrate.neighbours(episode, "has_predicate_recurrence_candidate"), "candidate")
    evidence = list(substrate.neighbours(candidate, "supported_by_segment"))
    offer = _one(substrate.neighbours(candidate, "has_mint_offer"), "offer")
    axis = _one(substrate.neighbours(candidate, "minted_axis"), "axis")
    cattrs, oattrs = substrate.node(candidate)["attrs"], substrate.node(offer)["attrs"]

    assert cattrs["predicate"] == "bind"  # predicate-only identity remains locked
    assert len(evidence) == 2
    assert cattrs["persistence"] == len(evidence) == 2
    assert oattrs["offered_at_persistence"] == 2
    assert oattrs["offered_at_segment"] == 2
    assert oattrs["offer_status"] == "minted" and oattrs["offer_resolved"] == 1
    assert axis in substrate.neighbours(episode, "minted_axis")
    assert substrate.node(request)["attrs"]["admissible"] == 1
    assert axis in substrate.neighbours(request, "reachable_via")

    before = {kind: len(substrate.nodes(kind)) for kind in
              ("PredicateRecurrenceCandidate", "ResidualSegmentEvidence", "Observation", "CapabilityAxis")}
    substrate._inner.run_rules()
    after = {kind: len(substrate.nodes(kind)) for kind in before}
    assert after == before


def test_semantic_counterfactual_requires_relation_witness_not_name_or_predicate():
    positive = _native_case("positive")
    syntax_only = _native_case("syntax_name_only")
    mismatch = _native_case("semantic_mismatch")

    for substrate, _agent, episode, request in (positive, syntax_only, mismatch):
        candidate = _one(substrate.neighbours(episode, "has_predicate_recurrence_candidate"), "candidate")
        assert substrate.node(candidate)["attrs"]["predicate"] == "bind"
        assert substrate.node(candidate)["attrs"]["persistence"] == 2
        assert len(list(substrate.neighbours(candidate, "has_mint_offer"))) == 1
        # All controls are recurrence-equivalent and may receive the same predicate-keyed mint.
        assert len(list(substrate.neighbours(candidate, "minted_axis"))) == 1

    assert positive[0].node(positive[3])["attrs"]["admissible"] == 1
    assert list(positive[0].neighbours(positive[3], "reachable_via"))
    assert not syntax_only[0].node(syntax_only[3])["attrs"].get("admissible")
    assert not list(syntax_only[0].neighbours(syntax_only[3], "reachable_via"))
    assert not mismatch[0].node(mismatch[3])["attrs"].get("admissible")
    assert not list(mismatch[0].neighbours(mismatch[3], "reachable_via"))


def test_loader_installs_recurrence_rules_once():
    substrate, agent = boot_core(seeds=())
    first = load_seeds_into(substrate, agent, ["minting_recurrence_ledger"])
    second = load_seeds_into(substrate, agent, ["minting_recurrence_ledger"])
    assert first == second
    names = [rule.get("name") for rule in substrate._inner.export_rules() if isinstance(rule, dict)]
    for name in ("mrl_open_candidate", "mrl_post_evidence_once", "mrl_derive_persistence",
                 "mrl_offer_due_once", "mrl_record_offer_terminal", "mrl_record_mint_result"):
        assert names.count(name) == 1
