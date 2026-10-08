# Response-priority cross-family v1: analysis amendment

Date: 2026-10-06

The source-linked harvest v2 analysis available before this run records six passing contracts out of ten: held-self-knowledge, self-report action, and unknown-word clarification pass in both baseline replicates; scene description and concern authoring fail in both. The preregistered phrase “every worker passes” was inconsistent with that known baseline. Evaluate faithful profile reproduction and paired no-regression instead; retain the two baseline failures as failures. The full capture reproduces this 6/10 profile on both arms with no paired priority regression.

The harvest runner's `task_ok` helper also contains a route-name type bug (`.get()` on strings for `self_report_action`). The attempted full run stopped at that helper before producing a capture and was discarded. The captured run used the harvest analyzer's existing `task_oracle`, retained the harvest runner's stricter scene faculty-build check, and separately checked source stability, boot, and turn count. The cross-family analyzer was then corrected to call that same oracle independently. The capture and lock remain the evidence source; this file records the post-capture analysis clarification.

The parity gate remains failed: scene-description graphs differ across arms in both replicates despite equal replies and equal node/edge counts. The divergence exists before continuation, so full continuation does not cause or repair it. All other four route families pass pairwise normalized graph parity. Diagnose the scene-route mutation difference before widening the scheduler claim.
