# Thoughtexperiment attribute-site active query v1 — preregistration

## Question

Does graph-resident selection of a typed attribute-swap site compose and generalize to a newly authored target rule, and does active querying select the useful proposal over the unmodified fault rule?

The new target is `classify_meter_delta`: it classifies a request from a measurement's `bad_score`, while the correct decision uses `good_score`. A secondary `audit` effect references `good_score`, making the ordered swap site structurally applicable. The residual cue names the ordered site `bad_score to good_score`; site choice is therefore prompted and this gate measures target/operator/site selection plumbing, not discovery of which field is wrong. Candidate predictions execute the native rule in isolated branches. Shared-page snapshot CoW is compared with full-copy branches.

## Procedure

Four workers create the target and expose only this mutable rule. The normal structural composer receives `classify meter delta`, `swap`, and the ordered-site phrase. Before oracle labels are released, each worker freezes its proposal, semantic match against generic candidate enumeration, and query choices. For each backend and neutral rate (0%, 50%, 90%, 99%), a 100-input pool contains either agreeing score fields (`bad_score == good_score`) or discriminating fields (`bad_score == -good_score`, with `good_score` alternating signs). The two hypothesis Terms identify the fault and proposal. Each hypothesis/input evaluation uses a new isolated branch and one native closure.

After all orders are frozen, the oracle returns `HOT` iff `good_score > 0`, else `COLD`. It adjudicates the selected query and seeded random probe. Fresh held-outs include positive, negative, zero, and a second positive score. Receipt, target preservation, fixed-point, source stability, and CoW/full-copy semantic parity are checked.

## Measures and pass conditions

Pass requires all 32 backend/neutral-rate query orders to be valid one-bit discriminators retaining only the composed proposal; every proposal must select target `classify_meter_delta`, operator `swap_term_leaf`, and site `bad_score -> good_score`, and semantically match a generic host-enumerated candidate. The proposal must pass all four held-outs; the fault must fail all nonzero held-outs. Both backends must agree exactly on query and held-out outputs, all branch receipts and fixed points must pass, and the primary substrate must remain unchanged. Report composer, fork, patch, closure, and total query costs. Four workers on this authored rule do not establish a general complexity or performance law.

## Scope boundary

Python creates the target rule, fault interpretation, cue, pools, oracle, and orchestration. The graph Term selects the rule/operator/site, and generic Python code materializes the variant. The task is synthetic, the site cue is answer-bearing, and the hypotheses are supplied. This measures transfer to a new rule shape and edit operator, not autonomous diagnosis or open-ended learning.

## Reproduction

Run `python3 evaluation/substrate_capability/thoughtexperiment_attribute_site_active_query_v1.py --lock`, `--orders`, and `--score`, followed by `python3 evaluation/substrate_capability/analyze_thoughtexperiment_attribute_site_active_query_v1.py`.
