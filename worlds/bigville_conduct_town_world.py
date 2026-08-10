"""BigvilleConductTownWorld -- the TOWN IS A SUPERGRAPH, wired (block 282000-c).

Many residents, ONE shared substrate. Each resident is a subgraph (a ConductState
hub + its EmotionParams + its held Bonds + its afforded directed options); the town
is the supergraph over them. Because the decision core (v1.1.0) scopes its Argmax
to `Neighbours(m,"in_scene")`, ALL residents' conduct collapses settle in ONE
`run_rules()` pass, each at its own reference frame -- the supergraph settling.

The adapter is mechanical: it maps town state (who is co-present, who holds what
Bond) into each resident's afforded DIRECTED options (help/harm/transfer toward
each co-present other) + the null `rest`, runs provision + the supergraph
valuation + every resident's scoped collapse, then reads each resident's chosen
action + target and ENACTS it (help raises / harm lowers the target's health). No
agent decision here -- provision, valuation, and choice are seed RULES.
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
_HEALTH_DELTA = {"harm": -25.0, "help": 15.0, "transfer": 0.0, "rest": 0.0}


class BigvilleConductTownWorld:
    """A town of residents deciding conduct on one supergraph substrate.

    residents: list of dict(name, place, w_supergraph=1.0, conduct_k=0.5).
    bonds:     dict[(a, b)] -> dict(affection=, resentment=, altruism_bias=) --
               a's held directed Bond toward b (missing pair = neutral).
    """

    def __init__(self, residents, bonds=None):
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        for seed in ("world_affordances", "bigville_supergraph_conduct",
                     "bigville_decision_core"):
            self.inner.load_seed_manifest(manifest_for(seed), self.eye._agent)
        self.residents = [r["name"] for r in residents]
        self.place = {r["name"]: r.get("place", "square") for r in residents}
        self._cfg = {r["name"]: r for r in residents}
        self.bonds = bonds or {}
        self.events = []
        self._hub = {}          # name -> ConductState node
        self._person = {}       # name -> Person body node
        self._opts = {}         # name -> list[(index, name, target, decaction node)]
        self._build()
        self._mint_scenes()

    # ------------------------------------------------------------------ ingest
    def _build(self):
        s, AE = self.s, self.inner.add_edge_unchecked
        for nm in self.residents:
            cfg = self._cfg[nm]
            m = s.add_node("ConductState", {
                "name": nm, "energy": 50.0, "health": 100.0, "committed_action": "",
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

    def _co_present(self, nm):
        return [o for o in self.residents
                if o != nm and self.place[o] == self.place[nm]]

    def _mint_scenes(self):
        """Mint each resident's afforded options once: rest + directed options
        toward each co-present other (sees edge -> provision; aims_at -> the Bond
        coupling + enactment). Also mint each hub's identity order-0 net."""
        s, AE = self.s, self.inner.add_edge_unchecked
        for nm in self.residents:
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
                opts.append((ix, name, target, d))
                ix += 1

            mint("rest", 0.15, 0.20)
            for o in self._co_present(nm):
                AE(m, "sees", self._person[o])          # provision reads this
                for name, bw in _DIRECTED.items():
                    mint(name, bw, _DIR_PLAN[name], target=o)
            self._opts[nm] = opts
            # identity order-0 net over this resident's scene
            n = ix
            asm = s.add_node("NetworkAssemblage", {"input_dim": n, "output_dim": n})
            sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
            AE(asm, "has_step", sid)
            ident = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
            for role, dat in {"W1": ident, "b1": [0.0] * n,
                              "W2": ident, "b2": [0.0] * n}.items():
                AE(sid, "has_weight", s.add_node("WeightTensor",
                                                 {"role": role, "data": dat}))
            rn = s.add_node("ReflexNet", {"name": "order0", "status": "idle",
                                          "enabled": 1.0, "eta": 0.5})
            AE(rn, "net_assemblage", asm)
            AE(m, "has_net", rn)
            s.set_attr(m, "input_vec", [0.0] * n)
            s.set_attr(m, "target_vec", [0.0] * n)

    # -------------------------------------------------------------------- tick
    def decide_town(self):
        """Settle the WHOLE town's conduct in one pass. (1) provision + supergraph
        valuation; (2) load each hub's provisioned impulses into its net input_vec;
        (3) ONE scoped collapse settles every resident; (4) enact + record."""
        self.inner.run_rules()                          # provision + plan_value
        for nm in self.residents:
            m = self._hub[nm]
            vec = [0.0] * len(self._opts[nm])
            for ix, _n, _t, d in self._opts[nm]:
                vec[ix] = float(self.s.node(d)["attrs"].get("impulse", 0.0))
            self.s.set_attr(m, "input_vec", vec)
            for f in ("collapse_armed", "settle_check_armed", "writeback_armed",
                      "done", "deepened"):
                self.s.set_attr(m, f, 0.0)
            self.s.set_attr(m, "collapse_armed", 1.0)
        self.inner.run_rules()                          # every scoped collapse
        out = []
        for nm in self.residents:
            m = self._hub[nm]
            code = int(round(float(self.s.node(m)["attrs"].get("chosen_code", -1.0))))
            name, target = None, None
            for ix, n_, t_, _d in self._opts[nm]:
                if ix == code:
                    name, target = n_, t_
            deep = int(round(float(self.s.node(m)["attrs"].get("deepened", 0.0))))
            if name in _HEALTH_DELTA and target is not None and _HEALTH_DELTA[name]:
                b = self._person[target]
                h = float(self.s.node(b)["attrs"]["health"])
                self.s.set_attr(b, "health", h + _HEALTH_DELTA[name])
                self.s.set_attr(b, "harmed" if name == "harm" else "helped", 1.0)
            rec = {"actor": nm, "act": name, "target": target,
                   "deepened": deep, "place": self.place[nm]}
            self.events.append(rec)
            out.append(rec)
        return out

    # -------------------------------------------------------------------- read
    def health(self, nm):
        return float(self.s.node(self._person[nm])["attrs"]["health"])

    def harm_events(self):
        return [e for e in self.events if e["act"] == "harm"]

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
