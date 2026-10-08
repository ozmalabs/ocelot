# Grounded concern-dispatch probe v1.2 amendment

V1.1 correctly captured all four workers and showed that both conditions took `concern_authored`. However, its alleged `non_concern_walk` control retained the original raw text containing “Compare” and “judge”. `act_on_instruction` intentionally routes when either the dispatch predicate is a concern-framing verb or the raw text contains one, so this control did not isolate dispatch-predicate behavior. Retain v1.1 as a positive-route replication with an invalid control; do not use it to claim routing specificity.

V1.2 keeps the grounded concern positive unchanged and replaces the control raw text with “Walk to the door.” while retaining the `walk` predicate. All other worker setup and gates remain the same. New preregistration, lock, raw, analysis, and result files prevent overwriting either prior version.
