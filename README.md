# OCELOT — a graph-native cognitive engine

**OCELOT** (Ozma Cognitive Engine: Logarithmic Objective Tower) is the
engine — the (G, Γ, C) substrate itself: a typed graph plus a reflective
admissibility grammar, executed by a Rust rule-matching runtime
(`substrate_rs`). **Jabberwock is the cognitive entity OCELOT enables** — the
agent that runs on this engine, not another name for the engine running it.
This repository is OCELOT: the substrate, not the entity.

**The agent is a graph, running in Rust.** OCELOT's substrate is an
implementation of the (G, Γ, C) substrate — a typed graph plus a
reflective admissibility grammar — where the agent's entire reasoning,
knowledge, and behaviour is graph data, executed by this same Rust
rule-matching runtime. Python exists only as a thin **world adapter**
layer: translating external I/O (text, audio, video, simulator state) into
graph mutations and back. There is no Python agent loop, no Python decision
tree over graph state, and no Python-resident "mind" — that architecture
(the old `domains/curious_agent.py` `CuriousAgent` class) was deleted
outright in 2026-06-18 (commit `56529c6d`) and is gone from this tree.

> **`CLAUDE.md` is the authoritative architecture rule for this repository.**
> It is longer and more detailed than this README, it is kept current as the
> project evolves, and if anything here ever conflicts with it, `CLAUDE.md`
> wins. Read it before writing code here.

## The shape of it

```
┌─────────────────────────────────────────────────────────┐
│  RUST AGENT RUNTIME  (substrate_rs, runners/dsl/)        │
│  • Substrate (G, Γ, C): typed graph + productions        │
│  • DSL evaluator: Term-trees → values                    │
│  • Rule engine: match + where + effects, run_rules fixpoint│
│  • Reflex loop: stimulus → response, tick scheduling      │
│  • Audio / speech / video / codec / JIT primitives        │
│  • The agent's reasoning AS GRAPH DATA: Rules, Concepts,  │
│    Microtheories, Frames, Reflexes, Productions           │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ ingest / tick() / query
              ┌─────────┴──────────┐
              │  world adapters     │  substrate/world_adapter.py,
              │  (Python, thin)     │  domains/*_world.py, worlds/*.py
              └─────────────────────┘
                        ▲
                        │ external I/O
                 text · audio · video · simulators
```

A **world adapter** does exactly two mechanical things: **ingest** (turn an
external event into substrate mutations — `substrate.add_node(...)`,
`substrate.add_edge(...)`) and **emit** (read graph state back out and
translate it to an external effect). Between the two it calls
`substrate.tick()` and lets the Rust engine do the actual reasoning. A world
adapter contains no `if`/`else` over graph state — any such conditional is a
Rule, and Rules are graph data, not Python.

## Seeds: the agent's knowledge is versioned, dependency-resolved graph data

The agent doesn't boot with one monolithic mind. A **seed** is a named,
versioned unit of graph data (`seeds/<id>.json`) — Concepts, Productions,
Rules, Reflexes, Microtheories, Frames — with explicit `depends_on` edges to
other seeds. An agent declares which seeds it wants; the boot layer
(`substrate/boot_core.py`, `substrate/boot_all.py`, `substrate/seed_loader.py`)
resolves the dependency closure and installs seeds in topological order via
 the Rust manifest loader (`runners/dsl/src/seed_manifest.rs`). A text-only
chat agent and a Doom-playing agent share the same Rust runtime and differ
only in which seeds they loaded.

When the agent is *taught* something new, it persists through the same
mechanism (`domains/teach.py`'s `teach()` facility): the fact lands in the
live graph, gets filed into the seed category the agent's own `RecogniseShape`
meta-shape classifier assigns it to (growing a new `MetaShape` when a
structural residual recurs), and is appended to that seed's manifest — so a
fresh boot includes it. `seeds/acquired/` (~306k small files) and
`seeds/generated/` (agent-authored seeds) are auto-grown caches, not
hand-authored seed data.

See **[`docs/SEED_DEVELOPMENT.md`](docs/SEED_DEVELOPMENT.md)** for the complete
guide to authoring seed manifests, writing `tools/build_*_seed.py` emitters,
declaring `Γ` productions, wiring the four-rung `ShapeDecode` Occam ladder,
and testing new seeds.

## Dynamic quantization — the core learning mechanism

Every capability in this tree — vision, handwriting, program synthesis,
spatial navigation, speech recognition — is an instance of one loop: an
observation is decoded against a held codebook of learned shapes; whatever
isn't covered is a residual; a residual that recurs mints a new codebook
entry, growing the codebook for the next decode. The `run_rules` fixpoint
*is* this decode → grow → re-decode loop; there is no Python iteration
driving it. See [`docs/features/dynamic-quantization.md`](docs/features/dynamic-quantization.md)
for the full mechanism (the four-rung Occam growth ladder: exact recognize →
transform in existing basis → infer missing dimension → mint novelty, plus
the frame/continuum invariant that keeps in-frame values integer while
cross-frame maps may be real-valued) and `docs/features/` generally for how
it shows up in each subsystem.

The separate bearer-authenticated OpenAI-compatible chat endpoint and its
copy-on-write user/session model are documented in
[`docs/features/OPENAI_COMPATIBLE_COW_API.md`](docs/features/OPENAI_COMPATIBLE_COW_API.md).

## Doing science research on the substrate

OCELOT is a **goal-using, not goal-seeking** research program: benchmarks are
targets used to measure and correct aim, and every empirical claim follows a
prospective **Pre-Registration (`*_PREREG.md`) → Measurement Script
(`scripts/*.py`) → Results (`*_RESULTS.md`)** workflow archived under
[`docs/research/`](docs/research/INDEX.md).

Before comparing experimental arms, every measurement must pass the
five-clause instrument gate (random-input floor, ideal-exemplar ceiling,
convergence on the formative distribution, alive-arm positive control, and
the `D = max|on − off| > 0` downstream load-bearing check), record its exact
Rust engine provenance (`domains/engine_provenance.py`), and claim
non-overlapping confirmatory RNG seeds in the burned-seed ledger
(`scripts/seed_claim.py`, `domains/seed_record.py`).

See **[`docs/SCIENCE_RESEARCH.md`](docs/SCIENCE_RESEARCH.md)** for the full
scientific methodology and operational handbook.

## Building

```bash
bash scripts/engine_build.sh
# Or for a Python-runtime-only rebuild without relinking Rust probe binaries:
bash scripts/engine_build.sh --lib-only
```

Under the hood, `cd runners/dsl && maturin develop --release` builds the
`substrate_rs` Rust extension, and `scripts/engine_build.sh` safely installs
`runners/dsl/python/substrate_rs/_native.abi3.so` using `cp --remove-destination`
(critical in git worktrees so a build never writes through a symlink into the
canonical tree's binary) and refreshes `_native.build.json` for content-based
staleness verification (`domains/engine_provenance.py`).

Two things worth knowing before you run a `--release` build:

- **Memory.** `runners/dsl/.cargo/config.toml` caps `jobs = 4`. The release
  profile uses fat LTO + `codegen-units=1` for benchmark fidelity, which
  makes each codegen unit large (1–2 GB); at default parallelism a release
  build can OOM mid-compile (exit 137) on a memory-constrained box. Debug
  builds are unaffected. If a release build still OOMs, drop further for
  that one run: `CARGO_BUILD_JOBS=2 cargo build --release`.
- **Tests don't need `--release`.** `cargo test` (debug) is the
  memory-safe default; reach for `--release` only for a specific
  performance-sensitive test.

## Testing

```bash
# Everyday development: run the scoped slice for the seed/module you touched
pytest tests/test_<feature>_migrated.py

# Full migrated gate (~8,300+ tests across 756 files; takes 60–90 min)
pytest tests/ -k migrated
```

`-k migrated` is this tree's standing convention: `tests/test_*_migrated.py`
(756 files out of 1,304 total test modules as of this writing) are the gate
for graph-native behaviour — the suite that replaced the old Python-vs-graph
parity tests once the `CuriousAgent` migration completed. The root
`conftest.py` pins the Rust engine this tree's tests must run against
(`domains/engine_provenance.py::engine_preamble`) and points dataset-reading
tests at the gitignored `data/` directory rather than `/tmp`. Known
pre-existing failures are tracked as an explicit, diagnosed list of node IDs
in `results/failure_baseline.json` (`scripts/failure_baseline.py`), never as
an unconditioned count.

- **Never run `pytest -n auto` on the full suite.** Unbounded xdist
  parallelism on a many-core, finite-RAM machine will OOM the host. Use
  scoped test files for iteration, and bound parallelism (e.g. `-n 6`) when
  a full sweep is required.
- **If you're working inside a nested git worktree** (`.worktrees/...`, common
  for isolated rung development in this project's history), pytest can pick
  up the *parent* repo's `conftest.py` instead of the worktree's own, which
  manifests as every test module failing to collect with `ImportError`. If you
  hit that, pass `--confcutdir=<the worktree root>` and set `COLUMNS=250`.
  Also symlink `data/` from the canonical checkout (`ln -s <canonical>/data data`)
  so corpus-dependent readers and gates do not silently fall back or skip.

## Finding your way around

- **[`CLAUDE.md`](CLAUDE.md)** — the architecture rule, authoritative, with a full
  chronological account of major landings (the CuriousAgent deletion, the
  composer/driver migration, the dynamic-quantization growth ladder, quanta
  navigation, transformation-as-dimension-change, the base-as-dimension
  invariant, the self-repair/gap-awareness machinery, and the shapes-not-numbers
  and rules-as-shape arcs). Read this for *why* something is built the way it is.
- **[`docs/SEED_DEVELOPMENT.md`](docs/SEED_DEVELOPMENT.md)** — practical guide
  to developing new graph-data seeds (`seeds/<id>.json`), authoring Rules,
  Productions, Reflexes, and Term ASTs, using `tools/build_*_seed.py`
  emitters and `domains/teach.py`, and avoiding fixpoint and selector traps.
- **[`docs/SCIENCE_RESEARCH.md`](docs/SCIENCE_RESEARCH.md)** — practical guide
  to doing science research on the substrate: the `PREREG → Measure → RESULTS`
  protocol, the five-clause instrument calibration gate, engine provenance
  (`domains/engine_provenance.py`), RNG seed accounting (`scripts/seed_claim.py`,
  `domains/seed_record.py`), and enumerated baseline discipline.
- **[`docs/CODE_MAP.md`](docs/CODE_MAP.md)** — what lives in every top-level
  source directory (`runners/dsl/`, `domains/`, `domains_rs/`, `worlds/`,
  `substrate/`, `seeds/`, `scripts/`, `tools/`, `tests/`, `web/`), with
  measured file/line counts, not estimates.
- **[`docs/features/`](docs/features/)** — synthesized, current-state summaries
  of each major subsystem (program synthesis, dynamic quantization, vision,
  Bigville, flight/vehicle control, humanoid embodiment, audio/speech, LS20
  spatial reasoning, psychology/affect, engine/substrate mechanics). Each ends
  with a pointer into the detailed historical record. Start here if you want
  the five-minute version of a subsystem before diving into its research
  archive.
- **[`docs/research/`](docs/research/INDEX.md)** — the full historical
  `PREREG → RESULTS` record, one subfolder per topic, each with its own
  `INDEX.md` (`docs/research/INDEX.md` is the top-level map). This is where
  the primary sources live: every claim in `docs/features/` and `CLAUDE.md`
  is backed by a document somewhere in here.
- **[`docs/meta/`](docs/meta/)** — `SPEC.md` (the project's original
  phase-by-phase design spec, from before the current architecture existed —
  historical value only), `SCREENCAST.md`, `NOTICES.md`, `JABBERWOCKY.md`.
- **[`VISION_PROTOCOL.md`](VISION_PROTOCOL.md)** (repo root, deliberately not
  moved into `docs/research/` — see `docs/CODE_MAP.md`) — the live,
  actively-parsed burned-seed ledger and binding experimental protocol rules.

## A note on scale

This is a large, long-running research program, not a small demo repo:
`runners/dsl/src/` alone is ~169k lines of Rust across 129 files;
`domains/` holds 823 Python world-adapter/seed-emitter files and `worlds/`
holds 129 newer world adapters; `seeds/` holds 878 top-level manifests plus
`seeds/generated/` and a ~306k-file auto-acquired knowledge cache; `tests/`
holds 1,304 test modules (756 `test_*_migrated.py`); and `docs/research/`
holds ~4,550 PREREG/RESULTS/design documents. `docs/CODE_MAP.md` and
`docs/research/INDEX.md` exist so a new reader doesn't have to discover that
scale by `ls`-ing around — start there.
