# Numeric relation model-misspecification v1.1 amendment

V1's learner/held-out capture remains descriptive, but its query-policy
analysis is invalid: the runner passed raw row lists where the selector
requires environment dictionaries, so it did not actually issue a query.
V1.1 corrects that runner binding and records an explicit selector reason.
It also changes the query-selector implementation: a failed Term evaluation
is represented as a distinct prediction outcome, and failed candidates are
removed after an oracle label arrives. The candidate inputs, training labels,
target relation, operator grammar, budgets, and held-out grid remain exactly
those frozen in v1.

Rerun the same five paired panels under a new source lock. Require that query
inputs are mappings with the four declared feature keys, independent replay of
prediction buckets and candidate elimination, complete held-out rescores, and
unchanged source hashes. Compare query availability, false singleton
frequency, empty-version-space detection, and selector cost to v1 as a
diagnostic baseline only.
This amendment does not add a model-adequacy guarantee: a unique survivor may
still be wrong on unobserved inputs.
