# ProblemShape observation-population scale extension v2 preregistration (2026-09-27)

## Question

Do the previously measured ProblemShape recurrence-guard work and dynamic/frozen state transitions persist when observation populations grow from N≤8 to N=16, 32, and 64?

## Design

Run one fresh full-seed process per cell in a 3×2×2 design:

- N = 16, 32, 64 observations.
- Task mix = recognition or recurrent residual.
- Codebook = normal dynamic rules or frozen (`ps_mint` removed before observations).

Reuse the v1.0 population-sweep worker function without modifying it; the v2 runner calls that function directly with larger N, rather than the legacy command-line choices. Preserve exact inputs, fixed order, scaffolding, seed set, audit counters, expected status/mint oracle, and rule-attributed counts. Lock the v2 protocol/runner, the reused worker and its measurement helper, current source/native closure, selected seed payloads, and native build freshness before and after all workers. Capture each child process's complete JSON record and stderr. This is an operation-count experiment; all native scale audit counters are enabled during observations, so wall/CPU values are secondary descriptive data only.

## Hypotheses and gates

- Recognition-only observations remain recognized with zero mint in dynamic and frozen arms; dynamic `ps_mint` recurrence-guard candidate checks equal N(N+1)/2, and frozen mode removes those checks.
- Recurrent-residual dynamic mode mints exactly once, re-decodes and recognizes later observations; frozen mode mints zero and leaves observations residual.
- All observations settle at reported fixed points, with exact expected status transitions and unchanged full-seed/native identities.
- Twelve distinct worker processes (one per cell), no source-lock drift, and all records retained. Report per-rule candidate pairs and term evaluations by prefix and cell. Do not fit a polynomial from three new sizes alone; compare counts with the v1 N=2/4/8 observations as a combined controlled envelope.

## Limits

This extends one project-authored recurrence pathway, not a natural novelty distribution or a rich hypothesis class. The frozen arm is an ablation rather than a deployment profile. It does not measure false-mint rate, transfer, prior-task retention, rollback, or end-to-end learning value. High boot cost is charged and reported, but candidate counts—not timing—are the primary mechanism scale measure.
