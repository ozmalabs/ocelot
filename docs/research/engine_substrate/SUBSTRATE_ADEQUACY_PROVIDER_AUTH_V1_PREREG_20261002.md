# Signed provider evidence at code-write adoption v1 — preregistration

## Question

Can a verifier-owned provider key registry reject forged, tampered, replayed, and unknown-provider labels before the current receipt gate reaches `teach()`? What remains possible when a trusted key signs an incorrect label?

## Mechanism under evaluation

Use a standard-library HMAC-SHA256 envelope bound to provider ID, request ID, probe ID, input hash, label ID, expected value, and claimed oracle-module hash. The trusted registry maps provider IDs to shared keys supplied by the verifier-side harness, separately from evidence. Verify all rows and the receipt's evidence hash before invoking the existing candidate-bound receipt and adoption checks. This is a prototype trust boundary; HMAC is symmetric and does not establish correctness or protect a key exposed to an untrusted caller.

## Full-seed cases

Run three fresh processes per case:

| Case | Candidate | Label | Signature | Expected result |
|---|---|---|---|---|
| Honest wrong candidate | identity | square says 4 | trusted provider | authenticated, receipt residual, refuse |
| Forged spoof | identity | forged 2 | absent | authentication refusal, no codebook growth |
| Trusted but incorrect | identity | forged 2 | trusted provider | authenticated, receipt accepts, false adoption exposed |
| Correct control | square | square says 4 | trusted provider | authenticated, receipt accepts, correct held-out adoption |

Every worker also checks that post-signature value tampering, replay under a different request ID, and a valid MAC from an unregistered provider are refused by the authentication verifier. Use `x=2`, acquisition `x=0 -> 0`, strict authenticated teaching, and held-outs `x=3..6`.

## Gates and limits

All source/native/seed hashes and request/candidate bindings must hold. Unsigned/tampered/replayed/unknown-provider responses must not change codebook state. Correctly signed honest evidence must preserve expected residual/adoption behavior. A trusted but incorrect signature is expected to pass authenticity and may still cause false adoption; that separates source authentication from oracle correctness.

The fixture key is test-only. This experiment is not a production key-management design: deployment still needs protected registry ownership, rotation/revocation, provider onboarding, replay policy, and key isolation. It does not establish provider accuracy or general task performance.
