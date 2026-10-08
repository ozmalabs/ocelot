# Held-out selector reason v1 preregistration

**Question.** Which openness-selector branch rejects the derivation-only `sift` scale-cancellation candidate in the full seed corpus?

## Method and gates

Read the source-stable v2 selector capture and take its first Direct order-1 derivation record. Full-boot the same seed corpus once. Reconstruct the selector input's distinctive keys from the captured `capability_keys`, compute the actual `_covered_keywords()` set from that full boot, and call `is_gap()` with the current repository search root. Record the exact verdict, covered-key intersections, `_codebase_has()` result, source fingerprints, and boot failures. Require `order_n_postulates.py` to match the v2 capture (the v2 panel included this file); fingerprint all files used by this diagnostic, including `speech_science.py`, before and after the current run. Require successful full-boot return and a determinate `is_gap()` reason.

## Limits

This is a one-worker diagnostic of the selector reason for the captured candidate. It does not evaluate whether the codebase implementation is adequate or whether the candidate should be considered useful in a different domain.
