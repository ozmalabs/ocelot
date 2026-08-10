# DOES THE FIXPOINT FIX MOVE THE **CONFIRMATORY** IDENTITY SEAM? — PRE-REGISTRATION

*Written and committed BEFORE any measurement number exists. Seed block
**123000–123999**. Closes the standing liability handed on by
`VISION_FIXPOINT_COVERAGE_RESULTS.md` §5.8 / §"standing liability" and
`VISION_FIXPOINT_RERUN_RESULTS.md`: the identity-seam **pilots** moved under the
fix (`identity_seam_pilot.json` 89 recognized / 7 minted under the defect → 96 / 0
under the fix), but the **confirmatory** `identity_seam_C1.json` /
`identity_seam_C2.json` — the documents that carry
`VISION_IDENTITY_SEAM_RESULTS.md`'s published conclusion — were NEVER RUN (the
COVERAGE selector's declared blind spot: constructed output paths). Their state
under the fix is therefore **UNKNOWN, not unchanged**.*

---

## 0. SEED CLAIM (§3 clause 8) — verbatim

```
SEED CLAIM 123000-123999: CLEAN -- no collision DETECTED.
  Scope: 825 files with seed sinks; 513 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Unresolved sink count: 513.**

**Like the two fixpoint predecessors, I DELIBERATELY RE-USE ALREADY-BURNED SEEDS,
and this is not a §3 violation — it is the point.** `identity_seam_measure.py`
seeds off its own fixed `SEED_BLOCK = 72000` (already consumed by the identity
seam rung). A replication that redraws is not a replication: the comparison is
fix-vs-revert on IDENTICAL inputs. My own block 123000–123999 is reserved for
material I draw myself (controls only) and I expect to return it essentially
unused.

## 1. THE QUESTION

**Do the confirmatory `identity_seam_C1.json` / `identity_seam_C2.json`, and the
per-observation `identity_seam_rows_{C1,C2}_{stock,ncc}.json` behind them, MOVE
under the fixpoint fix the way the pilots did — and if so, does
`VISION_IDENTITY_SEAM_RESULTS.md`'s landed CONFIRMATORY conclusion (clauses 1–3,
the mint trajectory) survive?**

**Established facts this rung builds on (not re-litigated):**

- The defect is real: `run_rules` returned over unsettled state because
  `dirty_by_writeset`'s already-dirty early-out skipped the cursor clear
  (`VISION_FIXPOINT_SETTLE_RESULTS.md`). The fix removes one line at
  `substrate.rs:539`; the revert re-adds `if self.rule_dirty[j] { continue; }`.
- The mechanism everywhere it has appeared: **the defect suppresses the ladder's
  post-mint EXACT RE-DECODE (`sd_redecode`, re-armed by `codebook_epoch`), so an
  observation that should resolve to a held identity instead records as a
  *minted* novelty with its span unexplained.**
- **The landed C1/C2 were produced UNDER THE DEFECT** (verified by ancestry, not
  assumed): identity-seam C1 landed at commit `76d514259e` on 2026-07-20 08:45;
  the fix landed at `1ebd1450da` the same day 15:20, ~7 h later, and is NOT an
  ancestor of the identity-seam commit. So the **REVERT arm is the reproduction
  arm** — it must reproduce the committed files — and the **FIX arm is the
  correction**.

## 2. THE ARMS AND THE STATISTIC

Two engines, **built by me in this worktree from this tree's source**, per
§10/§11:

- **FIX** — canonical source as-is (`substrate.rs:539` has no early-out).
- **REVERT** — one line re-added (`if self.rule_dirty[j] { continue; }`),
  rebuilt with `scripts/engine_build.sh`. This is a legitimate `own`-build case:
  the revert changes THIS tree's Rust source and the engine is rebuilt from it,
  so source and engine AGREE and the provenance gate passes strictly (no
  `strict=False` needed). **I state plainly that I am deliberately loading a
  REVERTED engine.**

Under each engine I run, unmodified:

```
PYTHONPATH=runners/dsl/python:. python scripts/identity_seam_measure.py \
    --corpora C1 --out results/identity_seam_C1.json
PYTHONPATH=runners/dsl/python:. python scripts/identity_seam_measure.py \
    --corpora C2 --out results/identity_seam_C2.json
```

(These are the exact constructed output paths of the landed files — recovered by
reading the script and the file structure, since the COVERAGE selector could not
find them from a literal.)

**The comparison is fix-vs-revert ON THE SAME TREE**, both engines mine. The
landed committed files are a THIRD, corroborating arm: the REVERT arm must
reproduce them.

**The statistic, exactly** — a field-by-field diff of each summary document and
each rows document, fix vs revert, with two named readouts:

1. **Per-observation STATUS distribution** on the main trajectory
   (`{minted / is_minted vs recognized / is_held / recognized_transformed}`,
   n=1600 per corpus×arm) — the pilot's headline lived here.
2. **The summary CONCLUSION fields** that `VISION_IDENTITY_SEAM_RESULTS.md`
   publishes: clause-1 persistence + floor + PASS (both strata), clause-2
   collapse DIFFERENT/SIMILAR + paired + PASS, clause-3 per-class rates + sep
   flags + PASS, the `CONJUNCTION_PASS`, and §5's mint trajectory (`traj`,
   `k_after_main`, `k_final`, mints/frame).

Wall-clock (`ms`, `wall_s`, `main_ms`) and provenance leaf fields are EXCLUDED
from the verdict (load-dependent); every reported mover is a COUNT, a VERDICT, or
a status label. No p-value is computed — the comparison is a deterministic
differential on identical inputs, exactly as the two predecessors did.

## 3. EXPOSURE — priced BEFORE any null is reported (§4 of the predecessors)

A null is worthless if the workload never triggers the defect. Exposure is
established two ways:

- **Direct evidence:** the landed (defect-produced) rows already contain
  **`minted`/`is_minted` observations** (measured from the committed files as the
  baseline: C1/stock 20, C1/ncc 23, C2/stock 24, C2/ncc 23 of 1600). Each is a
  candidate site where the suppressed re-decode could flip `minted`→`recognized`.
  If the fix flips any of them, exposure is **self-evident and non-zero** and the
  result is a MOVER, not a null.
- **If — and only if — the confirmatory files come back IDENTICAL fix-vs-revert,**
  I will build the reverted engine with the predecessors' `HARMFUL_SKIPS` counter
  and report the trigger count on a successful C1/C2 run, so the null is priced
  (earned vs vacuous). I will NOT report a bare "nothing moved."

## 4. DECISION RULE

- **MOVER (the pilot pattern reproduces):** if any confirmatory summary field
  that feeds a published claim moves — clause persistence, collapse, a PASS flag,
  the mint trajectory, or the codebook size — **the identity seam's CONFIRMATORY
  conclusion needs revisiting, this OUTRANKS everything, I report it loudly, and I
  do not rescue the original.**
- **STATUS-ONLY MOVE:** if the per-observation `status`/`covered_by`/
  `residual_len`/`covered_count` fields move (spurious `minted`→`recognized`) but
  every SUMMARY conclusion field is byte-stable, I report exactly that: the
  confirmatory moved at the diagnostic-status level (like the pilot) while the
  published conclusion SURVIVES — with the moved rows enumerated, not
  characterised.
- **EARNED NULL:** if nothing moves at all, I count the `sd_redecode` /
  `HARMFUL_SKIPS` exposure on the confirmatory (§3) and state whether the null is
  earned (exposure > 0) or vacuous (exposure == 0). A vacuous null licenses
  nothing.
- **VOID:** if either episode PIN fails to match at run time
  (C1 `08630d4b7b215c469df19b9c42d7b617`, C2 `119eca433329b36b19e5d69fef84966e`),
  the run is void (the script's own gate). Both were verified reachable and
  matching at setup; the gate re-checks at run time.

## 5. MY PREDICTION, STATED IN ADVANCE, WITH PROVISOS (§3 clause 7)

**Primary prediction: the confirmatory WILL move at the per-observation STATUS
level, and the published SUMMARY conclusion will LIKELY SURVIVE.**

Reasoning: the landed minted rows self-cover under the fix — a minted
observation keeps its own quantum id as its `identity` LABEL (verified in the
committed rows: a `minted` row already carries `identity='0_0'`, not `'novel'`),
and the mint EVENT (codebook growth) fires either way (the fix only adds the
re-decode AFTER the mint). So I expect:

- **STATUS distribution MOVES** — the ~20–24 `minted`/`is_minted` rows per arm
  become `recognized`/`is_held` (`residual_len`→0, `covered_count`→36,
  `covered_by`→own id), reproducing the pilot's signature. **PREDICTED MOVER.**
- **Clause 1 (persistence) / Clause 2 (collapse): LIKELY STABLE** — they key on
  the `identity` LABEL, which is stable across the flip (a minted row's label is
  already its quantum id).
- **Clause 3 (`minted` = codebook grew; `refused` = identity=='novel'): LIKELY
  STABLE** — codebook growth is unchanged by a post-mint re-decode, and the
  identity is a quantum id, not `'novel'`.
- **§5 mint trajectory (`traj`, `k_after_main`, `mints`): LIKELY STABLE** — these
  count codebook growth, which the re-decode does not change.

**Proviso most likely to break (and what it would mean):** if under the fix the
re-decode recognizes a **PRIOR-FRAME held identity** instead of self-covering the
fresh mint, then (a) the `identity` LABEL changes, (b) the codebook grows LESS
(no mint when an existing identity is recognized), and (c) clause-1 persistence
and the mint counts MOVE. **That is the outcome that would force revisiting the
confirmatory conclusion**, and §4's MOVER branch governs it. The pilot's fix-arm
`covered_by` was the row's OWN id (self-cover), which is why I predict stability —
but the pilot is n=96 on C1 only, and the confirmatory is n=1600 × 2 corpora × 2
arms, so a prior-frame recognition that never surfaced in the pilot could here.

**Two-sided, in one sentence:** I predict a status-level move with a surviving
conclusion; I will be equally loud if the conclusion moves, because that is the
more consequential outcome and the one the task ranks above all.

## 6. WHAT IS NOT SWEPT

Exactly the two corpora × two arms the landed document defines, each run once per
engine (video decode + substrate are deterministic; the REVERT arm reproducing
the committed file IS the determinism check). No parameter is varied, no metric is
chosen after looking, no re-run beyond the fix/revert/fix-rebuild engine
sequence. `data/` is symlinked (§10.2); the oracle condition is therefore the
**222/0** one on the FIX engine.
