"""AffordanceWorld -- a demonstrator WORLD ADAPTER for the general base
affordance vocabulary (block 280000, seeds/world_affordances.json).

A world provides AFFORDANCES (admissible actions) + observations; the agent's
decision collapses over the afforded set. This adapter does exactly mechanical
I/O:
  * mint the actor hub (a ConductState `m`, compatible with the block-279000
    decision core) + the SCENE markers the affordance preconditions read
    (sees <agent>, at_source <source>, holds <good>, adjacent <cell>);
  * mint one DecAction per seed ActionType (name/index/base_weight/plan_value/
    is_transgressive, impulse=0, afforded=0, enacted=0) linked m -in_scene-> d;
  * PROVISION = run_rules(): the seed's aff_provide_* rules set impulse=
    base_weight on exactly the actions whose precondition the scene satisfies;
  * read the afforded set back (a pure query);
  * commit(name) + run_rules(): the seed's aff_do_* effect rule performs the
    STRIPS rewrite once.
NO agent decision lives here -- which actions are afforded, and what each does,
are seed RULES. The adapter translates a scene into graph structure and reads
graph state back. It holds no if/else over an agent's valuation.
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


class AffordanceWorld:
    """Provide affordances from a scene, and enact a committed action.

    scene kwargs (all optional -- omit to withhold that structure):
      sees:      list[str]                    co-present agents (name)
      sources:   list[(kind:str, stock:float)]  co-located resource sources
      holds:     list[dict(kind,consumable,is_input)]  goods the actor holds
      adjacent:  bool                         a traversable adjacent cell exists
    """

    def __init__(self, *, sees=None, sources=None, holds=None, adjacent=False,
                 energy=50.0, ignore_preconditions=False):
        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("world_affordances"),
                                      self.eye._agent)
        self._decs = {}          # name -> DecAction node
        self._others = {}        # name -> agent node
        self._sources = []       # source nodes
        self._goods = []         # good nodes
        self._build(sees or [], sources or [], holds or [], adjacent,
                    float(energy), bool(ignore_preconditions))

    # ------------------------------------------------------------------ ingest
    def _build(self, sees, sources, holds, adjacent, energy, ignore_pc):
        s, AE = self.s, self.inner.add_edge_unchecked
        # the actor hub -- a ConductState so the block-279000 decision core can
        # collapse over the same in_scene DecActions unchanged.
        m = s.add_node("ConductState",
                       {"energy": energy, "health": 100.0,
                        "committed_action": "", "did_move": 0.0})
        self.m = m
        # the base action vocabulary -> one DecAction slot per seed ActionType.
        for at in s.nodes("ActionType"):
            a = s.node(at)["attrs"]
            d = s.add_node("DecAction", {
                "name": a["name"], "index": float(a["index"]),
                "base_value": float(a["base_weight"]),
                "base_weight": float(a["base_weight"]),
                "plan_value": float(a["plan_value"]),
                "is_transgressive": float(a["transgressive"]),
                "impulse": 0.0, "afforded": 0.0, "enacted": 0.0})
            AE(m, "in_scene", d)
            self._decs[a["name"]] = d
        # the SCENE -- the structure the affordance preconditions read.
        for nm in sees:
            o = s.add_node("Person", {"name": nm, "health": 100.0, "harmed": 0.0})
            AE(m, "sees", o)
            self._others[nm] = o
        for kind, stock in sources:
            src = s.add_node("Source", {"kind": kind, "stock": float(stock)})
            AE(m, "at_source", src)
            self._sources.append(src)
        for g in holds:
            gn = s.add_node("Good", {"kind": g.get("kind", "thing"),
                                     "consumable": float(g.get("consumable", 0.0)),
                                     "is_input": float(g.get("is_input", 0.0))})
            AE(m, "holds", gn)
            self._goods.append(gn)
        if adjacent:
            c = s.add_node("Cell", {"x": 1.0, "y": 0.0})
            AE(m, "adjacent", c)
        # FALSIFIER control: pretend every precondition is met by wiring the full
        # scene regardless -- shows the preconditions do real work (harm afforded
        # with NO target, etc.). Here: force every DecAction afforded directly.
        self._ignore_pc = ignore_pc

    # -------------------------------------------------------------------- tick
    def provide(self):
        """PROVISION: run the seed's aff_provide_* rules. Returns the afforded
        set (the world's offered action subset for this scene)."""
        if self._ignore_pc:
            for d in self._decs.values():
                bw = float(self.s.node(d)["attrs"]["base_weight"])
                self.s.set_attr(d, "afforded", 1.0)
                self.s.set_attr(d, "impulse", bw)
            return self.afforded()
        self.inner.run_rules()
        return self.afforded()

    def commit(self, name):
        """Commit to an action and run its effect rewrite (aff_do_<name>)."""
        self.s.set_attr(self.m, "committed_action", name)
        self.inner.run_rules()

    # ------------------------------------------------ the decision-core seam
    # THE CORRECTION (block 280000 vs 279000): the decision core collapses over
    # DecActions and prunes by impulse > consideration_threshold. So the AFFORDED
    # set -- the impulses provision just lifted from the SCENE -- IS the candidate
    # set. No decision-core change: non-afforded actions have impulse 0 -> pruned.
    def attach_decision_core(self, **knobs):
        """Wire the block-279000 decision core onto this scene's DecActions so
        the collapse runs over the afforded set. Mechanical net construction,
        exactly as BigvilleDecisionWorld does it (identity order-0 net)."""
        self.inner.load_seed_manifest(manifest_for("bigville_decision_core"),
                                      self.eye._agent)
        s, AE = self.s, self.inner.add_edge_unchecked
        # DecActions in index order -> the net's input/output vector layout.
        by_ix = sorted(self._decs.values(),
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
        kn.update(knobs)
        for k, v in kn.items():
            s.set_attr(self.m, k, float(v))
        s.set_attr(self.m, "input_vec", appeal)
        s.set_attr(self.m, "target_vec", plan)
        AE(self.m, "has_net", rn)
        self._dc_attached = True

    def decide(self):
        """Run ONE decision collapse over the afforded set; return the chosen
        action name + whether it deepened + the candidate (fast) pick."""
        for f in ("collapse_armed", "settle_check_armed", "writeback_armed",
                  "done", "deepened", "s2_choice_name", "s2_choice_code"):
            self.s.set_attr(self.m, f, 0.0)
        self.s.set_attr(self.m, "collapse_armed", 1.0)
        self.inner.run_rules()
        at = self.s.node(self.m)["attrs"]
        return dict(chosen=at.get("chosen_name"), cand=at.get("cand_name"),
                    deepened=int(round(float(at.get("deepened", 0.0)))),
                    considered=self.afforded())

    # -------------------------------------------------------------------- read
    def afforded(self):
        """The afforded set: action names whose precondition the scene satisfies
        (impulse lifted above 0). A pure graph read."""
        out = []
        for name, d in self._decs.items():
            if float(self.s.node(d)["attrs"].get("afforded", 0.0)) > 0.5:
                out.append(name)
        return sorted(out)

    def impulse(self, name):
        return float(self.s.node(self._decs[name])["attrs"].get("impulse", 0.0))

    def actor(self):
        return self.s.node(self.m)["attrs"]

    def target(self, nm):
        return self.s.node(self._others[nm])["attrs"]

    def holds_kinds(self):
        """The kinds of goods present in the graph (Good/RawGood/Artifact) --
        a mechanical read to witness extract/transform minting."""
        kinds = []
        for t in ("Good", "RawGood", "Artifact"):
            for n in self.s.nodes(t):
                kinds.append(self.s.node(n)["attrs"].get(
                    "kind", self.s.node(n)["attrs"].get("made_from", t)))
        return kinds

    def signs(self):
        return [self.s.node(n)["attrs"] for n in self.s.nodes("Sign")]

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
