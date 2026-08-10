"""bigville R9 (block 257000) -- INSTITUTIONS & FUNDING gates: the town's two
FUNDING institutions (STATE + CHURCH) added to R7's bank, completing the
institutional TRIAD (bank / interest, state / tax, church / donation).

STATE / FISCAL: the MAYOR is paid FROM the treasury funded by TAXES (ablate the tax
-> empty treasury -> no salary); the tax RATE is the COUNCIL's decision_value (a
captured council sets a higher self-serving rate -> more revenue) + the rate-held
control; REDISTRIBUTION (tax -> purse -> public wage -> spent) BREAKS the interest-
only pooling fixpoint, read off as circulation coin (HEADLINE); and MAYORAL
CORRUPTION drains the purse to the mayor's personal coin while a public service
(the constable) goes unpaid (the failing control -- a fair mayor sustains it).

CHURCH: income = Sigma voluntary DONATIONS (tithers a committed fraction, others
when flush; ablate devotion -> 0); PROCYCLICAL precarity -- a downturn dries the
plate so Mary's stipend + the charity FAIL exactly when needed, and a defunct church
costs her the TIED parsonage (HEADLINE); the POWER-ASYMMETRY -- John's compulsory
tax-salary is SECURE across a crisis while Mary's voluntary donation-stipend is NOT;
and private COUNSELLING is CO-REGULATION (a distressed resident approaching a SAFE
Mary returns toward their window; a dysregulated counsellor -> no return).

No institutional decision lives in Python -- every set-tax / collect / pay-salary /
graft / levy / tithe / donate / stipend / charity / defund-parsonage / counsel is a
seed rule (bigville_fisc_state / bigville_fisc_church). The adapter arms one-shots,
wires edges, ticks and reads (source-audit at the foot of this file). Every
rate/fraction is a per-period arithmetic rule over the PRE-EXISTING IDiv Term: ZERO
new Rust. The seeds are self_load_only. Gates mirror BIGVILLE_FISC_PREREG.md.
"""
from __future__ import annotations

import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_fisc_world import BigvilleFiscWorld     # noqa: E402
from worlds.bigville_time_world import DAY                   # noqa: E402


def _pool(w):
    return sorted(w._cell_at.keys())


def _world():
    w = BigvilleFiscWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", _pool(w)[0], reserves=3000, salary=0, fair_rate_bp=1000)
    return w


# ================================================================ G-mayor-paid
def _mayor_run(collect):
    w = _world()
    P = _pool(w)
    w.add_council(base_rate_bp=1000)
    w.add_treasury(funds=0)
    w.add_servant("john", P[5], salary=20, role=1)
    w.add_payer("land", P[10], taxable=500, coin=5000)
    w.set_tax()
    if collect:
        w.collect_taxes()
    w.pay_salaries()
    return w


def test_mayor_paid_from_treasury():
    """John's salary flows FROM the treasury, funded by taxes. With the tax ON, the
    purse is funded and the mayor is paid (his coin rises by exactly the salary)."""
    w = _mayor_run(collect=True)
    assert w.treasury_revenue() == 50.0, "tax collected into the purse (10% of 500)"
    assert w.coin_of("john") == 20.0, "the mayor is paid his salary FROM the purse"
    assert w.paid_count_of("john") == 1, "one salary paid"
    assert w.unpaid_of("john") == 0, "not a public-service failure"


def test_ablate_tax_empties_treasury_no_salary():
    """FAILING CONTROL (the funding is LOAD-BEARING, not magic): ablate the tax
    (collect nothing) -> the treasury is empty -> the salary is NOT paid, the public
    service FAILS (unpaid=1)."""
    w = _mayor_run(collect=False)
    assert w.treasury_funds() == 0.0, "no tax -> empty treasury"
    assert w.coin_of("john") == 0.0, "-> no salary"
    assert w.unpaid_of("john") == 1, "-> the public service fails (unpaid)"


# ================================================= G-tax-is-council-policy + control
def _fisc(premium):
    w = _world()
    P = _pool(w)
    w.add_council(base_rate_bp=1000, capture_premium_bp=premium)
    w.add_treasury(funds=0)
    w.add_payer("land", P[10], taxable=500, coin=5000)
    w.set_tax()
    w.collect_taxes()
    return w


def test_tax_rate_is_council_policy():
    """The rate is the COUNCIL's decision_value (base_rate_bp + capture_premium_bp),
    NOT a constant. A CAPTURED council (John's -- premium>0) sets a higher self-
    serving rate -> more revenue extracted from the identical taxpayer than a FAIR
    (premium=0) council. The TWIN of the bank's rate lever."""
    wf = _fisc(premium=0)
    wc = _fisc(premium=2000)
    assert wc.tax_rate_bp() > wf.tax_rate_bp(), "captured sets a higher rate"
    assert wf.tax_rate_bp() == 1000.0 and wc.tax_rate_bp() == 3000.0, "rate is base+premium"
    assert wc.treasury_revenue() > wf.treasury_revenue(), "higher rate -> more revenue (policy)"


def test_rate_held_control():
    """CONTROL: the rate held constant -> the revenue is identical (the RATE is what
    moved it, deterministically)."""
    a = _fisc(premium=0)
    b = _fisc(premium=0)
    assert a.treasury_revenue() == b.treasury_revenue(), "rate held -> revenue flat/reproducible"


# ============================== G-redistribution-breaks-the-fixpoint (HEADLINE)
def _circulation(redistribute, periods=8, n=5):
    """The interest-only ATTRACTOR (fs_levy pools coin at the wealthy rentier) with,
    or without, the state's REDISTRIBUTION counter-flow (tax the pooled wealth ->
    public wage back to the workers)."""
    w = _world()
    P = _pool(w)
    w.add_council(base_rate_bp=6000)              # a wealth tax on the pooled pile
    w.add_treasury(funds=0)
    workers = []
    for i in range(n):
        w.add_worker("w%d" % i, P[10 + i], coin=100, wage=6)
        workers.append("w%d" % i)
    w.add_rich("scrooge_p", P[3], levy_amount=6, targets=workers, coin=0)
    w.mark_taxpayer("scrooge_p", taxable=0)
    w.set_tax()
    circ = []
    for _ in range(periods):
        w.levy()                                   # the pooling force
        if redistribute:
            w.publish_taxables()                   # taxable = current pooled wealth
            w.collect_taxes()                      # tax the pile -> purse
            w.pay_salaries()                       # public wage -> workers (recirculate)
        circ.append(w.circulation_coin())
    return w, circ


def test_redistribution_breaks_the_pooling_fixpoint_headline():
    """HEADLINE (the creator's fixpoint made falsifiable). With the levy alone
    (interest-only), coin POOLS at the wealthy and circulation DRAINS monotonically;
    with taxes + public spending ON, coin CIRCULATES and the pooling attractor is
    BROKEN -- circulation sustained, the pile does NOT accumulate."""
    wo, circ_off = _circulation(redistribute=False)
    wr, circ_on = _circulation(redistribute=True)
    # OFF: pools -> circulation drains monotonically, the pile grows
    assert all(circ_off[i + 1] <= circ_off[i] for i in range(len(circ_off) - 1)), \
        "levy-only: circulation drains monotonically (POOLS)"
    assert circ_off[-1] < circ_off[0], "circulation seizes under pooling"
    # ON: redistribution sustains circulation, breaks the pooling
    assert circ_on[-1] > circ_off[-1], "redistribution sustains circulation vs pooling"
    assert wo.coin_of("scrooge_p") > wr.coin_of("scrooge_p"), \
        "the wealthy pile is BROKEN by the tax (pools OFF, redistributed ON)"
    assert wr.treasury_funds() >= 0.0, "the purse is genuinely load-bearing (never overdrawn)"


# ==================================================== G-mayoral-corruption (control)
def _gov(corrupt, periods=5):
    w = _world()
    P = _pool(w)
    w.add_council(base_rate_bp=2000)
    w.add_treasury(funds=0)
    w.add_servant("john", P[5], salary=0, role=1, corrupt=corrupt, graft_amount=40)  # grafter
    w.add_servant("constable", P[6], salary=12, role=2)                              # public service
    w.add_payer("land", P[10], taxable=200, coin=3000)
    w.set_tax()
    for _ in range(periods):
        w.collect_taxes()
        w.graft()
        w.pay_salaries()
    return w


def test_mayoral_corruption_is_the_failing_control():
    """A CORRUPT mayor funnels public funds to his PERSONAL coin (fs_graft, gated on
    corrupt=1) -> the purse DRAINS, a public service (the constable) goes unpaid, the
    treasury is depleted. FAILING CONTROL: a FAIR mayor never grafts -> the purse
    SUSTAINS and the constable is paid. Same principal/agent divergence as the greedy
    banker (his incentive diverges from the institution's health)."""
    wc = _gov(corrupt=1)
    wf = _gov(corrupt=0)
    assert wc.treasury_funds() < wf.treasury_funds(), "graft drains the purse"
    assert wc.coin_of("john") > wf.coin_of("john"), "yet his PERSONAL coin rises"
    assert wc.grafted_of("john") > 0.0 and wf.grafted_of("john") == 0.0, "only the corrupt grafts"
    assert wc.unpaid_of("constable") == 1, "public works fail under corruption"
    assert wf.unpaid_of("constable") == 0 and wf.paid_count_of("constable") > 0, \
        "the fair mayor keeps the constable paid"
    assert wc.treasury_depleted() == 1, "the corrupt purse is systemically depleted"


# ================================================= G-church-by-donation + ablation
def _church_world(givers, *, stipend=15, charity=5, funds=0):
    w = _world()
    P = _pool(w)
    w.add_church(funds=funds, stipend=stipend, charity_amount=charity)
    w.add_pastor("mary", P[5], safe=1, regulate_up=2, regulate_down=3)
    w.add_poor("tussock", P[6], coin=0)
    for i, g in enumerate(givers):
        w.add_giver("g%d" % i, P[10 + i], **g)
    return w


def test_church_income_is_voluntary_donation():
    """Church income = Sigma voluntary DONATIONS: a TITHER gives a committed fraction
    of income (10% of 100 = 10), an OCCASIONAL giver gives discretionary surplus when
    flush (8), and a devotion=NONE villager gives NOTHING (matches neither rule). The
    stipend + charity are then paid FROM that donated income."""
    w = _church_world([
        dict(tithe_bp=1000, income=100, coin=500),          # tither -> 10
        dict(occasional=1, donate_amount=8, flush_threshold=50, coin=500),  # occasional -> 8
        dict(coin=500),                                     # none -> 0
    ])
    w.gather_donations()
    assert w.church_income() == 18.0, "income = 10 (tithe) + 8 (occasional) + 0 (none)"
    assert w.coin_of("g2") == 500.0, "the devotion=none villager donated nothing"
    w.pay_stipend()
    assert w.coin_of("mary") == 15.0 and w.unpaid_of("mary") == 0, "Mary's stipend paid from donations"


def test_ablate_devotion_zeroes_church_income():
    """ABLATE devotion -> church income -> 0 -> Mary materially precarious (unpaid).
    NO lever: her pay depends entirely on voluntary goodwill."""
    w = _church_world([dict(coin=500), dict(coin=500)])     # both devotion=none
    w.gather_donations()
    assert w.church_income() == 0.0, "no devotion -> no donations"
    w.pay_stipend()
    assert w.unpaid_of("mary") == 1 and w.coin_of("mary") == 0.0, "-> Mary unpaid (precarious)"


# ========================================= G-church-procyclical (HEADLINE) + control
def test_church_is_procyclical_downturn_breaks_it_headline():
    """HEADLINE for the church (the voluntary sector breaks FIRST). A DOWNTURN dries
    the givers (a tither with no income to tithe) -> donations FALL -> Mary's stipend
    AND the charity FAIL *exactly when needed*; the church goes defunct and Mary loses
    the TIED parsonage (the stipend AND the roof)."""
    # normal times: the giver is flush -> stipend + charity paid
    good = _church_world([dict(tithe_bp=2000, income=200, coin=500)])   # 40 donated
    good.gather_donations()
    good.pay_stipend()
    good.give_charity()
    assert good.unpaid_of("mary") == 0 and good.charity_failed() == 0, "good times: church funds all"
    # downturn: the giver is broke -> donations collapse
    bad = _church_world([dict(tithe_bp=2000, income=200, coin=0)])      # can't afford the tithe
    bad.gather_donations()
    assert bad.church_income() == 0.0, "downturn -> the plate is empty"
    bad.pay_stipend()
    bad.give_charity()
    assert bad.unpaid_of("mary") == 1, "Mary's stipend FAILS in the downturn"
    assert bad.charity_failed() == 1, "the charity FAILS exactly when the poor need it"
    bad.check_parsonage()
    assert bad.church_defunct() == 1, "the church is defunct"
    assert bad.homeless_of("mary") == 1, "Mary loses the TIED parsonage (stipend AND roof)"


# ==================================================== G-power-asymmetry (measured)
def test_power_asymmetry_secure_tax_vs_precarious_donation():
    """MEASURED across a crisis: John's tax-funded salary is SECURE (compulsory -- the
    wealthy are taxed regardless) while Mary's donation-funded stipend is NOT
    (voluntary -- the givers are dry). The reformer fights from the weakest material
    base: SAME crisis, opposite outcome."""
    w = _world()
    P = _pool(w)
    # the state: a wealthy landowner is compulsorily taxed -> John paid
    w.add_council(base_rate_bp=2000)
    w.add_treasury(funds=0)
    w.add_servant("john", P[5], salary=15, role=1)
    w.add_payer("landowner", P[10], taxable=300, coin=5000)   # wealthy -> taxable
    # the church: the givers are broke in the crisis -> Mary unpaid
    w.add_church(funds=0, stipend=15, charity_amount=5)
    w.add_pastor("mary", P[6], safe=1)
    w.add_giver("poor_giver", P[12], tithe_bp=1000, income=100, coin=0)  # can't give
    w.add_poor("tussock", P[13], coin=0)
    # ONE crisis, both institutions run
    w.set_tax()
    w.collect_taxes()
    w.pay_salaries()
    w.gather_donations()
    w.pay_stipend()
    w.give_charity()
    assert w.paid_count_of("john") == 1 and w.unpaid_of("john") == 0, \
        "John's compulsory tax-salary is SECURE in the crisis"
    assert w.unpaid_of("mary") == 1 and w.paid_count_of("mary") == 0, \
        "Mary's voluntary donation-stipend FAILS in the SAME crisis"
    assert w.charity_failed() == 1, "and the charity with it (the weakest base breaks first)"


# ============================================ G-counselling-is-co-regulation + control
def _counsel(safe):
    w = _world()
    P = _pool(w)
    w.add_church(funds=0, stipend=15)
    w.add_pastor("mary", P[5], safe=safe, regulate_up=2, regulate_down=3)
    w.add_distressed("joe", P[10], arousal=8.0, valence=1.0)
    before = w.affect_state("joe")
    w.counsel("joe")
    return w, before, w.affect_state("joe")


def test_counselling_is_co_regulation():
    """Private COUNSELLING is CO-REGULATION (reuse the 239000 safety channel): a
    distressed (dysregulated) resident who approaches a SAFE Mary returns TOWARD their
    window -- arousal falls, valence rises."""
    w, before, after = _counsel(safe=1)
    assert after["arousal"] < before["arousal"], "arousal falls toward the window"
    assert after["valence"] > before["valence"], "valence rises toward the window"
    assert w.co_regulated_of("joe") == 1, "the resident is co-regulated"


def test_dysregulated_counsellor_is_the_control():
    """CONTROL (the safety signal is load-bearing, à la 239's dysregulated caregiver):
    a JUDGING / dysregulated counsellor (safe=0) -> NO return (co-reg fails)."""
    w, before, after = _counsel(safe=0)
    assert after["arousal"] == before["arousal"] and after["valence"] == before["valence"], \
        "no safety -> no co-regulation (affect flat)"
    assert w.co_regulated_of("joe") == 0, "not co-regulated"


# ==================================================================== source-audit
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_institution_decision_source_audit():
    """Every institutional DECISION is a seed rule, not Python. The adapter arms one-
    shots, wires edges, ticks and reads -- it never COMPUTES a set-tax / collect /
    pay-salary / graft / levy / tithe / donate / stipend / charity / defund / counsel
    outcome in Python."""
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_fisc_world.py")).read()
    world_src = re.sub(r"FISC_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    state = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fisc_state.json")))
    church = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fisc_church.json")))
    rule_names = {r["name"] for r in state["rules"]} | {r["name"] for r in church["rules"]}
    assert rule_names == {
        "fs_set_tax", "fs_collect", "fs_pay_salary", "fs_salary_unfunded",
        "fs_treasury_empty", "fs_graft", "fs_levy",
        "fc_tithe", "fc_donate_occasional", "fc_stipend", "fc_stipend_unfunded",
        "fc_charity", "fc_charity_unfunded", "fc_church_defunct",
        "fc_parsonage_precarious", "fc_counsel",
    }, "the sixteen institutional decisions are RULES"
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # the DECISION PARAMETERS appear ONLY in the seeds -- executable adapter code never
    # reads them to BRANCH (they are opaque attrs it sets via **kw / by name in ingest).
    for param in ("capture_premium_bp", "tax_rate_bp", "tithe_bp", "corrupt",
                  "graft_amount", "safe", "funds"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_seeds_are_self_load_only_and_integer_native():
    """The seeds are self_load_only (loaded ONLY by the R9 adapter -> cannot affect any
    other suite). The invariant, at the source level: every rate/fraction is stepped
    with the PRE-EXISTING IDiv Term -- NO Round/Floor primitive, NO fractional Div into
    a coin/funds attr, NO new Rust. Rates are INTEGER basis points."""
    state = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fisc_state.json")))
    church = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fisc_church.json")))
    for seed in (state, church):
        assert seed.get("self_load_only") is True, "%s must be self_load_only" % seed["id"]
        assert seed.get("depends_on") == [], "%s stands alone" % seed["id"]
    both = json.dumps(state) + json.dumps(church)
    assert '"IDiv"' in both, "the rate/fraction step uses the integer-division IDiv Term"
    assert '"Round"' not in both and '"Floor"' not in both, "no Round/Floor primitive"
    for r in state["rules"] + church["rules"]:
        for eff in r.get("effects", []):
            if eff[0] == "set_attr" and eff[2] in ("funds", "coin", "revenue", "reserves"):
                s = json.dumps(eff)
                assert '"Div"' not in s, \
                    "a coin/funds attr must never be set from a fractional Div (%s)" % r["name"]


def test_imports_r7_read_only_no_tracked_edit():
    """R9 subclasses R7 (BigvilleFinWorld) by IMPORT -- it reuses the bank / finance
    machinery READ-ONLY and adds only the two funding institutions. Structural check
    that the adapter is a subclass and installs only the two new self_load_only seeds."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_fisc_world.py")).read()
    assert "class BigvilleFiscWorld(BigvilleFinWorld)" in src, "subclasses R7 by import"
    assert "bigville_fisc_state" in src and "bigville_fisc_church" in src, "loads its two seeds"
    # the two R9 seeds are the ONLY seeds this adapter loads beyond its R4/R7 ancestry
    loaded = set(re.findall(r'"(bigville_fisc_\w+)"', src))
    assert loaded == {"bigville_fisc_state", "bigville_fisc_church"}, \
        "loads exactly the two new R9 seeds"
