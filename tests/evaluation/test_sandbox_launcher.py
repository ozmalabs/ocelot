from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.p0a.sandbox import (BwrapSandboxLauncher, SandboxPolicyUnavailable,
                                    SandboxSpec, StagedEntrypoint)


class Scope:
    def __init__(self, run_id): self.run_id, self.kills = run_id, []
    def spawn(self, *_args, **_kwargs): raise AssertionError("construction test must not spawn")
    def kill(self, reason): self.kills.append(reason)


class Controller:
    def __init__(self, available=True): self.available, self.scopes = available, []
    def verify(self): return self.available
    def create_scope(self, run_id):
        scope = Scope(run_id); self.scopes.append(scope); return scope


def spec(tmp_path: Path) -> SandboxSpec:
    runtime, agent, inputs, work, policy = (tmp_path / name for name in ("runtime", "agent", "input", "work", "policy"))
    for path in (runtime, agent, inputs, work): path.mkdir()
    (agent / "trusted_staged_agent.py").write_text("def run(client):\n    return None\n")
    policy.write_bytes(b"policy")
    entrypoint = StagedEntrypoint.from_staged_agent(agent, "trusted_staged_agent:run")
    return SandboxSpec(runtime, agent, inputs, ("/runtime/python", "-I", "-m", "evaluation.p0a.agent_worker"),
                       work, policy, entrypoint)


def test_bwrap_argv_has_empty_root_explicit_allowlist_and_no_host_binds(tmp_path):
    launcher, sandbox = BwrapSandboxLauncher(Controller()), spec(tmp_path)
    argv = launcher.argv(sandbox)
    assert "--tmpfs" in argv and "/" in argv and "--unshare-net" in argv and "--die-with-parent" in argv
    assert ["--ro-bind", str(sandbox.runtime_root), "/runtime"] == argv[argv.index("--ro-bind"):argv.index("--ro-bind") + 3]
    rendered = " ".join(argv)
    for forbidden in ("/home", "docker.sock", "podman.sock", "receipts", "control-plane"):
        assert forbidden not in rendered
    assert "/run" not in argv
    binding = sandbox.entrypoint.worker_binding(sandbox.agent_root)
    assert launcher.safe_environment(entrypoint_binding=binding)["P0_STAGED_ENTRYPOINT_BINDING"] == binding
    assert "P0_AGENT_ENTRYPOINT" not in launcher.safe_environment()


def test_policy_controller_failure_is_before_worker_start(tmp_path):
    launcher = BwrapSandboxLauncher(Controller(available=False))
    with pytest.raises(SandboxPolicyUnavailable, match="cgroup controller"):
        launcher.preflight(spec(tmp_path))


def test_staged_entrypoint_rejects_agent_escape_and_substitution(tmp_path):
    sandbox = spec(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("def run(client): pass\n")
    (sandbox.agent_root / "escaped.py").symlink_to(outside)
    with pytest.raises(SandboxPolicyUnavailable, match="escapes staged agent"):
        StagedEntrypoint.from_staged_agent(sandbox.agent_root, "escaped:run")
    (sandbox.agent_root / "trusted_staged_agent.py").write_text("def run(client): return 'changed'\n")
    with pytest.raises(SandboxPolicyUnavailable, match="digest mismatch"):
        sandbox.validate()
