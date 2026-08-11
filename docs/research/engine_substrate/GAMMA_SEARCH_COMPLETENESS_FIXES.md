# Γ search-completeness fixes — Bug 1 (label bias) and Bug 2 (beam completeness)

**Status: TWO CONCRETE FIXES LANDED, worktree-isolated, uncommitted to `main`.**
This is the fix rung for the two named, already-diagnosed bugs in
`GAMMA_SEARCH_COMPLETENESS_CEILING.md` §2 (Probe 2, the `weighted.py`
label-bias gap) and §3 (Probe 3, the composer's beam-completeness gap).
Per that document's own scoping, this rung does NOT touch the Γ
admit/retract design work (`docs/research/adventure_mechanics/`) and does
NOT attempt a from-scratch best-first/admissible-heuristic rewrite of the
composer (option 3 of that document's §3.4 — no admissible heuristic over
partial covering-plans exists in this codebase, and inventing one was
explicitly out of scope). Both fixes follow the SAME shape: keep the
existing correct pattern where it's already correct, and replace the ONE
place found to be wrong with a cited, in-repo, already-working precedent
(`domains/fovea_bridge.py` for Bug 1; `synth_enumerate.rs` for Bug 2).

**Engine provenance.** `main`'s tip verified at the start of this rung:
`74baaea` (git log). Worktree: `/home/matt/ocelot-gamma-fixes`, branch
`gamma-completeness-fixes`, detached from `74baaea`.

| build | sha256 | matches |
|---|---|---|
| `main`@`74baaea`, unmodified source, freshly rebuilt (`scripts/engine_build.sh`) | `953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85` | byte-identical to the COMMITTED `.so` at `74baaea` — confirms the toolchain reproduces the shipped binary exactly, so every "vanilla"/"before" measurement below used the real `main` engine, not an approximation |
| this rung's fix, `runners/dsl/src/{term,jsonio,reflect,shape_decode}.rs` + `substrate/weighted.py` edited, rebuilt | `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567` | the engine every "after" measurement below used |

Toolchain: `~/.cargo/bin/rustc 1.97.1` (rustup; NOT the `/home/linuxbrew`
1.87.0 that resolves first on `$PATH` by default — `PATH="/home/matt/.cargo/bin:$PATH"`
was set for every build in this rung). `cargo test --release --lib` needed
`RUSTFLAGS="-C link-arg=-lpython3.13 -C link-arg=-L/home/linuxbrew/.linuxbrew/opt/python@3.13/lib"`
+ `LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH"`
at both link and run time (the box's Python is 3.13.5 via Homebrew, not
3.14 as `PROGRAM_SYNTHESIS_P4A_NOTES.md`'s own build note assumed for its
box — the *shape* of the fix, "point the linker/loader at the real
`libpythonX.Y.so`," is the same precedent, the version number differs).
`cargo build --release` (the actual `.so` build, via `scripts/engine_build.sh`)
needed neither — the `cdylib` resolves Python symbols at `dlopen` time, only
the standalone test-binary linker needs them resolved eagerly.

Coherence probe (`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back
`[1, 2, 3]` (`list`) and `(1, 2, 3)` (`tuple`) distinctly) passed on both
builds.

`results/` (21G, gitignored) and `data/` (39G, gitignored) were hardlinked
(`cp -al`, same filesystem, near-instant, zero extra disk) from the
canonical tree into the worktree — several migrated-test gates read fixed
artifacts under those paths by relative path, and a fresh `git worktree add`
does not populate untracked directories. This is read/reference data only;
nothing under either path was written back to the canonical tree from the
worktree (`git status --porcelain` checked clean in the canonical tree's
`results/`/`seeds/` throughout — see §5).

---

## Bug 1 — `substrate/weighted.py`'s `weighted_walk`, label bias

### Diagnosis recap (from the ceiling-probe doc, not re-derived here)

Γ's `weight` field is a log-domain quantity (`selection ∝ exp(w)`,
`grammar.rs` header); `checker.rs`'s `evaluate_weight`/`admissible_moves`
already sum RAW, un-normalized `w` additively for one choice point, never
normalizing (the doc's Probe 2, §2.1-§2.2). `domains/fovea_bridge.py`'s
`fovea_resolve` composes this way for exactly one decision
(`ArgminUnique(Neg(Log(salience)+goal_logweight))`, an additive sum of two
raw log quantities). The one existing MULTI-HOP consumer,
`substrate/weighted.py`'s `weighted_walk`, instead runs a per-step LOCALLY
renormalized categorical draw (`rng.choices(keys, weights=weights, k=1)`)
— the CRF *label bias* shape (Lafferty/McCallum/Pereira 2001): composing
local per-step probabilities across hops is structurally biased by each
node's branching factor, independent of how good the alternatives actually
were.

### What this rung found on closer reading, and why the fix is additive, not corrective-in-place

`weighted_walk` has exactly one production caller inside this repo: its own
test (`tests/test_substrate.py::test_weighted_walker_respects_existing_edges`,
grepped exhaustively, `grep -rn weighted_walk` over every `.py`/`.rs`/`.json`
in the tree — no other consumer exists, in seeds, domains, or scripts). It
is exported from `substrate/__init__.py`'s public surface but nothing in
the graph-native agent's runtime calls it.

Re-reading the function against the label-bias diagnosis precisely: the
per-step `rng.choices(...)` draw is **not itself wrong** — `weighted_walk`'s
actual job (its own docstring, and `docs/meta/SPEC.md:61`'s "Theorem D
weighted-traversal SAMPLER") is an honest stochastic coverage/visitation
sampler, and per-step-proportional sampling is the CORRECT way to draw the
next step of a random walk; a categorical draw cannot avoid local
normalization (you cannot sample from un-normalized weights — normalizing
at the point of sampling is what makes it a valid probability
distribution). The bug the ceiling-probe doc names is narrower and more
precise than "the sampler is broken": **this file was the only precedent
in the repo for "composing Gamma weight across hops," and its shape is the
wrong one to copy** if anyone later builds a best-path/comparable-path-score
consumer over Γ. The function computed no path score at all before this
fix — there was nothing to "fix" in the sense of correcting a wrong
formula, because the wrong formula didn't exist yet; the actual gap is an
ABSENCE of the right template next to the wrong one.

The fix: `weighted_walk` keeps its stochastic step-selection completely
unchanged (still the correct locally-normalized draw), and gains a new,
correctly-composed, read-only field — `WalkResult.path_logweights`, one
entry per walk, `sum(log(w_i))` over the RAW `weight_fn` values of the hops
actually taken (the Carré 1971 / Mohri 2002 semiring-valid composition,
`fovea_bridge.py`'s shape, generalized from one hop to a path). This gives
a future best-path consumer the RIGHT quantity sitting right next to the
sampler, instead of only the wrong-shaped template.

### The discriminating test

`tests/test_substrate.py::test_weighted_walk_path_logweight_is_label_bias_free`
(new). Construction: two graphs, IDENTICAL raw weight (8.0) on "the same"
edge, differing ONLY in branching factor at the fork — `lo_s` has one
outgoing edge (branching 1); `hi_s` has the identical weight-8.0 edge plus
two weight-1.0 distractor siblings (branching 3). 200 walks each,
`walk_length=1`, same seed.

| quantity | low-branching (`lo_s`) | high-branching (`hi_s`) | equal? |
|---|---|---|---|
| `path_logweights` entry when the weight-8.0 edge is taken (THE FIX) | `log(8.0) = 2.0794...` | `log(8.0) = 2.0794...` | **YES — exactly, by construction** |
| hypothetical OLD-style local-probability composition for the SAME realised hop (computed in the test for contrast, NOT produced by `weighted_walk` any more) | `log(8.0/8.0) = log(1.0) = 0.0` | `log(8.0/(8.0+1.0+1.0)) = log(0.8) ≈ -0.223` | **NO — label-biased, more negative for the busier fork despite an identical raw weight taken** |

Both assertions are live in the test: `hi_hits[0] == pytest.approx(lo_hits[0])`
(the fix is branching-factor invariant) and
`old_style_local_logprob_hi < old_style_local_logprob_lo` (the discarded
shape would NOT have been invariant — it is strictly worse for the busier
fork, exactly the CRF prediction). `pytest tests/test_substrate.py` — 18
passed (was 17 before this test was added; every existing test, including
the ORIGINAL `test_weighted_walker_respects_existing_edges`, is
byte-unchanged in behaviour).

### Caller-threshold audit

Per the task brief's own concern ("if a caller was implicitly relying on
the locally-normalized score as a probability-like [0,1] quantity for a
fixed-threshold comparison, the fix could change scale under it"): moot —
`weighted_walk` never returned any composed score before this change
(only `visits`/`terminated_at`, both untouched), so there is no existing
threshold comparison anywhere in the tree to audit or fix. `grep -rn
weighted_walk` confirms the only caller is the test above, itself
unaffected (asserts only `.visits`, never `.path_logweights`, until the
new test explicitly opts in).

---

## Bug 2 — the composer's beam-search completeness gap

### Diagnosis recap

`eval_shape_decode` (`runners/dsl/src/shape_decode.rs`) is the composer's
whole beam search (`domains/reflective_faculty.py::compose_design_for_goal`
is a thin shim that builds the Term JSON and evaluates it once). Verified
line numbers on THIS rung's starting commit (`74baaea`; the ceiling-probe
doc's own corrected pointer, `~1202-1369`, matched closely but had drifted
slightly further by this rung — re-verified fresh rather than trusted):
`struct BeamState` at `1016-1024`; `eval_shape_decode` spans `1202-1369`;
the per-state candidate cap (`.take(cand_w)`) at `1286`; the cross-state
width prune (`if pruned.len() >= beam_w { break; }`, after a
`sort_by((coverage DESC, total_fit DESC))`) at `1319-1336`. Two independent
truncation points existed; `scripts/probe_beam_completeness.py`
(pre-existing, read not rewritten this rung) exercises the width-prune one.

The construction (Johnson 1974 greedy-set-cover shape, miniaturized):
`part_A={g1,g2}` + `part_B={g3,g4}` is the OPTIMAL, disjoint, 2-part,
fully-covering plan; `part_C={g1,g3}` ties `part_A`/`part_B` on coverage at
step 1 and wins the `shape_fit` tie-break by construction, then needs 2
MORE single-relation parts to finish — impossible at `max_steps=2`. A
width-1 beam keeps only `part_C`'s (dead-end) state after step 1;
`part_A`/`part_B`'s states — which WOULD have combined into the optimal
plan on step 2 — are discarded permanently (a `BeamState` that misses the
top-`beam_w` cut never re-enters `frontier`).

### The fix

Following `synth_enumerate.rs`'s already-shipped precedent for the sibling
program-synthesis enumerator (`PROGRAM_SYNTHESIS_P4A_NOTES.md`: `"beam
(legacy unguided width cap) — NO, dropped — dead weight the guided path
superseded"`, replaced by exhaustive, size/MDL-ordered, count-budgeted
search): the fixed-width cross-state prune is REPLACED, not merely
widened, by a total-expansion BUDGET (the `ProgEval`-fuel /
`SynthEnumerate`-`max_candidates` idiom):

- The `(coverage DESC, total_fit DESC)` sort and the `(residual,
  used-set)`-keyed dedup are UNCHANGED — every deduped candidate state now
  survives to the next round (no `if pruned.len() >= beam_w { break; }`),
  still cost-ordered best-first.
- A running counter (`expansions`) increments once per candidate STATE
  created (one unit per `(state, part)` pairing that survives the
  unchanged per-state `cand_w` cap); when it would exceed a budget
  (`sd_budget`, `<=0` on the wire → `DEFAULT_SD_BUDGET = 20_000`), the
  search stops generating new candidates and returns its best-so-far —
  honestly.
- New output field `budget_exhausted: bool` — `true` iff the budget cut the
  search short before it would otherwise have stopped (frontier naturally
  empty, or full coverage reached). `authored` (pre-existing) never meant
  "certified complete" before or after this fix (it was already `true` on
  the OLD engine's incomplete `beam=1` result) — `budget_exhausted` is the
  new, additive honesty signal the task asked for: a caller can now tell
  "as good as this search gets" from "gave up partway, here's the best
  partial."
- `beam` stays on the wire (every existing `seeds/*.json` call site parses
  unchanged) and in the output Dict (informational/back-compat) but no
  longer truncates anything.
- New optional Term field `budget` (default 0 → the constant above),
  threaded through `term.rs` (struct + `copy_subtree` + eval dispatch +
  cache key), `jsonio.rs` (emit + parse, `unwrap_or(0)`), and `reflect.rs`
  (decompose + reconstruct, `get_int` already treats an absent attr as 0 —
  no special-casing needed for old persisted term-subgraphs).
  `reflective_faculty.py::compose_design_for_goal` gained a pass-through
  `budget: int = 0` kwarg.

### Why `DEFAULT_SD_BUDGET = 20_000`

The two production shapes found in `seeds/*.json` (`grep`-verified across
every seed file containing `"type": "ShapeDecode"`) are `cand_k<=1`
(single-step real-time callers) and `cand_k∈{2,3}, max_steps=8`
(`reflective_faculty`'s composer default; `shape_decode_loop.json`,
`reflex_net.json`, `program_synthesis.json`, `meaning_inference.json`,
`prog_construction_loop.json`). The exhaustive worst case for the latter
(`sum_{k=1..8} cand_k^k`, no dedup benefit) is 510 (`cand_k=2`) or 9840
(`cand_k=3`) total expansions — 20,000 gives that class room to run to
GENUINE exhaustion with slack, while still bounding a much larger
caller-supplied `cand_k`/`max_steps` to an honest `budget_exhausted`
result. `domains/*.py` also builds `ShapeDecode` Terms directly (not only
via the shim); one call site (`domains/predictive_reading.py`) sets
`max_steps=len(goal)+2, cand_k=max(8, len(goal)+1)` — GOAL-SIZE-DEPENDENT,
unbounded in principle for a large goal. This is a named residual, not
silently absorbed — see §4 below.

### The discriminating test — Rust, gated at the same layer as the bug

`runners/dsl/src/shape_decode.rs`, `mod tests`, four new `#[test]`s built
on the exact `scripts/probe_beam_completeness.py` construction
transplanted verbatim (`build_beam_trap`):

| test | what it shows |
|---|---|
| `beam1_no_longer_loses_the_optimal_plan` | `beam=1, max_steps=2, cand_k=5`: `covered_count == 4` (full), `residual == []`, `budget_exhausted == false`. Before the fix this same call returns `covered_count == 3`, `residual == [g2]` (the doc's own live-verified §3.3 number) — the discriminating delta. |
| `beam3_still_finds_the_optimal_plan` | Sanity twin: `beam=3` (already-complete pre-fix) is unchanged — same optimal plan. |
| `starved_budget_is_flagged_honestly` | `budget=1`: still returns a result (no panic/hang), `budget_exhausted == true`, `authored == true` (the one candidate the budget allowed is still reported, not discarded). |
| `mid_search_budget_exhaustion_is_flagged` | `budget=3` (exactly the 3 step-1 candidates, none has spawned a step-2 child yet): `budget_exhausted == true`, `covered_count == 2` — proves the flag reflects genuine exhaustion state, not merely "budget looks small." |

`target/release/deps/substrate_rs-* shape_decode::tests` — **12 passed, 0
failed** (the 4 new + the 8 pre-existing `mod tests` cases, including
`parity_hand_computed_example` and `greedy_degenerate_beam1_cand1_matches`,
BYTE-UNCHANGED — the 3-part/4-relation hand-traced fixture never needed the
width prune to find its answer, so it is an honest zero-diff control).

**Python-level, end-to-end confirmation** — `scripts/probe_beam_completeness.py`
(pre-existing, unmodified) run against the fixed engine:

```
beam=1:  ordered_parts=[part_A, part_B]   covered=4/4  residual=[]   total_fit=7
beam=2:  ordered_parts=[part_A, part_B]   covered=4/4  residual=[]   total_fit=7
beam=3:  ordered_parts=[part_A, part_B]   covered=4/4  residual=[]   total_fit=7
```

(BEFORE, `GAMMA_SEARCH_COMPLETENESS_CEILING.md` §3.3, live-verified on
`main`@`74baaea`: `beam=1` → `ordered_parts=[part_C, part_B-or-part_only4]`,
`covered=3/4`, `residual=[g2]`, `"authored": true` — indistinguishable from
a certified result.) The probe script's own pass/fail line now reads "NOT
REPRODUCED... beam width did not change the outcome" — its designed
success signal was DIVERGENCE across beam widths (the bug), so this exit
code correctly flips once the divergence is fixed; the JSON block above is
the actual evidence, not the script's own verdict line.

### Honest cost measurement

`compose_design_for_goal(..., beam=3, max_steps=8, cand_k=3)` (the real
production default) on a synthetic, moderately-organic codebook (20
disjoint 2-relation "real" parts forming the exact cover of a 40-relation
goal, plus decoy single-relation parts drawn from the same relation pool —
approximating an organically-grown codebook's noise, not a no-op;
`N_REPEATS` runs per point, fresh `boot_core()` each run, wall-clock via
`time.perf_counter()`):

| codebook size | OLD engine (`953b8e3f`) median | NEW engine (`c5e50801`) median | Δ absolute | Δ relative | both find `covered_count` |
|---|---|---|---|---|---|
| 170 parts (150 decoys) | 4.38 ms | 20.20 ms | +15.8 ms | **4.6×** | 16/40 (identical — bounded by `max_steps=8 × 2 rel/part`, not by the fix) |
| 520 parts (500 decoys) | 12.25 ms | 58.01 ms | +45.8 ms | **4.7×** | 16/40 (identical) |

Both scales report `budget_exhausted: false` on the new engine (well under
the 20,000-expansion default) — the extra time is genuinely "exploring
more of the search space that was previously discarded," not budget-cap
churn. The ratio (~4.6-4.7×) is consistent across a 3× codebook-size
range, i.e. this looks like a real, roughly-constant multiplicative
overhead from "keep the discarded branches instead of dropping them,"
not a blow-up that gets worse with scale in this regime — but this was
only measured up to 520 parts / 40-relation goals; no claim is made about
codebooks an order of magnitude larger.

**The `cand_k<=1` real-time callers are unaffected, analytically and
empirically.** Analytically: `best` is updated at candidate-CREATION time
(inside the same loop that scores/spawns children), BEFORE any pruning
ever runs — for `max_steps=1` there is no second round for pruning to
matter in, regardless of what `beam` used to discard. Empirically: every
`seeds/*.json` file using `beam=1, max_steps=1, cand_k<=1` (the real-time
shape — `embodied_motor_bootstrap.json`, `humanoid_adaptation.json` ×12,
`vision_verdict_comparator.json`, `vision_invariant_comparator.json`,
`vision_crossframe_identity.json`, `somatomotor_waves.json`,
`embodied_physics_proposal.json`, `embodied_development.json`) has its
corresponding migrated test file green post-fix (§5) — including
`test_humanoid_adaptation_migrated.py`'s `~100`-second live-execution
suite, unaffected in wall-clock or outcome.

**Named residual, not silently absorbed:** `domains/predictive_reading.py`
constructs a `ShapeDecode` Term with `max_steps=len(goal)+2,
cand_k=max(8, len(goal)+1)` — goal-size-DEPENDENT, so a sufficiently large
goal COULD approach or exceed the 20,000-expansion default budget where the
old fixed `beam=2` never would have (it always did O(beam×cand_k×max_steps)
work, bounded regardless of goal size, at the cost of the exact
completeness bug this rung fixes). `tests/test_predictive_reading.py` could
not be run this rung — collection fails on `ModuleNotFoundError: No module
named 'pyarrow'` (a pre-existing, environment-level optional-dependency gap
unrelated to this change: `python3 -c "import pyarrow"` fails standalone,
`pip install pyarrow` refuses under this box's externally-managed-Python
guard, and installing it was judged out of scope / too invasive for this
rung to force). This is an honest, unverified-not-hidden gap: this
specific caller's behaviour under the new budget regime was not directly
measured. It is very unlikely to be WORSE than before (worst case it now
honestly reports `budget_exhausted: true` on a goal so large the old code
also could not have covered it — completeness was never claimed for that
caller either way), but "not measured" is stated plainly rather than
assumed benign.

---

## Regression results

Paired list, not a bare count, per this repo's own "baseline must be a
list of node ids" rule (`results/failure_baseline.json`'s convention).
`condition`: no `data/`/`results/` symlink (hardlinked copies, see engine
provenance section), `chess` not installed, `pyarrow` not installed — both
pre-existing environment gaps, confirmed absent regardless of this rung's
changes.

### Rust — `cargo test --release --lib` (full suite)

| | before (vanilla `74baaea`, confirmed via `git stash`) | after (this rung's fix) |
|---|---|---|
| default (unspecified) thread count | 730 passed, **3 failed** (`shape_decode::dim_infer_tests::{d_codebook_growth_is_seen_by_the_encoder, d_green_different_goals_are_seven_distinct, d_red_identical_arguments_collapse_to_one}`) | 730 passed, **3 failed** (SAME three node ids) |
| `--test-threads=1` | 733 passed, 0 failed | 733 passed, 0 failed |
| `--test-threads=4` | not measured (see below) | **737 passed, 0 failed, 4 ignored** |

The 3 default-thread-count failures are a **pre-existing, unrelated,
parallel-test-isolation hazard**, not a regression: `d_*`'s own assertion
message ("the recording site must see every invocation") is a shared
GLOBAL `scale_audit` invocation counter racing against unrelated
concurrently-running tests; none of this rung's edits touch
`scale_audit`/`term_units` call sites (only `shape_fit`/`covers_relation`,
UNCHANGED functions, call them). Confirmed directly: `git stash` (reverting
to vanilla `74baaea` source), rebuild (byte-identical sha256
`953b8e3f...`), same 3 tests fail the SAME way under default threading and
pass clean under `--test-threads=1` — reproduced on the UNMODIFIED engine,
before this rung touched anything. `--test-threads=4` (a value this rung
happened to pick for its own full-suite run) came up clean at 737/0/4 —
consistent with a genuine race (thread-count-and-scheduling-sensitive), not
a deterministic failure.

`shape_decode::tests` (the 8 pre-existing composer cases + 4 new): **12
passed, 0 failed**, `--test-threads` irrelevant (no shared global state).

### Python — `pytest`, `--confcutdir=. PYTHONPATH=runners/dsl/python:.:scripts`

| suite | before (`74baaea`, same environment/condition) | after |
|---|---|---|
| `tests/test_substrate.py` | 17 passed | **18 passed** (+1, the new Bug-1 discriminating test) |
| `tests/test_arc_executor_migrated.py` | 103 passed, 1 failed (`test_ex1_the_frozen_artifacts_are_STILL_byte_identical` — `git show HEAD:results/arc6_verdict_before.json` empty; `results/` is gitignored, never committed, independent of engine or this rung) | SAME: 1 failed (same node id), rest passed |
| `tests/test_goal_residual_migrated.py::test_gr4_the_live_mbpp_pass_ids_are_unchanged` | **failed** — engine-provenance allowlist (`8311d4356082`/`4a9a492936bb`/`39c4dbb7f2ed`) does not include ANY engine built from `74baaea`'s current source (`953b8e3f...`), regardless of this rung's changes | SAME: failed, same reason (now doesn't include `c5e50801...` either, for the identical pre-existing reason) |
| `tests/test_composer_driver_migrated.py` | 5 passed, 2 failed (`test_ground_concern_dispatch_parity`, `test_question_driver_parity` — a captured `driver.json`/`ground_concern.json` fixture stale relative to the CURRENT seed set's rule count, `rule_count_before/after` 20→134 in the diff this rung inspected then discarded, unrelated to Bug 1/2; `test_question_driver_parity`'s `know` step is additionally a ~62s live network-dependent step whose content visibly drifts run to run) | 6 passed (**+1**: `test_shape_decode_composer_parity` now passes — see below), 2 failed (SAME two node ids, confirmed reproduced independently on vanilla `74baaea` too, in this environment, before any of this rung's edits) |
| `tests/test_arc_goals_migrated.py`, `tests/test_arc6_valuelayer_migrated.py`, `tests/test_arc_magnitude_migrated.py`, `tests/test_transform_decode_migrated.py`, `tests/test_dimension_inference_migrated.py`, `tests/test_engine_provenance_migrated.py` | all green | all green, unchanged |
| **Combined target slice (10 files)** | 4 failed (listed above), rest passed | **4 failed — SAME 4 node ids**, 259 passed (was 252 for the same 9-of-10 files; +7 from adding `test_engine_provenance_migrated.py` to this final run, +1 from the new substrate test) |
| `tests/test_humanoid_adaptation_migrated.py`, `test_embodied_motor_bootstrap_migrated.py`, `test_reflex_net_migrated.py`, `test_embodied_physics_proposal_migrated.py`, `test_embodied_development_migrated.py`, `test_somatomotor_waves_migrated.py`, `test_prog_constructions_migrated.py` (every seed-file caller of `ShapeDecode` with a runnable migrated test, per `grep "type.*ShapeDecode" seeds/*.json`) | not separately re-run against vanilla this rung (analytically + previously known green) | **105 passed, 7 skipped, 0 failed** |
| `tests/test_ink_decode_migrated.py`, `tests/test_modality_reflex_migrated.py` (two more `ShapeDecode` Python-constructor call sites, `beam=1/max_steps=1` and `beam=3/max_steps=steps` respectively) | not separately re-run | **36 passed, 0 failed** |

**Blocked by pre-existing environment gaps, not run this rung (neither
before nor after):** `tests/test_discourse_coherence.py`,
`tests/test_narrative_structure.py`, `tests/test_predictive_reading.py`,
`tests/test_throughlines.py`, `tests/test_trope_theme.py`,
`tests/test_meaning_inference_migrated.py` — all fail Python IMPORT at
collection time on `ModuleNotFoundError: No module named 'pyarrow'`
(`domains/wiki_library.py:28`, three import-hops deep from
`domains.dictionary_lexicon`), confirmed via a bare `python3 -c "import
pyarrow"` that this is an environment-level absence, not code touched by
this rung. `pip install pyarrow` refuses (`externally-managed-environment`,
PEP 668) without `--break-system-packages`, which was judged too invasive
to force on a shared box for this rung's scope. This is the SAME class of
gap the retracted `CLAUDE.md` "optional-dep note" documents for `chess`
(collection error, not an assertion failure — disjoint population, per that
note's own finding) — named here rather than silently worked around, per
that note's own standing rule.

**`test_humanoid_adaptation_migrated.py::test_graph_learns_full_humanoid_and_survives_matched_impulse`**
— `HUMANOID_DECOMPOSITION_CONTINUATION.md` (an earlier point in this
session, dated before this rung) recorded this as a pre-existing red
(`first_fall_action 326`) NOT caused by that rung's own work. This rung's
run of the full file (105/105 passed within that file's slice) shows it
GREEN now — either fixed by intervening commits before `74baaea`, or
flaky/order-dependent. Reported plainly rather than silently reconciled:
this rung did not investigate which.

---

## What broke / remaining uncertainties (numbered, honest)

1. **Bug 2's cost is real, not free** (~4.6-4.7× on a synthetic
   170-520-part codebook at the production default `beam=3, max_steps=8,
   cand_k=3`) — this is the expected, named tradeoff (§3.4 option 2 in the
   ceiling-probe doc: "not free... a real rewrite"), measured rather than
   assumed. It is a composer-path cost, not a real-time-control-loop cost
   (every `cand_k<=1` config, which is what F-16/humanoid/vision hot loops
   actually use, is provably and empirically unaffected).
2. **`domains/predictive_reading.py`'s goal-size-dependent
   `max_steps`/`cand_k`** could not be regression-tested this rung
   (`pyarrow` import gap, pre-existing, environment-level). Named as an
   honest unverified case, not assumed benign — see the Bug 2 write-up.
3. **`DEFAULT_SD_BUDGET = 20_000` is a reasoned constant, not a measured
   optimum.** It comfortably covers every discovered production `cand_k∈{1,2,3}`
   config with slack, but no organically-grown, real (not synthetic)
   large codebook was available to validate the constant against — the
   ceiling-probe doc's own §5 named "how often this bites organically-grown
   codebooks" as unmeasured, and that remains true for the fix's cost too.
4. **`test_ground_concern_dispatch_parity`/`test_question_driver_parity`'s
   underlying fixture staleness (rule count 20→134) was found and NOT
   fixed** — it is unrelated to Bug 1/2 (confirmed: these same two tests
   fail identically on unmodified `74baaea`), and fixing it is out of this
   rung's scope (would mean re-capturing `ground_concern.json`/`driver.json`
   against a live, possibly-network-dependent run, a separate piece of
   work). `composer.json` WAS re-captured (see below) because that diff was
   clean and directly caused by this rung's own additive field.
5. **The Rust `dim_infer_tests` 3-test flakiness under default thread count
   is pre-existing** (reproduced on vanilla `74baaea`) and was not fixed —
   out of scope for this rung (a shared global `scale_audit` counter is not
   part of either named bug). Noted so a future rung doesn't have to
   re-diagnose it from scratch: it passes clean under `--test-threads=1`.
6. **`beam` is now informational-only** on `ShapeDecode` — every existing
   seed and Python call site keeps working (the wire field is still parsed
   and reported), but any code relying on `beam` actually bounding the
   search's cost (as opposed to `budget` now doing that) would be relying
   on stale behaviour. `grep`-audited across every `seeds/*.json` and
   `domains/*.py` `"type": "ShapeDecode"` site this rung could find; no
   caller was found treating `beam` as anything but "how many survivors,"
   which is exactly what changed.

---

## Files changed

| file | shape of the change |
|---|---|
| `substrate/weighted.py` | Additive: `WalkResult.path_logweights: list[float]`, computed alongside the UNCHANGED stochastic draw. Module/field docstrings cite `fovea_bridge.py`, Carré 1971, Mohri 2002, Lafferty/McCallum/Pereira 2001 as the fix's own reference implementation and the bug's own literature, per the task brief. |
| `tests/test_substrate.py` | +1 test: `test_weighted_walk_path_logweight_is_label_bias_free` (Bug 1's discriminating test, described above). |
| `runners/dsl/src/term.rs` | `TermNode::ShapeDecode` gains `budget: i64` (struct def + `copy_subtree` + eval dispatch + `sd_cache_key`'s scalar list, so caching is budget-aware). |
| `runners/dsl/src/jsonio.rs` | `ShapeDecode` emit/parse gain `budget` (`unwrap_or(0)` on parse — absent-in-JSON is the near-universal case across shipped seeds). |
| `runners/dsl/src/reflect.rs` | `ShapeDecode` term-subgraph decompose/reconstruct gain `budget` (`get_int` already treats an absent attr as 0 — no special-casing for old persisted subgraphs). |
| `runners/dsl/src/shape_decode.rs` | The actual fix: `DEFAULT_SD_BUDGET` constant + doc; `eval_shape_decode` gains a `budget: i64` parameter; the cross-state `if pruned.len() >= beam_w { break; }` width truncation is REMOVED (the sort+dedup that feeds it is UNCHANGED); a new `expansions`/`budget_exhausted` pair bounds total search work instead; output Dict gains `budget_exhausted: bool`. Plus: 4 new `#[test]`s (`beam1_no_longer_loses_the_optimal_plan`, `beam3_still_finds_the_optimal_plan`, `starved_budget_is_flagged_honestly`, `mid_search_budget_exhaustion_is_flagged`) and one test-helper (`build_decode_term_budgeted`); the pre-existing `build_decode_term` test helper gained a hardcoded `budget: 0` field (needed to keep compiling, no behaviour change for its callers). |
| `domains/reflective_faculty.py` | `compose_design_for_goal` gains a pass-through `budget: int = 0` kwarg, included in the `ShapeDecode` Term JSON unconditionally (0 → Rust default). Mechanical; no new decision. |
| `tests/fixtures/composer_driver_parity/composer.json` | Re-captured via the pre-existing `capture.py` (this rung wrote no new capture logic). Diff is EXACTLY four `"budget_exhausted": false` insertions, nothing else — verified via `git diff` before accepting. `ground_concern.json`/`driver.json`/`induce_concern.json` were ALSO regenerated by the same `capture.py` run, inspected, found to carry large UNRELATED staleness (a rule-count drift 20→134, `content_hash`/`revision`/`rule_uid` fields that didn't exist when those fixtures were last captured, and `induce_concern.json`'s only diff was a non-deterministic `axis_id` the test already masks) — and were REVERTED (`git checkout --`) rather than committed, per "fix only the two named bugs." |

`git diff --stat` over the above: 8 files, 476 insertions, 22 deletions
(excluding the binary `.so`, which is also modified in the worktree —
rebuilt via `scripts/engine_build.sh`, sha256 `c5e50801d48a...` as stamped
above).

---

## Reproduce

```bash
# From the canonical tree, verify main's tip and mint the isolated worktree:
git -C /home/matt/ozmadev/ocelot log --oneline -1 main   # 74baaea
git worktree add --detach /home/matt/ocelot-gamma-fixes 74baaea
cd /home/matt/ocelot-gamma-fixes && git checkout -b gamma-completeness-fixes

# Toolchain + engine (this box's rustup, not the homebrew rustc that
# resolves first on a bare $PATH):
export PATH="/home/matt/.cargo/bin:$PATH"
bash scripts/engine_build.sh          # -> sha256 c5e50801d48a...

# Coherence probe:
PYTHONPATH=runners/dsl/python:.:scripts python3 -c "
from substrate.boot_core import boot_core
s, ag = boot_core()
n = s.add_node('T', {'lst':[1,2,3], 'tup':(1,2,3)})
a = s.node(n)['attrs']
assert a['lst'] == [1,2,3] and isinstance(a['lst'], list)
assert a['tup'] == (1,2,3) and isinstance(a['tup'], tuple)
print('OK')"

# Bug 1, discriminating test:
PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest -q \
  tests/test_substrate.py -k weighted

# Bug 2, discriminating tests (Rust):
export RUSTFLAGS="-C link-arg=-lpython3.13 -C link-arg=-L/home/linuxbrew/.linuxbrew/opt/python@3.13/lib"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH"
(cd runners/dsl && cargo test --release --lib shape_decode::tests)

# Bug 2, end-to-end Python-level confirmation (pre-existing probe script,
# unmodified):
PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/probe_beam_completeness.py

# Broad regression slice:
PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest -q --confcutdir=. \
  tests/test_arc_executor_migrated.py tests/test_arc_goals_migrated.py \
  tests/test_goal_residual_migrated.py tests/test_arc6_valuelayer_migrated.py \
  tests/test_arc_magnitude_migrated.py tests/test_substrate.py \
  tests/test_transform_decode_migrated.py tests/test_composer_driver_migrated.py \
  tests/test_dimension_inference_migrated.py tests/test_engine_provenance_migrated.py
# expect: 4 pre-existing failures (test_ex1_the_frozen_artifacts_are_STILL_byte_identical,
# test_gr4_the_live_mbpp_pass_ids_are_unchanged, test_ground_concern_dispatch_parity,
# test_question_driver_parity), 259 passed, 1 skipped
```

---

## What a human reviewer should look at first

1. **`runners/dsl/src/shape_decode.rs`'s diff around the old `beam_w`
   truncation site** (the actual algorithmic change — the rest of the Rust
   diff is wiring a new optional parameter through four files
   mechanically).
2. **The honest-cost table** (§"Honest cost measurement" above) — is
   4.6-4.7× acceptable for the composer's real callers? This rung's own
   read is yes (no real-time caller uses `max_steps>1`), but that
   judgment is worth a second opinion.
3. **`tests/fixtures/composer_driver_parity/composer.json`'s diff** — should
   be exactly 4 lines (`"budget_exhausted": false` insertions); if it is
   not, something in this rung's Bug 2 change is not as purely-additive as
   claimed.
4. **The `domains/predictive_reading.py` residual** (§"What broke" #2) —
   whether it's worth installing `pyarrow` in a follow-up rung (or a
   dedicated CI environment) specifically to close this gap.
