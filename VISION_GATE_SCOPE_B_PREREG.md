# VISION — SCOPE B GATE AUDIT + CHRONIC-FAILURE SWEEP — PRE-REGISTRATION

**Seed block: 107000–107999.** Continues `VISION_GATE_AUDIT_PREREG.md` /
`VISION_GATE_AUDIT_RESULTS.md`, whose §7 residual 7 reads: *"I did not achieve
by-construction aliveness for SCOPE B … the population is enumerated, not audited."*

## 0. Provenance (§10, recorded before the numbers)

- tree: `.claude/worktrees/agent-a41cc0af482455d6d/research/experiments/gamma-substrate`
- branch `worktree-agent-a41cc0af482455d6d`, HEAD `91e367f0c332`
- engine: **`9931e144d19b`**, built in THIS worktree by `scripts/engine_build.sh`
  (`[1 other tree build(s) shadowed]` — the canonical tree's engine was NOT written to).
  `engine_preamble()` did NOT raise.
- oracle: **212 passed / 10 skipped / 0 failed** (`scripts/rung7_vision_bench.sh`, no `data/`).

### §3 clause 8 — THE VERBATIM RECORD

`python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(107000,107999)[1])"`:

```
SEED CLAIM 107000-107999: CLEAN -- no collision DETECTED.
  Scope: 807 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

This is a claim about **AVAILABILITY, not consumption**. This rung is a source /
gate audit and draws **zero** random numbers for any claim.

### ERROR ALREADY MADE, recorded here rather than in the results (§7 applies to process)

**This pre-registration was written AFTER two measurements, not before all of them,
and §3 says before ANY number.** Specifically, before this file existed I had already
taken: (a) the seven-plant by-construction probe of `test_verdict_comparator_migrated.py`'s
adapter gate and the six-plant probe of its incumbent predicate; (b) a **5-gate pilot** of
the Scope B sweep (`ALIVE, INERT, ALIVE, BASELINE-RED, ALIVE`). Those numbers are reported
in the results, marked as pre-prereg. The predictions in §7 below are therefore made with
5 of 83 gates already seen, and I say so rather than presenting them as blind — a
prediction made after peeking is a weaker instrument and pretending otherwise is the
failure this section exists to prevent.

## 1. Hypotheses

**H1 (Scope B).** The gate-failure class the previous rung characterised — a §13/§0 gate
asserts a REACHABILITY property (*no path runs from an author-written value, or a graph
read, to a decision sink*) and fails by approximating SOURCE by a token, SINK by a
context, or REGION by a substring — **generalises to Scope B**, the reading arc's
donkey-zero / no-regex / no-decision gates, a population it never audited.

**H1 predicts** a materially non-zero INERT rate in a population nobody has probed, and
predicts it **asymmetrically**: the `no_import_re` family should be nearly all ALIVE (its
invariant is a genuine token-level property — an import IS a token, so the token
approximation is exact), while the `no python decision` / `donkey zero` families should
carry most of the inertness (their invariants are reachability properties, and a token
proxy for a reachability property is what the class says fails).

**The two-sided alternative, stated so it can win.** H1 fails if Scope B is uniformly
ALIVE (the class was a property of the vision arc, not of gates), or if inertness is
distributed with no relation to whether the invariant is token-level — i.e. if the
SOURCE/SINK/REGION taxonomy has no predictive purchase outside the population it was
built on. **Either outcome is reported as the result.**

**H2 (chronic failure).** *A check that fails chronically has verified nothing either.*
A gate that is always red is exactly as uninformative as one that can never go red, and
this tree has produced both. **H2 predicts** that the chronically-red population is
dominated NOT by real regressions but by **stale success reports** and **false
accusations** — failures whose message reports an IMPROVEMENT, or which diff a mutable
tree against a fixed sha and so accuse a later rung of an earlier one's work (§12.3).

**H2 fails** if most chronic reds are genuine unfixed violations. That would mean the
tree has a backlog, not a broken instrument, and it is a different and less interesting
finding — which is why it is worth stating in advance.

## 2. The statistic

**Per Scope B gate, established BY CONSTRUCTION, never by reading** (`scripts/gate_scope_b.py`,
over `scripts/gate_inject.py`):

1. **BASELINE** — the gate is run first. A gate already RED proves nothing about any
   plant; it is recorded `BASELINE-RED` and handed to the chronic sweep.
2. **PLANT** — each of four defects, each an INSTANTIATION OF THE INVARIANT rather than
   a spelling of a recorded failure: a name-bound decision over graph state; a name-bound
   §13 threshold; a used regex; a hardcoded word list. Every plant is a **nested `def`**,
   so the module's runtime behaviour is byte-unchanged and only its SOURCE carries the
   defect — a plant spliced as live statements can redden a gate with a `NameError`,
   which credits a gate that never looked.
3. **LAND** — `verify_lands` confirms the plant is inside the region the gate selects.
   A plant that did not land is **VOID-MISLANDED**, never INERT.
4. **REVERT** — always, in a `finally`.

Verdicts: `ALIVE` (≥1 plant reddens it) / `INERT` (landed, reddened by none) /
`VOID-MISLANDED` / `VOID-NO-SITE` / `UNRESOLVED-TARGET` / `BASELINE-RED`.

**Per chronically-red gate:** verdict class (STALE SUCCESS REPORT / REAL REGRESSION /
FALSE ACCUSATION / ENVIRONMENTAL) and **red-duration in both commits and days**, each
marked **MEASURED** (run red at an older commit) or **INFERRED** (read off the diff).

## 3. n, fixed in advance

**The population is enumerated, not sampled.** Scope B = every AST-parsing test function
in `tests/` **outside** the 21 files named by `scripts/rung7_vision_bench.sh` (which is
Scope A, and which the previous rung audited). Measured before any probe:

- **151** AST-parsing test functions in Scope B;
- **83** with an audited target resolvable by AST identity (`open(<path>)` or
  `inspect.getsource(mod)` / `inspect.getsource(mod.fn)`, resolved through the test's own
  imports);
- **68 UNRESOLVED-TARGET** — counted, never dropped. These are reported as a hole of known
  size, `seed_claim`'s posture. Many are legitimately targetless (they parse an inline
  fixture string, not a file), and I will separate those from genuine resolver misses.

**The by-construction sweep covers all 83.** The 68 do not get an aliveness verdict and
will not be reported as if they did.

Chronic sweep: **every file in `tests/`**, per-file (never `-k`; §12).

## 4. Confirmatory seeds

None consumed. Block 107000–107999 claimed, returned unburned.

## 5. Decision rule

- **INERT is the strong verdict.** A gate that stays green while a violation of its own
  stated invariant sits inside the file it audits has verified nothing.
- **ALIVE is the weak verdict** and will be reported as such: ALIVE means "this gate can
  be made to fail by a violation of the invariant it names", **never** "this gate catches
  everything". A gate can be ALIVE on these four plants and blind to the defect it was
  actually written for.
- **A null is a result** (§7). If Scope B comes back ~100% ALIVE, H1 is refuted for this
  population and I report that the class does not generalise, with the evidence.
- Gates may be made **precise**, never **quiet**. Any loosening ships with the specific
  false positive that justified it, recorded at the narrowing site.
- **A gate that reddens on landed code is a FINDING**, reported with rung and site, not
  silenced. **No other rung's exemption list is edited** (§11 rule 4) — with ONE
  exception, declared here in advance: `test_verdict_comparator_migrated.py`'s adapter
  gate, which this rung is explicitly commissioned to repair.
- **Nothing is added to `scripts/rung7_vision_bench.sh`'s file list.**
- **My own instruments (`gate_scope_b.py`, and `gate_audit.py`'s additions) are subject to
  all of the above and are audited with themselves.** That result is reported whether or
  not it is flattering — the previous rung's instrument failed its own audit three ways.

## 6. Exactly the listed checks. No sweeps.

The four plants, on the enumerated 83. The chronic sweep, per file. No re-runs to improve
a number; a gate is probed once and its verdict stands.

## 7. Predictions, stated in advance (§3 clause 7)

**Made with 5 of 83 Scope B gates already observed** (see §0's recorded error). Denominator
83 unless stated.

| class | predicted | reasoning |
|---|---|---|
| **INERT** | **12–30** (15–36%) | the class predicts token-proxy gates fail; the previous rung found every §13 gate it probed afflicted, but Scope B contains many genuinely token-level invariants that a token proxy checks EXACTLY |
| **ALIVE** | **40–62** | the residual |
| **BASELINE-RED (chronic)** | **3–12** | one appeared in the first five |
| **VOID-MISLANDED + VOID-NO-SITE** | **3–15** | function-scope targets whose body the plant cannot enter |
| **INERT rate, `no_import_re`/donkey-zero family** | **< 15%** | an import IS a token, so the token approximation is EXACT and the class predicts these should be fine |
| **INERT rate, `no python decision` / `no hardcoded list` family** | **> 35%**, and STRICTLY HIGHER than the `no_import_re` family | their invariant is reachability; a token proxy for reachability is precisely what the class says fails |
| **CROSS-FAMILY REDDENING** (a gate reddened by a plant outside its declared family) | **≥ 15 gates** | the over-inclusive direction of SINK-by-a-CONTEXT: whole-file substring audits flag anything |
| **chronically-red gates tree-wide** | **6–20** | |
| **fraction of chronic reds that are STALE SUCCESS REPORT or FALSE ACCUSATION** | **≥ 50%** | H2 |

**The asymmetry prediction is the one that makes H1 more than relabelling**, and it is
the one I most expect to be wrong: if the two families come back with the same INERT
rate, the SOURCE/SINK/REGION taxonomy has no predictive purchase here and I will say so.

**Proviso.** ALIVE is measured against MY four plants. If a family is ALIVE only because
a whole-file substring audit trips on the word `re` anywhere in the plant, that is
aliveness of a crude instrument, and I will report the plant that caught it so the
distinction is visible rather than folded into a green count.

## 8. What this rung may NOT do

- No number without its engine, its commit, and its selector (§12).
- No `-k` selector, ever.
- No gate weakened. A relaxation without its justifying false positive is quieting.
- `VISION_PROTOCOL.md` is NOT edited. Proposed amendments go in the results.
