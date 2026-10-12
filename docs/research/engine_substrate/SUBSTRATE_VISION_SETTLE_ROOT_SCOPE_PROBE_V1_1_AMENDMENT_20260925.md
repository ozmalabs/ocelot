# Root-scoped settle probe v1.1 amendment

Date: 2026-09-25. This amendment preserves v1's preregistration and failed raw result. No production seed or engine source changed.

## Correction
V1 predicted that the root-scoped arm would output `[0.5, 0.5]`. The executed probe returned `[0,0]` in both B conditions. The corrected value follows directly from the authored equation: for A, local neighbor mean is 1 and A-only mean is 1, so `max(0 + 1 - 1, 0) = 0`. For B=[0,0], both terms are zero; for B=[1,1], both are one. Thus root-scoped prediction is `[0,0]` for A in both cases.

## Confirmatory run
Run the same paired fixture and transformation as v1, using the corrected expectation. Preserve v1's protocol, runner source state via git history/worktree evidence, and raw output. Required results: authored global outputs `[0.5,0.5]` then `[0,0]`; scoped outputs `[0,0]` in both conditions; all four calls progress and complete; scoped A is invariant to B. This confirms DSL expressibility and scope semantics only. No quality, convergence, or cost claim is implied.
