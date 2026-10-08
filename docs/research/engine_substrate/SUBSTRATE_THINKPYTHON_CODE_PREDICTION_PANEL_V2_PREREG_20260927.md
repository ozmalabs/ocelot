# Think Python code-prediction panel v2 preregistration

Date: 2026-09-27  
Status: freeze before running the substrate.  
Question: on a broader, statically selected subset of textbook code, how often does the production code-reading/Term-evaluation route return the exact source behavior, and how often does it abstain?

## Frame, eligibility, and fixed inputs

Scan all fenced Python examples in `data/think_python_2e`. The first top-level function in each block is eligible only if it contains a return, has an exact signature in the selector's predeclared input table, and every statement/expression belongs to the frozen safe grammar. The grammar permits local assignment, augmented assignment, bounded `for`, `if`, return, pass; literals, names, bounded sequences/index/slices, arithmetic/boolean/comparison expressions; and bare calls to `abs`, `min`, `max`, `sum`, `len`, `round`, `all`, `any`, `sorted`, and `range`. Exclude recursion, attributes/methods, imports, mutation, `while`, I/O, unknown calls, and other statements. Include every eligible item, sorted by SHA-256 of compact JSON `[chapter filename, zero-based block index]`. The frozen frame stores only IDs, hashes, formal arguments, and test inputs.

There are two predetermined input cases per eligible function, using small bounded values. Cases exercise positive and negative membership/comparison outcomes, empty/nonempty paths where safe, and zero/nonzero branch values. All cases are fixed in the frame before the runtime call. The expected values are computed only by the analyzer's independent AST interpreter; the runner receives no expected answers.

## Independent interpreter

The analyzer interprets the source AST directly using explicit Python operator maps and a bare-name builtin whitelist. It never imports or executes source functions and never uses `eval` or `exec`. It enforces a 2,048-step cap, a 32-element maximum loop/range length, and bounded intermediate sequence/integer sizes. If a selected AST exceeds these safety bounds or uses unsupported semantics, the analysis gate fails; it is not silently excluded after seeing substrate output. Output comparison includes Python type as well as value. Oracle exceptions and substrate abstentions are reported separately.

## Runtime route and measurements

Two fresh full-runtime workers process every function/case pair in the selected frame order, sequentially on one graph per worker. Each call uses `domains.code_reading.predict_output`; no source function is executed by the runtime runner. Record typed prediction or exception class, source hash, frozen arguments, per-call wall/CPU time, receipt/Observation/minted-edge deltas, boot count/failures, and peak RSS. Preserve every call. Report coverage, exact correctness over all cases, exact correctness among predictions, abstention causes, task-family and construction breakdown, acquisition/receipt incidence, and timing. Repeated calls for the same function remain distinct scheduled cases and use natural within-worker carryover.

## Gates and interpretation

Lock protocol, selector, frame, runner, analyzer, domain/runtime source, seeds, native binding/source/extension, and the complete Think Python corpus. Require two fresh PIDs, source-lock stability, independent exact-frame reconstruction, exact case/order/hash parity, complete worker rows, analyzer safety-bound compliance, and exact worker schedule/prediction parity. This remains a single textbook corpus and a bounded safe-AST slice; it does not establish code capability outside this grammar, independent-task transfer, or natural workload prevalence. A separate acquisition/transfer arm is needed to test whether newly minted shapes improve predictions on held-out functions.
