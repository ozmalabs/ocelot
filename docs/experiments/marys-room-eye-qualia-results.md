# Mary’s Room with the eye and qualia system — RESULTS

Preregistered v1: `marys-room-eye-qualia-prereg.md` at commit `ec7b2b00`.
The first execution failed its liveness controls because default core cognition
seeds prevented the standalone color rules from running in the selected cycle.
That full failed output is preserved at
`results/marys_room_eye_qualia_v1_precondition_failure.json`.

The v2 amendment was committed at `6105820c`, before its confirmatory
invocation. The amendment uses a bare substrate with the same color and qualia
seeds; it does not alter any measured rules or thresholds. Runner:
`scripts/marys_room_eye_qualia.py`.

## v2 result — all preregistered gates pass

Engine provenance: `b6a41e3bbba6` in the isolated worktree.

- **Before release:** no eye regions or color categories; physical theory
  baseline predicts `(10, 0)` from the declared cone responses and opponent
  equations.
- **After chromatic release:** all 12 cells compute `(10, 0)`; one category is
  minted at `(10, 0)` with 12 members. `concept_signature` exposes `attr:crg`
  and `attr:cby` coordinates (`10.0`, `0.0`) in the shared signature space.
- **Achromatic floor:** all 12 cells compute `(0, 0)`; one neutral category is
  minted at `(0, 0)`.
- **Achromatopsia:** all 12 opponent values remain `(10, 0)`; no category is
  minted.
- **Overall:** PASS.

Raw output is preserved at `results/marys_room_eye_qualia.json`.

## Interpretation

The system’s declared physical equations predict the eye’s chromatic output
exactly. After input, the eye rules compute that output and the category is
readable in the shared qualia signature. Therefore this run demonstrates the
implemented distinction between a physical-theory prediction baseline and a
sensory-grounded category/signature update.

It does **not** show that physical theory lacked information about the
chromatic state: the theory predicted the exact opponent coordinates before
release. It does not establish phenomenal experience or settle Mary’s Room.
