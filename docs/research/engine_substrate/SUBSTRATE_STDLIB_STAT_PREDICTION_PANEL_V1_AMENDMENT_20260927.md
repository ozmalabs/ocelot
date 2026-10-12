# CPython `stat` file-mode predicate panel v1 amendment

Date: 2026-09-27  
Status: post-run selection-provenance clarification; task frame and results unchanged.

The CPython `stat.py` module and the `S_IFMT(mode) == S_IF*` pattern were selected after inspecting the local licensed-source inventory and the module's AST. The deterministic selector exhaustively includes every module-level function matching that preregistered pattern, and no prediction or oracle result was consulted to select or remove candidates. However, the corpus and target family were not chosen blindly. The experiment is therefore a source-independent, outcome-blind measurement of a deliberately selected family, not a blind family-transfer estimate.

This amendment does not change the 7-function frame, 35 primary cases, two controls, oracle, source, scoring, or run. The runner's captured manifest predates this interpretive clarification and does not hash this amendment; the final result links and hashes the amendment alongside the captured raw report. Future panels must register source and family selection criteria before opening candidate function bodies if a blind transfer claim is intended.
