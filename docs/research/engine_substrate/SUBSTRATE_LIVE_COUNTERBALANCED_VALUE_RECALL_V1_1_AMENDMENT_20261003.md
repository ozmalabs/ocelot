# Live counterbalanced value recall v1.1 amendment

Date: 2026-10-03  
Status: post-capture analysis amendment; the v1 protocol, capture, and analysis are preserved.

## Control oracle correction

The v1 fresh-control oracle required only that neither numeral occur. The captured reply was `ERROR: no communicative response could be generated.`, which contains neither value but is not an epistemic abstention. Thus v1 incorrectly counted all three fresh-control workers as passes. V1.1 requires a substantive non-error reply that explicitly signals lack of knowledge/information and contains neither value. The same non-error requirement applies to the value arms. This correction is applied to the already captured outputs; it does not change the record that the v1 oracle passed the fresh controls.

## Replicate canonicalization

V1's raw graph digest gate fails in all three conditions. Pairwise inspection found identical graph-array order and directed typed topology; the only differing field is the order of values in `Interlocutor.attrs.believed_concepts`, serialized as an unordered `__fset__`. The v1.1 semantic digest sorts only that set-valued list, retaining the raw digests. This is a post-capture amendment and does not retroactively pass the raw digest gate.

Analyzer: [v1.1 independent analyzer](../../../evaluation/substrate_capability/analyze_live_counterbalanced_value_recall_v1_1.py). Capture unchanged: [raw gzip JSONL](../../../evaluation/reports/live_counterbalanced_value_recall_v1_20261003.jsonl.gz).
