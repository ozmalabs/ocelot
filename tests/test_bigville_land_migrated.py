"""bigville R13 (block 261000) -- LAND gates: land the FOUNDATIONAL scarce asset,
FINITE / NON-PRODUCED / CONSERVED (Σ Count(Plot) invariant; ownership partitions a
fixed map); the three ACQUISITION modes BUY / CLAIM (first-come) / GRANT + the
structural-exclusion control; land as the ROOT of tenure / construction / collateral
(build requires the plot; foreclosure transfers the LAND, grounding R7's proxy); and
land CONCENTRATES harder than money -> the landless escape ONLY via a STRUCTURAL lever
(tax / grant / enclosure-reversal), never personal effort (the agency/structure bedrock,
§0). Gates mirror BIGVILLE_LAND_PREREG.md.

No land decision lives in Python -- every buy / fail / claim / grant / build /
trespass / foreclose / tax / forfeit / reversal is a seed rule (bigville_land_market /
bigville_land_tenure). The adapter wires transient edges / arms one-shots, ticks and
reads (source-audit at the foot of this file). NO Plot node is minted or destroyed by
any rule (Σplots conserved at the source level); ZERO new Rust.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_land_world import BigvilleLandWorld               # noqa: E402
from worlds.bigville_time_world import DAY                             # noqa: E402


def _pool(w):
    return sorted(w._cell_at.keys())


def _world():
    w = BigvilleLandWorld(day_range=16)
    w.set_phase(DAY)
    return w


# ============================================== G-land-is-owned-and-conserved
def test_land_is_conserved_through_all_modes():
    """Σ Count(Plot) is INVARIANT across BUY, CLAIM, GRANT, TAX-FORFEIT and
    ENCLOSURE-REVERSAL -- land is never minted or destroyed, only TRANSFERRED (an
    `owns` edge moves). The count equals the ingest count at every step."""
    w = _world()
    P = _pool(w)
    w.make_char("council", P[0], coin=0); w.set_council("council")
    w.make_char("rich", P[10], coin=1000)
    w.make_char("seller", P[11], coin=0)
    w.make_char("claimant", P[12], coin=0)
    w.make_char("recipient", P[13], coin=0)
    w.make_char("baron", P[14], coin=0)          # can't pay tax
    # a FIXED map of six parcels
    w.add_plot("m0"); w.own_plot("seller", "m0"); w.list_for_sale("m0", 100)
    w.add_plot("m1", frontier=True)
    w.add_plot("m2"); w.own_plot("council", "m2")
    w.add_plot("m3", tax=50.0); w.own_plot("baron", "m3"); w.set_taxed_by("m3", "council")
    w.add_plot("m4"); w.own_plot("rich", "m4")
    w.add_plot("m5"); w.own_plot("seller", "m5")
    N0 = w.total_plots()
    assert N0 == 6

    w.want_buy("rich", "m0")                      # BUY
    assert w.total_plots() == N0
    w.want_claim("claimant", "m1")                # CLAIM
    assert w.total_plots() == N0
    w.grant("council", "m2", "recipient")         # GRANT
    assert w.total_plots() == N0
    w.levy_tax(["m3"])                            # TAX -> FORFEIT to council
    assert w.total_plots() == N0 and w.owner_of("m3") == "council"
    w.revert_commons("m4")                        # ENCLOSURE-REVERSAL
    assert w.total_plots() == N0
    w.want_claim("claimant", "m4")               # re-claim the commons
    assert w.total_plots() == N0
    # the map is exactly the six seeded parcels, none minted/destroyed
    assert w.total_plots() == N0 == len(w._plots)


def test_ownership_partitions_the_map():
    """Ownership PARTITIONS the fixed map: every plot has <=1 owner throughout a
    contested run (owner_of asserts the partition; a buy/claim/grant never leaves two
    owners on one parcel)."""
    w = _world()
    P = _pool(w)
    w.make_char("a", P[10], coin=500)
    w.make_char("b", P[11], coin=500)
    w.make_char("seller", P[12], coin=0)
    for i in range(3):
        w.add_plot("p%d" % i); w.own_plot("seller", "p%d" % i); w.list_for_sale("p%d" % i, 100)
    w.add_plot("f", frontier=True)
    # a and b both chase the market + the frontier
    for nm in ("a", "b"):
        for i in range(3):
            w.want_buy(nm, "p%d" % i)
        w.want_claim(nm, "f")
    # every plot resolves to exactly one owner (or none) -- owner_of asserts <=1
    owners = [w.owner_of("p%d" % i) for i in range(3)] + [w.owner_of("f")]
    for o in owners:
        assert o is None or isinstance(o, str)
    # no parcel is double-sold: the sum of holdings never exceeds the map
    total_held = sum(w.plots_held(nm) for nm in ("a", "b", "seller"))
    assert total_held == w.total_plots(), "every parcel has exactly one holder"


# ===================================== G-acquisition (buy / claim / grant) + control
def test_buy_acquires_seller_priced():
    """BUY: a buyer who can afford a listed plot acquires it -- coin transfers
    buyer->seller and the `owns` edge moves seller->buyer."""
    w = _world()
    P = _pool(w)
    w.make_char("buyer", P[10], coin=300)
    w.make_char("seller", P[11], coin=0)
    w.add_plot("lot"); w.own_plot("seller", "lot"); w.list_for_sale("lot", 120)
    w.want_buy("buyer", "lot")
    assert w.owner_of("lot") == "buyer"
    assert w.coin_of("buyer") == 180 and w.coin_of("seller") == 120
    assert w.plot_attr("lot", "for_sale") == 0.0, "de-listed after sale"


def test_claim_homesteads_frontier_first_come():
    """CLAIM: unowned FRONTIER land is homesteaded FIRST-COME. The first claimant
    takes it; a later claimant to the SAME plot is blocked (owned) -- the ABSENCE of a
    match, graph-native first-come."""
    w = _world()
    P = _pool(w)
    w.make_char("first", P[10], coin=0)
    w.make_char("second", P[11], coin=0)
    w.add_plot("frontier", frontier=True)
    w.want_claim("first", "frontier")            # arrives first
    w.want_claim("second", "frontier")           # too late
    assert w.owner_of("frontier") == "first"
    assert w.plots_held("second") == 0
    assert not w.is_frontier("frontier"), "claimed land is no longer frontier commons"


def test_grant_by_council():
    """GRANT: the council (R9) transfers a council-held plot to a recipient."""
    w = _world()
    P = _pool(w)
    w.make_char("council", P[0], coin=0); w.set_council("council")
    w.make_char("recipient", P[10], coin=0)
    w.add_plot("commons"); w.own_plot("council", "commons")
    w.grant("council", "commons", "recipient")
    assert w.owner_of("commons") == "recipient"


def test_landless_cannot_acquire_structural_exclusion():
    """CONTROL (the structural exclusion): all land OWNED, NO frontier, NO seller
    (nothing listed), NO grant -> a landless resident who ARMS a buy AND a claim
    acquires NOTHING. Only a structural lever can open land to him -- personal effort
    cannot. This control MUST leave him at 0 holdings."""
    w = _world()
    P = _pool(w)
    w.make_char("baron", P[10], coin=0)
    w.make_char("landless", P[11], coin=1000)     # even WITH coin -- nothing is for sale
    for i in range(3):
        w.add_plot("p%d" % i); w.own_plot("baron", "p%d" % i)   # all owned, none listed, none frontier
    w.want_buy("landless", "p0")                  # nothing for_sale -> no match
    w.want_claim("landless", "p1")                # owned -> blocked
    assert w.plots_held("landless") == 0, "the landless are STRUCTURALLY excluded"
    assert w.plots_held("baron") == 3, "the baron keeps all land"


def test_buy_fail_cant_afford_control():
    """CONTROL: a buyer who CANNOT afford the price does not acquire -- bl_buy_fail
    flags the failure, no transfer, the seller keeps the plot."""
    w = _world()
    P = _pool(w)
    w.make_char("poor", P[10], coin=5)
    w.make_char("seller", P[11], coin=0)
    w.add_plot("lot"); w.own_plot("seller", "lot"); w.list_for_sale("lot", 100)
    w.want_buy("poor", "lot")
    assert w.owner_of("lot") == "seller" and w.buy_failed_of("poor") == 1
    assert w.coin_of("poor") == 5, "no coin left the poor buyer"


# ================================================ G-land-underlies-tenure+build
def test_build_requires_owning_the_plot():
    """Construction REQUIRES owning the plot (the R12 precondition). The owner builds;
    a non-owner on ANOTHER'S land is refused = TRESPASS; unowned frontier is refused
    too (built stays 0 -- refusal as absence)."""
    w = _world()
    P = _pool(w)
    w.make_char("owner", P[10], coin=0)
    w.make_char("intruder", P[11], coin=0)
    w.add_plot("mine"); w.own_plot("owner", "mine")
    w.add_plot("open", frontier=True)
    # owner builds on his own plot
    w.want_build("owner", "mine")
    assert w.is_built("mine") and w.trespass_of("owner") == 0
    # intruder builds on the owner's land -> trespass, NOT built again by him
    w.eng.set_attr(w._plots["mine"], "built", 0.0)      # reset the built flag (ingest)
    w.want_build("intruder", "mine")
    assert w.trespass_of("intruder") == 1 and not w.is_built("mine")
    # nobody may build on unowned frontier -> refused (no owner edge, no build)
    w.want_build("intruder", "open")
    assert not w.is_built("open"), "unowned frontier cannot be built (refused as absence)"


def _shock_land_world(mortgagor):
    """A fishmonger whose income collapses, either as a MORTGAGOR whose mortgage is
    secured on his PLOT, or an OWNER-outright of the same plot."""
    w = _world()
    P = _pool(w)
    w.add_bank("scrooge", P[0], reserves=100000, salary=0, fair_rate_bp=500)
    w.make_char("fish", P[10], coin=1000)
    w.attach_affect("fish", concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=5.0)
    w.add_house("h", 200, apprec=0)
    w.add_plot("land"); w.own_plot("fish", "land")
    if mortgagor:
        w.mortgage("fish", "h", principal=500, payment=30, term=3)
        w.secure_on_plot("fish", "land")          # secured on the LAND
    w.set_char("fish", coin=0)                     # the income collapse
    for _ in range(5):
        w.period()
    return w


def test_foreclosure_transfers_the_land():
    """HEADLINE: foreclosure transfers the LAND. A mortgage secured on the fishmonger's
    PLOT + an income collapse -> R7 forecloses (its own decision, over the house) and
    R13 MOVES the plot's `owns` edge debtor->bank -- grounding R7's proxied
    land-as-ultimate-collateral. Σplots conserved."""
    w = _shock_land_world(mortgagor=True)
    assert w.foreclosed_of("fish") == 1, "the income collapse forecloses"
    assert w.owner_of("land") == "__bank__", "the LAND transfers to the bank"
    assert not w.owns_plot("fish", "land"), "the debtor loses the land"
    assert w.total_plots() == 1, "the parcel is not destroyed -- it moved"


def test_owned_outright_keeps_the_land():
    """CONTROL: the SAME income collapse on an OWNER-OUTRIGHT (no mortgage) keeps his
    land -- leverage on the LAND is the amplifier."""
    w = _shock_land_world(mortgagor=False)
    assert w.owner_of("land") == "fish", "the outright owner keeps his land"


def test_tenure_derives_from_land():
    """R7 TENURE derives from LAND: the landlord OWNS the plot (and rents to the
    tenant); the homeowner OWNS his plot; the renter owns NO land. The three tenures
    map to plot-ownership -- land is the root."""
    w = _world()
    P = _pool(w)
    w.add_bank("scrooge", P[0], reserves=100000, salary=0, fair_rate_bp=500)
    w.make_char("landlord", P[10], coin=1000)
    w.make_char("tenant", P[11], coin=1000)
    w.make_char("homeowner", P[12], coin=1000)
    w.add_house("rental_house", 100, apprec=0)
    w.add_house("own_house", 100, apprec=0)
    w.add_plot("landlord_plot"); w.own_plot("landlord", "landlord_plot")
    w.add_plot("homeowner_plot"); w.own_plot("homeowner", "homeowner_plot")
    w.rent("tenant", "landlord", "rental_house", rent=5, term=3)   # R7 tenancy
    assert w.owner_of("landlord_plot") == "landlord", "the landlord holds the land"
    assert w.owner_of("homeowner_plot") == "homeowner", "the homeowner holds his plot"
    assert w.plots_held("tenant") == 0, "the renter owns NO land (builds no land equity)"


# ================================================ G-land-concentrates + structural floor
def test_land_concentrates_with_capital():
    """Land POOLS with capital. The map starts DISTRIBUTED -- N small owners hold one
    parcel each (max_share = 1/N) and list them -- and a rich buyer sweeps the market:
    max_share rises to 1.0 while the poor hold 0. Non-produced + finite -> land
    concentrates HARDER than money (once bought it cannot be re-created for the poor)."""
    w = _world()
    P = _pool(w)
    w.make_char("rich", P[10], coin=10000)
    w.make_char("poor", P[11], coin=10)
    N = 6
    plots = ["lot%d" % i for i in range(N)]
    for i, nm in enumerate(plots):
        w.make_char("small%d" % i, P[20 + i], coin=0)        # a distributed smallholder
        w.add_plot(nm); w.own_plot("small%d" % i, nm); w.list_for_sale(nm, 100)
    share0 = w.max_share()
    assert abs(share0 - 1.0 / N) < 1e-9, "the map starts distributed (1 parcel each)"
    w.want_buy_many("rich", plots)                # the sweep
    for nm in plots:                              # the poor try too -- cannot afford
        w.want_buy("poor", nm)
    assert w.max_share() > share0, "land concentrates (max share rises from 1/N)"
    assert w.plots_held("rich") == N, "the rich buyer holds the whole market"
    assert w.plots_held("poor") == 0, "the poor hold none"
    assert w.max_share() == 1.0, "one holder owns ALL the land"


def _floor_world():
    """All land held by a baron; a landless resident (coin=0); a council holding one
    spare parcel; a taxable baron parcel; a revertible baron parcel."""
    w = _world()
    P = _pool(w)
    w.make_char("council", P[0], coin=0); w.set_council("council")
    w.make_char("baron", P[10], coin=5)           # can't pay a 50 tax
    w.make_char("landless", P[11], coin=0)
    w.add_plot("held0"); w.own_plot("baron", "held0")               # for enclosure-reversal
    w.add_plot("held1", tax=50.0); w.own_plot("baron", "held1")     # for tax-forfeit
    w.set_taxed_by("held1", "council")
    w.add_plot("spare"); w.own_plot("council", "spare")             # for the grant
    return w


def test_landless_escapes_only_structurally():
    """The AGENCY/STRUCTURE bedrock (§0): a landless resident's PERSONAL effort
    (unaffordable buy, no-frontier claim) leaves him at 0; only a STRUCTURAL lever opens
    land -- GRANT, ENCLOSURE-REVERSAL, or TAX-FORFEIT->GRANT. Each lever hands him a
    parcel; Σplots stays conserved throughout."""
    w = _floor_world()
    N0 = w.total_plots()
    # personal effort: nothing for sale he can afford, nothing frontier
    w.want_buy("landless", "held0")
    w.want_claim("landless", "held0")
    assert w.plots_held("landless") == 0, "personal effort cannot open land"

    # LEVER 1 -- council GRANT
    w.grant("council", "spare", "landless")
    assert w.plots_held("landless") == 1, "a grant opens land"

    # LEVER 2 -- ENCLOSURE-REVERSAL then claim
    w.revert_commons("held0")
    w.want_claim("landless", "held0")
    assert w.plots_held("landless") == 2, "enclosure-reversal opens land"

    # LEVER 3 -- GEORGIST land tax -> forfeit -> grant
    w.levy_tax(["held1"])
    assert w.owner_of("held1") == "council", "the baron forfeits the taxed plot"
    w.grant("council", "held1", "landless")
    assert w.plots_held("landless") == 3, "a land tax (redistributed) opens land"

    assert w.total_plots() == N0, "no land minted or destroyed by any lever"


def test_no_lever_stays_landless():
    """CONTROL: with NO structural lever applied, the same landless resident's personal
    effort leaves him at 0 -- the LEVER is what moves it, deterministically."""
    w = _floor_world()
    w.want_buy("landless", "held0")
    w.want_claim("landless", "held0")
    w.want_claim("landless", "held1")
    assert w.plots_held("landless") == 0, "no lever -> still landless"


# ==================================================================== source-audit
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every land DECISION is a seed rule, not Python. The adapter wires transient
    edges / arms one-shots, ticks and reads -- it never COMPUTES a buy / claim / grant /
    build / foreclose / tax outcome in Python."""
    import json
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_land_world.py")).read()
    world_src = re.sub(r"PLOT_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    market = json.load(open(os.path.join(_ROOT, "seeds", "bigville_land_market.json")))
    tenure = json.load(open(os.path.join(_ROOT, "seeds", "bigville_land_tenure.json")))
    rule_names = {r["name"] for r in market["rules"]} | {r["name"] for r in tenure["rules"]}
    assert rule_names == {
        "bl_buy", "bl_buy_fail", "bl_claim", "bl_grant",
        "bl_build", "bl_build_trespass", "bl_foreclose_land",
        "bl_land_tax", "bl_tax_forfeit", "bl_enclosure_reversal",
    }, "the ten land decisions are RULES"
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # the DECISION PARAMETERS appear ONLY in the seeds -- the adapter never branches on
    # them (they are opaque attrs it sets by name in ingest).
    for param in ("for_sale", "built", "foreclosed", "is_council", "revert_armed"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seeds_are_self_load_only_and_conserve_land():
    """Discipline at the source level: both seeds are `self_load_only` (loaded ONLY by
    the R13 adapter -> cannot regress another suite); NO rule mints or destroys a Plot
    node (no add_node/del_node anywhere -> Σplots conserved by construction); no coin
    attr is set from a fractional Div; NO new Rust."""
    import json
    market = json.load(open(os.path.join(_ROOT, "seeds", "bigville_land_market.json")))
    tenure = json.load(open(os.path.join(_ROOT, "seeds", "bigville_land_tenure.json")))
    for s in (market, tenure):
        assert s.get("self_load_only") is True, "%s must be self_load_only" % s["id"]
    for s in (market, tenure):
        for r in s["rules"]:
            for eff in r.get("effects", []):
                assert eff[0] not in ("add_node", "del_node"), \
                    "%s mints/destroys a node -- LAND is CONSERVED, only owns edges move" % r["name"]
                if eff[0] == "set_attr" and eff[2] in ("coin", "reserves", "balance"):
                    s_ = json.dumps(eff)
                    assert '"Div"' not in s_, "a coin attr must never be set from a fractional Div"
    # every plot transfer is an owns-edge move; the ONLY node minting is at adapter
    # ingest (add_plot), never a rule -- the conservation invariant at the source.
    both = json.dumps(market) + json.dumps(tenure)
    assert '"add_node"' not in both and '"del_node"' not in both, \
        "no rule adds or removes a node -- Σ Count(Plot) is invariant"
