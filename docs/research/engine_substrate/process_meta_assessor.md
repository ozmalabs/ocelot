# Process-level meta-assessor

The next fixer the agent identified when it assessed its own research loop. It is
the process-level successor to `domains/meta_monitor.py` — the single-process
spinning detector — built graph-resident (Rules / Term-trees, the
`recognition_graph` / `order_n_postulates` pattern), not as Python heuristics.

- Agent-composed (the decisions): `domains/process_meta_assessor.py` — four
  general Rules as composed Term-trees, evaluated natively.
- Dials (seeded data, not Python constants): `seeds/process_meta_assessor.json`.
- World-adapter I/O (mechanical): the loop-graph builders in the same module
  (`record_iteration`, `set_frontier`) and the read-back (`get_issues`).
- Live demo (side-by-side with the old detector + controls):
  `scripts/process_meta_assessor_demo.py`.
- Tests: `tests/test_process_meta_assessor.py`.

## Why the old detector missed this session's loop

`meta_monitor` watches a SINGLE process with one EFFORT signal and one PAYOFF
signal over a window, flagging `effort_without_payoff` when effort rises while
payoff stays flat. Fed this session's 5-iteration research loop it returned
`get_meta_issues() == []` for two wrong reasons (machine-verified, commit
e45bee08):

1. **Grain / scale.** `effort_rise = 4` (iter 1..5) is far below the dial
   `effort_min_rise = 20`, which is scaled for "322 features minted", not "5
   iterations". The spinning test never armed.
2. **Probe / payoff conflation.** It scored the loop as *improving* because a
   WER-margin moved (-8 → -4) while the recognition PROBE stayed BELOW unigram the
   whole run. The loop never actually recognised, but a different number moving
   made the one payoff channel look healthy.

## The three-part fix

- **Iteration grain.** The unit is an iteration; the window is iterations. A loop
  is a `ResearchLoopRoot` plus a chain of `Iteration` nodes linked `follows`, with
  `first_iter` / `last_iter` / `has_iter` edges so the window-aggregate rules can
  read both endpoints.
- **Two payoff channels.** Each iteration carries a PROBE channel (`probe_payoff`
  — the speech outcome, e.g. recognition margin over unigram) and a FIXER channel
  (`fixer_payoff` — cumulative loop-autonomy capabilities). Judged separately so a
  moving fixer can never mask a failing probe (the conflation fix) and probe
  spinning can never hide real fixer progress.
- **Frontier-awareness.** The root carries the current `frontier_rank` (the
  bottleneck's position in the upstream→downstream pipeline ordering). An iteration
  whose `pick_rank` is downstream of it spent effort below where the bottleneck is.

## The four rules (general predicates, zero session constants)

| Rule | Scope | Fires when |
|---|---|---|
| `DOMAIN_SPINNING` | window (root) | effort rose across the window AND the probe stayed below `probe_target` at BOTH endpoints → `loop_issue = domain_spinning`. Judged on the probe alone. |
| `FIXER_PROGRESS` | window (root) | fixer channel rose across the window → record `fixer_progressing = 1`; flag NOTHING (compounding capability is the real payoff). |
| `BELOW_FRONTIER` | per-iteration | `pick_rank > frontier_rank` (downstream of the frontier) → `below_frontier = 1`. |
| `FIX_THE_OUTCOME` | per-iteration | `fixer_delta <= fixer_flat_band` (added no capability) AND `moved_source == 0` (the change did not move its source) → `fix_the_outcome = 1`. |

Every threshold is a seeded dial. There is no `if iter == 5` anywhere — the rules
are predicates over the channels / ranks. Generality is proven two ways: on an
efficient control loop they flag nothing; on an all-spinning loop they flag
`domain_spinning`; and moving the frontier rank downstream stops `BELOW_FRONTIER`
firing on the same iterations (it reads the rank, not a hard-coded level).

## Live result on this session's loop

```
OLD meta_monitor : get_meta_issues() == []      (missed it)
NEW assessor     : loop_issue = domain_spinning  (probe never crossed target)
                   below_frontier = iter-2, iter-3, iter-4, iter-5(+gate)
                   fix_the_outcome = iter-5-gate   (the +0-fixer gate; iter-4 also
                                                    added +0 fixer but MOVED its
                                                    source, so is correctly NOT
                                                    flagged)
                   fixer_progressing = 1           (fixer rose 1 → 4; real progress)
```

`iter-5` in the brief is two moves: a fix-the-OUTCOME specificity gate (+0
capability, source unmoved) followed by the real harvest-precision fix (+1). The
demo and test model them as the two steps they were (`iter-5-gate`, `iter-5`),
faithful to the recorded fixer series 1,2,3,3,4 with the gate's +0 made explicit.
The discriminating contrast — iter-4 (+0 fixer, moved source) vs iter-5-gate (+0
fixer, source unmoved) — is exactly what `FIX_THE_OUTCOME`'s conjunction
distinguishes.

## Live vs stubbed (honest)

- **Live:** all four rules, their native evaluation, the loop graph, the
  side-by-side with the old detector, and the two synthetic controls. The signals
  `effort` / `probe_payoff` / `fixer_payoff` / `pick_rank` / `frontier_rank` /
  `moved_source` are reported by the world adapter; the rules are general
  regardless of where the numbers come from.
- **Stubbed:** the *automatic* wiring of two of those signals.
  - `frontier_rank` should come from the agent's own frontier flag
    (`domains/perception_self_assessment.py` already sets `frontier = "perception"`
    from the unit-predictability yardstick). The adapter currently sets it via
    `set_frontier`; connecting it to the perception self-assessment root is the next
    wiring step.
  - `moved_source` (FIX_THE_OUTCOME's "did the change move its source?") needs the
    measurement-feedback edges (`domains/measurement_feedback.py`) that record which
    source a change targeted and whether it moved. Until those are wired the adapter
    reports the flag from the recorded outcome. The RULE is live; the automatic
    source-movement signal is the stub.

Nothing in the detection is faked: the rules fire from the graph state, and the
acceptance checks (and tests) assert the verdicts, not prose.
