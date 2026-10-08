# Thoughtexperiment recurrence compose-and-select v1 — preregistration

**Question.** Does the graph-resident evidence selector choose a useful recurrence repair when the failed general-composer proposal is included alongside the existing explicit repair hypotheses?

## Design

Four source/native-locked workers each construct the established `mrl_offer_due_once` fault and eight candidates from the unchanged correction generator. The general structural composer receives the fixed cue `mrl offer due once guard constrain restrict narrow extra condition equality`; its materialized proposal is added as a ninth candidate if its canonical digest is distinct. Candidate order is shuffled by a fixed worker seed. The graph selector receives opaque candidate IDs, not host labels or any held-out information.

For each candidate, collect two fresh training episodes with distinct keyed inputs and independently recompute correctness from exactly one offer per due candidate and zero work at fixed point. Store per-candidate training outcomes as graph evidence in a snapshot branch; the native Term selector must return a unique positive maximum. Freeze all nine descriptors, training outcomes, and the selected digest before scoring. A separate stage rebuilds the fault and candidate set, checks exact descriptor parity, and scores only the frozen winner on two fresh held-out episodes. Also exercise all-wrong and tied-evidence selector controls. Keep candidate generation, composition, scoring oracle, and orchestration attribution explicit.

## Gates

- Lock all active sources, native binary, task adapters, protocol, runner, and analyzer before capture; maintain source stability throughout.
- Each worker has exactly nine unique candidates including the composer proposal; labels are excluded from the selector input, candidate order is deterministic from the locked seed, and train keys are disjoint from held-out keys.
- The native Term returns a unique winner using only the two training episodes per candidate; all-wrong and tie controls abstain.
- The selected candidate is `dedup_identity_fix` and matches the independently recomputed training maximum; it passes both held-out episodes.
- The proposal/evidence nodes remain branch-local; the primary target rule definition is unchanged; the result is bound to a compact returned digest.

Failure is retained and reported. This isolates a substrate-side selection handoff over supplied explicit hypotheses. It does not test candidate invention, independent oracle reliability, open-ended diagnosis, or learning a new operator; the task, cue, host candidate generator, and expected labels are external.

Capture training orders first with `--orders`; run held-out scoring afterward with `--scores`; finish with the independent analyzer.
