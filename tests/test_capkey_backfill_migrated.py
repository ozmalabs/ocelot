"""Wave 5, task 3: the CapKey LOAD-TIME BACKFILL — the self-extension spec's
named open seam (docs/jabberwock_self_extension_spec.md: seeds/primitives
declaring `capability_keys` list-attrs get CapKey nodes + provides_key edges
minted at seed load, find-or-create, idempotent), plus the resumed-daemon
reconcile (`jabberwock_daemon._reconcile_seed_capkeys`, the
_reconcile_seed_typed_nodes precedent).

The point of the seam (gated below): `compose_from_held_primitives`'
coverage JOIN (seeds/self_extension.json: axis -requires_key-> k
<-provides_key- p) now sees keys from OUTSIDE self_extension.json's own
hand-wired fixtures — the session seeds (speech_act_classify,
conversation_steering, conversation_experiment, gap_awareness,
comprehend_instruction, conversation_self_concern, variation_ops) declare
top-level `capability_keys`, and their SeedSummary provenance nodes become
the providers the compose rules assemble from.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

jd = pytest.importorskip("jabberwock_daemon")

_DECLARED = {
    "speech_act_classify": "classify_speech_act",
    "conversation_steering": "steer_gap_pipeline",
    "conversation_experiment": "conversation_replay_experiment",
    "gap_awareness": "gap_detection",
    "comprehend_instruction": "route_instruction",
    "conversation_self_concern": "self_improvement_concern",
    "variation_ops": "cue_set_edit",
}


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _capkey(a, name):
    for n in a.s.nodes("CapKey"):
        if a.s.node(n)["attrs"].get("name") == name:
            return n
    return None


def _summary(a, sid):
    for n in a.s.nodes("SeedSummary"):
        if a.s.node(n)["attrs"].get("seed_id") == sid:
            return n
    return None


def test_boot_backfills_declared_seed_capkeys(agent):
    for sid, key in _DECLARED.items():
        ck = _capkey(agent, key)
        assert ck is not None, f"CapKey {key!r} (declared by seed {sid!r}) must be minted at boot"
        summary = _summary(agent, sid)
        assert summary is not None, f"SeedSummary for {sid!r} must exist"
        assert ck in agent.inner.neighbours(summary, "provides_key"), (
            f"SeedSummary({sid}) -provides_key-> CapKey({key}) must be wired at load time")
    # interned: one CapKey node per name (find-or-create, never duplicated)
    names = [agent.s.node(n)["attrs"].get("name") for n in agent.s.nodes("CapKey")]
    assert len(names) == len(set(names)), "CapKey nodes must be interned by name"


def test_compose_join_sees_keys_from_outside_self_extension(agent):
    """The spec's gate: a needs_tool impasse whose axis requires a key one of
    the SESSION seeds provides composes from that provider — the join works on
    keys minted by the backfill, not just self_extension.json's fixtures."""
    agent.wire_self_extension()          # load the compose rules (idempotent)
    ck = _capkey(agent, "route_instruction")
    assert ck is not None
    ax = agent.s.add_node("CapabilityAxis", {"is_axis": 1.0, "name": "capkey_join_gate"})
    agent.inner.add_edge_unchecked(ax, "requires_key", ck)
    mi = agent.s.add_node("Impasse", {"order": 4, "kind": "escalation"})
    agent.inner.add_edge_unchecked(mi, "needs_tool", ax)
    agent.inner.run_rules(60000)

    cops = [o for o in agent.inner.neighbours(ax, "investigated_by")
            if agent.s.has_node(o) and agent.s.node(o)["attrs"].get("composed") == 1]
    assert cops, "compose_from_held_primitives must mint a composed Operator for the coverable key"
    providers = [p for p in agent.inner.neighbours(cops[0], "composed_from") if agent.s.has_node(p)]
    summary = _summary(agent, "comprehend_instruction")
    assert summary in providers, (
        "the composed operator must be wired composed_from the comprehend_instruction "
        "SeedSummary — a provider from OUTSIDE self_extension.json")
    assert ck in agent.inner.neighbours(ax, "covered_key"), "the join must mark the key covered"


def test_reconcile_capkeys_is_idempotent_on_a_minimal_agent():
    """The resumed-daemon path: a checkpoint-shaped agent (core seeds only, no
    SeedSummary/CapKey backfill) gets the join reconciled exactly once."""
    a = WorldAdapter()
    assert _capkey(a, "route_instruction") is None, "precondition: minimal agent lacks the backfill"
    added = jd._reconcile_seed_capkeys(a)
    assert added > 0
    ck = _capkey(a, "route_instruction")
    assert ck is not None
    summary = _summary(a, "comprehend_instruction")
    assert summary is not None and ck in a.inner.neighbours(summary, "provides_key")
    assert jd._reconcile_seed_capkeys(a) == 0, "second reconcile adds nothing (edge-once)"
