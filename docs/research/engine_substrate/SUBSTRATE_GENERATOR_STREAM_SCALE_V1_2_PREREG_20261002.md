# Generated hypothesis-pool stress scale v1.2 — preregistration

## Question

At the first expression-size increment beyond the completed size-7 batch/stream comparison, do the two generator modes preserve behavior under a strict external wall cap, or does one produce an incomplete/timeout outcome? What are the measured exploration, wall, CPU, and process peak-memory costs when a single training example leaves a broad hypothesis set?

## Design

Use the same fixed triangular-number task as v1.1: one labeled example `(n=1, output=1)`, operators `Plus`, `Times`, `Minus`, `Div`, constants `{0,1,2,-1}`, disabled output-constant expansion, and 12 unlabeled probe inputs `n=0..11`. Compare size cap 7 as the same-regime reference with size cap 9 as the stress treatment; size 8 is omitted because this grammar's binary terms have odd node counts and it adds no new cohort. Cross each size with batch and `stream_cohort` modes for three fresh-process replicates, using a 10-second internal synthesis limit and a 15-second parent process timeout. Retain every completed, internal-timeout, parent-timeout, or worker-error row; do not retry or replace any outcome. Pool cap remains 10,000 fitting hypotheses.

The four held-out values remain `13,17,23,31`. They are evaluated only after synthesis returns a pool and never enter its labeled examples, probe signature, candidate ranking, or stopping decision. Completed workers record exact pool digests and finite held-out coverage. Parent timeouts record elapsed wall time and the terminating subprocess status, but no synthesized pool or within-worker RSS is available for those rows. Do not infer that the parent timeout implies a particular internal stop reason.

## Gates and analysis

The 10 checks require: (1) source/native provenance matches the pre-capture lock; (2) all 12 scheduled mode/size/replicate outcomes are recorded once; (3) worker outcomes are explicitly one of complete, internal timeout, parent timeout, or worker error; (4) completed batch/stream pairs have identical pool digest, stop reason, explored count, and held-out coverage; (5) fixed single-example and probe counts are verified; (6) completed pools are training-consistent; (7) complete is true only for `max_size`; (8) all completed measurements and exact-term predictions are finite and respect configured caps; (9) all completed worker source checks are stable; and (10) incomplete outcomes and unavailable metrics remain explicit rather than imputed.

Report completion rate and paired resource results separately by size and mode. A parent timeout or internal cap is an ordinary incomplete-search result. The study tests one arithmetic family and one anchor, and it cannot establish general synthesis tractability. The v1.1 result showed exact batch/stream semantics through 8.7k explored terms; v1.2 extends this controlled comparison to size 9 with a stricter external resource boundary.

## Reproduction

Run `python3 evaluation/substrate_capability/substrate_generator_stream_scale_v1_2.py --lock`, then `--capture`, then `python3 evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1_3.py`.
