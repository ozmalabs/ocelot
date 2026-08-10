"""ComprehensionWorld — a thin world adapter for the autonomous comprehension-gap investigation.

The understand Drive picks a gap CapabilityAxis; the loop binds it to its Operator; this world's
execute() ENACTS that operator — it grounds the gap's concepts through the on-disk teachers and
measures how much of the gap it now covers. No decision about WHAT to investigate lives here (that is
the graph's frontier pick); execute switches only on the literal operator/runner string and returns a
MeasuredCapability the bank rule reads. The agent reads about each gap and we watch what it can ground.
"""
from __future__ import annotations
import re


def _slug(s):
    return "taught_" + re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


class ComprehensionWorld:
    def __init__(self, adapter):
        self.a = adapter
        self.s = adapter.s

    def register_affordances(self):
        # the seed already provides the Microtheory + Operators + Axes; nothing to mint.
        pass

    def _concepts_for(self, runner):
        """Read the concept list off the Operator whose runner matches (the agent's own seed data)."""
        for o in self.s.nodes("Operator"):
            at = self.s.node(o)["attrs"]
            if at.get("runner") == runner:
                return list(at.get("concepts") or [])
        return []

    def execute(self, req):
        """Ground the gap's concepts via the teachers; coverage = fraction that got a real definition."""
        runner = req.get("operator", "")
        concepts = self._concepts_for(runner)
        if not concepts:
            return self.s.add_node("MeasuredCapability", {
                "measured": 0.0, "target": float(req.get("target", 0.6) or 0.6),
                "metric": req.get("measurement_key", "coverage"),
                "note": f"no concepts for runner {runner!r}"})
        grounded, learned, held = 0, [], []
        for c in concepts:
            try:
                self.a.ground_unknowns(c)             # read it via the on-disk teacher chain
            except Exception:
                pass
            defn = (self.a._taught_lookup.get(_slug(c)) or "") if hasattr(self.a, "_taught_lookup") else ""
            if defn:
                grounded += 1; learned.append(c)
            else:
                held.append(c)
        coverage = grounded / len(concepts)
        note = (f"grounded {grounded}/{len(concepts)} [{', '.join(learned)}]"
                + (f"; HELD (no teacher def): {', '.join(held)}" if held else ""))
        return self.s.add_node("MeasuredCapability", {
            "measured": round(coverage, 3), "target": float(req.get("target", 0.6) or 0.6),
            "metric": req.get("measurement_key", "coverage"), "synth_pending": 1, "note": note})
