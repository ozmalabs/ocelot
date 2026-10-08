# CPython module-held-out code prediction panel v1 preregistration

Date: 2026-09-28  
Status: frozen before candidate frame generation and before candidate execution.

## Question and claim boundary

Does the current bounded module-composition emitter generalize from the inspected `stat.py` fragment to syntactically compatible functions in other CPython standard-library modules that were not used to design the intervention? This is a same-project, held-out-module transfer measurement. It is not an independent-project corpus test, broad Python accuracy estimate, or proof of general capability.

The source corpus is CPython 3.13.5 top-level `Lib/*.py` copied byte-for-byte from the local 3.13.5 install; the matching `LICENSE.txt` is retained. `stat.py` is excluded. All other module files, including private helpers, enter the eligible file inventory. The selector and all candidate rules below are fixed before parsing function bodies for selection.

## Frozen selection and scoring

1. Rank eligible module basenames by `SHA256("CPython3.13.5-module-heldout-v1\0" + basename)`; choose the first 32. Tie-break by basename. The ordered module list and hashes are written into the frozen frame.
2. Within only those files, consider top-level synchronous `FunctionDef`s. Require exactly one required positional parameter; no decorators, defaults, positional-only, keyword-only, `*args`, or `**kwargs`; and exactly one `Return` after an optional docstring.
3. The returned expression and any same-module helpers it calls must be acyclic and within the emitter’s fixed helper depth. Permit only exact integer literals, bound parameters, unique top-level integer literal constants, unary `USub`/`Not`, `BitAnd`/`BitOr`/`BitXor`, and single comparisons from `Eq`, `NotEq`, `Lt`, `LtE`, `Gt`, `GtE`. Helper calls must be bare same-module function names with positional arguments and required positional signatures. Reject unresolved names, ambiguous writes, attributes, imports as values, and all other AST nodes. Require at least one bitwise operator in the transitive expression closure.
4. Rank eligible functions by `SHA256("CPython3.13.5-function-heldout-v1\0" + basename + "\0" + function_name + "\0" + line_number)`; take the first 12, tie-break by `(basename, function_name, line_number)`. Do not manually replace an empty or inconvenient selection.
5. Apply exactly nine integer inputs per selected function, in order: `[-1, 0, 1, 63, 64, 65, 127, 128, 255]`. The selected argument name is bound to each input. A safe, independent AST interpreter in the analyzer computes expected typed outputs; it never imports or executes corpus source. If the independent evaluator rejects any selected case, the preregistered panel is invalid; do not silently drop that case.

The frozen frame records the complete module inventory, the 32-file sample, all eligible functions before the 12-function cap, selected source/function hashes, exact cases and independent expected outputs. Coverage reports selected/eligible counts at both the module and function stages. Candidate coverage, exact accuracy conditional on a returned value, abstention, wrong returns, worker parity, receipts/mints, wall/CPU time, boot failures, and RSS are reported separately.

## Execution and integrity gates

Two fresh full-runtime workers run the exact same frozen frame. Lock the full measured runtime trees, seed inputs, native extension, corpus source/license, selector, runner, analyzer, protocol, amendment (if any), and frame before, during, and after execution. Require exact input hashes, complete schedules, distinct PIDs, stable locks, a shared run manifest and hashed console capture, and independent frame/oracle reconstruction. Any source drift invalidates the run and requires a disclosed amendment plus a fresh lock and execution.

A positive prediction requires exact typed equality with the independent AST oracle. An `EmitError` is an abstention. Other exceptions are separately counted and do not count as safe abstentions. Any wrong returned value is reported as a critical failure, regardless of aggregate accuracy. No source is executed or imported by the benchmark or oracle.

## Interpretation

Passing establishes only transfer to the selected same-project module-held-out subset and declared safe grammar. It does not establish general Python performance, independent-project transfer, safety outside the tested syntax, or natural-task prevalence. A zero-candidate panel is a valid selector result but yields no capability estimate; preserve it and revise only in a new preregistered version.
