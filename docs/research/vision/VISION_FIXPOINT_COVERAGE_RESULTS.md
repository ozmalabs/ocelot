# FINISHING THE FIXPOINT RE-RUN — COVERAGE — RESULTS

# **SEVEN LANDED DOCUMENTS MOVE, NOT ONE — AND THE ONE THE PREDECESSOR FOUND WAS THE SMALL CASE**

**At 49.4% document coverage and 98.4% EXPOSURE coverage, seven documents move
under the fixpoint fix.** The predecessor found one at 7.5% coverage. The new
headline is **`results/identity_seam_pilot.json`: 89 recognized / 7 minted under
the defect, 96 recognized / 0 minted under the fix.** **Seven of ninety-six
observations (7.3%) were SPURIOUS MINTS manufactured by the engine**, and the
same signature appears in `identity_seam_pilot2.json` (4 of 8 rows). The
predecessor's `codebook_axis` finding reproduces exactly and independently.

**The mechanism is one mechanism everywhere it appears: the defect suppresses
post-mint EXACT RECOGNITION, so an observation that should resolve to a held
identity instead mints a new one.** It does not change what is minted first; it
eats the step that would have recognised instead of minting.

*Pre-registration `VISION_FIXPOINT_COVERAGE_PREREG.md`, committed at **`c0569aa1`**
BEFORE any number existed. Seeds **98000–98999**, returned essentially unused
(a replication must not redraw).*

---

## 0. PROVENANCE — which binaries produced these numbers

| | |
|---|---|
| branch | **`worktree-agent-a10024f57a416923f`** — reported as observed |
| base / prereg commit | **`77e932f1`** / **`c0569aa1`** (prereg before any number) |
| **engine, FIX arm** | **`a1d350bbd23b`** — my own build, `scripts/engine_build.sh`. **Byte-identical to the predecessor's independently-built fix engine**, and built THREE times here (my worktree, the fix worktree, and again after restoring the revert) to the same hash |
| **engine, REVERT + trigger counter** | **`85f1f24567b4`** — same script, the early-out `if self.rule_dirty[j] { continue; }` restored in `dirty_by_writeset`, plus the counter of §1.2 |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed**, as its OWN step, on **every** engine before any number |
| **`strict=False` disclosure (§10 rule 1b)** | I deliberately loaded a REVERTED engine. Per the rule's own text I state so. **Note it did NOT require `strict=False`:** the revert is a change to the TREE's Rust source and the engine was rebuilt from it, so source and engine AGREE and the gate passes strictly in both arms |
| **engine fingerprints RE-VERIFIED at the end** | `85f1f24567b4` and `a1d350bbd23b`, **both real files, neither a symlink**. The canonical engine was rebuilt twice during my window; **my engines were unaffected** because both were built in trees I own and never borrowed |
| **oracle, FIX engine** | **212 passed / 10 skipped** (`scripts/rung7_vision_bench.sh`, no `data/`) |
| **oracle, REVERT engine** | **212 passed / 10 skipped** — **identical. The oracle has NO POWER to detect this defect**, now confirmed a second time and independently |
| machine / load | AMD Ryzen 5 9600X, 12 logical cores. **Heavily over-subscribed** (peak load ~26, partly my own two concurrent arms). Consequences quantified in §5.2 |

**Restoring the fix rebuilt to `a1d350bbd23b` bit-identically**, so the revert
was demonstrably undone. The arms report DIFFERENT hashes, so the revert
demonstrably took.

---

## 1. THE INSTRUMENTS — every one shown ABLE to fail BEFORE it was trusted

### 1.1 The engine arms

| engine | `tests/test_fixpoint_settle_migrated.py` |
|---|---|
| FIX `a1d350bbd23b` | **6 passed** |
| REVERT `85f1f24567b4` | **1 failed, 5 passed** — the documented defect, reproduced exactly |

### 1.2 The trigger counter, and its contribution measured at ZERO BY CONSTRUCTION

A `HARMFUL_SKIPS` counter compiled into the reverted engine, incrementing
exactly when the early-out skips a consumer for which the fixed code would have
cleared a **non-empty** cursor. Positive control on the reproduction:

| arm | Markers (expect 1) | `HARMFUL_SKIPS` |
|---|---|---|
| `pre_open_gate=False` (defective) | **0 — WRONG** | **1** |
| `pre_open_gate=True` (benign) | 1 — correct | 1 |

It fires on the arm that yields the wrong answer, so **`HARMFUL_SKIPS > 0` is an
UPPER BOUND on the defect's firing and `== 0` is a PROOF it could not have
affected the run.** Reading is via a PyO3 function that loads two atomics and
**does not boot a `Substrate`** — verified `(0, 0)` at bare import. The
predecessor's equivalent had a fallback that booted the machinery it measured
and had to measure its own contribution; mine cannot contribute by construction.

It also **reproduces the predecessor's counts exactly** on the scripts they
share (genmint 5519, agnosia 4106, blob_cost 864, continuous_pose 238, blink 0),
which is an independent replication of that instrument.

### 1.3 The comparator, self-tested against a KNOWN movement

Before trusting any "identical", the comparator was run against the
predecessor's committed `ARM_fix_codebook_axis.json` vs
`ARM_revert_codebook_axis.json` and **required** to find the known `n_exact`
movement. It found all five (`1,2,2,2,4` vs `0,0,0,0,0`). **A comparator that
has never reported a difference is not a comparator.**

### 1.4 Both filters are COUNTED, and neither is inert

The predecessor's hand-written timing-key filter excluded **zero** fields in
every comparison. Mine self-report:

| filter | fields excluded | verdict |
|---|---|---|
| **derived same-engine noise set** (FIX run twice) | **1,675** | live, and did most of the work |
| **provenance filter** (engine/commit/sha leaf keys) | **106** | live |

A provenance filter is unavoidable here because the two arms report different
engine hashes **by design**, so the same-engine noise set can never catch them.
It is declared, counted, and **it still leaked** — see §5.1.

---

## 2. THE SELECTION RULE, EXECUTED

> *a script is selected iff an AST walk finds a string literal naming an
> existing `results/*.json` AND the script contains a write call.*

Executed by `scripts/fixpoint_coverage_select.py`, never hand-listed. **160
result documents, 97 mapped, 63 unmapped, 95 producing scripts — full list
printed and committed.** Each selected script was then run under all three arms.

**Attribution does NOT trust that map.** The map over-maps (a script that merely
*reads* `results/X.json` matches the literal), so what each script produced was
decided by a **before/after snapshot of the whole `results/` directory**.

---

## 3. THE RESULT

### 3.1 Coverage, in both denominators

| | |
|---|---|
| result documents in tree | **160** |
| **documents COMPARED across three arms** | **79 ⇒ 49.4%** (predecessor: 11 of 147 ⇒ 7.5%) |
| **EXPOSURE COVERAGE** — harmful-skip triggers in compared documents / triggers observed across all runs | **489,896 / 498,028 ⇒ 98.4%** |
| total harmful skips observed (79 scripts, rc=0) | **498,028** |
| scripts selected / ran / NOT RUN | 95 / 79 / **16** |

**The exposure denominator is the one that matters**, and it is the correction
this rung makes to the predecessor's method: a document with zero exposure
contributes nothing, and 22 of my own nulls are exactly that.

### 3.2 The movers

**8 documents moved. 7 are engine-attributable; 1 is not.**

| document | exposure | what moved | kind |
|---|---|---|---|
| **`identity_seam_pilot.json`** | 1,582 | **`status` minted→recognized on 7 of 96 rows**; `residual_len` 36→0; `covered_count` 0→36 | **SEMANTIC — spurious mints** |
| **`identity_seam_pilot2.json`** | 2,110 | same signature, 4 of 8 rows | **SEMANTIC — spurious mints** |
| **`codebook_axis.json`** | 8,124 | `alive.n_exact` **[0,0,0,0,0] → [1,2,2,2,4]** + 504 sweep counters | **SEMANTIC — reproduces the predecessor exactly** |
| `video_probe_rerun_layers.json` | 1,357 | fit outputs, incl. `fit_cand_enum_vs_cells.r2` **None → 0.654** | **ANALYSIS OUTPUT** |
| `g5_responsiveness.json` | 4,275 | `term_evals_while_on` 919,764→962,509 + sweep counters | counters |
| `identity_cost_anatomy.json` | 816 | `cand_enum` 21→31 etc. | counters |
| `dim_infer_args.json` | 419 | `cand_enum` 21→31, `cand_enum_repeat` 3→13 | counters |
| `phi_measure.json` | **0** | 9 node-`first_id`/`last_id` fields | **NOT ATTRIBUTABLE — §3.4** |

### 3.3 THE HEADLINE — the defect MANUFACTURES IDENTITIES

`identity_seam_pilot.json`, identical inputs, the two engines:

| arm | `recognized` | `minted` |
|---|---|---|
| **REVERT (as landed)** | 89 | **7** |
| **FIX** | **96** | **0** |

Row 0, side by side:

| field | REVERT | FIX |
|---|---|---|
| `status` | `minted` | `recognized` |
| `covered_by` | `None` | `0_0` |
| `covered_count` | 0 | 36 |
| `residual_len` | 36 | 0 |

**A region that the fixed engine recognises as an identity it already holds, the
defective engine records as a brand-new identity with the entire span
unexplained.** This is the same mechanism as the `codebook_axis` finding — the
suppressed post-mint re-decode — but here it corrupts *per-observation identity
assignments*, not an aliveness counter. It is the more consequential of the two.

**SCOPE, STATED PLAINLY: these are the PILOTS.** `VISION_IDENTITY_SEAM_RESULTS.md`
labels `identity_seam_pilot{,2}` as *"pilots, burned seeds"*; its headline
(0.982 / 0.892 same-identity, floor 0.26–0.28) rests on
`identity_seam_{C1,C2}.json` and `identity_seam_rows_*`. **I did NOT run those,
and I do not claim they moved.** They are **NOT RUN** — see §4. **I make no
estimate of what they would show**, and a 7.3% spurious-mint rate in the pilots
is a reason to re-run them, not evidence about them.

### 3.4 One mover is NOT ATTRIBUTABLE, and I say so rather than count it

`phi_measure.json` moved on 9 node-id fields — but it ran with
**`HARMFUL_SKIPS = 0` and `run_rules_calls = 0`**, and `== 0` is a proof the
defect could not have acted. The document also carries **38** same-engine noise
paths, i.e. it is independently nondeterministic in node numbering. Two
replicates were not enough to characterise that. **It is reported as NOT
ATTRIBUTABLE, not as a mover** — exactly the case §10.6 of the pre-registration
reserved in advance.

### 3.5 The nulls, separated into EARNED and VACUOUS

| | |
|---|---|
| unmoved, **POWERED** (exposure > 0) — **earned nulls** | **47** |
| unmoved, **VACUOUS** (exposure == 0) — licenses nothing | **22** |

The largest earned nulls are substantial: **`redundancy_seed_map.json`
(343,014 harmful skips)**, `video_accum_calibrate.json` (17,467),
`waveiso_confirm.json` (11,682), `figadj_replacement.json` (10,304),
`genmint_measure.json` (5,519). **The defect fired 343,014 times while producing
`redundancy_seed_map.json` and the document is bit-identical.** That is what a
powered null looks like, and it is why the exposure accounting is not optional.

### 3.6 MY PREDICTION WAS HALF RIGHT, AND THE HALF THAT BROKE IS THE INFORMATIVE HALF

I predicted **H1, "few and concentrated"**, with proviso (a): *"I assume most of
the 95 scripts have LOW or ZERO exposure."*

- **RIGHT:** H1; movers are concentrated in terminal-state readouts, not in the
  counts that precede them; the movers are `status`/`n_exact` fields exactly as
  reasoned.
- **PROVISO (a) BROKEN, decisively.** **54 of 79 scripts have nonzero exposure**
  and the total is **498,028** — two orders of magnitude beyond the
  predecessor's ~11k across 12 scripts. `redundancy_trace_seeds.py` alone fires
  **343,014** times, 62× the largest figure in the previous rung. **The defect's
  blast radius across this tree is BROAD, not concentrated.** What is narrow is
  its *effect*: broad firing, few movements. That combination is the real finding
  of §3.5 — the engine hit this path half a million times and changed 7 documents.

## 4. Q-B — THE FOUR NAMED SEEDS, AND WHY THEY WERE NEVER GOING TO MOVE A NUMBER

Executing the selection rule answered the brief's question before any
measurement: **ZERO of the 95 result-producing scripts boots
`impasse_escalation`, `goal_derivation`, `nav_intent` or `grid_navigation`.**
They are booted by agent/demo scripts that write no `results/*.json`. **The four
largest static consumers have NO LANDED NUMBER that could move** — which is why
the predecessor could not reach them, and it is a fact about the seed→script
map, not a gap in either rung's diligence.

Their **live runtime exposure** is a different question, and it is large:

| script | seeds | `HARMFUL_SKIPS` |
|---|---|---|
| `maze_run.py` | grid_navigation | **106,935** |
| `arc_run.py` | goal_derivation + nav_intent + grid_navigation | **21,611** |
| `escalation_domain_agnostic.py` | impasse_escalation | 94 |
| `build_persona_faculty.py` | impasse_escalation | 35 |
| 6 further impasse/grid scripts | — | 1–21 each |
| `derive_loop.py` | goal_derivation | **NOT RUN (rc=1)** — counter read 83,685 before failure, reported for completeness, **not counted** |

**So the defect fires heavily in the live navigation path.** Whether it changes
navigation *behaviour* is **UNMEASURED** — these scripts emit no comparable
document, and I did not build one. That is the honest boundary, and it is the
single highest-value thing left undone.

## 5. WHAT I GOT WRONG

**5.1 I ran the two arms in two different DIRECTORIES, and it injected false
movers.** To halve wall-time I ran the FIX arms in a second worktree. Two
documents (`cut_mint.json`, `tripwire_repair.json`) then "moved" purely because
they record **absolute paths** — an engine path inside a `log` array and a seed
path in an audit field. My provenance filter missed them because it keys on the
*leaf name* (`log`, `seed`), not the value. **Caught by inspecting every mover
rather than counting them**, and excluded — but had I only tallied "10 moved",
two of the ten would have been my own harness. A same-directory sequential
design would not have had this failure mode; I bought speed with a confound.

**5.2 My wall-clock cutoff produced three ARM-ASYMMETRIC failures, and the
machine was over-subscribed.** 9 scripts hit the 600 s cutoff in some arm;
**`margin_measure` and `surface_assignment_measure` timed out in ONE arm and
succeeded in others**, and `timephi_measure` failed in one arm only. Under a
peak load of ~26 on 12 cores — **partly caused by my own two concurrent arms** —
**those reds are not attributable to anything.** They are correctly reported
NOT RUN by the comparator, but the cutoff itself was a poor instrument on a
contended machine, and `surface_assignment_measure` (8,252 exposure) was lost
from the comparison because of it.

**5.3 My first capture criterion would have destroyed the entire null.** I keyed
"the script produced this document" on the **content hash** changing. A
deterministic script re-run writes identical bytes, so every unmoved document
would have been recorded as *never produced* — the criterion would have
discarded precisely the nulls and kept only the movers, in a rung whose job is
to weigh them against each other. Caught within minutes because a script that
captured 1 document in a smoke test captured 0 on re-run. Fixed to mtime.
**Byte-identity is what this rung MEASURES; using it as a capture gate was a
category error.**

**5.4 My Q-B candidate selector matched ITS OWN SOURCE and executed itself.** It
selects scripts naming the four seeds; its own docstring names all four. It duly
ran itself. **A selector that matches itself** — §12, in a fresh costume, and I
wrote it despite the trap being named three times in this tree.

**5.5 The same Q-B selector then UNDER-selected the two biggest carriers.** It
required a *quoted* literal, but `arc_run.py` and `derive_loop.py` name
`goal_derivation`/`nav_intent` unquoted. My first Q-B summary therefore printed
`goal_derivation ran=0, total=0` and `grid_navigation total=21` — which reads as
a null and **is not one**. The true figures are 21,611 and 106,935. **I caught it
only because "0 ran" and "total 0" appearing together looked like a measurement
when it was an absence.** Zero-because-unmeasured and zero-because-measured are
different facts and my own output conflated them for one step.

**5.6 I started working in the SHARED canonical checkout.** My first six
commands ran in `/home/matt/ozma/internal/research/...`, not my worktree — the
exact shared-mutable-state hazard §11 exists to prevent, while other rungs were
live. Caught before any write; every subsequent action was in my own worktree.

**5.7 I misread a process as dead using a stale PID.** I checked the FIX runner
with the PID of its *first, failed* launch and reported "fix runner GONE" when it
was healthy. **I diagnosed process state with a probe that could not see the
process** — the same shape as the `pgrep` self-match, arrived at differently.
Corrected by verifying via log advancement.

**5.8 The selector's declared blind spot BIT, in the worst possible place.** 63
of 160 documents have constructed output paths and are unmapped — including
**`identity_seam_C1.json` / `identity_seam_C2.json`**, the confirmatory
documents behind the very result whose pilots produced my headline. Declaring a
blind spot in advance does not stop it costing you.

## 6. COVERAGE — WHAT THIS LICENSES AND WHAT IT DOES NOT

**Licensed:** the fixpoint fix moves **seven** landed documents, not one; the
mechanism is uniform (suppressed post-mint exact recognition) and in two
documents it manufactures spurious identities at **7.3%** and **50%** of rows;
47 nulls are genuinely powered, one of them at 343,014 firings; the oracle
cannot see any of it (212/10 both engines).

**NOT licensed:** any statement about the **81 documents I did not compare**,
including the confirmatory `identity_seam_{C1,C2}` documents that carry that
rung's published claim. **A document I did not execute is NOT REPORTED AS
UNCHANGED — it is reported as NOT RUN.** Nothing here licenses a claim about the
*behaviour* of the live navigation path despite its 100k+ firings, and 22 of my
own nulls are vacuous.

**Python-installed rules: the gap did not bite the MEASUREMENT** — differential
execution is agnostic to how a rule was installed — **but it still bites any
static claim** about which seeds are at risk, and I make none.

### The standing liability I hand on

**`scripts/identity_seam_measure.py` and `identity_seam_diagnose.py` (18,730
harmful skips, rc=1 in all three arms) were never compared.** Given that their
pilots show a 7.3% spurious-mint rate under the defect, **re-running the
confirmatory identity-seam documents under the fix is the highest-value
remaining work in this arc.** I did not do it and I do not predict its outcome.

## 7. LEDGER ROW (for the supervisor to apply — I did not edit `VISION_PROTOCOL.md`)

| 98000–98999 CLAIMED, RETURNED ESSENTIALLY UNUSED (a replication must not redraw; `check_claim` CLEAN, **497 unresolved sink sites**, under its two declared caveats) | **FIXPOINT COVERAGE — SEVEN LANDED DOCUMENTS MOVE, NOT ONE, AND THE PREDECESSOR FOUND THE SMALL CASE.** At **49.4% document coverage (79/160)** and **98.4% EXPOSURE coverage (489,896 / 498,028 harmful-skip triggers)**, **7 documents are engine-attributable movers** (+1 explicitly NOT ATTRIBUTABLE). **NEW HEADLINE: `results/identity_seam_pilot.json` is 89 recognized / 7 minted under the defect and 96 / 0 under the fix — 7 of 96 observations (7.3%) were SPURIOUS MINTS manufactured by the engine**, with `residual_len` 36→0 and `covered_by` None→`0_0`; `identity_seam_pilot2.json` shows the same signature on 4 of 8 rows. **THE MECHANISM IS UNIFORM: the defect suppresses post-mint EXACT RECOGNITION, so an observation that should resolve to a held identity mints a new one instead** — the `codebook_axis` `n_exact` `[0,0,0,0,0]→[1,2,2,2,4]` finding REPRODUCES EXACTLY AND INDEPENDENTLY, as do the predecessor's trigger counts (genmint 5519, agnosia 4106, blob_cost 864, blink 0). **SCOPE: these are the PILOTS; the confirmatory `identity_seam_{C1,C2}.json` were NOT RUN (constructed output paths — my selector's declared blind spot, biting at the worst possible place) and NO claim is made about them.** **THE PREDECESSOR'S RULE IS CONFIRMED AND THEN INVERTED: exposure is a property of the WORKLOAD, and it is BROAD — 54 of 79 scripts fire, 498,028 triggers total, `redundancy_trace_seeds` alone 343,014 (62× the previous largest). My pre-registered proviso "most scripts have low or zero exposure" is BROKEN. Broad firing, narrow effect: half a million firings changed 7 documents.** **47 nulls are EARNED (powered, exposure>0 — `redundancy_seed_map.json` bit-identical under 343,014 firings) and 22 are VACUOUS (zero exposure, licensing nothing).** **Q-B: ZERO of the 95 result-producing scripts boots `impasse_escalation`/`goal_derivation`/`nav_intent`/`grid_navigation` — the four largest STATIC consumers have NO LANDED NUMBER that could move; their LIVE exposure is large (`maze_run` 106,935, `arc_run` 21,611) and whether it changes navigation BEHAVIOUR is UNMEASURED.** **THE ORACLE CANNOT SEE ANY OF IT: 212/10 on both engines.** **EIGHT ERRORS: I ran the arms in two DIRECTORIES and injected 2 false movers via absolute paths (caught by inspecting every mover, not counting them); my wall-clock cutoff produced 3 ARM-ASYMMETRIC failures on a machine at load ~26 that I helped cause, losing `surface_assignment` (8,252 exposure) from the comparison; my first capture criterion keyed on CONTENT and would have silently discarded every unmoved document — the entire null — in a rung that weighs nulls; my Q-B selector MATCHED ITS OWN SOURCE and ran itself; the same selector then UNDER-selected `arc_run`/`derive_loop` and printed "ran=0, total=0" which READS as a null and is an ABSENCE; I began work in the SHARED canonical checkout; I declared a process dead from a STALE PID; and my declared blind spot bit on the confirmatory documents behind my own headline.** **STANDING LIABILITY HANDED ON: `identity_seam_measure.py` + `identity_seam_diagnose.py` (18,730 skips, rc=1 in all arms) were never compared, and their pilots' 7.3% spurious-mint rate makes re-running them the highest-value remaining work.** Gates: oracle **212/10 on both engines**; provenance **7 passed** on every engine as its own step; fixpoint control **RED on revert (1 failed/5 passed), GREEN on fix (6 passed)**; counter positive-controlled (fires on the wrong-answer arm, contributes 0 by construction); comparator self-tested against a KNOWN movement; **both filters counted and neither inert (noise 1,675 / provenance 106)**; restoring the fix rebuilt to `a1d350bbd23b` **bit-identically**, and both engine fingerprints were RE-VERIFIED as real files at the end. |
