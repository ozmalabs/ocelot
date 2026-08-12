# PROGRAM SYNTHESIS — chunk-grain SEMANTIC EQUIVALENCE (prereg)

**Date:** 2026-08-12. Companion to `PROGRAM_SYNTHESIS_P7C.md` (the idiom-grain
chunk codebook — `chunk_key`, `ckg_recognize`'s `Covers` check, residual #8).
This rung asks one question, precisely: can two DIFFERENTLY-SHAPED code
fragments that are PROVABLY the same program be recognized as the same chunk
identity, closing residual #8 — *"a self-taught near-variant of a held chunk
with a DIFFERENT shape mints its own entry rather than joining… §1.4's
measurement showed only 4 joins at corpus scale, so the added rule mass isn't
yet paid for. Revisit if self-taught entries proliferate."*

No code is touched by this document. §1 below is the registered decision
rule, written after reading the mechanism (`chunk_key`/`chunk_rels`/`Covers`)
but BEFORE the corpus-prevalence numbers in §2+ were tabulated in the exact
form reported — the P7C precedent for a rule stated in terms that cannot be
adjusted after the fact (a real-recurrence bar, not a tuned constant).

## 1. REGISTERED — the decision rule, the safety bar, the mechanism test

### 1.1 What "provably safe" means here (the calibration test)

A candidate rewrite is admitted to this investigation ONLY IF it can be
stated as an unconditional semantic-preservation argument that holds for
**every** possible runtime value and every possible execution path — never
"these look similar" (the is-None / falsy-check example named in the task
charter is the canonical NON-example: `v0 is None` and `not v0` diverge at
`v0 = 0`, and must never be unified). Two failure modes are explicitly
disqualifying, checked for every candidate before it is measured:

- **value divergence** — the transform changes the result for some input
  (the is-None/falsy trap);
- **evaluation-order divergence** — the transform changes when a
  side-effecting sub-expression runs relative to another one (a subtler
  trap this rung's own investigation surfaced — see §2.3: an unrestricted
  "inline the sole use" rewrite is NOT safe in general, only the special
  case where nothing else is evaluated between the definition and the use).

### 1.2 The GO/NO-GO rule (registered before the exact counts were read)

**GO** requires BOTH:

1. at least one candidate rewrite that passes the §1.1 bar with a stated,
   checkable, unconditional argument, AND
2. that rewrite's real corpus recurrence produces at least one case where
   the REWRITE changes a recognition outcome — i.e. at least one pair of
   chunk instances (whether both natural corpus occurrences, or a
   self-teach-vs-held-codebook pair) that do NOT already share a
   `chunk_key`/`Covers` match today but WOULD after the rewrite is applied
   to one side. Zero such pairs, however common the *pattern* is in
   isolation, is a **NO-GO** — mirroring P7C §1.4's own registered
   "measured, not blindly re-imposed" discipline (4 joins at corpus scale
   were enough to adopt the 2/3 AntiUnify criterion; the bar here is the
   same shape: does it ever actually fire).

A NO-GO is registered here, in advance, as a complete and valuable outcome
if criterion 2 measures zero — not a failure to be pushed past with a
broader (and less provably safe) rewrite.

### 1.3 Mechanism test (registered before the choice is made)

Two mechanisms are on the table, per the task charter:

- **(a) canonicalize-before-hash** — rewrite a candidate's statement list
  before `chunk_key`/`chunk_rels` are computed, so equal chunks hash
  identically at MINE time (`scripts/prog_chunk_mine.py`) and SCAN time
  (`domains/prog_chunk_growth.scan_marked_programs`) alike. This touches
  the corpus miner's own registered §1.2 grain (would require a full
  corpus re-mine, and interacts with the §1.4 AntiUnify dedup and the
  window-floor rule below) — the BIGGER-footprint option.
- **(b) extend `ckg_recognize`'s `Covers`** — leave `chunk_key`/`chunk_rels`
  computation and the corpus miner completely alone; at the SELF-TEACH
  recognition rule only, additionally check the rewritten form of an
  incoming `Observation` (and/or a held entry) under `Covers`. This is
  residual #8's own literal scope ("a self-taught near-variant of a HELD
  chunk") — the SMALLER-footprint option.

**Registered choice of mechanism, IF GO:** (b), extend-`Covers`, precisely
because it is scoped to residual #8's own stated concern (self-teach
recognition) without re-running or risking the corpus mine's own frozen,
determinism-gated artifact (`results/prog_chunk_mine.json`, byte-identical
twin-run gated in P7C §2.1) — (a) is the "sounds more general" option the
task charter explicitly warns against assuming correct without
justification, and this investigation's own §2 finding (the window-floor
interaction) shows (a) has a real structural cost (b) does not: (a) would
change the corpus miner's candidate POPULATION itself (which windows even
get enrolled), a materially bigger and riskier surface than (b)'s
recognition-only reach.

### 1.4 Corpus + condition (same as P7C, for comparability)

Corpus: the P2/P3 emittable list (`results/prog_ir_python_coverage.json`),
re-emitted via `domains/prog_ir_emit.emit_prog_ir`, resolved by
`prog_construction_scan._FileCache`/`parse_id` (imported, not copied) — the
SAME plumbing P7C's own miner uses. Candidate extraction via the UNCHANGED
`domains/prog_chunk_growth.chunk_candidates`/`_blocks`/`_is_compound` (no
modification for this investigation — a read-only scan). Condition:
`PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1`; worktree engine (`_native.abi3.so`, committed
in-tree, mtime-touched); a bare `substrate_rs.Substrate` used only where an
engine Term is invoked.

**Honest note on corpus drift:** the corpus's SOURCE FILES (`domains/*.py`)
have continued to change since P7C's mine last ran (2026-07-31, artifact
re-confirmed present and byte-matching its own registered totals as of
2026-08-10). Re-emitting the SAME (file, qualname, lineno) id list TODAY
naturally yields a different not-emittable count than the frozen artifact
(new code uses constructs outside `NATIVE_ORACLES`) — this is corpus drift,
not a bug in this investigation's scan; §2 reports the numbers actually
measured today, not a reproduction of P7C's exact frozen totals.
