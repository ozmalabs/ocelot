# CPython `stat` file-mode prediction panel v1 preregistration

Date: 2026-09-27  
Status: frozen before candidate execution.

## Question

On a separately sourced and licensed Python code module, can the current substrate predict the return values of pure file-type predicates using module-level constants and a shared mask helper? This is an out-of-box capability probe. No code change will be made in response to its results under this protocol.

## Corpus and provenance

The fixed source is the unchanged CPython 3.13.5 `Lib/stat.py`, stored at `data/python_stdlib_3_13_5/stat.py` with its `LICENSE.txt` and provenance note. The selector hashes the complete source. The benchmark is distinct from both Think Python and the Stacks Project. FSDD helper code is excluded because its local README licenses the dataset but does not clearly license the Python helper source.

## Selection and task construction

From module-level `FunctionDef`s, select every function with exactly one positional argument and exactly one non-docstring `Return`, where the return is a single `Eq` comparison: its left side is a call to the bare name `S_IFMT` with that same argument, and its right side is a bare module-level name bound to an integer literal. This rule is applied to the complete file and must select all qualifying functions. No function is selected or dropped based on prediction or oracle outcomes.

The selector independently extracts the mask from the one-argument module-level `S_IFMT(mode)` helper's `mode & integer-literal` return. For each candidate constant `K`, construct five deterministic integer cases: `0`, `K`, `K | 0o755`, `next_type_mask | 0o640` (cyclic order across selected constants), and `0o7777`. The oracle is independently implemented as `(mode & extracted_type_mask) == K`, returning an exact Boolean. Two existing Think Python arithmetic control calls from the frozen v2 string panel are appended unchanged, and scored with its bounded independent AST oracle.

## Execution and analysis gates

Use two fresh workers and one isolated substrate agent per worker. Lock the protocol, selector, frame, runner, analyzer, all Python/domain/substrate/world source, loaded seeds, native extension, Rust sources, CPython source/license, Think Python controls, and prior control reference artifacts. Compare full pre/post locks in each worker. Preserve per-call typed predictions or exact error classes; report coverage, exactness, false outputs, abstentions, receipts, mints, wall/cpu time, boot counts/failures, and peak RSS. Reconstruct selection, test cases and oracle in an independent analyzer. Require worker parity, complete schedules, stable locks, both arithmetic controls passing, and a hashed console capture in the run manifest. A candidate abstention is a measured capability gap, not an integrity failure.

## Claim boundary and follow-up

This panel measures one narrow, deterministic CPython utility family. It is not a general software-accuracy estimate or blind transfer across languages, and the fixed five-case panel does not establish distributional performance. Any subsequent implementation change requires a separate versioned intervention and a new held-out panel selected after code freeze.
