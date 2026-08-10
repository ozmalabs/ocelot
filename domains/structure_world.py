"""Structure world — the agent's second mathematical floor: SETS and FUNCTIONS.

The number world grounded magnitude in countable units. The next floor up is
the structure most of mathematics is actually built from: a SET is a thing with
ELEMENTS (membership), a FUNCTION is a set of ordered PAIRS carrying one element
to another (maps, composition). These are even more directly perceivable than
number — the structure *is* the perception: the agent sees which elements a set
holds and which element each pair carries to which.

As always the world publishes only raw structure (element / pair / dom / cod
edges between identified objects) — never "this is injective", "this is a
subgroup", or any label. The agent grounds ``member`` / ``subset`` /
``injective`` / … as Term-trees over what it perceives, and from this floor the
road climbs toward ``group`` and ``homomorphism`` (a set + an operation).

A small fixed universe, fully observed (structure, not space, is the point);
a cursor focuses one object at a time for attention. Stateless apply_action,
like the other worlds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph


@dataclass
class StructureWorld:
    """A small universe of sets and functions over shared elements."""

    elements: tuple[str, ...] = ("e1", "e2", "e3", "e4")
    # name -> the elements it contains
    sets: dict = field(default_factory=lambda: {
        "A": ("e1", "e2", "e3"),
        "B": ("e2", "e3", "e4"),
        "C": ("e1", "e2"),                 # ⊆ A
    })
    # name -> ordered (domain, codomain) pairs
    functions: dict = field(default_factory=lambda: {
        "f": (("e1", "e2"), ("e2", "e3"), ("e3", "e4")),   # injective
        "g": (("e1", "e2"), ("e2", "e2"), ("e3", "e4")),   # NOT injective
    })
    # A group = a carrier set + a binary operation, given as a Cayley table
    # {(left, right): result}. The agent perceives the table as OpTriples and
    # grounds the axioms (closure, identity, inverse, commutativity) over it.
    groups: dict = field(default_factory=lambda: {
        # ℤ/3 under addition mod 3 — a real abelian group.
        "Z3": {"carrier": ("z0", "z1", "z2"),
               "op": {(f"z{i}", f"z{j}"): f"z{(i + j) % 3}"
                      for i in range(3) for j in range(3)}},
        # left-projection a∘b = a — closed & associative, but NO identity and
        # NOT commutative, so NOT a group. The negative control.
        "Lp": {"carrier": ("z0", "z1", "z2"),
               "op": {(f"z{i}", f"z{j}"): f"z{i}"
                      for i in range(3) for j in range(3)}},
    })
    # Maps BETWEEN groups — functions that carry from_group/to_group, so the
    # agent can ground homomorphism (preserves the operation: f(a∘b)=f(a)∘f(b)).
    group_maps: dict = field(default_factory=lambda: {
        # ×2 mod 3 (an automorphism of ℤ/3) — a real homomorphism.
        "double": {"from": "Z3", "to": "Z3",
                   "map": {"z0": "z0", "z1": "z2", "z2": "z1"}},
        # swap 0,1 — f(0+0)=f(0)=1 but f(0)+f(0)=1+1=2 — NOT a homomorphism.
        "swap": {"from": "Z3", "to": "Z3",
                 "map": {"z0": "z1", "z1": "z0", "z2": "z2"}},
    })
    # Rings = a carrier with TWO operations (+ and ×), given as two Cayley
    # tables. The floor where field grounds (ℤ/p is a field; ℤ/4 is not — 2 has
    # no multiplicative inverse). Algebraic number theory's base.
    rings: dict = field(default_factory=lambda: {
        # ℤ/3 — a FIELD (every nonzero element is invertible).
        "Z3": {"carrier": tuple(f"z{i}" for i in range(3)),
               "add": {(f"z{i}", f"z{j}"): f"z{(i + j) % 3}"
                       for i in range(3) for j in range(3)},
               "mul": {(f"z{i}", f"z{j}"): f"z{(i * j) % 3}"
                       for i in range(3) for j in range(3)}},
        # ℤ/4 — a ring but NOT a field (2·2=0; 2 has no inverse).
        "Z4": {"carrier": tuple(f"w{i}" for i in range(4)),
               "add": {(f"w{i}", f"w{j}"): f"w{(i + j) % 4}"
                       for i in range(4) for j in range(4)},
               "mul": {(f"w{i}", f"w{j}"): f"w{(i * j) % 4}"
                       for i in range(4) for j in range(4)}},
    })

    # Cyclic groups given ONLY by a generator's action — a single `g_acts`
    # edge per element forming a cycle (e → g → g² → … → e). No Cayley table:
    # the whole operation is RECOVERED by recursion (apply g_acts k times). The
    # cycle closing back to e is the reflexive rule that makes the group finite;
    # drop the closure and the same rule generates an infinite group (ℤ). This
    # is "infinity as recursion on a reflexive graph" at the structure floor.
    cyclic: dict = field(default_factory=lambda: {"C5": 5})
    # An INFINITE cyclic group ℤ = ⟨g⟩: the SAME generator rule as a finite
    # cyclic group, but the g_acts chain does NOT close back to e. Finiteness
    # is exactly the closure (the reflexive edge home); without it the same
    # rule generates the infinite. The world shows a finite prefix; the rule is
    # what's infinite. (`order` 0 = unbounded.) Reached by recursion, never a
    # table — a table for ℤ would be infinite.
    open_cyclic: dict = field(default_factory=lambda: {"Zinf": 12})

    def _objects(self) -> list[str]:
        return ([f"set_{s}" for s in self.sets]
                + [f"fn_{f}" for f in self.functions]
                + [f"grp_{g}" for g in self.groups]
                + [f"hom_{h}" for h in self.group_maps]
                + [f"ring_{r}" for r in self.rings]
                + [f"cyc_{c}" for c in self.cyclic]
                + [f"inf_{c}" for c in self.open_cyclic])

    def reset(self) -> tuple[Any, dict]:
        ctx = {"focus": 0, "tick": 0}
        return self._build(ctx), ctx

    def _build(self, ctx: dict) -> Any:
        g = TypedGraph()
        elem_id: dict[str, Any] = {}

        def elem(name: str):
            if name not in elem_id:
                elem_id[name] = g._insert_node("Element", {"id": name})
            return elem_id[name]

        # Sets with membership edges.
        node_id: dict[str, Any] = {}
        for name, members in self.sets.items():
            sid = g._insert_node("MathSet", {"id": f"set_{name}"})
            node_id[f"set_{name}"] = sid
            for e in members:
                g._insert_edge(sid, "element", elem(e))
        # Functions as collections of ordered pairs (dom -> cod).
        for name, pairs in self.functions.items():
            fid = g._insert_node("Function", {"id": f"fn_{name}"})
            node_id[f"fn_{name}"] = fid
            for i, (dom, cod) in enumerate(pairs):
                pid = g._insert_node("OrderedPair", {"id": f"pair_{name}_{i}"})
                g._insert_edge(fid, "pair", pid)
                g._insert_edge(pid, "dom", elem(dom))
                g._insert_edge(pid, "cod", elem(cod))
        # Groups: a carrier MathSet + the operation as OpTriples (left,right -> result).
        for name, spec in self.groups.items():
            gid = g._insert_node("Group", {"id": f"grp_{name}"})
            node_id[f"grp_{name}"] = gid
            cid = g._insert_node("MathSet", {"id": f"car_{name}"})
            g._insert_edge(gid, "carrier", cid)
            for e in spec["carrier"]:
                g._insert_edge(cid, "element", elem(e))
            for (a, b), c in spec["op"].items():
                tid = g._insert_node("OpTriple", {"id": f"op_{name}_{a}_{b}"})
                g._insert_edge(gid, "op_triple", tid)
                g._insert_edge(tid, "left", elem(a))
                g._insert_edge(tid, "right", elem(b))
                g._insert_edge(tid, "result", elem(c))
        # Group maps: a Function between two groups' carriers, tagged with the
        # source/target groups so the preservation law is checkable.
        for name, spec in self.group_maps.items():
            mid = g._insert_node("Function", {"id": f"hom_{name}"})
            node_id[f"hom_{name}"] = mid
            g._insert_edge(mid, "from_group", node_id[f"grp_{spec['from']}"])
            g._insert_edge(mid, "to_group", node_id[f"grp_{spec['to']}"])
            for i, (dom, cod) in enumerate(spec["map"].items()):
                pid = g._insert_node("OrderedPair", {"id": f"mpair_{name}_{i}"})
                g._insert_edge(mid, "pair", pid)
                g._insert_edge(pid, "dom", elem(dom))
                g._insert_edge(pid, "cod", elem(cod))
        # Rings: a carrier MathSet + two operation tables (add / mul).
        for name, spec in self.rings.items():
            rid = g._insert_node("Ring", {"id": f"ring_{name}"})
            node_id[f"ring_{name}"] = rid
            cid = g._insert_node("MathSet", {"id": f"rcar_{name}"})
            g._insert_edge(rid, "carrier", cid)
            for e in spec["carrier"]:
                g._insert_edge(cid, "element", elem(e))
            for opname, edge in (("add", "add_triple"), ("mul", "mul_triple")):
                for (a, b), c in spec[opname].items():
                    tid = g._insert_node("OpTriple",
                                         {"id": f"{opname}_{name}_{a}_{b}"})
                    g._insert_edge(rid, edge, tid)
                    g._insert_edge(tid, "left", elem(a))
                    g._insert_edge(tid, "right", elem(b))
                    g._insert_edge(tid, "result", elem(c))
        # Cyclic groups: a generator action only (a cycle of g_acts edges).
        for name, n in self.cyclic.items():
            gid = g._insert_node("CyclicGroup", {"id": f"cyc_{name}", "order": n})
            node_id[f"cyc_{name}"] = gid
            els = [g._insert_node("GElem", {"id": f"{name}_e{i}"}) for i in range(n)]
            for i in range(n):
                g._insert_edge(els[i], "g_acts", els[(i + 1) % n])   # the cycle
                g._insert_edge(gid, "has_elem", els[i])
            g._insert_edge(gid, "identity", els[0])
        # Infinite cyclic groups: the generator chain WITHOUT the closing edge
        # (e0 → e1 → … → e_{n-1}, and it stops — no return to e0). A finite
        # prefix of an object the rule generates without end.
        for name, n in self.open_cyclic.items():
            gid = g._insert_node("CyclicGroup", {"id": f"inf_{name}", "order": 0})
            node_id[f"inf_{name}"] = gid
            els = [g._insert_node("GElem", {"id": f"{name}_e{i}"}) for i in range(n)]
            for i in range(n - 1):                          # open: no wrap-around
                g._insert_edge(els[i], "g_acts", els[i + 1])
            for e in els:
                g._insert_edge(gid, "has_elem", e)
            g._insert_edge(gid, "identity", els[0])
        # A cursor marks the object the agent is attending to.
        objs = self._objects()
        body_id = g._insert_node("Body", {"id": "cursor"})
        focus_node = node_id.get(objs[ctx["focus"] % len(objs)])
        if focus_node is not None:
            g._insert_edge(body_id, "at", focus_node)
        return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))

    def legal_actions(self, ctx: dict, agent_id: str, agent) -> list:
        return [("focus_next",), ("focus_prev",), ("look",)]

    def interpret_acts_on(self, ctx: dict, action) -> list[str]:
        if action[0] in ("focus_next", "focus_prev"):
            return ["Body"]
        return []

    def apply_action(self, ctx: dict, action) -> tuple[Any, dict]:
        n = len(self._objects())
        focus = ctx["focus"]
        if action[0] == "focus_next":
            focus = (focus + 1) % n
        elif action[0] == "focus_prev":
            focus = (focus - 1) % n
        new_ctx = {"focus": focus, "tick": ctx["tick"] + 1}
        return self._build(new_ctx), new_ctx


def structure_world_handle(world: StructureWorld, agent) -> dict:
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
        "name": "structure",
        "reset": reset,
        "legal_actions": legal_actions,
        "apply_action": apply_action,
        "interpret_acts_on": interpret_acts_on,
    }
