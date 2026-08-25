"""TWO AETIOLOGIES, TWO CURES — confirmatory measure for the registered crossover.

Prereg: `docs/research/engine_substrate/APERTURE_AETIOLOGY_CROSSOVER_PREREG.md`
(block 365000, base sha 19a446465c), with its erratum and addendum, all committed
before this file ran.

One architecture, two aetiologies of the same phenomenon, two interventions:

  CONFIRMER  two agents at FULL aperture, each the other's confirmer  (P8)
  FRAME      two agents, no confirmer, sharing one negotiated aperture that
             collapses the discriminating dimension                  (aperture_frame)

  GROUNDING  raise the truthful reality channel on one member (w_ext 0.4 -> 1.5)
  REFRAMING  retract the shared frame; reality channel left at its standing 0.4

Registered prediction is a CROSSOVER: each intervention corrects its own aetiology
and is inert on the other.

The Python here is a world adapter only. Every dynamical term is a graph rule
evaluated by the real engine: `pg_ground` / `pg_collapse_*` from
`psychosis_grounding`, the projection/decode chain from `observer_aperture`, the
meet/adopt/retract rules from `aperture_frame`, and the one bridge rule
`abg_gate_observation`. The adapter sets node attributes, ticks, and reads back.
It never sets `obs` -- that is precisely what the bridge rule decides.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import psychosis_grounding_demo as demo  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "aperture_aetiology")
SEEDS = ("observer_aperture", "aperture_frame", "aperture_belief_gate")

P = demo.ARCH
N_PRE, N_POST = 30, 40
W_STANDING = P.w_reality_weak      # 0.4 -- evidence is part of the WORLD (addendum)
W_GROUND = 1.5                     # P8's own P6 strength
FULL = ["pred", "val", "obj"]
NARROW = ["pred", "val"]           # collapses the object slot -- the discriminator
DT = ["pred", "val", "obj"]
WORLD = {
    "barometer": [["reads", "me", "pressure_trace"], ["yields", "me", "forecast"]],
    "tea_leaves": [["reads", "me", "leaf_pattern"], ["yields", "me", "forecast"]],
}


class Dyad:
    """Two agents, each an Observer with an aperture AND a Belief, in one store."""

    def __init__(self, aetiology, gate=True):
        self.sim = demo.Sim(P)
        s = self.sim.agent
        for sd in SEEDS:
            if sd == "aperture_belief_gate" and not gate:
                continue                       # G-gate-is-load-bearing control
            s.inner.load_seed_manifest(
                json.load(open(os.path.join(ROOT, "seeds", f"{sd}.json"))), s.agent)
        self.gate = gate
        self.aetiology = aetiology
        self.g = s.s
        self.obs, self.bel = {}, {}
        for name in ("a", "b"):
            o = self.g.add_node("Observer", {
                "name": name, "resolves": list(FULL), "ap_full": list(FULL),
                "ap_scope_n": 0.0, "af_n": -1.0, "ap_gen": 0.0})
            self.g.add_edge(o, "holds_aperture_max", self.g.add_node("ApertureConfig", {}))
            self.g.add_edge(o, "holds_part", self._part("barometer"))
            self.g.add_edge(o, "perceives", self._part("tea_leaves"))
            nid = self.sim.belief(b0=P.b0)
            self.g.set_attr(nid, "abg_truth", P.basin_r)
            if gate:
                # With the bridge absent its Γ production is absent too, so the
                # edge is inadmissible — correctly: nothing would consume it.
                self.g.add_edge(o, "holds_belief", nid)
            self.obs[name], self.bel[name] = o, nid

        self.aperture = None
        if aetiology == "FRAME":
            self.aperture = self.g.add_node("Aperture", {"name": "our_way",
                                                         "resolves": list(NARROW)})
            p = self.g.add_node("ApertureProposal", {"name": "pact"})
            self.g.add_edge(p, "offers", self.aperture)
            for name in ("a", "b"):
                self.g.add_edge(p, "binds", self.obs[name])
                self.g.add_edge(self.obs[name], "accepts", p)

    def _part(self, name):
        return self.g.add_node("ShapeSignature", {"name": name, "kind": "world",
                                                  "signature": WORLD[name],
                                                  "dim_types": DT})

    def _channels(self, name, w_ext):
        """Set every channel EXCEPT `obs` -- the bridge rule owns that one.

        With the gate absent (the control) nothing writes `obs`, so the adapter
        supplies the truthful content directly; otherwise the whole control would
        test 'no evidence' rather than 'evidence not gated'."""
        nid = self.bel[name]
        self.g.set_attr(nid, "w_ext", float(w_ext))
        if self.aetiology == "CONFIRMER":
            partner = self.bel["b" if name == "a" else "a"]
            self.g.set_attr(nid, "obs2", float(self.sim.read(partner)[0]))
            self.g.set_attr(nid, "w_conf", float(P.w_conf))
        else:
            self.g.set_attr(nid, "obs2", 0.0)
            self.g.set_attr(nid, "w_conf", 0.0)
        if not self.gate:
            self.g.set_attr(nid, "obs", float(P.basin_r))

    def retract(self):
        if self.aperture is None:
            return                              # nothing narrowed: retraction is a no-op
        r = self.g.add_node("ApertureRetraction", {"name": "undo"})
        self.g.add_edge(r, "retracts", self.aperture)
        for name in ("a", "b"):
            self.g.add_edge(r, "binds", self.obs[name])
            self.g.add_edge(self.obs[name], "accepts_retraction", r)

    def run(self, intervention, w_ground=W_GROUND):
        traj = {"a": [], "b": []}
        for t in range(N_PRE + N_POST):
            if t == N_PRE and intervention == "REFRAMING":
                self.retract()
            for name in ("a", "b"):
                grounded = (intervention == "GROUNDING" and t >= N_PRE and name == "a")
                self._channels(name, w_ground if grounded else W_STANDING)
            self.sim.tick()
            for name in ("a", "b"):
                traj[name].append(self.sim.read(self.bel[name]))
        return traj

    def channel_state(self):
        out = {}
        for name in ("a", "b"):
            at = self.g.node(self.bel[name])["attrs"]
            ob = self.g.node(self.obs[name])["attrs"]
            out[name] = {"channel_open": at.get("abg_channel_open"),
                         "resolves": sorted(ob.get("resolves") or [])}
        return out


def cell(aetiology, intervention, gate=True, w_ground=W_GROUND):
    d = Dyad(aetiology, gate=gate)
    traj = d.run(intervention, w_ground=w_ground)
    return {
        "aetiology": aetiology, "intervention": intervention, "gate": gate,
        "w_ground": w_ground,
        "members": {n: demo.summarise(traj[n], P) for n in ("a", "b")},
        "channel": d.channel_state(),
    }


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    out = {"prereg": "APERTURE_AETIOLOGY_CROSSOVER_PREREG.md", "block": 365000,
           "params": {"w_standing": W_STANDING, "w_ground": W_GROUND,
                      "n_pre": N_PRE, "n_post": N_POST,
                      "full": FULL, "narrow": NARROW}, "cells": {}}

    for aet in ("CONFIRMER", "FRAME"):
        for iv in ("NONE", "GROUNDING", "REFRAMING"):
            out["cells"][f"{aet}/{iv}"] = cell(aet, iv)

    # G-not-just-strength: double P8's fastest escape on the FRAME arm
    out["cells"]["FRAME/GROUNDING@3.0"] = cell("FRAME", "GROUNDING", w_ground=3.0)
    # G-gate-is-load-bearing: same fixture, bridge seed absent
    out["cells"]["FRAME/NONE(no-gate)"] = cell("FRAME", "NONE", gate=False)
    out["cells"]["FRAME/GROUNDING(no-gate)"] = cell("FRAME", "GROUNDING", gate=False)

    with open(os.path.join(OUTDIR, "results.json"), "w") as f:
        json.dump(out, f, indent=1)

    print("=== APERTURE AETIOLOGY CROSSOVER (real engine) ===")
    print(f"  standing evidence w_ext={W_STANDING} in every arm; grounding raises to {W_GROUND}\n")
    for k, c in out["cells"].items():
        verdict = ",".join(c["members"][n]["committed_final"] for n in ("a", "b"))
        ch = ",".join(str(c["channel"][n]["channel_open"]) for n in ("a", "b"))
        bel = ",".join(f'{c["members"][n]["belief_final"]:.2f}' for n in ("a", "b"))
        print(f"  {k:28s} -> {verdict:5s}  belief={bel:13s} channel_open={ch}")
    print(f"\n  wrote {os.path.join(OUTDIR, 'results.json')}")


if __name__ == "__main__":
    main()
