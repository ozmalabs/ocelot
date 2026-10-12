# Live self-report current-source regression probe v1

Date: 2026-09-27

## Question

On the current full-seed source snapshot, does the previously successful live instruction `report your organisation` still select the `self_report` route and resolve one Goal, or does it fall through to a generic unsupported-faculty response?

## Method

Run three fresh processes. Each loads all seeds with `load_all_seeds`, records loaded and failed seed IDs, sends the same instruction as Alice, and captures the inbound route, exact reply, comprehending Goals and lifecycle, graph size/digest, and source fingerprints at worker start/end. The driver records the same source fingerprint before and after all workers. No frame or noise intervention is applied.

This is a source-regression reproduction, not a randomized capability sample. The response/failure hypothesis was formed after a preliminary current-source probe; the three scheduled fresh boots are the confirmation set. No code changes are made to the substrate by this diagnostic.

## Gates

1. Three unique worker PIDs and identical locked source inputs at driver start/end and every worker start/end.
2. Exact route, reply, and Goal behavior repeat across all three workers.
3. The observed failure class is reproduced: no communication route, no Goal comprehending the inbound Message, and the generic held-faculty gap response.
4. The failed seed list and final semantic graph size/digest repeat exactly.

## Interpretation boundary

This establishes whether one previously measured route currently regresses under the full boot. It does not identify a single causal code change, characterize all conversation routes, or estimate a natural-task failure rate. Seed-load failures may be associated with the route shortfall but are not assumed causal without a targeted intervention.
