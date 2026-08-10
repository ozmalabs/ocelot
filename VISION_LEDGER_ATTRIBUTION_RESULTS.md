# LEDGER ATTRIBUTION + THE SEVEN UNPINNED SCRIPTS — RESULTS

**The 4.5× jump was ATTRIBUTED THE WHOLE TIME, by a gate already in the tree,
whose message nobody read because it sits in a suite that has been red since
`293782f1`. And the "one-line fix" for the seven was NOT a one-line fix for two
of them — in those two the prescribed line is a PROVABLE NO-OP.**

Pre-registration: `VISION_LEDGER_ATTRIBUTION_PREREG.md` (with a disclosed §3
deviation — see §0 there and §6.1 here).

---

## 0. PROVENANCE, RUN AS ITS OWN STEP, BEFORE ANY NUMBER

**BRANCH / SHA AS OBSERVED:** `worktree-agent-a60e8c1c27b805abf` @
**`77e932f12d6f64a735775b0083c137f9d5df532b`**.

**ENGINE (§10) — printed from INSIDE the measuring process:**

```
engine a1d350bbd23b @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]
```

Built by `bash scripts/engine_build.sh`. **No Rust added.**
`pytest tests/test_engine_provenance_migrated.py -q` → **7 passed**, run as its
own step before any number.

**SEED CLAIM (§3 clause 8)** — verbatim in PREREG §0.1:

```
SEED CLAIM 101000-101999: CLEAN -- no collision DETECTED.
  Scope: 805 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

**497 unresolved sinks.** **SEEDS DRAWN: ZERO — 101000–101999 IS RETURNED
ENTIRELY INTACT.** Every control here is a revert of a REAL file, so no
randomised plant was needed. The vacuity that creates is answered in §4: both
directions were demonstrated on real tree state, not on synthetic input.

**ORACLE:** `bash scripts/rung7_vision_bench.sh` → **222 passed / 0 failed**
before the change and **222 passed / 0 failed** after, with `data/` symlinked
(§10.2). Quoted with its condition, never bare. **Nothing was added to that
file's list — that list IS the oracle.**

**NEIGHBOURING GATES (§9):** `test_engine_provenance_migrated` +
`test_provenance_endpoint_guard_migrated` + `test_seed_accounting_migrated` →
**664 passed**. `test_instrument_seams_migrated.py` → **22 passed** (unchanged
count).

---

## 1. TASK 1 — THE ATTRIBUTION OF 110 → 493, PER RUN

### 1.1 The arithmetic, complete and exact

Diffing the record committed at `87a462c7` (the seams rung's own) against the one
committed at `77e932f1`:

| | Δ | evidence |
|---|---|---|
| **TIMEPHI** — `scripts/timephi_measure.py`, run **93000–93399** | **+400** | one contiguous run, one file |
| **FIGADJ-NESTING** — `nesting_surface_measure.py` (92000–92004, 92010–92014, 92100–92104, 92110–92114), `figadj_nesting_measure.py` (92900), `test_border_ownership_nesting_migrated.py` (92700–92701) | **+23** | six runs, three files |
| **the seams rung's OWN 95000–95019 / 95100–95119 LEAVING** the undeclared set, because the supervisor wrote its ledger row at `77e932f1` | **−40** | two runs removed |
| | **+383** | **110 + 383 = 493 ✓** |

**Nothing else moved.** 52 runs live, 47 before, 7 added, 2 removed. The residue
is zero.

### 1.2 Both offered hypotheses are REFUTED, and the second is refuted twice

**(b) "The tool does not credit a RETROACTIVE ledger row" — REFUTED, and the
suspicion should be withdrawn.** Measured directly:

```
parse_ledger() blocks    : (38000, 38099), (40000, 40099)        <- both parsed
seed_ledger_measured.json: fill 1.0, measured_seeds 100, each     <- both credited
undeclared_runs in 37000-41000: []                                <- neither reported
```

**And they were credited already in the seams rung's OWN committed record at
`87a462c7`** — same three readings, same values. So its §6.6 ("recs #1 … remain
NOT APPLIED, and are now visible in `results/seed_ledger_measured.json` under
`undeclared_runs`") is **contradicted by the artifact it shipped in the same
commit.** The supervisor caught the first half (the rows ARE applied) and left
the second half open as "a separate question about how the tool reads a
retroactive row." **There is no such question. The tool reads them correctly.**

**Where the belief came from, since it did not come from nothing:**
`tests/test_seed_claim_migrated.py` carries a *hand-written frozen* baseline
whose prose still reads *"§11 row recommended, NOT YET APPLIED"* for both blocks,
and `check_claim(38000, 38099)` REFUSES — correctly, because the range is both
occupied and declared. **A refusal was read as "still undeclared."** The
machine-derived instrument said the opposite the whole time, in as many words:

```
38000-38099 is now DECLARED at [(38000, 38099)]. The ledger-blindness this
gate documents has been fixed; update the baseline.
```

**The generated record and the frozen prose in the test disagreed, and the prose
was believed.** That is §11 rec #4's own thesis — *a ledger row's declared block
is a claim about the tree; this file is the tree* — recurring one level up, in
the gate written to enforce it.

**(a) "The declaration convention, not the rungs" — REFUTED, and refuted in the
OPPOSITE DIRECTION from the one proposed.** The motion rung is the named
instance. Its complete static footprint:

```
scripts/motion_sensor_gate.py            seeds: [0]   unknown_sinks: 15
tests/test_motion_sensor_gate_migrated.py seeds: [3]  unknown_sinks: 0
```

**Two seeds, both below `LEDGER_FLOOR`, both excluded.** It contributes **zero**
to `undeclared_seeds`. The hypothesis was that a static scan sees MORE literal
seeds than a declaration covers; measured, the scan sees **2 where the rung drew
2257**. Its effect landed entirely in the OTHER moved number:
**`unresolved_sinks` 482 → 497 = +15, all of it `scripts/motion_sensor_gate.py`**
— the exact figure that rung disclosed in its own ledger row. The declaration
convention is not the defect; the rung's runtime draws are simply invisible to a
static analyser, which is blind spot #5 of the tool's declared seven.

### 1.3 The actual cause, which is in neither box

**Two rungs pre-registered their blocks, ran `check_claim`, and have no §11
ledger row.** `VISION_TIMEPHI_PREREG.md` declares 93000–93999 and pastes its
claim verdict; `VISION_FIGADJ_NESTING_PREREG.md` declares 92000–92999 and pastes
its claim verdict. Both did everything the protocol asks of a rung. **The row is
the supervisor's to write, and it was not written.** So the record is right, the
rungs are right, and **the ledger is two rows behind.**

**Why it looked unattributable: the delta spans a MERGE OF FOUR CONCURRENT
BRANCHES.** The seams rung's base `ee0a1af2` is **not** an ancestor of the
timephi merge (`5efa34a6`), the motion merge (`eff5d45b`), or the nesting work —
verified with `git merge-base --is-ancestor`. It measured a whole-tree derived
quantity from inside an isolated worktree (§11), so **every concurrently-merged
rung's seeds appeared at once, at merge time, in a single step nobody owned.**
This is a structural interaction between §11 (isolate) and the record being
whole-tree (aggregate), and it will recur on every parallel wave.

### 1.4 THE FINDING THAT OUTRANKS THE ATTRIBUTION

**A gate in this tree printed the complete per-run attribution before I started.**
`tests/test_seed_claim_migrated.py::test_undeclared_consumption_does_not_grow`:

```
NEW UNDECLARED SEED CONSUMPTION -- seeds are drawn in these ranges and no
VISION_PROTOCOL.md §11 row declares them:
  92000-92004  n=5    scripts/nesting_surface_measure.py
  92010-92014  n=5    scripts/nesting_surface_measure.py
  92100-92104  n=5    scripts/nesting_surface_measure.py
  92110-92114  n=5    scripts/nesting_surface_measure.py
  92700-92701  n=2    tests/test_border_ownership_nesting_migrated.py
  92900-92900  n=1    scripts/figadj_nesting_measure.py
  93000-93399  n=400  scripts/timephi_measure.py
```

That is §1.1's table, exactly, with the files named. **It was not read because it
is 1 failure inside a suite that returns 8, and the other 7 were triaged — twice,
correctly — as "pre-existing, not mine."** The seams rung verified that
classification with `git stash -u` and was right about all seven. But the eighth
changed meaning between the two triages, and a chronically-red suite has no way
to say so.

> **A CHECK THAT PASSES WITH UNKNOWN SINKS HAS VERIFIED NOTHING — and a check
> that FAILS CHRONICALLY has verified nothing either.** The arc has a rule for
> the first and none for the second. 7 of the 8 failures in that file are stale
> *because the defect they documented was FIXED*; they are success reports
> wearing a failure's clothes, and they are camouflage for the one live signal
> in the same file.

### 1.5 What the number SHOULD be

| quantity | value | meaning |
|---|---|---|
| **493** | as committed | arithmetically correct for what it measures |
| **−48** | date literals + conventional magic constants (`20260705…`, `12648430`, `1234`, `789996`) | a namespace the project **already declared is not ledger draws** (seed-accounting rec 5). `test_seed_claim_migrated._ledger_scale` excludes it; `seed_record.undeclared_seeds` does not. **Two instruments in one tree compute the same-named quantity by different rules and differ by 48.** |
| **445** | ledger-scale | what the gate actually reads |
| **−423** | the two rows-pending rungs | **closes when the supervisor writes two rows** |
| **22** | the standing floor | `test_vision_maps_migrated.py` 1000–1019 (n=20, predates the convention), `99991`, `100003` |

**So: after two ledger rows, the record reads 70 raw / 22 ledger-scale.** The
honest headline for the tree today is **"two rungs are awaiting a ledger row,"
not "493".**

### 1.6 IS THE RECORD GATE-WORTHY? — QUALIFIED YES, WITH ONE NUMBER THAT IS NOT

**The FRESHNESS gate is sound and should be kept.** It fired correctly, forced the
regeneration, and the regenerated diff is a complete, per-file, per-run
attribution. Nothing about the mechanism failed. Both hypotheses that the tool
was lying are refuted by measurement.

**The `undeclared_seeds` HEADLINE is not gate-worthy, and nothing currently gates
on its value** — the freshness gate compares the whole rendered document, so it
gates *change*, never *magnitude*. That is fortunate, because the magnitude is
not comparable across rungs:

> **400 of the 423 come from ONE file, and it is the file that was MOST
> COOPERATIVE with the auditor.** `timephi_measure.py` says so in its own source:
> *"Every draw is materialised HERE, from a single sink bound to an explicit
> `range`, so `seed_audit.py` can RESOLVE every seed statically instead of
> reporting an unknown sink."* A rung that instead writes `default_rng(93000)`
> and loops internally scores **1**. Two rungs are equally undeclared; one shows
> 400 and the other 23. **`undeclared_seeds` measures seed-expression STYLE at
> least as much as accounting severity, and it penalises the behaviour the tool
> wants.**

The quantity that answers the ledger's question is the one the gate already uses:
**undeclared RUNS and the FILES that drew them** — 7 runs, 3 files, 2 rungs.
Recommended in §5.

**A gate reporting a number nobody can attribute is worse than no gate — but that
is not what happened here.** The number was attributable, in one command, from a
gate already installed. It was not attributed. That is a **reading** failure with
a **structural** cause (a chronically-red suite), not an instrument failure, and
§5 proposes the fix for the cause rather than for the symptom.

---

## 2. TASK 2 — THE SEVEN, VERIFIED BY HAND BEFORE BEING TOUCHED

Each was read directly, one at a time, before any edit — the seams rung's
discipline, applied to the seams rung's own accusation:

| file | REPORTS via | PINS | resolves through |
|---|---|---|---|
| `blob_cost_measure.py` | `ep.provenance_line()` :179 | **no** | `sys.path.insert(runners/dsl/python)` |
| `blob_proto_measure.py` | `ep.provenance_line()` :238 | **no** | same |
| `ink_ventral_measure.py` | `engine_provenance.provenance_line()` :423 | **no** | same |
| `ink_ventral_pin.py` | `provenance_line()` + `engine_provenance()` :32–33 | **no** | same |
| `resolution_k_arm.py` | `ep.provenance_line()` :136 | **no** | same |
| `resolution_scale_measure.py` | `ep.provenance_line()` :187 | **no** | same |
| `value_flood_measure.py` | `ep.provenance_line()` :284 | **no** | **the canonical `.pth`** (it inserts `domains`, not `runners/dsl/python`) |

**The accusation is confirmed on all seven.** All now call `engine_preamble()`,
and `pa.audit_repo()["imported_not_called"]` is **`[]`**.

### 2.1 THE FINDING: "EACH IS A ONE-LINE FIX" IS FALSE FOR TWO OF THE SEVEN

**An extension module is bound at FIRST IMPORT. A preamble that runs after any
module-level import of the engine is a NO-OP ON RESOLUTION — it changes only the
line that gets printed.** Measured, not reasoned, on `value_flood_measure.py`
with the pin placed exactly where the floor prescribes:

```
loaded BEFORE preamble: .../research/experiments/gamma-substrate/... _native.abi3.so   <- CANONICAL
ep.engine_preamble()                     # the prescribed "one-line fix"
loaded AFTER  preamble: .../research/experiments/gamma-substrate/... _native.abi3.so   <- UNCHANGED
engine befe27c3a49d @ <CANONICAL tree>  [shared build — Rust source identical]
```

**It does not even refuse**, and it is right not to: the Rust source is
byte-identical, so `shared` is the correct verdict under §10.1's
content-not-location invariant. The pin is silently vacuous and everything reads
green.

Two files needed the provenance import **HOISTED above the first engine-loading
import**, not a line appended where it sat:

* `value_flood_measure.py` — `from substrate.boot_core import …` was above it.
* `ink_ventral_measure.py` — `import scripts.jabberwock_omniglot_dynamic_quantization`
  was above it (verified: that module loads `substrate_rs` on import).

**This is §10 rule 1b one level deeper.** Rule 1b says a green gate in a
different PROCESS is not provenance. This says **a pin in the wrong PLACE in the
same process is not provenance either** — and unlike the process case, it
produces a plausible green line rather than a divergence. Proposed as an
amendment in §5.

### 2.2 DOES PINNING MOVE A NUMBER? — MEASURED, AND NO

**Engine resolution, per script, before → after** (probe replays each file's real
module-level preamble, then reports `realpath(substrate_rs._native.__file__)`):

| script | before | after |
|---|---|---|
| the six that insert `runners/dsl/python` | `a1d350bbd23b` (own tree) | `a1d350bbd23b` — **unchanged** |
| **`value_flood_measure.py`** | **`befe27c3a49d` — the CANONICAL tree's binary** | **`a1d350bbd23b` — own tree** |

So six repairs cannot move a number in a tree that has built its engine (they
matter in a fresh worktree, where §10.2 measured this convention pinning a
HEADLESS package). **One repair genuinely changes which binary is loaded**, so
P4's registered failure condition was live and had to be tested, not assumed.

**Tested.** `value_flood_measure.controls()` — the corpus-free, deterministic
control block (D1 committed reproduction, D2a/D2b/D2c dead-instrument arms, the
per-lattice arm), i.e. the part that boots the substrate and runs the
border-ownership rules to a `run_rules` fixpoint — run under both binaries via
per-process `PYTHONPATH` (§11 rule 2: a private path, never a `.pth` swap):

```
ARM A  engine .../research/.../_native.abi3.so          (canonical, befe27c3a49d)
ARM B  engine .../worktrees/.../_native.abi3.so         (own,       a1d350bbd23b)
diff   -> BYTE-IDENTICAL
```

**NO LANDED NUMBER MOVES.** Two different binaries — the difference is build
non-determinism, not source: `diff -rq runners/dsl/src` against canonical is
empty, and `Cargo.toml` is identical.

**SCOPE OF THAT NEGATIVE, STATED (§8):** it covers the control block, not the
corpus rows, and it is one script. It is a *behavioural* check on top of a
*source* argument, not a re-run of the rung. The stronger statement is the source
one: byte-identical `.rs` ⇒ byte-identical semantics; the binary-hash difference
is a build artifact §10.1 explicitly anticipates. **What it does NOT license is
the general claim "any two engines here agree"** — that is exactly the assumption
§10 exists to forbid, and the only reason it holds today is that the arc has
added no Rust.

**INCIDENTAL, AND IT IS THE LIVE FORM OF THE HAZARD:** the canonical engine was
rebuilt at **20:13**, one minute before my own build, **by a concurrent agent**.
Until this commit, `value_flood_measure.py` would have measured that binary. It
was benign only because the source agreed. **This is §11's shared-mutable-state
hazard, observed live rather than reconstructed** — and it is precisely the file
whose pin the floor called a one-liner.

### 2.3 THE FLOOR IS SHRUNK TO ZERO — AND THAT BROKE ITS OWN ALIVENESS CONTROL

`results/preamble_audit_floor.json` → **`known_violations: []`**. The gate now
binds every file in the tree with no exemption.

**Emptying it turned the audit's only real-tree non-vacuity check RED**, and the
reason is worth recording:

```python
known = pa.read_floor()
assert known, "the floor is empty — the audit found nothing on a tree where
               seven violations were verified by hand"
still = known & set(rep["imported_not_called"])
assert still, "not one floor entry reproduces — DEAD INSTRUMENT, not a clean tree"
```

**The instrument's proof-of-life was tied to the tree still being broken.**
Repairing every entry made the aliveness control fail, and the cheapest route
back to green would have been **to leave one defect unfixed**. That is the same
failure class the audit was built to catch, sitting inside the audit.

**Fixed by INVERSION, not deletion.** The seven are retained under a new
`repaired` key as the audit's permanent **real-tree regression corpus**, and the
assertion is flipped: each must now **PIN**, asserted positively per file from
the AST (`imports_preamble` AND `calls_preamble`) rather than as an absence — *an
audit that scanned the wrong subtree satisfies an absence by finding nothing.*
Plus a new assertion that `known_violations` stays empty: **a floor that never
shrinks is an exemption list wearing a different name, and one that can silently
re-grow is the same thing.** `write_floor()` carries `repaired` forward, so
regenerating cannot delete the landing check.

This is strictly stronger than what it replaces: same real files, and it also
fails on regression.

---

## 3. GATES

| gate | result |
|---|---|
| `tests/test_instrument_seams_migrated.py` | **22 passed** (count unchanged) |
| provenance + endpoint + seed-accounting | **664 passed** |
| `bash scripts/rung7_vision_bench.sh` (with `data/`) | **222 / 0** before, **222 / 0** after |
| `python3 -m domains.seed_record` | *measured ledger record is current* (zero seeds drawn ⇒ no regeneration) |
| `preregs_missing_claim()` | `[]`, and this rung's prereg is **NOT on the grandfather floor** (checked explicitly) |

**ON `--write`:** this rung drew **zero** seeds and the record is already current,
so **no regeneration was performed and none is owed.** Had one been, it would
have meant only "the set of seeds this tree draws is unchanged" — the generator
itself was not modified by this rung.

---

## 4. POSITIVE CONTROLS — BOTH DIRECTIONS, ON REAL TREE STATE

*A gate that has never been ABLE to fail has not been tested*, and this rung
emptied a floor, so its replacement had to be shown to fail.

| control | expected | **measured** |
|---|---|---|
| remove the pin from ONE real repaired file | RED, naming that file | `REGRESSION: ['scripts/resolution_k_arm.py'] report provenance and no longer pin it` |
| re-add ONE exemption to `known_violations` | RED, naming the re-growth | `preamble_audit_floor.json has regained exemptions. A floor that never shrinks is an exemption list wearing a different name.` |
| restore both | GREEN | 1 passed |

**These are reverts of real files, not plants** — the seams rung's own landing
check made the same point in the other direction (*"a control that scans the
wrong subtree passes by finding nothing"*). The cost is that this rung ran no
randomised arm and therefore drew no seed; that trade is declared in the prereg
rather than discovered here.

---

## 5. PROPOSED §-AMENDMENTS — the supervisor applies them; I did not edit the protocol

### 5.1 For §10, as rule 1c

> **1c. A PIN BELOW THE FIRST ENGINE IMPORT IS NOT A PIN.** An extension module
> is bound at FIRST IMPORT; `engine_preamble()` mutates `sys.path` and **cannot
> rebind an engine already in `sys.modules`.** Placed after any module-level
> import that loads the substrate, the call is a **NO-OP ON RESOLUTION** — it
> changes only the line that gets printed, and it does not refuse, because a
> shared build from identical Rust source is a legitimate `shared` verdict.
> **Measured 2026-07-20 on `scripts/value_flood_measure.py`: with the pin where
> §10 rule 3 would put it, the process stayed bound to the CANONICAL tree's
> binary and reported green.** Rule 1b says a green gate in a different PROCESS
> is not provenance; this says a pin in the wrong PLACE in the same process is
> not provenance either, and it is the quieter of the two. **Put the
> `engine_provenance` import and the `engine_preamble()` call ABOVE every import
> that can reach the engine.**

### 5.2 For §10 rule 3b, replacing the floor sentence

> `results/preamble_audit_floor.json` **`known_violations` is now EMPTY — all
> seven were repaired 2026-07-20 and the gate binds every file with no
> exemption.** The seven are retained under `repaired` as the audit's real-tree
> REGRESSION CORPUS with the assertion INVERTED (each must PIN), because the
> original landing check asserted that floor entries still reproduce AS
> VIOLATIONS — **tying the instrument's proof-of-life to the tree still being
> broken, so that fixing everything turned the aliveness control red.** An
> instrument whose non-vacuity requires an unrepaired defect is the failure class
> it was built to catch. **Two of the seven were NOT one-line fixes** (§10 rule
> 1c).

### 5.3 For §11, alongside rec #4 — TWO ADDITIONS

> **(i) THE RECORD'S HEADLINE IS NOT THE RECORD'S SIGNAL.** `undeclared_seeds`
> counts seed INTEGERS, so it measures seed-expression STYLE as much as
> accounting severity — **and it penalises cooperation.** Measured 2026-07-20:
> two equally-undeclared rungs scored **400** and **23**, and the 400 is the rung
> that deliberately materialised every draw from an explicit `range` *so the
> audit could resolve it statically*. Quote **undeclared RUNS and the FILES that
> drew them** (7 runs / 3 files / 2 rungs); quote the seed count only with the
> unit caveat attached. `seed_record.undeclared_seeds` should also apply
> `_ledger_scale`'s exclusions (date literals + conventional magic constants,
> **48 seeds**), which the gate already applies and the record does not — **two
> instruments in one tree computing the same-named quantity by different rules.**
>
> **(ii) A WHOLE-TREE DERIVED RECORD MEASURED IN AN ISOLATED WORKTREE STEPS AT
> MERGE TIME.** §11 isolates; the record aggregates. A rung's committed record
> describes **its base**, so a wave of N concurrent rungs produces ONE unowned
> step on merge, attributable only by diffing against each base. This is
> structural and will recur. **Regenerate the record on the MERGE, and read
> `test_undeclared_consumption_does_not_grow`'s message — it is the attribution,
> per run, per file.**

### 5.4 For §12 — a new clause

> **A CHRONICALLY-RED SUITE IS A DEAD INSTRUMENT, IN THE SAME SENSE AS A GATE
> THAT CANNOT FAIL.** `tests/test_seed_claim_migrated.py` returns 8 failures.
> **7 are stale success reports** — assertions written when 38000/40000/90003
> were undeclared, which now fail *because the defect was FIXED* (the messages
> say so: *"is now DECLARED … update the baseline"*). The 8th is the live,
> complete, per-run attribution of the 110→493 jump. It was triaged twice as
> "pre-existing, not mine" — **correctly both times**, and the signal was lost
> anyway. *A check that passes with unknown sinks has verified nothing; a check
> that fails chronically has verified nothing either.* **A gate whose message
> reads "update the baseline" is a TODO, not a failure, and it must not be
> allowed to camouflage a live one.**

### 5.5 For the burned-seed ledger — THREE ROWS

> | **93000–93399 CONSUMED (`scripts/timephi_measure.py`; rest of 93000–93999 returned)** | **TIMEPHI — row written retroactively at the ledger-attribution rung's finding.** Pre-registered at `VISION_TIMEPHI_PREREG.md` with its `check_claim` verdict pasted; merged at `5efa34a6` with **no §11 row**. **THE DOMINANT CAUSE of `undeclared_seeds` 110 → 493 (+400 of +383 net).** Its 400 is large *because the script deliberately materialises every draw from an explicit `range` so the audit can resolve it statically* — the most audit-cooperative rung in the wave produced 94% of the headline. |
> | **92000–92004, 92010–92014, 92100–92104, 92110–92114, 92700–92701, 92900 CONSUMED (rest of 92000–92999 returned)** | **FIGADJ-NESTING — row written retroactively at the ledger-attribution rung's finding.** Pre-registered at `VISION_FIGADJ_NESTING_PREREG.md` (92000–92999) with its `check_claim` verdict pasted; **no §11 row**. `scripts/nesting_surface_measure.py` (20), `tests/test_border_ownership_nesting_migrated.py` (2), `scripts/figadj_nesting_measure.py` (1) = **+23**. |
> | **101000–101999 CLAIMED, ZERO DRAWN (block returned entirely clean, measured)** | **LEDGER ATTRIBUTION + THE SEVEN UNPINNED SCRIPTS.** **THE 4.5× JUMP WAS FULLY ATTRIBUTED BY A GATE ALREADY IN THE TREE, WHOSE MESSAGE WAS LOST INSIDE A CHRONICALLY-RED SUITE.** Both offered hypotheses REFUTED: the tool **does** credit the retroactive 38000/40000 rows (fill 1.0, zero undeclared runs — **and did so in the seams rung's OWN committed record**, so its §6.6 is falsified by the artifact it shipped); the motion rung contributes **ZERO** and its footprint is **2 seeds, not many** — it moved `unresolved_sinks` +15 instead. Real cause: **two rungs pre-registered and check_claim'd their blocks and the ledger rows were never written**, observed across a merge of four concurrent branches from a base that predated all three. **THE SEVEN §10-rule-3 DEFECTS ARE FIXED AND THE FLOOR IS EMPTY — and "each is a one-line fix" IS FALSE FOR TWO OF THEM: an extension module is bound at first import, so a pin below it is a PROVABLE NO-OP that reports green (measured: `value_flood_measure.py` stayed bound to the CANONICAL binary through the prescribed fix).** Pinning moves **NO landed number** (two binaries, byte-identical control output, byte-identical `.rs`) — but it does change which binary `value_flood_measure.py` loads, and **the canonical engine had been rebuilt by a concurrent agent one minute earlier**, so §11's hazard was live. **EMPTYING THE FLOOR BROKE THE AUDIT'S OWN ALIVENESS CONTROL** — it asserted floor entries still reproduce AS VIOLATIONS, tying proof-of-life to the tree staying broken; INVERTED into a `repaired` regression corpus, positive-controlled in both directions on real files. No Rust, no seed; provenance its OWN step (7 passed); oracle **222/0** before and after. |

---

## 6. WHAT I GOT WRONG

1. **I measured TASK 1 before writing a pre-registration.** §3 says pre-register
   before any number, and I did not — the attribution numbers existed before
   `VISION_LEDGER_ATTRIBUTION_PREREG.md` did. I have disclosed it in the prereg
   rather than backdating the document. My defence is that this rung selects no
   metric and drops no arm — every figure is a deterministic property of the tree
   — but §3 does not carve out diagnostics, and "it wasn't the kind of number the
   rule is about" is the argument every §3 violation makes.
2. **I nearly emptied the floor and stopped.** The gate would have gone red on
   `assert known` and the obvious repair — leave one violation behind — is the
   exact anti-pattern the task warned about. I caught it by reading the test
   before deleting the entries, not by reasoning about it in advance.
3. **My first inverted assertion referenced a report key that does not exist**
   (`imports_and_calls`). It would have raised `KeyError` rather than failing
   informatively, and I found it by running the audit, not by reading the module.
   **A control that errors is not a control that fails** — the rewrite asserts
   per-file from `audit_file()`, which is the evidence the verdict is built from.
4. **P4 was right for the wrong reason on six of seven scripts.** I predicted
   "no number moves because resolution is unchanged." For `value_flood_measure.py`
   resolution **did** change, and the correct reason the number holds is that the
   Rust source is byte-identical — a source argument, not a path argument. §10.1
   says the invariant is content not location, and my prediction reasoned about
   location.
5. **I did not re-run the seven scripts' full measurements.** I compared one
   script's control block across the two binaries and rested the rest on the
   byte-identical `.rs`. That is a bounded claim and §2.2 states its bound; it is
   not the same as re-earning the seven rungs' numbers, and I have not done that.
6. **I edited three files I do not own** (`domains/preamble_audit.py`,
   `tests/test_instrument_seams_migrated.py`, plus the seven scripts) — §11 rule
   4 territory. The task directed the repair and the floor could not be shrunk
   without the first two, but the aliveness-control inversion in particular is a
   design change to another rung's gate and the supervisor should review it as
   one, not merge it as cleanup.

---

## 7. BOUNDS (§8)

* **Everything inherits `seed_audit`'s 7 blind spots and 497 unresolved sinks.**
  The attribution in §1.1 is complete *with respect to what the scanner can
  resolve*. **A CLEAN RECORD MEANS "NOTHING DETECTED", NEVER "NOTHING THERE"** —
  and the motion rung is this arc's proof, with 2257 runtime draws showing as 2.
* **The "no number moves" negative covers one script's control block**, not the
  corpus rows and not the other six (§2.2).
* **The engine equivalence holds only while no rung adds Rust.** It is a
  restatement of §10.1's audit, not a new guarantee.
* **The static audit still cannot see a process that never runs.** S3 = 814
  entrypoints reach the engine without pinning it; 554 via the §10.2-broken
  convention. Not gate-grade, unchanged, still a reporter.
* **This rung fixes no scientific defect and moves no scientific number.** It
  attributes a bookkeeping number and repairs seven instrument defects.
* **§9:** no seed installed, no rule changed, no Rust added, no default flipped,
  nothing added to the oracle's file list.
