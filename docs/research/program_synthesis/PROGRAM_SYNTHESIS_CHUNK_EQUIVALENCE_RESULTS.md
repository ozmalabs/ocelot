# PROGRAM SYNTHESIS — chunk-grain SEMANTIC EQUIVALENCE (results): NO-GO, measured

**Date:** 2026-08-12. Registered rules: `PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_PREREG.md`
§1. **Verdict: NO-GO.** Two candidate provably-safe rewrites were found and
measured against the real corpus; the one that is genuinely provably safe
(dead-temp elimination, §1.1's bar applied strictly) has **zero** corpus
occurrences that would change a recognition outcome (§1.2 criterion 2 reads
0/0); the other, more prevalent candidate (general single-use inlining) was
disqualified by the §1.1 evaluation-order bar BEFORE prevalence was even the
deciding factor. No code changes are carried in this commit — only this
document and its prereg, per the charter's own instruction that a NO-GO must
not leave unsafe/incomplete code behind.

## 1. Investigation — reading the mechanism first

`chunk_key` (`domains/prog_chunk_growth.chunk_record`) is the canonical JSON
of a role/slot-abstracted STATEMENT LIST; `chunk_rels` is its flat
relation-system form (`["ckstmt", i, label]` + `["ck", i, path, atom]`,
POSITIONAL — one row-group per statement index `i`). `ckg_recognize`
(`seeds/prog_chunk_growth.json`) decides recognition via the engine `Covers`
Term over `chunk_rels`. Reading `covers_value` (`runners/dsl/src/term.rs`,
confirmed live): a `Tuple`/`List` pattern covers an instance **only if they
have EQUAL LENGTH** (`pt.len() == it.len()`) — a WILD leaf in the pattern
auto-matches ANY leaf value at that position, but the relation-list itself
must have the exact same row count as the instance. This is P7C §1.4's own
documented fact ("unequal counts anti-unify to WILD") confirmed at the
engine level: **two chunks with a different STATEMENT COUNT can never
`Covers`-match, however similar their meaning, because they have a different
number of `ckstmt`/`ck` rows by construction.** This is the exact shape of
residual #8 — a semantically-equivalent but differently-SIZED rewrite is
invisible to `Covers` no matter what wildcarding it carries.

No live-variable / def-use analysis Term exists in the Rust engine today
(`grep -rn "LiveVar\|live_var\|DefUse\|liveness" runners/dsl/src/*.rs`
returns no analysis Term — only doc-comment mentions of "liveness" in an
unrelated `g5.rs` test-gate comment). `docs/features/program-synthesis.md`'s
"live-variable analysis at the final expression" refers to P7-A's descent
hole-fill (`Hole` local-row derivation), a DIFFERENT mechanism reading a
program's OWN already-decided splice, not a general def-use analyzer — it
was not reusable here, and as §2.3 below shows, it also was not NEEDED for
the one rewrite this investigation could actually prove safe.

## 2. Candidate rewrites — measured, in the order investigated

### 2.1 Dead-temp elimination (the task charter's flagship example)

**The exact, narrow, provably-safe statement:** `X = <expr>; return X`
(statement `i` is `ProgAssignVar(name=X, value=E)`; statement `i+1`,
IMMEDIATELY adjacent, is `ProgReturn(value=Var(name=X))`, nothing else in
between) `≡` `return <expr>`. **Safety argument (unconditional, no
live-variable analysis needed):** `ProgReturn` terminates the function's
control flow — nothing can observe `X`'s binding after this point in either
form. `E` is evaluated EXACTLY ONCE in both forms, at the SAME point
relative to every other statement in the block (there is nothing else
evaluated between the assignment and the return to reorder against). This
is strictly narrower than "X used once in the return expression" — see §2.3
for why that generalisation is NOT safe.

**Measured over the live corpus today** (`domains/prog_chunk_growth.chunk_candidates`
over every resolved+emittable id in `results/prog_ir_python_coverage.json`,
unchanged extraction walk, read-only scan — script kept at
`/tmp/.../scratchpad/prevalence_scan.py`, not committed, pure investigation):

| quantity | count |
|---|---|
| functions emitted (today, live) | 3452 |
| candidate chunk instances (windows + compound singles) | 22294 |
| instances containing the dead-temp pattern anywhere | **40** (0.18%) |
| … of those, canonicalized form falls BELOW the grain's own window floor (< 2 stmts, non-compound) | 18 |
| … of those, canonicalized form is a valid ≥2-stmt window | 22 |
| distinct reduced `chunk_key`s among the 22 | 22 |
| reduced key coincides with an EXISTING natural chunk type elsewhere in the corpus | **0** |
| reduced key would be a brand-new type (no merge target exists) | 22 |

**Corpus-drift honesty note:** today's live re-emission resolves fewer
functions (3452) than P7C's frozen mine (4099) because the SOURCE FILES have
changed since 2026-07-31 (new code uses constructs outside
`NATIVE_ORACLES`) — `results/prog_chunk_mine.json` on disk is unchanged and
still matches its own registered totals exactly (verified: `scan_scope`,
`totals`, `threshold` all reproduce PROGRAM_SYNTHESIS_P7C.md §2.1's numbers
byte-for-byte). This investigation's own scan is a fresh read against
today's tree, not a re-run of the frozen mine.

**Held-codebook cross-check:** none of the 15 mined codebook entries
(`results/prog_chunk_mine.json`'s `chunks`) has label sequence
`[ProgAssignVar, ProgReturn]` or any shape a dead-temp-eliminated candidate
could newly `Covers`-match — the mined codebook's actual idioms are
`ProgIfStmt` guards, `ProgAssignVar+ProgAssignVar` resolve chains, and
`ProgAssignVar+ProgLoopCtl` (`v = <x>; break`, support 72). **Criterion 2 of
the registered GO/NO-GO rule (§1.2) reads exactly 0/0 both ways**: zero
matches against the corpus's own natural types, zero matches against the
held self-teach-proposable codebook. Building EITHER mechanism (canonicalize-
before-hash or extend-`Covers`) would recognize nothing new on the measured
corpus.

**A concrete real example, for the record** (not a merge — illustrating the
pattern's shape): `domains/apply_exact_sequence.py::_strip_math`:

```python
def _strip_math(s: str) -> str:
    t = s.strip()
    t = t.replace("$$", " ").replace("$", " ")
    t = re.sub(r"\\(?:cdots|ldots|dots)\b", "...", t)
    return t
```

The tail `t = re.sub(...); return t` is a real, live instance of the exact
narrow pattern (embedded as the 2-statement tail of a 4-statement block, so
its reduction — `return re.sub(...)` — stays a valid ≥2-stmt window when
taken together with an earlier statement). It is one of the 40 found; its
reduced form does not coincide with anything else in the corpus.

### 2.2 If/else with identical bodies (the task charter's second suggestion)

Measured directly: **0 / 2526** `ProgIfStmt` occurrences in the live corpus
have byte-identical `then`/`orelse` blocks (exact JSON equality on the
statement lists). Zero prevalence — trivially NO-GO, not investigated
further (no safety argument was even needed).

### 2.3 General "inline the sole use" — found MORE prevalent, and DISQUALIFIED

Before settling on the narrow §2.1 statement, a broader candidate was
checked: "`X = E`, immediately followed by a statement `S` in which `Var(X)`
appears exactly once anywhere (not only a bare `return X`) `≡` `S` with that
one occurrence substituted by `E`." This is measured MUCH more prevalent —
**2072** adjacent (assign, single-later-use) pairs in the live corpus, of
which 373 have `S` = `ProgReturn`. If this were safe it would dominate the
picture. **It is not safe**, and the §1.1 bar catches it precisely on the
evaluation-order clause, with a constructed counterexample:

```python
X = f()
logger.log(g(), X)          # original order: f(), then g()
# "inlined":
logger.log(g(), f())        # new order: g(), then f() — REVERSED
```

If `f()` and `g()` are both side-effecting (a logging call, a mutation, an
exception source), the two programs are observably different — this is
exactly the evaluation-order divergence flagged in §1.1, the same shape of
mistake as the is-None/falsy trap but on the "order" axis instead of the
"value" axis. The narrow §2.1 statement survives this trap only because
`return X` (bare) has NOTHING ELSE to reorder against — the return
statement's entire evaluation IS the one substituted occurrence. Widening to
"exactly one occurrence anywhere in `S`" reintroduces the trap the moment
`S` has more than one sub-expression (e.g. `return g() + X`, or any call
with `X` as a non-first argument) UNLESS an additional purity/ordering proof
is built for `E` and every sub-expression of `S` evaluated before the
occurrence — a genuine live-variable/effect analysis this project does not
have (§1) and this rung does not build. **Disqualified at the safety bar,
not the prevalence bar** — recorded so a future rung does not re-propose it
without re-deriving this exact counterexample.

## 3. GO/NO-GO (registered rule §1.2, applied)

Criterion 1 (a rewrite passing the safety bar) is satisfied: §2.1's dead-temp
elimination is genuinely, unconditionally provably safe. **Criterion 2 (at
least one pair whose recognition outcome the rewrite would change) is NOT
satisfied: 0/40 at corpus grain, 0 against the 15-entry held codebook.**
Per the registered rule, this is a **NO-GO**. §1.3's mechanism question
(canonicalize-before-hash vs extend-`Covers`) is answered for the record —
extend-`Covers` (b) is the correctly-scoped mechanism, smaller and safer
than re-mining the corpus — but neither is built, because there is nothing
for either mechanism to recognize yet.

This is the same reasoning residual #8 itself already used to decline
merge-at-mint in P7C ("§1.4's measurement showed only 4 joins at corpus
scale, so the added rule mass isn't yet paid for"), now applied to the
SPECIFIC rewrite the task charter named, with the actual count: **not 4
joins, but 0.** The residual's own escape clause — *"Revisit if self-taught
entries proliferate"* — has not fired: self-taught entries remain at the
single hand-constructed P7C §3 demo (`ckt_prog_assign_var_q10`); there is no
evidence of the proliferation that would change this measurement's
denominator.

## 4. Negative control (unaffected, confirmed structurally)

No code changed, so the trap named in the task charter cannot have been
triggered — confirmed by re-reading the two relevant held entries directly
off `results/prog_chunk_mine.json` (unmodified): `ck_prog_if_stmt_n1_q0`
(support 166, `cond: ProgIsOp{op: is, b: Lit(None)}` — `v0 is None`) and
`ck_prog_if_stmt_n1_q1` (support 142, `cond: Not{arg: Var(v0)}` — `not v0`)
remain two separate `ShapeSignature` entries. Neither of the two rewrites
investigated here (§2.1, §2.3) would ever have unified them in any case —
`ProgIsOp` and `Not` are different node types under a completely different
rewrite question (identity-check vs falsy-check, not a statement-count
reduction) — so this is confirmation the trap was never in scope, not a
test of a built mechanism.

## 5. No regression

No source file under this track's ownership was modified. Ran, same engine,
same moment, worktree `/home/matt/ocelot-chunk-equivalence`
(`systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G`, per the
box's OOM history):

```
tests/test_prog_chunks_migrated.py            \
tests/test_prog_constructions_migrated.py     \
tests/test_program_synthesis_migrated.py      \
tests/test_prog_synthesis_battery_migrated.py \
tests/test_code_synthesis_baseline_migrated.py
  → 69 passed, 1 skipped, 16 warnings in 15.70s
```

The 1 skip is the pre-existing optional-dependency skip documented in
`CLAUDE.md`'s "optional-dep note" — no new red, no new skip, paired against
a clean run (all node ids green; zero failing-id list to report). The
gitignored `results/*.json` artifacts this suite reads
(`prog_chunk_mine.json`, `prog_ir_python_coverage.json`,
`code_synthesis_baseline.json`, `prog_construction_scan.json`,
`prog_synthesis_battery.json`) were copied byte-identical from the primary
tree into the worktree (they are build artifacts, not tracked by git, and a
fresh worktree checkout does not carry them) — none was regenerated or
modified.

## 6. What a reviewer should look at first

1. `PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_PREREG.md` §1.2 — the registered
   GO/NO-GO rule (criterion 2 is the one that decided this).
2. §2.1 above — the exact safety argument for the one rewrite that passed,
   and why it is narrower than the task charter's own informal phrasing
   ("no other use of X between assignment and return" — true, but the
   REAL reason it's safe is that `return X` bare has nothing else to
   reorder against, not merely "no other use").
3. §2.3 — the disqualified generalisation and its counterexample; this is
   the rung's own version of the is-None/falsy trap, on a different axis
   (order, not value), and is the most reusable finding for future rungs
   that might be tempted to widen the rewrite for more prevalence.
4. §1 (mechanism reading) — `covers_value`'s equal-length requirement
   (`runners/dsl/src/term.rs`) is the root cause of residual #8, confirmed
   at the engine level, independent of this rung's own GO/NO-GO.

## 7. Honest residuals

1. **Only two candidate rewrites were built out to a full safety argument**
   (dead-temp elimination, if/else-identical-bodies); the task charter's
   broader "any other rewrites you find" was pursued one level (general
   inlining) and stopped at the disqualifying counterexample, not explored
   exhaustively — a genuine live-variable/effect-purity analysis (were one
   built) could rescue a RESTRICTED form of §2.3 (e.g. "safe when `E` is
   provably pure AND `X`'s occurrence is the first sub-expression evaluated
   in `S`"), but building that analysis is unjustified while even the
   UNCONDITIONALLY safe narrow case measures zero corpus payoff.
2. **The window-floor interaction is a real, separate structural fact**
   this investigation surfaced but did not need to resolve: 18/40 dead-temp
   instances reduce to a bare single `ProgReturn` statement, which the
   registered §1.2 grain (`_WINDOW_SIZES = (2,3,4)` plus compound-only
   singles) never enrols as a candidate AT ALL, with or without this rung's
   rewrite — those 18 are permanently incomparable to anything under the
   current grain definition, a fact independent of the GO/NO-GO verdict
   here and worth naming if a future rung revisits the grain's own floor.
3. **Corpus drift** (§2.1): the live corpus today resolves fewer functions
   than P7C's frozen mine; this investigation's numbers are against TODAY's
   tree, honestly labelled as such, not a claim about the frozen artifact.
