# PROGRAM SYNTHESIS (P1–P6) — PRE-REGISTRATION

**Written and committed at P0, before any P1 Rust, any new seed rule, or any
codebook scan exists.** Companion to `PROGRAM_SYNTHESIS_PLAN.md` (the design)
and `results/code_synthesis_baseline.json` (the frozen enumerated baseline,
gated by `tests/test_code_synthesis_baseline_migrated.py`). This file registers
the hypotheses, the gates, the protected controls, and what a null means —
per phase — so no later rung can move a goalpost it did not declare.

- **branch (as observed):** `worktree-program-synthesis-plan`
- **base SHA (as observed):** `c3fd855d22dc08404e781571c7139c7962ac3ce1`
- **engine:** prebuilt `runners/dsl/python/substrate_rs/_native.abi3.so`
  (no rebuild at P0; P1+ builds are their own provenance steps)
- **condition:** `OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1`, full seed set
  (`WorldAdapter(seeds=()) + load_all_seeds`), scan scope `domains/` only
  (`scripts/` is documented pathologically slow for this scan —
  `code_curriculum_run.baseline_measurement`'s measured scoping note)

## §0 — STANDING RULES THIS ARC RUNS UNDER (inherited, binding)

1. **A BASELINE IS A LIST OF IDENTITIES, NEVER A COUNT OR A CHARACTERISATION**
   (the 2026-07-21 retraction). Every phase reports its deltas as identities
   moving between lists (`file + qualname`, battery request strings, per-frame
   residual node ids) — a count can be held; a list has to be read.
2. **POWER THE GATE BEFORE THE ENDGAME** (run-15 rule). Deltas within ~3× the
   per-episode step are not results. No headline number is quoted before the
   P6 powered battery (n ≥ 100/arm, Wilson CIs).
3. **SYNTHETIC-PROVEN MECHANISM ≠ BENCHMARK VALUE.** Every mechanism gate
   (round-trip laws, fixture parities, source audits) is reported as a
   mechanism result; capability claims come only from the powered battery.
   Both get reported.
4. **EVAL-SUBSET COVERAGE IS PART OF EVERY CLAIM.** Which languages, which
   strata, which scan scope — always stated with the number. The P0 scan is
   `domains/` only and every claim built on it says so.
5. **No Python agent decisions** (CLAUDE.md). Each phase lands with a
   source-audit test on its adapter surface (the ink-suite precedent).
6. **In-frame integer / cross-frame continuous** (2026-07-08 invariant).
   Fuel, indices, arity, counts are integers in the IR; similarity scores,
   timings, toolchain verdicts live in the maps.

## §1 — THE FROZEN BASELINE (P0, measured fresh at this SHA — what IS)

`results/code_synthesis_baseline.json`, all values derived from lists:

- **Scan:** 7177 top-level functions over 668 files under `domains/`;
  construction recognized on 6981; **term-emittable: 27 — the enumerated
  list** (file + qualname + construction), not the number. The plan quoted
  27/6252 from the 2026-07-13 curriculum report; the tree has since grown to
  7177 functions and **the emittable set is still exactly 27** — the wall did
  not move while the corpus grew, which sharpens the P2 hypothesis.
- **Write battery:** the frozen 26-item `WRITE_BATTERY`
  (`scripts/code_curriculum_run.py`, imported verbatim — the gate pins the
  requests byte-identical), **7/26 ok at fresh boot**, per-item outcome +
  failure-reason strings enumerated. NOTE, registered honestly: the plan's
  "(21/26)" is the prior run's AFTER-TEACHING live-agent state; teaching is
  not persisted (`OZMA_SEED_PERSIST_DISABLED=1`), so the reproducible boot
  baseline is 7/26 and THAT is what is frozen. The 21/26 remains recorded in
  `results/code_curriculum/code_curriculum_report.json` as a historical
  measurement of the teach loop, not a boot capability.
- **Fixture corpus:** the isolated 2-file
  `tests/fixtures/code_curriculum/measurement_corpus` scan (3 functions),
  frozen at fresh-boot state — the gate's live re-verification subset.
- **Measured instrument fact (found at P0, recorded, not papered over):**
  the read codebook MINTS while it scans, so construction labels are a
  function of (fresh boot, sorted scan order) — the same fixture function
  labels `learned_code_import_return` when scanned after the 7k-function
  sweep vs `learned_code_while_return` fresh. The baseline therefore freezes
  the gate subset at fresh-boot state on its own agent, and the full scan on
  a second fresh agent (`condition.measurement_order` in the artifact). Any
  P3 claim about codebook growth must state its scan order.

P0 part B (the statement-shape histogram over the scanned corpus, which picks
the P1 IR variant set) is a separate deliverable; its output lands in
`results/` before P1 begins. **P1's variant set may not exceed what the
histogram justifies** — that is the governor on IR creep (plan §6.1).

## §2 — PROTECTED CONTROLS (declared once, in force for every phase)

- **C-BATTERY (the frozen arm).** The 26-item battery is run byte-identical
  at every phase boundary through the SAME path
  (`run_write_battery → write_function_from_request`, never `converse`).
  Its per-item outcomes may improve; **any item flipping ok→fail is a
  regression that blocks the phase** (identity named, not netted against
  gains). The battery text is never edited, extended, or re-weighted —
  P6's larger battery is a NEW instrument measured alongside, never a
  replacement for this arm.
- **C-CODEBOOK-FROZEN (P6).** The powered battery runs one arm with minting
  disabled (no `sd_mint_quantum`, codebook pinned at its pre-scan state).
  "Corpus training helped" is claimable only CI-separated against this arm.
- **C-FIXTURE.** The 2-file measurement corpus outcomes
  (construction + emittability + predict) stay byte-stable at fresh boot
  across all phases until a phase EXPLICITLY declares it changes them (P2
  will: `loopy` becoming emittable is a declared success criterion, and the
  baseline gate's frozen fixture list is then re-frozen IN THE SAME COMMIT
  with the diff enumerated).
- **C-BENCH.** The migrated bench and `results/failure_baseline.json` (the
  enumerated red list) hold; no phase inherits an anonymous new red.

## §3 — P1: HUB IR + `ProgEval` (the enabling primitive)

**H1a.** The statement IR variants the P0-B histogram justifies can be added
as reflected Term subgraph variants satisfying the existing round-trip
`reflect` law (Term → subgraph → Term identical), without touching any
existing variant index.
**H1b.** A fueled, pure `ProgEval` (Dict in → Dict out, no substrate
mutation) agrees with CPython on a fixture corpus of functions built from
those variants.
**H1c (naming).** A minimal naming primitive set lets a rule synthesize an
identifier from spec words without an interner-mutation soundness hole
(fallback registered in advance: Surface(Text)-everywhere — uglier, no
soundness cost; plan §6.3).

**Gates (all mechanism-grade, §0.3):** per-variant reflect round-trip;
`ProgEval` vs CPython agreement on the fixture corpus — **disagreement list
must be EMPTY, and every fixture is enumerated in the results file**; fuel
honesty (fuel exhaustion → `halted:false`, NEVER a value — a wrong answer is
worse than an honest timeout); existing bench + C-BATTERY unchanged.
**Null reading:** if `ProgEval` cannot reach CPython agreement on the
histogram-justified variant set, P2+ do not proceed on the disagreeing
variants; the disagreement list is the result.

## §4 — P2: READING — five frames → hub IR

**H2.** With correspondence rules extended to the P1 variant set, the
Python-frame IR-emittable set grows from the frozen 27-identity list to the
cumulative-mass target **read off the P0-B histogram curve before P2 code is
written** (registered then, in the results file, as a number derived from
data — not ambition). Rust/Lua/LLVM-IR frames each get fixture round-trips
(parse → IR → render → parse → same IR) over the SAME construction families.

**Gates:** the new emittable LIST is diffed against the frozen 27 (every
entry entering or leaving is named); per-frame fixture round-trip green;
per-frame coverage residual is a LIST of unparseable construct ids;
C-BATTERY holds; C-FIXTURE change (loopy → emittable) lands as a declared
re-freeze. **Prediction, registered:** the 27 survive as a subset — any
formerly-emittable function going non-emittable is a regression, named.
**Null reading:** coverage below the histogram target with the variant set
exhausted means the histogram under-modeled real bodies (e.g. Call-extern
density); report the gap-mass breakdown, do not add unjustified variants.

## §5 — P3: THE CODEBOOK + CORPUS STATISTICS (the "training run")

**H3a.** The unchanged sd loop over IR observations grows a
`code_construction_v2` codebook whose minted quanta are DEDUPED by
anti-unification at mint time (same shape twice → ONE quantum) and named
from dominant (predicate, role) — killing the unbounded-concatenation names
(the 24-quanta pile of the curriculum run).
**H3b.** Transition statistics (`trans_logp` on ConstructionBigram nodes)
are earned deterministically from the scan.

**Gates:** mint-dedup test; scan determinism (two fresh agents, same corpus,
same sorted order → identical codebook + stats — the P0 instrument fact
makes scan order part of the claim); codebook-size-vs-coverage curve
recorded with no silent caps; the anti-unify merge gets its own small prereg
BEFORE the big scan (plan §6.6). **Null reading:** if dedup cannot hold
under the full corpus, the scan does not run at scale — a codebook of
concatenated names is worse than a small one.

## §6 — P4: GENERATION — propose–render–verify as seed rules

**H4.** The synthesis loop (goal → ShapeDecode propose → lattice spine →
slot-bind → render → round-trip + `ProgEval` verdict → accept /
counterexample / gap) runs as ONE `run_rules` fixpoint: request in →
**exactly one** accepted Program node + rendered source, with zero Python
decisions on the path (source audit), CEGIS counterexamples as nodes, and
failures filing `SelfConcern{code_write}` through the standing pipeline.

**Gates:** end-to-end fixpoint gate (the ink-suite audit pattern);
`looks_like_write_request` false-positive set from the curriculum run (3 of
4 lesson "exercise requests") re-run and CLOSED or explicitly carried;
C-BATTERY holds — **P4 makes no capability claim from the battery; capability
is P6's** (§0.2, §0.3). **Null reading:** if the fixpoint cannot converge to
exactly-one accepted Program without Python arbitration, the loop design is
wrong — report which rule needed the crutch; do not ship the crutch.

## §7 — P5: RENDERING COMPLETENESS PER FRAME

**H5.** Every P1 variant renders per target frame (python statement-grain
RenderRules; rust value-semantics subset; lua via the taught-at-runtime
path; LLVM IR via `emit_llvm_ir` + CFG, x86-64 through the existing chain) —
and every render HOLE files a gap that heals via the teacher loop live
(the Lua precedent), rather than being exhaustively hand-seeded.

**Gates:** per-frame round-trip suite green on the P2 fixtures; one live
render-gap → teach → re-render demonstration per frame; render gaps are a
LIST per frame in results. **Null reading:** a frame whose subset cannot
round-trip honestly shrinks its declared coverage (stated per §0.4); no
speculative rendering.

## §8 — P6: THE POWERED ENDGAME GATE

**H6.** On a stratified battery of N ≥ 100 tasks × {python, rust, lua,
llvm-ir} (x86-64 scored via the chain; strata: expression /
single-statement / loop / error-handling / multi-function; each task = NL
request + examples; score = verdict-layer pass), the full pipeline is
**CI-separated above BOTH protected controls**: the frozen-P0-capability arm
(what the boot agent could already do) and C-CODEBOOK-FROZEN (no minting).

**Gates:** Wilson CIs per arm per language; per-stratum and per-language
coverage reported with every number (§0.4); the frozen 26-item C-BATTERY
reported alongside as the continuity instrument; failed tasks flow into the
gap → StandingConcern → experiment/adopt pipeline end-to-end at least once,
live. **Decision rule:** arms inside each other's CIs = "no measured
capability gain" is the honest headline, whatever the mechanism gates say
(run-15's lesson, applied prospectively). A CI-separated gain on a subset of
languages is claimed for THAT subset only.

## §9 — WHAT A GLOBAL NULL MEANS

If P1–P5's mechanism gates pass but P6 shows no CI-separated gain over
C-CODEBOOK-FROZEN, the result is: **corpus statistics did not convert to
generation capability at this grain** — the run-16 shape ("bins propose,
continuous decides") predicts the verdict layer, not the proposal layer, may
be where capability binds. That outcome is registered as publishable, and
the next prereg starts from the per-stratum failure lists, not from a
parameter search.

## §10 — MEASURED CONDITIONS AND DEVIATIONS AT P0 (honesty ledger)

- Fresh scan ≠ prior report: **7177 functions / 668 files** vs the
  2026-07-13 report's 6252 / 560 — the tree grew; the baseline is what IS.
  Emittable count unchanged at 27 (identity list now frozen; the two sets
  were never enumerable against each other before — that is the point of P0).
- Battery boot-state is **7/26**, not the plan's quoted 21/26
  (after-teaching state, not persisted). Frozen accordingly.
- Label order-dependence of the scanning instrument (§1, measured):
  recorded in the artifact's `condition.measurement_order`; every future
  codebook claim carries its scan order.
- CPU discipline: builder is single-process; loadavg recorded in the
  artifact alongside the measurement.
