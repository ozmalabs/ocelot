# Derived-operator tier — first buildable slice — RESULTS

Prereg: `DERIVED_OPERATOR_TIER_SLICE1_PREREG.md`, same worktree/branch. Parent
design: `DERIVED_OPERATOR_TIER_RESULTS.md`. Base `main @ a8cb4f5` ("Merge
oplist-admissibility-grammar-slice1: Γ-admissibility first slice for op-list
gating"), verified via `git log --oneline -1 main` immediately before creating
the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/derived-operator-tier-slice1`, branch
`derived-operator-tier-slice1` — **not merged to `main`**, left for the
orchestrator to review and merge.

**Headline: all three steps (§9 steps 1-3) built and gated GO.** `TermNode::
Call{name,args}` dispatches through a per-search `DerivedOpRegistry`; build-A's
five narrow fallback arms are wired; the `Total2` parity op (a registry-authored
re-expression of the shipped `Plus` op) is byte-identical to native `Plus` at
both the evaluation level and the full search level (size/tested/distinct/
pruned_equiv/halt_reason all equal). Bench: 774 → 778 (774 baseline + 4 new
tests, all green, zero regressions). MBPP battery: 69/68/98, task-ID sets and
every per-task outcome byte-identical to the pre-existing baseline artifact —
zero regressions, zero new passes, exactly as predicted (this rung's new code
paths are never exercised by the battery, since no task supplies `derived_ops`).

---

## 1. Design decisions this slice had to resolve that the parent doc left open

The parent doc's §3.2 pseudocode reads `ctx.derived_ops` directly, and its
§3.3 choice (b) rejects "a new `EvalCtx.derived_ops` field" **in the specific
sense of a PyO3-exposed, Python-facing field** (comparing against option (a),
which would mirror `derivations`' own never-wired-from-Python shape). It does
not, and could not, resolve a real Rust borrow-checker question the design
stage never had to hit: `EvalCtx<'a>` has ONE lifetime parameter shared by
every field. A `DerivedOpRegistry` built fresh *inside* `eval_synth_enumerate`
is a local, short-lived value — it structurally cannot satisfy `'a` (fixed by
whatever ancestor call constructed `ctx`, generally far outliving one
`SynthEnumerate` call). Splitting `EvalCtx` into two lifetime parameters would
break lifetime elision at every one of the ~19 files that write bare
`&mut EvalCtx` today — far outside this rung's budget.

**Resolution, implemented:** `EvalCtx` gained
`pub derived_ops: Option<std::sync::Arc<DerivedOpRegistry>>` — an `Arc`, not a
borrowed reference (matching the codebase's own `Value::Surface`'s use of
`Arc<[u8]>` for shared immutable data). `Arc` carries no borrowed lifetime, so
`EvalCtx<'a>` keeps its existing single lifetime parameter unchanged and
**zero other files needed to change** — confirmed: only `term.rs`,
`jsonio.rs`, `reflect.rs`, `term_variants.rs`, `synth_enumerate.rs` are
touched (§6). `eval_synth_enumerate` installs the registry via a small
`with_derived_ops` scope-guard helper (`ctx.derived_ops.take()` → run the
search closure → restore the previous value, `None` in every real case
today) so a stale registry can never leak to an unrelated `Call` node
evaluated later in the same `evaluate()` call tree — verified directly by
`derived_ops_registry_does_not_leak_past_the_call` (§4), which reuses ONE
`EvalCtx` instance across two `evaluate()` calls (a fresh `EvalCtx` would
trivially read `None` regardless of whether the guard works, so the test
deliberately does not construct a new one for its second check).

**The `derived_ops` argument's wire shape** is a list of Term-JSON
registry-entry strings — `{"name", "params":[{"name","pool"}], "extra_cost",
"template"}`, exactly the parent doc's §3.1 schema. Parsing is two-stage,
because `op_list` (which needs each entry's arity/pool shape to build an
`OpKind`) is constructed *before* `Search`/`search.scratch` exists — the arena
a template body must be parsed into (the `filter_templates_by_size`
precedent). Stage 1 (`parse_derived_op_meta`) reads only name/params/
extra_cost — no arena needed, run once per `derived_ops` list item. Stage 2
(`build_derived_op_registry`) parses each entry's `template` into
`search.scratch` once `search` exists, reusing `parse_excluded_term`'s
EXISTING local grammar unchanged, called with an EXTENDED `var_by_name` (spec
vars plus this entry's own params) — the literal sense in which this is "an
extension of `parse_excluded_term`'s existing local grammar" per the PREREG's
own framing: a new calling context, not a grammar rewrite. `Total2`'s own
template (`Plus{Var(a),Var(b)}`) needed zero new grammar support — `Plus`/`Var`
were already in `parse_excluded_term`'s vocabulary. A template referencing
ANOTHER derived op (`Call` inside a template) is NOT supported — out of scope,
no entry this slice registers needs it.

**Arity/pool → `OpKind` inference** (`derived_op_kind`, used only for the
explicit `ops` list — derived ops are never part of a typed default, like
`JoinListSep`'s own precedent): `[general]` → `Unary`, `[general,general]` →
`Binary`, `[general,general,general]` → `Ternary`, `[list]` → `ListUnary`,
`[list,list]` → `ListBinary`. Any other combination (including
`JoinListSep`'s own mixed `[list,general]` shape) is correctly refused — build
(B)'s job, not this slice's. Verified directly:
`mixed_pool_derived_op_is_silently_unusable_under_build_a` registers a
`Mixed{[list,general]}` entry, names it in `ops`, and confirms `found:false`
on a spec that would need genuine composition (two rows with different
outputs, neither reachable from a bare leaf) — the entry is silently dropped
from `op_list`, never an error, exactly the documented residual.

**Fallback-arm reachability, stated honestly:** `build_op`
(Unary/Binary/Ternary), `build_list_unary`, and `build_list_binary` are
reachable today. `build_list_ho` (`ListFilter`/`ListMap`) and
`build_indexed_map` (`IndexedMap`) also got a mechanical fallback arm per
step 2's literal five-function instruction, but per the parent doc's own
§3.1 ("the three template pools are NOT argument sources for a top-level
op"), no `op_list`-construction path this slice builds can route an
unrecognized name into those two `OpKind`s — those two fallback arms are
DEAD CODE under this slice's own registry-inference rules, added for literal
completeness, not because they are reachable. Documented in both files'
own doc comments, not left implicit.

**A gap the parent doc's pseudocode didn't surface, found and closed while
building:** a winning candidate can itself BE a `Call` node (the whole point
of build-A's fallback arms), but `synth_enumerate.rs`'s own LOCAL
`term_json`/`term_str` serializers (used for the winning candidate's output —
`jsonio.rs`'s generic serializer is deliberately NOT reused here, per the
module's own "Serialization is LOCAL" doc) had no `Call` arm before this
change — `term_json`'s catchall was `_ => unreachable!(...)`, which would have
PANICKED the moment a derived op actually won a search. Fixed: both
functions gained a `Call` arm (§6), and each derived op's own name/param
Syms are registered into the search's own `names: FxHashMap<Sym,String>`
output table (mirroring exactly how `__item`/`__acc`/every spec variable
already register there) so `Call`'s `name` field resolves through the SAME
local table every other Var/op name uses, never `Interner::resolve` directly
on a possibly-locally-fabricated Sym.

---

## 2. The parity-check derived op

**`Total2`** — Binary, general pool, template `Plus{items:[Var(a),Var(b)]}`,
`extra_cost:0`:

```json
{"name": "Total2",
 "params": [{"name": "a", "pool": "general"}, {"name": "b", "pool": "general"}],
 "extra_cost": 0,
 "template": {"type": "Plus", "items": [{"type": "Var", "name": "a"}, {"type": "Var", "name": "b"}]}}
```

Deliberately chosen as the cleanest possible isolation of dispatch-plumbing
correctness: it is not a novel composition, it is a registry-authored
re-expression of the ALREADY-SHIPPED, byte-for-byte-identical `Plus` op (the
existing op it mirrors). Two levels of parity, both verified directly:

1. **Evaluation parity** (`call_dispatches_to_registry_template_matching_
   native_plus`): `Call{"Total2",[3,4]}` evaluates to `Value::Int(7)`,
   identical to `Plus{items:[3,4]}` evaluated on the same arena/ctx. A
   `Call` to an unregistered name (`"Bogus"`) evaluates to `Value::None`,
   never a panic — the documented contract.
2. **Search parity** (`total2_derived_op_search_matches_native_plus_byte_for_
   byte`): a 4-row spec (`a+b`, non-trivially — no single leaf/auto-appended
   const can satisfy all four rows, forcing genuine composition) run with
   `ops:["Plus"]` (native) vs `ops:["Total2"]` (derived, via `derived_ops`)
   produces **identical** `found`, `size`, `tested`, `distinct`,
   `pruned_equiv`, `halt_reason` — the winning term differs ONLY in the outer
   node's own shape (`(x + y)` vs `Total2(x, y)`; `term` JSON differs in
   `"type"` only, `term_str` differs in surface form only). This holds
   analytically, not by luck: `OpKind::Binary`'s size accounting
   (`size = 1 + sa + sb`) is identical regardless of which `TermNode`
   `build_op` returns, and `Total2`'s template computes EXACTLY what `Plus`
   computes, so every candidate's observational-equivalence signature is
   identical between the two runs — same leaves, same op-list size (one op
   each), same dedup/registration sequence.

---

## 3. Files touched, and the line-count tally vs the ~60-100 line estimate

The parent doc's `§3.4` ~60-100-line estimate was scoped to `TermNode::Call`'s
OWN six touch points ALONE (enum variant, `evaluate()` arm, `copy_subtree`,
`children()`, `jsonio.rs`, `reflect.rs`) — priced against the `Reverse`/`Plus`
precedents. This slice's actual footprint is larger, for two honest reasons
not separately priced in that estimate: (a) `Call` needed NEW supporting
types (`DerivedOpDef`/`DerivedOpRegistry`/`DerivedOpPool`, the
`EvalCtx.derived_ops` field, `with_derived_ops`) that the `Reverse`/`Plus`
precedents never needed (they dispatch natively, no registry); (b) the
`SynthEnumerate` Term ALSO gained a new field (`derived_ops:
Option<TermIdx>`), which is its OWN six-touch-point change (enum field +
`copy_subtree` + `evaluate()`-arm passthrough + `children()` + `jsonio.rs` +
`reflect.rs`) bundled into the same file edits — not a single-variant change,
two bundled together.

| file | insertions | deletions | what |
|---|---|---|---|
| `runners/dsl/src/term.rs` | 132 | 4 | `Call` variant + doc; `SynthEnumerate.derived_ops` field + doc; `DerivedOpPool`/`DerivedOpDef`/`DerivedOpRegistry` types; `EvalCtx.derived_ops` field + doc; `EvalCtx::new` default; `copy_subtree` arms (`Call`, `SynthEnumerate`); `evaluate()` arms (`Call` dispatch, `SynthEnumerate` passthrough); `children()` arms |
| `runners/dsl/src/term_variants.rs` | 5 | 3 | mechanical regen (`tools/gen_term_variants.py`) — `NUM_TERM_VARIANTS` 228→229, `"Call"` added to the name table |
| `runners/dsl/src/jsonio.rs` | 12 | 1 | variant-name arm; write arm (`Call`, `SynthEnumerate.derived_ops`); read arm (same) |
| `runners/dsl/src/reflect.rs` | 11 | 1 | write arm (`Call`, `SynthEnumerate.derived_ops`); read arm (same) |
| `runners/dsl/src/synth_enumerate.rs` (core, non-test) | 278 | 27 | new `derived_ops_t` param; `DerivedOpMeta`/`parse_derived_op_meta`/`derived_op_kind`/`build_derived_op_registry`/`with_derived_ops`; stage-1/stage-2 parsing wired into `eval_synth_enumerate`; `names` table registration for derived-op Syms; `call_fallback` helper; five build-A fallback arms (`build_op`, `build_list_unary`, `build_list_binary`, `build_list_ho`, `build_indexed_map` — the last gained a `name` param it didn't have); `list_unary_extra_cost`/`list_binary_extra_cost` threaded with `derived_extra`; growth-loop call-site updates (9 call sites); `term_json`/`term_str` `Call` arms (the panic-avoidance fix, §1) |
| `runners/dsl/src/synth_enumerate.rs` (test module) | 220 | 0 | `Fixture::run`/two other pre-existing `TermNode::SynthEnumerate{...}` literals gained `derived_ops: None`; new `Fixture::run_with_derived` helper; 4 new `#[test]` fns (§2, §1's leak test, §1's mixed-pool test) |
| **`Call`'s own six-touch-point total** (term.rs's Call-specific lines + term_variants.rs + jsonio.rs + reflect.rs + synth_enumerate.rs's `term_json`/`term_str` Call arms) | **~155** | — | vs. the ~60-100 estimate — see below |

**Honest accounting of the overrun**: of term.rs's 132 insertions, roughly
half (~65) are the `DerivedOpPool`/`DerivedOpDef`/`DerivedOpRegistry` type
definitions + `EvalCtx.derived_ops` field + `SynthEnumerate.derived_ops`
field/doc — infrastructure the `§3.4` estimate did not itemize because it
was pricing `Call` as if it dispatched through an ALREADY-EXISTING channel
(the doc's own pseudocode assumed `ctx.derived_ops` already existed as a
concept; building that concept, including the `Arc`-not-`&'a` lifetime
resolution in §1, is real, necessary, uncounted work). The REMAINING ~67
lines of term.rs plus term_variants.rs/jsonio.rs/reflect.rs's 28 lines plus
synth_enumerate.rs's own ~12-line `Call` rendering arms total ~107 — close to,
modestly above, the upper end of the original ~60-100 estimate for the
`Call` variant's touch points alone, consistent with `Reverse`/`Plus`'s
precedent once the registry-infrastructure lines are separated out. The
build-A wiring itself (synth_enumerate.rs's ~278 core lines) was never
priced by `§3.4` at all — it is `§4`'s own, separately-scoped "narrow
fallback arms" piece, sized here for the first time: **278 lines, not a
handful**, because five distinct dispatch functions each needed a fallback
arm, `op_list` construction needed the two-stage metadata/registry split,
and `list_unary_extra_cost`/`list_binary_extra_cost` needed threading to stay
honest for future `ListUnary`/`ListBinary` derived ops (not exercised by
`Total2`, but left correct rather than silently wrong).

---

## 4. Gates

### 4.1 `cargo build --release`

Green, zero errors, on the first attempt after all edits (both the
pre-change baseline build and the full post-change build were run and
confirmed separately).

### 4.2 `cargo test --lib --release -- --test-threads=1`

**A real environment gotcha, found and fixed, not glossed over**: this
crate's `pyo3 = { features = ["extension-module", ...] }` is set
UNCONDITIONALLY (`Cargo.toml:12`), which prevents a plain `cargo test` from
linking at all (`undefined reference to Py_DecRef` etc. — extension-module
mode deliberately does not link libpython, correct for the `.so` build,
fatal for a standalone test binary). Already-documented fix, found in
`META_SHAPE_FIRST_CLASS_RESULTS.md` §7.1 and reused verbatim:

```
RUSTFLAGS="-C link-arg=-L$(python3 -c 'import sysconfig;print(sysconfig.get_config_var("LIBDIR"))') -C link-arg=-lpython3.13" \
LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/lib cargo test --lib --release -- --test-threads=1
```

- **Baseline** (`main @ a8cb4f5`, this worktree's own unedited base, run in
  the separate `/home/matt/ozmadev/ocelot` checkout to avoid any risk of
  contamination from the worktree's in-flight edits): **774 passed; 0
  failed; 4 ignored.**
- **This worktree, after all changes**: **778 passed; 0 failed; 4
  ignored** — 774 + 4 new tests (`call_dispatches_to_registry_template_
  matching_native_plus`, `derived_ops_registry_does_not_leak_past_the_call`,
  `total2_derived_op_search_matches_native_plus_byte_for_byte`,
  `mixed_pool_derived_op_is_silently_unusable_under_build_a`), all green.
  **774 → 778, exactly N=4, zero regressions.**

### 4.3 `bash scripts/engine_build.sh`

Installed cleanly (`runners/dsl/python/substrate_rs/_native.abi3.so` +
`_native.build.json` rebuilt and committed). The script's own trailing
build-record step failed on this box specifically because it shells out to
`python` (not `python3`) — a pre-existing, environment-specific naming gap,
not a defect in the engine or this rung's code; the build record was written
by running the SAME Python call the script itself performs, with `python3`,
and `tests/test_engine_provenance_migrated.py` (9 passed, 1 skipped) confirms
the tree's engine matches its own source.

### 4.4 `python3 scripts/mbpp_endgame_battery.py`

**A second environment gotcha, found and fixed**: this worktree (like any
fresh `git worktree add`) starts with `data/` (a real directory in the
canonical checkout, gitignored, never tracked) and every file under
`results/` (also `results/* ` gitignored) absent — `domains/prog_synthesis.
py::ensure_construction_bigrams` needs `results/prog_construction_scan.json`
to even BOOT the synthesis pipeline, so every one of the 257 tasks failed
with a swallowed `FileNotFoundError` (`run_task`'s own "never let one row
crash the batch" `except Exception` — the observed symptom was
`runnable 0/257` for every arm, RUN in ~9s instead of the real ~70-120s per
arm, a giveaway in retrospect that nothing had actually executed). Fixed by
symlinking `data/` and `rsync`-copying every file under `results/` from the
canonical checkout (`/home/matt/ozmadev/ocelot`) into this worktree — pure
local reference data, gitignored, not part of this rung's source diff, and
removed (`data`) / left in place (`results/*`, invisible to `git status`
either way) before the final commit.

**Paired task-ID comparison, not bare counts** — every `runnable_rows`
outcome, for all 257 tasks, in all three arms, compared field-by-field
between the pre-existing baseline artifact
(`/home/matt/ozmadev/ocelot/results/mbpp_endgame.json`, itself freshly
re-run and reconfirmed at 69/68/98 during this same session, `det_identical:
true`) and this worktree's own fresh run:

| arm | pass task IDs (both baseline and this worktree, identical) | outcome diff count |
|---|---|---|
| `full` | `11, 16, 20, 58, 59, 64, 69, 71, 74, 82, 84, 85, 87, 88, 89, 90, 98, 104, 106, 115, 118, 120, 127, 131, 132, 135, 138, 139, 141, 142, 145, 161, 227, 230, 232, 233, 234, 249, 257, 266, 272, 276, 278, 281, 290, 309, 312, 393, 394, 404, 406, 410, 413, 418, 428, 433, 436, 443, 450, 451, 456, 457, 458, 460, 472, 473, 474, 475, 477` (69) | **0** |
| `content_stripped` | `11, 16, 20, 58, 59, 64, 69, 71, 74, 82, 84, 85, 87, 88, 89, 90, 98, 104, 106, 115, 118, 120, 127, 131, 132, 135, 138, 139, 141, 142, 145, 161, 227, 230, 232, 233, 234, 249, 257, 266, 272, 276, 278, 281, 290, 309, 312, 393, 394, 404, 406, 410, 413, 418, 428, 433, 436, 443, 450, 451, 456, 457, 458, 460, 472, 474, 475, 477` (68) | **0** |
| `official` | `11, 12, 14, 16, 17, 19, 20, 58, 62, 64, 66, 68, 69, 70, 71, 82, 84, 85, 87, 88, 89, 90, 95, 98, 104, 105, 106, 115, 118, 120, 127, 131, 132, 135, 138, 139, 141, 142, 143, 145, 161, 164, 168, 171, 227, 230, 232, 233, 234, 249, 250, 253, 257, 266, 272, 276, 278, 281, 284, 285, 290, 294, 296, 309, 311, 312, 393, 394, 400, 404, 406, 410, 413, 414, 418, 424, 425, 428, 433, 434, 436, 443, 446, 450, 452, 456, 457, 458, 460, 461, 464, 471, 472, 473, 474, 475, 476, 477` (98) | **0** |

"Outcome diff count" is over EVERY per-task outcome string (`pass`,
`gapped:*`, `accepted_holdout_fail`, `not_recognized`, `runner_exception:*`,
…), not just the pass/fail boundary — zero divergence anywhere, for any of
the 257×3 = 771 (task, arm) cells. **69/68/98, exactly matching
`results/mbpp_endgame.json`'s own cited baseline, byte-for-byte — zero
regressions, zero new passes**, exactly as predicted (this rung's new
`Call`/`derived_ops` machinery is never exercised by the battery, since no
task's spec ever supplies a `derived_ops` argument — the mechanism is
additive and dormant unless explicitly invoked, exactly the "plumbing
proof, not a capability claim" framing this step was scoped as).

---

## 5. What this slice does NOT establish

Per the parent doc's own §9 exclusion list, none of the following were built
or attempted: the generic (B) pool-typed combinator; the offline mint sweep;
the Γ-composition wiring (`SynthOp{kind:"derived"}`); registering
`JoinListSep` itself (§8.3 of the parent doc already shows it would fail the
mint bar even if buildable); any motor-program unification. `build_list_ho`/
`build_indexed_map`'s own fallback arms are unreachable dead code under this
slice's registry-inference rules (§1) — real, not hidden. The `Arc`-based
`EvalCtx.derived_ops` resolution (§1) is this slice's own addition to the
parent doc's design, not present in `DERIVED_OPERATOR_TIER_RESULTS.md`
itself — a real Rust lifetime constraint the design-only document could not
have hit without attempting to compile it.

---

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/derived-operator-tier-slice1
git log --oneline -1   # on top of main @ a8cb4f5
LIBDIR=$(python3 -c 'import sysconfig;print(sysconfig.get_config_var("LIBDIR"))')
RUSTFLAGS="-C link-arg=-L${LIBDIR} -C link-arg=-lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH" \
  cargo test --manifest-path runners/dsl/Cargo.toml --lib --release -- --test-threads=1
bash scripts/engine_build.sh
ln -s /home/matt/ozmadev/ocelot/data data   # local reference data, gitignored
rsync -a --ignore-existing /home/matt/ozmadev/ocelot/results/ results/
PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
```
