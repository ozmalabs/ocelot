# Linear P6 evaluation preregistration

Status: **frozen before the held-out draw**. This is the sole P6 v1 protocol. Any correction to the runner, scorer, task IDs, limits, or criteria requires a new protocol version and untouched allocation.

## Frozen implementation

- Plan: `COGNITION_BUILD_PLAN_20261010.md`, P6.01–P6.E3.
- Runner: `evaluation/process_mastery/linear_p6_v1.py`, SHA-256 `ee7dbec4098f027f7f4d70bbaeec3c86217455d9c64baccb90d75b3445cf5f7f`.
- Analyzer: `evaluation/process_mastery/analyze_linear_p6_v1.py` (included in source bundle below).
- Agent/profile/world source bundle SHA-256: `cb20ae4304068ddaa68d4a8215187403151f9adb64124b9515d64b4673f6ae97`.
- Native engine source bundle SHA-256: `f8217681e706ef1c64f380e59b1dc98f4526d8f656acc8a3b7cec43191c39525`.
- Native extension binary SHA-256: `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`.
- Source commit: `3178ee20dc34ed568d1ea3a3acdd760584e9bb07`.
- Dataset: vendored MBPP sanitized subset, fixture SHA-256 `ca95deaa9a01ef0a6f439f88bcf0dd3db3563d22f22aad6cae04ebb9a8d8c8e9`; provenance is `tests/fixtures/mbpp/provenance.json`.
- Runtime: Python 3.13.5, seed persistence disabled, no LLM.

The exact arm limit is **3 native ticks, at most 100 rule steps per tick**. Exceeding the tick limit without a solved state is `TIMEOUT`; quiescing without success is `FAILED`. Each task uses a fresh isolated graph. The baseline omits every Track I seed and policy. The treatment adds the frozen Track I closure. Both arms receive the same task instance, world affordances, visible state/goal, and limits.

## Allocations and protocols

| Panel | Held-out allocation | Input and scorer boundary | Primary report |
|---|---|---|---|
| Loopover (a) | 200 seeds `1,000,000–1,000,199`; 2×2 board; eight-move deterministic scramble | Initial board, solved goal, and declared row/column processes are visible. The native graph chooses and applies processes; final state is read back mechanically. | Paired solved fraction, primitive steps, ticks, elapsed time, graph growth, and process trace. |
| D4 (c) | 200 seeds `1,000,200–1,000,399` | `d4_task(seed)` creates each shape and transform. No grounded D4 action/effect adapter is registered; both arms are explicitly `NOT_RUN`. Only a scorer-side transform digest is retained. | `NOT_RUN` counts and reason. No comparative D4 claim. |
| Finite mechanism (b) | 200 seeds `1,000,400–1,000,599` | `blicket_task(seed)` creates hidden truth. No intervention/observation adapter is registered; both arms are explicitly `NOT_RUN`. Only a scorer-side truth digest is retained. | `NOT_RUN` counts and reason. No comparative mechanism claim. |
| View controls | 100 cases `1,000,600–1,000,699`; case class cycles malformed, stale Program source, opaque TransitionHypothesis | Detached `ProcessApply` must return unknown and leave serialized graph attributes unchanged. | Fail-closed and zero-mutation counts. |
| Program synthesis (e) | All runnable vendored MBPP test tasks listed below (task IDs in `11–510`) | Existing `prog_synthesis` rules only. The first parseable assertion is revealed; remaining parseable assertions stay in the detached evaluator. Test `code` is stripped before task handling. | Accepted candidate rate; external all-held-out-assertions pass rate; solver status, attempts/budget, elapsed time, graph growth. |

Exact runnable MBPP test task IDs (240):

```text
11, 12, 14, 16, 17, 18, 19, 20, 56, 57, 58, 59, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 74, 75, 77, 79, 80, 83, 84, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 99, 100, 101, 102, 103, 104, 105, 106, 108, 109, 113, 115, 116, 117, 118, 119, 120, 123, 125, 126, 127, 128, 129, 130, 131, 132, 133, 135, 138, 141, 142, 143, 145, 160, 161, 162, 164, 165, 166, 167, 168, 170, 171, 172, 222, 223, 224, 226, 227, 228, 229, 230, 234, 235, 237, 238, 239, 240, 242, 244, 245, 247, 249, 250, 251, 252, 253, 255, 256, 257, 259, 260, 261, 262, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 290, 291, 292, 293, 294, 295, 296, 297, 299, 301, 304, 305, 306, 307, 308, 309, 310, 311, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 417, 418, 419, 420, 421, 422, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 468, 470, 471, 472, 474, 475, 476, 477, 478, 479
```

The train/development split is disjoint: Loopover seeds `0–199`, D4 `200–399`, mechanism `400–599`, controls `600–699`, and MBPP validation IDs `511–600`. Development raw scorecard SHA-256 is `4c9f321cdf1d718bad8314d9601161491dae430123b8d76d79c2abd0922e205b`; its analysis SHA-256 is `d95601cd46b909fa5e25e900b6f741d6c39a978a5941ea5c063c135a2889f193`. Development outcomes were 0/200 Loopover baseline and 200/200 Track I; MBPP validation was 3/41 all-held-out passes in each arm; 100/100 view controls passed. D4 and mechanism each returned 200 `NOT_RUN` rows per arm because their adapters are absent. This freezes their non-comparability; it does not turn the panels into measured failures or authorize a capability claim.

## Criteria and execution

Primary outcomes are descriptive paired results; there is no human-parity claim. A new Track I gain is not inferred from the 2×2 Loopover panel or from MBPP, whose solver is unchanged between profiles. D4 and mechanism remain blocked unless an adapter exists before this freeze; this version will report their preregistered `NOT_RUN` records and will not substitute another task or solver. All 100 controls must fail closed with zero graph-attribute mutation. The MBPP solution/code and held-out assertions must not enter the agent graph. Any leakage invalidates the affected family result. Unsupported/NOT_RUN, TIMEOUT, FAILED, and COMPLETED remain distinct.

Development self-checks, completed before this freeze:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p6_v1 --split development --self-check
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p6_v1 --self-check
```

Registered held-out run and analysis (raw JSON stays outside git):

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p6_v1 --split heldout --output /tmp/linear-p6-heldout.json
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p6_v1 /tmp/linear-p6-heldout.json
sha256sum /tmp/linear-p6-heldout.json
```

Do not change the frozen source, IDs, limits, criteria, or analyzer after starting this draw. A failed or unsupported outcome is retained as measured here; corrections require a new protocol and untouched allocation.
