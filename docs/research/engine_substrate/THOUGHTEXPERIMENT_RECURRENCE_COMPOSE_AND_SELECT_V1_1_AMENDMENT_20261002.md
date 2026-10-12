# Recurrence compose-and-select v1.1 amendment

The v1 training-order capture completed and is retained. Its separate held-out scoring stage stopped before worker 0 was scored because the scorer regenerated candidates in canonical host order but compared them directly with the shuffled, locked training order. No held-out outcome was written. The v1 lock and training orders remain valid for the training-stage result only; they do not support a transfer claim.

V1.1 replays the recorded permutation during candidate regeneration and uses new lock/order/score paths. Candidate set, seed, scoring protocol, cue, and gates are unchanged. The amendment, corrected runner, and analyzer are source-locked before the v1.1 capture. V1 training outcomes are not merged into v1.1.
