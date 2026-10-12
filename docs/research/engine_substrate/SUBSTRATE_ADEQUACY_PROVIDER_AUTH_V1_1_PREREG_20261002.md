# Signed provider evidence at code-write adoption v1.1 — amendment

## Amendment to v1

V1 completed its registered 12-worker panel with all registered signature controls passing. A follow-up code review found an unregistered boundary case: an internally consistent request with zero probes and an empty receipt could satisfy the verifier vacuously. V1.1 hardens the verifier to reject empty probe sets and adds an explicit zero-probe negative control. The v1 lock/raw capture remains the original pre-hardening record and is not overwritten.

## Follow-up design

Repeat the four v1 full-seed cases (honest residual, unsigned forgery, trusted-but-incorrect signature, and correct candidate) in three fresh workers each against the hardened current source. Each worker also checks four authentication failures: post-signature value tampering, cross-request replay, a signed but unregistered provider, and a correctly rehashed empty-probe request with empty evidence. The core receipt adjudicator is expected to accept the empty set vacuously; the authentication verifier must refuse it. The other v1 gates remain unchanged.

## Limits

This follow-up validates the empty-set fix within the same source-locked harness. HMAC remains shared-key authentication. The key registry is caller supplied in this prototype, trusted signers can still issue incorrect labels, key lifecycle is absent, and the legacy receipt-only teach path remains available.
