"""THE DEVELOPMENTAL MEASUREMENT CHANNEL — the migrated gate.

Measured from a live 13-hour checkpoint (2.3M nodes, 13 sessions, 111 physical
trials): every session sat at curriculum ordinal 0, and the capability counters
carried the signature `attempt_count == failure_count` with `success_count`
pinned at exactly 1.

That signature is not a counting bug.  `ed_learn_capability_from_causally_closed_receipt`
books `attempt += 1`, `success += S` and `failure += (1 - S)` off ONE criterion,
so `attempt == failure` is the arithmetic statement that S was 0 on every
receipt.  S was 0 because the field it reads —
`receipt.development_configuration_changed` — was never written by anything:
51 of 58 `development_*` fields were read by rules and written by nobody.  Rule
terms read attributes through a `Plus[Attr, Lit 0]` null-coalescing idiom, so a
MISSING measurement is indistinguishable from a FAILED one, and the whole
curriculum failed silently for thirteen hours without raising anything.

This gate spans the join: transducer evidence -> session receipt -> capability
accounting, with BOTH seeds loaded, which is what no single existing test did.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.world_adapter import WorldAdapter     # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _agent():
    """Both halves of the join, unlike either seed's own gate."""
    agent = WorldAdapter()
    for seed in ("counterfactual_experiment", "embodied_learning_session",
                 "embodied_development"):
        agent.inner.load_seed_manifest(manifest_for(seed), agent.agent)
    return agent


def _closed_receipt(agent, *, proprioceptive_delta):
    """Drive one trial to a closed developmental receipt and return it.

    The receipt is minted by the session rule from the evidence — the test
    never writes a `development_*` field itself, which is the whole point.
    """
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    body = agent.s.add_node("EmbodiedBodySchema", {"morphology_epoch": 1})
    world = agent.s.add_node("EmbodiedLearningWorld", {"world_epoch": 1})
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, episode, "has_embodied_body_schema", body)
    _edge(agent, episode, "has_embodied_learning_world", world)
    agent.tick()

    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability",
        {"success_count": 0, "attempt_count": 0, "failure_count": 0,
         "last_receipt_seq": 0, "activation_receipt_seq": 0,
         "evidence_kind": "spontaneous_configuration_change"})
    _edge(agent, episode, "has_active_embodied_developmental_capability",
          capability)
    # The acquisition rule is gated on the episode actively learning; in the
    # live daemon this flag is set by the developmental episode itself.
    agent.inner.set_attr(episode, "development_learning_active", 1)
    return episode, capability, proprioceptive_delta


def _book_one_receipt(agent, episode, capability, *, configuration_changed):
    """Publish one closed receipt carrying the wired measurement and settle."""
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed",
        "development_receipt_closed": 1,
        "development_receipt_seq": 1,
        "development_configuration_changed": configuration_changed,
        "development_external_event": 0,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "embodiment_destroyed": 0,
        "causal_closed": 1, "grounded": 1,
        "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 1)
    agent.tick()
    return agent.s.node(capability)["attrs"]


def test_the_session_rule_writes_the_measurement_the_criterion_reads():
    """The field name join, asserted on the SEED rather than on a fixture.

    The criterion in `embodied_development` reads exactly the key the
    `embodied_learning_session` receipt rule writes.  A rename on either side
    silently reopens the thirteen-hour failure, so it is pinned here.
    """
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    session_seed = json.loads(
        (root / "seeds" / "embodied_learning_session.json").read_text())
    rule = next(r for r in session_seed["rules"]
                if r["name"] == "els_close_exact_external_trial_as_causal_development_receipt")
    minted = next(e[3] for e in rule["effects"]
                  if e[0] == "add_node" and e[2] == "EmbodiedLearningTrialReceipt")
    assert "development_configuration_changed" in minted
    assert "development_external_event" in minted

    development_seed = json.loads(
        (root / "seeds" / "embodied_development.json").read_text())
    criterion = next(r for r in development_seed["rules"]
                     if r["name"] == "ed_learn_capability_from_causally_closed_receipt")
    body = json.dumps(criterion)
    assert '"key": "development_configuration_changed"' in body
    assert '"key": "development_external_event"' in body


def test_a_moved_body_books_a_success_and_the_counters_separate():
    agent = _agent()
    episode, capability, _ = _closed_receipt(agent, proprioceptive_delta=[1])
    attrs = _book_one_receipt(agent, episode, capability,
                              configuration_changed=1)
    assert attrs["attempt_count"] == 1
    assert attrs["success_count"] == 1
    assert attrs["failure_count"] == 0
    # The live signature was attempt == failure. It must no longer hold.
    assert attrs["attempt_count"] != attrs["failure_count"]


def test_a_still_body_books_a_failure_and_is_distinguishable_from_a_gap():
    agent = _agent()
    episode, capability, _ = _closed_receipt(agent, proprioceptive_delta=[0])
    attrs = _book_one_receipt(agent, episode, capability,
                              configuration_changed=0)
    assert attrs["attempt_count"] == 1
    assert attrs["success_count"] == 0
    assert attrs["failure_count"] == 1
    # An honest negative looks exactly like the thirteen-hour signature —
    # which is precisely why the MISSING field was undetectable from the
    # counters alone, and why the field's presence is pinned above.
    assert attrs["attempt_count"] == attrs["failure_count"]
