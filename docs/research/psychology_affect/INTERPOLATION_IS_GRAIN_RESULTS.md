# Interpolation is lower grain, not a different machine — RESULTS

**Block**: 303000. Pre-reg: `INTERPOLATION_IS_GRAIN_PREREG.md`.
Measure: `scripts/interpolation_is_grain_measure.py`.

The user's claim: *"we don't need to choose. interpolation is just a lower
grain and a slightly different model or different parameters."* — degree, not
kind. **Verdict: SUPPORTED**, with one part bounded exactly as predicted.

## Measured (real CAN field dynamics, this machine)

| Part | Test | Result | Verdict |
|---|---|---|---|
| 1 | 1-hop graded superposition + grain | fine 1→2→3→4 monotone; coarse(8) → all 0 (collapsed) | **HOLDS** |
| 2 | multi-hop reach (no direct edge) | target state +1.0, run_rules 5 steps | **HOLDS** |
| 3 | multi-hop graded, discrete commit | states [1,1,1,1] for 1..4 paths | **SATURATES** (as predicted) |
| 4 | multi-hop graded, continuous read, weak paths | acts 0.071→0.141→0.206→0.268, spread 0.197 | **HOLDS** |

### Part 1 — interpolation and retrieval are the same read at different grain
A held-out cue combination produces a **graded** coherence on the shared
candidate (1.0→2.0→3.0→4.0 as overlap goes 1→4 cues) — a value the field
PRODUCES by superposition, not a stored "{these cues}→answer" edge. At **fine
grain** the read resolves that gradient (graded similarity = interpolation);
at **coarse grain (8.0)** the whole gradient collapses to one bucket
(present/absent = retrieval/categorisation). The aperture grain IS the dial
between interpolation and retrieval.

### Part 2 — the field reaches past direct associations
A `target` node with NO direct edge from the cues reaches state +1.0, driven
purely by 2-hop coupling through an intermediate (cues pinned by
`external_field`, `run_rules` fired 5 steps). The substrate is NOT bounded to
memorised direct associations — it propagates.

(Note: an earlier probe wrongly suggested a 1-hop bound. Root cause: that
probe never LOADED the seed rules, so `run_rules` was a no-op. With
`load_seed_manifest(engine_rules_only(...))` and the correct structure —
symmetric weighted `causal_influence` pairs, a nonzero `external_field` drive —
the relaxation fires and propagates. Corrected here.)

### Part 3 — the discrete commit saturates (this is the bounded part)
Under the native 3-state update, target state is +1 for 1, 2, 3, OR 4
supporting paths — identical. Once a neighbour commits to +1, extra support
adds nothing: the 3-state Hopfield update is a **winner-take-all attractor**.
It answers "is target in the basin? yes/no", not "how strongly". The discrete
commit QUANTISES the multi-hop gradient away. **This is the one thing that
"fails" — and it is a categorical-commit MODE, built to be a retrieval
attractor, not a limit on the substrate.**

### Part 4 — the lower-grain (continuous) read recovers graded multi-hop
Propagating the CONTINUOUS pre-threshold local field (`tanh(local)`, no
commit) in the fair regime — WEAK paths where no single path saturates the
target — produces a **genuinely graded, monotone** multi-hop value:
0.071 → 0.141 → 0.206 → 0.268, roughly linear in the number of supporting
paths (spread 0.197). This is the graded far-interpolation an LLM performs,
recovered from the SAME graph by a pure Python read — the "lower grain"
the claim names, no seed/rule/Rust change.

## Verdict on the extrapolation

**SUPPORTED.** Interpolation is not a different KIND of machine bolted onto the
substrate — it is the same convergent field read:
- graded at 1 hop (part 1),
- reaching multi-hop (part 2),
- and graded multi-hop under the continuous read (part 4).

The only thing that saturates is the discrete 3-state COMMIT at strong drive
(part 3) — a mode/parameter choice (it is deliberately a categorical retrieval
attractor), exactly the "slightly different model or different parameters" the
user named. Retrieval ↔ interpolation is a resolution dial (grain) and a
commit-vs-continuous mode, not a wall. **Degree, not kind — confirmed with
numbers.**

## Correction to SUBSTRATE_SCALING_PROJECTION_RESULTS.md

That rung's "coverage ≠ capability parity" ceiling asserted the substrate does
"compositional reasoning over EXPLICIT structure, NOT the LLM's generative
interpolation," treated as a kind boundary. **This rung corrects that**: graded
interpolation (including multi-hop) IS available on the same substrate via the
continuous read; the discrete-commit saturation that looked like a ceiling is a
PARAMETER/mode, not a kind difference. The honest residual ceiling is narrower:
what the substrate can interpolate is bounded by GRAPH DENSITY and coupling
reach (a sparse/badly-curated graph interpolates poorly — coarse grain over
noise is mush, not insight), which is a degree of graph richness, not a
different machine.

## Honest bounds (still true)
- Part 4's continuous read is a DEMONSTRATION of the parameter-mode the claim
  predicts — a Python read over the graph, NOT a new committed inference
  default. Wiring a continuous multi-hop interpolation mode as a first-class
  substrate primitive is a named follow-on, not built here.
- Interpolation QUALITY depends on graph density + coupling reach; measured
  here on small constructed graphs, not a 10⁹-node corpus.
- The fair graded test requires the weak-path regime (registered before
  measuring); strong paths saturate trivially in BOTH discrete and continuous
  reads and tell us nothing.

## Verification
`.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246` (seed+python only, no Rust);
protected CAN-internals (`can_ops.rs`) / toolbox untouched; the continuous read
is a pure Python read, no seed/rule change.
