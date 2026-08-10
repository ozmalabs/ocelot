"""bigville R12 (block 260000) -- CONSTRUCTION gates: a BUILDER consumes RAW
MATERIALS (timber+stone) + LABOUR (a per-tick step whose SPEED = the CONSTRUCTION
skill) over TIME (multi-tick) to raise a durable BUILDING on an OWNED, FUNDED plot
(R13 precondition); building on ANOTHER'S land is TRESPASS (refused); funding is
PERSONAL (coin) or a BANK LOAN (R7 -- a construction loan that ACCRUES like a
mortgage); an existing building is MODIFIED / ADDED-ON; the CHURCH EXPANDS iff its
donations/funds suffice; and THE MUTABLE WORLD (the headline) -- a new building
CHANGES the map so nav RE-ROUTES around it and occlusion UPDATES, removing it reverts
the cells. Gates mirror BIGVILLE_BUILD_PREREG.md.

No construction decision lives in Python -- every consume / raise / trespass / fund /
loan / accrue / addon / wall-off / expand / demolish is a seed rule
(bigville_build_construct / bigville_build_mutate). The adapter ingests graph data,
arms one-shots, ticks, reflects the `built` verdict into the host grid, and reads
(source-audit at the foot of this file). Imports R13/R7 READ-ONLY; ZERO new Rust.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_build_world import BigvilleBuildWorld           # noqa: E402
from worlds.bigville_time_world import DAY                           # noqa: E402


def _world():
    w = BigvilleBuildWorld(day_range=120)
    w.set_phase(DAY)
    return w


def _cells(w):
    return sorted(w._cell_at.keys())


# a walkable build site + a goal cell in the open square
SITE = (13, 8)
DOOR = (8, 4)             # the office's ONLY exit -- a genuine chokepoint
INSIDE = (5, 4)           # inside the enclosed office
GOAL = (12, 8)            # open square


# ================================= G-build-needs-materials+skill+time
def test_build_consumes_materials_skill_time():
    """A building rises only with MATERIALS (consumed) + SKILL (speed) + TIME
    (multi-tick). skill=2, required=6 -> 3 ticks; mat_cost=2 -> 6 timber+stone
    consumed; a Building is minted and the plot's map cell is marked blocked."""
    w = _world()
    w.make_char("bob", GOAL, coin=1000)
    w.add_buildable_plot("lot", SITE, required=6, mat_cost=2, build_cost=100)
    w.own_plot("bob", "lot")
    w.set_construction_skill("bob", 2)
    w.give_materials("bob", timber=100, stone=100)
    w.fund("bob", "lot")
    assert w.funded_of("lot") == 1 and w.coin_of("bob") == 900.0
    assert not w.is_built("lot")
    w.build_tick("bob", "lot")                      # tick 1
    assert w.progress_of("lot") == 2.0 and not w.is_built("lot"), "TIME: one tick != done"
    w.build_until_done("bob", "lot")
    assert w.is_built("lot"), "materials + skill + time -> a building"
    assert w.progress_of("lot") == 6.0
    assert w.timber_of("bob") == 94.0 and w.stone_of("bob") == 94.0, "materials consumed"
    assert w.building_count() == 1 and w.cell_blocked("lot") == 1


def test_ablate_materials_no_build():
    """Ablate MATERIALS (too little timber/stone) -> bb_consume never matches ->
    progress stays 0 -> NO building. Materials are load-bearing."""
    w = _world()
    w.make_char("bob", GOAL, coin=1000)
    w.add_buildable_plot("lot", SITE, required=6, mat_cost=2, build_cost=100)
    w.own_plot("bob", "lot")
    w.set_construction_skill("bob", 2)
    w.give_materials("bob", timber=1, stone=1)      # < mat_cost
    w.fund("bob", "lot")
    assert not w.build_until_done("bob", "lot", max_ticks=12)
    assert w.progress_of("lot") == 0.0 and w.building_count() == 0


def test_ablate_skill_no_build():
    """Ablate SKILL (no CONSTRUCTION skill) -> bb_consume never matches -> NO
    building. Skill is load-bearing."""
    w = _world()
    w.make_char("bob", GOAL, coin=1000)
    w.add_buildable_plot("lot", SITE, required=6, mat_cost=2, build_cost=100)
    w.own_plot("bob", "lot")
    w.give_materials("bob", timber=100, stone=100)  # no skill attached
    w.fund("bob", "lot")
    assert not w.build_until_done("bob", "lot", max_ticks=12)
    assert w.progress_of("lot") == 0.0 and w.building_count() == 0


def test_ablate_time_incomplete():
    """Ablate TIME (fewer ticks than required/skill) -> progress accrues but the
    building is NOT complete. required=6, skill=2 -> 2 ticks give progress 4 < 6."""
    w = _world()
    w.make_char("bob", GOAL, coin=1000)
    w.add_buildable_plot("lot", SITE, required=6, mat_cost=2, build_cost=100)
    w.own_plot("bob", "lot")
    w.set_construction_skill("bob", 2)
    w.give_materials("bob", timber=100, stone=100)
    w.fund("bob", "lot")
    w.build_tick("bob", "lot")
    w.build_tick("bob", "lot")
    assert w.progress_of("lot") == 4.0 and not w.is_built("lot"), "not enough TIME yet"
    assert w.building_count() == 0


# ============================================= G-financed-build
def test_personal_funding():
    """PERSONAL funding: the build cost is paid from the builder's SAVINGS (coin
    drops); funded=1, no loan taken."""
    w = _world()
    w.make_char("saver", GOAL, coin=500)
    w.add_buildable_plot("lot", SITE, required=2, mat_cost=1, build_cost=120)
    w.own_plot("saver", "lot")
    w.set_construction_skill("saver", 2)
    w.give_materials("saver", timber=10, stone=10)
    w.fund("saver", "lot")
    assert w.funded_of("lot") == 1 and w.coin_of("saver") == 380.0
    assert w.has_loan("saver") == 0, "no loan -- paid from savings"
    assert w.build_until_done("saver", "lot")


def test_loan_funded_build_accrues():
    """LOAN funding: a builder with NO savings takes a BANK LOAN (R7) -> the bank's
    reserves drop, the builder's coin rises, and the build is funded from the
    proceeds. The construction loan ACCRUES like a mortgage (10% -> 100 becomes 110)."""
    w = _world()
    P = _cells(w)
    w.add_bank("scrooge", P[0], reserves=100000, salary=0, fair_rate_bp=1000)
    w.make_char("poor", GOAL, coin=0)
    w.add_buildable_plot("lot", SITE, required=2, mat_cost=1, build_cost=100)
    w.own_plot("poor", "lot")
    w.set_construction_skill("poor", 2)
    w.give_materials("poor", timber=10, stone=10)
    w.take_loan("poor", 100)
    assert w.coin_of("poor") == 100.0 and w.reserves() == 99900.0
    assert w.has_loan("poor") == 1 and w.loan_balance_of("poor") == 100.0
    w.fund("poor", "lot")
    assert w.funded_of("lot") == 1 and w.coin_of("poor") == 0.0
    assert w.build_until_done("poor", "lot")
    w.accrue_loan("poor")
    assert w.loan_balance_of("poor") == 110.0, "interest accrues like a mortgage"


def test_no_funds_no_loan_no_build_control():
    """CONTROL: insufficient savings AND no loan -> bb_fund does not fire -> funded
    stays 0 -> bb_consume cannot proceed -> NO building. Funding is load-bearing."""
    w = _world()
    w.make_char("broke", GOAL, coin=5)
    w.add_buildable_plot("lot", SITE, required=2, mat_cost=1, build_cost=100)
    w.own_plot("broke", "lot")
    w.set_construction_skill("broke", 2)
    w.give_materials("broke", timber=10, stone=10)
    w.fund("broke", "lot")
    assert w.funded_of("lot") == 0, "cannot fund from 5 coin"
    assert not w.build_until_done("broke", "lot", max_ticks=8)
    assert w.coin_of("broke") == 5.0 and w.building_count() == 0


# ============================================= G-mutable-world (HEADLINE)
def test_build_reroutes_nav_and_updates_occlusion():
    """THE HEADLINE: a new building CHANGES the map. Baseline -- a resident inside the
    office reaches the square (nav routes through the door) and Mary sees into the
    office. Build a house ON the door plot (a chokepoint) -> bb_raise marks the map
    cell blocked+occludes, bbnav_wall_off severs its walkable adjacency, and the
    adapter reflects `built` into the host grid. AFTER -- the resident is SEALED IN
    (nav can no longer route through) and Mary's line-of-sight is BROKEN (occlusion
    updated). REMOVE the building -> the cells REVERT (both restore)."""
    w = _world()
    w.make_char("resident", INSIDE, coin=0, energy=4000.0)
    w.make_char("owner", GOAL, coin=1000)
    w.add_buildable_plot("door", DOOR, required=2, mat_cost=1, build_cost=50)
    w.own_plot("owner", "door")
    w.set_construction_skill("owner", 2)
    w.give_materials("owner", timber=10, stone=10)

    # baseline -- the map-belief connects, LOS is clear
    assert w.can_reach("resident", INSIDE, GOAL), "baseline: nav routes through the door"
    assert w.can_see("Mary", INSIDE), "baseline: Mary sees into the office"
    assert w.cell_blocked("door") == 0

    # build the house on the chokepoint
    w.fund("owner", "door")
    assert w.build_until_done("owner", "door")
    assert w.cell_blocked("door") == 1 and w.cell_occludes("door") == 1
    assert w.grid[DOOR[1]][DOOR[0]] != w._orig_tile[DOOR], "host grid reflects the build"

    # nav RE-ROUTES / seals; occlusion UPDATES
    assert not w.can_reach("resident", INSIDE, GOAL), "the building seals nav (re-route)"
    assert not w.can_see("Mary", INSIDE), "the building breaks line-of-sight (occlusion)"

    # remove it -> the cells REVERT
    w.demolish("door")
    assert not w.is_built("door") and w.cell_blocked("door") == 0
    assert w.can_reach("resident", INSIDE, GOAL), "demolition reverts nav"
    assert w.can_see("Mary", INSIDE), "demolition reverts occlusion"


# ============================================= G-church-expands-if-funded
def test_church_expands_when_funded():
    """The CHURCH (an institution) EXPANDS iff donations/funds cover the cost ->
    capacity + size grow, funds drop (a grounded lift of R9's fixed size)."""
    w = _world()
    w.add_church("stewe", GOAL, funds=40, expand_cost=50, capacity=1)
    w.donate("stewe", 20)                            # tips it over the cost
    assert w.church_funds("stewe") == 60.0
    w.expand_church("stewe")
    assert w.church_capacity("stewe") == 2.0 and w.church_size("stewe") == 2.0
    assert w.church_funds("stewe") == 10.0


def test_church_no_expand_unfunded_control():
    """CONTROL: funds below the cost -> bb_church_expand does not fire -> NO
    expansion. Institutional growth is income-gated."""
    w = _world()
    w.add_church("stewe", GOAL, funds=10, expand_cost=50, capacity=1)
    w.expand_church("stewe")
    assert w.church_capacity("stewe") == 1.0, "cannot expand without the funds"
    assert w.church_funds("stewe") == 10.0


# ============================================= G-modify / add-on
def test_addon_extends_building():
    """MODIFY / ADD-ON: an existing building is extended with more materials ->
    size + capacity grow, materials consumed (a durable modification)."""
    w = _world()
    w.make_char("bob", GOAL, coin=1000)
    w.add_buildable_plot("lot", SITE, required=2, mat_cost=1, build_cost=100)
    w.own_plot("bob", "lot")
    w.set_construction_skill("bob", 2)
    w.give_materials("bob", timber=10, stone=10)
    w.fund("bob", "lot")
    w.build_until_done("bob", "lot")
    w.eng.set_attr(w._buildings["lot"], "addon_cost", 3.0)
    tw0, size0 = w.timber_of("bob"), w.building_size("lot")
    w.extend("bob", "lot")
    assert w.building_size("lot") == size0 + 1 and w.building_capacity("lot") == 2.0
    assert w.timber_of("bob") == tw0 - 3.0 and w.stone_of("bob") == tw0 - 3.0


# ============================================= G-trespass
def test_build_on_others_land_is_trespass():
    """Building on ANOTHER'S land is refused = TRESPASS: an intruder who arms a build
    on an owned plot gets a trespass flag, and the plot is NOT built by him."""
    w = _world()
    w.make_char("owner", GOAL, coin=1000)
    w.make_char("intruder", (11, 8), coin=1000)
    w.add_buildable_plot("lot", SITE, required=2, mat_cost=1, build_cost=100)
    w.own_plot("owner", "lot")
    w.fund("owner", "lot")
    w.set_construction_skill("intruder", 2)
    w.give_materials("intruder", timber=10, stone=10)
    w.build_tick("intruder", "lot")
    assert w.trespass_of("intruder") == 1 and not w.is_built("lot")
    assert w.building_count() == 0


def test_build_on_unowned_land_refused():
    """Building on UNOWNED land is refused as ABSENCE: no owner -> neither bb_consume
    (needs builder-owns) nor bb_trespass (needs an owner) matches -> built stays 0."""
    w = _world()
    w.make_char("squatter", GOAL, coin=1000)
    w.add_buildable_plot("open", SITE, required=2, mat_cost=1, build_cost=100,
                         frontier=True)                  # unowned frontier
    w.set_construction_skill("squatter", 2)
    w.give_materials("squatter", timber=10, stone=10)
    w.build_tick("squatter", "open")
    assert not w.is_built("open") and w.trespass_of("squatter") == 0
    assert w.building_count() == 0


# ============================================= G-growth-loop (measure-first)
def test_growth_loop_raises_carrying_capacity():
    """MEASURE-FIRST: population growth -> housing demand -> BUILD -> the town's
    carrying capacity (housing units = building_count) rises ORGANICALLY. Three
    incoming households each build a house; the built stock grows 0 -> 3 (the physical
    form is emergent, not hand-placed)."""
    w = _world()
    sites = [(1, 1), (2, 1), (3, 1)]                    # open grass frontier row
    assert w.building_count() == 0
    for i, cell in enumerate(sites):
        name = "immigrant_%d" % i
        w.make_char(name, GOAL, coin=1000)
        w.add_buildable_plot("h%d" % i, cell, required=2, mat_cost=1, build_cost=50)
        w.own_plot(name, "h%d" % i)
        w.set_construction_skill(name, 2)
        w.give_materials(name, timber=10, stone=10)
        w.fund(name, "h%d" % i)
        assert w.build_until_done(name, "h%d" % i)
        assert w.building_count() == i + 1, "carrying capacity grows with each build"
    assert w.building_count() == 3


# ==================================================================== source-audit
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every construction DECISION is a seed rule, not Python. The adapter arms
    one-shots, ticks, reflects the `built` verdict into the host grid (the _apply_hop
    pattern), and reads -- it never COMPUTES a consume / raise / fund / loan / addon /
    expand / trespass outcome in Python."""
    import json
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_build_world.py")).read()
    world_src = re.sub(r"BUILD_PLOT_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    construct = json.load(open(os.path.join(_ROOT, "seeds", "bigville_build_construct.json")))
    mutate = json.load(open(os.path.join(_ROOT, "seeds", "bigville_build_mutate.json")))
    rule_names = {r["name"] for r in construct["rules"]} | {r["name"] for r in mutate["rules"]}
    assert rule_names == {
        "bb_loan", "bb_loan_accrue", "bb_fund", "bb_consume", "bb_raise",
        "bb_trespass", "bb_addon",
        "bbnav_wall_off", "bb_church_expand", "bb_demolish",
    }, "the ten construction decisions are RULES"
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # decision parameters appear ONLY in the seeds -- the adapter never BRANCHES on
    # them (it sets/reads them by name as opaque attrs).
    for param in ("funded", "trespass", "progress", "required", "expand", "blocked"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seeds_are_self_load_only_and_no_new_rust():
    """Discipline at the source level: both seeds are `self_load_only` (loaded ONLY
    by the R12 adapter -> cannot regress another suite); NO rule mints or destroys a
    Plot node (land stays R13-conserved -- construction only ADDS Building/BuildLoan
    nodes); no coin attr is set from a fractional Div; ZERO new Rust (checked at the
    repo level -- git diff runners/dsl empty)."""
    import json
    construct = json.load(open(os.path.join(_ROOT, "seeds", "bigville_build_construct.json")))
    mutate = json.load(open(os.path.join(_ROOT, "seeds", "bigville_build_mutate.json")))
    for s in (construct, mutate):
        assert s.get("self_load_only") is True, "%s must be self_load_only" % s["id"]
        for r in s["rules"]:
            for eff in r.get("effects", []):
                if eff[0] == "add_node":
                    assert eff[2] != "Plot", "no rule mints a Plot -- land stays conserved (R13)"
                if eff[0] == "del_node":
                    assert r["name"] == "bb_demolish", "only bb_demolish drops a node (a Building)"
                if eff[0] == "set_attr" and eff[2] in ("coin", "reserves", "balance"):
                    assert '"Div"' not in json.dumps(eff), \
                        "a coin/reserves attr must never be set from a fractional Div"
