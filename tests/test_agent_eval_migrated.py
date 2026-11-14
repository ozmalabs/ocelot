"""tests/test_agent_eval_migrated.py -- hermetic gates for scripts/ocelot_agent_eval.py.

Every test runs against a tiny git repository built in tmp_path (git init and a commit
with `-c user.name=t -c user.email=t@t`; no global git config is touched). No model is
called. The live drivers are only checked for refusal, never executed.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts import ocelot_agent_eval as ae
from scripts.ocelot_agent_eval import (
    ARMS,
    LIVE_ENV,
    CommandDriver,
    FakeDriver,
    HarnessError,
    LiveRunNotApproved,
    NoopDriver,
    aggregate,
    load_tasks,
    main,
    make_driver,
    paired,
    render_markdown,
    run_eval,
    select_tasks,
    validate_task,
    write_arm_config,
)

ROOT = Path(__file__).resolve().parent.parent

MOD_SRC = "def add(a, b):\n    return a + b\n"
TEST_SRC = (
    "from pkg.mod import add\n\n\n"
    "def test_add():\n    assert add(1, 2) == 3\n"
)
BREAK_SIGN = (
    "--- a/pkg/mod.py\n+++ b/pkg/mod.py\n@@ -1,2 +1,2 @@\n"
    " def add(a, b):\n-    return a + b\n+    return a - b\n"
)
BREAK_COMMENT_ONLY = (
    "--- a/pkg/mod.py\n+++ b/pkg/mod.py\n@@ -1,2 +1,3 @@\n"
    " def add(a, b):\n     return a + b\n+# harmless\n"
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _repo(root: Path) -> tuple[Path, str]:
    repo = root / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "pkg" / "mod.py").write_text(MOD_SRC, encoding="utf-8")
    (repo / "tests" / "test_mod.py").write_text(TEST_SRC, encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo, _git(repo, "rev-parse", "HEAD")


def _task(tid: str, patch: str, node: str = "tests/test_mod.py::test_add") -> dict:
    return {
        "id": tid,
        "prompt": "addition gives the wrong sign",
        "area": "pkg",
        "break_patch": f"patches/{tid}.patch",
        "check": {"argv": ["-m", "pytest", "-q", "-p", "no:cacheprovider",
                           "--confcutdir={workdir}", node],
                  "timeout_s": 60},
        "expected_files": ["pkg/mod.py"],
        "notes": "fixture",
    }


def _tasks_dir(root: Path, tasks: list[tuple[dict, str]]) -> Path:
    tdir = root / "tasks"
    (tdir / "patches").mkdir(parents=True)
    for task, patch in tasks:
        (tdir / task["break_patch"]).write_text(patch, encoding="utf-8")
    return tdir


@pytest.fixture()
def fixture(tmp_path: Path):
    repo, base = _repo(tmp_path)
    sign = _task("add-sign", BREAK_SIGN)
    tdir = _tasks_dir(tmp_path, [(sign, BREAK_SIGN)])
    return {"repo": repo, "base": base, "tdir": tdir, "sign": sign,
            "run_root": tmp_path / "runs"}


def _worktrees(repo: Path) -> list[str]:
    out = _git(repo, "worktree", "list", "--porcelain")
    return [line.split(" ", 1)[1] for line in out.splitlines()
            if line.startswith("worktree ")]


# ===================================================================================== #
# validation
# ===================================================================================== #
def test_validate_detects_pass_on_base_and_fail_after_break(fixture):
    res = validate_task(fixture["repo"], fixture["sign"], fixture["base"],
                        tasks_dir=fixture["tdir"], python=_python(),
                        run_root=fixture["run_root"])
    assert res["ok"] is True
    assert res["pass_on_base"] is True
    assert res["fail_after_break"] is True
    assert res["details"]["break_apply"]["ok"] is True


def test_task_whose_check_survives_the_break_is_rejected(tmp_path):
    repo, base = _repo(tmp_path)
    harmless = _task("comment-only", BREAK_COMMENT_ONLY)
    tdir = _tasks_dir(tmp_path, [(harmless, BREAK_COMMENT_ONLY)])
    res = validate_task(repo, harmless, base, tasks_dir=tdir, python=_python(),
                        run_root=tmp_path / "runs")
    assert res["ok"] is False
    assert res["pass_on_base"] is True
    assert res["fail_after_break"] is False
    assert res["details"]["reason"] == "check still passes after the break patch"


def test_check_failing_on_base_is_rejected(tmp_path):
    repo, base = _repo(tmp_path)
    missing = _task("no-such-test", BREAK_SIGN, node="tests/test_mod.py::test_nope")
    tdir = _tasks_dir(tmp_path, [(missing, BREAK_SIGN)])
    res = validate_task(repo, missing, base, tasks_dir=tdir, python=_python(),
                        run_root=tmp_path / "runs")
    assert res["ok"] is False
    assert res["pass_on_base"] is False
    assert res["details"]["reason"] == "check does not pass on base"


def test_validate_removes_its_workdir(fixture):
    validate_task(fixture["repo"], fixture["sign"], fixture["base"],
                  tasks_dir=fixture["tdir"], python=_python(),
                  run_root=fixture["run_root"])
    assert not any((fixture["run_root"] / "work").glob("*"))
    assert len(_worktrees(fixture["repo"])) == 1


# ===================================================================================== #
# drivers and runs
# ===================================================================================== #
def test_fake_driver_succeeds_and_noop_fails(fixture):
    tasks = [fixture["sign"]]
    fake = run_eval(fixture["repo"], tasks, ARMS, FakeDriver(), fixture["base"],
                    tasks_dir=fixture["tdir"], python=_python(),
                    run_root=fixture["run_root"])
    assert [r["success"] for r in fake["runs"]] == [True, True]
    assert all(r["localized"] for r in fake["runs"])
    assert all(r["files_changed"] == ["pkg/mod.py"] for r in fake["runs"])

    noop = run_eval(fixture["repo"], tasks, ["baseline"], NoopDriver(), fixture["base"],
                    tasks_dir=fixture["tdir"], python=_python(),
                    run_root=fixture["run_root"])
    assert [r["success"] for r in noop["runs"]] == [False]
    assert noop["runs"][0]["files_changed"] == []
    assert noop["runs"][0]["localized"] is False


def test_run_order_is_deterministic_and_repeats_are_recorded(fixture):
    other = _task("add-sign-b", BREAK_SIGN)
    (fixture["tdir"] / other["break_patch"]).write_text(BREAK_SIGN, encoding="utf-8")
    tasks = [other, fixture["sign"]]
    first = run_eval(fixture["repo"], tasks, ARMS, NoopDriver(), fixture["base"],
                     tasks_dir=fixture["tdir"], repeats=2, python=_python(),
                     run_root=fixture["run_root"])
    keys = [(r["task"], r["arm"], r["repeat"]) for r in first["runs"]]
    assert keys == sorted(keys, key=lambda k: (k[0], ARMS.index(k[1]), k[2]))
    assert len(keys) == 2 * len(ARMS) * 2
    assert first["tasks"] == ["add-sign", "add-sign-b"]


def test_workdirs_are_cleaned_up_after_a_run(fixture):
    run_eval(fixture["repo"], [fixture["sign"]], ARMS, FakeDriver(), fixture["base"],
             tasks_dir=fixture["tdir"], python=_python(),
             run_root=fixture["run_root"])
    assert len(_worktrees(fixture["repo"])) == 1
    assert not any((fixture["run_root"] / "work").glob("*"))


def test_harness_refuses_to_remove_a_path_it_did_not_create(fixture):
    with pytest.raises(HarnessError, match="did not create"):
        ae.remove_workdir(fixture["repo"], fixture["repo"], fixture["run_root"])


def test_dev_memory_arm_writes_mcp_config_into_workdir(tmp_path):
    log = tmp_path / "log"
    paths = write_arm_config(tmp_path, "dev_memory", "/usr/bin/python3", log)
    assert {p.name for p in paths} == {ae.MCP_CONFIG_CLAUDE, ae.MCP_CONFIG_OPENCODE}
    claude = json.loads((tmp_path / ae.MCP_CONFIG_CLAUDE).read_text(encoding="utf-8"))
    server = claude["mcpServers"][ae.MCP_SERVER_NAME]
    assert server["args"] == ["-m", "scripts.ocelot_dev_memory_mcp"]
    assert server["env"]["OCELOT_DEV_ROOT"] == str(tmp_path)
    # The snapshot is prepared before the driver starts, so the server must not
    # rebuild it inside the timed session.
    assert server["env"]["OCELOT_DEV_AUTOBUILD"] == "0"
    assert server["env"]["OCELOT_DEV_DUMP"] == str(log / "dev_graph.json")
    opencode = json.loads((tmp_path / ae.MCP_CONFIG_OPENCODE).read_text(encoding="utf-8"))
    assert ae.MCP_SERVER_NAME in opencode["mcp"]


def test_baseline_arm_writes_no_mcp_config(tmp_path):
    assert write_arm_config(tmp_path, "baseline", "python", tmp_path / "log") == []
    assert list(tmp_path.iterdir()) == []


def test_claude_command_uses_strict_mcp_flags_per_arm(tmp_path):
    driver = CommandDriver("claude")
    base_argv = driver._argv("p", "baseline", None)
    assert "--strict-mcp-config" in base_argv
    assert "--mcp-config" not in base_argv
    cfg = tmp_path / ae.MCP_CONFIG_CLAUDE
    dm_argv = driver._argv("p", "dev_memory", cfg)
    assert dm_argv[dm_argv.index("--mcp-config") + 1] == str(cfg)
    assert dm_argv[dm_argv.index("-p") + 1] == "p"


def test_claude_json_parser_reads_result_cost_and_usage():
    doc = json.dumps({"result": "done", "total_cost_usd": 0.25,
                      "usage": {"input_tokens": 120, "output_tokens": 30}})
    parsed = ae._parse_claude_json(doc)
    assert parsed == {"tokens_in": 120, "tokens_out": 30, "cost_usd": 0.25,
                      "transcript": "done"}
    assert ae._parse_claude_json("not json") == {}


# ===================================================================================== #
# live gating
# ===================================================================================== #
@pytest.mark.parametrize("name", ["claude", "opencode"])
def test_live_drivers_refuse_without_both_flag_and_env(monkeypatch, name):
    monkeypatch.delenv(LIVE_ENV, raising=False)
    with pytest.raises(LiveRunNotApproved):
        make_driver(name, live=False)
    with pytest.raises(LiveRunNotApproved):
        make_driver(name, live=True)
    monkeypatch.setenv(LIVE_ENV, "1")
    with pytest.raises(LiveRunNotApproved):
        make_driver(name, live=False)
    monkeypatch.setenv(LIVE_ENV, "0")
    with pytest.raises(LiveRunNotApproved):
        make_driver(name, live=True)
    monkeypatch.setenv(LIVE_ENV, "1")
    assert isinstance(make_driver(name, live=True), CommandDriver)


def test_cli_refuses_live_driver_before_creating_worktrees(monkeypatch, fixture, capsys):
    monkeypatch.delenv(LIVE_ENV, raising=False)
    code = main(["run", "--driver", "claude", "--repo", str(fixture["repo"]),
                 "--tasks", str(_write_tasks(fixture)), "--run-root", str(fixture["run_root"]),
                 "--arms", "baseline"])
    assert code == 2
    assert "needs both --live" in capsys.readouterr().err
    assert len(_worktrees(fixture["repo"])) == 1


def _write_tasks(fixture) -> Path:
    path = fixture["tdir"] / "tasks.json"
    path.write_text(json.dumps({"version": 1, "base": fixture["base"],
                                "tasks": [fixture["sign"]]}), encoding="utf-8")
    return path


# ===================================================================================== #
# task file
# ===================================================================================== #
def test_load_tasks_rejects_a_malformed_task(fixture):
    bad = dict(fixture["sign"])
    bad["check"] = {"argv": [], "timeout_s": 60}
    path = fixture["tdir"] / "bad.json"
    path.write_text(json.dumps({"version": 1, "tasks": [bad]}), encoding="utf-8")
    with pytest.raises(HarnessError, match="check.argv"):
        load_tasks(path)


def test_select_tasks_rejects_unknown_ids(fixture):
    with pytest.raises(HarnessError, match="unknown task ids: nope"):
        select_tasks([fixture["sign"]], ["nope"])


def test_shipped_task_file_is_well_formed():
    spec = load_tasks(ROOT / "evaluation" / "agent_e2e" / "tasks.json")
    tasks = spec["tasks"]
    assert 6 <= len(tasks) <= 8
    assert len({t["id"] for t in tasks}) == len(tasks)
    assert len({t["area"] for t in tasks}) >= 3
    for task in tasks:
        assert (ROOT / "evaluation" / "agent_e2e" / task["break_patch"]).is_file()
        assert any("{workdir}" in a for a in task["check"]["argv"])
        assert task["check"]["timeout_s"] <= 60
        assert task["expected_files"]
        assert "tests/" in " ".join(task["check"]["argv"])


# ===================================================================================== #
# report
# ===================================================================================== #
def _run(task, arm, repeat, success, wall=None, tin=None, cost=None, localized=False):
    return {"task": task, "arm": arm, "repeat": repeat, "success": success,
            "wall_s": wall, "tokens_in": tin, "tokens_out": None,
            "cost_usd": cost, "localized": localized}


def test_report_aggregates_arms_and_pairs_outcomes():
    runs = [
        _run("t1", "baseline", 1, True, wall=10.0, tin=100, cost=0.5, localized=True),
        _run("t1", "baseline", 2, False, wall=20.0, tin=None, localized=False),
        _run("t1", "dev_memory", 1, True, wall=5.0, tin=50, cost=0.25, localized=True),
        _run("t1", "dev_memory", 2, True, wall=7.0, tin=None, localized=True),
        _run("t2", "baseline", 1, False, wall=3.0),
        _run("t2", "dev_memory", 1, False, wall=4.0),
    ]
    rows = {r["arm"]: r for r in aggregate(runs, ["baseline", "dev_memory"])}
    assert rows["baseline"]["runs"] == 3
    assert rows["baseline"]["successes"] == 1
    assert rows["baseline"]["success_rate"] == pytest.approx(0.3333)
    assert rows["baseline"]["mean_wall_s"] == pytest.approx(11.0)
    assert rows["baseline"]["mean_tokens_in"] == pytest.approx(100.0, abs=0.1)
    assert rows["baseline"]["tokens_known_runs"] == 1
    assert rows["dev_memory"]["success_rate"] == pytest.approx(0.6667)
    assert rows["dev_memory"]["localization_rate"] == pytest.approx(0.6667)
    assert rows["dev_memory"]["mean_cost_usd"] == pytest.approx(0.25)
    assert rows["dev_memory"]["mean_tokens_out"] is None

    pairs = paired(runs, ["baseline", "dev_memory"])
    assert pairs["t1"]["baseline"]["outcomes"] == [True, False]
    assert pairs["t1"]["dev_memory"]["successes"] == 2
    assert pairs["t2"]["baseline"]["repeats"] == 1


def test_markdown_labels_every_arm_and_task_and_flags_live_drivers():
    report = {
        "driver": "claude", "base": "abc", "arms": ["baseline", "dev_memory"],
        "repeats": 1, "tasks": ["t1"],
        "summary": aggregate([_run("t1", "baseline", 1, True),
                              _run("t1", "dev_memory", 1, False)],
                             ["baseline", "dev_memory"]),
        "per_task": paired([_run("t1", "baseline", 1, True),
                            _run("t1", "dev_memory", 1, False)],
                           ["baseline", "dev_memory"]),
    }
    md = render_markdown(report)
    assert "baseline" in md and "dev_memory" in md and "| t1 |" in md
    assert "untested live" in md


# ===================================================================================== #
# source audit (style of test_contrastive_verdict_no_python_decisions)
# ===================================================================================== #
def test_agent_eval_has_no_substrate_or_rule_engine_calls():
    src = (ROOT / "scripts" / "ocelot_agent_eval.py").read_text(encoding="utf-8")
    for needle in ("substrate_rs", "from domains", "import domains", "graph_rewrite",
                   "gr._match", "gr._apply"):
        assert needle not in src, needle


def _python() -> str:
    import sys
    return sys.executable


# ===================================================================================== #
# dt-w4-fixes-b (review 11): scoped cleanup, process groups, shared refs, prep timing
# ===================================================================================== #
def _pid_gone(pid: int) -> bool:
    import os
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _listed(repo: Path) -> set[str]:
    return {str(Path(p).resolve()) for p in _worktrees(repo)}


def test_cleanup_does_not_prune_an_unrelated_missing_worktree(fixture, tmp_path):
    import shutil
    repo, base = fixture["repo"], fixture["base"]
    other = tmp_path / "unrelated-wt"
    _git(repo, "worktree", "add", "--detach", str(other), base)
    shutil.rmtree(other)  # directory vanishes out of band; admin entry stays
    assert str(other.resolve()) in _listed(repo)
    run_eval(repo, [fixture["sign"]], ["baseline"], FakeDriver(), base,
             tasks_dir=fixture["tdir"], python=_python(),
             run_root=fixture["run_root"])
    assert str(other.resolve()) in _listed(repo)
    assert not any((fixture["run_root"] / "work").glob("*"))


def test_partial_cleanup_is_reported_and_removes_only_its_own_entry(fixture):
    repo, base, run_root = fixture["repo"], fixture["base"], fixture["run_root"]
    wd = ae.make_workdir(repo, base, run_root, "locked-1")
    _git(repo, "worktree", "lock", str(wd))
    warnings = ae.remove_workdir(repo, wd, run_root)
    assert warnings and warnings[0].startswith("git worktree remove --force failed")
    assert not wd.exists()
    assert str(wd.resolve()) not in _listed(repo)
    assert str(repo.resolve()) in _listed(repo)


def test_clean_cleanup_reports_no_warnings(fixture):
    repo, base, run_root = fixture["repo"], fixture["base"], fixture["run_root"]
    wd = ae.make_workdir(repo, base, run_root, "clean-1")
    assert ae.remove_workdir(repo, wd, run_root) == []
    assert not wd.exists()


_VICTIM = (
    "import os, subprocess, sys, time\n"
    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
    "with open(sys.argv[1], 'w') as fh:\n"
    "    fh.write(f'{os.getpid()} {child.pid}')\n"
    "time.sleep(600)\n"
)


def test_run_check_timeout_kills_driver_and_its_child(tmp_path):
    victim = tmp_path / "victim.py"
    victim.write_text(_VICTIM, encoding="utf-8")
    pidfile = tmp_path / "pids.txt"
    res = ae.run_check(tmp_path, {"argv": [str(victim), str(pidfile)], "timeout_s": 3},
                       _python(), tmp_path / "check.log")
    assert res["timed_out"] is True and res["passed"] is False
    parent, child = (int(x) for x in pidfile.read_text(encoding="utf-8").split())
    assert _pid_gone(parent)
    assert _pid_gone(child)


class _StubCommandDriver(CommandDriver):
    """Test-only. Shares CommandDriver's group runner, with an argv set by the test.

    Not in LIVE_DRIVERS, never returned by make_driver, and it does not call
    _require_live_env because it never reaches a model."""

    def __init__(self, argv: list[str]) -> None:
        self.name = "stub-command"
        self.max_budget_usd = None
        self.spec = {"argv": [], "arm_argv": {}, "mcp_config_file": "none",
                     "parse": lambda stdout: {"transcript": stdout}}
        self._stub_argv = argv

    def run(self, workdir, prompt, arm, timeout_s, log_dir, *, patch_path=None):
        res = ae.spawn_group(self._stub_argv, cwd=workdir, env=dict(os.environ),
                             timeout_s=timeout_s)
        return ae._empty_result(exit_code=res["returncode"], wall_s=res["seconds"],
                                timed_out=res["timed_out"], transcript=res["stdout"])


def test_driver_timeout_kills_the_driver_tree_and_is_recorded(fixture, tmp_path):
    victim = tmp_path / "victim.py"
    victim.write_text(_VICTIM, encoding="utf-8")
    pidfile = tmp_path / "pids.txt"
    driver = _StubCommandDriver([_python(), str(victim), str(pidfile)])
    rec = ae.run_one(fixture["repo"], fixture["sign"], "baseline", 1, driver,
                     fixture["base"], tasks_dir=fixture["tdir"], python=_python(),
                     run_root=fixture["run_root"], timeout_s=3, keep=False)
    assert rec["timed_out"] is True
    assert rec["success"] is False
    parent, child = (int(x) for x in pidfile.read_text(encoding="utf-8").split())
    assert _pid_gone(parent)
    assert _pid_gone(child)
    assert rec["cleanup_warnings"] == []


def test_stub_driver_is_not_a_live_driver_and_make_driver_still_refuses():
    assert "stub-command" not in ae.LIVE_DRIVERS
    with pytest.raises(LiveRunNotApproved):
        make_driver("claude", live=True)


def test_claude_disallows_shared_ref_moving_git_commands():
    argv = CommandDriver("claude")._argv("p", "baseline", None)
    i = argv.index("--disallowedTools")
    tokens = argv[i + 1].split(",")
    expected = ["Bash(git commit:*)", "Bash(git push:*)", "Bash(git stash:*)",
                "Bash(git branch:*)", "Bash(git checkout:*)", "Bash(git switch:*)",
                "Bash(git reset:*)", "Bash(git rebase:*)", "Bash(git merge:*)",
                "Bash(git tag:*)", "Bash(git worktree:*)"]
    assert tokens == expected
    assert argv[i + 2].startswith("--")  # the next token is a flag, so parsing stops


def test_snapshot_ignores_gitignored_var_dir(tmp_path):
    repo, _base = _repo(tmp_path)
    (repo / ".gitignore").write_text("var/\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "ignore var")
    base = _git(repo, "rev-parse", "HEAD")
    wd = ae.make_workdir(repo, base, tmp_path / "runs", "snap-1")
    (wd / "var").mkdir()
    (wd / "var" / "ocelot_dev_tags.json").write_text("{}", encoding="utf-8")
    assert "var/ocelot_dev_tags.json" not in ae._snapshot(wd)
    ae.remove_workdir(repo, wd, tmp_path / "runs")


def test_prep_failure_is_recorded_and_the_run_still_scored(fixture, tmp_path):
    prep = ae.prepare_dev_memory(fixture["repo"], _python(), tmp_path / "log")
    assert prep["prep_ok"] is False
    assert prep["prep_error"]
    assert (tmp_path / "log" / "prep.log").is_file()
    runs = run_eval(fixture["repo"], [fixture["sign"]], ARMS, FakeDriver(),
                    fixture["base"], tasks_dir=fixture["tdir"], python=_python(),
                    run_root=fixture["run_root"])["runs"]
    by_arm = {r["arm"]: r for r in runs}
    assert by_arm["baseline"]["prep_s"] == 0.0
    assert by_arm["baseline"]["prep_ok"] is None
    assert by_arm["dev_memory"]["prep_ok"] is False
    assert by_arm["dev_memory"]["prep_error"]
    assert by_arm["dev_memory"]["success"] is True


def test_aggregate_reports_mean_prep_and_prep_failures():
    runs = [
        {"task": "t1", "arm": "baseline", "repeat": 1, "success": True,
         "prep_s": 0.0, "prep_ok": None},
        {"task": "t1", "arm": "dev_memory", "repeat": 1, "success": True,
         "prep_s": 10.0, "prep_ok": True},
        {"task": "t2", "arm": "dev_memory", "repeat": 1, "success": False,
         "prep_s": 2.0, "prep_ok": False},
    ]
    rows = {r["arm"]: r for r in aggregate(runs, ["baseline", "dev_memory"])}
    assert rows["baseline"]["mean_prep_s"] == 0.0
    assert rows["dev_memory"]["mean_prep_s"] == pytest.approx(6.0)
    assert rows["dev_memory"]["prep_failures"] == 1
    assert rows["baseline"]["prep_failures"] == 0
