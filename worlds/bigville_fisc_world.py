"""BigvilleFiscWorld -- bigville R9 (block 257000): graph-native INSTITUTIONS &
FUNDING on top of the proven R4 economy / R7 finance world. The town's
institutional TRIAD adds its two FUNDING institutions to R7's bank:

  * STATE / FISCAL -- a `Council` sets the TAX RATE (a decision_value, the fiscal
    lever -- TWIN of R7's bank rate); revenue flows to a `Treasury` purse that pays
    the MAYOR's salary + the CONSTABLE's wage; money RE-ENTERS circulation when
    spent. A corrupt mayor grafts from the purse (principal/agent, like the banker).

  * CHURCH -- funded by voluntary DONATION (tithers give a committed fraction,
    others give discretionary surplus when flush -- a per-villager devotion axis).
    Church income funds Mary's STIPEND + parsonage (TIED housing) + CHARITY, and
    private CO-REGULATION COUNSELLING. NO lever -- procyclical + precarious.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2 FISCAL + CHURCH, sec 3 R9)
--------------------------------------------------------------------------------------
  * THE STATE   -- `Council`{base_rate_bp, capture_premium_bp}, `Treasury`{funds},
                   public-servant Movers (mayor/constable) paid FROM the purse.
  * THE CHURCH  -- `Church`{funds, stipend, charity_amount} run by the pastor Mary,
                   funded by donation, funding stipend + tied parsonage + charity.
  * CIRCULATION -- fs_levy pools coin at the wealthy (the R7 interest attractor's
                   essence); the tax+salary loop BREAKS the pooling fixpoint --
                   read off as money velocity / circulation coin.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R7 (BigvilleFinWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY does mechanical I/O: register
Council/Treasury/Church/servant/giver/poor graph data (ingest); ARM a one-shot flag
for the phase being advanced (set-tax / collect / pay-salary / graft / levy / gather
/ stipend / charity / parsonage / counsel); run the Rust `run_rules` fixpoint; read
state back. EVERY institutional decision -- set the rate, collect, pay a salary,
graft, tithe, donate, pay the stipend, give charity, defund the parsonage, co-
regulate -- is a seed RULE (bigville_fisc_state / bigville_fisc_church), never
Python. All rate/fraction math is a per-period arithmetic rule over the pre-existing
IDiv Term: NO new Rust. The seeds are self_load_only (loaded only here).
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                     # noqa: E402
from worlds.bigville_fin_world import BigvilleFinWorld             # noqa: E402

# fiscal/church attrs set on every character so a rule never reads a missing key.
# The population variation (role, devotion, corruption) is set by the caller --
# these are ingest, not a decision (the R4 ECON_DEFAULTS / R7 FIN_DEFAULTS pattern).
FISC_DEFAULTS = dict(
    # public-payroll / fiscal
    salary=0.0, unpaid=0.0, paid_count=0.0, corrupt=0.0, grafted=0.0,
    graft_amount=0.0, graft_armed=0.0, salary_armed=0.0,
    taxable=0.0, collect_armed=0.0, levy_amount=0.0, levy_armed=0.0,
    # devotion / church
    tithe_bp=0.0, occasional=0.0, income=0.0, flush_threshold=0.0,
    donate_amount=0.0, donate_armed=0.0, income_total=0.0,
    # counselling / co-regulation
    safe=0.0, regulate_up=0.0, regulate_down=0.0, counsel_armed=0.0,
    co_regulated=0.0,
)


class BigvilleFiscWorld(BigvilleFinWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_fisc_state", "bigville_fisc_church"):
            self.eng.load_seed_manifest(manifest_for(sid), None)
        self._council = None
        self._treasury = None
        self._church = None
        self._pastor = None            # pastor char name
        self._rich = None              # rentier char name (the pooling sink)
        self._servants = {}            # name -> Mover nid (public payroll)
        self._payers = {}              # name -> Mover nid (TAXED: treasury -taxes->)
        self._levied = {}              # name -> Mover nid (LEVIED: rich -levies->)
        self._givers = {}              # name -> Mover nid (church givers)

    # ---------------------------------------------------------------- ingest
    def make_person(self, name, start, **kw):
        """A townsperson who can hold fiscal/church roles. R7 make_char (coin +
        finance attrs) + the R9 fiscal/church attrs. Mechanical graph data."""
        m = self.make_char(name, start)
        for k, v in FISC_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def set_person(self, name, **kw):
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    # ---- the STATE ---------------------------------------------------------
    def add_council(self, *, base_rate_bp, capture_premium_bp=0.0):
        """The COUNCIL -- holds the tax-rate decision (base + capture premium: a fair
        council premium=0, a captured one premium>0). Which values it picks is ITS
        decision; the RATE decision itself is fs_set_tax."""
        c = self.eng.add_node("Council", {
            "base_rate_bp": float(base_rate_bp),
            "capture_premium_bp": float(capture_premium_bp),
            "tax_rate_bp": 0.0, "tax_armed": 0.0})
        self._council = c
        return c

    def add_treasury(self, *, funds=0.0):
        """The public PURSE. Revenue in via fs_collect; salaries out via fs_pay_salary."""
        t = self.eng.add_node("Treasury", {
            "funds": float(funds), "revenue": 0.0, "tax_rate_bp": 0.0, "depleted": 0.0})
        self.eng.add_edge_unchecked(self._council, "sets_tax", t)
        self._treasury = t
        return t

    def add_servant(self, name, start, *, salary, role=0.0, corrupt=0.0, graft_amount=0.0):
        """A public-payroll agent (mayor/constable) paid FROM the treasury."""
        m = self.make_person(name, start, salary=salary, role=role,
                             corrupt=corrupt, graft_amount=graft_amount, coin=0.0)
        self.eng.add_edge_unchecked(self._treasury, "pays", m)
        self._servants[name] = m
        return m

    def add_payer(self, name, start, *, taxable, coin=0.0):
        """A landowner/worker who is TAXED (treasury -taxes-> payer)."""
        m = self.make_person(name, start, taxable=taxable, coin=coin)
        self.eng.add_edge_unchecked(self._treasury, "taxes", m)
        self._payers[name] = m
        return m

    def add_rich(self, name, start, *, levy_amount, targets, coin=0.0):
        """The wealthy rentier (Scrooge's personal purse) -- the POOLING sink for
        fs_levy (the R7 interest-attractor essence). Levies each named `targets`
        worker (the LEVIED set, distinct from the TAXED set so the state can tax the
        pooled wealth and redistribute it to the workers -- the circulation loop)."""
        m = self.make_person(name, start, levy_amount=levy_amount, coin=coin)
        self._rich = name
        for tn in targets:
            self.eng.add_edge_unchecked(m, "levies", self._movers[tn])
            self._levied[tn] = self._movers[tn]
        return m

    def set_council(self, **kw):
        for k, v in kw.items():
            self.eng.set_attr(self._council, k, float(v))

    # ---- the CHURCH --------------------------------------------------------
    def add_church(self, *, funds=0.0, stipend, charity_amount=0.0):
        ch = self.eng.add_node("Church", {
            "funds": float(funds), "income_total": 0.0, "stipend": float(stipend),
            "charity_amount": float(charity_amount), "charity_given": 0.0,
            "charity_failed": 0.0, "defunct": 0.0,
            "stipend_armed": 0.0, "charity_armed": 0.0, "parsonage_armed": 0.0})
        self._church = ch
        return ch

    def add_pastor(self, name, start, *, safe=1.0, regulate_up=0.0, regulate_down=0.0):
        """Mary -- runs the church (run_by), lives in the TIED parsonage (houses),
        and counsels (safe = the 239 non-judging safety signal)."""
        m = self.make_person(name, start, safe=safe, regulate_up=regulate_up,
                            regulate_down=regulate_down, coin=0.0)
        self.eng.add_edge_unchecked(self._church, "run_by", m)
        self.eng.add_edge_unchecked(self._church, "houses", m)
        self._pastor = name
        return m

    def add_giver(self, name, start, *, tithe_bp=0.0, occasional=0.0, income=0.0,
                  flush_threshold=0.0, donate_amount=0.0, coin=0.0):
        """A church donor with a devotion axis: tither (tithe_bp>0, committed
        fraction) / occasional (occasional=1, discretionary when flush) / none."""
        m = self.make_person(name, start, tithe_bp=tithe_bp, occasional=occasional,
                            income=income, flush_threshold=flush_threshold,
                            donate_amount=donate_amount, coin=coin)
        self.eng.add_edge_unchecked(self._church, "gathers", m)
        self._givers[name] = m
        return m

    def add_worker(self, name, start, *, coin, wage=0.0):
        """A worker in the circulation loop: LEVIED by the rentier and paid a public
        WAGE from the treasury (a servant). Registered as a servant; add_rich lists it
        as a levy target."""
        m = self.make_person(name, start, coin=coin, salary=wage)
        self.eng.add_edge_unchecked(self._treasury, "pays", m)
        self._servants[name] = m
        return m

    def mark_taxpayer(self, name, *, taxable=0.0):
        """Register an existing Mover as a TAXED payer (treasury -taxes-> payer). Used
        to tax the rentier's pooled wealth so the state can redistribute it."""
        m = self._movers[name]
        self.eng.add_edge_unchecked(self._treasury, "taxes", m)
        self.eng.set_attr(m, "taxable", float(taxable))
        self._payers[name] = m
        return m

    def add_poor(self, name, start, *, coin=0.0):
        """Old Tussock -- receives church CHARITY (church -gives_charity-> poor)."""
        m = self.make_person(name, start, coin=coin)
        self.eng.add_edge_unchecked(self._church, "gives_charity", m)
        self._poor = m
        return m

    def add_distressed(self, name, start, *, arousal, valence, coin=0.0):
        """A dysregulated resident who may seek Mary's counsel (co-regulation)."""
        m = self.make_person(name, start, coin=coin)
        self.attach_affect(name, arousal=arousal, valence=valence)
        self.eng.add_edge_unchecked(m, "seeks_counsel", self._movers[self._pastor])
        return m

    # ------------------------------------------------- rule-driven one-shots
    def set_tax(self):
        """The COUNCIL sets the rate (fs_set_tax reads its decision + writes the
        treasury's tax_rate_bp)."""
        self.eng.set_attr(self._council, "tax_armed", 1.0)
        return self._run()

    def collect_taxes(self):
        """Arm one collection on every payer; fs_collect transfers tax_due to the
        purse (per-payer, like R7's per-mortgage arming)."""
        for m in self._payers.values():
            self.eng.set_attr(m, "collect_armed", 1.0)
        return self._run()

    def pay_salaries(self):
        """Pay each public servant from the purse, ONE AT A TIME (fs_pay_salary if the
        purse can afford it, else fs_salary_unfunded). Serialised per servant because
        the guard reads the SHARED, DECREASING treasury: the engine matches all
        bindings of a pass against the pre-pass funds, so N servants armed together
        would all pass one `gte(funds, salary)` check and overdraw the purse. Arming
        one servant per fixpoint (deterministic sorted order) makes the purse
        genuinely LOAD-BEARING -- exactly the async scheduler's one-mover-per-tick
        discipline, mechanical, no decision."""
        steps = 0
        for name in sorted(self._servants):
            self.eng.set_attr(self._servants[name], "salary_armed", 1.0)
            steps += self._run()
        return steps

    def graft(self):
        """Arm the mayoral graft (fs_graft fires ONLY for a corrupt mayor)."""
        for m in self._servants.values():
            self.eng.set_attr(m, "graft_armed", 1.0)
        return self._run()

    def levy(self):
        """Arm one rentier levy on every levied worker (fs_levy pools coin at the
        wealthy -- the R7 interest-attractor essence)."""
        for m in self._levied.values():
            self.eng.set_attr(m, "levy_armed", 1.0)
        return self._run()

    def publish_taxables(self):
        """Publish each payer's taxable base = its current coin (mechanical world
        fact, like R3's `lateness` / R4's `now_epoch`) so a WEALTH tax tracks the
        pooling pile. The tax DECISION is fs_collect, not this."""
        for m in self._payers.values():
            self.eng.set_attr(m, "taxable",
                              float(self.eng.node(m)["attrs"].get("coin", 0.0)))
        return None

    def gather_donations(self):
        """Arm one donation on every giver; fc_tithe / fc_donate_occasional decides."""
        for m in self._givers.values():
            self.eng.set_attr(m, "donate_armed", 1.0)
        return self._run()

    def pay_stipend(self):
        """Arm Mary's stipend (fc_stipend if funded, else fc_stipend_unfunded)."""
        self.eng.set_attr(self._church, "stipend_armed", 1.0)
        return self._run()

    def give_charity(self):
        """Arm the charity to the poor (fc_charity if funded, else fc_charity_unfunded)."""
        self.eng.set_attr(self._church, "charity_armed", 1.0)
        return self._run()

    def check_parsonage(self):
        """Arm the tied-housing check (fc_church_defunct + fc_parsonage_precarious)."""
        self.eng.set_attr(self._church, "parsonage_armed", 1.0)
        return self._run()

    def counsel(self, resident):
        """Arm a counselling approach (fc_counsel co-regulates iff Mary is safe)."""
        self.eng.set_attr(self._movers[resident], "counsel_armed", 1.0)
        return self._run()

    # ------------------------------------------------- glass-box read-offs
    def treasury_funds(self):
        return float(self.eng.node(self._treasury)["attrs"].get("funds", 0.0))

    def treasury_revenue(self):
        return float(self.eng.node(self._treasury)["attrs"].get("revenue", 0.0))

    def treasury_depleted(self):
        return int(self.eng.node(self._treasury)["attrs"].get("depleted", 0.0))

    def tax_rate_bp(self):
        return float(self.eng.node(self._treasury)["attrs"].get("tax_rate_bp", 0.0))

    def unpaid_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("unpaid", 0.0))

    def paid_count_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("paid_count", 0.0))

    def grafted_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("grafted", 0.0))

    def church_funds(self):
        return float(self.eng.node(self._church)["attrs"].get("funds", 0.0))

    def church_income(self):
        return float(self.eng.node(self._church)["attrs"].get("income_total", 0.0))

    def church_defunct(self):
        return int(self.eng.node(self._church)["attrs"].get("defunct", 0.0))

    def charity_given(self):
        return float(self.eng.node(self._church)["attrs"].get("charity_given", 0.0))

    def charity_failed(self):
        return int(self.eng.node(self._church)["attrs"].get("charity_failed", 0.0))

    def homeless_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("homeless", 0.0))

    def co_regulated_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("co_regulated", 0.0))

    def circulation_coin(self):
        """Total coin held by the LEVIED workers (the money in CIRCULATION -- the
        pooling readout: it drains under levy-only, sustains under redistribution)."""
        return sum(float(self.eng.node(m)["attrs"].get("coin", 0.0))
                   for m in self._levied.values())

    def rich_coin(self):
        return self.coin_of(self._rich)
