# Trusted signer live-route adequacy test v1 — preregistration

Date: 2026-10-02

## Question

Can a configured provider that signs a false label matching a wrong candidate's output cause false shape adoption through the strict live `WorldAdapter.converse` route?

## Design

Two source-bound candidates are tested in three fresh workers each:

- `honest_square`: `square(x)`; trusted provider signs `square(2)=4`.
- `trusted_wrong_identity`: `identity(x)`; the same trusted provider signs `identity(2)=2` while identifying the signed oracle as the square oracle, whose independent fixture answer is 4.

Both have the same single known example `f(0)=0` and one requested probe `x=2`, so both candidates are consistent with the known example and each receives a label consistent with its own output at the requested probe. The evidence request and receipt bind to each exact candidate and Term. The expected core receipt is accepted and the HMAC authenticates in both arms. The adapter is strict and receives the evidence through `converse`.

After adoption, evaluate each candidate Term on held-out `x=3,4,5` and compare to the fixed independent square oracle. Expected result: square passes 3/3 held-outs; identity is adopted despite provider authentication but fails all 3/3 held-outs. This isolates provider identity authenticity from provider answer truthfulness and adequacy.

## Interpretation limits

This is one authored scalar family, one trusted test key, and one host. The panel does not estimate natural false-label frequency, calibrate a provider, or establish general learning ability. The wrong label is deliberately adversarial. It does establish whether the live adapter distinguishes a valid MAC from an adequate answer.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_trusted_signer_live_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_trusted_signer_live_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_trusted_signer_live_v1.py
```
