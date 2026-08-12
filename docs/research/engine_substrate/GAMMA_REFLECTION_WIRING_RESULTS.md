# Γ reflection wiring — results

**Verdict: GO (scoped).** `production_from_node`/`grammar_from_graph` were built
(`runners/dsl/src/grammar_reflect.rs`, the exact analogue of
`graph_rules::rule_from_node`), and `Substrate::add_production` (the Rust
inherent method) now routes its `where_`/`weight` Terms through
`reflect::term_to_subgraph`, writing a real `GammaProduction` graph node for
every production added through it. This closes recommendation 2(ii) of
`SELF_REFERENCE_INFINITY_GROUNDING.md` §5 **literally and honestly, at the
scope that method's own real callers occupy** — not at the scope of "all Γ
mutation everywhere," which turned out, on investigation, to be a materially
larger and separately-risked claim (§2 below). All five PREREG (§1.3)
GO/NO-GO bars cleared. Round-trip content-equality is proven two ways: an
isolated unit round-trip in `grammar_reflect.rs`, and an end-to-end test
through the real `Substrate::add_production` call path comparing
`checker.grammar` against `grammar_from_graph`'s reconstruction
byte-for-byte via `jsonio::term_to_json`.

**The honest boundary, stated up front (do not skip to the numbers without
this):** the PyO3-exposed `add_production` Python binding — the path
essentially all real-world Γ growth goes through (129 call sites across
`tests/*.py`, plus `substrate/world_adapter.py`) — was found, during this
rung's own investigation, to bypass the Rust inherent `Substrate::add_production`
entirely (it calls `checker.grammar.add(p)` directly). This rung's mirror
therefore does **not** fire for that traffic. What is graph-resident after
this build is real, provably correct, and satisfies the literal text of
recommendation 2(ii) — but it currently covers only the Rust-internal call
sites (`declare_shares_shape`, `declare_relation_edge`) plus any new caller
that uses the Rust inherent method directly. See §2 for the full, precise
accounting of what changed and what didn't.

**Regression headline:** `cargo test --lib` paired 737→740 passed, 0 failed,
0→0 regressions (+3 new tests). `pytest -k migrated`, full suite, 99%
coverage (9800 recorded outcomes; the tail did not complete within a
responsible time/memory budget on shared hardware — see §4b), diffed
node-for-node against a freshly rebuilt baseline engine on every single red
node from the changed run (871 node ids, 100% of the flagged set): **exactly
one node differs, and it is a pre-existing, unrelated repo-wide "no new Rust
anywhere" tripwire from a different rung's cost-bar experiment
(`test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED`) that fails for any
Rust-touching change by design, not a functional defect in what this rung
built.** Zero genuine behavioural regressions found. Full method and honest
coverage accounting in §4b.

---

## 0. Provenance

- Worktree: `/home/matt/ocelot-gamma-reflection-wiring`, branch
  `gamma-reflection-wiring`, detached from `main` at `003a121` (verified;
  `main` in the primary tree advanced to `3e031e3` over the course of this
  session via the concurrent ARC6 thread — expected and harmless, since this
  worktree is isolated and never reads from the primary tree's working copy).
- Baseline (unedited source, this worktree's own checkout of `003a121`) `.so`
  sha256, rebuilt fresh for the regression comparison in §4/§5:
  `517e06df3eeaaa43d9877e0f146a6b609ae8aa4046b5d7387e167d5013024621`
  (`domains.engine_provenance.engine_provenance()`: `source_match = "own"`,
  `stale_rust = []`). The `003a121`-tip binary as originally committed hashes
  `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`; the
  rebuilt hash differs only because the release profile is not
  bit-reproducible across separate `cargo build` invocations on this box
  (timestamps/build-id in the object file) — the SOURCE is verified
  byte-identical to `003a121` (`git stash`'d this rung's 4 changed files,
  confirmed via `git status`/`git diff` before the rebuild).
- **Final** engine WITH changes, sha256:
  `d7acb906da8ffb2c02c6feccd3bf3ecc62241b956f6343c336479a0f5e363843`
  (`source_match = "own"`, `stale_rust = []`, verified in-process
  immediately before every measurement below — see §6 for two separate
  stale-provenance gotchas this rung hit and fixed along the way, including
  one caused by a doc-comment-only edit to `reflect.rs` made mid-run).
  Reproducible: rebuilt twice from the identical final source and got the
  identical hash both times.
- Build: `maturin develop --release --skip-install` inside a local venv
  created solely to satisfy maturin's virtualenv-detection requirement
  (`--skip-install` touches no pip/site-packages state — only this
  worktree's own `runners/dsl/python/substrate_rs/_native.abi3.so`, the file
  `conftest.py`'s own sys.path logic prefers). **`CARGO_BUILD_JOBS=2`** for
  every build in this rung (not the committed config's default of 4) —
  this box hosts live home infrastructure (security cameras, home
  automation, a media server); after a genuine OOM event mid-rung (§6),
  every subsequent heavy command in this rung was run under
  `systemd-run --scope --user -p MemoryMax=... -p MemoryHigh=...` as a hard
  ceiling, one heavy process at a time, with `free -h` checked before each.
- PREREG: `docs/research/engine_substrate/GAMMA_REFLECTION_WIRING_PREREG.md`,
  registered before any Rust was written.

---

## 1. What was built

`runners/dsl/src/grammar_reflect.rs` (new file, ~300 lines including tests):

- `production_to_subgraph(root, index, &Production, &mut TypedGraph, &TermArena, &mut Interner) -> NodeID`
  — writes one `GammaProduction` node (attrs: `edge_type`, `provenance`),
  two `GammaNodePattern` nodes (`pattern.src`/`pattern.tgt` edges, attrs
  `type`/`var`), and reflects `where_` (if present) and `weight` (always
  present) through `reflect::term_to_subgraph` as real `Term.*` subgraphs,
  wired via `pattern.where`/`pattern.weight` edges. Wired from `root` (a
  `GammaGrammar` node) via a `production` edge carrying an `index` attr.
- `production_from_node(&TypedGraph, NodeID, &mut TermArena, &Interner) -> Result<Production, GammaReflectError>`
  — the exact analogue of `graph_rules::rule_from_node`, reading a
  `GammaProduction` node back into a native `Production`, reconstructing
  `where_`/`weight` via `reflect::term_from_subgraph`.
- `grammar_from_graph(&TypedGraph, NodeID, &mut TermArena, &Interner) -> Result<Grammar, GammaReflectError>`
  — walks every `production` edge from a `GammaGrammar` root (ordered by the
  `index` attr), parses each via `production_from_node`, and builds a fresh
  indexed `Grammar` — the analogue of `graph_rules::run_graph_rules_opts`'s
  "walk every Rule node, parse, collect" loop, applied to productions.
- Deliberately distinct node-type vocabulary — `GammaGrammar` /
  `GammaProduction` / `GammaNodePattern` — NOT the pre-existing
  `Grammar`/`Production`/`NodePattern` strings `substrate/grammar.py` /
  `substrate/world_adapter.py` already use for a different, disconnected
  object (§2.2). Reusing those strings would have been both a collision risk
  and a category error.

`runners/dsl/src/substrate.rs`:

- New field `gamma_graph_root: Option<NodeID>` on `Substrate`, lazily
  created on first mirrored `add_production` call.
- New accessor `gamma_graph_root() -> Option<NodeID>`.
- `Substrate::add_production` now, in addition to its existing
  `checker.grammar.add(p)` + `gamma_epoch.bump()`, calls
  `grammar_reflect::production_to_subgraph` to write the mirror, using the
  count of existing `production` edges from the root as the new production's
  `index`.
- Two new Rust unit tests: `graph_mirror_is_content_equal_to_checker_grammar`
  (end-to-end through the real `add_production` path, §3) plus the fix to a
  pre-existing test that turned out to hard-code node-insertion order (§5).

`runners/dsl/src/lib.rs`: one new `pub mod grammar_reflect;` line.

**Total new/changed Rust:** `grammar_reflect.rs` ≈ 300 lines (incl. tests);
`substrate.rs` net +~135 lines (mirror wiring + 2 new tests + the fix to
`settle_repro`'s call sites); `lib.rs` +1 line. **Well under the registered
bar-1 threshold (≤300 net new lines for the reader + wiring alone).**

---

## 2. The honest boundary — what is and isn't graph-resident now

This section is the point of the whole exercise; it is written to the exact
standard `SELF_REFERENCE_INFINITY_GROUNDING.md` §3.2 asked not to be
repeated in the other direction (claiming full graph-nativity for a
mirror/shadow copy).

### 2.1 What genuinely changed

Every `Production` added via the **Rust inherent** `Substrate::add_production`
now has a real, independently-reconstructable graph mirror: a
`GammaProduction` node, its `GammaNodePattern` src/tgt, and (crucially, the
literal ask of recommendation 2(ii)) its `where_`/`weight` as real `Term.*`
subgraphs — not a JSON string, not a Rust-only value. This was proven, not
just asserted:

- `grammar_reflect::tests::round_trip_content_equal` — isolated round-trip
  (`production_to_subgraph` → `grammar_from_graph`), content-equal via
  `jsonio::term_to_json` comparison across two independent `TermArena`s.
- `substrate::tests::graph_mirror_is_content_equal_to_checker_grammar` —
  END-TO-END through the real call path: two productions (one with a
  `where`-clause Term, one without) added via `s.add_production(...)`, then
  `grammar_from_graph(&s.graph, s.gamma_graph_root().unwrap(), ...)`
  reconstructs a `Grammar` that is field-for-field, Term-for-Term equal to
  `s.checker.grammar` itself.
- A live Python-visible demonstration (not just Rust unit tests):
  `s.declare_shares_shape()` (a real, shipped Rust-internal caller of
  `Substrate::add_production`) produces exactly `GammaGrammar` (1),
  `GammaProduction` (1), `GammaNodePattern` (2), `Term.Lit` (1) — five real
  graph nodes, queryable via the ordinary `graph_to_dict()` Python API, with
  no Python-side code involved in producing them.

`ConsistencyChecker.grammar` — the object `check_edge` actually reads — is
**unchanged**: still a plain Rust `Vec<Production>` + hashmap index, same
algorithm, same complexity (bar 2, verified: no new graph traversal was
added anywhere on the `check_edge` call path; `grammar_reflect.rs` is never
imported by `checker.rs`).

### 2.2 What did NOT change, and why this matters more than it first looks

**Finding, made during this rung's own §0 investigation (not anticipated by
the brief):** the PyO3-exposed `PySubstrate::add_production` binding
(`py.rs:7803-7820`) — the method every real caller uses (129 call sites
across `tests/*.py`, plus `substrate/world_adapter.py`'s `boot_gamma_meta`/
`grow_gamma`) — does **not** call the Rust inherent `Substrate::add_production`.
It calls `inner.checker.grammar.add(p)` directly. This was true before this
rung and remains true after it; this rung's mirror is wired into the method
the brief named literally (`Substrate::add_production`), and that method is
not, in practice, where most Γ growth happens today. Two consequences:

1. **This was already a real, pre-existing bug independent of this rung's
   charter**: the PyO3 path also bypasses `gamma_epoch.bump()`, silently
   breaking the documented "installed L2 dispatchers see the Γ change"
   contract for every Python-driven `add_production` call. Verified live
   (`s.add_production({...})` via the PyO3 binding, then `grammar_to_json()`
   showed the production was added to `checker.grammar` correctly, but a
   direct inspection of `graph_to_dict()`'s node types showed no
   `GammaGrammar`/mirror nodes — confirming the bypass empirically, not just
   by reading the two functions side by side).
2. **A second, more informative prior-art finding**: `substrate/grammar.py`
   and `substrate/world_adapter.py` (NOT deleted — still live) already
   implement a DIFFERENT graph-resident Γ mechanism
   (`boot_gamma_meta`/`gamma_dynamic`/`_append_production`/`grow_gamma`),
   using the type strings `Grammar`/`Production`/`NodePattern` and storing
   `where` as a `where_json` STRING attr rather than a real Term subgraph.
   Reading `grow_gamma` (`world_adapter.py:6788-6852`) shows it calls
   `self._append_production(...)` — which never calls `add_production`
   (neither the PyO3 binding nor, transitively, the Rust method) — so the
   CuriousAgent's discovered relations become graph-resident BOOKKEEPING
   (feeding `quality_of_gamma`'s monotone score) but are **never actually
   admissible**: they never touch `ConsistencyChecker.grammar`. This is
   Γ_dynamic in the CuriousAgent sense, not Γ in the paper's Definition-2
   sense — a DIFFERENT object from what this rung's charter is about, real
   and working on its own terms, but not a substitute for what recommendation
   2(ii) asked for and not something this rung's file-scope permitted editing.

**Net honest statement for a reviewer:** after this build, THREE distinct
things exist in this codebase that could each be glossed as "Γ is
graph-native," and they must not be conflated:

| Thing | Graph-resident? | Actually gates `check_edge`? | Real Term subgraphs (vs JSON/opaque)? |
|---|---|---|---|
| `ConsistencyChecker.grammar` (the paper's Γ) | No — Rust struct, unchanged | **Yes — this is the gate** | N/A (native `TermIdx`) |
| This rung's mirror (`GammaGrammar`/`GammaProduction`) | **Yes**, for `Substrate::add_production` callers only | No (mirror only) | **Yes** |
| `substrate/world_adapter.py`'s Γ_dynamic (`Grammar`/`Production`) | Yes, for `_append_production` callers (mostly `grow_gamma`) | No (bookkeeping only) | No — `where_json` string |

None of the three, alone, is "Γ is graph-native and gates admissibility" —
that would require unifying row 1 and row 2 (not attempted here; see §7)
or row 1 and row 3 (a different, larger project outside this rung's scope
entirely). This rung's contribution is making row 2 real, correct, and
provably content-equal to row 1 for the traffic it covers.

---

## 3. GO/NO-GO bars — verdict table (against PREREG §1.3)

| # | Bar | Threshold | Measured | Verdict |
|---|---|---|---|---|
| 1 | New Rust LOC | ≤300 net new for reader+wiring | `grammar_reflect.rs` ~300 incl. 2 tests; `substrate.rs` wiring itself ~30 lines (the rest of its diff is 2 new tests + a 3-line fix to a pre-existing test) | **GO** |
| 2 | `check_edge` hot path unchanged | zero new graph traversal | Confirmed by inspection: `checker.rs` has no new imports, `grammar_reflect` is never called from the check path | **GO** |
| 3 | `grammar_to_json`/`grammar_from_json` byte-identical | unchanged output | `jsonio.rs` untouched (zero diff); live-verified: `grammar_to_json()` output shape/values identical before/after this build for the same productions | **GO** |
| 4 | Full regression, paired | `pytest -k migrated` + `cargo test` before/after | `cargo test`: 737→740, 0 failed either side (§4). `pytest -k migrated`: 99% coverage full run + a complete (871/871 node) targeted baseline diff on every red node found exactly ONE difference, a pre-existing unrelated tripwire, not a functional regression (§4b) | **GO** (§5: one Rust-level regression found via `cargo test` and fixed; §4b: the pytest-level diff; §6: three environmental gotchas, incl. a machine OOM, none caused by this rung's design) |
| 5 | Round-trip / "same data" | content-equal reconstruction, not just "some nodes exist" | `grammar_reflect::tests::round_trip_content_equal` + `substrate::tests::graph_mirror_is_content_equal_to_checker_grammar` (end-to-end) both green | **GO** |

---

## 4. `cargo test` — full lib suite

`cargo test --lib` under this repo's actual toolchain (see §6 for the
toolchain-shadowing gotcha this rung had to work around) with
`-- --test-threads=1` (parallel `cargo test` on this crate is independently
flaky — see below, unrelated to this rung):

- **Baseline** (`git stash` of this rung's 3 changed files, same worktree,
  same toolchain): **737 passed, 0 failed, 4 ignored.**
- **With changes** (final, after the fix in §5): **740 passed, 0 failed, 4
  ignored** (+2 new tests in `grammar_reflect.rs`, +1 new integration test
  `graph_mirror_is_content_equal_to_checker_grammar` in `substrate.rs`).

**Parallel `cargo test --lib` (default `--test-threads`) is flaky on this
crate independent of this rung** — confirmed on BOTH the baseline (3
different tests failed) and the changed tree (5 different failed, on an
earlier attempt before the fix in §5), with DIFFERENT specific
failures each run and left/right value mismatches characteristic of shared
global-counter contamination between tests (`scale_audit`/`shape_decode`
instrumentation is explicitly documented as process-global,
"Default OFF" toggles). Serial execution (`--test-threads=1`) is
fully deterministic and green on both baseline and changed. This is a
**pre-existing property of the test suite**, not introduced by this rung —
reported here because it is exactly the kind of thing a rung must not
paper over, and because it is why this results doc's numbers are all
serial-execution numbers.

---

## 4b. `pytest -k migrated` — full suite, paired failing-node-id lists

**Method, stated up front because it deviates from a naive "run the whole
suite twice" and the deviation matters.** A first full-parallelism attempt
(`-n 12`) coincided with a genuine machine-wide OOM/reboot (root cause: a
runaway, unrelated to this rung's own worker count per the owner's own
post-mortem — see §6). Every subsequent heavy command in this rung ran
under a `systemd-run --scope --user -p MemoryMax=... -p MemoryHigh=...`
hard ceiling, one at a time, with `free -h` checked first. Under that
discipline, a full **from-scratch baseline run at the same width the
changed run used would have cost another ~3 hours** — not a responsible
use of a shared box that also runs this owner's home infrastructure. The
methodology actually used instead, which answers the SAME regression
question with a fraction of the cost and is arguably a MORE targeted
instrument for it:

1. **Full changed-engine run, `pytest tests/ -k migrated -n 4` (capped,
   `MemoryMax=16G`), to completion.** It ran 3h09m and was stopped with a
   clean `SIGINT` (not `SIGKILL`) at ~99% coverage after the run had
   genuinely stalled for the final ~1% behind one single-threaded,
   growing-RSS worker (a subprocess-heavy retry/restart test); pytest's own
   interrupt handler printed its normal end-of-session summary for
   everything that HAD completed — this is pytest's documented graceful-stop
   behaviour, not a crash, and the summary line is real:
   **`519 failed, 8680 passed, 240 skipped, 361 errors` (11380.62s = 3:09:40)**,
   `1608` warnings. Coverage is declared, not implied: `8680+519+240+361 =
   9800` node outcomes recorded; a small tail (the exact stalled test plus
   whatever xdist had not yet dispatched) is `NOT_ESTABLISHED` rather than
   silently folded into any bucket, per this repo's own
   `test_failure_baseline_migrated.py` discipline ("coverage is declared").
2. **Extract every FAILED/ERROR node id from that run** (871 unique lines,
   `/tmp/gamma_rw_results/changed_red.txt` — not reproduced here since `/tmp`
   does not survive a reboot, but the derivation is mechanical and the
   result is restated in full below).
3. **Rebuild the baseline engine** (`git stash` this rung's 4 changed files,
   `CARGO_BUILD_JOBS=2`, capped) — sha256
   `517e06df3eeaaa43d9877e0f146a6b609ae8aa4046b5d7387e167d5013024621`,
   `source_match = "own"`, `stale_rust = []`.
4. **Re-run EXACTLY those 871 node ids against the baseline engine**
   (`-n 4`, capped `MemoryMax=12G`) — this is the actual regression
   question, asked directly: *of everything that was red in the changed
   run, how much was ALREADY red before this rung touched anything?*
   870 collected (one line was a duplicate-shaped collection-error entry),
   28 collection errors, in 19m09s:
   **`518 failed, 1 passed, 361 errors`**.
5. **Diff the two failing-node-id sets** (`comm -23`/`comm -13` on the
   sorted, deduped lists).

**Result: exactly ONE node differs between the two sets, in either
direction.** `tests/test_arc_decompose_migrated.py::test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED`
is red in the changed run and green in the baseline-targeted run; every
other one of the 870 shared node ids is red in BOTH. Read directly, this
test is not a functional regression at all — it is a repo-wide tripwire
from a completely unrelated prior rung (ARC6's AR17b(iii)/AR18d cost bar)
whose entire body is `assert git diff HEAD -- runners/dsl/src/ == ""`
("no new Rust for A17/A18") plus an AST-level check of two unrelated
adapter files. **This assertion is definitionally incompatible with this
rung's own charter** (`runners/dsl/src/` is exactly where CLAUDE.md and
this rung's brief direct new Rust to go) and would fail identically for
ANY Rust-touching change in this repo, regardless of what it does — it is
not evidence about `grammar_reflect.rs`, `Substrate::add_production`, or
anything this rung built. Read the test's own docstring
(`tests/test_arc_decompose_migrated.py:683-700`) for the full, self-declared
scope of what it is actually gating (an unrelated ARC6 program-synthesis
cost-bar experiment), confirming this reading, not asserting it.

**Net: zero genuine behavioural regressions found**, across a 99%-coverage
full-suite run (9800 recorded outcomes) plus a targeted, complete (100% of
the flagged set) baseline comparison on every single item that was ever
red. `1741` total lines were compared (`871 + 870`); `1740` matched exactly
between engines.

The `divergence.json` fixture note (also relevant here): `tests/fixtures/
comprehension_divergence/divergence.json` was found MODIFIED after each
full-suite run (only `shadow_latency_ms` values changed — a live wall-clock
timing measurement some test writes back into this fixture on every run,
unconditionally, regardless of engine). This is test-suite behaviour
unrelated to this rung's own changes (confirmed: it happened identically
after the baseline-targeted run, which touches no code this rung wrote) —
`git checkout -- tests/fixtures/comprehension_divergence/divergence.json`
was run before every commit-adjacent state check, and the file is untouched
in the final committed diff.

---

## 5. The one real regression found, and the fix

`substrate::tests::run_rules_returns_over_unsettled_state_when_attr_write_follows_structural_dirty`
broke under the changed engine (serial run): its precondition assertion
failed because the test hard-codes `let n1 = crate::graph::NodeID(3); //
4th inserted node` inside `settle_repro`'s caller — an assumption that
`n1` is exactly the 4th node ever inserted into `s.graph`. `settle_repro`
calls `s.add_production(...)` (line 6265, BEFORE its own `s1`/`s2`/`s3`/`n1`/
`n2` nodes are created) to declare the `tag` edge type admissible — and this
rung's mirror now allocates 5 real graph nodes (the `GammaGrammar` root +
1 `GammaProduction` + 2 `GammaNodePattern` + 1 `Term.Lit` for the default
weight) during that call, shifting every subsequently-inserted node's ID by
5. This is exactly the class of risk the PREREG's §1.3 "known risk flagged
before building" paragraph anticipated (18 Python test files combining
`add_production` with node-count-shaped assertions) — found instead, by
actually running the tests, in a Rust unit test's node-ID LITERAL rather
than a Python node-count assertion, which is the same underlying risk class
in a different shape.

**Fix (mechanical, minimal, does not weaken the test):** `settle_repro` now
returns `n1`'s actual `NodeID` (`fn settle_repro(pre_open_gate: bool) ->
(Substrate, Sym, NodeID)`) instead of the caller reconstructing it from a
hard-coded literal. Both call sites were updated
(`run_rules_returns_over_unsettled_state_when_attr_write_follows_structural_dirty`,
`settle_repro_settles_when_the_attribute_is_present_before_the_first_pass`).
The test's actual subject — the fixpoint-settle defect it reproduces — is
completely untouched; only the insertion-order-derived ID literal was ever
load-bearing on node-allocation order, which is now honestly a
`Substrate::add_production` side effect it did not have before this rung.

**Consequence worth naming plainly for a future caller:** `Substrate::add_production`
is no longer a pure Rust-struct mutation with zero effect on `self.graph`'s
node-ID sequence — it now allocates real graph nodes too. Any future test or
caller that assumes NodeID contiguity/order across an `add_production` call
will see the same class of shift this rung's own regression run caught. A
repo-wide grep for `NodeID(<literal>)` found exactly two other occurrences
(`persist.rs:539,567`), both unrelated to `add_production` (confirmed: no
`add_production` call in that file) — no further collateral found.

---

## 6. A build-provenance gotcha this rung hit and is worth recording

Mid-rung, after the .so had already been built, a Rust unit test was added
to `substrate.rs` (§2.1's end-to-end test) — a source edit AFTER the build.
This bumped `substrate.rs`'s mtime past the `.so`'s, and
`domains/engine_provenance.py`'s `stale_rust` check (part of
`engine_preamble`, which `conftest.py` calls on every pytest collection)
refused essentially the entire `pytest -k migrated` collection
(`EngineProvenanceError`-shaped failures on ~150+ files) — NOT a real defect
in this rung's Rust, purely a stale-timestamp artifact of editing source
after building. Diagnosed directly (`domains.engine_provenance.engine_provenance()`
printed `stale_rust: ['runners/dsl/src/substrate.rs']`), fixed by rebuilding
once more after all source edits were finalized (`stale_rust: []`
afterward, same content hash as the pre-test-addition build — confirming the
test-only edit changed no compiled behaviour). **Lesson for future rungs
doing this exact "prereg → build → discover a needed test → add it → forgot
to rebuild" loop**: rebuild is the LAST step after the LAST source edit, not
after the last *behavioural* edit — `#[cfg(test)]`-only changes still bump
mtimes and still trip this gate.

A second, unrelated environmental issue found and worked around, not a
defect of this rung: the box's default `rustc`/`cargo` on `PATH` was a
Homebrew-installed 1.87.0 (too old to stably support the `avx512f`/`avx512bf16`
`target_feature` attributes this crate's `l1_hot_paths.rs`/`l3_lqr.rs`
already use — pre-existing on `main`, confirmed by running the identical
`cargo check --lib` against the unmodified primary tree and seeing the same
29 `E0658` errors). `rustup`'s own managed toolchain (1.97.1, at
`~/.cargo/bin`, shadowed by Homebrew's earlier `PATH` entry) supports them
natively; putting `~/.cargo/bin` first on `PATH` was sufficient. Reported
here in case a future rung in this environment hits the same wall and
wastes time suspecting its own Rust edits.

**A third, unrelated but serious incident: a machine-wide OOM/reboot
occurred mid-rung.** This box hosts real home infrastructure (security
cameras/Frigate, Home Assistant, a media server, a network controller)
alongside this and several OTHER concurrent worktrees' agent sessions. The
owner's own post-mortem: the crash was a genuine runaway process, not
ordinary parallel-worker contention (an initial "cap everything at `-n 2`"
instruction was issued, then explicitly revised once the actual cause was
identified). The two durable practices this rung adopted for the remainder
of its work, worth carrying into any future heavy rung on shared
infrastructure like this: **(a) wrap every long/heavy command in
`systemd-run --scope --user -p MemoryMax=<N>G -p MemoryHigh=<N-4>G --`** —
this converts an unbounded runaway into a bounded, swap-throttled one that
cannot itself take the box down, confirmed live (one xdist worker's RSS was
observed climbing across checkpoints during the recovered full run;
because the whole scope carried a ceiling, it throttled into swap rather
than exhausting the machine); **(b) `free -h` before every command
expected to be memory-heavy, and treat `available` (not `free`) as the
number that matters** (page cache inflates `used`/deflates `free` harmlessly
under normal Linux accounting — this rung's own runs regularly showed
`free` near 1-2Gi while `available` held at 18-25Gi throughout, which is
healthy, not a warning sign; the actual warning sign to watch is `available`
itself trending down across checkpoints, or swap climbing without bound).
One heavy process ran at a time for the remainder of the rung
(`cargo build`/`maturin develop`/`pytest`), never overlapping.

---

## 7. What a full unification (row 1 = row 2 in §2.2's table) would cost — not attempted, sized for a future rung

Named, not built, per the PREREG's own explicit scope:

- **Covering the PyO3 `add_production` binding too** would mean rerouting
  `py.rs:7803-7820`'s loop from `inner.checker.grammar.add(p)` to
  `inner.add_production(p)`. This is a ONE-LINE-PER-CALL change but a
  materially larger risk: 129 real call sites across `tests/*.py`, 18 of
  which were found (grep) to combine `add_production(` with
  node-count-shaped assertions in the same file — exactly the class of
  regression §5 found and fixed in the Rust suite, but at Python-test scale
  where the fix-cost per broken test is unknown without actually running
  them. It would also, as a side effect, retroactively fix the pre-existing
  `gamma_epoch` bump bug named in §2.2(1) — a genuine improvement, but one
  that changes behaviour for every existing seed/world-adapter caller, not
  something to bundle into a "wiring" rung without its own gate.
- **Making the graph the actual source of truth for `check_edge`** (rather
  than a mirror) would require either re-deriving `checker.grammar`'s index
  from the graph on every `check_edge` call (an O(1)→O(graph) regression on
  the hottest path in the substrate — a clear NO) or invalidating/rebuilding
  the index lazily on `gamma_epoch` bumps (plausible, since Γ changes are
  rare relative to `check_edge` calls, but a materially different design
  with its own correctness surface — e.g. what happens to in-flight
  `ProdIdx`/`CheckOutcome::Admitted` references across a rebuild — not
  designed or estimated here).

Recommendation: if a future rung wants full unification, it should be
pre-registered and gated exactly like this one, with the PyO3-reroute risk
measured empirically (run the 18 flagged Python test files first, in
isolation, before touching the shared binding) rather than assumed.

---

## 8. Reproduce

```bash
cd /home/matt/ocelot-gamma-reflection-wiring/runners/dsl
export PATH="/home/matt/.cargo/bin:$PATH"          # rustup's cargo, NOT Homebrew's
export RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"
cargo test --lib -- --test-threads=1                # 740 passed, 0 failed, 4 ignored

cd /home/matt/ocelot-gamma-reflection-wiring
python3 -m venv .build-venv && export VIRTUAL_ENV=$PWD/.build-venv
cd runners/dsl
CARGO_BUILD_JOBS=2 maturin develop --release --skip-install
cd /home/matt/ocelot-gamma-reflection-wiring
# Wrap in a memory ceiling on shared/home-infra hardware (see §6):
systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=12G -- \
  python3 -m pytest tests/ -k migrated -q --continue-on-collection-errors -n 4
# 8680 passed, 519 failed, 240 skipped, 361 errors (99% coverage, 3:09:40)
git checkout -- tests/fixtures/comprehension_divergence/divergence.json
```

Live demonstration (Python, no Rust test harness needed):

```python
import sys; sys.path.insert(0, "runners/dsl/python")
import substrate_rs as srs
s = srs.Substrate()
s.declare_shares_shape()
types = [n["type"] for n in s.graph_to_dict()["nodes"]]
assert "GammaGrammar" in types and "GammaProduction" in types
```
