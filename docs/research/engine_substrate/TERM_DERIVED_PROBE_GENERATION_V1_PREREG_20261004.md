# Term-derived probe generation v1 preregistration

## Question

Can a syntax-directed policy recover a useful input boundary from a candidate
Term itself, with no threshold side-channel, and use the native selector to
reject a bounded near-equivalent candidate across varied encodings and task
relations?

## Frozen matrix and policy

Use five upstream frozen panels, two task relations (additive and product),
three thresholds (3.75, 5, 8), and four guard encodings (direct `ax < c`,
`not(ax >= c)`, reversed `c > ax`, and affine `ax + k < c + k` with a
registered nonzero offset). This yields 120 cells. Each candidate set contains
two commuted exact relation Terms and the relation conjoined with the encoded
guard. The bound is present only in the candidate AST; policy inputs are the
Term and task-variable names. A structural walker extracts an affine
`ax + offset` comparison, normalizes comparison direction and negation, and
generates examples at effective-bound minus 0.5, the bound, and plus 0.5.
The substrate's native Term evaluator and finite-set discriminating-input
selector choose a probe; the task oracle supplies one label.

## Measurements and gates

Lock source/native fingerprints and every panel/candidate before running.
Independently replay the extracted boundary from the serialized Term, require
the generated query to belong to the three generated probes, require its
oracle label to reject the bounded candidate and retain both exact Terms, and
score the resulting class on a fixed seeded wider set. Report extraction and
selection success by encoding and task, labels, candidate/probe evaluations,
selection latency, and wide errors. A failure in any cell is reported as a
failure, not dropped.

## Limits

This is a controlled Term-syntax transfer experiment. The extractor is
authored for a small affine comparison fragment; the candidate family,
variables, task oracle, and examples remain known. Passing would establish
robustness over these encodings only, not general term understanding, new
candidate invention, or autonomous self-improvement.
