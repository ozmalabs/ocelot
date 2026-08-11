# Active-transducer interface — build plan

The empirically-confirmed rate-limiter. The cognition (weighted-admissibility collapse over frames) is done and
proven; the n-gram already drives recognition to 0.758 from a 0.096 acoustic. What caps every new acoustic/
prosodic frame is the *quality of the read*: passive, batched, coarse, un-clocked. Both order-N frames KILLed for
this one reason (syllable: 75%-reliable passive peak-count; formant: coarse 32-band curvature). The interface —
not the cognition, not the frames — is where the next gains and the real difficulty live.

## What it is
A transducer that is **active, self-clocking, predictive, and real-time** — the four things the human interface
does that we don't have (memory ozma_interface_layer_is_active_transduction):
1. **Active** — the cognition *controls* its own transduction (efferent gain/sharpness, attention gating). Perception is an act.
2. **Self-clocking** — chunks by an entrained *rhythm* (theta ≈ syllable, gamma ≈ phoneme), not by fixed clips. The windows fall out of the oscillation.
3. **Predictive filter at the transduction** — the prediction (efferent copy) goes *down*; the front end pre-subtracts the predicted so what reaches cognition is mostly residual.
4. **The tick** — continuous, sample-by-sample, never has the whole utterance, only the edge.

## Stages (prioritized by impact, each a complete experiment)

### Stage A — the self-clocking rhythmic sampler (HIGHEST impact; fixes the syllable KILL)
A phase-locked **theta oscillator entrained to the energy envelope** emits syllable boundaries from its *phase*,
not from passive peak-counting. The oscillator integrates over time (robust to local sonorant-internal dips like
`follow`/`zero` that broke the 75% peak-counter). Gamma nested in theta gives phoneme-rate windows.
- BUILD (owned DSP, no net): an entrained oscillator / adaptive phase-locked loop on the broadband energy
  envelope; boundaries = theta phase-zero crossings; windows = the inter-boundary spans. Compose from owned ops.
- TEST: cross-speaker syllable-boundary reliability vs the passive peak-counter (the 75% baseline) → then re-run
  the syllable frame (f8576bbc) with these boundaries: does it now carve where the passive read couldn't?
- DONKEY: oscillator = owned DSP; the frame/collapse unchanged.
- KILL: if the entrained oscillator isn't more reliable cross-speaker than the peak-counter, rhythm isn't the fix.

### Stage B — the predictive filter at the transduction
The multi-frame collapse's **prediction goes down** to the front end; the transducer subtracts the predicted and
passes the residual up. Uses the *over-determined* multi-frame prediction (speaker × lexical × context), which is
far richer than the single forward model the earlier waveform-subtraction KILLs used.
- BUILD (owned): per-frame predicted feature from the current collapse state; residual = read − predicted, fed
  back up. A within-utterance loop (predict → subtract → re-collapse), order-N iterated.
- TEST: does recognising on the residual (with the rich multi-frame prediction) lift cross-speaker over the raw
  read? Specifically does it sharpen the SAME frames (syllable/formant) that were too noisy?
- KILL: if the predict-subtract still cancels signal (entanglement) even with the rich prediction, it's deeper
  than a transduction filter.

### Stage C — active gain / attention control
The cognition **steers** the transducer: amplify/sharpen the expected time-frequency region (the predicted next),
gate the rest. The efferent loop — the agent tuning its own ear toward what it expects to hear.
- BUILD (owned): a gain/sharpness mask over the read, set from the prediction; the agent's control, owned ops.
- TEST: does steering the read toward the prediction lift recognition / reliability vs an un-steered read?
- KILL: if steering doesn't help (or over-focuses and misses the surprise), the open-loop read was already enough.

### Stage D — the continuous tick (real-time streaming)
Process sample/frame-by-frame, never batching the whole utterance — the moving now. Hardest engineering, lowest
research-risk; deferred until A–C show the active read pays on batched data first.

## Donkey boundaries (hard)
- The transducer is the **sense** (the read) — owned DSP, NO net in it. The SSL partial-universe-recovery may
  feed it (perceive-with-it), but the oscillator/filter/control are owned.
- The **cognition** (collapse, frame-inference, decision) stays the agent's, unchanged — these stages improve
  what's *fed* to it, not the decision.
- Held-out speakers never banked; CortexLoop untouched; LOSO ungameable.

## Risks / longest poles
1. **Entrainment robustness** (Stage A) — does a single envelope oscillator entrain reliably across speakers/rates,
   or does it need multi-band / adaptive-rate? Most likely the real difficulty.
2. **The predictive filter re-hitting the entanglement wall** (Stage B) — the richer prediction may or may not
   escape what the linear subtracts couldn't.
3. **Closed-loop instability** (B+C) — predict→subtract→re-read can oscillate; needs the temperature/abstain
   damping the cognition already uses.
4. **Real-time** (Stage D) — bounded engineering, deferred.

## First concrete step
Stage A only: build the entrained-theta sampler, measure cross-speaker syllable-boundary reliability vs the
passive peak-counter, and re-run the syllable frame with the new boundaries. It directly tests "the passive
interface failed the frame, the active interface fixes it" — the cheapest, most direct validation of the whole
thesis, and it reuses the syllable harness already built.

## Success criteria
- **Primary:** the active read makes a previously-KILLed frame (syllable, then formant) *carve* — i.e. the same
  frame + same cognition lifts cross-speaker once fed an active/self-clocked/predicted read instead of a passive one.
- **The artifact:** an agent that *tunes and clocks its own senses* — perception as an act, the motor-perceptual
  loop at the boundary, not a passive recorder feeding a smart decoder.
- **The thesis:** the cognition was never the limit; the interface was — and the same collapse, given a live read,
  is what the cognition was always waiting for.
