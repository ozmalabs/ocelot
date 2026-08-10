# BIGVILLE 247000 — KNOWN LAWS + IN-GAME ENFORCEMENT — PRE-REGISTRATION

Pre-registered BEFORE the reported numbers. A synthetic MODEL of a
law-enforcement mechanism, **not** a claim about real law or politics and not
new social science. Deterministic / categorical (stated below).

## Block claim (verbatim `seed_claim` output)

```
$ python scripts/seed_claim.py 247000 247999
SEED CLAIM 247000-247999: CLEAN -- no collision DETECTED.
  Scope: 969 files with seed sinks; 680 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
EXIT: 0
```

Block **247000–247999** claimed.

## Base / engine

- Base SHA: `611bf0464f` (worktree branched from it; merge-base verified).
- Engine: built in THIS worktree (`cargo build --release`); `source_match=own`
  via `test_engine_provenance_migrated`. Zero Rust added (`git diff runners/dsl`
  empty). Canonical shared `.so` never written through (md5 recorded start==end
  in the results doc).

## The mechanism (all graph-native; NO Rust, NO Python decision)

Built additively on the bigville scaffold (245000 drama + sim occlusion gate +
reporter/credibility). New seed `seeds/bigville_laws_enforcement.json` (5 rules,
`self_load_only`, integer-native) + a thin subclass adapter
`worlds/bigville_law_world.py` (imports `BigvilleSimWorld`; edits no existing
file).

- **Law = KNOWN.** Two first-class `Law` graph nodes every inhabitant HOLDS
  (`knows_law` edges): a **prohibition** law (`PROHIBIT_OFFICE_HARM`,
  `prohibits=office_harm` — John can break it) and a **removal** law
  (`OFFICE_REMOVAL`, council process — the lawful instrument of Mary's counter).
  Not a hardcoded world constraint.
- **Violation = witnessed (occlusion-gated).** The adapter accrues the
  Constable's `witnessed_harm`/`witnessed_act` ONLY when it has line-of-sight to
  the office (the scaffold's Bresenham LOS query) AND John held harm.
  `bl_detect_violation` mints a `Violation` iff the held law's `prohibits`
  pattern matches the witnessed act AND `witnessed_harm>0`. An occluded office
  scheme is never detected.
- **Enforcer = an agent, deciding by rule.** `bl_enforce`/`bl_decline`: the
  Constable acts iff `duty_weight > loyalty_to_john`. Impartial (loyalty 0)
  enforces; captured (John's lever, loyalty 2 > duty 1) declines. No external
  referee; no Python `if` decides the outcome.
- **Consequence = in-graph.** Enforcement sets `Office.censures=1`; lawful
  removal sets `Office.hold=0`, `Office.removed=1`.
- **Lawful counter.** `bl_mary_files_motion` mints a `RemovalMotion` citing the
  removal law (Mary's `reduce_office_hold` goal cannot act extra-legally);
  `bl_council_removes` removes John iff a lawful motion exists, the council is
  impartial, and a quorum of the ELECTORATE backs Mary (`Sum` over elector
  villagers > quorum) — the credibility asymmetry gates the counter.

## FIXED config regime (declared; the DECISION is never these numbers)

| knob | value |
|---|---|
| `PROHIBIT_OFFICE_HARM.prohibits` | `office_harm` |
| `OFFICE_REMOVAL.kind` | `removal` (council process) |
| Constable `duty_weight` | 1 |
| Constable `loyalty_to_john` — impartial | 0 |
| Constable `loyalty_to_john` — captured | 2 |
| Constable witness post (LOS to office) | (10,4) office-door beat |
| Constable occluded post (no LOS) | (14,8) town square |
| Council `quorum` (electorate = the 5 citizens; press `is_elector=0`) | 3 |
| T (ticks) | 20 |

Constable LOS to the office `(5,4)` was verified with the scaffold's own
`perceives` query BEFORE measurement: `(10,4)→True`, `(14,8)→False`.

## Pre-registered gates (with failing controls)

- **G-law-known.** The two laws are graph nodes inhabitants HOLD (`knows_law`);
  John holds the prohibition law he breaks, Mary the removal law; source-audit
  shows no hardcoded law constraint deciding outcomes.
- **G-enforcement-in-game.** A witnessing agent DETECTS the violation and an
  enforcer RULE applies the consequence; source-audit: no forbidden Python
  rule-engine call, no external referee, no Python `if` deciding an enforcement
  outcome.
- **G-occlusion-limits-enforcement (HEADLINE, failing control).** John schemes
  every tick in BOTH arms; the ONLY change is the constable's LOS. Occluded ⇒
  never enforced (0 violations, 0 censures); witnessed ⇒ enforced (1 censure).
  Enforcement flips with occlusion alone.
- **G-captured-enforcer (failing control).** A captured constable (John's lever)
  DECLINES against John even when it witnesses the violation ⇒ violation
  persists, no censure; an impartial enforcer enforces ⇒ the two arms differ.
- **G-lawful-counter.** Mary's `reduce_office_hold` runs THROUGH the removal law
  (file motion → council process), not extra-legally. Controls: no removal law
  ⇒ no motion, no removal; captured council ⇒ motion filed but removal blocked.
- **G-discipline.** No Rust (`runners/dsl` diff empty); own engine
  (`source_match=own`); canonical `.so` start==end; rung7 vision bench and
  per-area fail-set unchanged from baseline; additive files only.

## Falsifier

If the SAME John behaviour (schemes every tick) produced the SAME enforcement
outcome regardless of the constable's line-of-sight — i.e. an occluded office
scheme were censured, OR a witnessed one were not — the occlusion gate would be
cosmetic and G-occlusion-limits-enforcement would be FALSE. Likewise, if John
were removed with NO removal law held / NO motion filed, the "law is the
mechanism" claim would be FALSE (extra-legal removal). Either observation voids
the headline.

## Honesty / residuals (declared up front)

- Deterministic categorical gates (fixed roles; the seeds are the only
  variation) — stated, not hidden.
- Synthetic model of a mechanism; the abuse-line credibility asymmetry is reused
  from 245000, not re-derived.
- The council quorum reading the electorate (press excluded via `is_elector`)
  and the sim-scaffold backing counts (which differ from the pure 245000 drama
  because of the geometry + newspaper) are reported straight in the results doc.
