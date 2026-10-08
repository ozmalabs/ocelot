# CPython `stat` bounded module-composition current-source replay v1.2

Date: 2026-09-28  
Status: frozen before v1.2 candidate execution.

## Purpose

Re-run the same bounded module-composition intervention as v1.1 after adding an explicit `EmitError` for ambiguous/dynamic module-name references. Verify that the additional refusal guard preserves exact behavior on the frozen positive fragment. This is a current-source replay of an inspected family, not a new transfer estimate.

## Frozen workload and references

Use the unchanged v1 frame and schedule: seven `stat.S_IS*` predicates × five input cases (35 primary cases), plus the two frozen arithmetic controls. Preserve the v1 independent bit-mask oracle and case/source hashes. The v1 baseline artifacts remain raw `0a45d7f3df52630995ca62ed7f3fafe3c419a5983f7f888c26baaf288a77da98`, analysis `1b9b71713dd905056a1c0282e72409d4e823e5b8c0f3d567115fd3b0162a4589`, frame `d1538bb1dec48de2ef8d89252f1afd4f9e8159a0e9768688b29945b1ac5d8bc0`, lock `446445c9fbefe80a9b0137fbd167e23344a4280b5151786bf189148de46ac03c`.

## Source snapshot and claim boundary

The v1.1 run already passed 35/35 primary cases and 2/2 controls. Since that run, one additional emitter guard was added: a non-parameter `Name` whose top-level module binding is ambiguous/dynamic now raises `EmitError` instead of becoming an unconstrained Term variable. Current source is re-locked for this replay. The comparison against v1 also includes pre-existing `comprehend_text.py` and `boot_all.py` changes listed in the v1.1 source-drift amendment; score/cost differences remain non-causal. This replay does not separately exercise the new ambiguous-name refusal branch.

Two fresh workers, exact schedule, full stable locks, independent oracle/frame reconstruction, worker parity, both positive controls, shared run manifest and hashed console capture remain mandatory. Report coverage, wrong returns, abstentions, receipts/mints, wall/cpu costs, boot failures and RSS. Target success is 35/35 exact primary outputs, controls 2/2 and zero wrong returned values in both workers, with every integrity gate passing.
