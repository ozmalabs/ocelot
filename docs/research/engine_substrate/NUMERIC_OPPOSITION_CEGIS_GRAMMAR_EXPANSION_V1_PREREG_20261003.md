# Counterexample-triggered grammar expansion v1 preregistration

Date: 2026-10-03

## Question

Can a bounded learner repair false singleton or no-fit outcomes by using oracle counterexamples to trigger one predeclared grammar expansion?

## Frozen design

Use the five XOR-target workers from the locked CEGIS adequacy capture. The first-stage learner used `Neg`/`Eq`/`And`; its capture is frozen before this follow-up. For each worker, preserve its original training labels and all first-stage query/label pairs. If its final candidate is a singleton, examine a separately frozen 24-row reserve pool in seeded order. Query the oracle at each row until the singleton disagrees or the pool is exhausted; a disagreement triggers expansion. If stage one returned no fit, expansion triggers immediately. The only allowed expansion is adding `Not`, yielding `Neg`/`Eq`/`And`/`Not`; no other grammar or task data are added. Then rerun enumerative synthesis from every revealed label, no constants, size cap 9, 12-second limit. Freeze the first fitting term, or report no-fit/timeout. Score frozen terms on the same disjoint 1,296-case fractional holdout only after search.

## Gates and claim boundary

Lock the upstream source lock and capture hashes, reserve rows, sources, and analyzer before capture. Replay reserve selection and oracle labels, validate the final term against all revealed examples, preserve timeout/no-fit outcomes, and independently rescore the holdout. This tests a human-authored escalation policy and one related XOR task only; it does not show that the substrate invents primitives, chooses a useful grammar expansion autonomously, or transfers to unrelated tasks.
