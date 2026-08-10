# Python `substrate/` → Rust `substrate_rs` migration map

Goal: retire the legacy pure-Python `(G,Γ)` engine (`substrate/*.py`) so the
agent runs entirely on the Rust runtime (`substrate_rs`). This is the end
state CLAUDE.md already mandates ("Python `substrate.Substrate` / `TypedGraph`
— being deleted; the wrapping shim survives until the last call site
migrates").

**Status:** ~93 files imported the Python substrate. **68 sites remain.**
Done: `stt_pipeline`, `lexical_access`, `compositional_chunking`, `reconsider`,
`sonority_valley`, `transcoding`, `build_elf`, `transcription_pipeline`,
`transcoding_pipeline`, `llvm_pass_compiler` (+test), and the Wave 4a reasoning
domains on the native rule engine + `Substrate.search`: **`equation`**,
**`topology`**, **`language`**, **`linear_algebra`**, **`audience`**,
**`communicate`**, **`representation`**, **`probability`** (+ consumer `reason`;
`test_more_floors` now fully native). Nine self-contained reasoning floors are
done — the recipe is mechanical. The remaining 68 are the hard cluster (below). The consumer-driven floors
(`audience`/`communicate`/`linear_algebra`) follow one recipe: a `new_graph()`
factory with a permissive Γ grammar for the schema, `_insert_node`→`add_node`,
`out_edges`→`neighbours`, `node().attrs`→`node()["attrs"]`,
`_delete_edge(EdgeKey)`→`remove_edge`, and the test's `TypedGraph()`→
`<module>.new_graph()`. Shared-graph layers (communicate uses audience) register
the union grammar.

### Wave 4a STARTED — the wheel was rebuilt; the Rust rule engine is live

The Rust-native rule engine (`add_rule`/`apply_rule_once`/`run_rules`/`tick`)
was fully written in the in-tree WIP but not in the installed wheel. **Rebuilt
the wheel** (`maturin build --release` + force-reinstall with
`--break-system-packages`; the `.so` was backed up to `/tmp/substrate_rs_BACKUP`
first). Verified **regression-free**: key suites identical to baseline (163
pass / 4 fail — the 4 are the legacy-Python `term_from_subgraph` bug); the codec
sweep is 30-fail/71-pass on BOTH the old and new `.so` (environmental: ffmpeg/
x265). NB the rule engine lives on `_native.Substrate`, not the higher-level
`substrate_rs.Substrate` wrapper.

**`equation` ported + verified** (`test_equation` 4/4) — the recipe for the
remaining `make_rule`+`run` domains:
1. Rust `Substrate.add_node` checks Γ-admissibility (Python `TypedGraph` used
   unchecked `_insert_node`). There is NO `add_node_unchecked` → register a
   permissive grammar first (open `add_production` over the schema's type/edge
   combos; see `equation._new_graph`).
2. `make_rule(match, where, effects)` → `add_rule({name, match, where:
   term.to_dict(), effects})`. `term_to_json` == `.to_dict()`, byte-identical.
3. Attr values: the Rust attr Value is int/float/str/bool — it coerces a Python
   `Fraction` to f64, losing exactness. Store exact rationals as **strings**,
   parse back in Python (no rule inspects the value).
4. `run_rules()` runs ALL installed rules; for *run-only-this-rule* semantics
   (e.g. `topology.connected_components`) loop `apply_rule_once(idx)` to a
   fixed point.
5. TypedGraph API → Substrate API: `_insert_node`→`add_node`, `_insert_edge`→
   `add_edge`, `node(n).attrs`→`node(n)["attrs"]`, `out_edges(n,e)`→
   `neighbours(n,e)` (returns targets).

**Remaining Wave 4a:**
- `language` — DONE (test_language 13/13). The rule-engine path (comprehend /
  lex, with computed-attr effects, `None`/`Lit(None)`, two-phase lexical+cleanup
  via `apply_rule_once`, and Merge composition) is fully native. Its 3
  *lexicon-storage* helpers (`make_lexicon`/`learn_sign`/`signs_from_graph`)
  still use the generic `_insert_node` API because `curious_agent` calls them
  with its TypedGraph `mind_graph`; they carry no python-substrate import and
  migrate when the agent's graph does. (`test_self_integration` has 4 PRE-
  EXISTING failures from the legacy `term_from_subgraph` bug in
  `curious_agent.word_meaning` — identical on the original file; not from this
  work.)
- `topology` — DONE. Added a `new_graph()` factory; `test_more_floors` now uses
  it; decoupled `test_graph_rewrite._count_colorings` by inlining the small
  complex-builder (that test exercises the Python *search* layer, so it stays on
  TypedGraph). Used `apply_rule_once(idx)` loop for run-one-rule reachability.
  NB: `test_graph_rewrite` has 2 PRE-EXISTING issues (a tuple/list assert in
  `test_rule_is_graph_resident`; `test_transpose…` runs to max_steps and
  hangs) — confirmed present on the BACKUP wheel too, not from this work.
- `linear_algebra` — DONE (fully native). `_determinant_grid`/Cramer solve ride
  `Substrate.search`; `matmul` now uses `add_rule` + `apply_rule_once` — and the
  native rule engine **FIXED** `test_matmul_and_trace` (was producing `[[0,0]]`
  on the Python `graph_rewrite`, now `[[19,22],[43,50]]`). `make_matrix`/`read`/
  `trace` on the native API + a `new_graph()` factory; `test_linear_algebra` 4/4.
  Consumer `reason._mat` repointed to `la.new_graph()`, which cleared `reason`'s
  only Python-substrate import (TypedGraph) — `reason` is now off the package too.
- `fp_group` — STILL BLOCKED on the search side: its `search_count_general` uses
  a Python `apply_option` that computes the rule binding from precomputed dicts
  (slot/inv/num) — not expressible as a fixed `assign_edge`. Needs either a
  rule-based `Substrate.search` variant (apply a named Rule with a computed
  binding + undo) or a graph-resident refactor of Todd–Coxeter.

### The native search primitive (Rust)

`Substrate.search(open, options, assign_edge, fail=None, value=None,
accept=None, env=None)` in `runners/dsl/src/py.rs`: DFS-with-undo where the
strategy is graph-resident Terms — `open` yields undecided items, the search
adds `assign_edge` from the lowest-id open item to each `options` candidate,
recurses, then deletes (backtrack); `fail` prunes, `accept` gates a leaf;
`value` None ⇒ COUNT solutions, else SUM that Term over leaves. Two gotchas hit
+ fixed during the build: (1) `evaluate` mutates env as a scratch stack, so each
eval must clone the (small, constant) base env — sharing one `&mut env` across a
level's fail/open/options evals corrupts it; (2) `Neighbours`/`Filter` return
`Value::FrozenSet`, NOT `Value::Set` — the node extractor must match both.
- `intent` — Production-object coupled (Wave-4 reclassified).
- Delete `graph_rewrite.py` only once all dependents are off it.

### Refinements learned by executing Waves 0/1/3 (the map was too optimistic)

1. **"Term-only" ≠ "Rust-ready."** The real discriminator is whether a file
   builds **`Production()`/`NodePattern()` OBJECTS** that get fed into a
   **Python** `Substrate`/grammar. `substrate_rs.Production` has no `.admits()`,
   so those break (`'Production' object has no attribute 'admits'`). Files that
   only **serialize Term-trees to JSON** (`.to_dict()`) or **evaluate** via
   `substrate_rs` are safe. **Reclassified Wave-0→Wave-4** (engine-tier):
   `agent_tools, conversation, intent, llm_partner, psychology` — they emit
   grammar productions as objects; migrate them only when their consumers/tests
   move to `substrate_rs`.
2. **`term_to_json` →** keep call sites unchanged with a 1-line module shim
   `def term_to_json(t): return t.to_dict()`; only the import changes.
3. **Wave 2 is BLOCKED, not low-risk** — each file depends on something bigger:
   `viz/server` needs `GammaLearner` (port the learner → Wave 4); `capture_seed`
   needs the agent seed `REGISTRY` (Wave 4); `shared_chess` needs genuinely-new
   Rust `term_to_subgraph`. Defer all three.
4. **Wave 3 needed NO rebuild.** The bit-ops (`BitAnd/BitOr/BitXor/Ashr/Shl/
   IDiv/IRem/Lshr`) already exist in `term.rs` + the in-tree `substrate_rs`
   Python layer (WIP); the installed wheel is just stale. Since
   `llvm_pass_compiler` only *constructs + serializes* them (rules go to
   `Substrate.add_rule` as JSON; not evaluated in Python), a forward-compatible
   `try: from substrate_rs import … except ImportError: def …(_Term)` bridge
   works on the stale wheel today and auto-uses native exports after a rebuild.
5. **Wheel rebuild deferred.** The whole Rust source is **untracked WIP** and
   `pipeline_runtime.rs` has 175 uncommitted lines. `cargo check` is clean, but
   a rebuild bakes that WIP into the installed `_native` with **system-wide
   blast radius** — not worth it for the remaining Rust-gated files. Do it
   deliberately, with the `.so` backed up first.

Method is proven (see the speech-path migration): `substrate_rs` Terms
serialize via `.to_dict()` **byte-identically** to `substrate.term_to_json`,
so Term-only files are mechanical renames.

---

## What `substrate_rs` already provides vs what's missing

**Present (90 exports):** every DSL Term class (And/Attr/Lit/Var/Eq/Filter/
Count/Neighbours/Not/Or/Plus/Minus/Times/Div/Mod/Gt/Gte/Lt/Lte/In/Exists/
IfThenElse/TypeOf/Sum/SetT/Pick/Holds/MapNeighbours/Cat/Surface/Dot/
Magnitude/VecSub/MaxOver/MinOver/Render/Slot/…), `Term`, `Production`,
`NodePattern`, `NodeID`, `InadmissibleEdge`, module `encode`/`decode`, and
`Substrate` with a full engine API (`add_node/add_edge/add_production`,
`tick`, `evaluate`, `neighbours/in_neighbours`, `graph_to_dict/from_dict`,
`load_seed_manifest`, `grammar_to_json`, `define_concept`,
`admissible_moves`, `is_edge_admissible`, …).

**MISSING — gating Rust work that must land before the waves that need it:**

| Missing symbol(s) | Used by | Fix |
|---|---|---|
| `TypedGraph`, `Grammar`, `ConsistencyChecker`, `EdgeKey` | engine wave (49 sites) | No standalone Rust class — their behaviour lives **inside** `Substrate`. These sites need an **API port**, not a rename. |
| `term_to_subgraph`, `term_from_subgraph` | SERIAL wave (4 sites) | Add Rust graph↔Term storage, or a Python adapter over `Substrate` graph ops. **The `agent_speech` `term_from_subgraph` bug lives here.** |
| `grammar_from_json` | SERIAL (3) | `Substrate` has `grammar_to_json` but no inverse — add it. |
| `Ashr`, `BitAnd`, `BitOr`, `BitXor` (and `Shl`/`Shr`) | `llvm_pass_compiler` | Add Term variants in `runners/dsl/src/term.rs` + evaluator + PyO3, rebuild wheel. |
| ~~`search_count` / `search_sum`~~ | `linear_algebra`, `fp_group` | **DONE** — added the native `Substrate.search(open, options, assign_edge, fail, value, accept, env)` in `py.rs` (DFS with undo; strategy = graph-resident Terms). Handles the fixed-`assign_edge` form (determinant, colourings). `fp_group`'s general search has a Python `apply_option` (dict lookups) → still needs a rule-based search variant or a graph-resident refactor. |

**Second coupling axis — `graph_rewrite` (Python rule engine):** 8 domains
import it (`equation, language, linear_algebra, intent, topology, fp_group,
phonology, curious_agent`) — **including the live `phonology` and `intent`**,
even though those don't `import substrate` directly. CLAUDE.md: it "is being
replaced by Rust `tick()`." Migrating it is a prerequisite for those 8.
**First check whether `phonology`/`intent` use it live or vestigially** (the
speech dev loop already runs on `substrate_rs.tick()`).

---

## Migration waves (file-level)

### Wave 0 — mechanical, Rust-ready TODAY (proven method). ~12 files.
Same edit as the speech-path migration: `from substrate import X` →
`from substrate_rs import X`; `term_to_json(t)` → `t.to_dict()`. Verify rule
serialization is byte-identical where Rules are built.
- **rename only (7 domains + 1 script):** `agent_tools, audio_world,
  chat_world, conversation, intent, llm_partner, psychology`,
  `scripts/build_elf`
- **rename + `.to_dict()` (4 domains):** `compositional_chunking, reconsider,
  sonority_valley, transcoding`
- Risk: low. Each ~5–15 min. (`intent` also touches `graph_rewrite` — see Wave 4a.)

### Wave 1 — seed loaders. 3 domains.
`seed_registry, transcoding_pipeline, transcription_pipeline`. Replace
`substrate.seed_loader.manifest_for` with the `_manifest_for` JSON adapter
(as in `stt_pipeline`) and `seeds.load_seeds/REGISTRY/Seed` with a thin
pure-Python registry adapter (it's file I/O) or `Substrate.load_seed_manifest`.
Risk: low.

### Wave 2 — serialization shims. 1 domain + 2 infra. **Needs Rust work.**
`shared_chess`, `tools/capture_seed`, `viz/server`. Requires
`term_to_subgraph`/`term_from_subgraph` + `grammar_from_json` in Rust (or a
Substrate-graph adapter). **Land the `term_from_subgraph` fix here — it also
clears the 7 `agent_speech` failures** once that faculty stops using the
Python path. Risk: medium (Rust + serialization correctness).

### Wave 3 — missing primitives. 1 domain. **Needs Rust + wheel rebuild.**
`llvm_pass_compiler` uses `Ashr/BitAnd/BitOr/BitXor`. Add the Term variants in
Rust, rebuild the wheel. Risk: low logic, but a build step (do NOT bundle
unrelated uncommitted Rust changes).

### Wave 4 — the engine core. 26 domains + ~23 tests. **The 80%.**
These instantiate `TypedGraph + Grammar + ConsistencyChecker` directly — an
**API port to `substrate_rs.Substrate`**, not a rename. Sub-order:

- **4a. `graph_rewrite` → `Substrate.tick()`** (keystone; unblocks 8
  dependents incl. live `phonology`/`intent`). CLAUDE.md explicitly wants
  this. First: audit `phonology`/`intent` for live vs vestigial use.
- **4b. reasoning / math domains** (several still live, have passing tests):
  `equation, linear_algebra, number_world, fp_group, reason, topology,
  probability, sequence_infer, ca_infer, representation, language`.
- **4c. `curious_agent`** (~13K lines). CLAUDE.md says "being deleted." No
  domain imports it (leaf); its consumers are scripts, and the live harness
  (`develop.py`) already uses cortices, not `CuriousAgent`. Likely **delete +
  point remaining scripts at the cortex harness**, not port.
- **4d. legacy worlds** (dormant experiments): `chess, conway, doom_world,
  collision_world, harvest_world, lever_world, meta_chess_world,
  multi_game_world, physics_world, structure_world, walker_world` — port to
  `Substrate` or archive. Decide per-world; several have no live consumer.
- **4e. tests:** the 44 test sites largely test the Python engine itself
  (TypedGraph/Grammar/ConsistencyChecker parity). They **retire or rewrite
  with their domain**; Rust already has `test_rust_engine_parity` et al.
  Lower priority — they don't block runtime.

---

## Recommended sequence

1. **Waves 0+1** now — ~15 mechanical files, zero new Rust, same verified
   method as the speech path. Biggest reduction for least risk.
2. **Wave 3** — small Rust add (bit-ops) unblocks `llvm_pass_compiler`.
3. **Wave 2** — Rust serialization + the `term_from_subgraph` fix; clears
   `agent_speech` once that faculty is repointed.
4. **Wave 4a** — `graph_rewrite`→`tick()`; audit live speech coupling first.
5. **Wave 4b** — reasoning/math domains (keep their passing tests green).
6. **Wave 4c/4d** — delete `curious_agent`; port-or-archive legacy worlds.
7. **Wave 4e** — retire/rewrite the Python-engine tests; delete `substrate/`.

**Done-when:** zero `from substrate import` / `import substrate` outside
`substrate/` itself, then delete the package.
