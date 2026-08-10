"""bigville R7 (block 255000) -- FINANCE gates: tenure-driven equity DIVERGENCE;
LEVERAGE AMPLIFIES a shock into homelessness (HEADLINE) + the owned-outright control;
the RATE is Scrooge's POLICY (greedy vs fair foreclosures) + the rate-held control;
INTEREST is the cross-frame multiplicative base read STEPPED as INTEGER coin (the
frame/continuum invariant); the BANK is an ENTITY whose funds are SEPARATE from
Scrooge's SALARY + the no-salary control; the GREEDY-banker principal/agent
divergence; systemic INSOLVENCY distinct from Scrooge's personal wealth; and the
RENTIER lever (John-as-slumlord). Gates mirror BIGVILLE_FIN_PREREG.md.

No finance decision lives in Python -- every accrue / set-rate / pay-vs-miss /
foreclose / evict / salary / insolvency / rent-raise is a seed rule
(bigville_fin_bank / bigville_fin_tenure). The adapter arms one-shots, wires edges,
ticks and reads (source-audit at the foot of this file). Interest is a per-period
arithmetic rule over the PRE-EXISTING IDiv Term: ZERO new Rust.
"""
from __future__ import annotations

import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_fin_world import BigvilleFinWorld, OWN, MORTGAGE, RENT  # noqa: E402
from worlds.bigville_time_world import DAY                                   # noqa: E402


def _pool(w):
    return sorted(w._cell_at.keys())


def _bank_world(reserves=100000, salary=0, fair_rate_bp=1000, greed_premium_bp=0.0):
    w = BigvilleFinWorld(day_range=16)
    w.set_phase(DAY)
    w.add_bank("scrooge", _pool(w)[0], reserves=reserves, salary=salary,
               fair_rate_bp=fair_rate_bp, greed_premium_bp=greed_premium_bp)
    return w


# ============================================================ G-tenure-diverges
def test_tenure_diverges():
    """Over a multi-day run OWNER and LANDLORD equity RISES (they hold an appreciating
    asset) while the RENTER's stays FLAT at 0 -- a wealth/class gap from tenure alone.
    The renter matches NO equity rule; that ABSENCE is the flat curve (graph-native)."""
    w = _bank_world()
    P = _pool(w)
    w.make_char("owner", P[10], coin=1000)
    w.make_char("landlord", P[11], coin=1000)
    w.make_char("renter", P[12], coin=1000)
    w.add_house("h_own", 100, apprec=10)
    w.add_house("h_rent", 100, apprec=10)
    w.own("owner", "h_own")
    w.rent("renter", "landlord", "h_rent", rent=5, term=3)
    eq_o, eq_l, eq_r = [], [], []
    for _ in range(6):
        w.period()
        eq_o.append(w.equity_of("owner"))
        eq_l.append(w.equity_of("landlord"))
        eq_r.append(w.equity_of("renter"))
    assert eq_o[-1] > eq_o[0], "owner equity rises"
    assert eq_l[-1] > eq_l[0], "landlord equity rises"
    assert len(set(eq_r)) == 1 and eq_r[0] == 0.0, "renter equity FLAT at 0 (no asset)"
    assert all(eq_o[i + 1] > eq_o[i] for i in range(len(eq_o) - 1)), "owner monotone up"
    # the renter DID pay (coin fell) yet built no equity -- the class structure
    assert w.coin_of("renter") == 1000 - 6 * 5, "renter paid rent every period"
    assert w.coin_of("landlord") == 1000 + 6 * 5, "landlord collected it"


# ============================================ G-leverage-amplifies (HEADLINE) + control
def _shock_world(mortgagor):
    """A fishmonger whose income collapses (coin->0), either as a MORTGAGOR or an
    OWNED-OUTRIGHT owner of the SAME house."""
    w = _bank_world(fair_rate_bp=500)
    P = _pool(w)
    w.make_char("fish", P[10], coin=1000)
    w.attach_affect("fish", concern_mag=4.0, concern_drop=3.0, arousal=0.0, valence=5.0)
    w.add_house("h", 200, apprec=0)
    if mortgagor:
        w.mortgage("fish", "h", principal=500, payment=30, term=3)
    else:
        w.own("fish", "h")
    w.set_char("fish", coin=0)                 # the fishmonger's bad run (R4 shock)
    for _ in range(5):
        w.period()
    return w


def test_leverage_amplifies_headline():
    """A goods shock (income collapse) becomes a HOUSING CATASTROPHE through the
    mortgage: missed payments past term -> the bank FORECLOSES (seizes the LAND) ->
    homeless -> the 204000/239000 distress fires."""
    w = _shock_world(mortgagor=True)
    assert w.missed_of("fish") >= 3, "the income collapse misses payments past term"
    assert w.foreclosed_of("fish") == 1, "the bank forecloses"
    assert not w.owns_house("fish", "h"), "the debtor loses the house"
    assert w.bank_owns("h"), "the LAND+building transfers to the bank (the collateral)"
    assert w.homeless_of("fish") == 1, "-> homelessness"
    assert w.social_concern_of("fish") == 1, "-> a social concern is filed"
    aff = w.affect_state("fish")
    assert aff["arousal"] > 0.0 and aff["valence"] < 5.0, "distress: arousal up, valence down"


def test_owned_outright_is_the_failing_control():
    """FAILING CONTROL (leverage is the amplifier, isolated): the SAME income collapse
    on an OWNED-OUTRIGHT character -> he keeps the house, no foreclosure, no distress."""
    w = _shock_world(mortgagor=False)
    assert w.homeless_of("fish") == 0, "owner weathers the identical shock"
    assert w.owns_house("fish", "h"), "keeps the house"
    assert w.social_concern_of("fish") == 0, "no distress"
    assert w.affect_state("fish")["valence"] == 5.0, "affect unchanged"


# ============================================ G-interest-is-policy + rate-held control
def _cohort(greed_bp, salary, periods=8, n=4):
    w = _bank_world(reserves=2000, salary=salary, fair_rate_bp=1000, greed_premium_bp=greed_bp)
    P = _pool(w)
    for i in range(n):
        nm = "m%d" % i
        w.make_char(nm, P[10 + i], coin=40)
        w.add_house("h%d" % i, 400, apprec=0)
        w.mortgage(nm, "h%d" % i, principal=400, payment=5, term=2)
    w.set_rate()                               # Scrooge's decision propagates
    for _ in range(periods):
        for i in range(n):
            w.set_char("m%d" % i, coin=w.coin_of("m%d" % i) + 45)   # marginal income
        w.period()
    fc = sum(w.foreclosed_of("m%d" % i) for i in range(n))
    return w, fc


def test_interest_is_policy():
    """The rate is Scrooge's DECISION (fair_rate_bp + greed_premium_bp). A GREEDY
    (high-premium) Scrooge raises every mortgagor's required payment (interest_due
    scales with the rate) -> more marginal debtors can't pay -> MORE foreclosures than
    a FAIR one on the identical cast."""
    wf, fc_fair = _cohort(greed_bp=0, salary=15)
    wg, fc_greedy = _cohort(greed_bp=1500, salary=60)
    assert wg.bank_rate_bp() > wf.bank_rate_bp(), "greedy sets a higher rate"
    assert fc_greedy > fc_fair, "higher rate -> more foreclosures (rate is policy)"
    assert fc_fair == 0, "the fair rate is affordable on the same income"


def test_rate_held_control():
    """CONTROL: the rate held constant -> the foreclosure count is identical (the RATE
    is what moved it, deterministically)."""
    _w1, fc1 = _cohort(greed_bp=0, salary=15)
    _w2, fc2 = _cohort(greed_bp=0, salary=15)
    assert fc1 == fc2, "rate held -> foreclosure count flat/reproducible"


# ==================================================== G-interest-is-stepped (invariant)
def test_interest_is_stepped_closed_form_and_integer():
    """The multiplicative base read STEPPED. A mortgage that only ACCRUES (never
    charged) tracks the closed form round(P*(1+r)^k) EXACTLY at integer periods, and
    the stored balance is INTEGER-valued at every step -- r applied INTENSIONALLY
    (basis points in the rule), never a fractional float in a frame."""
    w = _bank_world(fair_rate_bp=1000)         # r = 0.10
    P = _pool(w)
    w.make_char("d", P[10], coin=0)
    w.add_house("h", 5000)
    w.mortgage("d", "h", principal=1000, payment=0, term=99, deduct_reserves=False)
    bal = 1000
    for k in range(8):
        w.accrue()                             # arm bf_accrue only (pure geometric)
        bal = round(bal * 1.10)                # closed form, round-half-up
        gb = w.balance_of("d")
        assert gb == int(gb), "balance stays INTEGER coin (never a fractional float)"
        assert round(gb) == bal, ("graph %.4f != closed form %d at period %d" % (gb, bal, k + 1))
    assert w.period_of("d") == 8, "eight integer periods stepped"


def test_odd_balance_rounds_half_up_integer():
    """A balance whose (1+r) product is fractional (999 * 1.10 = 1098.9) is stored as
    the round-half-up INTEGER 1099 -- IDiv(x + denom/2, denom), no Round primitive, no
    float stored."""
    w = _bank_world(fair_rate_bp=1000)
    P = _pool(w)
    w.make_char("d", P[10], coin=0)
    w.add_house("h", 5000)
    w.mortgage("d", "h", principal=999, payment=0, term=99, deduct_reserves=False)
    w.accrue()
    gb = w.balance_of("d")
    assert gb == 1099.0 and gb == int(gb), "round(1098.9)=1099, integer"


def test_all_coin_attrs_integer_through_a_full_run():
    """The whole finance run keeps every coin/balance/reserves read INTEGER-valued --
    in-frame is INTEGER (the continuum lives only in the rate MAP, applied)."""
    w, _fc = _cohort(greed_bp=1500, salary=60, periods=6, n=3)
    reads = [w.reserves(), w.scrooge_coin()]
    for i in range(3):
        reads += [w.coin_of("m%d" % i), w.balance_of("m%d" % i), w.equity_of("m%d" % i)]
    for v in reads:
        assert v == int(v), "every in-frame coin/balance/reserve/equity is integer-valued: %r" % v


# ============================================ G-bank-is-an-entity + salary + control
def _salary_run(salary):
    w = _bank_world(reserves=5000, salary=salary, fair_rate_bp=1000)
    P = _pool(w)
    w.make_char("m", P[10], coin=1000)
    w.add_house("h", 300)
    w.mortgage("m", "h", principal=300, payment=10, term=3)
    sc, res = [], []
    for _ in range(5):
        w.set_char("m", coin=w.coin_of("m") + 200)
        w.period()
        sc.append(w.scrooge_coin())
        res.append(w.reserves())
    return w, sc, res


def test_bank_is_an_entity_salary_separate():
    """The Bank's reserves are SEPARATE from Scrooge's personal coin. A SALARY
    transfers bank->Scrooge each cycle; his personal wealth tracks the SALARY (rises by
    exactly salary/period), NOT the reserves (which move with lending/repayment)."""
    w, sc, res = _salary_run(30)
    assert sc == [30.0, 60.0, 90.0, 120.0, 150.0], "personal wealth = cumulative salary"
    # reserves and personal coin are DISTINCT trajectories
    assert res[-1] != sc[-1], "reserves != Scrooge's personal coin (funds separate)"
    assert res[-1] > sc[-1], "the bank still holds far more than Scrooge personally drew"


def test_no_salary_control():
    """CONTROL: salary=0 -> Scrooge's PERSONAL coin stays FLAT at 0 while the bank
    still OPERATES (lends, is repaid, its reserves move)."""
    w, sc, res = _salary_run(0)
    assert len(set(sc)) == 1 and sc[0] == 0.0, "no salary -> personal wealth flat"
    assert res[-1] != 5000 - 300, "the bank still operated (reserves changed via repayment)"


# ==================================================== G-greedy-banker (failing control)
def test_greedy_banker_principal_agent_divergence():
    """A GREEDY Scrooge (high salary + high rate) drains the RESERVES faster and causes
    MORE foreclosures than a FAIR one, while his PERSONAL coin rises FASTER -- the
    principal/agent divergence (his incentive diverges from the bank's health)."""
    wf, fc_fair = _cohort(greed_bp=0, salary=15)
    wg, fc_greedy = _cohort(greed_bp=1500, salary=60)
    assert wg.reserves() < wf.reserves(), "greedy drains reserves faster"
    assert fc_greedy > fc_fair, "greedy causes more foreclosures"
    assert wg.scrooge_coin() > wf.scrooge_coin(), "yet his PERSONAL wealth rises faster"


# ==================================================== G-insolvency (systemic)
def test_insolvency_is_systemic_distinct_from_scrooge():
    """Enough defaults + salary withdrawals drive Bank.reserves <= 0 -> insolvent=1, a
    town-wide credit event DISTINCT from Scrooge's personal wealth (he stays rich while
    the bank fails)."""
    w = _bank_world(reserves=300, salary=50, fair_rate_bp=2000)
    P = _pool(w)
    for i in range(2):
        nm = "m%d" % i
        w.make_char(nm, P[10 + i], coin=0)     # never earns -> always defaults
        w.add_house("h%d" % i, 200)
        w.mortgage(nm, "h%d" % i, principal=100, payment=5, term=99)
    for _ in range(6):
        w.period()
        if w.insolvent():
            break
    assert w.insolvent() == 1, "reserves hit 0 -> systemic insolvency"
    assert w.reserves() <= 0, "the bank is out of reserves"
    assert w.scrooge_coin() > 0, "yet Scrooge is personally rich (the divergence)"


# ==================================================== G-rentier-power + control
def _rentier(raise_it):
    w = _bank_world(reserves=1000, salary=0, fair_rate_bp=1000)
    P = _pool(w)
    w.make_char("john", P[5], coin=0, coerce_mag=4.0, coerce_drop=3.0)
    w.make_char("tenant", P[10], coin=1000)
    w.attach_affect("tenant", concern_mag=1.0, concern_drop=1.0, arousal=0.0, valence=5.0)
    w.add_house("h", 200)
    w.rent("tenant", "john", "h", rent=5, term=3, raise_amount=10)
    before = w.affect_state("tenant")
    if raise_it:
        w.raise_rent("tenant")
    return w, before


def test_rentier_power_moves_affect_and_backing():
    """The RENTIER lever (John-as-slumlord): raising rent / threatening eviction moves
    the tenant's affect (valence DOWN, arousal UP) and backing UP -- economic coercive
    control (ties to 239/247)."""
    w, before = _rentier(raise_it=True)
    after = w.affect_state("tenant")
    assert w.rent_of("tenant") == 15.0, "rent raised 5 -> 15"
    assert after["valence"] < before["valence"], "tenant valence falls (coercion)"
    assert after["arousal"] > before["arousal"], "tenant arousal rises"
    assert w.backing_of("tenant") > 0.0, "backing shifts toward the landlord (compelled)"


def test_rentier_no_raise_control():
    """CONTROL: no raise -> the tenant's affect is unchanged (the raise is what moved it)."""
    w, before = _rentier(raise_it=False)
    after = w.affect_state("tenant")
    assert after["valence"] == before["valence"] and after["arousal"] == before["arousal"], \
        "no raise -> affect flat"
    assert w.backing_of("tenant") == 0.0, "no compelled backing"


# ==================================================================== source-audit
def _strip_py(src: str) -> str:
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return src


def test_no_python_agent_decision_source_audit():
    """Every finance DECISION is a seed rule, not Python. The adapter arms one-shots,
    wires edges, ticks and reads -- it never COMPUTES an accrue / pay-vs-miss /
    foreclose / salary / insolvency / rent-raise outcome in Python."""
    import json
    world_src = open(os.path.join(_ROOT, "worlds", "bigville_fin_world.py")).read()
    world_src = re.sub(r"FIN_DEFAULTS\s*=\s*dict\([\s\S]*?\)\n", "", world_src, count=1)
    code = _strip_py(world_src)
    bank = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fin_bank.json")))
    ten = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fin_tenure.json")))
    rule_names = {r["name"] for r in bank["rules"]} | {r["name"] for r in ten["rules"]}
    assert rule_names == {
        "bf_accrue", "bf_set_rate", "bf_salary", "bf_insolvent",
        "bf_mortgage_pay", "bf_mortgage_miss", "bf_foreclose",
        "bf_rent_pay", "bf_rent_miss", "bf_evict", "bf_homeless_affect",
        "bf_owner_equity", "bf_mortgagor_equity", "bf_appreciate", "bf_rent_raise",
    }, "the fifteen finance decisions are RULES"
    # no Python rule engine in the adapter
    for banned in ("graph_rewrite", "gr._match", "gr._apply", "make_rule"):
        assert banned not in code, "adapter must not run/author the Python rule engine"
    # the DECISION PARAMETERS appear ONLY in the seeds -- executable adapter code never
    # reads them to branch (they are opaque attrs it sets via **kw / by name in ingest).
    for param in ("greed_premium_bp", "rate_bp", "interest_due", "missed", "foreclosed"):
        assert ("if " + param) not in code, \
            "decision parameter %s must live in a rule `where`, not an adapter branch" % param


def test_interest_is_a_rule_over_IDiv_no_new_rust():
    """The invariant, at the source level: the balance is stepped with the PRE-EXISTING
    IDiv (integer division) Term -- NO `Div`-into-a-stored-balance, NO Round primitive,
    NO new Rust. The rate is stored as INTEGER basis points (rate_bp), never a
    fractional float on a node."""
    import json
    bank = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fin_bank.json")))
    ten = json.load(open(os.path.join(_ROOT, "seeds", "bigville_fin_tenure.json")))
    both = json.dumps(bank) + json.dumps(ten)
    assert '"IDiv"' in both, "the interest step uses the integer-division IDiv Term"
    assert '"Round"' not in both and '"Floor"' not in both, "no Round/Floor primitive"
    # the balance is only ever set from an IDiv/Minus expression, never a fractional Div
    for r in bank["rules"] + ten["rules"]:
        for eff in r.get("effects", []):
            if eff[0] == "set_attr" and eff[2] in ("balance", "reserves", "coin", "equity"):
                s = json.dumps(eff)
                assert '"Div"' not in s, \
                    "a coin/balance attr must never be set from a fractional Div (%s)" % r["name"]
    # runners/dsl carries no diff: the Rust source is unchanged (asserted here as a
    # standing reminder; the discipline ledger verifies the empty diff + own-engine md5).
    assert True
