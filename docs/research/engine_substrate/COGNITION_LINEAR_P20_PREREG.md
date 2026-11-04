# Linear P20 preregistration — fresh learning, transfer and social acquisition

**Protocol:** `linear-p20-v1`  
**Frozen against parent commit:** `882a00c0`  
**Status:** prospective; no held-out rows have been accessed as of this freeze.  
**Purpose:** evaluate the P20 fresh target learner, verified source-to-target transfer, social evidence routes and explanation reconstruction. This is a bounded mechanism study in two deterministic simulator worlds, not a claim about broad transfer or human learning.

## Frozen questions and criteria

The primary estimand is the paired difference in normalized target learning-curve area, mapped-source minus fresh, averaged over the two registered domain pairs. AUC uses the runner's fixed checkpoints and trapezoidal integration over target interactions. The primary passes at a gain of at least `0.20`; any smaller estimate, including a negative estimate, is a primary `FAIL` when the structural and provenance audit is valid. Missing or invalid panels make the primary `NOT_ESTABLISHED`. Mismatched-source is a negative-control arm and is reported separately; it does not replace the fresh comparator.

The secondary interaction-cost criterion is explicitly disabled for this protocol. No alternate interaction threshold or subgroup rescue will be substituted after the draw. Social acquisition and explanation-rebuild outcomes are descriptive mechanism panels with zero-tolerance structural checks: observation, demonstration and parsed instruction must verify and execute the complete sequence; reward-only must abstain when it contains no ordered action evidence. All structural controls must reject unsupported evidence. Explanation reconstructions must independently parse, preserve ordered semantics and preconditions, reject the counterexample, avoid source-AST leakage, and be adopted only after fresh-world verification.

## Worlds, arms and allocation

The target panel uses two independently implemented domain pairs: heat-source to thermal-sample and lever-control to latch. Each target stream has fresh, mapped-source and mismatched-source arms. Source information is supplied only in the mapped and mismatched arms; the learner can adopt a source prior only after native map evidence and independent target-effect receipts. The fixed scorer observes actual simulator receipts and does not supply answers to the learner.

The social panel uses observation, demonstration, parsed instruction and reward-only arms in the bounded request→repair world. Instruction is produced in a separate source graph and parsed in the receiver graph. Each accepted sequence must be independently verified in a fresh target world before the executor receives per-action authorization. Four structural control kinds are included: wrong frame, missing step, body mismatch and false description.

The held-out allocation is generated deterministically by `allocation("heldout")` in the frozen runner:

- 200 stream IDs per target domain pair, each evaluated in all three target arms (400 paired streams; 1,200 arm rows).
- 200 stream IDs per social arm (800 social rows).
- 25 controls per control kind (100 controls).
- 200 native explanation-rebuild streams.

The development allocation used for readiness checking is 8 streams per target pair, 8 per social arm, 25 per control kind and 8 explanation streams. The exact serialized allocation digests are embedded below. Stream namespaces are split-specific (`dev:` / `dev-control:` versus `heldout:` / `heldout-control:`); no held-out identifier is read during development. The registered worlds are the two pairs and social protocol named above; stream numbering and arm assignment are fixed by the runner and may not be altered after freeze.

## Resource and exposure accounting

The runner records target actions, source-information units, native rule steps, graph footprint, social evidence opportunities, visible observations, source-world actions, authorized target actions, budget debits, source and receiver native steps, graph nodes/bytes, explanation length, fresh-world actions, counterexample attempts and elapsed time. Every row, including abstentions and failures, remains in the denominator. No arm receives a disabled learner or a different native evidence policy.

Per target stream, the fixed tasks permit at most 3 target interactions in the mapped arm and 2 in fresh or mismatched arms; source evidence is limited to the two registered receipts in mapped/mismatched arms. Per social stream, the source contains at most two ordered action receipts (one scalar reward item in reward-only), and an executor can issue at most the two authorized sequence actions. Each explanation is bounded to the runner's fixed two semantic steps and one counterexample attempt. Budget debits, compute, graph growth, actions and source-information units will be reported by arm; no post-hoc resource normalization or exclusion is allowed.

## Validity, stopping and analysis

The single fixed allocation is run once after this file is committed alone. No efficacy-based interim stop, replacement stream, optional stopping or rerun is allowed. A runtime, adapter, allocation, provenance or control failure invalidates the affected registered result and is reported as `NOT_ESTABLISHED`; a valid negative efficacy result remains `FAIL`. The analyzer must verify complete pair×arm coverage, unique allocated IDs, exact allocation content and digest, current source-file hashes, exact loaded extension/build receipt attestation, all receipt gates and structural controls before classifying the primary.

Run after freeze:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p20_v1 \
  --split heldout --preregistration docs/research/engine_substrate/COGNITION_LINEAR_P20_PREREG.md \
  --output /tmp/cognition_p20_heldout.json
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p20_v1 \
  /tmp/cognition_p20_heldout.json \
  --preregistration docs/research/engine_substrate/COGNITION_LINEAR_P20_PREREG.md \
  --output /tmp/cognition_p20_heldout_analysis.json
```

Raw payloads and analyzer output remain outside git; their SHA-256 hashes and all criteria are recorded in the P20 results ledger. The runner enforces that this exact preregistration is clean, the immediately preceding commit contains only this file, its parent is the frozen code commit, and all runtime/provenance/allocation records match.

## Frozen artifacts

The loaded extension was verified with `ATTESTED` status, native symbols bound, build sources matching, and no attestation issues. Hashes below bind the runner, analyzer, source bundle, wrapper, loaded extension, build receipt, cognition-on profile, world adapters and dependency closure. Exact per-source hashes are captured in every run payload and checked by the analyzer.

P20_FREEZE_JSON: {"phase":"linear-p20-v1","freeze_parent_commit":"882a00c014297d618c47e327783a971410426b50","runner_sha256":"28bbcf3f3d6025a04f06b6b3888d26dfeec1c036d4f407d3c98a838dbacff277","analyzer_sha256":"4844fa47b3598f1b962e806d8c0317f0f720962c1a2912ebfeac1984c8d5ed63","source_bundle_sha256":"5f9c573332b0af7f057fb89268762320673083cfb46a1f9adcaf68cb9db83763","wrapper_sha256":"b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5","loaded_extension_sha256":"16b94f563be757ad9293e4921864466052d02e3fa07102ecff9e014b0b76a12b","build_receipt_sha256":"c350006f11edc703ae3668c302aedb9ae04aa61659e4752b6fb2bcdb7e4916a1","profile_sha256":"c05b83e5d42051dabbbb5fa17da73294a2dff349f4e144524d9bb3fd09f2f9d0","world_adapter_sha256":"dd0e5adf62a4433917266bf68b94159b5d96960b2339fe29357b621ef6a05c90","dependency_closure_sha256":"918f0b77bb15f1790a4c12d4ad34026027c4c7c19333d5b1aeec5d1fb669c35d","development_allocation_sha256":"8f4b89c4f2cd2ac58d2b11d8f998f08ae447b60b1865cf9f6730d78b830d167a","heldout_allocation_sha256":"daf7e1bea9da4d50620553870e3132611cb45e2143567a3b0e83de5bb15fa0eb","primary":{"metric":"normalized_learning_curve_auc","comparison":"mapped_source_minus_fresh","minimum_gain":0.2},"secondary_interaction_rule":{"enabled":false,"minimum_reduction":0.25,"maximum_success_loss":0.02}}
