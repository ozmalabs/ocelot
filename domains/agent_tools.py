"""Filesystem + shell capabilities for the agent.

Three CAPABILITIES it gains by installation:

  read_file(of=<path>)        any path the user can read; returns text
  write_file(a=<content>,     workspace-scoped by default; writes UTF-8
             b=<path>)
  run_command(of=<command>)   workspace cwd, captured output, 30 s timeout

Defaults are workspace-scoped: writes + the cwd for ``run_command`` are
confined to ``~/.gamma_workspace`` (or whatever directory the ToolBox
points at). Reads are unrestricted — the agent can consult anything its
process can. The override knob is ``allow_outside_workspace=True``.

Every call lands in the agent's graph as an Action node (own type +
attrs) so the agent SEES its own action history and can reason about it
through the same Term-trees that observe the rest of the world.

Installation is one call: ``install_tools(agent, toolbox)`` extends the
agent's runtime_capabilities, installs the matching Frames (so natural
phrasings like "read foo.txt", "run ls", "write hello to bar.txt"
recognise through the agent's Frame layer), and asserts the
``agent_tools`` Microtheory so the Frame-scope check admits them.
"""
from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_WORKSPACE = Path(os.environ.get(
    "GAMMA_WORKSPACE", str(Path.home() / ".gamma_workspace")))
ACTION_NODE_TYPE = "Action"


# ---------------------------------------------------------------------------
# the ToolBox
# ---------------------------------------------------------------------------

@dataclass
class ToolBox:
    """Filesystem + shell capabilities the agent inherits when installed.

    Workspace-scoped by default: writes outside ``workspace`` raise
    PermissionError; ``run_command`` runs with ``cwd=workspace`` and the
    spawned process inherits the env. Reads are unrestricted — the agent
    can read anything its user can.
    """
    workspace: Path = field(default_factory=lambda: DEFAULT_WORKSPACE)
    timeout: float = 30.0
    max_output_bytes: int = 16_384      # truncate huge stdout/stderr
    max_read_bytes: int = 1_000_000     # 1 MB; same intent as output truncation
    allow_outside_workspace: bool = False
    log: list[dict] = field(default_factory=list, init=False)
    agent: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.workspace = Path(self.workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    # --- capability implementations ----------------------------------

    def read_file(self, args: dict) -> str:
        path = self._resolve(self._arg(args, "of", "arg", "path"))
        if not path.exists():
            raise FileNotFoundError(f"no such file: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"not a regular file: {path}")
        # cap at max_read_bytes so a 5GB log doesn't crater the session
        size = path.stat().st_size
        if size > self.max_read_bytes:
            with path.open("rb") as fh:
                blob = fh.read(self.max_read_bytes)
            text = blob.decode("utf-8", errors="replace")
            text += f"\n…[truncated; {size} bytes total]"
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
        self._record("read_file", {"path": str(path), "bytes": size})
        return text

    def write_file(self, args: dict) -> str:
        # Bindings can come in via either function_of_two_subjects
        # (a=content, b=path) or an explicit content/path teach pattern.
        content = self._arg(args, "a", "content")
        path_str = self._arg(args, "b", "to", "path")
        if path_str is None:
            raise ValueError("write_file: missing path (expected 'b' or 'path')")
        if content is None:
            raise ValueError("write_file: missing content "
                             "(expected 'a' or 'content')")
        path = self._resolve(path_str)
        self._check_writable(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = str(content)
        path.write_text(text, encoding="utf-8")
        self._record("write_file",
                     {"path": str(path), "bytes": len(text)})
        return f"wrote {len(text)} bytes → {path}"

    def run_command(self, args: dict) -> dict:
        command = self._arg(args, "of", "arg", "command")
        if not command:
            return {"error": "no command", "exit_code": -1}
        cmd_str = str(command)
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd_str, shell=True, capture_output=True, text=True,
                timeout=self.timeout, cwd=str(self.workspace))
            stdout = proc.stdout[:self.max_output_bytes]
            stderr = proc.stderr[:self.max_output_bytes]
            truncated_out = len(proc.stdout) > self.max_output_bytes
            truncated_err = len(proc.stderr) > self.max_output_bytes
            dt = (time.monotonic() - t0) * 1000
            result = {
                "exit_code": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": round(dt, 1),
                "truncated_stdout": truncated_out,
                "truncated_stderr": truncated_err,
            }
        except subprocess.TimeoutExpired:
            result = {"error": f"timeout after {self.timeout}s",
                      "exit_code": -1}
        self._record("run_command", {"command": cmd_str, **result})
        return result

    # --- internals ---------------------------------------------------

    @staticmethod
    def _arg(args: dict, *names: str) -> Any:
        for n in names:
            if n in args:
                return args[n]
        return None

    def _resolve(self, path_str: Any) -> Path:
        """Path expansion: ~ + env + relative-to-workspace, then resolve."""
        s = str(path_str)
        p = Path(os.path.expandvars(s)).expanduser()
        if not p.is_absolute():
            p = self.workspace / p
        return p.resolve()

    def _check_writable(self, path: Path) -> None:
        if self.allow_outside_workspace:
            return
        try:
            path.resolve().relative_to(self.workspace)
        except ValueError:
            raise PermissionError(
                f"workspace-scoped: writing outside {self.workspace} is "
                "disabled (set allow_outside_workspace=True to enable)")

    def _record(self, kind: str, payload: dict) -> None:
        """Append to the Python-side log AND, if installed on an agent,
        write an Action node into the mind graph — same shape as the
        agent's own perception events. The graph version is what the
        agent sees through its observation pipeline."""
        entry = {"kind": kind, "tick": time.time(), **payload}
        self.log.append(entry)
        if self.agent is None:
            return
        try:
            if hasattr(self.agent, "mind_substrate"):       # CuriousAgent host
                with self.agent.mind_substrate.transform() as tx:
                    nid = tx.add_node(ACTION_NODE_TYPE, entry)
                    tx.add_edge(self.agent.agent_root, "did", nid)
            else:                                            # WorldAdapter host
                nid = self.agent.s.add_node(ACTION_NODE_TYPE, entry)
                self.agent.inner.add_edge_unchecked(self.agent.agent, "did", nid)
        except Exception:
            # Never let logging break a capability call.
            pass

    # --- the capability dict the agent merges in ---------------------

    def capabilities(self) -> dict:
        return {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "run_command": self.run_command,
        }


# ---------------------------------------------------------------------------
# install — wire into agent
# ---------------------------------------------------------------------------

# What surface forms evoke each Frame. Words live in the agent's lexicon
# as soon as the Frame is installed.
_READ_EVOKED  = ["read", "open file", "show file", "cat"]
_WRITE_EVOKED = ["write", "save", "create file"]
_RUN_EVOKED   = ["run", "execute", "shell", "exec"]


def install_tools(agent, toolbox: ToolBox | None = None,
                  microtheory: str = "agent_tools") -> ToolBox:
    """Install ``toolbox`` (or a default ToolBox if None) into ``agent``.

    Wires the three capabilities into the agent's runtime_capabilities
    dispatch and installs three Frames so natural-language asks
    ('read foo.txt', 'run ls', 'write hello to bar.txt') route through
    the agent's recogniser.

    Idempotent: calling twice replaces the toolbox without duplicating
    Frames or Mts. Returns the toolbox (useful for the caller to keep a
    handle to ``.log`` and the workspace path).
    """
    from substrate import Production, NodePattern

    if toolbox is None:
        toolbox = ToolBox()
    toolbox.agent = agent

    # Productions for the action-log: Agent --did--> Action. Only the
    # CuriousAgent host runs an admissibility grammar; the WorldAdapter writes
    # the edge unchecked, so this is a no-op there.
    if hasattr(agent, "mind_substrate"):
        grammar = agent.mind_substrate.checker.grammar
        try:
            grammar.add(Production(
                src=NodePattern("Agent", "agent"),
                edge_type="did",
                tgt=NodePattern(ACTION_NODE_TYPE, "action"),
                provenance="meta:Agent-did-Action (agent_tools)",
            ))
        except Exception:
            pass

    # Make sure the Mt exists and the agent operates in it. install_microtheory
    # is idempotent (find-or-create), so call it unconditionally — works on any
    # host without reaching into a private index.
    agent.install_microtheory(
        microtheory,
        description="filesystem + shell capabilities the agent inherits",
        genl="general_knowledge")
    agent.operates_in(microtheory)

    # Install Frames — keep them function/predicate-of-subject because the
    # agent's comprehender treats those as the canonical shapes. Idempotent.
    agent.install_frame(
        name="read_file_frame",
        evoked_by=_READ_EVOKED,
        realised_by="read_file",
        holds_in=microtheory,
        core_elements=[{"slot": "of", "type": "any"}],
        binding_pattern="function_of_subject")
    agent.install_frame(
        name="write_file_frame",
        evoked_by=_WRITE_EVOKED,
        realised_by="write_file",
        holds_in=microtheory,
        core_elements=[
            {"slot": "a", "type": "any"},
            {"slot": "b", "type": "any"}],
        binding_pattern="function_of_two_subjects")
    agent.install_frame(
        name="run_command_frame",
        evoked_by=_RUN_EVOKED,
        realised_by="run_command",
        holds_in=microtheory,
        core_elements=[{"slot": "of", "type": "any"}],
        binding_pattern="function_of_subject")

    # Merge toolbox capabilities into the agent's runtime_capabilities dispatch.
    # We wrap rather than replace so future additions (other tool packs) can
    # stack the same way without losing what's underneath.
    original = agent.runtime_capabilities
    tool_caps = toolbox.capabilities()

    def merged():
        out = dict(original())
        out.update(tool_caps)
        return out

    # Tag the wrapper so we can detect + unwrap later if needed.
    merged._gamma_toolbox = toolbox    # type: ignore[attr-defined]
    agent.runtime_capabilities = merged

    return toolbox


__all__ = ["ToolBox", "install_tools", "ACTION_NODE_TYPE",
           "DEFAULT_WORKSPACE"]
