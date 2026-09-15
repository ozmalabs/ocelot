# Capability Suite — Track 6 Results (cost)

The cost track. A newer LLM would narrow the RQ2 typicality gap (see the perishability
caveat in `CAPABILITY_T5_RESULTS.md`) — but it would **widen** the cost gap, and the
cost difference is the durable, architecture-level point. This track measures what it
costs the substrate to *do* the capability (coin a new dimension mid-reasoning) in the
substrate's own hardware-independent counters, and frames the LLM comparison honestly as
a cost-**class** difference — not a joules-to-joules race the repo cannot fairly run.

## What is measured (primary, portable)

The substrate's native op-counters, read straight off the running engine (`s.counters()`)
around a minting run, with the build phase excluded (counters cleared after the graph is
seeded, so the figure is the *thinking + minting*, not seed I/O): node inserts, edge
inserts, admissibility checks, rule evaluations, cache hits/misses. This is the "load = a
directly countable substrate quantity" unit the project's analysis-by-synthesis work uses
— no human-data fit, no GPU, no matmul. Wall-clock is reported only as a secondary,
hardware-dependent figure.

## Result (`track6_cost.py`, exit 0, C1–C4 PASS)

Coining 4 new axes per category costs:

| category | native ops (total) | node inserts | edge | admissibility | evals | minted | spy |
|----------|-------------------|--------------|------|---------------|-------|--------|-----|
| bird | 130 | 32 | 4 | 4 | 90 | 4 | 0 |
| fruit | 40 | 32 | 4 | 4 | 0 | 4 | 0 |
| vegetable | 40 | 32 | 4 | 4 | 0 | 4 | 0 |
| furniture | 40 | 32 | 4 | 4 | 0 | 4 | 0 |
| vehicle | 40 | 32 | 4 | 4 | 0 | 4 | 0 |
| weapon | 40 | 32 | 4 | 4 | 0 | 4 | 0 |

**Mean ≈ 55 native graph ops** per minting run (range 40–130; the bird run's extra 90
evaluations is a first-run rule-path warm-up — node/edge/admissibility are stable at
32/4/4). Wall-clock ~3–5 s, dominated by seed loading (secondary).

- **C1 bounded native cost** — small, finite, same small order across all categories.
- **C2 teacher-free / zero-GPU** — ask-spy = 0; the cost is entirely graph ops (there is
  no matmul or model-load call site in the minting path).
- **C3 cost-class** — the substrate mints at inference in bounded ticks; the LLM side is
  a **labelled cited estimate**, not a measured ratio.
- **C4 discrete / integer counters** — every cost quantity is an integer count.

## What is NOT measured (and why)

LLM joules / FLOPs are **not** measured here — they depend on hardware, batching, and
quantization, and this repo holds no model. The LLM figures are a clearly-labelled
**cited estimate for framing only**. And the honest claim is **not** "LLMs cannot build
new representations" — the Sept-2026 frontier shows they can: **GPT-6 Astra** turns
unfamiliar ARC-AGI-3 environments into *compact symbolic world-models and its own DSL
shorthand*, even writing game-specific code (ARC Prize, 2026-09-03). The claim is that
their architecture **bounds** it and the cost is **orders of magnitude higher —
different in kind**:

- **Substrate:** mints a **persistent** new dimension in ~55 graph ops at think time,
  teacher-free, no GPU; the axis is a graph node that **survives and is reused**.
- **LLM (frontier):** builds the representation in the **context window / opaque
  per-session state** — it **evaporates at session end** (frozen weights); a weight-level
  new axis needs retraining. Astra's ARC-AGI-3 runs cost **~$19K** (Provider Adapter,
  99.9%) to **~$26K** (Standard harness, 62.7%) **per benchmark**; ARC Prize prices the
  human brain-energy baseline at **~0.067 cents per game**.

Persistence class + cost class — not a ratio.

## Why this is the durable comparison

The RQ2 typicality contest (T2) is perishable — a frontier model raises its ρ, and Astra
shows frontier models now *match the substrate on building representations at all*. What a
bigger model does **not** change:

- **Persistence.** Scaling a transformer does not make its on-the-fly representation
  persist beyond the session or become a reusable structural commitment; it stays context/
  state-bound. The substrate's mint is a permanent graph axis.
- **Cost class.** Astra's own published figures (~$19K–26K/benchmark) against the human
  ~0.067-cents/game baseline confirm the gap is orders of magnitude — the substrate's ~55
  graph ops sit on the human side of that divide. Bigger models widen this, not narrow it.

That is the architecture-validation point, sharpened by the frontier evidence rather than
refuted by it. (ARC Prize explicitly does **not** claim AGI and notes ARC-AGI-3 is
bounded/closed-ended, not open-ended representational growth.)

## Guardrails

Additive only. `.so` md5 `7efe75eba05b006cafd15dbb4b7da246` frozen; no protected-file
edit; `conceptualizer.py` untouched (audit green); nothing under `/applications`. Files:
`tests/capability/minting/track6_cost.py`, the `capture_minting_cost` addition to
`runners/substrate_runner.py`, and this doc.
