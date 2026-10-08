# Think Python code-reading rung-entry panel v1 preregistration

Date: 2026-09-27  
Status: freeze before confirmatory execution.  
Question: on a hash-selected stream of independently authored Python function examples, how often does the production code-reading route use held structure versus enter dimension induction, and what are its route costs?

## Frame and selection

The selector scans fenced Python blocks in the 21 chapter text files listed by `data/think_python_2e/provenance.json`. Eligibility requires only that a block parse with Python's `ast` parser and contain at least one top-level function. Rank eligible blocks by SHA-256 of compact JSON `[chapter filename, zero-based block index]`; select the first 64. This uses no substrate output, task success, or code-reading result. The frame stores identifiers, source hashes, and function names, not the book's code text. At preregistration there are 124 eligible blocks. Each selected block is passed as captured and the first top-level function is read.

## Route and runtime

Two fresh processes load the full seed runtime through `WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)` and `load_all_seeds`, then process the exact selected schedule sequentially on independent graph instances. Each task calls production `domains.code_reading.read_function(adapter, source, selected_function)`. This evaluates explicit structural code reading, not conversational coding, execution correctness, or general software engineering. Sequential processing deliberately includes codebook growth and graph carryover.

## Outcomes and cost

Before and after each task, passively collect concern receipt IDs, Observation IDs and typed outcomes, `CapabilityAxis` attributes, transform nodes, and `ShapeSignature` nodes. A rung mint requires a new Observation with a native `minted` edge to an axis; count the `read_function` returned `minted` flag and construction separately as route reports. `CapabilityAxis` type growth is reported by kind and is not itself induction. Any word surface is replaced by a SHA-256 hash. Record source hash, route exception, construction-present bit, Term-present bit, task wall/CPU time, graph-size deltas, and boot/RSS. Do not store code text or rendered source in raw results.

Primary measures: post-cold-start task incidence of new concern receipt and Observation-linked mint (tasks 2–64); construction/read coverage on all 64; Term-emission coverage as a separate stricter outcome; receipt/native work deltas where present; worker parity; request CPU/wall distribution and process RSS. No answer-quality claim is made by successful parsing or construction recognition. The examples are a convenience corpus, not a representative natural software workload.

## Lock and gates

Lock the protocol, selector, frame, runner, analyzer, all Python files under `domains/`, `substrate/`, `worlds/`, `scripts/`, native Python bindings, Rust source and extension, all seed JSON, and `data/think_python_2e`. Require two distinct fresh worker PIDs; expected full runtime boot; all 64 IDs in exact order per worker; matching content hashes; no task exception; worker schedule parity; pre/post source-lock equality; and independent analyzer reconstruction of candidate eligibility, selector ranks, frame, and outcome counts. Source mutation invalidates the run.

## Interpretation boundary

This panel estimates code-reading route behavior on one selected collection of textbook examples. It does not establish semantic code understanding, output prediction accuracy, production repository performance, human workload prevalence, or general rung-three acquisition economics. A next capability panel must pair route outcomes with an independent semantic oracle (for example, held-out function input/output cases) and vary code structure/size under a preregistered design. Results from this corpus remain separate from the NaturalProofs prose-to-conversation panel.
