# Primitive-menu help policy v1.1 amendment

V1's capture is retained as a diagnostic, not a confirmatory result. Its
independent analyzer replayed every recorded query but treated the absence of
a query step as a budget stop. It therefore failed to validate 20 recorded
selector-abstention reasons and the corresponding help triggers. The runner
capture and source binding are retained unchanged; the v1.1 analyzer explicitly
replays abstention against the remaining pool, and the source lock and capture
are regenerated under new versioned artifact names.

The v1.1 design, task/panel schedule, budgets, candidate menus, stop policy,
and help action are otherwise unchanged. Analysis must independently verify
both successful query selection and no-query abstention, plus whether a help
call occurred only on a registered unresolved signal. Do not combine v1 and
v1.1 result summaries.
