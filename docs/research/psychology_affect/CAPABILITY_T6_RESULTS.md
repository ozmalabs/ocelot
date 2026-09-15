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
quantization, and this repo holds no model. The LLM figures in the track are a
clearly-labelled **cited estimate for framing only**. The honest claim is not "our
forward pass is cheaper by factor N," it is a cost-**class** difference:

- **Substrate:** coining a new dimension is ~55 graph ops at think time, teacher-free.
- **LLM:** a genuinely new representational axis is **not an inference-time operation** —
  a frozen-weight model must be **retrained / fine-tuned** to acquire it (a training run,
  many GPU-hours), or cannot acquire it online at all.

Different cost class (bounded-tick inference vs a training run), not a ratio.

## Why this is the durable comparison

The RQ2 typicality contest (T2) is perishable — a frontier model likely raises its ρ. The
cost class is not: scaling a transformer does not turn representational change into an
inference-time operation; it remains a training-time event. So as models get bigger, the
typicality gap narrows while the cost-class gap for *acquiring a new axis mid-reasoning*
stays — or widens. That is the architecture-validation point this suite exists to make.

## Guardrails

Additive only. `.so` md5 `7efe75eba05b006cafd15dbb4b7da246` frozen; no protected-file
edit; `conceptualizer.py` untouched (audit green); nothing under `/applications`. Files:
`tests/capability/minting/track6_cost.py`, the `capture_minting_cost` addition to
`runners/substrate_runner.py`, and this doc.
