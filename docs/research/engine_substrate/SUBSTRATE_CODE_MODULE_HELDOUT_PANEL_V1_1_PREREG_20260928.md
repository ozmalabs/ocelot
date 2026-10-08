# CPython module-held-out code prediction panel v1.1 preregistration

Date: 2026-09-28  
Status: frozen before v1.1 candidate-frame generation and execution.

## Amendment rationale

The frozen v1 selector applied its registered 32-module hash sample and found zero eligible functions. Preserve the empty v1 frame as a valid selector outcome with no capability estimate. This v1.1 revision broadens the sampling universe and arity based only on that count; it does not inspect or hand-select any function body. No v1 candidate outcomes were run.

## Question and claim boundary

Measure transfer of the bounded module-composition emitter to bitwise-containing functions in CPython 3.13.5 standard-library modules other than the already inspected `stat.py`. This is same-project, module-held-out transfer, not independent-project transfer or general Python accuracy.

The corpus remains the 154 copied top-level Python files and matching PSF license at `data/cpython_lib_3_13_5/`. All top-level modules except `stat.py` and `__*` interpreter demonstration modules enter the deterministic function search. `stat.py` remains excluded.

## Frozen selector and workload

1. Consider top-level synchronous functions with one or two required positional arguments only; reject defaults, decorators, positional-only, keyword-only, variadic arguments, and bodies beyond one `Return` after optional docstring.
2. Expression and transitive same-module helpers must satisfy the unchanged v1 safe grammar: exact integer literals, bound names, unique module integer constants, unary `USub`/`Not`, bitwise `BitAnd`/`BitOr`/`BitXor`, one supported comparison, and bare positional calls to acyclic module helpers with required positional signatures and emitter depth ≤4. Require at least one bitwise operator in the transitive expression closure. No source import or execution.
3. Rank all eligible functions by the frozen v1 function hash formula over `(basename, function_name, line_number)`; select the first 24, tie-break lexically. Do not hand-replace any candidate.
4. One-argument cases use `[-1,0,1,63,64,65,127,128,255]`. Two-argument cases use, in order, `[[-1,0],[0,-1],[0,1],[1,0],[63,64],[64,63],[64,65],[65,64],[255,128]]`.
5. The selector writes the full 153-module inventory, eligible function list, selected functions, source hashes, and fixed inputs. An independent analyzer re-evaluates each case with a separately implemented safe AST interpreter and rejects the panel if any selected case is outside the oracle fragment.

All candidate outputs remain outcome-blind until frame and source lock are written. Report selection attrition, coverage, exact typed accuracy conditional on prediction, abstention, wrong returns, worker parity, receipts/mints, cost, boot failures, and RSS.

## Execution gates and interpretation

Run two fresh full-runtime workers over the exact frozen frame. Lock runtime source trees, all loaded seed inputs, native extension, corpus source/license, selector, runner, analyzer, protocol and frame before/during/after. Require independent frame/oracle reconstruction, exact hashes, complete schedules, distinct worker PIDs, stable locks, shared manifest, and hashed console capture. Any drift invalidates the run and requires a disclosed amendment and fresh execution.

A pass supports only transfer to this selected CPython same-project subset and safe grammar. It is not independent-project transfer, broad Python accuracy, or natural-task prevalence. Zero candidates, if it occurs, is retained and yields no capability estimate.
