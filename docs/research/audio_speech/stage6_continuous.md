# Stage 6 (capstone) — continuous, top-down, the order-N loop everywhere

## (1) Verdict — LEAD

**STAGE 6 STARTS — FIRES (single-source).** On continuous speech (concatenated
FSDD digit-strings, LOSO), the single-pass re-ranker improves over the bottom-up
hypothesis AND wrapping it in the order-N loop co-refines boundaries + identity to
**convergence**, with a clean **n-passes signature** (harder inputs take more
passes). All three structural gate conditions hold:

```
strings: 72  (LOSO, 6 held-out speakers; n_per=3, digit-strings of length 2..5)

(1) single-pass re-ranker IMPROVES over bottom-up   : YES
      boundary F1  0.725 (equal-split) -> 0.753 (order-N)   delta +0.029
                   [pure-acoustic energy-valley baseline 0.620]
      word identity 0.257 -> 0.286                          delta +0.029
(2) order-N loop CONVERGES (collapse cost falls + fixed point): YES
      converged (no move lowers cost before cap) : 64/72 = 0.889
      collapse COST  0.179 -> 0.160  (mean drop +0.019)
      surprise       7.987 -> 7.985 (near-flat — reported, see honest limit)
(3) N-PASSES SIGNATURE (harder -> more passes)      : YES
      n_dig  mean_passes
        2       2.72
        3       3.56
        4       3.72
        5       5.11
      slope +0.733 passes/digit   corr +0.956

>>> STAGE 6 GATE FIRES (single-source continuous order-N loop): True
```

Run captured to `/tmp/stage6_full.log` (`MARKER_STAGE6_CONTINUOUS_COMPLETE`,
`elapsed 105s`; process pgrep-verified gone). `scripts/solve_for_n.py` and
CortexLoop were **left untouched**.

The capstone's success signal per the curriculum is the **structural readiness**
signal — the loop *converges* and the *n-passes signature* exists — **not** a
held-out accuracy number ([[ozma_no_premature_testing_mid_curriculum]]). Both
hold, and the re-ranker beats the bottom-up hypothesis on both the boundary and
the identity axis.

---

## (2) What was wired (the order-N loop on the native collapse core)

The order-N loop **IS** the native collapse core iterated against the owned
forward model, with native surprise as the refinement signal. Nothing in the
engine was reinvented — Stage 6 wires the existing pieces:

| order-N component | what it is | file:line |
|---|---|---|
| **T8 collapse** | native manifold softmax/conf/entropy as graph Term-trees in Rust | `scripts/native_collapse.py:70-90` (`T_MAX_LW`/`T_Z`/`T_CONF`) |
| **the MATCH** | `DtwTo(heard, forward_model[w])` — native Rust DSL Term | `runners/dsl/src/term.rs:291`, composed by `domains/recognition_graph.py:98` |
| **T10/T11 forward model** | per-word mean A1 trajectory (`speak(w)` = stored trajectory), LOSO | `scripts/stage6_continuous.py:build_forward_model` (reuses `analysis_by_synthesis_accept.py`) |
| **SURPRISE** | `-log(conf-at-collapse)` — the native Term `Neg(Log(conf))` | `scripts/native_collapse.py:90` (`T_SURPRISE`), called at `stage6_continuous.py:CollapseUnit.collapse` |
| **the order-N LOOP** | collapse -> surprise localises -> re-segment -> iterate to fixed point | `scripts/stage6_continuous.py:order_n_loop` |

The loop (`order_n_loop`, `scripts/stage6_continuous.py`):

1. **collapse** every segment against the forward model — `CollapseUnit.collapse`
   sets each candidate's manifold log-weight `lw(w) = -DtwTo(heard, fm[w])`
   (evaluated in Rust), reads the winning word, the native confidence (`T_CONF`),
   and the native **surprise** (`T_SURPRISE`);
2. **surprise localises** the worst-explained segment (`argmax` per-segment
   surprise) → the boundaries adjacent to it are the re-segmentation candidates;
3. **re-segment (top-down)** — try moving that boundary ±step; **accept the move
   iff the total native synth-error (the collapse cost) drops** — the agent's own
   weighted-admissibility selector, not a tuned heuristic over a free knob;
4. **iterate** until no move lowers the cost (the fixed point = convergence). The
   number of passes-to-convergence is the n-passes signature.

### Architecture audit (CLAUDE.md — native, no new Python cognition)

- The **cognition is native**: the collapse decision, confidence, entropy,
  surprise, and the synth-error match all run as graph Term-trees evaluated by
  `substrate.evaluate` in Rust (`T_MAX_LW`/`T_Z`/`T_CONF`/`T_SURPRISE`/`DtwTo`).
  No Python `exp`/`log`/softmax touches the manifold.
- The **forward model is the owned synth** (per-word mean A1 trajectory) — T10/T11,
  the same model the single-word AxS re-ranker uses; no TTS net.
- **Python is the world adapter + instrument only**: audio I/O (decode FSDD WAVs,
  concatenate into a continuous stream), boundary-offset bookkeeping, and the
  measurement harness (boundary-F1 / identity / convergence / n-passes). The
  re-segmentation **decision** (move-accept) is gated on the native collapse cost
  — the agent's selector — not a Python conditional over a fitted threshold.
- **Donkey-clean**: no `.fit`, no gradient, no loss, no net, no sweep. The only
  free quantity is "how many digits" (the length prior the n-gram would carry);
  the loop finds *where*. `solve_for_n.py` and CortexLoop are untouched.

---

## (3) The numbers — re-ranker improvement, convergence, n-passes

### Re-ranker vs order-N loop (72 LOSO strings, lengths 2..5)

The bottom-up hypothesis is the **degraded equal-duration split** (the pure
bottom-up prior carrying no acoustic boundary evidence — wrong because digits
differ in duration; this is the W4 top-down-restoration setup, giving the loop
genuine work). The digits **abut directly (0 ms gap)** — a coarticulated
continuous stream, not silence-padded tokens.

- **boundary F1**: equal-split `0.725` → order-N converged `0.753` (**+0.029**).
  The order-N loop's top-down re-segmentation moves boundaries toward where the
  forward model explains the signal, beating the naive split **and** the
  pure-acoustic energy-valley baseline (`0.620`) — top-down feedback rescues the
  degraded bottom-up boundaries.
- **word identity**: `0.257` → `0.286` (**+0.029**). Co-refining the boundaries
  improves the per-segment recognition (better-cut spans collapse to the right
  digit more often). Absolute identity is modest — this is LOSO 10-way cross-
  speaker recognition off a single mean-trajectory forward model (the known
  forward-model-resolution ceiling, W5), not the readiness signal.

### Convergence

- **64/72 = 0.889** strings reach a fixed point (no move lowers the collapse cost)
  before the 8-pass cap.
- The **collapse cost** (the loop's order-N objective = total native synth-error)
  falls `0.179 → 0.160` (mean drop **+0.019**) — the loop genuinely lowers the
  quantity it optimises and then stabilises.

### N-passes signature

Passes-to-convergence rise monotonically with difficulty (digit count):

```
  2 digits -> 2.72 passes
  3 digits -> 3.56
  4 digits -> 3.72
  5 digits -> 5.11
  slope +0.733 passes/digit,  corr +0.956
```

Harder inputs take more passes — the n-passes signature the curriculum names as
the structural success signal for T6.

---

## (4) Honest verdict — what fires, what is the named next

**Stage 6 starts and the single-source gate FIRES.** The single-pass re-ranker
improves over the bottom-up hypothesis (boundary +0.029, identity +0.029), the
order-N loop converges (88.9% reach a fixed point; collapse cost falls +0.019 and
stabilises), and the n-passes signature is clean (slope +0.733/digit, corr
+0.956). The loop is the native collapse core iterated against the owned forward
model, surprise-localised re-segmentation, donkey-clean, with `solve_for_n.py`
and CortexLoop untouched.

### Honest limits (read the numbers, not the boolean)

1. **Surprise is near-flat (7.987 → 7.985)**; the loop's measurable convergence is
   carried by the **collapse cost** (total synth-error), not by per-segment
   surprise. Per-segment confidence is already near-saturated (the 10-way digit
   manifold collapses hard per span), so `-log(conf)` has little headroom to fall
   even as the boundaries improve. The cost is the loop's actual objective and it
   *does* fall and stabilise; surprise is reported honestly as near-flat, not
   dressed up. (Surprise would carry more of the signal on a larger, less-peaked
   lexicon where per-segment confidence is not saturated.)

2. **The cost objective is a slightly biased proxy for the true boundary.** On the
   smaller smoke config (36 strings) the loop *lowered the cost but marginally
   worsened* boundary F1 (0.736 → 0.694) — the forward model's resolution (a mean
   A1 trajectory, the W5 ceiling) means minimising synth-error does not always pull
   a boundary to the true cut. On the full 72-string run the boundary improves
   (+0.029), so the bias is small relative to the gain, but it is real: a sharper
   forward model (W5 babble-refinement) would tighten the cost↔truth alignment.
   This is the [[ozma_grounding_closes_on_consistency_not_accuracy]] lesson — the
   loop converges on its own consistency, which here is *mostly* but not perfectly
   the ground-truth boundary.

3. **Venue.** Concatenated FSDD digit-strings give KNOWN identities + boundaries
   (so the loop is measurable), and they are continuous (0 ms abutment,
   coarticulated). They are not LibriSpeech continuous prose — that venue has no
   word timestamps and noisy sub-word units, so neither axis is checkable there;
   the digit-string venue is the honest measurable instance of the same capability.

### The named next (within Stage 6)

**Multi-source / mixtures (ASA / streaming, the steerable fovea).** This run is
single-source (the directive's "single-source → mixtures"). The next sub-step is
to add the auditory-scene / source-grouping front end (W3) and the steerable fovea
so the same order-N loop groups + attends to one talker in a mixture before
recognising — "what sources would have produced this?" as the same invert-the-
forward-model collapse, now over a source-assignment hypothesis as well as a
segment + identity hypothesis. The single-source order-N loop proven here is its
prerequisite.

### Files

- `scripts/stage6_continuous.py` — the order-N loop wired on the native collapse
  core + owned forward model + native surprise; the world adapter (audio
  concatenation, boundary bookkeeping) + the measurement harness. NEW.
- `docs/stage6_continuous.md` — this report. NEW.
- `/tmp/stage6_full.log` — full captured run
  (`MARKER_STAGE6_CONTINUOUS_COMPLETE`).

Reused unchanged: `scripts/native_collapse.py` (T8 + surprise), `runners/dsl/
src/term.rs` `DtwTo` (the match), `scripts/analysis_by_synthesis_accept.py` (the
forward model + the single-word AxS lineage), `domains/recognition_graph.py` (the
graph synth-error/argmax terms). `scripts/solve_for_n.py` and CortexLoop UNTOUCHED.
