# BIGVILLE R16 — COLLECTION, AGENCY & THE MORAL INJURY OF EVICTION — RESULTS

**Block 264000.** Measured AFTER the prereg (`BIGVILLE_COLL_PREREG.md`) was
committed. All numbers are read straight off the graph by
`scripts/bigville_coll_run.py` → `results/bigville_coll/summary.json`; the gates are
`tests/test_bigville_coll_migrated.py` (**16/16 green**). Engine `source_match ==
own`; `runners/dsl` diff EMPTY (no Rust); canonical `.so` md5 unchanged. A SYNTHETIC
glass-box model — mechanism-proven, N small and stated; not a benchmark number.

## What R16 fixed about R7

R7's payment auto-DEBITED the payer and its foreclosure/eviction FLIPPED a state the
instant `missed ≥ term`. R16 leaves those R7 rules **loaded but dormant** (never
armed; R7's `missed` never reaches `term`) and routes payment through a **collector**
(who must REACH the payer, R1) and seizure through an **enforcer** (who must reach the
home and FEELS it). Nine rules, all graph-native, ZERO new Rust. R7's
`bf_homeless_affect` is REUSED verbatim to book the evicted family's distress.

## Gate results (all PASS)

### G-collection-is-an-act ✓
Rent moves ONLY on the act. Self-collector co-located with the tenant:
`(owner, tenant) coin (0, 100) → (5, 95)`. **Ablation** — owner NOT proximate:
`owner 0, tenant 100` (**no transfer**; the R7 auto-debit is gone, and it is NOT a
tenant default — the owner simply didn't collect). A hired agent is paid a wage and
the owner nets `rent − wage`: rent 10, wage 3 → **owner_net = 7 < 10** (a
self-collector's full rent). Scale economics land exactly as specified.

### G-collection-is-refusable (234) ✓
| collector | deliver_bp | stated_collected | held_delivered | owner_net | collector_take |
|---|---|---|---|---|---|
| honest | 10000 | 10 | 10 | 7 | 3 (wage only) |
| **saboteur** | 6000 | **10** | **6** | **3** | **7** (wage 3 + skim 4) |

The saboteur's `stated_collected (10) > held_delivered (6)` — the **234 `stated≠held`
atom on collection**. The owner is short by the skim; the collector is richer by it.
The honest control closes the gap (full delivery). No magical guarantee the owner is
paid. The skim split is `IDiv(collected·deliver_bp + 5000, 10000)` — round-half-up on
integers via the pre-existing R7 interest Term, no `Round`/`Div` primitive.

### G-eviction-is-enforcement-with-a-doer ✓
Identical arrears (`arr = 3 ≥ term = 2`) in every arm.
- Doer wired + at the home cell → `r16_evicted = 1`, `homeless = 1`, the family's
  distress fires (victim valence `5 → 2`, arousal `0 → 4` via R7 `bf_homeless_affect`).
- **Control — no enforcer wired** → `r16_evicted = 0`, `homeless = 0`, victim valence
  unchanged (**5**). A house can't be seized with nobody to seize it.
- **Control — doer wired but standing away from the home** (not proximate) →
  `r16_evicted = 0`. He has to reach the door. Eviction is NOT a state-flip.

### G-moral-injury (HEADLINE) ✓ — the perpetrator-side mirror
The SAME eviction, two evictors:
| evictor | w_supergraph | valence | arousal | moral_injury |
|---|---|---|---|---|
| **empathic** | 4.0 | **5 → 2** | **0 → 4** | **1** |
| **psychopath** (John) | 0.0 | 5 → 5 | 0 → 0 | 0 |

The empathic evictor takes an affective HIT (guilt / moral injury) — the exact mirror
of the family's `valence 5→2, arousal 0→4` distress. The psychopath performs the
identical act and feels **nothing** (`zero_injury_evictions = 1`). **Ablation** —
drop the empathic doer's `w_supergraph → 0` and the injury vanishes though the
eviction is byte-identical. Empathy is load-bearing for injury and DISCRIMINATES who
can do this cheaply.

### G-dirty-work-offloads (emergent, MEASURE-FIRST) — the finding
The injury cost is real (Gate 4) AND offloadable. Measuring the three conservation
cases plus the emergent market pick:

**Conservation:** who ends up holding the injury when an empathic owner offloads?
| case | who feels it | injury_total |
|---|---|---|
| empathic owner **self-evicts** | the owner | **4** |
| empathic owner **hires an empathic bailiff** | the bailiff (owner: 0) | **4 → MOVED** (conserved) |
| empathic owner **hires a psychopath bailiff** | **nobody** | **0 → ERASED** |

The sharp, dark result: injury is **conserved (MOVES to the doer) only when the doer
has empathy; hiring a psychopath ERASES it entirely** — nobody in the system feels
the eviction. "Conserved not erased" (the spec's phrasing) holds **only** for an
empathic doer; the psychopath case is strict erasure. This is *the banality of
eviction* at its coldest.

**Emergent market pick** (`bc_pick_cheapest_hands` — the graph's Argmax over candidate
doers by `−(ask_wage + w_supergraph·injury_mag)`, NOT scripted): the cost-minimizing
choice, where cost legitimately includes what the hands FEEL.
| owner | owner empathy | picked evictor empathy | picked wage |
|---|---|---|---|
| empathic_owner | 1.0 | **0.0** (offloads to a psychopath bailiff) | 2 |
| psychopath_owner | 0.0 | **0.0** (self-evicts; already cheap) | 0 |

**In BOTH cases the actual evictor has `w_supergraph = 0`.** The empathic owner routes
the dirty work to low-empathy hands to escape the injury; the psychopath owner does it
himself because it costs him nothing. **The empathy of the evictor is systematically
below the empathy of the debt-holder — the banality of eviction FALLS OUT of the
injury cost being real + offloadable.** Not scripted: it is the Argmax of a cost that
merely counts the felt injury as part of the price.

Honest scope of the emergent claim: the offload objective is a MODEL — it prices the
act as `wage + w·injury_mag`, so a cost-minimizer necessarily prefers low-`w` hands.
The claim is not "we discovered agents avoid guilt" but "when the felt injury is a
real, priced, offloadable cost (Gate 4 measured it is), the market equilibrium routes
harm to those who feel it least, and that follows mechanically." A NULL would have
been `picked_w` insensitive to `w` — it is not (it tracks the min-cost hands).

### ETHICS — induce → measure → RESTORE ✓
Every eviction/injury gate binds the relational-ethics protocol. After inducing
(`homeless = 1`, `moral_injury = 1`, doer valence `5 → 2`) and MEASURING, `restore`
returns both affects to baseline (`tenant {arousal 0, valence 5}`, `doer valence 5`)
and clears the flags (`homeless = 0`, `r16_evicted = 0`). **NO reward, NO punishment**
— the harm-analog is undone; the measurement is a glass-box read of a mechanism, not a
treatment of a subject.

## Discipline ledger

- **Base / merge-base:** `81f6e5b2e614ca76a492c84f427de64ea257ae4b` (the R16 SPEC
  commit; R16 IMPLEMENTATION is this branch).
- **Prereg committed BEFORE any number:** `BIGVILLE_COLL_PREREG.md` (commit 1).
- **Seed-claim:** `264-264` and `264000-264999` both CLEAN.
- **No Rust:** `git diff <base> -- runners/dsl` EMPTY (incl `term.rs`). Every seed
  composes existing DSL Terms (`Attr/Var/Lit/Plus/Minus/Times/IDiv/Eq/Gt/Gte/Lt/And/
  Not/Argmax/Neighbours`).
- **Own engine:** built here (`cargo build --release`), `source_match == own`.
- **Canonical `.so`:** `fd82dc2978dbb055496dd82390ac2ebe` UNCHANGED start == end (never
  committed).
- **Oracles:** `rung7_vision_bench.sh` and `per_area_settlement_regression.sh` fail-set
  ⊆ enumerated `results/failure_baseline.json` (ZERO NEW reds);
  `test_failure_baseline_migrated` 11/11.
- **Gates:** `test_bigville_coll_migrated` **16/16**; source-audit asserts the nine R16
  decisions are RULES, the adapter never branches on a decision parameter, and R16 does
  NOT duplicate R7's `bf_evict/bf_foreclose/bf_rent_pay/bf_mortgage_pay`.
- **Additive only:** all-new `bigville_coll_*` files; no tracked file edited (R7
  imported read-only).

## Honest residuals

- **Collection is demonstrated on RENT (landlord/agent).** Mortgage collection (bank
  as owner, Scrooge or a hired agent) uses the identical structure but is not
  separately instantiated — the mechanism is proven on the rent path; the mortgage
  path is a wiring of the same rules and is left for the next rung.
- **The offload objective is a model, not a discovery** (see the emergent-claim scope
  above): low-`w` selection follows from pricing the felt injury. The measured content
  is the *conservation-vs-erasure asymmetry* (empathic doer conserves, psychopath
  erases) and the *systematic low-empathy evictor*, both read off, not scripted.
- **`bc_pick_cheapest_hands` selects a SCALAR, not an edge.** The engine's `AddEdge`
  binds match-vars only, so the pick writes the winning doer's empathy to `picked_w`
  (the `gb_choose_give` pattern); the ACTUAL eviction is then run with an explicitly
  wired doer to show the injury lands. A full "select-then-wire-then-evict" in one
  fixpoint would need an edge-to-computed-node effect the DSL does not currently expose
  (noted, NOT built — that would be Rust).
- **N is small and synthetic** (2 owners, 2 bailiffs in the market pick; single
  tenancies elsewhere). Mechanism-proven ≠ population result; a powered many-agent
  sweep of the empathy-vs-evictor-role correlation is the natural follow-on.
- **Injury is a fixed magnitude per doer** (`injury_mag`), not yet modulated by
  relationship, repetition (habituation / moral callousing), or the victim's
  visibility — all natural extensions the current single-shot gate does not probe.
