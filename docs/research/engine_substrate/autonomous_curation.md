# Autonomous failure-curation — the agent banks its own lessons

## (1) VERDICT (lead) — the loop SELF-CLOSES, no human writes the memory

**YES.** A novel failure the generative skeptic CANNOT currently catch is
DETECTED (native surprise), RESOLVED (localize the weak link + do-contrast),
BANKED (the failure-shape abstracted from the resolution as a new `FailureLesson`
graph node), and then CAUGHT on replay — the same failure AND a near-miss — with
**no human writing the lesson**. The residual the generative skeptic reported
("bottoms out on an un-banked failure-mode; a human must bank it") now closes
itself, one mistake at a time. The failure-shape library grows from the agent's
own mistakes.

Run captured to `/tmp/curation_full.log` (`EXIT=0`,
`===MARKER_CURATION_COMPLETE===`, pgrep-verified gone). The script:
`scripts/autonomous_curation_replay.py`. The existing
`generative_skeptic_replay.py` still passes unchanged (no regression).

The real numbers, two INDEPENDENT novel failures + the boundary:

| case | novel? (skeptic bottoms out) | weak link localized (native surprise) | do-contrast resolution | banked | self-close (re-caught) | near-miss caught | unrelated fires |
|---|---|---|---|---|---|---|---|
| **A — leakage** (corpus-wide normalisation = train/test leak) | **True** (`novel_failure_no_matching_shape`) | `corpus_wide_normalisation` (surprise **1.142** vs 0.043) | `lever_harms` (Δ **−0.360**) | **True** | **True** | **True** | **False** |
| **B — proxy-metric** (optimised a proxy, not the target) | **True** | `silhouette_coefficient` (surprise **1.352** vs 0.148) | `disconnected_lever` (Δ **+0.000**) | **True** | **True** | **True** | (n/a) |
| **C — silent** (Dvorak finger-travel, fluent + consistent) | **True** | none (max surprise **−0.000**) | — | **False (bottoms out)** | (boundary) | — | — |

Pre-curation the library held **6** human-banked shapes; after the run it holds
**8** — the two the agent banked itself this run
(`learned__corpus_wide_normalisation__lever_harms`,
`learned__silhouette_coefficient__disconnected_lever`).

## (2) Does the banked shape GENERALIZE or overfit? — GENERALIZES

The abstracted `match_patterns` are the **content tokens at the localized weak
link**, each a single token, so any conclusion mentioning those tokens (a
near-miss of the same shape) matches — not only the exact sentence:

- **A** banked `['normalising','global','mean','computed','across','entire']`.
  The near-miss *"We **z-scored** each frame using the **global mean** and
  variance computed **across** every recording…"* — a DIFFERENT sentence, same
  leakage shape — **matched** (shares `global`/`mean`/`across`/`computed`). The
  UNRELATED conclusion *"The cochlear filterbank uses 32 gammatone channels…"*
  did **NOT** fire the learned shape. Generalises without over-firing.
- **B** banked `['silhouette','coefficient','centroid','placement','proxy','metric']`.
  The near-miss *"Tuning the embedding raised the **silhouette** score…"*
  **matched**. Generalises.

So the shape is neither a memorised exact-string (it catches paraphrases) nor a
fire-on-everything overfit (the unrelated cochlea conclusion stays off). The
generalisation is the same binary-admissibility signature the manifold-collapse
loop shows: the structure fires where the shape genuinely recurs and nowhere
else.

## (3) The HONEST BOUNDARY — silent novel failures (the fresh-mind residual)

**Named, not forced to pass.** The loop is DRIVEN by localized surprise: the
weak link is the dimension carrying the highest prediction-error. A **SILENT**
novel failure — fluent, internally consistent, whose error is only visible
against ground truth the agent does not hold — exposes **no dimension the
prediction-error can point at** (Case C: every dimension's realised support
equals its claim, max surprise `−0.000`). With nothing localized, the do-contrast
has no real weak link to toggle; banking a shape off it would be banking on an
arbitrary dimension. The loop therefore **bottoms out**: `bank` gates on a
`surprise_floor` (0.10) and refuses, reporting *"SILENT failure … no dimension
the prediction-error points at; nothing to localize or abstract."*

This is the irreducible residual, one level deeper than the skeptic's own
("un-banked shape") residual: **the loop self-closes the failures it can FEEL
(localized surprise), not the ones it cannot.** Catching a silent failure
requires a fresh mind (or external ground truth), exactly as recognising a
brand-new failure-mode for the first time did. The mechanism does not fake a pass
on it.

## (4) What was built (file:line) — detect → resolve → bank → self-close

A single NEW module + a NEW killer test. **ADDITIVE** — nothing pre-existing
modified.

- **`domains/autonomous_curation.py`** — the curation loop, the SAME
  surprise→localize→construct learning loop pointed at failure-shapes:
  - `T_DIM_SURPRISE` / `T_DIM_CONF` (`:102`/`:99`) — the per-dimension surprise as
    NATIVE Terms: `Neg(Log(realised/claimed))`, the agent's own error signal
    (imported in spirit from `scripts.native_collapse.T_SURPRISE`).
  - `T_MAX_DIM_SURPRISE` (`:106`) — the weak-link localization as a native
    **`MaxOver`** over the conclusion's `has_dim` neighbours (the argmax-localize
    the collapse loop uses to find WHERE to construct). Evaluated **in Rust**
    (verified: `MaxOver` returns the max dim surprise to machine precision).
  - `detect` (`:121`) — **DETECT**: marshal per-dimension prediction-error onto
    `Conclusion`+`Dim` nodes, evaluate the native surprise at each, localize the
    weak link via the native MaxOver.
  - `resolve` (`:182`) — **RESOLVE**: do-contrast at the weak link via the agent's
    OWN investigator (`meta_monitor.register_process` /`record_intervention` /
    `install_investigation_rule` / `agent_conclude_investigation`) — the 3-way
    `lever_helps`/`lever_harms`/`disconnected_lever` graph Rule, decided from
    MEASUREMENT. That verdict IS the resolution (what was actually wrong).
  - `_abstract_patterns` (`:227`) / `bank` (`:251`) — **CONSTRUCT/BANK**: abstract
    the failure-SHAPE from the resolution (the content tokens at the localized
    weak link → loose match-patterns; probe = "check THIS dimension"; the
    hat-input recipe) and write a new `FailureLesson` via a **native graph
    mutation** (`add_node` + `has_lesson` edge) — the construct step of the
    learning loop, meta level. Gates on `surprise_floor` (the silent boundary)
    and on a real miss (`lever_harms`/`disconnected_lever`).
  - `curate` (`:352`) — the whole loop: DETECT → (skeptic UNMATCHED) → RESOLVE →
    BANK. **SELF-CLOSE** is then verified by re-running
    `generative_skeptic.generate_probe`, which now MATCHES the banked shape (its
    `harvest_failure_shapes` reads the new node).
- **`scripts/autonomous_curation_replay.py`** — the killer test (world-glue:
  installs the 6 pre-banked lessons from `seeds/generative_skeptic.json`, hands 2
  novel failures + 1 silent one, runs the loop, replays the skeptic on each +
  near-miss + an unrelated control).

### Donkey / architecture audit

- **ADDITIVE.** Only 2 new paths (`git status`: `?? domains/autonomous_curation.py`,
  `?? scripts/autonomous_curation_replay.py`). `CortexLoop` / `solve_for_n.py` /
  `cortex_loop.py` untouched. `domains/order_n_postulates.py` and
  `domains/speech_science.py` (task B's) **not touched** — verified no
  `autonomous_curation` reference added to them, to `solve_for_n.py`, or to
  `cortex_loop.py`.
- **References READ, not modified.** `domains/generative_skeptic.py`,
  `domains/self_check_hat.py`, `domains/meta_monitor.py`,
  `seeds/generative_skeptic.json` are all unchanged (none dirty in git). The
  existing `generative_skeptic_replay.py` still passes (EXIT=0, SEATED verdict).
- **No net, no `.fit`, no gradient, no sweep, no loss/optimiser** — grep of the
  cognition module finds none (only the audit lines in the docstring).
- **Shapes ABSTRACTED, not authored.** The banked `match_patterns` are the
  content tokens the agent's OWN do-contrast localized at the weak link
  (`_abstract_patterns` over `resolution.weak_link_tokens`), not a hand-written
  probe list. The probe text and hat-input recipe are templated from the
  localized dimension + the measured meta-verdict — derived from the resolution.
- **NATIVE where the cognition lives.** Surprise + weak-link localization are
  native Term-trees (`Neg`/`Log`/`MaxOver`, Rust-evaluated); the do-contrast
  verdict is the meta-monitor's graph Rule; the bank is a native graph mutation
  (`add_node`/`add_edge`). Python is world-adapter glue only: marshal the
  per-dimension numbers, run the caller's measurement callables (world-I/O),
  tokenise, add the node — exactly what `meta_monitor.investigate` already does.

## Is the loop closed?

**Yes, for the failures the agent can FEEL — and the residual is named.** The
library grows from the agent's own mistakes: a novel failure → detected →
resolved → banked → caught (it + its near-misses, leaving unrelated conclusions
alone), with no human in the loop, demonstrated on TWO independent novel
failures. The irreducible residual is the SILENT failure (no localized surprise),
where the loop honestly bottoms out rather than faking a bank — the fresh-mind
part, one level deeper than the skeptic's own un-banked-shape residual.

NOT committed (coordinate).
