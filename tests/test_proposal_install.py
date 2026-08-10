"""GATE for domains/proposal_install.py — the ONE reusable host helper that
turns a validated `ExtensionProposal` into an installed runtime primitive
(web-approval today; auto-approve next — see that module's docstring).

Honest accounting of what runs LIVE vs MOCKED:

  (a) LIVE, real substrate_rs, real self_extend_rust: the ALREADY-INSTALLED
      `ReachableFrom` proposal → idempotent no-op. This never reaches cargo
      or maturin at all — `self_extend_rust.validate_spec`'s `already_present`
      short-circuit fires before any sandbox/render/compile work happens (see
      `domains/self_extend_rust.py:validate_spec`, the check right after
      `before = fingerprint_live_tree()`), and `install_proposal`'s own
      guardrail 2 short-circuits before ever calling
      `PrimitiveExtension.extend`. Asserted directly: `PrimitiveExtension`
      is never *constructed* on this path, the call completes in well under
      a second, and the live tree's md5 fingerprint is byte-identical
      before/after.

  (b) MOCKED: a synthetic "validated" proposal whose render would touch a
      file outside the installer's small allowed set. `ser.validate_spec`
      and `ser.render_spec` are monkeypatched so no real cargo check runs
      (the point of this test is the denylist derivation, not compilation);
      `PrimitiveExtension` is monkeypatched to raise if ever constructed, so
      a bug that let the denylist through would fail loudly here rather than
      silently attempting a real build in CI.

  (c) LIVE (no mocking needed — it's a pure status check): a proposal with
      status "failed" → refused before any sandbox/install work.

  (d) LIVE: `scripts/jabberwock_daemon.py`'s `list_proposals` /
      `proposal_detail` query functions, called directly against a real
      substrate carrying the nodes from (a) — no HTTP server needed.

No path in this file ever calls maturin or writes to `runners/dsl/src`
permanently; the final md5 assertion proves the live tree is unchanged by
the whole run.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs                                    # noqa: E402
from substrate.seed_loader import manifest_for                # noqa: E402
from domains import self_extend_rust as ser                   # noqa: E402
from domains import proposal_install as pinstall               # noqa: E402
import jabberwock_daemon as daemon                              # noqa: E402

# Captured at import time (before any test in this module runs) so the final
# integrity test proves the WHOLE module's run left the tree untouched, not
# just the instant between two adjacent calls.
_MODULE_BEFORE_FINGERPRINT = ser.fingerprint_live_tree()


def _fresh_substrate_with_reachable_from_proposal():
    """A real substrate carrying exactly the nodes ser.validate_spec mints
    for the (already live) ReachableFrom primitive — mirrors exactly what
    tests/test_rung4_sandbox.py's test_a exercises, and what the daemon
    checkpoint used in the live-daemon manual check carried."""
    s = srs.Substrate()
    agent = s.add_node("Agent", {})
    try:
        s._inner.load_seed_manifest(manifest_for("compiler_theory"), agent)
    except Exception:  # noqa: BLE001 -- grounding is best-effort, not required here
        pass
    spec = ser.agent_specify_reachable_from_primitive(s)
    res = ser.validate_spec(s, spec, scratch_dir="/tmp/gamma_substrate_test_proposal_install_scratch")
    assert res["ok"] is True
    assert res["stage"] == "already_present", (
        "this gate assumes ReachableFrom is already installed live (commit 54bbecf4); "
        f"got stage={res['stage']!r} instead — if ReachableFrom was ever reverted, "
        "this fixture needs a different already-installed primitive name")
    props = s.nodes("ExtensionProposal")
    assert props
    return s, props[-1]


# ---------------------------------------------------------------------------
# (a) LIVE: idempotent no-op on the already-installed ReachableFrom proposal
# ---------------------------------------------------------------------------

def test_a_idempotent_no_op_on_already_installed_reachable_from(monkeypatch):
    s, prop_id = _fresh_substrate_with_reachable_from_proposal()
    assert s.node(prop_id)["attrs"]["status"] == "already_present"
    assert s.node(prop_id)["attrs"]["installed"] is False

    # Prove PrimitiveExtension is never even CONSTRUCTED on this path (i.e.
    # no cargo/maturin call is possible) -- not just "didn't crash".
    def _boom(*a, **k):
        raise AssertionError("PrimitiveExtension must not be constructed on the "
                              "already_present idempotent-no-op path")
    monkeypatch.setattr(pinstall, "PrimitiveExtension", _boom)

    before = ser.fingerprint_live_tree()
    t0 = time.time()
    result = pinstall.install_proposal(s, prop_id, approver="pytest")
    dt = time.time() - t0

    assert result == {
        "ok": True, "installed": True, "requires_restart": True,
        "rebuilt": False, "reason": "already in runtime",
    }
    assert dt < 2.0, f"idempotent no-op took {dt:.2f}s -- should be near-instant (no cargo call)"

    attrs = s.node(prop_id)["attrs"]
    assert attrs["installed"] is True
    assert attrs["approved_by"] == "pytest"
    assert attrs["requires_restart"] is True

    # an Install record was minted and linked.
    installs = s.nodes("Install")
    assert installs
    linked = list(s._inner.neighbours(installs[-1], "installs"))
    assert prop_id in linked

    problems = ser.assert_live_tree_untouched(before)
    assert not problems, f"idempotent no-op touched the live tree: {problems}"

    # calling it again refuses (guardrail 1: no double-install).
    result2 = pinstall.install_proposal(s, prop_id, approver="pytest")
    assert result2["ok"] is False
    assert result2["reason"] == "already installed"
    assert result2["installed"] is True


# ---------------------------------------------------------------------------
# (b) MOCKED: a validated proposal whose render touches a disallowed file
# ---------------------------------------------------------------------------

def test_b_denylist_refuses_disallowed_file(monkeypatch):
    s = srs.Substrate()
    spec_id = s.add_node("RustExtensionSpec", {
        "name": "EvilPrimitive", "semantics_kind": "graph_reachability",
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
        "compiled": True, "stage": "cargo_check", "errors": "", "origin": "test",
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": "EvilPrimitive", "status": "validated", "installed": False,
        "requires_restart": True, "seconds": 1.0, "sandbox": "", "ts": time.time(),
    })
    s._inner.add_edge_unchecked(prop_id, "validates", spec_id)

    # Mock the fresh-revalidation to "pass" (we're not testing cargo here --
    # see the module docstring's guardrail 4 vs 5 split) and mock render_spec
    # to report a fragment keyed to a file OUTSIDE the allowed set.
    monkeypatch.setattr(pinstall.ser, "validate_spec",
                        lambda substrate, spec, **kw: {"ok": True, "stage": "cargo_check"})
    monkeypatch.setattr(pinstall.ser, "render_spec",
                        lambda spec: {"evil_backdoor.rs (some arm)": "// malicious"})

    def _boom(*a, **k):
        raise AssertionError("PrimitiveExtension must not be constructed when the "
                              "denylist guardrail refuses the spec")
    monkeypatch.setattr(pinstall, "PrimitiveExtension", _boom)

    result = pinstall.install_proposal(s, prop_id, approver="pytest")
    assert result["ok"] is False
    assert "evil_backdoor.rs" in result["reason"]
    assert "disallowed" in result["reason"]

    attrs = s.node(prop_id)["attrs"]
    assert attrs["installed"] is False, "a refused install must not be marked installed"


# ---------------------------------------------------------------------------
# (c) LIVE: a "failed" proposal is refused outright, no sandbox/install work
# ---------------------------------------------------------------------------

def test_c_failed_status_refused(monkeypatch):
    s = srs.Substrate()
    spec_id = s.add_node("RustExtensionSpec", {
        "name": "BrokenPrimitive", "semantics_kind": "graph_reachability",
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
        "compiled": False, "stage": "cargo_check", "errors": "E0425", "origin": "test",
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": "BrokenPrimitive", "status": "failed", "installed": False,
        "requires_restart": True, "seconds": 1.0, "sandbox": "", "ts": time.time(),
    })
    s._inner.add_edge_unchecked(prop_id, "validates", spec_id)

    calls = []
    monkeypatch.setattr(pinstall.ser, "validate_spec",
                        lambda *a, **k: calls.append("validate_spec") or {"ok": True})

    def _boom(*a, **k):
        raise AssertionError("must not construct PrimitiveExtension for a failed proposal")
    monkeypatch.setattr(pinstall, "PrimitiveExtension", _boom)

    result = pinstall.install_proposal(s, prop_id, approver="pytest")
    assert result == {"ok": False, "reason": "status is 'failed', not 'validated'"}
    assert not calls, "a failed proposal must be refused before any fresh re-validation runs"
    assert s.node(prop_id)["attrs"]["installed"] is False


def test_not_found_refused():
    s = srs.Substrate()
    result = pinstall.install_proposal(s, 999999, approver="pytest")
    assert result["ok"] is False
    assert "not found" in result["reason"]


def test_persisted_complete_spec_round_trips_and_is_authenticated():
    spec = {
        "name": "DurableReduce",
        "semantics": {
            "kind": "reduce",
            "reduce_op": "maximum",
            "band": 7,
            "nested": {"recur_kind": "tree"},
        },
        "purpose": "prove restart-safe reconstruction",
        "why_new": "the summary is intentionally insufficient",
        "motivating_residual": "restart",
    }
    result = {"ok": False, "stage": "render", "errors": ["expected fixture stop"]}
    s = srs.Substrate()
    ser._record(s, spec, result)
    node = s.nodes("RustExtensionSpec")[0]
    attrs = s.node(node)["attrs"]

    assert pinstall._spec_dict_from_node(attrs) == spec
    assert json.loads(attrs["spec_json"]) == spec
    assert len(attrs["spec_sha256"]) == 64

    tampered = dict(attrs)
    tampered["spec_json"] = attrs["spec_json"].replace("maximum", "minimum")
    with pytest.raises(ValueError, match="hash mismatch"):
        pinstall._spec_dict_from_node(tampered)


def test_legacy_lossy_nontrivial_spec_is_refused_before_validation(monkeypatch):
    s = srs.Substrate()
    spec_id = s.add_node("RustExtensionSpec", {
        "name": "LegacyReduce", "semantics_kind": "reduce",
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": "LegacyReduce", "status": "validated", "installed": False,
    })
    s._inner.add_edge_unchecked(prop_id, "validates", spec_id)
    monkeypatch.setattr(
        pinstall.ser,
        "validate_spec",
        lambda *a, **k: pytest.fail("lossy proposal must be refused before validation"),
    )

    result = pinstall.install_proposal(s, prop_id, approver="pytest")
    assert result["ok"] is False
    assert "incomplete" in result["reason"]


# ---------------------------------------------------------------------------
# (d) LIVE: the daemon's mechanical proposal query functions
# ---------------------------------------------------------------------------

class _FakeInner:
    """Minimal stand-in exposing just .neighbours, matching WorldAdapter.inner's
    surface for the one call list_proposals/proposal_detail make."""
    def __init__(self, s):
        self._s = s

    def neighbours(self, nid, edge_type):
        return self._s.neighbours(nid, edge_type)


class _FakeAdapter:
    """Duck-types the two attributes list_proposals/proposal_detail touch
    (.s, .inner) without booting a full WorldAdapter."""
    def __init__(self, s):
        self.s = s
        self.inner = _FakeInner(s)


def test_d_daemon_list_and_detail_query_functions():
    s, prop_id = _fresh_substrate_with_reachable_from_proposal()
    adapter = _FakeAdapter(s)

    proposals = daemon.list_proposals(adapter)
    assert len(proposals) == 1
    entry = proposals[0]
    assert entry["id"] == prop_id.value
    assert entry["name"] == "ReachableFrom"
    assert entry["status"] == "already_present"
    assert entry["installed"] is False
    assert entry["requires_restart"] is True
    assert entry["purpose"]
    assert entry["motivating_residual"]

    res = daemon.proposal_detail(adapter, str(prop_id.value))
    assert res is not None
    proposal, spec, diff = res
    assert proposal["of"] == "ReachableFrom"
    assert proposal["status"] == "already_present"
    assert spec["name"] == "ReachableFrom"
    assert spec["semantics_kind"] == "graph_reachability"
    assert "ReachableFrom" in diff
    assert "term.rs" in diff

    # unknown id -> None, not a crash.
    assert daemon.proposal_detail(adapter, "999999999") is None
    assert daemon.list_proposals(_FakeAdapter(srs.Substrate())) == []


# ---------------------------------------------------------------------------
# final integrity proof: nothing in this whole file left the live tree dirty
# ---------------------------------------------------------------------------

def test_z_live_tree_untouched_after_whole_module():
    problems = ser.assert_live_tree_untouched(_MODULE_BEFORE_FINGERPRINT)
    assert not problems, f"live tree/installed .so changed during this test module: {problems}"
