# PROGRAM SYNTHESIS P7 — track D: the POWERED re-measurement (H7a/H7b/H7c verdicts)

**Date:** 2026-07-31. Prereg: `PROGRAM_SYNTHESIS_P7_PREREG.md` (written
first; this document is the registered verdict on H7a/H7b/H7c/H7d).
Companions: `PROGRAM_SYNTHESIS_P7A.md` (descent), `PROGRAM_SYNTHESIS_P7B.md`
(repair), `PROGRAM_SYNTHESIS_P7C.md` (chunks), `PROGRAM_SYNTHESIS_P6_BATTERY.md`
(the frozen instrument + delta methodology). Deliverables:
`scripts/prog_synthesis_battery.py` (`--append-p7`, additive arm modes),
`results/prog_synthesis_battery.json` (three APPENDED arms — the frozen
MAIN / FROZEN / MAIN-POSTFIX rows are byte-untouched, hash-pinned before and
after the append), `tests/test_prog_synthesis_battery_migrated.py` (+10
additive gates; all 11 existing pins unmodified and green).

## 0. THE PROTOCOL DECISION (made first, as the task card requires)

**The PRIMARY metric protocol is UNCHANGED from MAIN-POSTFIX:** held-out
rows are never revealed to the loop; a task scores `accepted_holdout_ok` on
its own example rows only. Repair (P7-B) therefore acts only on failures the
loop's OWN verification reveals — its example rows, via CEGIS. Without an
ingested counterexample the repair lane is provably inert (gated twice in
P7-B), so **the primary battery number cannot move on repair's account by
construction**. This resolves the P7-B residual 1 question ("whether track
D's protocol includes a verification-feedback arm is track D's registered
decision") in favour of protocol continuity: every primary number in this
document is commensurable with MAIN-POSTFIX .616 [.528, .697].

**Additionally, ONE clearly-labeled secondary arm runs a DIFFERENT
protocol — REPAIR-ORACLE:** after a `holdout_fail`, exactly ONE failing
held-out row is fed back via `ingest_counterexample` (one round — the
pass@2-with-feedback analog). Every one of its rows carries
`protocol: "repair_oracle_feedback"`; the gate
(`test_p7_protocol_separation`) proves no primary aggregate or delta
includes its counts. Its numbers are reported in §4 and are NEVER
comparable to the primary rows.

## 1. Arms + conditions

Same instrument and protocol as P6/P6.5 in every other respect: the frozen
125-task set, sorted-id order, one fresh substrate per task, primary score =
accepted Program whose ProgEval agrees on ALL held-out rows, Wilson 95% CIs,
Newcombe deltas, twin-run determinism per arm. Engine + seed at this commit:
`seeds/program_synthesis.json` **v1.3.0** (43 rules — descent + repair live
in every arm).

| arm | codebook content | mechanisms | protocol |
|---|---|---|---|
| **MAIN-P7** | starter 8 + spine + boarded bigrams + **15 mined chunks** (`install_mined_chunks`, `results/prog_chunk_mine.json` v1.0.0) | descent + repair rules live | primary |
| **C-CODEBOOK-FROZEN-P7** | starter 8 ONLY (no spine, no chunks, no bigrams — `strip_to_starter`; chunks never installed) | **the SAME mechanisms** (seed rules untouched) — the H7c contrast is CONTENT, not mechanism | primary |
| **REPAIR-ORACLE** | = MAIN-P7 | = MAIN-P7 | secondary (one revealed ce row after a holdout_fail) |

Twin-run determinism: **byte-identical in all three arms**
(main_p7 `c824280ea50a7cd1…`, frozen_p7 `e0f2eba62f24445c…`,
repair_oracle `1c605c1e06e75e90…`; 2.4 s / 2.4 s / 2.8 s per run — no N
cut, no silent caps). Protected controls re-pinned: the frozen MAIN and
MAIN-POSTFIX rows hash to their recorded determinism hashes before AND
after the append (asserted in the driver and in
`test_p7_frozen_arms_untouched_by_the_append`).

## 2. THE POWERED TABLE (primary score, Wilson 95% CIs)

| stratum | n | MAIN-P7 | C-CODEBOOK-FROZEN-P7 | MAIN-POSTFIX (frozen control) |
|---|---|---|---|---|
| branching | 25 | 17/25 (.680 [.484, .828]) | 17/25 (.680 [.484, .828]) | 17/25 (.680 [.484, .828]) |
| error_handling | 5 | 3/5 (.600 [.231, .882]) | 3/5 (.600 [.231, .882]) | 3/5 (.600 [.231, .882]) |
| expression | 30 | 23/30 (.767 [.591, .882]) | 23/30 (.767 [.591, .882]) | 23/30 (.767 [.591, .882]) |
| loop_accumulation | 30 | 8/30 (.267 [.142, .444]) | 5/30 (.167 [.073, .336]) | 7/30 (.233 [.118, .409]) |
| multi_statement | 10 | 8/10 (.800 [.490, .943]) | 7/10 (.700 [.397, .892]) | 6/10 (.600 [.313, .832]) |
| single_statement | 25 | 21/25 (.840 [.653, .936]) | 21/25 (.840 [.653, .936]) | 21/25 (.840 [.653, .936]) |
| **overall** | **125** | **80/125 (.640 [.553, .719])** | **76/125 (.608 [.520, .689])** | **77/125 (.616 [.528, .697])** |

Failure taxonomy (MAIN-P7 vs MAIN-POSTFIX): accepted_holdout_ok 77 → **80**,
gapped:enumerate_failed 29 → **22**, accepted_holdout_fail 15 → **19**,
not_recognized 3 → 3, gapped:no_shape 1 → 1, stalled **0 → 0** (every row
terminal in every arm).

**The paired identity claim (exact, CI-free — the machinery is
deterministic):** the changed-row set vs MAIN-POSTFIX is exactly **7 ids,
all previously `gapped:enumerate_failed`**, and the STOP-defect check is
clean — **zero currently-passing rows flipped** (gated):

- → accepted_holdout_ok (3): `la_20_double_each_total`,
  `ms_04_avg_by_parts`, `ms_09_count_then_double` — the P7-A cited set,
  nothing else; all three descent accepts (rungs.descend = 1, enumerate
  never ran).
- → accepted_holdout_fail (4): `la_10_count_positives`, `la_11_count_evens`,
  `la_21_count_zeros`, `la_29_count_above_ten` — descent's weak
  singleton-derived hole rows overfit; the held-out rows caught every one
  (the prereg §4 taxonomy-shift class, counted as NON-successes).

This is the P7-A informal diagnostic reproduced exactly under the powered
protocol and frozen into the artifact — the diagnostic's changed-set and the
powered changed-set are the same identity list.

## 3. Verdicts against the prereg

### H7a (descent moves loop_accumulation CI-separated) — **REGISTERED NULL**

- MAIN-P7 loop_accumulation **8/30 (.267 [.142, .444])** vs frozen
  MAIN-POSTFIX 7/30 (.233 [.118, .409]); Δ +.033 [−.182, +.245].
- The registered decision rule: stratum Wilson lower bound must exceed
  .409. Measured lower bound: **.142**. Nowhere near — the null P7-A's
  diagnostic anticipated, now measured at power.
- The paired stratum list IS the claim: +1 net (la_20 → ok; la_10/11/21/29
  → holdout_fail, non-successes by the prereg's own rule).
- The mechanism secondary (≥2 cited ids accept via descent with rung
  provenance) was MET 3/3 in P7-A's gates and reproduces here (la_20,
  ms_04, ms_09 accepted, `rungs.enumerate is None`). Both readings stand;
  neither substitutes for the other. Where the stratum mass actually is
  (per-id, from the rows): trigger-grain mismatch (SUM cues `sum_of_two`,
  not a fold — la_09, la_28), no decode cover at all
  (la_07/08/13/14/22/25/26), and multi-item-row folds whose holes derive
  too few rows — codebook-content gaps (P7-C-shaped), not descent-mechanics
  gaps.

### H7b (repair: attempts-per-accept falls; conversions) — **NULL at the primary protocol; mechanism real under the oracle protocol**

- **Primary conversions: zero.** No `holdout_fail → ok` id vs MAIN-POSTFIX.
  By design: the primary protocol reveals nothing for repair to act on, and
  the repair lane is inert without an ingested counterexample (P7-B gate).
- **Attempts-per-accept did NOT fall — it rose slightly by composition:**
  mean over accepted tasks .533 (postfix, n=92) → .606 (MAIN-P7, n=99);
  distributions {0:63, 1:14, 2:10, 3:5} → {0:62, 1:20, 2:11, 3:6}. The
  paired-id fact is sharper: **on the 92 tasks accepted in BOTH arms,
  attempts are identical on 91 and differ on exactly one —
  `br_19_pick_or_boost` 0 → 3, the chunk-decoy cost (§3-H7c)**. The mean
  moved because 7 new descent accepts joined at attempts 1–2, not because
  any standing accept got cheaper. The P7-B mechanism number (1 unit of
  post-failure work vs 3 under global re-proposal, on la_10) remains a
  gate-level fact; at battery grain the primary protocol never exercises it.
- **Parks: 0 in all three arms** (gated) — the P6.5 discipline holds
  through descent + repair + chunks.

### H7c (learned layer pays, CI-separated — the H6 retest) — **NULL AGAIN, now with the mechanism/content split measured**

- MAIN-P7 − C-CODEBOOK-FROZEN-P7 = **+3.2 pp [−.087, +.150]** —
  `inside_ci_above_3x_step_no_measured_gain`. The H6 verdict reproduces at
  the P7 stack: **no CI-separated capability gain from learned CONTENT.**
- The paired identity list is the SAME four ids as H6's entire delta:
  `la_03_running_sum`, `la_04_accumulate_all`, `la_05_tally_up`,
  `ms_01_fold_sum` — the spine/lattice (tally) tasks. Nothing else moved
  in either direction.
- **What the learned layer DID buy, at paired-id grain (rung provenance,
  the P6.5 read-the-markers convention):**
  - chunk rung-1 accepts: **0**. The chunk layer's entire battery
    footprint is ONE id — `br_19_pick_or_boost`, where a cueable chunk
    (`ck_prog_if_stmt_n1_q1`, triggers {IF, STMT}) fired as a DECOY,
    consumed 3 attempts, was CEGIS-excluded, and the enumerator then
    accepted the same term as before (outcome unchanged, attempts 0 → 3).
    P7-C §5's prediction ("cueing surface near zero at this
    corpus↔battery pairing") measured exactly.
  - descent hole-fills using chunk content: **0** — descent's skeleton
    material on this battery is the STARTER shapes (`total_of_list`,
    `count_of_list`); the same 7 descent accepts appear in BOTH arms
    (the frozen arm's provenance lists the identical id set). Descent is
    mechanism, not learned content, and the arm design proves it.
  - spine + bigrams: the 4 tally ids — the whole measured delta,
    unchanged since P6.
- **The null reading, stated plainly (per prereg):** capability mass
  remains on the ENUMERATOR + the EXECUTION-VERDICT layer. MAIN-P7's 99
  accepted-any decompose as: enumerate 78, codebook rung-1 10, descent 7,
  spine/lattice 4 (+ br_19 counted at its enumerate rung). The learned
  layer is, at this grain and this corpus↔battery pairing, a RECOGNITION /
  DECOY surface, not a GENERATION asset — the §9/P6 reading with a second
  powered measurement behind it, and with P7-C's sharper cause attached:
  the mined idioms are graph-adapter guards; the battery is integer
  arithmetic; chunk mining transfers idioms, not domains.
- Condition note (the P6.5 §7.4 precedent): FROZEN-P7 76/125 vs the
  original FROZEN 61/125 is **not** a learned-layer statement — it
  conflates the P6.5 stall fix + the descent mechanism (both live in
  FROZEN-P7's seed). The only fair content contrast is MAIN-P7 vs
  FROZEN-P7, same seed, same moment — the row above.

## 4. REPAIR-ORACLE (secondary protocol — reported separately, never compared to primary rows)

One revealed counterexample per holdout-failing task, one round. Overall
under this protocol: **81/125 (.648 [.561, .726])**;
loop_accumulation 9/30 (.300 [.167, .479]). 19 tasks ingested a ce
(identity list in the artifact); where they landed:

| landing | n | ids / what it means |
|---|---|---|
| → accepted_holdout_ok | 1 | `la_10_count_positives` — localized to the final_expr hole, 1 repair round, the never-revealed held-out row passes (the P7-B conversion reproduced under the battery driver) |
| → still accepted_holdout_fail | 2 | `la_11_count_evens`, `br_21_pass_fail` — round 1 re-fits another wrong term; the ONE-round cap leaves it standing (P7-B measured la_11 reaching the honest terminal at round 2) |
| → honest gap | 16 | 11 `no_shape` + 3 `exhausted` + 2 `enumerate_failed` — refuted accepts RETRACTED and retired honestly: 2 localized to a hole and failed the re-solve (`la_21`/`la_29` → enumerate_failed); 14 rung-1/enumerate accepts refused localization honestly (no skeleton/hole split — the P7-B refusal contract) and exhausted the global CEGIS path. (Of the 19 fed, 4 localized — la_10/11/21/29, the descent-grain accepts — and 15 refused.) |

The honest headline for this arm: **a verifier-in-the-loop converts +1 task
and, more importantly, retires 16 standing WRONG accepts to honest
terminals** — accepted_holdout_fail drops 19 → 2 under feedback. That is
the verdict layer's §2.2 class being drained by the repair lane exactly as
P7-B designed, at the cost of accepted-count optics (80 → 81 ok, but
accepted_any 99 → 83). Under this protocol the score is
protocol-inflated relative to primary (one held-out row is revealed), which
is why it is fenced off; parks stay 0 and twin-run determinism holds here
too.

## 5. Gates (all green at this commit)

`tests/test_prog_synthesis_battery_migrated.py` — **21 passed, 0.54 s**
(11 existing pins UNMODIFIED + 10 additive):

- `test_p7_arms_rows_are_baseline_and_aggregates_derive` — rows are the
  baseline for all three new arms (overall + per-stratum Wilson re-derived,
  taxonomy accounts every row, twin hashes re-derive, zero parks);
- `test_p7_protocol_separation` — every repair_oracle row carries the
  protocol label, every primary row carries `primary`, the H7c delta
  re-derives from the PRIMARY arms and provably would not from the oracle
  arm, H7a reads the main_p7 stratum block verbatim;
- `test_p7_frozen_arms_untouched_by_the_append` — MAIN and MAIN-POSTFIX
  rows still hash to their recorded determinism hashes;
- `test_p7_verdicts_rederive_from_the_rows` — the H7a decision rule
  re-applies, the STOP-defect list re-derives empty, paired lists and
  oracle conversions re-derive from rows;
- 6 live re-verifications (2 per arm): main_p7 `la_20` (descent accept) +
  `br_19` (chunk decoy, attempts 3, enumerate accept); frozen_p7 `la_03`
  (spine stripped → gapped) + `la_20` (descent on starter content —
  mechanism-on/content-off, live); repair_oracle `la_10` (the conversion,
  rounds=1) + `br_10` (refused localization → honest gap).

Neighbor suites at the same moment: program_synthesis 17, descent 15,
repair 11, chunks 11, selfimprove 5, constructions 10, baseline 11 —
**80 passed, 6.0 s**. Driver changes are additive (`run_task` now delegates
to the shared `_build_row`; its output for the legacy arms is
shape-identical, and the pre-existing live-reverify pins passed with zero
edits).

## 6. Honest residuals

1. **The scoreboard's remaining mass is enumerated, not characterised:**
   22 `gapped:enumerate_failed` (folds/parity/closed forms beyond every
   rung — per-id in the artifact), 19 `accepted_holdout_fail`
   (underdetermined 3-5-row specs — the verdict layer catching first-fit;
   4 of them descent-grain), 3 `not_recognized`, 1 `no_shape`.
2. **The chunk decoy cost is real but tiny** (1 id, +3 attempts, no outcome
   change). If chunk mining is re-run on a matched-domain corpus, decoy
   mass should be re-measured before cueing is widened.
3. **REPAIR-ORACLE is one-round by registration.** la_11-class tasks need
   round 2 to reach their honest terminal; a multi-round oracle arm is a
   different (again protocol-distinct) instrument.
4. **Named levers carried forward** (unchanged by this rung, listed in the
   arc summary): the Rust `SynthEnumerate` exclude param; scalar-loop
   descent scope; value-domain widening (Mod / floor-div / const reach);
   spec-comprehension for the 3 not_recognized phrasings; an MBPP-style
   external probe for eval-subset coverage.
