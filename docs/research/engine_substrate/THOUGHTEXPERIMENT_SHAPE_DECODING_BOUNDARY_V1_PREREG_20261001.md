# Shape-decoding aperture-boundary v1 — preregistration

**Question:** At fixed node count and edge count, how does a growing focus boundary change rehearsal cost?

Use 100k `ThoughtexperimentNoise` nodes and fractions 0%, 1%, 10%, 50%, and 99%. Starting from the existing path, choose boundary nodes evenly across its index range; for each chosen node replace its outgoing `te_noise_next` edge with an edge from one of the three focus observations to that node. This holds the total node and edge counts constant while growing the number of edges exposed directly at the aperture. Compare scoped full-copy/shared pages × sequential/concurrent fanout 8 × positive/negative candidate × three fresh processes (60 processes). Record realized boundary count/fraction, node/edge counts, candidate wave timing, aggregate worker CPU, phase timings, semantic outputs, and primary-state/provenance checks.

**Gates:** 60 unique processes; complete fraction/backend/mode matrix; exact node/edge counts fixed across fractions; realized boundary count matches the protocol; positive convergence and negative rejection; exact result parity across backends/modes at each boundary fraction/arm; primary isolation; source/native lock; nonnegative timings.

**Interpretation limits:** Replacement preserves edge count but progressively segments the synthetic path; this is a controlled aperture intervention, not an estimate of natural topology. One task and host; no complexity-law claim. Compare medians and shape of the response rather than fitting an asymptotic exponent from five points.
