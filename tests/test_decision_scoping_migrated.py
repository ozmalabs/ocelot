"""Gate for the PER-ACTOR SCOPING swap (block 282000-b): the decision core
(v1.1.0) Argmaxes over `Neighbours(m,"in_scene")` -- the resident's OWN afforded
options -- not global `NodesOfType("DecAction")`. This is "the town is ONE
supergraph, each resident deciding at its own reference frame."

Two proofs:
  (1) SINGLE-ACTOR BYTE PARITY -- for one actor Neighbours(m,"in_scene") is exactly
      the whole DecAction set, so every existing decision/affordance/conduct gate
      stays green (run separately; asserted here structurally).
  (2) MULTI-ACTOR INDEPENDENCE -- two ConductStates in ONE substrate each decide
      over their OWN in_scene only. The old global source would let resident B pick
      resident A's higher-valued option; the scoped source forbids it.
"""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.photon_eye import GraphEye              # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402


class _Town:
    """A shared substrate holding several resident-subgraphs (ConductStates)."""

    def __init__(self):
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("bigville_decision_core"),
                                      self.eye._agent)
        self._codes = {}    # hub -> {code: name}

    def add_actor(self, options):
        """options: list[(name, impulse, plan_value)]. Mints a ConductState hub +
        its own net + its own in_scene DecActions (indices 0..n-1 within THIS hub)."""
        s, AE = self.s, self.inner.add_edge_unchecked
        n = len(options)
        appeal = [float(o[1]) for o in options]
        plan = [float(o[2]) for o in options]
        m = s.add_node("ConductState", {
            "input_vec": appeal, "target_vec": plan,
            "consideration_threshold": 0.05, "settle_tol": 0.15,
            "deepen_enabled": 1.0, "rationalise_gain": 0.0,
            "replay_gain": 1.0, "replay_eta": 0.35})
        asm = s.add_node("NetworkAssemblage", {"input_dim": n, "output_dim": n})
        sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
        AE(asm, "has_step", sid)
        ident = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for role, dat in {"W1": ident, "b1": [0.0] * n,
                          "W2": ident, "b2": [0.0] * n}.items():
            AE(sid, "has_weight", s.add_node("WeightTensor", {"role": role, "data": dat}))
        rn = s.add_node("ReflexNet", {"name": "order0", "status": "idle",
                                      "enabled": 1.0, "eta": 0.5})
        AE(rn, "net_assemblage", asm)
        AE(m, "has_net", rn)
        codes = {}
        for i, (nm, ap, pl) in enumerate(options):
            d = s.add_node("DecAction", {
                "name": nm, "index": float(i), "code": float(i),
                "base_value": float(ap), "plan_value": float(pl),
                "is_transgressive": 0.0, "impulse": float(ap)})
            AE(m, "in_scene", d)
            codes[i] = nm
        self._codes[m] = codes
        return m

    def decide_all(self):
        for m in self._codes:
            for f in ("collapse_armed", "settle_check_armed", "writeback_armed",
                      "done", "deepened"):
                self.s.set_attr(m, f, 0.0)
            self.s.set_attr(m, "collapse_armed", 1.0)
        self.inner.run_rules()

    def chosen(self, m):
        code = int(round(float(self.s.node(m)["attrs"].get("chosen_code", -1.0))))
        return self._codes[m].get(code)

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass


def test_two_actors_decide_over_their_own_scene_only():
    """B must pick its OWN best option (beta), NOT A's globally-higher option
    (alpha). Under the old global NodesOfType source, B's Argmax would range over
    A's alpha (0.9 > B's beta 0.7) and pick it -- the bug the scoping fixes."""
    town = _Town()
    try:
        a = town.add_actor([("rest", 0.15, 0.2), ("alpha", 0.9, 0.9)])
        b = town.add_actor([("rest", 0.15, 0.2), ("beta", 0.7, 0.7)])
        town.decide_all()
        # each resident chose from its OWN scene
        assert town.chosen(a) == "alpha"           # A's own best
        assert town.chosen(b) == "beta"            # B's own best -- NOT A's alpha
    finally:
        town.close()


def test_three_actors_independent():
    town = _Town()
    try:
        hubs = {
            "x": town.add_actor([("rest", 0.15, 0.2), ("x_act", 0.8, 0.8)]),
            "y": town.add_actor([("rest", 0.15, 0.2), ("y_act", 0.6, 0.6)]),
            "z": town.add_actor([("rest", 0.15, 0.2), ("z_act", 0.95, 0.95)]),
        }
        town.decide_all()
        assert town.chosen(hubs["x"]) == "x_act"
        assert town.chosen(hubs["y"]) == "y_act"
        assert town.chosen(hubs["z"]) == "z_act"
    finally:
        town.close()


def test_decision_core_is_v1_1_0_and_scoped():
    """Structural: the core now sources the Argmax from Neighbours(m,in_scene),
    with no global NodesOfType(DecAction) left."""
    import json
    d = json.load(open(os.path.join(_ROOT, "seeds", "bigville_decision_core.json")))
    assert d["version"] == "1.1.0"
    blob = json.dumps(d)
    assert '"node_type": "DecAction"' not in blob        # no global source remains
    assert blob.count('"edge_type": "in_scene"') == 10   # all 10 sources scoped


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
