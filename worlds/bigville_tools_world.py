"""BigvilleToolsWorld -- bigville R43 (block 336000): TOOLS + INVENTORY.

Basic adventure-game mechanics: USE X ON Z / USE X WITH Y. A tool is an effectiveness
multiplier on an action, held in an agent's inventory. Bare hands can attempt anything
but bear almost nothing at large cost; the right tool actually works. The same knife
that helps prep food can wound a person -- one node, two fitnesses, selected by the verb.

A WORLD ADAPTER. No gather/strike/prep DECISION in Python -- tl_* are seed rules. The
adapter mints agents (each with their own bare hands + inventory slots), tools and their
fitness data, resource deposits, arms `use(agent, verb, target, tool)`, and reads.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402

# bare-hands fitness: (verb -> (mult, effort)). Hands bear almost nothing at large cost.
_HANDS = {"mine": (0.05, 3.0), "fish": (0.05, 3.0), "prep": (1.0, 1.0), "strike": (0.3, 1.0)}


class BigvilleToolsWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_tools"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._agents = {}
        self._tools = {}          # (agent, toolname) -> node
        self._slots = {}          # (agent, kind) -> node
        self._deposits = {}
        self._foods = {}
        self._owners = {}         # name -> claimant node (agent OR institution)
        self._claims = {}         # (holder, toolname) -> [OwnershipClaim nodes]
        self._instrument = {}     # agent -> current tool node
        self._acting_on = {}      # agent -> current target node

    def add_institution(self, name):
        """An institution (the inn) that can OWN things without holding them --
        the inn owns the kitchen's knives and pots; its cook holds them to work."""
        node = self.eng.add_node("Institution", {"name": name})
        self.eng.add_edge_unchecked(self._town, "has_institution", node)
        self._owners[name] = node
        return node

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name, *, energy=50.0, cook_skill=0.6, base_effort=1.0,
                  health=10.0, inventory=("ore", "fish")):
        a = self.eng.add_node("Agent", {"name": name, "energy": float(energy),
                                        "cook_skill": float(cook_skill), "base_effort": float(base_effort),
                                        "health": float(health), "act_verb": "", "act_armed": 0.0,
                                        "last_yield": 0.0, "last_effort": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_agent", a)
        self._agents[name] = a
        self._owners[name] = a          # an agent can own things (starting with their own hands)
        # every agent has their OWN bare hands (a per-agent tool, so no shared-node edge clash)
        self._mint_tool(name, "hands", _HANDS)          # owner defaults to the holder (you own your hands)
        self._instrument[name] = self._tools[(name, "hands")]
        self.eng.add_edge_unchecked(a, "instrument", self._instrument[name])
        # inventory slots -- a haul lands in the slot matching the deposit's resource
        for kind in inventory:
            s = self.eng.add_node("Resource", {"kind": kind, "qty": 0.0})
            self.eng.add_edge_unchecked(a, "holds", s)
            self._slots[(name, kind)] = s
        return a

    def _mint_tool(self, agent, toolname, fits):
        """Mint a tool physically HELD by `agent` (inventory). Ownership is NOT set here --
        it is a separate recognized claim (owner is not a world fact)."""
        t = self.eng.add_node("Tool", {"name": toolname})
        self.eng.add_edge_unchecked(self._agents[agent], "holds", t)
        for verb, (mult, eff) in fits.items():
            f = self.eng.add_node("Fitness", {"verb": verb, "mult": float(mult), "effort": float(eff)})
            self.eng.add_edge_unchecked(t, "fit_for", f)
        self._tools[(agent, toolname)] = t
        return t

    def give_tool(self, agent, toolname, **fits):
        """Give `agent` a tool with per-verb fitness, e.g. give_tool('M','pick', mine=(1.0,1.0)).
        This is PHYSICAL possession only. Who OWNS it is a separate recognized claim
        (claim_ownership). A tool with several fitnesses (knife: prep+strike) is dual-use."""
        return self._mint_tool(agent, toolname, fits)

    # ---- ownership: a RECOGNIZED FRAME, not a world fact (mirrors authority=Count(recognizers)) ----
    def claim_ownership(self, claimant, holder, toolname):
        """`claimant` (an institution or agent) CLAIMS to own the tool `holder` holds. A claim is
        just an assertion -- it is worth only the recognition it gathers, not a fact by itself."""
        if claimant not in self._owners:
            self.add_institution(claimant)
        c = self.eng.add_node("OwnershipClaim", {"claimant": claimant, "recognition": 0.0})
        self.eng.add_edge_unchecked(c, "over", self._tools[(holder, toolname)])
        self.eng.add_edge_unchecked(self._owners[claimant], "asserts", c)
        self._claims.setdefault((holder, toolname), []).append(c)
        return c

    def recognize_ownership(self, recognizer, claim):
        """An agent RECOGNIZES an ownership claim. Ownership exists only to the extent it is
        recognized -- in the live town this is a decision collapse (rc_recognize); here it is
        seeded. Possession never grants it."""
        self.eng.add_edge_unchecked(self._agents[recognizer], "recognizes", claim)
        self._run()

    def add_deposit(self, name, *, resource, richness, stock, gather_verb):
        d = self.eng.add_node("Deposit", {"name": name, "resource": resource,
                                          "richness": float(richness), "stock": float(stock),
                                          "gather_verb": gather_verb})
        self.eng.add_edge_unchecked(self._town, "has_deposit", d)
        self._deposits[name] = d
        return d

    def add_food(self, name, *, taste=0.2, prep_bonus=0.3):
        f = self.eng.add_node("Food", {"name": name, "taste": float(taste),
                                       "prep_bonus": float(prep_bonus), "quality": 0.0})
        self._foods[name] = f
        return f

    def _target_node(self, target):
        if target in self._deposits: return self._deposits[target]
        if target in self._foods:    return self._foods[target]
        if target in self._agents:   return self._agents[target]
        raise KeyError(target)

    def use(self, agent, verb, target, *, tool="hands"):
        """USE X ON/WITH Z -- agent uses `tool` (default bare hands) to `verb` on `target`.
        Switches the agent's single instrument + acting_on edges, arms, and ticks."""
        a = self._agents[agent]
        # instrument: one 'using' tool at a time
        newtool = self._tools[(agent, tool)]
        if self._instrument.get(agent) is not newtool:
            if self._instrument.get(agent) is not None:
                self.eng.remove_edge_unchecked(a, "instrument", self._instrument[agent])
            self.eng.add_edge_unchecked(a, "instrument", newtool)
            self._instrument[agent] = newtool
        # acting_on: one target at a time
        tgt = self._target_node(target)
        if self._acting_on.get(agent) is not tgt:
            if self._acting_on.get(agent) is not None:
                self.eng.remove_edge_unchecked(a, "acting_on", self._acting_on[agent])
            self.eng.add_edge_unchecked(a, "acting_on", tgt)
            self._acting_on[agent] = tgt
        self.eng.set_attr(a, "act_verb", verb)
        self.eng.set_attr(a, "act_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def _a(self, name, k): return round(float(self.eng.node(self._agents[name])["attrs"].get(k, 0.0)), 4)
    def inventory(self, agent, kind): return round(float(self.eng.node(self._slots[(agent, kind)])["attrs"]["qty"]), 4)
    def energy(self, agent): return self._a(agent, "energy")
    def health(self, agent): return self._a(agent, "health")
    def last_yield(self, agent): return self._a(agent, "last_yield")
    def last_effort(self, agent): return self._a(agent, "last_effort")
    def deposit_stock(self, name): return round(float(self.eng.node(self._deposits[name])["attrs"]["stock"]), 4)
    def food_quality(self, name): return round(float(self.eng.node(self._foods[name])["attrs"]["quality"]), 4)
    def food_taste(self, name): return round(float(self.eng.node(self._foods[name])["attrs"]["taste"]), 4)

    # ownership is a RECOGNIZED frame, not a world fact -- read it by counting recognition
    def _claim_recognition(self, claim):
        return int(round(float(self.eng.node(claim)["attrs"].get("recognition", 0.0))))
    def recognition_of(self, claim):
        return self._claim_recognition(claim)
    def owner_of(self, holder, toolname):
        """The RECOGNIZED owner of the tool `holder` holds -- the claimant of the most-recognized
        claim over it. None if unclaimed/unrecognized, 'disputed' if the top is tied. NOT a fact:
        it is whoever the town recognizes, computed from recognition counts."""
        claims = self._claims.get((holder, toolname), [])
        scored = [(self._claim_recognition(c), self.eng.node(c)["attrs"]["claimant"]) for c in claims]
        scored = [(r, name) for r, name in scored if r > 0]
        if not scored:
            return None
        top = max(r for r, _ in scored)
        winners = [name for r, name in scored if r == top]
        return winners[0] if len(winners) == 1 else "disputed"
    def holds_tool(self, holder, toolname):
        return (holder, toolname) in self._tools
