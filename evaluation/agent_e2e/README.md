# Agent end-to-end task set

Break/fix tasks for `scripts/ocelot_agent_eval.py`. Full design: `docs/features/AGENT_E2E_EVAL.md`.

Files:

- `tasks.json`: the task list. Each task names a prompt, a break patch and a pytest check.
- `patches/<id>.patch`: the break for each task, applied to the base commit.
- `validation.json`: output of `validate` against the base. Every task must be `ok`.
- `dry_run_fake.{json,md}`: the fake driver (expected 100% success). Validates the harness.
- `dry_run_noop.{json,md}`: the noop driver (expected 0% success). Negative control.

Commands (from the repo root, with the venv Python):

```
PY=/applications/data/projects/ocelot/.venv/bin/python
$PY -m scripts.ocelot_agent_eval validate --python $PY              # check every task
$PY -m scripts.ocelot_agent_eval validate --task-ids dev-memory-strict-bool --keep
$PY -m scripts.ocelot_agent_eval run --driver fake --python $PY     # both arms, all tasks
```

Live drivers (`claude`, `opencode`) need `--live` and `OCELOT_AGENT_EVAL_LIVE=1`. They
spend tokens. Do not run them without user approval. See the doc for the approved command.

Each run writes worktrees under `/tmp/ocelot_agent_eval/<run>/work/` and removes them
on exit. Only the harness's own worktree is removed; there is no repo-wide prune. If a
removal is partial, the run record lists it under `cleanup_warnings`. Logs stay in
`/tmp/ocelot_agent_eval/<run>/logs/`.

The dev_memory arm builds its snapshot and tag cache before the driver starts. That
time is recorded as `prep_s` and kept out of `wall_s`. Every driver and check runs in
its own process group, and a timeout kills the whole group.

Live drivers (`claude`, `opencode`) can move the shared git refs. `claude` denies the
common ref-moving git commands. `opencode` has no restriction. See the doc for the
residual risks before any live run.
