# VISION — §13 GATE `trace` ACCUMULATOR BLINDNESS — PRE-REGISTRATION

Pre-registered BEFORE the fix is written and BEFORE any result number is read.
Seed block **122000–122999** (a gate-instrument fix — NO seeds expected drawn).

## 0. Provenance (§10)

| | |
|---|---|
| tree | `.claude/worktrees/agent-af735d75eb9856e69/research/experiments/gamma-substrate` |
| branch | `worktree-agent-af735d75eb9856e69` |
| base HEAD | `c5bf33582d3b` |
| engine | **`7041d2e6a7dd`**, `own` build (`bash scripts/engine_build.sh`) — re-verified after |
| oracle | `scripts/rung7_vision_bench.sh` WITH `data/` symlinked — recorded before AND after |

## 1. THE BUG (from `VISION_ENCLOSURE_GRAIN_RESULTS.md` §5.2, §11 rule-4 hand-audit)

`gate_audit.trace` resolves a **rebound** name to its **FIRST** binding. An
ACCUMULATOR — `x = 0` then `x += <literal|measured>` / `x = x + C` /
`x = max(x, C)` — therefore grades `AUTHORED (-> literal 0)` off its
initialiser. Two consequences, one cause:

- **FALSE NEGATIVE.** `audit_source`'s *"both sides authored ⇒ constant-folded
  dead code"* branch then SUPPRESSES a real magic-number threshold on any
  accumulated quantity (`x += C; if x > K`; `enc/ncell > K`) — bare AND
  name-bound. The threshold `K` ships undetected.
- **FALSE POSITIVE.** `max(largest_gnd, running)` reports `largest_gnd ->
  literal 0` — the accumulator's zero initialiser read as a magic bound.

Confirmed CURRENT behaviour on constructed plants (engine `7041d2e6a7dd`):

| plant | current | why |
|---|---|---|
| S1 `x += 5; if x > 0.42` | authored=0 (BLIND) | dead-code suppression |
| S2 `x = x + 5; return x > 0.42` | authored=0 (BLIND) | dead-code suppression |
| S3 `x = max(x, 0.42)` | authored=1 but `x -> literal 0` (WRONG literal / masks 0.42) | init-0 FP, `authored_sides[0]` |
| S4 name-bound `C`; `x += C; if x > 0.42` | authored=0 (BLIND) | dead-code suppression |
| S5 `enc/ncell > 0.42` (two accumulators) | authored=0 (BLIND) | dead-code suppression |
| FP `max(largest, run)` (no literal) | authored=1 `largest -> literal 0` (FALSE POSITIVE) | init-0 read as bound |

## 2. THE FIX — model REBINDING, do not weaken the gate

A SOURCE-approximation error (source approximated by FIRST binding), fixed by
proper transitive dataflow — NOT a sixth spelling.

1. **`trace` (ast.Name):** if ANY binding of a name is an ACCUMULATION (an
   expression that references the name ITSELF — `x = x + C`, `x += C` bound to
   `x + C`, `x = max(x, C)`), the name is a new provenance verdict
   **`ACCUMULATED`** — a derived quantity, NOT a fixed authored constant. The
   initialiser literal (`x = 0`) no longer stands in for it. The accumulated
   delta stays reachable (traced), reported in the detail.
2. **`trace` (ast.BinOp/UnaryOp):** ACCUMULATED propagates (an arithmetic on an
   accumulated value is accumulated) — closes the `enc/ncell` two-accumulator
   ratio.
3. **`audit_source` dead-code branch:** must NOT fire when EITHER side's
   provenance is ACCUMULATED (an accumulator is not a constant fold). Naturally
   satisfied because ACCUMULATED ∉ authored_sides; made explicit as a guard.

ACCUMULATED is treated like MEASURED for the sink decision: it does not suppress
and is not itself flagged; the OTHER side's real threshold surfaces.

## 3. PREDICTIONS (pre-registered)

- **P1 — the 5 currently-blind/mis-flagged spellings now catch the REAL
  threshold.** After the fix: S1 flags `0.42` (T1 compare); S2 flags `0.42`
  (T1 compare); S3 flags the REAL `0.42` (T2 bound, NOT `literal 0`); S4 flags
  `0.42` (T1 compare); S5 flags `0.42` (T1 compare). Every one traces to the
  literal `0.42`, none reports `literal 0`.
- **P2 — the false positive clears.** FP `max(largest, run)` → authored=0
  (largest ACCUMULATED, run untraced/UNRESOLVED). No `literal 0` finding.
- **P3 — regression is ZERO.** `test_gate_audit_migrated.py` +
  `test_vision_floor_migrated.py` + `test_verdict_comparator_migrated.py`
  currently **103 passed**; predict **103 passed** after. `audit_source` on the
  real `domains/vision_world.py` is 0 authored / 0 unresolved before; predict
  unchanged (no accumulator-vs-literal there to un-suppress).
- **P4 — self-audit unchanged in TIER.** `gate_audit.py` / `gate_inject.py`
  self-audit stays **T1 = 0** (the migrated suite's standing assertion). The
  fix adds only `== name` sentinel checks, no ordering-vs-literal sink. Note
  whether any previously-suppressed comparison in `gate_audit.py` itself
  surfaces (report, do not silence).
- **P5 — oracle unmoved.** Pure-Python gate change, `git diff -- seeds/
  runners/` EMPTY ⇒ §9 trivial: oracle identical before==after; engine
  fingerprint `7041d2e6a7dd` re-verified identical after.

**Falsification:** if any Sx still reports authored=0 or `literal 0`, or the FP
still fires, or regression > 0 on real code without being reported as a finding,
or the oracle moves, the fix is wrong.

## 4. What could go wrong (honest, in advance)

- Un-suppressing dead-code could surface a genuinely-suppressed accumulator
  comparison somewhere in the tree that a landed gate ran over. Only
  `test_vision_floor` runs `audit_source` on real code (vision_world.py, 0/0),
  so the blast radius is bounded — but if it reddens, that is a FINDING (a real
  hidden threshold), reported with rung + site, never silenced.
- `scripts/enclosure_grain_injection.py` (a one-off measurement script, not a
  pytest gate) asserts the OLD blindness (P4/P5 RED=False). After the fix it
  would flip — that is the bug being fixed, reported not silenced.

## 5. §3 clause 8 — `check_claim` VERBATIM for 122000–122999

```
SEED CLAIM 122000-122999: CLEAN -- no collision DETECTED.
  Scope: 825 files with seed sinks; 513 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

unknown_sinks: the tree-wide unresolved count is 513 (advisory, not in-block);
this rung draws NO seeds of its own.
