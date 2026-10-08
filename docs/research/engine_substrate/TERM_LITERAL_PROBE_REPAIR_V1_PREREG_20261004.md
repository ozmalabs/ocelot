# Term-literal probe repair v1 preregistration

## Question

Does extracting variable/literal comparison boundaries from candidate Terms repair the structured false-class acceptance found by edge-only probing?

## Paired policy comparison

Use the three v2 panels, replacing the point alias with a narrow interval guard: `(ax==ex) OR (0.125<=ax<0.126 AND 0.25<=ex<0.251)`. The heldout contains interior points `(0.1255,0.2505)` and its reverse, while the probe generator may only use literals extracted from Terms. Compare:

- **Edge-only:** the v2 variable-pair IEEE stress slate.
- **Edge-plus-literal:** the same slate plus Cartesian assignments of direct `Var`/`Lit` comparison boundaries for each variable pair, both orders.

Both policies use the same native disagreement selector, oracle, candidate Terms, prior pool, holdout, and eight-label cap. Holdout data are used only for disjointness and post-decision scoring, never as proposal labels. Strict syntactic singleton acceptance remains a help/abstention reference.

## Measures and validity

Lock all inputs, policies, sources, and seeds. Independently replay literal extraction, both proposal slates, bitwise float disjointness, selector events, output-class decisions, and 4,096-case holdout scores. Report per-panel false and exact class acceptance, help, labels, native evaluations, and time. The repair passes the targeted control only if edge-plus-literal rejects the interval alias and accepts the exact identity while the edge-only arm reproduces its false-class behavior.

## Limits

This tests one narrow, harness-authored literal guard and three numeric panels. It cannot show that all Term literals or boundaries are extracted, and finite classes still do not prove unrestricted equivalence. No proposal is installed.
