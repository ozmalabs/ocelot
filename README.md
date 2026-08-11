# Jabberwock — a graph-native agent

**The agent is a graph, running in Rust.** Jabberwock (the "ocelot" repo) is
an implementation of the (G, Γ, C) substrate — a typed graph plus a
reflective admissibility grammar — where the agent's entire reasoning,
knowledge, and behaviour is graph data, executed by a Rust rule-matching
runtime (`substrate_rs`). Python exists only as a thin **world adapter**
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
other seeds. An agent declares which seeds it wants; the loader
(`substrate/seed_loader.py`) resolves the dependency closure and installs
seeds in topological order. A text-only chat agent and a Doom-playing agent
share the same Rust runtime and differ only in which seeds they loaded.

When the agent is *taught* something new, it persists through the same
mechanism (`domains/teach.py`'s `teach()` facility): the fact lands in the
live graph, gets filed into the seed category the agent's own meta-shape
classifier assigns it to, and is appended to that seed's manifest — so a
fresh boot includes it. `seeds/acquired/` (hundreds of thousands of small
files) is exactly this: an auto-grown grounding cache, not hand-authored
seed data.

## Dynamic quantization — the core learning mechanism

Every capability in this tree — vision, handwriting, program synthesis,
spatial navigation, speech recognition — is an instance of one loop: an
observation is decoded against a held codebook of learned shapes; whatever
isn't covered is a residual; a residual that recurs mints a new codebook
entry, growing the codebook for the next decode. The `run_rules` fixpoint
*is* this decode → grow → re-decode loop; there is no Python iteration
driving it. See `docs/features/dynamic-quantization.md` for the full
mechanism (the growth ladder, the frame/continuum invariant that keeps
in-graph values integer while cross-frame maps may be real-valued) and
`docs/features/` generally for how it shows up in each subsystem.

## Building

```bash
cd runners/dsl
maturin develop --release
```

This builds the `substrate_rs` Rust extension and installs it into the
active Python environment. Two things worth knowing before you run a
`--release` build:

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
pytest tests/ -k migrated
```

`-k migrated` is this tree's standing convention: `tests/test_*_migrated.py`
(768 files as of this writing) are the gate for graph-native behaviour —
the suite that replaced the old Python-vs-graph parity tests once the
`CuriousAgent` migration completed. The root `conftest.py` pins the Rust
engine this tree's tests must run against
(`domains/engine_provenance.py::engine_preamble`) and points dataset-reading
tests at the gitignored `data/` directory rather than `/tmp`.

**If you're working inside a nested git worktree** (`.worktrees/...`, common
for isolated rung development in this project's history), pytest can pick
up the *parent* repo's `conftest.py` instead of the worktree's own, which
manifests as every test module failing to collect with `ImportError`. If you
hit that, pass `--confcutdir=<the worktree root>` and set `COLUMNS=250`.
This does not affect a normal top-level checkout — only worktrees nested
inside the canonical repo.

## Finding your way around

- **`CLAUDE.md`** — the architecture rule, authoritative, with a full
  chronological account of major landings (the CuriousAgent deletion, the
  composer/driver migration, the dynamic-quantization growth ladder, quanta
  navigation, transformation-as-dimension-change, the base-as-dimension
  invariant, the self-repair/gap-awareness machinery). Read this for *why*
  something is built the way it is.
- **`docs/CODE_MAP.md`** — what lives in every top-level source directory
  (`runners/dsl/`, `domains/`, `domains_rs/`, `worlds/`, `substrate/`,
  `seeds/`, `scripts/`, `tools/`, `tests/`, `web/`), with measured file/line
  counts, not estimates.
- **`docs/features/`** — synthesized, current-state summaries of each major
  subsystem (program synthesis, dynamic quantization, vision, Bigville,
  flight/vehicle control, humanoid embodiment, audio/speech, LS20 spatial
  reasoning, psychology/affect, engine/substrate mechanics). Each ends with
  a pointer into the detailed historical record. Start here if you want the
  five-minute version of a subsystem before diving into its research
  archive.
- **`docs/research/`** — the full historical PREREG → RESULTS record, one
  subfolder per topic, each with its own `INDEX.md`
  (`docs/research/INDEX.md` is the top-level map). This is where the
  primary sources live: every claim in `docs/features/` and `CLAUDE.md` is
  backed by a document somewhere in here. The dominant convention
  throughout: a `*_PREREG.md` is committed *before* a measurement, a script
  performs it, and a `*_RESULTS.md` reports what happened, honestly,
  including nulls and reverted work — never edited after the fact to fit
  the result.
- **`docs/meta/`** — `SPEC.md` (the project's original phase-by-phase design
  spec, from before the current architecture existed — historical value
  only), `SCREENCAST.md`, `NOTICES.md`, `JABBERWOCKY.md`.
- **`VISION_PROTOCOL.md`** (repo root, deliberately not moved into
  `docs/research/` — see `docs/CODE_MAP.md`) — the live, actively-parsed
  burned-seed ledger and binding-rules document for the vision research
  thread specifically.

## A note on scale

This is a large, long-running research program, not a small demo repo:
`runners/dsl/src/` alone is ~106k lines of Rust across 84 files;
`domains/` holds 720 Python world-adapter/seed-emitter files; `seeds/`
holds 888 hand/tool-authored manifests plus a ~306k-file auto-acquired
knowledge cache; `docs/research/` holds well over a thousand PREREG/RESULTS
documents. `docs/CODE_MAP.md` and `docs/research/INDEX.md` exist so a new
reader doesn't have to discover that scale by `ls`-ing around — start there.
