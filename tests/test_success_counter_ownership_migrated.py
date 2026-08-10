"""ONE COUNTER, ONE MEANING — the migrated gate.

Measured from growth9's final checkpoint (2026-08-07): `spontaneous_general_movement`
carried `success_count == 200` against `attempt_count == 147`. A success count
larger than the attempt count is arithmetically impossible for
`ed_learn_capability_from_causally_closed_receipt`, which books `attempt += 1` and
`success += 0|1` in ONE effect — so a second writer had to exist, and it did:

    ed_learn_capability_from_causally_closed_receipt   ->  27   (criterion met)
    els_count_positive_receipt_as_capability_success   -> 173   (world measured progress)
                                                          ---
                                                          200

Counted independently on the plan step, which evaluates the SAME criterion on the
SAME receipts, the honest tally was 27 successes / 120 failures = 147 attempts,
which reconciles exactly. 200 + 120 = 320 does not.

The two writers were not duplicates — they were two DIFFERENT FACTS sharing an
attribute. "The world measured positive goal progress on this trial" and "this
capability's developmental criterion was satisfied" are independent claims, and
`success_count` is what MASTERY and RETENTION are judged on. Ordinal 0 — the only
mastery this line has produced — was declared off the inflated figure.

So the notions are separated at the source: measured progress accumulates into
`positive_progress_count`, which mission confirmation reads (it was always a delta
test over that notion, not over the criterion); `success_count` is left owned by
the developmental criterion alone.

The rule NAME is deliberately unchanged even though the attribute is not, because
`_reconcile_seed_rules` refreshes by name and installs an unknown name additively
— a rename would leave the old body live on every resumed daemon and have both
increment on the same evidence, reintroducing the double-count.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import json                                            # noqa: E402
from pathlib import Path                               # noqa: E402

from substrate.world_adapter import WorldAdapter       # noqa: E402
from substrate.seed_loader import manifest_for         # noqa: E402

SEEDS = Path(__file__).resolve().parents[1] / "seeds"


def _writers_of(attr):
    """Every rule in the embodied seeds that SETS `attr`, by seed."""
    found = []
    for name in ("embodied_learning_session", "embodied_development",
                 "embodied_instruction_goal"):
        manifest = json.loads((SEEDS / f"{name}.json").read_text(encoding="utf-8"))
        for rule in manifest.get("rules", []):
            for effect in rule.get("effects") or []:
                if (isinstance(effect, list) and len(effect) >= 3
                        and effect[0] == "set_attr" and effect[2] == attr):
                    found.append((name, rule["name"]))
    return found


# ------------------------------------------------------ ownership, on the seed

def test_success_count_is_owned_by_the_developmental_criterion_alone():
    """THE HEADLINE, asserted where the defect lived. Every writer of
    `success_count` must be a developmental-criterion rule; a writer from the
    session layer is the double-count returning."""
    writers = _writers_of("success_count")
    assert writers, "no writer found at all — the attribute was renamed away"
    foreign = [(seed, rule) for seed, rule in writers
               if seed != "embodied_development"]
    assert not foreign, (
        "a non-criterion rule writes the attribute mastery is judged on: "
        f"{foreign}")


def test_measured_progress_has_a_counter_of_its_own():
    writers = _writers_of("positive_progress_count")
    assert ("embodied_learning_session",
            "els_count_positive_receipt_as_capability_success") in writers


def test_mission_confirmation_reads_progress_not_the_criterion():
    """Mission confirmation was always a DELTA test over measured progress — it
    snapshots a baseline and requires the count to exceed it. That is the
    progress notion, so it must read the progress counter; leaving it on
    `success_count` would silently re-couple the two."""
    manifest = json.loads(
        (SEEDS / "embodied_instruction_goal.json").read_text(encoding="utf-8"))
    rules = {rule["name"]: json.dumps(rule) for rule in manifest["rules"]}
    confirm = rules["eig_confirm_goal_only_from_later_closed_embodied_receipt"]
    assert "positive_progress_count" in confirm
    assert "baseline_positive_progress_units" in confirm
    assert "success_count" not in confirm, (
        "mission confirmation still reads the criterion counter")
    opened = rules["eig_open_receipt_confirmation_for_proposed_humanoid_goal"]
    assert "baseline_positive_progress_units" in opened
    assert "success_count" not in opened, (
        "the baseline is snapshotted off the criterion counter, so the delta "
        "test spans two different notions")


# --------------------------------------------------------- ownership, in a graph

def _agent():
    agent = WorldAdapter()
    for seed in ("counterfactual_experiment", "embodied_learning_session",
                 "embodied_development"):
        agent.inner.load_seed_manifest(manifest_for(seed), agent.agent)
    return agent


def test_measured_progress_does_not_move_the_criterion_counter():
    """The live half: publish developmental evidence carrying the world's own
    positive progress and confirm it lands in the progress counter WITHOUT
    touching the counter mastery reads."""
    agent = _agent()
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability",
        {"success_count": 0, "attempt_count": 0, "failure_count": 0,
         "last_receipt_seq": 0, "activation_receipt_seq": 0,
         "evidence_kind": "support_topology_change"})
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "development_receipt_closed": 1,
        "development_receipt_seq": 1, "integer_native": 1})
    evidence = agent.s.add_node("EmbodiedDevelopmentalEvidence", {
        "kind": "grounded_external_trial", "success_units": 1,
        "progress_units": 1, "receipt_seq": 1,
        "grounded": 1, "integer_native": 1, "output_authority": 0})
    agent.inner.add_edge_unchecked(
        capability, "has_embodied_developmental_evidence", evidence)
    agent.inner.add_edge_unchecked(evidence, "grounded_in_causal_receipt", receipt)
    agent.inner.run_rules()

    attrs = agent.s.node(capability)["attrs"]
    assert attrs.get("positive_progress_count") == 1, (
        f"measured progress was not counted: {attrs}")
    assert attrs["success_count"] == 0, (
        "measured progress inflated the criterion counter — this is the exact "
        f"defect that put ordinal 0's mastery on a false number: {attrs}")


def test_the_progress_counter_advances_once_per_evidence_node():
    """The once-guard survives the split: re-running the fixpoint must not
    re-count the same evidence."""
    agent = _agent()
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability",
        {"success_count": 0, "attempt_count": 0, "failure_count": 0,
         "last_receipt_seq": 0, "activation_receipt_seq": 0,
         "evidence_kind": "support_topology_change"})
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "development_receipt_closed": 1,
        "development_receipt_seq": 1, "integer_native": 1})
    evidence = agent.s.add_node("EmbodiedDevelopmentalEvidence", {
        "kind": "grounded_external_trial", "success_units": 1,
        "progress_units": 1, "receipt_seq": 1,
        "grounded": 1, "integer_native": 1, "output_authority": 0})
    agent.inner.add_edge_unchecked(
        capability, "has_embodied_developmental_evidence", evidence)
    agent.inner.add_edge_unchecked(evidence, "grounded_in_causal_receipt", receipt)
    for _ in range(4):
        agent.inner.run_rules()

    assert agent.s.node(capability)["attrs"].get("positive_progress_count") == 1
