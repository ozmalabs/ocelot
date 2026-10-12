# Adequacy label-provider spoof at adoption v1 — preregistration

## Question

Does the current provenance-bound receipt path distinguish a genuine oracle response from a forged label carrying the same provider ID and oracle hash, and what reaches the real code-shape adoption boundary?

## Design

Use six fresh full-seed processes: three truthful-label controls and three forged-label treatments. Each process reads candidate `identity(x)=x` for a square request, uses acquisition row `x=0 -> 0`, and requests exactly the fresh distinguishing probe `x=2`. The provider source ID is `independent-codewrite-oracle-v1:<SHA256 of the locked square oracle>` in both arms. The honest label is 4; the forged response claims 2, matching the candidate, while copying the true oracle hash and constructing well-formed request/probe/label identifiers.

Both arms submit their rows to `adjudicate_audit_receipt`, then pass the resulting receipt to `teach_write_shape_from_example` with strict receipt-required adoption. Capture receipt status/integrity, `teach()` outcome, codebook epoch, generated candidate, and sealed square held-outs. The analyzer independently recomputes the oracle label from the locked oracle module.

## Gates and interpretation

- The truthful arm must be rejected with a prediction residual and leave the codebook unchanged.
- The forged arm's actual behavior is measured, not assumed. If the API accepts it, strict teach adoption and held-out failure establish that source IDs and oracle hashes do not authenticate providers.
- Both arms must use identical candidate, request, probe, acquisition evidence, and claimed provider identity; only expected label differs.

This is a controlled integrity attack by a caller able to submit labels. It measures the current API trust boundary, not compromise of a cryptographic provider or error rates of real label services. The experiment does not add authentication; follow-on design must specify a trusted key registry and key lifecycle before making a security claim.
