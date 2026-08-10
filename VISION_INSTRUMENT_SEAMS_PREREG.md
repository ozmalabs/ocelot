# INSTRUMENT SEAMS — pre-registration

**PROTOCOL §3. Written and committed BEFORE any number below the line.**

Base: `main` HEAD **`ee0a1af2`** (worktree `worktree-agent-a182430576b3b6012`).

---

## §0.1 ENGINE PROVENANCE — RUN AS ITS OWN STEP, BEFORE THIS FILE WAS WRITTEN

`bash scripts/engine_build.sh` (§10, §11 rule 2 — this tree owns its engine; NEVER a
symlink to canonical, NEVER a `cp` onto the engine path):

```
engine a1d350bbd23b @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]
```

`pytest tests/test_engine_provenance_migrated.py -q` → **7 passed**.

**This rung adds NO Rust.** The build exists only so that nothing I measure is
another tree's binary — which is *exactly* the defect this rung is about, so
measuring it on a shared engine would be self-refuting.

## §0.2 SEED CLAIM — §11 rec #7, applied to myself first

Allocated block **95000–95999**. `python3 scripts/seed_claim.py 95000 95999`, run at
base `ee0a1af2` **before** a single seed was written into any file of mine:

```
SEED CLAIM 95000-95999: CLEAN -- no collision DETECTED.
  Scope: 798 files with seed sinks; 482 UNRESOLVED sink sites tree-wide
         (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**482 unresolved sinks. A CLEAN verdict here is a lower bound on cleanliness, not a
proof of it** (§8) — recorded because "a check that passes with unknown sinks has
verified nothing" unless the unknowns are priced.

## §0.3 SEEDS I INTEND TO SPEND, AND WHY A STATIC ANALYSER MUST SPEND ANY

A static analyser draws no seeds, so its self-audit is vacuous. Declared IN ADVANCE:

| sub-range | purpose |
|---|---|
| **95000–95019** | randomised plant-and-remove positive controls (synthetic prereg / ledger / script fixtures), `default_rng(95000 + i)` written with PLAIN integer literals |
| **95100–95119** | the SAME controls, seeded with **PEP-515 underscore literals** (`default_rng(95_100 + i)`) — spent deliberately so that my own measured record contains the literal form that made the supervisor's pre-launch `grep "90000"` blind to `default_rng(90_000 + seed)` |

**95020–95099 and 95120–95999 are to remain CLEAN.** I will report MEASURED
sub-ranges (§11 rec #4), not the declared block, and I will verify the measured
record against my own tooling.

---

## 1. HYPOTHESES (two-sided; a null is a result, §7)

### H1 — the provenance seam
A gate that certifies **the tree's configuration under its own preamble** cannot
certify **the process that takes the number**. If the verdict is computed from the
`substrate_rs` module actually resident in `sys.modules` of the measuring process, and
that computation is attached to the call every non-pytest entrypoint is already
REQUIRED to make (§10 rule 3, `engine_preamble()`), then a measuring process cannot
take a number on a DIVERGED engine without raising.

*Two-sided:* it may instead prove that the seam is unreachable — that scripts do not in
fact route through `engine_preamble()`, in which case attaching the check there buys
nothing and the honest finding is "there is no unskippable seam in Python, only in
pytest."

### H2 — the preamble is imported but not called
The known instance (a diagnostic that imported `engine_preamble` and never called it)
is one member of a class: *a process that uses the engine without pinning it*. An AST
audit that resolves the **binding** (not the substring, not the docstring) can decide
both `imported-not-called` and `engine-used-without-preamble`.

*Two-sided, and this is the arm I expect to hurt:* if the tree contains many
pre-existing violations, the check cannot be a gate on day one without being
unconditionally red — the failure mode §10.1 names explicitly. I will report the count
BEFORE deciding, and grandfather explicitly if I must.

### H3 — the ledger seam
§11 rec #4 ("record MEASURED sub-ranges, not the declared block") is currently a prose
discipline. Prose cannot be gated without a substring selector, and this arc has now
failed four times on substring selectors. **A MACHINE-GENERATED measured record,
committed and gated for freshness, delivers rec #4's content without parsing one word
of prose.** Any seed added anywhere in the tree then makes the record stale, and the
gate goes red until it is regenerated.

*Two-sided:* the nuisance mode is real and must be named — an unrelated rung that adds
a seed gets a red gate it did not cause. If regeneration is not a single command, this
is ceremony and should not ship.

### H4 — the prereg seam
§11 rec #7 ("a prereg must record its `check_claim` output") fires only if something
reads pregregs. A gate over `VISION_*_PREREG.md` with an explicit, committed
grandfather floor makes it binding on every rung AFTER this one, and on none before.

---

## 2. THE STATISTICS, EXACTLY

This rung measures instruments, not phenomena. Every quantity below is a **count**,
deterministic given a tree state — no sampling, no p-values, no power analysis, and
therefore no n to fix (§3.3 is inapplicable and I say so rather than inventing a
statistic to satisfy it).

| # | statistic | how obtained |
|---|---|---|
| S1 | in-process `source_match` verdict of a measuring process | `engine_provenance()["source_match"]` read inside that process |
| S2 | count of `scripts/*.py` that bind `engine_preamble` and never CALL it | AST binding resolution |
| S3 | count of `scripts/*.py` entrypoints importing `substrate_rs` without a preamble call | AST binding resolution |
| S4 | per-ledger-block MEASURED seed count and sub-ranges | `seed_audit.analyse_tree` (AST) |
| S5 | count of `VISION_*_PREREG.md` recording a `SEED CLAIM` verdict | line scan of the tool's OWN emitted verdict format |
| S6 | my own measured seed sub-ranges | S4 restricted to my files |

## 3. DECISION RULE

1. **A check ships as a GATE only if it is verified to FIRE on a planted real defect AND
   to be GREEN on the clean tree** — both directions, both demonstrated, in the same
   commit. A check demonstrated in one direction only ships as a REPORTER, not a gate.
   (Three provenance gates in this arc sat green for 51 commits and then fired at once
   as false accusations. A gate that has never been able to fail has not been tested.)
2. **Every positive control must be verified to LAND** — I will assert the gate is RED
   with the plant present, and that the plant is inside the subtree the gate scans,
   before I record a pass. A quiet control is a finding to chase, never a pass to log.
   (The seed-claim rung's first control passed silently because it planted in an
   already-declared block; the supervisor's injection test passed because it planted in
   the wrong subtree.)
3. **If S2 + S3 > 0 on the clean tree**, the audit ships with an explicit committed
   grandfather set and gates only on NEW violations. An unconditionally red gate is one
   agents route around, which is worse than no gate.
4. **If regeneration of the measured ledger record is not one command, H3 does not
   ship.** "Do not invent ceremony nobody will run" is the binding constraint.
5. **A null is a result.** If no seam is unskippable, I report that and ship reporters.

## 4. EXACTLY THE LISTED WORK. NO SWEEPS.

Four artifacts, named in advance:

* `domains/engine_provenance.py` — additive: `EngineProvenanceError`,
  `assert_measuring_engine()`, `provenance_stamp()`, and a `strict=` parameter on
  `engine_preamble()`.
* `domains/preamble_audit.py` — new, AST-only, imports no engine.
* `scripts/seed_claim.py` — additive: `--measured` and `--ledger-report`.
* `tests/test_instrument_seams_migrated.py` — the gates and both-direction controls.

**I will NOT edit `VISION_PROTOCOL.md`** (proposed §-amendment text goes in the results
doc; the supervisor applies it). **I will NOT add any file to
`scripts/rung7_vision_bench.sh`'s list** — that list IS the oracle and moving a
protocol-load-bearing number is not a rung's call. **I will not edit another rung's
prereg, results, seed or test** (§11 rule 4).

## 5. §9 — DEFAULTS PRESERVE COMMITTED RESULTS

* `engine_preamble()` keeps its current signature and current behaviour for every
  existing caller **except** that it now REFUSES a provably-wrong engine. That is not a
  default change; it is the removal of a silent pass. `conftest.py` passes
  `strict=False` so **the oracle count cannot move** — the dedicated provenance gate
  already reports DIVERGED under pytest, and turning a 2-test failure into a
  collection-time abort would move a protocol number.
* No seed is installed, no rule changed, no Rust added.
* Oracle to be re-earned: `bash scripts/rung7_vision_bench.sh` → the documented
  **212 passed / 10 skipped without `data/`** condition (§10.2 — quoted WITH its
  condition; `data/` is gitignored and absent in every worktree).

## 6. MY PREDICTION, STATED IN ADVANCE (§3.7)

1. **S2 = 0 or 1.** The known instance was in a diagnostic, and the supervisor said it
   was already recorded; I expect it to be fixed or gone. *Proviso that would break:*
   if S2 is large, `engine_preamble` is decorative across the tree and H1's seam is
   weaker than I think.
2. **S3 > 0, and I expect between 3 and 15.** `scripts/` contains many one-off
   authoring tools that import the engine and predate §10 entirely. If S3 = 0 I have
   probably built a detector that cannot see, and I will positive-control it before
   believing it. **A quiet detector is the first thing to distrust here.**
3. **H3's freshness gate goes red immediately** on the tree as it stands, because I am
   about to add seeds to it myself. That is the mechanism working, and it is also the
   first evidence that the nuisance mode is real.
4. **Median ledger fill will still be near 0.100.** The seed-accounting rung measured
   it; nothing since has changed how blocks are declared, and my measured record should
   reproduce that number rather than improve it. **I am building a record, not a fix**
   — if fill improves, something other than my change moved it and I should find out
   what.
5. **My own footprint will be exactly 40 seeds in 2 contiguous sub-ranges** (95000–95019,
   95100–95120 exclusive of the top). *Proviso:* if `seed_audit` reports the underscore
   sub-range as absent, the AST scan has a hole and that is a more important finding
   than anything else in this rung.

## 7. WHAT A NULL MEANS

* **H1 null** — scripts do not route through `engine_preamble()`, so there is no
  Python-side unskippable seam. Report it; the honest consequence is that §10's
  in-process rule stays a discipline and only pytest is structurally protected.
* **H2 null (S2 = S3 = 0)** — either the tree is clean or my detector is blind. The
  positive control decides which, and I will say which.
* **H3 null** — regeneration is not one command, or the record is not stable across
  runs. Then the measured ledger is a reporter and rec #4 stays prose.
* **H4 null** — pregregs already record claims, so the gate is vacuous on arrival and
  I say so instead of counting it as protection.

## 8. WHAT THIS RUNG CANNOT DO (§8, stated before the numbers)

* It inherits every limit of `seed_audit`: **7 declared blind spots, 482 unresolved
  sink sites.** It cannot see CLI/env seeds, data-derived seeds, cross-module
  constants, non-Python seeds, or over-cap expressions.
* It enforces **declaration and recording**, never **correctness**: it cannot prove the
  declarer is the drawer.
* The provenance seam protects a process that CALLS the preamble. **It cannot protect a
  process that never pins its engine at all** — that hole is exactly what the AST audit
  exists to see, and the two checks are deliberately computed by different mechanisms
  from different inputs so that neither certifies itself.
* **This rung fixes no present defect.** The tree has no known live wrong number.
  It converts two post-hoc discoveries into pre-hoc refusals, and that is all.
