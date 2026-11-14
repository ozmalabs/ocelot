# Dev session graph — a replayable development state graph

**Status:** v0 (2026-11-14). Workstream C of
`docs/features/GRAPH_EDIT_AND_SESSION_PLAN.md`.

**Not agent runtime.** This is dev tooling. It records what a coding agent did
during one development task and answers one mechanical question: *which action
does the workflow table say comes next?* It never edits a file, never runs a
test, never calls a model, and never imports the seed/rule runtime. The agent
remains the decider; the session is a typed receipt graph and a checklist.

The point is replayability and honest state. A session is one JSON document
that can be reloaded, inspected, diffed, or handed to another agent without
carrying live process state.

## Graph shape

A session has one node kind per stage of a development task:

```text
Session -has_task-> Task
Session -has_plan-> Plan
Session -has_step-> Step
Step    -attempt-> Attempt
Attempt -edit-> Edit
Attempt -verification-> Verification
Step    -next-> Step
Session -decision-> Decision
```

Node types: `Session`, `Task`, `Plan`, `Step`, `Attempt`, `Edit`,
`Verification`, `Decision`.

Every recorded node has:

| Field | Meaning |
|---|---|
| `id` | Stable id (`s1` for the session, `n1`, `n2`, ... for records). |
| `kind` | Record kind (`plan`, `step`, `attempt`, `edit`, `verification`, `decision`). |
| `type` | Graph type (`Plan`, `Step`, ...). |
| `ts` | UTC timestamp, `YYYY-MM-DDTHH:MM:SSZ`. |
| ... | Kind-specific JSON fields, unchanged from `record()`. |

Edges are `{src, type, tgt, ts}`. The graph is append-only apart from the
small session header (`status`, `outcome`, `updated_at`); step verdicts are
derived from verification edges, not written back onto step nodes. That keeps
the record replayable.

An **Attempt** is created automatically by the first `edit` of a step, or
explicitly with `record("attempt", ...)` after a diagnosis. After a failed
verification, a new attempt is required before the next edit. An attempt holds
the edit(s) and their verification.

## Persistence

One file per session:

```text
var/ocelot_dev_sessions/<session_id>.json
```

- Written atomically: `tempfile.mkstemp` in the same directory, `fsync`,
  `os.replace`.
- Plain JSON only. `record()` round-trips every field through `json` and
  refuses callables, paths, sockets, live substrate handles, `NaN` and
  infinity. Nothing in the file is executable.
- Stable ids: `next_node` is persisted, so reloading and continuing a session
  does not renumber or duplicate nodes.
- Every `record()` and `finish()` is a checkpoint: the file always reflects the
  last accepted node. Rollback is manual (copy/restore a session file); there
  is no in-module rollback method.
- `load_session()` verifies the id in the file matches the filename.
- The directory is under `var/`, which is gitignored.

`list_sessions()` reports unreadable files with `{"ok": false, "error": ...}`
instead of silently skipping them.

## Public API

Methods return plain dicts/lists (except `start`/`load_session`, which return a
session) and never print. Errors raise `DevSessionError` with a specific
reason.

```python
from scripts.ocelot_dev_session import (
    DevSession, DevSessionError, load_session, list_sessions, load_workflow,
)

session = DevSession.start("fix the stale reply rule", max_attempts=3,
                           root="/applications/data/projects/ocelot")
```

| Call | Returns | Effect |
|---|---|---|
| `DevSession.start(task, *, max_attempts=3, root=...)` | session | Creates the file with a `Session` + `Task`; next action is `orient`. |
| `record(kind, **fields)` | node dict | Validates, appends one node + edges, persists. |
| `state()` | graph summary | Counts, derived summary, all nodes and edges; JSON-safe. |
| `next_action()` | `{action, reason, step_id?}` | Mechanical first-match lookup in the workflow table. |
| `finish(outcome)` | final state | Appends a `Decision` (`choice: "finish"`), closes the session. |
| `load_session(id, *, root=...)` | session | Reloads one file without modifying it. |
| `list_sessions(*, root=...)` | list of summaries | Newest first; honest `ok: false` entries. |
| `load_workflow(path=None)` | dict | Loads and validates the transition data. |

Read-only properties: `session.session_id`, `session.path` (the persisted
file), `session.max_attempts`.

### Record kinds

| Kind | Required fields | Optional fields | Graph effect |
|---|---|---|---|
| `plan` | — | `steps` (list of strings/objects), `title`, `summary` | One `Plan`; `steps` gets stable ids `ps1`, `ps2`, ... |
| `step` | — | `title`, `summary` | `Step`; defaults the title from the next plan step. |
| `attempt` | — | `summary`, ... | `Attempt` under the current step; `n` is assigned by the session. |
| `edit` | — | `files`, `summary`, ... | `Edit` under the current attempt; the first edit of a step auto-creates its attempt. |
| `verification` | `passed` (bool) | `command`, `exit_code`, `summary` | `Verification` under the current attempt. |
| `decision` | `summary` or `choice` | `gate` (`wait` / `approve` / `clear`) | `Decision` under the session. |

Record order is enforced honestly:

- a step needs a plan;
- a new step waits until the current step has a passed verification;
- an attempt waits for the previous attempt to be verified;
- after a failed verification, a new edit waits for an explicit `attempt`
  checkpoint (the `diagnose` → `act` transition);
- a verification needs an edit and is one per attempt;
- after `max_attempts` failed attempts, new attempts/edits are refused and
  `next_action()` is `blocked`;
- a closed session accepts no more records.

`edit` accepts `files` as a string or list and normalizes it to a list.

## The transition table

`scripts/dev_session_workflow.json` is the decision data. The evaluator is a
first-match rule scan over facts derived from the recorded graph; there is no
Python `if/elif` state machine.

```json
{
  "version": 1,
  "name": "ocelot-dev-session",
  "actions": ["orient", "plan_step", "..."],
  "node_types": ["Session", "Task", "..."],
  "edge_types": ["has_task", "has_plan", "..."],
  "record_types": {"plan": "Plan", "step": "Step", "...": "..."},
  "rules": [
    {
      "id": "orient",
      "when": {"plan_count": 0},
      "action": "orient",
      "reason": "no plan recorded; orient the task, then record a plan",
      "include_step": false
    }
  ],
  "fallback": {
    "id": "unknown",
    "action": "blocked",
    "reason": "no workflow rule matched this state ..."
  }
}
```

Rule schema:

| Key | Meaning |
|---|---|
| `id` | Stable rule name (diagnostics and tests). |
| `when` | Non-empty object of fact conditions; all must match. |
| `action` | One of the declared `actions`. |
| `reason` | Human-readable template; `{fact}` placeholders are filled mechanically. |
| `include_step` | If true and a current step exists, add `step_id` to the result. |

A condition value is either an equality literal or an operator object:

```json
{"status_known": false}
{"attempts_remaining": {"gt": 0}}
{"gate": "wait"}
```

Operators: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `not_in`. A missing fact
or an unknown operator is an honest `DevSessionError`, not a silent `False`.

### Facts

Facts are computed mechanically from the graph on every call:

| Fact | Meaning |
|---|---|
| `closed`, `status`, `status_known`, `outcome` | Session header state. |
| `gate` | Latest human gate (`wait`, `approve`, or `null`). |
| `plan_count`, `step_count` | Recorded `Plan` / `Step` count. |
| `plan_steps`, `completed_steps`, `steps_remaining` | Planned-step progress. |
| `next_step_title` | The next planned step title, for the reason text. |
| `current_step_id`, `current_step_title`, `current_step_status` | Latest step (`active`, `passed`, `blocked`, `none`). |
| `current_step_has_edit`, `current_step_has_verification` | Facts about the latest attempt. |
| `last_verification_passed` | `true`, `false`, or `null` (no verification yet). |
| `attempts`, `failed_attempts`, `max_attempts` | Attempt accounting. |
| `attempts_remaining` | `max(0, max_attempts - failed_attempts)`. |

The shipped rules, in order:

1. closed → `done`
2. unknown status → `blocked`
3. gate `wait` → `wait`
4. gate `approve` → `approve`
5. no plan → `orient`
6. plan but no step → `plan_step`
7. step with no edit → `act`
8. edit with no verification → `verify`
9. failed verification, attempts remain → `diagnose`
10. failed verification, no attempts remain → `blocked`
11. passed, planned steps remain → `plan_step`
12. passed, all planned steps done → `finish`
13. anything else → `blocked` with an "unknown transition" reason

`next_action()` never executes the action. It reports it.

### Example

```python
session = DevSession.start("fix the stale reply rule", root=repo)
session.next_action()
# {'action': 'orient', 'reason': 'no plan recorded; orient the task, ...'}

session.record("plan", steps=["read the rule", "fix the seed"])
session.next_action()
# {'action': 'plan_step', 'reason': 'plan recorded (0/2 planned steps ...'}

session.record("step")                 # title defaults to "read the rule"
session.next_action()
# {'action': 'act', 'reason': 'step n3 (read the rule) has no edit yet; ...',
#  'step_id': 'n3'}

session.record("edit", files=["seeds/gap_awareness.json"])
session.next_action()
# {'action': 'verify', ...}

session.record("verification", passed=False,
               command="pytest tests/test_gap_awareness_migrated.py -q",
               exit_code=1)
session.next_action()
# {'action': 'diagnose', ...}

session.record("attempt", summary="the rule matches too broadly")
session.record("edit", files=["seeds/gap_awareness.json"])
session.record("verification", passed=True)
session.next_action()
# {'action': 'plan_step', 'reason': '... 1 planned step(s) remain ...'}
```

## Integration notes (central workstream)

This module is intentionally not wired into the MCP server, CLI or dispatcher
by workstream C. The integrator should add:

### MCP tools

| Tool | Arguments | Calls |
|---|---|---|
| `dev_session_start` | `task`, `max_attempts=3` | `DevSession.start(...)`; return `state()` + `next_action()`. |
| `dev_session_record` | `session_id`, `kind`, `fields` (object) | `load_session(...).record(kind, **fields)`; return node + `next_action()`. |
| `dev_session_state` | `session_id` | `load_session(...).state()`. |
| `dev_session_next` | `session_id` | `load_session(...).next_action()`. |
| `dev_session_finish` | `session_id`, `outcome` | `load_session(...).finish(outcome)`. |
| `dev_session_load` | `session_id` | `load_session(...).state()`. |
| `dev_session_list` | — | `list_sessions()`. |

Suggested CLI verbs in `scripts/ocelot_dev_memory.py`:
`session-start`, `session-record`, `session-state`, `session-next`,
`session-finish`, `session-list`. The CLI is a thin JSON wrapper; no decision
logic belongs there.

## Honest limits (v0)

- **One plan per session.** Re-planning requires a new session; plan revision
  is not modelled.
- **An open-ended plan finishes after one passed step.** Record the planned
  steps up front for multi-step work; `steps: []` has no notion of "more".
- **One linear step sequence.** The `next` edge is linear; parallel branches
  and subgraphs are not modelled.
- **Attempts consume only failures.** `max_attempts` counts failed attempts,
  not explicit no-op attempts. An explicit attempt can only start after the
  previous attempt has been verified (or as the first attempt).
- **The table cannot know intent.** If the workflow says `plan_step`, it does
  not choose *which* step; the agent does. `next_step_title` is a hint from the
  plan, not a decision.
- **The human gate is advisory.** A `wait`/`approve` decision changes
  `next_action()`, but `record()` does not refuse other records while a gate
  is set. The agent and the human remain responsible for honouring it.
- **No execution.** The session records `command`/`exit_code`; it never runs
  them and cannot prove a verification is true. The journal and the actual
  test run remain the evidence.
- **`finish(outcome)` records the caller's claim.** It closes the session with
  the supplied outcome; it does not prove that outcome or require every step
  to have passed.
- **No concurrency control.** Writes are atomic per file, but two processes
  writing the same session can lose an update; one agent should own a session.
- **Not a snapshot input yet.** Sessions live under `var/` and are not indexed
  by `ocelot_dev_memory`; a `dev_session` view would be an integration step.

## Source

- `scripts/ocelot_dev_session.py` — graph, persistence, facts, evaluator.
- `scripts/dev_session_workflow.json` — the declarative transition table.
- `tests/test_dev_session_migrated.py` — scoped gate:

  ```bash
  .venv/bin/python -m pytest tests/test_dev_session_migrated.py -q
  ```

- `docs/features/DEV_MEMORY_MCP.md` — the repo-memory surface this accompanies.
- `docs/features/GRAPH_EDIT_AND_SESSION_PLAN.md` — workstream plan.
