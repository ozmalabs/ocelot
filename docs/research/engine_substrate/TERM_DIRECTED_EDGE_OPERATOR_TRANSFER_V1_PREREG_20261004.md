# Term-directed edge-probe operator transfer v1 preregistration

## Question

Does variable-pair IEEE stress probing transfer beyond the squared-versus-absolute equality example, and can it expose false candidates involving a different primitive operator?

## Panels

Use two paired tasks. Panel A is the existing absolute-equality survivor set: native candidates for `abs(ax)==abs(ex)`, including the squared-equality false candidate. Panel B is a new division task: target `ax==ex`, with candidate `(ax/ex)==1`; all training and ordinary selection inputs have nonzero denominators, where these candidates agree. Terms, training rows, prior ordinary-scale pool, and seeded log-scale holdout are locked before the run.

## Task-blind policy

Extract variable pairs from candidate Terms only. Generate a fixed slate of assignments using zero/zero, subnormal, underflow, overflow, and adjacent-representable value pairs in both orders. Other variables are zero. Exclude training, prior query pool, and sealed holdout rows. Apply the native discriminating-input selector; query the task oracle for chosen probes and filter disagreeing Terms. Stop when the survivors form one output class under the registered binary classifier, the selector finds no split, or the label cap of eight is reached. Compare against strict syntactic-singleton abstention on the prior ordinary-scale pool.

## Measures and validity

Lock implementation/native sources, panel Terms, generator constants, seeds, and holdout rows. Independent analysis replays proposal generation, class partitions, selector queries, oracle labels, stop decisions, and holdout predictions. Report per panel: correct/false class acceptance, help, labels, native Term evaluations, proposal/selection time, and wide holdout disagreements. The holdout contains 4,096 deterministic log-scale/ULP examples per panel and is disjoint from the edge-probe slate.

## Limits

Two authored equality tasks do not establish operator-general transfer. Finite stress probes and holdouts do not prove equivalence for all IEEE-754 inputs. No Term is installed or persisted; this measures diagnosis and behavior-class selection, not autonomous concept invention.
