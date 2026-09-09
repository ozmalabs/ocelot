# Interpolation is lower grain, not a different machine — PREREG

**Block**: 303000

**Task**: The user's claim, correcting the previous rung's coverage-ceiling:
*"except we don't need to choose. interpolation is just a lower grain and a
slightly different model or different parameters."* — i.e. the substrate's
retrieval and an LLM's generative interpolation are the SAME operation at
different resolution / parameters, a degree-not-kind difference, NOT two
different kinds of machine. *"I want real numbers — the point is to support
(or disprove) my extrapolations about the capability of the substrate."*

This registers a falsifiable test of that claim, measured on the real CAN
field dynamics.

## 1. The claim, decomposed into falsifiable parts

"Interpolation is just lower grain" is not one claim but four, each of which
can independently hold or fail:

1. **1-hop graded superposition** — a held-out cue combination produces a
   GRADED value on a candidate reflecting partial pattern overlap (a value the
   dynamics PRODUCE, not a stored edge), and the aperture GRAIN slides that
   read between fine (graded similarity = interpolation) and coarse
   (present/absent = retrieval/categorisation).
2. **Multi-hop reach** — the field propagates ≥2 hops to light a node with NO
   direct edge from the cues (so the substrate is not bounded to memorised
   direct associations).
3. **Multi-hop graded, discrete commit** — does the graded value survive past
   one hop under the native 3-state discrete update?
4. **Multi-hop graded, continuous read** — does propagating the CONTINUOUS
   pre-threshold local field (the "lower grain" the claim predicts) produce a
   graded multi-hop value, as a Python read over the SAME graph, no rule
   change?

## 2. Mechanism + method

The convergent local field
`local(n) = external_field(n) + identity_field(n) + Σ weight·state(neighbour)`
is the same Σ coupling `can_native_update_3state` computes. The 3-state update
COMMITS this to {+1, 0, −1} against the ATANH_HALF deadzone; the continuous
read applies `tanh(local)` WITHOUT committing.

To fire the real relaxation the graph must be built as the seed rules require
(discovered this rung, from `tests/test_can_native_reimplementation.py`):
load `seeds/can_native_reimplementation.json` via
`engine_rules_only`+`load_seed_manifest`; Mt with
`temperature`/`discrete_mode`/`can_tick`; Concepts on the Mt via `has_concept`
with `state`/`external_field`/`identity_field`; SYMMETRIC `causal_influence`
edge PAIRS with a `weight` attr; a nonzero `external_field` DRIVE to pin cues.

The continuous read (part 4) is a Gauss-Seidel `tanh(local)` sweep in Python
over the same graph — a READ, no seed/rule/Rust change.

## 3. Predictions (registered before write-up)

1. 1-hop: coherence on the shared candidate rises MONOTONICALLY with overlap
   (1→4 cues); coarse grain collapses that gradient to present/absent.
2. Multi-hop reach: a target with no direct cue edge reaches nonzero state.
3. Multi-hop discrete: EXPECTED to SATURATE (winner-take-all attractor) — a
   single sufficient path pins the target, extra paths add nothing. If it
   saturates, the discrete commit quantises away the multi-hop gradient.
4. Multi-hop continuous, WEAK paths (no single path saturates): EXPECTED to be
   MONOTONE GRADED — the graded interpolation the claim predicts, recovered by
   the lower-grain (continuous) read.

## 4. What each outcome means for the claim

- Parts 1+2+4 holding, with part 3 saturating, would SUPPORT the claim:
  interpolation IS available on the same substrate; the only thing that
  "fails" is the discrete categorical commit at strong drive, which is a
  MODE/PARAMETER choice (built to be a retrieval attractor), not a different
  kind of machine. The continuous read is the "lower grain," and it
  interpolates.
- Part 4 FAILING (continuous multi-hop also flat/non-graded) would DISPROVE
  the claim: graded far-interpolation would not fall out of the substrate's
  field at all, and the LLM's generative reach WOULD be a difference in kind.

Report honestly which hold. This CORRECTS
`SUBSTRATE_SCALING_PROJECTION_RESULTS.md`'s "coverage ≠ capability parity /
compositional-vs-generative" ceiling: if the claim is supported, that ceiling
is a discrete-commit PARAMETER, not a kind boundary.

## 5. Anti-faking bars

- **Held-out**: the interpolation target for a combination is a value the
  dynamics PRODUCE (superposition sum / propagated field), never a stored
  "{these cues}→answer" edge. The gradient must be produced, not looked up.
- **Fair graded test**: multi-hop graded (parts 3/4) must use a WEAK-path
  regime where no single path saturates the target — otherwise saturation is
  trivial and tells us nothing. Registered before measuring.
- **default==today**: the continuous read is a pure Python read; no seed/rule
  change, `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`. Protected
  CAN-internals / toolbox untouched.

## 6. Scope

seed+python only: a measurement script + docs + tests + this note correcting
the prior ceiling. NO Rust, NO CAN-internals, NO toolbox. The continuous read
is a demonstration of the parameter-mode the claim predicts, not a new
committed inference primitive (a named follow-on, not built as a default here).
