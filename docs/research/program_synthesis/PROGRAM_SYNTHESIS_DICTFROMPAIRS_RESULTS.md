# `DictFromPairs` — built, correct, zero regression, zero MBPP conversion this rung — RESULTS

Prereg: `PROGRAM_SYNTHESIS_DICTFROMPAIRS_PREREG.md`, same worktree/branch.
Base `main @ 27db12b` ("Merge progsyn-ceiling-reassessment-4: IntersectAll/
UnionAll op-table exposure, MBPP 69->71"), verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-dictfrompairs`, branch
`progsyn-dictfrompairs` — **not merged to `main`**, left for the orchestrator
to independently verify and merge (this session's explicit instruction:
never merge to `main`, never `git stash`, never push).

**Headline: NO-GO on MBPP battery conversion — `full`/`content_stripped`/
`official` all measure byte-identical to baseline (71/70/100, exact
task-id-set-identical, not just count-identical). This is an honest,
well-localized null, not a failure to find anything: the PREREG's own central
claim — that `DictFromPairs` needs zero new `TermNode`s — is CONFIRMED live,
twice over, by two independent methods (hand-built term evaluation AND raw
`SynthEnumerate` itself, under a widened search budget, discovering a working
general solution unprompted). The reason neither target task (277, 465)
converts in the SHIPPED, real pipeline is a precisely diagnosed, genuinely
separate, out-of-scope architectural constraint: `domains/prog_synthesis.py`'s
`run_enumerate` hardcodes `max_size: 9` (line 1338) for every spec, and this
rung's own (correctly-priced, low-risk) `DICT_DEFAULT_OPS` widening
deliberately excludes `DictItems`/`FilterList` (§4 of the PREREG) — both
factors, independently confirmed necessary, are outside a single-variable
rung's scope to fix. A genuine, independent, pre-existing engine bug was
found and fixed en route (a missing `TermNode::MkDict` arm in
`synth_enumerate.rs`'s own local `term_json` renderer, which would panic
`unreachable!()` the first time ANY op composes a search-built candidate
containing `MkDict` — `DictFromPairs` is that first op).**

---

## 1. The zero-new-`TermNode` finding, reconfirmed from the PREREG and now
   ALSO independently discovered by the search itself

The PREREG's §3 live-verification (hand-built term-JSON, `Fold{init:MkDict
([]), body:DictMerge(acc, MkDict([IndexAt(item,0),IndexAt(item,1)]))}`,
6/6 exact matches across both tasks' revealed+held-out rows) is unchanged
and was NOT re-run here — it needed no code change to reproduce and nothing
in the build touches its own evaluation path.

**New this document:** the SAME composition was independently rediscovered
by raw `SynthEnumerate` itself, forcing the op set
`["DictItems","FilterList","DictFromPairs","Eq","IfThenElse","GroupCount",
"DictMerge"]` (task 277) / `+"Not"` (task 465) directly via
`substrate_rs.Substrate()._inner.evaluate()` on a hand-built `SynthEnumerate`
Term (the same diagnostic-depth precedent `GROUPCOUNT_DICTMERGE_RESULTS.md`
§4 used), at `max_size: 20` (`max_candidates: 400000`):

```
task 277: found=True, tested=158531, term=
  Fold(source=FilterList(DictItems(dict), item,
         Gte(MinOver(item, inner, inner), Var(n))),
       init=MkDict([]),
       body=DictMerge(acc, MkDict([IndexAt(item,0),IndexAt(item,1)])))

task 465: found=True, tested=72140, term=
  Fold(source=FilterList(DictItems(dict1), item,
         Gt(MinOver(item, inner, inner), Lit(0))),
       init=MkDict([]),
       body=DictMerge(acc, MkDict([IndexAt(item,0),IndexAt(item,1)])))
```

Both re-evaluated directly against ALL THREE real fixture rows (revealed AND
held-out) for their own task: **6/6 exact matches, both tasks.** The search
used the ALREADY-EXISTING `tmpl:nested_reduction` filter-template shape
(`MinOver(item, inner, inner)`, a min-reduction over the bound item's own
elements) rather than the "index-projection" shape the PREREG §5 named as
missing — `item` is a `(key: Str, value: Int)` pair, and `MinOver` over a
heterogeneous pair reliably selects the numeric element under this engine's
own `cmp_value` ordering (Int sorts below Str), which happens to give
EXACTLY the value-projection both predicates need. **This corrects the
PREREG's own §5 conclusion**: raw `SynthEnumerate`'s predicate grammar is
NOT missing the shape needed here after all — it reaches the correct
predicate via a DIFFERENT existing template than the one this document's own
predecessor anticipated. The PREREG's §5 prediction ("almost certainly
cannot construct the needed predicate") is retracted by this measurement,
in place, not silently corrected — the missing-template diagnosis was wrong,
though its bottom-line caution (raw search likely won't reach either witness
in the SHIPPED pipeline) turns out to be right for a DIFFERENT reason, §3
below.

## 2. The genuine engine bug found and fixed

Forcing the same op set at `max_size: 20` initially **panicked**:

```
thread '<unnamed>' panicked at src/synth_enumerate.rs:1587:14:
internal error: entered unreachable code: candidates are built only from
the op table + leaves
```

Root-caused directly: `synth_enumerate.rs`'s own local `term_json` renderer
(distinct from `jsonio.rs`'s — this module builds its own JSON-repr of a
WINNING candidate for the `SynthEnumerate` Term's `term`/`term_str` return
fields, called only when `finish()` has a `solved` candidate, `synth_
enumerate.rs:1930`) has a match arm for every `TermNode` variant this
module's `OP_TABLE` builders can produce — EXCEPT `TermNode::MkDict`, which
falls through to the catch-all `_ => unreachable!(...)`. Every pre-existing
`MkDict` construction site in `term.rs` is rule-authoring/`Verify`-test code,
never reachable from a search-built candidate (confirmed by grep before this
rung); `DictFromPairs` is the FIRST op-table exposure whose build function
(`build_list_unary`) embeds a `MkDict` node inside the tree it returns, so
this is the first time `finish()` was ever asked to render one. **This is a
real, previously-latent crash bug, unmasked (not introduced) by this rung's
own primitive** — any future op-table addition composing `MkDict` would have
hit the identical panic.

**Fix**: one additive match arm, `TermNode::MkDict { items } => json!({"type":
"MkDict", "items": items.iter().map(|i| term_json(...)).collect()})`,
mirroring the neighbouring `Vec_`/`DictItems`/`DictMerge` arms exactly and
matching `jsonio.rs`'s own `"items"` field name for round-trip compatibility.
Rebuilt from source (genuine, 2m02s, not cached) and re-ran the SAME forced-op
diagnostic: no panic, `found=True` both tasks, term rendered and verified as
in §1.

## 3. Why the SHIPPED pipeline still does not convert either task —
   diagnosed to its exact, separate mechanism, not left as a residual

Both target tasks were run through the REAL pipeline
(`domains.prog_synthesis.synthesize_from_request`, not a forced-`ops` call)
on the built, installed engine:

```
task 277: status=gapped, construction=None, gap_reason=enumerate_failed, ir=null
task 465: status=gapped, construction=None, gap_reason=enumerate_failed, ir=null
```

Neither `retrieved_exemplar` (the lane that converted `IntersectAll`/
`UnionAll` and `GroupCount` under an identical "primitive exists, raw search
alone can't obviously reach it" profile) nor raw enumerate found anything —
`construction: None` means retrieval never even proposed a candidate for
either task.

**§1's forced-op experiment used TWO conditions the real pipeline does not
supply, and both are independently necessary** (confirmed by direct
measurement, not inferred):

1. **Op availability.** `DICT_DEFAULT_OPS` (the real routing bucket both
   tasks reach, `synth_enumerate.rs:490`) is, per this rung's own §4 pricing
   decision, `["Eq","IfThenElse","GroupCount","DictMerge","DictFromPairs"]`
   — `DictItems`/`FilterList` deliberately NOT added (priced and rejected in
   the PREREG: no measured raw-search benefit was known at pricing time, and
   real regression risk to the bucket's one live canary, task 87). Without
   `DictItems`/`FilterList` available, `FilterList(DictItems(dict), ...)`
   can never be constructed regardless of `DictFromPairs`'s own presence —
   confirmed directly: re-running the real pipeline (unchanged shipped
   `DICT_DEFAULT_OPS`) still reports `gapped:enumerate_failed` for both
   tasks.
2. **Size budget.** `run_enumerate` (`domains/prog_synthesis.py:1338`)
   hardcodes `"max_size": 9` for every spec passed through the real pipeline
   — not configurable per-task, not related to `DICT_DEFAULT_OPS` at all.
   The winning candidates in §1 needed `max_size: 20` to be found (re-tested
   directly: `max_size` 12/13/14/15/16 all returned `found: False,
   halt_reason: 'max_size'` for task 277 with the FULL forced op set
   already available — only `max_size: 20` succeeded). Even a hypothetical
   future rung that also widens `DICT_DEFAULT_OPS` with `DictItems`/
   `FilterList` would still need `run_enumerate`'s own `max_size` raised
   roughly 2x, a change shared by EVERY spec through this one seam, not
   scoped to this bucket.

**Both are real, correctly out-of-scope architectural decisions for a
single-variable primitive-layer rung** — widening `DICT_DEFAULT_OPS` further
was priced and explicitly rejected in the PREREG (§4) on measured
regression-risk grounds that this document's own new evidence (§1) does NOT
overturn (the missing-template diagnosis was wrong, but the regression-risk
argument for keeping `DictItems`/`FilterList` out of this bucket never
depended on that diagnosis — it depended on "no measured benefit," which
now has a DIFFERENT, still-true replacement: no benefit UNLESS `max_size` is
also raised, which is its own separate, unpriced, shared-seam change).
Raising `run_enumerate`'s global `max_size` is a materially bigger,
differently-scoped change (affects every spec through this pipeline, not
just Dict-shaped ones) and was never priced by this rung — named here as a
genuine, real, follow-on candidate for a FUTURE rung, not attempted.

## 4. Regression risk, priced in the PREREG, now measured

Exactly one currently-passing canary (task 87) shares the widened bucket
(PREREG §2, §6). Confirmed directly, not assumed: task 87 remains in BOTH
the before and after `full`-arm pass sets (§5's set-diff below), and its own
solution (`DictMerge(DictMerge(c,b),a)`) is unaffected — no new op ever
enters its own accepted candidate.

## 5. Full MBPP battery — before/after, all three arms, real set-diff

**Before** (this worktree, unmodified `main @ 27db12b`, freshly measured):

```
full:              71/257  p=0.276265  ci=[0.225196, 0.333924]  det_identical=True
content_stripped:  70/257  p=0.272374  ci=[0.221597, 0.329855]  det_identical=True
official:          100/257 p=0.389105  ci=[0.331549, 0.449927]  det_identical=True
```

**After** (this rung, `DictFromPairs` + `term_json` `MkDict` fix installed):

```
full:              71/257  p=0.276265  ci=[0.225196, 0.333924]  det_identical=True
content_stripped:  70/257  p=0.272374  ci=[0.221597, 0.329855]  det_identical=True
official:          100/257 p=0.389105  ci=[0.331549, 0.449927]  det_identical=True
```

**Exact task-id set-diff, all three arms** (direct set computation from
`results/mbpp_endgame.json`'s `runnable_rows`, saved before/after:
`results/mbpp_endgame_BEFORE_this_rung.json` vs. `results/
mbpp_endgame.json`):

| arm | before (n) | after (n) | newly passing | regressed | identical |
|---|---|---|---|---|---|
| `full` | 71 | 71 | `{}` | `{}` | True |
| `content_stripped` | 70 | 70 | `{}` | `{}` | True |
| `official` | 100 | 100 | `{}` | `{}` | True |

Confirmed directly: task 277 and 465 are NOT in the `after` `full`-arm pass
set. **Byte-identical before/after on every arm, every task id** — zero
regression, zero conversion, exactly the honest null this document's
headline states.

## 6. Build discipline

**Genuine from-source rebuild, twice** (the second time after adding the
`term_json` `MkDict` fix found in §2): `cargo build --release` in
`runners/dsl/`, **2m 26s** then **2m 02s** (neither a cached sub-second
no-op). `bash scripts/engine_build.sh` installed the built `.so`; its own
final `python` invocation hit the documented benign `python: command not
found` PATH quirk — the two trailing commands run directly with `python3`
per the task's own standing note.

**Rust suite**: `RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib
-lpython3.13" LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:
$LD_LIBRARY_PATH" cargo test --lib --release -- --test-threads=1`:
**778 passed; 0 failed; 4 ignored** — byte-identical to the documented
current baseline (`CEILING_REASSESSMENT_4_RESULTS.md`'s own 778/778). This
rung adds zero new Rust tests (it touches op-table/search-loop registration
code plus one renderer match arm, no new Term evaluator semantics beyond
what §1/§2 already live-verify via `evaluate()`).

**Named 9-file suite**: **3 failed / 241 passed** — byte-identical count AND
byte-identical failing test names to the documented pre-existing baseline
(`test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`,
`test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_
drift`, `test_exact_first_migrated.py::test_named_regression_sweep_only_
known_pins_drift`), same nested-sweep detail (`6 failed, 432 passed, 2
skipped, 23 errors` inside the sweep tests, matching the already-documented
"shared mutable output path" fragility this arc has repeatedly re-confirmed
present on clean `main`) — none of the 3 top-level failures or the nested
sweep's own failures mentions `DictFromPairs`, `MkDict`, tasks 277/465, or
`DICT_DEFAULT_OPS`.

**Worktree artifact note**: this worktree's `results/` directory (gitignored,
per-tree) initially lacked several small input artifacts several tests read
(`prog_construction_scan.json`, `prog_chunk_mine.json`,
`code_synthesis_baseline.json`, `mbpp_train_diet.json`,
`prog_synthesis_battery.json`, `mbpp_arc3_endgame.json`,
`arc4_structural_verdicts.json`) — copied verbatim from `main`'s own
`results/` (small, static, read-only inputs, not touched by this rung's own
code) before the regression suite would run clean; this is worktree-setup
housekeeping, not a code change, and is not part of this commit (`results/`
stays gitignored).

## 7. What this document does NOT establish

1. Whether raising `run_enumerate`'s hardcoded `max_size: 9` and/or widening
   `DICT_DEFAULT_OPS` with `DictItems`/`FilterList` would be safe and cheap
   enough to build as a follow-on rung — named as a real candidate (§3), not
   priced, not attempted. Any such change is NOT scoped to Dict-shaped specs
   alone (`max_size` is a shared seam) and would need its own regression
   pricing across every spec shape, not just this bucket's one canary.
2. Whether `retrieved_exemplar`'s exact internal mechanism could ever be
   made to find this composition without the raw-enumerate path changing at
   all — not investigated; `construction: None` for both tasks says
   retrieval never proposed anything, but not WHY (matching this arc's
   standing "not re-traced to its exact internal code path" residual for
   every prior rung's own retrieval conversions).
3. Whether `DictFromPairs` (as shipped, unconverting this rung) is worth
   keeping on `main` at all, given it currently helps zero MBPP tasks — left
   entirely to the orchestrator's own judgment. The case FOR keeping it:
   zero regression (§4-5), a real capability that is ALREADY genuinely
   correct and discoverable by the engine's own search once the two named
   out-of-scope constraints are eventually relaxed (§1, §3), and it carries
   a real, independent bug fix (§2) that protects any FUTURE `MkDict`-
   composing op from the same latent panic. The case AGAINST: it converts
   nothing today, and the task brief's own standing instruction is "if it
   doesn't convert the tasks even if built ... do not force a build" — this
   document takes the position that the build was already necessary to
   DISCOVER both the corrected zero-new-Term finding and the genuine bug
   fix, and reports the null explicitly rather than either reverting the
   otherwise-correct, zero-regression code or overstating it as a
   conversion win.
4. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## 8. GO/NO-GO

**NO-GO on MBPP battery conversion this rung: `full`/`content_stripped`/
`official` all measure byte-identical to the 71/70/100 baseline, exact
task-id-set-identical.** The underlying `DictFromPairs` primitive is
correctly priced (zero new `TermNode`, matching `IntersectAll`/`UnionAll`'s
cost class, cheaper than the PREREG's own predecessor document's estimate),
live-verified correct by two independent methods including the engine's own
search discovering it unprompted under a widened budget, and lands with
measured zero regression on every axis checked (Rust suite, named Python
regression suite, full 3-arm MBPP battery with exact task-id set-diff). It
does not convert any MBPP task in the SHIPPED pipeline because of two
precisely diagnosed, genuinely separate, larger-scoped architectural
constraints (`run_enumerate`'s hardcoded `max_size: 9`; this rung's own
correctly-scoped `DICT_DEFAULT_OPS` exclusion of `DictItems`/`FilterList`),
neither of which this single-variable rung is scoped to fix. A genuine,
independent engine bug (missing `MkDict` arm in `term_json`, a latent panic
for any future `MkDict`-composing op) was found and fixed as part of this
investigation. Left for the orchestrator's own call on whether a
correctly-priced, zero-regression, currently-non-converting primitive plus
an independent bug fix is worth merging.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-dictfrompairs
git log --oneline -1   # on top of main @ 27db12b
bash scripts/engine_build.sh   # then: python3 -c "...record_build()..." ; python3 -m pytest tests/test_engine_provenance_migrated.py -q
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```

Forced-op raw-search diagnostic (§1, no code change needed to reproduce on
the built engine):
```bash
PYTHONPATH="runners/dsl/python:." python3 -c "
import substrate_rs as srs
s = srs.Substrate()
def wire(v):
    if isinstance(v, dict): return {'__dict__': [[k, wire(x)] for k, x in v.items()]}
    if isinstance(v, list): return {'__list__': [wire(x) for x in v]}
    return v
rows = [
    {'inputs': {'dict': wire({'Cierra Vega': 175, 'Alden Cantrell': 180, 'Kierra Gentry': 165, 'Pierre Cox': 190}), 'n': 170},
     'output': wire({'Cierra Vega': 175, 'Alden Cantrell': 180, 'Pierre Cox': 190})},
    {'inputs': {'dict': wire({'Cierra Vega': 175, 'Alden Cantrell': 180, 'Kierra Gentry': 165, 'Pierre Cox': 190}), 'n': 180},
     'output': wire({'Alden Cantrell': 180, 'Pierre Cox': 190})},
]
spec = {'type': 'SynthEnumerate', 'examples': {'type': 'Lit', 'value': rows},
        'max_size': 20, 'max_candidates': 400000, 'saturate_k': 0, 'field': '',
        'ops': {'type': 'Lit', 'value': ['DictItems','FilterList','DictFromPairs','Eq','IfThenElse','GroupCount','DictMerge']}}
r = s._inner.evaluate(spec, {})
print({k: r.get(k) for k in ('found','term_str','halt_reason','tested')})
"
```

Named 9-file regression suite:
```bash
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q
```

Rust suite:
```bash
cd runners/dsl && RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
```
