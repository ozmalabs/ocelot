# PROGRAM SYNTHESIS P7 — PREREGISTRATION (all four tracks)

**Date:** 2026-07-31. Written BEFORE the P7 code, per the §0 standing rules
(power the gate before the endgame; a baseline is a list of identities;
synthetic-proven mechanism ≠ benchmark value — report both; eval-subset
coverage is part of every claim; no silent caps). Companion to
`PROGRAM_SYNTHESIS_PLAN.md` §2-4, `PROGRAM_SYNTHESIS_P4B.md` (+P6.5 §9),
`PROGRAM_SYNTHESIS_P6_BATTERY.md`.

**Point of departure (frozen):** the 125-task battery artifact
(`results/prog_synthesis_battery.json`), arm **MAIN-POSTFIX** = the standing
measurement: overall 77/125 (.616 [.528, .697]); loop_accumulation
**7/30 (.233 [.118, .409])**; failure taxonomy accepted_holdout_ok 77,
gapped:enumerate_failed 29, accepted_holdout_fail 15, not_recognized 3,
gapped:no_shape 1. The recoverable-mass stratum this phase attacks is
**gapped:enumerate_failed (29 ids, per-row in the artifact)** — honest gaps
where no rung could build (list folds / parity / large closed forms).

**Governing insight (P7-A, user-supplied design intent, verbatim):**
*"shapedecode will tell you what is going on"* — the decode's coverage
assignment IS the plan; partial cover is not failure, it is
segmentation-by-recognition; each residual span becomes a sub-goal one grain
finer; only a residual that survives every grain reaches the enumerator;
execution verdict at every level.

---

## 1. Hypotheses

### H7a — recursive descent (track A, this worktree's deliverable)

On a goal whose rung-1 codebook cover is PARTIAL, the rules mint a skeleton
from the covered spans and each uncovered span becomes a Hole sub-goal that
runs the SAME ladder over MECHANICALLY DERIVED local example rows;
hole-scoped enumeration (small holes, big reach) reaches programs the
whole-goal enumerator cannot (its leaves are scalar: a list-input spec is
inadmissible at whole-goal grain, decomposable at hole grain).

- **Primary reading:** loop_accumulation solve rate improves CI-SEPARATED vs
  the frozen MAIN-POSTFIX .233 [.118, .409] on the same 125-task battery —
  i.e. the re-measured stratum's Wilson lower bound > .409.
- **Registered null:** enumerate-at-the-hole does not reach the folds either
  (the derivable-row set is too weak at n=1 singleton rows per task, or the
  residual is not a hole the taxonomy supports). If null: report the
  residual taxonomy per task id — which hole positions were underivable,
  which fold-ups refused, which tasks never had a covered span.
- **Secondary (mechanism, gate-level, this track):** ≥2 real
  `gapped:enumerate_failed` battery ids accept end-to-end via descent with
  held-out rows correct and rung provenance showing descent + hole-solve.
  Cited targets (chosen from the artifact BEFORE implementation, by
  inspection of decode cover + derivability, with their frozen rows):
  `la_20_double_each_total`, `ms_09_count_then_double`, `ms_04_avg_by_parts`
  (all three frozen `gapped:enumerate_failed` in MAIN and MAIN-POSTFIX).
- **Honest scope, declared up front:** derived sub-rows are only minted
  where the skeleton makes them determinable —
  (a) **final-expression hole**: sub-rows = outer rows over LIVE VARS (the
      covered constructions' values computed per row by prefix evaluation);
      always derivable modulo traps;
  (b) **fold accumulator-step hole** (covered construction is a Fold with a
      literal init): derivable exactly for outer rows whose list argument
      has length 1 (acc_before = init, acc_after = the outer output —
      one-iteration unroll; no inversion, no arithmetic);
  (c) **branch-arm hole**: DECLARED A NAMED BLOCKER this rung — zero
      corpus mass in the battery's gapped set (measured: no gapped
      branching id has a partial codebook cover with derivable arms), so it
      ships as taxonomy vocabulary only, honest-refused if requested.
  Anything else (multi-item fold rows, non-fold non-expression covers,
  stmts-mode covers in a live-var position) → the hole is honest-refused
  and the goal falls to the next rung. Scalar-loop tasks (sum_to_n family)
  have NO list rows and NO derivable hole — registered as out of descent's
  scope; they stay on the whole-goal enumerate rung.

### H7b — counterexample-guided REPAIR (track B, sibling)

Attempts-per-accept falls; `accepted_holdout_fail` converts to
`accepted_holdout_ok` without global re-proposal; park count stays 0.
Null: local repair converts nothing the global loop didn't; report the
attempted-repair taxonomy.

### H7c — chunk mining (track C, sibling)

The codebook-frozen delta becomes CI-separated on the P7 battery re-run
(the H6 retest — the learned layer finally pays, because mined chunks
propose content the starter codebook lacks). Null: capability stays on the
enumerator; state what that means for the architecture (the learned layer
is then a RECOGNITION asset, not a GENERATION asset, at this grain — the
§9/P6 null restated with a second measurement behind it).

### H7d — re-measurement (track D, owns the battery)

The P7 battery re-run appends new arms to the artifact; **frozen
MAIN / FROZEN / MAIN-POSTFIX rows are untouched** (protected control); the
changed-row set is reported as an identity list vs MAIN-POSTFIX, never a
count; twin-run determinism required; Wilson CIs on every proportion;
paired identity check: no currently-passing row may flip to failing
(any such flip is a STOP defect, not a trade).

## 2. Gates (track A — `tests/test_prog_descent_migrated.py` + additive main-suite tests)

1. **Headline:** ≥2 of the cited battery-gapped ids
   (`la_20_double_each_total`, `ms_09_count_then_double`,
   `ms_04_avg_by_parts`) accept via descent, held-out rows correct, rung
   provenance shows descent + hole solve (and NOT whole-goal enumerate).
2. **Derived-row correctness (pinned):** for a fold task the derived
   (acc, item) → acc' rows equal the hand-computed truth
   (la_20: exactly one derivable row, `(acc=0, x=5) → 10` from the
   singleton example; the `[1,2,3]` row is NOT derivable and is counted as
   such).
3. **Boundaries-from-decode:** the skeleton's cover/residual facts on the
   goal equal an independently evaluated ShapeDecode of the same skeleton
   (assert the plan facts, not a Python cut); the hole sub-goal's tokens
   are exactly the decode residual.
4. **Depth budget honest:** a goal at ps_depth ≥ ps_max_depth never
   descends (falls to enumerate/gap); sub-goal failure → fold-up refuses →
   the outer goal falls to the next rung honestly (a refused descent ends
   `gapped:enumerate_failed`, exactly the pre-P7 terminal).
5. **Occam guards:** codebook-covered requests never descend (rung attrs);
   scalar-row requests never descend; descent-exhausted goals still reach
   whole-goal enumerate then gap.
6. **Non-regression:** the FULL existing program_synthesis suite green
   (the single seed-manifest rule-count pin updated alongside the version
   bump, the P6.5 precedent — every behavioural assertion untouched);
   battery gate 11 green over the UNMODIFIED artifact (frozen rows
   untouched; the three pinned live-reverify ids reproduce:
   `ex_01_pick_larger`, `la_03_running_sum`, `ms_10_collatz_next` — ms_10
   has ZERO decode cover, measured, so descent cannot touch it).
7. **No-Python-decision source audit** re-run on the modified adapter
   (ink-suite regex pattern).
8. Suites stay under ~120 s total; the full battery is NOT re-run here
   (track D owns re-measurement) — the cited ids run end-to-end as the
   gate instead.

## 3. Protected controls

- `results/prog_synthesis_battery.json`: append-only; MAIN / FROZEN /
  MAIN-POSTFIX rows byte-frozen.
- `results/code_synthesis_baseline.json` (C-BATTERY, 7/26): untouched;
  its gate keeps running.
- The P4 gate fixtures remain the mechanism dev set; no battery request
  text may be copied into new tests (contamination guard stands).
- Attempt-counter discipline: the P6.5 collision lesson applies to
  sub-goals from the start — every Hole sub-goal is its OWN Goal node with
  its OWN integer `ps_attempts`/`ps_budget` (collision-free by
  construction); fold-up verification uses hole-scoped row facts
  (`fu_*`), never the outer rows' `eval_attempt`/`verdict_attempt` lane,
  so the P6.5 guard is never re-armed by descent.

## 4. Decision rules for readings

- A stratum delta is claimed CI-separated only if the arms' Wilson 95%
  intervals are disjoint (the P6 rule); deltas within ~3× the per-episode
  step (2.4 pp at n=125; ~3.3 pp within a 30-task stratum) are noise.
- Mechanism gates (the cited-id conversions) are exact, deterministic,
  and reported separately from any battery number.
- `gapped → accepted_holdout_fail` conversions are NOT successes; they are
  reported as taxonomy shifts (the verdict layer catching weak derived
  rows — the §2.2 class at descent grain).

---

## 5. OUTCOMES (appended 2026-07-31 by track D — nothing above edited; full detail in `PROGRAM_SYNTHESIS_P7D.md`)

Protocol decision (track D's registered call, §H7b/P7-B residual 1):
PRIMARY protocol unchanged from MAIN-POSTFIX (held-out rows never revealed;
repair acts only on loop-revealed failures). One protocol-DISTINCT secondary
arm, REPAIR-ORACLE (one revealed ce row after a holdout_fail, one round),
reported separately and never merged into primary aggregates (gated).

Arms appended to the artifact (frozen MAIN/FROZEN/MAIN-POSTFIX rows
hash-pinned untouched; twin-run determinism byte-identical ×3; zero parks;
zero STOP-defect flips vs MAIN-POSTFIX):

- **MAIN-P7** (full stack: seed v1.3.0 descent+repair, 15 mined chunks,
  starter+spine+bigrams): **80/125 (.640 [.553, .719])**.
- **C-CODEBOOK-FROZEN-P7** (same mechanisms, content stripped to starter 8):
  **76/125 (.608 [.520, .689])**.
- **REPAIR-ORACLE** (secondary protocol): 81/125 (.648 [.561, .726]);
  accepted_holdout_fail 19 → 2 (16 wrong accepts retired to honest gaps,
  1 converted, 2 one-round-capped).

**H7a — REGISTERED NULL.** loop_accumulation 8/30 (.267 [.142, .444]) vs
frozen MAIN-POSTFIX 7/30 (.233 [.118, .409]); the decision rule (stratum
Wilson lower bound > .409) fails at .142. The paired stratum list is the
claim: la_20 → holdout_ok; la_10/11/21/29 → holdout_fail (non-successes per
§4). The §1 mechanism secondary stands as met (3/3 cited ids, gate-level).
The residual-taxonomy reporting duty §H7a's null clause requires is
discharged in P7D §3 (trigger-grain mismatch / no-cover / weak-derived-row
ids enumerated).

**H7b — NULL at the primary protocol; mechanism real under the oracle.**
Primary conversions: zero (repair lane inert without a revealed row — by
design, gated). Attempts-per-accept did not fall (.533 → .606 by
composition; paired-id attempts identical on 91/92 shared accepts, the one
change being the br_19 chunk-decoy +3). Parks 0. Under REPAIR-ORACLE:
la_10 converts (1 localized round, unrevealed row passes); 16 standing
wrong accepts retire honestly.

**H7c — NULL AGAIN (the H6 retest).** MAIN-P7 − FROZEN-P7 = +3.2 pp
[−.087, +.150]; the identity list is H6's same four spine ids
(la_03/la_04/la_05/ms_01). Chunk rung-1 accepts: 0 (battery footprint = the
br_19 decoy only); descent accepts identical in both arms (mechanism, not
content). The registered null reading applies with P7-C's cause: the
learned layer is a recognition/decoy surface at this corpus↔battery
pairing; capability mass stays on the enumerator (78/99 accepts) + the
execution-verdict layer.

**H7d — delivered as specified:** append-only artifact, frozen rows
untouched (hash-gated), changed-row set reported as an identity list (7
ids, all ex-gapped), twin-run determinism, Wilson CIs throughout, paired
no-flip check clean (empty STOP list, gated).
