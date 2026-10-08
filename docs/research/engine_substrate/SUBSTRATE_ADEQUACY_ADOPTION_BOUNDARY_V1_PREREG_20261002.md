# Adequacy-gated adoption boundary v1 — preregistration

## Question

What graph state does the authenticated code-shape adoption transaction mutate after conversation/bootstrap and code parsing have completed, and does a rejected receipt reach that transaction?

## Design

Run three fresh workers. Each boots a minimal `WorldAdapter` with one trusted test provider, parses the same square function, and constructs candidate-bound audit evidence over a finite square domain. First submit a validly signed but false label that adjudicates to `rejected`; require no call to `code_write_growth._teach_shape` and no growth in the code-write shape inventory or epoch. Then submit truthful signed evidence for the same candidate. Instrument `_teach_shape` to capture canonical full graph state immediately before and after its call. This boundary includes the actual `teach()` plus its `write_codebook_epoch` update and excludes earlier AST/Term parsing and later conversation turn mutations.

## Gates

Require three unique fresh PIDs and stable source/native hashes. Recompute both receipts and provider authentication independently. The rejected case must be refused without entering `_teach_shape` or growing the codebook. The accepted case must add exactly one `ShapeSignature` of kind `code_write_construction`, exactly one associated pending `ShapeObservation`, modify only the existing Agent's `write_codebook_epoch` from 0 to 1, remove no nodes/edges, and add only edges incident to one of the two new nodes. Store complete before/after graph snapshots so the analyzer can replay the delta independently. Preserve timings for the instrumented transaction as descriptive measurements.

## Limits

One host, one authored square task, one provider key, and three workers. This isolates a code-shape adoption boundary; it does not establish that arbitrary graph deltas are safe, provider labels are truthful, or the complete live conversation is side-effect-free. Cold conversation initialization remains separately measured by the failed full-graph gate in the v1.2 live-route panel.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_adoption_boundary_v1.py
```
