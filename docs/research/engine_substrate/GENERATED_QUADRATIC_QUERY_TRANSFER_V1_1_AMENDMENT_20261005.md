# Generated quadratic query-transfer v1.1 amendment

V1's source-locked 120-cell capture is preserved. Its first analyzer run failed because the independent replay compared stringified mapping order rather than mapping content and reconstructed the seeded random permutation with sampling instead of the runner's shuffle procedure. The capture itself is structurally complete, but v1 outcomes are not admitted until an analyzer with corrected independent replay passes.

V1.1 makes no task, grammar, candidate, policy, or budget changes. It fixes only the replay checker, creates a fresh lock including the corrected analyzer, and repeats the 120 cells. The analysis now also reports mean oracle calls alongside medians so permutation-level differences are visible. V1 artifacts remain preserved and are not pooled.
