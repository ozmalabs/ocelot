#!/usr/bin/env python3
"""jabberwock_commitment_gate — demonstrator for domains/commitment_gate.py.

Prints the reversibility classification table, then runs three scenarios
against a fresh, throwaway `substrate_rs.Substrate()` (no daemon, no
checkpoint):

  1. a reversible in-graph action (add_node) -- passes free, no record.
  2. a committing action with no policy/approver (del_node) -- refused.
  3. the same committing action, approved under an explicit policy -- allowed,
     Commitment record minted.

Then demonstrates SUBSUMPTION against `domains/proposal_install.py`'s real
guardrails on a "failed" proposal (refused) -- see
`tests/test_commitment_gate.py` for the full allow-side proof too (mocked
there, since it would otherwise require a real cargo/maturin call; this
script only runs the cheap, un-mocked refusal case live).

Run: python3 scripts/jabberwock_commitment_gate.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs                                # noqa: E402
from domains import commitment_gate as cg                 # noqa: E402
from domains import proposal_install as pinstall           # noqa: E402


def print_table() -> None:
    print("=" * 78)
    print("REVERSIBILITY CLASSIFICATION TABLE")
    print("=" * 78)
    for row in cg.classification_table():
        star = "*" if row.get("archetype") else " "
        print(f"{star} {row['category']:<11} {row['kind']:<20} {row['reason'][:90]}")
    print()


def scenario_reversible() -> None:
    print("-" * 78)
    print("1) reversible action: add_node -- should pass free, no record")
    s = srs.Substrate()
    before = list(s.nodes("Commitment")) if _has_type(s, "Commitment") else []
    result = cg.commit_gate(s, {"kind": "add_node"})
    after = list(s.nodes("Commitment")) if _has_type(s, "Commitment") else []
    print(f"   result: {result}")
    assert result["allowed"] is True and result["gated"] is False and result["record"] is None
    assert len(after) == len(before)
    print("   OK: allowed, ungated, no Commitment record minted.\n")


def scenario_committing_refused() -> None:
    print("-" * 78)
    print("2) committing action, no policy/approver: del_node -- should be refused")
    s = srs.Substrate()
    result = cg.commit_gate(s, {"kind": "del_node"})
    print(f"   result: {result}")
    assert result["allowed"] is False and result["gated"] is True and result["record"] is not None
    rec = s.node(result["record"])["attrs"]
    print(f"   Commitment record: {rec}")
    print("   OK: refused (no approver), Commitment record minted for the refusal.\n")


def scenario_committing_approved() -> None:
    print("-" * 78)
    print("3) committing action, approved under policy: del_node -- should be allowed")
    s = srs.Substrate()
    policy = {"allowlist": ["del_node"], "require_approver": True}
    result = cg.commit_gate(s, {"kind": "del_node"}, approver="pytest", policy=policy)
    print(f"   result: {result}")
    assert result["allowed"] is True and result["gated"] is True and result["record"] is not None
    rec = s.node(result["record"])["attrs"]
    print(f"   Commitment record: {rec}")
    print("   OK: allowed under policy, Commitment record minted.\n")


def scenario_subsumption_deny() -> None:
    print("-" * 78)
    print("4) SUBSUMPTION (deny case): a 'failed' ExtensionProposal --")
    print("   commit_gate's runtime_install eligibility precheck vs the real")
    print("   proposal_install.install_proposal, live, unmocked.")
    s = srs.Substrate()
    spec_id = s.add_node("RustExtensionSpec", {
        "name": "BrokenPrimitive", "semantics_kind": "graph_reachability",
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
        "compiled": False, "stage": "cargo_check", "errors": "E0425", "origin": "demo",
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": "BrokenPrimitive", "status": "failed", "installed": False,
        "requires_restart": True, "seconds": 1.0, "sandbox": "", "ts": time.time(),
    })
    s._inner.add_edge_unchecked(prop_id, "validates", spec_id)

    gate_result = cg.commit_gate(s, {"kind": "runtime_install", "proposal_id": prop_id},
                                  approver="pytest")
    oracle_result = pinstall.install_proposal(s, prop_id, approver="pytest")
    print(f"   commit_gate:      allowed={gate_result['allowed']!r} reason={gate_result['reason']!r}")
    print(f"   install_proposal: ok={oracle_result['ok']!r} reason={oracle_result['reason']!r}")
    assert gate_result["allowed"] is False and oracle_result["ok"] is False
    print("   OK: both refuse the failed proposal -- subsumption holds on the deny case.\n")


def _has_type(s, type_name: str) -> bool:
    try:
        s.nodes(type_name)
        return True
    except Exception:  # noqa: BLE001
        return False


def main() -> None:
    print_table()
    scenario_reversible()
    scenario_committing_refused()
    scenario_committing_approved()
    scenario_subsumption_deny()
    print("=" * 78)
    print("All scenarios passed. See tests/test_commitment_gate.py for the full")
    print("allow-side subsumption proof (mocked cargo/maturin) and discriminative")
    print("cases.")


if __name__ == "__main__":
    main()
