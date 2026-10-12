# Term-literal adversarial family v1 preregistration

## Question and design

Does adding pairwise variable/literal boundary assignments prevent false behavior-class acceptance when a structured exception guard spans more variables or uses different comparison forms?

Use six frozen false candidates: interval and point-equality guards at arities 2, 3, and 4 over `ax, ay, ex, ey`. Each candidate is `ax==ex OR guard`; the oracle remains `ax==ex`. Guards use separated positive literal values, so they fit neither the frozen training rows nor prior rows. Lock one false witness per guard. The holdout excludes all proposal rows; for point guards, the direct boundary proposal can equal the unique witness, so report whether the policy queried it and use the witness to measure an unfalsified false candidate rather than reusing the query as held-out evidence. Compare the existing edge-only and edge-plus-literal proposals with the same selector and eight-label cap. Do not tune the policy after examining outcomes.

## Measures and gates

Lock all generated Terms, witnesses, training/prior/holdout rows, policies, source hashes, and upstream evidence before capture. Independently replay guard construction, candidate fit, proposal generation, bitwise disjointness, selector transcript, decisions, and holdout scoring. Report false-class acceptance, witness queried/unfalsified status, rejection/help, labels, native Term evaluations, and time by guard kind and arity. This is a stress-family measurement, not a prevalence estimate; six hand-specified structures cannot represent natural Term distributions.

## Expected interpretation

Pairwise literal proposals can expose two-variable guards. Guards requiring three or four simultaneous coordinates may remain invisible because the proposal slate varies only pairs at a time. A surviving false class is a measured failure of proposal coverage, not evidence that the engine cannot represent or evaluate the guard. No acceptance is a proof of equivalence.
