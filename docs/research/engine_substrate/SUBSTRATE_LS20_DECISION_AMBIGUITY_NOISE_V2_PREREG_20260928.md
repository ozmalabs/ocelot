# LS20 decision ambiguity/noise multi-seed replication v2 preregistration

**Question.** How does pixel-noise intensity affect exact transform recognition and end-to-end task success, and does the response change when five distractor stations expose all six transform operators?

## Design and scope

Use 16x16 maps with 20% walls; compare one station against six stations, where exactly one performs the required transform. Cross station count {1,6}, Gaussian pixel-noise sigma {8,10,12,14}, and four independent PCG64 seed blocks. Each seed block contributes 20 scenarios per station/noise cell: 640 distinct worlds total, each run paired clean/noisy with the same world and fixed `quanta` router (1,280 episode executions). Seeds are `929000 + 100*s_index + 10*noise_index + block`, with s_index 0/1, noise_index 0..3 in listed order, and block 1..4. The clean comparator uses the existing production recognizer; the noisy arm adds independent Gaussian image noise to symbol and goal renders, clips to uint8, then uses the same grid-recovery and transform-recognition path.

Balance the six required transform operators within every 20-world seed block (three rotations, two reflections, and the symbol-specific recolour). With six stations, the five alternatives are present as distractors; with one station, station count is absent as a confound. Preserve symbol, transform, stations, map and both outcomes in the raw capture. Keep planning rules, route executor, world physics, and episode budget unchanged.

This tests a synthetic offline LS20-shaped task family. It is not live LS20 performance, a natural-noise distribution, arbitrary visual ambiguity, general planning, or evidence that frame locality holds in natural tasks. Sigma 8/10/12/14 are a targeted transition sweep following v1's 20/20 recognition at sigma 8 and conservative refusal at sigma 12.

## Outcomes and analysis

Primary outcomes are exact required-key recognition, refusal rate (`None`), wrong-key rate (a non-None incorrect key), and task success. Also report task failure reason, paired clean/noisy fixed and broken outcomes, route steps, per-arm wall/CPU time, process wall/CPU and peak RSS. Report station × sigma strata, pooled over four seed blocks only after showing every block. Give Wilson 95% intervals and exact two-sided McNemar tests per stratum; adjust the eight paired tests by Holm and identify unadjusted/adjusted values. Report transform-operator strata to expose differential confusion. No pooling across sigma or station count for efficacy conclusions.

Integrity gates: exactly 640 unique worlds and 1,280 complete paired episodes; all intended transforms and exactly-one-correct-station conditions independently reconstruct; BFS confirms every goal/station reachable; every `win` agrees with the delivered terminal; all six required operators appear 3 or 4 times in each seed block; every scenario digest recomputes; source/build/input lock is stable pre/post/live; native extension is fresh. Preserve partial checkpoints and stop on any lock drift. No outcome-guided exclusions or seed replacement.

## Reproducibility and output

Hash the protocol, runner, independent analyzer, benchmark and scenario source, loaded Python runtime closure, Rust sources/manifests, native facade/extension/build manifest, recursively loaded seed closure, and `arc3_env.py`. Use fresh v2 lock and output paths; the completed v1 screening data remain untouched. The analyzer independently reconstructs task truth, scenario digests, class balance, reachability, confidence intervals, and paired tests from raw data and verifies lock stability. If the source lock drifts, retain the capture as censored and do not resume against changed inputs.
