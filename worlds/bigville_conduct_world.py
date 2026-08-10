"""BigvilleConductWorld -- DIRECTED, BOND-COUPLED CONDUCT (block 281000).

Wires the affordance vocabulary (280000) + the decision core (279000) + the held
Bond (277000) into one loop: a resident, seeing others it has RELATIONSHIPS with,
collapses over the afforded actions, and WHOM it acts on reads the held Bond. The
adapter is mechanical:
  * mint the actor hub (ConductState) + its held Bonds toward each co-present
    agent (the relationship representation -- affect_affection / affect_resentment
    read straight from the Bond node);
  * mint the afforded options: non-directed (rest/ingest/extract per the actor's
    own situation) + DIRECTED per co-present target (harm/help/transfer, each with
    an `aims_at` edge to its target and plan_base = the vocabulary's default);
  * run provision + the Bond->plan_value coupling (seed rules), attach the
    decision core net, run ONE collapse, and read back the chosen action AND its
    target (chosen_code -> DecAction -> aims_at).
NO agent decision here -- provision, the Bond coupling, and the choice are all
seed RULES; the adapter mints the scene and reads the result.
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

_DIRECTED = {"harm": 0.20, "help": 0.70, "transfer": 0.50}   # name -> base_weight
_DIR_PLAN = {"harm": -0.40, "help": 0.60, "transfer": 0.55}  # name -> plan_base
# how each directed act changes the TARGET's fulfilment (sign intrinsic to the
# action; magnitude adapter-published, per the supergraph valuation, 282000).
_DIR_EFFECT = {"harm": -1.0, "help": 1.0, "transfer": 0.8}   # name -> target_effect


class BigvilleConductWorld:
    """One resident's conduct as a Bond-coupled collapse over afforded actions.

    targets: list of dict(name, affection=0.0, resentment=0.0) -- the co-present
             agents and the actor's HELD Bond affect toward each.
    """

    def __init__(self, targets, *, has_food=False, at_source=False,
                 resent_gain=0.5, affection_gain=0.5, valuation="couple",
                 conduct_k=0.5, w_supergraph=1.0, **dc_knobs):
        # valuation="couple"     -> the 281000 three-rule Bond coupling (default).
        # valuation="supergraph" -> the 282000 ONE-rule supergraph sum.
        self.valuation = valuation
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        conduct_seed = ("bigville_supergraph_conduct" if valuation == "supergraph"
                        else "bigville_conduct")
        for seed in ("world_affordances", conduct_seed, "bigville_decision_core"):
            self.inner.load_seed_manifest(manifest_for(seed), self.eye._agent)
        self._by_code = {}       # index -> (name, target_name or None)
        self._targets = {}       # name -> Person node
        self._dc_knobs = dc_knobs
        self._build(targets, has_food, at_source, resent_gain, affection_gain,
                    float(conduct_k), float(w_supergraph))

    def _build(self, targets, has_food, at_source, resent_gain, affection_gain,
               conduct_k, w_supergraph):
        s, AE = self.s, self.inner.add_edge_unchecked
        m = s.add_node("ConductState", {
            "energy": 50.0, "health": 100.0, "committed_action": "",
            "conduct_resent_gain": float(resent_gain),
            "conduct_affection_gain": float(affection_gain),
            "conduct_k": conduct_k})
        self.m = m
        # the actor's EmotionParams -- the global psychopathy gate w_supergraph
        # (default 1.0; 0 = weights no one) the supergraph valuation multiplies by.
        ep = s.add_node("EmotionParams", {"w_supergraph": w_supergraph, "enabled": 1.0})
        AE(m, "has_ep", ep)
        self.ep = ep
        ix = 0

        def mint(name, base_weight, plan_base, target_node=None, target_name=None):
            nonlocal ix
            attrs = {
                "name": name, "index": float(ix), "code": float(ix),
                "base_value": float(base_weight), "base_weight": float(base_weight),
                "plan_value": float(plan_base), "plan_base": float(plan_base),
                "is_transgressive": 1.0 if name == "harm" else 0.0,
                "impulse": 0.0, "afforded": 0.0, "enacted": 0.0}
            if target_node is not None:
                attrs["target_effect"] = _DIR_EFFECT.get(name, 0.0)
            d = s.add_node("DecAction", attrs)
            AE(m, "in_scene", d)
            if target_node is not None:
                AE(d, "aims_at", target_node)
            self._by_code[ix] = (name, target_name)
            ix += 1
            return d

        # non-directed options (the actor's own situation)
        mint("rest", 0.15, 0.20)
        if has_food:
            g = s.add_node("Good", {"kind": "bread", "consumable": 1.0, "is_input": 0.0})
            AE(m, "holds", g)
            mint("ingest", 0.65, 0.70)
        if at_source:
            src = s.add_node("Source", {"kind": "fish", "stock": 5.0})
            AE(m, "at_source", src)
            mint("extract_resource", 0.55, 0.60)
        # co-present agents: a Bond per target + the directed options toward each.
        for t in targets:
            nm = t["name"]
            o = s.add_node("Person", {"name": nm, "health": 100.0,
                                      "harmed": 0.0, "helped": 0.0})
            AE(m, "sees", o)
            self._targets[nm] = o
            bond = s.add_node("Bond", {
                "affect_affection": float(t.get("affection", 0.0)),
                "affect_resentment": float(t.get("resentment", 0.0))})
            AE(m, "holds_bond", bond)
            AE(bond, "toward", o)
            for name, bw in _DIRECTED.items():
                mint(name, bw, _DIR_PLAN[name], target_node=o, target_name=nm)
        self._n = ix

    # ------------------------------------------------------------------- provide
    def provide(self):
        """Run provision (impulse from precondition) + the Bond->plan_value
        coupling. Both are seed rules in one fixpoint."""
        self.inner.run_rules()

    # ------------------------------------------------------ decision-core seam
    def _attach_decision_core(self):
        s, AE = self.s, self.inner.add_edge_unchecked
        by_ix = sorted((d for d in self.s.nodes("DecAction")),
                       key=lambda d: float(s.node(d)["attrs"]["index"]))
        n = len(by_ix)
        appeal = [float(s.node(d)["attrs"].get("impulse", 0.0)) for d in by_ix]
        plan = [float(s.node(d)["attrs"]["plan_value"]) for d in by_ix]
        asm = s.add_node("NetworkAssemblage", {"input_dim": n, "output_dim": n})
        sid = s.add_node("AssemblageStep", {"order": 0, "dim_behavior": "transform"})
        AE(asm, "has_step", sid)
        ident = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for role, dat in {"W1": ident, "b1": [0.0] * n,
                          "W2": ident, "b2": [0.0] * n}.items():
            AE(sid, "has_weight", s.add_node("WeightTensor",
                                             {"role": role, "data": dat}))
        rn = s.add_node("ReflexNet", {"name": "order0_conduct", "status": "idle",
                                      "enabled": 1.0, "eta": 0.5})
        AE(rn, "net_assemblage", asm)
        kn = dict(consideration_threshold=0.05, settle_tol=0.15,
                  deepen_enabled=1.0, rationalise_gain=0.0,
                  replay_gain=1.0, replay_eta=0.35)
        kn.update(self._dc_knobs)
        for k, v in kn.items():
            s.set_attr(self.m, k, float(v))
        s.set_attr(self.m, "input_vec", appeal)
        s.set_attr(self.m, "target_vec", plan)
        AE(self.m, "has_net", rn)

    def decide(self):
        """Run ONE collapse over the afforded (Bond-coupled) options; return the
        chosen action + WHOM it is directed at + whether it deepened."""
        self.provide()
        self._attach_decision_core()
        for f in ("collapse_armed", "settle_check_armed", "writeback_armed",
                  "done", "deepened", "s2_choice_name", "s2_choice_code"):
            self.s.set_attr(self.m, f, 0.0)
        self.s.set_attr(self.m, "collapse_armed", 1.0)
        self.inner.run_rules()
        at = self.s.node(self.m)["attrs"]
        code = int(round(float(at.get("chosen_code", -1.0))))
        name, target = self._by_code.get(code, (at.get("chosen_name"), None))
        return dict(chosen=name, target=target,
                    deepened=int(round(float(at.get("deepened", 0.0)))))

    # --------------------------------------------------------------------- read
    def plan_value(self, name, target_name):
        """Read the (Bond-coupled) plan_value of a directed option -- a graph read
        to witness the coupling."""
        want = {code for code, (nm, tgt) in self._by_code.items()
                if nm == name and tgt == target_name}
        for d in self.s.nodes("DecAction"):
            a = self.s.node(d)["attrs"]
            if int(round(float(a["code"]))) in want:
                return round(float(a["plan_value"]), 4)
        return None

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
