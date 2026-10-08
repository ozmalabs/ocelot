# Exact-linear GenInfer prefilter v1.1 amendment (2026-10-06)

## Trigger and evidence

The feature-on/runtime-on cubic high-bound smoke worker was supervised for
300 seconds and remained in training closure; timeout sent SIGINT and required
SIGKILL after five seconds (worker exit 137). This is a failed engineering
smoke, not a preregistered capture: it used one binary and produced no closure
result or native audit snapshot. In the paired linear pilot, half of the
eligible base attempts fell back to enumeration.

## Narrow implementation amendment

Inspection of the existing `build_candidate` validator shows its first
semantic guard rejects every matrix when transformed signature length differs
from goal relation count. `apply_linear_once` preserves relation count. The
prefilter may therefore classify `source.len() != target.len()` as proven
no-fit and skip enumeration; this conclusion does not depend on stable IDs,
coordinate rank, or coefficient arithmetic. Add a direct differential test
that confirms the historical candidate builder rejects the same mismatched
length input. No other fallback condition or candidate-selection rule changes.

## Counter amendment

The preregistered high-bound condition currently asks an audit-off worker both
for clean timing and for a proof counter. Since scale-audit counters are
intentionally disabled in audit-off mode, use a matched audit-on sibling to
record the proof/outcome counters and an audit-off sibling for timing. Both
remain separately capped at 300 seconds, and audit-on time is excluded from
performance summaries. The high-bound cell remains separate from the matched
main-panel summary.

All other v1 conditions, three build arms, source locking, admission criteria,
and limits remain unchanged. The amendment and source changes must be included
in the v1 lock before any confirmatory worker is run.
