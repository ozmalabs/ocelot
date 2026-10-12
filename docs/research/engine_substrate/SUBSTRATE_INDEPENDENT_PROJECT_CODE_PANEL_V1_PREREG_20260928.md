# Independent-project code prediction panel v1 preregistration

Date: 2026-09-28  
Status: frozen before project selection, source snapshot, function selection, and candidate execution.

## Question and scope

Test transfer of the current code-reading path to a licensed Python project outside CPython, Think Python, and the Stacks examples already used. This is a bounded source-to-Term behavior panel; it does not estimate broad repository accuracy, code quality, or natural-task capability.

## Project selection without source inspection

Use installed distribution metadata and recorded file paths only; do not read `.py` file contents before this protocol and selector are frozen. Candidate distributions must have an exact permissive `License-Expression` or `License` equal to MIT, Apache-2.0, or BSD-3-Clause; at least one packaged license/copying/notice document; and at least ten production `.py` files after excluding `tests/`, `test/`, and basename `test_*.py`. Select the distribution with the lowest `SHA256("ocelot-independent-code-transfer-v1\0" + normalized_distribution_name)`; tie-break lexically by normalized name. Snapshot all eligible source files and license documents byte-for-byte; record distribution name/version/license metadata and every source/license hash. Do not substitute a hand-chosen project if the selected project is inconvenient.

## Frozen function selection

Within the selected project snapshot, consider each production Python file in lexical relative-path order and top-level synchronous functions. Require one or two required positional arguments, no decorators/defaults/keyword-only/positional-only/variadic arguments, and one `Return` after an optional docstring. Permit an exact safe AST grammar: integer constants, bound parameter names, unique module-scope integer constants, unary `USub`/`Not`, binary `Add`/`Sub`/`Mult`/`BitAnd`/`BitOr`/`BitXor`, a single `Eq`/`NotEq`/`Lt`/`LtE`/`Gt`/`GtE`, and acyclic same-module helper calls with positional arguments and the emitter's required-parameter/depth rules. Require at least one binary/comparison operation in the transitive function/helper expression. Reject all other syntax without manual replacement. Rank candidates by `SHA256("ocelot-independent-function-v1\0" + relative_path + "\0" + function_name + "\0" + line_number)` and take the first 24.

Each one-argument function receives nine inputs `[-3,-1,0,1,2,3,7,16,64]`. Each two-argument function receives nine pairs `[[-3,-1],[-1,-3],[0,1],[1,0],[2,3],[3,2],[7,16],[16,7],[64,3]]`. Freeze candidate source hashes and all arguments before invoking the substrate. An independently implemented safe AST interpreter computes typed expected outputs without importing or executing project source. Any oracle error invalidates the panel; no oracle-based case dropping.

## Gates and reporting

Two fresh full-runtime workers run the exact frozen frame. Lock runtime source/seed trees, native extension, snapshot corpus, license, selector, runner, analyzer, protocol, frame and generated reference before/during/after. Require independent frame reconstruction and oracle scoring, complete schedules, distinct PIDs, stable locks, source/case hash parity, shared run manifest and hashed console capture. Any source drift invalidates the execution and requires a disclosed amendment and a fresh run.

Report project selection provenance, file/candidate attrition, eligible and selected functions, exact coverage, accuracy conditional on a return, abstentions, wrong returns, receipts/mints, wall/CPU costs, boot failures and RSS. Any wrong returned value is surfaced separately. A zero-candidate result is retained and yields no capability estimate.

## Interpretation

A passing result supports only the selected licensed project and declared grammar. It does not establish broad independent-project transfer or code safety outside the tested path. The CPython module-held-out result remains a separate same-project estimate.
