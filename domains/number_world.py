"""Number world — the agent's first MATHEMATICAL world: a number line it walks.

Math has nothing to perceive, so a word like ``prime`` can never bottom out in
experience — it stays "held, awaiting" forever (see learn_word /
_unmet_dependencies). This world gives mathematics something to perceive, the
same way Doom gives space something to perceive: numbers are OBJECTS on a line,
connected by ``succ`` edges, and each number's MAGNITUDE is grounded in
countable ``Unit`` tokens — cardinality, the child's entry into number ("three
is *this many*"). The agent walks the line by counting (count_up/count_down),
perceiving only a local window — so it must count to reach further, exactly as
it must move to see further in space.

The world publishes raw structure only — the successor edges and the unit
tokens. It does NOT publish "this is 3", "this is prime", or any magnitude
label: the agent grounds number by COUNTING the units it sees, and grounds
successor / order / even / divides by reasoning over the structure. From this
seed, arithmetic and divisibility compose upward via the DSL + the
teach-and-ground loop; nothing is interpreted for the agent.

Stateless ``apply_action`` (returns a fresh substrate+ctx), like the other
worlds, so choose_action can preview candidate counts without corrupting state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph


@dataclass
class NumberWorld:
    """A 1D line of natural numbers the agent walks by counting. Immutable
    config only; the mutable focus position lives in ctx, threaded by the
    driver (so previews don't mutate the world)."""

    window: int = 2          # numbers visible on each side of the focus
    unit_cap: int = 12       # cap on tokens rendered per number (keeps it small)
    max_n: int = 40          # ceiling the agent can count to

    def reset(self) -> tuple[Any, dict]:
        ctx = {"focus": 0, "max_seen": 0, "tick": 0}
        return self._build(ctx), ctx

    def _build(self, ctx: dict) -> Any:
        """Fresh substrate for the current focus. Locality: only numbers within
        ``window`` of the focus are sensed — further numbers are not yet seen,
        the agent must count toward them."""
        g = TypedGraph()
        focus = ctx["focus"]
        lo, hi = max(0, focus - self.window), focus + self.window
        # A cursor (Body) marks where the agent is on the line — its "position",
        # like the body's x in space. It carries no magnitude label.
        body_id = g._insert_node("Body", {"id": "cursor"})
        num_ids: dict[int, Any] = {}
        for k in range(lo, hi + 1):
            # ``value`` is the magnitude as a raw quantity the number carries —
            # like a coordinate, not a label (the agent still grounds even /
            # prime / divides over it). It does not collapse, so arithmetic
            # stays exact at any scale. Its MEANING is grounded in cardinality:
            # small numbers (k ≤ unit_cap) also carry that many countable Unit
            # tokens, so the agent can SEE that value == "this many" and learn
            # what the quantity means — then carry it symbolically beyond what
            # it can enumerate, the way a child grounds 1–10 by counting and
            # then trusts the numeral.
            num_ids[k] = g._insert_node("Number", {"id": f"num_{k}", "value": k})
            if k <= self.unit_cap:
                for i in range(k):
                    u = g._insert_node("Unit", {"id": f"unit_{k}_{i}"})
                    g._insert_edge(num_ids[k], "has_unit", u)
        # Successor structure — the spine of the line (purely relational, like
        # cell adjacency in the map). next_to is symmetric-ish via succ/pred.
        for k in range(lo, hi):
            if k in num_ids and (k + 1) in num_ids:
                g._insert_edge(num_ids[k], "succ", num_ids[k + 1])
        # Where the agent is standing.
        if focus in num_ids:
            g._insert_edge(body_id, "at", num_ids[focus])
        substrate = Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))
        return substrate

    def legal_actions(self, ctx: dict, agent_id: str, agent) -> list:
        acts = [("count_up",)]
        if ctx["focus"] > 0:
            acts.append(("count_down",))
        acts.append(("stay",))
        return acts

    def interpret_acts_on(self, ctx: dict, action) -> list[str]:
        """What the action touches — counting moves the cursor along Numbers
        (and reveals their Units)."""
        if action[0] in ("count_up", "count_down"):
            return ["Body", "Number"]
        return []

    def apply_action(self, ctx: dict, action) -> tuple[Any, dict]:
        """Stateless: return the future (substrate, ctx)."""
        focus = ctx["focus"]
        if action[0] == "count_up":
            focus = min(self.max_n, focus + 1)
        elif action[0] == "count_down":
            focus = max(0, focus - 1)
        new_ctx = {
            "focus": focus,
            "max_seen": max(ctx["max_seen"], focus),
            "tick": ctx["tick"] + 1,
        }
        return self._build(new_ctx), new_ctx


def number_world_handle(world: NumberWorld, agent) -> dict:
    """World handle for a CuriousAgent."""
    def reset():
        return world.reset()

    def legal_actions(s, ctx):
        return world.legal_actions(ctx, "agent", agent)

    def apply_action(s, ctx, action):
        return world.apply_action(ctx, action)

    def interpret_acts_on(s, ctx, action):
        return world.interpret_acts_on(ctx, action)

    return {
        "name": "number",
        "reset": reset,
        "legal_actions": legal_actions,
        "apply_action": apply_action,
        "interpret_acts_on": interpret_acts_on,
    }
