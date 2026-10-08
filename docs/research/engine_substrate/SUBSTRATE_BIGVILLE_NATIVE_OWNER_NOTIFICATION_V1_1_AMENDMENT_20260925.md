# Bigville native owner-notification amendment v1.1

**Applied before the locked multi-replicate run.** The v1 worker reused the existing dynamic-link harness's `omit_evidence_notification` policy. Source inspection showed that this policy suppresses the initial caller seeds at both cross-link insertion and the authored-evidence update. It therefore is a broader omitted-notification arm than v1 stated.

Keep the full and native-event arms unchanged. Interpret the omission arm as a sensitivity control that skips both the injected-link and evidence-update notifications; require positive independent full-graph residual at the evidence checkpoint, and report the link-insertion residual separately. This remains a valid falsifier of missing notifications, but it cannot attribute the stale state to the evidence seed alone.

No thresholds, graph generation, task inputs, native implementation, or primary full/event correctness gates change. The result and lock must cite this amendment and preserve the worker policy name as a harness identifier only.
