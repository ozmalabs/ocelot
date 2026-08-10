"""A MEASUREMENT THAT ARRIVES AFTER ITS CONSUMER IS A MEASUREMENT THAT NEVER HAPPENED.

Measured from growth9's final checkpoint (2026-08-07, 482 receipts): the support
topology channel was LIT — all 482 receipts carried
`development_support_topology_changed`, and 164 of them (34%) carried a 1 — while
`surface_contact_mapping` (ordinal 3, `evidence_kind == "support_topology_change"`,
the capability whose success criterion reads exactly that field) sat at
310 attempts / 310 failures / 0 successes.

Both rules are `hard_realtime` and run in the same `run_rules` fixpoint, but they
are not symmetric in REGISTRATION ORDER:

  * `els_carry_observed_support_topology_to_causal_receipt` (embodied_learning_session)
    WRITES the field onto the receipt from the trial evidence. It is not gated on
    the receipt being closed.
  * `ed_learn_capability_from_causally_closed_receipt` (embodied_development)
    READS it, books attempt/success/failure, and then raises
    `instance.last_receipt_seq` to this receipt's seq — which makes its own guard
    false forever. The receipt is consumed EXACTLY ONCE and can never be re-credited.

Measured on the daemon's own `seeds="embodied"` boot set, the consumers come 213
rules BEFORE the producer:

    ed_update_learning_plan_step_from_causal_receipt        index 259
    ed_learn_capability_from_causally_closed_receipt        index 260
    els_carry_observed_support_topology_to_causal_receipt   index 473

`embodied_development` resolves ahead of `embodied_learning_session` in the
dependency closure, so the credit rule reads the field while it is still ABSENT,
`P0`'s `Plus[Attr, Lit 0]` coalesces that absence to 0, a failure is booked, and
the seq guard closes the receipt to any later correction. The carry rule then
writes the true value onto a receipt nobody will ever score again.

THE INVARIANT THIS FILE GATES: a rule that ENRICHES a receipt and a rule that
CONSUMES it must not be order-dependent, because nothing in a seed's dependency
declaration expresses "run after everything that might still write to my input".
Producing the right answer only under a lucky registration order is not producing
the right answer. So both orders are asserted, and they must agree.

The existing gate (`test_support_topology_channel_migrated.py`) cannot see any of
this: it loads only `embodied_learning_session`, so the consumer is not in the
graph at all, and the carry rule passes in isolation while the capability it feeds
stays at zero. This file loads BOTH and never writes a `development_support_*`
field itself — the carry rule has to put it there, which is the whole question.
"""
import pytest                                          # noqa: E402
from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.world_adapter import WorldAdapter     # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


# The producer-first order is the one that happens to work; the consumer-first
# order is the one the daemon's own `seeds="embodied"` closure actually produces.
# A correct rule set is indifferent to both.
PRODUCER_FIRST = ("embodied_learning_session", "embodied_development")
CONSUMER_FIRST = ("embodied_development", "embodied_learning_session")
BOTH_ORDERS = pytest.mark.parametrize(
    "order", [PRODUCER_FIRST, CONSUMER_FIRST],
    ids=["carry_registered_first", "credit_registered_first_LIVE"])


def _agent(order=PRODUCER_FIRST):
    agent = WorldAdapter()
    for seed in ("counterfactual_experiment",) + tuple(order):
        agent.inner.load_seed_manifest(manifest_for(seed), agent.agent)
    return agent


def _episode_with_active_capability(agent, evidence_kind):
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
         "evidence_kind": evidence_kind})
    _edge(agent, episode, "has_active_embodied_developmental_capability",
          capability)
    agent.inner.set_attr(episode, "development_learning_active", 1)
    return episode, capability


def _observed(before, after):
    """The transducer's publication — link SETS, not `development_*` fields."""
    return {
        "support_contact_links_before": list(before),
        "support_contact_links_after": list(after),
        "support_contact_count_before": len(before),
        "support_contact_count_after": len(after),
        "support_contact_observed": 1,
        "integer_native": 1,
    }


def _closed_receipt_with_evidence(agent, episode, evidence_attrs):
    """A closed receipt whose support fields exist ONLY via the carry rule."""
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed",
        "development_receipt_closed": 1,
        "development_receipt_seq": 1,
        "development_external_event": 0,
        "development_experience_retained": 0,
        "development_recoverability_units": 0,
        "development_unbuffered_exposure_units": 1,
        "embodiment_destroyed": 0,
        "causal_closed": 1, "grounded": 1,
        "integer_native": 1, "output_authority": 0,
    })
    evidence = agent.s.add_node("EmbodiedExternalTrialEvidence", evidence_attrs)
    _edge(agent, receipt, "grounded_in_external_trial_evidence", evidence)
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 1)
    return receipt


# --------------------------------------------------------------- the control

def test_a_PRE_WRITTEN_topology_change_is_credited():
    """Isolates ordering from the predicate. If the field is already on the
    receipt when the credit rule first sees it, the success MUST be booked —
    otherwise the criterion itself is broken and the race is not the story."""
    agent = _agent()
    episode, capability = _episode_with_active_capability(
        agent, "support_topology_change")
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed",
        "development_receipt_closed": 1,
        "development_receipt_seq": 1,
        "development_support_topology_changed": 1,
        "development_support_observed": 1,
        "development_post_support_count": 1,
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
    agent.inner.run_rules()

    attrs = agent.s.node(capability)["attrs"]
    assert attrs["attempt_count"] == 1
    assert attrs["success_count"] == 1, (
        "the criterion cannot read a field that is plainly there: "
        f"{attrs}")


# -------------------------------------------------------------- the headline

@BOTH_ORDERS
def test_a_CARRIED_topology_change_is_credited_in_the_SAME_fixpoint(order):
    """THE HEADLINE. The evidence says the topology changed; nothing writes the
    `development_*` field but the carry rule. If the credit rule consumes the
    receipt first, the field lands on an already-scored failure and the
    capability never moves — 145 observed changes in ordinal 3's window, 0
    successes. Both registration orders must give the same answer."""
    agent = _agent(order)
    episode, capability = _episode_with_active_capability(
        agent, "support_topology_change")
    receipt = _closed_receipt_with_evidence(
        agent, episode, _observed((3, 7), (3,)))
    agent.inner.run_rules()

    carried = agent.s.node(receipt)["attrs"]
    credited = agent.s.node(capability)["attrs"]
    assert carried.get("development_support_topology_changed") == 1, (
        "the carry rule did not run at all — different failure, read it first")
    assert credited["attempt_count"] == 1
    assert credited["success_count"] == 1, (
        "THE RACE: the receipt now carries a topology change the capability was "
        "never credited for. attempt/success/failure = "
        f"{credited['attempt_count']}/{credited['success_count']}/"
        f"{credited['failure_count']}")


@BOTH_ORDERS
def test_the_receipt_cannot_be_re_credited_once_consumed(order):
    """Why losing the race is fatal rather than merely late: the credit rule
    raises `last_receipt_seq` past this receipt, so no later fixpoint can
    revisit it. A value that arrives after consumption is lost permanently —
    which is why re-running to convergence does not heal the live run."""
    agent = _agent(order)
    episode, capability = _episode_with_active_capability(
        agent, "support_topology_change")
    receipt = _closed_receipt_with_evidence(
        agent, episode, _observed((3, 7), (3,)))
    for _ in range(5):
        agent.inner.run_rules()

    credited = agent.s.node(capability)["attrs"]
    assert credited["attempt_count"] == 1, (
        "the receipt was consumed more than once — the seq guard is not doing "
        f"what this test assumes: {credited}")
    assert agent.s.node(receipt)["attrs"]["development_support_topology_changed"] == 1
    assert credited["success_count"] == 1, (
        "re-running the fixpoint does not rescue it: "
        f"{credited}")


@BOTH_ORDERS
def test_an_UNMEASURED_trial_is_counted_apart_from_a_FAILED_one(order):
    """The repair must not trade one silence for another. A capability whose
    channel is written by nothing now DECLINES rather than booking fabricated
    failures — so it must say so, or a dark channel merely stops looking like
    failure and starts looking like "not started yet".

    The first receipt carries no evidence at all and is then superseded by a
    second, which is what proves its chance has passed rather than merely not
    arrived."""
    agent = _agent(order)
    episode, capability = _episode_with_active_capability(
        agent, "support_topology_change")
    blind = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "development_receipt_closed": 1,
        "development_receipt_seq": 1, "causal_closed": 1, "grounded": 1,
        "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, episode, "has_embodied_development_receipt", blind)
    later = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "development_receipt_closed": 1,
        "development_receipt_seq": 2, "causal_closed": 1, "grounded": 1,
        "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, episode, "has_embodied_development_receipt", later)
    agent.inner.set_attr(episode, "latest_development_receipt_seq", 2)
    agent.inner.run_rules()

    attrs = agent.s.node(capability)["attrs"]
    assert attrs["attempt_count"] == 0, (
        "an unmeasured trial was scored as an attempt — this is the flat-zero "
        f"pathology the guard exists to remove: {attrs}")
    assert attrs["failure_count"] == 0
    assert attrs.get("unmeasured_receipt_count") == 1, (
        f"declining was silent instead of loud: {attrs}")
    assert attrs.get("measurement_blocked_on") == "support_topology_change"


def test_every_criterion_kind_carries_a_readiness_guard():
    """The anti-drift invariant, asserted on the DERIVATION rather than on a
    hand-kept list: readiness is read out of `capability_success()`'s own term
    tree, so a criterion cannot acquire a receipt field and forget to guard it.
    If these two ever fall out of correspondence, there are two of them."""
    from scripts.gen_embodied_development_seed import (      # noqa: E402
        capability_measurement_declared, capability_success)

    criterion_kinds = [branch["items"][0]["b"]["value"]
                       for branch in capability_success()["items"]]
    readiness_kinds = [branch["items"][0]["b"]["value"]
                       if branch.get("type") == "And" else branch["b"]["value"]
                       for branch in capability_measurement_declared()["items"]]
    assert readiness_kinds == criterion_kinds
    assert len(set(criterion_kinds)) == len(criterion_kinds)


def test_a_disjunctive_criterion_is_not_made_STRICTER_by_its_guard():
    """Readiness mirrors the criterion's boolean structure. `supported_half_turn`
    succeeds on the receipt's `half_turn_transition` OR on the instance's own
    `trajectory_half_turn_complete`, so requiring the receipt field would refuse
    trials the criterion accepts. A guard that changes which trials pass is not
    a guard, it is a new criterion."""
    from scripts.gen_embodied_development_seed import (      # noqa: E402
        _readiness, capability_success)
    from scripts.gen_humanoid_adaptation_seed import And as _And   # noqa: E402

    def required(term, out=None):
        out = [] if out is None else out
        if isinstance(term, dict):
            if (term.get("type") == "Eq"
                    and isinstance(term.get("b"), dict)
                    and term["b"].get("value") is None
                    and term.get("a", {}).get("type") == "Attr"):
                out.append(term["a"]["key"])
            for value in term.values():
                required(value, out)
        elif isinstance(term, list):
            for item in term:
                required(item, out)
        return out

    branches = {b["items"][0]["b"]["value"]: b for b in capability_success()["items"]}
    ready = _readiness(_And(*branches["supported_half_turn"]["items"][1:]), "receipt")
    keys = required(ready)
    assert "development_post_support_count" in keys, (
        "the conjunctive half of the criterion still needs its measurement")
    assert "development_half_turn_transition" not in keys, (
        "the disjunction was flattened — the guard is now stricter than the "
        f"criterion it guards: {keys}")


@BOTH_ORDERS
def test_a_stable_topology_is_still_a_real_failure(order):
    """The other side of the control: an OBSERVED unchanged topology is a
    genuine failure, not a lost measurement. This must stay at 0 successes
    under any fix — a repair that simply credits everything is not a repair."""
    agent = _agent(order)
    episode, capability = _episode_with_active_capability(
        agent, "support_topology_change")
    receipt = _closed_receipt_with_evidence(
        agent, episode, _observed((3, 7), (3, 7)))
    agent.inner.run_rules()

    assert agent.s.node(receipt)["attrs"]["development_support_topology_changed"] == 0
    credited = agent.s.node(capability)["attrs"]
    assert credited["attempt_count"] == 1
    assert credited["success_count"] == 0
    assert credited["failure_count"] == 1
