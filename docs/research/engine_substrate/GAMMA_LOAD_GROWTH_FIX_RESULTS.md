# Γ load-growth fix — results

**Verdict: GO on AR1-AR3 and AR5 (landed); AR4 (the PyO3 reroute) is
independently re-validated CLEAN but deliberately NOT merged into this
rung's final commit.** The unbounded save/load growth
`GAMMA_PYO3_REROUTE_RESULTS.md` §2.5 found (+261 nodes/cycle, no
convergence) and the `detect_god_object` population-statistics corruption
§2.4 found are both fixed, small, and shown live to introduce **zero**
regressions against a pristine rebuilt baseline (18/18 identical
failing-node-ids, paired). The reroute itself was reconstructed on top of
both fixes and re-measured: it now closes cleanly, reproducing exactly the
**one** honest, pre-predicted "literal count needs bumping" test failure
(`test_rust_engine_parity.py::test_graph_round_trip_via_dict`) plus an
independently-confirmed second one from the prior rung's own
classification (`test_photon_eye_held_prediction_migrated.py`) — no new,
unexplained regression class. But fixing those two literals requires
editing test files, which sit outside this rung's declared file-scope
(`runners/dsl/src/py.rs`, `substrate/world_adapter.py`, and
`domains/architecture_assessment.py`'s `detect_god_object` only). Rather
than land a change that leaves two previously-green tests red in the
committed tree, the reroute's one-line `py.rs` change was reverted before
the final commit — its correctness is fully evidenced below (§4), sized as
a two-file, two-line follow-up, and left for a rung with test-file scope.

**The one thing worth reading if you read nothing else:** the replay in
`WorldAdapter.load()` is not a redundant seed-reinstall or a leftover
Python habit — it is the *only* mechanism that restores
`ConsistencyChecker.grammar` (a plain Rust struct `graph_from_dict` never
touches) from the separate `grammar_to_json`/`jsonio.rs` persistence path
`save()` also writes. It is load-bearing and cannot simply be deleted. The
actual bug was that this replay borrowed the general, possibly-mirroring
`add_production` binding for a job that never needed a mirror in the first
place (the mirror, if any, is already restored by `graph_from_dict`
because `save()` dumped it as part of the graph). The fix
(`add_production_no_mirror`, a `py.rs`-only sibling method) decouples
`load()`'s replay from whatever the general binding does, permanently —
this makes the growth bug structurally unreachable rather than merely
unobserved, and does not require the reroute to land atomically alongside
it (unlike the "reconstruct from `grammar_from_graph`" alternative, which
this rung investigated and rejected — see §1.3).

---

## 0. Provenance

- Worktree: `/home/matt/ocelot-gamma-load-growth-fix`, branch
  `gamma-load-growth-fix`, detached from `main` at `3e3daa5` (verified at
  worktree-creation time via `git log --oneline -1 main`).
- **Baseline** (unedited `3e3daa5` source, this worktree's own rebuild,
  `git stash` of this rung's 3 source files, `CARGO_BUILD_JOBS=2`, memory
  capped) `.so` sha256:
  `f87f857cf54a19a3942bd8878093e533d6b4896c9ec397f6e13f530a76165916`
  (`source_match = "own"`, `stale_rust = []`) — the identical hash
  `GAMMA_PYO3_REROUTE_RESULTS.md` reports as ITS OWN baseline, confirming
  byte-identical source across both rungs' starting points.
- **Final, landed** engine (AR2 `detect_god_object` filter + AR3
  `add_production_no_mirror` + `load()` using it; AR4's reroute NOT
  included) sha256:
  `81d75c0a84dc221839cb1d4aa9668d2064061613a225bf754cbc768c9f9b5b2e`
  (`source_match = "own"`, `stale_rust = []`). Rebuilt twice from identical
  final source (once mid-rung before the AR4 experiment, once after
  reverting AR4's line) and got the **identical hash both times** —
  reproducible; confirms the AR4 revert left zero residual diff.
- **AR4-included** engine (reroute reconstructed on top of AR2+AR3,
  measured in §4, NOT in the final commit) sha256:
  `5fa3bbb19783c199c71d4288089112e22fb83d7f6783043eb3525fedc067bed9`.
- Build: `maturin develop --release --skip-install` inside a local
  `.build-venv` (venv-detection only, touches no system site-packages),
  `CARGO_BUILD_JOBS=2`, `~/.cargo/bin` (rustup 1.97.1) placed first on
  `PATH` ahead of Homebrew's older toolchain (same pre-existing
  `avx512f`/`avx512bf16` gotcha both prior rungs documented). Every heavy
  command wrapped in `systemd-run --scope --user -p MemoryMax=8G -p
  MemoryHigh=7G --`, `free -h` checked first, one heavy process at a time.
- Coherence probe (all three engines): `add_node("T", {"lst":[1,2,3],
  "tup":(1,2,3)})` reads back `{'lst': [1, 2, 3], 'tup': (1, 2, 3)}` —
  list/tuple distinct.
- PREREG: `docs/research/engine_substrate/GAMMA_LOAD_GROWTH_FIX_PREREG.md`,
  registered before any code was written; its §0 root-cause investigation
  is not repeated here in full — read it for the complete reasoning behind
  candidate selection.
- Final diff (landed): `runners/dsl/src/py.rs` (+30 net, one new
  `#[pymethods]` fn), `substrate/world_adapter.py` (+9/-2, one call-site
  swap + comment), `domains/architecture_assessment.py` (+21/-4, one type
  filter), plus the rebuilt `.so`. `runners/dsl/src/grammar_reflect.rs`
  and `runners/dsl/src/substrate.rs` — untouched, as required.

---

## 1. AR1 — root-cause investigation

**Finding, confirmed by reading `substrate/world_adapter.py:6119-6223`, not
inferred:** `save()` writes two independent Γ representations —
`"graph"` (the full `TypedGraph` dump, which includes any `GammaGrammar`/
`GammaProduction`/`GammaNodePattern` mirror nodes IF any exist) and
`"grammar"` (`grammar_to_json()`, a separate `jsonio.rs`-serialised
snapshot of `checker.grammar` itself). `load()`'s `graph_from_dict` call
restores `inner.graph` but **never touches `inner.checker`** (confirmed by
reading `py.rs:7923-7930`) — so the replay loop
(`for p in blob["grammar"]["productions"]: s._inner.add_production(p)`)
is the *only* thing that repopulates `checker.grammar`, the struct
`check_edge` actually reads. **This answers the brief's question
directly: the replay is re-deriving from the separate
`grammar_to_json`/`jsonio.rs` persistence path, not re-walking seed
manifests** (no seed loading happens in `load()` at all) **and not
redundant with the graph dump** (which cannot restore a plain Rust struct
by itself). The replay is load-bearing; it cannot be deleted.

**Why the bug is invisible on `main` today.** The unrerouted
`PySubstrate::add_production` (`py.rs:7803-7820`, unchanged before this
rung) is `checker.grammar.add(p)` only — no mirror write. Replaying it N
times per load is graph-inert (though it does silently accumulate
duplicate `Production` entries inside `checker.grammar` itself on every
load — a separate, pre-existing, harmless-to-`self.graph` inefficiency,
out of this rung's charter, not touched). The growth bug requires the
general binding to be mirroring, which it is not on `main`.

**Three candidates evaluated (full reasoning in the PREREG's §0.3-0.4):**

- **(a) Restore `checker.grammar` from the graph's own mirror via
  `grammar_from_graph`.** Rejected: correct only once every persisted
  production was mirrored through the reroute — on `main` today, or for
  any checkpoint saved before a future reroute, this would silently
  restore an EMPTY grammar (total admissibility loss), worse than the bug
  it replaces. Requires a new PyO3 exposure of `grammar_from_graph` plus a
  migration path for pre-reroute checkpoints — real, but bigger, and
  **not safe to build independently of the reroute landing atomically**.
- **(b) Content-dedup the mirror before minting.** Rejected as more
  machinery than the problem needs: would require walking the existing
  mirror (via the same not-yet-exposed `grammar_from_graph`) and comparing
  every replayed production against it.
- **(c) Selected.** Give `load()`'s replay a dedicated, mirror-free PyO3
  method (`add_production_no_mirror`) — literally the CURRENT
  `add_production` body, moved to a new name. Zero `substrate.rs`/
  `grammar_reflect.rs` changes, zero dependency on whether/when the
  reroute lands, byte-identical restored `checker.grammar` content.

**Residual named, not fixed (PREREG §0.5, out of file-scope):**
`Substrate::gamma_graph_root` is not restored by `graph_from_dict`, so a
NEW production added post-load (e.g. `ensure_instance_edge_type`, a normal
runtime call) would, under a rerouted engine, mint a second, disconnected
`GammaGrammar` root rather than reusing the restored one. This is inert on
every live code path today (`grammar_from_graph`/`gamma_graph_root()` are
called from no production Python code) and does NOT reproduce the measured
growth bug (that bug is about replaying EXISTING productions; this is
about ONE new production correctly costing ~5 nodes once). Sizing for a
future rung: a `Substrate::reconcile_gamma_graph_root` scanning for an
existing `GammaGrammar` node post-`graph_from_dict`, PyO3-exposed, called
from `load()` — ~20-30 Rust lines, requires `substrate.rs`, outside this
rung's scope.

---

## 2. AR2 — `detect_god_object` fix

**Landed** (`domains/architecture_assessment.py`): a module-level
`_GAMMA_MIRROR_TYPES` tuple + `_is_graph_machinery_type()` helper,
following the exact precedent already used throughout
`substrate/world_adapter.py` for excluding `Term.*` graph-machinery nodes
from population-facing logic (e.g. line 6949: "Term.* are graph machinery,
never instanced"). `all_nodes` is now filtered before computing
`mean`/`std`/`cutoff`.

**Bar met:**
`tests/test_analogical_relative_ranking.py::test_same_count_flagged_or_not_depending_on_distribution`
passes on the landed (unrerouted) engine (no-op — no Gamma/Term nodes
exist without the reroute, so behaviour is byte-identical to before this
fix) **and** on the AR4-reconstructed rerouted engine (§4 below), where
the 192-production `_substrate()` fixture mints ~960 mirror nodes and the
filter is what keeps the outlier statistic correct.

---

## 3. AR3 — the load-growth fix

**Landed:**

1. `runners/dsl/src/py.rs`: new `#[pymethods] fn add_production_no_mirror`
   on `PySubstrate`, structurally identical to `add_production`'s current
   body (`grammar_from_json` → `inner.checker.grammar.add(p)` per parsed
   production), never calling the mirroring Rust-inherent
   `Substrate::add_production`.
2. `substrate/world_adapter.py:6171`: `s._inner.add_production(p)` →
   `s._inner.add_production_no_mirror(p)`.

**B1 — content-fidelity, live-verified:**

```
s2.grammar_to_json() == {'productions': [{'edge_type': 'e', 'provenance': 'p2',
  'src': {'type': 'A', 'var': 'src'}, 'tgt': {'type': 'B', 'var': 'tgt'},
  'weight': None, 'where': None}]}
```
— exactly the production passed in, same order, same fields.

**B2 — zero redundant growth, live-verified, landed (unrerouted) engine:**

```
750 751
750 751
750 751
750 751
750 751
750 751
```
6 consecutive save/load cycles, flat (matches the unrerouted-engine
baseline behaviour the prior rung's own reproduce script showed —
"with the baseline engine this sequence is flat").

**B2, the actual fix demonstration, under the AR4-reconstructed rerouted
engine (§4's sha256 `5fa3bbb1...`)** — this is the scenario that was
previously broken:

```
1011 1011  gamma-mirror present: True
1011 1011  gamma-mirror present: True
1011 1011  gamma-mirror present: True
1011 1011  gamma-mirror present: True
1011 1011  gamma-mirror present: True
1011 1011  gamma-mirror present: True
```
Flat across 6 cycles, WITH a real `GammaGrammar` mirror present (confirming
`ensure_instance_edge_type`'s own `add_production` call correctly mirrors)
— versus the prior rung's measured **+261/+260 every cycle, no
convergence**. The fix eliminates the specific compounding-replay
mechanism; genuinely new productions between saves still correctly cost
mirror nodes once (not exercised by this flat-world script, not eliminated
by design — see PREREG §3 B2's explicit scope note).

**B3 — admissibility unchanged, live-verified** (unrerouted engine):
`add_production_no_mirror`-restored production gates `add_edge`
identically — admissible edge succeeds, `add_edge(a, "links_to", c)`
(not covered by any production) raises `InadmissibleEdge`, both before
and after this rung's change.

---

## 4. AR4 — PyO3 reroute reconstructed and re-measured (validated, NOT merged)

Reconstructed `GAMMA_PYO3_REROUTE_PREREG.md` §3's exact one-line-per-call
change (`PySubstrate::add_production`'s general binding:
`inner.checker.grammar.add(p)` → `inner.add_production(p)`) on top of
AR2+AR3, built (sha256 `5fa3bbb1...`), and live-verified:

- Mirror write via the PyO3 path: `graph_to_dict()` shows
  `['GammaGrammar', 'GammaNodePattern', 'GammaProduction', 'Term.Lit']`
  after a single `s.add_production({...})` call.
- `gamma_epoch.bump()` fires: `jit_report()` epoch component `0 → 1`
  across the same call (previously silently bypassed, per
  `GAMMA_REFLECTION_WIRING_RESULTS.md` §2.2 item 1).
- `ConsistencyChecker.grammar`/`check_edge` unchanged: admissible edge
  succeeds, inadmissible edge correctly raises `InadmissibleEdge`.
- **The load-growth bug is gone** (B2 above, 1011/1011 flat × 6 cycles,
  with the mirror genuinely present — this is the direct fix
  demonstration).
- **The `detect_god_object` regression is gone:**
  `test_analogical_relative_ranking.py::test_same_count_flagged_or_not_depending_on_distribution`
  passes.
- **The other §2.5 regression target is gone:**
  `test_persistence_migrated.py::test_round_trip_is_faithful` and
  `test_rules_checkpoint.py::test_old_checkpoint_without_rules_key_loads_with_warning`
  both pass.

**Full regression sweep, same 105-file union (96-file `add_production` set
+ 10-file `WorldAdapter.load` set, deduped) `AR5` used, paired against the
AR2+AR3-only run (identical source except the one reroute line):**

- AR2+AR3-only: `17 failed, 1361 passed, 1 skipped, 1 error` (422.65s /
  427.62s across two runs, identical red set both times).
- AR2+AR3+reroute: `18 failed, 1360 passed, 1 skipped, 1 error` (684.48s).
- **Diff: exactly ONE net-new red**,
  `tests/test_rust_engine_parity.py::test_graph_round_trip_via_dict`
  (`assert s2.node_count() == 2` → actual `7`) — the PREREG's own §0.5 and
  the prior rung's own §0.5/§2.3 prediction, confirmed exactly: the
  mirror's 5 nodes (1 `GammaGrammar` + 1 `GammaProduction` + 2
  `GammaNodePattern` + 1 `Term.Lit`) now correctly appear in a round-trip
  dump. No other test in the 105-file set changed verdict in either
  direction (`comm -13`/`comm -23` on the sorted red-id sets, both empty
  except the one line above).
- **Independently confirmed (run directly, not part of the 105-file set,
  because it isn't seeded by a literal `add_production(` call in its own
  body — it's seed-boot-driven via `load_seed_manifest`):**
  `test_photon_eye_held_prediction_migrated.py::test_opt_in_adds_exactly_one_graph_cell_per_receptor`
  also breaks, exactly as the prior rung's §2.3 classified it
  (`assert 138 == 130` — the enabled/baseline node-count-difference formula
  needs a mirror-overhead term). Both are the exact two "honest count
  update" cases the prior NO-GO rung already predicted and classified —
  **no new, unexplained regression class appeared.**

**AR4's own GO bar is therefore met.** The reroute mechanism is correct,
complete, and — on top of AR2+AR3 — safe. It is not in this rung's final
commit anyway, for a reason orthogonal to its own correctness: **landing
it here would leave two previously-green tests red**, and this rung's
declared file-scope excludes editing test files to bump their literal
counts. That is a two-file, two-line follow-up
(`tests/test_rust_engine_parity.py:149`,
`tests/test_photon_eye_held_prediction_migrated.py:117` — exact expected
values already measured above), explicitly sized here rather than bundled
into a rung whose charter was the load-growth/`detect_god_object` fixes.
The `py.rs` one-line reroute diff itself was reverted before the final
commit (§0's two identical rebuild hashes confirm the revert left zero
residual).

---

## 5. AR5 — full regression (landed AR2+AR3 engine, sha256 `81d75c0a...`)

- **`cargo test --lib`** (debug, `--test-threads=1`): **740 passed, 0
  failed, 4 ignored** — identical to both prior rungs' own final numbers.
  Not independently re-paired against a from-scratch baseline `cargo test`
  run: the `py.rs` addition is entirely a new sibling `#[pymethods]` fn,
  invoked only through the Python extension module; no existing Rust test
  exercises it or the (unchanged) general `add_production` body.
- **105-file union** (96 files with a literal `add_production(` call +
  10 files touching `WorldAdapter.load`), run twice against the landed
  engine, paired against a freshly rebuilt pristine baseline
  (sha256 `f87f857c...`, same source `3e3daa5`):

  | Run | Result |
  |---|---|
  | AR2+AR3 changed, 1st pass | `17 failed, 1361 passed, 1 skipped, 1 error` (422.65s) |
  | AR2+AR3 changed, 2nd pass (post AR4-revert rebuild) | `17 failed, 1361 passed, 1 skipped, 1 error` (427.62s) — **identical red-id set to the 1st pass** |
  | Pristine baseline, targeted re-run of the 18 flagged node ids only | `17 failed, 1 error` — **identical red-id set** |

  **Zero regressions, paired failing-node-id lists (not counts), 18/18
  identical across all three runs:**
  ```
  tests/test_codec_graph_resident.py::test_hevc_pps_tile_array_bump_via_ffmpeg
  tests/test_codec_graph_resident.py::test_hevc_scaling_list_custom_matrix_branch
  tests/test_codec_graph_resident.py::test_hevc_scaling_list_data_round_trip
  tests/test_codec_graph_resident.py::test_hevc_sps_conformance_window_bump_via_ffmpeg
  tests/test_codec_graph_resident.py::test_hevc_sps_extended_fields_decode
  tests/test_codec_graph_resident.py::test_hevc_sps_prefix_full_grammar
  tests/test_codec_graph_resident.py::test_hevc_sps_scaling_list_bump_via_ffmpeg
  tests/test_codec_graph_resident.py::test_loop_fixed_count_literal
  tests/test_curious_agent_vision_graph_migrated.py::test_agent_can_count_its_visual_receptors_by_class
  tests/test_curious_agent_vision_graph_migrated.py::test_agent_can_inspect_receptor_spectral_state
  tests/test_curious_agent_vision_graph_migrated.py::test_agent_can_introspect_receptive_fields_via_dsl
  tests/test_curious_agent_vision_graph_migrated.py::test_existing_vision_pipeline_still_drives_attention
  tests/test_curious_agent_vision_graph_migrated.py::test_vision_built_on_first_frame
  tests/test_curious_agent_vision_graph_migrated.py::test_vision_projection_nodes_match_n_azimuth
  tests/test_curious_agent_vision_graph_migrated.py::test_vision_substrate_excluded_from_persistence
  tests/test_render_llvm_migrated.py::test_p4_artifact_chain_max_of_two_and_synthesized_loop
  tests/test_rust_engine_ext_7c.py::test_run_rules_transitive_closure_reaches_fixed_point
  tests/test_speech_semiotics.py (collection error)
  ```
  All 18 are PRE-EXISTING, unrelated to this rung (confirmed by identical
  failure on the pristine, untouched-source baseline): vision/`cv2` and
  `av` optional-dependency gaps, HEVC codec decode failures, a missing
  `results/prog_construction_scan.json` fixture, and a `run_rules`
  fixpoint step-count assertion — none call `add_production` or
  `WorldAdapter.load` in their failing path, and all were already red on
  `main` before this rung touched anything.
- **`WorldAdapter.load`/checkpoint-specific tests** — explicitly re-run:
  `test_persistence_migrated.py`, `test_rules_checkpoint.py`,
  `test_rust_engine_parity.py`, `test_analogical_relative_ranking.py`: **20
  passed, 0 failed** on the landed engine.

---

## 6. Everything that broke, and what didn't

- **Broke nothing** on the landed AR2+AR3 engine — 18/18 identical
  pre-existing reds against a from-scratch pristine baseline rebuild, plus
  a clean `cargo test --lib`.
- **AR4 (not landed) broke exactly the two pre-classified, pre-predicted
  tests** named in §4 — no surprises, no unexplained values, both
  traceable to the mirror becoming real for calls that previously weren't
  mirrored, exactly matching the prior NO-GO rung's own §2.3 classification
  methodology.
- The `divergence.json` fixture note from the reflection-wiring rung
  (`tests/fixtures/comprehension_divergence/divergence.json` gets a
  timestamp-only rewrite from an unrelated test on every full-suite run)
  applies here too — checked, confirmed unrelated, `git checkout --` run
  before the final commit.

---

## 7. Remaining uncertainties

- **`gamma_graph_root` post-load fragmentation** (§1's residual) is named
  and sized but not fixed — it requires `substrate.rs`, outside this
  rung's file-scope, and is inert on every current live code path.
- **AR4's two test-literal updates** are measured exactly (§4) but not
  applied (test files outside file-scope) — a mechanical two-line follow-up
  a future rung with test-file scope should bundle with the reroute itself
  so both land in one atomic, green commit.
- **`checker.grammar` duplicate-entry accumulation on repeated load()**
  (named in §1, pre-existing, NOT part of either prior rung's own
  charter): each `load()` call still appends `blob["grammar"]
  ["productions"]` into `checker.grammar` without checking whether an
  equivalent `Production` is already present, so `checker.grammar`'s own
  `Vec` grows (wastefully, not incorrectly — `check_edge` still gates
  correctly, just via a longer linear scan) across repeated save/load
  cycles, independent of the graph-node growth this rung fixed. Not
  measured quantitatively here (out of charter — the brief's charter was
  specifically the GRAPH growth bug); worth a future rung's own
  measurement if `checker.grammar` size becomes a `check_edge` latency
  concern at long-running-daemon scale.
- A full, unscoped `pytest -k migrated` (the ~9800-outcome, 3+ hour run the
  reflection-wiring rung ran once) was **not** re-run here, for the same
  reasoning the reroute rung itself gave for skipping it: the 105-file
  union already covers every literal `add_production` call site plus every
  `WorldAdapter.load` site, the two regressions this rung fixes were both
  found and fully characterized within that scope, and a 3-hour run on
  this shared, home-infrastructure-hosting box was not warranted to
  re-confirm an already-established, narrowly-scoped result.

---

## 8. Reproduce

```bash
cd /home/matt/ocelot-gamma-load-growth-fix/runners/dsl
export PATH="/home/matt/.cargo/bin:$PATH"
export RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"
CARGO_BUILD_JOBS=2 systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  cargo test --lib -- --test-threads=1        # 740 passed, 0 failed, 4 ignored

cd /home/matt/ocelot-gamma-load-growth-fix
python3 -m venv .build-venv && source .build-venv/bin/activate
export VIRTUAL_ENV=$PWD/.build-venv
cd runners/dsl
CARGO_BUILD_JOBS=2 systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  maturin develop --release --skip-install
```

Live demonstration — the fix (landed, unrerouted engine — flat, matching
pre-fix baseline behaviour since the bug never manifests without the
reroute):

```python
import sys, tempfile, os
sys.path.insert(0, "runners/dsl/python")
from substrate.world_adapter import WorldAdapter

wa = WorldAdapter()
a = wa.ensure_world_instance("Rock", "rock_1")
b = wa.ensure_world_instance("Rock", "rock_2")
wa.ensure_instance_edge_type("near")
wa.s.add_edge(a, "near", b)

tmp = tempfile.mkdtemp()
cur = wa
for i in range(6):
    path = os.path.join(tmp, f"ckpt_{i}.json")
    cur.save(path)
    cur = WorldAdapter.load(path)
    print(cur.s.node_count(), cur.s.edge_count())
# 750,751 -> 750,751 -> ... flat, 6 cycles
```

To reproduce AR4's validation (reroute + both fixes — NOT the committed
state), apply the one-line `py.rs` change `GAMMA_PYO3_REROUTE_PREREG.md`
§3 describes (`inner.checker.grammar.add(p)` → `inner.add_production(p)`
inside the general `add_production` method only — leave
`add_production_no_mirror` untouched), rebuild, and re-run the same script
above: the sequence becomes `1011,1011` flat with `GammaGrammar` present in
`graph_to_dict()`, versus the prior rung's measured `+261/+260` per cycle
without this rung's fix underneath it.
