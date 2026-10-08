# Term-conditioned audit v1 preregistration

## Question

Can candidate-Term predictions guide task-blind oracle queries that expose false singleton candidates missed by uniform continuous sampling?

## Policy

Freeze the 20 candidates from adaptive factored search. For each candidate, draw four-variable rows uniformly from the finite support `{-3,-2.75,...,3}` using a deterministic seed. Exclude training, selection, and sealed holdout rows. Evaluate the candidate Term and collect up to 32 predicted-true and 32 predicted-false rows, preserving their random proposal order. The policy does not receive task identity or use oracle labels during proposal generation. Report each prefix at oracle-label caps 4, 16, and 64, stopping at the first prediction/oracle mismatch; provisionally accept only if no mismatch is found by the cap. A help-only arm always abstains.

The sampler uses candidate predictions to find a balanced challenge set. Count every native Term evaluation used to build that set separately from oracle labels and report proposal sampling cost and wall time. This policy is task blind but candidate aware. The held task definition is used only by the oracle and independent scorer.

## Gates and measures

Lock code/native/upstream hashes, panels, finite support, random seeds, proposal budget, and caps before execution. The independent analyzer replays proposal generation, candidate classifications, query labels, stopping decisions, and sealed 1,296-point holdout scores; checks disjointness and class balance; and verifies native evaluation counts. Report correct/false acceptance, help, labels, Term evaluations, and wall/CPU time per policy cap and task family. Compare with integer, task-conditioned, and uniform-continuous audits on the same candidate identities. The run is valid only if the full paired panel and all provenance/transcript gates pass.

## Limits

Finite support can miss behaviors requiring other values, and candidate-conditioned sampling can fail when a useful class is rare or absent under the support. Passing this audit cannot certify equivalence. This remains a post-search audit; no residual-driven resynthesis or primitive invention occurs.
