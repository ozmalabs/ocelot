# VISION — §13 GATE `trace` ACCUMULATOR BLINDNESS — RESULTS

Pre-registration: `VISION_GATE_ACCUMULATOR_PREREG.md`, committed at `4b8bad54c0`
**before** the fix. Seed block **122000–122999** — **NO seeds drawn** (a
gate-instrument fix).

## 0. Provenance (§10)

| | |
|---|---|
| tree | `.claude/worktrees/agent-af735d75eb9856e69/research/experiments/gamma-substrate` |
| branch | `worktree-agent-af735d75eb9856e69` |
| base HEAD | `c5bf33582d3b` |
| prereg commit | `4b8bad54c0` |
| engine | **`7041d2e6a7dd`**, `own` build — re-verified **identical** after the change |
| oracle (before) | **222 passed / 0 failed** (`scripts/rung7_vision_bench.sh`, `data/` symlinked) |
| oracle (after) | **222 passed / 0 failed** — UNMOVED (§9 trivial) |
| §9 | **`git diff -- seeds/ runners/` EMPTY** — pure-Python scripts/ change |
| seed claim | `check_claim(122000,122999)` → **CLEAN**; 513 UNRESOLVED sink sites tree-wide (advisory; this rung draws none) |
| loadavg | before-oracle `2.56`; after-oracle-launch `2.67` (concurrent rungs) — no wall-clock verdict taken |

## 1. THE BUG (measured, before)

`gate_audit.trace` resolved a REBOUND name to its FIRST binding, so an
accumulator (`x = 0` then `x += …`) graded `AUTHORED (-> literal 0)` off its
initialiser. Confirmed on constructed plants (engine `7041d2e6a7dd`):

| plant | BEFORE | after |
|---|---|---|
| S1 `x += 5; if x > 0.42` | authored=0 (**BLIND** — dead-code suppression) | **T1 flags `x > 0.42` :: literal 0.42** |
| S2 `x = x + 5; return x > 0.42` | authored=0 (**BLIND**) | **T1 flags `x > 0.42` :: literal 0.42** |
| S3 `x = max(x, 0.42)` | authored=1 but `x -> literal 0` (**masks 0.42, false init-0**) | **T2 flags `max(x, 0.42)` :: literal 0.42** (real) |
| S4 name-bound `C`; `x += C; if x > 0.42` | authored=0 (**BLIND**) | **T1 flags `x > 0.42` :: literal 0.42** |
| S5 `enc/ncell > 0.42` (two accumulators) | authored=0 (**BLIND**) | **T1 flags `enc / ncell > 0.42` :: literal 0.42** |
| FP `max(largest, run)` (no literal) | authored=1 `largest -> literal 0` (**FALSE POSITIVE**) | **authored=0** — cleared |

The gate bit 3/5 accumulator spellings and was blind on 2/5, exactly as the
enclosure-grain rung measured (`VISION_ENCLOSURE_GRAIN_RESULTS.md` §5.2). S3 was
worse than "bit": it flagged the WRONG literal (`literal 0`, the init) and
masked the real `0.42`.

## 2. THE FIX — model REBINDING, not a spelling

`scripts/gate_audit.py`. A SOURCE-approximation error (source approximated by
FIRST binding), fixed by proper transitive dataflow — a new provenance verdict
**`ACCUMULATED`**, NOT a checklist entry.

- **New helpers `_references(node, name)` / `_delta_operands(node, name)`** —
  an accumulation is a binding that READS the name it is bound to (`x = x + C`,
  `x += C` recorded by `_Binder` as `x + C`, `x = max(x, C)`).
- **`trace` (ast.Name):** if ANY binding of a name is an accumulation, the name
  is `ACCUMULATED` — a DERIVED quantity (init-plus-steps), never a fixed
  authored constant. The initialiser literal no longer stands in for it; the
  accumulated step stays reachable in `detail`.
- **`trace` (ast.BinOp):** ACCUMULATED propagates (arithmetic on an accumulated
  value is accumulated) — this is what closes the `enc/ncell > K`
  two-accumulator ratio, whose left side must not read AUTHORED.
- **`audit_source` dead-code branch:** now guarded `and not accumulated`, so
  *"both sides authored ⇒ constant-folded dead code"* NEVER fires when either
  operand is an accumulation. (Naturally true since ACCUMULATED ∉ authored, made
  explicit at the branch that used to swallow K.)

ACCUMULATED behaves like MEASURED for the sink decision: it does not suppress
and is not itself flagged; the OTHER side's real threshold surfaces.

## 3. VERDICT vs PREDICTIONS

- **P1 CONFIRMED** — all 5 spellings now flag the REAL threshold `0.42` (S1/S2/S4/S5
  T1; S3 T2 bound), none reports `literal 0`. Table §1.
- **P2 CONFIRMED** — the false positive `max(largest, run)` clears to authored=0
  (`largest` ACCUMULATED, `run` UNRESOLVED — counted, 1).
- **P3 CONFIRMED — regression ZERO.** `test_gate_audit_migrated.py` +
  `test_vision_floor_migrated.py` + `test_verdict_comparator_migrated.py`:
  **103 passed before, 103 passed after** (the gate_audit suite grows to **65
  passed** with the 7 new by-construction plant tests below; the trio-count 103
  refers to the pre-existing tests). `audit_source(domains/vision_world.py)` =
  **0 authored / 0 unresolved before and after** — no real accumulator-vs-literal
  there to un-suppress, so no landed gate reddened.
- **P4 CONFIRMED — self-audit TIER unchanged.** `gate_audit.py` self-audit stays
  **T1 = 0** (one T3 `len(pairs) > 1` cardinality, 2 unresolved);
  `gate_inject.py` **T1 = 0** (0 authored, 1 unresolved). No previously-suppressed
  comparison in `gate_audit.py` surfaced as a new T1.
- **P5 CONFIRMED — oracle unmoved.** 222/0 → 222/0; `git diff -- seeds/ runners/`
  empty; engine `7041d2e6a7dd` re-verified identical after.

## 4. POSITIVE CONTROL BY CONSTRUCTION — permanent, in the migrated suite

Added to `tests/test_gate_audit_migrated.py` (7 tests):

- `ACCUMULATOR_SPELLINGS` (5, parametrized) — each hides `0.42` behind an
  accumulator (bare aug, plain `x = x + C`, running-max bound, name-bound step,
  two-accumulator ratio); asserts the threshold is flagged, traces to the real
  `0.42`, and does NOT report `literal 0`.
- `test_the_running_max_of_two_measurements_is_NOT_a_threshold` — the FP
  direction: `max(largest, run)` with no literal must not flag.
- `test_an_accumulator_grades_ACCUMULATED_not_AUTHORED` — the mechanism pinned
  directly (`trace` of an accumulator returns `ACCUMULATED`).

These audit the whole probe source (no qualname), so there is no subtree
mis-selection: the finding lands at the exact expected line on the exact
expression, verified by the `0.42`-in-detail assertion. A future edit that
reintroduces the first-binding bug reddens these by construction.

## 5. SELF-AUDIT OF `gate_audit.py` (with the fixed gate)

`gate_audit.py`: **1 authored (T3 `len(pairs) > 1`, cardinality), T1 = 0**,
2 unresolved. `gate_inject.py`: 0 authored, T1 = 0, 1 unresolved. The fix's new
code adds only `== name` sentinel comparisons (not ordering-vs-literal sinks),
so it introduces no finding.

**On the `src[-80:]` note in the brief:** the current `gate_audit.py` contains
**no `src[-80:]` (or any negative/integer slice-bound) literal.** The only
bracket-index in the module is `prov.detail.rsplit("->", 1)[-1]` — a
LAST-ELEMENT index, structural, not a threshold — which the gate correctly does
not treat as a sink (subscript slices are excluded by parent-context typing, by
design). My fix neither adds nor removes any such slice; the self-audit is
unchanged in this respect.

## 6. REGRESSION — did any landed gate move?

**No.** The only runtime consumers of `gate_audit` in the test tree are the
three files above (all 103 pre-existing tests green). `scripts/scale_split_measure.py`
and `scripts/enclosure_grain_injection.py` also import it but are measurement
SCRIPTS, referenced by **no** pytest test and in **no** oracle file list.

**One historical script would now flip, and it is the bug being fixed, reported
not silenced:** `scripts/enclosure_grain_injection.py` asserts the OLD blindness
(its `P4`/`P5` accumulator plants `RED=False`). Re-run against the fixed gate
those two plants would now go `RED=True`. That script is a one-off record of the
enclosure-grain rung's measurement (already committed with its numbers); it is
not a gate and is not in any suite. It is named here so the flip is on record.

## 7. WHAT I GOT WRONG / honest residuals

- The brief's `src[-80:]` magic number is **not present** in the current
  `gate_audit.py` — I looked for it and report its absence rather than inventing
  a fix for it. If it existed in an earlier version it has since been removed;
  the standing structural blind spot it names (a slice bound is not a sink) is
  real and correct-by-design, and my fix does not touch it.
- ACCUMULATED is treated like MEASURED at the sink: an accumulator compared to a
  NON-literal (e.g. `if x > count` where `x` accumulates by a literal step)
  produces no finding — the step literal lives at the AugAssign, not at a sink,
  so `find_sinks` never sees it. This is consistent with the gate's "value AT a
  sink" contract and is a strengthening over the old false-positive-on-init, but
  it means a magic STEP that never reaches a sink is out of scope (unchanged from
  before, and not claimed fixed).
- `check_claim` is advisory-only for this block (no seeds drawn); the 513
  tree-wide unresolved count is priced, not in-block.
