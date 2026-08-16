# Γ consultation flip — closing residual #41 — RESULTS

Prereg: `GAMMA_CONSULTATION_FLIP_PREREG.md`, same worktree/branch. Base
`main @ de1845d` ("Merge mdl-occam-witness-pricing: witness-priced
literals, the Occam-ordering metric fix -- +1 (task 451), zero
regressions"), verified via `git log --oneline -1 main` before creating
the worktree and reconfirmed unchanged at the end of this session.
Worktree: `/home/matt/ozmadev/ocelot-worktrees/gamma-consultation-flip`,
branch `gamma-consultation-flip` — **not merged to `main`, not pushed**,
left for the orchestrator to independently verify and merge.

**Headline: GO. `domains/prog_synthesis.py::run_enumerate` now reads Γ's
own `admissible_moves` verdict as the SOURCE of `spec["ops"]` when the
caller passes no explicit `ops` — closing residual #41. The Γ table was
extended with two small productions (`GroupCount`/`ZipWith`, sites O/P)
covering evidence sites that landed in the Rust ladder AFTER the bulk
transcription rung, both confirmed missing by direct source reading, not
assumed. The paired MBPP battery's FIRST run (post-flip, pre-fix)
surfaced a REAL, genuine regression (−3 full, −3 content_stripped: tasks
171/246/435 lost) — traced to `Mod`/`Sqrt` being pushed unconditionally
on the bare-scalar branch in the real Rust ladder but never having been
given Γ coverage (their branch's Γ verdict was non-empty regardless, so
the empty-verdict fallback never caught the gap). Fixed by widening the
existing bare-scalar-fallback baseline production to also admit
`Mod`/`Sqrt` under the identical gate. The battery was RE-RUN after the
fix and is now byte-identical to the 88/87/114 baseline on all three
arms, exact task-id set diff empty. This is exactly the house discipline
working as designed: a real deviation was found, localised precisely, and
fixed — not swept under "Γ already proven 420/420" from a prior rung.**

---

## 1. What was built

Per the PREREG's own plan (§3), all delivered in this rung, zero `.rs`
files touched (confirmed throughout — `git diff --stat -- runners/dsl/src/`
empty at every checkpoint):

1. **`domains/prog_synthesis.py::run_enumerate`** — the SortBy-only
   `is_edge_admissible` parity probe is replaced by ONE
   `admissible_moves` call over all 58 real `SynthOp` names
   (`_GAMMA_OP_CANDIDATE_ORDER`, a new module-level constant — OP_TABLE's
   own live declaration order, the THIRD instance of this file's
   "duplicated evidence, documented tradeoff" idiom). When the caller's
   own explicit `ps_enum_ops` is absent, Γ's non-empty admitted set
   becomes `spec["ops"]`; an empty verdict leaves `spec["ops"]` unset,
   deferring to the Rust ladder's own internal typed default — byte-
   identical to pre-flip behaviour for that call. New recorded facts:
   `ps_enum_gamma_ops_admitted` (comma-joined names), `ps_enum_gamma_ops_
   used` (bool), `ps_enum_gamma_ops_error` (on exception, never
   propagated — matching the SLICE1 precedent's own discipline).
2. **`_synth_spec_shape_flags`** gains a 12th flag,
   `has_two_zippable_list_vars` — a direct 1:1 port of
   `spec_has_two_zippable_list_vars` (`synth_enumerate.rs:2395-2413`).
3. **`seeds/program_synthesis_opgrammar.json`** (version 1.1.0 → 1.3.0):
   - `ZipWith` added as the 58th static `SynthOp` node (OP_TABLE grew
     58 since the bulk-transcription snapshot's 57, per the
     `progsyn-zip-elementwise` rung, landed AFTER that snapshot).
   - Site O (`site_o_list_shaped_dictlike_output_groupcount`):
     `GroupCount` admitted when `is_list_shaped ∧ output_is_dictlike ∧
     ¬output_is_setlike` — the list-shaped-branch push
     (`synth_enumerate.rs:2667-2669`, task 88's own witness), DISTINCT
     from the still-uncovered `DICT_DEFAULT_OPS` bucket.
   - Site P (`site_p_list_shaped_two_zippable_vars_zipwith`): `ZipWith`
     admitted when `is_list_shaped ∧ has_two_zippable_list_vars ∧
     ¬output_is_setlike` — the `ZIP_ELEMENTWISE` rung's own evidence
     gate, landed after the bulk-transcription snapshot.
   - **The bare-scalar-fallback baseline production widened** (found
     necessary mid-verification, §5): `Mod`/`Sqrt` added to its `In`
     member list, under the SAME gate the 12 `DEFAULT_OPS` names already
     use.
   - 17 productions total (15 from before + sites O/P), 58 `SynthOp`
     nodes (57 + `ZipWith`).
4. **`scripts/opgrammar_bulk_parity_sweep.py`** — updated to match
   CURRENT source exactly (its own oracle had drifted stale): fixed
   `DICT_DEFAULT_OPS` from the stale 5-op list to the real 7-op list
   (`ceiling-reassessment-6` added `DictItems`/`FilterList`, AFTER the
   bulk-transcription snapshot); added the `ZipWith` branch to
   `_real_admitted_ops`; switched `_gamma_admitted_ops` from repeated
   `is_edge_admissible` probes to ONE `admissible_moves` call (the SAME
   mechanism `run_enumerate` now actually uses in production); narrowed
   `_OUT_OF_SCOPE_OPS` from `{GroupCount, DictMerge, DictFromPairs, Mod,
   Sqrt}` to `{DictMerge, DictFromPairs}` (the only two ops that remain
   genuinely out of Γ scope, both confined to the `DICT_DEFAULT_OPS`
   branch).
5. **`tests/test_opgrammar_migrated.py`** — updated seed-count assertions
   (58/17), added dedicated tests for sites O/P, a dedicated `Mod`/`Sqrt`
   regression test, and three new end-to-end tests exercising the flip
   itself live on real MBPP tasks (87 — fallback branch; 88 — site O; 259
   — site P), plus a test confirming explicit `ps_enum_ops` still wins
   over Γ. 32/32 passed (was 31 with the two new O/P unit tests, +1 for
   the Mod/Sqrt regression test).

## 2. Downstream-consumer audit (PREREG §3.4, reconfirmed)

Re-read `eval_synth_enumerate` end to end before writing any code: the
`ZIP_MAX_CANDIDATES`/`DICT_FILTER_MAX_CANDIDATES` budget-raise gates and
`exclude_ops` all read the FULLY RESOLVED `op_list`, "whether it came
from the typed default above or a caller's own explicit `ops`" (the
code's own comment) — confirmed source-agnostic. This is why extending Γ
to cover `ZipWith` (site P) mattered beyond op selection alone: without
it, a Γ-sourced op list missing `ZipWith` would also silently fail to
trigger the 300k-candidate budget raise for zip-shaped specs. With site
P, Γ's output correctly includes `ZipWith` whenever the real ladder's
default would, so the budget gate fires identically regardless of
source — confirmed live on task 259 (§4).

## 3. `admissible_moves` return shape — one implementation correction
   made before any test was run

`admissible_moves` returns `(tgt_TYPE, tgt_attrs, weight)` triples, not
`(tgt_NAME, ...)` — the op NAME lives in `tgt_attrs["name"]`, the first
slot is always the literal string `"SynthOp"` (the candidate TYPE every
scratch node was materialised with). Caught by a direct smoke test before
wiring `run_enumerate` (`admitted[0]` printed as `('SynthOp', {'name':
'Plus'}, 1.0)`, not `('Plus', ...)`) — `run_enumerate` and the parity
sweep both read `attrs["name"]`, documented inline in both places.

## 4. Live confirmation on real MBPP tasks (all four cases)

Ran `run_enumerate` directly (boot → `ensure_program_synthesis` →
`ingest_spec` → `pump` → force `run_enumerate`) on four real, hand-
selected witnesses covering every branch this rung touches:

| task | shape | `ps_enum_gamma_ops_used` | winning term |
|---|---|---|---|
| 64 | list-of-lists, SortBy | True | `SortBy(a, __item, Sort(__item))` |
| 475 | dict-value, SortBy | True | uses `SortBy`/`Reverse` |
| 87 | `merge_dictionaries_three` — DICT_DEFAULT_OPS branch (`is_list_shaped=False, output_is_dictlike=True`) | **False** (Γ verdict empty) | `DictMerge(b, DictMerge(c,a))` — Rust's own internal default, unaffected |
| 88 | `freq_count` — site O witness (`is_list_shaped=True, output_is_dictlike=True`) | True | `GroupCount(a)` |
| 259 | ZIP_ELEMENTWISE witness — site P (`has_two_zippable_list_vars=True`) | True | `ZipWith(a, b, ...)` |
| 2 | negative control, neither gate | True (Γ non-empty, just no `SortBy`) | `Intersect(a, b)` — no `SortBy` |

Task 87 is the discriminating case for the fallback rule itself: Γ's
admitted set is confirmed exactly empty (`ps_enum_gamma_ops_admitted ==
""`), `spec["ops"]` stays unset, and the Rust ladder's own internal
`DICT_DEFAULT_OPS` default finds the SAME `DictMerge`-based solution as
before the flip — the fallback rule works exactly as designed. All five
are now permanent regression tests in `test_opgrammar_migrated.py`
(§1 item 5).

## 5. A REAL regression, found, localised, and fixed — not glossed over

**First paired MBPP battery (post-flip, pre-fix):**

```
full:              85/257  (before: 88)
content_stripped:  84/257  (before: 87)
official:          114/257 (before: 114, but different task-ids)
```

Exact task-id diff against the saved BEFORE state:

```
full:              removed=[171, 246, 435]           added=[]
content_stripped:  removed=[171, 246, 435]           added=[]
official:          removed=[246, 435, 441, 479]      added=[14, 164, 455, 464]
```

Per house discipline ("treat ANY deviation as a bug to find and explain
precisely, never as a bonus"), this was investigated immediately, not
reported as noise. Reading each regressed task's own `_synth_spec_shape_
flags`: ALL of them (171, 246, 435, 441, 479, 14, 464) land in the
**bare-scalar fallback branch** (every flag false except `output_is_bare_
int` for some). The real Rust ladder's bare-scalar `else` arm is:

```rust
let mut v = DEFAULT_OPS.to_vec();
v.extend(extra_evidence_ops.iter().copied());
v.push("Mod");
v.push("Sqrt");
v
```

The bare-scalar-fallback baseline production (added by the bulk-
transcription rung) only ever carried `DEFAULT_OPS`'s 12 names — `Mod`/
`Sqrt` were left out, correctly per THAT rung's own scope (it was never
asked to port them), but the PREREG's own fallback-rule reasoning (§3.2:
"empty Γ verdict ⟺ Γ has no opinion, defer to Rust's own default") does
NOT catch this gap, because the bare-scalar branch's Γ verdict is
NON-EMPTY regardless (`DEFAULT_OPS` alone is 12 real ops) — so `elif
gamma_ops:` fires, `spec["ops"]` is set to the (incomplete) Γ list, and
`Mod`/`Sqrt` are silently dropped for every bare-scalar spec. Task 246
("square roots using the babylonian method") needs `Sqrt`; tasks
171/435/441/479/14/464 need `Mod` for digit/geometry arithmetic. This is
exactly the kind of gap the PREREG's own §4 order-fidelity caveat was
watching for, but it turned out to be a SET-coverage gap, not an order
one. Notably, the parity sweep run BEFORE this battery (with sites O/P
already added, but before the Mod/Sqrt fix) reported **267/420 exact,
153/420 "diff-but-fully-explained", 0 unexpected — a clean GO** —
because `Mod`/`Sqrt` were still listed in `_OUT_OF_SCOPE_OPS` at that
point, so every bare-scalar spec's missing `Mod`/`Sqrt` was silently
classified as an EXPECTED, already-known-out-of-scope difference rather
than flagged. The sweep is only as honest as that exclusion list; it did
not (and structurally could not) distinguish "this op is out of scope
because it should be" from "this op is out of scope because nobody
noticed it should have been covered." The battery — which knows nothing
about `_OUT_OF_SCOPE_OPS` and only measures real search-and-verify
outcomes — is what actually caught this (§8 item 5 returns to this
point).

**Fix**: widened the SAME `bare_scalar_fallback_default_ops_baseline`
production (renamed `..._baseline_plus_modsqrt`) to also admit `Mod`/
`Sqrt`, under the IDENTICAL gate (`¬is_string_shaped ∧ ¬output_is_setlike
∧ ¬is_list_shaped ∧ ¬output_is_dictlike`) — both ops are pushed in this
exact unconditional bare-scalar context in the real ladder, so this is
the SAME site widened, not a new one. `_OUT_OF_SCOPE_OPS` in the parity
sweep narrowed accordingly (`{DictMerge, DictFromPairs}` only).

**Re-verified live** on the exact 6 regressed full/content_stripped
tasks (171/246/435/441/479/464): all now show `ps_enum_gamma_ops_used=
True`, `outcome=ok`, with `Mod`/`Sqrt` present in the Γ-admitted set and
correctly used in the winning term (e.g. task 246 → `Sqrt(a)`; task 441 →
`Mod`-based conditional).

**Re-run parity sweep (post-fix)**:

```
Checked 420 real, runnable MBPP task specs.
Exact set-agreement (Gamma == real, no diff at all): 416/420
Diff-but-fully-explained (out-of-scope ops or Dict branch): 4/420
Specs landing in the out-of-scope DICT_DEFAULT_OPS branch: 4
UNEXPECTED mismatches: 0
TOTAL EXPLAINED: 420/420 (ALL EXPLAINED, GO)
```

Exact agreement jumped from 267/420 (pre-fix, with Mod/Sqrt silently
misclassified as expected diffs) to 416/420 — the remaining 4 are
EXACTLY the 4 real specs landing in the still-uncovered
`DICT_DEFAULT_OPS` branch, nothing else. This single number (416/420 vs
267/420) is itself strong independent confirmation of how large the
bare-scalar branch is in the real corpus, and how much of the pre-fix
"explained" bucket was silently absorbing the Mod/Sqrt gap rather than
genuinely explaining it.

**Re-run paired MBPP battery (post-fix)**:

```
full:              88/257  p=0.342412  ci=[0.287101, 0.402365]  det_identical=True
content_stripped:  87/257  p=0.338521  ci=[0.283424, 0.398375]  det_identical=True
official:          114/257 p=0.44358   ci=[0.384115, 0.504707]  det_identical=True
```

**Byte-identical to the pre-existing baseline** (88/87/114). **Exact
task-id set diff, all three arms:**

```
full:              before=88  after=88  added=[]  removed=[]
content_stripped:  before=87  after=87  added=[]  removed=[]
official:          before=114 after=114 added=[]  removed=[]
```

Zero regressions, zero new passes, at the task-id grain — exactly the
outcome the PREREG predicted for a genuinely behaviour-preserving flip,
achieved only AFTER the real gap found mid-verification was fixed, not
assumed away.

## 6. Regression discipline

**No `.rs` files touched** — `git diff --stat -- runners/dsl/src/` empty
throughout this rung (confirmed before, during, and after); no Rust
rebuild performed or required.

**`tests/test_opgrammar_migrated.py`: 32/32 passed.**

**Named 9-file suite** (`test_prog_synthesis_battery_migrated.py
test_mbpp_baseline_migrated.py test_mbpp_endgame_migrated.py
test_mbpp_contamination_migrated.py test_mbpp_diet_migrated.py
test_program_synthesis_migrated.py test_prog_moves_migrated.py
test_prog_property_migrated.py test_exact_first_migrated.py`) +
`test_opgrammar_migrated.py`, run sequentially AFTER the (post-fix,
byte-identical) battery finished, avoiding the documented shared-
mutable-`results/mbpp_endgame.json`-path contamination this arc's prior
rungs already named:

```
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
3 failed, 273 passed in 181.41s
```

**Exact match, same three test names**, to the already-documented
pre-existing pin-drift failures named explicitly in this task's own
brief and in every prior rung of this arc — none of `test_opgrammar_
migrated.py`'s own 32 tests appear in the failure list (independently
confirmed green, §1 item 5: 32/32 passed standalone). 273 passed here vs
the bulk-transcription rung's own 266 (9 files + 25 opgrammar tests) is
fully explained by the +7 new opgrammar tests this rung adds (32 − 25 =
7), not by anything else changing.

Two of `test_prog_moves_migrated.py`/`test_exact_first_migrated.py`'s
own `test_named_regression_sweep_only_known_pins_drift` failures run an
INTERNAL, broader ~19-file subprocess sweep with its own hardcoded
`_KNOWN_OUT_OF_SCOPE_FAILURES` allowlist; that subprocess's own output
(surfaced inside the pytest assertion text) lists 10 failed/23 errored
node ids beyond its allowlist — this is the PRE-EXISTING pin-drift the
test's own name describes (the reason the test itself is a known,
documented, standing failure — not a new regression introduced by this
rung). Cross-checked against this rung's own diff: none of the touched
files (`domains/prog_synthesis.py`, `seeds/program_synthesis_opgrammar.
json`, `scripts/opgrammar_bulk_parity_sweep.py`, `tests/test_opgrammar_
migrated.py`) appear anywhere in that internal sweep's own failure
list — the internal sweep's failures are drawn from files this rung
never touches (`test_budget_isolation_migrated.py`, `test_mbpp_arc3_
endgame_migrated.py`, `test_prog_descent_migrated.py`, `test_retrieval_
migrated.py`, `test_verdict_discrimination_migrated.py`,
`test_descent_widening_migrated.py`).

## 7. GO/NO-GO

**GO.** `run_enumerate`'s op-list construction is now a real Γ consumer,
not merely a recorder — residual #41 is closed. Two new evidence sites
(O, P) close a genuine post-bulk-transcription coverage gap (`ZipWith`,
`GroupCount`-in-the-list-shaped-branch); a THIRD gap (`Mod`/`Sqrt` on the
bare-scalar branch) was found live by the battery itself, localised
precisely, and fixed — not glossed over. Final state: MBPP battery
byte-identical to baseline (88/87/114, exact task-id diff empty on all
three arms); parity sweep 420/420 explained (416 exact, 4 correctly
attributed to the one branch that remains, by design, out of Γ scope);
named suite + opgrammar suite green modulo the 3 documented pre-existing
pin-drift failures; zero `.rs` changes.

---

## 8. What this document does NOT establish

1. **The `DICT_DEFAULT_OPS` branch remains out of Γ scope**, by design —
   `DictMerge`/`DictFromPairs` are never admitted by any production; a
   spec landing there gets `spec["ops"]` left unset, deferring entirely
   to Rust's own internal default. Extending Γ to cover this branch is a
   real, well-scoped follow-on, not attempted here.
2. **Op-list ORDER fidelity to the real ladder's own per-branch push
   order is NOT proven, only tested indirectly** (PREREG §4's own
   confirmed structural impossibility of a single static order matching
   every branch). The paired battery's exact task-id match is evidence
   this doesn't manifest as an observable regression on the 420-spec
   corpus TODAY, not a proof it never could on a future spec with
   multiple observationally-tied candidates at the same search size.
3. **The literal-pricing-as-Γ-evidence stretch goal** (design doc's
   Slice 2 framing — re-expressing `mdl-occam`'s witness pricing as
   consulted Γ evidence) was NOT attempted — the core flip plus the
   Mod/Sqrt regression investigation consumed this rung's full scope.
   Named as a real, well-scoped follow-on.
4. **`SynthSpecShape` nodes remain undeduplicated** (unchanged from the
   bulk-transcription rung's own standing note) — one minted per
   `run_enumerate` call; not addressed here.
5. **The near-miss in the parity sweep's own pre-battery state is worth
   naming explicitly**: the sweep reported "420/420 ALL EXPLAINED" both
   BEFORE and AFTER the Mod/Sqrt gap existed, because `Mod`/`Sqrt` were
   (correctly, at the time) still listed in `_OUT_OF_SCOPE_OPS` — the
   sweep is only as good as that list's own accuracy, and a genuine
   coverage gap that happens to coincide with an already-declared
   out-of-scope name is invisible to it by construction. The battery
   (which does not know about `_OUT_OF_SCOPE_OPS` at all) is what
   actually caught this — a reminder that the parity sweep and the
   battery are checking DIFFERENT things (admitted-set agreement vs.
   real search-and-verify outcomes) and both are necessary gates, neither
   subsumes the other.
