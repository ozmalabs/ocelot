# Scheduler EvalCache codec probe v1.1 preregistration

## Question

Does scheduler checkpoint schema V6 serialize and restore representative nonempty neighbour, filter, argmax, and holds cache entries with exact full-checkpoint equality?

## Procedure

Build a tiny graph with two live node IDs and a rule that creates a valid term-arena index. Seed the four cache families through their checkpoint wire representation with typed values, symbol bindings, and optional Holds node arguments. Import the same graph and ordered rules into a fresh substrate, restore the checkpoint, and compare the complete exported checkpoint object. Lock source, engine artifact, runner, and this protocol before capture.

## Acceptance and limits

Require source-lock stability, expected schema/counts, exact payload equality for all four families, and exact whole-checkpoint equality. This is a codec round-trip probe. It deliberately does not claim that an evaluator naturally generated these keys, that cache hits preserve behavior, or that downstream rule work matches under cache use. Follow it with evaluator-generated nonempty cache fixtures and workload transfer.


V1.1 supplies Holds entries in the canonical checkpoint sort order. V1 showed that restore sorts map entries deterministically; an unordered input array is not expected to reproduce byte-for-byte.
