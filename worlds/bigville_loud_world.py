"""BigvilleLoudWorld -- bigville R19 (block 267000): utterance LOUDNESS and the
OBSERVE-vs-HEAR split on the proven bigville grid.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R19 + sec 2 loudness)
---------------------------------------------------------------------------------
Every utterance carries a LOUDNESS scalar that scales the EXISTING occlusion-gated
earshot query: an utterance at loudness L delivers its CONTENT only to hearers
within `radius(L)`, occlusion-adjusted. TWO channels off ONE act -- SIGHT (line of
sight to the speaker) delivers the COMMUNICATION ACT ("X communicating with Y" is
a VISIBLE event); HEARING (inside `radius(L)`) delivers the CONTENT. So a
whispered exchange in plain view is *observed-as-conversation* while its content
never enters a distant witness's graph.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
This is a WORLD ADAPTER. It edits no tracked file and holds NO agent decision:

  * Communication runs in an ISOLATED comm substrate (`substrate_rs.Substrate`)
    loading two SEED manifests (bigville_loud_comm / bigville_loud_class). EVERY
    decision is a RULE there:
      - `lo_choose_loudness` : eff_loudness = clamp(chosen,max) under choice,
                               base when choice ablated, FLAT when loudness ablated.
      - `lo_deliver_content` : CONTENT iff eff_loudness >= dist AND not occluded
                               (loudness IS the Chebyshev hearing radius).
      - `lo_observe_act`     : mint the CommAct for any witness with SIGHT to the
                               speaker (range + no occlusion), REGARDLESS of content.
      - `lo_chatter_distracts` / `lo_control_restores` : the classroom attention
                               proxy (a child's `attending` scalar).
    None of those lives in Python.
  * This adapter only does mechanical I/O: it computes the RAW GEOMETRY per
    (utterance, perceiver) pair -- Chebyshev distance + occlusion via the
    scaffold's occlusion gate (`_line` / `OCCLUDERS`, IMPORTED verbatim from
    bigville_sim_world) -- ingests it as node attrs, runs the rules, and reads
    state. No Python `if`/`else` over agent state decides who hears / who
    observes / how loud -- source-audit gate. Loudness parametrizes the existing
    earshot query; NO new Rust.

The classroom-chatter gate is a SCOPED loudness proxy: `attending` stands in for
the R17/R18 attention-gate; the true acquisition/learning coupling is DEFERRED
(needs R18) and is NOT claimed here.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.engine_provenance import engine_preamble            # noqa: E402
engine_preamble(strict=False)                                    # resolve THIS tree's engine

import substrate_rs                                              # noqa: E402
from substrate.seed_loader import manifest_for                   # noqa: E402
# REUSE the scaffold's occlusion-gated LOS geometry (mechanical perception gate).
from worlds.bigville_sim_world import (                          # noqa: E402
    build_town, _line, OCCLUDERS, SIGHT_RANGE,
)

# per-character loudness defaults (population variation via base/max seed axes)
PERSON_DEFAULTS = dict(base_loudness=6.0, max_loudness=12.0, peer_pull=0.0,
                       attending=1.0)


class BigvilleLoudWorld:
    def __init__(self, flat_radius=6.0):
        self.grid, _ = build_town()
        self.flat_radius = float(flat_radius)
        # ---- the ISOLATED comm substrate + its two seed manifests ------------
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_loud_comm"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_loud_class"), None)
        self.people = {}                 # name -> Person nid
        self.pos = {}                    # name -> (x, y)
        self._utter_count = 0

    # ------------------------------------------------------------------ ingest
    def add_person(self, name, pos, **axes):
        """Register a person at grid `pos` with per-character seed loudness axes
        (base_loudness / max_loudness) + optional peer_pull / attending."""
        attrs = dict(PERSON_DEFAULTS)
        attrs.update(axes)
        attrs["name"] = name
        p = self.eng.add_node("Person", attrs)
        self.people[name] = p
        self.pos[name] = tuple(pos)
        return p

    # -------------------------------------------- the occlusion-gated geometry
    def _occluded(self, a, b):
        """True iff the grid line a->b crosses an occluder BETWEEN the endpoints
        (the scaffold's rule; endpoints excluded). Mechanical geometry."""
        for (x, y) in _line(a[0], a[1], b[0], b[1])[1:-1]:
            if self.grid[y][x] in OCCLUDERS:
                return True
        return False

    @staticmethod
    def _cheb(a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    # ------------------------------------------------------------------ speak
    def speak(self, speaker, addressee, chosen_loudness=None, choice_on=1,
              loudness_on=1, is_control=0, hearers=None):
        """Mint an Utterance + a Reception per candidate hearer, run the earshot /
        observe-hear rules, and read back per-hearer (dist, occluded, got_content,
        observed_act) + the rule-chosen eff_loudness. Transient nodes are purged
        after read-off so a later speak() in the same substrate is not confused by
        stale receptions (persistent Person state -- e.g. `attending` -- stays)."""
        spk = self.people[speaker]
        sa = self.eng.node(spk)["attrs"]
        if chosen_loudness is None:
            chosen_loudness = sa["base_loudness"]
        self._utter_count += 1
        u = self.eng.add_node("Utterance", {
            "speaker": speaker, "addressee": addressee,
            "chosen_loudness": float(chosen_loudness), "choice_on": float(choice_on),
            "loudness_on": float(loudness_on), "is_control": float(is_control),
            "base_loudness": float(sa["base_loudness"]),
            "max_loudness": float(sa["max_loudness"]),
            "flat_radius": self.flat_radius, "eff_loudness": 0.0})
        self.eng.add_edge_unchecked(u, "spoken_by", spk)

        sp_pos = self.pos[speaker]
        targets = hearers if hearers is not None else [
            n for n in self.people if n != speaker]
        recs = {}
        for name in targets:
            ppos = self.pos[name]
            occ = 1.0 if self._occluded(sp_pos, ppos) else 0.0
            r = self.eng.add_node("Reception", {
                "dist": float(self._cheb(sp_pos, ppos)),
                "sight_occluded": occ, "hear_occluded": occ,
                "got_content": 0.0, "observed_act": 0.0,
                "speaker": speaker, "addressee": addressee, "perceiver": name})
            self.eng.add_edge_unchecked(u, "reception", r)
            self.eng.add_edge_unchecked(r, "to", self.people[name])
            recs[name] = r

        self.eng.run_rules(1000000)

        out = {}
        for name, r in recs.items():
            a = self.eng.node(r)["attrs"]
            out[name] = dict(
                dist=int(a["dist"]), occluded=int(a["sight_occluded"]),
                got_content=int(a["got_content"]),
                observed_act=int(a["observed_act"]))
        eff = float(self.eng.node(u)["attrs"]["eff_loudness"])
        self._purge(u, recs)
        return dict(eff_loudness=eff, radius=eff, receptions=out)

    def _purge(self, u, recs):
        """Remove the transient Utterance / Reception / CommAct nodes (mechanical
        cleanup) so persistent Person state is the only thing carried forward."""
        for r in recs.values():
            for ca in list(self.eng.neighbours(r, "act")):
                self.eng.remove_node(ca)
            self.eng.remove_node(r)
        self.eng.remove_node(u)

    # ------------------------------------------------- glass-box read-offs
    def attending_of(self, name):
        return float(self.eng.node(self.people[name])["attrs"].get("attending", 1.0))

    def person_axes(self, name):
        a = self.eng.node(self.people[name])["attrs"]
        return dict(base=float(a["base_loudness"]), max=float(a["max_loudness"]),
                    peer_pull=float(a.get("peer_pull", 0.0)),
                    attending=float(a.get("attending", 1.0)))

    def close(self):
        self.people.clear()
        self.pos.clear()
