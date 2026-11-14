# Agent end-to-end evaluation (W3-C)

Status: harness shipped; **live drivers are untested live**. No hosted-model run has been made.

Code: `scripts/ocelot_agent_eval.py`. Tasks: `evaluation/agent_e2e/tasks.json`.
Tests: `tests/test_agent_eval_migrated.py`. Plan: `docs/features/DEV_TOOLING_V2_PLAN.md`, item V6.

## Why

Retrieval metrics (recall at a token budget) measure whether the right files
appear in a prompt. They do not measure whether the agent fixed the problem.
The studies cited in the plan (arXiv 2611.07286, 2610.33958) report that better
retrieval often leaves task success unchanged. `ocelot_repo_map_eval` covers the
retrieval half. This harness covers the other half: given a symptom, does the
agent make a failing test pass again?

## Task format

`evaluation/agent_e2e/tasks.json`:

```json
{
  "version": 1,
  "base": "<commit sha>",
  "tasks": [
    {
      "id": "kebab-case-id",
      "prompt": "Symptom-style description the agent receives.",
      "area": "scripts",
      "break_patch": "patches/kebab-case-id.patch",
      "check": {"argv": ["-m", "pytest", "-q", "-p", "no:cacheprovider",
                         "--confcutdir={workdir}", "tests/x_migrated.py::test_y"],
                "timeout_s": 60},
      "expected_files": ["scripts/x.py"],
      "notes": "What the break does (for reviewers, not the agent)."
    }
  ]
}
```

- `break_patch` is a unified diff relative to `base`. It must apply with `git apply`.
- `check` is a pytest argv without the interpreter. The harness runs it with the
  chosen Python in the workdir. `{workdir}` is replaced by the workdir path.
- The check must **pass on base and fail after the break**. `validate` enforces this.
  A break the check does not catch is rejected.
- `prompt` describes the missing behaviour the way a user would. It must not name the
  file to edit. It may name the failing test.
- `expected_files` are the files a correct fix touches. They are used only for the
  localization metric.

### Adding a task

1. Pick a small behaviour with a fast existing test (under 60 s). Do not add new tests
   to the base.
2. Write the break as a patch, from a file at `base`. Keep it to one function body or a
   few lines. Generate the patch with `diff -u` (or `git diff`) against a clean copy,
   and check that the header paths are `a/...` and `b/...`.
3. Add the entry to `tasks.json`, then run
   `python -m scripts.ocelot_agent_eval validate --task-ids <id>`.
4. Run the fake driver on that task to confirm the pipeline end to end.

## Harness flow

For each task and arm, `run_eval` does the following:

1. Creates a detached worktree at `base` under `<run_root>/work/<task>-<arm>-r<n>`.
2. Applies the break patch.
3. Writes the arm's MCP config into the workdir, if the arm needs one.
4. Snapshots the content hash of every modified, deleted or untracked file.
5. Runs the driver with the prompt. The driver's `run` returns exit code, wall time,
   tokens, cost, transcript and tool calls. Unknown values are `None`.
6. Snapshots again. `files_changed` lists paths whose content hash changed in step 5.
   The break itself does not count as an agent edit.
7. Runs the check. `success` means the check passed.
8. `localized` is true if any `expected_files` entry is in `files_changed`.
9. Removes the worktree, unless `--keep`.

Logs (driver stdout and stderr, check output, transcripts, the dev-memory snapshot and
journal) stay in `<run_root>/logs/`. Only worktrees are removed.

`validate` runs check, then break, then check on a worktree at `base`. It reports
`ok` only when the check passes on base, the patch applies, and the check fails
after the break.

## Drivers

| name | what it does | live |
|---|---|---|
| `noop` | Does nothing. Negative control. Expected success 0%. | no |
| `fake` | Reverts the break with `git apply -R`. Expected success 100%. Checks the harness only. | no |
| `claude` | `claude -p <prompt> --output-format json --permission-mode acceptEdits --no-session-persistence --allowedTools Read,Edit,Write,Glob,Grep,Bash`, run in the workdir. | **untested live** |
| `opencode` | `opencode run --format json --auto <prompt>`, run in the workdir. | **untested live** |

Token and cost fields come from the Claude JSON output (`usage.input_tokens`,
`usage.output_tokens`, `total_cost_usd`, `result`). Those names were confirmed in the
installed binary (claude 2.1.322), not in a live run. `usage.input_tokens` may
exclude cache-read tokens. OpenCode's JSON event stream is recorded as raw transcript
only, so its token and cost fields are `None`.

The `fake` and `noop` drivers ignore the arm. They do not start an MCP server.

### Live gate

`claude` and `opencode` refuse to run unless **both** of these hold:

- the command includes `--live`, and
- the environment has `OCELOT_AGENT_EVAL_LIVE=1`.

The refusal happens before any worktree is created. The CLI exits with status 2. The
driver also checks the environment variable again when it runs.

## Arms

| arm | configuration |
|---|---|
| `baseline` | No Ocelot MCP server. Claude Code runs with `--strict-mcp-config`, which ignores the user's MCP servers. OpenCode gets no override, so a user's global MCP servers can still load. This is a known gap for the OpenCode baseline. |
| `dev_memory` | The workdir gets `.ocelot_agent_eval_mcp.json` (Claude Code, passed with `--mcp-config`) and `.ocelot_agent_eval_opencode.json` (OpenCode, selected with the `OPENCODE_CONFIG` environment variable). Both start `<python> -m scripts.ocelot_dev_memory_mcp` with `PYTHONPATH` and `OCELOT_DEV_ROOT` set to the workdir. The snapshot and journal go under the run's log directory, and `OCELOT_DEV_AUTOBUILD=1` builds the snapshot on first start. A smoke test on this tree (no model) answered `initialize` and listed 39 tools, after about 100 s of snapshot build. That build time is inside the session's wall time. |

The two config files are untracked and are written before the snapshot. They are
not counted as agent edits. The agent can still see them with `git status`.

## Running

Validate the task set (no models, creates worktrees):

```
PY=/applications/data/projects/ocelot/.venv/bin/python
$PY -m scripts.ocelot_agent_eval validate --python $PY \
    --out-json evaluation/agent_e2e/validation.json
```

Local dry runs (no models):

```
$PY -m scripts.ocelot_agent_eval run --driver fake --arms baseline,dev_memory \
    --python $PY --out-json evaluation/agent_e2e/dry_run_fake.json \
    --out-md evaluation/agent_e2e/dry_run_fake.md
$PY -m scripts.ocelot_agent_eval run --driver noop --arms baseline \
    --python $PY --out-json evaluation/agent_e2e/dry_run_noop.json \
    --out-md evaluation/agent_e2e/dry_run_noop.md
```

## How a live run is approved and launched

A live run spends hosted-model tokens. The supervisor requests approval from the user
and states the exact command, the number of sessions and the cost ceiling. The
command only runs after approval:

```
OCELOT_AGENT_EVAL_LIVE=1 $PY -m scripts.ocelot_agent_eval run \
    --driver claude --live --arms baseline,dev_memory --repeats 1 \
    --max-budget-usd <USD ceiling> --timeout-s 900 --python $PY \
    --out-json <out>.json --out-md <out>.md
```

Size: sessions = tasks × arms × repeats. The shipped set has 7 tasks, so a pilot with
1 repeat and both arms is 14 sessions.

## Cost controls

- `--repeats`: keep at 1 for a pilot. Repeats are the only way to see variance.
- `--task-ids a,b`: run a subset.
- `--arms`: run one arm at a time.
- `--timeout-s`: wall-clock limit per session. A timed-out session scores as a
  failure, with `timed_out` recorded.
- `--max-budget-usd`: passed to `claude --max-budget-usd`. OpenCode has no equivalent
  flag in this harness, so set a budget there outside the harness.

## Limits

- The break patches are authored by the task author. A break can be easier or harder
  than a real bug. The task set is small, so it does not measure general task success.
- Drivers' network access and tool permissions are not restricted by the harness. The
  agent runs as the operator with a worktree as its working directory.
- The checks use the Python passed in with `--python`, and the agent can run any shell
  command through `Bash`. A `Bash` call can change files outside the workdir.
- `PYTHONDONTWRITEBYTECODE=1` is set for checks and drivers. Without it, a break that
  keeps the byte length of a file, such as `a + b` to `a - b`, can run stale bytecode
  from the base check when the edit lands within the same mtime second.
- Results from `fake` and `noop` validate the harness. They say nothing about any agent.
