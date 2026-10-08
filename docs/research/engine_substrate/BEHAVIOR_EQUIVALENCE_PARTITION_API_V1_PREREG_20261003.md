# Finite behavior-partition API and cost study v1 preregistration

## Question

Can the query layer return a deterministic, typed partition of surviving Terms
by their predictions on an explicitly supplied finite probe set, and what is
the cost as candidate count H and probe count P grow?

## API contract

`partition_hypotheses_by_behavior` receives a stable evaluator, unique-ID Term
hypotheses, and finite JSON probe environments. It returns typed prediction
signatures, candidate IDs grouped by equal signatures, H, P, and a digest of the
probe set. Evaluation failures are a distinct bucket. The result describes
agreement only on the supplied probes; it makes no claim outside them. It does
not see oracle labels, task IDs, or held-out examples.

## Measurement

Replay all 50 original/zero-aware survivor sets from semantic-equivalence v1
and compare class membership against its independent grouping implementation.
Measure five repetitions per cell. Separately measure the H×P work curve for
H={1,2,4,8,16,32,64} and nested P={4,8,16,32,64} probes using locked initial
candidate Terms from one panel per task; when H exceeds distinct Terms, cycle
Terms with unique IDs and label that scaling arm synthetic. Count evaluator
calls exactly. No oracle or holdout work is included in this API microbenchmark.

## Analysis gates

Lock the query API, evaluator/native build, runner, analyzer, source capture, and
all probe/candidate inputs before measurement. Independently reconstruct each
finite partition, verify typed errors and probe digests, check exactly H×P
evaluator calls per invocation, and report latency by H/P and actual panel.
The study measures finite grouping cost and behavior only; it does not prove
semantic equivalence outside probes or evaluate a policy that chooses the
probe set.
