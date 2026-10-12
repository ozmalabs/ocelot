# Contract query selection v1 — preregistration

## Question

Can a bounded substrate-side selector choose an input that separates multiple held Term hypotheses, using earlier labeled examples to remove inconsistent candidates?

## Mechanism under evaluation

`domains.contract_query.select_discriminating_input` filters hypotheses against observed `{inputs, expected}` rows, evaluates each surviving Term over a finite candidate-input set through the native Term evaluator, and chooses the input with maximum output-partition entropy. Ties follow candidate-input order. The selector receives no intended-target identifier and returns no expected answer; an external task oracle supplies the label after selection. This is an active query mechanism over a caller-supplied finite hypothesis set, not autonomous hypothesis generation or a general semantic oracle.

## Families and controls

Six fresh native-runtime workers cover two repetitions each for three unary integer hypothesis families:

1. identity / square / absolute value, prior labels at 0 and 1; hidden target square.
2. identity / square / negation, prior label at 0; hidden target negation.
3. square / cube / absolute value, prior labels at 0 and 1; hidden target cube.

Candidate inputs are integers -5 through 5 in ascending order. After each selected query, the external oracle returns the hidden target's output and the selector is called again until one hypothesis remains. Compare against 2,000 seeded random input orders per worker. The analyzer independently reimplements each small target formula and the random baseline.

## Gates and scope

For each family, the first selected query must attain the maximum entropy available on the candidate grid; the surviving set must contain the hidden target after every label; and the loop must identify the target without supplying its ID to the selector. Record rounds, selected inputs, partitions, random-control query counts, native runtime, and source fingerprints. This measures a small finite-set query heuristic only. It does not show the substrate generated the hypotheses, selected the task, or produced trustworthy labels without an external evaluator. No asymptotic or natural-task prevalence claim follows.
