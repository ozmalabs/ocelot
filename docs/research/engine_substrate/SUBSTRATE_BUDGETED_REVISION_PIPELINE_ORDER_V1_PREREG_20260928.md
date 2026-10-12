# Budgeted staged-revision order and readiness guards v1

## Question

Can a one-pass progress-budget return commit stale derived outputs when max/count/decision rules fire in an adverse order, and do revision-readiness guards prevent that false commit and permit recovery?

## Design

Use three fresh workers, N=2/8/64, and four arms: normal vs reverse rule installation order crossed with unguarded vs guarded stages. Lower the initial unique winner's score and add a revision-1 event with max/count/decision/commit stage edges all present before closure. Run once with `max_steps=1`, capture stamps/outputs, then resume with a large budget and compare to an independent score oracle.

In the guarded arms, count may write only when `max_revision == event.revision`; decision may write only when `count_revision == event.revision`; commit may write only when max/count/decision stamps all match the event. Unguarded controls use the same effects but omit the max/count readiness guards. Stage installation order is max→count→decision→commit or decision→count→max→commit.

## Gates

Both guarded orders must never expose `resolved_revision=1` after the limited pass unless all output fields already match the oracle; the resume closure must end fixed point with all stamps 1 and the correct winner. Normal unguarded order is a positive ordering control. Reverse unguarded order is an expected falsifier: it should reproduce a committed-but-wrong output after the limited pass and remain wrong after full settle, demonstrating that stamps without stage-validity guards are insufficient. Integer counts replicate across workers, excluding timing fields.

## Limits

This is a controlled sequential scheduler order test with all stage edges pre-inserted. It does not test concurrent rule firing, OS kill during Rust execution, persistent restart, other rule families, or a universal ordering guarantee. The readiness guards are an authored construction, not an engine-enforced stage type.
