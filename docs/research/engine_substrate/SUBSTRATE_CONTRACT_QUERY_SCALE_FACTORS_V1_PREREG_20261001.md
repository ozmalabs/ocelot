# Contract query scaling factors v1 — preregistration

## Purpose

The prior H=8/32/128 panel changed candidate count, Term depth, and grid size together. This follow-up raises the hypothesis ceiling and varies expression depth and input-grid size independently around a shared H=32 baseline.

## Factor cells

Use two fresh workers for each of seven cells:

| Cell | H | Coded depth K | Neutral padding D | Candidate inputs N |
|---|---:|---:|---:|---:|
| Baseline | 32 | 5 | 0 | 20 |
| Candidate scale 256 | 256 | 8 | 0 | 32 |
| Candidate scale 512 | 512 | 9 | 0 | 36 |
| Term depth 16 | 32 | 5 | 16 | 20 |
| Term depth 64 | 32 | 5 | 64 | 20 |
| Grid 100 | 32 | 5 | 0 | 100 |
| Grid 500 | 32 | 5 | 0 | 500 |

All versions are balanced binary-coded hypothesis Terms agreeing at x=0, and each selector run uses an external labeler for a fixed target. Candidate input grids contain all K informative points and N-K unanimous decoys. Neutral padding wraps each Term in false constant-condition branches, increasing evaluator depth without changing its function. This is a controlled engine workload, not naturally occurring program data.

## Measures

Lock source/native/harness hashes and record fresh PIDs, H/K/D/N, exact query sequence, native evaluation calls, total selection-loop wall time, time per query, and peak RSS. Independently verify all selected queries, target labels, max-entropy choices, and exact operation counts. Do not pool the three scaling axes: estimate each factor against the common baseline. Preserve every worker result and failure.

## Interpretation limits

These cells can expose scaling in the selector's nested work and native Term depth cost through N=500, D=64, H=512. They do not prove asymptotics, cover arbitrary Term operators, or validate model adequacy; those limits and the previous false-singleton case remain in force.
