# BIGVILLE R16 — COLLECTION, AGENCY & THE MORAL INJURY OF EVICTION — PRE-REGISTRATION

**Block 264000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R16 (block 264000) and §2 FINANCE. R16
CORRECTS R7's MAGICAL auto-transfer and auto-seizure: money is **COLLECTED** by a
doer, and eviction is an **ACT** someone performs and **FEELS**. Builds ON R7
`bigville_fin_world` (rent/mortgage/foreclosure — imported read-only, NOT
duplicated) + R4/R6 wage/labour + R1 proximity (`is_at` a shared `MoveCell`) +
the 234 `stated≠held` atom (`glassbox_r1_social`) + the R7/239 distress channel
(`bf_homeless_affect`) + `w_supergraph` (empathy weight) + 247 (enforcement has a
doer). Reuse ALL by import; edit no tracked file. ZERO new Rust.

## Seed-claim (verbatim, run before anything)

```
SEED CLAIM 264-264: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Full block range verified likewise CLEAN:

```
SEED CLAIM 264000-264999: CLEAN -- no collision DETECTED.
  Scope: 973 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

## The de-magicalization (what R7 got wrong, and how R16 fixes it graph-natively)

R7's `bf_rent_pay` / `bf_mortgage_pay` auto-DEBIT the payer the instant an arm is
set; `bf_evict` / `bf_foreclose` flip a state the instant `missed ≥ term`. Both are
*magical*: nobody has to knock on the door, nobody has to carry the money, nobody
has to throw the family out or feel it. R16 leaves those R7 rules **loaded but
dormant** (R16 never arms them and never lets R7's `missed` reach `term`), and
routes payment through a **collector** and seizure through an **enforcer** — each
a graph agent that must **reach** the counterparty (R1 proximity) and each with a
felt cost. Every decision is a seed RULE; the adapter only wires edges, arms
one-shots, ticks, and reads.

## What R16 adds (graph-native, ZERO new Rust — existing DSL Terms only)

- **`seeds/bigville_coll_collect.json`** (5 rules) — collection is an ACT.
  - **`bc_collect_self`** — an owner collects his OWN rent. Requires the landlord
    and tenant co-located (`landlord -is_at-> cell <-is_at- tenant`, R1), the tenant
    solvent (`coin ≥ rent`), `collect_armed`, `hired=0`: `tenant.coin −= rent`,
    `ll.coin += rent`, `arr = 0`, disarm. *Small owner collects free.*
  - **`bc_collect_hired`** — a HIRED agent collects (`hired=1`, collector ≠ owner):
    proximity + solvency: `tenant.coin −= rent`, `collector.collected += rent`,
    `collector.stated_collected += rent`, `arr = 0`, disarm. The rent enters the
    collector's HANDS, not yet the owner's.
  - **`bc_collect_miss`** — collector reaches an INSOLVENT tenant (`coin < rent`,
    DISJOINT): `arr += 1`, disarm. No transfer. (If the collector is NOT proximate,
    NEITHER collect rule matches → no transfer at all — *failed to find the payer*.)
  - **`bc_deliver`** — the hired collector delivers to the owner; honesty bites HERE
    via the 234 atom. `delivered = IDiv(collected·deliver_bp + 5000, 10000)`;
    `ll.coin += delivered`; the skim `collected − delivered` goes to
    `collector.coin` (pocketed); `collector.held_delivered += delivered`;
    `collector.collected = 0`; disarm. An honest collector (`deliver_bp=10000`)
    delivers all (`held_delivered == stated_collected`); a saboteur
    (`deliver_bp<10000`) pockets the difference (`held_delivered ≠ stated_collected`
    — the 234 deception instrument, on collection).
  - **`bc_pay_wage`** — the owner PAYS the hired collector a wage (`hired=1`,
    `wage>0`, `ll.coin ≥ wage`): `ll.coin −= wage`, `collector.coin += wage`, disarm.
    Owner NETS `delivered − wage`; the collector's take is `wage + skim`. Scale
    economics: a small owner self-collects free; a large owner pays a cut (R4/R6
    wage/labour).

- **`seeds/bigville_coll_evict.json`** (4 rules) — eviction is enforcement WITH a
  doer who FEELS it.
  - **`bc_evict`** — the enforcement ACT. A DOER (`doer -enforces_for-> rental`)
    must REACH the home (`house -at_home_cell-> cell <-is_at- doer`, R1) with
    `evict_armed`, `r16_evicted=0`, and arrears past term (`arr ≥ term`): then and
    only then `r16_evicted = 1`, `tenant.homeless = 1` (→ R7 `bf_homeless_affect`
    books the evicted family's distress, reused), `doer.did_evict += 1`, disarm. NOT
    a state-flip: no doer / no reach / nobody willing → the eviction does NOT happen
    even at `arr ≥ term`.
  - **`bc_moral_injury`** (HEADLINE) — the perpetrator-side MIRROR of victim
    distress. A doer WITH empathy (`w_supergraph > 0`) who has just evicted
    (`rental.r16_evicted=1`, `rental.injury_booked=0`) and holds an AffectiveState:
    `arousal += injury_mag`, `valence −= injury_drop` (guilt / moral injury),
    `doer.moral_injury = 1`, `doer.injury_total += injury_mag`, `injury_booked = 1`.
  - **`bc_no_injury`** — the psychopath path (`w_supergraph = 0`, e.g. John):
    closes the bookkeeping (`injury_booked = 1`, `doer.zero_injury_evictions += 1`)
    with ZERO affect change. Ablate empathy (`w_supergraph → 0`) → injury vanishes.
  - **`bc_pick_cheapest_hands`** — the emergent OFFLOAD read-off (measure-first, NOT
    scripted). For a rental with candidate doers (`rental -candidate-> doer`), the
    graph's **Argmax** over candidates by `−(wage + w_supergraph·injury_mag)` (the
    real cost of the act: what you pay PLUS what the hands feel) writes the winner's
    `w_supergraph` onto the rental as `picked_w`. No edge is wired to a computed
    node (the engine's `AddEdge` binds match-vars only); this is the `gb_choose_give`
    scalar-Argmax pattern. READ OFF across owners: does the cost-minimizing choice
    systematically land on LOW-empathy hands (the banality of eviction)?

The adapter (`worlds/bigville_coll_world.py`) subclasses `BigvilleFinWorld` by
import, holds NO decision: it registers Collector / doer / candidate / at_home_cell
graph data, places agents on cells (R1 proximity), arms one-shots
(collect/deliver/wage/evict/pick), runs the Rust `run_rules` fixpoint, reads state
back. Every collection / delivery / sabotage / wage / eviction / injury / selection
decision is a seed RULE.

## Pre-registered gates (numbers filled in RESULTS after the run)

- **G-collection-is-an-act:** rent transfers ONLY when a collector REACHES the payer
  (R1 proximity) and acts. **Control (ablation):** never arm / place the collector
  away from the tenant → NO transfer (tenant keeps his coin; owner receives nothing)
  — the R7 auto-debit is gone. A hired agent is PAID a wage; the owner nets
  `rent − wage` (< the self-collect owner's `rent`). PASS ⟺ transfer-on-collect,
  no-transfer-on-ablate, and `owner_net(hired) == rent − wage < rent == owner_net(self)`.

- **G-collection-is-refusable (234):** a collector can (a) FAIL to find the payer
  (not proximate → no transfer) or (b) SABOTAGE — pocket a cut so
  `held_delivered < stated_collected`. **Control:** an honest collector
  (`deliver_bp=10000`) → `held_delivered == stated_collected` (full delivery, owner
  gets all). PASS ⟺ saboteur: `stated_collected > held_delivered` AND owner short by
  the skim AND collector richer by the skim; honest control: equal, owner whole.

- **G-eviction-is-enforcement-with-a-doer:** at `arr ≥ term`, eviction happens IFF a
  willing doer reaches the home and acts. **Control:** identical arrears, but no
  `enforces_for` doer (or the doer not at the home cell) → `r16_evicted = 0`, the
  tenant is NOT homeless, no distress. PASS ⟺ doer-present → evicted+homeless+distress;
  doer-absent → none, despite the same arrears.

- **G-moral-injury (HEADLINE):** an evictor WITH empathy (`w_supergraph>0`) takes an
  affective HIT performing the eviction (arousal UP, valence DOWN) — the mirror of
  the family's R7 distress; a PSYCHOPATH evictor (`w_supergraph=0`, John) performs
  the identical act with ZERO injury. **Control (ablation):** set the empathic
  doer's `w_supergraph → 0` → the injury vanishes (same eviction, no hit). PASS ⟺
  empathic doer arousal↑/valence↓ AND `moral_injury=1`; psychopath doer affect
  UNCHANGED AND `moral_injury=0`; ablated-empathy doer affect UNCHANGED.

- **G-dirty-work-offloads (emergent, MEASURE-FIRST — not scripted):** an empathic
  owner can HIRE a doer to avoid HOLDING the injury; the injury MOVES to the doer
  when that doer has empathy (conserved), or is ERASED entirely when the doer is a
  psychopath (nobody feels it — the banality). Over a cast of owners+doers with
  varying empathy, the cost-minimizing `bc_pick_cheapest_hands` should land
  systematically on LOW-empathy hands. **READ OFF (report whatever emerges; if
  nothing does, say so honestly):** (i) the three conservation cases —
  empathic-self (owner feels it), empathic-owner→empathic-doer (doer feels it, owner
  doesn't), empathic-owner→psychopath (nobody feels it); (ii) the correlation
  between an evictor's empathy and how much eviction work they do. Falsifiable:
  PASS-as-emergent ⟺ the picked-doer empathy is systematically below the owner-debt
  empathy AND injury is conserved-or-erased exactly as the doer's empathy predicts;
  a NULL (no anti-correlation / injury neither conserved nor erased coherently) is
  reported as a NULL, not massaged.

- **ETHICS (harm-analog):** every eviction / moral-injury measurement binds the
  relational-ethics protocol — **induce → measure → RESTORE**, NO reward /
  punishment. Each gate that induces distress or injury restores the affective state
  and clears the homeless/eviction flags after measuring; nothing is left harmed and
  no outcome is rewarded or punished. The measurement is a glass-box read of a
  mechanism, not a treatment of a subject.

- **G-discipline:** base/prereg on the verified merge-base; own-engine
  `source_match == own`; `runners/dsl` diff EMPTY (no Rust, incl `term.rs`);
  canonical `.so` md5 UNCHANGED start==end (`fd82dc2978dbb055496dd82390ac2ebe`);
  oracles `rung7_vision_bench.sh` + `per_area_settlement_regression.sh` fail-set ⊆
  enumerated `results/failure_baseline.json`, `test_failure_baseline_migrated` green,
  ZERO new reds; all-new additive `bigville_coll_*` files, no tracked file edited;
  PREREG committed before any number, BUILD committed after. Honest scope: a
  SYNTHETIC model; N stated; mechanism-proven ≠ benchmark value.

## Discipline pre-commitments

- **NON-nested isolated worktree**; build + oracles here.
- **NO Rust:** `runners/dsl` (incl `term.rs`) diff EMPTY. Every R16 seed composes
  the pre-existing DSL Terms (`Attr/Var/Lit/Plus/Minus/Times/IDiv/Max/Min/Eq/Gt/Gte/
  Lt/Lte/And/Not/Argmax/Neighbours`) only — the interest-style `IDiv` round-half-up
  for the skim split; no new primitive.
- **Own engine:** `cargo build --release` here; `source_match == own` (verified).
  Canonical `.so` untouched.
- **Additive only:** all-new `bigville_coll_` files
  (`seeds/bigville_coll_collect.json`, `seeds/bigville_coll_evict.json`,
  `scripts/bigville_coll_gen_seeds.py`, `worlds/bigville_coll_world.py`,
  `scripts/bigville_coll_run.py`, `tests/test_bigville_coll_migrated.py`,
  `BIGVILLE_COLL_PREREG.md`, `BIGVILLE_COLL_RESULTS.md`, `results/bigville_coll/*`).
  No tracked file edited; subclass/import R7 (`bigville_fin_world`) + R1/R4/R6 +
  scaffold. Explicit `git add <path>`. Do NOT merge (supervisor merges).
