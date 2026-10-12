# Conversation shared-evidence boundary wakeup preregistration (2026-09-26)

## Question

When a shared read-only evidence node changes between closure epochs, does notifying both dependent frame owners preserve the full-closure projection? Does omitting one dependent frame produce a detectable stale result, and can a subsequent full pass recover exact parity?

## Frozen workload and arms

Use the locked read-only-boundary conversation fixture: frame-local mutable deliberation candidates and one immutable-during-closure evidence node shared by each adjacent pair; the patched native scoring rule reads the evidence node's `boundary_value`. Test chain sizes 2, 4, and 8; mutate the first shared boundary only, from 1.0 to 4.0. Run three fresh-process replicates for each of three arms (27 workers total):

- `full`: bump the epochs of both endpoint deliberations and settle through native full closure.
- `required`: bump both endpoint epochs and settle only frames 0 and 1 through repeated native scoped closure, then use full closure as a zero-work fixed-point oracle.
- `omitted`: bump both endpoint epochs but settle only frame 0. Save this pre-repair projection, then run a full catch-up pass and save the recovered projection and progress.

The epoch bump invalidates each local candidate score cache in both dependent frames; the deliberate omission is solely the absent frame execution/notification. Frame 1's old winner is expected to become stale after the first edge value rises above its neighboring boundary value. Record baseline and post-mutation projections, selected ids and scores, notified/omitted frame ids, full-probe/catch-up progress, candidate and Term counts, per-stage wall/CPU time, and native/source provenance.

## Gates

Require exact 27-cell randomized schedule and unique worker PIDs; exact 2/4/8 chain ownership, with each shared boundary node owned by exactly its adjacent frames and each mutable candidate local to one frame; unchanged baseline projection across all arms; the scoring rule's explicit boundary read; boundary value remains read-only during closure; fixed points in full and required arms; exact required-vs-full projection parity and zero-work full probe; stale projection and positive catch-up work for every omitted arm; and exact recovered-vs-full parity after catch-up. Cost results are descriptive and cannot override semantic failure.

## Claim limits

This is one authored native conversation rule family and one chain edge mutation. It tests explicit caller notification and omission detection, not native observer delivery, arbitrary read/write effects, dense or cyclic boundary topologies, natural event rates, general GALS, or asymptotic cost. The current fixture supplies frame ids to the runner; automatic effect-to-frame mapping is not evaluated.

## Provenance

Lock this protocol, runner, analyzer, the read-only-boundary runner/result inputs, conversation seed/materializer, and engine sources. Store a new lock and capture separate from the immutable-evidence and shared-mutable-candidate studies.
