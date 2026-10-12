# Shared-substrate matched scope endpoint comparison v1.7 preregistration

## Question
On the identical adapted graph and exact four fixed-frame conditions, does the global `st_settle` fold produce different endpoint `act`/`rate` outcomes or closure work from the root-scoped fold?

## Design
Prepare and adapt the paired fixture once under the registered root-scoped schedule (seed 20260934, 3,000 retinal development steps per Retina, 2,000 paired adaptation presentations). Freeze plasticity and retain the exact prepared graph dictionary. Build an isomorphic global-rule fixture from the same seed and restore that exact graph state into it. Before probing, require identical Retina/SUnit identities and graph digest after restoration. This matched transfer intentionally holds learned weights and state fixed; it estimates endpoint-scope effects conditional on a root-scoped-adapted state. It does not compare how global versus root-scoped adaptation would learn.

Run both rule variants over the same four conditions from restored copies of the prepared graph: both blank, B exact grating only, A exact grating only, both exact gratings. The B frame is orientation 0°, phase 0°, period 4; A is orientation 45°, phase 0.3, period 4. Capture per-unit `act`, `theta`, `rate`, update stamps, retinal bursts, full closure status/work, and graph digest. Bound each closure at 1.6M cumulative progress. No between-condition learning is allowed.

## Analysis gates
Require common starting graph identity for each paired condition, all condition records in both modes, terminal statuses within the cap, threshold-equation consistency `rate=max(act-theta,0)`, exact act/rate stamps, and exact comparison of each unit's outputs across scopes. Report closure progress rather than interpreting timing as a general speedup. Any graph transfer mismatch invalidates the matched comparison and must be reported without fallback claims.

## Claim boundary
One seed, one small two-sheet fixture, one learned state, four endpoint presentations, and one-sided adaptation history. A pass can establish endpoint parity/difference on this matched state only; it cannot establish general scope safety, natural-task locality, or tractability at scale.
