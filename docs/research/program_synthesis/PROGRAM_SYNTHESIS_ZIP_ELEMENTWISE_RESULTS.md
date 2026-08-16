# ZIP_ELEMENTWISE — primitive built and verified correct; MEASURED MBPP
gain is ZERO — RESULTS

Prereg: `PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_PREREG.md` (this worktree). Base
`main @ dbe67c6`, verified fresh before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-zip-elementwise`, branch
`progsyn-zip-elementwise` — **not merged to `main`, not pushed.**

**A DISK-SPACE SCARE, HONESTLY RECORDED, THAT RESOLVED BEFORE THE RUNG
FINISHED.** Host free space dropped from 22G (worktree creation) to
**7.9G** (100% used) mid-rung, from a CONCURRENT, unrelated session's own
activity — not this rung's own work (this rung's own `target/` growth was
the same bounded ~1-2 min-per-rebuild pattern every prior rung in this arc
measured). Per the task brief's explicit instruction, this triggered an
immediate, unconditional STOP the moment free space was confirmed below
10G: all further `cargo build`/`cargo test`/battery re-runs were halted,
no disk cleanup attempted (not this rung's call to judge another session's
files safe to remove). Free space subsequently RECOVERED (17G, stable,
confirmed repeatedly across the remainder of this rung) as the concurrent
session's own activity moved on — the regression suites below (§5) were
then run to completion, re-checking `df -h /` before each step. **Nothing
in this rung's own work pushed the host below 10G at any point** — the
drop and recovery both track the concurrent session, confirmed by this
rung's OWN build artifacts staying the same bounded size across every
rebuild in this session.

---

## Headline

**The primitive is real, correctly designed, and independently verified
correct end-to-end (hand simulation, real-engine hand-built terms on
revealed+held-out rows, and real `SynthEnumerate` search calls all agree).
The measured MBPP battery gain is ZERO — `full`/`content_stripped`/
`official` are BYTE-IDENTICAL to baseline (76/75/101), exact task-id set
diff confirms zero gained AND zero lost on all three arms.** The cause is
diagnosed and localized, live, not guessed: **none of the 8 target tasks'
real `synthesize_from_request` call ever reaches `SynthEnumerate` with a
chance to use `ZipWith` under conditions where it can still help** — for 5
tasks (261/273/282/399/429) a PRE-EXISTING, EARLIER construction lane
(`retrieved_exemplar`) proposes a WRONG candidate first and the pipeline's
own documented, deliberate policy (`seeds/program_synthesis.json`, the
`ps_structural_reject_exclusion_reopen`/D1/D2 comment) is to terminate as
`gapped:structural_verdict_reject` rather than fall through to enumerate;
for the 3 nested tasks (259/401/445), enumerate at least sometimes runs but
the DEFAULT `max_candidates` budget (200,000) is measurably ~30% short of
what the full production op inventory needs to reach `ZipWith`'s own
size-9 nested candidate (measured: 261,316-261,322 tested to solve it under
the REAL default op inventory, vs the 200,000 cap). **This is a legitimate,
reportable NULL per this rung's own task brief** ("fewer than 2 of the 8
tasks actually convert... that's a legitimate outcome to report honestly
rather than force through") — 0 of 8 converts in the measured battery,
despite the primitive itself being correct.

---

## 1. What was independently verified correct

### 1.1 The 8-task cluster is genuine, not a stale citation (PREREG §2)

Every task's real prompt + reference `code` re-read from
`sanitized-mbpp.json` directly — all 8 confirmed a genuine `zip(a,b)` +
per-pair binary combiner shape (5 flat: 261/273/282/399/429; 3 one-level-
nested, a tuple OF tuples: 259/401/445). None of the 8 was already passing
under the fresh baseline (confirmed by direct set intersection against
`results/mbpp_endgame_BEFORE_this_rung.json`'s own pass-id list — empty).

### 1.2 Zero-new-Term composability checked and ruled out (PREREG §3)

Read `term.rs` end-to-end: every sequence-iterating Term (`MapList`,
`MapSet`, `IndexedMap`, `Sum`, `Prod`, `MaxOver`, `MinOver`, `Fold`,
`FilterList`, `Exists`) binds over ONE source. `vec_binary`
(`VecAdd`/`VecSub`) already zips two operands but with a hard-coded f64
closure, never a Term argument, and always emits a bare `Tuple` (wrong for
task 282's List). No zero-new-Term composition reaches the needed shape —
confirmed, not assumed.

### 1.3 Design hand-verified BEFORE any Rust was written (PREREG §4)

A Python simulation of the exact intended `ZipWith` semantics (`zip`
truncation + type-preserving output) verified all 8 tasks, 24/24 rows
(revealed + held-out), including exact container-type match, BEFORE any
`.rs` file was touched.

### 1.4 Built, and re-verified against the REAL engine

`TermNode::ZipWith { a, b, a_name, b_name, value }` (`term.rs`) + 6-file
registration (`term_variants.rs` regen, `reflect.rs`, `jsonio.rs`,
`synth_enumerate.rs`: `OpKind::ZipMap`, `OP_TABLE` entry,
`build_zip_with`, `ZIP_ELEMENTWISE_OP_NAMES`/`build_zip_elementwise_op`, 4
new local `Sym`s, `spec_has_two_zippable_list_vars` evidence gate,
`zip_op_templates_by_size` pool, growth-loop arm) — full design in
`PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_PREREG.md` §5.

**`cargo build --release` succeeded genuinely from source** (2m03s wall,
not a cached sub-second finish — confirmed by rebuild after each Rust edit,
5 separate genuine rebuilds across this rung). `cargo check --release`
clean (no errors, only pre-existing warnings) after the FINAL diff.

**Hand-built `ZipWith` terms, evaluated through the real, newly-built
engine (`substrate_rs.Substrate()._inner.evaluate`), all 8 tasks, ALL
rows (revealed AND held-out): 24/24 correct**, including exact container-
type match (List for 282, Tuple for the other 7) — reproduced in §6.

**The REAL `SynthEnumerate` Term, called directly (not the production
pipeline), with the production TYPED-DEFAULT op inventory (no explicit
`ops` override), against each task's real revealed rows:**

```
259 (nested Max)   -> found=False, tested=200000, halt=budget   (default 200K cap)
261 (flat IDiv)    -> found=True,  tested=17039,  halt=solved,  size=6
273 (flat Minus)   -> found=True,  tested=19233,  halt=solved,  size=6
282 (flat Minus)   -> found=True,  tested=10352,  halt=solved,  size=6
399 (flat BitXor)  -> found=True,  tested=15488,  halt=solved,  size=6
401 (nested Plus)  -> found=False, tested=200000, halt=budget   (default 200K cap)
429 (flat BitAnd)  -> found=True,  tested=19712,  halt=solved,  size=6
445 (nested Times) -> found=False, tested=200000, halt=budget   (default 200K cap)
```

**5 of 8 (all the FLAT tasks) solve directly within the default 200,000-
candidate budget, at the exact predicted size (6) and term shape** (e.g.
`261 -> "[(__za // __zb) for __za, __zb in zip(a, b)]"`). The 3 NESTED
tasks (259/401/445) exhaust budget at size 9 under the FULL default op
inventory. Raising `max_candidates` to 2,000,000 confirms all 3 DO solve
(261,316–261,322 tested, ~30% over the 200,000 default) at the exact
predicted term (`"[[max(__zi,__zj) for __zi,__zj in zip(__za,__zb)] for
__za,__zb in zip(a,b)]"` etc.) — **the mechanism is correct; it is
short of the DEFAULT budget under real-world op-inventory competition, not
broken.** Isolating `ops=['ZipWith']` alone (no competing ops) finds the
SAME nested candidates in 42-48 tested — confirming `ZipWith`'s own
registration cost is exactly as cheap as designed (PREREG §5's size
accounting); the shortfall is competition from the rest of the (much
larger) default op inventory across sizes 2-8, not `ZipWith` itself.

**One genuine mid-rung finding, found live and fixed (not silently
absorbed):** `synth_enumerate.rs`'s OWN local `term_json`/`term_str`
renderers (distinct from `jsonio.rs`'s — the SAME distinction the
`MkDict`/`DictFromPairs` rung already named) had NO arm for `IDiv`,
`BitAnd`, or `BitXor` — three pre-existing, fully-shipped `TermNode`s
(already handled everywhere else in the engine — `jsonio.rs`, `reflect.rs`,
`term.rs`'s own `copy_subtree`/`children`/`evaluate`) that had simply never
been exposed via `OP_TABLE` before, so this module's exhaustive local
renderer never needed an arm for them. `ZipWith`'s template pool is the
FIRST thing to make all three reachable as part of a winning search
candidate (tasks 261/399/429's own winning terms), which panicked
(`unreachable!("candidates are built only from the op table + leaves")`)
the first time the search tried to render one. Diagnosed via a temporary
`{:?}`-printing debug arm (reverted before shipping), confirmed the exact
missing variant each time, fixed with 3 small additive arms (mirroring
`Div`'s own existing arm exactly) — the SAME class of gap, found and fixed
the SAME way, `DICTFROMPAIRS_PREREG.md` §4 already hit for `MkDict`.
**This IS a real, load-bearing fix** (without it, `ZipWith` would panic —
not silently degrade — the first time it solved a task using these three
ops) and is included in the diff below.

---

## 2. The real battery — measured, byte-identical to baseline

```
full:              76/257  p=0.29572   ci=[0.243264, 0.354192]  det_identical=True
content_stripped:  75/257  p=0.291829  ci=[0.239641, 0.350148]  det_identical=True
official:         101/257  p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

**Exact task-id set-diff, all three arms, direct set computation (never
bare counts):**

| arm | before (n) | after (n) | gained | lost |
|---|---|---|---|---|
| `full` | 76 | 76 | `{}` | `{}` |
| `content_stripped` | 75 | 75 | `{}` | `{}` |
| `official` | 101 | 101 | `{}` | `{}` |

**Zero gained, zero lost, on all three arms.** None of the 8 target tasks
entered the pass set; no other task regressed.

---

## 3. Root cause, traced live (a logging proxy substituted for `s._inner`,
   the same method this arc's own prior rungs use)

Per-task status against the REAL `synthesize_from_request` pipeline (the
exact call `mbpp_endgame_battery.py`'s own `run_task` makes):

```
259 -> gapped:enumerate_failed         construction=None
261 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
273 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
282 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
399 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
401 -> gapped:enumerate_failed (construction=mck_prog_aug_assign_n2_q3 attempted first)
429 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
445 -> gapped:enumerate_failed (construction=mck_prog_aug_assign_n2_q3 attempted first)
```

**A logging proxy substituted for `s._inner.evaluate`** (a thin wrapper
class — the native PyO3 `Substrate` object's own methods are read-only and
cannot be monkeypatched directly, confirmed live; the plain-Python
`Substrate` WRAPPER's `_inner` attribute CAN be reassigned, which is what
makes this technique work at all) traced every real `SynthEnumerate` call
task 261 and task 259 actually make through the production pipeline:

```
261: 1 SynthEnumerate call, max_size=7, no explicit `ops` (typed default)
     -> but the TASK'S OWN final verdict came from `retrieved_exemplar`,
        NOT from this enumerate call — confirmed by `construction` field.
259: 3 SynthEnumerate calls (max_size=7, then a max_size=1 probe, then
      max_size=9) -> the size=9 call is where `ZipWith`'s nested candidate
      WOULD be reached, but the real call's own budget (unspecified in the
      JSON, defaulting internally) is exhausted before solving it,
      matching the isolated 200K-budget measurement above.
```

**For the 5 `retrieved_exemplar`-intercepted tasks, `SynthEnumerate` is
invoked in the real pipeline (once, non-zero evidence it CAN reach ops
correctly), but the interception happens at a HIGHER level: a prior,
separate construction lane (`retrieved_exemplar`, a pattern/template-based
retrieval, distinct from the raw-enumerate fallback) proposes a candidate
FIRST. When that candidate fails a downstream structural verdict, the
pipeline's own EXISTING, DOCUMENTED policy — read directly from
`seeds/program_synthesis.json`'s own comment on `ps_structural_reject_
exclusion_reopen` (added by a PRIOR rung, not this one) — is to terminate
as `gapped: structural_verdict_reject` rather than retry via enumerate**:
*"`ps_construction=='retrieved_exemplar'` means [an exclude-and-retry]
can't [distinguish candidates] ... measured live as the S2 stall ... so
THIS rung goes straight to the honest terminal."* This is PRE-EXISTING
architecture from a different rung's own deliberate, measured decision —
not a bug this rung introduced, and not something this rung's own scope
(a missing arithmetic PRIMITIVE) is positioned to fix; fixing it would be
a construction-lane/pipeline-dispatch change, a different, larger-blast-
radius class of work this arc has repeatedly declined to bundle into a
single-variable rung (the SAME discipline `GROUPCOUNT_DICTMERGE_RESULTS.md`
and `BUDGET_EXHAUSTED_SURVEY_PREREG.md` both already apply elsewhere).

**For the 3 nested tasks, the mechanism DOES get a chance (enumerate runs,
sometimes multiple times) but the default `max_candidates` budget is short
by ~30% under the real, much larger production op inventory** — this one
IS, in principle, a search-cost/budget question this arc's own prior
work (`MAX_SIZE_SEAM_PRICING_PREREG.md`, cited in the budget-exhausted
survey) has already investigated and NO-GO'd as a global change (raising
the shared default budget affects every task's search cost, a much larger
blast radius than this rung's own single-primitive scope) — not
re-litigated here.

---

## 4. What this establishes, and what it does not

**Established, independently, with the real engine:** `ZipWith` is a
correctly-designed, correctly-built, correctly-verified new primitive that
DOES let `SynthEnumerate` solve all 8 of the target tasks' underlying
program-synthesis PROBLEM (as opposed to the MBPP battery's own,
DIFFERENT, higher-level pass/fail criterion) — 5/8 within the exact
default budget the real battery uses, 3/8 with a larger budget, at the
EXACT term shape the task's reference implementation names, verified
against revealed AND held-out rows every time. This is a genuine
capability the search did not have before this rung and now does.

**NOT established:** that this capability converts any MBPP task in the
real, measured battery — it measurably does not, for reasons entirely
outside `SynthEnumerate`/`ZipWith` itself (§3). Per CLAUDE.md's Purpose
section, this is exactly the class of null this arc is supposed to report
as a headline finding: **the target (an MBPP score gain) was aimed at,
missed for a real, localized, generalizable reason (construction-lane
precedence + a budget shortfall, not the primitive), and the underlying
capability (`SynthEnumerate` reaching a two-sequence lockstep combine) is
real and independently verified regardless of the score.** This is also a
second, independent confirmation of a lesson this arc has already named
once (`GROUPCOUNT_DICTMERGE_RESULTS.md`'s own "construction ≠ conversion"
residual for task 88/`retrieved_exemplar`) — here the SAME mechanism
blocks conversion for 5 tasks OUTRIGHT, not just via a different attributed
construction path.

**NOT established:**

1. **Regression risk for `spec_has_two_zippable_list_vars`'s own
   additive gate** (PREREG §6) is REASONED about (purely additive,
   `list_by_size[1]`-only sourcing bounds worst-case cost) but not
   confirmed against a DEDICATED canary sweep the way
   `GROUPCOUNT_DICTMERGE_RESULTS.md` §5-7 did — the battery's own
   zero-regression set-diff (§2 above, `{}` lost on all 3 arms) and the
   Rust/Python regression suites (§5 below, both clean) ARE real evidence
   of no regression across the populations they cover, but no task-by-task
   audit of every currently-passing task with 2+ equal-length list-shaped
   variables was performed.
2. Whether a different (non-MBPP, non-regression-suite) task or canary
   anywhere in the broader codebase is touched by this rung's changes is
   unknown — out of this rung's own scoped verification.

---

## 5. Regression discipline — completed after the disk-space scare
   resolved (see the note above the Headline)

**Rust suite** (`cargo test --lib --release -- --test-threads=1`, the
pyo3-linking `RUSTFLAGS`/`LD_LIBRARY_PATH` combination):

```
test result: ok. 778 passed; 0 failed; 4 ignored; 0 measured; 0 filtered out
```

**Byte-identical to the task brief's own cited baseline (778 passed)** —
zero new Rust-suite failures from this rung's 5 touched files.

**Named 9-file Python suite:**

```
3 failed, 241 passed
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

**Exactly the 3 known pre-existing pin-drift failures named in the task
brief — nothing new.** The nested nested-sweep detail inside those 3 tests
(10 failed / 427 passed / 2 skipped / 23 errors) matches the SAME
already-documented "shared mutable output path" fragility
`CEILING_REASSESSMENT_3_RESULTS.md` §6 and every subsequent rung in this
arc has re-confirmed present on clean `main` — not re-traced to its exact
mechanism again here, consistent with how every prior rung in this arc has
handled it.

---

## 6. GO/NO-GO

**Mixed, honestly reported, not smoothed into either a clean GO or a clean
NO-GO:**

- **GO on the primitive itself**: `ZipWith` is correctly designed, built,
  and verified (hand simulation, real-engine hand-built terms on
  revealed+held-out rows, real `SynthEnumerate` search calls) — a genuine,
  reusable capability addition matching this rung's own touch-point-cost
  discipline (1 new `TermNode`, ~230 lines across 6 files, in line with
  the `GroupCount`/`DictMerge` template once the template-pool cost
  `IndexedMap`-class ops carry is accounted for).
- **NULL on the MBPP battery gain**: 0/8 tasks convert, byte-identical
  76/75/101 before and after, root cause diagnosed and localized to
  pre-existing pipeline architecture (construction-lane precedence) and a
  budget shortfall under the real op inventory, neither of which this
  rung's own scope (a missing arithmetic Term) is positioned to fix.
- **CLEAN on regression discipline**: Rust suite 778 passed / 0 failed / 4
  ignored (byte-identical to the task brief's cited baseline); named
  9-file Python suite 241 passed / 3 failed, exactly the 3 known
  pre-existing pin-drift failures, nothing new. Both completed after a
  mid-rung disk-space scare resolved (see the note above the Headline) — re-checked `df -h /` before
  each run.

**State left in the worktree:** all Rust source changes + both docs
committed (see below); `results/mbpp_endgame.json` reflects the AFTER
state (byte-identical to before); `results/mbpp_endgame_BEFORE_this_rung.json`
preserved for the diff. Engine `.so` in `runners/dsl/python/substrate_rs/`
reflects the FINAL (IDiv/BitAnd/BitXor-fixed) build, matching the
provenance record (`_native.build.json`, `engine_sha256:
83b0dd8387ab1f41f683778b65c4ac499bb19ed189d079792183a923d31d914b`).

---

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-zip-elementwise
git log --oneline -1   # on top of main @ dbe67c6
```

Rebuild + full verification chain, exactly as run in this rung:
```bash
bash scripts/engine_build.sh
python3 -c "import sys; sys.path.insert(0, '.'); from domains.engine_provenance import record_build; print(record_build())"
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1   # 778 passed; 0 failed; 4 ignored
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q   # 241 passed; 3 failed (the 3 known pin-drift tests)
```

Isolated `ZipWith` search re-check (real engine, no explicit `ops`
override — the production typed-default path):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import json, substrate_rs as srs
from domains.mbpp_spec import parse_asserts, split_rows
s = srs.Substrate()
with open('tests/fixtures/mbpp/sanitized-mbpp.json') as f:
    tasks = {t['task_id']: t for t in json.load(f)}
for tid in [259, 261, 273, 282, 399, 401, 429, 445]:
    rows = split_rows(parse_asserts(tasks[tid])['rows'], 'primary')
    examples = [{'inputs': r['inputs'], 'output': r['expected']} for r in rows['revealed']]
    spec = {'type': 'SynthEnumerate', 'examples': {'type': 'Lit', 'value': examples},
            'max_size': 9, 'max_candidates': 200000, 'saturate_k': 0, 'field': ''}
    r = s._inner.evaluate(spec, {})
    print(tid, r['found'], r['tested'], r['halt_reason'], r['term_str'])
"
```
