# LS20 UNDERSTANDING — PRE-REGISTRATION (block 221000)

**Status:** pre-registered, MEASURE-FIRST. Committed ALONE before the measure
script / results. Block `221000` claimed CLEAN by
`python scripts/seed_claim.py 221000 221999` (exit 0, "no collision DETECTED").

## THE REFRAME (owner steer, non-negotiable — lead with it)

*"Not win condition — winning is a side effect of understanding. The true victory
is knowledge."* The objective is to **UNDERSTAND ls20's mechanic**, NOT to win.
Binding to the win state is goal-blindness one level up. This rung applies the
project's own **curiosity drive + compression-as-quality + predict-and-residual
(the sd-loop / order-N)** to the game DYNAMICS. **Winning is LOGGED as a
downstream consequence; it is NEVER an objective function anywhere in the graph.**

## WHAT "UNDERSTANDING THE MECHANIC" IS, CONCRETELY (assemble, do not invent)

The mechanic to understand: a set of `S` transform **stations**, each applying an
unknown transform (rot90:k / reflect / recolour) to a carried symbol. The agent
does NOT read which station does what — it **discovers** the station→transform map
by investigation. All machinery is EXISTING:

- **Perceive** — the 216000 pixel eye (`recover_grid_from_render`) sees the probe/
  goal; the 217000 sd-loop (`recognise_required_key`, TransformDecode/DimInfer)
  RECOGNISES the transform a station applied (before→after). Dimension-arbitrary,
  graph-native, nothing ls20-specific.
- **Model** — a station's effect is a `Hypothesis{key, conf}` minted as graph data
  (the `qf_* msp CLOSED → mint-Hypothesis` precedent). Each hypothesis carries a
  PREDICTION (its `key`).
- **Curiosity** — `uh_probe_pick` routes to the LEAST-modelled station
  (`Argmin visits`), the `ae_frontier_goal` Argmax precedent — NOT to the goal.
- **Test = predict-and-residual** — `uh_predict` predicts the station's effect from
  the model; the OBSERVED effect gives the RESIDUAL (= surprise); a confirmed
  prediction COMPRESSES the model (`uh_confirm`), a surprise MINTS (`uh_mint`) or
  REVISES (`uh_revise`) a hypothesis. The `run_rules` fixpoint IS the loop.
- **Deliver** — winning FALLS OUT: `uh_deliver_route` consults the LEARNED model to
  find the station whose hypothesis applies the required transform. Model lookup,
  never goal-proximity search.

Files: `domains/ls20_understanding_seed.py` (→ `seeds/ls20_understanding.json`,
the `uh_*` drive + `wb_*` control rules); `worlds/arc_ls20_understanding.py` (the
mechanical adapter + episode driver); `scripts/arc_ls20_understanding_measure.py`
(the powered offline measure). One persistent agent per arm — the model carries
across levels (that IS the reframe); the world only presents observances and
affordances. Reused unchanged: `shape_decode_loop`, `recognise_required_key`, the
216000 pixel eye, the corpus/transforms.

## THE CONTROL that EARNS the reframe

`win_bound` (`wb_*`): optimises GOAL-REACH directly — `wb_probe_pick` picks the
station NEAREST THE GOAL (the win-objective), applies it, delivers if it matches;
backtracking per-level search, holds NO persistent model → re-searches every level.
The win-objective lives ONLY in the `wb_*` control, never in the `uh_*` drive
(source-audited).

## BASELINE (established FIRST, before pre-registering the gate)

Pilots (in-block seeds, `--tag pilot`/`pilot4`):

- **Convergence (clean, sigma=0):** surprise/cycle `1 1 1 1 1 1 0 0 0 0 0 0`;
  accuracy/cycle `.17 .33 .50 .67 .83 1.0 1.0 …`; **confirmed 6/6** (min 6);
  frac_model_complete 1.0; median complete-cycle 5. **DETERMINISTIC** (identical
  every episode — recognition is deterministic; the curiosity Argmin covers all
  S stations in S cycles, then confirms in S more).
- **Convergence under noise:** sigma=8 identical (219000 parity envelope);
  **sigma=16 → accuracy 0.0, confirmed 0** (recognition breaks on the small probe;
  surprise still self-converges to a WRONG model — accuracy vs ground truth is the
  gate that detects this).
- **Win-as-side-effect:** model_complete_cycle 5; held-out win-rate **1.0**
  [0.91,1.0]; wins_before_model 0.
- **vs-win-bound:** understand **1.0** [0.91,1.0] @ 1.0 applies/level (12-probe
  investigation ONCE); win_bound B=1 **0.125** [0.055,0.261]; win_bound B=S **1.0**
  @ **3.55** applies/level (re-paid EVERY level).

## PRE-REGISTERED GATES (understanding is PRIMARY; thresholds fixed NOW)

Powered run: `--episodes 25` (clean convergence, deterministic), `--levels 200`
(generalisation, Wilson CIs), `--noise 0 8 16 --noise-episodes 6` (teeth), in the
221000 seed block.

- **G-understanding (HEADLINE — the true victory).** At sigma=0: mean surprise[t]
  == 1.0 for t < S and ≤ 0.02 for t ≥ S; mean accuracy ≥ 0.99 by cycle S; **mean
  confirmed ≥ 5.9** (min ≥ 5); frac_model_complete Wilson-lower ≥ 0.85. **GATE
  TEETH (must be able to fail):** at sigma=16, frac_model_complete ≤ 0.25 —
  demonstrating the accuracy metric DETECTS perceptual failure (surprise-only
  convergence would mask it).
- **G-win-as-side-effect.** Held-out win-rate Wilson-lower ≥ 0.85; **wins before
  model-complete == 0** (structural: delivery uses the post-investigation model).
- **G-vs-win-bound.** understand win-rate Wilson-lower ≥ 0.85; **win_bound(B=1)
  win-rate Wilson-UPPER < understand Wilson-LOWER** (CI-separated — understanding
  generalises, win-binding is brittle under a tight budget). win_bound(B=S)
  reported STRAIGHT (expected ~1.0) with applies/level ≥ 2.0 — the amortisation
  gap: understand pays ~2S probes ONCE then ~1 apply/level; win_bound re-pays the
  search EVERY level (total-cost crossover ~ K==S).
- **G-graph-native + source-audit.** The drive is curiosity/surprise/hypothesis
  RULES; the adapter is mechanical. `banned_tokens` (a win/goal-reach objective
  pattern) must be ABSENT from every `uh_*` drive rule (present only in `wb_*` by
  design). Reported by a `source_match` scan.
- **G-discipline.** Integer-native in-frame; **default-OFF byte-identical**
  (existing 218000/220000 tests unchanged with `understand_on` absent);
  **canonical `.so` md5 `793ce09e…` UNCHANGED**; `term.rs` + whole `runners/dsl`
  diff EMPTY (no Rust); oracle `rung7_vision_bench` BEFORE==AFTER; 34-file
  `per_area_settlement_regression` node-id set IDENTICAL.

## LIVE HALF (the honest real-world confirmation, bounded n)

Verify auth + connectivity BEFORE measuring (`ARC_API_KEY` from `.env`, NEVER
printed/committed; the `.so` is gitignored, NEVER committed). Run the understanding
loop's perception + next-effect residual on REAL live ls20 frames (bounded n). **If
the API is unreachable/rejected/rate-limited, STOP and report — NEVER fabricate,
cherry-pick, or estimate a number.** The offline understanding result is the
deliverable regardless.

## FALSIFICATION BAR

Understanding must be GENERAL (the SAME surprise/compression/hypothesis machinery
that drives Doom curiosity + the sd-loop — dimension-arbitrary), EXPLICIT (named
`Hypothesis` nodes + a named surprise metric = the predict/observe residual), and
DISCOVERED (the station→transform map is LEARNED by investigation, not hardcoded).
