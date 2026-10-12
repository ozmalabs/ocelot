# Thoughtexperiment effect-trace versus rematch counterfactual v1 preregistration

## Question

When a known failing node is available, does effect-value tracing reduce total diagnosis cost relative to (a) endpoint-only events plus full graph/rule rematching and (b) endpoint-only candidates tested by counterfactual rule-effect omission? The study measures whether intermediate trace information beats a stronger computational baseline, not whether it beats an oracle with hidden labels.

## Held-out cases and branches

Use 80 deterministic held-out graph/rule cases across 4/8/16/32 bound targets/effects (20 per size). Each case has one anchor, one typed slot edge per target, one conjunction binding all target variables, and one effect per variable. Clause order, node creation order, and effect order are separately shuffled. Exactly one effect sets the queried target's `health` to 999; the other effects set health to 1. The query supplies the failing node ID and the rule name.

Capture one immutable `shared_graph_pages` snapshot before closure. Compare three policies from that same base: (1) endpoint event report, then test candidate effect omissions in index order until the target no longer has health 999; (2) endpoint event plus a complete conjunctive rematch against the branch's full graph and the authored rule body, then test its predicted omission; (3) per-effect value trace, then test its predicted omission. Every omission is a fresh shared-page snapshot fork whose branch-local rule replaces the candidate effect out of the active rule; settle one firing and inspect only that branch's target. The primary graph and rule revision must remain unchanged.

Measure observer, rematch, branch, and total diagnosis wall/CPU times separately. Snapshot creation and case generation are shared setup outside the timed arms. Counterfactual branch construction, rule replacement, closure, and outcome check are included in branch time. These are native shared-graph-page branches, not operating-system process forks.

## Gates

Require three source-locked worker replications; exact 80-case matrix; one progressed event per arm; endpoint reports with no per-effect payload; exact full-rematch and trace localization; exact counterfactual cure only when the true effect is omitted; event-only search attempts equal `bad_effect_index + 1`; one branch for each exact policy; identical closure status; and unchanged primary graph/rule revision. Report medians by size and overall. Do not preregister a speed winner; compare measured end-to-end diagnosis time and branch count.

## Claim limit

This improves on a report-only random candidate baseline by including actual graph/rule rematching and isolated counterfactual branches. The generator remains an authored single-rule family with a supplied failing node and explicit SetAttr effects. Results do not establish natural-task diagnosis utility, general counterfactual planning, learned cause selection, or substrate self-improvement.
