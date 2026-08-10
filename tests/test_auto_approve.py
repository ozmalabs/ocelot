"""GATE for domains/auto_approve.py — the human's OFF-by-default auto-approve
SETTING plus the mechanical policy evaluation that acts on it, and the daemon
wiring (`/api/auto_approve`, `/api/status`'s `auto_approve` block, the
`_auto_approve_tick` hook, and boot's ensure/clear-pause calls).

Honest accounting of what runs LIVE vs MOCKED, mirroring tests/test_proposal_
install.py's own convention:

  LIVE, real substrate_rs: every node/edge/attr read+write in this file is a
      real Substrate (or a real WorldAdapter for the persistence test) — no
      graph-layer mocking anywhere.

  MOCKED: `domains.proposal_install.install_proposal` (and, for the two
      scope-guardrail unit tests that need it, `domains.auto_approve.
      ser.plan_inserts` / `_is_additive`). NO test in this file ever calls
      the real installer, so NO test ever reaches cargo or maturin — the
      whole point of `scan_and_auto_approve` mocked here is to prove the
      POLICY WIRING (which proposals qualify, in what order, with what
      audit log), not to re-prove `install_proposal`'s own guardrails
      (tests/test_proposal_install.py already owns that).

Every test that calls `pinstall.install_proposal` for real is disallowed by
construction: `_boom` monkeypatches raise loudly if construction/call is
ever attempted on a path that should have been skipped by policy.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import substrate_rs as srs                                     # noqa: E402
from domains import auto_approve as auto_appr                  # noqa: E402
from domains import proposal_install as pinstall                # noqa: E402
from domains import self_extend_rust as ser                     # noqa: E402
import jabberwock_daemon as daemon                               # noqa: E402

NOW = 1_800_000_000.0  # fixed clock -- deterministic rate-cap arithmetic


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------

def _fresh_validated_proposal(s, *, name="FakeAdditive", kind="graph_reachability"):
    """A real ExtensionProposal + RustExtensionSpec pair shaped exactly like
    what `self_extend_rust._record` mints for a validated, not-yet-installed
    proposal (see that module) -- but never actually run through the sandbox
    (no cargo call anywhere in this file)."""
    spec_id = s.add_node("RustExtensionSpec", {
        "name": name, "semantics_kind": kind,
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
        "compiled": True, "stage": "cargo_check", "errors": "", "origin": "test",
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": name, "status": "validated", "installed": False,
        "requires_restart": True, "seconds": 1.0, "sandbox": "", "ts": NOW,
    })
    s.add_edge_unchecked(prop_id, "validates", spec_id)
    return prop_id, spec_id


def _boom(*a, **k):
    raise AssertionError("install_proposal must not be called on a path policy should have skipped")


# ---------------------------------------------------------------------------
# (a) OFF by default -- the safe posture
# ---------------------------------------------------------------------------

def test_a1_no_policy_node_scan_is_noop(monkeypatch):
    s = srs.Substrate()
    _fresh_validated_proposal(s)
    monkeypatch.setattr(pinstall, "install_proposal", _boom)

    assert auto_appr.get_policy(s) is None  # nothing minted yet
    results = auto_appr.scan_and_auto_approve(s, now_ts=NOW)
    assert results == []


def test_a2_policy_off_explicit_scan_is_noop(monkeypatch):
    s = srs.Substrate()
    _fresh_validated_proposal(s)
    auto_appr.ensure_policy_node(s)  # enabled: False (the default)
    monkeypatch.setattr(pinstall, "install_proposal", _boom)

    policy = auto_appr.get_policy(s)
    assert policy["enabled"] is False
    assert policy["max_installs_per_hour"] == 2
    assert policy["require_additive"] is True
    assert policy["allowed_semantics_kinds"] == ["graph_reachability"]
    assert policy["paused_until_restart"] is False

    log_lines = []
    results = auto_appr.scan_and_auto_approve(s, now_ts=NOW, log=log_lines.append)
    assert results == []
    assert any("disabled" in ln for ln in log_lines)


# ---------------------------------------------------------------------------
# (b) ON + a proposal that PASSES scope -> install_proposal is called
# ---------------------------------------------------------------------------

def test_b_policy_on_passes_scope_installs_and_pauses(monkeypatch):
    s = srs.Substrate()
    prop_id, _spec_id = _fresh_validated_proposal(s, name="ReachableFrom2")
    auto_appr.set_policy(s, enabled=True, max_installs_per_hour=5,
                          require_additive=True,
                          allowed_semantics_kinds=["graph_reachability"])

    calls = []

    def _fake_install(agent, proposal_id, *, approver="web", **kw):
        calls.append((proposal_id, approver))
        return {"ok": True, "installed": True, "requires_restart": True,
                "reason": "installed (mocked)"}

    monkeypatch.setattr(pinstall, "install_proposal", _fake_install)

    log_lines = []
    results = auto_appr.scan_and_auto_approve(s, now_ts=NOW, log=log_lines.append)

    assert len(calls) == 1
    called_id, called_approver = calls[0]
    assert called_approver == "auto"
    assert called_id == prop_id

    assert len(results) == 1
    assert results[0]["action"] == "approved"
    assert results[0]["id"] == prop_id.value
    assert results[0]["installed"] is True

    # a requires_restart install must pause further auto-installs.
    policy = auto_appr.get_policy(s)
    assert policy["paused_until_restart"] is True
    assert any("APPROVING" in ln for ln in log_lines)
    assert any("pausing further auto-installs" in ln for ln in log_lines)


# ---------------------------------------------------------------------------
# (c) ON + a proposal that FAILS a scope guardrail -- discriminative
# ---------------------------------------------------------------------------

def test_c1_wrong_semantics_kind_skipped(monkeypatch):
    s = srs.Substrate()
    _fresh_validated_proposal(s, name="SomeMatrixThing", kind="matrix_whiten_batch")
    auto_appr.set_policy(s, enabled=True, allowed_semantics_kinds=["graph_reachability"])
    monkeypatch.setattr(pinstall, "install_proposal", _boom)

    log_lines = []
    results = auto_appr.scan_and_auto_approve(s, now_ts=NOW, log=log_lines.append)
    assert len(results) == 1
    assert results[0]["action"] == "skipped"
    assert "semantics_kind" in results[0]["reason"]
    assert "matrix_whiten_batch" in results[0]["reason"]
    assert not auto_appr.get_policy(s)["paused_until_restart"]


def test_c2_non_additive_skipped(monkeypatch):
    s = srs.Substrate()
    _fresh_validated_proposal(s, name="FakeAdditive", kind="graph_reachability")
    auto_appr.set_policy(s, enabled=True, require_additive=True,
                          allowed_semantics_kinds=["graph_reachability"])
    monkeypatch.setattr(pinstall, "install_proposal", _boom)
    monkeypatch.setattr(auto_appr, "_is_additive",
                         lambda spec: (False, "mocked: would overwrite an existing arm"))

    log_lines = []
    results = auto_appr.scan_and_auto_approve(s, now_ts=NOW, log=log_lines.append)
    assert len(results) == 1
    assert results[0]["action"] == "skipped"
    assert "not additive" in results[0]["reason"]


def test_c2b_is_additive_unit_real_pipeline():
    """Unit-level proof of `_is_additive` against the REAL render_spec /
    plan_inserts pipeline (no monkeypatching) -- the ReachableFrom-shaped
    spec is genuinely additive (every insert splices before/after an anchor,
    per self_extend_rust.apply_to_sandbox); a synthetic 'replace' position
    (which nothing in this codebase emits today, but which a future codegen
    template COULD) is correctly refused."""
    real_spec = ser.agent_specify_reachable_from_primitive()
    ok, why = auto_appr._is_additive(real_spec)
    assert ok is True, why

    # Force a non-additive position through the real render, to prove the
    # position check itself (not just the happy path) is load-bearing.
    fake_frags = {"term.rs (enum variant)": "// x"}
    real_render = ser.render_spec
    real_plan = ser.plan_inserts
    try:
        ser.render_spec = lambda spec: fake_frags
        ser.plan_inserts = lambda frags: (
            [{"home": k, "file": "term.rs", "anchor": "a", "insert": "b", "position": "replace"}
             for k in frags], [])
        ok2, why2 = auto_appr._is_additive(real_spec)
        assert ok2 is False
        assert "non-additive" in why2
    finally:
        ser.render_spec = real_render
        ser.plan_inserts = real_plan


def test_c3_rate_cap_skipped(monkeypatch):
    s = srs.Substrate()
    _fresh_validated_proposal(s, name="FakeAdditive2", kind="graph_reachability")
    auto_appr.set_policy(s, enabled=True, max_installs_per_hour=1,
                          require_additive=False,  # isolate the rate-cap guardrail
                          allowed_semantics_kinds=["graph_reachability"])
    # one successful auto-install already recorded within the last hour.
    s.add_node("Install", {"proposal": 1, "approver": "auto", "ts": NOW - 100,
                            "ok": True, "note": "prior"})
    monkeypatch.setattr(pinstall, "install_proposal", _boom)

    assert auto_appr._count_recent_auto_installs(s, NOW) == 1

    log_lines = []
    results = auto_appr.scan_and_auto_approve(s, now_ts=NOW, log=log_lines.append)
    assert len(results) == 1
    assert results[0]["action"] == "skipped"
    assert "rate cap" in results[0]["reason"]


def test_c3b_rate_cap_ignores_old_and_human_installs():
    s = srs.Substrate()
    # outside the window -- must not count.
    s.add_node("Install", {"proposal": 1, "approver": "auto", "ts": NOW - 7200,
                            "ok": True, "note": "old"})
    # a human-approved install -- must not count against the AUTO rate cap.
    s.add_node("Install", {"proposal": 2, "approver": "web", "ts": NOW - 10,
                            "ok": True, "note": "human"})
    # a failed auto attempt -- must not count (nothing was actually installed).
    s.add_node("Install", {"proposal": 3, "approver": "auto", "ts": NOW - 10,
                            "ok": False, "note": "failed"})
    assert auto_appr._count_recent_auto_installs(s, NOW) == 0


# ---------------------------------------------------------------------------
# (d) paused_until_restart -- scan is a no-op until a boot clears it
# ---------------------------------------------------------------------------

def test_d1_paused_scan_is_noop(monkeypatch):
    s = srs.Substrate()
    _fresh_validated_proposal(s)
    auto_appr.set_policy(s, enabled=True)
    pid = auto_appr.ensure_policy_node(s)
    s.set_attr(pid, "paused_until_restart", True)
    monkeypatch.setattr(pinstall, "install_proposal", _boom)

    log_lines = []
    results = auto_appr.scan_and_auto_approve(s, now_ts=NOW, log=log_lines.append)
    assert results == []
    assert any("paused_until_restart" in ln for ln in log_lines)


def test_d2_clear_pause_on_boot():
    s = srs.Substrate()
    pid = auto_appr.ensure_policy_node(s)
    s.set_attr(pid, "paused_until_restart", True)
    assert auto_appr.get_policy(s)["paused_until_restart"] is True

    auto_appr.clear_pause_on_boot(s)
    assert auto_appr.get_policy(s)["paused_until_restart"] is False

    # no-op (no crash) when no policy node exists at all.
    auto_appr.clear_pause_on_boot(srs.Substrate())


# ---------------------------------------------------------------------------
# (e) the daemon's HTTP routes: GET/POST /api/auto_approve, /api/status
# ---------------------------------------------------------------------------

class _FakeAdapter:
    """Duck-types the one attribute (.s) the auto-approve + status routes
    touch, without booting a full WorldAdapter -- mirrors test_proposal_
    install.py's own _FakeAdapter pattern."""
    def __init__(self, s):
        self.s = s


def test_e_http_routes_auto_approve_and_status():
    s = srs.Substrate()
    adapter = _FakeAdapter(s)
    state = daemon.DaemonState(adapter, "checkpoint")
    srv, _t = daemon.serve_http(state, 0)
    try:
        port = srv.socket.getsockname()[1]
        base = f"http://127.0.0.1:{port}"

        with urllib.request.urlopen(base + "/api/auto_approve", timeout=5) as r:
            d = json.loads(r.read())
        assert d["ok"] is True
        assert d["enabled"] is False
        assert d["max_installs_per_hour"] == 2

        req = urllib.request.Request(
            base + "/api/auto_approve",
            data=json.dumps({"enabled": True, "max_installs_per_hour": 7,
                              "allowed_semantics_kinds": ["graph_reachability", "primitive"]}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            d2 = json.loads(r.read())
        assert d2["ok"] is True
        assert d2["enabled"] is True
        assert d2["max_installs_per_hour"] == 7
        assert d2["allowed_semantics_kinds"] == ["graph_reachability", "primitive"]

        # paused_until_restart is NOT a settable field via this route.
        req2 = urllib.request.Request(
            base + "/api/auto_approve",
            data=json.dumps({"paused_until_restart": True}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req2, timeout=5) as r:
            d3 = json.loads(r.read())
        assert d3["paused_until_restart"] is False  # ignored, still default

        with urllib.request.urlopen(base + "/api/status", timeout=5) as r:
            st = json.loads(r.read())
        assert st["ok"] is True
        assert st["auto_approve"]["enabled"] is True
        assert st["auto_approve"]["max_installs_per_hour"] == 7
    finally:
        srv.shutdown()
        srv.server_close()


# ---------------------------------------------------------------------------
# (f) persistence: survives save/load; a fresh boot has it, default OFF
# ---------------------------------------------------------------------------

def test_f_policy_survives_save_load(tmp_path):
    from substrate.world_adapter import WorldAdapter

    wa = WorldAdapter(seeds=())  # minimal, fast boot -- no seed set needed
    auto_appr.ensure_policy_node(wa)
    assert auto_appr.get_policy(wa)["enabled"] is False  # default OFF, unminted-fresh
    auto_appr.set_policy(wa, enabled=True, max_installs_per_hour=9,
                          allowed_semantics_kinds=["graph_reachability", "widened_kind"])

    path = tmp_path / "aa_persist.save"
    wa.save(str(path))

    wa2 = WorldAdapter.load(str(path))
    policy2 = auto_appr.get_policy(wa2)
    assert policy2 is not None
    assert policy2["enabled"] is True
    assert policy2["max_installs_per_hour"] == 9
    assert policy2["allowed_semantics_kinds"] == ["graph_reachability", "widened_kind"]

    # a genuinely fresh graph (no save/load at all) mints its OWN node,
    # independently defaulted OFF -- one agent's toggle never leaks into
    # a different agent's fresh boot.
    wa3 = WorldAdapter(seeds=())
    auto_appr.ensure_policy_node(wa3)
    assert auto_appr.get_policy(wa3)["enabled"] is False


# ---------------------------------------------------------------------------
# (g) daemon boots clean with the hook + flag
# ---------------------------------------------------------------------------

def test_g_daemon_boots_clean_with_hook_and_flag(tmp_path):
    import subprocess
    ckpt_dir = tmp_path / "ckpt"
    runs_dir = tmp_path / "runs"
    env = {**__import__("os").environ}
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "jabberwock_daemon.py"),
         "--seeds", "chat", "--once", "--ckpt-dir", str(ckpt_dir),
         "--runs-dir", str(runs_dir), "--no-http",
         "--auto-approve-every", "5"],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, (
        f"daemon --once failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    assert "once-mode complete" in result.stdout
    # boot() must have minted the policy node (default OFF) even on a fresh,
    # never-checkpointed boot -- verify by loading the checkpoint it just wrote.
    snaps = sorted(ckpt_dir.glob("snapshot-*.save"))
    assert snaps, "no checkpoint written"
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter.load(str(snaps[-1]))
    policy = auto_appr.get_policy(wa)
    assert policy is not None
    assert policy["enabled"] is False


# ---------------------------------------------------------------------------
# (h) auto-approve hook: cheap no-op path when disabled (no loud log/build)
# ---------------------------------------------------------------------------

def test_h_auto_approve_tick_noop_when_disabled(monkeypatch):
    s = srs.Substrate()
    adapter = _FakeAdapter(s)
    _fresh_validated_proposal(s)
    monkeypatch.setattr(pinstall, "install_proposal", _boom)
    # must not raise, must not install anything (policy unminted -> disabled).
    daemon._auto_approve_tick(adapter)
    assert auto_appr.get_policy(s) is None or auto_appr.get_policy(s)["enabled"] is False
