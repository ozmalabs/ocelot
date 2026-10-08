# Rejected matcher candidate trace probe v1 preregistration (2026-09-26)

## Question

Does the graph access trace record the candidate edge reads that the matcher enumerates when its bound `where` predicate rejects candidates?

## Design

Create one-edge rules `a -probe_edge-> b` with a `where` condition `Attr(a, accepted) == 1`. Compare graph sizes with 1 versus 9 candidate edges. Every edge has a distinct source; exactly one source has `accepted=1`. Run fresh substrates with tracing off/on and the scale audit enabled. The independent work oracle is native `cand_enum` and `cand_tested`; semantic oracle is one accepted binding, one successful pattern-edge event, and fixed-point status.

## Predictions

- `cand_enum` and `cand_tested` increase from 1 to 9.
- The successful `pattern_edge` count remains one because the trace is emitted only at the accepted leaf.
- Attribute reads for the predicate should show the source nodes visited; they do not substitute for concrete candidate-edge identities.
- Traced and untraced progress/status match, plain trace is empty, and no trace overflow occurs.

## Limits

This isolates one matcher-plus-predicate family. It does not characterize all join orderings, graph indices, scheduler work, edge-type scans with no candidates, or natural task distributions. It tests whether edge identities for predicate-rejected candidates are absent from the access trace, not whether all other associated reads are invisible.
