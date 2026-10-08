# CAN strip width-profile results

**Status:** all 60 amended workers pass extraction and exactness checks across strip heights 1–5; a valid column-order elimination certificate preserves width h. Generic min-fill overestimates the 5-row strip width by one from length 32 onward.

## Confirmatory profile

The amended preregistered sweep uses binary grid strips with heights 1–5, lengths 16/32/64/128, and three fresh-process replicates per cell. For every worker, runtime extraction matched all generated factors, junction-tree MAP using both min-fill and column-major elimination matched an independent transfer-matrix DP, and the column order produced bags of size h+1. Min-fill returned the correct width for heights 1–4. At height 5 and lengths 32, 64, and 128, it returned width 6 even though the explicit column order certifies width 5; this is a one-unit overestimate, not an exact-inference failure.

At fixed height, MAP cost was approximately linear with strip length. At height 5, median min-fill MAP time rose from 69 ms at length 16 to 642 ms at length 128; height 4 rose from 33 ms to 270 ms over the same lengths. The column-order MAP was exact but not uniformly faster. Generic min-fill ordering itself scaled much faster with length: for height 5 it rose from about 4 ms to 302 ms. Thus ordering, not message passing alone, is a material cost in this implementation.

These are synthetic strips with known separators. They test exact inference conditional on a supplied narrow structure; they do not test discovery of that structure or natural-task prevalence.

## Preserved v1 harness failure

The initial v1 sweep stopped at height 5, length 32 because its gate incorrectly required min-fill's upper bound to equal the known strip width. It had completed 51 workers and had passed exact oracle checks through the first height-5 cell. The partial console measurements and assertion diagnosis are preserved in [v1 failure record](../../../evaluation/reports/can_strip_width_profile_v1_failure_20260925.json). Amendment 1.1 changes only the gate: the explicit column order certifies width h, while min-fill is recorded as an upper bound and its overestimate is reported.

Protocol: [original preregistration](CAN_STRIP_WIDTH_PROFILE_PREREG_20260925.md), [v1.1 amendment](CAN_STRIP_WIDTH_PROFILE_V1_1_AMENDMENT_20260925.md). Runner: [strip profile runner](../../../scripts/can_strip_width_profile.py). Lock: [v1.1 content lock](../../../evaluation/substrate_capability/can_strip_width_profile_v1_1_lock_20260925.json). Raw report: [60-worker profile](../../../evaluation/reports/can_strip_width_profile_v1_1_20260925.json).
