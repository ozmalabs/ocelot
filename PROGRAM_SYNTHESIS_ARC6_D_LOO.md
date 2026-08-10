# ARC 6 SEAM D — THE DISCRIMINATING MEASUREMENT: **LEAVE-ONE-OUT IS 0/36**

**Date:** 2026-08-01. Measures `PROGRAM_SYNTHESIS_ARC6_D.md` (HEAD
`9c54925d7598565d8659c2d5b7dca62c6fdd801a`). Nothing Seam D built was
modified: `seeds/program_properties.json`, `domains/prog_property.py` and
the seed rules are read-only inputs here.

Driver: `scripts/arc6_d_loo.py` → `results/arc6_d_loo.json`.
Isolated `git worktree` at committed HEAD, this tree's own
`_native.abi3.so` (`sha256 5c1b472fe674…`, the engine
`results/arc5_final.json` was measured on). Twin-run deterministic:
`content_sha256 = 7504de7ada7534ef0276d8707262e97d28ce3b68b86b9a25aa480d3533f6ec14`
on two consecutive runs. 8.4 s.

---

## 0. THE VERDICT, first, because it is a null

Seam D's headline is **36/36 (100%) self-detected wrongness** on the frozen
36-task residual. **Almost none of it survives.**

| measurement | authored | leave-one-out |
|---|---|---|
| frozen 36-task residual | **36/36** | **0/36** |
| arc-4 S5 denominator (104) | 72/104 | 36/104 (= the property rung's contribution is **+0**) |
| arc-5 wrong accepts caught (79 `accepted_holdout_fail`) | 35/79 | **0/79** |
| tasks refuted by a **foreign** atom, anywhere in 257 | — | **0** |

**Every one of the 36 PropertyAtoms is a per-task key.** Remove a task's
own atom and the other 35 refute nothing: all 36 tasks go straight back to
`status='accepted'` with a Program node minted — the wrong program sails
through. There is no foreign refutation anywhere in the 257-task split, at
any level of the atom's own gate.

**What IS real, and is not diminished by the null:** the machinery. The
self-verify gate, the witness execution through the shared `ProgEval`
term, the reject-before-accept wiring into `ps_accept`, and the
explainability contract all work exactly as `PROGRAM_SYNTHESIS_ARC6_D.md`
describes, and the soundness result got *stronger* under a
widened sweep (§2). What is not real is the **capability claim**: 36/36 measures
the authoring, not a property faculty. This is the shape of the six
coincidental fits this project has already caught, and it is the largest
one — caught before it was quoted onward.

---

## 1. M1 — LEAVE-ONE-OUT: **0/36**

For each of the 36 residual tasks: that task's own atom is removed, the
other 35 stay active, and the verdict is re-run **through the real seed
rules** (`psy.pump`), replaying the frozen `full_r3` accepted IR into a
fresh minimal goal — the identical harness
`tests/test_prog_property_migrated.py` uses.

**Control (full 36-atom table), reproduced live in the same process:
36/36**, ids exactly

```
17 56 67 72 77 79 91 96 105 113 143 165 167 171 224 235 238 244 250
256 268 279 291 292 295 300 311 388 389 392 405 441 444 452 453 455
```

(32 terminate `gapped:property_verdict_reject`; 4 are still inside the
standing CEGIS reopen lane at the end of the replay budget — the same
reopen dynamic Seam D §2.3 already documents. All 36 fire.)

**LEAVE-ONE-OUT — survives (refuted by a FOREIGN atom):**

```
(empty)
```

**LEAVE-ONE-OUT — does not survive:**

```
17 56 67 72 77 79 91 96 105 113 143 165 167 171 224 235 238 244 250
256 268 279 291 292 295 300 311 388 389 392 405 441 444 452 453 455
```

All 36. And the failure is total, not marginal: in the LOO arm every one
of the 36 is `status='accepted'`, `program_minted=True`,
`fired_properties=[]`, `any_fired=0.0`. Not one foreign atom so much as
*applies*, let alone refutes.

The brief asked for **constructed witnesses** for any claim that an atom
correctly refutes a task it was not authored for. **There is no such claim
to witness.** The count is zero, so the strongest-evidence requirement is
moot — reported here rather than quietly dropped.

---

## 2. M2 — FALSE-REFUTATION SWEEP, WIDENED: **0/35 on a widened, later population**

Seam D's published `0/21` is over the frozen arc-3 population's correct
programs only. Widened here to the **full 257-task runnable split** of the
settled arc-5 measurement (`results/arc5_final.json`, 35/257), replaying
every task that has an accepted candidate IR (114 = 35 `pass` + 79
`accepted_holdout_fail`) with the **full 36-atom table**.

**False refutations on the 35 currently-passing tasks:**

```
(empty)   — 0/35
```

The 35 passing ids all survive intact:
`16 20 58 59 69 82 84 85 89 90 127 132 135 138 139 142 145 227 233 234
266 276 278 281 309 312 394 404 406 410 433 443 458 472 477`.
**35/257 is not reduced.** The soundness claim holds on 35 correct programs rather than 21 (1.67x
the gated population), across a 114-candidate replay rather than 57 (2x
the accepted population), and over the *later* arc-5 accepted programs
rather than only the arc-3 ones.

**Reach on genuinely wrong accepts, same run.** Of the 79 arc-5
`accepted_holdout_fail` tasks, **35 fire**:

```
17 56 67 72 79 91 96 105 113 143 165 167 171 224 235 238 244 250 256
268 279 291 292 295 300 311 388 389 392 405 441 444 452 453 455
```

— every one an authored id, and every one fired **by its own atom**
(`ahf_fired_by_a_foreign_atom_ids = []`,
`ahf_fired_outside_the_authored_36_ids = []`). The remaining **44 wrong
accepts are untouched**:

```
19 57 61 62 63 65 66 70 95 100 101 116 119 129 130 133 162 166 168 223
245 253 267 270 271 284 286 287 294 296 306 398 400 407 409 425 431 438
446 461 463 464 471 476
```

Under LOO that 35/79 becomes **0/79**.

(The 36th authored id, **77**, is not in this population: its arc-5
outcome is `gapped:enumerate_failed` — no accepted candidate to replay.)

---

## 3. M3 — CROSS-TASK FIRING: the atoms are lookup keys, and the one exception proves it

Atoms are keyed by prompt substrings AND-matched, plus an `arg_count`
guard, plus self-verification against the goal's own revealed rows. Three
widening levels, over all 257:

| level | tasks | of which by a **foreign** atom |
|---|---|---|
| **cue_match** (prompt substrings hit) | **37 / 257** | **1** |
| **applicable** (cue + `arg_count` + self-verify) | **36 / 257** | **0** |
| **refuted** (applicable + witness mismatch on the real candidate) | **35 / 257** | **0** |

The 36 applicable tasks are exactly the 36 authored ids. **35 of the 36
atoms cue-match only their own task** — literally a one-to-one key. The
cue grammar makes this structural rather than accidental: 35 of the 36
atoms carry a **single** phrase, lifted verbatim from their own task's
prompt (`"perimeter of a square"`, `"bell numbers"`, `"twice its
reverse"`, …), and one carries two.

**The single exception is the most informative row in this whole
measurement.** `prop_surface_area_cube` (authored for task **441**,
`"surface area of a cube"`, reference `6a²`) cue-matches task **266**:

> *"Write a function to find the **lateral surface area of a cube** given
> its side length."*

Task 266's program is **correct** (it is one of the 35 arc-5 `pass` ids),
and lateral surface area is `4a²`, not `6a²`. So the one time an atom
reached past its own task, it reached **the wrong relation onto a correct
program** — a false refutation that would have taken 35/257 down to
34/257. It did not fire because **`_self_verify_atom` blocked it**: task
266's own revealed rows (`5 → 100`) contradict `6a²`.

That is a genuine, load-bearing soundness win for the design — and, read
honestly, it is also the shape of the whole result: cross-task reach in
this table happens once, and when it happens it is *wrong*. The
self-verify gate is doing the work that the "property" is claimed to do.

---

## 4. M4 — THE HONEST FRAMING OF 58.7%

The same 104-task denominator arc-4 S5 measured
(`results/arc4_endgame.json` `no_structural` arm's
`accepted_holdout_fail` rows), replayed in **three arms in one process
under identical conditions**. Self-detected wrongness = the candidate
never reaches a clean accept (`status != 'accepted'` OR no Program
minted).

| arm | self-detected | delta vs property-off |
|---|---|---|
| property atoms **OFF** (structural D1–D3 only) | **36/104** | — |
| **full 36-atom table (AUTHORED)** | **72/104** | **+36** |
| **LEAVE-ONE-OUT (TRANSFERABLE)** | **36/104** | **+0** |

`arm_leave_one_out.ids` is **byte-identical** to `arm_property_off.ids`.
The 36 ids the authored arm adds are exactly the 36 authored task ids —
all 36 of the residual are inside this denominator — and all 36 are lost
again under LOO (`ids_lost_from_authored_to_loo` = the full authored 36).

**Side by side, plainly:**

- **AUTHORED: 72/104 (69.2%)** — the shape of Seam D's published 61/104.
  This number is the atom table restating its own authoring.
- **LEAVE-ONE-OUT: 36/104 (34.6%)** — identical to the structural-only
  rung. **This is the transferable claim, and the property rung's
  transferable contribution to it is zero.**

**Named condition difference, not averaged.** The property-OFF arm here is
**36/104, not arc-4 S5's published 26/104**. Two conditions differ and
both are stated rather than reconciled by fiat: (a) **the engine** — the
`substrate_rs` binary was rebuilt between arc-4 and arc-5, and
`results/arc5_final.json`'s own `discrepancy_investigation` shows that
rebuild alone moved 34 → 32 by correcting two coincidental fits; (b) **the
harness** — this is a minimal-goal *replay* of each row's frozen IR
through `psy.pump`, not a full live battery re-run of the
propose/lattice/screen pipeline. The claim made here is therefore the
**within-run paired delta across the three arms**, all taken in one
process on one engine. The absolute baseline is not being restated, and
Seam D's 61/104 is not being contradicted on its own terms — what is being
contradicted is the reading of it as transfer.

---

## 5. What this does and does not license

**Does not license:** "the substrate can detect 100% of its residual
wrongness by understanding task properties." The measured transfer is
**0/36**, **0/79**, **+0/104**. On this evidence the property table is a
36-entry answer key with an execution-checked front end, and the 36/36 is
a restatement of `PROGRAM_SYNTHESIS_ARC6_M0_CD.md §2.2`'s per-task table.

**Does license:**

1. **The mechanism is built and sound.** `0/35` false refutations on a
   wider, later correct-program population (35 correct programs vs the
   gated 21; 114 replayed candidates vs 57) — Seam D's own soundness
   claim survives widening, which is the rarer outcome.
2. **The self-verify gate is load-bearing, and it is measured, not
   asserted.** The single cross-task reach in 257 tasks was a wrong
   relation aimed at a correct program, and the gate stopped it. That is
   the gate earning its place, live.
3. **The binding constraint is now named and it is the cue grammar, not
   the reference library.** 35/36 atoms carry one verbatim prompt
   substring; reach is one-to-one by construction. Any transfer claim
   needs atoms authored from a **generic vocabulary** (a "perimeter of a
   regular n-gon" family, a "count things satisfying P below n" family)
   and, critically, **scored on tasks that were not used to author them**
   — the 44 uncaught arc-5 wrong accepts listed in §2 are the honest
   held-out population for that, and they are named here in advance.

**The standing rule this reinforces:** a per-task-authored detector scored
on its own authoring population produces a 100% that means nothing. The
LOO arm costs 8 seconds and is the whole difference between a headline and
a result.

---

## 6. What broke while measuring (recorded, because it is the isolation failure mode itself)

**The isolated worktree silently imported the CANONICAL tree's engine.**
The first run of `scripts/arc6_d_loo.py` died with
`ValueError: bad Term JSON: UnknownTermType("ProgSeq")` at
`prog_retrieval.ensure_exemplar_store`. Cause: `site-packages`'
`substrate_rs.pth` is an **absolute** path into the canonical tree and
`_native.abi3.so` is gitignored, so a fresh worktree resolves someone
else's binary. `conftest.py` handles this for pytest via
`domains.engine_provenance.engine_preamble()`; a **script is not pytest**
and must call it itself (§10 rule 3). Fixed by calling
`engine_preamble()` before `import substrate_rs`, and by copying this
tree's `.so` into the worktree — verified `sha256 5c1b472fe674…`, the same
engine `results/arc5_final.json` records.

This is exactly the failure the "measure from an isolated worktree"
discipline exists to prevent, and it fails *loudly* only by luck (the
canonical tree's binary happened to lack `ProgEval`; had it merely been a
different build, the run would have produced numbers silently).

Nothing else broke. No test was run or changed, no seed or faculty file
was touched (`git status` clean over `domains/`, `seeds/`, `tests/`), and
`scripts/arc6_a_ceiling.py` / `results/arc6_a_ceiling.json` (the
concurrent A-ceiling measurement) were not read or written.

---

## 7. Files

`scripts/arc6_d_loo.py` (re-runnable, deterministic — compare
`content_sha256`), `results/arc6_d_loo.json` (all four measurements with
paired id lists, per-task and per-atom detail), this file.
