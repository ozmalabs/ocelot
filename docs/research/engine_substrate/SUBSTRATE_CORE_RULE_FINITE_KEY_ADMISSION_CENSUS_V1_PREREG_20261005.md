# Core-profile finite-key rule admission census v1 preregistration

**Question.** How much of the default `boot_core()` active rule set fits the existing checked finite-key insertion-only fragment that has a finite-state closure bound?

**Method.** Under a source/native lock, boot the default `CORE_SEEDS` and dependency closure without running rules. Export the active native rule store and complete initial graph. Apply `scripts/analyze_mint_termination_fragment.py` to each active rule and to the full active set, supplying the exact exported match/effect forms and complete graph node/edge inventory. Record per-rule names, effect classes, extra semantic fields, checker decisions/reasons, and aggregate bounds when accepted.

**Analysis.** An independent analyzer will verify source-lock integrity, reconstruct the checker inputs, implement a second conservative acceptance predicate for the fragment, and reconcile its per-rule and aggregate outcomes with the captured checker. Report accepted/rejected denominators and common exclusion reasons. Do not infer nontermination from rejection: the checker is a narrow sufficient fragment, not a general termination analyzer.

**Limits.** This is a census of one default core boot profile before execution. It does not cover every registered seed, runtime-authored rule, checkpoint, patch, or self-mint route; it does not change admission behavior; and it does not prove the runtime termination of accepted or rejected rules. A zero-acceptance result would show that the current core profile cannot inherit the finite-key fragment's guarantee as a whole.
