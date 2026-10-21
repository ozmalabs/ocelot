# Process Mastery Battery (PMB) v1

Status: specification and harness contract; held-out capability results are not yet established.

PMB separates world generation, agent policy, and scoring. A task generator supplies an initial state, goal, and affordances; it never supplies a strategy or answer. Development and held-out instances use disjoint deterministic seed ranges (`0..9999` and `1000000..1009999`). Report per-instance records, aggregate scores, task-generator version, enabled seeds/policies, compute limits, and the exact held-out seed list. Do not tune on held-out outcomes.

| Family | Task and score | Human comparison / current status |
|---|---|---|
| (a) Permutation puzzles | Loopover, cube, and sliding puzzles; solve rate, primitive-action cost, and compute | Published human records must be matched to the same puzzle, scramble distribution, and stopping rule before comparison. Loopover generator exists; human baseline not yet calibrated. |
| (b) Mechanism discovery | Identify a hidden blicket-style rule; accuracy and interventions | Developmental causal-learning studies are candidate baselines; protocol/population matching required before a claim. Generator exists, evaluator pending. |
| (c) Grid transformations | Infer/apply held transformations; exact-match accuracy and examples used | ARC/LS20 are candidate held-out sources; licensing and split provenance must be recorded. D4 generator exists. |
| (d) Tool invention | Compose held tools to achieve a novel grid-world goal; success and action cost | Human baseline collection/protocol pending. |
| (e) Program synthesis | Held-out MBPP-style specification pass rate and compute | Use repository's existing synthesis evaluation; freeze task split and runner version. |
| (f) Explain and rebuild | Rebuild a process from an explanation alone; held-out effect-fingerprint agreement | Human baseline and explanation protocol pending. |
| (g) Cross-domain transfer | Paired learning curves with and without source-domain experience | Pre-register domains, pairings, and minimum transfer margin. |
| (h) Law rediscovery | Recover known laws from simulated observations; law precision/recall and sample count | Synthetic ground truth; report data-generation and noise settings. |

Levels are gated by the Track I plan: L1 requires mechanism identification and explain/rebuild evidence; L2 requires held-out puzzle solving without a hand-written solver strategy; later levels require their named families. No level is passed by mechanism tests alone. Human-baseline claims require a cited, protocol-matched source; otherwise report the comparison as unavailable.

## Reproducibility contract

The harness is mechanical: it installs a declared world, boots a declared profile, ticks under fixed limits, and emits raw records. It must not choose operators, rank candidate actions, or repair outcomes in Python. Baseline runs omit Track I seeds and report unsupported tasks as unsupported, not as agent failures. Track I runs opt into its seeds and policies explicitly. A result is capability evidence only when the held-out generator, profile, scoring rule, and human comparison were frozen before the run.

Current implementation covers deterministic generators for Loopover, D4 transformations, and a blicket-style hidden mechanism, plus graph installation/ticking scaffolding. The Loopover evaluator is still an early mechanism probe; it is not a PMB-compliant held-out capability evaluation.
