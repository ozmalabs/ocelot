# PREREG — the draw→order map: how much of ABIDES's RNG entanglement is OBSERVABLE through Tier-A?

**Committed BEFORE any number.** This is the real Track 3 investigation. Its
output is INFORMATION about the shape of the problem, not a speed number. Per
CLAUDE.md: a rung exists to hold a transferable shape, not to fit a benchmark;
"synthetic-proven mechanism ≠ benchmark value, report both." Phase 2's +13%
elision stands as a safe floor; this does NOT replace it — it goes after the
thing worth knowing, which the norm (and everyone who just accelerates ABIDES)
leaves unexamined.

## The reframe (why the norm's "avoid" is the target)

The audit said: reproducing ABIDES's `np.random.RandomState` stream bit-for-bit
is the Tier-A crux, so AVOID owning the loop. Everyone inherits that conclusion
and ends up accelerating only the RNG-free periphery — same ceiling (~1.6×),
same results as everyone. The unexamined assumption inside "RNG-exact is
required" is that **the draws matter as numbers.** They do not. Tier-A checks the
observable TRACE: exact event multiset + fill sequence + Kendall-τ≥0.999, with a
±1µs timestamp tolerance. The draws matter only through the ORDER they induce on
events. So the real object is the MAP

    draw stream  ──(event-ordering map)──►  observable trace (up to Tier-A tolerance)

and Tier-A constrains only the PROJECTION (the trace), never the pre-image (the
draws). The question worth answering — the one that produces information — is:
**how much of the draw entropy is actually observable through that projection,
vs projected out by the tolerance and the deterministic tiebreak?**

## The mechanism, pinned from the real code (so the experiment perturbs the right thing)

- Each message's delivery time: `deliver_at = sent_time + int(latency)`, where
  `latency` is the per-message RNG draw (`config.py get_latency`:
  `lognormal`/`uniform`/`pareto`, clipped to `[min_ns,max_ns]`).
  (`kernel.py:619,651`)
- The event calendar is a `PriorityQueue` ordered on
  `(deliver_at, (sender_id, recipient_id, message))` (`kernel.py:651`). The pop
  order (`runner`: `self.current_time, event = self.messages.get()`,
  `kernel.py:315`) IS the event order that produces the trace.
- **The tiebreak on equal `deliver_at` is `(sender_id, recipient_id, …)` —
  DETERMINISTIC, draw-independent.** So a draw changes OBSERVABLE order ONLY when
  it moves a message's `deliver_at` across a NEIGHBORING message's distinct
  `deliver_at`. A draw that stays within the gap to its neighbors changes only a
  timestamp — and if that move is <±1µs it is invisible to Tier-A entirely.

This makes the entanglement MEASURABLE, not axiomatic: the draw→order coupling
is exactly the distribution of MARGINS between each message's `deliver_at` and
its nearest queue neighbor, relative to the draw's own spread.

## Hypotheses (falsifiable, pre-declared, whichever way it lands)

- **H-D1 (the headline — is exactness reducible?):** across the public
  scenarios, MOST latency draws are NOT order-pivotal: the margin from each
  message's `deliver_at` to its nearest neighboring distinct `deliver_at` is
  large relative to the perturbation a re-draw would produce, and/or the moves
  are within ±1µs. Operationalized two ways, both measured:
  (a) **Analytic margin measure:** instrument `send_message` to record, per
      message, `deliver_at` and the margin to the nearest OTHER `deliver_at` live
      in the queue. Report the distribution of margins vs the draw spread
      (interquartile range of the latency distribution). The ORDER-PIVOTAL
      FRACTION = fraction of messages whose margin is smaller than the draw's own
      typical jitter (i.e. a plausible re-draw would reorder them).
  (b) **Empirical perturbation measure:** re-run each scenario with the latency
      RandomState perturbed (a different latency seed ONLY — agents' decision RNG
      held fixed), and measure how much of the observable trace changed under the
      Tier-A comparator: Δevent-order (Kendall-τ vs the baseline trace), Δfill
      sequence, and how many events moved >±1µs. This is the DIRECT observable
      sensitivity: what fraction of Tier-A-relevant structure is invariant to the
      latency draws.
  **CONFIRMED** iff a substantial fraction of Tier-A structure is draw-invariant
  (order-pivotal fraction well below 1, and/or perturbed traces retain
  Kendall-τ≥0.999 on a large share of events). **NULL** iff nearly every draw is
  order-pivotal (dense entanglement) — see below.

- **H-D2 (agent-RNG vs latency-RNG separation):** the observable order depends
  much more on the AGENT decision draws (what/when to order — the event SET) than
  on the LATENCY draws (the delivery-time perturbation — the event ORDER within
  near-ties). Measured by perturbing the two RNG streams SEPARATELY (latency-only
  vs agent-only) and comparing which changes the Tier-A observables more. If the
  event SET is agent-RNG-determined and the latency-RNG only jitters timestamps
  within tolerance, then a fast engine must reproduce the agent draws (the SET)
  but has FREEDOM on the latency draws (the jitter) — a strictly weaker
  requirement than "reproduce every draw."

- **H-D3 (effective dimension):** the draw→order map has low effective dimension
  through the Tier-A gate — most of the latency-draw entropy is projected out
  (absorbed by the ±1µs tolerance + the deterministic tiebreak + large margins).
  Measured as: bits of draw entropy consumed vs bits of observable-order entropy
  that actually pass the Tier-A comparator. A large gap = the map is a heavy
  projection = a fast engine can live on the lower-dimensional observable
  manifold.

## What each outcome MEANS (the information, pre-committed)

- **H-D1 CONFIRMED / H-D2 separation / H-D3 low-dim** → the norm's "reproduce
  MT19937 bit-for-bit" is FALSE as stated. The real requirement is: reproduce the
  agent-decision event SET, and reproduce the latency-induced order ONLY at the
  measured order-pivotal points (a small, characterizable set), with freedom
  elsewhere. That is a genuinely new, transferable claim about discrete-event
  sims under a tolerance gate — and it re-opens the audit's "AVOID" as a
  measured, viable path (own the loop in Rust, defer to numpy ONLY at pivots).
  This is the shape worth holding.
- **H-D1 NULL (dense entanglement)** → every draw is order-pivotal; the trace is
  a faithful high-dimensional projection of the draw stream; exactness is
  irreducible. This JUSTIFIES the norm's avoidance WITH EVIDENCE instead of
  inheriting it, and it is itself a real result about ABIDES-class sims (the
  entanglement is structural, not incidental). Reported as the headline finding,
  not buried.

Either way the output is a characterization of the draw→trace map, which
transfers to ANY discrete-event sim graded under a tolerance comparator — that
is the information this rung exists to produce.

## Method / discipline

- Perturb via SEED, not by editing the engine's math (keep the scored engine
  intact); the latency draws come from a seeded RandomState (`config.py`), so a
  latency-only vs agent-only perturbation is a controlled seed split — verify the
  streams are separable in the config first, and if they share one RandomState,
  report that (it would itself bound H-D2).
- Measure on the PUBLIC scenarios across families (the margin/perturbation
  distributions will differ by family — latency-edge-case pareto scenarios vs
  dense agent-mix; report per-family, the shape is the point).
- Use the REAL Tier-A comparator (`semantics.py::check_tier_a`) as the observable
  yardstick — Kendall-τ, fill sequence, ±1µs coverage — never a bespoke metric.
- PREREG-then-measure; report the whole distribution, not a headline scalar;
  nulls are the finding; no fabricated numbers. This produces INFORMATION about
  the problem's shape; a faster submission is not the deliverable and its absence
  is not a failure.

## Deliverables

- `T3_DRAW_ORDER_RESULTS.md` — the margin distribution (per family), the
  latency-only vs agent-only perturbation sensitivity (H-D2), the order-pivotal
  fraction (H-D1), the effective-dimension gap (H-D3), and the pre-committed
  interpretation of whichever way it landed. The transferable shape stated
  plainly.
- the instrumentation (a build-time patch logging `deliver_at`+margin, and a
  seed-split perturbation harness) — reused ABIDES patch mechanism, pinned
  checkout untouched.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
