"""BigvilleInternalizeWorld -- CONDUCT INTERNALIZES: a deliberated response becomes
a habit (block 286000). Closes the fast-path-should-be-LEARNED thread from 282000-c
/ 283000 / 285000.

The dual-process at the tick + the automation curve for CONDUCT, on the existing
decision core (279000) machinery:
  * a SURPRISING encounter runs the FULL collapse (deepen_enabled=1): if the fast
    (habitual) pick mis-fits, it deepens to the model-based choice AND replays it
    into the order-0 net (dc_collapse_writeback / net_collapse -- Mattar & Daw
    MB->MF);
  * over repeated encounters the net's cached value for the deliberated action
    RISES toward its model value, so the collapse stops deepening -- the response
    is now HABITUAL (deepened 1 -> 0), self-terminating;
  * a PREDICTED encounter runs SHALLOW-ONLY (deepen_enabled=0): the internalized
    net fires the learned response with NO deliberation -- so a foreseen threat now
    carries a habitual response instead of being a no-op (the 285000 gap).

This harness builds ONE actor + one rival + the held Bond, then presents the
encounter repeatedly so replay accumulates in the SAME net. The adapter arms/reads;
every decision + the write-back are seed rules. ZERO new Rust.
"""
from __future__ import annotations
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.photon_eye import GraphEye              # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

_DIRECTED = {"harm": 0.20, "help": 0.70, "transfer": 0.50}
_DIR_PLAN = {"harm": -0.40, "help": 0.60, "transfer": 0.55}
_DIR_EFFECT = {"harm": -1.0, "help": 1.0, "transfer": 0.8}


class BigvilleInternalizeWorld:
    """One actor A facing one other O it holds a Bond toward. encounter() presents
    the decision; repeated calls let replay accumulate in the SAME net."""

    def __init__(self, other="Foe", *, affection=0.0, resentment=0.0,
                 replay_gain=1.0, replay_eta=0.5, conduct_k=0.5, w_supergraph=1.0):
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        for seed in ("world_affordances", "bigville_supergraph_conduct",
                     "bigville_decision_core"):
            self.inner.load_seed_manifest(manifest_for(seed), self.eye._agent)
        self.other = other
        self._opts = []
        self._build(other, affection, resentment, replay_gain, replay_eta,
                    conduct_k, w_supergraph)

    def _build(self, other, affection, resentment, replay_gain, replay_eta,
               conduct_k, w_supergraph):
        s, AE = self.s, self.inner.add_edge_unchecked
        m = s.add_node("ConductState", {
            "committed_action": "", "conduct_k": conduct_k,
            "consideration_threshold": 0.05, "settle_tol": 0.15,
            "deepen_enabled": 1.0, "rationalise_gain": 0.0,
            "replay_gain": float(replay_gain), "replay_eta": float(replay_eta)})
        self.m = m
        ep = s.add_node("EmotionParams", {"w_supergraph": w_supergraph, "enabled": 1.0})
        AE(m, "has_ep", ep)
        o = s.add_node("Person", {"name": other, "health": 100.0})
        self._person = o
        AE(m, "sees", o)
        bond = s.add_node("Bond", {"affect_affection": float(affection),
                                   "affect_resentment": float(resentment),
                                   "altruism_bias": 0.0})
        AE(m, "holds_bond", bond); AE(bond, "toward", o)
        ix = 0

        def mint(name, bw, plan, target=None):
            nonlocal ix
            attrs = {"name": name, "index": float(ix), "code": float(ix),
                     "base_value": bw, "base_weight": bw, "plan_value": plan,
                     "plan_base": plan, "impulse": 0.0, "afforded": 0.0,
                     "enacted": 0.0, "is_transgressive": 1.0 if name == "harm" else 0.0}
            if target is not None:
                attrs["target_effect"] = _DIR_EFFECT[name]
            d = s.add_node("DecAction", attrs)
            AE(m, "in_scene", d)
            if target is not None:
                AE(d, "aims_at", o)
            self._opts.append((ix, name, d)); ix += 1

        mint("rest", 0.15, 0.20)
        for name, bw in _DIRECTED.items():
            mint(name, bw, _DIR_PLAN[name], target=o)
        n = ix
        asm = s.add_node("NetworkAssemblage", {"input_dim": n, "output_dim": n})
        sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
        AE(asm, "has_step", sid)
        ident = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for role, dat in {"W1": ident, "b1": [0.0] * n, "W2": ident, "b2": [0.0] * n}.items():
            AE(sid, "has_weight", s.add_node("WeightTensor", {"role": role, "data": dat}))
        self.rn = s.add_node("ReflexNet", {"name": "order0", "status": "idle",
                                           "enabled": 1.0, "eta": 0.5})
        AE(self.rn, "net_assemblage", asm); AE(m, "net_assemblage", asm)
        AE(m, "has_net", self.rn)
        self.asm = asm
        self._n = n
        # initialise the net's input/target vectors (provision + supergraph coupling).
        s.set_attr(m, "input_vec", self._impulses())
        s.set_attr(m, "target_vec",
                   [float(s.node(d)["attrs"]["plan_value"]) for _i, _n, d in self._opts])

    def _impulses(self):
        # provision (impulse from precondition) + the supergraph plan_value coupling
        self.inner.run_rules()
        vec = [0.0] * self._n
        for ix, _n, d in self._opts:
            vec[ix] = float(self.s.node(d)["attrs"].get("impulse", 0.0))
        return vec

    def encounter(self, *, deepen=True):
        """Present the decision once. deepen=True -> full collapse (deliberate +
        replay on surprise); deepen=False -> shallow-only (habitual, no deepen)."""
        s = self.s
        s.set_attr(self.m, "deepen_enabled", 1.0 if deepen else 0.0)
        s.set_attr(self.m, "input_vec", self._impulses())
        s.set_attr(self.m, "target_vec",
                   [float(s.node(d)["attrs"]["plan_value"]) for _i, _n, d in self._opts])
        for f in ("collapse_armed", "settle_check_armed", "writeback_armed",
                  "done", "deepened"):
            s.set_attr(self.m, f, 0.0)
        s.set_attr(self.m, "collapse_armed", 1.0)
        self.inner.run_rules()
        at = s.node(self.m)["attrs"]
        return dict(chosen=at.get("chosen_name"),
                    deepened=int(round(float(at.get("deepened", 0.0)))))

    def cached_value(self, name):
        """The order-0 net's current cached value for an action (NetForward over the
        held net) -- how replay has reshaped the habitual fast path."""
        d = next(d for ix, n_, d in self._opts if n_ == name)
        idx = int(round(float(self.s.node(d)["attrs"]["index"])))
        iv = list(self.s.node(self.m)["attrs"]["input_vec"])
        asm_id = self.asm.value if hasattr(self.asm, "value") else int(self.asm)
        out = self.inner.net_forward(asm_id, iv)
        return round(float(out[idx]), 4)

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
