# Accepted string-program bounded exhaustive audit v1 preregistration

Date: 2026-10-03

## Question

Do accepted P4 programs implement their registered function over a complete finite input domain, rather than only the sampled benchmark rows?

## Frozen protocol

Score every accepted program artifact in the four frozen PBE arms using native ProgEval. For `casefold_count`, enumerate every string of lengths 0 through 5 over the five-symbol alphabet consisting of the task's two parameter characters, their uppercase forms, and `#` (deduplicated if needed). For `split_reverse_tokens`, enumerate every string of lengths 0 through 5 over `{a, A, separator, #}` (deduplicated if needed). There are 3,906 inputs per casefold-count task and 1,365 per split-reverse-token task with the current parameters. Compare every output to the independently implemented frozen oracle using the benchmark's `agree` relation and require normal halt/no trap. Report exact-on-domain programs, row accuracy, errors by length, and provenance hashes.

The bounded domains intentionally include empty strings and strings without separators. The result is exact for these alphabets and lengths only. No search or acceptance decision is changed.
