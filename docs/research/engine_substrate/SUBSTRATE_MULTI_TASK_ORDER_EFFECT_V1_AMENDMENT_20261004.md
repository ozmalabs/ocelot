# Multi-task order-effect v1 amendment

Date: 2026-10-04

The preregistration specified the legacy scene contract, including one
`_ensure_describe` faculty build with a rule delta of 18. The capture records
the direct action wrapper, prompt-linked Goal, reply, and lifecycle events, but
does not wrap `_ensure_describe`; therefore it cannot evaluate that conjunct
directly. All ten scene-description runs fail two other required conjuncts:
the exact expected scene reply and a resolved `describe_scene` Goal. The full
legacy contract therefore fails in every scene run regardless of the omitted
faculty-build measurement. The 30/50 contract count is consequently valid for
this panel, but the scene failure diagnosis is incomplete. A follow-up that
needs faculty-path attribution must capture its call count and rule delta.

## Source closure note

Post-capture provenance review found that the base engine source closure did
not include the dynamically imported `scripts/arc_self_report.py`, which
implements the scene faculty build and request view. The counterbalanced
capture therefore proves repeatable outputs within its recorded lock but does
not independently bind every scene-path source dependency. The later
[route-diagnostics v1.1 result](SUBSTRATE_CONVERSATION_ROUTE_FAILURE_DIAGNOSTICS_V1_1_RESULTS_20261004.md)
adds explicit hashes for this script and the direct language-production
dependencies, and reproduces the describe-path failure in two fresh workers.
The ten-worker counterbalanced panel still requires a rerun with this complete
dynamic dependency list before it serves as a fully source-closed benchmark.
