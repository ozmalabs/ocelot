"""Physics WORLD ADAPTERS — free-fall, elastic collision, and lever.

RESTORED from the deleted originals (physics_world / collision_world /
lever_world at commit ebb8b63610), re-expressed for the seed-booted Rust
substrate. These are WORLD ADAPTERS in the CLAUDE.md sense: mechanical I/O that
simulates a world (owning its own real-valued state) and PUBLISHES ONLY
position + intrinsic mass into the graph each tick — never a velocity, never a
rate, never a derived quantity. Between publishes the RUST AGENT does the work
(`run_rules` fires seeds/physics_derivation.json). No conditionals over graph
state, no derivation, no decisions live here.

The invariant kept from the originals: "the world publishes POSITION and
intrinsic MASS only." The agent invents velocity/acceleration and discovers the
laws — see seeds/physics_derivation.json.

Usage (see tests/test_physics_derivation_migrated.py):

    from substrate.boot_core import boot_core
    from domains.physics_world import PhysicsWorld, run_world
    s, ag = boot_core()
    load_physics_seed(s, ag)
    run_world(s, ag, PhysicsWorld(), ticks=16)
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from substrate.seed_loader import manifest_for


def load_physics_seed(s, agent) -> None:
    """Mechanical seed I/O: install seeds/physics_derivation.json's rules."""
    s._inner.load_seed_manifest(manifest_for("physics_derivation"), agent)


# ===========================================================================
# Free fall — Galileo (acc ⟂ mass)
# ===========================================================================
@dataclass
class PhysicsWorld:
    n_balls: int = 3
    gravity: float = 1.0
    floor_y: float = 0.0
    ceiling_y: float = 80.0
    width: float = 80.0
    _bodies: dict = field(default_factory=dict, init=False, repr=False)
    _spawn_counter: int = field(default=0, init=False, repr=False)

    def __post_init__(self):
        self._bodies = {}
        self._spawn_counter = self.n_balls
        masses = [1.0, 4.0, 9.0]
        for i in range(self.n_balls):
            self._bodies[f"ball_{i}"] = {
                "type": "Ball", "x": float(8 + i * 12),
                "y": float(int(self.ceiling_y)), "vx": 0.0, "vy": 0.0,
                "mass": masses[i % len(masses)]}

    def step(self) -> None:
        respawn = []
        for bid, b in self._bodies.items():
            b["vy"] += -self.gravity              # gravity: an acceleration on every body regardless of mass
            b["y"] += b["vy"]
            if b["y"] <= self.floor_y:
                b["y"] = self.floor_y
                b["vy"] = 0.0
                b["rest"] = b.get("rest", 0) + 1  # rest a few ticks (contrast), then a FRESH id falls
                if b["rest"] >= 3:
                    respawn.append(bid)
        for bid in respawn:
            old = self._bodies.pop(bid)
            self._spawn_counter += 1
            self._bodies[f"ball_{self._spawn_counter}"] = {
                "type": "Ball", "x": old["x"], "y": float(int(self.ceiling_y)),
                "vx": 0.0, "vy": 0.0, "mass": old["mass"]}

    def publish(self) -> list[dict]:
        # POSITION + intrinsic MASS only. on_ground is a mechanical predicate on
        # position (as in the original), used by the derivation rule's regime.
        out = []
        for bid, b in self._bodies.items():
            out.append({
                "id": bid, "type_name": "Ball",
                "x_bin": int(round(b["x"])), "y_bin": int(round(b["y"])),
                "mass": b["mass"],
                "on_ground": 1 if b["y"] <= self.floor_y + 0.5 else 0})
        return out


# ===========================================================================
# Collision on a line — conservation of momentum Σ(m·v)
# ===========================================================================
@dataclass
class CollisionWorld:
    _pucks: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        self._pucks = [
            {"id": "a", "x": 0.0, "v": 3.0, "mass": 1.0},
            {"id": "b", "x": 8.0, "v": -1.0, "mass": 1.0},
            {"id": "c", "x": 40.0, "v": 0.0, "mass": 1.0}]

    def step(self) -> None:
        for p in self._pucks:
            p["x"] += p["v"]
        order = sorted(self._pucks, key=lambda p: p["x"])
        for i in range(len(order) - 1):
            a, b = order[i], order[i + 1]
            if abs(a["x"] - b["x"]) < 1.0 and a["v"] > b["v"]:
                a["v"], b["v"] = b["v"], a["v"]  # equal-mass elastic exchange

    def publish(self) -> list[dict]:
        # POSITION + intrinsic MASS only. y_bin held constant (1-D world).
        return [{"id": p["id"], "type_name": "Puck",
                 "x_bin": int(round(p["x"])), "y_bin": 0, "mass": p["mass"],
                 "on_ground": 0} for p in self._pucks]


# ===========================================================================
# Lever / balance — Archimedes (net torque = 0 at balance)
# ===========================================================================
@dataclass
class LeverWorld:
    seed: int = 0
    balanced_fraction: float = 0.4
    max_mass: int = 9
    max_dist: int = 6
    _rng: random.Random = field(default=None, init=False, repr=False)
    _cfg: dict = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self._rng = random.Random(self.seed)
        self._cfg = self._new_config()

    def _new_config(self) -> dict:
        rng = self._rng
        mL = rng.randint(1, self.max_mass)
        dL = rng.randint(1, self.max_dist)
        mR = dR = None
        if rng.random() < self.balanced_fraction:
            target = mL * dL
            divisors = [d for d in range(1, self.max_dist + 1)
                        if target % d == 0 and 1 <= target // d <= self.max_mass]
            if divisors:
                dR = rng.choice(divisors)
                mR = target // dR
        if mR is None:
            mR = rng.randint(1, self.max_mass)
            dR = rng.randint(1, self.max_dist)
        return {"mL": mL, "dL": dL, "mR": mR, "dR": dR}

    def step(self) -> None:
        self._cfg = self._new_config()

    def publish(self):
        # POSITION (signed arm) + intrinsic MASS + whether the beam is level.
        # Never a moment/torque — the agent forms that itself.
        c = self._cfg
        net = c["mR"] * c["dR"] - c["mL"] * c["dL"]
        return {
            "lever": {"balanced": 1 if net == 0 else 0},
            "weights": [
                {"id": "left", "type_name": "Weight", "mass": float(c["mL"]), "signed_distance": -c["dL"]},
                {"id": "right", "type_name": "Weight", "mass": float(c["mR"]), "signed_distance": c["dR"]}]}


# ===========================================================================
# The adapter loop — publish position+mass, tick, let Rust derive.
# ===========================================================================
def _sync_bodies(s, inner, sys_id, published, live, cur_tick, edge="has_body"):
    """Create/update body nodes to match `published`; remove gone ones.
    Pure mechanical translation of world state into graph nodes."""
    seen = set()
    for rec in published:
        bid = rec["id"]
        seen.add(bid)
        nid = live.get(bid)
        if nid is None:
            nid = s.add_node(rec["type_name"], {})
            inner.add_edge_unchecked(sys_id, edge, nid)
            live[bid] = nid
        for k, v in rec.items():
            s.set_attr(nid, k, v)
        s.set_attr(nid, "cur_tick", cur_tick)
    for bid in [b for b in live if b not in seen]:
        nid = live.pop(bid)
        if s.has_node(nid):
            s.remove_node(nid)


def run_world(s, agent, world, ticks: int) -> None:
    """Run a System-hub world (PhysicsWorld / CollisionWorld) for `ticks`
    steps, publishing position+mass and firing the agent each tick."""
    inner = s._inner
    sys_id = s.add_node("System", {})
    inner.add_edge_unchecked(agent, "owns_system", sys_id)
    live: dict = {}
    for t in range(ticks):
        world.step()
        s.set_attr(sys_id, "cur_tick", t)
        _sync_bodies(s, inner, sys_id, world.publish(), live, t)
        inner.run_rules(200_000)


def run_lever(s, agent, world, configs: int) -> None:
    """Run the LeverWorld for `configs` fresh configurations."""
    inner = s._inner
    lev_id = s.add_node("Lever", {})
    inner.add_edge_unchecked(agent, "owns_lever", lev_id)
    live: dict = {}
    for t in range(configs):
        if t > 0:
            world.step()
        pub = world.publish()
        s.set_attr(lev_id, "balanced", pub["lever"]["balanced"])
        s.set_attr(lev_id, "cur_tick", t)
        _sync_bodies(s, inner, lev_id, pub["weights"], live, t, edge="has_weight")
        inner.run_rules(200_000)
