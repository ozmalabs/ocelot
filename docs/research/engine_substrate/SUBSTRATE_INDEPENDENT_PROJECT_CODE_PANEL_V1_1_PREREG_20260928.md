# Multi-project independent code prediction panel v1.1 preregistration

Date: 2026-09-28  
Status: frozen before expanding the source universe; v1 source outcome retained.

## Amendment rationale

The frozen v1 metadata hash selected `filelock` 3.25.2 (MIT, 11 production Python files), but the frozen function selector yielded zero eligible functions. That result is retained as a valid corpus/syntax coverage outcome and no candidate execution was run. To measure project diversity without selecting a replacement based on source inspection, v1.1 includes every installed distribution meeting the same metadata/license/file-count rule and searches all of them with one fixed selector. The complete selected-project set and all attrition are reported; no project or function is hand-substituted.

## Project universe

Using installed distribution metadata and file paths only, include every distribution whose exact `License-Expression` or `License` is MIT, Apache-2.0, or BSD-3-Clause; that packages at least one license/copying/notice text; and that contains at least ten production `.py` files after excluding paths with `test`/`tests` components and `test_*.py`. Snapshot all qualifying project sources and licenses byte-for-byte. Record each distribution name, version, license metadata, Python file inventory and hashes. Do not read source bodies until this protocol and the snapshotter/selector are frozen.

## Frozen function selector and cases

Across the full frozen project set, consider lexical project name, then lexical source path, then top-level synchronous functions. Require one or two required positional arguments; no decorators/defaults/keyword-only/positional-only/variadic arguments; and one `Return` after an optional docstring. The expression and same-file helper closure must be acyclic, obey the emitter's helper depth and argument rules, and use only integer constants, bound names, unique module integer constants, unary `USub`/`Not`, binary `Add`/`Sub`/`Mult`/`BitAnd`/`BitOr`/`BitXor`, one comparison from `Eq`/`NotEq`/`Lt`/`LtE`/`Gt`/`GtE`, and bare same-file positional helper calls. Require at least one binary or comparison operation in the transitive expression. All other syntax is rejected mechanically.

Rank eligible functions by `SHA256("ocelot-independent-function-v1\0" + normalized_project + "\0" + relative_path + "\0" + function_name + "\0" + line_number)`. To preserve project diversity, first select the lowest-ranked eligible function in each project, rank those project representatives by `SHA256("ocelot-independent-project-v1\0" + normalized_project)`, and take the first 24 projects. The panel therefore has at most one function per project. Report number of qualifying projects, projects with any eligible function, projects selected, all eligible functions, and selected functions.

Each one-argument function receives `[-3,-1,0,1,2,3,7,16,64]`. Each two-argument function receives `[[-3,-1],[-1,-3],[0,1],[1,0],[2,3],[3,2],[7,16],[16,7],[64,3]]`. An independent safe AST interpreter computes typed expected outputs without importing or executing source. Any selected oracle error invalidates the panel; no post-selection dropping.

## Execution gates and reporting

Two fresh full-runtime workers run the frozen frame. Lock runtime/seed trees, native extension, all project sources/licenses, manifest, selector, runner, analyzer, protocol and frame before/during/after. Require independent frame reconstruction and oracle scoring, exact source/case hashes, full schedules, distinct PIDs, stable locks, worker parity, shared run manifest and hashed console capture. On drift, discard the run and amend/relock before retry.

Report coverage, exact accuracy conditional on return, abstention, wrong returns, receipt/mint incidence, per-call wall/CPU costs, boot failures and RSS, separately by project and in total. Any wrong output is surfaced distinctly. A zero-project or zero-function result is retained as an empirical coverage boundary, not recast as a successful capability test.

## Claim boundary

A passing result is evidence for the selected independent licensed projects and the fixed safe grammar only. It is not broad repository accuracy, code safety, or natural-task prevalence. The earlier filelock-only v1 remains separately reportable and its empty selection is not pooled with v1.1.
