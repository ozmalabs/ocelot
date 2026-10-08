# Term-directed edge-probe operator transfer v2 preregistration

## Question

Does variable-pair IEEE probing transfer across arithmetic Terms when holdouts distinguish bit-level edge inputs, and how often can a finite behavior class still contain a structured false candidate?

## Panels

1. **Abs/Times underflow transfer:** replay the three inherited `absolute` worker-4 survivors (`ax*ax==ex*ex`, `abs(ax)==abs(ex)`, and the wrapped equality form).
2. **Div/Eq signed-zero transfer:** target `ax==ex`; compare it with `(ax/ex)==1`. Training and ordinary prior probes use nonzero denominators and include equal/unequal values.
3. **Structured alias control:** use the same identity target with a false candidate `(ax==ex) OR ((ax==0.125) AND (ex==0.25))`. The probe generator does not inspect literals, so this control tests finite-class overacceptance; a sealed holdout includes the exact exceptional pair.

## Policy

Extract variable pairs from candidate Terms only. Generate the fixed IEEE edge slate (positive/negative zero, subnormal, underflow, overflow, and adjacent floats) in both orders, with other variables zero. Use bitwise float identity for disjointness, so `(+0,+0)` and `(-0,-0)` are distinct inputs. Exclude all training, prior-pool, and sealed-holdout rows. Run native disagreement selection, query the task oracle, and filter candidates. When no further split exists, accept a behavior class only if all survivors agree under the registered binary output classifier on the complete probe slate; otherwise request help. Strict syntactic-singleton acceptance is the abstention control.

## Holdout and measures

Use a 4,096-row seeded log-scale/ULP holdout per panel, with signed-zero cases for Div and the literal alias pair for the structured control. Lock exact terms, panel data, probe constants, seed, source/native hashes, and holdout rows. Independently replay generation, float-bit disjointness, candidate and oracle predictions, selector transcripts, class decisions, and holdout scores. Report correct and false class acceptance, abstention, labels, native Term evaluations, and policy time. The holdout is scored only after the policy decision.

## Limits

Three small, authored numeric panels do not establish broad operator transfer. Finite behavior classes are not universal semantic equivalence proofs. This study performs no installation or persistent learning.
