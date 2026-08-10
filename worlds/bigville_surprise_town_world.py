"""BigvilleSurpriseTownWorld -- the supergraph town on a SURPRISE clock, graph-native
(block 284000). Composes: surprise gate (284000) + supergraph conduct (282000) +
scoped decision core (279000 v1.1.0) + affordance vocabulary (280000).

Each resident holds a SocialPrediction (predicts_near edges) and a scene of
pre-minted directed options toward every other resident. Per tick the adapter mints
observation (sees edges from co-presence -- mechanical), then runs the graph:
  * sg_surprise (RULE) sets m.surprised iff a `sees` has no matching predicts_near;
    sg_absorb (RULE) folds the new other into the prediction; sg_provide_directed
    (RULE) lifts the impulse of options whose target is seen.
Only a SURPRISED resident then runs its conduct collapse (the gate m.surprised is a
rule output the adapter reads); an unsurprised resident is a NO-OP -- it continues.
The DECISION on surprise is the 282000 supergraph collapse, Bond-directed. The
adapter is a mechanical dispatcher on a rule-computed flag.
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
_HEALTH_DELTA = {"harm": -25.0, "help": 15.0, "transfer": 0.0}


class BigvilleSurpriseTownWorld:
    """residents: [dict(name, w_supergraph=1.0, conduct_k=0.5, predicts=[names])].
    bonds: {(a, b): dict(affection=, resentment=, altruism_bias=)}."""

    def __init__(self, residents, bonds=None, *, extra_seeds=(), fast_gain=0.0):
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        for seed in (("world_affordances", "bigville_surprise_gate",
                      "bigville_supergraph_conduct", "bigville_decision_core")
                     + tuple(extra_seeds)):
            self.inner.load_seed_manifest(manifest_for(seed), self.eye._agent)
        self.names = [r["name"] for r in residents]
        self._cfg = {r["name"]: r for r in residents}
        self.bonds = bonds or {}
        self._fast_gain = float(fast_gain)
        self._hub, self._person, self._opts, self._sees = {}, {}, {}, {}
        self.decided = []            # [(tick, resident, chosen, target)]
        self.tick_no = 0
        self._build(residents)

    def _build(self, residents):
        s, AE = self.s, self.inner.add_edge_unchecked
        for nm in self.names:
            cfg = self._cfg[nm]
            m = s.add_node("ConductState", {
                "name": nm, "committed_action": "", "surprised": 0.0,
                "fast_gain": self._fast_gain,
                "conduct_k": float(cfg.get("conduct_k", 0.5)),
                "consideration_threshold": 0.05, "settle_tol": 0.15,
                "deepen_enabled": 1.0, "rationalise_gain": 0.0,
                "replay_gain": 1.0, "replay_eta": 0.35})
            ep = s.add_node("EmotionParams",
                            {"w_supergraph": float(cfg.get("w_supergraph", 1.0)),
                             "enabled": 1.0})
            AE(m, "has_ep", ep)
            body = s.add_node("Person", {"name": nm, "health": 100.0,
                                         "harmed": 0.0, "helped": 0.0})
            self._hub[nm], self._person[nm] = m, body
        for (a, b), aff in self.bonds.items():
            bond = s.add_node("Bond", {
                "affect_affection": float(aff.get("affection", 0.0)),
                "affect_resentment": float(aff.get("resentment", 0.0)),
                "altruism_bias": float(aff.get("altruism_bias", 0.0))})
            AE(self._hub[a], "holds_bond", bond)
            AE(bond, "toward", self._person[b])
        # pre-mint each resident's scene: rest + directed options toward EVERY other.
        for nm in self.names:
            m = self._hub[nm]
            opts, ix = [], 0

            def mint(name, bw, plan, target=None):
                nonlocal ix
                attrs = {"name": name, "index": float(ix), "code": float(ix),
                         "base_value": bw, "base_weight": bw, "plan_value": plan,
                         "plan_base": plan, "impulse": 0.0, "afforded": 0.0,
                         "enacted": 0.0,
                         "is_transgressive": 1.0 if name == "harm" else 0.0}
                if target is not None:
                    attrs["target_effect"] = _DIR_EFFECT[name]
                d = s.add_node("DecAction", attrs)
                AE(m, "in_scene", d)
                if target is not None:
                    AE(d, "aims_at", self._person[target])
                opts.append((ix, name, target, d)); ix += 1

            mint("rest", 0.15, 0.20)
            for o in self.names:
                if o == nm:
                    continue
                for name, bw in _DIRECTED.items():
                    mint(name, bw, _DIR_PLAN[name], target=o)
            self._opts[nm] = opts
            n = ix
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
            s.set_attr(m, "input_vec", [0.0] * n)
            s.set_attr(m, "target_vec", [0.0] * n)
            # the held SocialPrediction: who this resident predicts nearby.
            for o in cfg_predicts(self._cfg[nm]):
                if o in self._person:
                    AE(m, "predicts_near", self._person[o])

    # -------------------------------------------------------------------- tick
    def tick(self, copresence):
        """copresence: {resident: [names co-present with it] }. Mints sees edges,
        runs the surprise gate + provision, and runs the conduct collapse ONLY for
        residents the surprise rule flagged. Returns per-resident outcomes."""
        self.tick_no += 1
        s, AE = self.s, self.inner.add_edge_unchecked
        # (1) observation: refresh sees edges (mechanical). Clear last-tick sees.
        for nm in self.names:
            m = self._hub[nm]
            for o in self.inner.neighbours(m, "sees"):
                self.inner.remove_edge_unchecked(m, "sees", o)
            self.s.set_attr(m, "surprised", 0.0)
        for nm, others in copresence.items():
            for o in others:
                AE(self._hub[nm], "sees", self._person[o])
        # (2) surprise gate + directed provision (rules).
        self.inner.run_rules()
        # (3) only SURPRISED residents decide (the gate is a rule output).
        out = []
        surprised = [nm for nm in self.names
                     if float(s.node(self._hub[nm])["attrs"].get("surprised", 0.0)) > 0.5]
        for nm in surprised:
            m = self._hub[nm]
            vec = [0.0] * len(self._opts[nm])
            for ix, _n, _t, d in self._opts[nm]:
                vec[ix] = float(s.node(d)["attrs"].get("impulse", 0.0))
            s.set_attr(m, "input_vec", vec)
            for f in ("collapse_armed", "settle_check_armed", "writeback_armed",
                      "done", "deepened"):
                s.set_attr(m, f, 0.0)
            s.set_attr(m, "collapse_armed", 1.0)
        self.inner.run_rules()
        for nm in self.names:
            m = self._hub[nm]
            if nm not in surprised:
                out.append({"resident": nm, "surprised": False, "chosen": None})
                continue
            code = int(round(float(s.node(m)["attrs"].get("chosen_code", -1.0))))
            name, target = None, None
            for ix, n_, t_, _d in self._opts[nm]:
                if ix == code:
                    name, target = n_, t_
            # enact a directed act on its target's vital state (mechanical).
            if name in _HEALTH_DELTA and target is not None and _HEALTH_DELTA[name]:
                b = self._person[target]
                h = float(s.node(b)["attrs"]["health"])
                s.set_attr(b, "health", h + _HEALTH_DELTA[name])
                s.set_attr(b, "harmed" if name == "harm" else "helped", 1.0)
            self.decided.append((self.tick_no, nm, name, target))
            out.append({"resident": nm, "surprised": True, "chosen": name, "target": target})
        return out

    def decision_count(self):
        return len(self.decided)

    def predicts(self, nm):
        return sorted(self.s.node(o)["attrs"]["name"]
                      for o in self.inner.neighbours(self._hub[nm], "predicts_near"))

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass


def cfg_predicts(cfg):
    return list(cfg.get("predicts", []))
