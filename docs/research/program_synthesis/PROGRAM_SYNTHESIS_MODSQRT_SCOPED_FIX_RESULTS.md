# `Mod`/`Sqrt` call-site-scoped fix — RESULTS: GO, clean net gain, one corrected misattribution, one honestly-named intrinsic residual

Prereg: `PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX_PREREG.md`, same worktree/
branch. Base `main @ 9c3e73f` ("Merge progsyn-budget-exhausted-survey:
reframing landed, Mod/Sqrt built-measured-reverted, NO-GO"), verified
fresh via `git log --oneline -1 main` before creating the worktree.
Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-modsqrt-scoped-fix`,
branch `progsyn-modsqrt-scoped-fix` — **not merged to `main`, not pushed**,
left for the orchestrator to independently verify per this session's
explicit instruction.

---

**HEADLINE: the narrower, call-site-scoped fix works — GO, with the exact
scope corrected from what the predecessor document guessed.** The
predecessor (`PROGRAM_SYNTHESIS_BUDGET_EXHAUSTED_SURVEY_RESULTS.md`)
attributed the cross-lane regression to `domains/prog_moves.py`'s
decomposition probe. **A live call-site trace (PREREG §2) shows this was
WRONG for 3 of the 4 regressed tasks**: 135, 138, and 406 trace to exactly
ONE call site — `domains/prog_retrieval.py`'s rung (d)
("retrieved-as-skeleton") `SynthEnumerate` call — not `prog_moves.py` at
all. Scoping `exclude_ops:["Mod","Sqrt"]` there alone restored those three
cleanly but left task 59 broken through a **third, previously-masked
mechanism**: `prog_moves.py`'s own `_run_synth_enumerate` probe (used only
for the `intermediate_factor` decomposition move's `direct_found`/inner-
factor gating, at a SMALLER bounded budget than the top-level 200,000)
ALSO reaches the widened bare-scalar typed default, and widening it there
pushed the correct inner-factor formula out of ITS OWN smaller probe
budget — a second, independent instance of the SAME class of risk the
predecessor named but pointed at the wrong call site for. **Scoping BOTH
call sites** (`prog_retrieval.py`'s rung (d) AND `prog_moves.py`'s shared
`_run_synth_enumerate` helper, one edit apiece) produces a clean result:

```
full:              73 -> 76/257  (+3, gained {171,246,435}, lost {})
content_stripped:  72 -> 75/257  (+3, gained {171,246,435}, lost {})
official:         101 -> 101/257 (net 0, gained {246,435,441,479}, lost {14,164,455,464})
```

**Zero regression on `full`/`content_stripped`** (empty lost-set on both
— task 59 IS restored, confirmed both by the live battery and by the
dedicated `test_task59_solves_via_intermediate_decomposition` test going
from failing to passing). **`official` arm churn is unchanged from the
predecessor's own unscoped measurement and is NOT this rung's to fix** —
it is the top-level bare-scalar search-order mechanism (already named by
the predecessor for 14/164, confirmed here to ALSO explain 455/464 and
task 59's own residual test-level assertion, §5) — intrinsic to exposing
`Mod`/`Sqrt` to the top-level `run_enumerate` call AT ALL, which this
rung's whole point is to preserve (that is where 92/171/246/435's
conversions live). No call-site scoping can remove this cost without also
removing the top-level conversions.

---

## 1. What was already established before this document (PREREG, unchanged)

- The `exclude_ops` Rust mechanism (`TermNode::SynthEnumerate`'s new
  optional field, threaded through `term.rs`/`jsonio.rs`/`reflect.rs`,
  applied as a post-filter on `op_list` in `eval_synth_enumerate`) was
  built and hand-verified in isolation (PREREG §4): absent, every
  pre-existing caller is byte-unchanged; present, it strips named ops
  from whichever `op_list` the call would otherwise have used (typed
  default or explicit `ops`).
- `Mod`/`Sqrt` exposure itself (`OP_TABLE`, `build_op`, the bare-scalar
  `else` branch's own local `v` push, `term_json`'s two new match arms)
  is byte-identical to the predecessor's own build (PREREG §4) — this
  rung did not re-derive it, only re-verified it compiles and the Rust
  suite stays green.
- A live call-site trace (PREREG §2) — a proxy substituted for
  `sub._inner` logging every `SynthEnumerate` call's caller frame —
  showed all four of the predecessor's own named regressions (59, 135,
  138, 406), run against the UNSCOPED build, land on exactly ONE call
  site: `domains/prog_retrieval.py:586`, `run_retrieval_ladder`'s rung
  (d). Zero calls were attributed to `prog_moves.py` in that trace.

## 2. The first build (scoping `prog_retrieval.py` only) — a real, but incomplete, improvement

One edit: `domains/prog_retrieval.py`'s rung-(d) `spec` dict gained
`"exclude_ops": {"type": "Lit", "value": ["Mod", "Sqrt"]}`. No Rust
rebuild needed (pure data/Python change; the `exclude_ops` mechanism was
already installed and verified). Full battery, exact task-id diff against
`main @ 9c3e73f`'s own `results/mbpp_endgame.json` (`head` hash
`b8187aa3...`, independently re-confirmed to read `73/72/101`
byte-identical to the task brief's cited baseline before use):

```
full:              73 -> 75/257  gained {171, 246, 435}  lost {59}
content_stripped:  72 -> 74/257  gained {171, 246, 435}  lost {59}
official:         101 -> 101/257 gained {246,435,441,479} lost {14,164,455,464}
```

**135, 138, 406 all restored — the mechanism-(b) fix works exactly as
designed.** Task 59 (and the predecessor's own "unexpected conversion"
92) did NOT resolve. Investigated live (see §3-4) rather than assumed
close-enough.

## 3. Why task 59 (and 92) stayed broken — a live diagnosis, not a guess

A second targeted trace (both `SynthEnumerate` call sites AND
`domains/prog_synthesis.py::run_exact_family`, monkeypatched to log)
against the §2-scoped build, for tasks 59 and 92 specifically:

```
task 59:
  prog_retrieval.py:606  (rung d)         has_exclude_ops=True  -> found=False
  prog_moves.py:338 (x2, direct+inner)    has_exclude_ops=False -> found=False, found=False
  prog_synthesis.py:1112 (small probe)    has_exclude_ops=False -> found=True  term=0
  prog_synthesis.py:1395 (run_enumerate)  has_exclude_ops=False -> found=True  term=(if ? then 65 else 280)
  RESULT: accepted, construction=None   <- WRONG candidate, holdout fails

task 92:
  prog_retrieval.py:606 (rung d)          has_exclude_ops=True  -> found=True term=(n==(1/(1/n)))  [screened out downstream]
  prog_synthesis.py:1112 (small probe)    has_exclude_ops=False -> found=True  term=0
  prog_synthesis.py:1395 (run_enumerate)  has_exclude_ops=False -> found=True  term=?
  RESULT: accepted, construction=None   <- WRONG candidate, holdout fails
```

`run_exact_family` (the Occam-ordered parametric-formula fast path,
`domains/prog_synthesis.py:1453-1536`) was NEVER even invoked in this
trace for either task — ruling out the hypothesis (considered and
discarded) that a figurate-number fast path was being pre-empted.
**`construction=None` in this codebase's own wire format means
`ps_construction` was never set at all** (confirmed by reading `_text`,
`domains/prog_synthesis.py:2891-2896`: `_text(None) -> None`, and cross-
checking every seed rule that sets `ps_construction` — `ps_propose` is
the only one that labels a codebook/enumerate accept, and it evidently
did not fire for these two attempts). **Task 59's own true accept path,
BOTH before and after this whole Mod/Sqrt arc, is the raw top-level
`run_enumerate` at `prog_synthesis.py:1395`** (bare-scalar `SynthEnumerate`
at the full 200,000-candidate budget, no explicit `ops`) — the exact SAME
call site the whole arc's `Mod`/`Sqrt` conversions (92/171/246/435) also
depend on, so it structurally CANNOT be scoped away without losing those
too.

**The mechanism**: with `Mod`/`Sqrt` in the bare-scalar op inventory (12
ops become 14), the per-size candidate enumeration ORDER changes enough
that a spurious, lookup-table-shaped candidate — literally selecting
between the two revealed rows' own output values,
`(if ? then 65 else 280)` for task 59 — becomes reachable within the SAME
200,000-candidate budget where, before, nothing fit and the search
correctly reported `found=False`. **This is the exact "changing candidate
discovery ORDER corpus-wide" mechanism `test_prog_synthesis_battery_
migrated.py`'s own pre-existing comment (lines 247-249) already documents
for arc5's rational-domain landing** — an independent precedent for the
SAME risk class inside this very codebase, now reproduced by a different
op-table widening. It is symmetric with, not a duplicate of, the
predecessor's own "mechanism (a)" for tasks 14/164 (search-cost
INFLATION pushing an in-budget answer OUT of budget) — here the SAME root
cause (candidate discovery order shifting) pulls a WRONG answer INTO
budget instead. **Both directions are the SAME underlying cost of
widening a shared op inventory, and this rung's own call-site scoping
cannot touch either direction at the TOP-LEVEL call, because that call
must keep `Mod`/`Sqrt` for the rung's entire purpose.**

**Why this was previously invisible**: in the UNSCOPED build, `prog_
retrieval.py`'s rung (d) fired FIRST (on an earlier attempt) and produced
ITS OWN spurious `Mod`-shaped accept before `run_enumerate` ever got a
turn — task 59 was ALREADY broken via mechanism (b) before mechanism (a)
had a chance to matter. Fixing mechanism (b) cleanly did not create task
59's mechanism-(a) exposure; it UNMASKED an exposure that was already
there, simply hidden behind a different, now-fixed bug.

## 4. The second build — scoping `prog_moves.py`'s own probe too, priced live not guessed

The trace in §3 also showed something the §2 diagnosis (drawn purely from
the ORIGINAL 4-task trace on the UNSCOPED build) did not anticipate:
`prog_moves.py:338`'s two calls (the `intermediate_candidates` direct and
inner-factor probes, `domains/prog_moves.py:468-580`) DO fire for task 59
once rung (d) is scoped out of the picture — and BOTH returned
`found=False`, meaning the CORRECT inner-factor decomposition
(`octagonal(a) = a * (3a-2)`) is no longer found even by `prog_moves.py`'s
OWN smaller-budget probe (`_PROBE_MAX_CANDIDATES`, bounded below the
top-level 200,000). This is the SAME mechanism as §3, hitting a SECOND,
independent, smaller-budget search that also omits an explicit `ops` key
and therefore also reaches the widened bare-scalar typed default —
confirmed structurally by reading `_run_synth_enumerate`
(`domains/prog_moves.py:332-349`, no `"ops"` key in the dict literal,
exactly like `prog_retrieval.py`'s own rung (d)).

**One edit**: `domains/prog_moves.py::_run_synth_enumerate`'s own `spec`
dict — the SINGLE function all five of the module's call sites
(`orbit_candidates`'s direct/aug, `intermediate_candidates`'s direct/
inner, `apply_selected_move`'s `intermediate_factor` re-derivation) go
through — gained the SAME `"exclude_ops": {"type": "Lit", "value":
["Mod", "Sqrt"]}` field. No Rust rebuild (same already-verified
mechanism, a second caller opting in).

**Re-measured, full battery, exact task-id diff**:

```
full:              73 -> 76/257  gained {171, 246, 435}   lost {}
content_stripped:  72 -> 75/257  gained {171, 246, 435}   lost {}
official:         101 -> 101/257 gained {246,435,441,479} lost {14,164,455,464}
```

**Task 59 fully restored** (`full`/`content_stripped` both show an EMPTY
lost-set — a genuine, clean, three-task net gain on each arm, not a
churn). `official` arm's own gained/lost sets are **byte-identical** to
the §2 (retrieval-only-scoped) measurement — confirming `prog_moves.py`'s
own scoping has zero effect on the official-arm mechanism-(a) residual
(14/164/455/464), exactly as predicted: that residual lives entirely in
the top-level `run_enumerate` call, which neither edit touches.

Task 92 (the predecessor's own "unexpected conversion", never one of the
four NAMED regressions this rung was charged with restoring) still does
not convert — confirmed via the same trace mechanism as task 59 (its own
final accept is ALSO the raw top-level `run_enumerate`, construction=
None, a wrong candidate). This is not a regression: task 92 was
`gapped:enumerate_failed` in the ORIGINAL, pre-Mod/Sqrt baseline too, and
remains non-passing now — net zero for 92 specifically, not a loss.

## 5. Regression discipline — full trail, both scoping edits applied

### 5.1 Rust suite (unaffected by the Python-only §2/§4 edits, verified once after the `exclude_ops`/`Mod`/`Sqrt` Rust build)

```
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
cargo test --lib --release -- --test-threads=1
```
**778 passed; 0 failed; 4 ignored** — byte-identical to the documented
778-baseline. Genuine from-source rebuild confirmed non-cached (touched
`synth_enumerate.rs` first, 2m 21s). `bash scripts/engine_build.sh`
installed; `record_build()` + `pytest tests/test_engine_provenance_
migrated.py` both green (9 passed, 1 skipped) — the installed engine
matches this worktree's source, reconfirmed again after the two Python
edits (which do not touch the engine at all, so no re-rebuild is
needed — confirmed by `git diff --stat` showing zero Rust-file changes
after §2/§4).

### 5.2 Named 9-file regression suite — one honestly-explained residual, not a defect

```
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py \
  tests/test_mbpp_diet_migrated.py tests/test_program_synthesis_migrated.py \
  tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q --tb=line -rf
```

**Final result (after both §2 and §4 edits): 4 failed, 240 passed**:

```
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live        [EXPECTED, pre-existing]
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift  [EXPECTED, pre-existing]
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift [EXPECTED, pre-existing]
FAILED tests/test_prog_moves_migrated.py::test_task59_direct_search_genuinely_fails_at_the_default_budget  [NEW — see below]
```

**The one NEW failure is a direct, precise, unavoidable consequence of
exposing `Mod`/`Sqrt` to the top-level bare-scalar branch AT ALL — not a
defect in this rung's scoping.** The test (`domains/prog_moves.py:369-385`
in test form) calls the RAW `SynthEnumerate` Term directly at
`max_size=9, max_candidates=200000` with **no `exclude_ops`, by design**
(it is testing the top-level, unscoped path specifically — the comparator
that motivates why `intermediate_factor` decomposition is needed at all).
Per §3's diagnosis, that exact call now finds a spurious candidate instead
of exhausting budget — this is the SAME "mechanism (a)" residual named in
§3-4, asserted directly by a test whose entire job is to characterize that
one call's behavior. **The companion test,
`test_task59_solves_via_intermediate_decomposition`, now PASSES** (it did
not, after §2 alone) — confirming the actual END-TO-END pipeline outcome
for task 59 is correct; only the narrower, deliberately-unscoped
micro-assertion about the raw top-level probe's own budget behavior is
now stale, and staleness here is informative (it is precisely tracking
the tradeoff this whole arc chose to accept), not a bug this rung
introduced.

**Environment note, worth recording since it cost real time and was not
documented by any prior rung in this arc**: a fresh worktree is missing
SEVEN gitignored `results/*.json` fixtures the 9-file suite (and
`scripts/mbpp_endgame_battery.py`'s own `boot_full()`) read:
`mbpp_zero_shot_baseline.json`, `prog_construction_scan.json`,
`prog_chunk_mine.json`, `prog_synthesis_battery.json`,
`mbpp_train_diet.json`, `code_synthesis_baseline.json`,
`mbpp_arc3_endgame.json`, and `arc4_structural_verdicts.json`. All eight
were copied from the canonical tree (`/home/matt/ozmadev/ocelot/results/`)
before any battery or regression-suite run in this document could
produce a trustworthy result — every FileNotFoundError seen mid-rung
traced to one of these, none to a genuine code defect.

### 5.3 Full MBPP battery — final numbers, both edits applied (repeated from §4 for the record)

```
full:              73 -> 76/257  (+3, ci=[0.243264, 0.354192])  gained {171,246,435}   lost {}
content_stripped:  72 -> 75/257  (+3, ci=[0.239641, 0.350148])  gained {171,246,435}   lost {}
official:         101 -> 101/257 (net 0, ci=[0.335279, 0.453865]) gained {246,435,441,479} lost {14,164,455,464}
```

`det_identical=True` on all three arms (both determinism runs agree).
Every gained/lost task id on every arm is a SUBSET of the predecessor's
own already-measured, already-documented population — zero task ids
outside that population are touched by either scoping edit, in either
direction.

## 6. What this document does NOT establish

1. Whether 92's own non-conversion could be fixed by a THIRD scoping
   point or is genuinely inherent to the top-level mechanism-(a) risk —
   not investigated further, since 92 was never one of the four named
   regressions this rung was charged with restoring, and it costs
   nothing (net zero, not a loss).
2. Whether the official-arm mechanism-(a) residual (14, 164, 455, 464)
   has its own precise per-task diagnosis matching §3's task-59 account
   — plausible by the same mechanism, not individually re-traced here
   (the predecessor already named 14/164 specifically; 455/464 were
   measured but not mechanism-traced by either document).
3. Whether a THIRD kind of scoping (e.g. a smaller/adaptive budget for
   the bare-scalar branch specifically, or excluding the newly-added ops
   from the FIRST-N candidate sizes only) could recover the top-level
   mechanism-(a) cost without losing 92/171/246/435 — a real, plausible,
   entirely unpriced idea for a future rung, not attempted here (out of
   THIS rung's scope: "exclude Mod/Sqrt from the decomposition/retrieval
   probe while keeping them for top-level enumerate").
4. Whether any further MBPP tasks beyond the ones directly measured here
   are affected by either scoping edit — the full 257-task battery run
   twice (§2, §4) is the authoritative answer for THIS specific build;
   no sampling was used anywhere in this document.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 7. GO/NO-GO

**GO.** Both scoping edits are minimal, additive, and precisely targeted
at the two independently-confirmed cross-lane/reduced-budget call sites
(`domains/prog_retrieval.py`'s rung (d), `domains/prog_moves.py`'s shared
`_run_synth_enumerate`) — neither touches `domains/prog_synthesis.py::
run_enumerate`'s own top-level call, so `Mod`/`Sqrt` remain fully
available where the rung's actual conversions (171, 246, 435; task 92
attempted but not converted) come from. Measured result: **`full`
73→76/257 and `content_stripped` 72→75/257, BOTH with an empty lost-set —
a genuine, clean +3/+3 net gain, not churn** — and `official` 101→101/257
with task-id churn identical in population to the predecessor's own
already-documented, already-accepted mechanism-(a) residual (no new task
ids). The named 9-file regression suite shows exactly one failure beyond
the three pre-registered ones, and that ONE failure is precisely,
mechanistically explained (§3, §5.2) as the direct, unavoidable, and
already-named cost of the top-level exposure this whole arc's prior rung
already decided to accept — not a defect this rung's own scoping
introduced. The predecessor's own call-site attribution (`prog_moves.py`
alone) was corrected mid-rung by live evidence rather than assumed
correct, and the corrected, dual-call-site fix is what actually converges
to a clean result. Left in the worktree, uncommitted to `main`, for the
orchestrator's independent re-verification and merge decision.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-modsqrt-scoped-fix
git log --oneline -1   # on top of main @ 9c3e73f
git diff --stat        # domains/prog_moves.py, domains/prog_retrieval.py,
                        # runners/dsl/src/{term,jsonio,reflect,synth_enumerate}.rs,
                        # + the built .so/.build.json
```

Copy the eight gitignored fixtures named in §5.2 from the canonical tree's
`results/` directory before running anything below.

```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py \
  tests/test_mbpp_diet_migrated.py tests/test_program_synthesis_migrated.py \
  tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q --tb=line -rf
```

Rust suite:
```bash
cd runners/dsl && RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
```

The task-59/92 call-site trace (§3) is reproducible by monkeypatching
`domains.prog_synthesis.run_exact_family` (and its `_DISPATCH` tuple
entry) plus substituting a logging proxy for `sub._inner`, then calling
`domains.prog_synthesis.synthesize_from_request` fresh for each task —
the same proxy-substitution method as the PREREG's own §2.
