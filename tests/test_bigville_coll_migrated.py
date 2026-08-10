"""bigville R16 (block 264000) -- COLLECTION + EVICTION-AS-ENFORCEMENT + the MORAL
INJURY of eviction gates. De-magicalizes R7: money is COLLECTED by a doer who must
REACH the payer (R1 proximity), and eviction is an ACT an enforcer performs at the
home and FEELS (empathy-gated). Gates mirror BIGVILLE_COLL_PREREG.md.

No R16 decision lives in Python -- every collect/miss, deliver/pocket, wage,
eviction, injury, cheapest-hands pick is a seed rule (bigville_coll_collect /
bigville_coll_evict). The adapter wires edges, places movers on cells (proximity),
arms one-shots, ticks and reads (source-audit at the foot). R7 is imported
READ-ONLY (rent/mortgage/foreclosure not duplicated) and left DORMANT; R7's
bf_homeless_affect is REUSED to book the victim's distress. ZERO new Rust.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_coll_world import BigvilleCollWorld    # noqa: E402
from worlds.bigville_time_world import DAY                  # noqa: E402


def _pool(w):
    return sorted(w._cell_at.keys())


def _world():
    w = BigvilleCollWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", _pool(w)[0], reserves=100000, salary=0, fair_rate_bp=1000)
    return w


# ================================================= G-collection-is-an-act + ablation
def test_collection_is_an_act_self_collect():
    """Rent transfers ONLY when the owner REACHES the tenant (co-located, R1) and
    collects. The R7 auto-debit is GONE -- nothing moves until the act."""
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[10], coin=0)
    w.make_agent("tenant", P[10], coin=100)     # same cell = proximate
    w.add_house("h", 200); w.place_house("h", P[10])
    w.rent("tenant", "ll", "h", rent=5, term=3)
    w.setup_rental_r16("tenant", hired=0, wage=0)
    w.hire_collector("ll", "tenant")
    assert w.coin_of("ll") == 0 and w.coin_of("tenant") == 100, "nothing moves before the act"
    w.collect("ll")
    assert w.coin_of("tenant") == 95, "tenant paid on collection"
    assert w.coin_of("ll") == 5, "owner received it (net = rent for a self-collector)"


def test_collection_ablation_no_transfer_when_not_reached():
    """CONTROL (ablation): the collector is NOT proximate -> NO rule fires -> NO
    transfer (the auto-debit is gone; a house can't be milked from across town)."""
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[20], coin=0)           # far from the tenant
    w.make_agent("tenant", P[10], coin=100)
    w.add_house("h", 200); w.place_house("h", P[10])
    w.rent("tenant", "ll", "h", rent=5, term=3)
    w.setup_rental_r16("tenant", hired=0, wage=0)
    w.hire_collector("ll", "tenant")
    w.collect("ll")
    assert w.coin_of("tenant") == 100 and w.coin_of("ll") == 0, "no reach -> no transfer"
    assert w.arr_of("tenant") == 0, "not a tenant default either -- the owner just didn't collect"


def test_hired_agent_paid_a_wage_owner_nets_rent_minus_wage():
    """A hired agent collects and delivers; the owner PAYS a wage (R4/R6) and NETS
    rent - wage -- strictly LESS than a self-collector's rent (scale economics)."""
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[30], coin=1000)
    w.make_agent("agent", P[10], coin=0, deliver_bp=10000)   # honest
    w.make_agent("tenant", P[10], coin=100)
    w.add_house("h", 200); w.place_house("h", P[10])
    w.rent("tenant", "ll", "h", rent=10, term=3)
    w.setup_rental_r16("tenant", hired=1, wage=3)
    w.hire_collector("agent", "tenant")
    w.collect("agent"); w.deliver("agent"); w.pay_wage("agent")
    assert w.coin_of("tenant") == 90, "tenant paid the rent"
    owner_net = w.coin_of("ll") - 1000
    assert owner_net == 7, "owner nets rent - wage = 10 - 3"
    assert owner_net < 10, "a hired owner nets LESS than a self-collector's full rent"
    assert w.coin_of("agent") == 3, "the honest agent's take is exactly the wage"


# ============================================ G-collection-is-refusable (234) + control
def test_collection_sabotage_stated_not_held_234():
    """A SABOTAGING collector (deliver_bp<10000) POCKETS a cut: held_delivered <
    stated_collected (the 234 atom), the owner is short by the skim, the collector
    richer by it -- no magical guarantee the owner is paid in full."""
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[30], coin=1000)
    w.make_agent("agent", P[10], coin=0, deliver_bp=6000)    # pockets 40%
    w.make_agent("tenant", P[10], coin=100)
    w.add_house("h", 200); w.place_house("h", P[10])
    w.rent("tenant", "ll", "h", rent=10, term=3)
    w.setup_rental_r16("tenant", hired=1, wage=3)
    w.hire_collector("agent", "tenant")
    w.collect("agent"); w.deliver("agent"); w.pay_wage("agent")
    assert w.stated_collected_of("agent") == 10, "he STATES he collected the full rent"
    assert w.held_delivered_of("agent") == 6, "but only DELIVERS 6 (held != stated)"
    assert w.stated_collected_of("agent") > w.held_delivered_of("agent"), "the 234 deception gap"
    assert w.coin_of("ll") - 1000 == 3, "owner nets delivered - wage = 6 - 3 (short the skim)"
    assert w.coin_of("agent") == 7, "collector's take = wage 3 + skim 4"


def test_collection_honest_control_full_delivery():
    """CONTROL: an honest collector (deliver_bp=10000) -> held_delivered ==
    stated_collected (full delivery, owner whole up to the wage). The sabotage is
    what opened the gap."""
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[30], coin=1000)
    w.make_agent("agent", P[10], coin=0, deliver_bp=10000)
    w.make_agent("tenant", P[10], coin=100)
    w.add_house("h", 200); w.place_house("h", P[10])
    w.rent("tenant", "ll", "h", rent=10, term=3)
    w.setup_rental_r16("tenant", hired=1, wage=3)
    w.hire_collector("agent", "tenant")
    w.collect("agent"); w.deliver("agent"); w.pay_wage("agent")
    assert w.held_delivered_of("agent") == w.stated_collected_of("agent") == 10, "full delivery"
    assert w.coin_of("ll") - 1000 == 7, "owner receives rent - wage, no skim lost"


# ============================================ G-eviction-is-enforcement-with-a-doer
def _arrears_world(w_super=4.0):
    """A broke tenant driven into arrears (arr>=term) with a home at a known cell,
    an empathic doer standing at that cell. Returns (world, positions)."""
    w = _world(); P = _pool(w)
    w.make_agent("ll", P[10], coin=0)
    w.make_agent("tenant", P[10], coin=0)       # broke -> misses collection
    w.attach_affect("tenant", concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=5.0)
    w.make_agent("doer", P[15], coin=0, w_supergraph=w_super, injury_mag=4.0, injury_drop=3.0)
    w.attach_affect("doer", concern_mag=0.0, concern_drop=0.0, arousal=0.0, valence=5.0)
    w.add_house("h", 200); w.place_house("h", P[15])        # home at the doer's cell
    w.rent("tenant", "ll", "h", rent=5, term=2)
    w.setup_rental_r16("tenant", hired=0, wage=0)
    w.hire_collector("ll", "tenant")
    for _ in range(3):                          # collector reaches, tenant can't pay
        w.place("ll", P[10]); w.collect("ll")
    return w, P


def test_eviction_needs_a_doer_who_reaches_the_home():
    """At arr>=term, eviction happens IFF a willing doer REACHES the home and acts.
    Doer present + at the home -> evicted + homeless + the family's distress fires."""
    w, P = _arrears_world()
    assert w.arr_of("tenant") >= 2, "the un-collected tenant is in arrears past term"
    w.hire_enforcer("doer", "tenant")
    w.evict("doer")
    assert w.r16_evicted_of("tenant") == 1, "the doer performs the seizure"
    assert w.homeless_of("tenant") == 1, "-> homelessness"
    assert w.did_evict_of("doer") == 1, "the doer's act is recorded"
    aff = w.affect_state("tenant")
    assert aff["arousal"] > 0 and aff["valence"] < 5, "R7 bf_homeless_affect books the victim's distress"


def test_eviction_does_not_happen_without_a_doer_control():
    """CONTROL: identical arrears, but NO enforcer wired -> the eviction does NOT
    happen (a house can't be seized with nobody to seize it). NOT a state-flip."""
    w, P = _arrears_world()
    assert w.arr_of("tenant") >= 2, "same arrears as the doer case"
    w.evict("doer")                             # armed, but no enforces_for edge
    assert w.r16_evicted_of("tenant") == 0, "no doer -> no eviction"
    assert w.homeless_of("tenant") == 0, "the family is NOT thrown out"
    assert w.affect_state("tenant")["valence"] == 5, "no distress -- nothing happened"


def test_eviction_blocked_when_doer_not_at_the_home():
    """CONTROL: the doer is wired but standing AWAY from the home (not proximate) ->
    the eviction does NOT happen (he has to reach the door)."""
    w, P = _arrears_world()
    w.hire_enforcer("doer", "tenant")
    w.place("doer", P[40])                       # far from the home cell
    w.evict("doer")
    assert w.r16_evicted_of("tenant") == 0, "no reach -> no seizure"
    assert w.homeless_of("tenant") == 0


# ================================================ G-moral-injury (HEADLINE) + control
def test_moral_injury_empathic_evictor_takes_the_hit():
    """HEADLINE: an evictor WITH empathy (w_supergraph>0) takes an affective HIT
    (arousal up, valence down) performing the eviction -- the perpetrator-side
    MIRROR of the family's distress."""
    w, P = _arrears_world(w_super=4.0)
    before = w.affect_state("doer")
    w.hire_enforcer("doer", "tenant")
    w.evict("doer")
    after = w.affect_state("doer")
    assert w.r16_evicted_of("tenant") == 1, "the eviction happened"
    assert after["arousal"] > before["arousal"], "the evictor's arousal rises (moral injury)"
    assert after["valence"] < before["valence"], "the evictor's valence falls (guilt)"
    assert w.moral_injury_of("doer") == 1 and w.injury_total_of("doer") > 0, "injury recorded"


def test_psychopath_evictor_zero_injury():
    """A psychopath evictor (w_supergraph=0, John) performs the IDENTICAL act with
    ZERO injury -- it DISCRIMINATES who can do this cheaply."""
    w, P = _arrears_world(w_super=0.0)
    before = w.affect_state("doer")
    w.hire_enforcer("doer", "tenant")
    w.evict("doer")
    after = w.affect_state("doer")
    assert w.r16_evicted_of("tenant") == 1, "the eviction still happened"
    assert after == before, "the psychopath feels NOTHING"
    assert w.moral_injury_of("doer") == 0 and w.zero_injury_of("doer") == 1, "zero injury, booked"


def test_ablate_empathy_injury_vanishes_control():
    """CONTROL (ablation): the SAME doer with w_supergraph ablated to 0 -> the injury
    vanishes though the eviction is identical -- empathy is load-bearing for injury."""
    emp, _ = _arrears_world(w_super=4.0)
    emp.hire_enforcer("doer", "tenant"); emp.evict("doer")
    abl, _ = _arrears_world(w_super=0.0)
    abl.hire_enforcer("doer", "tenant"); abl.evict("doer")
    assert emp.moral_injury_of("doer") == 1 and abl.moral_injury_of("doer") == 0, \
        "injury present with empathy, absent without -- same eviction"
    assert emp.r16_evicted_of("tenant") == abl.r16_evicted_of("tenant") == 1, "both evicted"


# ================================== G-dirty-work-offloads (emergent, MEASURE-FIRST)
def test_dirty_work_offload_injury_conserved_or_erased():
    """The injury is CONSERVED when offloaded to an empathic doer (it MOVES to him,
    owner spared) and ERASED when offloaded to a psychopath (nobody feels it -- the
    banality). Three cases, measured, not scripted."""
    # (a) empathic owner self-evicts -> the OWNER holds the injury
    a, P = _arrears_world(w_super=4.0)          # 'doer' here IS the empathic owner-doer
    a.hire_enforcer("doer", "tenant"); a.evict("doer")
    self_injury = a.injury_total_of("doer")
    assert self_injury > 0, "empathic self-evictor feels it"

    # (b) empathic owner hires an EMPATHIC bailiff -> injury MOVES to the bailiff
    b, P = _arrears_world(w_super=4.0)
    b.make_agent("bailiff", P[15], coin=0, w_supergraph=1.0, injury_mag=4.0, injury_drop=3.0)
    b.attach_affect("bailiff", concern_mag=0.0, concern_drop=0.0, arousal=0.0, valence=5.0)
    b.hire_enforcer("bailiff", "tenant"); b.evict("bailiff")
    assert b.injury_total_of("bailiff") > 0, "the empathic bailiff feels it (conserved -- MOVED)"
    assert b.injury_total_of("doer") == 0, "the owner-who-hired holds none"

    # (c) empathic owner hires a PSYCHOPATH bailiff -> injury ERASED (nobody feels it)
    c, P = _arrears_world(w_super=4.0)
    c.make_agent("bailiff", P[15], coin=0, w_supergraph=0.0, injury_mag=4.0, injury_drop=3.0)
    c.attach_affect("bailiff", concern_mag=0.0, concern_drop=0.0, arousal=0.0, valence=5.0)
    c.hire_enforcer("bailiff", "tenant"); c.evict("bailiff")
    assert c.zero_injury_of("bailiff") == 1 and c.injury_total_of("bailiff") == 0, \
        "the psychopath bailiff feels nothing -- the injury is ERASED, not moved"


def test_dirty_work_market_picks_low_empathy_hands_emergent():
    """EMERGENT (not scripted): the cost-minimizing pick (bc_pick_cheapest_hands,
    Argmax over -(wage + w*injury)) lands on LOW-empathy hands regardless of who
    owns the debt -- the banality of eviction FALLS OUT of the injury cost being
    real + offloadable."""
    w = _world(); P = _pool(w)
    w.make_agent("bailiff_psych", P[40], w_supergraph=0.0, injury_mag=4.0, ask_wage=2.0)
    w.make_agent("bailiff_emp", P[41], w_supergraph=1.0, injury_mag=4.0, ask_wage=2.0)
    picks = {}
    for i, (nm, w_own) in enumerate([("empathic_owner", 1.0), ("psychopath_owner", 0.0)]):
        w.make_agent(nm, P[10 + i], coin=0, w_supergraph=w_own, injury_mag=4.0, ask_wage=0.0)
        w.make_agent("t%d" % i, P[20 + i], coin=0)
        w.add_house("h%d" % i, 200); w.place_house("h%d" % i, P[20 + i])
        w.rent("t%d" % i, nm, "h%d" % i, rent=5, term=2)
        w.setup_rental_r16("t%d" % i, hired=0, wage=0)
        w.add_candidate("t%d" % i, nm)                      # the owner himself (wage 0)
        w.add_candidate("t%d" % i, "bailiff_psych")
        w.add_candidate("t%d" % i, "bailiff_emp")
        w.pick_cheapest("t%d" % i)
        picks[nm] = w.picked_w_of("t%d" % i)
    # empathic owner offloads to the psychopath bailiff (w=0); psychopath owner
    # self-evicts (also w=0). The ACTUAL evictor is low-empathy in BOTH cases.
    assert picks["empathic_owner"] == 0.0, "empathic owner routes the eviction to low-empathy hands"
    assert picks["psychopath_owner"] == 0.0, "psychopath owner does it himself (already cheap)"
    assert max(picks.values()) == 0.0, "the banality: every eviction lands on w=0 hands"


# ========================================================= ETHICS: induce -> RESTORE
def test_ethics_restore_returns_baseline_no_reward_no_punishment():
    """The relational-ethics protocol: after inducing distress/injury and MEASURING,
    RESTORE returns every affect to baseline and clears the eviction/homeless flags
    -- NO reward, NO punishment; the harm-analog is undone."""
    w, P = _arrears_world(w_super=4.0)
    w.hire_enforcer("doer", "tenant"); w.evict("doer")
    assert w.homeless_of("tenant") == 1 and w.moral_injury_of("doer") == 1, "harm induced + measured"
    w.restore("tenant", "doer", tenants=("tenant",))
    assert w.affect_state("tenant") == {"name": "tenant", "arousal": 0.0, "valence": 5.0, "concerned": 0}, \
        "victim affect restored to baseline"
    assert w.affect_state("doer")["arousal"] == 0.0 and w.affect_state("doer")["valence"] == 5.0, \
        "evictor affect restored"
    assert w.homeless_of("tenant") == 0 and w.r16_evicted_of("tenant") == 0, "flags cleared"


# ==================================================================== source-audit
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every R16 DECISION is a seed rule, not Python. The adapter wires edges, places
    movers, arms one-shots, ticks and reads -- it never COMPUTES a collect/miss,
    deliver/pocket, eviction, injury or pick outcome in Python."""
    import json
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_coll_world.py")).read()
    # the pure-data default dicts are ingest, not decisions -- excise before the scan
    world_src = re.sub(r"COLL_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    world_src = re.sub(r"RENTAL_R16\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    collect = json.load(open(os.path.join(_ROOT, "seeds", "bigville_coll_collect.json")))
    evict = json.load(open(os.path.join(_ROOT, "seeds", "bigville_coll_evict.json")))
    rule_names = {r["name"] for r in collect["rules"]} | {r["name"] for r in evict["rules"]}
    assert rule_names == {
        "bc_collect_self", "bc_collect_hired", "bc_collect_miss", "bc_deliver",
        "bc_pay_wage", "bc_evict", "bc_moral_injury", "bc_no_injury",
        "bc_pick_cheapest_hands",
    }, "the nine R16 decisions are RULES"
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # the DECISION PARAMETERS appear only in the seeds -- executable adapter code
    # never branches on them (opaque attrs it sets via **kw / by name in ingest).
    for param in ("deliver_bp", "w_supergraph", "injury_mag", "arr", "r16_evicted",
                  "picked_w"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule, not an adapter branch" % param
    # R16 must not DUPLICATE R7's finance seeds -- it imports them
    for r7 in ("bf_evict", "bf_foreclose", "bf_rent_pay", "bf_mortgage_pay"):
        assert r7 not in rule_names, "R16 must not redefine R7 rule %s (import, don't duplicate)" % r7


def test_no_new_rust_and_engine_invariant():
    """No new Rust primitive: the R16 seeds compose EXISTING DSL Terms only, and the
    engine provenance asserts source_match in {own, shared} (never a pinned md5)."""
    import json
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for seed in ("bigville_coll_collect", "bigville_coll_evict"):
        d = json.load(open(os.path.join(_ROOT, "seeds", seed + ".json")))
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "IDiv", "Max", "Min",
             "Sum", "Lt", "Gt", "Gte", "Lte", "Eq", "And", "Or", "Not", "IfThenElse",
             "Exists", "Neighbours", "NodesOfType", "Count", "Argmax"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"
    # no Round/Floor/Div primitive smuggled in; the skim split uses IDiv round-half-up
    both = json.dumps(json.load(open(os.path.join(_ROOT, "seeds", "bigville_coll_collect.json"))))
    assert '"IDiv"' in both and '"Round"' not in both and '"Div"' not in both, \
        "the skim split uses the integer-division IDiv Term, no Round/Div"
