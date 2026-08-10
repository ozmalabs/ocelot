"""BigvilleWorldWorld -- bigville R11 (block 259000): THE OPEN WORLD. Bigville
becomes a WINDOW onto a bigger world (Giantville on the horizon) at the cost of
only what is in view, via SCOPE-GATING. Travellers pass through, stay at the inn,
trade across the boundary, bring news of the frontier, and recruit residents whose
escape DREAM (R8) collapses into leaving.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2.7 + sec 3 R11)
--------------------------------------------------------------------------
  * SCOPE-GATING (HEADLINE) -- an IN-SCOPE agent carries the activity wiring
    (`active_beat`/`active_clock`) and is matched by `bw_run_in_scope` (it RUNS
    each tick); an OUT-OF-SCOPE agent is a bare PERSISTED node with NO wiring, so
    the matcher never scans it -> ~0 compute (DORMANT), state byte-identical.
    `bw_dissolve_on_leave` takes a departed agent (left==1) out of scope.
  * OPEN ECONOMY -- a traveller's inn stay INJECTS external coin (logged influx);
    an import moves coin ACROSS the boundary outward (logged outflux) and gives
    bigville a good it cannot produce.
  * FULL-AGENT TRAVELLERS -- one persisted node with held state (coin/story/goal)
    that REOCCURS remembered (the innkeeper's `knows` edge + `familiarity` grow
    across visits).
  * NEWS FROM THE FRONTIER -- a traveller's news yields a SECOND-HAND belief
    (lower confidence, hearsay); a resident who VISITED holds a GROUNDED one.
  * DREAM -> DEPARTURE (R8 + R11) -- a recruiter grounds a path; R8's dream
    collapse mints leave; the resident dissolves out of scope.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It builds its OWN Rust engine, loads the four R11
`self_load_only` seeds + R8 `bigville_goal_dream` (read-only), edits no tracked
file, and holds NO agent decision. It only does mechanical I/O: MATERIALIZE /
DISSOLVE frontier graph data (a traveller entering town = add node + activity
wiring; a departure = a RULE detaches it), wire edges, arm one-shots, bump the
clock, run the Rust `run_rules` fixpoint, and read state back. EVERY R11 decision
-- who runs each tick, the departure-to-dormant, the inn economics, the
familiarity bond, the import, the second-hand-vs-grounded belief, the recruiter's
grounded path -- is a seed RULE (bigville_world_scope / _open / _news / _depart +
R8's gg_dream_collapse_path). No new Rust: all compose existing DSL Terms.
"""
from __future__ import annotations

import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.engine_provenance import engine_preamble               # noqa: E402
engine_preamble(strict=False)

import substrate_rs                                                 # noqa: E402
from substrate.seed_loader import manifest_for                     # noqa: E402

R11_SEEDS = ("bigville_world_scope", "bigville_world_open",
             "bigville_world_news", "bigville_world_depart")
# R8 (read-only) supplies the Giantville escape Dream + the collapse rule the
# departure gate ties to.
R8_SEEDS = ("bigville_goal_dream",)

DREAM_GIANTVILLE = 1.0   # a Dream.kind code (opaque to the adapter)


class BigvilleWorldWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        for sid in R8_SEEDS + R11_SEEDS:
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._n = {}                       # name -> node id (persisted agents)
        self.clk = self.eng.add_node("Clock", {"epoch": 0.0})
        self.ledger = self.eng.add_node(
            "Ledger", {"external_influx": 0.0, "external_outflux": 0.0})

    # ------------------------------------------------------------ engine I/O
    def _run(self):
        return self.eng.run_rules(1000000)

    def _a(self, name):
        return self.eng.node(self._n[name])["attrs"]

    def set_attrs(self, name, **kw):
        for k, v in kw.items():
            self.eng.set_attr(self._n[name], k, float(v))

    # ---------------------------------------------- SCOPE: materialize/dissolve
    def _wire_active(self, nid):
        """Give an agent the activity wiring that makes bw_run_in_scope MATCH it
        (in scope). Mechanical -- materialize from the frontier."""
        hb = self.eng.add_node("HeartBeat", {})
        self.eng.add_edge_unchecked(nid, "active_beat", hb)
        self.eng.add_edge_unchecked(nid, "active_clock", self.clk)

    def materialize_agent(self, name, *, in_scope=True, **attrs):
        """Add a PERSISTED agent node (a resident or a traveller). When wired it
        carries the activity wiring; out of scope it is a bare dormant node (no
        wiring -> matcher never scans it -> ~0 compute). `in_scope` is a
        materialization PARAMETER (which side of the frontier the agent enters
        on) -- an ingest choice, not a graph-state read. Mechanical ingest."""
        wired = bool(in_scope)
        base = dict(in_scope=1.0 if wired else 0.0, left=0.0, dormant=0.0,
                    last_beat=0.0, age=0.0)
        base.update({k: float(v) for k, v in attrs.items()})
        nid = self.eng.add_node("Villager", base)
        self._n[name] = nid
        if wired:
            self._wire_active(nid)
        return nid

    def enter_scope(self, name):
        """A dormant agent RE-ENTERS scope (frontier arrival / reactivation): the
        activity wiring is re-attached and the leave-flag cleared (an arrival is
        not a departure); its persisted attrs otherwise resume unchanged.
        Mechanical (an external boundary-crossing event)."""
        self.eng.set_attr(self._n[name], "in_scope", 1.0)
        self.eng.set_attr(self._n[name], "dormant", 0.0)
        self.eng.set_attr(self._n[name], "left", 0.0)
        self._wire_active(self._n[name])

    def tick(self):
        """Bump the shared clock one epoch and run the fixpoint. Each in-scope
        (wired) agent's bw_run_in_scope fires once; dormant agents are not
        matched. Returns the fixpoint step count."""
        self.eng.set_attr(self.clk, "epoch", self._epoch() + 1.0)
        return self._run()

    def _epoch(self):
        return float(self.eng.node(self.clk)["attrs"]["epoch"])

    def in_scope_of(self, name):
        return int(self._a(name).get("in_scope", 0.0))

    def dormant_of(self, name):
        return int(self._a(name).get("dormant", 0.0))

    def age_of(self, name):
        return float(self._a(name).get("age", 0.0))

    def is_wired(self, name):
        return bool(list(self.eng.neighbours(self._n[name], "active_beat")))

    # ------------------------------------------------------ OPEN ECONOMY / inn
    def add_inn(self, name, *, coin=0.0, lodging_cost=5.0):
        nid = self.eng.add_node("Inn", {"coin": float(coin),
                                         "lodging_cost": float(lodging_cost)})
        self._n[name] = nid
        return nid

    def add_traveller(self, name, *, coin=100.0, in_scope=True, story=0.0,
                      goal=0.0, is_recruiter=0.0):
        """A traveller is a FULL agent: a persisted Villager with held state
        (coin/story/goal) plus the traveller-role attrs. Mechanical ingest."""
        nid = self.materialize_agent(
            name, in_scope=in_scope, coin=coin, story=story, goal=goal,
            visits=0.0, stayed=0.0, stay_armed=0.0, bonded=0.0, familiarity=0.0,
            is_recruiter=is_recruiter, offer_armed=0.0,
            comprehend_armed=0.0, ground_armed=0.0, import_armed=0.0)
        return nid

    def lodge_at(self, trav, inn):
        """Wire a traveller to the inn + the external-trade ledger. Mechanical."""
        self.eng.add_edge_unchecked(self._n[trav], "lodges_at", self._n[inn])
        self.eng.add_edge_unchecked(self._n[trav], "logs", self.ledger)

    def stay(self, trav):
        """Arm one inn stay; bw_inn_stay + the bond rules run."""
        self.eng.set_attr(self._n[trav], "stayed", 0.0)
        self.eng.set_attr(self._n[trav], "stay_armed", 1.0)
        return self._run()

    def coin_of(self, name):
        return float(self._a(name).get("coin", 0.0))

    def visits_of(self, name):
        return float(self._a(name).get("visits", 0.0))

    def familiarity_of(self, name):
        return float(self._a(name).get("familiarity", 0.0))

    def inn_knows(self, inn, trav):
        return self._n[trav] in list(self.eng.neighbours(self._n[inn], "knows"))

    def external_influx(self):
        return float(self.eng.node(self.ledger)["attrs"]["external_influx"])

    def external_outflux(self):
        return float(self.eng.node(self.ledger)["attrs"]["external_outflux"])

    # ------------------------------------------------------------- imports
    def add_good(self, name, *, price=10.0, produced_locally=0.0):
        nid = self.eng.add_node("Good", {"price": float(price),
                                          "produced_locally": float(produced_locally),
                                          "imported": 0.0})
        self._n[name] = nid
        return nid

    def offer_import(self, resident, trav, good):
        """Wire a resident to buy a traveller-carried good. Mechanical."""
        self.eng.add_edge_unchecked(self._n[resident], "import_deal", self._n[trav])
        self.eng.add_edge_unchecked(self._n[trav], "carries", self._n[good])

    def buy_import(self, resident):
        self.eng.set_attr(self._n[resident], "import_armed", 1.0)
        return self._run()

    def owns_good(self, resident, good):
        return self._n[good] in list(self.eng.neighbours(self._n[resident], "owns_good"))

    def good_imported(self, good):
        return int(self.eng.node(self._n[good])["attrs"].get("imported", 0.0))

    # -------------------------------------------------- NEWS FROM THE FRONTIER
    def add_place(self, name, *, place_id=1.0):
        nid = self.eng.add_node("Place", {"place_id": float(place_id)})
        self._n[name] = nid
        return nid

    def add_resident(self, name, *, in_scope=True, coin=0.0):
        nid = self.materialize_agent(
            name, in_scope=in_scope, coin=coin, comprehend_armed=0.0,
            ground_armed=0.0, import_armed=0.0)
        return nid

    def bring_news(self, resident, place, *, credibility=0.7):
        """A traveller brings a NewsItem about a frontier place to a resident.
        Mechanical ingest of a testimony event."""
        news = self.eng.add_node("NewsItem", {"credibility": float(credibility)})
        self.eng.add_edge_unchecked(self._n[resident], "hears", news)
        self.eng.add_edge_unchecked(news, "about", self._n[place])
        return news

    def comprehend(self, resident):
        self.eng.set_attr(self._n[resident], "comprehend_armed", 1.0)
        return self._run()

    def mark_visited(self, resident, place):
        self.eng.add_edge_unchecked(self._n[resident], "visited", self._n[place])

    def ground_belief(self, resident):
        self.eng.set_attr(self._n[resident], "ground_armed", 1.0)
        return self._run()

    def giantville_belief(self, resident):
        blf = list(self.eng.neighbours(self._n[resident], "giantville_belief"))
        if not blf:
            return None
        a = self.eng.node(blf[0])["attrs"]
        return dict(confidence=float(a.get("confidence", 0.0)),
                    hearsay=int(a.get("provenance_hearsay", 0.0)),
                    grounded=int(a.get("provenance_grounded", 0.0)),
                    about_place=float(a.get("about_place", -1.0)))

    # ------------------------------------------- DREAM -> DEPARTURE (R8 + R11)
    def give_dream(self, name, *, kind=DREAM_GIANTVILLE, collapse_threshold=-100.0,
                   aversive_threshold=5.0):
        """Attach an R8 Giantville escape Dream (UNGROUNDED -- no grounded_path).
        Mechanical graph data (the R8 node shape)."""
        dr = self.eng.add_node("Dream", {
            "kind": float(kind), "relief_valence": 3.0, "relief_arousal": 2.0,
            "aversive_threshold": float(aversive_threshold),
            "collapse_threshold": float(collapse_threshold),
            "ungrounded": 0.0, "invoked": 0.0, "collapsed": 0.0, "latent": 0.0,
            "path_offered": 0.0})
        self.eng.add_edge_unchecked(self._n[name], "has_dream", dr)
        self._n["_dream_" + name] = dr
        return dr

    def dream_of(self, name):
        dr = self._n["_dream_" + name]
        a = self.eng.node(dr)["attrs"]
        return dict(collapsed=int(a.get("collapsed", 0.0)),
                    path_offered=int(a.get("path_offered", 0.0)),
                    has_grounded_path=bool(list(self.eng.neighbours(dr, "grounded_path"))))

    def recruits(self, trav, resident):
        """A recruiter approaches a resident. Mechanical wiring."""
        self.eng.set_attr(self._n[trav], "is_recruiter", 1.0)
        self.eng.add_edge_unchecked(self._n[trav], "recruits", self._n[resident])

    def offer_path(self, trav):
        """Arm the recruiter's offer; bw_recruiter_grounds_path mints the
        grounded_path on the resident's dream."""
        self.eng.set_attr(self._n[trav], "offer_armed", 1.0)
        return self._run()

    def arm_collapse(self, resident):
        """Arm R8's dream collapse; gg_dream_collapse_path fires when a
        grounded_path exists -> ActionGoal{leave}, left=1."""
        self.eng.set_attr(self._n[resident], "collapse_armed", 1.0)
        return self._run()

    def left_of(self, name):
        return int(self._a(name).get("left", 0.0))

    def action_goal_kinds(self, name):
        out = []
        for g in self.eng.neighbours(self._n[name], "has_goal"):
            n = self.eng.node(g)
            if n["type"] == "ActionGoal":
                out.append(n["attrs"].get("kind"))
        return out

    def returns_as_traveller(self, name, place):
        """A departed resident REOCCURS as a returning traveller who has now
        GROUNDED Giantville (the going made the dream a real life). Mechanical
        frontier re-arrival: re-enter scope + a visited edge so the news rule
        grounds the belief first-hand."""
        self.enter_scope(name)
        self.mark_visited(name, place)
        return self._n[name]

    # ------------------------------------------------------------ persistence
    def snapshot(self):
        """The whole world as a durable dict (stored-graph persistence)."""
        return self.eng.graph_to_dict()

    def node_attrs(self, name):
        return dict(self._a(name))

    # ----------------------------------------------------- COST INSTRUMENT
    def run_cost_of_rule(self, rule_name):
        """The engine's cost-units for one rule (a compute proxy)."""
        for row in self.eng.rule_costs():
            if row[0] == rule_name:
                return int(row[1])
        return 0

    def reset_costs(self):
        self.eng.reset_rule_costs()

    def timed_tick(self, reps=1):
        """Wall-clock µs for `reps` ticks (warm), for the scope-gating harness."""
        t0 = time.perf_counter()
        for _ in range(reps):
            self.tick()
        return (time.perf_counter() - t0) / reps * 1e6
