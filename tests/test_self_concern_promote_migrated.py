"""Phase 3 continuation: chat self-concerns become actionable, HUMAN-GATED.

A self-directed chat instruction files a SelfConcern (status 'noted'); the
daemon exposes list + promote functions so a human can PROMOTE one into the
agent's existing (already-safety-gated) self-improvement pipeline -- minting a
StandingConcern{status:'pending'} the _concern_tick hook processes. This gates
self-modification behind an explicit human action; nothing auto-promotes.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

jd = pytest.importorskip("jabberwock_daemon")


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _promoted_standing(a):
    return [n for n in a.s.nodes("StandingConcern")
            if a.s.node(n)["attrs"].get("source") == "conversation_promoted"
            and a.s.node(n)["attrs"].get("status") == "pending"]


def test_list_and_human_gated_promote(agent):
    agent.converse("Fix your grammar.", speech_act="request")   # 'grammar' is held -> confident -> files a concern
    scs = jd.list_self_concerns(agent)
    assert scs, "a confident self-directed instruction must file a listable self-concern"
    noted = [c for c in scs if c["status"] == "noted"]
    assert noted, "the filed concern is 'noted' (not auto-promoted)"
    c = noted[0]

    before = len(_promoted_standing(agent))
    res = jd.promote_self_concern(agent, str(c["id"]))
    assert res["ok"] and res.get("standing_concern"), "human-gated promote must succeed"

    after = _promoted_standing(agent)
    assert len(after) == before + 1, (
        "promotion must mint a pending StandingConcern -- the handoff into the "
        "existing (gated) self-improvement pipeline the _concern_tick hook runs")

    scs2 = {x["id"]: x for x in jd.list_self_concerns(agent)}
    assert scs2[c["id"]]["status"] == "promoted"
    assert scs2[c["id"]]["promoted_to"], "the concern must link to its StandingConcern"

    res2 = jd.promote_self_concern(agent, str(c["id"]))
    assert not res2["ok"], "promotion must be idempotent (no double-promote)"


def test_filing_a_concern_does_not_auto_promote(agent):
    before = len(_promoted_standing(agent))
    agent.converse("Improve your reading.", speech_act="request")   # confident (reading is held)
    after = len(_promoted_standing(agent))
    assert after == before, (
        "filing a self-concern must NOT create a pending StandingConcern on its "
        "own -- self-modification requires an explicit human promote")


# --- seed-on-resume reconciliation (the checkpoint-staleness fix) ---------

def test_seed_rule_reconciliation_installs_missing_rules_exactly_once():
    # A minimal boot (CORE_SEEDS) lacks the conversation-migration rules --
    # the same situation a checkpoint saved before those seeds existed is in.
    a = WorldAdapter()
    names0 = [r.get("name") for r in a.inner.export_rules()]
    assert "comprehend_read_instruction" not in names0, "precondition: rule absent on a minimal boot"

    added = jd._reconcile_seed_rules(a)
    assert added > 0, "reconciliation must install the missing seed rules"
    names1 = [r.get("name") for r in a.inner.export_rules()]
    assert "comprehend_read_instruction" in names1
    assert names1.count("comprehend_read_instruction") == 1, "installed exactly once (no duplicate)"
    assert "instruction_world_action_floor" in names1
    assert "mint_self_improvement_concern_confident" in names1
    assert "ask_clarification_self_improvement" in names1

    # Idempotent: a second reconciliation adds nothing and never duplicates.
    added2 = jd._reconcile_seed_rules(a)
    assert added2 == 0, "reconciliation must be idempotent on a reconciled graph"
    names2 = [r.get("name") for r in a.inner.export_rules()]
    assert names2.count("comprehend_read_instruction") == 1


def test_seed_rule_reconciliation_refreshes_a_changed_rule_body_leak_free():
    # The durable fix: a seed rule whose BODY changed since the checkpoint (an
    # EDIT to an existing rule -- e.g. a new where-guard) is REFRESHED on resume,
    # and an UNCHANGED rule is never churned (leak-free).
    import glob
    import json
    import os
    from substrate.seed_loader import SEED_DIR

    a = WorldAdapter()
    jd._reconcile_seed_rules(a)                       # install all current seed rules

    # Leak-free: a second pass on the just-reconciled graph refreshes nothing.
    assert jd._reconcile_seed_rules(a) == 0, "unchanged rules must not be churned (no tombstone leak)"

    # Pick a real seed rule and install a STALE variant (drop its last where-item)
    # under the same name, simulating a checkpoint saved before the rule was edited.
    seed = json.load(open(os.path.join(str(SEED_DIR), "gap_awareness.json")))
    target = next(r for r in seed["rules"] if r["name"] == "note_unresolved_topic_gap")
    stale = json.loads(json.dumps(target))
    stale["where"]["items"] = stale["where"]["items"][:-1]   # a genuinely different body
    assert jd._canon_rule_body(stale) != jd._canon_rule_body(target), "precondition: bodies differ"

    # Remove the current one and install the stale body in its place.
    for i, r in enumerate(a.inner.export_rules()):
        if r.get("active") and r.get("name") == "note_unresolved_topic_gap":
            a.inner.remove_rule(i)
    a.inner.load_seed_manifest({"id": "gap_awareness", "rules": [stale]}, a.agent)

    # Reconcile -> detects the body diff -> refreshes to the FILE version.
    n = jd._reconcile_seed_rules(a)
    assert n >= 1, "a changed rule body must be refreshed from the seed file"
    live = [r for r in a.inner.export_rules()
            if r.get("active") and r.get("name") == "note_unresolved_topic_gap"]
    assert len(live) == 1, "exactly one active copy after refresh"
    assert jd._canon_rule_body(live[0]) == jd._canon_rule_body(target), (
        "the active rule body must now match the seed file")


def test_seed_concept_reconciliation_installs_missing_concepts_by_name():
    # gap_awareness ships Concept nodes (the deficiency cues) its explicit-report
    # rule depends on for recognition; a checkpoint saved before that seed lacks
    # them, and _reconcile_seed_rules is rules-only -- so the concepts must be
    # reconciled or note_reported_gap can never match on a resumed agent.
    a = WorldAdapter()

    def _held():
        return {a.s.node(c)["attrs"].get("name") for c in a.s.nodes("Concept")}

    assert "cannot" not in _held(), "precondition: the deficiency concept is absent on a minimal boot"

    added = jd._reconcile_seed_concepts(a)
    assert added > 0, "reconciliation must install the missing seed concepts"
    held = _held()
    for name in ("cannot", "gap", "limitation", "stuck"):
        assert name in held, f"deficiency concept {name!r} must be installed"

    # Idempotent + name-guarded: a second pass adds nothing, no duplicate node.
    added2 = jd._reconcile_seed_concepts(a)
    assert added2 == 0, "concept reconciliation must be idempotent"
    names = [a.s.node(c)["attrs"].get("name") for c in a.s.nodes("Concept")]
    assert names.count("cannot") == 1, "no duplicate Concept node"


# --- NL -> directed experiment (the request steers which subsystem is tested) --

def test_promotion_directs_the_experiment_at_the_request_content(agent):
    import domains.reflective_faculty as rf

    agent.converse("Fix your grammar.", speech_act="request")   # confident -> files a concern about 'grammar'
    noted = [c for c in jd.list_self_concerns(agent) if c["status"] == "noted"]
    assert noted
    res = jd.promote_self_concern(agent, str(noted[0]["id"]))
    assert res["ok"]
    assert "grammar" in (res.get("target_words") or []), "the request content is captured"

    # the promoted StandingConcern carries the content word as a relation HEAD
    # (alongside the proven cue heads), so it becomes a residual_predicate.
    standing = [n for n in agent.s.nodes("StandingConcern")
                if agent.s.node(n)["attrs"].get("source") == "conversation_promoted"][-1]
    rels = [list(r) for r in (agent.s.node(standing)["attrs"].get("relations") or [])]
    heads = {r[0] for r in rels if r}
    assert "grammar" in heads, "content word must be a relation head"
    assert {"test", "vary", "send", "judge", "gradient", "adopt"} <= heads, "proven cue heads remain"

    # THE DIRECTION LEVER: inducing the concern mints an axis whose
    # residual_predicates include the request content -- the exact text the
    # composer's vary/acting-variant Argmax overlaps against each seed's
    # keywords_text to pick WHICH subsystem to experiment on.
    ind = rf.induce_concern(agent, rels, name_hint="probe_directed_grammar")
    preds = ind.get("residual_predicates") or []
    assert "grammar" in preds, (
        "the request content must reach residual_predicates -- the lever that "
        "steers the experiment's vary/acting-variant seed selection")
