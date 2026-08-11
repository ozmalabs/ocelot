# BATCH-APPLY THE DRIVE RULES — PRE-REGISTRATION

*Written and committed BEFORE any change to Rust, seed or adapter, and BEFORE
any measurement (PROTOCOL §3). Base commit pinned in §9 below.*

**Seed block:** 63000–63999, verified free before launch. Expected consumption:
**NONE** — every statistic here is a deterministic operation COUNT, the same
posture `VISION_SCALE_SPLIT_RESULTS.md` took (it claimed 61000–61999 and
consumed none). If any arm turns out to need a seed, it is drawn from this
block and recorded.

**Predecessor:** `VISION_SCALE_SPLIT_RESULTS.md` §9 recommendation 1 —
*"Set `batch: true` on the five `vision_change` rules and re-measure."*
This rung executes that recommendation, and §2 below reports a defect in it
found by reading the code before touching anything.

---

## 1. THE QUESTION

The scale rung decomposed the retina drive's counted operations and found the
wall in ONE term: **99.81% of all candidate enumeration is
`WaveWorld._drive_phase()`'s `while nat.apply_rule_once(idx): pass` loop
re-deriving the binding set on every iteration** (217,213 calls at 4096 cells
against an irreducible floor of 100). It selected batch-apply over a proposal
net and over an async collapse loop on the explicit ground that batching is
**exact, not approximate**: it should remove work rather than approximate it,
and therefore cost no accuracy and no legibility.

**Two questions, in this order:**

- **Q1 (CORRECTNESS, gates everything).** Batching changes the ORDER in which
  bindings are applied within one pass. Does any verdict move?
- **Q2 (EFFECT).** Does enabling `batch` reproduce the ablation's measured
  exponent shift (1.955 → 0.982) on the REAL path, or is the ablation
  (which removed the drive phase entirely) a different intervention?

---

## 2. A DEFECT IN THE PREDECESSOR'S RECOMMENDATION, FOUND BEFORE ANY CHANGE

**`apply_rule_once` DOES NOT HONOUR THE `batch` FLAG.** Read in code
(PROTOCOL §12.3), not inferred:

- `Substrate::apply_rule_once` (`runners/dsl/src/substrate.rs:1389–1415`)
  calls `rewrite::match_rule` — which returns **ONE** binding — then
  `rewrite::apply_rule`. There is **no `rule.batch` test anywhere in it.**
- The batch dispatch exists in exactly one place:
  `Substrate::run_rules_opts` (`runners/dsl/src/substrate.rs:~1955`,
  `if self.rules[rule_idx].batch { ... batch_apply_rule ... }`).
- `WaveWorld._drive_phase` (`domains/wave_world.py:306`) drives via
  `nat.apply_rule_once(idx)`, and deliberately so — its docstring records that
  `run_rules()` here "would advance the WAVE rules an extra time per step and
  destroy every committed result".

**Therefore setting `"batch": true` in `seeds/vision_change.json` and nothing
else would change NOTHING on this path, and would produce a null that looks
like a refutation of batching while actually measuring a flag nobody read.**
That is this arc's recurring failure mode (eleven inert instruments) arriving
one layer up, in a BUILD rather than an instrument. It is recorded here,
before the change, so the null it would have produced cannot be reported as a
result about batching.

The intervention is therefore three parts, not one (§4).

---

## 3. MONOTONICITY CLASSIFICATION — DONE FROM THE RULE BODIES, BEFORE ENABLING ANYTHING

`batch_apply_rule` (`runners/dsl/src/rewrite.rs:1972`) **snapshots every
binding before any effect fires**, then applies each exactly once with
`record_undo = false`. So batching is safe for a rule iff the fixpoint it
reaches is **order-independent (confluent)** over that snapshot.

### 3.1 The structural facts the classification rests on

Verified in code, not assumed:

- **One `Retina` hub per world** (`wave_world.py:126`), **one `has_cell` edge
  per cell** (`wave_world.py:158`). `lateral_world` adds only DISTINCT edge
  types (`has_hcell`, `pools_to`, `has_lbipolar`, `neighbour2`). The scale
  rung's §6.2 known-count gate independently confirmed exactly h·w `has_cell`
  edges. **⇒ the bindings of `[r, has_cell, c]` are in BIJECTION with cells;
  `c` is unique per binding.**
- **All ten effects across all five rules are `set_attr`.** Zero `del_edge`,
  `del_node`, `add_node`, `add_edge`. **⇒ no rule retracts, and the match
  STRUCTURE (nodes + `has_cell` edges) is invariant across the entire drive
  phase.** The binding set cannot grow or shrink; only the `where` filter over
  a fixed set can change.

### 3.2 The five rules

| rule | writes | non-local reads | classification |
|---|---|---|---|
| `ch_drive_median` | `c.driven`, `c.dstep_med` | `r.frame_median`, `r.step`, `ChangeParams.change` | **non-monotone (mutating), CONFLUENT** |
| `ch_transient_on` | `c.driven`, `c.dstep_on` | `r.step`, `ChangeParams.{change,nmax}` | **non-monotone (mutating), CONFLUENT** |
| `ch_transient_off` | `c.driven`, `c.dstep_off` | `r.step`, `ChangeParams.{change,nmax}` | **non-monotone (mutating), CONFLUENT** |
| `ch_sustained` | `c.driven`, `c.dstep_sus` | `r.step`, `ChangeParams.{change,sustain,nmax}`, **`q.lum_raw` for every `q ∈ neighbours(c)`** | **non-monotone (mutating), CONFLUENT — but by the §3.3(iv) argument, not by locality** |
| `ch_adapt_ref` | `c.lum_ref`, `c.ref_n`, `c.ref_step` | `r.step` | **non-monotone (mutating, READ-MODIFY-WRITE accumulator), CONFLUENT** |

**NONE of the five is monotone in the add-only sense** — every one mutates
attributes. Monotonicity is therefore NOT the property that licenses batching
here, and saying "they're add-only" would be false. The property that does is
**confluence**, and it holds by the conjunction of four facts:

### 3.3 Why each is safe — the four-part argument, stated so it can fail

**(i) NO RETRACTION ⇒ the binding set is fixed.** All effects are `set_attr`
(§3.1). Nothing a rule does can create or destroy a `[r, has_cell, c]` match.

**(ii) SELF-NARROWING ONLY ⇒ no binding is ENABLED by another's effect.**
Each rule sets its own phase key (`dstep_med` / `dstep_on` / `dstep_off` /
`dstep_sus` / `ref_step`) to `r.step`, which falsifies its OWN
`Lt(c.dstep_*, r.step)` guard. That is the documented termination device
("fires ONCE per cell per step and TERMINATES"). An applied binding can only
LEAVE the admissible set. No effect makes any guard TRUE.

**(iii) WRITE-SETS ARE PAIRWISE BINDING-DISJOINT.** Every write targets `c`,
and `c` is unique per binding (§3.1). No rule writes to `r`, and no rule
writes to `ChangeParams`. `driven` is written by four rules to the same
constant `1.0` — idempotent, and read by NO `where` in this seed.

**(iv) THE ONE CROSS-BINDING READ IS OF AN ATTRIBUTE NO RULE WRITES.**
`ch_sustained` sums `lum_raw` over `c`'s `neighbour` edges — a read of OTHER
bindings' cells. `lum_raw` is written by the ADAPTER
(`wave_world.drive()`), before `_drive_phase` is entered, and by **no rule in
this seed**. It is therefore constant for the whole phase, and the neighbour
sum is order-independent.

**`ch_adapt_ref` gets its own paragraph because it is the one that looks
dangerous.** It is a read-modify-write accumulator:
`lum_ref += (lum_raw − lum_ref)/max(ref_n,1)` and `ref_n += 1`. Under
`batch_apply_rule`, bindings are snapshotted but effects are applied
SEQUENTIALLY against the live graph — so a genuine shared accumulator WOULD
be order-sensitive. It is safe here only because each binding reads and writes
its OWN `c` and no two bindings share a `c` (§3.1), and because the
`ref_step` phase guard admits each cell exactly once per step under BOTH
regimes. Same count, same operands, same value. **If §3.1's bijection were
ever false — a second `Retina`, or a duplicated `has_cell` edge — this rule is
the one that would break first, and it would break silently in the last
decimal place.**

### 3.4 DECISION: batch ALL FIVE

All five satisfy (i)–(iv), so all five are batched. **What I will do with a
non-monotone rule is: batch it anyway iff I can show confluence, and say
which of (i)–(iv) carries it.** For (iv) that is `ch_sustained`; for the
accumulator argument that is `ch_adapt_ref`. Both are named above rather than
waved through.

**No rule is withheld.** If a rule had failed any of (i)–(iv) it would have
been left unbatched and the coverage reported as partial; none did.

---

## 4. THE INTERVENTION — three parts, all declared now

**(A) RUST, PURELY ADDITIVE.** A new PyO3 method
`Substrate::apply_rule_batch(rule_idx) -> bool` that dispatches to
`rewrite::batch_apply_rule` **iff `rules[idx].batch`**, and otherwise falls
back to `apply_rule_once`'s exact behaviour.

*Why not simply add the `batch` test inside `apply_rule_once`:* two seed rules
already set `"batch": true` (`seeds/vision_settle.json` — `st_settle`,
`st_commit`). Putting the dispatch in `apply_rule_once` would silently change
their behaviour for any Python caller that drives them that way. That is a
scope widening disguised as a one-line fix, and §5 forbids it. **With a
separate method, every path that does not call it is byte-identical BY
CONSTRUCTION (§9), not by test.**

The new method **must replicate `run_rules_opts`'s post-batch
`eval_cache` clear** (`neighbours` / `filter` / `holds`). `batch_apply_rule`
matches with the cache live and applies with `None`; the caller is responsible
for invalidating it. `ch_sustained`'s `Sum`/`Count` over `Neighbours` is
exactly a cached term. **This is pre-registered as the single most likely
source of a byte-identity failure, and if it fires it is MY BUG, not a finding
about the fixpoint** (§6 requires the report to distinguish these).

**(B) SEED DATA.** `"batch": true` on the five `vision_change` rules.
`_install_change_rules` passes each rule dict straight to `nat.add_rule`, and
`graph_rules.rs:~383` interns the `batch` attribute, so no loader change is
needed.

**(C) ADAPTER, ONE LINE.** `_drive_phase` calls `nat.apply_rule_batch(idx)`
in place of `nat.apply_rule_once(idx)`, **keeping the `while ... : pass` loop
verbatim**. Mechanical dispatch, no conditional over graph state — the rules'
own guards continue to decide everything (CLAUDE.md).

---

## 5. THE FLOOR IS NOT 100 — and this is registered BEFORE it is measured

With the `while ... : pass` loop retained, a batch rule that fires costs **TWO
enumerations** per tick: pass 1 applies every binding and returns `True`; pass
2 finds no admissible binding and returns `False`. A rule that fires for zero
cells costs **ONE**. So the achievable floor is

```
floor ∈ [ n_rules × ticks , 2 × n_rules × ticks ]  =  [100, 200]
```

with the exact value determined by how many of the five rules fire on each
tick. **Nothing here is chosen — `n_rules` is read from the seed file and
`ticks` from the schedule (§13).** The second pass is the QUIESCENCE CHECK and
is a property of "loop until no progress", not of batching.

Registering this now so that landing at ~200 cannot later be presented either
as a shortfall against a floor of 100 or as a floor quietly redefined after
the fact (§5).

---

## 6. DECISION RULES

### D1 — BYTE-IDENTITY IS THE GATE, CHECKED FIRST

Read before any exponent is looked at.

1. `bash scripts/rung7_vision_bench.sh` with `data/` symlinked ⇒ **200 passed,
   0 failed, 0 skipped, exit 0.** (Recorded WITH the symlink state — 190/10
   without is the §10.2 trap.)
2. `pytest tests/test_sdloop_vision_migrated.py` ⇒ 8 passed, sd orbit law
   `{2:1, 3:2, 4:2, 6:2, 12:4}` **unmoved**.
3. **The sharpest test, because the drive phase's entire output is the cells'
   attributes:** for each grid in {12,16,24,32,48,64}, on the eye arm under
   the identical schedule, dump a canonical per-cell record of every attribute
   the drive phase can touch — `driven`, `dstep_med`, `dstep_on`, `dstep_off`,
   `dstep_sus`, `lum_ref`, `ref_n`, `ref_step`, plus `state`, `activated_at`,
   `last_burst` to catch downstream drift — batch OFF vs batch ON.
   **Requirement: BITWISE EQUAL.** Floats compared by exact `repr`, never
   rounded and never toleranced — a tolerance here would be metric surgery
   (§5) on the one gate that matters.

**If ANY of the three fails: STOP.** Do not tune, do not reorder, do not
narrow the rule set to make it pass. Report it as a **finding about the
fixpoint's order-independence** — naming the exact rule, cell and attribute —
because that is a genuinely important negative bearing on the shelved async
plan. **The report must state explicitly whether the failure is (a) my
`eval_cache` bug per §4(A), or (b) real order-dependence in the fixpoint.**
These are different results and conflating them would be worthless.

### D2 — THE EFFECT (read only if D1 passes)

Statistic: **counted-op exponent** = log-log slope of `buckets.total` vs
cells, 6 points, 144–4096 cells, via the SAME instrument the scale rung merged
(`scale_audit.rs`, env-gated, default OFF; `scripts/scale_split_measure.py`'s
`fit`), so the numbers are directly comparable.

The threshold is **DERIVED from the two already-measured endpoints**, not
chosen: baseline **1.955**, drive-phase ablation **0.982**, midpoint
**1.4685**.

- **DELIVERS** iff exponent_after < 1.4685 (closer to the ablation than to the
  baseline) AND r² ≥ 0.95.
- **PARTIAL** iff the exponent falls by ≥ 0.15 (the protocol's own
  "does not change" band, from hypothesis (b)'s decision rule) but lands
  ≥ 1.4685.
- **DOES NOT DELIVER** iff the exponent falls by < 0.15. **In that case the
  scale rung's recommendation is WRONG and this document says so in writing**
  (§7): batch-apply would then not be the tool, and the ablation's 138,005×
  would be an artefact of removing the drive phase rather than of removing
  its re-scan.

Also reported, whatever the verdict: counted ops before and after at every
grid; the F/C/R split and its reattribution; `epochs_apply_once` against the
§5 floor band; and the residual if the floor is not reached.

### D3 — WALL-CLOCK

Reported **only** alongside its concurrent-load state, and **never as a
share** (this machine has been measured swinging 1.66× on load alone). Every
headline is a count.

---

## 7. PREDICTIONS, STATED IN ADVANCE (PROTOCOL §3.7)

| # | prediction | confidence | the proviso that would break it |
|---|---|---|---|
| **P1** | **Byte-identity HOLDS on all three D1 checks.** | High — the argument is structural (§3.3), not empirical | If §3.1's cell↔binding bijection is false anywhere, `ch_adapt_ref` breaks first and in the last decimal. My named self-suspicion is the `eval_cache` clear (§4A), which is my bug, not the fixpoint's. |
| **P2** | **DELIVERS: exponent lands ≈ 1.0**, and total ops at 4096 cells land **within 2× of the ablation's 4.10×10⁶**. | Medium-high | The ablation did ZERO drive-phase enumeration; batching still pays ~5–10 full N-scans per tick. If the drive-phase scan dominates the residual, ops could exceed the ablation by more than 2× while the exponent still reads ~1.0 — in which case P2's exponent half is right and its ops half is wrong, and I will score them separately. |
| **P3** | **The floor is approached but lands near 200, not 100** (§5). | High | If some of the five never fire at these grids, it lands below 200. |
| **P4** | **The scan share and the −1 survival slope are UNMOVED.** Batching removes REPEATED scans; it does not make any single scan local. Hypothesis (a)'s ARCHITECTURAL verdict should survive intact. | High | If it moves, the survival statistic was measuring the re-scan loop rather than centralization, which would revise §3 of the predecessor. |

**P2 is the one I most expect to be partly wrong**, and I have said in advance
which half.

---

## 8. SCOPE — declared now, NOT widened later (§5, §8)

- **The five `vision_change` rules ONLY.** That is the named target and the
  whole intervention.
- **Named but NOT touched:** `wv_refract` and `wv_recover`
  (`seeds/vision_waves.json`) match `[r, has_cell, c]` both-unbound through
  the same `Retina` star and were identified by the predecessor's §3 as
  star-scans. They run through `tick()` → `Substrate::run_rules_opts`, which
  **already** has semi-naive incremental matching AND batch dispatch, and
  where the predecessor measured within-epoch re-enumeration at **1.4%**.
  They are not this rung's term. **Touching them after seeing results would be
  the scope change §5 forbids.**
- **ONE workload:** the retina drive (`WaveWorld.step` on `vision_waves` +
  `vision_lateral`, frame-driven, `change=1`, `sustain=1`), the object the
  predecessor split. Nothing here generalises to the identity / sd-loop layer.
- **Coverage will be reported**: how much of the measured 99.81% cross-epoch
  redundancy the five rules actually account for.
- **The measured range is 144–4096 cells.** Any 1080p figure is a labelled
  counterfactual in COUNTED OPERATIONS, never seconds.

---

## 9. PROVENANCE

- **Base commit** (this prereg's parent):
  `6905ec9bd72fca5a3803f588285305e090625b21`.
- **This pre-registration is committed BEFORE** any edit to
  `runners/dsl/src/*.rs`, `seeds/vision_change.json`, `domains/wave_world.py`,
  or any measurement run. The results document will pin BOTH endpoints of its
  diff range explicitly — never a range ending at `HEAD`
  (`tests/test_provenance_endpoint_guard_migrated.py`).
- **Engine:** this rung ADDS RUST, so a shared binary is invalid. The engine
  is built in THIS worktree via `scripts/engine_build.sh` and its realpath +
  md5 are pinned in the results document. A baseline build of the UNMODIFIED
  source is made first, so the "before" numbers come from this tree too and
  the before/after comparison is not confounded by which binary produced it.
- **§9 defaults:** the new Rust method is additive; the seed flag affects only
  the five drive rules; no default elsewhere moves.
