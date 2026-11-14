"""ocelot_dev_session — a replayable dev-session state graph (LangGraph-like).

DEV TOOLING, NOT AGENT RUNTIME. This module records what a coding agent did
during one development task: the task, its plan, the steps it worked on, the
attempts, edits, verifications and decisions. It is a *receipt graph*, not a
runtime: it never edits files, never runs tests, never calls a model and never
holds a live substrate handle.

The graph is typed and append-only apart from the small session header:

    Session -has_task-> Task
    Session -has_plan-> Plan
    Session -has_step-> Step
    Step    -attempt-> Attempt
    Attempt -edit-> Edit
    Attempt -verification-> Verification
    Step    -next-> Step
    Session -decision-> Decision

The single decision this module makes is **which action the workflow table
says comes next**. The table lives in ``scripts/dev_session_workflow.json``;
the evaluator is a mechanical first-match lookup over facts derived from the
recorded graph. Python contains no hand-written state machine: change the JSON
to change the workflow.

Persistence is one JSON document per session at
``var/ocelot_dev_sessions/<session_id>.json``, written atomically with a
temporary file plus ``os.replace``. Only plain JSON values are stored, so a
session can be reloaded, replayed and diffed.

Usage::

    session = DevSession.start("fix the stale reply rule", root=repo)
    session.record("plan", steps=["read the rule", "fix the seed"])
    session.record("step", title="read the rule")
    session.record("edit", files=["seeds/gap_awareness.json"])
    session.record("verification", passed=True,
                   command="pytest tests/test_gap_awareness_migrated.py -q")
    session.next_action()   # {'action': 'plan_step', 'reason': ...}
    session.finish("completed")

The same surface is intended to be exposed by the dev-memory MCP server and
CLI (``dev_session_*``); the central integrator wires that, not this module.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKFLOW = Path(__file__).with_name("dev_session_workflow.json")
SESSIONS_DIR = Path("var") / "ocelot_dev_sessions"

SESSION_VERSION = 1
WORKFLOW_VERSION = 1
SESSION_STATUSES = ("open", "closed")
GATE_VALUES = ("wait", "approve", "clear")
RESERVED_NODE_KEYS = {"id", "kind", "type", "ts"}

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

_COMPARE_OPS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "lt": lambda a, b: _compare(a, b, lambda x, y: x < y),
    "lte": lambda a, b: _compare(a, b, lambda x, y: x <= y),
    "gt": lambda a, b: _compare(a, b, lambda x, y: x > y),
    "gte": lambda a, b: _compare(a, b, lambda x, y: x >= y),
    "in": lambda a, b: _contains(b, a),
    "not_in": lambda a, b: not _contains(b, a),
}


class DevSessionError(RuntimeError):
    """An honest refusal from the dev-session graph.

    Raised for malformed input, a missing session, an impossible record
    sequence, or a workflow table that cannot be evaluated. The module never
    silently repairs a session.
    """


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _now() -> str:
    """A sortable UTC timestamp; the session format has a fixed precision."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _compare(a: Any, b: Any, op: Callable[[Any, Any], bool]) -> bool:
    try:
        return op(a, b)
    except TypeError:
        return False


def _contains(container: Any, item: Any) -> bool:
    try:
        return item in container
    except TypeError:
        return False


def _json_safe(value: Any, what: str) -> Any:
    """Round-trip a value through JSON so only plain data is ever stored."""
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as e:
        raise DevSessionError(f"{what} must be JSON-safe: {e}") from e


def _session_id(value: Any) -> str:
    sid = str(value or "").strip()
    if sid.endswith(".json"):
        sid = sid[:-5]
    if not sid or not _SESSION_ID_RE.fullmatch(sid):
        raise DevSessionError(
            f"invalid session id {value!r}; use the id returned by start()")
    return sid


def _new_session_id(root: Path) -> str:
    directory = root / SESSIONS_DIR
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    for _ in range(32):
        sid = f"ds-{stamp}-{secrets.token_hex(4)}"
        if not (directory / f"{sid}.json").exists():
            return sid
    raise DevSessionError("could not allocate a unique session id")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write one JSON document atomically: temp file, fsync, os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=False, allow_nan=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.",
                                    suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------- #
# workflow table
# --------------------------------------------------------------------------- #
def _validate_condition(condition: Any, *, rule_id: str) -> None:
    if not isinstance(condition, dict) or not condition:
        raise DevSessionError(
            f"workflow rule {rule_id!r} has an empty or non-object condition")
    for op in condition:
        if op not in _COMPARE_OPS:
            raise DevSessionError(
                f"workflow rule {rule_id!r} uses unknown operator {op!r}")


def _validate_workflow(data: Any) -> None:
    if not isinstance(data, dict):
        raise DevSessionError("workflow must be a JSON object")
    if data.get("version") != WORKFLOW_VERSION:
        raise DevSessionError(
            f"workflow version must be {WORKFLOW_VERSION}, "
            f"got {data.get('version')!r}")
    actions = data.get("actions")
    if not isinstance(actions, list) or not actions:
        raise DevSessionError("workflow needs a non-empty actions list")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise DevSessionError("workflow needs a non-empty rules list")
    for rule in rules:
        if not isinstance(rule, dict):
            raise DevSessionError("every workflow rule must be an object")
        rule_id = str(rule.get("id") or "")
        action = str(rule.get("action") or "")
        reason = rule.get("reason")
        if not rule_id or not action or not isinstance(reason, str) or not reason:
            raise DevSessionError(
                "every workflow rule needs id, action and reason")
        if action not in actions:
            raise DevSessionError(
                f"workflow rule {rule_id!r} uses undeclared action {action!r}")
        when = rule.get("when")
        if not isinstance(when, dict) or not when:
            raise DevSessionError(
                f"workflow rule {rule_id!r} needs a non-empty when object")
        for fact, condition in when.items():
            if isinstance(condition, dict):
                _validate_condition(condition, rule_id=rule_id)
    fallback = data.get("fallback")
    if not isinstance(fallback, dict):
        raise DevSessionError("workflow needs a fallback object")
    if str(fallback.get("action") or "") not in actions:
        raise DevSessionError("workflow fallback uses an undeclared action")
    if not isinstance(fallback.get("reason"), str) or not fallback["reason"]:
        raise DevSessionError("workflow fallback needs a reason")
    record_types = data.get("record_types")
    if not isinstance(record_types, dict) or not record_types:
        raise DevSessionError("workflow needs a record_types object")


def load_workflow(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate the declarative transition table."""
    source = Path(path) if path is not None else DEFAULT_WORKFLOW
    try:
        raw = source.read_text(encoding="utf-8")
    except OSError as e:
        raise DevSessionError(f"cannot read workflow {source}: {e}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise DevSessionError(f"workflow {source} is not valid JSON: {e}") from e
    _validate_workflow(data)
    return data


def _match_condition(condition: dict[str, Any],
                     facts: dict[str, Any]) -> bool:
    """Mechanical fact matching: equality or one of the declared operators."""
    for fact, expected in condition.items():
        if fact not in facts:
            raise DevSessionError(
                f"workflow condition references unknown fact {fact!r}")
        actual = facts[fact]
        if isinstance(expected, dict):
            for op, operand in expected.items():
                handler = _COMPARE_OPS.get(op)
                if handler is None:
                    raise DevSessionError(
                        f"workflow condition uses unknown operator {op!r}")
                if not handler(actual, operand):
                    return False
        elif actual != expected:
            return False
    return True


def _render_reason(template: str, facts: dict[str, Any]) -> str:
    values = {key: ("" if value is None else value)
              for key, value in facts.items()}
    try:
        return str(template).format(**values)
    except (KeyError, IndexError, ValueError):
        return str(template)


# --------------------------------------------------------------------------- #
# input normalisation
# --------------------------------------------------------------------------- #
def _normalise_plan_steps(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise DevSessionError("plan steps must be a list")
    steps: list[dict[str, Any]] = []
    for index, item in enumerate(raw, 1):
        if isinstance(item, str):
            entry: dict[str, Any] = {"title": item.strip()}
        elif isinstance(item, dict):
            entry = dict(item)
        else:
            raise DevSessionError(
                f"plan step {index} must be a string or an object")
        title = str(entry.get("title") or entry.get("summary") or "").strip()
        if not title:
            raise DevSessionError(f"plan step {index} needs a title")
        entry["id"] = f"ps{index}"
        entry["index"] = index
        entry["title"] = title
        steps.append(_json_safe(entry, f"plan step {index}"))
    return steps


def _validate_session_data(data: Any) -> None:
    if not isinstance(data, dict):
        raise DevSessionError("session data must be a JSON object")
    if data.get("version") != SESSION_VERSION:
        raise DevSessionError(
            f"session version must be {SESSION_VERSION}, "
            f"got {data.get('version')!r}")
    for key in ("session_id", "task", "status"):
        if not isinstance(data.get(key), str):
            raise DevSessionError(f"session field {key!r} must be a string")
    max_attempts = data.get("max_attempts")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) \
            or max_attempts < 1:
        raise DevSessionError("session max_attempts must be a positive integer")
    next_node = data.get("next_node")
    if isinstance(next_node, bool) or not isinstance(next_node, int) \
            or next_node < 1:
        raise DevSessionError("session next_node must be a positive integer")
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise DevSessionError("session nodes and edges must be lists")
    ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise DevSessionError("every session node needs a string id")
        ids.append(node["id"])
    if len(set(ids)) != len(ids):
        raise DevSessionError("session contains duplicate node ids")
    numeric_ids = [int(node_id[1:]) for node_id in ids
                   if node_id.startswith("n") and node_id[1:].isdigit()]
    if numeric_ids and next_node <= max(numeric_ids):
        raise DevSessionError(
            "session next_node must be greater than every recorded node id")
    for edge in edges:
        if not isinstance(edge, dict):
            raise DevSessionError("every session edge must be an object")
        for key in ("src", "type", "tgt"):
            if not isinstance(edge.get(key), str):
                raise DevSessionError(f"every session edge needs {key!r}")
        if edge["src"] not in ids or edge["tgt"] not in ids:
            raise DevSessionError(
                "session edge references a node that is not in the session")


# --------------------------------------------------------------------------- #
# the session graph
# --------------------------------------------------------------------------- #
class DevSession:
    """One development session as a typed, persisted graph."""

    def __init__(self, data: dict[str, Any], root: str | Path | None = None,
                 *,
                 workflow: dict[str, Any] | None = None) -> None:
        _validate_session_data(data)
        self.root = Path(root).resolve() if root is not None else ROOT
        self.data = data
        table = workflow if workflow is not None else load_workflow()
        _validate_workflow(table)
        self.workflow = table

    # -- construction ------------------------------------------------------ #
    @classmethod
    def start(cls, task: str, *, max_attempts: int = 3,
              root: str | Path | None = None) -> DevSession:
        """Create a session with only a Task node; the next action is orient."""
        task_text = str(task or "").strip()
        if not task_text:
            raise DevSessionError("task must be a non-empty string")
        if isinstance(max_attempts, bool):
            raise DevSessionError("max_attempts must be an integer")
        try:
            attempts = int(max_attempts)
        except (TypeError, ValueError) as e:
            raise DevSessionError("max_attempts must be an integer") from e
        if attempts < 1:
            raise DevSessionError("max_attempts must be at least 1")
        root_path = Path(root).resolve() if root is not None else ROOT
        workflow = load_workflow()
        session_id = _new_session_id(root_path)
        ts = _now()
        data: dict[str, Any] = {
            "version": SESSION_VERSION,
            "session_id": session_id,
            "task": task_text,
            "status": "open",
            "outcome": None,
            "max_attempts": attempts,
            "created_at": ts,
            "updated_at": ts,
            "finished_at": None,
            "next_node": 1,
            "nodes": [{
                "id": "s1",
                "kind": "session",
                "type": "Session",
                "ts": ts,
                "task": task_text,
            }],
            "edges": [],
        }
        session = cls(data, root_path, workflow=workflow)
        task_node = session._append_node("task", "Task", {"title": task_text})
        session._add_edge("s1", "has_task", task_node["id"],
                          ts=task_node["ts"])
        session._save()
        return session

    # -- public API -------------------------------------------------------- #
    @property
    def session_id(self) -> str:
        return str(self.data["session_id"])

    @property
    def path(self) -> Path:
        return self.root / SESSIONS_DIR / f"{self.session_id}.json"

    @property
    def max_attempts(self) -> int:
        return int(self.data["max_attempts"])

    def record(self, kind: str, **fields: Any) -> dict[str, Any]:
        """Append one typed node to the graph and persist the session.

        Public kinds: ``plan``, ``step``, ``attempt``, ``edit``,
        ``verification``, ``decision``. Returns the new node as a plain dict.
        Invalid kinds, impossible sequences and non-JSON fields raise
        :class:`DevSessionError`.
        """
        kind_key = str(kind or "").strip().lower()
        record_types = self.workflow["record_types"]
        if kind_key not in record_types:
            expected = ", ".join(sorted(record_types))
            raise DevSessionError(
                f"unknown record kind {kind!r}; expected one of: {expected}")
        if self.data["status"] != "open":
            raise DevSessionError(
                f"session is {self.data['status']}; cannot record {kind_key}")
        reserved = RESERVED_NODE_KEYS.intersection(fields)
        if reserved:
            raise DevSessionError(
                f"record fields may not set reserved keys: "
                f"{', '.join(sorted(reserved))}")
        clean = _json_safe(fields, f"{kind_key} fields")
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "plan": self._record_plan,
            "step": self._record_step,
            "attempt": self._record_attempt,
            "edit": self._record_edit,
            "verification": self._record_verification,
            "decision": self._record_decision,
        }
        handler = handlers.get(kind_key)
        if handler is None:
            raise DevSessionError(
                f"workflow declares record kind {kind_key!r} without a handler")
        before = _json_safe(self.data, "session snapshot")
        try:
            node = handler(clean)
            self._save()
        except BaseException:
            self.data.clear()
            self.data.update(before)
            raise
        return _json_safe(node, f"{kind_key} node")

    def state(self) -> dict[str, Any]:
        """A compact, JSON-safe snapshot of the graph and its derived facts."""
        facts = self._facts()
        counts = Counter(str(n.get("type") or "") for n in self.data["nodes"])
        plan = self._plan()
        nodes = [dict(n) for n in self.data["nodes"]]
        edges = [dict(e) for e in self.data["edges"]]
        payload: dict[str, Any] = {
            "ok": True,
            "session_id": self.session_id,
            "task": self.data["task"],
            "status": self.data["status"],
            "outcome": self.data.get("outcome"),
            "max_attempts": self.max_attempts,
            "created_at": self.data.get("created_at"),
            "updated_at": self.data.get("updated_at"),
            "finished_at": self.data.get("finished_at"),
            "counts": dict(sorted(counts.items())),
            "summary": {
                "plan": None if plan is None else {
                    "id": plan["id"],
                    "title": plan.get("title", ""),
                    "steps": plan.get("steps", []),
                },
                "steps": [self._step_summary(step)
                          for step in self._steps()],
                "current_step_id": facts["current_step_id"],
                "current_step_status": facts["current_step_status"],
                "completed_steps": facts["completed_steps"],
                "remaining_steps": facts["steps_remaining"],
                "attempts": facts["attempts"],
                "failed_attempts": facts["failed_attempts"],
            },
            "nodes": nodes,
            "edges": edges,
        }
        return _json_safe(payload, "session state")

    def next_action(self) -> dict[str, Any]:
        """The next workflow action and its reason, from the table lookup."""
        facts = self._facts()
        for rule in self.workflow["rules"]:
            if _match_condition(rule["when"], facts):
                return self._action_from_rule(rule, facts)
        return self._action_from_rule(self.workflow["fallback"], facts)

    def finish(self, outcome: str) -> dict[str, Any]:
        """Close the session with an outcome and return the final state."""
        if self.data["status"] != "open":
            raise DevSessionError(
                f"session is already {self.data['status']}")
        outcome_text = str(outcome or "").strip()
        if not outcome_text:
            raise DevSessionError("finish needs a non-empty outcome")
        before = _json_safe(self.data, "session snapshot")
        ts = _now()
        try:
            node = self._append_node(
                "decision", "Decision",
                {
                    "choice": "finish",
                    "outcome": outcome_text,
                    "summary": f"session finished: {outcome_text}",
                },
                ts=ts,
            )
            self._add_edge("s1", "decision", node["id"], ts=ts)
            self.data["status"] = "closed"
            self.data["outcome"] = outcome_text
            self.data["finished_at"] = ts
            self._save()
        except BaseException:
            self.data.clear()
            self.data.update(before)
            raise
        return self.state()

    # -- record handlers --------------------------------------------------- #
    def _record_plan(self, fields: dict[str, Any]) -> dict[str, Any]:
        if self._plan() is not None:
            raise DevSessionError("session already has a plan")
        raw_steps = fields.pop("steps", [])
        steps = _normalise_plan_steps(raw_steps)
        fields["title"] = (
            str(fields.get("title") or fields.get("summary") or "").strip()
            or "plan")
        fields["steps"] = steps
        node = self._append_node("plan", "Plan", fields)
        self._add_edge("s1", "has_plan", node["id"], ts=node["ts"])
        return node

    def _record_step(self, fields: dict[str, Any]) -> dict[str, Any]:
        plan = self._plan()
        if plan is None:
            raise DevSessionError("record a plan before a step")
        steps = self._steps()
        if steps and not self._step_passed(steps[-1]):
            raise DevSessionError(
                f"current step {steps[-1]['id']} has not passed; verify it "
                f"or finish the session before starting another step")
        index = len(steps) + 1
        plan_steps = plan.get("steps")
        default_title = ""
        plan_step_id = None
        if isinstance(plan_steps, list) and index <= len(plan_steps):
            plan_step = plan_steps[index - 1]
            if isinstance(plan_step, dict):
                default_title = str(plan_step.get("title") or "")
                plan_step_id = plan_step.get("id")
        raw_title = fields.pop("title", None)
        raw_summary = fields.pop("summary", None)
        title = str(raw_title or raw_summary or default_title
                    or f"step {index}").strip()
        title = title or f"step {index}"
        fields["title"] = title
        fields["plan_index"] = index
        if plan_step_id:
            fields["plan_step_id"] = plan_step_id
        if raw_summary and raw_title:
            fields["summary"] = str(raw_summary)
        node = self._append_node("step", "Step", fields)
        self._add_edge("s1", "has_step", node["id"], ts=node["ts"])
        if steps:
            self._add_edge(steps[-1]["id"], "next", node["id"], ts=node["ts"])
        return node

    def _record_attempt(self, fields: dict[str, Any]) -> dict[str, Any]:
        step = self._require_open_step()
        self._guard_attempts(step)
        attempts = self._attempts(step["id"])
        if attempts and not self._verifications(attempts[-1]["id"]):
            raise DevSessionError(
                f"current attempt {attempts[-1]['id']} has no verification; "
                f"record verification or finish the session")
        if "n" in fields:
            raise DevSessionError("attempt number is assigned by the session")
        return self._create_attempt(step, fields)

    def _record_edit(self, fields: dict[str, Any]) -> dict[str, Any]:
        step = self._require_open_step()
        self._guard_attempts(step)
        files = fields.get("files")
        if isinstance(files, str):
            fields["files"] = [files]
        elif files is not None and not isinstance(files, list):
            raise DevSessionError("edit files must be a list or a string")
        attempts = self._attempts(step["id"])
        if not attempts:
            attempt = self._create_attempt(
                step, {"auto": True, "summary": "auto-created for edit"})
        else:
            attempt = attempts[-1]
            if self._verifications(attempt["id"]):
                raise DevSessionError(
                    f"attempt {attempt['id']} is verified; after a failed "
                    f"verification diagnose and record an attempt before a "
                    f"new edit")
        fields["step_id"] = step["id"]
        fields["attempt_id"] = attempt["id"]
        node = self._append_node("edit", "Edit", fields)
        self._add_edge(attempt["id"], "edit", node["id"], ts=node["ts"])
        return node

    def _record_verification(self, fields: dict[str, Any]) -> dict[str, Any]:
        step = self._require_open_step()
        attempts = self._attempts(step["id"])
        if not attempts:
            raise DevSessionError(
                "record an edit before a verification; there is no attempt")
        attempt = attempts[-1]
        if not self._edits(attempt["id"]):
            raise DevSessionError(
                f"attempt {attempt['id']} has no edit to verify")
        if self._verifications(attempt["id"]):
            raise DevSessionError(
                f"attempt {attempt['id']} already has a verification; record "
                f"an attempt or edit to start a new one")
        passed = fields.get("passed")
        if not isinstance(passed, bool):
            raise DevSessionError(
                "verification needs passed=true or passed=false")
        fields["step_id"] = step["id"]
        fields["attempt_id"] = attempt["id"]
        node = self._append_node("verification", "Verification", fields)
        self._add_edge(attempt["id"], "verification", node["id"], ts=node["ts"])
        return node

    def _record_decision(self, fields: dict[str, Any]) -> dict[str, Any]:
        if not fields.get("summary") and not fields.get("choice"):
            raise DevSessionError("decision needs a summary or a choice")
        gate = fields.get("gate")
        if gate is not None and gate not in GATE_VALUES:
            raise DevSessionError(
                f"decision gate must be one of {GATE_VALUES}")
        node = self._append_node("decision", "Decision", fields)
        self._add_edge("s1", "decision", node["id"], ts=node["ts"])
        return node

    # -- internal graph helpers ------------------------------------------- #
    def _append_node(self, kind: str, type_name: str,
                     fields: dict[str, Any], *, ts: str | None = None
                     ) -> dict[str, Any]:
        reserved = RESERVED_NODE_KEYS.intersection(fields)
        if reserved:
            raise DevSessionError(
                f"internal node fields may not set reserved keys: "
                f"{', '.join(sorted(reserved))}")
        seq = int(self.data["next_node"])
        self.data["next_node"] = seq + 1
        node = {
            "id": f"n{seq}",
            "kind": str(kind),
            "type": str(type_name),
            "ts": ts or _now(),
            **fields,
        }
        self.data["nodes"].append(node)
        self.data["updated_at"] = node["ts"]
        return node

    def _add_edge(self, src: str, edge_type: str, tgt: str, *,
                  ts: str | None = None) -> dict[str, Any]:
        edge = {
            "src": str(src),
            "type": str(edge_type),
            "tgt": str(tgt),
            "ts": ts or _now(),
        }
        self.data["edges"].append(edge)
        return edge

    def _save(self) -> None:
        self.data["updated_at"] = _now()
        try:
            _atomic_write_json(self.path, self.data)
        except OSError as e:
            raise DevSessionError(
                f"cannot write session {self.session_id}: {e}") from e

    def _create_attempt(self, step: dict[str, Any],
                        fields: dict[str, Any]) -> dict[str, Any]:
        attempts = self._attempts(step["id"])
        attempt_fields = dict(fields)
        attempt_fields["n"] = len(attempts) + 1
        node = self._append_node("attempt", "Attempt", attempt_fields)
        self._add_edge(step["id"], "attempt", node["id"], ts=node["ts"])
        return node

    def _nodes_of_type(self, type_name: str) -> list[dict[str, Any]]:
        return [n for n in self.data["nodes"] if n.get("type") == type_name]

    def _node_by_id(self, node_id: str) -> dict[str, Any] | None:
        for node in self.data["nodes"]:
            if node.get("id") == node_id:
                return node
        return None

    def _targets(self, src: str, edge_type: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for edge in self.data["edges"]:
            if edge.get("src") == src and edge.get("type") == edge_type:
                node = self._node_by_id(str(edge.get("tgt") or ""))
                if node is not None:
                    out.append(node)
        return out

    def _plan(self) -> dict[str, Any] | None:
        plans = self._nodes_of_type("Plan")
        return plans[0] if plans else None

    def _steps(self) -> list[dict[str, Any]]:
        return self._nodes_of_type("Step")

    def _attempts(self, step_id: str) -> list[dict[str, Any]]:
        return self._targets(step_id, "attempt")

    def _edits(self, attempt_id: str) -> list[dict[str, Any]]:
        return self._targets(attempt_id, "edit")

    def _verifications(self, attempt_id: str) -> list[dict[str, Any]]:
        return self._targets(attempt_id, "verification")

    def _step_passed(self, step: dict[str, Any]) -> bool:
        for attempt in self._attempts(step["id"]):
            if any(v.get("passed") is True
                   for v in self._verifications(attempt["id"])):
                return True
        return False

    def _failed_attempts(self, step_id: str) -> int:
        count = 0
        for attempt in self._attempts(step_id):
            if any(v.get("passed") is False
                   for v in self._verifications(attempt["id"])):
                count += 1
        return count

    def _step_summary(self, step: dict[str, Any]) -> dict[str, Any]:
        attempts = self._attempts(step["id"])
        failed = self._failed_attempts(step["id"])
        if self._step_passed(step):
            status = "passed"
        elif failed >= self.max_attempts:
            status = "blocked"
        else:
            status = "active"
        return {
            "id": step["id"],
            "title": step.get("title", ""),
            "plan_index": step.get("plan_index"),
            "status": status,
            "attempts": len(attempts),
            "failed_attempts": failed,
        }

    def _require_open_step(self) -> dict[str, Any]:
        steps = self._steps()
        if not steps:
            raise DevSessionError(
                "record a step before this record; there is no current step")
        step = steps[-1]
        if self._step_passed(step):
            raise DevSessionError(
                f"step {step['id']} already passed; record a new step")
        return step

    def _guard_attempts(self, step: dict[str, Any]) -> None:
        failed = self._failed_attempts(step["id"])
        if failed >= self.max_attempts:
            raise DevSessionError(
                f"step {step['id']} has used all {self.max_attempts} "
                f"attempts; finish(blocked) or record a decision")

    # -- facts for the transition table ----------------------------------- #
    def _gate(self) -> str | None:
        gate: str | None = None
        for decision in self._nodes_of_type("Decision"):
            value = decision.get("gate")
            choice = str(decision.get("choice") or "").lower()
            if value is None:
                if choice in ("wait", "approve"):
                    value = choice
                elif choice in ("resume", "approved", "clear"):
                    value = "clear"
            if value in ("wait", "approve"):
                gate = str(value)
            elif value == "clear":
                gate = None
        return gate

    def _facts(self) -> dict[str, Any]:
        plans = self._nodes_of_type("Plan")
        steps = self._steps()
        plan = plans[0] if plans else None
        plan_steps = plan.get("steps") if plan is not None else []
        if not isinstance(plan_steps, list):
            plan_steps = []
        current_step = steps[-1] if steps else None
        attempts = self._attempts(current_step["id"]) if current_step else []
        current_attempt = attempts[-1] if attempts else None
        edits = self._edits(current_attempt["id"]) if current_attempt else []
        verifications = (self._verifications(current_attempt["id"])
                         if current_attempt else [])
        last_verification = verifications[-1] if verifications else None
        last_passed: bool | None = None
        if last_verification is not None \
                and isinstance(last_verification.get("passed"), bool):
            last_passed = bool(last_verification["passed"])
        completed_steps = sum(1 for step in steps if self._step_passed(step))
        steps_remaining = max(0, len(plan_steps) - completed_steps)
        next_step_title = ""
        if completed_steps < len(plan_steps):
            entry = plan_steps[completed_steps]
            if isinstance(entry, dict):
                next_step_title = str(entry.get("title") or "")
        failed_attempts = (self._failed_attempts(current_step["id"])
                           if current_step else 0)
        max_attempts = self.max_attempts
        status = str(self.data["status"])
        current_status = "none"
        if current_step is not None:
            if self._step_passed(current_step):
                current_status = "passed"
            elif failed_attempts >= max_attempts:
                current_status = "blocked"
            else:
                current_status = "active"
        return {
            "session_id": self.session_id,
            "task": self.data["task"],
            "status": status,
            "status_known": status in SESSION_STATUSES,
            "closed": status == "closed",
            "outcome": self.data.get("outcome") or "",
            "max_attempts": max_attempts,
            "gate": self._gate(),
            "plan_count": len(plans),
            "step_count": len(steps),
            "plan_steps": len(plan_steps),
            "completed_steps": completed_steps,
            "steps_remaining": steps_remaining,
            "next_step_title": next_step_title,
            "current_step_id": (current_step["id"] if current_step else ""),
            "current_step_title": (str(current_step.get("title") or "")
                                   if current_step else ""),
            "current_step_status": current_status,
            "current_step_has_edit": bool(edits),
            "current_step_has_verification": bool(verifications),
            "last_verification_passed": last_passed,
            "attempts": len(attempts),
            "failed_attempts": failed_attempts,
            "attempts_remaining": max(0, max_attempts - failed_attempts),
        }

    @staticmethod
    def _action_from_rule(rule: dict[str, Any],
                          facts: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {
            "action": str(rule["action"]),
            "reason": _render_reason(str(rule["reason"]), facts),
        }
        if rule.get("include_step") and facts.get("current_step_id"):
            result["step_id"] = str(facts["current_step_id"])
        return result


# --------------------------------------------------------------------------- #
# loading / listing
# --------------------------------------------------------------------------- #
def load_session(session_id: str,
                 *, root: str | Path | None = None) -> DevSession:
    """Reload one persisted session without modifying it."""
    root_path = Path(root).resolve() if root is not None else ROOT
    sid = _session_id(session_id)
    path = root_path / SESSIONS_DIR / f"{sid}.json"
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise DevSessionError(f"no such session: {sid}") from None
    except OSError as e:
        raise DevSessionError(f"cannot read session {sid}: {e}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise DevSessionError(
            f"session {sid} is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise DevSessionError(f"session {sid} is not a JSON object")
    if str(data.get("session_id") or "") != sid:
        raise DevSessionError(
            f"session file {path.name} carries id "
            f"{data.get('session_id')!r}, expected {sid!r}")
    return DevSession(data, root_path)


def list_sessions(*, root: str | Path | None = None) -> list[dict[str, Any]]:
    """Summaries of every persisted session, newest first.

    Unreadable files are reported honestly with ``ok: false`` rather than
    being skipped silently.
    """
    root_path = Path(root).resolve() if root is not None else ROOT
    directory = root_path / SESSIONS_DIR
    if not directory.is_dir():
        return []
    summaries: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            session = load_session(path.stem, root=root_path)
        except DevSessionError as e:
            summaries.append({
                "ok": False,
                "session_id": path.stem,
                "error": str(e),
            })
            continue
        state = session.state()
        summaries.append({
            "ok": True,
            "session_id": state["session_id"],
            "task": state["task"],
            "status": state["status"],
            "outcome": state["outcome"],
            "max_attempts": state["max_attempts"],
            "created_at": state["created_at"],
            "updated_at": state["updated_at"],
            "counts": state["counts"],
            "summary": state["summary"],
        })
    summaries.sort(
        key=lambda item: (str(item.get("created_at") or ""),
                          str(item.get("session_id") or "")),
        reverse=True,
    )
    return summaries
