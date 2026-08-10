# LEDGER ATTRIBUTION + THE SEVEN UNPINNED SCRIPTS — PRE-REGISTRATION

**SCOPE HONESTY, UP FRONT (§3 DEVIATION, DISCLOSED).** This rung runs no
experimental arms. Every number in it is a **deterministic property of the tree**
— an AST scan, a git-history diff, an engine-resolution probe — reproducible by
anyone at this SHA with one command. There is no metric to select post hoc and no
arm to drop. **The attribution in TASK 1 was measured BEFORE this document
existed**, which is a real §3 deviation and is recorded here rather than
backdated. What IS pre-registered below is the part that could still have gone
either way: whether pinning the seven scripts MOVES A LANDED NUMBER.

---

## 0.1 SEED CLAIM (§3 clause 8) — verbatim, including the unresolved-sink count

`python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(101000,101999)[1])"`

```
SEED CLAIM 101000-101999: CLEAN -- no collision DETECTED.
  Scope: 805 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**497 unresolved sinks.** Quoted with every number below. *A check that passes
with unknown sinks has verified nothing unless the silence is priced* — and this
rung is auditing the tool that prints that sentence, so it is quoted more
literally than usual.

**DECLARED CONSUMPTION: 101000–101999. EXPECTED DRAW: ZERO.** The controls in
this rung are reverts of REAL files, not randomised plants, so no seed is
required. If the block is returned intact that is recorded as such, and the
vacuity risk it creates (a static rung with no randomised self-audit) is answered
by both-direction controls on real tree state instead.

## 0.2 ENGINE (§10) — own build, printed from inside the measuring process

```
engine a1d350bbd23b @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]
```

Built by `bash scripts/engine_build.sh` (§10.3 — never a hand-rolled `cp`, never
a symlink to canonical). **No Rust added.** The build exists because this rung
compares engine RESOLUTION across two binaries, which is not measurable from a
borrowed one.

## 0.3 ORACLE condition

`data/` is symlinked to canonical (§10.2 rule 2 — a symlink, never a copy;
gitignored so it cannot enter a commit). The oracle is therefore quoted in the
**222/0** condition, with its condition, never bare.

---

## 1. PRE-REGISTERED PREDICTIONS

Written before the engine-resolution probe was run.

* **P1 — the seams rung's §6.6 claim is checkable and I expect it to be WRONG
  in the direction the supervisor already found.** It asserts the 38000/40000
  rows are "NOT APPLIED, and are now visible in `seed_ledger_measured.json` under
  `undeclared_runs`." Predicted: the rows ARE applied, AND the record does NOT
  list them — i.e. hypothesis (b) fails twice, and the second failure is
  demonstrable against the seams rung's OWN committed artifact.
* **P2 — hypothesis (a) contributes ZERO to the 110→493 jump.** The motion rung
  is the named instance; predicted its static footprint is SMALL, not large, and
  that its effect lands in `unresolved_sinks` rather than `undeclared_seeds`.
* **P3 — the dominant cause is neither (a) nor (b).** Predicted: seeds from
  rungs merged between the seams rung's base and HEAD, whose §11 rows have not
  been written.
* **P4 — pinning the seven CHANGES NO LANDED NUMBER.** Predicted: for the six
  that already insert `runners/dsl/python`, engine resolution is unchanged; for
  `value_flood_measure.py`, which resolves purely through the canonical `.pth`,
  resolution CHANGES but output does not, because the Rust source is
  byte-identical across trees. **Registered failure condition: if any measured
  output differs across the two binaries, that is the finding and it outranks
  the cleanup — the seven scripts' landed numbers would need re-running.**
* **P5 — the floor can be emptied without weakening any gate.** Predicted the
  seven repairs are independent one-liners.

## 2. WHAT WOULD FALSIFY THE REPAIR

* Any of the seven still reads `imported_not_called` after the edit.
* The oracle moves off **222/0**.
* `test_instrument_seams_migrated.py` loses a test or drops below 22.
* The emptied floor makes any gate unable to fail. **Both directions must be
  demonstrated on the inverted control before it is believed** — a gate that has
  never been ABLE to fail has not been tested.
