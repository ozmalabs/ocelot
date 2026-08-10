"""THE JABBERWOCK DEBUGS ITSELF IN THE DEATH-WORLD — the boundary is fatal, and it fixes that itself.

Same generic self-debug stack as maze_autonomy / escalation_domain_agnostic (autonomy + investigation_loop
+ investigation_teacher + impasse_escalation), now pointed at a world where walking off the board ENDS the
agent (AvatarDeathEnv4, GAME_OVER, no clamp). The loop body is ONLY `master_tick(); tick()`:

  investigate the BLIND baseline (always Right) -> measure survival (it walks into the wall and dies, low) ->
  it stays below target and PLATEAUS (mf_stall) -> the ladder CLIMBS: order-2 change-method (no alternative)
  -> order-3 reframe -> order-4 AUTHOR A TOOL: the death-world REALISES the agent's order-4 request as a
  boundary-ROLLOUT survival method (roll the body forward by the action model; refuse actions that leave the
  board) -> investigate THAT -> it survives (high) -> the escalation RESOLVES at the goal.

This run is possible only because the self-debug ladder is now world-agnostic (the investigation executor
guarantees one fresh bank per trial, so mf_stall advances in ANY world — see ozma_self_debug_world_agnostic).
The world deliberately does NOT pass fresh=True to record_measured_capability, to prove that.

The only Python here is the world SURFACE: it MEASURES a named method's survival (mechanical, like maze_world
scoring a solver) and REALISES an authored faculty (like ArcWorld.author_faculty). The DECISION to climb and
to author is the agent's ladder, graph-native.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/play_death_autonomy.py [n_ticks]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from arc3_env import GameState, ACTION1, ACTION2, ACTION3, ACTION4
from stage2_phi_world import AvatarDeathEnv4, AV
from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.gap_prioritiser import record_measured_capability

SEP = "=" * 96
SEEDS = ["enact", "discourse", "autonomy", "investigation_loop", "investigation_teacher", "impasse_escalation"]
TARGET = 0.9
EVAL_STEPS = 40
_ACT = {"Up": ACTION1, "Down": ACTION2, "Left": ACTION3, "Right": ACTION4}
_DELTA = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}


def _bbox(grid):
    """The avatar's bounding box = the extent of the value-9 cells (the world's mechanical perception)."""
    rs = [r for r, row in enumerate(grid) for v in row if v == AV]
    cs = [c for row in grid for c, v in enumerate(row) if v == AV]
    if not rs:
        return None
    return min(rs), max(rs), min(cs), max(cs)


class DeathCapabilityWorld:
    """World SURFACE for the 'survive the boundary' capability. execute() MEASURES a named method's survival
    on a fresh episode; author_faculty() REALISES the agent's order-4 request as a runnable rollout method.
    No agent decision lives here — the ladder decides what to try and when to author."""

    def __init__(self, adapter, eval_steps=EVAL_STEPS):
        self.a = adapter
        self.s = adapter.s
        self.eval_steps = eval_steps

    def register_affordances(self):
        s = self.s
        for a, e, b in (("Operator", "applies_in", "Microtheory"),
                        ("CapabilityAxis", "investigated_by", "Operator")):
            try:
                s.add_production({"src": {"type": a, "var": "x"}, "edge_type": e,
                                  "tgt": {"type": b, "var": "y"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "death_world"})
            except Exception:
                pass
        mt = s.add_node("Microtheory", {"name": "death_world", "domain": "game"})
        op = s.add_node("Operator", {"name": "blind", "runner": "blind",
                                     "metric": "survival", "target": TARGET})
        s.add_edge(op, "applies_in", mt)
        ax = s.add_node("CapabilityAxis", {"is_axis": 1.0, "capability_keys": ["survive", "boundary"],
                                           "saturation": 0.0, "shortfall": 0.7, "min_order": 1.0,
                                           "investigated_count": 0, "mf_stall": 0})
        s.add_edge(ax, "investigated_by", op)
        s.add_edge(self.a.agent, "operates_in", mt)
        return ax

    # --- the world's mechanical survival measurement of a named method ---
    def _survival(self, method):
        env = AvatarDeathEnv4()
        f = env.reset()
        last = "Right"
        survived = 0
        for _ in range(self.eval_steps):
            act = method(f.grid, last)
            last = act
            f = env.step(_ACT[act], None)
            if f.state == GameState.GAME_OVER:
                break
            survived += 1
        return survived / self.eval_steps

    @staticmethod
    def _blind(grid, last):
        return "Right"                                   # no model of the boundary -> walks into the wall

    @staticmethod
    def _rollout(grid, last):
        """Roll the body forward by the action model; refuse any action whose rolled box leaves the board.
        Keep the current heading if it survives, else turn to the first surviving action."""
        bb = _bbox(grid)
        if bb is None:
            return last
        mnr, mxr, mnc, mxc = bb
        H = W = 20

        def safe(act):
            dr, dc = _DELTA[act]
            return 0 <= mnr + dr and mxr + dr < H and 0 <= mnc + dc and mxc + dc < W
        if safe(last):
            return last
        for act in ("Up", "Down", "Left", "Right"):
            if safe(act):
                return act
        return last

    def execute(self, req):
        op = req.get("operator")
        method = self._blind if op == "blind" else self._rollout    # authored ops use the rollout method
        surv = round(self._survival(method), 3)
        note = f"{op}: survived {int(surv*self.eval_steps)}/{self.eval_steps} steps -> survival {surv}"
        # DELIBERATELY no fresh=True: prove the world-agnostic executor advances mf_stall regardless.
        return record_measured_capability(
            self.s, req.get("capability_keys", ["survive", "boundary"]),
            measured=surv, target=float(req.get("target", TARGET) or TARGET),
            metric="survival", note=note)

    def author_faculty(self, capability_keys, approach=""):
        """REALISE the agent's order-4 request: a boundary-rollout survival method (the world supplies the
        runnable spec; the agent decided to author it). Mirrors ArcWorld.author_faculty."""
        return {"runner": "rollout", "metric": "survival", "target": TARGET,
                "name": "boundary_rollout",
                "approach": approach or "roll the body forward by the action model; refuse actions that leave the board"}


def _orders(adapter):
    o = 0
    for mi in adapter.s.nodes("Impasse"):
        a = adapter.s.node(mi)["attrs"]
        if a.get("kind") in ("escalation", "self_extend", "self_rethink") and a.get("order"):
            o = max(o, int(a["order"]))
    return o


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    print(SEP)
    print("DEATH-WORLD AUTONOMY — the jabberwock self-debugs a fatal boundary (loop = master_tick; tick).")
    print(SEP)
    adapter = WorldAdapter()
    for sid in SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
    world = DeathCapabilityWorld(adapter)
    ax = world.register_affordances()
    adapter.wire_autonomy_faculty()
    adapter.wire_enact_faculty()
    adapter.wire_investigation_faculty(world)            # the now-generic handle: ANY world
    adapter.wire_escalation_faculties()                  # order-4 self-extend authors the tool
    # NO set_self_teacher: the world realises the authored faculty; no how-to teacher needed.

    print("  booted the generic self-debug stack on the DEATH-world. given baseline: blind (always Right).")
    print(f"  survive target = {TARGET}. the ladder + authoring are graph-native; the loop is master_tick;tick.\n")

    seen_mc, seen_order, authored_op = set(), set(), None
    survivals, banked_seen = {}, set()
    for t in range(1, n_ticks + 1):
        adapter.master_tick(); adapter.tick()
        for mc in adapter.s.nodes("MeasuredCapability"):
            a = adapter.s.node(mc)["attrs"]
            note = a.get("note") or ""
            # the world reuses ONE node (fresh=False) — key the stream by trial signature, not node id,
            # so a re-measured (overwritten) node is still captured each time it changes.
            sig = (note, a.get("measured"))
            if sig in banked_seen:
                continue
            banked_seen.add(mc); banked_seen.add(sig)
            print(f"  [tick {t:3d}] RAN -> {note}")
            if "blind" in note:
                survivals["blind"] = a.get("measured")
            elif "rollout" in note:
                survivals["rollout"] = a.get("measured")
        o = _orders(adapter)
        if o and o not in seen_order:
            seen_order.add(o)
            label = {2: "change METHOD", 3: "reframe", 4: "AUTHOR a tool", 5: "re-prioritise", 6: "rethink self"}.get(o, "")
            print(f"  [tick {t:3d}] ladder climbed to ORDER {o} — {label}")
        if authored_op is None:
            ao = next((op for op in adapter.s.nodes("Operator")
                       if adapter.s.node(op)["attrs"].get("authored_by_escalation") == 1.0), None)
            if ao is not None:
                authored_op = ao
                at = adapter.s.node(ao)["attrs"]
                print(f"  [tick {t:3d}] >>> AUTHORED its own survival faculty: '{at.get('name')}' "
                      f"(runner={at.get('runner')!r}) — approach={str(at.get('approach',''))[:70]!r}")
        if adapter.s.node(ax)["attrs"].get("saturation", 0.0) >= 0.95:
            print(f"  [tick {t:3d}] survive axis SATURATED (saturation="
                  f"{adapter.s.node(ax)['attrs'].get('saturation')}) — the authored method survives. RESOLVED.")
            break

    print(f"\n{SEP}")
    sat = adapter.s.node(ax)["attrs"].get("saturation", 0.0)
    authored = [adapter.s.node(o)["attrs"] for o in adapter.s.nodes("Operator")
                if adapter.s.node(o)["attrs"].get("authored_by_escalation") == 1.0]
    b, r = survivals.get("blind"), survivals.get("rollout")
    ok = sat >= 0.95 and len(authored) >= 1 and b is not None and r is not None and r > b
    print(f"  blind baseline survival = {b}; AUTHORED rollout survival = {r}")
    print(f"  faculties the agent authored by escalation: {len(authored)}; final survive saturation = {sat}")
    print(f"  {'PASS' if ok else 'FAIL'} — in a world where the boundary is fatal, the agent recognised its blind "
          f"method dies, CLIMBED its own ladder, AUTHORED a boundary-rollout, and that method survives. It "
          f"debugged itself — in a world that is not speech.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
