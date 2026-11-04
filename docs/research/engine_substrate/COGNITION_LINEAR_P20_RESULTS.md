# Linear P20 results — fresh learning, transfer and social acquisition

**Protocol:** [`COGNITION_LINEAR_P20_PREREG.md`](COGNITION_LINEAR_P20_PREREG.md), committed alone as `42e577db`.  
**Run:** single frozen allocation, 2026-10-23.  
**Classification:** structural audit `PASS`; runtime provenance `ATTESTED`; primary transfer efficacy `FAIL`.

## Frozen primary

The registered mapped-source minus fresh normalized learning-curve AUC difference was **−0.3333**, below the frozen `+0.20` threshold. Fresh AUC was `0.5000`, mapped-source AUC `0.1667`, and mismatched-source AUC `0.5000`. The primary is a valid negative result, not an invalid or underpowered run. The secondary interaction-cost criterion was disabled in advance and was not evaluated as a rescue.

Both domain pairs show the same aggregate AUC; stream counts and all fixed checkpoints are preserved in the raw payload. Mapped-source required three target interactions on average versus two for fresh and mismatched-source. It also consumed two source-information units per target stream, compared with zero for fresh. The result therefore does not establish that the native mapped prior improves target learning under this protocol.

## Mechanism and structural outcomes

The allocation completed with 1,200 target arm rows (200 streams per pair × three arms), 800 social rows (200 per arm), 200 explanation trials and 100 structural controls. The analyzer found complete allocated coverage, no duplicate IDs, exact allocation/provenance hashes, valid receipts and no structural failures.

Observation, demonstration and instruction each verified and executed 200/200 sequences in fresh worlds, with two authorized actions per stream. Reward-only abstained as underidentified in 200/200 streams and issued no actions. All 100 wrong-frame, missing-step, body-mismatch and false-description controls passed. The explanation arm verified and adopted 200/200 reconstructions, with 100% fidelity, two fresh-world actions and one counterexample attempt per trial; source-AST leakage remained false.

Mean target resource records per stream were:

| Arm | Target actions | Source-information units | Native rule steps | Graph nodes | Graph bytes |
|---|---:|---:|---:|---:|---:|
| Fresh | 2 | 0 | 10 | 762 | 55,636.5 |
| Mapped source | 3 | 2 | 14 | 766 | 58,725.5 |
| Mismatched source | 2 | 2 | 12 | 766 | 57,930 |

Social budget debits were two per sequence-bearing stream and one per reward-only stream. Mean source-information units were 2 for observation, 2 for demonstration, 15 for parsed instruction and 1 for reward-only. Instruction's 15 units include its bounded natural-language exposure. The fixed panel permitted at most two own actions per stream; sequence-bearing arms used both, reward-only used none. Explanation trials averaged three total source/receiver budget debits and 14 words.

## Provenance and artifacts

The exact loaded extension, wrapper and build receipt were attested; build sources matched, native symbols were bound and the attestation reported no issues. The preregistration and analyzer both verified the frozen parent, standalone freeze commit, fixed allocation and source/profile/world/dependency hashes.

- Raw payload: `/tmp/cognition_p20_heldout.json`, SHA-256 `76f575f5710449f58adf0d7152452a14d2d831f643bee5b4e7599d90e2f938c8`.
- Analyzer output: `/tmp/cognition_p20_heldout_analysis.json`, SHA-256 `6ecfaa9738670bb32ef41f87e96c38aaeaf315ed6c2a903bcd9312d84233f5c8`.
- Frozen development raw payload: `/tmp/cognition_p20_combined_dev_8x100.json`, SHA-256 `671c3d02b760027c0d4a79c8455fa88677e6ec9630f4b43b4149bb9d763a0cd2`.
- Frozen development analyzer: `/tmp/cognition_p20_combined_dev_8x100_analysis.json`; structural `PASS`, primary `NOT_ESTIMATED`, provenance `ATTESTED`.
- Held-out allocation SHA-256: `daf7e1bea9da4d50620553870e3132611cb45e2143567a3b0e83de5bb15fa0eb`.
- Development allocation SHA-256: `8f4b89c4f2cd2ac58d2b11d8f998f08ae447b60b1865cf9f6730d78b830d167a`.

The focused P20 suite passed 101 tests before final freeze hardening; the runner/analyzer test file passed 4 tests after those changes. The full held-out analyzer returned structural `PASS` with no failures. These results support the bounded fresh learner, social sequence adapters and explanation reconstruction mechanisms in the declared simulator panels. They do not establish beneficial transfer, general social learning, open-ended language reconstruction or any broad capability level.

## Phase 21 entry decision

Proceed to P21 using the fresh native target learner as the supported training-task consumer. Treat mapped-source benefit as unsupported and do not depend on transfer for retention or curriculum effects. Carry forward the P20 `FAIL` unchanged; no P20 holdout rerun or threshold revision is authorized by this result.
