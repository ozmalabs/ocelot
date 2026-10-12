# Challenger selector to receipt and adoption v1 — results

All six independent analysis checks pass across nine source-stable fresh full-seed processes. The challenger selector chose a fresh probe without labels, the existing audit-request API bound that exact singleton descriptor and candidate Term, an independent square labeler supplied evidence, the receipt adjudicator evaluated the candidate, and the real `teach_write_shape_from_example` boundary enforced the result.

| Case | Selected probes | Receipts | Teach outcomes | Held-out transfer |
|---|---|---|---|---|
| Correct square candidate | `x=2` or `x=3` | accepted 3/3 | adopted 3/3; epoch +1 | 4/4 exact in 3/3 |
| Wrong identity, broad domain | `x=3` or `x=4` | rejected 3/3 | refused 3/3; epoch +0 | no candidate emitted |
| Wrong identity, alias domain `{x=1}` | `x=1` | accepted 3/3 | adopted 3/3; epoch +1 | 0/4 exact in 3/3 |

This confirms the selector, provenance-bound request/receipt, and strict adoption gate compose on the live full-seed write-shape path. It also reproduces the key limitation at the actual adoption boundary: a validly bound receipt can authorize a false candidate when the caller's finite domain contains only aliasing probes. Median full-seed boot was 11.93 s; this is integration evidence, not an optimization result.

The selection record and request record are captured together, and the request cryptographically binds the exact selected descriptor and candidate. The receipt does not independently authenticate the selector implementation or label-provider identity; both remain inside the source-locked caller/harness boundary. The helper is not yet wired into routine production acquisition, and the challenger set/domain remain caller supplied. No general self-improvement or natural-task adequacy rate follows.

Artifacts: [protocol](SUBSTRATE_ADEQUACY_SELECTOR_RECEIPT_ADOPTION_V1_PREREG_20261002.md), [selector API](../../../domains/adequacy_probe_selection.py), [runner](../../../evaluation/substrate_capability/substrate_adequacy_selector_receipt_adoption_v1.py), [lock](../../../evaluation/substrate_capability/substrate_adequacy_selector_receipt_adoption_v1_lock_20261002.json), [independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_selector_receipt_adoption_v1.py), [raw capture](../../../evaluation/reports/substrate_adequacy_selector_receipt_adoption_v1_raw_20261002.json), and [analysis](../../../evaluation/reports/substrate_adequacy_selector_receipt_adoption_v1_analysis_20261002.json).
