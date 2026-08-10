# SEED ACCOUNTING AUDIT — RESULTS

**Pre-registration:** `VISION_SEED_ACCOUNTING_PREREG.md`, committed BEFORE any
measurement at **`72b79722`**.

**Branch actually seen:** `worktree-agent-a17e760b79a2d8af0` — NOT the intended
`gamma-substrate/seed-accounting`. The eighth consecutive rung to run under an
auto-generated name.

**Base HEAD:** `c7a57ec8a0e532a9937906fcd00cd7805fce3d0e` (the resolution
rung's own ledger-row commit — the defect under audit).

**Block:** 82000–82999. **Consumed: 82000–82049 and 82300–82349** (100 seeds,
by the self-audit fixture). 82050–82299 and 82350–82999 CLEAN.

No Rust. No Term. No seed manifest. No constant. Two new scripts and one gate.

---

## THE HEADLINE

**THE LEDGER IS NOT FICTION, AND IT IS ALSO NOT LOAD-BEARING.**

Every ledger-scale seed the tree measurably draws is accounted for, and there
is **exactly ONE cross-rung seed collision in 3,241 ledger-scale seeds — and it
is DELIBERATE, protocol-mandated, and documented in the source that causes it.**
So the defect that prompted this rung is a **one-off in its collision aspect**.

But the second half of the answer is the uncomfortable one, and it was
pre-registered as such:

**THE LEDGER RECORDS DECLARATIONS, AND DECLARATIONS OVER-STATE CONSUMPTION BY
ROUGHLY 10× AT THE MEDIAN.** Of 108 declared blocks, **58 measure ZERO
consumption** and the median fill of the rest is **0.100** — a declared
1000-wide block typically consumes 100 seeds. **The ledger cannot distinguish
"drew the whole block" from "drew 100 scattered seeds inside it", which is
precisely the condition that let the resolution rung's K arm be allocated on
top of seeds the same rung had already consumed.** The bookkeeping is honest;
it is simply not at a resolution that can protect a successor.

**AND THE LEDGER IS NOT THE ONLY SEED NAMESPACE.** A second, entirely
undeclared convention runs in parallel: **date literals** (`20260711`,
`20260802`, …) used directly as seeds in 30+ scripts, plus **conventional low
seeds** (`default_rng(0)` and friends) in **492 of 590 files that draw any
resolvable seed at all**. Neither is in the ledger, and neither needs to be —
but no collision check that consults only the ledger sees either.

---

## PHASE 1 — THE INSTRUMENT, AND WHAT IT CANNOT SEE

`scripts/seed_audit.py`. An AST walk with abstract interpretation over the
domain `frozenset[int] | UNKNOWN`. It resolves module-level constant
propagation, `range()` loop-variable expansion, tuple-unpacking loop targets
(`for label, off in (("G2c",700),("G2t",800))`), integer folding, and
**intra-file interprocedural** binding of seeds passed as arguments.

**It is not a substring scan, and this is load-bearing** (§12: a selector that
matches by substring is not a selector; substring selectors have failed four
times in this arc). `resolution_scale_measure.py` contains **no integer literal
in 79001–79999** anywhere in its code — every one of its 200 draws is derived.

### WHAT IT CANNOT SEE — measured limits, not prose

`unknown_sinks = 481` across the tree: 481 seed-sink call sites whose argument
could not be resolved. **These are COUNTED, never silently dropped.** The tool
under-reports; it never over-reports. Two of the limits are asserted as tests
(`test_unresolvable_seeds_are_reported_unknown_not_silently_dropped`,
`test_module_boundary_is_a_declared_blind_spot`) so they are tested properties
rather than claims:

1. **CLI args, `os.environ`, config files** — runtime values. Invisible.
2. **Data-derived seeds** — `hash(x)`, `len(pool)`, timestamps. Invisible.
3. **Cross-MODULE constants** — interprocedural analysis is INTRA-FILE only. A
   `BLOCK` imported from another module and seeded is invisible.
4. **Library/adapter draws** reached from a script but in an unanalysed file.
5. **Consecutive draws from one generator.** `default_rng(S)` burns an
   unbounded stream downstream of S. **The ledger's unit is the SEED INTEGER
   and that is what is measured.** A rung reserving 1000 integers and seeding
   once at the base draws ONE seed by this measure. **This is a definitional
   choice, declared in the prereg, not an oversight** — and it is the single
   most important caveat on every Class-A number below. Under the other reading
   ("a block reserves a namespace"), over-declaration is not over-declaration
   at all, merely unused headroom.
6. **Non-Python seeds** — shell, Rust, notebooks. Not scanned.
7. **Expressions exceeding `ENUM_CAP = 20000`** — abandoned as UNKNOWN rather
   than truncated, because a truncated set would under-report a real collision.

**Coverage actually achieved:** 8 roots (`scripts domains substrate tools
runners benchmarks demos tests`), **0 parse errors**, 792 files with at least
one seed sink, 590 files with at least one *resolvable* seed, 3,344 distinct
seed integers recovered.

---

## PHASE 1b — THE SELF-AUDIT (V1), REPORTED BEFORE ANYONE ELSE'S

A static analyser draws no seeds of its own, which is **exactly the vacuous
case §1.1 warns about — a tool reporting zero everywhere and a clean tree look
identical.** So this rung spent part of its own block deliberately, in
`scripts/seed_audit_selfcheck.py`, using the same three constructs that made
the resolution rung's consumption invisible.

| | |
|---|---|
| **DECLARED** | 82000–82999 |
| **MEASURED** | **82000–82049, 82300–82349** (100 seeds, 2 scattered sub-ranges) |
| **unknown sinks** | 0 |
| **declared ⊇ measured** | **PASS** |
| **negative control** (declare 82000–82099) | **FAILS as required**, naming 82300–82349 |

**My own consumption has the same shape as the defect I am auditing: two
scattered sub-ranges inside one declared block, 10% fill.** Had I written only
`SEED_BLOCK = 82000` in a results file, I would have mis-stated it the same way
the resolution rung did.

---

## PHASE 2 — THE THREE-CLASS LEDGER AUDIT

Ledger parsed from `VISION_PROTOCOL.md`'s burned-seed table: **92 rows, 108
declared blocks** (the brief's estimate of ~138 counts row mentions rather than
distinct ranges). Lowest declared block starts at **1100**; highest ends at
**80999**.

### CLASS A — declared ⊋ measured (OVER-DECLARED)

| statistic | value |
|---|---|
| declared blocks | **108** |
| blocks measuring **ZERO** consumption | **58** (53.7%) |
| blocks with non-zero measured consumption | 50 |
| **median fill** (measured / declared width) | **0.100** |
| min fill | 0.0010 |
| blocks at 100% fill | 15 |
| blocks under 5% fill | 20 |

**P2 HOLDS.** Over-declaration is the dominant class, and by an order of
magnitude at the median.

**The 58 zero-measured blocks are NOT all detector failures, and I do not
conflate them.** Three distinct causes, and the prereg required me to separate
them: (a) rungs that genuinely consumed nothing **by design** — the k-scope and
block-unit re-analysis rungs, which the ledger itself records as "CLAIMED, ZERO
CONSUMED (returned intact)"; (b) rungs whose runner draws through one of the
seven blind spots above; (c) rungs whose runner is no longer in the tree.
**I can distinguish (a) from (b)+(c) only where the ledger says so in prose.**
This is a real limit on the Class-A count and I am not going to dress it up:
**the honest statement is that at most 50 of 108 declared blocks are confirmed
consumed from source, and the status of the other 58 is not established by this
rung.**

### CLASS B — measured ⊄ declared (DREW OUTSIDE THE BLOCK)

**373 ledger-scale seeds fall in NO declared block**, in 34 contiguous runs.
Decomposed:

| run | n | drawn by | reading |
|---|---|---|---|
| **38000–38099** | **100** | `scripts/det1_measure.py` | **REAL: an undeclared 100-seed block.** 37000 and 39000 are declared; 38000 is not. |
| **40000–40099** | **100** | `scripts/continuous_pose_measure.py` | **REAL: an undeclared 100-seed block.** 39000 and 41000 are declared; 40000 is not. |
| 82000–82049, 82300–82349 | 100 | `seed_audit_selfcheck.py` | **MINE** — correctly flagged; my block is not in the ledger because I do not edit §11 (supervisor amends). |
| 1000–1019 | 20 | `tests/test_vision_maps_migrated.py` | AMBIGUOUS — below the lowest declared block (1100). |
| 90000–90002, 99991, 100003 | 5 | 3 scripts | above the ledger's top. |
| ~15 date literals | ~40 | 30+ scripts | the parallel convention, never intended as ledger draws. |
| 1234, 12345, 1451, 2024, 2026, 2748, 3243, 3567, 789996, 12648430 | 10 | many | conventional magic constants. |

**P5 HOLDS, and it is stronger than predicted: TWO FULL 100-SEED BLOCKS
(38000–38099, 40000–40099) WERE CONSUMED WITHOUT EVER BEING DECLARED.** These
are genuine accounting errors — not collisions today, but a future rung that
reads the ledger, sees no 38000 row, and claims 38000–38999 would collide with
`det1_measure.py`'s 100 consumed seeds and never know.

**CONFIRMED THREE WAYS, because this is the rung's strongest claim:**

1. **`38000` and `40000` each appear ZERO times in the whole of
   `VISION_PROTOCOL.md`.** Not in a row, not in the FREE list, nowhere.
2. **Neither runner is named anywhere in the ledger** — `det1_measure` and
   `continuous_pose_measure` both return 0 occurrences.
3. **The source shows the authors WERE seed-conscious and the ledger step was
   simply skipped.** Both scripts carry the comment:

   ```python
   # noise — seeds 38000-38099 (never used)
       rng = random.Random(38000 + i)
   ```

   *"(never used)"* is the author verifying the range was free before taking
   it. **They checked; they just never wrote it down.** That is the whole
   failure mode in one line: **the ledger is a write-side discipline with no
   read-side enforcement, so a correct free-range check leaves no trace.**

### CLASS C — GENUINE COLLISIONS

155 seeds are drawn by two or more distinct files. Decomposed — and the
decomposition is the result:

| class | seeds | reading |
|---|---|---|
| script ↔ **its own gate test** | **88** | **NOT a collision.** The gate re-runs the rung's own measurement at the rung's own seed. That is reproduction, and it is correct. |
| **date-literal convention** | 15 | two scripts written the same day both seeded with that date. Outside the ledger entirely. |
| conventional magic (`1234`, `12345`, …) | 2 | ditto. |
| **REAL script ↔ script** | **50** | **EXACTLY ONE PAIR** — see below. |

**The one real pair: `invariant_comparator_measure.py` and
`verdict_comparator_measure.py` both draw 57400–57449.**

**AND IT IS DELIBERATE.** `verdict_comparator_measure.py` sets
`SEED_BLOCK = 70000` for its confirmatory run and, separately:

```python
#: The PILOT uses the invariant-comparator rung's ALREADY-BURNED block, per
#: protocol section 3.3 (a power pilot must not consume confirmatory seeds).
PILOT_SEED_BLOCK = 57000
```

§3.3 of `VISION_PROTOCOL.md` requires exactly this: *"n, FIXED IN ADVANCE by a
power analysis on a pilot restricted to **already-burned** seeds."* The ledger
itself records other rungs doing the same (`0–13, 3000 (again)`; `0–7 (again)`).

**P4 HOLDS. Genuine unexplained cross-rung collisions: ZERO.**

---

## PHASE 3 — BLAST RADIUS

Phase 3 runs only for genuine collisions. There is one candidate, and it
resolves to **NO EXPOSURE ON ANY LANDED CONFIRMATORY RESULT** — but the
exposure it *does* carry is worth naming precisely, because "deliberate" is not
the same as "free".

**The collision:** the verdict rung's **power pilot** (`--pilot`, C2,
`N_PILOT_BASE = 10`) shares its distant-frame probe draws (`random.Random(
57000 + 400 + t)`, which selects the A2 distractor frame) with the invariant
rung's **published confirmatory arms** on the same corpus.

**Did any landed result depend on the independence this breaks?**

- **NO for the verdict rung's headline.** Its confirmatory arms (`run_c3`,
  `run_video`) run on `SEED_BLOCK = 70000`, **disjoint from 57000**. The
  V0→V1→V2→V3 ladder and the `+0.1786` MISID / `+0.7639` TIES intervals are
  measured entirely on 70000-series draws. **This is exactly the separation
  §3.3 exists to produce, and it held.**
- **NO for the invariant rung.** It ran first and published on its own block;
  a later pilot reading the same seeds cannot reach backwards into it.
- **THE ONE REAL EXPOSURE, NAMED:** the verdict rung's **power calculation** —
  the variance estimate that FIXED ITS `n` — was computed on data whose
  distractor draws are identical to those of the invariant rung's published
  arms. So `n` is not statistically independent of the earlier published
  numbers. **The consequence is bounded and small: a shared distractor draw
  perturbs the variance ESTIMATE used for sizing, not the confirmatory
  measurement, and §3.3 accepts precisely this trade** (it prefers reusing
  burned seeds over spending confirmatory ones). **I name it and stop; I do not
  re-litigate either rung.**

**No control arm shares a seed with its test arm anywhere in the tree.** No
"replication" reuses its original's seed. Those were the two exposures worth
hunting and neither exists.

---

## PREDICTIONS — 4 RIGHT, 1 WRONG, AND THE WRONG ONE IS THE USEFUL ONE

| | prediction | outcome |
|---|---|---|
| **P1** | tool recovers the four sub-ranges + K-arm collision blind | **RIGHT** — exactly `(79200,79249) (79400,79449) (79700,79749) (79800,79849)`, 0 unknown sinks, no literal in code. |
| **P2** | over-declaration dominant; median fill <10%; majority of blocks zero | **RIGHT** — median fill 0.100, 58/108 zero. |
| **P3** | `default_rng(0)` is a red herring — conventional seeds outside the ledger | **RIGHT, and bigger than expected** — 492 of 590 seed-drawing files use sub-1100 seeds; seed 0 alone in 264 files. Not vestigial blocks; a different namespace. |
| **P4** | 0–3 genuine collisions | **RIGHT** — one pair, and it is protocol-mandated. |
| **P5** | ≥1 measured-outside-declared case | **RIGHT, and understated** — I expected stragglers; found **two undeclared 100-seed blocks** (38000–38099, 40000–40099). |

**WHAT I GOT WRONG, and it is the finding that matters most:** I framed the
audit as a hunt for **collisions**, and predicted the interesting answer would
be found there. It was not. **The real defect is CLASS B — two blocks consumed
with no declaration at all — and it is invisible to every check the project
currently runs, including this rung's own gate**, because a `declared ⊇
measured` assertion needs a *declaration* to check against and these have none.
The gate I was asked to leave behind would not have caught either one.

---

## WHAT WENT WRONG IN THIS RUNG

**MY OWN GATE WENT RED ON A DOCSTRING — the fourth time in this arc a substring
selector has failed, and I walked straight into it.** My first version of
`test_recovers_resolution_rungs_four_scattered_subranges` asserted
`"79200" not in src` to prove the number was not a literal. It went red: the
string **is** in the file — in the docstring, where the resolution rung recorded
its own post-hoc audit. **I fixed the SELECTOR, not the gate** (§5): the
assertion now walks AST integer constants and asserts that **no literal in
79001–79999 appears in code at all**, which is the claim I actually meant and
is strictly stronger. Prose is not what the analyser reads.

**A path-prefix bug in my own summary script** briefly reported "script ↔ its
own test collisions: 0" because I matched `'/tests/'` against paths of the form
`tests/…`. Caught by noticing the number contradicted an earlier run of the
same analysis (67 vs 0). Corrected; no number from the buggy pass is reported.

**A pre-existing test failure, verified NOT mine:**
`tests/test_dynamic_thresholds_migrated.py::test_global_contradiction_reopen_provenance_round_trips`
fails at base `c7a57ec8` with my files removed and the working tree stashed.
Reported, not fixed — it is outside this rung's scope.

---

## THE GATE LEFT BEHIND

`seed_audit.check_block` — one line, runnable at pre-registration time, before
any seed is spent:

```python
from seed_audit import check_block
ok, outside = check_block(["scripts/my_rung.py"], 82000, 82999)
assert ok, f"draws outside declared block: {outside}"
```

Also available as a CLI: `python3 scripts/seed_audit.py --check 82000 82999
scripts/my_rung.py` (exit 1 on violation).

**Positive-controlled, per §1.1.** `tests/test_seed_accounting_migrated.py`
(**12/12**) proves the detector fires and goes quiet:

- `test_the_gate_can_actually_fail` — declaring a block too narrow goes RED.
- `test_planted_collision_is_detected_and_removal_restores_clean` — a planted
  script drawing `BASE + 210 + t` into the resolution rung's consumed range is
  detected as a collision; **removing it restores clean.**
- `test_unresolvable_seeds_are_reported_unknown_not_silently_dropped` and
  `test_module_boundary_is_a_declared_blind_spot` — the blind spots are TESTED
  properties, not prose.

**What this gate would and would not have caught.** It **would** have caught
the resolution rung's K-arm collision, at pre-registration time, before the
rung ran — that was the brief. It would **not** have caught the two undeclared
blocks (Class B), because it checks measured against a declaration and those
have none. **Closing that hole needs a ledger-wide sweep, not a per-rung
assertion** — `scripts/seed_ledger_audit.py` is that sweep, and it is left
behind too, but nothing currently runs it on a schedule.

---

## RECOMMENDATIONS FOR §11 (the supervisor amends; I do not edit the protocol)

1. **Add rows for 38000–38099 (`det1_measure.py`) and 40000–40099
   (`continuous_pose_measure.py`).** Both are consumed and undeclared.
2. **Add a row for 82000–82049 + 82300–82349** (this rung).
3. **Re-allocate the resolution rung's K arm.** Its declared 79200–79399
   overlaps 79200–79249, already consumed. 79500–79699 and 79850–79999 are
   measurably clean.
4. **Record MEASURED sub-ranges in ledger rows, not just the declared block** —
   the resolution rung's own corrected row already does this and is the model.
5. **Note that date literals and sub-1100 seeds are a separate, deliberate
   namespace** outside the ledger, so future collision checks do not chase them.

---

## VERIFICATION (§9, §12.3)

- **PROVENANCE GATE RUN AS ITS OWN STEP, BEFORE ANY NUMBER IN THIS DOCUMENT.**
  `pytest -k provenance` → **694 passed, 1 failed**. The one failure,
  `test_dynamic_thresholds_migrated.py::test_global_contradiction_reopen_provenance_round_trips`,
  is **PRE-EXISTING at base `c7a57ec8`** — verified by removing this rung's two
  untracked scripts and stashing the working tree, where it fails identically.
  Not caused here, not fixed here.
- **Endpoint guard specifically:** `tests/test_provenance_endpoint_guard_migrated.py`
  → **630 passed**. Both provenance endpoints in this document are pinned
  SHAs (`72b79722` prereg, `c7a57ec8` base); **neither is `HEAD`**.
- **New gate:** `tests/test_seed_accounting_migrated.py` → **12/12**, with the
  planted-collision positive control and the can-actually-fail negative control.
- **ORACLE:** `bash scripts/rung7_vision_bench.sh` → **212 passed, 10 skipped**
  in 165s. **`data/` is ABSENT in this worktree** (verified by `ls`), so this is
  the documented **212/10 no-`data/` condition**, not the 222 figure. Per §10.2,
  a fresh worktree lacks `data/` because it is gitignored.
- **No Rust, no Term, no seed manifest, no constant, no engine build** — this
  rung is static analysis of source and touches no runtime.

## BOUNDS (§8)

- **Static analysis only.** Seven declared blind spots; 481 unresolved sink
  sites. Every Class-A and Class-C number is a LOWER bound on consumption and
  therefore a LOWER bound on collisions.
- **The seed-INTEGER definition is a choice** (blind spot 5). Under a
  "block reserves a namespace" reading, Class A is not over-declaration.
- **Class-A zero-blocks are not diagnosed.** At most 50 of 108 blocks are
  confirmed consumed from source; the other 58 are unresolved between
  "genuinely unspent", "invisible to the tool", and "runner deleted".
- **Files, not rungs.** Collisions are defined file-wise; the script↔test and
  §3.3-pilot classifications were made by READING the files, not computed.
- No claim is made about seeds consumed by rungs whose runners are absent from
  this tree.
