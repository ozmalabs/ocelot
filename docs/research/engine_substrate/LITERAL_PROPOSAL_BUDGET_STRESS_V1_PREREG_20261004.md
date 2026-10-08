# Literal proposal budget stress v1 preregistration

## Question

How does direct-literal Cartesian proposal cost grow when a candidate contains irrelevant literal comparisons, and can a fixed proposal budget avoid silently accepting an unresolved false candidate?

## Frozen stress case

Start from the locked four-variable identity panel. Replace the false candidate with `ax==ex OR (main_guard OR contradictory_noise)`. `main_guard` is a four-variable interval conjunction using two direct literal boundaries per variable. `contradictory_noise` adds two direct literals per variable in an impossible lower-bound/upper-bound pair. Thus four direct literal values are available per variable although only one interval conjunction is satisfiable. Keep training and prior examples unchanged; filter holdout against the candidate and add one main-guard witness. The oracle remains `ax==ex`.

## Paired proposal budgets

Use the existing edge and pairwise literal slate in both arms. **Exhaustive** adds every unseen four-variable Cartesian assignment. **Budgeted** adds only the first 64 unseen Cartesian assignments in sorted, deterministic order. If a budgeted slate is incomplete and its remaining class is not split, final policy must request help even if finite behavior agreement would otherwise accept. Both arms share the oracle, selector, and eight-label cap.

## Measures and gates

Lock the Term, all inputs, proposal order, source hashes, upstream artifacts, 64-row budget, and 8-label cap. Independently replay the 256-combination product, filtering/deduplication, first-64 truncation, queried labels, underlying finite-class decision, final abstention override, holdout score, native evaluation count, and elapsed time. Report generated rows, labels, false acceptance versus help, and work. This is a constructed stress case, not a natural prevalence or general scaling claim.
