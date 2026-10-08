# Candidate-boundary-directed probe repair v1 preregistration

## Question

Can numeric comparison literals in a surviving Term guide an added probe that
separates a candidate whose false condition lies just outside the fixed
coverage domain?

## Frozen inputs and policy

Use the five opposition panels and three Terms from the locked false-safe
coverage experiment. Extract a threshold from each candidate `Lt(Var, Lit)`
comparison. For a threshold `c` and the exact opposition relation in the
candidate pool, construct candidate probes at `ax = c-0.5, c, c+0.5`, with
`ex = -ax` and other variables zero. Pass these probes to the native
discriminating-input selector together with the frozen covered pool. Query
the task oracle at its selected input once, filter candidates using the
observed Boolean label, and partition the survivors over old and added probes.

## Analysis and limits

Replay the selector input and candidate transitions. Require both exact
Terms to remain and the restricted term to be eliminated; independently
score survivors on the registered holdout and balanced wide domain. Compare
to the current policy's locked false-safe result. This is a targeted numeric
repair control: extracting one comparison literal and solving the declared
opposition equation is not a general term-directed probe algorithm. Candidate
construction remains harness-supplied; broader task families and unknown
operator forms remain unevaluated.
