# `ArgminUnique` — PRE-REGISTRATION

*Written and committed BEFORE any number. VISION_PROTOCOL §3.*

- **branch (as observed):** `worktree-agent-a846557d10087d8f6`
- **base SHA (as observed):** `8f41cc2ab277e6be4265ccf7d0dc632e2575f4cd`
- **seed block:** **110000–110999**, and **every generator argument will be a
  LITERAL element of that range** — never `base + K` (the refusal-capacity
  rung's §11.6: an offset expression defeats the static ledger as completely
  as a CLI value).
- **THIS RUNG ADDS RUST**, so it MUST build its own engine
  (`scripts/engine_build.sh`) and re-verify the fingerprint after the long
  measurement.

## 0 — `check_claim`, VERBATIM (§3 clause 8, GATED)

```
$ python3 -c "import sys;sys.path.insert(0,'scripts');from seed_claim import check_claim;print(check_claim(110000,110999)[1])"
SEED CLAIM 110000-110999: CLEAN -- no collision DETECTED.
  Scope: 811 files with seed sinks; 506 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**506 unresolved sinks tree-wide, priced not discarded.** A clean claim means
no collision DETECTED.

## 1 — WHAT IS BEING BUILT

`VISION_REFUSAL_CAPACITY_RESULTS.md` §7/§9.1 named the fix and did not build it:

> **`Argmin` returned a winner from FIVE IDENTICAL CANDIDATES.** `PickUnique`
> already escalates on ambiguity and is bound to **185 CONFIGURATION reads and
> ZERO VERDICT reads** — the seed layer's config hard-fails while its percepts
> soft-fail.

**Two artifacts, deliberately different in scope:**

1. **THE MECHANISM — `ArgminUnique`, one new Term variant, APPENDED.** Same
   fold as `Argmin`; returns its `default` (or `Value::None`) when the extremum
   is **not unique**. Uniqueness is EXACT EQUALITY (`cmp_value == Equal`), so
   **there is no constant and nowhere to put one** (§13 satisfied by
   construction). It is opt-in **by not existing at any site**: no seed is
   rebound in this rung, so §9 holds trivially for the Term.
2. **THE INSTRUMENT — a process-global tie audit, DEFAULT OFF**, on the
   `selector_audit` precedent (a global read inside the fold itself, so
   coverage is structural rather than remembered). Modes:
   - `off` (default) — one relaxed atomic load; behaviour byte-identical.
   - `count` — count firings / ties / empties. **Behaviour unchanged.**
   - `refuse_min` — every `Argmin` behaves as `ArgminUnique`.
   - `refuse_all` — every `Argmin` **and** `Argmax` refuses on a tie.

   The instrument exists to answer (a) — *how many landed numbers move* — on
   the WHOLE tree at once, which rebinding sites one at a time cannot do.

**Why the instrument is broader than the mechanism:** the shipped Term is
`ArgminUnique` alone (the brief's scope); the tie EXPOSURE must be measured on
`Argmax` too or the census under-reports. Movement will be reported separately
for `refuse_min` and `refuse_all` so the two are never conflated.

## 2 — POSITIVE CONTROL, IN BOTH DIRECTIONS (arm P) — RUN FIRST, BEFORE ANY Δ

*The trap: a rung last wave built a refusal instrument whose READER died first,
and a dead reader and a perfect refuser produce byte-identical output.*

**A null is not a refusal.** `Argmin` already returns `Value::None` on an empty
source. If my instrument cannot separate *refused because ambiguous* from
*produced nothing because empty* — and from *my reader is broken* — every number
below is fake in exactly the documented way.

**P-A (refusal is REAL):** 5 identical candidates ⇒ `ArgminUnique` returns
`None`, the **tie counter increments**, the **empty counter does NOT**.
**P-B (refusal is SPECIFIC):** 5 candidates with a unique minimum ⇒
`ArgminUnique` returns **the same node `Argmin` returns**, tie counter
**unchanged**. A mechanism that refuses everything fails here.
**P-C (empty ≠ tie):** an EMPTY source ⇒ `None`, **empty counter** increments,
**tie counter does not** — the two indistinguishable outputs are distinguished
by the instrument, in both directions.
**P-D (the reader is alive):** the same reader that reports the nulls above must
report a NON-null on P-B in the same process. A reader returning `None`
universally fails P-B and P-D together.

**ABORT RULE: if P-A…P-D do not all hold, NO Δ IS REPORTED.** This is the
refusal-capacity rung's abort discipline, adopted verbatim.

**Randomised replicate:** 200 draws, seeds **110000–110199** (literal, in
block), each constructing a candidate set that is a tie or a strict extremum by
construction; the instrument must classify 200/200 correctly in both directions.

## 3 — THE MEASUREMENTS

### Arm T — THE TIE CENSUS (`count` mode; behaviour must be byte-identical)

`bash scripts/rung7_vision_bench.sh` under `count`, and per-file counters.
**Statistic: `tie_firings / firings`**, globally and per bench file.
**Gate on the instrument itself: the bench result under `count` must equal the
`off` baseline exactly** (222/0 with `data/`). If it does not, the instrument is
not an instrument and the rung stops.

### Arm M — HOW MANY LANDED NUMBERS MOVE (the finding that outranks the build)

The same named bench under `refuse_min` and again under `refuse_all`, diffed
test-by-test against the `off` baseline, plus a re-run of the vision results
JSONs regenerable in-tree.

**Statistic: the COUNT of bench tests whose outcome changes, and for each, the
magnitude and direction of the number that moved.**

**§5, in advance: if a published number moves, THAT IS THE RESULT.** It will be
reported with magnitude and direction and **no attempt will be made to rescue
the original claim** — not by tuning, not by narrowing the mode, not by
declaring the site out of scope.

### Arm C — PER-SITE ADMISSIBILITY (is the escalation ADMISSIBLE, or merely possible?)

*C1 of the refusal rung: a structured refusal is ERASED at the field boundary —
`False` from one Term and bare `None` from another, indistinguishable to a rule.
**A refusal the caller cannot represent is not a refusal.***

Every `Argmin`/`Argmax` occurrence in `seeds/*.json` is enumerated with its
ENCLOSING context, and each site is classified:

| class | meaning |
|---|---|
| **ADMISSIBLE** | the caller can represent the null AS a refusal — it reaches a guard that distinguishes `None` from a value, or an effect that does not fire |
| **ERASED** | the null is swallowed into a FALSE (e.g. `Eq(x, Argmin{…})` with a null operand) — the rule cannot tell *ambiguous* from *lost the comparison* |
| **INADMISSIBLE** | the null becomes an attribute value / a written datum — the refusal is stored as if it were a percept |

**This is a classification by construction, not a rate**, and it is reported per
site with the enclosing Term named.

## 4 — PREDICTIONS, STATED IN ADVANCE (§3 clause 7)

- **P1 — the tie rate is NOT zero.** I predict **> 5%** of audited `Argmin`/
  `Argmax` firings across the vision bench have a non-unique extremum, because
  many vision scores are small integers or counts. **Two-sided: a measured 0%
  would be a real and reportable finding** — it would mean the confabulation
  `Argmin` enables is latent rather than active, and would make `ArgminUnique`
  a guard rather than a fix.
- **P2 — landed numbers: I predict BETWEEN 1 AND 10 bench tests move under
  `refuse_all`, and FEWER (0–5) under `refuse_min`.** Two-sided; a 0 is a clean
  §9 result and a >10 is the headline.
- **P3 — direction.** Every movement will be toward ABSENCE (a rule not firing,
  a value becoming null), never toward a DIFFERENT non-null value. A different
  non-null value would mean the refusal changed a downstream selection rather
  than removing one, and would falsify my model of the mechanism.
- **P4 — admissibility: I predict the MAJORITY of verdict-side sites are
  ERASED**, i.e. the null is consumed by an `Eq`/arithmetic context that turns
  it into a `False` or a skipped match, so the escalation is *possible* but not
  *admissible*. If most sites are ADMISSIBLE, `ArgminUnique` can be armed
  site-by-site today; if most are ERASED, it cannot, and the finding is that
  **the fix is cheap and its DELIVERY is not.**
- **P5 — §13.** No tolerance will be needed. **If any site requires an epsilon
  on "identical" to be useful, that is a finding, reported, with NO number
  picked.**

## 5 — DECISION RULES

- **NULL RESULT (P1 = 0%):** report the earned null — `Argmin`'s inability to
  refuse is a latent hazard, not an active one, on this bench. `ArgminUnique`
  still ships (default-unused) as the guard; no claim of a fix is made.
- **Any landed number moves:** the movement is the headline and is reported
  ahead of the build.
- **P-A…P-D fail:** no Δ is reported at all.
- **No seed manifest is shipped, no default is moved, no other rung's file is
  edited.** `EnclosedCount`'s zero/unmeasurable conflation and the motion
  sensor's SAD argmin are NAMED and LEFT (separate rungs).

## 6 — CPU DISCIPLINE

At most **2 concurrent workers**. `os.getloadavg()` recorded with every
measurement written to an artifact. **No wall-clock cutoff is a verdict.**
