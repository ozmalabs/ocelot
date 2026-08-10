# SEED CLAIM ENFORCEMENT — PRE-REGISTRATION

Written and committed **BEFORE any measurement** (VISION_PROTOCOL.md §3).

**Branch actually seen:** `worktree-agent-affadc338e794482c` — the ninth
consecutive rung to run under an auto-generated name, not
`gamma-substrate/seed-claim-enforcement`.

**Base HEAD:** `e8bf398747c4b14f54a8519d234b0667f246438a`.

**Block:** 90000–90999. **Predicted consumption: ZERO.** This rung is static
analysis plus tests; it seeds no RNG. If any seed is drawn it will be measured
by this rung's own instrument and reported.

**Provenance gate, run as its own step BEFORE this document was written:**
`pytest -q tests/ -k provenance` → **698 passed, 1 failed**. The one failure,
`tests/test_dynamic_thresholds_migrated.py::test_global_contradiction_reopen_provenance_round_trips`,
is the SAME failure the seed-accounting rung recorded as pre-existing at base
`c7a57ec8`; my working tree contained zero edits when it was run.

---

## THE DEFECT BEING ADDRESSED

`VISION_SEED_ACCOUNTING_RESULTS.md` (merged `70734520`): the ledger is honest
but **not load-bearing**. Its verdict in one line — **it is a write-side
discipline with no read-side enforcement.** Concretely:

- 373 seeds across 34 runs drawn OUTSIDE any declared block;
- **two full 100-seed blocks consumed with NO declaration at all**
  (38000–38099 `det1_measure.py`; 40000–40099 `continuous_pose_measure.py`);
- `scripts/seed_ledger_audit.py` exists and **nothing runs it on a schedule**.

And the correction that rung made to the supervisor, which governs this design:
the gate `declared ⊇ measured` **cannot catch an undeclared block, because it
needs a declaration to check against.** It catches the minority case and misses
the dominant one.

## THE MECHANISM, FIXED IN ADVANCE

A **claim check** that consults **MEASURED draws across the whole tree**, and
consults the ledger only as an ADVISORY second signal. The authoritative
question is not "is this block declared?" but **"is this block measurably
drawn by anyone?"** — the check `det1_measure.py`'s author performed by hand
(the source comment `# noise — seeds 38000-38099 (never used)`) and never
recorded.

One line, at pre-registration time, before any seed is spent:

```python
from seed_claim import check_claim
ok, report = check_claim(90000, 90999)
assert ok, report
```

CLI: `python3 scripts/seed_claim.py 90000 90999` (exit 1 if occupied).

**Contract fixed here and not redefined after seeing results:**

- **OCCUPIED (fail)** — one or more seed integers in `[lo, hi]` are measurably
  drawn by some file in the tree. Report names every file and seed.
- **DECLARED-ELSEWHERE (fail)** — `[lo, hi]` overlaps a §11 ledger declaration
  belonging to another rung, even at zero measured consumption. A declaration
  with no measured draws is still someone's reservation; blind spot 5 means
  "measures zero" does not mean "drew nothing".
- **CLEAN (pass)** — neither. **And "clean" means NO COLLISION DETECTED, never
  NO COLLISION EXISTS** (see caveats).

## THE TWO CAVEATS, CARRIED INTO THE FAILURE MESSAGE

Both are inherited from `seed_audit.py` and are load-bearing. They will appear
in the text the tool prints, not only in this document, because a future reader
sees the tool's output and not this file:

1. **The unit is the SEED INTEGER, not consecutive draws from one generator.**
   `default_rng(S)` burns an unbounded stream downstream of `S`; a rung that
   reserves 1000 integers and seeds once at the base measures as ONE seed. This
   is a definitional choice, declared, not an oversight.
2. **The tool UNDER-REPORTS BY DESIGN.** Unresolvable sink sites are COUNTED,
   never discarded (7 declared blind spots: CLI/env, data-derived seeds,
   cross-module constants, unanalysed library files, generator streams,
   non-Python seeds, over-cap expressions). Therefore **a clean result means
   "no collision detected", NEVER "no collision exists."** The count of
   unresolved sinks in scope is printed alongside every verdict so the reader
   can price the silence.

## WHERE IT RUNS — decided in advance

1. **A migrated-suite gate**, `tests/test_seed_claim_migrated.py`, which runs
   under the project's documented regression bench (`pytest -k migrated`).
2. **NOT added to `scripts/rung7_vision_bench.sh`.** That script is rung 7's
   explicit file list and its count IS the protocol's oracle (222 with `data/`,
   212/10 without). Adding a file would move the oracle number, which is
   protocol-load-bearing state I do not own (§11 rule 4). Recommended to the
   supervisor instead.

## PREDICTIONS, STATED IN ADVANCE (§3.7)

| | prediction |
|---|---|
| **P1** | The checker reports **OCCUPIED** on 38000–38099 and 40000–40099, naming `det1_measure.py` / `continuous_pose_measure.py`. A ledger-only checker reports these FREE. This is the positive control and it is real tree data, not a plant. |
| **P2** | **My own assigned block 90000–90999 is NOT clean.** The audit reported `90000–90002` drawn by 3 scripts, above the ledger's top. So the first real use of this tool rejects the supervisor's own allocation to me. If so I will claim a verified-clean sub-range instead. |
| **P3** | A synthetic planted draw into a verified-clean range flips that range OCCUPIED, and removing the file restores CLEAN. |
| **P4** | Whole-tree scan cost is single-digit-to-low-tens of seconds, i.e. cheap enough to gate. Measured before claiming it. |
| **P5** | The count of consumed-but-undeclared runs at base is > 0 and matches the prior rung's 34 runs / 373 seeds within the tolerance of a differing tree state. |

## DECISION RULE

- **Enforcement is cheap and wired** if the checker fires on P1 (real historical
  data), passes P3 (plant/remove), and the scan cost of P4 is bench-tolerable.
- **Enforcement costs more than it saves** if the scan is too slow to gate or
  the false-accusation rate on legitimate rungs is high. The ledger has ZERO
  real collisions today, so the value is PREVENTING a future one, not fixing a
  present one — a high nuisance rate would not be worth that.
- **The measurement is too incomplete to enforce against** if the unresolved
  sink count in a typical claimed range is large enough that CLEAN carries no
  information. Then I name what would have to improve first and wire nothing.

A null here is a real outcome and will be reported as one (§7).

## WHAT THIS RUNG DOES NOT DO (§8)

No Rust, no Term, no seed manifest, no constant, no engine build. It does not
edit `VISION_PROTOCOL.md` (§11 rule 4) — the five §11 amendments the prior rung
recommended, plus any this rung adds, are REPORTED for the supervisor to apply.
It cannot see any of the seven declared blind spots, and does not claim to.
