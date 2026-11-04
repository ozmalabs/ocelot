"""Independent finite worlds for the P19 development and registered panels."""
from __future__ import annotations

import hashlib
import json
import random
from collections import deque


FAMILIES = ("permutation", "irreversible_objects")
TASK_KINDS = ("process_effect", "multi_step_constraint")


def _apply_permutation(state, process):
    out = [None] * len(state)
    for source, target in enumerate(process):
        out[target] = state[source]
    return out


def _compose(a, b):
    """Return the positional map for applying a and then b."""
    return [b[a[index]] for index in range(len(a))]


def _permutation_task(seed: int, task_kind: str):
    rng = random.Random(seed)
    # Four positions retain a nontrivial permutation group while keeping the
    # complete transition graph small enough for the native planner's frozen
    # model-query ceiling.
    width = 4
    primitives = {}
    for index in range(4):
        process = list(range(width))
        rng.shuffle(process)
        if process == list(range(width)):
            process[0], process[1] = process[1], process[0]
        primitives[f"perm_{index}"] = process
    initial = list(range(width))
    rng.shuffle(initial)
    length = 3 if task_kind == "process_effect" else 5
    witness = [f"perm_{rng.randrange(len(primitives))}" for _ in range(length)]
    goal = list(initial)
    for name in witness:
        goal = _apply_permutation(goal, primitives[name])
    if goal == initial:
        name = witness[-1]
        primitives[name][0], primitives[name][1] = primitives[name][1], primitives[name][0]
        goal = list(initial)
        for action in witness:
            goal = _apply_permutation(goal, primitives[action])
    return {"family": "permutation", "task_kind": task_kind, "seed": int(seed),
        "kind": "permutation", "initial_state": initial, "goal_state": goal,
        "primitive_affordances": primitives}, witness


def _object_actions():
    actions = {}
    for object_ix in range(2):
        prepare = [0, 0, 0, 0]
        prepare[object_ix * 2] = 1
        seal = [0, 0, 0, 0]
        seal[object_ix * 2 + 1] = 1
        actions[f"prepare_{object_ix}"] = ["add", prepare]
        actions[f"seal_{object_ix}"] = ["add", seal]
    return actions


def _object_task(seed: int, task_kind: str):
    rng = random.Random(seed ^ 0x19A5EED)
    primitives = _object_actions()
    objects = [0, 1]
    rng.shuffle(objects)
    if task_kind == "process_effect":
        witness = [f"prepare_{objects[0]}", f"seal_{objects[0]}"]
    else:
        witness = []
        for object_ix in objects:
            witness.extend((f"prepare_{object_ix}", f"seal_{object_ix}"))
    return {"family": "irreversible_objects", "task_kind": task_kind,
        "seed": int(seed), "kind": "integer_vector", "initial_state": [0, 0, 0, 0],
        "goal_state": [1, 1, 1, 1] if task_kind == "multi_step_constraint"
        else ([1, 1, 0, 0] if objects[0] == 0 else [0, 0, 1, 1]),
        "primitive_affordances": primitives}, witness


def generate_task(family: str, task_kind: str, seed: int):
    if family not in FAMILIES or task_kind not in TASK_KINDS:
        raise ValueError("unsupported P19 family or task kind")
    task, witness = (_permutation_task(seed, task_kind) if family == "permutation"
                     else _object_task(seed, task_kind))
    return task, P19World(task), tuple(witness)


class P19World:
    """Simulator owns legality and receipts; it never supplies a solution."""

    def __init__(self, task):
        self.family = task["family"]
        self.kind = task["kind"]
        self.seed = int(task["seed"])
        self.goal = tuple(task["goal_state"])
        self.primitives = {name: value for name, value in task["primitive_affordances"].items()}
        self.state = tuple(task["initial_state"])
        self.epoch = 0

    def legal_actions(self, state=None):
        state = tuple(self.state if state is None else state)
        if self.family == "permutation":
            return tuple(sorted(self.primitives))
        legal = []
        for name in self.primitives:
            if name.startswith("prepare_"):
                ix = int(name[-1]) * 2
                if state[ix] == 0 and state[ix + 1] == 0:
                    legal.append(name)
            else:
                ix = int(name[-1]) * 2
                if state[ix] == 1 and state[ix + 1] == 0:
                    legal.append(name)
        return tuple(sorted(legal))

    def _apply_action(self, state, name):
        if name not in self.legal_actions(state):
            raise ValueError("illegal_or_precondition_failed")
        params = self.primitives[name]
        if self.family == "permutation":
            return tuple(_apply_permutation(state, params))
        delta = params[1]
        return tuple(value + amount for value, amount in zip(state, delta))

    def transition_sequence(self, names, *, requested_process=None):
        before = tuple(self.state)
        state = before
        applied = []
        try:
            for name in names:
                state = self._apply_action(state, name)
                applied.append(name)
        except (ValueError, KeyError) as exc:
            return {"status": "rejected", "reason": str(exc), "world_id": self.world_id,
                    "world_epoch": self.epoch, "before": list(before),
                    "requested_actions": list(names), "applied_actions": applied,
                    "observed_state": list(before)}
        self.state = state
        body = {"status": "verified", "reason": None, "world_id": self.world_id,
            "world_epoch": self.epoch, "before": list(before),
            "requested_actions": list(names), "applied_actions": applied,
            "requested_process": requested_process, "observed_state": list(state)}
        body["receipt_sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        self.epoch += 1
        return body

    def transition(self, state, action):
        if tuple(state) != tuple(self.state):
            return {"status": "rejected", "reason": "stale_world_state",
                    "world_id": self.world_id, "world_epoch": self.epoch,
                    "before": list(self.state), "requested_actions": [action],
                    "applied_actions": [], "observed_state": list(self.state)}
        return self.transition_sequence((action,), requested_process=action)

    @property
    def world_id(self):
        return f"p19:{self.family}:{self.seed}"

    def verify_receipt(self, receipt):
        if receipt.get("status") != "verified" or "receipt_sha256" not in receipt:
            return False
        body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        return digest == receipt["receipt_sha256"]

    def native_task(self, task, *, max_nodes=256):
        graph = self.transition_graph(max_nodes=max_nodes)
        state_key = lambda state: ",".join(map(str, state))
        transition_model = [(state_key(source), action, state_key(target))
                            for source, action, target in graph["transitions"]]
        legal = {state_key(state): list(self.legal_actions(state))
                 for state in graph["states"]}
        return {**task, "legal_actions_by_state": legal,
            "transition_model": transition_model, "transition_graph_complete": graph["complete"]}

    @staticmethod
    def task_digest(task):
        canonical = json.dumps(task, sort_keys=True, separators=(",", ":"), default=list)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def transition_graph(self, *, max_nodes=256):
        """Return independent reachable-state transitions for native BFS."""
        start = tuple(self.state)
        queue, seen, edges = deque([start]), {start}, []
        while queue and len(seen) <= max_nodes:
            state = queue.popleft()
            for name in self.legal_actions(state):
                target = self._apply_action(state, name)
                edges.append((state, name, target))
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
                    if len(seen) > max_nodes:
                        break
        return {"states": sorted((list(state) for state in seen)),
                "transitions": [(list(a), name, list(b)) for a, name, b in edges],
                "complete": not queue}


def expression_actions(tree):
    """Decode graph-authored expression order into primitive world actions."""
    if isinstance(tree, str):
        return [tree]
    if not isinstance(tree, (list, tuple)) or not tree:
        return None
    tag = tree[0]
    if tag in {"guard", "subgoal"}:
        return expression_actions(tree[-1])
    if tag == "compose" and len(tree) == 3:
        left, right = expression_actions(tree[1]), expression_actions(tree[2])
        return left + right if left is not None and right is not None else None
    if tag == "inverse":
        return None
    if tag == "power" and len(tree) == 3:
        sequence = expression_actions(tree[2])
        count = int(tree[1])
        return sequence * count if sequence is not None and count in {2, 3} else None
    return None
