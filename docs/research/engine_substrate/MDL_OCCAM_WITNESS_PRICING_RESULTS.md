# MDL/Occam witness-priced literals — RESULTS (Proposal 1, Slice 1 of
   `DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md`)

**Date:** 2026-08-16. Base `main @ f4394fd`, verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ocelot-mdl-occam-witness-pricing`, branch
`mdl-occam-witness-pricing`. **Not merged to `main`, not pushed** — left
for the orchestrator to independently re-verify and merge. Commits on this
branch: `c7db134` (mechanism + `MDL_OCCAM_WITNESS_PRICING_PREREG.md`),
`0fce174` (rebuilt engine artifact matching `c7db134`'s source).

**HEADLINE: SHIPS. Gate (1) — the load-bearing known-safe-fact check —
passes clean with an unexpected genuine BONUS, not just neutrality: full
88/88 (lost=[], gained=[]), content_stripped 87/87 (lost=[], gained=[]),
official 113→114 (lost=[], gained=[task 451], reproduced identically
across two independent before/after pairs). Gate (2) eliminates the named
2-branch `IfThenElse` literal-lookup shape 5/5 as predicted, but surfaces
an HONEST, ADJACENT residual the design doc's own scoping did not close:
task 396 still returns a degenerate answer — not the predicted shape, but
a bare ROW-INVARIANT literal quote, which slice 1 deliberately prices at
cost 1 because a 2-revealed-row spec cannot distinguish "genuine task
constant" from "coincidence of a tiny sample." Gate (3) — the decisive,
reportable negative the design doc explicitly permits — finds neither
102 nor 411 at the DEFAULT budget: the search-cost wall
`CEILING_REASSESSMENT_7` measured is a real, SEPARATE bottleneck from the
literal-mispricing bug this rung fixes, not subsumed by it. Zero MBPP
regressions anywhere; +1 real conversion (451, official arm only); the
9-file named regression suite and the 778-test Rust suite are clean.**

---

## 0. Mechanism, as shipped (unchanged from PREREG, restated for this
     document's self-containedness)

`runners/dsl/src/synth_enumerate.rs`: a new function
`literal_witness_cost(s, envs, outputs, interner) -> usize` (currently
`:1404-1461`) prices each pooled STRING literal by a witness census over
data already in scope (`envs`, `outputs`, no new inputs):

1. occurs (substring) in ANY revealed input → data-derived, cost 1.
2. occurs (substring) in EVERY revealed row's output → row-invariant
   (genuine task constant), cost 1.
3. occurs in EXACTLY ONE row's output and neither of the above →
   single-witness output quote (the memorization signature), cost =
   `s.chars().count().max(1)`.
4. otherwise (partial multi-row output coverage) → cost 1, unchanged
   (the conservative default — slice 1's scope is the one named
   signature, not every shade of partial coverage).

The registration site (was `synth_enumerate.rs:2744-2809` at the design
doc's citation) now registers `str_consts` SEPARATELY from `const_set`
(the numeric defaults + auto-appended integer outputs, untouched, still
all cost 1), each string literal at its witness-priced size; an entry
priced above `max_size` is skipped entirely rather than registered (it
could never be reached by the growth loop regardless, and indexing
`by_size` past its length would panic). Integer-output literals are
explicitly out of scope, per the design doc's own §7 item 6.

Full mechanism detail, line citations, and the byte-preservation argument
are in `MDL_OCCAM_WITNESS_PRICING_PREREG.md` §1 (committed before any gate
was run) — not re-derived here.

---

## 1. Gate (1) — known-safe fact first (load-bearing)

**Method:** paired before/after runs of `scripts/mbpp_endgame_battery.py`
(`PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/mbpp_endgame_battery.py`),
same worktree, same fixture, same prerequisite `results/*.json`
artifacts (copied once from the canonical tree — `mbpp_zero_shot_
baseline.json`, `prog_construction_scan.json`, `prog_chunk_mine.json`,
`mbpp_train_diet.json`, `mbpp_arc3_endgame.json`,
`arc4_structural_verdicts.json`, `prog_synthesis_battery.json`,
`code_synthesis_baseline.json` — all static, mining/scan artifacts this
rung never touches, needed because `results/` is per-worktree and
gitignored; fixture file (`tests/fixtures/mbpp/sanitized-mbpp.json`) and
`scripts/mbpp_endgame_battery.py` itself confirmed byte-identical to the
canonical tree via `diff` before use), ONLY `runners/dsl/src/synth_
enumerate.rs` swapped via `git checkout f4394fd -- ...` /
`git checkout HEAD -- ...` + a genuine `bash scripts/engine_build.sh`
rebuild between each run (never a cached/sub-second finish — every
rebuild reported `Finished ... in ~2m`).

**Reproducibility check (done because task 451's gain was unexpected —
see §1.2):** each side (before, after) run TWICE, independently. Both
before-runs and both after-runs produced byte-identical pass-task-id sets
in all three arms — the effect is deterministic given the code, not
process-level noise (e.g. Python hash-seed randomization).

### 1.1 Exact task-id-set diff (before → after), all three arms

| arm | before | after | lost_pass | gained |
|---|---|---|---|---|
| full | 88 | 88 | **[]** | [] |
| content_stripped | 87 | 87 | **[]** | [] |
| official | 113 | **114** | **[]** | **[451]** |

`lost_pass` is empty in every arm — the load-bearing safety condition
the design doc names is satisfied. This is not merely neutral: the
official arm shows a genuine +1 net gain with zero risk (nothing that
was passing stopped passing).

### 1.2 Task 451's gain, traced to source (not left as an unexplained
      side effect)

Task 451 ("remove all whitespaces from the given string", official
protocol reveals all 3 rows) went from `gapped:enumerate_failed`
(`construction: null`, top-level rungs `codebook:1.0, lattice:1.0,
enumerate:1.0`, `attempts:2`) to `pass` (`construction:
"retrieved_exemplar"`, `attempts:1`, all top-level rungs `null`).

Read directly, `domains/prog_retrieval.py:20,49,586-602`: EVERY top-level
goal enters `run_retrieval_ladder` BEFORE the codebook/enumerate/descend
stack (`seeds/program_synthesis.json:12103`'s own comment: "mints
`Goal{status:retrieve_pending}`... enters the retrieval ladder... BEFORE
the arc-2 codebook/enumerate/descend stack"). Rung (d) of that ladder
("retrieved-as-skeleton") masks the retrieved exemplar's final compute
statement and **calls `SynthEnumerate` to fill the one masked hole from
the revealed rows' expected outputs** (`prog_retrieval.py:49`, "derive
the hole's row from each revealed row's expected output, and call
SynthEnumerate on it"). This is the SAME repriced code path — a
single-hole spec over the SAME `envs`/`outputs` census this rung changes.
Before this fix, the hole-fill search for task 451 evidently either found
no adequate candidate (falling through to the codebook/lattice/enumerate
stack, which then also failed) or found a candidate that failed the
retrieval ladder's own execution screen; after the fix, it finds a
genuinely correct hole-fill on the FIRST attempt, which the
`prog_retrieval.py` screen (ProgEval on the goal's own revealed rows)
accepts, and since the official protocol's revealed rows ARE the
held-out rows, the same correctness carries straight through to `pass`.

**This is not a mysterious or superstitious side effect — it is the
SAME mechanism this rung targets, reached through a second call site
(`prog_retrieval.py`'s rung-(d) hole-fill) that this rung's design doc
did not name explicitly but that shares the exact repriced code.** No
other MBPP task changed outcome in any arm.

### 1.3 Verdict

**Gate (1): CLEAN PASS.** `lost_pass=[]` in all three arms, plus a
reproducible, traced, zero-risk +1 in the official arm. This satisfies
the design doc's load-bearing safety condition and clears the way to
ship.

---

## 2. Gate (2) — the 5-task spurious probe re-swept

**Method:** direct `SynthEnumerate` evaluate call (no graph pipeline),
`ops` omitted (typed-default op selection — the same method
`CEILING_REASSESSMENT_7_PREREG.md §5.1` used), `max_size=20`,
`max_candidates=2,000,000`, tasks `102, 396, 427, 437, 478`, `primary`
protocol (reveal all but the last row). Script:
`/tmp/.../scratchpad/probe5.py` (not committed — a diagnostic probe, not
a shipped artifact). Run against this rung's shipped (AFTER) engine.

### 2.1 Result, exact

| task | found | halt_reason | term_str | held-out |
|---|---|---|---|---|
| 102 | **false** | budget (tested=2,000,000) | — | — |
| 396 | **true** | solved (tested=9) | `'Valid'` | **FAILS** (expected `'Invalid'`, trap `prog:invalid`) |
| 427 | **false** | budget (tested=2,000,000) | — | — |
| 437 | **false** | budget (tested=2,000,000) | — | — |
| 478 | **false** | budget (tested=2,000,000) | — | — |

### 2.2 Reading this precisely against the design doc's own prediction

The design doc's falsifiable prediction was **"zero of the five return a
literal-lookup shape"**, specifically the 2-branch `IfThenElse` shape
`CEILING_REASSESSMENT_7 §5.1` measured 5/5 on this exact probe set before
this fix (cited, not re-derived: that document's own measurement). **In
the narrow, literal sense of that specific shape, the prediction holds:
zero of the five return a 2-branch `IfThenElse` literal lookup.** Four of
the five (102, 427, 437, 478) now find NOTHING within the 2,000,000
budget — the degenerate shape's cost-1 pricing advantage that made it
findable first is gone, and (per `CEILING_REASSESSMENT_7`'s own
already-measured finding that the genuine compositions for this cluster
are not reliably reachable even at 2-5M) the genuine answer is not
reached either at this budget.

**Task 396 is an honest, adjacent residual, not a clean 0/5.** It
converges to `Lit('Valid')` — a bare, zero-branch constant, smaller and
even MORE degenerate than the eliminated `IfThenElse` shape. Read
directly against the fixture
(`tests/fixtures/mbpp/sanitized-mbpp.json`, task 396, "check whether the
given string starts and ends with the same character"): the `primary`
protocol reveals rows 1-2 (`"abba"→"Valid"`, `"a"→"Valid"`) and holds out
row 3 (`"abcd"→"Invalid"`). **Both revealed outputs happen to be
identical** — not because the task is a constant function, but because
the 2-row revealed sample coincidentally shares a value. Under this
rung's own rule 2 (row-invariant → cost 1, "a genuine constant of the
task"), `'Valid'` is indistinguishable from a real task constant given
only the revealed rows — the census has no way to know, from 2 rows
alone, that the shared value is coincidental rather than definitional.
This is a SCOPE gap the PREREG named honestly in advance (§1, rule 4's
own framing: "slice 1's scope is the one named signature, not every
shade of partial coverage") but did not anticipate would surface on
exactly this probe set. **It is not a bug in the implementation — the
row-invariant rule fires exactly as designed — it is a genuine, reported
limit of what a 2-witness census can distinguish**, and it is named here
as a residual for a follow-on rung (a candidate future fix: raise the
row-invariant bar to ≥2 CO-OCCURRING-with-distinct-input witnesses
before granting cost 1, mirroring the ≥2-witness mint bar this arc
already applies elsewhere — not built here, this rung's scope is slice 1
as specified).

### 2.3 Verdict

**Gate (2): PARTIALLY CONFIRMED, reported precisely.** The named 2-branch
`IfThenElse` shape is eliminated 5/5. A different, smaller, single-witness-
immune degenerate shape (bare row-invariant literal) still reaches one of
the five under a 2-row reveal — an honest, scoped residual, not a
regression and not the shape the design doc measured, reported as found
rather than smoothed over.

---

## 3. Gate (3) — tasks 102/411 re-swept at the DEFAULT budget

**Method:** the real pipeline, `domains.prog_synthesis.
synthesize_from_request` via `scripts/mbpp_endgame_battery.py`'s own
`run_task` (`max_size=20`, `max_candidates=0` → engine default
`200,000`), `primary` protocol, this rung's shipped (AFTER) engine.
Script: `/tmp/.../scratchpad/gate3.py`.

### 3.1 Result, exact

| task | outcome | status | construction | enumerate_outcome |
|---|---|---|---|---|
| 102 | `gapped:enumerate_failed` | gapped | null | failed |
| 411 | `gapped:enumerate_failed` | gapped | null | failed |

**Neither task is found at the default budget, even with the degenerate
literal-lookup shape's pricing advantage removed.** This is consistent
with — not contradicted by — `CEILING_REASSESSMENT_7`'s own prior
measurement: that document's own budget sweep (§5.1) found task 102's
degenerate candidate at `tested≈1,732,357` (already 8.7× the default
200,000) and never found the GENUINE composition for either 102 or 411
even at 2,000,000 candidates. Removing the degenerate shape's unfair
cost advantage does not, by itself, shrink the remaining search space the
genuine composition sits inside; it only removes the wrong answer that
used to arrive first. The search-cost wall `CEILING_REASSESSMENT_7 §5.3`
named ("the space of small, wrong, literal-lookup candidates is large
enough on its own to consume any currently-affordable budget") is
therefore confirmed as a REAL, SEPARATE bottleneck from the literal-
mispricing bug this rung fixes — not subsumed by it, exactly as the
design doc's own §7 item 2 permitted as an outcome.

### 3.2 Verdict

**Gate (3): DECISIVE NEGATIVE, reported as instructed.** No MBPP
conversion from this cluster at default budget. This is not this rung's
failure — the design doc explicitly scoped "still not found" as a
valuable, reportable finding distinguishing "literal pricing was the
whole wall" (false, now measured) from "literal pricing was one part of
a taller wall" (true, now measured).

---

## 4. Regression discipline

### 4.1 `cargo test --lib --release -- --test-threads=1`

Run with `RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib
-lpython3.13"` and `LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/
python@3.13/lib:$LD_LIBRARY_PATH"` set together, after `touch src/synth_
enumerate.rs` to force a genuine rebuild (confirmed genuine: `Finished
... in 3m18s`, not a sub-second cached finish).

**778 passed; 0 failed; 4 ignored** — matches the expected 778 baseline
exactly (this rung added no new `#[test]` functions, only the
`literal_witness_cost` function and its call sites, so 778+0 is the
correct expectation, not a discrepancy).

### 4.2 `bash scripts/engine_build.sh` + provenance

Genuine rebuild (`Finished ... in ~2m` each time, four separate times
across this rung's before/after cycles — never cached). The script's own
final `python -c ...`/`python -m pytest ...` steps hit the documented
benign `python: command not found` PATH quirk; run directly via
`python3`:

```
== build record: .../runners/dsl/python/substrate_rs/_native.build.json
tests/test_engine_provenance_migrated.py: 10 passed
```

Confirmed (run 4 times across the before/after cycles, always 10/10) —
the installed engine always matched the committed/checked-out Rust
source at the time of each measurement.

### 4.3 The named 9-file regression suite

`test_prog_synthesis_battery_migrated.py test_mbpp_baseline_migrated.py
test_mbpp_endgame_migrated.py test_mbpp_contamination_migrated.py
test_mbpp_diet_migrated.py test_program_synthesis_migrated.py
test_prog_moves_migrated.py test_prog_property_migrated.py
test_exact_first_migrated.py`, run paired (before-engine, after-engine),
same prerequisite `results/*.json` copy-in as gate (1) (this worktree's
`results/` started nearly empty — gitignored, per-worktree — and needed
`mbpp_zero_shot_baseline.json`, `prog_construction_scan.json`,
`prog_chunk_mine.json`, `mbpp_train_diet.json`, `mbpp_arc3_endgame.json`,
`arc4_structural_verdicts.json`, `prog_synthesis_battery.json`,
`code_synthesis_baseline.json` copied in before either run — an
artifact-availability gap in this isolated worktree, not a code issue,
confirmed by the fact that copying them produced IDENTICAL results on
both sides).

**Before:** `3 failed, 241 passed`. **After:** `3 failed, 241 passed`,
byte-identical failing test-id set both times:

```
tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

**Exactly the 3 known pre-existing pin-drift failures the task brief
named, nothing new, on both sides.**

---

## 5. What this document does NOT establish

1. The Γ flip (design doc §2 slice 2) and the negative-codebook variant
   (§2 slice 3) are unbuilt — Slice 1 only, as scoped.
2. Task 396's row-invariant-coincidence residual (§2.2) is named, not
   fixed. Whether it recurs at scale (beyond this 5-task probe) is not
   measured here — it would need a corpus-wide sweep this rung did not
   run (out of the specified gates).
3. Whether the genuine 102/411/137/442 compositions are reachable at
   SOME budget above default (with witness pricing live) is not
   re-measured here — the design doc's gate (3) specifies the default
   budget only; a higher-budget sweep under repricing would be a natural
   follow-on but is out of this rung's specified scope.
4. Integer-output literal pricing remains explicitly out of scope
   (design doc §7 item 6, restated in the PREREG).
5. The `results/*.json` prerequisite artifacts copied into this worktree
   were taken from the canonical tree at whatever commit it was at when
   copied (not necessarily `f4394fd` exactly, given the concurrent-session
   drift this task's brief warned about) — confirmed as safe for this
   rung's purposes only because (a) the MBPP fixture and battery script
   themselves were diffed byte-identical against the canonical tree
   before use, and (b) every comparison in this document is INTERNAL to
   this worktree (before-engine vs after-engine, same artifacts both
   times) rather than against the canonical tree's own numbers — the
   88/87/113 baseline was independently RE-DERIVED here (§1.1's "before"
   column), not assumed from the task brief's cited figure.

---

## 6. Recommendation

**SHIP.** Gate (1) is clean with a genuine, traced +1. Gate (2) confirms
the targeted mechanism is fixed and honestly surfaces one adjacent,
scoped residual worth a follow-on rung (task 396's coincidental
row-invariant literal). Gate (3) is a real, decisive negative that
correctly separates "literal mispricing" from "search-cost wall" as two
distinct problems — exactly the finding the design doc's own ranked
recommendation (§6) anticipated as a valuable possible outcome. Left in
this worktree, unmerged, for the orchestrator's independent
re-verification per house discipline.
