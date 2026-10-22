# Process Mastery Battery (PMB) v1

Status: specification and harness contract; held-out capability results are not yet established. P15 recursive-improvement generations and their immutable split, arm, resource, analysis and human-comparison boundaries are specified in [`COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`](COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md).

PMB separates world generation, agent policy, and scoring. A task generator supplies an initial state, goal, and affordances; it never supplies a strategy or answer. Development and held-out instances use disjoint deterministic seed ranges (`0..9999` and `1000000..1009999`). Report per-instance records, aggregate scores, task-generator version, enabled seeds/policies, compute limits, and the exact held-out seed list. Do not tune on held-out outcomes.

| Family | Task and score | Human comparison / current status |
|---|---|---|
| (a) Permutation puzzles | Loopover, cube, and sliding puzzles; solve rate, primitive-action cost, and compute | Published human records must be matched to the same puzzle, scramble distribution, and stopping rule before comparison. Loopover generator exists; human baseline not yet calibrated. |
| (b) Mechanism discovery | Identify a hidden blicket-style rule; accuracy and interventions | Developmental causal-learning studies are candidate baselines; protocol/population matching required before a claim. Generator exists, evaluator pending. |
| (c) Grid transformations | Infer/apply held transformations; exact-match accuracy and examples used | `pmb_generated_d4_v1` is supported through `evaluation/process_mastery/grid_transfer_adapter.py`; it is repository-generated and has deterministic train/heldout seeds. ARC and LS20 remain explicitly unsupported: this checkout has domain ingestion/scoring work elsewhere, but no registered PMB source/split adapter or license record for this transfer panel. Do not generalize D4 outcomes to either source. |
| (d) Tool invention | Compose held tools to achieve a novel grid-world goal; success and action cost | Human baseline collection/protocol pending. |
| (e) Program synthesis | Held-out MBPP-style specification pass rate and compute | Use repository's existing synthesis evaluation; freeze task split and runner version. |
| (f) Explain and rebuild | Rebuild a process from an explanation alone; held-out effect-fingerprint agreement | Human baseline and explanation protocol pending. |
| (g) Cross-domain transfer | Paired learning curves with and without source-domain experience | Pre-register domains, pairings, and minimum transfer margin. |
| (h) Law rediscovery | Recover known laws from simulated observations; law precision/recall and sample count | Synthetic ground truth; report data-generation and noise settings. |

Levels are gated by the Track I plan: L1 requires mechanism identification and explain/rebuild evidence; L2 requires held-out puzzle solving without a hand-written solver strategy; later levels require their named families. No level is passed by mechanism tests alone. Human-baseline claims require a cited, protocol-matched source; otherwise report the comparison as unavailable.

## Reproducibility contract

The harness is mechanical: it installs a declared world, boots a declared profile, ticks under fixed limits, and emits raw records. It must not choose operators, rank candidate actions, or repair outcomes in Python. Baseline runs omit Track I seeds and report unsupported tasks as unsupported, not as agent failures. Track I runs opt into its seeds and policies explicitly. A result is capability evidence only when the held-out generator, profile, scoring rule, and human comparison were frozen before the run.

### Phase 15 recursive-improvement evaluation

The three-generation evaluation freezes the engine, proof/evaluation machinery, task families, criteria, primitive access, ceilings and sealed held-out identifiers. Its matched arms are an unchanged P14 operator portfolio with fixed training, the same portfolio with graph-authored residual curriculum, and the full graph-authored curriculum/operator lifecycle with per-candidate human approval. Each family/generation/arm receives at least 200 fresh matched evaluation tasks from disjoint training, selection and sealed evaluation seed blocks. The registered primary is the corrected generation slope in paired task success for full versus unchanged; curriculum-only separates task-selection effects. Work is reported separately, with no efficiency inference from success alone. A zero-tolerance grounding, proof, provenance or external-action violation fails the generation. The full lineage, deterministic parallel-fold, shared-budget and claim contract is frozen in [`COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md`](COGNITION_RECURSIVE_IMPROVEMENT_CONTRACT.md). No protocol-matched human baseline is currently available.

Current implementation covers deterministic generators for Loopover, D4 transformations, and a blicket-style hidden mechanism, plus graph installation/ticking scaffolding. The Loopover evaluator is still an early mechanism probe; it is not a PMB-compliant held-out capability evaluation.

## Phase 6 comparison and effect contract

The authoritative native-view, source-epoch, evaluator, exactness, budget, receipt, baseline-arm and raw-record requirements are frozen in [`COGNITION_PROCESS_EXECUTION_CONTRACT.md`](COGNITION_PROCESS_EXECUTION_CONTRACT.md). In brief, the baseline omits all Track I seeds and policies; the Track I arm names its opt-in closure; paired agents receive the same generated world with isolated state and equal per-agent limits. The current `harness.Agent` is Track-I-on only and cannot produce the baseline arm.

A fingerprint means agreement on the listed probes. Only a declared complete separating set under matching owner/domain/source/probe epochs permits exact deduplication. An opaque or failed evaluation (`None`) is unknown and excluded from identity, support, deduplication, and law checks. Trial records preserve concrete split/seed, profile and engine provenance, budget/debit and source/receipt identity, actual outcome, work, graph growth, and terminal status. Missing adapters are `NOT_RUN` or `UNSUPPORTED`, never zero. These conditions govern future evaluation; this section does not upgrade the existing NOT_RUN baseline record.
