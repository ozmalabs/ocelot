"""PUSH WORLD — a thin pixel+affordance world adapter (inertial mass by action).

The agent PUSHES objects it sees and discovers their HIDDEN inertial mass FROM
THE PUSH — the operational definition of inertial mass, F=ma inverted
(m = impulse / Δv). The world's ONLY outputs are PIXELS (a 0/1 cell field the eye
carves) and AFFORDANCES (push actions). Each object carries a HIDDEN inertial
mass in the world's PRIVATE Python state (`_objects[i]['mass']`), drawn from an
UNTUNED distribution. **That mass is NEVER written to the graph.**

DISCIPLINE (CLAUDE.md — the agent is a graph; Python is only the world adapter):
- Object mass/position/velocity live ONLY as Python locals in `_objects`. Pixels
  (via `native.segment`) and the eye's own `Region` carve are the only things that
  reach the graph. The `mass` field is private and is asserted absent from the
  graph by the gate.
- No agent decisions in Python. The CHOICE of push is the existing
  `choose_action_meta_curious` machinery (+ `target_fn` → the SEEN object). The
  mass DISCOVERY is the existing order-N / invariance machinery
  (`TimeInfer` / `time_axis`) + the graph-native `seeds/mass_by_action.json` rule
  (`m = IDiv(J, |acceleration|)`). This module only renders pixels, applies the
  world's physical response `Δv = impulse / mass`, integrates, and reads the eye's
  carve + the minted `MassScalar` back out. It computes NO `impulse/Δv`.
- Grouping "same object" is the eye's persistent `Region` identity, NEVER a world
  id. The private object→region map below is used ONLY to APPLY force and to bind
  the `seen_as` action bonus — never to group masses (the mass rule keys on the
  Region node the trajectory Observation points at via `of_region`).

Physics: no gravity, no friction. A sustained push (the same action every tick)
adds `Δv = J/m` per tick, so the object accelerates UNIFORMLY at `a = J/m`; the eye
tracks it as ONE Region and order-N mints ORDER-2 (`coeffs[1]` = a). A single push
then coast is constant velocity → order-1 → no acceleration → no mass minted.
"""
from __future__ import annotations

import json
import os
from typing import Any

DT = ["pred", "coord:r", "coord:c", "val"]
MIN_ORBIT = 4   # order-2 witness minimum (see falling_world) — repeated-push evidence


def _render(objects, h: int, w: int, k: int) -> list[int]:
    """Row-major 0/1 field: a k×k square of 1 at each object's rounded (row,col),
    clipped to the field. Pure pixels — no kinematics reach the graph."""
    grid = [0] * (h * w)
    for ob in objects:
        top = int(round(ob["row"]))
        left = int(round(ob["col"]))
        for r in range(top, top + k):
            if 0 <= r < h:
                base = r * w
                for c in range(left, left + k):
                    if 0 <= c < w:
                        grid[base + c] = 1
    return grid


def boot_push():
    """Boot a full WorldAdapter (for choose_action_meta_curious) with BOTH the eye
    and the order-N + mass-by-action discovery machinery. Mirrors
    falling_world.boot_falling but on a WorldAdapter, and adds the
    `mass_by_action` seed. Pure setup — no agent decisions."""
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains import reflective_faculty as rf

    wa = WorldAdapter()
    native = wa.inner
    rf._ensure_shape_decode_loop(wa.s, native, wa.agent)
    native.load_seed_manifest(manifest_for("time_axis"), wa.agent)
    wa.s.set_attr(wa.agent, "time_infer_enabled", 1.0)
    wa.s.add_node("ShapeSignature",
                  {"name": "pt", "signature": json.dumps([["obj", 0, 0, "obj"]]),
                   "kind": "faculty", "faculty": "pt", "dim_types": DT})
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "seeds", "region_grouping.json")) as fh:
        for prod in json.load(fh)["productions"]:
            try:
                native.add_production(prod)
            except Exception:
                pass
    native.load_seed_manifest(manifest_for("mass_by_action"), wa.agent)
    return wa


class PushWorld:
    """A pixel+affordance push world over a WorldAdapter. Objects (blobs) with
    HIDDEN mass; the agent pushes SEEN Regions; mass is discovered by action."""

    def __init__(self, wa, h: int, w: int, k: int, objects: list[dict],
                 impulse_menu: list[int], axis: str = "col"):
        # objects: [{"mass": <hidden>, "row": float, "col": float, "vel": float}]
        self.wa = wa
        self.native = wa.inner
        self.s = wa.s
        self.ag = wa.agent
        self.h, self.w, self.k = h, w, k
        self._objects = [dict(o) for o in objects]   # PRIVATE; mass never graphed
        for o in self._objects:
            o.setdefault("vel", 0.0)
        self.menu = list(impulse_menu)
        self.axis = axis                              # "col" (rightward) or "row"
        self.game = self.s.add_node("WorldInstance", {"frame": 0.0, "world_type": "Game"})
        cells = [self.s.add_node("WorldInstance", {}) for _ in range(h * w)]
        self.cell_ids = [int(str(n).lstrip("#")) for n in cells]
        # per-object Body WorldInstance nodes — ONLY for the seen_as action bonus,
        # NEVER read for mass grouping (grouping is by perceived Region).
        self.bodies = [self.s.add_node("WorldInstance", {"world_type": "Body"})
                       for _ in self._objects]
        self.tick = 0
        self.region2object: dict = {}   # Region node -> object index (world-private)
        self.region2body: dict = {}     # Region node -> body index  (world-private)
        # per-Region perceived trajectory + the (constant) impulse pushed with
        self.trajectories: dict = {}
        self._segment()

    # ── perception (mechanical: render pixels, run eye, read carve) ────────────
    def _regions(self) -> list[dict]:
        out = []
        for n in self.native.neighbours(self.game, "has_region"):
            a = self.s.node(n)["attrs"]
            out.append({"node": n, "id": int(str(n).lstrip("#")),
                        "count": float(a.get("count", 0.0)),
                        "cy": float(a.get("cy", 0.0)), "cx": float(a.get("cx", 0.0)),
                        "drow": float(a.get("drow", 0.0)), "dcol": float(a.get("dcol", 0.0)),
                        "is_ground": float(a.get("is_ground", 0.0))})
        return out

    def _regions_nonground(self) -> list[dict]:
        return [r for r in self._regions() if r["is_ground"] == 0.0]

    def _obj_centroid(self, ob) -> tuple[float, float]:
        return (ob["row"] + (self.k - 1) / 2.0, ob["col"] + (self.k - 1) / 2.0)

    def _segment(self) -> list[dict]:
        vals = _render(self._objects, self.h, self.w, self.k)
        self.s.set_attr(self.game, "frame", float(self.tick))
        self.native.segment(self.game, self.h, self.w, vals, self.cell_ids)
        regions = self._regions_nonground()
        # world-private nearest-centroid map region<->object (to apply force / bind
        # seen_as). NOT published; NOT used for mass grouping.
        self.region2object, self.region2body = {}, {}
        for r in regions:
            best_i, best_d = None, None
            for i, ob in enumerate(self._objects):
                cy, cx = self._obj_centroid(ob)
                d = (cy - r["cy"]) ** 2 + (cx - r["cx"]) ** 2
                if best_d is None or d < best_d:
                    best_d, best_i = d, i
            if best_i is not None:
                self.region2object[r["node"]] = best_i
                self.region2body[r["node"]] = best_i
                # bind seen_as (object body SEEN as this Region) — the see→link→ACT
                # bonus target for choose_action_meta_curious.
                if r["node"] not in self.native.neighbours(self.bodies[best_i], "seen_as"):
                    self.native.add_edge_unchecked(self.bodies[best_i], "seen_as", r["node"])
            # collect the perceived trajectory per persistent Region node
            tr = self.trajectories.setdefault(r["node"], {"cy": [], "cx": [], "impulse": None})
            tr["cy"].append(r["cy"])
            tr["cx"].append(r["cx"])
        return regions

    # ── affordances (four-callable-compatible handle) ─────────────────────────
    def legal_actions(self) -> list:
        acts = []
        for r in self._regions_nonground():
            for J in self.menu:
                acts.append(("push", r["node"], J))
        return acts

    def interpret_acts_on(self, action) -> list[str]:
        return ["Body"]

    def target_fn(self, action):
        """The SEEN object (Body WorldInstance) this push acts on — it carries a
        seen_as edge to the perceived Region, so acting on it is meta-curious."""
        _, rnode, _J = action
        bi = self.region2body.get(rnode)
        return self.bodies[bi] if bi is not None else None

    def _push(self, rnode, J) -> None:
        """Apply the world's PHYSICAL response to ONE pushed object: Δv = impulse /
        hidden_mass. No integration yet. Mass is the world's PRIVATE resistance."""
        oi = self.region2object.get(rnode)
        if oi is None:
            return
        ob = self._objects[oi]
        ob["vel"] += J / ob["mass"]               # Δv = impulse / hidden_mass
        tr = self.trajectories.get(rnode)         # record the (constant) impulse
        if tr is not None:
            tr["impulse"] = J if tr["impulse"] in (None, J) else "mixed"

    def _step(self) -> None:
        """Integrate ALL objects one tick (semi-implicit Euler), re-render, re-observe."""
        for ob in self._objects:
            ob[self.axis] += ob["vel"]
        self.tick += 1
        self._segment()

    def apply_action(self, action) -> None:
        """Push one chosen object, then advance the world one tick."""
        _, rnode, J = action
        self._push(rnode, J)
        self._step()

    def apply_pushes(self, actions) -> None:
        """Push several objects this tick (one action each), then advance ONCE —
        so every pushed object gets a sustained per-tick impulse in lockstep."""
        for _, rnode, J in actions:
            self._push(rnode, J)
        self._step()

    def handle(self) -> dict:
        return {"name": "push", "legal_actions": self.legal_actions,
                "apply_action": self.apply_action,
                "interpret_acts_on": self.interpret_acts_on,
                "target_fn": self.target_fn}

    # ── mass discovery (feed perceived trajectories -> order-N + mass rule) ────
    def discover_masses(self) -> None:
        """Feed each PERCEIVED Region's cy/cx trajectory (grouped by the eye's
        persistent Region node — the perceived identity) into the order-N /
        mass-by-action pipeline as an Observation `of_region` that Region, carrying
        the impulse it was pushed with. The order-2 acceleration + the graph-native
        `mass_from_push` rule mint a MassScalar. Mechanical ingest only; the
        DECISION (order-N + m=J/a) is the graph."""
        live = set(self.native.neighbours(self.game, "has_region"))
        for rnode, tr in self.trajectories.items():
            if rnode not in live:          # a reaped (dead) Region — skip
                continue
            if len(tr["cy"]) < MIN_ORBIT or not isinstance(tr["impulse"], int):
                continue
            frames = [[["obj", int(round(y)), int(round(x)), "obj"]]
                      for y, x in zip(tr["cy"], tr["cx"])]
            o = self.s.add_node("Observation",
                                {"frames": frames, "dim_types": DT,
                                 "status": "motion_seq", "key": ["motion"],
                                 "impulse": tr["impulse"]})
            self.s.add_edge(self.ag, "observed", o)
            self.s.add_edge(o, "of_region", rnode)
        self.native.run_rules()

    def masses_by_region(self) -> dict:
        """Read minted MassScalars back out FROM THE GRAPH, keyed by perceived
        Region node. {region_node: [mass, ...]}. No world mass/id is read."""
        out = {}
        live = set(self.native.neighbours(self.game, "has_region"))
        for rnode in self.trajectories:
            if rnode not in live:
                continue
            ms = [self.s.node(n)["attrs"].get("mass")
                  for n in self.native.neighbours(rnode, "has_mass")]
            if ms:
                out[rnode] = sorted(ms)
        return out


def run_push_episode(pw: PushWorld, n_ticks: int) -> list:
    """Drive the agent's own action loop: each tick the agent CHOOSES a push on a
    SEEN Region via choose_action_meta_curious (+ target_fn → the seen Body), the
    world applies the physical response, the eye re-observes. Returns the list of
    chosen actions. No agent decision in Python — the choice is the seeded score."""
    chosen = []
    for _ in range(n_ticks):
        acts = pw.legal_actions()
        if not acts:
            break
        action = pw.wa.choose_action_meta_curious(
            acts, lambda a: None, pw.interpret_acts_on, pw.target_fn)
        chosen.append(action)
        pw.apply_action(action)
    return chosen


def run_push_all(pw: PushWorld, n_ticks: int, impulse: int) -> None:
    """Sustained push of EVERY currently-seen object each tick with `impulse` (one
    push per live Region), integrating once per tick. Used for the multi-object
    ratio / equal-mass arms where each object must accelerate uniformly. Still the
    world's action machinery (`_push`/`_step`); no agent decision in Python."""
    for _ in range(n_ticks):
        acts = [("push", r["node"], impulse) for r in pw._regions_nonground()]
        if not acts:
            break
        pw.apply_pushes(acts)
