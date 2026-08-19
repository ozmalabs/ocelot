"""GATE for domains/commitment_gate.py — the GENERAL commit-vs-explore gate
that generalizes the fold_clock_edge (reversible run_rules fixpoint vs the
lawful non-monotone "tock") distinction, and proposal_install.py's bespoke
rung-4 install gate, into declarative frame data
(seeds/reversibility_frame.json) plus one reusable `commit_gate` function.

Honest accounting of what runs LIVE vs MOCKED, mirroring tests/test_proposal_
install.py's own convention:

  LIVE, real substrate_rs: every node/edge/attr read+write in this file is a
      real `Substrate()` — no graph-layer mocking anywhere.

  MOCKED (allow-side subsumption test only): `domains.proposal_install.ser.
      validate_spec`, `.render_spec`, and `.PrimitiveExtension` — exactly the
      same three seams tests/test_proposal_install.py's own test_b mocks, for
      the same reason: proving an ALLOWED decision without ever invoking a
      real cargo/maturin build. Every other test in this file calls
      `commit_gate` and (where used) the real, unmocked `install_proposal`
      on cheap, read-only-refusal paths (status != validated), which never
      reach cargo/maturin at all — see test_proposal_install.py's own test_c
      for the precedent that this path is genuinely free to call live.

Nothing in this file performs a real external/irreversible action: no HTTP
call, no browser session, no ARC world, no voice output, no real install. The
GATE is what is tested, never the gated action itself.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs                                # noqa: E402
from domains import commitment_gate as cg                 # noqa: E402
from domains import proposal_install as pinstall           # noqa: E402


def _risk(*, goal=1.0, requires_approval=0.0):
    tube = [{"time": t, "cells": {"core": {"weight": 1, "information": 0, "metadata": {}}}, "links": []} for t in range(3)]
    projection = {"manifold_id": "m1", "projected_tube": tube,
                  "action_count": 0, "intervention_magnitude": 0}
    return {
        "manifold": {"manifold_id": "m1", "required_horizon": 2,
                      "minimum_width": 1, "maximum_information_loss": 0,
                      "required_tube": tube},
        "commit": {"name": "commit", "expected_goal_work": goal,
                   "requires_approval": requires_approval,
                   "projection": projection},
        "wait": {"name": "wait", "delay_cost": 1.0,
                 "projection": projection},
        "refine": {"name": "refine", "refinement_cost": 2.0,
                   "projection": projection},
    }


# ---------------------------------------------------------------------------
# (a) frame data / classification
# ---------------------------------------------------------------------------

def test_classification_table_has_both_categories_and_the_archetype():
    rows = cg.classification_table()
    kinds = {r["kind"]: r for r in rows}
    assert kinds["add_node"]["category"] == "reversible"
    assert kinds["set_attr"]["category"] == "reversible"
    assert kinds["del_node"]["category"] == "committing"
    assert kinds["del_edge"]["category"] == "committing"
    assert kinds["fold_clock_edge"]["category"] == "committing"
    assert kinds["fold_clock_edge"]["archetype"] is True
    assert kinds["runtime_install"]["category"] == "committing"
    assert kinds["http_get"]["category"] == "committing"
    assert kinds["browser_apply"]["category"] == "committing"
    assert kinds["arc_apply"]["category"] == "committing"
    assert kinds["voice_emit"]["category"] == "committing"
    assert kinds["teach_to_disk"]["category"] == "committing"
    assert kinds["checkpoint_overwrite"]["category"] == "committing"
    # every row has a non-trivial reason (documented rationale, not a stub).
    assert all(len(r["reason"]) > 20 for r in rows)


def test_classify_unknown_kind_fails_closed_committing():
    detail = cg.classify_detail("some_kind_never_seen_before")
    assert detail["category"] == "committing"
    assert detail["known"] is False
    assert cg.classify("some_kind_never_seen_before") == "committing"


# ---------------------------------------------------------------------------
# (b1) reversible action passes freely, no approval, no record
# ---------------------------------------------------------------------------

def test_reversible_action_passes_free_no_record():
    s = srs.Substrate()
    result = cg.commit_gate(s, {"kind": "add_node"})
    assert result == {
        "allowed": True, "reversible": True, "kind": "add_node",
        "reason": result["reason"], "requires_approval": False,
        "gated": False, "record": None,
    }
    # no Commitment node type even exists yet -- nothing was minted.
    assert _commitment_nodes(s) == []


def test_reversible_action_bare_string_kind_also_works():
    s = srs.Substrate()
    result = cg.commit_gate(s, "set_attr")
    assert result["allowed"] is True
    assert result["reversible"] is True
    assert result["gated"] is False


# ---------------------------------------------------------------------------
# (b2) committing action gated: refused without policy/approver
# ---------------------------------------------------------------------------

def test_committing_action_refused_with_no_approver():
    s = srs.Substrate()
    result = cg.commit_gate(s, {"kind": "del_node", "risk": _risk()})
    assert result["allowed"] is False
    assert result["reversible"] is False
    assert result["gated"] is True
    assert "approver" in result["reason"]
    # a refusal IS a decision on a committing action -- record minted.
    assert result["record"] is not None
    rec = s.node(result["record"])["attrs"]
    assert rec["action"] == "del_node"
    assert rec["allowed"] is False
    assert rec["reversible"] is False


def test_committing_action_refused_by_denylist_even_with_approver():
    s = srs.Substrate()
    result = cg.commit_gate(s, {"kind": "del_node", "risk": _risk()}, approver="pytest",
                             policy={"denylist": ["del_node"]})
    assert result["allowed"] is False
    assert "denylist" in result["reason"]


def test_committing_action_allowed_under_explicit_policy():
    s = srs.Substrate()
    result = cg.commit_gate(s, {"kind": "del_node", "risk": _risk()}, approver="pytest",
                             policy={"allowlist": ["del_node"]})
    assert result["allowed"] is True
    assert result["gated"] is True
    assert result["record"] is not None
    rec = s.node(result["record"])["attrs"]
    assert rec["allowed"] is True
    assert rec["approver"] == "pytest"


def test_external_action_kinds_are_gated_committing():
    """browser apply / ARC apply / http fetch / voice emit / runtime install
    all classify committing and are refused with no approver -- proves the
    frame data actually covers the world-adapter external-action surface the
    task calls out, not just the in-graph effect kinds."""
    s = srs.Substrate()
    for kind in ("browser_apply", "arc_apply", "http_get", "voice_emit"):
        result = cg.commit_gate(s, {"kind": kind, "risk": _risk()})
        assert result["allowed"] is False, f"{kind} should be refused with no approver"
        assert result["reversible"] is False, f"{kind} should classify committing"


# ---------------------------------------------------------------------------
# (c) SUBSUMPTION — commit_gate's runtime_install decision == install_
#     proposal's own decision, on both an allowed and a refused case.
# ---------------------------------------------------------------------------

def _spec_and_proposal(s, *, status: str, installed: bool = False, name="Demo"):
    spec_id = s.add_node("RustExtensionSpec", {
        "name": name, "semantics_kind": "graph_reachability",
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
        "compiled": status == "validated", "stage": "cargo_check",
        "errors": "" if status == "validated" else "E0425", "origin": "test",
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": name, "status": status, "installed": installed,
        "requires_restart": True, "seconds": 1.0, "sandbox": "", "ts": time.time(),
    })
    s._inner.add_edge_unchecked(prop_id, "validates", spec_id)
    return prop_id


def test_c_subsumption_deny_case_matches_install_proposal(monkeypatch):
    s = srs.Substrate()
    prop_id = _spec_and_proposal(s, status="failed")

    def _boom(*a, **k):
        raise AssertionError("must not construct PrimitiveExtension for a failed proposal")
    monkeypatch.setattr(pinstall, "PrimitiveExtension", _boom)

    gate_result = cg.commit_gate(s, {"kind": "runtime_install", "proposal_id": prop_id, "risk": _risk()},
                                  approver="pytest")
    oracle_result = pinstall.install_proposal(s, prop_id, approver="pytest")

    assert gate_result["allowed"] is False
    assert oracle_result["ok"] is False
    # same underlying reason (status check), not just "both False" by luck.
    assert gate_result["reason"] == oracle_result["reason"] == "status is 'failed', not 'validated'"


def test_c_subsumption_allow_case_matches_install_proposal(monkeypatch):
    s = srs.Substrate()
    prop_id = _spec_and_proposal(s, status="validated")

    # Mock exactly the seams test_proposal_install.py's own test_b mocks, so
    # the oracle call below never reaches cargo/maturin.
    monkeypatch.setattr(pinstall.ser, "validate_spec",
                        lambda substrate, spec, **kw: {"ok": True, "stage": "cargo_check"})
    monkeypatch.setattr(pinstall.ser, "render_spec",
                        lambda spec: {"term.rs (some arm)": "// harmless"})

    class _FakeExtension:
        def extend(self, spec, anchor_spec=None, *, build=True, revert_after=False):
            return {"ok": True, "stage": "rebuild", "built": True, "files": ["term.rs"]}

    monkeypatch.setattr(pinstall, "PrimitiveExtension", _FakeExtension)
    # install_proposal's success path calls teach(agent, "TaughtHint", ...,
    # category="runtime_extensions") -- that would really write
    # seeds/runtime_extensions.json to disk (teach()'s SAVE half, see
    # CLAUDE.md's teach facility) and expects an `agent.s` attribute a raw
    # Substrate doesn't have. Neither belongs in this test (the gate is what
    # is under test, not teach()'s disk persistence, and the CAUTIONS forbid
    # a real disk write here) -- stub it to a no-op recorder.
    taught = []
    monkeypatch.setattr(pinstall, "teach",
                        lambda agent, type_, attrs, **kw: taught.append((type_, attrs)))

    gate_result = cg.commit_gate(s, {"kind": "runtime_install", "proposal_id": prop_id, "risk": _risk()},
                                  approver="pytest")
    oracle_result = pinstall.install_proposal(s, prop_id, approver="pytest")

    assert gate_result["allowed"] is True
    assert oracle_result["ok"] is True
    assert oracle_result["installed"] is True


def test_c_subsumption_already_installed_matches_install_proposal():
    s = srs.Substrate()
    prop_id = _spec_and_proposal(s, status="validated", installed=True)

    gate_result = cg.commit_gate(s, {"kind": "runtime_install", "proposal_id": prop_id, "risk": _risk()},
                                  approver="pytest")
    oracle_result = pinstall.install_proposal(s, prop_id, approver="pytest")

    assert gate_result["allowed"] is False
    assert oracle_result["ok"] is False
    assert gate_result["reason"] == "already installed"
    assert oracle_result["reason"] == "already installed"


# ---------------------------------------------------------------------------
# (d) discriminative: a mis-declared "reversible" kind that is actually
#     external is caught, or is honestly documented as relying on the frame
#     being correct (there is no way to catch this from INSIDE the gate --
#     it has no way to inspect what an action kind string "really" does).
# ---------------------------------------------------------------------------

def test_d_mis_declared_kind_relies_on_frame_correctness_documented():
    """The gate has no oracle for "is this kind's frame entry honest" -- it
    is pure data lookup. Demonstrate the failure mode explicitly: an
    external effector that a caller mis-registers under a reversible kind
    name (e.g. calling http_get 'add_node' by mistake) sails through
    ungated. This is not a bug in the gate; it is why the frame data must be
    reviewed like any other safety-relevant classification (same posture as
    proposal_install's ALLOWED_INSTALL_FILES denylist, which is likewise
    only as good as its own authorship). The one thing the gate DOES
    guarantee is the opposite failure mode is impossible: an UNKNOWN kind
    can never sail through, because unclassified kinds fail closed
    (test_classify_unknown_kind_fails_closed_committing, above)."""
    s = srs.Substrate()
    # a real external kind, deliberately mis-tagged by the caller as the
    # in-graph "add_node" kind name.
    result = cg.commit_gate(s, {"kind": "add_node"})
    assert result["allowed"] is True, (
        "documented limitation: the gate trusts the kind string it is given; "
        "mis-declaring an external action under a reversible kind name is a "
        "frame-authorship bug, not something the gate can detect from inside")
    # the discriminative guarantee the gate DOES provide: the correctly
    # spelled external kind is never accidentally reversible.
    real = cg.commit_gate(s, {"kind": "http_get"})
    assert real["allowed"] is False
    assert real["reversible"] is False


# ---------------------------------------------------------------------------
# (e) Commitment record minted only for a PASSED commit, never reversible
# ---------------------------------------------------------------------------

def test_e_commitment_record_only_for_passed_commit():
    s = srs.Substrate()

    # a reversible action: no record at all, ever.
    for _ in range(3):
        cg.commit_gate(s, {"kind": "add_node"})
    assert _commitment_nodes(s) == []

    # a refused committing action: a record IS minted (audit trail for the
    # refusal), but marked allowed=False -- distinguish "gated + logged" from
    # "passed".
    refused = cg.commit_gate(s, {"kind": "del_node"})
    assert refused["record"] is not None
    refused_ids_before = set(_commitment_nodes(s))

    # a passed committing action: a record is minted and marked allowed=True.
    passed = cg.commit_gate(s, {"kind": "del_node", "risk": _risk()}, approver="pytest",
                             policy={"allowlist": ["del_node"]})
    assert passed["record"] is not None
    passed_ids_after = set(_commitment_nodes(s))
    assert passed_ids_after - refused_ids_before == {passed["record"]}

    passed_rec = s.node(passed["record"])["attrs"]
    assert passed_rec["allowed"] is True
    assert passed_rec["reversible"] is False

    refused_rec = s.node(refused["record"])["attrs"]
    assert refused_rec["allowed"] is False
    assert refused_rec["reversible"] is False


def test_manifold_action_key_delegates_future_manifold_gate_and_approval_separately():
    s = srs.Substrate()
    risk = _risk(goal=100, requires_approval=1)
    result = cg.commit_gate(s, {"kind": "world_action", "risk": risk})
    assert result["decision"] == "commit"
    assert result["allowed"] is False


def test_shape_information_loss_is_not_traded_for_goal_utility():
    s = srs.Substrate()
    risk = _risk(goal=10000)
    lost_tube = list(risk["commit"]["projection"]["projected_tube"])
    lost_tube[-1] = {"time": 2, "cells": {}, "links": []}
    risk["commit"]["projection"] = dict(risk["commit"]["projection"],
                                           projected_tube=lost_tube)
    result = cg.commit_gate(s, {"kind": "world_action", "risk": risk})
    assert result["decision"] == "wait"


def test_candidate_approval_cannot_be_waived_by_outer_policy():
    s = srs.Substrate()
    risk = _risk(goal=100, requires_approval=1)

    result = cg.commit_gate(
        s, {"kind": "world_action", "risk": risk},
        policy={"require_approver": False},
    )

    assert result["decision"] == "commit"
    assert result["allowed"] is False
    assert result["reason"] == "external_approval_required"
    assert result["record"] is not None
    assert s.node(result["record"])["attrs"]["allowed"] is False

    approved = cg.commit_gate(
        s, {"kind": "world_action", "risk": risk},
        approver="pytest", policy={"require_approver": False},
    )
    assert approved["allowed"] is True


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _commitment_nodes(s) -> list:
    """Every live `Commitment` node id, or [] if the type doesn't exist yet
    in this substrate (mirrors auto_approve.py's own `_policy_nodes` --
    `nodes(type)` on a never-minted type is the thing that can raise)."""
    try:
        return [n for n in s.nodes("Commitment") if s.has_node(n)]
    except Exception:  # noqa: BLE001
        return []
