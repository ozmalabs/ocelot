# INSTRUMENT SEAMS — RESULTS

**Two defects, found by two different rungs, both offered upward, neither applied. Both
are now REFUSALS rather than recommendations.**

Pre-registration: `VISION_INSTRUMENT_SEAMS_PREREG.md`, committed BEFORE the run at
**`356978bb`** (base `main` HEAD **`ee0a1af2`**, worktree
`worktree-agent-a182430576b3b6012`).

---

## 0. PROVENANCE, RUN AS ITS OWN STEP, BEFORE ANY NUMBER

**ENGINE (PROTOCOL §10) — printed from INSIDE the measuring process:**

```
engine a1d350bbd23b @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]        source_match: own
```

Built by `bash scripts/engine_build.sh` (§10.3 — never a hand-rolled `cp`, never a
symlink to canonical). **This rung adds NO Rust**; the build exists only so that nothing
measured here is another tree's binary — which is the very defect under repair, so
measuring it on a borrowed engine would have been self-refuting.

`pytest tests/test_engine_provenance_migrated.py -q` → **7 passed**, run before the
pre-registration was written and again after the change.

**SEED CLAIM (§11 rec #7, applied to myself first)** — `scripts/seed_claim.py 95000
95999` at base `ee0a1af2`, recorded verbatim in PREREG §0.2:

```
SEED CLAIM 95000-95999: CLEAN -- no collision DETECTED.
  Scope: 798 files with seed sinks; 482 UNRESOLVED sink sites tree-wide.
```

**482 unresolved sinks.** A clean verdict is a lower bound on cleanliness. It is quoted
with every number below for the same reason the tool quotes it: *a check that passes
with unknown sinks has verified nothing* unless the unknowns are priced.

**ORACLE:** `bash scripts/rung7_vision_bench.sh` → **212 passed, 10 skipped** in 178 s.
`data/` is **absent** (gitignored, as in every worktree), so this is exactly the
documented **212/10** condition (§10.2) — quoted with its condition, never bare. The 10
skips are the BSDS300 corpus tests that have never run in a worktree.

**NEIGHBOURING GATES (§9):** `test_engine_provenance_migrated` +
`test_provenance_endpoint_guard_migrated` + `test_seed_accounting_migrated` +
`test_seed_claim_migrated` → **665 passed, 8 failed.**

**SEVEN OF THE EIGHT PRE-EXIST AND ARE NOT MINE — VERIFIED, NOT ASSUMED.** With
`git stash -u` (working tree byte-clean at base `ee0a1af2`),
`tests/test_seed_claim_migrated.py` alone is **7 failed, 6 passed**: its fixtures assume
ledger state that later commits changed (rows now exist for 90003–90999 and for
38000/40000, which its "these blocks read free" cases were written against). Restored,
the same 7 fail identically.

**The eighth is MINE, and it is a TRUE POSITIVE:**
`test_undeclared_consumption_does_not_grow` fires on

```
95000-95019  n=20  tests/test_instrument_seams_migrated.py
95100-95119  n=20  tests/test_instrument_seams_migrated.py
```

— my 40 seeds have **no §11 ledger row**, because the supervisor owns that file. This is
the ordering nuisance mode the seed-claim rung named in advance ("if the runner and its
§11 row land in different commits this gate fires on the gap — a true positive about
ordering"). **I did NOT silence it by editing their `KNOWN_UNDECLARED` list** (§11 rule 4
— not my file), and it needs no such edit: applying the ledger row proposed in §6.5 makes
`parse_ledger()` see the block and the gate goes green on its own.

**A rung's first act was to be caught by another rung's gate, exactly as designed.**

**MY SEEDS, MEASURED (§11 rec #4, applied to myself):**

| declared block | MEASURED sub-ranges | seeds | fill |
|---|---|---|---|
| 95000–95999 | **95000–95019**, **95100–95119** | **40** | **0.04** |

95020–95099 and 95120–95999 remain CLEAN. **My fill (0.04) is WORSE than the ledger's
0.100 median-of-nonzero.** That is recorded rather than hidden: it is exactly the
over-declaration rec #4 exists to expose, and it is mine. (The seed-accounting rung
found its own footprint had the same shape as the defect it was auditing. So does this
one.)

---

## 1. DEFECT 1 — "A GREEN PROVENANCE GATE IN A DIFFERENT PROCESS IS NOT PROVENANCE"

### 1.1 The defect, restated from the rung that found it

`VISION_SURFACE_ASSIGNMENT_RESULTS.md` §9: a concurrent rung rebuilt canonical from
changed Rust mid-pilot, and in the **same minute**

```
pytest tests/test_engine_provenance_migrated.py   ->  7 PASSED
a plain script in the same tree                   ->  ** WRONG ENGINE **
```

Both readings were correct. **The gate certifies the TREE'S CONFIGURATION UNDER ITS OWN
PREAMBLE; it does not certify that the process you are about to measure in loaded the
engine you think it did.**

### 1.2 THE SEAM I CHOSE, AND WHY IT CANNOT BE SKIPPED

**`engine_preamble()` — the call §10 rule 3 ALREADY REQUIRES of every non-pytest
entrypoint — now performs the in-process check and REFUSES.**

`domains/engine_provenance.py`, additive:

* `assert_measuring_engine()` — computes the verdict from the module resident in **this
  process's** `sys.modules` (`loaded_native_path()` reads the imported module's own
  `__file__`; it is never re-derived from `sys.path`), and raises
  `EngineProvenanceError` on `DIVERGED`, on `unknown`, and on stale Rust.
* `engine_preamble(..., strict=True)` — default on.
* `provenance_stamp()` — the write-side helper §10 rule 1 asks for: the record *plus*
  the refusal, for `rec["engine_provenance"] = provenance_stamp()`.

**Why this seam and not another.** Three candidates were considered:

| candidate seam | why not |
|---|---|
| a stronger pytest gate | **this is the defect.** The failing process was not pytest. |
| a results-writing helper | correct, but requires ADOPTION — and the binding constraint here is *"a gate only enforces if someone runs it."* Shipped anyway as `provenance_stamp()`, honestly labelled as adoption-dependent. |
| making `provenance_line()` raise | **rejected.** The existing gate READS it to describe a broken setup. An instrument that refuses to describe a fault is not an improvement on one that describes it. The reporter stays pure; the refusal lives on the PIN and the WRITE. |

The preamble is the seam because **you cannot pin the engine without certifying what you
pinned.** It is not a new step anyone must remember — it is a step already mandatory,
which now also carries the check. **Measured coverage: 140 scripts in `scripts/` call
`engine_preamble()` and are protected from this commit with no edit to any of them** —
including every vision measure script in the arc (`lighting_l*_measure`, `depth_measure`,
`stereo_measure`, `genmint_measure`, `surface_assignment_measure`, …).

**`conftest.py` passes `strict=False`, DELIBERATELY (§9).** Under pytest the refusal
would abort COLLECTION, turning the two named failures of the dedicated gate into a dead
suite — and moving the oracle's protocol number. **The gate reports; the preamble
refuses; neither was made to do the other's job.** This is itself gated, by AST, in
`test_conftest_pins_strict_False_on_purpose`.

### 1.3 THE BLIND SPOT, AND THE INDEPENDENT SECOND CHECK

A runtime check cannot see **a process that never calls it.** The known instance is on
record: a rung's diagnostic *imported* `engine_preamble` and never *called* it.

`domains/preamble_audit.py` — **AST only. It imports no engine, evaluates no Term, draws
no seed.** That independence is the design constraint, not an accident: *a diagnostic
must not be computed by the component it checks.* The two checks share no input, no
mechanism, and no failure mode.

**Located by SHAPE, never by substring.** `grep engine_preamble` cannot distinguish an
import from a call from a comment from a docstring — and this arc has now lost **four**
selectors to substring matching, the most recent going red on a docstring. The audit
resolves the *binding* and looks for an `ast.Call` whose callee is it, so alias,
module-qualified, and dotted forms are **the same case**:

| spelling | seen as a call |
|---|---|
| `engine_preamble()` | yes |
| `pin()` after `import ... as pin` | yes |
| `engine_provenance.engine_preamble()` | yes |
| `ep.engine_preamble()` | yes |
| `domains.engine_provenance.engine_preamble()` | yes |
| a docstring / comment / string mentioning it | **no** |

*A detector built from observed instances covers observed instances* — six spellings once
felt like a pattern here and were a sample, and the seventh walked through within one
commit. **The defence is not a longer list; it is resolving the binding, so a spelling
nobody has written yet still resolves.** Gated by `test_every_spelling_of_a_CALL_is_seen_as_a_call`
and `test_a_MENTION_is_not_a_call`.

### 1.4 WHAT THE AUDIT FOUND — S2 AND S3, AND BOTH PREDICTIONS WERE WRONG

2692 files scanned, **0 parse errors** (this module's own unknown-sink count).

| statistic | predicted | **MEASURED** |
|---|---|---|
| **S2** `imported_not_called` | 0 or 1 | **7** |
| **S3** entrypoint reaches engine, never pins | 3–15 | **814** |
| `path_insert_only` (the §10.2 convention) | not predicted | **554** |

**S2 = 7, AND THEY ARE ALL VISION MEASURE SCRIPTS. VERIFIED BY HAND, ONE AT A TIME,
BEFORE BEING BELIEVED** — three provenance gates in this arc sat green for 51 commits and
then fired at once as FALSE ACCUSATIONS, so an unverified accusation is worth nothing:

```
scripts/blob_cost_measure.py      scripts/resolution_k_arm.py
scripts/blob_proto_measure.py     scripts/resolution_scale_measure.py
scripts/ink_ventral_measure.py    scripts/value_flood_measure.py
scripts/ink_ventral_pin.py
```

Every one of them **reports** provenance (`ep.provenance_line()` into its results
artifact — they are obeying §10 rule 1) and **never pins** (`engine_preamble()` is never
called). They resolve instead through `sys.path.insert(0, runners/dsl/python)` — the old
convention §10 rule 6 called "safe" and §10.2 then measured as **actively broken in a
worktree**, where it pins a headless package. One of them,
`scripts/value_flood_measure.py`, does not even insert that path: it inserts `domains`,
and resolves the engine purely through the canonical `.pth`.

**This is the exact population the defect lives in — scripts that care enough about §10
to print the line, and are covered by nothing that acts on it.** They print an honest
verdict that nothing reads.

**S3 = 814 is NOT gate-grade and does not ship as a gate.** *Above-the-null is not
gate-grade*; 814 of ~2700 files is not a discriminating signal, it is a description of a
`scripts/` directory that predates §10. It ships as a **reporter**. The gate is on S2's
shape instead — "a script that cares enough about §10 to REPORT the engine must also PIN
it" — which is principled, small, and fixable.

**Grandfathered, with the floor saying what it is.** `results/preamble_audit_floor.json`
lists the 7 as **LIVE DEFECTS, NOT EXEMPTIONS**, records that each is a one-line fix, and
says never to add to the list to silence a failure. They are other rungs' files (§11 rule
4) — **recommended for repair, not repaired here.** An always-red gate is one agents route
around (§10.1 says so in those words about the old provenance test); a gate that binds new
violations is one that holds.

---

## 2. DEFECT 2 — "A PREREG RECORDS DECLARATIONS, NOT MEASUREMENTS"

### 2.1 Why rec #4 was never applied, and could not have been

It was written as a **prose** discipline: remember to type the measured sub-ranges into a
markdown cell. The seed-accounting rung measured what that yields — 58 of 108 blocks
measuring zero, median fill 0.100, two full 100-seed blocks consumed with no declaration
at all. **That is the predictable output of a write-side discipline with no read-side
enforcement, not carelessness.**

And it cannot be fixed by gating the prose, because gating prose means a substring
selector, and this arc's record on substring selectors is 0–4.

### 2.2 THE SEAM: GENERATE THE FACT, GATE IT FOR FRESHNESS

`domains/seed_record.py` derives measured occupancy per declared ledger block from the
AST scan the tree already has, and commits it as `results/seed_ledger_measured.json`.

**Why it cannot be skipped: any seed added, moved, or removed anywhere in the tree
changes the derived report, and the gate goes red until it is regenerated.** The
remediation is one command, printed in the failure message:

```
python3 -m domains.seed_record --write
```

**This is the whole argument for this seam.** The old discipline failed at the moment of
writing a ledger row — a moment with nothing attached to it. This attaches the
requirement to the moment a rung's seeds land in the tree, which is a moment nobody can
miss, because the gate is already running.

**THE NUISANCE MODE, NAMED IN ADVANCE, AND IT IS A TRUE POSITIVE:** a rung that adds a
seed for an unrelated reason gets a red gate it did not intend to trip. It is saying
something true — *you changed which seeds this tree draws* — and the diff it forces IS
the record the protocol asked for. **A gate whose nuisance mode is undocumented reads as
noise.** It is documented in the module, in the failure text, and here.

### 2.3 What the record says about the tree

| | seed-accounting rung | **now (123 blocks)** |
|---|---|---|
| declared blocks | 108 | **123** |
| measuring ZERO | 58 (53.7%) | **63 (51.2%)** |
| median fill | 0.100 | **0.0 over all blocks; 0.100 over the 60 non-zero blocks** |
| undeclared seeds above floor | — | **110** (70 before my own 40 landed) |
| unresolved sinks | — | **482** |

**PREDICTION 4 WAS RIGHT ONLY UNDER THE OTHER RUNG'S DEFINITION, AND I NEARLY MISREAD MY
OWN NUMBER.** I predicted median fill ≈ 0.100 and measured 0.0 — which looked like a
regression. It is not: with >50% of blocks at zero, the median over ALL blocks is 0.0 *by
construction*, and the median over non-zero blocks is **exactly 0.100**, reproducing the
prior number. The two rungs computed different statistics with the same name. Both are
reported; neither is a change. (§4 — *re-derive what each arm MEANS*.)

**My own 40 seeds pushed undeclared_seeds 70 → 110**, because block 95000–95999 has no
§11 ledger row. **The gate caught its own author's undeclared consumption on its first
firing.** A row is recommended below.

### 2.4 THE PREREG SEAM (§11 rec #7)

`preregs_missing_claim()` requires every non-grandfathered `VISION_*_PREREG.md` to
contain the tool's **own emitted verdict header** — `SEED CLAIM <lo>-<hi>:` — not a
keyword. A document that says "I ran check_claim and it was fine" **does not satisfy it**;
a document that pasted the output does, and pasting the output is the entire ask.

`results/prereg_claim_floor.json` grandfathers the **95** pre-registrations that predate
the gate. **An explicit committed list — never a date, never an mtime.**

### 2.5 I GRANDFATHERED MYSELF, AND THAT IS THE TRAP I WAS WARNED ABOUT

I generated the floor from `os.listdir` **after** writing my own pre-registration. My
document landed in the exempt set, and the gate was green on me **for the reason that it
never looked at me.**

That is the same shape as the two failures on the record: the seed-claim rung's first
positive control passed silently because it planted in an already-declared block, and the
supervisor's injection test passed because it planted in the wrong subtree. **A gate that
exempts its own author has not been tested.**

Corrected: `_GATE_AUTHOR_PREREG` is excluded from the floor, this rung is inside its own
gate, and `test_every_new_prereg_records_its_check_claim_output` asserts the exclusion
directly — so it cannot silently return.

---

## 3. POSITIVE CONTROLS — BOTH DIRECTIONS, ON EVERY GATE

`tests/test_instrument_seams_migrated.py` → **22 passed**. Not added to
`scripts/rung7_vision_bench.sh` — **that list IS the oracle**, and moving a
protocol-load-bearing number is not a rung's call (a predecessor declined this and was
right to).

| gate | FIRES on a real defect | GREEN on a clean tree | landing check |
|---|---|---|---|
| `assert_measuring_engine` | 20 randomised REAL divergent trees (actual differing `.rs`, real fingerprint comparison, **nothing mocked**) → raises | live tree → `own` | asserts the fake tree's fingerprint **really differs** before trusting the verdict |
| `engine_preamble(strict=True)` | raises on a divergent tree | `strict=False` silent; `sys.path` unmutated | asserts `sys.path` is byte-identical after — a control must not contaminate the session |
| `provenance_line` purity | must NOT raise | returns `WRONG ENGINE` text | verifies the verdict is `DIVERGED` independently |
| preamble AST audit | 20 randomised plants ×2 classes | 20 randomised clean modules | asserts **60 files scanned** — a control that scans the wrong subtree passes by finding nothing |
| audit on the REAL tree | 7 floor entries reproduce | — | asserts each is a real `.py` that exists; **"not one floor entry reproduces" is a DEAD INSTRUMENT, not a clean tree** |
| freshness | 20 randomised perturbations | live record current | **the message must NAME the block that was broken** |
| prereg claim | 40 randomised documents (no-claim + mention-only) | claim-present, and grandfather silences only what it lists | per-document parser assertion |

**Randomised, not hand-picked** — the plants are drawn from the declared seed block, so no
control can pass by accident of one convenient example. **This is also why a static
analyser spends seeds at all:** a rung that draws none has a vacuous self-audit.

### 3.1 THE CONTROL FOUND A REAL BUG IN MY OWN INSTRUMENT

`record_is_fresh` keyed its diff by `(lo, hi)`. **The §11 ledger repeats declared ranges
on purpose** ("0–13 (again)"; 1900–1999 appears twice), so the dict silently kept only the
last row — and perturbing any earlier duplicate produced a **correct STALE verdict with an
EMPTY explanation.**

**The top-level comparison still fired, so the gate looked fine.** Only the landing check
— *the message must name the block I broke* — exposed that it could not say **why**. A
gate that cannot name what it caught is one nobody can act on. Fixed (positional
comparison), and pinned by
`test_a_perturbed_DUPLICATE_declared_range_is_still_named`.

**Had I asserted only "the gate goes red," I would have shipped it.** That is the
seed-claim rung's lesson — *"had I not asked why it was quiet, I would have logged a dead
instrument as a pass"* — arriving one level in, on the instrument built to enforce it.

---

## 4. WHAT I GOT WRONG

1. **I grandfathered my own pre-registration** (§2.5). The gate was green on me because it
   never looked at me — the precise failure I had quoted in my own decision rule two hours
   earlier. Caught by writing the assertion that the author is *not* on the floor.
2. **My diff message was silent about duplicate ledger ranges** (§3.1). Caught only by the
   landing check.
3. **Both S2 and S3 predictions were wrong, in opposite directions.** S2: predicted 0–1,
   measured **7** — I assumed a recorded defect had been fixed. It is endemic in exactly
   the scripts that take vision numbers. S3: predicted 3–15, measured **814** — I badly
   underestimated how much of `scripts/` predates §10, which is why S3 ships as a reporter
   and not a gate.
4. **I wrote a substring assertion that matched itself.** The control proving the AST scan
   reads `95_100` where a grep cannot ended with `assert "default_rng(95100" not in raw` —
   which found *its own source line*. **The substring-selector failure, occurring inside
   the test written to warn about substring selectors, on the fifth iteration of that
   lesson in this arc.** Now located by AST over `default_rng` call sites.
5. **An earlier draft of that same test contained `assert ... , None or True`** — a
   malformed assertion that could never fail. A vacuous assertion in the file whose
   subject is vacuous instruments. Deleted, along with a second dead
   `assert X or True` in the real-tree landing check.
6. **I initially planned to make `provenance_line()` raise.** That would have broken the
   existing gate's ability to *describe* a fault. Caught before shipping by reading
   `tests/test_engine_provenance_migrated.py` — not by reasoning.

---

## 5. BOUNDS — WHAT THIS DOES NOT DO (§8)

* **It inherits every limit of `seed_audit`:** 7 declared blind spots, **482 unresolved
  sink sites**. It cannot see CLI/env seeds, data-derived seeds, cross-module constants,
  non-Python seeds, or over-cap expressions. **A CLEAN RECORD MEANS "NOTHING DETECTED",
  NEVER "NOTHING THERE."**
* **The runtime seam protects a process that CALLS the preamble.** 140 do. It cannot
  protect one that never pins at all — that is what the static audit makes *visible*, and
  visibility is not protection.
* **The 7 live violations are NOT fixed.** They are other rungs' files. Each is one line.
* **`provenance_stamp()` requires adoption**, and adoption is exactly what the binding
  constraint says not to rely on. It is offered, not counted as coverage.
* **It enforces RECORDING, never CORRECTNESS.** It cannot prove the declarer is the drawer.
* **This rung fixes no present defect and moves no scientific number.** The tree has no
  known live wrong number. It converts two post-hoc discoveries into pre-hoc refusals.
* **§9:** no seed installed, no rule changed, no Rust added, no default flipped. The only
  behavioural change to an existing path is that `engine_preamble()` now refuses a
  provably-wrong engine — the removal of a silent pass, not a default change — and
  `conftest.py` opts out explicitly so the oracle cannot move.

---

## 6. PROPOSED §-AMENDMENT TEXT — the supervisor applies it; I do not edit the protocol

### 6.1 For §10, after rule 1

> **1b. THE PROVENANCE CHECK MUST RUN IN THE PROCESS THAT TAKES THE NUMBER.** A green
> `tests/test_engine_provenance_migrated.py` certifies THE TREE'S CONFIGURATION UNDER ITS
> OWN PREAMBLE. It does not certify that the process you are about to measure in loaded
> the engine you think it did — measured 2026-07-19: **7 PASSED in the same minute a plain
> script in the same tree resolved `** WRONG ENGINE **`.** A bare `python -c` with
> `sys.path.insert(0, '.')` picks up the canonical `.pth` first and the gate is silent
> about it. **A GREEN GATE IN A DIFFERENT PROCESS IS NOT PROVENANCE.**
>
> This is now structural rather than remembered: `engine_preamble()` — the call rule 3
> already requires of every non-pytest entrypoint — computes the verdict from the module
> resident in THIS process's `sys.modules` and RAISES `EngineProvenanceError` on
> `DIVERGED`, on an unverifiable engine, and on stale Rust. **You cannot pin the engine
> without certifying what you pinned.** 140 scripts were covered by this with no edit to
> any of them.
>
> `conftest.py` passes `strict=False` deliberately: under pytest the refusal would abort
> COLLECTION and move the oracle's number (§9). **The gate reports; the preamble refuses;
> neither does the other's job.**
>
> Write the record where the number is written: `rec["engine_provenance"] =
> provenance_stamp()`.

### 6.2 For §10, alongside rule 3

> **3b. A RUNTIME CHECK CANNOT SEE A PROCESS THAT NEVER RUNS IT.** `domains/preamble_audit.py`
> is the independent static half — AST only, importing no engine, **deliberately not
> computed by the machinery it checks.** It resolves the BINDING and looks for a Call, so
> alias / qualified / dotted spellings are one case and a docstring is not a call (the
> fifth substring-selector failure in this arc happened *inside the test written to warn
> about substring selectors*).
>
> **Measured 2026-07-19: SEVEN vision measure scripts REPORT provenance via
> `provenance_line()` and never PIN via `engine_preamble()`** — they obey rule 1 and are
> covered by nothing that acts on it, resolving instead through the
> `sys.path.insert(runners/dsl/python)` convention §10.2 measured as broken in a worktree.
> `results/preamble_audit_floor.json` holds them as **LIVE DEFECTS, NOT EXEMPTIONS**, so
> the gate binds new violations instead of being red on arrival. Each is a one-line fix.

### 6.3 For §11, replacing rec #4

> **4. THE MEASURED RECORD IS GENERATED, NOT WRITTEN.** Rec #4 was a prose discipline for
> two rungs and was never applied, because prose can only be gated by a substring selector
> and this arc's record on those is 0–4. `results/seed_ledger_measured.json` is DERIVED
> from the AST scan and **gated for freshness**: any seed added, moved or removed anywhere
> changes it, and the gate is red until
>
> ```
> python3 -m domains.seed_record --write
> ```
>
> The requirement now attaches to the moment a rung's seeds LAND, not to the moment
> someone writes a ledger row — which is the moment the old discipline reliably failed.
> **The nuisance mode is real and is a TRUE POSITIVE**: an unrelated rung that adds a seed
> gets a red gate saying something true, and the diff it forces IS the record.
>
> **A ledger row's DECLARED block is a claim about the tree; this file is the tree.**
> Current state: **123 declared blocks, 63 measuring zero, median fill 0.100 over the 60
> non-zero blocks (0.0 over all), 110 undeclared seeds above the floor, 482 unresolved
> sinks.** *A clean record means "nothing detected", never "nothing there".*

### 6.4 For §3, as clause 8 (this is rec #7)

> **8. RECORD YOUR `check_claim` OUTPUT.** A pre-registration must contain the verbatim
> verdict of `scripts/seed_claim.py <lo> <hi>` for its block, **including the unresolved-
> sink count** — a claim that passes with unknown sinks has verified nothing unless the
> silence is priced. §3.4 already demands "confirmatory seeds never used for anything";
> this makes that clause CHECKABLE rather than an honour system.
>
> Enforced by `tests/test_instrument_seams_migrated.py`, with an explicit committed
> grandfather floor (`results/prereg_claim_floor.json`, 95 documents) so it binds every
> rung AFTER it and none before. **A MENTION IS NOT A RECORD:** "I ran check_claim and it
> was fine" does not satisfy the gate; the pasted output does.

### 6.5 For the burned-seed ledger

> | **95000–95999** | **INSTRUMENT SEAMS — the two instrument defects made structural refusals — CONSUMED (randomised positive controls 95000–95019 plain literals; 95100–95119 PEP-515 underscore literals, spent deliberately in the spelling that defeated a real `grep` pre-launch check)** (`VISION_INSTRUMENT_SEAMS_PREREG.md`, committed BEFORE the run at **`356978bb`**; results `VISION_INSTRUMENT_SEAMS_RESULTS.md`; gate `tests/test_instrument_seams_migrated.py`; modules `domains/preamble_audit.py`, `domains/seed_record.py`; base `main` HEAD **`ee0a1af2`**; engine **`a1d350bbd23b`** own build, NO Rust added). **MEASURED fill 0.04 of the declared block — 95020–95099 and 95120–95999 remain CLEAN.** |

### 6.6 Still open from earlier rungs, unchanged and NOT mine to apply

Recs **#1** (rows for 38000–38099 and 40000–40099) and **#3** (the resolution rung's
79200–79399 overlap) remain **NOT APPLIED**, and are now visible in
`results/seed_ledger_measured.json` under `undeclared_runs` rather than only in a prior
rung's prose.

---

## 7. FOR THE NEXT RUNG

Findings, not a plan; sequencing is the supervisor's.

1. **Seven one-line fixes.** Each file in `results/preamble_audit_floor.json` needs
   `ep.engine_preamble()` where it currently only calls `ep.provenance_line()`. Delete each
   from the floor as it lands. **They are the population the defect actually lives in.**
2. **814 entrypoints reach the engine without pinning it** (554 via the §10.2-broken
   convention). Not gate-grade, and no rung should try to fix them wholesale — but any rung
   that *measures* through one of them is measuring on an unpinned engine.
3. **`provenance_stamp()` is adoption-dependent and therefore weak.** If a rung finds a
   seam where results-writing is structurally funnelled, that is the stronger home.
4. **My own fill is 0.04.** The 1000-seed block is the wrong unit for a rung that needs 40
   seeds. If blocks were sized to measurement rather than to convenience, the ledger's
   median fill problem would mostly dissolve on its own.
