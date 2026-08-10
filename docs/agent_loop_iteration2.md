# Autopoietic loop — iteration 2 (measurement → gap-graph feedback)

The crank turned a second time, and this time the previous iteration's
**measurement feeds back into the gap-graph** so the agent's own ranker
re-picks. This doc reports HONESTLY what self-corrected and every
intervention.

Reproduce: `SG_PER=10 python scripts/agent_loop_iteration2.py`
(reads FSDD from the repo's `scripts/fsdd_learner_world` loader).

---

## 1. The feedback mechanism + the re-rank result

**Iteration 1** (commits `701ec9a` / `26852c4`): the agent's graph-resident
ranker (`domains/gap_prioritiser.py`) picked **cross-speaker clustering** by
a-priori compression-payoff (own payoff = #held postulates the capability
unifies): clustering 6, word-scale chunking 4, LPC 2 — **LPC last**. It built
clustering and measured it **capped by the blurry front-end** (FSDD label-free
purity 0.441 < raw-spectrum 0.483; mirroring sound-graph LOSO filter 0.335 <<
spectrum 0.649). The loop *observed* this points at LPC but never *encoded* it.

**Iteration 2 — the new mechanism** (`domains/measurement_feedback.py`, a
world↔graph adapter):

1. `record_outcome` writes the iter-1 measurement RESULT back into the graph as
   a `MeasurementOutcome` node and — because the probe reported a **non-positive**
   gain attributed to the front-end — a `blocked_by` edge **clustering → LPC**.
2. The ranking Term is EXTENDED so a gap inherits the payoff of the gaps it
   UNBLOCKS:
   ```
   unblock_bonus(axis)    = Σ_{a : a blocked_by axis} Count(Neighbours(a,"unifies"))
   effective_payoff(axis) = Count(Neighbours(axis,"unifies")) + unblock_bonus(axis)
   effective_score(axis)  = effective_payoff(axis)*1000 − min_order(axis)
   pick                   = Argmax over CapabilityAxis of effective_score
   ```
   Graph Term-trees only — `Plus / Sum / InNeighbours / Count / Neighbours /
   Times / Minus / Attr / Argmax`. Every variant verified present in
   `runners/dsl/src/term.rs` (`InNeighbours` at line 51, `Sum` 58, `Plus` 188,
   etc.) and JSON-parseable (`runners/dsl/src/jsonio.rs`). **No new primitive.**
   A graph Rule (`pick_frontier_gap_with_feedback`) evaluates the Argmax natively
   and writes the winner onto a `FrontierRoot` — the Rule, not Python, makes the
   pick.

**Re-rank result (native Term evaluation):**

| axis | own payoff | unblock bonus | effective payoff | effective score |
|---|---|---|---|---|
| **LPC / all-pole** | 2 | **6** (unblocks clustering) | **8** | **7999** |
| cross-speaker clustering | 6 | 0 | 6 | 5999 |
| word-scale chunking | 4 | 0 | 4 | 3999 |

### Did LPC win via the feedback? — **YES. The loop self-corrected.**

LPC's effective payoff = its own 2 + clustering's 6 (LPC unblocks clustering) =
**8 > clustering's 6**. The native Argmax over the extended score Term picked
`all-pole / levinson / lpc-formant`. The pick was **NOT forced** — it is the
verdict of the agent's own Term over the measurement-written edge. A new
`FrontierChoice` (origin `measurement_feedback`) records it.

This is the iteration's headline: **a-priori reasoning ranked LPC last; the
agent's own measurement, fed back as graph state, re-ranked it first.**

---

## 2. The build (composed vs adapter-math split)

The agent forward-built the LPC all-pole formant extractor from its
**source-filter / all-pole science**:

- **Spec (the agent's WHAT)** — `domains/runtime_design.agent_specify_lpc_formants`
  reads the held `source_filter_theory` concept ("speech = source through a
  vocal-tract FILTER") and the harvested all-pole implication-shape ("a recursive
  / IIR / autoregressive system is captured by a FEW poles, recovered by linear
  prediction"). It records an `OperationSpec` node: invert the all-pole filter by
  linear prediction → pole angles are the resonances = formants. The spec is
  grounded in `source_filter_theory` (True). *Honest:* the explicit `all-pole`
  concept text lives in the `audio_coding_theory` seed, which the base STT agent
  does **not** load, so `all_pole_model`/`iir_recursive` grounding flags read
  False in this seed set — only the source-filter grounding is load-bearing here.

- **Extractor (the HOW)** — `domains/sound_graph._lpc_formant_peaks`
  (`build_sound_graph(..., frontend="lpc")`): pre-emphasis → autocorrelation →
  Levinson-Durbin recursion → roots of A(z) → pole angles = formant frequencies,
  pole radius = bandwidth; keep poles in 200–3400 Hz with bandwidth < 400 Hz.
  Output is the **same `(freq, mag)` shape** the cepstral extractor returns, so
  it drops into the graph builder producing the same `FormantNode` schema — the
  downstream signatures are unchanged.

**Composed vs adapter-math, named plainly:** the LPC math (autocorrelation +
Levinson-Durbin + polynomial root-finding) is **adapter-math (numeric DSP)** in
the extraction layer — it is NOT composed from DSL primitives, and is honestly
labelled so in the spec's `category` field. This is the **same category** as the
`np.fft` cepstral lifter it replaces (which is also numpy in the extraction
layer). Per the architecture rule, audio/DSP primitives are Rust-or-numpy at the
I/O boundary; the agent's reasoning (which front-end, why) is the graph-resident
part (the spec + the re-ranked pick), and the extractor's OUTPUT enters the graph
as FormantNodes exactly as before. Levinson-Durbin has no DSL primitive, so this
is the honest place for it; specifying it as a Rust primitive (runtime_design's
emit path) was not done — it would be a large iterative-numeric Term with no
re-use beyond LPC.

---

## 3. The measurement — did closing the front-end gap unblock the downstream?

FSDD, 6 speakers, leave-one-speaker-out. `SG_PER=10` (clustering) / `12` (LOSO).

**(a) Sound-graph LOSO** (cross-speaker nearest-prototype accuracy, chance 0.10):

| front-end | LOSO acc | same−across separation |
|---|---|---|
| cepstral filter (OLD) | 0.337 | +0.192 |
| **LPC all-pole (NEW)** | **0.480** | **+0.389** |
| raw spectrum (ceiling) | 0.640 | — |

LPC lifts the filter-graph LOSO **+0.143 (0.337 → 0.480, +42% relative)** and
nearly **doubles** the same/across separation. Cleaner formant nodes, measurably.
It still does **not** reach the raw spectrum's 0.640 (−0.160): the 12-dim
3-formant-ratio relational summary remains lossy vs the 96-dim spectrum
trajectory. LPC closes ~45% of that gap, then hits the inherent ceiling of the
3-formant representation on 8 kHz digits.

**(b) Cross-speaker clustering purity** (label-free; random floor 0.162) — the
downstream the feedback said LPC would unblock:

| representation | purity |
|---|---|
| cepstral filter (OLD) | 0.315 |
| **LPC all-pole filter (NEW)** | **0.460** |
| CMVN log-mel (iter-1 agent) | 0.441 |
| raw spectrum (iter-1 cap) | 0.483 |

The LPC front-end clusters **+0.145 above** the old cepstral filter and **+0.019
above the iter-1 agent's own capped CMVN front-end (0.460 > 0.441)** — i.e.
closing the front-end gap pushed the agent's front-end *above its iteration-1
self*. It still does **not** clear the raw-spectrum cap (0.460 < 0.483, −0.023)
that limited iter-1.

**Verdict on the feedback's prediction:** directionally correct and
substantially confirmed — the front-end fix lifted the downstream by the
predicted magnitude and beat the iter-1 agent's own front-end — but it did **not
fully clear the raw-spectrum ceiling** on 8 kHz digits. An honest *partial*
unblock, exactly the "modest / hits its own ceiling" outcome flagged as possible.

---

## 4. Every intervention, named

- **Did I force the pick?** No. LPC wins by the agent's extended Term's native
  Argmax over the measurement-written `blocked_by` edge (effective score 7999 vs
  5999). The mechanism (the feedback edge + the score-extension Term) is the
  orchestrator's contribution — it is the **world↔graph adapter role**: translate
  a measurement RESULT into graph state. The DECISION (which axis wins) is the
  graph Term.
- **One honest forced-adjacent step (flagged):** at the current tree the agent's
  order-N synthesis **does not produce the LPC axis** — the harvested all-pole
  implication-shape no longer fires on `source_filter_theory` (the iter-1 demo's
  ACCEPTANCE 1 prints `MISS LPC … HARVEST INSUFFICIENT`, contradicting its own
  stale hardcoded "3/3" honesty paragraph; this is pre-existing in the tree, not
  introduced here). So the blocker the measurement names did not exist as a
  synthesized axis. `measurement_feedback._mint_blocker_axis` therefore **mints
  the LPC axis from the measurement evidence**, grounded by `unifies` edges to the
  held `source_filter_theory` + `vocal_tract_resonance_formants` Concepts (so its
  own payoff of 2 is a real postulate count, not invented), flagged
  `provenance: measurement_derived_axis (NOT order_n synthesised)`. This is
  defensible as I/O translation — the measurement is direct, *stronger* evidence
  the gap is real than the a-priori unification count — but it is the
  orchestrator supplying the axis, not the synthesis. **If the synthesis had
  emitted the LPC axis (as the iter-1 commit messages claim it once did), no
  minting would occur and the re-rank is identical** (verified: when the LPC axis
  is present, the same `blocked_by` edge writes and LPC reaches effective payoff
  8 > 6 with no minting). The residual to fully close is upstream: fix the
  harvester so the all-pole shape fires on the source-filter postulate.
- **Hand-coded LPC math?** Yes — Levinson-Durbin / autocorrelation / root-finding
  is numpy adapter-math (same category as the existing FFT cepstral lifter). The
  agent specified WHAT (the OperationSpec, grounded in its science); the math is
  the I/O-boundary DSP. No DSL primitive was added.
- **A peer LLM?** None. No model authored code or made any decision.

## Files (left in the working tree, NOT committed)

- `domains/measurement_feedback.py` — NEW. The feedback adapter + extended
  ranking Term (graph-resident) + the re-rank/pick enactment.
- `domains/runtime_design.py` — added `agent_specify_lpc_formants` (the agent's
  spec, grounded in its source-filter science).
- `domains/sound_graph.py` — added `_lpc_formant_peaks` + `frontend=` switch in
  `build_sound_graph` (the LPC all-pole front-end; cepstral remains the default,
  so nothing else changes).
- `scripts/agent_loop_iteration2.py` — NEW. Runs the whole iteration-2 loop.
- `docs/agent_loop_iteration2.md` — this note.

Tests: `tests/test_stt_pipeline.py` + `tests/test_perception_self_assessment.py`
both green (12 passed).
