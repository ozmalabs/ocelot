# P18 observed-model and experiment evaluation preregistration

Frozen before access to the P18 held-out allocation. Protocol: `linear-p18-v1`.

## Claim and limits

The evaluation tests bounded observation-built categorical models in independent object-mechanism and partially observed temporal worlds. The simulator owns its hidden equations and verifies every action or continuation receipt. The learner receives public observations, legal actions, and observed outcomes only. This does not test physical causality, robotics, unrestricted model induction, general science, or calibrated probabilities.

## Allocation and arms

- 200 worlds per family, paired across `learned_model`, `held_vocabulary_search`, `passive`, and `fixed_probe`: 1,600 primary rows total.
- Arms receive the same world distribution, four training interactions, visible observation and legal action access, and a ceiling of five interactions. The learned arm uses native source-bound process induction, disagreement-derived probe proposals and graph-authored experiment selection. The held-vocabulary comparator searches the same finite visible feature/action vocabulary; passive does not form model candidates; fixed-probe executes a predetermined probe.
- Object-mechanism worlds train on four objects and hold out a fifth object combination. Temporal worlds expose three regular samples and a fresh continuation. World equations and the mechanism key are never included in learner input.
- Structural controls: 100 ambiguous object-model cases, 100 missing temporal-window cases, and 100 irregular temporal-window cases. Held-out offset is +2,000,000 from the registered bases. A minimum of 100 actual simulator-result-linked refinements is required.
- Each task is bounded to 60 native ticks and 100,000 rule steps per tick, with a fixed 1,000-unit thinking exposure budget. No Python decision dispatch is used in the learned-model arm.

## Outcomes and decision rules

Efficacy passes if learned-model gains at least 20 percentage points over the strongest supported comparator in either registered family, or uses at least 25% fewer interventions with solve loss no greater than two points. If neither condition holds, efficacy is `NOT_ESTABLISHED`, even if the learned model path is structurally valid. All controls, paired allocations, native-source audits and world receipts must pass; all rows are retained. At least 100 learned model refinements must link to actual world results. Missing predictions and failed probes count as unsuccessful. No threshold or outcome may be changed after the held-out draw.

## Artifact freeze

The runner and analyzer are committed as `evaluation/process_mastery/linear_p18_v1.py` and `evaluation/process_mastery/analyze_linear_p18_v1.py`. Their exact source and loaded-native provenance is frozen below. Development used 8 worlds per family/arm (64 rows), 10 controls per kind, passed integrity/conformance and five tamper probes, and did not meet the efficacy threshold because held-vocabulary search tied the learned-model arm.

```json
{
  "artifacts": {
    "analyzer_sha256": "49a1c5f43ade44b50d7d7457be48186a947b821e224916a815cea0e20f46a8a5",
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1",
    "dependency_closure_sha256": "8e8512fe04516181b8d5ca0b96a530bac77b84f0f11192f8a27ecfc7dcd7cc78",
    "engine_source_sha256": "2ded41f8d4c036b3b89501db9dfbd117aead6273c80b843b9938b6969a1fa4b8",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "profile_sha256": "68264ae90b8fbf98cc433e211d9a2a00e18327d3bab261a3ffe741b6e1c5e735",
    "runner_sha256": "6872f1e5b125eec7c29f844f7ed2c7321da0abcb397f9b51d36bf2829c7f1d8d",
    "source_bundle_sha256": "27c063f1ee1ddc1d704df204697d1439bc09e829d30d2e06b7a05c73212b931d",
    "world_adapter_sha256": "aaf88f99e383ca89430776f8da7d489d47258d5633a3f0b63a180261b1674334",
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5"
  },
  "decision_rules": {
    "controls": "all ambiguous, missing and irregular controls must abstain or retain/dispute alternatives as specified; 100% pass required",
    "primary": "learned-model gain at least 20 percentage points over the strongest supported comparator, OR at least 25% fewer interventions with solve loss no greater than 2 percentage points",
    "structural": "no supplied transition hypotheses or answer fields; exact receipts, source/model/frame binding and complete pairing; at least 100 actual simulator-result-linked refinements",
    "unsupported": [
      "physical causality",
      "robotics",
      "unrestricted model induction",
      "general science",
      "calibrated probabilities"
    ]
  },
  "development": {
    "actual_result_linked_refinements": 16,
    "conformance": "PASS",
    "controls_per_kind": 10,
    "efficacy": "NOT_ESTABLISHED",
    "fixed_probe_success": "0/8 in each family",
    "held_vocabulary_search_success": "8/8 in each family",
    "integrity": "PASS",
    "learned_model_success": "8/8 in each family",
    "paired_worlds": 16,
    "passive_success": "0/8 in each family",
    "rows": 64,
    "tamper_probes": "5/5 detected",
    "worlds_per_family_per_arm": 8
  },
  "implementation_commit": "7bb77bebbe6ba401905286c65bc5148eb1889f55",
  "protocol": "linear-p18-v1",
  "registered_allocation": {
    "arms": [
      "learned_model",
      "held_vocabulary_search",
      "passive",
      "fixed_probe"
    ],
    "controls": {
      "ambiguous": 100,
      "irregular": 100,
      "missing": 100
    },
    "exposure_budget": 1000.0,
    "families": [
      "object_mechanism",
      "temporal_latent"
    ],
    "heldout_offset": 2000000,
    "interaction_ceiling": 5,
    "max_steps_per_tick": 100000,
    "max_ticks": 60,
    "minimum_actual_result_linked_refinements": 100,
    "worlds_per_family_per_arm": 200
  },
  "runtime": {
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1",
    "build_source_fingerprint": "73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5"
  }
}
```

Held-out raw bytes must be preserved before analysis. The frozen analyzer validates exact runtime identity, allocation, input audits, all world receipts and result-derived outcomes. A protocol defect invalidates the run and requires a new version and disjoint allocation.
