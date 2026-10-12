# Live self-identity reply-release integration v3.1 amendment (2026-09-26)

The initial v3 runtime reached all three workers, but the analyzer raised `KeyError: 'comprehension'` when constructing a route signature for the intentionally injected faculty-failure row. That row has no comprehension capture by design. The runner had not written the captured workers before constructing checks, so no raw worker payload was preserved. The v3 source lock records the attempted runner fingerprint; this attempt is excluded from runtime claims.

Before the v3.1 repeat, the route signature is made failure-row-safe and the runner writes raw worker captures immediately after all fresh processes finish, before analysis gates are computed. Preregistered prompts, source closure, route/lifecycle/reply/receipt gates, and failure expectations remain unchanged. Any further analyzer failure will leave the worker payload available for independent review.
