"""BigvilleLandWorld -- bigville R13 (block 261000): graph-native LAND, the
FOUNDATIONAL scarce asset, on top of the proven R7 finance world. LAND is FINITE /
NON-PRODUCED / CONSERVED: a PLOT is a graph node, OWNERSHIP is an `owns` edge, and
Sigma(Plot) is INVARIANT -- no rule mints or destroys a Plot node; acquisition only
MOVES `owns` edges over a fixed set of pre-existing parcels.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2 LAND + sec 3 R13)
-----------------------------------------------------------------------------
  * ACQUISITION (3 modes) -- BUY (seller-priced market, `bl_buy` / the can't-afford
                       `bl_buy_fail` control), CLAIM (unowned FRONTIER land,
                       first-come homestead, `bl_claim`), GRANT (council, `bl_grant`).
  * CONSERVATION    -- Sigma(Plot) invariant: every transfer is an `owns` edge move;
                       no node minted/destroyed. Ownership PARTITIONS the fixed map
                       (<=1 owner per plot).
  * ROOT OF TENURE/BUILD/COLLATERAL -- construction REQUIRES the plot (`bl_build`;
                       building on another's land = `bl_build_trespass`); foreclosure
                       transfers the LAND (`bl_foreclose_land` grounds R7's proxied
                       collateral by keying off R7's OWN `foreclosed` flag).
  * CONCENTRATION + THE STRUCTURAL FLOOR -- land pools with capital (the rich buyer
                       sweeps the market); the landless escape ONLY via a STRUCTURAL
                       lever -- a land TAX (`bl_land_tax` -> `bl_tax_forfeit` ->
                       council -> grant), a GRANT, or ENCLOSURE-REVERSAL
                       (`bl_enclosure_reversal`) -- NEVER personal effort.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R7 (BigvilleFinWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY does mechanical I/O: register Plot graph
data + `owns` edges (ingest); ARM an acquisition by wiring the transient
`wants_to_buy` / `wants_to_claim` / `granted_to` / `wants_to_build` edge or a
one-shot `*_armed` flag; run the Rust `run_rules` fixpoint; read state back. EVERY
land decision -- buy-vs-fail, claim/first-come, grant, build-vs-trespass, foreclose,
tax, forfeit, enclosure-reversal -- is a seed RULE (bigville_land_market /
bigville_land_tenure), never Python. No new Rust.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                       # noqa: E402
from worlds.bigville_fin_world import BigvilleFinWorld                # noqa: E402

# Plot attrs set on every parcel so a rule never reads a missing key.
PLOT_DEFAULTS = dict(
    owned=0.0, frontier=0.0, for_sale=0.0, price=0.0, built=0.0,
    tax=0.0, tax_armed=0.0, revert_armed=0.0, forfeited=0.0,
)


class BigvilleLandWorld(BigvilleFinWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_land_market", "bigville_land_tenure"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._plots = {}          # name -> Plot nid
        self._plot_name = {}      # nid -> name

    # ---------------------------------------------------------------- ingest
    def set_council(self, name):
        """Mark a character as THE council (R9), the only grantor bl_grant honours.
        Mechanical attr write."""
        self.eng.set_attr(self._movers[name], "is_council", 1.0)

    def add_plot(self, name, *, frontier=False, price=0.0, tax=0.0):
        """A parcel of the FIXED map. `frontier=True` seeds unowned commons open to
        CLAIM. Mechanical graph data -- this is the ONLY place Plot nodes are minted
        (at ingest, a fixed map); no RULE ever mints or destroys one."""
        attrs = dict(PLOT_DEFAULTS)
        attrs.update(plot_id=float(len(self._plots)), frontier=1.0 if frontier else 0.0,
                     price=float(price), tax=float(tax))
        p = self.eng.add_node("Plot", attrs)
        self._plots[name] = p
        self._plot_name[p] = name
        return p

    def own_plot(self, char, plot):
        """Seed initial ownership: an `owns` edge char->plot + owned=1. Ingest."""
        self.eng.add_edge_unchecked(self._movers[char], "owns", self._plots[plot])
        self.eng.set_attr(self._plots[plot], "owned", 1.0)

    def bank_own_plot(self, plot):
        """Seed the BANK as a plot owner (a foreclosed/held parcel). Ingest."""
        self.eng.add_edge_unchecked(self._bank, "owns", self._plots[plot])
        self.eng.set_attr(self._plots[plot], "owned", 1.0)

    def list_for_sale(self, plot, price):
        """The owner LISTS a plot on the market at `price`. Mechanical (WHO lists /
        at what price is opaque data; the BUY decision is bl_buy)."""
        self.eng.set_attr(self._plots[plot], "for_sale", 1.0)
        self.eng.set_attr(self._plots[plot], "price", float(price))

    def set_taxed_by(self, plot, council):
        """Wire a plot under a jurisdiction's land tax (a `taxed_by` edge). Ingest."""
        self.eng.add_edge_unchecked(self._plots[plot], "taxed_by", self._movers[council])

    def secure_on_plot(self, char, plot):
        """Link a character's R7 MORTGAGE to the LAND it is secured on (a
        `secured_on_plot` edge mort->plot), so foreclosure transfers the plot. Ingest
        -- reuses the R7 Mortgage node READ-ONLY."""
        mort = self._mortgages[char]
        self.eng.add_edge_unchecked(mort, "secured_on_plot", self._plots[plot])

    # ------------------------------------------------- rule-driven one-shots
    def want_buy(self, buyer, plot):
        """ARM a market purchase: wire the transient `wants_to_buy` edge; bl_buy /
        bl_buy_fail decides + applies."""
        self.eng.add_edge_unchecked(self._movers[buyer], "wants_to_buy", self._plots[plot])
        return self._run()

    def want_buy_many(self, buyer, plots):
        """The market SWEEP: arm the buyer against each plot in TURN, ONE fixpoint per
        plot, so the shrinking BUDGET is respected (bl_buy re-reads coin>=price after
        each purchase, then bl_buy_fail once the budget is exhausted). One-arm-per-
        fixpoint is the safe primitive: a match set is snapshotted WITHIN a fixpoint,
        so a budget-coupled rule must not be armed against many plots at once."""
        n = 0
        for plot in plots:
            self.eng.add_edge_unchecked(self._movers[buyer], "wants_to_buy", self._plots[plot])
            n += self._run()
        return n

    def want_claim(self, claimant, plot):
        """ARM a homestead CLAIM: wire the transient `wants_to_claim` edge; bl_claim
        decides (frontier + unowned, first-come)."""
        self.eng.add_edge_unchecked(self._movers[claimant], "wants_to_claim", self._plots[plot])
        return self._run()

    def grant(self, council, plot, recipient):
        """The COUNCIL GRANT lever: wire the `granted_to` edge; bl_grant moves `owns`
        council->recipient (the council must already hold the plot)."""
        self.eng.add_edge_unchecked(self._plots[plot], "granted_to", self._movers[recipient])
        return self._run()

    def want_build(self, builder, plot):
        """ARM construction: wire the transient `wants_to_build` edge; bl_build (owns
        it) or bl_build_trespass (someone else's) decides."""
        self.eng.add_edge_unchecked(self._movers[builder], "wants_to_build", self._plots[plot])
        return self._run()

    def levy_tax(self, plots):
        """The GEORGIST land-tax lever: arm the per-plot tax on each named plot;
        bl_land_tax (pay) or bl_tax_forfeit (can't pay -> plot to council) decides."""
        for plot in plots:
            self.eng.set_attr(self._plots[plot], "tax_armed", 1.0)
        return self._run()

    def revert_commons(self, plot):
        """The ENCLOSURE-REVERSAL lever: arm a plot to revert to unowned frontier
        commons; bl_enclosure_reversal applies it."""
        self.eng.set_attr(self._plots[plot], "revert_armed", 1.0)
        return self._run()

    # ------------------------------------------------- glass-box read-offs
    def _owners(self):
        """Every candidate holder of land: the characters + the bank."""
        holders = dict(self._movers)
        if self._bank is not None:
            holders["__bank__"] = self._bank
        return holders

    def owns_plot(self, char, plot):
        holder = self._bank if char == "__bank__" else self._movers[char]
        return self._plots[plot] in list(self.eng.neighbours(holder, "owns"))

    def owner_of(self, plot):
        """The single owner name of a plot, or None if unowned (the partition)."""
        p = self._plots[plot]
        found = [nm for nm, nid in self._owners().items()
                 if p in list(self.eng.neighbours(nid, "owns"))]
        assert len(found) <= 1, "a plot has >1 owner -- partition violated: %r" % found
        return found[0] if found else None

    def plots_held(self, char):
        holder = self._bank if char == "__bank__" else self._movers[char]
        return sum(1 for p in self._plots.values()
                   if p in list(self.eng.neighbours(holder, "owns")))

    def total_plots(self):
        """Sigma(Plot): the conserved count of land parcels (a mechanical Count)."""
        return len(list(self.eng.nodes("Plot")))

    def holdings(self):
        """name -> plots held, for every holder that holds >=1 (concentration)."""
        h = {nm: self.plots_held(nm) for nm in self._owners()}
        return {nm: n for nm, n in h.items() if n > 0}

    def max_share(self):
        """The largest single holding as a fraction of all land (a concentration
        read-off; 1.0 = one holder owns everything)."""
        tot = self.total_plots()
        if tot == 0:
            return 0.0
        held = [self.plots_held(nm) for nm in self._owners()]
        return max(held) / float(tot)

    def plot_attr(self, plot, key):
        return float(self.eng.node(self._plots[plot])["attrs"].get(key, 0.0))

    def is_frontier(self, plot):
        return self.plot_attr(plot, "frontier") == 1.0

    def is_built(self, plot):
        return self.plot_attr(plot, "built") == 1.0

    def is_forfeited(self, plot):
        return self.plot_attr(plot, "forfeited") == 1.0

    def trespass_of(self, char):
        return int(self.eng.node(self._movers[char])["attrs"].get("trespass", 0.0))

    def buy_failed_of(self, char):
        return int(self.eng.node(self._movers[char])["attrs"].get("buy_failed", 0.0))
