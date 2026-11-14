"""ocelot_agent_eval — end-to-end task-success harness for coding agents.

DEV TOOLING. Not agent runtime: nothing here is loaded by the substrate, and
the CLAUDE.md runtime rules (integer frames, no Python decisions) do not apply.

Why this exists: retrieval recall does not guarantee task success. The studies
cited in docs/features/DEV_TOOLING_V2_PLAN.md (arXiv 2611.07286, 2610.33958)
report that better retrieval often leaves the end result unchanged. This
harness measures the end result: can an agent, given a symptom, make a failing
test pass again?

Each task is a break/fix case (see docs/features/AGENT_E2E_EVAL.md):

  1. A fresh detached git worktree is created at the base commit.
  2. The task's check (a pytest node-id list) must PASS on the base.
  3. The task's break patch is applied. The check must now FAIL.
  4. For a run, the driver (the agent under test) gets the task prompt in the
     broken worktree. The check then decides success.

Drivers:
  noop    does nothing. Expected success 0%. Negative control.
  fake    reverts the break patch with `git apply -R`. Expected success 100%.
          Validates the harness, not any agent.
  claude  Claude Code CLI in print mode. LIVE ONLY, untested live.
  opencode  OpenCode CLI in `run` mode. LIVE ONLY, untested live.

Arms:
  baseline    no Ocelot MCP server. Claude Code runs with --strict-mcp-config.
  dev_memory  Ocelot dev-memory MCP server (scripts.ocelot_dev_memory_mcp)
              registered through a config file written into the workdir.

Live drivers refuse to run unless both `--live` and the environment variable
OCELOT_AGENT_EVAL_LIVE=1 are set. A live run spends hosted-model tokens and
needs explicit user approval.

Usage:

    .venv/bin/python -m scripts.ocelot_agent_eval validate
    .venv/bin/python -m scripts.ocelot_agent_eval run --driver fake \\
        --arms baseline,dev_memory --out-json out.json --out-md out.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS = ROOT / "evaluation" / "agent_e2e" / "tasks.json"
DEFAULT_RUN_ROOT = Path("/tmp/ocelot_agent_eval")
ARMS = ("baseline", "dev_memory")
LIVE_ENV = "OCELOT_AGENT_EVAL_LIVE"
MCP_SERVER_NAME = "ocelot-dev-memory"
MCP_MODULE = "scripts.ocelot_dev_memory_mcp"
MCP_CONFIG_CLAUDE = ".ocelot_agent_eval_mcp.json"
MCP_CONFIG_OPENCODE = ".ocelot_agent_eval_opencode.json"
TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LIVE_DRIVERS = ("claude", "opencode")
LOCAL_DRIVERS = ("noop", "fake")
# A driver error that means no session can succeed; the run stops at once.
_AUTH_ERROR_RE = re.compile(r"authenticat|not logged in|invalid api key|oauth",
                            re.IGNORECASE)


class HarnessError(RuntimeError):
    """A harness step failed for a reason the operator must fix."""


class LiveRunNotApproved(HarnessError):
    """A live driver was requested without both --live and the env flag."""


# --------------------------------------------------------------------------- #
# tasks
# --------------------------------------------------------------------------- #
def load_tasks(path: str | Path) -> dict[str, Any]:
    """Load and check a task file. Returns {"base", "tasks", "path"}."""
    path = Path(path).resolve()
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise HarnessError(f"{path}: expected an object with version 1")
    tasks = doc.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise HarnessError(f"{path}: 'tasks' must be a non-empty list")
    seen: set[str] = set()
    for task in tasks:
        _check_task(task, path.parent, seen)
    return {"base": doc.get("base"), "tasks": tasks, "path": str(path),
            "dir": str(path.parent)}


def _check_task(task: Any, tasks_dir: Path, seen: set[str]) -> None:
    if not isinstance(task, dict):
        raise HarnessError("every task must be an object")
    tid = task.get("id")
    if not isinstance(tid, str) or not TASK_ID_RE.match(tid):
        raise HarnessError(f"invalid task id: {tid!r}")
    if tid in seen:
        raise HarnessError(f"duplicate task id: {tid}")
    seen.add(tid)
    for key in ("prompt", "area", "break_patch", "notes"):
        if not isinstance(task.get(key), str) or not task[key].strip():
            raise HarnessError(f"{tid}: '{key}' must be a non-empty string")
    if not (tasks_dir / task["break_patch"]).is_file():
        raise HarnessError(f"{tid}: break_patch not found: {task['break_patch']}")
    check = task.get("check")
    if not isinstance(check, dict):
        raise HarnessError(f"{tid}: 'check' must be an object")
    argv = check.get("argv")
    if (not isinstance(argv, list) or not argv
            or not all(isinstance(a, str) for a in argv)):
        raise HarnessError(f"{tid}: check.argv must be a non-empty list of strings")
    timeout = check.get("timeout_s")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise HarnessError(f"{tid}: check.timeout_s must be a positive integer")
    expected = task.get("expected_files")
    if (not isinstance(expected, list) or not expected
            or not all(isinstance(f, str) and f for f in expected)):
        raise HarnessError(f"{tid}: expected_files must be a non-empty list of paths")


def select_tasks(tasks: list[dict[str, Any]],
                 ids: Iterable[str] | None) -> list[dict[str, Any]]:
    """Tasks in id order, optionally restricted to `ids`."""
    ordered = sorted(tasks, key=lambda t: t["id"])
    if ids is None:
        return ordered
    wanted = {str(i).strip() for i in ids if str(i).strip()}
    known = {t["id"] for t in ordered}
    unknown = sorted(wanted - known)
    if unknown:
        raise HarnessError(f"unknown task ids: {', '.join(unknown)}")
    return [t for t in ordered if t["id"] in wanted]


# --------------------------------------------------------------------------- #
# git and worktrees
# --------------------------------------------------------------------------- #
def _git(args: list[str], cwd: str | Path, *, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        raise HarnessError(
            f"git {' '.join(args)} failed in {cwd}: {proc.stderr.strip()}")
    return proc


def new_run_root(base_dir: str | Path = DEFAULT_RUN_ROOT) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    run_root = Path(base_dir) / f"{stamp}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    run_root.mkdir(parents=True, exist_ok=True)
    return run_root


def make_workdir(repo: str | Path, base: str, run_root: Path, name: str) -> Path:
    """A detached worktree at `base` under run_root/work/<name>."""
    path = run_root / "work" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(["worktree", "add", "--detach", str(path), base], repo)
    return path


def _worktree_admin_dir(path: Path) -> Path | None:
    """The admin dir a linked worktree points at, read from its `.git` file."""
    try:
        text = (path / ".git").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text.startswith("gitdir:"):
        return None
    admin = Path(text.split(":", 1)[1].strip())
    return admin if admin.is_absolute() else (path / admin).resolve()


def remove_workdir(repo: str | Path, path: Path, run_root: Path) -> list[str]:
    """Remove a worktree the harness created under run_root/work.

    Only this worktree is touched. There is no repo-wide `git worktree prune`,
    because that would also drop the admin entries of unrelated worktrees whose
    directories are missing. If `git worktree remove --force` fails, the
    directory is deleted and this worktree's own admin dir (under
    `<common git dir>/worktrees/`) is deleted too. Returns warnings; an empty
    list means the cleanup was complete.
    """
    owned = (run_root.resolve() / "work").resolve()
    if owned not in path.resolve().parents:
        raise HarnessError(f"refusing to remove a path the harness did not create: {path}")
    admin = _worktree_admin_dir(path)
    proc = _git(["worktree", "remove", "--force", str(path)], repo, check=False)
    warnings: list[str] = []
    if proc.returncode == 0 and not path.exists():
        return warnings
    warnings.append("git worktree remove --force failed: "
                    + (proc.stderr.strip() or f"exit {proc.returncode}"))
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        warnings.append(f"directory still present after cleanup: {path}")
    common = _git(["rev-parse", "--git-common-dir"], repo, check=False)
    if admin is not None and common.returncode == 0:
        common_dir = (Path(repo) / common.stdout.strip()).resolve()
        worktrees_dir = (common_dir / "worktrees").resolve()
        if worktrees_dir in admin.resolve().parents and admin.exists():
            shutil.rmtree(admin, ignore_errors=True)
            warnings.append(f"removed admin entry {admin.name} by hand")
    return warnings


def apply_patch(workdir: Path, patch: Path, *, reverse: bool = False) -> dict[str, Any]:
    args = ["apply", "--whitespace=nowarn"]
    if reverse:
        args.append("-R")
    args.append(str(patch))
    proc = _git(args, workdir, check=False)
    return {"ok": proc.returncode == 0,
            "output": (proc.stdout + proc.stderr).strip()}


def _snapshot(workdir: Path) -> dict[str, str | None]:
    """Content digest of every modified, deleted or untracked file."""
    proc = _git(["ls-files", "-z", "-m", "-d", "-o", "--exclude-standard"], workdir)
    snap: dict[str, str | None] = {}
    for rel in sorted(p for p in proc.stdout.split("\0") if p):
        target = workdir / rel
        if target.is_file():
            snap[rel] = hashlib.sha256(target.read_bytes()).hexdigest()
        else:
            snap[rel] = None
    return snap


def changed_since(before: dict[str, str | None],
                  after: dict[str, str | None]) -> list[str]:
    keys = set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k))


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def _tail(text: str, lines: int = 30) -> str:
    return "\n".join(text.splitlines()[-lines:])


KILL_GRACE_S = 5.0


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def spawn_group(argv: list[str], *, cwd: str | Path, env: dict[str, str],
                timeout_s: float) -> dict[str, Any]:
    """Run argv in its own session and process group, with a time limit.

    On timeout the whole group gets SIGTERM, the harness waits up to
    KILL_GRACE_S for it to exit, and then SIGKILL is sent to the group. The
    driver's children (an MCP server, a language server, a sleeping shell) are
    killed with it, so they do not outlive the run.
    """
    started = time.monotonic()
    proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                            text=True, encoding="utf-8",
                            errors="replace", start_new_session=True)
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        pgid = proc.pid
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + KILL_GRACE_S
        while time.monotonic() < deadline:
            proc.poll()  # reaps the leader so only real survivors keep the group
            if not _group_alive(pgid):
                break
            time.sleep(0.05)
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            out, err = proc.communicate(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = "", ""
    return {"returncode": None if timed_out else proc.returncode,
            "stdout": out or "", "stderr": err or "", "timed_out": timed_out,
            "seconds": round(time.monotonic() - started, 3)}


def run_check(workdir: Path, check: dict[str, Any], python: str,
              log_path: Path) -> dict[str, Any]:
    argv = [a.replace("{workdir}", str(workdir)) for a in check["argv"]]
    cmd = [python, *argv]
    timeout = int(check["timeout_s"])
    # No .pyc files: a break that keeps the byte length (a + b -> a - b) within the
    # same mtime second would otherwise run stale bytecode from the base check.
    env = dict(os.environ, COLUMNS="250", PYTHONDONTWRITEBYTECODE="1")
    res = spawn_group(cmd, cwd=workdir, env=env, timeout_s=timeout)
    out, err = res["stdout"], res["stderr"]
    returncode, timed_out = res["returncode"], res["timed_out"]
    seconds = res["seconds"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(f"$ {' '.join(cmd)}\n\n{out}\n--- stderr ---\n{err}\n",
                        encoding="utf-8")
    return {"passed": (not timed_out) and returncode == 0,
            "returncode": returncode, "timed_out": timed_out,
            "seconds": seconds, "log": str(log_path),
            "tail": _tail(out + "\n" + err, 12)}


# --------------------------------------------------------------------------- #
# validation: pass on base, fail after the break
# --------------------------------------------------------------------------- #
def validate_task(repo: str | Path, task: dict[str, Any], base: str, *,
                  tasks_dir: str | Path = DEFAULT_TASKS.parent,
                  python: str | None = None, run_root: Path | None = None,
                  keep: bool = False) -> dict[str, Any]:
    python = python or sys.executable
    run_root = run_root or new_run_root()
    log_dir = run_root / "logs"
    tid = task["id"]
    started = time.monotonic()
    workdir = make_workdir(repo, base, run_root, f"validate-{tid}")
    cleanup: list[str] = []
    try:
        base_check = run_check(workdir, task["check"], python,
                               log_dir / f"validate-{tid}-base.log")
        applied = apply_patch(workdir, Path(tasks_dir) / task["break_patch"])
        broken_check: dict[str, Any] | None = None
        if applied["ok"]:
            broken_check = run_check(workdir, task["check"], python,
                                     log_dir / f"validate-{tid}-broken.log")
        pass_on_base = base_check["passed"]
        fail_after_break = broken_check is not None and not broken_check["passed"]
        ok = bool(pass_on_base and applied["ok"] and fail_after_break)
        details: dict[str, Any] = {
            "base_check": {k: base_check[k] for k in ("returncode", "seconds", "log")},
            "break_apply": applied,
        }
        if broken_check is not None:
            details["broken_check"] = {k: broken_check[k]
                                       for k in ("returncode", "seconds", "log")}
        if not ok:
            details["reason"] = _validation_reason(pass_on_base, applied["ok"],
                                                   fail_after_break)
        result = {"id": tid, "ok": ok, "pass_on_base": pass_on_base,
                  "fail_after_break": fail_after_break,
                  "seconds": round(time.monotonic() - started, 3),
                  "details": details, "cleanup_warnings": cleanup}
        if keep:
            result["workdir"] = str(workdir)
        return result
    finally:
        if not keep:
            cleanup.extend(remove_workdir(repo, workdir, run_root))


def _validation_reason(pass_on_base: bool, applied: bool, fail_after_break: bool) -> str:
    if not pass_on_base:
        return "check does not pass on base"
    if not applied:
        return "break patch does not apply to base"
    if not fail_after_break:
        return "check still passes after the break patch"
    return "unknown"


def validate_all(repo: str | Path, tasks: list[dict[str, Any]], base: str, *,
                 tasks_dir: str | Path, python: str | None = None,
                 run_root: Path | None = None, keep: bool = False) -> dict[str, Any]:
    run_root = run_root or new_run_root()
    results = [validate_task(repo, t, base, tasks_dir=tasks_dir, python=python,
                             run_root=run_root, keep=keep) for t in tasks]
    return {"version": 1, "base": base, "run_root": str(run_root),
            "ok": all(r["ok"] for r in results), "results": results}


# --------------------------------------------------------------------------- #
# drivers
# --------------------------------------------------------------------------- #
def _empty_result(**fields: Any) -> dict[str, Any]:
    out = {"exit_code": None, "wall_s": 0.0, "tokens_in": None,
           "tokens_out": None, "cost_usd": None, "tool_calls": None,
           "transcript": "", "timed_out": False, "driver_error": None}
    out.update(fields)
    return out


class NoopDriver:
    """Does nothing. Negative control; expected success 0%."""
    name = "noop"

    def run(self, workdir: Path, prompt: str, arm: str, timeout_s: int,
            log_dir: Path, *, patch_path: Path | None = None) -> dict[str, Any]:
        return _empty_result(exit_code=0)


class FakeDriver:
    """Reverts the break patch. A perfect agent, used to validate the harness."""
    name = "fake"

    def run(self, workdir: Path, prompt: str, arm: str, timeout_s: int,
            log_dir: Path, *, patch_path: Path | None = None) -> dict[str, Any]:
        if patch_path is None:
            raise HarnessError("fake driver needs the task's break patch")
        started = time.monotonic()
        applied = apply_patch(workdir, patch_path, reverse=True)
        return _empty_result(exit_code=0 if applied["ok"] else 1,
                             wall_s=round(time.monotonic() - started, 3),
                             transcript=applied["output"])


def _parse_claude_json(stdout: str) -> dict[str, Any]:
    """Fields from `claude -p --output-format json`: result, total_cost_usd and
    usage.{input_tokens,output_tokens}. Names confirmed in the installed
    binary's strings (version 2.1.322), not by a live run."""
    try:
        doc = json.loads(stdout)
    except ValueError:
        return {}
    if not isinstance(doc, dict):
        return {}
    usage = doc.get("usage") if isinstance(doc.get("usage"), dict) else {}

    def number(value: Any) -> Any:
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    error = None
    if doc.get("is_error") or doc.get("terminal_reason") == "api_error":
        error = str(doc.get("result") or doc.get("terminal_reason") or "error")
    return {"tokens_in": number(usage.get("input_tokens")),
            "tokens_out": number(usage.get("output_tokens")),
            "cost_usd": number(doc.get("total_cost_usd")),
            "driver_error": error,
            "transcript": doc["result"] if isinstance(doc.get("result"), str) else stdout}


# argv templates. "{prompt}" and "{mcp_config}" are replaced as whole tokens.
# Git subcommands that move or rewrite shared refs. Bash stays allowed for the
# rest. Residual risk: a pattern matches the command's text, so `git -C dir
# commit` or `git --git-dir=... push` gets past it. See AGENT_E2E_EVAL.md.
DISALLOWED_GIT_TOOLS = (
    "Bash(git commit:*)", "Bash(git push:*)", "Bash(git stash:*)",
    "Bash(git branch:*)", "Bash(git checkout:*)", "Bash(git switch:*)",
    "Bash(git reset:*)", "Bash(git rebase:*)", "Bash(git merge:*)",
    "Bash(git tag:*)", "Bash(git worktree:*)",
)
DRIVERS: dict[str, dict[str, Any]] = {
    "claude": {
        "argv": ["claude", "-p", "{prompt}", "--output-format", "json",
                 "--permission-mode", "acceptEdits", "--no-session-persistence",
                 "--allowedTools", "Read,Edit,Write,Glob,Grep,Bash",
                 # Refs are shared with the canonical checkout (detached worktrees
                 # share refs and stash), so the agent may not move them.
                 # Comma-joined: one token, and the next token is a flag.
                 "--disallowedTools", ",".join(DISALLOWED_GIT_TOOLS)],
        "arm_argv": {
            "baseline": ["--strict-mcp-config"],
            "dev_memory": ["--strict-mcp-config", "--mcp-config", "{mcp_config}"],
        },
        "mcp_config_file": MCP_CONFIG_CLAUDE,
        "parse": _parse_claude_json,
    },
    "opencode": {
        "argv": ["opencode", "run", "--format", "json", "--auto", "{prompt}"],
        "arm_argv": {"baseline": [], "dev_memory": []},
        "arm_env": {"baseline": {}, "dev_memory": {"OPENCODE_CONFIG": "{mcp_config}"}},
        "mcp_config_file": MCP_CONFIG_OPENCODE,
        "parse": lambda stdout: {"transcript": stdout},
    },
}


class CommandDriver:
    """A live CLI agent. Built only through make_driver, which enforces approval."""

    def __init__(self, name: str, *, max_budget_usd: float | None = None) -> None:
        self.name = name
        self.spec = DRIVERS[name]
        self.max_budget_usd = max_budget_usd

    def _argv(self, prompt: str, arm: str, mcp_config: Path | None) -> list[str]:
        argv = list(self.spec["argv"])
        argv.extend(self.spec["arm_argv"].get(arm, []))
        if self.max_budget_usd is not None and self.name == "claude":
            argv.extend(["--max-budget-usd", str(self.max_budget_usd)])
        out = []
        for token in argv:
            if token == "{prompt}":
                out.append(prompt)
            elif token == "{mcp_config}":
                if mcp_config is None:
                    raise HarnessError(f"{self.name} arm {arm} needs an MCP config")
                out.append(str(mcp_config))
            else:
                out.append(token)
        return out

    def run(self, workdir: Path, prompt: str, arm: str, timeout_s: int,
            log_dir: Path, *, patch_path: Path | None = None) -> dict[str, Any]:
        _require_live_env(self.name)
        mcp = workdir / self.spec["mcp_config_file"] if arm == "dev_memory" else None
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for key, value in self.spec.get("arm_env", {}).get(arm, {}).items():
            env[key] = value.replace("{mcp_config}", str(mcp))
        argv = self._argv(prompt, arm, mcp)
        log_dir.mkdir(parents=True, exist_ok=True)
        res = spawn_group(argv, cwd=workdir, env=env, timeout_s=timeout_s)
        code, out, err = res["returncode"], res["stdout"], res["stderr"]
        timed_out, wall = res["timed_out"], res["seconds"]
        (log_dir / "driver.stdout.txt").write_text(out, encoding="utf-8")
        (log_dir / "driver.stderr.txt").write_text(err, encoding="utf-8")
        parsed = self.spec["parse"](out)
        return _empty_result(exit_code=code, wall_s=wall, timed_out=timed_out,
                             tokens_in=parsed.get("tokens_in"),
                             tokens_out=parsed.get("tokens_out"),
                             cost_usd=parsed.get("cost_usd"),
                             driver_error=parsed.get("driver_error"),
                             transcript=parsed.get("transcript", out))

    def preflight(self) -> None:
        """Refuse before any worktree is made when the CLI cannot authenticate.

        `claude auth status` makes no model call. An API key in the
        environment also counts as credentials.
        """
        if self.name != "claude":
            return
        if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get(
                "CLAUDE_CODE_OAUTH_TOKEN"):
            return
        try:
            proc = subprocess.run(["claude", "auth", "status"], capture_output=True,
                                  text=True, timeout=30, stdin=subprocess.DEVNULL)
            status = json.loads(proc.stdout or "{}")
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise HarnessError(f"claude auth status failed: {exc}") from exc
        if not status.get("loggedIn"):
            raise HarnessError(
                "claude is not logged in (claude auth status: loggedIn=false). "
                "Run `claude` and /login, or set ANTHROPIC_API_KEY, then retry.")


def _require_live_env(name: str) -> None:
    if os.environ.get(LIVE_ENV) != "1":
        raise LiveRunNotApproved(
            f"driver {name!r} makes hosted-model calls. Set {LIVE_ENV}=1 and pass --live.")


def make_driver(name: str, *, live: bool = False,
                max_budget_usd: float | None = None) -> Any:
    if name in LOCAL_DRIVERS:
        return {"noop": NoopDriver, "fake": FakeDriver}[name]()
    if name in LIVE_DRIVERS:
        if not live or os.environ.get(LIVE_ENV) != "1":
            raise LiveRunNotApproved(
                f"driver {name!r} makes hosted-model calls and needs both --live "
                f"and {LIVE_ENV}=1. Get user approval first.")
        return CommandDriver(name, max_budget_usd=max_budget_usd)
    raise HarnessError(f"unknown driver: {name}")


def write_arm_config(workdir: Path, arm: str, python: str, log_dir: Path) -> list[Path]:
    """Write the MCP registration for an arm into the workdir.

    baseline writes nothing. dev_memory writes one Claude Code file and one
    OpenCode file. Both start the same stdio server with a snapshot and a journal
    kept under log_dir, so the workdir stays clean. The files are untracked and
    are written before the change snapshot, so they never count as agent edits."""
    if arm == "baseline":
        return []
    if arm != "dev_memory":
        raise HarnessError(f"unknown arm: {arm}")
    env = {
        "PYTHONPATH": str(workdir),
        "OCELOT_DEV_ROOT": str(workdir),
        "OCELOT_DEV_DUMP": str(log_dir / "dev_graph.json"),
        "OCELOT_DEV_JOURNAL": str(log_dir / "journal.jsonl"),
        # The snapshot is built by prepare_dev_memory before the driver starts,
        # so the server never builds it inside the timed agent session.
        "OCELOT_DEV_AUTOBUILD": "0",
    }
    log_dir.mkdir(parents=True, exist_ok=True)
    claude_doc = {"mcpServers": {MCP_SERVER_NAME: {
        "command": python, "args": ["-m", MCP_MODULE], "env": env}}}
    opencode_doc = {"$schema": "https://opencode.ai/config.json", "mcp": {
        MCP_SERVER_NAME: {"type": "local", "command": [python, "-m", MCP_MODULE],
                          "environment": env, "enabled": True}}}
    paths = [workdir / MCP_CONFIG_CLAUDE, workdir / MCP_CONFIG_OPENCODE]
    for path, doc in zip(paths, (claude_doc, opencode_doc)):
        path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return paths


# --------------------------------------------------------------------------- #
# run loop
# --------------------------------------------------------------------------- #
PREP_TIMEOUT_S = 900
_PREP_CODE = (
    "import sys\n"
    "from pathlib import Path\n"
    "from scripts.ocelot_dev_memory import build_index\n"
    "from scripts.ocelot_repo_map import update_tag_cache\n"
    "work = Path(sys.argv[1])\n"
    "build_index(work, Path(sys.argv[2]))\n"
    "update_tag_cache(work, cache_path=work / 'var' / 'ocelot_dev_tags.json')\n"
)


def prepare_dev_memory(workdir: Path, python: str, log_dir: Path) -> dict[str, Any]:
    """Build the dev-memory snapshot and warm the tag cache, outside the timer.

    Runs in a subprocess with the run's python and PYTHONPATH=workdir, so the
    snapshot describes the broken worktree. The graph dump goes to log_dir and
    the tag cache to workdir/var, which is gitignored and so not an agent edit.
    A failed prep is recorded in the run; the driver still runs and the check
    still decides, so a broken index shows up as a result, not a silent skip.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(workdir), PYTHONDONTWRITEBYTECODE="1",
               COLUMNS="250")
    res = spawn_group([python, "-c", _PREP_CODE, str(workdir),
                       str(log_dir / "dev_graph.json")],
                      cwd=workdir, env=env, timeout_s=PREP_TIMEOUT_S)
    ok = res["returncode"] == 0 and not res["timed_out"]
    (log_dir / "prep.log").write_text(
        f"{res['stdout']}\n--- stderr ---\n{res['stderr']}\n", encoding="utf-8")
    if ok:
        error = None
    elif res["timed_out"]:
        error = f"prep timed out after {PREP_TIMEOUT_S} s"
    else:
        error = _tail(res["stderr"], 12) or f"exit {res['returncode']}"
    return {"prep_s": res["seconds"], "prep_ok": ok, "prep_error": error}


def run_one(repo: str | Path, task: dict[str, Any], arm: str, repeat: int,
            driver: Any, base: str, *, tasks_dir: str | Path, python: str,
            run_root: Path, timeout_s: int, keep: bool) -> dict[str, Any]:
    tid = task["id"]
    name = f"{tid}-{arm}-r{repeat}"
    log_dir = run_root / "logs" / name
    workdir = make_workdir(repo, base, run_root, name)
    cleanup: list[str] = []
    record: dict[str, Any] = {"task": tid, "arm": arm, "repeat": repeat,
                              "driver": driver.name, "prep_s": 0.0,
                              "prep_ok": None, "prep_error": None,
                              "cleanup_warnings": cleanup}
    try:
        patch = Path(tasks_dir) / task["break_patch"]
        applied = apply_patch(workdir, patch)
        if not applied["ok"]:
            record.update(success=False, error="break patch does not apply",
                          files_changed=[], localized=False, wall_s=0.0)
            return record
        write_arm_config(workdir, arm, python, log_dir)
        if arm == "dev_memory":
            prep = prepare_dev_memory(workdir, python, log_dir)
            record.update(prep_s=prep["prep_s"], prep_ok=prep["prep_ok"],
                          prep_error=prep["prep_error"])
        before = _snapshot(workdir)
        result = driver.run(workdir, task["prompt"], arm, timeout_s, log_dir,
                            patch_path=patch)
        after = _snapshot(workdir)
        files_changed = changed_since(before, after)
        check = run_check(workdir, task["check"], python, log_dir / "check.log")
        expected = [f.replace("\\", "/") for f in task["expected_files"]]
        record.update(
            success=check["passed"],
            check_returncode=check["returncode"],
            check_s=check["seconds"],
            exit_code=result["exit_code"],
            wall_s=result["wall_s"],
            timed_out=result["timed_out"],
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost_usd=result["cost_usd"],
            tool_calls=result["tool_calls"],
            driver_error=result.get("driver_error"),
            files_changed=files_changed,
            localized=any(f in files_changed for f in expected),
            diff_vs_base=_git(["diff", "--name-only", base], workdir).stdout.split(),
            log_dir=str(log_dir),
        )
        (log_dir / "transcript.txt").write_text(result["transcript"] or "", encoding="utf-8")
        return record
    finally:
        if not keep:
            cleanup.extend(remove_workdir(repo, workdir, run_root))
        else:
            record["workdir"] = str(workdir)


def run_eval(repo: str | Path, tasks: list[dict[str, Any]], arms: Iterable[str],
             driver: Any, base: str, *, tasks_dir: str | Path = DEFAULT_TASKS.parent,
             repeats: int = 1, python: str | None = None, run_root: Path | None = None,
             keep: bool = False, timeout_s: int = 900) -> dict[str, Any]:
    arms = list(arms)
    unknown = [a for a in arms if a not in ARMS]
    if unknown:
        raise HarnessError(f"unknown arms: {', '.join(unknown)}")
    if repeats < 1:
        raise HarnessError("repeats must be at least 1")
    python = python or sys.executable
    run_root = run_root or new_run_root()
    ordered_arms = [a for a in ARMS if a in arms]
    runs: list[dict[str, Any]] = []
    preflight = getattr(driver, "preflight", None)
    if callable(preflight):
        preflight()
    for task in sorted(tasks, key=lambda t: t["id"]):
        for arm in ordered_arms:
            for repeat in range(1, repeats + 1):
                record = run_one(repo, task, arm, repeat, driver, base,
                                 tasks_dir=tasks_dir, python=python,
                                 run_root=run_root, timeout_s=timeout_s,
                                 keep=keep)
                runs.append(record)
                if _AUTH_ERROR_RE.search(str(record.get("driver_error") or "")):
                    raise HarnessError(
                        f"driver cannot authenticate ({record['driver_error']}); "
                        f"stopped after {len(runs)} run(s). Logs: {run_root}")
    return {"version": 1, "base": base, "driver": driver.name,
            "arms": ordered_arms, "repeats": repeats,
            "tasks": [t["id"] for t in sorted(tasks, key=lambda t: t["id"])],
            "run_root": str(run_root),
            "runs": runs,
            "summary": aggregate(runs, ordered_arms),
            "per_task": paired(runs, ordered_arms)}


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #
def _mean(values: Iterable[Any], digits: int = 3) -> float | None:
    known = [float(v) for v in values if v is not None]
    return round(sum(known) / len(known), digits) if known else None


def aggregate(runs: list[dict[str, Any]], arms: Iterable[str]) -> list[dict[str, Any]]:
    rows = []
    for arm in arms:
        mine = [r for r in runs if r["arm"] == arm]
        n = len(mine)
        successes = sum(1 for r in mine if r.get("success") is True)
        rows.append({
            "arm": arm,
            "runs": n,
            "successes": successes,
            "success_rate": round(successes / n, 4) if n else None,
            "mean_wall_s": _mean(r.get("wall_s") for r in mine),
            "mean_prep_s": _mean((r.get("prep_s") for r in mine), 1),
            "prep_failures": sum(1 for r in mine if r.get("prep_ok") is False),
            "driver_errors": sum(1 for r in mine if r.get("driver_error")),
            "tokens_known_runs": sum(1 for r in mine if r.get("tokens_in") is not None),
            "mean_tokens_in": _mean((r.get("tokens_in") for r in mine), 1),
            "mean_tokens_out": _mean((r.get("tokens_out") for r in mine), 1),
            "mean_cost_usd": _mean((r.get("cost_usd") for r in mine), 4),
            "localization_rate": round(sum(1 for r in mine if r.get("localized")) / n, 4)
            if n else None,
        })
    return rows


def paired(runs: list[dict[str, Any]], arms: Iterable[str]) -> dict[str, Any]:
    """Per task, the success outcome of each repeat, for each arm."""
    arms = list(arms)
    out: dict[str, Any] = {}
    for tid in sorted({r["task"] for r in runs}):
        row: dict[str, Any] = {}
        for arm in arms:
            outcomes = [r.get("success") is True for r in sorted(
                (r for r in runs if r["task"] == tid and r["arm"] == arm),
                key=lambda r: r["repeat"])]
            row[arm] = {"outcomes": outcomes,
                        "successes": sum(outcomes),
                        "repeats": len(outcomes)}
        out[tid] = row
    return out


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Agent end-to-end evaluation",
        "",
        f"- Driver: `{report['driver']}`"
        + (" (untested live: see docs/features/AGENT_E2E_EVAL.md)"
           if report["driver"] in LIVE_DRIVERS else ""),
        f"- Base: `{report['base']}`",
        f"- Arms: {', '.join(report['arms'])}",
        f"- Repeats per task and arm: {report['repeats']}",
        f"- Tasks: {len(report['tasks'])}",
        "",
        "## Per arm",
        "",
        "| arm | runs | success | success rate | mean wall s | mean prep s | "
        "prep failures | driver errors | mean tokens in | "
        "mean tokens out | mean cost USD | localization rate |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in report["summary"]:
        lines.append("| " + " | ".join(_cell(v) for v in (
            row["arm"], row["runs"], row["successes"], row["success_rate"],
            row["mean_wall_s"], row["mean_prep_s"], row["prep_failures"],
            row.get("driver_errors", 0),
            row["mean_tokens_in"], row["mean_tokens_out"],
            row["mean_cost_usd"], row["localization_rate"])) + " |")
    lines += ["", "Token and cost columns are blank where the driver reports no value. "
              "Prep (dev_memory snapshot and tag cache) runs before the driver timer; "
              "mean prep s is 0 for baseline.",
              "", "## Per task (paired)", ""]
    header = "| task | " + " | ".join(report["arms"]) + " |"
    lines += [header, "|---" * (len(report["arms"]) + 1) + "|"]
    for tid, row in report["per_task"].items():
        cells = [f"{row[a]['successes']}/{row[a]['repeats']}" for a in report["arms"]]
        lines.append(f"| {_cell(tid)} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _split(text: str | None) -> list[str] | None:
    if text is None:
        return None
    return [p.strip() for p in text.split(",") if p.strip()]


def _write(path: str | None, text: str) -> None:
    if path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")


def _cmd_validate(args: argparse.Namespace) -> int:
    spec = load_tasks(args.tasks)
    base = args.base or spec["base"]
    tasks = select_tasks(spec["tasks"], _split(args.task_ids))
    report = validate_all(args.repo, tasks, base, tasks_dir=spec["dir"],
                          python=args.python, run_root=_run_root(args),
                          keep=args.keep)
    for r in report["results"]:
        print(f"{'ok  ' if r['ok'] else 'FAIL'} {r['id']}: pass_on_base={r['pass_on_base']} "
              f"fail_after_break={r['fail_after_break']} "
              + ("" if r["ok"] else f"({r['details'].get('reason')})"))
    _write(args.out_json, json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["ok"] else 1


def _run_root(args: argparse.Namespace) -> Path:
    return Path(args.run_root) if args.run_root else new_run_root()


def _cmd_run(args: argparse.Namespace) -> int:
    spec = load_tasks(args.tasks)
    base = args.base or spec["base"]
    arms = _split(args.arms) or list(ARMS)
    tasks = select_tasks(spec["tasks"], _split(args.task_ids))
    driver = make_driver(args.driver, live=args.live,
                         max_budget_usd=args.max_budget_usd)
    report = run_eval(args.repo, tasks, arms, driver, base,
                      tasks_dir=spec["dir"], repeats=args.repeats,
                      python=args.python, run_root=_run_root(args),
                      keep=args.keep, timeout_s=args.timeout_s)
    _write(args.out_json, json.dumps(report, indent=2, sort_keys=True) + "\n")
    _write(args.out_md, render_markdown(report))
    for row in report["summary"]:
        print(f"{row['arm']}: {row['successes']}/{row['runs']} succeeded "
              f"(rate {row['success_rate']}), localized {row['localization_rate']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--tasks", default=str(DEFAULT_TASKS))
        sp.add_argument("--repo", default=str(ROOT), help="git repo to create worktrees from")
        sp.add_argument("--base", default=None, help="base commit (default: tasks file)")
        sp.add_argument("--task-ids", default=None, help="comma-separated subset")
        sp.add_argument("--python", default=None,
                        help="python for checks and the MCP server (default: this one)")
        sp.add_argument("--run-root", default=None,
                        help="scratch root (default: a new dir under /tmp/ocelot_agent_eval)")
        sp.add_argument("--keep", action="store_true", help="keep worktrees")
        sp.add_argument("--out-json", default=None)

    v = sub.add_parser("validate", help="check pass-on-base and fail-after-break")
    common(v)
    v.set_defaults(func=_cmd_validate)

    r = sub.add_parser("run", help="run drivers over tasks and arms")
    common(r)
    r.add_argument("--driver", required=True,
                   choices=sorted(LOCAL_DRIVERS + LIVE_DRIVERS))
    r.add_argument("--arms", default=",".join(ARMS))
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--timeout-s", type=int, default=900,
                   help="wall-clock limit per driver session")
    r.add_argument("--live", action="store_true",
                   help="required, with OCELOT_AGENT_EVAL_LIVE=1, for claude and opencode")
    r.add_argument("--max-budget-usd", type=float, default=None,
                   help="claude only: passed as --max-budget-usd")
    r.add_argument("--out-md", default=None)
    r.set_defaults(func=_cmd_run)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except LiveRunNotApproved as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
