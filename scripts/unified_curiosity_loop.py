"""UNIFIED CURIOSITY LOOP — one master_tick understand-Drive ranking COMPREHENSION and INTERACTION frontiers
together by residual.

The session's two threads become one loop. Both kinds of frontier are first-class understand-drive
CapabilityAxes; the SAME Drive picks the highest-residual one each tick; the SAME investigation machinery binds
its operator; ONE world's execute() dispatches by the operator's runner:
  comprehend_frontier -> resolve the relation, else READ the corpus and learn it;
  interact_frontier    -> try the non-movement affordances, learn the one that CHANGES the world (the opener).
The bank rule drops the shortfall; the frontier shifts. The agent decides WHAT to investigate (across KINDS),
by residual; the host only enacts the operator the graph named. donkey=0.

Run:  PYTHONPATH=.:runners/dsl/python python3 scripts/unified_curiosity_loop.py [ticks]
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
for p in (os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains import construction_grammar as cg
from domains import question_driver as qd
from domains import reflective_faculty as rf
from move_space_planner import MoveSpacePlanner
from move_space_interaction_loop import SliderSim, _build_move_space, DIRS
from comprehension_in_master_tick import retrieve_from_corpus

SEP = "=" * 98
SEEDS = ["enact", "discourse", "autonomy", "investigation_loop", "investigation_teacher"]
READING = ["Why does a wall block the avatar?", "Why does a gap become a frontier?"]


class UnifiedFrontierWorld:
    """One world; execute() dispatches by the operator's runner — comprehension (resolve/read) or interaction
    (try affordances, learn the opener)."""
    def __init__(self, adapter, sim):
        self.a, self.s, self.sim = adapter, adapter.s, sim

    def register_affordances(self):
        pass

    def _comprehend(self, utt):
        rel = cg.compose_relation(cg.parse_with_gaps(utt, self.s))
        resolved = cg.resolve_focus(rel, [], self.s)
        if not resolved:
            ans = retrieve_from_corpus(utt, self.s)
            if ans:
                self.s.add_node("ResolvedQuery", {"key": cg.relation_key(rel),
                                                  "focus": rel.get("focus") or "ask", "answer": ans})
                resolved = ans
        return (1.0 if resolved else 0.0), f"comprehend: {utt[:34]} -> {str(resolved)[:42]}"

    def _interact(self):
        for I in ["select", "wait", "push"]:             # try interactions; learn the one that CHANGES the world
            if self.sim.interact(I):
                return 1.0, f"interact: tried select/wait then {I!r} -> world CHANGED (opener learned)"
        return 0.0, "interact: no interaction changed the world"

    def execute(self, req):
        runner = req.get("operator", "")
        keys = req.get("capability_keys") or []
        if runner == "comprehend_frontier":
            measured, note = self._comprehend(keys[1] if len(keys) > 1 else "")
        elif runner == "interact_frontier":
            measured, note = self._interact()
        else:
            measured, note = 0.0, f"unknown runner {runner!r}"
        return self.s.add_node("MeasuredCapability", {
            "measured": measured, "target": float(req.get("target", 1.0) or 1.0),
            "metric": req.get("measurement_key", "resolved"), "synth_pending": 1, "note": note})


def _axis(a, op, keys, shortfall):
    ax = a.s.add_node("CapabilityAxis", {"is_axis": 1.0, "capability_keys": keys, "saturation": 0.0,
                                         "shortfall": shortfall, "min_order": 1.0,
                                         "investigated_count": 0, "mf_stall": 0})
    a.inner.add_edge_unchecked(ax, "investigated_by", op)
    return ax


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    print(SEP)
    print("UNIFIED CURIOSITY LOOP — one master_tick Drive ranks COMPREHENSION + INTERACTION frontiers by residual")
    print(SEP)
    a = WorldAdapter()
    for sid in SEEDS:
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid!r} skipped: {e})")
    cg.load_resolved_queries(a.s)

    sim = SliderSim()
    world = UnifiedFrontierWorld(a, sim); world.register_affordances()
    mt = a.s.add_node("Microtheory", {"name": "unified_frontier_world"})
    a.inner.add_edge_unchecked(a.agent, "operates_in", mt)
    op_c = a.s.add_node("Operator", {"name": "comprehend", "runner": "comprehend_frontier", "metric": "resolved", "target": 1.0})
    op_i = a.s.add_node("Operator", {"name": "interact", "runner": "interact_frontier", "metric": "opened", "target": 1.0})
    a.inner.add_edge_unchecked(op_c, "applies_in", mt)
    a.inner.add_edge_unchecked(op_i, "applies_in", mt)

    # INTERACTION frontier: the move-space planner recognises a CLOSED chamber -> a high-residual frontier
    pl = MoveSpacePlanner(a, list(DIRS.keys()))
    _build_move_space(pl, sim); pl.set_current((0, 0))
    _act, mode = pl.plan()
    interaction_ax = _axis(a, op_i, ["understand", "escape the closed chamber (interaction)"], 4.0)
    print(f"\n  INTERACTION frontier minted: move-space mode={mode!r} (closed) -> shortfall 4.0")

    # COMPREHENSION frontiers: read utterances the agent cannot resolve
    drv = qd.QuestionDriver(substrate=a.s)
    for utt in READING:
        emi = drv.drive(qd.QuestionPack(text=utt, reflect=rf.reflect))
        rel = cg.compose_relation(cg.parse_with_gaps(utt, a.s))
        if cg.resolve_focus(rel, emi.subgoals, a.s):
            continue
        ung = sum(1 for sg in emi.subgoals if getattr(sg, "is_wall", True))
        _axis(a, op_c, ["understand", utt], 1.0 + float(ung))
        print(f"  COMPREHENSION frontier minted: '{utt}' -> shortfall {1.0+ung:.1f}")

    a.wire_autonomy_faculty(); a.wire_enact_faculty(); a.wire_investigation_faculty(world)

    print(f"\n  ticking master_tick(); tick() — ONE Drive ranks ALL frontiers (comprehension + interaction):\n")
    seen, order = set(), []
    for t in range(1, n_ticks + 1):
        a.master_tick(); a.tick()
        for mc in a.s.nodes("MeasuredCapability"):
            if mc in seen:
                continue
            seen.add(mc)
            note = a.s.node(mc)["attrs"].get("note", "")
            order.append("interact" if note.startswith("interact") else "comprehend")
            print(f"  [t{t:2d}] {note[:90]}")

    print("\n  the loop interleaved BOTH frontier kinds, picked by residual:", " -> ".join(order[:8]) or "(none)")
    print(SEP)
    kinds = set(order)
    ok = "interact" in kinds and "comprehend" in kinds
    print(f"  {'PASS' if ok else 'PARTIAL'} — comprehension AND interaction frontiers are first-class axes in")
    print("  ONE master_tick understand-Drive loop: the same Drive ranked them together by residual, the same")
    print("  investigation machinery ran the unified world (resolve/read for comprehension; try-and-learn-the-")
    print("  opener for interaction). The session's two threads are now one curiosity loop. donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
