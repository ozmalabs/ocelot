# Independent post-selection adequacy gate v1 — preregistration

## Question

Can a bounded set of fresh labeled audit probes distinguish correct generated survivors from a generated-pool false singleton, while retaining correct models and preserving explicit refusal when the acquisition pool is empty?

## Frozen inputs and audit panels

Use only the frozen selected survivors from the source-locked generated-pool transfer, cubic transfer, grid/misspecification, and cubic-alias captures. Hash each raw input capture and its source lock before evaluation. Use separate integer audit descriptors not present in the associated known, candidate, query, or held-out rows:

- Triangular, square, and cubic survivors: inputs `101, 137, 211, 509`, labeled by independent integer formulas.
- Euler survivor: (a) a 5-vertex path of four maximal edges, (b) a 7-cycle of maximal edges, (c) two filled triangles sharing only one vertex, and (d) three filled triangles sharing only one vertex. Build each descriptor by independently enumerating its simplicial closure; label by the alternating sum over all faces. The resulting scalar descriptors are checked against every known, candidate, queried, and held-out descriptor in the source capture before locking.
- Cubic false-singleton survivor from the `x=−1` alias capture: audit `x=2,7,11,13`, with cubic labels.
- Absolute-value acquisition that ended with an empty version space: preserve the prior refusal and do not fabricate a candidate for audit.

Apply one mechanical gate: a nonempty candidate is accepted only if it matches every independent audit label supplied at the selected budget; any mismatch rejects it with the exact residual rows. An empty acquired version space stays refused. Evaluate budgets `k=0,1,2,4` using the listed order. Recompute every prediction with both the native Term evaluator and an independent Python interpreter; recompute every label from the frozen task definition. Report false acceptance, false refusal, empty-pool refusal, coverage, evaluations, and elapsed audit cost by task family and budget.

## Validity and limits

Require source/native hashes to match the four capture locks and remain unchanged through evaluation; exact input-capture hashes; independent target labels; native/Python prediction parity; and complete results for each available worker/task/budget cell. Do not treat three repeated workers on the same authored task as independent task families. `k=0` is the baseline with no adequacy information and accepts any singleton vacuously. Report exact counts and family-stratified outcomes; this small panel is a mechanism/control evaluation, not a calibrated natural-task false-accept rate or a claim that four audit probes certify a model generally.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_contract_query_independent_adequacy_gate_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_query_independent_adequacy_gate_v1.py`
- The runner writes an input/source lock and raw audit capture in the capability and report directories.
