# Rung 3 hinge-map grammar contrast v1 — preregistration

**Status:** locked confirmatory contrast. **Date:** 2026-09-29.

## Question

Does supplying a small operator inventory let the existing graph-authored Rung 3 route acquire and transfer a piecewise hinge map under balanced examples when the normal broad default inventory reaches its candidate cap? This measures grammar restriction as a search-control intervention. The supplied inventory is oracle information from the known task family; it does not test whether the substrate can select a suitable grammar.

## Pilot disclosure and amendment boundary

Before this preregistration, one exploratory balanced-hinge probe using eight examples found that the default arm gapped at 200,000 candidates, while setting the existing message `ps_enum_ops` seam to `Plus, Minus, Max, TupleOf` produced an accepted candidate after 61,384 tests. That probe did not independently execute the returned Program on heldout points. This preregistration fixes those two conditions and requires fresh repeated workers plus heldout readback; pilot data will not be pooled.

## Task and arms

The target is `(r + max(c-1, 0), c)`. Training has eight examples: `r ∈ {0,1}` at each `c ∈ {0,1,2,3}`. The disjoint holdout points are `(r,c) ∈ {(0,4),(2,4),(1,5),(4,5),(2,6),(5,6)}`. This tests new r values and c values beyond the training support. All outputs remain typed coordinate tuples in `ingest_spec`.

Two fresh-substrate arms use the same request, examples, normal `ensure_program_synthesis` → `ingest_spec` → `pump` route, 200,000 default candidate cap, verification path, and six heldout executions:

1. **Default grammar:** leave `ps_enum_ops` unset; the production Gamma consultation and native default path choose operators.
2. **Oracle grammar intervention:** before `pump`, set the existing message fact `ps_enum_ops` to exactly `['Plus', 'Minus', 'Max', 'TupleOf']`. This bypasses learned/operator-shape selection for that invocation and is reported only as a constrained-grammar upper bound.

Run five fresh processes per arm (10 workers total), pairing by repetition and counterbalancing arm order. No retries or budget increases. Record status, route facts, selected operator inventory, candidate tests, exact candidate Program/IR, all holdout results, pump wall/CPU time, peak RSS, and source/native stability.

## Gates and analysis

1. Source, native extension, seed manifests, protocol, runner, analyzer, and fixed tasks match the pre-run lock and remain unchanged across each worker.
2. Exactly five unique workers per arm complete with one header/footer, all reach Rung 3, and all end in a terminal accepted/gapped result.
3. Every accepted candidate has one graph-reflected Program and is executed on all six heldout rows using `ProgEval`; every output is independently compared with the target formula. Any accepted holdout error is a transfer failure, not removed from the denominator.
4. Report arm-wise acceptance, exact transfer, gaps, candidate counts, costs, false acceptance, and paired candidate-count differences. A selective-search advantage is supported only if the oracle arm transfers in at least 4/5 workers, default reaches its 200,000 cap in at least 4/5, and median default candidate work is at least three times the oracle arm's median. Report failure of any threshold plainly.

Even if all thresholds pass, the result establishes only that a manually supplied grammar reduces search work for this fixed task. It does not establish an autonomous grammar learner, general nonlinear dimension induction, a natural task distribution, or scaling.
