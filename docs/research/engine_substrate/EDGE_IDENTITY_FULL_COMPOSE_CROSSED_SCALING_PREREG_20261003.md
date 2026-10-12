# Edge identity full-compose crossed scaling preregistration (2026-10-03)

## Question

How does current-source edge-identity composition cost change jointly with the
number of identity fields and unrelated graph nodes, through enumeration,
graph-resident `EditSite` materialization, native cue scoring, and variant
construction?

## Frozen design

Use `compose_general_structural_variant` on the actor-recipient rule with total
identity-field counts 2, 4, 8, 16, and 32. The rule always has `actor` and
`verb` fields; additional fields are bound copies of the actor attribute. Cross
these counts with 0, 1,000, and 10,000 unrelated graph nodes. The cue contains
`actor verb pair identity`, so the expected unique maximum is the two-field
`actor+verb` site. One warmup and three measured trials per cell, in a frozen
shuffled order. A trial is a success only if the intended operator and exact
site are selected, the proposal builds, the active primary rule store is
unchanged, and the enumerated site count equals the independently computed
singleton/pair/full-set formula plus edge sites.

The candidate cap is 600 sites per trial; the largest preregistered field
count produces 532 attribute sites and remains inside that cap. Graph setup is
timed separately from composition. Record wall time, site counts, process RSS
before and after composition, outcome, and candidate correctness. Do not
extrapolate beyond these synthetic rules or claim general graph scaling.

## Interpretation limits

The unrelated nodes do not participate in rule matching. This is a graph-size
stress control, not a natural workload or a frame-locality test. Added identity
fields are synthetic bound copies. The experiment measures the complete
composer path for a supplied rule and cue; it does not measure autonomous cue
generation, residual grounding, or learning a new identity dimension.

## Stop and validity rules

Abort a cell if candidate count exceeds 600, the source/build lock drifts, the
native engine is stale, or the harness does not select the exact expected
site. Preserve partial output only as diagnostic and do not score it as a
valid capture. The independent analyzer must verify source and lock hashes,
all 45 measured trials, site-count arithmetic, selection correctness, and
primary-rule immutability.
