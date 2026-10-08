# Probe-coverage false-equivalent control v1 preregistration

## Question

Can the current coverage-aware policy return a class containing a near-match
that agrees across every available probe but fails just beyond probe support?

## Frozen candidates and panels

Use the five source-locked opposition panels and unchanged query/coverage
policy. Supply three Terms: `ax == -ex`, the distinct equivalent
`-ax == ex`, and the restricted candidate `(ax == -ex) AND (ax < 4)`. The
restricted candidate agrees on every policy probe and on the registered
fractional holdout, whose `ax` maximum is 3.5, but fails for positive
opposition examples at `ax >= 4`. Candidate formulas are harness supplied;
the case targets coverage adequacy, not hypothesis generation.

## Analysis

Replay labels and survivor transitions from the frozen inputs. Recompute
coverage and behavior signatures over all policy selection/challenge probes.
Score all returned members both on the locked 6,560-row holdout and a separate
balanced wider domain that includes positive opposition cases with `ax >= 4`.
Report whether the policy returns the restricted candidate and its wider
domain errors. The experiment is designed to expose a false-safe return if
the registered coverage condition is insufficient; such an outcome is a
policy failure finding, not a success gate.

## Limits

This is one authored numeric counterexample over five repeated panels. It
does not estimate how often real learned candidates exploit unobserved
boundaries, and it does not test substrate-side candidate generation.
