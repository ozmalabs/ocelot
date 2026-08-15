# Code map

A directory-by-directory map of the source tree, for a reader who knows
`CLAUDE.md`'s architecture rule (**the agent is a graph, running in Rust; Python
is only the world adapter**) and wants to know where each piece actually lives.
Line/file counts below were measured against the tree, not estimated — re-run
the obvious `find`/`wc -l` if they've drifted.

For narrative summaries of what each subsystem *does*, see `docs/features/`.
For the full historical record behind any of it, see `docs/research/`.

## `runners/dsl/` — the Rust substrate crate (`substrate_rs`)

The agent runtime. This is not a library the agent calls into — it *is* the
agent: the typed graph (G), the admissibility grammar (Γ), the Term-tree DSL
evaluator, the `run_rules` fixpoint engine, the reflex/tick scheduler, and
every primitive (audio/cochlea/FFT, video/codec, shape-decode/dynamic
quantization, space-quantize navigation, stroke/handwriting quantization,
JIT compile path) the graph can invoke.

- `src/` — 84 `.rs` files, ~106k lines. Notable modules: `graph.rs` /
  `graph_rules.rs` (G, Γ, the rule engine), `term.rs` (the DSL's Term
  variants), `rewrite.rs` (`run_rules` fixpoint), `shape_decode.rs` (the sd
  loop: decode / recognize / mint / transform / dim-infer — see
  `docs/features/dynamic-quantization.md`), `space_quantize.rs` (quanta
  navigation), `strokes.rs` (handwriting quantization), `substrate.rs` (the
  graph operations Python calls through), `py.rs` (the PyO3 binding surface
  — CLAUDE.md's rule: this file should be one-line handoffs, never logic),
  plus audio (`audio_primitives.rs`, `cochlear_nucleus.rs`,
  `auditory_cortex.rs`), video/codec (`h264_*.rs`, `cabac.rs`, `codec.rs`),
  and a small x86_64 JIT (`gpu_me.rs`/`gpu_me.wgsl` for the optional GPU
  motion-estimation path).
- `python/substrate_rs/` — the PyO3-generated Python package: `_native.abi3.so`
  (gitignored build artifact) plus thin Python wrappers (`audio.py`,
  `video.py`, `vision.py`, `speech.py`, `bitstream.py`, `communication.py`,
  `ext.py`) that mirror `substrate/dsl.py`'s Term-factory surface so callers
  can swap `from substrate import ...` for `from substrate_rs import ...`.
- `target/` — gitignored Cargo build output.
- `Cargo.toml` sets `codegen-units=1` + fat LTO for the release profile
  (benchmark fidelity); `.cargo/config.toml` caps `jobs = 4` because this box
  runs swap-heavy and a full-parallelism release build OOMs mid-compile
  (exit 137) — see that file's comment before "fixing" the job count back up.
- Build: `cd runners/dsl && maturin develop --release` (installs the
  extension module into the active Python environment).

## `domains/` — world adapters, seed-emitter scripts, capability classes

720 Python files, ~281k lines. Per CLAUDE.md this directory must stay
mechanical I/O — translating external events into substrate mutations and
back, never making an agent decision itself. In practice it holds three
kinds of file:

1. **World adapters** — one per simulated environment or sense (e.g.
   `eye_world.py`, `harvest_world.py`, `doom_pattern_eye.py`,
   `crossframe_world.py`). Each does ingest (events → nodes/edges) + emit
   (graph state → external effect), and calls `substrate.tick()` in
   between. No conditionals over graph state.
2. **Seed-authoring / emitter helpers** (`concept_expansions.py`,
   `concept_promotion_rules.py`, `self_authored.py`, ...) — Python that
   *emits* seed JSON, not Python that reasons at runtime.
3. **Capability classes with no agent decisions** — `ToolBox`, teacher
   classes, `GraphEye`, and similar; per CLAUDE.md's "what still exists in
   Python" section these are legal because they hold no agent state and make
   no decisions, only expose primitives.

`reflective_faculty.py` and `question_driver.py` also live here; per
CLAUDE.md (2026-07-02 migration) they are now thin shims over `ShapeDecode`
and the seeded rule loops, not where the reasoning happens.

## `domains_rs/` — parity-pinned Rust-backed domain mirrors

A small, newer sibling of `domains/`: each module here mirrors a `domains/`
Python file but builds its substrate on `substrate_rs` directly, parity-pinned
against the Python original via the test suite. Currently just `conway.py` —
watch this directory if more of `domains/` migrates onto the Rust substrate
API directly rather than through `substrate/world_adapter.py`.

## `worlds/` — newer world adapters (Bigville, ARC/LS20, affordance)

129 files. Architecturally identical role to `domains/`'s world-adapter files
(thin I/O translation — see `worlds/arc.py`'s own docstring, which states the
rule explicitly and says it supersedes `domains/arc3_thin`), but this is
where the Bigville town-simulation family (`bigville_*_world.py`, well over
80 files — actions, affect, bonds, building, church, commodities, council,
courts, drama, economy, ...) and the ARC-AGI/LS20 spatial-task family
(`arc_ls20_*.py`) live. New world adapters have been landing here rather
than in `domains/`.

## `substrate/` — the Python boot layer

The world-adapter-layer glue that turns seeds + the Rust engine into a
running agent. NOT the agent's reasoning (that's `runners/dsl/`'s job) — this
is assembly and I/O:

- `boot_core.py` (156 lines) — creates a bare `substrate_rs` substrate, adds
  the agent root, and loads the migrated core seeds (`decision_core`,
  `learning_core`, `perception_core`, `epistemics_core`, `motor_core`, ...)
  through the Rust seed loader. No `CuriousAgent` class; the agent is the
  loaded graph data.
- `boot_all.py` (816 lines) — the fuller seed-set boot path (adds
  conversation/perception/domain seeds on top of core).
- `seed_loader.py` (247 lines) — reads seed manifest JSON
  (`seeds/<id>.json`), resolves `depends_on` closures topologically,
  installs Concept/Rule/Reflex/Frame/Microtheory nodes.
- `world_adapter.py` — **10,142 lines**, by far the largest file in the
  tree. This is *the* world adapter CLAUDE.md's "what still exists in
  Python" section names explicitly: big, but (per that section's audit)
  every method is mechanical I/O or fires a seeded Term/Rule — perception,
  intent, conversation render, teaching, goals, planning, spatial routing
  all dispatch into the seed-booted graph rather than deciding anything in
  Python.
- `dsl.py`, `graph.py`, `grammar.py`, `checker.py`, `learner.py`,
  `persistence.py`, `primitives.py`, `rule_ir.py`, `weighted.py`,
  `jsonio.py`, `seeds.py` — the **legacy pure-Python `(G,Γ)` engine**.
  CLAUDE.md is explicit that this is retained only as a reference /
  world-graph-construction helper for tests; no agent runs on it — the agent
  runs on `substrate_rs`. See `docs/research/engine_substrate/` for the
  migration history (`SUBSTRATE_RS_MIGRATION.md`) that made the Rust engine
  canonical.

## `seeds/` — graph-data manifests

888 top-level `*.json` manifests (`seeds/<id>.json`), each a
`{Seed{id,version}, depends_on: [...], contains: [Concept/Rule/Reflex/...]}`
unit per CLAUDE.md's "seeds are modular with dependencies" section. A few
that map directly onto sections of CLAUDE.md: `conversation.json`,
`intent.json`, `psychology.json`, `relations.json`, `speech.json`,
`shape_decode_loop.json` (the sd/dynamic-quantization loop),
`quanta_navigation.json` (space-quantize flood), `gap_awareness.json`
(self-gap finding), `composer_dispatch.json`, `core_emotions.json`.

Subdirectories:
- `seeds/acquired/` — **~306k JSON files**, an auto-acquired
  grounding/knowledge cache (per-concept dictionary/wiki groundings the
  agent's teacher loop filed), not hand-authored seed data. This is why
  `seeds/` looks enormous by file count; it is not 300k hand-written rules.
- `seeds/generated/`, `seeds/procedural/`, `seeds/expansions/`,
  `seeds/self_authored/`, `seeds/code_authoring/` — smaller, similarly
  machine-produced categories (the `teach()` facility's per-category output,
  expansion packs, code-authoring lessons).

Seeds are almost always produced by an emitter script under `tools/`
(`tools/build_arc_executor_seed.py`, `tools/build_vision_lighting.py`,
`tools/build_crowding_seed.py`, ...) rather than hand-typed — the emitter is
legal Python (it assembles Rule/Concept JSON) even though the *result* is the
thing that runs.

## `scripts/` — one-off measurement / build / report scripts

2,437 files. The dominant convention across this whole research program: a
`*_PREREG.md` is committed *before* a change or measurement, a `scripts/*.py`
performs the build/measurement, and a `*_RESULTS.md` reports what happened —
"PREREG then measure," never edited after the fact. Also home to the
project's own gates/audits (`seed_claim.py`, `seed_audit.py`,
`seed_ledger_audit.py`, `failure_baseline.py`) and the `jabberwock_*.py`
family of scripts that run a specific measured session (e.g.
`jabberwock_daemon.py`, the long-running checkpointed agent process).

## `tools/` — seed-authoring / emitter scripts

64 files. Narrower than `scripts/`: these specifically *build* seed JSON
(`build_*_seed.py`, `author_*.py`) or audit seed authorship
(`term_ast_audit.py`, `guard_coalesce_lint.py`). Legal Python per CLAUDE.md
because the output is graph data, not runtime reasoning.

## `tests/` — the migrated gate suite

1,088 `test_*.py` files, of which 768 are `test_*_migrated.py` — the
convention `pytest tests/ -k migrated` selects. These are the tests that
gate the graph-native behaviour (as opposed to older, now-superseded
Python-vs-graph parity tests). `conftest.py` at the repo root pins the Rust
engine this tree's tests run against (`domains/engine_provenance.py`) and
sets `DEEPWRITING_DIR`/dataset-root defaults so tests read corpora from the
gitignored `data/` directory rather than `/tmp`.

## `web/` — viewers

- `web/index.html` + `app.js` + `mock_server.py` — a graph visualiser /
  interrogation frontend (`graph_interrogate.py`'s "ASK" counterpart to this
  "LOOK" viewer — see `docs/research/engine_substrate/`).
- Bigville's game client and town viewer now live in the standalone
  [`ozmalabs/bigville`](https://github.com/ozmalabs/bigville) repository. Ocelot
  retains only the substrate and explicit integration boundaries; it does not
  carry a duplicate Bigville renderer.

## Top-level non-source directories (not part of this reorg's scope)

`data/`, `results/`, `runs/`, `recordings/`, `.worktrees/`, `benchmarks/`,
`demos/`, `deploy/`, `protocols/`, `schemas/`, `naming_corpus/`,
`pronunciation_corpus/`, `repeating_corpus/`, `simulators/`, `var/`, `viz/` —
corpora, generated results, run logs, protocol definitions, and other
non-documentation trees. Untouched by the docs reorg this map accompanies.

## Documentation layout (this reorg)

- `README.md`, `CLAUDE.md`, `VISION_PROTOCOL.md` — repo root (see below for
  why `VISION_PROTOCOL.md` stays put).
- `docs/CODE_MAP.md` — this file.
- `docs/features/` — synthesized current-state summaries, one per major
  subsystem.
- `docs/meta/` — `SPEC.md`, `SCREENCAST.md`, `NOTICES.md`, `JABBERWOCKY.md`.
- `docs/research/<topic>/` — the full historical PREREG/RESULTS/plan corpus,
  grouped by subject; see `docs/research/INDEX.md`.
- `docs/attempts/`, `docs/literature/` — pre-existing subdirectories, left
  as-is by this reorg.

**Why `VISION_PROTOCOL.md` did not move.** Unlike every other `VISION_*.md`
document, this one is not a historical research note — it is the live,
actively-parsed burned-seed ledger. `scripts/seed_ledger_audit.py` hardcodes
`os.path.join(ROOT, "VISION_PROTOCOL.md")` and several gated tests reference
it by bare root-relative filename. Moving it would have required either
rewriting a live parsing path for a single, heavily-load-bearing file with no
real documentation-organization benefit, or accepting a subtle path-drift
risk — so it stays at root, alongside `CLAUDE.md` and `README.md`, as a
deliberate exception. See the "landmine" note in
`domains/seed_record.py`'s `PREREG_DIR` for the one path reference that *did*
need to move (`VISION_*_PREREG.md` documents, which relocated to
`docs/research/vision/` along with every other `VISION_*` research file, with
the scanner updated to match).
