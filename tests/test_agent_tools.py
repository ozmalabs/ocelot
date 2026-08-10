"""Filesystem + shell capabilities — workspace scoping, capability dispatch,
and Frame-layer integration with the agent's answer pipeline."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from domains.agent_tools import (ACTION_NODE_TYPE, ToolBox, install_tools)
from substrate.world_adapter import WorldAdapter


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def toolbox(tmp_path: Path) -> ToolBox:
    return ToolBox(workspace=tmp_path / "ws")


@pytest.fixture
def agent_with_tools(toolbox: ToolBox) -> tuple[WorldAdapter, ToolBox]:
    a = WorldAdapter()
    install_tools(a, toolbox)
    return a, toolbox


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------

def test_read_file_returns_content(toolbox: ToolBox, tmp_path: Path):
    p = tmp_path / "src.txt"
    p.write_text("hello, gamma")
    out = toolbox.read_file({"of": str(p)})
    assert out == "hello, gamma"


def test_read_file_handles_relative_path_via_workspace(toolbox: ToolBox):
    (toolbox.workspace / "a.txt").write_text("workspace file")
    out = toolbox.read_file({"of": "a.txt"})
    assert out == "workspace file"


def test_read_file_can_read_outside_workspace(toolbox: ToolBox,
                                              tmp_path: Path):
    # Reads are unrestricted — outside-workspace path is fine.
    elsewhere = tmp_path / "outside.txt"
    elsewhere.write_text("not in workspace")
    out = toolbox.read_file({"of": str(elsewhere)})
    assert out == "not in workspace"


def test_read_file_missing_raises(toolbox: ToolBox, tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        toolbox.read_file({"of": str(tmp_path / "ghost.txt")})


def test_read_file_truncates_huge_files(toolbox: ToolBox, tmp_path: Path):
    p = tmp_path / "big.bin"
    p.write_bytes(b"A" * 2_000_000)
    toolbox.max_read_bytes = 1024
    out = toolbox.read_file({"of": str(p)})
    assert len(out) >= 1024
    assert "truncated" in out


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

def test_write_file_inside_workspace_succeeds(toolbox: ToolBox):
    result = toolbox.write_file({"a": "hi", "b": "out.txt"})
    written = (toolbox.workspace / "out.txt").read_text()
    assert written == "hi"
    assert "wrote 2 bytes" in result


def test_write_file_creates_subdirs(toolbox: ToolBox):
    toolbox.write_file({"a": "deep", "b": "sub/dir/nested.txt"})
    assert (toolbox.workspace / "sub" / "dir" / "nested.txt").read_text() == "deep"


def test_write_file_outside_workspace_refused(toolbox: ToolBox,
                                              tmp_path: Path):
    target = tmp_path / "not_ok.txt"
    with pytest.raises(PermissionError):
        toolbox.write_file({"a": "hi", "b": str(target)})
    assert not target.exists()


def test_write_file_outside_allowed_when_opted_in(toolbox: ToolBox,
                                                  tmp_path: Path):
    toolbox.allow_outside_workspace = True
    target = tmp_path / "yes_ok.txt"
    toolbox.write_file({"a": "yes", "b": str(target)})
    assert target.read_text() == "yes"


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------

def test_run_command_captures_stdout(toolbox: ToolBox):
    r = toolbox.run_command({"of": "echo gamma"})
    assert r["exit_code"] == 0
    assert r["stdout"].strip() == "gamma"
    assert r["stderr"] == ""


def test_run_command_captures_stderr_and_exit_code(toolbox: ToolBox):
    r = toolbox.run_command({"of": "ls /no/such/path"})
    assert r["exit_code"] != 0
    assert r["stderr"] != ""


def test_run_command_cwd_is_workspace(toolbox: ToolBox):
    (toolbox.workspace / "marker.txt").write_text("here")
    r = toolbox.run_command({"of": "ls marker.txt"})
    assert r["exit_code"] == 0
    assert "marker.txt" in r["stdout"]


def test_run_command_times_out(toolbox: ToolBox):
    toolbox.timeout = 0.5
    r = toolbox.run_command({"of": "sleep 10"})
    assert "timeout" in r.get("error", "")


def test_run_command_truncates_huge_output(toolbox: ToolBox):
    toolbox.max_output_bytes = 100
    r = toolbox.run_command({"of": "yes gamma | head -c 5000"})
    assert len(r["stdout"]) <= 100
    assert r["truncated_stdout"] is True


# ---------------------------------------------------------------------------
# install_tools — agent integration
# ---------------------------------------------------------------------------

def test_install_tools_registers_capabilities(agent_with_tools):
    a, tb = agent_with_tools
    caps = a.runtime_capabilities()
    assert "read_file" in caps
    assert "write_file" in caps
    assert "run_command" in caps


def test_install_tools_installs_frames_and_microtheory(agent_with_tools):
    a, _ = agent_with_tools
    assert a.microtheory("agent_tools") is not None
    assert a.frame("read_file_frame") is not None
    assert a.frame("write_file_frame") is not None
    assert a.frame("run_command_frame") is not None


def test_install_tools_is_idempotent(agent_with_tools):
    # Second install replaces toolbox without dup-installing Frames/Mts.
    a, _ = agent_with_tools
    fnode = a.frame("read_file_frame")
    tb2 = ToolBox(workspace=Path("/tmp"))
    install_tools(a, tb2)
    assert a.frame("read_file_frame") == fnode             # same node


def test_action_node_lands_in_graph_after_capability_call(agent_with_tools,
                                                          tmp_path):
    """The agent SEES what it has done — every capability call writes an
    Action node attached to agent_root via a 'did' edge."""
    a, tb = agent_with_tools
    p = tmp_path / "src.txt"
    p.write_text("yo")
    a.runtime_capabilities()["read_file"]({"of": str(p)})
    actions = [n for n in a.s.nodes() if a.s.node(n)["type"] == ACTION_NODE_TYPE]
    assert len(actions) == 1
    attrs = a.s.node(actions[0])["attrs"]
    assert attrs["kind"] == "read_file"
    assert str(p) in attrs["path"]


# ---------------------------------------------------------------------------
# end-to-end through answer_within
# ---------------------------------------------------------------------------

def test_answer_within_recognises_and_routes_read_command(agent_with_tools):
    """The agent's Frame recogniser matches 'read X' to read_file_frame,
    binds X as the 'of' slot, dispatches to the capability. The same
    pipeline answer_within uses.

    Note: the comprehender tokenises words; multi-segment file paths
    (/tmp/x/y/z.txt) aren't single tokens. The intended ergonomic is
    workspace-relative bare-word file names — the recogniser handles
    'read hello' cleanly, and the toolbox resolves 'hello' against the
    workspace. This matches the workspace-scoped design."""
    from domains.reason import answer_within
    a, tb = agent_with_tools
    (tb.workspace / "hello").write_text("frame-routed")
    answer, _ops, strategy = answer_within(
        "read hello", bindings={}, budget_ops=1_000_000, agent=a)
    assert answer == "frame-routed"


def test_answer_within_recognises_run_command(agent_with_tools):
    """run_command binds the entire trailing phrase as 'of', which the
    workspace shell then executes verbatim. 'echo' fits as a one-word
    subject; multi-arg commands work via 'run of <cmd>' (the 'of'
    particle is the explicit slot marker the comprehender already
    knows)."""
    from domains.reason import answer_within
    a, _tb = agent_with_tools
    answer, _ops, _strategy = answer_within(
        "run echo", bindings={}, budget_ops=1_000_000, agent=a)
    assert isinstance(answer, dict)
    assert answer["exit_code"] == 0
