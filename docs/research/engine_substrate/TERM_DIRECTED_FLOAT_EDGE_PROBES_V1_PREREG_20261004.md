# Term-directed floating-point edge probes v1 preregistration

## Question

Can task-blind probes derived from survivor-Term variable structure separate a false candidate that agrees with the registered selection pool because ordinary-scale inputs hide floating-point underflow/overflow?

## Frozen panel and policy

Use the unresolved `absolute`, worker 4 candidate pool from residual-resynthesis v1.2, separately for its no-residual and one-residual arms. The same three survivor Terms must be present in both. First reproduce that all three agree under the prior finite selection pool. Generate a task-agnostic slate by extracting variable names from the Terms, pairing variables, and assigning values from a fixed IEEE stress set: underflow-scale, overflow-scale, adjacent representable values near one, and subnormals; set other variables to zero. Exclude training, prior selection, and sealed holdout inputs. Do not use task identity or oracle labels to construct probes.

Run the native discriminating-input selector over this slate. Query the task oracle only for the chosen query, eliminate candidates that disagree, and stop when the remaining candidates form one equivalence class under the substrate's binary output classifier over the full stress slate, no separating probe remains, or the pool is exhausted. Compare with strict syntactic singleton acceptance, which requests help on the prior pool. Report native Term evaluations, proposal/selector time, oracle labels, class members, and decisions.

## Scoring and validity

Lock current source, upstream captures/analysis, exact survivor terms, generator constants, and random seeds. Independently replay probe generation, proposal predictions, oracle labels, class partition, and policy stopping. After decisions, score each accepted class member against the registered 1,296-point holdout and a separate log-scale/ULP stress holdout with deterministic inputs; keep holdout values out of proposal generation. A passing result requires provenance, pairing, disjointness, selector transcript, class partition, and independent scoring gates.

## Limits

This is one ambiguous panel from four authored numeric task families. Equivalence is only established on the finite probe/holdout sets and under the explicit binary classifier. It does not prove equality over all IEEE values or real numbers, and no candidate is installed or persisted.
