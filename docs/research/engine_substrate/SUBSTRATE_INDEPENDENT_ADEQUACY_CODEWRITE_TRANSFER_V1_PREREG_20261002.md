# Independent adequacy gate on code-write acquisition v1

## Question

Does the strict independent-adequacy receipt gate carry through actual
example-supervised code-shape acquisition on two existing task families, and
does a fresh probe reject an observationally compatible but semantically wrong
identity candidate for a square request?

## Frozen task set

1. `parity(value) = (value % 2 == 0)` with acquisition inputs 0 and 1;
   held-out inputs are every integer from -20 through 20.
2. `clamp_value(value, lower, upper)` with three acquisition examples;
   held-out inputs include below/at/inside/at/above intervals over positive,
   negative, and mixed bounds.
3. Negative control `identity(x) = x` supplied for a square request, with the
   acquisition example `x=1 -> 1`. Fresh square probes exclude `x=1`, so the
   candidate is contradicted away from the known example.

## Procedure and gates

- Run three fresh full-seed `WorldAdapter` workers, each on one shared graph.
- Confirm parity and clamp requests initially have no matching write shape.
- For every candidate, parse its Term, bind the receipt to source/name/args/
  Term/request, select deterministic fresh probes, and generate labels from
  the separate `independent_codewrite_oracles.py` module. Store the oracle
  source digest and output for every probe in the capture.
- Supply acquisition examples as contract rows, then call
  `teach_write_shape_from_example(..., require_adequacy_receipt=True)`.
- Pass requires parity and clamp receipts to be accepted, one matching shape
  and one epoch increment per accepted candidate, exact native-Term and
  emitted-Python agreement with the independent oracle on all held-outs, and
  zero `taught_identity` growth/epoch change after the square receipt is
  rejected.
- Lock runner, analyzer, oracle module, protocol, implementation sources,
  native extension, and loaded seed manifests before capture; verify hashes
  again after all workers.

## Interpretation limits

This tests an integration boundary, not autonomous example selection or
independent external-label governance. The oracle module is source-hashed and
separate from the candidate functions, but its code and expected functions are
authored for this panel. Three workers and two positive task families do not
estimate natural-task prevalence, broad induction, or general acquisition
quality.
