"""GALILEO WORLD — the equivalence principle, discovered by shoving and staring.

A thin pixel+affordance world adapter that COMPOSES two landed primitives:

1. **Inertial mass by action** (`domains/push_world.py` + `seeds/mass_by_action.json`):
   the robot PUSHES each seen object horizontally and the substrate mints a
   per-object `MassScalar = impulse/Δv` from the perceived acceleration, grouped
   by the eye's PERCEIVED `Region`. The masses DIFFER across objects.

2. **The fall discovered by the eye** (`domains/falling_world.py` machinery /
   `seeds/time_axis.json`): each object falls under gravity; the eye tracks it;
   the generic order-N loop mints an order-2 `latent:time` generator whose
   `coeffs[1]` is the perceived fall acceleration.

The NEW content is NOT a physics law. It is `seeds/galileo.json`: a GENERAL
cross-object generator codebook (recognize-or-mint keyed on the `coeffs`
signature). In the REAL world every object falls at the SAME acceleration, so
exactly ONE `MotionGenerator{kind=fall}` is minted and every other object's fall
is RECOGNIZED against it — while the `MassScalar`s differ. "One fall generator
across objects of measured-different mass" IS `acc ⊥ mass`, read from the graph.
In the ARISTOTLE control (heavier falls faster) the accelerations differ, so N
distinct generators are minted (mass-dependence correctly found). Same pipeline.

DISCIPLINE (CLAUDE.md): the object mass/position/velocity/gravity live ONLY as
Python locals; NOTHING kinematic is graphed (pixels + affordances out). No agent
decision in Python — the mass discovery is the `mass_by_action` rule, the fall
order-N is `TimeInfer`, and the cross-object recognition is the three general
`galileo.json` rules. This module renders pixels, applies the world's physical
response, and mechanically reads the eye's carve + the minted graph nodes back.
"""
from __future__ import annotations

import json
import os

from domains.push_world import _render, PushWorld, run_push_all

DT = ["pred", "coord:r", "coord:c", "val"]
MIN_ORBIT = 4   # order-2 witness minimum (>=4 perceived samples)


def boot_galileo():
    """Boot a WorldAdapter with the eye + order-N + mass-by-action + the general
    galileo generator codebook. Mirrors push_world.boot_push and adds
    seeds/galileo.json. Pure setup — no agent decisions."""
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
    native.load_seed_manifest(manifest_for("galileo"), wa.agent)
    return wa


class GalileoWorld:
    """N blobs with HIDDEN mass. Phase 1: push each horizontally -> MassScalar by
    action. Phase 2: drop each -> fall generator, deduped across objects by the
    general codebook. `gravity_fn(i)` returns object i's fall acceleration: a
    constant `g` for the real world, a mass-dependent value for Aristotle."""

    def __init__(self, wa, h: int, w: int, k: int, masses: list[int],
                 impulse_menu: list[int], gravity_fn,
                 fall_cols: list[int] | None = None):
        self.wa = wa
        self.native = wa.inner
        self.s = wa.s
        self.ag = wa.agent
        self.h, self.w, self.k = h, w, k
        self.masses = list(masses)               # HIDDEN — never graphed
        self.impulse_menu = list(impulse_menu)
        self.gravity_fn = gravity_fn
        n = len(self.masses)
        # well-separated columns so the eye carves N distinct Regions
        self.fall_cols = fall_cols or [3 + i * max(2 * k, 6) for i in range(n)]
        self._mass_pws: list = []                # per-object push episodes
        self.fall_traj: dict = {}                # perceived Region node -> [cy...]

    # ── PHASE 1: push -> mass by action (reuse the landed primitive verbatim) ──
    def measure_masses(self, n_push: int = 6) -> list:
        """The robot PROBES each object with the impulse menu (the landed
        primitive's own methodology): each object is pushed on its OWN in a
        single-object episode per menu impulse; a resonant impulse (a = J/m
        integer, a ≤ span+2) mints a MassScalar = impulse/Δv on that object's
        PERCEIVED Region. No hidden mass is used to choose the impulse — the menu
        is probed and the graph decides which impulse resonates. Returns the
        distinct minted MassScalar values FROM THE GRAPH."""
        pw_w = max(self.w, 60)
        for i, m in enumerate(self.masses):
            for J in self.impulse_menu:
                objs = [{"mass": m, "row": 3.0, "col": 3.0}]
                pw = PushWorld(self.wa, 12, pw_w, self.k, objs, [J], axis="col")
                run_push_all(pw, n_push, J)
                pw.discover_masses()
                self._mass_pws.append(pw)
        return self.minted_masses()

    # ── PHASE 2: drop -> fall generator, deduped across objects ───────────────
    def watch_falls(self, n_fall: int = 6) -> None:
        """Each object falls straight down under gravity_fn(i) in a FRESH game
        hub; the eye tracks each as a persistent Region; each perceived fall
        trajectory is fed as an Observation tagged motion_kind='fall',
        gen_track=1. The order-N loop mints its order-2 generator and the general
        galileo codebook recognizes-or-mints across objects. Mechanical ingest;
        the DECISION is the graph."""
        game = self.s.add_node("WorldInstance", {"frame": 0.0, "world_type": "Game"})
        cells = [self.s.add_node("WorldInstance", {}) for _ in range(self.h * self.w)]
        cell_ids = [int(str(n).lstrip("#")) for n in cells]
        objs = [{"row": 1.0, "col": float(self.fall_cols[i]), "vy": 0.0,
                 "g": int(self.gravity_fn(i))}
                for i in range(len(self.masses))]
        self._fall_game = game
        traj: dict = {}
        for t in range(n_fall):
            vals = _render(objs, self.h, self.w, self.k)
            self.s.set_attr(game, "frame", float(t))
            self.native.segment(game, self.h, self.w, vals, cell_ids)
            for n in self.native.neighbours(game, "has_region"):
                a = self.s.node(n)["attrs"]
                if float(a.get("is_ground", 0.0)) != 0.0:
                    continue
                tr = traj.setdefault(n, {"cy": [], "cx": []})
                tr["cy"].append(float(a.get("cy", 0.0)))
                tr["cx"].append(float(a.get("cx", 0.0)))
            for o in objs:                        # semi-implicit Euler fall
                o["vy"] += o["g"]
                o["row"] += o["vy"]
        self.fall_traj = traj
        live = set(self.native.neighbours(game, "has_region"))
        for rnode, tr in traj.items():
            if rnode not in live or len(tr["cy"]) < MIN_ORBIT:
                continue
            frames = [[["obj", int(round(y)), int(round(x)), "obj"]]
                      for y, x in zip(tr["cy"], tr["cx"])]
            o = self.s.add_node("Observation",
                                {"frames": frames, "dim_types": DT,
                                 "status": "motion_seq", "key": ["motion"],
                                 "motion_kind": "fall", "gen_track": 1})
            self.s.add_edge(self.ag, "observed", o)
            # provenance: this fall generator is grouped by the eye's PERCEIVED
            # Region. A DISTINCT edge type (not of_region) so the mass_by_action
            # rule — which mints m=impulse/Δv on an of_region Observation — never
            # fires on a fall (a fall carries no impulse; of_region would mint a
            # spurious mass 0). Grouping stays perceived; masses stay push-only.
            self.s.add_edge(o, "fall_of_region", rnode)
        self.s.add_node("NativeGalileoReceipt", {
            "schema": "native_galileo_receipt_v1",
            "cluster": "galileo_world.fall_discovery",
            "provenance": "native_rule_readback:galileo_falls",
            "native_rule": "galileo_fall_native_rules",
            "native_steps": ["ingest_fall_trajectories", "run_rules", "readback"],
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        self.native.run_rules()

    # ── readers (mechanical; read minted graph nodes back out) ────────────────
    def fall_generators(self) -> list:
        """The distinct fall generators FROM THE GRAPH: MotionGenerator{kind=fall}
        nodes. Returns [(sig, order)...]. Real world -> 1; Aristotle -> N."""
        out = []
        for n in self.s.nodes("MotionGenerator"):
            a = self.s.node(n)["attrs"]
            if a.get("kind") == "fall":
                out.append((tuple(map(tuple, a.get("sig") or ())), a.get("order")))
        return out

    def fall_observation_status(self) -> list:
        """Per fall Observation: (generator_status, coeffs) read from the graph —
        'minted' for the survivor, 'recognized' for every peer of one generator."""
        out = []
        for n in self.s.nodes("Observation"):
            a = self.s.node(n)["attrs"]
            if a.get("motion_kind") == "fall" and a.get("gen_track") == 1:
                out.append((a.get("generator_status"),
                            tuple(map(tuple, a.get("gen_sig") or ()))))
        return out

    def minted_masses(self) -> list:
        """The DISTINCT minted MassScalar values FROM THE GRAPH, each reached only
        through a Region -has_mass-> MassScalar edge (grouped by the eye's
        PERCEIVED Region; the MassScalar carries no world object-id). Distinct
        across objects."""
        seen = []
        for rnode in self.s.nodes("Region"):
            for mn in self.native.neighbours(rnode, "has_mass"):
                v = self.s.node(mn)["attrs"].get("mass")
                if v is not None:
                    seen.append(v)
        return sorted(set(seen))
