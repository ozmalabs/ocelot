# BIGVILLE R20 — COUNCIL MEETINGS & THE NOTICEBOARD (block 268000) — RESULTS

**Measured after the prereg commit.** Base merge-base (origin/main):
`350a45c4078403510bd1c83ea389a06ae6dadacd`. Branch:
`worktree-agent-ae7e37507f2118a0e`. All numbers are graph read-offs; every
decision is a seed rule. Prereg: `BIGVILLE_COUNCIL_PREREG.md`.

## Headline

Governance became a PROCESS with a public face, a private core, and a controllable
written record — all graph-native (10 rules across two `self_load_only` seeds,
**zero new Rust**). The four R20 gates land:

| gate | result |
|---|---|
| G-two-tier-meeting | public address perceived (`heard_address=1`), private decision OCCLUDED (`heard_decision=0`) while `private_on=1`; off-cadence ⇒ no meeting; ablate private tier ⇒ decision becomes public |
| **G-public-influence-or-theatre (HEADLINE)** | **responsive council Pearson r = +1.0000 (agency); captured council r = 0.0000 (theatre)** |
| G-institutional-stated≠held | captured+malice: address 10 vs decision 60 ⇒ `stated_held_gap = 50`; ablate malice ⇒ gap = 0 |
| G-noticeboard-promulgates | biased clerk distorts (`recorded = decision + bias`); only the literate-at-hall resident learns the law; illiterate / distant ⇒ officially known yet personally UNKNOWN; ablate literacy gate ⇒ uniform (access still binds) |

## The mechanism (all rules; adapter is mechanical I/O)

`bigville_council_gov.json` (7 rules): `cm_convene` (R3 cadence
`Mod(now_day,cadence)==0`), `cm_public_address`, `cm_attendee_hears_address`,
`cm_member_vote` (`vote = captured ? base+malice*premium : public_demand`),
`cm_private_decision` (`held_decision = IDiv(Sum vote, Count members)` — the
collective decision_value over the backing-graph), `cm_attendee_hears_decision`
(fires only when `private_on==0` — the R19 observe-vs-hear occlusion of the room),
`cm_institutional_gap` (`|address − decision|`, the 234 atom at institutional
scale).

`bigville_council_board.json` (3 rules): `cm_clerk_writes`
(`recorded = held_decision + clerk_bias` — the biased minutes), `cm_post_notice`
(`officially_known=1`), `cm_resident_reads` (learns iff `at_hall AND (literate OR
gate_ablated)` — R1 access + R18 literacy).

## G-public-influence-or-theatre — the measurement

Public demand swept over `[10, 15, 20, 25, 30, 35]`; the private `held_decision`
read off per meeting; Pearson r computed over the pairs.

- **Responsive council** (`captured=0`): decisions `= [10,15,20,25,30,35]` (the
  decision IS the demand) → **r = +1.0000**. Public voice reaches the lever — AGENCY.
- **Captured council** (John's, `captured=1, malice_on=1`): decisions
  `= [60,60,60,60,60,60]` (never moves) → zero covariance → **r = 0.0000**. Ritual
  over a pre-made decision — STRUCTURE.

This is the agency-vs-structure question MADE MEASURABLE, not asserted. The
correlation is READ OFF the graph (a statistic over read-offs) — not a new
primitive; the votes/decision are set entirely by rules.

## The §0 "room where it happened" asymmetry

Occlusion is real for the agents (`heard_decision=0` under `private_on=1` — the
town sees the council convene but never hears the deliberation) and TRANSPARENT for
the observer (we read `held_decision`, each member's `vote`, and the
`stated_held_gap` directly). The noticeboard minutes (`recorded`) are a lossy,
optionally-biased rendering scoreable against the ground-truth `held_decision` we
hold — the controlled validation ground for the case-reconstruction machinery.

## Discipline

- `runners/dsl` diff vs base **empty** — no new Rust. Terms used ⊆ the existing set
  (`IfThenElse/Eq/And/Or/Not/Gt/Gte/Abs/Plus/Minus/Times/IDiv/Mod/Sum/Count/
  Neighbours/Attr/Var/Lit`).
- Both seeds `self_load_only`, `depends_on: []` — cannot regress any other suite.
- Adapter source-audit: no Python rule engine, no decision-parameter branch.
- Engine provenance `source_match = shared`; canonical `.so` md5
  `fd82dc2978dbb055496dd82390ac2ebe` unchanged.
- Gates run INLINE: `test_bigville_council_migrated` **11/11**;
  `test_failure_baseline_migrated` **11/11**; `test_engine_provenance_migrated`
  **7/7**. The ~43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh`
  were NOT run (additive `self_load_only` rung — 2026-07-29 directive).

## Honest residuals

- **Scheduling is minimal.** `cm_convene` demonstrates the R3 cadence
  (`Mod(now_day,cadence)==0`) but the meeting is armed per call by the adapter — a
  full autonomous R3 clock driving the cadence is not wired here (the cadence is the
  gate; the clock is R3's, imported in concept only).
- **The correlation is deterministic (r = 1.0 / 0.0), not noisy.** With
  `vote = IfThenElse(captured, held, demand)` the responsive council tracks demand
  perfectly and the captured one is exactly flat. A partial-responsiveness blend
  (an intermediate r) is expressible in the same Terms (an `IDiv` bp-weighted mix)
  but is not built — the headline is the SEPARATION (agency vs theatre), and a clean
  ±1/0 separation is the strongest form of it, not a tuned midpoint.
- **Literacy is a seed axis, not an R18 outcome edge.** The `literate` flag stands
  in for the R18 attainment; the actual `Skill.level`→literacy coupling is imported
  in concept only (R18 is read-only here), matching how R19 scoped its classroom
  proxy.
- **One notice per meeting.** The noticeboard holds the latest decision; a
  persistent multi-notice board history is not modelled (out of R20 scope).
