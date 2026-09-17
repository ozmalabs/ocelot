from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.p0a import agent_worker
from evaluation.p0a.agent_worker import _assert_fds, _staged_target
from evaluation.p0a.canonical import ProtocolError, sha256


def binding(root: Path, *, module: str = "trusted_agent", artifact: Path | None = None,
            digest: str | None = None) -> str:
    artifact = artifact or root / "trusted_agent.py"
    return json.dumps({"module": module, "function": "run", "artifact_path": str(artifact),
                       "artifact_digest": digest or sha256(artifact.read_bytes())})


def test_worker_executes_verified_staged_bytes_not_ambient_module(tmp_path, monkeypatch):
    root = tmp_path / "agent"; root.mkdir()
    artifact = root / "trusted_agent.py"
    artifact.write_text("def run(client):\n    client.append('staged')\n")
    # An ambient module with the same name must never be consulted.
    import types, sys
    ambient = types.ModuleType("trusted_agent")
    ambient.run = lambda _client: (_ for _ in ()).throw(AssertionError("ambient import used"))
    monkeypatch.setitem(sys.modules, "trusted_agent", ambient)
    calls = []
    _staged_target(binding(root), agent_root=root, mount_root=root)(calls)
    assert calls == ["staged"]


def test_worker_denies_module_path_substitution(tmp_path):
    root = tmp_path / "agent"; root.mkdir()
    artifact = root / "trusted_agent.py"
    artifact.write_text("def run(client): pass\n")
    with pytest.raises(ProtocolError, match="module path mismatch"):
        _staged_target(binding(root, module="ambient_module"), agent_root=root, mount_root=root)


def test_worker_denies_staging_content_substitution(tmp_path):
    root = tmp_path / "agent"; root.mkdir()
    artifact = root / "trusted_agent.py"
    artifact.write_text("def run(client): pass\n")
    staged_binding = binding(root)
    artifact.write_text("def run(client): return 'substituted'\n")
    with pytest.raises(ProtocolError, match="digest mismatch"):
        _staged_target(staged_binding, agent_root=root, mount_root=root)


def test_worker_denies_artifact_outside_staged_agent_mount(tmp_path):
    root = tmp_path / "agent"; root.mkdir()
    artifact = root / "trusted_agent.py"
    artifact.write_text("def run(client): pass\n")
    outside = tmp_path / "outside.py"
    outside.write_text("def run(client): pass\n")
    with pytest.raises(ProtocolError, match="escapes agent mount"):
        _staged_target(binding(root, artifact=outside), agent_root=root, mount_root=root)



def test_worker_fd_guard_ignores_only_its_closed_proc_enumeration_fd(monkeypatch):
    monkeypatch.setattr(agent_worker.os, "listdir", lambda _path: ["0", "1", "2", "3"])
    monkeypatch.setattr(agent_worker.os.path, "exists", lambda path: not path.endswith("/3"))
    _assert_fds()


def test_worker_fd_guard_rejects_a_live_extra_descriptor(monkeypatch):
    monkeypatch.setattr(agent_worker.os, "listdir", lambda _path: ["0", "1", "2", "3"])
    monkeypatch.setattr(agent_worker.os.path, "exists", lambda _path: True)
    with pytest.raises(ProtocolError, match="unexpected inherited descriptor"):
        _assert_fds()
