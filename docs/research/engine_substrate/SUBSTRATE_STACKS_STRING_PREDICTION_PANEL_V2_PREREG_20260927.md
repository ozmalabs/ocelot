# Stacks Project string-predicate prediction panel v2 preregistration

Date: 2026-09-27  
Status: confirmatory candidate evaluation; v1 is the frozen baseline.  
Question: does the constrained native-Term lowering for `str.find` plus `Assign, If, Return` turn the v1 all-abstain result into exact output prediction on the same external cases and Unicode boundary additions?

## Frozen baseline and candidate

The v1 raw report, analysis, and frame are frozen baseline artifacts with SHA-256 values respectively `7805756c4bace58b64033fa71a54f07d47d48162f36cca947a752d35d050bb4e`, `d8a2a350743d3b427e1e245db254625417e7bee70ef9b720f39dda37432f9033`, and `5b35d14054401e6dd1f749a95f43ee0c58c0b90f9af36d1292ed51bbb8d5873d`. V2 retains the same five AST-selected Stacks functions, lexical acquisition/held-out order, and all four v1 cases per function; it appends one Unicode-prefix case per function. Thus the 20 v1 Stacks calls are exactly paired within v2, and five new cases stress UTF-8 byte-offset vs Python character-index behavior. The two existing Think Python `is_divisible` control calls remain last and outside Stacks scoring.

Candidate implementation maps only the exact shape `n = <one function str argument>.find(<literal string>); if n < 0: return x; return y` or the `n == 0` variant. It lowers to existing `StringIndexOf`, `Let`, comparison and `IfThenElse` Terms. The input type is supplied from the concrete prediction call and must be exactly `str`; other types abstain because Python `.find` raises `TypeError` while the native primitive otherwise returns `-1`. The binding `n` cannot be returned or used outside the comparison. Only `< 0` and `== 0` are emitted: byte offset and Python Unicode code-point offset agree on these predicates' truth values for all valid strings, though the numeric offsets themselves can differ. No generic Attribute call support is added.

## Cases and scoring

Five functions × five inputs = 25 primary Stacks cases per worker; four functions (16 cases) are held out from the first function. Each worker then runs the two frozen positive-control cases. The bounded independent AST oracle supports only the preregistered function grammar (one `.find` assignment, one restricted comparison/early return, final return) plus the arithmetic control (`%` and `==`); it never executes corpus source. Exact typed output, coverage, abstention, incorrect return, acquisition vs held-out score, Unicode-case score, and mint/receipt incidence are reported separately.

## Integrity gates

Two fresh full-runtime workers; exact 27-case schedules; distinct PIDs; source locks stable before/after; exact candidate frame reconstruction; source and input hashes; zero oracle errors; worker parity; both positive-control outputs correct; shared run manifest and hashed console log valid; and the v1 raw/analysis/frame hashes and v1 scoring reconfirmed from the immutable baseline files. Candidate capability outcomes are measured, not used as integrity gates. The source lock includes all runtime files, boot-selected seeds, native extension/build state, Stacks repository commit and license, Think Python control corpus/provenance, and baseline artifacts. This is a small controlled intervention result, not a field generalization claim. A subsequent replication must use new source functions and a second repository.
