# Adequacy-probe coverage and gated/ungated comparison v1

## Question

How does the finite admissible-input domain affect the strict receipt gate's
protection against an identity candidate offered for a square request, and
what is the gate's incremental effect when the gated and ungated arms receive
identical examples, probes, oracle labels, and search work?

## Frozen arms

All arms use candidate `identity(x)=x`, request `square transform`, and the
same one-row acquisition contract `x=0 -> 0`. The independent square oracle
labels every selected audit probe. Each arm is a fresh full-seed process.

| Probe domain | Audit budget | Gate |
|---|---:|---|
| Narrow: `{x=1}` | 1 fresh probe | Strict on / off |
| Distinguishing: `{x=1,2,3,4}` | 3 fresh probes | Strict on / off |

Each matched gated/ungated pair computes the same request, labels, and receipt;
the ungated arm pays that evidence-generation work but does not require the
receipt for `teach()`. After the intervention, query the square request on
held-out `x={2,3,4,5}` using the learned native Term and emitted Python.
Repeat each of four arms in three fresh processes.

## Pass and interpretation

- Narrow receipts should be `accepted`, demonstrating the alias if the candidate
  matches at `x=1`; both gated and ungated arms will be evaluated for actual
  adoption and held-out error.
- Distinguishing receipts should be `rejected`; strict gating should preserve
  the starter codebook and abstain, while the ungated control should adopt the
  same candidate and expose its held-out errors.
- Exact receipt, source, query, label, graph-growth, epoch, and held-out checks
  are recorded per arm. Report end-to-end CPU/wall time separately from full
  seed boot and precomputed-evidence costs.

This is a deliberately adversarial one-function coverage study. It estimates
neither natural probe-domain quality nor broad gate precision/recall. The
oracle is separate and source-hashed but harness-authored; the test does not
authenticate external labels. Results describe the exact finite-domain gate
contract: accepted means agreement on submitted fresh probes, not universal
semantic adequacy.
