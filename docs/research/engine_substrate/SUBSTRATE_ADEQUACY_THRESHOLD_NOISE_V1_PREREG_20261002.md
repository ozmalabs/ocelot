# Threshold-task signed-evidence and domain-shift panel v1 — preregistration

## Question

Does the strict selected-probe adoption route behave correctly on a previously unused three-input comparison task under domain shift, aliasing, conflicting signed labels, and a validly signed false label?

## Task and conditions

The independent oracle is `left + right > limit`. The positive candidate is the matching function; the negative candidate always returns false. Both candidates and the alternative Term are read from supplied source. Five conditions run in three fresh processes each:

1. `truthful_positive`: correct candidate, broad domain, truthful signature; adopt and pass out-of-range held-outs.
2. `truthful_wrong_broad`: false candidate, broad domain, truthful label; receipt must reject and no construction may be added.
3. `truthful_wrong_alias`: false candidate on a domain where every sum is below the limit; the receipt may accept but zero-entropy probe policy must refuse adoption.
4. `trusted_false_label`: false candidate, broad domain, trusted provider signs the opposite of the independent oracle; expected to expose the known authenticity/truth distinction by adopting and failing held-outs.
5. `conflicting_signed_labels`: false candidate, broad domain, two trusted providers sign opposite labels; receipt must be ambiguous and adoption must be refused.

The broad selection domain uses small integer values; held-outs include values outside those ranges. Thus positive transfer tests structural extrapolation, while false-label and alias controls expose the remaining limits. All cases exercise `WorldAdapter.converse` with authenticated evidence and discriminating-probe enforcement.

## Independent analysis gates

Require source/native/seed lock stability; 15 unique worker processes and a complete schedule; exact independent recomputation of selections, signatures, receipts, and held-out outputs; one expected outcome per condition; and zero undeclared construction changes on rejected/refused cases. The analyzer must preserve the `trusted_false_label` failure as a measured outcome, not relabel it as a successful gate.

## Limits

This is one authored scalar task and one host. Candidate programs, challenger, finite domains, oracle, and provider keys are harness supplied. The false-label case is adversarial and not a prevalence estimate. No provider quorum or truth certification is inferred.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_threshold_noise_v1.py
```

The initial pre-capture lock is retained as `substrate_adequacy_threshold_noise_v1_initial_diagnostic_lock_20261002.json`. The first worker failed before recording a panel row because the harness passed a string instead of a native `NodeID` to the baseline construction census. The corrected census uses the native ID object. The first complete capture and its incorrect strict analyzer gate are retained as v1.1 diagnostics; the confirmatory analyzer corrects the criterion to require held-out error for wrong candidates, not zero correct examples. See the [v1.1 amendment](SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_1_AMENDMENT_20261002.md) and [v1.2 amendment](SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_2_AMENDMENT_20261002.md).
