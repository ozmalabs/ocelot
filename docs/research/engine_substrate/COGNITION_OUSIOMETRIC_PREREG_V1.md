# P28 representation-value preregistration v1

Status: **FROZEN**. This standalone protocol was committed before any P28.14 sealed allocation is opened. The freeze fixes a paired behavioral panel on two registered simulator families; it does not claim human semantic calibration. The lexical endpoint is unsupported because there is no frozen lexical checkpoint/token bridge, and the external target score columns remain unopened.

## Frozen question and decision

The sole primary compares `eq4_rotation_64bit_fixed_l1` with `shared_basis_64bit_fixed_l1` on paired normalized learning-curve AUC, separately in `tool_intervention` and `social_request_repair`. Since compatible feature-to-lexical calibration is absent, this is labeled **published-rotation-bounded** and refers only to the rounded full-rank Eq. 4 map used as a bounded axis-aligned representation. It does not identify psychological VAD/PDS semantics or a new-information effect.

Each family has 200 fixed seeds and each seed is run in every one of six arms. The fixed source-evidence horizons are 0, 1, 2, and 4 verified receipts. Every arm gets the same changed-map target calibration action and fresh target scoring schedule for the paired world. The four-point learning curve scores an authorized, receipt-verified, goal-satisfying outcome as 1 and all failures, abstentions, timeouts, or unverified outcomes as 0. No row is excluded for its outcome.

For each family, report the mean paired AUC difference, a 99% paired world bootstrap interval (10,000 resamples), and a one-sided paired sign-flip randomization p-value (100,000 flips). Holm-correct the two family p-values at alpha .01. A family passes only if the mean advantage is at least 0.10, the 99% lower interval exceeds zero, its Holm p-value is at most .01, and the adverse-consequence rate increase is no greater than 0.02. The primary passes only if both families pass. This is a frozen decision rule; no arm, endpoint, threshold, seed, or exclusion may be changed after opening.

## Arms, secondary controls, and costs

All six registered arms use the same native goal/action consumer: shared-basis fixed L1 (comparator), Eq. 4 fixed L1 (treatment), shared-basis transported L1, Eq. 4 transported L1, one deterministic seeded random rotation, and an 8-bit Eq. 4 fixed-L1 precision control. Full-rank transported controls test coordinate invariance. Fixed metric and reduced precision arms describe bounded basis/precision effects. None replaces the single primary contrast.

Every checkpoint retains verification checks, metric queries, native steps, target actions, failed proposals, representation and mapping bits, coordinate precision, decoder graph bytes/nodes, elapsed seconds, and remaining budget. Report per-arm means for these costs. These simulator results cannot establish environmental safety or broad competence.

## Lexical and safety boundaries

Identifier-only concept split is namespace `p28-ousiometry-v1`; its fixed digest, source payload hashes and counts are embedded below. The split is label-blind. No checkpoint or token-to-concept bridge is frozen, so external GPADS/NRC scores are not opened or analyzed and lexical status remains `UNSUPPORTED`. If calibration remains absent, no psychological or semantic alignment claim is permitted.

Language is untrusted/asserted evidence only. Physical action decisions require the existing verified consequence path and time-indexed future-manifold boundary; reassuring text cannot hide measured escape, and frightening/quoted/negated text cannot prove danger. The same-epoch native stop veto remains authoritative.

## Provenance and execution

The machine-readable block pins the complete source-hash bundle, loaded native runtime attestation, seeds, transformation, profile, data manifest, lexical readiness and analysis constants. The evaluator rejects mismatched hashes or protocol parameters before running. It writes raw results to `/tmp/p28_ousiometric_raw_v1.json` by default. Hash raw bytes before analysis; analyze exactly once with `evaluation.ousiometrics.analyze_v1`. The preregistration file is committed alone before that run.

<!-- P28_PREREG_JSON
{
  "acquisition_seed_sha256": "9714db5151b14930eba167fa501ae6434ae44b1fa30db5a2418c48d26c566b4b",
  "allocation": {
    "seed_list_hashes": {
      "social": "4822143430328110717d209b578ecd2a406c5e039d1a01f7f42816ad254da972",
      "tool": "5eb8bdf96843afd73e2ecf2125fbc1209662000836744cbf88b7e8c1e884b879"
    },
    "seeds_disjoint": true,
    "social_seed_start": 36202610000,
    "tool_seed_start": 28202610000
  },
  "capacity_and_costs": {
    "costs_per_checkpoint": [
      "exact_checks",
      "query_count",
      "native_steps",
      "target_actions",
      "failed_proposals",
      "frame_mapping_bits",
      "metric_policy_bits",
      "coordinate_bits",
      "total_representation_bits",
      "decoder_graph_bytes",
      "decoder_graph_nodes",
      "wall_time_seconds",
      "thinking_budget_remaining"
    ],
    "declared_arms": [
      "shared_basis_64bit_fixed_l1",
      "eq4_rotation_64bit_fixed_l1",
      "shared_basis_64bit_transported_l1",
      "eq4_rotation_64bit_transported_l1",
      "random_rotation_dev_64bit_fixed_l1",
      "eq4_rotation_8bit_fixed_l1"
    ],
    "primary_capacity": "three coordinates, 64-bit primary fixed frames, same source receipts, target calibration action, action opportunities and verifier policy",
    "resource_limits": "runner-defined investigation profile and simulator task envelope; all action failures and abstentions remain in the data"
  },
  "checkpoint_sha256": null,
  "checks_before_draw": {
    "all_behavior_arms_and_worlds_use_same_native_consumer": "PASS",
    "frequency_and_rare_adverse_controls": "PASS",
    "investigation_profile_isolation": "PASS",
    "lexical_arm": "UNSUPPORTED",
    "loaded_native_runtime": "ATTESTED",
    "mathematical_full_rank_equivalence": "PASS",
    "native_host_veto": "PASS",
    "profile_dependency_orphan_audit": "PASS",
    "risk_residual_boundary": "PASS"
  },
  "controls": {
    "all_failures_retained": true,
    "geometry": "full-rank Eq4 rounded display map and computed inverse; transported full-information predictions/distance parity within float64 tolerance",
    "lexical_scores_opened": false,
    "no_host_action_selection": true,
    "risk_boundary": "measured future-manifold residual and same-epoch native stop veto; language evidence cannot authorize or suppress a physical action",
    "same_native_action_consumer": true
  },
  "external_source_manifest": {
    "sources": [
      {
        "citation": "Dodds et al. (2026), doi:10.1126/sciadv.adr4039; Zenodo doi:10.5281/zenodo.18509376",
        "columns": [
          "word",
          "goodness",
          "power",
          "aggression",
          "danger",
          "structure"
        ],
        "container_sha256": "",
        "key": "gpads",
        "license_id": "CC-BY-4.0",
        "payload_name": "ousiometry_GPADS.txt",
        "payload_sha256": "1825f9f23b796add681bd6dcd9753e8f1bf68cbf158c4af5e710bbc507b47e0a",
        "redistribution_permitted": true,
        "sign_convention": "goodness/power/aggression/danger: signed source coordinates; structure high=unstructured, low=structured",
        "source_url": "https://zenodo.org/records/18509376",
        "terms": "Attribution required; verify record terms on retrieval.",
        "units": "source score units; centered ratings as distributed",
        "version": "v2 (published 2026-02-06)"
      },
      {
        "citation": "Mohammad (2018), Obtaining Reliable Human Ratings of Valence, Arousal, and Dominance for 20,000 English Words",
        "columns": [
          "English Word",
          "Valence",
          "Arousal",
          "Dominance"
        ],
        "container_sha256": "f956a7814823d22b34e67af451a33095f57635f11dae98728dee891a30a83aea",
        "key": "nrc_vad",
        "license_id": "NRC non-commercial research/educational terms",
        "payload_name": "NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt",
        "payload_sha256": "fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7",
        "redistribution_permitted": false,
        "sign_convention": "higher valence=more positive, higher arousal=more active, higher dominance=more dominant",
        "source_url": "https://saifmohammad.com/WebPages/nrc-vad.html",
        "terms": "Free for non-commercial research/education; citation required; redistribution prohibited.",
        "units": "dimension scores on [0,1]; paper centers each dimension by 0.5 before SVD",
        "version": "v1 (released 2018; README updated 2022)"
      }
    ],
    "split_policy": {
      "cluster_hash": "SHA-256 of sorted canonical lexical identifiers in each connected synonym family",
      "cluster_source": "WordNet synsets from the repository's pinned sense table; no score columns",
      "identifier_normalization": "Unicode NFKC, casefold, strip outer whitespace",
      "split_fraction_rule": "first digest byte: 0-127 train, 128-165 development, 166-191 anchor, 192-255 heldout",
      "split_hash": "SHA-256 of protocol namespace plus cluster hash; deterministic, label-blind"
    },
    "transformation": {
      "equation": "Eq. 4",
      "limitations": "paper reports approximate coefficients; source/preprocessing reproduction is required for psychological lexical calibration and reproducing original empirical coordinates",
      "paper_doi": "10.1126/sciadv.adr4039",
      "precision": "rounded display coefficients; frozen coefficients plus computed inverse define a mathematical reference map, not a reproduction of original empirical coordinates",
      "printed_vad_to_pds": [
        [
          0.5,
          0.48,
          0.72
        ],
        [
          -0.72,
          0.69,
          0.04
        ],
        [
          0.48,
          0.55,
          -0.69
        ]
      ],
      "procedure": "center original NRC VAD dimensions by 0.5, full 3D SVD, orient G/A/St, then rotate G/A plane by -pi/4"
    }
  },
  "frame_seed_sha256": "84c97dd8f90077d0ed5d6e2b0eb889d32a9b708a0d1b696e47b1e74302cb02f6",
  "lexical_source_hashes": {
    "checkpoint_sha256": null,
    "cluster_count": 7723,
    "gpads_v2_payload_sha256": "1825f9f23b796add681bd6dcd9753e8f1bf68cbf158c4af5e710bbc507b47e0a",
    "nrc_vad_v1_payload_sha256": "fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7",
    "oversized_cluster_count": 1,
    "oversized_cluster_size": 10726,
    "scores_opened": false,
    "split_counts": {
      "anchor": 941,
      "development": 1348,
      "heldout": 2320,
      "train": 15361
    },
    "split_digest": "0670f22600947a83d666708fe6a39c1886912ba0c83070f0106c83ca5595d726",
    "split_namespace": "p28-ousiometry-v1",
    "token_bridge_sha256": null
  },
  "lexical_status": "UNSUPPORTED",
  "paper_transform_sha256": "c7532105c2796d1ca9b263f34ca726ba627fcae4ffc79c2c33df0189eabe7a84",
  "primary": {
    "comparator": "shared_basis_64bit_fixed_l1",
    "direction": "treatment greater than comparator",
    "estimand": "paired normalized learning-curve trapezoidal AUC difference",
    "status_label": "published-rotation-bounded",
    "success_definition": "world verifies selected authorized action and task goal is satisfied; every abstention/failure scores 0",
    "treatment": "eq4_rotation_64bit_fixed_l1"
  },
  "protocol": {
    "arms": [
      "shared_basis_64bit_fixed_l1",
      "eq4_rotation_64bit_fixed_l1",
      "shared_basis_64bit_transported_l1",
      "eq4_rotation_64bit_transported_l1",
      "random_rotation_dev_64bit_fixed_l1",
      "eq4_rotation_8bit_fixed_l1"
    ],
    "bootstrap_replicates": 10000,
    "bootstrap_seed": 28202614,
    "holm_alpha": 0.01,
    "horizons": [
      0,
      1,
      2,
      4
    ],
    "minimum_auc_improvement": 0.1,
    "paired_sign_flip_replicates": 100000,
    "replicates_per_family": 200,
    "safety_noninferiority_margin": 0.02,
    "world_families": [
      "tool_intervention",
      "social_request_repair"
    ]
  },
  "randomization": {
    "bootstrap_unit": "paired seed/world; resample within each family",
    "multiplicity": "Holm across the two family-specific primary tests",
    "pairing": "same family seed and source/target schedule across every arm",
    "primary_gate": "each family mean AUC difference >= 0.10, 99% paired bootstrap lower bound > 0, Holm adjusted one-sided paired sign-flip p <= .01, adverse consequence rate increase <= .02"
  },
  "representation_profile_sha256": "b27fca45f2c3f88923c73b193d0f3ece3398668682afc418d3f4e96a78daf051",
  "runtime_attestation": {
    "build_receipt_path": "/home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.build.json",
    "build_receipt_sha256": "661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66",
    "build_source_fingerprint": "a525aa2d8ffcb430e1268c368cad6c97f59092e16b048ee397e73cc1a71e34e3",
    "build_sources_match": true,
    "issues": [],
    "loaded_extension_path": "/home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so",
    "loaded_extension_sha256": "5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07",
    "native_symbols_bound": true,
    "status": "ATTESTED",
    "wrapper_path": "/home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/__init__.py",
    "wrapper_sha256": "b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5"
  },
  "scores_opened": false,
  "seed_allocation": {
    "n_per_family": 200,
    "social_seed_list_sha256": "4822143430328110717d209b578ecd2a406c5e039d1a01f7f42816ad254da972",
    "social_start": 36202610000,
    "tool_seed_list_sha256": "5eb8bdf96843afd73e2ecf2125fbc1209662000836744cbf88b7e8c1e884b879",
    "tool_start": 28202610000
  },
  "source_hashes": {
    "docs/research/engine_substrate/COGNITION_OUSIOMETRIC_CONTRACT.md": "2c78bcf29ee0ecdf4540c58d71a38ab5d78073ae0fa73281c4d636ea458db697",
    "docs/research/engine_substrate/OUSIOMETRIC_DATA_MANIFEST.md": "769e7170140c5aa864035e6b1869d8c75a3b2be1b74ea83f6f744537e57d3174",
    "domains/commitment_gate.py": "84cf65cad146cbc2a9ee47bc72ef73f67617a7a4c66a3c5e9ede3b08e2418b2f",
    "domains/future_option_risk.py": "63ea7ca9cd44226fd1b04a356470c87d7aa816d825fe2c5e3fe7d17fe265e786",
    "evaluation/ousiometrics/analyze_v1.py": "e85354936fcfa5c640674c6e0160cef8d4a6a64d455349895f5d441755dd94bc",
    "evaluation/ousiometrics/behavior_panel.py": "349a062049b4b2e9b6fc3087e08947c4fd3b38d18d25064c803a2531eb582342",
    "evaluation/ousiometrics/distribution_panel.py": "845d6bf78a07e2bd26192f5b53b0e53108f9a78d683ef8180e779a7847d267f9",
    "evaluation/ousiometrics/geometry_reference.py": "68dbe680efd872227893ccedfd7f9262d51ef89eed377e5a321622ca32ac6804",
    "evaluation/ousiometrics/lexical_validation.py": "746007989ca866aea526b10cc732ba78b69cc1764ade9dfec40a6f092f332807",
    "evaluation/ousiometrics/native_adapter.py": "5bee18a5e7af5fac2f8688158d13a4489fe8f76e06984c0a2163f123514c2be6",
    "evaluation/ousiometrics/run_v1.py": "2198d6a92973dd49511d25c65c98aa7c4ff4f6139e5f7484c1c79919f0d9cc80",
    "evaluation/ousiometrics/source_manifest.py": "00ba8d0158e9b4d6a59e59fcca7a81127f1263dc313cc956bb5aa595d7623e7e",
    "evaluation/ousiometrics/worlds.py": "320f9086c43fe05708c17609f9446fc371348951e7b98ee4838a1308748955e9",
    "evaluation/process_mastery/common_target_learner.py": "26d131acc67fd9bf7a77d14244cc3c1683eece3b276847bdb08ebe9b11edc1fa",
    "evaluation/process_mastery/harness.py": "f4ec0357a679c08feb8041d0e982823bf36caf8322f399d1863fc6ce81d738bf",
    "evaluation/process_mastery/target_learner.py": "56a514abb58a4a780c3af823cfee3f54fc8690a67accc0b2156e848846713df1",
    "scripts/gen_response_inhibition_seed.py": "38a6e1a6ca8670bfc07bc5b18ff57a8e1a957846d65422d5039bdca13955091f",
    "seeds/adaptive_control_core.json": "79fd69946de61bd36f15cccd896f984766ee19357b9c6da1593b5e3cf5921eb8",
    "seeds/affective_state_core.json": "9cfd82ff99c780a0ddfb5ec65942fef77ea2275341e6a09f5b78d1910c354990",
    "seeds/decision_core.json": "a2226728536b18760ffbeac4d699aad4db9d965f4a0f37470f73350c8b202198",
    "seeds/default_mode_core.json": "bdbdb5b3505a410fa2533a3cdc6e56b5bd10d2b5d85879f38ff87515c33e8ab1",
    "seeds/episodic_working_memory_core.json": "023050b48704fa75ed8da0c2db64c2e468f355112b5578897a04caa643fd9b57",
    "seeds/epistemics_core.json": "485d3517bd988d332312fc08b83c2d757bd13a613e0a7d8ad4e1972ddae81e3e",
    "seeds/experimentation_core.json": "dfbba83b66305e06328a3cc737765da56e0ab3fc66580b45dad7d75b0fb1ff7a",
    "seeds/generative_world_model.json": "f147432955e1970bae03f1ec8cb1b3238fe8abba1520129e506c3600a07ed0a6",
    "seeds/goal_construction.json": "598a573afb85beaaaafc90a6259e01f1cde211ffc4ea96acd1f2b9074d2e0e83",
    "seeds/learning_core.json": "8269692b08f399096fef7d15bc58a207d79477e6954288aa09d3ed5e98bd3141",
    "seeds/memory_core.json": "5ec7f07b90f192bc3cea660d87335e34c5074d466a7d484b7381abf651231e6b",
    "seeds/motor_core.json": "12cbe423bd6f1149fe28801e9172f86eaf34744948975a4bae27e349f7cbd6c3",
    "seeds/ousiometric_acquisition.json": "9714db5151b14930eba167fa501ae6434ae44b1fa30db5a2418c48d26c566b4b",
    "seeds/ousiometric_frames.json": "84c97dd8f90077d0ed5d6e2b0eb889d32a9b708a0d1b696e47b1e74302cb02f6",
    "seeds/perception_core.json": "7a274b9410bce9503392f0210bb22873273ea91c1558b9007e57885d852ae9bc",
    "seeds/process_induction.json": "8a1018cf42b8db4c44a48a2103705358322528102604d900e410121beed6ba4c",
    "seeds/qualia_acquisition.json": "7d13c76b4288f84bd91f032c013be434deb775c1a24febe6e01f6dff13881145",
    "seeds/qualia_behavior.json": "640cc271971741272dcb345a96cf352a428c3a5d9fdaeeeccd6f3e06986ffedd",
    "seeds/reflex_core.json": "f760e7821058306a48b6550fb041c871f044b18d0ef1359238fe90d292726c43",
    "seeds/response_inhibition.json": "db17a126e774609025ccec60d5e77ffe3f55cc5080623a5989fde7c911f1e3d3",
    "seeds/self_monitoring.json": "17cc07e1460c1505b6d223bdca203b4c3fbe17669971d904a5ffff322032eb58",
    "seeds/target_learning.json": "70c61ff72fe84c944685ac575a23bffedb7ab5589b7713dc285c266d2e9541b4",
    "seeds/theorem_core.json": "5630cfd5bd90a3c23f3346cbbc90af32a8f64848a287913b7688879095a7d332",
    "seeds/thinking_budget.json": "3aa1f98b7b97a010c5c0862e997d422276306c4a6579c9fda7c5595e912d5313",
    "substrate/world_adapter.py": "baf71b3e71b779f006f8266ae76d6e7c1d5e45588f85eea175dc145a8cd405ad",
    "tests/test_ousiometric_behavior_panel.py": "cf503d712e246ed03bc0026941d4f05472394af0e8df350881f4a9f7b2b4aafb",
    "tests/test_ousiometric_causal_controls.py": "c501c72b04740446363095450ace3f1692e797432d245f9c15d803d498f47124",
    "tests/test_ousiometric_distribution_panel.py": "e69da28763642e648121c94acf0f6251fcc2460b9bf47c258838b28e314db1ff",
    "tests/test_ousiometric_lexical_validation.py": "aeb40e1c6e3e3f599eec4de74b6642462221cd9825a05340a2db10aa98e7c17f",
    "tests/test_ousiometric_native_adapter.py": "8b2e4fcbee93fda7db4edd07ebd427367634f9f0dd9a0434e7f717cd79f25c2d",
    "tests/test_ousiometric_risk_boundary.py": "8a154ce8cf1704a663cad1b74391bd9bf0237f2181fa14d6c2b491223b2a4240",
    "tests/test_ousiometric_worlds.py": "0491e251d4132b07aa9b92ed30e85c45537c9c4342c936994375b07acce4f70b",
    "tests/test_ousiometrics_geometry.py": "3a561ffb8840242e6a203f7f953f2b7dbd64e00a7fe2d1b6bb4ee9254568a5fa",
    "tests/test_response_inhibition_migrated.py": "c9c055e2c24ad8d3a084892d4c81f1b743a87e3adfabf776662d96c0fcb5a1a3"
  },
  "status": "FROZEN",
  "token_to_concept_bridge_sha256": null
}
-->
