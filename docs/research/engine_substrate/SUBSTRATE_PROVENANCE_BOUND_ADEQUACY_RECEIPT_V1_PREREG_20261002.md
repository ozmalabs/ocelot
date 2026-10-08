# Provenance-bound independent adequacy request/receipt v1 — preregistration

## Question

Can the substrate represent a fresh probe request bound to a specific candidate and acquisition trace, then return a deterministic residual receipt that distinguishes agreement, contradiction, label ambiguity, incomplete evidence, and invalid provenance?

## API under evaluation

`domains.independent_adequacy.propose_audit_request` selects a seeded, deterministic subset from a caller-supplied admissible input domain, excluding all acquisition descriptors. Its request binds candidate ID, canonical Term digest, acquisition digest/source IDs, admissible-domain digest, seed, selected descriptors, and input digests. The caller obtains labels from a distinct evidence source; the module never produces labels. `adjudicate_audit_receipt` verifies candidate/request identity, exact requested descriptors, source and label provenance, evidence completeness, and prediction residuals. It returns accepted, rejected, ambiguous, incomplete, or invalid without installing/adopting the candidate.

## Frozen controls

Use prior source-locked generated captures as candidate/acquisition provenance: three workers each from triangular, square, Euler, correct cubic, and cubic grid tasks; the cubic false singleton; and the empty absolute-value version space. Four fresh audit descriptors per representable task are frozen in the preceding adequacy-gate protocol. For each nonempty survivor, request budgets 1/2/4 from the same deterministic fresh-domain ordering and provide independent formula/closure labels. Preserve empty acquisition as `refused_empty` with no candidate request.

Run six protocol controls on the cubic candidate/request: two independent sources disagree on a label (`ambiguous`); one requested probe is omitted (`incomplete`); an audit source ID is reused from acquisition (`invalid`); the requested descriptor is altered (`invalid`); the request body is changed without recomputing its ID (must fail closed); and a single incorrect label from a separately named source (`rejected` with a residual). Positive correct candidates must be accepted, and the false singleton must be rejected by the first requested audit label.

## Gates and limits

Require source/native and parent-capture locks, exact input freshness, stable request IDs, candidate-Term binding, expected statuses for all controls, complete receipts, independently recomputed residuals, and unchanged primary/acquisition data. Report call counts and wall time separately from probe-label work. This tests a provenance and decision-record mechanism; source IDs are caller assertions, not cryptographic identities. Probe-domain quality, oracle truth, natural false-accept rates, integration into acquisition/adoption, and broad learning efficacy remain unmeasured.

## Artifacts

- API: `domains/independent_adequacy.py`
- Runner: `evaluation/substrate_capability/substrate_provenance_bound_adequacy_receipt_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_provenance_bound_adequacy_receipt_v1.py`
- The runner writes a source/input lock and raw capture in the capability and report directories.
