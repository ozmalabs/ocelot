# BIGVILLE 247000 — KNOWN LAWS + IN-GAME ENFORCEMENT — RESULTS

Synthetic MODEL of a law-enforcement mechanism (not a claim about real law or
politics). Deterministic / categorical gates. Pre-registration:
`BIGVILLE_LAW_PREREG.md`. All decisions are graph rules
(`seeds/bigville_laws_enforcement.json`); the world adapter
(`worlds/bigville_law_world.py`) only ingests (occlusion-gated witnessing) and
emits. NO Rust; own engine; canonical `.so` untouched.

## The mechanism, one line each

- **Law = KNOWN.** Two `Law` nodes every inhabitant HOLDS (`knows_law`):
  `PROHIBIT_OFFICE_HARM` (John can break it) and `OFFICE_REMOVAL` (a council
  process — Mary's lawful instrument). Not a hardcoded world constraint.
- **Violation = witnessed (occlusion-gated).** `bl_detect_violation` mints a
  `Violation` iff the Constable's held prohibition law's `prohibits` pattern ==
  the act it WITNESSED, and it actually witnessed harm — and the adapter accrues
  that witness ONLY under line-of-sight to the office (the scaffold's Bresenham
  LOS query).
- **Enforcer = an agent, by rule.** `bl_enforce`/`bl_decline`: the Constable
  acts iff `duty_weight > loyalty_to_john`. No external referee, no Python `if`.
- **Consequence = in-graph.** `Office.censures=1` (enforcement); `Office.hold=0`,
  `Office.removed=1` (lawful removal).
- **Lawful counter.** `bl_mary_files_motion` files a `RemovalMotion` citing the
  removal law; `bl_council_removes` removes John via that motion + an impartial
  council + an electorate quorum backing Mary.

## HEADLINE — enforcement flips with occlusion alone

The pasted occlusion-flip pair (same John — schemes every tick, scheme_rate 1.00
in BOTH arms; the ONLY difference is the constable's line-of-sight):

| arm | constable sees office | John scheme rate | violation detected | ENFORCED | censures |
|---|---|---|---|---|---|
| **WITNESSED** (constable at office-door beat, LOS to office) | True | 1.00 | 1 | **True** | 1 |
| **OCCLUDED** (constable in the square; office walls block LOS) | False | 1.00 | 0 | **False** | 0 |

`flips_with_occlusion_alone = True`. An occluded office scheme is NEVER enforced;
the SAME scheme moved into the enforcer's line-of-sight IS enforced.

## Gates (each with its failing control)

| gate | result | control |
|---|---|---|
| **G-law-known** | PASS | 2 laws are graph nodes held via `knows_law`; John holds `PROHIBIT_OFFICE_HARM`, Mary holds `OFFICE_REMOVAL`; every citizen holds both. Source-audit: no hardcoded law constraint decides outcomes. |
| **G-enforcement-in-game** | PASS | main: violation detected (1) + censure applied by the enforcer RULE (censures=1). Source-audit: no `graph_rewrite.run`/`gr.run`/`_match`/`_apply`/`make_rule`, no `referee`, no reward/shaping token. |
| **G-occlusion-limits-enforcement (HEADLINE)** | PASS | witnessed ⇒ enforced (censures 1); occluded ⇒ 0 violations / 0 censures. Enforcement flips with occlusion alone (pair above). |
| **G-captured-enforcer** | PASS | captured constable (John's lever, loyalty 2 > duty 1) WITNESSES the violation (detected=1) but DECLINES (enforced=False, censures=0 — violation persists); impartial constable enforces (censures=1). The two arms differ by motivation only. |
| **G-lawful-counter** | PASS | no-deception + impartial council + Mary holds the removal law ⇒ motion filed (1) → council removes John (lawful=1, office_hold=0). Controls: NO removal law ⇒ 0 motions, John stays (office_hold=1, no extra-legal path); CAPTURED council ⇒ motion filed (1) but removal blocked (office_hold=1). Bonus: under deception the credibility asymmetry starves the motion of quorum (electorate backing 3, quorum 3 ⇒ not removed). |

All 5 gates PASS; runner `results/bigville_law/results.json` `all_pass=True`.

## Discipline ledger

| item | value |
|---|---|
| base SHA | `611bf0464f` (merge-base verified) |
| prereg commit | `c02002b7dfb2adaa69becb71e6193ecb0c0db0c0` |
| impl commit | `d26cf8fc63890df00239d44363c922c471a0a1c7` |
| own engine md5 | `10f65be659e0d9a9290aff39f7f5b92a` (`source_match=own`) |
| canonical `.so` md5 START | `fd82dc2978dbb055496dd82390ac2ebe` |
| canonical `.so` md5 END | `fd82dc2978dbb055496dd82390ac2ebe` (identical) |
| `git diff runners/dsl` | EMPTY (zero Rust) |
| rung7 vision bench (clean, no `data/`) | 214 passed / 10 skipped / 0 failed (matches baseline) |
| per-area fail-set (clean, no `data/`) | 23 failed / 278 passed / 5 skipped — ALL 23 are recorded-baseline nodes (0 NEW, 0 `bigville_law`); fail-set ⊆ baseline |
| `test_failure_baseline_migrated` | GREEN |
| bigville_law gate tests | 10/10 |
| bigville_drama (unbroken) | 9/9 |

### The oracle was measured in a NON-NESTED worktree (honest note)

The delivery worktree was created **inside** the canonical gamma-substrate
directory (`gamma-substrate/.worktrees/…`). When pytest is invoked there by
path, its rootdir walk hits the canonical `tests/`/`domains/` **above** the
worktree, and `data/` resolves against the canonical ancestor — so the nested
run reported 2 `test_engine_provenance_migrated` failures (`this_tree` ≠ `ROOT`)
and saw `data/` present (224 collected, 0 skipped). **Both are worktree-PLACEMENT
artifacts, not this rung's code** — proven by a clean module-import probe (all
paths worktree, `source_match=own`) and by the recorded baseline
(`condition: no data/ symlink; own engine build`) carrying **zero** provenance
entries. The oracle numbers above were therefore measured in a **non-nested
verify worktree** at the impl commit (`.claude/worktrees/bl247-verify`, own
build, no `data/`), where the 2 provenance failures vanish. The additive files
(`bigville_law_*` / `bigville_laws_enforcement.json`) are in nobody's fixed list
and cannot change either oracle's fail-set.

## Honest residuals

- Deterministic categorical gates (fixed roles; the seeds are the only
  variation) — stated, not hidden.
- The sim-scaffold backing counts differ from the pure 245000 drama (geometry +
  newspaper), which is why the deception-arm electorate backing is 3 (not 1);
  reported straight. The council quorum reads the ELECTORATE (press
  `is_elector=0`, excluded).
- The credibility asymmetry gating the lawful counter is a bonus observation
  (quorum 3 vs deception backing 3), sensitive to the config; the REQUIRED gate
  is only that the counter runs THROUGH the law, which the no-law and
  captured-council controls establish.
- Synthetic model; the abuse-line credibility asymmetry is reused from 245000,
  not re-derived. Absence/novelty claims are weak-by-construction; Smallville et
  al. prior art is conceded in `BIGVILLE_BUILD_NOTES.md`.

## Falsifier (as pre-registered)

Same John behaviour producing the same enforcement outcome regardless of LOS
(occluded scheme censured, or witnessed one not), OR John removed with no removal
law held / no motion filed, would void the headline. Observed: neither occurs.
