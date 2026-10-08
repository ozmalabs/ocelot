# Adequacy receipt adoption integration v1

## Question

Does the provenance-bound independent adequacy receipt gate control the real
`teach_write_shape_from_example` adoption boundary? Refused evidence must not
add a code-write `ShapeSignature` or advance `write_codebook_epoch`; a receipt
accepted for the exact candidate must add the shape and advance the epoch.

## Frozen procedure

- Use `def square(x): return x * x` and request text `square x`.
- Start each repetition from `WorldAdapter(seeds=())` followed by
  `load_all_seeds`; each repetition runs in a fresh process.
- Obtain the parsed Term using `code_reading.read_function`, derive its
  candidate ID with `independent_adequacy.candidate_id_for_write_shape`, and
  request one fresh probe outside the acquisition input set.
- Exercise rejected, ambiguous, incomplete, invalid-provenance, and
  missing-receipt refusals on the same still-unmodified worker graph. Then
  adopt once using the accepted receipt. Every call sets the strict
  `require_adequacy_receipt` option, including the missing-receipt case.
- Record receipt and function outcomes, existing/new `taught_square` nodes,
  codebook epoch, per-case CPU/wall time, full-seed boot time, PID, RSS high
  water mark, and source hashes.
- Pass requires all five supplied receipt statuses to match expectation,
  every refused case to preserve the code-write shape inventory and epoch,
  and the accepted case to add one shape and increment the epoch exactly once.

## Interpretation limits

This is an integration-mechanism panel, not a measure of label quality or
natural-task prevalence. The label values and source identifiers are supplied
by the harness; receipt hashes do not authenticate the label provider. Three
fresh processes on one host establish repeatability only for this authored
arithmetic example. Existing unguarded calls remain ungated unless callers
provide `adequacy_receipt`.
