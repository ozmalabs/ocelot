# Bounded quadratic GenInfer v2.2 partial results

## Disposition

The v2.2 capture is **incomplete and fails admission**. The locked schedule
contains 320 workers. Nine completed; the tenth timed out after 300 seconds in
training closure. The runner stopped and preserved the partial raw report; no
remaining workers ran. This is a measured timeout for the registered
high-range cubic control, not a completed 320-worker evaluation.

The immutable v2.2 lock has SHA-256
`6ad02788ce08a53314c94ae7090c67d6fa51f4628b0e739af30deb867cf1fc8d`.
The partial raw report has SHA-256
`427f630ce006f34336e7cd7ac38eedb72606fa16c73e28eca4031601a03b17fd` and the
analyzer output has SHA-256
`7d1b3c89a4a767b54c555ba948eb338a15446405a25096e234a302007d61c653`.

## What completed workers show

- The linear positive control acquired `genlin_[1,1,0,2]` and reloaded it for
  exact held-out `DimInfer` reuse. Its training closure was about 75 ms and
  held-out closure about 1 ms.
- Both bounded quadratic families completed feature-on acquisition, graph
  serialization/reload, and exact held-out reuse in their completed workers.
  The cross-term worker took about 185 ms to train. The coupled quadratic
  audit-on worker took about 13.4 seconds and recorded 7,115,520 linear matrix
  candidate attempts and 124,522,999 term work units before the quadratic
  operator was selected. Held-out reuse after reload took about 1 ms.
- Feature-off coupled-quadratic and corrupted-training workers minted no
  `quadratic2` generator. They used the existing novelty fallback and took
  roughly 3.2–4.9 seconds in training closure on these captures.
- The completed audit-on workers reconciled quadratic attempts into refusals,
  validation rejects, and survivors. The per-worker applicable acquisition,
  false-mint, oracle, and counter checks passed. Full audit parity did not pass
  because most scheduled pairs never ran.

## Tractability finding

The first cubic control used `T(x,y)=(x,y+x^3)`. On its seven training rows,
the normalized goal extent gave the legacy 2×2 linear search bound `B=64`.
The search enumerates every matrix in `[-B,B]^4`, or `129^4 = 276,922,881`
matrices for each eligible base per `GenInfer` evaluation. A single worker
remained in training closure until its 300-second timeout. The source shows the
quadratic solver runs only after the linear matrix search finds no winner, so
this failure is in the existing operating path and prevents the new learner
from reaching its own abstention decision.

The coupled quadratic worker provides a smaller measured scaling point:
`B=16` gives `33^4 - 1` candidates per base; six base evaluations account for
the observed 7,115,520 candidate attempts. The measured 13.4 seconds is
consistent with the exhaustive search dominating acquisition. A direct
`B^4` latency extrapolation to the cubic bound would be highly uncertain, so
the only accepted high-bound statement is the measured lower bound of 300
seconds for one worker.

## Analyzer disposition and limits

The analyzer reports `passed=false`, `worker_count=9`, missing schedule rows,
an empty worker-failure check, incomplete audit parity, and false
`capture_complete`. It does confirm source/binary stability, correct binary
assignment for completed workers, exact held-out oracle rows for those
workers, no quadratic false mints among completed controls, correct positive
acquisition/reuse in completed cases, and counter conservation for completed
audit-on cases.

This partial run establishes neither the 320-worker protocol nor overall
tractability. It does identify a serious cost centre: worst-case candidate
enumeration in the already-held linear hypothesis family grows as `B^4`, and a
large output extent can make an out-of-family rejection take minutes before
bounded quadratic induction starts.

## Next gate

Before another quadratic acquisition capture, add a separately versioned
exact-linear prefilter for unambiguous, full-rank identity-aligned 2-D bases.
It must recover the unique integer matrix directly, validate it through the
existing candidate builder, and skip exhaustive enumeration only when
uniqueness proves that no other matrix can fit. Rank-deficient or ambiguous
cases retain the exhaustive path. Compare semantic outcomes to the historical
enumerator on small exhaustive fixtures, then re-run the linear, both
quadratic, corruption, identity, rank-deficiency, and cubic controls with
candidate-work and timeouts recorded. This is a proposed next gate, not a
verified fix.
