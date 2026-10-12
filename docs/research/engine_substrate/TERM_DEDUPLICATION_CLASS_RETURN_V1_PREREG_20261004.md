# Term deduplication and class-return ablation v1 preregistration

## Question

How much of the coverage-aware policy's apparent hypothesis ambiguity and
label cost comes from identical Term JSON emitted under multiple grammar
families, and does deduplicating exact Terms preserve held-out correctness?

## Design

Use all 25 panels and candidate pools in the source-locked coverage-aware
class-return study. Keep the first occurrence of each canonical Term JSON,
then rerun the same coverage-aware policy on that deduplicated pool. The
upstream source-locked capture is the no-dedup comparison. Do not alter
candidate generation, query pools, coverage threshold, label budget, oracle,
or finite holdout. Capture candidate counts before/after deduplication,
policy decisions, labels, expansions, returned members, and per-member
holdout scores.

## Analysis and limits

Independently reconstruct survivor transitions and score returned Terms on
the upstream declared finite holdout. Report exact duplicate counts, policy
decision changes, labels/help, and false or exact outputs. Exact JSON
deduplication addresses repeated representations only; it does not merge
semantically equivalent but structurally different Terms. This is a candidate
pool ablation on five authored numeric relations, not general induction,
natural task transfer, or autonomous search improvement.
