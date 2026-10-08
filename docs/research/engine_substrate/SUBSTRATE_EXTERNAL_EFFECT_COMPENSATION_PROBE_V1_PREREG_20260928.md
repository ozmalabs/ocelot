# External predicate effect compensation probe v1

## Question

After a versioned external predicate changes from true to false, does the engine undo an earlier effect, and what do explicit compensation rules accomplish?

## Design

- Three independent fresh processes; each builds three independent arms: `sticky_attr`, `compensating_attr`, and `retractable_edge`.
- Each arm has one `trigger` match and a file-backed `UseTool` predicate keyed by graph `resource_rev`. Resource revisions are `r0=0`, `r1=1`, `r2=0`.
- `sticky_attr`: true rule writes `accepted=1`, with no false-case rule.
- `compensating_attr`: true rule writes `accepted=1`; false rule uses `set_attr_if_different` to set `accepted=0`.
- `retractable_edge`: true rule adds `accepted`; false rule deletes that edge.
- Sequence: settle at r0; advance graph revision to r1 and settle; mutate the currently referenced r1 resource to `0` without graph changes and settle; publish r2=`0`, advance graph revision to r2, then settle and record graph state and callback calls.
- Lock source/native inputs and preserve per-phase graph projections and resource hashes.

## Gates

All workers must complete all arms with identical source/native locks. Initial state is false; r1 yields a positive effect; external-only change causes no callback and leaves state unchanged; r2 re-evaluates false. Final state must expose whether each correction strategy preserves, compensates, or deletes the prior positive result. These are behavior gates, not a requirement that the substrate automatically retract effects.

## Limits

The probe tests one rule shape and one fixed resource sequence. A compensation rule is explicitly authored and does not provide truth maintenance in general. It does not measure every rule ordering, concurrent updates, rollback, or natural use frequency. `set_attr_if_different` and `del_edge` are the tested correction primitives; source inspection indicates no `DelAttr` effect.
