# BIGVILLE R12 — CONSTRUCTION + the MUTABLE WORLD — RESULTS

**Block 260000. Landed.** Pre-registration: `BIGVILLE_BUILD_PREREG.md` (committed BEFORE
any measured number). Spec §2.8 + §3 R12. Builds ON R13 land / R7 finance, imported
READ-ONLY. ZERO new Rust; canonical `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe`
UNCHANGED; own-engine provenance `source_match = shared`.

## Gate results — `tests/test_bigville_build_migrated.py` — **16/16 GREEN**

| Gate | Test(s) | Result |
|---|---|---|
| build needs materials+skill+time | `test_build_consumes_materials_skill_time` + 3 ablations | PASS — skill=2/required=6 → 3 ticks, 6 timber+stone consumed, `Building` minted; each of materials / skill / time ablated → NO build |
| financed (personal vs loan) | `test_personal_funding`, `test_loan_funded_build_accrues` | PASS — savings drop (personal); loan → reserves drop + builder coin up, balance 100 → 110 at 10% (accrues like a mortgage) |
| — control (no funds, no loan) | `test_no_funds_no_loan_no_build_control` | PASS — funded 0 → no build |
| **MUTABLE WORLD (headline)** | `test_build_reroutes_nav_and_updates_occlusion` | PASS — build on the office-door chokepoint SEALS nav (resident trapped) + BREAKS Mary's line-of-sight; demolish REVERTS both |
| church expands if funded | `test_church_expands_when_funded` | PASS — donations → capacity+size grow, funds drop |
| — control (unfunded) | `test_church_no_expand_unfunded_control` | PASS — funds < cost → no expansion |
| modify / add-on | `test_addon_extends_building` | PASS — extend → size+capacity grow, materials consumed |
| trespass refused | `test_build_on_others_land_is_trespass`, `test_build_on_unowned_land_refused` | PASS — non-owner → trespass flag, not built; unowned → refused as absence |
| growth-loop (measure-first) | `test_growth_loop_raises_carrying_capacity` | PASS — 3 households build → capacity 0 → 3 |
| source-audit / discipline | `test_no_python_agent_decision_source_audit`, `test_seeds_are_self_load_only_and_no_new_rust` | PASS — 10 decisions are rules; self_load_only; no Plot minted; no new Rust |

Baseline `test_failure_baseline_migrated` **11/11**; provenance `test_engine_provenance_migrated`
**7/7** (`source_match = shared`).

## Glass-box findings

- **Build on OWNED land; trespass refused.** `bb_consume`/`bb_raise` match `[builder, owns,
  plot]`, so construction needs the R13 plot. A non-owner arming a build gets a `trespass`
  flag and no building; UNOWNED land matches neither the build nor the trespass rule and is
  refused as absence. The R13 precondition is enforced at the source, not by a Python `if`.
- **Personal vs loan funding, both grounded.** Personal: `build_cost` leaves the builder's own
  coin. Loan: `bb_loan` moves coin from the R7 bank's reserves to the builder and mints a
  `BuildLoan`; `bb_loan_accrue` grows the balance multiplicatively (`IDiv(balance·(10000+
  rate_bp), 10000)` — integer coin), exactly the `bf_accrue` mortgage step. A no-savings
  builder can only build by borrowing, and then carries the interest — the leverage that turns
  a boom into a bust.
- **Modify / add-on.** `bb_addon` consumes further materials and grows a building's `size` +
  `capacity` — a durable modification distinct from a fresh build.
- **Institutional expansion, income-gated.** `bb_church_expand` grows the church's capacity iff
  its (donation-fed) funds cover the cost — a grounded lift of R9's fixed size; underfunded → no
  growth. Soft-power capacity is now EARNED and mutable.
- **THE MUTABLE WORLD (headline).** `bb_raise` marks the built plot's map cell `blocked` +
  `occludes` — a RULE mutating the persistent map-belief. `bbnav_wall_off` then severs that
  cell's walkable adjacency, so the existing `bigville_move_nav` Bellman flood RE-ROUTES around
  the building by construction; the adapter reflects the `built` verdict into the host grid so
  the occlusion query (`can_see`) re-queries the mutated map. Measured on the office-door
  chokepoint: a resident who reached the square and a pastor who saw into the office are, after
  one house rises on the door, respectively SEALED IN and BLINDED — and demolition reverts both.
  Nav and perception re-query the changed world exactly as movement already re-queries.

## Growth-loop measurement — `scripts/bigville_build_run.py` → `results/bigville_build/summary.json`

- **SUSTAINED arm (6 households, personal funding):** carrying capacity (built housing units)
  rises 0 → 1 → 2 → 3 → 4 → 5 → 6 organically; coin conserved (6000 held, 300 spent on
  construction, 5700 remaining). The town's physical form is EMERGENT, not hand-placed.
- **BOOM/BUST arm (4 speculators, debt-financed, 20% rate):** the stock booms to 4; total debt
  400 → **93 664** after 30 accrual periods with no income; all builders underwater (coin 0 <
  debt) → structural default. The R7 interest-fixpoint at the construction level — a natural
  PUNCTUATION (R10). Reported as a FINDING, not tuned away.

## Honest residuals

- The growth loop is demonstrated at **small N on the fixed scaffold town** — NOT swept toward
  the 200 north-star. Immigration/birth inflow (R11/R14), the carrying-capacity BALANCE against
  consumption (R5), and a full boom→bust→**recovery** time-series are deferred to the
  integrative capstone (R10). This rung gates the MECHANISM (build / fund / mutate / expand),
  not the macro dynamics.
- The mutable-world demonstration uses ONE chokepoint (the office door) for a crisp binary
  re-route/occlusion flip; a dense many-building boom filling the map and the resulting
  aggregate route-length shift is left to the scale rung.
- `bbnav_wall_off` reuses the R1 nav flood by SEVERING adjacency of blocked cells (map mutation
  by rule); the *reversal* re-adds adjacency mechanically (adapter re-ingest) rather than by a
  rule — reverting the walkable graph is mechanical map I/O, symmetric with the initial ingest.
- Occlusion is reflected into the host grid (`_apply_hop` pattern) and read by the scaffold's
  geometric `can_see`; the cell's `occludes` attr is also set by the rule, so the belief carries
  the mutation even where a consumer reads the graph directly.

## Discipline confirmation

Additive-only, one prefix `bigville_build_`. NEW files only; no tracked file edited (R13/R7
imported read-only; `VISION_PROTOCOL.md` / `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` untouched). Both
seeds `self_load_only`. `git diff <base> -- runners/dsl` EMPTY (no Rust, incl `term.rs`).
Canonical `.so` md5 UNCHANGED start→end; no `.so` committed. The ~43-min oracle benches
(`per_area_settlement_regression.sh` / `rung7_vision_bench.sh`) were NOT run — an additive
`self_load_only` rung cannot regress them, and the fast baseline gate (11/11) + additive
discipline + a decision-free adapter source-audit suffice (2026-07-29 directive).
