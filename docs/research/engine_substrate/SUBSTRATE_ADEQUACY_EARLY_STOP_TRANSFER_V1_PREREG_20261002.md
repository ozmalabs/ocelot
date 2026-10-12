# Early-stop and hypothesis-family transfer for adequacy probes v1 — preregistration

## Question

Does candidate-challenger maximum-entropy probe selection reduce false acceptance and label use when the audit stops at the first candidate mismatch? Does the result transfer from a sparse polynomial family to a two-variable arithmetic family?

## Frozen cases

Use 30 deterministic repetitions, budgets 1/2/4, and two policies: seeded hash order and greedy maximum Shannon entropy over native predictions for the candidate plus remaining alternatives. The labeler returns one hidden analytic target value after each selection; challengers inconsistent with that label are removed. Stop immediately on candidate mismatch. The hash arm uses the same candidate domains and tie seed. Record hash-order setup separately from marginal selection/update time.

The polynomial family uses `D(x)=∏(x−i), i=1..12`, with one witness at `x=13` and alias points at `x=1..12`. The vector arithmetic family uses `x+y` versus `x−y`: its broad domain has 31 `y=0` aliases and one `y=1` witness. Each family has a represented wrong candidate, a correct-candidate control, a wrong candidate whose target is omitted from the alternatives, and an alias-only domain. Acquisition is fixed at `x=0` or `(x,y)=(0,0)`, where all models agree. Integer outputs stay within the native signed range.

## Measures and interpretation

Report false acceptance on wrong candidates, correct acceptance and sealed held-out exactness, false refusal, labels to decision, witness selection, candidate/alternative evaluation cost, and source/native stability. Compare policies at equal maximum label budgets, while the stop-on-first-residual rule may use fewer labels. A useful result reduces broad-domain false acceptance in both families without rejecting the correct controls; alias-only false acceptance is expected for both policies because no test can distinguish the models there.

This is a controlled finite study with supplied alternatives and harness-authored analytic labels. It measures transfer between two authored Term families, not natural-task prevalence, authenticated oracle evidence, general adequacy, or autonomous candidate generation. Maximum entropy is an experimental selector, not yet a production change.
