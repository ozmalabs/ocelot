# P17 matched later-behavior evaluation preregistration (v2)

Frozen before access to the v2 held-out allocation. Version 1 was invalidated before efficacy analysis: its preregistered native build source fingerprint contained a transcription error. The v1 raw scorecard is preserved at SHA-256 `372742d0525e3401146ff5df937ab28f5ad3adce50d873b0345d80855268d103`; the frozen analyzer rejected it and produced no report. It is excluded from all efficacy claims. Version 2 changes the phase identifier and uses a disjoint held-out seed offset.

## Claim and limits

This evaluation tests whether source-bound acquired distinctions change later predictions and action proposals in two finite simulator families: `tool_contact` and `social_request_repair`. It does not test real-world qualia, consciousness, human-relative significance, open-world action, or general strategy quality.

## Allocation and arms

- 200 independently seeded later-task worlds per family, paired across four arms: `acquired`, `frozen`, `shuffled`, and `no_experience` (1,600 scored rows total).
- Five observed training episodes per trained arm/world. The frozen arm receives the same episodes and compute ceiling with acquisition disabled. Shuffled receives the same observations with feature labels permuted. No-experience receives no training episodes. Every arm receives the same fresh task, legal actions, and exposure budget (1,000 units).
- Primary worlds use seeds `31,000,000 + 2,000,000 + family_index*10,000 + draw`, family order `tool_contact`, `social_request_repair`, and draw `0..199`.
- For each family, 100 orthogonal controls and 100 reversal controls use seed `31,020,000 + 2,000,000 + family_index*10,000 + control_kind_index*1,000 + draw`, kind order `orthogonal`, `reversal`, draw `0..99`. These controls are additional to the paired primary worlds.
- Maximum 50 native ticks per task and 100,000 rule steps per tick. Training has exactly five episodes for trained arms. No Python agent dispatch is permitted.

## Outcomes and decision rules

Primary outcome is a correct native prediction plus an authorized action whose simulator receipt verifies the independent expected consequence (`behavior_success`). Acquired must exceed each of frozen, shuffled, and no-experience by at least 20 percentage points in each family. All allocated rows must be present, paired, and verified. Every orthogonal and reversal control must pass its registered structural criterion. Zero wrong-owner or stale-source acceptance, zero action after axis knockout/contestation, and zero target-field/hidden-solution input leaks are required; any violation fails conformance regardless of efficacy.

Action accuracy, prediction accuracy, candidate counts, graph node counts, training episode counts, and elapsed task time are reported descriptively. Missing proposals count as unsuccessful primary outcomes. No outcome or threshold may be removed after the held-out run.

## Artifact freeze

The runner and analyzer are the committed `evaluation/process_mastery/linear_p17_v2.py` and `evaluation/process_mastery/analyze_linear_p17_v2.py` at implementation commit `712eae5f27969eff8b3dfa6685e1bd3670526f5b`. The following hashes bind the scored source and runtime:

```json
{
  "protocol": "linear-p17-v2",
  "implementation_commit": "712eae5f27969eff8b3dfa6685e1bd3670526f5b",
  "artifacts": {
    "source_bundle_sha256": "138495281c1c85c79502f44d87dc559315aa305829ea8f471405db80045fffc0",
    "runner_sha256": "9a4ee18c147fd396f413d64668ff12587de3a207574233f166972ce9fd3b9244",
    "analyzer_sha256": "58ba44b03913911c958e9974624159207eb04282fc8b3ef749dc3d41d3eb6da8",
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1",
    "profile_sha256": "68264ae90b8fbf98cc433e211d9a2a00e18327d3bab261a3ffe741b6e1c5e735",
    "world_adapter_sha256": "00a861358cceeebc364e5eb44c092bd24c663057d71c459c2a36e708941b7326",
    "dependency_closure_sha256": "8e8512fe04516181b8d5ca0b96a530bac77b84f0f11192f8a27ecfc7dcd7cc78",
    "engine_source_sha256": "2ded41f8d4c036b3b89501db9dfbd117aead6273c80b843b9938b6969a1fa4b8"
  },
  "runtime": {
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5",
    "loaded_extension_sha256": "b4bbda168693def44b8da6825d0c6c9feddcae8249274524f746a9fa8ab062a1",
    "build_receipt_sha256": "6ea5443a70b410abf1c7bd697dac944a075a2f512f90db96a86d9e1a45e623a1",
    "build_source_fingerprint": "73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54"
  },
  "registered_allocation": {
    "families": ["tool_contact", "social_request_repair"],
    "arms": ["acquired", "frozen", "shuffled", "no_experience"],
    "worlds_per_family_per_arm": 200,
    "controls_per_family_per_kind": 100,
    "control_kinds": ["orthogonal", "reversal"],
    "training_episodes": 5,
    "exposure_budget": 1000.0,
    "max_ticks": 50,
    "max_steps_per_tick": 100000,
    "heldout_offset": 2000000
  },
  "development": {
    "worlds_per_family_per_arm": 8,
    "paired_worlds": 16,
    "scored_rows": 64,
    "controls_per_family_per_kind": 100,
    "integrity": "PASS",
    "conformance": "PASS",
    "efficacy": "PASS",
    "acquired_behavior_success": "8/8 in each family",
    "frozen_behavior_success": "0/8 in each family",
    "shuffled_behavior_success": "0/8 in each family",
    "no_experience_behavior_success": "0/8 in each family",
    "tamper_probes": "5/5 detected"
  }
}
```

The development allocation is not part of the held-out allocation. Held-out bytes must be preserved before analysis, and the frozen analyzer must validate exact native runtime identity and every row. Any protocol defect invalidates the run; a corrected protocol requires a new version and a fresh, disjoint allocation.
