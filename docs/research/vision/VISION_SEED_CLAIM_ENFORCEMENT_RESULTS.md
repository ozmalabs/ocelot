# SEED CLAIM ENFORCEMENT — RESULTS

**Pre-registration:** `VISION_SEED_CLAIM_ENFORCEMENT_PREREG.md`, committed
BEFORE any measurement at **`0d7dbef5d1782f067baea3a77153135e8cf254b5`**.

**Branch actually seen:** `worktree-agent-affadc338e794482c` — NOT the intended
`gamma-substrate/seed-claim-enforcement`. **The ninth consecutive rung to run
under an auto-generated name.**

**Base HEAD:** `e8bf398747c4b14f54a8519d234b0667f246438a`.

**Block: 90000–90999. CONSUMED: ZERO.** Measured with this rung's own
instrument on its own two files: no resolvable seed integer at all. This is
TOOLING; it draws nothing.

No Rust. No Term. No seed manifest. No constant. No engine build. One new
script, one new gate.

---

## THE HEADLINE

**ENFORCEMENT IS CHEAP, AND IT IS NOW WIRED — AND THE FIRST REAL USE OF IT
REJECTED THE SUPERVISOR'S OWN SEED ALLOCATION TO THIS RUNG.**

The claim check was asked whether block **90000–90999** was free. It is not:
**`scripts/rung7_snr_pilot.py` measurably draws 90000, 90001, 90002**, and no
ledger row declares them. **The ledger says that block is free. The tree says
it is not.** The tool found the defect it was built to find, in its own
allocation, on its first invocation — which is the strongest evidence available
that it is not vacuous.

The design point the prior rung established, now implemented: **the
authoritative question is not "is this range DECLARED?" but "is this range
measurably DRAWN?"** `check_block` (write-side) needs a declaration and is
therefore blind to a block that has none. `check_claim` (read-side) needs
nothing but the tree.

---

## THE MECHANISM

`scripts/seed_claim.py`. One line, at pre-registration time, before a seed is
spent:

```python
from seed_claim import check_claim
ok, report = check_claim(90000, 90999)
assert ok, report
```

CLI: `python3 scripts/seed_claim.py 90000 90999` (exit 1 if occupied);
`python3 scripts/seed_claim.py --sweep` for the whole-tree Class-B sweep.

Three verdicts, fixed in the prereg and not redefined after seeing results (§5):

| verdict | meaning |
|---|---|
| **OCCUPIED** | a seed in `[lo,hi]` is measurably drawn by some file. Every seed and file named. |
| **DECLARED ELSEWHERE** | overlaps a §11 row belonging to another rung, **even at zero measured consumption** — 58 of 108 declared blocks measure zero, and measuring zero is not drawing nothing (caveat 1). |
| **CLEAN** | neither — **and this means NO COLLISION DETECTED, never NO COLLISION EXISTS.** |

Two helpers, both driven by the cases this rung actually hit:
`first_clean_subrange(lo, hi, width)` (the block you were given is partly
occupied — here it returned **90003–90102**), and `undeclared_runs()`, the
sweep that needs no declaration to check against.

**Cost (P4): a cold whole-tree scan is 10.3 s; cached follow-up queries are
1 ms.** The full 13-test gate runs in **11.8 s**. That is bench-tolerable, and
it settles the cost half of the decision rule.

---

## THE POSITIVE CONTROL — AND IT ACTUALLY FIRED, TWICE, ONE OF THEM ON HISTORY

§1.1: a checker that finds nothing and a clean tree are indistinguishable.

**Control 1 — REAL DATA, not a plant.** The two blocks the seed-accounting rung
found consumed with no declaration:

| range | verdict | occupying file | ledger says |
|---|---|---|---|
| **38000–38099** | **REFUSED**, 100 seeds | `scripts/det1_measure.py` | **no declaration — FREE** |
| **40000–40099** | **REFUSED**, 100 seeds | `scripts/continuous_pose_measure.py` (+ its own gate test) | **no declaration — FREE** |

Both are asserted in the gate, *together with* the assertion that the ledger
still declares neither — so the test proves the tool adds information the
ledger does not carry, and will itself go red the day that stops being true.

**Control 2 — A PLANT, IN THE REAL TREE, WATCHED FIRING AND GOING QUIET.** A
script drawing `SEED_BLOCK + 600 + t` was added under `scripts/`. The standing
gate `test_undeclared_consumption_does_not_grow` **went RED**, naming
`91600-91649 n=50 scripts/_planted_undeclared_rung.py`, with both caveats in
the failure text. Removing the file restored **13/13 green**. **The literal
`91600` appears zero times in the planted source** — no substring selector
could have found it (§12); it is recovered by constant propagation and
`range()` expansion.

**MY FIRST PLANT DID NOT FIRE, AND THE REASON MATTERS.** I first planted at
`55000 + 600 + t`. The gate stayed green — correctly: **55000–55999 IS
declared**, so those draws are not Class B. The gate was right and my control
was wrong. Had I not checked *why* the silence occurred, I would have recorded
a dead instrument as a pass — the exact failure §1.1 describes. The claim arm
*did* refuse that range, on the collision path (`REFUSED … 55600:
_planted_undeclared_rung.py, crossframe_identity_measure.py`), which is how the
two arms are meant to be complementary.

---

## WHERE IT RUNS, AND WHY

**Wired as a migrated-suite gate: `tests/test_seed_claim_migrated.py`, 13/13.**
It is collected by `pytest -k migrated`, the project's documented regression
bench.

**NOT added to `scripts/rung7_vision_bench.sh`, deliberately.** That script is
rung 7's explicit file list and its count IS the protocol's oracle (222 with
`data/`, 212/10 without). Adding a file would move a protocol-load-bearing
number I do not own (§11 rule 4). **Recommended to the supervisor**, who owns
that decision — the argument for is that the oracle is the number people
actually run; the argument against is that a seed-accounting gate is not a
vision test and the oracle should stay a vision measurement.

The gate has two jobs:

1. **Keep the instrument alive** — the real-data and plant controls above.
2. **Enforce, standing:** `test_undeclared_consumption_does_not_grow` holds a
   **frozen baseline of 7 ledger-scale runs** measured outside every declared
   block at `0d7dbef5`. A new entry means a rung consumed seeds with no §11
   row. `test_the_baseline_is_not_stale` fails in the other direction, so the
   allowlist cannot quietly become a graveyard.

**THE FROZEN BASELINE — every one is a real accounting gap:**

| range | n | drawn by |
|---|---|---|
| 1000–1019 | 20 | `tests/test_vision_maps_migrated.py` — below the ledger's lowest block (1100); predates the convention |
| **38000–38099** | **100** | `scripts/det1_measure.py` — **§11 row recommended by the prior rung, NOT YET APPLIED** |
| **40000–40019 / 40020–40099** | **100** | `scripts/continuous_pose_measure.py` (+ gate test) — **row recommended, NOT YET APPLIED** |
| **90000–90002** | **3** | `scripts/rung7_snr_pilot.py` — **found by this tool, in this rung's own allocated block** |
| 99991 | 1 | `scripts/self_directed_speech_loop.py` |
| 100003 | 1 | `scripts/jabberwock_handwriting_feasibility.py` |

Date literals (≥ 20 000 000) and the ten conventional magic constants are
excluded by rule, per the prior rung's recommendation 5 — otherwise the gate
chases a namespace that was never meant to be in the ledger.

**P5 reconciles exactly.** I measure **273** undeclared seeds; the prior rung
measured **373**. The difference is **exactly the 100 seeds of its own
`seed_audit_selfcheck.py`**, which the supervisor has since declared in §11
(recommendation 2, applied). `373 − 100 = 273`. My run count (49 vs 34) is
higher only because I additionally split a run when the drawing file-set
changes — a definitional difference, visible as the 40000–40019 / 40020–40099
split.

---

## THE TWO CAVEATS, CARRIED INTO THE OUTPUT

Both are printed with **every** verdict, pass or fail, and both are asserted as
properties of the verdict text — not left in a document a future reader will
not open:

```
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Every verdict also prices its own silence: *"795 files with seed sinks; **481
UNRESOLVED sink sites** tree-wide (counted, not discarded)."*
`test_a_clean_verdict_still_reports_unresolved_sinks` asserts a clean verdict is
never bare — a CLEAN with zero unresolved sinks would mean the scanner had not
run.

Caveat 1 is also **load-bearing in the logic**, not only in the text: it is why
a declared-but-unmeasured block is still REFUSED.

---

## PREDICTIONS — 5 of 5 RIGHT

| | prediction | outcome |
|---|---|---|
| **P1** | fires on 38000/40000; a ledger-only check calls them free | **RIGHT** — 100 seeds each, both files named, both still undeclared |
| **P2** | **my own block 90000–90999 is not clean** | **RIGHT** — 90000–90002, `rung7_snr_pilot.py`. The tool rejected my own allocation |
| **P3** | plant flips a clean range; removal restores it | **RIGHT** — but see the first plant, which did not fire and was my error, not the gate's |
| **P4** | scan cost single-digit-to-low-tens of seconds | **RIGHT** — 10.3 s cold, 1 ms cached, 11.8 s for the whole gate |
| **P5** | undeclared runs > 0, matching the prior rung within tree drift | **RIGHT, and exactly** — 273 = 373 − 100, the difference fully attributed |

Being right five times is weaker evidence than being wrong once informatively,
and the informative thing here is **not** in the prediction table — it is the
plant that silently passed (above).

---

## RECOMMENDATIONS FOR §11 — the supervisor amends; I do not edit the protocol

**The prior rung's five, re-reported with my read on which are load-bearing.
The supervisor applied #2 and has not applied #1, #3, #4, #5** — verified: 82000
now has a row; `38000` and `40000` still appear nowhere in `VISION_PROTOCOL.md`.

| # | recommendation | status | my read |
|---|---|---|---|
| **1** | rows for **38000–38099** (`det1_measure`) and **40000–40099** (`continuous_pose_measure`) | **NOT APPLIED** | **LOAD-BEARING — apply first.** These are live: a future rung reading the ledger sees 38000 free and would collide. My gate now holds them as known-undeclared, which *documents* the gap; only the §11 row *closes* it. |
| 2 | row for 82000–82049 + 82300–82349 | **APPLIED** | done |
| **3** | re-allocate the resolution rung's K arm (declared 79200–79399 overlaps consumed 79200–79249) | **NOT APPLIED** | **LOAD-BEARING.** A known overlap left standing. 79500–79699 and 79850–79999 were measured clean. |
| **4** | record **MEASURED** sub-ranges in ledger rows, not just the declared block | **NOT APPLIED** | **LOAD-BEARING, and the highest-leverage of the five.** This is the root cause: declarations at ~10× true consumption are what makes the ledger unusable for a successor. Cheap now — `--sweep` and `check_claim` produce the measured ranges mechanically. |
| 5 | note that date literals and sub-1100 seeds are a separate namespace | **NOT APPLIED** | **COSMETIC IN THE LEDGER, LOAD-BEARING IN CODE — and I have already implemented it.** The exclusion rule lives in `test_seed_claim_migrated.py`. A §11 note is documentation of a behaviour that now exists either way. |

**Three of my own, in priority order:**

| # | recommendation | my read |
|---|---|---|
| **6** | **Add a row for 90000–90002 (`scripts/rung7_snr_pilot.py`), and STOP ALLOCATING 90000–90999 as a fresh block.** | **LOAD-BEARING and immediate.** This block was handed to me as free. It is not. Any future allocation above the ledger's top (80999) is unchecked territory — 99991 and 100003 are drawn up there too. |
| **7** | **Add to §3: a pre-registration must record the output of `check_claim(lo, hi)` for its block.** | **LOAD-BEARING — this is the actual read-side discipline.** The tool only enforces if someone runs it. §3.4 already demands "confirmatory seeds never used for anything"; this makes that clause *checkable* instead of an honour system. One line in the prereg. |
| 8 | Note in §11 that the ledger's authority is **measured occupancy**, and a declaration is a *claim about* the tree, not the tree. | Framing, but it is the framing that makes 6 and 7 obvious rather than bureaucratic. |

---

## VERIFICATION (§9, §12.3)

- **PROVENANCE GATE RUN AS ITS OWN STEP, BEFORE ANY NUMBER IN THIS DOCUMENT AND
  BEFORE THE PREREG WAS WRITTEN.** `pytest -q tests/ -k provenance` → **698
  passed, 1 failed**. The failure,
  `test_dynamic_thresholds_migrated.py::test_global_contradiction_reopen_provenance_round_trips`,
  is the SAME one the seed-accounting rung recorded as pre-existing at base
  `c7a57ec8`; **my working tree contained zero edits when it ran.**
- **Endpoint guard:** `tests/test_provenance_endpoint_guard_migrated.py` →
  **635 passed.** Both endpoints in this document are pinned SHAs
  (`0d7dbef5` prereg, `e8bf3987` base); **neither is `HEAD`.**
- **New gate:** `tests/test_seed_claim_migrated.py` → **13/13**, with the
  real-data positive control, the plant-and-remove control, and the standing
  baseline in both directions.
- **Prior gate untouched and still green:** `test_seed_accounting_migrated.py`
  + this rung's → **25 passed**.
- **ORACLE — AND IT IS NOT CLEAN, AND IT IS NOT MINE.**
  `bash scripts/rung7_vision_bench.sh` → **210 passed, 2 failed, 10 skipped**
  in 213 s. `data/` is **ABSENT** (verified), so the reference is the documented
  **212/10** condition (§10.2). The two failures are both in
  `tests/test_engine_provenance_migrated.py`, verdict **`source_match:
  DIVERGED`**. **Attribution:** the loaded engine is the CANONICAL tree's
  (`engine_tree` ≠ `this_tree`), and its `engine_source_fingerprint`
  (`891b1f7ffe43`) no longer matches this tree's `source_fingerprint`
  (`bf2ad4fb7d6a`). **`git diff e8bf3987 HEAD -- runners/` is EMPTY — this rung
  changed no Rust**, and `stale_rust` is `[]`. Engine provenance was **GREEN in
  the same worktree earlier in this session** (it is inside the 698-passed
  provenance run above). A concurrent rung changed Rust and/or rebuilt the
  shared engine underneath me: **§11 rule 5 exactly** — *"long-running
  measurement is not a lock."* I did not touch the canonical tree to
  investigate further, per the standing rule. **This rung's own result does not
  depend on the binary:** it is static analysis of Python source and imports no
  engine.

## BOUNDS (§8)

- **The check inherits every limit of `seed_audit`** — 7 declared blind spots,
  481 unresolved sink sites. **A CLEAN verdict is a lower bound on cleanliness.**
  It cannot see seeds from CLI/env, data-derived seeds, cross-MODULE constants,
  unanalysed library code, non-Python seeds, or over-cap expressions.
- **The seed-INTEGER unit is a choice.** Under the "a block reserves a
  namespace" reading, an unoccupied integer inside someone's seeded stream is
  not free, and this tool will call it CLEAN.
- **It enforces DECLARATION, not CORRECTNESS.** The standing gate proves a
  drawn range is declared by *someone*; it cannot prove the declarer is the
  drawer. Attribution stays file-wise, as the prior rung defined it.
- **The nuisance mode, named:** if a runner and its §11 row land in different
  commits, the gate fires on the gap. That is a true positive about ordering,
  and the failure message says so — but it will read as noise to someone who
  did not expect it.
- **It runs only where it is wired.** In the migrated suite today, not in the
  oracle bench. A rung that runs neither before claiming a block is still
  unprotected — which is why §11 recommendation 7 (record `check_claim` output
  in the prereg) matters more than the gate itself.
- **The value here is PREVENTION, not repair.** The tree has zero real
  unexplained collisions today. Nothing in this rung fixes a present defect; it
  makes a future one visible at pre-registration time instead of never.
